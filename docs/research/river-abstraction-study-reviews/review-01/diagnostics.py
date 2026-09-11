import json, sys, itertools, hashlib, math, random
from pathlib import Path
assert sys.version_info[:3] == (3,14,6), sys.version
sys.path.insert(0, 'D:/Pontius-worktrees/eval-runner-consolidation/src')
sys.path.insert(0, 'D:/Projects/pluribus-lite')
import numpy as np
from pontius.river_abstraction_study import PayoffGame, CFR, DEVELOPMENT_BOARDS, uniform_equities, development_case, representations, anchored_clusters, range_features
from pluribus_lite.abstraction import river_equity
from pluribus_lite.evaluator import BACKEND
from pontius.river import evaluate_seven
out = {'python':sys.version,'numpy':np.__version__,'independent_baseline_backend':BACKEND}
# A different rank evaluator and inclusion-exclusion implementation for every own hand.
eq = uniform_equities(DEVELOPMENT_BOARDS[0])
other = {h:river_equity(h, DEVELOPMENT_BOARDS[0]) for h in eq}
assert all(eq[h].hex()==other[h].hex() for h in eq)
assert all(min(int(eq[h]*200),199)==min(int(other[h]*200),199) for h in eq)
out['baseline_bit_identical_equities_and_bins'] = len(eq)
# Explicit scalar outcome sum and exhaustive hand-contingent pure best responses.
rng = random.Random(91721)
max_error=0.0
for trial in range(40):
    n,m = 3,4
    weights = [[(rng.random()*8 if rng.random()>.2 else 0.) for j in range(m)] for i in range(n)]
    for i in range(n): weights[i][i] += 1
    weights[0][3]+=1
    total = sum(map(sum, weights))
    q=np.array(weights,dtype=float)/total
    z=np.array([[rng.choice((-1,0,1)) for j in range(m)] for i in range(n)])
    game=PayoffGame(q,q*z*5,q*5,q*z*10,None,'independent-synthetic')
    def scalar(x,y):
        return math.fsum(float(q[i,j])*((1-x[i])*float(z[i,j])*5+x[i]*((1-y[j])*5+y[j]*float(z[i,j])*10)) for i in range(n) for j in range(m))
    x=[rng.random() for i in range(n)]; y=[rng.random() for j in range(m)]
    expected={'value':scalar(x,y),'upper':max(scalar(p,y) for p in itertools.product((0,1),repeat=n)),'lower':min(scalar(x,p) for p in itertools.product((0,1),repeat=m))}
    actual=game.evaluate(x,y)
    for k in expected:
        error=abs(actual[k]-expected[k]); max_error=max(max_error,error)
        assert error<1e-12,(trial,k,actual,expected)
    # Independent scalar regret bookkeeping, including all negative regrets and averaging.
    r=[[[0.,0.] for _ in range(count)] for count in (n,m)]
    sums=[[[0.,0.] for _ in range(count)] for count in (n,m)]
    def match(row):
        p=[max(v,0.) for v in row]; t=sum(p)
        return [v/t for v in p] if t else [.5,.5]
    compact=CFR(game)
    for step in range(20):
        for p,count in ((0,n),(1,m)):
            policies=[[match(row) for row in rp] for rp in r]
            for hand in range(count):
                s=policies[p][hand]
                vals=[]
                for action in (0,1):
                    if p==0:
                        val=math.fsum(float(q[hand,j])*(float(z[hand,j])*5 if action==0 else policies[1][j][0]*5+policies[1][j][1]*float(z[hand,j])*10) for j in range(m))
                    else:
                        val=math.fsum(float(q[i,hand])*policies[0][i][1]*(-5 if action==0 else -float(z[i,hand])*10) for i in range(n))
                    vals.append(val)
                ev=sum(a*b for a,b in zip(vals,s))
                for a in (0,1): r[p][hand][a]+=vals[a]-ev; sums[p][hand][a]+=s[a]
        compact.step()
        for p in (0,1):
            np.testing.assert_allclose(compact.regrets[p],r[p],atol=1e-11,rtol=1e-11,err_msg=f'trial={trial} step={step} p={p} q={q.tolist()} z={z.tolist()}')
            np.testing.assert_allclose(compact.sums[p],sums[p],atol=1e-11,rtol=1e-11)
    groups=(np.array([0,1,0]),np.array([0,1,1,0]))
    reduced=game.aggregate(groups)
    a=np.array([.23,.84]); b=np.array([.16,.72])
    full=game.evaluate(a[groups[0]],b[groups[1]]); restricted=reduced.evaluate(a,b)
    assert abs(full['value']-restricted['value'])<1e-12
    assert full['upper']+1e-12>=restricted['upper'] and full['lower']<=restricted['lower']+1e-12
