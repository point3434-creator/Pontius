"""Retrospective exact-arithmetic diagnosis; no fitting, LPs, or training."""
from pathlib import Path
import importlib.util
import sys
from fractions import Fraction as Q
from time import perf_counter
from collections import Counter
import json

HERE = Path(__file__).resolve().parent
ROOT = Path('D:/Pontius-worktrees/eval-runner-consolidation')
HISTORY = ROOT/'experiments/river-abstraction-study'
CONFIRM = HISTORY/'witness-group-repair-confirmation-001'
NAME = 'witness-repair-regression-diagnostic-001'
spec = importlib.util.spec_from_file_location('frozen_confirmation',
    CONFIRM/'verification-tools/confirmation.py')
c = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = c
spec.loader.exec_module(c)
read, write, digest = c.read, c.write, c.digest


def feasible(groups, probabilities):
    return all(len({p for g, p in zip(groups, probabilities) if g == k}) == 1
               for k in set(groups))


def merge_cost(changes, groups, a, b):
    totals = [sum((d for d, g in zip(changes, groups) if g == k), Q(0)) for k in (a, b)]
    return sum(max(Q(0), t) for t in totals)-max(Q(0), sum(totals))


def lift(coefficients, groups):
    return [Q(float(coefficients[g])) for g in groups]


class Kernel:
    def __init__(self, check, fold, call):
        self.check, self.fold, self.call = check, fold, call
        self.n, self.m = len(check), len(check[0])
        self.row_check = [sum(row, Q(0)) for row in check]

    @classmethod
    def from_matrix(cls, matrix):
        return cls(*[[[Q(float(v)) for v in row] for row in a]
                     for a in (matrix.check, matrix.fold, matrix.call)])

    def advantages(self, opponent, seat):
        if seat == 0:
            return [sum(((1-opponent[j])*self.fold[i][j]+
                         opponent[j]*self.call[i][j] for j in range(self.m)), Q(0))-
                    self.row_check[i] for i in range(self.n)]
        return [sum((opponent[i]*(self.fold[i][j]-self.call[i][j])
                     for i in range(self.n)), Q(0)) for j in range(self.m)]

    def best(self, opponent, groups, seat):
        changes = self.advantages(opponent, seat)
        if seat == 0:
            constant = sum(self.row_check, Q(0))
        else:
            constant = -sum(((1-opponent[i])*self.row_check[i]+
                             opponent[i]*sum(self.fold[i], Q(0))
                             for i in range(self.n)), Q(0))
        return constant+sum((max(Q(0), sum((d for d, g in zip(changes, groups) if g == k),
                                          Q(0))) for k in set(groups)), Q(0))

    def security(self, own, seat):
        if seat == 0:
            return sum(((1-own[i])*self.row_check[i] for i in range(self.n)), Q(0))+sum(
                (min(sum((own[i]*self.fold[i][j] for i in range(self.n)), Q(0)),
                     sum((own[i]*self.call[i][j] for i in range(self.n)), Q(0)))
                for j in range(self.m)), Q(0))
        return -sum((max(self.row_check[i],
                         sum(((1-own[j])*self.fold[i][j]+own[j]*self.call[i][j]
                              for j in range(self.m)), Q(0))) for i in range(self.n)), Q(0))


def own_interval(solution, seat):
    value = solution[f'seat{seat}']['value']
    lo, hi = Q(value['lower_exact']), Q(value['upper_exact'])
    return (lo, hi) if seat == 0 else (-hi, -lo)


def direction(value, tolerance=Q('1e-10')):
    return 'worse' if value > tolerance else 'better' if value < -tolerance else 'equal'


