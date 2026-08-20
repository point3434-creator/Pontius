# ADR-0089: Preregister restartable h32 DCFR checkpoint ladder

**Status:** Accepted after h4 restart development and h32 iteration-two
quality, but before any h7 restart or h32 iteration above two

**Date:** 2026-08-20

## Decision

Run one frozen continuous DCFR learning curve on both h32 range families. The
frozen configuration is
`experiments/configs/leaf-adjoint-checkpoint-ladder-v1.json`; its SHA-256 is
`74bb6f5a29e7d0b5043c9f39d787b50258242dfd503d1efa089fd4a6bc915747`.
The result target is
`experiments/results/leaf-adjoint-checkpoint-ladder-v1.json`.

Train cold-start DCFR continuously to iteration 32, saving restartable states
at iterations 1, 2, 4, 8, 16, and 32. Measure exact current and average
NashConv at every checkpoint. Cross a real JSON serialization/restore boundary
at iteration 16 and continue the production trajectory from the restored
solver.

This experiment is authorized by ADR-0088's large replicated two-step quality
gain. It is still a one-board reduced-game mechanism test, not blueprint
training for full hold'em.

## Restartable state contract

The ADR-0085 artifact stored policies but not the accumulators required to
resume the same DCFR trajectory. Its policy can warm start another solver, but
that is not continuation.

The additive checkpoint format stores:

- solver variant and iteration;
- the exact warm-start flag;
- player and public-node counts;
- SHA-256 of the complete public topology;
- SHA-256 of the ordered private-hand axes;
- SHA-256 of the information/action schema;
- every Float64 regret accumulator;
- every Float64 average-strategy accumulator;
- current and average-policy digests;
- caller-supplied game context and code/config provenance; and
- a canonical digest over the entire payload.

JSON serialization uses sorted keys, compact separators, and rejects NaN or
infinity. Python's shortest round-tripping Float64 representation preserves
the literal binary values. Restore requires a pristine solver, exact variant,
topology, axes, schema, and payload digest. It validates finite regrets,
finite nonnegative strategy sums, then recomputes current and average-policy
digests after loading.

The format is deliberately verbose and transparent for this laboratory. A
future production checkpoint may use a binary array container, but it must
retain these semantic digests and exact restart tests.

## Small restart gate before wide execution

For h4 and h7 in both range families, compare:

1. an uninterrupted cold solver run to iteration four; and
2. a cold solver run to iteration two, canonical JSON export/import into a
   fresh solver, then continuation to iteration four.

Require bit-identical regret tables, strategy-sum tables, current policies,
average policies, and final state digests. The maximum accumulator error gate
is exactly zero, not `1e-10`.

This produces four rows. If any row fails, stop before constructing an h32
solver. The checkpoint ladder cannot be interpreted if restart changes the
algorithm it measures.

## Frozen wide schedule

For balanced and blocker-heavy h32 factor beliefs, run one cold alternating
DCFR trajectory through iterations 1-32. Save full checkpoint state at:

`1, 2, 4, 8, 16, 32`.

At each checkpoint record:

- current and average policy digests and statistics;
- cumulative training wall time;
- exact current and average utilities, unilateral response values, deviation
  gains, NashConv, and zero-sum residual;
- normalized improvement from uniform;
- improvement per cumulative training second; and
- marginal average-policy improvement per incremental training second.

Iterations 1 and 2 already have frozen quality results in ADR-0087. To avoid
spending about 100 seconds recomputing them, reuse those rows only if the live
current and average policy digests exactly match the immutable ADR-0085 source.
Any digest difference rejects source reuse. Iterations 4, 8, 16, and 32 are
evaluated live through the frozen GPU best-response engine for both current and
average policies.

The full live bill is therefore 64 training steps plus 16 complete six-seat
quality evaluations, not 24. Reuse is identity-based, not range similarity or
an estimated cache hit.

## Iteration-16 restart

After training and evaluating iteration 16:

1. serialize the complete state to canonical JSON;
2. restore it into a new h32 solver bound to the same workspace, automata, and
   resident GPU operators;
3. re-export immediately and require identical state digest; and
4. discard the original solver and run iterations 17-32 from the restored
   instance.

The small controls establish continuation identity against an uninterrupted
oracle. The wide arm validates the complete h32 state and then actually uses
the restored path. It does not duplicate the final 16 wide iterations in a
second uninterrupted solver; that would double an already measured bill
without adding a new serialization mechanism.

## Quality gates and non-gates

Require final average normalized NashConv to improve over the frozen
iteration-two average by at least `1e-4` in both families. This tests whether
the additional 30 iterations buy measurable aggregate quality.

Do not require monotonic current or average NashConv at every checkpoint.
Alternating multiplayer DCFR has no such guarantee, and the shape of those
oscillations is one of the experiment's outputs. Report:

- best current checkpoint;
- best average checkpoint;
- every per-seat deviation vector;
- every marginal improvement slope; and
- any interval with negative quality gained per second.

