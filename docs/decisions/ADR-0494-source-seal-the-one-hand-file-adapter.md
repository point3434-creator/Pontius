# ADR-0494: Source-seal the one-hand file adapter

- Status: accepted source-only seal upon its separately authorized decision commit
- Date: 2026-09-05
- Follows: ADR-0493
- Base-Commit: abe559511a72086791ca53cd3dfec24e49ec280b
- Invocation-Authority: none; operating, experimental and rehearsal execution remain closed
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0494
- Front-Door-Contract: ADR-0307
- Front-Door-Revoked: ADR-0281, ADR-0468, ADR-0472, ADR-0475
- Front-Door-Active-Next: Select the next bounded source task; no operating or research execution
- Front-Door-Blockers: operating budgets, authoritative population and invocation remain closed

## Decision

Accept the exact reviewed one-hand file adapter implementation r003 as a CPU-only
source asset. This closes source acceptance opened by ADR-0493. A scripted hand
JSON file and portable blueprint feed the existing ReplayHost; the adapter checks
the persisted trace independently and emits a concise actions/settlement summary.
Choosing these correctness inputs requires no Python edits. This is not a trained
policy, interactive opponent, strategy evaluation or operating result.

Effect requires the separately authorized decision commit. A working ADR,
generated STATUS, review ref or passing test run does not activate this seal.
Incorporate the exact 16-path payload below, this new ADR and generated STATUS
only. No workflow-rule adjustment or further implementation change belongs here.

## Bound source identity and exact scope

Task: `v0a-hand-adapter-impl/r003`.
Commit: `2ac3f225ffaf5b941c80ce0d108e9c4dfadd640b`.
Base: `abe559511a72086791ca53cd3dfec24e49ec280b`.
Tree: `5b2315ea16e8a4e41525d98797cb29e41abd0569`.
Manifest SHA-256:
`094d3c761af6dfec2734b46e262804309157a4cf2b8617094905f4f3a91e7fea`.

These paths must have the candidate's raw frozen blob bytes:

- `.github/workflows/ci.yml`
- `src/pontius/hand_scenario/__init__.py`
- `src/pontius/hand_scenario/codec.py`
- `tests/fixtures/hand_adapter/raise_blueprint.json`
- `tests/fixtures/hand_adapter/raise_scenario.json`
- `tests/fixtures/hand_adapter/showdown_blueprint.json`
- `tests/fixtures/hand_adapter/showdown_scenario.json`
- `tests/test-inventory.json`
- `tests/test-profiles.toml`
- `tests/test_hand_adapter_boundary.py`
- `tests/test_hand_scenario.py`
- `tests/test_inventory_and_profiles.py`
- `tests/test_v0a_hand_adapter.py`
- `tools/check_stabilization_boundaries.py`
- `tools/generate_test_inventory.py`
- `tools/v0a_hand_adapter.py`

Adopt only ADR-0493's closed scenario admission, immutable fixture adaptation,
raw source/file admission, single host call, independent persisted-byte acceptance,
typed refusal and compact summary contract. The library runtime, old driver,
blueprint codec, immutable blueprint and prior decisions remain byte-identical.
No dependency, helper module, operating mode or policy search is added.

The six registration exceptions remain confined to ADR-0493's opened scope.
Every one of the 2854 prior inventory rows is preserved; 13 new methods are
registered. Capability bindings remain zero. Generator inference stays unchanged
and known unsound under ADR-0486; registration does not establish analyzer safety.

Record the controller's two explicit implementation extensions: readable new-test
capacity increased from 400 to 500 LF lines, and one additional registration-only
r003 round was authorized after r002's final acceptance failure. They do not
grant further rounds, new files, features or a standing budget exception.
Final use: 359/500 production lines, 480/500 new-test lines, four fixtures totaling
7596/16384 bytes and 91/100 manually added/removed registration lines.

## Review lineage and final acceptance

