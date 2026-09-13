"""Crash-safe, fingerprinted capture of auditable river states (harness 3,
step 4).

A captured state is just `(hand_index, deck, action_ids)`. `NLHE.reset(deck)`
and `NLHE.step(action)` consume NO randomness, so a hand replays exactly and
capture cannot perturb the self-play stream it observes. Everything else --
board, pot, stacks, live seats, ranges, buckets -- is rederived offline.

FINGERPRINT. `searchab.py:242` set the precedent and the ultracode audit
showed why: a dump resumed under a different seed or checkpoint silently
pools incompatible rows. That fingerprint omits several things this harness
cannot afford to omit, and each omission is a way to pool states that are
not comparable:

  - it uses `os.path.basename(blueprint)`, so two directories with the same
    basename collide. Here the ABSOLUTE path is recorded, plus the
    checkpoint's own iteration and bucket build id, which pin CONTENT
    rather than name;
  - purification threshold, floor configuration and the range-construction
    rule all change what a row MEANS, not merely how it was reached;
  - the eligibility predicate defines the population. Two dumps built under
    different predicates describe different estimands and must never merge.

Resume refuses on any mismatch and there is deliberately NO --force, again
following searchab.

CRASH SAFETY. Rows append and fsync immediately; a torn final line (killed
mid-append) is dropped with a note on resume, while a torn interior line is
corruption and refuses.

The cascade counters ride ON EACH ROW rather than in a periodically
rewritten trailer. A trailer is a SECOND source of truth that a clean exit
keeps in sync and a hard kill does not: the sealed rehearsal killed a run
at 80 states with the trailer last written at 50, so resume restarted
BEHIND the last recorded row, replayed hands that had already produced
rows, and reported 1,123 hands where the uninterrupted run reported 1,944.
Carrying cumulative counters and the next hand index on every row makes the
last surviving row authoritative, which is exactly the granularity fsync
already guarantees. Hands played after that row produced nothing, so
replaying them counts them exactly once.
"""
import hashlib
import json
import os
import random
import time

HEADER = "hand,deck,actions,seats,cascade"
FP_PREFIX = "# fp "
CASCADE_PREFIX = "# cascade "
SCHEMA_VERSION = 2

CASCADE_KEYS = ("hands", "rivers_dealt", "hands_reaching_river",
                "river_decisions", "river_start_nodes", "river_start_hu",
                "hu_mid_street_only", "hu_start_with_allin",
                "hands_eligible", "next_hand")


def eligible(game):
    """THE pre-registered predicate (ROADMAP, frozen 2026-08-14).

    `history[-1] == '/'` is load-bearing, not cosmetic: active_players() is
    "not folded" and INCLUDES all-in seats, so without it 7,985 of 50,000
    measured hands would have contributed a mid-street state, many of them
    degenerate one-node subgames.
    """
    return (game.street == 3
            and bool(game.history) and game.history[-1] == "/"
            and len(game.active_players()) == 2
            and all(game.stacks[s] > 0 for s in game.active_players()))


def _file_sha(path):
    try:
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()[:32]
    except OSError:
        return None


