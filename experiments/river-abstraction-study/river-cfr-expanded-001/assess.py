"""Assess exact quality, measured capacity and all repeats; no new solver runs."""
from pathlib import Path
from fractions import Fraction as Q
from statistics import median
import json
import hashlib
import csv

HERE = Path(__file__).resolve().parent


def read(p):
    return json.loads(p.read_text(encoding='utf-8'))


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


rows, curves, intersections = [], [], {}
for variant in ('checkback','raise'):
    cell = HERE/variant
    plan = read(cell/'plan.json')
    receipt = read(cell/'run/receipt.json')
    assert receipt['complete'] and (receipt['workers'],receipt['certificates']) == (12,4)
    assert receipt['plan_sha256'] == digest(cell/'plan.json')
    for name, expected in plan['pins'].items():
        assert digest(Path(name)) == expected, name
    lows, highs = [], []
    for arm in plan['arms']:
        name = arm['name']
        reps = [read(cell/'run'/f'{r}-{name}.json') for r in range(3)]
        processes = [read(cell/'run'/f'{r}-{name}-receipt.json') for r in range(3)]
        audit = read(cell/'run'/f'0-{name}-certificate.json')
        audit_process = read(cell/'run'/f'0-{name}-verify-receipt.json')
        assert audit['float_agreement'] and audit['retained_tree_identity']
        assert len({r['policy_sha256'] for r in reps}) == 1
        assert all(p['exit'] == 0 and p['stop_reason'] is None
                   for p in processes+[audit_process])
        cert = audit['certificate']
        lows.append(Q(cert['lower']))
        highs.append(Q(cert['upper']))
        rows.append(dict(variant=variant, arm=name, exploitability=float(Q(cert['gap'])/2),
                         gap=float(Q(cert['gap'])), strict_pass=cert['strict_pass'],
                         training_seconds=median(r['checkpoints'][-1]['training_seconds']
                                                 for r in reps),
                         worker_wall_seconds=median(p['seconds'] for p in processes),
                         worker_peak_mib=max(p['os_peak_commit_bytes'] for p in processes)/1024**2,
                         audit_seconds=audit['certificate_seconds'],
                         audit_wall_seconds=audit_process['seconds'],
                         audit_peak_mib=audit_process['os_peak_commit_bytes']/1024**2,
                         policy_sha256=reps[0]['policy_sha256']))
        for checkpoint in reps[0]['checkpoints']:
            curves.append(dict(variant=variant, arm=name, **checkpoint))
    assert max(lows) <= min(highs), 'independent equilibrium intervals disagree'
    intersections[variant] = dict(lower=str(max(lows)), upper=str(min(highs)),
                                  width=float(min(highs)-max(lows)))
result = dict(complete=True, training_workers=24, audit_workers=8, rows=rows,
              equilibrium_interval_intersections=intersections,
              strict_passes=sum(r['strict_pass'] for r in rows),
              all_repeats_policy_identical=True, solver_unchanged=True,
              decision='Capacity demonstrated for approximate solutions on both fixed trees; '
                       'GPU-CFR execution assessment may follow, with full-cost and quality checks')
with (HERE/'assessment.json').open('x', encoding='utf-8', newline='\n') as f:
    json.dump(result, f, indent=2, sort_keys=True)
    f.write('\n')
with (HERE/'curves.csv').open('x', encoding='utf-8', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=list(curves[0]))
    writer.writeheader()
    writer.writerows(curves)
labels = dict(cfr_g4='CFR+, matched averaging', dcfr_paper='DCFR+, paper definition',
              pdcfr_matched='PDCFR+, matched parameters', dcfr_code='DCFR+, code definition')
table = '\n'.join(f'| {r["variant"]} | {labels[r["arm"]]} | {r["exploitability"]:.6g} | '
                  f'{r["training_seconds"]:.3f} | {r["worker_peak_mib"]:.1f} | '
                  f'{r["audit_seconds"]:.3f} | {r["audit_peak_mib"]:.1f} |' for r in rows)
ratios = []
for variant in ('checkback','raise'):
    arm = {r['arm']:r for r in rows if r['variant']==variant}
    ratios.append(f'- {variant}: paper DCFR+ vs matched CFR+ error reduction '
                  f'{arm["cfr_g4"]["exploitability"]/arm["dcfr_paper"]["exploitability"]:.3f}x; '
                  f'matched prediction/DCFR+ error ratio '
                  f'{arm["pdcfr_matched"]["exploitability"]/arm["dcfr_paper"]["exploitability"]:.3f}; '
                  f'lowest error: {min(arm,key=lambda k:arm[k]["exploitability"])}.')
