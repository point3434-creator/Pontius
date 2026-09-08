# ADR-0087: Preregister leaf-adjoint best-response quality audit

**Status:** Accepted after h4 dense-oracle development, but before any h7 or
h32 leaf-adjoint best-response result

**Date:** 2026-08-20

## Decision

Run one frozen audit of exact fixed-policy utilities, unilateral best
responses, and NashConv through the leaf-adjoint engine. The frozen
configuration is
`experiments/configs/leaf-adjoint-evaluation-audit-v1.json`; its SHA-256 is
`9b76bafb135e1198f8cb24e47c62a61219fa45f327738650f3df43243c044b58`.
The result target is
`experiments/results/leaf-adjoint-evaluation-audit-v1.json`.

ADR-0086 proved that the engine can emit wide policies. This audit asks the
more important next question: did two cold DCFR iterations improve a literal
strategy metric at all? It deliberately runs before a deeper checkpoint
ladder or native optimization.

The audit has two separable products:

1. an exact dense-oracle bridge for the evaluator; and
2. a frozen strategy-direction test on the saved h32 policies.

If the evaluator passes but the policies do not improve, retain the evaluator
and reject the two-step policy hypothesis. Do not discard a correct measuring
instrument because it reports an unfavorable strategy result.

## Leaf-adjoint best-response identity

For target seat `t`, contract every terminal payoff after multiplying all
opponents' public-path action probabilities into unary private-hand factors.
Omit every action probability belonging to `t`. The resulting terminal vectors
already aggregate chance, compatible opponent hands, beliefs, and opponent
play for each open target hand.

Perform two reverse public-tree recurrences over the same terminal vectors:

- the profile recurrence folds child vectors by `t`'s supplied hand-wise
  policy at every target node; and
- the response recurrence chooses the maximum child vector independently for
  each target hand at every target node.

At opponent nodes, both recurrences sum children because the opponent action
probability is already embedded in each terminal path. Deeper target choices
are solved before ancestors, so repeated actions by the target do not create a
policy-enumeration cross product.

Summing the root vector over target hands gives the target's expected utility
or best-response utility. The nonnegative difference is its unilateral
deviation gain. Summing six gains gives NashConv.

This is exact NashConv for the frozen reduced game. In six-player constant-sum
poker it is not two-player exploitability, a coalition bound, or a guarantee
against cooperating opponents.

## Small dense-oracle bridge

Use both balanced and blocker-heavy range families at four and seven hands.
Evaluate two profiles on each geometry:

- exact uniform; and
- the immutable checkpoint-16 DCFR average from
  `real-policy-source-v1.json`.

This produces eight rows. For every row, compare the leaf evaluator with
`PublicTreeTensorEvaluator.evaluate` across all six seats. Require maximum
absolute error at most `1e-10` for:

- fixed-policy utilities;
- best-response utilities;
- deviation gains;
- total NashConv; and
- six-seat zero-sum residual.

Raw best-response action identity is diagnostic, not a gate. ADR-0084 proved
that independently reordered Float64 reductions can choose different sides of
an exact tie. Instead, replace each target's policy with the leaf-selected
deterministic response and evaluate that policy through the dense oracle. Its
utility must attain the dense best-response value within `1e-10`. This tests
the strategic object without pretending that a tied action label is unique.

If any small gate fails, the audit must stop before constructing or evaluating
any h32 profile. The wide quality result remains unopened until the evaluator
is an exact small-game instrument.

## Frozen h32 policy set

The immutable wide source is the accepted ADR-0085 artifact with SHA-256
`58455716893afcff2cc19eb5000f0bb74b90fa6b49564f08762b9c9db2b023ee`.
For each range family, independently verify the embedded policy digest and
evaluate four distinct profiles:

1. the step-one average, which must be bitwise uniform;
2. step-one current;
3. step-two current; and
4. step-two average.

Known TV, entropy, and purity metadata from ADR-0086 is allowed provenance;
none of these policies' utility, best-response value, deviation gain, or
NashConv has been measured through the new evaluator before this freeze.

Every full profile evaluation must return:

- six finite utilities;
- six finite best-response values and nonnegative deviation gains;
- finite NashConv;
- zero-sum residual at most `1e-9`;
- exactly 1,024 response actions per seat over 6,144 information sets; and
- no Cartesian `32^6` policy or payoff tensor.

Response action maps are not serialized in full. Record their counts, exact
tie counts, minimum action gap, and per-seat response values. The strategy
metric is the value, not the incidental encoding of a tie.

## Strategy-direction gate

For each family define:

`normalized_nash_conv = nash_conv / payoff_span`

and

`improvement = normalized_uniform - normalized_average_step2`.

Require improvement of at least `1e-6` in both families. This threshold is far
above the measured small-axis numerical error but intentionally makes no claim
that a two-step policy is good. It tests only whether the first saved average
moves in the correct aggregate unilateral direction.

