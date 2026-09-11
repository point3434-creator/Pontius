"""Bounded one-bet river abstraction laboratory; not a deployed poker policy.

The full-hand payoff matrix is the evaluation domain. Grouped matrices restrict
only the policy class, never the deal population or an evaluator's best response.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from itertools import combinations

import numpy as np

from .river import BET, CALL, CHECK, FOLD, RiverHoldem, RiverState, evaluate_seven


def _probabilities(value, size):
    array = np.asarray(value, dtype=np.float64)
    if array.shape != (size,) or not np.isfinite(array).all():
        raise ValueError('policy must have one finite probability per hand/group')
    if ((array < 0) | (array > 1)).any():
        raise ValueError('policy probabilities must be in [0,1]')
    return array


def _labels(value, size):
    array = np.asarray(value)
    if array.shape != (size,) or array.dtype.kind not in 'iu':
        raise ValueError('groups must be an integer vector covering every hand')
    if not np.array_equal(np.unique(array), np.arange(len(np.unique(array)))):
        raise ValueError('groups must be contiguous occupied labels starting at zero')
    return array.astype(np.int64)


@dataclass(frozen=True)
class PayoffGame:
    """Joint-mass-weighted terminal payoffs to player 0, in chips."""

    joint: np.ndarray
    check: np.ndarray
    fold: np.ndarray
    call: np.ndarray
    hands: tuple | None
    source_digest: str

    @classmethod
    def from_river(cls, game: RiverHoldem):
        if game.raise_to is not None or game.num_players != 2:
            raise ValueError('only the heads-up one-bet game is supported')
        hands = tuple(tuple(sorted(game.marginal_distribution(p))) for p in (0, 1))
        index = tuple({hand: i for i, hand in enumerate(pool)} for pool in hands)
        joint = np.zeros(tuple(map(len, hands)))
        sign = np.zeros_like(joint)
        ranks = {hand: evaluate_seven((*game.board, *hand)) for pool in hands for hand in pool}
        for deal, probability in game.deals:
            i, j = index[0][deal.player0], index[1][deal.player1]
            joint[i, j] = probability
            a, b = ranks[deal.player0], ranks[deal.player1]
            sign[i, j] = (a > b) - (a < b)
        return cls(joint, joint * sign * (game.pot / 2), joint * (game.pot / 2),
                   joint * sign * (game.pot / 2 + game.bet_size), hands,
                   game.provenance_digest)

    def aggregate(self, groups):
        if len(groups) != 2:
            raise ValueError('two group vectors required')
        g0, g1 = (_labels(g, n) for g, n in zip(groups, self.joint.shape, strict=True))
        shape = (int(g0.max()) + 1, int(g1.max()) + 1)

        def reduce(array):
            result = np.zeros(shape)
            np.add.at(result, (g0[:, None], g1[None, :]), array)
            return result

        return PayoffGame(*(reduce(a) for a in (self.joint, self.check, self.fold, self.call)),
                          None, self.source_digest)

    def evaluate(self, bet, call):
        x, y = (_probabilities(v, n) for v, n in zip((bet, call), self.joint.shape, strict=True))
        check = self.check.sum(axis=1)
        betting = self.fold.sum(axis=1) + (self.call - self.fold) @ y
        value = float((1 - x) @ check + x @ betting)
        upper = float(np.maximum(check, betting).sum())
        lower = float((1 - x) @ check + np.minimum(x @ self.fold, x @ self.call).sum())
        return {'value': value, 'lower': lower, 'upper': upper,
                'deviation0': upper - value, 'deviation1': value - lower,
                'exploitability': (upper - lower) / 2}

    def lift_policy(self, game, bet, call):
        """Build every exact information-set row; never fill a missing row uniformly."""
        if self.hands is None or game.provenance_digest != self.source_digest:
            raise ValueError('policy lifting requires the original exact game')
        x, y = (_probabilities(v, n) for v, n in zip((bet, call), self.joint.shape, strict=True))
        policy = {}
        for player, probabilities, actions in [(0, x, (CHECK, BET)), (1, y, (FOLD, CALL))]:
            witnesses = {deal.hand(player): deal for deal, _ in game.deals}
            for hand, probability in zip(self.hands[player], probabilities, strict=True):
                state = RiverState(game, witnesses[hand], () if player == 0 else ((0, BET),))
                policy[state.information_state_key(player)] = {
                    actions[0]: float(1 - probability), actions[1]: float(probability)}
        return policy


def _regret_match(regrets):
    positive = np.maximum(regrets, 0)
    mass = positive.sum(axis=1, keepdims=True)
    return np.divide(positive, mass, out=np.full_like(positive, 0.5), where=mass > 0)


class CFR:
    """Alternating vanilla CFR for the single decision per player per hand tree."""

    def __init__(self, game: PayoffGame):
        self.game = game
        self.regrets = [np.zeros((n, 2)) for n in game.joint.shape]
        self.sums = [np.zeros_like(r) for r in self.regrets]
        self.iteration = 0
        self.check = game.check.sum(axis=1)
        self.fold = game.fold.sum(axis=1)
        self.difference = game.call - game.fold

    def current(self):
        return tuple(_regret_match(r)[:, 1] for r in self.regrets)

    def step(self):
        s0, s1 = (_regret_match(r) for r in self.regrets)
        self.sums[0] += s0
        values0 = np.column_stack((self.check, self.fold + self.difference @ s1[:, 1]))
        self.regrets[0] += values0 - (s0 * values0).sum(axis=1, keepdims=True)
        x = _regret_match(self.regrets[0])[:, 1]
        self.sums[1] += s1
        values1 = np.column_stack((-x @ self.game.fold, -x @ self.game.call))
        self.regrets[1] += values1 - (s1 * values1).sum(axis=1, keepdims=True)
        self.iteration += 1

    def average(self):
        if self.iteration == 0:
            raise ValueError('no average strategy before an iteration')
        return tuple(total[:, 1] / self.iteration for total in self.sums)


def uniform_equities(board):
    """Exact win/tie counts against the 990 compatible uniform opponent hands."""
    board = tuple(sorted(board))
    if len(board) != 5 or len(set(board)) != 5:
        raise ValueError('five distinct board cards required')
    hands = tuple(combinations([c for c in range(52) if c not in board], 2))
    ranks = {h: evaluate_seven((*board, *h)) for h in hands}
    result = {}
    for hand in hands:
        compatible = [h for h in hands if not (set(hand) & set(h))]
        wins = sum(ranks[hand] > ranks[h] for h in compatible)
        ties = sum(ranks[hand] == ranks[h] for h in compatible)
        if len(compatible) != 990:
            raise ValueError('invalid compatible opponent population')
        result[hand] = (wins + 0.5 * ties) / 990
    return result


def anchored_clusters(features, weights, k):
    """Deterministic weighted farthest-first/Lloyd clustering with occupied anchors."""
    f, w = np.asarray(features, dtype=float), np.asarray(weights, dtype=float)
    if f.ndim != 2 or not np.isfinite(f).all() or w.shape != (len(f),):
        raise ValueError('finite feature matrix and matching weights required')
    if not np.isfinite(w).all() or (w <= 0).any() or type(k) is not int or not 1 <= k <= len(f):
        raise ValueError('positive weights and 1 <= K <= hand count required')
    seeds = [int(np.argmax(w))]
    while len(seeds) < k:
        distance = ((f[:, None, :] - f[seeds][None, :, :]) ** 2).sum(axis=2).min(axis=1)
        scores = distance * w
        scores[seeds] = -1
        seeds.append(int(np.argmax(scores)))
    centers = f[seeds].copy()
    for _ in range(20):
        labels = ((f[:, None, :] - centers[None, :, :]) ** 2).sum(axis=2).argmin(axis=1)
        labels[seeds] = np.arange(k)
        centers = np.array([np.average(f[labels == i], axis=0, weights=w[labels == i])
                            for i in range(k)])
    return labels


def range_features(matrix, equities, player):
    """Conditional mass/win/tie by public opponent-equity thirds, plus range equity."""
    if matrix.hands is None or player not in (0, 1):
        raise ValueError('features require an exact game and player 0 or 1')
    joint = matrix.joint if player == 0 else matrix.joint.T
    check = matrix.check if player == 0 else -matrix.check.T
    marginal = joint.sum(axis=1)
    conditional = joint / marginal[:, None]
    opponent = matrix.hands[1 - player]
    bands = np.array([min(int(equities[h] * 3), 2) for h in opponent])
    columns = []
    for band in range(3):
        mass = conditional * (bands == band)[None, :]
        columns.extend([mass.sum(axis=1), (mass * (check > 0)).sum(axis=1),
                        (mass * (check == 0)).sum(axis=1)])
    equity = (conditional * ((check > 0) + 0.5 * (check == 0))).sum(axis=1)
    return np.column_stack(columns), equity


def representations(matrix, equities):
    if matrix.hands is None:
        raise ValueError('representations require the exact game')
    names = ('exact', 'uniform_equity_200', 'range_equity', 'range_response')
    result = {name: [] for name in names}
    for player, hands in enumerate(matrix.hands):
        baseline = np.array([min(int(equities[h] * 200), 199) for h in hands])
        _, labels = np.unique(baseline, return_inverse=True)
        k = len(np.unique(labels))
        features, equity = range_features(matrix, equities, player)
        marginal = matrix.joint.sum(axis=1 - player)
        result['exact'].append(np.arange(len(hands)))
        result['uniform_equity_200'].append(labels)
        result['range_equity'].append(anchored_clusters(equity[:, None], marginal, k))
        result['range_response'].append(anchored_clusters(features, marginal, k))
    return {name: tuple(groups) for name, groups in result.items()}


DEVELOPMENT_BOARDS = ((0, 21, 30, 39, 40), (2, 22, 38, 40, 47))


def development_case(board, hand_count=16, regime='uniform'):
    board = tuple(sorted(board))
    if board not in DEVELOPMENT_BOARDS:
        raise ValueError('this development driver does not admit holdout or arbitrary boards')
    if type(hand_count) is not int or not 2 <= hand_count <= 96:
        raise ValueError('hand count must be an integer in [2,96]')
    if regime not in ('uniform', 'polarized'):
        raise ValueError('unknown range regime')
    equities = uniform_equities(board)
    ranges = []
    prefix = ','.join(map(str, board))
    for player in (0, 1):
        def order(hand):
            payload = f'river-study-v1|{prefix}|{player}|{hand[0]},{hand[1]}'
            return sha256(payload.encode('ascii')).digest(), hand

        hands = sorted(equities, key=order)[:hand_count]
        ranges.append({h: 4 if regime == 'polarized' and
                       (equities[h] <= 0.2 or equities[h] >= 0.8) else 1 for h in hands})
    game = RiverHoldem.from_independent_ranges(
        board=board, pot=10, stacks=(20, 20), bet_size=5,
        player0_weights=ranges[0], player1_weights=ranges[1])
    return game, equities, ranges
