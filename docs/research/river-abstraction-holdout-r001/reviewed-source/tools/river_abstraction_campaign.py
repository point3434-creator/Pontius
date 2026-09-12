"""Bounded, fixed-grid river study plans and sequential execution."""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from math import fsum, isfinite
import os
from pathlib import Path
import subprocess
import sys
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
DRIVER_SOURCES = (
    'src/pontius/river_abstraction_study.py', 'src/pontius/river.py',
    'src/pontius/game.py', 'src/pontius/__init__.py', 'tools/river_abstraction_study.py',
    'docs/research/river-abstraction-study.md',
)
SOURCES = DRIVER_SOURCES + ('tools/river_abstraction_campaign.py',
                             'docs/research/river-abstraction-holdout.md')
METHODS = ('exact', 'uniform_equity_200', 'range_equity', 'range_response')
CRITERION = 'equal_weight_mean_full_exploitability_at_final_checkpoint'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def pairs(items):
    result = {}
    for key, value in items:
        require(key not in result, 'duplicate JSON key')
        result[key] = value
    return result


def parse_json(raw):
    return json.loads(raw, object_pairs_hook=pairs,
                      parse_constant=lambda value: require(False, 'nonfinite JSON'))


def read_json(path):
    return parse_json(path.read_bytes())


