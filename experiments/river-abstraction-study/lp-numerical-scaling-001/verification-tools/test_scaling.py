import json
from pathlib import Path
import sys
import unittest
from fractions import Fraction as Q
import numpy as np
from scipy.optimize import linprog

RED = '--red' in sys.argv
if RED:
    sys.argv.remove('--red')


class Scaling(unittest.TestCase):
    def test_tiny_real_constraint_is_not_discarded(self):
        solver = linprog if RED else __import__('scaling').solve
        result = solver(np.array([-1.]), A_ub=np.array([[1e-10]]),
            b_ub=np.array([0.]), bounds=[(0, 1)], method='highs-ds',
            options=dict(primal_feasibility_tolerance=1e-9,
                         dual_feasibility_tolerance=1e-9, time_limit=10, maxiter=20000))
        self.assertTrue(result.success)
        self.assertEqual(result.x[0], 0., 'positive coefficient implies x <= 0')

    @unittest.skipIf(RED, 'adapter controls apply after correction')
    def test_exact_change_of_units_with_free_value_variable(self):
        import scaling as s
        c = np.array([-0.25, -1.])
        a = np.array([[-2**-40, 1.], [-0.125, 1.]])
        kw = dict(A_ub=a, b_ub=np.array([0., 0.5]), bounds=[(0,1),(None,None)])
        cost, new, policy = s.transform(c, kw)
        x = [Q(3,8), Q(1,2**44)]
        z = [x[0], x[1]*s.SCALE]
        self.assertEqual(sum(Q(float(v))*w for v,w in zip(cost,z)),
                         s.SCALE*sum(Q(float(v))*w for v,w in zip(c,x)))
        for old, scaled, rhs, rhs2 in zip(a, new['A_ub'], kw['b_ub'], new['b_ub']):
            self.assertEqual(sum(Q(float(v))*w for v,w in zip(scaled,z))-Q(float(rhs2)),
                s.SCALE*(sum(Q(float(v))*w for v,w in zip(old,x))-Q(float(rhs))))
        np.testing.assert_array_equal(a, [[-2**-40,1],[-.125,1]])
        np.testing.assert_array_equal(c, [-.25,-1])

    @unittest.skipIf(RED, 'adapter controls apply after correction')
    def test_unrepresentably_small_coefficient_refuses(self):
        import scaling as s
        with self.assertRaisesRegex(AssertionError, 'below cutoff'):
            s.transform([1.], dict(A_ub=np.array([[1e-30]]), b_ub=np.zeros(1),
                                   bounds=[(0,1)]))

    @unittest.skipIf(RED, 'adapter controls apply after correction')
    def test_one_and_two_size_literal_game_certificates(self):
        from diagnose import d
        import scaling as s
        rng = np.random.default_rng(77129)
        original = d.c.opt.linprog
        try:
            d.c.opt.linprog = s.solve
            for bets in (1,2):
                a = rng.normal(size=(7,9))*.01
                game = d.m.Game(a, np.full((bets,7,9),.01),
                               np.array([(j+2)*a for j in range(bets)]))
                groups = [list(range(7)),list(range(9))]
                d.m.bounds = d.Kernel(game).bounds
                answer = d.m.pair(game, groups)
                literal = d.literal(game, answer['x'], answer['y'], groups)
                self.assertEqual(list(map(str,literal)), answer['bounds'])
                self.assertLessEqual(literal[1]-literal[0], Q('1e-8'))
        finally:
            d.c.opt.linprog = original


if __name__ == '__main__':
    unittest.main()
