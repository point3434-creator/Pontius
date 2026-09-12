"""Bounded development screen for one fixed witness-action-value representation."""
from __future__ import annotations

import argparse
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('retained_group_diagnostic',
                                            ROOT/'tools/river_group_optimality.py')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)  # Reuse admission, input reconstruction and evidence helpers.
from pontius.river_group_optimality import require, solve_groups  # noqa: E402
from pontius.river_witness_groups import METHODS, propose, result_record, verify_record  # noqa: E402

IDS = base.IDS[:4]
SOURCES = (*base.SOURCES, 'src/pontius/river_witness_groups.py',
           'tools/river_witness_groups.py', 'docs/research/river-witness-groups.md')


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def source_hashes():
    return {name: digest(ROOT/name) for name in SOURCES}


def file_binding(path):
    return dict(path=str(path.resolve()), sha256=digest(path))


def make_plan(output, *, smoke_directory=None, witness_directory=None):
    source = base.make_plan(output, smoke_directory=smoke_directory)
    directory = witness_directory or ROOT/'experiments/river-abstraction-study/group-optimality-001'
    cases = source['cases'][:4] if smoke_directory is None else source['cases']
    for case in cases:
        witness = directory/(case['id']+'.json')
        case.update(witness_file=str(witness.resolve()), witness_sha256=digest(witness))
    return dict(schema='river-witness-groups-v1', mode='development' if smoke_directory is None
                else 'smoke', hands=source['hands'], steps=source['steps'],
                python=source['python'], numpy=source['numpy'], scipy=source['scipy'],
                executable=sys.executable, timeout_seconds=120,
                output_directory=str(output.resolve()), sources=source_hashes(), cases=cases,
                witness_plan=file_binding(directory/'plan.json'),
                witness_manifest=file_binding(directory/'manifest.json'))


def input_case(case):
    return {k: case[k] for k in ('id', 'directory', 'files')}


def verify_bindings(plan):
    keys = {'schema', 'mode', 'hands', 'steps', 'python', 'numpy', 'scipy', 'executable',
            'timeout_seconds', 'output_directory', 'sources', 'cases', 'witness_plan',
            'witness_manifest'}
    require(type(plan) is dict and set(plan) == keys and
            plan['schema'] == 'river-witness-groups-v1', 'invalid plan schema')
    require(plan['mode'] in ('development', 'smoke'), 'development only')
    observed = plan['mode'] == 'development'
    require(type(plan['hands']) is int and plan['hands'] == (96 if observed else 2) and
            plan['steps'] == ([100, 1000, 10000] if observed else [10]) and
            all(type(n) is int for n in plan['steps']), 'input schedule mismatch')
    require(type(plan['timeout_seconds']) is int and plan['timeout_seconds'] == 120,
            'worker limit changed')
    require(plan['python'] == '3.14.6' and sys.version_info[:3] == (3, 14, 6) and
            plan['numpy'] == base.np.__version__ == '2.5.2' and
            plan['scipy'] == base.scipy.__version__ == '1.18.0' and
            plan['executable'] == sys.executable, 'environment mismatch')
    require(Path(plan['output_directory']).is_absolute(), 'absolute output required')
    require(plan['sources'] == source_hashes(), 'source drift')
    for key in ('witness_plan', 'witness_manifest'):
        binding = plan[key]
        require(set(binding) == {'path', 'sha256'} and Path(binding['path']).is_absolute() and
                digest(Path(binding['path'])) == binding['sha256'], 'witness binding drift')
    directory = Path(plan['witness_manifest']['path']).parent
    require(Path(plan['witness_manifest']['path']).name == 'manifest.json' and
            Path(plan['witness_plan']['path']) == directory/'plan.json', 'witness root mismatch')
    manifest = base.read(directory/'manifest.json')
    producer = base.read(directory/'plan.json')
    require(manifest['plan.json'] == plan['witness_plan']['sha256'] and
            producer['schema'] == 'river-group-optimality-v1' and
            producer['mode'] == ('observed' if observed else 'smoke') and
            type(producer['hands']) is int and producer['hands'] == plan['hands'] and
            producer['steps'] == plan['steps'] and producer['sources'] == base.hashes(),
            'witness producer mismatch')
    require([c['id'] for c in plan['cases']] == (IDS if observed else ['smoke']),
            'case grid changed')
    for case in plan['cases']:
        require(set(case) == {'id', 'directory', 'files', 'witness_file', 'witness_sha256'},
                'case schema mismatch')
        matches = [c for c in producer['cases'] if c['id'] == case['id']]
        require(matches == [input_case(case)], 'witness uses different case inputs')
        require(Path(case['directory']).is_absolute() and set(case['files']) == set(base.FILES),
                'invalid case input binding')
        for name, h in case['files'].items():
            require(digest(Path(case['directory'])/name) == h, 'input drift')
        witness = directory/(case['id']+'.json')
        require(Path(case['witness_file']) == witness and digest(witness) ==
                case['witness_sha256'] == manifest[witness.name], 'witness case drift')


