"""Retain successes and refusals; never turn a survivor mean into panel evidence."""
import experiment as e
import shutil

OUT = e.Path('D:/Pontius-training/river-abstraction-study')/e.NAME
ARCHIVE = e.HISTORY/e.NAME
REPORT = e.ROOT/'docs/research/river-full-combo-direct-001.md'
plan, receipt = e.read(OUT/'plan.json'), e.read(OUT/'receipt.json')
assert e.digest(OUT/'plan.json') == e.read(e.HERE/'freeze.json')['plan_sha256']
assert e.digest(OUT/'results-manifest.json') == receipt['result_manifest_sha256']
for member, value in e.read(OUT/'results-manifest.json').items():
    assert e.digest(OUT/member) == value
e.bindings(plan)
summary = dict(cases=[], complete=receipt['complete'])
for j, status in enumerate(receipt['cases']):
    process = e.read(OUT/f'worker-{j:03d}-receipt.json')
    item = dict(case=j, verified=status.get('verify', False),
        sampled_worker_private_mib=process['sampled_peak_private_bytes']/1024**2,
        os_worker_peak_commit_mib=process['os_peak_commit_bytes']/1024**2,
        process_stop=process['stop_reason'], process_exit=process['exit'])
    if item['verified']:
        row = e.read(OUT/f'case-{j:03d}.json')
        cmp, full, floor = row['compressed'], row['full'], row['floor']
        item.update(pot=row['inputs']['menu']['pot'],
            sizes=row['inputs']['menu']['distinct_sizes'],
            compressed_exploitability=cmp['exploitability'],
            compressed_seconds=cmp['training_seconds']+cmp['scoring_seconds'],
            compressed_training_seconds=cmp['training_seconds'],
            full_status=full['status'], full_seconds=full['seconds'],
            full_exact_bound_seconds=full['exact_bound_seconds'],
            setup_seconds=row['setup_seconds'], floor_status=floor['status'])
        if full['status'] == 'certified':
            low, high = map(e.Q, full['solution']['bounds'])
            item['full_exploitability'] = float((high-low)/2)
            item['value_interval'] = full['solution']['bounds']
            item['time_ratio_full_over_compressed'] = full['seconds']/item['compressed_seconds']
        if floor['status'] == 'certified':
            item['grouping_floor'] = [float(e.Q(v)) for v in floor['solution']['floor']]
        item['lp_calls'] = {name: [dict(status=c['status'], seconds=c['seconds'],
            iterations=c['iterations'], message=c['message']) for c in row[name]['calls']]
            for name in ('full', 'floor')}
    summary['cases'].append(item)
summary['all_full_certified'] = all(v.get('full_status') == 'certified' for v in summary['cases'])
summary['means'] = None
if summary['all_full_certified'] and summary['complete']:
    summary['means'] = {k: sum(v[k] for v in summary['cases'])/4 for k in
        ('compressed_exploitability', 'full_exploitability', 'compressed_seconds', 'full_seconds')}
previous = e.read(e.HERE/'preflight.json')['prior_milestones']
for name, expected in previous.items():
    folder = e.HISTORY/name
    assert e.digest(folder/'milestone-manifest.json') == expected
    for member, value in e.read(folder/'milestone-manifest.json').items():
        assert e.digest(folder/member) == value
before = e.read(e.HERE/'worktree-before.json')
for name, expected in before['modified_tracked_files'].items():
    assert e.digest(e.ROOT/name) == expected
git = ['C:/Program Files/Git/cmd/git.exe', '-c', f'safe.directory={e.ROOT}', '-C', str(e.ROOT)]
assert e.subprocess.check_output(git+['rev-parse', 'HEAD'], text=True).strip() == before['head']
assert not ARCHIVE.exists() and not REPORT.exists()
lines = ['# Full-combo direct 001', '',
    'Same four actual-pot public-range games; full 1081-hand LP versus K=16 compression.',
    'Three check/all-in games and one check/bet14/bet29 game; no duplicate bet actions.', '',
    '## Results', '',
    '| Case | Sizes | Compressed exploitability | Grouping floor upper | Full exploitability |',
    '|---|---|---:|---:|---:|']
for item in summary['cases']:
    if not item['verified']:
        lines.append(f"| {item['case']} | - | unverified | - | unverified |")
        continue
    floor = f"{item['grouping_floor'][1]:.9g}" if 'grouping_floor' in item else 'not certified'
    full = f"{item['full_exploitability']:.9g}" if 'full_exploitability' in item else 'not certified'
    lines.append(f"| {item['case']} | {item['sizes']} | "
                 f"{item['compressed_exploitability']:.9g} | {floor} | {full} |")
lines += ['', 'Lower is better. Exploitability is half the unrestricted-response gap, in normalized',
    'chips (payoffs scaled by 10/actual pot). Multiply by actual pot/10 for actual chip units.',
    'Exact rational certificates refer to the binary64 payoff matrix, gap at most 1e-8.', '',
    '| Case | Compressed + score s | Full solve + certificate s | Full exact bounds s |',
    '|---|---:|---:|---:|']
