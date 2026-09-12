"""Bounded retained runner for the soft-assignment pilot."""
from environment import (ROOT, np, scipy, opt, PayoffGame, RiverHoldem,
                         anchored_clusters, design, raw_features, uniform_equities)
from fractions import Fraction as Q
from hashlib import sha256
import json
from math import fsum
from pathlib import Path
import subprocess
import sys
from time import perf_counter
import tracemalloc
from scipy.special import expit
import soft

HERE = Path(__file__).resolve().parent
NAME = 'witness-soft-assignment-001'
PRIOR = ROOT/'experiments/river-abstraction-study/witness-ordinal-001'
MODEL = (ROOT/'experiments/river-abstraction-study/witness-preference-confirmation-001'
         /'candidate.json')
SEAL = '078b3e0ab9962d99102eb4d315a08dc3f33eeca2ba0ff1a6bdb2e179ed446f23'
METHODS = ('hard', 'soft')


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def write(path, value):
    with Path(path).open('w', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(value, sort_keys=True, indent=2, allow_nan=False)+'\n')


def source_pins():
    paths = {p.resolve() for p in HERE.glob('*.py')}
    paths.add(HERE/'design.md')
    for module in tuple(sys.modules.values()):
        path = getattr(module, '__file__', None)
        if path:
            path = Path(path).resolve()
            if path.suffix == '.py' and path.is_relative_to(ROOT):
                paths.add(path)
    paths.add(Path(sys.executable).resolve())
    return {str(p): digest(p) for p in sorted(paths)}


def make_plan(output, *, synthetic=False):
    pins = source_pins()
    if synthetic:
        entries = [dict(case=dict(id='synthetic', board_index=0, texture='synthetic',
                                 regime='uniform', pool=0), bet=5)]
    else:
        opt.require(digest(PRIOR/'milestone-manifest.json') == SEAL, 'predecessor seal changed')
        manifest, prior_plan = read(PRIOR/'milestone-manifest.json'), read(PRIOR/'plan.json')
        pins[str(PRIOR/'milestone-manifest.json')] = SEAL
        opt.require(digest(MODEL) == prior_plan['pins'][str(MODEL)], 'frozen model changed')
        pins[str(MODEL)] = digest(MODEL)
        entries = []
        for case in prior_plan['evaluation_cases']:
            if case['pool'] != 0:
                continue
            for bet in (5, 10):
                path = PRIOR/f"eval-{case['id']}-bet-{bet}.json"
                opt.require(digest(path) == manifest[path.name], 'retained case changed')
                pins[str(path)] = digest(path)
                entries.append(dict(case=case, bet=bet, path=str(path)))
        opt.require(len(entries) == 32, '32 declared cases required')
        opt.require(digest(PRIOR/'plan.json') == manifest['plan.json'], 'prior plan changed')
        pins[str(PRIOR/'plan.json')] = digest(PRIOR/'plan.json')
    return dict(schema='river-soft-assignment-pilot-v1', milestone=NAME,
                status='synthetic rehearsal' if synthetic else 'awaiting retained-run approval',
                synthetic=synthetic, entries=entries,
                capacities=[1, 2] if synthetic else [8, 16, 32],
                checkpoints=[3, 10] if synthetic else [1000, 10000],
                timer_seconds=.001 if synthetic else .1, timer_repeats=3,
                timer_iteration_cap=100 if synthetic else 100000,
                phase_timeout_seconds=60 if synthetic else 1800,
                output=str(Path(output).resolve()), pins=pins, methods=list(METHODS),
                python=sys.version, numpy=np.__version__, scipy=scipy.__version__,
                fitting_tasks=0)


def bindings(plan):
    opt.require(not tracemalloc.is_tracing(), 'tracing must be off')
    opt.require(plan['schema'] == 'river-soft-assignment-pilot-v1' and
                plan['methods'] == list(METHODS) and type(plan['synthetic']) is bool,
                'wrong plan schema')
    for path, expected in plan['pins'].items():
        opt.require(digest(path) == expected, 'binding changed: '+path)
    opt.require(plan['python'] == sys.version and plan['numpy'] == np.__version__ and
                plan['scipy'] == scipy.__version__, 'environment changed')
    if not plan['synthetic']:
        opt.require(plan['capacities'] == [8, 16, 32] and
                    plan['checkpoints'] == [1000, 10000] and
                    plan['timer_seconds'] == .1 and plan['timer_repeats'] == 3 and
                    plan['timer_iteration_cap'] == 100000 and
                    plan['phase_timeout_seconds'] == 1800 and len(plan['entries']) == 32,
                    'retained design changed')


