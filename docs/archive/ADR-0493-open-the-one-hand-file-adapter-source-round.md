# ADR-0493: Open the one-hand file adapter source round

- Status: accepted source-opening decision upon its separately authorized commit
- Date: 2026-09-05
- Follows: ADR-0492
- Base-Commit: 7a387e995e3b37232d2379332927247a4d49c64e
- Invocation-Authority: none; operating, experimental and rehearsal execution remain closed
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0493
- Front-Door-Contract: ADR-0307
- Front-Door-Revoked: ADR-0281, ADR-0468, ADR-0472, ADR-0475
- Front-Door-Active-Next: Implement the bounded one-hand file adapter; no operating run
- Front-Door-Blockers: adapter source acceptance remains open; operating and research gates remain

## Decision

Adopt the independently reviewed one-hand file adapter design r003 and open
its bounded CPU-only source round. A saved portable blueprint and a scripted
hand JSON file will feed the existing ReplayHost, followed by independent
persisted-trace verification and a concise actions/settlement summary. Selecting
these inputs will not require Python edits. This supplies a correctness adapter,
not a trained policy, interactive opponent, strategy evaluation or operating run.

This decision takes effect only at its separately authorized adoption commit.
The copied proposal files remain byte-identical historical inputs: their draft
and conditional wording does not activate permissions by itself. This ADR adopts
their specified mechanisms, constraints and acceptance map and activates only
the exact source opening below. A working ADR, generated STATUS or review ref
does not open implementation. Source acceptance/seal and invocation stay separate.

## Bound design and review identities

Design task: `v0a-hand-adapter-design/r003`.
Candidate: `02e24f143b8df4b2f03e8a94c58ab57905a8b2b6`.
Base: `7a387e995e3b37232d2379332927247a4d49c64e`.
Tree: `bd1cd2f83612aacac9d1de1c8e0afd673a86579c`.
Manifest SHA-256:
`f730799182d3f3eda2d9efa273048b2eaf28ceeb4274ea7525df95426ca679b1`.

Copy the three reviewed blobs unchanged into
`docs/architecture/v0a-hand-adapter-r002/`:

- `brief.md`, SHA-256
  `f33da4160da7aa8b7caa8c99b15ff9456b257e970eb0c99efd349fc817ff06b9`.
- `design.md`, SHA-256
  `fbe4d15e03ae06567a4a0a795e23976fa29aa48f50da024c36f5beccb175e63a`.
- `source-opening-draft.md`, SHA-256
  `4e62f00b05c3401905d04d57e04db27fb1ea5f5a28286f3bd979736970ac41da`.

The r002 document edition names are intentionally retained. r003 is the new
snapshot round, correcting only one extra terminal LF in each r002 document.
The controller separately approved that one-time design-budget extension. It
does not extend the later implementation budget or authorize another lane.

Both fresh independent Tier C reviews of r003 are CLEAN, Spec PASS, Quality PASS,
C/I/M 0/0/0, Design SOUND. Original reports are retained byte-exact in the packet
at `D:/Pontius/tmp/v0a-hand-adapter-design-r001/packets/r003/`:

- `reviews/review-a.md`, SHA-256
  `ed499e3b4764aa1f8d7afe4a206f965f8f870cc67e409aae50c45c3e1f5e5765`.
- `reviews/review-b.md`, SHA-256
  `0320d1f877a0567013bd0c9a992be68bcc5a300c505d8b114cb99d3694190e99`.

The prior source-identity finding is closed at design level by both reviewers:
every initial/final source identity operation uses raw Git object mode, with
prospective real-CLI replacement-object refusal controls. Those controls are not
implemented or executed yet. All earlier candidates and failed issued outcomes
remain unchanged. Design acceptance is not runtime or implementation acceptance.

## Exact source opening

