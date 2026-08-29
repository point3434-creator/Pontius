# Task 1 Report: Orchestration Contracts

## Status

- Result: complete after controller fix round 1/5
- Base commit: `89303d1e7bdda4f3aec74b131d8a8cc8d1afcc09`
- Branch: `codex/orch-task1`
- Initial commit: `b4a16549bbfc4a923e12a1f9b0ab74faa981ac8a`
- Initial commit subject: `feat(testing): lock orchestration contracts`
- Fix commit: `f129787048ed2ef9a43c673a78dfdcdc1965ebb8`
- Fix commit subject: `fix(testing): enforce orchestration contracts`
- Isolated worktree: `C:\Users\point\AppData\Local\Temp\pontius-orch-task1`
- Final worktree status: clean (`git status --short --branch` printed only `## codex/orch-task1`)
- Merge/push/cherry-pick: not performed

## Controller fix round 1/5

All seven Important controller findings and the approved forward-compatibility corrections were reproduced and closed:

1. Full summaries now use the distinct worker-binding union: workers may share an identical binding, while conflicting identities for one slot are rejected.
2. Run summaries retain the actual not-run trigger category, bind the one profile summary to the requested profile, reject empty completed success, return `7` for direct unavailable GPU, and keep optional GPU unavailable non-exit-affecting under `full`. Full optional-condition rows must be the exact union owned by `OPTIONAL_UNAVAILABLE` GPU workers, so fabricated optional observations are rejected.
3. Direct and full aggregate requested IDs, outcome rows, and counts are recomputed from their exact child payload/worker rows. Natural keys are unique, conflicting repeated full projections are rejected, and optional full payload projections must equal the nested projection when present.
4. Historical cases now require the exact inventory/probe runtime closure, exclude lifecycle fixture result IDs, require every named payload to own at least one runtime item, bind selected-test blobs exactly, bind blobs to snapshot phase/commit/governance, and reject conflicting roots for one `(phase, commit)` natural key.
5. Full-profile fixtures are resolved transitively with cycle detection. Lifecycle fixture IDs, module/class identity, nonempty membership, and exact inventory/payload ownership are enforced.
6. Capability definitions/bindings are expanded and validated per approval scope with the ruled binding/expanded-row orders, exact semantic digests, no dangling/unused/cross-scope definitions, and fail-closed selection. Both-zero preapproval files parse, but every applicable selection refuses with exact code `capability_approval_required` and message `applicable capabilities are not approved`.
7. Nested frozen values reject dataclasses, including a real frozen `ChildExecutionResult` containing mutable report data, preventing hidden mutable aliases.

The approved `declared_unconditional_skip` inventory variant is supported with an exact nonempty reason and no irrelevant platform fields. Variant parsers reject irrelevant keys even when their values are empty. `dynamic_program_sha256` is omitted when inapplicable and is required to equal the UTF-8 SHA-256 of the program following the sole Python `-c`; non-Python `-c` tokens remain static arguments. `CallCapability.return_contract` remains a nonempty string for the Task 3 wire contract.

## Implemented contract

- Added tool-local, stable, recursively immutable orchestration errors without importing `pontius`.
- Added the exact Task 1 enums and frozen/slotted model field sets, plus the integration-required `InventoryEntry` assignment-XOR-exclusion model so excluded inventory rows remain present in `ConfigurationBundle`.
- Added strict value, path, digest, budget, lifecycle, evidence-guard, status, nested-summary, exit, and internal worker-plan closure validation.
- Canonicalized repeated collections into sorted tuples using their ruled semantic identities, including interpreter bindings by `slot_name`, capability bindings by `(approval_scope, item_id, capability_kind, capability_id)`, evidence rows by relative path, and capability definitions by ID.
- Preserved ordered and duplicate subprocess argv/argv-template tokens while rejecting unordered duplicate values elsewhere.
- Kept `CallCapability.return_contract` as the Task 3-compatible nonempty string wire value.
- Added exact interpreter wire identity/version validation compatible with the downstream protocol contract.
- Added dedicated `probe:<name>` validation in the shared model and strict configuration parser.
- Added strict duplicate-rejecting JSON and TOML parsing, normalized repository-rooted paths, assignment/reference validation, immutable sorted mappings, semantic digest normalization independent of mapping/collection source order, profile selection, and pure exit precedence.
- Added an exact-path test bootstrap that loads only `<snapshot>/tools/test_orchestration` through a synthetic package and does not mutate `sys.path`.

