"""Behavior checks: exact extrema, class restrictions, and hard-path parity."""
from environment import np, opt, PayoffGame
from fractions import Fraction as Q
from itertools import product
import copy
import ast
from pathlib import Path
import unittest
import soft


def fixture():
    # V = x0*(1/2+y0/2) + x1*(1/2-3*y1/2).
    return PayoffGame(np.eye(2)/2, np.zeros((2, 2)), np.eye(2)/2,
                      np.diag([1., -1.]), None, 'synthetic')


class SoftTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(callable(getattr(soft, 'assignments', None)),
                        'soft assignment implementation is absent')

    def test_two_neighbour_weights_and_exact_row_mass(self):
        f = [[0.], [1.], [3.], [4.]]
        labels = [0, 0, 1, 1]
        hard, mixed = soft.assignments(f, [1, 1, 1, 1], labels)
        self.assertEqual(hard.tolist(), [[1, 0], [1, 0], [0, 1], [0, 1]])
        # Centers 0.5,3.5; inverse-distance interpolation is exactly 7/8,5/6,...
        self.assertEqual(mixed[0].tolist(), [.875, .125])
        self.assertAlmostEqual(mixed[1, 1], 1/6, delta=1/2**20)
        for row in mixed:
            self.assertEqual(sum(map(Q, row)), 1)
            self.assertLessEqual(np.count_nonzero(row), 2)

    def test_duplicate_centers_single_group_and_exact_center(self):
        for features, labels in [([[1.], [1.]], [0, 1]),
                                 ([[0.], [2.]], [0, 0]),
                                 ([[0.], [2.]], [0, 1])]:
            hard, mixed = soft.assignments(features, [1, 1], labels)
            np.testing.assert_array_equal(hard, mixed)

    def test_invalid_embeddings_refused_before_algebra(self):
        for p in ([[1., -.1], [0., 1.]], [[.1, .8], [0., 1.]],
                  [[float('nan'), 0], [0, 1]], [[True, False], [False, True]],
                  [['1', '0'], ['0', '1']], [[.5, .5]]):
            with self.subTest(p=p), self.assertRaises(ValueError):
                soft.validate(p, 2)

    def test_one_hot_floor_matches_old_certified_solver(self):
        for labels, expected in [(([0, 1], [0, 1]), Q(0)),
                                  (([0, 0], [0, 1]), Q(1, 4)),
                                  (([0, 1], [0, 0]), Q(1, 12)),
                                  (([0, 0], [0, 0]), Q(1, 3))]:
            weights = [np.eye(max(g)+1)[g] for g in labels]
            actual = soft.solve(fixture(), weights)
            bounds = actual['minimum_exploitability']
            self.assertLessEqual(Q(bounds['lower_exact']), expected)
            self.assertGreaterEqual(Q(bounds['upper_exact']), expected)
            prior = opt.solve_groups(fixture(), labels)['minimum_exploitability']
            self.assertLessEqual(Q(bounds['lower_exact']), Q(prior['upper_exact']))
            self.assertGreaterEqual(Q(bounds['upper_exact']), Q(prior['lower_exact']))

    def test_soft_certificates_match_enumerated_latent_corners(self):
        p = [[1., 0.], [.25, .75]]
        q = [[.5, .5], [0., 1.]]
        a, b = [.25, .75], [.75, .25]
        def lift(w, z):
            return [sum(Q(v)*Q(t) for v, t in zip(row, z)) for row in w]
        def payoff(x, y):
            return x[0]*(Q(1, 2)+y[0]/2)+x[1]*(Q(1, 2)-3*y[1]/2)
        x, y = lift(p, a), lift(q, b)
        low, high = soft.exact_bounds(fixture(), [p, q], [a, b])
        corners = list(product((0, 1), repeat=2))
        self.assertEqual(low, min(payoff(x, lift(q, c)) for c in corners))
        self.assertEqual(high, max(payoff(lift(p, c), y) for c in corners))

    def test_softening_can_destroy_an_exact_policy_class(self):
        # Both latent corners force x0=x1 after the rows become identical.
        weights = [np.full((2, 2), .5), np.eye(2)]
        result = soft.solve(fixture(), weights)
        bounds = result['minimum_exploitability']
        self.assertLessEqual(Q(bounds['lower_exact']), Q(1, 4))
        self.assertGreaterEqual(Q(bounds['upper_exact']), Q(1, 4))
        self.assertGreater(float(Q(bounds['lower_exact'])), .24)

    def test_tampered_witness_and_suboptimal_lp_are_rejected(self):
        weights = [np.eye(2), np.eye(2)]
        record = soft.solve(fixture(), weights)
        for key in ('coefficients', 'value'):
            bad = copy.deepcopy(record)
            if key == 'coefficients':
                bad['seat0'][key][0] = [0., 0.]
            else:
                bad['seat0'][key]['upper_exact'] = '999'
            with self.assertRaises(ValueError):
                soft.verify(fixture(), weights, bad)

    def test_learner_reaches_restriction_floor_and_replays(self):
        weights = [np.ones((2, 1)), np.eye(2)]
        first, second = (soft.RegretBR(fixture(), weights) for _ in range(2))
        with self.assertRaises(ValueError):
            first.average()
        for _ in range(2000):
            first.step()
            second.step()
        for a, b in zip(first.average(), second.average()):
            np.testing.assert_array_equal(a, b)
        x, y = [p @ a for p, a in zip(weights, first.average())]
        score = fixture().evaluate(x, y)['exploitability']
        self.assertGreaterEqual(score, .25-1e-14)
        self.assertLess(score, .255)

    def test_hard_learner_matches_frozen_predecessor_step_for_step(self):
        # Execute only the predecessor class, avoiding its historical driver imports.
        source = Path('D:/Pontius/tmp/witness-pot-diagnostic-author/br.py').read_text()
        tree = ast.parse(source)
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef))
        from environment import _regret_match
        scope = dict(np=np, opt=opt, _regret_match=_regret_match)
        exec(compile(ast.Module(body=[cls], type_ignores=[]), '<frozen-br>', 'exec'), scope)
        rng = np.random.default_rng(701)
        shape = (7, 5)
        m = PayoffGame(np.ones(shape)/35, *(rng.normal(size=shape) for _ in range(3)),
                       None, 'synthetic')
        groups = ([0, 0, 1, 1, 2, 2, 2], [0, 0, 1, 1, 1])
        old = scope['RegretBR'](m, groups)
        new = soft.RegretBR(m, [np.eye(max(g)+1)[g] for g in groups])
        for _ in range(100):
            old.step()
            new.step()
            for a, b in zip(old.regrets+old.sums, new.regrets+new.sums):
                np.testing.assert_array_equal(a, b)

    def test_nonsymmetric_extrema_against_independent_corner_enumeration(self):
        rng = np.random.default_rng(841)
        for _ in range(12):
            arrays = [rng.integers(-4, 5, size=(3, 2))/8 for _ in range(3)]
            m = PayoffGame(np.ones((3, 2))/6, *arrays, None, 'synthetic')
            weights = [np.column_stack((t, 1-t)) for t in
                       (rng.integers(0, 9, size=3)/8, rng.integers(0, 9, size=2)/8)]
            policies = rng.integers(0, 9, size=(2, 2))/8
            def value(a, b):
                x = [sum(Q(float(w))*Q(float(z)) for w, z in zip(row, a))
                     for row in weights[0]]
                y = [sum(Q(float(w))*Q(float(z)) for w, z in zip(row, b))
                     for row in weights[1]]
                return sum((1-x[i])*Q(float(arrays[0][i, j]))+
                           x[i]*(1-y[j])*Q(float(arrays[1][i, j]))+
                           x[i]*y[j]*Q(float(arrays[2][i, j]))
                           for i in range(3) for j in range(2))
            corners = list(product((0., 1.), repeat=2))
            low, high = soft.exact_bounds(m, weights, policies)
            self.assertEqual(low, min(value(policies[0], b) for b in corners))
            self.assertEqual(high, max(value(a, policies[1]) for a in corners))


if __name__ == '__main__':
    unittest.main(verbosity=2)
