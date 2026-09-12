"""Preserve the complete four-case pilot and all earlier named milestones."""
from pathlib import Path
import shutil
import subprocess
import experiment as e

HERE = Path(__file__).resolve().parent
OUT = Path('D:/Pontius-training/river-abstraction-study')/e.NAME
ARCHIVE = e.HISTORY/e.NAME
REPORT = e.ROOT/'docs/research'/('river-'+e.NAME+'.md')
plan, receipt, audit = (e.read(OUT/p) for p in ('plan.json', 'receipt.json', 'audit.json'))
assert receipt['exit'] == 0 and audit['passed'] and audit['cases'] == 4
assert e.digest(OUT/'plan.json') == e.read(HERE/'freeze.json')['plan_sha256']
assert e.digest(OUT/'results-manifest.json') == receipt['result_manifest_sha256']
for name, expected in e.read(OUT/'results-manifest.json').items():
    assert e.digest(OUT/name) == expected
e.bindings(plan)
rows = [e.read(OUT/f'case-{j:03d}.json') for j in range(4)]
inputs = [e.read(OUT/f'input-{j:03d}.json') for j in range(4)]
corpus = e.read(OUT/'capture.json')
summary = dict(cases=4, capture_census=corpus['census'],
               capture_policy_statuses=corpus['policy_statuses'], modes={})
for mode in ('initial', 'repair', 'continuation'):
    scores = [r['initial']['exploitability'] if mode == 'initial' else
              r['choices'][mode]['score']['exploitability'] for r in rows]
    summary['modes'][mode] = dict(mean_exploitability=sum(scores)/4, cases=scores)
    if mode != 'initial':
        summary['modes'][mode]['accepted'] = sum(r['choices'][mode]['accepted'] for r in rows)
summary['repair_strictly_better_than_continuation'] = sum(
    e.Q(r['choices']['repair']['score']['exploitability_exact']) <
    e.Q(r['choices']['continuation']['score']['exploitability_exact']) for r in rows)
summary['repair_grouping_changed'] = sum(r['proposal']['groups'] != r['groups'][0] for r in rows)
summary['equal_weight_scope'] = 'Four reached states; normalized game, full-combo factorized ranges'
summary['range_records'] = [v['ranges'] for v in inputs]
summary['timing'] = {name: sum(values)/4 for name, values in {
    'range_build': [r['range_seconds'] for r in rows],
    'initial_both_roles': [r['times']['initial_both_roles'] for r in rows],
    'repair_with_gate': [r['times']['repair_work']+r['times']['repair_gate'] for r in rows],
    'continuation_with_gate': [r['continued']['seconds']+
                              r['times']['continuation_gate'] for r in rows]}.items()}
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

lines = ['# Blueprint range transfer 001', '',
    'Four first eligible heads-up river starts reached by baseline-000 six-max self-play.',
    'Full 1081-combo public ranges; frozen K=16 size repair; no model fitting.', '',
    '## Outcomes', '', '| Policy | Mean exploitability (normalized chips) | Accepted |',
    '|---|---:|---:|']
for mode, value in summary['modes'].items():
    lines.append(f"| {mode} | {value['mean_exploitability']:.9f} | "
                 f"{value.get('accepted', '-')} |")
lines += ['', '| Case | Source hand | Board (card ids) | Initial | Repair | Continuation |',
    '|---|---:|---|---:|---:|---:|']
for j, (row, data) in enumerate(zip(rows, inputs)):
    vals = [summary['modes'][mode]['cases'][j] for mode in ('initial', 'repair', 'continuation')]
    lines.append(f"| {j} | {data['actual_state']['hand_index']} | {data['board']} | "+
                 ' | '.join(f'{v:.9f}' for v in vals)+' |')
lines += ['', 'Exploitability is half the exact unrestricted-response gap in the normalized',
    'heads-up check/half-pot/pot game. Lower is better. The caller is fixed after 50000',
    'incumbent updates; both alternatives must pass the same exact nonworse security gate.',
    f"Repair strictly beats continuation in {summary['repair_strictly_better_than_continuation']}/4 cases.",
    f"The proposal changes grouping in {summary['repair_grouping_changed']}/4 cases.", '',
    '## Grouping floor intervals', '',
    '| Case | Original lower | Original upper | Proposed lower | Proposed upper |',
    '|---|---:|---:|---:|---:|']
for j, row in enumerate(rows):
    vals = [float(e.Q(v)) for key in ('original_solution', 'proposed_solution')
            for v in row[key]['floor']]
    lines.append(f'| {j} | '+' | '.join(f'{v:.9f}' for v in vals)+' |')
