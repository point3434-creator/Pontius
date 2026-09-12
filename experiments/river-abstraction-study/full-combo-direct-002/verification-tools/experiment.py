"""Bounded four-case direct full-combo versus compressed river comparison."""
import direct as d
from direct import Path, sys, Q, perf_counter
import os
import subprocess
import ctypes as ct
from ctypes import wintypes as wt
import time
import tracemalloc

HERE = Path(__file__).resolve().parent
NAME = 'full-combo-direct-002'
ROOT, HISTORY, PREVIOUS = d.ROOT, d.HISTORY, d.PREVIOUS
read, write, digest = d.read, d.write, d.digest
sys.set_int_max_str_digits(100000)
BASE_PYTHON = 'C:/Users/point/AppData/Local/Python/pythoncore-3.14-64/python.exe'
SITE = 'D:/Pontius/tmp/group-opt-author/venv/Lib/site-packages'


def child_command(args):
    code = ('import sys,runpy; sys.path.insert(0,'+repr(SITE)+'); '
            'sys.path.insert(0,'+repr(str(HERE))+'); sys.argv=sys.argv[1:]; '
            'runpy.run_path(sys.argv[0],run_name="__main__")')
    return [BASE_PYTHON, '-I', '-S', '-B', '-W', 'error::ResourceWarning', '-c', code, *args]


def bindings(plan):
    assert plan['name'] == NAME and sys.version_info[:3] == (3, 14, 6)
    assert (plan['python'], plan['numpy'], plan['scipy']) == (
        sys.version, d.np.__version__, d.c.scipy.__version__)
    assert not tracemalloc.is_tracing() and d.b.e.evaluator.BACKEND == 'phevaluator-c'
    assert plan['case_timeout_seconds'] == 120 and plan['private_limit_mib'] == 3072
    assert plan['cases'] == list(range(4))
    for name in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'):
        assert os.environ[name] == '1'
    for path, expected in plan['pins'].items():
        assert digest(path) == expected, path
    assert plan['base_python'] == BASE_PYTHON and plan['site_packages'] == SITE


def attempt(game, groups, kernel, operation):
    original = d.c.opt.linprog
    calls = []
    def observed(*args, **kwargs):
        start = perf_counter()
        answer = original(*args, **kwargs)
        calls.append(dict(success=bool(answer.success), status=int(answer.status),
            message=str(answer.message), iterations=int(answer.nit),
            seconds=perf_counter()-start, options=kwargs['options'],
            variables=len(args[0]), x=None if answer.x is None else answer.x.tolist()))
        return answer
    d.c.opt.linprog = observed
    start, before = perf_counter(), kernel.bound_seconds
    try:
        value = operation()
        result = dict(status='certified', solution=value)
    except AssertionError as error:
        result = dict(status='not_certified', error=str(error))
    finally:
        d.c.opt.linprog = original
    result.update(seconds=perf_counter()-start,
                  exact_bound_seconds=kernel.bound_seconds-before, calls=calls)
    return result


def worker(plan, out, j):
    bindings(plan)
    start = perf_counter()
    record = read(d.b.PRIOR/f'input-{j:03d}.json')
    game, groups, meta = d.build(record)
    kernel = d.Kernel(game)
    setup = perf_counter()-start
    d.m.bounds = kernel.bounds
    identity = [list(range(1081))]*2
    row = dict(case=j, input_sha256=digest(d.b.PRIOR/f'input-{j:03d}.json'),
               groups=groups, inputs=meta, setup_seconds=setup, executing_pid=os.getpid())
    order = ['full', 'compressed'] if j % 2 == 0 else ['compressed', 'full']
    for arm in order:
        if arm == 'full':
            row['full'] = attempt(game, identity, kernel, lambda: d.m.pair(game, identity))
        else:
            start = perf_counter()
            trainer = d.m.Trainer(game, groups)
            for _ in range(50000):
                trainer.step()
            x, y = trainer.average()
            train_seconds = perf_counter()-start
            start = perf_counter()
            score = d.m.score(game, groups, x, y)
            row['compressed'] = dict(x=x, y=y, iteration=50000, **score,
                training_seconds=train_seconds, scoring_seconds=perf_counter()-start)
        print(f'case {j} {arm} completed', flush=True)
    row['floor'] = attempt(game, groups, kernel, lambda: d.m.solve(game, groups))
    row['arm_order'] = order
    write(out/f'case-{j:03d}.json', row)
    bindings(plan)


