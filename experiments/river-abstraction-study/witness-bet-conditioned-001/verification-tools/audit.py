"""Independent standard-library reconstruction of every reported panel."""
from collections import Counter
from fractions import Fraction as Q
import json
from math import isclose

def audit(out):
    read=lambda p:json.loads(p.read_bytes())
    plan=read(out/'plan.json');saved=read(out/'summary.json')
    rows=[read(out/f"eval-{c['id']}-bet-{b}.json") for c in plan['evaluation_cases'] for b in (5,10)]
    methods=('conditioned','blind','ordinary_preference','range_response','oracle_sign','oracle_clipped')
    solvers=methods[:4];checks=0
    avg=lambda xs:sum(map(Q,xs))/len(xs)
    def interval(lo,hi):return dict(lower_exact=str(lo),upper_exact=str(hi),
        lower_chips_approx=float(lo),upper_chips_approx=float(hi))
    def compare(a,b):
        nonlocal checks
        if isinstance(b,dict):
            assert a.keys()==b.keys()
            for k,v in b.items():compare(a[k],v)
        elif isinstance(b,str):assert a==b;checks+=1
        else:assert isclose(float(a),float(b),rel_tol=1e-12,abs_tol=1e-12);checks+=1
    def stats(rs,n):
        vals={m:[Q(next(p for p in r['records'][m] if p['iteration']==n)['full']['exploitability'])
                 for r in rs] for m in solvers}
        floors={m:interval(avg([r['solutions'][m]['minimum_exploitability']['lower_exact'] for r in rs]),
                            avg([r['solutions'][m]['minimum_exploitability']['upper_exact'] for r in rs])) for m in methods}
        comparisons={}
        for m in methods[1:]:
            lo=[];hi=[];labels=[]
            for r in rs:
                a=r['solutions']['conditioned']['minimum_exploitability']
                b=r['solutions'][m]['minimum_exploitability']
                l=Q(a['lower_exact'])-Q(b['upper_exact']);h=Q(a['upper_exact'])-Q(b['lower_exact'])
                lo.append(l);hi.append(h);labels.append('lower' if h<0 else 'higher' if l>0 else 'overlapping')
            v=dict(floor=dict(**interval(avg(lo),avg(hi)),counts=dict(Counter(labels))))
            if m in solvers:
                ds=[a-b for a,b in zip(vals['conditioned'],vals[m],strict=True)]
                v['actual']=dict(delta=avg(ds),counts=dict(Counter('lower' if d<Q(-1e-10) else
                    'higher' if d>Q(1e-10) else 'overlapping' for d in ds)))
            comparisons[m]=v
        return dict(actual={m:avg(v) for m,v in vals.items()},floors=floors,comparisons=comparisons)
    expected={}
    for bet in (5,10):
        rs=[r for r in rows if r['bet']==bet]
        assert len(rs)==32 and Counter(r['case']['board_index'] for r in rs)==dict.fromkeys(range(8),4)
        panels=dict(overall=stats(rs,50000),checkpoints={str(n):stats(rs,n) for n in (1000,10000,50000)},
            boards={str(b):stats([r for r in rs if r['case']['board_index']==b],50000) for b in range(8)},
            textures={t:stats([r for r in rs if r['case']['texture']==t],50000) for t in sorted({r['case']['texture'] for r in rs})},
            regimes={t:stats([r for r in rs if r['case']['regime']==t],50000) for t in ('uniform','polarized')},
            leave_one_board_out={str(b):stats([r for r in rs if r['case']['board_index']!=b],50000) for b in range(8)})
        expected[str(bet)]=panels
        compare(saved['panels'][str(bet)],panels)
    pot=expected['10']['overall']['comparisons']
    flags=dict(conditioning_actual_gain=pot['blind']['actual']['delta']<Q(-1e-10),
        conditioning_floor_gain=Q(pot['blind']['floor']['upper_exact'])<0,
        beats_existing_actual=all(pot[m]['actual']['delta']<Q(-1e-10) for m in ('ordinary_preference','range_response')),
        beats_existing_floor=all(Q(pot[m]['floor']['upper_exact'])<0 for m in ('ordinary_preference','range_response')))
    flags['cross_bet_robustness']=all(v['comparisons'][m]['actual']['delta']<Q(-1e-10) and
        Q(v['comparisons'][m]['floor']['upper_exact'])<0 for panel in expected.values()
        for category in ('textures','regimes','leave_one_board_out') for v in panel[category].values()
        for m in ('blind','ordinary_preference','range_response'))
    assert flags==saved['flags']
    return dict(passed=True,summary_scalar_checks=checks,decision_flags_checked=5,
        evaluation_cells=64,board_units=8,arithmetic='Fraction from binary64 and exact certificate endpoints')
