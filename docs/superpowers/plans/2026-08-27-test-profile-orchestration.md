# Test Profile Orchestration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace unreliable one-process discovery with a deterministic, profile-owned, snapshot-isolated test system that runs current tests from a captured harness, historical controls from exact commits, GPU checks explicitly, and every child inside a contained process tree.

**Architecture:** A standard-library-only parent captures an immutable disposable harness root `H`, validates the inventory/profile contracts, and launches a self-contained child from `H`. Current targets use `T == H`; historical targets use exact detached clones `T` while the child harness remains in `H`. Parent and child communicate only through strict atomic JSON. The orchestrator reads evidence TOML directly and never imports `pontius` or test modules.

**Tech Stack:** Python 3.11+, standard library (`argparse`, `ast`, `ctypes`, `dataclasses`, `hashlib`, `importlib`, `json`, `pathlib`, `subprocess`, `tomllib`, `unittest`), Git plumbing, Windows Job Objects, POSIX process groups, Ruff when provisioned, CodeRabbit as an additional review gate.

**Spec:** [Evidence and Test Stabilization Design](../specs/2026-08-27-evidence-test-stabilization-design.md)

## Global Constraints

- Execute the coordinated plans in this order: evidence Tasks 1-3; orchestration Tasks 1-2 plus Task 11a; evidence Tasks 4-9; orchestration Tasks 3-10; Task 11b; then Task 12. This preserves the approved data-first delivery slice while keeping the active evidence API ahead of the runner that consumes its TOML. The orchestrator consumes `sealed-current-files.toml`, `sealed-current-absences.toml`, `historical-blobs.toml`, and `retained-v7.toml` as schemas/data; it does not import `pontius.evidence`.
- Do not modify any existing v2-v7 owner, reader, runner, historical test, configuration, decision, or retained lifecycle artifact. Do not launch a real scientific owner under any profile.
- `tools/run_tests.py`, every `tools/test_orchestration/*.py` module, inventory/baseline generators, boundary checker, and `tools/test_child.py` remain standard-library-only. They may import sibling orchestration modules but not `pontius`, tests, experiments, CuPy/CUDA/GPU modules, or historical owners/readers/runners.
- `tools/test_child.py` is self-contained. It imports no sibling helper and installs all guards before loading any repository test or `pontius` module.
- The parent never imports a test module. It never treats raw `unittest` text or return code as the result protocol.
- No test payload runs from or writes to the primary checkout. Until Task 12 approves and writes the final complete design-scope capability table, run new orchestration/current test files only through the disposable bootstrap-snapshot procedure from the evidence plan with synthetic test-local guard policies. A profile may use the canonical runner earlier only when its entire applicable capability scope has an approved nonzero digest (historical after Task 10); never bypass preapproval refusal.
- Every payload gets a fresh interpreter with `-B -P`, cwd `T`, and `PYTHONPATH` exactly `T/src`. Neither `H`, `T`, `T/tests`, the primary checkout, nor an empty path element may appear in child `sys.path`.
- The interpreter prefix/site-packages is the only allowed primary-tree exception when the repository virtual environment lives below the primary checkout. Record it explicitly in interpreter identity.
- Create all run roots under the resolved OS temporary directory, outside OneDrive. Use local clones with `--no-hardlinks`; reject alternates, junctions, reparse links, hard links back to primary, or any resolved escape.
- Configuration is fully validated before a child is created. Safety failures stop later payloads after contained termination and post-evidence checks. Ordinary assertion failures do not erase already independent results.
- Use monotonic nanosecond deadlines. Total budgets reserve positive setup, child, termination-grace, and cleanup budgets.
- Build child environments from a documented allowlist. Do not copy ambient environment and then try to subtract dangerous keys.
- Direct profile requests and `full` have different optional-GPU semantics: a schema-valid unavailable GPU is exit `7` for explicit `gpu` and a visible nonfailing profile skip in `full`. A crashed or malformed probe is runtime exit `5`.
- CPython 3.11 is a required release slot. The current development interpreter cannot silently replace it.
- Each task ends with a review checkpoint. Run a listed commit command only after explicit user authorization to create commits; otherwise leave the work uncommitted and record the checkpoint.

## File Structure

Create the orchestration package and entry points:

```text
tools/
  __init__.py
  run_tests.py
  test_child.py
  generate_test_inventory.py
  generate_dependency_baseline.py
  check_stabilization_boundaries.py
  test_orchestration/
    __init__.py
    errors.py
    model.py
    configuration.py
    protocol.py
    environment.py
    git.py
    workspace.py
    evidence_guard.py
    process.py
    windows_job.py
    posix_group.py
    engine.py
```

Create owned data:

```text
tests/test-inventory.json
tests/test-profiles.toml
docs/architecture/dependency-baseline.toml
```

Create test support and focused tests:

```text
tests/orchestration_test_support.py
tests/test_test_orchestration_configuration.py
tests/test_inventory_and_profiles.py
tests/test_test_orchestration_protocol.py
tests/test_test_orchestration_process.py
tests/test_test_orchestration_windows_job.py
tests/test_test_orchestration_posix_group.py
tests/test_test_orchestration_environment.py
tests/test_test_orchestration_child.py
tests/test_test_orchestration_guards.py
tests/test_test_orchestration_workspace.py
tests/test_test_orchestration_historical.py
tests/test_test_orchestration_engine.py
tests/test_stabilization_boundaries.py
tests/test_test_orchestration_import_boundary.py
```

Modify documentation only after the runner is verified:

```text
README.md
RUNBOOK.md
```

---

### Task 1: Lock Orchestrator Errors, Models, Configuration, and Exit Semantics

**Files:**

- Create: `tools/__init__.py`
- Create: `tools/test_orchestration/__init__.py`
- Create: `tools/test_orchestration/errors.py`
- Create: `tools/test_orchestration/model.py`
- Create: `tools/test_orchestration/configuration.py`
- Create: `tests/orchestration_test_support.py`
- Create: `tests/test_test_orchestration_configuration.py`

**Interfaces:**

- Consumes: Python 3.11+ standard library and repository-rooted TOML/JSON paths; no `pontius`, test-module, or experiment import.
- Produces: tool-local typed errors, the exact enums/models below plus `ConfigurationBundle`, `parse_stable_id(value: str) -> StableSelector`, `load_configuration(profiles_path: Path, inventory_path: Path, *, repository_root: Path) -> ConfigurationBundle`, `select_profile(bundle: ConfigurationBundle, name: str, *, payload_id: str | None = None, historical_case: str | None = None) -> ProfilePlan`, and `choose_exit_code(conditions: Iterable[ObservedCondition]) -> ExitCode`.

- [ ] Add a file-local test bootstrap that creates a synthetic `pontius_test_orchestration` package rooted only at `<snapshot>/tools/test_orchestration` with `importlib.util`. Do not add `H`, `T`, or the primary checkout to `sys.path`.

- [ ] Write failing tests for stable errors, recursive immutable context, exact enums, dataclass validation, stable-ID grammar, positive/reserved budgets, normalized paths, strict TOML fields/types, duplicate keys, unknown profile/payload/capability references, and semantic digest independence from TOML key order.

- [ ] Implement tool-local error classes named `EvidenceConfigurationError`, `EvidenceIntegrityError`, `AuthorizationPhaseError`, `LifecycleStateError`, and `RuntimeContractError`. They deliberately duplicate the active layer's names because importing `pontius.evidence.errors` would violate the parent boundary.

- [ ] Implement these exact enums and frozen core values:

```python
class ExitCode(IntEnum):
    SUCCESS = 0
    CONFIGURATION = 2
    INTEGRITY = 3
    PHASE = 4
    RUNTIME = 5
    TEST_FAILURE = 6
    OPTIONAL_UNAVAILABLE = 7


class TargetKind(StrEnum):
    CURRENT_SNAPSHOT = "current_snapshot"
    HISTORICAL_CLONE = "historical_clone"


class ExecutionStatus(StrEnum):
    PASSED = "passed"
    TEST_FAILURE = "test_failure"
    CONFIGURATION_FAILURE = "configuration_failure"
    INTEGRITY_FAILURE = "integrity_failure"
    PHASE_FAILURE = "phase_failure"
    RUNTIME_SAFETY_STOP = "runtime_safety_stop"
    CANCELLED = "cancelled"
    NOT_RUN_SAFETY_STOP = "not_run_safety_stop"
    OPTIONAL_UNAVAILABLE = "optional_unavailable"


@dataclass(frozen=True, slots=True)
class StageBudgets:
    setup_ns: int
    child_ns: int
    termination_grace_ns: int
    cleanup_ns: int
    total_ns: int


@dataclass(frozen=True, slots=True)
class StableSelector:
    stable_id: str
    relative_path: PurePosixPath
    case_name: str
    method_name: str
```

Add the following validated frozen models with these exact field sets:

```text
InterpreterIdentity:
  executable, resolved_executable, platform_identity, executable_sha256,
  implementation, version, prefix, base_prefix, no_user_site, safe_path,
  dont_write_bytecode, distributions_sha256, dependency_lock_sha256
InterpreterBinding:
  slot_name, identity
TargetIdentity:
  kind, root, head_commit, root_tree_oid, file_inventory_sha256
PrimaryRootIdentity:
  resolved_path, platform_identity, capture_sha256
GitToolIdentity:
  executable, resolved_executable, platform_identity, executable_sha256
InterpreterSlot:
  name, resolution, windows_relative_path, posix_relative_path,
  environment_variable, implementation, minimum_version, exact_version,
  required_for_full
ProfilePlan:
  name, interpreter_slots, default_interpreter_slot, payload_ids,
  historical_case_ids, subprofiles, budgets, fixture_specs, gpu_optional,
  definition_sha256
FixtureSpec:
  relative_path, path_kind, byte_length, raw_sha256
InventoryExpectation:
  kind, applicable_platforms, skip_safe_reason_code
ResolvedInventoryItem:
  selector, expectation
PayloadPlan:
  payload_id, profile_name, target_kind, allowed_interpreter_slots,
  inventory_items,
  probe_ids, lifecycle_fixtures,
  environment_additions, environment_removals, allowed_write_roots,
  forbidden_relative_paths, fixture_specs, serialized
LifecycleFixturePlan:
  fixture_id, kind, relative_path, class_name, member_ids,
  allowed_write_roots, forbidden_relative_paths, serialized
HistoricalItemExpectation:
  item_id, outcome, phase, exception_type, safe_reason_code, body_entered,
  capability_counters
HistoricalSnapshotExpectation:
  phase, commit, root_tree_oid, governing_decision
HistoricalBlobExpectation:
  commit, relative_path, git_blob_oid, raw_sha256, role, phase,
  governing_decision
HistoricalCase:
  case_id, phase, commit, root_tree_oid, payload_ids, expected_vector,
  item_expectations, overlay_ids
OverlaySpec:
  overlay_id, source_commit, source_path, destination_path, byte_length,
  raw_sha256
SubprocessCapability:
  capability_id, executable_role, executable_slot, executable_constraints,
  argv, argv_template, dynamic_program_sha256, cwd_class,
  environment_additions, environment_removals, timeout_ns,
  expected_return_category, read_roots, write_roots,
  fixed_descendant_permission
CallCapability:
  capability_id, kind, module_name, qualified_name, action, maximum_calls,
  return_contract
CapabilityBinding:
  item_id, approval_scope, capability_kind, capability_id
EvidenceManifestIdentity:
  relative_path, schema_version, byte_length, raw_sha256, semantic_sha256,
  platform_identity
EvidenceFileExpectation:
  relative_path, byte_length, raw_sha256, role, platform_identity
EvidenceAbsenceExpectation:
  relative_path, role
EvidenceGuardPlan:
  semantic_sha256, manifest_identities, present_files, absences
EvidenceGuardSummary:
  before_semantic_sha256, after_semantic_sha256, status, conditions
ResolvedWorkerPlan:
  semantic_sha256, profile, inventory_entries, payloads,
  historical_cases, historical_snapshots, historical_blobs, overlays,
  subprocess_capabilities, call_capabilities, capability_bindings,
  spec_capabilities_sha256, capability_bindings_sha256
ExecutionBundle:
  configuration, evidence_guard_plan, historical_snapshots,
  historical_blobs, semantic_sha256
ObservedCondition:
  category, code, affects_exit, context
CapturedStreamIdentity:
  byte_length, raw_sha256, truncated
CapturedOutputIdentity:
  stdout, stderr
ChildExecutionResult:
  report, process_return_category, captured_output, completed
PayloadSummary:
  payload_id, status, requested_ids, outcomes, counts, conditions,
  captured_output,
  duration_ns, completed
WorkerSummary:
  profile, interpreter_binding, status, summary, conditions, duration_ns,
  completed
ProfileSummary:
  profile, profile_definition_sha256, inventory_sha256,
  spec_capabilities_sha256, capability_bindings_sha256,
  interpreter_bindings,
  payload_summaries, worker_summaries, requested_ids, outcomes, counts,
  conditions, evidence_guard_sha256, evidence_guard, duration_ns, completed
RunSummary:
  run_id, requested_profile, profile_summaries, conditions, exit_code,
  duration_ns, completed
ConfigurationBundle:
  repository_root, profiles_path, inventory_path, baseline_commit,
  sealed_current_files_manifest, sealed_current_absences_manifest,
  historical_blobs_manifest, retained_v7_manifest,
  profile_definition_sha256, inventory_sha256,
  spec_capabilities_sha256, capability_bindings_sha256, inventory_entries,
  interpreter_slots, profiles, payloads,
  historical_cases, overlays, subprocess_capabilities, call_capabilities,
  capability_bindings, stabilization_test_files
```

All repeated collections become sorted tuples and all mappings become recursively frozen sorted mappings. Optional digest/path fields use `str | None`, never magic empty strings. `StageBudgets` requires every field positive and `total_ns >= setup_ns + child_ns + termination_grace_ns + cleanup_ns`.

`InterpreterBinding.identity` is an exact nested `InterpreterIdentity`; bindings sort uniquely by `slot_name`. A direct profile summary recorded after interpreter resolution contains exactly its one binding, populates `payload_summaries`, and leaves `worker_summaries` empty. A pre-resolution failure may contain no binding only with `completed=false`. `full` populates `worker_summaries`, records the sorted unique union of their bindings, and may include aggregate payload rows from completed workers; every worker binding must occur exactly once in that union. An unstarted payload/worker has status `not_run_safety_stop`, `completed=false`, zero duration, empty outcomes/counts, and the triggering condition. It has no fabricated `ChildResultV1` outcome. Active terminated work uses `runtime_safety_stop`; user-cancelled active work uses `cancelled`.

`EvidenceGuardPlan.manifest_identities` contains the four exact evidence TOML source identities and semantic digests; `present_files` contains the six exact governed current identities; `absences` contains the eighteen exact governed absent paths. All three collections are sorted and unique, their paths are normalized below the primary root, and `semantic_sha256` is recomputed from their canonical form. `EvidenceGuardSummary.status` is exactly `unchanged`, `changed`, or `not_measured`. Completed direct/full summaries require nonnull lowercase before/after digests; success requires `unchanged` and equality. Only a pre-measurement failure may use `not_measured` with both digests null. `changed` is an integrity condition and preserves both unequal digests. A full summary's guard is the coordinator-level measurement; each nested worker summary preserves its own direct `ProfileSummary` guard.

