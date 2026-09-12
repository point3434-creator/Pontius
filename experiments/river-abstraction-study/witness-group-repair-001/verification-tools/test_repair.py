from environment import np, opt, core, PayoffGame
from fractions import Fraction as Q
from itertools import combinations, product
import unittest
import repair


def fixture():
    joint = np.eye(4)/4
    return PayoffGame(joint, np.zeros((4, 4)), np.diag([.25, .25, 0, 0]),
                      np.diag([.5, -.5, 0, 0]), None, 'synthetic')


class RepairTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(callable(getattr(repair, 'propose', None)), 'repair is absent')

    def test_utility_signs_and_joint_mass(self):
        m = fixture()
        self.assertEqual(repair.deltas(m, [1, 1, 0, 0], 0),
                         [Q(1, 2), -Q(1, 2), Q(0), Q(0)])
        self.assertEqual(repair.deltas(m, [1, 1, 0, 0], 1),
                         [-Q(1, 4), Q(3, 4), Q(0), Q(0)])

    def test_split_merge_removes_known_restriction_cost(self):
        m = fixture()
        groups = [[0, 0, 1, 2], [0, 0, 1, 2]]
        weights = [np.eye(3)[g] for g in groups]
        baseline = core.solve(m, weights)
        before = baseline['minimum_exploitability']
        self.assertLessEqual(Q(before['lower_exact']), Q(1, 6))
        self.assertGreaterEqual(Q(before['upper_exact']), Q(1, 6))
        proposal = repair.propose(m, groups, baseline)
        for g in proposal['groups']:
            self.assertNotEqual(g[0], g[1])
            self.assertEqual(g[2], g[3])
            self.assertEqual(set(g), {0, 1, 2})
        after = core.solve(m, [np.eye(3)[g] for g in proposal['groups']])
        self.assertLess(float(Q(after['minimum_exploitability']['upper_exact'])), 1e-8)

    def test_no_conflict_zero_advantage_or_insufficient_groups_is_noop(self):
        for groups, changes in [([0, 0, 1, 2], [1, 2, -1, -2]),
                                 ([0, 0, 1, 2], [0, 0, 0, 0]),
                                 ([0, 0, 1, 1], [1, -1, 1, -1])]:
            result = repair.exchange(groups, list(map(Q, changes)))
            self.assertEqual(result['groups'], groups)
            self.assertFalse(result['changed'])

    def test_rejects_tampered_witness_before_proposal(self):
        m, groups = fixture(), [[0, 0, 1, 2]]*2
        baseline = core.solve(m, [np.eye(3)[g] for g in groups])
        baseline['seat0']['coefficients'][1][0] = 2.0
        with self.assertRaises(ValueError):
            repair.propose(m, groups, baseline)

    def test_exchange_objective_matches_exhaustive_binary_group_policies(self):
        groups = [0, 0, 1, 1, 2, 2, 3, 3]
        def objective(g, d):
            return max(sum(d[i]*actions[g[i]] for i in range(len(g)))
                       for actions in product((0, 1), repeat=len(set(g))))
        rng = np.random.default_rng(519)
        for _ in range(30):
            d = [Q(int(x), 8) for x in rng.integers(-7, 8, size=8)]
            original = objective(groups, d)
            possible = [original]
            for split in range(4):
                for a, b in combinations([x for x in range(4) if x != split], 2):
                    g = [4 if x == split and d[i] <= 0 else a if x == b else x
                         for i, x in enumerate(groups)]
                    mapping = {v: i for i, v in enumerate(sorted(set(g)))}
                    g = [mapping[x] for x in g]
                    if len(set(g)) == 4:
                        possible.append(objective(g, d))
            result = repair.exchange(groups, d)
            self.assertEqual(objective(result['groups'], d), max(possible))
            self.assertEqual(Q(result['net_witness_gain_exact']), max(possible)-original)
            self.assertEqual(len(set(result['groups'])), 4)

    def test_zeros_have_deterministic_side_and_witness_score_reconstructs(self):
        result = repair.exchange([0, 0, 0, 1, 2], [Q(3), Q(-2), Q(0), Q(0), Q(0)])
        self.assertEqual(result['groups'][1], result['groups'][2])
        self.assertNotEqual(result['groups'][0], result['groups'][1])
        self.assertEqual(Q(result['net_witness_gain_exact']), 2)


if __name__ == '__main__':
    unittest.main(verbosity=2)
