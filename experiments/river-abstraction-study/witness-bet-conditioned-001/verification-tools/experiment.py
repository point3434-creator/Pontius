"""Predeclared two-bet distillation, with disjoint fresh-board evaluation."""
from collections import Counter
from fractions import Fraction as Q
from hashlib import sha256
import json
from math import fsum
from pathlib import Path
import subprocess
import sys
from time import perf_counter
import tracemalloc
from bridge import ROOT,PRIOR,np,opt,base,budget,transfer,read,write,digest,pref,RegretBR,anchored_clusters,action_advantages
import model

HERE=Path(__file__).parent
SEED='witness-bet-conditioned-001'
BETS=(5,10)
BANK=('ordinary_preference','range_response','range_equity')
SOLVERS=('conditioned','blind','ordinary_preference','range_response')
METHODS=(*SOLVERS,'oracle_sign','oracle_clipped')
CHECKPOINTS=(1000,10000,50000)

def select(excluded,pilot):
    seen={pilot.canonical_board(b) for b in excluded}
    chosen={t:[] for t in pilot.TEXTURES}
    receipt=[]
    for attempt in range(10000):
        board=sorted(sorted(range(52),key=lambda c:(sha256(f'{SEED}|{attempt}|{c}'.encode()).digest(),c))[:5])
        key=pilot.canonical_board(board);t=pilot.texture(board)
        if key not in seen and len(chosen[t])<2:
            chosen[t].append(board);seen.add(key)
            receipt.append(dict(attempt=attempt,board=board,texture=t))
        if all(len(v)==2 for v in chosen.values()):
            return [b for t in pilot.TEXTURES for b in chosen[t]],receipt
    raise AssertionError('board selection limit')

def grid(boards,tool):return [c for c in tool.pilot.case_grid(boards) if c['pool']<2]

def bindings(plan):
    assert sys.version_info[:3]==(3,14,6) and np.__version__=='2.5.2'
    assert budget.conf.scipy.__version__=='1.18.0' and not tracemalloc.is_tracing()
    assert digest(__file__)==plan['script_sha256']
    for p,h in plan['pins'].items():assert digest(p)==h,p
    tool=base.helpers()
    boards,receipt=select(plan['excluded_boards'],tool.pilot)
    assert boards==plan['boards'] and receipt==plan['selection_receipt']
    assert grid(boards,tool)==plan['evaluation_cases']
    assert len(plan['training_cases'])==len(plan['evaluation_cases'])==32
    old=read(ROOT/'experiments/river-abstraction-study/witness-preference-001/plan.json')
    assert plan['training_cases']==[c for c in old['training_cases'] if c['pool']<2]
    assert not ({tool.pilot.canonical_board(c['board']) for c in plan['training_cases']}&
                {tool.pilot.canonical_board(c['board']) for c in plan['evaluation_cases']})

def setup(case,bet,tool,cache):
    equities=tool.old.equities_for(case,cache)
    reference,_,inputs=tool.pilot.build_inputs(case,96,equities)
    game,matrix=transfer.build(inputs,bet)
    transfer.validate_game(matrix,reference,inputs,bet)
    oldmodels=read(transfer.PRIOR/'candidate.json')['models']
    raw=[tool.student.raw_features(matrix,equities,s).tolist() for s in (0,1)]
    groups={m:[g.tolist() for g in budget.prepare(matrix,equities,oldmodels,m,tool)[0]] for m in BANK}
    assert all([len(set(g)) for g in groups[m]]==[len(set(g)) for g in groups[BANK[0]]] for m in BANK)
    return matrix,dict(case=case,bet=bet,inputs=inputs,provenance_digest=game.provenance_digest,
                       raw_features=raw,bank_groups=groups)

def witness(matrix,bank):
    rows=[]
    for seat in (0,1):
        opponents=[bank[m][f'seat{seat}']['call' if seat==0 else 'bet'] for m in BANK]
        advantages=action_advantages(matrix,opponents,seat)
        rows.append(dict(opponents=opponents,advantages=advantages.tolist(),
            target=pref.targets(advantages).tolist(),clipped=np.clip(advantages,-.5,.5).tolist(),
            weights=matrix.joint.sum(axis=1-seat).tolist()))
    return rows

