"""Fixed stochastic assignments for the one-bet river laboratory.

LPs propose strategies in binary64. Certificates use the original payoff
coefficients and assignment weights interpreted as exact rational numbers.
"""
from fractions import Fraction as Q
from environment import np, opt, PayoffGame, _regret_match

DENOMINATOR = 2**20


def validate(value, hands):
    array = np.asarray(value)
    opt.require(array.dtype.kind in 'iuf' and array.ndim == 2 and
                array.shape[0] == hands and 1 <= array.shape[1] <= hands,
                'numeric hand by component matrix required')
    opt.require(np.isfinite(array).all() and (array >= 0).all() and (array <= 1).all(),
                'invalid assignment weight')
    opt.require(all(sum(map(Q, map(float, row))) == 1 for row in array),
                'assignment rows must sum exactly to one')
    return array.astype(float)


def assignments(features, mass, labels):
    """Keep the hard label; blend it with its nearest other weighted centroid.

Distance is Euclidean. The other-center weight is d_home/(d_home+d_other).
Round that weight to 20 binary fractional bits; the home weight is its exact
complement. Equal zero distances fall back to the hard label.
"""
    f, mass = np.asarray(features, float), np.asarray(mass, float)
    opt.require(f.ndim == 2 and len(f) > 0 and np.isfinite(f).all(), 'invalid features')
    opt.require(mass.shape == (len(f),) and np.isfinite(mass).all() and (mass > 0).all(),
                'positive finite hand mass required')
    labels = opt._labels(labels, len(f))
    k = int(max(labels))+1
    hard = np.eye(k)[labels]
    mixed = hard.copy()
    if k == 1:
        return hard, mixed
    centers = np.array([np.average(f[labels == g], weights=mass[labels == g], axis=0)
                        for g in range(k)])
    distance = np.linalg.norm(f[:, None, :]-centers[None, :, :], axis=2)
    opt.require(np.isfinite(distance).all(), 'nonfinite centroid distance')
    for i, home in enumerate(labels):
        rivals = distance[i].copy()
        rivals[home] = np.inf
        other = int(rivals.argmin())
        total = distance[i, home]+distance[i, other]
        weight = 0. if total == 0 else distance[i, home]/total
        numerator = int(round(float(weight)*DENOMINATOR))
        mixed[i, home] = (DENOMINATOR-numerator)/DENOMINATOR
        mixed[i, other] = numerator/DENOMINATOR
    return validate(hard, len(f)), validate(mixed, len(f))


def checked(matrix, weights):
    opt.validate(matrix, tuple(np.arange(n) for n in matrix.joint.shape))
    opt.require(len(weights) == 2, 'two assignment matrices required')
    return tuple(validate(p, n) for p, n in zip(weights, matrix.joint.shape, strict=True))


def reduced(matrix, weights):
    p, q = checked(matrix, weights)
    # Preserve the existing accumulation order on the hard-control path.
    if all(np.all((w == 0) | (w == 1)) and np.all(w.sum(axis=0) > 0) for w in (p, q)):
        return matrix.aggregate((p.argmax(axis=1), q.argmax(axis=1)))
    return PayoffGame(*(p.T @ m @ q for m in
                       (matrix.joint, matrix.check, matrix.fold, matrix.call)),
                      None, matrix.source_digest)


def coefficients(values, size):
    a = np.asarray(values)
    opt.require(a.shape == (size,) and a.dtype.kind in 'iuf' and
                np.isfinite(a).all() and (a >= 0).all() and (a <= 1).all(),
                'infeasible component policy')
    return list(map(Q, map(float, a)))


def exact_bounds(matrix, weights, policies, *, unrestricted=False):
    """Exact extrema against the specified policy classes or full-hand responses."""
    p, q = checked(matrix, weights)
    opt.require(len(policies) == 2, 'two component policies required')
    a, b = (coefficients(v, w.shape[1]) for v, w in zip(policies, (p, q), strict=True))
    sparse = [[[(j, Q(float(v))) for j, v in enumerate(row) if v]
               for row in w] for w in (p, q)]
    x, y = [[sum((v*z[j] for j, v in row), Q(0)) for row in rows]
            for rows, z in zip(sparse, (a, b), strict=True)]
    c = [sum((Q(float(v)) for v in row), Q(0)) for row in matrix.check]
    fold = [[Q(float(v)) for v in row] for row in matrix.fold]
    call = [[Q(float(v)) for v in row] for row in matrix.call]
    n, m = matrix.joint.shape
    row_delta, col_delta = [Q(0)]*n, [Q(0)]*m
    lower = sum(((1-x[i])*c[i] for i in range(n)), Q(0))
    for i in range(n):
        row_delta[i] = -c[i]
        for j in range(m):
            d = call[i][j]-fold[i][j]
            row_delta[i] += fold[i][j]+d*y[j]
            lower += x[i]*fold[i][j]
            col_delta[j] += x[i]*d
    upper = sum(c, Q(0))
    deltas = [row_delta, col_delta]
    if not unrestricted:
        projected = []
        for rows, changes, size in zip(sparse, deltas, (len(a), len(b)), strict=True):
            result = [Q(0)]*size
            for row, change in zip(rows, changes, strict=True):
                for j, value in row:
                    result[j] += value*change
            projected.append(result)
        deltas = projected
    upper += sum((max(Q(0), v) for v in deltas[0]), Q(0))
    lower += sum((min(Q(0), v) for v in deltas[1]), Q(0))
    opt.require(lower <= upper, 'invalid exact saddle bracket')
    return lower, upper


