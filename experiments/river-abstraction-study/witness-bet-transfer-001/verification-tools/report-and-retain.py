"""Retain every bet-transfer outcome and a transparent report, without publication."""
from collections import Counter
from fractions import Fraction as Q
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess

ROOT=Path('D:/Pontius-worktrees/eval-runner-consolidation')
HERE=Path(__file__).parent
OUT=Path('D:/Pontius-training/river-abstraction-study/witness-bet-transfer-001')
ARCHIVE=ROOT/'experiments/river-abstraction-study/witness-bet-transfer-001'
REPORT=ROOT/'docs/research/river-witness-bet-transfer-001.md'
read=lambda p:json.loads(p.read_bytes())
digest=lambda p:sha256(p.read_bytes()).hexdigest()
mid=lambda v:float((Q(v['lower_exact'])+Q(v['upper_exact']))/2)


def write(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as f:
        f.write(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n')


p=read(OUT/'plan.json')
s=read(OUT/'summary.json')
audit=read(OUT/'audit.json')
sa=read(OUT/'summary-audit.json')
receipt=read(OUT/'receipt.json')
worker=read(OUT/'worker-receipt.json')
verifier=read(OUT/'verify-receipt.json')
assert receipt['exit']==worker['exit']==verifier['exit']==0
assert audit['passed'] and sa['passed']
assert not REPORT.exists() and not ARCHIVE.exists()
for path,h in p['pins'].items():assert digest(Path(path))==h,path
assert digest(OUT/'results-manifest.json')==receipt['result_manifest_sha256']
for name,h in read(OUT/'results-manifest.json').items():assert digest(OUT/name)==h,name
rows=[read(OUT/(c['id']+f'-bet-{bet:g}.json')) for c in p['cases'] for bet in p['bets']]
methods=p['methods']
counts=lambda c:'/'.join(str(c.get(k,0)) for k in ('lower','higher','overlapping'))
analysis={}
for key,panel in s['panels'].items():
    v=panel['overall']
    worst=sorted([r for r in rows if r['bet']==float(key)],
                 key=lambda r:r['comparisons']['range_response']['actual'],reverse=True)[:5]
    analysis[key]=dict(
        actual_reduction_percent=100*(v['means']['range_response']-v['means'][methods[0]])/
            v['means']['range_response'],
        floor_reduction_percent=100*(mid(v['floors']['range_response'])-mid(v['floors'][methods[0]]))/
            mid(v['floors']['range_response']),
        board_actual_counts=dict(Counter('lower' if x['comparisons']['range_response']['actual']['delta'] < -1e-10
            else 'higher' if x['comparisons']['range_response']['actual']['delta'] > 1e-10 else 'overlapping'
            for x in panel['boards'].values())),
        board_floor_counts=dict(Counter('lower' if Q(x['comparisons']['range_response']['floor']['upper_exact'])<0
            else 'higher' if Q(x['comparisons']['range_response']['floor']['lower_exact'])>0 else 'overlapping'
            for x in panel['boards'].values())),
        failed_robustness_panels=[dict(panel=name,label=label,
            actual_delta=x['comparisons']['range_response']['actual']['delta'],
            floor_delta=mid(x['comparisons']['range_response']['floor']))
            for name in ('textures','regimes','leave_one_board_out') for label,x in panel[name].items()
            if x['comparisons']['range_response']['actual']['delta']>=-1e-10 or
               Q(x['comparisons']['range_response']['floor']['upper_exact'])>=0],
        worst_actual=[dict(case=r['case'],candidate=r['methods'][methods[0]]['records'][-1]['full']['exploitability'],
            reference=r['methods']['range_response']['records'][-1]['full']['exploitability'],
            delta=r['comparisons']['range_response']['actual']) for r in worst])
write(OUT/'analysis.json',analysis)
labels={'2.5':'Quarter pot (2.5)','5.0':'Half pot (5), retained anchor','10.0':'Pot sized (10)'}
lines=['# Frozen bet-size transfer: witness-bet-transfer-001','',
    '## Result and decision rules','',
    'Actual-policy transfer: '+('PASS.' if s['actual_policy_transfer_pass'] else 'NOT PASSED.'),
    'Representation transfer: '+('PASS.' if s['representation_transfer_pass'] else 'NOT PASSED.'),
    'Texture/range/leave-one-board-out robustness: '+('PASS.' if s['robustness_pass'] else 'NOT PASSED.'),
    'These are the rules frozen before scoring, not confidence levels or adoption decisions.',
    'The two new bet sizes are judged separately; a win at one cannot offset a loss at',
    'the other. Half-pot data are a verified retained anchor, not a new replication.','',
    'Actual-policy transfer requires mean learned-minus-range-response exploitability',
    'below -1e-10 chips at 10000 iterations at both quarter-pot and pot-sized bets.',
    'Representation transfer separately requires a negative upper numerical endpoint',
    'of that difference in certified grouping floors at both new sizes. Robustness',
    'requires both comparisons to hold in every texture, range regime and omitted-board',
    'panel at each new size. Full per-board and case losses remain below.','',
    'Failures of the robustness rule are shown explicitly here. Positive delta means',
    'the learned method is worse than range-response in that measure. A negative',
    'floor delta with positive actual delta distinguishes representation potential',
    'from the policy the compressed-game solver actually produced.','',
    '| New bet | Panel | Actual delta | Floor delta |','|---|---|---:|---:|']
for key in ('2.5','10.0'):
    for v in analysis[key]['failed_robustness_panels']:
        lines.append(f"| {key} | {v['label']} | {v['actual_delta']:.10f} | {v['floor_delta']:.10f} |")
lines += ['',
    '## Actual full-hand exploitability at 10000 iterations','',
    'Lower is better. Units are conditional river-game chips; pot is always 10.',
    'These are unrestricted best-response evaluations of computed CFR policies.',
    'They are not sampled match win rates, BB/100 or six-max strength measurements.','',
    '| Bet size | Learned groups | Range-response | Range-equity | Reduction vs response |',
    '|---|---:|---:|---:|---:|']
for key in ('2.5','5.0','10.0'):
    v=s['panels'][key]['overall']
    lines.append(f"| {labels[key]} | {v['means'][methods[0]]:.10f} | "
        f"{v['means']['range_response']:.10f} | {v['means']['range_equity']:.10f} | "
        f"{analysis[key]['actual_reduction_percent']:.2f}% |")
lines += ['', '## Certified grouping floors','',
    'These are the least full-hand profile exploitabilities representable by each',
    'pair of groupings, shown as rational-certificate interval midpoints. An equilibrium',
    'in the compressed game need not attain this floor.','',
    '| Bet size | Learned groups | Range-response | Range-equity | Reduction vs response |',
    '|---|---:|---:|---:|---:|']
for key in ('2.5','5.0','10.0'):
    v=s['panels'][key]['overall']
    lines.append(f"| {labels[key]} | {mid(v['floors'][methods[0]]):.10f} | "
        f"{mid(v['floors']['range_response']):.10f} | {mid(v['floors']['range_equity']):.10f} | "
        f"{analysis[key]['floor_reduction_percent']:.2f}% |")
lines += ['', 'Counts mean lower / higher / numerically overlapping cases.','',
    '| Bet | Reference | Actual delta | Actual counts | Floor delta | Floor counts |',
    '|---|---|---:|---:|---:|---:|']
for key in ('2.5','5.0','10.0'):
    for m,v in s['panels'][key]['overall']['comparisons'].items():
        lines.append(f"| {key} | {m} | {v['actual']['delta']:.10f} | "
            f"{counts(v['actual']['counts'])} | {mid(v['floor']):.10f} | {counts(v['floor']['counts'])} |")
lines += ['', '## Earlier solver checkpoints','',
    '| Bet | Iterations | Learned | Range-response | Range-equity |','|---|---:|---:|---:|---:|']
for key in ('2.5','5.0','10.0'):
    for n,v in s['panels'][key]['iterations'].items():
        lines.append(f"| {key} | {n} | {v['means'][methods[0]]:.10f} | "
                     f"{v['means']['range_response']:.10f} | {v['means']['range_equity']:.10f} |")
lines += ['', '## Reusing half-pot actions versus re-solving','',
    'The representation is frozen, but CFR chooses actions anew for each bet size.',
    'The separate control applies the unchanged half-pot 10000-iteration policy under',
    'the new payoffs. Negative resolved-minus-fixed means re-solving reduces its',
    'exploitability. This diagnostic was predeclared and does not replace the primary',
    'comparison against other representations.','',
    '| Bet | Method | Re-solved | Fixed half-pot policy | Delta | Bettor change | Caller change |',
    '|---|---|---:|---:|---:|---:|---:|']
for key in ('2.5','5.0','10.0'):
    v=s['panels'][key]['overall']
    for m in methods:
        a,b=v['action_change'][m]
        lines.append(f"| {key} | {m} | {v['means'][m]:.10f} | {v['fixed_policy'][m]:.10f} | "
            f"{v['resolved_minus_fixed'][m]:.10f} | {a:.7f} | {b:.7f} |")
lines += ['', 'Action change is absolute probability change averaged by that seat\'s',
    'collision-conditioned hand marginal. The half-pot anchor has exactly zero change.',
    'No action-change threshold was used to select cases or make the transfer ruling.','',
    '## Solver residual at 10000 iterations','',
    '| Bet | Method | Above grouping floor | Compressed-game exploitability |',
    '|---|---|---:|---:|']
for key in ('2.5','5.0','10.0'):
    v=s['panels'][key]['overall']
    for m in methods:
        lines.append(f"| {key} | {m} | {v['above_floor'][m]:.10f} | {v['restricted'][m]:.10f} |")
lines += ['', 'The residual includes finite optimization and potentially the mismatch between',
    'a compressed equilibrium and the least exploitable representable profile. It is',
    'not all necessarily removable by more iterations of the same algorithm.','',
    '## Board sensitivity','',
    '| Board | Quarter-pot actual delta | Half-pot actual delta | Pot-sized actual delta |',
    '|---|---:|---:|---:|']
for b in range(16):
    vals=[s['panels'][k]['boards'][str(b)]['comparisons']['range_response']['actual']['delta']
          for k in ('2.5','5.0','10.0')]
    lines.append(f'| {b} | {vals[0]:.10f} | {vals[1]:.10f} | {vals[2]:.10f} |')
for name in ('textures','regimes','leave_one_board_out'):
    lines += ['', f'### {name}', '',
        '| Bet | Panel | Actual delta vs response | Floor delta vs response |','|---|---|---:|---:|']
    for key in ('2.5','5.0','10.0'):
        for label,v in s['panels'][key][name].items():
            c=v['comparisons']['range_response']
            lines.append(f"| {key} | {label} | {c['actual']['delta']:.10f} | {mid(c['floor']):.10f} |")
lines += ['', '## Change in relative advantage versus half pot','',
    'These are difference-of-differences: (learned minus reference at new bet) minus',
    '(learned minus reference at half pot). A positive value means less absolute',
    'advantage or more disadvantage in chips. Games differ, so this is descriptive;',
    'it is not a causal claim about real betting frequencies or a win-rate estimate.','',
    '| Bet | Reference | Actual interaction | Floor interaction |','|---|---|---:|---:|']
for key,refs in s['interactions_vs_half_pot'].items():
    for m,v in refs.items():lines.append(f"| {key} | {m} | {v['actual']:.10f} | {mid(v['floor']):.10f} |")
lines += ['', '## Largest actual-policy losses','',
    '| Bet | Case | Learned | Range-response | Delta |','|---|---|---:|---:|---:|']
for key,a in analysis.items():
    for v in a['worst_actual']:
        lines.append(f"| {key} | {v['case']['id']} | {v['candidate']:.10f} | "
                     f"{v['reference']:.10f} | {v['delta']:.10f} |")
lines += ['', '## Frozen design and verification','',
    'All 96 observed-panel cases are reused at each of three bet sizes: 288 cells.',
    'Six cases per board are equally weighted; sixteen boards receive equal weight.',
    'There is no mean pooled across bet sizes for primary claims. These are synthetic',
    'ranges, not reached betting posteriors. All games are heads-up, one bet, 96 holdings',
    'per seat, pot 10, stacks 20/20, with no raises or additional streets.','',
    'Quarter-pot and pot-sized games were built through RiverHoldem using identical',
    'input ranges. Joint/check/fold arrays stayed identical; call payoffs equal the',
    'showdown sign times joint probability times (5 + bet). All eleven raw features,',
    'four classifier outputs and group labels stayed identical at every bet size.',
    'The model never received bet size and no coefficient or feature was changed.',
    'Group capacities match the predecessor for every method and case.','',
    'There were exactly 1152 new LP calls and 576 new CFR trajectories. The existing',
    'LP iteration/time limits and rational saddle certificates applied unchanged.',
    'CFR uses deterministic alternating updates, zero initial regrets and unweighted',
    'average policies. All three checkpoints were retained. No model fitting, seed',
    'search, adaptive sample extension or scored-panel rehearsal. No new timed-budget',
    'comparison is claimed; source solve times are diagnostic only.','',
    'Preflight public-tree checks passed at all sizes, with direct payoff identities,',
    'feature invariance, tied showdowns and invalid bet refusals. Thirteen existing',
    'CFR/certificate tests passed. Console provenance is recorded in preflight.json.',
    f"Worker: {worker['seconds']:.6f} seconds; verifier: {verifier['seconds']:.6f} seconds.",
    f"Combined invocation: {receipt['seconds']:.6f} seconds, exit 0.",
    'Each subprocess had a 1200-second limit. No RSS ceiling or peak-memory claim.',
    'Python 3.14.6 / NumPy 2.5.2 / SciPy 1.18.0, one BLAS thread, no tracemalloc.','',
    'The parent reconstructed all inputs and groups, checked all 1728 asymmetric',
    'certificates with LP disabled and replayed every resolved policy, including the',
    'retained half-pot anchor: 8,640,000 deterministic iterations. Scalar arithmetic',
    'independently checked full-hand values and best responses for 2592 resolved',
    'policies and 864 fixed-policy controls. The rational summary audit re-derived all',
    'reported panels, intervals, comparisons, interactions and predeclared flags.',
    f"Feature values confirmed unchanged: {audit['unchanged_feature_values']:,}.",
    f"Maximum scalar/vector discrepancy: {audit['maximum_scalar_discrepancy']:.6e} chips.",
    f"Independent summary scalar checks: {sa['summary_scalar_checks']:,}.",
    f"Pinned files verified before and after: {len(p['pins'])}.",
    'No independent cold reviewer or population confidence interval is claimed.',
    'All fourteen earlier milestones are preserved. No production change, commit,',
    'push or adoption was performed.','',
    'Plan SHA-256:',digest(OUT/'plan.json'),'',
    'Frozen candidate SHA-256:',p['candidate_sha256'],'',
    'Original result manifest SHA-256:',receipt['result_manifest_sha256'],'']
with REPORT.open('x',encoding='utf-8',newline='\n') as f:f.write('\n'.join(lines))
shutil.copytree(OUT,ARCHIVE)
(ARCHIVE/'verification-tools').mkdir()
for name in ('design.md','experiment.py','summary-audit.py','prepare.py','report-and-retain.py',
             'preflight.json','worktree-before.json'):
    shutil.copyfile(HERE/name,ARCHIVE/'verification-tools'/name)
shutil.copyfile(REPORT,ARCHIVE/'report.md')
for file in OUT.iterdir():
    if file.is_file():assert digest(file)==digest(ARCHIVE/file.name)
members={f.relative_to(ARCHIVE).as_posix():digest(f) for f in sorted(ARCHIVE.rglob('*')) if f.is_file()}
write(ARCHIVE/'milestone-manifest.json',members)
for name,h in members.items():assert digest(ARCHIVE/name)==h,name
prior={}
for directory in sorted(ARCHIVE.parent.iterdir()):
    manifest=directory/'milestone-manifest.json'
    if directory!=ARCHIVE and manifest.is_file():
        for name,h in read(manifest).items():assert digest(directory/name)==h,(directory,name)
        prior[directory.name]=digest(manifest)
assert len(prior)==14
before=read(HERE/'worktree-before.json')
for name,h in before['modified_tracked_files'].items():assert digest(ROOT/name)==h,name
overview=ROOT/'docs/research/README.md'
with (HERE/'research-readme-before.md').open('xb') as f:f.write(overview.read_bytes())
with overview.open('ab') as f:
    f.write(b'\n## Frozen grouping bet-size transfer\n\n'
        b'[Witness-bet-transfer-001](river-witness-bet-transfer-001.md) tests unchanged\n'
        b'learned groups at quarter-pot, half-pot and pot-sized bets, with certified\n'
        b'floors, re-solved CFR policies and unchanged-half-pot-policy controls.\n')
git=['C:/Program Files/Git/cmd/git.exe','-c',f'safe.directory={ROOT}','-C',str(ROOT)]
assert subprocess.check_output(git+['rev-parse','HEAD'],text=True).strip()==before['head']
record=dict(passed=True,milestone_members=len(members),
    milestone_sha256=digest(ARCHIVE/'milestone-manifest.json'),report_sha256=digest(REPORT),
    prior_milestones=prior,source_head=before['head'],commit_performed=False,push_performed=False)
write(HERE/'retention.json',record)
print(json.dumps(record,indent=2))
