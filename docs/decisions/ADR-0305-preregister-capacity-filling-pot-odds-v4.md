# ADR-0305: Preregister capacity-filling pot-odds v4

- Status: accepted prospective mechanism and replicated fresh-panel preregistration before v4 source code, structure construction, or values
- Date: 2026-08-23
- Follows: ADR-0304
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0305
- Front-Door-Contract: ADR-0282
- Front-Door-Revoked: ADR-0281
- Front-Door-Active-Next: Implement only the exact-rational capacity-filling pot-odds v4 source below, prove exhaustive legality, v3 action-set inclusion, full available-slot use, bounded construction work, projection, provenance, and immutability, then commit its source digest before constructing any of the three already-seeded fresh structures or opening any value; keep every parked candidate and all replay, blueprint, convex-master, resolver, and strategy integration closed
- Front-Door-Blockers: the v4 source and digest do not exist; all three frozen v4 seed streams remain unconstructed; both candidate-blind qualification replications and every v4 value remain unopened; no action abstraction has passed reduced quality and power gates; integration remains unauthorized

## Question

Can one materially different, value-independent mechanism recover the sizing
gain missed by collision-repair v3 while retaining every v3 action and the
same worst-case seven-raise ceiling?

## Post-outcome disclosure

ADR-0304 is development evidence for this mechanism choice. It shows that v3
passes small payoff-span-normalized loss gates but recovers only 80.05% of the
available raw-chip gain on its qualified panel. No additional subset value,
per-context best size, strategy, dual selector, or candidate diagnostic has
been opened after that result. The new mechanism responds only to a structural
fact visible in v3's source and provenance: clipping and deduplication can
leave part of its already-authorized seven-raise capacity unused.

The ADR-0301 representative and qualified structures and every earlier opened
panel are development-only. None may confirm v4. V4 must use the wholly fresh
streams and replicated candidate-blind protocol below.

## Mechanism

Define **capacity-filling pot-odds v4** as an immutable exact-legal successor
whose initial distinct raise-to set is exactly collision-repair v3's set. It
never removes or changes a v3 action. It adds no learned, card, range, value,
street-table, or result-dependent input.

Freeze algorithm version
`exact-rational-capacity-filling-pot-odds-v4` and source id
`adr-0305-capacity-filling-pot-odds-v4`.

For one exact legal decision with a raise interval, define:

```text
base_raise_to = acting street contribution + exact call amount
pot_after_call = current pot + exact call amount
increment(r) = r - base_raise_to
pot_odds(r) = increment(r) / (pot_after_call + 2 * increment(r))
target_raise_count = min(7, number of exact legal integer raise-to amounts)
```

All arithmetic in construction and provenance is exact integer/rational
arithmetic. V3 retains the legal minimum and acting-seat all-in, so every
unretained exact integer raise lies strictly between two retained raise-to
amounts. While fewer than `target_raise_count` distinct raises are retained:

1. For every adjacent retained pair `left < right` containing at least one
   unretained integer, find the legal integer `r` that maximizes
   `min(pot_odds(r) - pot_odds(left), pot_odds(right) - pot_odds(r))`.
2. Obtain that discrete maximizer without enumerating the integer interval.
   Let `q` be the exact midpoint of the two endpoint pot-odds values and invert
   `q = d / (pot_after_call + 2*d)`. Evaluate only the legal floor and ceiling
   raise-to integers around `base_raise_to + pot_after_call*q/(1 - 2*q)`,
   clipped to the open interval.
3. Select the interval candidate with the greatest exact rational nearest-
   neighbor distance. Break every exact tie by the smaller raise-to amount.
4. Retain it with refill rank, bracketing raise-to amounts, exact score, and
   parent-v3 source identity in canonical provenance, then repeat.

The midpoint inversion is only a bounded candidate derivation; floats and a
scan over all legal integers are forbidden. Since the exact legal minimum and
maximum are retained, the loop must reach the target unless the exact raise
range itself is smaller. Construction work is bounded by the fixed width, not
chip depth.