def load_case(plan, entry, cache):
    if plan['synthetic']:
        m = PayoffGame(np.eye(2)/2, np.zeros((2, 2)), np.eye(2)/2,
                       np.diag([1., -1.]), None, 'synthetic')
        return m, [np.array([[0.], [1.]])]*2
    row = read(entry['path'])
    opt.require(row['case'] == entry['case'] and row['bet'] == entry['bet'], 'case identity')
    inputs = row['inputs']
    ranges = [{tuple(h): w for h, w in rows} for rows in inputs['ranges']]
    game = RiverHoldem.from_independent_ranges(board=entry['case']['board'], pot=10,
        stacks=(20, 20), bet_size=entry['bet'],
        player0_weights=ranges[0], player1_weights=ranges[1])
    m = PayoffGame.from_river(game)
    opt.require(m.joint.shape == (96, 96) and game.provenance_digest == row['provenance_digest']
                and m.joint.tolist() == inputs['joint'] and
                [[list(h) for h in pool] for pool in m.hands] == inputs['hands'],
                'game reconstruction mismatch')
    board = tuple(game.board)
    if board not in cache:
        cache[board] = uniform_equities(board)
    models = read(MODEL)['models']
    features = []
    for seat in (0, 1):
        raw = raw_features(m, cache[board], seat)
        opt.require(raw.tolist() == row['raw_features'][seat], 'raw feature mismatch')
        x = design(raw)
        # Same retained four-head inference; no fitting or test-target access.
        model = models[seat]
        opt.require(len(model) == 4, 'four frozen heads required')
        f = np.column_stack([np.full(len(x), head['constant'])
                             if head['constant'] is not None else
                             expit(x @ np.asarray(head['coefficients'])) for head in model])
        features.append(f)
    return m, features


def proposals(matrix, features, k):
    result = {m: [] for m in METHODS}
    labels = []
    for seat in (0, 1):
        mass = matrix.joint.sum(axis=1-seat)
        g = anchored_clusters(features[seat], mass, k)
        hard, mixed = soft.assignments(features[seat], mass, g)
        labels.append(g.tolist())
        result['hard'].append(hard)
        result['soft'].append(mixed)
    return result, labels


def scalar_score(matrix, hand):
    x, y = hand
    n, m = matrix.joint.shape
    check = [fsum(float(matrix.check[i, j]) for j in range(m)) for i in range(n)]
    betting = [fsum((1-y[j])*float(matrix.fold[i, j])+y[j]*float(matrix.call[i, j])
                    for j in range(m)) for i in range(n)]
    upper = fsum(max(c, b) for c, b in zip(check, betting))
    lower = fsum((1-x[i])*check[i] for i in range(n))+fsum(
        min(fsum(x[i]*float(matrix.fold[i, j]) for i in range(n)),
            fsum(x[i]*float(matrix.call[i, j]) for i in range(n))) for j in range(m))
    return (upper-lower)/2


def score(matrix, weights, values):
    hand = [p @ np.asarray(v) for p, v in zip(weights, values, strict=True)]
    actual = matrix.evaluate(*hand)['exploitability']
    low, high = soft.exact_bounds(matrix, weights, values, unrestricted=True)
    exact = (high-low)/2
    scalar = scalar_score(matrix, hand)
    opt.require(abs(actual-scalar) <= 1e-10 and abs(actual-float(exact)) <= 1e-10,
                'independent evaluation mismatch')
    return dict(hand_probabilities=[v.tolist() for v in hand], exploitability=actual,
                exact_exploitability=str(exact), scalar_exploitability=scalar)


