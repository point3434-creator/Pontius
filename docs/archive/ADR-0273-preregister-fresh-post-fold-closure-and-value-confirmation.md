# ADR-0273: Preregister fresh post-fold closure and value confirmation

- Status: accepted preregistration before any post-fold warm step, optimizer, or strategy label
- Date: 2026-08-22
- Follows: ADR-0272
- Manifest: `experiments/results/h32-post-fold-posterior-manifest-v1.json`
- Manifest SHA-256: `01e424665ce7f7c81c6d15602eef716e18bb16c6a1035588831310ab90fcfc5f`
- Config: `experiments/configs/h32-post-fold-closure-value-confirmation-v1.json`
- Config SHA-256: `848d61f09378958ab07d9de2395691d9899d29d61dc79ad99c4bdda725208807`
- Runner SHA-256: `2766f93d2c0a47226887e71de0f6366a0a94bab430617b6d72a5fcae50bf68b6`
- Setup SHA-256: `9e21a6fabfdb728c0547dbe4cf0ab306c63e7d3c178c03da3d8873c456f5f01e`
- Control SHA-256: `bd0a3d0a029e94bed7c71be313dbe25936439cfc81ea6735b0aedfdb6df07004`

## Question

On all six unopened ADR-0266 post-fold current decisions, does the frozen
one-seat program close globally by round one, produce an independently safe
and value-positive factor-`0.5` retreat, and fit the complete measured and
conservative 15-second ledgers?

This is the first strategy-label campaign on these identities. The boards and
source blueprints are retained, but each post-fold posterior identity and all
of its optimizer and strategy labels are fresh.

## Frozen targets and inheritance

Use all six ADR-0266 targets in manifest order. Do not select, omit, or reorder
by belief TV, source value, prior post-call result, position, anticipated facet,
or timing. Each target observes checks, one bet, and exactly the first
responder's fold; the next responder is current, with one h32 acting public
node, 32 information sets, 64 behavioral variables, and three opponents still
downstream.

Load the byte-pinned ADR-0263 current-decision config and inherit its source
blueprints, one resident DCFR warm step, six profile rows, five opponent fixed-
response rows, behavioral master, multi-cut first separation, maximum one cut
round, factor `0.5`, materiality rule, guard, cap and epigraph allowances,
projection and master tolerances, runtime contract, memory gates, and
immutable-blueprint external emission.

Change only the posterior/continuation setup from first-call to first-fold and
add the ADR-0272 post-cut endpoint certificate.

## Fail-closed fold setup

Use a separately pinned fold adapter. It reconstructs the sealed fold
observation sequence and requires exact public-prefix, observed-responder,
observed-action, posterior, current-player, fold/call-root, and downstream-
responder identity. It temporarily replaces only the sealed core's setup
function and restores it on success or failure. A call-specific historical
adapter is not generalized or edited.

## Exact endpoint and epigraph capture

The sealed historical core computes but does not retain its full endpoint
policy or master epigraph vector. Wrap its existing mix and master calls in a
scoped capture that calls the byte-pinned functions exactly once and records
their outputs without changing arguments or results. Require the captured
endpoint digest and every captured epigraph digest to equal the sealed
construction row, then restore both functions on success or failure.

Controls require exact mix behavior, restoration, nested-use rejection, and a
mutated epigraph digest to fail closed. The capture adds data retention, not a
new optimizer or safety rule.

## Barrier and oracle order

For each fixed target, construct the endpoint and retreat with the existing
first exact separation oracle and optional multi-cut resolve. Freeze all six
captured endpoints, final epigraphs, retreats, and prelabel checks before any
post-cut endpoint-confirmation oracle or final retreat oracle. Cross-target
adaptation is forbidden.

The first separation oracle is an adaptive construction label, as in ADR-0263;
the campaign-wide barrier applies to the newly added post-cut endpoint labels
and final retreat labels. Record this distinction explicitly rather than
calling the whole campaign label-blind.

## Global one-seat closure

For a zero-cut target, reuse the first exact endpoint oracle; charge no new
oracle. For a one-cut target, resolve once and run exactly one new exact
all-seat oracle on the captured post-cut endpoint before certifying the
retreat. Do not add a second cut or resolve again regardless of that result.

Call an endpoint globally closed within the frozen one-seat program only when:

- its exact gains satisfy every blueprint-plus-guard cap under the `2e-11`
  allowance;
- its exact opponent responses close the final epigraph under the unchanged
  `1e-9` separation allowance; and
- exact endpoint NashConv minus the verified restricted-master lower bound is
  at most `1e-8`.

The lower bound and exact feasible endpoint remain distinct. Any material
bound reversal is an arithmetic failure. A second-facet need is a valid
negative closure outcome, not permission to continue generation.

## Safe retreat and value

Run one independent exact all-seat oracle on the frozen factor-`0.5` retreat.
That oracle alone has safety authority. Preserve the `3e-9` raw guard,
`2e-11` cap allowance, `1e-10` positive-quality allowance, and `1.48e-9`
required interior slack.

Report process validity separately from scientific confirmation. Successful
closure-and-value confirmation requires:

- all six endpoints globally close by round one;
- all six retreats are independently exact-certified, cap-feasible, interior,
  schedule-admitted, and strictly value-positive;
- at least four retreats exceed `0.001`; and
- both balanced and blocker-heavy families occur among those material rows.

## Complete ledger

Charge warm step, initial rows, every master, first exact oracle, cut
extraction, at least 50 ms for retreat/envelope work, final retreat oracle,
and 1,000 ms emission reserve exactly as ADR-0263 did.

For a one-cut target, additionally charge the measured post-cut endpoint
oracle and require it to finish within `1,000 ms`. Its conservative ledger is
the unchanged `13,967.615699994712 ms` floor plus a fixed `1,000 ms`; a
zero-cut target retains the unchanged floor. Require measured and effective
conservative totals to fit `15,000 ms`. No unpriced work may consume the
remaining `32.384 ms` one-cut margin.

## Gates and decisions

Require clean Git before runtime initialization; byte-pinned passing source,
manifest, and ledger parents; zero prior post-fold labels; exact manifest
order; current-actor fold topology; setup and capture restoration; captured
digest identity; the inherited numerical, row, projection, timing, memory,
response-accounting, and one-cut gates; campaign-wide barrier; reconstruction
identity; exact oracle/label accounting; hard endpoint-oracle ceiling; both
ledgers; independent retreat certificates; immutable external blueprint;
finite output; and a null population claim.

A process-valid run may report negative closure or value. If every scientific
condition passes, authorize a separate architecture decision on demoting
direction generation only inside this bounded current-decision continuation
scope. If any endpoint needs another round, any retreat is unsafe or
nonpositive, or the transfer threshold fails, retain the direction fallback.
Any process-gate failure rejects the invocation.

## Decision

Commit the fold adapter, capture/runner, config, controls, this ADR, roadmap,
and generated status from a clean tree. Then execute the six-target GPU
campaign exactly once. Do not pilot a target, inspect a partial value to alter
another target, loosen the endpoint ceiling, add a cut round, change the
retreat, or substitute a posterior after execution begins.

## Claims boundary

No candidate is externally emitted. Even a full pass applies only to the
fixed h32 one-seat current-decision continuation shape on retained boards and
blueprints; it is not an IID deployment rate. The globally closed endpoint and
safe half-retreat are different policies. No multi-seat, composition,
cross-street, chip-EV, AIVAT, full-width, exploitability, or broad poker-
strength claim is authorized.
