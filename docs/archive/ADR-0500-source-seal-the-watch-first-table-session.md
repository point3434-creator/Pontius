# ADR-0500: Source-seal the watch-first table session

- Status: accepted source-only seal upon its separately authorized decision commit
- Date: 2026-09-06
- Follows: ADR-0499
- Base-Commit: 470f654c187b2c1f0fff8cc1a953edbcbd225ef1
- Invocation-Authority: none; operating, experimental and rehearsal execution remain closed
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0500
- Front-Door-Contract: ADR-0307
- Front-Door-Revoked: ADR-0281, ADR-0468, ADR-0472, ADR-0475
- Front-Door-Active-Next: Select bounded operating-entry task; operating/research closed
- Front-Door-Blockers: operating budgets, authoritative population and invocation remain closed

## Decision

Accept the exact reviewed watch-first table-session r001 as a CPU-only source
asset, closing the implementation acceptance opened by ADR-0499. The new terminal
tool composes the sealed one-hand host across a finite explicit schedule. Pontius
plays five existing simple opponents; completed stacks carry and the button rotates.
During each hand the terminal shows the bot's own cards, the public board and actual
actions. Enter/n and q operate between hands. Automatic mode shares the lifecycle;
automatic JSON mode produces one closed result.

Effect requires the separately authorized decision commit. A working ADR,
generated STATUS, review ref or passing test run does not activate this seal.
Incorporate only the exact eleven source payload blobs below, this new ADR and
generated STATUS. No further implementation or workflow-rule change belongs here.

## Bound source identity and exact scope

Task: v0a-table-session-impl/r001.
Commit: ea06060d5f50753d97e897223dd8db47a4971bf5.
Base: 470f654c187b2c1f0fff8cc1a953edbcbd225ef1.
Tree: 14bb652c9b4df0fba92add409993657d1c17b228.
Manifest SHA-256:
186fcbd9060a28ea47c2f7b3b6b1f7d351b1b8f05ce220de80bb9ed3442a66c5.

These paths must have the source candidate's raw frozen blob bytes:

- .github/workflows/ci.yml
- tests/fixtures/table_session/below_blind.json
- tests/fixtures/table_session/two_hands.json
- tests/test-inventory.json
- tests/test-profiles.toml
- tests/test_inventory_and_profiles.py
- tests/test_v0a_table_session.py
- tests/test_v0a_table_session_boundary.py
- tools/check_stabilization_boundaries.py
- tools/generate_test_inventory.py
- tools/v0a_table_session.py

Adopt ADR-0499's exact input, admission, lifecycle, projection, output and failure
contracts. The tool binds its raw source and the exact sealed host before loading
that host through the one fixed compile/exec route. One admitted Source/Modules
context is reused; each hand gets fresh table, failure ledger, wire consumer and
native child ownership. Every scheduled deal is validated before any launch.
Canonical per-hand input is derived in memory using carried stacks and button.

Accept and carry only after inherited completion, final source/input checks,
successful native cleanup, actual child exit zero and complete capture. Acceptance
precedes settled display. A failed hand retains the exact applied-action prefix
and null settlement; later failure cannot erase an accepted earlier hand.
Schedule exhaustion precedes the between-hand insufficient-stack predicate.
Quit/EOF, invalid commands, source/input drift, interruption and failures stop
before another launch. Final revalidation also applies after quit/EOF.

Recognized cancellation is a KeyboardInterrupt observable by the caller. Primary
interrupted produces status interrupted and exit 130; distinct later failures
remain secondary. Constructor/finish interruptions consumed by the sealed host
retain its public phase or cleanup_failed and exit 1. No cause introspection,
signal observer, private-host access or replacement native cleanup is introduced.
Final publication failure separately exits 1 without retrying the document.

Immutable primitive/tuple projections expose only own cards and current public
state. Updates follow completed exchanges; the action cursor advances before
one-shot publication. Failed-hand unrendered actions may appear only after cleanup.
Text line/session and final JSON bounds remain those in the accepted design.
No blocked-output liveness or newly measured operating budget is claimed.

The host remains raw blob 0faa101f9be9940f9ae935df51f8c79e2eeb2b15. Its inherited
source base is 1329c2c201bbf2f396946f2ebf460ee944ae4ece. All src/pontius bytes,
prior adapters/driver, sealed host and old empty blueprint remain unchanged.
Existing wire, origin, native process, action/timing/accounting and receipt
semantics are preserved, including the 15-second action wall and inherited reserves.
This source addition introduces no private CPython or new package dependency.

