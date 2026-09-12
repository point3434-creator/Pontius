"""Retain every trained model and held-out result without adoption or publication."""
from collections import Counter
from fractions import Fraction as Q
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess

ROOT=Path('D:/Pontius-worktrees/eval-runner-consolidation')
HERE=Path(__file__).parent
OUT=Path('D:/Pontius-training/river-abstraction-study/witness-bet-conditioned-001')
ARCHIVE=ROOT/'experiments/river-abstraction-study/witness-bet-conditioned-001'
REPORT=ROOT/'docs/research/river-witness-bet-conditioned-001.md'
read=lambda p:json.loads(p.read_bytes())
digest=lambda p:sha256(p.read_bytes()).hexdigest()
mid=lambda v:float((Q(v['lower_exact'])+Q(v['upper_exact']))/2)
def write(p,v):
    with p.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(v,sort_keys=True,indent=2,allow_nan=False)+'\n')
def counts(c):return '/'.join(str(c.get(k,0)) for k in ('lower','higher','overlapping'))
def direction(x):return 'lower' if x < -1e-10 else 'higher' if x > 1e-10 else 'overlapping'

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
assert len(prior)==16
analysis={}
for bet,panel in s['panels'].items():
    v=panel['overall']
    analysis[bet]=dict(actual_reductions_percent={m:100*(v['actual'][m]-v['actual']['conditioned'])/v['actual'][m]
        for m in ('blind','ordinary_preference','range_response')},
        floor_reductions_percent={m:100*(mid(v['floors'][m])-mid(v['floors']['conditioned']))/mid(v['floors'][m])
        for m in ('blind','ordinary_preference','range_response')},
        actual_board_counts={m:dict(Counter(direction(x['comparisons'][m]['actual']['delta']) for x in panel['boards'].values()))
            for m in ('blind','ordinary_preference','range_response')},
        actual_omitted_board_counts={m:dict(Counter(direction(x['comparisons'][m]['actual']['delta'])
            for x in panel['leave_one_board_out'].values())) for m in ('blind','ordinary_preference','range_response')},
        failed_robustness_panels=[dict(category=c,label=k,reference=m,
            actual_delta=v['comparisons'][m]['actual']['delta'],floor_delta=mid(v['comparisons'][m]['floor']))
            for c in ('textures','regimes','leave_one_board_out') for k,v in panel[c].items()
            for m in ('blind','ordinary_preference','range_response')
            if v['comparisons'][m]['actual']['delta']>=-1e-10 or Q(v['comparisons'][m]['floor']['upper_exact'])>=0])
write(OUT/'analysis.json',analysis)
assert s['flags']==dict(conditioning_actual_gain=True,conditioning_floor_gain=True,
    beats_existing_actual=False,beats_existing_floor=False,cross_bet_robustness=False)
lines=['# Bet-conditioned preference pilot: witness-bet-conditioned-001','',
    '## Frozen decisions','', '| Decision | Result |','|---|---|']
for key,v in s['flags'].items():lines.append(f"| {key} | {'PASS' if v else 'NOT PASSED'} |")
lines += ['',
    'The primary actual flag compares conditioned against blind on pot-sized games',
    'at 50000 iterations, requiring mean delta below -1e-10. The separate floor flag',
    'requires a negative upper endpoint of the mean certified floor difference.',
    'Practical candidate flags require the same comparisons against both old learned',
    'and range-response. Cross-bet robustness requires both measures to beat all three',
    'controls in every texture, regime and omitted-board panel at both bet sizes.',
    'Every rule was frozen before training. They are descriptive decisions, not',
    'confidence levels or adoption decisions. Neither bet size can offset the other.', '',
    '## Interpretation','',
    'Bet size helps the matched new predictor, but the new candidate does not replace',
    'the existing learned model. On pot-sized evaluation cells, conditioning reduces',
    f"actual exploitability by {analysis['10']['actual_reductions_percent']['blind']:.2f}%",
    'versus the blind control, and also improves its certified grouping floor.',
    f"The half-pot actual reduction versus blind is {analysis['5']['actual_reductions_percent']['blind']:.2f}%.",
    'The conditioned predictor beats range-response on both aggregate bet panels.',
    'However, it is worse than the old learned model on both, by',
    f"{-analysis['10']['actual_reductions_percent']['ordinary_preference']:.2f}% at pot size and",
    f"{-analysis['5']['actual_reductions_percent']['ordinary_preference']:.2f}% at half pot.",
    'This does not show that adding bet size harms the old model: the new model also',
    'uses different targets, output count and training examples. The matched blind',
    'comparison is the evidence specifically about exposing bet size.', '',
    'Exact clipped-advantage groups remain much better than all learned groups on',
    'these fresh boards. Exact hard-sign groups are substantially worse at pot size.',
    'That makes magnitude-aware prediction a useful follow-up: the exact values',
    'provide grouping distinctions that hard action labels omit. It does not prove',
    'a learned magnitude predictor will generalize or that hard signs bound what',
    'soft classifier probabilities can achieve. Current coefficients stay unchanged.', '',
    '## Actual policies on fresh boards','',
    'Lower unrestricted exploitability is better. Units are conditional river-game',
    'chips, with pot 10. All methods below use the same RegretBR solver from zero.',
    'These are full enumerations within the selected hand pools, not sampled match',
    'returns, BB/100, or six-max playing-strength results.','',
    '| Bet | Iterations | Conditioned | Blind | Old learned | Range-response |',
    '|---|---:|---:|---:|---:|---:|']
