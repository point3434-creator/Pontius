"""Continuation under the retained second-repair compute budget, with an upper bracket."""
from bridge import ROOT, HISTORY, PRIOR, c, gate
from pathlib import Path
from fractions import Fraction as Q
from time import perf_counter
from collections import Counter
from math import isfinite
import sys
import subprocess
import tracemalloc

HERE = Path(__file__).resolve().parent
NAME = 'witness-compute-matched-continuation-001'
read, write, digest = c.read, c.write, c.digest


def budgets(row):
    train = row['records']['repaired'][1]
    work = row['baseline_lp_seconds']+row['proposal_seconds']
    work += train['setup_seconds']+train['active_seconds']
    return dict(work_seconds=work, total_seconds=work+row['gate_seconds'])


def timed_continue(engine, work, total, *, clock=perf_counter, block=100, cap=200000):
    c.opt.require(isfinite(work) and isfinite(total) and 0 < work < total, 'invalid budget')
    c.opt.require(type(block) is int and block > 0 and engine.iteration > 0, 'invalid block')
    active, matched = 0., None
    trace = []
    def snapshot(sums, iteration, elapsed, crossing):
        return dict(iteration=iteration, coefficients=[(v[:, 1]/iteration).tolist() for v in sums],
                    active_seconds=elapsed, crossing_seconds=crossing)
    while True:
        c.opt.require(engine.iteration < cap, 'timed iteration cap exhausted')
        started = clock()
        before = [s.copy() for s in engine.sums]
        previous_iteration, previous_elapsed = engine.iteration, active
        for _ in range(min(block, cap-engine.iteration)):
            engine.step()
        elapsed = clock()-started
        c.opt.require(isfinite(elapsed) and elapsed >= 0, 'invalid clock interval')
        active += elapsed
        trace.append(dict(before_iteration=previous_iteration, iteration=engine.iteration,
                          before_seconds=previous_elapsed, after_seconds=active))
        if matched is None and active > work:
            matched = snapshot(before, previous_iteration, previous_elapsed, active)
        if active >= total:
            return dict(matched=matched, generous=snapshot(engine.sums, engine.iteration,
                        active, active), trace=trace)


def bindings(plan):
    assert plan['name'] == NAME and not tracemalloc.is_tracing()
    assert plan['python'] == sys.version and plan['numpy'] == c.np.__version__
    assert plan['scipy'] == c.scipy.__version__
    for path, expected in plan['pins'].items():
        assert digest(path) == expected, path
    assert plan['sources'] == [str(PRIOR/f'case-{i:03d}.json') for i in range(64)]
    assert plan['budgets'] == [budgets(read(path)) for path in plan['sources']]
    assert plan['block_updates'] == 100 and plan['iteration_cap'] == 200000
    assert plan['phase_timeout_seconds'] == 900


def load_case(path):
    source = read(path)
    parent = read(source['source_path'])
    assert digest(source['source_path']) == source['source_sha256']
    matrix, original_groups, inputs = c.build_case(source['entry'])
    assert inputs == parent['inputs'] and original_groups == parent['baseline_groups']
    groups, coefficients = source['incumbent_groups'], source['incumbent_coefficients']
    assert c.score(matrix, groups, coefficients) == source['incumbent_score']
    assert c.score(matrix, source['repair_gate']['groups'],
                   source['repair_gate']['coefficients']) == source['second_score']
    c.core.verify(matrix, c.weights(groups), source['baseline'])
    return source, matrix, groups, coefficients