for item in summary['cases']:
    if item['verified']:
        lines.append(f"| {item['case']} | {item['compressed_seconds']:.3f} | "
                     f"{item['full_seconds']:.3f} | {item['full_exact_bound_seconds']:.3f} |")
lines += ['', 'Compressed time includes learner setup, 50000 updates, averaging and final score.',
    'Full time includes dense LP assembly, primal/dual solves and exact original-matrix bounds.',
    'Shared payoff/integer-array preparation and grouping-floor diagnostics are excluded.',
    'This compares operating points, not equal compute or optimally tuned algorithms.',
    'Order alternates by case, with one timing observation. These are not stable speed ratios.', '',
    '| Case | Sampled worker private MiB | OS worker peak commit MiB | Verified |',
    '|---|---:|---:|---|']
for item in summary['cases']:
    lines.append(f"| {item['case']} | {item['sampled_worker_private_mib']:.1f} | "
                 f"{item['os_worker_peak_commit_mib']:.1f} | {item['verified']} |")
lines += ['', 'Memory covers the entire worker, including both arms and diagnostics; it cannot be',
    'attributed exclusively to direct or compressed solving. Sample interval 50ms; 3072 MiB',
    'private-memory stop and 120s wall stop per child. This is not a hard memory cap.', '',
    '## Solver outcomes', '']
for item in summary['cases']:
    if not item['verified']:
        lines.append(f"- Case {item['case']}: process exit {item['process_exit']}, "
                     f"stop {item['process_stop']}; no verified strategy comparison.")
    else:
        lines.append(f"- Case {item['case']}: full {item['full_status']}; floor {item['floor_status']}.")
        for name, calls in item['lp_calls'].items():
            lines.append(f"  {name} LP statuses: {[v['status'] for v in calls]}; "
                         f"iterations: {[v['iterations'] for v in calls]}.")
lines += ['', 'Every original solver status, option, raw solution vector and refusal is retained.',
    'Time-limited or uncertified candidates are not reported as solved equilibria.', '',
    '## Scope', '',
    'Full detail means independently represented private holdings, not a full betting tree.',
    'The caller cannot bet after a check or reraise; other legal bet sizes are omitted.',
    'Ranges are those of the early checkpoint, with substantial postflop fallback dependence.',
    'Folded-player cards are not jointly marginalized. No new training or fitted abstraction.',
    'Four known cases establish neither board generalization nor six-max playing strength.',
    'The quality comparison changes representation and solver method together. It establishes',
    'these concrete operating points, not a causal speed effect from representation alone.', '',
    '## Verification', '',
    'Three preflight tests cover one/two-size literal bounds, full-hand small LP parity and',
    'all four actual game inputs; three monitor checks exercise both stops and success.',
    'Each successful verifier replays 50000 learner updates, checks all payoff coefficients,',
    'rechecks returned full/group certificates without new LP solves, and repeats engine',
    'settlements. Exact full profiles also face three literal subgame comparisons.',
    f"Complete process/verification census: {receipt['complete']}.",
    f"All four full-hand pairs certified: {summary['all_full_certified']}.",
    f"Total bounded campaign time: {receipt['seconds']:.3f}s.",
    f'All {len(previous)} prior milestones preserved. No production changes, commit or push.', '',
    'Plan SHA-256: '+e.digest(OUT/'plan.json'), '',
    'Results manifest SHA-256: '+receipt['result_manifest_sha256'], '']
e.write(OUT/'summary.json', summary)
with REPORT.open('x', encoding='utf-8', newline='\n') as f:
    f.write('\n'.join(lines))
shutil.copytree(OUT, ARCHIVE)
shutil.copytree(e.HERE, ARCHIVE/'verification-tools',
                ignore=shutil.ignore_patterns('plan.json', '__pycache__'))
shutil.copyfile(REPORT, ARCHIVE/'report.md')
manifest = {p.relative_to(ARCHIVE).as_posix(): e.digest(p)
            for p in sorted(ARCHIVE.rglob('*')) if p.is_file()}
e.write(ARCHIVE/'milestone-manifest.json', manifest)
for member, value in manifest.items():
    assert e.digest(ARCHIVE/member) == value
index = e.ROOT/'docs/research/README.md'
old = index.read_bytes()
index.write_bytes(old+('\n## Full-hand direct river solving\n\n'
    '[Direct comparison 001](river-full-combo-direct-001.md) measures full 1081-hand LP\n'
    'quality, time and case memory against the compressed learner on four actual-pot games.\n').encode())
assert index.read_bytes().startswith(old)
e.write(e.HERE/'retention.json', dict(report=str(REPORT), archive=str(ARCHIVE),
    members=len(manifest), manifest_sha256=e.digest(ARCHIVE/'milestone-manifest.json'),
    prior_milestones_preserved=len(previous), committed=False, pushed=False))
print(e.read(e.HERE/'retention.json'))
print(summary)
