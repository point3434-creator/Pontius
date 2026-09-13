"""Independent small-game and hand-derived update checks; no retained solves."""
import unittest
import itertools
import numpy as np
from solver import Solver, update, normalize


class Checks(unittest.TestCase):
    def test_discount_and_prediction(self):
        old = np.array([[2., 0., 1.]])
        regret = np.array([[-.5, 1., -2.]])
        r, p = update(old, regret, 2, 1., 1., False)
        np.testing.assert_array_equal(r, [[.5, 1., 0.]])
        np.testing.assert_allclose(p, [[1/3, 2/3, 0.]])
        r, p = update(old, regret, 2, 1., 1., True)
        np.testing.assert_allclose(p, [[0., 1., 0.]])
        r, p = update(old, regret, 2, 1., 1.5, False)
        np.testing.assert_allclose(r, [[.3, 1., 0.]])

    def test_uniform_zero(self):
        np.testing.assert_allclose(normalize(np.zeros((2, 3))), np.ones((2, 3))/3)

    def test_matching_pennies(self):
        nodes = [dict(player=0, children=[1, 4]),
                 dict(player=1, children=[2, 3]),
                 dict(player=-1, payoff=['a']), dict(player=-1, payoff=['b']),
                 dict(player=1, children=[5, 6]),
                 dict(player=-1, payoff=['b']), dict(player=-1, payoff=['a'])]
        # Perfect information at the response nodes: minimizer wins -1.
        arrays = {('a',): np.ones((1, 1)), ('b',): -np.ones((1, 1))}
        s = Solver(nodes, arrays, dict(alpha=1.5, denominator=1., predict=True, gamma=4))
        for _ in range(256):
            s.step()
        score = s.score(s.average())
        self.assertLess(score['gap'], 1e-6)
        self.assertAlmostEqual(score['value'], -1., places=6)

    def test_literal_counterfactual_and_br(self):
        # Hidden hand plus two decisions by role 0. Own reach must not weight regret.
        nodes = [dict(player=0, children=[1, 2]), dict(player=-1, payoff=['a']),
                 dict(player=1, children=[3, 4]), dict(player=-1, payoff=['b']),
                 dict(player=0, children=[5, 6]),
                 dict(player=-1, payoff=['c']), dict(player=-1, payoff=['d'])]
        arrays = { (k,): np.array(v, dtype=float)/16 for k, v in dict(
            a=[[2, 0], [1, 3]], b=[[-3, 0], [1, -1]],
            c=[[4, 0], [-2, 2]], d=[[-2, 0], [3, -1]]).items() }
        s = Solver(nodes, arrays, dict(alpha=None, denominator=1., predict=False, gamma=4))
        s.policy = {0: np.array([[.2,.8],[.7,.3]]),
                    2: np.array([[.1,.9],[.4,.6]]),
                    4: np.array([[.3,.7],[.8,.2]])}
        def literal(p):
            def visit(i, h0, h1):
                node = nodes[i]
                if node['player'] == -1:
                    return arrays[tuple(node['payoff'])][h0,h1]
                h = h0 if node['player'] == 0 else h1
                return sum(p[i][h,a]*visit(c,h0,h1)
                           for a,c in enumerate(node['children']))
            return sum(visit(0,i,j) for i in range(2) for j in range(2))
        score = s.score(s.policy)
        self.assertAlmostEqual(score['value'], literal(s.policy), places=14)
        for role, key, choose in [(0,'upper',max),(1,'lower',min)]:
            owned = [i for i,n in enumerate(nodes) if n['player']==role]
            values = []
            for bits in itertools.product(range(2), repeat=2*len(owned)):
                p = {i:v.copy() for i,v in s.policy.items()}
                for q,i in enumerate(owned):
                    p[i] = np.eye(2)[list(bits[2*q:2*q+2])]
                values.append(literal(p))
            self.assertAlmostEqual(score[key], choose(values), places=14)
        regrets = s.regrets_for(0)
        action_values = np.stack([arrays[(k,)] @ s.policy[2][:,1] for k in ('c','d')],1)
        expected = action_values - np.sum(action_values*s.policy[4],1,keepdims=True)
        np.testing.assert_allclose(regrets[4], expected, atol=1e-15)
        # Average realization, not unweighted local probabilities at the later node.
        s.step()
        np.testing.assert_allclose(s.average()[4], [[.3,.7],[.8,.2]])
        for _ in range(7):
            s.step()
        for p in s.average().values():
            self.assertTrue(np.isfinite(p).all())
            np.testing.assert_allclose(p.sum(1), 1.)


if __name__ == '__main__':
    unittest.main()
