"""Accept saved policies by exact worst-case value, independently per role."""
from fractions import Fraction as Q
from base import c


def select(matrix, old_groups, old_coefficients, new_groups, new_coefficients):
    groups = [old_groups, new_groups]
    coefficients = [old_coefficients, new_coefficients]
    security = []
    for gs, cs in zip(groups, coefficients, strict=True):
        c.opt.validate(matrix, gs)
        low, high = c.core.exact_bounds(matrix, c.weights(gs), cs, unrestricted=True)
        security.append([low, -high])
    accepted = [security[1][s] >= security[0][s] for s in (0, 1)]
    return dict(accepted=accepted,
        security_exact=[[str(x) for x in pair] for pair in security],
        groups=[list(groups[int(accepted[s])][s]) for s in (0, 1)],
        coefficients=[list(coefficients[int(accepted[s])][s]) for s in (0, 1)])


def audit_security(matrix, hand_policies):
    """Independent terminal-payoff sums; no call to the acceptance evaluator."""
    x, y = hand_policies
    n, m = matrix.joint.shape
    check = [[Q(float(v)) for v in row] for row in matrix.check]
    fold = [[Q(float(v)) for v in row] for row in matrix.fold]
    call = [[Q(float(v)) for v in row] for row in matrix.call]
    bettor = sum(((1-x[i])*sum(check[i], Q(0)) for i in range(n)), Q(0))
    for j in range(m):
        bettor += min(sum((x[i]*fold[i][j] for i in range(n)), Q(0)),
                      sum((x[i]*call[i][j] for i in range(n)), Q(0)))
    caller = Q(0)
    for i in range(n):
        caller -= max(sum(check[i], Q(0)),
            sum(((1-y[j])*fold[i][j]+y[j]*call[i][j] for j in range(m)), Q(0)))
    return [bettor, caller]
