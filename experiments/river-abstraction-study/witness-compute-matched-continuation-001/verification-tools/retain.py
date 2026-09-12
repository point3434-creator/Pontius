"""Independent arithmetic audit and immutable local retention."""
from pathlib import Path
from fractions import Fraction as Q
from collections import Counter
from hashlib import sha256
import json
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = Path('D:/Pontius-worktrees/eval-runner-consolidation')
NAME = 'witness-compute-matched-continuation-001'
OUT = Path('D:/Pontius-training/river-abstraction-study')/NAME
ARCHIVE = ROOT/'experiments/river-abstraction-study'/NAME
REPORT = ROOT/'docs/research'/('river-'+NAME+'.md')
read = lambda p: json.loads(p.read_bytes())
digest = lambda p: sha256(p.read_bytes()).hexdigest()


def write(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as f:
        f.write(json.dumps(value, sort_keys=True, indent=2, allow_nan=False)+'\n')


def values(row):
    return dict(incumbent=Q(row['incumbent_score']['exact_exploitability']),
        repair=Q(row['repair_score']['exact_exploitability']),
        **{k: Q(row['records'][k]['selected_score']['exact_exploitability'])
           for k in ('matched', 'generous')})


def direction(x):
    return 'better' if x < 0 else 'worse' if x > 0 else 'equal'


plan, summary, audit, receipt = (read(OUT/p) for p in
    ('plan.json', 'summary.json', 'audit.json', 'receipt.json'))
worker, verifier = (read(OUT/p) for p in ('worker-receipt.json', 'verify-receipt.json'))
assert receipt['exit'] == worker['exit'] == verifier['exit'] == 0 and audit['passed']
assert audit['cases'] == audit['timing_traces'] == 64
for k in ('asymmetric_certificates', 'raw_profiles', 'selected_profiles',
          'retained_reference_profiles', 'independent_gate_audits'):
    assert audit[k] == 128
assert audit['new_lp_calls'] == 0
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
    assert row['incumbent_score'] == source['incumbent_score']
    assert row['repair_score'] == source['second_score']
    assert row['grouping_floor'] == source['baseline']['minimum_exploitability']
    train = source['records']['repaired'][1]
    work = source['baseline_lp_seconds']+source['proposal_seconds']
    work += train['setup_seconds']+train['active_seconds']
    assert row['budgets'] == dict(work_seconds=work,
                                total_seconds=work+source['gate_seconds'])
    for name in ('matched', 'generous'):
        point = row['records'][name]
        g = point['gate']
        pair = [list(map(Q, p)) for p in g['security_exact']]
        selected = [pair[1][s] >= pair[0][s] for s in (0, 1)]
        assert g['accepted'] == selected
        assert -sum(pair[0], Q(0))/2 == Q(row['incumbent_score']['exact_exploitability'])
        assert -sum(pair[1], Q(0))/2 == Q(point['raw']['exact_exploitability'])
        result = -sum((pair[int(selected[s])][s] for s in (0, 1)), Q(0))/2
        assert result == values(row)[name] <= values(row)['incumbent']
        assert result >= Q(row['grouping_floor']['lower_exact'])
        assert g['groups'] == source['incumbent_groups']
        for s in (0, 1):
            assert g['coefficients'][s] == (point['coefficients'] if selected[s]
                                           else source['incumbent_coefficients'])[s]
        assert point['total_component_seconds'] == point['active_seconds']+point['gate_seconds']
        checks += 10
    assert row['records']['matched']['active_seconds'] <= work
    assert row['records']['generous']['active_seconds'] >= row['budgets']['total_seconds']
    assert row['records']['generous']['total_component_seconds'] >= row['budgets']['total_seconds']
    checks += 8
assert audit['replayed_updates'] == sum(r['records']['generous']['iteration'] for r in rows)

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
        means = {k: sum((v[k] for v in vs), Q(0))/len(vs) for k in vs[0]}
        assert value['means_exact'] == {k: str(v) for k, v in means.items()}
        assert value['means'] == {k: float(v) for k, v in means.items()}
        assert value['floor_interval'] == [str(sum((Q(r['grouping_floor'][k])
            for r in subset), Q(0))/len(subset)) for k in ('lower_exact', 'upper_exact')]
        for name in ('matched', 'generous'):
            assert Q(value['repair_minus_'+name]) == means['repair']-means[name]
            for a, b in [('repair', name), (name, 'incumbent')]:
                assert value[a+'_vs_'+b] == dict(Counter(direction(v[a]-v[b]) for v in vs))
            assert value['mean_total_ratios'][name] == sum(
                r['records'][name]['total_component_seconds'] for r in subset)/sum(
                r['budgets']['total_seconds'] for r in subset)
            assert value['mean_extra_iterations'][name] == sum(
                r['records'][name]['iteration']-10000 for r in subset)/len(subset)
        assert value['repair_below_floor_cases'] == sum(v['repair'] < Q(
            r['grouping_floor']['lower_exact'])-Q('1e-8') for r, v in zip(subset, vs))
        checks += 16
    v = panel['overall']
    means = {k: Q(x) for k, x in v['means_exact'].items()}
    ratios = {k: [r['records'][k]['total_component_seconds']/r['budgets']['total_seconds']
                  for r in rs] for k in ('matched', 'generous')}
    analysis[bet] = dict(means=v['means'],
        repair_gain_percent={k: 100*float(1-means['repair']/means[k])
                             for k in ('matched', 'generous')},
        continuation_gain_percent={k: 100*float(1-means[k]/means['incumbent'])
                                   for k in ('matched', 'generous')},
        mean_group_floor=float(Q(v['floor_interval'][0])),
        repair_below_floor_cases=v['repair_below_floor_cases'],
        mean_total_ratios=v['mean_total_ratios'],
        ratio_ranges={k: [min(x), max(x)] for k, x in ratios.items()},
        matched_over_budget_cases=sum(x > 1 for x in ratios['matched']),
        mean_extra_iterations=v['mean_extra_iterations'],
        extra_iteration_ranges={k: [min(r['records'][k]['iteration']-10000 for r in rs),
            max(r['records'][k]['iteration']-10000 for r in rs)] for k in ratios},
        mean_reference_seconds=sum(r['budgets']['total_seconds'] for r in rs)/len(rs),
        mean_actual_seconds={k: sum(r['records'][k]['total_component_seconds']
            for r in rs)/len(rs) for k in ratios},
        versus_generous=v['repair_vs_generous'], versus_matched=v['repair_vs_matched'],
        board_directions={k: dict(Counter(direction(Q(p['repair_minus_'+k]))
            for p in panel['boards'].values())) for k in ratios},
        lobo_beats_generous=all(Q(p['repair_minus_generous']) < 0
                               for p in panel['leave_one_board_out'].values()))
safe = all(v['matched'] <= v['incumbent'] and v['generous'] <= v['incumbent']
           for v in map(values, rows))
half = summary['panels']['5']['overall']
assert summary['flags'] == dict(continuation_nonregression=safe,
    beats_matched_half_pot=Q(half['repair_minus_matched']) < -Q('1e-6'),
    beats_generous_half_pot=Q(half['repair_minus_generous']) < -Q('1e-6'))
previous = {}
for directory in sorted(ARCHIVE.parent.iterdir()):
    path = directory/'milestone-manifest.json'
    if path.is_file():
        for name, expected in read(path).items():
            assert digest(directory/name) == expected, (directory, name)
        previous[directory.name] = digest(path)
assert previous == read(HERE/'preflight.json')['prior_milestones'] and len(previous) == 25
before = read(HERE/'worktree-before.json')
for name, expected in before['modified_tracked_files'].items():
    assert digest(ROOT/name) == expected, name
git = ['C:/Program Files/Git/cmd/git.exe', '-c', f'safe.directory={ROOT}', '-C', str(ROOT)]
assert subprocess.check_output(git+['rev-parse', 'HEAD'], text=True).strip() == before['head']

lines = ['# Compute-matched continuation 001', '',
    'All 64 retained cases: 16 existing boards, two regimes, two bets. Lower exact-hand',
    'exploitability is better. This follow-up controls computation; it adds no fresh boards.', '',
    '| Bet | Incumbent | Matched continuation | Generous continuation | Second repair |',
    '|---|---:|---:|---:|---:|']
for bet, a in analysis.items():
    m = a['means']
    lines.append(f"| {bet} | {m['incumbent']:.9f} | {m['matched']:.9f} | "
                 f"{m['generous']:.9f} | {m['repair']:.9f} |")
lines += ['', '## Representation limit and case directions', '',
    '| Bet | Current-group mean floor | Repair below floor | Repair vs generous B/E/W |',
    '|---|---:|---:|---|']
for bet, a in analysis.items():
    counts = '/'.join(str(a['versus_generous'].get(k, 0)) for k in ('better', 'equal', 'worse'))
    lines.append(f"| {bet} | {a['mean_group_floor']:.9f} | "
                 f"{a['repair_below_floor_cases']}/32 | {counts} |")
lines += ['', 'Floor claims use independently verified exact-rational asymmetric certificates',
    'on the retained binary64 payoff matrix. Below-floor counting requires a margin',
    'over 1e-8 chips. More optimization within unchanged groups cannot beat that floor',
    'in these games. This is separate from generalization or six-player strength.', '',
    '## Measured computation', '',
    '| Bet | Reference seconds | Matched seconds | Generous seconds |', '|---|---:|---:|---:|']
for bet, a in analysis.items():
    lines.append(f"| {bet} | {a['mean_reference_seconds']:.6f} | "
        f"{a['mean_actual_seconds']['matched']:.6f} | "
        f"{a['mean_actual_seconds']['generous']:.6f} |")
lines += ['', 'The matched checkpoint stops before crossing historical pre-gate work time.',
    'Actual gate time varies; this is a nominal component match, not exact wall-time parity.',
    'Generous training alone reaches the complete historical repair budget, then adds',
    'acceptance time. It therefore favors continuation. Active blocks include snapshots',
    'and updates; input reconstruction, scoring, trace formatting and verification are excluded.',
    'One timing pass. Endpoints replay exactly; hardware timings are observations.', '',
    '```json', json.dumps(analysis, indent=2), '```', '',
    '## Frozen criteria and verification', '',
    '```json', json.dumps(summary['flags'], indent=2), '```', '',
    'The half-pot mean advantage threshold is 1e-6 chips for both comparisons.',
    'All profiles must pass the unchanged per-role exact security gate against incumbent.',
    'These are descriptive fixed-panel criteria, not confidence intervals.',
    '15 preflight checks; four incumbent reconstructions before freeze.',
    f"Replay verifier: {audit['replayed_updates']:,} updates, 64 timing traces,",
    '128 asymmetric certificates, 128 raw and 128 selected profiles,',
    '128 retained reference profiles and 128 independent gate audits. No new LPs or fitting.',
    f'Independent retention arithmetic checks: {checks+1}.',
    f"Worker {worker['seconds']:.3f} s; verifier {verifier['seconds']:.3f} s; "
    f"total {receipt['seconds']:.3f} s, exit 0.",
    'Python 3.14.6, NumPy 2.5.2, SciPy 1.18.0; one BLAS thread; no allocation tracing.',
    '900-second limit per phase; no hard RSS cap. All 25 prior milestones unchanged.',
    'Heads-up one-bet river, 96 holdings per role, K=16; all compatible deals included.',
    'No full-range, six-max, live-latency, population uncertainty or BB/100 claim.',
    'No adoption, commit or push.', '', 'Plan SHA-256: '+digest(OUT/'plan.json'), '',
    'Results manifest SHA-256: '+receipt['result_manifest_sha256'], '']
write(OUT/'summary-audit.json', dict(passed=True, arithmetic_checks=checks+1, analysis=analysis))
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
    f.write(b'\n## Compute-matched continuation\n\n'
        b'[Compute-matched continuation 001](river-witness-compute-matched-continuation-001.md)\n'
        b'compares unchanged-group continuation with the second repair budget and group floor.\n')
assert overview.read_bytes().startswith(old)
write(HERE/'retention.json', dict(passed=True, members=len(members), previous=previous,
    milestone_sha256=digest(ARCHIVE/'milestone-manifest.json'), report_sha256=digest(REPORT),
    source_head=before['head'], commit=False, push=False))
print(json.dumps(dict(flags=summary['flags'], analysis=analysis,
    milestone_sha256=digest(ARCHIVE/'milestone-manifest.json')), indent=2))
