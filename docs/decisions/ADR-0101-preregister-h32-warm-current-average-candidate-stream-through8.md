# ADR-0101: Preregister h32 warm current/average candidate stream through 8

**Status:** Frozen after ADR-0100 and before any h32 warm current-policy or
iteration-eight quality label

**Date:** 2026-08-20

## Decision

Reuse the exact four ADR-0099 target beliefs and all twelve serialized warm
states. Evaluate the previously unmeasured current policies at iterations one,
two, and four. Restore each exact iteration-four state, continue DCFR through
iteration eight, and evaluate current and average eight. Replay one frozen
current-then-average candidate stream through the existing aggregate and
all-six-seat unilateral incumbents.

The frozen config is
`experiments/configs/h32-warm-candidate-stream-v1.json`, SHA-256
`154a281bf4ab2c7808b602581f2f68be25095fe9c4a486080f6060172cb78883`.
The runner is `src/pontius/h32_warm_candidate_stream_audit.py`, SHA-256
`2f00b5123439dc3a933728461a927d1997d731c62d265a867d049dcc78ee54a9`.
The result target is
`experiments/results/h32-warm-candidate-stream-v1.json`.

The complete ADR-0099 source artifact is pinned at SHA-256
`150362ea770c80190c8124148fa66e0a376d98d1bd01b790f3d11e5ad9b5d8a9`.
The post-freeze shifted-belief h4 dense control is pinned at SHA-256
`c276a3cb0c5ba0b1cca64ebf39f475b8f6db54d3b48e94313699142c4db0cbe5`.

No current-policy NashConv, current-policy deviation vector, iteration-eight
policy, or iteration-eight quality value was observed before this freeze.

## Question

ADR-0100 produced two competing explanations:

1. fixed average four was merely the wrong product endpoint, while sharper
   current policies or a longer average contain more safe value; or
2. warm DCFR itself moves in an unhelpful direction under the dense strength
   shifts, so faster verification would accelerate the wrong generator.

This audit separates them using candidates already latent in the trajectory.
Current policies cost no additional search to generate, and continuing four
more iterations is cheaper than designing a new solver or verifier.

## Frozen source and continuation

For each balanced/blocker-heavy source family and each local-blocker/all-seat
strength target:

1. rebuild the exact source and target workspaces from the ADR-0099 config;
2. reproduce the complete target descriptor, excluding timing from its
   digest;
3. validate iteration-one, -two, and -four state digests plus both policy
   digests;
4. reconstruct and evaluate current one, two, and four;
5. restore iteration four into a pristine target-belief solver;
6. execute exactly iterations five through eight;
7. export, JSON-round-trip, restore, and re-export the iteration-eight state;
   and
8. evaluate current eight and average eight.

The source average-one/two/four and blueprint quality vectors are reused
literally from the pinned artifact. Re-evaluating them would add about five
minutes while testing no new policy. Their state/policy digests are checked
before reuse.

There are five new exact evaluations per target and twenty overall:

- current one;
- current two;
- current four;
- current eight; and
- average eight.

There are four new training steps per target and sixteen overall.

## Frozen candidate order

The full stream is:

1. current one;
2. average one;
3. current two;
4. average two;
5. current four;
6. average four;
7. current eight; and
8. average eight.

Current precedes average at each checkpoint because it is the strategy emitted
by the latest regret update; the average then supplies the stable trajectory
summary at the same paid search horizon. This order is frozen, not selected
from quality labels.

Replay three declared portfolios independently from the iteration-64
blueprint:

- `full_interleaved`: all eight candidates in the order above;
- `current_only`: current one/two/four/eight; and
- `average_only`: average one/two/four/eight.

Each portfolio keeps independent aggregate and unilateral incumbents. The
unilateral rule still requires a strict aggregate NashConv reduction above the
`1e-10` normalized guard and no raw deviation-gain increase above the
corresponding `3e-9` guard for any seat.

The portfolios are analytical controls, not a fitted policy-kind dispatch.

## Quality and cost reporting

For every new policy retain:

- exact utilities, best-response values, and six deviation gains;
- normalized NashConv and zero-sum residual;
- policy digest and distribution statistics;
- cumulative search cost; and
- exact evaluation, terminal, reverse, memory, and GPU telemetry.

For each portfolio report:

- final aggregate and unilateral incumbents;
- normalized reduction from the target-belief blueprint;
- search-to-eight cost;
- the sum of every candidate evaluation charged to that portfolio;
- precompiled and one-shot verified bills; and
- unilateral reduction per precompiled millisecond.

The full stream is also compared with ADR-0099's average-only-through-four
unilateral incumbent. This is a declared diagnostic, not a quality gate.

No signed clean-fringe or learned verifier participates. The question remains
candidate quality under an exact teacher.

## Frozen mechanism gates

The audit passes only if:

- four target rows, two per family, are present;
- each target has three source states, five new exact evaluations, eight
  candidate rows, and four extension steps;
