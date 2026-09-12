"""Retain completed policies and their verified analysis without changing old milestones."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess

ROOT=Path('D:/Pontius-worktrees/eval-runner-consolidation')
HERE=Path(__file__).parent
OUT=Path('D:/Pontius-training/river-abstraction-study/witness-solver-budget-001')
ARCHIVE=ROOT/'experiments/river-abstraction-study/witness-solver-budget-001'
REPORT=ROOT/'docs/research/river-witness-solver-budget-001.md'
read=lambda p:json.loads(p.read_bytes())
digest=lambda p:sha256(p.read_bytes()).hexdigest()


def write(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as f:
        f.write(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n')


plan=read(OUT/'plan.json')
summary=read(OUT/'summary.json')
receipt=read(OUT/'receipt.json')
audit=read(OUT/'audit.json')
sa=read(OUT/'summary-audit.json')
worker=read(OUT/'worker-receipt.json')
verifier=read(OUT/'verify-receipt.json')
assert receipt['exit']==worker['exit']==verifier['exit']==0
assert audit['passed'] and sa['passed']
assert not ARCHIVE.exists() and not REPORT.exists()
for path,h in plan['pins'].items():assert digest(Path(path))==h,path
assert digest(OUT/'results-manifest.json')==receipt['result_manifest_sha256']
for name,h in read(OUT/'results-manifest.json').items():assert digest(OUT/name)==h,name
rows=[read(OUT/(c['id']+'.json')) for c in plan['cases']]
assert [r['case'] for r in rows]==plan['cases']
methods=plan['methods']
def counts(v):
    return '/'.join(str(v['counts'].get(k,0)) for k in ('lower','higher','overlapping'))
def case_value(row,kind,budget,method):
    rs=[x['full']['exploitability'] for r in row['runs'] if r['method']==method
        for x in r['records'] if x['kind']==kind and x['budget']==budget]
    assert len(rs)==(3 if kind=='seconds' else 1)
    return sum(rs)/len(rs)
worst={}
for kind,budget in [('iterations',10000),('seconds',.5)]:
    values=[dict(case=r['case'],candidate=case_value(r,kind,budget,methods[0]),
                 reference=case_value(r,kind,budget,methods[1])) for r in rows]
    for v in values:v['delta']=v['candidate']-v['reference']
    worst[f'{kind}:{budget}']=sorted(values,key=lambda v:v['delta'],reverse=True)[:5]
board_counts={key:dict(Counter('lower' if v[key]['comparisons']['range_response']['delta'] < -1e-10
    else 'higher' if v[key]['comparisons']['range_response']['delta'] > 1e-10 else 'overlapping'
    for v in summary['boards'].values())) for key in ('iterations:10000','seconds:0.5')}
analysis=dict(worst_cases=worst,board_counts=board_counts,
    relative_reductions_percent={k:100*(v['means']['range_response']-v['means'][methods[0]])/
        v['means']['range_response'] for k,v in summary['overall'].items()},
    numerical_improvement_pass=summary['numerical_improvement_pass'],
    robustness_pass=summary['robustness_pass'])
write(OUT/'analysis.json',analysis)
lines=['# Frozen groups under solver budgets: witness-solver-budget-001','',
    '## Result','',
    'Predeclared numerical improvement flag: '+('PASS.' if summary['numerical_improvement_pass'] else 'NOT PASSED.'),
    'Predeclared robustness flag: '+('PASS.' if summary['robustness_pass'] else 'NOT PASSED.'),
    'These are deterministic benchmark criteria with a 1e-10-chip comparison tolerance,',
    'not statistical confidence levels, adoption decisions or full-game strength claims.','',
    'The primary endpoints are 10000 iterations and 0.5 seconds. The timed endpoint',
    'averages the three repetitions within each case. Cases are equally weighted',
    'within each board, and the sixteen boards receive equal weight.','',
    '## Actual full-hand exploitability','',
    'Lower is better. Units are conditional one-bet game chips, not BB/100.',
    'Policies are lifted to all 96 holdings per seat; best responses are unrestricted.',
    'This measures computed policies, rather than only the best representable floor.','',
    '| Budget | Learned preference | Range-response | Range-equity | Reduction vs response |',
    '|---|---:|---:|---:|---:|']
for k,v in summary['overall'].items():
    f=v['means']
    lines.append(f"| {k} | {f[methods[0]]:.10f} | {f[methods[1]]:.10f} | "
                 f"{f[methods[2]]:.10f} | {analysis['relative_reductions_percent'][k]:.2f}% |")
lines += ['', 'Counts below mean lower / higher / numerically overlapping cases.','',
    '| Budget | Delta vs response | Counts | Delta vs equity | Counts |',
    '|---|---:|---:|---:|---:|']
for k,v in summary['overall'].items():
    a,b=v['comparisons']['range_response'],v['comparisons']['range_equity']
    lines.append(f"| {k} | {a['delta']:.10f} | {counts(a)} | {b['delta']:.10f} | {counts(b)} |")
lines += ['', '## Representation floor and computed-policy residual','',
    'The floor is the retained certificate for the best representable full-hand profile.',
    'Residual equals actual exploitability minus this floor. It can include both finite',
    'optimization error and the difference between solving the compressed equilibrium',
    'and minimizing unrestricted exploitability within the representation. It is not',
    'necessarily removable merely by running this CFR solver longer.','',
    '| Budget | Method | Full-hand exploitability | Above floor | Compressed exploitability |',
    '|---|---|---:|---:|---:|']
for key in ('iterations:10000','seconds:0.5'):
    v=summary['overall'][key]
    for m in methods:
        lines.append(f"| {key} | {m} | {v['means'][m]:.10f} | "
                     f"{v['above_floor'][m]:.10f} | {v['restricted'][m]:.10f} |")
lines += ['', '## Board and range sensitivity','',
    '| Board | Delta at 10000 iterations | Delta at 0.5 seconds |','|---|---:|---:|']
for b,v in sorted(summary['boards'].items(),key=lambda item:int(item[0])):
    lines.append(f"| {b} | {v['iterations:10000']['comparisons']['range_response']['delta']:.10f} | "
                 f"{v['seconds:0.5']['comparisons']['range_response']['delta']:.10f} |")
lines += ['', '| Panel | Delta at 10000 iterations | Delta at 0.5 seconds |','|---|---:|---:|']
for name in ('textures','regimes'):
    for label,v in summary[name].items():
        lines.append(f"| {label} | {v['iterations:10000']['comparisons']['range_response']['delta']:.10f} | "
                     f"{v['seconds:0.5']['comparisons']['range_response']['delta']:.10f} |")
lines += ['', '| Omitted board | Delta at 10000 iterations | Delta at 0.5 seconds |','|---|---:|---:|']
for b,v in sorted(summary['leave_one_board_out'].items(),key=lambda item:int(item[0])):
    lines.append(f"| {b} | {v['iterations:10000']['comparisons']['range_response']['delta']:.10f} | "
                 f"{v['seconds:0.5']['comparisons']['range_response']['delta']:.10f} |")
lines += ['', '## Timing repetitions and completed work','',
    '| Repetition at 0.5 s | Learned | Response | Equity | Delta vs response |',
    '|---|---:|---:|---:|---:|']
for label,v in summary['repetitions'].items():
    lines.append(f"| {label} | {v['means'][methods[0]]:.10f} | {v['means'][methods[1]]:.10f} | "
                 f"{v['means'][methods[2]]:.10f} | {v['comparisons']['range_response']['delta']:.10f} |")
lines += ['', '| Budget | Mean learned iterations | Mean response iterations | Mean equity iterations |',
    '|---|---:|---:|---:|']
for k,v in summary['overall'].items():
    f=v['mean_iterations']
    lines.append(f"| {k} | {f[methods[0]]:.2f} | {f[methods[1]]:.2f} | {f[methods[2]]:.2f} |")
lines += ['', 'Three timed repetitions rotate method order within every case. Time is measured',
    'on this machine, with one BLAS thread and no allocation tracing. Reported budgets',
    'start with loaded games, full-board equity tables and loaded model coefficients.',
    'They include each method\'s features, prediction, grouping, aggregation and CFR setup',
    'and updates. Clock/checkpoint bookkeeping is excluded; pre-step policy copies are',
    'included. Imports, disk I/O, certification and scoring are outside the boundary.',
    'Thus these are warm-input active-wall budgets, not cold end-to-end latency.','',
    'The saved timed policy is from the last completed iteration before its deadline.',
    'The crossing iteration is not credited. Every cell records both timestamps.',
    f"Setup missed {summary['setup_misses']} checkpoint budgets; those cells retain the uniform policy.",
    f"Common input construction and validation: {summary['common_seconds']:.6f} s total.",
    'That shared stage includes exact equity-cache fills, game creation and predecessor',
    'control construction. It is not charged selectively to any method.','',
    '| Method | Total setup over 384 trajectories | Mean setup |','|---|---:|---:|']
for m,t in summary['setup_seconds'].items():
    lines.append(f'| {m} | {t:.6f} s | {1000*t/384:.4f} ms |')
lines += ['', '| Setup-miss case | Method | Repetition | Budget | Setup ms |',
    '|---|---|---:|---:|---:|']
for row in rows:
    for run in row['runs']:
        for rec in run['records']:
            if rec.get('setup_missed',False):
                lines.append(f"| {row['case']['id']} | {run['method']} | "
                    f"{run['repetition']} | {rec['budget']} s | "
                    f"{1000*run['setup_seconds']:.4f} |")
lines += ['', '## Largest losses retained','',
    '| Endpoint | Case | Learned | Response | Delta |','|---|---:|---:|---:|']
for key,values in worst.items():
    for v in values:
        lines.append(f"| {key} | {v['case']['id']} | {v['candidate']:.10f} | "
                     f"{v['reference']:.10f} | {v['delta']:.10f} |")
lines += ['', '## Design, execution and verification','',
    'All 96 cases from witness-preference-confirmation-001 are retained: sixteen observed',
    'boards, three fixed pools and two synthetic range regimes. No new boards, fitting,',
    'hyperparameter search, alternative seed, adaptive budget or favorable subset.',
    'The model, features and groups reproduce the predecessor exactly. Each method has',
    'the same occupied group capacity per case. Pot 10, bet 5, stacks 20/20, one bet,',
    'two players, 96 hands per seat. These ranges are not reached betting posteriors.',
    'The existing alternating vanilla CFR starts with zero regrets and uniform policy.',
    'Strategies use its unweighted average; updates are deterministic full enumeration.','',
    'Preflight: seven existing tests passed, including compact/full-tree and grouped',
    'CFR parity, payoff/BR equivalence and aggregation. Synthetic checks covered budget',
    'crossings, crossing several budgets, exact-boundary equality and setup failure.',
    'No scored benchmark rehearsal was used. The preflight tool receipts are described',
    'in the pinned preflight.json; the original console outputs remain in tool history.','',
    f"Worker: {worker['seconds']:.6f} s, exit 0, maximum 1200 s.",
    f"Verifier: {verifier['seconds']:.6f} s, exit 0, maximum 900 s.",
    f"Combined invocation: {receipt['seconds']:.6f} s, exit 0.",
    'No RSS ceiling or peak-memory measurement. CPython 3.14.6 / NumPy 2.5.2 / SciPy 1.18.0.',
    'All 1152 solver trajectories and 3456 checkpoint policies retained. No new LP solve',
    'or model fit. The verifier rebuilt every input and grouping, checked 576 retained',
    'asymmetric certificates with solving disabled, and replayed every saved policy',
    'exactly from the deterministic CFR trajectory. Scalar fsum arithmetic independently',
    'checked all full-hand payoff and best-response metrics. Restricted-game inequalities',
    'and actual-versus-floor bounds passed for every policy.','',
    f"Replay iterations: {audit['replayed_steps']:,}.",
    f"Maximum scalar/vector metric discrepancy: {audit['maximum_scalar_discrepancy']:.6e} chips.",
    f"Independent rational summary scalar checks: {sa['summary_scalars_verified']:,}.",
    f"All {len(plan['pins'])} pinned files were reverified after execution.",
    'No opposing cold review is claimed. Numerical checks bound implementation agreement',
    'at the declared tolerance; they are not uncertainty intervals over possible boards.',
    'The thirteen older milestones, original source and unrelated edits remain preserved.',
    'No production modification, commit, push or adoption was performed.','',
    'Plan SHA-256:',digest(OUT/'plan.json'),'',
    'Frozen candidate SHA-256:',plan['candidate_sha256'],'',
    'Original result manifest SHA-256:',receipt['result_manifest_sha256'],'']
with REPORT.open('x',encoding='utf-8',newline='\n') as f:f.write('\n'.join(lines))
shutil.copytree(OUT,ARCHIVE)
(ARCHIVE/'verification-tools').mkdir()
for name in ('design.md','experiment.py','prepare.py','summary-audit.py',
             'report-and-retain.py','preflight.json','worktree-before.json'):
    shutil.copyfile(HERE/name,ARCHIVE/'verification-tools'/name)
shutil.copyfile(REPORT,ARCHIVE/'report.md')
for p in OUT.iterdir():
    if p.is_file():assert digest(p)==digest(ARCHIVE/p.name)
members={p.relative_to(ARCHIVE).as_posix():digest(p) for p in sorted(ARCHIVE.rglob('*')) if p.is_file()}
write(ARCHIVE/'milestone-manifest.json',members)
for name,h in members.items():assert digest(ARCHIVE/name)==h,name
prior={}
for directory in sorted(ARCHIVE.parent.iterdir()):
    manifest=directory/'milestone-manifest.json'
    if directory!=ARCHIVE and manifest.is_file():
        for name,h in read(manifest).items():assert digest(directory/name)==h,(directory,name)
        prior[directory.name]=digest(manifest)
assert len(prior)==13
overview=ROOT/'docs/research/README.md'
with (HERE/'research-readme-before.md').open('xb') as f:f.write(overview.read_bytes())
with overview.open('ab') as f:
    f.write(b'\n## Frozen grouping solver-budget benchmark\n\n'
        b'[Witness-solver-budget-001](river-witness-solver-budget-001.md) compares actual\n'
        b'CFR policies at matched iterations and three repeated time budgets, with\n'
        b'all 96 observed-panel cases retained and the learned grouping frozen.\n')
git=['C:/Program Files/Git/cmd/git.exe','-c',f'safe.directory={ROOT}','-C',str(ROOT)]
before=read(HERE/'worktree-before.json')
assert subprocess.check_output(git+['rev-parse','HEAD'],text=True).strip()==before['head']
for name,h in before['unrelated_files'].items():assert digest(ROOT/name)==h,name
record=dict(passed=True,milestone_members=len(members),
    milestone_sha256=digest(ARCHIVE/'milestone-manifest.json'),
    report_sha256=digest(REPORT),prior_milestones=prior,source_head=before['head'],
    commit_performed=False,push_performed=False)
write(HERE/'retention.json',record)
print(json.dumps(record,indent=2))
