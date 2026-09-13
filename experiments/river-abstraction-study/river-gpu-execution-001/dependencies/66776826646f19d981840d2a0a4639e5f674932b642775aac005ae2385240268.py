"""Retained runner for one-step fixed-capacity group repair."""
from environment import ROOT, PRIOR, np, scipy, opt, core, PayoffGame, RiverHoldem
from collections import Counter
from fractions import Fraction as Q
from hashlib import sha256
from itertools import combinations
import json
from math import fsum
from pathlib import Path
import subprocess
import sys
from time import perf_counter
import tracemalloc
import repair

HERE = Path(__file__).resolve().parent
NAME = 'witness-group-repair-001'
SEAL = 'd39ac27ca3fa2dc4d84b17791ba01d6b125d883184d293a059a677e24b8c8292'


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def write(path, value):
    with Path(path).open('w', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(value, sort_keys=True, indent=2, allow_nan=False)+'\n')


def weights(groups):
    return [np.eye(max(g)+1)[g] for g in groups]


def make_plan(output, *, synthetic=False):
    paths = {p.resolve() for p in HERE.glob('*.py')}
    paths.add(HERE/'design.md')
    paths.add(Path(sys.executable).resolve())
    for module in tuple(sys.modules.values()):
        file = getattr(module, '__file__', None)
        if file:
            file = Path(file).resolve()
            if file.suffix == '.py' and file.is_relative_to(ROOT):
                paths.add(file)
    pins = {str(p): digest(p) for p in sorted(paths)}
    entries = []
    if synthetic:
        groups = [[0, 0, 1, 2]]*2
        matrix = synthetic_game()
        baseline = core.solve(matrix, weights(groups))
        entries.append(dict(case=dict(id='synthetic', board_index=0, texture='synthetic',
                        regime='uniform', pool=0), bet=5, groups=groups, baseline=baseline))
    else:
        opt.require(digest(PRIOR/'milestone-manifest.json') == SEAL, 'predecessor seal changed')
        manifest = read(PRIOR/'milestone-manifest.json')
        opt.require(digest(core.__file__) == manifest['verification-tools/soft.py'],
                    'frozen mathematical component changed')
        old_plan = read(PRIOR/'plan.json')
        for path in paths:
            if path.is_relative_to(ROOT/'src'):
                opt.require(digest(path) == old_plan['pins'].get(str(path)),
                            'predecessor library dependency changed: '+str(path))
        pins[str(PRIOR/'milestone-manifest.json')] = SEAL
        for i in range(1, 96, 3):
            path = PRIOR/f'cell-{i:03d}.json'
            opt.require(digest(path) == manifest[path.name], 'prior case changed')
            row = read(path)
            opt.require(row['capacity'] == 16, 'wrong predecessor capacity')
            original = Path(row['entry']['path'])
            opt.require(digest(original) == old_plan['pins'][str(original)], 'input changed')
            entries.append(dict(case=row['entry']['case'], bet=row['entry']['bet'],
                                path=str(path), original=str(original)))
            pins[str(path)], pins[str(original)] = digest(path), digest(original)
        opt.require(digest(PRIOR/'plan.json') == manifest['plan.json'], 'prior plan changed')
        pins[str(PRIOR/'plan.json')] = digest(PRIOR/'plan.json')
        opt.require(len(entries) == 32, 'wrong case count')
    return dict(schema='witness-group-repair-v1', milestone=NAME, synthetic=synthetic,
        entries=entries, pins=pins, output=str(Path(output).resolve()),
        repaired_checkpoints=[3, 10] if synthetic else [1000, 10000],
        control_checkpoints=[10, 50] if synthetic else [10000, 50000],
        phase_timeout_seconds=60 if synthetic else 900, fitting_tasks=0,
        python=sys.version, numpy=np.__version__, scipy=scipy.__version__)


