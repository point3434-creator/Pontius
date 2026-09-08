# ADR-0228: Continuation rooting delivers exact safe value on all twelve targets

- Status: accepted fresh research result
- Date: 2026-08-22
- Implements: ADR-0227
- Clean preregistration commit: `9109058`
- Result: `experiments/results/h32-continuation-root-strategy-trial-v1.json`
- Result SHA-256: `59b866ef05441754329539d60a8385c747c928b115929fe58d458285fa6ccdfc`

## Formal result

Every provenance, parent, source, target, blueprint, warm-start, complete
block-manifest, convex-scope, six-row charge, affine-intercept, hard-clock,
feature-label-barrier, independent-teacher, winner-selection, deadline-fallback,
memory, finite, immutable-emission, and numerical-identity gate passes. The
clean invocation completed in `231.362 s` from commit `9109058`.

All 12 targets priced all 31 continuation blocks before any exact strategy
label existed. The frozen matrix contains 372 candidates. Of these, 356 have a
positive complete affine envelope, 15 stop as objective-nonimproving, and one
stops at the objective allowance. Every target therefore has at least one
positive affine winner.

The label barrier is exact: all 12 matrices and winners were frozen while the
372 candidate labels and all teacher rows were null. The teacher then queried
exactly one frozen winner per target. It made no second query and performed no
adaptive scale search.

## Every frozen winner verifies

All 12 independent incremental certificates complete, pass the fixed
per-seat blueprint-gain envelope, finish before the emission cutoff, and are
accepted by the shadow rule. Eleven winners use scale `0.5`; one uses scale
`0.25`.

The pooled affine prediction is `0.07695540387238467` NashConv reduction. The
pooled independent exact result is `0.07695540387238250`, a difference of
about `2.2e-15`. Maximum error over predicted and exact utilities,
best-response values, and deviation gains is `1.07e-14`, below the frozen
`2e-11` ceiling. Maximum affine-intercept error is zero.

Exact per-target reductions range from `0.001140914853` to `0.02163989738`,
with median `0.003155601691`. Relative to each target's restricted-blueprint
NashConv, the reduction ranges from `2.14%` to `9.91%`, with median `5.84%`.
These are local continuation-subgame quantities under the frozen conditioned
beliefs, not whole-game or population win rates.

The exact cap condition has comfortable numerical separation. Across all 72
winner-seat gain comparisons, the largest candidate excess over
`blueprint gain + 3e-9 guard` is `-2.99999933e-9`; no winner consumes the guard.
The improvement comes from reducing one or more deviation gains without
raising any seat above its blueprint ceiling.

## The live-like ledger closes

Independent winner certificates cost `60.109 ms` to `382.963 ms`. Simulated
live completion, including warm step, all 31 affine candidates, and the one
exact winner proof, ranges from `4.674 s` to `9.564 s`. Adding the frozen
one-second emission reserve produces complete hard ledgers from `5.674 s` to
`10.564 s`, leaving at least `4.436 s` before the 15-second boundary.

No candidate-start guard fires. All 12 targets remain library-limited rather
than deadline-limited. GPU-pool allocation peaks at `8,174,427,136` bytes and
physical-free memory never falls below `7,185,891,328` bytes.

Winning schedule indices are 1, 3, 4, 7, or 19, and every acting seat wins at
least once. This is descriptive only. The experiment was designed to price all
31 blocks, so it does not authorize a smaller structural schedule or a
position-only selector.

## Decision

Accept the fresh result. The solver spine now has one causally correct positive
end-to-end vertebra: exact post-action belief, exact continuation topology,
one resident warm step, complete legal block library, full six-seat affine
proof, one independent exact certificate, hard deadline, and immutable
fallback. Within these 12 frozen contexts, the one-step regret-vertex path
delivers exact safe local value on every target.

Do not populate a deployment strategy from this artifact. The same source
boards and posterior family have now been opened, the game remains an exact
six-player one-bet river abstraction, and only one direction family was tested.

The next compute question is whether the remaining minimum `4.436 s` of hard
ledger headroom should buy a second continuation warm step. Measure that first
as a label-free retained-context differential: one versus two warm steps,
followed by the same 31-row pricing bill, with no new exact winner query. If the
two-step worst-case hard ledger remains below 15 seconds on every target,
preregister a fresh held-out posterior panel comparing one-step and two-step
delivered exact value. If it does not fit, retain the proven one-step path and
spend the headroom elsewhere.

This result establishes exact local safe improvement only for the frozen
continuation contexts. It makes no deployment, continual-resolving,
composition, population, whole-game, or broad poker-strength claim.
