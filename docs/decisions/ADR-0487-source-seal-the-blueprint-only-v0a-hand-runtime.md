# ADR-0487: Source-seal the blueprint-only v0a hand runtime

- Status: accepted library-only source seal upon its separately authorized decision commit; exact r004 source and r007 core are preserved, bounded CPU acceptance is complete, the inherited Windows fixture caveat remains open, and no rehearsal, invocation, timing, strategy, or strength result is authorized or asserted
- Date: 2026-09-04
- Follows: ADR-0486
- Base-Commit: bb959371eec17e76ab46ee6e42f1bac49c26d54a
- Source-Candidate: fe1e2fc68675c6c92a1263450b455011b5987207
- Source-Tree: 27fa787e80f504f17233c29961d9df545f8eb7dd
- Source-Manifest-SHA256: 6eb5ec280b6a8051e88d7659920ef74b46ea682a06dc80f688ed951d75f3f221
- Core-Candidate: ddea6efbeb55cb8b71da1ebd5a359a0c2c901cf1
- Legacy-Baseline-Blob: 5fe6ee47f3380b65887b528efef05b72c8e6ac0a
- Source-Bindings: docs/architecture/v0a-increment-1-source-bindings.json
- Source-Bindings-SHA256: 4136020b369eabcd1dd7c160a7b4f9dd05d9fc587fc8276993cc807b9f9e034b
- Invocation-Authority: none; the production identity remains reserved and unopened
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0487
- Front-Door-Contract: ADR-0307
- Front-Door-Revoked: ADR-0281, ADR-0468, ADR-0472, ADR-0475
- Front-Door-Active-Next: After the authorized source-seal commit, prepare a separately identified and reviewed non-evidentiary rehearsal driver with exact argv, disjoint identities and run root; request controller authorization before execution. Keep all other lanes parked. Measured operating budgets, authoritative replay population and one-shot invocation authority remain separate later decisions under ADR-0485
- Front-Door-Blockers: no rehearsal driver/argv, rehearsal report, measured operating-budget closure, authoritative replay population or invocation authority exists; inherited Windows fixture reliability remains open; the analyzer remains known unsound with zero grants, Gate 13 remains rejected at revision 23, and the research blockers and parked lanes of ADR-0485 and ADR-0486 remain unchanged

## Question

Can the exact reviewed blueprint-only increment-one library be source-sealed
without reopening the preserved core or the parked analyzer, mistaking ordinary
correctness checks for a campaign, or inventing an operational launcher?

## Decision

Accept the exact r004 library source and its bounded CPU acceptance. This
records the controller's approval of the acceptance disposition, including the
inherited fixture caveat and the library-only seal boundary. It takes effect as
a source seal only at the separately authorized ceremonial decision commit.
A working copy, review ref, generated STATUS, or this uncommitted record does
not itself activate the seal. No experimental owner is admitted.

The source candidate adds the six `pontius.v0a` modules and four test suites
byte-identically from r007. Its remaining scope is registration, narrow origin
and import boundaries, four direct CPU CI gates, and a typed refusal for the
baseline helper binder's unrepresentable positional/default alignment. The
expanded descriptor-provenance analyzer is not adopted. The refusal appears
before sensitivity filtering at both consumers and grants no capability.
ADR-0486's general analyzer-unsoundness disposition is unchanged.

The source manifest binds all 17 files changed from the stated base. The full
source tree binds the inherited repository dependencies, including package
initialization; it is not limited to the six directly allowed runtime imports.
No inherited kernel, historical replay, legacy dependency baseline, dependency
lock, or retained evidence byte changes. The five manual registration/boundary/
CI files contain 357 additions and 29 removals, below the 600-addition cap.

## Library, configuration, and independent reader

The bound JSON is an exact copy of the materialization independently compared
on CPython 3.11.15 and 3.14.6. It records both complete fixture declarations,
materialized suit-renamed deals, configuration identities, schema names, API
signatures, and 31 observed import origins with raw byte counts and SHA-256s.
Its scope field describes that read-only capture, not the later seal's status.
The observed origin list is not a proof of arbitrary dynamic reachability; the
complete Git source tree and reviewed import policy are the source boundary.

- Event schema: `pontius-v0a-event-v1`.
- Trace schema: `pontius-v0a-trace-v1`.
- Host API: `pontius.v0a.replay.ReplayHost.run`, with keyword arguments
  `destination=None` and `run_root=None`, returning `ReplayOutcome`.
- Independent reader: `pontius.v0a.replay.verify_successful_trace`, accepting
  raw content and independently supplied fixture, blueprint, source commit,
  source manifest, expected mode, and expected clock kind.

Control A's configuration SHA-256 is
`69861c84550f07d2d72ae1466f90a838a1ceaa345645376d7797a129a9a9f0bf`;
control B's is
`762fb7122087739a2d9c16b5749568165919e8318e220dca5338efa0ee4125f2`.
The materialized JSON also binds their declared payouts, pots, and action
counts; a fixture configuration digest alone is not substituted for that full
declaration. These remain correctness controls, not an authoritative campaign
population or statistically independent observations.

