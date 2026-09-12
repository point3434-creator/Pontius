"""Second guarded repair versus guarded continuation from the retained first step."""
from support import ROOT, HISTORY, PRIOR, c, gate
from pathlib import Path
from fractions import Fraction as Q
from time import perf_counter
from collections import Counter
import sys
import subprocess
import tracemalloc

HERE = Path(__file__).resolve().parent
NAME = 'witness-second-guarded-repair-001'
read, write, digest = c.read, c.write, c.digest


def incumbent(row):
    return row['gate']['groups'], row['gate']['coefficients']


def continuation_cost(records):
    c.opt.require([r['iteration'] for r in records] == [10000, 20000], 'wrong continuation budget')
    value = records[1]['active_seconds']-records[0]['active_seconds']
    c.opt.require(value >= 0, 'negative continuation cost')
    return value


def bindings(plan):
    assert plan['name'] == NAME and not tracemalloc.is_tracing()
    assert plan['python'] == sys.version and plan['numpy'] == c.np.__version__
    assert plan['scipy'] == c.scipy.__version__
    for path, expected in plan['pins'].items():
        assert digest(path) == expected, path
    assert plan['sources'] == [str(PRIOR/f'case-{i:03d}.json') for i in range(64)]
    assert plan['control_checkpoints'] == [10000, 20000]
    assert plan['repaired_checkpoints'] == [1000, 10000]
    assert plan['phase_timeout_seconds'] == 900


def load_case(path):
    previous = read(path)
    matrix, original_groups, inputs = c.build_case(previous['entry'])
    assert inputs == previous['inputs'] and original_groups == previous['baseline_groups']
    groups, coefficients = incumbent(previous)
    assert c.score(matrix, groups, coefficients) == previous['selected_score']
    assert all(len(set(gs)) == 16 for gs in groups)
    return previous, matrix, groups, coefficients


def worker(plan, out):
    bindings(plan)
    for i, path in enumerate(plan['sources']):
        start = perf_counter()
        previous, matrix, groups, coefficients = load_case(path)
        preparation = perf_counter()-start
        start = perf_counter()
        baseline = c.core.solve(matrix, c.weights(groups))
        witness_seconds = perf_counter()-start
        start = perf_counter()
        proposal = c.repair.propose(matrix, groups, baseline)
        proposal_seconds = perf_counter()-start
        records = {}
        for name in (('repaired', 'control') if i % 2 == 0 else ('control', 'repaired')):
            gs = proposal['groups'] if name == 'repaired' else groups
            records[name] = c.train(matrix, gs, plan[name+'_checkpoints'])
        assert records['control'][0]['coefficients'] == coefficients, 'incumbent replay changed'
        assert records['control'][0]['exact_exploitability'] == (
            previous['selected_score']['exact_exploitability'])
        start = perf_counter()
        second = gate.select(matrix, groups, coefficients, proposal['groups'],
                             records['repaired'][1]['coefficients'])
        gate_seconds = perf_counter()-start
        start = perf_counter()
        continued = gate.select(matrix, groups, coefficients, groups,
                                records['control'][1]['coefficients'])
        continuation_gate_seconds = perf_counter()-start
        second_score = c.score(matrix, second['groups'], second['coefficients'])
        continuation_score = c.score(matrix, continued['groups'], continued['coefficients'])
        start = perf_counter()
        solution = c.core.solve(matrix, c.weights(proposal['groups']))
        diagnostic_seconds = perf_counter()-start
        write(out/f'case-{i:03d}.json', dict(entry=previous['entry'], source_path=path,
            source_sha256=digest(path), incumbent_groups=groups,
            incumbent_coefficients=coefficients,
            incumbent_score=previous['selected_score'], baseline=baseline, proposal=proposal,
            original10k=previous['records']['control'][0]['exact_exploitability'],
            solution=solution, records=records, repair_gate=second, continuation_gate=continued,
            second_score=second_score, continuation_score=continuation_score,
            preparation_seconds=preparation, baseline_lp_seconds=witness_seconds,
            proposal_seconds=proposal_seconds, gate_seconds=gate_seconds,
            continuation_gate_seconds=continuation_gate_seconds,
            continuation_update_seconds=continuation_cost(records['control']),
            diagnostic_lp_seconds=diagnostic_seconds))
        print(f'completed {i+1}/64: {previous["entry"]["case"]["id"]}', flush=True)
    bindings(plan)
    write(out/'worker-complete.json', dict(complete=True, cases=64, lp_calls=256,
                                         trajectories=128, gates=128, fitting_tasks=0))


