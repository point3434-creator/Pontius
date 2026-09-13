"""Linear MCCFR with negative-regret pruning — the Pluribus blueprint algorithm.

External-sampling Monte Carlo CFR:
  - one traversal per seat per iteration; at the traverser's decision points we
    explore every action, at opponents' we sample one from the current strategy
  - regret matching turns accumulated regrets into the current strategy
  - the *average* strategy (what you actually play) accumulates at sampled
    opponent nodes
  - Linear CFR is applied as periodic discounting: every `discount_every`
    iterations, regrets are scaled by w/(w+1) and strategy sums by (w/(w+1))^2
    (DCFR's gamma=2 average weighting). Discounting is a *warmup*: after
    `discount_until` iterations it stops so regrets can accumulate deep
    negatives and pruning engages (the Pluribus schedule)
  - negative-regret pruning: actions whose regret is deeply negative are
    skipped in 95% of traversals (never on the river); regrets are floored so
    pruned actions can recover

STORAGE is a structure-of-arrays slab table (see table.py): float64 regret /
strategy slabs plus a digest index, with a shared-memory backend so a
multi-process run keeps ONE table machine-wide instead of a copy per worker.
Two modes:
  direct  — run_single and the parallel MASTER mutate slab rows in place
  window  — parallel WORKERS buffer each sync window privately
            (WindowOverlay) and ship compact row-keyed delta packs; the
            master is the only writer, so all processes stay exactly equal

Checkpoints are raw-dump directories (fast sequential IO); legacy
dict-of-Nodes .pkl checkpoints load transparently and convert on next save.
Checkpoints carry a config + abstraction fingerprint and refuse to resume
under a mismatched game or a rebuilt bucket abstraction.
"""
import json
import os
import pickle
import random
import sys

import numpy as np

from . import keyed
from .engine import CHECK_CALL, FOLD, NLHE
from .evaltable import EvalTable, SidecarError, SidecarUnavailable
from .table import FrequencySketch, SlabTable, WindowOverlay, key_digest

sys.setrecursionlimit(20000)

_UNIFORMS = {}  # read-only uniform distributions keyed by action count


def regret_matching(regrets):
    pos = np.maximum(regrets, 0.0)
    s = pos.sum()
    if s <= 0:
        n = len(regrets)
        u = _UNIFORMS.get(n)
        if u is None:
            u = np.full(n, 1.0 / n)
            u.setflags(write=False)
            _UNIFORMS[n] = u
        return u
    return pos / s


class Node:
    """Small standalone regret/strategy pair (subgame search tables)."""
    __slots__ = ("regret", "strat")

    def __init__(self, n_actions):
        self.regret = np.zeros(n_actions, dtype=np.float64)
        self.strat = np.zeros(n_actions, dtype=np.float64)


class _RowHandle:
    """dict-of-Nodes compatibility view over one slab row."""
    __slots__ = ("regret", "strat")

    def __init__(self, reg, strat):
        self.regret = reg
        self.strat = strat


class _NodesView:
    """Mapping-style view of a SlabTable (tests, in-memory policies)."""

    def __init__(self, table):
        self._t = table

    def __len__(self):
        return self._t.rows

    def __contains__(self, key):
        return self._t.lookup(key) is not None

    def __getitem__(self, key):
        row = self._t.lookup(key)
        if row is None:
            raise KeyError(key)
        reg, strat, _ = self._t.row_values(row)
        return _RowHandle(reg, strat)

    def get(self, key):
        row = self._t.lookup(key)
        if row is None:
            return None
        reg, strat, _ = self._t.row_values(row)
        return _RowHandle(reg, strat)


def menu_width(menu):
    """Max action-count for a menu: fold + check/call + raises + all-in."""
    return 3 + max(len(f) for f in menu.fractions)