`ResolvedWorkerPlan` is the complete immutable, profile-specific transitive closure needed by a fresh worker. Every referenced inventory item, payload, fixture, historical case/snapshot/blob, overlay, capability definition, and binding occurs exactly once; no unrelated row is included. Its `profile`, design digest, and historical digest equal the request fields, and `semantic_sha256` is recomputed over the entire canonical nested plan. `ExecutionBundle.configuration` is the one validated `ConfigurationBundle`; its historical rows come from the one secure parse of `historical-blobs.toml`, its guard plan comes from the same preparation pass over all four evidence manifests/current paths, and `semantic_sha256` binds the complete combination. A worker executes only this supplied plan and never reparses `tests/test-profiles.toml`, `tests/test-inventory.json`, or an evidence manifest.

The only payload/worker status literals are the `ExecutionStatus` values above. `passed` and `test_failure` require `completed=true` and exact requested/prepared/executed/outcome set equality; `passed` has no failing count and `test_failure` has at least one. `optional_unavailable` is worker/profile-only, has `completed=true`, zero requested/executed IDs, and one validated optional-capability condition. `runtime_safety_stop` and `cancelled` have `completed=false` and only a bounded executed prefix. Configuration/integrity/phase failures discard untrusted outcomes and use `completed=false`. `not_run_safety_stop` has the zero/empty invariants above.

`ChildExecutionResult.report` is `ChildResultV1 | None`; its captured stream identities come only from the parent's contained pipe drain after EOF and are never fields the child claims. `process_return_category` is exactly `protocol_committed` or `protocol_failure`, never a raw platform status. `protocol_committed` requires `ProcessOutcome.status="exited"`, return code `0`, pipe EOF, and a valid matching atomic report; every other combination is `protocol_failure`. A completed execution additionally requires successful containment closure and a report whose own `completed=true`. `PayloadSummary.captured_output` is that parent-owned identity for every started payload and is null only when no child was spawned.

- [ ] Implement `parse_stable_id` for the exact form `tests/<file>.py::<ClassName>::<test_method>`. Require a normalized path below `tests`, a Python identifier class, and a method beginning `test_`. Reject additional separators and probe IDs; probes use their own `probe:<name>` parser.

- [ ] Implement strict `load_configuration(profiles_path, inventory_path, *, repository_root)` and `select_profile(bundle, name, *, payload_id=None, historical_case=None)`. Canonical semantic digests use sorted-key compact ASCII JSON over the validated object, not TOML layout.

- [ ] Implement exit precedence in a pure function and exhaustively test all pairs/combinations:

```text
integrity(3) > configuration(2) > phase(4) > runtime(5)
> test failure(6) > explicit optional unavailable(7) > success(0)
```

The summary retains every observed condition even though only one process exit code is returned.

`choose_exit_code` considers only conditions with `affects_exit=true`; all integrity/configuration/phase/runtime/test-failure conditions require true. `optional_unavailable` may use false only when the enclosing `full` plan marks that worker optional, so the condition remains visible while the aggregate may return success. The same reason under a direct `gpu` request uses true and returns `7`. Success is represented by no exit-affecting condition, not a synthetic success condition.

- [ ] Run the focused configuration test directly in a fresh bootstrap snapshot and confirm green.

- [ ] Review checkpoint: run `git diff --check`. With explicit commit authorization only, create `feat(testing): lock orchestration contracts`.

---

### Task 2: Generate the Exact Inventory and Profile Ownership Lock

**Files:**

- Create: `tools/generate_test_inventory.py`
- Create: `tests/test-inventory.json`
- Create: `tests/test-profiles.toml`
- Create: `tests/test_inventory_and_profiles.py`
- Modify: `tools/test_orchestration/configuration.py`
- Modify: `tools/test_orchestration/model.py`

**Interfaces:**

- Consumes: Task 1 strict configuration/models, baseline Git tree `a842c4b6a73a2991a63a481f4107580b72750582`, and working-tree Python test sources parsed only by AST.
- Produces: `tools/generate_test_inventory.py` with default `--check`, explicit inventory `--write`, `--emit-design-capability-review <absolute-temp-path>`, and `--write-design-capabilities --approved-spec-capabilities-sha256 <digest>`; canonical `tests/test-inventory.json`; independently preapproval-capable design and historical scopes in `tests/test-profiles.toml`; and exact inventory/profile digests consumed by every parent/child request.

- [ ] Write failing synthetic-tree tests for AST discovery, direct-method formation, sorted canonical output, duplicate/missing/multiple ownership, unknown payloads, exclusions missing reason/owner/milestone, zero-test selectors, discovery drift, fully expanded scope-partitioned capability digest semantics, both-zero preapproval, token-gated design approval followed by historical-only preapproval, profile-selection refusal for every unapproved applicable scope, cross-scope sharing, digest/row mismatch, dangling/unused capability definitions, and mutations of referenced argv, environment, root, timeout, callable module/qualname, maximum-call, or return-contract fields.

- [ ] Implement deterministic AST discovery of direct `test_*` methods in explicit `unittest.TestCase` subclasses without importing tests. Discover the recorded baseline from Git commit `a842c4b6a73a2991a63a481f4107580b72750582` separately from the implementation working tree. Lock this baseline partition:

In the same AST pass, record exact `setUpModule`/`tearDownModule` and class-local `setUpClass`/`tearDownClass` definitions and emit the module/class lifecycle fixture rows above without adding synthetic test IDs to the 2,367 count. Reject inherited/ambiguous fixture ownership, a fixture spanning payloads, or differing class-level grants among grouped member IDs.

```text
test files:             392
stable IDs:             2367
all-ID digest:          c8e6465527a9b784f4be41947745f6e86d53f45d16fd0d10955009bbb127b37b
historical IDs:         137
historical digest:      77ccf22ac1f52ebbeff7311bf2c4c1fb4f83671a5cfe10f84dbbde655ecb58a8
GPU IDs:                51
GPU digest:             896fb0675371186476df33b13eb7a5d9286dfeb01f53d37daa0f458e72021005
core IDs:               50
core digest:            38166290ad900c24a08c93f08de3376dac92a2c35544a94c3228726b01a02dfc
current IDs:            2129
current digest:         c32575a47a889e7e324db2abb56ef5c5b37295bb6a5cc3e6006cb04c767c6803
explicit exclusions:    0
```

Every digest is SHA-256 of sorted stable IDs joined with LF plus a final LF. The 2,367 lock intentionally supersedes the earlier 2,357 one-process discovery count. New evidence/orchestration test methods are not part of those baseline counts; they are intentionally appended to the final current inventory and receive their own generated count/digest.

- [ ] Assign ownership in this exact order:

  1. Historical: every direct method in the eight exact compiled-global-separation classes from base through v7. Map each ID once to a version payload; a multi-phase payload may execute the same selector at multiple declared commits.
  2. GPU: every method in a class/method carrying the literal `find_spec("cupy")` optional-capability decorator; every method in a class that directly imports `cupy`; and the three methods of `tests/test_legal_river_quotient_cuda_consumer.py::LegalRiverQuotientCudaConsumerDeviceTests`, whose class setup calls the real bounded CUDA consumer. Materialize the resulting exact 51 IDs in the lock; do not reclassify automatically when source changes. Keep all 18 `SharedDirectDeviceSourceSealTests` in current because they explicitly assert CuPy-free/device-free source-seal behavior.
  3. Core: all direct methods in exactly `tests/test_cfr.py`, `tests/test_coalition.py`, `tests/test_evaluation.py`, `tests/test_holdem_cards.py`, and `tests/test_kuhn.py`. This is the deliberately narrow reviewed 50-ID hermetic CPU set.
  4. Current: every remaining applicable ID, exactly 2,129 at baseline.

Every new test file named in either implementation plan is explicitly classified as stabilization/current. A new test outside that reviewed file list, a changed baseline ID, or a changed baseline assignment makes `--check` fail and requires an intentional reviewed inventory/profile update.

- [ ] Emit `tests/test-inventory.json` in canonical UTF-8 JSON with schema `pontius-test-inventory-v1`, baseline commit, exact `baseline_discovery`, exact working-tree `discovery`, and one sorted entry per working-tree ID. Each entry has exactly one `assignment` object or one full `exclusion` object. Baseline entries also record their locked baseline assignment; added stabilization entries record `introduced_after_baseline=true`. Group current/core payloads by test file and GPU payloads by test class so class setup is isolated.

Each `assignment` has exact keys `profile_name`, `payload_id`, and `expectation`. Expectation is one strict variant: `{kind: "pass"}`; `{kind: "platform_conditioned", applicable_platforms: ["windows"|"posix"], skip_safe_reason_code: <stable string>}`; or `{kind: "case_defined"}` for historical IDs only. `applicable_platforms` is sorted/unique/nonempty. Each full exclusion has exact keys `reason`, `owner`, and `milestone`. Each entry also carries its parsed `relative_path`, `case_name`, and `method_name`; `load_configuration` joins entries by `payload_id` into the sorted `PayloadPlan.inventory_items` tuple and retains every validated entry in `ConfigurationBundle.inventory_entries`. Historical ChildRequest items come from the selected case's item expectations, never from a default pass assumption.

- [ ] Define interpreter slots in `tests/test-profiles.toml`: `development` resolves the repository-relative `.venv/Scripts/python.exe` only on Windows and `.venv/bin/python` only on POSIX; any other platform or missing/nonregular executable rejects. `cpython311` resolves only the absolute path in `PONTIUS_CPYTHON311` and requires CPython version `(3, 11)`. `full` requires both. No slot uses ambient `PATH` fallback.

The profile TOML requires exact schema literal `pontius-test-profiles-v1` and has only these top-level keys/tables: `schema_version`, `baseline_commit`, `sealed_current_files_manifest`, `sealed_current_absences_manifest`, `historical_blobs_manifest`, `retained_v7_manifest`, `inventory_path`, `spec_capabilities_sha256`, `capability_bindings_sha256`, `interpreter_slot[]`, `profile[]`, `payload[]`, `historical_case[]`, `overlay[]`, `subprocess_capability[]`, `call_capability[]`, `capability_binding[]`, and `stabilization_test_files`. Each binding has `approval_scope="design"` or `approval_scope="historical_review"`. `spec_capabilities_sha256` covers canonical sorted fully expanded nonempty design-scope bindings whose `item_id` is a core/current/GPU stable ID, lifecycle fixture, or probe; `capability_bindings_sha256` analogously covers nonempty historical-review bindings. The inventory/profile digests bind the complete item universe, and every item absent from the applicable capability bindings is explicitly deny-all—no synthetic no-op capability row is invented. A subprocess record contains its binding plus every stable `subprocess_capability[]` field, including executable role/slot/constraints, argv/template and dynamic-program digest, cwd class, environment delta, timeout, expected return category, allowed/forbidden roots, and descendant permission. A callable record contains its binding plus every `call_capability[]` field: kind (`owner`, `scientific`, `cuda_query`, or `cuda_allocation`), module/qualified name/action, exact maximum calls, and return contract. DLL-directory telemetry is an unconditional non-authorizing preparation observation rule in the guard, never a capability binding or digest row. Host-specific resolved paths, file IDs, and executable hashes are excluded from both checked-in digests; they are measured into `InterpreterIdentity`/`GitToolIdentity`, bound into each runtime request, and independently verified by the child.

Initially both scope definitions/bindings are absent and both digests are the all-zero 64-hex value. Only Task 2's separately parsed design-review generator may operate then; it cannot select a profile, import/launch target code, or write repository state. After the user approves the complete emitted design table/digest and the token-gated write succeeds, core/current/GPU may run with a nonzero `spec_capabilities_sha256` while historical rows remain absent and `capability_bindings_sha256` remains all-zero. Selecting any profile whose applicable scope is unapproved raises `EvidenceConfigurationError("capability_approval_required", "applicable capabilities are not approved")`. Task 10's separately parsed historical-review generator is the only preapproval exception for that scope; it may read historical case metadata and materialize exact read-only proposal clones but never calls `select_profile`, imports target code, or launches a historical payload. Approved historical mode requires a nonzero user-approved historical digest and complete rows whose expansion hashes to it. A capability definition may belong to exactly one scope; reject cross-scope sharing, mixed modes, dangling references, unused definitions, duplicate expanded semantics, missing applicable bindings, a wrong digest, or any mutation that does not change the applicable digest.

The non-capability nested schemas are exact:

```text
development interpreter_slot:
  name="development", resolution="repository_relative",
  windows_relative_path, posix_relative_path, implementation,
  minimum_version=[exact-int, exact-int], required_for_full=exact-bool
exact interpreter_slot:
  name, resolution="environment_absolute", environment_variable,
  implementation, exact_version=[exact-int, exact-int],
  required_for_full=exact-bool
profile:
  name, interpreter_slots, default_interpreter_slot, payload_ids,
  historical_case_ids, subprofiles, gpu_optional,
  budgets={setup_seconds, child_seconds, termination_seconds,
           cleanup_seconds, total_seconds}
payload:
  payload_id, profile_name, target_kind, allowed_interpreter_slots, probe_ids,
  environment_additions, environment_removals, allowed_write_roots,
  forbidden_relative_paths, serialized, ignored_fixture[], lifecycle_fixture[]
payload ignored_fixture:
  relative_path, path_kind, byte_length, raw_sha256
payload module lifecycle_fixture:
  fixture_id="fixture:<relative-path>", kind="module", relative_path,
  member_ids, allowed_write_roots, forbidden_relative_paths, serialized
payload class lifecycle_fixture:
  fixture_id="fixture:<relative-path>::<ClassName>", kind="class",
  relative_path, class_name, member_ids, allowed_write_roots,
  forbidden_relative_paths, serialized
historical_case:
  case_id, phase, commit, root_tree_oid, payload_ids, overlay_ids,
  expected_vector, item_expectation[]
historical pass item_expectation:
  item_id, outcome="pass"
historical negative item_expectation:
  item_id, outcome="expected_negative", phase, exception_type,
  safe_reason_code, body_entered, capability_counters
historical probe item_expectation:
  item_id="probe:<registered-name>", outcome="pass"
positive expected_vector:
  kind="positive", passed, assertion_failed, setup_failed, body_entered,
  owner_calls, scientific_calls
negative expected_vector:
  kind="negative", passed, assertion_failed, setup_failed, body_entered,
  owner_calls, scientific_calls, phase, exception_type, safe_reason_code
overlay:
  overlay_id, source_commit, source_path, destination_path,
  byte_length, raw_sha256
```

