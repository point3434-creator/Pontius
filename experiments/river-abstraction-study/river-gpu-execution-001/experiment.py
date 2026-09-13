"""Bounded actual-game CPU/GPU comparison. No strategy or runtime adoption."""
from time import perf_counter
START = perf_counter()
from pathlib import Path
import hashlib
import importlib.util
import json
import os
import sys
import numpy as np
from solver import Solver

HERE = Path(__file__).resolve().parent
HISTORY = Path('D:/Pontius-worktrees/eval-runner-consolidation/experiments/river-abstraction-study')
PRIOR = Path('D:/Pontius/experiments/river-cfr-expanded-001')
BASE = 'C:/Users/point/AppData/Local/Python/pythoncore-3.14-64/python.exe'
CONFIG = dict(alpha=1.5, denominator=1.5, gamma=4, predict=False)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path, data):
    with Path(path).open('x', encoding='utf-8', newline='\n') as f:
        json.dump(data, f, indent=2, sort_keys=True, allow_nan=False)
        f.write('\n')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def bindings():
    plan = read(HERE/'plan.json')
    assert sys.version_info[:3] == (3, 14, 6) and np.__version__ == '2.5.2'
    for path, sha in plan['pins'].items():
        assert digest(path) == sha, path
    return plan


def game(case):
    spec = read(PRIOR/case/'game.json')
    with np.load(PRIOR/case/'payoffs.npz') as z:
        arrays = {tuple(k): z[str(i)] for i, k in enumerate(spec['keys'])}
    assert all(a.dtype == np.float64 and a.shape == (1081, 1081) for a in arrays.values())
    return spec, arrays


def prepare():
    pins = {}
    for case in ('checkback', 'raise'):
        prior = read(PRIOR/case/'plan.json')
        pins.update(prior['pins'])
        pins[str(PRIOR/case/'plan.json')] = digest(PRIOR/case/'plan.json')
    for name in ('launch.py', 'experiment.py', 'solver.py', 'gpu_adapter.py'):
        pins[str(HERE/name)] = digest(HERE/name)
    write(HERE/'plan.json', dict(name=HERE.name, authorization='User: Lets run next stop',
        variants=['checkback', 'raise'], arms=['cpu', 'gpu'], repeats=3,
        iterations=2048, parity_iterations=32, config=CONFIG,
        parity_atol=1e-10, parity_rtol=1e-8,
        quality_rule='GPU final independently audited gap <= 1.01 * CPU gap + 1e-10',
        strict_gap_threshold=1e-8, case_timeout_seconds=180, private_limit_mib=3072,
        gpu_pool_limit_mib=1024, profile_iterations=128,
        timing='Synchronized wall; one BLAS thread; 32 warmup iterations then fresh reset; '
               'setup, warmup, transfer, scoring and process wall retained separately',
        cache='Dedicated CuPy kernel cache shared across sequential workers; '
              'first-use compile paid in first parity process, recorded separately',
        scope='Eager float64 port, no CUDA graph, no GPU-CFR compiler, no six-max claim',
        pins=pins))


def parity(case):
    plan = bindings()
    t = perf_counter()
    import cupy as cp
    from gpu_adapter import Solver as GPU
    cp.get_default_memory_pool().set_limit(size=1024*2**20)
    spec, arrays = game(case)
    cpu = Solver(spec['nodes'], arrays, CONFIG)
    gpu = GPU(spec['nodes'], {k: cp.asarray(a) for k, a in arrays.items()}, CONFIG)
    differences = []
    for iteration in range(1, 33):
        cpu.step()
        gpu.step()
        maximum = 0.
        for attr in ('regret', 'policy', 'accumulator'):
            for key, expected in getattr(cpu, attr).items():
                actual = cp.asnumpy(getattr(gpu, attr)[key])
                np.testing.assert_allclose(actual, expected,
                    atol=plan['parity_atol'], rtol=plan['parity_rtol'])
                maximum = max(maximum, float(np.max(np.abs(actual-expected))))
        differences.append(maximum)
    # The only adapted primitive must handle zero, positive and clipped regret rows.
    from gpu_adapter import normalize
    probe = np.array([[0., 0.], [2., 3.], [0., 5.]])
    np.testing.assert_allclose(cp.asnumpy(normalize(cp.asarray(probe))),
                               [[.5,.5],[.4,.6],[0.,1.]], atol=1e-15)
    write(HERE/'run'/f'{case}-parity.json', dict(passed=True,
        executing_pid=os.getpid(), iterations=32, max_abs_by_iteration=differences,
        import_compile_transfer_check_seconds=perf_counter()-t,
        cupy=cp.__version__, device=cp.cuda.runtime.getDeviceProperties(0)['name'].decode(),
        pool_reserved_bytes=cp.get_default_memory_pool().total_bytes()))


def profile(case):
    bindings()
    spec, arrays = game(case)
    times = []
    class TimedMatrix(np.ndarray):
        def __matmul__(self, other):
            t = perf_counter()
            value = self.view(np.ndarray) @ np.asarray(other)
            times.append(perf_counter()-t)
            return value
        def __rmatmul__(self, other):
            t = perf_counter()
            value = np.asarray(other) @ self.view(np.ndarray)
            times.append(perf_counter()-t)
            return value
    solver = Solver(spec['nodes'], {k:a.view(TimedMatrix) for k,a in arrays.items()}, CONFIG)
    t = perf_counter()
    for _ in range(128):
        solver.step()
    elapsed = perf_counter()-t
    expected = 256 * sum(n['player'] == -1 for n in spec['nodes'])
    assert len(times) == expected
    write(HERE/'run'/f'{case}-profile.json', dict(executing_pid=os.getpid(),
        iterations=128, calls=len(times), instrumented_total_seconds=elapsed,
        matrix_product_seconds=sum(times), matrix_share=sum(times)/elapsed,
        warning='Diagnostic attribution only; instrumented time excluded from comparison'))


