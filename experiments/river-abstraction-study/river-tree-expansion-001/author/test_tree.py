import unittest
import itertools
from fractions import Fraction as Q
import numpy as np
import tree as t


class TreeTests(unittest.TestCase):
    def test_public_tree_nesting_and_all_in_alias(self):
        for j in range(4):
            record = t.d.read(t.d.b.PRIOR/f'input-{j:03d}.json')
            base, check, raised = [t.public_tree(record,v) for v in t.VARIANTS]
            paths = lambda ns: {tuple(n['path']) for n in ns if n['player'] == -1}
            self.assertTrue(paths(base) <= paths(check) <= paths(raised))
            self.assertGreater(len(check),len(base))
            self.assertEqual(check == raised, j != 1)

    def test_all_terminal_payoffs_against_engine(self):
        for j in range(4):
            record = t.d.read(t.d.b.PRIOR/f'input-{j:03d}.json')
            tree = t.public_tree(record,'raise')
            audit = t.engine_audit(record,tree)
            self.assertEqual(audit['checks'],3*sum(n['player'] == -1 for n in tree))

    def test_quantization_simplexes_and_unreachable_rows(self):
        raw=np.array([[0.,0.,0.],[.2,.3,.5],[-1e-14,.4,.6]])
        q=t.quantize(raw)
        self.assertTrue(all(sum(r)==t.GRID and min(r)>=0 for r in q))
        self.assertLessEqual(max(q[0])-min(q[0]),1)
        self.assertLess(np.max(np.abs(np.array(q,dtype=float)[1:]/t.GRID-np.maximum(raw[1:],0))),1e-13)

    def test_sequence_lp_and_literal_response_enumeration(self):
        record=t.d.read(t.d.b.PRIOR/'input-000.json')
        nodes=t.public_tree(record,'checkback')
        seq,flow=t.sequence_layout(nodes)
        # Two private hands each; compare integer DP with all deterministic policies.
        values={tuple(n['payoff']):np.array([[.125,-.25],[.375,.0625]])*(i+1)
                for i,n in enumerate(nodes) if n['player']==-1}
        solve=t.solve(nodes,seq,flow,values)
        self.assertTrue(solve['solver_success'])
        probs=t.behavior(nodes,solve['realizations'],2)
        cert=t.certificate(nodes,seq,values,probs)
        self.assertLessEqual(Q(cert['gap']),Q('1e-8'))
        for role in (0,1):
            owned=[(i,n) for i,n in enumerate(nodes) if n['player']==role]
            choices=[range(len(n['children'])) for i,n in owned for _ in range(2)]
            outcomes=[]
            for combination in itertools.product(*choices):
                candidate=dict(probs)
                for k,(i,n) in enumerate(owned):
                    candidate[str(i)]=[[t.GRID if a==combination[2*k+h] else 0
                        for a in range(len(n['children']))] for h in range(2)]
                outcomes.append(t.literal_value(nodes,seq,values,candidate))
            expected=max(outcomes) if role==0 else min(outcomes)
            self.assertEqual(expected,Q(cert['upper' if role==0 else 'lower']))


if __name__=='__main__':
    unittest.main()
