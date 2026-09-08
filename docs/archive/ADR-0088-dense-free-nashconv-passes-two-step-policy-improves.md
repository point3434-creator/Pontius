# ADR-0088: Dense-free NashConv passes and two-step policy improves

**Status:** Frozen audit accepted; restartable h32 checkpoint ladder authorized

**Date:** 2026-08-20

## Result

The ADR-0087 audit ran from clean commit
`c1f3d2290f854461e97a29c1e2bac56138d75dde` and completed in 292.957 seconds.
Every frozen correctness, economic, resource, and strategy-direction gate
passed.

The canonical result is
`experiments/results/leaf-adjoint-evaluation-audit-v1.json`. Its SHA-256 is
`1ce5a4256a922c4cee88a5cc41953c159c89e283e7aa831a6aeca75066608747`
and its size is 30,424 bytes.

The main result is strategically meaningful: both h32 step-two average
policies reduce exact reduced-game NashConv from about 14.6 to about 4.17. The
minimum payoff-normalized improvement is `0.348608`, versus the frozen
`0.000001` threshold.

## The best-response evaluator is exact on the dense boundary

Across eight h4/h7 rows—two range families and uniform/checkpoint-16
profiles—the worst errors were:

- utility: `5.47e-15`;
- best-response value: `3.55e-15`;
- unilateral deviation gain: `6.00e-15`;
- NashConv: `7.11e-15`;
- dense value attained by the leaf-selected response: `1.89e-14`; and
- six-seat zero-sum residual: `8.27e-15`.

All 8 rows are more than four orders of magnitude inside the frozen `1e-10`
gates. There were zero raw response-action mismatches and zero exact top-action
ties in the small controls.

The h7 rows matter because no h7 result from the new evaluator existed at
freeze. Uniform NashConv was 14.3599 balanced and 13.6931 blocker-heavy;
checkpoint-16 average NashConv was 1.99332 and 1.99310. Leaf wall time was
about 589-640 ms per complete six-seat evaluation.

This closes the evaluator bridge across utilities, optimal response values,
response policies, and aggregate NashConv—not merely one local action table.

## Wide strategy result

The payoff span is 30 in both h32 geometries.

| Family | Profile | NashConv | Normalized | Change from uniform |
|---|---|---:|---:|---:|
| balanced | uniform | 14.6881 | 0.489604 | — |
| balanced | current step 1 | 2.34985 | 0.078328 | -83.999% |
| balanced | current step 2 | 2.10364 | 0.070121 | -85.678% |
| balanced | average step 2 | 4.16070 | 0.138690 | -71.673% |
| blocker-heavy | uniform | 14.6288 | 0.487627 | — |
| blocker-heavy | current step 1 | 2.39209 | 0.079736 | -83.648% |
| blocker-heavy | current step 2 | 2.26992 | 0.075664 | -84.483% |
| blocker-heavy | average step 2 | 4.17056 | 0.139019 | -71.491% |

Absolute average-policy improvements are 10.5274 and 10.4582. Payoff-normalized
improvements are `0.350914` and `0.348608`. The strategy-direction result is
not marginal or tolerance-sensitive.

The current policies are substantially better than the two-step averages on
this snapshot: average NashConv is `1.98x` current in balanced and `1.84x` in
blocker-heavy. This is expected in part because the step-two average still
contains the initial uniform strategy. It is not permission to use current
policies as the blueprint. Current CFR strategies can oscillate; the checkpoint
ladder must measure both curves.

## Where the remaining unilateral gap lives

For the step-two averages, per-seat deviation gains are:

| Seat | Balanced | Blocker-heavy |
|---:|---:|---:|
| 0 | 1.3385 | 1.4802 |
| 1 | 0.8132 | 0.7906 |
| 2 | 0.5623 | 0.5176 |
| 3 | 0.4750 | 0.4461 |
| 4 | 0.4799 | 0.4079 |
| 5 | 0.4918 | 0.5281 |

Seat zero carries roughly one-third of aggregate average-policy NashConv, with
seat one next. The current-step-two gaps show the same front-loaded shape.
This may reflect acting order, alternating update order, or genuinely harder
early-position decisions. It is a useful scheduler signal, but two checkpoints
are insufficient to distinguish those causes. Do not fit a seat selector yet.

All eight wide profiles conserve utility within `2.20e-14`. Every profile is
finite and returns exactly 1,024 response actions per seat over 6,144
information sets.

## Ties reappear exactly where expected

Both step-one current profiles produced 2,688 exact best-action ties. The
blocker-heavy step-two current produced 12; all uniform and average profiles
and balanced step-two current had none.

