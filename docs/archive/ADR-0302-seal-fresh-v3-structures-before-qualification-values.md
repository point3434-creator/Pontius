# ADR-0302: Seal fresh v3 structures before qualification values

- Status: accepted value-free structural freeze; every fresh sizing value remains unopened
- Date: 2026-08-23
- Follows: ADR-0301
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0302
- Front-Door-Contract: ADR-0282
- Front-Door-Revoked: ADR-0281
- Front-Door-Active-Next: Implement a separate candidate-blind owned qualification runner against only the sealed 96-context qualified pool, bind an exact one-to-one structural-to-oracle conversion, and stop immediately on the twenty-fourth qualifier, first ambiguity, or exhaustion; keep the representative family and every v3 value, replay, blueprint, convex-master, resolver, and strategy integration unopened
- Front-Door-Blockers: no fresh full/narrow value or qualified result exists, the 24-context qualified panel is not identified, the representative family has no value, no v3 evaluation has run, and integration remains unauthorized

## Verdict

Accept and seal the value-free half of ADR-0300's dual-panel construction. The
two ADR-0301 streams reconstruct exactly, satisfy every frozen card, chip,
range, width, filter, ordering, and identity invariant, and have no semantic
counterpart in the finite maintained ADR-0291 through ADR-0299 inventory or in
each other.

This record precedes every full, narrow, teacher, and v3 value on either fresh
family. Source/seed freeze commit `da1ca66` existed before the first structural
construction.

## Sealed structures

| Family | Accepted contexts | Raw card candidates | Structure SHA-256 |
|---|---:|---:|---|
| Representative | 48 | 172 | `b678f1140dd7ba75f5315abf58392d42b42a1a633c3249ec36991846a1bbab69` |
| Qualified pool | 96 | 496 | `fb26a8cfd2f82fd56896e22f6d006495f1148669dd6db3f56dcf2e79deeb4146` |

Both families span all ten frozen pot values and all six frozen stack values.
The representative family has 48 distinct showdown-sign matrices; the
qualified pool has 96. Every context contains exactly 21 distinct physical
cards, four canonically ordered opener pairs, four canonically ordered
responder pairs, positive exact rational weight on all 16 joint deals, exact
total probability one, both showdown signs, at least three distinct rows and
three distinct columns, and the derived chip payoff span
`pot + 2 * stack`.

The value-free module defines its own immutable structural probability and
context records. Its direct import inventory contains only the already frozen
ADR-0293 stream/card helpers plus standard-library types. It imports no reduced
sizing oracle, collision-repair source, legal action abstraction, replay,
blueprint, convex master, resolver, or strategy module. It has no value or
policy field and no solver call.

## Finite disjointness evidence

The maintained prior inventory contains exactly 604 semantic contexts:
ADR-0291's four reduced controls, ADR-0293's 24-context confirmation family,
all three 96-context ADR-0295 structural pools, and all three 96-context
ADR-0297 structural pools. All 604 keys are unique. Context ids are excluded
from semantic comparison; board, pot, stack, minimum bet, both ordered private-
hand axes, and every reduced exact probability are included.

| Inventory | Semantic-inventory SHA-256 |
|---|---|
| Prior ADR-0291--0299 | `a6b1c8863c40f475ebdf05a16bde258138b483d9de8e08172609e78ea6d702ef` |
| Fresh representative | `f22ee49b3217292e7b3db0a27e6720ab4ed8120ea4a904de6c31e0514ba424ec` |
| Fresh qualified pool | `deac14a912d46d15997436e03514e61d738f37a59583cda684f266fb442ef8ff` |

Every pairwise intersection has size zero. The complete finite-disjointness
evidence SHA-256 is
`a8db09b3800acfb53be14edc97f4ba9034cc38c2ec3410051bbc5e3483bacd97`.
This is an exhaustively checked absence claim over those finite maintained
inventories, not evidence about population frequency or IID sampling.

## Preservation and adversaries

Deterministic rebuild, canonical byte, source-digest, exact probability, card,
filter, count, attempt, id/order, semantic-uniqueness, and immutability controls
pass. Wrong seeds, generator versions, attempt counts, ids/order, pot sets,
physical-card identities, probability sums, probability types, and mutable
state fail closed. ADR-0293, ADR-0295, and ADR-0297 structural identities remain
unchanged.

Changed-file Ruff, Python 3.11 grammar parsing, whitespace, source inventory,
documentation, and the complete repository suite pass. The suite contains
1,143 tests with two expected skips.

## Decision

Commit these structural identities before implementing or calling the value-
owning qualification successor. That successor must convert each structural
record one-to-one into the existing reduced oracle context and prove equality
of every semantic field before solving. It may import full/narrow oracle
machinery but must not import the collision-repair source or derive any
candidate action. It must own both calls, classification, contiguous prefix,
first ambiguity, exact stop state, numerical controls, pivot caps, and result
binding.

The representative family remains entirely value-unopened during qualified-
pool classification. After a clean target-reached result, extract exactly the
first 24 qualifiers and commit the result, qualified-panel identity, teacher
controls, and disjointness preservation before opening the first representative
or qualified v3 value.

## Evidence classification

- **Known:** exact seed/source provenance, structure bytes and digests, attempt
  counts, context fields, import inventory, and finite semantic inventories.
- **Reproduced:** deterministic reconstruction, exact structural invariants,
  diversity, mutation failures, earlier identities, and zero finite overlap.
- **Unopened:** every value on both fresh families, qualification state, all v3
  values, and every integration path.
- **Hypothesis:** the separate 96-context pool will reach 24 unambiguous
  qualifiers within the frozen exact-work limits.

## Claims boundary

This result establishes only two fresh deterministic value-free reduced-game
structures and finite-inventory disjointness. It does not establish sizing
opportunity, candidate quality, representative poker frequency, production
range width, real-time decision quality, latency, replay or convex-master
compatibility, a trained blueprint, resolving, multiplayer safety, NashConv,
AIVAT, league strength, C5 completion, or a complete bot. No revoked
experiment, external publication, or thesis change is authorized.
