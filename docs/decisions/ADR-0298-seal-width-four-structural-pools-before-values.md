# ADR-0298: Seal width-four structural pools before values

- Status: accepted structural freeze; all width-four sizing values remain unopened
- Date: 2026-08-23
- Follows: ADR-0297
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0298
- Front-Door-Contract: ADR-0282
- Front-Door-Revoked: ADR-0281
- Front-Door-Active-Next: Implement and execute ADR-0297's exact value-owning runner against only the three sealed width-four pools, stopping each batch at target, ambiguity, or exhaustion; keep ADR-0295 batch 2 and every action-abstraction, replay, blueprint, convex-master, resolver, and strategy label closed
- Front-Door-Blockers: no width-four full or narrow LP has run, replicated yield and pivot gates remain unknown, and no v3 mechanism is authorized

## Verdict

Accept the structural half of ADR-0297 and seal all three width-four pools
before opening any sizing value. The generator, structural filter, exact joint
ranges, canonical bytes, analytic LP dimensions, and preservation controls
pass. The structural module does not import the sizing solver or any legal-
action abstraction source.

## Sealed pools

| Batch | Raw card candidates | Pool SHA-256 |
|---:|---:|---|
| 0 | 459 | `ee82577c3820685376af6f988c892df265a68dacb36f0fafdd89095dac2d1603` |
| 1 | 471 | `d2022051f734d1d977055bd1148f6b6e830a41af047e63964ce6a4fc4421a2cf` |
| 2 | 493 | `ebf029eb2930f0a63030096373f7e91dd5b361055754e2497f229fff4f38f049` |

Each pool contains 96 ordered four-by-four contexts. Every context has 21
distinct physical cards, positive exact rational probability on all 16 joint
deals, both showdown signs, and at least three distinct row and column sign
patterns. The three pool digests are unique.

For every context the static full-arm compact LP has `8*S - 4` variables and
`8*S` inequalities at stack `S`; the narrow arm has 20 variables and 24
inequalities. The frozen stack set reaches the preregistered maxima of 236
variables and 240 inequalities. This is exact work structure, not elapsed-time
or strategy-quality evidence.

ADR-0293's confirmation panel remains
`c3d1f5ca6dea3291e202d73e542caccb05cf61bca775b327fad90c3e62bc5438`.
ADR-0295's three structural pools remain
`37d6e5ee5ce23b5473b1a3cf7cf521a9e40673a0b514ff2368dc02c5e325eda2`,
`7590e8490266315bc3bfcf5757fb6e1cdea232151cb0dd0000b90dbe66aedde6`,
and `6ac85b6314e4d8bd1124775e2d65899fcc1dd059a6bc649dce42bc3d860ebac8`.
ADR-0295 batch 2 values remain unopened.

## Decision

Commit the generator, pool identities, structural tests, and this record as a
separate evidence boundary. After this commit, implement ADR-0297's value
runner in a separate module so the structural source remains value-free. The
runner must own both LP calls, the frozen constants, numerical and pivot gates,
pool-prefix binding, classification, and immediate termination. Only that
runner may open width-four values.

## Evidence classification

- **Known:** the generator source contains no sizing-solver import; all pool
  fields, exact work dimensions, and digests are deterministic.
- **Reproduced:** all three pools reconstruct identically, satisfy the frozen
  width/filter/card/range invariants, and preserve earlier structural digests.
- **Unopened:** every width-four full and narrow value and ADR-0295 batch 2.
- **Hypothesis:** width four raises candidate-blind sizing-opportunity yield
  enough to pass all three 12-of-96 replications under the pivot cap.

## Dissent

Supporting continuation: the temporal boundary is intact, the structural
generator is independent of candidate and value code, and exact LP growth is
the frozen four-thirds factor.

Opposing evidence: the stronger sign-pattern filter needs roughly five raw
card candidates per accepted context, and structural richness previously
failed to predict sizing opportunity.

Largest unknown: the unopened full-over-narrow yield.

Cheapest falsifying experiment: execute the already-frozen owned runner in
batch order and stop on the first failed batch without opening later batches.

## Claims boundary

This result establishes only deterministic structural pools and analytic LP
dimensions. It does not establish sizing opportunity, oracle cost in
milliseconds, action quality, a valid abstraction, representative range
frequency, runtime latency, replay or solver integration, a blueprint,
resolving, multiplayer safety, strength, C5 completion, or a complete bot. No
revoked experiment, external publication, or thesis change is authorized.