**Entry-point/argv disposition.** ADR-0485's source-seal requirement is applied
here to the library API and its independent reader. There is no standalone CLI
or owner argv in r004; this library-only seal neither supplies nor authorizes
one. Before rehearsal, its separate driver must receive identified source,
exact argv, run-root/identity constraints, applicable review, and controller
execution authorization. A source-seal claim for an operational workflow is
not made by this record. New driver code may not be inserted into these sealed
library bytes. This explicit boundary resolves the library packaging item;
it does not remove the future executable entry-point binding requirement.

The source-candidate commit and manifest above identify the reviewed payload,
not an authorization token or a self-referential final commit hash. Any future
driver must bind both the actual authorized seal commit and the preserved
source payload identity without confusing a review snapshot with a decision.

## Reviews and bounded acceptance

The r007 core's existing reviews remain binding to its exact source. The r004
consolidation received two independent CLEAN / Spec PASS / Quality PASS /
SOUND reviews with zero Critical, Important, or Minor findings. Neither is
represented as a new whole-core design review. The issued r004 report hashes:

- Review A: `d6dc616d2c5d24ce4737b01a067481c07a37d1969bf8ca027283e24594c71561`.
- Review B: `f67b53dde991cd7867d14c5097cfadbeadd21a0885364e9d91fb60688803aad0`.
- B's append-only count correction:
  `c28bee942de1722348a9a159aaf98f7271e5dc26402099920f9d05cdf0aae194`.

The controller accepts the complete existing direct CPU CI hard-gate population,
four v0a suites, and six unchanged direct-kernel suites as this increment's
permitted broader correctness wall under ADR-0485. This scoped ruling does not
close repository-wide scientific profiles or their capability-approval backlog.

Fresh disposable D:-local snapshots ran 3.11.15 first, then 3.14.6, with `-B -P`,
snapshot cwd and `PYTHONPATH`, scrubbed environment, D:-local temporary roots,
and absolute bound Git. Each completed 23 commands and 19 whole suites, with
526 tests collected: 525 passed and one existing POSIX-only skip on Windows.
All command exits were zero, and the 17 source hashes were unchanged before
and after. The inventory suite ran all 88 tests on both slots. There was no
retry of a failed command in this acceptance set.

The source acceptance report is retained with SHA-256
`dfbe1a6b3db4d9480d0994744f0d7fc34ba022a3002855600a9ec6a01e91db37`.
Floor `results.json` SHA-256:
`bfd918a728aca921806f9c050ae0f37e265f87202729177b4925224b1897f74e`.
Development `results.json` SHA-256:
`32e9545edb009f001a37651197424e0dc63961a590e26a6c27986815fbbcb448`.
These receipts precede the three metadata files added by this seal record;
metadata verification is separate and must not be attributed to those runs.

The permanent coordination packet is
`D:/Pontius-handoffs/v0a-consolidation/r004/`, with issued reviews, acceptance,
controller ruling, exact identities and copied check receipts. The core packet
remains at `D:/Pontius-handoffs/v0a-i01-ab/r007/`. Original local artifacts and
failed receipts remain in place; publication is not deletion or reclassification.

## Inherited fixture caveat

An earlier development inventory run failed the numeric Windows handle-reuse
fixture before establishing its intended reused-handle fault schedule. An exact
bb95937 baseline diagnostic independently failed the same assertion. Both
fixture methods are unchanged, and the precise reason a process did not reuse
the selected handle number remains unestablished.

The controller accepts this as an open inherited fixture-reliability issue,
not a required correction to r004. No assertion is waived, no test is skipped,
no failed receipt is relabeled, and no fixture repair is claimed. Both current
complete acceptance runs and the independent reviewers' complete normal-user
runs passed. A later failure remains a failure requiring disposition, not
permission to retry until green. The candidate report and review-outcome record
retain the earlier failures and the reviewer process-stop coordination caveat.

## Continuity, next step, and claims boundary

This is one library source-seal decision, not a rehearsal or operating opening.
All production attempt, journal, result and launch identities remain unopened.
The protocol `pontius-v0a-hand-replay-v1` stays reserved. Rehearsal must use the
disjoint rehearsal namespace, a reviewed driver and a separately authorized run.
Measured operating budgets and the authoritative replay schedule/population
require their own append-only closure before any one-shot invocation authority.
No operating limit is invented from these correctness checks.

ADR-0307's action wall and emission reserve, ADR-0485's contracts and kill
criteria, the unchanged historical trust chain, and ADR-0486's zero-grant
registration and parking dispositions remain binding. Gate 13 stays rejected
at revision 23; analyzer repair, H32/instrumentation, campaign and compiled work
stay parked. Consumed owners remain permanently closed.

No hosted CI run, guarded scientific profile, GPU run, dependency installation,
historical owner, rehearsal, timing distribution, trained blueprint, poker
strength, strategy improvement, or authoritative complete-hand result is
asserted. This library closes an integration-source boundary, not the research
questions or operational gates that follow it.