## Changed files

1. `tests/orchestration_test_support.py`
2. `tests/test_test_orchestration_configuration.py`
3. `tools/__init__.py`
4. `tools/test_orchestration/__init__.py`
5. `tools/test_orchestration/configuration.py`
6. `tools/test_orchestration/errors.py`
7. `tools/test_orchestration/model.py`

`git show --stat --summary b4a16549bbfc4a923e12a1f9b0ab74faa981ac8a` reports exactly these seven new files and 3,643 insertions. No protected v2-v9 owner/reader/runner/authorization artifact was changed.

Fix round 1 changed exactly these existing Task 1 files:

1. `tests/test_test_orchestration_configuration.py`
2. `tools/test_orchestration/configuration.py`
3. `tools/test_orchestration/model.py`

Fix commit `f129787048ed2ef9a43c673a78dfdcdc1965ebb8` reports 1,765 insertions and 86 deletions across exactly those three files. No other repository file and no protected artifact changed.

## Test execution boundary

Every payload was run from a fresh canonical OS-temp snapshot created by:

```powershell
& 'C:\Users\point\AppData\Local\Temp\pontius-evidence-test-stabilization\.superpowers\sdd\2026-08-27-test-profile-orchestration\task-1-run-snapshot.ps1' -Label '<label>' -ExpectedExit <0-or-1>
```

The helper used a local no-hardlink/no-alternates clone at the exact base commit, overlaid only the seven Task 1 files, set working directory to the disposable harness root, and launched:

```text
C:\Users\point\AppData\Local\Temp\pontius-evidence-test-stabilization\.venv\Scripts\python.exe -B -P tests/test_test_orchestration_configuration.py -v
PYTHONPATH=<snapshot>/harness/src
```

Git and Python environments were allowlisted. All reported snapshots ended with `CLEANED=true`; stdout was empty and verbose unittest evidence was captured on stderr.

## RED/GREEN evidence

