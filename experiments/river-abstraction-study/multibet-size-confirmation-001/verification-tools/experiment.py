"""Fresh-board preparation followed by the unchanged, census-adjusted pilot."""
from support import ROOT, HISTORY, c, m, d
from pathlib import Path
from fractions import Fraction as Q
from itertools import permutations
from time import perf_counter
import sys
import tracemalloc
import pilot

HERE = Path(__file__).resolve().parent
NAME = 'multibet-size-confirmation-001'
PILOT = HISTORY/'multibet-size-repair-001'
read, write, digest = c.read, c.write, c.digest


def novelty(plan):
    for i, board in enumerate(plan['boards']):
        for old in [*plan['excluded_boards'], *plan['boards'][:i]]:
            assert all(sorted(4*(v//4)+p[v%4] for v in board) != sorted(old)
                       for p in permutations(range(4)))


def bindings(plan):
    assert plan['name'] == NAME and not tracemalloc.is_tracing()
    assert (plan['python'], plan['numpy'], plan['scipy']) == (
        sys.version, c.np.__version__, c.scipy.__version__)
    for path, expected in plan['pins'].items():
        assert digest(path) == expected, path
    boards, receipt = c.select_boards(plan['excluded_boards'], per_texture=2)
    assert boards == plan['boards'] and receipt == plan['selection_receipt']
    assert plan['entries'] == [e for e in c.entries_for(boards) if e['bet'] == 5]
    assert len(boards) == 8 and len(plan['entries']) == 16
    assert plan['sources'] == [str(Path(plan['output'])/'baseline'/f'case-{i:03d}.json')
                               for i in range(16)]
    assert plan['phase_timeout_seconds'] == 900
    novelty(plan)


def worker(plan, out):
    bindings(plan)
    baseline = out/'baseline'
    baseline.mkdir(exist_ok=False)
    for i, entry in enumerate(plan['entries']):
        matrices, groups, inputs = d.build(entry)
        game = d.menu_game(matrices, 'both')
        start = perf_counter()
        first = m.pair(game, [groups[0], list(range(game.check.shape[1]))])
        witness_seconds = perf_counter()-start
        start = perf_counter()
        second = m.pair(game, [list(range(game.check.shape[0])), groups[1]])
        caller_certificate_seconds = perf_counter()-start
        l0, u0 = map(Q, first['bounds'])
        l1, u1 = map(Q, second['bounds'])
        solution = dict(seat0=first, seat1=second,
                        floor=list(map(str, (max(Q(0), (l1-u0)/2), (u1-l0)/2))))
        m.verify(game, groups, solution)
        start = perf_counter()
        trainer = m.Trainer(game, groups)
        while trainer.iteration < 50000:
            trainer.step()
        training_seconds = perf_counter()-start
        x, y = trainer.average()
        record = dict(iteration=50000, x=x, y=y, **m.score(game, groups, x, y))
        write(baseline/f'case-{i:03d}.json', dict(entry=entry, groups=groups, inputs=inputs,
            menus=dict(both=dict(solution=solution, records=[record])),
            witness_seconds=witness_seconds, caller_certificate_seconds=caller_certificate_seconds,
            initial_training_seconds=training_seconds))
        print(f'prepared {i+1}/16', flush=True)
    write(out/'baseline-manifest.json', {p.name: digest(p) for p in sorted(baseline.iterdir())})
    pilot.bindings = bindings
    pilot.worker(plan, out)


def verify(plan, out):
    bindings(plan)
    def forbidden(*args, **kwargs):
        raise AssertionError('verifier LP forbidden')
    c.opt.linprog = forbidden
    manifest = read(out/'baseline-manifest.json')
    assert set(manifest) == {f'case-{i:03d}.json' for i in range(16)}
    for i, entry in enumerate(plan['entries']):
        path = Path(plan['sources'][i])
        assert digest(path) == manifest[path.name]
        old, game, groups, original = pilot.build(path)
        assert old['entry'] == entry
        trainer = m.Trainer(game, groups)
        while trainer.iteration < 50000:
            trainer.step()
        x, y = trainer.average()
        record = original['records'][0]
        assert record['x'] == x and record['y'] == y
        print(f'baseline verified {i+1}/16', flush=True)
    write(out/'baseline-audit.json', dict(passed=True, cases=16,
        joint_role_updates=800000, asymmetric_certificates=32, new_lp_calls=0))
    pilot.bindings = bindings
    pilot.verify(plan, out)


if __name__ == '__main__':
    mode, path, expected = sys.argv[1:]
    assert digest(path) == expected
    if mode == 'run':
        d.runner.HERE, d.runner.bindings = HERE, bindings
        d.runner.run(Path(path), expected)
    else:
        plan = read(path)
        {'worker': worker, 'verify': verify}[mode](plan, Path(plan['output']))
