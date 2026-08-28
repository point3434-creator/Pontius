from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass, fields, is_dataclass
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import MappingProxyType
import unittest


COMMIT = "b" * 40
SHA256 = "a" * 64
ZERO_SHA256 = "0" * 64
SNAPSHOT_ROOT = Path(__file__).resolve().parents[1]

_SUPPORT_PATH = Path(__file__).with_name("orchestration_test_support.py")
_SUPPORT_SPEC = importlib.util.spec_from_file_location(
    "orchestration_test_support", _SUPPORT_PATH
)
if _SUPPORT_SPEC is None or _SUPPORT_SPEC.loader is None:
    raise RuntimeError("orchestration test support could not be loaded by exact path")
_SUPPORT = importlib.util.module_from_spec(_SUPPORT_SPEC)
_SUPPORT_SPEC.loader.exec_module(_SUPPORT)
_PATH_BEFORE_BOOTSTRAP = tuple(sys.path)
ERRORS, MODEL, CONFIGURATION = _SUPPORT.load_orchestration_modules(SNAPSHOT_ROOT)


MODEL_FIELDS = {
    "InterpreterIdentity": (
        "executable", "resolved_executable", "platform_identity", "executable_sha256",
        "implementation", "version", "prefix", "base_prefix", "no_user_site",
        "safe_path", "dont_write_bytecode", "distributions_sha256",
        "dependency_lock_sha256",
    ),
    "InterpreterBinding": ("slot_name", "identity"),
    "TargetIdentity": ("kind", "root", "head_commit", "root_tree_oid", "file_inventory_sha256"),
    "PrimaryRootIdentity": ("resolved_path", "platform_identity", "capture_sha256"),
    "GitToolIdentity": ("executable", "resolved_executable", "platform_identity", "executable_sha256"),
    "InterpreterSlot": (
        "name", "resolution", "windows_relative_path", "posix_relative_path",
        "environment_variable", "implementation", "minimum_version", "exact_version",
        "required_for_full",
    ),
    "ProfilePlan": (
        "name", "interpreter_slots", "default_interpreter_slot", "payload_ids",
        "historical_case_ids", "subprofiles", "budgets", "fixture_specs", "gpu_optional",
        "definition_sha256",
    ),
    "FixtureSpec": ("relative_path", "path_kind", "byte_length", "raw_sha256"),
    "InventoryExpectation": ("kind", "applicable_platforms", "skip_safe_reason_code"),
    "ResolvedInventoryItem": ("selector", "expectation"),
    "InventoryEntry": (
        "selector", "profile_name", "payload_id", "expectation", "exclusion_reason",
        "exclusion_owner", "exclusion_milestone",
    ),
    "PayloadPlan": (
        "payload_id", "profile_name", "target_kind", "allowed_interpreter_slots",
        "inventory_items", "probe_ids", "lifecycle_fixtures", "environment_additions",
        "environment_removals", "allowed_write_roots", "forbidden_relative_paths",
        "fixture_specs", "serialized",
    ),
    "LifecycleFixturePlan": (
        "fixture_id", "kind", "relative_path", "class_name", "member_ids",
        "allowed_write_roots", "forbidden_relative_paths", "serialized",
    ),
    "HistoricalItemExpectation": (
        "item_id", "outcome", "phase", "exception_type", "safe_reason_code",
        "body_entered", "capability_counters",
    ),
    "HistoricalSnapshotExpectation": ("phase", "commit", "root_tree_oid", "governing_decision"),
    "HistoricalBlobExpectation": (
        "commit", "relative_path", "git_blob_oid", "raw_sha256", "role", "phase",
        "governing_decision",
    ),
    "HistoricalCase": (
        "case_id", "phase", "commit", "root_tree_oid", "payload_ids", "expected_vector",
        "item_expectations", "overlay_ids",
    ),
    "OverlaySpec": (
        "overlay_id", "source_commit", "source_path", "destination_path", "byte_length",
        "raw_sha256",
    ),
    "SubprocessCapability": (
        "capability_id", "executable_role", "executable_slot", "executable_constraints",
        "argv", "argv_template", "dynamic_program_sha256", "cwd_class",
        "environment_additions", "environment_removals", "timeout_ns",
        "expected_return_category", "read_roots", "write_roots",
        "fixed_descendant_permission",
    ),
    "CallCapability": (
        "capability_id", "kind", "module_name", "qualified_name", "action",
        "maximum_calls", "return_contract",
    ),
    "CapabilityBinding": ("item_id", "approval_scope", "capability_kind", "capability_id"),
    "EvidenceManifestIdentity": (
        "relative_path", "schema_version", "byte_length", "raw_sha256", "semantic_sha256",
        "platform_identity",
    ),
    "EvidenceFileExpectation": ("relative_path", "byte_length", "raw_sha256", "role", "platform_identity"),
    "EvidenceAbsenceExpectation": ("relative_path", "role"),
    "EvidenceGuardPlan": ("semantic_sha256", "manifest_identities", "present_files", "absences"),
    "EvidenceGuardSummary": ("before_semantic_sha256", "after_semantic_sha256", "status", "conditions"),
    "ResolvedWorkerPlan": (
        "semantic_sha256", "profile", "inventory_entries", "payloads", "historical_cases",
        "historical_snapshots", "historical_blobs", "overlays", "subprocess_capabilities",
        "call_capabilities", "capability_bindings", "spec_capabilities_sha256",
        "capability_bindings_sha256",
    ),
    "ExecutionBundle": (
        "configuration", "evidence_guard_plan", "historical_snapshots", "historical_blobs",
        "semantic_sha256",
    ),
    "ObservedCondition": ("category", "code", "affects_exit", "context"),
    "CapturedStreamIdentity": ("byte_length", "raw_sha256", "truncated"),
    "CapturedOutputIdentity": ("stdout", "stderr"),
    "ChildExecutionResult": ("report", "process_return_category", "captured_output", "completed"),
    "PayloadSummary": (
        "payload_id", "status", "requested_ids", "outcomes", "counts", "conditions",
        "captured_output", "duration_ns", "completed",
    ),
    "WorkerSummary": (
        "profile", "interpreter_binding", "status", "summary", "conditions", "duration_ns",
        "completed",
    ),
    "ProfileSummary": (
        "profile", "profile_definition_sha256", "inventory_sha256", "spec_capabilities_sha256",
        "capability_bindings_sha256", "interpreter_bindings", "payload_summaries",
        "worker_summaries", "requested_ids", "outcomes", "counts", "conditions",
        "evidence_guard_sha256", "evidence_guard", "duration_ns", "completed",
    ),
    "RunSummary": (
        "run_id", "requested_profile", "profile_summaries", "conditions", "exit_code",
        "duration_ns", "completed",
    ),
    "ConfigurationBundle": (
        "repository_root", "profiles_path", "inventory_path", "baseline_commit",
        "sealed_current_files_manifest", "sealed_current_absences_manifest",
        "historical_blobs_manifest", "retained_v7_manifest", "profile_definition_sha256",
        "inventory_sha256", "spec_capabilities_sha256", "capability_bindings_sha256",
        "inventory_entries", "interpreter_slots", "profiles", "payloads", "historical_cases",
        "overlays", "subprocess_capabilities", "call_capabilities", "capability_bindings",
        "stabilization_test_files",
    ),
}


def _profiles_toml(*, reverse_root: bool = False) -> str:
    roots = [
        ("schema_version", '"pontius-test-profiles-v1"'),
        ("baseline_commit", f'"{COMMIT}"'),
        ("sealed_current_files_manifest", '"docs/architecture/sealed-current-files.toml"'),
        ("sealed_current_absences_manifest", '"docs/architecture/sealed-current-absences.toml"'),
        ("historical_blobs_manifest", '"docs/architecture/historical-blobs.toml"'),
        ("retained_v7_manifest", '"docs/architecture/retained-v7.toml"'),
        ("inventory_path", '"tests/test-inventory.json"'),
        ("spec_capabilities_sha256", f'"{ZERO_SHA256}"'),
        ("capability_bindings_sha256", f'"{ZERO_SHA256}"'),
        ("stabilization_test_files", '["tests/test_test_orchestration_configuration.py"]'),
    ]
    if reverse_root:
        roots.reverse()
    root_text = "\n".join(f"{key} = {value}" for key, value in roots)
    return root_text + f"""

[[interpreter_slot]]
name = "development"
resolution = "repository_relative"
windows_relative_path = ".venv/Scripts/python.exe"
posix_relative_path = ".venv/bin/python"
implementation = "cpython"
minimum_version = [3, 11]
required_for_full = true

[[profile]]
name = "core"
interpreter_slots = ["development"]
default_interpreter_slot = "development"
payload_ids = ["core:sample"]
historical_case_ids = []
subprofiles = []
gpu_optional = false

[profile.budgets]
setup_seconds = 2
child_seconds = 3
termination_seconds = 5
cleanup_seconds = 7
total_seconds = 17

[[payload]]
payload_id = "core:sample"
profile_name = "core"
target_kind = "current_snapshot"
allowed_interpreter_slots = ["development"]
probe_ids = []
environment_additions = {{ SAFE = "1" }}
environment_removals = ["PYTHONSTARTUP"]
allowed_write_roots = ["temporary"]
forbidden_relative_paths = ["artifacts/retained.json"]
serialized = false
"""


def _inventory(*, profile_name: str = "core", payload_id: str = "core:sample") -> dict[str, object]:
    stable_id = "tests/test_sample.py::SampleTests::test_value"
    return {
        "schema_version": "pontius-test-inventory-v1",
        "baseline_commit": COMMIT,
        "entries": [
            {
                "stable_id": stable_id,
                "relative_path": "tests/test_sample.py",
                "case_name": "SampleTests",
                "method_name": "test_value",
                "assignment": {
                    "profile_name": profile_name,
                    "payload_id": payload_id,
                    "expectation": {"kind": "pass"},
                },
            }
        ],
    }


def _call_capability_definition(capability_id: str = "call:sample") -> dict[str, object]:
    return {
        "capability_id": capability_id,
        "kind": "owner",
        "module_name": "sample",
        "qualified_name": "sample.owner",
        "action": "invoke",
        "maximum_calls": 1,
        "return_contract": "returns_none",
    }


