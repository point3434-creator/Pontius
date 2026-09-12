"""Seal the full ordinal pilot and report, including any non-improvement."""
from collections import Counter
from fractions import Fraction as Q
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess

ROOT=Path('D:/Pontius-worktrees/eval-runner-consolidation')
HERE=Path(__file__).parent
OUT=Path('D:/Pontius-training/river-abstraction-study/witness-ordinal-001')
ARCHIVE=ROOT/'experiments/river-abstraction-study/witness-ordinal-001'
REPORT=ROOT/'docs/research/river-witness-ordinal-001.md'
read=lambda p:json.loads(p.read_bytes())
digest=lambda p:sha256(p.read_bytes()).hexdigest()
mid=lambda v:float((Q(v['lower_exact'])+Q(v['upper_exact']))/2)
def write(p,v):
    with p.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(v,sort_keys=True,indent=2,allow_nan=False)+'\n')
def direction(d):return 'lower' if d < -1e-10 else 'higher' if d > 1e-10 else 'overlapping'
def counts(v):return '/'.join(str(v.get(k,0)) for k in ('lower','higher','overlapping'))

p=read(OUT/'plan.json');s=read(OUT/'summary.json');a=read(OUT/'audit.json')
sa=read(OUT/'summary-audit.json');receipt=read(OUT/'receipt.json')
worker=read(OUT/'worker-receipt.json');verifier=read(OUT/'verify-receipt.json')
assert a['passed'] and sa['passed'] and receipt['exit']==worker['exit']==verifier['exit']==0
assert not ARCHIVE.exists() and not REPORT.exists()
for path,h in p['pins'].items():assert digest(Path(path))==h,path
assert digest(OUT/'results-manifest.json')==receipt['result_manifest_sha256']
for name,h in read(OUT/'results-manifest.json').items():assert digest(OUT/name)==h,name
before=read(HERE/'worktree-before.json')
for name,h in before['modified_tracked_files'].items():assert digest(ROOT/name)==h,name
git=['C:/Program Files/Git/cmd/git.exe','-c',f'safe.directory={ROOT}','-C',str(ROOT)]
assert subprocess.check_output(git+['rev-parse','HEAD'],text=True).strip()==before['head']
prior={}
for d in sorted(ARCHIVE.parent.iterdir()):
    manifest=d/'milestone-manifest.json'
    if d!=ARCHIVE and manifest.is_file():
        for name,h in read(manifest).items():assert digest(d/name)==h,(d,name)
        prior[d.name]=digest(manifest)
assert len(prior)==17
refs=('sign_conditioned','ordinary_preference','range_response')
analysis={}
for bet,panel in s['panels'].items():
    v=panel['overall']
    analysis[bet]=dict(actual_reductions_percent={m:100*(v['actual'][m]-v['actual']['ordinal'])/v['actual'][m] for m in refs},
        floor_reductions_percent={m:100*(mid(v['floors'][m])-mid(v['floors']['ordinal']))/mid(v['floors'][m]) for m in refs},
        board_counts={m:dict(Counter(direction(x['comparisons'][m]['actual']['delta']) for x in panel['boards'].values())) for m in refs},
        omit_board_counts={m:dict(Counter(direction(x['comparisons'][m]['actual']['delta']) for x in panel['leave_one_board_out'].values())) for m in refs},
        failures=[dict(category=c,label=k,reference=m,actual_delta=v['comparisons'][m]['actual']['delta'],floor_delta=mid(v['comparisons'][m]['floor']))
            for c in ('textures','regimes','leave_one_board_out') for k,v in panel[c].items() for m in refs
            if v['comparisons'][m]['actual']['delta']>=-1e-10 or Q(v['comparisons'][m]['floor']['upper_exact'])>=0])
    rows=[read(OUT/f"eval-{c['id']}-bet-{bet}.json") for c in p['evaluation_cases']]
    contributions={}
    for ref in refs:
        seats={}
        for seat in (0,1):
            lo=[];hi=[]
            for r in rows:
                left=r['solutions']['ordinal'][f'seat{seat}']['value']
                right=r['solutions'][ref][f'seat{seat}']['value']
                if seat==0:left,right=right,left
                lo.append((Q(left['lower_exact'])-Q(right['upper_exact']))/2)
                hi.append((Q(left['upper_exact'])-Q(right['lower_exact']))/2)
            seats['caller' if seat else 'bettor']=dict(lower_exact=str(sum(lo)/len(lo)),upper_exact=str(sum(hi)/len(hi)))
        error=abs(sum(mid(x) for x in seats.values())-mid(v['comparisons'][ref]['floor']))
        assert error<1e-10
        contributions[ref]=dict(**seats,closure_error=error)
    analysis[bet]['posthoc_seat_contributions']=contributions
