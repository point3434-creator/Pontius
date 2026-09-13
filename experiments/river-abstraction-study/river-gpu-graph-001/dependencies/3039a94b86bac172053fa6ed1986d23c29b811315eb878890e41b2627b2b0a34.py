"""Small check/multiple-bet game; separate call/fold response after each size."""
from bridge import c
from fractions import Fraction as Q
from dataclasses import dataclass

np = c.np


@dataclass
class Game:
    check: object
    fold: object
    call: object

    def __post_init__(self):
        self.check, self.fold, self.call = map(np.asarray, (self.check, self.fold, self.call))
        assert self.check.ndim == 2 and self.fold.ndim == 3
        assert self.fold.shape == self.call.shape and self.fold.shape[1:] == self.check.shape
        assert len(self.fold) in (1, 2)
        assert all(np.isfinite(v).all() for v in (self.check, self.fold, self.call))


def reduced(game, groups):
    w = c.weights(groups)
    return Game(w[0].T @ game.check @ w[1],
                [w[0].T @ v @ w[1] for v in game.fold],
                [w[0].T @ v @ w[1] for v in game.call])


def policies(game, x, y):
    n, k = game.check.shape
    b = len(game.fold)
    assert len(x) == n and len(y) == b and all(len(row) == b+1 for row in x)
    assert all(len(row) == k for row in y)
    xx = [[Q(float(v)) for v in row] for row in x]
    yy = [[Q(float(v)) for v in row] for row in y]
    assert all(min(row) >= 0 and sum(row) > 0 for row in xx)
    assert all(0 <= p <= 1 for row in yy for p in row)
    return [[v/sum(row) for v in row] for row in xx], yy


def bounds(game, x, y, groups):
    x, y = policies(game, x, y)
    n, k = game.check.shape
    b = len(game.fold)
    g0, g1 = groups
    assert len(g0) == n and len(g1) == k
    row = [[Q(0)]*(b+1) for _ in range(max(g0)+1)]
    folds = [[Q(0)]*(max(g1)+1) for _ in range(b)]
    calls = [[Q(0)]*(max(g1)+1) for _ in range(b)]
    base = Q(0)
    for i in range(n):
        for j in range(k):
            check = Q(float(game.check[i, j]))
            row[g0[i]][0] += check
            base += x[i][0]*check
            for s in range(b):
                f, a = Q(float(game.fold[s, i, j])), Q(float(game.call[s, i, j]))
                row[g0[i]][s+1] += (1-y[s][j])*f+y[s][j]*a
                folds[s][g1[j]] += x[i][s+1]*f
                calls[s][g1[j]] += x[i][s+1]*a
    low = base+sum((min(f, a) for fs, cs in zip(folds, calls)
                   for f, a in zip(fs, cs)), Q(0))
    high = sum(map(max, row), Q(0))
    assert low <= high
    return low, high


def pair(game, groups):
    """Solve primal and opposing LP, then certify on original coefficients."""
    small = reduced(game, groups)
    n, k = small.check.shape
    b, actions = len(small.fold), len(small.fold)+1
    count = n*actions
    objective = np.zeros(count+b*k)
    objective[np.arange(n)*actions] = -small.check.sum(axis=1)
    objective[count:] = -1
    eq = np.zeros((n, count+b*k))
    for i in range(n):
        eq[i, i*actions:(i+1)*actions] = 1
    ub = np.zeros((2*b*k, count+b*k))
    for s in range(b):
        for j in range(k):
            for choice, payoff in enumerate((small.fold, small.call)):
                r = (s*k+j)*2+choice
                ub[r, np.arange(n)*actions+s+1] = -payoff[s, :, j]
                ub[r, count+s*k+j] = 1
    options = dict(time_limit=10, maxiter=20000, primal_feasibility_tolerance=1e-9,
                   dual_feasibility_tolerance=1e-9)
    first = c.opt.linprog(objective, A_ub=ub, b_ub=np.zeros(len(ub)),
        A_eq=eq, b_eq=np.ones(n), bounds=[(0, 1)]*count+[(None, None)]*(b*k),
        method='highs-ds', options=options)
    ub = np.zeros((n*actions, b*k+n))
    rhs = np.zeros(n*actions)
    for i in range(n):
        ub[i*actions, b*k+i] = -1
        rhs[i*actions] = -small.check[i].sum()
        for s in range(b):
            r = i*actions+s+1
            ub[r, s*k:(s+1)*k] = small.call[s, i]-small.fold[s, i]
            ub[r, b*k+i] = -1
            rhs[r] = -small.fold[s, i].sum()
    second = c.opt.linprog(np.r_[np.zeros(b*k), np.ones(n)], A_ub=ub, b_ub=rhs,
        bounds=[(0, 1)]*(b*k)+[(None, None)]*n, method='highs-ds', options=options)
    assert first.success and second.success
    x = np.clip(first.x[:count].reshape(n, actions), 0, 1)[groups[0]].tolist()
    y = np.clip(second.x[:b*k].reshape(b, k), 0, 1)[:, groups[1]].tolist()
    low, high = bounds(game, x, y, groups)
    assert high-low <= Q('1e-8'), float(high-low)
    return dict(x=x, y=y, bounds=list(map(str, (low, high))),
                lp_iterations=[int(first.nit), int(second.nit)])


