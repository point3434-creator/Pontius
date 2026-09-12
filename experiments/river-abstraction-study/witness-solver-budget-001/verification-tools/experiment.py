"""Frozen grouping versus actual CFR policies under work and active-wall budgets."""
from collections import Counter
from fractions import Fraction
from hashlib import sha256
import importlib.util
import json
from math import fsum, isclose
import os
from pathlib import Path
import subprocess
import sys
from time import perf_counter
import tracemalloc

ROOT = Path('D:/Pontius-worktrees/eval-runner-consolidation')
HERE = Path(__file__).parent
PRIOR = ROOT / 'experiments/river-abstraction-study/witness-preference-confirmation-001'
for key in ('OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'OMP_NUM_THREADS'):
    os.environ[key] = '1'
spec = importlib.util.spec_from_file_location('confirmation', PRIOR/'verification-tools/experiment.py')
conf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(conf)
np, opt, pref, base = conf.np, conf.opt, conf.pref, conf.base
read, write, digest = base.read, base.write, base.digest
from pontius.river_abstraction_study import CFR, PayoffGame, anchored_clusters, range_features

METHODS = ('ordinary_preference', 'range_response', 'range_equity')
ITERATIONS = (100, 1000, 10000)
BUDGETS = (.05, .2, .5)
TOL = 1e-10


def bindings(plan):
    assert sys.version_info[:3] == (3, 14, 6)
    assert np.__version__ == '2.5.2' and conf.scipy.__version__ == '1.18.0'
    assert not tracemalloc.is_tracing()
    assert digest(__file__) == plan['script_sha256']
    for path, expected in plan['pins'].items():
        assert digest(path) == expected, path
    assert plan['cases'] == read(PRIOR/'plan.json')['cases']
    assert len(plan['cases']) == 96


def prepare(matrix, equities, models, method, tool):
    groups = []
    for seat, hands in enumerate(matrix.hands):
        capacity = len({min(int(equities[h]*200), 199) for h in hands})
        if method == 'ordinary_preference':
            raw = tool.student.raw_features(matrix, equities, seat)
            features = pref.predict(models[seat], tool.student.design(raw))
        else:
            response, equity = range_features(matrix, equities, seat)
            features = response if method == 'range_response' else equity[:, None]
        groups.append(anchored_clusters(features, matrix.joint.sum(axis=1-seat), capacity))
    reduced = matrix.aggregate(groups)
    return groups, reduced, CFR(reduced)


def snapshot(sums, iteration):
    return [(s[:, 1]/iteration if iteration else np.full(len(s), .5)).tolist() for s in sums]


def fixed(solver):
    saved = []
    start = perf_counter()
    paused = 0.
    for i in range(1, ITERATIONS[-1]+1):
        solver.step()
        if i in ITERATIONS:
            now = perf_counter()
            saved.append(dict(kind='iterations', budget=i, iteration=i,
                              policy=snapshot(solver.sums, i), active_seconds=now-start-paused))
            paused += perf_counter()-now
    return saved


def timed(solver, start, setup, budgets=BUDGETS, clock=perf_counter):
    saved, remaining = [], list(budgets)
    paused = 0.
    now = clock()
    while remaining and setup > remaining[0]:
        b = remaining.pop(0)
        saved.append(dict(kind='seconds', budget=b, iteration=0,
                          policy=snapshot(solver.sums, 0), active_seconds=0.,
                          crossing_seconds=setup, setup_missed=True))
    paused += clock()-now
    previous_elapsed = setup
    while remaining:
        assert solver.iteration < 100000, 'timed iteration ceiling'
        before = [s.copy() for s in solver.sums]
        previous_iteration = solver.iteration
        solver.step()
        elapsed = clock()-start-paused
        now = clock()
        while remaining and elapsed > remaining[0]:
            b = remaining.pop(0)
            assert previous_elapsed <= b < elapsed
            saved.append(dict(kind='seconds', budget=b, iteration=previous_iteration,
                              policy=snapshot(before, previous_iteration),
                              active_seconds=previous_elapsed, crossing_seconds=elapsed,
                              setup_missed=False))
        paused += clock()-now
        previous_elapsed = elapsed
    return saved


def score(matrix, reduced, groups, record, floor):
    x, y = (np.asarray(v) for v in record['policy'])
    full = matrix.evaluate(x[groups[0]], y[groups[1]])
    restricted = reduced.evaluate(x, y)
    midpoint = float((Fraction(floor['lower_exact'])+Fraction(floor['upper_exact']))/2)
    return dict(**record, full=full, restricted=restricted,
                grouping_floor=midpoint, above_floor=full['exploitability']-midpoint)


def no_learning(tool):
    def forbidden(*a, **kw):
        raise AssertionError('LP solving and model fitting are forbidden')
    conf.forbid_fit(tool)
    opt.linprog = opt.solve_groups = forbidden


def worker(plan, out):
    bindings(plan)
    tool = base.helpers()
    no_learning(tool)
    models = read(PRIOR/'candidate.json')['models']
    cache, trajectories, checkpoints = {}, 0, 0
    for index, case in enumerate(plan['cases']):
        common_start = perf_counter()
        equities = tool.old.equities_for(case, cache)
        matrix, controls, inputs = tool.pilot.build_inputs(case, 96, equities)
        common_seconds = perf_counter()-common_start
        prior = read(PRIOR/(case['id']+'.json'))
        assert inputs == prior['inputs']
        runs = []
        for phase in range(4):
            offset = (index + max(0, phase-1)) % 3
            order = METHODS[offset:]+METHODS[:offset]
            for position, method in enumerate(order):
                start = perf_counter()
                groups, reduced, solver = prepare(matrix, equities, models, method, tool)
                setup = perf_counter()-start
                records = fixed(solver) if phase == 0 else timed(solver, start, setup)
                assert [g.tolist() for g in groups] == prior['groups'][method]
                floor = prior['floors'][method]
                scored = [score(matrix, reduced, groups, r, floor) for r in records]
                runs.append(dict(method=method, phase=phase, repetition=phase-1,
                                 order_position=position, setup_seconds=setup,
                                 groups=[g.tolist() for g in groups], records=scored))
                trajectories += 1
                checkpoints += len(scored)
        write(out/(case['id']+'.json'), dict(case=case, common_seconds=common_seconds, runs=runs))
        print(f"completed {index+1}/96 {case['id']}", flush=True)
    assert (trajectories, checkpoints) == (1152, 3456)
    bindings(plan)
    write(out/'worker-complete.json', dict(complete=True, cases=96, trajectories=trajectories,
                                          checkpoints=checkpoints, lp_calls=0, model_fits=0))


def scalar_evaluate(matrix, x, y):
    c, f, a = matrix.check.tolist(), matrix.fold.tolist(), matrix.call.tolist()
    check = [fsum(row) for row in c]
    bet = [fsum((1-y[j])*f[i][j]+y[j]*a[i][j] for j in range(len(y)))
           for i in range(len(x))]
    value = fsum((1-x[i])*check[i]+x[i]*bet[i] for i in range(len(x)))
    upper = fsum(max(check[i], bet[i]) for i in range(len(x)))
    lower = fsum((1-x[i])*check[i] for i in range(len(x))) + fsum(
        min(fsum(x[i]*f[i][j] for i in range(len(x))),
            fsum(x[i]*a[i][j] for i in range(len(x)))) for j in range(len(y)))
    return dict(value=value, lower=lower, upper=upper, deviation0=upper-value,
                deviation1=value-lower, exploitability=(upper-lower)/2)


def selections(row, kind, budget, method, repetition=None):
    return [r for run in row['runs'] if run['method'] == method
            and ((kind == 'iterations' and run['phase'] == 0) or
                 (kind == 'seconds' and run['phase'] > 0 and
                  (repetition is None or run['repetition'] == repetition)))
            for r in run['records'] if r['kind'] == kind and r['budget'] == budget]


def statistics(rows, kind, budget, repetition=None):
    values = {m: [] for m in METHODS}
    gaps = {m: [] for m in METHODS}
    restricted = {m: [] for m in METHODS}
    counts_iterations = {m: [] for m in METHODS}
    for row in rows:
        for method in METHODS:
            records = selections(row, kind, budget, method, repetition)
            assert len(records) == (3 if kind == 'seconds' and repetition is None else 1)
            values[method].append(fsum(r['full']['exploitability'] for r in records)/len(records))
            gaps[method].append(fsum(r['above_floor'] for r in records)/len(records))
            restricted[method].append(fsum(r['restricted']['exploitability'] for r in records)/len(records))
            counts_iterations[method].append(fsum(r['iteration'] for r in records)/len(records))
    mean = lambda xs: fsum(xs)/len(xs)
    comparison = {}
    for method in METHODS[1:]:
        ds = [a-b for a, b in zip(values[METHODS[0]], values[method], strict=True)]
        comparison[method] = dict(delta=mean(ds), counts=dict(Counter(
            'lower' if d < -TOL else 'higher' if d > TOL else 'overlapping' for d in ds)))
    return dict(means={m: mean(v) for m,v in values.items()}, comparisons=comparison,
                above_floor={m:mean(v) for m,v in gaps.items()},
                restricted={m:mean(v) for m,v in restricted.items()},
                mean_iterations={m:mean(v) for m,v in counts_iterations.items()})


def summarize(rows):
    assert len(rows) == 96
    endpoints = [('iterations', b) for b in ITERATIONS]+[('seconds', b) for b in BUDGETS]
    full = {f'{k}:{b}': statistics(rows,k,b) for k,b in endpoints}
    primary = lambda rs: {f'{k}:{b}':statistics(rs,k,b) for k,b in
                         [('iterations',10000),('seconds',.5)]}
    boards = {str(b):primary([r for r in rows if r['case']['board_index']==b]) for b in range(16)}
    textures = {t:primary([r for r in rows if r['case']['texture']==t])
                for t in sorted({r['case']['texture'] for r in rows})}
    regimes = {t:primary([r for r in rows if r['case']['regime']==t]) for t in ('uniform','polarized')}
    lobo = {str(b):primary([r for r in rows if r['case']['board_index']!=b]) for b in range(16)}
    repeats = {str(n):statistics(rows,'seconds',.5,n) for n in range(3)}
    passes = lambda s: s['comparisons']['range_response']['delta'] < -TOL
    numerical = all(passes(full[k]) for k in ('iterations:10000','seconds:0.5'))
    robust = all(passes(s) for panel in (textures,regimes,lobo) for group in panel.values()
                 for s in group.values()) and all(passes(s) for s in repeats.values())
    return dict(overall=full,boards=boards,textures=textures,regimes=regimes,
                leave_one_board_out=lobo,repetitions=repeats,
                numerical_improvement_pass=numerical,robustness_pass=robust,
                common_seconds=sum(r['common_seconds'] for r in rows),
                setup_seconds={m:sum(run['setup_seconds'] for r in rows for run in r['runs']
                                     if run['method']==m) for m in METHODS},
                setup_misses=sum(x.get('setup_missed',False) for r in rows for run in r['runs']
                                 for x in run['records']))


def verify(plan, out):
    bindings(plan)
    tool = base.helpers()
    no_learning(tool)
    models = read(PRIOR/'candidate.json')['models']
    cache, rows = {}, []
    certificates = policies = replay_steps = 0
    max_error = 0.
    for index, case in enumerate(plan['cases']):
        row = read(out/(case['id']+'.json'))
        assert row['case'] == case and len(row['runs']) == 12
        equities = tool.old.equities_for(case, cache)
        matrix, _, inputs = tool.pilot.build_inputs(case,96,equities)
        prior = read(PRIOR/(case['id']+'.json'))
        assert inputs == prior['inputs']
        for phase in range(4):
            offset = (index+max(0,phase-1))%3
            assert [r['method'] for r in row['runs'] if r['phase']==phase] == list(
                METHODS[offset:]+METHODS[:offset])
        for method in METHODS:
            groups,reduced,solver = prepare(matrix,equities,models,method,tool)
            assert [g.tolist() for g in groups] == prior['groups'][method]
            opt.verify_solution(matrix,groups,prior['solutions'][method])
            certificates += 2
            at = {}
            for run in [r for r in row['runs'] if r['method']==method]:
                assert run['groups'] == prior['groups'][method]
                assert run['repetition'] == run['phase']-1
                assert 0 <= run['order_position'] < 3 and run['setup_seconds'] >= 0
                expected = ITERATIONS if run['phase']==0 else BUDGETS
                assert [r['budget'] for r in run['records']] == list(expected)
                for rec in run['records']:
                    assert rec['kind'] == ('iterations' if run['phase']==0 else 'seconds')
                    n = rec['iteration']
                    assert type(n) is int and 0 <= n <= 100000
                    if rec['kind']=='iterations':
                        assert n == rec['budget']
                    else:
                        assert 0 <= rec['active_seconds'] <= rec['budget'] < rec['crossing_seconds']
                        assert rec['setup_missed'] == (run['setup_seconds'] > rec['budget'])
                        if rec['setup_missed']:
                            assert n==0 and rec['active_seconds']==0
                    at.setdefault(n,[]).append(rec)
            for n in sorted(at):
                while solver.iteration < n:
                    solver.step()
                    replay_steps += 1
                actual = snapshot(solver.sums,n)
                for rec in at[n]:
                    assert rec['policy']==actual, (case['id'],method,n)
                    full = matrix.evaluate(np.asarray(actual[0])[groups[0]],np.asarray(actual[1])[groups[1]])
                    restricted = reduced.evaluate(*actual)
                    scalar = scalar_evaluate(matrix,np.asarray(actual[0])[groups[0]],
                                             np.asarray(actual[1])[groups[1]])
                    assert full == rec['full'] and restricted == rec['restricted']
                    for key,value in scalar.items():
                        error = abs(value-full[key])
                        max_error = max(max_error,error)
                        assert error <= TOL, (key,error)
                    assert abs(full['value']-restricted['value']) <= TOL
                    assert full['upper']+TOL >= restricted['upper']
                    assert full['lower'] <= restricted['lower']+TOL
                    floor = prior['floors'][method]
                    mid = float((Fraction(floor['lower_exact'])+Fraction(floor['upper_exact']))/2)
                    assert rec['grouping_floor']==mid
                    assert rec['above_floor']==full['exploitability']-mid
                    assert rec['above_floor'] >= -TOL
                    policies += 1
        rows.append(row)
        print(f'verified {index+1}/96',flush=True)
    assert (certificates,policies)==(576,3456)
    write(out/'summary.json',summarize(rows))
    bindings(plan)
    write(out/'audit.json',dict(passed=True,certificates=certificates,policies=policies,
                               scalar_policy_metrics=policies*6,replayed_steps=replay_steps,
                               maximum_scalar_discrepancy=max_error,lp_calls=0,model_fits=0))
    spec = importlib.util.spec_from_file_location('summary_audit', HERE/'summary-audit.py')
    auditor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(auditor)
    write(out/'summary-audit.json', auditor.audit(out))


def self_test():
    # A toy matrix has analytically known best responses and no project data.
    m=PayoffGame(np.ones((2,2))/4,np.array([[1.,-1.],[-1.,1.]]),
                 np.ones((2,2)),np.array([[2.,-2.],[-2.,2.]]),None,'toy')
    x,y=[.2,.8],[.3,.7]
    assert all(isclose(m.evaluate(x,y)[k],v,abs_tol=1e-12)
               for k,v in scalar_evaluate(m,x,y).items())
    # Inject a deterministic clock: setup .02, first step completes at .2.
    ticks=iter([.02,.02,.2,.2,.2])
    r=timed(CFR(m),0.,.02,budgets=(.05,.1),clock=lambda:next(ticks))
    assert [v['iteration'] for v in r]==[0,0]
    assert all(v['active_seconds']==.02 and v['crossing_seconds']==.2 for v in r)
    ticks=iter([.3,.3])
    r=timed(CFR(m),0.,.3,budgets=(.05,.1),clock=lambda:next(ticks))
    assert all(v['setup_missed'] and v['iteration']==0 for v in r)
    # Equality belongs to the budget; crossing only on a strictly later clock.
    ticks=iter([.02,.02,.05,.05,.05,.08,.08,.08])
    r=timed(CFR(m),0.,.02,budgets=(.05,),clock=lambda:next(ticks))
    assert r[0]['iteration']==1 and r[0]['active_seconds']==.05
    assert scalar_evaluate(m,[0,0],[0,0])['exploitability']==2.
    print('PASS: scalar BR, pre-boundary policy, multiple crossed budgets, setup miss, equality.')


def run(path, expected):
    assert digest(path)==expected
    plan=read(path)
    bindings(plan)
    out=Path(plan['output'])
    out.mkdir(parents=True,exist_ok=False)
    write(out/'plan.json',plan)
    write(out/'started.json',dict(plan_sha256=expected))
    start=perf_counter()
    try:
        for mode,timeout in [('worker',1200),('verify',900)]:
            command=[sys.executable,'-B','-W','error::ResourceWarning',str(HERE/'experiment.py'),
                     mode,str(path),expected]
            begin=perf_counter()
            with (out/(mode+'-stdout.txt')).open('xb') as stdout, (out/(mode+'-stderr.txt')).open('xb') as stderr:
                child=subprocess.run(command,cwd=ROOT,stdout=stdout,stderr=stderr,timeout=timeout)
            write(out/(mode+'-receipt.json'),dict(exit=child.returncode,seconds=perf_counter()-begin,
                                                command=command,timeout_seconds=timeout))
            assert child.returncode==0,mode+' failed'
        bindings(plan)
        write(out/'results-manifest.json',{p.name:digest(p) for p in sorted(out.iterdir()) if p.is_file()})
        write(out/'receipt.json',dict(exit=0,seconds=perf_counter()-start,
              result_manifest_sha256=digest(out/'results-manifest.json')))
        print(json.dumps(read(out/'audit.json'),indent=2))
    except BaseException as error:
        write(out/'failed.json',dict(error=type(error).__name__,message=str(error)))
        raise


if __name__=='__main__':
    if sys.argv[1]=='self-test':
        self_test()
    elif sys.argv[1]=='run':
        run(Path(sys.argv[2]),sys.argv[3])
    else:
        assert digest(sys.argv[2])==sys.argv[3]
        plan=read(sys.argv[2])
        {'worker':worker,'verify':verify}[sys.argv[1]](plan,Path(plan['output']))
