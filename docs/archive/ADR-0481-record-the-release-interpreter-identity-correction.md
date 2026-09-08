# ADR-0481: Record the release-interpreter identity correction

- Status: accepted Tier-C correction and evidence-label correction; the test-governance stack mixed 32-bit `os.stat` volume serials (CPython <= 3.11) with 64-bit `FileIdInfo` handle identities, so the generator's Git machinery, governance writer, and repository revalidation failed deterministically on the CPython 3.11 release interpreter while every recorded "isolated Python 3.11 snapshot" had actually executed on the 3.14.6 development venv; the correction uses full-width `FileIdInfo` identities on both sides of every such comparison with independent observations preserved and no replacement, reparse, ownership, or rollback check weakened, the string-decoy census is version-stable, the snapshot-runner successor asserts and records the actual child interpreter fail-closed, both independent Tier-C cold reviews returned CLEAN on the frozen manifest, the committed tree is byte-identical to the reviewed candidate, fresh disposable-snapshot suites pass on CPython 3.11.15 and 3.14.6, and the continuous-integration wall passed completely on a hosted runner's genuine CPython 3.11.9; historical results remain valid only as CPython 3.14.6 evidence, no retrospective 3.11 validation of any earlier run is implied, and no scientific result is recertified
- Date: 2026-08-30
- Follows: ADR-0480
- Correction commit: `b5df265` on master; byte-identical to frozen review candidate `3674d497d2cfce24eff3afc401147f0a2d2c89ee` (empty whole-tree diff)
- Review manifest (sorted rows, SHA-256): `9b3190a5e5c1593c73d9b6c8c289214f2ec6be46eb4bb6763b6ab992130b865b` over `tools/generate_test_inventory.py`, `tools/check_stabilization_boundaries.py`, `tools/ci_native_diagnostics.py`, and `tests/test_inventory_and_profiles.py`
- External review: two independent Tier-C cold reviews, both CLEAN, findings bound to the manifest; review ref retired after the byte-identity check
- Mechanism reference: CPython 3.12 widened `os.stat` Windows identity fields (`st_dev`/`st_ino`); on 3.11 `st_dev` is the 32-bit volume serial while `GetFileInformationByHandleEx(FileIdInfo)` reports 64 bits, so stat-derived and handle-derived identities may never be compared
- Downstream cascade closed: the identity rejection triggered rollback, rollback guards hit further mixed comparisons, cleanup went pending with the deterministic lock retained, and teardown then failed with access-denied unlinks — one root, four symptom layers
- Evidence-label correction: `task-2-run-snapshot.ps1` line 14 resolves the CPython 3.14.6 development venv; every "isolated Python 3.11 snapshot" label in the Task 2 report denotes a 3.14.6 execution, corrected by an appended report section with historical bytes preserved
- Interpreter contract: `task-2-run-snapshot-v2.ps1` takes the interpreter and expected version explicitly, asserts and records the child's executable, implementation, and full version before any payload, and fails closed on absence or mismatch; the fail-closed branch was exercised (expected 3.11 against the 3.14.6 venv threw with no payload run)
- Dual-interpreter GREEN (fresh D:-local disposable snapshots, both CPython 3.14.6 and 3.11.15): inventory 87/87, stabilization boundaries 48 with one POSIX-only skip, orchestration configuration 53/53, generator `--check` byte-stable exit 0, boundary check exit 0, assertive probe exit 0
- Continuous integration: run `33293625754` completed success on `windows-latest` CPython 3.11.9 — the first fully passing wall, including the inventory suite and the classified assertive diagnostics probe
- Version-stable census: f-string constants anchor to the JoinedStr start line; the expected string-decoy digest is `ed3d0769d3896960ee77af0fcd4b7d37b1858a627b88e288fc29937be5cce09e`; checked-in inventory and profile bytes are unchanged at `0dd70ea42bcbde0c2abfc156c20c0214060a504b80bfb1cbbad495d48336543d` and `2773545eb34b8e643c55c87e1e6ba6ee0a3ac5a930038d4266f514e54ae497ea`
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0481
- Front-Door-Contract: ADR-0307
- Front-Door-Revoked: ADR-0281, ADR-0468, ADR-0472, ADR-0475
- Front-Door-Active-Next: Hold the compiled synthetic topology-calibration lane and conduct the architecture checkpoint before any successor owner: bind a real production source-local base producer, its exact algebra, epoch identity, refresh cadence, exponent admission, and cold-versus-hit frequency in the one-seat river bridge, or park this lane and return to v0a integration; any later compiled experiment requires a fresh preregistration and lifecycle, must charge cold structural cover once per genuine production epoch and provenance hits at their actual consumers, and may not reuse v7's partial rows, relax the rejected wall, thin the frozen population, or select an arm from this artifact. Separately, continue the stabilization plan's remaining orchestration tasks under the installed collaboration protocol, rule explicitly on the proposed protocol amendments during the architecture review, and complete the open operations items — the restore drill and a retained-evidence inventory test — before broad-suite reliance
- Front-Door-Blockers: v7 is permanently consumed and the compiled calibration is incomplete; no production source-local base producer, refresh cadence, exponent admission, or width bound exists; no selected topology, complete reduced compiled-calibration result, population-25 result, actual-45 numerical result, global resolver-certificate integration, complete resolver iteration, known certificate count per action, or 15-second action result exists; no repeated-actor multiway existence result, off-tree opponent-action result, cross-street belief and certificate handoff, certified full-width river strategy bridge, trained blueprint, integrated bot, production action width, or poker-strength result exists; the stabilization adds test-governance capability but clears none of these, and broad-suite execution, capability approvals, the holistic-audit backlog, the protocol-amendment rulings, and the restore drill remain open

