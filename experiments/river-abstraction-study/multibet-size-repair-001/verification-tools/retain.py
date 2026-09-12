"""Audit the fixed-caller pilot arithmetic and preserve the complete result."""
from pathlib import Path
from fractions import Fraction as Q
from hashlib import sha256
from collections import Counter
import json
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = Path('D:/Pontius-worktrees/eval-runner-consolidation')
HISTORY = ROOT/'experiments/river-abstraction-study'
NAME = 'multibet-size-repair-001'
OUT = Path('D:/Pontius-training/river-abstraction-study')/NAME
ARCHIVE = HISTORY/NAME
REPORT = ROOT/'docs/research'/('river-'+NAME+'.md')
read = lambda p: json.loads(p.read_bytes())
digest = lambda p: sha256(p.read_bytes()).hexdigest()


def write(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as f:
        f.write(json.dumps(value, sort_keys=True, indent=2, allow_nan=False)+'\n')


def direction(a, b):
    return 'better' if a < b else 'worse' if a > b else 'equal'


plan, receipt, audit = (read(OUT/p) for p in ('plan.json', 'receipt.json', 'audit.json'))
assert receipt['exit'] == 0 and audit['passed'] and audit['cases'] == 8
assert audit['proposed_certificates'] == audit['incumbent_certificates'] == 16
assert audit['independent_gate_audits'] == 16 and audit['replayed_updates'] == 1200000
assert digest(OUT/'plan.json') == read(HERE/'freeze.json')['plan_sha256']
assert digest(OUT/'results-manifest.json') == receipt['result_manifest_sha256']
for name, expected in read(OUT/'results-manifest.json').items():
    assert digest(OUT/name) == expected
for name, expected in plan['pins'].items():
    assert digest(Path(name)) == expected
cases = []
for i, path in enumerate(plan['sources']):
    row, parent = read(OUT/f'case-{i:03d}.json'), read(Path(path))
    assert row['source_path'] == path and row['source_sha256'] == digest(Path(path))
    assert row['entry'] == parent['entry']
    original = parent['menus']['both']
    policy = original['records'][-1]
    values = dict(incumbent=Q(policy['exploitability_exact']),
        raw_10k=Q(row['records']['repair'][0]['exploitability_exact']),
        raw_50k=Q(row['records']['repair'][1]['exploitability_exact']),
        repair=Q(row['choices']['repair']['score']['exploitability_exact']),
        continuation=Q(row['choices']['control']['score']['exploitability_exact']))
    assert values['repair'] <= values['incumbent'] and values['continuation'] <= values['incumbent']
    assert row['records']['control'][0]['x'] == policy['x']
    for name in ('repair', 'control'):
        choice = row['choices'][name]
        old_l, old_u = map(Q, choice['old_bounds'])
        new_l, new_u = map(Q, choice['new_bounds'])
        assert old_u == new_u and (old_u-old_l)/2 == values['incumbent']
        assert choice['accepted'] == (new_l >= old_l)
        assert (new_u-new_l)/2 == Q(row['records'][name][-1]['exploitability_exact'])
        assert Q(choice['score']['exploitability_exact']) == (
            old_u-(new_l if choice['accepted'] else old_l))/2
        assert choice['y'] == policy['y'] and choice['groups'][1] == parent['groups'][1]
        assert len(set(choice['groups'][0])) == 16
    proposed_floor = Q(row['solution']['floor'][0])
    old_floor = Q(original['solution']['floor'][0])
    assert values['raw_50k'] >= proposed_floor
    accepted_floor = proposed_floor if row['choices']['repair']['accepted'] else old_floor
    assert values['repair'] >= accepted_floor
    candidate = row['records']['repair'][-1]
    control = row['records']['control']
    cases.append(dict(board=row['entry']['case']['board'], texture=row['entry']['case']['texture'],
        regime=row['entry']['case']['regime'], values_exact={k: str(v) for k, v in values.items()},
        values={k: float(v) for k, v in values.items()}, operation=row['proposal']['operation'],
        witness_gain=float(Q(row['proposal']['net_gain'])),
        accepted=row['choices']['repair']['accepted'],
        raw_direction=direction(values['raw_50k'], values['incumbent']),
        versus_incumbent=direction(values['repair'], values['incumbent']),
        versus_continuation=direction(values['repair'], values['continuation']),
        original_floor=float(old_floor), proposed_floor=float(proposed_floor),
        accepted_floor=float(accepted_floor),
        cached_witness_repair_seconds=row['proposal_seconds']+candidate['setup_seconds']+
            candidate['active_seconds']+row['choices']['repair']['seconds'],
        continuation_seconds=control[1]['active_seconds']-control[0]['active_seconds']+
            row['choices']['control']['seconds']))
means_q = {k: sum((Q(r['values_exact'][k]) for r in cases), Q(0))/8
           for k in cases[0]['values_exact']}
summary = dict(complete=True, cases=cases, means={k: float(v) for k, v in means_q.items()},
    means_exact={k: str(v) for k, v in means_q.items()},
    flags=dict(nonregression=all(r['versus_incumbent'] != 'worse' for r in cases),
        improves_incumbent=means_q['repair'] < means_q['incumbent']-Q('1e-6'),
        beats_continuation=means_q['repair'] < means_q['continuation']-Q('1e-6')),
    reduction_percent=100*float(1-means_q['repair']/means_q['incumbent']),
    versus_continuation_percent=100*float(1-means_q['repair']/means_q['continuation']),
    proposed_cases=sum(r['operation'] is not None for r in cases),
    accepted_cases=sum(r['accepted'] for r in cases),
    directions={k: dict(Counter(r[k] for r in cases)) for k in
                ('raw_direction', 'versus_incumbent', 'versus_continuation')},
    mean_original_floor=sum(r['original_floor'] for r in cases)/8,
    mean_proposed_floor=sum(r['proposed_floor'] for r in cases)/8,
    mean_accepted_floor=sum(r['accepted_floor'] for r in cases)/8,
    mean_cached_witness_repair_seconds=sum(r['cached_witness_repair_seconds'] for r in cases)/8,
    mean_continuation_seconds=sum(r['continuation_seconds'] for r in cases)/8)
previous = read(HERE/'preflight.json')['prior_milestones']
assert len(previous) == 29
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
lines = ['# Bettor size repair 001', '',
    'One size-aware split and compensating merge on each of eight known cases.',
    'Check/half-pot/pot together; K=16; caller policy fixed at the retained 50k checkpoint.',
    'Four existing boards, uniform and polarized ranges. No fresh-board claim.', '',
    '| Case | Incumbent | Raw repair 50k | Accepted repair | Accepted continuation |',
    '|---|---:|---:|---:|---:|']
for i, row in enumerate(cases):
    v = row['values']
    lines.append(f"| {i} | {v['incumbent']:.9f} | {v['raw_50k']:.9f} | "
                 f"{v['repair']:.9f} | {v['continuation']:.9f} |")
lines += ['', 'Exploitability in chips, lower is better. Both accepted arms must be nonworse.',
    'Candidate uses 50k fresh bettor updates; continuation adds 50k to the incumbent.',
    'The 10k candidate is retained diagnostically and never selected after seeing outcomes.',
    'Worst-case bettor value determines acceptance; caller remains byte-identical.', '',
    '## Full audit and summary', '', '```json', json.dumps(summary, indent=2), '```', '',
    '## Computation and scope', '',
    'Recorded repair cost includes proposal, training setup/updates and acceptance.',
    'The witness is reused from the previous diagnostic, so its acquisition cost is excluded.',
    'Continuation excludes the initial 50k reconstruction. Diagnostic LPs, input building,',
    'profile scoring and verification are excluded from both component-cost figures.',
    'Equal additional bettor updates do not imply equal computation or live feasibility.',
    'No caller regrouping, model fitting, second repair, adoption, commit or push.',
    'No population, full-range, multiway or live-bot claim.', '',
    '## Verification', '',
    'Four new analytic checks and five inherited checks passed before freeze.',
    '1,200,000 bettor updates replayed; 16 incumbent and 16 proposed certificates checked.',
    'Sixteen exact acceptance decisions audited with independent terminal-payoff sums.',
    f"All {audit['enumerated_partitions']:,} permitted partitions independently enumerated.",
    'Verifier performs no LP solves. Caller strategy and group count verified unchanged.',
    'All 29 earlier milestones verified unchanged. Python 3.14.6, one BLAS thread.',
    'No allocation tracing; 900-second phase limits; no hard RSS cap.',
    f"Run plus verification: {receipt['seconds']:.3f} seconds, exit 0.", '',
    'Plan SHA-256: '+digest(OUT/'plan.json'), '',
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
    f.write(b'\n## Bettor size repair\n\n'
        b'[Bettor size repair 001](river-multibet-size-repair-001.md)\n'
        b'tests one fixed-capacity size split with a frozen caller and exact acceptance.\n')
assert overview.read_bytes().startswith(old)
write(HERE/'retention.json', dict(passed=True, members=len(manifest),
    milestone_sha256=digest(ARCHIVE/'milestone-manifest.json'), report_sha256=digest(REPORT),
    source_head=before['head'], commit=False, push=False))
print(json.dumps({k: v for k, v in summary.items() if k not in ('cases', 'means_exact')}, indent=2))
