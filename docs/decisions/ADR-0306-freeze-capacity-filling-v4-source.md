# ADR-0306: Freeze capacity-filling v4 source

- Status: accepted value-free source gate; v4 source is frozen before every seeded structure and value
- Date: 2026-08-23
- Follows: ADR-0305
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0306
- Front-Door-Contract: ADR-0282
- Front-Door-Revoked: ADR-0281
- Front-Door-Active-Next: Construct only ADR-0305's value-free 48-context representative, 96-context qualified-A, and 96-context qualified-B streams from their exact frozen seeds; commit all three identities, attempt counts, within/across-family uniqueness, and zero-counterpart checks before importing a sizing candidate or opening any qualification value
- Front-Door-Blockers: all three v4 structures remain unconstructed; both candidate-blind qualification replications and every representative, v3-control, and v4 value remain unopened; v4 has not passed sizing quality or power; replay, blueprint, convex-master, resolver, and strategy integration remain unauthorized

## Verdict

Accept and freeze the exact-rational capacity-filling pot-odds v4 source at
SHA-256
`37824e44b7793b10b081957fc8be387bdca5c565b4bfe2386ca13f7e1c785c8b`.
The source passes ADR-0305's value-free legality, inclusion, capacity, bounded-
work, projection, provenance, immutability, and dependency gates. This commits
only the mechanism bytes. No frozen stream has been constructed and no solver
value has been opened.

## Frozen source

The implementation is `pontius.capacity_filling_action_abstraction` with:

- algorithm version `exact-rational-capacity-filling-pot-odds-v4`;
- source id `adr-0305-capacity-filling-pot-odds-v4`;
- immutable collision-repair v3 parent SHA-256
  `ebae17f69c4f37377edf0fb0c55a99049c8688c8517dcbc525230d8e418a811a`;
- at most seven raises and nine total actions; and
- source SHA-256
  `37824e44b7793b10b081957fc8be387bdca5c565b4bfe2386ca13f7e1c785c8b`.

Canonical source bytes bind the parent identity, exact minimum and acting-seat
all-in anchors, every exact parent non-raise, v3 action-set inclusion, target
width, pot-odds coordinate, midpoint inversion, floor/ceiling-only candidates,
smaller-raise tie break, refill provenance, width ceilings, and the unchanged
exact barycentric projector. The source id is exact rather than a caller label.

For each decision, the constructor first rebuilds the digest-bound v3 parent.
It then greedily fills to the lesser of seven raises and the complete legal
integer raise count. Each refill stores a contiguous rank, its exact adjacent
bracket, selected raise-to, and reduced rational nearest-neighbor distance.
The generic legality object independently reconstructs that ordered chain and
rejects a changed rank, bracket, score, selected integer, missing slot, illegal
action, changed parent provenance, or over-width result. The v4 wrapper also
rebuilds v3 and checks literal action-set inclusion and unchanged inherited
origins.

## Verification

The maintained exhaustive traversal covers all 45,456 reachable six-player
three-chip betting states across every button, including 22,920 active
decisions and 60,732 exact legal transitions. At every active decision it
checks v3 action-set inclusion, exact target-width filling, legal retained
actions, seven-raise/nine-action ceilings, exact action counts, and projection
of every legal integer action through the v4 source.

Focused tests cover distinct and collided v3 parents, one- and multi-slot
refill, full small intervals, short all-ins, closed raising, unequal stacks,
cumulative short-all-in reopening, exact tie direction, barycentric
projection, stale and malformed inputs, provenance mutation, and immutable
source identity. A billion-chip state returns seven raises without interval
enumeration. Static source inspection excludes `range` and `float` from the
midpoint selector and excludes card, range, value, panel, replay, blueprint,
convex-master, resolver, and strategy dependencies from the v4 module.

Two independent spot checks supplement those maintained tests:

- ADR-0305's pre-source exact-rational diagnostic matched exhaustive discrete
  maximization over 2,418,000 synthetic gaps; and
- a post-source stdin oracle exhaustively compared every sequential refill on
  5,000 even-pot river geometries with pots 2 through 100 and stacks 2 through
  101, then built a `10^100`-chip interval. Every selected integer, bracket,
  exact score, final set, and tie matched.

These are bounded verification exercises, not certification of the source or
evidence of poker quality, production latency, or full-game behavior.
The complete repository regression boundary passes 1,160 tests with two
intentional environment-dependent skips.

## Mathematical check

For fixed positive `P = pot_after_call`, the coordinate
`q(d) = d / (P + 2d)` is strictly increasing for positive raise increment
`d` and remains below one half. Within an adjacent retained interval, the
minimum of the left and right coordinate distances is maximized at the
coordinate midpoint in the continuous relaxation. The exact inverse
`d = Pq / (1 - 2q)` is therefore finite and unique. Monotonicity makes the two
adjacent integers around that inverse sufficient for the discrete maximum;
exact rational comparison and the frozen smaller-raise tie rule select the
unique canonical result. The outer loop examines at most six retained gaps
for at most five additions, so construction work is bounded by the fixed
action ceiling rather than chip depth.

## Decision

Freeze the source and proceed only to the three value-free structure builds in
ADR-0305's order. The structural module must retain the exact frozen seeds and
generator semantics, import no sizing candidate or value owner, and commit all
identities and disjointness results before qualification. Do not edit this
source, construct a replacement seed, inspect a value, connect v4 to the
reference hand, or treat this source pass as action-abstraction acceptance.

## Evidence classification

- **Known:** canonical source bytes, source and parent identities, exact
  mechanism, ceilings, provenance schema, and maintained test scope.
- **Reproduced:** source digest, exhaustive three-chip state/edge counts,
  representative exact sizes, bounded huge-interval construction, midpoint
  selections, and fail-closed mutations.
- **Unopened:** all three ADR-0305 structures; both qualification replications;
  every representative, candidate, and control value; and every integration
  path.
- **Hypothesis:** spending v3's unused capacity by value-independent pot-odds
  coverage will pass both fresh qualified recovery replications.

## Claims boundary

This decision establishes only a deterministic, bounded, exact-legal v4 source
that preserves v3 and fills its already-authorized width. It establishes no
sizing quality, strategically exact translation, production range width,
earlier-street quality, multiplayer safety, runtime decision quality,
15-second feasibility, action width through the convex master, replay
compatibility, trained blueprint, resolver strength, NashConv, AIVAT, league
strength, C5 completion, or complete bot. No revoked experiment, external
publication, or thesis change is authorized.