The curve should determine the most efficient measured checkpoint, not a
post-hoc gate selected from its minimum.

At the final average, crosscheck seat zero through CPU SciPy against the GPU
result in each family. Require utility, best-response value, and deviation-gain
errors at most `1e-9`, plus at least `3x` charged GPU speedup on both families
and the blocker-heavy validation family.

## Economic and resource gates

Require:

- every training step at most 60 seconds;
- every live six-seat quality evaluation at most 60 seconds;
- conservative host numeric peak at most 3 GB;
- CuPy pool total at most 4 GB;
- quality zero-sum residual at most `1e-9`;
- exactly 6,144 information sets and 12,288 hand-action entries;
- finite accumulator states and quality outputs; and
- total pre-serialization audit wall time at most one hour.

The one-hour ceiling is a failure boundary, not a target. ADR-0088 predicts
roughly 27 minutes of training and ten minutes of live evaluation across both
families, plus small controls and final CPU checks.

## Pre-freeze engineering disclosure

The checkpoint serializer has only h4 development evidence.

One warm-start h4 DCFR trajectory was split after iteration one, round-tripped
through JSON, and continued to iteration three. Regrets, strategy sums, current
policy, and average policy were bit-identical to uninterrupted execution.

One cold balanced-h4 control was split at iteration two and continued to
iteration four. It returned:

- maximum regret error `0.0`;
- maximum strategy-sum error `0.0`;
- exact current and average-policy identity;
- identical final state digest; and
- 338,634 compact JSON bytes at the split checkpoint.

Digest mutation, solver-variant mismatch, non-pristine restore, NaN metadata,
and non-JSON provenance are rejected in targeted tests. Four serializer tests
and two strict config tests with ten mutation subtests pass.

No h7 restart result has been observed. No h32 iteration 3, 4, 8, 16, or 32
policy, accumulator, state size, latency, utility, response, NashConv, quality
slope, or restart result has been observed.

Frozen prior evidence is allowed and hash-pinned:

- ADR-0085 policy source SHA-256
  `58455716893afcff2cc19eb5000f0bb74b90fa6b49564f08762b9c9db2b023ee`;
- ADR-0087 quality source SHA-256
  `1ce5a4256a922c4cee88a5cc41953c159c89e283e7aa831a6aeca75066608747`;
- iteration-two average normalized NashConv 0.138690 balanced and 0.139019
  blocker-heavy; and
- iteration-two current normalized NashConv 0.070121 and 0.075664.

Those source points motivate the ladder but do not reveal its later curve.

## Interpretation branches

- Any nonzero small restart error rejects the checkpoint format and prevents
  the wide run.
- Any iteration-one/two policy digest mismatch rejects reuse of prior quality
  rows and the frozen audit as configured; it does not permit silently
  recomputing under a different trajectory.
- A wide restart digest mismatch rejects the state artifact even if policy
  quality improves.
- A final average that fails to improve by `1e-4` accepts the measured curve
  and rejects further blind DCFR iteration as the next efficiency move.
- A curve that improves but sharply saturates identifies an empirical stopping
  point and the value of faster kernels.
- A clean pass with continuing marginal gains authorizes native GPU fusion and
  a wider board/range replication matrix.

## What this experiment can teach us

The result will separate three possible bottlenecks:

1. **algorithmic convergence:** NashConv continues to fall, so faster sweeps
   buy strategy;
2. **averaging lag:** current improves while average trails, suggesting more
   iterations or an averaging-policy study; and
3. **representation/game limit:** both curves plateau early, so abstraction,
   update rule, or objective deserves attention before kernel work.

Per-seat curves also test whether the large seat-zero gap is a transient of
alternating update order. That is a declared diagnostic, not authorization to
allocate seat-weighted computation from six labels.

## Limitations

- One board and two constructed range families cannot establish general
  poker strategy quality.
- Exact reduced-game NashConv remains unilateral and coalition-blind.
- Training and evaluation share the same terminal algebra, though small dense
  controls and CPU/GPU checks independently pin its semantics.
- JSON checkpoint size includes repeated information keys and is not a runtime
  storage design.
- Offline blueprint compute is not online decision latency.

## Dissent protocol

**Confidence:** very high in h4 restart identity; high that h7 transfers; high
that the live iteration-one/two digests reproduce; moderate that average
quality improves through 32; low that either curve is monotone.

**Opposing evidence:** current strategies are sharp, exact off-path ties are
common, and multiplayer DCFR lacks a monotone convergence guarantee.

**Largest risk:** spending 30-plus minutes to produce a smooth-looking curve
whose conclusion is specific to one board. The frozen output is a kernel and
solver mechanism test, not a generalization claim.

**Cheapest falsification:** h7 bit identity, followed by the live iteration-one
and iteration-two policy digests. If those pass, iteration four is the first
new quality point; its direction provides an early warning but does not alter
the frozen continuation schedule.