Every named array is sorted and unique; `argv` remains the later explicit ordered-token exception. Environment additions are sorted string mappings. Counts/seconds/lengths are exact nonnegative integers (budgets are positive), booleans including `serialized` are exact, paths are normalized to the declared root class, and every reference resolves exactly once. A direct profile's `default_interpreter_slot` is nonnull and belongs to both its `interpreter_slots` and every selected payload's `allowed_interpreter_slots`; `full` has a null default and projects each subprofile once per scheduled binding. Lifecycle fixture member IDs must belong to the same module/class and payload, and every owned module/class fixture is represented exactly once even when it has no positive capability. Direct profiles have empty `subprofiles`; `full` has only `subprofiles` and no direct payload/case IDs. `load_configuration` resolves each profile's `fixture_specs` as the conflict-free union of its referenced payload fixtures; `full` resolves the union of constituent profiles.

Every `HistoricalCase.payload_ids` row is a sorted nonempty unique tuple. Each case item expectation resolves through inventory to exactly one of those payloads, and every named payload owns at least one case item/probe. The engine launches one fresh child per payload and then validates the aggregate `expected_vector`. In particular, the v4 authorization case names distinct `historical:v4-positive` and `historical:v4-authorization-negative` payloads: the 38 positive IDs belong only to the first, the one negative ID only to the second, and the environment flag is granted only to the negative child's exact item capability.

- [ ] Lock these positive profile budgets in seconds, converting once to nanoseconds during parsing:

| Profile | Setup | Child | Termination | Cleanup | Total |
| --- | ---: | ---: | ---: | ---: | ---: |
| `core` | 180 | 900 | 15 | 120 | 1500 |
| `current` | 300 | 7200 | 15 | 180 | 8100 |
| `historical` | 900 | 5400 | 20 | 300 | 7200 |
| `gpu` | 300 | 3600 | 20 | 180 | 4500 |
| `full` | 900 | 27000 | 20 | 300 | 29000 |

`core` and `current` declare both `development` and `cpython311` as allowed, with `development` as their direct default. `historical` and `gpu` allow/default only `development`. `full` schedules core/current once on each supported binding, historical on development, and GPU on development as optional. The selected binding is authoritative for its projected payload rows; no stale payload-level development literal survives a CPython 3.11 projection.

- [ ] Lock the historical selector digests and case grouping:

```text
base source: 21 / 83a33794ecf850587627ace90a9d3a208b82fcf875400ccb6ed7c5cd72cb6e81
v2 source: 8 / 3645c2e5636e658167aafbcac4da1031ebf784416f4c12f05b56e3f9dd87fc9c
v2 retained: 5 / da4886b2674e687b6c336303cb430b8c4d214a1f274db2df23c4a01137415467
v3 source: 9 / 00a4caad1791a20720d133be06f50a9a422a8b691294db4196a5780ae2100813
v4 positive: 38 / 676f497cdedaa8958e96bfefc63808f9335f897621fb8f1d65a0835bfc4bc6f3
v4 negative ID: fa7790a99fecb14eddd78316b017ab7dc82c699866cc851e1d27b97239b52c52
v5 retained: 18 / f927b8680c80739d04b64c667d757377c05723ec7eab25a224ba31bacdc4843d
v6 phases: 17 / 30d6a566cc57298e593a0fa7ac8d66890ad86cdc03df25aca2e1e9915cd7ec7d
v7 phases: 20 / 6f62dc5b6cd8b61709d9ef148384fa9cf319d54b88281d6ea45245496852112c
```

Every historical case also stores the exact root-tree OID and must match the evidence manifest:

```text
88148da07324c13b79c72ea494b14167a975c001  bc5d1952f690da5d49275344919de36224af26cb
08bb6857f47f9669b8f531c65079d4decd52a573  0d01a4133a4e6ab10467ad0bd298630149702a73
3de8e0c9eebf67f2cc2573041242a869468de6e9  ea80b86ac60cb324e3c18ddad83d8bbba0ade933
77feb7c78990ca53e70b1302a6866fe5d781411f  d26ba99c033875342a652ae352067beee1ca44ee
ba6a3418b7c991238cc1a65898fd61fa03b4a3cb  73b53cb04c91459e8b7028ccd292b972d2dfdf69
815d23c115289347e3d4028a4866eb9f87d4669a  894c026603156df4bba1134ba9861e98bd3a6663
5c0c9a401e5f2ebf59296832d954d0075c4d4624  f3418410c442a4d06c62aba9777def72633ca5c5
d633f3fb469a27dee688587293c6efb1d2cb2757  9c9ff658c2836bde5d1df71f5596d1d6aa1a5bd2
cbfa3598f22c7aba7d824f71356ca156f8b01b0c  9873ff13131c91b058307643dc838a8452268fbb
56127da2970f5a8a8056a97a247ebe1fdf4b983b  ee2437ba1b2efbf2dc4ab3c21bbacdbf26c58648
aaca2dda40e29be8ebd091d58e7853bce1c62fd8  e7bd077f40b1970e9b40a83c891996ab02cd5ffd
```

- [ ] Add exact overlay and capability schemas to the profile TOML. A subprocess capability contains portable executable role/slot/constraints, exact argv or fixed tokenized template, dynamic-program digest for `-c`, cwd class, environment additions/removals, timeout, expected return category, read/write roots, and fixed-descendant permission. A call capability contains exact kind/module/qualified-name/action/maximum-call/return-contract fields. Runtime executable identity is never a checked-in field. Start with both scopes absent and both digests all-zero. The design review generator statically derives the complete core/current/GPU stable-ID, fixture-ID, and probe-ID subprocess/call surface—including current source-seal subprocess tests and exact CUDA query/allocation calls—while DLL bootstrap remains only a hard-coded non-authorizing observation rule. Wildcards and shell commands are invalid. Task 10 alone may later populate historical-review rows through its separate approved write command after exact historical-clone materialization exists.

`SubprocessCapability.executable_slot` is exactly `active_worker`, `development`, `cpython311`, or `git`. A target call to `sys.executable` uses `active_worker`; expansion binds its runtime executable field byte-for-byte to the enclosing child/worker `InterpreterBinding.identity`, so the same approved portable row works when core/current are projected under CPython 3.11. Fixed Python slots are permitted only when the reviewed test intentionally invokes a different configured interpreter. `git` binds only the request's measured `GitToolIdentity`. Any mismatch between role/slot/constraint and the measured runtime identity rejects before spawn.

- [ ] Run inventory `--write`, inspect all 2,367 baseline assignments and every then-present stabilization assignment, and prove `--check` plus focused tests pass in a new snapshot while both capability scopes remain absent/all-zero. Implement and test the two design-review/write commands now, including static AST/literal extraction, fail-closed no-target-spawn behavior, the complete nonempty stable/fixture/probe binding table plus a separately enumerated deny-all item list bound by inventory digest, unresolved-dynamic blockers, host-specific diagnostics outside the digest, fresh rederivation, token mismatch refusal, atomic scope-only write, and preservation of the other scope. Do not emit for approval or write design rows yet: Tasks 3-11 intentionally add current-owned process/guard/workspace tests. Task 12 performs one final emission/approval/write over the complete stabilized ID universe. Ordinary inventory regeneration must preserve/revalidate any approved scope; drift always requires a new emitted review and token, never reset or auto-approval.

- [ ] Review checkpoint: run `git diff --check`. With explicit commit authorization only, create `build(testing): lock stable test ownership`.

---

### Task 3: Implement the Atomic Parent/Child Protocol and CLI Composition Root

**Files:**

- Create: `tools/test_orchestration/protocol.py`
- Create: `tools/run_tests.py`
- Create: `tests/test_test_orchestration_protocol.py`
- Create: `tests/fixtures/test-orchestration-protocol/golden-request-windows.json`
- Create: `tests/fixtures/test-orchestration-protocol/golden-result-windows.json`
- Create: `tests/fixtures/test-orchestration-protocol/golden-request-posix.json`
- Create: `tests/fixtures/test-orchestration-protocol/golden-result-posix.json`
- Create: `tests/fixtures/test-orchestration-protocol/duplicate-key-request.json`
- Create: `tests/fixtures/test-orchestration-protocol/malformed-result.json`
- Modify: `tools/test_orchestration/model.py`
- Modify: `tools/test_orchestration/configuration.py`

**Interfaces:**

- Consumes: Task 1 `ProfilePlan`, `InterpreterIdentity`, `TargetIdentity`, typed errors, and Task 2 inventory/profile semantic digests.
- Produces: immutable child wire `ChildRequestV1`/`ChildResultV1` plus parent-owned `ChildExecutionResult`; `write_child_request_atomic(path: Path, request: ChildRequestV1) -> None`; `read_child_request(path: Path, *, maximum_bytes: int = 16 * 1024 * 1024) -> ChildRequestV1`; `read_child_result(path: Path, request: ChildRequestV1, *, maximum_bytes: int = 16 * 1024 * 1024) -> ChildResultV1`; `write_child_result_atomic(path: Path, result: ChildResultV1) -> None`; `reconcile_child_execution(request: ChildRequestV1, report: ChildResultV1 | None, process_outcome: ProcessOutcome) -> ChildExecutionResult`; Windows/POSIX byte-exact golden pairs plus malformed data vectors; and `tools.run_tests.main(argv: Sequence[str] | None = None) -> int`.

- [ ] Write failing tests for exact request/result fields, duplicate JSON keys, missing/extra fields, wrong types, booleans as integers, unsorted/duplicate IDs, digest/run-ID mismatch, oversized files, incomplete results, non-atomic temp results, and result/request set disagreement.

- [ ] Implement `ChildRequestV1` with exactly these top-level keys:

```text
schema_version, run_id, profile, payload_id,
profile_definition_sha256, inventory_sha256,
harness, target, interpreter, items, guard_policy,
subprocess_capabilities
```

`harness` contains `root` and `test_child_sha256`; `target` contains kind/root/HEAD/root-tree/file-inventory digest; `interpreter` contains the full recorded identity. Each item is either a strict unittest selector with expected vector or a strict `probe:` selector.

Use schema version `pontius-child-request-v1` and a canonical lowercase UUID `run_id`. Nested objects reject missing/extra/duplicate keys and have these exact shapes/types:

```text
harness:
  root: absolute normalized string
  test_child_sha256: lowercase 64-hex string
target:
  kind: "current_snapshot" | "historical_clone"
  root: absolute normalized string
  head_commit: lowercase 40-hex string
  root_tree_oid: lowercase 40-hex string
  file_inventory_sha256: lowercase 64-hex string
interpreter:
  executable, resolved_executable, platform_identity, executable_sha256,
  implementation, prefix, base_prefix, distributions_sha256: strings
  version: [exact-int, exact-int, exact-int, string, exact-int]
  no_user_site, safe_path, dont_write_bytecode: exact booleans
  dependency_lock_sha256: lowercase 64-hex string | null
unittest item:
  kind: "unittest"
  stable_id, relative_path, case_name, method_name: strings
  expected: expected object
probe item:
  kind: "probe"
  probe_id: "probe:<registered-name>"
  expected: expected object
expected object:
  outcome: "pass" | "expected_negative" | "expected_skip"
  platform_predicate: "all" | "windows_only" | "posix_only"
  phase: "setup" | "body" | "probe" | null
  exception_type, safe_reason_code: string | null
  body_entered: exact boolean
  capability_counters: sorted mapping of string to exact nonnegative int
guard_policy:
  mode: string
  primary_root: object with exact string keys resolved_path,
                platform_identity, capture_sha256
  allowed_import_roots, forbidden_import_prefixes, allowed_write_roots,
  forbidden_relative_paths: sorted unique string arrays
  call_capabilities: sorted fully expanded call capability rows
  lifecycle_fixtures: sorted exact `LifecycleFixturePlan` rows
  event_limit: exact positive int
call capability row:
  item_id, capability_id: stable/probe/fixture and capability IDs
  kind: "owner" | "scientific" | "cuda_query" | "cuda_allocation"
  module_name, qualified_name, action, return_contract: nonempty strings
  maximum_calls: exact positive int
subprocess_capability row:
  item_id (stable ID or registered probe/fixture ID) plus every exact
  `SubprocessCapability` field from Task 1;
  runtime_executable={role,resolved_path,platform_identity,raw_sha256}
    and must satisfy the stable slot/constraints;
  argv/argv_template are ordered string-token arrays and preserve duplicates;
  environment_additions is a sorted string-to-string mapping;
  environment_removals/read_roots/write_roots are sorted unique string arrays;
  timeout is an exact positive int and descendant permission an exact boolean
```

The request's `items` and expanded `subprocess_capabilities` arrays are sorted by stable/probe ID. `profile_definition_sha256` and `inventory_sha256` are lowercase 64-hex; all unqualified scalar IDs are nonempty strings; all integer validation rejects booleans.

- [ ] Implement `ChildResultV1` with exactly these top-level keys:

```text
schema_version, run_id, profile, payload_id,
profile_definition_sha256, inventory_sha256,
interpreter, target, requested_ids, prepared_ids,
executed_ids, outcomes, counts, capability_counters,
capability_events, child_status,
duration_ns, completed
```

Each outcome records one terminal projection plus its body and aggregate-fixture diagnostics. This preserves an earlier body result if a later class/module teardown fails without creating a second outcome row. Do not persist arbitrary exception text or launch tokens.

Use schema version `pontius-child-result-v1`. `interpreter` and `target` must be field-for-field equal to the validated request objects. The remaining nested objects have these exact shapes/types:

```text
outcome:
  stable_id: string
  status: "passed" | "assertion_failed" | "setup_failed" | "error" |
          "expected_negative_matched" | "skipped" | "cancelled" |
          "runtime_safety_stop"
  body_status: "not_entered" | "passed" | "assertion_failed" | "error" |
               "expected_negative_matched" | "skipped" | "cancelled" |
               "runtime_safety_stop"
  duration_ns: exact nonnegative int
  body_entered: exact boolean
  primary_failure_phase: "module_setup" | "class_setup" | "test_setup" |
                         "body" | "test_teardown" | null
  primary_exception_type, primary_exception_message_sha256: string | null
  aggregate_teardown_error_phase: "class_teardown" | "module_teardown" | null
  aggregate_teardown_exception_type,
  aggregate_teardown_exception_message_sha256: string | null
  safe_reason_code: string | null
counts:
  requested, prepared, executed, passed, assertion_failed, setup_failed,
  error, expected_negative_matched, skipped, cancelled,
  runtime_safety_stop: exact nonnegative ints
capability_counters:
  total_events, forbidden_imports, cuda_queries, cuda_allocations,
  owner_calls, scientific_calls, retained_write_attempts,
  primary_write_attempts, subprocess_allowed, subprocess_denied,
  filesystem_denied, dll_directory_bootstrap_events: exact nonnegative ints
capability_event:
  sequence: exact nonnegative int
  phase: "bootstrap" | "preparation" | "module_setup" |
         "class_setup" | "test" | "class_teardown" |
         "module_teardown" | "result_write"
  item_id: stable/probe/fixture ID | null
  operation, reason_code: nonempty strings
  decision: "allowed" | "denied" | "observed"
  target_sha256: lowercase 64-hex string
child_status:
  "completed" | "test_failure" | "runtime_safety_stop" | "cancelled"
```

