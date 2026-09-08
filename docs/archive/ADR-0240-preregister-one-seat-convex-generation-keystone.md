# ADR-0240: Preregister one-seat convex generation keystone

- Status: accepted preregistration before the frozen convex-keystone run
- Date: 2026-08-22
- Follows: ADR-0239
- Proof: `docs/one-seat-convex-generation.md`
- Proof SHA-256: `adc376afd7077b140ef849998a31b0931aaee87548242ccea4627e587a9b42fc`
- Config: `experiments/configs/one-seat-convex-keystone-v1.json`
- Config SHA-256: `3d2ba1bbba3b7cbedda9bde1afbf164234284d1bd509ec78dbba58ce39c3e5c3`
- Primitive SHA-256: `a84126b66aad760dcda28ba4870cd4a5daba18ebe5377fef8b1efa53a04d9231`
- Implementation SHA-256: `fd77aa6d107bc4a27c40b83cfc51c7fbea93aec22a5f8a6d340a132a02c8c5c1`
- Primitive control SHA-256: `94b03674f67e32773b2dde975ecb5f23611bd9f427f4fef4ce9736fd878698f2`
- Runner control SHA-256: `e9dc30c252d84883ee82c777b10ec632bb8abdc85866f0abd950a27d329dac11`

## Question

With every other seat fixed at an immutable blueprint, can exact one-seat
NashConv minimization under the existing per-seat envelope be solved as a
finite sequence-form epigraph LP by generating opponent best-response rows on
demand? Does the restricted master reproduce an independently enumerated
global optimum while preserving a valid safe-incumbent upper bound, master
lower bound, and `U - L` timeout gap?

This is a finite algebra and optimizer keystone only. It does not ask whether
the resulting small-game policy is stronger, whether cut extraction fits h32,
or whether the method should be deployed.

## Frozen theorem boundary

The accepted proof fixes one acting seat `i`. In sequence-form realization
coordinates, every fixed opponent response payoff is affine in `x_i`.
Opponent deviation gain is the finite maximum of those affine rows, while the
acting seat's gain is affine because its best-response value is invariant to
its current policy. Per-seat cap sublevel sets are convex and the restricted
one-seat NashConv objective is convex. Epigraph variables convert the finite
problem to an LP.

The theorem does not cover multi-seat joint edits. No two-player safety result
is imported into the six-player envelope. The exact evaluator remains the only
emission authority.

## Frozen independent control

Use deterministic `kuhn2` LCFR after exactly 37 iterations and optimize acting
seats 0 and 1 separately. Use raw guard `0.25`, Float64 tolerance `1e-10`, at
most 128 row-generation iterations, and interior retreat factor `0.8`.

Kuhn2 is selected because each seat has exactly 64 pure plans, so the teacher
can enumerate every acting plan and every opponent response. It also contains
a path on which seat 0 checks and later responds, deliberately falsifying the
behavioral-coordinate shortcut while leaving sequence form valid. The h4
continuation control is not globally pure-plan enumerable; describing its own
generated-row solution as an independent enumerated teacher would be circular.
h4 is therefore the next coefficient-extraction differential, not this
keystone's global teacher.

The generated solver and teacher must use different representations:

1. the generated solver uses sequence-form realization variables, exact open-
   axis fixed-response contractions, and all violated opponent epigraph cuts
   per iteration;
2. the teacher uses a complete mixed-normal-form LP whose coefficients come
   from direct exact utility evaluation of all 64 by 64 plan pairs; and
3. both may share the already-verified exact evaluator and two-phase simplex,
   but the teacher may not call the open-axis coefficient primitive.

For each acting seat, independently re-evaluate the emitted safe incumbent and
the retreated policy. Require generated `L`, certified `U`, and the complete
teacher objective to agree within `1e-9`, with final `U - L <= 1e-9`.

## Frozen row and timeout discipline

Seed every target with its exact blueprint best-response tape. Separate every
opponent epigraph at every master solution even when all caps already pass, and
add all violated opponent rows in that iteration. The acting-seat invariant
row is present from the start.

Deduplicate only byte-stable exact response signatures. Do not discard a row
for numerical proximity at the simplex tolerance. Report numerical rank,
effective condition number, and minimum normalized row separation as
diagnostics. A repeated exact signature that remains violated is an
implementation failure, not a row to add twice.

The restricted master objective is a lower bound `L`. The best independently
evaluated cap-feasible policy is an upper bound `U`. Freeze the timeout gap as
`U - L`; the reverse sign is forbidden. A one-iteration mutation arm must
return a cap-feasible independently evaluated incumbent and a correctly
oriented bound even without convergence. Lower bounds must be nondecreasing and
incumbent upper bounds nonincreasing modulo the frozen tolerance.

Rows are reusable only within an exact `(belief, blueprint opponents,
payoff/layout, acting-coordinate)` epoch. This trial does not test cross-epoch
reuse.

## Frozen retreat and shortcut controls

Construct the retreated policy by convexly mixing blueprint and endpoint
realization plans, not by naïvely interpolating behavioral rows. Exact
evaluation must satisfy the per-seat and summed Jensen inequalities within
`1e-9`. This is a geometry control; the independent evaluator remains the
authority.

Mechanically record whether any root-to-terminal path visits one seat twice.
The Kuhn2 trial must report that such a path exists and the behavioral-affine
shortcut must reject it. A separate three-player one-iteration mutation arm
must add both violated opponent rows in one round, proving that separation is
multi-cut rather than first-violation-only.

## Promotion rule

Authorize an h4 open-axis cut-extraction differential only if both acting-seat
trials converge, match their complete teachers, retain valid monotone bounds,
pass realization equivalence and independent evaluation, pass retreat Jensen,
use zero approximate-row removals, and pass every frozen mutation and
provenance gate.

The h4 differential must then measure the new open-axis transposed contraction
directly and compare its rows with independently evaluated fixed-tape
perturbations. Only after h4 identity passes may the corrected ADR-0238 external-
axis machinery be reconsidered as an h32 cut extractor. Cut count, coefficient
latency, master latency, conditioning, exact final-certificate latency, and the
15-second ledger remain open empirical gates.

If the generated solver disagrees with the complete teacher, reverses a bound,
fails the repeated-actor control, or needs approximate cut deletion, reject the
one-seat convex implementation before any h4 or h32 spend.

## Claims boundary

A pass establishes only that the finite one-seat LP, row-generation oracle,
timeout bound, and retreat implementation reproduce an independently
enumerated small-game optimum. It makes no strategy-quality, multiplayer-safe,
population, deployment, composition, cross-street, h4-latency, h32-latency, or
broad poker-strength claim.

## Decision

Commit the proof, primitive, layout gate, complete teacher, runner, config,
controls, this ADR, risk-register update, and generated status from one clean
tree before the first frozen LCFR-37 keystone invocation. Run once and follow
the frozen branch without changing tolerances or selecting rows from the
result.
