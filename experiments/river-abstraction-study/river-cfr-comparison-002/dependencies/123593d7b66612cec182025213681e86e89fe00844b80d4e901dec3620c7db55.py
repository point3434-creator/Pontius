"""Public-history range construction for the river audit (harness 3, step 2).

`RangeTracker` (search.py:84) is deliberately NOT reused and NOT modified.
It is observer-relative — `dead = set(game.holes[hero])` removes the chosen
hero's two actual cards from EVERY tracked seat's range including its own
(search.py:87-89), which is private information leaking into what must be a
public quantity; measured, that leaves 990 of 1081 combos, and the 91 it
drops are exactly the ones containing a hero card. It also floors each
per-step likelihood in place with no record (search.py:153) and silently
resets a collapsed range to uniform (search.py:161-163). Those choices are
right for sampled search and its bit-pinned golden traces, and wrong here;
retrofitting would change behaviour those traces pin exactly.

WHAT THIS BUILDS. For each seat, a weight over EVERY two-card combo, formed
by multiplying day4's own purified action probabilities along the observed
public history. No realized private cards enter: all C(52,2) combos start
alive for every seat, and only PUBLIC board cards remove any. The two live
seats' ranges are independent marginals; the solver applies pairwise
disjointness (river_solver.py:130). Folded players' action-conditioned card
removal is NOT jointly marginalized, which is why the estimand says
"blueprint-factorized public range model".

D4 (ROADMAP, settled 2026-08-14) — TWO quantities, never conflated:

  raw       the exact product of day4's actual probabilities, zeros and
            all. This is the fidelity record: the audit stays exact
            because it is preserved.
  effective max(raw, floor) for ELIGIBLE combos only, renormalized. This
            is the estimator: without it, a purification-induced zero
            collapses a range, the state becomes unauditable, and dropping
            it biases the audit toward well-covered states — the same
            direction as dropping fallback states.

STRUCTURAL zeros are never floored. A combo containing a public board card
is logically impossible and zero is correct for it. The floor exists only
where purification or finite precision zeroed an otherwise eligible combo.

Every floor application and the probability mass it adds are recorded, as
is per-combo provenance (trained / uniform / miss / bad), because a range
built mostly from the card-blind fallback means something different from
one built from trained rows.

ORDER OF OPERATIONS, and it matters: normalize, THEN floor, THEN
renormalize. `raw` is an unnormalized product whose scale depends on how
many actions the hand contained, so an absolute floor applied to it would
mean different things at different histories. Normalizing first makes the
floor scale-invariant — at ~1081 combos a typical normalized weight is
~1e-3, so the primary floor of 1e-6 touches only genuinely tiny weights.
This is an interpretation of D4's text, which specifies the floor and the
renormalization but not the leading normalization.
"""
import itertools

import numpy as np

ALL_COMBOS = tuple(itertools.combinations(range(52), 2))
COMBO_ID = {c: i for i, c in enumerate(ALL_COMBOS)}
N_ALL = len(ALL_COMBOS)                      # 1326

PRIMARY_FLOOR = 1e-6         # matches search.py's PROB_FLOOR
SENSITIVITY_FLOOR = 1e-9     # the second value D4 requires reporting

STATUSES = ("trained", "uniform", "miss", "bad")


class RangeCollapsed(Exception):
    """Every eligible combo reached exactly zero raw weight. Never reset to
    uniform silently (search.py:161-163 does; that is the behaviour this
    module exists to avoid) — the caller must count it as a category."""


