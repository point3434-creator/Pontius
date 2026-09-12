"""Separate stdlib rational reconstruction of panels and declared decisions."""
from collections import Counter
from fractions import Fraction as Q
from math import isclose
import json
from pathlib import Path


def audit(out):
    read=lambda p:json.loads(p.read_bytes())
    plan=read(out/'plan.json')
    saved=read(out/'summary.json')
    rows=[read(out/(c['id']+'.json')) for c in plan['cases']]
    methods=('ordinary_preference','range_response')
    checked=0
    def compare(actual,expected):
        nonlocal checked
        if isinstance(expected,dict):
            assert actual.keys()==expected.keys(),(actual.keys(),expected.keys())
            for k,v in expected.items():compare(actual[k],v)
        elif isinstance(expected,str):
            assert actual==expected
            checked+=1
        else:
            assert isclose(float(actual),float(expected),rel_tol=1e-12,abs_tol=1e-12),(actual,expected)
            checked+=1
    avg=lambda xs:sum(map(Q,xs))/len(xs)
    def interval(lo,hi):
        return dict(lower_exact=str(lo),upper_exact=str(hi),
                    lower_chips_approx=float(lo),upper_chips_approx=float(hi))
    def mean_intervals(xs):
        return interval(avg([x['lower_exact'] for x in xs]),avg([x['upper_exact'] for x in xs]))
    def stats(rs,n):
        values={}
        gaps={}
        times={}
        for m in methods:
            for a in ('cfr','br'):
                ps=[next(p for p in next(run for run in r['runs'] if run['method']==m and
                    run['algorithm']==a)['records'] if p['iteration']==n) for r in rs]
                key=m+':'+a
                values[key]=[Q(p['full']['exploitability']) for p in ps]
                gaps[key]=avg([p['above_floor'] for p in ps])
                times[key]=avg([p['active_seconds'] for p in ps])
        pairs={'learned_br_minus_cfr':('ordinary_preference:br','ordinary_preference:cfr'),
            'response_br_minus_cfr':('range_response:br','range_response:cfr'),
            'learned_minus_response_br':('ordinary_preference:br','range_response:br'),
            'learned_minus_response_cfr':('ordinary_preference:cfr','range_response:cfr')}
        comparisons={}
        for k,(a,b) in pairs.items():
            ds=[x-y for x,y in zip(values[a],values[b],strict=True)]
            comparisons[k]=dict(delta=avg(ds),counts=dict(Counter(
                'lower' if d<Q(-1e-10) else 'higher' if d>Q(1e-10) else 'overlapping' for d in ds)))
        return dict(means={k:avg(v) for k,v in values.items()},above_floor=gaps,
            mean_active_seconds=times,floors={m:mean_intervals([r['floors'][m] for r in rs]) for m in methods},
            comparisons=comparisons)
    def group_stats(rs):
        def floor(r,m):return r['floors'][m] if m in methods else r['oracle'][m]['solution']['minimum_exploitability']
        names=(*methods,'half_witness','pot_witness')
        comparisons={}
        for m in (*methods,'half_witness'):
            ds=[]
            labels=[]
            for r in rs:
                a,b=floor(r,'pot_witness'),floor(r,m)
                lo,hi=Q(a['lower_exact'])-Q(b['upper_exact']),Q(a['upper_exact'])-Q(b['lower_exact'])
                ds.append(interval(lo,hi))
                labels.append('lower' if hi<0 else 'higher' if lo>0 else 'overlapping')
            comparisons['pot_minus_'+m]=dict(**mean_intervals(ds),counts=dict(Counter(labels)))
        return dict(floors={m:mean_intervals([floor(r,m) for r in rs]) for m in names},comparisons=comparisons)
    polarized=[r for r in rows if r['case']['regime']=='polarized']
    paired=[r for r in rows if r['case']['texture']=='multiple-pairs-or-trips']
    intersection=[r for r in paired if r['case']['regime']=='polarized']
    assert [len(rows),len(polarized),len(paired),len(intersection)]==[60,48,24,12]
    panels=dict(polarized=polarized,paired_trips=paired,intersection=intersection)
    for name,rs in panels.items():
        for n,v in saved['solver_panels'][name].items():compare(v,stats(rs,int(n)))
        for b,v in saved['solver_boards'][name].items():
            compare(v,stats([r for r in rs if r['case']['board_index']==int(b)],50000))
        for b,v in saved['solver_leave_one_board_out'][name].items():
            compare(v,stats([r for r in rs if r['case']['board_index']!=int(b)],50000))
    grouping=saved['grouping']
    compare(grouping['overall'],group_stats(paired))
    for name,predicate in [('boards',lambda r,k:r['case']['board_index']==int(k)),
        ('regimes',lambda r,k:r['case']['regime']==k),
        ('leave_one_board_out',lambda r,k:r['case']['board_index']!=int(k))]:
        for label,v in grouping[name].items():compare(v,group_stats([r for r in paired if predicate(r,label)]))
    primary=stats(polarized,50000)['comparisons']
    assert saved['solver_gap_reduced']==(primary['learned_br_minus_cfr']['delta']<Q(-1e-10))
    assert saved['solver_ranking_repaired']==(primary['learned_minus_response_br']['delta']<Q(-1e-10))
    grp=group_stats(paired)['comparisons']
    assert saved['oracle_representation_repaired']==all(Q(grp['pot_minus_'+m]['upper_exact'])<0 for m in methods)
    assert saved['oracle_context_gain']==(Q(grp['pot_minus_half_witness']['upper_exact'])<0)
    return dict(passed=True,summary_scalar_checks=checked,panel_sizes=[48,24,12],union_cases=60,
                arithmetic='Fraction from binary64 and exact certificate endpoints',decision_flags_checked=4)
