"""Post-run assessment; no solver invocation or parameter selection."""
from pathlib import Path
from fractions import Fraction
from statistics import median
import hashlib
import json
import subprocess
import sys
import csv

HERE = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, obj):
    with path.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(obj, f, sort_keys=True, indent=2, allow_nan=False)
        f.write('\n')


plan = read(HERE/'plan.json')
receipt = read(HERE/'run/receipt.json')
assert receipt['complete'] and receipt['workers'] == 18 and receipt['certificates'] == 6
assert receipt['plan_sha256'] == digest(HERE/'plan.json')
for path, expected in plan['pins'].items():
    assert digest(Path(path)) == expected, path
cmd = [sys.executable, '-I', '-S', '-B', '-W', 'error::ResourceWarning',
       str(HERE/'launch.py'), 'test_solver.py']
test = subprocess.run(cmd, capture_output=True, timeout=30)
(HERE/'tests-stdout.txt').write_bytes(test.stdout)
(HERE/'tests-stderr.txt').write_bytes(test.stderr)
assert test.returncode == 0
rows, curves = [], []
for arm in plan['arms']:
    name = arm['name']
    reps = [read(HERE/'run'/f'{r}-{name}.json') for r in range(3)]
    cert = read(HERE/'run'/f'0-{name}-certificate.json')
    assert cert['float_agreement'] and cert['retained_reference_overlap']
    assert len({r['policy_sha256'] for r in reps}) == 1
    exact = float(Fraction(cert['certificate']['gap'])/2)
    times = [r['checkpoints'][-1]['training_seconds'] for r in reps]
    process = [read(HERE/'run'/f'{r}-{name}-receipt.json') for r in range(3)]
    rows.append(dict(name=name, exploitability=exact, fraction_of_pot=exact/10,
                training_median=median(times), training_min=min(times), training_max=max(times),
                worker_wall_median=median(p['seconds'] for p in process),
                worker_peak_mib=max(p['os_peak_commit_bytes'] for p in process)/1024**2,
                certificate_seconds=cert['certificate_seconds'],
                certificate_peak_mib=read(HERE/'run'/f'0-{name}-verify-receipt.json')[
                    'os_peak_commit_bytes']/1024**2,
                strict_gap_pass=cert['certificate']['strict_pass']))
    for c in reps[0]['checkpoints']:
        curves.append(dict(arm=name, **c))
with (HERE/'curves.csv').open('x', encoding='utf-8', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=list(curves[0]))
    writer.writeheader()
    writer.writerows(curves)
assessment = dict(complete=True, rows=rows, tests_exit=test.returncode,
                 matched_dcfr_improvement=rows[0]['exploitability']/rows[1]['exploitability'],
                 matched_prediction_error_ratio=rows[2]['exploitability']/rows[1]['exploitability'],
                 code_vs_linear_improvement=rows[3]['exploitability']/rows[4]['exploitability'],
                 source_pins_verified=len(plan['pins']),
                 decision='Confirm DCFR+ on a different retained game and expanded tree next; no adoption')
write(HERE/'assessment.json', assessment)
labels = dict(cfr_g4='CFR+, matched averaging', dcfr_paper='DCFR+, paper denominator +1',
              pdcfr_matched='PDCFR+, matched parameters', cfr_linear='CFR+, linear averaging',
              dcfr_code='DCFR+, released-code denominator +1.5',
              pdcfr_published='PDCFR+, published parameters')
table = '\n'.join(f'| {labels[r["name"]]} | {r["exploitability"]:.6g} | '
                  f'{r["training_median"]:.3f} | {r["worker_peak_mib"]:.1f} | '
                  f'{r["certificate_seconds"]:.3f} |' for r in rows)
