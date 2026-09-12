"""Audit diagnostic arithmetic and retain one completed research milestone."""
from pathlib import Path
from fractions import Fraction as Q
from hashlib import sha256
import json
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = Path('D:/Pontius-worktrees/eval-runner-consolidation')
HISTORY = ROOT/'experiments/river-abstraction-study'
NAME = 'multibet-group-diagnostic-001'
OUT = Path('D:/Pontius-training/river-abstraction-study')/NAME
ARCHIVE = HISTORY/NAME
REPORT = ROOT/'docs/research'/('river-'+NAME+'.md')
read = lambda p: json.loads(p.read_bytes())
digest = lambda p: sha256(p.read_bytes()).hexdigest()


def write(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as f:
        f.write(json.dumps(value, sort_keys=True, indent=2, allow_nan=False)+'\n')


plan, receipt, audit = (read(OUT/p) for p in ('plan.json', 'receipt.json', 'audit.json'))
assert receipt['exit'] == 0 and audit['passed'] and audit['cases'] == 8
assert audit['certificates'] == 72 and audit['profiles'] == 48
assert audit['replayed_updates'] == 1200000 and audit['legacy_profile_crosschecks'] == 32
assert digest(OUT/'plan.json') == read(HERE/'freeze.json')['plan_sha256']
assert digest(OUT/'results-manifest.json') == receipt['result_manifest_sha256']
for name, expected in read(OUT/'results-manifest.json').items():
    assert digest(OUT/name) == expected
for name, expected in plan['pins'].items():
    assert digest(Path(name)) == expected
rows = [read(OUT/f'case-{i:03d}.json') for i in range(8)]
cases = []
for row, entry in zip(rows, plan['entries'], strict=True):
    assert row['entry'] == entry
    item = dict(board=entry['case']['board'], texture=entry['case']['texture'],
                regime=entry['case']['regime'], menus={})
    for name, menu in row['menus'].items():
        first, second = menu['solution']['seat0'], menu['solution']['seat1']
        l0, u0 = map(Q, first['bounds'])
        l1, u1 = map(Q, second['bounds'])
        low, high = map(Q, menu['reference']['bounds'])
        floor = [max(Q(0), (l1-u0)/2), (u1-l0)/2]
        assert menu['solution']['floor'] == list(map(str, floor))
        assert all(0 <= b-a <= Q('1e-8') for a, b in ((l0, u0), (l1, u1), (low, high)))
        records = menu['records']
        assert [r['iteration'] for r in records] == [10000, 50000]
        exploit = [Q(r['exploitability_exact']) for r in records]
        assert all(v >= floor[0] for v in exploit)
        assert all(float(v) == r['exploitability'] for v, r in zip(exploit, records))
        item['menus'][name] = dict(floor_exact=list(map(str, floor)), floor=float(floor[0]),
            exploitability_10k=float(exploit[0]), exploitability_50k=float(exploit[1]),
            residual_50k=float(max(Q(0), exploit[1]-floor[1])),
            bettor_class_loss=[str(max(Q(0), low-u0)), str(high-l0)],
            caller_class_loss=[str(max(Q(0), l1-high)), str(u1-low)],
            seconds_50k=records[-1]['active_seconds']+records[-1]['setup_seconds'])
    item['size_gain_exact'] = row['menus']['both']['conflict']['size_gain_exact']
    item['size_gain'] = float(Q(item['size_gain_exact']))
    item['conflicting_groups'] = row['menus']['both']['conflict']['groups_with_both_strict_sizes']
    cases.append(item)
means = {}
for name in ('half', 'pot', 'both'):
    rs = [r['menus'][name] for r in cases]
    means[name] = {k: sum(r[k] for r in rs)/8 for k in
        ('floor', 'exploitability_10k', 'exploitability_50k', 'residual_50k', 'seconds_50k')}
    means[name]['bettor_class_loss'] = sum(float(Q(r['bettor_class_loss'][0])) for r in rs)/8
    means[name]['caller_class_loss'] = sum(float(Q(r['caller_class_loss'][0])) for r in rs)/8
    means[name]['floor_share_of_50k'] = means[name]['floor']/means[name]['exploitability_50k']
floor_mean = sum((Q(r['menus']['both']['floor_exact'][0]) for r in cases), Q(0))/8
positive = sum(Q(r['size_gain_exact']) > Q('1e-6') for r in cases)
summary = dict(complete=True, cases=cases, means=means,
    flags=dict(grouping_room=floor_mean > Q('1e-6'), size_conflict_at_least_half=positive >= 4),
    positive_size_gain_cases=positive, mean_size_gain=float(sum(
        (Q(r['size_gain_exact']) for r in cases), Q(0))/8))
previous = read(HERE/'preflight.json')['prior_milestones']
assert len(previous) == 28
for name, expected in previous.items():
    directory = HISTORY/name
    assert digest(directory/'milestone-manifest.json') == expected
    for member, value in read(directory/'milestone-manifest.json').items():
        assert digest(directory/member) == value
before = read(HERE/'worktree-before.json')
for name, expected in before['modified_tracked_files'].items():
    assert digest(ROOT/name) == expected, name
git = ['C:/Program Files/Git/cmd/git.exe', '-c', f'safe.directory={ROOT}', '-C', str(ROOT)]
assert subprocess.check_output(git+['rev-parse', 'HEAD'], text=True).strip() == before['head']
assert not ARCHIVE.exists() and not REPORT.exists()
lines = ['# Multiple bet sizes: group diagnostic 001', '',
    'Four existing boards, one per texture; uniform and polarized ranges. Eight cases.',
    'Frozen half-pot-derived preference groups, K=16, identical hands and weights across menus.',
    'The caller observes the bet size and can respond differently to each size.',
    'No repair, fitting, fresh-board claim or production source change.', '',
    '| Menu | Group floor | Trained 10k | Trained 50k | Residual at 50k |',
    '|---|---:|---:|---:|---:|']
for name, v in means.items():
    lines.append(f"| {name} | {v['floor']:.9f} | {v['exploitability_10k']:.9f} | "
                 f"{v['exploitability_50k']:.9f} | {v['residual_50k']:.9f} |")
lines += ['', 'Mean exploitability in chips, lower is better. Floors are certificate lower bounds.',
    'Residual is the part above the certificate upper bound. Interval widths <=1e-8 chips.',
    'The action menu changes the game. Cross-menu floor differences are descriptive,',
    'not a direct playing-strength comparison between policies in different games.', '',
    f'Positive fixed-witness size-selection gain (>1e-6): {positive}/8 cases.',
    'The gain permits per-hand size choices within a common group betting probability.',
    'It is a diagnostic against one witness, not a guaranteed gain after retraining.',
    'A zero value does not exclude conflicts under a different optimal witness.', '',
    '## Full retained summary', '', '```json', json.dumps(summary, indent=2), '```', '',
    '## Scope and verification', '',
    'Five analytic checks passed, including exhaustive pure-response enumeration, observed-size',
    'separation, a known grouping floor, and one-bet solver/trainer equivalence.',
    '72 saddle certificates on original binary64 payoff coefficients interpreted as rationals.',
    'Bettor probability weights are normalized exactly; caller probabilities remain in [0,1].',
    '1,200,000 updates replayed; 48 profiles verified; 32 one-bet legacy evaluator crosschecks.',
    'Each asymmetric/full-hand game used two opposing LPs; 144 LPs total.',
    'Independent replay verifier performs no LP solve. Known boards are diagnostic inputs.',
    '16 groups per player stay fixed; additional actions increase the policy parameter count.',
    '10k/50k are matched-update checkpoints, not equal-compute comparisons.',
    'Timings exclude reconstruction, scoring, LPs and verification; no live-latency claim.',
    'Five frozen preflight tests; all 28 previous milestones verified unchanged.',
    'Python 3.14.6, NumPy 2.5.2, SciPy 1.18.0, one BLAS thread, no allocation tracing.',
    '900-second phase limits, 10-second/20k-iteration LP limits, no hard RSS cap.',
    f"Run and verification: {receipt['seconds']:.3f} seconds, exit 0.",
    'No adoption, commit or push.', '', 'Plan SHA-256: '+digest(OUT/'plan.json'), '',
    'Results manifest SHA-256: '+receipt['result_manifest_sha256'], '']
write(OUT/'summary.json', summary)
with REPORT.open('x', encoding='utf-8', newline='\n') as f:
    f.write('\n'.join(lines))
shutil.copytree(OUT, ARCHIVE)
(ARCHIVE/'verification-tools').mkdir()
for path in sorted(HERE.iterdir()):
    if path.is_file() and path.name != 'plan.json':
        shutil.copyfile(path, ARCHIVE/'verification-tools'/path.name)
shutil.copyfile(REPORT, ARCHIVE/'report.md')
manifest = {p.relative_to(ARCHIVE).as_posix(): digest(p)
            for p in sorted(ARCHIVE.rglob('*')) if p.is_file()}
write(ARCHIVE/'milestone-manifest.json', manifest)
assert all(digest(ARCHIVE/k) == v for k, v in manifest.items())
overview = ROOT/'docs/research/README.md'
old = overview.read_bytes()
with (HERE/'research-readme-before.md').open('xb') as f:
    f.write(old)
with overview.open('ab') as f:
    f.write(b'\n## Multiple bet sizes\n\n'
        b'[Multi-bet group diagnostic 001](river-multibet-group-diagnostic-001.md)\n'
        b'measures fixed-group limits and training residuals when both bet sizes coexist.\n')
assert overview.read_bytes().startswith(old)
write(HERE/'retention.json', dict(passed=True, members=len(manifest),
    milestone_sha256=digest(ARCHIVE/'milestone-manifest.json'), report_sha256=digest(REPORT),
    source_head=before['head'], commit=False, push=False))
print(json.dumps(dict(means=means, flags=summary['flags'], positive_size_gain_cases=positive,
                     mean_size_gain=summary['mean_size_gain'],
                     conflicts=[r['conflicting_groups'] for r in cases]), indent=2))
