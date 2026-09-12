"""Audit aggregate arithmetic, report all outcomes, and retain the completed study."""
from collections import Counter
from fractions import Fraction as Q
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = Path('D:/Pontius-worktrees/eval-runner-consolidation')
OUT = Path('D:/Pontius-training/river-abstraction-study/witness-soft-assignment-001')
ARCHIVE = ROOT/'experiments/river-abstraction-study/witness-soft-assignment-001'
REPORT = ROOT/'docs/research/river-witness-soft-assignment-001.md'


def read(path):
    return json.loads(path.read_bytes())


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def write(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(value, sort_keys=True, indent=2, allow_nan=False)+'\n')


def direction(value):
    return 'lower' if value < -Q('1e-10') else 'higher' if value > Q('1e-10') else 'equal'


def mid(value):
    return float((Q(value['lower_exact'])+Q(value['upper_exact']))/2)


plan, summary, audit = (read(OUT/name) for name in ('plan.json', 'summary.json', 'audit.json'))
receipt, worker, verifier = (read(OUT/name) for name in
                            ('receipt.json', 'worker-receipt.json', 'verify-receipt.json'))
assert receipt['exit'] == worker['exit'] == verifier['exit'] == 0
assert summary['complete'] and not summary['synthetic'] and audit['passed']
assert audit['certificates'] == 384 and audit['profiles'] == 960
assert not ARCHIVE.exists() and not REPORT.exists()
assert digest(OUT/'results-manifest.json') == receipt['result_manifest_sha256']
for name, expected in read(OUT/'results-manifest.json').items():
    assert digest(OUT/name) == expected, name
for name, expected in plan['pins'].items():
    assert digest(Path(name)) == expected, name
rows = [read(OUT/f'cell-{i:03d}.json') for i in range(96)]

# This audit does not import the experiment's summary/statistics functions.
checks, analysis = 0, {}
for label, panel in summary['panels'].items():
    _, bet, _, capacity = label.split('-')
    selected = [r for r in rows if r['entry']['bet'] == int(bet)
                and r['capacity'] == int(capacity)]
    selections = [('overall', '', panel['overall'], selected)]
    for category, case_key in [('boards', 'board_index'), ('textures', 'texture'),
                               ('regimes', 'regime'), ('leave_one_board_out', 'board_index')]:
        for value, reported in panel[category].items():
            subset = [r for r in selected if
                      (str(r['entry']['case'][case_key]) == value) !=
                      (category == 'leave_one_board_out')]
            selections.append((category, value, reported, subset))
    for category, value, reported, subset in selections:
        assert reported['cells'] == len(subset) and subset
        lo, hi, actual, timed = {}, {}, {}, {}
        for method in ('hard', 'soft'):
            values = [r['methods'][method] for r in subset]
            lo[method] = sum(Q(v['solution']['minimum_exploitability']['lower_exact'])
                             for v in values)/len(values)
            hi[method] = sum(Q(v['solution']['minimum_exploitability']['upper_exact'])
                             for v in values)/len(values)
            actual[method] = sum(Q(v['records'][-1]['exact_exploitability'])
                                 for v in values)/len(values)
            timed[method] = sum(Q(t['exact_exploitability']) for v in values
                                for t in v['timed'])/(3*len(values))
            assert Q(reported['floors'][method]['lower_exact']) == lo[method]
            assert Q(reported['floors'][method]['upper_exact']) == hi[method]
            assert reported['actual'][method] == float(actual[method])
            assert reported['timed'][method] == float(timed[method])
            checks += 4
        assert Q(reported['floor_delta']['lower_exact']) == lo['soft']-hi['hard']
        assert Q(reported['floor_delta']['upper_exact']) == hi['soft']-lo['hard']
        assert Q(reported['actual_delta_exact']) == actual['soft']-actual['hard']
        assert Q(reported['timed_delta_exact']) == timed['soft']-timed['hard']
        checks += 4
    v = panel['overall']
    analysis[label] = dict(
        actual_change_percent=100*(v['actual']['soft']/v['actual']['hard']-1),
        floor_change_percent=100*(mid(v['floors']['soft'])/mid(v['floors']['hard'])-1),
        timed_change_percent=100*(v['timed']['soft']/v['timed']['hard']-1),
        board_directions=dict(Counter(direction(Q(b['actual_delta_exact']))
                                      for b in panel['boards'].values())),
        all_omitted_board_actual_deltas_negative=all(Q(b['actual_delta_exact']) < 0
            for b in panel['leave_one_board_out'].values()))
primary = summary['panels']['bet-5-k-16']['overall']
support = Q(primary['floor_delta']['upper_exact']) < -Q('1e-8')
assert summary['flags'] == dict(representation_support=support,
    practical_support=support and Q(primary['actual_delta_exact']) < -Q('1e-6'))

prior = {}
for directory in sorted(ARCHIVE.parent.iterdir()):
    manifest = directory/'milestone-manifest.json'
    if manifest.is_file():
        for name, expected in read(manifest).items():
            assert digest(directory/name) == expected, (directory, name)
        prior[directory.name] = digest(manifest)
before = read(HERE/'worktree-before-retention.json')
for name, expected in before['modified_tracked_files'].items():
    assert digest(ROOT/name) == expected, name
git = ['C:/Program Files/Git/cmd/git.exe', '-c', f'safe.directory={ROOT}', '-C', str(ROOT)]
assert subprocess.check_output(git+['rev-parse', 'HEAD'], text=True).strip() == before['head']

lines = ['# Soft strategy assignment pilot 001', '',
    'The approved frozen experiment completed and its separate verifier passed.',
    'This compares fixed geometric interpolation against hard assignments using',
    'the same frozen ordinary-preference features and component count. It is an',
    'observed-panel diagnostic, not an Embedding CFR reproduction or a fresh-board',
    'confirmation. No policy was adopted.', '',
    '## Frozen primary decisions', '', '| Decision | Passed |', '|---|---|']
