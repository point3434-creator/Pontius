# ADR-0299: Width four passes replicated sizing power

- Status: accepted candidate-blind evaluation-power result; one v3 preregistration is authorized but no mechanism or integration is accepted
- Date: 2026-08-23
- Follows: ADR-0298
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0299
- Front-Door-Contract: ADR-0282
- Front-Door-Revoked: ADR-0281
- Front-Door-Active-Next: Preregister exactly one v3 legal sizing mechanism before constructing fresh representative and independently width-four-qualified confirmation panels; keep every ADR-0291 through ADR-0299 panel development-only and keep replay, blueprint, convex-master, resolver, and strategy integration closed
- Front-Door-Blockers: no v3 mechanism or fresh dual-panel protocol is frozen, no v3 value exists, and neither candidate quality nor real-time integration has passed

## Verdict

Accept ADR-0297's width-four game as a powered candidate-blind development-
panel constructor. All three frozen batches reach 12 material full-over-
minimum/all-in contexts before their 96-context cap, with no ambiguity,
post-target opening, numerical failure, diversity failure, or exact-work
failure. This authorizes preregistration of one v3 mechanism on fresh panels;
it does not accept an action abstraction.

## Temporal and scope integrity

ADR-0297 was committed as `9f392f6` before pool construction. ADR-0298's three
structural pools and digests were committed as `b5b6b85` before the first
width-four value invocation. The value-owning campaign constructed only those
sealed pools, processed batches in order, owned both LP calls and all stop
state, and would have stopped the campaign before any later batch after a
failure.

Static AST inventory finds no legal-action abstraction, v1/v2 candidate, or
ADR-0295 value-runner import in the width-four evaluation source or maintained
value test. ADR-0295 batch 2 remains value-unopened. No earlier panel enters
this result.

## Frozen result

| Batch | Opened prefix | Qualifying indices | Result SHA-256 | Panel SHA-256 |
|---:|---:|---|---|---|
| 0 | 23 | `0,1,3,5,8,10,13,15,17,20,21,22` | `fcdd3a31301286b0db0e3c37201756f980ed611eaa9ed0f3acb2adb8e99c2a58` | `7ad25925d2108f6201aaeab2781645ec2366d171e374d83d452dd729a536a034` |
| 1 | 24 | `2,5,7,8,12,13,14,16,17,18,22,23` | `829231b00f4f70f65343654c43bc289cd94677dd63ad6dfe93528470f11955a1` | `109e1a3f4c0841cbc7fe60e7b5add9688d9461df70f1468cf4a60283cf3beba3` |
| 2 | 32 | `0,5,7,8,11,13,18,25,26,27,30,31` | `eceb8b2d74be8de8360e1f23b7793745f6b53a3f93aa2d2ade4fe6cd0a3b6da6` | `a9e6872992dc0f74f5c33f93abce4da0eedbb48ad8e53df728e91264230c042b` |

The campaign digest is
`4c37efdf69c3c96cc3aeef0bf22ab5f2a8078fd673c429ecf61b0f96b55d4ccd`.
Teacher-control digests for batches zero through two are respectively
`8cf5150af471041182feb8dd6b518f85d2253357f0e61a5b0a9755caac8a0641`,
`c722d3b9ef44d2ee7dc78c053b30ec4b3f91ee16743fdbe267ec0ad707a60f3c`,
and `f00843dc40945944856620c9067fcb3f67c7a36c94b8f35e18bd1d71f220202f`.

The retained panels span respectively 7/7/4 pot values, 5/5/5 stack values,
and 12/12/12 distinct four-by-four showdown-sign matrices. All exceed the
frozen 3, 3, and 8 minima.

## Numerical and exact-work controls

Across all 79 opened width-four contexts, the maxima are:

| Diagnostic | Maximum | Frozen ceiling |
|---|---:|---:|
| Probability-simplex residual | `3.391e-13` | `1e-9` |
| Chip-objective reconstruction error | `2.482e-12` chips | `1e-9` chips |
| LP primal-dual objective gap | `9.095e-13` chips | `1e-9` chips |
| Lower-envelope constraint violation | `1.990e-13` chips | `1e-9` chips |
| Full-arm simplex pivots | 445 | 4,096 |
| Narrow-arm simplex pivots | 40 | 4,096 |

Across the 36 leading two-by-two controls, maximum compact/teacher value
difference is `1.670e-13` chips, maximum teacher duality gap is `9.415e-14`
chips, and maximum compact pivots are 20. All frozen oracle gates pass.

The full invocation used 158 width-four full/narrow compact LPs, 36 projected
compact LPs, and 36 bounded normal-form teachers. One serial Python 3.11
observation on this workstation took `28.6158` seconds including structural
construction. This is a per-campaign offline diagnostic, not per-solve or per-
iteration latency, not a production game, and not evidence against or within
the 15-second per-street runtime contract.

## Semantic residual correction

Before the first value invocation, runner review found that the generic LP
field `linear_program_max_constraint_violation` takes a numerical maximum over
both dimensionless policy-simplex rows and chip-valued lower-envelope rows.
Using that mixed-unit number as one semantic gate would repeat the project's
numerical-coincidence defect family.

The reduced oracle now separately reconstructs
`max_envelope_constraint_violation_chips`; the campaign gates the existing
dimensionless probability residual and the new chip-valued envelope residual
through distinct nominal allowances. LP objective duality is also explicitly
chip-valued. The legacy mixed-coordinate diagnostic remains available for
backward compatibility but carries no width-four semantic authority.

## Decision

Park all ADR-0297 pools, observations, and panels as candidate-blind
development evidence. Do not use them to fit or confirm v3. The next checkpoint
may preregister exactly one legal v3 sizing mechanism. Only after its source is
frozen may fresh commit-derived seeds construct two disjoint evaluation
families:

1. an unqualified representative panel for maximum and mean full-versus-v3
   harm; and
2. an independently width-four-qualified panel for aggregate recovery where
   material intermediate-sizing opportunity exists.

The candidate must pass both families conjunctively before any reference-hand,
convex-master, blueprint, resolver, or strategy-label integration is eligible.
The exact legal action source remains the reference fallback.

## Evidence classification

- **Known:** source/configuration provenance, structural and result digests,
  exact LP dimensions, action counts, opened prefixes, and stop state.
- **Reproduced:** three 12-context yields, diversity, teacher agreement,
  numerical residuals, and pivot counts through the maintained campaign.
- **Observed:** the single `28.6158`-second local offline campaign duration.
- **Hypothesis:** a not-yet-frozen v3 can retain the conditional recovery seen
  in v2 while also passing fresh representative harm and qualified recovery
  gates.
- **Rejected:** treating width-four yield as candidate quality,
  representativeness, production range width, or runtime latency.

## Dissent

Supporting acceptance: all three disjoint seeds pass by substantial yield
margins, every panel has maximum sign-matrix diversity among its 12 retained
contexts, and exact/numerical work stays far inside the frozen ceilings.

Opposing evidence: the structural filter accepts only about one in five raw
card candidates; qualification explicitly conditions on material sizing
opportunity; the game still has only one bet and no responder raise; and no
candidate has faced untouched evidence.

Largest unknown: whether a compact legal lattice generalizes across both fresh
representative and qualified panels without post-outcome tuning.

Cheapest falsifying next experiment: freeze one v3 source and its complete
dual-panel gates before deriving fresh seeds or opening any new context.

## Claims boundary

This result establishes only a reproducible candidate-blind four-by-four one-
bet evaluation-power method within frozen exact-work limits. It does not
establish representative poker frequency, production range width, a valid
action abstraction, translation safety, real-time action quality, optimized
latency, replay or convex-master integration, blueprint strength, resolving,
multiplayer safety, NashConv, AIVAT, league strength, C5 completion, or a
complete bot. No revoked experiment, external publication, or thesis change is
authorized.