`requested_ids`, `prepared_ids`, and `executed_ids` are sorted unique string arrays. `outcomes` and capability events are ordered by requested ID and sequence respectively. Top-level `duration_ns` is an exact nonnegative integer and `completed` an exact boolean; every aggregate count is recomputed from the one terminal `status` per outcome rather than trusted. A class/module setup failure yields `status="setup_failed"`, `body_status="not_entered"`, and the exact setup `primary_failure_phase` for each affected member. A class/module teardown failure changes each affected member's one terminal status to `error`, preserves its prior `body_status`/primary diagnostics, and fills only the three aggregate-teardown fields. Without aggregate teardown failure those three fields are null. Field combinations outside these projections reject.

`expected_skip` is valid only when the platform predicate excludes the current platform, `safe_reason_code` equals the inventory-locked platform reason, `body_entered=false`, `body_status="skipped"`, and every failure/exception field is null. A skip on an applicable platform or any undeclared skip is a test failure.

For `completed=true`, requested, prepared, executed, and outcome ID sets must match exactly. A fatal guard/runtime event may atomically emit `completed=false` with the executed prefix solely as bounded diagnostics; semantic validation deliberately rejects it as runtime category `5`, so it is never mistaken for a valid partial test run.

`ChildResultV1` deliberately contains no stdout/stderr claim. Only after the contained lease has observed descendant exit and drained both OS pipes to EOF does the parent compute `CapturedOutputIdentity` (`byte_length`, full-stream SHA-256, and whether bounded raw retention truncated) and call `reconcile_child_execution`. The reconciler never edits the atomic report: it pairs the immutable report with `ProcessOutcome`, requires run/digest/interpreter/target/return-category agreement, and returns a separate immutable `ChildExecutionResult`. Missing report, premature EOF, drain failure, unexpected process status, or mismatch is runtime category `5`; ordinary test failure with a valid report remains category `6`.

Every internal protocol producer—test child, interpreter probe, GPU probe, and full worker—exits `0` if and only if it has atomically committed one final schema-valid report file and performed no operation afterward except ordinary interpreter teardown. The report may legitimately encode test failure, optional unavailability, or `completed=false` runtime/cancellation diagnostics; the parent maps those semantics from the validated JSON. A nonzero/signal exit, an exit `0` without exactly one valid report, or any report followed by an abnormal exit is a protocol failure and maps to runtime category `5`; never use child exit `6` or `7`. Only the public composition root returns stable profile exits `0/2/3/4/5/6/7`.

- [ ] Implement duplicate-rejecting JSON parsing and both parent-request/child-result atomic writers to a sibling temp file followed by flush, `fsync`, and `os.replace`. The consumer requires the final file to have been absent before producer start, be a regular non-reparse file, remain below its protocol directory, and satisfy its size bound. Generate and inspect six byte-level data vectors: canonical request/result pairs containing normalized absolute Windows paths and normalized absolute POSIX paths, plus one duplicate-key request and one malformed result. Keep the public readers native-only. Give the parent decoder and the child's file-local decoder a private, test-only injectable path-syntax validator so conformance tests on either host decode and re-encode both golden pairs without touching those paths; native atomic-I/O tests must additionally accept only the host-native pair and reject the foreign pair. Shared and file-local implementations must accept/reject the same bytes and canonicalize each applicable golden output identically.

- [ ] Implement `tools/run_tests.py` as a small composition root with `main(argv: Sequence[str] | None = None) -> int`. Under `-P`, it resolves its own repository root, validates that exact root, adds only that explicit root to the parent import path, imports `tools.test_orchestration`, and dispatches `core|current|historical|gpu|full`. Support public `--payload`, `--case`, and `--json-summary <absolute-path>` options only; reject incompatible selectors before setup. A separately parsed internal worker request is accepted only from an already validated H path and is never exposed as a public owner-launch flag.

`--json-summary` writes schema `pontius-run-summary-v1` with exact top-level keys `schema_version`, `run_id`, `requested_profile`, `profile_summaries`, `conditions`, `exit_code`, `duration_ns`, and `completed`. Nested rows are canonical `ProfileSummary`/`PayloadSummary`/`WorkerSummary`/`ObservedCondition` serializations from Task 1. Encode sorted-key compact UTF-8 JSON plus one LF; arrays follow their declared canonical order. `write_run_summary_atomic(path: Path, summary: RunSummary) -> None` requires an absolute path outside the primary checkout, final-path absence, a validated regular nonreparse parent, sibling temp creation, flush/fsync/replace, and final identity/size verification. It never overwrites. Condition context permits only schema-declared stable strings, counts, booleans, normalized root classes, and digests; raw output, arbitrary exception text, environments, launch tokens, and secret values reject serialization.

- [ ] Translate one typed failure into one structured stderr diagnostic and stable exit category. Keep human progress on stdout separate from machine JSON. Never print secrets, launch tokens, full child environments, or unbounded captured output.

- [ ] Rerun configuration/protocol tests in a fresh bootstrap snapshot.

- [ ] Review checkpoint: run `git diff --check`. With explicit commit authorization only, create `feat(testing): add strict orchestration protocol`.

---

### Task 4: Implement Monotonic Budgets and Contained Process Adapters

**Files:**

- Create: `tools/test_orchestration/process.py`
- Create: `tools/test_orchestration/windows_job.py`
- Create: `tools/test_orchestration/posix_group.py`
- Create: `tests/test_test_orchestration_process.py`
- Create: `tests/test_test_orchestration_windows_job.py`
- Create: `tests/test_test_orchestration_posix_group.py`

**Interfaces:**

- Consumes: Task 1 `StageBudgets`/typed runtime errors, immutable argv/environment/cwd process specifications, and a monotonic clock.
- Produces: frozen `ProcessSpec` and `ProcessOutcome`, context-managed `ContainedProcessLease`, `ProcessAdapter.spawn_contained(process_spec: ProcessSpec) -> ContainedProcessLease`, and `run_contained(lease: ContainedProcessLease, process_spec: ProcessSpec, budgets: StageBudgets) -> ProcessOutcome` with lease ownership retained by the engine.

- [ ] Write fake-clock/fake-process tests for normal exit, child timeout, graceful stop, output drain, forced tree termination, descendant verification, cancellation, stage-budget exhaustion, cleanup reserve, close-on-every-path behavior, and owned-root versus inherited-worker containment.

- [ ] Define a platform-neutral `ProcessAdapter.spawn_contained(ProcessSpec) -> ContainedProcessLease` seam. The engine owns the live context-managed lease through descendant termination and post-evidence verification; `run_contained(lease, process_spec, budgets)` never closes it. The state machine cannot consume termination/cleanup reserves and returns bounded stdout/stderr identities plus a structured outcome. The engine closes the lease after post-evidence checks and before verified filesystem cleanup on every path.

Use these exact process value contracts: `ProcessSpec(argv, cwd, environment, stdout_limit_bytes, stderr_limit_bytes, containment_mode)`; Task 1 `CapturedStreamIdentity(byte_length, raw_sha256, truncated)`; and `ProcessOutcome(status, return_code, stdout, stderr, duration_ns, graceful_stop_requested, forced_tree_termination, descendants_confirmed)`. `containment_mode` is exactly `owned_tree` or `inherited_worker_tree`. Captured streams persist identities only—never raw or decoded output tails. `status` is exactly one of `exited`, `timed_out`, `cancelled`, `spawn_failed`, or `containment_failed`. A `ContainedProcessLease` exposes read-only `pid`, `request_graceful_stop() -> bool`, `force_terminate() -> None`, `wait(timeout_ns: int) -> int | None`, `drain_until_eof(timeout_ns: int) -> tuple[CapturedStreamIdentity, CapturedStreamIdentity]`, `active_descendant_count() -> int`, and idempotent `close() -> None`, in addition to context-manager methods.

The composition root/direct-profile parent always uses `owned_tree`. A `full` worker itself is one `owned_tree` child of the full coordinator; every payload spawned inside that worker uses `inherited_worker_tree` and must remain in the worker's already-owned containment domain. In inherited mode the worker may signal/wait/drain its direct child but cannot create, enumerate, kill, or close a nested group/job. It validates only direct-child exit and pipe EOF. On timeout, cancellation, drain failure, or guard failure it writes a bounded incomplete worker result/stop condition and exits. After any worker exit—and before accepting even a completed worker result—the full coordinator's owned lease requires whole Job/process-group disappearance; if members remain it terminates the owned tree and classifies runtime failure. Target subprocess guards deny `setsid`, `setpgid`, Windows breakaway flags, job reassignment, or any equivalent containment escape.

- [ ] Implement Windows `owned_tree` creation through `ctypes` `CreateProcessW`, not `subprocess.Popen(CREATE_SUSPENDED)`, because the primary thread handle must remain available for assignment and resume. The exact order is: create inheritable pipes; create suspended/new-process-group/unicode-environment process; create and configure a Job Object with `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE` and no breakaway flags; assign the suspended process; resume the primary thread; close inherited parent handles. In `inherited_worker_tree`, create the direct child without breakaway or a nested Job so it inherits the coordinator-owned worker Job; retain only direct process/pipe handles.

- [ ] Implement Windows timeout flow with `GenerateConsoleCtrlEvent(CTRL_BREAK_EVENT, process_group_id)` as the graceful request, concurrent pipe drain, grace wait, `TerminateJobObject`, process wait, active-process-count query, and confirmation that every descendant exited. If the control event cannot be delivered, record that condition and fall back immediately to `TerminateJobObject`. Keep the Job handle in the lease until the engine finishes post-evidence verification; closing it is the final kill-on-close backstop.

- [ ] Add Windows integration fixtures for a direct owned child/grandchild and a full-style owned worker with an inherited payload/grandchild. Force root-level timeout/safety stop, assert every PID exits even if the worker is killed first, assert bounded output is drained, and assert the verified temp tree can be cleaned. Do not use any primary-checkout path as its cwd or write root.

- [ ] Implement POSIX `owned_tree` with `start_new_session=True`, `SIGTERM`, grace, `SIGKILL`, drain, wait, and process-group disappearance verification. Implement `inherited_worker_tree` with `start_new_session=False` and explicit inheritance of the worker's process group; it never calls `killpg` or reports tree disappearance while the worker is alive. Add a full-style integration fixture where an owned worker starts an inherited payload/grandchild, then the root coordinator kills the worker group and proves no descendant remains. Platform-inapplicable integration tests skip with an exact reason; fake-adapter contract tests always run.

- [ ] Rerun process tests twice to catch handle/timing leaks.

- [ ] Review checkpoint: run `git diff --check`. With explicit commit authorization only, create `feat(testing): contain every child process tree`.

---

### Task 5: Implement Interpreter Identity and Minimal Environments

**Files:**

- Create: `tools/test_orchestration/environment.py`
- Create: `tests/test_test_orchestration_environment.py`
- Modify: `tools/test_orchestration/model.py`

**Interfaces:**

- Consumes: Task 1 interpreter-slot configuration and `InterpreterIdentity`, plus Task 4 contained process execution.
- Produces: `resolve_interpreter_slot(bundle: ConfigurationBundle, slot_name: str) -> Path`; `resolve_git_tool(environment_variable: str = "PONTIUS_GIT") -> GitToolIdentity`; atomic `InterpreterProbeResultV1`; `probe_interpreter(executable: Path, *, process_adapter: ProcessAdapter, budgets: StageBudgets, protocol_root: Path) -> InterpreterIdentity`; and `build_child_environment(interpreter: InterpreterIdentity, *, git_identity: GitToolIdentity | None, target_root: Path, temp_root: Path, declared_additions: Mapping[str, str], declared_removals: tuple[str, ...]) -> Mapping[str, str]`.

- [ ] Write failing tests for absolute/resolved executable identity, implementation/version/prefix/base-prefix, executable hash/file identity, sorted installed-distribution fingerprint, optional lock digest, undeclared/missing slot, wrong Python minor version, absolute `PONTIUS_GIT` identity, and forbidden fallback to PATH for either executable.

- [ ] Probe interpreters only through the contained process adapter. Invoke the fixed-digest command `<python> -B -P -c <probe-program> <canonical-run-id> <absolute-result-path>` with a result path below a dedicated `protocol_root`; stdout/stderr remain identity-only. The file-local probe program atomically writes schema `pontius-interpreter-probe-result-v1` with exact keys `schema_version`, `run_id`, `implementation`, `version`, `executable`, `prefix`, `base_prefix`, `no_user_site`, `safe_path`, `dont_write_bytecode`, `distributions_sha256`, `duration_ns`, and `completed`. The parent creates the canonical UUID run ID, passes it in that exact argv position, requires result absence before spawn, then duplicate-rejects/size-bounds/identity-checks the result before combining it with the independently measured executable path/hash/file identity. Crash, timeout, missing/malformed/mismatched JSON, or executable identity drift is runtime failure; the protocol file is cleaned only after contained descendant and evidence checks.

- [ ] Build a fresh case-insensitive child environment with only the resolved interpreter/Git directories, required Windows system directory, `SystemRoot`, `WINDIR`, `ComSpec`, `PATHEXT`, dedicated `TEMP`/`TMP`, and profile-declared keys. Set exactly:

```text
PYTHONPATH=<T>/src
PYTHONDONTWRITEBYTECODE=1
PYTHONSAFEPATH=1
PYTHONNOUSERSITE=1
PYTHONHASHSEED=0
PYTHONUTF8=1
```

On POSIX, the base allowlist is `PATH`, dedicated `HOME`, `LANG`, `LC_ALL`, and dedicated `TMPDIR`, plus profile-declared keys; child TEMP/TMP remain dedicated too. Every orchestrator and capability-authorized Git process sets `GIT_CONFIG_NOSYSTEM=1`, sets `GIT_CONFIG_GLOBAL` to `NUL` on Windows or `/dev/null` on POSIX, and uses a dedicated HOME/USERPROFILE so ambient system/global Git configuration cannot re-enter. Ambient Python startup/user-site/inspect, CUDA, proxy, and lifecycle variables are absent unless the exact profile declares them.

Construct PATH from the parent directories of `interpreter.resolved_executable` and, only when the resolved payload has an approved Git capability, `git_identity.resolved_executable`, followed by the required OS system directory; reject a null/mismatched Git identity when such a capability exists. Apply `declared_removals` before exact `declared_additions`, reject case-folded collisions/reserved-key overrides, and never resolve either tool through the resulting PATH.

- [ ] Resolve Git only from absolute `PONTIUS_GIT`, require a regular nonlink/nonreparse executable, and record its measured identity before constructing `HardenedGit`. Record the absolute Git executable and interpreter identities in every applicable request. A child independently compares the observed interpreter fields with the request before importing tests; workers independently remeasure Git before use.

- [ ] Add an effective-flags integration test that runs a contained child with the exact structural command `<python> -B -P <H>/tools/test_child.py --request <protocol-dir>/request.json --result <protocol-dir>/result.json` once Task 6 supplies the child. Before that, exercise the same flags with a tiny temp probe outside the repository.

- [ ] Rerun environment/process tests in a fresh bootstrap snapshot.

- [ ] Review checkpoint: run `git diff --check`. With explicit commit authorization only, create `feat(testing): bind interpreters and scrub environments`.

---

### Task 6: Implement Direct unittest Loading and Structured Results