Before any repository source implementation, an independent exact-rational
stdin diagnostic compared the floor/ceiling construction with exhaustive
integer maximization across 2,418,000 synthetic positive-pot gaps spanning
pots 1 through 100 and multiple base/endpoint geometries. Every selected
integer and smaller-raise tie matched. This checks the discrete midpoint
lemma only; it is not source, poker-quality, runtime, or panel evidence.

Retain all exact legal non-raise actions and the existing adjacent exact
barycentric off-tree projector. Canonical action order remains non-raises then
increasing raise-to. At most seven distinct raises and nine total actions may
survive. The source digest must bind this algorithm version, the immutable v3
parent digest, coordinate formula, inverse, exact tie rule, refill provenance,
width ceilings, anchors, and projection rule.

This is a new mechanism rather than a fitted fraction: it converts unused
bounded capacity into greedy maximin coverage in a fixed responder pot-odds
coordinate. It neither alters v3 nor widens v3's preregistered worst-case
ceiling. V1, v2, and v3 remain parked as standalone candidates.

## Frozen fresh streams

The exact ASCII seed texts are committed now, before source implementation:

```text
pontius:adr-0305:capacity-filling-pot-odds-v4:representative:sha256-stream:v1
pontius:adr-0305:capacity-filling-pot-odds-v4:qualified-a:sha256-stream:v1
pontius:adr-0305:capacity-filling-pot-odds-v4:qualified-b:sha256-stream:v1
```

After the source passes and its digest is committed, use the ADR-0301 exact
SHA-256 stream semantics, four-by-four private widths, card construction, chip
sets, exact joint-weight construction, structural filter, and value-free
records under generator version
`fresh-capacity-filling-pot-odds-v4-structure-v1` to construct:

- the first 48 admissible representative contexts;
- a separate first 96-context qualified-A pool; and
- a separate first 96-context qualified-B pool.

Commit all three complete structure identities and candidate-attempt counts
before any qualification value. Require unique semantic contexts within and
across the three structures and no semantic counterpart in the maintained
finite inventory of ADR-0291 through ADR-0304 contexts. Any collision rejects
the construction; do not skip, reseed, or enlarge a stream after seeing it.

Structural modules may not import the reduced oracle, v1-v4 candidates,
replay, blueprint, convex master, resolver, or strategy code.

## Replicated candidate-blind qualification

Only after the structural commit, open qualified A and then qualified B through
one owned full-integer-versus-minimum/all-in runner that imports no action
candidate. Reuse ADR-0300's exact reduced solver, distinct numerical units,
4,096-pivot cap, derived `pot + 2*stack` payoff span, normalized `1e-4`
opportunity floor, and `1e-8`-chip ambiguity guard.

For each pool retain the first 24 qualifying contexts and stop immediately.
Any ambiguity, numerical failure, pivot failure, semantic binding drift, or
fewer than 24 qualifiers in 96 contexts rejects qualification. If A rejects,
B values remain unopened. If both pass, commit both exact selected panels,
prefixes, result digests, and leading-two-by-two teacher controls before the
first representative, v3, or v4 evaluation value. Qualification opens no
representative value and no candidate value.

## Frozen candidate evaluation

Only after the final panel commit, execute one ordered campaign:

1. all 48 representative contexts;
2. the exact 24 qualified-A contexts; and
3. the exact 24 qualified-B contexts.

Never open a later family after an earlier failure. On every context solve the
identical game under four nested arms:

1. full integer check plus every exact bet from two through the stack;
2. capacity-filling pot-odds v4's exact retained bets;
3. collision-repair v3's exact retained bets; and
4. check plus minimum/all-in.

Use solver tolerance `1e-11`, distinct `1e-9` dimensionless probability,
`1e-9`-chip objective, `1e-9`-chip LP-duality, and `1e-9`-chip envelope
allowances, and a 4,096 simplex-pivot cap per compact LP. Require exact
source/panel binding, all exact teacher controls from ADR-0300, seven v4 raises
whenever the exact arm offers at least seven, no more than nine total actions,
strict width reduction from the full arm, and
`full >= v4 >= v3 >= minimum/all-in` within the distinct `1e-9`-chip ordering
allowance.

