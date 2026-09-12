"""Independent arithmetic audit; reads frozen witnesses, never imports the worker."""
from collections import Counter
from fractions import Fraction
from hashlib import sha256
import json
from math import isclose
from pathlib import Path

def audit(out):
    q=Fraction
    read=lambda p:json.loads(p.read_bytes())
    h=lambda p:sha256(p.read_bytes()).hexdigest()
    def b(x):return q(x['lower_exact']),q(x['upper_exact'])
    def check(x,v):
        assert b(x)==v,(b(x),v)
        for name,val in zip(('lower_chips_approx','upper_chips_approx'),v):
            assert x[name]==float(val)
    def label(v):return 'lower' if v[1]<0 else 'higher' if v[0]>0 else 'overlapping'
    def subtract(x,y):return x[0]-y[1],x[1]-y[0]
    def weighted(terms):
        lo=hi=q(0)
        for c,v in terms:
            endpoints=(v[0],v[1]) if c>=0 else (v[1],v[0])
            lo+=c*endpoints[0];hi+=c*endpoints[1]
        return lo,hi
    def avg(items):return tuple(sum(v[i] for v in items)/len(items) for i in (0,1))
    plan=read(out/'plan.json')
    assert read(out/'worker-receipt.json')['exit']==0
    assert read(out/'worker-complete.json')==dict(complete=True,cases=48,
        fresh_asymmetric_certificates=192,arms_per_case=4,attempts={'fit':0,'lp':0})
    for p,d in plan['pins'].items():assert h(Path(p))==d,p
    assert not (out/'failed.json').exists()
    rows=[]; expected=[]; floors_checked=contrasts_checked=range_values=0
    maxgap=q(0)
    for case in plan['cases']:
        row=read(out/(case['id']+'.json'));rows.append(row)
        old=read(Path(plan['old'])/(case['id']+'.json'))
        new=read(Path(plan['new'])/(case['id']+'.json'))
        teacher=read(Path(plan['evaluation'])/(case['id']+'.json'))['teacher']
        assert row['case']==old['case']==new['case']==teacher['case']==case
        sol=[old['solutions']['clipped_prediction'],new['solutions']['clipped_target_model']]
        groups=[old['groups']['clipped_prediction'],new['groups']['clipped_target_model']]
        vals=[[b(s[f'seat{i}']['value']) for i in range(2)] for s in sol]
        for m in range(2):
            for seat in range(2):
                assert q(sol[m][f'seat{seat}']['gap_exact'])==vals[m][seat][1]-vals[m][seat][0]
                maxgap=max(maxgap,vals[m][seat][1]-vals[m][seat][0])
                assert row['values'][('old','new')[m]][seat]==sol[m][f'seat{seat}']['value']
        ef={}
        for arm,i,j in [('old_old',0,0),('new_old',1,0),('old_new',0,1),('new_new',1,1)]:
            endpoints=weighted([(q(1,2),vals[j][1]),(q(-1,2),vals[i][0])])
            v=max(q(0),endpoints[0]),endpoints[1]
            check(row['floors'][arm],v);floors_checked+=1;ef[arm]=v
            profile=row['profiles'][arm]
            assert profile['groups']==[groups[i][0],groups[j][1]]
            assert profile['bet']==sol[i]['seat0']['bet'] and profile['call']==sol[j]['seat1']['call']
            assert profile['source_seats']==[('old','new')[i],('old','new')[j]]
            assert [len(set(g)) for g in profile['groups']]==row['capacity']
            for probabilities,labels in zip([profile['bet'],profile['call']],profile['groups']):
                assert len(probabilities)==len(labels)==96
                seen={}
                for p,g in zip(probabilities,labels):
                    assert type(p) in (float,int) and 0<=p<=1
                    assert p==seen.setdefault(g,p)
        assert row['floors']['old_old']==old['floors']['clipped_prediction']
        assert row['floors']['new_new']==new['floors']['clipped_target_model']
        for ref in ('range_response','range_equity','clipped_oracle'):
            assert row['floors'][ref]==old['floors'][ref]==new['floors'][ref]
            ef[ref]=b(row['floors'][ref])
        e0=weighted([(q(1,2),vals[0][0]),(q(-1,2),vals[1][0])])
        e1=weighted([(q(1,2),vals[1][1]),(q(-1,2),vals[0][1])])
        es={'bettor':e0,'caller':e1,'both':(e0[0]+e1[0],e0[1]+e1[1])}
        for name,v in es.items():
            check(row['effects'][name],v);assert row['effects'][name]['classification']==label(v)
            contrasts_checked+=1
        comparisons={}
        for arm in ('old_old','new_old','old_new','new_new'):
            comparisons[arm]={}
            for ref in ('old_old','range_response','range_equity','clipped_oracle'):
                v=(q(0),q(0)) if arm==ref else subtract(ef[arm],ef[ref])
                check(row['comparisons'][arm][ref],v)
                assert row['comparisons'][arm][ref]['classification']==label(v)
                comparisons[arm][ref]=v;contrasts_checked+=1
        assert row['input_sha256']==sha256(json.dumps(teacher['inputs'],sort_keys=True,
            allow_nan=False).encode()).hexdigest()
        for seat, r in enumerate(row['range_mass']):
            assert r['hands']==teacher['inputs']['hands'][seat]
            raw={tuple(hand):weight for hand,weight in teacher['inputs']['ranges'][seat]}
            assert r['raw_weights']==[raw[tuple(hand)] for hand in r['hands']]
            joint=teacher['inputs']['joint']
            marginal=[sum(joint[i][j] for j in range(96)) for i in range(96)] if seat==0 else [
                sum(joint[i][j] for i in range(96)) for j in range(96)]
            assert all(isclose(x,y,rel_tol=1e-13,abs_tol=1e-15) for x,y in zip(marginal,r['marginal']))
            for band in ('low','middle','high'):
                assert r['counts'][band]==r['bands'].count(band)
                for field,ws in [('prior',r['raw_weights']),('conditioned',marginal)]:
                    mass=sum(w for w,t in zip(ws,r['bands']) if t==band)/sum(ws)
                    assert isclose(mass,r[field][band],rel_tol=1e-13,abs_tol=1e-15)
                    range_values+=1
        expected.append(dict(case=case,floors=ef,effects=es,comparisons=comparisons))
    assert len(rows)==48 and maxgap<=q(1,10**8)
    summary=read(out/'summary.json');aggregates=0
    def checkstats(v,values):
        check(v,avg(values));assert v['counts']==dict(Counter(label(t) for t in values))
    def checkagg(actual,selected):
        nonlocal aggregates
        assert actual['cases']==len(selected)
        for k,v in actual['floors'].items():check(v,avg([r['floors'][k] for r in selected]));aggregates+=1
        for k,v in actual['effects'].items():checkstats(v,[r['effects'][k] for r in selected]);aggregates+=1
        for arm,cs in actual['comparisons'].items():
            for ref,v in cs.items():
                checkstats(v,[r['comparisons'][arm][ref] for r in selected]);aggregates+=1
    checkagg(summary['overall'],expected)
    for bindex in range(8):
        checkagg(summary['boards'][str(bindex)],[r for r in expected if r['case']['board_index']==bindex])
        checkagg(summary['leave_one_board_out'][str(bindex)],
                 [r for r in expected if r['case']['board_index']!=bindex])
        for p in range(3):
            checkagg(summary['board_pools'][f'{bindex}-{p}'],[r for r in expected if
                r['case']['board_index']==bindex and r['case']['pool']==p])
    for bucket,key in [('regimes','regime'),('textures','texture')]:
        for value,s in summary[bucket].items():checkagg(s,[r for r in expected if r['case'][key]==value])
    pairdata=summary['paired_regime_effects'];pairvals=[]
    for p in pairdata['pairs']:
        selected={r['case']['regime']:r for r in expected if
                  r['case']['board_index']==p['board_index'] and r['case']['pool']==p['pool']}
        u,z=selected['uniform'],selected['polarized'];effects={}
        for key,v in p['effects'].items():
            effects[key]=subtract(z['effects'][key],u['effects'][key])
            check(v,effects[key]);assert v['classification']==label(effects[key])
        pairvals.append((p['board_index'],effects))
    assert len(pairvals)==24
    for key,v in pairdata['overall'].items():checkstats(v,[e[key] for _,e in pairvals])
    for bindex in range(8):
        for key,v in pairdata['boards'][str(bindex)].items():
            checkstats(v,[e[key] for bidx,e in pairvals if bidx==bindex])
        for key,v in pairdata['leave_one_board_out'][str(bindex)].items():
            checkstats(v,[e[key] for bidx,e in pairvals if bidx!=bindex])
    return dict(passed=True,cases=48,crossed_floor_identities=floors_checked,
        signed_case_contrasts=contrasts_checked,aggregate_records=aggregates,
        paired_regime_cases=24,range_mass_values=range_values,
        max_original_certificate_gap=float(maxgap),new_lp_calls=0,new_model_fits=0,
        auditor_sha256=h(Path(__file__)))
