"""Full-combo comparison using retained games, LPs, and regret learner."""
from pathlib import Path
import sys
import importlib.util
from time import perf_counter
from fractions import Fraction as Q

ROOT = Path('D:/Pontius-worktrees/eval-runner-consolidation')
HISTORY = ROOT/'experiments/river-abstraction-study'
PREVIOUS = HISTORY/'river-stack-transfer-001'
spec = importlib.util.spec_from_file_location('frozen_stack_bridge',
    PREVIOUS/'verification-tools/stack_bridge.py')
b = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = b
spec.loader.exec_module(b)
m, np, c = b.m, b.np, b.c
read, write, digest = b.read, b.write, b.digest
literal = m.bounds
old_kernel = sys.modules[b.e.Kernel.__module__]


class Kernel(b.e.Kernel):
    """Generalize the frozen integer evaluator to one or two distinct bet sizes."""
    def __init__(self, game):
        super().__init__(game)
        self.bound_seconds = 0.

    def bounds(self, game, x, y, groups):
        start = perf_counter()
        assert game is self.game
        xx, yy = m.policies(game, x, y)
        bets = len(game.fold)
        gx, xs = old_kernel.labels(xx)
        gy, ys = old_kernel.labels(zip(*yy))
        xi, dx = old_kernel.integers(xs)
        yi, dy = old_kernel.integers(ys)
        arrays = self.aggregate(gx, groups[1])
        low = sum(xi[:, 0]*arrays[0].sum(axis=1))
        for s in range(bets):
            f, a = arrays[1+s], arrays[1+bets+s]
            low += sum(min(v, w) for v, w in zip(xi[:, s+1] @ f, xi[:, s+1] @ a))
        arrays = self.aggregate(groups[0], gy)
        values = [arrays[0].sum(axis=1)*dy]
        for s in range(bets):
            f, a = arrays[1+s], arrays[1+bets+s]
            values.append(f.sum(axis=1)*dy+(a-f) @ yi[:, s])
        high = sum(max(row) for row in zip(*values))
        answer = Q(int(low), self.denominator*dx), Q(int(high), self.denominator*dy)
        assert answer[0] <= answer[1]
        self.bound_seconds += perf_counter()-start
        return answer


def build(record):
    menu = b.admission(record)
    _, groups, _ = b.original_build(record)
    hands, joint, signs, compatible = b.population(record)
    hero, villain = record['role_seats']
    pot, sizes = menu['pot'], menu['distinct_sizes']
    tie = (pot % 2)*(.5 if hero < villain else -.5)
    scale = 10/pot
    check = joint*(signs*(pot/2)+(signs == 0)*tie)*scale
    fold = joint*(pot/2)*scale
    calls = [joint*(signs*(pot/2+bet)+(signs == 0)*tie)*scale for bet in sizes]
    game = m.Game(check, [fold]*len(sizes), calls)
    from hashlib import sha256
    meta = dict(menu=menu, shapes=dict(check=list(check.shape), call=list(game.call.shape)),
        hashes={k: sha256(np.ascontiguousarray(v).tobytes()).hexdigest()
                for k, v in [('joint', joint), ('check', check),
                             ('fold', game.fold), ('call', game.call)]})
    return game, groups, meta


def coefficient_audit(game, kernel):
    checked = 0
    for raw, integers in zip([game.check, *game.fold, *game.call], kernel.arrays):
        for value, integer in zip(raw.flat, integers.flat):
            n, den = float(value).as_integer_ratio()
            assert int(integer)*den == n*kernel.denominator
            checked += 1
    return checked


def profile_audit(game, kernel, profile):
    gs = [list(range(n)) for n in game.check.shape]
    bounds = kernel.bounds(game, profile['x'], profile['y'], gs)
    assert profile['bounds'] == list(map(str, bounds))
    assert bounds[1]-bounds[0] <= Q('1e-8')
    for start in (0, 237, 811):
        ii = [(start+17*k) % 1081 for k in range(9)]
        jj = [(start+31*k+7) % 1081 for k in range(11)]
        sub = m.Game(game.check[np.ix_(ii, jj)], game.fold[:, ii][:, :, jj],
                     game.call[:, ii][:, :, jj])
        x = [profile['x'][k] for k in ii]
        y = [[row[k] for k in jj] for row in profile['y']]
        assert Kernel(sub).bounds(sub, x, y, [list(range(9)), list(range(11))]) == \
            literal(sub, x, y, [list(range(9)), list(range(11))])
    return (bounds[1]-bounds[0])/2