Adopt brief.md's criteria and design.md's closed scenario schema, literal-card
adaptation, exact direct imports, source/file admission, single host invocation,
persisted-byte acceptance conjunction, summary/refusal contract and test map.
Adopt the companion proposal's "Exact proposed additions", "Six current-file
registration exceptions proposed" and "Acceptance, authority and completion"
sections as the binding scope. Their adoption condition is satisfied only by
this ADR's separately authorized decision commit, not by copying the documents.

Open exactly these new production paths:

- `src/pontius/hand_scenario/__init__.py`, inert.
- `src/pontius/hand_scenario/codec.py`, value-only admission and fixture adaptation.
- `tools/v0a_hand_adapter.py`, the source-bound file/host/reader command line.

Open only the three test suites and four JSON fixtures named in the proposal.
There is no additional module, re-export, input format, dependency, launcher,
trace schema, source-proof framework, policy search or operating mode.
Ordinary correctness work uses fresh declared expectations and task identities
under the existing snapshot policy; the correctness namespace is not a grant
for experiments, arbitrary data use, scientific profiles or consumed owners.

Prospectively supersede CLAUDE.md rule 1 only for the six current registration
file versions and exact delta scopes printed in the proposal. All six base
Git blob pins must still match at opening; unexplained drift stops work rather
than transferring permission. The exceptions are registration-only, not authority
to change analyzer inference, historical IDs, old assertion behavior, legacy
edges, SCC checks, complete-deal restrictions, capability grants or old CI gates.
No registration file changes in this adoption commit.

Extend ADR-0486's registration-only zero-grant treatment to this exact task.
The analyzer stays known unsound and parked; registration does not prove safety.
If the unchanged generator cannot register these additions, stop rather than
repair it here. Keep the existing runtime, blueprint codec, immutable blueprint,
driver, old tests outside the exact exception, prior ADRs and sealed history
byte-identical. Runtime/policy inputs never receive the full host-side deal.

## Bounds and implementation acceptance

Retain the reviewed budgets: 500 production lines total, 400 combined new-test
lines, four JSON fixtures totaling at most 16 KiB, and 100 manually added/removed
registration lines excluding generated outputs and separate decision metadata.
One initial implementation round and at most one bounded correction are opened;
return before a larger scope, third candidate or sealed-core change. Qualified
mechanical corrections follow ADR-0492 without retrospective verdict transfers.
The design's other stop and reassessment rules stay binding. Tight test budgets
are not permission to omit required controls or compress away clear structure.

Keep both independent Tier C implementation reviews and every design acceptance
control, including all 24 literal-card permutations, real loaded-policy hands,
independent settlement/action expectations, source commit/blob replacement,
persisted-trace/refusal fault controls, strict input admission and the real
repository boundary gate. No source-control bypass flag or fake success oracle.

Run CPython 3.11.15 first, then 3.14.6, in fresh D-local snapshots with -B -P,
snapshot-root cwd/src, scrubbed environments and absolute PONTIUS_GIT. Retain
the minimum decimal-conversion-setting controls and the reviewed post-CLEAN
direct CPU population. No implementation pass is claimed by this decision.
Source acceptance/seal and later use beyond scoped correctness work require
their own applicable evidence, review and authorization.

## Adoption verification and exclusions

This adoption changes exactly this ADR, generated STATUS and the three unchanged
reviewed documents. Following ADR-0490's faithful-incorporation precedent, the
metadata check is Tier A: one fresh independent light review plus the unchanged
status generator check and its 12-test suite on the floor then development slot
in fresh snapshots. The existing Tier C design reviews are not replaced or
waived. Any actual scope or contract divergence stops faithful incorporation.
STATUS is generated, never hand-edited; its output is mechanically kept LF-only.

No production source/test, registration, CI, workflow, dependency or historical
artifact changes in this adoption. No measured capacity, byte/memory/wall quota,
strength, expected-value improvement or exhaustive poker-coverage claim follows.
The chip integer domain is a conversion-compatibility constraint, not a measured
bankroll or operating bound. Operating budgets and authoritative populations stay
unadmitted. H32, campaign, compiled work, Gate 13 and analyzer repair stay parked.
No experiment, rehearsal, operating run or consumed identity is opened or revived.
