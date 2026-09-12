"""No-fit transfer of frozen groups across three public one-bet river games."""
from collections import Counter
from fractions import Fraction as Q
import importlib.util
import json
from math import fsum
from pathlib import Path
import subprocess
import sys
from time import perf_counter
import tracemalloc

ROOT=Path('D:/Pontius-worktrees/eval-runner-consolidation')
HERE=Path(__file__).parent
BUDGET=ROOT/'experiments/river-abstraction-study/witness-solver-budget-001'
spec=importlib.util.spec_from_file_location('budget',BUDGET/'verification-tools/experiment.py')
budget=importlib.util.module_from_spec(spec)
spec.loader.exec_module(budget)
np,opt,pref,base=budget.np,budget.opt,budget.pref,budget.base
read,write,digest=base.read,base.write,base.digest
PRIOR=budget.PRIOR
METHODS=budget.METHODS
BETS=(2.5,5.,10.)
from pontius.river import RiverHoldem, evaluate_seven
from pontius.river_abstraction_study import CFR, PayoffGame


def bindings(plan):
    assert sys.version_info[:3]==(3,14,6)
    assert np.__version__=='2.5.2' and budget.conf.scipy.__version__=='1.18.0'
    assert not tracemalloc.is_tracing()
    assert digest(__file__)==plan['script_sha256']
    for path,h in plan['pins'].items():assert digest(path)==h,path
    assert plan['cases']==read(PRIOR/'plan.json')['cases'] and len(plan['cases'])==96


def build(inputs,bet):
    ranges=[{tuple(h):w for h,w in rs} for rs in inputs['ranges']]
    game=RiverHoldem.from_independent_ranges(board=inputs['board'],pot=10,stacks=(20,20),
        bet_size=bet,player0_weights=ranges[0],player1_weights=ranges[1])
    return game,PayoffGame.from_river(game)


def validate_game(matrix,reference,inputs,bet):
    assert matrix.hands==reference.hands
    assert np.array_equal(matrix.joint,reference.joint)
    assert np.array_equal(matrix.check,reference.check)
    assert np.array_equal(matrix.fold,reference.fold)
    expected=np.sign(reference.check)*matrix.joint*(5+bet)
    assert np.array_equal(matrix.call,expected)
    assert matrix.joint.tolist()==inputs['joint']
    assert [list(map(list,hs)) for hs in matrix.hands]==inputs['hands']


def feature_identity(matrix,equities,tool,models,prior):
    for seat in (0,1):
        raw=tool.student.raw_features(matrix,equities,seat)
        assert raw.tolist()==prior['raw_features'][seat]
        predicted=pref.predict(models[seat],tool.student.design(raw))
        assert predicted.tolist()==prior['candidate_features'][seat]


def original_records(case,method):
    row=read(BUDGET/(case['id']+'.json'))
    run=next(r for r in row['runs'] if r['phase']==0 and r['method']==method)
    return run['records']


def record(matrix,reduced,groups,policies,solution,anchor):
    floor=solution['minimum_exploitability']
    saved=[]
    for policy in policies:
        minimal={k:policy[k] for k in ('kind','budget','iteration','policy','active_seconds')}
        saved.append(budget.score(matrix,reduced,groups,minimal,floor))
    x,y=(np.asarray(v) for v in anchor['policy'])
    fixed=matrix.evaluate(x[groups[0]],y[groups[1]])
    final=saved[-1]
    action_change=[float(matrix.joint.sum(axis=1-seat) @ np.abs(
        np.asarray(final['policy'][seat])[groups[seat]]-
        np.asarray(anchor['policy'][seat])[groups[seat]])) for seat in (0,1)]
    return dict(solution=solution,records=saved,half_pot_policy=anchor['policy'],
        half_pot_policy_evaluation=fixed,
        resolved_minus_fixed=final['full']['exploitability']-fixed['exploitability'],
        action_change=action_change)


def comparisons(methods):
    floors={m:methods[m]['solution']['minimum_exploitability'] for m in METHODS}
    return {m:dict(floor=base.difference(floors[METHODS[0]],floors[m]),
                   actual=methods[METHODS[0]]['records'][-1]['full']['exploitability']-
                          methods[m]['records'][-1]['full']['exploitability']) for m in METHODS[1:]}