**Files:**

- Create: `tools/test_child.py`
- Create: `tests/test_test_orchestration_child.py`
- Test data: `tests/fixtures/test-orchestration-protocol/*.json`
- Modify: `tools/test_orchestration/protocol.py`
- Modify: `tools/test_orchestration/environment.py`

**Interfaces:**

- Consumes: Task 3's six byte-level Windows/POSIX golden and malformed request/result vectors plus wire specification as data, Task 5 interpreter/environment contract, and exact target files rooted only at `T`; `test_child.py` imports no Task 3 module.
- Produces: `tools.test_child.main(argv: Sequence[str] | None = None) -> int`, direct stable-ID-to-`unittest.TestCase` preparation with no discovery, and one atomic `ChildResultV1` whose completed/fatal semantics exactly match Task 3.

- [ ] Write synthetic-target tests proving exact class/method instantiation, no discovery, no inherited method substitution, zero-test rejection, request/prepared/executed set equality, one terminal outcome per ID, import freshness across children, and no harness/primary path in `sys.path`.

- [ ] In the child, validate the request/result paths before any repository import. Install guards, then synthesize a `tests` package whose sole `__path__` is `T/tests`. Load each selected file with `spec_from_file_location` under `tests.<module>`, obtain the class only from `vars(module)`, require an exact `unittest.TestCase` subclass, require the method in `case_type.__dict__`, and instantiate exactly that method.

- [ ] Run exact unittest lifecycle semantics through a file-local `TestSuite` subclass: module import remains deny-all preparation; before `setUpModule`/`tearDownModule`, activate the exact module fixture ID; before `setUpClass`/`tearDownClass`, activate the exact class fixture ID; before each case `setUp`/body/`tearDown`, activate its stable ID. Clear context in `finally` after every phase. The requested payload must contain the fixture row and complete member-ID set; a missing/extra/mixed-grant row rejects before fixture execution. A module/class setup failure deterministically emits one `setup_failed`, body-not-entered outcome for every affected member. A teardown failure updates each affected member's existing row through Task 3's exact single-terminal projection: terminal `error`, preserved `body_status`/primary diagnostics, and populated aggregate-teardown fields. It never appends a second outcome or changes requested/prepared/executed membership. Do not bypass or manually omit any unittest fixture hook.

- [ ] Implement file-local duplicate-rejecting request parsing, canonical result encoding, and atomic result writing inside `test_child.py`. Run shared conformance tests that feed both the parent protocol implementation and child file-local functions all six exact fixture byte streams, use the explicit private Windows/POSIX syntax validators for both golden pairs, exercise duplicate-key/malformed rejection, and compare canonical bytes. Separately prove each public/native reader rejects the foreign-path pair before filesystem use. The conformance test loads child functions by exact file location in a synthetic namespace; production child code never imports a sibling helper.

- [ ] Never call `unittest.discover`, `loadTestsFromModule`, or `loadTestsFromNames`. Use a custom `TestResult` to record start/stop, outcome, duration, setup/body distinction, bounded output digest, and one terminal result.

- [ ] Install the sole legacy alias `test_reduced_river_sizing_oracle` only while loading `tests/test_dyadic_action_abstraction_confirmation.py` and `tests/test_fresh_collision_repair_structures.py`, and point both names to the same module object. Reject every new bare `test_*` import.

- [ ] For expected-negative items, run normal `setUp`; never instantiate a different method or bypass setup. Mark `expected_negative_matched` only when phase, exception type, safe reason contract, body-entered count, and capability counters match. An unexpected pass or different failure is a test failure.

- [ ] Atomically write the strict result after ordinary test failures and continue the remaining IDs in that payload. On a runtime guard violation, stop the child immediately and, when safe, write the bounded `completed=false` fatal diagnostic described in Task 3. The parent rejects its set mismatch as runtime category `5`; a missing/malformed result is the same category.

- [ ] Run child tests through the contained adapter in a bootstrap snapshot and compare two independent results after removing run ID and timings.

- [ ] Review checkpoint: run `git diff --check`. With explicit commit authorization only, create `feat(testing): load exact unittest ids in fresh children`.

---

### Task 7: Install Child Capability Guards Before Test Imports

**Files:**

- Create: `tests/test_test_orchestration_guards.py`
- Modify: `tools/test_child.py`
- Modify: `tools/test_orchestration/configuration.py`
- Modify: `tests/test-profiles.toml`

**Interfaces:**

- Consumes: Task 2 binding/capability schemas, Task 3 child request, Task 6 direct test lifecycle, and the authenticated primary-root identity.
- Produces: irreversible `install_child_guards(request: ChildRequestV1, *, primary_root: PrimaryRootIdentity, protocol_root: Path, result_path: Path) -> GuardSession`, bounded counters/events incorporated into `ChildResultV1`, synthetic-table executable conformance tests for every design capability kind, and tests of the separate non-authorizing DLL observation rule. Checked-in design scope remains preapproval until the final Task 12 table covers all later stabilization tests; historical-review scope remains separately preapproval until Task 10.

`CapabilityEvent` has exact fields `sequence`, `phase`, `item_id`, `operation`, `decision`, `reason_code`, and `target_sha256`; `item_id` is null only during declared bootstrap/preparation/result-write phases and is mandatory during module/class/test lifecycle phases. It never stores a raw secret, launch token, arbitrary exception text, or unbounded path. `install_child_guards` requires `protocol_root` to be the already authenticated request/result directory and `result_path` to equal the normalized final `--result` path below it, absent at installation. It derives one private sibling-temp pathname pattern from that final name. Outside an active item context, sensitive imports/calls/subprocesses/writes are deny-all except exact create/write/fsync/replace operations from that one sibling temp to that one final result after context is cleared; reads, overwrites, alternate temp names, a second result, links/reparse entries, and any escape remain denied. Observation-only DLL-directory events may be recorded during preparation but confer no capability. `GuardReport` has exact fields `counters` and `events`. `GuardSession` exposes only `set_item_context(item_id: str, phase: str) -> None`, `clear_item_context() -> None`, `begin_result_write() -> GuardReport`, and diagnostic `snapshot() -> GuardReport`. `begin_result_write` is one-shot, requires cleared context, appends the final logical `result_write_authorized` event, freezes counters/events, enters only the exact writer latch, and returns the immutable report to serialize. The subsequent exact temp create/write/fsync/replace syscalls are enforced but deliberately non-reporting, avoiding a report-about-its-own-write cycle. Any denied or out-of-sequence writer operation aborts the producer; the parent then observes a missing/invalid report or abnormal exit and returns runtime category `5`. Installing a second session, entering result-write twice, or uninstalling guards is a runtime-contract error.

- [ ] Write synthetic tests for denied/allowed imports, CUDA adapter calls, observation-only Windows DLL-directory bootstrap events, historical owner/scientific calls, writes, rename/delete/link/symlink operations, subprocess calls, shell execution, dynamic `-c` digest, cwd/environment mismatch, descendant shape, bounded event reporting, per-stable-ID context, and the one exact final-plus-sibling-temp result authorization. Prove `result_write_authorized` is the last serialized event and all counts freeze before bytes are encoded; prove an alternate temp name, overwrite, second result, link/reparse target, pre-context-clear write, post-freeze reporting attempt, or protocol-root escape aborts and is classified by the parent as protocol/runtime failure.

- [ ] Before test import, install an irreversible `sys.addaudithook` for open/mutation/subprocess events, then a meta-path blocker/wrapping loader; write guards around `builtins.open`, `io.open`, `os.open`, mutating/destructive `os` functions, and link creation; subprocess guards around `subprocess.Popen`/helpers plus `os.system`/spawn/exec families; and callable wrappers for declared CUDA, owner, and scientific-executor seams. On Windows, observe `os.add_dll_directory` before package import and report only normalized path identity/digest, success/failure category, and call count; do not change or suppress the existing package bootstrap. The audit hook provides a second observation layer; wrappers perform exact path/capability normalization and counters.

- [ ] Set stable-ID context before each `TestCase.run` (and verify `TestResult.startTest` sees the same ID), clear it after `stopTest`, and wrap the exact test method to count body entry without bypassing `setUp`. Use Task 6's exact module/class fixture contexts around their hooks. Record denied attempts before raising a child-local runtime-contract exception.

- [ ] Enforce profile modes: core/current deny `cupy`/`cupyx`, declared CUDA queries/allocations, v2-v7 owner entrypoints, and retained lifecycle writes; historical denies real science and writes outside T while allowing only exact synthetic contracts; GPU permits declared GPU adapters but still denies historical owners and retained writes.

- [ ] Every mode unconditionally treats the resolved primary root as forbidden and carries exact allowed-write roots. TEMP/TMP is always a dedicated payload directory; additional T-local roots are permitted only by the payload's reviewed path/type policy; retained relative paths remain forbidden even inside T except declared historical fixture setup performed by the parent before child start. The child bootstrap alone receives a private capability for the exact result temp/final paths after test context is cleared; tests never receive that path as a write root. Add a primary-write negative test for core, current, GPU, and historical.

- [ ] Lock synthetic owner exceptions to only these four stable IDs: the named synthetic journal methods in base, v2, and v3, plus v4 `test_public_pre_writer_failure_consumes_the_attempt`. Allow one declared clone-local non-scientific entrypoint per binding and no public campaign mode.

- [ ] Lock subprocess-bearing historical IDs/capabilities from the approved matrix: base source probe; v2 absolute-Git and retained `check-attr`; v3 post-scrub probe; v4 launcher/import/provenance/fresh-reader/temp-repository methods; v5 launcher; v6/v7 source and launcher probes; and every exact Git query used by v7 authorization setup/teardown. Bind every Python `-c` body by raw or fixed-template SHA-256. The v4 authorization-negative child gets `PONTIUS_ADR0467_AUTH_READER_CHILD=1` and no nested-unittest capability.

- [ ] Run every guard test in a fresh child, then scan the result counters to prove denied/allowed distinctions do not rely merely on final files or `sys.modules`.

- [ ] Review checkpoint: run `git diff --check`. With explicit commit authorization only, create `feat(testing): enforce child capabilities`.

---

### Task 8: Capture and Materialize an Exact Current-State Harness

**Files:**

- Create: `tools/test_orchestration/git.py`
- Create: `tools/test_orchestration/workspace.py`
- Create: `tests/test_test_orchestration_workspace.py`
- Modify: `tools/test_orchestration/model.py`

**Interfaces:**

- Consumes: the primary repository path, resolved hardened Git identity, a validated temporary run root `R`, and Task 1 typed integrity/runtime errors.
- Produces: `GitCommandResult` and a stdlib-only `HardenedGit` port bound to Task 1 `GitToolIdentity`; frozen `PrimaryCapture`; `capture_primary_state(repository_root: Path, *, run_root: Path, git: HardenedGit, fixture_specs: tuple[FixtureSpec, ...]) -> PrimaryCapture`; `materialize_current_snapshot(capture: PrimaryCapture, *, run_root: Path, git: HardenedGit) -> Path`; `verify_primary_unchanged(capture: PrimaryCapture, *, git: HardenedGit) -> None`; and `cleanup_verified_run_root(run_root: Path, *, budgets: StageBudgets) -> None`.

`CapturedPath` has exact fields `relative_path`, `path_kind`, `working_mode`, `index_entries`, `spooled_bytes_path`, `byte_length`, `raw_sha256`, `platform_identity`, and `link_target`; nonapplicable fields are `None`. `CapturedIndexBlob` has exact fields `blob_oid`, `spooled_bytes_path`, `byte_length`, and `raw_sha256`, with one row per distinct index blob OID regardless of how many paths/stages reference it. `PrimaryCapture` has exact fields `primary_root`, `primary_root_identity`, `head_commit`, `branch_name`, `raw_index_spool_path`, `raw_index_sha256`, `index_blobs`, `paths`, `file_inventory_sha256`, `spool_root`, and `capture_sha256`. `CapturedPath.index_entries` preserves every exact `(mode, blob_oid, stage)` tuple; every referenced OID resolves to exactly one `CapturedIndexBlob`; and `capture_sha256` covers every normalized field plus the raw-index, captured-index-blob, and working-byte spool identities.

`GitCommandResult` has exact fields `return_code`, `stdout`, `stderr_byte_length`, and `stderr_sha256`; raw stderr is never persisted. `HardenedGit` exposes immutable Task 1 `GitToolIdentity` as `identity` and `run(args: tuple[str, ...], *, cwd: Path, input_bytes: bytes | None, timeout_ns: int, maximum_stdout_bytes: int) -> GitCommandResult`, always applying the minimal no-config/no-replacement environment and argument-vector rules from this plan.

- [ ] Write synthetic Git-repository tests covering dirty tracked bytes, staged-only bytes, mixed index/worktree bytes, every index stage/mode, tracked deletion, nonignored untracked file, ignored file exclusion, file-type drift, concurrent mutation, primary link/alternate rejection, and verified cleanup exhaustion.

- [ ] Implement `capture_primary_state` to capture HEAD, branch, complete NUL-delimited index entries/stages/modes, tracked working bytes/deletions, and every nonignored untracked path with exact file type. During that one capture, read every distinct staged blob through bounded hardened `git cat-file blob <oid>`, spool it once below `R`, and record its OID/length/raw digest in `CapturedIndexBlob`; do not depend on a later clone's object store. Separately spool each regular working-file byte snapshot once, record normalized path/type/length/raw SHA-256/platform identity, and record safe internal symlink targets as data. Reject junctions/reparse escapes, special devices, unsupported non-regular types, a blob whose raw bytes do not hash to its OID, or any index OID missing its spool row. Then recapture HEAD/index/path identities and reject any drift.

The selected plan supplies every ignored fixture as a validated `FixtureSpec`; direct profiles pass their exact tuple, while `full` computes the sorted deduplicated union across every constituent plan before its one H capture and rejects conflicting declarations for the same path. An ignored path absent from that tuple is excluded; a declared fixture with the wrong type/length/digest rejects capture. No capture function reads profile configuration or ambient fixture state on its own.

- [ ] Implement `materialize_current_snapshot`: create `H` through `git clone --local --no-hardlinks --no-checkout`; remove origin; reject object alternates; feed every immutable `CapturedIndexBlob` spool through `git -C H hash-object -w --stdin`, require the returned OID to equal its captured OID, reconstruct every captured index entry/stage/mode from the raw captured records through `git -C H update-index -z --index-info`, overlay captured working bytes/deletions; and verify HEAD, full index, file inventory, every staged OID, and no connection to primary. No materialization read may return to primary or trust an unverified clone object for captured index state.

- [ ] Validate that every symlink/reparse target inside H stays within H and never resolves to primary. Reject a hard-linked regular file by comparing platform file identities/link counts where supported.

- [ ] Implement `verify_primary_unchanged(capture)`: if live state changed after capture, classify concurrent workspace mutation, discard payload results, leave the user's state untouched, and run post-evidence checks. Never restore or overwrite primary files. Ignored fixtures are excluded unless a payload declares an exact path/type/length/digest; add tests for a declared ignored fixture and an undeclared one.

