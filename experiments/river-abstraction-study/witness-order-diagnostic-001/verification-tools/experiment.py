"""Frozen, no-refit caller threshold-order intervention on an observed panel."""
from environment import ROOT,PRIOR,old,np,opt,base,budget,transfer,read,write,digest
from collections import Counter
from fractions import Fraction as Q
from math import fsum
from pathlib import Path
import subprocess
import sys
from time import perf_counter
import tracemalloc
import projection
from test_projection import reference

HERE=Path(__file__).parent
NAME='witness-order-diagnostic-001'
NEW='caller_projected'
REFS=('ordinal','sign_conditioned','ordinary_preference','range_response')
METHODS=(NEW,*REFS)
CHECKPOINTS=(1000,10000,50000)

def forbidden(*a,**kw):raise AssertionError('forbidden operation')

def bindings(plan):
    assert sys.version_info[:3]==(3,14,6) and np.__version__=='2.5.2'
    assert budget.conf.scipy.__version__=='1.18.0' and not tracemalloc.is_tracing()
    for p,h in plan['pins'].items():assert digest(p)==h,p
    assert plan['evaluation_cases']==read(PRIOR/'plan.json')['evaluation_cases']
    assert plan['methods']==list(METHODS) and plan['bets']==[5,10]
    old.model.fit=forbidden;old.ordinal.fit_models=forbidden

def filename(case,bet):return old.filename('eval',case,bet)

def propose(prior,matrix):
    original=prior['proposal']['features']['ordinal'][1]
    projected=projection.project(original)
    weights=matrix.joint.sum(axis=0)
    before=prior['proposal']['groups']['ordinal']
    k=len(set(before[1]))
    caller=old.anchored_clusters(np.asarray(projected),weights,k).tolist()
    groups=[before[0],caller];opt.validate(matrix,groups)
    assert [len(set(g)) for g in groups]==[len(set(g)) for g in before]
    delta=np.asarray(projected)-np.asarray(original)
    g,h=np.asarray(before[1]),np.asarray(caller)
    diagnostic=dict(
        crossing_before=old.ordinal.crossing(original,weights)['mean'],
        crossing_after=old.ordinal.crossing(projected,weights)['mean'],
        changed_hand_mass=float(weights[np.any(delta!=0,axis=1)].sum()),
        zero_head_mean_absolute_shift=float(weights @ np.abs(delta[:,[1,4,7]]).mean(axis=1)),
        weighted_squared_distance=float(weights @ (delta*delta).sum(axis=1)),
        changed_comembership_mass=float(np.sum(np.outer(weights,weights)*
            ((g[:,None]==g[None,:])!=(h[:,None]==h[None,:])))))
    assert diagnostic['crossing_after']==0
    return dict(groups=groups,caller_features=projected,diagnostic=diagnostic)

def worker(plan,out):
    bindings(plan);calls=0;original=opt.linprog
    def counted(*a,**kw):
        nonlocal calls
        calls+=1;assert calls<=128
        return original(*a,**kw)
    opt.linprog=counted
    for i,case in enumerate(plan['evaluation_cases']):
        for bet in plan['bets']:
            name=filename(case,bet);prior=read(PRIOR/name)
            game,matrix=transfer.build(prior['inputs'],bet)
            assert game.provenance_digest==prior['provenance_digest']
            proposed=propose(prior,matrix)
            solution=opt.solve_groups(matrix,proposed['groups'])
            records=old.solve(matrix,proposed['groups'],solution)
            assert all(p['policy'][0]==q['policy'][0] for p,q in
                       zip(records,prior['records']['ordinal'],strict=True))
            write(out/name,dict(case=case,bet=bet,prior_sha256=digest(PRIOR/name),
                **proposed,solution=solution,records=records))
        print(f'completed {i+1}/32 case pairs',flush=True)
    assert calls==128;bindings(plan)
    write(out/'worker-complete.json',dict(complete=True,lp_calls=calls,fit_tasks=0,
        cells=64,trajectories=64,checkpoint_policies=192,bettor_unchanged=True))

def combined(row):
    prior=read(PRIOR/filename(row['case'],row['bet']))
    return dict(case=row['case'],bet=row['bet'],diagnostic=row['diagnostic'],
        solutions={NEW:row['solution'],**{m:prior['solutions'][m] for m in REFS}},
        records={NEW:row['records'],**{m:prior['records'][m] for m in REFS}})

def direction(d):return 'lower' if d < -1e-10 else 'higher' if d > 1e-10 else 'overlapping'

def stats(rows,n=50000):
    avg=lambda v:fsum(v)/len(v)
    actual={m:avg([next(p for p in r['records'][m] if p['iteration']==n)['full']['exploitability']
                      for r in rows]) for m in METHODS}
    floors={m:base.average([r['solutions'][m]['minimum_exploitability'] for r in rows]) for m in METHODS}
    comparisons={}
    for m in REFS:
        ds=[next(p for p in r['records'][NEW] if p['iteration']==n)['full']['exploitability']-
            next(p for p in r['records'][m] if p['iteration']==n)['full']['exploitability'] for r in rows]
        comparisons[m]=dict(actual_delta=avg(ds),cell_directions=dict(Counter(map(direction,ds))),
            floor_delta=base.average([base.difference(r['solutions'][NEW]['minimum_exploitability'],
                r['solutions'][m]['minimum_exploitability']) for r in rows]))
    return dict(actual=actual,floors=floors,comparisons=comparisons,
        diagnostics={k:avg([r['diagnostic'][k] for r in rows]) for k in rows[0]['diagnostic']})

