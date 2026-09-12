"""Bounded 8-board x 3-pool x 2-range pilot; planning does not score any fresh case."""
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
import tracemalloc

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    'retained_helpers',ROOT/'tools/river_group_optimality.py')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)  # Sets one BLAS thread before NumPy import.
from pontius.river_abstraction_study import DEVELOPMENT_BOARDS, uniform_equities  # noqa: E402
from pontius.river_group_optimality import require  # noqa: E402
from pontius.river_witness_pilot import (  # noqa: E402
    SELECTION_SEED, canonical_json, case_grid, select_boards, solve_record,
    summarize, verify_record,
)

SOURCES = (*base.SOURCES,'src/pontius/river_witness_groups.py',
           'docs/research/river-witness-groups.md','src/pontius/river_witness_pilot.py',
           'tools/river_witness_pilot.py','docs/research/river-witness-pilot.md')


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def hashes():
    return {name:digest(ROOT/name) for name in SOURCES}


def make_plan(output, *, smoke=False):
    cases = case_grid([DEVELOPMENT_BOARDS[0]])[:1] if smoke else case_grid(select_boards())
    return dict(schema='river-witness-pilot-v1',mode='smoke' if smoke else 'pilot',
        selection_seed=SELECTION_SEED,hands=2 if smoke else 96,cases=cases,
        lp_calls=10*len(cases),timeout_seconds=1200,python='3.14.6',numpy='2.5.2',scipy='1.18.0',
        executable=sys.executable,output_directory=str(output.resolve()),sources=hashes())


def verify_bindings(plan):
    keys = {'schema','mode','selection_seed','hands','cases','lp_calls','timeout_seconds',
            'python','numpy','scipy','executable','output_directory','sources'}
    require(type(plan) is dict and set(plan) == keys and
            plan['schema'] == 'river-witness-pilot-v1', 'invalid plan schema')
    require(plan['mode'] in ('pilot','smoke') and plan['selection_seed'] == SELECTION_SEED,
            'selection rule changed')
    smoke = plan['mode'] == 'smoke'
    expected = case_grid([DEVELOPMENT_BOARDS[0]])[:1] if smoke else case_grid(select_boards())
    require(canonical_json(plan['cases']) == canonical_json(expected), 'case selection changed')
    require(type(plan['hands']) is int and plan['hands'] == (2 if smoke else 96),
            'pool size changed')
    require(type(plan['lp_calls']) is int and plan['lp_calls'] == 10*len(expected) and
            type(plan['timeout_seconds']) is int and plan['timeout_seconds'] == 1200,
            'workload or timeout changed')
    require(plan['python'] == '3.14.6' and sys.version_info[:3] == (3,14,6) and
            plan['numpy'] == base.np.__version__ == '2.5.2' and
            plan['scipy'] == base.scipy.__version__ == '1.18.0' and
            plan['executable'] == sys.executable, 'environment mismatch')
    require(not tracemalloc.is_tracing(), 'allocation tracing must be disabled')
    require(Path(plan['output_directory']).is_absolute(), 'absolute output required')
    require(plan['sources'] == hashes(), 'source drift')


def read_plan(path, expected):
    raw = path.read_bytes()
    require(sha256(raw).hexdigest() == expected, 'plan digest mismatch')
    plan = base.parse(raw)
    verify_bindings(plan)
    return raw,plan


def equities_for(case, cache):
    board = tuple(case['board'])
    if board not in cache:
        cache[board] = uniform_equities(board)
    return cache[board]


def worker(path, expected):
    _,plan = read_plan(path,expected)
    output,cache = Path(plan['output_directory']),{}
    for case in plan['cases']:
        record = solve_record(case,plan['hands'],equities_for(case,cache))
        base.write_json(output/(case['id']+'.json'),record)
    verify_bindings(plan)


def execute_plan(path, expected):
    raw,plan = read_plan(path,expected)
    output = Path(plan['output_directory'])
    output.mkdir(parents=True,exist_ok=False)
    started = perf_counter()
    try:
        with (output/'plan.json').open('xb') as stream:
            stream.write(raw)
        command = [sys.executable,'-B',str(ROOT/'tools/river_witness_pilot.py'),
                   'worker','--plan',str(path.resolve()),'--sha256',expected]
        base.write_json(output/'started.json',dict(command=command,plan_sha256=expected))
        environment = os.environ.copy()
        environment['PYTHONDONTWRITEBYTECODE'] = '1'
        environment.pop('PYTHONTRACEMALLOC',None)
        try:
            child = subprocess.run(command,cwd=ROOT,env=environment,capture_output=True,
                                   timeout=plan['timeout_seconds'])
        except subprocess.TimeoutExpired as error:
            (output/'stdout.txt').write_bytes(error.stdout or b'')
            (output/'stderr.txt').write_bytes(error.stderr or b'')
            raise
        (output/'stdout.txt').write_bytes(child.stdout)
        (output/'stderr.txt').write_bytes(child.stderr)
        base.write_json(output/'receipt.json',dict(exit=child.returncode,
                                                  seconds=perf_counter()-started))
        require(child.returncode == 0, 'pilot worker failed')
        results,cache = [],{}
        for case in plan['cases']:
            record = base.read(output/(case['id']+'.json'))
            results.append(verify_record(case,plan['hands'],equities_for(case,cache),record))
        verify_bindings(plan)
        summary = summarize(plan['cases'],results)
        base.write_json(output/'summary.json',summary)
        base.write_json(output/'manifest.json',{p.name:digest(p)
                                               for p in sorted(output.iterdir()) if p.is_file()})
        return summary
    except BaseException as error:
        base.write_json(output/'failed.json',dict(complete=False,error=type(error).__name__,
                                                 message=str(error)))
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation',choices=('plan','run','worker'))
    parser.add_argument('--plan',required=True,type=Path)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--sha256')
    args = parser.parse_args()
    if args.operation == 'plan':
        require(args.output is not None and args.sha256 is None, 'plan output required')
        base.write_json(args.plan,make_plan(args.output))
        print(digest(args.plan))
    else:
        require(args.output is None and args.sha256 is not None, 'bound plan only')
        if args.operation == 'worker':
            worker(args.plan,args.sha256)
        else:
            result = execute_plan(args.plan,args.sha256)
            print(json.dumps(dict(complete=result['complete'],cases=result['case_count'])))


if __name__ == '__main__':
    main()
