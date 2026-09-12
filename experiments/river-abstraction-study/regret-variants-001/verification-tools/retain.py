"""Verify complete receipts and preserve all solver outcomes as a named milestone."""
from pathlib import Path
import shutil
import subprocess
from statistics import median
import experiment as e
from analysis import summarize

HERE = Path(__file__).resolve().parent
OUT = Path('D:/Pontius-training/river-abstraction-study')/e.NAME
ARCHIVE = e.HISTORY/e.NAME
REPORT = e.ROOT/'docs/research'/('river-'+e.NAME+'.md')
plan, receipt, audit = (e.read(OUT/p) for p in ('plan.json', 'receipt.json', 'audit.json'))
assert receipt['exit'] == 0 and audit['passed']
assert audit['independently_transformed_replay_updates'] == 2400000
assert audit['cases'] == 16 and audit['profiles'] == 240
assert e.digest(OUT/'plan.json') == e.read(HERE/'freeze.json')['plan_sha256']
assert e.digest(OUT/'results-manifest.json') == receipt['result_manifest_sha256']
for name, expected in e.read(OUT/'results-manifest.json').items():
    assert e.digest(OUT/name) == expected
e.bindings(plan)
rows = [e.read(OUT/f'case-{i:03d}.json') for i in range(16)]
summary = summarize(rows)
summary['panels'] = {}
for category in ('texture', 'regime'):
    summary['panels'][category] = {}
    for label in sorted({r['entry']['case'][category] for r in rows}):
        subset = [r for r in rows if r['entry']['case'][category] == label]
        summary['panels'][category][label] = dict(cases=len(subset), modes={mode: dict(
            mean_final_residual=sum(float(e.Q(r['arms'][mode][-1]['residual_interval'][1]))
                                   for r in subset)/len(subset)) for mode in e.MODES})
previous = e.read(HERE/'preflight.json')['prior_milestones']
for name, expected in previous.items():
    folder = e.HISTORY/name
    assert e.digest(folder/'milestone-manifest.json') == expected
    for member, value in e.read(folder/'milestone-manifest.json').items():
        assert e.digest(folder/member) == value
before = e.read(HERE/'worktree-before.json')
for name, expected in before['modified_tracked_files'].items():
    assert e.digest(e.ROOT/name) == expected, name
git = ['C:/Program Files/Git/cmd/git.exe', '-c', f'safe.directory={e.ROOT}', '-C', str(e.ROOT)]
assert subprocess.check_output(git+['rev-parse', 'HEAD'], text=True).strip() == before['head']
assert not ARCHIVE.exists() and not REPORT.exists()
lines = ['# Fixed-group regret variants 001', '',
    'Development comparison on the 16 retained size-confirmation incumbent cases.',
    'Both roles train from zero against unrestricted hand-specific best responses.',
    'No grouping repair, changed game, fresh boards, or fitted hyperparameters.', '',
    '## Results', '', '| Recipe | Final residual | Final exploitability | 50k solver seconds |',
    '|---|---:|---:|---:|']
for mode, r in summary['modes'].items():
    lines.append(f"| {mode} | {r['mean_final_residual']:.9f} | "
                 f"{r['mean_final_exploitability']:.9f} | {r['mean_50k_solver_seconds']:.3f} |")
lines += ['', 'Values are chips; residual is exploitability minus the certified floor lower bound.',
    'Times are mean across cases of the median of two timed repetitions.', '',
    '| Recipe | Target 0.001 first/persistent | Target 0.0001 first/persistent |',
    '|---|---:|---:|']
for mode, r in summary['modes'].items():
    a, b = r['crossings']['0.001'], r['crossings']['0.0001']
    lines.append(f"| {mode} | {a['first_crossed']}/{a['persistent_crossed']} of 16 | "
                 f"{b['first_crossed']}/{b['persistent_crossed']} of 16 |")
lines += ['', 'Persistent means that this and all subsequent sampled checkpoints pass.',
    'It does not assert monotonic convergence between checkpoints or after 50,000 updates.', '',
    '## Frozen decision rule', '']
for mode, r in summary['decisions'].items():
    ratio = r['median_paired_time_ratio']
    lines += [f"- {mode}: earns fresh-board confirmation = {r['earns_confirmation']};",
        f"  paired crossings {r['paired_crossings']}/16; faster {r['faster_cases']}/16;",
        f"  median paired solver-time ratio {ratio:.4f};" if ratio is not None else
        '  median paired solver-time ratio unavailable;',
        f"  mean final residual nonworse = {r['mean_final_residual_nonworse']}."]
lines += ['', 'The predeclared rule requires all 16 paired persistent crossings, at least 12 faster',
    'cases, median paired ratio below one, and no worse mean final residual.', '',
    '## Cases: final remaining error', '',
    '| Case | Texture | Range | rm | rm_plus | discounted |', '|---|---|---|---:|---:|---:|']