def _approved_call_profiles(
    profiles: str,
    *,
    item_id: str = "tests/test_sample.py::SampleTests::test_value",
    scope: str = "design",
    capability_id: str = "call:sample",
    include_definition: bool = True,
) -> str:
    definition = _call_capability_definition(capability_id)
    row = {
        "item_id": item_id,
        "approval_scope": scope,
        "capability_kind": "call",
        **definition,
    }
    digest_name = (
        "spec_capabilities_sha256"
        if scope == "design"
        else "capability_bindings_sha256"
    )
    digest = MODEL.semantic_sha256((row,))
    profiles = profiles.replace(
        f'{digest_name} = "{ZERO_SHA256}"', f'{digest_name} = "{digest}"'
    )
    definition_text = ""
    if include_definition:
        definition_text = f'''\n\n[[call_capability]]
capability_id = "{capability_id}"
kind = "owner"
module_name = "sample"
qualified_name = "sample.owner"
action = "invoke"
maximum_calls = 1
return_contract = "returns_none"
'''
    return profiles + definition_text + f'''\n
[[capability_binding]]
item_id = "{item_id}"
approval_scope = "{scope}"
capability_kind = "call"
capability_id = "{capability_id}"
'''


def _approved_static_subprocess_profiles(profiles: str) -> str:
    item_id = "tests/test_sample.py::SampleTests::test_value"
    definition = {
        "capability_id": "process:sample",
        "executable_role": "python",
        "executable_slot": "active_worker",
        "executable_constraints": {},
        "argv": ("-m", "sample"),
        "argv_template": (),
        "dynamic_program_sha256": None,
        "cwd_class": "target",
        "environment_additions": {},
        "environment_removals": (),
        "timeout_ns": 10,
        "expected_return_category": "protocol_committed",
        "read_roots": ("target",),
        "write_roots": ("temporary",),
        "fixed_descendant_permission": False,
    }
    row = {
        "item_id": item_id,
        "approval_scope": "design",
        "capability_kind": "subprocess",
        **definition,
    }
    digest = MODEL.semantic_sha256((row,))
    profiles = profiles.replace(
        f'spec_capabilities_sha256 = "{ZERO_SHA256}"',
        f'spec_capabilities_sha256 = "{digest}"',
    )
    return profiles + f'''\n
[[subprocess_capability]]
capability_id = "process:sample"
executable_role = "python"
executable_slot = "active_worker"
executable_constraints = {{}}
argv = ["-m", "sample"]
argv_template = []
cwd_class = "target"
environment_additions = {{}}
environment_removals = []
timeout_ns = 10
expected_return_category = "protocol_committed"
read_roots = ["target"]
write_roots = ["temporary"]
fixed_descendant_permission = false

[[capability_binding]]
item_id = "{item_id}"
approval_scope = "design"
capability_kind = "subprocess"
capability_id = "process:sample"
'''


def _interpreter_binding(
    slot_name: str = "development", *, platform_identity: str = "windows:identity"
) -> object:
    identity = MODEL.InterpreterIdentity(
        "C:/Python/python.exe", "C:/Python/python.exe", platform_identity, SHA256,
        "cpython", [3, 14, 6, "final", 0], "C:/Python", "C:/Python",
        True, True, True, SHA256, None,
    )
    return MODEL.InterpreterBinding(slot_name, identity)


def _captured_output() -> object:
    stream = MODEL.CapturedStreamIdentity(0, sha256(b"").hexdigest(), False)
    return MODEL.CapturedOutputIdentity(stream, stream)


def _passed_payload(payload_id: str, stable_id: str) -> object:
    outcome = {"stable_id": stable_id, "outcome": "passed"}
    return MODEL.PayloadSummary(
        payload_id, MODEL.ExecutionStatus.PASSED, [stable_id], [outcome],
        {"passed": 1}, [], _captured_output(), 1, True,
    )


def _passed_direct(profile: str, binding: object, payloads: list[object]) -> object:
    outcomes = tuple(
        outcome for payload in payloads for outcome in payload.outcomes
    )
    requested_ids = tuple(item["stable_id"] for item in outcomes)
    counts: dict[str, int] = {}
    for payload in payloads:
        for key, value in payload.counts.items():
            counts[key] = counts.get(key, 0) + int(value)
    return MODEL.ProfileSummary(
        profile, SHA256, SHA256, SHA256, SHA256, [binding], payloads, [],
        requested_ids, outcomes, counts, [], SHA256,
        MODEL.EvidenceGuardSummary(SHA256, SHA256, "unchanged", []),
        1, True,
    )