def verify(plan, out, j):
    bindings(plan)
    def forbidden(*args, **kwargs):
        raise AssertionError('verifier LP forbidden')
    d.c.opt.linprog = forbidden
    row = read(out/f'case-{j:03d}.json')
    record = read(d.b.PRIOR/f'input-{j:03d}.json')
    game, groups, meta = d.build(record)
    assert row['case'] == j and row['input_sha256'] == digest(d.b.PRIOR/f'input-{j:03d}.json')
    assert row['inputs'] == meta and row['groups'] == groups
    kernel = d.Kernel(game)
    d.m.bounds = kernel.bounds
    trainer = d.m.Trainer(game, groups)
    for _ in range(50000):
        trainer.step()
    x, y = trainer.average()
    cmp = row['compressed']
    assert (x, y) == (cmp['x'], cmp['y']) and cmp['iteration'] == 50000
    assert all(cmp[k] == v for k, v in d.m.score(game, groups, x, y).items())
    if row['full']['status'] == 'certified':
        value = d.profile_audit(game, kernel, row['full']['solution'])
        assert value <= Q('5e-9')
    if row['floor']['status'] == 'certified':
        d.m.verify(game, groups, row['floor']['solution'])
    for name in ('full', 'floor'):
        result = row[name]
        assert result['status'] in ('certified', 'not_certified')
        assert len(result['calls']) in ((2,) if name == 'full' else (2, 4))
        if result['status'] == 'certified':
            assert all(v['success'] for v in result['calls'])
        else:
            assert 'solution' not in result and 'error' in result
        for call in result['calls']:
            assert call['options']['time_limit'] == 10
            assert call['options']['maxiter'] == 20000
    checks = d.coefficient_audit(game, kernel)
    settlement = d.b.engine_audit(record)
    assert settlement['checks'] == 15
    write(out/f'audit-{j:03d}.json', dict(passed=True, case=j, replayed_updates=50000,
        coefficients=checks, literal_settlements=15, new_lp_calls=0,
        full_status=row['full']['status'], floor_status=row['floor']['status'],
        executing_pid=os.getpid()))
    bindings(plan)


class Memory(ct.Structure):
    _fields_ = [('cb', wt.DWORD), ('PageFaultCount', wt.DWORD)]+[
        (name, ct.c_size_t) for name in ('PeakWorkingSetSize', 'WorkingSetSize',
        'QuotaPeakPagedPoolUsage', 'QuotaPagedPoolUsage', 'QuotaPeakNonPagedPoolUsage',
        'QuotaNonPagedPoolUsage', 'PagefileUsage', 'PeakPagefileUsage', 'PrivateUsage')]


def monitor(command, plan, out, label):
    api = ct.WinDLL('psapi').GetProcessMemoryInfo
    api.argtypes = [wt.HANDLE, ct.POINTER(Memory), wt.DWORD]
    api.restype = wt.BOOL
    start, private, working, peak_commit, samples, reason = perf_counter(), 0, 0, 0, 0, None
    with (out/(label+'-stdout.txt')).open('xb') as stdout, \
         (out/(label+'-stderr.txt')).open('xb') as stderr:
        with subprocess.Popen(command, cwd=HERE, stdout=stdout, stderr=stderr) as child:
            while child.poll() is None:
                info = Memory()
                info.cb = ct.sizeof(info)
                if not api(int(child._handle), ct.byref(info), info.cb):
                    if child.poll() is None:
                        reason = 'memory_observer_failed'
                        child.kill()
                    break
                samples += 1
                private = max(private, info.PrivateUsage)
                working = max(working, info.WorkingSetSize)
                peak_commit = max(peak_commit, info.PeakPagefileUsage)
                if private > plan['private_limit_mib']*1024**2:
                    reason = 'sampled_private_memory_limit'
                elif perf_counter()-start > plan['case_timeout_seconds']:
                    reason = 'wall_time_limit'
                if reason:
                    child.kill()
                    break
                time.sleep(.05)
            code = child.wait()
    result = dict(command=command, exit=code, seconds=perf_counter()-start,
        observed_pid=child.pid,
        stop_reason=reason, samples=samples, sampled_peak_private_bytes=private,
        sampled_peak_working_set_bytes=working, os_peak_commit_bytes=peak_commit)
    write(out/(label+'-receipt.json'), result)
    return result


def run(path, expected):
    plan = read(path)
    bindings(plan)
    out = Path(plan['output'])
    out.mkdir(parents=True, exist_ok=False)
    write(out/'plan.json', plan)
    start, statuses = perf_counter(), []
    for j in plan['cases']:
        status = dict(case=j)
        for mode in ('worker', 'verify'):
            command = child_command([str(HERE/'experiment.py'), mode, str(path), expected, str(j)])
            receipt = monitor(command, plan, out, f'{mode}-{j:03d}')
            status[mode] = receipt['exit'] == 0 and receipt['stop_reason'] is None
            if not status[mode]:
                break
            artifact = read(out/f'{"case" if mode == "worker" else "audit"}-{j:03d}.json')
            assert receipt['observed_pid'] == artifact['executing_pid']
        statuses.append(status)
    bindings(plan)
    write(out/'results-manifest.json', {p.name: digest(p) for p in sorted(out.iterdir())
                                        if p.is_file()})
    write(out/'receipt.json', dict(seconds=perf_counter()-start, cases=statuses,
        complete=all(v.get('verify', False) for v in statuses),
        result_manifest_sha256=digest(out/'results-manifest.json')))


if __name__ == '__main__':
    mode, path, expected, *rest = sys.argv[1:]
    assert digest(path) == expected
    if mode == 'run':
        run(Path(path), expected)
    else:
        plan = read(path)
        {'worker': worker, 'verify': verify}[mode](plan, Path(plan['output']), int(rest[0]))
