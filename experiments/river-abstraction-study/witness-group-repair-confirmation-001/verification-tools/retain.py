"""Independently audit summaries and retain every outcome of the completed repair pilot."""
from collections import Counter
from fractions import Fraction as Q
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = Path('D:/Pontius-worktrees/eval-runner-consolidation')
OUT = Path('D:/Pontius-training/river-abstraction-study/witness-group-repair-confirmation-001')
ARCHIVE = ROOT/'experiments/river-abstraction-study/witness-group-repair-confirmation-001'
REPORT = ROOT/'docs/research/river-witness-group-repair-confirmation-001.md'
read = lambda p: json.loads(p.read_bytes())
digest = lambda p: sha256(p.read_bytes()).hexdigest()


def write(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as f:
        f.write(json.dumps(value, sort_keys=True, indent=2, allow_nan=False)+'\n')


def mid(value):
    return float((Q(value['lower_exact'])+Q(value['upper_exact']))/2)


def direction(value):
    return 'lower' if value < -Q('1e-10') else 'higher' if value > Q('1e-10') else 'equal'


plan, summary, audit, receipt = (read(OUT/name) for name in
    ('plan.json', 'summary.json', 'audit.json', 'receipt.json'))
worker, verifier = (read(OUT/name) for name in ('worker-receipt.json', 'verify-receipt.json'))
novelty = read(HERE/'novelty-audit.json')
assert novelty['passed'] and novelty['fresh_boards'] == 16
assert novelty['plan_sha256'] == digest(OUT/'plan.json')
assert receipt['exit'] == worker['exit'] == verifier['exit'] == 0 and audit['passed']
assert summary['complete'] and audit['profiles'] == audit['certificates'] == 256
assert audit['replayed_updates'] == 3840000
assert not ARCHIVE.exists() and not REPORT.exists()
assert digest(OUT/'results-manifest.json') == receipt['result_manifest_sha256']
for name, expected in read(OUT/'results-manifest.json').items():
    assert digest(OUT/name) == expected, name
for name, expected in plan['pins'].items():
    assert digest(Path(name)) == expected, name
rows = [read(OUT/f'case-{i:03d}.json') for i in range(64)]
checks, analysis = 0, {}
for bet, panel in summary['panels'].items():
    selected = [r for r in rows if r['entry']['bet'] == int(bet)]
    selections = [(panel['overall'], selected)]
    for category, key in [('boards', 'board_index'), ('textures', 'texture'),
                          ('regimes', 'regime'), ('leave_one_board_out', 'board_index')]:
        for label, value in panel[category].items():
            subset = [r for r in selected if (str(r['entry']['case'][key]) == label)
                      != (category == 'leave_one_board_out')]
            selections.append((value, subset))
    for value, subset in selections:
        assert value['cases'] == len(subset) and subset
        base = [sum(Q(r['baseline']['minimum_exploitability'][k]) for r in subset)/len(subset)
                for k in ('lower_exact', 'upper_exact')]
        prop = [sum(Q(r['solution']['minimum_exploitability'][k]) for r in subset)/len(subset)
                for k in ('lower_exact', 'upper_exact')]
        for name, bounds in [('baseline', base), ('repaired', prop)]:
            assert Q(value['floors'][name]['lower_exact']) == bounds[0]
            assert Q(value['floors'][name]['upper_exact']) == bounds[1]
            checks += 2
        assert Q(value['floor_delta']['lower_exact']) == prop[0]-base[1]
        assert Q(value['floor_delta']['upper_exact']) == prop[1]-base[0]
        scores = {}
        for name, method, index in [('baseline_10k', 'control', 0), ('baseline_50k', 'control', 1),
                                    ('repaired_10k', 'repaired', 1)]:
            scores[name] = sum(Q(r['records'][method][index]['exact_exploitability'])
                               for r in subset)/len(subset)
            assert value['actual'][name] == float(scores[name])
        assert Q(value['actual_delta_exact']) == scores['repaired_10k']-scores['baseline_10k']
        assert Q(value['versus_50k_exact']) == scores['repaired_10k']-scores['baseline_50k']
        assert value['changed_seats'] == sum(s['changed'] for r in subset
                                           for s in r['proposal']['seats'])
        directions = Counter('lower' if
            Q(r['solution']['minimum_exploitability']['upper_exact']) <
            Q(r['baseline']['minimum_exploitability']['lower_exact']) else 'higher' if
            Q(r['solution']['minimum_exploitability']['lower_exact']) >
            Q(r['baseline']['minimum_exploitability']['upper_exact']) else 'overlapping'
            for r in subset)
        assert value['floor_directions'] == dict(directions)
        checks += 9
    value = panel['overall']
    actual = value['actual']
    analysis[bet] = dict(
        actual_change_percent=100*(actual['repaired_10k']/actual['baseline_10k']-1),
        versus_longer_control_percent=100*(actual['repaired_10k']/actual['baseline_50k']-1),
        floor_change_percent=100*(mid(value['floors']['repaired'])/
                                  mid(value['floors']['baseline'])-1),
        board_directions=dict(Counter(direction(Q(v['actual_delta_exact']))
                                      for v in panel['boards'].values())),
        floor_case_directions=value['floor_directions'], changed_seats=value['changed_seats'],
        mean_fixed_witness_gain=[float(sum(Q(r['proposal']['seats'][s]['net_witness_gain_exact'])
                                          for r in selected)/len(selected)) for s in (0, 1)])

for bet, value in analysis.items():
    panel = summary['panels'][bet]
    selected = [r for r in rows if r['entry']['bet'] == int(bet)]
    def delta(row):
        return (Q(row['records']['repaired'][1]['exact_exploitability'])-
                Q(row['records']['control'][0]['exact_exploitability']))
    worst = max(selected, key=delta)
    value['worst_case'] = dict(case=worst['entry']['case'], actual_delta_exact=str(delta(worst)))
    value['actual_case_directions'] = dict(Counter(direction(delta(r)) for r in selected))
    value['leave_one_board_out_all_improve'] = all(
        Q(v['actual_delta_exact']) < 0 for v in panel['leave_one_board_out'].values())
    value['texture_actual_deltas'] = {k: float(Q(v['actual_delta_exact']))
                                     for k, v in panel['textures'].items()}
    value['regime_actual_deltas'] = {k: float(Q(v['actual_delta_exact']))
                                    for k, v in panel['regimes'].items()}
primary = summary['panels']['5']['overall']
support = Q(primary['floor_delta']['upper_exact']) < -Q('1e-8')
assert summary['flags'] == dict(representation_support=support,
    practical_support=support and Q(primary['actual_delta_exact']) < -Q('1e-6'))

previous = {}
for directory in sorted(ARCHIVE.parent.iterdir()):
    path = directory/'milestone-manifest.json'
    if path.is_file():
        for name, expected in read(path).items():
            assert digest(directory/name) == expected, (directory, name)
        previous[directory.name] = digest(path)
before = read(HERE/'worktree-before.json')
for name, expected in before['modified_tracked_files'].items():
    assert digest(ROOT/name) == expected, name
git = ['C:/Program Files/Git/cmd/git.exe', '-c', f'safe.directory={ROOT}', '-C', str(ROOT)]
assert subprocess.check_output(git+['rev-parse', 'HEAD'], text=True).strip() == before['head']

lines = ['# Fresh-board witness group repair confirmation 001', '',
    'Completed under the frozen design. One split and one merge per seat at K=16;',
    'every proposal is scored, including no-ops and regressions. This is offline',
    'refinement using a witness from the evaluation game, not a learned-model',
    'generalization test. No proposal or policy was adopted.', '',
    '## Frozen primary criteria', '', '| Criterion | Passed |', '|---|---|']
for name, value in summary['flags'].items():
    lines.append(f'| {name} | {value} |')
lines += ['', 'Half-pot is primary. The mean certified floor-difference upper endpoint',
    'must be below -1e-8 chips; practical support also requires mean actual',
    '10,000-update difference below -1e-6 chips. These are descriptive thresholds.', '',
    '## All results', '', 'Exploitability in chips, lower is better.',
    'Positive percentage change means',
    'the repair is worse. Floor midpoints are display-only; exact bounds are retained.', '',
    '| Bet | Original floor | Repaired floor | Original 10k | Repaired 10k | Original 50k |',
    '|---|---:|---:|---:|---:|---:|']
for bet, panel in summary['panels'].items():
    value = panel['overall']; actual = value['actual']
    lines.append(f"| {bet} | {mid(value['floors']['baseline']):.9f} | "
        f"{mid(value['floors']['repaired']):.9f} | {actual['baseline_10k']:.9f} | "
        f"{actual['repaired_10k']:.9f} | {actual['baseline_50k']:.9f} |")
lines += ['', '| Bet | Actual change % | Floor change % | Versus original 50k % |',
          '|---|---:|---:|---:|']
for bet, value in analysis.items():
    lines.append(f"| {bet} | {value['actual_change_percent']:+.2f} | "
        f"{value['floor_change_percent']:+.2f} | {value['versus_longer_control_percent']:+.2f} |")
lines += ['', '## Mechanism and limits', '',
    'The exchange maximizes improvement against one fixed opponent witness within',
    'the declared one-split/two-other-groups-merge family. The opponent is allowed',
    'to change its response during evaluation, so positive witness gain is not a',
    'guarantee of a lower exploitability floor. No new certificate gates selection.',
    'The original control gets five times as many solver updates, not equal wall',
    'time. Incremental proposal, LP and training times are retained separately.',
    'Baseline witness generation is separately timed in every new case. Prior',
    'model fitting is excluded; there is no fitting in this confirmation.', '',
    '| Bet | Changed seats | Floor lower/higher/overlap cases | Board lower/higher/equal |',
    '|---|---:|---|---|']
for bet, value in analysis.items():
    counts = value['floor_case_directions']; boards = value['board_directions']
    lines.append(f"| {bet} | {value['changed_seats']}/64 | "
        f"{counts.get('lower',0)}/{counts.get('higher',0)}/{counts.get('overlapping',0)} | "
        f"{boards.get('lower',0)}/{boards.get('higher',0)}/{boards.get('equal',0)} |")
for category in ('boards', 'textures', 'regimes', 'leave_one_board_out'):
    lines += ['', '## '+category.replace('_', ' '), '',
        '| Bet | Panel | Actual delta | Floor lower | Floor upper |',
        '|---|---|---:|---:|---:|']
    for bet, panel in summary['panels'].items():
        for label, value in panel[category].items():
            lines.append(f"| {bet} | {label} | {float(Q(value['actual_delta_exact'])):.9f} | "
                f"{float(Q(value['floor_delta']['lower_exact'])):.9f} | "
                f"{float(Q(value['floor_delta']['upper_exact'])):.9f} |")

lines += ['', '## Freshness and worst regressions', '',
    'All 16 boards were frozen before evaluation. Four per texture, excluding 52',
    'historical board classes up to suit isomorphism. This is the unchanged',
    'one-step algorithm, including a fresh per-game offline witness; it is not a',
    'claim that the learned model alone generalizes to repaired group labels.', '',
    '| Bet | Worst case | Actual exploitability increase | LOBO means all improve |',
    '|---|---|---:|---|']
for bet, value in analysis.items():
    worst = value['worst_case']
    lines.append(f"| {bet} | {worst['case']['id']} | "
        f"{float(Q(worst['actual_delta_exact'])):+.9f} | "
        f"{value['leave_one_board_out_all_improve']} |")
lines += ['', '## Verification and scope', '',
    '64 observed cases: sixteen fresh boards, one pool, two regimes, two bet sizes.',
    '96 holdings per seat, pot 10, stacks 20/20, heads-up one-bet river game.',
    'All compatible deals and unrestricted exact-hand best responses remain.',
    'No population confidence interval or six-max strength claim.', '',
    '16 author checks passed. 256 new LP calls and 128 trajectories completed.',
    '256 asymmetric certificates and 256 saved profiles verified; 3,840,000',
    'updates replayed with verifier LP calls disabled. All new inputs and group',
    'labels were rebuilt. Four historical cases reproduced before the freeze.',
    'A separate stdlib audit compared all 24 suit relabelings with historical boards.',
    f"Independent exchange enumerations: {audit['independently_enumerated_exchanges']:,}.",
    f'Independent aggregate arithmetic checks: {checks+1}.',
    f"Worker {worker['seconds']:.3f} s; verifier {verifier['seconds']:.3f} s; "
    f"combined {receipt['seconds']:.3f} s, exit 0.",
    'Python 3.14.6, NumPy 2.5.2, SciPy 1.18.0; one BLAS thread; tracing disabled.',
    '900-second limit per phase; no hard RSS cap or memory measurement claim.',
    f'All {len(previous)} prior milestones verified and preserved. No source changes,',
    'adoption, commit, push or independent cold-review claim.', '',
    'Plan SHA-256: '+digest(OUT/'plan.json'), '',
    'Results manifest SHA-256: '+receipt['result_manifest_sha256'], '']
write(OUT/'summary-audit.json', dict(passed=True, rational_checks=checks+1, analysis=analysis))
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
for name, expected in members.items():
    assert digest(ARCHIVE/name) == expected, name
overview = ROOT/'docs/research/README.md'
old = overview.read_bytes()
with (HERE/'research-readme-before.md').open('xb') as f:
    f.write(old)
with overview.open('ab') as f:
    f.write(b'\n## Fresh-board witness group repair confirmation\n\n'
        b'[Witness-group-repair-confirmation-001]'
        b'(river-witness-group-repair-confirmation-001.md) tests one\n'
        b'unchanged fixed-capacity repair on sixteen new boards; every outcome is retained.\n')
assert overview.read_bytes().startswith(old)
write(HERE/'retention.json', dict(passed=True, milestone_members=len(members),
    milestone_sha256=digest(ARCHIVE/'milestone-manifest.json'), prior_milestones=previous,
    report_sha256=digest(REPORT), source_head=before['head'], commit=False, push=False))
print(json.dumps(dict(flags=summary['flags'], analysis=analysis,
    retention=read(HERE/'retention.json')), indent=2))
