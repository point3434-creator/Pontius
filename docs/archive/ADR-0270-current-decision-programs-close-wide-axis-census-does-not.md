# ADR-0270: Current-decision programs close; wide-axis census does not

- Status: accepted retrospective censored result; current-decision combined-ledger replay authorized
- Date: 2026-08-22
- Implements: ADR-0269
- Clean preregistration commit: `23e9fae8c34d4e81249806c39726fe6ae915b1c0`
- Result: `experiments/results/h32-retained-convex-closure-census-v2.json`
- Result SHA-256: `e0ad1af41061fce837ac689fcc0507c105346c2a3b8b08756e86285c17a0f3e3`
- Final checkpoint: `experiments/results/h32-retained-convex-closure-census-v2.partial.json`
- Final checkpoint SHA-256: `0b193021d3c0279bcf3be40c705ea38aa4142589a5d803a3a6e2cde0d1810be0`

## Process result

The target-isolated invocation passes all 17 provenance, base-config,
inventory, ordered-attempt, checkpoint, known-error, target-validity,
keystone, label-disclosure, memory, emission, finite, and null-claim gates. It
attempts all 42 targets in the frozen order and atomically checkpoints every
outcome. The recorded checkpoint hash matches the final partial artifact.

Forty-one targets complete normally. Target 6 reproduces the exact known
`ArithmeticError: behavioral master primal/dual verification failed`, is
marked censored, releases its GPU state, and does not stop target 7. No other
target error occurs. The run completes in `533.492 s` and emits no candidate.

The ADR-0247 keystone reproduces both new cut players `(4, 5)`, its one-round
count, and all compared initial/final bounds and oracle quantities within
`5.90e-16`.

## Full retained distribution

Thirty-five of 42 programs reach verified facet, exact-cap, and `U - L`
closure. Their cut-round distribution is:

| Rounds | Targets |
|---:|---:|
| 0 | 7 |
| 1 | 11 |
| 2 | 10 |
| 3 | 7 |

Six additional targets stop in the preregistered no-new-facet branch without
cap-and-bound closure, and one is censored by the known master KKT failure.
No completed target reaches a round or time cap; the maximum verified closure
depth is three rounds. The run performs 63 multi-cut rounds, adds 92 exact
opponent-response rows, and opens 104 explicitly retrospective all-seat oracle
labels on completed targets.

Universal one-round closure is decisively false: only 18 of 42 close in zero or
one round, while 17 verified programs need two or three. The existing ray and
direction machinery therefore remains a live fallback for the broad retained
scope. Full one-seat convex generation is an effective off-clock exact teacher,
not yet a universal within-contract global optimizer.

These counts are fixed-panel descriptions, not IID rates.

## The current-decision subgroup is qualitatively different

All six post-call contexts—where the optimized seat is the player actually on
the clock—reach verified global one-seat closure. Four need no new facet and
two need one multi-cut round. Their complete census invocations take
`6.067–9.154 s`, including cold reconstruction, and none stalls or errors.

The 36 wide last-responder programs account for every two/three-round closure,
all six stalls, and the one KKT failure. This identifies scope width as an
important part of the operational story: the theorem applies to both shapes,
but the deployment-aligned one-node programs are much easier to separate on
this retained corpus.

This is strong retrospective evidence, not fresh confirmation. The v2 timing
does not include the independent half-retreat certificate and emission reserve
required by the live strategy contract. Do not claim that a globally closed
endpoint plus the emitted safe retreat already fits 15 seconds from this row
alone.

## Facet closure is not cap-and-bound closure

Every one of the six normal stalls has no genuinely new response signature at
its final candidate, but that exact candidate violates at least one cap beyond
the `2e-11` certificate allowance. Maximum exact cap violations range from
`1.24e-10` to `2.48e-9`; retained master primal residuals remain within the
looser `1e-8` verification ceiling. Because the only exact feasible incumbent
remains materially above the restricted lower bound, final gaps range from
`0.00606` to `0.01789`.

This is not evidence that another facet is missing. It is a numerical contract
mismatch at an optimum that sits on a cap boundary: an LP-feasible point under
the master's verified residual can still be infeasible under the much tighter
exact certificate. Record this defect family as R39.

Do not fix it by weakening exact cap feasibility or relabeling no-new-row as
closure. Candidate-side high-accuracy primal refinement, scaling, or a second
master used only to construct an independently exact-feasible upper-bound
incumbent may be investigated later. The original restricted-master lower
bound and exact certificate remain authoritative. Convex interior retreat is a
safe emission mechanism, but by itself it does not prove a `1e-8` global gap.

## Decision

Accept the target-isolated retrospective census and its censored branch. Retain
the live ray/direction fallback across the broad scope. Do not formally
supersede the direction-diversity ADR line.

Authorize one read-only current-decision combined-ledger replay before opening
post-fold labels. Join the six ADR-0270 endpoint-closure paths with their exact
ADR-0264 half-retreat certificate costs and frozen 50-ms envelope and 1,000-ms
emission reserves. Preserve per-target pairing and use the unchanged
`13,967.616 ms` conservative floor plus only the genuinely incremental
post-cut endpoint-oracle charge. If every measured and conservative combined
path fits 15 seconds, separately preregister the six sealed post-fold targets
as the fresh current-decision closure-and-value confirmation. Otherwise retain
the current safe retreat without a live global-optimality claim.

Do not use the current six-of-six result to tune the post-fold factor, guard,
cap allowance, residual tolerance, cut budget, order, or materiality floor.

## Claims boundary

No candidate was emitted and the warm DCFR step remains in the measured path
despite not feeding the convex master. The post-fold panel receives zero
strategy labels. This result makes no deployment-rate, direction-obsolescence,
multi-seat, composition, cross-street, chip-EV, AIVAT, full-width,
exploitation, or broad poker-strength claim. It specifically rejects the
statement that the current bot is already provably maximal on every decision.
