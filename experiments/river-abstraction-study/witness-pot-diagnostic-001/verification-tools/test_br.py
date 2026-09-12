"""Analytic and scalar tests for an unrestricted-best-response regret solver."""
from itertools import product
from math import fsum
import unittest

from context import np,PayoffGame,CFR,action_advantages,anchored_clusters
from br import RegretBR


def fixture():
    return PayoffGame(np.eye(2)/2,np.zeros((2,2)),np.eye(2)/2,
                      np.diag([1.,-1.]),None,'synthetic')


def match(rows):
    result=[]
    for a,b in rows:
        a,b=max(a,0),max(b,0)
        result.append([a/(a+b),b/(a+b)] if a+b else [.5,.5])
    return result


def scalar_step(matrix,groups,regrets,sums):
    c,f,a=(getattr(matrix,k).tolist() for k in ('check','fold','call'))
    s=[match(r) for r in regrets]
    x=[s[0][g][1] for g in groups[0]]
    y=[s[1][g][1] for g in groups[1]]
    fold=[fsum(x[i]*f[i][j] for i in range(len(x))) for j in range(len(y))]
    call=[fsum(x[i]*a[i][j] for i in range(len(x))) for j in range(len(y))]
    br_y=[1. if b<d else 0. if b>d else .5 for d,b in zip(fold,call)]
    check=[fsum(row) for row in c]
    betting=[fsum((1-y[j])*f[i][j]+y[j]*a[i][j] for j in range(len(y))) for i in range(len(x))]
    br_x=[1. if b>d else 0. if b<d else .5 for d,b in zip(check,betting)]
    values=[[[0.,0.] for _ in r] for r in regrets]
    for i,g in enumerate(groups[0]):
        values[0][g][0]+=check[i]
        values[0][g][1]+=fsum((1-br_y[j])*f[i][j]+br_y[j]*a[i][j] for j in range(len(y)))
    for j,g in enumerate(groups[1]):
        values[1][g][0]-=fsum(br_x[i]*f[i][j] for i in range(len(x)))
        values[1][g][1]-=fsum(br_x[i]*a[i][j] for i in range(len(x)))
    for seat in (0,1):
        for g,row in enumerate(values[seat]):
            v=sum(p*u for p,u in zip(s[seat][g],row))
            for action in (0,1):
                regrets[seat][g][action]+=row[action]-v
                sums[seat][g][action]+=s[seat][g][action]
    return br_x,br_y


class BRTests(unittest.TestCase):
    def test_witness_arithmetic_clipping_and_capacity(self):
        opponents=[[.2,.7],[0.,1.],[1.,0.]]
        first=action_advantages(fixture(),opponents,0)
        second=action_advantages(fixture(),opponents,1)
        np.testing.assert_allclose(first,[[1.2,1.,2.],[-1.1,-2.,1.]],rtol=0,atol=1e-14)
        np.testing.assert_allclose(second,[[-.2,0.,-1.],[2.1,3.,0.]],rtol=0,atol=1e-14)
        clipped=np.clip(first,-.5,.5)
        np.testing.assert_array_equal(clipped,[[.5,.5,.5],[-.5,-.5,.5]])
        for k in (1,2):
            self.assertEqual(len(set(anchored_clusters(clipped,np.ones(2),k))),k)
            self.assertEqual(len(set(anchored_clusters(np.zeros((2,3)),np.ones(2),k))),k)

    def test_first_update_uses_unrestricted_best_responses(self):
        solver=RegretBR(fixture(),([0,1],[0,1]))
        solver.step()
        np.testing.assert_array_equal(solver.current()[0],[1.,0.])
        np.testing.assert_array_equal(solver.current()[1],[0.,.5])
        np.testing.assert_array_equal(solver.average()[0],[.5,.5])

    def test_scalar_trajectory_and_pure_response_optimality(self):
        # Dyadic coefficients make the independent order changes exact here.
        matrix=PayoffGame(np.ones((3,3))/16,np.array([[1,0,-1],[0,1,-1],[-1,1,0]])/16,
            np.ones((3,3))/8,np.array([[2,0,-2],[0,2,-2],[-2,2,0]])/16,None,'scalar')
        groups=([0,0,1],[0,1,1])
        solver=RegretBR(matrix,groups)
        regrets=[[[0.,0.] for _ in range(2)] for _ in (0,1)]
        sums=[[[0.,0.] for _ in range(2)] for _ in (0,1)]
        for step in range(100):
            old=solver.current()
            x=np.asarray(old[0])[groups[0]]
            y=np.asarray(old[1])[groups[1]]
            bx,by=scalar_step(matrix,groups,regrets,sums)
            lower=matrix.evaluate(x,by)['value']
            upper=matrix.evaluate(bx,y)['value']
            self.assertAlmostEqual(lower,min(matrix.evaluate(x,p)['value'] for p in product((0,1),repeat=3)))
            self.assertAlmostEqual(upper,max(matrix.evaluate(p,y)['value'] for p in product((0,1),repeat=3)))
            solver.step()
            for seat in (0,1):
                np.testing.assert_allclose(solver.regrets[seat],regrets[seat],rtol=1e-9,atol=1e-10)
                np.testing.assert_allclose(solver.sums[seat],sums[seat],rtol=1e-9,atol=1e-10)

    def test_known_group_floor_and_compressed_equilibrium_gap(self):
        matrix=fixture()
        groups=([0,0],[0,0])
        solver=RegretBR(matrix,groups)
        ordinary=CFR(matrix.aggregate(groups))
        for _ in range(10000):
            solver.step()
            ordinary.step()
        score=lambda p:matrix.evaluate(np.asarray(p[0])[groups[0]],np.asarray(p[1])[groups[1]])['exploitability']
        value=score(solver.average())
        self.assertGreaterEqual(value+1e-12,1/3)
        self.assertLess(value,1/3+.01)
        self.assertGreater(score(ordinary.average())-value,.1)

    def test_zero_payoffs_preserve_uniform_ties(self):
        zero=np.zeros((2,2))
        solver=RegretBR(PayoffGame(np.eye(2)/2,zero,zero,zero,None,'zero'),([0,1],[0,0]))
        for _ in range(10):solver.step()
        np.testing.assert_array_equal(solver.average()[0],[.5,.5])
        np.testing.assert_array_equal(solver.average()[1],[.5])

    def test_invalid_groups_and_empty_average(self):
        with self.assertRaises(ValueError):RegretBR(fixture(),([0,2],[0,1]))
        with self.assertRaises(ValueError):RegretBR(fixture(),([0,1],[0,1])).average()


if __name__=='__main__':unittest.main()
