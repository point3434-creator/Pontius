# ADR-0028: Frozen river scheduler passes the sealed test

**Status:** Accepted as an exact-river research control

**Date:** 2026-08-19

## Decision

Accept `river-post-probe-scheduler-v1` as the adaptive-compute control for the
current exact heads-up sequential-river game. It may replace fixed
checkpoint-four DCFR in experiments that use the identical game, feature,
pooling, timing, and budget semantics. Do not retune it on the reserved data.

This result establishes unseen board/range transfer inside the exact river
generator. It does not establish transfer to a wider action tree, earlier
streets, asynchronous live scheduling, neural leaves, or multiplayer poker.
Fixed checkpoint-four DCFR remains the fallback outside the tested envelope.

## Sealed chronology and provenance

Commit `68eecc8` froze the selection-free evaluator, the rule-hash guard, exact
feature-cost timing, and both reserved configurations before a reserved result
existed. The first validation-generation attempt stopped before writing an
artifact when one exact matrix teacher exceeded the packing-simplex pivot
limit. Commit `662c46a` added a verified two-phase fallback and passed a
teacher-only audit. The unchanged validation then passed, and commit `c38fa4b`
recorded that verdict before the test trace was constructed.

The frozen rule SHA-256 remained
`74d6c3d68dbb7363af9927b72f83dce7769613656df8253ace36a1ff0cc598bd`.
The 15,529,828-byte test trace has SHA-256
`a0e51f653987a1fa6f532ae9e56ea5013823e9a961fd6c0525392a775b53ac2e`.
It contains 70 untouched board groups, 280 four-family joint-range contexts,
280 DCFR trajectories, and 3,640 checkpoint records. All 280 exact teachers use
the packing backend; maximum duality gap and behavioral NashConv are both
`9.429e-12`, and the maximum pivot count is 112.

The 18,166-byte selection-free test verdict has SHA-256
`47fea9294ff28f37a0dc2e41706267d3fb25f379a01943c575448f36a0221c89`.
It records `candidate_selection_performed: false`, validates the passing
validation artifact and frozen rule hash, and reports `status: test_passed`.

## Test result

The primary verdict applies the fixed rule independently within five disjoint
board-group folds:

| Fold | Contexts | Raw uplift | Perfect-uplift capture | Charged rate uplift | State visits, adaptive/fixed |
|---:|---:|---:|---:|---:|---:|
| 0 | 48 | 3.696 | 19.34% | 1.54% | 44,192 / 44,416 |
| 1 | 52 | 5.029 | 24.84% | 1.96% | 47,648 / 47,712 |
| 2 | 44 | 4.601 | 30.46% | 1.82% | 39,392 / 39,392 |
| 3 | 60 | 6.770 | 46.01% | 2.35% | 53,024 / 53,088 |
| 4 | 76 | 17.627 | 46.23% | 3.88% | 68,156 / 68,512 |

Every fold strictly improves raw final exploitability and charged reduction per
millisecond. Aggregate fold-local final exploitability is 263.548 versus
301.273 fixed, a 12.522% decrease. Raw uplift is `37.724`, capturing 35.156%
of the exact post-probe perfect-information uplift. Charged reduction per
millisecond is `1.49319` versus `1.45678`, a 2.499% improvement.

The adaptive folds use 1,118 versus 1,120 iterations and 252,412 versus 253,120
deterministic state visits. Their charged time is 1,080.888 ms versus 1,082.006
ms, including 2.453 ms for the one-pass regret feature and 0.403 ms for ranking
and allocation. All five preregistered gates pass.

The whole-test-pool diagnostic assigns 35 contexts to checkpoint two, 210 to
checkpoint four, and 35 to checkpoint six. It improves final exploitability by
`37.863` at exactly the fixed iteration budget, but the disjoint fold aggregate
above remains the preregistered verdict.

## Interpretation

The important positive result is not that regret is a universally strong
scheduler feature. It is that a tiny, fully charged, tree-local statistic
supports a conservative compute exchange that survives development,
validation, and a final untouched test. The gain is only about 2.5% in the
primary quality-per-millisecond metric, so a neural scheduler is not yet an
efficient next investment. The transparent rule is now a control that richer
trees and future schedulers must beat.

The next experiment should attack a different bottleneck: measure exact
strategy reuse, warm-start, and recertification under paired blocker-sensitive
range perturbations. After that control is secure, expand the river action tree
and then player count. Approximate range similarity must never authorize a
strategy-cache hit by itself.

## Dissent protocol

**Confidence:** high that the frozen rule transfers across this generator's
reserved boards and joint ranges; moderate that the small timing advantage is
stable on the same implementation; low that the effect size survives a wider
tree or six-player beliefs.

**Opposing evidence:** two test folds capture less than 25% of their local
perfect uplift, the aggregate rate gain is only 2.499%, and the pool represents
shared or speculative jobs rather than live latency-constrained decisions.

**Largest unknown:** whether blocker-sensitive range shifts and added bet sizes
destroy the regret ranking or make recertification cost dominate the saved
search work.

**Cheapest falsification:** use the frozen scheduler unchanged as a control on
paired near-range sequential-river instances with a wider action set; report
both root strategy error and fully charged recertification cost.
