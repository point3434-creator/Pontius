"""Independent threshold preferences, used as grouping features rather than a CDF."""
from loader import np,pref,model,read,PRIOR
THRESHOLDS=(-.25,0.,.25)

def targets(advantages):
    a=np.asarray(advantages,float)
    assert a.ndim==2 and a.shape[1]==3 and np.isfinite(a).all()
    return pref.targets(a[:,:,None]-np.array(THRESHOLDS)).reshape(len(a),9)

def fit_models(rows):
    assert len(rows)==64
    reference=read(PRIOR/'candidate.json')['models']['conditioned']
    fitted=[]
    for seat in (0,1):
        x=np.vstack([model.design(r['raw_features'][seat],r['bet'],True) for r in rows])
        y=np.vstack([targets(r['witness'][seat]['advantages']) for r in rows])
        w=np.concatenate([np.asarray(r['witness'][seat]['weights'])/
            sum(r['witness'][seat]['weights'])/len(rows) for r in rows])
        heads=[model.fit(x,y[:,j],w) for j in range(9)]
        assert [heads[j] for j in (1,4,7)]==reference[seat]
        fitted.append(heads)
    return dict(ordinal=fitted,sign_conditioned=reference)

def crossing(features,weights):
    f=np.asarray(features,float).reshape(-1,3,3)
    w=np.asarray(weights,float);w=w/w.sum()
    per_witness=w @ np.any(f[:,:,1:]>f[:,:,:-1]+1e-12,axis=2)
    return dict(per_witness=per_witness.tolist(),mean=float(per_witness.mean()))
