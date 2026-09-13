"""Dense exact heads-up river solver: vector-form CFR+ over combo ranges.

WHY (ROADMAP "corrected search-track ordering"): the sampled re-solver
pins the hero's ACTUAL hand every iteration, so it never produces
P(a|h) for the hero's counterfactual hands and the hero's public range
cannot be updated coherently from search output. This solver is the
enabling infrastructure for coherent nested search — and the measured
CFR+ dense-solve speedup lives here, not under action sampling (chance-
sampled CFR+ was at parity with LCFR; see test_search).

Shape: the public board owns a ComboIndex over its unseen cards — river
C(47,2)=1081 combos (turn 1128, flop 1176). Both players' ranges are
length-n vectors over that index; every decision node carries dense
[n_combos, n_actions] regret/strategy arrays, so ONE solve yields a
strategy for every hand either player could hold.

Exact terminals: the betting tree is built by stepping real engine
clones, so chip accounting is the engine's own. Fold terminals read
engine.payoffs() directly (hole-independent: refunds included).
Showdown terminals score combo-vs-combo with the terminal's exact chip
scalars: win = c + dead, lose = -c, tie = the dead-money split with the
odd chip to the LOWER seat — matching engine payoffs to the chip
(cross-checked in test_river_solver against engine.payoffs() with
injected holes).

Terminal evaluation is O(n) per terminal, NOT an n x n mat-vec: combos
are pre-sorted by hand rank into tie blocks, and per-call prefix sums
over (block, card) — np.bincount, one pass — give each combo the
opponent weight strictly below / tied / above it among DISJOINT combos
via inclusion-exclusion on its two cards (a j sharing both cards is i
itself, which the collision rule excludes). The first draft's dense
mat-vec (~1 s/iteration at stack 100) measured ~50x slower; the dense
matrices remain available through showdown_masks() and a parity test
pins the prefix path to them bit-tight.

No randomness anywhere: CFR+ over ranges is deterministic, so solves
compose with the keyed-CRN evaluation layer for free. GPU/numba only
after the CPU benchmark in test_river_solver says so (ROADMAP).
"""
import itertools

import numpy as np

from .evaluator import hand_rank


class ComboIndex:
    """Enumeration of two-card combos over the cards a public board leaves
    unseen, in deterministic lexicographic combo-id order, plus the
    pairwise collision mask (test/reference use — the solve path never
    materializes n x n products). Owned by the BOARD: every range vector
    and strategy matrix in a solve is indexed by this object."""

    def __init__(self, board):
        self.board = tuple(board)
        dead = set(self.board)
        self.cards = [c for c in range(52) if c not in dead]
        self.combos = list(itertools.combinations(self.cards, 2))
        self.n = len(self.combos)
        self.id_of = {c: k for k, c in enumerate(self.combos)}
        self.card_a = np.array([c[0] for c in self.combos], dtype=np.int64)
        self.card_b = np.array([c[1] for c in self.combos], dtype=np.int64)
        self._mask = None

    @property
    def mask(self):
        """n x n disjointness mask (built lazily; tests/reference only —
        the solve path never materializes n x n anything)."""
        if self._mask is None:
            a, b = self.card_a, self.card_b
            self._mask = ((a[:, None] != a[None, :])
                          & (a[:, None] != b[None, :])
                          & (b[:, None] != a[None, :])
                          & (b[:, None] != b[None, :]))
        return self._mask

    def range_vector(self, weights):
        """Dense weight vector from a {(lo_card, hi_card): w} dict (the
        RangeTracker representation). Combos touching the board must
        already be absent; unknown pairs raise."""
        v = np.zeros(self.n, dtype=np.float64)
        for pair, w in weights.items():
            v[self.id_of[pair]] = w
        return v


