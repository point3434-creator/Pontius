"""Frozen six-arm river experiment; serial fresh workers and independent certificates."""
from pathlib import Path
import sys
import json
import os
import hashlib
import importlib.util
from time import perf_counter
from datetime import datetime, timezone
import numpy as np
from solver import Solver

HERE = Path(__file__).resolve().parent
HISTORY = Path('D:/Pontius-worktrees/eval-runner-consolidation/experiments/river-abstraction-study')
TREE = HISTORY / 'river-tree-expansion-001/author/tree.py'
BASE = 'C:/Users/point/AppData/Local/Python/pythoncore-3.14-64/python.exe'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path, data):
    with Path(path).open('x', encoding='utf-8', newline='\n') as f:
        json.dump(data, f, indent=2, sort_keys=True, allow_nan=False)
        f.write('\n')


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def monitor_module():
    old = HISTORY / 'full-combo-direct-002/verification-tools'
    sys.path.insert(0, str(old))
    return load('comparison_monitor', old/'experiment.py')


def command(*args):
    return [BASE, '-I', '-S', '-B', '-W', 'error::ResourceWarning',
            str(HERE/'launch.py'), 'experiment.py', *map(str, args)]


def bindings():
    plan = read(HERE/'plan.json')
    assert sys.version_info[:3] == (3, 14, 6)
    assert np.__version__ == plan['numpy']
    assert all(os.environ[k] == '1' for k in
               ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'))
    for path, expected in plan['pins'].items():
        assert digest(path) == expected, path
    return plan


def prepare():
    t = load('retained_river_tree', TREE)
    m = monitor_module()
    start = perf_counter()
    source = t.d.b.PRIOR/'input-001.json'
    record = read(source)
    nodes = t.public_tree(record, 'raise')
    sizes, _ = t.sequence_layout(nodes)
    arrays = t.payoff_arrays(record, nodes)
    preparation = perf_counter()-start
    assert next(iter(arrays.values())).shape == (1081, 1081)
    engine = t.engine_audit(record, nodes)
    with (HERE/'payoffs.npz').open('xb') as f:
        np.savez(f, **{str(i): a for i, a in enumerate(arrays.values())})
    write(HERE/'input.json', record)
    write(HERE/'game.json', dict(nodes=nodes, sizes=sizes, keys=list(arrays)))
    reference = HISTORY/'river-tree-expansion-001/author/plan.json'
    write(HERE/'reference.json', read(reference))
    arms = [
        dict(name='cfr_g4', alpha=None, denominator=1., predict=False, gamma=4),
        dict(name='dcfr_paper', alpha=1.5, denominator=1., predict=False, gamma=4),
        dict(name='pdcfr_matched', alpha=1.5, denominator=1., predict=True, gamma=4),
        dict(name='cfr_linear', alpha=None, denominator=1., predict=False, gamma=1),
        dict(name='dcfr_code', alpha=1.5, denominator=1.5, predict=False, gamma=4),
        dict(name='pdcfr_published', alpha=2.3, denominator=1., predict=True, gamma=5),
    ]
    arms = [a for a in arms if a['name'] in ('cfr_g4', 'dcfr_paper', 'pdcfr_matched', 'dcfr_code')]
    paths = {Path(getattr(mod, '__file__', '')).resolve()
             for mod in list(sys.modules.values()) if getattr(mod, '__file__', None)}
    paths = {p for p in paths if str(p).lower().startswith('d:')
             and 'site-packages' not in str(p) and p.is_file()}
    paths.update([source, reference, t.d.b.e.BASELINE/'checkpoint/meta.json',
                  HERE/'launch.py', HERE/'test_solver.py', TREE])
    paths.update(p for p in HERE.iterdir() if p.is_file())
    plan = dict(name='river-cfr-expanded-001-raise', frozen_at=datetime.now(timezone.utc).isoformat(),
                source_commit='6518b9d3af252c93f8a9dbdb13fb28adc2859b4c',
                context_checkout='D:/Pontius-worktrees/eval-runner-consolidation',
                authorization='User: Let\'s test it', case=1, variant='raise',
                arms=arms, repeats=3, iterations=2048, checkpoints=[16,64,256,1024,2048],
                case_timeout_seconds=180, private_limit_mib=3072,
                numpy=np.__version__, python=sys.version,
                pins={str(p):digest(p) for p in sorted(paths)},
                preparation_seconds=preparation, engine_audit=engine,
                payoff_bytes=sum(a.nbytes for a in arrays.values()), hands_per_role=1081,
                independent_final_certificate='retained rational evaluator on repeat zero of every arm',
                order='alternating role 0 then role 1; average each role before its update',
                selection='report every arm; no parameter tuning; no strategy adoption',
                quality='exploitability = (upper best response - lower best response)/2',
                units='10 units per starting pot; divide exploitability by 10 for fraction of pot',
                average='own-reach weighted; sum t^gamma realization plans, zero delay',
                comparison='first three arms share gamma=4; last three are definition controls',
                limits='sampled 50 ms memory stop, not hard cap; one observed board, not holdout')
    write(HERE/'plan.json', plan)
    print(json.dumps({k:v for k,v in plan.items() if k not in ('pins','python')}), flush=True)
    print('PLAN_SHA256', digest(HERE/'plan.json'), flush=True)


def game():
    spec = read(HERE/'game.json')
    with np.load(HERE/'payoffs.npz') as data:
        arrays = {tuple(k):data[str(i)] for i,k in enumerate(spec['keys'])}
    return spec, arrays


def worker(index, repeat):
    plan = bindings()
    start = perf_counter()
    spec, arrays = game()
    arm = plan['arms'][index]
    solver = Solver(spec['nodes'], arrays, arm)
    setup = perf_counter()-start
    training = 0.
    checkpoints = []
    snapshots = {}
    for stop in plan['checkpoints']:
        start = perf_counter()
        while solver.iteration < stop:
            solver.step()
        training += perf_counter()-start
        start = perf_counter()
        average = solver.average()
        score = solver.score(average)
        scoring = perf_counter()-start
        assert all(np.isfinite(v).all() and (v >= 0).all() for v in average.values())
        for i, p in average.items():
            np.testing.assert_allclose(p.sum(1), 1., atol=1e-14, rtol=0)
            snapshots[f'{stop}_{i}'] = p
        checkpoints.append(dict(iterations=stop, training_seconds=training,
                                score_seconds=scoring, **score))
    label = f'{repeat}-{arm["name"]}'
    with (HERE/'run'/f'{label}-policies.npz').open('xb') as f:
        np.savez(f, **snapshots)
    policy_digest = hashlib.sha256(b''.join(v.tobytes() for v in snapshots.values())).hexdigest()
    write(HERE/'run'/f'{label}.json', dict(executing_pid=os.getpid(), arm=arm, repeat=repeat,
          setup_seconds=setup, checkpoints=checkpoints, policy_sha256=policy_digest,
          numeric_bytes=sum(a.nbytes for a in arrays.values())+
          sum(a.nbytes for store in (solver.policy,solver.regret,solver.accumulator)
              for a in store.values())))
    bindings()


def verify(index):
    plan = bindings()
    t = load('retained_river_tree', TREE)
    spec, arrays = game()
    label = f'0-{plan["arms"][index]["name"]}'
    row = read(HERE/'run'/f'{label}.json')
    with np.load(HERE/'run'/f'{label}-policies.npz') as data:
        probs = {str(i):t.quantize(data[f'2048_{i}']) for i,node in enumerate(spec['nodes'])
                 if node['player'] != -1}
    start = perf_counter()
    cert = t.certificate(spec['nodes'], spec['sizes'], arrays, probs)
    seconds = perf_counter()-start
    for key in ('value','lower','upper','gap'):
        assert abs(float(t.Q(cert[key]))-row['checkpoints'][-1][key]) < 1e-10, key
    reference = read(HERE/'reference.json')
    frozen = next(j for j in reference['jobs']
                  if j['case'] == 1 and j['variant'] == plan['variant'])
    assert spec['nodes'] == frozen['nodes'] and spec['sizes'] == frozen['sequences']
    write(HERE/'run'/f'{label}-certificate.json', dict(executing_pid=os.getpid(),
          certificate=cert, certificate_seconds=seconds, float_agreement=True,
          retained_tree_identity=True, quantized_probabilities=probs))
    bindings()


def run(expected):
    assert digest(HERE/'plan.json') == expected
    plan = bindings()
    out = HERE/'run'
    out.mkdir(exist_ok=False)
    monitor = monitor_module()
    receipts = []
    for repeat in range(plan['repeats']):
        # Rotate order across fresh processes to reduce simple thermal/order bias.
        for index in [(j+2*repeat)%len(plan['arms']) for j in range(len(plan['arms']))]:
            label = f'{repeat}-{plan["arms"][index]["name"]}'
            receipt = monitor.monitor(command('worker',index,repeat), plan, out, label)
            receipts.append(receipt)
            assert receipt['exit'] == 0 and receipt['stop_reason'] is None, label
            row = read(out/f'{label}.json')
            assert row['executing_pid'] == receipt['observed_pid']
            print(label, row['checkpoints'][-1], flush=True)
    for index, arm in enumerate(plan['arms']):
        label = f'0-{arm["name"]}'
        receipt = monitor.monitor(command('verify',index), plan, out, label+'-verify')
        receipts.append(receipt)
        assert receipt['exit'] == 0 and receipt['stop_reason'] is None, label
        assert read(out/f'{label}-certificate.json')['executing_pid'] == receipt['observed_pid']
        assert len({read(out/f'{r}-{arm["name"]}.json')['policy_sha256']
                    for r in range(plan['repeats'])}) == 1
        print('CERTIFIED', label, flush=True)
    bindings()
    write(out/'receipt.json', dict(complete=True, workers=12, certificates=4,
          all_repeats_policy_identical=True, plan_sha256=expected, receipts=receipts))


if __name__ == '__main__':
    mode, *args = sys.argv[1:]
    if mode == 'prepare':
        prepare()
    elif mode == 'run':
        run(*args)
    elif mode == 'worker':
        worker(*map(int,args))
    elif mode == 'verify':
        verify(int(args[0]))
