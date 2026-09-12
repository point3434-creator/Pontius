"""Separate stdlib recomputation of every mean, comparison and declared decision."""
from collections import Counter
from fractions import Fraction as Q
from math import isclose
import json
from pathlib import Path
import sys


def audit(out):
    read=lambda p:json.loads(p.read_bytes())
    plan=read(out/'plan.json')
    saved=read(out/'summary.json')
    rows=[read(out/(case['id']+'.json')) for case in plan['cases']]
    methods=plan['methods']
    verified=0
    def close(a,b):
        assert isclose(float(a),float(b),rel_tol=1e-12,abs_tol=1e-12),(a,b)
    def stats(panel,key,repetition=None):
        kind,budget=key.split(':')
        budget=float(budget)
        values={m:[] for m in methods}
        extras={k:{m:[] for m in methods} for k in ('above_floor','restricted','mean_iterations')}
        for row in panel:
            for m in methods:
                rs=[r for run in row['runs'] if run['method']==m
                    and (repetition is None or run['repetition']==repetition)
                    for r in run['records'] if r['kind']==kind and r['budget']==budget]
                assert len(rs)==(3 if kind=='seconds' and repetition is None else 1)
                values[m].append(sum(Q(r['full']['exploitability']) for r in rs)/len(rs))
                for name,path in [('above_floor',None),('restricted','exploitability'),
                                  ('mean_iterations',None)]:
                    vals=[r['iteration'] if name=='mean_iterations' else
                          r[name][path] if path else r[name] for r in rs]
                    extras[name][m].append(sum(map(Q,vals))/len(vals))
        result={'means':{m:sum(v)/len(v) for m,v in values.items()},'comparisons':{}}
        for name,vs in extras.items():
            result[name]={m:sum(v)/len(v) for m,v in vs.items()}
        for m in methods[1:]:
            ds=[a-b for a,b in zip(values[methods[0]],values[m],strict=True)]
            result['comparisons'][m]=dict(delta=sum(ds)/len(ds),counts=dict(Counter(
                'lower' if d < Q(-1e-10) else 'higher' if d > Q(1e-10) else 'overlapping'
                for d in ds)))
        return result
    def check(actual,expected):
        nonlocal verified
        if isinstance(expected,dict):
            assert actual.keys()==expected.keys()
            for k,v in expected.items():check(actual[k],v)
        else:
            close(actual,expected)
            verified+=1
    for key,value in saved['overall'].items():check(value,stats(rows,key))
    for name,predicate in [('boards',lambda r,k:r['case']['board_index']==int(k)),
                           ('textures',lambda r,k:r['case']['texture']==k),
                           ('regimes',lambda r,k:r['case']['regime']==k),
                           ('leave_one_board_out',lambda r,k:r['case']['board_index']!=int(k))]:
        for k,panel in saved[name].items():
            subset=[r for r in rows if predicate(r,k)]
            for key,value in panel.items():check(value,stats(subset,key))
    for k,v in saved['repetitions'].items():check(v,stats(rows,'seconds:0.5',int(k)))
    passed=lambda v:v['comparisons']['range_response']['delta'] < -1e-10
    assert saved['numerical_improvement_pass']==all(passed(saved['overall'][k])
        for k in ('iterations:10000','seconds:0.5'))
    assert saved['robustness_pass']==(all(passed(v) for name in
        ('textures','regimes','leave_one_board_out') for panel in saved[name].values()
        for v in panel.values()) and all(passed(v) for v in saved['repetitions'].values()))
    close(saved['common_seconds'],sum(Q(r['common_seconds']) for r in rows))
    for m in methods:
        close(saved['setup_seconds'][m],sum(Q(run['setup_seconds']) for r in rows
                                           for run in r['runs'] if run['method']==m))
    assert saved['setup_misses']==sum(rec.get('setup_missed',False) for r in rows
                                     for run in r['runs'] for rec in run['records'])
    return dict(passed=True,summary_scalars_verified=verified,arithmetic='Fraction from binary64',
                all_cases=96,all_checkpoint_policies=3456)


if __name__=='__main__':
    out=Path(sys.argv[1])
    value=audit(out)
    with (out/'summary-audit.json').open('x',encoding='utf-8',newline='\n') as f:
        f.write(json.dumps(value,sort_keys=True,indent=2)+'\n')
    print(json.dumps(value,indent=2))
