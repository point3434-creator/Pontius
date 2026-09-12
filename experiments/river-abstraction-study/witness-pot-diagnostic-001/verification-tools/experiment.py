"""Pot-sized solver-objective and oracle-grouping diagnostics; fixed observed panels."""
from collections import Counter
from fractions import Fraction as Q
from math import fsum
from pathlib import Path
import importlib.util
import json
import subprocess
import sys
from time import perf_counter
import tracemalloc

from context import (ROOT,PRIOR,transfer,budget,np,opt,base,read,write,digest,CFR,
                     PayoffGame,anchored_clusters,action_advantages,select)
from br import RegretBR

HERE=Path(__file__).parent
METHODS=('ordinary_preference','range_response')
BANK=transfer.METHODS
CHECKPOINTS=(1000,10000,50000)
VARIANTS=('half_witness','pot_witness')


def bindings(plan):
    assert sys.version_info[:3]==(3,14,6)
    assert np.__version__=='2.5.2' and budget.conf.scipy.__version__=='1.18.0'
    assert not tracemalloc.is_tracing()
    assert digest(__file__)==plan['script_sha256']
    for p,h in plan['pins'].items():assert digest(p)==h,p
    assert plan['cases']==select(read(PRIOR/'plan.json')['cases'])
    assert len(plan['cases'])==60


def setup(case,tool,cache):
    old=read(transfer.PRIOR/(case['id']+'.json'))
    pot=read(PRIOR/(case['id']+'-bet-10.json'))
    game,matrix=transfer.build(old['inputs'],10.)
    assert game.provenance_digest==pot['provenance_digest']
    equities=tool.old.equities_for(case,cache)
    models=read(transfer.PRIOR/'candidate.json')['models']
    transfer.feature_identity(matrix,equities,tool,models,old)
    groups={}
    for m in BANK:
        pair,_,_=budget.prepare(matrix,equities,models,m,tool)
        assert [g.tolist() for g in pair]==old['groups'][m]==pot['methods'][m]['groups']
        groups[m]=pair
    return old,pot,matrix,groups


def oracle_groups(case,old,pot,matrix,groups):
    half=read(PRIOR/(case['id']+'-bet-5.json'))
    _,half_matrix=transfer.build(old['inputs'],5.)
    assert half_matrix.source_digest==half['provenance_digest']
    proposals={}
    for variant,source,source_matrix in [('half_witness',half,half_matrix),('pot_witness',pot,matrix)]:
        features=[]
        labels=[]
        for seat in (0,1):
            opponents=[source['methods'][m]['solution'][f'seat{seat}']['call' if seat==0 else 'bet'] for m in BANK]
            raw=action_advantages(source_matrix,opponents,seat)
            clipped=np.clip(raw,-.5,.5)
            k=len(set(groups['ordinary_preference'][seat]))
            g=anchored_clusters(clipped,matrix.joint.sum(axis=1-seat),k)
            assert len(set(g))==k
            features.append(dict(opponents=opponents,raw=raw.tolist(),clipped=clipped.tolist()))
            labels.append(g.tolist())
        proposals[variant]=dict(source_bet=5 if variant=='half_witness' else 10,
            source_provenance=source_matrix.source_digest,bank=list(BANK),features=features,groups=labels)
    return proposals,half,half_matrix


def lp_target(matrix,solution):
    policy=[solution['seat0']['bet'],solution['seat1']['call']]
    full=matrix.evaluate(*policy)
    assert abs(full['exploitability']-float(Q(solution['minimum_exploitability']['upper_exact'])))<1e-10
    return dict(policy=policy,full=full)


def solve(matrix,groups,algorithm,floor):
    reduced=matrix.aggregate(groups)
    engine=CFR(reduced) if algorithm=='cfr' else RegretBR(matrix,groups)
    start=perf_counter()
    pause=0.
    records=[]
    for i in range(1,50001):
        engine.step()
        if i in CHECKPOINTS:
            now=perf_counter()
            raw=dict(kind='iterations',budget=i,iteration=i,policy=[p.tolist() for p in engine.average()],
                     active_seconds=now-start-pause)
            records.append(budget.score(matrix,reduced,groups,raw,floor))
            pause+=perf_counter()-now
    return records