def worker(plan,out):
    bindings(plan)
    tool=base.helpers()
    budget.conf.forbid_fit(tool)
    models=read(PRIOR/'candidate.json')['models']
    calls=trajectories=0
    original=opt.linprog
    def counted(*args,**kwargs):
        nonlocal calls
        calls+=1
        assert calls<=1152
        return original(*args,**kwargs)
    opt.linprog=counted
    cache={}
    for index,case in enumerate(plan['cases']):
        prior=read(PRIOR/(case['id']+'.json'))
        equities=tool.old.equities_for(case,cache)
        refgame,reference=build(prior['inputs'],5.)
        assert refgame.provenance_digest==prior['inputs']['provenance_digest']
        for bindex,bet in enumerate(BETS):
            start=perf_counter()
            game,matrix=build(prior['inputs'],bet)
            validate_game(matrix,reference,prior['inputs'],bet)
            feature_identity(matrix,equities,tool,models,prior)
            preparation=perf_counter()-start
            offset=(index+bindex)%3
            order=METHODS[offset:]+METHODS[:offset]
            methods={}
            for method in order:
                start=perf_counter()
                groups,reduced,solver=budget.prepare(matrix,equities,models,method,tool)
                assert [g.tolist() for g in groups]==prior['groups'][method]
                groups_seconds=perf_counter()-start
                start=perf_counter()
                solution=prior['solutions'][method] if bet==5 else opt.solve_groups(matrix,groups)
                certificate_seconds=perf_counter()-start
                original_policies=original_records(case,method)
                if bet==5:
                    policies=original_policies
                else:
                    policies=budget.fixed(solver)
                    trajectories+=1
                methods[method]=dict(groups=[g.tolist() for g in groups],
                    source='retained-half-pot' if bet==5 else 'new-solve',
                    setup_seconds=groups_seconds,certificate_seconds=certificate_seconds,
                    **record(matrix,reduced,groups,policies,solution,original_policies[-1]))
            write(out/(case['id']+f'-bet-{bet:g}.json'),dict(case=case,bet=bet,
                provenance_digest=game.provenance_digest,preparation_seconds=preparation,
                method_order=list(order),methods=methods,comparisons=comparisons(methods)))
        print(f'completed {index+1}/96, three bet sizes',flush=True)
    assert (calls,trajectories)==(1152,576)
    bindings(plan)
    write(out/'worker-complete.json',dict(complete=True,case_bet_cells=288,
        new_lp_calls=calls,new_cfr_trajectories=trajectories,new_policy_checkpoints=1728,
        reused_policy_checkpoints=864,model_fits=0))


def avg(xs):
    return fsum(xs)/len(xs)


def stats(rows,iteration=10000):
    def rec(r,m):return next(x for x in r['methods'][m]['records'] if x['iteration']==iteration)
    means={m:avg([rec(r,m)['full']['exploitability'] for r in rows]) for m in METHODS}
    floor={m:base.average([r['methods'][m]['solution']['minimum_exploitability'] for r in rows])
           for m in METHODS}
    comps={}
    for m in METHODS[1:]:
        ds=[rec(r,METHODS[0])['full']['exploitability']-rec(r,m)['full']['exploitability'] for r in rows]
        fs=[r['comparisons'][m]['floor'] for r in rows]
        comps[m]=dict(actual=dict(delta=avg(ds),counts=dict(Counter(
            'lower' if d < -1e-10 else 'higher' if d > 1e-10 else 'overlapping' for d in ds))),
            floor=dict(**base.average(fs),counts=dict(Counter(v['classification'] for v in fs))))
    return dict(means=means,floors=floor,comparisons=comps,
        above_floor={m:avg([rec(r,m)['above_floor'] for r in rows]) for m in METHODS},
        restricted={m:avg([rec(r,m)['restricted']['exploitability'] for r in rows]) for m in METHODS},
        fixed_policy={m:avg([r['methods'][m]['half_pot_policy_evaluation']['exploitability'] for r in rows])
                      for m in METHODS},
        resolved_minus_fixed={m:avg([r['methods'][m]['resolved_minus_fixed'] for r in rows]) for m in METHODS},
        action_change={m:[avg([r['methods'][m]['action_change'][seat] for r in rows]) for seat in (0,1)]
                       for m in METHODS})


