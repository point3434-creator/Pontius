"""Bounded diagnostic of fixed groups from already observed river study cases."""
from __future__ import annotations

import argparse
from fractions import Fraction as Q
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
from time import perf_counter

for variable in ('OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'OMP_NUM_THREADS'):
    os.environ[variable] = '1'
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

import numpy as np  # noqa: E402
import scipy  # noqa: E402
from pontius.river import RiverHoldem  # noqa: E402
from pontius.river_abstraction_study import (  # noqa: E402
    DEVELOPMENT_BOARDS, HOLDOUT_BOARDS, PayoffGame, _labels,
)
from pontius.river_group_optimality import (  # noqa: E402
    compare_saved, interval, require, solve_groups, verify_solution,
)

METHODS = ('exact', 'uniform_equity_200', 'range_equity', 'range_response')
FILES = ('inputs.json', 'result.json', 'started.json', 'manifest.json')
SOURCES = ('src/pontius/__init__.py', 'src/pontius/game.py', 'src/pontius/river.py',
           'src/pontius/river_abstraction_study.py', 'src/pontius/river_group_optimality.py',
           'tools/river_group_optimality.py', 'docs/research/river-group-optimality.md')
IDS = [f'{split}-{b}-{r}' for split in ('development', 'holdout')
       for b in (0, 1) for r in ('uniform', 'polarized')]


def pairs(items):
    result = {}
    for name, value in items:
        require(name not in result, 'duplicate JSON key')
        result[name] = value
    return result


def parse(raw):
    return json.loads(raw, object_pairs_hook=pairs,
                      parse_constant=lambda _: require(False, 'nonfinite JSON'))


def read(path):
    return parse(path.read_bytes())


def write_json(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n')


def hashes():
    return {p: sha256((ROOT / p).read_bytes()).hexdigest() for p in SOURCES}


def bind_case(label, directory):
    return dict(id=label, directory=str(directory.resolve()),
                files={p: sha256((directory / p).read_bytes()).hexdigest() for p in FILES})


def make_plan(output, *, smoke_directory=None):
    cases = []
    for label in IDS if smoke_directory is None else ['smoke']:
        if label == 'smoke':
            directory = smoke_directory
        else:
            split, board, regime = label.split('-')
            subdirectory = f'd{board}-{regime}' if split == 'development' else label
            directory = ROOT / f'experiments/river-abstraction-study/{split}-001' / subdirectory
        cases.append(bind_case(label, directory))
    return dict(schema='river-group-optimality-v1', mode='observed' if smoke_directory is None
                else 'smoke', hands=96 if smoke_directory is None else 2,
                steps=[100, 1000, 10000] if smoke_directory is None else [10],
                python='3.14.6', numpy='2.5.2', scipy='1.18.0', executable=sys.executable,
                timeout_seconds=300, output_directory=str(output.resolve()),
                cases=cases, sources=hashes())


def verify_bindings(plan):
    keys = {'schema', 'mode', 'hands', 'steps', 'python', 'numpy', 'scipy', 'executable',
            'timeout_seconds', 'output_directory', 'cases', 'sources'}
    require(type(plan) is dict and set(plan) == keys and
            plan['schema'] == 'river-group-optimality-v1', 'invalid plan schema')
    require(plan['mode'] in ('observed', 'smoke'), 'unknown mode')
    require(type(plan['hands']) is int and
            plan['hands'] == (96 if plan['mode'] == 'observed' else 2), 'population changed')
    require(plan['steps'] == ([100, 1000, 10000] if plan['mode'] == 'observed' else [10]) and
            all(type(n) is int for n in plan['steps']), 'checkpoint schedule changed')
    require(type(plan['timeout_seconds']) is int and plan['timeout_seconds'] == 300,
            'worker timeout changed')
    require(plan['python'] == '3.14.6' and sys.version_info[:3] == (3, 14, 6) and
            plan['numpy'] == np.__version__ == '2.5.2' and
            plan['scipy'] == scipy.__version__ == '1.18.0' and
            plan['executable'] == sys.executable, 'environment mismatch')
    require(Path(plan['output_directory']).is_absolute(), 'absolute output required')
    require(plan['sources'] == hashes(), 'source drift')
    require([c['id'] for c in plan['cases']] == (IDS if plan['mode'] == 'observed' else ['smoke']),
            'case grid changed')
    for case in plan['cases']:
        require(set(case) == {'id', 'directory', 'files'} and set(case['files']) == set(FILES),
                'case schema mismatch')
        require(Path(case['directory']).is_absolute(), 'absolute input required')
        for name, digest in case['files'].items():
            require(sha256((Path(case['directory']) / name).read_bytes()).hexdigest() == digest,
                    'input drift')


def load_case(case, *, hands, steps):
    directory = Path(case['directory'])
    for name, digest in case['files'].items():
        require(sha256((directory / name).read_bytes()).hexdigest() == digest, 'input drift')
    manifest = read(directory / 'manifest.json')
    require(set(manifest) == set(FILES)-{'manifest.json'} and
            all(manifest[n] == case['files'][n] for n in manifest), 'case manifest mismatch')
    inputs, result, start = (read(directory / n) for n in FILES[:3])
    require(type(start['hands_per_player']) is int and start['hands_per_player'] == hands and
            type(start['iterations']) is int and start['iterations'] == max(steps) and
            start['board'] == inputs['board'], 'case header mismatch')
    if case['id'] != 'smoke':
        split, board, regime = case['id'].split('-')
        expected = (DEVELOPMENT_BOARDS if split == 'development' else HOLDOUT_BOARDS)[int(board)]
        require(inputs['board'] == list(expected) and start['regime'] == regime, 'case identity')
    require(inputs['pot'] == 10 and inputs['bet'] == 5 and inputs['stacks'] == [20, 20],
            'one-bet game geometry changed')
    ranges = [{tuple(h): w for h, w in rows} for rows in inputs['ranges']]
    require(len(ranges) == 2 and all(len(r) == hands for r in ranges) and
            all(len(rows) == hands for rows in inputs['ranges']), 'range population mismatch')
    game = RiverHoldem.from_independent_ranges(
        board=inputs['board'], pot=inputs['pot'], stacks=tuple(inputs['stacks']),
        bet_size=inputs['bet'], player0_weights=ranges[0], player1_weights=ranges[1])
    matrix = PayoffGame.from_river(game)
    require(inputs['provenance_digest'] == game.provenance_digest and
            inputs['joint'] == matrix.joint.tolist() and inputs['hands'] ==
            [[list(h) for h in pool] for pool in matrix.hands], 'game reconstruction mismatch')
    require(result['complete'] is True and type(result['accepted_joint_deals']) is int and
            result['accepted_joint_deals'] == len(game.deals), 'incomplete population')
    groups = inputs['groups']
    require(set(groups) == set(METHODS), 'method inventory changed')
    for method, pair in groups.items():
        require(len(pair) == 2, 'group pair missing')
        for p, g in enumerate(pair):
            _labels(g, hands)
            require(method == 'exact' or len(set(g)) == len(set(groups['uniform_equity_200'][p])),
                    'unequal compressed capacity')
        require(method != 'exact' or pair == [list(range(hands))]*2, 'exact reference compressed')
    records = result['records']
    require(len(records) == len(METHODS)*len(steps) and
            all(type(r['iteration']) is int for r in records) and
            {(r['method'], r['iteration']) for r in records} ==
            {(m, n) for m in METHODS for n in steps}, 'incomplete checkpoint grid')
    for r in records:
        pair = groups[r['method']]
        for p, (group_key, hand_key) in enumerate([('group_bet', 'hand_bet'),
                                                  ('group_call', 'hand_call')]):
            require(len(r[group_key]) == len(set(pair[p])) and
                    r[hand_key] == [r[group_key][g] for g in pair[p]], 'saved policy lift mismatch')
        measured = matrix.evaluate(r['hand_bet'], r['hand_call'])
        require(set(r['full_game']) == set(measured) and all(
            type(r['full_game'][k]) in (int, float) and abs(r['full_game'][k]-v) <= 1e-11
            for k, v in measured.items()), 'saved value mismatch')
    return matrix, groups, records


def diagnostic(matrix, groups, records):
    result = []
    for method in METHODS:
        solution = solve_groups(matrix, groups[method])
        saved = [dict(iteration=r['iteration'], **compare_saved(
            matrix, groups[method], solution, r['hand_bet'], r['hand_call']))
            for r in records if r['method'] == method]
        result.append(dict(method=method, solution=solution, saved=saved))
    return result


def mean_interval(values):
    return interval(sum((Q(v['lower_exact']) for v in values), Q(0))/len(values),
                    sum((Q(v['upper_exact']) for v in values), Q(0))/len(values))


def summarize(plan, results):
    cohorts = {}
    for cohort in ('development', 'holdout') if plan['mode'] == 'observed' else ('smoke',):
        selected = [r for r in results if r['case'].split('-')[0] == cohort]
        cohorts[cohort] = {}
        for method in METHODS:
            rows = [next(m for m in r['methods'] if m['method'] == method) for r in selected]
            floor = mean_interval([m['solution']['minimum_exploitability'] for m in rows])
            checkpoints = {}
            for n in plan['steps']:
                saved = [next(s for s in m['saved'] if s['iteration'] == n) for m in rows]
                value = sum((Q(s['saved_exploitability_exact']) for s in saved), Q(0))/len(saved)
                gap = mean_interval([s['avoidable_gap'] for s in saved])
                checkpoints[str(n)] = dict(saved_exact=str(value), saved_chips_approx=float(value),
                                            avoidable_gap=gap)
            cohorts[cohort][method] = dict(minimum_exploitability=floor, checkpoints=checkpoints)
    return dict(complete=True, verified_method_cases=len(results)*4,
                verified_saved_profiles=len(results)*4*len(plan['steps']),
                headline_iteration=max(plan['steps']), cohorts=cohorts, cases=results,
                interpretation='Observed-case diagnosis; rational bounds on binary64 payoffs; '
                'avoidable gap combines policy-selection and finite-training effects.')


def read_plan(path, digest):
    raw = path.read_bytes()
    require(sha256(raw).hexdigest() == digest, 'plan digest mismatch')
    plan = parse(raw)
    verify_bindings(plan)
    return raw, plan


def worker(path, digest):
    _, plan = read_plan(path, digest)
    output = Path(plan['output_directory'])
    for case in plan['cases']:
        matrix, groups, records = load_case(case, hands=plan['hands'], steps=plan['steps'])
        write_json(output / (case['id']+'.json'), dict(case=case['id'],
                                                     methods=diagnostic(matrix, groups, records)))
    verify_bindings(plan)


def execute_plan(path, digest):
    raw, plan = read_plan(path, digest)
    output = Path(plan['output_directory'])
    output.mkdir(parents=True, exist_ok=False)
    started = perf_counter()
    try:
        with (output / 'plan.json').open('xb') as stream:
            stream.write(raw)
        command = [sys.executable, '-B', str(ROOT / 'tools/river_group_optimality.py'),
                   'worker', '--plan', str(path.resolve()), '--sha256', digest]
        write_json(output / 'started.json', dict(command=command, plan_sha256=digest))
        environment = os.environ.copy()
        environment['PYTHONDONTWRITEBYTECODE'] = '1'
        environment.pop('PYTHONTRACEMALLOC', None)
        try:
            child = subprocess.run(command, cwd=ROOT, env=environment, capture_output=True,
                                   timeout=plan['timeout_seconds'])
        except subprocess.TimeoutExpired as error:
            (output / 'stdout.txt').write_bytes(error.stdout or b'')
            (output / 'stderr.txt').write_bytes(error.stderr or b'')
            raise
        (output / 'stdout.txt').write_bytes(child.stdout)
        (output / 'stderr.txt').write_bytes(child.stderr)
        write_json(output / 'receipt.json', dict(exit=child.returncode,
                                                seconds=perf_counter()-started))
        require(child.returncode == 0, 'diagnostic worker failed')
        results = []
        for case in plan['cases']:
            matrix, groups, records = load_case(case, hands=plan['hands'], steps=plan['steps'])
            result = read(output / (case['id']+'.json'))
            require(result['case'] == case['id'] and
                    [m['method'] for m in result['methods']] == list(METHODS),
                    'result grid mismatch')
            for row in result['methods']:
                pair = groups[row['method']]
                verify_solution(matrix, pair, row['solution'])
                expected = [dict(iteration=r['iteration'], **compare_saved(
                    matrix, pair, row['solution'], r['hand_bet'], r['hand_call']))
                    for r in records if r['method'] == row['method']]
                require(row['saved'] == expected, 'saved-policy comparison mismatch')
            results.append(result)
        verify_bindings(plan)
        summary = summarize(plan, results)
        write_json(output / 'summary.json', summary)
        write_json(output / 'manifest.json', {p.name: sha256(p.read_bytes()).hexdigest()
                                             for p in sorted(output.iterdir()) if p.is_file()})
        return summary
    except BaseException as error:
        write_json(output / 'failed.json', dict(complete=False, error=type(error).__name__,
                                               message=str(error)))
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('plan', 'run', 'worker'))
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--sha256')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.operation == 'plan':
        require(args.output is not None, 'plan output required')
        write_json(args.plan, make_plan(args.output))
        print(sha256(args.plan.read_bytes()).hexdigest())
    else:
        require(args.output is None and args.sha256 is not None, 'bound plan only')
        if args.operation == 'worker':
            worker(args.plan, args.sha256)
        else:
            result = execute_plan(args.plan, args.sha256)
            print(json.dumps(dict(complete=result['complete'],
                                  profiles=result['verified_saved_profiles'])))


if __name__ == '__main__':
    main()
