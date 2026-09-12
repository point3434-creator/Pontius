from hashlib import sha256
import json
from pathlib import Path
import shutil

ROOT=Path('D:/Pontius-worktrees/eval-runner-consolidation')
HERE=Path(__file__).parent
OUT=Path('D:/Pontius-training/river-abstraction-study/witness-hybrid-001')
ARCHIVE=ROOT/'experiments/river-abstraction-study/witness-hybrid-001'
REPORT=ROOT/'docs/research/river-witness-hybrid-001.md'
read=lambda p:json.loads(p.read_bytes())
digest=lambda p:sha256(p.read_bytes()).hexdigest()

def write(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as f:
        f.write(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n')

a=read(OUT/'analysis.json'); audit=read(OUT/'audit.json'); plan=read(OUT/'plan.json')
assert audit['passed'] is True and read(OUT/'receipt.json')['exit']==0
assert not ARCHIVE.exists() and not REPORT.exists()
for path,h in plan['pins'].items(): assert digest(Path(path))==h,path
lines=['# Combined-feature intervention: witness-hybrid-001','',
    'One authorized invocation completed all 48 already observed evaluation cases.',
    'There were 192 new LP calls and no model refitting, parameter sweep, control',
    're-solves or case deletion. Eight boards, three pools and two range regimes',
    'are weighted equally within the balanced panel. Each case has 96 holdings per seat.','',
    '## Research disposition','',
    'Do not adopt the fixed hybrid as an improvement over the strongest existing control.',
    'Restoring the original features reduces the mean floor by 48.25% versus predicted-only',
    'grouping, but hybrid is 3.26% worse than raw11 and 7.70% worse than range_response.',
    'The raw11 control is essential: the repair does not demonstrate incremental value',
    'from these learned predictions. Both raw11 and hybrid improve 45 of 48 cases against',
    'predicted-only. Hybrid is better than raw11 in 21 cases, worse in 25, with two',
    'overlapping numerical intervals. Those overlaps are not assertions of exact equality.','',
    'Hybrid improves every board mean against predicted-only. The incremental comparison',
    'against raw11 splits four boards each way; its overall mean is unfavorable, and',
    'removing any one board still leaves hybrid worse on average than raw11.','',
    'Hybrid is 3.67% better than range_equity on the overall panel, but only 25 of 48',
    'cases improve, and that small mean benefit changes sign in one leave-one-board-out',
    'check. The stronger range_response control is better on average. There is no basis',
    'to select the weaker comparison as the headline and declare a new best method.','',
    'This is an observed-panel intervention, not a fresh held-out confirmation or a',
    'six-max playing-strength result. It tests one fixed training-normalized mixture.',
    'It does not establish that every weighting, predictor or learned abstraction fails.',
    'Future work should address decision-relevant prediction or grouping, rather than',
    'assume another mixture of these same predictions will close the direct-witness gap.','',
    '## Mean strategic floors','',
    'Lower is better. Values are midpoints of certified intervals in game chips: the',
    'minimum full-hand exploitability achievable with these groups in the conditional',
    'one-bet heads-up river game. They are not a trained-policy win rate or BB/100.',
    'All compressed methods use identical occupied capacity per seat within each case.','',
    '| Method | Mean floor |','|---|---:|']
for method,value in a['mean_floors'].items(): lines.append(f'| {method} | {value:.10f} |')
lines += ['', '## Hybrid comparisons','',
    'Negative differences favor hybrid. Counts are lower / higher / overlapping.','',
    '| Reference | Mean hybrid-minus-reference | Counts |','|---|---:|---:|']
for method,c in a['comparisons']['hybrid'].items():
    counts='/'.join(str(c['counts'].get(k,0)) for k in ('lower','higher','overlapping'))
    lines.append(f"| {method} | {c['delta']:.10f} | {counts} |")
lines += ['', '## Board sensitivity','',
    '| Board | Hybrid | Raw11 | Delta predicted-only | Delta raw11 | Delta range-response |',
    '|---|---:|---:|---:|---:|---:|']
for board,b in a['boards'].items():
    f=b['floors']; d=b['hybrid_deltas']
    lines.append(f"| {board} | {f['hybrid']:.9f} | {f['raw11']:.9f} | "
        f"{d['predicted_only']:.9f} | {d['raw11']:.9f} | {d['range_response']:.9f} |")
lines += ['', '| Leave-one-board-out reference | Minimum mean delta | Maximum mean delta |',
    '|---|---:|---:|']
for method,values in a['lobo_hybrid'].items():
    lines.append(f'| {method} | {min(values):.10f} | {max(values):.10f} |')
lines += ['',
    'These are descriptive sensitivity checks, not confidence intervals. The 48 cases',
    'are not 48 independent boards. All board/pool/regime/texture summaries are retained.','',
    '## Range regimes','',
    '| Regime | Predicted-only | Raw11 | Hybrid | Range-response |',
    '|---|---:|---:|---:|---:|']
for regime,r in a['regimes'].items():
    f=r['floors']
    lines.append(f"| {regime} | {f['predicted_only']:.9f} | {f['raw11']:.9f} | "
                 f"{f['hybrid']:.9f} | {f['range_response']:.9f} |")
lines += ['', '## Fixed feature definition','',
    'Raw11 contains the nine range-response features plus range and uniform equity.',
    'Hybrid concatenates raw11 and the four saved witness predictions. One scalar per',
    'seat/block is the RMS within-case dispersion over the 48 training cases, using',
    'equal case weights and own-hand marginals. Divide each block by that scalar,',
    'giving equal training within-case distance energy. No per-column standardization,',
    'evaluation-dependent scale or coefficient search. Anchored clustering is unchanged.','',
    '| Seat | Raw scale | Prediction scale |','|---|---:|---:|']
for seat,v in enumerate(a['scales']):
    lines.append(f"| {seat} | {v['raw']:.12f} | {v['prediction']:.12f} |")
lines += ['', '## Execution and independent verification','',
    f"Worker: {a['worker_seconds']:.6f} seconds. Worker plus parent: "
    f"{a['worker_plus_parent_seconds']:.6f} seconds.",
    'The second timer begins before worker launch and ends after parent verification',
    'and results-manifest writing. It excludes preflight, output reservation and writing',
    'the final receipt. Parent work is outside the 600-second worker limit. No RSS cap',
    'or peak-memory measurement. Python 3.14.6 / NumPy 2.5.2 / SciPy 1.18.0; BLAS threads 1.',
    'Existing per-LP five-second and 10,000-iteration limits were preserved. Exit 0.','',
    'Pre-execution synthetic checks passed: equal-case weighted scales and offset',
    'invariance, block concatenation, exact occupied capacity even for tied features,',
    'and refusal of invalid/zero scales. Fitting entry points were disabled. The worker',
    'counted exactly 192 LP calls. The parent disabled optimization and reconstructed',
    'every scale/input/feature/group and verified every new certificate and comparison.',
    'All raw inputs and predictions matched their sealed prior records.','',
    'The independent scalar/rational audit verified four training-derived scales, 96',
    'new floor identities, 192 asymmetric gap records, 672 signed comparisons and 1,034',
    'aggregate records. It used no extra LP or fit. Maximum new certificate width:',
    f"{audit['maximum_certificate_gap']:.6e} chips. This concerns numerical certification",
    'on binary64 payoffs, not board-sampling uncertainty or an independent card evaluator.',
    'All 270 pinned files matched. This is a proportionate standalone research check,',
    'not a claim of a new cold opposing review. No extra reviewer was dispatched.','',
    '## Retention','',
    'Original output: D:/Pontius-training/river-abstraction-study/witness-hybrid-001',
    'Repository milestone: experiments/river-abstraction-study/witness-hybrid-001',
    'All 48 case results, groups, certificates, comparisons, summaries, scales, source',
    'recipe and audit are retained. All seven earlier milestones remain unchanged.',
    'No production source was modified, and no commit or push was performed.','',
    'Plan SHA-256:',digest(OUT/'plan.json'),'',
    'Original result manifest SHA-256:',audit['result_manifest_sha256'],'']
with REPORT.open('x',encoding='utf-8',newline='\n') as f:f.write('\n'.join(lines))
shutil.copytree(OUT,ARCHIVE)
(ARCHIVE/'verification-tools').mkdir()
for name in ('design.md','experiment.py','prepare.py','audit.py','report-and-retain.py'):
    shutil.copyfile(HERE/name,ARCHIVE/'verification-tools'/name)
shutil.copyfile(REPORT,ARCHIVE/'report.md')
for p in OUT.iterdir():
    if p.is_file(): assert digest(p)==digest(ARCHIVE/p.name)
members={p.relative_to(ARCHIVE).as_posix():digest(p) for p in sorted(ARCHIVE.rglob('*')) if p.is_file()}
write(ARCHIVE/'milestone-manifest.json',members)
for name,h in members.items(): assert digest(ARCHIVE/name)==h,name
prior={}
for name in ('development-001','holdout-001','group-optimality-001','witness-groups-development-001',
             'witness-pilot-001','witness-distillation-001','witness-fit-diagnostic-001'):
    directory=ROOT/'experiments/river-abstraction-study'/name
    for member,h in read(directory/'milestone-manifest.json').items():
        assert digest(directory/member)==h,(name,member)
    prior[name]=digest(directory/'milestone-manifest.json')
overview=ROOT/'docs/research/README.md'
before=overview.read_bytes()
with (HERE/'research-readme-before.md').open('xb') as f:f.write(before)
with overview.open('ab') as f:
    f.write(b'\n## Combined-feature intervention\n\n'
        b'[Witness-hybrid-001](river-witness-hybrid-001.md) compares fixed hybrid and raw11\n'
        b'grouping on all 48 observed evaluation cases, with 192 new certified LP calls.\n')
receipt=dict(passed=True,milestone_members=len(members),
    milestone_sha256=digest(ARCHIVE/'milestone-manifest.json'),report_sha256=digest(REPORT),
    prior_milestones=prior,commit_performed=False,push_performed=False)
write(HERE/'retention.json',receipt)
print(json.dumps(receipt,indent=2))