def summary(rows):
    assert len(rows)==288
    panels={}
    for bet in BETS:
        rs=[r for r in rows if r['bet']==bet]
        assert len(rs)==96
        panels[str(bet)]=dict(overall=stats(rs),
            iterations={str(i):{k:v for k,v in stats(rs,i).items() if k in
                ('means','floors','comparisons','above_floor','restricted')} for i in (100,1000)},
            boards={str(b):stats([r for r in rs if r['case']['board_index']==b]) for b in range(16)},
            textures={t:stats([r for r in rs if r['case']['texture']==t])
                      for t in sorted({r['case']['texture'] for r in rs})},
            regimes={t:stats([r for r in rs if r['case']['regime']==t]) for t in ('uniform','polarized')},
            leave_one_board_out={str(b):stats([r for r in rs if r['case']['board_index']!=b])
                                for b in range(16)})
    actual=lambda s:s['comparisons']['range_response']['actual']['delta'] < -1e-10
    floor=lambda s:Q(s['comparisons']['range_response']['floor']['upper_exact'])<0
    news=[panels[k] for k in ('2.5','10.0')]
    anchors=panels['5.0']['overall']['comparisons']
    interactions={k:{m:dict(actual=panels[k]['overall']['comparisons'][m]['actual']['delta']-
        anchors[m]['actual']['delta'],floor=base.difference(panels[k]['overall']['comparisons'][m]['floor'],
        anchors[m]['floor'])) for m in METHODS[1:]} for k in ('2.5','10.0')}
    return dict(panels=panels,interactions_vs_half_pot=interactions,
        actual_policy_transfer_pass=all(actual(p['overall']) for p in news),
        representation_transfer_pass=all(floor(p['overall']) for p in news),
        robustness_pass=all(actual(s) and floor(s) for p in news for name in
            ('textures','regimes','leave_one_board_out') for s in p[name].values()))


def verify(plan,out):
    bindings(plan)
    tool=base.helpers()
    budget.no_learning(tool)
    models=read(PRIOR/'candidate.json')['models']
    rows=[]
    cache={}
    certs=policies=fixed_controls=feature_values=0
    max_error=0.
    for index,case in enumerate(plan['cases']):
        prior=read(PRIOR/(case['id']+'.json'))
        equities=tool.old.equities_for(case,cache)
        game,reference=build(prior['inputs'],5.)
        assert game.provenance_digest==prior['inputs']['provenance_digest']
        for bindex,bet in enumerate(BETS):
            row=read(out/(case['id']+f'-bet-{bet:g}.json'))
            game,matrix=build(prior['inputs'],bet)
            assert row['case']==case and row['bet']==bet
            assert row['provenance_digest']==game.provenance_digest
            validate_game(matrix,reference,prior['inputs'],bet)
            feature_identity(matrix,equities,tool,models,prior)
            feature_values+=96*2*15
            offset=(index+bindex)%3
            assert row['method_order']==list(METHODS[offset:]+METHODS[:offset])
            assert set(row['methods'])==set(METHODS)
            for method in METHODS:
                data=row['methods'][method]
                groups,reduced,solver=budget.prepare(matrix,equities,models,method,tool)
                assert [g.tolist() for g in groups]==data['groups']==prior['groups'][method]
                opt.verify_solution(matrix,groups,data['solution'])
                certs+=2
                assert data['source']==('retained-half-pot' if bet==5 else 'new-solve')
                original=original_records(case,method)
                if bet==5:
                    assert data['solution']==prior['solutions'][method]
                    assert data['records']==original
                assert [p['iteration'] for p in data['records']]==[100,1000,10000]
                for rec in data['records']:
                    while solver.iteration<rec['iteration']:solver.step()
                    assert rec['policy']==budget.snapshot(solver.sums,solver.iteration)
                    assert rec['kind']=='iterations' and rec['budget']==rec['iteration']
                    x,y=(np.asarray(v) for v in rec['policy'])
                    full=matrix.evaluate(x[groups[0]],y[groups[1]])
                    assert full==rec['full'] and reduced.evaluate(x,y)==rec['restricted']
                    scalar=budget.scalar_evaluate(matrix,x[groups[0]],y[groups[1]])
                    for k,value in scalar.items():
                        error=abs(value-full[k])
                        max_error=max(max_error,error)
                        assert error<=1e-10
                    assert abs(full['value']-rec['restricted']['value'])<1e-10
                    assert full['upper']+1e-10>=rec['restricted']['upper']
                    assert full['lower']<=rec['restricted']['lower']+1e-10
                    floor=data['solution']['minimum_exploitability']
                    midpoint=float((Q(floor['lower_exact'])+Q(floor['upper_exact']))/2)
                    assert rec['grouping_floor']==midpoint
                    assert rec['above_floor']==full['exploitability']-midpoint
                    assert rec['above_floor']>=-1e-8
                    policies+=1
                assert data['half_pot_policy']==original[-1]['policy']
                x,y=(np.asarray(v) for v in data['half_pot_policy'])
                scalar=budget.scalar_evaluate(matrix,x[groups[0]],y[groups[1]])
                for k,value in scalar.items():
                    error=abs(value-data['half_pot_policy_evaluation'][k])
                    max_error=max(max_error,error)
                    assert error<=1e-10
                expected=record(matrix,reduced,groups,data['records'],data['solution'],original[-1])
                for key,value in expected.items():assert data[key]==value,key
                fixed_controls+=1
            assert row['comparisons']==comparisons(row['methods'])
            rows.append(row)
        print(f'verified {index+1}/96, three bet sizes',flush=True)
    assert (certs,policies,fixed_controls)==(1728,2592,864)
    write(out/'summary.json',summary(rows))
    bindings(plan)
    write(out/'audit.json',dict(passed=True,asymmetric_certificates=certs,
        resolved_policies=policies,fixed_policy_controls=fixed_controls,
        unchanged_feature_values=feature_values,replayed_iterations=8640000,
        maximum_scalar_discrepancy=max_error,lp_calls=0,model_fits=0))
    spec=importlib.util.spec_from_file_location('audit',HERE/'summary-audit.py')
    auditor=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(auditor)
    write(out/'summary-audit.json',auditor.audit(out))