def analyze(row, matrix):
    kernel = Kernel.from_matrix(matrix)
    old_groups, new_groups = row['baseline_groups'], row['proposal']['groups']
    baseline, repaired = row['baseline'], row['solution']
    for groups, solution in ((old_groups, baseline), (new_groups, repaired)):
        c.core.verify(matrix, c.weights(groups), solution)
    old_record, new_record = row['records']['control'][0], row['records']['repaired'][1]
    security = [[], []]
    seats = []
    for seat in (0, 1):
        old_witness = list(map(Q, baseline[f'seat{seat}']['coefficients'][1-seat]))
        new_witness = list(map(Q, repaired[f'seat{seat}']['coefficients'][1-seat]))
        old_values, new_values = own_interval(baseline, seat), own_interval(repaired, seat)
        old_best = kernel.best(old_witness, old_groups[seat], seat)
        new_fixed = kernel.best(old_witness, new_groups[seat], seat)
        new_best = kernel.best(new_witness, new_groups[seat], seat)
        assert old_best == old_values[1] and new_best == new_values[1]
        old_changes = kernel.advantages(old_witness, seat)
        new_changes = kernel.advantages(new_witness, seat)
        proposal = row['proposal']['seats'][seat]
        assert list(map(str, old_changes)) == proposal['weighted_advantages_exact']
        gain = Q(proposal['net_witness_gain_exact'])
        assert new_fixed-old_best == gain
        adaptation = new_fixed-new_best
        assert adaptation >= -c.opt.TOLERANCE
        assert new_best-old_best == gain-adaptation
        optimum = lift(baseline[f'seat{seat}']['coefficients'][seat], old_groups[seat])
        structural = feasible(new_groups[seat], optimum)
        for method, groups, record in [(0, old_groups, old_record),
                                      (1, new_groups, new_record)]:
            own = lift(record['coefficients'][seat], groups[seat])
            security[method].append(kernel.security(own, seat))
        move = proposal['operation']
        details = None
        if move:
            split, (a, b) = move['split'], move['merge']
            plus = sum((d for i, d in enumerate(new_changes)
                        if old_groups[seat][i] == split and old_changes[i] > 0), Q(0))
            minus = sum((d for i, d in enumerate(new_changes)
                         if old_groups[seat][i] == split and old_changes[i] <= 0), Q(0))
            split_gain = max(Q(0), plus)+max(Q(0), minus)-max(Q(0), plus+minus)
            cost = merge_cost(new_changes, old_groups[seat], a, b)
            new_net = kernel.best(new_witness, new_groups[seat], seat)-kernel.best(
                new_witness, old_groups[seat], seat)
            assert new_net == split_gain-cost
            assert merge_cost(old_changes, old_groups[seat], a, b) == Q(
                proposal['merge_cost_exact'])
            coefficients = baseline[f'seat{seat}']['coefficients'][seat]
            details = dict(operation=move,
                old_merge_cost=proposal['merge_cost_exact'],
                new_merge_cost=str(cost), new_split_gain=str(split_gain),
                new_witness_net=str(new_net),
                old_optimum_merge_action_gap=str(abs(Q(coefficients[a])-Q(coefficients[b]))))
        value_delta = [new_values[0]-old_values[1], new_values[1]-old_values[0]]
        seats.append(dict(seat=seat, changed=proposal['changed'],
            value_improvement_interval=list(map(str, value_delta)),
            certified_worse=value_delta[1] < -Q('1e-8'),
            fixed_witness_gain=str(gain), adaptation_penalty=str(adaptation),
            old_witness_best=str(old_best), new_witness_best=str(new_best),
            structural_accept=structural,
            floor_accept=value_delta[0] >= 0,
            security_accept=security[1][seat] >= security[0][seat],
            security_improvement=str(security[1][seat]-security[0][seat]),
            witness_probability_changes=sum(a != b for a, b in zip(old_witness, new_witness)),
            merge=details))
        if structural:
            assert value_delta[1] >= -c.opt.TOLERANCE, 'feasible policy lost its guarantee'
    actual = [-sum(v)/2 for v in security]
    assert actual == [Q(r['exact_exploitability']) for r in (old_record, new_record)]
    floor_intervals = [[Q(r['minimum_exploitability'][k]) for k in
                       ('lower_exact', 'upper_exact')] for r in (baseline, repaired)]
    raw_floor_delta = [floor_intervals[1][0]-floor_intervals[0][1],
                       floor_intervals[1][1]-floor_intervals[0][0]]
    gates = {}
    for name in ('structural', 'floor', 'security'):
        accepted = [s[name+'_accept'] and s['changed'] for s in seats]
        groups = [new_groups[s] if accepted[s] else old_groups[s] for s in (0, 1)]
        coefficients = [(new_record if accepted[s] else old_record)['coefficients'][s]
                        for s in (0, 1)]
        low, high = c.core.exact_bounds(matrix, c.weights(groups), coefficients, unrestricted=True)
        composed = -sum(security[int(accepted[s])][s] for s in (0, 1))/2
        assert composed == (high-low)/2, 'mixed-policy composition failed'
        chosen_values = [own_interval(repaired if accepted[s] else baseline, s)
                         for s in (0, 1)]
        floor = [max(Q(0), -sum(v[1] for v in chosen_values)/2),
                 -sum(v[0] for v in chosen_values)/2]
        floor_delta = [floor[0]-floor_intervals[0][1], floor[1]-floor_intervals[0][0]]
        if name == 'security':
            assert composed <= actual[0]
        if name == 'floor':
            assert floor_delta[0] <= 0 and floor_delta[1] <= 2*c.opt.TOLERANCE
        gates[name] = dict(accepted=accepted, actual_exact=str(composed),
            actual_delta_exact=str(composed-actual[0]), floor_interval=list(map(str, floor)),
            floor_delta_interval=list(map(str, floor_delta)))
    return dict(entry=row['entry'], seats=seats, baseline_actual=str(actual[0]),
        repaired_actual=str(actual[1]), raw_actual_delta=str(actual[1]-actual[0]),
        raw_floor_delta_interval=list(map(str, raw_floor_delta)), gates=gates)