lines += ['', 'These separate representational limits from remaining optimization error.',
    'Each interval combines two primal/dual certificates, checked against the original',
    'binary64 full-game coefficients with exact rationals and gap at most 1e-8.', '',
    '## Acquisition and range provenance', '',
    f"Capture census: `{corpus['census']}`.",
    f"Captured policy decisions by street/status: `{corpus['policy_statuses']}`.", '',
    '| Case | Role/seat | Trained observations | Fallback observations | Uniform observations |',
    '|---|---|---:|---:|---:|']
for j, data in enumerate(inputs):
    for role, item in zip(('bettor', 'caller'), data['ranges']):
        p = item['provenance']
        lines.append(f"| {j} | {role}/{item['seat']} | {p['trained_frac']:.3%} | "
                     f"{p['fallback_frac']:.3%} | {p['uniform_frac']:.3%} |")
lines += ['', 'Percentages count combo-by-action observations, not policy queries.', '',
    '| Case | Seat | Raw zeros | Collapsed | Floor mass added | Lower-floor L1 |',
    '|---|---:|---:|---|---:|---:|']
for j, data in enumerate(inputs):
    for item in data['ranges']:
        st = item['stats']
        lines.append(f"| {j} | {item['seat']} | {st['raw_zeros']} | {st['collapsed']} | "
                     f"{st['floor_mass_added']:.8g} | {item['lower_floor_l1']:.8g} |")
lines += ['', 'Raw and effective ranges are retained. Primary floor 1e-6; the 1e-9 diagnostic',
    'compares range vectors only, not alternative solved policies. No fallback or collapsed',
    'range is deleted. Pairwise collision rejection yields 1070190 ordered legal deals per case.',
    'Folded players are not jointly marginalized. These are factorized public ranges.', '',
    '## Timing and limits', '',
    '| Case | Range build s | Initial both roles s | Repair plus gate s | Continued plus gate s |',
    '|---|---:|---:|---:|---:|']
for j, row in enumerate(rows):
    t = row['times']
    lines.append(f"| {j} | {row['range_seconds']:.3f} | {t['initial_both_roles']:.3f} | "
                 f"{t['repair_work']+t['repair_gate']:.3f} | "
                 f"{row['continued']['seconds']+t['continuation_gate']:.3f} |")
lines += ['', 'Continuation stops at the first 250-update block covering measured repair work.',
    'Witness, proposal, setup, updates and averaging count. Gates are excluded from matching',
    'and included in the table. Source range acquisition and exact-kernel setup are shared',
    'preparation. Caller/proposed certificates and verifier replay are research diagnostics.',
    'One timing sample per case; fixed repair-first ordering is not a stable speed benchmark.', '',
    'Actual source pots/stacks/history are retained but not used as the solved payoff game.',
    'This changes both range source and pool size from the prior 96-hand synthetic studies.',
    'It cannot isolate range shape from compression ratio or imply six-max playing strength.',
    'Four reached states are an exploratory panel, not a broad board-distribution estimate.',
    'Conditional payoff evaluation enumerates all deals, so it has no Monte Carlo hand noise.', '',
    '## Verification', '',
    f"Eight preflight tests; {audit['exact_coefficients_checked']} coefficients checked by integer ratios;",
    f"{audit['replayed_updates']} learner updates replayed; twelve literal subgame comparisons;",
    'capture repeated exactly; all four ranges replayed and tested with different private cards;',
    'twelve asymmetric certificate pairs and eight gates reverified without new LP solves.',
    'Python 3.14.6; one BLAS thread; no tracing; 1800 seconds per phase; no hard RSS cap.',
    f"Worker plus verification: {receipt['seconds']:.3f} seconds, exit 0.",
    f'All {len(previous)} prior milestone manifests and members preserved unchanged.',
    'No production changes, checkpoint training, commit or push.', '',
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
for name, expected in manifest.items():
    assert e.digest(ARCHIVE/name) == expected
index = e.ROOT/'docs/research/README.md'
old = index.read_bytes()
addition = ('\n## Blueprint public-range transfer\n\n'
    '[Transfer pilot 001](river-blueprint-range-transfer-001.md) tests the frozen size repair\n'
    'on four reached river states with all 1081 combos and public-history range provenance.\n')
index.write_bytes(old+addition.encode())
assert index.read_bytes().startswith(old)
e.write(HERE/'retention.json', dict(report=str(REPORT), archive=str(ARCHIVE),
    manifest_sha256=e.digest(ARCHIVE/'milestone-manifest.json'), members=len(manifest),
    preserved_prior_milestones=len(previous), committed=False, pushed=False))
print(e.read(HERE/'retention.json'))
print({k: v for k, v in summary.items() if k not in ('range_records',)})