for name, passed in summary['flags'].items():
    lines.append(f'| {name} | {passed} |')
lines += ['', 'Primary: K=16, half-pot. Representation support requires the upper',
    'endpoint of mean soft-minus-hard floor difference below -1e-8 chips. Practical',
    'support also requires 10,000-update mean actual difference below -1e-6 chips.',
    'These are descriptive thresholds, not significance tests.', '',
    '## All capacity and bet panels', '',
    'Exploitability is in chips; lower is better. Floor values are certified',
    'interval midpoints for display. Exact rational bounds are retained in JSON.',
    'Positive percentage change means soft is worse; negative means soft is better.', '',
    '| Bet | K | Hard floor | Soft floor | Hard actual | Soft actual | Actual change % |',
    '|---|---|---:|---:|---:|---:|---:|']
for label, panel in summary['panels'].items():
    _, bet, _, k = label.split('-'); v = panel['overall']
    lines.append(f"| {bet} | {k} | {mid(v['floors']['hard']):.9f} | "
        f"{mid(v['floors']['soft']):.9f} | {v['actual']['hard']:.9f} | "
        f"{v['actual']['soft']:.9f} | {analysis[label]['actual_change_percent']:+.2f} |")
lines += ['', '## Matched active training time', '',
    'Three fresh 0.1-second trials per method and cell, each capped at 100,000',
    'updates. Active time excludes assignment building, matrix preparation and',
    'scoring. Actual iteration counts are retained and replayed. These timings',
    'describe this run and do not establish an end-to-end speed advantage.', '',
    '| Bet | K | Hard actual | Soft actual | Change % |', '|---|---|---:|---:|---:|']
for label, panel in summary['panels'].items():
    _, bet, _, k = label.split('-'); v = panel['overall']
    lines.append(f"| {bet} | {k} | {v['timed']['hard']:.9f} | {v['timed']['soft']:.9f} | "
                 f"{analysis[label]['timed_change_percent']:+.2f} |")
for category in ('boards', 'textures', 'regimes', 'leave_one_board_out'):
    lines += ['', '## '+category.replace('_', ' '), '',
        '| Bet/K | Panel | Actual delta | Floor delta lower | Floor delta upper |',
        '|---|---|---:|---:|---:|']
    for label, panel in summary['panels'].items():
        for name, value in panel[category].items():
            lines.append(f"| {label} | {name} | {float(Q(value['actual_delta_exact'])):.9f} | "
                f"{float(Q(value['floor_delta']['lower_exact'])):.9f} | "
                f"{float(Q(value['floor_delta']['upper_exact'])):.9f} |")
lines += ['', '## Scope and verification', '',
    'Eight boards, pool 0, two regimes, two bet sizes: 32 games with 96 holdings',
    'per seat, pot 10, stacks 20/20, a single heads-up bet and no raises. Exact',
    'deal enumeration avoids match-sampling noise; it does not supply a board',
    'population confidence interval or six-max playing-strength evidence.', '',
    'K=8/16/32 crossed with hard/soft gives 192 method-cells. Both seats have K',
    'free action probabilities. Soft adds assignment metadata; this is not an',
    'equal-storage comparison. The fixed interpolation rule is not a learned',
    'embedding and its result must not be generalized to all soft representations.', '',
    '384 asymmetric LP calls and no fits. The separate verifier reconstructs',
    'original-game rational certificates and all 960 saved profile evaluations.',
    f"Every trajectory was replayed: {audit['replayed_updates']:,} total updates.",
    f'Independent aggregate checks: {checks+1}; all passed.',
    'Fourteen preparation checks passed, including hard-path equality with the',
    'predecessor and independently enumerated soft-policy extrema.',
    f"Worker {worker['seconds']:.3f} s; verifier {verifier['seconds']:.3f} s; "
    f"combined {receipt['seconds']:.3f} s, exit 0.",
    'Python 3.14.6, NumPy 2.5.2, SciPy 1.18.0; one BLAS thread, no tracing.',
    'Each phase had a 1,800-second timeout. No RSS cap or memory measurement claim.',
    f'All {len(prior)} preceding milestone manifests and their members verified.',
    'No source changes, adoption, commit, push or independent cold-review claim.', '',
    'Plan SHA-256: '+digest(OUT/'plan.json'), '',
    'Results manifest SHA-256: '+receipt['result_manifest_sha256'], '']

write(OUT/'summary-audit.json', dict(passed=True, rational_checks=checks+1, analysis=analysis))
shutil.copyfile(HERE/'authorization.json', OUT/'authorization.json')
with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
    stream.write('\n'.join(lines))
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
    assert digest(ARCHIVE/name) == expected
overview = ROOT/'docs/research/README.md'
original = overview.read_bytes()
with (HERE/'research-readme-before.md').open('xb') as stream:
    stream.write(original)
with overview.open('ab') as stream:
    stream.write(b'\n## Soft strategy assignment pilot\n\n'
        b'[Witness-soft-assignment-001](river-witness-soft-assignment-001.md) tests\n'
        b'fixed two-group strategy interpolation at three compressed capacities,\n'
        b'with certified floors and matched work/time comparisons.\n')
assert overview.read_bytes().startswith(original)
write(HERE/'retention.json', dict(passed=True, milestone_members=len(members),
    milestone_sha256=digest(ARCHIVE/'milestone-manifest.json'), prior_milestones=prior,
    report_sha256=digest(REPORT), source_head=before['head'], commit=False, push=False))
print(json.dumps(dict(flags=summary['flags'], analysis=analysis,
    retention=read(HERE/'retention.json')), indent=2))
