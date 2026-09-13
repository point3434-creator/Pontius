"""Fixed checkpoints and accounted time budgets; no live deadline or policy adoption."""
from pathlib import Path
from time import perf_counter
import hashlib
import json
import sys
import os
import numpy as np
import run as previous
from selection import select

HERE = Path(__file__).resolve().parent
old = previous.old
read, write, digest = old.read, old.write, old.digest
CHECKPOINTS = [2048, 4096, 8192, 16384]
BUDGETS = [3, 5, 10, 15]


def bindings():
    plan = read(HERE/'plan.json')
    assert sys.version_info[:3] == (3, 14, 6) and np.__version__ == '2.5.2'
    for path, sha in plan['pins'].items():
        assert digest(path) == sha, path
    return plan


def prepare():
    previous.bindings()
    pins = dict(read(previous.HERE/'plan.json')['pins'])
    for name in ('run.py', 'plan.json'):
        pins[str(previous.HERE/name)] = digest(previous.HERE/name)
    for case in ('checkback', 'raise'):
        p = previous.HERE/'run'/f'{case}-graph-0.json'
        pins[str(p)] = digest(p)
    for p in HERE.glob('*.py'):
        pins[str(p)] = digest(p)
    pins[str(HERE/'design.md')] = digest(HERE/'design.md')
    write(HERE/'plan.json', dict(name=HERE.name, status='built; campaign not invoked',
        request="User: Let's build the next", variants=['checkback', 'raise'],
        checkpoints=CHECKPOINTS, budgets_seconds=BUDGETS, repeats=3,
        config=old.CONFIG, horizon=16384, case_timeout_seconds=180,
        private_limit_mib=3072, gpu_pool_limit_mib=1024, campaign_limit_seconds=600,
        budget_scope='Accounted prefix plus separately executed fresh audit process; '
                     'not an enforced online deadline or cold filesystem-cache test',
        selection='Latest affordable iteration, ignoring quality; no eligible row means missing',
        reference='Same-run 2048 checkpoint; must match retained graph policy digest',
        evidence='All checkpoints audited in each repeat; report every regression and budget miss',
        pins=pins))
    print(digest(HERE/'plan.json'))


def worker(case, repeat, mode):
    plan = bindings()
    import cupy as cp
    from static_solver import StaticSolver
    assert cp.__version__ == '14.2.0'
    cp.get_default_memory_pool().set_limit(size=1024*2**20)
    spec, host = old.game(case)
    arrays = {k: cp.asarray(a) for k, a in host.items()}
    model = StaticSolver(spec['nodes'], arrays, plan['horizon'])
    out = HERE/('preflight' if mode == 'preflight' else 'run')
    stops = [2048] if mode == 'preflight' else plan['checkpoints']
    rows = []
    try:
        with model.stream:
            for _ in range(32):
                model.step()
        model.stream.synchronize()
        with model.stream:
            model.reset()
        model.capture()
        assert model.iteration == 0 and int(model.counter.get()) == 0
        setup = perf_counter()-sys._research_start
        training = 0.
        for stop in stops:
            t = perf_counter()
            with model.stream:
                while model.iteration < stop:
                    model.step(replay=True)
            model.stream.synchronize()
            training += perf_counter()-t
            assert int(model.counter.get()) == stop
            avg = {k: cp.asnumpy(a) for k, a in model.average().items()}
            for a in avg.values():
                assert np.isfinite(a).all() and (a >= 0).all()
                np.testing.assert_allclose(a.sum(1), 1, atol=1e-14, rtol=0)
            score = old.Solver(spec['nodes'], host, old.CONFIG).score(avg)
            sha = hashlib.sha256(b''.join(a.tobytes() for a in avg.values())).hexdigest()
            if stop == 2048:
                anchor = read(previous.HERE/'run'/f'{case}-graph-0.json')
                assert sha == anchor['solves'][0]['policy_sha256']
            with (out/f'{case}-{repeat}-{stop}-policy.npz').open('xb') as f:
                np.savez(f, **{str(k): a for k, a in avg.items()})
            rows.append(dict(iterations=stop, training_seconds=training, score=score,
                prefix_seconds=perf_counter()-sys._research_start, policy_sha256=sha))
        pool = cp.get_default_memory_pool().total_bytes()
    finally:
        model.close()
    write(out/f'{case}-{repeat}.json', dict(executing_pid=os.getpid(), case=case,
        repeat=int(repeat), mode=mode, setup_seconds=setup, checkpoints=rows,
        pool_reserved_bytes=pool, elapsed_to_close_seconds=perf_counter()-sys._research_start))
    bindings()