write(OUT/'analysis.json',analysis)
assert all(Q(panel['overall']['floors']['ordinal']['lower_exact'])>
    Q(panel['overall']['actual']['ordinary_preference']) for panel in s['panels'].values())
lines=['# Multi-threshold preferences: witness-ordinal-001','',
    '## Decisions frozen before scoring','', '| Decision | Result |','|---|---|']
for k,v in s['flags'].items():lines.append(f"| {k} | {'PASS' if v else 'NOT PASSED'} |")
lines += ['',
    'Primary: pot-sized mean actual exploitability at 50000 iterations improves',
    'over the previous sign-conditioned predictor by more than 1e-10 chips. The',
    'separate representation flag requires a negative upper endpoint of the mean',
    'certified grouping-floor difference. Practical candidate flags require those',
    'comparisons against both old learned and range-response. Cross-bet robustness',
    'requires both measures to beat all three references in every texture, regime',
    'and omitted-board panel at both bet sizes. No pooled cross-bet acceptance rule.',
    'These descriptive pilot decisions are not confidence levels or adoption.', '',
    '## Interpretation','',
    f"At pot size, the actual reduction versus the previous conditioned predictor is",
    f"{analysis['10']['actual_reductions_percent']['sign_conditioned']:.2f}%; at half pot it is",
    f"{analysis['5']['actual_reductions_percent']['sign_conditioned']:.2f}% (negative means a regression).",
    'The new model is worse than the old learned model on both aggregate panels.',
    'Its small pot-sized gain does not justify replacing the established baseline.',
    'At both bet sizes, even the ordinal grouping\'s certified lower floor exceeds',
    'the old learned model\'s actual 50000-iteration score. More iterations within',
    'these fixed groups therefore cannot reverse that aggregate comparison.',
    'The oracle thresholds improve on oracle signs, but remain substantially worse',
    'than clipped continuous advantages. These fixed cutoffs preserve some useful',
    'information without providing a strong learned grouping improvement.', '',
    'A post-hoc decomposition of the retained certificates attributes most of the',
    'half-pot floor regression against the previous conditioned model to the caller',
    'grouping. This calculation required no additional solves and did not change',
    'any frozen decision rule. It identifies a useful diagnostic target; it does',
    'not establish that threshold crossings caused the loss.', '',
    '## Full-hand policy exploitability','',
    'Lower is better, in conditional river-game chips with pot 10. Every non-oracle',
    'candidate uses the same RegretBR solver and the same iteration checkpoints.',
    'These are enumerated best-response scores within the fixed hand pools, not',
    'sampled match returns, BB/100, or six-max playing-strength measurements.','',
    '| Bet | Iterations | Ordinal | Previous conditioned | Old learned | Range-response |',
    '|---|---:|---:|---:|---:|---:|']
for bet,panel in s['panels'].items():
    for n in ('1000','10000','50000'):
        lines.append(f'| {bet} | {n} | '+' | '.join(f"{panel['checkpoints'][n]['actual'][m]:.10f}" for m in p['solver_methods'])+' |')
lines += ['', '| Bet | Reference | Actual reduction percent | Floor reduction percent |','|---|---|---:|---:|']
for bet,v in analysis.items():
    for m in refs:lines.append(f"| {bet} | {m} | {v['actual_reductions_percent'][m]:.2f} | {v['floor_reductions_percent'][m]:.2f} |")
lines += ['', 'Positive reduction means improvement; negative means worse.','',
    '## Representation floors and oracle information','',
    'Each floor is the least full-hand profile exploitability representable by that',
    'particular pair of groups. Displayed values are midpoints of retained exact',
    'rational certificate intervals. Oracle-ordinal uses the nine exact threshold',
    'labels, oracle-sign uses only three zero labels, and oracle-clipped uses the',
    'three advantage values clipped to [-0.5,0.5]. Their witness policies are',
    'numerical solutions checked by the same rational certificate procedure.',
    'None is deployable or a bound over all possible groupings. Soft predictions',
    'can distinguish hands tied under hard labels; the hard-label oracle does not',
    'bound the learned model\'s performance.','',
    '| Bet | Grouping | Certified floor | Actual minus floor, 50k |','|---|---|---:|---:|']
