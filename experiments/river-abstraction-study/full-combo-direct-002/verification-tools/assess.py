"""Post-run interpretation, preserving the frozen pass/refusal classifications."""
import experiment as e
out = e.Path('D:/Pontius-training/river-abstraction-study')/e.NAME
audit = e.read(out/'full-profile-audit.json')
assert audit['passed'] and audit['new_lp_calls'] == 0 and len(audit['profiles']) == 4
lines = ['# Full-hand result assessment', '',
    'Post-run exact evaluation of every retained primal/dual strategy, including the two',
    'that missed the frozen 1e-8 gap threshold. No new LP solves or relaxed thresholds.', '',
    '| Situation | Grouped error | Full-hand error | Strict threshold | Grouped s | Full s |',
    '|---|---:|---:|---|---:|---:|']
facts = []
for j, profile in enumerate(audit['profiles']):
    row = e.read(out/f'case-{j:03d}.json')
    assert profile['source_sha256'] == e.digest(out/f'case-{j:03d}.json')
    cmp = row['compressed']
    seconds = cmp['training_seconds']+cmp['scoring_seconds']
    process = e.read(out/f'worker-{j:03d}-receipt.json')
    assert process['observed_pid'] == row['executing_pid']
    facts.append(dict(case=j, compressed_error=cmp['exploitability'],
        full_error=profile['exploitability'], grouped_seconds=seconds,
        full_seconds=row['full']['seconds'],
        sampled_private_mib=process['sampled_peak_private_bytes']/1024**2,
        os_peak_commit_mib=process['os_peak_commit_bytes']/1024**2,
        setup_seconds=row['setup_seconds'],
        strict_pass=profile['meets_frozen_gap_threshold']))
    lines.append(f"| {j+1} | {cmp['exploitability']:.9g} | {profile['exploitability']:.9g} | "
                 f"{'pass' if profile['meets_frozen_gap_threshold'] else 'miss'} | "
                 f"{seconds:.3f} | {row['full']['seconds']:.3f} |")
lines += ['', 'Error means half the exact unrestricted-response gap, normalized by 10/actual pot.',
    'Strict pass requires gap <=1e-8, hence error <=5e-9. A missed strict threshold remains',
    'a miss, even when the returned strategy has a small precisely measured error.',
    'The full-hand and grouped strategies were evaluated on the same full payoff matrices.', '',
    'All four full-hand strategies have less error and took less measured solve time than',
    'the existing 50000-update grouped learner. This compares the concrete LP and learner',
    'implementations, not an inherent speed advantage of full representation over grouping.',
    'Direct LP is the useful reference for this restricted river family; additional repair',
    'tuning has a weaker case until a larger tree makes full solving expensive.', '',
    '| Situation | Shared preparation s | Sampled worker private MiB | OS peak commit MiB |',
    '|---|---:|---:|---:|']
for f in facts:
    lines.append(f"| {f['case']+1} | {f['setup_seconds']:.3f} | "
                 f"{f['sampled_private_mib']:.1f} | {f['os_peak_commit_mib']:.1f} |")
lines += ['', 'Memory covers the entire case worker, including both arms and diagnostic LPs.',
    'Timing excludes shared preparation and grouping-floor diagnostics. One observation',
    'per case; fixed 10s per LP limits, 120s child limit and sampled 3072 MiB private limit.', '',
    'The first attempt measured the Windows launcher rather than its actual worker; its',
    'memory figures and stop claims are invalid. The corrected repeat verifies executing',
    'PID identity and an observed 128 MiB allocation. Original attempt bytes are preserved.',
    'The coordinator initially misread a complete audit as all strict passes and corrected',
    'that statement after inspecting the individual refusals. This assessment preserves',
    'the two misses and supplies their exact residual errors from retained LP vectors.', '',
    '## Per-hand tables', '',
    'Each CSV contains 1081 rows, with both players\' ranges, group labels, full and grouped',
    'bet/check probabilities and call probabilities facing each size. Fold is one minus call.',
    'The strict-threshold status is included in every row. Responses on unreachable branches',
    'can differ without changing exploitability. The earlier hand-detail-000.csv export was',
    'interrupted after its first case; the complete current tables are the -v2.csv files.', '']
for j in range(4):
    lines.append(f'- [Situation {j+1}](hand-detail-{j:03d}-v2.csv)')
lines += ['', 'Scope remains check-versus-bet, followed only by fold/call, on four known public',
    'ranges from an early, fallback-heavy checkpoint. All card combinations are represented,',
    'but the full river action tree and multiplayer solving are not. No six-max strength claim.', '']
with (out/'assessment.md').open('x', encoding='utf-8', newline='\n') as f:
    f.write('\n'.join(lines))
e.write(out/'assessment.json', dict(cases=facts, new_solver_invocations=0,
    strict_passes=sum(f['strict_pass'] for f in facts),
    first_attempt_policy_identity=[p['raw_lp_solutions_identical_to_first_attempt']
                                   for p in audit['profiles']]))
print(facts)