for i, row in enumerate(rows):
    case = row['entry']['case']
    values = [float(e.Q(row['arms'][mode][-1]['residual_interval'][1])) for mode in e.MODES]
    lines.append(f"| {i} | {case['texture']} | {case['regime']} | " +
                 ' | '.join(f'{v:.8f}' for v in values)+' |')
lines += ['', '## Interpretation limits', '',
    'rm uses signed cumulative regret and uniform averaging. rm_plus clips regret AFTER updates',
    'and uses quadratic averaging. discounted uses (alpha,beta,gamma)=(1.5,0,2), also with',
    'quadratic averaging. Recipe changes bundle averaging and regret; no causal attribution',
    'to either component alone. These adapt published recipes to the existing best-response',
    'learner, not a new full CFR self-play implementation or a transferred convergence theorem.', '',
    'The floor has an exact verified interval [L,U]. Every checkpoint retains [E-U,E-L].',
    'Thresholds use the conservative upper residual E-L, with no tolerance or clipping.',
    'Known boards are a development panel; no unseen-board or six-max playing-strength claim.', '',
    '## Timing', '',
    'Five checkpoints: 500, 2000, 10000, 25000, 50000. Arm order rotates by case and reverses',
    'in repetition two. Policies match exactly across repetitions. Solver time includes setup,',
    'updates and materializing averages. Exact scoring is excluded and separately timed on',
    'repetition one; summary crossing records include cumulative scoring for that pass.',
    'Two timing observations describe a range, not a confidence interval. Budget summaries use',
    'the latest completed checkpoint, never interpolation or the retrospectively best policy.',
    'A missing first checkpoint remains missing; no conditional mean is shown as complete.',
    'Shared game reconstruction, existing certificate validation and audit replay are outside',
    'solver timings. Exact checkpoint monitoring is research instrumentation, not live latency.', '',
    '## Verification and retention', '',
    'Eight analytic checks; three independent small-game replay comparisons before freezing.',
    '96 timed trajectories (4.8 million updates); 48 exact repeat-identity checks.',
    '2.4 million updates replayed using frozen payoff code and independent update transforms.',
    '240 exact profiles and 32 asymmetric certificates reverified; no new LP solves.',
    'All 16 plain 50k policies equal the historical checkpoints exactly.',
    f'All {len(previous)} prior milestone manifests and their members remain unchanged.',
    'Python 3.14.6; one BLAS thread; no allocation tracing; 900-second per-phase timeout.',
    'No hard RSS cap. Production source, frozen repair baseline and existing evidence unchanged.',
    f"Run plus verification: {receipt['seconds']:.3f} seconds; exit 0.", '',
    'Full curves, threshold crossings, timing samples and subgroup summaries: `summary.json`.',
    'Raw policies and exact rational certificates remain in each retained case file.', '',
    'Recipe reference: https://arxiv.org/pdf/1809.04040 (Brown and Sandholm, 2019).', '',
    'Plan SHA-256: '+e.digest(OUT/'plan.json'), '',
    'Results manifest SHA-256: '+receipt['result_manifest_sha256'], '']
e.write(OUT/'summary.json', summary)
with REPORT.open('x', encoding='utf-8', newline='\n') as f:
    f.write('\n'.join(lines))
shutil.copytree(OUT, ARCHIVE)
(ARCHIVE/'verification-tools').mkdir()
for p in sorted(HERE.iterdir()):
    if p.is_file() and p.name != 'plan.json':
        shutil.copyfile(p, ARCHIVE/'verification-tools'/p.name)
shutil.copyfile(REPORT, ARCHIVE/'report.md')
manifest = {p.relative_to(ARCHIVE).as_posix(): e.digest(p)
            for p in sorted(ARCHIVE.rglob('*')) if p.is_file()}
e.write(ARCHIVE/'milestone-manifest.json', manifest)
for name, value in manifest.items():
    assert e.digest(ARCHIVE/name) == value
index = e.ROOT/'docs/research/README.md'
old = index.read_bytes()
addition = ('\n## Fixed-group solver recipes\n\n'
    '[Regret variants 001](river-regret-variants-001.md) compares three fixed update recipes\n'
    'against the same certified grouping limits, with retained convergence and timing curves.\n')
index.write_bytes(old+addition.encode())
assert index.read_bytes().startswith(old)
e.write(HERE/'retention.json', dict(report=str(REPORT), archive=str(ARCHIVE),
    manifest_sha256=e.digest(ARCHIVE/'milestone-manifest.json'), members=len(manifest),
    preserved_prior_milestones=len(previous), committed=False, pushed=False))
print(e.read(HERE/'retention.json'))
print(summary['decisions'])