for bet,panel in s['panels'].items():
    for n in ('1000','10000','50000'):
        lines.append(f'| {bet} | {n} | '+' | '.join(f"{panel['checkpoints'][n]['actual'][m]:.10f}"
            for m in p['solver_methods'])+' |')
lines += ['', '| Bet | Reference | Actual reduction percent | Floor reduction percent |',
    '|---|---|---:|---:|']
for bet,v in analysis.items():
    for m in ('blind','ordinary_preference','range_response'):
        lines.append(f"| {bet} | {m} | {v['actual_reductions_percent'][m]:.2f} | {v['floor_reductions_percent'][m]:.2f} |")
lines += ['', 'Positive reduction means improvement; a negative reduction means worse.', '',
    '## Representation floors and oracle controls','',
    'Floors are the least full-hand profile exploitabilities representable by each',
    'group pair. Displayed numbers are midpoints of retained rational certificate',
    'intervals. Oracle-sign uses exact target-game action preferences; oracle-clipped',
    'uses exact action advantages clipped to [-0.5,0.5]. Neither is deployable.',
    'The sign oracle isolates the information retained by our classification target,',
    'while the clipped oracle retains magnitude as well as direction. Neither is',
    'a bound over all possible groupings. In particular, hard sign features can tie',
    'many hands, while soft learned probabilities can retain additional distinctions;',
    'the sign oracle is not a lower bound on the learned predictor\'s exploitability.',
    'Oracle features are computed from the certified numerical witness policies;',
    'a computed zero advantage receives label 0.5, as in the predecessor classifier.','',
    '| Bet | Method | Certified floor | Actual minus floor at 50k |','|---|---|---:|---:|']
for bet,panel in s['panels'].items():
    v=panel['overall']
    for m in p['methods']:
        residual=f"{v['actual'][m]-mid(v['floors'][m]):.10f}" if m in v['actual'] else 'Not solved iteratively'
        lines.append(f"| {bet} | {m} | {mid(v['floors'][m]):.10f} | {residual} |")
lines += ['', '## Matched comparisons and board sensitivity','',
    'All deltas are conditioned minus reference. Counts mean lower / higher /',
    'numerically overlapping. Each bet has 32 cases across eight board units.','',
    '| Bet | Reference | Actual delta | Case counts | Board counts | Omit-board counts | Floor delta |',
    '|---|---|---:|---:|---:|---:|---:|']
for bet,panel in s['panels'].items():
    for m,v in panel['overall']['comparisons'].items():
        if 'actual' in v:
            lines.append(f"| {bet} | {m} | {v['actual']['delta']:.10f} | {counts(v['actual']['counts'])} | "
                f"{counts(analysis[bet]['actual_board_counts'][m])} | "
                f"{counts(analysis[bet]['actual_omitted_board_counts'][m])} | {mid(v['floor']):.10f} |")
for category in ('boards','textures','regimes','leave_one_board_out'):
    lines += ['', '### '+category,'',
        '| Bet | Panel | Reference | Actual delta | Floor lower | Floor upper |',
        '|---|---|---|---:|---:|---:|']
    for bet,panel in s['panels'].items():
        for label,v in panel[category].items():
            for m in ('blind','ordinary_preference','range_response'):
                c=v['comparisons'][m]
                lines.append(f"| {bet} | {label} | {m} | {c['actual']['delta']:.10f} | "
                    f"{float(Q(c['floor']['lower_exact'])):.10f} | {float(Q(c['floor']['upper_exact'])):.10f} |")
