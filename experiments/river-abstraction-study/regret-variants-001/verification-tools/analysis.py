"""Predeclared checkpoint comparisons; preserve censoring and reversals."""
from fractions import Fraction as Q
from statistics import median

MODES = ('rm', 'rm_plus', 'discounted')


def crossing(records, epsilon, persistent):
    passed = [Q(r['residual_interval'][1]) <= Q(epsilon) for r in records]
    for i, ok in enumerate(passed):
        if ok and (not persistent or all(passed[i:])):
            r = records[i]
            return dict(iteration=r['iteration'], solver_seconds=r['solver_seconds'],
                median_solver_seconds=median(r['solver_seconds']),
                monitored_seconds=r['solver_seconds'][0]+sum(
                    p['scoring_seconds'] for p in records[:i+1]))
    return None


def summarize(rows):
    result = dict(cases=len(rows), modes={})
    for mode in MODES:
        curves = [r['arms'][mode] for r in rows]
        final = [Q(rs[-1]['residual_interval'][1]) for rs in curves]
        modes = dict(mean_final_residual=float(sum(final, Q(0))/len(final)),
            mean_final_exploitability=sum(rs[-1]['exploitability'] for rs in curves)/len(curves),
            mean_50k_solver_seconds=sum(median(rs[-1]['solver_seconds'])
                                       for rs in curves)/len(curves), crossings={}, curve=[])
        for epsilon in ('0.001', '0.0001'):
            first = [crossing(rs, epsilon, False) for rs in curves]
            stable = [crossing(rs, epsilon, True) for rs in curves]
            modes['crossings'][epsilon] = dict(first=first, persistent=stable,
                first_crossed=sum(v is not None for v in first),
                persistent_crossed=sum(v is not None for v in stable))
        for index in range(len(curves[0])):
            points = [rs[index] for rs in curves]
            modes['curve'].append(dict(iteration=points[0]['iteration'],
                mean_residual=float(sum((Q(p['residual_interval'][1]) for p in points),
                                        Q(0))/len(points)),
                mean_exploitability=sum(p['exploitability'] for p in points)/len(points),
                mean_solver_seconds=sum(median(p['solver_seconds'])
                                        for p in points)/len(points)))
        modes['budgets'] = {}
        for budget in (.1, .5, 1., 2., 4.):
            observed = []
            for rs in curves:
                for rep in range(2):
                    feasible = [r for r in rs if r['solver_seconds'][rep] <= budget]
                    observed.append(None if not feasible else feasible[-1])
            covered = [p for p in observed if p is not None]
            modes['budgets'][str(budget)] = dict(completed=len(covered), planned=len(observed),
                mean_residual=None if len(covered) != len(observed) else float(sum(
                    (Q(p['residual_interval'][1]) for p in covered), Q(0))/len(covered)))
        result['modes'][mode] = modes
    result['decisions'] = {}
    control = result['modes']['rm']['crossings']['0.001']['persistent']
    for mode in MODES[1:]:
        candidate = result['modes'][mode]['crossings']['0.001']['persistent']
        ratios = [a['median_solver_seconds']/b['median_solver_seconds']
                  for a, b in zip(candidate, control) if a is not None and b is not None]
        improved = sum(a['median_solver_seconds'] < b['median_solver_seconds']
                       for a, b in zip(candidate, control) if a is not None and b is not None)
        delta = sum((Q(r['arms'][mode][-1]['residual_interval'][1])-
                     Q(r['arms']['rm'][-1]['residual_interval'][1]) for r in rows), Q(0))
        result['decisions'][mode] = dict(paired_crossings=len(ratios),
            faster_cases=improved, median_paired_time_ratio=median(ratios) if ratios else None,
            mean_final_residual_nonworse=delta <= 0,
            earns_confirmation=(len(ratios) == len(rows) and improved >= 12 and
                                median(ratios) < 1 and delta <= 0))
    return result