def bindings(plan):
    opt.require(plan['schema'] == 'witness-group-repair-v1' and
                type(plan['synthetic']) is bool and not tracemalloc.is_tracing(), 'wrong mode')
    opt.require(plan['python'] == sys.version and plan['numpy'] == np.__version__ and
                plan['scipy'] == scipy.__version__, 'environment changed')
    for name, expected in plan['pins'].items():
        opt.require(digest(name) == expected, 'binding changed: '+name)
    if not plan['synthetic']:
        opt.require(len(plan['entries']) == 32 and plan['repaired_checkpoints'] == [1000, 10000]
                    and plan['control_checkpoints'] == [10000, 50000]
                    and plan['phase_timeout_seconds'] == 900, 'frozen design changed')


def synthetic_game():
    return PayoffGame(np.eye(4)/4, np.zeros((4, 4)), np.diag([.25, .25, 0, 0]),
                      np.diag([.5, -.5, 0, 0]), None, 'synthetic')


def load_case(plan, entry):
    if plan['synthetic']:
        return synthetic_game(), entry['groups'], entry['baseline'], None
    old, original = read(entry['path']), read(entry['original'])
    opt.require(original['case'] == entry['case'] and original['bet'] == entry['bet'] and
                old['entry']['case'] == entry['case'] and old['entry']['bet'] == entry['bet'],
                'case identity changed')
    inputs = original['inputs']
    ranges = [{tuple(h): w for h, w in records} for records in inputs['ranges']]
    game = RiverHoldem.from_independent_ranges(board=entry['case']['board'], pot=10,
        stacks=(20, 20), bet_size=entry['bet'],
        player0_weights=ranges[0], player1_weights=ranges[1])
    matrix = PayoffGame.from_river(game)
    opt.require(matrix.joint.shape == (96, 96) and
                matrix.joint.tolist() == inputs['joint'] and
                [[list(h) for h in hs] for hs in matrix.hands] == inputs['hands'] and
                game.provenance_digest == original['provenance_digest'], 'game mismatch')
    groups = old['labels']
    opt.require(all(len(set(g)) == 16 for g in groups) and
                [p.tolist() for p in weights(groups)] == old['methods']['hard']['weights'],
                'hard baseline mismatch')
    baseline = old['methods']['hard']['solution']
    core.verify(matrix, weights(groups), baseline)
    return matrix, groups, baseline, old['methods']['hard']['records'][-1]


def score(matrix, groups, coefficients):
    w = weights(groups)
    hand = [np.asarray(c)[np.asarray(g)] for c, g in zip(coefficients, groups, strict=True)]
    low, high = core.exact_bounds(matrix, w, coefficients, unrestricted=True)
    exact = (high-low)/2
    actual = matrix.evaluate(*hand)['exploitability']
    x, y = hand
    n, m = matrix.joint.shape
    check = [fsum(float(matrix.check[i, j]) for j in range(m)) for i in range(n)]
    betting = [fsum((1-y[j])*float(matrix.fold[i, j])+y[j]*float(matrix.call[i, j])
                    for j in range(m)) for i in range(n)]
    upper = fsum(max(a, b) for a, b in zip(check, betting))
    lower = fsum((1-x[i])*check[i] for i in range(n))+fsum(
        min(fsum(x[i]*float(matrix.fold[i, j]) for i in range(n)),
            fsum(x[i]*float(matrix.call[i, j]) for i in range(n))) for j in range(m))
    scalar = (upper-lower)/2
    opt.require(abs(actual-float(exact)) <= 1e-10 and abs(actual-scalar) <= 1e-10,
                'profile evaluation mismatch')
    return dict(exact_exploitability=str(exact), exploitability=actual,
                scalar_exploitability=scalar, hand_probabilities=[v.tolist() for v in hand])


def train(matrix, groups, checkpoints):
    start = perf_counter()
    engine = core.RegretBR(matrix, weights(groups))
    setup_seconds = perf_counter()-start
    result, active = [], 0.
    for checkpoint in checkpoints:
        start = perf_counter()
        while engine.iteration < checkpoint:
            engine.step()
        active += perf_counter()-start
        policy = [v.tolist() for v in engine.average()]
        result.append(dict(iteration=checkpoint, coefficients=policy,
            active_seconds=active, setup_seconds=setup_seconds, **score(matrix, groups, policy)))
    return result


