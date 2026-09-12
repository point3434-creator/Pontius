import unittest
from loader import np
import ordinal

class Tests(unittest.TestCase):
    def test_threshold_order_and_boundaries(self):
        a=np.array([[-.25,0.,.25]])
        expected=[[.5,0.,0.,1.,.5,0.,1.,1.,.5]]
        self.assertEqual(ordinal.targets(a).tolist(),expected)

    def test_scalar_labels_and_zero_head_identity(self):
        values=np.array([[-1.,-.1,.1],[.5,.25,0.],[.75,-.25,-.5]])
        expected=[[1. if a>t else 0. if a<t else .5 for a in row for t in (-.25,0.,.25)] for row in values]
        actual=ordinal.targets(values)
        self.assertEqual(actual.tolist(),expected)
        self.assertTrue(np.array_equal(actual[:,[1,4,7]],ordinal.pref.targets(values)))
        self.assertTrue(np.all(actual.reshape(-1,3,3)[:,:,:-1]>=actual.reshape(-1,3,3)[:,:,1:]))

    def test_crossings_are_diagnostic_not_projected(self):
        f=np.array([[.8,.6,.2]*3,[.2,.4,.1]*3])
        original=f.copy()
        self.assertEqual(ordinal.crossing(f,[3,1]),dict(per_witness=[.25]*3,mean=.25))
        self.assertTrue(np.array_equal(original,f))

    def test_invalid_labels_refused(self):
        for v in [np.zeros((2,2)),[[0,1,float('nan')]]]:
            with self.assertRaises(AssertionError):ordinal.targets(v)

    def test_new_board_selection_and_capacity(self):
        import experiment as e
        from loader import read,PRIOR
        old=read(PRIOR/'plan.json');excluded=old['excluded_boards']+old['boards']
        tool=e.base.helpers();boards,receipt=e.select(excluded,tool.pilot)
        self.assertEqual(len(boards),8)
        self.assertEqual((boards,receipt),e.select(excluded,tool.pilot))
        self.assertFalse({tool.pilot.canonical_board(b) for b in boards}&
                         {tool.pilot.canonical_board(b) for b in excluded})
        self.assertEqual(len(e.grid(boards,tool)),32)
        core=dict(bet=10,raw_features=[np.zeros((3,11)).tolist()]*2,
            bank_groups={m:[[0,1,1],[0,1,1]] for m in e.BANK})
        models={m:[[dict(constant=.25,coefficients=None)]*n]*2 for m,n in [('ordinal',9),('sign_conditioned',3)]}
        def ws(v):return [dict(weights=[.2,.3,.5],target=[[v]*3]*3,
            clipped=[[v/2]*3]*3,advantages=[[v]*3]*3)]*2
        a=e.proposal(core,ws(0),models);b=e.proposal(core,ws(1),models)
        for m in models:
            self.assertEqual(a['features'][m],b['features'][m])
            self.assertEqual(a['groups'][m],b['groups'][m])
            self.assertEqual(len(set(a['groups'][m][0])),2)

    def test_summary_audit_reconstructs_all_panels(self):
        import experiment as e
        from audit import audit
        from fractions import Fraction as Q
        from pathlib import Path
        from tempfile import TemporaryDirectory
        cases=[dict(id=f'b{b}-p{p}-{r}',board_index=b,pool=p,regime=r,texture=f't{b//2}')
               for b in range(8) for p in range(2) for r in ('uniform','polarized')]
        rows=[]
        with TemporaryDirectory() as directory:
            out=Path(directory);e.write(out/'plan.json',dict(evaluation_cases=cases))
            for c in cases:
                for bet in (5,10):
                    f=np.array([[.9,.5,.2]*3,[.2,.5,.3]*3])
                    ws=[dict(weights=[.75,.25])]*2
                    prop=dict(features=dict(ordinal=[f.tolist()]*2),
                        ordinal_crossings=[ordinal.crossing(f,ws[0]['weights'])]*2)
                    row=dict(case=c,bet=bet,witness=ws,proposal=prop,
                        solutions={m:dict(minimum_exploitability=e.opt.interval(Q(j+1,100),Q(j+1,100)))
                                   for j,m in enumerate(e.METHODS)},
                        records={m:[dict(iteration=n,full=dict(exploitability=(j+1)/100+.001))
                                    for n in e.CHECKPOINTS] for j,m in enumerate(e.SOLVERS)})
                    rows.append(row);e.write(out/e.filename('eval',c,bet),row)
            e.write(out/'summary.json',e.summarize(rows))
            self.assertTrue(audit(out)['passed'])

if __name__=='__main__':unittest.main()
