"""Describe the completed confirmation without adding solver runs."""
from pathlib import Path
import json
import hashlib

HERE = Path(__file__).resolve().parent
PRIOR = HERE.parent/'river-cfr-comparison-001'


def read(p):
    return json.loads(p.read_text(encoding='utf-8'))


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


new, old = read(HERE/'assessment.json'), read(PRIOR/'assessment.json')
plan, previous_plan = read(HERE/'plan.json'), read(PRIOR/'plan.json')
for name in ('solver.py', 'test_solver.py', 'launch.py'):
    assert digest(HERE/name) == digest(PRIOR/name), name
for field in ('arms','repeats','iterations','checkpoints','case_timeout_seconds',
              'private_limit_mib','numpy','order','average','units','quality'):
    assert plan[field] == previous_plan[field], field
original = (PRIOR/'experiment.py').read_text(encoding='utf-8')
expected = original.replace('input-001.json','input-000.json').replace(
    'run/001-baseline.json','run/000-baseline.json').replace(
    "name='river-cfr-comparison-001'","name='river-cfr-comparison-002'").replace(
    'case=1, variant=','case=0, variant=').replace(
    "User: Let\\'s run the comparisons", "User: Ok let\\'s run the next")
assert expected == (HERE/'experiment.py').read_text(encoding='utf-8')
record = read(HERE/'input.json')
prior_record = read(PRIOR/'input.json')
assert record['board'] != prior_record['board']
game = read(HERE/'game.json')
root = game['nodes'][0]
labels = ['CFR+, matched averaging','DCFR+, paper definition','PDCFR+, matched parameters',
          'CFR+, linear averaging','DCFR+, released-code definition','PDCFR+, published parameters']
table = '\n'.join(f'| {label} | {r["exploitability"]:.6g} | {r["training_median"]:.3f} | '
                  f'{r["worker_peak_mib"]:.1f} | {r["strict_gap_pass"]} |'
                  for label,r in zip(labels,new['rows']))
comparison = '\n'.join(f'| {label} | {a["exploitability"]:.6g} | {b["exploitability"]:.6g} |'
                       for label,a,b in zip(labels,old['rows'],new['rows']))
best = min(new['rows'], key=lambda r:r['exploitability'])
strict = [r['name'] for r in new['rows'] if r['strict_gap_pass']]
headline = (f'Paper DCFR+ has {new["matched_dcfr_improvement"]:.2f}x less error than '
            f'matched CFR+. Matched prediction/DCFR+ error ratio is '
            f'{new["matched_prediction_error_ratio"]:.3f}. Lowest-error arm: {best["name"]}.')
report = f'''# River CFR comparison 002: different-position confirmation

{headline}

## Scope and identity

Retained case 000 was selected as the lowest-index position not used by comparison 001,
before inspecting its CFR outcomes. It is a previously studied case, not an untouched
holdout. Board card IDs: {record['board']}; pot: {record['actual_state']['pot']}.
Both roles retain all 1,081 legal private hands and the original factorized, collision-aware
range model. The baseline tree has {len(root['children'])} distinct root actions;
the shorter stack collapses the opening sizes into one bet. Changing the position changes
board, pot, stack, ranges and effective action menu together; this is not a board-only ablation.

Solver, tests and bootstrap match comparison 001 byte for byte. Driver differences are
limited to identity, authorization, and case/reference selection, verified by whole-file
comparison. All six arms, parameters, averaging rules, alternating update order, 2,048
iterations, checkpoint times in iterations, precision, single-thread settings and limits
are identical. Three fresh-process repeats per arm rotate order. Python 3.14.6 only.
Authorization: "Ok let's run the next". Design was retained before preparation and run.
Plan SHA-256: {digest(HERE/'plan.json')}

## Final results

Exploitability is half the exact best-response interval width in units where pot=10.
Lower is better; divide by 10 for fraction of the starting pot. The strict column asks
whether the full gap meets the existing <=1e-8 threshold, independently of result validity.

| Configuration | Exploitability | Median training s | Worker peak MiB | Strict gap pass |
|---|---:|---:|---:|---|
{table}

Strict passing arms: {', '.join(strict) if strict else 'none'}.
All 18 runs and six independent rational final audits completed. Final policy arrays at
every stored checkpoint are byte-identical across repeats. These repeats establish
determinism and timing variation, not three independent strategic samples. Checkpoint
curves use the floating evaluator; final errors use the retained rational evaluator after
2^48 behavior quantization. All final value/bound checks agree within 1e-10, and each
interval contains the retained LP equilibrium interval. The LP reference was not rerun.

The four existing test methods passed again. The game engine audit checked all terminal
paths for win/tie/loss, {plan['engine_audit']['checks']} checks. These are author-run checks,
not an independent agent review. No algorithm parameters were changed after results.

## What transferred from the first case?

| Configuration | First case 001 error | Confirmation case 000 error |
|---|---:|---:|
{comparison}

Paper DCFR+/matched CFR+ error reduction: first case
{old['matched_dcfr_improvement']:.2f}x; confirmation {new['matched_dcfr_improvement']:.2f}x.
Matched prediction/DCFR+ error ratio: first case
{old['matched_prediction_error_ratio']:.3f}; confirmation
{new['matched_prediction_error_ratio']:.3f}. Below one favors prediction; above one disfavors it.
Interpret ranking within each game; different difficulty makes absolute errors across
games unsuitable as a pooled strength score. Two selected retained cases do not establish
a universal algorithm ranking. Keep both discount definitions and prediction controls in
the evidence; do not turn the initial board's prediction loss into a general prohibition.

## Cost boundaries and next decision

Training excludes array load, checkpoint scoring, serialization, process startup and the
independent rational audit. All corresponding worker-wall, audit-compute, and memory figures
are recorded separately in assessment.json. Shared payoff arrays use
{plan['payoff_bytes']/1024**2:.2f} MiB. Preparation took {plan['preparation_seconds']:.4f} s,
excluding imports, engine audit and freezing. The 180-second/3,072-MiB per-worker limits
never fired; memory was sampled every 50 ms, not enforced as a hard cap.

Next, test iterative quality and capacity on the expanded river trees that stopped inside
HiGHS. The present simpler-tree confirmation cannot establish that capacity result.
GPU-CFR remains queued after the CPU capacity test; neural discounted CFR remains later.
No six-max strength, live decision deadline, or folded-card bunching claim follows.
No commit, push, bot invocation or strategy adoption was performed.
'''
with (HERE/'report.md').open('x', encoding='utf-8', newline='\n') as f:
    f.write(report)
with (HERE/'comparison.json').open('x', encoding='utf-8', newline='\n') as f:
    json.dump(dict(headline=headline, unchanged_solver=True, fixed_config=True,
                   strict_passing_arms=strict, best_arm=best['name'],
                   prior_assessment_sha256=digest(PRIOR/'assessment.json')),
              f, indent=2, sort_keys=True)
    f.write('\n')
print(headline)
print(table)