def solve(game, groups):
    n, k = game.check.shape
    first = pair(game, [groups[0], list(range(k))])
    second = pair(game, [list(range(n)), groups[1]])
    l0, u0 = map(Q, first['bounds'])
    l1, u1 = map(Q, second['bounds'])
    result = dict(seat0=first, seat1=second,
                  floor=list(map(str, (max(Q(0), (l1-u0)/2), (u1-l0)/2))))
    verify(game, groups, result)
    return result


def verify(game, groups, result):
    n, k = game.check.shape
    for seat, gs in enumerate(([groups[0], list(range(k))], [list(range(n)), groups[1]])):
        r = result[f'seat{seat}']
        x, y = policies(game, r['x'], r['y'])
        assert all(x[i] == x[j] for i in range(n) for j in range(n) if gs[0][i] == gs[0][j])
        assert all(y[s][i] == y[s][j] for s in range(len(y)) for i in range(k)
                   for j in range(k) if gs[1][i] == gs[1][j])
        low, high = bounds(game, r['x'], r['y'], gs)
        assert r['bounds'] == list(map(str, (low, high))) and high-low <= Q('1e-8')
    l0, u0 = map(Q, result['seat0']['bounds'])
    l1, u1 = map(Q, result['seat1']['bounds'])
    assert result['floor'] == list(map(str, (max(Q(0), (l1-u0)/2), (u1-l0)/2)))


def match(regrets):
    positive = np.maximum(regrets, 0)
    total = positive.sum(axis=-1, keepdims=True)
    return np.divide(positive, total, out=np.full_like(positive, 1/positive.shape[-1]),
                     where=total > 0)


class Trainer:
    """Independent role learners against unrestricted hand-specific responses."""
    def __init__(self, game, groups):
        n, k = game.check.shape
        self.groups = groups
        self.games = [reduced(game, [groups[0], list(range(k))]),
                      reduced(game, [list(range(n)), groups[1]])]
        b = len(game.fold)
        self.regrets = [np.zeros((max(groups[0])+1, b+1)),
                        np.zeros((b, max(groups[1])+1, 2))]
        self.sums = [np.zeros_like(r) for r in self.regrets]
        self.iteration = 0

    def step(self):
        x, y = [match(r) for r in self.regrets]
        first, second = self.games
        b = len(first.fold)
        bettor = [first.check.sum(axis=1)]
        for s in range(b):
            f, a = x[:, s+1] @ first.fold[s], x[:, s+1] @ first.call[s]
            response = np.where(a < f, 1., np.where(a > f, 0., .5))
            bettor.append(first.fold[s].sum(axis=1)+(first.call[s]-first.fold[s]) @ response)
        options = np.column_stack([second.check.sum(axis=1)]+[
            second.fold[s].sum(axis=1)+(second.call[s]-second.fold[s]) @ y[s, :, 1]
            for s in range(b)])
        best = options == options.max(axis=1, keepdims=True)
        response = best/best.sum(axis=1, keepdims=True)
        caller = np.array([np.column_stack((-response[:, s+1] @ second.fold[s],
                                            -response[:, s+1] @ second.call[s])) for s in range(b)])
        for seat, (strategy, value) in enumerate(((x, np.column_stack(bettor)), (y, caller))):
            self.sums[seat] += strategy
            self.regrets[seat] += value-(strategy*value).sum(axis=-1, keepdims=True)
        self.iteration += 1

    def average(self):
        assert self.iteration > 0
        return ((self.sums[0]/self.iteration).tolist(),
                (self.sums[1][:, :, 1]/self.iteration).tolist())


def expand(groups, x, y):
    return np.asarray(x)[groups[0]].tolist(), np.asarray(y)[:, groups[1]].tolist()


def score(game, groups, x, y):
    xx, yy = expand(groups, x, y)
    low, high = bounds(game, xx, yy, [list(range(n)) for n in game.check.shape])
    return dict(exploitability_exact=str((high-low)/2), exploitability=float((high-low)/2))


def size_conflict(game, groups, witness):
    """Fixed-witness gain if betting hands can choose sizes within a shared group."""
    assert len(game.fold) == 2
    rows = []
    for i in range(game.check.shape[0]):
        values = [sum((Q(float(v)) for v in game.check[i]), Q(0))]
        for s in range(2):
            values.append(sum(((1-Q(p))*Q(float(f))+Q(p)*Q(float(a))
                for p, f, a in zip(witness[s], game.fold[s, i], game.call[s, i])), Q(0)))
        rows.append(values)
    gain, conflicting = Q(0), 0
    for g in sorted(set(groups)):
        rs = [v for v, label in zip(rows, groups) if label == g]
        totals = [sum((v[a] for v in rs), Q(0)) for a in range(3)]
        gain += max(totals[0], sum((max(v[1:]) for v in rs), Q(0)))-max(totals)
        preferred = {a for v in rs for a in (1, 2)
                     if all(v[a] > v[other]+Q('1e-10') for other in range(3) if a != other)}
        conflicting += preferred == {1, 2}
    return dict(size_gain_exact=str(gain), groups_with_both_strict_sizes=conflicting)
