# ADR-0496: Source-seal the one-hand event interface

- Status: accepted source-only seal upon its separately authorized decision commit
- Date: 2026-09-06
- Follows: ADR-0495
- Base-Commit: 09f2f6eb8b564b7c5928eff43f00bbd0a802ff9e
- Invocation-Authority: none; operating, experimental and rehearsal execution remain closed
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0496
- Front-Door-Contract: ADR-0307
- Front-Door-Revoked: ADR-0281, ADR-0468, ADR-0472, ADR-0475
- Front-Door-Active-Next: Select the next bounded source task; no operating or research execution
- Front-Door-Blockers: operating budgets, authoritative population and invocation remain closed

## Decision

Accept the exact reviewed one-hand event interface implementation r002 as a
CPU-only source asset. This closes source acceptance opened by ADR-0495. A local
caller loads one portable blueprint, sends one hand's public events as they
happen and receives the controlled seat's action before choosing its next event.
Existing betting, cards, policy and settlement logic retain their authority.
This supplies no table host, trained policy, strategy evaluation or operating result.

Effect requires the separately authorized decision commit. A working ADR,
generated STATUS, review ref or passing test run does not activate this seal.
Incorporate the exact 11-path payload below, this new ADR and generated STATUS
only. No workflow-rule adjustment or further implementation change belongs here.

## Bound source identity and exact scope

Task: `v0a-event-interface-impl/r002`.
Commit: `800293b1726eb906b958037a9810c981131aaef3`.
Base: `09f2f6eb8b564b7c5928eff43f00bbd0a802ff9e`.
Tree: `60490d529761df2a9b21dced7b76cef3704f99d8`.
Manifest SHA-256:
`e372c7337a36a7dacbb1e229fafdb5bcc84d13b68754f7ae70364910463e04ba`.

These paths must have the candidate's raw frozen blob bytes:

- `.github/workflows/ci.yml`
- `tests/fixtures/event_adapter/fold_blueprint.json`
- `tests/fixtures/event_adapter/showdown_blueprint.json`
- `tests/test-inventory.json`
- `tests/test-profiles.toml`
- `tests/test_inventory_and_profiles.py`
- `tests/test_v0a_event_adapter.py`
- `tests/test_v0a_event_adapter_boundary.py`
- `tools/check_stabilization_boundaries.py`
- `tools/generate_test_inventory.py`
- `tools/v0a_event_adapter.py`

Adopt only ADR-0495's strict raw-frame admission, closed event/output schemas,
single-write pipe receipt, existing blueprint dispatch and accounting/closing
contract. Frames are bounded at 16384 bytes including LF; decoding begins within
the inherited action wall after raw receipt. A short or failed publication is
UNKNOWN and never retried. Public accounting begins before ready; preparation
ends at the pre-publication cut, hand-result publication is measured separately,
and session-result is the declared external report.

The inherited source base remains `5f90279ab3d7d78fe790b115a697c52262280c0d`.
Private dispatch-shell coupling remains confined to the adopted design and pinned
to runtime blob `1c855b3b5e8f2d057105128733f43279b9f73990`. No ledger-private
access is added. Raw source admission and final revalidation remain required.
The 15-second action wall, 1-second reserve and cutoff inequalities are unchanged.
All src/pontius bytes and prior runtime/driver bytes remain unchanged.

The six registration exceptions remain confined to the opened source scope and
the controller's exact current-file expectation extensions below. All 2867 old
inventory rows are preserved; 25 new methods are registered. Capability bindings
remain zero. Generator inference remains unchanged and known unsound under
ADR-0486; these registrations do not establish analyzer safety.

Record both explicit implementation extensions: first the four-literal census
expectation patch, then the complete remaining blocker-count, reason-count and
source-location expectation patch in the same inventory test method. The first
patch's focused run failed at a later assertion; its diagnosis was incomplete.
That intermediate snapshot was never issued as r002 or accepted. The second
authorization completed the precise expectation correction within the one
already budgeted r002 round, without weakening predicates or changing test IDs.
The cumulative r001-to-r002 delta is 26 added and 24 removed lines; the other
ten payload blobs are identical. These exceptions grant no further round or
standing permission to change sealed tests.

Final use: 398/750 production LF lines, 899/900 combined new-test LF lines, two
fixtures totaling 1700/16384 bytes and 92/120 manual registration add/remove lines.

## Review lineage and final acceptance

