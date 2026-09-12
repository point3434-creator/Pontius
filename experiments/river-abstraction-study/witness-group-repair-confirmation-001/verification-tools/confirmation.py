"""Fresh-board adapter; frozen repair, evaluation and solver kernels are reused."""
import os
import sys
import importlib.util
from pathlib import Path
from hashlib import sha256
from fractions import Fraction as Q
from functools import lru_cache
from time import perf_counter
import json
import subprocess
import tracemalloc

HERE = Path(__file__).resolve().parent
ROOT = Path('D:/Pontius-worktrees/eval-runner-consolidation')
HISTORY = ROOT/'experiments/river-abstraction-study'
PREVIOUS = HISTORY/'witness-group-repair-001'
NAME = 'witness-group-repair-confirmation-001'
MODEL = HISTORY/'witness-preference-confirmation-001/candidate.json'
SEED = NAME


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    return result


environment = module('environment', PREVIOUS/'verification-tools/environment.py')
repair = module('repair', PREVIOUS/'verification-tools/repair.py')
frozen = module('frozen_repair_helpers', PREVIOUS/'verification-tools/experiment.py')
from environment import np, scipy, opt, core, PayoffGame, RiverHoldem
from pontius.river_abstraction_study import (
    DEVELOPMENT_BOARDS, HOLDOUT_BOARDS, uniform_equities, anchored_clusters)
from pontius.river_witness_distillation import raw_features, design
from pontius.river_witness_pilot import canonical_board, texture, TEXTURES, hand_pool, case_grid
from scipy.special import expit

read, write, digest = frozen.read, frozen.write, frozen.digest
weights, train, score = frozen.weights, frozen.train, frozen.score


def board_values(value):
    """Collect literal five-card boards from the bounded historical plan inventory."""
    if isinstance(value, list):
        if len(value) == 5 and all(type(v) is int and 0 <= v < 52 for v in value):
            return [value] if len(set(value)) == 5 else []
        return [b for child in value for b in board_values(child)]
    if isinstance(value, dict):
        return [b for child in value.values() for b in board_values(child)]
    return []


def historical_boards():
    excluded = {canonical_board(b) for b in (*DEVELOPMENT_BOARDS, *HOLDOUT_BOARDS)}
    sources = {}
    for path in sorted(HISTORY.glob('*/plan.json')):
        seal = read(path.parent/'milestone-manifest.json')
        opt.require(digest(path) == seal['plan.json'], 'historical plan changed')
        sources[str(path)] = digest(path)
        excluded.update(map(canonical_board, board_values(read(path))))
    return sorted(excluded), sources


def select_boards(excluded, per_texture=4):
    used = {canonical_board(b) for b in excluded}
    selected = {name: [] for name in TEXTURES}
    receipt = []
    for attempt in range(10000):
        def order(card):
            return sha256(f'{SEED}|board|{attempt}|{card}'.encode()).digest(), card
        board = sorted(sorted(range(52), key=order)[:5])
        key, name = canonical_board(board), texture(board)
        if key not in used and len(selected[name]) < per_texture:
            selected[name].append(board)
            receipt.append(dict(attempt=attempt, board=board, texture=name))
            used.add(key)
        if all(len(v) == per_texture for v in selected.values()):
            return [b for name in TEXTURES for b in selected[name]], receipt
    raise ValueError('declared board-selection budget exhausted')


def entries_for(boards):
    return [dict(case=case, bet=bet) for case in case_grid(boards)
            if case['pool'] == 0 for bet in (5, 10)]


@lru_cache(maxsize=1)
def equities_for(board):
    return uniform_equities(board)


