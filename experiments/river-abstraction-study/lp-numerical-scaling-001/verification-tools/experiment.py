"""One fixed LP unit change on four observed cases; no tuning or new population."""
from diagnose import d, ROOT, OLD
import scaling as s
from pathlib import Path
from fractions import Fraction as Q
import importlib.util
import json
import os
import sys
from time import perf_counter
from datetime import datetime, timezone
from hashlib import sha256

HERE = Path(__file__).resolve().parent
OUT = Path('D:/Pontius/tmp/river-lp-numerical-001/run')
sys.set_int_max_str_digits(100000)
sys.path.insert(0, str(OLD/'verification-tools'))
spec = importlib.util.spec_from_file_location('frozen_direct_monitor', OLD/'verification-tools/experiment.py')
monitor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(monitor)


def write(path, obj):
    with path.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(obj, f, indent=2, sort_keys=True, allow_nan=False)
        f.write('\n')


def freeze():
    pins = dict(d.read(OLD/'plan.json')['pins'])
    for p in HERE.iterdir():
        if p.is_file() and p.name != 'plan.json':
            pins[str(p)] = d.digest(p)
    for p in d.HISTORY.glob('*/milestone-manifest.json'):
        pins[str(p)] = d.digest(p)
    pins[str(OLD/'verification-tools/experiment.py')] = d.digest(OLD/'verification-tools/experiment.py')
    plan = dict(name='lp-numerical-scaling-001', cases=list(range(4)), scale=s.SCALE,
        hypothesis='small_matrix_value drops probability-weighted coefficients',
        source_commit='6518b9d3af252c93f8a9dbdb13fb28adc2859b4c',
        frozen_at_utc=datetime.now(timezone.utc).isoformat(), pins=pins,
        output=str(OUT), python=sys.version, numpy=d.np.__version__, scipy=d.c.scipy.__version__,
        exact_gap_limit='1e-8', max_lp_calls=8, time_limit_per_lp=10, maxiter=20000,
        case_timeout_seconds=120, private_limit_mib=3072, memory_scope='sampled worker private',
        rule='all four cases retained; one scale; original certificates; no retry or retuning')
    for p,h in pins.items():
        assert d.digest(p) == h, p
    write(HERE/'plan.json', plan)
    print('Frozen plan SHA-256:', d.digest(HERE/'plan.json'))