def values(row):
    return dict(original10k=Q(row['original10k']),
        incumbent=Q(row['incumbent_score']['exact_exploitability']),
        raw_second=Q(row['records']['repaired'][1]['exact_exploitability']),
        second=Q(row['second_score']['exact_exploitability']),
        continuation=Q(row['continuation_score']['exact_exploitability']))


def stats(rows):
    vs = [values(r) for r in rows]
    means = {k: sum(v[k] for v in vs)/len(vs) for k in vs[0]}
    def directions(method, reference):
        return dict(Counter('better' if v[method] < v[reference] else
                            'worse' if v[method] > v[reference] else 'equal' for v in vs))
    return dict(cases=len(rows), means_exact={k: str(v) for k, v in means.items()},
        means={k: float(v) for k, v in means.items()},
        delta_exact=str(means['second']-means['incumbent']),
        versus_continuation_exact=str(means['second']-means['continuation']),
        raw_directions=directions('raw_second', 'incumbent'),
        second_directions=directions('second', 'incumbent'),
        continuation_directions=directions('continuation', 'incumbent'),
        versus_continuation_directions=directions('second', 'continuation'),
        changed_seats=sum(s['changed'] for r in rows for s in r['proposal']['seats']),
        accepted_changed_seats=sum(r['repair_gate']['accepted'][s] and
            r['proposal']['seats'][s]['changed'] for r in rows for s in (0, 1)))


def summarize(rows):
    panels = {}
    for bet in (5, 10):
        rs = [r for r in rows if r['entry']['bet'] == bet]
        panel = dict(overall=stats(rs))
        for category, key in [('boards', 'board_index'), ('textures', 'texture'),
                              ('regimes', 'regime'), ('leave_one_board_out', 'board_index')]:
            panel[category] = {str(v): stats([r for r in rs if
                (r['entry']['case'][key] == v) != (category == 'leave_one_board_out')])
                for v in sorted({r['entry']['case'][key] for r in rs})}
        panels[str(bet)] = panel
    safe = all(v['second'] <= v['incumbent'] and v['continuation'] <= v['incumbent']
               for v in map(values, rows))
    half = panels['5']['overall']
    return dict(complete=True, panels=panels, flags=dict(exact_nonregression=safe,
        useful_second_half_pot=safe and Q(half['delta_exact']) < -Q('1e-6'),
        beats_continuation_half_pot=safe and Q(half['versus_continuation_exact']) < -Q('1e-6')))


def verify_choice(matrix, row, name, candidate, candidate_groups):
    coefficients, groups = row['incumbent_coefficients'], row['incumbent_groups']
    decision = row[name+'_gate']
    assert decision == gate.select(matrix, groups, coefficients, candidate_groups,
                                   candidate['coefficients'])
    pair = [gate.audit_security(matrix, [list(map(Q, ps)) for ps in record['hand_probabilities']])
            for record in (row['incumbent_score'], candidate)]
    assert [[str(x) for x in p] for p in pair] == decision['security_exact']
    assert decision['accepted'] == [pair[1][s] >= pair[0][s] for s in (0, 1)]
    expected = -sum((pair[int(decision['accepted'][s])][s] for s in (0, 1)), Q(0))/2
    scored = c.score(matrix, decision['groups'], decision['coefficients'])
    target = 'second_score' if name == 'repair' else 'continuation_score'
    assert scored == row[target]
    assert Q(scored['exact_exploitability']) == expected <= Q(
        row['incumbent_score']['exact_exploitability'])