The six registration exceptions remain exact and bounded. All 2942 old inventory
rows and 432 old payloads remain unchanged; 30 test methods and two CPU payloads
are added. Complete old analyzer observations remain in order with verified source
locations: 346 analyzed rows, 4140 helper edges, 591 decoys and 582 blockers.
New-suite additions are 35 analyzed rows, 56 helper edges and 56 blockers, with
no new decoys. All 141 expanded capability rows remain exact. Full derived counts,
digests, reason counts and downstream source-position assertions pass on both
actual interpreters. Old assertion predicates, IDs, rules and CI gates remain.
Capability bindings remain zero; analyzer inference is unchanged and remains
known unsound and parked under ADR-0486. No standing mutation exception follows.

Final use: 436/700 production LF lines, 883/1200 combined new-test LF lines,
two fixtures totaling 2345/8192 bytes and 87/200 manual registration add/remove lines.

## Review lineage and final acceptance

Both independent fresh Tier C source reviews are CLEAN, Spec PASS, Quality PASS,
C/I/M 0/0/0 and Design SOUND, with no required correction. Original reports remain
unchanged under D:/Pontius/tmp/v0a-table-session-impl-r001/packets/r001/:

- reviews/review-a.md, SHA-256
  cf51c08223d58a7379335e2d8b19554f92c8dec3bae49c199a1ce6b0b345812e.
- reviews/review-b.md, SHA-256
  45a39d7646861adfc868a25017df74743974c4d16d0112054564aedd76793873.

r001 is the initial and only issued source candidate. Original development
failures, diagnostics, snapshots and receipts remain retained. A malformed-stack
control exposed a TypeError before typed validation; the exact list-type check
corrected it. Native test development corrected an invalid nonzero kill-on-close
exit assumption using a real retained-handle exit oracle, and adjusted the late
fault trigger to the intended sixth action. These test-helper failures are not
relabeled as production defects or passing runs. Initial missing-tool/presentation/
registration REDs and census-refresh mismatches remain distinct from later passes.
Review A's initial identity-utility path error occurred before Python execution;
its corrected utility and both exact-candidate new suites passed. Review B's four
selected native cuts passed in its own fresh exact-candidate floor snapshot.

After both reviews, all 24 declared acceptance commands passed on CPython
3.11.15 first, then 3.14.6. Per interpreter, 21 named suites reported 451/451 tests
passing with zero failures, errors or skips, including all 91 inventory tests.
The additional session decoder control passed at int_max_str_digits=640.
Generator --check and the real stabilization boundary gate passed.

All 48 commands ran from fresh exact-r001 D-local snapshots with genuine
interpreter/module-origin preflights, -B -P, snapshot-root cwd/src, scrubbed
environments and absolute PONTIUS_GIT. Native permissions were used where needed.
Under the source packet root above, final evidence remains at:

- checks/final-acceptance-summary.json, SHA-256
  36572ba80df06791420582f680ecf9b35aea14a69ea76ba38531392cb09ad01d.
  This indexes all original final receipts, hashes and the exact population.
- disposition.md, SHA-256
  dae539049d4de09d7d668c7680598fbc8fbb7950bcd0afea6490a9380200f0c7.

These are bounded local correctness results, not hosted CI, Ruff, performance or
playing-strength results. Independent literal full-action, stack and pot arithmetic
supplements agreement with shared kernels. Hidden-card/future-deal permutations,
live terminal input and retained native root/descendant handles exercise the new
caller boundaries. Actual short writes are exercised; the maximum JSON ceiling
is structurally bounded rather than populated by a manufactured giant game result.
No exhaustive cancellation-at-every-bytecode or arbitrary operating-liveness claim.

The source receipts predate this ADR and STATUS. Following ADR-0498's faithful
incorporation precedent, metadata must separately pass one fresh independent Tier A
light review, unchanged status generator --check and all twelve status-generation
tests on 3.11.15 first then 3.14.6 in fresh exact-candidate snapshots. Verify all
eleven raw source incorporations and the complete thirteen-path integration delta.
Any mismatch stops incorporation. Metadata review replaces no Tier C review and
creates no source-review waiver. The user separately authorizes the exact commit.

## Next boundary and exclusions

Select the bounded operating-entry task separately. This seal grants no operating
or rehearsal session, arbitrary deal/population, random-deal generation, human
poker action input, seat elimination, rebuy, policy selection, timing study or
strategic claim. Correctness fixtures are not an admitted operating population;
source watchdogs are not measured operating budgets. Future neural, self-play and
league reuse remains compatibility context. No training or strength evaluation is
introduced. ADR-0307 and the unadmitted operating boundaries remain binding.
Gate 13, capability-analyzer repair, H32/instrumentation, campaign and compiled
work remain parked. No consumed owner or rejected scientific identity is revived.
No cleanup or ref retirement is authorized by this decision.