class BoardEval:
    """Per-board machinery for O(n) exact terminal evaluation.

    Combos are sorted by 7-card hand rank into tie BLOCKS. For a reach
    vector r, one bincount over (card, block) cells plus a cumsum yields,
    for every combo i with cards (a, b):

      below_i = sum of r_j over DISJOINT j ranked strictly worse
      tie_i   = ... in i's own block (i itself never counted)
      above_i = ... ranked strictly better

    each via inclusion-exclusion: subtract the same-cell sums for a and
    for b; the only combo sharing BOTH cards is i itself, which never
    belongs to the corrected set (or is added back explicitly for the
    disjoint total). Exact in float64: chips are small integers times
    products of range weights."""

    def __init__(self, cix, full_board):
        board = list(full_board)
        ranks = np.array([hand_rank(list(c) + board) for c in cix.combos],
                         dtype=np.int64)
        order = np.argsort(ranks, kind="stable")
        sr = ranks[order]
        new_block = np.concatenate(([True], sr[1:] != sr[:-1]))
        blk_sorted = np.cumsum(new_block) - 1
        self.n_blocks = int(blk_sorted[-1]) + 1
        self.blk = np.empty(cix.n, dtype=np.int64)
        self.blk[order] = blk_sorted  # block id per ORIGINAL combo id
        self.card_a, self.card_b = cix.card_a, cix.card_b
        self.ranks = ranks
        self._flat_a = self.card_a * self.n_blocks + self.blk
        self._flat_b = self.card_b * self.n_blocks + self.blk

    def card_sums(self, r):
        """sum of r_j over combos containing each card — 52-vector."""
        return (np.bincount(self.card_a, weights=r, minlength=52)
                + np.bincount(self.card_b, weights=r, minlength=52))

    def disjoint_total(self, r):
        """For each combo i: sum of r_j over combos disjoint from i."""
        ct = self.card_sums(r)
        return r.sum() - ct[self.card_a] - ct[self.card_b] + r

    def split(self, r):
        """(below, tie, above) opponent weight per combo, disjoint-only."""
        B = self.n_blocks
        blk_sum = np.bincount(self.blk, weights=r, minlength=B)
        blk_below = np.concatenate(([0.0], np.cumsum(blk_sum)[:-1]))
        cell = np.bincount(np.concatenate((self._flat_a, self._flat_b)),
                           weights=np.concatenate((r, r)),
                           minlength=52 * B).reshape(52, B)
        cell_below = np.concatenate(
            (np.zeros((52, 1)), np.cumsum(cell, axis=1)[:, :-1]), axis=1)
        a, b, blk = self.card_a, self.card_b, self.blk
        below = (blk_below[blk] - cell_below[a, blk] - cell_below[b, blk])
        tie = (blk_sum[blk] - cell[a, blk] - cell[b, blk] + r)
        above = self.disjoint_total(r) - below - tie
        return below, tie, above


def showdown_masks(cix, full_board):
    """Reference n x n (win, lose, tie) matrices, collision mask applied:
    win[i, j] = 1 iff combo i beats combo j and they share no card. The
    solve path never touches these — they exist so tests can pin the
    O(n) prefix evaluation to the exhaustive definition."""
    board = list(full_board)
    ranks = np.array([hand_rank(list(c) + board) for c in cix.combos],
                     dtype=np.int64)
    diff = ranks[:, None] - ranks[None, :]
    m = cix.mask
    return (((diff > 0) & m).astype(np.float64),
            ((diff < 0) & m).astype(np.float64),
            ((diff == 0) & m).astype(np.float64))


class _Decision:
    __slots__ = ("seat", "legal", "children", "regret", "strat")

    def __init__(self, seat, legal, children, n_combos):
        self.seat = seat
        self.legal = legal
        self.children = children
        self.regret = np.zeros((n_combos, len(legal)), dtype=np.float64)
        self.strat = np.zeros((n_combos, len(legal)), dtype=np.float64)


class _Fold:
    """Hand ended by a fold: payoff per seat is a combo-independent chip
    scalar straight from engine.payoffs() (refund rule included)."""
    __slots__ = ("pay",)

    def __init__(self, pay):
        self.pay = pay  # (payoff of lower live seat, of higher live seat)


class _Showdown:
    """Both live hands revealed: exact chip outcomes from the board's
    rank order and this terminal's commit scalars."""
    __slots__ = ("win_amt", "lose_amt", "tie_pay")

    def __init__(self, c, dead, tie_pay):
        self.win_amt = float(c + dead)
        self.lose_amt = float(c)
        # dead money splits; the engine gives the odd chip to the LOWER
        # seat index: tie_pay[0] for the lower live seat, [1] the higher
        self.tie_pay = tie_pay


