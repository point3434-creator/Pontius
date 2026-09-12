"""Fixed ridge-logistic preferences with a masked bet-input ablation."""
from bridge import np,pref

def design(raw,bet,conditioned):
    x=np.asarray(raw,float)
    assert x.ndim==2 and x.shape[1]==11 and np.isfinite(x).all()
    assert bet in (5,10) and type(conditioned) is bool
    z=np.column_stack((x,np.full(len(x),bet/10 if conditioned else 0.)))
    return np.column_stack((np.ones(len(x)),z,
        *[z[:,i]*z[:,j] for i in range(12) for j in range(i,12)]))

def fit(x,y,w):
    x,y,w=np.asarray(x,float),np.asarray(y,float),np.asarray(w,float)
    assert x.ndim==2 and x.shape[1]==91 and y.shape==w.shape==(len(x),)
    assert np.isfinite(x).all() and np.isfinite(y).all() and np.isfinite(w).all()
    assert (w>=0).all() and w.sum()>0 and ((y>=0)&(y<=1)).all() and np.all(x[:,0]==1)
    w=w/w.sum()
    active=y[w>0]
    if np.all(active==active[0]) and active[0] in (0.,.5,1.):
        return dict(constant=float(active[0]),coefficients=None,iterations=0,gradient_max=0.)
    beta=np.zeros(91)
    for iteration in range(81):
        loss,g=pref.objective(beta,x,y,w)
        maximum=float(np.max(np.abs(g)))
        if maximum<=1e-8:
            return dict(constant=None,coefficients=beta.tolist(),iterations=iteration,
                        gradient_max=maximum,objective=loss)
        assert iteration<80,'Newton iteration limit'
        probabilities=pref.expit(x@beta)
        h=x.T@((w*probabilities*(1-probabilities))[:,None]*x)+np.diag([0.]+[.001]*90)
        direction=np.linalg.solve(h,g)
        descent=float(g@direction)
        assert np.isfinite(direction).all() and descent>0
        for backtrack in range(40):
            trial=beta-(2.**-backtrack)*direction
            trial_loss,_=pref.objective(trial,x,y,w)
            if trial_loss<=loss-.0001*(2.**-backtrack)*descent:
                beta=trial
                break
        else:raise AssertionError('line search limit')
    raise AssertionError('unreachable')

predict=pref.predict
