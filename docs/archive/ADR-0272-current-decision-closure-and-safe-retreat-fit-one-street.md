# ADR-0272: Current-decision closure and safe retreat fit one street

- Status: accepted read-only ledger result; fresh post-fold confirmation preregistration authorized
- Date: 2026-08-22
- Implements: ADR-0271
- Clean preregistration commit: `8aa9dcbccfb15af842b8766f69601c03c74c6d52`
- Result: `experiments/results/h32-current-decision-combined-ledger-replay-v1.json`
- Result SHA-256: `2176807c6c9712931fa457e02fbd9165308bd406c7183f42092602d313639077`

## Result

The single CPU-only replay passes every frozen provenance, parent, target,
manifest-order, discrete identity, numerical identity, closure, cut-count,
incremental-work, oracle-ceiling, inherited safety, measured-ledger,
conservative-ledger, emission, label-count, finite, and null-claim gate. It
finishes in `0.109 s`, performs no GPU work, opens no optimizer or strategy
label, constructs no candidate, and leaves all six post-fold labels closed.

All six ADR-0270 rows pair exactly with ADR-0264. The maximum numerical error
across source NashConv, first/final master lower bounds, and first-oracle
objective is `1.08e-14`, below the frozen `2e-11` allowance. Ordered cut rows
and response signatures agree exactly.

## Incremental work

Four targets close at round zero. Their first exact endpoint oracle already
proves epigraph closure, so their complete global-endpoint plus safe-retreat
path retains the two exact oracles charged by ADR-0264.

Two targets require one cut round. Their first endpoint is not closed and was
not independently certified after the resolve in ADR-0264. Each therefore
adds exactly the final resolved-endpoint oracle from ADR-0270, raising its
complete path from two to three exact oracles. Those incremental oracles cost
`760.975 ms` and `844.294 ms`, both below the hard `1,000 ms` ceiling.

No warm step, initial row, master, cut extraction, retreat construction,
retreat certificate, envelope charge, or emission reserve is double-counted.

## Complete ledgers

The worst measured combined path is `5,884.573 ms`, leaving
`9,115.427 ms` under the 15-second street.

The conservative base remains exactly `13,967.615699994712 ms`. Applying the
fixed `1,000 ms` incremental charge to each one-cut path yields a worst
conservative total of `14,967.615699994712 ms` and only
`32.3843000052875 ms` headroom. Zero-cut paths retain `1,032.384 ms`.

Every inherited half-retreat is independently exact-certified, cap-feasible,
interior, predicate-accepted, and strictly value-positive. The actual
historical external emission remains the immutable blueprint.

## Interpretation

On these six opened post-call contexts, a path can both prove the one-seat
endpoint globally optimal and independently certify a value-positive interior
half-retreat within the 15-second accounting contract. This closes the
retrospective composition question that ADR-0270 left open.

It does not prove the emitted half-retreat globally optimal: the closed
endpoint and safe emitted retreat are distinct policies. Nor is the measured
margin a license to loosen the conservative contract; the binding one-cut
shape has almost no unpriced conservative slack.

## Decision

Accept and seal the read-only ledger result. Separately preregister all six
unopened ADR-0266 post-fold current-decision targets as the first fresh
confirmation of the complete closure-and-value path.

Preserve manifest order, one warm DCFR step, one-seat behavioral master,
multi-cut separation, at most one cut round, factor `0.5`, exact independent
retreat certificate, `2e-11` cap allowance, `1e-9` epigraph allowance,
`1e-10` quality allowance, inherited materiality threshold, immutable-
blueprint external emission, and campaign-wide prelabel barrier. Charge an
additional exact endpoint oracle only after a cut resolve; require it to finish
within `1,000 ms` and require the combined measured and conservative ledgers to
fit 15 seconds.

Require every target to close globally by round one and every retreat to be
safe and positive before considering current-decision direction generation
demotable. Any second-round need, numerical stall, endpoint-oracle overrun,
certificate failure, or ledger failure retains the direction fallback.

## Claims boundary

This result joins retained, non-IID post-call artifacts and is not a measured
same-invocation execution. It does not retire directions, remove the warm
DCFR step, emit a candidate, prove a deployment rate, or make a multi-seat,
composition, cross-street, chip-EV, AIVAT, full-width, exploitation, or broad
poker-strength claim.
