"""Analytic acceptance controls; no LP solve or training."""
from fractions import Fraction as Q
from unittest.mock import patch
import unittest
from base import c
import gate


class GateTests(unittest.TestCase):
    def setUp(self):
        self.m = c.PayoffGame(c.np.ones((1, 1)), c.np.zeros((1, 1)),
                             c.np.ones((1, 1)), -c.np.ones((1, 1)), None, 'one-deal')
        self.groups = [[0], [0]]

    def apply(self, old, new):
        return gate.select(self.m, self.groups, old, self.groups, new)

    def test_both_improve(self):
        result = self.apply([[1], [0]], [[0], [1]])
        self.assertEqual(result['accepted'], [True, True])
        self.assertEqual(result['security_exact'], [['-1', '-1'], ['0', '0']])

    def test_keep_original_caller(self):
        result = self.apply([[1], [1]], [[0], [0]])
        self.assertEqual(result['accepted'], [True, False])
        self.assertEqual(result['coefficients'], [[0], [1]])

    def test_keep_original_bettor(self):
        result = self.apply([[0], [0]], [[1], [1]])
        self.assertEqual(result['accepted'], [False, True])
        self.assertEqual(result['coefficients'], [[0], [1]])

    def test_exact_ties_are_accepted(self):
        self.assertEqual(self.apply([[0], [1]], [[0], [1]])['accepted'], [True, True])

    def test_no_lp_is_used(self):
        with patch.object(c.opt, 'linprog', side_effect=AssertionError('LP forbidden')):
            self.assertEqual(self.apply([[1], [0]], [[0], [1]])['accepted'], [True, True])

    def test_invalid_probability_refuses(self):
        with self.assertRaises(ValueError):
            self.apply([[0], [1]], [[float('nan')], [1]])

    def test_independent_security_matches_toy_values(self):
        self.assertEqual(gate.audit_security(self.m, [[Q(1)], [Q(0)]]), [Q(-1), Q(-1)])
        self.assertEqual(gate.audit_security(self.m, [[Q(0)], [Q(1)]]), [Q(0), Q(0)])


if __name__ == '__main__':
    unittest.main()