lines += ['', '## Design and limits','',
    'Eight original training boards, two hand pools and two range regimes at each',
    'of two bet sizes give 64 training cells. Eight new boards were selected before',
    'training by the frozen hash rule, two per texture, excluding all 36 earlier',
    'boards and their suit isomorphisms. The same pools/regimes/sizes give 64',
    'evaluation cells. Each has 96 holdings per seat, stacks 20/20, pot 10, one bet',
    'of 5 or 10, with no raises or extra streets. These are synthetic conditional',
    'ranges. Eight balanced boards are eight evaluation units, not 64 independent',
    'boards. This is a small fresh-board pilot, not a population guarantee.','',
    'Training uses three fixed bank witnesses per seat from the old learned, response',
    'and equity groupings. Labels are the signs of conditional action advantages,',
    'with exact ties 0.5. The two predictors see identical training rows and labels.',
    'Both use 91 quadratic columns and the same ridge-logistic fit; conditioned',
    'receives bet/pot and blind masks that coordinate to zero. Each cell has equal',
    'weight, distributed by that seat\'s collision-conditioned hand marginal.',
    'All six binary outputs per predictor are fitted on training cells only.',
    'The candidate is written and hashed before any evaluation cell is opened.',
    'Model fitting is then disabled. No selection among models by holdout scores.','',
    'The old learned model has four outputs and older training targets. Therefore',
    'comparisons with it are whole-candidate comparisons. Only the matched blind',
    'ablation isolates exposing bet size within the new training setup.',
    'Adding bet size also adds effective polynomial terms; no equal-effective-',
    'parameter or equal-wall-time claim is made. All groupings match occupied',
    'capacity and use the unchanged anchored clustering algorithm. Oracle holdout',
    'witnesses supply neither predictor\'s features, coefficients or labels.','',
    '## Verification and retention','',
    'The initial bet-input test failed as intended against a blind scaffold.',
    'Eight model/data-boundary preflights, six existing BR tests and thirteen',
    'payoff/optimality tests passed. A temporary older-experiment import collision',
    'was caught by preflight and corrected before freeze; its failed receipt is',
    'retained. There was no scored-panel rehearsal.','',
    'The worker made 1280 LP calls and fitted 12 binary tasks. It retained 256',
    'solver trajectories with 768 checkpoints. The parent disabled LP, rebuilt',
    'training targets and verified all 1280 certificates, refitted all models',
    'exactly, then disabled fitting for fresh-board verification. It replayed',
    '12.8 million iterations from zero and independently checked every saved',
    'full-hand policy using scalar arithmetic. Blind features and group labels',
    'were identical across bet sizes. A separate Fraction audit rebuilt every',
    'panel, mean, certificate interval and frozen decision flag.',
    f"Maximum scalar discrepancy: {a['maximum_scalar_discrepancy']:.6e} chips.",
    f"Independent summary scalar checks: {sa['summary_scalar_checks']:,}.",
    f"Pinned files checked before and after: {len(p['pins'])}.",
    f"Worker: {worker['seconds']:.6f} s; verifier: {verifier['seconds']:.6f} s.",
    f"Combined invocation: {receipt['seconds']:.6f} s, exit 0.",
    'Python 3.14.6, NumPy 2.5.2, SciPy 1.18.0; one BLAS thread; no tracemalloc.',
    'Each subprocess had a 1200-second timeout. No RSS cap or peak-memory claim.',
    'All sixteen earlier milestones were verified and preserved. No independent',
    'cold review, production change, adoption, commit or push is claimed.','',
    'Plan SHA-256:',digest(OUT/'plan.json'),'',
    'Frozen trained candidate SHA-256:',digest(OUT/'candidate.json'),'',
    'Original result manifest SHA-256:',receipt['result_manifest_sha256'],'']
with REPORT.open('x',encoding='utf-8',newline='\n') as f:f.write('\n'.join(lines))
shutil.copytree(OUT,ARCHIVE)
(ARCHIVE/'verification-tools').mkdir()
for f in HERE.iterdir():
    if f.is_file() and f.name not in ('plan.json',):shutil.copyfile(f,ARCHIVE/'verification-tools'/f.name)
shutil.copyfile(REPORT,ARCHIVE/'report.md')
for f in OUT.iterdir():
    if f.is_file():assert digest(f)==digest(ARCHIVE/f.name)
members={f.relative_to(ARCHIVE).as_posix():digest(f) for f in sorted(ARCHIVE.rglob('*')) if f.is_file()}
write(ARCHIVE/'milestone-manifest.json',members)
for name,h in members.items():assert digest(ARCHIVE/name)==h,name
overview=ROOT/'docs/research/README.md'
with (HERE/'research-readme-before.md').open('xb') as f:f.write(overview.read_bytes())
with overview.open('ab') as f:
    f.write(b'\n## Bet-conditioned preference pilot\n\n'
        b'[Witness-bet-conditioned-001](river-witness-bet-conditioned-001.md) compares\n'
        b'bet-conditioned and blind predictors on eight fresh boards, with matched\n'
        b'best-response training, certified floors and exact-witness controls.\n')
assert subprocess.check_output(git+['rev-parse','HEAD'],text=True).strip()==before['head']
retention=dict(passed=True,milestone_members=len(members),milestone_sha256=digest(ARCHIVE/'milestone-manifest.json'),
    report_sha256=digest(REPORT),candidate_sha256=digest(ARCHIVE/'candidate.json'),prior_milestones=prior,
    source_head=before['head'],commit_performed=False,push_performed=False)
write(HERE/'retention.json',retention)
print(json.dumps(retention,indent=2))