def worker(plan, out):
    bindings(plan)
    for i, entry in enumerate(plan['entries']):
        start = perf_counter()
        matrix, groups, baseline, old_policy = load_case(plan, entry)
        preparation = perf_counter()-start
        start = perf_counter()
        proposal = repair.propose(matrix, groups, baseline)
        proposing = perf_counter()-start
        start = perf_counter()
        solution = core.solve(matrix, weights(proposal['groups']))
        solving = perf_counter()-start
        records = {}
        for name in (('repaired', 'control') if i % 2 == 0 else ('control', 'repaired')):
            gs = proposal['groups'] if name == 'repaired' else groups
            records[name] = train(matrix, gs, plan[name+'_checkpoints'])
        if old_policy is not None:
            opt.require(records['control'][0]['coefficients'] == old_policy['coefficients']
                        and records['control'][0]['exact_exploitability'] ==
                        old_policy['exact_exploitability'], 'retained control did not reproduce')
        write(out/f'case-{i:03d}.json', dict(entry=entry, baseline_groups=groups,
              baseline=baseline, proposal=proposal, solution=solution, records=records,
              preparation_seconds=preparation, proposal_seconds=proposing, lp_seconds=solving))
        print(f"completed {i+1}/{len(plan['entries'])}: {entry['case']['id']} bet {entry['bet']}",
              flush=True)
    bindings(plan)
    write(out/'worker-complete.json', dict(complete=True, cases=len(plan['entries']),
          new_lp_calls=2*len(plan['entries']), trajectories=2*len(plan['entries']),
          fitting_tasks=0))


def independent_exchange(groups, changes):
    """Direct partition enumeration, without the split-gain/merge-cost shortcut."""
    k = max(groups)+1
    members = [[i for i, g in enumerate(groups) if g == s] for s in range(k)]
    def objective(parts):
        return sum((max(Q(0), sum((changes[i] for i in p), Q(0))) for p in parts), Q(0))
    base = objective(members)
    best, operation, examined = base, None, 0
    for split in range(k):
        plus = [i for i in members[split] if changes[i] > 0]
        minus = [i for i in members[split] if changes[i] <= 0]
        if not plus or not any(changes[i] < 0 for i in minus):
            continue
        for a, b in combinations([s for s in range(k) if s != split], 2):
            parts = [p for s, p in enumerate(members) if s not in (split, a, b)]
            parts += [plus, minus, members[a]+members[b]]
            value = objective(parts)
            examined += 1
            if value > best:
                best, operation = value, dict(split=split, merge=[a, b])
    return dict(net_witness_gain_exact=str(best-base), operation=operation,
                examined_exchanges=examined)


def statistics(rows):
    bounds = {}
    for name, key in [('baseline', 'baseline'), ('repaired', 'solution')]:
        bounds[name] = [sum(Q(r[key]['minimum_exploitability'][endpoint]) for r in rows)/len(rows)
                        for endpoint in ('lower_exact', 'upper_exact')]
    actual = {}
    for name, method, index in [('baseline_10k', 'control', 0), ('baseline_50k', 'control', 1),
                                ('repaired_10k', 'repaired', 1)]:
        actual[name] = sum(Q(r['records'][method][index]['exact_exploitability'])
                           for r in rows)/len(rows)
    low = bounds['repaired'][0]-bounds['baseline'][1]
    high = bounds['repaired'][1]-bounds['baseline'][0]
    return dict(cases=len(rows), floors={k: opt.interval(*v) for k, v in bounds.items()},
        floor_delta=opt.interval(low, high), actual={k: float(v) for k, v in actual.items()},
        actual_delta_exact=str(actual['repaired_10k']-actual['baseline_10k']),
        versus_50k_exact=str(actual['repaired_10k']-actual['baseline_50k']),
        changed_seats=sum(s['changed'] for r in rows for s in r['proposal']['seats']),
        floor_directions=dict(Counter('lower' if
            Q(r['solution']['minimum_exploitability']['upper_exact']) <
            Q(r['baseline']['minimum_exploitability']['lower_exact']) else 'higher' if
            Q(r['solution']['minimum_exploitability']['lower_exact']) >
            Q(r['baseline']['minimum_exploitability']['upper_exact']) else 'overlapping'
            for r in rows)))