out['pure_response_trials']=40; out['cfr_scalar_trajectory_steps']=800; out['max_pure_response_absolute_error']=max_error
# Input generation and population fairness, using only 16-hand preparation; no CFR/campaign.
game, eq2, ranges=development_case(DEVELOPMENT_BOARDS[0],16,'polarized')
for p in (0,1):
    hands=list(itertools.combinations(sorted(set(range(52))-set(game.board)),2))
    def key(h):
        payload='river-study-v1|'+','.join(str(c) for c in sorted(game.board))+'|'+str(p)+'|'+','.join(str(c) for c in h)
        return hashlib.sha256(payload.encode('ascii')).digest(),h
    selected=sorted(hands,key=key)[:16]
    assert set(selected)==set(ranges[p])
    assert ranges[p]=={h:(4 if other[h]<=.2 or other[h]>=.8 else 1) for h in selected}
matrix=PayoffGame.from_river(game)
normalizer=sum(w0*w1 for h0,w0 in ranges[0].items() for h1,w1 in ranges[1].items() if not set(h0)&set(h1))
for i,h0 in enumerate(matrix.hands[0]):
    for j,h1 in enumerate(matrix.hands[1]):
        expected=0 if set(h0)&set(h1) else ranges[0][h0]*ranges[1][h1]/normalizer
        assert abs(matrix.joint[i,j]-expected)<1e-15
methods=representations(matrix,eq2)
for p in (0,1):
    capacities=[len(set(methods[name][p])) for name in ('uniform_equity_200','range_equity','range_response')]
    assert len(set(capacities))==1
    features,equity=range_features(matrix,eq2,p)
    assert np.all(features>=0) and np.all(features<=1+1e-15)
    np.testing.assert_allclose(features[:,::3].sum(axis=1),1,atol=1e-14)
    np.testing.assert_allclose(features[:,1::3].sum(axis=1)+.5*features[:,2::3].sum(axis=1),equity,atol=1e-14)
    for i,h in enumerate(matrix.hands[p]):
        rank=evaluate_seven((*game.board,*h))
        expected=np.zeros(9)
        for opp,mass in game.conditional_opponent_distribution(p,h).items():
            # Comparisons express the specified half-open boundaries directly.
            b=0 if other[opp]<1/3 else 1 if other[opp]<2/3 else 2
            r2=evaluate_seven((*game.board,*opp))
            expected[3*b]+=mass; expected[3*b+1]+=mass*(rank>r2); expected[3*b+2]+=mass*(rank==r2)
        np.testing.assert_allclose(features[i],expected,atol=1e-14,rtol=0)
for k in (1,4,8):
    lab=anchored_clusters(np.zeros((8,9)),np.arange(1,9),k)
    assert len(set(lab))==k
out['prepared_polarized_hands_per_player']=16
out['accepted_polarized_deals']=len(game.deals)
out['occupied_polarized_groups']={name:[len(set(g)) for g in groups] for name,groups in methods.items()}
out['passed']=True
print(json.dumps(out,indent=2))
Path('D:/Pontius/tmp/river-study-review-01/diagnostics.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')



