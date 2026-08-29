# Review package: 89303d1e7bdda4f3aec74b131d8a8cc8d1afcc09..b4a16549bbfc4a923e12a1f9b0ab74faa981ac8a

## Commits
b4a1654 feat(testing): lock orchestration contracts

## Files changed
 tests/orchestration_test_support.py            |   42 +
 tests/test_test_orchestration_configuration.py | 1043 ++++++++++++++++
 tools/__init__.py                              |    1 +
 tools/test_orchestration/__init__.py           |    1 +
 tools/test_orchestration/configuration.py      |  948 +++++++++++++++
 tools/test_orchestration/errors.py             |   72 ++
 tools/test_orchestration/model.py              | 1536 ++++++++++++++++++++++++
 7 files changed, 3643 insertions(+)

## Diff
diff --git a/tests/orchestration_test_support.py b/tests/orchestration_test_support.py
new file mode 100644
index 0000000..6b96ae5
--- /dev/null
+++ b/tests/orchestration_test_support.py
@@ -0,0 +1,42 @@
+"""Exact-path support for orchestration tests executed with ``-P``."""
+
+from __future__ import annotations
+
+import importlib.machinery
+import importlib.util
+from pathlib import Path
+import sys
+from types import ModuleType
+
+
+PACKAGE_NAME = "pontius_test_orchestration"
+
+
+def load_orchestration_modules(snapshot_root: Path) -> tuple[ModuleType, ModuleType, ModuleType]:
+    """Load the tool package without adding a repository path to ``sys.path``."""
+    package_root = snapshot_root / "tools" / "test_orchestration"
+    for name in tuple(sys.modules):
+        if name == PACKAGE_NAME or name.startswith(f"{PACKAGE_NAME}."):
+            del sys.modules[name]
+
+    package = ModuleType(PACKAGE_NAME)
+    package.__file__ = str(package_root / "__init__.py")
+    package.__package__ = PACKAGE_NAME
+    package.__path__ = [str(package_root)]
+    package_spec = importlib.machinery.ModuleSpec(PACKAGE_NAME, loader=None, is_package=True)
+    package_spec.submodule_search_locations = [str(package_root)]
+    package.__spec__ = package_spec
+    sys.modules[PACKAGE_NAME] = package
+
+    loaded: list[ModuleType] = []
+    for short_name in ("errors", "model", "configuration"):
+        full_name = f"{PACKAGE_NAME}.{short_name}"
+        path = package_root / f"{short_name}.py"
+        specification = importlib.util.spec_from_file_location(full_name, path)
+        if specification is None or specification.loader is None:
+            raise RuntimeError(f"cannot load orchestration module: {path}")
+        module = importlib.util.module_from_spec(specification)
+        sys.modules[full_name] = module
+        specification.loader.exec_module(module)
+        loaded.append(module)
+    return loaded[0], loaded[1], loaded[2]
diff --git a/tests/test_test_orchestration_configuration.py b/tests/test_test_orchestration_configuration.py
new file mode 100644
index 0000000..51ba0bc
--- /dev/null
+++ b/tests/test_test_orchestration_configuration.py
@@ -0,0 +1,1043 @@
+from __future__ import annotations
+
+from dataclasses import FrozenInstanceError, fields, is_dataclass
+from hashlib import sha256
+import importlib.util
+import json
+from pathlib import Path
+import sys
+import tempfile
+from types import MappingProxyType
+import unittest
+
+
+COMMIT = "b" * 40
+SHA256 = "a" * 64
+ZERO_SHA256 = "0" * 64
+SNAPSHOT_ROOT = Path(__file__).resolve().parents[1]
+
+_SUPPORT_PATH = Path(__file__).with_name("orchestration_test_support.py")
+_SUPPORT_SPEC = importlib.util.spec_from_file_location(
+    "orchestration_test_support", _SUPPORT_PATH
+)
+if _SUPPORT_SPEC is None or _SUPPORT_SPEC.loader is None:
+    raise RuntimeError("orchestration test support could not be loaded by exact path")
+_SUPPORT = importlib.util.module_from_spec(_SUPPORT_SPEC)
+_SUPPORT_SPEC.loader.exec_module(_SUPPORT)
+_PATH_BEFORE_BOOTSTRAP = tuple(sys.path)
+ERRORS, MODEL, CONFIGURATION = _SUPPORT.load_orchestration_modules(SNAPSHOT_ROOT)
+
+
+MODEL_FIELDS = {
+    "InterpreterIdentity": (
+        "executable", "resolved_executable", "platform_identity", "executable_sha256",
+        "implementation", "version", "prefix", "base_prefix", "no_user_site",
+        "safe_path", "dont_write_bytecode", "distributions_sha256",
+        "dependency_lock_sha256",
+    ),
+    "InterpreterBinding": ("slot_name", "identity"),
+    "TargetIdentity": ("kind", "root", "head_commit", "root_tree_oid", "file_inventory_sha256"),
+    "PrimaryRootIdentity": ("resolved_path", "platform_identity", "capture_sha256"),
+    "GitToolIdentity": ("executable", "resolved_executable", "platform_identity", "executable_sha256"),
+    "InterpreterSlot": (
+        "name", "resolution", "windows_relative_path", "posix_relative_path",
+        "environment_variable", "implementation", "minimum_version", "exact_version",
+        "required_for_full",
+    ),
+    "ProfilePlan": (
+        "name", "interpreter_slots", "default_interpreter_slot", "payload_ids",
+        "historical_case_ids", "subprofiles", "budgets", "fixture_specs", "gpu_optional",
+        "definition_sha256",
+    ),
+    "FixtureSpec": ("relative_path", "path_kind", "byte_length", "raw_sha256"),
+    "InventoryExpectation": ("kind", "applicable_platforms", "skip_safe_reason_code"),
+    "ResolvedInventoryItem": ("selector", "expectation"),
+    "InventoryEntry": (
+        "selector", "profile_name", "payload_id", "expectation", "exclusion_reason",
+        "exclusion_owner", "exclusion_milestone",
+    ),
+    "PayloadPlan": (
+        "payload_id", "profile_name", "target_kind", "allowed_interpreter_slots",
+        "inventory_items", "probe_ids", "lifecycle_fixtures", "environment_additions",
+        "environment_removals", "allowed_write_roots", "forbidden_relative_paths",
+        "fixture_specs", "serialized",
+    ),
+    "LifecycleFixturePlan": (
+        "fixture_id", "kind", "relative_path", "class_name", "member_ids",
+        "allowed_write_roots", "forbidden_relative_paths", "serialized",
+    ),
+    "HistoricalItemExpectation": (
+        "item_id", "outcome", "phase", "exception_type", "safe_reason_code",
+        "body_entered", "capability_counters",
+    ),
+    "HistoricalSnapshotExpectation": ("phase", "commit", "root_tree_oid", "governing_decision"),
+    "HistoricalBlobExpectation": (
+        "commit", "relative_path", "git_blob_oid", "raw_sha256", "role", "phase",
+        "governing_decision",
+    ),
+    "HistoricalCase": (
+        "case_id", "phase", "commit", "root_tree_oid", "payload_ids", "expected_vector",
+        "item_expectations", "overlay_ids",
+    ),
+    "OverlaySpec": (
+        "overlay_id", "source_commit", "source_path", "destination_path", "byte_length",
+        "raw_sha256",
+    ),
+    "SubprocessCapability": (
+        "capability_id", "executable_role", "executable_slot", "executable_constraints",
+        "argv", "argv_template", "dynamic_program_sha256", "cwd_class",
+        "environment_additions", "environment_removals", "timeout_ns",
+        "expected_return_category", "read_roots", "write_roots",
+        "fixed_descendant_permission",
+    ),
+    "CallCapability": (
+        "capability_id", "kind", "module_name", "qualified_name", "action",
+        "maximum_calls", "return_contract",
+    ),
+    "CapabilityBinding": ("item_id", "approval_scope", "capability_kind", "capability_id"),
+    "EvidenceManifestIdentity": (
+        "relative_path", "schema_version", "byte_length", "raw_sha256", "semantic_sha256",
+        "platform_identity",
+    ),
+    "EvidenceFileExpectation": ("relative_path", "byte_length", "raw_sha256", "role", "platform_identity"),
+    "EvidenceAbsenceExpectation": ("relative_path", "role"),
+    "EvidenceGuardPlan": ("semantic_sha256", "manifest_identities", "present_files", "absences"),
+    "EvidenceGuardSummary": ("before_semantic_sha256", "after_semantic_sha256", "status", "conditions"),
+    "ResolvedWorkerPlan": (
+        "semantic_sha256", "profile", "inventory_entries", "payloads", "historical_cases",
+        "historical_snapshots", "historical_blobs", "overlays", "subprocess_capabilities",
+        "call_capabilities", "capability_bindings", "spec_capabilities_sha256",
+        "capability_bindings_sha256",
+    ),
+    "ExecutionBundle": (
+        "configuration", "evidence_guard_plan", "historical_snapshots", "historical_blobs",
+        "semantic_sha256",
+    ),
+    "ObservedCondition": ("category", "code", "affects_exit", "context"),
+    "CapturedStreamIdentity": ("byte_length", "raw_sha256", "truncated"),
+    "CapturedOutputIdentity": ("stdout", "stderr"),
+    "ChildExecutionResult": ("report", "process_return_category", "captured_output", "completed"),
+    "PayloadSummary": (
+        "payload_id", "status", "requested_ids", "outcomes", "counts", "conditions",
+        "captured_output", "duration_ns", "completed",
+    ),
+    "WorkerSummary": (
+        "profile", "interpreter_binding", "status", "summary", "conditions", "duration_ns",
+        "completed",
+    ),
+    "ProfileSummary": (
+        "profile", "profile_definition_sha256", "inventory_sha256", "spec_capabilities_sha256",
+        "capability_bindings_sha256", "interpreter_bindings", "payload_summaries",
+        "worker_summaries", "requested_ids", "outcomes", "counts", "conditions",
+        "evidence_guard_sha256", "evidence_guard", "duration_ns", "completed",
+    ),
+    "RunSummary": (
+        "run_id", "requested_profile", "profile_summaries", "conditions", "exit_code",
+        "duration_ns", "completed",
+    ),
+    "ConfigurationBundle": (
+        "repository_root", "profiles_path", "inventory_path", "baseline_commit",
+        "sealed_current_files_manifest", "sealed_current_absences_manifest",
+        "historical_blobs_manifest", "retained_v7_manifest", "profile_definition_sha256",
+        "inventory_sha256", "spec_capabilities_sha256", "capability_bindings_sha256",
+        "inventory_entries", "interpreter_slots", "profiles", "payloads", "historical_cases",
+        "overlays", "subprocess_capabilities", "call_capabilities", "capability_bindings",
+        "stabilization_test_files",
+    ),
+}
+
+
+def _profiles_toml(*, reverse_root: bool = False) -> str:
+    roots = [
+        ("schema_version", '"pontius-test-profiles-v1"'),
+        ("baseline_commit", f'"{COMMIT}"'),
+        ("sealed_current_files_manifest", '"docs/architecture/sealed-current-files.toml"'),
+        ("sealed_current_absences_manifest", '"docs/architecture/sealed-current-absences.toml"'),
+        ("historical_blobs_manifest", '"docs/architecture/historical-blobs.toml"'),
+        ("retained_v7_manifest", '"docs/architecture/retained-v7.toml"'),
+        ("inventory_path", '"tests/test-inventory.json"'),
+        ("spec_capabilities_sha256", f'"{ZERO_SHA256}"'),
+        ("capability_bindings_sha256", f'"{ZERO_SHA256}"'),
+        ("stabilization_test_files", '["tests/test_test_orchestration_configuration.py"]'),
+    ]
+    if reverse_root:
+        roots.reverse()
+    root_text = "\n".join(f"{key} = {value}" for key, value in roots)
+    return root_text + f"""
+
+[[interpreter_slot]]
+name = "development"
+resolution = "repository_relative"
+windows_relative_path = ".venv/Scripts/python.exe"
+posix_relative_path = ".venv/bin/python"
+implementation = "cpython"
+minimum_version = [3, 11]
+required_for_full = true
+
+[[profile]]
+name = "core"
+interpreter_slots = ["development"]
+default_interpreter_slot = "development"
+payload_ids = ["core:sample"]
+historical_case_ids = []
+subprofiles = []
+gpu_optional = false
+
+[profile.budgets]
+setup_seconds = 2
+child_seconds = 3
+termination_seconds = 5
+cleanup_seconds = 7
+total_seconds = 17
+
+[[payload]]
+payload_id = "core:sample"
+profile_name = "core"
+target_kind = "current_snapshot"
+allowed_interpreter_slots = ["development"]
+probe_ids = []
+environment_additions = {{ SAFE = "1" }}
+environment_removals = ["PYTHONSTARTUP"]
+allowed_write_roots = ["temporary"]
+forbidden_relative_paths = ["artifacts/retained.json"]
+serialized = false
+"""
+
+
+def _inventory(*, profile_name: str = "core", payload_id: str = "core:sample") -> dict[str, object]:
+    stable_id = "tests/test_sample.py::SampleTests::test_value"
+    return {
+        "schema_version": "pontius-test-inventory-v1",
+        "baseline_commit": COMMIT,
+        "entries": [
+            {
+                "stable_id": stable_id,
+                "relative_path": "tests/test_sample.py",
+                "case_name": "SampleTests",
+                "method_name": "test_value",
+                "assignment": {
+                    "profile_name": profile_name,
+                    "payload_id": payload_id,
+                    "expectation": {"kind": "pass"},
+                },
+            }
+        ],
+    }
+
+
+class _ConfigurationTree:
+    def __init__(self, profiles: str | None = None, inventory: dict[str, object] | None = None) -> None:
+        self._temporary = tempfile.TemporaryDirectory(prefix="pontius-orchestration-config-")
+        self.root = Path(self._temporary.name) / "repository"
+        (self.root / "tests").mkdir(parents=True)
+        self.profiles = self.root / "tests" / "test-profiles.toml"
+        self.inventory = self.root / "tests" / "test-inventory.json"
+        self.profiles.write_text(profiles if profiles is not None else _profiles_toml(), encoding="utf-8", newline="\n")
+        self.inventory.write_text(
+            json.dumps(inventory if inventory is not None else _inventory(), ensure_ascii=True, separators=(",", ":"), sort_keys=True) + "\n",
+            encoding="utf-8",
+            newline="\n",
+        )
+
+    def close(self) -> None:
+        self._temporary.cleanup()
+
+    def __enter__(self) -> "_ConfigurationTree":
+        return self
+
+    def __exit__(self, *_: object) -> None:
+        self.close()
+
+
+class OrchestrationBootstrapTests(unittest.TestCase):
+    def test_exact_path_bootstrap_does_not_mutate_sys_path(self) -> None:
+        self.assertEqual(tuple(sys.path), _PATH_BEFORE_BOOTSTRAP)
+        package = sys.modules["pontius_test_orchestration"]
+        self.assertEqual(package.__path__, [str(SNAPSHOT_ROOT / "tools" / "test_orchestration")])
+        forbidden = {str(SNAPSHOT_ROOT), str(SNAPSHOT_ROOT / "tests")}
+        self.assertTrue(forbidden.isdisjoint(sys.path))
+
+
+class OrchestrationErrorAndModelTests(unittest.TestCase):
+    def test_errors_have_stable_fields_and_recursively_immutable_sorted_context(self) -> None:
+        for error_type in (
+            ERRORS.EvidenceConfigurationError,
+            ERRORS.EvidenceIntegrityError,
+            ERRORS.AuthorizationPhaseError,
+            ERRORS.LifecycleStateError,
+            ERRORS.RuntimeContractError,
+        ):
+            error = error_type(
+                "stable_code",
+                "stable message",
+                context={"z": [3, {"b": 2, "a": 1}], "a": {"roles": {"gpu", "cpu"}}},
+            )
+            self.assertEqual(error.code, "stable_code")
+            self.assertEqual(error.message, "stable message")
+            self.assertEqual(tuple(error.context), ("a", "z"))
+            self.assertEqual(tuple(error.context["a"]), ("roles",))
+            self.assertEqual(error.context["z"], (3, MappingProxyType({"a": 1, "b": 2})))
+            with self.assertRaises(TypeError):
+                error.context["new"] = True
+        with self.assertRaises(TypeError):
+            ERRORS.RuntimeContractError("bad", "bad", context={"value": object()})
+        with self.assertRaises(TypeError):
+            ERRORS.RuntimeContractError("bad", "bad", context={1: "value"})
+
+    def test_exact_enums_and_every_declared_model_field_are_frozen_and_slotted(self) -> None:
+        self.assertEqual(
+            {item.name: item.value for item in MODEL.ExitCode},
+            {"SUCCESS": 0, "CONFIGURATION": 2, "INTEGRITY": 3, "PHASE": 4, "RUNTIME": 5,
+             "TEST_FAILURE": 6, "OPTIONAL_UNAVAILABLE": 7},
+        )
+        self.assertEqual(
+            {item.name: item.value for item in MODEL.TargetKind},
+            {"CURRENT_SNAPSHOT": "current_snapshot", "HISTORICAL_CLONE": "historical_clone"},
+        )
+        self.assertEqual(
+            {item.name: item.value for item in MODEL.ExecutionStatus},
+            {
+                "PASSED": "passed", "TEST_FAILURE": "test_failure",
+                "CONFIGURATION_FAILURE": "configuration_failure",
+                "INTEGRITY_FAILURE": "integrity_failure", "PHASE_FAILURE": "phase_failure",
+                "RUNTIME_SAFETY_STOP": "runtime_safety_stop", "CANCELLED": "cancelled",
+                "NOT_RUN_SAFETY_STOP": "not_run_safety_stop",
+                "OPTIONAL_UNAVAILABLE": "optional_unavailable",
+            },
+        )
+        expected = {"StageBudgets": ("setup_ns", "child_ns", "termination_grace_ns", "cleanup_ns", "total_ns"),
+                    "StableSelector": ("stable_id", "relative_path", "case_name", "method_name"), **MODEL_FIELDS}
+        for name, field_names in expected.items():
+            with self.subTest(model=name):
+                model_type = getattr(MODEL, name)
+                self.assertTrue(is_dataclass(model_type))
+                self.assertTrue(model_type.__dataclass_params__.frozen)
+                self.assertEqual(tuple(field.name for field in fields(model_type)), field_names)
+                self.assertIn("__slots__", vars(model_type))
+
+    def test_budgets_are_positive_exact_integers_and_reserve_every_stage(self) -> None:
+        valid = MODEL.StageBudgets(1, 2, 3, 4, 10)
+        self.assertEqual(valid.total_ns, 10)
+        with self.assertRaises(FrozenInstanceError):
+            valid.total_ns = 11
+        for values in ((0, 2, 3, 4, 10), (True, 2, 3, 4, 10), (1, 2, 3, 4, 9)):
+            with self.subTest(values=values), self.assertRaises(ValueError):
+                MODEL.StageBudgets(*values)
+
+    def test_stable_id_parser_accepts_only_normalized_test_methods(self) -> None:
+        selector = CONFIGURATION.parse_stable_id(
+            "tests/nested/test_sample.py::SampleTests::test_value"
+        )
+        self.assertEqual(selector.relative_path.as_posix(), "tests/nested/test_sample.py")
+        self.assertEqual(selector.case_name, "SampleTests")
+        self.assertEqual(selector.method_name, "test_value")
+        invalid = (
+            "probe:v7", "tests/test_sample.py::SampleTests", "tests/test_sample.py::SampleTests::value",
+            "tests/test_sample.txt::SampleTests::test_value",
+            "tests/../outside.py::SampleTests::test_value",
+            "tests\\test_sample.py::SampleTests::test_value",
+            "/tests/test_sample.py::SampleTests::test_value",
+            "tests/test_sample.py::not-valid::test_value",
+            "tests/test_sample.py::SampleTests::test_value::extra",
+        )
+        for value in invalid:
+            with self.subTest(value=value), self.assertRaises(ERRORS.EvidenceConfigurationError):
+                CONFIGURATION.parse_stable_id(value)
+
+    def test_repeated_values_sort_uniquely_and_mappings_freeze_recursively(self) -> None:
+        identity = MODEL.InterpreterIdentity(
+            "C:/Python/python.exe", "C:/Python/python.exe", "windows:volume-2:file-1",
+            SHA256, "cpython", [3, 14, 6, "final", 0], "C:/Python", "C:/Python", True, True, True,
+            SHA256, None,
+        )
+        binding = MODEL.InterpreterBinding("development", identity)
+        fixture_b = MODEL.FixtureSpec("fixtures/b.bin", "regular_file", 1, SHA256)
+        fixture_a = MODEL.FixtureSpec("fixtures/a.bin", "regular_file", 2, SHA256)
+        profile = MODEL.ProfilePlan(
+            "core", ["development"], "development", ["payload:b", "payload:a"], [], [],
+            MODEL.StageBudgets(1, 1, 1, 1, 4), [fixture_b, fixture_a], False, SHA256,
+        )
+        self.assertEqual(identity.platform_identity, "windows:volume-2:file-1")
+        self.assertEqual(identity.version, (3, 14, 6, "final", 0))
+        self.assertEqual(profile.payload_ids, ("payload:a", "payload:b"))
+        self.assertEqual(tuple(item.relative_path for item in profile.fixture_specs),
+                         ("fixtures/a.bin", "fixtures/b.bin"))
+        self.assertEqual(binding.identity, identity)
+        with self.assertRaises(ValueError):
+            MODEL.ProfilePlan(
+                "core", ["development", "development"], "development", [], [], [],
+                MODEL.StageBudgets(1, 1, 1, 1, 4), [], False, SHA256,
+            )
+        with self.assertRaises(ValueError):
+            MODEL.InterpreterIdentity(
+                "C:/Python/python.exe", "C:/Python/python.exe", "windows:identity", SHA256,
+                "cpython", [3, 14, 6, "final", 0], "C:/Python", "C:/Python",
+                True, True, True, SHA256, "",
+            )
+        for bad_platform, bad_version in (
+            ({"volume": 2}, [3, 14, 6, "final", 0]),
+            ("windows:identity", [3, 14, 6]),
+            ("windows:identity", [3, 14, True, "final", 0]),
+            ("windows:identity", [3, 14, 6, 7, 0]),
+        ):
+            with self.subTest(platform=bad_platform, version=bad_version), self.assertRaises(ValueError):
+                MODEL.InterpreterIdentity(
+                    "C:/Python/python.exe", "C:/Python/python.exe", bad_platform, SHA256,
+                    "cpython", bad_version, "C:/Python", "C:/Python", True, True, True,
+                    SHA256, None,
+                )
+
+    def test_profile_variants_require_direct_defaults_or_full_subprofiles(self) -> None:
+        budgets = MODEL.StageBudgets(1, 1, 1, 1, 4)
+        full = MODEL.ProfilePlan(
+            "full", ["development", "cpython311"], None, [], [], ["core"], budgets,
+            [], False, SHA256,
+        )
+        self.assertEqual(full.subprofiles, ("core",))
+        invalid = (
+            ("core", ["development"], None, ["core:sample"], [], []),
+            ("full", ["development"], "development", [], [], ["core"]),
+            ("full", ["development"], None, ["core:sample"], [], ["core"]),
+            ("full", ["development"], None, [], [], []),
+        )
+        for values in invalid:
+            with self.subTest(values=values), self.assertRaises(ValueError):
+                MODEL.ProfilePlan(*values, budgets, [], False, SHA256)
+
+    def test_interpreter_bindings_sort_by_slot_name_not_nested_identity(self) -> None:
+        identity_a = MODEL.InterpreterIdentity(
+            "C:/A/python.exe", "C:/A/python.exe", "windows:a", SHA256,
+            "cpython", [3, 14, 6, "final", 0], "C:/A", "C:/A",
+            True, True, True, SHA256, None,
+        )
+        identity_z = MODEL.InterpreterIdentity(
+            "C:/Z/python.exe", "C:/Z/python.exe", "windows:z", SHA256,
+            "cpython", [3, 11, 9, "final", 0], "C:/Z", "C:/Z",
+            True, True, True, SHA256, None,
+        )
+        condition = MODEL.ObservedCondition("runtime", "safety_stop", True, {})
+        binding_z = MODEL.InterpreterBinding("z-slot", identity_a)
+        binding_a = MODEL.InterpreterBinding("a-slot", identity_z)
+        summary = MODEL.ProfileSummary(
+            "full", SHA256, SHA256, SHA256, SHA256,
+            [binding_z, binding_a], [],
+            [
+                MODEL.WorkerSummary(
+                    "z-profile", binding_z, MODEL.ExecutionStatus.NOT_RUN_SAFETY_STOP,
+                    None, [condition], 0, False,
+                ),
+                MODEL.WorkerSummary(
+                    "a-profile", binding_a, MODEL.ExecutionStatus.NOT_RUN_SAFETY_STOP,
+                    None, [condition], 0, False,
+                ),
+            ],
+            [], [], {}, [condition], SHA256,
+            MODEL.EvidenceGuardSummary(None, None, "not_measured", []),
+            0, False,
+        )
+        self.assertEqual(
+            tuple(item.slot_name for item in summary.interpreter_bindings),
+            ("a-slot", "z-slot"),
+        )
+        with self.assertRaises(ValueError):
+            MODEL.ProfileSummary(
+                "core", SHA256, SHA256, SHA256, SHA256,
+                [binding_z, binding_a], [], [], [], [], {}, [condition], SHA256,
+                MODEL.EvidenceGuardSummary(None, None, "not_measured", []),
+                0, False,
+            )
+
+    def test_guard_and_terminal_summary_invariants_reject_incoherent_states(self) -> None:
+        condition = MODEL.ObservedCondition("runtime", "timeout", True, {"stage": "child"})
+        unchanged = MODEL.EvidenceGuardSummary(SHA256, SHA256, "unchanged", [])
+        self.assertEqual(unchanged.conditions, ())
+        with self.assertRaises(ValueError):
+            MODEL.EvidenceGuardSummary(SHA256, "c" * 64, "unchanged", [])
+        with self.assertRaises(ValueError):
+            MODEL.EvidenceGuardSummary(None, SHA256, "not_measured", [])
+        unstarted = MODEL.PayloadSummary(
+            "core:later", MODEL.ExecutionStatus.NOT_RUN_SAFETY_STOP, [], [], {}, [condition],
+            None, 0, False,
+        )
+        self.assertFalse(unstarted.completed)
+        with self.assertRaises(ValueError):
+            MODEL.PayloadSummary(
+                "core:later", MODEL.ExecutionStatus.NOT_RUN_SAFETY_STOP, ["id"], [], {},
+                [condition], None, 0, False,
+            )
+        with self.assertRaises(ValueError):
+            MODEL.PayloadSummary(
+                "core:done", MODEL.ExecutionStatus.PASSED, ["id"], [], {"passed": 1}, [],
+                None, 1, True,
+            )
+        with self.assertRaises(ValueError):
+            MODEL.PayloadSummary(
+                "core:active", MODEL.ExecutionStatus.RUNTIME_SAFETY_STOP,
+                ["id"], [], {}, [condition], None, 0, False,
+            )
+
+    def test_guard_plan_requires_exact_source_and_governed_path_cardinalities(self) -> None:
+        manifests = tuple(reversed(tuple(
+            MODEL.EvidenceManifestIdentity(
+                f"docs/manifest-{index:02d}.toml", "schema-v1", 100 - index, SHA256, SHA256,
+                f"windows:manifest-{index:02d}",
+            )
+            for index in range(4)
+        )))
+        present = tuple(reversed(tuple(
+            MODEL.EvidenceFileExpectation(
+                f"artifacts/present-{index:02d}.json", 100 - index, SHA256, "retained",
+                f"windows:present-{index:02d}",
+            )
+            for index in range(6)
+        )))
+        absences = tuple(reversed(tuple(
+            MODEL.EvidenceAbsenceExpectation(
+                f"artifacts/absent-{index:02d}.json", "required_absence"
+            )
+            for index in range(18)
+        )))
+        sorted_manifests = tuple(sorted(manifests, key=lambda item: item.relative_path))
+        sorted_present = tuple(sorted(present, key=lambda item: item.relative_path))
+        sorted_absences = tuple(sorted(absences, key=lambda item: item.relative_path))
+        digest = MODEL.semantic_sha256(
+            {
+                "manifest_identities": sorted_manifests,
+                "present_files": sorted_present,
+                "absences": sorted_absences,
+            }
+        )
+        plan = MODEL.EvidenceGuardPlan(digest, manifests, present, absences)
+        self.assertEqual(len(plan.absences), 18)
+        self.assertEqual(plan.manifest_identities, sorted_manifests)
+        self.assertEqual(plan.present_files, sorted_present)
+        self.assertEqual(plan.absences, sorted_absences)
+        for changed in (
+            (manifests[:-1], present, absences),
+            (manifests, present[:-1], absences),
+            (manifests, present, absences[:-1]),
+        ):
+            changed_digest = MODEL.semantic_sha256(
+                {
+                    "manifest_identities": changed[0],
+                    "present_files": changed[1],
+                    "absences": changed[2],
+                }
+            )
+            with self.subTest(lengths=tuple(len(items) for items in changed)), self.assertRaises(ValueError):
+                MODEL.EvidenceGuardPlan(changed_digest, *changed)
+
+    def test_payload_and_worker_summaries_validate_ids_and_unstarted_work(self) -> None:
+        stream = MODEL.CapturedStreamIdentity(0, sha256(b"").hexdigest(), False)
+        captured = MODEL.CapturedOutputIdentity(stream, stream)
+        with self.assertRaises(ValueError):
+            MODEL.PayloadSummary(
+                "core:sample", MODEL.ExecutionStatus.PASSED, ["id:a"],
+                [{"stable_id": "id:b"}], {"passed": 1}, [], captured, 1, True,
+            )
+
+        identity = MODEL.InterpreterIdentity(
+            "C:/Python/python.exe", "C:/Python/python.exe", "windows:identity", SHA256,
+            "cpython", [3, 14, 6, "final", 0], "C:/Python", "C:/Python",
+            True, True, True, SHA256, None,
+        )
+        binding = MODEL.InterpreterBinding("development", identity)
+        trigger = MODEL.ObservedCondition("runtime", "safety_stop", True, {})
+        not_run = MODEL.WorkerSummary(
+            "core", binding, MODEL.ExecutionStatus.NOT_RUN_SAFETY_STOP, None,
+            [trigger], 0, False,
+        )
+        self.assertFalse(not_run.completed)
+        for duration, completed, conditions in ((1, False, [trigger]), (0, True, [trigger]), (0, False, [])):
+            with self.subTest(duration=duration, completed=completed, conditions=conditions), self.assertRaises(ValueError):
+                MODEL.WorkerSummary(
+                    "core", binding, MODEL.ExecutionStatus.NOT_RUN_SAFETY_STOP, None,
+                    conditions, duration, completed,
+                )
+
+    def test_nested_summaries_reject_fabricated_completion_and_exit_state(self) -> None:
+        identity = MODEL.InterpreterIdentity(
+            "C:/Python/python.exe", "C:/Python/python.exe", "windows:identity", SHA256,
+            "cpython", [3, 14, 6, "final", 0], "C:/Python", "C:/Python",
+            True, True, True, SHA256, None,
+        )
+        binding = MODEL.InterpreterBinding("development", identity)
+        stream = MODEL.CapturedStreamIdentity(0, sha256(b"").hexdigest(), False)
+        captured = MODEL.CapturedOutputIdentity(stream, stream)
+        outcome = {"stable_id": "tests/test_sample.py::SampleTests::test_value"}
+        payload = MODEL.PayloadSummary(
+            "core:sample", MODEL.ExecutionStatus.PASSED,
+            [outcome["stable_id"]], [outcome], {"passed": 1}, [], captured, 1, True,
+        )
+        guard = MODEL.EvidenceGuardSummary(SHA256, SHA256, "unchanged", [])
+        direct = MODEL.ProfileSummary(
+            "core", SHA256, SHA256, SHA256, SHA256, [binding], [payload], [],
+            [outcome["stable_id"]], [outcome], {"passed": 1}, [], SHA256,
+            guard, 1, True,
+        )
+        with self.assertRaises(ValueError):
+            MODEL.WorkerSummary(
+                "different-profile", binding, MODEL.ExecutionStatus.PASSED,
+                direct, [], 1, True,
+            )
+
+        trigger = MODEL.ObservedCondition("runtime", "safety_stop", True, {})
+        not_run = MODEL.PayloadSummary(
+            "core:sample", MODEL.ExecutionStatus.NOT_RUN_SAFETY_STOP,
+            [], [], {}, [trigger], None, 0, False,
+        )
+        with self.assertRaises(ValueError):
+            MODEL.ProfileSummary(
+                "core", SHA256, SHA256, SHA256, SHA256, [binding], [not_run], [],
+                [], [], {}, [trigger], SHA256, guard, 1, True,
+            )
+        with self.assertRaises(ValueError):
+            MODEL.RunSummary(
+                "run-id", "core", [direct], [trigger], MODEL.ExitCode.SUCCESS, 1, True,
+            )
+
+        failed_payload = MODEL.PayloadSummary(
+            "core:sample", MODEL.ExecutionStatus.TEST_FAILURE,
+            [outcome["stable_id"]], [outcome], {"failures": 1}, [], captured, 1, True,
+        )
+        failed_profile = MODEL.ProfileSummary(
+            "core", SHA256, SHA256, SHA256, SHA256, [binding], [failed_payload], [],
+            [outcome["stable_id"]], [outcome], {"failures": 1}, [], SHA256,
+            guard, 1, True,
+        )
+        with self.assertRaises(ValueError):
+            MODEL.RunSummary(
+                "run-id", "core", [failed_profile], [], MODEL.ExitCode.SUCCESS, 1, True,
+            )
+        test_failure = MODEL.ObservedCondition(
+            "test_failure", "assertion_failed", True, {}
+        )
+        failed_run = MODEL.RunSummary(
+            "run-id", "core", [failed_profile], [test_failure],
+            MODEL.ExitCode.TEST_FAILURE, 1, True,
+        )
+        self.assertEqual(failed_run.exit_code, MODEL.ExitCode.TEST_FAILURE)
+
+    def test_resolved_worker_plan_requires_exact_internal_transitive_closure(self) -> None:
+        selector = CONFIGURATION.parse_stable_id(
+            "tests/test_sample.py::SampleTests::test_value"
+        )
+        inventory_item = MODEL.ResolvedInventoryItem(
+            selector, MODEL.InventoryExpectation("pass", [], None)
+        )
+        with self.assertRaises(ValueError):
+            MODEL.PayloadPlan(
+                "core:sample", "core", MODEL.TargetKind.CURRENT_SNAPSHOT,
+                ["development"], [inventory_item], ["not-a-probe"], [], {}, [],
+                [], [], [], False,
+            )
+        payload = MODEL.PayloadPlan(
+            "core:sample", "core", MODEL.TargetKind.CURRENT_SNAPSHOT,
+            ["development"], [inventory_item], [], [], {}, [], [], [], [], False,
+        )
+        profile = MODEL.ProfilePlan(
+            "core", ["development"], "development", ["core:sample"], [], [],
+            MODEL.StageBudgets(1, 1, 1, 1, 4), [], False, SHA256,
+        )
+
+        def plan(**changes: object) -> object:
+            values: dict[str, object] = {
+                "profile": profile,
+                "inventory_entries": [inventory_item],
+                "payloads": [payload],
+                "historical_cases": [],
+                "historical_snapshots": [],
+                "historical_blobs": [],
+                "overlays": [],
+                "subprocess_capabilities": [],
+                "call_capabilities": [],
+                "capability_bindings": [],
+                "spec_capabilities_sha256": SHA256,
+                "capability_bindings_sha256": SHA256,
+            }
+            values.update(changes)
+            for name in (
+                "inventory_entries", "payloads", "historical_cases",
+                "historical_snapshots", "historical_blobs", "overlays",
+                "subprocess_capabilities", "call_capabilities",
+                "capability_bindings",
+            ):
+                values[name] = tuple(sorted(
+                    values[name], key=MODEL.canonical_semantic_bytes
+                ))
+            return MODEL.ResolvedWorkerPlan(
+                semantic_sha256=MODEL.semantic_sha256(values), **values
+            )
+
+        self.assertEqual(plan().payloads, (payload,))
+        with self.assertRaises(ValueError):
+            plan(inventory_entries=[], payloads=[])
+        unrelated = MODEL.CallCapability(
+            "call:unrelated", "owner", "module", "qualified", "invoke", 1,
+            "returns_none",
+        )
+        with self.assertRaises(ValueError):
+            plan(call_capabilities=[unrelated])
+        conflicting_payload = MODEL.PayloadPlan(
+            "core:sample", "core", MODEL.TargetKind.CURRENT_SNAPSHOT,
+            ["development"], [inventory_item], [], [], {}, [], [], [], [], True,
+        )
+        with self.assertRaises(ValueError):
+            plan(payloads=[payload, conflicting_payload])
+
+    def test_completed_direct_and_full_summaries_require_their_owned_rows(self) -> None:
+        identity = MODEL.InterpreterIdentity(
+            "C:/Python/python.exe", "C:/Python/python.exe", "windows:identity", SHA256,
+            "cpython", [3, 14, 6, "final", 0], "C:/Python", "C:/Python",
+            True, True, True, SHA256, None,
+        )
+        binding = MODEL.InterpreterBinding("development", identity)
+        guard = MODEL.EvidenceGuardSummary(SHA256, SHA256, "unchanged", [])
+        summary_args = (
+            "core", SHA256, SHA256, SHA256, SHA256, [binding], [], [], [], [], {}, [],
+            SHA256, guard, 1, True,
+        )
+        with self.assertRaises(ValueError):
+            MODEL.ProfileSummary(*summary_args)
+
+        full_args = (
+            "full", SHA256, SHA256, SHA256, SHA256, [], [], [], [], [], {}, [],
+            SHA256, guard, 1, True,
+        )
+        with self.assertRaises(ValueError):
+            MODEL.ProfileSummary(*full_args)
+
+    def test_inventory_entries_preserve_assignment_xor_exclusion(self) -> None:
+        selector = CONFIGURATION.parse_stable_id(
+            "tests/test_sample.py::SampleTests::test_value"
+        )
+        expectation = MODEL.InventoryExpectation("pass", [], None)
+        assigned = MODEL.InventoryEntry(
+            selector, "core", "core:sample", expectation, None, None, None
+        )
+        excluded = MODEL.InventoryEntry(
+            selector, None, None, None, "legacy-only", "stabilization", "milestone-2"
+        )
+        self.assertEqual(assigned.expectation, expectation)
+        self.assertEqual(excluded.exclusion_owner, "stabilization")
+        with self.assertRaises(ValueError):
+            MODEL.InventoryEntry(
+                selector, "core", "core:sample", expectation,
+                "legacy-only", "stabilization", "milestone-2",
+            )
+        with self.assertRaises(ValueError):
+            MODEL.InventoryEntry(selector, None, None, None, None, None, None)
+
+    def test_capability_bindings_use_ruled_total_order_and_call_contract_is_string(self) -> None:
+        call = MODEL.CallCapability(
+            "call:a", "owner", "module", "qualified", "invoke", 1, "returns_none"
+        )
+        self.assertEqual(call.return_contract, "returns_none")
+        with self.assertRaises(ValueError):
+            MODEL.CallCapability("call:b", "owner", "module", "qualified", "invoke", 1, "")
+        with self.assertRaises(ValueError):
+            MODEL.CallCapability("call:c", "owner", "module", "qualified", "invoke", 1, {})
+
+        bindings = (
+            MODEL.CapabilityBinding("item:b", "design", "call", "call:a"),
+            MODEL.CapabilityBinding("item:a", "historical_review", "call", "call:a"),
+            MODEL.CapabilityBinding("item:a", "design", "subprocess", "process:z"),
+            MODEL.CapabilityBinding("item:a", "design", "call", "call:z"),
+        )
+        bundle = MODEL.ConfigurationBundle(
+            Path("C:/repository"), Path("C:/repository/tests/test-profiles.toml"),
+            Path("C:/repository/tests/test-inventory.json"), COMMIT,
+            "docs/files.toml", "docs/absences.toml", "docs/blobs.toml", "docs/v7.toml",
+            SHA256, SHA256, SHA256, SHA256, [], {}, {}, {}, {}, {}, {}, {}, bindings, [],
+        )
+        self.assertEqual(
+            tuple(
+                (item.approval_scope, item.item_id, item.capability_kind, item.capability_id)
+                for item in bundle.capability_bindings
+            ),
+            (
+                ("design", "item:a", "call", "call:z"),
+                ("design", "item:a", "subprocess", "process:z"),
+                ("design", "item:b", "call", "call:a"),
+                ("historical_review", "item:a", "call", "call:a"),
+            ),
+        )
+
+    def test_capability_models_validate_kinds_slots_and_ordered_duplicate_argv(self) -> None:
+        capability = MODEL.SubprocessCapability(
+            "process:a", "python", "active_worker", {},
+            ["python", "-c", "value", "value"], [], None, "target", {}, [], 10,
+            "protocol_committed", ["target"], ["temporary"], False,
+        )
+        self.assertEqual(capability.argv, ("python", "-c", "value", "value"))
+        with self.assertRaises(ValueError):
+            MODEL.SubprocessCapability(
+                "process:a", "python", "ambient_path", {}, ["python"], [], None,
+                "target", {}, [], 10, "protocol_committed", [], [], False,
+            )
+        with self.assertRaises(ValueError):
+            MODEL.CallCapability(
+                "call:a", "unknown", "module", "qualified", "invoke", 1, "returns_none"
+            )
+
+    def test_historical_expected_vectors_have_exact_variant_fields_and_counts(self) -> None:
+        item = MODEL.HistoricalItemExpectation(
+            "tests/test_sample.py::SampleTests::test_value", "pass", None, None, None,
+            None, {},
+        )
+        vector = {
+            "kind": "positive", "passed": 1, "assertion_failed": 0,
+            "setup_failed": 0, "body_entered": 1, "owner_calls": 0,
+            "scientific_calls": 0,
+        }
+        case = MODEL.HistoricalCase(
+            "base", "source", COMMIT, COMMIT, ["historical:base"], vector, [item], []
+        )
+        self.assertEqual(case.expected_vector["passed"], 1)
+        for invalid in ({**vector, "extra": 0}, {**vector, "passed": True}):
+            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
+                MODEL.HistoricalCase(
+                    "base", "source", COMMIT, COMMIT, ["historical:base"], invalid,
+                    [item], [],
+                )
+
+
+class OrchestrationConfigurationTests(unittest.TestCase):
+    def test_load_configuration_builds_frozen_normalized_bundle_and_ns_budgets(self) -> None:
+        with _ConfigurationTree() as tree:
+            bundle = CONFIGURATION.load_configuration(
+                tree.profiles, tree.inventory, repository_root=tree.root
+            )
+        self.assertEqual(bundle.baseline_commit, COMMIT)
+        self.assertEqual(bundle.profiles["core"].budgets, MODEL.StageBudgets(
+            2_000_000_000, 3_000_000_000, 5_000_000_000, 7_000_000_000,
+            17_000_000_000,
+        ))
+        self.assertEqual(
+            bundle.payloads["core:sample"].inventory_items[0].selector.stable_id,
+            "tests/test_sample.py::SampleTests::test_value",
+        )
+        self.assertIsInstance(bundle.profiles, MappingProxyType)
+        self.assertEqual(bundle.stabilization_test_files,
+                         ("tests/test_test_orchestration_configuration.py",))
+        selected = CONFIGURATION.select_profile(bundle, "core", payload_id="core:sample")
+        self.assertEqual(selected.payload_ids, ("core:sample",))
+        with self.assertRaises(ERRORS.EvidenceConfigurationError):
+            CONFIGURATION.select_profile(bundle, "missing")
+        with self.assertRaises(ERRORS.EvidenceConfigurationError):
+            CONFIGURATION.select_profile(bundle, "core", payload_id="missing")
+        with self.assertRaises(ERRORS.EvidenceConfigurationError):
+            CONFIGURATION.select_profile(
+                bundle, "core", payload_id="core:sample", historical_case="case"
+            )
+
+    def test_strict_toml_and_json_reject_duplicate_unknown_missing_and_wrong_types(self) -> None:
+        mutations = {
+            "duplicate-toml": _profiles_toml() + "\nschema_version = \"pontius-test-profiles-v1\"\n",
+            "unknown-root": _profiles_toml() + "\nunexpected = true\n",
+            "missing-root": _profiles_toml().replace(f'baseline_commit = "{COMMIT}"\n', ""),
+            "boolean-budget": _profiles_toml().replace("setup_seconds = 2", "setup_seconds = true"),
+            "unknown-profile-field": _profiles_toml().replace(
+                "gpu_optional = false", "gpu_optional = false\nunexpected = true"
+            ),
+            "escaping-manifest": _profiles_toml().replace(
+                "docs/architecture/sealed-current-files.toml", "../outside.toml"
+            ),
+        }
+        for name, profiles in mutations.items():
+            with self.subTest(name=name), _ConfigurationTree(profiles=profiles) as tree:
+                with self.assertRaises(ERRORS.EvidenceConfigurationError):
+                    CONFIGURATION.load_configuration(
+                        tree.profiles, tree.inventory, repository_root=tree.root
+                    )
+
+        duplicate_json = (
+            '{"schema_version":"pontius-test-inventory-v1",'
+            '"schema_version":"pontius-test-inventory-v1",'
+            f'"baseline_commit":"{COMMIT}","entries":[]}}\n'
+        )
+        with _ConfigurationTree() as tree:
+            tree.inventory.write_text(duplicate_json, encoding="utf-8", newline="\n")
+            with self.assertRaises(ERRORS.EvidenceConfigurationError):
+                CONFIGURATION.load_configuration(
+                    tree.profiles, tree.inventory, repository_root=tree.root
+                )
+
+    def test_unknown_profile_payload_and_capability_references_fail_closed(self) -> None:
+        cases: list[tuple[str, str, dict[str, object]]] = [
+            ("inventory-profile", _profiles_toml(), _inventory(profile_name="missing")),
+            ("inventory-payload", _profiles_toml(), _inventory(payload_id="missing")),
+            (
+                "profile-payload",
+                _profiles_toml().replace('payload_ids = ["core:sample"]', 'payload_ids = ["missing"]'),
+                _inventory(),
+            ),
+            (
+                "payload-interpreter-slot",
+                _profiles_toml().replace(
+                    'allowed_interpreter_slots = ["development"]',
+                    'allowed_interpreter_slots = ["development", "missing"]',
+                ),
+                _inventory(),
+            ),
+            (
+                "malformed-probe-id",
+                _profiles_toml().replace(
+                    "probe_ids = []", 'probe_ids = ["not-a-probe"]',
+                ),
+                _inventory(),
+            ),
+            (
+                "capability",
+                _profiles_toml() + """
+
+[[capability_binding]]
+item_id = "tests/test_sample.py::SampleTests::test_value"
+approval_scope = "design"
+capability_kind = "call"
+capability_id = "missing"
+""",
+                _inventory(),
+            ),
+        ]
+        for name, profiles, inventory in cases:
+            with self.subTest(name=name), _ConfigurationTree(profiles, inventory) as tree:
+                with self.assertRaises(ERRORS.EvidenceConfigurationError):
+                    CONFIGURATION.load_configuration(
+                        tree.profiles, tree.inventory, repository_root=tree.root
+                    )
+
+    def test_excluded_inventory_entries_are_retained_but_not_joined_to_payloads(self) -> None:
+        inventory = _inventory()
+        inventory["entries"].append(
+            {
+                "stable_id": "tests/test_legacy.py::LegacyTests::test_retained",
+                "relative_path": "tests/test_legacy.py",
+                "case_name": "LegacyTests",
+                "method_name": "test_retained",
+                "exclusion": {
+                    "reason": "historical-only",
+                    "owner": "stabilization",
+                    "milestone": "milestone-2",
+                },
+            }
+        )
+        with _ConfigurationTree(inventory=inventory) as tree:
+            bundle = CONFIGURATION.load_configuration(
+                tree.profiles, tree.inventory, repository_root=tree.root
+            )
+        self.assertEqual(len(bundle.inventory_entries), 2)
+        self.assertEqual(
+            tuple(item.selector.stable_id for item in bundle.payloads["core:sample"].inventory_items),
+            ("tests/test_sample.py::SampleTests::test_value",),
+        )
+        excluded = next(item for item in bundle.inventory_entries if item.exclusion_reason)
+        self.assertEqual(excluded.exclusion_milestone, "milestone-2")
+
+        both = _inventory()
+        both["entries"][0]["exclusion"] = {
+            "reason": "invalid", "owner": "owner", "milestone": "milestone"
+        }
+        with self.subTest(case="assignment-and-exclusion"), _ConfigurationTree(inventory=both) as tree:
+            with self.assertRaises(ERRORS.EvidenceConfigurationError):
+                CONFIGURATION.load_configuration(
+                    tree.profiles, tree.inventory, repository_root=tree.root
+                )
+
+    def test_semantic_digests_ignore_toml_and_json_mapping_key_order(self) -> None:
+        with _ConfigurationTree() as first, _ConfigurationTree(
+            profiles=_profiles_toml(reverse_root=True)
+        ) as second:
+            first_inventory = _inventory()
+            second_inventory = {
+                "entries": first_inventory["entries"],
+                "baseline_commit": first_inventory["baseline_commit"],
+                "schema_version": first_inventory["schema_version"],
+            }
+            second.inventory.write_text(
+                json.dumps(second_inventory, ensure_ascii=True, separators=(",", ":")) + "\n",
+                encoding="utf-8", newline="\n",
+            )
+            left = CONFIGURATION.load_configuration(
+                first.profiles, first.inventory, repository_root=first.root
+            )
+            right = CONFIGURATION.load_configuration(
+                second.profiles, second.inventory, repository_root=second.root
+            )
+        self.assertEqual(left.profile_definition_sha256, right.profile_definition_sha256)
+        self.assertEqual(left.inventory_sha256, right.inventory_sha256)
+        self.assertEqual(
+            CONFIGURATION.canonical_semantic_bytes({"b": [2, True], "a": None}),
+            b'{"a":null,"b":[2,true]}',
+        )
+        self.assertEqual(
+            CONFIGURATION.semantic_sha256({"a": 1}), sha256(b'{"a":1}').hexdigest()
+        )
+
+    def test_semantic_digests_use_normalized_collection_order(self) -> None:
+        exclusion = {
+            "stable_id": "tests/test_legacy.py::LegacyTests::test_retained",
+            "relative_path": "tests/test_legacy.py",
+            "case_name": "LegacyTests",
+            "method_name": "test_retained",
+            "exclusion": {
+                "reason": "historical-only", "owner": "stabilization",
+                "milestone": "milestone-2",
+            },
+        }
+        first_inventory = _inventory()
+        first_inventory["entries"].append(exclusion)
+        second_inventory = _inventory()
+        second_inventory["entries"].insert(0, exclusion)
+        first_profiles = _profiles_toml().replace(
+            '["tests/test_test_orchestration_configuration.py"]',
+            '["tests/z_stabilization.py", "tests/a_stabilization.py"]',
+        )
+        second_profiles = _profiles_toml().replace(
+            '["tests/test_test_orchestration_configuration.py"]',
+            '["tests/a_stabilization.py", "tests/z_stabilization.py"]',
+        )
+        with _ConfigurationTree(first_profiles, first_inventory) as first, _ConfigurationTree(
+            second_profiles, second_inventory
+        ) as second:
+            left = CONFIGURATION.load_configuration(
+                first.profiles, first.inventory, repository_root=first.root
+            )
+            right = CONFIGURATION.load_configuration(
+                second.profiles, second.inventory, repository_root=second.root
+            )
+        self.assertEqual(left.profile_definition_sha256, right.profile_definition_sha256)
+        self.assertEqual(left.inventory_sha256, right.inventory_sha256)
+
+    def test_exit_precedence_is_exhaustive_and_ignores_non_exit_optional_conditions(self) -> None:
+        categories = {
+            "integrity": MODEL.ExitCode.INTEGRITY,
+            "configuration": MODEL.ExitCode.CONFIGURATION,
+            "phase": MODEL.ExitCode.PHASE,
+            "runtime": MODEL.ExitCode.RUNTIME,
+            "test_failure": MODEL.ExitCode.TEST_FAILURE,
+            "optional_unavailable": MODEL.ExitCode.OPTIONAL_UNAVAILABLE,
+        }
+        ordered = ["integrity", "configuration", "phase", "runtime", "test_failure", "optional_unavailable"]
+        for left_index, left in enumerate(ordered):
+            for right_index, right in enumerate(ordered):
+                with self.subTest(left=left, right=right):
+                    conditions = [
+                        MODEL.ObservedCondition(left, f"{left}_code", True, {}),
+                        MODEL.ObservedCondition(right, f"{right}_code", True, {}),
+                    ]
+                    self.assertEqual(
+                        CONFIGURATION.choose_exit_code(conditions),
+                        categories[ordered[min(left_index, right_index)]],
+                    )
+        optional = MODEL.ObservedCondition(
+            "optional_unavailable", "gpu_unavailable", False, {"profile": "gpu"}
+        )
+        self.assertEqual(CONFIGURATION.choose_exit_code([optional]), MODEL.ExitCode.SUCCESS)
+        self.assertEqual(CONFIGURATION.choose_exit_code([]), MODEL.ExitCode.SUCCESS)
+        with self.assertRaises(ValueError):
+            MODEL.ObservedCondition("runtime", "timeout", False, {})
+
+
+if __name__ == "__main__":
+    unittest.main(verbosity=2)
diff --git a/tools/__init__.py b/tools/__init__.py
new file mode 100644
index 0000000..f193390
--- /dev/null
+++ b/tools/__init__.py
@@ -0,0 +1 @@
+"""Repository-local standard-library tooling."""
diff --git a/tools/test_orchestration/__init__.py b/tools/test_orchestration/__init__.py
new file mode 100644
index 0000000..a377493
--- /dev/null
+++ b/tools/test_orchestration/__init__.py
@@ -0,0 +1 @@
+"""Standard-library-only test orchestration primitives."""
diff --git a/tools/test_orchestration/configuration.py b/tools/test_orchestration/configuration.py
new file mode 100644
index 0000000..d74ba8e
--- /dev/null
+++ b/tools/test_orchestration/configuration.py
@@ -0,0 +1,948 @@
+"""Strict profile/inventory parsing and pure orchestration selection."""
+
+from __future__ import annotations
+
+from collections.abc import Iterable, Mapping
+from dataclasses import replace
+import json
+from pathlib import Path, PurePosixPath, PureWindowsPath
+import tomllib
+from typing import Any
+
+from .errors import EvidenceConfigurationError
+from .model import (
+    CallCapability,
+    CapabilityBinding,
+    ConfigurationBundle,
+    ExitCode,
+    FixtureSpec,
+    HistoricalCase,
+    HistoricalItemExpectation,
+    InventoryEntry,
+    InterpreterSlot,
+    InventoryExpectation,
+    LifecycleFixturePlan,
+    ObservedCondition,
+    OverlaySpec,
+    PayloadPlan,
+    ProfilePlan,
+    ResolvedInventoryItem,
+    StableSelector,
+    StageBudgets,
+    SubprocessCapability,
+    TargetKind,
+    _normalise_probe_id,
+    canonical_semantic_bytes,
+    semantic_sha256,
+)
+
+
+PROFILE_SCHEMA = "pontius-test-profiles-v1"
+INVENTORY_SCHEMA = "pontius-test-inventory-v1"
+MAX_CONFIGURATION_BYTES = 4 * 1024 * 1024
+_NANOSECONDS_PER_SECOND = 1_000_000_000
+
+
+_PROFILE_ROOT_REQUIRED = {
+    "schema_version",
+    "baseline_commit",
+    "sealed_current_files_manifest",
+    "sealed_current_absences_manifest",
+    "historical_blobs_manifest",
+    "retained_v7_manifest",
+    "inventory_path",
+    "spec_capabilities_sha256",
+    "capability_bindings_sha256",
+    "interpreter_slot",
+    "profile",
+    "payload",
+    "stabilization_test_files",
+}
+_PROFILE_ROOT_OPTIONAL = {
+    "historical_case",
+    "overlay",
+    "subprocess_capability",
+    "call_capability",
+    "capability_binding",
+}
+
+
+def _configuration_error(code: str, message: str, **context: object) -> EvidenceConfigurationError:
+    return EvidenceConfigurationError(code, message, context=context)
+
+
+def _exact_keys(
+    value: object,
+    *,
+    required: set[str],
+    optional: set[str] = frozenset(),
+    label: str,
+) -> Mapping[str, object]:
+    if not isinstance(value, Mapping) or any(type(key) is not str for key in value):
+        raise ValueError(f"{label} must be a string-keyed table")
+    present = set(value)
+    missing = required - present
+    extra = present - required - optional
+    if missing or extra:
+        raise ValueError(
+            f"{label} fields are invalid (missing={sorted(missing)!r}, extra={sorted(extra)!r})"
+        )
+    return value
+
+
+def _exact_string(value: object, name: str) -> str:
+    if type(value) is not str or not value:
+        raise ValueError(f"{name} must be a non-empty string")
+    return value
+
+
+def _optional_string(value: object, name: str) -> str | None:
+    if value is None:
+        return None
+    return _exact_string(value, name)
+
+
+def _exact_int(value: object, name: str, *, positive: bool = False) -> int:
+    if type(value) is not int or value < (1 if positive else 0):
+        qualifier = "positive" if positive else "non-negative"
+        raise ValueError(f"{name} must be a {qualifier} integer")
+    return value
+
+
+def _exact_bool(value: object, name: str) -> bool:
+    if type(value) is not bool:
+        raise ValueError(f"{name} must be a boolean")
+    return value
+
+
+def _exact_list(value: object, name: str) -> list[object]:
+    if type(value) is not list:
+        raise ValueError(f"{name} must be an array")
+    return value
+
+
+def _string_list(value: object, name: str) -> list[str]:
+    return [_exact_string(item, name) for item in _exact_list(value, name)]
+
+
+def _string_mapping(value: object, name: str) -> Mapping[str, str]:
+    table = _exact_keys(value, required=set(value) if isinstance(value, Mapping) else set(), label=name)
+    result: dict[str, str] = {}
+    for key, nested in table.items():
+        result[_exact_string(key, f"{name} key")] = _exact_string(nested, f"{name}.{key}")
+    return result
+
+
+def _require_lower_hex(value: object, name: str, length: int) -> str:
+    text = _exact_string(value, name)
+    if len(text) != length or any(character not in "0123456789abcdef" for character in text):
+        raise ValueError(f"{name} must be {length} lowercase hexadecimal characters")
+    return text
+
+
+def _relative_path(value: object, name: str) -> str:
+    text = _exact_string(value, name)
+    if PureWindowsPath(text).drive or text.startswith(("/", "\\")) or "\\" in text:
+        raise ValueError(f"{name} must be a normalized POSIX relative path")
+    path = PurePosixPath(text)
+    if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
+        raise ValueError(f"{name} must remain below the repository root")
+    normalized = path.as_posix()
+    if normalized in ("", ".") or normalized != text:
+        raise ValueError(f"{name} must be normalized")
+    return normalized
+
+
+def _resolved_child(root: Path, value: object, name: str) -> tuple[str, Path]:
+    relative = _relative_path(value, name)
+    candidate = (root / PurePosixPath(relative)).resolve(strict=False)
+    try:
+        candidate.relative_to(root)
+    except ValueError as error:
+        raise ValueError(f"{name} escapes repository_root") from error
+    return relative, candidate
+
+
+def _read_bounded(path: Path, *, root: Path, label: str) -> bytes:
+    if not isinstance(path, Path) or not path.is_absolute():
+        raise ValueError(f"{label} path must be absolute")
+    resolved = path.resolve(strict=True)
+    try:
+        resolved.relative_to(root)
+    except ValueError as error:
+        raise ValueError(f"{label} path must be below repository_root") from error
+    if not resolved.is_file() or resolved.is_symlink():
+        raise ValueError(f"{label} path must be a regular non-link file")
+    size = resolved.stat().st_size
+    if size > MAX_CONFIGURATION_BYTES:
+        raise ValueError(f"{label} exceeds the configuration size bound")
+    raw = resolved.read_bytes()
+    if len(raw) != size:
+        raise ValueError(f"{label} changed while being read")
+    return raw
+
+
+def _duplicate_rejecting_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
+    result: dict[str, object] = {}
+    for key, value in pairs:
+        if key in result:
+            raise ValueError(f"duplicate JSON key: {key}")
+        result[key] = value
+    return result
+
+
+def _parse_toml(raw: bytes, path: Path) -> Mapping[str, object]:
+    try:
+        text = raw.decode("utf-8", errors="strict")
+        value = tomllib.loads(text)
+    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as error:
+        raise _configuration_error(
+            "profiles_toml_invalid", "profiles configuration is not valid TOML",
+            path=path.as_posix(),
+        ) from error
+    return value
+
+
+def _parse_json(raw: bytes, path: Path) -> Mapping[str, object]:
+    try:
+        text = raw.decode("utf-8", errors="strict")
+        value = json.loads(text, object_pairs_hook=_duplicate_rejecting_object)
+    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
+        raise _configuration_error(
+            "inventory_json_invalid", "test inventory is not valid duplicate-free JSON",
+            path=path.as_posix(),
+        ) from error
+    if not isinstance(value, Mapping):
+        raise _configuration_error(
+            "inventory_json_invalid", "test inventory root must be an object",
+            path=path.as_posix(),
+        )
+    return value
+
+
+def parse_stable_id(value: str) -> StableSelector:
+    try:
+        text = _exact_string(value, "stable_id")
+        if text.count("::") != 2:
+            raise ValueError("stable_id must contain exactly two selector separators")
+        relative_text, case_name, method_name = text.split("::")
+        if "\\" in relative_text:
+            raise ValueError("stable_id paths use POSIX separators")
+        relative_path = _relative_path(relative_text, "stable_id path")
+        path = PurePosixPath(relative_path)
+        if not path.parts or path.parts[0] != "tests" or path.suffix != ".py":
+            raise ValueError("stable_id must name a Python file below tests")
+        if not case_name.isidentifier():
+            raise ValueError("stable_id class must be a Python identifier")
+        if not method_name.isidentifier() or not method_name.startswith("test_"):
+            raise ValueError("stable_id method must be a test_ Python identifier")
+        return StableSelector(text, path, case_name, method_name)
+    except ValueError as error:
+        raise _configuration_error(
+            "stable_id_invalid", "stable test ID is invalid", stable_id=value,
+        ) from error
+
+
+def _parse_inventory_expectation(value: object) -> InventoryExpectation:
+    table = _exact_keys(
+        value, required={"kind"}, optional={"applicable_platforms", "skip_safe_reason_code"},
+        label="inventory expectation",
+    )
+    return InventoryExpectation(
+        _exact_string(table["kind"], "expectation.kind"),
+        _string_list(table.get("applicable_platforms", []), "expectation.applicable_platforms"),
+        _optional_string(table.get("skip_safe_reason_code"), "expectation.skip_safe_reason_code"),
+    )
+
+
+def _parse_inventory(
+    data: Mapping[str, object],
+) -> tuple[
+    str,
+    list[InventoryEntry],
+    list[tuple[ResolvedInventoryItem, str, str]],
+    object,
+]:
+    root = _exact_keys(
+        data, required={"schema_version", "baseline_commit", "entries"},
+        label="inventory root",
+    )
+    if root["schema_version"] != INVENTORY_SCHEMA:
+        raise ValueError("inventory schema_version is unsupported")
+    baseline = _require_lower_hex(root["baseline_commit"], "inventory.baseline_commit", 40)
+    entries: list[InventoryEntry] = []
+    assigned_rows: list[tuple[ResolvedInventoryItem, str, str]] = []
+    seen: set[str] = set()
+    for index, raw_entry in enumerate(_exact_list(root["entries"], "inventory.entries")):
+        entry = _exact_keys(
+            raw_entry,
+            required={"stable_id", "relative_path", "case_name", "method_name"},
+            optional={"assignment", "exclusion"},
+            label=f"inventory.entries[{index}]",
+        )
+        if ("assignment" in entry) == ("exclusion" in entry):
+            raise ValueError("inventory entry requires assignment XOR exclusion")
+        selector = parse_stable_id(_exact_string(entry["stable_id"], "stable_id"))
+        if selector.stable_id in seen:
+            raise ValueError("inventory stable IDs must be unique")
+        seen.add(selector.stable_id)
+        if _relative_path(entry["relative_path"], "inventory relative_path") != selector.relative_path.as_posix():
+            raise ValueError("inventory relative_path disagrees with stable_id")
+        if entry["case_name"] != selector.case_name or entry["method_name"] != selector.method_name:
+            raise ValueError("inventory selector fields disagree with stable_id")
+        if "assignment" in entry:
+            assignment = _exact_keys(
+                entry["assignment"],
+                required={"profile_name", "payload_id", "expectation"},
+                label=f"inventory.entries[{index}].assignment",
+            )
+            profile_name = _exact_string(assignment["profile_name"], "assignment.profile_name")
+            payload_id = _exact_string(assignment["payload_id"], "assignment.payload_id")
+            expectation = _parse_inventory_expectation(assignment["expectation"])
+            item = ResolvedInventoryItem(selector, expectation)
+            entries.append(InventoryEntry(
+                selector, profile_name, payload_id, expectation, None, None, None
+            ))
+            assigned_rows.append((item, profile_name, payload_id))
+        else:
+            exclusion = _exact_keys(
+                entry["exclusion"],
+                required={"reason", "owner", "milestone"},
+                label=f"inventory.entries[{index}].exclusion",
+            )
+            entries.append(InventoryEntry(
+                selector, None, None, None,
+                _exact_string(exclusion["reason"], "exclusion.reason"),
+                _exact_string(exclusion["owner"], "exclusion.owner"),
+                _exact_string(exclusion["milestone"], "exclusion.milestone"),
+            ))
+    entries.sort(key=lambda item: item.selector.stable_id)
+    assigned_rows.sort(key=lambda row: row[0].selector.stable_id)
+    return baseline, entries, assigned_rows, root
+
+
+def _parse_slot(value: object, index: int) -> InterpreterSlot:
+    table = _exact_keys(
+        value,
+        required={"name", "resolution", "implementation", "required_for_full"},
+        optional={
+            "windows_relative_path", "posix_relative_path", "environment_variable",
+            "minimum_version", "exact_version",
+        },
+        label=f"interpreter_slot[{index}]",
+    )
+    resolution = _exact_string(table["resolution"], "interpreter_slot.resolution")
+    minimum = table.get("minimum_version")
+    exact = table.get("exact_version")
+    if minimum is not None:
+        minimum = [_exact_int(item, "minimum_version") for item in _exact_list(minimum, "minimum_version")]
+    if exact is not None:
+        exact = [_exact_int(item, "exact_version") for item in _exact_list(exact, "exact_version")]
+    return InterpreterSlot(
+        _exact_string(table["name"], "interpreter_slot.name"),
+        resolution,
+        _optional_string(table.get("windows_relative_path"), "windows_relative_path"),
+        _optional_string(table.get("posix_relative_path"), "posix_relative_path"),
+        _optional_string(table.get("environment_variable"), "environment_variable"),
+        _exact_string(table["implementation"], "implementation"),
+        minimum,
+        exact,
+        _exact_bool(table["required_for_full"], "required_for_full"),
+    )
+
+
+def _parse_fixture(value: object, label: str) -> FixtureSpec:
+    table = _exact_keys(
+        value, required={"relative_path", "path_kind", "byte_length", "raw_sha256"}, label=label,
+    )
+    return FixtureSpec(
+        _relative_path(table["relative_path"], f"{label}.relative_path"),
+        _exact_string(table["path_kind"], f"{label}.path_kind"),
+        _exact_int(table["byte_length"], f"{label}.byte_length"),
+        _require_lower_hex(table["raw_sha256"], f"{label}.raw_sha256", 64),
+    )
+
+
+def _parse_lifecycle_fixture(value: object, label: str) -> LifecycleFixturePlan:
+    table = _exact_keys(
+        value,
+        required={
+            "fixture_id", "kind", "relative_path", "member_ids", "allowed_write_roots",
+            "forbidden_relative_paths", "serialized",
+        },
+        optional={"class_name"},
+        label=label,
+    )
+    return LifecycleFixturePlan(
+        _exact_string(table["fixture_id"], f"{label}.fixture_id"),
+        _exact_string(table["kind"], f"{label}.kind"),
+        _relative_path(table["relative_path"], f"{label}.relative_path"),
+        _optional_string(table.get("class_name"), f"{label}.class_name"),
+        _string_list(table["member_ids"], f"{label}.member_ids"),
+        _string_list(table["allowed_write_roots"], f"{label}.allowed_write_roots"),
+        [_relative_path(item, f"{label}.forbidden_relative_paths") for item in _exact_list(table["forbidden_relative_paths"], f"{label}.forbidden_relative_paths")],
+        _exact_bool(table["serialized"], f"{label}.serialized"),
+    )
+
+
+def _parse_payload(
+    value: object,
+    index: int,
+    inventory_rows: list[tuple[ResolvedInventoryItem, str, str]],
+) -> PayloadPlan:
+    label = f"payload[{index}]"
+    table = _exact_keys(
+        value,
+        required={
+            "payload_id", "profile_name", "target_kind", "allowed_interpreter_slots",
+            "probe_ids", "environment_additions", "environment_removals", "allowed_write_roots",
+            "forbidden_relative_paths", "serialized",
+        },
+        optional={"ignored_fixture", "lifecycle_fixture"},
+        label=label,
+    )
+    payload_id = _exact_string(table["payload_id"], f"{label}.payload_id")
+    inventory_items = [item for item, _, assigned_payload in inventory_rows if assigned_payload == payload_id]
+    fixtures = [
+        _parse_fixture(item, f"{label}.ignored_fixture[{fixture_index}]")
+        for fixture_index, item in enumerate(_exact_list(table.get("ignored_fixture", []), f"{label}.ignored_fixture"))
+    ]
+    lifecycle = [
+        _parse_lifecycle_fixture(item, f"{label}.lifecycle_fixture[{fixture_index}]")
+        for fixture_index, item in enumerate(_exact_list(table.get("lifecycle_fixture", []), f"{label}.lifecycle_fixture"))
+    ]
+    return PayloadPlan(
+        payload_id,
+        _exact_string(table["profile_name"], f"{label}.profile_name"),
+        _exact_string(table["target_kind"], f"{label}.target_kind"),
+        _string_list(table["allowed_interpreter_slots"], f"{label}.allowed_interpreter_slots"),
+        inventory_items,
+        [
+            _normalise_probe_id(item, f"{label}.probe_ids")
+            for item in _exact_list(table["probe_ids"], f"{label}.probe_ids")
+        ],
+        lifecycle,
+        _string_mapping(table["environment_additions"], f"{label}.environment_additions"),
+        _string_list(table["environment_removals"], f"{label}.environment_removals"),
+        _string_list(table["allowed_write_roots"], f"{label}.allowed_write_roots"),
+        [_relative_path(item, f"{label}.forbidden_relative_paths") for item in _exact_list(table["forbidden_relative_paths"], f"{label}.forbidden_relative_paths")],
+        fixtures,
+        _exact_bool(table["serialized"], f"{label}.serialized"),
+    )
+
+
+def _parse_budgets(value: object, label: str) -> StageBudgets:
+    table = _exact_keys(
+        value,
+        required={"setup_seconds", "child_seconds", "termination_seconds", "cleanup_seconds", "total_seconds"},
+        label=label,
+    )
+    seconds = {
+        name: _exact_int(table[name], f"{label}.{name}", positive=True)
+        for name in table
+    }
+    return StageBudgets(
+        seconds["setup_seconds"] * _NANOSECONDS_PER_SECOND,
+        seconds["child_seconds"] * _NANOSECONDS_PER_SECOND,
+        seconds["termination_seconds"] * _NANOSECONDS_PER_SECOND,
+        seconds["cleanup_seconds"] * _NANOSECONDS_PER_SECOND,
+        seconds["total_seconds"] * _NANOSECONDS_PER_SECOND,
+    )
+
+
+def _fixture_union(payloads: Iterable[PayloadPlan]) -> tuple[FixtureSpec, ...]:
+    by_path: dict[str, FixtureSpec] = {}
+    for payload in payloads:
+        for fixture in payload.fixture_specs:
+            previous = by_path.get(fixture.relative_path)
+            if previous is not None and previous != fixture:
+                raise ValueError("profile payloads declare conflicting fixture identities")
+            by_path[fixture.relative_path] = fixture
+    return tuple(by_path[path] for path in sorted(by_path))
+
+
+def _parse_profile(
+    value: object,
+    index: int,
+    *,
+    payloads: Mapping[str, PayloadPlan],
+    slots: Mapping[str, InterpreterSlot],
+) -> ProfilePlan:
+    label = f"profile[{index}]"
+    table = _exact_keys(
+        value,
+        required={
+            "name", "interpreter_slots", "payload_ids",
+            "historical_case_ids", "subprofiles", "gpu_optional", "budgets",
+        },
+        optional={"default_interpreter_slot"},
+        label=label,
+    )
+    name = _exact_string(table["name"], f"{label}.name")
+    interpreter_slots = _string_list(table["interpreter_slots"], f"{label}.interpreter_slots")
+    payload_ids = _string_list(table["payload_ids"], f"{label}.payload_ids")
+    unknown_slots = set(interpreter_slots) - set(slots)
+    unknown_payloads = set(payload_ids) - set(payloads)
+    if unknown_slots:
+        raise ValueError(f"{label} references unknown interpreter slots")
+    if unknown_payloads:
+        raise ValueError(f"{label} references unknown payloads")
+    for payload_id in payload_ids:
+        payload = payloads[payload_id]
+        if payload.profile_name != name:
+            raise ValueError("payload profile_name disagrees with owning profile")
+    default_slot = _optional_string(table.get("default_interpreter_slot"), f"{label}.default_interpreter_slot")
+    if default_slot is not None:
+        for payload_id in payload_ids:
+            if default_slot not in payloads[payload_id].allowed_interpreter_slots:
+                raise ValueError("default interpreter slot is not allowed by every selected payload")
+    profile = ProfilePlan(
+        name,
+        interpreter_slots,
+        default_slot,
+        payload_ids,
+        _string_list(table["historical_case_ids"], f"{label}.historical_case_ids"),
+        _string_list(table["subprofiles"], f"{label}.subprofiles"),
+        _parse_budgets(table["budgets"], f"{label}.budgets"),
+        _fixture_union(payloads[payload_id] for payload_id in payload_ids),
+        _exact_bool(table["gpu_optional"], f"{label}.gpu_optional"),
+        "0" * 64,
+    )
+    definition = {
+        field: getattr(profile, field)
+        for field in (
+            "name", "interpreter_slots", "default_interpreter_slot", "payload_ids",
+            "historical_case_ids", "subprofiles", "budgets", "fixture_specs", "gpu_optional",
+        )
+    }
+    return replace(profile, definition_sha256=semantic_sha256(definition))
+
+
+def _parse_item_expectation(value: object, label: str) -> HistoricalItemExpectation:
+    table = _exact_keys(
+        value,
+        required={"item_id", "outcome"},
+        optional={"phase", "exception_type", "safe_reason_code", "body_entered", "capability_counters"},
+        label=label,
+    )
+    body_entered = table.get("body_entered")
+    if body_entered is not None:
+        body_entered = _exact_bool(body_entered, f"{label}.body_entered")
+    counters = table.get("capability_counters", {})
+    if not isinstance(counters, Mapping):
+        raise ValueError(f"{label}.capability_counters must be a mapping")
+    for key, count in counters.items():
+        _exact_string(key, f"{label}.capability_counters key")
+        _exact_int(count, f"{label}.capability_counters.{key}")
+    return HistoricalItemExpectation(
+        _exact_string(table["item_id"], f"{label}.item_id"),
+        _exact_string(table["outcome"], f"{label}.outcome"),
+        _optional_string(table.get("phase"), f"{label}.phase"),
+        _optional_string(table.get("exception_type"), f"{label}.exception_type"),
+        _optional_string(table.get("safe_reason_code"), f"{label}.safe_reason_code"),
+        body_entered,
+        counters,
+    )
+
+
+def _parse_historical_case(value: object, index: int) -> HistoricalCase:
+    label = f"historical_case[{index}]"
+    table = _exact_keys(
+        value,
+        required={
+            "case_id", "phase", "commit", "root_tree_oid", "payload_ids", "overlay_ids",
+            "expected_vector", "item_expectation",
+        },
+        label=label,
+    )
+    vector = table["expected_vector"]
+    if not isinstance(vector, Mapping):
+        raise ValueError(f"{label}.expected_vector must be a table")
+    return HistoricalCase(
+        _exact_string(table["case_id"], f"{label}.case_id"),
+        _exact_string(table["phase"], f"{label}.phase"),
+        _require_lower_hex(table["commit"], f"{label}.commit", 40),
+        _require_lower_hex(table["root_tree_oid"], f"{label}.root_tree_oid", 40),
+        _string_list(table["payload_ids"], f"{label}.payload_ids"),
+        vector,
+        [_parse_item_expectation(item, f"{label}.item_expectation[{item_index}]") for item_index, item in enumerate(_exact_list(table["item_expectation"], f"{label}.item_expectation"))],
+        _string_list(table["overlay_ids"], f"{label}.overlay_ids"),
+    )
+
+
+def _parse_overlay(value: object, index: int) -> OverlaySpec:
+    label = f"overlay[{index}]"
+    table = _exact_keys(
+        value,
+        required={"overlay_id", "source_commit", "source_path", "destination_path", "byte_length", "raw_sha256"},
+        label=label,
+    )
+    return OverlaySpec(
+        _exact_string(table["overlay_id"], f"{label}.overlay_id"),
+        _require_lower_hex(table["source_commit"], f"{label}.source_commit", 40),
+        _relative_path(table["source_path"], f"{label}.source_path"),
+        _relative_path(table["destination_path"], f"{label}.destination_path"),
+        _exact_int(table["byte_length"], f"{label}.byte_length"),
+        _require_lower_hex(table["raw_sha256"], f"{label}.raw_sha256", 64),
+    )
+
+
+def _parse_subprocess_capability(value: object, index: int) -> SubprocessCapability:
+    label = f"subprocess_capability[{index}]"
+    table = _exact_keys(
+        value,
+        required={
+            "capability_id", "executable_role", "executable_slot", "executable_constraints",
+            "argv", "argv_template", "dynamic_program_sha256", "cwd_class",
+            "environment_additions", "environment_removals", "timeout_ns",
+            "expected_return_category", "read_roots", "write_roots",
+            "fixed_descendant_permission",
+        },
+        label=label,
+    )
+    constraints = table["executable_constraints"]
+    if not isinstance(constraints, Mapping):
+        raise ValueError(f"{label}.executable_constraints must be a mapping")
+    return SubprocessCapability(
+        _exact_string(table["capability_id"], f"{label}.capability_id"),
+        _exact_string(table["executable_role"], f"{label}.executable_role"),
+        _exact_string(table["executable_slot"], f"{label}.executable_slot"),
+        constraints,
+        _string_list(table["argv"], f"{label}.argv"),
+        _string_list(table["argv_template"], f"{label}.argv_template"),
+        _optional_string(table["dynamic_program_sha256"], f"{label}.dynamic_program_sha256"),
+        _exact_string(table["cwd_class"], f"{label}.cwd_class"),
+        _string_mapping(table["environment_additions"], f"{label}.environment_additions"),
+        _string_list(table["environment_removals"], f"{label}.environment_removals"),
+        _exact_int(table["timeout_ns"], f"{label}.timeout_ns", positive=True),
+        _exact_string(table["expected_return_category"], f"{label}.expected_return_category"),
+        _string_list(table["read_roots"], f"{label}.read_roots"),
+        _string_list(table["write_roots"], f"{label}.write_roots"),
+        _exact_bool(table["fixed_descendant_permission"], f"{label}.fixed_descendant_permission"),
+    )
+
+
+def _parse_call_capability(value: object, index: int) -> CallCapability:
+    label = f"call_capability[{index}]"
+    table = _exact_keys(
+        value,
+        required={"capability_id", "kind", "module_name", "qualified_name", "action", "maximum_calls", "return_contract"},
+        label=label,
+    )
+    return CallCapability(
+        _exact_string(table["capability_id"], f"{label}.capability_id"),
+        _exact_string(table["kind"], f"{label}.kind"),
+        _exact_string(table["module_name"], f"{label}.module_name"),
+        _exact_string(table["qualified_name"], f"{label}.qualified_name"),
+        _exact_string(table["action"], f"{label}.action"),
+        _exact_int(table["maximum_calls"], f"{label}.maximum_calls", positive=True),
+        _exact_string(table["return_contract"], f"{label}.return_contract"),
+    )
+
+
+def _parse_capability_binding(value: object, index: int) -> CapabilityBinding:
+    label = f"capability_binding[{index}]"
+    table = _exact_keys(
+        value,
+        required={"item_id", "approval_scope", "capability_kind", "capability_id"},
+        label=label,
+    )
+    return CapabilityBinding(
+        _exact_string(table["item_id"], f"{label}.item_id"),
+        _exact_string(table["approval_scope"], f"{label}.approval_scope"),
+        _exact_string(table["capability_kind"], f"{label}.capability_kind"),
+        _exact_string(table["capability_id"], f"{label}.capability_id"),
+    )
+
+
+def _unique_mapping(values: Iterable[Any], key_name: str, label: str) -> dict[str, Any]:
+    result: dict[str, Any] = {}
+    for value in values:
+        key = getattr(value, key_name)
+        if key in result:
+            raise ValueError(f"{label} identifiers must be unique")
+        result[key] = value
+    return result
+
+
+def _validate_references(
+    *,
+    slots: Mapping[str, InterpreterSlot],
+    profiles: Mapping[str, ProfilePlan],
+    payloads: Mapping[str, PayloadPlan],
+    cases: Mapping[str, HistoricalCase],
+    overlays: Mapping[str, OverlaySpec],
+    subprocess_capabilities: Mapping[str, SubprocessCapability],
+    call_capabilities: Mapping[str, CallCapability],
+    bindings: tuple[CapabilityBinding, ...],
+    inventory_rows: list[tuple[ResolvedInventoryItem, str, str]],
+) -> None:
+    for item, profile_name, payload_id in inventory_rows:
+        if profile_name not in profiles or payload_id not in payloads:
+            raise ValueError(f"inventory item {item.selector.stable_id} has an unknown assignment")
+        if payloads[payload_id].profile_name != profile_name:
+            raise ValueError("inventory assignment profile and payload disagree")
+    for profile in profiles.values():
+        if set(profile.historical_case_ids) - set(cases):
+            raise ValueError("profile references an unknown historical case")
+        if set(profile.subprofiles) - set(profiles):
+            raise ValueError("profile references an unknown subprofile")
+    for payload in payloads.values():
+        if set(payload.allowed_interpreter_slots) - set(slots):
+            raise ValueError("payload references an unknown interpreter slot")
+    for case in cases.values():
+        if set(case.payload_ids) - set(payloads) or set(case.overlay_ids) - set(overlays):
+            raise ValueError("historical case contains an unknown payload or overlay")
+    known_items = {item.selector.stable_id for item, _, _ in inventory_rows}
+    for payload in payloads.values():
+        known_items.update(payload.probe_ids)
+        known_items.update(fixture.fixture_id for fixture in payload.lifecycle_fixtures)
+    for binding in bindings:
+        definitions: Mapping[str, object]
+        if binding.capability_kind == "subprocess":
+            definitions = subprocess_capabilities
+        else:
+            definitions = call_capabilities
+        if binding.capability_id not in definitions:
+            raise ValueError("capability binding references an unknown capability")
+        if binding.item_id not in known_items:
+            raise ValueError("capability binding references an unknown item")
+
+
+def load_configuration(
+    profiles_path: Path,
+    inventory_path: Path,
+    *,
+    repository_root: Path,
+) -> ConfigurationBundle:
+    try:
+        if not isinstance(repository_root, Path) or not repository_root.is_absolute():
+            raise ValueError("repository_root must be an absolute Path")
+        root = repository_root.resolve(strict=True)
+        if not root.is_dir() or root.is_symlink():
+            raise ValueError("repository_root must be a regular directory root")
+        profile_raw = _read_bounded(profiles_path, root=root, label="profiles")
+        inventory_raw = _read_bounded(inventory_path, root=root, label="inventory")
+        profile_data = _parse_toml(profile_raw, profiles_path)
+        inventory_data = _parse_json(inventory_raw, inventory_path)
+        profile_root = _exact_keys(
+            profile_data,
+            required=_PROFILE_ROOT_REQUIRED,
+            optional=_PROFILE_ROOT_OPTIONAL,
+            label="profiles root",
+        )
+        if profile_root["schema_version"] != PROFILE_SCHEMA:
+            raise ValueError("profiles schema_version is unsupported")
+        baseline = _require_lower_hex(profile_root["baseline_commit"], "baseline_commit", 40)
+        inventory_baseline, inventory_entries, inventory_rows, normalized_inventory = _parse_inventory(inventory_data)
+        if inventory_baseline != baseline:
+            raise ValueError("profile and inventory baselines disagree")
+
+        configured_inventory_path, expected_inventory_path = _resolved_child(
+            root, profile_root["inventory_path"], "inventory_path"
+        )
+        if expected_inventory_path != inventory_path.resolve(strict=True):
+            raise ValueError("inventory_path does not identify the supplied inventory")
+        manifest_paths = {}
+        for name in (
+            "sealed_current_files_manifest", "sealed_current_absences_manifest",
+            "historical_blobs_manifest", "retained_v7_manifest",
+        ):
+            manifest_paths[name], _ = _resolved_child(root, profile_root[name], name)
+
+        slots = _unique_mapping(
+            (_parse_slot(item, index) for index, item in enumerate(_exact_list(profile_root["interpreter_slot"], "interpreter_slot"))),
+            "name", "interpreter slots",
+        )
+        payloads = _unique_mapping(
+            (_parse_payload(item, index, inventory_rows) for index, item in enumerate(_exact_list(profile_root["payload"], "payload"))),
+            "payload_id", "payloads",
+        )
+        profiles = _unique_mapping(
+            (_parse_profile(item, index, payloads=payloads, slots=slots) for index, item in enumerate(_exact_list(profile_root["profile"], "profile"))),
+            "name", "profiles",
+        )
+        cases = _unique_mapping(
+            (_parse_historical_case(item, index) for index, item in enumerate(_exact_list(profile_root.get("historical_case", []), "historical_case"))),
+            "case_id", "historical cases",
+        )
+        overlays = _unique_mapping(
+            (_parse_overlay(item, index) for index, item in enumerate(_exact_list(profile_root.get("overlay", []), "overlay"))),
+            "overlay_id", "overlays",
+        )
+        subprocess_capabilities = _unique_mapping(
+            (_parse_subprocess_capability(item, index) for index, item in enumerate(_exact_list(profile_root.get("subprocess_capability", []), "subprocess_capability"))),
+            "capability_id", "subprocess capabilities",
+        )
+        call_capabilities = _unique_mapping(
+            (_parse_call_capability(item, index) for index, item in enumerate(_exact_list(profile_root.get("call_capability", []), "call_capability"))),
+            "capability_id", "call capabilities",
+        )
+        bindings = tuple(
+            _parse_capability_binding(item, index)
+            for index, item in enumerate(_exact_list(profile_root.get("capability_binding", []), "capability_binding"))
+        )
+        _validate_references(
+            slots=slots, profiles=profiles, payloads=payloads, cases=cases, overlays=overlays,
+            subprocess_capabilities=subprocess_capabilities, call_capabilities=call_capabilities,
+            bindings=bindings, inventory_rows=inventory_rows,
+        )
+        stabilization_files = [
+            _relative_path(item, "stabilization_test_files")
+            for item in _exact_list(profile_root["stabilization_test_files"], "stabilization_test_files")
+        ]
+        spec_digest = _require_lower_hex(profile_root["spec_capabilities_sha256"], "spec_capabilities_sha256", 64)
+        binding_digest = _require_lower_hex(profile_root["capability_bindings_sha256"], "capability_bindings_sha256", 64)
+        stabilization_files = tuple(sorted(set(stabilization_files)))
+        if len(stabilization_files) != len(_exact_list(profile_root["stabilization_test_files"], "stabilization_test_files")):
+            raise ValueError("stabilization_test_files must be unique")
+        normalized_profiles = {
+            "schema_version": PROFILE_SCHEMA,
+            "baseline_commit": baseline,
+            "sealed_current_files_manifest": manifest_paths["sealed_current_files_manifest"],
+            "sealed_current_absences_manifest": manifest_paths["sealed_current_absences_manifest"],
+            "historical_blobs_manifest": manifest_paths["historical_blobs_manifest"],
+            "retained_v7_manifest": manifest_paths["retained_v7_manifest"],
+            "inventory_path": configured_inventory_path,
+            "spec_capabilities_sha256": spec_digest,
+            "capability_bindings_sha256": binding_digest,
+            "interpreter_slots": tuple(slots[name] for name in sorted(slots)),
+            "profiles": tuple(profiles[name] for name in sorted(profiles)),
+            "payloads": tuple(payloads[name] for name in sorted(payloads)),
+            "historical_cases": tuple(cases[name] for name in sorted(cases)),
+            "overlays": tuple(overlays[name] for name in sorted(overlays)),
+            "subprocess_capabilities": tuple(
+                subprocess_capabilities[name] for name in sorted(subprocess_capabilities)
+            ),
+            "call_capabilities": tuple(
+                call_capabilities[name] for name in sorted(call_capabilities)
+            ),
+            "capability_bindings": tuple(sorted(
+                bindings,
+                key=lambda item: (
+                    item.approval_scope, item.item_id, item.capability_kind,
+                    item.capability_id,
+                ),
+            )),
+            "stabilization_test_files": stabilization_files,
+        }
+        normalized_inventory = {
+            "schema_version": INVENTORY_SCHEMA,
+            "baseline_commit": inventory_baseline,
+            "entries": tuple(inventory_entries),
+        }
+        return ConfigurationBundle(
+            root,
+            profiles_path.resolve(strict=True),
+            inventory_path.resolve(strict=True),
+            baseline,
+            manifest_paths["sealed_current_files_manifest"],
+            manifest_paths["sealed_current_absences_manifest"],
+            manifest_paths["historical_blobs_manifest"],
+            manifest_paths["retained_v7_manifest"],
+            semantic_sha256(normalized_profiles),
+            semantic_sha256(normalized_inventory),
+            spec_digest,
+            binding_digest,
+            inventory_entries,
+            slots,
+            profiles,
+            payloads,
+            cases,
+            overlays,
+            subprocess_capabilities,
+            call_capabilities,
+            bindings,
+            stabilization_files,
+        )
+    except EvidenceConfigurationError:
+        raise
+    except (OSError, ValueError, TypeError) as error:
+        raise _configuration_error(
+            "configuration_invalid", "test orchestration configuration is invalid",
+            profiles_path=profiles_path.as_posix() if isinstance(profiles_path, Path) else str(profiles_path),
+            inventory_path=inventory_path.as_posix() if isinstance(inventory_path, Path) else str(inventory_path),
+        ) from error
+
+
+def select_profile(
+    bundle: ConfigurationBundle,
+    name: str,
+    *,
+    payload_id: str | None = None,
+    historical_case: str | None = None,
+) -> ProfilePlan:
+    if not isinstance(bundle, ConfigurationBundle):
+        raise _configuration_error(
+            "configuration_bundle_invalid", "configuration bundle is invalid",
+            supplied_type=type(bundle).__name__,
+        )
+    if payload_id is not None and historical_case is not None:
+        raise _configuration_error(
+            "profile_selector_ambiguous", "payload and historical-case filters are mutually exclusive",
+            profile=name,
+        )
+    profile = bundle.profiles.get(name)
+    if profile is None:
+        raise _configuration_error("profile_unknown", "profile is not defined", profile=name)
+    if payload_id is not None:
+        if payload_id not in profile.payload_ids:
+            raise _configuration_error(
+                "payload_unknown", "payload does not belong to the selected profile",
+                profile=name, payload_id=payload_id,
+            )
+        payload = bundle.payloads[payload_id]
+        return replace(
+            profile,
+            payload_ids=(payload_id,),
+            historical_case_ids=(),
+            fixture_specs=payload.fixture_specs,
+        )
+    if historical_case is not None:
+        if historical_case not in profile.historical_case_ids:
+            raise _configuration_error(
+                "historical_case_unknown", "historical case does not belong to the selected profile",
+                profile=name, historical_case=historical_case,
+            )
+        case = bundle.historical_cases[historical_case]
+        payloads = tuple(bundle.payloads[payload] for payload in case.payload_ids)
+        return replace(
+            profile,
+            payload_ids=case.payload_ids,
+            historical_case_ids=(historical_case,),
+            fixture_specs=_fixture_union(payloads),
+        )
+    return profile
+
+
+_EXIT_PRECEDENCE = (
+    ("integrity", ExitCode.INTEGRITY),
+    ("configuration", ExitCode.CONFIGURATION),
+    ("phase", ExitCode.PHASE),
+    ("runtime", ExitCode.RUNTIME),
+    ("test_failure", ExitCode.TEST_FAILURE),
+    ("optional_unavailable", ExitCode.OPTIONAL_UNAVAILABLE),
+)
+
+
+def choose_exit_code(conditions: Iterable[ObservedCondition]) -> ExitCode:
+    observed: set[str] = set()
+    for condition in conditions:
+        if not isinstance(condition, ObservedCondition):
+            raise ValueError("conditions must contain ObservedCondition values")
+        if condition.affects_exit:
+            observed.add(condition.category)
+    for category, exit_code in _EXIT_PRECEDENCE:
+        if category in observed:
+            return exit_code
+    return ExitCode.SUCCESS
+
+
+__all__ = (
+    "canonical_semantic_bytes",
+    "choose_exit_code",
+    "load_configuration",
+    "parse_stable_id",
+    "select_profile",
+    "semantic_sha256",
+)
diff --git a/tools/test_orchestration/errors.py b/tools/test_orchestration/errors.py
new file mode 100644
index 0000000..d71de66
--- /dev/null
+++ b/tools/test_orchestration/errors.py
@@ -0,0 +1,72 @@
+"""Stable, tool-local exceptions for test orchestration."""
+
+from __future__ import annotations
+
+from collections.abc import Mapping
+from types import MappingProxyType
+from typing import TypeAlias
+
+
+FrozenContextValue: TypeAlias = (
+    str
+    | int
+    | bool
+    | None
+    | tuple["FrozenContextValue", ...]
+    | frozenset["FrozenContextValue"]
+    | Mapping[str, "FrozenContextValue"]
+)
+
+
+def _freeze_context_value(value: object) -> FrozenContextValue:
+    if value is None or type(value) in (str, int, bool):
+        return value
+    if isinstance(value, Mapping):
+        frozen_items: list[tuple[str, FrozenContextValue]] = []
+        for key, nested_value in value.items():
+            if type(key) is not str:
+                raise TypeError("orchestration error context keys must be strings")
+            frozen_items.append((key, _freeze_context_value(nested_value)))
+        return MappingProxyType(dict(sorted(frozen_items)))
+    if isinstance(value, (tuple, list)):
+        return tuple(_freeze_context_value(item) for item in value)
+    if isinstance(value, (set, frozenset)):
+        return frozenset(_freeze_context_value(item) for item in value)
+    raise TypeError("orchestration error context contains an unsupported value")
+
+
+class OrchestrationError(Exception):
+    """Base exception carrying stable machine-readable fields."""
+
+    def __init__(self, code: str, message: str, *, context: Mapping[str, object]) -> None:
+        if type(code) is not str or not code:
+            raise ValueError("orchestration error code must be a non-empty string")
+        if type(message) is not str or not message:
+            raise ValueError("orchestration error message must be a non-empty string")
+        frozen_context = _freeze_context_value(context)
+        if not isinstance(frozen_context, Mapping):
+            raise TypeError("orchestration error context must be a mapping")
+        self.code = code
+        self.message = message
+        self.context = frozen_context
+        super().__init__(message)
+
+
+class EvidenceConfigurationError(OrchestrationError):
+    """Profile, inventory, or command configuration is invalid."""
+
+
+class EvidenceIntegrityError(OrchestrationError):
+    """Evidence bytes or semantic identity do not match their contract."""
+
+
+class AuthorizationPhaseError(OrchestrationError):
+    """The requested authorization phase is unavailable or mixed."""
+
+
+class LifecycleStateError(OrchestrationError):
+    """Lifecycle state is incompatible with the selected profile."""
+
+
+class RuntimeContractError(OrchestrationError):
+    """A runtime collaborator violated the orchestration contract."""
diff --git a/tools/test_orchestration/model.py b/tools/test_orchestration/model.py
new file mode 100644
index 0000000..92a1dde
--- /dev/null
+++ b/tools/test_orchestration/model.py
@@ -0,0 +1,1536 @@
+"""Frozen value contracts shared by the standard-library test orchestrator."""
+
+from __future__ import annotations
+
+from collections.abc import Callable, Iterable, Mapping
+from dataclasses import dataclass, fields, is_dataclass
+from enum import IntEnum, StrEnum
+from hashlib import sha256
+import json
+from pathlib import Path, PurePosixPath, PureWindowsPath
+from types import MappingProxyType
+from typing import Any, TypeAlias
+
+
+FrozenValue: TypeAlias = (
+    str | int | bool | None | tuple["FrozenValue", ...] | Mapping[str, "FrozenValue"]
+)
+FrozenMapping: TypeAlias = Mapping[str, FrozenValue]
+
+
+class ExitCode(IntEnum):
+    SUCCESS = 0
+    CONFIGURATION = 2
+    INTEGRITY = 3
+    PHASE = 4
+    RUNTIME = 5
+    TEST_FAILURE = 6
+    OPTIONAL_UNAVAILABLE = 7
+
+
+class TargetKind(StrEnum):
+    CURRENT_SNAPSHOT = "current_snapshot"
+    HISTORICAL_CLONE = "historical_clone"
+
+
+class ExecutionStatus(StrEnum):
+    PASSED = "passed"
+    TEST_FAILURE = "test_failure"
+    CONFIGURATION_FAILURE = "configuration_failure"
+    INTEGRITY_FAILURE = "integrity_failure"
+    PHASE_FAILURE = "phase_failure"
+    RUNTIME_SAFETY_STOP = "runtime_safety_stop"
+    CANCELLED = "cancelled"
+    NOT_RUN_SAFETY_STOP = "not_run_safety_stop"
+    OPTIONAL_UNAVAILABLE = "optional_unavailable"
+
+
+def _require_string(value: object, name: str) -> str:
+    if type(value) is not str or not value:
+        raise ValueError(f"{name} must be a non-empty string")
+    return value
+
+
+def _require_optional_string(value: object, name: str) -> str | None:
+    if value is None:
+        return None
+    return _require_string(value, name)
+
+
+def _require_int(value: object, name: str, *, positive: bool = False) -> int:
+    if type(value) is not int or value < (1 if positive else 0):
+        qualifier = "positive" if positive else "non-negative"
+        raise ValueError(f"{name} must be a {qualifier} integer")
+    return value
+
+
+def _require_bool(value: object, name: str) -> bool:
+    if type(value) is not bool:
+        raise ValueError(f"{name} must be a boolean")
+    return value
+
+
+def _require_sha256(value: object, name: str, *, optional: bool = False) -> str | None:
+    if optional and value is None:
+        return None
+    text = _require_string(value, name)
+    if len(text) != 64 or any(character not in "0123456789abcdef" for character in text):
+        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
+    return text
+
+
+def _require_git_oid(value: object, name: str) -> str:
+    text = _require_string(value, name)
+    if len(text) != 40 or any(character not in "0123456789abcdef" for character in text):
+        raise ValueError(f"{name} must be a lowercase Git object identity")
+    return text
+
+
+def _normalise_relative_path(value: object, name: str) -> str:
+    text = _require_string(value, name)
+    if PureWindowsPath(text).drive or text.startswith(("/", "\\")):
+        raise ValueError(f"{name} must be repository-relative")
+    candidate = PurePosixPath(text.replace("\\", "/"))
+    if candidate.is_absolute() or any(part in ("", ".", "..") for part in candidate.parts):
+        raise ValueError(f"{name} must be normalized below the repository root")
+    normalised = candidate.as_posix()
+    if normalised in ("", "."):
+        raise ValueError(f"{name} must name a path")
+    return normalised
+
+
+def _normalise_probe_id(value: object, name: str) -> str:
+    text = _require_string(value, name)
+    if not text.startswith("probe:") or text.count(":") != 1:
+        raise ValueError(f"{name} must use the probe:<name> form")
+    probe_name = text.removeprefix("probe:")
+    if (
+        not probe_name
+        or probe_name != probe_name.lower()
+        or not probe_name[0].isalnum()
+        or not probe_name[-1].isalnum()
+        or any(
+            not character.isascii()
+            or (not character.isalnum() and character not in "-_")
+            for character in probe_name
+        )
+    ):
+        raise ValueError(f"{name} contains an invalid probe name")
+    return text
+
+
+def _require_absolute_path(value: object, name: str) -> str:
+    text = _require_string(value, name)
+    windows = PureWindowsPath(text)
+    posix = PurePosixPath(text)
+    if not windows.is_absolute() and not posix.is_absolute():
+        raise ValueError(f"{name} must be absolute")
+    return text
+
+
+def _freeze_value(value: object, name: str) -> Any:
+    if value is None or type(value) in (str, int, bool):
+        return value
+    if isinstance(value, StrEnum):
+        return value
+    if isinstance(value, Mapping):
+        items: list[tuple[str, Any]] = []
+        for key, nested in value.items():
+            if type(key) is not str or not key:
+                raise ValueError(f"{name} mapping keys must be non-empty strings")
+            items.append((key, _freeze_value(nested, f"{name}.{key}")))
+        return MappingProxyType(dict(sorted(items)))
+    if isinstance(value, (tuple, list)):
+        return tuple(_freeze_value(item, name) for item in value)
+    if is_dataclass(value) or isinstance(value, (Path, PurePosixPath)):
+        return value
+    raise ValueError(f"{name} contains an unsupported value")
+
+
+def _semantic_value(value: object) -> object:
+    if value is None or type(value) in (str, int, bool):
+        return value
+    if isinstance(value, (IntEnum, StrEnum)):
+        return value.value
+    if isinstance(value, (Path, PurePosixPath)):
+        return value.as_posix()
+    if is_dataclass(value):
+        return {field.name: _semantic_value(getattr(value, field.name)) for field in fields(value)}
+    if isinstance(value, Mapping):
+        if not all(type(key) is str for key in value):
+            raise ValueError("semantic mappings require string keys")
+        return {key: _semantic_value(value[key]) for key in sorted(value)}
+    if isinstance(value, (tuple, list)):
+        return [_semantic_value(item) for item in value]
+    raise ValueError("semantic value has an unsupported type")
+
+
+def canonical_semantic_bytes(value: object) -> bytes:
+    return json.dumps(
+        _semantic_value(value), allow_nan=False, ensure_ascii=True,
+        separators=(",", ":"), sort_keys=True,
+    ).encode("ascii")
+
+
+def semantic_sha256(value: object) -> str:
+    return sha256(canonical_semantic_bytes(value)).hexdigest()
+
+
+def _sort_key(value: object) -> bytes:
+    return canonical_semantic_bytes(value)
+
+
+def _normalise_tuple(
+    value: object,
+    name: str,
+    normaliser: Any = None,
+    *,
+    sort: bool = True,
+    unique: bool = True,
+    sort_key: Callable[[Any], object] | None = None,
+) -> tuple[Any, ...]:
+    if isinstance(value, (str, bytes, bytearray, Mapping)) or not isinstance(value, Iterable):
+        raise ValueError(f"{name} must be a collection")
+    convert = normaliser if normaliser is not None else (lambda item, _: _freeze_value(item, name))
+    items = tuple(convert(item, name) for item in value)
+    keys = tuple(_sort_key(item) for item in items)
+    if unique and len(set(keys)) != len(keys):
+        raise ValueError(f"{name} must not contain duplicates")
+    if sort:
+        order_keys = tuple(
+            _sort_key(sort_key(item) if sort_key is not None else item)
+            for item in items
+        )
+        return tuple(
+            item
+            for _, _, item in sorted(
+                zip(order_keys, keys, items), key=lambda row: (row[0], row[1])
+            )
+        )
+    return items
+
+
+def _string_item(value: object, name: str) -> str:
+    return _require_string(value, name)
+
+
+def _path_item(value: object, name: str) -> str:
+    return _normalise_relative_path(value, name)
+
+
+def _model_item(expected_type: type[Any]) -> Any:
+    def validate(value: object, name: str) -> object:
+        if not isinstance(value, expected_type):
+            raise ValueError(f"{name} values must be {expected_type.__name__}")
+        return value
+    return validate
+
+
+def _index_unique(
+    values: Iterable[Any], name: str, key: Callable[[Any], object],
+) -> dict[object, Any]:
+    indexed: dict[object, Any] = {}
+    for item in values:
+        identity = key(item)
+        if identity in indexed:
+            raise ValueError(f"{name} must be unique by semantic identity")
+        indexed[identity] = item
+    return indexed
+
+
+def _freeze_mapping(value: object, name: str) -> MappingProxyType:
+    frozen = _freeze_value(value, name)
+    if not isinstance(frozen, MappingProxyType):
+        raise ValueError(f"{name} must be a mapping")
+    return frozen
+
+
+def _freeze_count_mapping(value: object, name: str) -> MappingProxyType:
+    frozen = _freeze_mapping(value, name)
+    for key, count in frozen.items():
+        _require_int(count, f"{name}.{key}")
+    return frozen
+
+
+def _enum(value: object, enum_type: type[Any], name: str) -> Any:
+    try:
+        return enum_type(value)
+    except (TypeError, ValueError) as error:
+        raise ValueError(f"{name} has an unsupported value") from error
+
+
+@dataclass(frozen=True, slots=True)
+class StageBudgets:
+    setup_ns: int
+    child_ns: int
+    termination_grace_ns: int
+    cleanup_ns: int
+    total_ns: int
+
+    def __post_init__(self) -> None:
+        for name in ("setup_ns", "child_ns", "termination_grace_ns", "cleanup_ns", "total_ns"):
+            _require_int(getattr(self, name), name, positive=True)
+        reserved = self.setup_ns + self.child_ns + self.termination_grace_ns + self.cleanup_ns
+        if self.total_ns < reserved:
+            raise ValueError("total_ns must reserve every stage budget")
+
+
+@dataclass(frozen=True, slots=True)
+class StableSelector:
+    stable_id: str
+    relative_path: PurePosixPath
+    case_name: str
+    method_name: str
+
+    def __post_init__(self) -> None:
+        _require_string(self.stable_id, "stable_id")
+        path = PurePosixPath(_normalise_relative_path(self.relative_path.as_posix(), "relative_path"))
+        if not path.parts or path.parts[0] != "tests" or path.suffix != ".py":
+            raise ValueError("relative_path must name a Python file below tests")
+        object.__setattr__(self, "relative_path", path)
+        if not _require_string(self.case_name, "case_name").isidentifier():
+            raise ValueError("case_name must be a Python identifier")
+        method = _require_string(self.method_name, "method_name")
+        if not method.isidentifier() or not method.startswith("test_"):
+            raise ValueError("method_name must be a test_ Python identifier")
+        expected = f"{path.as_posix()}::{self.case_name}::{method}"
+        if self.stable_id != expected:
+            raise ValueError("stable_id fields do not agree")
+
+
+@dataclass(frozen=True, slots=True)
+class InterpreterIdentity:
+    executable: str
+    resolved_executable: str
+    platform_identity: str
+    executable_sha256: str
+    implementation: str
+    version: tuple[int, int, int, str, int]
+    prefix: str
+    base_prefix: str
+    no_user_site: bool
+    safe_path: bool
+    dont_write_bytecode: bool
+    distributions_sha256: str
+    dependency_lock_sha256: str | None
+
+    def __post_init__(self) -> None:
+        for name in ("executable", "resolved_executable", "prefix", "base_prefix"):
+            _require_absolute_path(getattr(self, name), name)
+        _require_string(self.platform_identity, "platform_identity")
+        for name in ("executable_sha256", "distributions_sha256"):
+            _require_sha256(getattr(self, name), name)
+        _require_sha256(self.dependency_lock_sha256, "dependency_lock_sha256", optional=True)
+        _require_string(self.implementation, "implementation")
+        version = _normalise_tuple(self.version, "version", sort=False, unique=False)
+        if len(version) != 5:
+            raise ValueError("version must contain major, minor, micro, release level, and serial")
+        for index in (0, 1, 2, 4):
+            _require_int(version[index], f"version[{index}]")
+        if type(version[3]) is not str or version[3] not in ("alpha", "beta", "candidate", "final"):
+            raise ValueError("version release level is unsupported")
+        object.__setattr__(self, "version", version)
+        for name in ("no_user_site", "safe_path", "dont_write_bytecode"):
+            _require_bool(getattr(self, name), name)
+
+
+@dataclass(frozen=True, slots=True)
+class InterpreterBinding:
+    slot_name: str
+    identity: InterpreterIdentity
+
+    def __post_init__(self) -> None:
+        _require_string(self.slot_name, "slot_name")
+        if not isinstance(self.identity, InterpreterIdentity):
+            raise ValueError("identity must be an InterpreterIdentity")
+
+
+@dataclass(frozen=True, slots=True)
+class TargetIdentity:
+    kind: TargetKind
+    root: str
+    head_commit: str
+    root_tree_oid: str
+    file_inventory_sha256: str
+
+    def __post_init__(self) -> None:
+        object.__setattr__(self, "kind", _enum(self.kind, TargetKind, "kind"))
+        _require_absolute_path(self.root, "root")
+        _require_git_oid(self.head_commit, "head_commit")
+        _require_git_oid(self.root_tree_oid, "root_tree_oid")
+        _require_sha256(self.file_inventory_sha256, "file_inventory_sha256")
+
+
+@dataclass(frozen=True, slots=True)
+class PrimaryRootIdentity:
+    resolved_path: str
+    platform_identity: str
+    capture_sha256: str
+
+    def __post_init__(self) -> None:
+        _require_absolute_path(self.resolved_path, "resolved_path")
+        _require_string(self.platform_identity, "platform_identity")
+        _require_sha256(self.capture_sha256, "capture_sha256")
+
+
+@dataclass(frozen=True, slots=True)
+class GitToolIdentity:
+    executable: str
+    resolved_executable: str
+    platform_identity: str
+    executable_sha256: str
+
+    def __post_init__(self) -> None:
+        _require_absolute_path(self.executable, "executable")
+        _require_absolute_path(self.resolved_executable, "resolved_executable")
+        _require_string(self.platform_identity, "platform_identity")
+        _require_sha256(self.executable_sha256, "executable_sha256")
+
+
+@dataclass(frozen=True, slots=True)
+class InterpreterSlot:
+    name: str
+    resolution: str
+    windows_relative_path: str | None
+    posix_relative_path: str | None
+    environment_variable: str | None
+    implementation: str
+    minimum_version: tuple[int, int] | None
+    exact_version: tuple[int, int] | None
+    required_for_full: bool
+
+    def __post_init__(self) -> None:
+        _require_string(self.name, "name")
+        _require_string(self.implementation, "implementation")
+        _require_bool(self.required_for_full, "required_for_full")
+        if self.resolution not in ("repository_relative", "environment_absolute"):
+            raise ValueError("resolution must be repository_relative or environment_absolute")
+        for name in ("windows_relative_path", "posix_relative_path"):
+            value = getattr(self, name)
+            if value is not None:
+                object.__setattr__(self, name, _normalise_relative_path(value, name))
+        _require_optional_string(self.environment_variable, "environment_variable")
+        for name in ("minimum_version", "exact_version"):
+            value = getattr(self, name)
+            if value is not None:
+                pair = _normalise_tuple(value, name, lambda item, label: _require_int(item, label), sort=False)
+                if len(pair) != 2:
+                    raise ValueError(f"{name} must contain exactly major and minor")
+                object.__setattr__(self, name, pair)
+        if self.resolution == "repository_relative":
+            if None in (self.windows_relative_path, self.posix_relative_path, self.minimum_version):
+                raise ValueError("repository_relative slots require both paths and minimum_version")
+            if self.environment_variable is not None or self.exact_version is not None:
+                raise ValueError("repository_relative slots cannot declare environment/exact values")
+        else:
+            if self.environment_variable is None or self.exact_version is None:
+                raise ValueError("environment_absolute slots require environment_variable and exact_version")
+            if self.windows_relative_path is not None or self.posix_relative_path is not None or self.minimum_version is not None:
+                raise ValueError("environment_absolute slots cannot declare repository-relative values")
+
+
+@dataclass(frozen=True, slots=True)
+class FixtureSpec:
+    relative_path: str
+    path_kind: str
+    byte_length: int
+    raw_sha256: str
+
+    def __post_init__(self) -> None:
+        object.__setattr__(self, "relative_path", _normalise_relative_path(self.relative_path, "relative_path"))
+        _require_string(self.path_kind, "path_kind")
+        _require_int(self.byte_length, "byte_length")
+        _require_sha256(self.raw_sha256, "raw_sha256")
+
+
+@dataclass(frozen=True, slots=True)
+class ProfilePlan:
+    name: str
+    interpreter_slots: tuple[str, ...]
+    default_interpreter_slot: str | None
+    payload_ids: tuple[str, ...]
+    historical_case_ids: tuple[str, ...]
+    subprofiles: tuple[str, ...]
+    budgets: StageBudgets
+    fixture_specs: tuple[FixtureSpec, ...]
+    gpu_optional: bool
+    definition_sha256: str
+
+    def __post_init__(self) -> None:
+        _require_string(self.name, "name")
+        for name in ("interpreter_slots", "payload_ids", "historical_case_ids", "subprofiles"):
+            object.__setattr__(self, name, _normalise_tuple(getattr(self, name), name, _string_item))
+        _require_optional_string(self.default_interpreter_slot, "default_interpreter_slot")
+        if self.default_interpreter_slot is not None and self.default_interpreter_slot not in self.interpreter_slots:
+            raise ValueError("default_interpreter_slot must belong to interpreter_slots")
+        if self.name == "full":
+            if self.default_interpreter_slot is not None or self.payload_ids or self.historical_case_ids or not self.subprofiles:
+                raise ValueError("full requires only subprofiles and no direct default or selectors")
+        elif self.default_interpreter_slot is None or self.subprofiles or not (self.payload_ids or self.historical_case_ids):
+            raise ValueError("direct profiles require a default, direct selectors, and no subprofiles")
+        if not isinstance(self.budgets, StageBudgets):
+            raise ValueError("budgets must be StageBudgets")
+        object.__setattr__(self, "fixture_specs", _normalise_tuple(
+            self.fixture_specs, "fixture_specs", _model_item(FixtureSpec),
+            sort_key=lambda item: item.relative_path,
+        ))
+        _require_bool(self.gpu_optional, "gpu_optional")
+        _require_sha256(self.definition_sha256, "definition_sha256")
+
+
+@dataclass(frozen=True, slots=True)
+class InventoryExpectation:
+    kind: str
+    applicable_platforms: tuple[str, ...]
+    skip_safe_reason_code: str | None
+
+    def __post_init__(self) -> None:
+        if self.kind not in ("pass", "platform_conditioned", "case_defined"):
+            raise ValueError("inventory expectation kind is unsupported")
+        object.__setattr__(self, "applicable_platforms", _normalise_tuple(self.applicable_platforms, "applicable_platforms", _string_item))
+        _require_optional_string(self.skip_safe_reason_code, "skip_safe_reason_code")
+        if self.kind == "platform_conditioned":
+            if not self.applicable_platforms or set(self.applicable_platforms) - {"windows", "posix"} or self.skip_safe_reason_code is None:
+                raise ValueError("platform_conditioned expectations require platforms and a reason")
+        elif self.applicable_platforms or self.skip_safe_reason_code is not None:
+            raise ValueError("only platform_conditioned expectations carry platform fields")
+
+
+@dataclass(frozen=True, slots=True)
+class ResolvedInventoryItem:
+    selector: StableSelector
+    expectation: InventoryExpectation
+
+    def __post_init__(self) -> None:
+        if not isinstance(self.selector, StableSelector) or not isinstance(self.expectation, InventoryExpectation):
+            raise ValueError("resolved inventory item has invalid nested values")
+
+
+@dataclass(frozen=True, slots=True)
+class InventoryEntry:
+    selector: StableSelector
+    profile_name: str | None
+    payload_id: str | None
+    expectation: InventoryExpectation | None
+    exclusion_reason: str | None
+    exclusion_owner: str | None
+    exclusion_milestone: str | None
+
+    def __post_init__(self) -> None:
+        if not isinstance(self.selector, StableSelector):
+            raise ValueError("selector must be StableSelector")
+        for name in (
+            "profile_name", "payload_id", "exclusion_reason", "exclusion_owner",
+            "exclusion_milestone",
+        ):
+            _require_optional_string(getattr(self, name), name)
+        if self.expectation is not None and not isinstance(self.expectation, InventoryExpectation):
+            raise ValueError("expectation must be InventoryExpectation or null")
+        assignment = (self.profile_name, self.payload_id, self.expectation)
+        exclusion = (self.exclusion_reason, self.exclusion_owner, self.exclusion_milestone)
+        assignment_complete = all(value is not None for value in assignment)
+        exclusion_complete = all(value is not None for value in exclusion)
+        if assignment_complete == exclusion_complete:
+            raise ValueError("inventory entry requires exactly one complete assignment or exclusion")
+        if not assignment_complete and any(value is not None for value in assignment):
+            raise ValueError("inventory assignment fields must be all present or all null")
+        if not exclusion_complete and any(value is not None for value in exclusion):
+            raise ValueError("inventory exclusion fields must be all present or all null")
+
+
+@dataclass(frozen=True, slots=True)
+class LifecycleFixturePlan:
+    fixture_id: str
+    kind: str
+    relative_path: str
+    class_name: str | None
+    member_ids: tuple[str, ...]
+    allowed_write_roots: tuple[str, ...]
+    forbidden_relative_paths: tuple[str, ...]
+    serialized: bool
+
+    def __post_init__(self) -> None:
+        _require_string(self.fixture_id, "fixture_id")
+        if self.kind not in ("module", "class"):
+            raise ValueError("lifecycle fixture kind must be module or class")
+        object.__setattr__(self, "relative_path", _normalise_relative_path(self.relative_path, "relative_path"))
+        _require_optional_string(self.class_name, "class_name")
+        if (self.kind == "class") != (self.class_name is not None):
+            raise ValueError("class_name must be present exactly for class fixtures")
+        object.__setattr__(self, "member_ids", _normalise_tuple(self.member_ids, "member_ids", _string_item))
+        object.__setattr__(self, "allowed_write_roots", _normalise_tuple(self.allowed_write_roots, "allowed_write_roots", _string_item))
+        object.__setattr__(self, "forbidden_relative_paths", _normalise_tuple(self.forbidden_relative_paths, "forbidden_relative_paths", _path_item))
+        _require_bool(self.serialized, "serialized")
+
+
+@dataclass(frozen=True, slots=True)
+class PayloadPlan:
+    payload_id: str
+    profile_name: str
+    target_kind: TargetKind
+    allowed_interpreter_slots: tuple[str, ...]
+    inventory_items: tuple[ResolvedInventoryItem, ...]
+    probe_ids: tuple[str, ...]
+    lifecycle_fixtures: tuple[LifecycleFixturePlan, ...]
+    environment_additions: FrozenMapping
+    environment_removals: tuple[str, ...]
+    allowed_write_roots: tuple[str, ...]
+    forbidden_relative_paths: tuple[str, ...]
+    fixture_specs: tuple[FixtureSpec, ...]
+    serialized: bool
+
+    def __post_init__(self) -> None:
+        _require_string(self.payload_id, "payload_id")
+        _require_string(self.profile_name, "profile_name")
+        object.__setattr__(self, "target_kind", _enum(self.target_kind, TargetKind, "target_kind"))
+        object.__setattr__(self, "allowed_interpreter_slots", _normalise_tuple(self.allowed_interpreter_slots, "allowed_interpreter_slots", _string_item))
+        object.__setattr__(self, "inventory_items", _normalise_tuple(
+            self.inventory_items, "inventory_items", _model_item(ResolvedInventoryItem),
+            sort_key=lambda item: item.selector.stable_id,
+        ))
+        object.__setattr__(self, "probe_ids", _normalise_tuple(
+            self.probe_ids, "probe_ids", _normalise_probe_id,
+        ))
+        object.__setattr__(self, "lifecycle_fixtures", _normalise_tuple(
+            self.lifecycle_fixtures, "lifecycle_fixtures", _model_item(LifecycleFixturePlan),
+            sort_key=lambda item: item.fixture_id,
+        ))
+        additions = _freeze_mapping(self.environment_additions, "environment_additions")
+        if any(type(value) is not str for value in additions.values()):
+            raise ValueError("environment_additions values must be strings")
+        object.__setattr__(self, "environment_additions", additions)
+        for name in ("environment_removals", "allowed_write_roots"):
+            object.__setattr__(self, name, _normalise_tuple(getattr(self, name), name, _string_item))
+        object.__setattr__(self, "forbidden_relative_paths", _normalise_tuple(self.forbidden_relative_paths, "forbidden_relative_paths", _path_item))
+        object.__setattr__(self, "fixture_specs", _normalise_tuple(
+            self.fixture_specs, "fixture_specs", _model_item(FixtureSpec),
+            sort_key=lambda item: item.relative_path,
+        ))
+        _require_bool(self.serialized, "serialized")
+
+
+@dataclass(frozen=True, slots=True)
+class HistoricalItemExpectation:
+    item_id: str
+    outcome: str
+    phase: str | None
+    exception_type: str | None
+    safe_reason_code: str | None
+    body_entered: bool | None
+    capability_counters: FrozenMapping
+
+    def __post_init__(self) -> None:
+        _require_string(self.item_id, "item_id")
+        if self.outcome not in ("pass", "expected_negative"):
+            raise ValueError("historical outcome must be pass or expected_negative")
+        for name in ("phase", "exception_type", "safe_reason_code"):
+            _require_optional_string(getattr(self, name), name)
+        if self.body_entered is not None:
+            _require_bool(self.body_entered, "body_entered")
+        object.__setattr__(self, "capability_counters", _freeze_count_mapping(self.capability_counters, "capability_counters"))
+        negative_fields = (self.phase, self.exception_type, self.safe_reason_code, self.body_entered)
+        if self.outcome == "expected_negative" and any(value is None for value in negative_fields):
+            raise ValueError("expected_negative requires complete failure fields")
+        if self.outcome == "pass" and any(value is not None for value in negative_fields):
+            raise ValueError("pass expectations cannot carry failure fields")
+
+
+@dataclass(frozen=True, slots=True)
+class HistoricalSnapshotExpectation:
+    phase: str
+    commit: str
+    root_tree_oid: str
+    governing_decision: str
+
+    def __post_init__(self) -> None:
+        _require_string(self.phase, "phase")
+        _require_git_oid(self.commit, "commit")
+        _require_git_oid(self.root_tree_oid, "root_tree_oid")
+        _require_string(self.governing_decision, "governing_decision")
+
+
+@dataclass(frozen=True, slots=True)
+class HistoricalBlobExpectation:
+    commit: str
+    relative_path: str
+    git_blob_oid: str
+    raw_sha256: str
+    role: str
+    phase: str
+    governing_decision: str
+
+    def __post_init__(self) -> None:
+        _require_git_oid(self.commit, "commit")
+        object.__setattr__(self, "relative_path", _normalise_relative_path(self.relative_path, "relative_path"))
+        _require_git_oid(self.git_blob_oid, "git_blob_oid")
+        _require_sha256(self.raw_sha256, "raw_sha256")
+        for name in ("role", "phase", "governing_decision"):
+            _require_string(getattr(self, name), name)
+
+
+@dataclass(frozen=True, slots=True)
+class HistoricalCase:
+    case_id: str
+    phase: str
+    commit: str
+    root_tree_oid: str
+    payload_ids: tuple[str, ...]
+    expected_vector: FrozenMapping
+    item_expectations: tuple[HistoricalItemExpectation, ...]
+    overlay_ids: tuple[str, ...]
+
+    def __post_init__(self) -> None:
+        for name in ("case_id", "phase"):
+            _require_string(getattr(self, name), name)
+        _require_git_oid(self.commit, "commit")
+        _require_git_oid(self.root_tree_oid, "root_tree_oid")
+        object.__setattr__(self, "payload_ids", _normalise_tuple(self.payload_ids, "payload_ids", _string_item))
+        if not self.payload_ids:
+            raise ValueError("historical case payload_ids must not be empty")
+        vector = _freeze_mapping(self.expected_vector, "expected_vector")
+        kind = vector.get("kind")
+        positive_fields = {
+            "kind", "passed", "assertion_failed", "setup_failed", "body_entered",
+            "owner_calls", "scientific_calls",
+        }
+        negative_fields = positive_fields | {"phase", "exception_type", "safe_reason_code"}
+        expected_fields = positive_fields if kind == "positive" else negative_fields if kind == "negative" else None
+        if expected_fields is None or set(vector) != expected_fields:
+            raise ValueError("expected_vector must be an exact positive or negative variant")
+        for name in positive_fields - {"kind"}:
+            _require_int(vector[name], f"expected_vector.{name}")
+        if kind == "negative":
+            for name in ("phase", "exception_type", "safe_reason_code"):
+                _require_string(vector[name], f"expected_vector.{name}")
+        object.__setattr__(self, "expected_vector", vector)
+        object.__setattr__(self, "item_expectations", _normalise_tuple(
+            self.item_expectations, "item_expectations", _model_item(HistoricalItemExpectation),
+            sort_key=lambda item: item.item_id,
+        ))
+        object.__setattr__(self, "overlay_ids", _normalise_tuple(self.overlay_ids, "overlay_ids", _string_item))
+
+
+@dataclass(frozen=True, slots=True)
+class OverlaySpec:
+    overlay_id: str
+    source_commit: str
+    source_path: str
+    destination_path: str
+    byte_length: int
+    raw_sha256: str
+
+    def __post_init__(self) -> None:
+        _require_string(self.overlay_id, "overlay_id")
+        _require_git_oid(self.source_commit, "source_commit")
+        for name in ("source_path", "destination_path"):
+            object.__setattr__(self, name, _normalise_relative_path(getattr(self, name), name))
+        _require_int(self.byte_length, "byte_length")
+        _require_sha256(self.raw_sha256, "raw_sha256")
+
+
+@dataclass(frozen=True, slots=True)
+class SubprocessCapability:
+    capability_id: str
+    executable_role: str
+    executable_slot: str
+    executable_constraints: FrozenMapping
+    argv: tuple[str, ...]
+    argv_template: tuple[str, ...]
+    dynamic_program_sha256: str | None
+    cwd_class: str
+    environment_additions: FrozenMapping
+    environment_removals: tuple[str, ...]
+    timeout_ns: int
+    expected_return_category: str
+    read_roots: tuple[str, ...]
+    write_roots: tuple[str, ...]
+    fixed_descendant_permission: bool
+
+    def __post_init__(self) -> None:
+        for name in ("capability_id", "cwd_class", "expected_return_category"):
+            _require_string(getattr(self, name), name)
+        if self.executable_role not in ("python", "git"):
+            raise ValueError("executable_role must be python or git")
+        if self.executable_slot not in ("active_worker", "development", "cpython311", "git"):
+            raise ValueError("executable_slot is unsupported")
+        if (self.executable_role == "git") != (self.executable_slot == "git"):
+            raise ValueError("executable role and slot disagree")
+        object.__setattr__(self, "executable_constraints", _freeze_mapping(self.executable_constraints, "executable_constraints"))
+        object.__setattr__(self, "argv", _normalise_tuple(self.argv, "argv", _string_item, sort=False, unique=False))
+        object.__setattr__(self, "argv_template", _normalise_tuple(self.argv_template, "argv_template", _string_item, sort=False, unique=False))
+        if bool(self.argv) == bool(self.argv_template):
+            raise ValueError("exactly one of argv and argv_template must be nonempty")
+        _require_sha256(self.dynamic_program_sha256, "dynamic_program_sha256", optional=True)
+        additions = _freeze_mapping(self.environment_additions, "environment_additions")
+        if any(type(value) is not str for value in additions.values()):
+            raise ValueError("environment_additions values must be strings")
+        object.__setattr__(self, "environment_additions", additions)
+        for name in ("environment_removals", "read_roots", "write_roots"):
+            object.__setattr__(self, name, _normalise_tuple(getattr(self, name), name, _string_item))
+        _require_int(self.timeout_ns, "timeout_ns", positive=True)
+        _require_bool(self.fixed_descendant_permission, "fixed_descendant_permission")
+
+
+@dataclass(frozen=True, slots=True)
+class CallCapability:
+    capability_id: str
+    kind: str
+    module_name: str
+    qualified_name: str
+    action: str
+    maximum_calls: int
+    return_contract: str
+
+    def __post_init__(self) -> None:
+        for name in ("capability_id", "module_name", "qualified_name", "action"):
+            _require_string(getattr(self, name), name)
+        if self.kind not in ("owner", "scientific", "cuda_query", "cuda_allocation"):
+            raise ValueError("call capability kind is unsupported")
+        _require_int(self.maximum_calls, "maximum_calls", positive=True)
+        _require_string(self.return_contract, "return_contract")
+
+
+@dataclass(frozen=True, slots=True)
+class CapabilityBinding:
+    item_id: str
+    approval_scope: str
+    capability_kind: str
+    capability_id: str
+
+    def __post_init__(self) -> None:
+        for name in ("item_id", "capability_id"):
+            _require_string(getattr(self, name), name)
+        if self.approval_scope not in ("design", "historical_review"):
+            raise ValueError("approval_scope is unsupported")
+        if self.capability_kind not in ("subprocess", "call"):
+            raise ValueError("capability_kind is unsupported")
+
+
+def _normalise_capability_bindings(value: object) -> tuple[CapabilityBinding, ...]:
+    bindings = _normalise_tuple(
+        value, "capability_bindings", _model_item(CapabilityBinding), sort=False
+    )
+    return tuple(sorted(
+        bindings,
+        key=lambda item: (
+            item.approval_scope, item.item_id, item.capability_kind, item.capability_id,
+        ),
+    ))
+
+
+@dataclass(frozen=True, slots=True)
+class EvidenceManifestIdentity:
+    relative_path: str
+    schema_version: str
+    byte_length: int
+    raw_sha256: str
+    semantic_sha256: str
+    platform_identity: str
+
+    def __post_init__(self) -> None:
+        object.__setattr__(self, "relative_path", _normalise_relative_path(self.relative_path, "relative_path"))
+        _require_string(self.schema_version, "schema_version")
+        _require_int(self.byte_length, "byte_length")
+        _require_sha256(self.raw_sha256, "raw_sha256")
+        _require_sha256(self.semantic_sha256, "semantic_sha256")
+        _require_string(self.platform_identity, "platform_identity")
+
+
+@dataclass(frozen=True, slots=True)
+class EvidenceFileExpectation:
+    relative_path: str
+    byte_length: int
+    raw_sha256: str
+    role: str
+    platform_identity: str
+
+    def __post_init__(self) -> None:
+        object.__setattr__(self, "relative_path", _normalise_relative_path(self.relative_path, "relative_path"))
+        _require_int(self.byte_length, "byte_length")
+        _require_sha256(self.raw_sha256, "raw_sha256")
+        _require_string(self.role, "role")
+        _require_string(self.platform_identity, "platform_identity")
+
+
+@dataclass(frozen=True, slots=True)
+class EvidenceAbsenceExpectation:
+    relative_path: str
+    role: str
+
+    def __post_init__(self) -> None:
+        object.__setattr__(self, "relative_path", _normalise_relative_path(self.relative_path, "relative_path"))
+        _require_string(self.role, "role")
+
+
+@dataclass(frozen=True, slots=True)
+class EvidenceGuardPlan:
+    semantic_sha256: str
+    manifest_identities: tuple[EvidenceManifestIdentity, ...]
+    present_files: tuple[EvidenceFileExpectation, ...]
+    absences: tuple[EvidenceAbsenceExpectation, ...]
+
+    def __post_init__(self) -> None:
+        for name, expected in (("manifest_identities", EvidenceManifestIdentity), ("present_files", EvidenceFileExpectation), ("absences", EvidenceAbsenceExpectation)):
+            object.__setattr__(self, name, _normalise_tuple(
+                getattr(self, name), name, _model_item(expected),
+                sort_key=lambda item: item.relative_path,
+            ))
+        if (
+            len(self.manifest_identities) != 4
+            or len(self.present_files) != 6
+            or len(self.absences) != 18
+        ):
+            raise ValueError("evidence guard requires exactly four manifests, six files, and eighteen absences")
+        path_groups = (
+            tuple(item.relative_path for item in self.manifest_identities),
+            tuple(item.relative_path for item in self.present_files),
+            tuple(item.relative_path for item in self.absences),
+        )
+        if any(len(paths) != len(set(paths)) for paths in path_groups):
+            raise ValueError("evidence guard paths must be unique within each collection")
+        if set(path_groups[1]) & set(path_groups[2]):
+            raise ValueError("present and absent evidence paths must be disjoint")
+        expected_digest = semantic_sha256({
+            "manifest_identities": self.manifest_identities,
+            "present_files": self.present_files,
+            "absences": self.absences,
+        })
+        _require_sha256(self.semantic_sha256, "semantic_sha256")
+        if self.semantic_sha256 != expected_digest:
+            raise ValueError("evidence guard semantic_sha256 does not match its canonical form")
+
+
+@dataclass(frozen=True, slots=True)
+class ObservedCondition:
+    category: str
+    code: str
+    affects_exit: bool
+    context: FrozenMapping
+
+    def __post_init__(self) -> None:
+        allowed = {"integrity", "configuration", "phase", "runtime", "test_failure", "optional_unavailable"}
+        if self.category not in allowed:
+            raise ValueError("condition category is unsupported")
+        _require_string(self.code, "code")
+        _require_bool(self.affects_exit, "affects_exit")
+        if self.category != "optional_unavailable" and not self.affects_exit:
+            raise ValueError("non-optional conditions must affect the process exit")
+        object.__setattr__(self, "context", _freeze_mapping(self.context, "context"))
+
+
+@dataclass(frozen=True, slots=True)
+class EvidenceGuardSummary:
+    before_semantic_sha256: str | None
+    after_semantic_sha256: str | None
+    status: str
+    conditions: tuple[ObservedCondition, ...]
+
+    def __post_init__(self) -> None:
+        object.__setattr__(self, "conditions", _normalise_tuple(self.conditions, "conditions", _model_item(ObservedCondition)))
+        if self.status not in ("unchanged", "changed", "not_measured"):
+            raise ValueError("evidence guard status is unsupported")
+        _require_sha256(self.before_semantic_sha256, "before_semantic_sha256", optional=True)
+        _require_sha256(self.after_semantic_sha256, "after_semantic_sha256", optional=True)
+        if self.status == "not_measured":
+            if self.before_semantic_sha256 is not None or self.after_semantic_sha256 is not None:
+                raise ValueError("not_measured requires both digests to be null")
+        elif self.before_semantic_sha256 is None or self.after_semantic_sha256 is None:
+            raise ValueError("measured guards require both digests")
+        elif (self.before_semantic_sha256 == self.after_semantic_sha256) != (self.status == "unchanged"):
+            raise ValueError("evidence guard status disagrees with measured digests")
+        if self.status == "changed" and not any(item.category == "integrity" for item in self.conditions):
+            raise ValueError("changed evidence requires an integrity condition")
+
+
+@dataclass(frozen=True, slots=True)
+class ResolvedWorkerPlan:
+    semantic_sha256: str
+    profile: ProfilePlan
+    inventory_entries: tuple[ResolvedInventoryItem, ...]
+    payloads: tuple[PayloadPlan, ...]
+    historical_cases: tuple[HistoricalCase, ...]
+    historical_snapshots: tuple[HistoricalSnapshotExpectation, ...]
+    historical_blobs: tuple[HistoricalBlobExpectation, ...]
+    overlays: tuple[OverlaySpec, ...]
+    subprocess_capabilities: tuple[SubprocessCapability, ...]
+    call_capabilities: tuple[CallCapability, ...]
+    capability_bindings: tuple[CapabilityBinding, ...]
+    spec_capabilities_sha256: str
+    capability_bindings_sha256: str
+
+    def __post_init__(self) -> None:
+        if not isinstance(self.profile, ProfilePlan):
+            raise ValueError("profile must be ProfilePlan")
+        collections = (
+            ("inventory_entries", ResolvedInventoryItem, lambda item: item.selector.stable_id),
+            ("payloads", PayloadPlan, lambda item: item.payload_id),
+            ("historical_cases", HistoricalCase, lambda item: item.case_id),
+            ("historical_snapshots", HistoricalSnapshotExpectation, lambda item: (item.phase, item.commit)),
+            ("historical_blobs", HistoricalBlobExpectation, lambda item: (item.commit, item.relative_path)),
+            ("overlays", OverlaySpec, lambda item: item.overlay_id),
+            ("subprocess_capabilities", SubprocessCapability, lambda item: item.capability_id),
+            ("call_capabilities", CallCapability, lambda item: item.capability_id),
+            ("capability_bindings", CapabilityBinding, None),
+        )
+        for name, expected, sort_key in collections:
+            object.__setattr__(self, name, _normalise_tuple(
+                getattr(self, name), name, _model_item(expected), sort_key=sort_key,
+            ))
+        for name in ("spec_capabilities_sha256", "capability_bindings_sha256"):
+            _require_sha256(getattr(self, name), name)
+        object.__setattr__(self, "capability_bindings", _normalise_capability_bindings(self.capability_bindings))
+        payloads = _index_unique(self.payloads, "payloads", lambda item: item.payload_id)
+        if set(payloads) != set(self.profile.payload_ids):
+            raise ValueError("resolved payloads must exactly match the selected profile")
+        if any(item.profile_name != self.profile.name for item in payloads.values()):
+            raise ValueError("resolved payload ownership must match the selected profile")
+
+        expected_inventory: dict[str, ResolvedInventoryItem] = {}
+        expected_fixtures: dict[str, FixtureSpec] = {}
+        known_item_ids: set[str] = set()
+        for payload in payloads.values():
+            for item in payload.inventory_items:
+                stable_id = item.selector.stable_id
+                if stable_id in expected_inventory:
+                    raise ValueError("resolved inventory ownership must be exact")
+                expected_inventory[stable_id] = item
+                known_item_ids.add(stable_id)
+            known_item_ids.update(payload.probe_ids)
+            for fixture in payload.lifecycle_fixtures:
+                if fixture.fixture_id in known_item_ids:
+                    raise ValueError("resolved item identities must be unique")
+                known_item_ids.add(fixture.fixture_id)
+            for fixture in payload.fixture_specs:
+                previous = expected_fixtures.get(fixture.relative_path)
+                if previous is not None and previous != fixture:
+                    raise ValueError("resolved fixtures contain conflicting identities")
+                expected_fixtures[fixture.relative_path] = fixture
+        actual_inventory = _index_unique(
+            self.inventory_entries, "inventory_entries",
+            lambda item: item.selector.stable_id,
+        )
+        if actual_inventory != expected_inventory:
+            raise ValueError("resolved inventory must exactly match payload ownership")
+        profile_fixtures = _index_unique(
+            self.profile.fixture_specs, "profile.fixture_specs",
+            lambda item: item.relative_path,
+        )
+        if profile_fixtures != expected_fixtures:
+            raise ValueError("resolved fixtures must exactly match the selected profile")
+
+        cases = _index_unique(
+            self.historical_cases, "historical_cases", lambda item: item.case_id,
+        )
+        if set(cases) != set(self.profile.historical_case_ids):
+            raise ValueError("resolved historical cases must exactly match the selected profile")
+        expected_overlay_ids: set[str] = set()
+        snapshot_keys: set[tuple[str, str, str]] = set()
+        case_commits: set[str] = set()
+        for case in cases.values():
+            if not set(case.payload_ids).issubset(payloads):
+                raise ValueError("historical case references an unresolved payload")
+            expected_overlay_ids.update(case.overlay_ids)
+            snapshot_keys.add((case.phase, case.commit, case.root_tree_oid))
+            case_commits.add(case.commit)
+            case_item_ids: set[str] = set()
+            for payload_id in case.payload_ids:
+                payload = payloads[payload_id]
+                case_item_ids.update(
+                    item.selector.stable_id for item in payload.inventory_items
+                )
+                case_item_ids.update(payload.probe_ids)
+                case_item_ids.update(
+                    fixture.fixture_id for fixture in payload.lifecycle_fixtures
+                )
+            if any(item.item_id not in case_item_ids for item in case.item_expectations):
+                raise ValueError("historical expectations reference unresolved items")
+        overlays = _index_unique(self.overlays, "overlays", lambda item: item.overlay_id)
+        if set(overlays) != expected_overlay_ids:
+            raise ValueError("resolved overlays must exactly match historical cases")
+        snapshots = _index_unique(
+            self.historical_snapshots, "historical_snapshots",
+            lambda item: (item.phase, item.commit, item.root_tree_oid),
+        )
+        if set(snapshots) != snapshot_keys:
+            raise ValueError("resolved snapshots must exactly match historical cases")
+        blobs = _index_unique(
+            self.historical_blobs, "historical_blobs",
+            lambda item: (item.commit, item.relative_path),
+        )
+        blob_commits = {item.commit for item in blobs.values()}
+        if blob_commits - case_commits or (case_commits and blob_commits != case_commits):
+            raise ValueError("resolved blobs must cover only and every historical commit")
+
+        subprocess_capabilities = _index_unique(
+            self.subprocess_capabilities, "subprocess_capabilities",
+            lambda item: item.capability_id,
+        )
+        call_capabilities = _index_unique(
+            self.call_capabilities, "call_capabilities",
+            lambda item: item.capability_id,
+        )
+        referenced_subprocess: set[str] = set()
+        referenced_calls: set[str] = set()
+        for binding in self.capability_bindings:
+            if binding.item_id not in known_item_ids:
+                raise ValueError("capability binding references an unresolved item")
+            if binding.capability_kind == "subprocess":
+                referenced_subprocess.add(binding.capability_id)
+            else:
+                referenced_calls.add(binding.capability_id)
+        if set(subprocess_capabilities) != referenced_subprocess:
+            raise ValueError("resolved subprocess definitions must exactly match bindings")
+        if set(call_capabilities) != referenced_calls:
+            raise ValueError("resolved call definitions must exactly match bindings")
+        _require_sha256(self.semantic_sha256, "semantic_sha256")
+        payload = {field.name: getattr(self, field.name) for field in fields(self) if field.name != "semantic_sha256"}
+        if self.semantic_sha256 != semantic_sha256(payload):
+            raise ValueError("resolved plan semantic_sha256 does not match its canonical form")
+
+
+@dataclass(frozen=True, slots=True)
+class ExecutionBundle:
+    configuration: ConfigurationBundle
+    evidence_guard_plan: EvidenceGuardPlan
+    historical_snapshots: tuple[HistoricalSnapshotExpectation, ...]
+    historical_blobs: tuple[HistoricalBlobExpectation, ...]
+    semantic_sha256: str
+
+    def __post_init__(self) -> None:
+        if not isinstance(self.configuration, ConfigurationBundle):
+            raise ValueError("configuration must be ConfigurationBundle")
+        if not isinstance(self.evidence_guard_plan, EvidenceGuardPlan):
+            raise ValueError("evidence_guard_plan must be EvidenceGuardPlan")
+        object.__setattr__(self, "historical_snapshots", _normalise_tuple(
+            self.historical_snapshots, "historical_snapshots",
+            _model_item(HistoricalSnapshotExpectation),
+            sort_key=lambda item: (item.phase, item.commit),
+        ))
+        object.__setattr__(self, "historical_blobs", _normalise_tuple(
+            self.historical_blobs, "historical_blobs",
+            _model_item(HistoricalBlobExpectation),
+            sort_key=lambda item: (item.commit, item.relative_path),
+        ))
+        _require_sha256(self.semantic_sha256, "semantic_sha256")
+        payload = {field.name: getattr(self, field.name) for field in fields(self) if field.name != "semantic_sha256"}
+        if self.semantic_sha256 != semantic_sha256(payload):
+            raise ValueError("execution bundle semantic_sha256 does not match its canonical form")
+
+
+@dataclass(frozen=True, slots=True)
+class CapturedStreamIdentity:
+    byte_length: int
+    raw_sha256: str
+    truncated: bool
+
+    def __post_init__(self) -> None:
+        _require_int(self.byte_length, "byte_length")
+        _require_sha256(self.raw_sha256, "raw_sha256")
+        _require_bool(self.truncated, "truncated")
+
+
+@dataclass(frozen=True, slots=True)
+class CapturedOutputIdentity:
+    stdout: CapturedStreamIdentity
+    stderr: CapturedStreamIdentity
+
+    def __post_init__(self) -> None:
+        if not isinstance(self.stdout, CapturedStreamIdentity) or not isinstance(self.stderr, CapturedStreamIdentity):
+            raise ValueError("captured output requires stream identities")
+
+
+@dataclass(frozen=True, slots=True)
+class ChildExecutionResult:
+    report: object | None
+    process_return_category: str
+    captured_output: CapturedOutputIdentity
+    completed: bool
+
+    def __post_init__(self) -> None:
+        if self.process_return_category not in ("protocol_committed", "protocol_failure"):
+            raise ValueError("process_return_category is unsupported")
+        if not isinstance(self.captured_output, CapturedOutputIdentity):
+            raise ValueError("captured_output must be CapturedOutputIdentity")
+        _require_bool(self.completed, "completed")
+        if self.process_return_category == "protocol_committed" and self.report is None:
+            raise ValueError("protocol_committed requires a report")
+        if self.completed and self.process_return_category != "protocol_committed":
+            raise ValueError("completed child execution requires a committed protocol")
+
+
+def _normalise_status(value: object) -> ExecutionStatus:
+    return _enum(value, ExecutionStatus, "status")
+
+
+def _normalise_outcomes(value: object) -> tuple[Mapping[str, FrozenValue], ...]:
+    items = _normalise_tuple(value, "outcomes", sort=False)
+    outcomes: list[Mapping[str, FrozenValue]] = []
+    identifiers: set[str] = set()
+    for item in items:
+        if not isinstance(item, Mapping):
+            raise ValueError("outcomes must contain mappings")
+        stable_id = _require_string(item.get("stable_id"), "outcome.stable_id")
+        if stable_id in identifiers:
+            raise ValueError("outcomes must contain unique stable IDs")
+        identifiers.add(stable_id)
+        outcomes.append(item)
+    return tuple(sorted(outcomes, key=lambda item: item["stable_id"]))
+
+
+def _outcome_ids(outcomes: tuple[Mapping[str, FrozenValue], ...]) -> tuple[str, ...]:
+    return tuple(str(item["stable_id"]) for item in outcomes)
+
+
+def _failure_count(counts: Mapping[str, object]) -> int:
+    return sum(
+        int(value)
+        for key, value in counts.items()
+        if key in {"failed", "failures", "errors", "assertion_failed", "setup_failed"}
+    )
+
+
+@dataclass(frozen=True, slots=True)
+class PayloadSummary:
+    payload_id: str
+    status: ExecutionStatus
+    requested_ids: tuple[str, ...]
+    outcomes: tuple[FrozenValue, ...]
+    counts: FrozenMapping
+    conditions: tuple[ObservedCondition, ...]
+    captured_output: CapturedOutputIdentity | None
+    duration_ns: int
+    completed: bool
+
+    def __post_init__(self) -> None:
+        _require_string(self.payload_id, "payload_id")
+        object.__setattr__(self, "status", _normalise_status(self.status))
+        if self.status is ExecutionStatus.OPTIONAL_UNAVAILABLE:
+            raise ValueError("optional_unavailable is not a payload status")
+        object.__setattr__(self, "requested_ids", _normalise_tuple(self.requested_ids, "requested_ids", _string_item))
+        object.__setattr__(self, "outcomes", _normalise_outcomes(self.outcomes))
+        object.__setattr__(self, "counts", _freeze_count_mapping(self.counts, "counts"))
+        object.__setattr__(self, "conditions", _normalise_tuple(self.conditions, "conditions", _model_item(ObservedCondition)))
+        if self.captured_output is not None and not isinstance(self.captured_output, CapturedOutputIdentity):
+            raise ValueError("captured_output must be CapturedOutputIdentity or null")
+        _require_int(self.duration_ns, "duration_ns")
+        _require_bool(self.completed, "completed")
+        if self.status is ExecutionStatus.NOT_RUN_SAFETY_STOP:
+            if self.completed or self.duration_ns or self.requested_ids or self.outcomes or self.counts or self.captured_output is not None or not self.conditions:
+                raise ValueError("not_run_safety_stop must be an empty unstarted result with a condition")
+        if self.status in (ExecutionStatus.PASSED, ExecutionStatus.TEST_FAILURE):
+            if (
+                not self.completed
+                or self.requested_ids != _outcome_ids(self.outcomes)
+                or self.captured_output is None
+            ):
+                raise ValueError("completed test results require exact outcomes and captured output")
+            failures = _failure_count(self.counts)
+            if (self.status is ExecutionStatus.PASSED and failures) or (self.status is ExecutionStatus.TEST_FAILURE and failures == 0):
+                raise ValueError("test status disagrees with failure counts")
+        if self.status in (ExecutionStatus.CONFIGURATION_FAILURE, ExecutionStatus.INTEGRITY_FAILURE, ExecutionStatus.PHASE_FAILURE):
+            if self.completed or self.outcomes:
+                raise ValueError("configuration/integrity/phase failures discard outcomes")
+        if self.status in (ExecutionStatus.RUNTIME_SAFETY_STOP, ExecutionStatus.CANCELLED) and self.completed:
+            raise ValueError("active safety stops are incomplete")
+        if self.status in (ExecutionStatus.RUNTIME_SAFETY_STOP, ExecutionStatus.CANCELLED):
+            if self.captured_output is None:
+                raise ValueError("active safety stops require parent-owned captured output")
+            outcome_ids = _outcome_ids(self.outcomes)
+            if outcome_ids != self.requested_ids[:len(outcome_ids)]:
+                raise ValueError("active safety-stop outcomes must be a bounded requested prefix")
+
+
+@dataclass(frozen=True, slots=True)
+class WorkerSummary:
+    profile: str
+    interpreter_binding: InterpreterBinding
+    status: ExecutionStatus
+    summary: ProfileSummary | None
+    conditions: tuple[ObservedCondition, ...]
+    duration_ns: int
+    completed: bool
+
+    def __post_init__(self) -> None:
+        _require_string(self.profile, "profile")
+        if not isinstance(self.interpreter_binding, InterpreterBinding):
+            raise ValueError("interpreter_binding must be InterpreterBinding")
+        object.__setattr__(self, "status", _normalise_status(self.status))
+        if self.summary is not None and not isinstance(self.summary, ProfileSummary):
+            raise ValueError("summary must be ProfileSummary or null")
+        object.__setattr__(self, "conditions", _normalise_tuple(self.conditions, "conditions", _model_item(ObservedCondition)))
+        _require_int(self.duration_ns, "duration_ns")
+        _require_bool(self.completed, "completed")
+        if self.status is ExecutionStatus.NOT_RUN_SAFETY_STOP:
+            if self.completed or self.duration_ns or self.summary is not None or not self.conditions:
+                raise ValueError("not_run_safety_stop workers must be empty and carry a trigger")
+        if self.status is ExecutionStatus.OPTIONAL_UNAVAILABLE and (not self.completed or self.summary is not None or len(self.conditions) != 1 or self.conditions[0].category != "optional_unavailable"):
+            raise ValueError("optional_unavailable worker requires one optional condition and no summary")
+        if self.status in (ExecutionStatus.PASSED, ExecutionStatus.TEST_FAILURE):
+            if not self.completed or self.summary is None or not self.summary.completed:
+                raise ValueError("completed worker statuses require a direct profile summary")
+            failures = _failure_count(self.summary.counts)
+            if (self.status is ExecutionStatus.PASSED and failures) or (self.status is ExecutionStatus.TEST_FAILURE and failures == 0):
+                raise ValueError("worker status disagrees with nested failure counts")
+        if self.status in (ExecutionStatus.RUNTIME_SAFETY_STOP, ExecutionStatus.CANCELLED) and self.completed:
+            raise ValueError("active worker safety stops are incomplete")
+        if self.status in (ExecutionStatus.CONFIGURATION_FAILURE, ExecutionStatus.INTEGRITY_FAILURE, ExecutionStatus.PHASE_FAILURE) and (self.completed or self.summary is not None):
+            raise ValueError("worker configuration/integrity/phase failures discard summaries")
+        if self.summary is not None:
+            if self.summary.profile != self.profile:
+                raise ValueError("worker and nested profile identities must match")
+            if self.summary.interpreter_bindings != (self.interpreter_binding,):
+                raise ValueError("worker and nested interpreter bindings must match")
+            if self.status in (ExecutionStatus.RUNTIME_SAFETY_STOP, ExecutionStatus.CANCELLED) and self.summary.completed:
+                raise ValueError("active worker summaries must remain incomplete")
+
+
+@dataclass(frozen=True, slots=True)
+class ProfileSummary:
+    profile: str
+    profile_definition_sha256: str
+    inventory_sha256: str
+    spec_capabilities_sha256: str
+    capability_bindings_sha256: str
+    interpreter_bindings: tuple[InterpreterBinding, ...]
+    payload_summaries: tuple[PayloadSummary, ...]
+    worker_summaries: tuple[WorkerSummary, ...]
+    requested_ids: tuple[str, ...]
+    outcomes: tuple[FrozenValue, ...]
+    counts: FrozenMapping
+    conditions: tuple[ObservedCondition, ...]
+    evidence_guard_sha256: str
+    evidence_guard: EvidenceGuardSummary
+    duration_ns: int
+    completed: bool
+
+    def __post_init__(self) -> None:
+        _require_string(self.profile, "profile")
+        for name in ("profile_definition_sha256", "inventory_sha256", "spec_capabilities_sha256", "capability_bindings_sha256", "evidence_guard_sha256"):
+            _require_sha256(getattr(self, name), name)
+        object.__setattr__(self, "interpreter_bindings", _normalise_tuple(
+            self.interpreter_bindings, "interpreter_bindings", _model_item(InterpreterBinding),
+            sort_key=lambda item: item.slot_name,
+        ))
+        if len({item.slot_name for item in self.interpreter_bindings}) != len(self.interpreter_bindings):
+            raise ValueError("interpreter bindings must be unique by slot_name")
+        object.__setattr__(self, "payload_summaries", _normalise_tuple(
+            self.payload_summaries, "payload_summaries", _model_item(PayloadSummary),
+            sort_key=lambda item: item.payload_id,
+        ))
+        object.__setattr__(self, "worker_summaries", _normalise_tuple(
+            self.worker_summaries, "worker_summaries", _model_item(WorkerSummary),
+            sort_key=lambda item: (item.profile, item.interpreter_binding.slot_name),
+        ))
+        object.__setattr__(self, "requested_ids", _normalise_tuple(self.requested_ids, "requested_ids", _string_item))
+        object.__setattr__(self, "outcomes", _normalise_outcomes(self.outcomes))
+        object.__setattr__(self, "counts", _freeze_count_mapping(self.counts, "counts"))
+        object.__setattr__(self, "conditions", _normalise_tuple(self.conditions, "conditions", _model_item(ObservedCondition)))
+        if not isinstance(self.evidence_guard, EvidenceGuardSummary):
+            raise ValueError("evidence_guard must be EvidenceGuardSummary")
+        _require_int(self.duration_ns, "duration_ns")
+        _require_bool(self.completed, "completed")
+        if self.completed and self.evidence_guard.status == "not_measured":
+            raise ValueError("completed profiles require measured evidence")
+        if self.completed and self.requested_ids != _outcome_ids(self.outcomes):
+            raise ValueError("completed profile outcomes must exactly match requested IDs")
+        if self.completed and not any(item.affects_exit for item in self.conditions) and _failure_count(self.counts) == 0 and self.evidence_guard.status != "unchanged":
+            raise ValueError("successful completed profiles require unchanged evidence")
+        if self.profile == "full":
+            if self.completed and not self.worker_summaries:
+                raise ValueError("completed full profiles require worker summaries")
+            worker_bindings = tuple(worker.interpreter_binding for worker in self.worker_summaries)
+            if set(worker_bindings) != set(self.interpreter_bindings) or len(worker_bindings) != len(set(worker_bindings)):
+                raise ValueError("full bindings must equal the unique worker binding union")
+            if self.completed and any(
+                not worker.completed
+                or worker.status not in (
+                    ExecutionStatus.PASSED, ExecutionStatus.TEST_FAILURE,
+                    ExecutionStatus.OPTIONAL_UNAVAILABLE,
+                )
+                for worker in self.worker_summaries
+            ):
+                raise ValueError("completed full profiles require terminal worker rows")
+        else:
+            if self.worker_summaries:
+                raise ValueError("direct profiles cannot contain worker summaries")
+            if not self.interpreter_bindings:
+                if self.completed or self.payload_summaries:
+                    raise ValueError("pre-resolution failures cannot contain payload summaries")
+            elif len(self.interpreter_bindings) != 1:
+                raise ValueError("resolved direct profiles require exactly one interpreter binding")
+            elif not self.payload_summaries:
+                raise ValueError("resolved direct profiles require payload summaries")
+            if self.completed and any(
+                not payload.completed
+                or payload.status not in (
+                    ExecutionStatus.PASSED, ExecutionStatus.TEST_FAILURE,
+                )
+                for payload in self.payload_summaries
+            ):
+                raise ValueError("completed direct profiles require terminal payload rows")
+            if self.completed:
+                child_requested = tuple(sorted(
+                    stable_id
+                    for payload in self.payload_summaries
+                    for stable_id in payload.requested_ids
+                ))
+                if len(child_requested) != len(set(child_requested)) or self.requested_ids != child_requested:
+                    raise ValueError("direct requested IDs must equal the payload union")
+        if self.completed:
+            child_failed = any(
+                payload.status is ExecutionStatus.TEST_FAILURE
+                for payload in self.payload_summaries
+            ) or any(
+                worker.status is ExecutionStatus.TEST_FAILURE
+                for worker in self.worker_summaries
+            )
+            if child_failed != (_failure_count(self.counts) > 0):
+                raise ValueError("profile failure counts must agree with child statuses")
+
+
+@dataclass(frozen=True, slots=True)
+class RunSummary:
+    run_id: str
+    requested_profile: str
+    profile_summaries: tuple[ProfileSummary, ...]
+    conditions: tuple[ObservedCondition, ...]
+    exit_code: ExitCode
+    duration_ns: int
+    completed: bool
+
+    def __post_init__(self) -> None:
+        _require_string(self.run_id, "run_id")
+        _require_string(self.requested_profile, "requested_profile")
+        object.__setattr__(self, "profile_summaries", _normalise_tuple(
+            self.profile_summaries, "profile_summaries", _model_item(ProfileSummary),
+            sort_key=lambda item: item.profile,
+        ))
+        object.__setattr__(self, "conditions", _normalise_tuple(self.conditions, "conditions", _model_item(ObservedCondition)))
+        object.__setattr__(self, "exit_code", _enum(self.exit_code, ExitCode, "exit_code"))
+        _require_int(self.duration_ns, "duration_ns")
+        _require_bool(self.completed, "completed")
+        precedence = (
+            ("integrity", ExitCode.INTEGRITY),
+            ("configuration", ExitCode.CONFIGURATION),
+            ("phase", ExitCode.PHASE),
+            ("runtime", ExitCode.RUNTIME),
+            ("test_failure", ExitCode.TEST_FAILURE),
+            ("optional_unavailable", ExitCode.OPTIONAL_UNAVAILABLE),
+        )
+        categories = {
+            condition.category for condition in self.conditions if condition.affects_exit
+        }
+        all_categories = {condition.category for condition in self.conditions}
+        run_condition_keys = {_sort_key(condition) for condition in self.conditions}
+        nested_conditions: list[ObservedCondition] = []
+        required_categories: set[str] = set()
+
+        def inspect_profile(summary: ProfileSummary) -> None:
+            nested_conditions.extend(summary.conditions)
+            nested_conditions.extend(summary.evidence_guard.conditions)
+            if summary.evidence_guard.status == "changed":
+                required_categories.add("integrity")
+            if _failure_count(summary.counts):
+                required_categories.add("test_failure")
+            for payload in summary.payload_summaries:
+                nested_conditions.extend(payload.conditions)
+                category = {
+                    ExecutionStatus.TEST_FAILURE: "test_failure",
+                    ExecutionStatus.CONFIGURATION_FAILURE: "configuration",
+                    ExecutionStatus.INTEGRITY_FAILURE: "integrity",
+                    ExecutionStatus.PHASE_FAILURE: "phase",
+                    ExecutionStatus.RUNTIME_SAFETY_STOP: "runtime",
+                    ExecutionStatus.CANCELLED: "runtime",
+                    ExecutionStatus.NOT_RUN_SAFETY_STOP: "runtime",
+                }.get(payload.status)
+                if category is not None:
+                    required_categories.add(category)
+            for worker in summary.worker_summaries:
+                nested_conditions.extend(worker.conditions)
+                category = {
+                    ExecutionStatus.TEST_FAILURE: "test_failure",
+                    ExecutionStatus.CONFIGURATION_FAILURE: "configuration",
+                    ExecutionStatus.INTEGRITY_FAILURE: "integrity",
+                    ExecutionStatus.PHASE_FAILURE: "phase",
+                    ExecutionStatus.RUNTIME_SAFETY_STOP: "runtime",
+                    ExecutionStatus.CANCELLED: "runtime",
+                    ExecutionStatus.NOT_RUN_SAFETY_STOP: "runtime",
+                    ExecutionStatus.OPTIONAL_UNAVAILABLE: "optional_unavailable",
+                }.get(worker.status)
+                if category is not None:
+                    required_categories.add(category)
+                if worker.summary is not None:
+                    inspect_profile(worker.summary)
+
+        for summary in self.profile_summaries:
+            inspect_profile(summary)
+        if any(_sort_key(condition) not in run_condition_keys for condition in nested_conditions):
+            raise ValueError("run conditions must retain every nested observed condition")
+        if "optional_unavailable" in required_categories and "optional_unavailable" not in all_categories:
+            raise ValueError("optional unavailability requires a retained run condition")
+        exit_required = required_categories - {"optional_unavailable"}
+        if not exit_required.issubset(categories):
+            raise ValueError("run conditions must cover every nested terminal status")
+        expected_exit = next(
+            (code for category, code in precedence if category in categories),
+            ExitCode.SUCCESS,
+        )
+        if self.exit_code is not expected_exit:
+            raise ValueError("run exit_code disagrees with observed conditions")
+        if self.completed and any(not summary.completed for summary in self.profile_summaries):
+            raise ValueError("completed runs require completed profile summaries")
+        if self.exit_code is ExitCode.SUCCESS and not self.completed:
+            raise ValueError("successful runs must be complete")
+
+
+@dataclass(frozen=True, slots=True)
+class ConfigurationBundle:
+    repository_root: Path
+    profiles_path: Path
+    inventory_path: Path
+    baseline_commit: str
+    sealed_current_files_manifest: str
+    sealed_current_absences_manifest: str
+    historical_blobs_manifest: str
+    retained_v7_manifest: str
+    profile_definition_sha256: str
+    inventory_sha256: str
+    spec_capabilities_sha256: str
+    capability_bindings_sha256: str
+    inventory_entries: tuple[InventoryEntry, ...]
+    interpreter_slots: Mapping[str, InterpreterSlot]
+    profiles: Mapping[str, ProfilePlan]
+    payloads: Mapping[str, PayloadPlan]
+    historical_cases: Mapping[str, HistoricalCase]
+    overlays: Mapping[str, OverlaySpec]
+    subprocess_capabilities: Mapping[str, SubprocessCapability]
+    call_capabilities: Mapping[str, CallCapability]
+    capability_bindings: tuple[CapabilityBinding, ...]
+    stabilization_test_files: tuple[str, ...]
+
+    def __post_init__(self) -> None:
+        for name in ("repository_root", "profiles_path", "inventory_path"):
+            value = getattr(self, name)
+            if not isinstance(value, Path) or not value.is_absolute():
+                raise ValueError(f"{name} must be an absolute Path")
+        _require_git_oid(self.baseline_commit, "baseline_commit")
+        for name in ("sealed_current_files_manifest", "sealed_current_absences_manifest", "historical_blobs_manifest", "retained_v7_manifest"):
+            object.__setattr__(self, name, _normalise_relative_path(getattr(self, name), name))
+        for name in ("profile_definition_sha256", "inventory_sha256", "spec_capabilities_sha256", "capability_bindings_sha256"):
+            _require_sha256(getattr(self, name), name)
+        object.__setattr__(self, "inventory_entries", _normalise_tuple(
+            self.inventory_entries, "inventory_entries", _model_item(InventoryEntry),
+            sort_key=lambda item: item.selector.stable_id,
+        ))
+        mappings = (
+            ("interpreter_slots", InterpreterSlot), ("profiles", ProfilePlan), ("payloads", PayloadPlan),
+            ("historical_cases", HistoricalCase), ("overlays", OverlaySpec),
+            ("subprocess_capabilities", SubprocessCapability), ("call_capabilities", CallCapability),
+        )
+        for name, expected_type in mappings:
+            value = getattr(self, name)
+            if not isinstance(value, Mapping) or any(type(key) is not str or not isinstance(item, expected_type) for key, item in value.items()):
+                raise ValueError(f"{name} must map strings to {expected_type.__name__}")
+            object.__setattr__(self, name, MappingProxyType(dict(sorted(value.items()))))
+        object.__setattr__(self, "capability_bindings", _normalise_capability_bindings(self.capability_bindings))
+        object.__setattr__(self, "stabilization_test_files", _normalise_tuple(self.stabilization_test_files, "stabilization_test_files", _path_item))
