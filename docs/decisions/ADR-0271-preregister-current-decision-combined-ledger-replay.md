# ADR-0271: Preregister current-decision combined-ledger replay

- Status: accepted executable preregistration before any post-fold strategy label
- Date: 2026-08-22
- Follows: ADR-0270
- Closure input SHA-256: `e0ad1af41061fce837ac689fcc0507c105346c2a3b8b08756e86285c17a0f3e3`
- Safe-retreat input SHA-256: `e926a64ca5d7ac55086607c3c697c51165777d888767f051359f19bb743b2d4f`
- Config: `experiments/configs/h32-current-decision-combined-ledger-replay-v1.json`
- Config SHA-256: `c41f8acfac49d6a3c2430879ad5ab6af82db941cca953acf23e106e035913b82`
- Runner SHA-256: `20383e0ee212589c67caf9657bfac09556a571bd04f973eaacb6455d33579ed4`
- Control SHA-256: `f9995727ccaf69875640b8c227e9bb2aa59058aa4fd20a533471609c1b627ce1`

## Question

Do the exact global endpoint-closure path and independent safe half-retreat
certificate fit one complete 15-second current-decision ledger on all six
already-opened post-call contexts?

This is an executable accounting and identity audit over sealed artifacts. Its
arithmetic is already inspectable and no label blindness is claimed. The
purpose is to make the proposed composition explicit, mutation-tested, and
machine-gated before any post-fold strategy label is opened.

## Frozen pairing and identity

Join only the six `post_call` rows from ADR-0270 to the six ADR-0264 rows by
exact target ID in their common manifest order. Require unique and identical
target sets, source, acting player, public prefix, round, cut count, final row
counts, ordered cut-player/response-signature rows, and first-oracle response
signatures.

The two invocations reassociate Float64 work and therefore do not require
endpoint-policy digest equality. Under ADR-0179, require at most `2e-11` error
across source NashConv, first and final master lower bounds, and first exact
oracle objective. A deliberately perturbed objective and reordered manifest
are required negative controls.

## Exact incremental-work rule

ADR-0264's safe path already charges one exact endpoint oracle and one exact
factor-`0.5` retreat oracle on every target.

For each of the four zero-cut targets, the first endpoint oracle is epigraph
closed and the endpoint is independently certified. Global closure therefore
adds no work: the combined path retains two exact oracles.

For each of the two one-cut targets, the first oracle is not epigraph closed.
The safe path already charges the cut extraction and resolved master but does
not independently certify the resolved endpoint. Add exactly the final
post-cut endpoint oracle recorded by ADR-0270. The combined path then has three
exact oracles. Do not add or subtract any other component.

Require both recorded incremental endpoint oracles to be at most `1,000 ms`.
The ceiling has an explicit lower-ceiling negative control.

## Safety and value inheritance

For every pair, require ADR-0264's factor-`0.5` retreat to remain independently
exact-certified, cap-feasible, interior, accepted by the frozen predicate, and
strictly value-positive. This replay creates no candidate and cannot replace
that exact certificate.

The globally closed endpoint and the safely emitted interior retreat are
different objects. Closure proves the endpoint is globally optimal within the
frozen one-seat behavioral program; it does not make the half-retreat itself
globally optimal.

## Measured and conservative ledgers

For measured accounting, add the recorded incremental endpoint-oracle time to
ADR-0264's measured safe-retreat ledger on one-cut targets and add zero on
zero-cut targets.

For conservative accounting, preserve ADR-0264's complete
`13,967.615699994712 ms` floor. Add a fixed `1,000 ms` charge on each one-cut
target and zero otherwise. Require both measured and conservative totals to be
at most `15,000 ms` on all six rows. This leaves only
`32.3843000052875 ms` of conservative headroom on the one-cut shape; no
unpriced work may be inferred to fit inside it.

## Gates and label policy

Require clean Git, byte-pinned passing parents, exact pairing, six globally
closed targets, the frozen four-zero/two-one cut split, at most one cut round,
numerical identity, exact incremental-work classification, the `1,000 ms`
oracle ceiling, valid inherited retreat certificates, measured and
conservative deadline fit, immutable-blueprint historical emission, finite
output, and a null population claim.

Run on CPU only. Generate zero optimizer labels, zero strategy labels, zero
post-fold labels, zero candidates, and zero GPU work. Runtime is capped at 30
seconds.

## Decision

Commit the runner, config, controls, this ADR, roadmap, and generated status
from a clean tree, then invoke the replay exactly once. If every gate passes,
seal the result and separately preregister all six unopened post-fold targets
for a fresh closure-and-value confirmation with the same one-round algorithm,
factor `0.5`, exact certificate, cap, allowances, target order, and fail-closed
`1,000 ms` incremental endpoint-oracle ceiling.

If any pair, certificate, incremental charge, measured ledger, or conservative
ledger fails, reject that fresh combined trial and retain the existing safe
retreat without a live global-optimality claim.

## Claims boundary

This replay is retained, deterministic artifact arithmetic, not a measured
same-invocation path or fresh generalization result. It does not retire the
direction fallback, remove the warm DCFR step, authorize candidate emission,
or make a deployment-rate, IID, multi-seat, composition, cross-street,
chip-EV, AIVAT, full-width, exploitation, or poker-strength claim.