def asymmetric(weights, shape, seat):
    return (weights[0], np.eye(shape[1])) if seat == 0 else (np.eye(shape[0]), weights[1])


def solve(matrix, weights):
    weights = checked(matrix, weights)
    records = {}
    for seat in (0, 1):
        pair = asymmetric(weights, matrix.joint.shape, seat)
        game = reduced(matrix, pair)
        labels = tuple(np.arange(n) for n in game.joint.shape)
        candidate = opt.solve_seat(game, labels, seat)
        policies = [candidate['bet'], candidate['call']]
        low, high = exact_bounds(matrix, pair, policies)
        opt.require(high-low <= opt.TOLERANCE, 'original-game certificate too wide')
        records[f'seat{seat}'] = dict(coefficients=policies, value=opt.interval(low, high),
                                     lp_iterations=candidate['lp_iterations'])
    l0, u0 = (Q(records['seat0']['value'][k]) for k in ('lower_exact', 'upper_exact'))
    l1, u1 = (Q(records['seat1']['value'][k]) for k in ('lower_exact', 'upper_exact'))
    records['minimum_exploitability'] = opt.interval(max(Q(0), (l1-u0)/2), (u1-l0)/2)
    verify(matrix, weights, records)
    return records


def verify(matrix, weights, record):
    weights = checked(matrix, weights)
    brackets = []
    for seat in (0, 1):
        row = record[f'seat{seat}']
        low, high = exact_bounds(matrix, asymmetric(weights, matrix.joint.shape, seat),
                                 row['coefficients'])
        opt.require(row['value'] == opt.interval(low, high), 'certificate record mismatch')
        opt.require(high-low <= opt.TOLERANCE, 'certificate too wide')
        brackets.append((low, high))
    (l0, u0), (l1, u1) = brackets
    expected = opt.interval(max(Q(0), (l1-u0)/2), (u1-l0)/2)
    opt.require(record['minimum_exploitability'] == expected, 'floor record mismatch')
    return expected


class RegretBR:
    """Separate component-policy regret learners versus exact-hand responses."""
    def __init__(self, matrix, weights):
        self.weights = checked(matrix, weights)
        self.games = tuple(reduced(matrix, asymmetric(self.weights, matrix.joint.shape, s))
                           for s in (0, 1))
        self.regrets = [np.zeros((p.shape[1], 2)) for p in self.weights]
        self.sums = [np.zeros_like(r) for r in self.regrets]
        self.check = [g.check.sum(axis=1) for g in self.games]
        self.fold = [g.fold.sum(axis=1) for g in self.games]
        self.difference = [g.call-g.fold for g in self.games]
        self.iteration = 0

    def step(self):
        s0, s1 = (_regret_match(r) for r in self.regrets)
        first, second = self.games
        f, a = s0[:, 1] @ first.fold, s0[:, 1] @ first.call
        y = np.where(a < f, 1., np.where(a > f, 0., .5))
        betting = self.fold[1]+self.difference[1] @ s1[:, 1]
        x = np.where(betting > self.check[1], 1., np.where(betting < self.check[1], 0., .5))
        values = (np.column_stack((self.check[0], self.fold[0]+self.difference[0] @ y)),
                  np.column_stack((-x @ second.fold, -x @ second.call)))
        for seat, strategy in enumerate((s0, s1)):
            self.sums[seat] += strategy
            self.regrets[seat] += values[seat]-(strategy*values[seat]).sum(axis=1, keepdims=True)
        self.iteration += 1

    def average(self):
        opt.require(self.iteration > 0, 'empty average')
        return tuple(s[:, 1]/self.iteration for s in self.sums)
