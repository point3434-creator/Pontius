# ADR-0098: h32 DCFR continuation passes; average improves as rate flattens

**Status:** Accepted; iteration-64 averages become the blueprint incumbents,
iteration 128 deferred in favor of the h32 acceptance reconnection

**Date:** 2026-08-20

## Result

The frozen ADR-0097 continuation completed from clean commit `42e1819` with
all 22 gates passing. The canonical local artifact is
`experiments/results/leaf-adjoint-checkpoint-extension-v1.json`:

- SHA-256:
  `cf2e2d85bfc8a5dd49f9490b7ddcac2817eaf9d73d9857535a72ac8e964f5ce9`;
- size: 14,672,349 bytes;
- config SHA-256:
  `7d693781f09db532455f94f1f454f9a7509bbaaae8200a5820312d68e5a09f82`;
  and
- implementation SHA-256:
  `891891182e37a3ac6d53a90909503cbfa16c08f587041e17c116dcdecc724003`.

Measured wall time was 1,817.416 seconds, or 30.29 minutes. Both exact
iteration-32 source states restored, both iteration-48 restart boundaries
replayed exactly, and all four new checkpoint states rehash and reconstruct
their current and average policy digests independently.

## Quality curve

All values are NashConv divided by the 30-chip payoff span.

### Balanced factor belief

| Iteration | Current | Average | Average marginal gain/s | Guarded incumbent after rung |
|---:|---:|---:|---:|---|
| 32 | 0.006640 | 0.007913 | 4.8145e-5 from 16 | current 32 |
| 48 | **0.002311** | 0.003115 | 1.0211e-5 | current 48 |
| 64 | 0.004378 | **0.001874** | 2.6552e-6 | average 64 |

### Blocker-heavy factor belief

| Iteration | Current | Average | Average marginal gain/s | Guarded incumbent after rung |
|---:|---:|---:|---:|---|
| 32 | 0.008694 | 0.007902 | 5.8294e-5 from 16 | average 32 |
| 48 | **0.002669** | 0.003244 | 1.3865e-5 | current 48 |
| 64 | 0.007378 | **0.001851** | 4.1413e-6 | average 64 |

The averages remain strictly monotone. From 32 to 64 they improve by factors
of 4.223 and 4.270. Final raw NashConv is `0.056214` balanced and `0.055523`
blocker-heavy. The final normalized values differ by only about 1.24% despite
different factor beliefs.

For context, these values are 62.3% and 55.3% below the independent h7
checkpoint-64 references recorded in ADR-0092. That comparison is useful
evidence that h32 width did not slow normalized convergence in this game, not
a claim that the h7 and h32 strategy spaces have identical difficulty.

## Current-policy oscillation repeats

Current quality improves sharply at 48 and then regresses at 64:

- balanced worsens by 89.5%, from `0.002311` to `0.004378`; and
- blocker-heavy worsens by 176.4%, from `0.002669` to `0.007378`.

The exact incumbent behaves as intended. It accepts current 48 in each family,
rejects average 48 relative to that sharper candidate, rejects the regressed
current 64, and then accepts average 64. Four of eight new policies are
accepted. No new candidate lies inside the `1e-10` guard, so the extension does
not exercise abstention.

This is the second direct training-time demonstration that a fixed-iteration
current strategy is an unsafe product interface even when the underlying
trajectory is improving. Iteration count alone is not a quality certificate.

The sharp-policy geometry persists:

- current 64 is pure at 93.4% and 93.8% of information sets and has 96 and 166
  exact action ties;
- average 64 is pure at zero of 6,144 information sets and has no exact ties;
  and
- the averages retain 2,263 and 2,269 distinct action distributions, with mean
  entropy `0.0616` and `0.0528`.

The average remains the stable blueprint/representation customer. Current 48
is retained as a realistic sharp-policy and search-candidate diagnostic, not
as the final blueprint.

## Marginal-efficiency verdict

Relative convergence remains impressive, but absolute quality gained per
second now clearly flattens:

| Family | 16-32 gain/s | 32-48 gain/s | 48-64 gain/s |
|---|---:|---:|---:|
| Balanced | 4.8145e-5 | 1.0211e-5 | 2.6552e-6 |
| Blocker-heavy | 5.8294e-5 | 1.3865e-5 | 4.1413e-6 |

The 32-48 rate retains only 21.2% and 23.8% of the prior interval's rate. The
48-64 rate then retains only 26.0% and 29.9% of that. This is the saturation
signal ADR-0092 did not yet contain.

Even the impossible best case in which iterations 65-128 remove all remaining
NashConv caps their average gain at roughly `1.0e-6` and `1.4e-6` per training
second under the measured step bills, before evaluation cost. Iteration 128
may still produce a useful offline teacher, but it is no longer the cheapest
experiment for learning how to spend online decision milliseconds.

