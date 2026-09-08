# ADR-0303: Seal fresh qualified panel before v3 values

- Status: accepted candidate-blind qualification pass and final dual-panel freeze; every v3 value remains unopened
- Date: 2026-08-23
- Follows: ADR-0302
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0303
- Front-Door-Contract: ADR-0282
- Front-Door-Revoked: ADR-0281
- Front-Door-Active-Next: Implement the frozen collision-repair v3 evaluator, then execute representative first and qualified second against only the sealed 48-context representative structure and 24-context qualified panel, with full-integer, v3, and minimum/all-in arms plus every numerical, teacher, width, monotonicity, normalized-loss, and aggregate-recovery gate from ADR-0300; keep replay, blueprint, convex-master, resolver, and strategy integration closed
- Front-Door-Blockers: no representative or qualified v3 value exists, both quality gates and aggregate recovery remain unknown, no passive replay audit is authorized, and integration remains unauthorized

## Verdict

Accept ADR-0302's candidate-blind qualification invocation. The sealed 96-
context pool reaches 24 material full-over-minimum/all-in contexts after a
contiguous 60-context prefix, without ambiguity, numerical failure, pivot-cap
failure, semantic conversion drift, or post-target pool opening. Seal that
24-context qualified panel alongside ADR-0302's still-value-unopened 48-
context representative family before the first v3 value.

Structural commit `f4e1744` existed before the first qualification value. The
qualifier source imports no v3 or legal-action source, has no representative-
family branch, and owns both exact arms, conversion, classification, prefix,
and stop state.

## Frozen qualification result

- Sealed pool SHA-256:
  `fb26a8cfd2f82fd56896e22f6d006495f1148669dd6db3f56dcf2e79deeb4146`
- Opened contiguous prefix: 60 of 96 contexts.
- Classification counts: 24 qualifying, 36 nonqualifying, zero ambiguous.
- Qualified indices:
  `0,5,10,13,15,21,22,23,24,25,31,33,34,37,40,41,42,43,45,48,52,53,55,59`.
- Qualification-result SHA-256:
  `c5be094e616043644a13ebbd477565ff548593a9d7d1f70dac0ae5340cbe0c23`.
- Qualified-panel SHA-256:
  `05f00a99ccec22bfea07abd405b1089414a89bce9a4c4e704efceb132ea1cf29`.
- Teacher-control SHA-256:
  `b88b47f2260da31bdb7e49a0d454309327483ded0ff6ea7b17d77bd2cf914ada`.
- Deterministic campaign SHA-256:
  `3ada7c7a68002eb2fa3d0e6ca904f0df771f17e8270fd09ef10cedef1772d8fe`.

The final panel spans all ten frozen pot values, all six frozen stack values,
and 24 distinct four-by-four showdown-sign matrices. Its contexts remain
semantically disjoint from the 48-context representative family and all 604
maintained ADR-0291 through ADR-0299 contexts under ADR-0302's finite inventory
comparison.

## Semantic conversion and stopping

Every opened structural record converts into an exact
`ReducedRiverSizingContext` through one field-by-field adapter. Each observation
binds the structural context digest, oracle context digest, conversion digest,
derived `pot + 2*stack` payoff span, complete full-integer bet tuple, exact
minimum/all-in tuple, LP dimensions, values, classifications, residuals, and
pivots. Verification reconstructs all 60 bindings and arms from the sealed
pool.

Mocked ownership controls prove that an all-qualifying stream performs exactly
48 LP calls and stops after context 23, while a first-context ambiguity performs
exactly two LP calls and stops. The real invocation stops at qualifying context
59. Contexts 60 through 95 remain qualification-value-unopened.

The smallest absolute distance between a full-over-narrow gap and its
`1e-4 * (pot + 2*stack)` threshold is `8.269404357176434e-4` chips, versus the
frozen `1e-8`-chip ambiguity guard.

## Numerical and exact-work controls

