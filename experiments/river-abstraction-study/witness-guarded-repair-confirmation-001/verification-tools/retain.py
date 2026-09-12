"""Independent summary audit, measured costs, and immutable milestone retention."""
from pathlib import Path
from fractions import Fraction as Q
from collections import Counter
from statistics import median
from hashlib import sha256
import json
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = Path('D:/Pontius-worktrees/eval-runner-consolidation')
NAME = 'witness-guarded-repair-confirmation-001'
OUT = Path('D:/Pontius-training/river-abstraction-study')/NAME
ARCHIVE = ROOT/'experiments/river-abstraction-study'/NAME
REPORT = ROOT/'docs/research/river-witness-guarded-repair-confirmation-001.md'
read = lambda p: json.loads(p.read_bytes())
digest = lambda p: sha256(p.read_bytes()).hexdigest()


def write(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as f:
        f.write(json.dumps(value, sort_keys=True, indent=2, allow_nan=False)+'\n')


def direction(value):
    return 'worse' if value > 0 else 'better' if value < 0 else 'equal'


plan, summary, audit, receipt = (read(OUT/p) for p in
    ('plan.json', 'summary.json', 'audit.json', 'receipt.json'))
worker, verifier = (read(OUT/p) for p in ('worker-receipt.json', 'verify-receipt.json'))
assert receipt['exit'] == worker['exit'] == verifier['exit'] == 0 and audit['passed']
assert audit['cases'] == 64 and audit['asymmetric_certificates'] == 256
assert audit['saved_profiles'] == 256 and audit['selected_profiles'] == 64
assert audit['replayed_updates'] == 3840000 and audit['independent_security_pairs'] == 128
assert audit['verifier_lp_calls'] == audit['model_fits'] == 0
assert digest(OUT/'results-manifest.json') == receipt['result_manifest_sha256']
assert digest(OUT/'plan.json') == read(HERE/'freeze.json')['plan_sha256']
assert not ARCHIVE.exists() and not REPORT.exists()
for name, expected in read(OUT/'results-manifest.json').items():
    assert digest(OUT/name) == expected, name
for name, expected in plan['pins'].items():
    assert digest(Path(name)) == expected, name
novelty = read(HERE/'novelty-audit.json')
assert novelty['passed'] and novelty['fresh_boards'] == 16
assert novelty['plan_sha256'] == digest(OUT/'plan.json')
rows = [read(OUT/f'case-{i:03d}.json') for i in range(64)]
assert [r['entry'] for r in rows] == plan['entries']
checks = 0
for row in rows:
    value = row['gate']
    pairs = [list(map(Q, pair)) for pair in value['security_exact']]
    accepted = [pairs[1][s] >= pairs[0][s] for s in (0, 1)]
    assert accepted == value['accepted']
    before, raw = [-sum(pair, Q(0))/2 for pair in pairs]
    selected = -sum((pairs[int(accepted[s])][s] for s in (0, 1)), Q(0))/2
    assert before == Q(row['records']['control'][0]['exact_exploitability'])
    assert raw == Q(row['records']['repaired'][1]['exact_exploitability'])
    assert selected == Q(row['selected_score']['exact_exploitability']) <= before
    for s in (0, 1):
        assert value['groups'][s] == (row['proposal']['groups'] if accepted[s]
                                     else row['baseline_groups'])[s]
        record = row['records']['repaired'][1] if accepted[s] else row['records']['control'][0]
        assert value['coefficients'][s] == record['coefficients'][s]
    checks += 8

analysis = {}
for bet, panel in summary['panels'].items():
    rs = [r for r in rows if r['entry']['bet'] == int(bet)]
    selections = [(panel['overall'], rs)]
    for category, key in [('boards', 'board_index'), ('textures', 'texture'),
                          ('regimes', 'regime'), ('leave_one_board_out', 'board_index')]:
        for label, value in panel[category].items():
            selections.append((value, [r for r in rs if
                (str(r['entry']['case'][key]) == label) != (category == 'leave_one_board_out')]))
    for value, subset in selections:
        n = len(subset)
        assert value['cases'] == n and n > 0
        means = {}
        for name, method, index in [('original10k', 'control', 0),
                                    ('original50k', 'control', 1), ('raw10k', 'repaired', 1)]:
            means[name] = sum(Q(r['records'][method][index]['exact_exploitability'])
                              for r in subset)/n
        means['guarded10k'] = sum(Q(r['selected_score']['exact_exploitability'])
                                 for r in subset)/n
        assert value['means_exact'] == {k: str(v) for k, v in means.items()}
        assert value['means'] == {k: float(v) for k, v in means.items()}
        assert Q(value['delta_exact']) == means['guarded10k']-means['original10k']
        assert Q(value['versus_50k_exact']) == means['guarded10k']-means['original50k']
        for kind in ('raw', 'guarded'):
            deltas = [Q((r['selected_score'] if kind == 'guarded' else
                         r['records']['repaired'][1])['exact_exploitability'])-
                      Q(r['records']['control'][0]['exact_exploitability']) for r in subset]
            assert value[kind+'_directions'] == dict(Counter(map(direction, deltas)))
        assert value['changed_seats'] == sum(s['changed'] for r in subset
                                              for s in r['proposal']['seats'])
        assert value['accepted_changed_seats'] == sum(r['gate']['accepted'][s] and
            r['proposal']['seats'][s]['changed'] for r in subset for s in (0, 1))
        assert value['mean_gate_seconds'] == sum(r['gate_seconds'] for r in subset)/n
        checks += 10
    value = panel['overall']
    means = {k: Q(v) for k, v in value['means_exact'].items()}
    analysis[bet] = dict(raw_reduction_percent=100*float(1-means['raw10k']/means['original10k']),
        guarded_reduction_percent=100*float(1-means['guarded10k']/means['original10k']),
        versus_50k_reduction_percent=100*float(1-means['guarded10k']/means['original50k']),
        board_directions=dict(Counter(direction(Q(v['delta_exact']))
                                      for v in panel['boards'].values())),
        leave_one_board_out_all_improve=all(Q(v['delta_exact']) < 0
                                           for v in panel['leave_one_board_out'].values()),
        all_textures_improve=all(Q(v['delta_exact']) < 0 for v in panel['textures'].values()),
        all_regimes_improve=all(Q(v['delta_exact']) < 0 for v in panel['regimes'].values()),
        raw_directions=value['raw_directions'], guarded_directions=value['guarded_directions'],
        changed_seats=value['changed_seats'],
        accepted_changed_seats=value['accepted_changed_seats'])
safe = all(Q(r['selected_score']['exact_exploitability']) <=
           Q(r['records']['control'][0]['exact_exploitability']) for r in rows)
assert summary['flags'] == dict(exact_nonregression=safe,
    useful_half_pot=safe and Q(summary['panels']['5']['overall']['delta_exact']) < -Q('1e-6'))

gate_times = [r['gate_seconds'] for r in rows]
components = {name: sum(r[field] for r in rows) for name, field in
    [('preparation', 'preparation_seconds'), ('baseline_witness', 'baseline_lp_seconds'),
     ('proposal', 'proposal_seconds'), ('acceptance', 'gate_seconds')]}
for name, method, index in [('original10k_solver', 'control', 0),
                           ('repaired10k_solver', 'repaired', 1)]:
    components[name] = sum(r['records'][method][index]['active_seconds']+
                           r['records'][method][index]['setup_seconds'] for r in rows)
component_total = sum(components.values())
costs = dict(total_component_seconds=component_total, components_total_seconds=components,
    mean_component_seconds=component_total/64, mean_gate_seconds=sum(gate_times)/64,
    median_gate_seconds=median(gate_times), min_gate_seconds=min(gate_times),
    max_gate_seconds=max(gate_times),
    gate_component_share_percent=100*sum(gate_times)/component_total,
    diagnostic_repaired_lp_seconds=sum(r['diagnostic_lp_seconds'] for r in rows),
    extra_original40k_update_seconds=sum(r['records']['control'][1]['active_seconds']-
        r['records']['control'][0]['active_seconds'] for r in rows),
    scope='Single-run component sums, not an independently timed standalone production launch.')
assert all(x >= 0 for x in components.values())

previous = {}
for directory in sorted(ARCHIVE.parent.iterdir()):
    path = directory/'milestone-manifest.json'
    if path.is_file():
        for name, expected in read(path).items():
            assert digest(directory/name) == expected, (directory, name)
        previous[directory.name] = digest(path)
assert len(previous) == 23
before = read(HERE/'worktree-before.json')
for name, expected in before['modified_tracked_files'].items():
    assert digest(ROOT/name) == expected, name
git = ['C:/Program Files/Git/cmd/git.exe', '-c', f'safe.directory={ROOT}', '-C', str(ROOT)]
assert subprocess.check_output(git+['rev-parse', 'HEAD'], text=True).strip() == before['head']

lines = ['# Guarded repair confirmation 001', '',
    'Prospective test on 16 new boards, four per texture, excluding all 68 prior',
    'board classes up to suit relabeling. The complete gate was frozen before any',
    'new-board scoring. No fitting, threshold tuning, or repaired-certificate input',
    'to acceptance. One fixed-capacity split/merge per role at 16 groups each.', '',
    '## Acceptance criteria', '', '| Criterion | Passed |', '|---|---|']
for key, value in summary['flags'].items():
    lines.append(f'| {key} | {value} |')
lines += ['', 'Every guarded profile must be no worse than original10k by exact comparison.',
    'Utility additionally requires mean half-pot difference below -1e-6 chips.',
    'These are fixed-panel criteria, not population confidence intervals.', '',
    '## Strategy results', '', 'Exploitability in chips; lower is better.', '',
    '| Bet | Original 10k | Raw repair 10k | Guarded 10k | Original 50k | Reduction % |',
    '|---|---:|---:|---:|---:|---:|']
for bet, panel in summary['panels'].items():
    v = panel['overall']['means']
    lines.append(f"| {bet} | {v['original10k']:.9f} | {v['raw10k']:.9f} | "
        f"{v['guarded10k']:.9f} | {v['original50k']:.9f} | "
        f"{analysis[bet]['guarded_reduction_percent']:.2f} |")
lines += ['', '| Bet | Raw better/equal/worse | Guarded better/equal/worse | Changed accepted |',
    '|---|---|---|---|']
for bet, value in analysis.items():
    triplet = lambda d: '/'.join(str(d.get(k, 0)) for k in ('better', 'equal', 'worse'))
    lines.append(f"| {bet} | {triplet(value['raw_directions'])} | "
        f"{triplet(value['guarded_directions'])} | "
        f"{value['accepted_changed_seats']}/{value['changed_seats']} |")
for category in ('boards', 'textures', 'regimes', 'leave_one_board_out'):
    lines += ['', '## '+category.replace('_', ' '), '',
              '| Bet | Panel | Guarded minus original10k |', '|---|---|---:|']
    for bet, panel in summary['panels'].items():
        for label, value in panel[category].items():
            lines.append(f"| {bet} | {label} | {float(Q(value['delta_exact'])):+.9f} |")
lines += ['', '## Measured cost', '',
    'One pass, one BLAS thread, allocation tracing disabled. Gate time includes',
    'two exact policy evaluations plus validation and selection. It excludes the',
    'independent selected-profile scoring and repaired diagnostic certificate.', '',
    f"Mean gate: {1000*costs['mean_gate_seconds']:.3f} ms; "
    f"median {1000*costs['median_gate_seconds']:.3f} ms; "
    f"range {1000*costs['min_gate_seconds']:.3f}-{1000*costs['max_gate_seconds']:.3f} ms.",
    f"Mean production-path component sum: {costs['mean_component_seconds']:.3f} s/case.",
    f"Gate share of that component sum: {costs['gate_component_share_percent']:.2f}%.", '',
    '| Component | Total seconds over 64 cases |', '|---|---:|']
for name, value in components.items():
    lines.append(f'| {name} | {value:.3f} |')
lines += ['', 'The component sum includes input preparation, original witness generation,',
    'proposal, original10k and repaired10k setup/updates, and acceptance. It excludes',
    'diagnostic scoring, original40k extra updates, repaired LP, serialization and',
    'verification. It is not an independently timed production invocation.',
    'Original50k compares iterations, not equal wall time or equal total work.', '',
    '## Verification and scope', '',
    '64 cases: 16 boards, one pool, two regimes, two bets; 96 holdings per seat.',
    'Pot 10, stacks 20/20, heads-up one-bet river. All compatible deals included.',
    'The model is unchanged, but each game still supplies its own offline witness.',
    'Exact saved-policy safety does not guarantee future retraining, approximate',
    'evaluators, multiway play, full ranges or BB/100 performance.', '',
    '20 preflight checks and four historical acceptance reproductions passed.',
    '256 asymmetric certificates, 256 saved profiles, and 64 selected profiles checked.',
    '3,840,000 solver updates replayed with verifier LP calls disabled.',
    '128 security pairs reconstructed with independent terminal-payoff sums.',
    f"Independent exchange enumerations: {audit['independently_enumerated_exchanges']:,}.",
    f'Independent aggregate and selection arithmetic checks: {checks+1}.',
    f"Worker {worker['seconds']:.3f} s; verifier {verifier['seconds']:.3f} s; "
    f"total {receipt['seconds']:.3f} s, exit 0.",
    'Python 3.14.6, NumPy 2.5.2, SciPy 1.18.0; 900 seconds per phase; no hard RSS cap.',
    'All 23 preceding milestone manifests and members verified unchanged.',
    'No production changes, adoption, commit, push or independent cold review.', '',
    'Plan SHA-256: '+digest(OUT/'plan.json'), '',
    'Results manifest SHA-256: '+receipt['result_manifest_sha256'], '']
write(OUT/'summary-audit.json', dict(passed=True, arithmetic_checks=checks+1,
    analysis=analysis, costs=costs))
with REPORT.open('x', encoding='utf-8', newline='\n') as f:
    f.write('\n'.join(lines))
shutil.copytree(OUT, ARCHIVE)
(ARCHIVE/'verification-tools').mkdir()
for path in sorted(HERE.iterdir()):
    if path.is_file() and path.name != 'plan.json':
        shutil.copyfile(path, ARCHIVE/'verification-tools'/path.name)
shutil.copyfile(REPORT, ARCHIVE/'report.md')
members = {p.relative_to(ARCHIVE).as_posix(): digest(p)
           for p in sorted(ARCHIVE.rglob('*')) if p.is_file()}
write(ARCHIVE/'milestone-manifest.json', members)
assert all(digest(ARCHIVE/k) == v for k, v in members.items())
overview = ROOT/'docs/research/README.md'
old = overview.read_bytes()
with (HERE/'research-readme-before.md').open('xb') as f:
    f.write(old)
with overview.open('ab') as f:
    f.write(b'\n## Guarded repair confirmation\n\n'
        b'[Guarded repair 001](river-witness-guarded-repair-confirmation-001.md)\n'
        b'tests the frozen per-role security gate on sixteen untouched boards.\n')
assert overview.read_bytes().startswith(old)
write(HERE/'retention.json', dict(passed=True, members=len(members), previous=previous,
    milestone_sha256=digest(ARCHIVE/'milestone-manifest.json'), report_sha256=digest(REPORT),
    source_head=before['head'], commit=False, push=False))
print(json.dumps(dict(flags=summary['flags'], analysis=analysis, costs=costs,
    milestone_sha256=digest(ARCHIVE/'milestone-manifest.json')), indent=2))
