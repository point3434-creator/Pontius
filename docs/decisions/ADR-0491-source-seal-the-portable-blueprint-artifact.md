# ADR-0491: Source-seal the portable blueprint artifact

- Status: accepted source-only seal upon its separately authorized decision commit
- Date: 2026-09-05
- Follows: ADR-0490
- Base-Commit: c4af7f61270b583eb3a3c6d8b3b7e4c49637dc98
- Invocation-Authority: none; operating, experimental and rehearsal execution remain closed
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0491
- Front-Door-Contract: ADR-0307
- Front-Door-Revoked: ADR-0281, ADR-0468, ADR-0472, ADR-0475
- Front-Door-Active-Next: Select the next bounded source task; no operating or research execution
- Front-Door-Blockers: operating budgets, authoritative population and invocation authority remain closed

## Decision

Accept the exact reviewed portable-blueprint codec r002 with the separately
reviewed Windows handle-fixture r002 as a CPU-only source asset. This closes the
codec source acceptance opened by ADR-0490 and the inherited numeric handle-reuse
fixture blocker within its tested Windows scope. No poker-strength, timing,
training, policy-selection or operational result follows from source acceptance.

Effect requires the separately authorized decision commit. A working ADR,
generated STATUS, review ref or passing test run does not activate this seal.
The integration changes the exact 12-path combined payload below, this new ADR,
and generated STATUS only. Workflow-rule adjustments are not part of this decision.

## Bound source identities

Codec task: `v0a-blueprint-artifact-impl/r002`.
Commit: `5e56e4454f7b8ccb360d3e36245abc33318349bb`.
Base: `c4af7f61270b583eb3a3c6d8b3b7e4c49637dc98`.
Tree: `dc18ed133504fe6c7677b494bcefba311cc73704`.
Manifest SHA-256:
`6d5e14a64466f8aaa874d4bdf62ada439703eb74911a7b4dc4445c14b2af13b5`.

Fixture task: `windows-handle-fixture/r002`.
Commit: `c7de23de276c50463d831f3983fede82a5400ce8`.
Sole parent: the codec commit above.
Tree: `014ee05a5014181bd63471247e5ee09607bb2346`.
Its two-path manifest SHA-256:
`f5e06a5fa9d0fdf37888d29f8bfe6b395b6fc40a4c6f87258f66c95aa17421ed`.

The fixture candidate already contains the complete combined payload. Relative
to the integration base, exactly these paths have its frozen bytes:

- `.github/workflows/ci.yml`
- `src/pontius/blueprint_artifact/__init__.py`
- `src/pontius/blueprint_artifact/codec.py`
- `tests/fixtures/blueprint_artifact/history_control.json`
- `tests/fixtures/blueprint_artifact/raise_control.json`
- `tests/test-inventory.json`
- `tests/test-profiles.toml`
- `tests/test_blueprint_artifact.py`
- `tests/test_blueprint_artifact_boundary.py`
- `tests/test_inventory_and_profiles.py`
- `tools/check_stabilization_boundaries.py`
- `tools/generate_test_inventory.py`

The fixture changes only the inventory and its test module relative to codec
r002. It preserves every prior entry and adds exactly three control tests.
All other codec candidate blobs remain byte-identical. Neither the old codec
candidate nor any rejected candidate, review, receipt or historical seal changes.

## Exact adopted scope and prior controller extensions

The codec implements the ADR-0490 design: non-executable portable policy bytes,
complete immutable keys/actions, exact schema/scalar admission, deterministic
encoding and typed refusal. It does not alter the runtime or driver, add an
executable launcher, train a policy, or confer capability grants.

Carry forward the two explicit controller extensions reviewed with codec r002:
the exact existing rehearsal-driver origin and its three existing internal
imports are admitted by the boundary checker, and its unchanged test suite is
registered alongside the two codec suites. No extra driver CI step, sibling
origin, forbidden import, analyzer inference or driver behavior is admitted.
Their bound input records in the codec packet are:

- `inputs/driver-amendment-authorization.md`, SHA-256
  `0d5cd53eb456a47a0ff346034fdfad173c77a39e37b030c99205c4913eeb2af7`.
- `inputs/inventory-amendment-authorization.md`, SHA-256
  `666d89a6708c9d749265d816d063857432be42d754b6e76ad2dbafff6ba98ea3`.