| Cycle | Snapshot suffix | Result | Evidence |
| --- | --- | --- | --- |
| Initial RED | `red-11fa9779f3424fc58960e0754e0db2ea` | exit 1 | Missing `tools/test_orchestration/errors.py` produced the expected `FileNotFoundError`. |
| Initial GREEN | `green1-34f722...` | exit 0 | 12/12 tests passed. |
| Integration RED | `red2-7cda85...` | exit 1 | 15 tests exposed four expected contract errors: excluded inventory representation/parser and mapping-valued `return_contract`. |
| Integration GREEN | `green2-5face...` | exit 0 | 15/15 tests passed. |
| Wire RED | `red3-02b67...` | exit 1 | 16 tests exposed interpreter platform/version and profile-variant contract gaps. |
| Wire GREEN | `green3-4841...` | exit 0 | 16/16 tests passed. |
| Invariant RED | `red4b-0ef667...` | exit 1 | 19 tests produced five expected failures covering evidence cardinality, outcome IDs, and direct/full owned-row invariants. |
| Invariant GREEN | `green4-609624...` | exit 0 | 19/19 tests passed. |
| Capability RED | `red5-3007b...` | exit 1 | 22 tests exposed ordered duplicate argv, capability kind/slot, exact historical-vector, and collection-order gaps. |
| Capability GREEN | `green5-1892e0190dd9499397d6a72a64e5ebda` | exit 0 | 22/22 tests passed. |
| Ordering RED | `red6-d015c8acd4fd420d989ea37c0bf4207d` | exit 1 | 23 tests produced two failures and one error for fixture-path, interpreter-slot, and evidence-path ordering. |
| Ordering GREEN | `green6-211b94b80b7341d3bb46ac8569276d0c` | exit 0 | 23/23 tests passed. |
| Reference/state RED | `red7b-3ec09efcf3a24ad8bb5f8608d086f396` | exit 1 | 23 tests produced three expected failures for unknown payload interpreter slots, active-output ownership, and direct binding cardinality. |
| Reference/state GREEN | `green7-a5d94b84c57547e2a6acba83cb272920` | exit 0 | 23/23 tests passed. |
| Review RED | `red8-afd363af39d54c10bd498762bad58de0` | exit 1 | 25 tests produced three expected failures for probe grammar, nested-summary consistency, and worker-plan closure. |
| Review GREEN | `green8-4a411bcde3104978b95b139f12a01a31` | exit 0 | 25/25 tests passed. |
| Re-review RED | `red9-05b10151595946e29a29ba3da7680e01` | exit 1 | 25 tests produced two expected failures for model-level probe validation and nested test-failure/run-exit reconciliation. |
| Re-review GREEN | `green9-a904115e142449fd9817ae1069512dd8` | exit 0 | 25/25 tests passed. |
| Final verification | `final2-74cef5cae565497b84d6b970a58bfb93` | exit 0 | 25/25 tests passed in 0.098 seconds; zero failures/errors; snapshot cleaned. |

### Controller fix round 1 evidence

| Cycle | Snapshot label | Result | Evidence |
| --- | --- | --- | --- |
| Broad controller RED | `r1-red1` | exit 1 | 37 tests produced 23 failures and 6 errors against the initial Task 1 implementation, covering the seven controller findings and approved schema corrections. |
| First corrected GREEN | `r1-green2` | exit 0 | 37/37 tests passed after the snapshot overlay helper was corrected. |
| Historical/lifecycle RED | `r1-red2` | exit 1 | Two expected failures exposed split lifecycle ownership and an extraneous selected-test blob. |
| Historical/lifecycle GREEN | `r1-green3` | exit 0 | 37/37 tests passed. |
| Static-argv RED | `r1-red3` | exit 1 | One expected error showed that Git `-c` was incorrectly treated as a dynamic Python program. |
| POSIX-ID RED | `r1-red4` | exit 1 | One expected failure rejected only after canonical POSIX stable-ID validation was restored. |
| Dataclass-spoof RED | `r1-red5` | exit 1 | One expected failure exposed acceptance of a spoofed frozen dataclass. |
| Consolidated GREEN | `r1-green5` | exit 0 | 37/37 tests passed after the `r1-red3`–`r1-red5` fixes. |
| Independent-review RED | `r1-red6-de688a4253c14ae99588678da351a9cc` | exit 1 | Exactly three failures reproduced mutable nested `ChildExecutionResult`, forged full exit-7 optional state, and conflicting historical roots for one phase/commit. |
| Independent-review GREEN | `r1-green6-c59ec88d7bb94748a8d3b7ca74768466` | exit 0 | 37/37 tests passed. |
| Optional-provenance RED | `r1-red7-096dcdb5f30a467aa6213456c6aeab92` | exit 1 | Exactly one failure reproduced a fabricated non-exit optional condition with no unavailable GPU worker. |
| Optional-provenance GREEN | `r1-green7-8cc4e973bdc8467e9ed4d32c897a5b33` | exit 0 | 37/37 tests passed. |
| Final fix-round verification | `r1-final-20909d386689401caa4d1fb2c3010f7a` | exit 0 | 37/37 tests passed in 0.194 seconds; zero failures/errors; `CLEANED=true`. |