def fit_models(rows):
    assert len(rows)==64
    models={m:[] for m in ('conditioned','blind')}
    for m in models:
        for seat in (0,1):
            x=np.vstack([model.design(r['raw_features'][seat],r['bet'],m=='conditioned') for r in rows])
            y=np.vstack([r['witness'][seat]['target'] for r in rows])
            weights=np.concatenate([np.asarray(r['witness'][seat]['weights'])/
                sum(r['witness'][seat]['weights'])/len(rows) for r in rows])
            models[m].append([model.fit(x,y[:,j],weights) for j in range(3)])
    return models

def proposal(core,witnesses,models):
    groups={m:core['bank_groups'][m] for m in SOLVERS if m in BANK}
    features={}
    for m in ('conditioned','blind','oracle_sign','oracle_clipped'):
        groups[m]=[];features[m]=[]
        for seat in (0,1):
            if m in models:
                x=model.design(core['raw_features'][seat],core['bet'],m=='conditioned')
                f=model.predict(models[m][seat],x)
            else:f=np.asarray(witnesses[seat]['target' if m=='oracle_sign' else 'clipped'])
            k=len(set(core['bank_groups'][BANK[0]][seat]))
            g=anchored_clusters(f,np.asarray(witnesses[seat]['weights']),k).tolist()
            assert len(set(g))==k
            groups[m].append(g);features[m].append(f.tolist())
    return dict(groups=groups,features=features)

def solve(matrix,groups,solution):
    groups=[np.asarray(g) for g in groups]
    engine=RegretBR(matrix,groups);reduced=matrix.aggregate(groups)
    start=perf_counter();pause=0.;records=[]
    for n in range(1,50001):
        engine.step()
        if n in CHECKPOINTS:
            now=perf_counter()
            r=dict(kind='iterations',budget=n,iteration=n,policy=[p.tolist() for p in engine.average()],
                   active_seconds=now-start-pause)
            records.append(budget.score(matrix,reduced,groups,r,solution['minimum_exploitability']))
            pause+=perf_counter()-now
    return records

def filename(split,case,bet):return f"{split}-{case['id']}-bet-{bet}.json"

def worker(plan,out):
    bindings(plan);tool=base.helpers();cache={};calls=0
    original=opt.linprog
    def counted(*args,**kwargs):
        nonlocal calls
        calls+=1;assert calls<=1280
        return original(*args,**kwargs)
    opt.linprog=counted
    training=[]
    for i,case in enumerate(plan['training_cases']):
        for bet in BETS:
            matrix,core=setup(case,bet,tool,cache)
            bank={m:opt.solve_groups(matrix,core['bank_groups'][m]) for m in BANK}
            row=dict(**core,bank=bank,witness=witness(matrix,bank))
            training.append(row);write(out/filename('train',case,bet),row)
        print(f'training cases {i+1}/32',flush=True)
    assert calls==384
    models=fit_models(training)
    candidate=dict(models=models,training_files={filename('train',c,b):digest(out/filename('train',c,b))
        for c in plan['training_cases'] for b in BETS},fit_tasks=12,
        schema='two-bet-preference-v1',outputs_per_seat=3,quadratic_columns=91)
    write(out/'candidate.json',candidate)
    candidate_sha=digest(out/'candidate.json')
    write(out/'model-frozen-before-evaluation.json',dict(candidate_sha256=candidate_sha,
        evaluation_files_present=any(out.glob('eval-*.json'))))
    def forbidden(*a,**kw):raise AssertionError('fitting after model freeze forbidden')
    model.fit=forbidden
    cache={}
    for i,case in enumerate(plan['evaluation_cases']):
        for bet in BETS:
            matrix,core=setup(case,bet,tool,cache)
            bank={m:opt.solve_groups(matrix,core['bank_groups'][m]) for m in BANK}
            ws=witness(matrix,bank);prop=proposal(core,ws,models)
            solutions={m:bank[m] if m in bank else opt.solve_groups(matrix,prop['groups'][m]) for m in METHODS}
            order=SOLVERS[i%4:]+SOLVERS[:i%4]
            records={m:solve(matrix,prop['groups'][m],solutions[m]) for m in order}
            row=dict(**core,bank=bank,witness=ws,proposal=prop,solutions=solutions,records=records,
                     candidate_sha256=candidate_sha,solver_order=list(order))
            write(out/filename('eval',case,bet),row)
        print(f'evaluation cases {i+1}/32',flush=True)
    assert calls==1280 and digest(out/'candidate.json')==candidate_sha
    bindings(plan)
    write(out/'worker-complete.json',dict(complete=True,training_cells=64,evaluation_cells=64,
        lp_calls=1280,fit_tasks=12,trajectories=256,checkpoint_policies=768))

