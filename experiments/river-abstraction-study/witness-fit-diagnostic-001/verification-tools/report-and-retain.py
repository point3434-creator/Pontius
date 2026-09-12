"""Document and retain completed diagnostic; no model or solver execution."""
from hashlib import sha256
import json
from pathlib import Path
import shutil

ROOT=Path('D:/Pontius-worktrees/eval-runner-consolidation')
HERE=Path(__file__).parent
OUT=Path('D:/Pontius-training/river-abstraction-study/witness-fit-diagnostic-001')
ARCHIVE=ROOT/'experiments/river-abstraction-study/witness-fit-diagnostic-001'
REPORT=ROOT/'docs/research/river-witness-fit-diagnostic-001.md'
read=lambda p:json.loads(p.read_bytes())
digest=lambda p:sha256(p.read_bytes()).hexdigest()
mean=lambda values:sum(values)/len(values)

def write(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as f:
        f.write(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n')

s=read(OUT/'summary.json')
assert read(OUT/'audit.json')['passed'] is True
assert read(OUT/'receipt.json')['exit']==0
plan=read(OUT/'plan.json')
for path,h in plan['pins'].items(): assert digest(Path(path))==h,path
assert not ARCHIVE.exists() and not REPORT.exists()
aggregates={}
for split,panel in s['panels'].items():
    aggregates[split]=[]
    for columns in panel['overall']:
        aggregates[split].append(dict(mse=mean([m['mse'] for m in columns]),
            opportunity_cost=mean([m['opportunity_cost'] for m in columns]),
            correlation_range=[min(m['correlation'] for m in columns),max(m['correlation'] for m in columns)],
            baseline_skill_range=[min(m['skill_vs_training_mean'] for m in columns),
                                  max(m['skill_vs_training_mean'] for m in columns)],
            near_sign_range=[min(m['bands']['near_0_to_0.1']['sign_mismatch_active'] for m in columns),
                             max(m['bands']['near_0_to_0.1']['sign_mismatch_active'] for m in columns)],
            far_sign_range=[min(m['bands']['far_over_0.5']['sign_mismatch_active'] for m in columns),
                            max(m['bands']['far_over_0.5']['sign_mismatch_active'] for m in columns)]))
write(OUT/'analysis.json',aggregates)
lines=['# Frozen-model fit versus transfer: witness-fit-diagnostic-001','',
    'One authorized diagnostic completed 96 observed cases: 48 training and 48 evaluation.',
    'All cases have 96 holdings per seat, three pools and two regimes across eight boards',
    'per split. The saved model, both source milestones and all computational source stayed',
    'unchanged. No refitting, tuning, new boards, grouping score or LP was performed.','',
    '## Finding','',
    'This is not a uniform transfer failure. Seat 0 has higher evaluation prediction error;',
    'seat 1 has similar error already on training data, with slightly lower evaluation MSE.',
    'Both seats preserve broad correlation with the targets on new boards. That did not',
    'preserve strategic grouping quality in witness-distillation-001.','',
    '| Seat | Training MSE | Evaluation MSE | Change |',
    '|---|---:|---:|---:|']
for seat,name in enumerate(('0: bet minus check','1: call minus fold, including bet reach')):
    train=aggregates['training'][seat]['mse']; evaluation=aggregates['evaluation'][seat]['mse']
    lines.append(f'| {name} | {train:.8f} | {evaluation:.8f} | {100*(evaluation/train-1):+.2f}% |')
lines += ['',
    'MSE is equally averaged across the four witness columns, with equal case weights',
    'and normalized own-hand weights within each case. It is in squared game chips.',
    'Panel composition differs; a raw train/evaluation error ratio is not a causal',
    'estimate of overfitting or an all-board generalization statistic.','',
    '| Seat | Split | Correlation across columns | MSE reduction vs training-mean constant |',
    '|---|---|---:|---:|']
for seat in (0,1):
    for split in ('training','evaluation'):
        r=aggregates[split][seat]; c=r['correlation_range']; b=r['baseline_skill_range']
        lines.append(f'| {seat} | {split} | {c[0]:.4f} to {c[1]:.4f} | '
                     f'{100*b[0]:.2f}% to {100*b[1]:.2f}% |')
lines += ['',
    'The constant baseline is each seat/column\'s equal-case training target mean,',
    'computed from retained targets; no saved model is fitted again. For training,',
    'this baseline is the weighted training mean. Evaluation retains the same constant.',
    'A large improvement over this weak baseline is not evidence of useful grouping.','',
    '## Where action-sign errors occur','',
    'A positive predicted advantage chooses bet for seat 0, call for seat 1. Predicted',
    'zero chooses check/fold. Sign rates exclude targets with absolute value <=1e-10',
    'from the conditional denominator. These are per-witness diagnostic responses,',
    'not the actions of the grouped equilibrium policy.','',
    '| Seat | Split | Near: abs(target)<=0.1 | Far: abs(target)>0.5 |',
    '|---|---|---:|---:|']
for seat in (0,1):
    for split in ('training','evaluation'):
        r=aggregates[split][seat]; n=r['near_sign_range']; f=r['far_sign_range']
        lines.append(f'| {seat} | {split} | {100*n[0]:.2f}% to {100*n[1]:.2f}% | '
                     f'{100*f[0]:.2f}% to {100*f[1]:.2f}% |')
lines += ['',
    'Ranges span the four witness columns; they are not uncertainty intervals.',
    'The near band has small individual decision costs, so a high error fraction there',
    'does not by itself establish the cause of the prior grouping-floor regression.',
    'Full band masses, MSE, sign rates and cost, including the middle band, are retained.','',
    '| Seat | Training mean opportunity cost | Evaluation mean opportunity cost |',
    '|---|---:|---:|']
for seat in (0,1):
    lines.append(f"| {seat} | {aggregates['training'][seat]['opportunity_cost']:.8f} | "
                 f"{aggregates['evaluation'][seat]['opportunity_cost']:.8f} |")
lines += ['',
    'Opportunity cost is max(y,0)-y*I(prediction>0), where y is the retained action',
    'advantage against one fixed witness. The table equally averages four separate',
    'witness-response diagnostics; it is not a joint policy value, exploitability,',
    'realized winnings or BB/100. Seat 1 retains the original betting-reach factor.','',
    '## Interpretation and next decision','',
    'More training boards alone are not established as the remedy. The caller-side',
    'residual and near-boundary errors are present in training as well as evaluation.',
    'The bettor side also shows a transfer gap. Neither observation establishes whether',
    'the limiting factor is features, model capacity, regularization or the objective.',
    'No new model is adopted. The current fixed model remains a retained nonimprovement.','',
    'The next useful intervention should test preservation of decision-relevant local',
    'structure, not reward global MSE alone. A bounded follow-up can compare grouping',
    'that retains the existing range/equity features while adding predicted witness',
    'information against the current predicted-only grouping, at the same group budget.',
    'Its strategic floor must be measured; these diagnostics do not guarantee benefit.',
    'This is a recommendation, not authorization for another invocation. These boards',
    'are observed and any tuning on them requires fresh evidence for generalization.','',
    '## Verification and provenance','',
    'Analytic checks preceded execution: weights, signs, zero predictions, ties, band',
    'boundaries, empty conditional bands and invalid weights. All checks passed.',
    'Fitting and optimizer entry points were replaced with refusal guards during the',
    'diagnostic. Every reconstructed input matched retained inputs, and every evaluation',
    'prediction reproduced the saved prediction exactly. All 157 pinned files matched',
    'before and after execution, including both complete source milestones.','',
    'A separate stdlib scalar audit recomputed all 4,928 reported metric values from',
    'the retained hand arrays with no production metric import, new fit, LP or prediction.',
    'Its initial ordering assertion failed because lexical filenames place polarized',
    'before uniform while the plan orders uniform first. The scratch audit was corrected',
    'to follow plan order; the diagnostic was not rerun and no result changed. The incident',
    'is retained in verification-tools/audit-initial-failure.txt.','',
    f"Worker process time: {read(OUT/'receipt.json')['worker_process_seconds']:.6f} seconds;",
    '300-second timeout. This spans child execution through exit and excludes parent',
    'preflight and the later scalar audit. Python 3.14.6, NumPy 2.5.2, SciPy 1.18.0,',
    'one BLAS thread. No RSS cap or peak-memory measurement. Exit 0.','',
    'This is a post-result diagnostic, not a cold candidate review or a held-out',
    'confirmation. No external reviewer was dispatched for this saved-data analysis.',
    'Existing models, source and previous milestone bytes are preserved. No commit/push.','',
    'Original output: D:/Pontius-training/river-abstraction-study/witness-fit-diagnostic-001',
    'Repository archive: experiments/river-abstraction-study/witness-fit-diagnostic-001','',
    'Plan SHA-256:',digest(OUT/'plan.json'),'']
with REPORT.open('x',encoding='utf-8',newline='\n') as f: f.write('\n'.join(lines))
shutil.copytree(OUT,ARCHIVE)
(ARCHIVE/'verification-tools').mkdir()
for name in ('design.md','diagnose.py','prepare.py','audit.py','audit-initial-failure.txt',
             'report-and-retain.py'):
    shutil.copyfile(HERE/name,ARCHIVE/'verification-tools'/name)
shutil.copyfile(REPORT,ARCHIVE/'report.md')
for p in OUT.iterdir():
    if p.is_file(): assert digest(p)==digest(ARCHIVE/p.name)
members={p.relative_to(ARCHIVE).as_posix():digest(p) for p in sorted(ARCHIVE.rglob('*')) if p.is_file()}
write(ARCHIVE/'milestone-manifest.json',members)
for name,h in members.items(): assert digest(ARCHIVE/name)==h,name
prior={}
for name in ('development-001','holdout-001','group-optimality-001','witness-groups-development-001',
             'witness-pilot-001','witness-distillation-001'):
    directory=ROOT/'experiments/river-abstraction-study'/name
    for member,h in read(directory/'milestone-manifest.json').items():
        assert digest(directory/member)==h,(name,member)
    prior[name]=digest(directory/'milestone-manifest.json')
overview=ROOT/'docs/research/README.md'
before=overview.read_bytes()
with (HERE/'research-readme-before.md').open('xb') as f: f.write(before)
with overview.open('ab') as f:
    f.write(b'\n## Frozen-model fit and transfer diagnostic\n\n'
        b'[Witness-fit-diagnostic-001](river-witness-fit-diagnostic-001.md) compares\n'
        b'the saved predictor on both observed panels without refitting or LP calls.\n')
receipt=dict(passed=True,archive_members=len(members),archive_sha256=digest(ARCHIVE/'milestone-manifest.json'),
    report_sha256=digest(REPORT),prior_milestones=prior,new_fits=0,new_lp_calls=0,
    commit_performed=False,push_performed=False)
write(HERE/'retention.json',receipt)
print(json.dumps(aggregates,indent=2))
print(json.dumps(receipt,indent=2))
