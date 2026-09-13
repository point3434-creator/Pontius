"""Bounded transfer from six-max public histories into the frozen river repair game."""
from support import *
from exact_kernel import Kernel
import inputs
from fractions import Fraction as Q
from time import perf_counter
import gc
import os
import tracemalloc

HERE = Path(__file__).resolve().parent
NAME = 'blueprint-range-transfer-001'
read, digest = c.read, c.digest
LITERAL_BOUNDS = m.bounds


def write(path, value):
    import json
    with Path(path).open('x', encoding='utf-8', newline='\n') as f:
        json.dump(value, f, sort_keys=True, indent=2, allow_nan=False)
        f.write('\n')


def bindings(plan):
    assert plan['name'] == NAME and not tracemalloc.is_tracing()
    assert sys.version_info[:3] == (3, 14, 6)
    assert (plan['python'], plan['numpy'], plan['scipy']) == (
        sys.version, np.__version__, c.scipy.__version__)
    assert evaluator.BACKEND == plan['evaluator'] == 'phevaluator-c'
    assert plan['phase_timeout_seconds'] == 1800
    assert plan['capture'] == dict(seed=inputs.SEED, target=4, max_hands=2000)
    assert inputs.TARGET == 4 and inputs.MAX_HANDS == 2000
    for name in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'):
        assert os.environ[name] == '1'
    for path, expected in plan['pins'].items():
        assert digest(path) == expected, path


def certificate(first, second):
    l0, u0 = map(Q, first['bounds'])
    l1, u1 = map(Q, second['bounds'])
    return dict(seat0=first, seat1=second,
        floor=list(map(str, (max(Q(0), (l1-u0)/2), (u1-l0)/2))))


def fit(game, groups, iterations):
    start = perf_counter()
    engine = r.Bettor(game, groups)
    for _ in range(iterations):
        engine.step()
    x = engine.average()
    return engine, dict(iteration=iterations, x=x, seconds=perf_counter()-start)


def solve_case(record):
    start = perf_counter()
    game, groups, details = inputs.build(record)
    preparation = perf_counter()-start
    start = perf_counter()
    kernel = Kernel(game)
    exact_setup = perf_counter()-start
    m.bounds = kernel.bounds
    try:
        start = perf_counter()
        trainer = m.Trainer(game, groups)
        for _ in range(50000):
            trainer.step()
        x, y = trainer.average()
        initial_seconds = perf_counter()-start
        initial = dict(x=x, y=y, iteration=50000, **m.score(game, groups, x, y))
        # Fresh witness cost belongs to repair; caller certificate is diagnostic only.
        start = perf_counter()
        first = m.pair(game, [groups[0], list(range(1081))])
        values = kernel.values(first['y'])
        proposal = r.exchange(groups[0], values)
        witness_proposal_seconds = perf_counter()-start
        proposed = [proposal['groups'], groups[1]]
        _, repaired = fit(game, proposed, 50000)
        work_budget = witness_proposal_seconds+repaired['seconds']
        start = perf_counter()
        repair_choice = r.accept(game, groups, x, y, proposed, repaired['x'])
        repair_gate_seconds = perf_counter()-start
        # Reconstruct the incumbent learner, then charge only additional updates.
        control, initial_control = fit(game, groups, 50000)
        assert initial_control['x'] == x
        active, trace = 0., []
        while active < work_budget and control.iteration < 1050000:
            start = perf_counter()
            for _ in range(250):
                control.step()
            candidate = control.average()
            active += perf_counter()-start
            trace.append([control.iteration, active])
        assert active >= work_budget, 'continuation update cap: incomplete comparison'
        continued = dict(iteration=control.iteration, x=candidate, seconds=active,
                         reconstruction_seconds=initial_control['seconds'], trace=trace)
        start = perf_counter()
        control_choice = r.accept(game, groups, x, y, groups, candidate)
        control_gate_seconds = perf_counter()-start
        start = perf_counter()
        second = m.pair(game, [list(range(1081)), groups[1]])
        original_solution = certificate(first, second)
        proposed_first = m.pair(game, [proposed[0], list(range(1081))])
        proposed_solution = certificate(proposed_first, second)
        m.verify(game, groups, original_solution)
        m.verify(game, proposed, proposed_solution)
        diagnostic_seconds = perf_counter()-start
        return dict(groups=groups, inputs=details, initial=initial, proposal=proposal,
            values=[[str(v) for v in row] for row in values],
            repaired=repaired, continued=continued,
            choices=dict(repair=repair_choice, continuation=control_choice),
            original_solution=original_solution, proposed_solution=proposed_solution,
            times=dict(game_preparation=preparation, exact_setup=exact_setup,
                initial_both_roles=initial_seconds, witness_proposal=witness_proposal_seconds,
                repair_work=work_budget, repair_gate=repair_gate_seconds,
                continuation_gate=control_gate_seconds, diagnostic=diagnostic_seconds))
    finally:
        m.bounds = LITERAL_BOUNDS


def worker(plan, out):
    bindings(plan)
    assigner = BucketAssigner(str(BASELINE/'buckets'))
    with inputs.Policy(assigner) as policy:
        start = perf_counter()
        corpus = inputs.capture(policy)
        write(out/'capture.json', corpus)
        write(out/'capture-timing.json', dict(seconds=perf_counter()-start))
        assert corpus['complete'], 'capture cap reached: no replacement cases'
        print(f"captured {len(corpus['rows'])} states in {corpus['census']['hands']} hands",
              flush=True)
        for j, row in enumerate(corpus['rows']):
            start = perf_counter()
            record = inputs.reconstruct(policy, assigner, row)
            range_seconds = perf_counter()-start
            write(out/f'input-{j:03d}.json', record)
            print(f'reconstructed {j+1}/4 in {range_seconds:.2f}s', flush=True)
            result = solve_case(record)
            result['range_seconds'] = range_seconds
            write(out/f'case-{j:03d}.json', result)
            print(f'completed {j+1}/4', flush=True)
            gc.collect()
    bindings(plan)
    write(out/'worker-complete.json', dict(complete=True, cases=4, lp_calls=24, gates=8))