class PublicRange:
    """One seat's public-history range over all C(52,2) combos."""

    def __init__(self):
        self.raw = np.ones(N_ALL, dtype=np.float64)
        self.structural = np.zeros(N_ALL, dtype=bool)   # holds a board card
        self.counts = {k: np.zeros(N_ALL, dtype=np.int64) for k in STATUSES}
        self.n_observations = 0

    # ------------------------------------------------------------- updates
    def remove_board(self, new_cards):
        """Public cards make every combo containing them impossible. This is
        a STRUCTURAL zero and is never floored."""
        if not new_cards:
            return
        s = set(new_cards)
        hit = np.array([(c[0] in s or c[1] in s) for c in ALL_COMBOS])
        self.structural |= hit
        self.raw[hit] = 0.0

    def observe(self, policy, buckets, game, action_index):
        """Multiply by day4's probability of the observed action, per combo.

        `buckets` is the hole->bucket array for the CURRENT board, computed
        once per board by the caller and shared across seats. Queries are
        grouped by bucket — day4's distribution is a function of the bucket
        alone — so this costs one policy query per DISTINCT bucket rather
        than one per combo.
        """
        live = ~self.structural
        if live.any() and int(buckets[live].min()) < 0:
            raise ValueError(
                "a live combo has no bucket (-1): the structural marks and "
                "the board used for bucketing disagree")
        for b in np.unique(buckets[live]):
            probs, status = policy.probabilities_with_status(game,
                                                             bucket=int(b))
            sel = live & (buckets == int(b))
            self.raw[sel] *= float(probs[action_index])
            self.counts[status][sel] += 1
        self.n_observations += 1

    # -------------------------------------------------------------- output
    def vector(self, cix, floor=PRIMARY_FLOOR):
        """(effective weights over cix.combos, stats).

        Normalize -> floor eligible combos -> renormalize. `raw` is kept
        untouched so the same build serves the primary and the
        lower-floor sensitivity configuration.
        """
        ids = np.array([COMBO_ID[c] for c in cix.combos], dtype=np.int64)
        if self.structural[ids].any():
            raise ValueError(
                "a combo in this ComboIndex is structurally impossible — the "
                "index and the observed board disagree")
        raw = self.raw[ids]
        total = float(raw.sum())
        stats = {"combos": len(ids), "raw_sum": total,
                 "raw_zeros": int((raw <= 0).sum()),
                 "floor": floor, "collapsed": False}
        if total <= 0:
            stats["collapsed"] = True
            if floor <= 0:
                # ATTRITION config. An empty range is the DATUM here: this
                # is the state the floor exists to rescue, so substituting
                # uniform would make the diagnostic report the opposite of
                # what it measures — all three floor configs would return
                # identical values on exactly the states that distinguish
                # them. Return the zeros and let the caller count it.
                stats["floor_applications"] = 0
                stats["floor_mass_added"] = 0.0
                return np.zeros(len(ids)), stats
            # every eligible combo is a purification zero. Flooring makes
            # this uniform; that is a real answer under D4 but it must be
            # REPORTED, never quietly produced.
            stats["floor_applications"] = len(ids)
            stats["floor_mass_added"] = 1.0
            return np.full(len(ids), 1.0 / len(ids)), stats
        p = raw / total
        below = p < floor
        eff = np.where(below, floor, p)
        stats["floor_applications"] = int(below.sum())
        stats["floor_mass_added"] = float((eff - p).sum())
        eff = eff / eff.sum()                       # explicit renormalization
        stats["max_weight"] = float(eff.max())
        return eff, stats

    def provenance(self, cix):
        """Per-combo observation counts by source, restricted to cix."""
        ids = np.array([COMBO_ID[c] for c in cix.combos], dtype=np.int64)
        tot = {k: int(self.counts[k][ids].sum()) for k in STATUSES}
        n = sum(tot.values())
        # combo_observations, NOT "queries": this counts combo x observation
        # cells, roughly 20x the actual policy traffic, because queries are
        # grouped by bucket. Quoting it as a query count overstates policy
        # load by an order of magnitude.
        out = dict(tot, observations=self.n_observations,
                   combo_observations=n)
        out["fallback_frac"] = (tot["miss"] + tot["bad"]) / n if n else 0.0
        out["uniform_frac"] = tot["uniform"] / n if n else 0.0
        out["trained_frac"] = tot["trained"] / n if n else 0.0
        return out


def bucket_array(assigner, board):
    """hole -> bucket for every combo on one board; -1 where the combo
    contains a board card.

    Board-conflicting combos MUST be skipped, not merely ignored later.
    `assigner.bucket` reaches `hand_rank` (evaluator.py:19), whose C
    evaluator is handed `hole + board` with a DUPLICATE card and takes an
    access violation — a segfault, not an exception, so no campaign loop
    can catch or count it. Measured: this killed the process mid-run while
    the two states before it had silently computed garbage bucket ids that
    happened never to be read.

    RangeTracker never hit this because observe_board deletes conflicting
    combos before bucketing (search.py:101-110), and river_audit's
    bucket_table iterates cix.combos, which excludes the board by
    construction. Only a sweep over ALL C(52,2) combos is exposed.
    """
    dead = set(board)
    out = np.full(N_ALL, -1, dtype=np.int64)
    for i, c in enumerate(ALL_COMBOS):
        if c[0] not in dead and c[1] not in dead:
            out[i] = assigner.bucket(list(c), board)
    return out


def build_public_ranges(policy, assigner, game, deck, actions, seats,
                        stop_at=None):
    """Replay a captured hand and accumulate public ranges for `seats`.

    `deck` + `actions` reconstruct the hand exactly — the engine consumes no
    randomness on replay — so this draws nothing and cannot perturb any
    caller's stream. Building only the seats that survive to the stop state
    (known from the capture) is what keeps the cost down: every other seat's
    range is discarded anyway.

    Returns (game_at_stop, {seat: PublicRange}). `stop_at(game)` decides
    where to stop; the action at the stop state is NOT observed.
    """
    game.reset(deck=deck)
    ranges = {s: PublicRange() for s in seats}
    board_seen = 0
    buckets = None
    board_key = None
    for entry in actions:
        # An entry is either a menu action id, or (abs_action, real_target)
        # for an OFF-MENU raise. Both forms are needed at play time: a human
        # (or any off-menu opponent) puts in exact chips while the blueprint
        # can only be conditioned on the menu id the raise translates to, so
        # replaying the menu id alone would reconstruct the wrong pot and
        # stacks for every later street. Bot-vs-bot callers pass plain ints
        # and this branch never fires.
        if isinstance(entry, tuple):
            a, real_target = entry
        else:
            a, real_target = entry, None
        if game.is_over():
            break
        if len(game.board) > board_seen:
            new = list(game.board[board_seen:])
            for r in ranges.values():
                r.remove_board(new)
            board_seen = len(game.board)
        if stop_at is not None and stop_at(game):
            return game, ranges
        seat = game.current
        r = ranges.get(seat)
        if r is not None:
            key = tuple(game.board)
            if key != board_key:
                buckets = bucket_array(assigner, list(game.board))
                board_key = key
            legal = game.legal_actions()
            try:
                i = legal.index(a)
            except ValueError:      # off-menu action: nothing to condition on
                i = None
            if i is not None:
                r.observe(policy, buckets, game, i)
        if real_target is None:
            game.step(a)
        else:
            game.step_raise_to(real_target)
    if len(game.board) > board_seen:
        for r in ranges.values():
            r.remove_board(list(game.board[board_seen:]))
    return game, ranges