The substantive anchor is `v0a-hand-adapter-impl/r002`, commit
`d840d2f8e5461217d171506a2c6d14360dec3b1e`, manifest
`ed24914eaa7a5c0d387ee6630ae06b50d1143b5384182af61f15fe130c2a13a1`.
Its two independent Tier C reports are CLEAN, Spec PASS, Quality PASS,
C/I/M 0/0/0, Design SOUND. Original issued reports are retained unchanged under
`D:/Pontius/tmp/v0a-hand-adapter-impl-r001/packets/`:

- `r002/reviews/review-a.md`, SHA-256
  `1c6c7470596d28fcf80d71663a156d1d010038ccce465de0dab4d63735170a2b`.
- `r002/reviews/review-b.md`, SHA-256
  `8ad81dfba420713905b2a9138b5f31166474d68537cf571ed164b4667b280402`.

r002 subsequently failed final acceptance on both interpreters: a test's literal
profile-file tuple had the correct population but not the existing generated
ordinal order. r002 remains a failed final-acceptance candidate. r003 changes
only four removed/four added physical lines within that tuple. All 35 names and
multiplicities, bytes outside the tuple, subsequent method positions, generated
data, production code and assertions remain unchanged. No test predicate is weakened.

Under ADR-0492's qualified-mechanical route, an independent non-author verified
the complete cumulative delta, source-position and generated-data consumers,
preserved acceptance meaning and closure. The result is QUALIFIED, CLEAN,
C/I/M 0/0/0, Design SOUND, not another substantive cold pass:

- `r003/reviews/mechanical-verification.md`, actual issued-file SHA-256
  `3bbe1928b9f406b17d4a11cce700b3bca35215dca6b1e3d1c123f34d34e2103e`.

That 9683-byte original report contains a stale embedded self-hash; it is
preserved, not silently edited. `r003/reviews/identity.md` records the correction.
Only the externally recomputed SHA-256 above binds the issued report here.
Candidate and anchor identities reproduce. The review's sandbox-limited checks
are distinguished from the coordinator's native exact-candidate executions;
no blocked development launcher is relabeled as an independent execution.

After qualification, all 22 acceptance commands passed on CPython 3.11.15 first,
then CPython 3.14.6. Per interpreter, 19 named suites reported 508 tests: 507
passed and one unchanged POSIX directory-descriptor mutation test was skipped
on Windows; zero failures or errors. Three consistency commands also passed.
The full inventory suite passed 91/91. The separate minimum decimal-conversion
setting control passed 4/4 on each interpreter at `int_max_str_digits=640`.

All runs used fresh exact-candidate D-local snapshots, actual interpreter/module
preflights, -B -P, snapshot-root cwd/src, scrubbed environments and absolute Git.
Native permissions were used where the existing hard-link fixture required them.
The final acceptance record and all 46 final command receipts are retained in
`r003/checks/`; `post-clean-summary.json` indexes the population and limits.
The complete disposition is `r003/disposition.md`, SHA-256
`aeb965f35d5bab6171cb73dd3e4ce7b3ffd93a8ecc8ba7220f379af6b1df589d`.
These are bounded local results, not a hosted CI or Ruff pass. Earlier failures,
environment-limited attempts, candidates, probes and original reviews remain intact.

The source receipts predate this ADR and STATUS. Following ADR-0491's faithful
incorporation precedent, integration metadata must separately pass one fresh
independent Tier A light review, the unchanged status generator check and its
complete 12-test suite on 3.11.15 then 3.14.6 in fresh snapshots. Verify all
16 payload blobs against r003 and the complete 18-path integration delta.
A mismatch stops incorporation. This metadata review neither replaces the two
Tier C reports plus mechanical qualification nor creates a review waiver.

## Next boundary and exclusions

Select the next bounded source task separately. This seal does not authorize
a rehearsal, operating hand, experiment, arbitrary data use, policy selection,
timing measurement or strategic claim. Correctness fixtures are not an admitted
operating population; source caps are not measured operating budgets.
ADR-0307 and the unadmitted operating boundaries in ADR-0485/0489 remain binding.
Gate 13, capability-analyzer repair, H32/instrumentation, campaign and compiled
work remain parked. No consumed owner or rejected scientific identity is revived.
