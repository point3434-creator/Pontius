"""Independent result arithmetic, history audit and local milestone retention."""
from pathlib import Path
from fractions import Fraction as Q
from hashlib import sha256
from itertools import permutations
import json
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = Path('D:/Pontius-worktrees/eval-runner-consolidation')
HISTORY = ROOT/'experiments/river-abstraction-study'
NAME = 'witness-next-board-002'
OUT = Path('D:/Pontius-training/river-abstraction-study')/NAME
ARCHIVE = HISTORY/NAME
REPORT = ROOT/'docs/research'/('river-'+NAME+'.md')
read = lambda p: json.loads(p.read_bytes())
digest = lambda p: sha256(p.read_bytes()).hexdigest()


def write(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as f:
        f.write(json.dumps(value, sort_keys=True, indent=2, allow_nan=False)+'\n')


def literal_boards(value):
    if isinstance(value, list):
        if len(value) == 5 and all(type(x) is int and 0 <= x < 52 for x in value):
            if len(set(value)) == 5:
                yield value
        else:
            for v in value:
                yield from literal_boards(v)
    elif isinstance(value, dict):
        for v in value.values():
            yield from literal_boards(v)


def exact(score):
    return Q(score['exact_exploitability'])


plan, receipt, audit = (read(OUT/p) for p in ('plan.json', 'receipt.json', 'audit.json'))
assert receipt['exit'] == 0 and audit['passed'] and audit['cases'] == 4
assert audit['asymmetric_certificates'] == audit['independent_gate_audits'] == 16
assert digest(OUT/'plan.json') == read(HERE/'freeze.json')['plan_sha256']
assert digest(OUT/'results-manifest.json') == receipt['result_manifest_sha256']
for name, expected in read(OUT/'results-manifest.json').items():
    assert digest(OUT/name) == expected, name
for name, expected in plan['pins'].items():
    assert digest(Path(name)) == expected, name
board = plan['selection']['board']
old_boards = []
for name, expected in plan['historical_plans'].items():
    assert digest(Path(name)) == expected
    old_boards.extend(literal_boards(read(Path(name))))
for old in old_boards:
    assert all(sorted(4*(v//4)+p[v%4] for v in board) != sorted(old)
               for p in permutations(range(4)))
rows = [read(OUT/f'case-{i:03d}.json') for i in range(4)]
cases = []
for row, entry in zip(rows, plan['entries'], strict=True):
    assert row['entry'] == entry
    values = dict(original=exact(row['initial']),
        first=exact(row['stages'][0]['selected_score']),
        second=exact(row['stages'][1]['selected_score']),
        **{k: exact(row['records'][k]['selected_score']) for k in ('matched', 'generous')})
    assert values['second'] <= values['first'] <= values['original']
    assert all(values[k] <= values['first'] for k in ('matched', 'generous'))
    for point in [*row['stages'], *row['records'].values()]:
        pairs = [list(map(Q, ps)) for ps in point['gate']['security_exact']]
        accepted = [pairs[1][s] >= pairs[0][s] for s in (0, 1)]
        assert point['gate']['accepted'] == accepted
        assert exact(point['selected_score']) == -sum(
            (pairs[int(accepted[s])][s] for s in (0, 1)), Q(0))/2
    floor = Q(row['stages'][1]['witness']['minimum_exploitability']['lower_exact'])
    assert values['matched'] >= floor and values['generous'] >= floor
    assert row['records']['generous']['active_seconds'] >= row['budgets']['total_seconds']
    cases.append(dict(bet=entry['bet'], regime=entry['case']['regime'],
        values_exact={k: str(v) for k, v in values.items()},
        values={k: float(v) for k, v in values.items()}, first_group_floor=float(floor),
        second_below_floor=values['second'] < floor-Q('1e-8'),
        second_beats_generous=values['second'] < values['generous'],
        raw_repair_regression=[exact(s['records'][-1]) > -sum(
            map(Q, s['gate']['security_exact'][0]), Q(0))/2 for s in row['stages']],
        accepted_roles=[s['gate']['accepted'] for s in row['stages']],
        reference_seconds=row['budgets']['total_seconds'],
        total_ratios={k: row['records'][k]['total_component_seconds']/
                        row['budgets']['total_seconds']
                      for k in ('matched', 'generous')},
        total_iterations={k: row['records'][k]['iteration'] for k in ('matched', 'generous')}))
means = {}
for bet in (5, 10):
    subset = [r for r in cases if r['bet'] == bet]
    assert len(subset) == 2
    avg = {k: sum((Q(r['values_exact'][k]) for r in subset), Q(0))/2
           for k in subset[0]['values_exact']}
    means[str(bet)] = dict(values={k: float(v) for k, v in avg.items()},
        values_exact={k: str(v) for k, v in avg.items()},
        second_improves_first=avg['second'] < avg['first']-Q('1e-6'),
        second_beats_matched=avg['second'] < avg['matched']-Q('1e-6'),
        second_beats_generous=avg['second'] < avg['generous']-Q('1e-6'),
        second_gain_percent=100*float(1-avg['second']/avg['first']) if avg['first'] else None,
        versus_generous_percent=100*float(1-avg['second']/avg['generous'])
                               if avg['generous'] else None)
previous = read(HERE/'preflight.json')['prior_milestones']
assert len(previous) == 27
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
result = dict(passed=True, selection=plan['selection'], cases=cases, means=means,
    novelty_historical_plans=len(plan['historical_plans']),
    novelty_literal_boards_checked=len(old_boards), prior_milestones=27)
write(OUT/'summary.json', result)
lines = ['# Next board 002', '',
    'One fresh board through the frozen two-repair procedure. Four cases cover both',
    'existing range regimes and bets. Every case is retained, including non-improvements.',
    'This is one additional board, not a population confidence or six-max strength claim.', '',
    'Board integer IDs: '+str(board)+'. Texture: '+plan['selection']['texture']+'.',
    'First unused board in the original SHA-256 sequence: attempt '+
    str(plan['selection']['attempt'])+'. Suit-equivalent prior boards excluded.', '',
    '| Bet | Regime | Original | First repair | Second repair | Matched | Generous |',
    '|---|---|---:|---:|---:|---:|---:|']
for r in cases:
    v = r['values']
    cells = ' | '.join(f'{v[k]:.9f}' for k in
                       ('original', 'first', 'second', 'matched', 'generous'))
    lines.append(f"| {r['bet']} | {r['regime']} | {cells} |")
lines += ['', 'Exact-hand exploitability in chips; lower is better.', '',
    'The matched control stops before crossing the second repair pre-gate work time.',
    'The generous control spends the entire second-repair budget on continuation,',
    'then adds the acceptance check. Gate times vary; see actual ratios below.',
    'These are component budgets, excluding reconstruction, scoring and verification.', '',
    '## Per-case audit and mean outcomes', '', '```json',
    json.dumps(result, indent=2), '```', '', '## Verification', '',
    '17 preflight checks, direct suit-permutation novelty audit against 27 historical plans.',
    f"{audit['replayed_updates']:,} updates replayed, 16 asymmetric certificates verified,",
    f"{audit['independent_exchanges']:,} independently enumerated proposal exchanges,",
    '16 independent exact security-gate audits; no LP solves in the verifier.',
    f"Worker and verification completed in {receipt['seconds']:.3f} seconds, exit 0.",
    'Python 3.14.6; one BLAS thread; no allocation tracing; 900-second limit per phase.',
    'Continuation capped at 200,000 total updates; no hard RSS cap.',
    'K=16, 96 holdings per role, pot 10, stacks 20; all compatible deals included.',
    'Preference model and repair rules unchanged; no fitting, adoption, commit or push.',
    'All 27 earlier milestones verified unchanged.', '',
    'Plan SHA-256: '+digest(OUT/'plan.json'), '',
    'Results manifest SHA-256: '+receipt['result_manifest_sha256'], '']
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
    f.write(b'\n## Next board\n\n[Next board 002](river-witness-next-board-002.md)\n'
        b'runs the frozen two-repair and continuation comparison on one additional unseen board.\n')
assert overview.read_bytes().startswith(old)
write(HERE/'retention.json', dict(passed=True, members=len(manifest),
    milestone_sha256=digest(ARCHIVE/'milestone-manifest.json'), report_sha256=digest(REPORT),
    source_head=before['head'], commit=False, push=False))
print(json.dumps(result, indent=2))