def verify(plan, out):
    bindings(plan)
    def forbidden(*args, **kwargs):
        raise AssertionError('verifier LP forbidden')
    c.opt.linprog = forbidden
    rows, replayed, examined = [], 0, 0
    for i, path in enumerate(plan['sources']):
        previous, matrix, groups, coefficients = load_case(path)
        row = read(out/f'case-{i:03d}.json')
        assert row['entry'] == previous['entry'] and row['source_sha256'] == digest(path)
        assert row['source_path'] == path and row['incumbent_groups'] == groups
        assert row['incumbent_coefficients'] == coefficients
        assert row['incumbent_score'] == previous['selected_score']
        assert row['original10k'] == previous['records']['control'][0]['exact_exploitability']
        c.core.verify(matrix, c.weights(groups), row['baseline'])
        proposal = c.repair.propose(matrix, groups, row['baseline'])
        assert proposal == row['proposal']
        for s in (0, 1):
            changes = list(map(Q, proposal['seats'][s]['weighted_advantages_exact']))
            check = c.frozen.independent_exchange(groups[s], changes)
            assert all(proposal['seats'][s][k] == v for k, v in check.items())
            examined += check['examined_exchanges']
        c.core.verify(matrix, c.weights(proposal['groups']), row['solution'])
        for name, gs, solution in [('control', groups, row['baseline']),
                                  ('repaired', proposal['groups'], row['solution'])]:
            records = row['records'][name]
            assert [r['iteration'] for r in records] == plan[name+'_checkpoints']
            engine = c.core.RegretBR(matrix, c.weights(gs))
            for record in records:
                while engine.iteration < record['iteration']:
                    engine.step()
                    replayed += 1
                policy = [v.tolist() for v in engine.average()]
                assert policy == record['coefficients']
                scored = c.score(matrix, gs, policy)
                assert all(record[k] == v for k, v in scored.items())
                assert Q(scored['exact_exploitability']) >= Q(
                    solution['minimum_exploitability']['lower_exact'])
        assert row['records']['control'][0]['coefficients'] == coefficients
        assert row['continuation_update_seconds'] == continuation_cost(row['records']['control'])
        verify_choice(matrix, row, 'repair', row['records']['repaired'][1], proposal['groups'])
        verify_choice(matrix, row, 'continuation', row['records']['control'][1], groups)
        rows.append(row)
        print(f'verified {i+1}/64', flush=True)
    assert read(out/'worker-complete.json') == dict(complete=True, cases=64, lp_calls=256,
                                                   trajectories=128, gates=128, fitting_tasks=0)
    bindings(plan)
    write(out/'summary.json', summarize(rows))
    write(out/'audit.json', dict(passed=True, cases=64, asymmetric_certificates=256,
        saved_profiles=256, selected_profiles=128, retained_incumbents=64,
        replayed_updates=replayed, independently_enumerated_exchanges=examined,
        independent_gate_audits=128, verifier_lp_calls=0, model_fits=0))


def run(path, expected):
    assert digest(path) == expected
    plan = read(path)
    bindings(plan)
    out = Path(plan['output'])
    out.mkdir(parents=True, exist_ok=False)
    start = perf_counter()
    try:
        write(out/'plan.json', plan)
        write(out/'started.json', dict(plan_sha256=expected))
        for mode in ('worker', 'verify'):
            command = [sys.executable, '-B', '-W', 'error::ResourceWarning',
                       str(HERE/'experiment.py'), mode, str(path), expected]
            begin = perf_counter()
            with (out/(mode+'-stdout.txt')).open('xb') as stdout, \
                 (out/(mode+'-stderr.txt')).open('xb') as stderr:
                result = subprocess.run(command, cwd=HERE, stdout=stdout, stderr=stderr,
                                        timeout=plan['phase_timeout_seconds'])
            write(out/(mode+'-receipt.json'), dict(exit=result.returncode,
                seconds=perf_counter()-begin, command=command))
            assert result.returncode == 0, mode+' failed'
        bindings(plan)
        write(out/'results-manifest.json', {p.name: digest(p) for p in sorted(out.iterdir())
                                           if p.is_file()})
        write(out/'receipt.json', dict(exit=0, seconds=perf_counter()-start,
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
