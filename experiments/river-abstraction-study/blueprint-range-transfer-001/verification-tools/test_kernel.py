"""Exact parity against the frozen literal Fraction evaluator."""
import unittest
from fractions import Fraction as Q
import numpy as np
from support import m, r
from exact_kernel import Kernel


class ExactKernel(unittest.TestCase):
    def test_literal_parity_all_group_shapes(self):
        rng = np.random.default_rng(98171)
        for n, k in ((3, 4), (9, 7)):
            g = m.Game(rng.normal(size=(n, k)), rng.normal(size=(2, n, k)),
                       rng.normal(size=(2, n, k)))
            kernel = Kernel(g)
            for g0, g1 in ((list(range(n)), list(range(k))),
                           ([i % 2 for i in range(n)], [j % 3 for j in range(k)])):
                xs = rng.random((max(g0)+1, 3))
                ys = rng.random((2, max(g1)+1))
                x, y = xs[g0].tolist(), ys[:, g1].tolist()
                self.assertEqual(kernel.bounds(g, x, y, [g0, g1]),
                                 m.bounds(g, x, y, [g0, g1]))
                self.assertEqual(kernel.values(y), r.action_values(g, y))

    def test_zero_and_tie_payoffs(self):
        g = m.Game(np.zeros((3, 3)), np.zeros((2, 3, 3)), np.zeros((2, 3, 3)))
        k = Kernel(g)
        x, y = [[0, .5, .5]]*3, [[.25]*3, [.75]*3]
        self.assertEqual(k.bounds(g, x, y, [list(range(3))]*2), (Q(0), Q(0)))

    def test_certificate_parity(self):
        rng = np.random.default_rng(816)
        a = rng.normal(size=(7, 9))*.03
        g = m.Game(a, np.full((2, 7, 9), .01), np.array([2*a, 3*a]))
        groups = [[j % 3 for j in range(7)], list(range(9))]
        original = m.bounds
        try:
            expected = m.pair(g, groups)
            m.bounds = Kernel(g).bounds
            self.assertEqual(m.pair(g, groups), expected)
        finally:
            m.bounds = original

    def test_dyadic_extreme_coefficients(self):
        a = np.array([[2.**-99, 2.**-71], [-2.**-81, 0.]])
        g = m.Game(a, np.array([a, a*2]), np.array([a*3, -a]))
        x, y = [[.1, .2, .7], [.3, .3, .4]], [[.2, .8], [.1, .9]]
        self.assertEqual(Kernel(g).bounds(g, x, y, [[0, 1], [0, 1]]),
                         m.bounds(g, x, y, [[0, 1], [0, 1]]))


if __name__ == '__main__':
    unittest.main()