def write_json(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n')


def source_hashes():
    return {name: sha256((ROOT / name).read_bytes()).hexdigest() for name in SOURCES}


def make_plan(output, *, split='holdout', hands=96, iterations=10000):
    plan = dict(schema='river-abstraction-campaign-v1', split=split, hands=hands,
                iterations=iterations, case_timeout_seconds=60,
                output_directory=str(output.resolve()), python='3.14.6', numpy='2.5.2',
                source_sha256=source_hashes(), primary_criterion=CRITERION,
                cases=[dict(id=f'{split}-{b}-{r}', board=b, regime=r)
                       for b in (0, 1) for r in ('uniform', 'polarized')])
    validate_plan(plan)
    return plan


def validate_plan(plan):
    keys = {'schema', 'split', 'hands', 'iterations', 'case_timeout_seconds',
            'output_directory', 'python', 'numpy', 'source_sha256', 'primary_criterion', 'cases'}
    require(type(plan) is dict and set(plan) == keys, 'invalid plan schema')
    require(plan['schema'] == 'river-abstraction-campaign-v1', 'unknown schema')
    require(plan['split'] in ('development', 'holdout'), 'unknown split')
    for key, low, high in [('hands', 2, 96), ('iterations', 1, 10000),
                           ('case_timeout_seconds', 60, 60)]:
        require(type(plan[key]) is int and low <= plan[key] <= high, 'invalid ' + key)
    if plan['split'] == 'holdout':
        require((plan['hands'], plan['iterations']) == (96, 10000), 'holdout schedule is fixed')
    require(plan['python'] == '3.14.6' and plan['numpy'] == '2.5.2', 'environment must be pinned')
    require(plan['primary_criterion'] == CRITERION, 'comparison criterion is fixed')
    require(isinstance(plan['output_directory'], str) and
            Path(plan['output_directory']).is_absolute(), 'absolute output directory required')
    expected = [dict(id=f"{plan['split']}-{b}-{r}", board=b, regime=r)
                for b in (0, 1) for r in ('uniform', 'polarized')]
    require(plan['cases'] == expected and all(type(c['board']) is int for c in plan['cases']),
            'four exact ordered cases required')
    require(type(plan['source_sha256']) is dict and set(plan['source_sha256']) == set(SOURCES),
            'source inventory mismatch')


def compare_metrics(actual, expected):
    require(type(actual) is dict and set(actual) == set(expected), 'metric schema mismatch')
    require(all(type(actual[k]) in (float, int) and isfinite(actual[k]) and
                abs(actual[k] - v) <= 1e-11 for k, v in expected.items()), 'metric mismatch')


def verify_case(directory, plan, case):
    # This repeats input preparation and evaluation, never training or an opponent draw.
    from pontius.river_abstraction_study import (
        DEVELOPMENT_BOARDS, HOLDOUT_BOARDS, PayoffGame, representations, study_case,
    )
    manifest = read_json(directory / 'manifest.json')
    require(set(manifest) == {'started.json', 'inputs.json', 'result.json'},
            'case manifest mismatch')
    for name, digest in manifest.items():
        require(sha256((directory / name).read_bytes()).hexdigest() == digest,
                'case digest mismatch')
    started = read_json(directory / 'started.json')
    inputs = read_json(directory / 'inputs.json')
    result = read_json(directory / 'result.json')
    boards = DEVELOPMENT_BOARDS if plan['split'] == 'development' else HOLDOUT_BOARDS
    board = boards[case['board']]
    require(started['source_sha256'] == {p: plan['source_sha256'][p] for p in DRIVER_SOURCES},
            'child source mismatch')
    require(started['numpy'] == plan['numpy'] and started['python'] == sys.version,
            'child environment mismatch')
    require(started['split'] == result['split'] == plan['split'] and
            started['board'] == list(board) and started['regime'] == case['regime'] and
            type(started['iterations']) is int and started['iterations'] == plan['iterations'] and
            type(started['hands_per_player']) is int and
            started['hands_per_player'] == plan['hands'],
            'child configuration mismatch')
    require(result['complete'] is True, 'incomplete child')
    game, equities, ranges = study_case(board, plan['hands'], case['regime'], split=plan['split'])
    matrix = PayoffGame.from_river(game)
    methods = representations(matrix, equities)
    expected_inputs = dict(
        board=list(board), pot=game.pot, bet=game.bet_size, stacks=list(game.stacks),
        provenance_digest=game.provenance_digest,
        ranges=[[[list(h), w] for h, w in sorted(r.items())] for r in ranges],
        hands=[[list(h) for h in pool] for pool in matrix.hands], joint=matrix.joint.tolist(),
        uniform_equities=[[equities[h] for h in pool] for pool in matrix.hands],
        groups={m: [g.tolist() for g in groups] for m, groups in methods.items()})
    require(inputs == expected_inputs, 'case inputs differ from bound preparation')
    require(type(result['accepted_joint_deals']) is int and
            result['accepted_joint_deals'] == len(game.deals), 'population count mismatch')
    steps = sorted({min(n, plan['iterations']) for n in (100, 1000, 10000)})
    records = result['records']
    require(all(type(r['iteration']) is int for r in records), 'invalid checkpoint counter')
    require(len(records) == len(METHODS) * len(steps) and
            {(r['method'], r['iteration']) for r in records} ==
            {(m, n) for m in METHODS for n in steps}, 'incomplete or duplicated checkpoint grid')
    for record in records:
        groups = methods[record['method']]
        reduced = matrix.aggregate(groups)
        x, y = record['group_bet'], record['group_call']
        require(all(type(p) in (int, float) for p in x + y), 'non-numeric policy')
        restricted = reduced.evaluate(x, y)
        lifted = ([x[g] for g in groups[0]], [y[g] for g in groups[1]])
        require(record['hand_bet'] == lifted[0] and record['hand_call'] == lifted[1],
                'lifted policy mismatch')
        require(record['occupied_groups'] == list(reduced.joint.shape), 'capacity mismatch')
        full = matrix.evaluate(*lifted)
        for name, metrics in [('full_game', full), ('restricted_game', restricted)]:
            compare_metrics(record[name], metrics)
            compare_metrics(record[name + '_fraction_of_pot'], {k: v / game.pot
                                                               for k, v in metrics.items()})
    return [dict(record, case=case['id']) for record in records]


def execute_plan(path, expected_sha):
    raw = path.read_bytes()
    require(sha256(raw).hexdigest() == expected_sha, 'plan digest mismatch')
    plan = parse_json(raw)
    validate_plan(plan)
    require(source_hashes() == plan['source_sha256'], 'source drift')
    require(sys.version_info[:3] == (3, 14, 6), 'Python 3.14.6 required')
    import numpy as np
    require(np.__version__ == plan['numpy'], 'NumPy version mismatch')
    output = Path(plan['output_directory'])
    output.mkdir(parents=True, exist_ok=False)
    receipts, records = [], []
    try:
        with (output / 'plan.json').open('xb') as stream:
            stream.write(raw)
        write_json(output / 'started.json', {'plan_sha256': expected_sha, 'python': sys.version})
        environment = os.environ.copy()
        environment['PYTHONDONTWRITEBYTECODE'] = '1'
        environment.pop('PYTHONTRACEMALLOC', None)
        for name in ('OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'OMP_NUM_THREADS'):
            environment[name] = '1'
        for case in plan['cases']:
            label = case['id']
            require(source_hashes() == plan['source_sha256'], 'source drift before launch')
            command = [sys.executable, '-B', str(ROOT / 'tools/river_abstraction_study.py'),
                       '--output', str(output / label), '--split', plan['split'],
                       '--board', str(case['board']), '--regime', case['regime'],
                       '--hands', str(plan['hands']), '--iterations', str(plan['iterations'])]
            write_json(output / (label + '-start.json'), {'command': command})
            started = perf_counter()
            try:
                child = subprocess.run(command, cwd=ROOT, env=environment, capture_output=True,
                                       timeout=plan['case_timeout_seconds'])
            except subprocess.TimeoutExpired as error:
                (output / (label + '-stdout.txt')).write_bytes(error.stdout or b'')
                (output / (label + '-stderr.txt')).write_bytes(error.stderr or b'')
                raise
            (output / (label + '-stdout.txt')).write_bytes(child.stdout)
            (output / (label + '-stderr.txt')).write_bytes(child.stderr)
            receipt = dict(case=label, exit=child.returncode, seconds=perf_counter() - started)
            receipts.append(receipt)
            write_json(output / (label + '-receipt.json'), receipt)
            if child.returncode:
                raise RuntimeError(f'child failed: {label}, exit {child.returncode}')
            records.extend(verify_case(output / label, plan, case))
        require(source_hashes() == plan['source_sha256'], 'source drift before completion')
        steps = sorted({r['iteration'] for r in records})
        means = {str(n): {m: fsum(r['full_game']['exploitability'] for r in records
                                  if r['iteration'] == n and r['method'] == m) / 4
                          for m in METHODS} for n in steps}
        summary = dict(complete=True, split=plan['split'], primary_criterion=CRITERION,
                       mean_full_exploitability=means, records=records, receipts=receipts)
        write_json(output / 'summary.json', summary)
        write_json(output / 'manifest.json', {
            p.relative_to(output).as_posix(): sha256(p.read_bytes()).hexdigest()
            for p in sorted(output.rglob('*')) if p.is_file()})
        return summary
    except BaseException as error:
        write_json(output / 'failed.json', dict(complete=False, error=type(error).__name__,
                                               message=str(error), receipts=receipts))
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='operation', required=True)
    build = commands.add_parser('plan')
    build.add_argument('--write', type=Path, required=True)
    build.add_argument('--output-directory', type=Path, required=True)
    build.add_argument('--split', choices=('development', 'holdout'), default='holdout')
    build.add_argument('--hands', type=int, default=96)
    build.add_argument('--iterations', type=int, default=10000)
    run = commands.add_parser('run')
    run.add_argument('--plan', type=Path, required=True)
    run.add_argument('--sha256', required=True)
    args = parser.parse_args()
    if args.operation == 'plan':
        write_json(args.write, make_plan(args.output_directory, split=args.split,
                                         hands=args.hands, iterations=args.iterations))
        print(sha256(args.write.read_bytes()).hexdigest())
    else:
        result = execute_plan(args.plan, args.sha256)
        print(json.dumps({'complete': result['complete'], 'records': len(result['records'])}))


if __name__ == '__main__':
    main()