## Question

The continuous-integration instrumentation round proved that the
test-governance stack fails deterministically on the CPython 3.11 release
interpreter and that every recorded "isolated Python 3.11 snapshot" had
executed on CPython 3.14.6. What correction is accepted, on what evidence,
and what does the record still not claim?

## Decision

Accept the release-interpreter identity correction onto the mainline and
correct the evidence labels. The defect was one mechanism with four symptom
layers: identity comparisons mixed `os.stat` fields — whose Windows `st_dev`
is a 32-bit volume serial on CPython 3.11 and 64-bit from 3.12 — with 64-bit
`FileIdInfo` handle identities, so every such comparison rejected on 3.11;
the rejection triggered rollback, rollback guards hit further mixed
comparisons, cleanup went pending with the deterministic lock retained, and
teardown failed with access-denied unlinks. The correction derives both
sides of every affected comparison from full-width `FileIdInfo` through
independent observations: ancestor-chain capture and revalidation each open
their own per-ancestor directory handle, the staging bind and publish
comparison use the retained staging handle's file id, readback and rollback
concurrent-destination guards compare against that staged identity, the
destination-replace guard compares against an expected file id captured by an
independent path-side open at validation time and fails closed when absent,
the recovery guard opens the recovery path independently, and destination
normalization constructs through the supplied path's own class because bare
`Path()` dispatches on the simulated platform and CPython 3.11 refuses
cross-flavor instantiation. Stat-to-stat comparisons, which are
version-consistent, are untouched, and no replacement, reparse, ownership,
or rollback check was weakened.

The string-decoy census is now version-stable: f-string constants anchor to
their JoinedStr's start line, the only position CPython 3.11 and 3.12+
report identically; two synthetic templates whose parts collapsed to
duplicate locations use explicit concatenation; and two runtime synthetics
wrap `sorted(reverse=...)` arguments in `bool(...)` because CPython 3.11
rejects non-integer reverse objects. Generated inventory and profile bytes
are unchanged. The diagnostics probe is classified as an orchestration
origin and is assertive: it exits nonzero unless every ancestor identity
comparison matches, the lock discipline behaves, and a real standalone
governance write publishes.

The evidence labels are corrected without touching historical bytes. The v1
snapshot runner resolves the CPython 3.14.6 development venv, so every
"isolated Python 3.11 snapshot" line in the Task 2 report records a 3.14.6
execution; an appended report section states this, the results remain valid
as 3.14.6 evidence, and the successor runner asserts and records the actual
child interpreter's executable, implementation, and full version before any
payload, failing closed on absence or mismatch, with the fail-closed branch
exercised.

Verification is layered and current. The retained RED is the probe's
pre-correction evidence on both the hosted runner (3.11.9) and the
development machine (3.11.15). Fresh disposable-snapshot GREEN covers both
CPython 3.14.6 and 3.11.15: inventory 87/87, stabilization boundaries 48
with one POSIX-only skip, orchestration configuration 53/53, byte-stable
generation, the boundary check, and the assertive probe. Two independent
Tier-C cold reviews returned CLEAN against the frozen four-file manifest,
the committed tree is byte-identical to the reviewed candidate, and
continuous-integration run `33293625754` then passed every gate on a hosted
runner's genuine CPython 3.11 — the first complete wall, and the first time
the 3.11 release interpreter has validated this stack anywhere.

The inherited front-door trust chain remains explicit, and every continuity
statement of ADR-0480's decision — the complete trust chain from ADR-0310
through ADR-0476, the machine-checked continuity directives, and the exact
historical continuity strings — remains binding and unchanged by this
correction, with one extension: ADR-0477 through ADR-0481 record the
stabilization era — archive replication, the agent charter and collaboration
protocol, the evidence layer and sealed-boundary manifests, the
orchestration absorption, and this release-interpreter identity correction —
without invoking any consumed owner or altering any retained byte.

### Result boundary

This decision proves the correction, its dual-interpreter GREEN, the CLEAN
reviews, and the passing continuous-integration wall. It does not
retroactively validate any historical run on CPython 3.11: every earlier
result stands only as evidence for the interpreter that actually executed
it, CPython 3.14.6. No scientific or GPU payload ran, and no capability was
approved.

### Kill criteria

Kill any claim that a pre-correction result was 3.11-validated. Kill any new
identity comparison that mixes stat-derived and handle-derived fields. Kill
any snapshot acceptance whose runner did not assert and record the actual
child interpreter. The census anchoring and decoy digest are frozen with
this decision; a future interpreter whose AST positions diverge again
requires a fresh correction, never a silent digest refresh.

### Claims boundary

ADR-0481 proves only what its evidence chain states. It clears no ADR-0476
research blocker, adopts no proposed protocol amendment, authorizes no item
of the holistic-audit backlog, recertifies no scientific result, and makes
no poker-strength, resolver, action-clock, or blueprint claim.