def trajectory(matrix, weights, plan, *, timed=False):
    setup = perf_counter()
    engine = soft.RegretBR(matrix, weights)
    setup_seconds = perf_counter()-setup
    records = []
    if timed:
        start = perf_counter()
        while engine.iteration < plan['timer_iteration_cap']:
            engine.step()
            if perf_counter()-start >= plan['timer_seconds']:
                break
        elapsed = perf_counter()-start
        records.append(dict(iteration=engine.iteration, coefficients=[v.tolist() for v in
                       engine.average()], active_seconds=elapsed, kind='time'))
    else:
        total = 0.
        for checkpoint in plan['checkpoints']:
            start = perf_counter()
            while engine.iteration < checkpoint:
                engine.step()
            total += perf_counter()-start
            records.append(dict(iteration=engine.iteration, coefficients=[v.tolist() for v in
                           engine.average()], active_seconds=total, kind='updates'))
    for record in records:
        record.update(score(matrix, weights, record['coefficients']))
        record['setup_seconds'] = setup_seconds
    return records


def worker(plan, out):
    bindings(plan)
    cache, index = {}, 0
    for entry in plan['entries']:
        start = perf_counter()
        matrix, features = load_case(plan, entry, cache)
        preparation = perf_counter()-start
        for k in plan['capacities']:
            start = perf_counter()
            pairs, labels = proposals(matrix, features, k)
            row = dict(entry=entry, capacity=k, labels=labels,
                       preparation_seconds=preparation, assignment_seconds=perf_counter()-start,
                       features=[f.tolist() for f in features], methods={})
            order = METHODS if index % 2 == 0 else METHODS[::-1]
            for method in order:
                weights = pairs[method]
                start = perf_counter()
                solution = soft.solve(matrix, weights)
                row['methods'][method] = dict(weights=[w.tolist() for w in weights],
                    solution=solution, lp_seconds=perf_counter()-start,
                    nonzero_weights=[int(np.count_nonzero(w)) for w in weights],
                    dense_weight_bytes=sum(w.nbytes for w in weights),
                    policy_parameters=sum(w.shape[1] for w in weights),
                    records=trajectory(matrix, weights, plan), timed=[])
            for repeat in range(plan['timer_repeats']):
                order = METHODS if (index+repeat) % 2 == 0 else METHODS[::-1]
                for method in order:
                    row['methods'][method]['timed'].append(
                        trajectory(matrix, pairs[method], plan, timed=True)[0])
            write(out/f'cell-{index:03d}.json', row)
            index += 1
        print(f'prepared and solved {entry["case"]["id"]}, bet {entry["bet"]}', flush=True)
    bindings(plan)
    write(out/'worker-complete.json', dict(complete=True, paired_cells=index,
        lp_calls=index*4, fixed_trajectories=index*2, timed_trajectories=index*6, fitting_tasks=0))


def statistics(rows):
    bounds, actual, timed = {}, {}, {}
    for method in METHODS:
        bounds[method] = [sum(Q(r['methods'][method]['solution']['minimum_exploitability'][key])
                              for r in rows)/len(rows) for key in ('lower_exact', 'upper_exact')]
        actual[method] = sum(Q(r['methods'][method]['records'][-1]['exact_exploitability'])
                             for r in rows)/len(rows)
        timed[method] = sum(Q(p['exact_exploitability']) for r in rows
                            for p in r['methods'][method]['timed'])/(len(rows)*3)
    lo, hi = bounds['soft'][0]-bounds['hard'][1], bounds['soft'][1]-bounds['hard'][0]
    return dict(cells=len(rows), floor_delta=opt.interval(lo, hi),
                floors={m: opt.interval(*v) for m, v in bounds.items()},
                actual={m: float(v) for m, v in actual.items()},
                actual_delta_exact=str(actual['soft']-actual['hard']),
                timed={m: float(v) for m, v in timed.items()},
                timed_delta_exact=str(timed['soft']-timed['hard']))