def summary(rows):
    result = {}
    for panel in ('pilot', 'confirmation'):
        result[panel] = {}
        for bet in (5, 10):
            rs = [r for r in rows if r['panel'] == panel and r['entry']['bet'] == bet]
            if not rs:
                continue
            mean = lambda field: sum(Q(r[field]) for r in rs)/len(rs)
            baseline, raw = mean('baseline_actual'), mean('repaired_actual')
            all_seats = [s for r in rs for s in r['seats']]
            damaged = [s for s in all_seats if s['certified_worse']]
            info = dict(cases=len(rs), baseline_actual=float(baseline), raw_actual=float(raw),
                raw_directions=dict(Counter(direction(Q(r['raw_actual_delta'])) for r in rs)),
                damaged_seats=len(damaged),
                damaged_seats_with_free_old_merge=sum(s['merge'] is not None and
                    Q(s['merge']['old_merge_cost']) == 0 for s in damaged),
                damaged_seats_with_costly_new_merge=sum(s['merge'] is not None and
                    Q(s['merge']['new_merge_cost']) > 0 for s in damaged),
                damaged_seats_changing_optimum=sum(not s['structural_accept'] for s in damaged),
                changed_seats=sum(s['changed'] for s in all_seats), gates={})
            for gate in ('structural', 'floor', 'security'):
                gs = [r['gates'][gate] for r in rs]
                value = sum(Q(g['actual_exact']) for g in gs)/len(gs)
                info['gates'][gate] = dict(mean_actual=float(value),
                    change_percent=100*float(value/baseline-1),
                    accepted_seats=sum(sum(g['accepted']) for g in gs),
                    actual_directions=dict(Counter(
                        direction(Q(g['actual_delta_exact'])) for g in gs)),
                    floor_regressions=sum(Q(g['floor_delta_interval'][0]) > Q('1e-8') for g in gs))
            result[panel][str(bet)] = info
    return result


def bindings(plan):
    assert plan['name'] == NAME and len(plan['cases']) == 96
    assert sys.version == plan['python'] and c.np.__version__ == plan['numpy']
    assert c.scipy.__version__ == plan['scipy']
    for path, expected in plan['pins'].items():
        assert digest(path) == expected, path


def worker(plan, out):
    bindings(plan)
    def forbidden(*args, **kwargs):
        raise AssertionError('diagnostic forbids fitting, LPs and solver training')
    c.opt.linprog = forbidden
    c.core.RegretBR = forbidden
    rows = []
    for i, item in enumerate(plan['cases']):
        row = read(item['path'])
        start = perf_counter()
        matrix, groups, inputs = c.build_case(row['entry'])
        assert groups == row['baseline_groups'], 'baseline group reconstruction changed'
        if item['panel'] == 'confirmation':
            assert inputs == row['inputs']
        else:
            original = read(row['entry']['original'])
            assert inputs['joint'] == original['inputs']['joint']
            assert inputs['provenance_digest'] == original['provenance_digest']
        result = dict(panel=item['panel'], source_sha256=digest(item['path']),
                      **analyze(row, matrix), analysis_seconds=perf_counter()-start)
        write(out/f'case-{i:03d}.json', result)
        rows.append(result)
        print(f'diagnosed {i+1}/96: {item["panel"]} {row["entry"]["case"]["id"]}', flush=True)
    bindings(plan)
    write(out/'summary.json', summary(rows))
    write(out/'audit.json', dict(passed=True, cases=96, asymmetric_certificates=384,
        composed_profiles=288, exact_witness_decompositions=192, new_lp_calls=0,
        model_fits=0, training_updates=0, independent_cold_review=False))


if __name__ == '__main__':
    plan_path, expected = sys.argv[1:]
    assert digest(plan_path) == expected
    plan = read(plan_path)
    worker(plan, Path(plan['output']))
