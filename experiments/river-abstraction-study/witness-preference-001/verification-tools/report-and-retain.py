from fractions import Fraction as Q
from hashlib import sha256
import json
from pathlib import Path
import shutil

ROOT=Path('D:/Pontius-worktrees/eval-runner-consolidation')
HERE=Path(__file__).parent
OUT=Path('D:/Pontius-training/river-abstraction-study/witness-preference-001')
ARCHIVE=ROOT/'experiments/river-abstraction-study/witness-preference-001'
REPORT=ROOT/'docs/research/river-witness-preference-001.md'
read=lambda p:json.loads(p.read_bytes())
digest=lambda p:sha256(p.read_bytes()).hexdigest()
mid=lambda v:float((Q(v['lower_exact'])+Q(v['upper_exact']))/2)

def write(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as f:
        f.write(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n')

plan=read(OUT/'plan.json');s=read(OUT/'summary.json');audit=read(OUT/'audit.json')
receipt=read(OUT/'receipt.json');worker=read(OUT/'worker-receipt.json');fit=read(OUT/'training.json')
assert receipt['exit']==worker['exit']==0 and audit['passed'] is True
assert not ARCHIVE.exists() and not REPORT.exists()
assert digest(OUT/'results-manifest.json')==receipt['result_manifest_sha256']
for path,h in plan['pins'].items():assert digest(Path(path))==h,path
for name,h in read(OUT/'results-manifest.json').items():assert digest(OUT/name)==h,name
rows=[read(OUT/(case['id']+'.json')) for case in plan['cases']]
def compact(a):
    return dict(floors={m:mid(v) for m,v in a['mean_floors'].items()},
        comparisons={m:{r:dict(delta=mid(v),counts=v['counts']) for r,v in cs.items()}
                     for m,cs in a['comparisons'].items()},
        seat_effects={m:{p:dict(delta=mid(v),counts=v['counts']) for p,v in seats.items()}
                      for m,seats in a['seat_effects'].items()})
a=dict(overall=compact(s['overall']),boards={k:compact(v) for k,v in s['boards'].items()},
    regimes={k:compact(v) for k,v in s['regimes'].items()},
    lobo={k:compact(v) for k,v in s['leave_one_board_out'].items()},
    expected_wrong_action_cost=audit['expected_wrong_action_cost'],
    preidentified={r['case']['id']:{m:mid(v) for m,v in r['floors'].items()} for r in rows
                  if r['case']['id'] in ('b07-p1-polarized','b07-p2-polarized')})
write(OUT/'analysis.json',a)
lines=['# Action-preference learning: witness-preference-001','',
    '## Result and research decision','',
    'Ordinary action-preference classification is a promising learned representation on',
    'this observed panel. Its mean grouping floor is 30.65% below range-response, with',
    '39 cases lower, eight higher and one overlapping. All eight board means improve,',
    'and every leave-one-board-out mean remains favorable. It also outperforms the',
    'previous mixed-model candidate in mean. Both seats contribute similar mean gains',
    'against range-response. This merits freezing a candidate for fresh-board confirmation;',
    'it is not confirmation already obtained or permission to adopt a playing policy.','',
    'The primary weighting hypothesis is not supported here: cost-weighted classification',
    'has a 13.42% higher mean floor than ordinary classification (22 lower cases, 23 higher,',
    'three overlapping). It is nevertheless 21.35% below range-response. Weighting helps',
    'the caller but hurts the bettor more. Removing board 7 narrowly reverses the mean',
    'weighted-versus-ordinary comparison; that board is retained in every main result.',
    'This finding applies to the specified weighting rule and model, not every form of',
    'decision-focused learning. No parameter was tuned after examining these outcomes.','',
    'Exact teacher preferences beat range-response in mean but are markedly worse than',
    'clipped exact advantage features. Sign information is useful, but this representation',
    'discards magnitude. The exact-preference arm is a privileged reference, not a bound',
    'on learned grouping quality: learned probabilities are continuous, the teacher is',
    'hard 0/1/.5, and clustering is not globally optimal. Ordinary classification beats',
    'the exact-preference grouping in nine cases. That does not contradict its identity.','',
    '## Fixed design','',
    'Original 48 training cases; all 48 already observed evaluation cases, eight boards',
    'x three pools x two range regimes, with 96 holdings per seat. No new boards, case',
    'selection, hyperparameter sweep or control re-solving. The learned variants use',
    'the same eleven inputs and 78-column quadratic basis, four sigmoid outputs per',
    'seat, lambda=.001 and unpenalized intercept. Their outputs feed unchanged anchored',
    'clustering with the original occupied capacities. Exact teacher preferences use',
    'one for positive advantage, zero for negative and .5 for an exact tie. All three',
    'arms are evaluated through 288 new asymmetric LP calls.','',
    'Both classifiers minimize binary cross entropy plus lambda/2 times squared slopes.',
    'Ordinary loss uses normalized own-hand mass and equal base case weights. Weighted',
    'loss multiplies that mass by absolute FULL, UNCLIPPED witness advantage, then',
    'normalizes globally per output using training data only. This intentionally shifts',
    'effective weight toward costly cases/hands; it is part of the intervention. The',
    'normalization keeps total loss mass comparable between the two objectives. Ties',
    'have zero cost weight. All 16 fitted outputs were nonconstant and converged.',
    'Models were persisted before any evaluation-case calculation. The parent refit',
    'all four seat models and reproduced their records exactly. No deployed source changed.','',
    '## Mean grouping floors','',
    'Lower is better. These are interval midpoints for the best full-hand profile',
    'exploitability representable by the groups in the fixed two-player one-bet river',
    'game, in conditional game chips. They are not win rates or BB/100. Eight boards',
    'receive equal weight, each averaging the six declared pool/regime combinations.','',
    '| Representation | Mean floor |','|---|---:|']
for m,v in a['overall']['floors'].items():lines.append(f'| {m} | {v:.10f} |')
lines += ['', 'Crossover control names old_old/new_old/old_new/new_new refer to the preceding',
    'full-target versus clipped-target regressors, bettor first and caller second. They',
    'are frozen controls, distinct from the new preference classifiers.','',
    '## Paired comparisons','',
    'Delta is candidate minus reference. Counts are lower / higher / overlapping.','',
    '| Candidate | Reference | Mean delta | Counts |','|---|---|---:|---:|']
def counts(v):return '/'.join(str(v['counts'].get(k,0)) for k in ('lower','higher','overlapping'))
for m,cs in s['overall']['comparisons'].items():
    for ref in ('ordinary_preference','range_response','new_old','exact_preference','clipped_oracle'):
        if ref in cs:
            v=cs[ref];lines.append(f'| {m} | {ref} | {mid(v):.10f} | {counts(v)} |')
lines += ['', 'All remaining comparisons are retained in summary.json.','',
    '## Seat contributions','',
    'The first three contrasts are against range-response. The last isolates weighting.',
    'Negative favors the candidate. Contributions add algebraically for this estimand.','',
    '| Contrast | Bettor delta | Bettor counts | Caller delta | Caller counts |',
    '|---|---:|---:|---:|---:|']
for m,ss in s['overall']['seat_effects'].items():
    b,c=ss['bettor'],ss['caller']
    lines.append(f'| {m} | {mid(b):.10f} | {counts(b)} | {mid(c):.10f} | {counts(c)} |')
lines += ['', '## Board and range results','',
    '| Board | Ordinary preference | Weighted preference | Exact preference | Range-response |',
    '|---|---:|---:|---:|---:|']
for b,v in a['boards'].items():
    lines.append('| '+b+' | '+' | '.join(f"{v['floors'][m]:.9f}" for m in
        ('ordinary_preference','weighted_preference','exact_preference','range_response'))+' |')
lines += ['', '| Regime | Ordinary preference | Weighted preference | Exact preference | Range-response |',
    '|---|---:|---:|---:|---:|']
for regime,v in a['regimes'].items():
    lines.append('| '+regime+' | '+' | '.join(f"{v['floors'][m]:.9f}" for m in
        ('ordinary_preference','weighted_preference','exact_preference','range_response'))+' |')
lines += ['', 'Ordinary classification improves both regime means. Weighted classification is',
    'slightly better than ordinary on uniform ranges, worse on polarized ranges and',
    'worse than range-response on polarized ranges. The synthetic range intervention',
    'still reweights both seats at once; it is not a posterior induced by earlier betting.','',
    '| Omitted board | Ordinary minus response | Weighted minus response | Weighted minus ordinary |',
    '|---|---:|---:|---:|']
for b,v in a['lobo'].items():
    cs=v['comparisons']
    lines.append(f"| {b} | {cs['ordinary_preference']['range_response']['delta']:.10f} | "
        f"{cs['weighted_preference']['range_response']['delta']:.10f} | "
        f"{cs['weighted_preference']['ordinary_preference']['delta']:.10f} |")
lines += ['', 'These are descriptive sensitivity checks, not confidence intervals.','',
    '## Preidentified difficult cases','',
    '| Case | Ordinary | Weighted | Exact preference | Range-response |',
    '|---|---:|---:|---:|---:|']
for case,fs in a['preidentified'].items():
    lines.append('| '+case+' | '+' | '.join(f'{fs[m]:.9f}' for m in
        ('ordinary_preference','weighted_preference','exact_preference','range_response'))+' |')
lines += ['', 'Both cases use 6h 6s Jh Qc Qd and polarized ranges. Neither is excluded.',
    'The weighted predictor again has a material loss on pool 2; ordinary does not.', '',
    '## Prediction diagnostic','',
    'The following averages the four witness columns. It is the expected wrong-action',
    'cost if each predicted probability were used as a decision against its fixed',
    'witness, weighted by own-hand mass. It is not grouped-policy exploitability or',
    'the training cross-entropy objective. Exact-preference costs are zero by definition.','',
    '| Split | Seat | Ordinary expected cost | Weighted expected cost |',
    '|---|---:|---:|---:|']
for split,d in audit['expected_wrong_action_cost'].items():
    for seat in (0,1):
        o=sum(d['ordinary_preference'][seat])/4;w=sum(d['weighted_preference'][seat])/4
        lines.append(f'| {split} | {seat} | {o:.9f} | {w:.9f} |')
lines += ['', 'Weighting substantially improves this caller diagnostic and its strategic floor.',
    'The bettor diagnostic barely changes on evaluation, while its grouping worsens.',
    'This again illustrates the gap between individual feature diagnostics and the',
    'quality of the induced partition. It does not identify a unique cause.','',
    '## Verification and retained execution','',
    f"Worker: {worker['seconds']:.6f} s; worker plus parent: {receipt['seconds']:.6f} s.",
    f"Worker training reconstruction: {fit['input_seconds']:.6f} s; fitting: {fit['fit_seconds']:.6f} s.",
    'Combined timing spans launch through parent verification, independent audit and',
    'original result-manifest writing, excluding preflight, reservation and final receipt.',
    'Python 3.14.6 / NumPy 2.5.2 / SciPy 1.18.0, one BLAS thread. Worker limit 600 s,',
    'parent outside it, no RSS cap or peak-memory claim. One invocation completed, exit 0.',
    'All 288 LP calls were counted. Each retained the five-second/10,000-iteration limits.',
    'Four models with 16 output tasks were fitted in the worker and refitted in the',
    'parent for verification. There was no hyperparameter search or launch retry.','',
    'The parent reconstructed every training/evaluation input, model, feature and group',
    'and verified all 288 asymmetric payoff certificates with the LP optimizer disabled.',
    'The separate audit used scalar sigmoid/target/cost calculations and independently',
    'assembled regularized gradients. It checked 147,456 probabilities, 16 output',
    'gradients, 144 floor identities, 1,296 signed comparisons, 384 seat contributions',
    'and 2,115 aggregate records, adding no fits or LPs.',
    f"Maximum audited gradient: {max(audit['output_gradients']):.6e}.",
    f"Maximum new certificate width: {audit['maximum_certificate_gap']:.6e} chips.",
    f"All {len(plan['pins'])} input pins verified again before retention.",
    'Pre-freeze analytic fits, finite-difference gradients, ties/constants and refusal',
    'checks passed. Certificates apply to encoded binary64 payoffs, not an independent',
    'card evaluator. No cold opposing review is claimed for this diagnostic.','',
    'The result is a development intervention on repeatedly observed boards. New-board',
    'confirmation is still required before generalization; full-game or six-max strength',
    'would require separate evaluation. No model was selected per evaluation case.','',
    'Original output: D:/Pontius-training/river-abstraction-study/witness-preference-001',
    'Archive: experiments/river-abstraction-study/witness-preference-001',
    'All eleven prior milestones preserved. No production change, commit, push or adoption.','',
    'Plan SHA-256:',digest(OUT/'plan.json'),'',
    'Original result manifest SHA-256:',receipt['result_manifest_sha256'],'']
with REPORT.open('x',encoding='utf-8',newline='\n') as f:f.write('\n'.join(lines))
shutil.copytree(OUT,ARCHIVE);(ARCHIVE/'verification-tools').mkdir()
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
    'witness-pilot-001','witness-distillation-001','witness-fit-diagnostic-001','witness-hybrid-001',
    'witness-boundary-001','witness-clipped-target-001','witness-seat-crossover-001'):
    directory=ROOT/'experiments/river-abstraction-study'/name
    for member,h in read(directory/'milestone-manifest.json').items():
        assert digest(directory/member)==h,(name,member)
    prior[name]=digest(directory/'milestone-manifest.json')
overview=ROOT/'docs/research/README.md'
with (HERE/'research-readme-before.md').open('xb') as f:f.write(overview.read_bytes())
with overview.open('ab') as f:
    f.write(b'\n## Action-preference learning\n\n'
        b'[Witness-preference-001](river-witness-preference-001.md) compares ordinary\n'
        b'and cost-weighted classifiers with exact teacher preferences. Ordinary improves\n'
        b'all eight board means versus range-response; weighting is worse overall.\n')
record=dict(passed=True,milestone_members=len(members),
    milestone_sha256=digest(ARCHIVE/'milestone-manifest.json'),report_sha256=digest(REPORT),
    prior_milestones=prior,commit_performed=False,push_performed=False)
write(HERE/'retention.json',record);print(json.dumps(record,indent=2))
