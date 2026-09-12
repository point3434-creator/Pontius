"""Analytic games and exhaustive pure-response checks for the action-menu adapter."""
import unittest
from itertools import product
from fractions import Fraction as Q
import multi as m


class MultiTests(unittest.TestCase):
    def test_bet_sizes_observed_separately(self):
        game = m.Game([[-2.]], [[[1.]], [[-1.]]], [[[-1.]], [[1.]]])
        result = m.solve(game, [[0], [0]])
        self.assertAlmostEqual(float(Q(result['seat0']['bounds'][0])), -1.)
        self.assertEqual(result['seat1']['y'], [[1.], [0.]])

    def test_size_conflict_has_known_group_floor(self):
        game = m.Game([[0.], [0.]], [[[.5], [0.]], [[0.], [.5]]],
                      [[[.5], [0.]], [[0.], [.5]]])
        result = m.solve(game, [[0, 0], [0]])
        self.assertEqual(list(map(Q, result['floor'])), [Q(1, 4), Q(1, 4)])
        conflict = m.size_conflict(game, [0, 0], result['seat0']['y'])
        self.assertEqual(Q(conflict['size_gain_exact']), Q(1, 2))
        self.assertEqual(conflict['groups_with_both_strict_sizes'], 1)

    def test_bounds_equal_enumerated_responses(self):
        game = m.Game([[.1, -.2], [.3, .1]],
            [[[.2, .1], [.1, .4]], [[.3, .2], [.2, .5]]],
            [[[-.3, .4], [.5, -.2]], [[-.5, .6], [.7, -.4]]])
        x, y = [[1., 2., 3.], [4., 1., 2.]], [[.2, .8], [.7, .1]]
        low, high = m.bounds(game, x, y, [[0, 1], [0, 1]])
        def value(xx, yy):
            xx = [[Q(v)/sum(map(Q, row)) for v in row] for row in xx]
            total = Q(0)
            for i in range(2):
                for j in range(2):
                    total += xx[i][0]*Q(float(game.check[i, j]))
                    for s in range(2):
                        p = Q(yy[s][j])
                        total += xx[i][s+1]*((1-p)*Q(float(game.fold[s, i, j]))+
                                              p*Q(float(game.call[s, i, j])))
            return total
        self.assertEqual(low, min(value(x, [z[:2], z[2:]])
                                 for z in product((0, 1), repeat=4)))
        self.assertEqual(high, max(value([[int(a == k) for k in range(3)] for a in z], y)
                                  for z in product(range(3), repeat=2)))

    def test_one_bet_agrees_with_frozen_solver_and_training(self):
        old = m.c.frozen.synthetic_game()
        groups = [[0, 0, 1, 2]]*2
        game = m.Game(old.check, [old.fold], [old.call])
        expected = m.c.core.solve(old, m.c.weights(groups))
        actual = m.solve(game, groups)
        self.assertLess(abs(float(Q(actual['floor'][0])-Q(
            expected['minimum_exploitability']['lower_exact']))), 1e-8)
        a, b = m.Trainer(game, groups), m.c.core.RegretBR(old, m.c.weights(groups))
        for _ in range(300):
            a.step()
            b.step()
        x, y = a.average()
        bx, by = b.average()
        m.np.testing.assert_allclose(m.np.array(x)[:, 1], bx, atol=1e-12)
        m.np.testing.assert_allclose(y[0], by, atol=1e-12)

    def test_negative_policy_refused(self):
        game = m.Game([[0.]], [[[1.]]], [[[-1.]]])
        with self.assertRaises(AssertionError):
            m.bounds(game, [[-.1, 1.1]], [[.5]], [[0], [0]])


if __name__ == '__main__':
    unittest.main()