Prospectively adopt the separately controller-approved fixture exception for
the exact r002 test-module and generated-inventory bytes. It extends the narrow
registration-only edit scope only to the reviewed three handle-reuse helpers,
their test-local adapter and controls, and derived census/registration bytes.
Historical sealed bytes remain unchanged in their original commits.

The rule-8 exception controls numeric reuse at the Windows API boundary; it does
not substitute the writer or cleanup implementation. Real native resources,
the production ownership/transaction paths, independent raw-native identity and
liveness observations, and deliberately bad replay controls remain required.
It covers the existing 14 schedules, not all Windows allocator schedules.
No general helper-double waiver or workflow-rule amendment is adopted.

The generator's registration additions do not repair its known-unsound analyzer.
ADR-0486's zero-grant and parked-analyzer disposition remains. The library and
driver seals, runtime bytes, old test method bytes outside the authorized fixture
scope, old decisions, research standing and consumed identities remain unchanged.

## Review and acceptance evidence

Codec r002 and fixture r002 each have two independent final implementation
reviews: CLEAN, Spec PASS, Quality PASS, C/I/M 0/0/0, Design SOUND. Their issued
reports are retained unchanged at these task-local paths:

- `D:/Pontius/tmp/v0a-blueprint-artifact-impl-r001/packets/r002/reviews/a/review.md`,
  SHA-256 `e84ad0fffd6378f19ed4e7ccd20b599d381365d544f96fed86894fdf18846588`.
- `D:/Pontius/tmp/v0a-blueprint-artifact-impl-r001/packets/r002/reviews/b/review.md`,
  SHA-256 `af42a16c4fa2c9d0258ca37298532fd8875e9381f77864158594532713acda94`.
- `D:/Pontius/tmp/windows-handle-fixture-r001/reviews/r002-a/review-a.md`,
  SHA-256 `ce809df1de640e493a0ac88981e5463938be7cd0a2829b935d670d30e3243700`.
- `D:/Pontius/tmp/windows-handle-fixture-r001/reviews/r002-b/review-b.md`,
  SHA-256 `d5f3cbffaff07f8f17bee0a0bc77954372033582b71aceeb498caebf163ef15e`.

After both fixture correction reviews were CLEAN, the complete 19-command codec
acceptance population passed on CPython 3.11.15 first, then CPython 3.14.6.
Per slot: 495 unittest methods, 494 passed and one existing POSIX-only skip,
plus three consistency commands; zero failures or errors. Both full 91-test
inventory suites passed. No broad command was retried; source bytes did not
change between slots. All snapshots matched the frozen payload afterward.

The complete command population, raw receipt locations, limits and post-run
audit are at `D:/Pontius/tmp/windows-handle-fixture-r001/packets/r002/acceptance.md`,
SHA-256 `5f3ce1d41b98fbf818c12a1825bd20f6c7f132d37015370ed4ba7e01cb800126`.
Its `acceptance-evidence.sha256` binds the 38 receipts, two summaries and three
runner/audit scripts; SHA-256
`25885f195b7d513f115a9706a0cdef83b24647852e117e46e519f6c2d9ebbf93`.

Those runs used fresh D-local snapshots, exact interpreter/module preflights,
`-B -P`, snapshot-root cwd/src, scrubbed environments and absolute Git.
They establish bounded local acceptance, not a hosted CI pass. Earlier failed
acceptance, baseline and environment-limited attempts remain failures at their
original identities. Ruff was unavailable; no Ruff pass is claimed. Added-line
width and source hygiene were checked directly.

These receipts predate this ADR and STATUS. Integration metadata must separately
pass one fresh independent Tier A faithful-incorporation review and the unchanged
status generator check and its 12-test suite on 3.11.15 then 3.14.6 in isolated
snapshots. That review does not replace the prior Tier C implementation reviews.
No new source or review waiver is created by treating exact incorporation as
metadata. A payload mismatch stops integration rather than inheriting acceptance.

## Next boundary and exclusions

This source seal completes portable artifact engineering acceptance, not the
research project. Select the next bounded source task separately. No new lane,
policy search, rehearsal, operational invocation or experiment opens here.
Operating budgets, authoritative populations and one-shot authority remain
unadmitted under ADR-0485/0489 and their dependencies. ADR-0307 remains binding.
Gate 13, analyzer repair, H32/instrumentation, campaign and compiled work remain
parked. There is no newly asserted poker-strength or strategic-improvement result.