- every extension reaches iteration eight;
- all geometries retain 6,144 information sets and 12,288 hand-action entries;
- balanced work uses 435 sparse terminal batches and blocker-heavy work uses
  311 on every step and evaluation;
- the complete ADR-0099 source, target descriptors, source states, and source
  policies reproduce exactly;
- iteration-four restore and iteration-eight checkpoint round trips are exact;
- every portfolio is non-worsening and obeys the frozen guard semantics;
- maximum step, evaluation, and target compilation times remain below 60, 60,
  and 30 seconds;
- host numeric and GPU pool peaks remain below 3 GB and 4 GB;
- maximum zero-sum residual is at most `1e-9`;
- every state, policy, and quality value is finite; and
- total wall time is at most 1,800 seconds.

There is no gate on current-policy quality, iteration-eight quality,
acceptance count, safe reduction, policy-kind ordering, or performance rate. A
clean strategic rejection must pass.

## Frozen hypotheses

Report these independently:

1. at least one current policy is accepted by the full unilateral stream;
2. at least one current policy is accepted on an all-seat strength target;
3. average eight is unilateral-safe versus the blueprint on at least one
   all-seat strength target;
4. the full stream improves upon ADR-0099's average-only-through-four
   unilateral incumbents;
5. the full stream has positive total unilateral reduction from the four
   blueprints; and
6. the current-only portfolio finishes below the average-only portfolio.

These are four-case development hypotheses. No result authorizes a current
versus average selector.

## Predictions before results

**Moderate confidence:** at least one early current policy is safely accepted.
Current policies react immediately to the shifted counterfactual values and
may expose useful directions before averaging dilutes them.

**Low-to-moderate confidence:** a current policy rescues at least one dense
strength target. The large target-belief residual supplies headroom, but
average two and four moved consistently in the wrong direction in both
families.

**Low confidence:** average eight becomes safe on a dense target. The damage
grew from average two to four; recovery by eight is possible but not the
default extrapolation.

**Moderate confidence:** the full stream improves on the source stream because
it cannot lose accepted quality and receives five additional exact
opportunities per target. This is not a claim that the improvement exceeds its
large verification bill.

## Validation before freeze

Five tests pin the complete source/workload/gate matrix, reject selector or
schedule mutations, reconstruct all twelve source states and twenty-four
source policy digests, verify target timing exclusion, and exercise aggregate
versus unilateral portfolio accounting.

A pre-freeze h4 orchestration control used the balanced local-blocker target.
It ran dense and leaf-adjoint DCFR through iteration four, serialized/restored
the leaf state, and continued both through iteration eight. Maximum complete
trajectory disagreement was `1.95e-15`. Final current and average NashConv
agreed with the literal dense evaluator within `1.12e-15` and `5.31e-15`.

A label-free h32 preflight rebuilt all four target descriptors exactly and
restored all four iteration-four states to their exact digests. Mean marginal
TVs remained `0.008188`, `0.072099`, `0.004234`, and `0.070051` in frozen
family/shift order.

The complete repository/GPU regression is required before execution.

## Interpretation branches

1. **Current rescues dense shifts:** the candidate generator has valuable
   sharp directions. Next add interpolation and per-seat sub-iteration
   checkpoints, then justify the h32 policy-delta verifier against the expanded
   stream's bill.
2. **Only sparse targets improve:** the replicated local/dense split hardens.
   Change dense adaptation—belief-corrected initialization, proximal updates,
   or coordinate candidates—before native verification.
3. **Average eight recovers:** iteration four was too short, but a fixed horizon
   remains unsafe. Keep the anytime incumbent and measure marginal gain per
   additional step.
4. **New candidates add no safe value:** stop extending this generator. Widen
   the game or replace the update rule before optimizing the read path.
5. **Aggregate improves while unilateral rejects:** retain the vector gate and
   treat the new policy as a direction for interpolation or seat-wise repair,
   not a deployable strategy.
6. **Mechanism gate fails:** reject every strategic conclusion.

## Limitations

The experiment remains one river board, one bet size, equal stacks, two
generated factor beliefs, and two deterministic support-preserving shifts.
The current/average stream is only one ordering. Exact unilateral NashConv is
not coalition safety or full-NLHE exploitability, and the seconds-scale teacher
is not a runtime implementation.

## Dissent protocol

**Confidence:** very high in source/target/state identity; high that the audit
isolates the remaining fixed-stopping explanation; low-to-moderate that sharp
current policies safely adapt the dense shifts.

**Opposing evidence:** source-game current policies oscillated by 90-176%, and
the balanced strength current-48 control improved aggregate quality while
violating three unilateral constraints. Sharpness can reveal a useful
direction without producing a safe endpoint.

**Largest risk:** exact evaluation of five additional policies per target
spends most of fifteen minutes confirming that current policies are noisy and
average eight continues the same harmful dense trajectory.

**Cheapest falsification:** this audit. It consumes stored states and sixteen
additional steps, requires no new representation, and directly determines
whether the next investment belongs in candidate generation or verification.