def summarize(rows):
    panels = {}
    for bet in sorted({r['entry']['bet'] for r in rows}):
        rs = [r for r in rows if r['entry']['bet'] == bet]
        panel = dict(overall=statistics(rs))
        for category, key in [('boards', 'board_index'), ('textures', 'texture'),
                              ('regimes', 'regime')]:
            panel[category] = {str(v): statistics([r for r in rs
                if r['entry']['case'][key] == v]) for v in sorted(
                {r['entry']['case'][key] for r in rs})}
        boards = sorted({r['entry']['case']['board_index'] for r in rs})
        panel['leave_one_board_out'] = {str(b): statistics([r for r in rs
            if r['entry']['case']['board_index'] != b]) for b in boards if len(boards) > 1}
        panels[str(bet)] = panel
    primary = panels['5']['overall']
    support = Q(primary['floor_delta']['upper_exact']) < -Q('1e-8')
    return dict(complete=True, panels=panels, flags=dict(representation_support=support,
        practical_support=support and Q(primary['actual_delta_exact']) < -Q('1e-6')))


def verify(plan, out):
    bindings(plan)
    saved = opt.linprog
    def forbidden(*args, **kwargs):
        raise AssertionError('verifier LP forbidden')
    opt.linprog = forbidden
    rows, replayed, profiles, examined = [], 0, 0, 0
    try:
        for i, entry in enumerate(plan['entries']):
            matrix, groups, baseline, old_policy = load_case(plan, entry)
            row = read(out/f'case-{i:03d}.json')
            proposal = repair.propose(matrix, groups, baseline)
            opt.require(row['entry'] == entry and row['baseline_groups'] == groups and
                        row['baseline'] == baseline and row['proposal'] == proposal,
                        'proposal reconstruction mismatch')
            for seat in (0, 1):
                change = [Q(v) for v in proposal['seats'][seat]['weighted_advantages_exact']]
                independent = independent_exchange(groups[seat], change)
                opt.require(all(proposal['seats'][seat][k] == v for k, v in independent.items()),
                            'independent exchange mismatch')
                examined += independent['examined_exchanges']
            core.verify(matrix, weights(proposal['groups']), row['solution'])
            for name, gs, solution in [('control', groups, baseline),
                                       ('repaired', proposal['groups'], row['solution'])]:
                engine = core.RegretBR(matrix, weights(gs))
                records = row['records'][name]
                opt.require([r['iteration'] for r in records] == plan[name+'_checkpoints'],
                            'checkpoint census mismatch')
                for record in records:
                    while engine.iteration < record['iteration']:
                        engine.step()
                        replayed += 1
                    values = [v.tolist() for v in engine.average()]
                    opt.require(record['coefficients'] == values, 'trajectory replay mismatch')
                    scored = score(matrix, gs, values)
                    opt.require(all(record[k] == v for k, v in scored.items()), 'score mismatch')
                    opt.require(Q(scored['exact_exploitability']) >=
                                Q(solution['minimum_exploitability']['lower_exact']),
                                'policy contradicts floor')
                    profiles += 1
            if old_policy is not None:
                opt.require(row['records']['control'][0]['coefficients'] ==
                            old_policy['coefficients'], 'predecessor replay mismatch')
            rows.append(row)
            print(f'verified {i+1}/{len(plan["entries"])}', flush=True)
        expected = dict(complete=True, cases=len(rows), new_lp_calls=2*len(rows),
                        trajectories=2*len(rows), fitting_tasks=0)
        opt.require(read(out/'worker-complete.json') == expected, 'worker census mismatch')
        bindings(plan)
        write(out/'summary.json', summarize(rows))
        write(out/'audit.json', dict(passed=True, certificates=4*len(rows), profiles=profiles,
            replayed_updates=replayed, independently_enumerated_exchanges=examined,
            verifier_lp_calls=0, fitting_tasks=0))
    finally:
        opt.linprog = saved


def run(path, expected):
    opt.require(digest(path) == expected, 'plan digest mismatch')
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
            opt.require(child.returncode == 0, mode+' failed')
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
    opt.require(digest(path) == expected, 'plan digest mismatch')
    if mode == 'run':
        run(Path(path), expected)
    else:
        plan = read(path)
        {'worker': worker, 'verify': verify}[mode](plan, Path(plan['output']))
