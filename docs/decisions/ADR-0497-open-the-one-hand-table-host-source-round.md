# ADR-0497: Open the one-hand table host source round

- Status: accepted source-opening decision upon its separately authorized commit
- Date: 2026-09-06
- Follows: ADR-0496
- Base-Commit: 1329c2c201bbf2f396946f2ebf460ee944ae4ece
- Invocation-Authority: none; operating, experimental and rehearsal execution remain closed
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0497
- Front-Door-Contract: ADR-0307
- Front-Door-Revoked: ADR-0281, ADR-0468, ADR-0472, ADR-0475
- Front-Door-Active-Next: Implement the one-hand reactive table host; no operating or research run
- Front-Door-Blockers: source acceptance pending; operating/research execution closed

## Decision

Adopt the reviewed one-hand reactive table-host design r001 and open its bounded
CPU-only source implementation. A local dealer owns one finite six-seat deal,
runs five declared simple opponents and applies the controlled bot's actual
returned actions through the existing public betting kernel. This completes the
one-hand table side of the already sealed event interface. Terminal interaction,
multi-hand operation and stronger decision machinery remain subsequent work.

This decision takes effect only at its separately authorized commit. The three
copied proposal documents remain exact historical inputs; their conditional
wording does not activate permissions. This ADR then activates only their exact
source scope and boundaries. A working ADR, generated STATUS or review ref does
not open implementation. Source acceptance and invocation remain separate.

## Bound design and review

Design task: v0a-table-host-design/r001.
Ref: refs/heads/review/v0a-table-host-design/r001.
Candidate: cf87e5087fa8e11ef5befac3f77a4896418d6509.
Base: 1329c2c201bbf2f396946f2ebf460ee944ae4ece.
Tree: 47626b7f3c2fd933633fb71a8b83d2de0ed0317f.
Manifest SHA-256:
a9e40454dd36e4289b1576d7cbf11527a7b4713177074ef2930b22b9ca930f93.

Incorporate these reviewed blobs unchanged under
docs/architecture/v0a-table-host-r001/:

- brief.md, SHA-256
  54ba2ac3d518a0426bcb99f4f8a0bd186323f17e8a7a0a3b380f7df20fa12d86.
- design.md, SHA-256
  88b9b5b30918502e9095d8926d54d74796980f960c79019ca760dfc4d7612f72.
- source-opening-proposal.md, SHA-256
  9b78ed56adcc4046ed0f79ef55858b5074f388cf7c00342353b810914b760487.

Both fresh independent Tier C reviews are CLEAN, Spec PASS, Quality PASS,
C/I/M 0/0/0 and Design SOUND at design level. Original reports are retained at
D:/Pontius/tmp/v0a-table-host-design-r001/packets/r001/:

- reviews/review-a.md, SHA-256
  3c4413b62c794f64cf515c463d60df311732c3ee5b428ed9d3f4df0c7a2a5e64.
- reviews/review-b.md, SHA-256
  442e0cd5652ca1fa7323cae4ba5704e95318cdf026f7b9f02970ab160c5bb936.

The reviews independently checked raw identities, six registration pins, public
interface compatibility, information boundaries and fixture arithmetic. Native
job assignment, blocked pipes, descendant termination and cleanup remain future
implementation obligations. No implementation, test execution, timing result or
poker-strength result follows from these design verdicts.

## Exact source opening

Adopt the brief's criteria, design's exact input/state/wire/process/result
contracts, and source-opening-proposal.md's exact additions, public imports,
registration exceptions, acceptance population and stop rules. Add only
tools/v0a_table_host.py, the two named test suites and four named table fixtures.
No src/pontius or older tool byte changes. Preserve ADR-0496's completed seal.

The host's semantic action application is distinct from the sealed event
adapter's local-byte delivery receipt. No acknowledgement is added to the bot
wire and no receipt, accounting scope, 15-second action wall or reserve changes.
An applied action survives a later protocol or cleanup failure; success requires
the complete hand/session/EOF/exit/cleanup conjunction and matching settlement.

