"""Preserve the diagnostic, including negative outcomes, without changing prior milestones."""
from collections import Counter
from fractions import Fraction as Q
from hashlib import sha256
import json
from math import fsum
from pathlib import Path
import shutil
import subprocess

ROOT=Path('D:/Pontius-worktrees/eval-runner-consolidation')
HERE=Path(__file__).parent
NAME='witness-order-diagnostic-001'
OUT=Path('D:/Pontius-training/river-abstraction-study')/NAME
ARCHIVE=ROOT/'experiments/river-abstraction-study'/NAME
REPORT=ROOT/'docs/research/river-witness-order-diagnostic-001.md'
PRIOR=ARCHIVE.parent/'witness-ordinal-001'
read=lambda p:json.loads(p.read_bytes())
digest=lambda p:sha256(p.read_bytes()).hexdigest()
mid=lambda v:float((Q(v['lower_exact'])+Q(v['upper_exact']))/2)
def write(p,v):
    with p.open('x',encoding='utf-8',newline='\n') as f:
        f.write(json.dumps(v,sort_keys=True,indent=2,allow_nan=False)+'\n')
def direction(v):return 'lower' if v < -1e-10 else 'higher' if v > 1e-10 else 'overlapping'
def counts(values):return dict(Counter(map(direction,values)))

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
assert len(prior)==18

# Independent scalar diagnostic accumulation, outside the executable freeze.
diagnostic_checks=0;maximum=0.;partition_counts={str(b):Counter() for b in (5,10)}
for case in p['evaluation_cases']:
    for bet in p['bets']:
        name=f"eval-{case['id']}-bet-{bet}.json"
        row=read(OUT/name);old=read(PRIOR/name)
        x=old['proposal']['features']['ordinal'][1];y=row['caller_features']
        weights=old['witness'][1]['weights']
        g=old['proposal']['groups']['ordinal'][1];h=row['groups'][1]
        same=all((g[i]==g[j])==(h[i]==h[j]) for i in range(len(g)) for j in range(len(g)))
        partition_counts[str(bet)]['identical' if same else 'changed']+=1
        cross=lambda f:fsum(weights[i]*sum(any(f[i][j+k+1]>f[i][j+k]+1e-12
                for k in (0,1)) for j in (0,3,6))/3 for i in range(len(f)))
        expected=dict(crossing_before=cross(x),crossing_after=cross(y),
            changed_hand_mass=fsum(w for w,src,dst in zip(weights,x,y) if src!=dst),
            zero_head_mean_absolute_shift=fsum(w*fsum(abs(dst[j]-src[j]) for j in (1,4,7))/3
                for w,src,dst in zip(weights,x,y)),
            weighted_squared_distance=fsum(w*fsum((v-u)**2 for u,v in zip(src,dst))
                for w,src,dst in zip(weights,x,y)),
            changed_comembership_mass=fsum(weights[i]*weights[j] for i in range(len(g))
                for j in range(len(g)) if (g[i]==g[j])!=(h[i]==h[j])))
        for k,v in expected.items():
            error=abs(v-row['diagnostic'][k]);maximum=max(maximum,error)
            assert error<1e-12,(name,k,v,row['diagnostic'][k]);diagnostic_checks+=1
write(OUT/'diagnostic-audit.json',dict(passed=True,scalar_checks=diagnostic_checks,
    maximum_discrepancy=maximum,scope='post-run independent scalar diagnostics; no solver execution'))

analysis={}
refs=('ordinal','sign_conditioned','ordinary_preference','range_response')
for bet,panel in s['panels'].items():
    v=panel['overall'];new=v['actual']['caller_projected']
    analysis[bet]=dict(actual_reductions_percent={m:100*(v['actual'][m]-new)/v['actual'][m] for m in refs},
        caller_partition_cells=dict(partition_counts[bet]),
        floor_reductions_percent={m:100*(mid(v['floors'][m])-mid(v['floors']['caller_projected']))/mid(v['floors'][m]) for m in refs},
        board_directions={m:counts([x['comparisons'][m]['actual_delta'] for x in panel['boards'].values()]) for m in refs},
        leave_one_board_out_directions={m:counts([x['comparisons'][m]['actual_delta'] for x in panel['leave_one_board_out'].values()]) for m in refs},
        floor_exceeds_reference_actual={m:float(Q(v['floors']['caller_projected']['lower_exact']))>v['actual'][m]+1e-10 for m in refs})
write(OUT/'analysis.json',analysis)