for bet,panel in s['panels'].items():
    v=panel['overall']
    for m in p['methods']:
        residual=f"{v['actual'][m]-mid(v['floors'][m]):.10f}" if m in v['actual'] else 'Not solved iteratively'
        lines.append(f"| {bet} | {m} | {mid(v['floors'][m]):.10f} | {residual} |")
lines += ['', '## Board sensitivity and matched differences','',
    'Deltas are ordinal minus reference. Counts are lower / higher / numerically',
    'overlapping. Each bet has 32 balanced cases across eight board units.','',
    '| Bet | Reference | Actual delta | Case counts | Board counts | Omit-board counts |',
    '|---|---|---:|---:|---:|---:|']
for bet,panel in s['panels'].items():
    for m in refs:
        v=panel['overall']['comparisons'][m]['actual']
        lines.append(f"| {bet} | {m} | {v['delta']:.10f} | {counts(v['counts'])} | "
            f"{counts(analysis[bet]['board_counts'][m])} | {counts(analysis[bet]['omit_board_counts'][m])} |")
for category in ('boards','textures','regimes','leave_one_board_out'):
    lines += ['', '### '+category,'', '| Bet | Panel | Reference | Actual delta | Floor lower | Floor upper |',
        '|---|---|---|---:|---:|---:|']
    for bet,panel in s['panels'].items():
        for label,v in panel[category].items():
            for m in refs:
                c=v['comparisons'][m]
                lines.append(f"| {bet} | {label} | {m} | {c['actual']['delta']:.10f} | "
                    f"{float(Q(c['floor']['lower_exact'])):.10f} | {float(Q(c['floor']['upper_exact'])):.10f} |")
lines += ['', '## Threshold-order diagnostics','',
    'Entries are mean own-hand marginal mass with any threshold crossing, averaged',
    'over the three witnesses. Each witness counts once per hand if its later',
    'threshold probability exceeds an earlier one by more than 1e-12. These are',
    'diagnostics only: no sorting or projection changed the feature vectors.','',
    '| Bet | Bettor crossing fraction | Caller crossing fraction |','|---|---:|---:|']
for bet,panel in s['panels'].items():
    x,y=panel['overall']['crossing_mass'];lines.append(f'| {bet} | {x:.10f} | {y:.10f} |')
lines += ['', '## Post-hoc seat decomposition','',
    'These are additive contributions to the certified floor difference, not new',
    'policy runs: minus half the constrained-bettor value difference plus half the',
    'constrained-caller value difference. Positive means the ordinal grouping is',
    'worse for that contribution. Interval arithmetic is retained in analysis.json;',
    'midpoint sums match the reported floor deltas within 1e-10 chips.','',
    '| Bet | Reference | Bettor contribution | Caller contribution |','|---|---|---:|---:|']
for bet,record in analysis.items():
    for ref,v in record['posthoc_seat_contributions'].items():
        lines.append(f"| {bet} | {ref} | {mid(v['bettor']):.10f} | {mid(v['caller']):.10f} |")