The 60-context prefix uses 120 compact LPs: one full-integer and one
minimum/all-in solve per context. The 24 retained contexts add 24 leading-
two-by-two minimum/all-in compact LPs and 24 independently enumerated bounded
normal-form teachers. Thus the bound result owns 144 compact LPs and 24
teachers, with no representative or v3 solve.

| Diagnostic | Maximum | Frozen ceiling |
|---|---:|---:|
| Probability-simplex residual | `6.661e-14` | `1e-9` |
| Chip-objective reconstruction error | `2.672e-12` chips | `1e-9` chips |
| Compact LP primal-dual gap | `4.547e-13` chips | `1e-9` chips |
| Lower-envelope violation | `1.066e-13` chips | `1e-9` chips |
| Full-arm simplex pivots | 336 | 4,096 |
| Narrow-arm simplex pivots | 39 | 4,096 |
| Teacher compact/value difference | `2.842e-14` chips | `1e-9` chips |
| Teacher primal-dual gap | `1.743e-14` chips | `1e-9` chips |
| Teacher compact pivots | 19 | 4,096 |

Every full LP has exact dimensions `8*S - 4` variables and `8*S`
inequalities at stack `S`; every narrow LP has 20 variables and 24
inequalities. Every teacher record binds its derived leading-two-by-two context,
exact minimum/all-in sizes, nine opener pure plans, and sixteen responder pure
plans.

One serial observation of the first fully bound invocation on this workstation
took `16.7752` seconds. This is an offline complete-campaign diagnostic, not a
per-solve, per-iteration, real-game, or 15-second street-latency result.

## Pre-seal plumbing correction

The first diagnostic run reached the same 60-context stop and same qualified
indices, and produced the same final panel digest. Before accepting evidence,
review found that its result serialized LP dimensions but not the exact arm
tuples, and its teacher rows bound the four-by-four source but not the derived
two-by-two context and sizes. The diagnostic hashes were result
`13525cc534014e2a3e412cdbdb5625fd02fd144db0ef2f892ab0071dfcef24ec`,
teacher
`8ed9ab0af2d77aa8f6605ed943f8c6a29811fe1c105028e28874415d4c5f1a4a`,
and campaign
`f95d372454763b4e5767a8d86604747448d36d50537428e4e69d5fb152bb236b`.

The successor schema adds only exact arm, bounded-context, and pure-plan
provenance plus cross-object verification. It changes no seed, structure,
context, solver, threshold, allowance, classification, stop rule, panel member,
or value. The unchanged invocation was rerun, and only the fully bound hashes
above carry evidence authority. The earlier in-memory hashes are diagnostic
and are recorded to avoid silently erasing the post-outcome plumbing repair.

## Decision

Proceed to the one frozen v3 campaign. Rebuild panel membership through the
value-free panel rebuilder; do not rerun qualification merely to discover
indices. Process all 48 representative contexts first, then the exact 24
qualified contexts. Stop before the second family if any representative
semantic, numerical, width, monotonicity, teacher, maximum-loss, or mean-loss
gate fails. If representative passes, process qualified and apply every
qualified loss and raw-chip aggregate-recovery conjunct. No source, panel,
threshold, unit, or gate may change after the first v3 value.

## Evidence classification

- **Known:** pool/prefix/panel membership, exact arms, conversion provenance,
  stop state, result bytes, work dimensions, and candidate-free import boundary.
- **Reproduced:** classifications, numerical controls, teacher agreement,
  pivots, immediate stopping, panel diversity, and deterministic hashes.
- **Unopened:** all 48 representative values, every v3 value, and all candidate
  integration.
- **Hypothesis:** collision-repair v3 will pass both fresh loss gates and recover
  at least 90% of the qualified raw-chip full-over-narrow gap.

## Claims boundary

This result establishes only a fresh candidate-blind sizing-opportunity panel
and exact reduced-oracle controls. It does not establish v3 quality,
representative poker frequency, production range width, strategically exact
translation, runtime decision quality, latency, replay or convex-master
compatibility, a trained blueprint, resolving, multiplayer safety, NashConv,
AIVAT, league strength, C5 completion, or a complete bot. No revoked
experiment, external publication, or thesis change is authorized.