lines=['# Caller threshold-order diagnostic 001','',
    'Completed with the frozen design. This is a no-refit intervention on the',
    'previously observed ordinal-001 panel, not a new-board confirmation.','',
    'The intervention projects only caller threshold probabilities into their',
    'required ordering. Bettor groups, trained coefficients, group counts, game',
    'inputs and solver budgets remain fixed. No production strategy was adopted.','',
    ('The primary mechanism test passed: caller projection improved both actual'
     if s['flags']['primary_mechanism_support'] else
     'The primary mechanism test did not pass. Correcting the probability order'),
    ('and representable half-pot scores on this observed panel.'
     if s['flags']['primary_mechanism_support'] else
     'did not deliver the required half-pot score and representation improvements.'),'',
    '## Predeclared decisions','',
    '| Diagnostic flag | Passed |','|---|---|']
for name,value in s['flags'].items():lines.append(f'| {name} | {value} |')
lines += ['',
    'Primary mechanism support requires lower half-pot actual exploitability and',
    'a strictly negative certified floor-difference upper bound versus ordinal.',
    'Practical recovery additionally requires those improvements versus both',
    'sign_conditioned and ordinary_preference. Pot non-regression uses 1e-10 chip',
    'tolerance on actual and certified floor upper difference against ordinal.',
    'These are descriptive diagnostic gates, not statistical significance tests.','',
    '## Matched 50,000-update results','',
    'Values are exploitability in chips; lower is better. Means weight cells',
    'equally within each bet panel. The certified floor is the best representable',
    'profile in these groups; its exact interval is retained in summary.json.','',
    '| Bet | Method | Actual exploitability | Floor midpoint |',
    '|---|---|---:|---:|']
for bet,panel in s['panels'].items():
    v=panel['overall']
    for m in ('caller_projected',*refs):
        lines.append(f"| {bet} | {m} | {v['actual'][m]:.10f} | {mid(v['floors'][m]):.10f} |")
lines += ['', 'Positive reduction percentages mean improvement; negative means worse.','',
    '| Bet | Reference | Actual reduction % | Floor reduction % | Board lower/higher/equal |',
    '|---|---|---:|---:|---|']
for bet,v in analysis.items():
    for m in refs:
        n=v['board_directions'][m]
        count='/'.join(str(n.get(k,0)) for k in ('lower','higher','overlapping'))
        lines.append(f"| {bet} | {m} | {v['actual_reductions_percent'][m]:.6f} | "
            f"{v['floor_reductions_percent'][m]:.6f} | {count} |")
lines += ['', '## Intervention diagnostics','',
    'Crossing mass is averaged across three witnesses under the caller marginal.',
    'Changed-hand mass counts any probability change. Co-membership mass is the',
    'caller-marginal-product mass of pairs whose shared-group status changes.',
    'It is independent of arbitrary group labels. Zero-head shift is the mean',
    'absolute change across the three zero-threshold heads.','',
    '| Bet | Crossing before | Crossing after | Changed hands | Zero-head shift | Pair change |',
    '|---|---:|---:|---:|---:|---:|']
for bet,panel in s['panels'].items():
    d=panel['overall']['diagnostics']
    lines.append(f"| {bet} | {d['crossing_before']:.10f} | {d['crossing_after']:.10f} | "
        f"{d['changed_hand_mass']:.10f} | {d['zero_head_mean_absolute_shift']:.10f} | "
        f"{d['changed_comembership_mass']:.10f} |")
for bet,v in analysis.items():
    counts=v['caller_partition_cells']
    lines += ['',f"Bet {bet}: {counts.get('identical',0)}/32 caller partitions unchanged; "
        f"{counts.get('changed',0)}/32 changed, comparing pair membership rather than labels."]
lines += ['', '## Sensitivity panels','',
    'All predeclared panels follow. Deltas are caller_projected minus reference;',
    'negative is better. Each leave-one-board-out row omits one whole board.',
    'Bounds below are displayed rounded; exact rational endpoints are in JSON.']
for category in ('checkpoints','boards','textures','regimes','leave_one_board_out'):
    lines += ['', '### '+category,'',
        '| Bet | Panel | Reference | Actual delta | Floor lower | Floor upper |',
        '|---|---|---|---:|---:|---:|']
    for bet,panel in s['panels'].items():
        for label,v in panel[category].items():
            for m in refs:
                c=v['comparisons'][m];lo=float(Q(c['floor_delta']['lower_exact']))
                hi=float(Q(c['floor_delta']['upper_exact']))
                lines.append(f"| {bet} | {label} | {m} | {c['actual_delta']:.10f} | {lo:.10f} | {hi:.10f} |")
