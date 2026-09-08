# ADR-0293: Preregister the dyadic pot-odds confirmation successor

- Status: accepted executable development/confirmation preregistration before any v2 source value or confirmation-panel construction
- Date: 2026-08-23
- Follows: ADR-0292
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0293
- Front-Door-Contract: ADR-0282
- Front-Door-Revoked: ADR-0281
- Front-Door-Active-Next: Execute the frozen dyadic development control and deterministic untouched 24-context confirmation panel once; integrate charged replay audit hooks only if every quality gate passes, and keep blueprint training, convex-master integration, resolving, and strategy labels closed
- Front-Door-Blockers: the confirmation generator and panel do not exist, v2 has not been evaluated even on development, and no charged action-abstraction replay hook exists

## Question

Can one principled replacement for ADR-0292's rejected fixed sizing rule retain
its exact legality and bounded width while recovering reduced sizing security
value on a confirmation panel that did not exist when the replacement was
chosen?

## Decision

Freeze exactly one v2 hypothesis: retain the complete ADR-0291 integer sizing,
rounding, clipping, deduplication, anchor, provenance, and barycentric
projection contracts, but replace the four fractions `(1/3, 2/3, 1, 3/2)`
with `(1/4, 1/2, 1, 2)`. The immutable source id is
`adr-0293-dyadic-pot-odds-v2`.

This is not an isolated addition of the three-chip bet exposed by ADR-0292.
The entire internal ladder changes before any v2 value is observed. Its
mechanism rationale is responder pot-odds coverage: bets of one quarter, one
half, one, and two pots span break-even call-equity coordinates
`1/6`, `1/4`, `1/3`, and `2/5` in the one-bet game. Exact minimum,
maximum-contestable, and own-all-in anchors remain mandatory. At most seven
unique raises and nine total actions remain available at a public decision.

No alternative fraction family, learned sizing proposal, development sweep,
or post-outcome substitution is part of this invocation.

## Open development control

ADR-0291's four contexts are already open and may only diagnose whether v2
implements its intended mechanism. Run full integer, v2, v1, and
minimum/all-in arms with the unchanged exact cards, probabilities, chip
payoffs, solver, and allowances. Before constructing confirmation, require:

- all numerical, monotonicity, width, and bounded normal-form controls from
  ADR-0291;
- v2 aggregate recovery of at least `80%` of the opened positive
  full-over-minimum/all-in gap; and
- v2 maximum and mean normalized full loss no worse than ADR-0291's `1%` and
  `0.5%` ceilings.

A pass is development fit only. It cannot validate v2 or change any frozen
confirmation rule below. A failure stops the invocation before confirmation.

## Untouched confirmation construction

The confirmation panel does not exist at preregistration time. Construct it
only after the development control passes, with no manual additions,
rejections, or ordering changes beyond this algorithm.

### Exact digest stream

The seed text is exactly:

```text
pontius|adr-0293|confirmation-panel-v1|baseline=4156ce6febe350fa153a3ee32c5130ada897b8a3
```

Encode it as ASCII. Stream blocks are
`SHA-256(seed_bytes || counter.to_bytes(8, "big"))` for counters beginning at
zero. Consume each block as four consecutive unsigned big-endian 64-bit
integers. `randbelow(n)` rejects a draw `x` at or above
`2^64 - (2^64 mod n)` and otherwise returns `x mod n`. Rejected draws still
consume stream position. Numerical booleans and nonpositive bounds reject.

### Context generation

For each candidate, Fisher-Yates shuffle the canonical integer deck `0..51`,
iterating `i=51..1` and swapping with `randbelow(i+1)`. Take the first five
cards as the ordered board, the next six as three ordered opener pairs, and the
next six as three ordered responder pairs; canonicalize each private pair.

Compute the actual `3 x 3` showdown sign matrix. Reject the card candidate if
any deal ties, if the matrix does not contain both wins and losses, if it has
fewer than two distinct rows, or if it has fewer than two distinct columns.
A rejected card candidate consumes its complete shuffle and no chip/weight
draws. This structural rule is frozen before cards exist and does not inspect
any action-size value.

