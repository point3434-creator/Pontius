"""Independent arithmetic audit and retention of the regression investigation."""
from pathlib import Path
from fractions import Fraction as Q
from collections import Counter
from hashlib import sha256
import json
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = Path('D:/Pontius-worktrees/eval-runner-consolidation')
NAME = 'witness-repair-regression-diagnostic-001'
OUT = Path('D:/Pontius-training/river-abstraction-study')/NAME
ARCHIVE = ROOT/'experiments/river-abstraction-study'/NAME
REPORT = ROOT/'docs/research/river-witness-repair-regression-diagnostic-001.md'
read = lambda p: json.loads(p.read_bytes())
digest = lambda p: sha256(p.read_bytes()).hexdigest()


def write(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as f:
        f.write(json.dumps(value, sort_keys=True, indent=2, allow_nan=False)+'\n')


def direction(value):
    return 'worse' if value > Q('1e-10') else 'better' if value < -Q('1e-10') else 'equal'


plan, receipt, audit, summary = (read(OUT/p) for p in
    ('plan.json', 'receipt.json', 'audit.json', 'summary.json'))
assert receipt['exit'] == read(OUT/'worker-receipt.json')['exit'] == 0 and audit['passed']
assert audit['cases'] == 96 and audit['asymmetric_certificates'] == 384
assert audit['composed_profiles'] == 288 and audit['exact_witness_decompositions'] == 192
assert audit['new_lp_calls'] == audit['model_fits'] == audit['training_updates'] == 0
assert digest(OUT/'plan.json') == read(HERE/'freeze.json')['plan_sha256']
assert digest(OUT/'results-manifest.json') == receipt['result_manifest_sha256']
for name, expected in read(OUT/'results-manifest.json').items():
    assert digest(OUT/name) == expected, name
for name, expected in plan['pins'].items():
    assert digest(Path(name)) == expected, name
assert not ARCHIVE.exists() and not REPORT.exists()
rows = [read(OUT/f'case-{i:03d}.json') for i in range(96)]
checks = 0
for row, item in zip(rows, plan['cases'], strict=True):
    original = read(Path(item['path']))
    assert row['source_sha256'] == digest(Path(item['path']))
    assert row['panel'] == item['panel'] and row['entry'] == original['entry']
    assert Q(row['baseline_actual']) == Q(
        original['records']['control'][0]['exact_exploitability'])
    assert Q(row['repaired_actual']) == Q(
        original['records']['repaired'][1]['exact_exploitability'])
    assert Q(row['raw_actual_delta']) == Q(row['repaired_actual'])-Q(row['baseline_actual'])
    improvements = []
    for s, seat in enumerate(row['seats']):
        assert seat['seat'] == s
        lower_upper = []
        for solution in (original['baseline'], original['solution']):
            value = solution[f'seat{s}']['value']
            lo, hi = Q(value['lower_exact']), Q(value['upper_exact'])
            lower_upper.append((lo, hi) if s == 0 else (-hi, -lo))
        (oldlo, oldhi), (newlo, newhi) = lower_upper
        assert list(map(Q, seat['value_improvement_interval'])) == [newlo-oldhi, newhi-oldlo]
        assert Q(seat['new_witness_best'])-Q(seat['old_witness_best']) == newhi-oldhi
        assert newhi-oldhi == Q(seat['fixed_witness_gain'])-Q(seat['adaptation_penalty'])
        assert seat['floor_accept'] == (newlo >= oldhi)
        assert seat['security_accept'] == (Q(seat['security_improvement']) >= 0)
        assert seat['certified_worse'] == (newhi-oldlo < -Q('1e-8'))
        oldg, newg = original['baseline_groups'][s], original['proposal']['groups'][s]
        coeff = original['baseline'][f'seat{s}']['coefficients'][s]
        probability = [Q(coeff[g]) for g in oldg]
        feasible = all(len({p for p, g in zip(probability, newg) if g == label}) == 1
                       for label in set(newg))
        assert seat['structural_accept'] == feasible
        improvements.append(Q(seat['security_improvement']))
        checks += 8
    assert -sum(improvements)/2 == Q(row['raw_actual_delta'])
    for name, gate in row['gates'].items():
        accepted = [s[name+'_accept'] and s['changed'] for s in row['seats']]
        assert gate['accepted'] == accepted
        delta = -sum((v for v, keep in zip(improvements, accepted) if keep), Q(0))/2
        assert delta == Q(gate['actual_delta_exact'])
        assert Q(gate['actual_exact']) == Q(row['baseline_actual'])+delta
        if name == 'security':
            assert delta <= 0
        checks += 3

extra = {}
for panel, bets in summary.items():
    extra[panel] = {}
    for bet, value in bets.items():
        selected = [r for r in rows if r['panel'] == panel and r['entry']['bet'] == int(bet)]
        assert value['cases'] == len(selected)
        baseline = sum(Q(r['baseline_actual']) for r in selected)/len(selected)
        raw = sum(Q(r['repaired_actual']) for r in selected)/len(selected)
        assert value['baseline_actual'] == float(baseline) and value['raw_actual'] == float(raw)
        assert value['raw_directions'] == dict(Counter(
            direction(Q(r['raw_actual_delta'])) for r in selected))
        seats = [s for r in selected for s in r['seats']]
        damaged = [s for s in seats if s['certified_worse']]
        assert value['damaged_seats'] == len(damaged)
        assert value['changed_seats'] == sum(s['changed'] for s in seats)
        assert value['damaged_seats_with_free_old_merge'] == sum(
            s['merge'] is not None and Q(s['merge']['old_merge_cost']) == 0 for s in damaged)
        assert value['damaged_seats_with_costly_new_merge'] == sum(
            s['merge'] is not None and Q(s['merge']['new_merge_cost']) > 0 for s in damaged)
        assert value['damaged_seats_changing_optimum'] == sum(
            not s['structural_accept'] for s in damaged)
        check_examples = {}
        for name, expected in value['gates'].items():
            gs = [r['gates'][name] for r in selected]
            mean = sum(Q(g['actual_exact']) for g in gs)/len(gs)
            assert expected['mean_actual'] == float(mean)
            assert expected['change_percent'] == 100*float(mean/baseline-1)
            assert expected['accepted_seats'] == sum(sum(g['accepted']) for g in gs)
            assert expected['actual_directions'] == dict(Counter(
                direction(Q(g['actual_delta_exact'])) for g in gs))
            assert expected['floor_regressions'] == sum(
                Q(g['floor_delta_interval'][0]) > Q('1e-8') for g in gs)
            check_examples[name] = dict(
                improved_cases_rejected_to_baseline=sum(
                    Q(r['raw_actual_delta']) < -Q('1e-10') and
                    abs(Q(r['gates'][name]['actual_delta_exact'])) <= Q('1e-10')
                    for r in selected),
                raw_regressions_repaired=sum(Q(r['raw_actual_delta']) > Q('1e-10') and
                    Q(r['gates'][name]['actual_delta_exact']) <= 0 for r in selected))
            checks += 5
        worst = max(selected, key=lambda r: Q(r['raw_actual_delta']))
        extra[panel][bet] = dict(worst_case=worst, gates=check_examples,
            actual_regressions_with_certified_floor_improvement=sum(
                Q(r['raw_actual_delta']) > Q('1e-10') and
                Q(r['raw_floor_delta_interval'][1]) < -Q('1e-8') for r in selected))
        checks += 9

previous = {}
for directory in sorted(ARCHIVE.parent.iterdir()):
    path = directory/'milestone-manifest.json'
    if path.is_file():
        for name, expected in read(path).items():
            assert digest(directory/name) == expected, (directory, name)
        previous[directory.name] = digest(path)
assert len(previous) == 22
before = read(HERE/'worktree-before.json')
for name, expected in before['modified_tracked_files'].items():
    assert digest(ROOT/name) == expected, name
git = ['C:/Program Files/Git/cmd/git.exe', '-c', f'safe.directory={ROOT}', '-C', str(ROOT)]
assert subprocess.check_output(git+['rev-parse', 'HEAD'], text=True).strip() == before['head']

lines = ['# Witness repair regression diagnostic 001', '',
    'Retrospective investigation of all 96 cases in the pilot and confirmation.',
    'Outcomes were known before design. This does not validate a new acceptance',
    'rule on untouched boards. No production source or adopted policy changed.', '',
    '## Measured effects', '',
    'Exploitability in chips, lower is better. All methods use saved 10k policies.',
    'Each gate independently selects the original or repaired policy per seat.', '',
    '| Panel | Bet | Original | Unguarded repair | Structural | Floor | Security |',
    '|---|---:|---:|---:|---:|---:|---:|']
for panel, bets in summary.items():
    for bet, value in bets.items():
        gates = value['gates']
        lines.append(f"| {panel} | {bet} | {value['baseline_actual']:.9f} | "
            f"{value['raw_actual']:.9f} | {gates['structural']['mean_actual']:.9f} | "
            f"{gates['floor']['mean_actual']:.9f} | {gates['security']['mean_actual']:.9f} |")
lines += ['', '| Panel | Bet | Gate | Accepted seats | Actual worse cases | Floor worse cases |',
          '|---|---:|---|---:|---:|---:|']
for panel, bets in summary.items():
    for bet, value in bets.items():
        for gate, v in value['gates'].items():
            lines.append(f"| {panel} | {bet} | {gate} | {v['accepted_seats']} | "
                f"{v['actual_directions'].get('worse', 0)} | {v['floor_regressions']} |")
lines += ['', '## Mechanism', '',
    'For each seat, fixed-witness improvement minus opponent-adaptation penalty',
    'equals the change in the certified own-value upper endpoint, exactly.',
    'Both interval endpoints classify material minimax losses. The merge is also',
    're-evaluated under the repaired game\'s witness while preserving its original',
    'split membership. This separates a free-looking merge from its later cost.', '',
    '| Panel | Bet | Damaged seats | Free old merge | Costly new merge | Old policy lost |',
    '|---|---:|---:|---:|---:|---:|']
for panel, bets in summary.items():
    for bet, v in bets.items():
        lines.append(f"| {panel} | {bet} | {v['damaged_seats']} | "
            f"{v['damaged_seats_with_free_old_merge']} | "
            f"{v['damaged_seats_with_costly_new_merge']} | "
            f"{v['damaged_seats_changing_optimum']} |")
lines += ['', '## Worst raw cases', '',
    '| Panel | Bet | Case | Seat | Fixed gain | Adaptation | New merge cost |',
    '|---|---:|---|---:|---:|---:|---:|']
for panel, bets in extra.items():
    for bet, value in bets.items():
        worst = value['worst_case']
        for seat in worst['seats']:
            merge = seat['merge']
            cost = float(Q(merge['new_merge_cost'])) if merge else 0
            lines.append(f"| {panel} | {bet} | {worst['entry']['case']['id']} | "
                f"{seat['seat']} | {float(Q(seat['fixed_witness_gain'])):.9f} | "
                f"{float(Q(seat['adaptation_penalty'])):.9f} | {cost:.9f} |")
lines += ['', '## Gate interpretation and limits', '',
    'Structural checks preserve feasibility of the old asymmetric optimal policy.',
    'They do not ensure that the new finite-iteration policy reaches its quality.',
    'Floor checks compare conservative certificate endpoints, protecting the group',
    'class while leaving finite-iteration error unguarded.', '',
    'The security gate compares exact worst-case values of the saved policies.',
    'With L(x)=min_y V(x,y) and U(y)=max_x V(x,y), exploitability is (U-L)/2.',
    'Accepting bettor L only upward and caller -U only upward cannot increase',
    'exploitability in this known two-player one-bet game. Every mixed profile was',
    'checked by the existing exact evaluator. Equality is allowed; failures fall',
    'back independently per seat. No acceptance threshold was tuned.', '',
    'This guards the saved strategy, not every strategy its grouping could learn.',
    'The exact evaluator uses the full known game; sampled, approximate, multiway',
    'or online deployments do not inherit this guarantee automatically.',
    'A gate belongs in the research harness before deployment. No gate is adopted.', '',
    '## Verification and retention', '',
    'Five analytic controls and one already-observed pilot-cell preflight passed.',
    '384 asymmetric certificates and 288 composed profiles checked.',
    '192 exact witness decompositions; no new LPs, model fits or training updates.',
    f'Independent retained arithmetic checks: {checks}.',
    f"Diagnostic completed in {receipt['seconds']:.3f} seconds, exit 0.",
    'Python 3.14.6, NumPy 2.5.2, SciPy 1.18.0; one BLAS thread.',
    '600-second worker limit; no hard memory cap. No independent cold review.',
    'All 22 previous milestone manifests and members verified unchanged.',
    'No production edits, adoption, commit or push.', '',
    'Plan SHA-256: '+digest(OUT/'plan.json'), '',
    'Results manifest SHA-256: '+receipt['result_manifest_sha256'], '']
write(OUT/'summary-audit.json', dict(passed=True, arithmetic_checks=checks, extra=extra))
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
assert all(digest(ARCHIVE/name) == h for name, h in members.items())
overview = ROOT/'docs/research/README.md'
old = overview.read_bytes()
with (HERE/'research-readme-before.md').open('xb') as f:
    f.write(old)
with overview.open('ab') as f:
    f.write(b'\n## Witness repair regression diagnostic\n\n'
        b'[Regression diagnostic 001](river-witness-repair-regression-diagnostic-001.md)\n'
        b'traces all 96 retained repair cases and compares three acceptance checks.\n')
assert overview.read_bytes().startswith(old)
write(HERE/'retention.json', dict(passed=True, milestone_sha256=digest(
    ARCHIVE/'milestone-manifest.json'), members=len(members), previous=previous,
    report_sha256=digest(REPORT), commit=False, push=False, source_head=before['head']))
print(json.dumps(dict(summary=summary, arithmetic_checks=checks,
    retention=read(HERE/'retention.json')), indent=2))