def worker(plan, out):
    bindings(plan)
    def forbidden(*args, **kwargs):
        raise AssertionError('new LP solving forbidden')
    c.opt.linprog = forbidden
    for i, path in enumerate(plan['sources']):
        source, matrix, groups, coefficients = load_case(path)
        engine = c.core.RegretBR(matrix, c.weights(groups))
        while engine.iteration < 10000:
            engine.step()
        assert [v.tolist() for v in engine.average()] == coefficients
        bound = plan['budgets'][i]
        timed = timed_continue(engine, bound['work_seconds'], bound['total_seconds'],
                               block=plan['block_updates'], cap=plan['iteration_cap'])
        records = {}
        for name in ('matched', 'generous'):
            point = timed[name]
            raw = c.score(matrix, groups, point['coefficients'])
            start = perf_counter()
            accepted = gate.select(matrix, groups, coefficients, groups, point['coefficients'])
            gate_seconds = perf_counter()-start
            score = c.score(matrix, accepted['groups'], accepted['coefficients'])
            records[name] = dict(**point, raw=raw, gate=accepted, selected_score=score,
                gate_seconds=gate_seconds,
                total_component_seconds=point['active_seconds']+gate_seconds)
        write(out/f'case-{i:03d}.json', dict(entry=source['entry'], source_path=path,
            source_sha256=digest(path), budgets=bound, trace=timed['trace'], records=records,
            incumbent_score=source['incumbent_score'], repair_score=source['second_score'],
            grouping_floor=source['baseline']['minimum_exploitability']))
        print(f'completed {i+1}/64: total iteration {timed["generous"]["iteration"]}', flush=True)
    bindings(plan)
    write(out/'worker-complete.json', dict(complete=True, cases=64, timed_trajectories=64,
                                         gates=128, new_lp_calls=0, fitting_tasks=0))


def vals(row):
    return dict(incumbent=Q(row['incumbent_score']['exact_exploitability']),
        repair=Q(row['repair_score']['exact_exploitability']),
        matched=Q(row['records']['matched']['selected_score']['exact_exploitability']),
        generous=Q(row['records']['generous']['selected_score']['exact_exploitability']))


def stats(rows):
    vs = [vals(r) for r in rows]
    means = {k: sum(v[k] for v in vs)/len(vs) for k in vs[0]}
    floors = [sum(Q(r['grouping_floor'][k]) for r in rows)/len(rows)
              for k in ('lower_exact', 'upper_exact')]
    def count(a, b):
        return dict(Counter('better' if v[a] < v[b] else 'worse' if v[a] > v[b]
                            else 'equal' for v in vs))
    return dict(cases=len(rows), means_exact={k: str(v) for k, v in means.items()},
        means={k: float(v) for k, v in means.items()}, floor_interval=list(map(str, floors)),
        repair_minus_matched=str(means['repair']-means['matched']),
        repair_minus_generous=str(means['repair']-means['generous']),
        repair_below_floor_cases=sum(v['repair'] < Q(r['grouping_floor']['lower_exact'])-Q('1e-8')
                                     for r, v in zip(rows, vs)),
        repair_vs_matched=count('repair', 'matched'),
        repair_vs_generous=count('repair', 'generous'),
        matched_vs_incumbent=count('matched', 'incumbent'),
        generous_vs_incumbent=count('generous', 'incumbent'),
        mean_total_ratios={name: sum(r['records'][name]['total_component_seconds'] for r in rows)/
            sum(r['budgets']['total_seconds'] for r in rows) for name in ('matched', 'generous')},
        mean_extra_iterations={name: sum(r['records'][name]['iteration']-10000
                                        for r in rows)/len(rows)
                               for name in ('matched', 'generous')})


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
    safe = all(v['matched'] <= v['incumbent'] and v['generous'] <= v['incumbent']
               for v in map(vals, rows))
    half = panels['5']['overall']
    return dict(complete=True, panels=panels, flags=dict(continuation_nonregression=safe,
        beats_matched_half_pot=Q(half['repair_minus_matched']) < -Q('1e-6'),
        beats_generous_half_pot=Q(half['repair_minus_generous']) < -Q('1e-6')))