The ties arise after sharp current policies make opponent-reach paths exactly
zero. They are not evaluator failures: the best-response value is unchanged by
the tied label. This is direct wide-axis evidence that ADR-0084's decision to
gate response value rather than raw `argmax` identity was necessary. A future
response-policy consumer must retain deterministic, value-preserving tie
semantics.

## Real-policy GPU path remains exact and useful

The h32 step-two average CPU/GPU crosschecks were:

| Family | CPU seat read | GPU seat read | Charged speedup | Utility error | BR error | Gain error |
|---|---:|---:|---:|---:|---:|---:|
| balanced | 27,163.19 ms | 5,830.89 ms | `4.650x` | `1.22e-15` | `3.26e-14` | `3.40e-14` |
| blocker-heavy | 18,570.19 ms | 4,205.78 ms | `4.407x` | `2.51e-14` | `9.99e-15` | `3.51e-14` |

Operator upload is included in the charged denominator. Both response maps had
zero CPU/GPU action mismatches and matching positive minimum gaps.

Complete GPU profile evaluations took 29.1-29.8 seconds balanced and
21.2-21.6 seconds blocker-heavy. The cost barely changes with policy kind
because the automaton ranks and packed feature widths are structural; changing
unary policy weights changes values, not batch geometry. This makes the future
checkpoint bill predictable.

Maximum host numeric peak was 1.497 GB and maximum CuPy pool total was 2.127
GB. Terminal contraction remained above 99.7% of wall time. Best-response
reverse propagation adds only about 44-55 ms across all six seats.

## Independent artifact verification

A post-run verifier independently recomputed:

- every profile's NashConv from its six deviation gains with zero discrepancy;
- every zero-sum residual from its six utilities with zero discrepancy;
- both normalized improvement formulas within `5.55e-17`; and
- the config, implementation, and ADR-0085 source hashes exactly.

This confirms result serialization and arithmetic. It is a diagnostic, not a
retroactive gate.

## Decision

1. Accept leaf-adjoint fixed-policy utility and unilateral best response as an
   exact dense-free evaluator for this reduced game.
2. Accept the ADR-0085 two-step policies as genuine strategy progress over
   uniform, while rejecting any claim that they are converged or strong enough
   for deployment.
3. Measure both current and average policies on the next learning curve; the
   early current advantage is too large to ignore and too shallow to trust.
4. Build restartable solver-state serialization before the longer run.
5. Authorize a continuous h32 DCFR ladder at iterations 1, 2, 4, 8, 16, and
   32 for both range families, with exact current/average NashConv at every
   frozen checkpoint.
6. Defer native GPU fusion until the ladder establishes quality gained per
   accumulated second.

## Why the ladder is now worth its bill

At the measured rates, 32 training sweeps cost about 15.5 minutes balanced and
11.4 minutes blocker-heavy. Evaluating both current and average at six
checkpoints adds about ten minutes. A complete two-family curve should fit
comfortably inside one hour on this workstation.

That is worthwhile because the two-step signal is large, exact, and replicated
across both range families. The curve can now answer questions that were
previously speculation:

- Does current NashConv keep falling or oscillate?
- When does the average overtake current, if ever?
- Does seat-zero headroom shrink at the same rate as later seats?
- Does improvement per second flatten before iteration 32?
- Are balanced and blocker-heavy curves parallel enough to justify one runtime
  scheduler model?

The solver-state artifact must include regrets, strategy sums, iteration,
variant, hand-axis digest, game config, and source-code provenance. An exact
restart test must match uninterrupted h4/h7 trajectories before the h32 run.

## What this does not authorize

- NashConv is unilateral. It does not certify coalition resistance or safety
  against cooperating opponents.
- The evaluated game is still an equal-stack one-bet river abstraction.
- Twenty-one to thirty seconds per evaluation is not an online bot budget.
- The first two CFR sweeps do not answer abstraction quality, cross-board
  generalization, opponent adaptation, or neural leaf accuracy.
- A lower reduced-game NashConv does not automatically imply higher full-NLHE
  EV.

## Dissent protocol

**Confidence:** very high in evaluator correctness; very high that the
two-step average improves over uniform in both frozen geometries; high that a
32-step curve is affordable; moderate that improvement continues smoothly;
low that current-policy superiority survives deeper training.

**Opposing evidence:** current policies are sharp and off-path, thousands of
exact response ties appear at step one, and multiplayer alternating DCFR has no
monotone NashConv guarantee.

**Largest risk:** overfitting architecture to one board and two constructed
range families. The learning curve is justified as a mechanism test, not as a
blueprint-quality claim across poker.

**Cheapest falsification:** exact restart identity followed by the iteration-4
current and average NashConv points. If restart changes the trajectory or both
quality curves reverse sharply, stop before iteration 32 and diagnose rather
than spending the frozen budget automatically.
