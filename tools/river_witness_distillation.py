"""Train fixed witness predictors on observed boards and evaluate a reserved panel."""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from time import perf_counter
import tracemalloc

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('pilot_helpers',ROOT/'tools/river_witness_pilot.py')
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)  # Pins BLAS threads before importing NumPy.
base = old.base
from pontius import river_witness_pilot as pilot  # noqa: E402
from pontius import river_witness_distillation as student  # noqa: E402
from pontius.river_abstraction_study import DEVELOPMENT_BOARDS  # noqa: E402
from pontius.river_group_optimality import require  # noqa: E402

TRAINING = ROOT/'experiments/river-abstraction-study/witness-pilot-001'
TRAINING_MANIFEST = 'd3b52b5f3c6046c6c36f2c967fa6d9e5e6f43608465da2cc974f94e54a121032'
TRAINING_PLAN = '535a3fa5b4d55d8bc6cc29763c63b5ab41f89cf0ea190bca90f9c00a5a8c9d2c'
SOURCES = (*old.SOURCES,'src/pontius/river_witness_distillation.py',
           'tools/river_witness_distillation.py','docs/research/river-witness-distillation.md')
digest = old.digest


def training_binding(directory, smoke):
    directory = Path(directory).resolve()
    if not smoke:
        require(directory == TRAINING.resolve(), 'training root changed')
        require(digest(directory/'milestone-manifest.json') == TRAINING_MANIFEST,
                'training milestone identity changed')
        names = base.read(directory/'milestone-manifest.json')
        require(all(digest(directory/name) == h for name,h in names.items()),
                'training milestone member drift')
        require(digest(directory/'plan.json') == TRAINING_PLAN, 'producer plan changed')
        names = [*names,'milestone-manifest.json']
    else:
        names = ['plan.json','b00-p0-uniform.json']
    producer = base.read(directory/'plan.json')
    old.verify_bindings(producer)
    require(producer['mode'] == ('smoke' if smoke else 'pilot'), 'training mode mismatch')
    return dict(directory=str(directory),files={name:digest(directory/name) for name in names})


def hashes():
    return {name:digest(ROOT/name) for name in SOURCES}


def make_plan(output, *, smoke=False, training=TRAINING):
    binding = training_binding(training,smoke)
    training_cases = base.read(Path(binding['directory'])/'plan.json')['cases']
    cases = pilot.case_grid([DEVELOPMENT_BOARDS[1]])[:1] if smoke else pilot.case_grid(
        student.select_boards())
    return dict(schema='river-witness-distillation-v1',mode='smoke' if smoke else 'pilot',
        selection_seed=student.SEED,alpha=student.ALPHA,hands=2 if smoke else 96,
        training=binding,training_cases=training_cases,cases=cases,lp_calls=12*len(cases),
        timeout_seconds=1200,python='3.14.6',numpy='2.5.2',scipy='1.18.0',
        executable=sys.executable,output_directory=str(output.resolve()),sources=hashes())


def verify_bindings(plan):
    keys = {'schema','mode','selection_seed','alpha','hands','training','training_cases','cases',
            'lp_calls','timeout_seconds','python','numpy','scipy','executable',
            'output_directory','sources'}
    require(type(plan) is dict and set(plan) == keys and
            plan['schema'] == 'river-witness-distillation-v1', 'invalid plan schema')
    require(plan['mode'] in ('pilot','smoke') and plan['selection_seed'] == student.SEED and
            type(plan['alpha']) is float and plan['alpha'] == student.ALPHA, 'recipe changed')
    smoke = plan['mode'] == 'smoke'
    cases = pilot.case_grid([DEVELOPMENT_BOARDS[1]])[:1] if smoke else pilot.case_grid(
        student.select_boards())
    require(pilot.canonical_json(plan['cases']) == pilot.canonical_json(cases), 'panel changed')
    require(type(plan['hands']) is int and plan['hands'] == (2 if smoke else 96) and
            type(plan['lp_calls']) is int and plan['lp_calls'] == 12*len(cases) and
            type(plan['timeout_seconds']) is int and plan['timeout_seconds'] == 1200,
            'workload changed')
    require(plan['python'] == '3.14.6' and sys.version_info[:3] == (3,14,6) and
            plan['numpy'] == base.np.__version__ == '2.5.2' and
            plan['scipy'] == base.scipy.__version__ == '1.18.0' and
            plan['executable'] == sys.executable, 'environment mismatch')
    require(not tracemalloc.is_tracing(), 'allocation tracing must be disabled')
    require(Path(plan['output_directory']).is_absolute(), 'absolute output required')
    require(plan['sources'] == hashes(), 'source drift')
    require(type(plan['training']) is dict and set(plan['training']) == {'directory','files'},
            'invalid training binding')
    binding = training_binding(Path(plan['training']['directory']),smoke)
    require(pilot.canonical_json(binding) == pilot.canonical_json(plan['training']),
            'training data drift')
    training_cases = base.read(Path(binding['directory'])/'plan.json')['cases']
    require(pilot.canonical_json(training_cases) == pilot.canonical_json(plan['training_cases']),
            'training panel changed')
    seen = {pilot.canonical_board(c['board']) for c in training_cases}
    require(all(pilot.canonical_board(c['board']) not in seen for c in cases),
            'training/evaluation board overlap')


