# ADR-0488: Source-seal the non-evidentiary v0a driver

- Status: accepted driver-only source seal upon controller approval and its separately authorized decision commit; this draft remains inactive until those conditions hold, two independent cold reviews and bounded v0a regression checks pass, no reviewed implementation byte changes, and no rehearsal or operational invocation is authorized
- Date: 2026-09-04
- Follows: ADR-0487
- Base-Commit: af90155ebd970d0be6fe26969b121bd213a7f1f2
- Source-Candidate: bdd96aa24286ba1ebcc11bfdbe7d3480fa3f4ad2
- Source-Tree: 957abe2f662395f9a00603a369444719b249ecc1
- Source-Manifest-SHA256: b085c3cba799a6563b5a9b9ba8a6b274b1f7d013079ea32cae769118c69d0c9f
- Invocation-Authority: none; no production or rehearsal execution is opened
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0488
- Front-Door-Contract: ADR-0307
- Front-Door-Revoked: ADR-0281, ADR-0468, ADR-0472, ADR-0475
- Front-Door-Active-Next: Obtain controller approval for this exact driver source seal and integration commit; after that commit, prepare the separately bound non-evidentiary rehearsal invocation with exact driver identity, interpreter, argv, environment and disjoint run root, and request execution authorization. Keep every other lane parked
- Front-Door-Blockers: this driver seal is not active before its authorized decision commit; no exact rehearsal invocation or execution authorization, rehearsal report, measured operating-budget closure or authoritative replay population exists; the inherited Windows fixture issue and ADR-0485/0486 parked lanes and zero-grant analyzer remain unchanged

## Decision

Propose accepting the exact three-file v0a-driver/r001 candidate and its bounded
review and regression evidence as a driver-only source seal. Controller approval
and the separately authorized ceremonial commit are required for effect. Neither
this working document, generated STATUS nor a frozen review ref activates a seal.
The proposed integration is exactly the three reviewed additions, this new ADR,
and regenerated STATUS.md. It changes no other accepted source or policy byte.

This closes the driver source boundary left open by ADR-0487, not its separate
executable-invocation requirement. The actual library seal remains
af90155ebd970d0be6fe26969b121bd213a7f1f2. No change to the library, fixed fixtures,
independent reader, writer, historical owners or consumed identities is admitted.

## Exact payload and behavior

The candidate's whole-row-sorted, blob-derived manifest covers exactly:

| Added path | SHA-256 |
| --- | --- |
| tools/v0a_rehearsal_driver.py | 4c91cad6b0e3ce296de656f4193b346967feca9bb769941ecb24c2903c9f16f3 |
| tests/test_v0a_rehearsal_driver.py | 89dd22ba2700b347b4745c60d099415e17b960988506eba5ab7f70e5b14fed57 |
| docs/architecture/v0a-rehearsal-driver-r001.md | 2397045c2ea71070a3d65df908da84618de6c7f5550b01f4da811cdc044c6e57 |

The driver selects only control-A or control-B and the existing empty reference
blueprint. It requires explicit correctness/rehearsal mode, a matching safe run
ID, and an existing empty non-reparse local directory named exactly as that ID.
It has no authorized mode. The sealed host publishes create-new trace.jsonl;
the driver accepts only successful complete host accounting, matching persisted
bytes and receipt digest, and independent trace replay with expected bindings.
Failures do not overwrite, delete or retry a published prefix.

Source preflight checks actual package bytes against the library seal before
import, rejects extra package files/caches, pins the existing bindings JSON, and
hashes the actual source closure plus the three driver files into the trace header.
That header manifest is distinct from the three-file review manifest above and
from the preserved r004 library payload manifest. The latter remains separately
reported as 6eb5ec280b6a8051e88d7659920ef74b46ea682a06dc80f688ed951d75f3f221.
The header source_commit is the library seal, not a claim that the new driver was
already adopted at that commit. Later invocation binding must separately identify
the actual authorized driver decision commit and these unchanged payload bytes.

The driver assumes trusted interpreter/stdlib/Git startup, a scrubbed environment
and no concurrent writers. It is not a hostile-process sandbox, global run-ID
registry, complete import proof or replacement native ownership framework.
The real clock is labeled monotonic_ns; no timing distribution, calibrated budget,
trained policy, strategy improvement or poker-strength evidence is inferred.

## Reviews and bounded verification

Two separate cold-context reviewers independently checked the frozen identity and
returned CLEAN / Specification PASS / Quality PASS / SOUND, each with zero
Critical, Important or Minor findings. Earlier design-informed checks do not count
as those reviews. Issued review identities in the permanent local packet:

- Review A: 5974af6da5cb1dc8fc910fbb1211a77ebce29495ee9ae9a2063ea5f1fd2b178d.
- Review B: 3d4b2ba8e5507446d618515e2ea5216a844a0851a4a9ad1cb27d7eba478e601d.
- Packet: D:/Pontius-handoffs/v0a-driver/r001/.

Both reviewers ran the new 12-test suite and independently chosen falsifiers on
CPython 3.11.15 first, then 3.14.6. After both CLEAN verdicts, fresh no-hardlink
detached clones of the exact frozen commit ran the driver suite plus all four
unchanged v0a suites. Each interpreter completed five commands and 194 tests:
12 driver, 45 hand replay, 53 trace, 62 replay and 22 contract-fault tests; all
passed, no skips, all exits zero. Snapshot source remained unchanged afterward.
Runs used -B -P, snapshot cwd/src, scrubbed environment, absolute Git and D-local
temporary roots under normal-user Windows permissions. Every host run used a
correctness identity, not an operational rehearsal.

Post-review results.json identities:

- 3.11: d3e1cc60971e89cf49a14df815dfadbe608a52d2afc042513e190f82395451c0.
- 3.14: 94291a198dc0a815490591331c3e4fe590827c73a557eb8fd9daa587b2d33e7d.

These receipts precede this ADR and generated STATUS; metadata checks are separate.
This decision proposes that affected v0a population as the bounded driver check,
not a repository-wide or hosted CI pass. Existing inventory and CI files are sealed
and unchanged; the new test is explicitly direct-run only, not registered there.
No new test capability grant or analyzer repair follows from this seal.

Reviewer harness newline mistakes and launcher/ownership environment refusals are
retained in the issued reports, not relabeled as product passes. The inherited
Windows numeric-handle fixture issue remains open. The prior library-seal fixture
exception is not a future waiver. Receipt-object doubles establish acceptance
rejection only, not native ownership under injected faults; sealed writer-failure
contracts are inherited, while real successful publication is directly exercised.

## Next boundary

After explicit approval and this decision's integration, prepare a separately
reviewed exact invocation: actual driver seal identity, unchanged payload, selected
fixed control, interpreter, expanded argv, scrubbed environment and fresh disjoint
rehearsal run root/ID. Request controller execution authorization before running.
This record intentionally provides no instantiated rehearsal argv or run identity.

ADR-0307 and ADR-0485/0486 remain binding. Measured operating budgets, authoritative
population and one-shot operational authority need separate closure. Gate 13 stays
rejected at revision 23; analyzer repair, H32/instrumentation, campaign and compiled
work remain parked. No result, owner, journal, launch identity or historical seal
is opened, reused or altered by driver source adoption.
