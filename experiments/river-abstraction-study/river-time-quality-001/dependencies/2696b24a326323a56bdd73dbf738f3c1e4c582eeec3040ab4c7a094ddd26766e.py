"""Oracle-assisted, fixed-capacity regrouping from retained opponent witnesses."""
from __future__ import annotations

from fractions import Fraction as Q
import json

import numpy as np

from .river_abstraction_study import anchored_clusters
from .river_group_optimality import interval, policy, require, validate, verify_solution

METHODS = ('exact', 'uniform_equity_200', 'range_equity', 'range_response')


def action_advantages(matrix, opponents, player):
    """Conditional-own-hand chip differences; seat 1 retains opponent bet reach."""
    require(type(player) is int and player in (0, 1), 'player must be 0 or 1')
    exact = tuple(np.arange(n) for n in np.shape(matrix.joint))
    validate(matrix, exact)
    marginal = matrix.joint.sum(axis=1-player)
    require((marginal > 0).all(), 'positive own-hand marginal required')
    require(1 <= len(opponents) <= 4, 'one to four opponent witnesses required')
    columns = []
    for witness in opponents:
        p = np.array([float(v) for v in policy(witness, exact[1-player])])
        if player == 0:
            delta = matrix.fold.sum(axis=1) + (matrix.call-matrix.fold) @ p
            delta -= matrix.check.sum(axis=1)
        else:
            delta = p @ (matrix.fold-matrix.call)
        columns.append(delta/marginal)
    features = np.column_stack(columns)
    require(np.isfinite(features).all(), 'nonfinite action advantage')
    return features


def propose(matrix, groups, bank):
    require(set(groups) == set(METHODS) and type(bank) is dict and
            set(bank) == {'case', 'methods'} and type(bank['case']) is str,
            'incomplete witness bank')
    require([r['method'] for r in bank['methods']] == list(METHODS), 'witness method order')
    exact = tuple(np.arange(n) for n in matrix.joint.shape)
    for name in METHODS:
        pair = validate(matrix, groups[name])
        if name == 'exact':
            require(all(np.array_equal(a, b) for a, b in zip(pair, exact)), 'exact control grouped')
        else:
            require([len(set(g)) for g in pair] ==
                    [len(set(g)) for g in groups['uniform_equity_200']], 'unequal capacity')
    for row in bank['methods']:
        verify_solution(matrix, groups[row['method']], row['solution'])
    features, labels, masses = [], [], []
    for player in (0, 1):
        # Each unrestricted opponent is the witness from the constrained-seat game.
        opponents = [r['solution'][f'seat{player}']['call' if player == 0 else 'bet']
                     for r in bank['methods']]
        feature = action_advantages(matrix, opponents, player)
        marginal = matrix.joint.sum(axis=1-player)
        k = len(set(groups['uniform_equity_200'][player]))
        labels.append(anchored_clusters(feature, marginal, k).tolist())
        features.append(feature.tolist())
        masses.append(marginal.tolist())
    return dict(method='witness_advantage', bank_methods=list(METHODS), features=features,
                marginals=masses, groups=labels)


def difference(candidate, control):
    lo = Q(candidate['lower_exact'])-Q(control['upper_exact'])
    hi = Q(candidate['upper_exact'])-Q(control['lower_exact'])
    classification = 'lower' if hi < 0 else 'higher' if lo > 0 else 'overlapping'
    return dict(**interval(lo, hi), classification=classification)


def result_record(matrix, groups, bank, solution):
    proposal = propose(matrix, groups, bank)
    candidate = verify_solution(matrix, proposal['groups'], solution)
    comparisons = {row['method']: difference(candidate, row['solution']['minimum_exploitability'])
                   for row in bank['methods']}
    return dict(case=bank['case'], proposal=proposal, solution=solution, comparisons=comparisons)


def verify_record(matrix, groups, bank, record):
    expected = result_record(matrix, groups, bank, record['solution'])
    def canonical(value):
        return json.dumps(value, sort_keys=True, allow_nan=False)
    require(canonical(record) == canonical(expected), 'regrouping result mismatch')
    return expected
