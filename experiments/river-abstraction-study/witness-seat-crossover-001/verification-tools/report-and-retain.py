from fractions import Fraction as Q
from hashlib import sha256
import json
from pathlib import Path
import shutil

ROOT=Path('D:/Pontius-worktrees/eval-runner-consolidation')
HERE=Path(__file__).parent
OUT=Path('D:/Pontius-training/river-abstraction-study/witness-seat-crossover-001')
ARCHIVE=ROOT/'experiments/river-abstraction-study/witness-seat-crossover-001'
REPORT=ROOT/'docs/research/river-witness-seat-crossover-001.md'
read=lambda p:json.loads(p.read_bytes())
digest=lambda p:sha256(p.read_bytes()).hexdigest()
mid=lambda v:float((Q(v['lower_exact'])+Q(v['upper_exact']))/2)

def write(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as f:
        f.write(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n')

plan=read(OUT/'plan.json');s=read(OUT/'summary.json');audit=read(OUT/'audit.json')
receipt=read(OUT/'receipt.json');worker=read(OUT/'worker-receipt.json')
assert receipt['exit']==worker['exit']==0 and audit['passed'] is True
assert audit['crossed_floor_identities']==192 and audit['aggregate_records']==1222
assert not ARCHIVE.exists() and not REPORT.exists()
assert digest(OUT/'results-manifest.json')==receipt['result_manifest_sha256']
for path,h in plan['pins'].items():assert digest(Path(path))==h,path
for name,h in read(OUT/'results-manifest.json').items():assert digest(OUT/name)==h,name
rows=[read(OUT/(case['id']+'.json')) for case in plan['cases']]
assert [r['case'] for r in rows]==plan['cases']
def compact(a):
    return dict(floors={k:mid(v) for k,v in a['floors'].items()},
        effects={k:dict(delta=mid(v),counts=v['counts']) for k,v in a['effects'].items()},
        comparisons={arm:{ref:dict(delta=mid(v),counts=v['counts']) for ref,v in cs.items()}
                     for arm,cs in a['comparisons'].items()})
analysis=dict(overall=compact(s['overall']),boards={k:compact(v) for k,v in s['boards'].items()},
    regimes={k:compact(v) for k,v in s['regimes'].items()},
    lobo={k:compact(v) for k,v in s['leave_one_board_out'].items()},
    paired_regime_effects={k:dict(delta=mid(v),counts=v['counts'])
                         for k,v in s['paired_regime_effects']['overall'].items()},
    preidentified={r['case']['id']:dict(floors={k:mid(v) for k,v in r['floors'].items()},
                   effects={k:mid(v) for k,v in r['effects'].items()}) for r in rows
                  if r['case']['id'] in ('b07-p1-polarized','b07-p2-polarized')},range_mass={})
for regime in ('uniform','polarized'):
    selected=[r for r in rows if r['case']['regime']==regime]
    analysis['range_mass'][regime]=[dict(
        prior_tail=sum(r['range_mass'][seat]['prior']['low']+
                       r['range_mass'][seat]['prior']['high'] for r in selected)/24,
        conditioned_tail=sum(r['range_mass'][seat]['conditioned']['low']+
                             r['range_mass'][seat]['conditioned']['high'] for r in selected)/24)
        for seat in (0,1)]
write(OUT/'analysis.json',analysis)
f=analysis['overall']['floors']
relative=100*(f['range_response']-f['new_old'])/f['range_response']
versus_old=100*(f['old_old']-f['new_old'])/f['old_old']
lines=['# Seat crossover and range-shape diagnostic: witness-seat-crossover-001','',
    '## Result and research decision','',
    'The two severe failures repaired in the last experiment were predominantly bettor',
    'grouping failures. Swapping only the bettor to the clipped-target model produces',
    'nearly all of both repairs. The caller change improves one slightly and worsens',
    'the other. Across the full panel, the bettor swap reduces mean floor, while the',
    'caller swap raises it. This runs opposite to the preceding squared prediction-error',
    'comparison: bettor MSE worsened and caller MSE improved. Prediction accuracy and',
    'strategic grouping quality must be measured separately.','',
    f'New bettor plus old caller has the best mean among the four fixed arms: {relative:.2f}%',
    f'below range-response and {versus_old:.2f}% below old/old. Against range-response it',
    'improves 30 cases, worsens 17 and overlaps one. Seven board means improve, but',
    'five of eight leave-one-board-out comparisons reverse its overall advantage.',
    'Against old/old it improves only three cases, worsens 34 and overlaps 11; seven',
    'board means worsen. Removing board 7 reverses that mean advantage. Keep this as',
    'a diagnostic candidate; do not adopt it as an established improvement.','',
    'The synthetic range-shape intervention changes the response to the target change.',
    'Both seat swaps improve the polarized-regime mean and worsen the uniform-regime',
    'mean. However, the bettor improves just two polarized cases and the caller eight.',
    'The average effect must not be read as broad case-by-case success. No causal',
    'claim about natural street progression or polarizing either player alone follows.','',
    '## Fixed comparison and estimand','',
    'Old = the original quadratic model trained on full targets, with output clipped.',
    'New = the same model recipe trained on clipped targets, with output clipped.',
    'Arm order is bettor (seat 0), caller (seat 1). All four combinations were declared',
    'before execution. Groups, models and witnesses are reused unchanged; each seat',
    'retains the original occupied capacity. No case-specific choice of model is made.',
    'All 48 observed cases remain: eight equal-weight boards x three pools x two regimes,',
    '96 holdings per seat. No new boards, target changes, fits or optimization calls.','',
    'With a(G0)=max_XG0 min_Y V and b(G1)=min_YG1 max_X V, the smallest representable',
    'full-hand profile exploitability is E*=[b(G1)-a(G0)]/2. Thus the existing asymmetric',
    'certificates can be crossed. The bettor effect is [a_old-a_new]/2 and the caller',
    'effect [b_new-b_old]/2. They add by construction; this is not a measured discovery',
    'of absent player interaction. The result is specific to the fixed two-player',
    'zero-sum game and its product policy classes. Crossed policies need not form an',
    'equilibrium of the doubly compressed game. The actual model is used to construct',
    'groups; the reported floor benchmarks the best policies those groups can represent.','',
    '## Mean grouping floors','',
    'Lower is better. Values are certified interval midpoints in conditional game chips.',
    'They are not win rates, BB/100 or full-game/six-max strength measurements.','',
    '| Bettor model | Caller model | Mean floor |','|---|---|---:|']
for arm in ('old_old','new_old','old_new','new_new'):
    x,y=arm.split('_');lines.append(f'| {x} | {y} | {f[arm]:.10f} |')
lines += [f"| Range-response baseline | Both seats | {f['range_response']:.10f} |",
          f"| Range-equity baseline | Both seats | {f['range_equity']:.10f} |",
          f"| Clipped exact witness oracle | Both seats | {f['clipped_oracle']:.10f} |",'',
    '## Seat effects','',
    'Negative favors changing the indicated seat to the new model. Counts are lower /',
    'higher / overlapping, using signed certificate intervals with shared values canceled.','',
    '| Regime | Bettor delta | Bettor counts | Caller delta | Caller counts |',
    '|---|---:|---:|---:|---:|']
def counts(v):return '/'.join(str(v['counts'].get(k,0)) for k in ('lower','higher','overlapping'))
for regime,data in [('all',s['overall']),*s['regimes'].items()]:
    b,c=data['effects']['bettor'],data['effects']['caller']
    lines.append(f'| {regime} | {mid(b):.10f} | {counts(b)} | {mid(c):.10f} | {counts(c)} |')
lines += ['', 'The 24 matched regime pairs use identical boards and hand pools. The following',
    'contrast is polarized-minus-uniform in the effect of swapping a model. It is not',
    'the raw polarized-minus-uniform floor difference.','',
    '| Model swap | Mean difference in effects | Lower / higher / overlapping |',
    '|---|---:|---:|']
for k,v in s['paired_regime_effects']['overall'].items():
    lines.append(f'| {k} | {mid(v):.10f} | {counts(v)} |')
lines += ['', '| Regime | Old/old | New/old | Old/new | New/new | Range-response |',
    '|---|---:|---:|---:|---:|---:|']
for k,v in analysis['regimes'].items():
    lines.append('| '+k+' | '+' | '.join(f"{v['floors'][m]:.9f}" for m in
        ('old_old','new_old','old_new','new_new','range_response'))+' |')
lines += ['', '## Preidentified severe cases','',
    '| Case | Old/old | New bettor only | New caller only | Both new |',
    '|---|---:|---:|---:|---:|']
for k,v in analysis['preidentified'].items():
    lines.append('| '+k+' | '+' | '.join(f"{v['floors'][m]:.9f}" for m in
        ('old_old','new_old','old_new','new_new'))+' |')
lines += ['', 'Both cases use board 6h 6s Jh Qc Qd and polarized ranges. They stay included.', '',
    '## Board sensitivity','',
    '| Board | Old/old | New/old | Old/new | New/new | Range-response |',
    '|---|---:|---:|---:|---:|---:|']
for k,v in analysis['boards'].items():
    lines.append('| '+k+' | '+' | '.join(f"{v['floors'][m]:.9f}" for m in
        ('old_old','new_old','old_new','new_new','range_response'))+' |')
lines += ['', '| Omitted board | New/old minus old/old | New/old minus range-response |',
    '|---|---:|---:|']
for k,v in analysis['lobo'].items():
    cs=v['comparisons']['new_old']
    lines.append(f"| {k} | {cs['old_old']['delta']:.10f} | {cs['range_response']['delta']:.10f} |")
lines += ['', 'These are descriptive sensitivity checks, not confidence intervals. The main',
    'result omits nothing. All arm/reference comparisons and board/pool/texture strata',
    'are in summary.json. None of the four arms constitutes fresh holdout evidence.', '',
    '## What the range intervention actually changes','',
    'For each seat, the retained generator assigns weight four to hands with uniform',
    'showdown equity <=0.2 or >=0.8 and weight one elsewhere. Uniform mode assigns',
    'weight one everywhere. The same hand support is preserved. Joint deals reject',
    'collisions and normalize; card removal therefore changes the effective marginals.',
    'This is a synthetic two-sided reweighting, not a range inferred from prior actions.', '',
    '| Regime | Seat | Prior low+high mass | Collision-conditioned low+high mass |',
    '|---|---:|---:|---:|']
for regime,seats in analysis['range_mass'].items():
    for seat,r in enumerate(seats):
        lines.append(f"| {regime} | {seat} | {r['prior_tail']:.6f} | {r['conditioned_tail']:.6f} |")
lines += ['', 'These average the 24 cases per regime. Per-case low/middle/high counts, weights',
    'and masses are retained. Both players change at once, along with the features and',
    'groupings derived from those ranges. The design cannot isolate own-range changes',
    'from opponent-range changes, nor establish that later-street ranges behave this way.', '',
    '## Verification and retention','',
    f"Worker: {worker['seconds']:.6f} s; worker plus parent: {receipt['seconds']:.6f} s.",
    'The latter spans worker launch, parent arithmetic audit and result-manifest writing;',
    'it excludes preflight, output reservation and final receipt writing. Python 3.14.6,',
    'NumPy 2.5.2, SciPy 1.18.0, one BLAS thread. Worker limit 600 s, parent outside it.',
    'No RSS cap or peak-memory claim. One invocation completed, exit 0. No retry.', '',
    'The worker rebuilt all 48 games and matched retained inputs, then freshly verified',
    '192 asymmetric payoff certificates. Fitting and optimization entry points were',
    'disabled; no attempts occurred. The separate audit imported no worker functions',
    'and checked 192 crossed floors, 912 signed case contrasts, 1,222 aggregate records,',
    '24 matched regime pairs and 576 range-mass values against original inputs.',
    'Old/old and new/new exactly reproduce prior floor records. Full crossed group',
    'vectors and constrained policies are saved with their seat provenance.',
    f"Maximum inherited certificate width: {audit['max_original_certificate_gap']:.6e} chips.",
    'Certificates apply to the encoded binary64 payoff matrices. This is not a separate',
    'card-evaluator implementation, cold opposing review, or board-population uncertainty',
    'bound. Synthetic arithmetic/cancellation/feasibility checks passed before freezing.',
    f"All {len(plan['pins'])} bound input files verified again before retention.", '',
    'Original output: D:/Pontius-training/river-abstraction-study/witness-seat-crossover-001',
    'Archive: experiments/river-abstraction-study/witness-seat-crossover-001',
    'All ten earlier milestones preserved. No production changes, commit, push or adoption.', '',
    'Plan SHA-256:',digest(OUT/'plan.json'),'',
    'Original result manifest SHA-256:',receipt['result_manifest_sha256'],'']
with REPORT.open('x',encoding='utf-8',newline='\n') as f:f.write('\n'.join(lines))
shutil.copytree(OUT,ARCHIVE)
(ARCHIVE/'verification-tools').mkdir()
for name in ('design.md','experiment.py','audit.py','prepare.py','report-and-retain.py'):
    shutil.copyfile(HERE/name,ARCHIVE/'verification-tools'/name)
shutil.copyfile(REPORT,ARCHIVE/'report.md')
for p in OUT.iterdir():
    if p.is_file():assert digest(p)==digest(ARCHIVE/p.name)
members={p.relative_to(ARCHIVE).as_posix():digest(p) for p in sorted(ARCHIVE.rglob('*')) if p.is_file()}
write(ARCHIVE/'milestone-manifest.json',members)
for name,h in members.items():assert digest(ARCHIVE/name)==h,name
prior={}
for name in ('development-001','holdout-001','group-optimality-001','witness-groups-development-001',
    'witness-pilot-001','witness-distillation-001','witness-fit-diagnostic-001',
    'witness-hybrid-001','witness-boundary-001','witness-clipped-target-001'):
    directory=ROOT/'experiments/river-abstraction-study'/name
    for member,h in read(directory/'milestone-manifest.json').items():
        assert digest(directory/member)==h,(name,member)
    prior[name]=digest(directory/'milestone-manifest.json')
overview=ROOT/'docs/research/README.md'
with (HERE/'research-readme-before.md').open('xb') as f:f.write(overview.read_bytes())
with overview.open('ab') as f:
    f.write(b'\n## Seat crossover and range-shape diagnostic\n\n'
        b'[Witness-seat-crossover-001](river-witness-seat-crossover-001.md) crosses the\n'
        b'old and new seat models without fitting or optimization. It locates the large\n'
        b'repairs in the bettor grouping and retains all range and board sensitivity.\n')
record=dict(passed=True,milestone_members=len(members),
    milestone_sha256=digest(ARCHIVE/'milestone-manifest.json'),report_sha256=digest(REPORT),
    prior_milestones=prior,commit_performed=False,push_performed=False)
write(HERE/'retention.json',record)
print(json.dumps(record,indent=2))
