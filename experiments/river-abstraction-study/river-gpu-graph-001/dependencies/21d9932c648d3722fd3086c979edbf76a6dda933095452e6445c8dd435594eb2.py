"""Bounded diagnostic using the frozen one-board execution coordinator."""
from bridge import ROOT, HISTORY, c
from pathlib import Path
from fractions import Fraction as Q
from time import perf_counter
import importlib.util
import sys
import tracemalloc
import multi as m

HERE = Path(__file__).resolve().parent
NAME = 'multibet-group-diagnostic-001'
PRIOR = HISTORY/'witness-next-board-002'
INPUT = HISTORY/'witness-group-repair-confirmation-001'
read, write, digest = c.read, c.write, c.digest
spec = importlib.util.spec_from_file_location('frozen_coordinator',
                                            PRIOR/'verification-tools/experiment.py')
runner = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = runner
spec.loader.exec_module(runner)
MENUS = dict(half=[0], pot=[1], both=[0, 1])


def entries():
    boards = [read(INPUT/'plan.json')['boards'][i] for i in (0, 4, 8, 12)]
    return [e for e in c.entries_for(boards) if e['bet'] == 5]


def bindings(plan):
    assert plan['name'] == NAME and not tracemalloc.is_tracing()
    assert (plan['python'], plan['numpy'], plan['scipy']) == (
        sys.version, c.np.__version__, c.scipy.__version__)
    for path, expected in plan['pins'].items():
        assert digest(path) == expected, path
    assert plan['entries'] == entries() and len(plan['entries']) == 8
    assert plan['checkpoints'] == [10000, 50000] and plan['phase_timeout_seconds'] == 900


def build(entry):
    half, groups, inputs = c.build_case(entry)
    pot, _, extra = c.build_case(dict(case=entry['case'], bet=10))
    for key in ('hands', 'joint', 'ranges'):
        assert inputs[key] == extra[key]
    assert m.np.array_equal(half.joint, pot.joint)
    assert m.np.array_equal(half.check, pot.check) and m.np.array_equal(half.fold, pot.fold)
    return [half, pot], groups, dict(half=inputs, pot=extra)


def menu_game(matrices, name):
    return m.Game(matrices[0].check, [matrices[i].fold for i in MENUS[name]],
                  [matrices[i].call for i in MENUS[name]])


def worker(plan, out):
    bindings(plan)
    for i, entry in enumerate(plan['entries']):
        matrices, groups, inputs = build(entry)
        menus = {}
        order = list(MENUS) if i % 2 == 0 else list(reversed(MENUS))
        for name in order:
            game = menu_game(matrices, name)
            start = perf_counter()
            solution = m.solve(game, groups)
            reference = m.pair(game, [list(range(n)) for n in game.check.shape])
            lp_seconds = perf_counter()-start
            start = perf_counter()
            engine = m.Trainer(game, groups)
            setup = perf_counter()-start
            records, active = [], 0.
            for checkpoint in plan['checkpoints']:
                start = perf_counter()
                while engine.iteration < checkpoint:
                    engine.step()
                active += perf_counter()-start
                x, y = engine.average()
                records.append(dict(iteration=checkpoint, x=x, y=y, active_seconds=active,
                    setup_seconds=setup, **m.score(game, groups, x, y)))
            menus[name] = dict(solution=solution, reference=reference, records=records,
                               lp_seconds=lp_seconds)
            if name == 'both':
                menus[name]['conflict'] = m.size_conflict(game, groups[0], solution['seat0']['y'])
        write(out/f'case-{i:03d}.json', dict(entry=entry, groups=groups,
                                           inputs=inputs, menus=menus))
        print(f'completed {i+1}/8', flush=True)
    bindings(plan)
    write(out/'worker-complete.json', dict(complete=True, cases=8, lp_calls=144, trajectories=24))


def verify(plan, out):
    bindings(plan)
    def forbidden(*args, **kwargs):
        raise AssertionError('verifier LP forbidden')
    c.opt.linprog = forbidden
    updates = 0
    for i, entry in enumerate(plan['entries']):
        matrices, groups, inputs = build(entry)
        row = read(out/f'case-{i:03d}.json')
        assert row['entry'] == entry and row['groups'] == groups and row['inputs'] == inputs
        assert set(row['menus']) == set(MENUS)
        for name, result in row['menus'].items():
            game = menu_game(matrices, name)
            m.verify(game, groups, result['solution'])
            ref = result['reference']
            bound = m.bounds(game, ref['x'], ref['y'], [list(range(n)) for n in game.check.shape])
            assert ref['bounds'] == list(map(str, bound)) and bound[1]-bound[0] <= Q('1e-8')
            engine = m.Trainer(game, groups)
            assert [r['iteration'] for r in result['records']] == plan['checkpoints']
            for record in result['records']:
                while engine.iteration < record['iteration']:
                    engine.step()
                    updates += 1
                x, y = engine.average()
                assert x == record['x'] and y == record['y']
                score = m.score(game, groups, x, y)
                assert all(record[k] == v for k, v in score.items())
                assert Q(score['exploitability_exact']) >= Q(result['solution']['floor'][0])
                if name != 'both':
                    low, high = c.core.exact_bounds(matrices[MENUS[name][0]], c.weights(groups),
                        [m.np.array(x)[:, 1].tolist(), y[0]], unrestricted=True)
                    assert abs(float((high-low)/2)-score['exploitability']) <= 1e-12
            if name == 'both':
                assert result['conflict'] == m.size_conflict(game, groups[0],
                                                            result['solution']['seat0']['y'])
        print(f'verified {i+1}/8', flush=True)
    bindings(plan)
    assert read(out/'worker-complete.json') == dict(complete=True, cases=8,
                                                  lp_calls=144, trajectories=24)
    write(out/'audit.json', dict(passed=True, cases=8, certificates=72,
        replayed_updates=updates, profiles=48, legacy_profile_crosschecks=32,
        new_verifier_lp_calls=0))


if __name__ == '__main__':
    mode, path, expected = sys.argv[1:]
    assert digest(path) == expected
    if mode == 'run':
        runner.HERE, runner.bindings = HERE, bindings
        runner.run(Path(path), expected)
    else:
        plan = read(path)
        {'worker': worker, 'verify': verify}[mode](plan, Path(plan['output']))