record = read(HERE/'input.json')
board = record['board']
pot = record['actual_state']['pot']
report = f'''# River CFR comparison 001

DCFR+ led this fixed-game comparison. Prediction did not beat discounting alone.
This is one observed river position, not a fresh-board confirmation or a bot-strength result.

## Frozen question and design

Compare update rules on retained case 001's baseline river tree: board card IDs {board},
pot {pot}, 1,081 private hands per role, collision-aware retained joint distribution,
half-pot and pot opening bets, fold/call responses, and forced checkback after a check.
No raises, sampled deals, hand abstraction, neural evaluation, GPU execution, or new LP calls.
The state/ranges and frozen binary64 payoff arrays are the same as the retained LP reference.
Reached ranges remain factorized; folded-player card bunching is not introduced here.

Each arm starts uniformly with zero regrets. One iteration updates role 0, then role 1.
Float64 CPU, one numerical thread, Python 3.14.6 and NumPy 2.5.2. Average strategies weight
each information set by its player's own reach. Three fresh-process repeats rotate arm order;
2,048 iterations and five checkpoints per run. The three repeats are timing replications,
not independent boards or random match samples. All policy arrays match byte for byte.

The first three arms use averaging exponent gamma=4. Both discounted arms there use
alpha=1.5 and denominator +1; their only update difference is prediction. The remaining
controls use ordinary linear-averaged CFR+, released DCFR+ (+1.5 denominator), and published
PDCFR+ (alpha=2.3, gamma=5). There is no parameter search on this game.

## Results at 2,048 iterations

Error is exploitability = half the exact best-response interval width, in units where
the starting pot is 10. Divide by 10 for fraction of pot. Smaller is better.

| Configuration | Exploitability | Median training s | Worker peak MiB | Exact audit s |
|---|---:|---:|---:|---:|
{table}

With averaging fixed, paper DCFR+ has {assessment['matched_dcfr_improvement']:.2f}x less
error than CFR+. Adding prediction with the same alpha/gamma increases error
{assessment['matched_prediction_error_ratio']:.2f}x relative to that DCFR+ arm.
Released-code DCFR+ has {assessment['code_vs_linear_improvement']:.2f}x less error than
linear-averaged CFR+; that comparison changes discounting and averaging together.
The two DCFR+ definitions are retained under separate names, without choosing one silently.

Training times exclude input load, checkpoint scoring and the independent rational audit.
Each worker loads the frozen arrays itself. Median complete worker walls, per-arm ranges,
verification memory and all checkpoint curves are in assessment.json and curves.csv.
Initial game/payoff preparation took {plan['preparation_seconds']:.4f} s, excluding imports,
engine audits, serialization and freezing. The shared arrays use
{plan['payoff_bytes']/1024**2:.2f} MiB. This is not complete live decision latency.
Memory limits were sampled at 50 ms and were not hard caps. No worker hit a stop.

## Verification and interpretation

Four test methods passed, covering hand-derived discount/prediction updates, uniform
fallback, a convergent perfect-information toy game, literal hidden-hand profile values,
exhaustive pure best responses, and exclusion of own reach from regret. The frozen engine
audit checked every terminal with a win, loss and tie: 15 checks. The independent retained
rational evaluator recomputed all six final profile values and best-response intervals
after quantization onto the 2^48 behavior grid. Every float result agrees within 1e-10,
and every response interval contains the retained LP equilibrium interval.

These certificates validate the reported residuals. NONE passes the older strict
gap <= 1e-8 equilibrium threshold; the LP reference remains more accurate. Intermediate
curve points use the new floating evaluator, while final errors use exact rational checks.
No comparison here demonstrates a memory advantage on the two expanded trees that stopped
inside HiGHS. That remains the next useful test after checking transfer to another case.

## Formula provenance

- Paper Table 1: https://arxiv.org/html/2404.13891v2
- Released DCFR+ implementation:
  https://github.com/rpSebastian/PDCFRPlus/blob/main/pdcfrplus/cfr/dcfr_plus.py
- Released PDCFR+ implementation:
  https://github.com/rpSebastian/PDCFRPlus/blob/main/pdcfrplus/cfr/pdcfr_plus.py

The paper's DCFR+ denominator adds 1; the released implementation adds 1.5.
PDCFR+ discounts the accumulator, clips it, then uses a separately discounted accumulator
plus the latest instantaneous regret to predict the next policy. Accumulation excludes
that prediction term. The source-derived label documents what was tested; it is not a
claim to reproduce the paper's entire benchmark protocol or its plotted results.

## Retention

Plan SHA-256: {digest(HERE/'plan.json')}
The user authorized this comparison with "Let's run the comparisons". No commit, push,
policy adoption, large training or retained bot invocation was performed. New research
files are isolated; prior source and experiment bytes remain unchanged. This report was
written after the run. There was no independent agent review of this new harness.
'''
with (HERE/'report.md').open('x', encoding='utf-8', newline='\n') as f:
    f.write(report)
print(json.dumps(assessment, indent=2))
