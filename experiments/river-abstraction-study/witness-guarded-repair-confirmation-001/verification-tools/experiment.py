"""Prospective fresh-board test of the complete guarded-repair procedure."""
from base import ROOT, HISTORY, PRIOR, c
from pathlib import Path
from fractions import Fraction as Q
from hashlib import sha256
from time import perf_counter
from collections import Counter
import sys
import subprocess
import tracemalloc
import gate

HERE = Path(__file__).resolve().parent
NAME = 'witness-guarded-repair-confirmation-001'
read, write, digest = c.read, c.write, c.digest


def select_boards(excluded):
    used = set(map(c.canonical_board, excluded))
    selected = {name: [] for name in c.TEXTURES}
    receipt = []
    for attempt in range(10000):
        def order(card):
            return sha256(f'{NAME}|board|{attempt}|{card}'.encode()).digest(), card
        board = sorted(sorted(range(52), key=order)[:5])
        key, kind = c.canonical_board(board), c.texture(board)
        if key not in used and len(selected[kind]) < 4:
            selected[kind].append(board)
            receipt.append(dict(attempt=attempt, board=board, texture=kind))
            used.add(key)
        if all(len(v) == 4 for v in selected.values()):
            return [b for kind in c.TEXTURES for b in selected[kind]], receipt
    raise ValueError('board selection exhausted')


def bindings(plan):
    assert plan['name'] == NAME and not tracemalloc.is_tracing()
    assert plan['python'] == sys.version and plan['numpy'] == c.np.__version__
    assert plan['scipy'] == c.scipy.__version__
    for name, expected in plan['pins'].items():
        assert digest(name) == expected, name
    boards, receipt = select_boards(plan['excluded_boards'])
    assert plan['boards'] == boards and plan['selection_receipt'] == receipt
    assert plan['entries'] == c.entries_for(boards) and len(plan['entries']) == 64
    assert plan['control_checkpoints'] == [10000, 50000]
    assert plan['repaired_checkpoints'] == [1000, 10000]
    assert plan['phase_timeout_seconds'] == 900


def worker(plan, out):
    bindings(plan)
    for i, entry in enumerate(plan['entries']):
        start = perf_counter()
        matrix, groups, inputs = c.build_case(entry)
        preparation = perf_counter()-start
        start = perf_counter()
        baseline = c.core.solve(matrix, c.weights(groups))
        baseline_seconds = perf_counter()-start
        start = perf_counter()
        proposal = c.repair.propose(matrix, groups, baseline)
        proposing = perf_counter()-start
        records = {}
        for name in (('repaired', 'control') if i % 2 == 0 else ('control', 'repaired')):
            gs = proposal['groups'] if name == 'repaired' else groups
            records[name] = c.train(matrix, gs, plan[name+'_checkpoints'])
        start = perf_counter()
        accepted = gate.select(matrix, groups, records['control'][0]['coefficients'],
                               proposal['groups'], records['repaired'][1]['coefficients'])
        gate_seconds = perf_counter()-start
        # Neither this score nor the repaired certificate is an input to the gate.
        score = c.score(matrix, accepted['groups'], accepted['coefficients'])
        start = perf_counter()
        solution = c.core.solve(matrix, c.weights(proposal['groups']))
        solving = perf_counter()-start
        write(out/f'case-{i:03d}.json', dict(entry=entry, baseline_groups=groups,
            inputs=inputs, baseline=baseline, proposal=proposal, solution=solution,
            records=records, gate=accepted, selected_score=score,
            preparation_seconds=preparation, baseline_lp_seconds=baseline_seconds,
            proposal_seconds=proposing, gate_seconds=gate_seconds,
            diagnostic_lp_seconds=solving))
        print(f'completed {i+1}/64: {entry["case"]["id"]} bet {entry["bet"]}', flush=True)
    bindings(plan)
    write(out/'worker-complete.json', dict(complete=True, cases=64, new_lp_calls=256,
        trajectories=128, fitting_tasks=0, gates=64))