V4 passes only if every numerical, semantic, width, ordering, and teacher
conjunct holds and:

- representative maximum normalized full-v4 loss is at most `0.005` and mean
  is at most `0.001`;
- qualified A separately has maximum loss at most `0.005`, mean at most
  `0.001`, and raw-chip aggregate recovery at least `0.90`; and
- qualified B separately has maximum loss at most `0.005`, mean at most
  `0.001`, and raw-chip aggregate recovery at least `0.90`.

Each recovery is exactly
`sum(v4 - minimum/all-in) / sum(full - minimum/all-in)` over that sealed panel.
Do not pool replications, average per-context ratios, substitute payoff-span-
normalized loss, or waive one family with another. V3 is a nested attribution
control only and has no independent promotion gate.

Record deterministic family and campaign digests plus exact work. A serial
wall-time observation is local offline campaign cost only, never per-solve,
per-iteration, real-game, or 15-second street latency.

## Commit order

1. This mechanism, seeds, panels, evaluation, gates, and kill criteria.
2. Exact v4 source, exhaustive/focused tests, and immutable source digest.
3. Three value-free structures, identities, disjointness, and tests.
4. Owned replicated candidate-blind qualification and both final panel
   identities, with no candidate import.
5. Representative-first candidate evaluator and the stopped outcome.

No later boundary may silently combine these phases.

## Decision

Proceed only to v4 source implementation and source-gate verification. Do not
construct a frozen stream, open a solver value, or modify a parked candidate.
The source must implement the exact mechanism above, preserve every v3 action,
fill every available slot through exact bounded interval candidates, and commit
its immutable digest in a successor ADR. Only that clean source boundary may
authorize construction from the already-frozen seeds.

## Source gate

Before any structure construction, the source must pass exhaustive traversal
of all 45,456 reachable six-player three-chip betting states and 60,732 legal
transitions across every button. Check exact legality, canonical ordering,
mandatory anchors, v3 action-set inclusion, exact target-width filling,
projection of every exact legal action, provenance, immutability, and the
seven-raise/nine-action ceilings.

Add focused checks for unequal stacks, clipped/deduplicated parents, cumulative
short-all-in reopening, closed raising, one-slot and multi-slot refill,
pot-odds midpoint/tie arithmetic, stale decisions, full small intervals, and
million/billion-chip intervals that must not be enumerated. Statically exclude
cards, ranges, values, panels, replay, blueprint, convex-master, resolver, and
strategy hooks.

## Kill criterion

Source code or constructed seed output before this ADR; any changed seed;
float-based or full-interval refill search; missing v3 action; illegal,
noncanonical, underfilled, over-width, mutable, nondeterministic, or value-
dependent source state; incomplete refill provenance; source drift after its
digest commit; structure construction before the source commit; structure
collision, skip, reseed, or enlargement; value before its structural/panel
commit; candidate access during qualification; opening B after A rejects;
ambiguity or insufficient yield; opening a later evaluation family after an
earlier failure; numerical, pivot, teacher, ordering, width, normalized-loss,
or either separate recovery failure; threshold relaxation; post-outcome source
or panel change; or any integration attempt rejects the checkpoint.

## Successor authority

A pass makes one separately preregistered passive reference-hand compatibility
and width-through-convex-master audit eligible. It does not itself connect v4
to replay, blueprint, resolving, or live selection. A failure parks v4 and does
not authorize a source edit, wider ceiling, new panel, or relaxed gate.

## Claims boundary

A pass would establish only a same-ceiling bounded exact-legal one-bet sizing
candidate on three fresh reduced development families. It would not establish
strategically exact translation, production range width, earlier-street
quality, multiplayer safety, runtime decision quality, optimized latency,
action width through the convex master, replay compatibility, a trained
blueprint, resolver strength, NashConv, AIVAT, league strength, C5 completion,
or a complete bot. No revoked experiment, external publication, or thesis
change is authorized.
