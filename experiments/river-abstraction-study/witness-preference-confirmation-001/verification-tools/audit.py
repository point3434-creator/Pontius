"""Independent board-selection, scalar predictor and rational certificate audit."""
from collections import Counter
from fractions import Fraction as Q
from hashlib import sha256
from itertools import permutations
import json
from math import exp,fsum,isclose,isfinite
from pathlib import Path

def audit(out):
    read=lambda p:json.loads(p.read_bytes())
    digest=lambda p:sha256(p.read_bytes()).hexdigest()
    bounds=lambda v:(Q(v['lower_exact']),Q(v['upper_exact']))
    def close(a,b):assert isclose(a,b,rel_tol=1e-9,abs_tol=1e-11),(a,b)
    def canonical(board):
        return min(tuple(sorted(4*(c//4)+s[c%4] for c in board)) for s in permutations(range(4)))
    textures=('unpaired-no-flush','unpaired-flush-possible','one-pair','multiple-pairs-or-trips')
    def texture(board):
        ranks=sorted(Counter(c//4 for c in board).values())
        if ranks==[1,1,1,2]:return textures[2]
        if ranks!=[1]*5:return textures[3]
        return textures[1] if max(Counter(c%4 for c in board).values())>=3 else textures[0]
    p=read(out/'plan.json');candidate=read(out/'candidate.json');summary=read(out/'summary.json')
    assert read(out/'worker-receipt.json')['exit']==0 and not (out/'failed.json').exists()
    assert read(out/'worker-complete.json')==dict(complete=True,cases=96,lp_calls=768,model_fits=0)
    for path,h in p['pins'].items():assert digest(Path(path))==h,path
    assert candidate==read(Path(p['candidate_path']))
    assert digest(Path(p['candidate_path']))==p['candidate_sha256']
    assert candidate['models']==read(Path(p['producer'])/'training.json')['models']['ordinary_preference']
    excluded={canonical(b) for b in p['excluded_boards']};assert len(excluded)==20
    selected={t:[] for t in textures};seen=set(excluded);receipts=[]
    for i in range(10000):
        ordered=sorted(range(52),key=lambda c:(sha256(
            f'witness-preference-confirmation-001|board|{i}|{c}'.encode()).digest(),c))
        board=sorted(ordered[:5]);key=canonical(board);t=texture(board)
        if key not in seen and len(selected[t])<4:
            seen.add(key);selected[t].append(board);receipts.append(dict(attempt=i,board=board,texture=t))
        if sum(map(len,selected.values()))==16:break
    assert [b for t in textures for b in selected[t]]==p['boards'] and receipts==p['selection_receipt']
    assert len(seen-excluded)==16 and not (set(map(canonical,p['boards']))&excluded)
    rows=[read(out/(c['id']+'.json')) for c in p['cases']]
    assert len(rows)==96 and [r['case'] for r in rows]==p['cases']
    probabilities=floors_checked=comparisons_checked=seat_checks=joint_cells=0;maxgap=Q(0)
    methods=('ordinary_preference','range_response','range_equity','exact')
    def checked(v,lo,hi):
        assert bounds(v)==(lo,hi)
        assert v['classification']==('lower' if hi<0 else 'higher' if lo>0 else 'overlapping')
    for row in rows:
        c=row['case'];assert c['board']==p['boards'][c['board_index']] and c['texture']==texture(c['board'])
        inputs=row['inputs'];assert inputs['board']==c['board'] and inputs['pot']==10 and inputs['bet']==5
        assert inputs['stacks']==[20,20]
        capacity=[len(set(g)) for g in inputs['groups']['uniform_equity_200']]
        assert all([len(set(g)) for g in row['groups'][m]]==capacity for m in methods[:3])
        assert row['groups']['exact']==[list(range(96)),list(range(96))]
        hands=inputs['hands'];weights=[]
        for seat in (0,1):
            assert len(hands[seat])==len(set(map(tuple,hands[seat])))==96
            for hand in hands[seat]:assert len(hand)==2 and hand[0]<hand[1] and not set(hand)&set(c['board'])
            raw={tuple(h):w for h,w in inputs['ranges'][seat]}
            weights.append([raw[tuple(h)] for h in hands[seat]])
            for i,x in enumerate(row['raw_features'][seat]):
                assert len(x)==11 and all(isfinite(v) and -1e-12<=v<=1+1e-12 for v in x)
                assert weights[seat][i]==(4 if c['regime']=='polarized' and (x[-1]<=.2 or x[-1]>=.8) else 1)
                phi=[1.,*x,*[x[j]*x[k] for j in range(11) for k in range(j,11)]]
                for j,model in enumerate(candidate['models'][seat]):
                    if model['constant'] is not None:v=model['constant']
                    else:
                        z=fsum(a*b for a,b in zip(phi,model['coefficients']))
                        v=1/(1+exp(-z)) if z>=0 else exp(z)/(1+exp(z))
                    close(v,row['candidate_features'][seat][i][j]);probabilities+=1
        total=sum(weights[0][i]*weights[1][j] for i in range(96) for j in range(96)
                  if not set(hands[0][i])&set(hands[1][j]))
        accepted=0
        for i in range(96):
            for j in range(96):
                valid=not set(hands[0][i])&set(hands[1][j]);accepted+=valid
                expected=weights[0][i]*weights[1][j]/total if valid else 0.
                close(expected,inputs['joint'][i][j]);joint_cells+=1
        assert accepted==inputs['accepted_joint_deals']
        for method in methods:
            sol=row['solutions'][method];values=[]
            for seat in (0,1):
                item=sol[f'seat{seat}'];lo,hi=bounds(item['value'])
                assert hi-lo==Q(item['gap_exact']) and 0<=hi-lo<=Q(1,10**8)
                maxgap=max(maxgap,hi-lo);values.append((lo,hi))
            (l0,u0),(l1,u1)=values
            assert bounds(sol['minimum_exploitability'])==bounds(row['floors'][method])==(
                max(Q(0),(l1-u0)/2),(u1-l0)/2)
            floors_checked+=1
        exact=row['solutions']['exact']
        x0,y0=bounds(exact['seat0']['value']);x1,y1=bounds(exact['seat1']['value'])
        assert max(x0,x1)<=min(y0,y1) and bounds(row['floors']['exact'])[0]==0
        for m in methods[1:]:
            lo,hi=bounds(row['floors']['ordinary_preference']);a,b=bounds(row['floors'][m])
            checked(row['comparisons'][m],lo-b,hi-a);comparisons_checked+=1
            cand=row['solutions']['ordinary_preference'];ref=row['solutions'][m]
            l0,u0=bounds(cand['seat0']['value']);l1,u1=bounds(cand['seat1']['value'])
            r0,s0=bounds(ref['seat0']['value']);r1,s1=bounds(ref['seat1']['value'])
            checked(row['seat_effects'][m]['bettor'],(r0-u0)/2,(s0-l0)/2)
            checked(row['seat_effects'][m]['caller'],(l1-s1)/2,(u1-r1)/2);seat_checks+=2
    aggregates=0
    def checkstats(selected,actual):
        nonlocal aggregates
        def check(v,vs):
            assert bounds(v)==tuple(sum(bounds(x)[i] for x in vs)/len(vs) for i in (0,1))
            if 'counts' in v:assert v['counts']==dict(Counter(x['classification'] for x in vs))
        for m,v in actual['mean_floors'].items():check(v,[r['floors'][m] for r in selected]);aggregates+=1
        for m,v in actual['comparisons'].items():check(v,[r['comparisons'][m] for r in selected]);aggregates+=1
        for m,seats in actual['seat_effects'].items():
            for seat,v in seats.items():check(v,[r['seat_effects'][m][seat] for r in selected]);aggregates+=1
    checkstats(rows,summary['overall'])
    for b,s in summary['boards'].items():
        selected=[r for r in rows if r['case']['board_index']==int(b)];assert len(selected)==6
        checkstats(selected,s)
        for pool,v in s['pools'].items():checkstats([r for r in selected if r['case']['pool']==int(pool)],v)
    for name,key in [('regimes','regime'),('textures','texture')]:
        for v,s in summary[name].items():checkstats([r for r in rows if r['case'][key]==v],s)
    for b,s in summary['leave_one_board_out'].items():checkstats([r for r in rows if r['case']['board_index']!=int(b)],s)
    assert summary['directional_replication_pass']==(bounds(summary['overall']['comparisons']['range_response'])[1]<0)
    assert summary['sensitivity_pass']==all(bounds(v['comparisons']['range_response'])[1]<0
        for name in ('textures','leave_one_board_out') for v in summary[name].values())
    for k,v in summary['stage_seconds'].items():close(v,fsum(r['timings'][k] for r in rows))
    assert probabilities==73728 and floors_checked==384 and comparisons_checked==288 and seat_checks==576
    assert joint_cells==884736 and aggregates==1131
    return dict(passed=True,fresh_boards=16,excluded_boards=20,probabilities_checked=probabilities,
        joint_cells_checked=joint_cells,floor_identities=floors_checked,signed_comparisons=comparisons_checked,
        seat_effects=seat_checks,aggregate_records=aggregates,maximum_certificate_gap=float(maxgap),
        model_fits=0,new_audit_lp_calls=0,auditor_sha256=digest(Path(__file__)))
