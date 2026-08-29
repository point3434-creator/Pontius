# Evidence plan preflight

Plan: `docs/superpowers/plans/2026-08-27-evidence-integrity-and-authorization.md`  
Spec: `docs/superpowers/specs/2026-08-27-evidence-test-stabilization-design.md`

## Per-task internal consistency

| Task | Internal producer/test/file consistency | Finding |
| --- | --- | --- |
| 1 | The errors/models and focused test are new; the public subpackage initializer is distinct from the protected `src/pontius/__init__.py`. Its stdlib-only dependency boundary and frozen/type-validation requirements agree with the global constraints. | PASS — no contradiction. |
| 2 | The pure bytes parsers and semantic encoder consume Task 1 values and defer path I/O to Task 4; the tests target the same strict schemas and type rules. | PASS — no contradiction. |
| 3 | The stdlib-only generator emits only the four new manifest files, checks retained bytes/absences before writing, and requires an exact user-approved earlier-phase seed digest before `--write`. Its explicit approval pause is consistent with the hard governance gate. | PASS — no contradiction. |
| 4 | Secure one-read filesystem/Git adapters and manifest loaders consume the Task 1/2 types and keep I/O outside the pure parsers; required tests cover their declared fail-closed behavior. | PASS — no contradiction. |
| 5 | The authorization state machine consumes the typed Task 1 state/adapters, reads a present file once, revalidates repository state, and replaces the legacy `KeyError` with the typed live-state failure. | PASS — no contradiction. |
| 6 | The assessor consumes Task 4 loaders/adapters and generated manifests, verifies retained bytes before semantics, calls only the allowed journal seam, and returns the negative frozen assessment without owner invocation. | PASS — no contradiction. |
| 7 | The semantic hardening changes only the assessor/tests, preserves the Task 3 manifest lock, and explicitly forbids numerical scientific recomputation and positive/launch APIs. | PASS — no contradiction. |
| 8 | The AST/diff boundary test and generator `--check` enforce the same sealed-path, absence, and narrow-import rules stated globally and in the spec; checks are read-only. | PASS — no contradiction. |
| 9 | The gate runs focused evidence checks only from fresh disposable snapshots, requires exact CPython 3.11 and Ruff as explicit release gates, and records both independent reviews before any authorized commit. | PASS — no contradiction. |

## Shared-file and shared-interface consistency

