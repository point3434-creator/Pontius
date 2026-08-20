# ADR-0103: Preregister h32 current-one/current-two behavioral interpolation

**Status:** Frozen after ADR-0102 and before any h32 interior-interpolation
quality label

**Date:** 2026-08-20

## Decision

Evaluate three fixed pointwise behavioral mixtures between warm current one and
current two on all four ADR-0101 targets. Replay the exact six-seat incumbent
over the ordered segment from current one to current two.

The frozen config is
`experiments/configs/h32-current-interpolation-audit-v1.json`, SHA-256
`3452e03a9d93c3a13901cc9bb252aa3b50d0297d7f0f3b4f01035d57633254a5`.
The runner is `src/pontius/h32_current_interpolation_audit.py`, SHA-256
`d1756cbe82b6e229a8090216d019381289f51f5f18ef2290dda1c2d735ff6789`.
The result target is
`experiments/results/h32-current-interpolation-audit-v1.json`.

Frozen strategy sources are:

- ADR-0101 candidate stream, SHA-256
  `b432eda21d1978b1dd576a9f4e7451250f1d53dcf9a88a6efa739d681ecb6f33`;
  and
- ADR-0099 warm states, SHA-256
  `150362ea770c80190c8124148fa66e0a376d98d1bd01b790f3d11e5ad9b5d8a9`.

No h32 policy at an interior coefficient was evaluated before freeze.

## Question

ADR-0102 found the same geometry on both local targets:

- current one improves aggregate NashConv and every seat's deviation gain;
- current two improves aggregate NashConv further; and
- only seat two crosses above its blueprint deviation gain at current two.

Does a fixed interior behavioral policy retain more of current two's aggregate
improvement while remaining inside all six unilateral constraints?

The two dense strength targets are mandatory negative controls. Both endpoints
are harmful there, so an interior acceptance would be surprising and must not
be inferred from the local result.

## Frozen interpolation

For every information set and legal action, define

`pi_alpha(a|I) = (1 - alpha) * pi_current1(a|I) + alpha * pi_current2(a|I)`.

Use exactly:

- `alpha = 0.25`;
- `alpha = 0.50`; and
- `alpha = 0.75`.

This is a pointwise behavioral mixture, not a random whole-policy mixture or a
realization-plan interpolation. It preserves every information key, action,
and normalized probability row and is cheap to construct from cached
policies.

The frozen candidate order is:

1. current one (`alpha = 0`);
2. alpha 0.25;
3. alpha 0.50;
4. alpha 0.75; and
5. current two (`alpha = 1`).

At each candidate the aggregate incumbent requires strict normalized NashConv
improvement above `1e-10`. The unilateral incumbent additionally requires no
seat's raw deviation gain to increase above the `3e-9` guard.

No coefficient is selected adaptively. The same ordered segment is measured
on all four targets.

## Frozen workload

For each family/shift target:

1. rebuild and digest the exact ADR-0101 target descriptor;
2. validate the iteration-one and iteration-two checkpoint and current-policy
   digests against both source artifacts;
3. reproduce alpha-zero and alpha-one policies exactly;
4. construct all three interior policies and verify normalization;
5. evaluate the three interiors with the exact GPU leaf-adjoint teacher;
6. reuse the frozen endpoint and blueprint quality vectors; and
7. replay the five-candidate aggregate and unilateral stream.

There are twelve new exact profiles and no new CFR steps.

## Honest cost bill

Every interior candidate is charged the cumulative two-step search required to
construct both endpoints. The portfolio bill includes:

- search through current two;
- exact reads for current one, all three interiors, and current two;
- target compilation plus blueprint evaluation in the one-shot arm; and
- candidate quality per precompiled millisecond.

Reused source evaluations are still charged to the hypothetical product even
though they do not contribute to this audit's wall time.

This is an exact-teacher strategy test. It does not claim that three online
policy reads are economical.

## Frozen mechanism gates

The audit passes only if:

- four targets, two per family, are present;
- every target contains three new evaluations and five candidate rows;
- every geometry retains 6,144 information sets and 12,288 hand-action
  entries;
- every balanced profile uses 435 terminal batches and every blocker-heavy
  profile uses 311;
- both complete source artifacts, all target descriptors, and all endpoint
  policy digests reproduce;