report = f'''# Expanded river CFR 001: capacity and exact residuals

All 24 training runs and eight independent rational audits completed within the original
sampled 3,072 MiB per-worker budget on the two exact trees where the LP stopped on memory.
This demonstrates capacity for independently checked approximate solutions, not a full
NLHE solution or strict equilibrium convergence. Strict gap passes: {result['strict_passes']}/8.

## Game and controls

Same previously observed case 001, pot 29 and effective stack 186, 1,081 private hands
per role, retained factorized collision-aware ranges, and original binary64 payoff units.
The checkback tree allows the second player to bet after a check: 15 public nodes and
nine terminals. The raise tree additionally permits the specified all-in response:
27 public nodes and 17 terminals. Both match the frozen expansion plan member for member;
all engine terminal paths were checked with win/tie/loss outcomes (27 and 51 checks).
No board, range, action, card removal, or payoff simplification was introduced.

Four fixed arms from the prior studies, each with three fresh-process repeats, 2,048
alternating iterations and checkpoints at 16, 64, 256, 1,024 and 2,048. Same float64 CPU
solver, bootstrap and test bytes; Python 3.14.6, NumPy 2.5.2, one numerical thread.
All arms use gamma=4. Discounted arms use alpha=1.5; paper and predictive arms have
denominator +1, while released-code DCFR+ has +1.5. No parameter tuning. The two unmatched
averaging controls were omitted in advance to bound this capacity test. A copied plan
description still says last three controls; preflight.json records the clarification.
The structured four-arm arrays, design and actual receipts agree. No extra arms ran.

## Results at the fixed iteration budget

Exploitability is half the exact best-response interval width; smaller is better.
Units set the starting pot to 10, so divide by 10 for a fraction of pot.

| Tree | Configuration | Exploitability | Median training s | Worker peak MiB | Exact audit s | Audit peak MiB |
|---|---|---:|---:|---:|---:|---:|
{table}

{chr(10).join(ratios)}

Ratios below one in the prediction comparison favor prediction; above one disfavor it.
Compare algorithms within each game. Expanding the game changes the equilibrium and
available deviations, so cross-tree absolute errors or profile values are not strength
improvements. The exact certificates bound residuals in each complete declared tree.

## Verification and timing boundaries

The existing four-method test suite passed before freezing. The prior solver, test and
bootstrap files match by hash. The retained independent rational evaluator checks every
final profile after behavior quantization onto the 2^48 grid. Float value and bound results
agree within 1e-10. The four equilibrium-bound intervals intersect within each game.
No completed full-range LP reference exists for these expanded cases, and no smaller-game
reference was substituted. There were zero LP invocations in this experiment.

Policy arrays at all five checkpoints match byte for byte across three repeats of each
arm. Repeats measure determinism and timing variability, not independent boards or match
samples. Intermediate curves use floating evaluation; final residuals are rationally
verified. The sample is one retained position under two nested action menus.

Training excludes imports, input loading, checkpoint evaluation, serialization and the
separate exact audit. Worker-wall and audit-wall receipts include their process startup;
assessment.json reports both. Shared payoff arrays use 44.58 MiB and 89.15 MiB, respectively.
Prior LP memory stops and current CFR memory are whole-worker measurements with their
respective implementations, not a controlled memory-only substitution inside one solver.
Every worker had a 180-second timeout and 50 ms sampled memory stop, not a hard cap.
No resource limit or observer failure occurred. Retained stop receipts remain unchanged.

## What this enables next

The iterative payoff-product route now has useful capacity evidence on both formerly
blocked trees. Carry the measured quality curves into the queued GPU-CFR assessment.
First establish whether execution overhead or matrix products dominate; retain setup,
memory, quality and repeat-solve boundaries. A GPU port is not yet justified by its paper's
speedup headline, and no neural approximation was needed for these two cases.
Later neural discounted CFR remains deferred. This run does not establish exact bunching,
six-max strength, arbitrary betting-tree coverage or complete live decision latency.

## Retention and authority

User authorization: "Let's test it". Source and configuration pins are in each cell's
plan.json; root preflight.json binds the two plan digests. Every run and audit is retained.
No automatic retries, commits, pushes, bot invocations or policy adoptions were performed.
This is an author-run experiment with an independent evaluator, not a cold agent review.
'''
with (HERE/'report.md').open('x',encoding='utf-8',newline='\n') as f:
    f.write(report)
print(table)
print('\n'.join(ratios))
