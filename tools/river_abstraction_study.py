"""Single-case development driver. The multi-case retained campaign is a later gate."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import sys
from time import perf_counter
import tracemalloc

# Keep these small matrix measurements on one BLAS thread, before importing NumPy.
for variable in ('OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'OMP_NUM_THREADS'):
    os.environ[variable] = '1'
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

import numpy as np  # noqa: E402 -- BLAS environment and source path must precede imports.

from pontius.river_abstraction_study import (  # noqa: E402
    CFR, DEVELOPMENT_BOARDS, PayoffGame, development_case, representations,
)


def write_json(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n')


def bounded_integer(low, high):
    def parse(text):
        value = int(text)
        if not low <= value <= high:
            raise argparse.ArgumentTypeError(f'must be between {low} and {high}')
        return value
    return parse


def run(args):
    if sys.version_info[:3] != (3, 14, 6):
        raise RuntimeError('this study requires CPython 3.14.6')
    if tracemalloc.is_tracing():
        raise RuntimeError('timing with allocation tracing is forbidden')
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    sources = ['src/pontius/river_abstraction_study.py', 'src/pontius/river.py',
               'src/pontius/game.py', 'src/pontius/__init__.py',
               'tools/river_abstraction_study.py', 'docs/research/river-abstraction-study.md']
    try:
        write_json(output / 'started.json', {
            'kind': 'development-only; not retained campaign or strength evidence',
            'python': sys.version, 'numpy': np.__version__, 'command': sys.argv,
            'source_sha256': {p: sha256((ROOT / p).read_bytes()).hexdigest() for p in sources},
            'board': list(DEVELOPMENT_BOARDS[args.board]), 'hands_per_player': args.hands,
            'regime': args.regime, 'iterations': args.iterations,
        })
        started = perf_counter()
        game, equities, ranges = development_case(
            DEVELOPMENT_BOARDS[args.board], args.hands, args.regime)
        matrix = PayoffGame.from_river(game)
        compilation_seconds = perf_counter() - started
        started = perf_counter()
        methods = representations(matrix, equities)
        grouping_seconds = perf_counter() - started
        inputs = {'board': list(game.board), 'pot': game.pot, 'bet': game.bet_size,
                  'stacks': list(game.stacks), 'provenance_digest': game.provenance_digest,
                  'ranges': [[[list(hand), weight] for hand, weight in sorted(r.items())]
                             for r in ranges],
                  'hands': [[list(h) for h in pool] for pool in matrix.hands],
                  'joint': matrix.joint.tolist(),
                  'uniform_equities': [[equities[h] for h in pool] for pool in matrix.hands],
                  'groups': {name: [g.tolist() for g in groups]
                             for name, groups in methods.items()}}
        write_json(output / 'inputs.json', inputs)
        checkpoints = sorted({min(n, args.iterations) for n in (100, 1000, 10000)})
        records = []
        for name, groups in methods.items():
            started = perf_counter()
            reduced = matrix.aggregate(groups)
            solver = CFR(reduced)
            aggregation_seconds = perf_counter() - started
            training_seconds = 0
            for checkpoint in checkpoints:
                started = perf_counter()
                for _ in range(solver.iteration, checkpoint):
                    solver.step()
                training_seconds += perf_counter() - started
                started = perf_counter()
                x, y = solver.average()
                lifted = (x[groups[0]], y[groups[1]])
                full = matrix.evaluate(*lifted)
                restricted = reduced.evaluate(x, y)
                evaluation_seconds = perf_counter() - started
                arrays = [reduced.joint, reduced.check, reduced.fold, reduced.call,
                          *solver.regrets, *solver.sums, solver.check, solver.fold,
                          solver.difference]
                records.append({
                    'method': name, 'iteration': checkpoint,
                    'occupied_groups': list(reduced.joint.shape),
                    'group_bet': x.tolist(), 'group_call': y.tolist(),
                    'hand_bet': lifted[0].tolist(), 'hand_call': lifted[1].tolist(),
                    'full_game': full, 'restricted_game': restricted,
                    'full_exploitability_fraction_of_pot': full['exploitability'] / game.pot,
                    'training_seconds_cumulative': training_seconds,
                    'aggregation_seconds': aggregation_seconds,
                    'evaluation_seconds': evaluation_seconds,
                    'solver_array_bytes': sum(a.nbytes for a in arrays),
                })
        write_json(output / 'result.json', {
            'complete': True, 'kind': 'development-only',
            'compile_seconds': compilation_seconds, 'all_grouping_seconds': grouping_seconds,
            'accepted_joint_deals': len(game.deals), 'records': records,
            'limits': [
                'Finite-budget reference; bounds are floating-point numerical calculations.',
                'Array bytes exclude Python objects, evaluator storage and temporary arrays.',
                'Times are one observation; no latency or process peak claim.',
                'No claim of six-max strength or generalization to other boards.',
            ],
        })
        members = {p.name: sha256(p.read_bytes()).hexdigest() for p in sorted(output.iterdir())}
        write_json(output / 'manifest.json', members)
        print(json.dumps({'complete': True, 'output': str(output),
                          'accepted_joint_deals': len(game.deals), 'records': len(records)}))
    except BaseException as error:
        write_json(output / 'failed.json', {'complete': False, 'type': type(error).__name__,
                                            'message': str(error)})
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--board', type=int, choices=(0, 1), default=0)
    parser.add_argument('--hands', type=bounded_integer(2, 96), default=16)
    parser.add_argument('--regime', choices=('uniform', 'polarized'), default='uniform')
    parser.add_argument('--iterations', type=bounded_integer(1, 10000), default=100)
    run(parser.parse_args())


if __name__ == '__main__':
    main()