class MCCFRTrainer:
    def __init__(self, assigner, num_players=8, stack=200, sb=1, bb=2,
                 menu=None, seed=0,
                 prune_threshold=-15000.0, prune_prob=0.95,
                 discount_every=1000, discount_until=None,
                 max_infosets=2_000_000, shared_prefix=None, attach=False,
                 min_visits=1, sketch_cells=2 ** 27, stream_base=None,
                 game_factory=None):
        self.assigner = assigner
        self.num_players = num_players
        self.rng = random.Random(seed)
        # stream_base != None switches to KEYED per-iteration randomness:
        # every iteration reseeds the cursor from (seed, stream_base +
        # iteration), so draws are a pure function of the GLOBAL iteration
        # number. A resumed run continues the stream instead of replaying
        # the seed's prefix (2026-08-12 review: fixed worker seeds replayed
        # the same initial decks on every restart). Workers pass the
        # master's checkpoint iteration as the base; single-process resumes
        # get continuity for free because load() restores self.iteration.
        # None = legacy fixed-cursor behavior, bit-identical to before.
        self._stream_base = stream_base
        self._stream_scope = None
        if stream_base is not None:
            self._stream_scope = keyed.derive_scope(
                keyed.KIND_TRAIN, 0, seed & keyed.M64)
        if game_factory is None:
            # sb/bb are explicit because CHIP UNITS ARE PART OF THE GAME, not a
            # display choice: an external opponent fixes them (Slumbot is
            # 50/100 with a 20,000 stack), and every regret-denominated
            # hyperparameter scales with the stack IN CHIPS. self.config reads
            # them back off the engine, so the checkpoint fingerprint records
            # whatever was actually played.
            self.game = NLHE(num_players=num_players, stack=stack,
                             sb=sb, bb=bb, menu=menu, rng=self.rng)
            width = menu_width(self.game.menu)
        else:
            # oracle games (test_oracle): anything duck-typing the engine
            # surface (reset/clone/step/current/holes/board/street/
            # legal_actions/infoset_key/is_over/payoffs + n, max_actions)
            # trains through the identical update path — exactly solvable
            # games measure TRUE exploitability of this trainer's
            # averaging/pruning/admission machinery
            self.game = game_factory(self.rng)
            self.num_players = num_players = self.game.n
            width = self.game.max_actions
        self.table = SlabTable(width=width,
                               max_keys=max_infosets,
                               shared_prefix=shared_prefix,
                               create=not attach)
        self.min_visits = min_visits
        self.sketch = None
        if min_visits > 1:
            self.sketch = FrequencySketch(
                cells=sketch_cells,
                shm_name=None if shared_prefix is None
                else f"{shared_prefix}_freq",
                create=not attach)
        self.window = WindowOverlay(self.table, self.sketch, min_visits) \
            if attach else None
        self.nodes = _NodesView(self.table)
        self.iteration = 0
        self.discount_round = 0
        self.prune_threshold = prune_threshold
        self.prune_floor = 2.0 * prune_threshold
        self.prune_prob = prune_prob
        self._prune_now = None  # this traversal's single pruning coin
        # --- capacity / pruning instrumentation -------------------------
        # The day3 run was blind to all of this: the index went exactly full
        # at iteration 2,419,300 and silently dropped every newly discovered
        # infoset for the remaining 67% of the run, with one warning ever in
        # parallel mode and none at all in single-process. These counters are
        # surfaced per convergence row so the next run cannot repeat that.
        # NOTE: these count EVENTS, not distinct infosets — the same dropped
        # line is re-counted every time it is met again.
        self.n_dropped_full = 0   # admissions refused: index at capacity
        self.n_gated = 0          # sightings held back by the min_visits gate
        self.n_traversals = 0
        self.n_traversals_pruned = 0
        self.n_pruned_actions = 0
        self._index_full_warned = False
        self.discount_every = discount_every
        self.discount_until = discount_until  # None => discount forever
        if game_factory is None:
            m = self.game.menu
            self.config = {
                "num_players": num_players, "stack": stack,
                "sb": self.game.sb, "bb": self.game.bb,
                "menu": (tuple(tuple(f) for f in m.fractions), m.cap,
                         m.late_fraction),
                "prune_threshold": prune_threshold,
            }
        else:
            self.config = {"game": getattr(self.game, "name", "custom"),
                           "prune_threshold": prune_threshold}
        self.bucket_build_id = getattr(assigner, "build_id", None)

    # ------------------------------------------------------------- table access
    def _node_values(self, key, n_actions):
        """(regret, strat) working arrays for this infoset."""
        if self.window is not None:
            return self.window.node_values(key, n_actions)
        digest = key_digest(key)
        row = self.table.index.get(digest)
        if row is None:
            if (self.sketch is not None
                    and self.sketch.bump(digest) < self.min_visits):
                # not admitted yet: learn nothing for this line
                self.n_gated += 1
                return (np.zeros(n_actions), np.zeros(n_actions))
            try:
                row = self.table.assign_row(key, n_actions)
            except MemoryError:
                # index full: learn nothing for this line, keep traversing.
                # Single-process used to do this in total silence — the run
                # looked healthy while it had stopped growing entirely.
                self.n_dropped_full += 1
                if not self._index_full_warned:
                    self._index_full_warned = True
                    print("WARNING: infoset index is FULL — training "
                          "continues on existing infosets only; new lines "
                          "fall back to the play-time heuristic. Raise "
                          "--max-infosets on the next run to grow further")
                return (np.zeros(n_actions), np.zeros(n_actions))
        reg, strat, _ = self.table.row_values(row)
        return reg, strat

    # --------------------------------------------------------------- traversal
    def run_iteration(self):
        """One iteration: an external-sampling traversal for every seat."""
        self.iteration += 1
        if self._stream_scope is not None:
            self.rng.seed(keyed.u64(self._stream_scope,
                                    keyed.NS_TRAIN_ITERATION,
                                    self._stream_base + self.iteration))
        for seat in range(self.num_players):
            self.game.reset()
            self._prune_now = None  # re-flipped (lazily) per traversal
            self._traverse(self.game, seat)
            self.n_traversals += 1
            if self._prune_now:  # coin was flipped AND came up "prune"
                self.n_traversals_pruned += 1
        if self.window is None and self.iteration % self.discount_every == 0 \
                and (self.discount_until is None
                     or self.iteration <= self.discount_until):
            self.discount_round += 1
            f = self.discount_round / (self.discount_round + 1.0)
            self.discount(f)
        return self.iteration

    def _traverse(self, game, traverser):
        if game.is_over():
            return float(game.payoffs()[traverser])
        p = game.current
        legal = game.legal_actions()
        bucket = self.assigner.bucket(game.holes[p], game.board)
        key = game.infoset_key(bucket)
        reg, strat = self._node_values(key, len(legal))
        sigma = regret_matching(reg)

        if p == traverser:
            values = np.zeros(len(legal), dtype=np.float64)
            explored = np.zeros(len(legal), dtype=bool)
            for i in range(len(legal)):
                if reg[i] < self.prune_threshold and game.street < 3:
                    if self._prune_now is None:
                        # ONE coin per traversal, as in Pluribus: ~5% of
                        # traversals run fully unpruned. Flipping it per
                        # ACTION (the old behavior) meant an all-pruned node
                        # needed every one of its coins to miss before it saw
                        # a real update, so it recovered on 0.05^n_actions of
                        # visits (0.25% at two actions, not the intended 5%),
                        # and a node behind d pruned edges on 0.05^d. Worse,
                        # a node where only ONE action survives the coins
                        # gets regret delta exactly zero (v == values[i]), so
                        # partial exploration is a dead update too.
                        # Drawn lazily: while nothing sits below the
                        # threshold this consumes no randomness at all, so
                        # runs with pruning dormant stay bit-identical.
                        self._prune_now = self.rng.random() < self.prune_prob
                    if self._prune_now:
                        self.n_pruned_actions += 1
                        continue  # pruned this traversal
                child = game.clone()
                child.step(legal[i])
                values[i] = self._traverse(child, traverser)
                explored[i] = True
            if not explored.any():
                i = self.rng.randrange(len(legal))
                child = game.clone()
                child.step(legal[i])
                values[i] = self._traverse(child, traverser)
                explored[i] = True
            w = sigma[explored].sum()
            if w <= 0:
                v = values[explored].mean()
            else:
                v = float((sigma[explored] * values[explored]).sum() / w)
            for i in range(len(legal)):
                if explored[i]:
                    reg[i] = max(reg[i] + (values[i] - v), self.prune_floor)
            return v
        else:
            # sampled opponent node: accumulate average strategy, sample action
            strat += sigma
            r = self.rng.random()
            acc = 0.0
            idx = len(legal) - 1
            for i, s in enumerate(sigma):
                acc += s
                if r < acc:
                    idx = i
                    break
            game.step(legal[idx])
            return self._traverse(game, traverser)

    # ------------------------------------------------------------- discounting
    def discount(self, factor):
        """Master/single only: scale the whole table (workers idle at the
        barrier hold no window state, so nothing else needs scaling)."""
        assert self.window is None, "workers do not discount"
        self.table.discount(factor, self.prune_floor)

    # ---------------------------------------------------- multi-process barrier
    def collect_window(self, include_stats=False):
        """Worker deltas since the last barrier, optionally with telemetry.

        Parallel workers own the traversal/pruning counters; the master does
        no traversals itself. Returning and resetting deltas here makes the
        master's convergence totals truthful without changing the historical
        two-value API used by tests and callers.
        """
        pack, fresh = self.window.collect()
        if not include_stats:
            return pack, fresh
        window_stats = self.window.pop_stats()
        stats = {
            "dropped_full": self.n_dropped_full
                            + window_stats["dropped_full"],
            "gated": self.n_gated + window_stats["gated"],
            "traversals": self.n_traversals,
            "traversals_pruned": self.n_traversals_pruned,
            "pruned_actions": self.n_pruned_actions,
        }
        self.n_dropped_full = 0
        self.n_gated = 0
        self.n_traversals = 0
        self.n_traversals_pruned = 0
        self.n_pruned_actions = 0
        return pack, fresh, stats

    def add_worker_stats(self, stats):
        """Master: aggregate one worker's barrier telemetry."""
        self.n_dropped_full += int(stats.get("dropped_full", 0))
        self.n_gated += int(stats.get("gated", 0))
        self.n_traversals += int(stats.get("traversals", 0))
        self.n_traversals_pruned += int(stats.get("traversals_pruned", 0))
        self.n_pruned_actions += int(stats.get("pruned_actions", 0))

    def apply_windows(self, packs, freshes):
        """Master: fold in every worker's window exactly once, then floor the
        touched rows — elementwise max(T + sum(deltas), floor), identical for
        every process because there is only one table."""
        touched = [p[0] for p in packs if len(p[0])]
        fresh_rows = []
        merged = {}
        for fresh in freshes:
            for key, (reg, strat, n) in fresh.items():
                ent = merged.get(key)
                if ent is None:
                    merged[key] = [reg.copy(), strat.copy(), n]
                else:
                    if ent[2] != n:
                        raise ValueError(f"action-count mismatch for fresh "
                                         f"infoset {key!r}")
                    ent[0] += reg
                    ent[1] += strat
        items = list(merged.items())
        for i, (key, (reg, strat, n)) in enumerate(items):
            try:
                row = self.table.assign_row(key, n)
            except MemoryError:
                # `break` abandons every REMAINING fresh infoset in this
                # barrier, not just this one — count them all, or the drop
                # rate reads ~1 per barrier instead of the true figure
                self.n_dropped_full += len(items) - i
                if not self._index_full_warned:
                    self._index_full_warned = True
                    print("WARNING: infoset index is FULL — training "
                          "continues on existing infosets only; new lines "
                          "fall back to the play-time heuristic. Raise "
                          "--max-infosets on the next run to grow further")
                break
            r, s, _ = self.table.row_values(row)
            r += reg
            s += strat
            fresh_rows.append(row)
        for pack in packs:
            self.table.apply_pack(*pack)
        if touched or fresh_rows:
            rows = np.concatenate(touched + [np.asarray(fresh_rows,
                                                        dtype=np.int64)])
            self.table.floor_rows(np.unique(rows), self.prune_floor)

    # ------------------------------------------------------------- persistence
    def save(self, path):
        self.table.save_dir(path, {
            "iteration": self.iteration,
            "discount_round": self.discount_round,
            "num_players": self.num_players,
            "config": self.config,
            "bucket_build_id": self.bucket_build_id,
        })

    def _check_meta(self, meta, path, require_fingerprint,
                    allow_prune_threshold_change=False, apply_state=True):
        cfg = meta.get("config")
        if isinstance(cfg, dict) and "menu" in cfg:
            # json round-trips tuples as lists; normalize for comparison
            fr, cap, late = cfg["menu"]
            cfg = dict(cfg, menu=(tuple(tuple(f) for f in fr), cap, late))
        if require_fingerprint and cfg is None:
            raise ValueError(
                f"{path} is a legacy checkpoint without a config/abstraction "
                f"fingerprint — it cannot be safely resumed against the "
                f"current abstraction. Move it away to start fresh")
        threshold_change = None
        if cfg is not None and cfg != self.config:
            diffs = {k: (cfg.get(k), self.config.get(k))
                     for k in set(cfg) | set(self.config)
                     if cfg.get(k) != self.config.get(k)}
            if (allow_prune_threshold_change
                    and set(diffs) == {"prune_threshold"}):
                threshold_change = diffs["prune_threshold"]
            else:
                hint = (" Pass --allow-prune-threshold-change to explicitly "
                        "migrate only that training setting."
                        if set(diffs) == {"prune_threshold"} else "")
                raise ValueError(
                    f"checkpoint config mismatch (checkpoint vs current): "
                    f"{diffs} — resuming would silently corrupt the tables."
                    f"{hint}")
        ckpt_build = meta.get("bucket_build_id")
        if (ckpt_build is not None and self.bucket_build_id is not None
                and ckpt_build != self.bucket_build_id):
            raise ValueError(
                "checkpoint was trained under a different bucket abstraction "
                "(centroids rebuilt since). Delete/move the checkpoint or "
                "restore the matching buckets/ build")
        if cfg is None and apply_state:
            print("WARNING: legacy checkpoint without a config fingerprint — "
                  "cannot verify it matches this game/abstraction")
        if apply_state:
            self.iteration = meta["iteration"]
            self.discount_round = meta["discount_round"]
        return threshold_change

    def load(self, path, require_fingerprint=False,
             allow_prune_threshold_change=False):
        if os.path.isdir(path):
            # Validate the cheap metadata and all file sizes before reading
            # the multi-gigabyte index/slabs. A bad CLI setting now fails in
            # milliseconds instead of after loading a 17 GB checkpoint.
            meta = self.table.preflight_dir(path)
            change = self._check_meta(
                meta, path, require_fingerprint,
                allow_prune_threshold_change, apply_state=False)
            self.table.load_dir(path, meta=meta)
            self._check_meta(meta, path, require_fingerprint,
                             allow_prune_threshold_change, apply_state=True)
            if change is not None:
                old, new = change
                old_floor = 2.0 * float(old)
                if self.prune_floor > old_floor:
                    self.table.floor_all(self.prune_floor)
                    detail = f"regrets clamped at {self.prune_floor:g}"
                else:
                    detail = "existing regrets need no clamp"
                print(f"prune-threshold migration: {old:g} -> {new:g}; "
                      f"{detail}")
            return
        with open(path, "rb") as f:  # legacy single-pickle checkpoint
            state = pickle.load(f)
        change = self._check_meta(state, path, require_fingerprint,
                                  allow_prune_threshold_change)
        self.table.load_legacy_nodes(state["nodes"])
        if change is not None:
            old, new = change
            if self.prune_floor > 2.0 * float(old):
                self.table.floor_all(self.prune_floor)
                detail = f"regrets clamped at {self.prune_floor:g}"
            else:
                detail = "existing regrets need no clamp"
            print(f"prune-threshold migration: {old:g} -> {new:g}; "
                  f"{detail}")


