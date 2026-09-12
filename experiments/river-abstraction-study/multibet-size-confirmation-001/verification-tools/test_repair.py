"""Analytic proposal, gate and retained-trainer equivalence checks."""
from fractions import Fraction as Q
import unittest
import size_repair as r


class RepairTests(unittest.TestCase):
    def test_known_split_gain_and_capacity(self):
        values = [[Q(0), Q(3), Q(0)], [Q(0), Q(0), Q(2)],
                  [Q(0), Q(1), Q(0)], [Q(0), Q(1), Q(0)]]
        result = r.exchange([0, 0, 1, 2], values)
        self.assertEqual(Q(result['net_gain']), 2)
        self.assertEqual(result['operation'], [0, 1, 2])
        self.assertEqual(len(set(result['groups'])), 3)
        self.assertNotEqual(result['groups'][0], result['groups'][1])

    def test_merge_cost_can_cancel_split_gain(self):
        values = [[Q(0), Q(1), Q(0)], [Q(0), Q(0), Q(1)],
                  [Q(0), Q(3), Q(0)], [Q(0), Q(0), Q(3)]]
        result = r.exchange([0, 0, 1, 2], values)
        self.assertEqual(result['groups'], [0, 0, 1, 2])
        self.assertIsNone(result['operation'])
        self.assertEqual(Q(result['net_gain']), 0)

    def test_gate_rejects_worse_and_accepts_tie(self):
        game = r.m.Game([[0.]], [[[1.]], [[2.]]], [[[-1.]], [[1.]]])
        groups, y = [[0], [0]], [[1.], [1.]]
        old = [[0., 0., 1.]]
        rejected = r.accept(game, groups, old, y, groups, [[0., 1., 0.]])
        self.assertFalse(rejected['accepted'])
        self.assertEqual(rejected['x'], old)
        self.assertTrue(r.accept(game, groups, old, y, groups, old)['accepted'])

    def test_bettor_only_matches_retained_trainer(self):
        game = r.m.Game([[.1], [-.1]], [[[.2], [.3]], [[.2], [.3]]],
                        [[[-.2], [.4]], [[-.5], [.7]]])
        groups = [[0, 1], [0]]
        a, b = r.Bettor(game, groups), r.m.Trainer(game, groups)
        for _ in range(300):
            a.step()
            b.step()
        self.assertEqual(a.average(), b.average()[0])


if __name__ == '__main__':
    unittest.main()
