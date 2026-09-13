"""Generate the completed campaign report from reconciled evidence."""
from pathlib import Path
import json
HERE=Path(__file__).parent
a=json.loads((HERE/'assessment.json').read_text())
assert a['complete']
lines=['# River time-budget quality 001: completed','',
'Additional graph-solver iterations reduced independently audited error at every',
'tested checkpoint on both retained river trees. This converts the prior execution',
'gain into better restricted-game approximate solutions, subject to measured cost.',
'It does not establish better six-max play, new-board transfer, or a live deadline.','',
'## Frozen experiment','',
'User launch authorization: "Let\'s launch it". Plan SHA-256:',
'`6da2525fc78e836b6d7fd412ec08c415636ea1c21bf4074a87ea14657971bc5a`.',
'The previously sealed build and preflight are preserved byte-for-byte; their',
'"not invoked" statements record the earlier build state. completion.json and',
'run/receipt.json record the subsequent completed invocation.','',
'Same case-001 board/ranges, two nested heads-up river trees: checkback and raise.',
'Each role has 1,081 private hands. DCFR+ alpha 1.5, denominator 1.5, gamma 4,',
'alternating players and own-reach averaging remain unchanged. Float64 throughout.',
'Graph replay uses the retained static solver and native cuBLAS bridge unchanged.',
'Horizon 16,384, checkpoints 2,048 / 4,096 / 8,192 / 16,384, three fresh',
'trajectories per game. Every trajectory begins uniform after warmup/reset.',
'The 2,048 checkpoint must match the previous graph-policy digest exactly.','',
'Python 3.14.6, CuPy 14.2.0, NumPy 2.5.2, RTX 5080. CPU libraries use one BLAS',
'thread. Each worker has a 180-second timeout and 3,072 MiB sampled private-memory',
'stop; the coordinator bounds execution to a 600-second campaign envelope.',
'CuPy pool limit is 1,024 MiB and does not cap other CUDA allocations.',
'The filesystem kernel cache was warmed by build validation, not newly empty.','',
'## Completion and correctness','',
f"All {a['trajectories']} training trajectories and {a['audits']} independent audits completed,",
'plus the frozen selector tests. All workers exited zero without a resource stop.',
f"Summed observed child-process wall time: {a['summed_child_wall_seconds']:.1f} s.",
f"Maximum sampled private memory across workers: {a['peak_private_mib']:.1f} MiB.",
'The child-wall sum excludes coordinator overhead and is not total wall time.',
'Every checkpoint has identical policy bytes across the three repeats. Audits',
'were nevertheless executed separately for every repeat, preserving audit-time',
'variation in budget decisions. All 24 certificates agree with the float evaluator',
'within 1e-10. Exact bounds use 2^48-quantized policy probabilities over the',
'original stored binary64 payoff matrices. No game or payoff reconstruction changed.',
f"Observed adjacent-checkpoint error regressions: {a['regressions']}; strict gap <= 1e-8",
f"passes: {a['strict_passes']} of 24. These remain approximate solutions.",'',
'## Quality and cost','',
'Error is exploitability: half the exact best-response gap. Units are ten per',
'starting pot; divide by ten for fraction of pot. Times are seconds. Charged',
'ranges cover all three repetitions, not confidence intervals.','',
'| Game | Iterations | Exact error | Reduction vs 2,048 | Solve median | Charged min–max |',
'|---|---:|---:|---:|---:|---:|']
for r in a['aggregates']:
    anchor=next(x['error'] for x in a['aggregates'] if x['case']==r['case'] and x['iterations']==2048)
    lines.append(f"| {r['case']} | {r['iterations']:,} | {r['error']:.9g} | "
        f"{anchor/r['error']:.2f}x | {r['training_median']:.3f} | "
        f"{r['charged_min']:.3f}–{r['charged_max']:.3f} |")
lines += ['', '## Declared budget decisions','',
'For each repeat independently, choose the latest affordable checkpoint. Error',
'does not enter selection. A missing cell stays missing. Each row lists all three',
'selected iteration counts in repeat order; a median cannot erase a miss.','',
'| Game | Budget s | Selected iterations, repeats 0 / 1 / 2 | Coverage |',
'|---|---:|---|---:|']
for r in a['budgets']:
    selected=' / '.join('none' if x is None else f'{x:,}' for x in r['selected_iterations'])
    lines.append(f"| {r['case']} | {r['budget']} | {selected} | {r['coverage']}/3 |")
lines += ['', 'Charged time is observed launcher-to-checkpoint elapsed, including imports,',
'binding checks, preparation, prior checkpoint observations, averaging, float',
'scoring and policy export; plus all otherwise unassigned process overhead; plus',
'that checkpoint\'s separately measured fresh independent audit process.',
'Unassigned process overhead is max(0, parent worker wall minus child elapsed',
'through close), charged to every prefix. Earlier checkpoints\' exact audits are',
'research diagnostics and do not enter the counterfactual later-prefix cost.',
'This follows the frozen design and is accounting, not an enforced online deadline.',
'No fixed-time CPU/GPU race or error-based policy selection was performed.','',
'## Interpretation','',
'The previous graph experiment demonstrated faster execution at identical quality.',
'This campaign demonstrates that spending additional computation improved quality',
'on these same restricted games. It also shows why reporting only solve time is',
'insufficient: preparation and independent verification consume part of each budget.',
'Audit costs remain included; no failed budget or strict-convergence threshold was relaxed.',
'', 'Freeze the solver settings and this quality/cost result. The next useful check',
'is transfer to a fresh board/range configuration, with the same selection and',
'accounting rules. Further optimization or a higher iteration ceiling is not',
'needed to establish the present finding. One board with two nested public trees',
'does not establish generalization, even with repeat-identical outputs.',
'Three repetitions measure local timing variation, not poker sampling uncertainty.',
'No production code, policy adoption, commit or push was part of this campaign.','']
with (HERE/'report.md').open('x',encoding='utf-8',newline='\n') as f:
    f.write('\n'.join(lines))
