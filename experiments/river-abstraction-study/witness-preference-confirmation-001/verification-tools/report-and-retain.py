from collections import Counter
from fractions import Fraction as Q
from hashlib import sha256
import json
from pathlib import Path
import shutil

ROOT=Path('D:/Pontius-worktrees/eval-runner-consolidation')
HERE=Path(__file__).parent
OUT=Path('D:/Pontius-training/river-abstraction-study/witness-preference-confirmation-001')
ARCHIVE=ROOT/'experiments/river-abstraction-study/witness-preference-confirmation-001'
REPORT=ROOT/'docs/research/river-witness-preference-confirmation-001.md'
read=lambda p:json.loads(p.read_bytes())
digest=lambda p:sha256(p.read_bytes()).hexdigest()
mid=lambda v:float((Q(v['lower_exact'])+Q(v['upper_exact']))/2)

def write(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as f:
        f.write(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n')

p=read(OUT/'plan.json');s=read(OUT/'summary.json');audit=read(OUT/'audit.json')
receipt=read(OUT/'receipt.json');worker=read(OUT/'worker-receipt.json')
assert receipt['exit']==worker['exit']==0 and audit['passed'] is True
assert not ARCHIVE.exists() and not REPORT.exists()
assert digest(OUT/'results-manifest.json')==receipt['result_manifest_sha256']
for path,h in p['pins'].items():assert digest(Path(path))==h,path
for name,h in read(OUT/'results-manifest.json').items():assert digest(OUT/name)==h,name
rows=[read(OUT/(c['id']+'.json')) for c in p['cases']]
assert [r['case'] for r in rows]==p['cases']
def compact(a):
    return dict(floors={m:mid(v) for m,v in a['mean_floors'].items()},
        comparisons={m:dict(delta=mid(v),counts=v['counts']) for m,v in a['comparisons'].items()},
        seat_effects={m:{seat:dict(delta=mid(v),counts=v['counts']) for seat,v in ss.items()}
                      for m,ss in a['seat_effects'].items()})
worst=sorted(rows,key=lambda r:mid(r['comparisons']['range_response']),reverse=True)[:5]
a=dict(overall=compact(s['overall']),boards={b:compact(v) for b,v in s['boards'].items()},
    regimes={v:compact(x) for v,x in s['regimes'].items()},
    textures={v:compact(x) for v,x in s['textures'].items()},
    lobo={b:compact(v) for b,v in s['leave_one_board_out'].items()},
    directional_replication_pass=s['directional_replication_pass'],sensitivity_pass=s['sensitivity_pass'],
    worst_cases=[dict(case=r['case'],candidate=mid(r['floors']['ordinary_preference']),
                     reference=mid(r['floors']['range_response']),
                     delta=mid(r['comparisons']['range_response'])) for r in worst],
    stage_seconds=s['stage_seconds'],worker_seconds=worker['seconds'],
    worker_plus_parent_seconds=receipt['seconds'])
write(OUT/'analysis.json',a)
f=a['overall']['floors'];relative=100*(f['range_response']-f['ordinary_preference'])/f['range_response']
board_counts=Counter('lower' if Q(v['comparisons']['range_response']['upper_exact'])<0 else
    'higher' if Q(v['comparisons']['range_response']['lower_exact'])>0 else 'overlapping'
    for v in s['boards'].values())
lines=['# Frozen ordinary-preference confirmation: witness-preference-confirmation-001','',
    '## Result and scope','',
    'Directional replication: '+('PASS.' if s['directional_replication_pass'] else 'NOT PASSED.'),
    'Predeclared texture/leave-one-board-out sensitivity: '+('PASS.' if s['sensitivity_pass'] else 'NOT PASSED.'),
    f'The frozen candidate changes mean grouping floor by {-relative:.2f}% relative to range-response.',
    f"Board means: {board_counts.get('lower',0)} lower, {board_counts.get('higher',0)} higher, "
    f"{board_counts.get('overlapping',0)} overlapping.",
    'These labels apply to the predeclared numerical mean and sensitivity rules on this',
    'fresh panel. They do not state a statistical confidence level or grant adoption.',
    ('The development result replicates directionally on previously unscored boards.' if s['directional_replication_pass'] else
     'The development advantage did not replicate under the declared primary criterion.'),
    'Every selected case is retained; no alternate seed, additional sample or model',
    'adjustment was used. Report the heterogeneous outcomes below with the overall mean.','',
    '## Frozen design and new panel','',
    'The two ordinary-preference models are copied exactly from witness-preference-001.',
    'No coefficient, input feature, output rule or grouping rule changed. No model was',
    'trained or refitted in this confirmation. The candidate was fixed before selecting',
    'the new boards. All source, producer and plan digests were sealed before scoring.',
    'The fixed classifier was selected using the earlier development results; that',
    'selection is acknowledged, not treated as another independent result.','',
    'Sixteen new boards: four in each existing texture category, three fixed hand pools',
    'and two range regimes per board, giving 96 cases. Each game has 96 holdings per',
    'seat, pot 10, bet 5 and stacks 20/20. All 20 earlier study boards are excluded,',
    'including suit-isomorphic equivalents. Hash selection uses the fixed seed',
    "'witness-preference-confirmation-001' and first four accepted boards per texture.",
    'The exact selection attempts and exclusion list are in plan.json. No equity,',
    'prediction, payoff or score was computed during selection. No scoring rehearsal.',
    'Four methods receive two asymmetric solves each: exactly 768 LP calls.',
    'Range-response is the primary baseline, range-equity secondary, exact hands the',
    'numerical reference. Compressed methods match occupied capacity within each case.','',
    'The primary endpoint is the equal-board mean candidate-minus-range-response floor.',
    'Its upper numerical endpoint must be negative to pass directional replication.',
    'The separate sensitivity flag requires a negative upper endpoint in every texture',
    'mean and every leave-one-board-out mean. Both rules were frozen before scoring.',
    'There was no post-result effect-size threshold or favorable-subset selection.','',
    '## Mean grouping floors','',
    'Lower is better. These are certified interval midpoints for the least full-hand',
    'profile exploitability representable by the groups in the encoded one-bet game.',
    'Units are conditional game chips, not win rate or BB/100. Six cases are equally',
    'weighted within each board; all 16 boards and four texture strata have equal weight.','',
    '| Method | Mean floor |','|---|---:|']
for m,v in f.items():lines.append(f'| {m} | {v:.10f} |')
lines += ['', 'Delta is candidate minus reference. Counts are lower / higher / overlapping.','',
    '| Reference | Mean delta | Counts |','|---|---:|---:|']
def counts(v):return '/'.join(str(v['counts'].get(k,0)) for k in ('lower','higher','overlapping'))
for m,v in s['overall']['comparisons'].items():lines.append(f'| {m} | {mid(v):.10f} | {counts(v)} |')
lines += ['', '## Boards and textures','',
    '| Board index | Cards (encoded) | Candidate | Range-response | Delta |',
    '|---|---|---:|---:|---:|']
for b,v in sorted(a['boards'].items(),key=lambda item:int(item[0])):
    lines.append(f"| {b} | {p['boards'][int(b)]} | {v['floors']['ordinary_preference']:.9f} | "
        f"{v['floors']['range_response']:.9f} | {v['comparisons']['range_response']['delta']:.9f} |")
lines += ['', 'Card encoding is rank index times four plus suit index, as in the frozen code.',
    'The public-card lists are identities, not learned board labels.','',
    '| Texture | Candidate | Range-response | Delta | Case counts |','|---|---:|---:|---:|---:|']
for t,v in s['textures'].items():
    lines.append(f"| {t} | {mid(v['mean_floors']['ordinary_preference']):.9f} | "
        f"{mid(v['mean_floors']['range_response']):.9f} | {mid(v['comparisons']['range_response']):.9f} | "
        f"{counts(v['comparisons']['range_response'])} |")
lines += ['', '| Regime | Candidate | Range-response | Delta | Case counts |','|---|---:|---:|---:|---:|']
for regime,v in s['regimes'].items():
    lines.append(f"| {regime} | {mid(v['mean_floors']['ordinary_preference']):.9f} | "
        f"{mid(v['mean_floors']['range_response']):.9f} | {mid(v['comparisons']['range_response']):.9f} | "
        f"{counts(v['comparisons']['range_response'])} |")
lines += ['', 'The polarized generator keeps the same support and multiplies low/high uniform',
    'showdown-equity hand weights by four for both players, with collision conditioning.',
    'These are synthetic ranges, not posteriors reached through earlier betting.','',
    '## Seat contributions','',
    '| Reference | Bettor delta | Bettor counts | Caller delta | Caller counts |',
    '|---|---:|---:|---:|---:|']
for m,ss in s['overall']['seat_effects'].items():
    b,c=ss['bettor'],ss['caller']
    lines.append(f'| {m} | {mid(b):.10f} | {counts(b)} | {mid(c):.10f} | {counts(c)} |')
lines += ['', 'These are the changes in the separate constrained-seat values, with the other',
    'seat unrestricted. They add algebraically to the grouping-floor change, up to',
    'numerical interval handling. They are not results from playing two trained bots.','',
    '## Sensitivity and largest losses','',
    '| Omitted board | Candidate-minus-response mean |','|---|---:|']
for b,v in sorted(a['lobo'].items(),key=lambda item:int(item[0])):
    lines.append(f"| {b} | {v['comparisons']['range_response']['delta']:.10f} |")
lines += ['', 'All omitted-board panels are descriptive checks; none replaces the full panel.', '',
    '| Case | Candidate floor | Reference floor | Delta |','|---|---:|---:|---:|']
for r in a['worst_cases']:
    lines.append(f"| {r['case']['id']} | {r['candidate']:.9f} | {r['reference']:.9f} | {r['delta']:.9f} |")
lines += ['', '## Execution and verification','',
    f"Worker: {worker['seconds']:.6f} s; worker plus parent: {receipt['seconds']:.6f} s.",
    'The combined boundary spans launch through parent verification, scalar/rational',
    'audit and result-manifest writing, excluding preflight, reservation and final receipt.',
    'Python 3.14.6 / NumPy 2.5.2 / SciPy 1.18.0, one BLAS thread, no allocation tracing.',
    'Worker limit 600 s, parent outside it, no RSS cap or peak-memory measurement.',
    'One invocation completed with exit 0 and exactly 768 LP calls; zero model fits.', '',
    '| Worker stage (sum over 96 cases) | Seconds |','|---|---:|']
for stage,value in s['stage_seconds'].items():lines.append(f'| {stage} | {value:.6f} |')
lines += ['', 'Prediction timing begins with loaded coefficients and prepared raw features.',
    'Clustering timing begins with predictions and existing capacity. Neither is an',
    'end-to-end live decision benchmark; preparation includes cached board equity work.',
    'The solve stage includes the worker certificate checks. Parent checks are separate.', '',
    'The parent reconstructed every game, feature and group, verified all 768 asymmetric',
    'certificates with LP calls disabled, and confirmed exact frozen candidate identity.',
    'The independent audit re-derived board selection and suit exclusion, checked 73,728',
    'scalar probabilities, 884,736 collision-conditioned joint cells, 384 floor identities,',
    '288 signed comparisons, 576 seat effects and 1,131 aggregate records. It recomputed',
    'both predeclared result flags and added no LP calls or model fitting.',
    f"Maximum certificate width: {audit['maximum_certificate_gap']:.6e} chips.",
    f"All {len(p['pins'])} bound files verified again before retention.",
    'All full-hand reference intervals contain the mathematical zero grouping floor.',
    'Synthetic sigmoid, tie capacity, signed interval and suit-invariance checks passed.', '',
    'Freshness is relative to this study and its pinned exclusion list. Hash-selected,',
    'equally stratified boards are not weighted by real-game reach. Numerical certificates',
    'bound solver error on binary64 payoffs, not population sampling uncertainty. No',
    'formal confidence level, independent card evaluator, cold opposing review, full-pool',
    'coverage, full-game improvement or six-max strength is claimed.', '',
    'Original output: D:/Pontius-training/river-abstraction-study/witness-preference-confirmation-001',
    'Archive: experiments/river-abstraction-study/witness-preference-confirmation-001',
    'All twelve prior milestones preserved. No production change, commit, push or adoption.', '',
    'Frozen candidate SHA-256:',p['candidate_sha256'],'',
    'Plan SHA-256:',digest(OUT/'plan.json'),'',
    'Original result manifest SHA-256:',receipt['result_manifest_sha256'],'']
with REPORT.open('x',encoding='utf-8',newline='\n') as f:f.write('\n'.join(lines))
shutil.copytree(OUT,ARCHIVE);(ARCHIVE/'verification-tools').mkdir()
for name in ('design.md','experiment.py','audit.py','prepare.py','report-and-retain.py'):
    shutil.copyfile(HERE/name,ARCHIVE/'verification-tools'/name)
shutil.copyfile(REPORT,ARCHIVE/'report.md')
for file in OUT.iterdir():
    if file.is_file():assert digest(file)==digest(ARCHIVE/file.name)
members={file.relative_to(ARCHIVE).as_posix():digest(file) for file in sorted(ARCHIVE.rglob('*')) if file.is_file()}
write(ARCHIVE/'milestone-manifest.json',members)
for name,h in members.items():assert digest(ARCHIVE/name)==h,name
prior={}
for name in ('development-001','holdout-001','group-optimality-001','witness-groups-development-001',
    'witness-pilot-001','witness-distillation-001','witness-fit-diagnostic-001','witness-hybrid-001',
    'witness-boundary-001','witness-clipped-target-001','witness-seat-crossover-001','witness-preference-001'):
    directory=ROOT/'experiments/river-abstraction-study'/name
    for member,h in read(directory/'milestone-manifest.json').items():
        assert digest(directory/member)==h,(name,member)
    prior[name]=digest(directory/'milestone-manifest.json')
overview=ROOT/'docs/research/README.md'
with (HERE/'research-readme-before.md').open('xb') as f:f.write(overview.read_bytes())
with overview.open('ab') as f:
    f.write(b'\n## Frozen ordinary-preference confirmation\n\n'
        b'[Witness-preference-confirmation-001](river-witness-preference-confirmation-001.md)\n'
        b'evaluates the unchanged classifier on 16 fresh boards, with fixed directional\n'
        b'and sensitivity criteria, no retraining, and all 96 cases retained.\n')
record=dict(passed=True,milestone_members=len(members),
    milestone_sha256=digest(ARCHIVE/'milestone-manifest.json'),report_sha256=digest(REPORT),
    prior_milestones=prior,commit_performed=False,push_performed=False)
write(HERE/'retention.json',record);print(json.dumps(record,indent=2))