def panels(rows):
    result={}
    for bet in (5,10):
        rs=[r for r in rows if r['bet']==bet]
        result[str(bet)]=dict(overall=stats(rs),
            checkpoints={str(n):stats(rs,n) for n in CHECKPOINTS},
            boards={str(b):stats([r for r in rs if r['case']['board_index']==b]) for b in range(8)},
            textures={t:stats([r for r in rs if r['case']['texture']==t]) for t in sorted({r['case']['texture'] for r in rs})},
            regimes={t:stats([r for r in rs if r['case']['regime']==t]) for t in ('uniform','polarized')},
            leave_one_board_out={str(b):stats([r for r in rs if r['case']['board_index']!=b]) for b in range(8)})
    def win(b,m):
        c=result[b]['overall']['comparisons'][m]
        return c['actual_delta'] < -1e-10 and Q(c['floor_delta']['upper_exact'])<0
    c=result['10']['overall']['comparisons']['ordinal']
    return dict(panels=result,flags=dict(primary_mechanism_support=win('5','ordinal'),
        primary_practical_recovery=all(win('5',m) for m in ('ordinal','sign_conditioned','ordinary_preference')),
        secondary_pot_nonregression=c['actual_delta']<=1e-10 and Q(c['floor_delta']['upper_exact'])<=Q('1e-10')))

def audit_summary(summary,rows):
    """Independent rational accumulation of all reported panel score and floor means."""
    checks=0
    for bet,panel in summary['panels'].items():
        rs=[r for r in rows if str(r['bet'])==bet]
        selections=[(panel['overall'],rs,50000)]
        for category in ('checkpoints','boards','textures','regimes','leave_one_board_out'):
            for label,v in panel[category].items():
                subset=rs
                if category=='boards':subset=[r for r in rs if str(r['case']['board_index'])==label]
                elif category=='leave_one_board_out':subset=[r for r in rs if str(r['case']['board_index'])!=label]
                elif category=='textures':subset=[r for r in rs if r['case']['texture']==label]
                elif category=='regimes':subset=[r for r in rs if r['case']['regime']==label]
                selections.append((v,subset,int(label) if category=='checkpoints' else 50000))
        for v,subset,n in selections:
            actual={};bounds={}
            for m in METHODS:
                actual[m]=sum(Q(next(p for p in r['records'][m] if p['iteration']==n)['full']['exploitability']) for r in subset)/len(subset)
                assert abs(float(actual[m])-v['actual'][m])<1e-14;checks+=1
                bounds[m]=[sum(Q(r['solutions'][m]['minimum_exploitability'][k]) for r in subset)/len(subset)
                           for k in ('lower_exact','upper_exact')]
                for x,k in zip(bounds[m],('lower_exact','upper_exact')):
                    assert Q(v['floors'][m][k])==x;checks+=1
            for m in REFS:
                c=v['comparisons'][m]
                assert abs(float(actual[NEW]-actual[m])-c['actual_delta'])<1e-14
                assert Q(c['floor_delta']['lower_exact'])==bounds[NEW][0]-bounds[m][1]
                assert Q(c['floor_delta']['upper_exact'])==bounds[NEW][1]-bounds[m][0];checks+=3
                ds=[next(p for p in r['records'][NEW] if p['iteration']==n)['full']['exploitability']-
                    next(p for p in r['records'][m] if p['iteration']==n)['full']['exploitability'] for r in subset]
                assert c['cell_directions']==dict(Counter(map(direction,ds)));checks+=1
            for k,x in v['diagnostics'].items():
                assert abs(float(sum(Q(r['diagnostic'][k]) for r in subset)/len(subset))-x)<1e-14;checks+=1
    primary=summary['panels']['5']['overall']['comparisons']
    wins={m:primary[m]['actual_delta'] < -1e-10 and Q(primary[m]['floor_delta']['upper_exact'])<0 for m in REFS}
    secondary=summary['panels']['10']['overall']['comparisons']['ordinal']
    assert summary['flags']==dict(primary_mechanism_support=wins['ordinal'],
        primary_practical_recovery=all(wins[m] for m in ('ordinal','sign_conditioned','ordinary_preference')),
        secondary_pot_nonregression=secondary['actual_delta']<=1e-10 and Q(secondary['floor_delta']['upper_exact'])<=Q('1e-10'))
    return dict(passed=True,rational_summary_checks=checks+3)