def make_fingerprint(policy, assigner, cfg, seed, floors, predicate="v1",
                     deck_size=None, buckets_dir="buckets"):
    """Canonical identity of everything that makes captured states
    comparable.

    ckpt_path + ckpt_iteration + bucket_build_id do NOT pin content: this
    repo contains two checkpoints (day4_ckpt and day4_compact) that differ
    by 94.6M rows while sharing the same iteration and bucket build, so a
    dump captured against one would be pooled with the other on any path
    that resolves alike. The checkpoint's meta.json is hashed instead --
    it carries `rows` and the compaction parameters, so it separates them.

    `deck_size` is recorded because `capture()` takes it as an independent
    argument: two corpora built with different deck sizes are different
    populations that would otherwise share a fingerprint.
    """
    body = {
        "schema": SCHEMA_VERSION,
        "seed": seed,
        "deck_size": deck_size,
        "predicate": predicate,
        "ckpt_meta_sha256": _file_sha(
            os.path.join(str(policy.source_path or ""), "meta.json")),
        "buckets_meta_sha256": _file_sha(
            os.path.join(buckets_dir, "meta.json")),
        # assign_cache.pkl is AUTHORITATIVE, not a memo: BucketAssigner.bucket
        # returns cache.get(key) and short-circuits the centroid computation
        # (abstraction.py:374), so a cached entry is never recomputed or
        # verified. Its only guard is a load-time build_id check, and
        # _compute_build_id (abstraction.py:329) hashes meta.json and the
        # centroids -- not the feature code that produced the entries. It
        # therefore cannot claim the "provably non-authoritative" exemption
        # and is hashed here. meta.json does carry feature_version=2, so the
        # build id covers the abstraction VERSION transitively; this closes
        # the remaining gap where entries and code could disagree.
        # Stable across a resume: only train_blueprint.py writes this file,
        # never the audit. If a training run does rewrite it mid-audit, the
        # fingerprint mismatch is the correct outcome, not a nuisance.
        "assign_cache_sha256": _file_sha(
            os.path.join(buckets_dir, "assign_cache.pkl")),
        "num_players": cfg["num_players"],
        "stack": cfg["stack"],
        "menu": json.loads(json.dumps(cfg["menu"])),
        "threshold": policy.threshold,
        "floors": list(floors),
        "range_rule": "public-history/purified/normalize-floor-renormalize",
        "ckpt_path": os.path.abspath(str(policy.source_path or "")),
        "ckpt_iteration": policy.ckpt_iteration,
        "bucket_build_id": getattr(assigner, "build_id", None),
        "ckpt_bucket_build_id": policy.bucket_build_id,
    }
    blob = json.dumps(body, sort_keys=True, separators=(",", ":"))
    digest = hashlib.blake2b(blob.encode(), digest_size=8).hexdigest()
    return FP_PREFIX + digest + " " + blob


def _atomic_replace(tmp, path):
    for attempt in range(10):        # os.replace needs retry loops on Windows
        try:
            os.replace(tmp, path)
            return
        except PermissionError:
            time.sleep(0.2 * (attempt + 1))
    os.replace(tmp, path)