This metric concerns laboratory compute allocation. Offline blueprint training
time is not itself online decision latency, and a future full-game blueprint
may justify much larger offline budgets. Here the relevant choice is what one
developer should measure next in the reduced laboratory.

## Per-seat result

Final average deviation gains are:

- balanced: `[0.009408, 0.013789, 0.008677, 0.007807, 0.007940,
  0.008591]`; and
- blocker-heavy: `[0.006707, 0.010415, 0.011219, 0.011525, 0.007931,
  0.007725]`.

Largest-to-smallest ratios are 1.766 and 1.718. Residual error is somewhat
less uniform than at iteration 32, but it does not restore the earlier
seat-zero pattern: the largest residual moves to seat one balanced and seat
three blocker-heavy. There is still no evidence for a fixed seat selector.

These are unilateral deviation gains. No coalition guarantee follows.

## Correctness and resource result

All structural and numerical gates pass:

- exact source, serialized checkpoint, and restart-state identities;
- 6,144 information sets and 12,288 hand-action entries per family;
- exactly 435 terminal batches on every balanced step and 311 on every
  blocker-heavy step;
- maximum zero-sum residual `1.03e-14`;
- maximum training step 30.353 seconds;
- maximum live six-seat evaluation 29.836 seconds;
- maximum host numeric estimate 1.497 GB;
- maximum CuPy pool 2.127 GB; and
- no nonfinite accumulator or quality value.

Independent post-run reconstruction validates all four state digests plus all
eight current/average policy digests.

Balanced continuation training costs 937.402 seconds and its four live
profiles cost 117.159 seconds. Blocker-heavy costs 672.294 and 85.045 seconds.
Terminal contraction consumes 99.72-99.84% of every measured step. The phase
diagnosis from ADR-0092 and ADR-0096 therefore remains unchanged.

## Decision

1. Adopt both iteration-64 average policies as the strongest blueprint
   artifacts in this reduced h32 game.
2. Retain both iteration-48 current policies as sharp, realistic diagnostic
   candidates; do not replace the averages with them.
3. Defer, but do not permanently reject, the 65-128 continuation. The final
   interval's absolute quality-per-second collapse satisfies ADR-0097's branch
   for changing experiments.
4. Reconnect the dense-free stack to strategy improvement now: run an
   ADR-0054-style h32 warm-search and guarded-acceptance experiment using the
   real 32/48/64 checkpoints as declared blueprints/candidates.
5. Compare blind deployment, aggregate improvement, and all-six-seat
   unilateral non-worsening. Keep coalition stress offline; a six-player
   coalition enumerator is not an online target.
6. Charge candidate generation, signed clean-fringe reads, recompose-and-read,
   and the flat incumbent under the same compile/marginal/break-even bill.
7. Return to iteration 128 if acceptance/search results show that blueprint
   residual dominates decision quality, or retain it as an overnight teacher
   after the strategic architecture is connected.
8. Keep the resident terminal pipeline as the subsequent systems target. Its
   justification is now a stable quality curve plus repeated 99.8% terminal
   localization, not an assumed kernel speedup.

The central question is no longer whether the wide engine can train. It can.
The next unknown is whether a limited online search, protected by the exact
dense-free evaluator, improves a strong real blueprint often and cheaply
enough to raise strategy quality per decision millisecond.

## What this establishes—and what it does not

Within the declared reduced game, exact dense-free h32 DCFR trains a stable
average policy to normalized NashConv near `0.00186`, survives two serialized
restart boundaries, and supports a guarded best-so-far policy stream. This is
substantive strategy evidence, not only evaluator infrastructure.

It is still one board, one action size, equal stacks, two generated beliefs,
and 32 selected hands per seat. It does not establish full 1,326-combo private
ranges, multi-street play, arbitrary stack depth, coalition safety, equilibrium
convergence in a six-player game, or real-opponent win rate.

## Dissent protocol

**Confidence:** very high in the measured curve and incumbent behavior; high
that the strategic acceptance experiment now has more information value than
an immediate 128 run; moderate that the h32 acceptance economics will be
favorable.

**Opposing evidence:** a stronger offline blueprint can reduce the amount of
online search required, and 64 additional iterations are inexpensive in
absolute hardware terms. If the goal were only to minimize this toy game's
NashConv, continuing would be reasonable. The project goal is broader:
discovering the highest decision quality per millisecond for six-player
hold'em.

**Largest risk:** the acceptance experiment may merely rediscover that this
already-low-residual one-bet game leaves too little headroom for local search.
That negative result would still be more architecture-relevant than another
point on a now-flattening training curve.

**Cheapest falsification:** freeze a small h32 acceptance matrix over the two
families and real checkpoint deltas. If guarded search never improves the
iteration-64 averages or its exact read bill overwhelms its gain, resume the
128 teacher before widening the game.
