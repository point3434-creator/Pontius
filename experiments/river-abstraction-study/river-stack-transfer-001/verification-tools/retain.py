"""Retain every domain outcome and the eligible comparison without survivor pooling."""
import experiment as e
from pathlib import Path
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
OUT = Path('D:/Pontius-training/river-abstraction-study')/e.NAME
ARCHIVE = e.HISTORY/e.NAME
REPORT = e.ROOT/'docs/research'/('river-stack-transfer-001.md')
plan, receipt, audit = [e.read(OUT/p) for p in ('plan.json', 'receipt.json', 'audit.json')]
assert receipt['exit'] == 0 and audit['passed'] and audit['evaluated'] == 1
assert e.digest(OUT/'plan.json') == e.read(HERE/'freeze.json')['plan_sha256']
assert e.digest(OUT/'results-manifest.json') == receipt['result_manifest_sha256']
for member, value in e.read(OUT/'results-manifest.json').items():
    assert e.digest(OUT/member) == value
e.bindings(plan)
rows = [e.read(OUT/f'case-{j:03d}.json') for j in range(4)]
eligible = [(j, r) for j, r in enumerate(rows) if r['status'] == 'evaluated']
assert [j for j, r in eligible] == [1]
row = rows[1]['result']
scores = dict(initial=row['initial']['exploitability'],
    repair=row['choices']['repair']['score']['exploitability'],
    continuation=row['choices']['continuation']['score']['exploitability'])
actual = {name: value*rows[1]['menu']['pot']/10 for name, value in scores.items()}
gain = 1-scores['repair']/scores['continuation']
summary = dict(census=4, applicable=1, structurally_inapplicable=3, evaluated_case=1,
    normalized_exploitability=scores, actual_chip_exploitability=actual,
    repair_relative_improvement=gain, pooled_mean=None,
    reason_no_pooling='No strategy comparison was run for structurally inapplicable cases',
    original_floor=row['original_solution']['floor'], proposed_floor=row['proposed_solution']['floor'])
previous = e.read(HERE/'preflight.json')['prior_milestones']
for name, expected in previous.items():
    folder = e.HISTORY/name
    assert e.digest(folder/'milestone-manifest.json') == expected
    for member, value in e.read(folder/'milestone-manifest.json').items():
        assert e.digest(folder/member) == value
before = e.read(HERE/'worktree-before.json')
for name, expected in before['modified_tracked_files'].items():
    assert e.digest(e.ROOT/name) == expected
git = ['C:/Program Files/Git/cmd/git.exe', '-c', f'safe.directory={e.ROOT}', '-C', str(e.ROOT)]
assert subprocess.check_output(git+['rev-parse', 'HEAD'], text=True).strip() == before['head']
assert not ARCHIVE.exists() and not REPORT.exists()
lines = ['# Actual river stack transfer 001', '',
    'Same four retained public ranges and group labels as blueprint-range-transfer-001.',
    'Actual pots, stack-capped legal sizes and seat-ordered odd-chip ties.', '',
    '## Domain census', '',
    '| Case | Pot | Remaining live stack | SPR | Requested sizes map to | Result |',
    '|---|---:|---:|---:|---|---|']
for j, item in enumerate(rows):
    menu = item['menu']
    lines.append(f"| {j} | {menu['pot']} | {menu['effective_stack']} | {menu['spr']:.4f} | "
                 f"{menu['sizes']} | {item['status']} |")
lines += ['', 'Three cases have only one distinct all-in size. The frozen size-choice repair is',
    'inapplicable there. No duplicate action labels, substituted bets, or replacement cases.',
    'These are structural outcomes, not missing runs or evaluated zero-gain observations.',
    'There is no four-case pooled exploitability or broad applicability-rate claim.', '',
    '## One eligible comparison', '',
    '| Policy | Normalized exploitability | Actual-chip exploitability |',
    '|---|---:|---:|']
for name, value in scores.items():
    lines.append(f'| {name} | {value:.9f} | {actual[name]:.9f} |')
