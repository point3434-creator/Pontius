"""Integer aggregation of exact binary64 payoffs; no rounded group sums."""
from collections import OrderedDict
from fractions import Fraction as Q
from math import lcm
import numpy as np
from support import m


def labels(rows):
    lookup, result, representatives = {}, [], []
    for row in rows:
        key = tuple(row)
        if key not in lookup:
            lookup[key] = len(lookup)
            representatives.append(key)
        result.append(lookup[key])
    return result, representatives


def integers(values):
    denominator = lcm(*(v.denominator for row in values for v in row))
    array = np.array([[v.numerator*(denominator//v.denominator) for v in row]
                      for row in values], dtype=object)
    return array, denominator


class Kernel:
    def __init__(self, game):
        self.game = game
        arrays = [game.check, *game.fold, *game.call]
        exponents = [int(np.frexp(np.abs(a[a != 0]))[1].min())
                     for a in arrays if np.any(a != 0)]
        power = max(0, 53-min(exponents)) if exponents else 0
        assert power < 1000, 'outside bounded experiment coefficient scale'
        self.denominator = 1 << power
        scale = float(self.denominator)
        cast = np.frompyfunc(int, 1, 1)
        self.arrays = [cast(a*scale) for a in arrays]
        self.cache = OrderedDict()

    def aggregate(self, rows, cols):
        key = (tuple(rows), tuple(cols))
        if key in self.cache:
            self.cache.move_to_end(key)
            return self.cache[key]
        assert set(rows) == set(range(max(rows)+1))
        assert set(cols) == set(range(max(cols)+1))
        rr, cc = np.asarray(rows), np.asarray(cols)
        result = []
        for a in self.arrays:
            b = a if rows == list(range(len(rows))) else np.stack(
                [a[rr == i].sum(axis=0) for i in range(max(rows)+1)])
            b = b if cols == list(range(len(cols))) else np.stack(
                [b[:, cc == i].sum(axis=1) for i in range(max(cols)+1)], axis=1)
            result.append(b)
        self.cache[key] = result
        if len(self.cache) > 6:
            self.cache.popitem(last=False)
        return result

    def bounds(self, game, x, y, groups):
        assert game is self.game
        xx, yy = m.policies(game, x, y)
        n, k = game.check.shape
        assert len(groups[0]) == n and len(groups[1]) == k
        gx, xs = labels(xx)
        gy, ys = labels(zip(*yy))
        xi, dx = integers(xs)
        yi, dy = integers(ys)
        check, f0, f1, c0, c1 = self.aggregate(gx, groups[1])
        low = sum(xi[:, 0]*check.sum(axis=1))
        for s, f, a in ((1, f0, c0), (2, f1, c1)):
            low += sum(min(v, w) for v, w in zip(xi[:, s] @ f, xi[:, s] @ a))
        check, f0, f1, c0, c1 = self.aggregate(groups[0], gy)
        values = [check.sum(axis=1)*dy]
        for s, f, a in ((0, f0, c0), (1, f1, c1)):
            values.append(f.sum(axis=1)*dy+(a-f) @ yi[:, s])
        high = sum(max(row) for row in zip(*values))
        answer = Q(int(low), self.denominator*dx), Q(int(high), self.denominator*dy)
        assert answer[0] <= answer[1]
        return answer

    def values(self, y):
        yy = [[Q(float(v)) for v in row] for row in y]
        gy, ys = labels(zip(*yy))
        yi, dy = integers(ys)
        check, f0, f1, c0, c1 = self.aggregate(list(range(self.game.check.shape[0])), gy)
        result = [check.sum(axis=1)*dy]
        for s, f, a in ((0, f0, c0), (1, f1, c1)):
            result.append(f.sum(axis=1)*dy+(a-f) @ yi[:, s])
        return [[Q(int(v), self.denominator*dy) for v in row] for row in zip(*result)]
