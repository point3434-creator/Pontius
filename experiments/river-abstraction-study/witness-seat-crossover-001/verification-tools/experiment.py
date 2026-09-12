"""Cross frozen seat groupings; reconstruct certificates without fitting or LP calls."""
from collections import Counter
from fractions import Fraction as Q
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from time import perf_counter

ROOT=Path('D:/Pontius-worktrees/eval-runner-consolidation')
HERE=Path(__file__).parent
for key in ('OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','OMP_NUM_THREADS'):
    os.environ[key]='1'
sys.path.insert(0,str(ROOT/'src'))
import numpy as np
import scipy
import scipy.optimize
import pontius.river_group_optimality as opt

read=lambda p:json.loads(Path(p).read_bytes())
digest=lambda p:sha256(Path(p).read_bytes()).hexdigest()
B=lambda x:(Q(x['lower_exact']),Q(x['upper_exact']))
ARMS={'old_old':('old','old'),'new_old':('new','old'),
      'old_new':('old','new'),'new_new':('new','new')}
EFFECTS=('bettor','caller','both')
REFERENCES=('old_old','range_response','range_equity','clipped_oracle')

def write(p,x):
    with Path(p).open('x',encoding='utf-8',newline='\n') as f:
        f.write(json.dumps(x,sort_keys=True,indent=2,allow_nan=False)+'\n')

def iv(lo,hi):
    assert lo<=hi
    return {'lower_exact':str(lo),'upper_exact':str(hi),
            'lower_chips_approx':float(lo),'upper_chips_approx':float(hi)}

def signed(lo,hi):
    return dict(**iv(lo,hi),classification='lower' if hi<0 else 'higher' if lo>0 else 'overlapping')

def delta(x,y):
    a,b=B(x);c,d=B(y)
    return signed(a-d,b-c)

def floor(a,b):
    la,ua=B(a);lb,ub=B(b)
    return iv(max(Q(0),(lb-ua)/2),(ub-la)/2)

def effects(values):
    oa,na=B(values['old'][0]),B(values['new'][0])
    ob,nb=B(values['old'][1]),B(values['new'][1])
    d0=((oa[0]-na[1])/2,(oa[1]-na[0])/2)
    d1=((nb[0]-ob[1])/2,(nb[1]-ob[0])/2)
    return dict(bettor=signed(*d0),caller=signed(*d1),
                both=signed(d0[0]+d1[0],d0[1]+d1[1]))

def mean(values):
    assert values
    return iv(*(sum(B(v)[i] for v in values)/len(values) for i in (0,1)))

def stats(values):
    return dict(**mean(values),counts=dict(Counter(v['classification'] for v in values)))

def aggregate(rows):
    return dict(cases=len(rows),
        floors={arm:mean([r['floors'][arm] for r in rows]) for arm in rows[0]['floors']},
        effects={e:stats([r['effects'][e] for r in rows]) for e in EFFECTS},
        comparisons={arm:{ref:stats([r['comparisons'][arm][ref] for r in rows])
                     for ref in REFERENCES} for arm in ARMS})

def summary(rows):
    boards=sorted({r['case']['board_index'] for r in rows})
    return dict(overall=aggregate(rows),
        boards={str(b):aggregate([r for r in rows if r['case']['board_index']==b]) for b in boards},
        board_pools={f'{b}-{p}':aggregate([r for r in rows if
            r['case']['board_index']==b and r['case']['pool']==p]) for b in boards for p in range(3)},
        regimes={v:aggregate([r for r in rows if r['case']['regime']==v])
                 for v in ('uniform','polarized')},
        textures={v:aggregate([r for r in rows if r['case']['texture']==v])
                  for v in sorted({r['case']['texture'] for r in rows})},
        leave_one_board_out={str(b):aggregate([r for r in rows if r['case']['board_index']!=b])
                             for b in boards})

def bindings(plan):
    assert sys.version_info[:3]==(3,14,6)
    assert np.__version__=='2.5.2' and scipy.__version__=='1.18.0'
    assert digest(__file__)==plan['script_sha256']
    for path,h in plan['pins'].items(): assert digest(path)==h,path

def helpers():
    spec=importlib.util.spec_from_file_location('distill',ROOT/'tools/river_witness_distillation.py')
    tool=importlib.util.module_from_spec(spec);spec.loader.exec_module(tool)
    return tool