def stats(rows,n=50000):
    avg=lambda xs:fsum(xs)/len(xs)
    actual={m:avg([next(p for p in r['records'][m] if p['iteration']==n)['full']['exploitability']
        for r in rows]) for m in SOLVERS}
    floors={m:base.average([r['solutions'][m]['minimum_exploitability'] for r in rows]) for m in METHODS}
    comparisons={}
    for m in METHODS[1:]:
        diffs=[base.difference(r['solutions']['conditioned']['minimum_exploitability'],
                              r['solutions'][m]['minimum_exploitability']) for r in rows]
        v=dict(floor=dict(**base.average(diffs),counts=dict(Counter(d['classification'] for d in diffs))))
        if m in SOLVERS:
            ds=[next(p for p in r['records']['conditioned'] if p['iteration']==n)['full']['exploitability']-
                next(p for p in r['records'][m] if p['iteration']==n)['full']['exploitability'] for r in rows]
            v['actual']=dict(delta=avg(ds),counts=dict(Counter('lower' if d < -1e-10 else
                'higher' if d > 1e-10 else 'overlapping' for d in ds)))
        comparisons[m]=v
    return dict(actual=actual,floors=floors,comparisons=comparisons)

def summarize(rows):
    panels={}
    for bet in BETS:
        rs=[r for r in rows if r['bet']==bet]
        panels[str(bet)]=dict(overall=stats(rs),checkpoints={str(n):stats(rs,n) for n in CHECKPOINTS},
            boards={str(b):stats([r for r in rs if r['case']['board_index']==b]) for b in range(8)},
            textures={t:stats([r for r in rs if r['case']['texture']==t]) for t in sorted({r['case']['texture'] for r in rs})},
            regimes={t:stats([r for r in rs if r['case']['regime']==t]) for t in ('uniform','polarized')},
            leave_one_board_out={str(b):stats([r for r in rs if r['case']['board_index']!=b]) for b in range(8)})
    pot=panels['10']['overall']['comparisons']
    flags=dict(conditioning_actual_gain=pot['blind']['actual']['delta'] < -1e-10,
        conditioning_floor_gain=Q(pot['blind']['floor']['upper_exact'])<0,
        beats_existing_actual=all(pot[m]['actual']['delta'] < -1e-10 for m in BANK[:2]),
        beats_existing_floor=all(Q(pot[m]['floor']['upper_exact'])<0 for m in BANK[:2]))
    flags['cross_bet_robustness']=all(v['comparisons'][m]['actual']['delta'] < -1e-10 and
        Q(v['comparisons'][m]['floor']['upper_exact'])<0 for panel in panels.values()
        for category in ('textures','regimes','leave_one_board_out') for v in panel[category].values()
        for m in ('blind','ordinary_preference','range_response'))
    return dict(panels=panels,flags=flags)

