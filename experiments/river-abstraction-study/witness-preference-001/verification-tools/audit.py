"""Scalar probability/label audit, independent score equations and rational result audit."""
from collections import Counter
from fractions import Fraction as Q
from hashlib import sha256
import json
from math import exp,fsum,isclose
from pathlib import Path
import numpy as np

def audit(out):
    read=lambda p:json.loads(p.read_bytes())
    digest=lambda p:sha256(p.read_bytes()).hexdigest()
    bounds=lambda x:(Q(x['lower_exact']),Q(x['upper_exact']))
    def close(a,b):assert isclose(a,b,rel_tol=1e-9,abs_tol=1e-11),(a,b)
    def phi(x):return [1.,*x,*[x[i]*x[j] for i in range(11) for j in range(i,11)]]
    def sigmoid(z):return 1/(1+exp(-z)) if z>=0 else exp(z)/(1+exp(z))
    def prediction(model,x):
        return [m['constant'] if m['constant'] is not None else
                sigmoid(fsum(a*b for a,b in zip(x,m['coefficients']))) for m in model]
    plan=read(out/'plan.json');fit=read(out/'training.json');summary=read(out/'summary.json')
    assert read(out/'worker-receipt.json')['exit']==0 and not (out/'failed.json').exists()
    assert read(out/'worker-complete.json')==dict(complete=True,cases=48,lp_calls=288,model_fits=4)
    assert fit['model_fits']==summary['parent_model_refits']==4 and fit['output_tasks']==16
    for p,h in plan['pins'].items():assert digest(Path(p))==h,p
    assert [r['case'] for r in fit['training_rows']]==plan['training_cases']
    rows=[read(out/(c['id']+'.json')) for c in plan['cases']]
    assert [r['case'] for r in rows]==plan['cases']
    methods=('ordinary_preference','weighted_preference','exact_preference')
    diagnostics=0;errors={};gradients=[];constants=0
    for split,selected in [('training',fit['training_rows']),('evaluation',rows)]:
        sums={m:np.zeros((2,4)) for m in methods[:2]}
        for row in selected:
            source=read(Path(plan[split])/(row['case']['id']+'.json'))
            teacher=source if split=='training' else source['teacher']
            prior=read(Path(plan['diagnostic'])/(split+'-'+row['case']['id']+'.json'))
            seats=row['seats'] if split=='training' else row['diagnostics']
            for seat,d in enumerate(seats):
                assert d['raw']==prior['seats'][seat]['raw']
                assert d['advantage']==teacher['candidate']['proposal']['features'][seat]
                assert len(d['weights'])==96 and all(w>0 for w in d['weights'])
                norm=fsum(d['weights']);costs={m:[[] for _ in range(4)] for m in methods[:2]}
                for i,(raw,a,y) in enumerate(zip(d['raw'],d['advantage'],d['target'])):
                    assert y==[1. if v>0 else 0. if v<0 else .5 for v in a]
                    x=phi(raw)
                    for method in methods[:2]:
                        pred=prediction(fit['models'][method][seat],x)
                        for c,p in enumerate(pred):
                            assert 0<=p<=1
                            if split=='evaluation':close(p,d['features'][method][i][c])
                            wrong=1-p if a[c]>0 else p if a[c]<0 else 0
                            costs[method][c].append(d['weights'][i]/norm*abs(a[c])*wrong)
                            diagnostics+=1
                    if split=='evaluation':assert d['features']['exact_preference'][i]==y
                for method in methods[:2]:
                    values=[fsum(v) for v in costs[method]]
                    sums[method][seat]+=np.array(values)/48
                    if split=='evaluation':
                        for a,b in zip(values,d['metrics'][method]['expected_wrong_action_cost']):close(a,b)
                if split=='evaluation':assert d['metrics']['exact_preference']['expected_wrong_action_cost']==[0.]*4
        errors[split]={m:s.tolist() for m,s in sums.items()}
    for seat in (0,1):
        data=[r['seats'][seat] for r in fit['training_rows']]
        x=np.array([phi(raw) for d in data for raw in d['raw']])
        y=np.array([v for d in data for v in d['target']])
        a=np.array([v for d in data for v in d['advantage']])
        base=np.array([w/fsum(d['weights'])/48 for d in data for w in d['weights']])
        for method in methods[:2]:
            for c,m in enumerate(fit['models'][method][seat]):
                w=base if method=='ordinary_preference' else base*np.abs(a[:,c])
                total=fsum(w)
                if method=='weighted_preference':close(total,fit['cost_normalizers'][seat][c])
                if m['constant'] is not None:
                    assert m['coefficients'] is None and m['iterations']==0
                    assert (total==0 and m['constant']==.5) or all(t==m['constant'] for t in y[w>0,c])
                    constants+=1;continue
                assert total>0 and len(m['coefficients'])==78 and 0<=m['iterations']<=80
                w=w/total;b=np.array(m['coefficients'])
                probabilities=np.array([sigmoid(fsum(v*coef for v,coef in zip(row,b))) for row in x])
                penalty=.001*b.copy();penalty[0]=0
                gradient=x.T@(w*(probabilities-y[:,c]))+penalty
                maximum=float(np.max(np.abs(gradient)));assert maximum<=2e-8,maximum
                close(maximum,m['gradient_max']);gradients.append(maximum)
    maxgap=Q(0);floor_checks=comparison_checks=seat_checks=0
    def classify(v):return 'lower' if v[1]<0 else 'higher' if v[0]>0 else 'overlapping'
    def checked(v,endpoints):
        assert bounds(v)==endpoints
        assert v['classification']==classify(endpoints)
    for row in rows:
        previous=read(Path(plan['crossover'])/(row['case']['id']+'.json'))
        teacher=read(Path(plan['evaluation'])/(row['case']['id']+'.json'))['teacher']
        controls=next(r['solution'] for r in teacher['bank']['methods'] if r['method']=='range_response')
        for name,f in previous['floors'].items():assert row['floors'][name]==f
        capacity=[len(set(g)) for g in teacher['inputs']['groups']['uniform_equity_200']]
        for method in methods:
            assert [len(set(g)) for g in row['groups'][method]]==capacity
            sol=row['solutions'][method];endpoints=[]
            for seat in ('seat0','seat1'):
                lo,hi=bounds(sol[seat]['value'])
                assert hi-lo==Q(sol[seat]['gap_exact']) and 0<=hi-lo<=Q(1,10**8)
                maxgap=max(maxgap,hi-lo);endpoints.append((lo,hi))
            (l0,u0),(l1,u1)=endpoints
            assert bounds(sol['minimum_exploitability'])==bounds(row['floors'][method])==(
                max(Q(0),(l1-u0)/2),(u1-l0)/2)
            floor_checks+=1
            for other,v in row['comparisons'][method].items():
                a,b=bounds(row['floors'][method]);c,d=bounds(row['floors'][other])
                checked(v,(a-d,b-c));comparison_checks+=1
        pairs=[(m,row['solutions'][m],controls) for m in methods]+[
            ('weighted_minus_ordinary',row['solutions']['weighted_preference'],row['solutions']['ordinary_preference'])]
        for name,a,b in pairs:
            l0,u0=bounds(a['seat0']['value']);l1,u1=bounds(a['seat1']['value'])
            r0,s0=bounds(b['seat0']['value']);r1,s1=bounds(b['seat1']['value'])
            checked(row['seat_effects'][name]['bettor'],((r0-u0)/2,(s0-l0)/2))
            checked(row['seat_effects'][name]['caller'],((l1-s1)/2,(u1-r1)/2));seat_checks+=2
    aggregates=0
    def check_stats(selected,actual):
        nonlocal aggregates
        def avg(xs):return tuple(sum(bounds(x)[i] for x in xs)/len(xs) for i in (0,1))
        def check(v,xs):
            assert bounds(v)==avg(xs)
            if 'counts' in v:assert v['counts']==dict(Counter(x['classification'] for x in xs))
        for m,v in actual['mean_floors'].items():check(v,[r['floors'][m] for r in selected]);aggregates+=1
        for m,cs in actual['comparisons'].items():
            for other,v in cs.items():check(v,[r['comparisons'][m][other] for r in selected]);aggregates+=1
        for m,ss in actual['seat_effects'].items():
            for seat,v in ss.items():check(v,[r['seat_effects'][m][seat] for r in selected]);aggregates+=1
    check_stats(rows,summary['overall'])
    for b,s in summary['boards'].items():
        selected=[r for r in rows if r['case']['board_index']==int(b)];assert len(selected)==6
        check_stats(selected,s)
        for p,v in s['pools'].items():check_stats([r for r in selected if r['case']['pool']==int(p)],v)
    for name,key in [('regimes','regime'),('textures','texture')]:
        for v,s in summary[name].items():check_stats([r for r in rows if r['case'][key]==v],s)
    for b,s in summary['leave_one_board_out'].items():check_stats([r for r in rows if r['case']['board_index']!=int(b)],s)
    assert floor_checks==144 and comparison_checks==1296 and seat_checks==384 and aggregates==2115
    return dict(passed=True,probabilities_checked=diagnostics,output_gradients=gradients,
        constant_outputs=constants,model_output_tasks=16,maximum_certificate_gap=float(maxgap),
        floor_identities=floor_checks,signed_comparisons=comparison_checks,seat_effects=seat_checks,
        aggregate_records=aggregates,expected_wrong_action_cost=errors,new_audit_fits=0,
        new_audit_lp_calls=0,auditor_sha256=digest(Path(__file__)))