def worker(case, arm, repeat):
    bindings()
    t = perf_counter()
    spec, arrays = game(case)
    load_seconds = perf_counter()-t
    sync = lambda: None
    cls, device_arrays = Solver, arrays
    gpu_setup = 0.
    if arm == 'gpu':
        t = perf_counter()
        import cupy as cp
        from gpu_adapter import Solver as cls
        cp.get_default_memory_pool().set_limit(size=1024*2**20)
        sync = cp.cuda.Stream.null.synchronize
        device_arrays = {k:cp.asarray(a) for k,a in arrays.items()}
        sync()
        gpu_setup = perf_counter()-t
    t = perf_counter()
    warm = cls(spec['nodes'], device_arrays, CONFIG)
    for _ in range(32):
        warm.step()
    sync()
    warm_seconds = perf_counter()-t
    del warm
    t = perf_counter()
    solver = cls(spec['nodes'], device_arrays, CONFIG)
    sync()
    reset_seconds = perf_counter()-t
    t = perf_counter()
    for _ in range(2048):
        solver.step()
    sync()
    train_seconds = perf_counter()-t
    t = perf_counter()
    average = solver.average()
    if arm == 'gpu':
        average = {i:cp.asnumpy(a) for i,a in average.items()}
    sync()
    average_transfer_seconds = perf_counter()-t
    t = perf_counter()
    score = Solver(spec['nodes'], arrays, CONFIG).score(average)
    score_seconds = perf_counter()-t
    for a in average.values():
        assert np.isfinite(a).all() and (a >= 0).all()
        np.testing.assert_allclose(a.sum(1), 1., atol=1e-14, rtol=0)
    label = f'{case}-{arm}-{repeat}'
    with (HERE/'run'/f'{label}-policy.npz').open('xb') as f:
        np.savez(f, **{str(i):a for i,a in average.items()})
    write(HERE/'run'/f'{label}.json', dict(executing_pid=os.getpid(), case=case,
        arm=arm, repeat=int(repeat), load_seconds=load_seconds, gpu_setup_seconds=gpu_setup,
        warmup_seconds=warm_seconds, reset_seconds=reset_seconds, train_seconds=train_seconds,
        average_transfer_seconds=average_transfer_seconds, score_seconds=score_seconds,
        worker_elapsed_seconds=perf_counter()-START, score=score,
        pool_reserved_bytes=cp.get_default_memory_pool().total_bytes() if arm=='gpu' else 0,
        policy_sha256=hashlib.sha256(b''.join(a.tobytes() for a in average.values())).hexdigest()))
    bindings()


def verify(case, arm):
    bindings()
    sys.path.insert(0, str(HISTORY/'full-combo-direct-002/verification-tools'))
    tree = load('gpu_exact_tree', HISTORY/'river-tree-expansion-001/author/tree.py')
    spec, arrays = game(case)
    label = f'{case}-{arm}-0'
    with np.load(HERE/'run'/f'{label}-policy.npz') as z:
        probs = {i:tree.quantize(z[i]) for i in z.files}
    t = perf_counter()
    cert = tree.certificate(spec['nodes'], spec['sizes'], arrays, probs)
    seconds = perf_counter()-t
    row = read(HERE/'run'/f'{label}.json')
    for key in ('value', 'lower', 'upper', 'gap'):
        assert abs(float(tree.Q(cert[key]))-row['score'][key]) < 1e-10, key
    write(HERE/'run'/f'{label}-certificate.json', dict(executing_pid=os.getpid(),
          certificate=cert, seconds=seconds, float_agreement=True))


def run(expected):
    assert digest(HERE/'plan.json') == expected
    plan = bindings()
    out = HERE/'run'
    out.mkdir(exist_ok=False)
    old = HISTORY/'full-combo-direct-002/verification-tools'
    sys.path.insert(0, str(old))
    monitor = load('gpu_monitor', old/'experiment.py')
    receipts = []
    def dispatch(label, *args):
        cmd = [BASE, '-I', '-S', '-B', '-W', 'error::ResourceWarning',
               str(HERE/'launch.py'), *map(str,args)]
        receipt = monitor.monitor(cmd, plan, out, label)
        receipts.append(receipt)
        assert receipt['exit'] == 0 and receipt['stop_reason'] is None, label
        print('COMPLETE', label, flush=True)
    for case in plan['variants']:
        dispatch(case+'-parity', 'parity', case)
        dispatch(case+'-profile', 'profile', case)
    for repeat in range(3):
        for case in plan['variants']:
            for arm in (['cpu','gpu'] if repeat%2==0 else ['gpu','cpu']):
                dispatch(f'{case}-{arm}-{repeat}', 'worker', case, arm, repeat)
    for case in plan['variants']:
        for arm in plan['arms']:
            dispatch(f'{case}-{arm}-verify', 'verify', case, arm)
        cpu = read(out/f'{case}-cpu-0.json')['score']['gap']
        for repeat in range(3):
            gpu = read(out/f'{case}-gpu-{repeat}.json')['score']['gap']
            assert gpu <= cpu*1.01+1e-10
    bindings()
    write(out/'receipt.json', dict(complete=True, plan_sha256=expected,
                                 quality_noninferiority_pass=True, receipts=receipts))


if __name__ == '__main__':
    mode, *args = sys.argv[1:]
    globals()[mode](*args)