- [ ] Implement bounded cleanup with target validation on every retry and Windows locked-file backoff. Cleanup exhaustion is runtime category `5` unless retained evidence changed, which takes integrity category `3`.

- [ ] Run workspace tests from a bootstrap snapshot, including a temp source repository with staged conflict entries. No fixture points at the real primary checkout except read-only capture integration.

- [ ] Review checkpoint: run `git diff --check`. With explicit commit authorization only, create `feat(testing): materialize exact current snapshots`.

---

### Task 9: Implement Core, Current, Full, and GPU Execution with Evidence Guards

**Files:**

- Create: `tools/test_orchestration/evidence_guard.py`
- Create: `tools/test_orchestration/engine.py`
- Create: `tools/compare_run_summaries.py`
- Create: `tests/test_test_orchestration_engine.py`
- Modify: `tools/run_tests.py`
- Modify: `tools/test_orchestration/model.py`
- Modify: `tools/test_orchestration/protocol.py`
- Modify: `tests/test-profiles.toml`

**Interfaces:**

- Consumes: Task 1 selected `ProfilePlan`/`ConfigurationBundle`, Tasks 3-7 protocol/process/environment/child/guard contracts, Task 8 `PrimaryCapture`/H materialization, and all four evidence TOML manifests through one tool-local secure preparation pass.
- Produces: `prepare_execution_bundle(configuration: ConfigurationBundle, *, primary_root: Path) -> ExecutionBundle`; `project_worker_plan(bundle: ExecutionBundle, plan: ProfilePlan, *, interpreter_binding: InterpreterBinding) -> ResolvedWorkerPlan`; strict `EvidenceBoundaryCapture`; `capture_evidence_boundary(plan: EvidenceGuardPlan, *, primary_root: Path) -> EvidenceBoundaryCapture`; `verify_evidence_boundary(capture: EvidenceBoundaryCapture) -> None`; `run_profile(bundle: ExecutionBundle, plan: ProfilePlan, *, git: HardenedGit, primary_capture: PrimaryCapture | None = None) -> RunSummary`; `run_resolved_worker(request: ProfileWorkerRequestV1, *, process_adapter: ProcessAdapter) -> ProfileWorkerResultV1`; `run_full(bundle: ExecutionBundle, plan: ProfilePlan, *, git: HardenedGit) -> RunSummary`; and `compare_current_summaries(first: RunSummary, second: RunSummary) -> None` exposed by `tools/compare_run_summaries.py --first <absolute-path> --second <absolute-path> --full <absolute-path> --gpu <absolute-path> --gpu-exit <0|7>`. The composition root binds one Git executable identity and passes the same port through capture, materialization, post-verification, and historical setup. It calls `prepare_execution_bundle` exactly once after configuration validation and before any child/worker spawn. The engine and workers resolve every payload, interpreter, manifest, capability, historical case, blob, and overlay only from the supplied immutable execution/worker bundle—never from ambient globals or a second configuration parse.

`GuardedEvidenceIdentity` has exact fields `relative_path`, `byte_length`, `raw_sha256`, `role`, and `platform_identity`. `EvidenceBoundaryCapture` has exact fields `primary_root`, `guard_plan_sha256`, `manifest_identities`, `present`, `absent_relative_paths`, and `semantic_sha256`; every collection is a sorted tuple. `prepare_execution_bundle` securely reads each of the four configured manifests exactly once, parses the exact schema independently without `pontius`, cross-validates baseline/commit/case/overlay references, measures all six present paths and eighteen absences, and constructs one canonical `EvidenceGuardPlan` plus historical rows. `capture_evidence_boundary` does no manifest parse: it reopens and verifies all four plan-bound `EvidenceManifestIdentity` rows plus every governed path against the plan, then records their fresh platform identities. The post-check reconstructs all four manifest and six `GuardedEvidenceIdentity` rows and requires exact equality while also requiring every absence to remain absent by no-follow identity.

- [ ] Write failing tests for direct standard-library parsing of all four exact evidence manifests, one-time execution-bundle preparation, complete worker-plan projection, bounded one-handle reads, symlink/reparse rejection, path replacement and handle mutation races, before/after manifest/present/absent identity, changed retained or manifest state despite green tests, current H/T equality, one fresh child per payload, ordinary-failure continuation, safety stop, cancellation, malformed result, optional GPU semantics, and exit precedence.

- [ ] Implement the evidence guard without importing the active evidence package. Give `evidence_guard.py` a tool-local stdlib filesystem adapter matching the active reader contract: validate normalized paths beneath primary; open without following links (`CreateFileW` plus `FILE_FLAG_OPEN_REPARSE_POINT` and handle tag/type checks on Windows, `os.open` with `O_NOFOLLOW` plus regular-file `fstat` on POSIX); read each file once from one handle with manifest bound 4 MiB and governed-file bound exactly declared length plus one rejection byte; hash while streaming; compare before/after handle identity, byte length, timestamps/attributes, and final no-follow path identity; fail closed on replacement, mutation, short/long reads, reparse/symlink/special files, or unsupported identity. During the sole preparation pass, strictly parse all four exact evidence schema literals/keys/types, validate paths below primary root, and build the immutable plan. Before snapshot and again in the unconditional post-check, remeasure all four manifest identities, all six present identities, and all eighteen required absences from that plan without reparsing. Absence uses no-follow `lexists`/identity so dangling links and reparse entries count as present. The post-check runs in a `finally` path after descendant exit/output drain but before lease close and filesystem cleanup even when result parsing, cancellation, or cleanup will fail. Integrity drift is exit `3` and outranks cleanup/runtime exit `5`. Include the exact guard summary in every direct, worker, and full profile summary.

- [ ] Implement `run_profile` to reserve budgets, capture H once, resolve all payload IDs before spawn, create dedicated protocol/temp dirs, spawn every payload fresh, validate atomic results, and continue independent payloads after ordinary assertion failures. A runtime/safety failure terminates the active lease, records the active payload as `runtime_safety_stop`, records every later payload as `not_run_safety_stop`, verifies evidence, and returns category `5`. User cancellation records the active payload `cancelled`, terminates the active lease/job, marks later payloads `not_run_safety_stop`, verifies evidence, and returns category `5`.

- [ ] Implement `run_full` so the root parent captures H once and launches each required subprofile as a separate contained internal worker process from H. Workers receive only an atomic worker request containing the authenticated primary-root identity plus H/interpreter/profile identities, never import each other's state, and return a strict worker result. Serialize every worker that executes the `current` profile, every historical lifecycle case, and any worker without a reviewed proof of read-only behavior and disjoint allowed roots. Parallelize only workers whose inventory-bound capability rows prove both read-only behavior and disjoint write roots. At the full coordinator level, any runtime/safety stop terminates every active lease, records each active worker as `runtime_safety_stop`, records every unstarted worker as `not_run_safety_stop`, performs all post-evidence checks, and returns category `5`. Apply the present/absence evidence guard before and after every constituent profile as well as around the full aggregate.

`ProfileWorkerRequestV1` has exact keys `schema_version`, `run_id`, `profile`, `profile_definition_sha256`, `inventory_sha256`, `spec_capabilities_sha256`, `capability_bindings_sha256`, `resolved_plan_sha256`, `primary_root`, `harness`, `interpreter_binding`, `git_tool`, `resolved_plan`, `evidence_guard_plan`, `evidence_guard_sha256`, `budgets`, `protocol_root`, and `containment_mode`. `containment_mode` is exactly `inherited_worker_tree`. `primary_root` has exact keys `resolved_path`, `platform_identity`, and `capture_sha256`; the parent derives it from the accepted primary capture, and the worker validates all three fields before installing the unconditional primary-root write guard or importing payload code. `git_tool` is the composition-root-bound `GitToolIdentity`, never a PATH lookup; the worker remeasures its executable before every allowed Git operation. `resolved_plan` is the complete exact `ResolvedWorkerPlan`, and `evidence_guard_plan` is the complete exact `EvidenceGuardPlan`; their recomputed semantic digests must equal `resolved_plan_sha256` and `evidence_guard_sha256`. `ProfileWorkerResultV1` has exact keys `schema_version`, `run_id`, `profile`, `profile_definition_sha256`, `inventory_sha256`, `spec_capabilities_sha256`, `capability_bindings_sha256`, `resolved_plan_sha256`, `evidence_guard_sha256`, `interpreter_binding`, `summary`, `conditions`, `evidence_guard`, `duration_ns`, and `completed`. Reuse duplicate-rejecting parsing and atomic completion; a malformed/mismatched worker result is runtime category `5`.

Use schema versions `pontius-profile-worker-request-v1` and `pontius-profile-worker-result-v1` plus a canonical lowercase UUID run ID. `profile` is the nonempty profile name; every named digest is lowercase 64-hex. Nested wire objects are canonical serializations of these exact contracts:

```text
primary_root: PrimaryRootIdentity
harness:
  root, head_commit, root_tree_oid, file_inventory_sha256,
  run_tests_sha256, test_child_sha256
interpreter_binding: InterpreterBinding
git_tool: GitToolIdentity
resolved_plan: ResolvedWorkerPlan
evidence_guard_plan: EvidenceGuardPlan
budgets: StageBudgets
protocol_root: absolute normalized string below the worker run root
containment_mode: "inherited_worker_tree"
summary: ProfileSummary, including exact PayloadSummary/WorkerSummary statuses
conditions: sorted ObservedCondition array
evidence_guard:
  before_semantic_sha256, after_semantic_sha256,
  status="unchanged"|"changed", conditions=sorted ObservedCondition array
```

All dataclass field/type/ordering rules from Task 1 apply to the wire form; path/digest/budget validations are repeated after decoding. The worker verifies that its profile, interpreter binding, design/historical capability digests, payload/case closure, evidence guard, and Git identity are exactly those supplied; it neither reparses repository configuration nor resolves an executable from ambient state. Add `write_profile_worker_request_atomic(path: Path, request: ProfileWorkerRequestV1) -> None`, `read_profile_worker_request(path: Path, *, maximum_bytes: int = 16 * 1024 * 1024) -> ProfileWorkerRequestV1`, `write_profile_worker_result_atomic(path: Path, result: ProfileWorkerResultV1) -> None`, and `read_profile_worker_result(path: Path, request: ProfileWorkerRequestV1, *, maximum_bytes: int = 16 * 1024 * 1024) -> ProfileWorkerResultV1`. They reuse Task 3's duplicate-rejecting/regular-nonreparse/absent-before-spawn/atomic-file rules. A result repeats the request run/profile/input digests and interpreter binding exactly; its top-level `evidence_guard` must equal `summary.evidence_guard`; `duration_ns` rejects booleans/negatives, and `completed` must agree with its nested summary/status records.

`run_resolved_worker` is the only fresh-worker execution seam. It verifies the request and its measured executable/Git identities, reconstructs a `HardenedGit` only from `request.git_tool` plus the fixed minimal environment, and executes `request.resolved_plan` under `request.interpreter_binding` and inherited containment. Current targets use the authenticated shared `H` read-only as `T`; historical targets materialize only below the worker's unique coordinator-created protocol/run subdirectory. The worker never captures, mutates, or recursively cleans H or the coordinator run root. It may create/remove only exact child-protocol and historical-target descendants assigned in its request; the full coordinator retains the worker lease and owns final verified cleanup after post-evidence checks.

- [ ] Implement a contained GPU capability probe over atomic files, never stdout. `GpuProbeRequestV1` uses schema `pontius-gpu-probe-request-v1` and exact keys `schema_version`, `run_id`, `harness`, `interpreter`, `primary_root`, `guard_policy`, and `protocol_root`; the nested objects reuse the worker/child contracts and permit only CuPy import plus device-count query, never allocation. `GpuProbeResultV1` uses schema `pontius-gpu-probe-result-v1` and exact keys `schema_version`, `run_id`, `status`, `reason_code`, `cupy_imported`, `device_query_attempted`, `device_count`, `allocation_attempts`, `owner_calls`, `primary_write_attempts`, `duration_ns`, and `completed`. Status is `available` or `unavailable`; unavailable reason is exactly `package_absent`, `driver_unavailable`, or `no_device`. Add atomic `write_gpu_probe_request_atomic`/`read_gpu_probe_result` functions and a self-contained internal `test_child.py` probe mode, applying the same absence, duplicate-key, size, run-ID, interpreter, containment, guard, and cleanup checks as child tests. A schema-valid unavailable result returns `7` for explicit GPU; `full` records `optional_unavailable` and may still return `0`. Crash, timeout, allocation attempt, owner/write attempt, or missing/malformed/mismatched result is runtime `5`.

- [ ] In disposable bootstrap snapshots, run the focused engine/protocol/guard tests with synthetic test-local capability tables. Prove the checked-in both-zero design preapproval state refuses `core`, `current`, `gpu`, and `full` before any H/child creation. With the synthetic table only, exercise exact 50-ID core planning, current payload continuation, full worker projection under development/CPython-3.11 bindings, GPU available/unavailable semantics, no CuPy activity in core, Windows DLL observation versus POSIX inapplicability, and zero owner/retained/primary writes. Do not write or silently approve repository design rows in this task.

- [ ] Build comparator fixtures for two independent synthetic current summaries and direct/full GPU results. Require identical profile/inventory/capability digests, complete sorted IDs, per-test outcomes, counts, interpreter bindings, evidence summaries, and aggregate result after excluding only run IDs/timings. Diagnose any implementation nondeterminism with `superpowers:systematic-debugging`; do not weaken the projection.

Implement the comparison as a strict `pontius-run-summary-v1` parser plus canonical projection. It removes only `run_id` and every `duration_ns`; it compares requested profile, profile/inventory/design/historical capability digests, interpreter-slot identities, complete sorted IDs, every nonduration outcome field, counts, exit-affecting/informational conditions, evidence-guard semantic identities, aggregate status, and forbidden counters. It also validates that direct GPU exit `0` corresponds to passed GPU summaries in both direct/full results, while exit `7` corresponds to direct exit-affecting `optional_unavailable` and full informational `optional_unavailable` with aggregate success. Any other difference is configuration/test failure, and malformed/secret-bearing input is configuration failure. The comparator writes no repository file, returns `0` on equality/consistent GPU semantics and `6` on a well-formed mismatch, and emits only a bounded success line or stable mismatch paths/digests.

- [ ] In the focused mutation fixtures, verify all four manifest identities, all six retained present identities, and eighteen absences before/after success, ordinary failure, runtime stop, and cancellation. Confirm child guard counters report zero forbidden imports, owner/science calls, retained writes, and primary-root write attempts. The fresh real core/current/GPU/full executions are deliberately deferred to Task 12 after the final complete design table is emitted and approved.

- [ ] Review checkpoint: run `git diff --check`. With explicit commit authorization only, create `feat(testing): implement isolated profile execution`.

---

### Task 10: Implement Exact Historical Clones, Vectors, and Retained Probe

**Files:**

- Create: `tests/test_test_orchestration_historical.py`
- Modify: `tools/test_orchestration/workspace.py`
- Modify: `tools/test_orchestration/engine.py`
- Modify: `tools/test_child.py`
- Modify: `tools/generate_test_inventory.py`
- Modify: `tests/test-inventory.json`
- Modify: `tests/test-profiles.toml`
- Modify: `tests/test_inventory_and_profiles.py`

