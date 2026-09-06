# ADR-0495: Open the one-hand event interface source round

- Status: accepted source-opening decision upon its separately authorized commit
- Date: 2026-09-06
- Follows: ADR-0494
- Base-Commit: 5f90279ab3d7d78fe790b115a697c52262280c0d
- Invocation-Authority: none; operating, experimental and rehearsal execution remain closed
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0495
- Front-Door-Contract: ADR-0307
- Front-Door-Revoked: ADR-0281, ADR-0468, ADR-0472, ADR-0475
- Front-Door-Active-Next: Implement the one-hand event interface; no operating or research run
- Front-Door-Blockers: source acceptance pending; operating/research execution closed

## Decision

Adopt the reviewed one-hand event-interface design r002 and open its bounded
CPU-only source implementation. A local caller loads one portable blueprint,
sends one hand's public events as they happen and receives the controlled seat's
actions before deciding its next event. This supplies a reactive integration
interface using the existing blueprint runtime. It supplies no table host,
trained policy, strategy evaluation or operating result.

This proposed decision takes effect only at its separately authorized commit.
The copied proposal documents remain exact historical inputs; their conditional
wording does not activate permissions. This ADR then activates only their exact
source scope and boundaries. A working ADR, generated STATUS or review ref does
not open implementation. Source acceptance and invocation remain separate.

## Bound design and review

Design task: v0a-event-interface-design/r002.
Candidate: f42041c4706553d1a14945f2114839bf14573685.
Base: 5f90279ab3d7d78fe790b115a697c52262280c0d.
Tree: dd7d7e3a25b4a9367eb23f329ae51b794d54d718.
Manifest SHA-256:
60709a0b50637d468323d8a0cd986899d31e18454eca307ed530b92e153dde1e.

Incorporate these reviewed blobs unchanged under
docs/architecture/v0a-event-interface-r002/:

- brief.md, SHA-256
  9a8f1d487c9b1a5608e1a0c849c96e51c483e3607314afb5d5144cf7ad2b6503.
- design.md, SHA-256
  3e348ac82d7142815b7676cd20f2cdd8181965fd27a18a5ff987f57425cc1f98.
- source-opening-proposal.md, SHA-256
  ba53277bbcf3e8409639c64879f69a3d4677f31ea1dd5772c1dae78a582ea774.

Both fresh independent Tier C reviews are CLEAN, Spec PASS, Quality PASS,
C/I/M 0/0/0 and Design SOUND. Their original reports are retained at
D:/Pontius/tmp/v0a-event-interface-design-r001/packets/r002/:

- reviews/review-a.md, SHA-256
  c17dc922db69762541c5bf49cc3365fae35a5711e9620cb018183c2668eb80da.
- reviews/review-b.md, SHA-256
  dddb21f107b4e9d63a088e516df0dc6deb4e8e15321b0969a4a9b89b1e412ee7.

The r001 accounting, raw-digest-key and aggregate-integer findings are resolved at
design level in this new candidate. The earlier findings and issued outcomes stay
unchanged. No implementation, test execution, timing result or poker-strength
result follows from design review. Future behavior remains untested.

## Exact source opening

Adopt the brief's criteria, design's exact wire/receipt/delivery/closing contract,
and source-opening-proposal.md's exact additions, imports, registration exceptions,
acceptance population and stop rules. There is one new production path,
tools/v0a_event_adapter.py, two named test suites and two named blueprint fixtures.
No src/pontius or older driver byte changes. Preserve ADR-0494's completed seal.

For this tool only, prospectively admit the raw-frame receipt boundary and local
single-write pipe mailbox in place of ADR-0485's in-memory delivery endpoint.
Admit only the private dispatch-shell dependencies named in design.md, pinned to
runtime blob 1c855b3b5e8f2d057105128733f43279b9f73990. No ledger-private access,
sample substitution, second response authority or core mutation is opened.
The 15-second action wall, 1-second reserve and inherited cutoff inequalities hold.

Adopt the explicit accounting scope: public runtime totals begin before ready,
end at the pre-publication cut, and report hand_result publication separately.
session_result is separately declared external host reporting after finalization.
Bootstrap before begin_host_accounting and final-receipt transport are outside
these totals; no full-process cost or preparation credit is claimed. For this
tool, trace_write_failed denotes host-frame serialization/write failure and
does not claim that a trace exists. Older endpoint measurements keep their meaning.

Prospectively supersede CLAUDE.md rule 1 only for the six registration versions
and exact deltas pinned in the proposal. Require all six blobs to match at opening.
No registration file changes in this adoption. Extend ADR-0486's registration-only
treatment with zero capability grants. Analyzer inference remains known unsound
and parked; no old row, assertion, legacy edge, SCC restriction or CI gate changes
outside the exact permitted registration additions. Unexplained drift stops work.

## Bounds and acceptance

Retain the exact budgets: 750 production LF lines, 900 combined new-test LF lines,
two fixtures totaling 16 KiB and 120 manual registration added/removed lines,
excluding generated outputs and separate decision metadata. One initial source
candidate and at most one bounded correction; return before a third or expansion.
The reviewed justification for the test allowance and all other stop rules hold.

Future source acceptance requires both independent Tier C reviews, real reactive
child-pipe observations, independently expected settlements, strict input/domain
and source refusal controls, clock/publication/closure faults, and every named
scoped regression check in the proposal. Use fresh D-local snapshots, actual
CPython 3.11.15 then 3.14.6, -B -P, snapshot-root cwd/src, scrubbed environment
and absolute PONTIUS_GIT. Retain minimum 640-digit conversion controls and blocked
attempts. Do not substitute a runtime, OS result or acceptance oracle with a fake.

Correctness tests use fresh declared finite inputs and task identities. This does
not admit arbitrary data, operating budgets, an authoritative research population,
rehearsal, experiments, consumed owners or public invocation beyond scoped tests.
Gate 13, analyzer repair, H32/instrumentation, campaign and compiled work stay parked.

## Faithful incorporation

The eventual adoption delta is exactly this ADR, generated STATUS and the three
unchanged design blobs. Following ADR-0493's faithful-incorporation precedent,
metadata review is Tier A: one fresh independent light pass and the unchanged
status generator check plus all 12 status-generation tests on both interpreters
in fresh snapshots. Any contract/scope divergence stops this route. No design
review is waived or transferred. Generate STATUS; never edit its content by hand.

No production, test, registration, workflow, CI, dependency or historical artifact
changes in this decision. No implementation acceptance or operating result is
claimed. The user must authorize this exact decision candidate before commit/push.