def worker(plan,out):
    bindings(plan)
    tool=base.helpers()
    budget.conf.forbid_fit(tool)
    calls=trajectories=0
    original=opt.linprog
    def counted(*args,**kwargs):
        nonlocal calls
        calls+=1
        assert calls<=96
        return original(*args,**kwargs)
    opt.linprog=counted
    cache={}
    combinations=[(m,a) for m in METHODS for a in ('cfr','br')]
    for index,case in enumerate(plan['cases']):
        old,pot,matrix,groups=setup(case,tool,cache)
        offset=index%4
        order=combinations[offset:]+combinations[:offset]
        runs=[]
        targets={m:lp_target(matrix,pot['methods'][m]['solution']) for m in METHODS}
        for method,algorithm in order:
            floor=pot['methods'][method]['solution']['minimum_exploitability']
            records=solve(matrix,groups[method],algorithm,floor)
            if algorithm=='cfr':
                prior={p['iteration']:p for p in pot['methods'][method]['records']}
                for record in records[:2]:
                    assert record['policy']==prior[record['iteration']]['policy']
                    assert record['full']==prior[record['iteration']]['full']
            runs.append(dict(method=method,algorithm=algorithm,groups=[g.tolist() for g in groups[method]],
                             records=records))
            trajectories+=1
        oracle={}
        if case['texture']=='multiple-pairs-or-trips':
            proposals,_,_=oracle_groups(case,old,pot,matrix,groups)
            for variant,proposal in proposals.items():
                oracle[variant]=dict(proposal=proposal,solution=opt.solve_groups(matrix,proposal['groups']))
        write(out/(case['id']+'.json'),dict(case=case,runs=runs,targets=targets,
            floors={m:pot['methods'][m]['solution']['minimum_exploitability'] for m in METHODS},oracle=oracle))
        print(f'completed {index+1}/60',flush=True)
    assert (calls,trajectories)==(96,240)
    bindings(plan)
    write(out/'worker-complete.json',dict(complete=True,cases=60,new_lp_calls=96,
        trajectories=240,checkpoints=720,lp_targets=120,oracle_group_pairs=48,model_fits=0))


def mean(xs):return fsum(xs)/len(xs)


def differences(xs):
    return dict(delta=mean(xs),counts=dict(Counter('lower' if x < -1e-10 else
                'higher' if x > 1e-10 else 'overlapping' for x in xs)))


def solver_stats(rows,n):
    values={}
    gaps={}
    times={}
    for m in METHODS:
        for a in ('cfr','br'):
            records=[next(p for p in next(run for run in r['runs'] if run['method']==m and
                     run['algorithm']==a)['records'] if p['iteration']==n) for r in rows]
            key=m+':'+a
            values[key]=[p['full']['exploitability'] for p in records]
            gaps[key]=mean([p['above_floor'] for p in records])
            times[key]=mean([p['active_seconds'] for p in records])
    pairs={'learned_br_minus_cfr':('ordinary_preference:br','ordinary_preference:cfr'),
           'response_br_minus_cfr':('range_response:br','range_response:cfr'),
           'learned_minus_response_br':('ordinary_preference:br','range_response:br'),
           'learned_minus_response_cfr':('ordinary_preference:cfr','range_response:cfr')}
    return dict(means={k:mean(v) for k,v in values.items()},above_floor=gaps,mean_active_seconds=times,
        floors={m:base.average([r['floors'][m] for r in rows]) for m in METHODS},
        comparisons={k:differences([x-y for x,y in zip(values[a],values[b],strict=True)])
                     for k,(a,b) in pairs.items()})


def grouping_stats(rows):
    names=(*METHODS,*VARIANTS)
    def floor(r,m):return r['floors'][m] if m in METHODS else r['oracle'][m]['solution']['minimum_exploitability']
    comparisons={}
    for control in (*METHODS,'half_witness'):
        ds=[base.difference(floor(r,'pot_witness'),floor(r,control)) for r in rows]
        comparisons['pot_minus_'+control]=dict(**base.average(ds),
            counts=dict(Counter(d['classification'] for d in ds)))
    return dict(floors={m:base.average([floor(r,m) for r in rows]) for m in names},comparisons=comparisons)