**Interfaces:**

- Consumes: Task 2 preapproval historical cases/capability schema, Task 3 child protocol, Task 7 guards, Task 8 hardened Git/current workspace primitives, and the approved `HistoricalBlobsManifest` bytes parsed by the parent without `pontius` imports.
- Produces: `materialize_historical_review_clone(bundle: ExecutionBundle, case: HistoricalCase, *, run_root: Path, git: HardenedGit) -> TargetIdentity` for preapproval read-only proposal analysis; and `materialize_historical_snapshot(plan: ResolvedWorkerPlan, case: HistoricalCase, *, harness_root: Path, run_root: Path, git: HardenedGit) -> TargetIdentity` for approved execution. The review function uses only the securely prepared historical rows in `ExecutionBundle`; the execution function uses only the selected case/snapshot/blob/overlay closure already serialized in `ResolvedWorkerPlan`. Neither reparses a manifest or configuration file. This task also produces the user-approved fully expanded capability tables/digest, serialized historical case execution through `run_profile`, and the child-local `probe:v7-sealed-reader-retained` result contract.

- [ ] Write temp-repository tests for exact commit/root tree, wrong/missing/extra historical blobs, ambient `autocrlf`, governed checkout conversion, H outside T, target-only imports, forbidden overlay roots, overlay collisions, primary-root sources, reparse paths, and pre-Python failure.

- [ ] Before historical review, regenerate inventory ownership for every Task 3-10 test method now present, inspect the full added-current assignment diff, and prove inventory `--check` while preserving both capability scopes exactly as found (design remains all-zero/absent; historical remains all-zero/absent). This makes the real historical runner's configuration current without prematurely approving design permissions. Task 11 additions are incorporated by the final Task 12 regeneration.

- [ ] Implement historical clone preparation with local `--no-hardlinks --no-checkout`, no network, system/user Git config disabled, explicit checkout conversion, detached exact commit, root-tree verification, and raw `(commit,path)` blob verification against `historical-blobs.toml`. Rematerialize a governed working file from its exact blob only inside T when conversion changed it.

- [ ] Extend the inventory tool with `--emit-capability-review <absolute-temp-path>` and `--write-capabilities --approved-capability-bindings-sha256 <lowercase-64-hex>`. The emit command has an explicit review-only preapproval path that directly validates the all-zero/absent historical-review scope while independently revalidating the unchanged design scope, iterates the exact `historical_case[]` records without `select_profile`, and uses `materialize_historical_review_clone` under a validated temporary root. Combine static AST extraction with a fail-closed no-payload-spawn audit in those exact clones to emit every proposed historical stable-ID-to-capability policy row, including portable subprocess fields and exact callable kind/module/qualname/action/maximum-call/return-contract fields. Runtime measured executable paths/file identities are emitted in a separate diagnostic section excluded from the approval digest. In review-only mode, only the bound hardened Git clone/plumbing commands may spawn; target Python/test code, owner/science calls, imports from T, overlays, lifecycle writes, and writes outside the proposal output plus R/T are unconditionally denied and counted, and present/absence evidence is verified before/after. Pause for user approval of the complete canonical historical policy table/digest. Only afterward invoke the write command; it must compare the supplied token with the freshly derived fully expanded historical digest and atomically add/replace only historical-scope subprocess/call definitions, bindings, and `capability_bindings_sha256`, preserving and revalidating design rows/`spec_capabilities_sha256`; absence, malformed/stale digest, cross-scope drift, or any design change rejects before writing. Configuration validation then rejects any missing/extra/digest-mismatched row before the first historical child is created. The Task 7 category list is not a substitute for this explicit approved table, and the tool never infers or auto-accepts the approval token.

- [ ] Execute these exact cases freshly and serially:

| Case | Commit | Expected vector |
| --- | --- | --- |
| base source | `88148da07324c13b79c72ea494b14167a975c001` | 21 pass |
| v2 source | `08bb6857f47f9669b8f531c65079d4decd52a573` | 8 pass |
| v2 retained | `3de8e0c9eebf67f2cc2573041242a869468de6e9` | 5 pass with fresh outcome verification |
| v3 source | `77feb7c78990ca53e70b1302a6866fe5d781411f` | 9 pass |
| v4 source | `ba6a3418b7c991238cc1a65898fd61fa03b4a3cb` | 38 pass |
| v4 authorization rejection | `815d23c115289347e3d4028a4866eb9f87d4669a` | 38 pass plus direct `ValueError` reason match, zero owner calls |
| v5 retained | `5c0c9a401e5f2ebf59296832d954d0075c4d4624` | 18 pass |
| v6 source | `d633f3fb469a27dee688587293c6efb1d2cb2757` | 17 pass |
| v6 authorization rejection | `cbfa3598f22c7aba7d824f71356ca156f8b01b0c` | 17 setup failures, zero bodies/owner calls |
| v7 source | `56127da2970f5a8a8056a97a247ebe1fdf4b983b` | 20 pass |
| v7 live | `aaca2dda40e29be8ebd091d58e7853bce1c62fd8` | 20 pass |
| v7 retained | detached `aaca2dda40e29be8ebd091d58e7853bce1c62fd8` plus three overlays | one exact retained-reader probe |

The v4 authorization-rejection row is one aggregate `HistoricalCase` whose `payload_ids` are exactly `historical:v4-positive` and `historical:v4-authorization-negative`. The 38 positive methods run in the first fresh child; the single negative method runs alone in the second fresh child. All other initial cases have one payload. Case-level vector validation occurs only after every child independently satisfies its request/prepared/executed/outcome invariants.

- [ ] For v4 negative, set `PONTIUS_ADR0467_AUTH_READER_CHILD=1` in the harness and match the direct `ValueError` safe reason `deferred-import header domain differs`; do not accept an outer nested-unittest assertion. For v6 negative, run normal setup for all 17 IDs and require safe reason code `v6_authorization_path_present`, 17 setup failures, zero bodies, and zero owner calls; normalize the clone-root prefix out of the assertion message before comparing the declared path identity.

- [ ] Apply overlays only for v7 retained, sourcing raw blobs from retention commit `a842c4b6a73a2991a63a481f4107580b72750582`: attempt 1,825 bytes/`ada1896f0bf63111e0c1e5e707315fbca6c13f6e2b63222805cb5ef4cb9dc413`; result 7,858,857 bytes/`78b2f8351ca49785756ec336d4f967bcc83a86f9ef96506a6144726cf3b312b3`; consumed marker 349 bytes/`c3c0a34cba6a677157034d8f8109cf47edea496a33c64992293176d879a2d629`. Require destination absence before overlay; pending/aborted stay absent; do not change detached HEAD or index.

- [ ] Implement file-local probe `probe:v7-sealed-reader-retained` in `test_child.py`. It imports the historical sealed reader from T and requires terminal `laboratory_wall_rejected`, passed false, complete true, event count 590, scientific calls 569, measured calls 0, null speed/candidate/topology/arithmetic claims, production base `producer_absent`, source commit `aaca2dda40e29be8ebd091d58e7853bce1c62fd8`, and raw result digest `78b2f8351ca49785756ec336d4f967bcc83a86f9ef96506a6144726cf3b312b3`. Do not overlay the active assessor or a new test into T, and do not load the old v7 test class for this retained case.

- [ ] After every case, reverify historical governed blobs, overlays, primary evidence, zero forbidden counters, and cleanup. Run `historical` twice and compare case IDs, selector digests, expected vectors, counts, and outcomes.

- [ ] Review checkpoint: run `git diff --check`. With explicit commit authorization only, create `feat(testing): reproduce exact historical phases`.

---

### Task 11: Baseline Legacy Dependencies and Enforce New Boundaries

**Files:**

- Create: `tools/generate_dependency_baseline.py`
- Create: `tools/check_stabilization_boundaries.py`
- Create: `docs/architecture/dependency-baseline.toml`
- Create: `tests/test_stabilization_boundaries.py`
- Create: `tests/test_test_orchestration_import_boundary.py`

**Interfaces:**

- Consumes: baseline/current Python ASTs, the baseline commit, and the explicit evidence/orchestration origin sets created by both plans.
- Produces: `tools/generate_dependency_baseline.py` with `--check`/explicit `--write`; canonical `dependency-baseline.toml`; and `tools/check_stabilization_boundaries.py` returning nonzero on baseline edge/SCC drift or any forbidden new boundary edge.

#### Task 11a: Early Baseline Generator and Checker Contract

- [ ] Write failing tests for the exact baseline graph, relative/absolute import resolution, `TYPE_CHECKING` imports, sorted edge/SCC encoding, a forbidden evidence edge, a forbidden parent edge, changed untouched-legacy edge, and new/expanded SCC.

- [ ] Implement a standard-library AST scanner and lock this mechanical baseline at `a842c4b6a73a2991a63a481f4107580b72750582`:

```text
modules:       470
edges:         2577
edge digest:   c178ed92158da1c544abaf39ab14842721658a31f3f9246cbeb3e05e3e3da6ee
SCCs:          469
SCC digest:    9987fddd06742fc2af87de7b8ebf79bc8b2dda7231260f7cc9efdcca18dff345
cyclic SCC:    pontius.action_clock, pontius.preparation_bank
```

The TOML records every module/path, every sorted internal edge, and every SCC membership. The existing two-node cycle remains visible and grandfathered mechanically; this milestone neither approves nor removes it.

The baseline has exact schema literal `pontius-dependency-baseline-v1` and only these keys/tables: `schema_version`, `baseline_commit`, `module_count`, `edge_count`, `edges_sha256`, `scc_count`, `sccs_sha256`, `module[]`, `edge[]`, and `scc[]`. A module row has exact string fields `module_name` and normalized repository-relative `relative_path`; an edge row has exact string fields `origin` and `target`; an SCC row has one sorted nonempty unique string array `members`. Rows sort by module name, `(origin, target)`, and member tuple respectively. Counts are exact nonnegative integers that equal row counts (booleans reject), commit/digest forms are strict lowercase hex, every edge endpoint and SCC member resolves to exactly one module, every module appears in exactly one SCC, and canonical row digests are recomputed rather than trusted.

- [ ] Make the generator default to `--check`; permit `--write` only for an explicitly named baseline file beneath `docs/architecture`. Inspect the complete generated diff before accepting it.

- [ ] Implement changed-origin policy: untouched legacy outgoing edges must match baseline; no SCC may be new/expanded; evidence origins may import only stdlib, siblings, and durable journal; orchestration origins may import only stdlib/siblings. Explicitly deny tests, experiments, compiled-calibration owner/runner/reader, CuPy/CUDA/GPU imports from stabilization code.

- [ ] During the coordinated early slice, run all Task 11 synthetic tests, generate the exact baseline with explicit `--write`, inspect it, then prove generator `--check` and checker mutation fixtures pass. Stop Task 11 here; do not claim the not-yet-created real parent/child/current integration has passed.

#### Task 11b: Post-Task-10 Real Integration

- [ ] AST-scan `tools/run_tests.py` and `tools/test_child.py` separately. Assert the parent imports neither `pontius` nor tests and the child imports no sibling helper. Assert neither file contains discovery/owner-launch code outside the declared child probe/capability dispatcher.

- [ ] In a disposable bootstrap snapshot with synthetic test-local guard policy, run the mutation fixtures and the checker directly against the real baseline/current diff. Prove the checked-in current profile still refuses before spawn while design scope is all-zero. Task 12 performs the first real current-profile execution after final design approval.

- [ ] Review checkpoint: run `git diff --check`. With explicit commit authorization only, create `test(architecture): lock legacy graph and new boundaries`.

---

### Task 12: Document, Verify, and Independently Review the Canonical Matrix

**Files:**

- Modify: `README.md`
- Modify: `RUNBOOK.md`
- Create: `tools/stabilization_verification.py`
- Create: `tests/test_stabilization_verification.py`
- Modify only for valid findings: any active source, test, tool, manifest, or documentation file added/changed by either coordinated implementation plan
- Create during review only if repository convention requires it: `docs/reviews/2026-08-27-test-stabilization-review.md`

**Interfaces:**

- Consumes: every generator/check/profile command from both plans, both required interpreter slots, absolute `PONTIUS_GIT`/`PONTIUS_RUFF` tools, and the two named independent review skills over one normalized diff scope.
- Produces: canonical README/RUNBOOK operator commands; standard-library `tools/stabilization_verification.py` with safe verification-workspace, normalized review-scope, and exact Ruff subcommands; a review record with exact findings/dispositions; and a binary architecture-review-readiness decision. No missing required tool or unresolved blocking/major finding may pass the completion gate.

- [ ] Replace raw one-process discovery in README quick start with:

```powershell
$python = (Resolve-Path ".\.venv\Scripts\python.exe").Path
& $python -B -P tools/run_tests.py core
& $python -B -P tools/run_tests.py current
& $python -B -P tools/run_tests.py full
```

Explain that raw discovery is non-authoritative because import contamination, mutually incompatible lifecycle phases, retained later artifacts, and missing contractual `-B/-P` change behavior.

- [ ] Update RUNBOOK profile/continuation sections with direct `historical` and `gpu` commands, absolute `PONTIUS_CPYTHON311`/`PONTIUS_GIT`/`PONTIUS_RUFF` configuration, optional-GPU full semantics, explicit-GPU exit `7`, stable exit codes `0/2/3/4/5/6/7`, safety-stop behavior, result locations, cleanup diagnostics, and the rule that the retained-v7 assessor is maintenance-only negative evidence—not scientific authority and never a source of a passing calibration.

- [ ] Test-drive `tools/stabilization_verification.py` in a bootstrap snapshot. `create-workspace --root <absolute-temp-child> --descriptor <absolute-temp-file>` requires both paths absent and strict children of the resolved OS temp root, an exact `pontius-verification-<32 lowercase hex>` root leaf, an exact distinct descriptor leaf, and no link/reparse ancestor; it creates the directory, captures platform directory identity, and atomically writes schema `pontius-verification-workspace-v1`. `cleanup-workspace --descriptor <path> --descriptor-sha256 <digest>` securely reads that descriptor once, requires its raw digest and the current root identity to match, uses OS-appropriate path comparison, rejects any symlink/reparse/special entry during no-follow traversal, and recursively removes only the captured root plus descriptor. Identity drift or unsafe content leaves the tree in place and fails. `emit-review-scope --baseline <commit> --git-executable <absolute> --output <absolute-temp-path>` uses Task 8 hardened Git rules to combine tracked `ACMR` changes since baseline with nonignored untracked paths, reject abnormal names/escapes and every unsupported `T/U/X/B` or unknown status, and atomically emit schema `pontius-review-scope-v1` with exact keys `schema_version`, `baseline_commit`, `paths`, `deleted_paths`, `python_paths`, `scope_sha256`, `content_sha256`; deleted paths are recorded for review but never passed to Ruff. `check-review-snapshot --baseline <commit> --git-executable <absolute> --scope-sha256 <digest> --content-sha256 <digest>` freshly rederives both digests without writing and fails on any path, byte, executable-mode, index-mode, deletion, or status drift. `run-ruff --scope <path> --scope-raw-sha256 <digest> --ruff-executable <absolute>` securely reads that scope once, verifies its supplied raw-file digest, strict schema, both freshly rederived semantic digests, every current `python_paths` entry, and Ruff identity, then invokes one argument-vector `ruff check --no-cache <all exact paths>` from repository root. Add replacement/reparse/case-sensitive-POSIX/missing-executable/untracked-file/unsupported-status/same-path-content-drift/mode-drift tests.

