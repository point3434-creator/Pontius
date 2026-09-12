import itertools
import math
import random
import unittest
from projection import triplet, project

def reference(values):
    """Enumerate every contiguous equality partition; choose feasible least squares."""
    candidates=[]
    for cuts in itertools.product((False,True),repeat=2):
        groups=[];start=0
        for i,cut in enumerate((*cuts,True)):
            if cut:groups.append(values[start:i+1]);start=i+1
        means=[math.fsum(g)/len(g) for g in groups]
        if all(a>=b for a,b in zip(means,means[1:])):
            result=sum(([v]*len(g) for v,g in zip(means,groups)),[])
            candidates.append((math.fsum((a-b)**2 for a,b in zip(values,result)),result))
    return min(candidates)[1]

class ProjectionTests(unittest.TestCase):
    def test_crossing_requires_pooling_not_sorting(self):
        self.assertEqual(triplet([.2,.8,.1]),[.5,.5,.1])
        self.assertEqual(triplet([0.,.5,1.]),[.5,.5,.5])

    def test_ordered_and_ties_unchanged(self):
        for x in ([1.,.4,0.],[.2,.2,.2],[1.,1.,0.],[0.,0.,0.]):
            self.assertEqual(triplet(x),list(x))

    def test_against_exhaustive_partitions(self):
        rng=random.Random(91631)
        points=list(itertools.product((0.,.1,.5,.9,1.),repeat=3))
        points += [[rng.random() for _ in range(3)] for _ in range(1000)]
        for x in points:
            actual=triplet(x);expected=reference(x)
            self.assertLessEqual(max(abs(a-b) for a,b in zip(actual,expected)),2e-15)
            self.assertTrue(1>=actual[0]>=actual[1]>=actual[2]>=0)
            self.assertEqual(triplet(actual),actual)

    def test_witness_boundaries_preserved(self):
        self.assertEqual(project([[.2,.8,.1,1.,.4,0.,0.,.5,1.]]),
                         [[.5,.5,.1,1.,.4,0.,.5,.5,.5]])

    def test_invalid_input_refused(self):
        for x in ([0,1],[0,1,2],[float('nan'),0,0],[float('inf'),0,0]):
            with self.assertRaises(ValueError):triplet(x)
        with self.assertRaises(ValueError):project([[0]*8])

if __name__=='__main__':unittest.main()