def summary(rows):
    polarized=[r for r in rows if r['case']['regime']=='polarized']
    paired=[r for r in rows if r['case']['texture']=='multiple-pairs-or-trips']
    intersection=[r for r in paired if r['case']['regime']=='polarized']
    assert (len(rows),len(polarized),len(paired),len(intersection))==(60,48,24,12)
    panels={'polarized':polarized,'paired_trips':paired,'intersection':intersection}
    solvers={name:{str(n):solver_stats(rs,n) for n in CHECKPOINTS} for name,rs in panels.items()}
    boards={name:{str(b):solver_stats([r for r in rs if r['case']['board_index']==b],50000)
                  for b in sorted({r['case']['board_index'] for r in rs})} for name,rs in panels.items()}
    lobo={name:{str(b):solver_stats([r for r in rs if r['case']['board_index']!=b],50000)
                for b in sorted({r['case']['board_index'] for r in rs})} for name,rs in panels.items()}
    grouping=dict(overall=grouping_stats(paired),
        boards={str(b):grouping_stats([r for r in paired if r['case']['board_index']==b])
                for b in sorted({r['case']['board_index'] for r in paired})},
        regimes={name:grouping_stats([r for r in paired if r['case']['regime']==name])
                 for name in ('uniform','polarized')},
        leave_one_board_out={str(b):grouping_stats([r for r in paired if r['case']['board_index']!=b])
                            for b in sorted({r['case']['board_index'] for r in paired})})
    primary=solvers['polarized']['50000']['comparisons']
    repaired=all(Q(grouping['overall']['comparisons']['pot_minus_'+m]['upper_exact'])<0 for m in METHODS)
    return dict(solver_panels=solvers,solver_boards=boards,solver_leave_one_board_out=lobo,grouping=grouping,
        solver_gap_reduced=primary['learned_br_minus_cfr']['delta'] < -1e-10,
        solver_ranking_repaired=primary['learned_minus_response_br']['delta'] < -1e-10,
        oracle_representation_repaired=repaired,
        oracle_context_gain=Q(grouping['overall']['comparisons']['pot_minus_half_witness']['upper_exact'])<0)