Current-policy rows and step-one current are diagnostics. CFR theory generally
privileges the average, and six-player alternating DCFR does not promise a
monotone current profile.

A failure of this gate rejects the claim that two iterations bought measured
strategy quality. It does not reject the evaluator if all correctness gates
pass.

## Real-policy CPU/GPU crosscheck

On the step-two average of each h32 family, evaluate seat zero once through the
CPU SciPy path and compare it with the seat-zero result from the complete GPU
profile evaluation. Require profile utility, best-response utility, and
deviation-gain error each at most `1e-9`.

Record raw action mismatches and tie/gap telemetry, but do not gate raw labels.
Require a GPU speedup of at least `3x` after charging the one-time operator
upload on both families and specifically on the untouched blocker-heavy
validation family. This checks that the GPU gain transfers from uniform CFR
reads to a mature nonuniform response workload.

Each complete six-seat GPU evaluation must finish within 60 seconds. Require
conservative host numeric peak at most 3 GB and CuPy pool peak at most 4 GB.
The host estimate adds all retained terminal automata to the active
contraction estimate, accepting slight double-counting rather than hiding
persistent structure.

## Frozen environment

Use the same optional environment as ADR-0085:

- NumPy 2.5.2;
- SciPy 1.18.0;
- CuPy CUDA 13x 14.2.0;
- CUDA runtime 13.2 (`13020`);
- driver API at least 13.0 (`13000`); and
- RTX 5080 compute capability 12.0.

The exact requirement file and every new or frozen execution module are
hash-pinned in the configuration. `PONTIUS_CUDA_DLL_DIRECTORY` remains an
explicit Windows execution requirement.

## Pre-freeze engineering disclosure

Only h4 best-response evidence exists before this freeze.

On one deterministic nonuniform balanced-h4 policy, the additive evaluator
matched the dense oracle with:

- maximum utility error `8.88e-16`;
- maximum best-response error `1.78e-15`;
- NashConv error about `5.3e-15`;
- zero raw response-action mismatches across all 768 target information rows;
- no exact top-action ties; and
- approximately 227 ms complete leaf wall time.

On the canonical balanced-h4 checkpoint-16 average, utility error was
`1.33e-15`, best-response error `4.44e-16`, NashConv error `1.55e-15`, selected
response value error `1.78e-15`, and zero raw action mismatches. Its measured
NashConv was about 1.3447; this small-axis number is development evidence, not
a source-quality gate.

Three evaluator tests and two strict config-parser tests with nine mutation
subtests pass. No h7 row has been evaluated by the new best-response module.
No h32 utility, response, deviation gain, NashConv, response action, tie count,
or real-policy CPU/GPU speed has been observed.

ADR-0086's wide solver times, memory, policy digests, TV movement, and policy
statistics are prior frozen evidence. They do not reveal this audit's quality
answer.

## Interpretation branches

- A small utility or best-response failure rejects the algebra and prevents
  the wide run.
- A small raw action mismatch with zero selected-policy value loss is recorded
  as a tie/reduction diagnostic, not a failure.
- A wide CPU/GPU value failure rejects GPU NashConv measurement even if small
  identity passes.
- A charged real-policy speedup below `3x` rejects the transfer-heavy CuPy
  wrapper as the preferred wide evaluator.
- A quality-direction failure with all evaluator gates passing accepts the
  measuring system and rejects two-step averages as evidence of progress.
- A complete pass authorizes a preregistered restartable DCFR checkpoint
  ladder, with NashConv measured at each checkpoint before native work.

## What follows a complete pass

Add exact solver-state serialization for regrets, strategy sums, iteration,
axes, game config, and code provenance. Then run a modest h32 ladder from cold
start—candidate checkpoints 1, 2, 4, 8, 16, and 32—and evaluate average and
current NashConv at frozen points.

The ladder should stop early if quality per accumulated second saturates or
reverses. If the curve improves, its slopes decide whether native GPU fusion
is worth building. If it does not, accelerating the current DCFR formulation
would improve throughput without improving the bot.

## Dissent protocol

**Confidence:** very high in the h4 algebra; high that h7 identity transfers;
high that CPU/GPU value errors remain small; low in the direction of a
two-step six-player average.

**Opposing evidence:** the saved current policies are already about 86% pure,
the averages contain only eight distinct distributions, and multiplayer
alternating DCFR need not improve NashConv monotonically after each sweep.

**Largest risk:** choosing a metric because it is now computable. Unilateral
NashConv is essential strategy telemetry but does not measure coalition
robustness, population performance, or exploitative adaptation. It is the next
instrument, not the final objective.

**Cheapest falsification:** the frozen h7 dense bridge. If it passes, the
step-two average-versus-uniform h32 comparison directly answers whether the
first wide strategy artifact bought any aggregate unilateral quality.