def build_case(entry):
    case = entry['case']
    equities = equities_for(tuple(case['board']))
    ranges = [{h: 4 if case['regime'] == 'polarized' and
               (equities[h] <= .2 or equities[h] >= .8) else 1
               for h in hand_pool(case['board'], 0, seat, 96)} for seat in (0, 1)]
    game = RiverHoldem.from_independent_ranges(board=case['board'], pot=10,
        stacks=(20, 20), bet_size=entry['bet'],
        player0_weights=ranges[0], player1_weights=ranges[1])
    matrix = PayoffGame.from_river(game)
    opt.require(matrix.joint.shape == (96, 96), 'unexpected game dimensions')
    features = [design(raw_features(matrix, equities, seat)) for seat in (0, 1)]
    models = read(MODEL)['models']
    predicted = [np.column_stack([
        np.full(len(x), head['constant']) if head['constant'] is not None
        else expit(x @ np.asarray(head['coefficients'])) for head in model])
        for x, model in zip(features, models, strict=True)]
    groups = [anchored_clusters(p, matrix.joint.sum(axis=1-seat), 16).tolist()
              for seat, p in enumerate(predicted)]
    opt.require(all(len(set(g)) == 16 for g in groups), 'capacity changed')
    inputs = dict(provenance_digest=game.provenance_digest,
        hands=[[list(h) for h in hs] for hs in matrix.hands], joint=matrix.joint.tolist(),
        ranges=[[[list(h), w] for h, w in sorted(r.items())] for r in ranges],
        features=[x.tolist() for x in features], predicted=[p.tolist() for p in predicted])
    return matrix, groups, inputs


def bindings(plan):
    opt.require(plan['schema'] == NAME and not tracemalloc.is_tracing(), 'wrong execution mode')
    opt.require(plan['python'] == sys.version and plan['numpy'] == np.__version__ and
                plan['scipy'] == scipy.__version__, 'environment changed')
    for path, expected in plan['pins'].items():
        opt.require(digest(path) == expected, 'binding changed: '+path)
    boards, receipt = select_boards(plan['excluded_boards'])
    opt.require(plan['boards'] == boards and plan['selection_receipt'] == receipt and
                plan['entries'] == entries_for(boards), 'selection or population changed')
    opt.require(len(boards) == 16 and len(plan['entries']) == 64 and
                plan['control_checkpoints'] == [10000, 50000] and
                plan['repaired_checkpoints'] == [1000, 10000] and
                plan['phase_timeout_seconds'] == 900, 'frozen budget changed')


def worker(plan, out):
    bindings(plan)
    for i, entry in enumerate(plan['entries']):
        start = perf_counter()
        matrix, groups, inputs = build_case(entry)
        preparation = perf_counter()-start
        start = perf_counter()
        baseline = core.solve(matrix, weights(groups))
        baseline_seconds = perf_counter()-start
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
        write(out/f'case-{i:03d}.json', dict(entry=entry, baseline_groups=groups,
            inputs=inputs, baseline=baseline, proposal=proposal, solution=solution,
            records=records, preparation_seconds=preparation, baseline_lp_seconds=baseline_seconds,
            proposal_seconds=proposing, lp_seconds=solving))
        print(f'completed {i+1}/64: {entry["case"]["id"]} bet {entry["bet"]}', flush=True)
    bindings(plan)
    write(out/'worker-complete.json', dict(complete=True, cases=64, new_lp_calls=256,
                                        trajectories=128, fitting_tasks=0))


def verify(plan, out):
    bindings(plan)
    saved = opt.linprog
    def forbidden(*args, **kwargs):
        raise AssertionError('verifier LP forbidden')
    opt.linprog = forbidden
    rows, replayed, profiles, examined = [], 0, 0, 0
    try:
        for i, entry in enumerate(plan['entries']):
            matrix, groups, inputs = build_case(entry)
            row = read(out/f'case-{i:03d}.json')
            opt.require(row['entry'] == entry and row['baseline_groups'] == groups and
                        row['inputs'] == inputs, 'input reconstruction mismatch')
            baseline = row['baseline']
            core.verify(matrix, weights(groups), baseline)
            proposal = repair.propose(matrix, groups, baseline)
            opt.require(row['proposal'] == proposal, 'proposal mismatch')
            for seat in (0, 1):
                changes = [Q(v) for v in proposal['seats'][seat]['weighted_advantages_exact']]
                independent = frozen.independent_exchange(groups[seat], changes)
                opt.require(all(proposal['seats'][seat][k] == v
                                for k, v in independent.items()), 'exchange mismatch')
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
            rows.append(row)
            print(f'verified {i+1}/64', flush=True)
        opt.require(read(out/'worker-complete.json') == dict(complete=True, cases=64,
                    new_lp_calls=256, trajectories=128, fitting_tasks=0), 'worker census mismatch')
        bindings(plan)
        write(out/'summary.json', frozen.summarize(rows))
        write(out/'audit.json', dict(passed=True, certificates=256, profiles=profiles,
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
                       str(HERE/'confirmation.py'), mode, str(path), expected]
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