The verification descriptor has only these exact keys: `schema_version`, `verification_id`, `temporary_root`, `temporary_root_identity`, `root`, `root_identity`, and `descriptor_path`. `verification_id` is the root leaf's 32 lowercase hex suffix. Each directory identity is one strict object variant: Windows `{platform="windows", volume_serial_number=<exact-nonnegative-int>, file_id_hex=<lowercase-even-hex>, file_attributes=<exact-nonnegative-int>}`; POSIX `{platform="posix", device=<exact-nonnegative-int>, inode=<exact-nonnegative-int>, file_type_mode=<exact-nonnegative-int>}`. Booleans never satisfy integers. Every path is an absolute normalized native string; descriptor/root are distinct strict children of the captured temporary root. Encode sorted-key compact UTF-8 JSON plus one LF, maximum 16 KiB, reject duplicate/missing/extra keys, and write the descriptor through absent-final sibling-temp/fsync/replace rules. Cleanup requires field-for-field current temporary-root/root identity equality before and during no-follow deletion and final descriptor removal.

The review-scope arrays are sorted unique normalized POSIX repository-relative paths. `paths` is exactly current tracked `A/C/M/R` destinations plus nonignored untracked files; `deleted_paths` is exactly tracked deletions (and rename sources when distinct); the two are disjoint. `python_paths` is exactly the current `.py` subset of `paths`. Any tracked status outside `A/C/M/R/D`—including `T`, `U`, `X`, `B`, an unmerged stage, or an unknown status—is a hard scope-generation failure; it is never omitted or downgraded to an untracked path. Reject absolute/drive-qualified/backslash/dot-segment/control-character/escape paths and any path whose current file identity is nonregular or reparse-linked. `scope_sha256` is SHA-256 of sorted-key compact ASCII JSON, with no trailing LF, over exactly `{baseline_commit, paths, deleted_paths, python_paths}` after validation. `content_sha256` is SHA-256 of the same encoding over exactly `{baseline_commit, files, deleted_paths}`, where `files` is sorted by path and contains one exact object for every `paths` entry: `{path, byte_length, raw_sha256, executable, index_mode}`. `byte_length` is an exact nonnegative integer, `raw_sha256` is lowercase SHA-256 of bytes read once through the secure regular-file adapter, `executable` is an exact boolean captured from the current platform mode, and `index_mode` is either exact string `untracked` or the validated current regular-file Git index mode; links, special modes, duplicate stages, and mode/identity drift fail closed. The persisted document is sorted-key compact UTF-8 JSON plus one LF and maximum 4 MiB; its separately supplied raw-file digest protects the cross-command handoff. Both semantic digests must be freshly recomputed immediately before and after each independent review.

- [ ] Regenerate the final inventory after `tests/test_stabilization_verification.py` and every Task 3-11 test exist, inspect the complete ID/ownership diff, and run inventory `--check`. Then emit `--emit-design-capability-review <absolute-temp-path>` over that final inventory. Present the complete nonempty core/current/GPU stable/fixture/probe binding table, the explicit deny-all item list, inventory digest, canonical capability digest, and host-excluded diagnostics to the user; pause for approval. Only after the user approves that exact digest, invoke `--write-design-capabilities --approved-spec-capabilities-sha256 <the-exact-user-approved-digest>`. The command freshly rederives the complete table, changes only design-scope definitions/bindings/digest, preserves/revalidates Task 10's approved historical scope, and rejects any stale/missing token or intervening source/inventory drift before writing. Inspect the full diff and rerun `--check`. No real core/current/GPU/full command below may run while the design digest is all-zero.

- [ ] Run deterministic checks:

```powershell
$ErrorActionPreference = "Stop"
function Invoke-CheckedNative {
    param(
        [Parameter(Mandatory = $true)][string]$Executable,
        [Parameter(Mandatory = $true)][string[]]$Arguments,
        [Parameter(Mandatory = $true)][string]$Label
    )
    & $Executable @Arguments
    $invoked = $?
    $exitCode = $LASTEXITCODE
    if (-not $invoked -or $exitCode -ne 0) { throw "$Label failed: $exitCode" }
}

$isWindows = [System.Environment]::OSVersion.Platform -eq [System.PlatformID]::Win32NT
$pythonRelative = if ($isWindows) { ".\.venv\Scripts\python.exe" } else { "./.venv/bin/python" }
$pythonItem = Get-Item -LiteralPath (Resolve-Path -LiteralPath $pythonRelative -ErrorAction Stop).Path -ErrorAction Stop
$gitConfigured = [Environment]::GetEnvironmentVariable("PONTIUS_GIT")
$ruffConfigured = [Environment]::GetEnvironmentVariable("PONTIUS_RUFF")
if ([string]::IsNullOrWhiteSpace($gitConfigured) -or -not [IO.Path]::IsPathFullyQualified($gitConfigured)) { throw "PONTIUS_GIT must name an absolute executable" }
if ([string]::IsNullOrWhiteSpace($ruffConfigured) -or -not [IO.Path]::IsPathFullyQualified($ruffConfigured)) { throw "PONTIUS_RUFF must name an absolute executable" }
$gitItem = Get-Item -LiteralPath $gitConfigured -ErrorAction Stop
$ruffItem = Get-Item -LiteralPath $ruffConfigured -ErrorAction Stop
foreach ($toolItem in @($pythonItem, $gitItem, $ruffItem)) {
    if ($toolItem.PSIsContainer -or (($toolItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0)) { throw "required executable type is invalid: $($toolItem.FullName)" }
}
$python = $pythonItem.FullName
$temporaryRoot = [IO.Path]::GetFullPath([IO.Path]::GetTempPath())
$verificationId = [guid]::NewGuid().ToString("N")
$verificationRoot = Join-Path $temporaryRoot ("pontius-verification-" + $verificationId)
$verificationDescriptor = Join-Path $temporaryRoot ("pontius-verification-descriptor-" + $verificationId + ".json")
$workspaceCreated = $false
$descriptorSha256 = $null
$coreSummary = Join-Path $verificationRoot "core.json"
$currentSummary1 = Join-Path $verificationRoot "current-1.json"
$currentSummary2 = Join-Path $verificationRoot "current-2.json"
$historicalSummary = Join-Path $verificationRoot "historical.json"
$gpuSummary = Join-Path $verificationRoot "gpu.json"
$fullSummary = Join-Path $verificationRoot "full.json"
$reviewScope = Join-Path $verificationRoot "review-scope.json"
$verificationSummaryDigests = $null
$reviewScopeIdentity = $null
$reviewScopeDocument = $null
try {
    Invoke-CheckedNative -Executable $python -Arguments @("-B", "-P", "tools/stabilization_verification.py", "create-workspace", "--root", $verificationRoot, "--descriptor", $verificationDescriptor) -Label "verification workspace creation"
    $workspaceCreated = $true
    $descriptorSha256 = (Get-FileHash -LiteralPath $verificationDescriptor -Algorithm SHA256 -ErrorAction Stop).Hash.ToLowerInvariant()
    Invoke-CheckedNative -Executable $python -Arguments @("-B", "-P", "tools/generate_evidence_manifests.py", "--check") -Label "evidence manifest check"
    Invoke-CheckedNative -Executable $python -Arguments @("-B", "-P", "tools/generate_test_inventory.py", "--check") -Label "test inventory check"
    Invoke-CheckedNative -Executable $python -Arguments @("-B", "-P", "tools/generate_dependency_baseline.py", "--check") -Label "dependency baseline check"
    Invoke-CheckedNative -Executable $python -Arguments @("-B", "-P", "tools/check_stabilization_boundaries.py") -Label "stabilization boundary check"
    Invoke-CheckedNative -Executable $python -Arguments @("-B", "-P", "tools/stabilization_verification.py", "emit-review-scope", "--baseline", "a842c4b6a73a2991a63a481f4107580b72750582", "--git-executable", $gitItem.FullName, "--output", $reviewScope) -Label "review scope generation"
    $reviewScopeIdentity = (Get-FileHash -LiteralPath $reviewScope -Algorithm SHA256 -ErrorAction Stop).Hash.ToLowerInvariant()
    $reviewScopeDocument = Get-Content -LiteralPath $reviewScope -Raw -ErrorAction Stop
    Invoke-CheckedNative -Executable $python -Arguments @("-B", "-P", "tools/stabilization_verification.py", "run-ruff", "--scope", $reviewScope, "--scope-raw-sha256", $reviewScopeIdentity, "--ruff-executable", $ruffItem.FullName) -Label "Ruff changed-Python gate"
    Invoke-CheckedNative -Executable $python -Arguments @("-B", "-P", "tools/run_tests.py", "core", "--json-summary", $coreSummary) -Label "core profile"
    Invoke-CheckedNative -Executable $python -Arguments @("-B", "-P", "tools/run_tests.py", "current", "--json-summary", $currentSummary1) -Label "first current profile"
    Invoke-CheckedNative -Executable $python -Arguments @("-B", "-P", "tools/run_tests.py", "current", "--json-summary", $currentSummary2) -Label "second current profile"
    Invoke-CheckedNative -Executable $python -Arguments @("-B", "-P", "tools/run_tests.py", "historical", "--json-summary", $historicalSummary) -Label "historical profile"
    & $python -B -P tools/run_tests.py gpu --json-summary $gpuSummary
    $gpuInvoked = $?
    $gpuExit = $LASTEXITCODE
    if (-not $gpuInvoked -or ($gpuExit -ne 0 -and $gpuExit -ne 7)) { throw "gpu profile failed unexpectedly: $gpuExit" }
    Invoke-CheckedNative -Executable $python -Arguments @("-B", "-P", "tools/run_tests.py", "full", "--json-summary", $fullSummary) -Label "full profile"
    Invoke-CheckedNative -Executable $python -Arguments @("-B", "-P", "tools/compare_run_summaries.py", "--first", $currentSummary1, "--second", $currentSummary2, "--full", $fullSummary, "--gpu", $gpuSummary, "--gpu-exit", [string]$gpuExit) -Label "summary comparison"
    $verificationSummaryDigests = Get-Item -LiteralPath $coreSummary,$currentSummary1,$currentSummary2,$historicalSummary,$gpuSummary,$fullSummary | Get-FileHash -Algorithm SHA256 | Select-Object Path,Hash
}
finally {
    if ($workspaceCreated) {
        Invoke-CheckedNative -Executable $python -Arguments @("-B", "-P", "tools/stabilization_verification.py", "cleanup-workspace", "--descriptor", $verificationDescriptor, "--descriptor-sha256", $descriptorSha256) -Label "verification workspace cleanup"
    }
}
```

The direct GPU command must atomically write its summary for both exit `0` and schema-valid unavailable exit `7`. Add `$verificationSummaryDigests`, `$reviewScopeIdentity`, and `$reviewScopeDocument` (which contains the canonical path-scope and content-snapshot digests) to the review record after the block; comparison/hash capture occurs before identity-bound cleanup. A cleanup refusal is a visible release-blocking runtime failure and never falls back to `Remove-Item` or another recursive command.

- [ ] Inspect the successful comparator result and recorded summary digests. Confirm it compared identical profile/inventory/design/historical capability digests, sorted IDs, per-test outcomes, counts, aggregate result, zero forbidden counters, pre/post retained identities, and direct/full GPU semantics before cleanup.

- [ ] Inspect the exact `pontius-review-scope-v1` output and successful `run-ruff` result. Confirm `python_paths` equals every current changed/untracked active Python path, unsupported Git statuses were absent, the content records cover every current `paths` entry, and the Ruff invocation used the complete Python array with `--no-cache`. The deterministic block fails closed when `PONTIUS_RUFF`, `PONTIUS_GIT`, the development interpreter, or the separate CPython 3.11 profile slot is missing or changes identity.

- [ ] Immediately before and after invoking `codex-engineering-guardrails:code-verification`, run `check-review-snapshot` with the recorded baseline, `scope_sha256`, and `content_sha256`; any mismatch invalidates the review. Perform the independent read-only review of exactly the canonical `paths` plus `deleted_paths` in the recorded `pontius-review-scope-v1` document. The scope is the diff since the recorded baseline and excludes unchanged historical blobs and generated raw review outputs outside the repository. Resolve every valid blocking/major finding.

- [ ] Immediately before and after invoking `coderabbit:code-review`, run `check-review-snapshot` with the same recorded path-scope/content digests; any mismatch invalidates the review. Review the same exact recorded `paths`/`deleted_paths` scope with a 20-minute wall limit. Record tool/plugin version, reported model, UTC time, baseline, both semantic digests, and raw NDJSON outside the repository. Mark timeout/unavailability explicitly; do not represent it as a successful CodeRabbit pass.

- [ ] Give every finding one disposition: `fixed`, `rejected-with-evidence`, or `deferred-with-approved-owner-and-milestone`. Blocking/major findings cannot be deferred from this milestone.

- [ ] Enforce a review fixed point. If either independent review causes any accepted repository edit, invalidate the prior verification/scope evidence: regenerate and check manifests, inventory, dependency baseline, and boundaries; re-emit and obtain fresh user approval only for any seed/design/historical capability table whose canonical rows or digest changed; rerun the entire deterministic block including both current runs, Ruff, all profiles, evidence guards, comparator, and safe cleanup; regenerate both review digests; then repeat both reviews over that new exact scope and content snapshot. Continue until a full gate run and both review dispositions produce no subsequent edit. Completion evidence must all name the same final `scope_sha256` and `content_sha256` pair.

- [ ] Verify `git diff --check`, protected files/absences, no generated bytecode, and no residual temp clone/worktree metadata. With explicit commit authorization only, create the final stabilization commit; otherwise hand off the reviewed uncommitted diff and exact commands/results.

## Orchestration Completion Gate

Do not begin the holistic architecture/V0a review until all of these have fresh evidence:

- all 2,367 baseline stable methods and every added stabilization test method are owned exactly once, with no missing/duplicate/zero-test selector;
- core passes without CuPy import or CUDA query/allocation;
- current passes twice from independent H snapshots with deterministic IDs/outcomes/counts;
- historical passes all exact commit/root-tree vectors without primary mutation;
- retained-v7 current assessment and historical sealed-reader probe agree on the negative terminal and zero authoritative measured calls;
- full exercises both development and CPython 3.11 slots and reports optional GPU status correctly;
- the complete legacy edge/SCC baseline and new exact boundary policy pass;
- retained evidence identities match before/after every profile;
- repository-owned review has no unresolved valid blocking/major issue; and
- CodeRabbit findings, when available, are fully triaged over the same exact scope.