def audit(case, repeat, stop, mode):
    bindings()
    stop = int(stop)
    sys.path.insert(0, str(old.HISTORY/'full-combo-direct-002/verification-tools'))
    tree = old.load('time_quality_exact', old.HISTORY/'river-tree-expansion-001/author/tree.py')
    spec, arrays = old.game(case)
    out = HERE/('preflight' if mode == 'preflight' else 'run')
    with np.load(out/f'{case}-{repeat}-{stop}-policy.npz') as z:
        probs = {i: tree.quantize(z[i]) for i in z.files}
    t = perf_counter()
    cert = tree.certificate(spec['nodes'], spec['sizes'], arrays, probs)
    elapsed = perf_counter()-t
    row = next(r for r in read(out/f'{case}-{repeat}.json')['checkpoints']
               if r['iterations'] == stop)
    for key in ('value', 'lower', 'upper', 'gap'):
        assert abs(float(tree.Q(cert[key]))-row['score'][key]) < 1e-10, key
    write(out/f'{case}-{repeat}-{stop}-audit.json', dict(executing_pid=os.getpid(),
        certificate=cert, audit_compute_seconds=elapsed, policy_sha256=row['policy_sha256']))


def execute(expected, mode):
    assert mode in ('preflight', 'run')
    assert digest(HERE/'plan.json') == expected
    plan = bindings()
    out = HERE/mode
    out.mkdir(exist_ok=False)
    path = old.HISTORY/'full-combo-direct-002/verification-tools'
    sys.path.insert(0, str(path))
    monitor = old.load('time_quality_monitor', path/'experiment.py')
    started = perf_counter()
    receipts = []
    def dispatch(label, target, *args):
        remaining = plan['campaign_limit_seconds']-(perf_counter()-started)
        assert remaining > 0, 'campaign time envelope exhausted'
        limits = dict(plan, case_timeout_seconds=min(plan['case_timeout_seconds'], remaining))
        command = [old.BASE, '-I', '-S', '-B', '-W', 'error::ResourceWarning',
                   str(HERE/'launch.py'), target, *map(str, args)]
        r = monitor.monitor(command, limits, out, label)
        receipts.append(r)
        assert r['exit'] == 0 and r['stop_reason'] is None, label
        print('COMPLETE', label, flush=True)
    dispatch('selection', 'test_selection.py')
    for repeat in range(1 if mode == 'preflight' else plan['repeats']):
        for case in plan['variants']:
            dispatch(f'{case}-{repeat}', 'campaign.py', 'worker', case, repeat, mode)
            for stop in ([2048] if mode == 'preflight' else plan['checkpoints']):
                dispatch(f'{case}-{repeat}-{stop}-audit', 'campaign.py',
                         'audit', case, repeat, stop, mode)
    bindings()
    write(out/'receipt.json', dict(complete=True, mode=mode, plan_sha256=expected,
        campaign_invoked=mode == 'run', receipts=receipts))
    summarize(mode)


def summarize(mode):
    plan = bindings()
    out = HERE/mode
    assert read(out/'receipt.json')['complete']
    result = []
    for repeat in range(1 if mode == 'preflight' else plan['repeats']):
        for case in plan['variants']:
            d = read(out/f'{case}-{repeat}.json')
            r = read(out/f'{case}-{repeat}-receipt.json')
            assert d['executing_pid'] == r['observed_pid']
            # Charge all otherwise unassigned fresh-process overhead to every prefix.
            overhead = max(0., r['seconds']-d['elapsed_to_close_seconds'])
            rows = []
            for checkpoint in d['checkpoints']:
                stop = checkpoint['iterations']
                cert = read(out/f'{case}-{repeat}-{stop}-audit.json')
                ar = read(out/f'{case}-{repeat}-{stop}-audit-receipt.json')
                assert cert['executing_pid'] == ar['observed_pid'] and ar['exit'] == 0
                assert cert['policy_sha256'] == checkpoint['policy_sha256']
                rows.append(dict(iterations=stop, policy_sha256=checkpoint['policy_sha256'],
                    charged_seconds=checkpoint['prefix_seconds']+overhead+ar['seconds'],
                    exact_exploitability=cert['certificate']['exploitability'],
                    strict_pass=cert['certificate']['strict_pass']))
            selected = {str(b): select(rows, b) for b in plan['budgets_seconds']}
            result.append(dict(case=case, repeat=repeat, rows=rows, selected=selected))
    write(out/'summary.json', dict(mode=mode, comparisons=result,
        note='Prefix accounting with independent audits; not a live deadline guarantee'))


if __name__ == '__main__':
    mode, *args = sys.argv[1:]
    globals()[mode](*args)
