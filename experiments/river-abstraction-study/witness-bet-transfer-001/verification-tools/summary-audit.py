"""Independent rational arithmetic on retained transfer endpoints and interactions."""
from collections import Counter
from fractions import Fraction as Q
import json
from math import isclose
from pathlib import Path


def audit(out):
    read=lambda p:json.loads(p.read_bytes())
    plan=read(out/'plan.json')
    saved=read(out/'summary.json')
    methods=plan['methods']
    rows=[read(out/(c['id']+f'-bet-{bet:g}.json')) for c in plan['cases'] for bet in plan['bets']]
    checked=0
    def interval(lo,hi,classification=False):
        result=dict(lower_exact=str(lo),upper_exact=str(hi),
                    lower_chips_approx=float(lo),upper_chips_approx=float(hi))
        if classification:
            result['classification']='lower' if hi<0 else 'higher' if lo>0 else 'overlapping'
        return result
    def average(xs):
        return sum(map(Q,xs))/len(xs)
    def mean_intervals(xs):
        return interval(average([x['lower_exact'] for x in xs]),average([x['upper_exact'] for x in xs]))
    def diff(a,b):
        return interval(Q(a['lower_exact'])-Q(b['upper_exact']),
                        Q(a['upper_exact'])-Q(b['lower_exact']),True)
    def compare(actual,expected):
        nonlocal checked
        if isinstance(expected,dict):
            assert actual.keys()==expected.keys(),(actual.keys(),expected.keys())
            for key,value in expected.items():compare(actual[key],value)
        elif isinstance(expected,list):
            assert len(actual)==len(expected)
            for a,b in zip(actual,expected,strict=True):compare(a,b)
        elif isinstance(expected,str):
            assert actual==expected
            checked+=1
        else:
            assert isclose(float(actual),float(expected),rel_tol=1e-12,abs_tol=1e-12),(actual,expected)
            checked+=1
    def stats(rs,iteration=10000):
        def rec(r,m):return next(x for x in r['methods'][m]['records'] if x['iteration']==iteration)
        floors={m:mean_intervals([r['methods'][m]['solution']['minimum_exploitability'] for r in rs])
                for m in methods}
        result=dict(means={m:average([rec(r,m)['full']['exploitability'] for r in rs]) for m in methods},
            floors=floors,comparisons={},
            above_floor={m:average([rec(r,m)['above_floor'] for r in rs]) for m in methods},
            restricted={m:average([rec(r,m)['restricted']['exploitability'] for r in rs]) for m in methods})
        for m in methods[1:]:
            ds=[Q(rec(r,methods[0])['full']['exploitability'])-Q(rec(r,m)['full']['exploitability']) for r in rs]
            fs=[diff(r['methods'][methods[0]]['solution']['minimum_exploitability'],
                     r['methods'][m]['solution']['minimum_exploitability']) for r in rs]
            result['comparisons'][m]=dict(actual=dict(delta=sum(ds)/len(ds),counts=dict(Counter(
                'lower' if d<Q(-1e-10) else 'higher' if d>Q(1e-10) else 'overlapping' for d in ds))),
                floor=dict(**mean_intervals(fs),counts=dict(Counter(x['classification'] for x in fs))))
        if iteration==10000:
            result.update(fixed_policy={m:average([r['methods'][m]['half_pot_policy_evaluation']['exploitability']
                                                  for r in rs]) for m in methods},
                resolved_minus_fixed={m:average([r['methods'][m]['resolved_minus_fixed'] for r in rs])
                                      for m in methods},
                action_change={m:[average([r['methods'][m]['action_change'][seat] for r in rs])
                                  for seat in (0,1)] for m in methods})
        return result
    rebuilt={}
    for key,panel in saved['panels'].items():
        rs=[r for r in rows if r['bet']==float(key)]
        assert len(rs)==96
        rebuilt[key]=stats(rs)
        compare(panel['overall'],rebuilt[key])
        for n,s in panel['iterations'].items():compare(s,stats(rs,int(n)))
        for name,predicate in [('boards',lambda r,k:r['case']['board_index']==int(k)),
            ('textures',lambda r,k:r['case']['texture']==k),
            ('regimes',lambda r,k:r['case']['regime']==k),
            ('leave_one_board_out',lambda r,k:r['case']['board_index']!=int(k))]:
            for label,value in panel[name].items():
                compare(value,stats([r for r in rs if predicate(r,label)]))
    for key,values in saved['interactions_vs_half_pot'].items():
        for m,actual in values.items():
            a,b=rebuilt[key]['comparisons'][m],rebuilt['5.0']['comparisons'][m]
            compare(actual,dict(actual=a['actual']['delta']-b['actual']['delta'],floor=diff(a['floor'],b['floor'])))
    act=lambda s:s['comparisons']['range_response']['actual']['delta'] < -1e-10
    flo=lambda s:Q(s['comparisons']['range_response']['floor']['upper_exact'])<0
    assert saved['actual_policy_transfer_pass']==all(act(rebuilt[k]) for k in ('2.5','10.0'))
    assert saved['representation_transfer_pass']==all(flo(rebuilt[k]) for k in ('2.5','10.0'))
    assert saved['robustness_pass']==all(act(s) and flo(s) for k in ('2.5','10.0') for name in
        ('textures','regimes','leave_one_board_out') for s in saved['panels'][k][name].values())
    return dict(passed=True,summary_scalar_checks=checked,case_bet_cells=288,
                arithmetic='Fraction from retained binary64, exact interval endpoints',
                decision_flags_checked=3)