def load_case(case, plan):
    matrix, groups, _ = base.load_case(input_case(case), hands=plan['hands'], steps=plan['steps'])
    require(digest(Path(case['witness_file'])) == case['witness_sha256'], 'witness case drift')
    bank = base.read(Path(case['witness_file']))
    require(bank['case'] == case['id'], 'witness case identity')
    return matrix, groups, bank


def summarize(plan, results):
    require([r['case'] for r in results] == (IDS if plan['mode'] == 'development' else ['smoke']),
            'incomplete result grid')
    comparisons = {}
    for name in METHODS:
        values = [r['comparisons'][name] for r in results]
        comparisons[name] = dict(**base.mean_interval(values), case_counts={
            key: sum(v['classification'] == key for v in values)
            for key in ('lower', 'higher', 'overlapping')})
    return dict(complete=True, cohort=plan['mode'], candidate_method_cases=len(results),
                lp_calls_planned=2*len(results), primary_control='range_equity',
                secondary_control='range_response',
                minimum_exploitability=base.mean_interval([
                    r['solution']['minimum_exploitability'] for r in results]),
                comparisons=comparisons, cases=results,
                interpretation='Oracle-assisted development screen at matched group capacity; '
                'prior witness construction cost excluded; no fresh holdout or strength claim.')


def read_plan(path, expected):
    raw = path.read_bytes()
    require(sha256(raw).hexdigest() == expected, 'plan digest mismatch')
    plan = base.parse(raw)
    verify_bindings(plan)
    return raw, plan


def worker(path, expected):
    _, plan = read_plan(path, expected)
    output = Path(plan['output_directory'])
    for case in plan['cases']:
        matrix, groups, bank = load_case(case, plan)
        proposal = propose(matrix, groups, bank)
        solution = solve_groups(matrix, proposal['groups'])
        base.write_json(output/(case['id']+'.json'), result_record(matrix, groups, bank, solution))
    verify_bindings(plan)


def execute_plan(path, expected):
    raw, plan = read_plan(path, expected)
    output = Path(plan['output_directory'])
    output.mkdir(parents=True, exist_ok=False)
    started = perf_counter()
    try:
        with (output/'plan.json').open('xb') as stream:
            stream.write(raw)
        command = [sys.executable, '-B', str(ROOT/'tools/river_witness_groups.py'),
                   'worker', '--plan', str(path.resolve()), '--sha256', expected]
        base.write_json(output/'started.json', dict(command=command, plan_sha256=expected))
        environment = os.environ.copy()
        environment['PYTHONDONTWRITEBYTECODE'] = '1'
        environment.pop('PYTHONTRACEMALLOC', None)
        try:
            child = subprocess.run(command, cwd=ROOT, env=environment,
                                   capture_output=True, timeout=plan['timeout_seconds'])
        except subprocess.TimeoutExpired as error:
            (output/'stdout.txt').write_bytes(error.stdout or b'')
            (output/'stderr.txt').write_bytes(error.stderr or b'')
            raise
        (output/'stdout.txt').write_bytes(child.stdout)
        (output/'stderr.txt').write_bytes(child.stderr)
        base.write_json(output/'receipt.json', dict(exit=child.returncode,
                                                   seconds=perf_counter()-started))
        require(child.returncode == 0, 'witness grouping worker failed')
        results = []
        for case in plan['cases']:
            matrix, groups, bank = load_case(case, plan)
            result = base.read(output/(case['id']+'.json'))
            results.append(verify_record(matrix, groups, bank, result))
        verify_bindings(plan)
        summary = summarize(plan, results)
        base.write_json(output/'summary.json', summary)
        base.write_json(output/'manifest.json', {p.name: digest(p)
                                                for p in sorted(output.iterdir()) if p.is_file()})
        return summary
    except BaseException as error:
        base.write_json(output/'failed.json', dict(complete=False, error=type(error).__name__,
                                                  message=str(error)))
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('plan', 'run', 'worker'))
    parser.add_argument('--plan', required=True, type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--sha256')
    args = parser.parse_args()
    if args.operation == 'plan':
        require(args.output is not None and args.sha256 is None, 'plan output required')
        base.write_json(args.plan, make_plan(args.output))
        print(digest(args.plan))
    else:
        require(args.output is None and args.sha256 is not None, 'bound invocation only')
        if args.operation == 'worker':
            worker(args.plan, args.sha256)
        else:
            result = execute_plan(args.plan, args.sha256)
            print(json.dumps(dict(complete=result['complete'],
                                  cases=result['candidate_method_cases'])))


if __name__ == '__main__':
    main()
