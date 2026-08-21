# ADR-0181: Preregister the h32 deep-horizon opportunity ladder

- Status: accepted preregistration
- Date: 2026-08-21
- Depends on: ADR-0166, ADR-0178, ADR-0179
- Config: `experiments/configs/h32-deep-horizon-opportunity-v1.json`

## Question

ADR-0178 positively identified one-step soft-generator weakness within a frozen
two-direction library, but did not establish whether ordinary DCFR produces
materially more certifiable value with depth. Does an off-clock 8/32/64-step
solve create stronger exact single-public-node directions, or does the useful
value plateau under the immutable six-seat envelope?

This is a mechanism audit. It does not fit a scheduler, authorize a live scale,
or make a strategy-population claim.

## Disclosed targets

Use two already opened ADR-0178 seat-1 blocker targets:

| Target | Board | Range family | Prior one-step wall time |
|---|---|---|---:|
| `panel_1/balanced/local_blocker_seat1_x2` | panel 1 | balanced | `8.54 s` |
| `panel_3/blocker_heavy/local_blocker_seat1_x2` | panel 3 | blocker-heavy | `7.17 s` |

They are the fastest disclosed one-step target within each range family and lie
on different boards. Runtime and structural coverage select them; no strategy
label selected the pair. Their ADR-0178 outcomes are already known, so this is
not a fresh holdout and cannot support a transfer-rate or population claim.

The audit must reconstruct each target from the frozen source belief, reproduce
its exact descriptor identity, and replay ADR-0178's six one-step soft public-
node blocks. The independently recomputed one-step policy digest is diagnostic,
not an authority gate. Structural block membership plus the preregistered
Float64 warm-start ceilings are the semantic replay gates, consistent with
ADR-0179.

## Depth ladder and endpoints

Warm-start resident DCFR from the same immutable source-average-64 blueprint and
run exactly 64 complete steps per target. Snapshot current and average policies
at steps 8, 32, and 64. Add one hybrid endpoint by purifying average-64: at each
information set choose the first maximum-probability action, with action order
as the tie-break.

The seven frozen endpoint families, in order, are:

1. `current8`;
2. `average8`;
3. `current32`;
4. `average32`;
5. `current64`;
6. `average64`; and
7. `purified_average64`.

Purification is a diagnostic direction family, not a deployment rule. Record
current/average policy total variation, cumulative solve time, every step's
wall time and work telemetry, persistent pool observations, and physical GPU
free memory.

## Exact certificate scope

For each endpoint and each of the six replayed blocks per target, overlay only
that block's 32 information sets onto the immutable blueprint. One common scale
therefore changes exactly one acting seat at one exact public history. The
per-seat gains and NashConv along the scalar retain ADR-0177's convex sublevel
geometry.

Use the same 34-point geometric-halving grid from scale 1 through `2^-33`.
Check the endpoint and numerical floor, bisect the first complete scale, then
find the exact discrete NashConv minimum over the complete suffix. Synthetic
controls already prove that the procedure uses at most 16 independent exact
certificates per direction. No multi-actor union or cross-public-node direction
is eligible for this optimization.

Every certificate:

- compares with the same immutable source-average-64 blueprint;
- uses the blueprint per-seat deviation gains plus the frozen raw guard;
- never reanchors or chains another result;
- expires at the public transition; and
- is an off-clock label whose selected scale is unavailable live.

The emitted policy is always the immutable blueprint.

## Measurements and interpretation

Report positive exact certified value by endpoint family, checkpoint, target,
and acting seat; largest and best complete scale; binding condition; certificate
time; solve time; policy displacement; and memory extrema. Compare the new
library with ADR-0178's retained soft and regret-vertex values on the identical
twelve blocks.

Freeze “material depth lift” as:

```text
best aggregate current/average value at step 32 or 64
    >= 2 × best aggregate current/average value at step 8
and
deep value > step-8 value + one raw guard per block
```

This classification is descriptive and is not an outcome gate. Also report
whether purified-average-64 exceeds raw average-64 and how the best deep DCFR
family compares with ADR-0178's bounded two-direction oracle.

- A material lift supports depth as a generator mechanism and motivates a
  separately preregistered amortized-deep architecture.
- A plateau adds evidence that ordinary deeper DCFR does not repair the local
  opportunity problem on these targets.
- A purification win preserves generator-direction ambiguity even if depth
  helps.
- No outcome proves global opportunity exhaustion or authorizes a live rule.

## Outcome-neutral gates

Require two targets, 128 complete resident steps, six checkpoint rows, twelve
replayed public blocks, 84 endpoint/block directions, no more than 16 queries
per direction or 1,344 total, two blueprint labels, clean committed execution,
accepted parent identities, exact immutable input provenance, numerical warm
identity, block replay, endpoint order, convex scope, search invariants,
independent immutable-anchor certificates, finite outputs, a 60-second ceiling
per step and certificate, a 12 GB pool ceiling, a 1 GB physical-free floor, and
a broad 4,200-second audit ceiling.

Do not gate on policy movement, completion rate, binding constraint, scale,
certified value, depth lift, purification lift, comparison with the parent
oracle, or retrospective latency.

## Decision

Commit the config, implementation, and mutation controls before any new deep
h32 step or certificate label. Execute once from that clean preregistration
commit. Preserve the frozen envelope and make no strategy-quality claim while
the audit is running.
