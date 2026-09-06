# ADR-0503: Source-seal the seeded-deal generator

- Status: accepted source-only seal upon its separately authorized decision commit
- Date: 2026-09-06
- Follows: ADR-0502
- Base-Commit: 62157da582fbf470b1091f2a56f4196ffa202d20
- Invocation-Authority: none; no new demonstration, rehearsal, operating or research run
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0503
- Front-Door-Contract: ADR-0307
- Front-Door-Revoked: ADR-0281, ADR-0468, ADR-0472, ADR-0475
- Front-Door-Active-Next: Select bounded seeded-deal session task; poker execution closed
- Front-Door-Blockers: generated session population and invocation remain unadmitted

## Decision

Accept the exact reviewed seeded-deal generator r001 as a CPU-only source asset,
closing the bounded implementation acceptance opened by ADR-0502. One standalone
stdlib tool materializes an existing-format six-seat session schedule from an
explicit saved seed request. The pure per-hand interface is independently callable;
the CLI saves a bounded schedule and receipt. It never launches poker or chooses
a seed according to generated cards, actions or payouts.

Effect requires this exact decision's separately authorized commit. A working ADR,
generated STATUS, review ref or passing test run does not activate this seal.
Incorporate only the eleven exact source payload blobs below, this new ADR and
generated STATUS. No additional implementation or workflow-rule change belongs here.

## Bound source identity and scope

Task: v0a-seeded-deals-source/r001.
Commit: 43ea7265d3dc759549b8f8c9e9839cf83bf8aefd.
Base: 62157da582fbf470b1091f2a56f4196ffa202d20.
Tree: 60c05a4162118e82ec235354a95e08726fa020c0.
Manifest SHA-256:
518276843679fabac6645a0e195b802f5dc86a269087f99deab66788d33c3e6a.

These paths must have the source candidate's exact raw frozen blob bytes:

- tools/v0a_seeded_deals.py
- tests/test_seeded_deals.py
- tests/test_seeded_deals_boundary.py
- tests/fixtures/seeded_deals/request.json
- tests/fixtures/seeded_deals/expected_session.json
- tools/check_stabilization_boundaries.py
- tools/generate_test_inventory.py
- tests/test-inventory.json
- tests/test-profiles.toml
- tests/test_inventory_and_profiles.py
- .github/workflows/ci.yml

Adopt the complete contracts in docs/architecture/v0a-seeded-deals-r001.md:
the exact versioned SHA-256 counter stream, big-endian hand/block indices and words,
bounded rejection sampling, descending Fisher-Yates shuffle, two-round dealing
relative to the rotating button, sorted private pairs and ordered five-card board.
The seed is exactly 64 lowercase hexadecimal characters; hand indices are exact
integers 0 through 15 and session counts are exact integers 1 through 16.
Each hand derives from its own seed/index stream with no shared random state.

The fixed table has six 200-chip stacks, blinds 1/2, initial button 0, controlled
seat 3 and five passive opponents. The emitted existing-format schedule contains
no seed, generator receipt, future-result or other new policy-facing metadata.
Both pure interfaces return fresh data containers and perform no explicit I/O.

The file CLI strictly decodes the closed request within 1024 bytes and checks
integer-token length before conversion. It admits only declared absolute D-local
non-reparse paths, binds request identity and exact bytes, exclusively creates a
new output, performs one counted write, flush/fsync/close and exact readback,
then revalidates the request before its one bounded receipt write. Failure retains
the actual output or prefix, reports the declared typed refusal when possible,
and never overwrites or retries the output. KeyboardInterrupt yields exit 130.
These checks implement the declared trusted-storage model, not a hostile-race sandbox.

All existing poker runtime, session/host/event tools, fixtures and blueprints remain
byte-for-byte unchanged. No src/pontius addition, private-host access, optional
dependency, new policy or strategic mechanism is introduced. The six registration
exceptions close with these exact accepted versions; no standing mutation grant follows.

## Independent oracle and registration preservation

Before production, an independent calculator materialized the declared three-hand
seed using struct packing, an explicit draw cursor and seat-centric dealing. Its
complete deck/word traces and canonical fixture bytes match on actual 3.11.15 and
3.14.6; a separate .NET calculation checks initial message packing and hashing.
Production was neither imported nor copied into that reference. The literal fixture
rejects a semantic change to the production hand index; controlled finite words
exercise the real index helper at the rejection boundary and exhaustion limit.

Reference report, under D:/Pontius/tmp/v0a-seeded-deals-source-r001/reference/:
reference-report.md, SHA-256
66bfb2580606ec08d10ffed3847a1285bddec2e538f1829bf6a6fae2958179a8.
Expected three-hand session SHA-256:
e584bd0e3cd1b44a2ff449c996b48f99e289547d319615c79efdf6c1d624267e.

All 2,972 old inventory records and 434 old payloads remain exact and ordered.
Exactly 27 deny-all test IDs and two CPU payloads are added. All old profile
settings, assertion predicates, test IDs, import rules and CI gates are preserved.
Complete ordered census comparison retains all 141 expanded capability rows,
638 old blockers, 381 old analyzed sites, 4,196 old helper edges and 591 decoys.
The one existing-source tuple insertion accounts for 46 blocker, 705 helper-edge
and 531 decoy source-line shifts. Additions are eight blockers, seven analyzed
sites and 73 helper edges; no decoy or expanded capability row is added.