class DenseRiverSolver:
    """Vector CFR+ on one river subgame with exactly two live players.

    game: an NLHE state on street 3 (river dealt) at a live decision.
    ranges: {seat: weight dict or vector} for BOTH live seats, indexed by
    (or convertible through) this board's ComboIndex. Weights need not be
    normalized. run(), then read per-combo average strategies.
    """

    def __init__(self, game, ranges, cix=None):
        if game.street != 3 or game.is_over():
            raise ValueError("solver wants a live river decision")
        live = game.active_players()
        if len(live) != 2:
            raise ValueError(f"heads-up only (live={live})")
        self.seats = tuple(live)  # ascending seat order by construction
        self.cix = cix or ComboIndex(game.board)
        if len(self.cix.board) != 5:
            raise ValueError("river board must have 5 cards")
        self.board_eval = BoardEval(self.cix, game.full_board)
        self.dead = sum(game.committed[s] for s in range(game.n)
                        if s not in live)
        self.ranges = {}
        for s in live:
            r = ranges[s]
            r = r if isinstance(r, np.ndarray) else self.cix.range_vector(r)
            if r.shape != (self.cix.n,) or (r < 0).any() or r.sum() <= 0:
                raise ValueError(f"bad range for seat {s}")
            self.ranges[s] = r.astype(np.float64)
        self.root = self._build(game)
        self.iteration = 0

    # ------------------------------------------------------------ tree
    def _build(self, g):
        if g.is_over():
            live = g.active_players()
            if len(live) == 1:  # fold ended it: chips are combo-free
                pay = g.payoffs()
                return _Fold((float(pay[self.seats[0]]),
                              float(pay[self.seats[1]])))
            c = g.committed[self.seats[0]]
            assert c == g.committed[self.seats[1]], "live commits equal"
            share, rem = divmod(2 * c + self.dead, 2)
            return _Showdown(c, self.dead,
                             (float(share - c + rem), float(share - c)))
        legal = g.legal_actions()
        children = []
        for a in legal:
            child = g.clone()
            child.step(a)
            children.append(self._build(child))
        return _Decision(g.current, legal, children, self.cix.n)

    # ----------------------------------------------------------- values
    def _term_val(self, node, seat, opp_reach):
        """Counterfactual chip values [n_combos] for `seat` at a terminal,
        opponent reach unnormalized (range weight x strategy products)."""
        lo = seat == self.seats[0]
        if isinstance(node, _Fold):
            return (node.pay[0 if lo else 1]
                    * self.board_eval.disjoint_total(opp_reach))
        below, tie, above = self.board_eval.split(opp_reach)
        return (node.win_amt * below - node.lose_amt * above
                + node.tie_pay[0 if lo else 1] * tie)

    @staticmethod
    def _rm_plus(regret):
        """Regret matching over floored regrets, uniform where empty."""
        s = regret.sum(axis=1, keepdims=True)
        n_a = regret.shape[1]
        return np.where(s > 0, regret / np.where(s > 0, s, 1.0), 1.0 / n_a)

    def _sigma(self, node):
        """Current strategy at a decision node.

        A hook, not indirection for its own sake: a solver that pins some
        combo rows to a fixed distribution (river_oracle's constrained
        seat) must override the strategy EVERY iteration, and the only
        alternative is duplicating _walk — the one method whose exact
        recursion the zero-reach-branch fix pins by test.
        """
        return self._rm_plus(node.regret)

    def _accumulate(self, node, vals, v, my_reach, sigma, t):
        """Regret and average-strategy accumulation at a traverser node.

        A hook for the same reason `_sigma` is. A solver with pinned combo
        rows must keep those rows out of BOTH accumulators — a pinned row
        that accumulated regret would have its strategy silently decided by
        regret matching on the next iteration, and one that accumulated
        `strat` would leave `average()` returning a blend of the pin and
        CFR+ rather than the pin. Overriding here is the alternative to
        duplicating `_walk`.
        """
        node.regret += (vals - v).T
        np.maximum(node.regret, 0.0, out=node.regret)  # the CFR+ floor
        node.strat += t * my_reach[:, None] * sigma

    def _walk(self, node, seat, my_reach, opp_reach, t):
        if not isinstance(node, _Decision):
            return self._term_val(node, seat, opp_reach)
        sigma = self._sigma(node)
        if node.seat == seat:
            vals = np.empty((len(node.legal), self.cix.n))
            for a, child in enumerate(node.children):
                vals[a] = self._walk(child, seat, my_reach * sigma[:, a],
                                     opp_reach, t)
            v = np.einsum("na,an->n", sigma, vals)
            self._accumulate(node, vals, v, my_reach, sigma, t)
            return v
        out = np.zeros(self.cix.n)
        for a, child in enumerate(node.children):
            # Descend unconditionally. The old `if branch.any()` gate skipped
            # this subtree whenever RM+ had driven the OPPONENT's probability
            # to exactly zero for all combos — but the recursion also
            # accumulates the TRAVERSER's average strategy below, and that is
            # weighted by `my_reach`, which is unrelated to the opponent reach
            # being tested. So `strat` froze under any action the opponent's
            # current strategy had abandoned while their AVERAGE strategy
            # still reached it. Measured directly: with the gate, a subtree
            # behind a zeroed opponent action accumulated exactly 0.0 strat
            # mass where it now accumulates 3221.38
            # (test_zero_reach_branch_still_trains_below).
            out += self._walk(child, seat, my_reach, opp_reach * sigma[:, a], t)
        return out

    # ------------------------------------------------------------- API
    def run(self, iters):
        """Alternating-update CFR+ with linear strategy averaging."""
        s0, s1 = self.seats
        for _ in range(iters):
            self.iteration += 1
            t = float(self.iteration)
            self._walk(self.root, s0, self.ranges[s0], self.ranges[s1], t)
            self._walk(self.root, s1, self.ranges[s1], self.ranges[s0], t)
        return self

    @staticmethod
    def average(node):
        """Average strategy [n_combos, n_actions] of a decision node."""
        s = node.strat.sum(axis=1, keepdims=True)
        n_a = node.strat.shape[1]
        return np.where(s > 0, node.strat / np.where(s > 0, s, 1.0),
                        1.0 / n_a)

    def root_strategy(self):
        return self.average(self.root)

    def node_iter(self):
        """(node, path) pairs over every decision node, root first."""
        stack = [(self.root, ())]
        while stack:
            node, path = stack.pop()
            if isinstance(node, _Decision):
                yield node, path
                for a, child in enumerate(node.children):
                    stack.append((child, path + (node.legal[a],)))

    # ----------------------------------------------------- exploitability
    def _br(self, node, seat, opp_reach):
        if not isinstance(node, _Decision):
            return self._term_val(node, seat, opp_reach)
        if node.seat == seat:
            vals = [self._br(child, seat, opp_reach)
                    for child in node.children]
            return np.max(np.stack(vals), axis=0)
        sigma = self.average(node)
        out = np.zeros(self.cix.n)
        for a, child in enumerate(node.children):
            branch = opp_reach * sigma[:, a]
            if branch.any():
                out += self._br(child, seat, branch)
        return out

    def br_values(self):
        """(br0, br1, norm) — each seat's best-response value against the
        other's current AVERAGE strategy, in the normalized chip units
        `exploitability` reports.

        Split out because the oracle needs the terms separately, not their
        sum: `br1` measures how exploitable seat 0 is and `br0` how
        exploitable seat 1 is, so the achievable-gain decomposition is one
        term per seat. Note each value is in its OWN seat's utility —
        converting br1 into seat-0 utility is `dead - br1`, and mixing the
        two conventions is the error this docstring exists to prevent.
        """
        s0, s1 = self.seats
        w0, w1 = self.ranges[s0], self.ranges[s1]
        norm = float(w0 @ self.board_eval.disjoint_total(w1))
        br0 = float(w0 @ self._br(self.root, s0, w1)) / norm
        br1 = float(w1 @ self._br(self.root, s1, w0)) / norm
        return br0, br1, norm

    def exploitability(self):
        """Nash gap in chips per matched combo pair: sum of both seats'
        best-response values against the current average strategies,
        minus the dead-money constant. Every terminal pays the live pair
        self.dead in total (folded seats' chips), so the subgame is
        CONSTANT-sum, not zero-sum, and br0 + br1 converges to self.dead.
        Both BR walks share the same norm, so the offset is exactly
        self.dead in the returned units; subtracting it restores the
        invariant: >= 0 always, 0 at equilibrium, and it must shrink as
        run() iterates — THE correctness signal."""
        br0, br1, _ = self.br_values()
        return br0 + br1 - self.dead
