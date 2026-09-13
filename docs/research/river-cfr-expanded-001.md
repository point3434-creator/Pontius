# Expanded river CFR 001: capacity and exact residuals

All 24 training runs and eight independent rational audits completed within the original
sampled 3,072 MiB per-worker budget on the two exact trees where the LP stopped on memory.
This demonstrates capacity for independently checked approximate solutions, not a full
NLHE solution or strict equilibrium convergence. Strict gap passes: 0/8.

## Game and controls

Same previously observed case 001, pot 29 and effective stack 186, 1,081 private hands
per role, retained factorized collision-aware ranges, and original binary64 payoff units.
The checkback tree allows the second player to bet after a check: 15 public nodes and
nine terminals. The raise tree additionally permits the specified all-in response:
27 public nodes and 17 terminals. Both match the frozen expansion plan member for member;
all engine terminal paths were checked with win/tie/loss outcomes (27 and 51 checks).
No board, range, action, card removal, or payoff simplification was introduced.

Four fixed arms from the prior studies, each with three fresh-process repeats, 2,048
alternating iterations and checkpoints at 16, 64, 256, 1,024 and 2,048. Same float64 CPU
solver, bootstrap and test bytes; Python 3.14.6, NumPy 2.5.2, one numerical thread.
All arms use gamma=4. Discounted arms use alpha=1.5; paper and predictive arms have
denominator +1, while released-code DCFR+ has +1.5. No parameter tuning. The two unmatched
averaging controls were omitted in advance to bound this capacity test. A copied plan
description still says last three controls; preflight.json records the clarification.
The structured four-arm arrays, design and actual receipts agree. No extra arms ran.

## Results at the fixed iteration budget

Exploitability is half the exact best-response interval width; smaller is better.
Units set the starting pot to 10, so divide by 10 for a fraction of pot.

| Tree | Configuration | Exploitability | Median training s | Worker peak MiB | Exact audit s | Audit peak MiB |
|---|---|---:|---:|---:|---:|---:|
| checkback | CFR+, matched averaging | 9.23894e-05 | 7.333 | 147.4 | 1.421 | 403.5 |
| checkback | DCFR+, paper definition | 1.60429e-05 | 7.416 | 147.3 | 1.453 | 404.5 |
| checkback | PDCFR+, matched parameters | 0.000117488 | 7.391 | 147.3 | 1.393 | 403.4 |
| checkback | DCFR+, code definition | 1.34796e-05 | 7.271 | 147.1 | 1.388 | 403.6 |
| raise | CFR+, matched averaging | 0.000481376 | 15.036 | 238.4 | 2.827 | 733.7 |
| raise | DCFR+, paper definition | 0.000190656 | 14.840 | 238.3 | 2.790 | 733.4 |
| raise | PDCFR+, matched parameters | 0.0006483 | 15.277 | 238.2 | 2.953 | 733.5 |
| raise | DCFR+, code definition | 0.000132077 | 14.963 | 238.3 | 2.754 | 733.0 |

- checkback: paper DCFR+ vs matched CFR+ error reduction 5.759x; matched prediction/DCFR+ error ratio 7.323; lowest error: dcfr_code.
- raise: paper DCFR+ vs matched CFR+ error reduction 2.525x; matched prediction/DCFR+ error ratio 3.400; lowest error: dcfr_code.

Ratios below one in the prediction comparison favor prediction; above one disfavor it.
Compare algorithms within each game. Expanding the game changes the equilibrium and
available deviations, so cross-tree absolute errors or profile values are not strength
improvements. The exact certificates bound residuals in each complete declared tree.

## Verification and timing boundaries

The existing four-method test suite passed before freezing. The prior solver, test and
bootstrap files match by hash. The retained independent rational evaluator checks every
final profile after behavior quantization onto the 2^48 grid. Float value and bound results
agree within 1e-10. The four equilibrium-bound intervals intersect within each game.
No completed full-range LP reference exists for these expanded cases, and no smaller-game
reference was substituted. There were zero LP invocations in this experiment.

Policy arrays at all five checkpoints match byte for byte across three repeats of each
arm. Repeats measure determinism and timing variability, not independent boards or match
samples. Intermediate curves use floating evaluation; final residuals are rationally
verified. The sample is one retained position under two nested action menus.

Training excludes imports, input loading, checkpoint evaluation, serialization and the
separate exact audit. Worker-wall and audit-wall receipts include their process startup;
assessment.json reports both. Shared payoff arrays use 44.58 MiB and 89.15 MiB, respectively.
Prior LP memory stops and current CFR memory are whole-worker measurements with their
respective implementations, not a controlled memory-only substitution inside one solver.
Every worker had a 180-second timeout and 50 ms sampled memory stop, not a hard cap.
No resource limit or observer failure occurred. Retained stop receipts remain unchanged.

## What this enables next

The iterative payoff-product route now has useful capacity evidence on both formerly
blocked trees. Carry the measured quality curves into the queued GPU-CFR assessment.
First establish whether execution overhead or matrix products dominate; retain setup,
memory, quality and repeat-solve boundaries. A GPU port is not yet justified by its paper's
speedup headline, and no neural approximation was needed for these two cases.
Later neural discounted CFR remains deferred. This run does not establish exact bunching,
six-max strength, arbitrary betting-tree coverage or complete live decision latency.

## Retention and authority

User authorization: "Let's test it". Source and configuration pins are in each cell's
plan.json; root preflight.json binds the two plan digests. Every run and audit is retained.
No automatic retries, commits, pushes, bot invocations or policy adoptions were performed.
This is an author-run experiment with an independent evaluator, not a cold agent review.
