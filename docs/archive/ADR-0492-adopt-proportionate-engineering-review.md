# ADR-0492: Adopt proportionate engineering review

- Status: accepted prospective workflow amendment upon its authorized decision commit
- Date: 2026-09-05
- Follows: ADR-0491
- Base-Commit: 53773cb9e7489d8cfa32b4e0ceadea37c5980023
- Invocation-Authority: none
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0492
- Front-Door-Contract: ADR-0307
- Front-Door-Revoked: ADR-0281, ADR-0468, ADR-0472, ADR-0475
- Front-Door-Active-Next: Select the next bounded source task; no operating or research execution
- Front-Door-Blockers: operating and research gates remain closed

## Decision

Adopt three prospective engineering-workflow changes: qualified mechanical
correction verification, controlled failure schedules with independent outcomes,
and review tiers selected by changed contract risk. The normative definitions
are the corresponding sections of docs/workflow.md and CLAUDE.md rule 8 in
this decision's exact reviewed tree. No fourth rule or new proof system is added.

This takes effect only at the separately authorized decision commit. A draft,
generated STATUS or review candidate does not activate it. The amendment itself
uses the prior protocol: two independent Tier C reviews, not the lighter route
it introduces, followed by isolated metadata acceptance and exact commit approval.

## Why these three

The Windows fixture repair's r001 reviews required five line-width corrections;
the following round verified unchanged parsed behavior except a mechanically
derived census value. The source-seal integration then repeated a review for
88 generated STATUS carriage returns. The corrections were appropriate; repeating
substantive review of unchanged behavior was not the useful part. The new route
keeps exact identities and one independent correction check, preserving earlier
reviews of the unchanged parts without relabeling their issued verdicts.

The fixture's original same-number reuse depended on OS allocation luck. The
accepted replacement controlled numeric tokens while retaining the real writer,
native resources, independently queried liveness/identity and deliberately bad
replay controls. The new schedule rule makes this distinction explicit, without
allowing an injector to certify the mechanism it replaces or hide an incorrect
production outcome. It is permission for scoped tests, not an execution grant.

Filename-based tiers could classify a normative configuration change as light
while treating harmless nearby reflow as evidence-critical. Tiers now follow the
highest direct/indirect risk to named invariants. Config, tests, generated data
and governance are not automatically safe; unknown classification rounds up.

These are historical motivations, not retrospective waivers. The exact prior
records and outcomes remain in the ADR-0491 source-seal packet and its referenced
fixture records. No rejected candidate becomes accepted under a new standard.

## Prospective supersession and preserved boundaries

Supersede the current versions only at CLAUDE.md rule 8 and docs/workflow.md's
Change tiers, new Controlled failure schedules, Stage 4 mechanical route, and
their direct Principles/Stage 3/Stage 5/checklist/template cross-references.
All historical versions, accepted ADRs and issued artifacts remain immutable.
Specific task constraints or stronger acceptance requirements still bind unless
separately amended; these general rules do not silently supersede a source seal.

Keep immutable refs and manifests, independent substantive review, real contract
behavior, explicit refusals, exact types, sealed-history/failure retention,
snapshot isolation, floor-first dual-interpreter acceptance, source-opening scope,
round/residual budgets, and exact per-commit authorization. No one-shot owner is
revived. No experiment, rehearsal, operating run, capability or parked lane opens.

## Verification and limit

The four-path change is CLAUDE.md, docs/workflow.md, this ADR and generated STATUS.
No runtime, test, analyzer, CI, profile or dependency byte changes. Reviewers must
challenge mechanical-chain laundering, source-sensitive changes, simulated
oracles and tier understatement against the full frozen text. The unchanged
status generator and its 12-test suite run on CPython 3.11.15 first, then 3.14.6,
from fresh isolated snapshots; raw LF/BOM/whitespace and exact scope are checked.
Those tests verify metadata, not the judgment quality of future reviews.

No numerical productivity gain or complete classification proof is claimed.
If a shortcut conceals a substantive change or a controlled test cannot detect
the prohibited behavior, its qualification fails and the ordinary stricter path
applies. The next source task remains separately selected under ADR-0491.
