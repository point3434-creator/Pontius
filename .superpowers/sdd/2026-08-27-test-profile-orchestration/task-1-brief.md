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