def self_test():
    from pontius.river import make_hole,parse_cards
    from pontius.evaluation import evaluate_profile
    ins=dict(board=list(parse_cards('2c','7d','9h','Js','Qc')),
        ranges=[[[list(make_hole('Ts','Ks')),2],[list(make_hole('Ah','3h')),1]],
                [[list(make_hole('Ac','Ad')),3],[list(make_hole('4s','5s')),1]]])
    matrices=[]
    for bet in BETS:
        game,matrix=build(ins,bet)
        x,y=np.array([.2,.8]),np.array([.3,.7])
        exact=evaluate_profile(game,matrix.lift_policy(game,x,y))
        value=matrix.evaluate(x,y)
        assert abs(value['value']-exact.utilities[0])<1e-12
        assert abs(value['upper']-exact.best_response_values[0])<1e-12
        assert abs(value['lower']+exact.best_response_values[1])<1e-12
        assert abs(value['exploitability']-exact.exploitability)<1e-12
        for i,h in enumerate(matrix.hands[0]):
            for j,o in enumerate(matrix.hands[1]):
                a,b=evaluate_seven((*game.board,*h)),evaluate_seven((*game.board,*o))
                assert matrix.call[i,j]==matrix.joint[i,j]*((a>b)-(a<b))*(5+bet)
        matrices.append(matrix)
    tool=base.helpers()
    equities={h:(i+1)/5 for i,h in enumerate(sorted(set(matrices[0].hands[0]+matrices[0].hands[1])))}
    for matrix in matrices[1:]:
        for key in ('joint','check','fold'):
            assert np.array_equal(getattr(matrix,key),getattr(matrices[0],key))
        for seat in (0,1):
            assert np.array_equal(tool.student.raw_features(matrix,equities,seat),
                                  tool.student.raw_features(matrices[0],equities,seat))
    ins['board']=list(parse_cards('Tc','Jc','Qc','Kc','Ac'))
    ins['ranges']=[[[list(make_hole('2h','3h')),1]],[[list(make_hole('4s','5s')),1]]]
    for bet in BETS:
        _,m=build(ins,bet)
        assert m.check[0,0]==m.call[0,0]==0 and m.fold[0,0]==5
    for bad in (0.,-1.,21.,float('nan')):
        try:build(ins,bad)
        except ValueError:pass
        else:raise AssertionError('invalid bet accepted')
    print('PASS: three sizes versus tree BR; exact stakes; feature invariance; ties; invalid bets.')


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
            command=[sys.executable,'-B','-W','error::ResourceWarning',str(HERE/'experiment.py'),
                     mode,str(path),expected]
            begin=perf_counter()
            with (out/(mode+'-stdout.txt')).open('xb') as stdout,(out/(mode+'-stderr.txt')).open('xb') as stderr:
                result=subprocess.run(command,cwd=ROOT,stdout=stdout,stderr=stderr,timeout=1200)
            write(out/(mode+'-receipt.json'),dict(exit=result.returncode,seconds=perf_counter()-begin,
                                                 command=command,timeout_seconds=1200))
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
    if sys.argv[1]=='self-test':self_test()
    elif sys.argv[1]=='run':run(Path(sys.argv[2]),sys.argv[3])
    else:
        assert digest(sys.argv[2])==sys.argv[3]
        plan=read(sys.argv[2])
        {'worker':worker,'verify':verify}[sys.argv[1]](plan,Path(plan['output']))
