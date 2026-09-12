"""One size-aware bettor repair against a frozen caller and continuation control."""
from support import ROOT, HISTORY, PRIOR, c, m, d
from pathlib import Path
from fractions import Fraction as Q
from time import perf_counter
from itertools import combinations
import sys
import tracemalloc
import size_repair as r

HERE = Path(__file__).resolve().parent
NAME = 'multibet-size-repair-001'
read, write, digest = c.read, c.write, c.digest


def bindings(plan):
    assert plan['name'] == NAME and not tracemalloc.is_tracing()
    assert (plan['python'], plan['numpy'], plan['scipy']) == (
        sys.version, c.np.__version__, c.scipy.__version__)
    for path, expected in plan['pins'].items():
        assert digest(path) == expected, path
    assert plan['sources'] == [str(PRIOR/f'case-{i:03d}.json') for i in range(8)]
    assert plan['phase_timeout_seconds'] == 900


def build(path):
    old = read(path)
    matrices, groups, inputs = d.build(old['entry'])
    assert inputs == old['inputs'] and groups == old['groups']
    game = d.menu_game(matrices, 'both')
    record = old['menus']['both']
    m.verify(game, groups, record['solution'])
    policy = record['records'][-1]
    assert policy['iteration'] == 50000
    assert all(policy[k] == v for k, v in m.score(game, groups, policy['x'], policy['y']).items())
    return old, game, groups, record


def train(game, groups, checkpoints):
    start = perf_counter()
    engine = r.Bettor(game, groups)
    setup = perf_counter()-start
    active, records = 0., []
    for checkpoint in checkpoints:
        start = perf_counter()
        while engine.iteration < checkpoint:
            engine.step()
        active += perf_counter()-start
        records.append(dict(iteration=checkpoint, x=engine.average(),
                            setup_seconds=setup, active_seconds=active))
    return records


def worker(plan, out):
    bindings(plan)
    for i, path in enumerate(plan['sources']):
        old, game, groups, record = build(path)
        initial = record['records'][-1]
        start = perf_counter()
        values = r.action_values(game, record['solution']['seat0']['y'])
        proposal = r.exchange(groups[0], values)
        proposal_seconds = perf_counter()-start
        proposed = [proposal['groups'], groups[1]]
        records = {}
        for name in (('repair', 'control') if i % 2 == 0 else ('control', 'repair')):
            records[name] = train(game, proposed if name == 'repair' else groups,
                                  [10000, 50000] if name == 'repair' else [50000, 100000])
        assert records['control'][0]['x'] == initial['x']
        choices = {}
        for name, gs in (('repair', proposed), ('control', groups)):
            for point in records[name]:
                point.update(m.score(game, gs, point['x'], initial['y']))
            start = perf_counter()
            choices[name] = r.accept(game, groups, initial['x'], initial['y'], gs,
                                     records[name][-1]['x'])
            choices[name]['seconds'] = perf_counter()-start
        start = perf_counter()
        first = m.pair(game, [proposed[0], list(range(game.check.shape[1]))])
        second = record['solution']['seat1']
        l0, u0 = map(Q, first['bounds'])
        l1, u1 = map(Q, second['bounds'])
        solution = dict(seat0=first, seat1=second,
                        floor=list(map(str, (max(Q(0), (l1-u0)/2), (u1-l0)/2))))
        diagnostic_seconds = perf_counter()-start
        write(out/f'case-{i:03d}.json', dict(source_path=path, source_sha256=digest(path),
            entry=old['entry'], proposal=proposal, values=[[str(v) for v in vs] for vs in values],
            records=records, choices=choices, solution=solution,
            proposal_seconds=proposal_seconds, diagnostic_seconds=diagnostic_seconds))
        print(f'completed {i+1}/8', flush=True)
    bindings(plan)
    write(out/'worker-complete.json', dict(complete=True, cases=8, lp_calls=16,
                                          bettor_trajectories=16, decisions=16))


def enumerate_proposal(groups, values):
    """Rebuild every candidate partition and score it directly, independent of gain formula."""
    best, operation, examined = Q(0), None, 0
    k = len(set(groups))
    base = r.objective(groups, values)
    for split in range(k):
        sides = {v[2] > v[1] for g, v in zip(groups, values) if g == split}
        if len(sides) < 2:
            continue
        for a, b in combinations([g for g in range(k) if g != split], 2):
            candidate = [k if g == split and v[2] > v[1] else a if g == b else g
                         for g, v in zip(groups, values)]
            gain = r.objective(candidate, values)-base
            examined += 1
            if gain > best:
                best, operation = gain, [split, a, b]
    return dict(net_gain=str(best), operation=operation, examined=examined)


def verify(plan, out):
    bindings(plan)
    def forbidden(*args, **kwargs):
        raise AssertionError('verifier LP forbidden')
    c.opt.linprog = forbidden
    updates, examined = 0, 0
    for i, path in enumerate(plan['sources']):
        old, game, groups, original = build(path)
        row = read(out/f'case-{i:03d}.json')
        assert row['source_path'] == path and row['source_sha256'] == digest(path)
        assert row['entry'] == old['entry']
        initial = original['records'][-1]
        values = r.action_values(game, original['solution']['seat0']['y'])
        assert row['values'] == [[str(v) for v in vs] for vs in values]
        assert row['proposal'] == r.exchange(groups[0], values)
        enumeration = enumerate_proposal(groups[0], values)
        assert all(row['proposal'][k] == v for k, v in enumeration.items())
        examined += enumeration['examined']
        proposed = [row['proposal']['groups'], groups[1]]
        m.verify(game, proposed, row['solution'])
        for name, gs, checkpoints in [('repair', proposed, [10000, 50000]),
                                     ('control', groups, [50000, 100000])]:
            engine = r.Bettor(game, gs)
            assert [p['iteration'] for p in row['records'][name]] == checkpoints
            for point in row['records'][name]:
                while engine.iteration < point['iteration']:
                    engine.step()
                    updates += 1
                assert engine.average() == point['x']
                score = m.score(game, gs, point['x'], initial['y'])
                assert all(point[k] == v for k, v in score.items())
            choice = row['choices'][name]
            expected = r.accept(game, groups, initial['x'], initial['y'], gs, engine.average())
            assert all(choice[k] == v for k, v in expected.items())
            before = r.audit_security(game, groups, initial['x'], initial['y'])
            after = r.audit_security(game, gs, engine.average(), initial['y'])
            assert before == Q(choice['old_bounds'][0]) and after == Q(choice['new_bounds'][0])
            assert choice['accepted'] == (after >= before)
            assert Q(choice['score']['exploitability_exact']) <= Q(initial['exploitability_exact'])
            assert choice['y'] == initial['y'] and choice['groups'][1] == groups[1]
        assert row['records']['control'][0]['x'] == initial['x']
        print(f'verified {i+1}/8', flush=True)
    bindings(plan)
    assert read(out/'worker-complete.json') == dict(complete=True, cases=8, lp_calls=16,
                                                   bettor_trajectories=16, decisions=16)
    write(out/'audit.json', dict(passed=True, cases=8, replayed_updates=updates,
        proposed_certificates=16, incumbent_certificates=16, independent_gate_audits=16,
        enumerated_partitions=examined, new_verifier_lp_calls=0))


if __name__ == '__main__':
    mode, path, expected = sys.argv[1:]
    assert digest(path) == expected
    if mode == 'run':
        d.runner.HERE, d.runner.bindings = HERE, bindings
        d.runner.run(Path(path), expected)
    else:
        plan = read(path)
        {'worker': worker, 'verify': verify}[mode](plan, Path(plan['output']))
