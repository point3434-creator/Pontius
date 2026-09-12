from hashlib import sha256
import json
from pathlib import Path
import shutil

ROOT = Path('D:/Pontius-worktrees/eval-runner-consolidation')
HERE = Path(__file__).parent
OUT = Path('D:/Pontius-training/river-abstraction-study/witness-clipped-target-001')
ARCHIVE = ROOT/'experiments/river-abstraction-study/witness-clipped-target-001'
REPORT = ROOT/'docs/research/river-witness-clipped-target-001.md'
read = lambda p: json.loads(p.read_bytes())
digest = lambda p: sha256(p.read_bytes()).hexdigest()

def write(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as f:
        f.write(json.dumps(value, sort_keys=True, indent=2, allow_nan=False)+'\n')

a = read(OUT/'analysis.json')
audit = read(OUT/'audit.json')
plan = read(OUT/'plan.json')
assert audit['passed'] is True and read(OUT/'receipt.json')['exit'] == 0
assert not ARCHIVE.exists() and not REPORT.exists()
for path, h in plan['pins'].items():
    assert digest(Path(path)) == h, path

lines = ['# Clipped-target learning: witness-clipped-target-001', '',
    '## Result and decision', '',
    'Training on clipped targets repairs the two preidentified severe failures, but',
    'does not produce a broadly better grouping method. Mean floor falls by 4.52%',
    'against the previous clipped predictor, while 39 of 48 cases and six of eight',
    'board means worsen. Large improvements in a few cases outweigh smaller regressions',
    'elsewhere. The new mean remains 12.74% worse than range-response grouping and',
    '0.84% worse than range-equity grouping. Do not adopt this candidate as an improvement.', '',
    'This is a useful mixed result: changing the target can repair the old tail failures,',
    'but target clipping alone does not close the gap to the existing baseline or the',
    'clipped oracle. Prediction error also changes differently by seat. Neither a lower',
    'average prediction error nor one repaired board establishes stronger general play.', '',
    '## Controlled intervention', '',
    'One authorized invocation trained two quadratic ridge models on the original 48',
    'training cases. The only target change was clipping each exact witness advantage',
    'to [-0.5,+0.5] game chips before fitting. Eleven inputs, the 78-column basis, four',
    'outputs, lambda=.001, unpenalized intercept, equal-case/own-hand weights, clustering',
    'and occupied group capacity were unchanged. New predictions were clipped before',
    'clustering. Oracle values were targets and diagnostics, not candidate inputs.',
    'All 48 previously observed evaluation cases were retained: eight equally weighted',
    'boards, three hand pools and two range regimes, with 96 holdings per seat.',
    'There was no tuning, new board, control re-solve or omitted case. Exactly 96 new',
    'LP calls evaluated the new groups. The parent separately refit both models for',
    'verification; those two additional fits were not a search.', '',
    '## Strategic results', '',
    'Lower is better. Floors are certified numerical intervals for minimum full-hand',
    'exploitability achievable with these groups in the conditional one-bet heads-up',
    'river game. The table gives interval midpoints in game chips, not BB/100 or win rates.', '',
    '| Method | Mean floor |', '|---|---:|']
for method, value in a['mean_floors'].items():
    lines.append(f'| {method} | {value:.10f} |')
lines += ['', 'All deltas are new clipped-target model minus reference. Counts use signed',
    'certificate intervals: lower / higher / overlapping.', '',
    '| Reference | Mean delta | Counts |', '|---|---:|---:|']
for method, c in a['comparisons'].items():
    counts = '/'.join(str(c['counts'].get(k, 0)) for k in ('lower','higher','overlapping'))
    lines.append(f"| {method} | {c['delta']:.10f} | {counts} |")
lines += ['', '## Preidentified failures', '',
    'Both cases are polarized ranges on board 6h 6s Jh Qc Qd. Both remain included.', '',
    '| Case | Old clipped | New clipped-target | Range-response | Clipped oracle |',
    '|---|---:|---:|---:|---:|']
for case, f in a['preidentified_cases'].items():
    lines.append(f"| {case} | {f['clipped_prediction']:.9f} | "
        f"{f['clipped_target_model']:.9f} | {f['range_response']:.9f} | "
        f"{f['clipped_oracle']:.9f} |")
lines += ['', '## Board and regime sensitivity', '',
    '| Board | New clipped-target | Old clipped | Range-response |', '|---|---:|---:|---:|']
for board, b in a['boards'].items():
    f = b['floors']
    lines.append(f"| {board} | {f['clipped_target_model']:.9f} | "
        f"{f['clipped_prediction']:.9f} | {f['range_response']:.9f} |")
lines += ['', 'Removing board 5 or board 7 reverses the mean advantage against the old',
    'clipped predictor. Every leave-one-board-out comparison against range-response',
    'remains unfavorable. These are sensitivity checks, not confidence intervals;',
    'no board is removed from the main result.', '',
    '| Reference | Minimum leave-one-board-out delta | Maximum delta |', '|---|---:|---:|']
for method, values in a['lobo'].items():
    lines.append(f'| {method} | {min(values):.10f} | {max(values):.10f} |')
lines += ['', '| Regime | New clipped-target | Old clipped | Range-response |',
    '|---|---:|---:|---:|']
for regime, r in a['regimes'].items():
    f = r['floors']
    lines.append(f"| {regime} | {f['clipped_target_model']:.9f} | "
        f"{f['clipped_prediction']:.9f} | {f['range_response']:.9f} |")
lines += ['', '## Prediction diagnostics', '',
    'Both models are compared after output clipping against the same clipped exact',
    'targets. These values average the four output columns after the retained case',
    'and own-hand weighting. Full per-column values remain in summary.json.', '',
    '| Split | Seat | Old MSE | New MSE | Old MAE | New MAE |', '|---|---|---:|---:|---:|---:|']
for split, seats in a['prediction_errors'].items():
    for seat, e in enumerate(seats):
        values = [sum(e[m][metric])/4 for metric in ('mse','mae') for m in ('old','new')]
        lines.append(f'| {split} | {seat} | '+' | '.join(f'{v:.8f}' for v in values)+' |')
lines += ['', 'Seat 0 MSE worsens on both training and evaluation data; seat 1 MSE improves.',
    'Seat 1 evaluation MAE nevertheless worsens slightly, so its error improvement is',
    'not uniform across metrics. Fitting clipped targets with a regularized quadratic',
    'model does not guarantee better error after nonlinear output clipping. The fixed',
    'regularizer also has a different relative influence at the changed target scale.',
    'This experiment does not isolate those effects. The independently assembled',
    'normal-equation residual checks passed for both fits.', '',
    '## Verification and execution', '',
    f"Worker: {a['worker_seconds']:.6f} s; worker plus parent: "
    f"{a['worker_plus_parent_seconds']:.6f} s.",
    f"Worker training reconstruction: {a['training_reconstruction_seconds']:.6f} s; "
    f"model fitting: {a['fit_seconds']:.6f} s.",
    'The combined boundary spans launch through parent verification and original',
    'results-manifest writing, excluding preflight, output reservation and final receipt.',
    'Python 3.14.6 / NumPy 2.5.2 / SciPy 1.18.0, one BLAS thread. Worker limit 600 s;',
    'parent outside it. No RSS cap or peak-memory claim. Existing five-second and',
    '10,000-iteration per-LP limits remained. Both stages completed with exit 0.', '',
    'Pre-freeze synthetic checks covered clipping endpoints, interior values, signs,',
    'idempotence, arm separation, invalid inputs and capacity under ties. An analytic',
    'intercept-only example distinguished target clipping from prediction clipping',
    'and checked equal case weight with unequal row counts.',
    'The parent reconstructed training inputs and witness targets, reproduced old',
    'predictions, refit the new models exactly and verified all new groups/certificates',
    'with optimization disabled. The worker counted exactly 96 LP calls.',
    'A separate scalar/rational audit checked 294,912 diagnostic values, 48 floor',
    'identities, 96 asymmetric gaps, 384 signed comparisons and 799 aggregate records.',
    'It added no fits or LP calls. Maximum certificate gap:',
    f"{audit['maximum_certificate_gap']:.6e} game chips.",
    'Independently assembled normal-equation maximum residuals:',
    ', '.join(f'{x:.6e}' for x in audit['normal_equation_max_residuals'])+'.',
    f"All {len(plan['pins'])} input pins verified before retention.",
    'These checks are not a separate implementation of the card evaluator or a cold',
    'opposing review. Numerical certificate widths do not measure board-population',
    'uncertainty. This reused panel supports an intervention result, not a fresh',
    'generalization claim, six-max claim or measured deployed playing-strength gain.', '',
    '## Retention', '',
    'All nine previous milestones remain unchanged. Full new models, predictions,',
    'case records, groups, certificates, timings, audit and source diff are retained.',
    'No production source change, commit, push or adoption was performed.', '',
    'Original output: D:/Pontius-training/river-abstraction-study/witness-clipped-target-001',
    'Repository archive: experiments/river-abstraction-study/witness-clipped-target-001', '',
    'Plan SHA-256:', digest(OUT/'plan.json'), '',
    'Original result manifest SHA-256:', audit['result_manifest_sha256'], '']
with REPORT.open('x', encoding='utf-8', newline='\n') as f:
    f.write('\n'.join(lines))
shutil.copytree(OUT, ARCHIVE)
(ARCHIVE/'verification-tools').mkdir()
for name in ('design.md','experiment.py','build.py','from-boundary.diff','prepare.py',
             'audit.py','report-and-retain.py'):
    shutil.copyfile(HERE/name, ARCHIVE/'verification-tools'/name)
shutil.copyfile(REPORT, ARCHIVE/'report.md')
for p in OUT.iterdir():
    if p.is_file():
        assert digest(p) == digest(ARCHIVE/p.name)
members = {p.relative_to(ARCHIVE).as_posix(): digest(p)
           for p in sorted(ARCHIVE.rglob('*')) if p.is_file()}
write(ARCHIVE/'milestone-manifest.json', members)
for name, h in members.items():
    assert digest(ARCHIVE/name) == h, name
prior = {}
for name in ('development-001','holdout-001','group-optimality-001',
             'witness-groups-development-001','witness-pilot-001','witness-distillation-001',
             'witness-fit-diagnostic-001','witness-hybrid-001','witness-boundary-001'):
    directory = ROOT/'experiments/river-abstraction-study'/name
    for member, h in read(directory/'milestone-manifest.json').items():
        assert digest(directory/member) == h, (name, member)
    prior[name] = digest(directory/'milestone-manifest.json')
overview = ROOT/'docs/research/README.md'
with (HERE/'research-readme-before.md').open('xb') as f:
    f.write(overview.read_bytes())
with overview.open('ab') as f:
    f.write(b'\n## Clipped-target learning\n\n'
        b'[Witness-clipped-target-001](river-witness-clipped-target-001.md) changes only\n'
        b'the training targets: two severe failures improve, but most cases regress\n'
        b'and the mean remains worse than range-response. All outcomes are retained.\n')
receipt = dict(passed=True, milestone_members=len(members),
    milestone_sha256=digest(ARCHIVE/'milestone-manifest.json'), report_sha256=digest(REPORT),
    prior_milestones=prior, commit_performed=False, push_performed=False)
write(HERE/'retention.json', receipt)
print(json.dumps(receipt, indent=2))