def kernel_audit(game, kernel, x, y):
    # Each scaled coefficient is checked against float.as_integer_ratio, not frexp scaling.
    checked = 0
    for raw, integers in zip([game.check, *game.fold, *game.call], kernel.arrays):
        for value, integer in zip(raw.flat, integers.flat):
            n, den = float(value).as_integer_ratio()
            assert int(integer)*den == n*kernel.denominator
            checked += 1
    # Literal Fraction loops on disjointly chosen full-game rows/columns.
    for start in (0, 237, 811):
        ii = [(start+17*k) % 1081 for k in range(9)]
        jj = [(start+31*k+7) % 1081 for k in range(11)]
        sub = m.Game(game.check[np.ix_(ii, jj)], game.fold[:, ii][:, :, jj],
                     game.call[:, ii][:, :, jj])
        xx = [x[k] for k in ii]
        yy = [[row[k] for k in jj] for row in y]
        gs = [list(range(9)), list(range(11))]
        assert Kernel(sub).bounds(sub, xx, yy, gs) == LITERAL_BOUNDS(sub, xx, yy, gs)
    return checked


def verify_case(record, row):
    game, groups, details = inputs.build(record)
    assert row['inputs'] == details and row['groups'] == groups
    kernel = Kernel(game)
    m.bounds = kernel.bounds
    try:
        initial = row['initial']
        trainer = m.Trainer(game, groups)
        for _ in range(50000):
            trainer.step()
        x, y = trainer.average()
        assert (x, y) == (initial['x'], initial['y'])
        assert all(initial[k] == v for k, v in m.score(game, groups, x, y).items())
        m.verify(game, groups, row['original_solution'])
        values = kernel.values(row['original_solution']['seat0']['y'])
        assert row['values'] == [[str(v) for v in vs] for vs in values]
        assert row['proposal'] == r.exchange(groups[0], values)
        proposed = [row['proposal']['groups'], groups[1]]
        m.verify(game, proposed, row['proposed_solution'])
        assert row['original_solution']['seat1'] == row['proposed_solution']['seat1']
        for name, gs, point in (('repair', proposed, row['repaired']),
                               ('continuation', groups, row['continued'])):
            engine, replay = fit(game, gs, point['iteration'])
            assert replay['x'] == point['x']
            expected = r.accept(game, groups, x, y, gs, replay['x'])
            assert row['choices'][name] == expected
            assert Q(expected['score']['exploitability_exact']) <= Q(initial['exploitability_exact'])
        trace = row['continued']['trace']
        assert [t[0] for t in trace] == list(range(50250, row['continued']['iteration']+1, 250))
        active = [0.]+[t[1] for t in trace]
        assert all(a < b for a, b in zip(active, active[1:]))
        budget = row['times']['repair_work']
        assert active[-2] < budget <= active[-1] == row['continued']['seconds']
        assert budget == row['times']['witness_proposal']+row['repaired']['seconds']
        assert row['repaired']['iteration'] == 50000
        assert row['continued']['iteration'] <= 1050000
        xx, yy = m.expand(groups, x, y)
        count = kernel_audit(game, kernel, xx, yy)
        return count, 100000+row['continued']['iteration']
    finally:
        m.bounds = LITERAL_BOUNDS


def verify(plan, out):
    bindings(plan)
    def forbidden(*args, **kwargs):
        raise AssertionError('no new verifier LP solves')
    c.opt.linprog = forbidden
    corpus = read(out/'capture.json')
    assert corpus['complete'] and len(corpus['rows']) == 4
    assigner = BucketAssigner(str(BASELINE/'buckets'))
    checked, updates = 0, 0
    with inputs.Policy(assigner) as policy:
        assert inputs.capture(policy) == corpus
        print('capture replay identical', flush=True)
        for j, row in enumerate(corpus['rows']):
            record = inputs.reconstruct(policy, assigner, row)
            assert record == read(out/f'input-{j:03d}.json')
            # Redeal all twelve private cards, hold public history and board fixed.
            other = [v for v in range(52) if v not in row['board']][-12:]+row['board']
            changed = inputs.reconstruct(policy, assigner, dict(row, deck=other))
            assert changed['ranges'] == record['ranges']
            assert changed['hands'] == record['hands']
            count, replayed = verify_case(record, read(out/f'case-{j:03d}.json'))
            checked += count
            updates += replayed
            print(f'verified {j+1}/4', flush=True)
            gc.collect()
    bindings(plan)
    assert read(out/'worker-complete.json') == dict(complete=True, cases=4, lp_calls=24, gates=8)
    write(out/'audit.json', dict(passed=True, cases=4, replayed_updates=updates,
        exact_coefficients_checked=checked, literal_subgame_checks=12,
        private_card_invariance=4, exact_gates=8, certificate_pairs=12,
        capture_replayed=True, new_lp_calls=0))


if __name__ == '__main__':
    mode, path, expected = sys.argv[1:]
    assert digest(path) == expected
    if mode == 'run':
        d.runner.HERE, d.runner.bindings = HERE, bindings
        d.runner.run(Path(path), expected)
    else:
        plan = read(path)
        {'worker': worker, 'verify': verify}[mode](plan, Path(plan['output']))