lines += ['', '## Frozen design and verification','',
    'Reuse 64 retained training cells from eight boards, two pools, two regimes and',
    'two bet sizes. Fit nine binary tasks per seat at thresholds -0.25, 0, +0.25',
    'chips, in witness-major order. A computed equality receives label 0.5. The',
    'six zero-threshold fit records exactly reproduce the previous conditioned',
    'model; their predictions match on every evaluated hand. No new training LP.',
    'Inputs and fit settings are unchanged: eleven raw probability features plus',
    'bet/pot, 91 quadratic columns, ordinary ridge-logistic objective with lambda',
    '0.001 on slopes only, and own-hand marginal weights totaling 1/64 per cell.',
    'There was no threshold search or fitting on evaluation data.','',
    'Eight new boards were frozen before fitting, two per texture, excluding all',
    '44 previous boards and their suit isomorphisms. Two pools and two regimes at',
    'bets 5 and 10 give 64 evaluation cells. All games have 96 holdings per seat,',
    'pot 10, stacks 20/20, and one heads-up bet with no raises. These are synthetic',
    'conditional ranges and eight board-level units, not 64 independent boards.',
    'The two bet panels are reported separately. This is a fresh-board pilot, not',
    'a population confidence statement.','',
    'All nine sigmoid outputs are used directly. Independent heads can cross;',
    'no coherent-distribution claim is made. Group capacities and weighted anchored',
    'clustering stay fixed. Added output heads increase model parameters and',
    'embedding dimension; equal group count is not equal model size or wall time.',
    'The model is written and hashed before any evaluation file exists, then fitting',
    'is disabled. Oracle labels never enter learned prediction. All four non-oracle',
    'policies use unchanged RegretBR at matched 1000/10000/50000 update counts.','',
    'Twenty preflight tests passed: six new target/data/audit checks, eight preserved',
    'fit/data checks and six preserved solver checks. The initial label-boundary',
    'test failed as intended against the retained repeated-sign RED scaffold.',
    'No scored-panel rehearsal. All receipts are retained.','',
    'The worker made 1024 new LP calls and 18 fits, retaining 256 trajectories and',
    '768 policies. Parent verification disabled LP, rebuilt training cases, checked',
    '384 retained plus 1024 new certificates, reproduced all 18 fits, and then',
    'disabled fitting for evaluation. Every policy was replayed from zero for',
    '12.8 million iterations and checked with independent scalar evaluation.',
    'A separate Fraction audit rebuilt panels, means, certificate differences,',
    'decision flags and crossing frequencies.',
    f"Maximum scalar discrepancy: {a['maximum_scalar_discrepancy']:.6e} chips.",
    f"Independent summary scalar checks: {sa['summary_scalar_checks']:,}.",
    f"Pinned files checked before and after: {len(p['pins'])}.",
    f"Worker: {worker['seconds']:.6f} s; verifier: {verifier['seconds']:.6f} s.",
    f"Combined invocation: {receipt['seconds']:.6f} s, exit 0.",
    'Python 3.14.6, NumPy 2.5.2, SciPy 1.18.0; one BLAS thread; no tracemalloc.',
    'Each subprocess had a 1200-second timeout. No RSS ceiling or peak-memory claim.',
    'All seventeen prior milestones are preserved. No production change, adoption,',
    'commit, push or independent cold review is claimed.','',
    'Plan SHA-256:',digest(OUT/'plan.json'),'',
    'Candidate SHA-256:',digest(OUT/'candidate.json'),'',
    'Original result manifest SHA-256:',receipt['result_manifest_sha256'],'']
with REPORT.open('x',encoding='utf-8',newline='\n') as f:f.write('\n'.join(lines))
shutil.copytree(OUT,ARCHIVE);(ARCHIVE/'verification-tools').mkdir()
for f in HERE.iterdir():
    if f.is_file() and f.name!='plan.json':shutil.copyfile(f,ARCHIVE/'verification-tools'/f.name)
shutil.copyfile(REPORT,ARCHIVE/'report.md')
for f in OUT.iterdir():
    if f.is_file():assert digest(f)==digest(ARCHIVE/f.name)
members={f.relative_to(ARCHIVE).as_posix():digest(f) for f in sorted(ARCHIVE.rglob('*')) if f.is_file()}
write(ARCHIVE/'milestone-manifest.json',members)
for name,h in members.items():assert digest(ARCHIVE/name)==h,name
overview=ROOT/'docs/research/README.md'
with (HERE/'research-readme-before.md').open('xb') as f:f.write(overview.read_bytes())
with overview.open('ab') as f:
    f.write(b'\n## Magnitude-aware threshold preferences\n\n'
        b'[Witness-ordinal-001](river-witness-ordinal-001.md) tests fixed advantage\n'
        b'thresholds against the preserved sign-conditioned model on eight fresh\n'
        b'boards, with matched solver budgets and three oracle controls.\n')
assert subprocess.check_output(git+['rev-parse','HEAD'],text=True).strip()==before['head']
record=dict(passed=True,milestone_members=len(members),milestone_sha256=digest(ARCHIVE/'milestone-manifest.json'),
    report_sha256=digest(REPORT),candidate_sha256=digest(ARCHIVE/'candidate.json'),prior_milestones=prior,
    source_head=before['head'],commit_performed=False,push_performed=False)
write(HERE/'retention.json',record);print(json.dumps(record,indent=2))