lines += ['', f'Repair relative improvement over continuation: {gain:.3%}.',
    f"Repair gate accepted: {row['choices']['repair']['accepted']}.",
    f"Continuation gate accepted: {row['choices']['continuation']['accepted']}.",
    'Lower is better. Normalized values use payoff scaling 10/pot; actual-chip values undo it.',
    'This is restricted-game exploitability, not BB/100 or measured six-max win rate.', '',
    'Original grouping floor interval: '+str([float(e.b.e.Q(v)) for v in summary['original_floor']]),
    'Proposed grouping floor interval: '+str([float(e.b.e.Q(v)) for v in summary['proposed_floor']]),
    '', '## Procedure and cost', '',
    'The frozen predecessor learner, proposal, exact gate, and full-combo verifier are reused.',
    'Both incumbent roles receive 50000 updates. Caller then stays fixed. Repair retrains only',
    'the bettor for 50000 updates. Continuation reconstructs the incumbent learner and receives',
    'additional 250-update blocks until its measured work covers repair work, with the same',
    'predeclared cap. Witness/proposal and setup count; gates are reported separately.',
    f"Continuation stopped at {row['continued']['iteration']} total bettor updates.",
    f"Repair work {row['times']['repair_work']:.6f}s; gate {row['times']['repair_gate']:.6f}s.",
    f"Continuation work {row['continued']['seconds']:.6f}s; "
    f"gate {row['times']['continuation_gate']:.6f}s.", '',
    'One timing observation, repair first. These times are not a stable speed benchmark.', '',
    '## Scope and interpretation', '',
    'The three collapsed-size cases include case 3, responsible for most of the preceding',
    'normalized-game improvement. That earlier gain cannot be assumed to survive their',
    'actual stacks: the mechanism needs two distinct bet sizes, which those states lack.',
    'Only case 1 is eligible here. Its outcome alone cannot establish generalization.',
    'This does not imply single-size river states need no solving or no grouping improvement.', '',
    'The retained public ranges remain dominated by early-checkpoint postflop fallbacks.',
    'Raw/effective weights and their floor are unchanged. Folded-player cards are not jointly',
    'marginalized. All 1081 board-legal combos and collision-compatible deals remain represented.',
    'The restricted tree omits caller betting after a check, reraises and other legal sizes.',
    'An actual-pot payoff adapter does not turn this into a full engine-state solution.', '',
    '## Verification and retention', '',
    'Four adapter tests, sixty engine settlements covering wins/ties/losses and check/fold/call.',
    'The engine rounds a half-pot bet of 14.5 to 14. Odd pots give the lower seat the odd chip;',
    'ties therefore retain a centered +/-0.5 payoff, rather than silently rounding to zero.',
    f"Fresh replay: {audit['replayed_updates']} updates; "
    f"{audit['exact_coefficients']} coefficients checked; three certificate pairs; two gates.",
    'No new verifier LP solves. Previous source, group and range identities verified.',
    f"Worker plus verifier: {receipt['seconds']:.3f}s; exit 0.",
    'Python 3.14.6, one BLAS thread, no tracing, 1800s timeout per phase, no hard RSS cap.',
    f'All {len(previous)} prior milestones preserved. No production edits, commit or push.', '',
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
for member, value in manifest.items():
    assert e.digest(ARCHIVE/member) == value
index = e.ROOT/'docs/research/README.md'
old = index.read_bytes()
index.write_bytes(old+('\n## Actual river stacks\n\n'
    '[Stack transfer 001](river-stack-transfer-001.md) checks actual-pot applicability and\n'
    'the eligible size-repair comparison on the four retained blueprint-range cases.\n').encode())
assert index.read_bytes().startswith(old)
e.write(HERE/'retention.json', dict(report=str(REPORT), archive=str(ARCHIVE),
    members=len(manifest), manifest_sha256=e.digest(ARCHIVE/'milestone-manifest.json'),
    previous_milestones_preserved=len(previous), committed=False, pushed=False))
print(e.read(HERE/'retention.json'))
print(summary)
