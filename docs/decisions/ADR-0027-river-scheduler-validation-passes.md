# ADR-0027: Frozen river scheduler passes validation

**Status:** Accepted; unchanged test evaluation authorized

**Date:** 2026-08-19

## Decision

Accept the selection-free validation result for
`river-post-probe-scheduler-v1` and authorize generation of the sealed test
split. Do not change the rule, allocator, feature, checkpoints, cost accounting,
fold assignment, or gates.

The first validation-generation attempt produced no artifact because the exact
matrix teacher hit a numerical pivot limit. ADR-0026 records the generic hybrid
oracle repair, its teacher-only audit, and commit `662c46a`. The unchanged
committed validation configuration was then rerun successfully.

The 16,436,768-byte validation trace has SHA-256
`315637393122ef2c47a7d3fddd3000e62d1e66b5adbf138e2a1ac5e92338eae8`.
It contains 74 unseen board groups, 296 contexts, one DCFR trajectory per
context, and 3,848 checkpoint records. Teacher maximum duality gap and
behavioral NashConv are both `8.6534e-11`; 295 teachers use the packing simplex
and one uses the verified two-phase fallback.

The 17,953-byte selection-free holdout result has SHA-256
`5e32a455a394b98dc8ca54ad6d849263ca0899f78900b01deda4051719a30223`.
It records `candidate_selection_performed: false` and applies only
`active_raw::shallow_12_5` under the frozen production-rule hash.

## Result

Every group fold improves fixed checkpoint-four DCFR:

| Fold | Contexts | Raw uplift | Perfect-uplift capture | Charged rate uplift |
|---:|---:|---:|---:|---:|
| 0 | 64 | 11.671 | 36.72% | 4.34% |
| 1 | 56 | 6.235 | 63.13% | 2.32% |
| 2 | 72 | 6.396 | 43.44% | 2.32% |
| 3 | 52 | 6.868 | 45.92% | 1.82% |
| 4 | 52 | 8.298 | 38.49% | 2.30% |

Aggregate fold-local raw exploitability uplift is `39.468`, capturing 42.484%
of the exact post-probe perfect-information uplift. Charged raw reduction per
millisecond improves by 2.630%. Every fold stays within fixed iterations and
state work. All frozen gates pass.

The whole-validation-pool diagnostic assigns 37 contexts to checkpoint two,
222 to checkpoint four, and 37 to checkpoint six. It improves aggregate final
exploitability by `42.125`, uses 267,744 versus 268,096 state visits, and
improves charged reduction per millisecond by 2.655%. This whole-pool number is
diagnostic; the disjoint fold aggregate is the preregistered verdict.

## Test authorization

At this decision point no test context or artifact exists. ADR-0025's evaluator
must receive this passing validation artifact and verify the identical rule
SHA-256 before it will accept `--split test`. Generate test once, evaluate the
same fixed rule once, and accept or reject under the identical five gates.

## Dissent protocol

**Confidence:** high that the board/range validation transfer is real within
this exact river generator; moderate that the approximately 2.6% timing edge is
stable; low that it transfers to another tree or multiplayer.

**Opposing evidence:** the gain is small, fold 3's rate edge is only 1.82%, and
the pool remains a speculative-job proxy rather than live hand scheduling.

**Largest unknown:** whether the result survives the final untouched test split
without a favorable validation fluctuation.

**Cheapest falsification:** the now-authorized unchanged test evaluation.