class CaptureDump:
    """Append-only dump with a fingerprint header and cascade counters."""

    def __init__(self, path, fingerprint):
        self.path = path
        self.fingerprint = fingerprint
        self.rows = []
        self.cascade = dict.fromkeys(CASCADE_KEYS, 0)
        self._f = None

    # ------------------------------------------------------------- reading
    def resume(self):
        """Load an existing dump. Returns the number of rows recovered."""
        if not os.path.exists(self.path):
            return 0
        # Byte-level, because a torn tail must be excised from the FILE, not
        # merely skipped in memory. Appending at EOF after a mid-row kill
        # fuses the next row onto the leftover prefix, and a tear inside the
        # hand-index field produces a line that parses PERFECTLY: right
        # field count, valid ints, exactly len(CASCADE_KEYS) counters. The
        # fabricated index (e.g. 9951 from "9" + "951") then poisons
        # next_hand and silently skips thousands of hands. A row is durable
        # iff it is newline-terminated: writes are one row at a time,
        # flushed and fsync'd, so an unterminated tail is by definition a
        # partial write regardless of whether it happens to parse.
        with open(self.path, "rb") as f:
            blob = f.read()
        if blob and not blob.endswith(b"\n"):
            self._good_end = blob.rfind(b"\n") + 1   # 0 when no full line
            print(f"  note: discarding {len(blob) - self._good_end} torn "
                  f"bytes after the last complete row")
        else:
            self._good_end = len(blob)
        lines = blob[:self._good_end].decode().splitlines()
        if not lines or lines[0] != HEADER:
            raise SystemExit(f"{self.path}: not a river-capture dump")
        if len(lines) < 2 or not lines[1].startswith(FP_PREFIX):
            raise SystemExit(f"{self.path}: no fingerprint -- start a fresh "
                             f"dump")
        if lines[1] != self.fingerprint:
            raise SystemExit(
                f"{self.path}: fingerprint mismatch; these states are not "
                f"comparable with this run.\n  dump: {lines[1][:160]}\n  "
                f"this: {self.fingerprint[:160]}\nUse a new --dump path "
                f"(there is deliberately no --force).")
        body = lines[2:]
        last_cascade = None
        for i, line in enumerate(body, start=3):
            if not line:
                continue
            if line.startswith("#"):
                continue
            try:
                hand, deck, actions, seats, counters = line.split(",", 4)
                row = (int(hand), _ints(deck), _ints(actions), _ints(seats))
                vals = _ints(counters)
                if len(vals) != len(CASCADE_KEYS):
                    raise ValueError("bad cascade width")
                last_cascade = dict(zip(CASCADE_KEYS, vals))
            except (ValueError, IndexError):
                if i == len(body) + 2:      # torn FINAL line: crash mid-append
                    print(f"  note: dropping torn final line {i}")
                    continue
                raise SystemExit(f"{self.path}:{i}: corrupt interior line")
            self.rows.append(row)
        seen = set()
        for r in self.rows:
            if r[0] in seen:
                raise SystemExit(f"{self.path}: duplicate hand index {r[0]}")
            seen.add(r[0])
        if last_cascade is not None:
            self.cascade.update(last_cascade)
            # The row's OWN counters are authoritative. Deriving next_hand
            # from max(seen)+1 instead would trust a hand index over the
            # counters written beside it, which is exactly how a fused
            # index propagates: it raises next_hand with full confidence
            # and skips every index in between.
            want = max(seen) + 1 if seen else 0
            if self.cascade["next_hand"] != want:
                raise SystemExit(
                    f"{self.path}: last row's next_hand="
                    f"{self.cascade['next_hand']} but its index implies "
                    f"{want} — the dump is corrupt (a fused or fabricated "
                    f"hand index). Refusing rather than silently skipping "
                    f"{abs(self.cascade['next_hand'] - want):,} hands.")
            if self.cascade["hands"] != self.cascade["next_hand"]:
                raise SystemExit(
                    f"{self.path}: hands={self.cascade['hands']} != "
                    f"next_hand={self.cascade['next_hand']}; every index "
                    f"below next_hand must have been played exactly once")
        return len(self.rows)

    # ------------------------------------------------------------- writing
    def open(self):
        # Cut the file back to the last complete row BEFORE appending.
        # Without this, "a" mode writes at EOF, which after a mid-row kill
        # is not a line boundary, and the next row fuses onto the torn
        # prefix. resume() computed the boundary; enforce it on disk.
        end = getattr(self, "_good_end", None)
        if (end is not None and os.path.exists(self.path)
                and os.path.getsize(self.path) != end):
            with open(self.path, "r+b") as f:
                f.truncate(end)
                f.flush()
                os.fsync(f.fileno())
        fresh = not self.rows and not os.path.exists(self.path)
        if fresh:
            tmp = self.path + ".tmp"
            with open(tmp, "w") as f:
                f.write(HEADER + "\n")
                f.write(self.fingerprint + "\n")
            _atomic_replace(tmp, self.path)
        self._f = open(self.path, "a")
        return self

    def append(self, hand, deck, actions, seats):
        """Row carries the cumulative cascade counters.

        They must NOT live in a periodically rewritten trailer. That is a
        second source of truth which a clean exit keeps in sync and a hard
        kill does not: the sealed rehearsal killed a run at 80 states with
        the trailer last written at 50, so resume restarted BEHIND the last
        recorded row, replayed hands that had already produced rows, and
        reported 1,123 hands where the uninterrupted run reported 1,944.
        On every row, the last surviving row is authoritative — exactly the
        granularity fsync already guarantees.
        """
        self.rows.append((hand, list(deck), list(actions), list(seats)))
        counters = _join(self.cascade[k] for k in CASCADE_KEYS)
        self._f.write(f"{hand},{_join(deck)},{_join(actions)},"
                      f"{_join(seats)},{counters}\n")
        self._f.flush()
        os.fsync(self._f.fileno())

    def checkpoint_cascade(self):
        """Deliberately a no-op.

        Counters ride on every row, so there is nothing periodic to flush
        and — the point — no second source of truth that a hard kill can
        leave disagreeing with the rows. Kept as a method so callers need
        not care how durability is achieved.
        """
        return

    def close(self):
        if self._f is not None:
            self._f.close()
            self._f = None

    def sorted_rows(self):
        """Bit-stable order regardless of append sequence or resume point."""
        return sorted(self.rows, key=lambda r: r[0])


def _join(xs):
    return " ".join(str(int(x)) for x in xs)


def _ints(s):
    s = s.strip()
    return [int(x) for x in s.split()] if s else []


def hand_rng(seed, index):
    """Per-hand keyed stream, so a hand's play is a pure function of its
    INDEX rather than of everything drawn before it.

    Resume skips hands already recorded. A single shared policy stream
    would therefore sit at a different position than in an uninterrupted
    run, and every subsequent hand would play differently — a corpus that
    silently depends on where the crash happened. Deterministic policies
    hide this completely (their actions do not depend on the draw), so it
    cannot be caught with a fixture that never mixes. Same reasoning as
    keyed training streams in mccfr (stream_base): key by index, never
    replay a prefix.
    """
    return random.Random(f"rivercap|{seed}|{int(index)}")