Final full census observations match byte-for-byte across both actual interpreters.
All new records, reason totals, source coordinates and derived digests are accounted
for in the full retained comparison. The analyzer implementation is unchanged,
capability scopes remain zero, and analyzer inference remains parked under ADR-0486.
This source acceptance makes no repaired-soundness claim.

Registration report, under the task root's registration/:
report.md, SHA-256
efb2f6f91cc5f5b2c2efdfafdcd00068b291703de3db2ea7c78d234ed95a9bfe.
evidence-index.json, SHA-256
27d487a72e370a79eee1bcaa6357a935d8e2f7df10b150296ec7e209e43ce8f0.
Final full census SHA-256:
05ca97aa9c10b1fa13b2e4ea477f5a1ab1a13f710778fd41c3b90889a326a1b4.

Final use: 207/350 production LF lines, 538/650 combined new-test LF lines,
two fixtures totaling 656/4096 bytes, and 86/200 manual registration add/remove lines.
Generated inventory/profile bytes and this decision metadata are counted separately.

## Review lineage and final acceptance

Both fresh independent Tier C source reviews are CLEAN for specification and
quality, C/I/M 0/0/0, and Design SOUND. No required correction remains. Original
reports are retained under the source task root's packets/r001/:

- reviews/review-a.md, SHA-256
  9551fbd857c6d1b0af923717c723c57a08a1326267e647178d63a0fb5340de39.
- reviews/review-b.md, SHA-256
  15d69e02cc713c1fc5dbffaf33ce28b86954894fabb37f4f673e099b74491e98.

r001 is the initial and only issued source candidate. Original development
failures and unsuccessful tooling attempts remain retained. The missing-tool and
missing-CLI controls failed before implementation. An argparse interruption exposed
an exception outside the handler; moving parsing inside it closed that boundary.
The registration rule initially rejected normal super initialization; its narrow
exception passed the real gate and 23 declared negative controls on both slots.
Before freeze, the integer test was corrected from an over-envelope 900-digit
request to an in-bound 700-digit request, with a before-conversion assertion.
The complete census accounts for the four inserted test lines. Earlier outputs
and digest refreshes remain distinct from final source observations.

After both reviews, all twenty declared payload commands passed on actual CPython
3.11.15 first, then 3.14.6. Per interpreter, the seven named suites reported
168/168 tests passing with zero failures, errors or skips, including all 91
inventory/profile tests. The additional decoder control passed at
int_max_str_digits=640. Inventory generator --check and the real stabilization
boundary gate passed. Each payload and its actual-version/module-origin preflight
ran from a fresh exact-candidate D-local snapshot with -B -P, bound cwd/src,
a scrubbed environment and absolute PONTIUS_GIT. Native permissions were used
where required for real Windows file/process boundaries.

The final retained 1-, 3- and 16-hand CLI schedules have identical bytes across
interpreters. Both new suites traverse unchanged public Admission, Schedule,
TableInput and card validation at those counts without playing generated hands.
Existing session/host regression suites retain their own fixed correctness controls.

Final evidence under the source packet root:

- checks/final-acceptance-summary.json, SHA-256
  8990bdc05cf6abee2f9b5a89ad2b1c92287bcc63c2fb40eb36713b6143025307.
  This indexes every original final receipt and the retained schedule comparison.
- disposition.md, SHA-256
  c6f6b8f729e1cbbcf34360847e1dbb8f6be37df5c56e9a0e61a9c08411a27cc3.

These are bounded local correctness results. No hosted CI, Ruff, performance,
statistical randomness, cryptographic suitability or playing-strength result is
claimed. The non-D-checkout admission-clone helper remains locally unexecuted;
the registered hosted CI steps are its future environmental check. Real I/O
failure controls prove their observed resource effects, not arbitrary operating
liveness or cancellation at every bytecode.

Source receipts predate this ADR and STATUS. Following ADR-0498 and ADR-0500,
metadata must separately pass one fresh independent Tier A light review, unchanged
status generator --check and all twelve status-generation tests on actual 3.11.15
first, then 3.14.6 in fresh exact-candidate snapshots. Verify eleven raw source
incorporations and the complete thirteen-path integration delta. Any mismatch
stops incorporation. This replaces no Tier C review and waives no source gate.
The user separately authorizes the exact decision commit and push.

## Next boundary and exclusions

Select a bounded seeded-deal session task separately. No generated schedule is an
admitted demonstration or operating population merely because it passed correctness
validation. This seal opens no demo, rehearsal, operating/research invocation,
arbitrary population sampling, policy selection, timing study, training, self-play,
league evaluation, rebuy, seat elimination or human poker action input.
Future neural and bot-comparison reuse remains compatibility context.
The ADR-0501 fixed demonstration remains completed and consumed; it is not rerun.
ADR-0307, formal operating prerequisites, parked lanes and consumed owners remain
binding. No cleanup, ref retirement or revived scientific identity is authorized.