Use only the public Pontius imports and standard-library modules enumerated in
the proposal. The complete deal belongs to the dealer, never to the controlled
policy or opponent selectors. The sole admitted private CPython dependency is
Popen._handle for native job assignment; no private Pontius access is opened.
The fixed cooperative bootstrap waits for successful job assignment before bot
execution. Its feasibility is a design conclusion, not executed containment
evidence; real Windows failure-path tests on both interpreters remain required.

Prospectively supersede CLAUDE.md rule 1 only for the six current registration
versions and exact deltas pinned in the proposal. Require all six blobs to match
before implementation. No registration bytes change in this decision. Preserve
old inventory records, test IDs, predicates, baseline edges/SCC rules and CI gates;
registration grants no capability. Analyzer inference remains known unsound and
parked under ADR-0486.

The explicit census exception includes complete derived counts, digests, reason
counts and source locations in CheckedInInventoryTests.
test_working_discovery_binds_every_entry_and_introduced_id. Compare the unchanged
real analyzer against the accepted base on both actual interpreters before
refreshing. Account for all prior and introduced records and downstream line
shifts, including those caused by expectation edits. Preserve the full assertion
chain and require the full inventory suite. Unexplained drift stops work; this
exception permits neither analyzer repair nor a standing sealed-test mutation.

## Bounds and acceptance

Retain the exact budgets: 1200 production LF lines, 1600 combined new-test LF
lines, four fixtures totaling 16384 bytes, and 200 manual registration added/
removed lines. Generated outputs and separate decision metadata are excluded as
specified in the brief. One initial source candidate and at most one bounded
correction; stop before a third, scope/budget expansion or sealed-core change.
The brief's written test allowance justification remains binding.

Future source acceptance requires both independent Tier C reviews and every
named check in the proposal: two new suites plus seventeen unchanged suites,
inventory generation check, the real boundary gate and the host's minimum
640-digit decoder controls. Run fresh D-local snapshots on actual CPython
3.11.15 first then 3.14.6, with -B -P, snapshot-root cwd/src, scrubbed environment,
module-origin preflight and absolute PONTIUS_GIT. Preserve blocked attempts and
obtain native permission for a fresh snapshot; do not fake the ownership oracle.

The three finite controls have independent expected results: fold final stacks
[200,199,198,203,200,200], passive showdown [210,198,198,198,198,198], and side-pot
payouts/final stacks [24,20,16,0,0,0] from pots 24/20/16. The design additionally
requires independently calculated tie/odd-chip expectations, information-boundary
falsifiers, causal opponent reactions, retained-action faults, strict diagnostic
validation and real gated-launch/pipe/descendant cleanup controls. These are
future correctness requirements, not passing observations.

Correctness uses fresh declared finite inputs and task identities. Host watchdogs
are source controls, not operating budgets or action timing credit. Arbitrary
deals, terminal play, multi-hand sessions, self-play, league training, performance
and strength analysis are not opened. Future training reuse is compatibility
context only. No consumed/rejected owner, operating/rehearsal/research authority,
Gate 13, analyzer repair, H32/instrumentation, campaign or compiled work reopens.

## Faithful incorporation

The adoption delta is exactly this ADR, generated STATUS and the three unchanged
design blobs. Following ADR-0495's faithful-incorporation route, metadata review
is Tier A: one fresh independent light pass and the unchanged status generator
check plus all twelve status-generation tests on both actual interpreters in
fresh exact-candidate snapshots. Any contract/scope divergence stops this route.
No design review is waived or transferred. Generate STATUS; never hand-edit it.

No production, test, registration, workflow, CI, dependency or historical artifact
changes in this decision. No implementation acceptance or operating result is
claimed. The user must authorize this exact decision candidate before commit/push.