def verify(plan,out):
    bindings(plan);opt.linprog=forbidden;opt.solve_groups=forbidden
    tool=base.helpers();cache={};certs=policies=triplets=0;maximum=0.;rows=[]
    models=read(PRIOR/'candidate.json')['models']
    for i,case in enumerate(plan['evaluation_cases']):
        for bet in plan['bets']:
            name=filename(case,bet);prior=read(PRIOR/name);row=read(out/name)
            assert row['case']==case and row['bet']==bet and row['prior_sha256']==digest(PRIOR/name)
            matrix,core=old.setup(case,bet,tool,cache)
            assert all(prior[k]==v for k,v in core.items())
            for seat in (0,1):
                f=old.model.predict(models['ordinal'][seat],old.model.design(core['raw_features'][seat],bet,True))
                assert f.tolist()==prior['proposal']['features']['ordinal'][seat]
            proposal=propose(prior,matrix)
            assert all(row[k]==v for k,v in proposal.items())
            for src,dst in zip(prior['proposal']['features']['ordinal'][1],row['caller_features'],strict=True):
                for j in (0,3,6):
                    expected=reference(src[j:j+3]);actual=dst[j:j+3]
                    assert max(abs(a-b) for a,b in zip(expected,actual))<=2e-15
                    assert 1>=actual[0]>=actual[1]>=actual[2]>=0
                    if src[j]>=src[j+1]>=src[j+2]:assert src[j:j+3]==actual
                    triplets+=1
            assert row['groups'][0]==prior['proposal']['groups']['ordinal'][0]
            for m in METHODS:
                groups=row['groups'] if m==NEW else prior['proposal']['groups'][m]
                solution=row['solution'] if m==NEW else prior['solutions'][m]
                opt.verify_solution(matrix,groups,solution);certs+=2
                records=row['records'] if m==NEW else prior['records'][m]
                g=[np.asarray(v) for v in groups];reduced=matrix.aggregate(g)
                engine=old.RegretBR(matrix,g) if m==NEW else None
                assert [p['iteration'] for p in records]==list(CHECKPOINTS)
                for index,p in enumerate(records):
                    if engine:
                        while engine.iteration<p['iteration']:engine.step()
                        assert [v.tolist() for v in engine.average()]==p['policy']
                        assert p['policy'][0]==prior['records']['ordinal'][index]['policy'][0]
                    scored=budget.score(matrix,reduced,g,{k:p[k] for k in
                        ('kind','budget','iteration','policy','active_seconds')},solution['minimum_exploitability'])
                    assert scored==p and p['above_floor']>=-1e-8
                    assert p['budget']==p['iteration'] and p['kind']=='iterations'
                    assert np.isfinite(p['active_seconds']) and p['active_seconds']>=0
                    scalar=budget.scalar_evaluate(matrix,*[np.asarray(v)[gs] for v,gs in zip(p['policy'],g,strict=True)])
                    for k,v in scalar.items():
                        error=abs(v-p['full'][k]);maximum=max(maximum,error);assert error<1e-10
                    policies+=1
            rows.append(combined(row))
        print(f'verified {i+1}/32 case pairs',flush=True)
    assert (certs,policies,triplets)==(640,960,18432)
    summary=panels(rows);write(out/'summary.json',summary)
    write(out/'summary-audit.json',audit_summary(summary,rows));bindings(plan)
    write(out/'audit.json',dict(passed=True,certificates=certs,checkpoint_scores=policies,
        projected_triplets_independently_checked=triplets,replayed_iterations=3200000,
        maximum_scalar_discrepancy=maximum,parent_lp_calls=0,fit_tasks=0,bettor_bit_identical=True))

def run(path,expected):
    assert digest(path)==expected
    plan=read(path);bindings(plan);out=Path(plan['output']);out.mkdir(parents=True,exist_ok=False)
    write(out/'plan.json',plan);write(out/'started.json',dict(plan_sha256=expected))
    start=perf_counter()
    try:
        for mode in ('worker','verify'):
            command=[sys.executable,'-B','-W','error::ResourceWarning',str(HERE/'experiment.py'),mode,str(path),expected]
            begin=perf_counter()
            with (out/(mode+'-stdout.txt')).open('xb') as stdout,(out/(mode+'-stderr.txt')).open('xb') as stderr:
                result=subprocess.run(command,cwd=ROOT,stdout=stdout,stderr=stderr,timeout=plan['phase_timeout_seconds'])
            write(out/(mode+'-receipt.json'),dict(command=command,exit=result.returncode,
                seconds=perf_counter()-begin,timeout_seconds=plan['phase_timeout_seconds']))
            assert result.returncode==0,mode+' failed'
        bindings(plan)
        write(out/'results-manifest.json',{p.name:digest(p) for p in sorted(out.iterdir()) if p.is_file()})
        write(out/'receipt.json',dict(exit=0,seconds=perf_counter()-start,
            result_manifest_sha256=digest(out/'results-manifest.json')))
        print(read(out/'audit.json'));print(read(out/'summary.json')['flags'])
    except BaseException as error:
        write(out/'failed.json',dict(error=type(error).__name__,message=str(error)));raise

if __name__=='__main__':
    if sys.argv[1]=='run':run(Path(sys.argv[2]),sys.argv[3])
    else:
        assert digest(sys.argv[2])==sys.argv[3]
        plan=read(sys.argv[2]);{'worker':worker,'verify':verify}[sys.argv[1]](plan,Path(plan['output']))
