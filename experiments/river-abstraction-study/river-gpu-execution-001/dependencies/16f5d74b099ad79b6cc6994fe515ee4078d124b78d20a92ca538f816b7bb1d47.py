"""Best representable policies in a fixed one-bet, two-player zero-sum game.

HiGHS proposes saddle strategies. Fraction arithmetic certifies their bounds on
the binary64 payoff coefficients interpreted exactly, not an ideal real game.
"""
from __future__ import annotations

from fractions import Fraction as Q

import numpy as np
from scipy.optimize import linprog

from .river_abstraction_study import _labels

TOLERANCE = Q(1, 10**8)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate(matrix, groups):
    shape = np.shape(matrix.joint)
    require(len(shape) == 2 and all(1 <= n <= 96 for n in shape), 'matrix size outside 1..96')
    for array in (matrix.joint, matrix.check, matrix.fold, matrix.call):
        require(np.shape(array) == shape and np.isfinite(array).all(), 'invalid payoff matrix')
    require((matrix.joint >= 0).all(), 'negative deal mass')
    require(len(groups) == 2, 'two group vectors required')
    return tuple(_labels(g, n) for g, n in zip(groups, shape, strict=True))


def policy(values, groups):
    require(len(values) == len(groups), 'policy length mismatch')
    require(all(isinstance(p, (int, float, np.integer, np.floating)) and
                not isinstance(p, (bool, np.bool_)) for p in values), 'non-numeric probability')
    probabilities = [Q(float(p)) for p in values]
    require(all(0 <= p <= 1 for p in probabilities), 'infeasible probability')
    for group in set(groups):
        require(len({p for p, g in zip(probabilities, groups) if g == group}) == 1,
                'policy violates group constraint')
    return probabilities


def saddle_bounds(matrix, bet, call, groups):
    """Exact min_y V(bet,y), max_x V(x,call) over declared group policy classes."""
    g0, g1 = validate(matrix, groups)
    x, y = policy(bet, g0), policy(call, g1)
    row_check, row_bet = [Q(0)] * (max(g0)+1), [Q(0)] * (max(g0)+1)
    col_fold, col_call = [Q(0)] * (max(g1)+1), [Q(0)] * (max(g1)+1)
    base = Q(0)
    for i in range(len(x)):
        for j in range(len(y)):
            c, f, a = (Q(float(t[i, j])) for t in (matrix.check, matrix.fold, matrix.call))
            row_check[g0[i]] += c
            row_bet[g0[i]] += (1-y[j]) * f + y[j] * a
            col_fold[g1[j]] += x[i] * f
            col_call[g1[j]] += x[i] * a
            base += (1-x[i]) * c
    lower = base + sum(map(min, col_fold, col_call), Q(0))
    upper = sum(map(max, row_check, row_bet), Q(0))
    require(lower <= upper, 'invalid saddle bracket')
    return lower, upper


def interval(lower, upper):
    require(lower <= upper, 'reversed interval')
    return dict(lower_exact=str(lower), upper_exact=str(upper),
                lower_chips_approx=float(lower), upper_chips_approx=float(upper))


def solve_seat(matrix, groups, seat):
    g0, g1 = validate(matrix, groups)
    n0, n1 = matrix.joint.shape
    exact = (np.arange(n0), np.arange(n1))
    asymmetric = (g0, exact[1]) if seat == 0 else (exact[0], g1)
    reduced = matrix.aggregate(asymmetric)
    rows, cols = reduced.joint.shape
    c, f, a = reduced.check.sum(axis=1), reduced.fold, reduced.call
    if seat == 0:
        objective = np.r_[c, -np.ones(cols)]
        constraints = np.vstack((np.c_[-f.T, np.eye(cols)], np.c_[-a.T, np.eye(cols)]))
        rhs = np.zeros(2*cols)
        bounds = [(0, 1)] * rows + [(None, None)] * cols
    else:
        objective = np.r_[np.zeros(cols), np.ones(rows)]
        constraints = np.vstack((np.c_[np.zeros((rows, cols)), -np.eye(rows)],
                                 np.c_[a-f, -np.eye(rows)]))
        rhs = np.r_[-c, -f.sum(axis=1)]
        bounds = [(0, 1)] * cols + [(None, None)] * rows
    result = linprog(objective, A_ub=constraints, b_ub=rhs, bounds=bounds,
                     method='highs-ds', options=dict(time_limit=5, maxiter=10000,
                         primal_feasibility_tolerance=1e-9, dual_feasibility_tolerance=1e-9))
    require(result.success and result.status == 0, 'LP did not terminate optimally')
    # Any clipping must still pass the independently computed exact saddle gap.
    if seat == 0:
        x = np.clip(result.x[:rows], 0, 1)[g0]
        y = np.clip(-result.ineqlin.marginals[cols:], 0, 1)
    else:
        y = np.clip(result.x[:cols], 0, 1)[g1]
        x = np.clip(-result.ineqlin.marginals[rows:], 0, 1)
    lower, upper = saddle_bounds(matrix, x, y, asymmetric)
    require(upper-lower <= TOLERANCE, 'LP candidate lacks required saddle certificate')
    return dict(bet=x.tolist(), call=y.tolist(), value=interval(lower, upper),
                gap_exact=str(upper-lower), lp_iterations=int(result.nit))


def verify_solution(matrix, groups, result):
    """Reconstruct both certificates without using the LP solver or its objective."""
    g0, g1 = validate(matrix, groups)
    n0, n1 = matrix.joint.shape
    brackets = []
    for seat, asymmetric in [(0, (g0, np.arange(n1))), (1, (np.arange(n0), g1))]:
        record = result[f'seat{seat}']
        low, high = saddle_bounds(matrix, record['bet'], record['call'], asymmetric)
        require(record['value'] == interval(low, high) and record['gap_exact'] == str(high-low),
                'certificate record mismatch')
        require(high-low <= TOLERANCE, 'certificate too wide')
        brackets.append((low, high))
    (l0, u0), (l1, u1) = brackets
    floor = interval(max(Q(0), (l1-u0)/2), (u1-l0)/2)
    require(result['minimum_exploitability'] == floor, 'minimum exploitability mismatch')
    return floor


def solve_groups(matrix, groups):
    first, second = solve_seat(matrix, groups, 0), solve_seat(matrix, groups, 1)
    l0, u0 = Q(first['value']['lower_exact']), Q(first['value']['upper_exact'])
    l1, u1 = Q(second['value']['lower_exact']), Q(second['value']['upper_exact'])
    result = dict(seat0=first, seat1=second,
                  minimum_exploitability=interval(max(Q(0), (l1-u0)/2), (u1-l0)/2))
    verify_solution(matrix, groups, result)
    return result


def compare_saved(matrix, groups, solution, bet, call):
    # Validate the saved policy in its own class, then allow full-hand deviations.
    g0, g1 = validate(matrix, groups)
    policy(bet, g0)
    policy(call, g1)
    low, high = saddle_bounds(matrix, bet, call, tuple(np.arange(n) for n in matrix.joint.shape))
    saved = (high-low)/2
    floor = solution['minimum_exploitability']
    lower, upper = Q(floor['lower_exact']), Q(floor['upper_exact'])
    require(saved >= lower, 'saved policy contradicts certified lower bound')
    return dict(saved_exploitability_exact=str(saved),
                saved_exploitability_chips_approx=float(saved),
                avoidable_gap=interval(max(Q(0), saved-upper), saved-lower))
