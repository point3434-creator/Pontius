"""Audit second-step comparisons and preserve the complete milestone."""
from pathlib import Path
from fractions import Fraction as Q
from collections import Counter
from hashlib import sha256
from statistics import median
import json
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = Path('D:/Pontius-worktrees/eval-runner-consolidation')
NAME = 'witness-second-guarded-repair-001'
OUT = Path('D:/Pontius-training/river-abstraction-study')/NAME
ARCHIVE = ROOT/'experiments/river-abstraction-study'/NAME
REPORT = ROOT/'docs/research/river-witness-second-guarded-repair-001.md'
read = lambda p: json.loads(p.read_bytes())
digest = lambda p: sha256(p.read_bytes()).hexdigest()


def write(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as f:
        f.write(json.dumps(value, sort_keys=True, indent=2, allow_nan=False)+'\n')


def values(row):
    return dict(original10k=Q(row['original10k']),
        incumbent=Q(row['incumbent_score']['exact_exploitability']),
        raw_second=Q(row['records']['repaired'][1]['exact_exploitability']),
        second=Q(row['second_score']['exact_exploitability']),
        continuation=Q(row['continuation_score']['exact_exploitability']))


def direction(x):
    return 'better' if x < 0 else 'worse' if x > 0 else 'equal'


plan, summary, audit, receipt = (read(OUT/p) for p in
    ('plan.json', 'summary.json', 'audit.json', 'receipt.json'))
worker, verifier = (read(OUT/p) for p in ('worker-receipt.json', 'verify-receipt.json'))
assert receipt['exit'] == worker['exit'] == verifier['exit'] == 0 and audit['passed']
assert audit['cases'] == audit['retained_incumbents'] == 64
assert audit['asymmetric_certificates'] == audit['saved_profiles'] == 256
assert audit['selected_profiles'] == audit['independent_gate_audits'] == 128
assert audit['replayed_updates'] == 1920000 and audit['verifier_lp_calls'] == 0
assert digest(OUT/'plan.json') == read(HERE/'freeze.json')['plan_sha256']
assert digest(OUT/'results-manifest.json') == receipt['result_manifest_sha256']
for name, expected in read(OUT/'results-manifest.json').items():
    assert digest(OUT/name) == expected, name
for name, expected in plan['pins'].items():
    assert digest(Path(name)) == expected, name
assert not ARCHIVE.exists() and not REPORT.exists()
rows = [read(OUT/f'case-{i:03d}.json') for i in range(64)]
checks = 0
for row, path in zip(rows, plan['sources'], strict=True):
    source = read(Path(path))
    assert row['source_path'] == path and row['source_sha256'] == digest(Path(path))
    assert row['incumbent_groups'] == source['gate']['groups']
    assert row['incumbent_coefficients'] == source['gate']['coefficients']
    assert row['incumbent_score'] == source['selected_score']
    assert row['original10k'] == source['records']['control'][0]['exact_exploitability']
    for name, score_name, candidate in [('repair', 'second_score', row['records']['repaired'][1]),
                                       ('continuation', 'continuation_score',
                                        row['records']['control'][1])]:
        g = row[name+'_gate']
        pair = [list(map(Q, p)) for p in g['security_exact']]
        selected = [pair[1][s] >= pair[0][s] for s in (0, 1)]
        assert g['accepted'] == selected
        assert -sum(pair[0], Q(0))/2 == Q(row['incumbent_score']['exact_exploitability'])
        assert -sum(pair[1], Q(0))/2 == Q(candidate['exact_exploitability'])
        result = -sum((pair[int(selected[s])][s] for s in (0, 1)), Q(0))/2
        assert result == Q(row[score_name]['exact_exploitability']) <= Q(
            row['incumbent_score']['exact_exploitability'])
        proposed_groups = row['proposal']['groups'] if name == 'repair' else row['incumbent_groups']
        for s in (0, 1):
            expected_groups = proposed_groups if selected[s] else row['incumbent_groups']
            assert g['groups'][s] == expected_groups[s]
            assert g['coefficients'][s] == (candidate['coefficients'] if selected[s]
                                            else row['incumbent_coefficients'])[s]
        checks += 8
    assert row['records']['control'][0]['coefficients'] == row['incumbent_coefficients']
    checks += 6

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
        vs = [values(r) for r in subset]
        assert len(vs) == value['cases'] and vs
        means = {k: sum(v[k] for v in vs)/len(vs) for k in vs[0]}
        assert value['means_exact'] == {k: str(v) for k, v in means.items()}
        assert value['means'] == {k: float(v) for k, v in means.items()}
        assert Q(value['delta_exact']) == means['second']-means['incumbent']
        assert Q(value['versus_continuation_exact']) == means['second']-means['continuation']
        for key, method, reference in [('raw_directions', 'raw_second', 'incumbent'),
            ('second_directions', 'second', 'incumbent'),
            ('continuation_directions', 'continuation', 'incumbent'),
            ('versus_continuation_directions', 'second', 'continuation')]:
            assert value[key] == dict(Counter(direction(v[method]-v[reference]) for v in vs))
        assert value['changed_seats'] == sum(s['changed'] for r in subset
                                              for s in r['proposal']['seats'])
        assert value['accepted_changed_seats'] == sum(r['repair_gate']['accepted'][s] and
            r['proposal']['seats'][s]['changed'] for r in subset for s in (0, 1))
        checks += 11
    value = panel['overall']
    means = {k: Q(v) for k, v in value['means_exact'].items()}
    analysis[bet] = dict(second_reduction_percent=100*float(1-means['second']/means['incumbent']),
        continuation_reduction_percent=100*float(1-means['continuation']/means['incumbent']),
        versus_continuation_reduction_percent=100*float(1-means['second']/means['continuation']),
        total_reduction_from_original_percent=100*float(1-means['second']/means['original10k']),
        raw_directions=value['raw_directions'], second_directions=value['second_directions'],
        continuation_directions=value['continuation_directions'],
        versus_continuation_directions=value['versus_continuation_directions'],
        changed_seats=value['changed_seats'],
        accepted_changed_seats=value['accepted_changed_seats'],
        board_directions=dict(Counter(direction(Q(v['delta_exact']))
                                      for v in panel['boards'].values())),
        boards_versus_continuation=dict(Counter(direction(Q(v['versus_continuation_exact']))
                                               for v in panel['boards'].values())),
        lobo_beats_continuation=all(Q(v['versus_continuation_exact']) < 0
                                  for v in panel['leave_one_board_out'].values()))
safe = all(v['second'] <= v['incumbent'] and v['continuation'] <= v['incumbent']
           for v in map(values, rows))
primary = summary['panels']['5']['overall']
assert summary['flags'] == dict(exact_nonregression=safe,
    useful_second_half_pot=safe and Q(primary['delta_exact']) < -Q('1e-6'),
    beats_continuation_half_pot=safe and Q(primary['versus_continuation_exact']) < -Q('1e-6'))

costs = {}
for bet in (5, 10):
    rs = [r for r in rows if r['entry']['bet'] == bet]
    parts = {label: sum(r[field] for r in rs) for label, field in
        [('witness', 'baseline_lp_seconds'), ('proposal', 'proposal_seconds'),
         ('repair_gate', 'gate_seconds'), ('continuation_gate', 'continuation_gate_seconds'),
         ('continuation_updates', 'continuation_update_seconds')]}
    parts['repair_training'] = sum(r['records']['repaired'][1]['setup_seconds']+
                                   r['records']['repaired'][1]['active_seconds'] for r in rs)
    repair = sum(parts[k] for k in ('witness', 'proposal', 'repair_gate', 'repair_training'))
    continued = parts['continuation_gate']+parts['continuation_updates']
    for r in rs:
        assert r['continuation_update_seconds'] == (r['records']['control'][1]['active_seconds']-
                                                    r['records']['control'][0]['active_seconds'])
    costs[str(bet)] = dict(component_totals=parts, mean_second_seconds=repair/len(rs),
        mean_continuation_seconds=continued/len(rs), second_to_continuation_ratio=repair/continued,
        mean_second_gate_seconds=parts['repair_gate']/len(rs))

previous = {}
for directory in sorted(ARCHIVE.parent.iterdir()):
    path = directory/'milestone-manifest.json'
    if path.is_file():
        for name, expected in read(path).items():
            assert digest(directory/name) == expected, (directory, name)
        previous[directory.name] = digest(path)
assert len(previous) == 24
before = read(HERE/'worktree-before.json')
for name, expected in before['modified_tracked_files'].items():
    assert digest(ROOT/name) == expected, name
git = ['C:/Program Files/Git/cmd/git.exe', '-c', f'safe.directory={ROOT}', '-C', str(ROOT)]
assert subprocess.check_output(git+['rev-parse', 'HEAD'], text=True).strip() == before['head']

lines = ['# Second guarded repair 001', '',
    'Full-panel follow-up using all 64 accepted first-step states. Sixteen existing',
    'boards, two bets and two regimes; no selection by first-step gain. Second-step',
    'rules were frozen before their outcomes. This is not a fresh-board replication.',
    'Both alternatives use the same per-role security gate against the incumbent.', '',
    '## Frozen criteria', '', '| Criterion | Passed |', '|---|---|']
for name, value in summary['flags'].items():
    lines.append(f'| {name} | {value} |')
lines += ['', 'Safety requires both alternatives never worsen the retained first step.',
    'Usefulness requires a half-pot mean gain exceeding 1e-6 chips; the additional',
    'continuation criterion compares the second repair against gated continuation.',
    'These are descriptive fixed-panel criteria, not population confidence intervals.', '',
    '## Exploitability', '', 'Chips, lower is better.',
    'All values use exact-hand best responses.', '',
    '| Bet | First step | Continue to 20k, gated | Second repair, gated | Original 10k |',
    '|---|---:|---:|---:|---:|']
for bet, panel in summary['panels'].items():
    v = panel['overall']['means']
    lines.append(f"| {bet} | {v['incumbent']:.9f} | {v['continuation']:.9f} | "
        f"{v['second']:.9f} | {v['original10k']:.9f} |")
lines += ['', '| Bet | Second-step gain % | Continuation gain % | Gain vs continuation % |',
          '|---|---:|---:|---:|']
for bet, v in analysis.items():
    lines.append(f"| {bet} | {v['second_reduction_percent']:.2f} | "
        f"{v['continuation_reduction_percent']:.2f} | "
        f"{v['versus_continuation_reduction_percent']:.2f} |")
lines += ['', '| Bet | Comparison | Better/equal/worse cases |', '|---|---|---|']
for bet, v in analysis.items():
    for name in ('raw_directions', 'second_directions', 'continuation_directions',
                 'versus_continuation_directions'):
        counts = '/'.join(str(v[name].get(k, 0)) for k in ('better', 'equal', 'worse'))
        lines.append(f'| {bet} | {name} | {counts} |')
    lines.append(f"| {bet} | Changed seats accepted | "
        f"{v['accepted_changed_seats']}/{v['changed_seats']} |")
for category in ('boards', 'textures', 'regimes', 'leave_one_board_out'):
    lines += ['', '## '+category.replace('_', ' '), '',
        '| Bet | Panel | Second minus first | Second minus continuation |', '|---|---|---:|---:|']
    for bet, panel in summary['panels'].items():
        for label, value in panel[category].items():
            lines.append(f"| {bet} | {label} | {float(Q(value['delta_exact'])):+.9f} | "
                f"{float(Q(value['versus_continuation_exact'])):+.9f} |")
lines += ['', '## Incremental computation', '',
    '| Bet | Second step seconds/case | Continuation seconds/case | Cost ratio |',
    '|---|---:|---:|---:|']
for bet, v in costs.items():
    lines.append(f"| {bet} | {v['mean_second_seconds']:.4f} | "
        f"{v['mean_continuation_seconds']:.4f} | {v['second_to_continuation_ratio']:.2f} |")
lines += ['', 'Second-step components include a newly computed witness, proposal, fresh',
    '10k training setup/updates and its gate. Continuation includes only additional',
    'updates from 10k to 20k plus its gate. Both use an additional 10k updates per',
    'role; these are not equal-CPU arms. The first 10k control updates reconstruct',
    'the retained state and are excluded from incremental cost. Input reconstruction,',
    'checkpoint scores, diagnostic repaired LP, I/O and verification are also excluded.',
    'These single-run component sums are not standalone production benchmarks.', '',
    '## Verification and limits', '',
    '15 preflight checks passed; four retained first-step policies reproduced before freeze.',
    'All 64 accepted incumbents reconstructed, preserving per-role fallback choices.',
    '256 new asymmetric certificates, 256 saved profiles, 128 selected profiles checked.',
    '1,920,000 updates replayed; 128 independent gate audits; verifier LP calls forbidden.',
    f"Independent exchange enumerations: {audit['independently_enumerated_exchanges']:,}.",
    f'Independent selection and summary arithmetic checks: {checks+1}.',
    f"Worker {worker['seconds']:.3f} s; verifier {verifier['seconds']:.3f} s; "
    f"total {receipt['seconds']:.3f} s, exit 0.",
    'Python 3.14.6, NumPy 2.5.2, SciPy 1.18.0, one BLAS thread, no allocation tracing.',
    '900-second limit per phase; no hard RSS cap. No model fitting.',
    'Heads-up one-bet river, 96 holdings per role, K=16; every compatible deal included.',
    'No full-range, six-max, live latency, population uncertainty or BB/100 claim.',
    'All 24 predecessor milestones verified unchanged; no adoption, commit or push.', '',
    'Plan SHA-256: '+digest(OUT/'plan.json'), '',
    'Results manifest SHA-256: '+receipt['result_manifest_sha256'], '']
write(OUT/'summary-audit.json', dict(passed=True, arithmetic_checks=checks+1,
    analysis=analysis, incremental_costs=costs))
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
    f.write(b'\n## Second guarded repair\n\n'
        b'[Second guarded repair 001](river-witness-second-guarded-repair-001.md)\n'
        b'compares another repair with guarded continuation on all retained first-step states.\n')
assert overview.read_bytes().startswith(old)
write(HERE/'retention.json', dict(passed=True, members=len(members), previous=previous,
    milestone_sha256=digest(ARCHIVE/'milestone-manifest.json'), report_sha256=digest(REPORT),
    source_head=before['head'], commit=False, push=False))
print(json.dumps(dict(flags=summary['flags'], analysis=analysis, costs=costs,
    milestone_sha256=digest(ARCHIVE/'milestone-manifest.json')), indent=2))