def capture(policy, game, rng, dump, target, deck_size, seed, log=print,
            checkpoint_every=250):
    """Self-play until `target` eligible states exist in `dump`.

    The corpus is a pure function of (seed, hand index): decks come from
    `rng` drawn once per index whether or not the hand is replayed, and the
    policy is reseeded per hand from `seed`. So resume reproduces the same
    corpus regardless of where a crash happened.
    """
    # Skip by INDEX, not by "did this hand yield a state". Hands that
    # produced nothing are absent from the recorded rows, so a resume keyed
    # on those rows would REPLAY them and count them a second time --
    # inflating exactly the denominators the cascade exists to report. The
    # deck stream is still advanced for skipped indices so it stays aligned.
    resume_from = int(dump.cascade.get("next_hand", 0))
    hand = 0
    start = time.time()
    while len(dump.rows) < target:
        deck = rng.sample(range(52), deck_size)
        idx = hand
        hand += 1
        if idx < resume_from:
            continue
        dump.cascade["next_hand"] = hand
        policy.rng = hand_rng(seed, idx)
        dump.cascade["hands"] += 1
        game.reset(deck=deck)
        actions = []
        hit = None
        saw_river = saw_start = False
        while not game.is_over():
            if game.street == 3:
                dump.cascade["river_decisions"] += 1
                if not saw_river:
                    dump.cascade["hands_reaching_river"] += 1
                    saw_river = True
                live = game.active_players()
                at_start = bool(game.history) and game.history[-1] == "/"
                if at_start:
                    dump.cascade["river_start_nodes"] += 1
                    if not saw_start:
                        saw_start = True
                    if len(live) == 2:
                        dump.cascade["river_start_hu"] += 1
                        if not all(game.stacks[s] > 0 for s in live):
                            dump.cascade["hu_start_with_allin"] += 1
                        elif hit is None:
                            hit = (list(deck), list(actions), list(live))
                elif len(live) == 2:
                    dump.cascade["hu_mid_street_only"] += 1
            a = policy.act(game)
            actions.append(a)
            game.step(a)
        if len(game.board) == 5:
            # a river was DEALT even if nobody could act on it (all-in
            # runouts). Coverage over decision-bearing rivers alone omits
            # those, so both denominators are recorded and reported.
            dump.cascade["rivers_dealt"] += 1
        if hit is not None:
            dump.cascade["hands_eligible"] += 1
            dump.append(idx, hit[0], hit[1], hit[2])
            if len(dump.rows) % checkpoint_every == 0:
                dump.checkpoint_cascade()
                el = time.time() - start
                log(f"  {len(dump.rows):,}/{target:,} states | "
                    f"{dump.cascade['hands']:,} hands | {el:.0f}s")
    dump.close()
    return dump


def cascade_report(cascade):
    """The eligibility cascade with its coverage figure. Reported ALWAYS --
    silent truncation of the denominators is prohibited."""
    c = cascade
    hands = max(c["hands"], 1)
    starts = max(c["river_start_nodes"], 1)
    dealt = max(c["rivers_dealt"], 1)
    return {
        "hands": c["hands"],
        "rivers_dealt": c["rivers_dealt"],
        "hands_reaching_river": c["hands_reaching_river"],
        "hands_eligible": c["hands_eligible"],
        "eligible_rate": c["hands_eligible"] / hands,
        "river_decisions": c["river_decisions"],
        "river_start_nodes": c["river_start_nodes"],
        "river_start_hu": c["river_start_hu"],
        "hu_mid_street_only": c["hu_mid_street_only"],
        "hu_start_with_allin": c["hu_start_with_allin"],
        # THE pre-registered gate: share of decision-bearing rivers the
        # two-seat solver can audit.
        "audit_coverage": c["river_start_hu"] / starts,
        # disclosed alongside it: the same numerator over every river
        # DEALT. Lower, because all-in runouts deal a river nobody acts on.
        # Reported so "coverage" is never read against the wrong population.
        "audit_coverage_of_dealt": c["river_start_hu"] / dealt,
        "decision_bearing_share": c["river_start_nodes"] / dealt,
    }
