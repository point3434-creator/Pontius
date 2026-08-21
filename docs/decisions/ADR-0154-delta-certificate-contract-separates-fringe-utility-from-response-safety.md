# ADR-0154: Delta-certificate contract separates fringe utility from response safety

## Status

Accepted as an additive semantic and mutation-control layer after ADR-0153.
It authorizes a separately preregistered response-certificate latency bridge,
not an h32 strategy run or online-deployment claim.

## Context

The deployment constraint is 15 seconds per decision. The relevant product is
therefore not maximum iterations or policy movement; it is maximum certified
decision value emitted before a hard deadline, with deterministic blueprint
fallback when no new certificate can finish.

ADR-0080 accepted the signed clean-fringe telescope and reach-weighted bound
for exact fixed-policy utility deltas. ADR-0108 through ADR-0110 accepted exact
partial-vector response verification and device residency. ADR-0111 made every
certificate one-root, one-belief, one-prefix, one-decision evidence that
expires after a public transition and never reanchors implicitly.

ADR-0153 now supplies 24 complete one-step rejection profiles, including two
one-size candidates that improve the scalar objective but breach immutable
caps. Those are useful future autopsy customers, but the clean-fringe utility
primitive cannot yet certify their cap vector.

## Engineering result

Add `src/pontius/delta_certificate_contract.py`, SHA-256
`79c61774eb463542b0cc658ef5d81afff84119317fe66aaeb9d3e4efc34c2774`,
and its direct mutation control
`tests/test_delta_certificate_contract.py`, SHA-256
`12af381ac5af4c7579b121b67ced0ee06f0693daca9f0accb8d589fda5a0cdda`.

The contract supplies:

- independent cap-pass and objective-pass classification;
- exact information-set atomic manifests and source-relative interpolation;
- one shared geometric-halving grid down to the existing `1e-10` numerical
  floor;
- exact inclusion-exclusion interaction residuals for recertified unions;
- complete certificate-scope identity and digesting;
- explicit expiry, no-reanchor, and no-cumulative-claim fields; and
- a 15-second fail-closed deadline check with a caller-supplied emission
  reserve.

Seven direct controls pass. They cover all four cap/objective cells, exact
atomic reconstruction, the shared grid, union residuals, payoff-span and epoch
staleness, reanchoring and cumulative-claim rejection, deadline fallback, and
the disjoint-hand-slice sup-norm tripwire.

## Load-bearing zero-reach result

A three-player exact control changes one information set that has zero reach
under the fixed blueprint. All fixed-policy utilities remain exactly
unchanged, but at least one best-response value changes. A subsequent identity
read reproduces the immutable source evaluation, proving that the epoch overlay
does not leak stale values across calls.

This result fixes the next system boundary:

`exact clean-fringe utility delta != exact unilateral-gain delta`.

For the changed seat's own deviation gain, its best-response value is
independent of its own behavioral policy, so the clean-fringe utility delta can
update that coordinate. For opponent seats, the edit can alter both fixed
utility and best-response value, including from a blueprint-zero-reach branch.
Those coordinates require exact source-relative response recertification.

No certificate may infer cap safety from zero blueprint reach, a zero
fixed-utility delta, policy total variation, or clean-fringe exactness alone.

## Frozen identification semantics

Every future rejection-autopsy probe must occupy one cell of the full 2x2:

| Cap condition | Objective condition | Classification |
|---|---|---|
| pass | pass | admissible improvement |
| fail | pass | cap-only rejection |
| pass | fail | objective-only rejection |
| fail | fail | cap-and-objective rejection |

Opportunity exhaustion may be diagnosed only if objective failure also
dominates the frozen atomic probe class. Generator proposals alone cannot
distinguish exhaustion from bad directions.

Acceptance-unit coarseness requires atoms or recertified unions that pass when
their parent bundle fails. Atomic safety never composes implicitly. Every union
must receive a new exact certificate and record its inclusion-exclusion
residual, same-seat or cross-seat tag, public-path co-occurrence, and
best-response action-switch telemetry.

Genuine local narrowness requires small admissible radii or violations at the
smallest nonzero inherited-grid perturbation. Absolute blueprint deviation
gains are anchor opportunity/risk descriptors, not cap slack; guard-relative
cap slack is uniform at the anchor.

Generator poverty requires certified value in the frozen probe class plus low
generator direction coverage or value capture. The benchmark must be finite
and deterministic. If its class contains every original generator candidate,
the captured fraction is bounded by one. Otherwise the result must be named a
lower-bound benchmark ratio and values above one are permitted.

## Fifteen-second deployment contract

Wall clock is the operational constraint and fixed work is the scientific
exposure. Future audits must report both.

The online path is:

`resident blueprint/cache -> state ingest -> bounded search -> incremental response certificate -> selection or blueprint fallback -> action emission`.

Cold topology construction and complete offline six-seat oracle evaluation do
not belong on the critical path. The runtime must retain the last completely
certified candidate and begin fallback early enough to emit inside 15 seconds.
An unfinished search step, atomic probe, union, or certificate has zero online
value.

The emission reserve is deliberately not selected in this ADR. It must be
calibrated from measured tail latency under a separately frozen runtime audit.
That audit should gate p95/p99 or a conservative maximum, not mean latency,
and decompose state ingestion, probability/overlay preparation, fringe value,
response recertification, selection, synchronization, and emission.

Primary deployment reporting is certified improvement delivered by the
deadline. Policy-TV per second is a motion diagnostic. Certified value per
second and deterministic work units per second explain whether more compute
buys value or merely movement.

## Decision

Adopt the contract and controls. Do not yet call the clean-fringe primitive an
envelope certificate. The next bounded implementation is a reduced exact
response-bridge audit followed by a one-size h32 replay preflight using
retained policies and resident caches. It must establish whether a complete
local response certificate can fit the 15-second boundary before any
large-scale atomic autopsy is scheduled.

Two-size online authorization is later. ADR-0153's two-size step and verifier
costs are not presently compatible with a conservative 15-second critical
path, even though its cache memory is safe.