The substantive anchor is `v0a-event-interface-impl/r001`, commit
`43dd888c1bd0c0fbce51af4554d6d2a8d480d4d4`, manifest
`4d0a4105cc1b1951e14b72c3bd8c83b4133d7e22a480833e951d68fb6d685fc8`.
Its two independent Tier C reports are CLEAN, Spec PASS, Quality PASS,
C/I/M 0/0/0, Design SOUND. Original reports remain unchanged under
`D:/Pontius/tmp/v0a-event-interface-impl-r001/packets/`:

- `r001/reviews/review-a.md`, SHA-256
  `a01e1119c1076352b397531169d55fe0366736ece7c39b6936991ce84493fa5d`.
- `r001/reviews/review-b.md`, SHA-256
  `7eba5f05e299ad4ac23f5486bc5f82f36c04696b66b7574940b1a61da613b64c`.

r001 subsequently FAILED final acceptance on both interpreters: 19/20 commands
passed, with 370/371 tests passing and one stale census assertion failing.
Its final acceptance remains failed despite the earlier CLEAN reviews. The
first four-literal intermediate correction also retains its later focused failure.
Every original candidate, review, diagnostic, failure and receipt is preserved.

Under ADR-0492's qualified-mechanical route, an independent non-author verified
the complete cumulative r002 delta, original records and source-position effects,
unchanged generated outputs, acceptance meaning and closure. All 471 original
blockers remain represented; 52 new records arise entirely in the two new suites.
The result is QUALIFIED, CLEAN, Spec PASS, Quality PASS, C/I/M 0/0/0, Design SOUND,
with no required correction. This is mechanical qualification of the original
substantive anchor, not another cold substantive pass:

- `r002/reviews/mechanical-verification.md`, externally verified SHA-256
  `50004cbd2e671e31f4b4e48f88e2528b5ad35bce5013dfb951f042935123e1ee`.

The verifier independently reproduced the original affected test and complete
observation data on actual CPython 3.11.15 then 3.14.6. Earlier r001 reviewers'
initial denied development preflights remain distinct from their later permitted
fresh-snapshot passes. No blocked attempt is relabeled as an independent pass;
there was no new blocked attempt during the r002 qualification.

After qualification, all 20 unchanged acceptance commands passed on CPython
3.11.15 first, then 3.14.6. Per interpreter, 17 named suites reported 371/371 tests
passing with zero failures, errors or skips, including all 91 inventory tests.
The additional minimum decimal-conversion controls passed 4/4 at
`int_max_str_digits=640`. Generator --check and the real boundary gate passed.

All 40 command runs used fresh exact-r002 D-local snapshots, actual interpreter
and module-origin preflights, -B -P, snapshot-root cwd/src, scrubbed environments
and absolute PONTIUS_GIT. Native permissions were used where required. Under the
packet root above, final evidence is retained as:

- `r002/checks/final-acceptance-summary.json`, SHA-256
  `d82889314b891ae6630ec6e4f9fb99d0b41f2533b1b778375c0b2aeec2d73fe6`.
  This indexes all original final receipts, their hashes and the unchanged population.
- `r002/disposition.md`, SHA-256
  `b87a81d572bea17209ba0ea806526c7a3d32ec7306f7d885227d2aa916257afd`.

These are bounded local results, not a hosted CI or Ruff pass. Expected negative
CLI diagnostics remain in the original outputs; terminal unittest summaries and
process exits determine acceptance. No failed test was reclassified as passing.

The source receipts predate this ADR and STATUS. Following ADR-0491/0494's faithful
incorporation precedent, integration metadata must separately pass one fresh
independent Tier A light review, the unchanged status generator check and its
complete 12-test suite on 3.11.15 then 3.14.6 in fresh snapshots. Verify all
11 payload blobs against r002 and the complete 13-path integration delta.
A mismatch stops incorporation. This metadata review neither replaces the two
Tier C reports plus mechanical qualification nor creates a review waiver.

## Next boundary and exclusions

Select the next bounded source task separately. This seal grants no rehearsal,
operating hand, experiment, arbitrary data use, policy selection, timing study or
strategic claim. Correctness fixtures are not an admitted operating population;
source caps are not measured operating budgets. ADR-0307 and the unadmitted
operating boundaries in ADR-0485/0489 remain binding. Gate 13, capability-analyzer
repair, H32/instrumentation, campaign and compiled work remain parked. No consumed
owner or rejected scientific identity is revived. No cleanup or ref retirement
is authorized by this decision.