def resolve_checkpoint(run_dir, name="blueprint"):
    """Preferred checkpoint path in run_dir: new dir format, else legacy pkl,
    else None. REFUSES to answer None while a stranded .bak/.tmp exists —
    that state means a save was interrupted mid-swap, and silently
    starting fresh would let the new run's second save rmtree the parked
    last-good checkpoint (ultracode audit 2026-08-12)."""
    d = os.path.join(run_dir, f"{name}_ckpt")
    rescue = d + "_rescue"
    if os.path.isdir(d):
        if os.path.isdir(rescue):
            try:
                def iteration(path):
                    with open(os.path.join(path, "meta.json")) as f:
                        return int(json.load(f)["iteration"])
                if iteration(rescue) > iteration(d):
                    print(f"WARNING: {rescue} is newer than {d}; resuming "
                          f"the rescue checkpoint automatically")
                    return rescue
            except (OSError, ValueError, KeyError, json.JSONDecodeError) as e:
                print(f"WARNING: ignoring unreadable rescue checkpoint "
                      f"{rescue}: {e}")
        return d
    for stranded in (d + ".bak", d + ".tmp"):
        if os.path.isdir(stranded):
            raise SystemExit(
                f"{d} is missing but {stranded} exists — a checkpoint swap "
                f"was interrupted. Inspect it and rename the good copy back "
                f"to {d} (or move it away to really start fresh). Refusing "
                f"to continue: a fresh run would silently destroy it.")
    p = os.path.join(run_dir, f"{name}.pkl")
    if os.path.isdir(rescue):
        return rescue
    if os.path.exists(p):
        return p
    return None