def read_plan(path, expected):
    require(digest(path) == expected, 'plan digest mismatch')
    raw = path.read_bytes()
    plan = base.parse(raw)
    verify_bindings(plan)
    return raw,plan


def load_training(plan):
    directory,cache,training = Path(plan['training']['directory']),{},[]
    for case in plan['training_cases']:
        equities = old.equities_for(case,cache)
        row = base.read(directory/(case['id']+'.json'))
        pilot.verify_record(case,plan['hands'],equities,row)
        matrix,_,_ = pilot.build_inputs(case,plan['hands'],equities)
        training.append((matrix,equities,row))
    return training


def fitted_record(plan):
    start = perf_counter()
    training = load_training(plan)
    loaded = perf_counter()
    models = student.fit_models(training)
    end = perf_counter()
    return dict(models=models,training_cases=[c['id'] for c in plan['training_cases']],
                validation_seconds=loaded-start,fit_seconds=end-loaded)


def worker(path, expected):
    _,plan = read_plan(path,expected)
    output,cache = Path(plan['output_directory']),{}
    fitted = fitted_record(plan)
    base.write_json(output/'models.json',fitted)  # Frozen before any evaluation-board equity.
    equity_seconds = 0.
    for case in plan['cases']:
        start = perf_counter()
        equities = old.equities_for(case,cache)
        equity_seconds += perf_counter()-start
        row = student.solve_record(case,plan['hands'],equities,fitted['models'])
        base.write_json(output/(case['id']+'.json'),row)
    base.write_json(output/'preparation.json',dict(equity_seconds=equity_seconds))
    verify_bindings(plan)


def checked_seconds(record, keys):
    require(all(type(record[k]) in (int,float) and base.np.isfinite(record[k]) and
                record[k] >= 0 for k in keys), 'invalid time record')


def execute_plan(path, expected):
    raw,plan = read_plan(path,expected)
    output = Path(plan['output_directory'])
    output.mkdir(parents=True,exist_ok=False)
    start = perf_counter()
    try:
        with (output/'plan.json').open('xb') as stream:
            stream.write(raw)
        command = [sys.executable,'-B',str(ROOT/'tools/river_witness_distillation.py'),
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
                                                  seconds=perf_counter()-start))
        require(child.returncode == 0, 'distillation worker failed')
        fitted = base.read(output/'models.json')
        require(type(fitted) is dict and set(fitted) == {
            'models','training_cases','validation_seconds','fit_seconds'}, 'invalid fitted record')
        checked_seconds(fitted,('validation_seconds','fit_seconds'))
        reconstructed = fitted_record(plan)
        for key in ('models','training_cases'):
            require(pilot.canonical_json(fitted[key]) == pilot.canonical_json(reconstructed[key]),
                    'fitted model reconstruction mismatch')
        preparation = base.read(output/'preparation.json')
        require(set(preparation) == {'equity_seconds'}, 'invalid preparation record')
        checked_seconds(preparation,('equity_seconds',))
        rows,cache = [],{}
        for case in plan['cases']:
            row = base.read(output/(case['id']+'.json'))
            rows.append(student.verify_record(case,plan['hands'],old.equities_for(case,cache),
                                               reconstructed['models'],row))
        verify_bindings(plan)
        summary = student.summarize(plan['cases'],rows)
        summary['training'] = fitted
        summary['equity_preparation_seconds'] = preparation['equity_seconds']
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