def self_test():
    v={'old':[iv(Q(-2),Q(-2)),iv(Q(6),Q(6))],
       'new':[iv(Q(0),Q(0)),iv(Q(2),Q(2))]}
    assert [B(floor(v[x][0],v[y][1])) for x,y in ARMS.values()]==[
        (Q(4),Q(4)),(Q(3),Q(3)),(Q(2),Q(2)),(Q(1),Q(1))]
    e=effects(v)
    assert [B(e[k]) for k in EFFECTS]==[(Q(-1),Q(-1)),(Q(-2),Q(-2)),(Q(-3),Q(-3))]
    assert all(e[k]['classification']=='lower' for k in EFFECTS)
    v['new'][0]=iv(Q(-4),Q(-4))
    assert B(effects(v)['bettor'])==(Q(1),Q(1))
    assert effects(v)['bettor']['classification']=='higher'
    v['new']=v['old']
    assert B(effects(v)['both'])==(Q(0),Q(0))
    # A shared caller value cancels even if its certificate is wide.
    v={'old':[iv(Q(-2),Q(-2)),iv(Q(5),Q(6))],
       'new':[iv(Q(0),Q(0)),iv(Q(2),Q(2))]}
    assert B(effects(v)['bettor'])==(Q(-1),Q(-1))
    assert B(delta(floor(v['new'][0],v['old'][1]),floor(*v['old'])))!=B(effects(v)['bettor'])
    for p,g in [([.1,.2],[0,0]),([False,0],[0,1]),([1.1,0],[0,1])]:
        try:opt.policy(p,g)
        except ValueError:pass
        else:raise AssertionError('invalid policy accepted')
    assert len(opt.policy([.5,.5],[0,0]))==2
    print('PASS: analytic four-arm floors, signed seat effects, shared-value cancellation and refusals.')

def record(plan,tool,case,cache):
    old=read(Path(plan['old'])/(case['id']+'.json'))
    new=read(Path(plan['new'])/(case['id']+'.json'))
    teacher=read(Path(plan['evaluation'])/(case['id']+'.json'))['teacher']
    assert old['case']==new['case']==teacher['case']==case
    equities=tool.old.equities_for(case,cache)
    matrix,controls,rebuilt=tool.pilot.build_inputs(case,96,equities)
    assert tool.pilot.canonical_json(rebuilt)==tool.pilot.canonical_json(teacher['inputs'])
    groups={'old':old['groups']['clipped_prediction'],'new':new['groups']['clipped_target_model']}
    solutions={'old':old['solutions']['clipped_prediction'],
               'new':new['solutions']['clipped_target_model']}
    capacity=[len(set(g)) for g in controls['uniform_equity_200']]
    for kind in ('old','new'):
        assert [len(set(g)) for g in groups[kind]]==capacity
        opt.verify_solution(matrix,groups[kind],solutions[kind])
    values={kind:[solutions[kind][f'seat{s}']['value'] for s in (0,1)] for kind in ('old','new')}
    floors={arm:floor(values[x][0],values[y][1]) for arm,(x,y) in ARMS.items()}
    assert floors['old_old']==old['floors']['clipped_prediction']
    assert floors['new_new']==new['floors']['clipped_target_model']
    for ref in REFERENCES[1:]:
        assert old['floors'][ref]==new['floors'][ref]
        floors[ref]=old['floors'][ref]
    profiles={}
    for arm,(x,y) in ARMS.items():
        # These are the constrained policies, not the unrestricted response witnesses.
        bet=solutions[x]['seat0']['bet'];call=solutions[y]['seat1']['call']
        opt.policy(bet,groups[x][0]);opt.policy(call,groups[y][1])
        profiles[arm]=dict(groups=[groups[x][0],groups[y][1]],bet=bet,call=call,
                          source_seats=[x,y])
    mass=[]
    for seat in (0,1):
        hands=rebuilt['hands'][seat]
        raw={tuple(h):w for h,w in rebuilt['ranges'][seat]}
        bands=['low' if equities[tuple(h)]<=.2 else 'high' if equities[tuple(h)]>=.8
               else 'middle' for h in hands]
        weights=[raw[tuple(h)] for h in hands]
        marginal=matrix.joint.sum(axis=1-seat).tolist()
        assert all(w==(4 if case['regime']=='polarized' and b!='middle' else 1)
                   for w,b in zip(weights,bands,strict=True))
        mass.append(dict(hands=hands,bands=bands,raw_weights=weights,marginal=marginal,
            counts={b:bands.count(b) for b in ('low','middle','high')},
            prior={b:sum(w for w,t in zip(weights,bands) if t==b)/sum(weights)
                   for b in ('low','middle','high')},
            conditioned={b:sum(w for w,t in zip(marginal,bands) if t==b)/sum(marginal)
                         for b in ('low','middle','high')}))
    return dict(case=case,capacity=capacity,values=values,profiles=profiles,floors=floors,
        effects=effects(values),comparisons={arm:{ref:(signed(Q(0),Q(0)) if arm==ref else
             delta(floors[arm],floors[ref])) for ref in REFERENCES} for arm in ARMS},
        range_mass=mass,input_sha256=sha256(tool.pilot.canonical_json(rebuilt).encode()).hexdigest())

