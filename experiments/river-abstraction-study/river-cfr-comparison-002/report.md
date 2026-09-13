# River CFR comparison 002: different-position confirmation

Paper DCFR+ has 6.56x less error than matched CFR+. Matched prediction/DCFR+ error ratio is 0.891. Lowest-error arm: dcfr_code.

## Scope and identity

Retained case 000 was selected as the lowest-index position not used by comparison 001,
before inspecting its CFR outcomes. It is a previously studied case, not an untouched
holdout. Board card IDs: [37, 38, 30, 35, 28]; pot: 279.
Both roles retain all 1,081 legal private hands and the original factorized, collision-aware
range model. The baseline tree has 2 distinct root actions;
the shorter stack collapses the opening sizes into one bet. Changing the position changes
board, pot, stack, ranges and effective action menu together; this is not a board-only ablation.

Solver, tests and bootstrap match comparison 001 byte for byte. Driver differences are
limited to identity, authorization, and case/reference selection, verified by whole-file
comparison. All six arms, parameters, averaging rules, alternating update order, 2,048
iterations, checkpoint times in iterations, precision, single-thread settings and limits
are identical. Three fresh-process repeats per arm rotate order. Python 3.14.6 only.
Authorization: "Ok let's run the next". Design was retained before preparation and run.
Plan SHA-256: 57e6d7a4795d1c6097d1bda5be6b21d64d3eaf6da8d6f2b9b65785b9803f8e03

## Final results

Exploitability is half the exact best-response interval width in units where pot=10.
Lower is better; divide by 10 for fraction of the starting pot. The strict column asks
whether the full gap meets the existing <=1e-8 threshold, independently of result validity.

| Configuration | Exploitability | Median training s | Worker peak MiB | Strict gap pass |
|---|---:|---:|---:|---|
| CFR+, matched averaging | 3.95307e-07 | 1.757 | 111.7 | False |
| DCFR+, paper definition | 6.02879e-08 | 1.708 | 111.7 | False |
| PDCFR+, matched parameters | 5.37213e-08 | 1.790 | 111.6 | False |
| CFR+, linear averaging | 1.88009e-06 | 1.677 | 111.7 | False |
| DCFR+, released-code definition | 4.51116e-08 | 1.726 | 111.9 | False |
| PDCFR+, published parameters | 1.57932e-06 | 1.739 | 111.9 | False |

Strict passing arms: none.
All 18 runs and six independent rational final audits completed. Final policy arrays at
every stored checkpoint are byte-identical across repeats. These repeats establish
determinism and timing variation, not three independent strategic samples. Checkpoint
curves use the floating evaluator; final errors use the retained rational evaluator after
2^48 behavior quantization. All final value/bound checks agree within 1e-10, and each
interval contains the retained LP equilibrium interval. The LP reference was not rerun.

The four existing test methods passed again. The game engine audit checked all terminal
paths for win/tie/loss, 9 checks. These are author-run checks,
not an independent agent review. No algorithm parameters were changed after results.

## What transferred from the first case?

| Configuration | First case 001 error | Confirmation case 000 error |
|---|---:|---:|
| CFR+, matched averaging | 4.93316e-05 | 3.95307e-07 |
| DCFR+, paper definition | 6.09262e-06 | 6.02879e-08 |
| PDCFR+, matched parameters | 3.65225e-05 | 5.37213e-08 |
| CFR+, linear averaging | 7.12163e-05 | 1.88009e-06 |
| DCFR+, released-code definition | 3.5038e-06 | 4.51116e-08 |
| PDCFR+, published parameters | 7.32175e-05 | 1.57932e-06 |

Paper DCFR+/matched CFR+ error reduction: first case
8.10x; confirmation 6.56x.
Matched prediction/DCFR+ error ratio: first case
5.995; confirmation
0.891. Below one favors prediction; above one disfavors it.
Interpret ranking within each game; different difficulty makes absolute errors across
games unsuitable as a pooled strength score. Two selected retained cases do not establish
a universal algorithm ranking. Keep both discount definitions and prediction controls in
the evidence; do not turn the initial board's prediction loss into a general prohibition.

## Cost boundaries and next decision

Training excludes array load, checkpoint scoring, serialization, process startup and the
independent rational audit. All corresponding worker-wall, audit-compute, and memory figures
are recorded separately in assessment.json. Shared payoff arrays use
26.75 MiB. Preparation took 0.0271 s,
excluding imports, engine audit and freezing. The 180-second/3,072-MiB per-worker limits
never fired; memory was sampled every 50 ms, not enforced as a hard cap.

Next, test iterative quality and capacity on the expanded river trees that stopped inside
HiGHS. The present simpler-tree confirmation cannot establish that capacity result.
GPU-CFR remains queued after the CPU capacity test; neural discounted CFR remains later.
No six-max strength, live decision deadline, or folded-card bunching claim follows.
No commit, push, bot invocation or strategy adoption was performed.