def summary(rows, plan):
    panels = {}
    for bet in sorted({r['entry']['bet'] for r in rows}):
        for k in plan['capacities']:
            rs = [r for r in rows if r['capacity'] == k and r['entry']['bet'] == bet]
            result = dict(overall=statistics(rs))
            for category, key in (('boards', 'board_index'), ('textures', 'texture'),
                                  ('regimes', 'regime')):
                result[category] = {str(v): statistics([r for r in rs
                    if r['entry']['case'][key] == v]) for v in sorted(
                    {r['entry']['case'][key] for r in rs})}
            boards = sorted({r['entry']['case']['board_index'] for r in rs})
            result['leave_one_board_out'] = {str(b): statistics([r for r in rs
                if r['entry']['case']['board_index'] != b]) for b in boards if len(boards) > 1}
            panels[f'bet-{bet}-k-{k}'] = result
    flags = None
    if not plan['synthetic']:
        primary = panels['bet-5-k-16']['overall']
        support = Q(primary['floor_delta']['upper_exact']) < -Q('1e-8')
        flags = dict(representation_support=support, practical_support=support and
                     Q(primary['actual_delta_exact']) < -Q('1e-6'))
    return dict(complete=True, synthetic=plan['synthetic'], panels=panels, flags=flags,
                meaning='Observed-panel descriptive pilot; no fresh-board or six-max claim.')


def verify(plan, out):
    bindings(plan)
    saved_lp = opt.linprog
    def forbidden(*args, **kwargs):
        raise AssertionError('verifier must not solve an LP')
    opt.linprog = forbidden
    cache, rows = {}, []
    certificates = profiles = replayed = 0
    try:
        for entry in plan['entries']:
            matrix, features = load_case(plan, entry, cache)
            for k in plan['capacities']:
                row = read(out/f'cell-{len(rows):03d}.json')
                weights, labels = proposals(matrix, features, k)
                opt.require(row['entry'] == entry and row['capacity'] == k and
                            row['labels'] == labels and
                            row['features'] == [f.tolist() for f in features],
                            'cell reconstruction mismatch')
                for method in METHODS:
                    value = row['methods'][method]
                    opt.require(value['weights'] == [w.tolist() for w in weights[method]],
                                'weight reconstruction mismatch')
                    floor = soft.verify(matrix, weights[method], value['solution'])
                    certificates += 2
                    opt.require([r['iteration'] for r in value['records']] == plan['checkpoints']
                                and len(value['timed']) == plan['timer_repeats'],
                                'checkpoint census')
                    runs = [value['records']]+[[r] for r in value['timed']]
                    for trial, records in enumerate(runs):
                        engine = soft.RegretBR(matrix, weights[method])
                        for record in records:
                            n = record['iteration']
                            opt.require(type(n) is int and 0 < n <= plan['timer_iteration_cap'],
                                        'invalid iteration count')
                            opt.require(record['kind'] == ('updates' if trial == 0 else 'time') and
                                        np.isfinite(record['active_seconds']) and
                                        record['active_seconds'] >= 0, 'invalid timer record')
                            if trial:
                                opt.require(record['active_seconds'] >= plan['timer_seconds'] or
                                            n == plan['timer_iteration_cap'], 'short timer trial')
                            while engine.iteration < n:
                                engine.step()
                                replayed += 1
                            expected = [v.tolist() for v in engine.average()]
                            opt.require(expected == record['coefficients'],
                                        'trajectory replay mismatch')
                            scored = score(matrix, weights[method], expected)
                            opt.require(all(record[key] == value for key, value in scored.items()),
                                        'score reconstruction mismatch')
                            opt.require(Q(record['exact_exploitability']) >=
                                        Q(floor['lower_exact']),
                                        'actual contradicts certified floor')
                            profiles += 1
                rows.append(row)
            print(f'verified {entry["case"]["id"]}, bet {entry["bet"]}', flush=True)
        expected = dict(complete=True, paired_cells=len(rows), lp_calls=len(rows)*4,
            fixed_trajectories=len(rows)*2, timed_trajectories=len(rows)*6, fitting_tasks=0)
        opt.require(read(out/'worker-complete.json') == expected, 'worker census mismatch')
        bindings(plan)
        write(out/'summary.json', summary(rows, plan))
        write(out/'audit.json', dict(passed=True, certificates=certificates,
              profiles=profiles, replayed_updates=replayed, verifier_lp_calls=0, fitting_tasks=0))
    finally:
        opt.linprog = saved_lp


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
