# River time-budget quality 001: completed

Additional graph-solver iterations reduced independently audited error at every
tested checkpoint on both retained river trees. This converts the prior execution
gain into better restricted-game approximate solutions, subject to measured cost.
It does not establish better six-max play, new-board transfer, or a live deadline.

## Frozen experiment

User launch authorization: "Let's launch it". Plan SHA-256:
`6da2525fc78e836b6d7fd412ec08c415636ea1c21bf4074a87ea14657971bc5a`.
The previously sealed build and preflight are preserved byte-for-byte; their
"not invoked" statements record the earlier build state. completion.json and
run/receipt.json record the subsequent completed invocation.

Same case-001 board/ranges, two nested heads-up river trees: checkback and raise.
Each role has 1,081 private hands. DCFR+ alpha 1.5, denominator 1.5, gamma 4,
alternating players and own-reach averaging remain unchanged. Float64 throughout.
Graph replay uses the retained static solver and native cuBLAS bridge unchanged.
Horizon 16,384, checkpoints 2,048 / 4,096 / 8,192 / 16,384, three fresh
trajectories per game. Every trajectory begins uniform after warmup/reset.
The 2,048 checkpoint must match the previous graph-policy digest exactly.

Python 3.14.6, CuPy 14.2.0, NumPy 2.5.2, RTX 5080. CPU libraries use one BLAS
thread. Each worker has a 180-second timeout and 3,072 MiB sampled private-memory
stop; the coordinator bounds execution to a 600-second campaign envelope.
CuPy pool limit is 1,024 MiB and does not cap other CUDA allocations.
The filesystem kernel cache was warmed by build validation, not newly empty.

## Completion and correctness

All 6 training trajectories and 24 independent audits completed,
plus the frozen selector tests. All workers exited zero without a resource stop.
Summed observed child-process wall time: 138.4 s.
Maximum sampled private memory across workers: 1255.8 MiB.
The child-wall sum excludes coordinator overhead and is not total wall time.
Every checkpoint has identical policy bytes across the three repeats. Audits
were nevertheless executed separately for every repeat, preserving audit-time
variation in budget decisions. All 24 certificates agree with the float evaluator
within 1e-10. Exact bounds use 2^48-quantized policy probabilities over the
original stored binary64 payoff matrices. No game or payoff reconstruction changed.
Observed adjacent-checkpoint error regressions: 0; strict gap <= 1e-8
passes: 0 of 24. These remain approximate solutions.

## Quality and cost

Error is exploitability: half the exact best-response gap. Units are ten per
starting pot; divide by ten for fraction of pot. Times are seconds. Charged
ranges cover all three repetitions, not confidence intervals.

| Game | Iterations | Exact error | Reduction vs 2,048 | Solve median | Charged min–max |
|---|---:|---:|---:|---:|---:|
| checkback | 2,048 | 1.34795943e-05 | 1.00x | 0.651 | 4.396–4.451 |
| checkback | 4,096 | 4.73346247e-06 | 2.85x | 1.314 | 5.029–5.106 |
| checkback | 8,192 | 1.84974205e-06 | 7.29x | 2.624 | 6.317–6.403 |
| checkback | 16,384 | 7.07266214e-07 | 19.06x | 5.256 | 8.926–8.998 |
| raise | 2,048 | 0.00013207718 | 1.00x | 1.575 | 6.741–6.795 |
| raise | 4,096 | 3.68655546e-05 | 3.58x | 3.139 | 8.303–8.391 |
| raise | 8,192 | 1.37882466e-05 | 9.58x | 6.267 | 11.447–11.460 |
| raise | 16,384 | 5.82085574e-06 | 22.69x | 12.561 | 17.556–17.673 |

## Declared budget decisions

For each repeat independently, choose the latest affordable checkpoint. Error
does not enter selection. A missing cell stays missing. Each row lists all three
selected iteration counts in repeat order; a median cannot erase a miss.

| Game | Budget s | Selected iterations, repeats 0 / 1 / 2 | Coverage |
|---|---:|---|---:|
| checkback | 3 | none / none / none | 0/3 |
| checkback | 5 | 2,048 / 2,048 / 2,048 | 3/3 |
| checkback | 10 | 16,384 / 16,384 / 16,384 | 3/3 |
| checkback | 15 | 16,384 / 16,384 / 16,384 | 3/3 |
| raise | 3 | none / none / none | 0/3 |
| raise | 5 | none / none / none | 0/3 |
| raise | 10 | 4,096 / 4,096 / 4,096 | 3/3 |
| raise | 15 | 8,192 / 8,192 / 8,192 | 3/3 |

Charged time is observed launcher-to-checkpoint elapsed, including imports,
binding checks, preparation, prior checkpoint observations, averaging, float
scoring and policy export; plus all otherwise unassigned process overhead; plus
that checkpoint's separately measured fresh independent audit process.
Unassigned process overhead is max(0, parent worker wall minus child elapsed
through close), charged to every prefix. Earlier checkpoints' exact audits are
research diagnostics and do not enter the counterfactual later-prefix cost.
This follows the frozen design and is accounting, not an enforced online deadline.
No fixed-time CPU/GPU race or error-based policy selection was performed.

## Interpretation

The previous graph experiment demonstrated faster execution at identical quality.
This campaign demonstrates that spending additional computation improved quality
on these same restricted games. It also shows why reporting only solve time is
insufficient: preparation and independent verification consume part of each budget.
Audit costs remain included; no failed budget or strict-convergence threshold was relaxed.

Freeze the solver settings and this quality/cost result. The next useful check
is transfer to a fresh board/range configuration, with the same selection and
accounting rules. Further optimization or a higher iteration ceiling is not
needed to establish the present finding. One board with two nested public trees
does not establish generalization, even with repeat-identical outputs.
Three repetitions measure local timing variation, not poker sampling uncertainty.
No production code, policy adoption, commit or push was part of this campaign.