- alpha-zero/one differ from their endpoints by at most `1e-15`;
- every interpolated row is finite, nonnegative, and normalized;
- every incumbent is non-worsening and follows the frozen guard semantics;
- maximum exact evaluation and target compilation are at most 60 and 30
  seconds;
- host numeric and GPU pool peaks remain at most 3 GB and 4 GB;
- maximum six-seat zero-sum residual is at most `1e-9`;
- every policy and quality value is finite; and
- total wall time is at most 900 seconds.

There is no gate on interpolation quality, winning alpha, local improvement,
dense rejection, acceptance count, or rate. A complete interpolation failure
must pass.

## Frozen hypotheses

Report independently:

1. alpha 0.50 is unilateral-safe versus the blueprint on both local targets;
2. the interpolation stream improves upon current one on both local targets;
3. no dense interior candidate is unilateral-safe;
4. the same interior coefficient becomes the final unilateral incumbent on
   both local targets;
5. the four-target interpolation stream improves total unilateral quality over
   current one; and
6. alpha 0.75 is unilateral-unsafe on both local targets.

These are mechanism-development hypotheses over two replicated local targets,
not an alpha selector.

## Predictions before results

Under a linear approximation to the measured seat-two deltas, the local safety
boundary lies near alpha `0.61` balanced and `0.58` blocker-heavy. Exact
best-response values are nonlinear in behavioral policy, so these are only
orientation calculations.

**Moderate-to-high confidence:** alpha 0.50 is safe on both local targets and
improves aggregate quality over current one.

**Moderate confidence:** alpha 0.75 is unsafe on both local targets and the
final unilateral incumbent is alpha 0.50.

**High confidence:** no dense interior is accepted. Every seat is already
worse at current one and worsens further at current two in both families.

**Low confidence in economics:** even a strategic win may lose quality per
millisecond once three exact interior reads are charged. The purpose is to
shape the verifier customer, not vindicate the current teacher bill.

## Validation before freeze

Four tests pin the source/workload/alpha/gate matrix, reject post-label alpha
selection, verify exact behavioral endpoints and midpoint arithmetic, and
reconstruct all eight h32 endpoint policies against both frozen artifacts.

A pre-freeze balanced-local h4 rehearsal constructed all three mixtures after
two shifted-belief warm updates. Leaf-adjoint utilities, best responses,
deviation gains, and NashConv agreed with the literal dense evaluator. Maximum
NashConv error was `3.50e-15`; maximum component error was `2.89e-15`.

A label-free h32 preflight retained 6,144 information sets and 12,288
hand-action entries. No interior h32 quality value was requested.

The complete repository/GPU regression is required before execution.

## Interpretation branches

1. **Alpha 0.50 wins both local targets:** behavioral line search is a real
   candidate generator. Freeze its policy deltas and exact read count as the
   first h32 verifier workload.
2. **Different alphas win:** interpolation still works, but no fixed coefficient
   is supported. Build a conservative bracketed reader or retain the measured
   discrete portfolio without fitting a target selector.
3. **No interior beats current one safely:** the seat-two boundary is too sharp
   or aggregate benefit too weak. Move to per-seat sub-iteration candidates or
   a constrained/proximal update.
4. **A dense interior wins:** inspect carefully; nonlinear composition created
   value absent at both endpoints. Replicate before changing architecture.
5. **Mechanism failure:** reject every strategic result.

## Limitations

This remains one river board, one action size, equal stacks, two constructed
belief families, and two deterministic shifts. Three coefficients do not
locate an exact safety boundary. Behavioral interpolation may behave
differently in deeper trees, and unilateral deviation constraints do not imply
coalition safety.

## Dissent protocol

**Confidence:** very high in source and arithmetic identity; moderate that
alpha 0.50 improves both local incumbents safely; low that the existing exact
bill is economically favorable.

**Opposing evidence:** multiplayer best-response values are piecewise nonlinear
in behavioral strategy. An opponent response switch between current one and
current two could move the binding constraint far from the endpoint-based
linear estimate.

**Largest risk:** extracting a slightly larger safe gain from the easy sparse
targets while making no progress on the strategically larger dense shifts.

**Cheapest falsification:** the frozen twelve reads. They require no additional
training, representation, or selector and directly test the repeated seat-two
boundary.
