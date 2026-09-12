from hashlib import sha256
import json
from pathlib import Path
import shutil
from fractions import Fraction as Q

ROOT=Path('D:/Pontius-worktrees/eval-runner-consolidation')
HERE=Path(__file__).parent
OUT=Path('D:/Pontius-training/river-abstraction-study/witness-boundary-001')
ARCHIVE=ROOT/'experiments/river-abstraction-study/witness-boundary-001'
REPORT=ROOT/'docs/research/river-witness-boundary-001.md'
read=lambda p:json.loads(p.read_bytes())
digest=lambda p:sha256(p.read_bytes()).hexdigest()
mid=lambda x:float((Q(x['lower_exact'])+Q(x['upper_exact']))/2)

def write(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as f:
        f.write(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n')

a=read(OUT/'analysis.json'); audit=read(OUT/'audit.json'); plan=read(OUT/'plan.json')
assert audit['passed'] is True and read(OUT/'receipt.json')['exit']==0
assert not ARCHIVE.exists() and not REPORT.exists()
for path,h in plan['pins'].items(): assert digest(Path(path))==h,path
rows=[read(OUT/(c['id']+'.json')) for c in plan['cases']]
lines=['# Boundary-resolution intervention: witness-boundary-001','',
    'One authorized invocation completed all 48 observed evaluation cases, with 192 new',
    'LP calls and no model refitting, threshold search, control re-solves or omitted cases.',
    'The fixed transform clips each of four advantage features to [-0.5,+0.5] game chips.',
    'It is applied separately to exact witness values and saved model predictions.','',
    '## Main finding and research decision','',
    'Boundary-focused grouping is a strong oracle-assisted diagnostic on this panel.',
    'Clipped exact witness features reduce mean floor by 79.19% versus unmodified exact',
    'witness features and 90.84% versus range-response grouping. They improve 43 of 48',
    'cases against the unmodified oracle, with five overlapping intervals and no regression.',
    'They improve all 48 cases against both range controls. Every board mean improves',
    'against the unmodified oracle, and every leave-one-board-out mean remains favorable.',
    'This is the strongest observed oracle-assisted representation in this comparison.',
    'It still uses solved opponent witnesses and is not a cheap deployed improvement.','',
    'Clipping predictions helps in 46 cases and reduces their mean floor by 43.26%, but',
    'the other two cases suffer large regressions. The resulting mean is 18.07% worse',
    'than range-response grouping. Do not adopt this learned variant. Its high case-win',
    'count does not compensate for the retained losses in the declared mean endpoint.',
    'The numerical separation between clipped exact and clipped predicted features',
    'identifies a remaining approximation problem under this fixed grouping transform;',
    'it does not by itself diagnose missing information versus model capacity or training loss.','',
    'The next targeted learning test is to train the same fixed predictor on clipped',
    'witness targets, rather than learn full-magnitude values and clip only afterward.',
    'That changes the supervised target to match this successful oracle representation.',
    'It should retain architecture, input features and group capacity for a controlled',
    'comparison. Whether it repairs the severe learned regressions remains untested.',
    'This recommendation is not another launch authorization or a claim of success.','',
    '## Mean floors','',
    'Lower is better. These are midpoints of certified numerical intervals for minimum',
    'full-hand exploitability achievable with the specified groups in the conditional',
    'one-bet heads-up river game. They are not win rates or BB/100. All compressed',
    'methods match occupied capacity within each case. Eight boards have equal weight,',
    'each averaging three hand pools and two range regimes; 96 holdings per seat.','',
    '| Method | Mean floor |','|---|---:|']
for method,value in a['mean_floors'].items():lines.append(f'| {method} | {value:.10f} |')
lines += ['', '## Paired comparisons','',
    'Negative delta favors the new method. Counts are lower / higher / overlapping.','',
    '| New method | Reference | Mean delta | Counts |','|---|---|---:|---:|']
for method,cols in a['comparisons'].items():
    for other,c in cols.items():
        counts='/'.join(str(c['counts'].get(k,0)) for k in ('lower','higher','overlapping'))
        lines.append(f"| {method} | {other} | {c['delta']:.10f} | {counts} |")
lines += ['',
    'Twenty-seven clipped-oracle intervals overlap the full-hand control numerically.',
    'This is not a claim of exact mathematical zero exploitability. Neither oracle',
    'clustering rule is globally optimal among partitions, so its improvement is valid',
    'without implying any violation of the full-hand reference.','',
    '## Board sensitivity','',
    '| Board | Exact witness | Clipped oracle | Predicted-only | Clipped prediction | Range-response |',
    '|---|---:|---:|---:|---:|---:|']
for board,b in a['boards'].items():
    f=b['floors']
    lines.append(f"| {board} | {f['direct_witness']:.9f} | {f['clipped_oracle']:.9f} | "
                 f"{f['predicted_only']:.9f} | {f['clipped_prediction']:.9f} | {f['range_response']:.9f} |")
lines += ['', '| Leave-one-board-out contrast | Minimum delta | Maximum delta |',
    '|---|---:|---:|']
for method,other in [('clipped_oracle','direct_witness'),('clipped_oracle','range_response'),
                     ('clipped_prediction','predicted_only'),('clipped_prediction','range_response')]:
    values=a['lobo'][method][other]
    lines.append(f'| {method} minus {other} | {min(values):.10f} | {max(values):.10f} |')
lines += ['',
    'These are descriptive sensitivity checks, not confidence intervals. Excluding',
    'board 7 reverses the clipped-prediction mean comparison against range_response.',
    'Board 7 remains included in every main result. No post-hoc exclusion is justified.','',
    '## The two regressions against unmodified predictions','',
    '| Case | Unmodified floor | Clipped floor | Increase |','|---|---:|---:|---:|']
bad=[]
for r in rows:
    c=r['comparisons']['clipped_prediction']['predicted_only']
    if c['classification']=='higher':
        bad.append(r['case']['id'])
        lines.append(f"| {r['case']['id']} | {mid(r['floors']['predicted_only']):.9f} | "
                     f"{mid(r['floors']['clipped_prediction']):.9f} | {mid(c):.9f} |")
assert bad==['b07-p1-polarized','b07-p2-polarized']
lines += ['',
    'Both use polarized ranges on board 6h 6s Jh Qc Qd, with different hand pools.',
    'This locates the failures; it does not prove their cause or support dropping that',
    'board or range regime. Every comparison against every control is retained.','',
    '## Range regimes','',
    '| Regime | Clipped oracle | Exact witness | Clipped prediction | Predicted-only | Range-response |',
    '|---|---:|---:|---:|---:|---:|']
for regime,r in a['regimes'].items():
    f=r['floors']
    lines.append(f"| {regime} | {f['clipped_oracle']:.9f} | {f['direct_witness']:.9f} | "
                 f"{f['clipped_prediction']:.9f} | {f['predicted_only']:.9f} | {f['range_response']:.9f} |")
lines += ['', '## Interpretation limits','',
    'The 0.5-chip threshold was fixed from the preceding diagnostic band before this',
    'run. There was no threshold sweep. These are already observed boards, so even the',
    'large oracle result is an intervention result requiring new reserved evidence',
    'before a generalization claim. It is not a six-max or full-game result.',
    'Clipping preserves signs and inner-band magnitudes while collapsing large same-sign',
    'values. Its allocation of duplicate vectors among occupied anchors is part of the',
    'fixed clustering algorithm. No unique or optimal partition is implied.',
    'Case-win rates and numerical certificate widths do not quantify board-population',
    'uncertainty or replace the declared equal-board mean endpoint.','',
    '## Verification and retained execution','',
    f"Worker: {a['worker_seconds']:.6f} seconds; worker plus parent: "
    f"{a['worker_plus_parent_seconds']:.6f} seconds.",
    'The latter spans launch through parent verification and results-manifest writing,',
    'excluding preflight, output reservation and final receipt writing. Worker limit:',
    '600 seconds; parent outside it. Python 3.14.6 / NumPy 2.5.2 / SciPy 1.18.0, one',
    'BLAS thread. No RSS cap or peak-memory measurement. Both stages completed, exit 0.',
    'Existing per-LP five-second and 10,000-iteration limits remained unchanged.','',
    'Synthetic checks passed for endpoints, interior identity, signs, idempotence, arm',
    'separation, nonfinite/wrong-shape refusal and occupied capacity under ties.',
    'Saved predictions and exact witness advantages were independently reconstructed',
    'from the frozen model and witness policies, respectively. The parent reconstructed',
    'both feature/group paths and verified all new certificates with optimization disabled.',
    'The worker counted exactly 192 LP calls; no model fit occurred.','',
    'The separate scalar/rational audit checked all 73,728 clipped values and signs,',
    '96 floor identities, 192 asymmetric gaps, 672 comparisons and 1,034 aggregate',
    'records. It added no fits or LPs. Maximum new certificate width:',
    f"{audit['maximum_certificate_gap']:.6e} chips. These certify numerical payoff results,",
    'not a second implementation of the card evaluator. All 161 input pins matched.',
    'An audit-preparation launch initially encountered sandbox access denial; approved',
    'escalation succeeded. The research invocation was not retried and no data changed.',
    'No new cold opposing review was claimed or dispatched for this diagnostic.','',
    'Original output: D:/Pontius-training/river-abstraction-study/witness-boundary-001',
    'Repository archive: experiments/river-abstraction-study/witness-boundary-001',
    'All eight earlier milestones and original production source remain unchanged.',
    'No commit, push or deployment. Full groups/features/certificates and reports retained.','',
    'Plan SHA-256:',digest(OUT/'plan.json'),'',
    'Original result manifest SHA-256:',audit['result_manifest_sha256'],'']
with REPORT.open('x',encoding='utf-8',newline='\n') as f:f.write('\n'.join(lines))
shutil.copytree(OUT,ARCHIVE)
(ARCHIVE/'verification-tools').mkdir()
for name in ('design.md','experiment.py','build.py','from-hybrid.diff','prepare.py',
             'build-audit.py','audit.py','report-and-retain.py'):
    shutil.copyfile(HERE/name,ARCHIVE/'verification-tools'/name)
shutil.copyfile(REPORT,ARCHIVE/'report.md')
for p in OUT.iterdir():
    if p.is_file():assert digest(p)==digest(ARCHIVE/p.name)
members={p.relative_to(ARCHIVE).as_posix():digest(p) for p in sorted(ARCHIVE.rglob('*')) if p.is_file()}
write(ARCHIVE/'milestone-manifest.json',members)
for name,h in members.items():assert digest(ARCHIVE/name)==h,name
prior={}
for name in ('development-001','holdout-001','group-optimality-001','witness-groups-development-001',
             'witness-pilot-001','witness-distillation-001','witness-fit-diagnostic-001','witness-hybrid-001'):
    directory=ROOT/'experiments/river-abstraction-study'/name
    for member,h in read(directory/'milestone-manifest.json').items():
        assert digest(directory/member)==h,(name,member)
    prior[name]=digest(directory/'milestone-manifest.json')
overview=ROOT/'docs/research/README.md'
before=overview.read_bytes()
with (HERE/'research-readme-before.md').open('xb') as f:f.write(before)
with overview.open('ab') as f:
    f.write(b'\n## Boundary-resolution intervention\n\n'
        b'[Witness-boundary-001](river-witness-boundary-001.md) compares the same fixed\n'
        b'clipping transform on exact and predicted witness features, retaining all 48 cases.\n')
receipt=dict(passed=True,milestone_members=len(members),
    milestone_sha256=digest(ARCHIVE/'milestone-manifest.json'),report_sha256=digest(REPORT),
    prior_milestones=prior,commit_performed=False,push_performed=False)
write(HERE/'retention.json',receipt)
print(json.dumps(receipt,indent=2))