def bindings(plan):
    assert sys.version_info[:3] == (3,14,6)
    assert (d.np.__version__, d.c.scipy.__version__) == ('2.5.2','1.18.0')
    assert s.SCALE == plan['scale'] == 2**20
    assert all(os.environ[k] == '1' for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'))
    for p,h in plan['pins'].items():
        assert d.digest(p) == h, p


def worker(plan, j):
    bindings(plan)
    start = perf_counter()
    game, _, meta = d.build(d.read(d.b.PRIOR/f'input-{j:03d}.json'))
    assert meta == d.read(OLD/f'case-{j:03d}.json')['inputs']
    kernel = d.Kernel(game)
    d.m.bounds = kernel.bounds
    setup = perf_counter()-start
    identity = [list(range(1081))]*2
    original = d.c.opt.linprog
    s.CALLS.clear()
    d.c.opt.linprog = s.solve
    start = perf_counter()
    failure = None
    try:
        d.m.pair(game, identity)
    except AssertionError as error:
        failure = str(error)
    finally:
        d.c.opt.linprog = original
    seconds = perf_counter()-start
    calls = list(s.CALLS)
    result = dict(case=j, executing_pid=os.getpid(), setup_seconds=setup,
        solve_and_certificate_seconds=seconds, calls=calls, refusal=failure, inputs=meta)
    if len(calls) == 2 and all(row['success'] for row in calls):
        bets = len(game.fold)
        x = d.np.clip(d.np.array(calls[0]['original_units_x'])[:1081*(bets+1)].reshape(1081,bets+1),0,1).tolist()
        y = d.np.clip(d.np.array(calls[1]['original_units_x'])[:1081*bets].reshape(bets,1081),0,1).tolist()
        low, high = kernel.bounds(game,x,y,identity)
        result.update(profile=dict(x=x,y=y,bounds=list(map(str,(low,high)))),
            exact_gap=str(high-low), exploitability=float((high-low)/2),
            strict_pass=high-low <= Q(plan['exact_gap_limit']))
        assert result['strict_pass'] == (failure is None)
    else:
        result['strict_pass'] = False
    write(OUT/f'case-{j:03d}.json', result)
    bindings(plan)


def verify(plan,j):
    bindings(plan)
    row = d.read(OUT/f'case-{j:03d}.json')
    game, _, meta = d.build(d.read(d.b.PRIOR/f'input-{j:03d}.json'))
    assert meta == row['inputs']
    def forbidden(*args,**kwargs):
        raise AssertionError('new verification solves forbidden')
    d.c.opt.linprog = forbidden
    assert len(row['calls']) == 2 and all(v['success'] for v in row['calls'])
    kernel = d.Kernel(game)
    profile = row['profile']
    low,high = kernel.bounds(game,profile['x'],profile['y'],[list(range(1081))]*2)
    assert profile['bounds'] == list(map(str,(low,high)))
    assert str(high-low) == row['exact_gap']
    assert row['strict_pass'] == (high-low <= Q('1e-8'))
    literal_checks = 0
    for start in (0,237,811):
        ii = [(start+17*k)%1081 for k in range(9)]
        jj = [(start+31*k+7)%1081 for k in range(11)]
        sub = d.m.Game(game.check[d.np.ix_(ii,jj)],game.fold[:,ii][:,:,jj],game.call[:,ii][:,:,jj])
        x = [profile['x'][i] for i in ii]
        y = [[r[i] for i in jj] for r in profile['y']]
        groups = [list(range(9)),list(range(11))]
        assert d.Kernel(sub).bounds(sub,x,y,groups) == d.literal(sub,x,y,groups)
        literal_checks += 1
    write(OUT/f'audit-{j:03d}.json',dict(case=j,passed=True,new_lp_calls=0,
        coefficients=d.coefficient_audit(game,kernel),literal_checks=literal_checks,
        strict_pass=row['strict_pass'],executing_pid=os.getpid()))


def run(plan):
    bindings(plan)
    OUT.mkdir(exist_ok=False)
    write(OUT/'plan.json',plan)
    rows = []
    start = perf_counter()
    for j in plan['cases']:
        entry = dict(case=j)
        for mode in ('worker','verify'):
            code = ('import sys,runpy;sys.path[:0]='+repr([monitor.SITE,str(HERE)])+
                ';sys.argv=sys.argv[1:];runpy.run_path(sys.argv[0],run_name="__main__")')
            cmd = [monitor.BASE_PYTHON,'-I','-S','-B','-W','error::ResourceWarning','-c',code,
                   str(HERE/'experiment.py'),mode,str(j)]
            receipt = monitor.monitor(cmd,plan,OUT,f'{mode}-{j:03d}')
            entry[mode] = receipt
            if receipt['exit'] or receipt['stop_reason']:
                break
            artifact = d.read(OUT/f'{"case" if mode == "worker" else "audit"}-{j:03d}.json')
            assert artifact['executing_pid'] == receipt['observed_pid']
            if mode == 'worker':
                entry.update(strict_pass=artifact['strict_pass'], exploitability=artifact.get('exploitability'),
                    solve_seconds=artifact['solve_and_certificate_seconds'])
        rows.append(entry)
        print(json.dumps({k:v for k,v in entry.items() if k not in ('worker','verify')}),flush=True)
    bindings(plan)
    write(OUT/'receipt.json',dict(cases=rows,seconds=perf_counter()-start,
        complete=all('verify' in r and r['verify']['exit'] == 0 for r in rows),
        strict_passes=sum(r.get('strict_pass',False) for r in rows)))


if __name__ == '__main__':
    if sys.argv[1] == 'freeze':
        freeze()
    else:
        plan = d.read(HERE/'plan.json')
        if sys.argv[1] == 'run':
            assert d.digest(HERE/'plan.json') == sys.argv[2]
            run(plan)
        else:
            globals()[sys.argv[1]](plan,int(sys.argv[2]))
