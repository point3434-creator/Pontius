# ADR-0097: Preregister staged h32 DCFR continuation through 64

**Status:** Frozen before any iteration-48 or iteration-64 policy, quality, or
timing result

**Date:** 2026-08-20

## Decision

Restore both exact ADR-0092 iteration-32 DCFR states and continue them through
iteration 64 with the ADR-0096-selected batch width 384. Measure literal
current and average policies at iterations 48 and 64, cross a serialized
restart at 48, and retain both iteration-64 accumulator states.

The frozen config is
`experiments/configs/leaf-adjoint-checkpoint-extension-v1.json`, SHA-256
`7d693781f09db532455f94f1f454f9a7509bbaaae8200a5820312d68e5a09f82`.
The runner is
`src/pontius/leaf_adjoint_checkpoint_extension_audit.py`, SHA-256
`891891182e37a3ac6d53a90909503cbfa16c08f587041e17c116dcdecc724003`.
The result target is
`experiments/results/leaf-adjoint-checkpoint-extension-v1.json`.

The immutable strategy source is
`experiments/results/leaf-adjoint-checkpoint-ladder-v2.json`, SHA-256
`242de5f0a42693248f98cc8f127f4fc892606df58e94d28c107d542b1276736b`.
The width decision is pinned to
`experiments/results/leaf-adjoint-batch-width-audit-v2.json`, SHA-256
`5e34cb54f0be353320d1190ca0cce504fce327693f9d3de47d29a33350d471c5`.

## Why stage at 64

ADR-0092 shows material improvement through iteration 32, but continuing both
families directly to 128 would cost roughly another 75-85 minutes before live
quality evaluations. Iterations 33-64 plus two intermediate/final evaluation
rungs should cost about 30-35 minutes and answer the decision-relevant
questions first:

1. Does the average remain monotone at the new 48 rung and at 64?
2. Does current continue to oscillate?
3. Does either policy beat the exact iteration-32 incumbent after a numerical
   guard?
4. Does h32 average quality approach the independent h7 checkpoint-64
   references near `0.0041-0.0050` normalized NashConv?
5. Does absolute normalized improvement per second remain large enough to pay
   for 65-128 before native work?

Iteration 128 is a successor decision made from the frozen 64 result. This is
not an early stopping rule inside the present run; both families always reach
64 if the correctness and resource path remains executable.

## Frozen workload

- six players, 32 constructed hands per seat;
- board `2c 7d 9h Js Qc`;
- 12-chip pot, 30-chip equal stacks, and one 3-chip bet;
- balanced and blocker-heavy factor beliefs;
- DCFR, exact iteration-32 regret and strategy-sum restoration;
- checkpoints 48 and 64;
- current then average evaluation at each checkpoint;
- batch width 384, query chunk 256, and the unchanged CuPy sparse terminal
  engine; and
- exact JSON restart and state-digest replay at iteration 48.

The runner records every step's wall time, terminal fraction, sparse-batch
count, host estimate, and CuPy-pool peak. Each checkpoint retains current and
average policy digests/statistics, all six exact dense-free evaluation rows,
and the complete restart state.

The source checkpoint is rehashed, its policy digests are checked against its
state, and a pristine solver must reproduce the exact source state digest
immediately after restoration. The iteration-48 JSON state must likewise
round-trip and reproduce its exact digest before training continues.

## Best-so-far incumbent semantics

For each family, replay the ordered candidate stream:

1. iterations `1, 2, 4, 8, 16, 32` from ADR-0092;
2. iterations `48, 64` from this audit; and
3. within each iteration, current before average.

Initialize from the first candidate. For every later candidate, let
`improvement = incumbent normalized NashConv - candidate normalized NashConv`
and use a frozen normalized guard of `1e-10`:

- accept only when improvement is strictly greater than the guard;
- reject when improvement is strictly less than the negative guard; and
- abstain inside the closed guard interval.

