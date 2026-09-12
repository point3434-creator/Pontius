"""Analytic controls for security values and partition feasibility."""
import unittest
from fractions import Fraction as Q
import diagnostic as d


class DiagnosticTests(unittest.TestCase):
    def test_security_on_one_deal(self):
        game = d.Kernel([[Q(0)]], [[Q(1)]], [[Q(-1)]])
        self.assertEqual(game.security([Q(1)], 0), -1)
        self.assertEqual(game.security([Q(0)], 0), 0)
        self.assertEqual(game.security([Q(0)], 1), -1)
        self.assertEqual(game.security([Q(1)], 1), 0)
        self.assertEqual(game.best([Q(0)], [0], 0), 1)
        self.assertEqual(game.best([Q(1)], [0], 1), 1)

    def test_caller_advantage_includes_bettor_reach(self):
        game = d.Kernel([[Q(0)]], [[Q(1)]], [[Q(-1)]])
        self.assertEqual(game.advantages([Q(0)], 1), [0])
        self.assertEqual(game.advantages([Q(1, 4)], 1), [Q(1, 2)])

    def test_partition_can_destroy_an_old_policy(self):
        self.assertFalse(d.feasible([0, 0], [Q(0), Q(1)]))
        self.assertTrue(d.feasible([0, 0], [Q(1, 2), Q(1, 2)]))
        self.assertTrue(d.feasible([0, 1], [Q(0), Q(1)]))

    def test_gate_composition_has_additive_exploitability(self):
        game = d.Kernel([[Q(0)]], [[Q(1)]], [[Q(-1)]])
        old = [[Q(1)], [Q(0)]]
        new = [[Q(0)], [Q(1)]]
        old_security = [game.security(old[s], s) for s in (0, 1)]
        new_security = [game.security(new[s], s) for s in (0, 1)]
        self.assertEqual(-sum(old_security)/2, 1)
        self.assertEqual(-sum(new_security)/2, 0)

    def test_cost_changes_with_opponent(self):
        # The same merge is free for like signs and costly for opposite signs.
        self.assertEqual(d.merge_cost([Q(2), Q(3)], [0, 1], 0, 1), 0)
        self.assertEqual(d.merge_cost([Q(2), Q(-3)], [0, 1], 0, 1), 2)


if __name__ == '__main__':
    unittest.main()
