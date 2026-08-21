# ADR-0186: Fresh vertices replicate generator weakness but no free selector transfers

- Status: accepted prospective result
- Date: 2026-08-21
- Implements: ADR-0185
- Result: `experiments/results/h32-fresh-causal-direction-screen-v1.json`
- Result SHA-256: `c6fde183230994915668b5288bedb290ac7e960d4b13437d336e80a6bbd88b4d`

## Protocol outcome

The clean committed ADR-0185 invocation passed every outcome-neutral gate. It
reconstructed all six previously unlabeled seat-2 targets, performed one
numerically identical resident warm step per target, built 36 coherent public
blocks, compared 108 direction rows, and executed 1,313 independent exact
certificate queries. All 36 fixed probes were present and were reused when the
adaptive regret-vertex search requested the same scale.

The run preserved the immutable source average-64 anchor, independent
certification, convex one-seat/one-public-node scope, frozen direction and
feature order, source and target identities, and blueprint-only emission. It
makes no strategy-population or deployment claim.

## Direction-library result

Aggregate positive certified value was:

| Direction or bounded library | Certified value | Fraction of three-family oracle |
|---|---:|---:|
| soft DCFR | `6.7112e-7` | `5.4659%` |
| regret vertex | `1.2180e-5` | `99.2017%` |
| immutable-blueprint best-response vertex | `1.2100e-5` | `98.5467%` |
| paired soft/regret oracle | `1.2278325765842368e-5` | effectively `100%` |
| three-family oracle | `1.2278325766605647e-5` | `100%` |

The best-response family changed the oracle by only `7.63e-16`, for a lift of
`1.000000000062x`. It won ten raw block tie-breaks but zero material block
wins, and it failed the frozen twofold-plus-one-raw-guard-per-block
classification. This added family therefore plateaus inside the bounded
library. Its near equality with the regret vertex is evidence of directional
redundancy, not library completeness.

The fresh-panel soft fraction is close to ADR-0178's disclosed `4.87%` capture.
Thus the earlier generator diagnosis replicates on six new belief shifts:
ordinary one-step soft DCFR movement remains nearly orthogonal to the decisive
vertex direction available from the same warm state.

## Opportunity-feature result

The preregistered top-one denominator was the sum of each target's best block,
`1.0067756563050811e-5`. No feature met the frozen descriptive-candidate rule:

| Feature | Available before any certificate | Pooled Spearman | Mean within-target Spearman | Aggregate top-one capture |
|---|---|---:|---:|---:|
| regret mass | yes | `-0.0476` | `-0.1238` | `2.7161%` |
| negative minimum action gap | yes | `-0.2149` | `-0.2190` | `2.4705%` |
| fixed-probe estimated cap radius | no | `0.3079` | `0.2540` | `95.4145%` |
| fixed-probe positive value | no | `0.1527` | `0.1429` | `3.8304%` |

Regret mass therefore fails to transfer as an opportunity locator, and the
blueprint minimum-action-gap hypothesis fails more strongly. The cap-radius
probe finds most aggregate target-best value under its frozen top-one rule,
but its rank correlation misses the `0.5` threshold, its target behavior is
spiky, and observing it for all six blocks requires six charged certificates.
It is a geometric clue, not an online selector. Probe value itself does not
repair the opportunity-ranking problem.

## Constraint and seat geometry

Of 108 adaptive direction searches, 75 were cap-bound, none were
objective-bound, and 33 remained complete at the full grid endpoint. The
immediate limiter inside this library is therefore per-seat policy-to-gain
sensitivity rather than exhaustion of the immutable-anchor objective. This
does not establish value outside the frozen directions or global anchor
optimality.

The bounded value remains strongly order-extreme on this panel: acting seat 0
contributed `66.5304%`, acting seat 5 contributed `19.9535%`, and the two
together contributed `86.4840%`. This is consistent with the prior structural
hypothesis, but seat order was not a preregistered selector classification and
is not promoted here.

## Systems and street result

The complete off-clock audit took `1177.31 s`. Maximum resident warm-step time
was `11.524 s`; maximum observed exact-certificate time was `2.267 s`. The
maximum GPU-pool total was `8,214,049,792` bytes and physical free memory never
fell below `7,032,799,232` bytes.

For both free features on every target, the descriptive ledger containing one
warm step, the selected block's fixed probe, and the one-second emission
reserve fit the 15-second boundary: 12 of 12 ledgers ranged from `9.162 s` to
`13.136 s`. This establishes capacity for one precommitted probe attempt, not
for all-six probe ranking, adaptive scale search, or candidate deployment.

## Decision

Accept the prospective mechanism result. Retain regret vertices as the
decisive bounded direction and reject this immutable-blueprint best-response
vertex as a useful library expansion. Reject regret mass and blueprint minimum
action gap as live opportunity selectors on the frozen construction. Do not
promote the cap-radius probe, any observed seat, block, scale, or candidate.

The next bottleneck is obtaining useful direction/cap information cheaply
enough to choose and realize a regret-vertex move inside the street. A
successor must preregister a genuinely online ledger on fresh contexts, charge
every probe and final certificate, reserve emission time, and fail closed to
the immutable blueprint. The order-extreme concentration and cap-radius
capture may define a narrow hypothesis, but they require prospective transfer
and cannot be mined into a rule from this panel.

Do not expand ordinary DCFR depth or introduce a predictive/discount-schedule
variant yet. Those changes alter the soft trajectory while the replicated
failure is opportunity location and decisive-direction realization. Revisit a
modern DCFR-family arm only after an online-feasible selector exists or as a
frozen control against that selector.

## Limits

Six deliberately constructed seat-2 belief shifts are not a population. The
three directions are a bounded lower-bound library. The adaptive searches and
all-block rankings are off clock. Exact certified values are mechanism labels,
not evidence that any candidate improves real poker strategy, transfers across
streets, or should be emitted in play.
