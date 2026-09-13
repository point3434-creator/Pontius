"""Replay retained LP vectors against reconstructed constraints; never optimize."""
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace

ROOT = Path('D:/Pontius-worktrees/eval-runner-consolidation')
OLD = ROOT/'experiments/river-abstraction-study/full-combo-direct-002'
spec = importlib.util.spec_from_file_location('numerical_direct', OLD/'verification-tools/direct.py')
d = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = d
spec.loader.exec_module(d)
np = d.np

def run(j):
    record = d.read(d.b.PRIOR/f'input-{j:03d}.json')
    game, groups, meta = d.build(record)
    previous = d.read(OLD/f'case-{j:03d}.json')
    assert meta == previous['inputs']
    kernel = d.Kernel(game)
    d.m.bounds = kernel.bounds
    calls = []
    def replay(c, **kw):
        old = previous['full']['calls'][len(calls)]
        x = np.array(old['x'])
        slack = kw['b_ub']-kw['A_ub'] @ x
        eq = 0 if 'A_eq' not in kw else float(np.max(np.abs(kw['A_eq'] @ x-kw['b_eq'])))
        violations = np.maximum(-slack, 0)
        ignored = (np.abs(kw['A_ub']) <= 1e-9) & (kw['A_ub'] != 0)
        dropped = np.where(ignored, kw['A_ub'], 0)
        dropped_slack = slack + dropped @ x
        bounds = kw['bounds']
        policy = np.array([b == (0,1) for b in bounds])
        row = dict(options=old['options'], objective=float(c @ x),
            max_inequality_violation=float(violations.max()),
            sum_inequality_violation=float(violations.sum()),
            violated_constraints=int((violations > 0).sum()),
            max_equality_violation=eq,
            max_policy_bound_violation=float(max(0, -x[policy].min(), x[policy].max()-1)),
            policy_variables=int(policy.sum()), constraints=len(slack),
            max_abs_policy_coefficient=float(np.abs(kw['A_ub'][:,policy]).max()))
        nonzero = np.abs(kw['A_ub'][kw['A_ub'] != 0])
        row.update(coefficients_at_or_below_solver_cutoff=int(ignored.sum()),
            smallest_nonzero_coefficient=float(nonzero.min()),
            max_inequality_violation_after_cutoff=float(max(0, -dropped_slack.min())))
        calls.append(row)
        return SimpleNamespace(success=True, x=x, nit=old['iterations'])
    d.c.opt.linprog = replay
    failure = None
    try:
        d.m.pair(game, [list(range(1081))]*2)
    except AssertionError as error:
        failure = str(error)
    assert len(calls) == 2
    old_bounds = d.read(OLD/'full-profile-audit.json')['profiles'][j]['full_profile']['bounds']
    low, high = map(d.Q, old_bounds)
    return dict(case=j, new_lp_calls=0, calls=calls, strict_failure=failure,
        exact_gap=str(high-low), gap_float=float(high-low),
        raw_objective_gap=calls[1]['objective']+calls[0]['objective'],
        lower_epigraph_overclaim=-calls[0]['objective']-float(low),
        upper_epigraph_underclaim=float(high)-calls[1]['objective'])

if __name__ == '__main__':
    assert sys.version_info[:3] == (3,14,6)
    output = Path(sys.argv[1])
    output.mkdir(exist_ok=False)
    for j in range(4):
        result = run(j)
        (output/f'case-{j:03d}.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
        print(json.dumps(result), flush=True)