An attempted `r1-green1` still exercised the initial committed implementation because the helper copied the package directory beneath an existing destination. It correctly returned exit 1 but is not claimed as GREEN evidence. The helper was repaired to overlay the seven allowlisted Task 1 files individually; every subsequent result above used that corrected boundary. All fix-round snapshots used the central venv executable with `-B -P`, working directory `H`, and `PYTHONPATH` exactly `H/src`; no test payload ran from a development worktree.

An early `red2` helper attempt deadlocked because stdout/stderr pipes were read sequentially. The process was stopped, its exact snapshot was safely validated and removed, and the helper was corrected to drain both pipes concurrently. It is operational history, not test evidence.

## Review evidence

An independent read-only Task 1 review found worker-plan closure, nested summary/run-state, and probe grammar gaps. Focused RED/GREEN tests were added before each correction. Re-review confirmed the worker-plan closure/natural-key fix and confirmed that the `ChildExecutionResult.report` placeholder can be replaced by Task 3 without changing the Task 1 field shape. Its two remaining findings—nested test-failure exit reconciliation and model-level probe validation—were then reproduced in `red9` and corrected in `green9`/`final2`.

The concrete `ChildResultV1` type, atomic report decoder, `ProcessOutcome`, and request/report identity matching are deliberately not invented in Task 1; those are Task 3-owned protocol contracts. Task 1 retains the exact `report` field seam and the protocol category/completion baseline for downstream strengthening.

Controller fix round 1 received an additional independent read-only review. Its first pass identified three Important edge cases (nested mutable report aliases, forged full optional exit state, and phase/commit snapshot-root ambiguity); its second pass identified the remaining optional-condition provenance gap. Each was reproduced in a fresh RED snapshot before correction. The final explicit verdict was: `CLEAN — no remaining Important findings.` The reviewer also confirmed that the other requested contracts remained materially covered and that no payload was run from the development worktree.

## Git verification

Before commit:

- `git rev-parse HEAD` returned the required base `89303d1e7bdda4f3aec74b131d8a8cc8d1afcc09`.
- `git diff --cached --check` exited 0 with no whitespace errors.
- `git diff --cached --name-only` listed exactly the seven Task 1 files above.

After commit:

- The initial implementation `git rev-parse HEAD` returned `b4a16549bbfc4a923e12a1f9b0ab74faa981ac8a`.
- Fix-round `git diff --cached --check` exited 0.
- Fix-round `git diff --cached --name-status` listed exactly the three scoped modified files.
- Fix-round `git rev-parse HEAD` returned `f129787048ed2ef9a43c673a78dfdcdc1965ebb8` with parent `b4a16549bbfc4a923e12a1f9b0ab74faa981ac8a`.
- `git status --short --branch` returned only `## codex/orch-task1`.
- The initial commit listed exactly the seven Task 1 files; fix-round `git diff-tree --no-commit-id --name-status -r HEAD` listed exactly the three modified Task 1 files.

## Limitations

- Ruff is not installed in the pinned disposable environment, so no Ruff result is claimed.
- The accepted Task 1 checkpoint requires the focused configuration test; the repository-wide suite and later CPython 3.11/full-profile matrices were not run because they belong to later orchestration tasks and payloads may not run from a development worktree.
- Only the current Windows host was exercised for Task 1. Windows/POSIX path and golden-wire cross-host behavior is assigned to later protocol/environment tasks.
- The external snapshot helper remains in the SDD evidence directory for reproducibility and is not part of the commit.
- `ResolvedWorkerPlan` validates the exact phase/commit/governance and selected-test blob closure available inside the Task 1 model. Exact comparison against the authoritative full dependency-blob universe must occur when the later plan assembler supplies `ExecutionBundle.historical_blobs`; Task 1 does not invent that downstream assembly seam.
- No primary checkout, main integration worktree, protected artifact, remote branch, or pull request was modified.
