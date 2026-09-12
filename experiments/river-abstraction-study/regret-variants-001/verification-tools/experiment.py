"""Retained fixed-group solver comparison using the existing bounded coordinator."""
from load_frozen import ROOT, HISTORY, PRIOR, c, m, d
from variants import Trainer, MODES
from pathlib import Path
from fractions import Fraction as Q
from time import perf_counter
import hashlib
import json
import os
import sys
import tracemalloc

HERE = Path(__file__).resolve().parent
NAME = 'regret-variants-001'
CHECKPOINTS = [500, 2000, 10000, 25000, 50000]
read = lambda p: json.loads(Path(p).read_bytes())
digest = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


def write(path, data):
    with Path(path).open('x', encoding='utf-8', newline='\n') as f:
        f.write(json.dumps(data, indent=2, sort_keys=True, allow_nan=False)+'\n')


def bindings(plan):
    assert plan['name'] == NAME and plan['checkpoints'] == CHECKPOINTS
    assert plan['modes'] == list(MODES) and plan['repetitions'] == 2
    assert plan['phase_timeout_seconds'] == 900 and len(plan['sources']) == 16
    assert not tracemalloc.is_tracing()
    assert sys.version == plan['python'] and sys.version_info[:3] == (3, 14, 6)
    assert m.np.__version__ == plan['numpy'] and c.scipy.__version__ == plan['scipy']
    assert all(os.environ.get(k) == '1' for k in
               ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'))
    for path, expected in plan['pins'].items():
        assert digest(path) == expected, path


def build(path):
    row = read(path)
    matrices, groups, inputs = d.build(row['entry'])
    assert groups == row['groups'] and inputs == row['inputs']
    game = d.menu_game(matrices, 'both')
    solution = row['menus']['both']['solution']
    m.verify(game, groups, solution)
    return row, game, groups, solution


def worker(plan, out):
    bindings(plan)
    for i, path in enumerate(plan['sources']):
        old, game, groups, solution = build(path)
        arms = {}
        for rep in range(2):
            order = list(MODES[i % 3:] + MODES[:i % 3])
            if rep:
                order.reverse()
            for mode in order:
                start = perf_counter()
                engine = Trainer(game, groups, mode)
                active = perf_counter()-start
                records = []
                for index, target in enumerate(CHECKPOINTS):
                    start = perf_counter()
                    while engine.iteration < target:
                        engine.step()
                    x, y = engine.average()
                    active += perf_counter()-start
                    if not rep:
                        start = perf_counter()
                        scored = m.score(game, groups, x, y)
                        seconds = perf_counter()-start
                        lower, upper = map(Q, solution['floor'])
                        e = Q(scored['exploitability_exact'])
                        assert e >= lower
                        records.append(dict(iteration=target, x=x, y=y, **scored,
                            residual_interval=list(map(str, (e-upper, e-lower))),
                            scoring_seconds=seconds, solver_seconds=[active]))
                    else:
                        record = arms[mode][index]
                        assert (x, y) == (record['x'], record['y'])
                        record['solver_seconds'].append(active)
                if not rep:
                    arms[mode] = records
                if mode == 'rm':
                    anchor = old['menus']['both']['records'][0]
                    assert (x, y) == (anchor['x'], anchor['y'])
        write(out/f'case-{i:03d}.json', dict(source_path=path, source_sha256=digest(path),
            entry=old['entry'], groups=groups, floor=solution['floor'], arms=arms))
        print(f'completed {i+1}/16', flush=True)
    bindings(plan)
    write(out/'worker-complete.json', dict(complete=True, cases=16, trajectories=96,
        updates=4800000, unique_profiles=240, new_lp_calls=0))


class Reference(m.Trainer):
    """Frozen payoff/update implementation; independent post-update transformation."""
    def __init__(self, game, groups, mode):
        super().__init__(game, groups)
        self.mode = mode
        self.weighted = [m.np.zeros_like(r) for r in self.regrets]

    def step(self):
        played = [m.match(r) for r in self.regrets]
        super().step()
        if self.mode != 'rm':
            for s in (0, 1):
                self.weighted[s] += float(self.iteration**2)*played[s]
                r = self.regrets[s]
                if self.mode == 'rm_plus':
                    r[r < 0] = 0
                else:
                    positive = r > 0
                    factor = self.iteration**1.5
                    r[positive] *= factor/(factor+1)
                    r[~positive] *= .5

    def average(self):
        if self.mode == 'rm':
            return super().average()
        t = self.iteration
        weight = float(t*(t+1)*(2*t+1)//6)
        return ((self.weighted[0]/weight).tolist(),
                (self.weighted[1][:, :, 1]/weight).tolist())


def verify(plan, out):
    bindings(plan)
    def forbidden(*args, **kwargs):
        raise AssertionError('No new LP permitted')
    c.opt.linprog = forbidden
    for i, path in enumerate(plan['sources']):
        old, game, groups, solution = build(path)
        row = read(out/f'case-{i:03d}.json')
        assert row['source_path'] == path and row['source_sha256'] == digest(path)
        assert row['entry'] == old['entry'] and row['groups'] == groups
        assert row['floor'] == solution['floor'] and set(row['arms']) == set(MODES)
        for mode, records in row['arms'].items():
            assert [r['iteration'] for r in records] == CHECKPOINTS
            engine = Reference(game, groups, mode)
            for index, record in enumerate(records):
                while engine.iteration < record['iteration']:
                    engine.step()
                x, y = engine.average()
                assert (x, y) == (record['x'], record['y']), (i, mode, index)
                score = m.score(game, groups, x, y)
                assert all(record[k] == v for k, v in score.items())
                e = Q(score['exploitability_exact'])
                low, high = map(Q, solution['floor'])
                assert record['residual_interval'] == list(map(str, (e-high, e-low)))
                assert e >= low and len(record['solver_seconds']) == 2
                assert all(m.np.isfinite(t) and t > 0 for t in record['solver_seconds'])
                assert m.np.isfinite(record['scoring_seconds']) and record['scoring_seconds'] > 0
                if index:
                    assert all(b > a for a, b in zip(records[index-1]['solver_seconds'],
                                                    record['solver_seconds']))
            if mode == 'rm':
                anchor = old['menus']['both']['records'][0]
                assert (x, y) == (anchor['x'], anchor['y'])
        print(f'verified {i+1}/16', flush=True)
    assert read(out/'worker-complete.json') == dict(complete=True, cases=16,
        trajectories=96, updates=4800000, unique_profiles=240, new_lp_calls=0)
    bindings(plan)
    write(out/'audit.json', dict(passed=True, cases=16, profiles=240, certificates=32,
        independently_transformed_replay_updates=2400000, historical_50k_matches=16,
        repeated_trajectory_identity_checks=48, new_lp_calls=0))


if __name__ == '__main__':
    mode, path, expected = sys.argv[1:]
    assert digest(path) == expected
    if mode == 'run':
        d.runner.HERE, d.runner.bindings = HERE, bindings
        d.runner.run(Path(path), expected)
    else:
        plan = read(path)
        {'worker': worker, 'verify': verify}[mode](plan, Path(plan['output']))
