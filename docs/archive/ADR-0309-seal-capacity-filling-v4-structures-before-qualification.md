# ADR-0309: Seal capacity-filling v4 structures before qualification

- Status: accepted value-free structural freeze; every v4 qualification and candidate value remains unopened
- Date: 2026-08-23
- Follows: ADR-0308
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0309
- Front-Door-Contract: ADR-0307
- Front-Door-Revoked: ADR-0281
- Front-Door-Active-Next: Implement a separate candidate-blind owned qualification runner over only the sealed qualified-A pool, stop at its twenty-fourth qualifier, first ambiguity, numerical failure, or exhaustion, and open qualified B only after A passes; keep the representative family and every v3/v4 candidate value unopened until both final panel identities are committed
- Front-Door-Blockers: neither candidate-blind qualification replication has opened a value; no 24-context qualified-A or qualified-B panel exists; every representative, v3-control, and v4 value remains unopened; v4 has no sizing-quality, replay, convex-master, resolver, blueprint, or strength result

## Decision

Accept and seal ADR-0305's three value-free capacity-filling v4 structures.
They reconstruct from the exact frozen ASCII seeds in the required
representative, qualified-A, qualified-B order; satisfy the inherited width-
four card, chip, exact-range, and sign-filter contract; are unique within and
across families; and have no semantic counterpart in the finite maintained
ADR-0291 through ADR-0304 context inventory.

This checkpoint opened no sizing-oracle, qualification, representative, v3,
or v4 value. The frozen capacity-filling candidate source is unchanged.

## Sealed structures

| Family | Contexts | Raw card candidates | Structure SHA-256 |
|---|---:|---:|---|
| Representative | 48 | 239 | `6ab4f7451b008a3a82309473df28384ede65e94da27fccc45a920e6ef4a4ffbc` |
| Qualified A | 96 | 570 | `54cd7ed77a7c37a67dc050e8155fbbbcad61e4d952316fa2e3eb5c2f602110ed` |
| Qualified B | 96 | 451 | `23c186d3c393c9d233558c8150e9bb1f7c38f75f6e3cf1d7c7685341057f5870` |

The implementation is
`pontius.fresh_capacity_filling_structures`. Its source SHA-256 is
`222f8ea8cfd3c7766440aebfc83010686c57d71da523819e9068e9d817d73bf5`.
Canonical structure bytes bind:

- ADR-0305's literal seed and generator version;
- ADR-0306's frozen source id, source SHA-256, and source commit
  `a6f7d4b20a67f00b67be40bf412a5e9ff32fc84d`;
- ADR-0293's SHA-256/Fisher-Yates dependency version, ten pot values, and six
  stack values;
- ADR-0301's width-four structural-filter version;
- family kind, exact raw candidate-attempt count, ordered context ids, and
  every card, chip, hand-axis, and reduced exact-probability field.

Each family spans all ten pot values and all six stack values. Every context
contains exactly 21 distinct physical cards, four canonically ordered opener
hands, four canonically ordered responder hands, and positive exact rational
probability on all 16 joint deals summing exactly to one. Every showdown matrix
has both signs and at least three distinct rows and columns. The representative,
qualified-A, and qualified-B structures contain 48, 94, and 96 distinct sign
matrices respectively; semantic context identity, not sign-matrix identity
alone, is the frozen uniqueness rule. Payoff span is retained only as the
derived `pot + 2 * stack` structural property; no value is computed.

## Candidate-free boundary

The structural source imports only `evaluate_seven` from the exact river card
evaluator. It contains its own immutable exact-probability and context records
and an exact reproduction of ADR-0293's SHA-256 counter stream, unbiased
`randbelow`, and Fisher-Yates shuffle. A maintained differential compares the
copied stream, shuffled deck, and showdown signs against the frozen ADR-0293
helpers for all three seeds. The source imports no reduced sizing oracle,
action-abstraction candidate, qualification or evaluation owner, replay,
blueprint, convex master, resolver, or strategy module.

The independent source keeps value-free construction from transitively loading
the reduced sizing oracle. This is dependency isolation, not a new random
generator: the version and differential make exact inherited semantics
authoritative.

## Finite disjointness evidence

The prior finite inventory contains 748 unique semantic contexts: ADR-0291's
four controls, ADR-0293's 24-context confirmation family, all six ADR-0295 and
ADR-0297 96-context pools, and ADR-0301's 48-context representative plus
96-context qualified pool. ADR-0303's final panel is a subset of that last
pool, so it adds no new semantic context.

| Inventory | Contexts | Semantic-inventory SHA-256 |
|---|---:|---|
| Prior ADR-0291--0304 | 748 | `cbeae15bb963fa9117cffeb12fddf189d2bcf9b5b46a491d5f8065e0b88de683` |
| V4 representative | 48 | `6310faf33536eb822986f63bc2f691a03b9c3d92d22163c9a57736cd8e80097f` |
| V4 qualified A | 96 | `448b857005c3d88a1dfe8a4179719c5249d7086bf41ea488b023bf5918b4bad8` |
| V4 qualified B | 96 | `46e462dabb8b4c5d47f9699c4550d8c0c1806b1a9ef8a64eb14560ad9bb46905` |

All six prior/fresh and fresh/fresh pairwise intersections have size zero. The
complete evidence SHA-256 is
`ee25807ce514b97b686595b328cf8c16b7812681309f9ba778bff4a26bda83d4`.
This is an exhaustive absence claim only over those finite maintained
inventories, not a population-frequency or IID claim.

## Verification

Six new deterministic tests cover ordered reconstruction, exact seeds,
attempts and structure identities, cards, exact ranges, filters, diversity,
all finite intersections, inherited stream/card/filter differentials, Python
3.11 grammar, strict source imports, malformed inputs, provenance mutation,
semantic duplication, digest drift, and immutability. The focused v4/v3 source
and structure slice passes 17 tests. The repository-wide suite passes 1,190
tests with two intentional environment-dependent skips. Ruff lint and format,
generated STATUS, maintained Markdown links, and staged whitespace checks pass.

## Next boundary

Implement the candidate-blind qualification owner separately from this source.
It may convert only the sealed qualified-A structure one-to-one into the
existing reduced oracle, own both full-integer and minimum/all-in calls, retain
the frozen unit-specific numerical allowances and 4,096-pivot cap, and stop
inside the runner at the twenty-fourth qualifier, first ambiguity, numerical
failure, or exhaustion. Qualified B remains unopened unless A passes. Commit
both exact selected panels and teacher controls before importing v3 or v4 into
any value-owning evaluator or opening the representative family.

## Claims boundary

This result establishes deterministic value-free structures and finite-
inventory disjointness only. It establishes no sizing opportunity, v4 quality,
raw-chip recovery, candidate ordering, representative poker frequency,
production range width, real-time decision quality, latency, action width
through the convex master, replay compatibility, blueprint, resolving,
multiplayer safety, NashConv, AIVAT, league strength, C5 completion, or complete
bot. No revoked experiment, external publication, or thesis change is
authorized.
