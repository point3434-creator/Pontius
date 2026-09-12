"""Postprocess and preserve the complete diagnostic; never launch or publish."""
from collections import Counter
from fractions import Fraction as Q
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path('D:/Pontius-worktrees/eval-runner-consolidation')
HERE = Path(__file__).parent
OUT = Path('D:/Pontius-training/river-abstraction-study/witness-pot-diagnostic-001')
ARCHIVE = ROOT/'experiments/river-abstraction-study/witness-pot-diagnostic-001'
REPORT = ROOT/'docs/research/river-witness-pot-diagnostic-001.md'
read = lambda p: json.loads(p.read_bytes())
digest = lambda p: sha256(p.read_bytes()).hexdigest()
mid = lambda x: float((Q(x['lower_exact'])+Q(x['upper_exact']))/2)


def write(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as f:
        f.write(json.dumps(value, sort_keys=True, indent=2, allow_nan=False)+'\n')


def direction(x):
    return 'lower' if x < -1e-10 else 'higher' if x > 1e-10 else 'overlapping'


def counts(x):
    return '/'.join(str(x.get(k, 0)) for k in ('lower', 'higher', 'overlapping'))


p = read(OUT/'plan.json')
s = read(OUT/'summary.json')
audit = read(OUT/'audit.json')
sa = read(OUT/'summary-audit.json')
receipt = read(OUT/'receipt.json')
worker = read(OUT/'worker-receipt.json')
verifier = read(OUT/'verify-receipt.json')
assert receipt['exit'] == worker['exit'] == verifier['exit'] == 0
assert audit['passed'] and sa['passed']
assert not REPORT.exists() and not ARCHIVE.exists()
for path, h in p['pins'].items():
    assert digest(Path(path)) == h, path
assert digest(OUT/'results-manifest.json') == receipt['result_manifest_sha256']
for name, h in read(OUT/'results-manifest.json').items():
    assert digest(OUT/name) == h, name
before = read(HERE/'worktree-before.json')
for name, h in before['modified_tracked_files'].items():
    assert digest(ROOT/name) == h, name
git = ['C:/Program Files/Git/cmd/git.exe', '-c', f'safe.directory={ROOT}', '-C', str(ROOT)]
assert subprocess.check_output(git+['rev-parse', 'HEAD'], text=True).strip() == before['head']
prior = {}
for directory in sorted(ARCHIVE.parent.iterdir()):
    manifest = directory/'milestone-manifest.json'
    if directory != ARCHIVE and manifest.is_file():
        for name, h in read(manifest).items():
            assert digest(directory/name) == h, (directory, name)
        prior[directory.name] = digest(manifest)
assert len(prior) == 15

analysis = {}
for panel, checkpoints in s['solver_panels'].items():
    v = checkpoints['50000']
    analysis[panel] = dict(
        learned_br_reduction_percent=100*(v['means']['ordinary_preference:cfr']-
            v['means']['ordinary_preference:br'])/v['means']['ordinary_preference:cfr'],
        response_br_reduction_percent=100*(v['means']['range_response:cfr']-
            v['means']['range_response:br'])/v['means']['range_response:cfr'],
        learned_residual_removed_percent=100*(v['above_floor']['ordinary_preference:cfr']-
            v['above_floor']['ordinary_preference:br'])/v['above_floor']['ordinary_preference:cfr'],
        board_counts={key:dict(Counter(direction(b['comparisons'][key]['delta'])
            for b in s['solver_boards'][panel].values())) for key in v['comparisons']},
        leave_one_board_out_counts={key:dict(Counter(direction(b['comparisons'][key]['delta'])
            for b in s['solver_leave_one_board_out'][panel].values())) for key in v['comparisons']})
g = s['grouping']['overall']['floors']
analysis['oracle_reduction_percent'] = {m:100*(mid(g[m])-mid(g['pot_witness']))/mid(g[m])
    for m in ('ordinary_preference', 'range_response', 'half_witness')}
assert analysis['polarized']['board_counts']['learned_minus_response_br'] == {'lower':9, 'higher':7}
assert sorted(int(b) for b, v in s['solver_leave_one_board_out']['polarized'].items()
    if v['comparisons']['learned_minus_response_br']['delta'] > 0) == [2, 10, 13]
assert s['solver_panels']['paired_trips']['50000']['comparisons']['learned_minus_response_br']['delta'] > 0
assert mid(g['ordinary_preference']) > mid(g['range_response'])
assert mid(g['half_witness']) > max(mid(g[m]) for m in ('ordinary_preference', 'range_response'))
write(OUT/'analysis.json', analysis)
keys = ('ordinary_preference:cfr', 'ordinary_preference:br',
        'range_response:cfr', 'range_response:br')
lines = ['# Pot-sized failure diagnostic: witness-pot-diagnostic-001', '',
    '## Results under the frozen rules', '',
    '| Separate decision | Result |', '|---|---|']
for key in ('solver_gap_reduced', 'solver_ranking_repaired',
            'oracle_representation_repaired', 'oracle_context_gain'):
    lines.append(f"| {key} | {'PASS' if s[key] else 'NOT PASSED'} |")
lines += ['',
    'The solver rules use the 48 polarized-range cases at 50000 iterations. Gap',
    'reduction means learned BR is less exploitable than learned ordinary CFR.',
    'Ranking repair separately means learned BR is less exploitable than response BR.',
    'Both require a mean difference below -1e-10 chips.',
    'The oracle rules use the 24 multiple-pairs-or-trips cases. Representation repair',
    'requires the pot-witness floor to beat both frozen learned and response floors.',
    'Context gain separately requires it to beat the half-witness floor. Each floor',
    'difference must have a negative upper numerical endpoint.',
    'These are separate predeclared diagnostics, not a combined adoption gate.', '',
    'This is a post-finding diagnostic on previously observed failing panels.',
    'It is not a fresh confirmation or a population confidence statement.',
    'The 60-case union contains 48 polarized cases and 24 paired/trips cases, with',
    '12 in their intersection. Every case from each declared panel was kept.',
    'Panels receive equal board weights and are reported separately; there is no',
    'primary average over the union that could hide one panel behind the other.', '',
    '## Interpretation', '',
    f"On polarized ranges, changing the solver reduces learned-policy exploitability by",
    f"{analysis['polarized']['learned_br_reduction_percent']:.2f}% at matched 50000 updates,",
    f"removing {analysis['polarized']['learned_residual_removed_percent']:.2f}% of its residual",
    'above the fixed grouping floor. The learned-vs-response ranking under BR is',
    ('favorable on this panel.' if s['solver_ranking_repaired'] else
     'not repaired on this panel under the frozen rule.'),
    'That small aggregate ranking is board-sensitive: learned BR wins on nine of',
    'sixteen board means, and omitting any of boards 2, 10 or 13 reverses the mean',
    'ranking. Passing the ranking flag is not a robust across-board advantage.',
    'This separates a solver-objective limitation from a lack of representation',
    'capacity. It does not prove ordinary CFR has converged; the finite checkpoint',
    'comparison and the independently attained LP targets are the evidence.', '',
    'The paired/trips panel must still be considered separately. Its learned floor',
    'remains worse than the response floor, and its learned BR policy is also worse',
    'than response BR at the final checkpoint. The solver improvement does not',
    'repair that representation ranking. Oracle pot-witness grouping reduces the',
    f"floor by {analysis['oracle_reduction_percent']['ordinary_preference']:.2f}% versus",
    f"learned and {analysis['oracle_reduction_percent']['range_response']:.2f}% versus response.",
    'That demonstrates substantial room at the same group count when exact target-',
    'game information is supplied. The half-witness control performs worse than',
    'both frozen groupings here, so exact signals from the old context are not',
    'enough. Payoffs and opponent witnesses change together; the test does not',
    'identify which of those two changes explains the context gain.', '',
    'A practical follow-up is to use the unrestricted-response objective when',
    'judging groupings and test whether a bet-conditioned predictor can recover',
    'the oracle advantage on untouched boards. The current result establishes',
    'neither that learned recovery nor a deployable policy improvement.', '',
    '## Solver comparison at all checkpoints', '',
    'Lower unrestricted full-hand exploitability is better. Units are conditional',
    'river-game chips, with pot 10 and bet 10. These are deterministic enumerated',
    'best-response values, not sampled match returns or BB/100.', '',
    '| Panel | Iterations | Learned CFR | Learned BR | Response CFR | Response BR |',
    '|---|---:|---:|---:|---:|---:|']
for panel, checkpoints in s['solver_panels'].items():
    for n in ('1000', '10000', '50000'):
        v = checkpoints[n]
        lines.append(f'| {panel} | {n} | '+' | '.join(f"{v['means'][k]:.10f}" for k in keys)+' |')
lines += ['', '## Representation targets and remaining solver gaps', '',
    'The grouping floor is the least full-hand profile exploitability representable',
    'by a pair of groups, certified by two asymmetric saddle problems. A compressed',
    'game equilibrium need not minimize that full-hand quantity.',
    'Floor values below are interval midpoints; exact rational endpoints are retained.', '',
    '| Panel | Method | Floor | CFR residual, 50k | BR residual, 50k |',
    '|---|---|---:|---:|---:|']
for panel, checkpoints in s['solver_panels'].items():
    v = checkpoints['50000']
    for m in ('ordinary_preference', 'range_response'):
        lines.append(f"| {panel} | {m} | {mid(v['floors'][m]):.10f} | "
            f"{v['above_floor'][m+':cfr']:.10f} | {v['above_floor'][m+':br']:.10f} |")
lines += ['',
    'The saved LP target combines each grouping\'s constrained-seat saddle policies.',
    'All 120 resulting full-hand profiles attain the corresponding certified floor',
    'upper endpoint within 1e-10 chips. These are oracle targets, not additional',
    'iterative solver trajectories. They independently establish the attainable',
    'representation target against which finite solver residuals are measured.', '',
    '## Solver sensitivity at 50000 iterations', '',
    'Counts are lower / higher / numerically overlapping. Differences are in chips.', '',
    '| Panel | Comparison | Mean delta | Case counts | Board counts | Omit-board counts |',
    '|---|---|---:|---:|---:|---:|']
for panel, checkpoints in s['solver_panels'].items():
    for key, v in checkpoints['50000']['comparisons'].items():
        lines.append(f"| {panel} | {key} | {v['delta']:.10f} | {counts(v['counts'])} | "
            f"{counts(analysis[panel]['board_counts'][key])} | "
            f"{counts(analysis[panel]['leave_one_board_out_counts'][key])} |")
for category in ('solver_boards', 'solver_leave_one_board_out'):
    lines += ['', '### '+category, '',
        '| Panel | Board | Learned BR minus CFR | Response BR minus CFR | Learned minus response BR |',
        '|---|---|---:|---:|---:|']
    for panel, values in s[category].items():
        for board, v in values.items():
            lines.append(f'| {panel} | {board} | '+' | '.join(
                f"{v['comparisons'][k]['delta']:.10f}" for k in (
                    'learned_br_minus_cfr', 'response_br_minus_cfr', 'learned_minus_response_br'))+' |')
lines += ['', '## Oracle grouping comparison on paired/trips cases', '',
    'Both oracle groupings keep each case\'s occupied group count. Three action-',
    'advantage columns come from the learned, response and equity opponent witnesses',
    'in that fixed order, clipped to [-0.5, 0.5], with unchanged weighted anchored',
    'clustering. Half-witness uses half-pot payoffs and witnesses; pot-witness uses',
    'pot-sized payoffs and witnesses. Both floors are evaluated in the pot-sized game.',
    'Thus the intervention changes both payoff context and opponent witnesses.',
    'It is not a one-scalar bet-input ablation. Target-case oracle information is',
    'used, so neither is a deployable learned candidate or evidence of generalization.', '',
    '| Panel | Learned floor | Response floor | Half-witness floor | Pot-witness floor |',
    '|---|---:|---:|---:|---:|']
group_panels = [('overall', s['grouping']['overall'])]
group_panels += [(kind+':'+name, v) for kind in ('boards', 'regimes', 'leave_one_board_out')
                 for name, v in s['grouping'][kind].items()]
for label, v in group_panels:
    lines.append(f'| {label} | '+' | '.join(f"{mid(v['floors'][m]):.10f}" for m in
        ('ordinary_preference', 'range_response', 'half_witness', 'pot_witness'))+' |')
lines += ['', '| Panel | Pot-witness minus | Lower endpoint | Upper endpoint | Case counts |',
    '|---|---|---:|---:|---:|']
for label, panel in group_panels:
    for key, v in panel['comparisons'].items():
        lines.append(f"| {label} | {key} | {float(Q(v['lower_exact'])):.10f} | "
            f"{float(Q(v['upper_exact'])):.10f} | {counts(v['counts'])} |")
lines += ['', '## Solver definition and cost', '',
    'Ordinary CFR is the existing alternating compressed-game solver. The new BR',
    'solver is two independent regret learners, each facing an unrestricted exact',
    'best response on every iteration. The averaged constrained-seat policies are',
    'paired only for profile evaluation. Both solvers start with zero regrets and',
    'uniform policies and use unweighted average strategies; exact best-response',
    'ties use probability 0.5. Every checkpoint is retained. No algorithm samples.',
    'The two methods receive matched paired update counts, not matched wall time or',
    'arithmetic work. Method/algorithm order rotates by case. No timing threshold',
    'is used to select a winner. Reported active times exclude checkpoint scoring.', '',
    'This full-enumeration one-bet specialization follows the objective of',
    '[Johanson et al., Finding Optimal Abstract Strategies in Extensive-Form Games',
    '(2012)](https://johanson.ca/publications/poker/2012-aaai-cfr-br/2012-aaai-cfr-br.pdf).',
    'Its two-player zero-sum interpretation does not establish a six-player guarantee.', '',
    '| Panel | Learned CFR seconds | Learned BR seconds | Response CFR seconds | Response BR seconds |',
    '|---|---:|---:|---:|---:|']
for panel, checkpoints in s['solver_panels'].items():
    v = checkpoints['50000']
    lines.append(f'| {panel} | '+' | '.join(f"{v['mean_active_seconds'][k]:.6f}" for k in keys)+' |')
lines += ['', '## Verification and retention', '',
    'All games use the retained public RiverHoldem path, 96 holdings per seat,',
    'pot 10, bet 10, stacks 20/20, heads-up and one bet without raises. These are',
    'synthetic conditional ranges, not ranges reached by a full-game betting policy.',
    'The learned classifier, frozen groups and source code were not modified.',
    'Exactly 240 solver trajectories produced 720 checkpoint policies. Forty-eight',
    'oracle group pairs required 96 new LP calls. LP time/iteration limits and',
    'rational certificate acceptance were unchanged. There were no model fits.', '',
    'The analytic update test first failed against a non-updating RED scaffold.',
    'After implementation, six preflight tests passed: direct scalar regret updates,',
    'exhaustive toy best responses, a known grouping floor, zero-payoff ties,',
    'invalid-input refusals and witness feature arithmetic.',
    'Thirteen existing payoff and optimality tests passed. No scored-panel rehearsal.',
    'The independent parent pass disabled LP and learning, reconstructed games and',
    'oracle features/groups, checked 600 certificates and replayed all 720 checkpoint',
    'policies from zero for 12000000 paired iterations. Ordinary CFR at 1000 and',
    '10000 iterations reproduced the retained pot-sized policy and score bytes.',
    'Separate scalar arithmetic checked all policy values and 120 LP targets.',
    'A separate standard-library rational audit rebuilt panels, means, intervals',
    'and the four frozen decision flags. This is computational verification;',
    'no independent cold review or population confidence interval is claimed.',
    f"Maximum scalar discrepancy: {audit['maximum_scalar_discrepancy']:.6e} chips.",
    f"Summary scalar checks: {sa['summary_scalar_checks']:,}.",
    f"Pinned files checked before and after execution: {len(p['pins'])}.",
    f"Worker: {worker['seconds']:.6f} s; verifier: {verifier['seconds']:.6f} s.",
    f"Combined invocation: {receipt['seconds']:.6f} s, exit 0.",
    'Each subprocess was bounded to 1200 seconds. No RSS cap or peak-memory claim.',
    'Python 3.14.6, NumPy 2.5.2, SciPy 1.18.0; one BLAS thread; no tracemalloc.',
    'All fifteen predecessor milestones were verified and preserved. Every result,',
    'including failures of decision flags, is retained. No production change,',
    'adoption, commit or push was performed.', '',
    'Plan SHA-256:', digest(OUT/'plan.json'), '',
    'Frozen learned candidate SHA-256:', p['candidate_sha256'], '',
    'Original result manifest SHA-256:', receipt['result_manifest_sha256'], '']
with REPORT.open('x', encoding='utf-8', newline='\n') as f:
    f.write('\n'.join(lines))
shutil.copytree(OUT, ARCHIVE)
(ARCHIVE/'verification-tools').mkdir()
for name in ('design.md', 'context.py', 'br.py', 'br-red.py', 'test_br.py',
             'experiment.py', 'summary-audit.py', 'prepare.py', 'report-and-retain.py',
             'red-to-green.diff', 'preflight.json', 'worktree-before.json'):
    shutil.copyfile(HERE/name, ARCHIVE/'verification-tools'/name)
shutil.copyfile(REPORT, ARCHIVE/'report.md')
for file in OUT.iterdir():
    if file.is_file():
        assert digest(file) == digest(ARCHIVE/file.name)
members = {f.relative_to(ARCHIVE).as_posix():digest(f)
           for f in sorted(ARCHIVE.rglob('*')) if f.is_file()}
write(ARCHIVE/'milestone-manifest.json', members)
for name, h in members.items():
    assert digest(ARCHIVE/name) == h, name
overview = ROOT/'docs/research/README.md'
with (HERE/'research-readme-before.md').open('xb') as f:
    f.write(overview.read_bytes())
with overview.open('ab') as f:
    f.write(b'\n## Pot-sized solver and grouping diagnostic\n\n'
        b'[Witness-pot-diagnostic-001](river-witness-pot-diagnostic-001.md) separates\n'
        b'solver residuals from representation limits on the prior failing panels,\n'
        b'using unrestricted best-response regret training and oracle witness groups.\n')
assert subprocess.check_output(git+['rev-parse', 'HEAD'], text=True).strip() == before['head']
record = dict(passed=True, milestone_members=len(members),
    milestone_sha256=digest(ARCHIVE/'milestone-manifest.json'), report_sha256=digest(REPORT),
    prior_milestones=prior, source_head=before['head'], commit_performed=False, push_performed=False)
write(HERE/'retention.json', record)
print(json.dumps(record, indent=2))
