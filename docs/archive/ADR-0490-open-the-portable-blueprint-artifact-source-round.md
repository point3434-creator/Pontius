# ADR-0490: Open the portable blueprint artifact source round

- Status: accepted source-opening decision upon its separately authorized decision commit
- Date: 2026-09-05
- Follows: ADR-0489
- Base-Commit: 7ee314b443e10896e87a2e194f24eddda31ff77d
- Invocation-Authority: none; operating, experimental and rehearsal execution remain closed
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0490
- Front-Door-Contract: ADR-0307
- Front-Door-Revoked: ADR-0281, ADR-0468, ADR-0472, ADR-0475
- Front-Door-Active-Next: Implement the bounded portable blueprint codec; no operating run
- Front-Door-Blockers: codec source acceptance remains open; operational and research gates remain

## Decision

Adopt the independently reviewed portable-blueprint design r002 and open its
bounded, additive, CPU-only source round. The codec supplies complete immutable
policy keys and actions as non-executable data to the existing runtime. It does
not change poker semantics, improve strategy, train a policy or authorize a run.

This decision takes effect only at its separately authorized adoption commit.
The reviewed proposal copies remain byte-identical historical inputs: their
draft/prospective status does not activate permissions by itself. This ADR now
adopts their specified mechanisms, constraints and acceptance requirements and
activates the precise source opening below; it does not rewrite those copies.
A working ADR or generated STATUS is not adoption. Implementation review and
acceptance, a source seal and any later operating authority remain separate.

## Bound design and review identities

Design task: `v0a-blueprint-artifact-design/r002`.
Candidate: `a552f6f34efe10155a702fd09a03bcc70802a369`.
Base: `7ee314b443e10896e87a2e194f24eddda31ff77d`.
Tree: `14b71ec9dc6bc6db20393008dde9f25db13a95c5`.
Manifest SHA-256:
`67abe320f73b8edfab60a93511f31eac62d0fac0279cdef712acda91fcf7aced`.

The three files are copied byte-for-byte into
`docs/architecture/v0a-blueprint-artifact-r002/`:

- `design.md`, SHA-256
  `5403709d2ee8cc6b0cbacd7775ca7cf71f07f1eecba5e5902286a2387de1b96d`.
- `source-opening-draft.md`, SHA-256
  `346aa8c36c59d970bd1ae71ecdf86d64ccbe78c996f955e526f581b061c96808`.
- `coverage.md`, SHA-256
  `d83bfd196dc8fe9b632858a83abba77a7dc9d8ae9e3247ea1d1fed82de80b2e3`.

The design and source-opening proposal each received two independent fresh-context
Tier C reviews: both CLEAN, Spec PASS, Quality PASS, C/I/M 0/0/0 and SOUND.
Permanent packet: `D:/Pontius-handoffs/v0a-blueprint-artifact-design/r002/`,
published at handoff commit `07d3cf2bea65d6532cfd8d08d7195714a17eefdd`.

- Review A, `reviews/review-01-codex-a.md`, SHA-256
  `5185b25b91171d096fe658e3e1cbe0c2fd600c5bfed6c47dd72fbde6e936620d`.
- Review B, `reviews/review-02-codex-b.md`, SHA-256
  `4e18f8ac0dbaebbbc7e8e88299717af65b2ce29fb501c162ce4d9462bbf168b4`.
- A's report-format clarification, SHA-256
  `4033048db6a8e9360da37fa6ce12d4593084d38bb5409cfedcffd1977605d4f4`.

The clarification corrects a report-formatting claim, not the design verdict or
candidate. All r001/r002 candidates and issued records remain unchanged. The
review outcome is design acceptance, not executed codec or policy evidence.

## Exact source opening

Adopt `design.md`'s API, closed schema, symmetric scalar admission, deterministic
encoding, identity relationship, direct imports and independent acceptance map.
Adopt the companion proposal's sections "New paths proposed", "Six exact
registration exceptions proposed" and "Limits, evidence and review" as the
binding implementation scope. Its conditional adoption language is satisfied
only by this ADR's authorized decision commit, not by copying or reading it.

Only these new source paths are opened:

- `src/pontius/blueprint_artifact/__init__.py`, inert.
- `src/pontius/blueprint_artifact/codec.py`, two byte operations and typed refusal.

Only the two named tests and two named JSON fixtures in the reviewed proposal
are opened. No additional module, launcher, dependency, re-export or fixture tree
is implicit. Ordinary correctness development uses fresh task identities and
the existing snapshot procedure; it is not a scientific profile or owner.

Prospectively supersede the original artifact brief's no-sealed-byte instruction
and CLAUDE.md rule 1 only for the six current registration-file versions and exact
delta scopes printed in the reviewed proposal. The six base blob pins must still
match at source opening; unexplained drift stops work rather than transferring
permission. The exceptions are registration-only and do not authorize changing
test behavior, analyzer inference, historical IDs, legacy edges, capability
semantics, existing CI hard gates, the six-file v0a population or runtime bytes.

Extend ADR-0486's registration-only, zero-grant disposition to this exact codec
task as specified in the reviewed proposal. The analyzer remains known unsound
and parked; registration is not a claim that it proves safety. If the unchanged
generator cannot register the additions, stop rather than repair it in this round.
Historic commits, source seals and every issued artifact remain immutable.

## Bounds and acceptance

Retain the reviewed 300-line codec and 300-line combined new-test budgets, two
fixtures of at most 8 KiB combined, and at most 100 manually added/removed lines
across the six registration exceptions, excluding generated bytes and decision
metadata. Allow one initial implementation round and at most one bounded
correction; return before any larger scope, third round or sealed-runtime edit.
The accepted design's reassessment and stop rules remain binding.

Retain both independent Tier C implementation reviews and the complete reviewed
acceptance map: independent full-key/canonical-byte oracles, real loaded-policy
action and complete-hand replay, the independent reader, miss/illegal-hit cases,
schema/exact-graph refusals, scalar boundaries and the real source boundary gate.
Run the floor first, CPython 3.11.15 then 3.14.6 in fresh D-local snapshots;
include the declared minimum decimal-conversion-setting controls and the reviewed
post-CLEAN direct CPU acceptance population. No passing implementation is claimed.

No artifact-byte, entry-count or source-ID-length ceiling is adopted. The numeric
domain derives from CPython conversion compatibility, not a measured bankroll,
wall or memory limit. No operational quota or capacity guarantee is introduced.
The deferred operating budgets and all separate invocation prerequisites remain
unadmitted. The source seal and any runtime use beyond ordinary scoped correctness
work require their own applicable review, evidence and authorization.

## Adoption verification and exclusions

This adoption changes exactly this ADR, generated STATUS and the three unchanged
reviewed documents. Its mechanical metadata check is Tier A: one fresh independent
light review of faithful incorporation and status, plus the unchanged status
generator's focused checks on 3.11.15 then 3.14.6 in fresh snapshots. The prior
Tier C design reviews are not replaced or waived, and no previous one-time
existing-reviewer exception is reused. STATUS is generated, never hand-edited.

No codec/test implementation, registration or CI edit occurs in this adoption
commit. No library/driver seal, old brief, prior ADR, runtime contract, retained
result, journal, consumed identity or historical standing changes. H32, campaign,
compiled work, Gate 13 and analyzer repair remain parked. No training, measured
strength, expected-value improvement, rehearsal or operating result is asserted.