class _ConfigurationTree:
    def __init__(self, profiles: str | None = None, inventory: dict[str, object] | None = None) -> None:
        self._temporary = tempfile.TemporaryDirectory(prefix="pontius-orchestration-config-")
        self.root = Path(self._temporary.name) / "repository"
        (self.root / "tests").mkdir(parents=True)
        self.profiles = self.root / "tests" / "test-profiles.toml"
        self.inventory = self.root / "tests" / "test-inventory.json"
        self.profiles.write_text(profiles if profiles is not None else _profiles_toml(), encoding="utf-8", newline="\n")
        self.inventory.write_text(
            json.dumps(inventory if inventory is not None else _inventory(), ensure_ascii=True, separators=(",", ":"), sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )

    def close(self) -> None:
        self._temporary.cleanup()

    def __enter__(self) -> "_ConfigurationTree":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


class OrchestrationBootstrapTests(unittest.TestCase):
    def test_exact_path_bootstrap_does_not_mutate_sys_path(self) -> None:
        self.assertEqual(tuple(sys.path), _PATH_BEFORE_BOOTSTRAP)
        package = sys.modules["pontius_test_orchestration"]
        self.assertEqual(package.__path__, [str(SNAPSHOT_ROOT / "tools" / "test_orchestration")])
        forbidden = {str(SNAPSHOT_ROOT), str(SNAPSHOT_ROOT / "tests")}
        self.assertTrue(forbidden.isdisjoint(sys.path))


class OrchestrationErrorAndModelTests(unittest.TestCase):
    def test_errors_have_stable_fields_and_recursively_immutable_sorted_context(self) -> None:
        for error_type in (
            ERRORS.EvidenceConfigurationError,
            ERRORS.EvidenceIntegrityError,
            ERRORS.AuthorizationPhaseError,
            ERRORS.LifecycleStateError,
            ERRORS.RuntimeContractError,
        ):
            error = error_type(
                "stable_code",
                "stable message",
                context={"z": [3, {"b": 2, "a": 1}], "a": {"roles": {"gpu", "cpu"}}},
            )
            self.assertEqual(error.code, "stable_code")
            self.assertEqual(error.message, "stable message")
            self.assertEqual(tuple(error.context), ("a", "z"))
            self.assertEqual(tuple(error.context["a"]), ("roles",))
            self.assertEqual(error.context["z"], (3, MappingProxyType({"a": 1, "b": 2})))
            with self.assertRaises(TypeError):
                error.context["new"] = True
        with self.assertRaises(TypeError):
            ERRORS.RuntimeContractError("bad", "bad", context={"value": object()})
        with self.assertRaises(TypeError):
            ERRORS.RuntimeContractError("bad", "bad", context={1: "value"})

    def test_exact_enums_and_every_declared_model_field_are_frozen_and_slotted(self) -> None:
        self.assertEqual(
            {item.name: item.value for item in MODEL.ExitCode},
            {"SUCCESS": 0, "CONFIGURATION": 2, "INTEGRITY": 3, "PHASE": 4, "RUNTIME": 5,
             "TEST_FAILURE": 6, "OPTIONAL_UNAVAILABLE": 7},
        )
        self.assertEqual(
            {item.name: item.value for item in MODEL.TargetKind},
            {"CURRENT_SNAPSHOT": "current_snapshot", "HISTORICAL_CLONE": "historical_clone"},
        )
        self.assertEqual(
            {item.name: item.value for item in MODEL.ExecutionStatus},
            {
                "PASSED": "passed", "TEST_FAILURE": "test_failure",
                "CONFIGURATION_FAILURE": "configuration_failure",
                "INTEGRITY_FAILURE": "integrity_failure", "PHASE_FAILURE": "phase_failure",
                "RUNTIME_SAFETY_STOP": "runtime_safety_stop", "CANCELLED": "cancelled",
                "NOT_RUN_SAFETY_STOP": "not_run_safety_stop",
                "OPTIONAL_UNAVAILABLE": "optional_unavailable",
            },
        )
        expected = {"StageBudgets": ("setup_ns", "child_ns", "termination_grace_ns", "cleanup_ns", "total_ns"),
                    "StableSelector": ("stable_id", "relative_path", "case_name", "method_name"), **MODEL_FIELDS}
        for name, field_names in expected.items():
            with self.subTest(model=name):
                model_type = getattr(MODEL, name)
                self.assertTrue(is_dataclass(model_type))
                self.assertTrue(model_type.__dataclass_params__.frozen)
                self.assertEqual(tuple(field.name for field in fields(model_type)), field_names)
                self.assertIn("__slots__", vars(model_type))

    def test_budgets_are_positive_exact_integers_and_reserve_every_stage(self) -> None:
        valid = MODEL.StageBudgets(1, 2, 3, 4, 10)
        self.assertEqual(valid.total_ns, 10)
        with self.assertRaises(FrozenInstanceError):
            valid.total_ns = 11
        for values in ((0, 2, 3, 4, 10), (True, 2, 3, 4, 10), (1, 2, 3, 4, 9)):
            with self.subTest(values=values), self.assertRaises(ValueError):
                MODEL.StageBudgets(*values)

    def test_stable_id_parser_accepts_only_normalized_test_methods(self) -> None:
        selector = CONFIGURATION.parse_stable_id(
            "tests/nested/test_sample.py::SampleTests::test_value"
        )
        self.assertEqual(selector.relative_path.as_posix(), "tests/nested/test_sample.py")
        self.assertEqual(selector.case_name, "SampleTests")
        self.assertEqual(selector.method_name, "test_value")
        invalid = (
            "probe:v7", "tests/test_sample.py::SampleTests", "tests/test_sample.py::SampleTests::value",
            "tests/test_sample.txt::SampleTests::test_value",
            "tests/../outside.py::SampleTests::test_value",
            "tests\\test_sample.py::SampleTests::test_value",
            "/tests/test_sample.py::SampleTests::test_value",
            "tests/test_sample.py::not-valid::test_value",
            "tests/test_sample.py::SampleTests::test_value::extra",
        )
        for value in invalid:
            with self.subTest(value=value), self.assertRaises(ERRORS.EvidenceConfigurationError):
                CONFIGURATION.parse_stable_id(value)

    def test_repeated_values_sort_uniquely_and_mappings_freeze_recursively(self) -> None:
        identity = MODEL.InterpreterIdentity(
            "C:/Python/python.exe", "C:/Python/python.exe", "windows:volume-2:file-1",
            SHA256, "cpython", [3, 14, 6, "final", 0], "C:/Python", "C:/Python", True, True, True,
            SHA256, None,
        )
        binding = MODEL.InterpreterBinding("development", identity)
        fixture_b = MODEL.FixtureSpec("fixtures/b.bin", "regular_file", 1, SHA256)
        fixture_a = MODEL.FixtureSpec("fixtures/a.bin", "regular_file", 2, SHA256)
        profile = MODEL.ProfilePlan(
            "core", ["development"], "development", ["payload:b", "payload:a"], [], [],
            MODEL.StageBudgets(1, 1, 1, 1, 4), [fixture_b, fixture_a], False, SHA256,
        )
        self.assertEqual(identity.platform_identity, "windows:volume-2:file-1")
        self.assertEqual(identity.version, (3, 14, 6, "final", 0))
        self.assertEqual(profile.payload_ids, ("payload:a", "payload:b"))
        self.assertEqual(tuple(item.relative_path for item in profile.fixture_specs),
                         ("fixtures/a.bin", "fixtures/b.bin"))
        self.assertEqual(binding.identity, identity)
        with self.assertRaises(ValueError):
            MODEL.ProfilePlan(
                "core", ["development", "development"], "development", [], [], [],
                MODEL.StageBudgets(1, 1, 1, 1, 4), [], False, SHA256,
            )
        with self.assertRaises(ValueError):
            MODEL.InterpreterIdentity(
                "C:/Python/python.exe", "C:/Python/python.exe", "windows:identity", SHA256,
                "cpython", [3, 14, 6, "final", 0], "C:/Python", "C:/Python",
                True, True, True, SHA256, "",
            )
        for bad_platform, bad_version in (
            ({"volume": 2}, [3, 14, 6, "final", 0]),
            ("windows:identity", [3, 14, 6]),
            ("windows:identity", [3, 14, True, "final", 0]),
            ("windows:identity", [3, 14, 6, 7, 0]),
        ):
            with self.subTest(platform=bad_platform, version=bad_version), self.assertRaises(ValueError):
                MODEL.InterpreterIdentity(
                    "C:/Python/python.exe", "C:/Python/python.exe", bad_platform, SHA256,
                    "cpython", bad_version, "C:/Python", "C:/Python", True, True, True,
                    SHA256, None,
                )

    def test_profile_variants_require_direct_defaults_or_full_subprofiles(self) -> None:
        budgets = MODEL.StageBudgets(1, 1, 1, 1, 4)
        full = MODEL.ProfilePlan(
            "full", ["development", "cpython311"], None, [], [], ["core"], budgets,
            [], False, SHA256,
        )
        self.assertEqual(full.subprofiles, ("core",))
        invalid = (
            ("core", ["development"], None, ["core:sample"], [], []),
            ("full", ["development"], "development", [], [], ["core"]),
            ("full", ["development"], None, ["core:sample"], [], ["core"]),
            ("full", ["development"], None, [], [], []),
        )
        for values in invalid:
            with self.subTest(values=values), self.assertRaises(ValueError):
                MODEL.ProfilePlan(*values, budgets, [], False, SHA256)

    def test_interpreter_bindings_sort_by_slot_name_not_nested_identity(self) -> None:
        identity_a = MODEL.InterpreterIdentity(
            "C:/A/python.exe", "C:/A/python.exe", "windows:a", SHA256,
            "cpython", [3, 14, 6, "final", 0], "C:/A", "C:/A",
            True, True, True, SHA256, None,
        )
        identity_z = MODEL.InterpreterIdentity(
            "C:/Z/python.exe", "C:/Z/python.exe", "windows:z", SHA256,
            "cpython", [3, 11, 9, "final", 0], "C:/Z", "C:/Z",
            True, True, True, SHA256, None,
        )
        condition = MODEL.ObservedCondition("runtime", "safety_stop", True, {})
        binding_z = MODEL.InterpreterBinding("z-slot", identity_a)
        binding_a = MODEL.InterpreterBinding("a-slot", identity_z)
        summary = MODEL.ProfileSummary(
            "full", SHA256, SHA256, SHA256, SHA256,
            [binding_z, binding_a], [],
            [
                MODEL.WorkerSummary(
                    "z-profile", binding_z, MODEL.ExecutionStatus.NOT_RUN_SAFETY_STOP,
                    None, [condition], 0, False,
                ),
                MODEL.WorkerSummary(
                    "a-profile", binding_a, MODEL.ExecutionStatus.NOT_RUN_SAFETY_STOP,
                    None, [condition], 0, False,
                ),
            ],
            [], [], {}, [condition], SHA256,
            MODEL.EvidenceGuardSummary(None, None, "not_measured", []),
            0, False,
        )
        self.assertEqual(
            tuple(item.slot_name for item in summary.interpreter_bindings),
            ("a-slot", "z-slot"),
        )
        with self.assertRaises(ValueError):
            MODEL.ProfileSummary(
                "core", SHA256, SHA256, SHA256, SHA256,
                [binding_z, binding_a], [], [], [], [], {}, [condition], SHA256,
                MODEL.EvidenceGuardSummary(None, None, "not_measured", []),
                0, False,
            )

    def test_guard_and_terminal_summary_invariants_reject_incoherent_states(self) -> None:
        condition = MODEL.ObservedCondition("runtime", "timeout", True, {"stage": "child"})
        unchanged = MODEL.EvidenceGuardSummary(SHA256, SHA256, "unchanged", [])
        self.assertEqual(unchanged.conditions, ())
        with self.assertRaises(ValueError):
            MODEL.EvidenceGuardSummary(SHA256, "c" * 64, "unchanged", [])
        with self.assertRaises(ValueError):
            MODEL.EvidenceGuardSummary(None, SHA256, "not_measured", [])
        unstarted = MODEL.PayloadSummary(
            "core:later", MODEL.ExecutionStatus.NOT_RUN_SAFETY_STOP, [], [], {}, [condition],
            None, 0, False,
        )
        self.assertFalse(unstarted.completed)
        with self.assertRaises(ValueError):
            MODEL.PayloadSummary(
                "core:later", MODEL.ExecutionStatus.NOT_RUN_SAFETY_STOP, ["id"], [], {},
                [condition], None, 0, False,
            )
        with self.assertRaises(ValueError):
            MODEL.PayloadSummary(
                "core:done", MODEL.ExecutionStatus.PASSED, ["id"], [], {"passed": 1}, [],
                None, 1, True,
            )
        with self.assertRaises(ValueError):
            MODEL.PayloadSummary(
                "core:active", MODEL.ExecutionStatus.RUNTIME_SAFETY_STOP,
                ["id"], [], {}, [condition], None, 0, False,
            )

    def test_guard_plan_requires_exact_source_and_governed_path_cardinalities(self) -> None:
        manifests = tuple(reversed(tuple(
            MODEL.EvidenceManifestIdentity(
                f"docs/manifest-{index:02d}.toml", "schema-v1", 100 - index, SHA256, SHA256,
                f"windows:manifest-{index:02d}",
            )
            for index in range(4)
        )))
        present = tuple(reversed(tuple(
            MODEL.EvidenceFileExpectation(
                f"artifacts/present-{index:02d}.json", 100 - index, SHA256, "retained",
                f"windows:present-{index:02d}",
            )
            for index in range(6)
        )))
        absences = tuple(reversed(tuple(
            MODEL.EvidenceAbsenceExpectation(
                f"artifacts/absent-{index:02d}.json", "required_absence"
            )
            for index in range(18)
        )))
        sorted_manifests = tuple(sorted(manifests, key=lambda item: item.relative_path))
        sorted_present = tuple(sorted(present, key=lambda item: item.relative_path))
        sorted_absences = tuple(sorted(absences, key=lambda item: item.relative_path))
        digest = MODEL.semantic_sha256(
            {
                "manifest_identities": sorted_manifests,
                "present_files": sorted_present,
                "absences": sorted_absences,
            }
        )
        plan = MODEL.EvidenceGuardPlan(digest, manifests, present, absences)
        self.assertEqual(len(plan.absences), 18)
        self.assertEqual(plan.manifest_identities, sorted_manifests)
        self.assertEqual(plan.present_files, sorted_present)
        self.assertEqual(plan.absences, sorted_absences)
        for changed in (
            (manifests[:-1], present, absences),
            (manifests, present[:-1], absences),
            (manifests, present, absences[:-1]),
        ):
            changed_digest = MODEL.semantic_sha256(
                {
                    "manifest_identities": changed[0],
                    "present_files": changed[1],
                    "absences": changed[2],
                }
            )
            with self.subTest(lengths=tuple(len(items) for items in changed)), self.assertRaises(ValueError):
                MODEL.EvidenceGuardPlan(changed_digest, *changed)

    def test_payload_and_worker_summaries_validate_ids_and_unstarted_work(self) -> None:
        stream = MODEL.CapturedStreamIdentity(0, sha256(b"").hexdigest(), False)
        captured = MODEL.CapturedOutputIdentity(stream, stream)
        with self.assertRaises(ValueError):
            MODEL.PayloadSummary(
                "core:sample", MODEL.ExecutionStatus.PASSED, ["id:a"],
                [{"stable_id": "id:b"}], {"passed": 1}, [], captured, 1, True,
            )

        identity = MODEL.InterpreterIdentity(
            "C:/Python/python.exe", "C:/Python/python.exe", "windows:identity", SHA256,
            "cpython", [3, 14, 6, "final", 0], "C:/Python", "C:/Python",
            True, True, True, SHA256, None,
        )
        binding = MODEL.InterpreterBinding("development", identity)
        trigger = MODEL.ObservedCondition("runtime", "safety_stop", True, {})
        not_run = MODEL.WorkerSummary(
            "core", binding, MODEL.ExecutionStatus.NOT_RUN_SAFETY_STOP, None,
            [trigger], 0, False,
        )
        self.assertFalse(not_run.completed)
        for duration, completed, conditions in ((1, False, [trigger]), (0, True, [trigger]), (0, False, [])):
            with self.subTest(duration=duration, completed=completed, conditions=conditions), self.assertRaises(ValueError):
                MODEL.WorkerSummary(
                    "core", binding, MODEL.ExecutionStatus.NOT_RUN_SAFETY_STOP, None,
                    conditions, duration, completed,
                )

    def test_nested_summaries_reject_fabricated_completion_and_exit_state(self) -> None:
        identity = MODEL.InterpreterIdentity(
            "C:/Python/python.exe", "C:/Python/python.exe", "windows:identity", SHA256,
            "cpython", [3, 14, 6, "final", 0], "C:/Python", "C:/Python",
            True, True, True, SHA256, None,
        )
        binding = MODEL.InterpreterBinding("development", identity)
        stream = MODEL.CapturedStreamIdentity(0, sha256(b"").hexdigest(), False)
        captured = MODEL.CapturedOutputIdentity(stream, stream)
        outcome = {"stable_id": "tests/test_sample.py::SampleTests::test_value"}
        payload = MODEL.PayloadSummary(
            "core:sample", MODEL.ExecutionStatus.PASSED,
            [outcome["stable_id"]], [outcome], {"passed": 1}, [], captured, 1, True,
        )
        guard = MODEL.EvidenceGuardSummary(SHA256, SHA256, "unchanged", [])
        direct = MODEL.ProfileSummary(
            "core", SHA256, SHA256, SHA256, SHA256, [binding], [payload], [],
            [outcome["stable_id"]], [outcome], {"passed": 1}, [], SHA256,
            guard, 1, True,
        )
        with self.assertRaises(ValueError):
            MODEL.WorkerSummary(
                "different-profile", binding, MODEL.ExecutionStatus.PASSED,
                direct, [], 1, True,
            )

        trigger = MODEL.ObservedCondition("runtime", "safety_stop", True, {})
        not_run = MODEL.PayloadSummary(
            "core:sample", MODEL.ExecutionStatus.NOT_RUN_SAFETY_STOP,
            [], [], {}, [trigger], None, 0, False,
        )
        with self.assertRaises(ValueError):
            MODEL.ProfileSummary(
                "core", SHA256, SHA256, SHA256, SHA256, [binding], [not_run], [],
                [], [], {}, [trigger], SHA256, guard, 1, True,
            )
        with self.assertRaises(ValueError):
            MODEL.RunSummary(
                "run-id", "core", [direct], [trigger], MODEL.ExitCode.SUCCESS, 1, True,
            )

        failed_payload = MODEL.PayloadSummary(
            "core:sample", MODEL.ExecutionStatus.TEST_FAILURE,
            [outcome["stable_id"]], [outcome], {"failures": 1}, [], captured, 1, True,
        )
        failed_profile = MODEL.ProfileSummary(
            "core", SHA256, SHA256, SHA256, SHA256, [binding], [failed_payload], [],
            [outcome["stable_id"]], [outcome], {"failures": 1}, [], SHA256,
            guard, 1, True,
        )
        with self.assertRaises(ValueError):
            MODEL.RunSummary(
                "run-id", "core", [failed_profile], [], MODEL.ExitCode.SUCCESS, 1, True,
            )
        test_failure = MODEL.ObservedCondition(
            "test_failure", "assertion_failed", True, {}
        )
        failed_run = MODEL.RunSummary(
            "run-id", "core", [failed_profile], [test_failure],
            MODEL.ExitCode.TEST_FAILURE, 1, True,
        )
        self.assertEqual(failed_run.exit_code, MODEL.ExitCode.TEST_FAILURE)

    def test_resolved_worker_plan_requires_exact_internal_transitive_closure(self) -> None:
        selector = CONFIGURATION.parse_stable_id(
            "tests/test_sample.py::SampleTests::test_value"
        )
        inventory_item = MODEL.ResolvedInventoryItem(
            selector, MODEL.InventoryExpectation("pass", [], None)
        )
        with self.assertRaises(ValueError):
            MODEL.PayloadPlan(
                "core:sample", "core", MODEL.TargetKind.CURRENT_SNAPSHOT,
                ["development"], [inventory_item], ["not-a-probe"], [], {}, [],
                [], [], [], False,
            )
        payload = MODEL.PayloadPlan(
            "core:sample", "core", MODEL.TargetKind.CURRENT_SNAPSHOT,
            ["development"], [inventory_item], [], [], {}, [], [], [], [], False,
        )
        profile = MODEL.ProfilePlan(
            "core", ["development"], "development", ["core:sample"], [], [],
            MODEL.StageBudgets(1, 1, 1, 1, 4), [], False, SHA256,
        )

        def plan(**changes: object) -> object:
            values: dict[str, object] = {
                "profile": profile,
                "inventory_entries": [inventory_item],
                "payloads": [payload],
                "historical_cases": [],
                "historical_snapshots": [],
                "historical_blobs": [],
                "overlays": [],
                "subprocess_capabilities": [],
                "call_capabilities": [],
                "capability_bindings": [],
                "spec_capabilities_sha256": SHA256,
                "capability_bindings_sha256": SHA256,
            }
            values.update(changes)
            for name in (
                "inventory_entries", "payloads", "historical_cases",
                "historical_snapshots", "historical_blobs", "overlays",
                "subprocess_capabilities", "call_capabilities",
                "capability_bindings",
            ):
                values[name] = tuple(sorted(
                    values[name], key=MODEL.canonical_semantic_bytes
                ))
            return MODEL.ResolvedWorkerPlan(
                semantic_sha256=MODEL.semantic_sha256(values), **values
            )

        self.assertEqual(plan().payloads, (payload,))
        with self.assertRaises(ValueError):
            plan(inventory_entries=[], payloads=[])
        unrelated = MODEL.CallCapability(
            "call:unrelated", "owner", "module", "qualified", "invoke", 1,
            "returns_none",
        )
        with self.assertRaises(ValueError):
            plan(call_capabilities=[unrelated])
        conflicting_payload = MODEL.PayloadPlan(
            "core:sample", "core", MODEL.TargetKind.CURRENT_SNAPSHOT,
            ["development"], [inventory_item], [], [], {}, [], [], [], [], True,
        )
        with self.assertRaises(ValueError):
            plan(payloads=[payload, conflicting_payload])

    def test_completed_direct_and_full_summaries_require_their_owned_rows(self) -> None:
        identity = MODEL.InterpreterIdentity(
            "C:/Python/python.exe", "C:/Python/python.exe", "windows:identity", SHA256,
            "cpython", [3, 14, 6, "final", 0], "C:/Python", "C:/Python",
            True, True, True, SHA256, None,
        )
        binding = MODEL.InterpreterBinding("development", identity)
        guard = MODEL.EvidenceGuardSummary(SHA256, SHA256, "unchanged", [])
        summary_args = (
            "core", SHA256, SHA256, SHA256, SHA256, [binding], [], [], [], [], {}, [],
            SHA256, guard, 1, True,
        )
        with self.assertRaises(ValueError):
            MODEL.ProfileSummary(*summary_args)

        full_args = (
            "full", SHA256, SHA256, SHA256, SHA256, [], [], [], [], [], {}, [],
            SHA256, guard, 1, True,
        )
        with self.assertRaises(ValueError):
            MODEL.ProfileSummary(*full_args)

    def test_inventory_entries_preserve_assignment_xor_exclusion(self) -> None:
        selector = CONFIGURATION.parse_stable_id(
            "tests/test_sample.py::SampleTests::test_value"
        )
        expectation = MODEL.InventoryExpectation("pass", [], None)
        assigned = MODEL.InventoryEntry(
            selector, "core", "core:sample", expectation, None, None, None
        )
        excluded = MODEL.InventoryEntry(
            selector, None, None, None, "legacy-only", "stabilization", "milestone-2"
        )
        self.assertEqual(assigned.expectation, expectation)
        self.assertEqual(excluded.exclusion_owner, "stabilization")
        with self.assertRaises(ValueError):
            MODEL.InventoryEntry(
                selector, "core", "core:sample", expectation,
                "legacy-only", "stabilization", "milestone-2",
            )
        with self.assertRaises(ValueError):
            MODEL.InventoryEntry(selector, None, None, None, None, None, None)

    def test_capability_bindings_use_ruled_total_order_and_call_contract_is_string(self) -> None:
        call = MODEL.CallCapability(
            "call:a", "owner", "module", "qualified", "invoke", 1, "returns_none"
        )
        self.assertEqual(call.return_contract, "returns_none")
        with self.assertRaises(ValueError):
            MODEL.CallCapability("call:b", "owner", "module", "qualified", "invoke", 1, "")
        with self.assertRaises(ValueError):
            MODEL.CallCapability("call:c", "owner", "module", "qualified", "invoke", 1, {})

        bindings = (
            MODEL.CapabilityBinding("item:b", "design", "call", "call:a"),
            MODEL.CapabilityBinding("item:a", "historical_review", "call", "call:a"),
            MODEL.CapabilityBinding("item:a", "design", "subprocess", "process:z"),
            MODEL.CapabilityBinding("item:a", "design", "call", "call:z"),
        )
        bundle = MODEL.ConfigurationBundle(
            Path("C:/repository"), Path("C:/repository/tests/test-profiles.toml"),
            Path("C:/repository/tests/test-inventory.json"), COMMIT,
            "docs/files.toml", "docs/absences.toml", "docs/blobs.toml", "docs/v7.toml",
            SHA256, SHA256, SHA256, SHA256, [], {}, {}, {}, {}, {}, {}, {}, bindings, [],
        )
        self.assertEqual(
            tuple(
                (item.approval_scope, item.item_id, item.capability_kind, item.capability_id)
                for item in bundle.capability_bindings
            ),
            (
                ("design", "item:a", "call", "call:z"),
                ("design", "item:a", "subprocess", "process:z"),
                ("design", "item:b", "call", "call:a"),
                ("historical_review", "item:a", "call", "call:a"),
            ),
        )

    def test_capability_models_validate_kinds_slots_and_ordered_duplicate_argv(self) -> None:
        program = "value"
        capability = MODEL.SubprocessCapability(
            "process:a", "python", "active_worker", {},
            ["python", "-c", program, "value"], [],
            sha256(program.encode("utf-8")).hexdigest(), "target", {}, [], 10,
            "protocol_committed", ["target"], ["temporary"], False,
        )
        self.assertEqual(capability.argv, ("python", "-c", "value", "value"))
        static = MODEL.SubprocessCapability(
            "process:static", "python", "active_worker", {},
            ["-m", "sample"], [], None, "target", {}, [], 10,
            "protocol_committed", ["target"], ["temporary"], False,
        )
        self.assertIsNone(static.dynamic_program_sha256)
        git_configuration = MODEL.SubprocessCapability(
            "process:git-config", "git", "git", {},
            ["-c", "safe.directory=C:/target", "status"], [], None, "target", {},
            [], 10, "exited_zero", ["target"], [], False,
        )
        self.assertEqual(git_configuration.argv[0], "-c")
        for argv, dynamic_digest in (
            (["-c", program], None),
            (["-c", program], SHA256),
            (["-m", "sample"], SHA256),
            (["-c"], sha256(b"").hexdigest()),
            (["-c", program, "-c", program], sha256(program.encode()).hexdigest()),
        ):
            with self.subTest(argv=argv, digest=dynamic_digest), self.assertRaises(ValueError):
                MODEL.SubprocessCapability(
                    "process:dynamic", "python", "active_worker", {}, argv, [],
                    dynamic_digest, "target", {}, [], 10, "protocol_committed",
                    ["target"], ["temporary"], False,
                )
        with self.assertRaises(ValueError):
            MODEL.SubprocessCapability(
                "process:a", "python", "ambient_path", {}, ["python"], [], None,
                "target", {}, [], 10, "protocol_committed", [], [], False,
            )
        with self.assertRaises(ValueError):
            MODEL.CallCapability(
                "call:a", "unknown", "module", "qualified", "invoke", 1, "returns_none"
            )

    def test_inventory_expectation_variants_and_nested_values_fail_closed(self) -> None:
        unconditional = MODEL.InventoryExpectation(
            "declared_unconditional_skip", [], "unsupported_by_design"
        )
        self.assertEqual(unconditional.skip_safe_reason_code, "unsupported_by_design")
        for values in (
            ("declared_unconditional_skip", ["windows"], "reason"),
            ("declared_unconditional_skip", [], None),
            ("pass", [], "irrelevant"),
            ("case_defined", ["posix"], None),
        ):
            with self.subTest(values=values), self.assertRaises(ValueError):
                MODEL.InventoryExpectation(*values)

        @dataclass
        class MutableValue:
            values: list[int]

        @dataclass(frozen=True)
        class SpoofedFrozenValue:
            values: list[int]

        SpoofedFrozenValue.__module__ = MODEL.__name__

        mutable = MutableValue([1])
        with self.assertRaises(ValueError):
            MODEL.ObservedCondition(
                "runtime", "unsafe_nested_value", True, {"mutable": mutable}
            )
        with self.assertRaises(ValueError):
            MODEL.PayloadSummary(
                "core:sample", MODEL.ExecutionStatus.PASSED, ["id"],
                [{"stable_id": "id", "mutable": mutable}], {"passed": 1}, [],
                _captured_output(), 1, True,
            )
        with self.assertRaises(ValueError):
            MODEL.ObservedCondition(
                "runtime", "spoofed_nested_value", True,
                {"mutable": SpoofedFrozenValue([1])},
            )
        mutable_internal = MODEL.ChildExecutionResult(
            {"x": []}, "protocol_committed", _captured_output(), True
        )
        with self.assertRaises(ValueError):
            MODEL.ObservedCondition(
                "runtime", "mutable_internal_dataclass", True,
                {"mutable": mutable_internal},
            )

    def test_lifecycle_fixtures_require_canonical_ids_and_exact_payload_members(self) -> None:
        stable_id = "tests/test_sample.py::SampleTests::test_value"
        selector = CONFIGURATION.parse_stable_id(stable_id)
        inventory_item = MODEL.ResolvedInventoryItem(
            selector, MODEL.InventoryExpectation("pass", [], None)
        )
        module_fixture = MODEL.LifecycleFixturePlan(
            "fixture:tests/test_sample.py", "module", "tests/test_sample.py", None,
            [stable_id], ["temporary"], [], True,
        )
        class_fixture = MODEL.LifecycleFixturePlan(
            "fixture:tests/test_sample.py::SampleTests", "class",
            "tests/test_sample.py", "SampleTests", [stable_id], ["temporary"], [],
            True,
        )
        payload = MODEL.PayloadPlan(
            "core:sample", "core", MODEL.TargetKind.CURRENT_SNAPSHOT,
            ["development"], [inventory_item], [], [module_fixture, class_fixture],
            {}, [], [], [], [], True,
        )
        self.assertEqual(
            tuple(item.fixture_id for item in payload.lifecycle_fixtures),
            (
                "fixture:tests/test_sample.py",
                "fixture:tests/test_sample.py::SampleTests",
            ),
        )
        invalid_fixtures = (
            ("fixture:wrong.py", "module", "tests/test_sample.py", None, [stable_id]),
            ("fixture:tests/test_sample.py::Wrong", "class", "tests/test_sample.py", "Wrong", [stable_id]),
            ("fixture:tests/test_sample.py", "module", "tests/test_sample.py", None, []),
            (
                "fixture:tests/test_sample.py::SampleTests", "class",
                "tests/test_sample.py", "SampleTests",
                ["tests/test_other.py::SampleTests::test_value"],
            ),
            (
                "fixture:tests/test_sample.py", "module", "tests/test_sample.py",
                None, ["tests\\test_sample.py::SampleTests::test_value"],
            ),
        )
        for values in invalid_fixtures:
            with self.subTest(values=values), self.assertRaises(ValueError):
                MODEL.LifecycleFixturePlan(*values, ["temporary"], [], True)
        other_member = MODEL.LifecycleFixturePlan(
            "fixture:tests/test_other.py", "module", "tests/test_other.py", None,
            ["tests/test_other.py::OtherTests::test_value"], ["temporary"], [], True,
        )
        with self.assertRaises(ValueError):
            MODEL.PayloadPlan(
                "core:sample", "core", MODEL.TargetKind.CURRENT_SNAPSHOT,
                ["development"], [inventory_item], [], [other_member], {}, [], [], [],
                [], True,
            )

    def test_profile_aggregates_bind_exact_child_rows_counts_and_outcomes(self) -> None:
        binding = _interpreter_binding()
        first = _passed_payload("core:first", "tests/test_a.py::ATests::test_a")
        second = _passed_payload("core:second", "tests/test_b.py::BTests::test_b")
        direct = _passed_direct("core", binding, [second, first])
        self.assertEqual(
            tuple(item.payload_id for item in direct.payload_summaries),
            ("core:first", "core:second"),
        )
        common = (
            "core", SHA256, SHA256, SHA256, SHA256, [binding], [first, second], [],
            ["tests/test_a.py::ATests::test_a", "tests/test_b.py::BTests::test_b"],
        )
        for outcomes, counts in (
            (
                [
                    {"stable_id": "tests/test_a.py::ATests::test_a", "outcome": "fabricated"},
                    {"stable_id": "tests/test_b.py::BTests::test_b", "outcome": "passed"},
                ],
                {"passed": 2},
            ),
            (list(first.outcomes + second.outcomes), {"passed": 99}),
        ):
            with self.subTest(outcomes=outcomes, counts=counts), self.assertRaises(ValueError):
                MODEL.ProfileSummary(
                    *common, outcomes, counts, [], SHA256,
                    MODEL.EvidenceGuardSummary(SHA256, SHA256, "unchanged", []),
                    1, True,
                )
        duplicate_id = MODEL.PayloadSummary(
            first.payload_id, first.status, first.requested_ids, first.outcomes,
            first.counts, first.conditions, first.captured_output, 2, True,
        )
        with self.assertRaises(ValueError):
            _passed_direct("core", binding, [first, duplicate_id])

    def test_full_summary_uses_distinct_binding_union_and_exact_worker_aggregates(self) -> None:
        binding = _interpreter_binding()
        core_payload = _passed_payload(
            "core:sample", "tests/test_core.py::CoreTests::test_value"
        )
        current_payload = _passed_payload(
            "current:sample", "tests/test_current.py::CurrentTests::test_value"
        )
        core = _passed_direct("core", binding, [core_payload])
        current = _passed_direct("current", binding, [current_payload])
        workers = [
            MODEL.WorkerSummary(
                "core", binding, MODEL.ExecutionStatus.PASSED, core, [], 1, True
            ),
            MODEL.WorkerSummary(
                "current", binding, MODEL.ExecutionStatus.PASSED, current, [], 1, True
            ),
        ]
        requested = tuple(sorted(core.requested_ids + current.requested_ids))
        outcomes = tuple(sorted(core.outcomes + current.outcomes, key=lambda row: row["stable_id"]))
        guard = MODEL.EvidenceGuardSummary(SHA256, SHA256, "unchanged", [])
        full = MODEL.ProfileSummary(
            "full", SHA256, SHA256, SHA256, SHA256, [binding], [], workers,
            requested, outcomes, {"passed": 2}, [], SHA256, guard, 2, True,
        )
        self.assertEqual(full.interpreter_bindings, (binding,))
        full_with_payload_rows = MODEL.ProfileSummary(
            "full", SHA256, SHA256, SHA256, SHA256, [binding],
            [current_payload, core_payload], workers, requested, outcomes,
            {"passed": 2}, [], SHA256, guard, 2, True,
        )
        self.assertEqual(len(full_with_payload_rows.payload_summaries), 2)
        with self.assertRaises(ValueError):
            MODEL.ProfileSummary(
                "full", SHA256, SHA256, SHA256, SHA256, [binding], [], workers,
                requested,
                [
                    {"stable_id": requested[0], "outcome": "fabricated"},
                    {"stable_id": requested[1], "outcome": "passed"},
                ],
                {"passed": 2}, [], SHA256, guard, 2, True,
            )
        with self.assertRaises(ValueError):
            MODEL.ProfileSummary(
                "full", SHA256, SHA256, SHA256, SHA256, [binding],
                [core_payload], workers, requested, outcomes, {"passed": 2}, [],
                SHA256, guard, 2, True,
            )
        conflicting_binding = _interpreter_binding(
            platform_identity="windows:conflicting"
        )
        conflicting_worker = MODEL.WorkerSummary(
            "current", conflicting_binding, MODEL.ExecutionStatus.PASSED,
            _passed_direct("current", conflicting_binding, [current_payload]), [], 1,
            True,
        )
        with self.assertRaises(ValueError):
            MODEL.ProfileSummary(
                "full", SHA256, SHA256, SHA256, SHA256, [binding], [],
                [workers[0], conflicting_worker], requested, outcomes, {"passed": 2},
                [], SHA256, guard, 2, True,
            )
        duplicate_worker = MODEL.WorkerSummary(
            "core", binding, MODEL.ExecutionStatus.PASSED, core, [], 2, True
        )
        with self.assertRaises(ValueError):
            MODEL.ProfileSummary(
                "full", SHA256, SHA256, SHA256, SHA256, [binding], [],
                [workers[0], duplicate_worker], core.requested_ids, core.outcomes,
                {"passed": 2}, [], SHA256, guard, 2, True,
            )

    def test_run_summary_retains_not_run_trigger_and_direct_gpu_semantics(self) -> None:
        binding = _interpreter_binding()
        for category, exit_code in (
            ("integrity", MODEL.ExitCode.INTEGRITY),
            ("phase", MODEL.ExitCode.PHASE),
        ):
            condition = MODEL.ObservedCondition(category, f"{category}_stop", True, {})
            payload = MODEL.PayloadSummary(
                "core:sample", MODEL.ExecutionStatus.NOT_RUN_SAFETY_STOP,
                [], [], {}, [condition], None, 0, False,
            )
            profile = MODEL.ProfileSummary(
                "core", SHA256, SHA256, SHA256, SHA256, [binding], [payload], [],
                [], [], {}, [condition], SHA256,
                MODEL.EvidenceGuardSummary(None, None, "not_measured", []), 0, False,
            )
            run = MODEL.RunSummary(
                f"run-{category}", "core", [profile], [condition], exit_code, 0, False
            )
            self.assertEqual(run.exit_code, exit_code)

        optional_direct = MODEL.ObservedCondition(
            "optional_unavailable", "gpu_unavailable", True, {"profile": "gpu"}
        )
        guard = MODEL.EvidenceGuardSummary(SHA256, SHA256, "unchanged", [])
        gpu = MODEL.ProfileSummary(
            "gpu", SHA256, SHA256, SHA256, SHA256, [binding], [], [], [], [], {},
            [optional_direct], SHA256, guard, 1, True,
        )
        direct_run = MODEL.RunSummary(
            "run-gpu", "gpu", [gpu], [optional_direct],
            MODEL.ExitCode.OPTIONAL_UNAVAILABLE, 1, True,
        )
        self.assertEqual(direct_run.exit_code, MODEL.ExitCode.OPTIONAL_UNAVAILABLE)

        optional_full = MODEL.ObservedCondition(
            "optional_unavailable", "gpu_unavailable", False, {"profile": "gpu"}
        )
        worker = MODEL.WorkerSummary(
            "gpu", binding, MODEL.ExecutionStatus.OPTIONAL_UNAVAILABLE, None,
            [optional_full], 0, True,
        )
        full = MODEL.ProfileSummary(
            "full", SHA256, SHA256, SHA256, SHA256, [binding], [], [worker],
            [], [], {}, [optional_full], SHA256, guard, 1, True,
        )
        full_run = MODEL.RunSummary(
            "run-full", "full", [full], [optional_full], MODEL.ExitCode.SUCCESS, 1,
            True,
        )
        self.assertEqual(full_run.exit_code, MODEL.ExitCode.SUCCESS)
        core_payload = _passed_payload(
            "core:sample", "tests/test_sample.py::SampleTests::test_value"
        )
        core_summary = _passed_direct("core", binding, [core_payload])
        passed_worker = MODEL.WorkerSummary(
            "core", binding, MODEL.ExecutionStatus.PASSED, core_summary, [], 1,
            True,
        )
        with self.assertRaises(ValueError):
            MODEL.ProfileSummary(
                "full", SHA256, SHA256, SHA256, SHA256, [binding], [],
                [passed_worker], core_summary.requested_ids, core_summary.outcomes,
                core_summary.counts, [optional_full], SHA256, guard, 1, True,
            )
        affecting_full_optional = MODEL.ObservedCondition(
            "optional_unavailable", "gpu_unavailable", True, {"profile": "gpu"}
        )
        with self.assertRaises(ValueError):
            MODEL.ProfileSummary(
                "full", SHA256, SHA256, SHA256, SHA256, [binding], [], [worker],
                [], [], {}, [affecting_full_optional], SHA256, guard, 1, True,
            )
        with self.assertRaises(ValueError):
            MODEL.RunSummary(
                "run-full-exit-seven", "full", [full],
                [optional_full, affecting_full_optional],
                MODEL.ExitCode.OPTIONAL_UNAVAILABLE, 1, True,
            )
        with self.assertRaises(ValueError):
            MODEL.RunSummary(
                "run-mismatch", "current", [gpu], [optional_direct],
                MODEL.ExitCode.OPTIONAL_UNAVAILABLE, 1, True,
            )
        with self.assertRaises(ValueError):
            MODEL.RunSummary(
                "run-empty", "core", [], [], MODEL.ExitCode.SUCCESS, 0, True
            )

    def test_historical_expected_vectors_have_exact_variant_fields_and_counts(self) -> None:
        item = MODEL.HistoricalItemExpectation(
            "tests/test_sample.py::SampleTests::test_value", "pass", None, None, None,
            None, {},
        )
        vector = {
            "kind": "positive", "passed": 1, "assertion_failed": 0,
            "setup_failed": 0, "body_entered": 1, "owner_calls": 0,
            "scientific_calls": 0,
        }
        case = MODEL.HistoricalCase(
            "base", "source", COMMIT, COMMIT, ["historical:base"], vector, [item], []
        )
        self.assertEqual(case.expected_vector["passed"], 1)
        for invalid in ({**vector, "extra": 0}, {**vector, "passed": True}):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                MODEL.HistoricalCase(
                    "base", "source", COMMIT, COMMIT, ["historical:base"], invalid,
                    [item], [],
                )

    def test_resolved_historical_plan_requires_exact_runtime_item_and_blob_closure(self) -> None:
        stable_id = "tests/test_sample.py::SampleTests::test_value"
        selector = CONFIGURATION.parse_stable_id(stable_id)
        item = MODEL.ResolvedInventoryItem(
            selector, MODEL.InventoryExpectation("case_defined", [], None)
        )
        fixture = MODEL.LifecycleFixturePlan(
            "fixture:tests/test_sample.py", "module", "tests/test_sample.py", None,
            [stable_id], [], [], True,
        )
        payload = MODEL.PayloadPlan(
            "historical:sample", "historical", MODEL.TargetKind.HISTORICAL_CLONE,
            ["development"], [item], ["probe:sealed-reader"], [fixture], {}, [],
            [], [], [], True,
        )
        profile = MODEL.ProfilePlan(
            "historical", ["development"], "development", ["historical:sample"],
            ["case:sample"], [], MODEL.StageBudgets(1, 1, 1, 1, 4), [], False,
            SHA256,
        )
        vector = {
            "kind": "positive", "passed": 2, "assertion_failed": 0,
            "setup_failed": 0, "body_entered": 2, "owner_calls": 0,
            "scientific_calls": 0,
        }
        expected_items = [
            MODEL.HistoricalItemExpectation(
                stable_id, "pass", None, None, None, None, {}
            ),
            MODEL.HistoricalItemExpectation(
                "probe:sealed-reader", "pass", None, None, None, None, {}
            ),
        ]
        case = MODEL.HistoricalCase(
            "case:sample", "source", COMMIT, COMMIT, ["historical:sample"],
            vector, expected_items, [],
        )
        snapshot = MODEL.HistoricalSnapshotExpectation(
            "source", COMMIT, COMMIT, "reviewed"
        )
        blob = MODEL.HistoricalBlobExpectation(
            COMMIT, "tests/test_sample.py", COMMIT, SHA256, "selected_test",
            "source", "reviewed",
        )

        def resolved(**changes: object) -> object:
            values: dict[str, object] = {
                "profile": profile,
                "inventory_entries": [item],
                "payloads": [payload],
                "historical_cases": [case],
                "historical_snapshots": [snapshot],
                "historical_blobs": [blob],
                "overlays": [],
                "subprocess_capabilities": [],
                "call_capabilities": [],
                "capability_bindings": [],
                "spec_capabilities_sha256": SHA256,
                "capability_bindings_sha256": SHA256,
            }
            values.update(changes)
            for name in (
                "inventory_entries", "payloads", "historical_cases",
                "historical_snapshots", "historical_blobs", "overlays",
                "subprocess_capabilities", "call_capabilities",
                "capability_bindings",
            ):
                values[name] = tuple(sorted(
                    values[name], key=MODEL.canonical_semantic_bytes
                ))
            return MODEL.ResolvedWorkerPlan(
                semantic_sha256=MODEL.semantic_sha256(values), **values
            )

        self.assertEqual(resolved().historical_blobs, (blob,))
        missing_item_case = MODEL.HistoricalCase(
            "case:sample", "source", COMMIT, COMMIT, ["historical:sample"],
            vector, expected_items[:1], [],
        )
        fixture_result_case = MODEL.HistoricalCase(
            "case:sample", "source", COMMIT, COMMIT, ["historical:sample"],
            vector,
            expected_items + [
                MODEL.HistoricalItemExpectation(
                    fixture.fixture_id, "pass", None, None, None, None, {}
                )
            ],
            [],
        )
        wrong_phase_blob = MODEL.HistoricalBlobExpectation(
            COMMIT, "tests/test_sample.py", COMMIT, SHA256, "selected_test",
            "retained", "reviewed",
        )
        unrelated_selected_blob = MODEL.HistoricalBlobExpectation(
            COMMIT, "tests/test_unrelated.py", "c" * 40, "d" * 64,
            "selected_test", "source", "reviewed",
        )
        for changes in (
            {"historical_cases": [missing_item_case]},
            {"historical_cases": [fixture_result_case]},
            {"historical_blobs": [wrong_phase_blob]},
            {"historical_blobs": []},
            {"historical_blobs": [blob, unrelated_selected_blob]},
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                resolved(**changes)

        conflicting_root_case = MODEL.HistoricalCase(
            "case:conflicting-root", "source", COMMIT, "c" * 40,
            ["historical:sample"], vector, expected_items, [],
        )
        conflicting_root_snapshot = MODEL.HistoricalSnapshotExpectation(
            "source", COMMIT, "c" * 40, "reviewed"
        )
        conflicting_root_profile = MODEL.ProfilePlan(
            "historical", ["development"], "development", ["historical:sample"],
            ["case:sample", "case:conflicting-root"], [],
            MODEL.StageBudgets(1, 1, 1, 1, 4), [], False, SHA256,
        )
        with self.assertRaises(ValueError):
            resolved(
                profile=conflicting_root_profile,
                historical_cases=[case, conflicting_root_case],
                historical_snapshots=[snapshot, conflicting_root_snapshot],
            )

        empty_payload = MODEL.PayloadPlan(
            "historical:empty", "historical", MODEL.TargetKind.HISTORICAL_CLONE,
            ["development"], [], [], [], {}, [], [], [], [], True,
        )
        two_payload_profile = MODEL.ProfilePlan(
            "historical", ["development"], "development",
            ["historical:sample", "historical:empty"], ["case:sample"], [],
            MODEL.StageBudgets(1, 1, 1, 1, 4), [], False, SHA256,
        )
        empty_owner_case = MODEL.HistoricalCase(
            "case:sample", "source", COMMIT, COMMIT,
            ["historical:sample", "historical:empty"], vector, expected_items, [],
        )
        with self.assertRaises(ValueError):
            resolved(
                profile=two_payload_profile,
                payloads=[payload, empty_payload],
                historical_cases=[empty_owner_case],
            )

        conflicting_expectation = MODEL.HistoricalItemExpectation(
            stable_id, "expected_negative", "source", "ValueError", "blocked",
            False, {},
        )
        with self.assertRaises(ValueError):
            MODEL.HistoricalCase(
                "case:duplicate", "source", COMMIT, COMMIT,
                ["historical:sample"], vector,
                [expected_items[0], conflicting_expectation], [],
            )


class OrchestrationConfigurationTests(unittest.TestCase):
    def test_load_configuration_builds_frozen_normalized_bundle_and_ns_budgets(self) -> None:
        with _ConfigurationTree() as tree:
            bundle = CONFIGURATION.load_configuration(
                tree.profiles, tree.inventory, repository_root=tree.root
            )
        self.assertEqual(bundle.baseline_commit, COMMIT)
        self.assertEqual(bundle.profiles["core"].budgets, MODEL.StageBudgets(
            2_000_000_000, 3_000_000_000, 5_000_000_000, 7_000_000_000,
            17_000_000_000,
        ))
        self.assertEqual(
            bundle.payloads["core:sample"].inventory_items[0].selector.stable_id,
            "tests/test_sample.py::SampleTests::test_value",
        )
        self.assertIsInstance(bundle.profiles, MappingProxyType)
        self.assertEqual(bundle.stabilization_test_files,
                         ("tests/test_test_orchestration_configuration.py",))
        with self.assertRaises(ERRORS.EvidenceConfigurationError) as refused:
            CONFIGURATION.select_profile(bundle, "core", payload_id="core:sample")
        self.assertEqual(refused.exception.code, "capability_approval_required")
        self.assertEqual(
            refused.exception.message, "applicable capabilities are not approved"
        )
        with self.assertRaises(ERRORS.EvidenceConfigurationError):
            CONFIGURATION.select_profile(bundle, "missing")
        with self.assertRaises(ERRORS.EvidenceConfigurationError):
            CONFIGURATION.select_profile(bundle, "core", payload_id="missing")
        with self.assertRaises(ERRORS.EvidenceConfigurationError):
            CONFIGURATION.select_profile(
                bundle, "core", payload_id="core:sample", historical_case="case"
            )

    def test_inventory_variants_use_exact_keys_including_unconditional_skip(self) -> None:
        unconditional = _inventory()
        unconditional["entries"][0]["assignment"]["expectation"] = {
            "kind": "declared_unconditional_skip",
            "skip_safe_reason_code": "unsupported_by_design",
        }
        with _ConfigurationTree(inventory=unconditional) as tree:
            bundle = CONFIGURATION.load_configuration(
                tree.profiles, tree.inventory, repository_root=tree.root
            )
        expectation = bundle.payloads["core:sample"].inventory_items[0].expectation
        self.assertEqual(expectation.kind, "declared_unconditional_skip")

        invalid_expectations = (
            {"kind": "pass", "applicable_platforms": []},
            {"kind": "pass", "skip_safe_reason_code": None},
            {"kind": "case_defined", "applicable_platforms": []},
            {
                "kind": "declared_unconditional_skip",
                "applicable_platforms": [],
                "skip_safe_reason_code": "reason",
            },
        )
        for expectation in invalid_expectations:
            inventory = _inventory()
            inventory["entries"][0]["assignment"]["expectation"] = expectation
            with self.subTest(expectation=expectation), _ConfigurationTree(
                inventory=inventory
            ) as tree:
                with self.assertRaises(ERRORS.EvidenceConfigurationError):
                    CONFIGURATION.load_configuration(
                        tree.profiles, tree.inventory, repository_root=tree.root
                    )

    def test_full_profile_resolves_transitive_fixtures_and_rejects_cycles(self) -> None:
        profiles = _profiles_toml() + f'''\n
[[payload.ignored_fixture]]
relative_path = "fixtures/sample.bin"
path_kind = "regular_file"
byte_length = 1
raw_sha256 = "{SHA256}"

[[profile]]
name = "full"
interpreter_slots = ["development"]
payload_ids = []
historical_case_ids = []
subprofiles = ["core"]
gpu_optional = false

[profile.budgets]
setup_seconds = 2
child_seconds = 3
termination_seconds = 5
cleanup_seconds = 7
total_seconds = 17
'''
        with _ConfigurationTree(profiles=profiles) as tree:
            bundle = CONFIGURATION.load_configuration(
                tree.profiles, tree.inventory, repository_root=tree.root
            )
        self.assertEqual(
            tuple(item.relative_path for item in bundle.profiles["full"].fixture_specs),
            ("fixtures/sample.bin",),
        )
        expected_definition = MODEL.semantic_sha256({
            field: getattr(bundle.profiles["full"], field)
            for field in (
                "name", "interpreter_slots", "default_interpreter_slot",
                "payload_ids", "historical_case_ids", "subprofiles", "budgets",
                "fixture_specs", "gpu_optional",
            )
        })
        self.assertEqual(
            bundle.profiles["full"].definition_sha256, expected_definition
        )

        cyclic = profiles.replace('subprofiles = ["core"]', 'subprofiles = ["full"]')
        with _ConfigurationTree(profiles=cyclic) as tree:
            with self.assertRaises(ERRORS.EvidenceConfigurationError):
                CONFIGURATION.load_configuration(
                    tree.profiles, tree.inventory, repository_root=tree.root
                )

    def test_lifecycle_fixture_configuration_requires_exact_member_closure(self) -> None:
        fixture_text = '''

[[payload.lifecycle_fixture]]
fixture_id = "fixture:tests/test_sample.py"
kind = "module"
relative_path = "tests/test_sample.py"
member_ids = ["tests/test_sample.py::SampleTests::test_value"]
allowed_write_roots = ["temporary"]
forbidden_relative_paths = []
serialized = true
'''
        with _ConfigurationTree(profiles=_profiles_toml() + fixture_text) as tree:
            bundle = CONFIGURATION.load_configuration(
                tree.profiles, tree.inventory, repository_root=tree.root
            )
        self.assertEqual(
            bundle.payloads["core:sample"].lifecycle_fixtures[0].fixture_id,
            "fixture:tests/test_sample.py",
        )
        invalid_profiles = (
            (_profiles_toml() + fixture_text).replace(
                'fixture_id = "fixture:tests/test_sample.py"',
                'fixture_id = "fixture:tests/wrong.py"',
            ),
            (_profiles_toml() + fixture_text).replace(
                'member_ids = ["tests/test_sample.py::SampleTests::test_value"]',
                'member_ids = []',
            ),
            (_profiles_toml() + fixture_text).replace(
                'member_ids = ["tests/test_sample.py::SampleTests::test_value"]',
                'member_ids = ["tests/test_other.py::OtherTests::test_value"]',
            ),
        )
        for profiles in invalid_profiles:
            with self.subTest(profiles=profiles[-100:]), _ConfigurationTree(
                profiles=profiles
            ) as tree:
                with self.assertRaises(ERRORS.EvidenceConfigurationError):
                    CONFIGURATION.load_configuration(
                        tree.profiles, tree.inventory, repository_root=tree.root
                    )

        split_inventory = _inventory()
        split_inventory["entries"].append({
            "stable_id": "tests/test_sample.py::OtherTests::test_other",
            "relative_path": "tests/test_sample.py",
            "case_name": "OtherTests",
            "method_name": "test_other",
            "assignment": {
                "profile_name": "core",
                "payload_id": "core:second",
                "expectation": {"kind": "pass"},
            },
        })
        split_profiles = (
            _profiles_toml().replace(
                'payload_ids = ["core:sample"]',
                'payload_ids = ["core:sample", "core:second"]',
            )
            + fixture_text
            + '''

[[payload]]
payload_id = "core:second"
profile_name = "core"
target_kind = "current_snapshot"
allowed_interpreter_slots = ["development"]
probe_ids = []
environment_additions = {}
environment_removals = []
allowed_write_roots = ["temporary"]
forbidden_relative_paths = []
serialized = true
'''
        )
        with _ConfigurationTree(split_profiles, split_inventory) as tree:
            with self.assertRaises(ERRORS.EvidenceConfigurationError):
                CONFIGURATION.load_configuration(
                    tree.profiles, tree.inventory, repository_root=tree.root
                )

    def test_capability_digests_validate_expansion_and_selection_by_scope(self) -> None:
        approved = _approved_call_profiles(_profiles_toml())
        with _ConfigurationTree(profiles=approved) as tree:
            bundle = CONFIGURATION.load_configuration(
                tree.profiles, tree.inventory, repository_root=tree.root
            )
        selected = CONFIGURATION.select_profile(
            bundle, "core", payload_id="core:sample"
        )
        self.assertEqual(selected.payload_ids, ("core:sample",))

        stale = approved.replace('maximum_calls = 1', 'maximum_calls = 2')
        with _ConfigurationTree(profiles=stale) as tree:
            with self.assertRaises(ERRORS.EvidenceConfigurationError):
                CONFIGURATION.load_configuration(
                    tree.profiles, tree.inventory, repository_root=tree.root
                )

        zero_with_rows = approved.replace(
            next(
                line.split(' = "', 1)[1][:-1]
                for line in approved.splitlines()
                if line.startswith("spec_capabilities_sha256 = ")
            ),
            ZERO_SHA256,
            1,
        )
        with _ConfigurationTree(profiles=zero_with_rows) as tree:
            with self.assertRaises(ERRORS.EvidenceConfigurationError):
                CONFIGURATION.load_configuration(
                    tree.profiles, tree.inventory, repository_root=tree.root
                )

        unused = _profiles_toml() + '''

[[call_capability]]
capability_id = "call:unused"
kind = "owner"
module_name = "sample"
qualified_name = "sample.owner"
action = "invoke"
maximum_calls = 1
return_contract = "returns_none"
'''
        with _ConfigurationTree(profiles=unused) as tree:
            with self.assertRaises(ERRORS.EvidenceConfigurationError):
                CONFIGURATION.load_configuration(
                    tree.profiles, tree.inventory, repository_root=tree.root
                )

    def test_static_subprocess_capability_omits_inapplicable_dynamic_digest(self) -> None:
        profiles = _approved_static_subprocess_profiles(_profiles_toml())
        with _ConfigurationTree(profiles=profiles) as tree:
            bundle = CONFIGURATION.load_configuration(
                tree.profiles, tree.inventory, repository_root=tree.root
            )
        capability = bundle.subprocess_capabilities["process:sample"]
        self.assertIsNone(capability.dynamic_program_sha256)
        self.assertEqual(
            CONFIGURATION.select_profile(bundle, "core").name, "core"
        )

    def test_capability_approval_is_scope_aware_and_transitive_for_full(self) -> None:
        historical_id = "tests/test_history.py::HistoryTests::test_value"
        mixed_profiles = _profiles_toml() + f'''\n
[[profile]]
name = "historical"
interpreter_slots = ["development"]
default_interpreter_slot = "development"
payload_ids = ["historical:sample"]
historical_case_ids = ["case:source"]
subprofiles = []
gpu_optional = false

[profile.budgets]
setup_seconds = 2
child_seconds = 3
termination_seconds = 5
cleanup_seconds = 7
total_seconds = 17

[[profile]]
name = "full"
interpreter_slots = ["development"]
payload_ids = []
historical_case_ids = []
subprofiles = ["core", "historical"]
gpu_optional = false

[profile.budgets]
setup_seconds = 2
child_seconds = 3
termination_seconds = 5
cleanup_seconds = 7
total_seconds = 17

[[payload]]
payload_id = "historical:sample"
profile_name = "historical"
target_kind = "historical_clone"
allowed_interpreter_slots = ["development"]
probe_ids = []
environment_additions = {{}}
environment_removals = []
allowed_write_roots = ["temporary"]
forbidden_relative_paths = []
serialized = true

[[historical_case]]
case_id = "case:source"
phase = "source"
commit = "{COMMIT}"
root_tree_oid = "{COMMIT}"
payload_ids = ["historical:sample"]
overlay_ids = []
expected_vector = {{ kind = "positive", passed = 1, assertion_failed = 0, setup_failed = 0, body_entered = 1, owner_calls = 0, scientific_calls = 0 }}

[[historical_case.item_expectation]]
item_id = "{historical_id}"
outcome = "pass"
'''
        inventory = _inventory()
        inventory["entries"].append({
            "stable_id": historical_id,
            "relative_path": "tests/test_history.py",
            "case_name": "HistoryTests",
            "method_name": "test_value",
            "assignment": {
                "profile_name": "historical",
                "payload_id": "historical:sample",
                "expectation": {"kind": "case_defined"},
            },
        })
        design_approved = _approved_call_profiles(mixed_profiles)
        with _ConfigurationTree(design_approved, inventory) as tree:
            bundle = CONFIGURATION.load_configuration(
                tree.profiles, tree.inventory, repository_root=tree.root
            )
        self.assertEqual(CONFIGURATION.select_profile(bundle, "core").name, "core")
        for profile_name in ("historical", "full"):
            with self.subTest(profile=profile_name):
                with self.assertRaises(
                    ERRORS.EvidenceConfigurationError
                ) as refused:
                    CONFIGURATION.select_profile(bundle, profile_name)
                self.assertEqual(
                    refused.exception.code, "capability_approval_required"
                )
                self.assertEqual(
                    refused.exception.message,
                    "applicable capabilities are not approved",
                )

        shared_across_scopes = _approved_call_profiles(
            design_approved,
            item_id=historical_id,
            scope="historical_review",
            include_definition=False,
        )
        with _ConfigurationTree(shared_across_scopes, inventory) as tree:
            with self.assertRaises(ERRORS.EvidenceConfigurationError):
                CONFIGURATION.load_configuration(
                    tree.profiles, tree.inventory, repository_root=tree.root
                )

    def test_strict_toml_and_json_reject_duplicate_unknown_missing_and_wrong_types(self) -> None:
        mutations = {
            "duplicate-toml": _profiles_toml() + "\nschema_version = \"pontius-test-profiles-v1\"\n",
            "unknown-root": _profiles_toml() + "\nunexpected = true\n",
            "missing-root": _profiles_toml().replace(f'baseline_commit = "{COMMIT}"\n', ""),
            "boolean-budget": _profiles_toml().replace("setup_seconds = 2", "setup_seconds = true"),
            "unknown-profile-field": _profiles_toml().replace(
                "gpu_optional = false", "gpu_optional = false\nunexpected = true"
            ),
            "escaping-manifest": _profiles_toml().replace(
                "docs/architecture/sealed-current-files.toml", "../outside.toml"
            ),
        }
        for name, profiles in mutations.items():
            with self.subTest(name=name), _ConfigurationTree(profiles=profiles) as tree:
                with self.assertRaises(ERRORS.EvidenceConfigurationError):
                    CONFIGURATION.load_configuration(
                        tree.profiles, tree.inventory, repository_root=tree.root
                    )

        duplicate_json = (
            '{"schema_version":"pontius-test-inventory-v1",'
            '"schema_version":"pontius-test-inventory-v1",'
            f'"baseline_commit":"{COMMIT}","entries":[]}}\n'
        )
        with _ConfigurationTree() as tree:
            tree.inventory.write_text(duplicate_json, encoding="utf-8", newline="\n")
            with self.assertRaises(ERRORS.EvidenceConfigurationError):
                CONFIGURATION.load_configuration(
                    tree.profiles, tree.inventory, repository_root=tree.root
                )

    def test_unknown_profile_payload_and_capability_references_fail_closed(self) -> None:
        cases: list[tuple[str, str, dict[str, object]]] = [
            ("inventory-profile", _profiles_toml(), _inventory(profile_name="missing")),
            ("inventory-payload", _profiles_toml(), _inventory(payload_id="missing")),
            (
                "profile-payload",
                _profiles_toml().replace('payload_ids = ["core:sample"]', 'payload_ids = ["missing"]'),
                _inventory(),
            ),
            (
                "payload-interpreter-slot",
                _profiles_toml().replace(
                    'allowed_interpreter_slots = ["development"]',
                    'allowed_interpreter_slots = ["development", "missing"]',
                ),
                _inventory(),
            ),
            (
                "malformed-probe-id",
                _profiles_toml().replace(
                    "probe_ids = []", 'probe_ids = ["not-a-probe"]',
                ),
                _inventory(),
            ),
            (
                "capability",
                _profiles_toml() + """

[[capability_binding]]
item_id = "tests/test_sample.py::SampleTests::test_value"
approval_scope = "design"
capability_kind = "call"
capability_id = "missing"
""",
                _inventory(),
            ),
        ]
        for name, profiles, inventory in cases:
            with self.subTest(name=name), _ConfigurationTree(profiles, inventory) as tree:
                with self.assertRaises(ERRORS.EvidenceConfigurationError):
                    CONFIGURATION.load_configuration(
                        tree.profiles, tree.inventory, repository_root=tree.root
                    )

    def test_excluded_inventory_entries_are_retained_but_not_joined_to_payloads(self) -> None:
        inventory = _inventory()
        inventory["entries"].append(
            {
                "stable_id": "tests/test_legacy.py::LegacyTests::test_retained",
                "relative_path": "tests/test_legacy.py",
                "case_name": "LegacyTests",
                "method_name": "test_retained",
                "exclusion": {
                    "reason": "historical-only",
                    "owner": "stabilization",
                    "milestone": "milestone-2",
                },
            }
        )
        with _ConfigurationTree(inventory=inventory) as tree:
            bundle = CONFIGURATION.load_configuration(
                tree.profiles, tree.inventory, repository_root=tree.root
            )
        self.assertEqual(len(bundle.inventory_entries), 2)
        self.assertEqual(
            tuple(item.selector.stable_id for item in bundle.payloads["core:sample"].inventory_items),
            ("tests/test_sample.py::SampleTests::test_value",),
        )
        excluded = next(item for item in bundle.inventory_entries if item.exclusion_reason)
        self.assertEqual(excluded.exclusion_milestone, "milestone-2")

        both = _inventory()
        both["entries"][0]["exclusion"] = {
            "reason": "invalid", "owner": "owner", "milestone": "milestone"
        }
        with self.subTest(case="assignment-and-exclusion"), _ConfigurationTree(inventory=both) as tree:
            with self.assertRaises(ERRORS.EvidenceConfigurationError):
                CONFIGURATION.load_configuration(
                    tree.profiles, tree.inventory, repository_root=tree.root
                )

    def test_semantic_digests_ignore_toml_and_json_mapping_key_order(self) -> None:
        with _ConfigurationTree() as first, _ConfigurationTree(
            profiles=_profiles_toml(reverse_root=True)
        ) as second:
            first_inventory = _inventory()
            second_inventory = {
                "entries": first_inventory["entries"],
                "baseline_commit": first_inventory["baseline_commit"],
                "schema_version": first_inventory["schema_version"],
            }
            second.inventory.write_text(
                json.dumps(second_inventory, ensure_ascii=True, separators=(",", ":")) + "\n",
                encoding="utf-8", newline="\n",
            )
            left = CONFIGURATION.load_configuration(
                first.profiles, first.inventory, repository_root=first.root
            )
            right = CONFIGURATION.load_configuration(
                second.profiles, second.inventory, repository_root=second.root
            )
        self.assertEqual(left.profile_definition_sha256, right.profile_definition_sha256)
        self.assertEqual(left.inventory_sha256, right.inventory_sha256)
        self.assertEqual(
            CONFIGURATION.canonical_semantic_bytes({"b": [2, True], "a": None}),
            b'{"a":null,"b":[2,true]}',
        )
        self.assertEqual(
            CONFIGURATION.semantic_sha256({"a": 1}), sha256(b'{"a":1}').hexdigest()
        )

    def test_semantic_digests_use_normalized_collection_order(self) -> None:
        exclusion = {
            "stable_id": "tests/test_legacy.py::LegacyTests::test_retained",
            "relative_path": "tests/test_legacy.py",
            "case_name": "LegacyTests",
            "method_name": "test_retained",
            "exclusion": {
                "reason": "historical-only", "owner": "stabilization",
                "milestone": "milestone-2",
            },
        }
        first_inventory = _inventory()
        first_inventory["entries"].append(exclusion)
        second_inventory = _inventory()
        second_inventory["entries"].insert(0, exclusion)
        first_profiles = _profiles_toml().replace(
            '["tests/test_test_orchestration_configuration.py"]',
            '["tests/z_stabilization.py", "tests/a_stabilization.py"]',
        )
        second_profiles = _profiles_toml().replace(
            '["tests/test_test_orchestration_configuration.py"]',
            '["tests/a_stabilization.py", "tests/z_stabilization.py"]',
        )
        with _ConfigurationTree(first_profiles, first_inventory) as first, _ConfigurationTree(
            second_profiles, second_inventory
        ) as second:
            left = CONFIGURATION.load_configuration(
                first.profiles, first.inventory, repository_root=first.root
            )
            right = CONFIGURATION.load_configuration(
                second.profiles, second.inventory, repository_root=second.root
            )
        self.assertEqual(left.profile_definition_sha256, right.profile_definition_sha256)
        self.assertEqual(left.inventory_sha256, right.inventory_sha256)

    def test_exit_precedence_is_exhaustive_and_ignores_non_exit_optional_conditions(self) -> None:
        categories = {
            "integrity": MODEL.ExitCode.INTEGRITY,
            "configuration": MODEL.ExitCode.CONFIGURATION,
            "phase": MODEL.ExitCode.PHASE,
            "runtime": MODEL.ExitCode.RUNTIME,
            "test_failure": MODEL.ExitCode.TEST_FAILURE,
            "optional_unavailable": MODEL.ExitCode.OPTIONAL_UNAVAILABLE,
        }
        ordered = ["integrity", "configuration", "phase", "runtime", "test_failure", "optional_unavailable"]
        for left_index, left in enumerate(ordered):
            for right_index, right in enumerate(ordered):
                with self.subTest(left=left, right=right):
                    conditions = [
                        MODEL.ObservedCondition(left, f"{left}_code", True, {}),
                        MODEL.ObservedCondition(right, f"{right}_code", True, {}),
                    ]
                    self.assertEqual(
                        CONFIGURATION.choose_exit_code(conditions),
                        categories[ordered[min(left_index, right_index)]],
                    )
        optional = MODEL.ObservedCondition(
            "optional_unavailable", "gpu_unavailable", False, {"profile": "gpu"}
        )
        self.assertEqual(CONFIGURATION.choose_exit_code([optional]), MODEL.ExitCode.SUCCESS)
        self.assertEqual(CONFIGURATION.choose_exit_code([]), MODEL.ExitCode.SUCCESS)
        with self.assertRaises(ValueError):
            MODEL.ObservedCondition("runtime", "timeout", False, {})


if __name__ == "__main__":
    unittest.main(verbosity=2)