lines += ['', '## Design and verification','',
    'All 64 prior evaluation cells are included: eight boards, two pools, two',
    'regimes, and two bet sizes (5 and 10 chips). Games have 96 holdings per seat,',
    'pot 10, stacks 20/20, a single heads-up bet and no raises. Outcomes and best',
    'responses are enumerated within those games, with no match-sampling noise.',
    'The eight boards are the board-level units. This is not population evidence',
    'or evidence of general-purpose six-max strength.','',
    'PAVA uses equal Euclidean weight for the three probabilities within each',
    'witness and no fitted parameters. The original ordinal bettor is unchanged.',
    'Frozen coefficients and raw inputs reproduce prior inference bit for bit.',
    'The projected caller is clustered by the preserved weighted anchored rule;',
    'both occupied group counts are checked. Projection can change the zero head.',
    'No search over thresholds, repair methods or selected favorable cells.','',
    'Five preflight tests pass, including exhaustive-partition comparisons on',
    '1,125 triplets. The retained identity scaffold fails four tests as expected.',
    'The scored panel was not rehearsed. The parent independently checked all',
    '18,432 evaluated caller triplets by enumerating equality partitions.','',
    '128 new LP calls, zero fits, 64 new trajectories and 192 new checkpoints.',
    'The separate parent verifier forbids LP and fitting, reconstructs the game',
    'inputs and source provenance, checks 640 certificates (128 new, 512 retained),',
    'and replays every new trajectory from zero: 3.2 million iterations. It checks',
    '960 checkpoint scores including all four retained references. Every new',
    'bettor policy is bit-identical to ordinal at every retained checkpoint.',
    f"Maximum independent scalar score discrepancy: {a['maximum_scalar_discrepancy']:.6e} chips.",
    f"Independent rational summary checks: {sa['rational_summary_checks']:,}.",
    f"Independent scalar intervention diagnostic checks: {diagnostic_checks}.",
    f"Source and artifact pins checked before and after: {len(p['pins'])}.",
    f"Worker {worker['seconds']:.6f} s; verifier {verifier['seconds']:.6f} s.",
    f"Combined invocation {receipt['seconds']:.6f} s, exit 0.",
    'Python 3.14.6, NumPy 2.5.2, SciPy 1.18.0; single BLAS thread, no tracemalloc.',
    'Each phase has a 900-second timeout. No RSS cap or measured-memory claim.',
    'All eighteen preceding milestones and pre-existing tracked edits are',
    'preserved; only the research index gains an entry. No source change,',
    'adoption, commit, push or independent cold review.','',
    'Plan SHA-256:',digest(OUT/'plan.json'),'',
    'Frozen predecessor model SHA-256:',digest(PRIOR/'candidate.json'),'',
    'Original results manifest SHA-256:',receipt['result_manifest_sha256'],'']
with REPORT.open('x',encoding='utf-8',newline='\n') as f:f.write('\n'.join(lines))
shutil.copytree(OUT,ARCHIVE);(ARCHIVE/'verification-tools').mkdir()
for path in HERE.iterdir():
    if path.is_file() and path.name!='plan.json':shutil.copyfile(path,ARCHIVE/'verification-tools'/path.name)
shutil.copyfile(REPORT,ARCHIVE/'report.md')
for path in OUT.iterdir():
    if path.is_file():assert digest(path)==digest(ARCHIVE/path.name)
members={path.relative_to(ARCHIVE).as_posix():digest(path) for path in sorted(ARCHIVE.rglob('*')) if path.is_file()}
write(ARCHIVE/'milestone-manifest.json',members)
for name,h in members.items():assert digest(ARCHIVE/name)==h,name
overview=ROOT/'docs/research/README.md'
with (HERE/'research-readme-before.md').open('xb') as f:f.write(overview.read_bytes())
with overview.open('ab') as f:
    f.write(b'\n## Caller threshold-order diagnostic\n\n'
        b'[Witness-order-diagnostic-001](river-witness-order-diagnostic-001.md) isolates\n'
        b'caller probability-order projection on the observed ordinal panel, with\n'
        b'unchanged coefficients, group counts, bettor and solver budgets.\n')
assert subprocess.check_output(git+['rev-parse','HEAD'],text=True).strip()==before['head']
record=dict(passed=True,milestone_members=len(members),milestone_sha256=digest(ARCHIVE/'milestone-manifest.json'),
    report_sha256=digest(REPORT),prior_milestones=prior,source_head=before['head'],
    commit_performed=False,push_performed=False)
write(HERE/'retention.json',record);print(json.dumps(record,indent=2))
