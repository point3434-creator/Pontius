"""One bettor size split, one compensating merge, exact worst-case acceptance."""
from support import m, c
from fractions import Fraction as Q
from itertools import combinations


def action_values(game, witness):
    rows = []
    for i in range(game.check.shape[0]):
        values = [sum((Q(float(v)) for v in game.check[i]), Q(0))]
        for s in range(2):
            values.append(sum(((1-Q(p))*Q(float(f))+Q(p)*Q(float(a))
                for p, f, a in zip(witness[s], game.fold[s, i], game.call[s, i])), Q(0)))
        rows.append(values)
    return rows


def objective(groups, values):
    return sum((max(sum((v[a] for v, label in zip(values, groups) if label == g), Q(0))
                       for a in range(3)) for g in sorted(set(groups))), Q(0))


def exchange(groups, values):
    k = len(set(groups))
    assert set(groups) == set(range(k)) and len(groups) == len(values)
    assert all(len(v) == 3 and all(type(x) is Q for x in v) for v in values)
    totals = [[sum((v[a] for v, label in zip(values, groups) if label == g), Q(0))
               for a in range(3)] for g in range(k)]
    best, operation, result, examined = Q(0), None, list(groups), 0
    for split in range(k):
        left = [v for v, g in zip(values, groups) if g == split and v[2] > v[1]]
        right = [v for v, g in zip(values, groups) if g == split and v[2] <= v[1]]
        if not left or not right:
            continue
        gain = sum((max(sum((v[a] for v in rs), Q(0)) for a in range(3))
                    for rs in (left, right)), Q(0))-max(totals[split])
        for a, b in combinations([g for g in range(k) if g != split], 2):
            cost = max(totals[a])+max(totals[b])-max(x+y for x, y in zip(totals[a], totals[b]))
            examined += 1
            if gain-cost > best:
                best, operation = gain-cost, [split, a, b]
    if operation is not None:
        split, a, b = operation
        labels = [k if g == split and v[2] > v[1] else a if g == b else g
                  for g, v in zip(groups, values)]
        mapping = {g: i for i, g in enumerate(sorted(set(labels)))}
        result = [mapping[g] for g in labels]
    assert len(set(result)) == k and objective(result, values)-objective(groups, values) == best
    return dict(groups=result, operation=operation, net_gain=str(best), examined=examined)


class Bettor:
    def __init__(self, game, groups):
        self.game = m.reduced(game, [groups[0], list(range(game.check.shape[1]))])
        self.regrets = m.np.zeros((max(groups[0])+1, 3))
        self.sums = m.np.zeros_like(self.regrets)
        self.iteration = 0

    def step(self):
        x, game = m.match(self.regrets), self.game
        options = [game.check.sum(axis=1)]
        for s in range(2):
            f, a = x[:, s+1] @ game.fold[s], x[:, s+1] @ game.call[s]
            response = m.np.where(a < f, 1., m.np.where(a > f, 0., .5))
            options.append(game.fold[s].sum(axis=1)+(game.call[s]-game.fold[s]) @ response)
        value = m.np.column_stack(options)
        self.sums += x
        self.regrets += value-(x*value).sum(axis=-1, keepdims=True)
        self.iteration += 1

    def average(self):
        assert self.iteration > 0
        return (self.sums/self.iteration).tolist()


def security(game, groups, x, y):
    xx, yy = m.expand(groups, x, y)
    return m.bounds(game, xx, yy, [list(range(n)) for n in game.check.shape])


def accept(game, groups, old_x, y, new_groups, new_x):
    assert groups[1] == new_groups[1]
    old, new = security(game, groups, old_x, y), security(game, new_groups, new_x, y)
    assert old[1] == new[1], 'caller strategy changed'
    accepted = new[0] >= old[0]
    chosen_groups, x = (new_groups, new_x) if accepted else (groups, old_x)
    return dict(accepted=accepted, groups=chosen_groups, x=x, y=y,
        old_bounds=list(map(str, old)), new_bounds=list(map(str, new)),
        score=m.score(game, chosen_groups, x, y))


def audit_security(game, groups, x, y):
    """Independent fold/call sums for bettor security; no bounds evaluator."""
    xx, yy = m.expand(groups, x, y)
    xx, _ = m.policies(game, xx, yy)
    value = sum((xx[i][0]*Q(float(game.check[i, j])) for i in range(len(xx))
                 for j in range(game.check.shape[1])), Q(0))
    for s in range(2):
        for j in range(game.check.shape[1]):
            outcomes = [sum((xx[i][s+1]*Q(float(payoff[s, i, j])) for i in range(len(xx))), Q(0))
                        for payoff in (game.fold, game.call)]
            value += min(outcomes)
    return value
