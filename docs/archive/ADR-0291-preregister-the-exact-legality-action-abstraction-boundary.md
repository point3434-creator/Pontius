# ADR-0291: Preregister the exact-legality action-abstraction boundary

- Status: accepted executable correctness and reduced-quality preregistration before any new action-abstraction result
- Date: 2026-08-23
- Follows: ADR-0290
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0291
- Front-Door-Contract: ADR-0282
- Front-Door-Revoked: ADR-0281
- Front-Door-Active-Next: Execute the frozen exact-legality lattice, projection, exhaustive-state, reduced river security-value, and charged complete-hand controls once; keep blueprint training, convex-master integration, resolving, and strategy labels closed
- Front-Door-Blockers: the immutable integer sizing source, semantic projection weights, public-state provenance, reduced sizing LP oracle, exhaustive abstraction controls, and charged replay hooks do not yet exist

## Question

Can Pontius replace an intractable interval of exact integer raise amounts with
a small, provenance-bound action lattice while retaining exact legality,
all-ins, explicit off-tree translation, and acceptable reduced-game security
value before any abstraction reaches a convex master or resolver?

## Decision

Build one additive immutable sizing source over `LegalBettingDecision`, one
exact barycentric off-tree projector, and one dependency-free reduced river
sizing oracle. Connect the source only as a charged audit boundary in ADR-0290's
unchanged passive complete-hand trace. The exact betting kernel continues to
apply the original observed or emitted action; projection may describe an
abstract observation but may never rewrite public chip state.

This is a candidate abstraction gate, not selection of a production betting
tree. It opens no trained blueprint, h32 action-width result, convex master,
resolver, strategy-quality label, or deployment claim.

### Frozen integer sizing rule

For the current exact public betting state and its exact current
`LegalBettingDecision`, retain every legal non-raise action literally. If no
raise is legal, the lattice ends there.

When a raise is legal, define:

- `base_raise_to = street_contribution + call_amount`;
- `pot_after_call = public pot + call_amount`; and
- the ordered exact pot fractions `1/3`, `2/3`, `1`, and `3/2`.

For each fraction, multiply `pot_after_call` in exact rational arithmetic,
round the positive increment to the nearest integer with ties upward, and add
it to `base_raise_to`. Also generate three semantic anchors: the exact minimum
legal raise-to, the exact maximum contestable raise-to, and the acting player's
exact all-in raise-to.

Every raw target is explicitly clamped to the exact inclusive legal interval.
The record must name whether it was clipped low, clipped high, or unchanged;
clipping may not be hidden. Deduplicate only after integer projection, retain
every ordered origin as provenance on the surviving amount, sort raises by
exact raise-to, and bind the complete algorithm and fraction list to an
immutable source digest. The minimum and all-in anchors guarantee that every
legal exact raise lies inside the abstract span. There are at most seven unique
raises and at most nine total actions at one decision.

The maximum contestable amount and own all-in remain different semantic
origins even when they coincide numerically. A short all-in-only interval must
collapse to that one exact raise without losing either its minimum/all-in
provenance or its `all_in_only` context. No stack, pot, payoff span, tolerance,
probability, or interpolation weight may substitute for another merely because
the frozen fixture makes two numbers equal.

### Frozen off-tree projection

Fold, check, and call project to themselves with exact unit mass. An abstract
raise also projects to itself. Every other exact legal raise-to `t` is bracketed
by the adjacent abstract raises `l < t < u` and maps to exactly two atoms:

`(l, (u-t)/(u-l))` and `(u, (t-l)/(u-l))`.

Weights use a new reduced rational semantic type distinct from action-policy
probabilities and range weights. They must be nonnegative, sum exactly to one,
and reproduce `t` exactly in chip-coordinate expectation. Ties and Float64 are
absent from this operation. A wrong state, stale decision, illegal action,
partial lattice, missing endpoint, mutable alias, numerical boolean, zero
denominator, or provenance mismatch rejects.

The projector defines an observation interface only. It makes no claim that
linear chip interpolation is strategically exact, and it may not convert a
controlled mixed projection into a randomized emitted bet in this checkpoint.

### Frozen exact-state controls

Run the source and projector across all 45,456 reachable semantic states and
60,732 transitions in the maintained six-seat three-chip exhaustive oracle.
For every active decision:

- the abstract actions are an ordered unique subset of the exact legal actions;
- every exact non-raise action, minimum raise, maximum contestable anchor, and
  own all-in is retained with its semantic origin;
- every exact legal raise projects only to retained legal actions, with exact
  unit mass and exact expected raise-to; and
- applying every retained action through `NoLimitBettingState` succeeds and
  preserves the existing independent pot/settlement invariants.

Add deterministic 100-big-blind and adversarial short-all-in, cumulative
reopening, unequal-stack, clipped-origin, and duplicate-origin cases. Probe
large legal intervals without enumerating them except in the bounded reduced
quality game below.