def verify(plan,out):
    bindings(plan)
    tool=base.helpers()
    budget.no_learning(tool)
    cache={}
    rows=[]
    certs=policies=targets=0
    maximum=0.
    def scalar_check(matrix,policy,expected):
        nonlocal maximum
        actual=budget.scalar_evaluate(matrix,*policy)
        for k,v in actual.items():
            error=abs(v-expected[k])
            maximum=max(maximum,error)
            assert error<=1e-10,(k,error)
    for index,case in enumerate(plan['cases']):
        row=read(out/(case['id']+'.json'))
        assert row['case']==case and len(row['runs'])==4
        old,pot,matrix,groups=setup(case,tool,cache)
        for m in BANK:
            opt.verify_solution(matrix,groups[m],pot['methods'][m]['solution'])
            certs+=2
        expected=[(m,a) for m in METHODS for a in ('cfr','br')]
        offset=index%4
        assert [(r['method'],r['algorithm']) for r in row['runs']]==expected[offset:]+expected[:offset]
        for m in METHODS:
            assert row['floors'][m]==pot['methods'][m]['solution']['minimum_exploitability']
            assert row['targets'][m]==lp_target(matrix,pot['methods'][m]['solution'])
            scalar_check(matrix,row['targets'][m]['policy'],row['targets'][m]['full'])
            targets+=1
        for run in row['runs']:
            m,a=run['method'],run['algorithm']
            assert run['groups']==[g.tolist() for g in groups[m]]
            reduced=matrix.aggregate(groups[m])
            engine=CFR(reduced) if a=='cfr' else RegretBR(matrix,groups[m])
            assert [r['iteration'] for r in run['records']]==list(CHECKPOINTS)
            for record in run['records']:
                n=record['iteration']
                while engine.iteration<n:engine.step()
                assert [p.tolist() for p in engine.average()]==record['policy']
                assert record['kind']=='iterations' and record['budget']==n
                assert np.isfinite(record['active_seconds']) and record['active_seconds']>=0
                full_policy=[np.asarray(p)[g] for p,g in zip(record['policy'],groups[m],strict=True)]
                assert matrix.evaluate(*full_policy)==record['full']
                assert reduced.evaluate(*record['policy'])==record['restricted']
                scalar_check(matrix,full_policy,record['full'])
                floor=row['floors'][m]
                mid=float((Q(floor['lower_exact'])+Q(floor['upper_exact']))/2)
                assert record['grouping_floor']==mid
                assert record['above_floor']==record['full']['exploitability']-mid
                assert record['above_floor']>=-1e-8
                if a=='cfr' and n<=10000:
                    anchor=next(p for p in pot['methods'][m]['records'] if p['iteration']==n)
                    assert record['policy']==anchor['policy'] and record['full']==anchor['full']
                policies+=1
        if case['texture']=='multiple-pairs-or-trips':
            proposals,half,hm=oracle_groups(case,old,pot,matrix,groups)
            assert set(row['oracle'])==set(VARIANTS)
            for m in BANK:
                opt.verify_solution(hm,groups[m],half['methods'][m]['solution'])
                certs+=2
            for v in VARIANTS:
                assert row['oracle'][v]['proposal']==proposals[v]
                opt.verify_solution(matrix,proposals[v]['groups'],row['oracle'][v]['solution'])
                certs+=2
        else:assert row['oracle']=={}
        rows.append(row)
        print(f'verified {index+1}/60',flush=True)
    assert (certs,policies,targets)==(600,720,120)
    write(out/'summary.json',summary(rows))
    bindings(plan)
    write(out/'audit.json',dict(passed=True,certificates=certs,checkpoint_policies=policies,
        lp_policy_targets=targets,replayed_paired_iterations=12000000,
        maximum_scalar_discrepancy=maximum,parent_lp_calls=0,model_fits=0))
    spec=importlib.util.spec_from_file_location('summary_audit',HERE/'summary-audit.py')
    auditor=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(auditor)
    write(out/'summary-audit.json',auditor.audit(out))


def run(path,expected):
    assert digest(path)==expected
    plan=read(path)
    bindings(plan)
    out=Path(plan['output'])
    out.mkdir(parents=True,exist_ok=False)
    write(out/'plan.json',plan)
    write(out/'started.json',dict(plan_sha256=expected))
    start=perf_counter()
    try:
        for mode in ('worker','verify'):
            command=[sys.executable,'-B','-W','error::ResourceWarning',str(HERE/'experiment.py'),mode,str(path),expected]
            begin=perf_counter()
            with (out/(mode+'-stdout.txt')).open('xb') as stdout,(out/(mode+'-stderr.txt')).open('xb') as stderr:
                result=subprocess.run(command,cwd=ROOT,stdout=stdout,stderr=stderr,timeout=1200)
            write(out/(mode+'-receipt.json'),dict(command=command,exit=result.returncode,
                seconds=perf_counter()-begin,timeout_seconds=1200))
            assert result.returncode==0,mode+' failed'
        bindings(plan)
        write(out/'results-manifest.json',{p.name:digest(p) for p in sorted(out.iterdir()) if p.is_file()})
        write(out/'receipt.json',dict(exit=0,seconds=perf_counter()-start,
              result_manifest_sha256=digest(out/'results-manifest.json')))
        print(json.dumps(read(out/'audit.json'),indent=2))
    except BaseException as error:
        write(out/'failed.json',dict(error=type(error).__name__,message=str(error)))
        raise


if __name__=='__main__':
    if sys.argv[1]=='run':run(Path(sys.argv[2]),sys.argv[3])
    else:
        assert digest(sys.argv[2])==sys.argv[3]
        plan=read(sys.argv[2])
        {'worker':worker,'verify':verify}[sys.argv[1]](plan,Path(plan['output']))
