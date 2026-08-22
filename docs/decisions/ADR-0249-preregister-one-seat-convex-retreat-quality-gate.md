# ADR-0249: Preregister one-seat convex-retreat quality gate

- Status: accepted preregistration before any h32 retreat certificate or fallback label join
- Date: 2026-08-22
- Follows: ADR-0247 and ADR-0248
- Config: `experiments/configs/h32-one-seat-retreat-quality-v1.json`
- Config SHA-256: `c544bee4687e68a9059c0d6f7a92e5d6b1585a3cd122af4898767d8c9d9a3ca7`
- Runner SHA-256: `2dfda449fcf8061dd57c26a85b4c113995440118c82ecd2025997e30dccb9e81`
- Runner control SHA-256: `388942f695b2101453475ac08f259c82678456abb591367857899cdc64fad197`
- Exact-assessment SHA-256: `efcafe79a316fe02bc1fc5af030d5cb66a21929d95e276f5374fa1fd4cd19f29`
- Assessment control SHA-256: `c0a8edbabbb59c8c56c0f4d8c1ff217e22e75c8f9f21dbd8f7dc3cb2181e2e4b`

## Question

On the single retained ADR-0247 target, does an independently certified
factor-`0.5` blueprint-to-convex-endpoint retreat deliver more exact safe value
than the immutable blueprint and the accepted one-step, complete-31-block live
fallback? Does it also win on value per millisecond when the retreat is charged
the full conservative one-round ledger rather than its favorable measured
time?

This is the narrow quality question authorized by ADR-0247. The target is
already known and was selected for the preceding optimizer feasibility gate;
therefore a positive result is development evidence only and cannot establish
fresh transfer, population performance, deployment strength, or broad poker
quality.

## Frozen candidate and reconstruction

Reuse exactly `panel_2/balanced/checks_then_bet_seat1`, acting seat 0, the
immutable restricted blueprint, normalized guard `1e-10`, and factor-`0.5`
retreat. Derive the raw guard only with `raw_guard(layout, normalized)`; it must
equal `3e-9` from `layout.game.payoff_span = 30`.

Reconstruct the ADR-0247 optimizer without modifying its frozen runner:

1. perform the same one resident warm step;
2. build all six profile rows and five opponent fixed-response rows;
3. solve the source restricted master;
4. run one all-six exact oracle and add exactly the missing seat-4 and seat-5
   response facets;
5. resolve exactly once; and
6. construct the half-retreat from the immutable blueprint and reconstructed
   second-master endpoint.

Before opening the retreat label, require the exact blueprint, first-candidate,
endpoint, retreat, cut-player, cut-signature, and row-count identities frozen in
the config. Require both master bounds to reproduce within `1e-12`, all sparse
master primal and dual residual families to remain below `1e-8`, and all row,
projection, profile-equivalence, topology, provenance, warm-start, and external-
axis gates to pass. The policy digests are authoritative here because the
experiment explicitly tests deterministic reconstruction of the exact
previously sealed candidate before joining a new label; numerical gates remain
authoritative for the GPU-derived quantities.

## Frozen oracle budget and tolerance separation

Run exactly two all-seat exact oracles. The first is the required master
separation oracle. The second is spent on the factor-`0.5` retreat, not on a
third endpoint evaluation. The endpoint was independently evaluated by
ADR-0247 and must reproduce by frozen optimizer identities, but it receives no
new quality label in this trial.

The two tolerances implicated by ADR-0247's audit correction remain distinct:

- exact envelope caps use `2e-11`; and
- master-epigraph separation uses `1e-9`.

The shared exact-assessment primitive accepts those knobs separately. Its
required negative control constructs a `5e-10` cap violation that must fail the
cap check while passing the epigraph check. Quality-vector and Jensen
comparisons use the already established ADR-0179 `1e-10` Float64 ceiling.
Exact digests of GPU-derived quality values are diagnostic only.

## Label barrier and comparator

The accepted fallback artifact is pinned as opaque bytes by SHA-256 before the
run. Its numeric value, NashConv, and charged time are deliberately absent from
the new configuration. Do not deserialize that artifact until all optimizer
identities pass, the retreat policy is frozen, and the independent retreat
oracle completes.

After certification, open exactly the depth-1 arm for the same target and
require its 31-block manifest, immutable blueprint, candidate ID, policy digest,
complete independent certificate, accepted shadow status, and deadline status.
Then verify internally that its sealed exact value equals blueprint NashConv
minus candidate NashConv. No comparator field may influence candidate
construction, cut selection, retreat factor, certificate, or tolerance.

## Exact retreat certificate

The final all-six exact response evaluation is the sole safety and quality
authority. Require:

- every clamped exact deviation gain to be at or below its immutable-blueprint
  cap plus `2e-11`;
- exact retreat NashConv to improve on the immutable blueprint by more than the
  `1e-10` quality allowance;
- exact NashConv to lie below the convex Jensen ceiling formed from blueprint
  NashConv and ADR-0247's independently evaluated endpoint `U`, plus `1e-10`;
  and
- the minimum exact cap slack to be at least
  `(1 - 0.5) * raw_guard - 2e-11`.

The Jensen and interior-slack checks are theorem diagnostics. They do not
replace the independent exact certificate.

## Wall clock, promotion, and emission

Charge warm work, eleven initial passes, both master solves, the first exact
oracle, both cut rows, the retreat exact oracle, at least `50 ms` for retreat
construction and envelope work, and the fixed `1,000 ms` synchronization/action
reserve. Require the measured total to fit 15 seconds.

For the promotion comparison, charge the retreat the full corrected ADR-0247
conservative ledger of `13,967.6157 ms`. This is valid because it substitutes
the same all-six exact oracle primitive on the retreat for the endpoint oracle;
the oracle count and every other conservative reserve remain unchanged. Require
that ledger to fit 15 seconds as well.

Authorize a separately preregistered fresh-target replication only if every
gate passes and both of these strict comparisons hold:

1. retreat exact value exceeds fallback exact value by more than one raw guard;
   and
2. retreat exact value divided by `13,967.6157 ms` exceeds fallback exact value
   divided by its sealed charged ledger.

Otherwise retain the accepted one-step/31-block fallback and reject fresh
retreat replication at this design point. No threshold, factor, target,
comparator, or ledger may change after seeing the label.

The run is shadow-only. Even a passing retreat is not externally emitted;
`actual_emitted_policy` remains the immutable restricted blueprint. A pass can
authorize only fresh-target research, not deployment.

## Claims boundary

The experiment may establish one-target exact safe value and a conservative
rate comparison. It makes no fresh-target, population, multiplayer-safe,
multi-seat, composition, cross-street, exploitative, deployment, or broad
poker-strength claim. The one-seat and no-composition boundaries remain exact.

## Decision

Commit the assessment primitive, runner, controls, config, this ADR, roadmap,
and generated status from one clean tree before the first retreat certificate.
Invoke the frozen artifact once with the repository `.venv` and no manual CUDA
DLL setup; ADR-0248 must supply the pinned bundle. Follow the promotion or
rejection branch without adjustment.
