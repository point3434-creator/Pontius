"""One unused board through the frozen two-repair and continuation procedures."""
from bridge import ROOT, HISTORY, c, gate
from pathlib import Path
from fractions import Fraction as Q
from hashlib import sha256
from itertools import permutations
from time import perf_counter
import importlib.util
import subprocess
import sys
import tracemalloc

HERE = Path(__file__).resolve().parent
NAME = 'witness-next-board-002'
PRIOR = HISTORY/'witness-compute-matched-continuation-001'
spec = importlib.util.spec_from_file_location('frozen_timing',
                                            PRIOR/'verification-tools/experiment.py')
timing = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = timing
spec.loader.exec_module(timing)
read, write, digest = c.read, c.write, c.digest


def select(excluded):
    used = set(map(c.canonical_board, excluded))
    for attempt in range(10000):
        def order(card):
            return sha256(f'{c.SEED}|board|{attempt}|{card}'.encode()).digest(), card
        board = sorted(sorted(range(52), key=order)[:5])
        if c.canonical_board(board) not in used:
            return dict(board=board, attempt=attempt, texture=c.texture(board))
    raise ValueError('board selection exhausted')


def novelty(plan):
    board = plan['selection']['board']
    for old in plan['excluded_boards']:
        for p in permutations(range(4)):
            assert sorted(4*(v//4)+p[v%4] for v in board) != sorted(old)


def bindings(plan):
    assert plan['name'] == NAME and not tracemalloc.is_tracing()
    assert (plan['python'], plan['numpy'], plan['scipy']) == (
        sys.version, c.np.__version__, c.scipy.__version__)
    for path, expected in plan['pins'].items():
        assert digest(path) == expected, path
    assert plan['selection'] == select(plan['excluded_boards'])
    assert plan['entries'] == c.entries_for([plan['selection']['board']])
    assert len(plan['entries']) == 4 and plan['phase_timeout_seconds'] == 900
    novelty(plan)


def choose(matrix, groups, coeff, proposed, candidate):
    start = perf_counter()
    accepted = gate.select(matrix, groups, coeff, proposed, candidate)
    elapsed = perf_counter()-start
    return dict(gate=accepted, gate_seconds=elapsed,
                selected_score=c.score(matrix, accepted['groups'], accepted['coefficients']))


def worker(plan, out):
    bindings(plan)
    for i, entry in enumerate(plan['entries']):
        matrix, initial_groups, inputs = c.build_case(entry)
        initial = c.train(matrix, initial_groups, [10000])[0]
        groups, coeff = initial_groups, initial['coefficients']
        stages = []
        for step in (1, 2):
            start = perf_counter()
            witness = c.core.solve(matrix, c.weights(groups))
            witness_seconds = perf_counter()-start
            start = perf_counter()
            proposal = c.repair.propose(matrix, groups, witness)
            proposal_seconds = perf_counter()-start
            records = c.train(matrix, proposal['groups'], [1000, 10000])
            chosen = choose(matrix, groups, coeff, proposal['groups'], records[-1]['coefficients'])
            stages.append(dict(step=step, incumbent_groups=groups, incumbent_coefficients=coeff,
                witness=witness, witness_seconds=witness_seconds, proposal=proposal,
                proposal_seconds=proposal_seconds, records=records, **chosen))
            groups, coeff = chosen['gate']['groups'], chosen['gate']['coefficients']
        second = stages[1]
        groups, coeff = second['incumbent_groups'], second['incumbent_coefficients']
        engine = c.core.RegretBR(matrix, c.weights(groups))
        while engine.iteration < 10000:
            engine.step()
        assert [v.tolist() for v in engine.average()] == coeff
        train = second['records'][-1]
        work = second['witness_seconds']+second['proposal_seconds']
        work += train['setup_seconds']+train['active_seconds']
        budgets = dict(work_seconds=work, total_seconds=work+second['gate_seconds'])
        timed = timing.timed_continue(engine, work, budgets['total_seconds'])
        records = {}
        for name in ('matched', 'generous'):
            point = timed[name]
            chosen = choose(matrix, groups, coeff, groups, point['coefficients'])
            records[name] = dict(**point, **chosen,
                raw=c.score(matrix, groups, point['coefficients']),
                total_component_seconds=point['active_seconds']+chosen['gate_seconds'])
        write(out/f'case-{i:03d}.json', dict(entry=entry, inputs=inputs,
            initial_groups=initial_groups, initial=initial, stages=stages,
            budgets=budgets, trace=timed['trace'], records=records))
        print(f'completed {i+1}/4', flush=True)
    bindings(plan)
    write(out/'worker-complete.json', dict(complete=True, cases=4, lp_calls=16, gates=16))


def verify_policy(matrix, groups, record):
    assert c.score(matrix, groups, record['coefficients']) == {
        k: record[k] for k in c.score(matrix, groups, record['coefficients'])}


def verify_gate(matrix, groups, coeff, proposed, candidate, record):
    expected = gate.select(matrix, groups, coeff, proposed, candidate)
    assert expected == record['gate']
    scored = [c.score(matrix, gs, ps) for gs, ps in ((groups, coeff), (proposed, candidate))]
    pairs = [gate.audit_security(matrix, [list(map(Q, p)) for p in s['hand_probabilities']])
             for s in scored]
    assert expected['security_exact'] == [[str(v) for v in p] for p in pairs]
    assert expected['accepted'] == [pairs[1][s] >= pairs[0][s] for s in (0, 1)]
    value = -sum((pairs[int(expected['accepted'][s])][s] for s in (0, 1)), Q(0))/2
    assert c.score(matrix, expected['groups'], expected['coefficients']) == record['selected_score']
    assert Q(record['selected_score']['exact_exploitability']) == value <= Q(
        scored[0]['exact_exploitability'])


def verify(plan, out):
    bindings(plan)
    def forbidden(*args, **kwargs):
        raise AssertionError('verifier LP forbidden')
    c.opt.linprog = forbidden
    updates, exchanges, rows = 0, 0, []
    for i, entry in enumerate(plan['entries']):
        row = read(out/f'case-{i:03d}.json')
        matrix, groups, inputs = c.build_case(entry)
        assert row['entry'] == entry and row['inputs'] == inputs and row['initial_groups'] == groups
        def replay(gs, records):
            nonlocal updates
            engine = c.core.RegretBR(matrix, c.weights(gs))
            for r in records:
                while engine.iteration < r['iteration']:
                    engine.step()
                    updates += 1
                assert [v.tolist() for v in engine.average()] == r['coefficients']
            return engine
        replay(groups, [row['initial']])
        verify_policy(matrix, groups, row['initial'])
        coeff = row['initial']['coefficients']
        assert len(row['stages']) == 2
        for step, stage in enumerate(row['stages'], 1):
            assert stage['step'] == step and stage['incumbent_groups'] == groups
            assert stage['incumbent_coefficients'] == coeff
            c.core.verify(matrix, c.weights(groups), stage['witness'])
            proposal = c.repair.propose(matrix, groups, stage['witness'])
            assert proposal == stage['proposal']
            for s in (0, 1):
                delta = list(map(Q, proposal['seats'][s]['weighted_advantages_exact']))
                check = c.frozen.independent_exchange(groups[s], delta)
                assert all(proposal['seats'][s][k] == v for k, v in check.items())
                exchanges += check['examined_exchanges']
            assert [r['iteration'] for r in stage['records']] == [1000, 10000]
            replay(proposal['groups'], stage['records'])
            for r in stage['records']:
                verify_policy(matrix, proposal['groups'], r)
            verify_gate(matrix, groups, coeff, proposal['groups'],
                        stage['records'][-1]['coefficients'], stage)
            groups, coeff = stage['gate']['groups'], stage['gate']['coefficients']
        stage = row['stages'][1]
        train = stage['records'][-1]
        work = stage['witness_seconds']+stage['proposal_seconds']
        work += train['setup_seconds']+train['active_seconds']
        assert row['budgets'] == dict(work_seconds=work,
                                     total_seconds=work+stage['gate_seconds'])
        timing.verify_trace(row)
        groups, coeff = stage['incumbent_groups'], stage['incumbent_coefficients']
        points = [row['records'][n] for n in ('matched', 'generous')]
        replay(groups, [dict(iteration=10000, coefficients=coeff), *points])
        for point in points:
            assert c.score(matrix, groups, point['coefficients']) == point['raw']
            verify_gate(matrix, groups, coeff, groups, point['coefficients'], point)
            assert point['total_component_seconds'] == point['active_seconds']+point['gate_seconds']
            assert Q(point['selected_score']['exact_exploitability']) >= Q(
                stage['witness']['minimum_exploitability']['lower_exact'])
        rows.append(row)
        print(f'verified {i+1}/4', flush=True)
    bindings(plan)
    assert read(out/'worker-complete.json') == dict(complete=True, cases=4, lp_calls=16, gates=16)
    write(out/'audit.json', dict(passed=True, cases=4, replayed_updates=updates,
        asymmetric_certificates=16, independent_exchanges=exchanges, independent_gate_audits=16,
        new_verifier_lp_calls=0))


def run(path, expected):
    assert digest(path) == expected
    plan = read(path)
    bindings(plan)
    out = Path(plan['output'])
    out.mkdir(parents=True, exist_ok=False)
    started = perf_counter()
    try:
        write(out/'plan.json', plan)
        for mode in ('worker', 'verify'):
            start = perf_counter()
            command = [sys.executable, '-B', '-W', 'error::ResourceWarning',
                       str(HERE/'experiment.py'), mode, str(path), expected]
            with (out/(mode+'-stdout.txt')).open('xb') as stdout, \
                 (out/(mode+'-stderr.txt')).open('xb') as stderr:
                result = subprocess.run(command, cwd=HERE, stdout=stdout, stderr=stderr,
                                        timeout=plan['phase_timeout_seconds'])
            write(out/(mode+'-receipt.json'), dict(exit=result.returncode,
                seconds=perf_counter()-start, command=command))
            assert result.returncode == 0, mode+' failed'
        bindings(plan)
        write(out/'results-manifest.json', {p.name: digest(p) for p in sorted(out.iterdir())
                                           if p.is_file()})
        write(out/'receipt.json', dict(exit=0, seconds=perf_counter()-started,
            result_manifest_sha256=digest(out/'results-manifest.json')))
    except BaseException as error:
        write(out/'failed.json', dict(error=type(error).__name__, message=str(error)))
        raise


if __name__ == '__main__':
    mode, path, expected = sys.argv[1:]
    assert digest(path) == expected
    if mode == 'run':
        run(Path(path), expected)
    else:
        plan = read(path)
        {'worker': worker, 'verify': verify}[mode](plan, Path(plan['output']))