class BlueprintPolicy:
    """Playable average strategy from a trained (or in-training) table.

    Play-time hygiene (Ganzfried & Sandholm 2012; Pluribus did the same):
    probabilities below `threshold` are zeroed and the rest renormalized —
    sampled MCCFR leaves noise mass on never-really-explored actions.
    Untrained infosets fall back to a pot-odds heuristic instead of uniform
    random.

    Accepts: a checkpoint DIRECTORY (new format), a legacy .pkl path, a
    trainer's .nodes view, or a plain dict of Nodes (tests/search).
    """

    def __init__(self, source, assigner, rng=None, threshold=0.05,
                 loader="auto", track_rows=False):
        self._track_rows = track_rows
        self._slab = None
        self._owns_slab = False  # never close a trainer's live table
        self.loader = None       # which path actually loaded (dumps record it)
        self.table = None
        self.meta_players = None
        self.config = None
        self.bucket_build_id = None
        self.ckpt_iteration = None  # checkpoint identity (searchab dumps)
        # where this policy came from, for run fingerprints. searchab's
        # fingerprint records only os.path.basename, so two directories
        # sharing a basename collide and resume pools incompatible rows.
        self.source_path = source if isinstance(source, str) else None
        if isinstance(source, str):
            if os.path.isdir(source):
                with open(os.path.join(source, "meta.json")) as f:
                    meta = json.load(f)
                self._slab = self._open_dir(source, meta, loader)
                self._owns_slab = True
                self._set_meta(meta)
            else:
                with open(source, "rb") as f:
                    state = pickle.load(f)
                self.table = {k: np.asarray(v[1], dtype=np.float64)
                              for k, v in state["nodes"].items()}
                self._set_meta(state)
        elif isinstance(source, _NodesView):
            self._slab = source._t
        else:
            self.table = {k: n.strat for k, n in source.items()}
        self.assigner = assigner
        self.rng = rng or random.Random()
        self.threshold = threshold
        # coverage tallies per street (2026-08-12 review: table SIZE is
        # not COVERAGE): queries land where play actually goes, so these
        # are reach-weighted by construction. hit = trained row used;
        # miss = no row (unknown line); bad = row unusable (zero mass or
        # action-count mismatch). Every consumer of probabilities()
        # counts — table play, range updates, search continuations.
        self.q_hit = [0, 0, 0, 0]
        self.q_miss = [0, 0, 0, 0]
        self.q_bad = [0, 0, 0, 0]

    def _open_dir(self, source, meta, loader):
        """Eval-only loader when a valid sidecar exists, else the full table.

        `loader="eval"` is REQUIRED for verdict runs and multi-worker
        searchab: without it a missing sidecar silently falls back to a
        28.85 GiB load (38.80 on day4 raw), or to twelve of them. An
        INVALID sidecar is always fatal — only an ABSENT one may fall back.
        """
        if loader not in ("auto", "eval", "full"):
            raise ValueError(f"unknown loader {loader!r}")
        if loader != "full":
            try:
                t = EvalTable(source, track_rows=self._track_rows)
                self.loader = "eval"
                return t
            except SidecarUnavailable:
                # absent, or a trainer-managed path the eval loader refuses
                # to map. Nothing is wrong — the fast path does not apply.
                # play.py and eval_blueprint default to resolve_checkpoint(),
                # which returns the LIVE blueprint_ckpt, so this is the
                # ordinary case for both and must not raise.
                if loader == "eval":
                    raise
            except SidecarError:
                raise  # stale/malformed: never degrade silently
        slab = SlabTable(width=meta["width"],
                         max_keys=max(meta["rows"], 1024))
        slab.load_dir(source)
        self.loader = "full"
        return slab

    def close(self):
        """Release checkpoint mappings. Required before any rename/delete of
        the artifact on Windows, and worth doing between league agents."""
        if self._owns_slab and self._slab is not None:
            self._slab.close()
        self._slab = None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False

    def _set_meta(self, meta):
        self.meta_players = meta.get("num_players")
        self.ckpt_iteration = meta.get("iteration")
        cfg = meta.get("config")
        if isinstance(cfg, dict) and "menu" in cfg:
            fr, cap, late = cfg["menu"]
            cfg = dict(cfg, menu=(tuple(tuple(f) for f in fr), cap, late))
        self.config = cfg
        self.bucket_build_id = meta.get("bucket_build_id")

    def size(self):
        """Number of infosets the policy can look up."""
        if self._slab is not None:
            return self._slab.rows
        return len(self.table)

    def _strat_for(self, key):
        if self._slab is not None:
            row = self._slab.lookup(key)
            if row is None:
                return None
            _, strat, n = self._slab.row_values(row)
            return strat
        return self.table.get(key)

    def probabilities(self, game, hole=None, bucket=None, raw=False):
        """Average-strategy distribution over legal actions for game.current.

        `hole` substitutes the acting player's cards — used by range trackers
        asking "what would the blueprint do here holding h?". Passing
        `bucket` directly skips the assigner: probabilities depend on the
        hole only through its bucket, so range-wide sweeps compute one
        distribution per distinct bucket instead of per hole. `raw=True`
        skips play-time purification — consumers modeling future behavior
        (search leaf continuations) need the unthresholded average, since
        thresholding zeroes exactly the low-mass actions the fold/raise
        biases exist to amplify."""
        probs, status = self.probabilities_with_status(game, hole, bucket, raw)
        if status == "miss":
            self.q_miss[game.street] += 1
        elif status == "bad":
            self.q_bad[game.street] += 1
        else:
            self.q_hit[game.street] += 1
        return probs

    # A normalized row within this of uniform is uniform. Rows reached only
    # as sampled OPPONENT nodes accumulate strat but never regret, and
    # regret_matching(zeros) returns uniform: measured across 254,077 such
    # rows the max deviation from exactly uniform was 5.6e-17, so exact
    # equality would misclassify every one of them as trained.
    UNIFORM_TOL = 1e-12

    def probabilities_with_status(self, game, hole=None, bucket=None,
                                  raw=False):
        """(probs, status) with NO tally mutation — status is one of
        "trained" / "uniform" / "miss" / "bad".

        `probabilities()` is this plus the tallies, so the two can never
        drift. Callers that sweep hypothetical holes (the river audit asks
        for every non-conflicting combo at every node) must use THIS one:
        those queries never happened at a table and must not enter
        coverage_report(), and stratifying results by fallback status must
        not be reverse-engineered from deltas in a global counter.

        "uniform" is separate from "trained" deliberately. A row that exists
        but serves exactly uniform is not strategy, and scoring it as
        coverage is the error that cost this project a headline statistic.
        """
        p = game.current
        legal = game.legal_actions()
        if bucket is None:
            bucket = self.assigner.bucket(
                hole if hole is not None else game.holes[p], game.board)
        strat = self._strat_for(game.infoset_key(bucket))
        if strat is None:
            return self._fallback(game, legal), "miss"
        # Finiteness and sign must be checked BEFORE normalizing. `NaN <= 0`
        # is False, so a NaN row passes a mass check, normalizes to all-NaN,
        # and then `NaN <= UNIFORM_TOL` is also False — the row is returned
        # as an all-NaN distribution labelled "trained". A row like [-1, 3]
        # sums positive and normalizes to a negative probability.
        if (len(strat) != len(legal) or not np.isfinite(strat).all()
                or (strat < 0).any() or strat.sum() <= 0):
            return self._fallback(game, legal), "bad"
        probs = strat / strat.sum()
        status = ("uniform"
                  if float(probs.max() - probs.min()) <= self.UNIFORM_TOL
                  else "trained")
        if self.threshold > 0.0 and not raw:
            kept = np.where(probs >= self.threshold, probs, 0.0)
            s = kept.sum()
            if s > 0:
                probs = kept / s
        return probs, status

    @staticmethod
    def _fallback(game, legal):
        """Untrained infoset: check when free, call getting 2:1+ pot odds,
        otherwise fold. Never bluffs chips into a line it knows nothing about."""
        probs = np.zeros(len(legal))
        to_call = game.to_call(game.current)
        if to_call == 0 or 2 * to_call <= game.pot:
            probs[legal.index(CHECK_CALL)] = 1.0
        else:
            probs[legal.index(FOLD)] = 1.0
        return probs

    def coverage_report(self):
        """One line of per-street policy coverage over the queries made so
        far (reach-weighted by construction — see the tally comment)."""
        names = ("preflop", "flop", "turn", "river")
        parts = []
        for s in range(4):
            n = self.q_hit[s] + self.q_miss[s] + self.q_bad[s]
            if n:
                parts.append(f"{names[s]} {self.q_hit[s] / n:.1%} of "
                             f"{n:,} (miss {self.q_miss[s]:,}, bad "
                             f"{self.q_bad[s]:,})")
        return " | ".join(parts) if parts else "no policy queries"

    def act(self, game):
        legal = game.legal_actions()
        probs = self.probabilities(game)
        r = self.rng.random()
        acc = 0.0
        for i, pr in enumerate(probs):
            acc += pr
            if r < acc:
                return legal[i]
        return legal[-1]