def paired(rows):
    pairs=[]
    for b in range(8):
        for p in range(3):
            selected={r['case']['regime']:r for r in rows if
                      r['case']['board_index']==b and r['case']['pool']==p}
            u,z=selected['uniform'],selected['polarized']
            assert u['case']['board']==z['case']['board']
            assert all(u['range_mass'][s]['hands']==z['range_mass'][s]['hands'] for s in (0,1))
            pairs.append(dict(board_index=b,pool=p,
                effects={e:delta(z['effects'][e],u['effects'][e]) for e in EFFECTS}))
    def agg(selected):return {e:stats([r['effects'][e] for r in selected]) for e in EFFECTS}
    return dict(pairs=pairs,overall=agg(pairs),
        boards={str(b):agg([r for r in pairs if r['board_index']==b]) for b in range(8)},
        leave_one_board_out={str(b):agg([r for r in pairs if r['board_index']!=b]) for b in range(8)})

def worker(plan):
    bindings(plan);tool=helpers();attempts={'lp':0,'fit':0}
    def forbidden(kind):
        def fail(*a,**kw):
            attempts[kind]+=1
            raise RuntimeError('new '+kind+' call forbidden')
        return fail
    scipy.optimize.linprog=opt.linprog=forbidden('lp')
    opt.solve_groups=opt.solve_seat=forbidden('lp')
    tool.student.fit_model=tool.student.fit_models=np.linalg.solve=forbidden('fit')
    cache={};rows=[];out=Path(plan['output'])
    for case in plan['cases']:
        r=record(plan,tool,case,cache);write(out/(case['id']+'.json'),r);rows.append(r)
    assert attempts=={'lp':0,'fit':0}
    assert [r['case'] for r in rows]==plan['cases'] and len(rows)==48
    result=summary(rows);result['paired_regime_effects']=paired(rows)
    write(out/'summary.json',result)
    bindings(plan)
    write(out/'worker-complete.json',dict(complete=True,cases=48,
          fresh_asymmetric_certificates=192,arms_per_case=4,attempts=attempts))

def run(path,expected):
    assert digest(path)==expected
    plan=read(path);bindings(plan)
    out=Path(plan['output']);out.mkdir(parents=True,exist_ok=False)
    start=perf_counter()
    try:
        write(out/'plan.json',plan)
        command=[sys.executable,'-B','-W','error::ResourceWarning',str(Path(__file__).resolve()),
                 'worker',str(path),expected]
        write(out/'started.json',dict(command=command,plan_sha256=expected))
        try:
            child=subprocess.run(command,cwd=ROOT,capture_output=True,timeout=600)
        except subprocess.TimeoutExpired as e:
            (out/'stdout.txt').write_bytes(e.stdout or b'');(out/'stderr.txt').write_bytes(e.stderr or b'')
            raise
        (out/'stdout.txt').write_bytes(child.stdout);(out/'stderr.txt').write_bytes(child.stderr)
        write(out/'worker-receipt.json',dict(exit=child.returncode,seconds=perf_counter()-start))
        assert child.returncode==0,'worker failed'
        spec=importlib.util.spec_from_file_location('crossover_audit',HERE/'audit.py')
        auditor=importlib.util.module_from_spec(spec);spec.loader.exec_module(auditor)
        audit=auditor.audit(out);write(out/'audit.json',audit)
        bindings(plan)
        write(out/'results-manifest.json',{p.name:digest(p) for p in sorted(out.iterdir()) if p.is_file()})
        write(out/'receipt.json',dict(exit=0,seconds=perf_counter()-start,
              result_manifest_sha256=digest(out/'results-manifest.json')))
        print(json.dumps(audit,indent=2))
        print('Completed; summary retained at '+str(out/'summary.json'))
    except BaseException as e:
        write(out/'failed.json',dict(complete=False,error=type(e).__name__,message=str(e)))
        raise

if __name__=='__main__':
    if sys.argv[1]=='self-test':self_test()
    elif sys.argv[1]=='worker':
        assert digest(sys.argv[2])==sys.argv[3];worker(read(sys.argv[2]))
    elif sys.argv[1]=='run':run(Path(sys.argv[2]),sys.argv[3])
    else:raise ValueError('unknown operation')
