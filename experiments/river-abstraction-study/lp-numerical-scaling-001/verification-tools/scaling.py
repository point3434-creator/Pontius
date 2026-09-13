"""Research-only change of LP value units, retaining policy units and exact scoring."""
from types import SimpleNamespace
import numpy as np
from scipy.optimize import linprog

SCALE = 2**20
CALLS = []


def transform(objective, kwargs):
    objective = np.array(objective, dtype=float, copy=True)
    bound = kwargs['bounds']
    assert all(b in ((0, 1), (None, None)) for b in bound)
    policy = np.array([b == (0, 1) for b in bound])
    objective[policy] *= SCALE
    changed = dict(kwargs)
    matrix = np.array(kwargs['A_ub'], dtype=float, copy=True)
    matrix[:, policy] *= SCALE
    changed['A_ub'] = matrix
    changed['b_ub'] = np.asarray(kwargs['b_ub'])*SCALE
    if 'A_eq' in kwargs:
        assert not np.any(kwargs['A_eq'][:, ~policy])
    nonzero = np.abs(matrix[matrix != 0])
    assert np.isfinite(matrix).all() and np.isfinite(objective).all()
    assert not len(nonzero) or nonzero.min() > 1e-9, 'scaled coefficients remain below cutoff'
    return objective, changed, policy


def solve(objective, **kwargs):
    cost, changed, policy = transform(objective, kwargs)
    answer = linprog(cost, **changed)
    x = None if answer.x is None else answer.x.copy()
    if x is not None:
        x[~policy] /= SCALE
    CALLS.append(dict(status=int(answer.status), success=bool(answer.success),
        message=str(answer.message), iterations=int(answer.nit),
        raw_scaled_x=None if answer.x is None else answer.x.tolist(),
        original_units_x=None if x is None else x.tolist(), options=kwargs['options']))
    # Only the fields the frozen pair solver consumes; residuals and duals are not exposed.
    return SimpleNamespace(success=answer.success, status=answer.status, message=answer.message,
        x=x, nit=answer.nit)