Every trace row records the prior value, candidate improvement, decision, and
resulting incumbent digest. The source-only prefix must replay to within the
same `1e-10` guard of the literal minimum, accepted incumbents may never
worsen, and all three branches must follow the frozen inequalities.

This is a conservative Float64 training selector, not the bounded clean-fringe
certificate intended for online acceptance. The guard is many orders above
the measured `1e-14` evaluator discrepancies but does not constitute a formal
all-seat error interval. The result must call it guarded, not certified.

## Frozen gates

The audit passes only if:

- two family rows, two new checkpoints, four new quality profiles, 12 source
  candidates, and four new candidates per family are present;
- both final states are at iteration 64;
- each family retains 6,144 information sets and 12,288 hand-action entries;
- every balanced step has 435 terminal batches and every blocker-heavy step
  has 311;
- source restore, checkpoint serialization, and iteration-48 restart identities
  all pass;
- incumbent non-worsening, branch semantics, and source-prefix replay pass;
- maximum step and live quality walls are at most 60 seconds each;
- host numeric and CuPy-pool peaks stay at or below 3 GB and 4 GB;
- all states and quality rows are finite;
- maximum six-seat zero-sum residual is at most `1e-9`; and
- the complete audit finishes within 2,700 seconds.

There is deliberately no minimum improvement, maximum NashConv, monotonic
average, accepted-candidate count, h7-comparison, or quality-per-second gate.
Those are the unknown scientific outcomes. A flat, oscillating, or worse
continuation can pass if it is measured correctly and the incumbent refuses
it.

## Validation before freeze

All 465 repository tests pass, with 21 optional-dependency skips in the base
test environment. Four new tests pin:

- the 32-to-48-to-64 schedule and width 384;
- the outcome-neutral gate set;
- all source, hardware, schedule, guard, and resource fields against mutation;
  and
- initialize, accept, reject, abstain, non-worsening, invalid-candidate, and
  invalid-guard behavior.

The new runner reuses the already validated case builder, exact checkpoint
serializer, DCFR solver, CuPy operator, and dense-free six-seat evaluator. No
numeric primitive changes in this audit.

## Interpretation branches

1. **Average improves materially through 64:** authorize the 65-128 extension
   before native work, unless marginal normalized gain per second has already
   collapsed.
2. **Average improves but absolute gain per second collapses:** compare the
   projected 128 gain against the scoped resident-kernel experiment; do not use
   relative convergence alone.
3. **Current improves while average stalls:** retain the guarded incumbent and
   densify the checkpoint ladder before treating a sharp current policy as a
   production customer.
4. **Neither improves:** stop the ladder at the best exact incumbent and move
   to the h32 acceptance/re-solving experiment; more blueprint iteration is no
   longer the best quality-per-millisecond investment.
5. **Correctness or resource gate fails:** reject the run; do not interpret
   quality values downstream of the failure.

## Limitations

The result will remain one river board, one bet size, equal stacks, a generated
32-hand axis, two belief families, and unilateral reduced-game NashConv. It
does not establish coalition robustness, full-game exploitability, or strength
against real six-max opponents. Multiplayer DCFR also lacks the two-player
zero-sum convergence guarantee; a descending measured NashConv curve is
evidence for this game, not a theorem for NLHE.

## Dissent protocol

**Confidence:** very high in the source/restart semantics and outcome-neutral
design; high that 64 is the right staged purchase; moderate that the two
families will remain parallel.

**Opposing evidence:** the final ADR-0092 relative residual shrank unusually
fast, so iteration 64 may be valuable enough that staging looks conservative.
Conversely, absolute gain per second was already falling, so relative
acceleration may overstate its economic value.

**Largest risk:** one board and two related generated beliefs can make a clean
shared curve look universal. No selector or production stopping model may be
fit from this audit alone.

**Cheapest falsification:** the frozen continuation itself. Iteration 48 gives
an intermediate point at no extra training cost and only four additional live
profile evaluations across both families.