For each accepted card candidate, draw the pot from
`(6, 8, 10, 12, 14, 16, 20, 24, 30, 40)` and the effective stack from
`(10, 12, 16, 20, 24, 30)`, each by one `randbelow` index. Draw nine integer
joint weights as `1 + randbelow(9)`, in row-major order, and normalize them by
their exact integer sum. The exact minimum bet is two. Name accepted contexts
`adr0293-confirmation-00` through `adr0293-confirmation-23` and stop after 24.

Bind the seed, generator version, every card integer, chip field, exact weight,
and ordered context id to canonical JSON and a panel SHA-256. The first code
execution may reveal and record that digest; it may not alter the panel.

## Frozen confirmation arms

For every accepted context compare identical reduced games under:

1. full integer check plus every bet from two through the stack;
2. v2's dyadic lattice;
3. ADR-0292's parked v1 lattice; and
4. check plus minimum/all-in only.

Use the existing distinct `ProbabilitySimplexAllowance(1e-9)` and
`ChipObjectiveAllowance(1e-9)`. Reconstruct every compact LP objective from its
behavioral policy and responder minima. On the leading two-by-two hand
projection of every context, compare the compact minimum/all-in LP against the
independent complete normal-form teacher within `1e-9` chips.

The confirmation gate passes only if:

- every LP has probability-simplex residual and chip-objective reconstruction
  error at most `1e-9`, and every normal-form comparison and duality gap is at
  most `1e-9` chips;
- `full >= v2 >= minimum/all-in` holds within `1e-9` chips in every context;
- at least eight contexts have a positive full-over-minimum/all-in gap larger
  than `1e-6 * payoff_span`;
- across those informative contexts v2 recovers at least `80%` of the aggregate
  full-over-minimum/all-in gain;
- maximum `(full-v2)/payoff_span` is at most `1%`, and its 24-context mean is at
  most `0.5%`;
- v2's aggregate normalized full loss is no greater than v1's aggregate
  normalized full loss within `1e-9`; and
- v2 has at most nine total actions and strictly fewer actions than the full
  integer arm in every context.

All aggregates use only contexts named by the frozen rule. A low-powered panel,
v1 tie, or small absolute loss does not waive a failed conjunctive gate.

## Conditional complete-hand audit

Only after every confirmation gate passes, connect the accepted v2 source as a
charged audit boundary in ADR-0290 fixture A. Build one abstraction for all 24
public decisions and project the same 20 opponent check/call observations.
Source construction is immutable pre-hand preparation. Each build and
projection owns one named charged interval in the cumulative 15-second street
ledger.

Projection remains descriptive: apply the original exact observed action to
the betting kernel and the original action to the rational belief update. Each
of the four controlled passive candidates and fallbacks must be literal v2
actions. Exact cards, action order, belief updates, pot, payout, four street
ledgers, and post-terminal boundary must otherwise match ADR-0290.

## Gates

The checkpoint passes only if development, untouched confirmation, exact
legality/provenance, numerical-unit, width, conditional replay, timing,
documentation, and preservation gates all pass unchanged. Run the complete
repository suite, changed-file Ruff, Python 3.11 parse, generated front door,
documentation integrity, whitespace, and baseline preservation controls.

## Kill criterion

Any development failure stops before panel construction. Any generator drift,
manual panel intervention, numerical or semantic cross-wire, insufficient
confirmation power, quality failure, replay drift, illegal action, or street-
wall breach rejects v2. Do not change fractions, seed, generator, filters,
context count, arms, thresholds, or units after any result. A rejected v2 joins
v1 as a parked control; ADR-0290 remains the emitted reference fallback.

## Claims boundary

A pass would establish only a second bounded exact-legal candidate lattice,
untouched reduced one-street confirmation evidence, and charged passive replay
compatibility. It would not prove optimal sizing, strategically exact
translation, full-game or multiplayer safety, a trained blueprint, scalable
contraction, action width through the convex master, resolving, NashConv,
AIVAT, league strength, optimized latency, live dealing, or complete C5. No
revoked experiment, external publication, or thesis change is authorized.