### Frozen reduced sizing-quality control

Use a dependency-free one-bet, no-raise, heads-up river security-value oracle.
The opener observes one of three actual private hands and chooses check or an
integer bet. The responder observes its own one of three actual hands plus the
bet and chooses fold or call. Exact joint deal probabilities and exact showdown
ranks define the zero-sum chip payoff. The opener's behavioral maximin program
is a compact LP: one simplex row per private-hand action and two responder
envelopes, fold and call, per opponent-hand/bet information set. Reconstruct
its objective and every responder minimum independently after solving.

Use board `2c 7d 9h Js Qc`. Ordered opener hands are `Ks Td`, `As Ad`, and
`4s 5s`; ordered responder hands are `Ts 8s`, `Kh Kd`, and `Ah 3h`. This gives
three strict showdown tiers on each side and nine card-compatible deals. Freeze
four exact joint-weight matrices, in that order by row and column:

1. pot 10, stack 20, weights all `1/9`;
2. pot 20, stack 20, integer weights
   `((1,2,1),(2,1,2),(1,2,1))/13`;
3. pot 6, stack 20, integer weights
   `((4,1,1),(1,3,1),(1,1,2))/15`; and
4. pot 12, stack 12, integer weights
   `((1,1,1),(1,2,1),(3,2,1))/13`.

The exact minimum bet is two chips. For each context compare:

- the full action universe containing check and every integer bet from two
  through the stack;
- ADR-0291's fixed lattice generated from a validated two-live-seat six-seat
  river opening state with the same pot and stack; and
- a deliberately narrow control containing only the minimum and all-in bets.

The full, candidate, and narrow LPs use identical cards, weights, payoff units,
and solver contract. `payoff_span = pot + 2*stack` is derived once from the
reduced game and is used only for the dimensionless loss report. Probability-
simplex residual and chip-objective reconstruction error use nominally distinct
allowance types. On bounded two-hand/two-bet projections, compare the compact
LP with the independent complete normal-form matrix oracle within `1e-9` chips.

The quality gate passes only if:

- every LP has probability residual at most `1e-9`, chip-objective
  reconstruction error at most `1e-9`, and verified monotonic ordering
  `full >= candidate >= narrow` within `1e-9` chips;
- at least two contexts have a nondegenerate full-over-narrow value gap larger
  than `1e-6 * payoff_span`;
- across positive-gap contexts the candidate recovers at least 80% of the
  aggregate full-over-narrow security-value gain;
- maximum `(full-candidate)/payoff_span` is at most 1% and its four-context
  mean is at most 0.5%; and
- the candidate uses at most nine total actions and strictly fewer than half
  the full actions in every context with stack 20.

These are reduced one-street security values, not NashConv, multiplayer safety,
full-game strength, or evidence that the fraction list is optimal. A clean
quality failure rejects this lattice rather than permitting post-outcome size,
context, threshold, rounding, or interpolation changes.

### Frozen complete-hand trace

Reuse ADR-0289 fixture A literally with both the accepted full-width policy and
belief active. Build one abstraction for every one of its 24 public decisions.
Project each of the same 20 opponent call/check observations before applying the
unchanged exact action. Require all four controlled passive candidates and
their deterministic fallbacks to appear literally in their current lattice.

Each abstraction build and opponent projection is agent work and owns one named
charged interval in the cumulative 15-second street ledger. Source construction
is immutable pre-hand preparation. The trace must retain the exact cards,
action order, 20 belief updates, four candidate actions, four street ledgers,
12-chip pot, seat-3 payout, and post-terminal verification boundary from
ADR-0290.

## Gates

The checkpoint passes only if all sizing, provenance, exhaustive-state,
projection, reduced-quality, replay, timing, documentation, and preservation
gates above pass unchanged. The complete repository suite, changed-file Ruff,
Python 3.11 parse, generated front door, documentation integrity, whitespace,
and byte preservation of every untouched ADR-0290 file must also pass.

## Kill criterion

Any illegal or missing endpoint, hidden clip, origin loss, mutable/stale
context, interpolation mismatch, semantic-unit cross-wire, exhaustive betting
failure, reduced-quality gate failure, replay drift, or street-wall breach
rejects the candidate lattice. On rejection retain ADR-0290's exact integer
kernel, full-width symbolic belief, rational reference policy, and passive
complete-hand loop. Do not rescue the result by changing fractions, rounding,
contexts, gates, or units after inspection.

## Claims boundary

A pass would establish only a legal, bounded, provenance-complete candidate
action lattice and exact off-tree observation projection, plus narrow reduced
evidence that its bet sizes retain security value. It would not establish a
trained blueprint, chosen production abstraction, strategically exact
translation, calibrated ranges, normalized full-width marginals, scalable
value contraction, action width through the convex master, resolving, safety,
exploitability, NashConv improvement, AIVAT, league strength, optimized
latency, live dealing, or a complete C5 bot. No revoked experiment or external
publication is authorized.