| Tasks | Shared file/interface — producer → consumer | Finding |
| --- | --- | --- |
| 1 / 2 | `model.py` and typed errors — Task 1 frozen models/errors → Task 2 manifest constructors/parsers. | PASS — Task 2 defers filesystem I/O as required. |
| 1 / 4 | `FileIdentity`, `GitTreeEntry`, `GitIndexEntry`, manifest wrappers — Task 1 → Task 4 adapters/loaders. | PASS — exact types and one-read protocols are compatible. |
| 1 / 5 | authorization state/error types — Task 1 → Task 5 reader and `require_live_authorization`. | PASS — typed union prevents the legacy mapping access. |
| 1 / 6 | retained-manifest/assessment model types — Task 1 → Task 6 assessor. | PASS — negative assessment fields match the approved model. |
| 1 / 7 | unchanged `RetainedV7Assessment` — Task 1 → Task 7 semantic hardening. | PASS — Task 7 preserves the public frozen assessment interface. |
| 1 / 8 | new evidence modules — Tasks 1 modules → Task 8 import-boundary classification. | PASS — permitted imports match the global allowlist. |
| 1 / 9 | Task 1 focused test/model scope → Task 9 evidence suite and review gate. | PASS — included in the required suite. |
| 2 / 3 | schema literals, canonical semantic encoding, and `test_evidence_manifests.py` — Task 2 → Task 3 generator/conformance vectors. | PASS — generator stays stdlib-only while tests compare both implementations. |
| 2 / 4 | pure `parse_*_manifest` functions and `manifest.py` — Task 2 → Task 4 secure path loaders. | PASS — loaders add the required secure one-read I/O without changing pure-parser scope. |
| 2 / 5 | `tests/evidence_test_support.py` — Task 2 creates → Task 5 extends. | PASS — support loading rule remains compatible with `-B -P`. |
| 2 / 6 | manifest models/parsers and test support — Task 2 → Task 6 retained assessor. | PASS — strict manifest inputs are retained. |
| 2 / 7 | frozen retained-v7 manifest/model interface — Task 2 → Task 7 validation. | PASS — Task 7 reads the lock; it does not rewrite it. |
| 2 / 8 | active manifest module/schema surface — Task 2 → Task 8 boundary classification. | PASS — Task 8 enforces, rather than expands, the allowed imports. |
| 2 / 9 | manifest tests and semantic identities — Task 2 → Task 9 suite/review. | PASS — both manifest test files are required gate inputs. |
| 3 / 4 | secure-reader behavioral contract and manifest files — Task 3 generator → Task 4 adapters/loaders. | PASS — Task 4's shared conformance tests are an intended later strengthening. |
| 3 / 6 | four generated manifests, especially historical/retained-v7 data — Task 3 → Task 6 assessor. | PASS — Task 6 verifies rather than modifies generated evidence. |
| 3 / 7 | `docs/architecture/retained-v7.toml` identity lock — Task 3 → Task 7. | PASS — Task 7 explicitly preserves raw and semantic identities. |
| 3 / 8 | generator and `test_evidence_manifest_generation.py` — Task 3 → Task 8. | PASS — Task 8 adds read-only generator/boundary checks. |
| 3 / 9 | generated manifests and `--check` — Task 3 → Task 9 final gate. | PASS — pre/post generator checks are included. |
| 4 / 5 | `AuthorizationFileSystem`, `GitRepository`, and identity types — Task 4 → Task 5 reader. | PASS — Task 5 injects these adapters and creates none implicitly. |
| 4 / 6 | `RetainedEvidenceFileSystem`, `GitRepository`, and strict loaders — Task 4 → Task 6 assessor. | PASS — supports bounded, one-read artifact verification and explicit historical Git reads. |
| 4 / 8 | new adapter and loader modules — Task 4 → Task 8 import-boundary scope. | PASS — Task 8's allow/deny test covers these modules. |
| 4 / 9 | adapter/loader focused tests — Task 4 → Task 9 suite/review. | PASS — `test_evidence_filesystem_and_git.py` is included. |
| 5 / 6 | `tests/evidence_test_support.py` — Task 5 extends → Task 6 extends. | PASS — shared test support stays within the declared `-B -P` file-loading constraint. |
| 5 / 8 | authorization module and regression test — Task 5 → Task 8 boundary scope. | PASS — boundary rules admit only the declared evidence dependencies. |
| 5 / 9 | authorization tests and `require_live_authorization` evidence — Task 5 → Task 9 completion gate. | PASS — the required suite includes the KeyError-regression coverage. |
| 6 / 7 | `retained_v7.py` and `test_retained_v7_assessment.py` — Task 6 public assessor/pure seam → Task 7 stricter validation. | PASS — Task 7 keeps the public signature and negative-only API. |
| 6 / 8 | retained assessor/module and generated manifests — Task 6 → Task 8 boundary enforcement. | PASS — Task 8 verifies the journal-seam-only import policy. |
| 6 / 9 | retained-v7 assessment tests/results — Task 6 → Task 9 gate. | PASS — assessor fields and durable-journal regression are required inputs. |
| 7 / 8 | hardened assessor/test scope — Task 7 → Task 8 import/history boundary. | PASS — no new scientific API or dependency is introduced. |
| 7 / 9 | Task 7 independent-snapshot retained assessment evidence — Task 7 → Task 9 gate. | PASS — final suite rechecks the unchanged negative assessment. |
| 8 / 9 | `test_evidence_import_boundary.py`, generator `--check`, and protected-boundary evidence — Task 8 → Task 9 review gate. | PASS — Task 9 requires these checks before a release claim. |

## Result

PASS — no concrete contradiction with the plan's Global Constraints or the approved specification. The Task 3 earlier-phase seed approval remains an explicit external governance checkpoint and must not be bypassed.
