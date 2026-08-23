# ADR-0307: Make the action clock and preparation bank authoritative

- Status: accepted charter amendment and executable successor preregistration before action-clock or preparation-bank source
- Date: 2026-08-23
- Follows: ADR-0306
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0307
- Front-Door-Contract: ADR-0307
- Front-Door-Revoked: ADR-0281
- Front-Door-Active-Next: Implement only the additive continuous 15-second action-response ledger, provenance-bound one-use online preparation bank, and exact legal-decision-spine v2 below; preserve the ADR-0286 cumulative-street implementation for historical reproduction, keep all ADR-0305 streams and values unopened, and commit exhaustive timing/provenance tests before resuming v4 structures
- Front-Door-Blockers: the maintained controller still implements ADR-0282's superseded cumulative charged-compute street ledger; no provenance-bound preparation bank or action-clock spine v2 exists; v4 structures and values remain unopened; no complete bot or live host adapter exists

## Question

What time resource should Pontius optimize when the agent receives a 15-second
clock on each turn but can compute before that clock during prior streets or
opponent turns?

## Decision

Replace ADR-0282's cumulative 15-second charged-compute allowance per street
with two distinct and jointly reported resources:

1. one hard 15,000 ms continuous wall-clock response deadline for each
   controlled action, including the existing 1,000 ms synchronization and
   emission reserve; and
2. online preparation work performed before that action clock starts, which
   may benefit a later decision only through an exact provenance-bound
   artifact hit.

The optimization objective is now **maximum marginal chip-valued decision
quality per additional millisecond of attributable online workstation compute,
subject to the hard 15-second response deadline on every controlled action**.
Report the quality curve, not only one quality/latency ratio.

The response clock starts when an observed event makes the controlled seat the
actor, not when the resolver chooses to start a timer. It runs continuously
through event processing, belief updates, legality, candidate construction,
solving, certification, fallback selection, synchronization, and emission.
Pauses or uninstrumented gaps inside that interval still consume the external
wall. Each later controlled action receives a new 15-second response wall.

Opponent think and transport time before the controlled turn do not consume
the response wall. Agent computation during that opportunity is not free: it
is online preparation and consumes the one workstation. Preparation may begin
on an earlier street, enumerate future public branches, or refine a current-
street branch before the controlled seat acts. Only work embodied in an exact
matching artifact may be credited to the eventual decision. All preparation
spent, credited, unclaimed, invalidated, and aborted must remain visible.

## What banking means

Pontius banks **computed artifacts**, not unused milliseconds. Doing no work
for five seconds on a prior street does not create a 20-second future response
deadline. A decision may nevertheless embody more than 15 seconds of total
online computation when it consumes valid work performed before its action
clock.

An online preparation credit must bind at least:

- immutable artifact bytes or their externally verified SHA-256;
- complete consumer-defined semantic context SHA-256;
- implementation/source SHA-256;
- creation street and one monotonic, internally measured work interval; and
- one exact future action identity when claimed.

The preparation bank must reject duplicate artifact identities, stale or
mismatched context/source identities, caller-supplied elapsed time, reuse of a
one-use credit, noncanonical digests, nested work, clock reversal, and claims
outside an active action. A failed match remains spent preparation but supplies
zero credited work. The action deadline may report credited preparation but
must never add it to `remaining_seconds` or postpone fallback emission.

Reusable offline blueprints, models, and training are not online preparation
credits. Report their build/training cost separately. If a future deployment
host supplies a literal rules-defined time bank that extends an action clock,
it requires a separate exact adapter and contract. The default balance is zero;
this decision does not invent host permission to emit after 15 seconds.

## Executable successor boundary

Preserve `pontius.street_deadline.StreetDeadlineLedger` and
`pontius.legal_decision_spine.LegalDecisionSpine` unchanged as ADR-0282/0286
historical controls. They are no longer the governing timing implementation.

Implement additive successors with these properties:

- a monotonic action ledger starts exactly one active response, measures its
  continuous wall independently of explicit charge intervals, reserves the
  final second, archives every completed action and street, and resets only at
  the next controlled-action boundary;
- off-clock agent work is measured separately as preparation and never reduces
  or enlarges the action wall;
- a frozen preparation-bank entry owns its timing measurement and exact
  artifact/context/source identities, and a claim is one-use and action-bound;
- the v2 legal spine starts the clock as soon as its exact betting transition
  yields the controlled actor, charges construction and observation work to the
  correct side of that boundary, and always emits the immutable legal fallback
  if the work cutoff or final wall is crossed; and
- no caller may reset, extend, pause, or backdate an active response clock.

Use exact fake-clock tests for multiple controlled actions on one street,
first-to-act and last-to-act boundaries, previous-street and same-street
preparation, successful and mismatched claims, double claims, aborted work,
uninstrumented on-clock wall, reserve crossing, terminal finalization, street
archives, nested intervals, and clock reversal. Retain all exact-betting and
fallback legality invariants from ADR-0286.

No action-abstraction stream, sizing value, blueprint, resolver, GPU kernel, or
research label may enter this implementation checkpoint.

## Consequences

- Late position can exploit actual opponent elapsed time for branch-specific
  preparation without losing its full response wall.
- Early position can benefit from prior-street conditional preparation, but
  branch fanout and invalidation waste become explicit costs.
- Two agents compared at the same 15-second response latency must also report
  attributable online preparation; unlimited hidden pondering is not an equal-
  compute comparison.
- Scheduling research should estimate marginal quality from another
  millisecond on the current response versus another speculative branch,
  including hit probability and invalidation cost.
- ADR-0282 and every result produced under its cumulative-street ledger remain
  reproducible historical evidence. They do not establish capacity or latency
  under this successor contract, and this decision does not reinterpret their
  recorded numbers.

## Kill criterion

Source before this ADR; a timer that begins after the controlled seat is
already on the clock; any pause or reset within one response; credited work
without exact artifact/context/source identity; caller-supplied duration;
double credit; preparation seconds added to the live remainder; unreported
missed or aborted work; literal carryover beyond 15 seconds without an external
host rule; mutation of the historical ledger; hidden action-abstraction or
value dependency; or weakened fallback/reserve behavior rejects the successor.

## Claims boundary

This decision changes the governing resource contract and preregisters its
additive timing controls. It does not show that useful speculation exists, that
banked work improves strategy, that any cache has adequate hit rate, that a
complete decision fits 15 seconds, or that Pontius is strong. It opens no v4
structure or value and authorizes no action-abstraction, blueprint, convex-
master, resolver, GPU, self-play, or deployment integration. No revoked
experiment or external publication is authorized.