def verify_trace(row):
    trace, records, bound = row['trace'], row['records'], row['budgets']
    iteration, active = 10000, 0.
    for block in trace:
        assert block['before_iteration'] == iteration and block['before_seconds'] == active
        assert block['iteration'] == min(iteration+100, 200000)
        assert isfinite(block['after_seconds']) and block['after_seconds'] >= active
        assert active < bound['total_seconds']
        iteration, active = block['iteration'], block['after_seconds']
    first = next(b for b in trace if b['after_seconds'] > bound['work_seconds'])
    point = records['matched']
    assert point['iteration'] == first['before_iteration']
    assert point['active_seconds'] == first['before_seconds'] <= bound['work_seconds']
    assert point['crossing_seconds'] == first['after_seconds'] > bound['work_seconds']
    assert records['generous']['iteration'] == iteration
    assert records['generous']['active_seconds'] == active >= bound['total_seconds']
    assert records['generous']['crossing_seconds'] == active


def verify(plan, out):
    bindings(plan)
    def forbidden(*args, **kwargs):
        raise AssertionError('verifier LP forbidden')
    c.opt.linprog = forbidden
    rows, updates = [], 0
    for i, path in enumerate(plan['sources']):
        source, matrix, groups, coefficients = load_case(path)
        row = read(out/f'case-{i:03d}.json')
        assert row['entry'] == source['entry'] and row['source_path'] == path
        assert row['source_sha256'] == digest(path) and row['budgets'] == plan['budgets'][i]
        assert row['incumbent_score'] == source['incumbent_score']
        assert row['repair_score'] == source['second_score']
        assert row['grouping_floor'] == source['baseline']['minimum_exploitability']
        verify_trace(row)
        engine = c.core.RegretBR(matrix, c.weights(groups))
        for name in ('matched', 'generous'):
            point = row['records'][name]
            while engine.iteration < point['iteration']:
                engine.step()
                updates += 1
                if engine.iteration == 10000:
                    assert [v.tolist() for v in engine.average()] == coefficients
            policy = [v.tolist() for v in engine.average()]
            assert policy == point['coefficients']
            assert c.score(matrix, groups, policy) == point['raw']
            chosen = gate.select(matrix, groups, coefficients, groups, policy)
            assert chosen == point['gate']
            pairs = [gate.audit_security(matrix, [list(map(Q, p)) for p in r['hand_probabilities']])
                     for r in (source['incumbent_score'], point['raw'])]
            assert chosen['security_exact'] == [[str(x) for x in p] for p in pairs]
            assert chosen['accepted'] == [pairs[1][s] >= pairs[0][s] for s in (0, 1)]
            expected = -sum((pairs[int(chosen['accepted'][s])][s] for s in (0, 1)), Q(0))/2
            assert c.score(matrix, chosen['groups'], chosen['coefficients']) == (
                point['selected_score'])
            assert Q(point['selected_score']['exact_exploitability']) == expected <= Q(
                source['incumbent_score']['exact_exploitability'])
            assert expected >= Q(row['grouping_floor']['lower_exact'])
            assert isfinite(point['gate_seconds']) and point['gate_seconds'] >= 0
            assert point['total_component_seconds'] == point['active_seconds']+point['gate_seconds']
        rows.append(row)
        print(f'verified {i+1}/64', flush=True)
    assert read(out/'worker-complete.json') == dict(complete=True, cases=64, timed_trajectories=64,
                                                  gates=128, new_lp_calls=0, fitting_tasks=0)
    bindings(plan)
    write(out/'summary.json', summarize(rows))
    write(out/'audit.json', dict(passed=True, cases=64, replayed_updates=updates,
        timing_traces=64, asymmetric_certificates=128, raw_profiles=128, selected_profiles=128,
        retained_reference_profiles=128, independent_gate_audits=128, new_lp_calls=0))


def run(path, expected):
    assert digest(path) == expected
    plan = read(path)
    bindings(plan)
    out = Path(plan['output'])
    out.mkdir(parents=True, exist_ok=False)
    started = perf_counter()
    try:
        write(out/'plan.json', plan)
        write(out/'started.json', dict(plan_sha256=expected))
        for mode in ('worker', 'verify'):
            command = [sys.executable, '-B', '-W', 'error::ResourceWarning',
                       str(HERE/'experiment.py'), mode, str(path), expected]
            start = perf_counter()
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