def verify(plan,out):
    bindings(plan);tool=base.helpers();cache={};certs=policies=0;maximum=0.
    def forbidden(*a,**kw):raise AssertionError('parent LP forbidden')
    opt.linprog=opt.solve_groups=forbidden
    training=[]
    for case in plan['training_cases']:
        for bet in BETS:
            row=read(out/filename('train',case,bet));matrix,core=setup(case,bet,tool,cache)
            assert all(row[k]==v for k,v in core.items())
            for m in BANK:
                opt.verify_solution(matrix,core['bank_groups'][m],row['bank'][m]);certs+=2
            assert row['witness']==witness(matrix,row['bank']);training.append(row)
    candidate=read(out/'candidate.json')
    assert candidate['training_files']=={filename('train',c,b):digest(out/filename('train',c,b))
        for c in plan['training_cases'] for b in BETS}
    for name,h in candidate['training_files'].items():assert digest(out/name)==h
    assert candidate['models']==fit_models(training)
    frozen=read(out/'model-frozen-before-evaluation.json')
    assert frozen==dict(candidate_sha256=digest(out/'candidate.json'),evaluation_files_present=False)
    model.fit=forbidden
    models=candidate['models'];cache={};rows=[]
    for i,case in enumerate(plan['evaluation_cases']):
        pair=[]
        for bet in BETS:
            row=read(out/filename('eval',case,bet));matrix,core=setup(case,bet,tool,cache)
            assert all(row[k]==v for k,v in core.items())
            assert row['candidate_sha256']==digest(out/'candidate.json')
            for m in BANK:
                opt.verify_solution(matrix,core['bank_groups'][m],row['bank'][m]);certs+=2
            ws=witness(matrix,row['bank']);assert row['witness']==ws
            prop=proposal(core,ws,models);assert row['proposal']==prop
            for m in METHODS:
                if m in BANK:assert row['solutions'][m]==row['bank'][m]
                else:
                    opt.verify_solution(matrix,prop['groups'][m],row['solutions'][m]);certs+=2
            assert row['solver_order']==list(SOLVERS[i%4:]+SOLVERS[:i%4])
            for m in SOLVERS:
                g=[np.asarray(v) for v in prop['groups'][m]]
                engine=RegretBR(matrix,g);reduced=matrix.aggregate(g)
                assert [p['iteration'] for p in row['records'][m]]==list(CHECKPOINTS)
                for p in row['records'][m]:
                    while engine.iteration<p['iteration']:engine.step()
                    assert [v.tolist() for v in engine.average()]==p['policy']
                    scored=budget.score(matrix,reduced,g,{k:p[k] for k in
                        ('kind','budget','iteration','policy','active_seconds')},row['solutions'][m]['minimum_exploitability'])
                    assert scored==p and p['above_floor']>=-1e-8
                    assert p['budget']==p['iteration'] and p['kind']=='iterations'
                    assert np.isfinite(p['active_seconds']) and p['active_seconds']>=0
                    scalar=budget.scalar_evaluate(matrix,*[np.asarray(v)[gs] for v,gs in zip(p['policy'],g,strict=True)])
                    for k,v in scalar.items():
                        error=abs(v-p['full'][k]);maximum=max(maximum,error);assert error<1e-10
                    policies+=1
            rows.append(row);pair.append(row)
        assert pair[0]['raw_features']==pair[1]['raw_features']
        assert pair[0]['proposal']['features']['blind']==pair[1]['proposal']['features']['blind']
        assert pair[0]['proposal']['groups']['blind']==pair[1]['proposal']['groups']['blind']
        print(f'verified evaluation {i+1}/32',flush=True)
    assert (certs,policies)==(1280,768)
    write(out/'summary.json',summarize(rows))
    bindings(plan)
    write(out/'audit.json',dict(passed=True,certificates=certs,checkpoint_policies=policies,
        replayed_iterations=12800000,fit_tasks_reproduced=12,maximum_scalar_discrepancy=maximum,
        parent_lp_calls=0,training_evaluation_disjoint=True))
    from audit import audit
    write(out/'summary-audit.json',audit(out))

def run(path,expected):
    assert digest(path)==expected
    plan=read(path);bindings(plan)
    out=Path(plan['output']);out.mkdir(parents=True,exist_ok=False)
    write(out/'plan.json',plan);write(out/'started.json',dict(plan_sha256=expected))
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
        write(out/'failed.json',dict(error=type(error).__name__,message=str(error)));raise

if __name__=='__main__':
    if sys.argv[1]=='run':run(Path(sys.argv[2]),sys.argv[3])
    else:
        assert digest(sys.argv[2])==sys.argv[3]
        p=read(sys.argv[2]);{'worker':worker,'verify':verify}[sys.argv[1]](p,Path(p['output']))
