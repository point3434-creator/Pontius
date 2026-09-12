import unittest
from bridge import np
import model

class Tests(unittest.TestCase):
    def test_conditioned_input_changes_only_bet_terms(self):
        raw=np.full((3,11),.25)
        a=model.design(raw,5,True)
        b=model.design(raw,10,True)
        self.assertEqual(a.shape,(3,91))
        self.assertTrue(np.array_equal(a[:,1:12],raw))
        self.assertTrue(np.all(a[:,12]==.5))
        self.assertTrue(np.all(b[:,12]==1.))
        self.assertTrue(np.all(a[:,-1]==.25))
        self.assertTrue(np.all(b[:,-1]==1.))
        self.assertTrue(np.array_equal(model.design(raw,5,False),model.design(raw,10,False)))

    def test_conditioning_can_learn_opposite_labels(self):
        raw=np.zeros((4,11))
        y=np.array([0.,0.,1.,1.])
        x=np.vstack((model.design(raw[:2],5,True),model.design(raw[2:],10,True)))
        fitted=model.fit(x,y,np.ones(4))
        predicted=model.predict([fitted],x)[:,0]
        self.assertLess(max(predicted[:2]),.2)
        self.assertGreater(min(predicted[2:]),.8)
        blind=model.design(raw,5,False)
        self.assertTrue(np.allclose(model.predict([model.fit(blind,y,np.ones(4))],blind),.5))

    def test_ties_constants_and_zero_weight(self):
        x=model.design(np.zeros((2,11)),5,True)
        for v in (0.,.5,1.):
            self.assertEqual(model.fit(x,[v,1-v],[1,0])['constant'],v)

    def test_gradient_and_weight_scale(self):
        x=model.design(np.full((2,11),.2),10,True)
        y=np.array([0.,1.]);w=np.array([.25,.75]);beta=np.linspace(-.01,.01,91)
        _,g=model.pref.objective(beta,x,y,w)
        for j in (0,12,23,90):
            d=np.zeros(91);d[j]=1e-5
            numerical=(model.pref.objective(beta+d,x,y,w)[0]-
                       model.pref.objective(beta-d,x,y,w)[0])/(2e-5)
            self.assertAlmostEqual(g[j],numerical,places=8)
        self.assertEqual(model.fit(x,y,w),model.fit(x,y,w*2))

    def test_invalid_inputs_refused(self):
        x=model.design(np.zeros((2,11)),5,True)
        for y,w in [([0,1],[0,0]),([0,2],[1,1]),([0,1],[-1,2]),([0,float('nan')],[1,1])]:
            with self.assertRaises(AssertionError):model.fit(x,y,w)
        with self.assertRaises(AssertionError):model.design(np.zeros((2,11)),2.5,True)
        with self.assertRaises(AssertionError):model.design(np.zeros((2,10)),5,True)

    def test_fresh_selection_excludes_suit_equivalents(self):
        import experiment as e
        tool=e.base.helpers()
        excluded=[[0,5,10,15,20]]
        boards,receipt=e.select(excluded,tool.pilot)
        keys=[tool.pilot.canonical_board(b) for b in boards]
        self.assertEqual(len(set(keys)),8)
        self.assertNotIn(tool.pilot.canonical_board(excluded[0]),keys)
        self.assertEqual((boards,receipt),e.select(excluded,tool.pilot))
        self.assertEqual(len(e.grid(boards,tool)),32)
        self.assertEqual(sorted([tool.pilot.texture(b) for b in boards]),
                         sorted(list(tool.pilot.TEXTURES)*2))

    def test_public_payoffs_and_blind_features(self):
        import experiment as e
        tool=e.base.helpers()
        case=dict(id='preflight',board=[0,5,10,15,20],board_index=0,pool=0,
                  texture=tool.pilot.texture([0,5,10,15,20]),regime='uniform')
        equities=tool.old.equities_for(case,{})
        reference,_,inputs=tool.pilot.build_inputs(case,8,equities)
        raw=[]
        for bet in (5,10):
            _,matrix=e.transfer.build(inputs,bet)
            e.transfer.validate_game(matrix,reference,inputs,bet)
            raw.append(tool.student.raw_features(matrix,equities,0))
        self.assertTrue(np.array_equal(raw[0],raw[1]))

    def test_learned_prediction_ignores_holdout_witness_targets(self):
        import experiment as e
        core=dict(bet=10,raw_features=[np.zeros((3,11)).tolist()]*2,
            bank_groups={m:[[0,1,1],[0,1,1]] for m in e.BANK})
        models={m:[[dict(constant=.25,coefficients=None)]*3]*2 for m in ('conditioned','blind')}
        def ws(v):return [dict(weights=[.2,.3,.5],target=[[v]*3]*3,clipped=[[v/2]*3]*3)]*2
        a=e.proposal(core,ws(0),models);b=e.proposal(core,ws(1),models)
        for m in models:
            self.assertEqual(a['features'][m],b['features'][m])
            self.assertEqual(a['groups'][m],b['groups'][m])
            self.assertEqual(len(set(a['groups'][m][0])),2)

if __name__=='__main__':unittest.main()
