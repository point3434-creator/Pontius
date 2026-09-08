# ADR-0300: Preregister collision-repair v3 and fresh dual panels

- Status: accepted executable mechanism and evaluation preregistration before v3 source implementation or fresh panel construction
- Date: 2026-08-23
- Follows: ADR-0299
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0300
- Front-Door-Contract: ADR-0282
- Front-Door-Revoked: ADR-0281
- Front-Door-Active-Next: Implement and exhaustively validate exactly the collision-repair v3 legal source, then commit its source digest and exact fresh representative/qualified seed texts before constructing either panel; keep every opened panel and all replay, blueprint, convex-master, resolver, and strategy integration closed
- Front-Door-Blockers: the v3 source and digest do not exist, fresh seed texts and panels are not sealed, no v3 value exists, and integration remains unauthorized

## Question

Can a bounded exact-legal lattice recover most full-integer one-bet value on
both representative and materially sizing-informative fresh games by repairing
v2's clipped/deduplicated overbet slot without widening its worst-case action
ceiling?

## Decision

Freeze exactly one mechanism, collision-repair v3, before implementing its
source. It is derived only from v2's recorded mechanism and the exact legality
and provenance rules. No ADR-0297 pool, observation, qualifying index, policy,
or value may influence the source.

For every exact legal raise decision define:

```text
base_raise_to = acting street contribution + exact call amount
pot_after_call = current pot + exact call amount
```

Round every exact rational increment to integer chips by nearest with ties up,
then clip to the exact legal raise-to interval. Retain the mandatory minimum,
maximum-contestable, and acting-seat all-in anchors. Retain fixed pot-fraction
origins `1/4`, `1/2`, and `1`.

For the final adaptive origin, first construct the `2 * pot_after_call` raw
target. If its clipped raise-to is distinct from all three mandatory anchor
raise-to amounts, retain fraction `2`. If it coincides with any mandatory
anchor, instead construct and retain fraction `3/2`. Clip and deduplicate that
fallback normally. Bind the chosen fraction and collision decision in exact
provenance.

This rule never removes a v2 action: when v2's two-pot action is distinct, v3
retains it; when it collides with an anchor, that exact action remains through
the anchor and v3 may add the three-halves target. Together with identical
`1/4`, `1/2`, and `1` origins and mandatory anchors, v2's exact action set must
be a subset of v3's at every legal public decision.

Retain all exact legal non-raise actions and the existing adjacent exact
barycentric off-tree projection. The source is immutable and digest-bound. At
most seven distinct raises and nine total actions may survive. No learned
parameter, card/range input, street-specific table, or result-dependent branch
is permitted.

## Source gate before panels

Commit this ADR before source implementation. The implementation must then:

- pass exhaustive traversal of all reachable six-player three-chip betting
  states across every button, checking exact legality, canonical ordering,
  mandatory anchors, v2 action-set inclusion, projection of every exact legal
  action, and the seven-raise/nine-action ceilings;
- pass focused unequal-stack, clipping, cumulative-short-all-in reopening,
  primary-two-pot, fallback-three-halves, deduplication, provenance, stale-
  decision, and immutable-source controls; and
- expose no replay, blueprint, convex-master, resolver, or strategy hook.

After those tests, record the immutable source SHA-256 and commit source plus
tests in a successor ADR. Only that successor may freeze exact fresh seeds.
No panel may be constructed before the source/digest/seed commit.

## Fresh dual-panel construction

After the source freeze, construct two disjoint four-by-four families with new
SHA-256 streams and the ADR-0297 card, chip, exact-weight, width, and structural
filter semantics:

1. **Representative:** the first 48 structurally admissible contexts, without
   opening any full, narrow, or candidate value and without qualification.
2. **Qualified:** a separate 96-context structural pool. Open only full-integer
   and minimum/all-in values through a candidate-blind owned runner, using
   ADR-0297's exact solver, numerical, pivot, normalized `1e-4` opportunity,
   and `1e-8`-chip ambiguity contracts. Retain the first 24 qualifiers and stop
   immediately. Any ambiguity or fewer than 24 qualifiers rejects before v3.

The successor ADR must freeze exact seed text, generator versions, pool and
panel identities, candidate-blind result digest, and disjointness evidence.
Commit both panel identities before the first v3 value. The representative and
qualified panels may not reuse any semantic context from ADR-0291 through
ADR-0299.

## Frozen v3 evaluation

Only after the panel commit, one campaign may process representative first and
qualified second. For every context solve the identical game under:

1. full integer check plus every bet from two through the stack;
2. collision-repair v3's exact retained bet sizes; and
3. check plus minimum/all-in.

Use solver tolerance `1e-11`, the distinct `1e-9` dimensionless probability,
`1e-9`-chip objective, `1e-9`-chip LP-duality, and `1e-9`-chip envelope
allowances, and a 4,096 simplex-pivot cap per compact LP. Require
`full >= v3 >= narrow` within `1e-9` chips, exact source/panel binding, and at
most seven v3 bets and nine total legal actions. V3 must remain a strict action-
width reduction from the full arm whenever the full arm has more actions.

On every representative and qualified context, compare the leading two-by-two
minimum/all-in compact oracle against the bounded normal-form teacher within
`1e-9` chips and require teacher duality gap at most `1e-9` chips.

The candidate passes only if all conjuncts hold:

- representative maximum normalized full-v3 loss at most `0.005` and mean at
  most `0.001`;
- qualified maximum normalized full-v3 loss at most `0.005` and mean at most
  `0.001`; and
- aggregate qualified recovery
  `sum(v3 - narrow) / sum(full - narrow)` at least `0.90`.

All normalized losses divide by the context's derived
`payoff_span = pot + 2*stack`; no stack surrogate is permitted. Aggregate
recovery uses exact panel membership and raw chip gaps, not a mean of ratios.
An ambiguity, numerical failure, width failure, or any failed quality conjunct
rejects v3 and stops before integration.

Record deterministic digests and exact work. One serial wall-time observation
may be reported only as local per-campaign diagnostic cost, not per-solve,
per-iteration, real-game, or 15-second street latency.

## Successor authority

A pass makes a separately preregistered passive reference-hand compatibility
audit eligible. It does not itself connect v3 anywhere. A failure parks v3 and
does not authorize fraction changes, a new panel, or a wider candidate.

## Gates

At every commit boundary run changed-file Ruff, Python 3.11 parse, generated
front door, documentation integrity, staged whitespace, relevant focused
tests, preservation of all earlier digests, and the complete repository suite.
The preregistration, source/seed freeze, and panel freeze must each precede the
next evidence-opening phase.

## Kill criterion

Any source code before this preregistration commit; access to an ADR-0297 value
or selected context while implementing v3; failure of v2 action-set inclusion;
illegal, missing-anchor, over-width, mutable, or nondeterministic source state;
panel construction before source/seed commit; panel collision or drift;
candidate access during qualification; v3 value before panel commit; ambiguity;
insufficient qualified yield; numerical, pivot, teacher, monotonicity, width,
or quality failure; threshold relaxation; post-outcome source or panel change;
or integration attempt rejects the checkpoint.

## Claims boundary

A pass would establish only a bounded exact-legal one-bet sizing candidate on
two fresh reduced development families. It would not establish strategically
exact translation, production ranges, earlier-street quality, multiplayer
safety, real-time decision quality, optimized latency, action width through the
convex master, replay compatibility, blueprint or resolver strength, NashConv,
AIVAT, league strength, C5 completion, or a complete bot. No revoked
experiment, external publication, or thesis change is authorized.