def stats(rows):
    n = len(rows)
    means = {}
    for name, method, index in [('original10k', 'control', 0),
                                ('original50k', 'control', 1), ('raw10k', 'repaired', 1)]:
        means[name] = sum(Q(r['records'][method][index]['exact_exploitability'])
                          for r in rows)/n
    means['guarded10k'] = sum(Q(r['selected_score']['exact_exploitability']) for r in rows)/n
    delta = lambda r, method: Q((r['selected_score'] if method == 'guarded' else
        r['records']['repaired'][1])['exact_exploitability'])-Q(
        r['records']['control'][0]['exact_exploitability'])
    directions = lambda method: dict(Counter('worse' if delta(r, method) > 0 else
        'better' if delta(r, method) < 0 else 'equal' for r in rows))
    return dict(cases=n, means_exact={k: str(v) for k, v in means.items()},
        means={k: float(v) for k, v in means.items()},
        delta_exact=str(means['guarded10k']-means['original10k']),
        versus_50k_exact=str(means['guarded10k']-means['original50k']),
        raw_directions=directions('raw'), guarded_directions=directions('guarded'),
        changed_seats=sum(s['changed'] for r in rows for s in r['proposal']['seats']),
        accepted_changed_seats=sum(r['gate']['accepted'][s] and
            r['proposal']['seats'][s]['changed'] for r in rows for s in (0, 1)),
        mean_gate_seconds=sum(r['gate_seconds'] for r in rows)/n)


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
    safe = all(Q(r['selected_score']['exact_exploitability']) <=
               Q(r['records']['control'][0]['exact_exploitability']) for r in rows)
    return dict(complete=True, panels=panels, flags=dict(exact_nonregression=safe,
        useful_half_pot=safe and Q(panels['5']['overall']['delta_exact']) < -Q('1e-6')))


def verify(plan, out):
    bindings(plan)
    def forbidden(*args, **kwargs):
        raise AssertionError('verifier LP forbidden')
    c.opt.linprog = forbidden
    rows, replayed, examined = [], 0, 0
    for i, entry in enumerate(plan['entries']):
        row = read(out/f'case-{i:03d}.json')
        matrix, groups, inputs = c.build_case(entry)
        assert row['entry'] == entry and row['baseline_groups'] == groups
        assert row['inputs'] == inputs
        c.core.verify(matrix, c.weights(groups), row['baseline'])
        proposal = c.repair.propose(matrix, groups, row['baseline'])
        assert proposal == row['proposal']
        for s in (0, 1):
            changes = list(map(Q, proposal['seats'][s]['weighted_advantages_exact']))
            expected = c.frozen.independent_exchange(groups[s], changes)
            assert all(proposal['seats'][s][k] == v for k, v in expected.items())
            examined += expected['examined_exchanges']
        c.core.verify(matrix, c.weights(proposal['groups']), row['solution'])
        for name, gs, solution in [('control', groups, row['baseline']),
                                  ('repaired', proposal['groups'], row['solution'])]:
            engine = c.core.RegretBR(matrix, c.weights(gs))
            records = row['records'][name]
            assert [r['iteration'] for r in records] == plan[name+'_checkpoints']
            for record in records:
                while engine.iteration < record['iteration']:
                    engine.step()
                    replayed += 1
                coeff = [v.tolist() for v in engine.average()]
                assert coeff == record['coefficients']
                scored = c.score(matrix, gs, coeff)
                assert all(record[k] == v for k, v in scored.items())
                assert Q(scored['exact_exploitability']) >= Q(
                    solution['minimum_exploitability']['lower_exact'])
        old, new = row['records']['control'][0], row['records']['repaired'][1]
        decision = gate.select(matrix, groups, old['coefficients'],
                               proposal['groups'], new['coefficients'])
        assert decision == row['gate']
        audited = []
        for record in (old, new):
            hands = [list(map(Q, ps)) for ps in record['hand_probabilities']]
            audited.append(gate.audit_security(matrix, hands))
        assert [[str(v) for v in pair] for pair in audited] == decision['security_exact']
        assert decision['accepted'] == [audited[1][s] >= audited[0][s] for s in (0, 1)]
        expected = -sum(audited[int(decision['accepted'][s])][s] for s in (0, 1))/2
        scored = c.score(matrix, decision['groups'], decision['coefficients'])
        assert scored == row['selected_score']
        assert Q(scored['exact_exploitability']) == expected <= Q(old['exact_exploitability'])
        rows.append(row)
        print(f'verified {i+1}/64', flush=True)
    assert read(out/'worker-complete.json') == dict(complete=True, cases=64, new_lp_calls=256,
        trajectories=128, fitting_tasks=0, gates=64)
    bindings(plan)
    write(out/'summary.json', summarize(rows))
    write(out/'audit.json', dict(passed=True, cases=64, asymmetric_certificates=256,
        saved_profiles=256, selected_profiles=64, replayed_updates=replayed,
        independently_enumerated_exchanges=examined, independent_security_pairs=128,
        verifier_lp_calls=0, model_fits=0))


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
                child = subprocess.run(command, cwd=HERE, stdout=stdout, stderr=stderr,
                                       timeout=plan['phase_timeout_seconds'])
            write(out/(mode+'-receipt.json'), dict(exit=child.returncode,
                seconds=perf_counter()-begin, command=command))
            assert child.returncode == 0, mode+' failed'
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
