"""Generate and verify the immutable test ownership and profile lock."""

from __future__ import annotations

import argparse
import ast
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from hashlib import sha1, sha256
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import tempfile
import threading
import time
import tomllib
from typing import Any
import uuid

_SECURE_FILESYSTEM_PATH = Path(__file__).with_name("generate_dependency_baseline.py")
_SECURE_FILESYSTEM_SPEC = importlib.util.spec_from_file_location(
    "pontius_inventory_secure_filesystem", _SECURE_FILESYSTEM_PATH
)
if _SECURE_FILESYSTEM_SPEC is None or _SECURE_FILESYSTEM_SPEC.loader is None:
    raise RuntimeError("secure filesystem sibling cannot be loaded")
secure_filesystem = importlib.util.module_from_spec(_SECURE_FILESYSTEM_SPEC)
sys.modules[_SECURE_FILESYSTEM_SPEC.name] = secure_filesystem
_SECURE_FILESYSTEM_SPEC.loader.exec_module(secure_filesystem)


SCHEMA_VERSION = "pontius-test-inventory-v1"
PROFILE_SCHEMA_VERSION = "pontius-test-profiles-v1"
REVIEW_SCHEMA_VERSION = "pontius-design-capability-review-v1"
RECEIPT_SCHEMA_VERSION = "pontius-design-capability-review-receipt-v1"
BASELINE_COMMIT = "a842c4b6a73a2991a63a481f4107580b72750582"
BASELINE_ROOT_TREE_OID = "80feb736d287bb271905b3eb7ee3a878e026cd62"
ZERO_SHA256 = "0" * 64
MAXIMUM_ARCHIVE_BYTES = 64 * 1024 * 1024
MAXIMUM_SOURCE_BYTES = 16 * 1024 * 1024
MAXIMUM_GIT_METADATA_BYTES = 4 * 1024 * 1024
_HEX40 = re.compile(r"[0-9a-f]{40}\Z")
_HEX64 = re.compile(r"[0-9a-f]{64}\Z")
_GOVERNANCE_ATTRIBUTE_PATHS = (
    "docs/architecture/dependency-baseline.toml",
    "tests/test-inventory.json",
    "tests/test-profiles.toml",
)
_RETAINED_BOUNDED_PROCESS_OWNERS: list[object] = []

V7_RETAINED_OVERLAYS = {
    "overlay:v7-retained:attempt": (
        "artifacts/work_preflight/"
        "legal_river_quotient_compiled_global_separation_calibration_v7.attempt.json",
        1825,
        "ada1896f0bf63111e0c1e5e707315fbca6c13f6e2b63222805cb5ef4cb9dc413",
    ),
    "overlay:v7-retained:consumed-launch": (
        "artifacts/work_preflight/"
        "legal_river_quotient_compiled_global_separation_calibration_v7.launch-consumed.json",
        349,
        "c3c0a34cba6a677157034d8f8109cf47edea496a33c64992293176d879a2d629",
    ),
    "overlay:v7-retained:result": (
        "artifacts/work_preflight/"
        "legal_river_quotient_compiled_global_separation_calibration_v7.jsonl",
        7_858_857,
        "78b2f8351ca49785756ec336d4f967bcc83a86f9ef96506a6144726cf3b312b3",
    ),
}
DESIGN_GPU_PROBE_ID = "probe:gpu-availability"
HISTORICAL_RETAINED_V7_PROBE_ID = "probe:v7-sealed-reader-retained"
REGISTERED_PROBE_IMPLEMENTATIONS = {
    DESIGN_GPU_PROBE_ID: ("tools/test_child.py", "_run_gpu_probe"),
}

BASELINE_LOCKS = {
    "test_file_count": 392,
    "stable_id_count": 2367,
    "stable_ids_sha256": "c8e6465527a9b784f4be41947745f6e86d53f45d16fd0d10955009bbb127b37b",
    "historical_id_count": 137,
    "historical_ids_sha256": "77ccf22ac1f52ebbeff7311bf2c4c1fb4f83671a5cfe10f84dbbde655ecb58a8",
    "gpu_id_count": 51,
    "gpu_ids_sha256": "896fb0675371186476df33b13eb7a5d9286dfeb01f53d37daa0f458e72021005",
    "core_id_count": 50,
    "core_ids_sha256": "38166290ad900c24a08c93f08de3376dac92a2c35544a94c3228726b01a02dfc",
    "current_id_count": 2129,
    "current_ids_sha256": "c32575a47a889e7e324db2abb56ef5c5b37295bb6a5cc3e6006cb04c767c6803",
    "explicit_exclusion_count": 0,
}

HISTORICAL_CLASSES = {
    "CompiledGlobalSeparationSourceSealTests": "historical:base-source",
    "AbsoluteGitCalibrationSuccessorTests": "historical:v2-source",
    "CompiledGlobalSeparationCalibrationV2OutcomeTests": "historical:v2-retained",
    "CompiledGlobalSeparationCalibrationV3Tests": "historical:v3-source",
    "CompiledGlobalSeparationCalibrationV4Tests": "historical:v4-positive",
    "CompiledGlobalSeparationCalibrationV5Tests": "historical:v5-retained",
    "CompiledGlobalSeparationCalibrationV6Tests": "historical:v6-phases",
    "CompiledGlobalSeparationCalibrationV7Tests": "historical:v7-phases",
}
V4_NEGATIVE_ID = (
    "tests/test_legal_river_quotient_compiled_global_separation_calibration_v4.py::"
    "CompiledGlobalSeparationCalibrationV4Tests::"
    "test_full_reader_journal_and_mutations_after_authorization"
)
CORE_FILES = {
    "tests/test_cfr.py",
    "tests/test_coalition.py",
    "tests/test_evaluation.py",
    "tests/test_holdem_cards.py",
    "tests/test_kuhn.py",
}
GPU_CURRENT_EXCEPTION = "SharedDirectDeviceSourceSealTests"
CUDA_DEVICE_CLASS = "LegalRiverQuotientCudaConsumerDeviceTests"
DECLARED_SKIPS = {
    (
        "tests/test_h32_pre_bet_action_width_capacity.py::"
        "H32PreBetActionWidthCapacityTests::"
        "test_small_runtime_composition_keeps_candidate_at_current_node"
    ): (
        "sealed rejected runner is retained byte-for-byte and never rerun",
        "sealed_rejected_runner_never_rerun",
        "50af0f964e7e6b2fd708e85b3cff20b9c073c3d8cb084b65033f333fefbf6f57",
    ),
    (
        "tests/test_h32_pre_bet_initial_row_cache_seed.py::"
        "H32PreBetInitialRowCacheSeedTests::"
        "test_small_gpu_seed_round_trips_both_distinct_arms_without_optimizer_work"
    ): (
        "ADR-0281 seed authority is revoked; its GPU path is never invoked",
        "revoked_adr_0281_gpu_path_never_invoked",
        "aa949216ccc291eab69a7eca888eb7e0fa5f43c804099bf6cf51c6fde9429909",
    ),
}
STABILIZATION_TEST_FILES = frozenset({
    "tests/evidence_test_support.py",
    "tests/orchestration_test_support.py",
    "tests/test_evidence_errors_and_model.py",
    "tests/test_evidence_manifests.py",
    "tests/test_evidence_manifest_generation.py",
    "tests/test_evidence_filesystem_and_git.py",
    "tests/test_evidence_authorization.py",
    "tests/test_retained_v7_assessment.py",
    "tests/test_evidence_import_boundary.py",
    "tests/test_test_orchestration_configuration.py",
    "tests/test_inventory_and_profiles.py",
    "tests/test_test_orchestration_protocol.py",
    "tests/test_test_orchestration_process.py",
    "tests/test_test_orchestration_windows_job.py",
    "tests/test_test_orchestration_posix_group.py",
    "tests/test_test_orchestration_environment.py",
    "tests/test_test_orchestration_child.py",
    "tests/test_test_orchestration_guards.py",
    "tests/test_test_orchestration_workspace.py",
    "tests/test_test_orchestration_historical.py",
    "tests/test_test_orchestration_engine.py",
    "tests/test_stabilization_boundaries.py",
    "tests/test_test_orchestration_import_boundary.py",
    "tests/test_stabilization_verification.py",
})


class InventoryError(RuntimeError):
    """Deterministic inventory/profile generation failure."""


@dataclass(frozen=True, slots=True)
class GitToolSnapshot:
    configured_executable: str
    resolved_executable: str
    platform_identity: tuple[int, ...]
    executable_sha256: str


@dataclass(slots=True)
class _GitLaunchLease:
    path: Path
    identity: tuple[int, ...]
    descriptor: int
    launch_executable: Path | None
    pass_fds: tuple[int, ...]

    def close(self) -> None:
        os.close(self.descriptor)


@dataclass(frozen=True, slots=True)
class TestMethod:
    relative_path: str
    case_name: str
    method_name: str
    decorator_dumps: tuple[str, ...]
    unconditional_skip_literal: str | None
    has_cupy_decorator: bool
    class_imports_cupy: bool

    @property
    def stable_id(self) -> str:
        return f"{self.relative_path}::{self.case_name}::{self.method_name}"


@dataclass(frozen=True, slots=True)
class LifecycleDefinition:
    kind: str
    relative_path: str
    class_name: str | None
    member_ids: tuple[str, ...]

    @property
    def fixture_id(self) -> str:
        suffix = "" if self.class_name is None else f"::{self.class_name}"
        return f"fixture:{self.relative_path}{suffix}"


@dataclass(frozen=True, slots=True)
class Discovery:
    methods: tuple[TestMethod, ...]
    lifecycle_fixtures: tuple[LifecycleDefinition, ...]
    source_paths: tuple[str, ...]

    @property
    def test_file_count(self) -> int:
        return len(self.source_paths)

    @property
    def items(self) -> tuple[TestMethod, ...]:
        return self.methods

    @property
    def stable_ids(self) -> tuple[str, ...]:
        return tuple(method.stable_id for method in self.methods)


@dataclass(frozen=True, slots=True)
class WorkingSourcesSnapshot:
    repository_root: Path
    tests_directory: Path
    tests_directory_identity: tuple[int, ...]
    sources: Mapping[str, bytes]
    file_snapshots: tuple[object, ...]
    include_support_modules: bool
    probe_source_names: tuple[str, ...]

    def revalidate(self) -> None:
        current_directory = _working_tests_directory_identity(self.tests_directory)
        if current_directory != self.tests_directory_identity:
            raise InventoryError("working tests directory identity changed")
        expected_sources = _working_source_names(
            self.tests_directory,
            include_support_modules=self.include_support_modules,
        ) + _registered_probe_source_names(
            self.repository_root,
            include=self.include_support_modules,
        )
        current_probe_sources = _registered_probe_source_names(
            self.repository_root,
            include=self.include_support_modules,
        )
        if (
            tuple(self.sources) != expected_sources
            or current_probe_sources != self.probe_source_names
        ):
            raise InventoryError("working test source set changed")
        for snapshot in self.file_snapshots:
            snapshot.revalidate()
        if (
            _working_tests_directory_identity(self.tests_directory)
            != self.tests_directory_identity
        ):
            raise InventoryError("working tests directory identity changed")


def _canonical_lf(raw: bytes) -> bytes:
    if raw.startswith(b"\xef\xbb\xbf"):
        raise InventoryError("governance/source bytes must not contain a UTF-8 BOM")
    return raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=True, separators=(",", ":"), sort_keys=True
    ).encode("ascii")


def _semantic_bytes(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=True, separators=(",", ":"), sort_keys=True
    ).encode("ascii")


def stable_ids_sha256(stable_ids: Iterable[str]) -> str:
    ordered = tuple(sorted(stable_ids))
    if len(set(ordered)) != len(ordered):
        raise InventoryError("stable IDs must be unique")
    return sha256(("\n".join(ordered) + ("\n" if ordered else "")).encode("utf-8")).hexdigest()


def _is_test_case_base(node: ast.expr) -> bool:
    return (
        isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "unittest"
        and node.attr == "TestCase"
    )


def _find_spec_cupy(node: ast.AST) -> bool:
    for candidate in ast.walk(node):
        if not isinstance(candidate, ast.Call) or not candidate.args:
            continue
        function = candidate.func
        if (
            isinstance(function, ast.Attribute)
            and function.attr == "find_spec"
            and isinstance(candidate.args[0], ast.Constant)
            and candidate.args[0].value == "cupy"
        ):
            return True
    return False


def _literal_unittest_skip(node: ast.expr) -> str | None:
    if not (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "unittest"
        and node.func.attr == "skip"
        and len(node.args) == 1
        and not node.keywords
        and isinstance(node.args[0], ast.Constant)
        and type(node.args[0].value) is str
    ):
        return None
    return node.args[0].value


def discover_test_sources(sources: Mapping[str, bytes]) -> Discovery:
    methods: list[TestMethod] = []
    fixtures: list[LifecycleDefinition] = []
    normalized_sources: dict[str, bytes] = {}
    for supplied_path, supplied_raw in sources.items():
        if type(supplied_path) is not str or type(supplied_raw) is not bytes:
            raise InventoryError("test sources must map string paths to exact bytes")
        path = PurePosixPath(supplied_path)
        if (
            path.as_posix() != supplied_path
            or len(path.parts) != 2
            or path.parts[0] != "tests"
            or not path.name.startswith("test")
            or path.suffix != ".py"
        ):
            raise InventoryError(f"test source path is not canonical: {supplied_path}")
        if supplied_path in normalized_sources:
            raise InventoryError(f"duplicate test source path: {supplied_path}")
        raw = _canonical_lf(supplied_raw)
        if len(raw) > MAXIMUM_SOURCE_BYTES:
            raise InventoryError(f"test source is oversized: {supplied_path}")
        normalized_sources[supplied_path] = raw
    for relative_path in sorted(normalized_sources):
        raw = normalized_sources[relative_path]
        try:
            tree = ast.parse(raw.decode("utf-8", errors="strict"), filename=relative_path)
        except (UnicodeDecodeError, SyntaxError) as error:
            raise InventoryError(f"test source cannot be parsed: {relative_path}") from error
        module_fixture = any(
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name in {"setUpModule", "tearDownModule"}
            for node in tree.body
        )
        module_members: list[str] = []
        for class_node in (node for node in tree.body if isinstance(node, ast.ClassDef)):
            if not any(_is_test_case_base(base) for base in class_node.bases):
                continue
            class_imports_cupy = any(
                (
                    isinstance(node, ast.Import)
                    and any(
                        alias.name == "cupy" or alias.name.startswith("cupy.")
                        for alias in node.names
                    )
                )
                or (isinstance(node, ast.ImportFrom) and node.module == "cupy")
                for node in ast.walk(class_node)
            )
            class_has_cupy_decorator = any(
                _find_spec_cupy(item) for item in class_node.decorator_list
            )
            class_methods: list[TestMethod] = []
            class_fixture = False
            for node in class_node.body:
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                if node.name in {"setUpClass", "tearDownClass"}:
                    class_fixture = True
                if not node.name.startswith("test_"):
                    continue
                literal = (
                    _literal_unittest_skip(node.decorator_list[0])
                    if node.decorator_list else None
                )
                method = TestMethod(
                    relative_path,
                    class_node.name,
                    node.name,
                    tuple(ast.dump(item, include_attributes=False) for item in node.decorator_list),
                    literal,
                    class_has_cupy_decorator
                    or any(_find_spec_cupy(item) for item in node.decorator_list),
                    class_imports_cupy,
                )
                class_methods.append(method)
                methods.append(method)
                module_members.append(method.stable_id)
            if class_fixture and class_methods:
                fixtures.append(LifecycleDefinition(
                    "class", relative_path, class_node.name,
                    tuple(sorted(item.stable_id for item in class_methods)),
                ))
            elif class_fixture:
                raise InventoryError(
                    "class lifecycle fixture has no direct test methods: "
                    f"{relative_path}::{class_node.name}"
                )
        if module_fixture and module_members:
            fixtures.append(LifecycleDefinition(
                "module", relative_path, None, tuple(sorted(module_members))
            ))
    methods.sort(key=lambda item: item.stable_id)
    if len({item.stable_id for item in methods}) != len(methods):
        raise InventoryError("test discovery produced duplicate stable IDs")
    fixtures.sort(key=lambda item: item.fixture_id)
    return Discovery(tuple(methods), tuple(fixtures), tuple(sorted(normalized_sources)))


def _profile_for(method: TestMethod) -> tuple[str, str]:
    historical = HISTORICAL_CLASSES.get(method.case_name)
    if historical is not None:
        if method.stable_id == V4_NEGATIVE_ID:
            historical = "historical:v4-authorization-negative"
        return "historical", historical
    gpu = (
        method.case_name != GPU_CURRENT_EXCEPTION
        and (
            method.has_cupy_decorator
            or method.class_imports_cupy
            or method.case_name == CUDA_DEVICE_CLASS
        )
    )
    stem = PurePosixPath(method.relative_path).stem
    if gpu:
        return "gpu", f"gpu:{stem}:{method.case_name}"
    if method.relative_path in CORE_FILES:
        return "core", f"core:{stem}"
    return "current", f"current:{stem}"


def _expectation(method: TestMethod, *, profile_name: str) -> dict[str, object]:
    if method.stable_id in DECLARED_SKIPS:
        literal, code, digest = DECLARED_SKIPS[method.stable_id]
        if (
            method.unconditional_skip_literal != literal
            or sha256(literal.encode("utf-8")).hexdigest() != digest
            or not method.has_cupy_decorator
        ):
            raise InventoryError(
                f"declared unconditional skip AST drifted: {method.stable_id}"
            )
        return {"kind": "declared_unconditional_skip", "skip_safe_reason_code": code}
    if method.unconditional_skip_literal is not None:
        raise InventoryError(f"unapproved unconditional skip: {method.stable_id}")
    if profile_name == "historical":
        return {"kind": "case_defined"}
    dumps = " ".join(method.decorator_dumps)
    if any(token in dumps for token in ("win32", "Windows", "name='nt'", "id='nt'")):
        return {
            "kind": "platform_conditioned",
            "applicable_platforms": ["windows"],
            "skip_safe_reason_code": "requires_windows",
        }
    if any(token in dumps for token in ("posix", "Linux")):
        return {
            "kind": "platform_conditioned",
            "applicable_platforms": ["posix"],
            "skip_safe_reason_code": "requires_posix",
        }
    return {"kind": "pass"}


def _assignment(method: TestMethod) -> dict[str, object]:
    profile_name, payload_id = _profile_for(method)
    return {
        "profile_name": profile_name,
        "payload_id": payload_id,
        "expectation": _expectation(method, profile_name=profile_name),
    }


def _discovery_row(discovery: Discovery) -> dict[str, object]:
    return {
        "test_file_count": len(discovery.source_paths),
        "stable_id_count": len(discovery.methods),
        "stable_ids_sha256": stable_ids_sha256(discovery.stable_ids),
    }


def build_inventory(
    baseline_sources: Mapping[str, bytes],
    working_sources: Mapping[str, bytes],
    *,
    enforce_baseline_lock: bool = False,
) -> dict[str, object]:
    baseline = discover_test_sources(baseline_sources)
    working = discover_test_sources(working_sources)
    baseline_row = _discovery_row(baseline)
    baseline_assignments = {
        method.stable_id: _assignment(method) for method in baseline.methods
    }
    groups = {name: [] for name in ("historical", "gpu", "core", "current")}
    for method in baseline.methods:
        groups[_profile_for(method)[0]].append(method.stable_id)
    baseline_row.update({
        "historical_id_count": len(groups["historical"]),
        "historical_ids_sha256": stable_ids_sha256(groups["historical"]),
        "gpu_id_count": len(groups["gpu"]),
        "gpu_ids_sha256": stable_ids_sha256(groups["gpu"]),
        "core_id_count": len(groups["core"]),
        "core_ids_sha256": stable_ids_sha256(groups["core"]),
        "current_id_count": len(groups["current"]),
        "current_ids_sha256": stable_ids_sha256(groups["current"]),
        "explicit_exclusion_count": 0,
    })
    if enforce_baseline_lock and baseline_row != BASELINE_LOCKS:
        raise InventoryError(f"baseline discovery/partition lock drifted: {baseline_row!r}")
    working_by_id = {method.stable_id: method for method in working.methods}
    if set(baseline_assignments) - set(working_by_id):
        raise InventoryError("a baseline stable ID is missing or changed in the working tree")
    introduced = sorted(set(working_by_id) - set(baseline_assignments))
    for stable_id in introduced:
        if working_by_id[stable_id].relative_path not in STABILIZATION_TEST_FILES:
            raise InventoryError(f"unreviewed stabilization test file: {stable_id}")
    if enforce_baseline_lock and set(working_by_id) & set(DECLARED_SKIPS) != set(DECLARED_SKIPS):
        raise InventoryError("approved declared-skip stable IDs are incomplete")
    entries: list[dict[str, object]] = []
    for method in working.methods:
        current_assignment = _assignment(method)
        if method.stable_id in baseline_assignments:
            assignment = baseline_assignments[method.stable_id]
            entry = {
                "stable_id": method.stable_id,
                "relative_path": method.relative_path,
                "case_name": method.case_name,
                "method_name": method.method_name,
                "assignment": assignment,
                "baseline_assignment": assignment,
            }
            # The baseline assignment is materialized. Mutable classification hints
            # are deliberately unable to reassign an existing stable ID.
        else:
            profile_name, payload_id = _profile_for(method)
            if profile_name != "current":
                raise InventoryError("post-baseline stabilization tests must be current-owned")
            entry = {
                "stable_id": method.stable_id,
                "relative_path": method.relative_path,
                "case_name": method.case_name,
                "method_name": method.method_name,
                "assignment": {
                    "profile_name": "current",
                    "payload_id": payload_id,
                    "expectation": _expectation(method, profile_name="current"),
                },
                "introduced_after_baseline": True,
            }
        entries.append(entry)
    discovery_row = _discovery_row(working)
    discovery_row.update({
        "introduced_id_count": len(introduced),
        "introduced_ids_sha256": stable_ids_sha256(introduced),
    })
    return {
        "schema_version": SCHEMA_VERSION,
        "baseline_commit": BASELINE_COMMIT,
        "baseline_discovery": baseline_row,
        "discovery": discovery_row,
        "entries": entries,
    }


def _toml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=True)


def _toml_array(values: Iterable[str]) -> str:
    return "[" + ", ".join(_toml_string(value) for value in values) + "]"


def _payload_rows(inventory: Mapping[str, object], discovery: Discovery) -> list[str]:
    entries = inventory["entries"]
    assert isinstance(entries, list)
    by_payload: dict[str, list[Mapping[str, object]]] = {}
    for entry in entries:
        assert isinstance(entry, Mapping)
        assignment = entry["assignment"]
        assert isinstance(assignment, Mapping)
        by_payload.setdefault(str(assignment["payload_id"]), []).append(entry)
    if "historical:v7-retained-probe" not in by_payload:
        by_payload["historical:v7-retained-probe"] = []
    if "gpu:availability-probe" not in by_payload:
        by_payload["gpu:availability-probe"] = []
    fixture_by_payload: dict[str, list[LifecycleDefinition]] = {}
    owner_by_id = {
        str(entry["stable_id"]): str(entry["assignment"]["payload_id"])
        for entry in entries
    }
    for fixture in discovery.lifecycle_fixtures:
        owners = {owner_by_id[item] for item in fixture.member_ids}
        if len(owners) != 1:
            raise InventoryError(f"lifecycle fixture spans payloads: {fixture.fixture_id}")
        fixture_by_payload.setdefault(owners.pop(), []).append(fixture)
    rows: list[str] = []
    for payload_id in sorted(by_payload):
        owned = by_payload[payload_id]
        if owned:
            profile_name = str(owned[0]["assignment"]["profile_name"])
        elif payload_id == "gpu:availability-probe":
            profile_name = "gpu"
        else:
            profile_name = "historical"
        target_kind = (
            "historical_clone"
            if profile_name == "historical"
            else "current_snapshot"
        )
        slots = (
            ["cpython311", "development"]
            if profile_name in {"core", "current"}
            else ["development"]
        )
        probes = {
            "gpu:availability-probe": [DESIGN_GPU_PROBE_ID],
            "historical:v7-retained-probe": [HISTORICAL_RETAINED_V7_PROBE_ID],
        }.get(payload_id, [])
        additions = (
            '{ PONTIUS_ADR0467_AUTH_READER_CHILD = "1" }'
            if payload_id == "historical:v4-authorization-negative" else "{}"
        )
        rows.extend([
            "[[payload]]",
            f"payload_id = {_toml_string(payload_id)}",
            f"profile_name = {_toml_string(profile_name)}",
            f"target_kind = {_toml_string(target_kind)}",
            f"allowed_interpreter_slots = {_toml_array(slots)}",
            f"probe_ids = {_toml_array(probes)}",
            f"environment_additions = {additions}",
            'environment_removals = ["PYTHONHOME", "PYTHONPATH", "PYTHONSTARTUP"]',
            'allowed_write_roots = ["temporary"]',
            'forbidden_relative_paths = ["artifacts/work_preflight"]',
            f"serialized = {'true' if profile_name == 'historical' else 'false'}",
        ])
        for fixture in sorted(
            fixture_by_payload.get(payload_id, ()),
            key=lambda item: item.fixture_id,
        ):
            rows.extend([
                "[[payload.lifecycle_fixture]]",
                f"fixture_id = {_toml_string(fixture.fixture_id)}",
                f"kind = {_toml_string(fixture.kind)}",
                f"relative_path = {_toml_string(fixture.relative_path)}",
            ])
            if fixture.class_name is not None:
                rows.append(f"class_name = {_toml_string(fixture.class_name)}")
            rows.extend([
                f"member_ids = {_toml_array(fixture.member_ids)}",
                'allowed_write_roots = ["temporary"]',
                'forbidden_relative_paths = ["artifacts/work_preflight"]',
                "serialized = true",
            ])
        rows.append("")
    return rows


SNAPSHOTS = {
    "base_source_seal": (
        "88148da07324c13b79c72ea494b14167a975c001",
        "bc5d1952f690da5d49275344919de36224af26cb",
    ),
    "v2_source_seal": (
        "08bb6857f47f9669b8f531c65079d4decd52a573",
        "0d01a4133a4e6ab10467ad0bd298630149702a73",
    ),
    "v2_retained_rejection": (
        "3de8e0c9eebf67f2cc2573041242a869468de6e9",
        "ea80b86ac60cb324e3c18ddad83d8bbba0ade933",
    ),
    "v3_source_seal": (
        "77feb7c78990ca53e70b1302a6866fe5d781411f",
        "d26ba99c033875342a652ae352067beee1ca44ee",
    ),
    "v4_source_seal": (
        "ba6a3418b7c991238cc1a65898fd61fa03b4a3cb",
        "73b53cb04c91459e8b7028ccd292b972d2dfdf69",
    ),
    "v4_authorization_rejection": (
        "815d23c115289347e3d4028a4866eb9f87d4669a",
        "894c026603156df4bba1134ba9861e98bd3a6663",
    ),
    "v5_retained_attempt": (
        "5c0c9a401e5f2ebf59296832d954d0075c4d4624",
        "f3418410c442a4d06c62aba9777def72633ca5c5",
    ),
    "v6_source_seal": (
        "d633f3fb469a27dee688587293c6efb1d2cb2757",
        "9c9ff658c2836bde5d1df71f5596d1d6aa1a5bd2",
    ),
    "v6_authorization_rejection": (
        "cbfa3598f22c7aba7d824f71356ca156f8b01b0c",
        "9873ff13131c91b058307643dc838a8452268fbb",
    ),
    "v7_source_seal": (
        "56127da2970f5a8a8056a97a247ebe1fdf4b983b",
        "ee2437ba1b2efbf2dc4ab3c21bbacdbf26c58648",
    ),
    "v7_live_authorization": (
        "aaca2dda40e29be8ebd091d58e7853bce1c62fd8",
        "e7bd077f40b1970e9b40a83c891996ab02cd5ffd",
    ),
}
CASE_PAYLOADS = {
    "base_source_seal": ("historical:base-source",),
    "v2_source_seal": ("historical:v2-source",),
    "v2_retained_rejection": ("historical:v2-retained",),
    "v3_source_seal": ("historical:v3-source",),
    "v4_source_seal": ("historical:v4-positive",),
    "v4_authorization_rejection": (
        "historical:v4-positive",
        "historical:v4-authorization-negative",
    ),
    "v5_retained_attempt": ("historical:v5-retained",),
    "v6_source_seal": ("historical:v6-phases",),
    "v6_authorization_rejection": ("historical:v6-phases",),
    "v7_source_seal": ("historical:v7-phases",),
    "v7_live_authorization": ("historical:v7-phases",),
    "v7_retained_probe": ("historical:v7-retained-probe",),
}


def _case_rows(inventory: Mapping[str, object]) -> list[str]:
    entries = inventory["entries"]
    assert isinstance(entries, list)
    by_payload: dict[str, list[str]] = {}
    for entry in entries:
        assignment = entry["assignment"]
        by_payload.setdefault(str(assignment["payload_id"]), []).append(str(entry["stable_id"]))
    by_payload["historical:v7-retained-probe"] = [
        HISTORICAL_RETAINED_V7_PROBE_ID
    ]
    rows: list[str] = []
    for phase, configured_payloads in CASE_PAYLOADS.items():
        payloads = tuple(sorted(configured_payloads))
        snapshot_phase = "v7_live_authorization" if phase == "v7_retained_probe" else phase
        commit, tree = SNAPSHOTS[snapshot_phase]
        item_ids = sorted(item for payload in payloads for item in by_payload[payload])
        v4_negative = phase == "v4_authorization_rejection"
        v6_negative = phase == "v6_authorization_rejection"
        overlay_ids = (
            sorted(V7_RETAINED_OVERLAYS)
            if phase == "v7_retained_probe"
            else []
        )
        if v4_negative:
            vector = (
                'expected_vector = { kind = "negative", passed = 38, '
                'assertion_failed = 0, setup_failed = 0, body_entered = 39, '
                'owner_calls = 0, scientific_calls = 0, phase = "body", '
                'exception_type = "ValueError", '
                'safe_reason_code = "deferred-import header domain differs" }'
            )
        elif v6_negative:
            vector = (
                'expected_vector = { kind = "negative", passed = 0, '
                'assertion_failed = 0, setup_failed = 17, body_entered = 0, '
                'owner_calls = 0, scientific_calls = 0, phase = "setup", '
                'exception_type = "AssertionError", '
                'safe_reason_code = "v6_authorization_path_present" }'
            )
        else:
            vector = (
                f'expected_vector = {{ kind = "positive", passed = {len(item_ids)}, '
                f'assertion_failed = 0, setup_failed = 0, body_entered = {len(item_ids)}, '
                'owner_calls = 0, scientific_calls = 0 }'
            )
        rows.extend([
            "[[historical_case]]",
            f"case_id = {_toml_string('case:' + phase)}",
            f"phase = {_toml_string(phase)}",
            f"commit = {_toml_string(commit)}",
            f"root_tree_oid = {_toml_string(tree)}",
            f"payload_ids = {_toml_array(payloads)}",
            f"overlay_ids = {_toml_array(overlay_ids)}",
            vector,
        ])
        for item_id in item_ids:
            rows.append("[[historical_case.item_expectation]]")
            rows.append(f"item_id = {_toml_string(item_id)}")
            if v4_negative and item_id == V4_NEGATIVE_ID:
                rows.extend([
                    'outcome = "expected_negative"',
                    'phase = "body"',
                    'exception_type = "ValueError"',
                    'safe_reason_code = "deferred-import header domain differs"',
                    "body_entered = true",
                    "capability_counters = {}",
                ])
            elif v6_negative:
                rows.extend([
                    'outcome = "expected_negative"',
                    'phase = "setup"',
                    'exception_type = "AssertionError"',
                    'safe_reason_code = "v6_authorization_path_present"',
                    "body_entered = false",
                    "capability_counters = {}",
                ])
            else:
                rows.append('outcome = "pass"')
        rows.append("")
    return rows


def render_profiles(inventory: Mapping[str, object], discovery: Discovery) -> bytes:
    entries = inventory["entries"]
    assert isinstance(entries, list)
    profile_payloads: dict[str, set[str]] = {
        name: set() for name in ("core", "current", "historical", "gpu")
    }
    for entry in entries:
        assignment = entry["assignment"]
        profile_payloads[str(assignment["profile_name"])].add(str(assignment["payload_id"]))
    profile_payloads["historical"].add("historical:v7-retained-probe")
    profile_payloads["gpu"].add("gpu:availability-probe")
    budgets = {
        "core": (180, 900, 15, 120, 1500),
        "current": (300, 7200, 15, 180, 8100),
        "historical": (900, 5400, 20, 300, 7200),
        "gpu": (300, 3600, 20, 180, 4500),
        "full": (900, 27000, 20, 300, 29000),
    }
    lines = [
        f'schema_version = "{PROFILE_SCHEMA_VERSION}"',
        f'baseline_commit = "{BASELINE_COMMIT}"',
        'sealed_current_files_manifest = "docs/architecture/sealed-current-files.toml"',
        'sealed_current_absences_manifest = "docs/architecture/sealed-current-absences.toml"',
        'historical_blobs_manifest = "docs/architecture/historical-blobs.toml"',
        'retained_v7_manifest = "docs/architecture/retained-v7.toml"',
        'inventory_path = "tests/test-inventory.json"',
        f'spec_capabilities_sha256 = "{ZERO_SHA256}"',
        f'capability_bindings_sha256 = "{ZERO_SHA256}"',
        f"stabilization_test_files = {_toml_array(sorted(STABILIZATION_TEST_FILES))}",
        "",
        "[[interpreter_slot]]",
        'name = "development"',
        'resolution = "repository_relative"',
        'windows_relative_path = ".venv/Scripts/python.exe"',
        'posix_relative_path = ".venv/bin/python"',
        'implementation = "cpython"',
        'minimum_version = [3, 11]',
        "required_for_full = true",
        "",
        "[[interpreter_slot]]",
        'name = "cpython311"',
        'resolution = "environment_absolute"',
        'environment_variable = "PONTIUS_CPYTHON311"',
        'implementation = "cpython"',
        'exact_version = [3, 11]',
        "required_for_full = true",
        "",
    ]
    for overlay_id in sorted(V7_RETAINED_OVERLAYS):
        relative_path, byte_length, raw_sha256 = V7_RETAINED_OVERLAYS[overlay_id]
        lines.extend([
            "[[overlay]]",
            f"overlay_id = {_toml_string(overlay_id)}",
            f"source_commit = {_toml_string(BASELINE_COMMIT)}",
            f"source_path = {_toml_string(relative_path)}",
            f"destination_path = {_toml_string(relative_path)}",
            f"byte_length = {byte_length}",
            f"raw_sha256 = {_toml_string(raw_sha256)}",
            "",
        ])
    for name in ("core", "current", "historical", "gpu", "full"):
        setup, child, termination, cleanup, total = budgets[name]
        direct = name != "full"
        slots = (
            ["cpython311", "development"]
            if name in {"core", "current", "full"}
            else ["development"]
        )
        cases = (
            sorted("case:" + phase for phase in CASE_PAYLOADS)
            if name == "historical"
            else []
        )
        lines.extend([
            "[[profile]]", f'name = "{name}"', f"interpreter_slots = {_toml_array(slots)}",
        ])
        if direct:
            lines.append('default_interpreter_slot = "development"')
        lines.extend([
            "payload_ids = "
            f"{_toml_array(sorted(profile_payloads.get(name, ()) if direct else ()))}",
            f"historical_case_ids = {_toml_array(cases)}",
            "subprofiles = "
            f"{_toml_array([] if direct else ['core', 'current', 'gpu', 'historical'])}",
            f"gpu_optional = {'true' if name == 'full' else 'false'}",
            "[profile.budgets]",
            f"setup_seconds = {setup}",
            f"child_seconds = {child}",
            f"termination_seconds = {termination}",
            f"cleanup_seconds = {cleanup}",
            f"total_seconds = {total}",
            "",
        ])
    lines.extend(_payload_rows(inventory, discovery))
    lines.extend(_case_rows(inventory))
    lines.extend([
        "# BEGIN GENERATED DESIGN SCOPE",
        "# END GENERATED DESIGN SCOPE",
        "# BEGIN GENERATED HISTORICAL SCOPE",
        "# END GENERATED HISTORICAL SCOPE",
        "",
    ])
    return "\n".join(lines).encode("ascii")


def _git_path_stat(path: Path) -> os.stat_result:
    return os.lstat(path)


def _git_stat_identity(info: os.stat_result) -> tuple[int, ...]:
    return (
        int(info.st_dev), int(info.st_ino), int(info.st_size),
        int(info.st_mtime_ns), int(info.st_ctime_ns), int(info.st_mode),
        int(getattr(info, "st_file_attributes", 0)),
        int(getattr(info, "st_reparse_tag", 0)),
    )


def _read_git_bytes(path: Path, before_path: os.stat_result) -> bytes:
    descriptor = secure_filesystem._open_regular_no_follow(path)
    primary_failure: BaseException | None = None
    raw = b""
    try:
        metadata = (
            secure_filesystem._windows_regular_handle_metadata(descriptor, path)
            if os.name == "nt" else None
        )
        if metadata is not None and (metadata[0] & 0x400 or metadata[1]):
            raise InventoryError("PONTIUS_GIT opened handle is a reparse")
        before_handle = os.fstat(descriptor)
        path_core = (
            int(before_path.st_dev), int(before_path.st_ino),
            int(before_path.st_size), int(before_path.st_mtime_ns),
        )
        handle_core = (
            int(before_handle.st_dev), int(before_handle.st_ino),
            int(before_handle.st_size), int(before_handle.st_mtime_ns),
        )
        if path_core != handle_core or not stat.S_ISREG(before_handle.st_mode):
            raise InventoryError("PONTIUS_GIT identity changed while opening")
        chunks: list[bytes] = []
        remaining = 64 * 1024 * 1024 + 1
        while remaining:
            chunk = os.read(descriptor, min(1024 * 1024, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        raw = b"".join(chunks)
        after_handle = os.fstat(descriptor)
        after_metadata = (
            secure_filesystem._windows_regular_handle_metadata(descriptor, path)
            if os.name == "nt" else None
        )
        if (
            len(raw) > 64 * 1024 * 1024
            or len(raw) != before_handle.st_size
            or secure_filesystem._file_identity(before_handle, windows_metadata=metadata)
            != secure_filesystem._file_identity(after_handle, windows_metadata=after_metadata)
        ):
            raise InventoryError("PONTIUS_GIT identity changed while reading")
    except BaseException as error:
        primary_failure = error
    close_failure: BaseException | None = None
    try:
        os.close(descriptor)
    except BaseException as error:
        close_failure = error
    if primary_failure is not None:
        if close_failure is not None:
            raise InventoryError(
                "PONTIUS_GIT read and cleanup both failed"
            ) from ExceptionGroup(
                "PONTIUS_GIT read and close failures",
                (primary_failure, close_failure),
            )
        raise primary_failure
    if close_failure is not None:
        raise InventoryError("PONTIUS_GIT handle could not be closed") from close_failure
    return raw


def _git_ancestor_chain(path: Path) -> tuple[tuple[Path, tuple[int, ...]], ...]:
    chain: list[tuple[Path, tuple[int, ...]]] = []
    for ancestor in path.parents:
        if ancestor == ancestor.parent:
            continue
        info = os.lstat(ancestor)
        if (
            stat.S_ISLNK(info.st_mode)
            or secure_filesystem._is_any_reparse(info)
            or not stat.S_ISDIR(info.st_mode)
        ):
            raise InventoryError("PONTIUS_GIT ancestor is a link or reparse")
        chain.append((ancestor, _git_stat_identity(info)))
    return tuple(chain)


def _revalidate_git_ancestor_chain(
    chain: Sequence[tuple[Path, tuple[int, ...]]],
) -> None:
    for ancestor, expected in chain:
        info = os.lstat(ancestor)
        if (
            stat.S_ISLNK(info.st_mode)
            or secure_filesystem._is_any_reparse(info)
            or not stat.S_ISDIR(info.st_mode)
            or _git_stat_identity(info) != expected
        ):
            raise InventoryError("PONTIUS_GIT ancestor identity changed")


def resolve_git_tool(configured: str | None) -> GitToolSnapshot:
    if type(configured) is not str or not configured.strip():
        raise InventoryError("PONTIUS_GIT must name an absolute executable")
    path = Path(configured)
    if not path.is_absolute():
        raise InventoryError("PONTIUS_GIT must name an absolute executable")
    supplied = Path(os.path.abspath(path))
    try:
        ancestors = _git_ancestor_chain(supplied)
        before = _git_path_stat(supplied)
    except OSError as error:
        raise InventoryError("PONTIUS_GIT cannot be inspected") from error
    if (
        stat.S_ISLNK(before.st_mode)
        or secure_filesystem._is_any_reparse(before)
        or not stat.S_ISREG(before.st_mode)
    ):
        raise InventoryError("PONTIUS_GIT must be a regular nonlink nonreparse file")
    if os.name != "nt" and not os.access(supplied, os.X_OK):
        raise InventoryError("PONTIUS_GIT must be executable")
    try:
        resolved = supplied.resolve(strict=True)
        raw = _read_git_bytes(supplied, before)
        after = _git_path_stat(supplied)
        _revalidate_git_ancestor_chain(ancestors)
    except Exception as error:
        raise InventoryError("PONTIUS_GIT identity cannot be measured") from error
    if (
        os.path.normcase(str(resolved)) != os.path.normcase(str(supplied))
        or _git_stat_identity(before) != _git_stat_identity(after)
    ):
        raise InventoryError("PONTIUS_GIT identity changed during measurement")
    return GitToolSnapshot(
        str(supplied), str(resolved), _git_stat_identity(after), sha256(raw).hexdigest()
    )


def _strict_git_snapshot(path: Path) -> tuple[Path, bytes, tuple[int, ...]]:
    identity = resolve_git_tool(str(path))
    supplied = Path(identity.resolved_executable)
    try:
        before = _git_path_stat(supplied)
        raw = _read_git_bytes(supplied, before)
        after = _git_path_stat(supplied)
    except Exception as error:
        raise InventoryError("PONTIUS_GIT must be a regular identity-bound file") from error
    if (
        _git_stat_identity(before) != identity.platform_identity
        or _git_stat_identity(after) != identity.platform_identity
        or sha256(raw).hexdigest() != identity.executable_sha256
    ):
        raise InventoryError("PONTIUS_GIT identity changed after resolution")
    return supplied, raw, identity.platform_identity


def _acquire_git_launch_lease(
    path: Path,
    expected_identity: tuple[int, ...],
) -> _GitLaunchLease:
    before = _git_path_stat(path)
    if _git_stat_identity(before) != expected_identity:
        raise InventoryError("PONTIUS_GIT changed before launch lease acquisition")
    descriptor: int | None = None
    try:
        if os.name == "nt":
            create, _, close = secure_filesystem._windows_path_api()
            handle = create(
                str(path),
                0x80000000,
                0x00000001,
                None,
                3,
                0x00200000 | 0x08000000,
                None,
            )
            invalid = secure_filesystem.ctypes.c_void_p(-1).value
            if not handle or int(handle) == invalid:
                code = secure_filesystem.ctypes.get_last_error()
                raise OSError(code, os.strerror(code), str(path))
            try:
                descriptor = secure_filesystem.msvcrt.open_osfhandle(
                    int(handle),
                    os.O_RDONLY | getattr(os, "O_BINARY", 0),
                )
            except BaseException:
                close(secure_filesystem.wintypes.HANDLE(int(handle)))
                raise
            launch_executable = None
            pass_fds: tuple[int, ...] = ()
        else:
            if not hasattr(os, "O_NOFOLLOW"):
                raise InventoryError("PONTIUS_GIT no-follow launch is unavailable")
            descriptor = os.open(
                path,
                os.O_RDONLY
                | os.O_NOFOLLOW
                | getattr(os, "O_NONBLOCK", 0)
                | getattr(os, "O_CLOEXEC", 0),
            )
            candidates = (
                Path(f"/proc/self/fd/{descriptor}"),
                Path(f"/dev/fd/{descriptor}"),
            )
            launch_executable = next(
                (candidate for candidate in candidates if candidate.exists()),
                None,
            )
            if launch_executable is None:
                raise InventoryError("PONTIUS_GIT descriptor launch is unavailable")
            pass_fds = (descriptor,)
        handle_info = os.fstat(descriptor)
        after = _git_path_stat(path)
        handle_identity = (
            int(handle_info.st_dev),
            int(handle_info.st_ino),
            int(handle_info.st_size),
            int(handle_info.st_mtime_ns),
            int(handle_info.st_ctime_ns),
            int(handle_info.st_mode),
        )
        core_length = 4 if os.name == "nt" else 6
        if (
            not stat.S_ISREG(handle_info.st_mode)
            or handle_identity[:core_length]
            != expected_identity[:core_length]
            or _git_stat_identity(after) != expected_identity
        ):
            raise InventoryError("PONTIUS_GIT launch lease identity changed")
        return _GitLaunchLease(
            path,
            expected_identity,
            descriptor,
            launch_executable,
            pass_fds,
        )
    except BaseException as error:
        if descriptor is not None:
            try:
                os.close(descriptor)
            except BaseException as close_error:
                raise InventoryError(
                    "PONTIUS_GIT launch lease and cleanup both failed"
                ) from ExceptionGroup(
                    "PONTIUS_GIT launch lease failures",
                    (error, close_error),
                )
        if isinstance(error, InventoryError):
            raise
        raise InventoryError("PONTIUS_GIT launch lease failed") from error


def _revalidate_git_launch_lease(lease: _GitLaunchLease) -> None:
    handle_info = os.fstat(lease.descriptor)
    path_info = _git_path_stat(lease.path)
    handle_identity = (
        int(handle_info.st_dev),
        int(handle_info.st_ino),
        int(handle_info.st_size),
        int(handle_info.st_mtime_ns),
        int(handle_info.st_ctime_ns),
        int(handle_info.st_mode),
    )
    if (
        handle_identity[: (4 if os.name == "nt" else 6)]
        != lease.identity[: (4 if os.name == "nt" else 6)]
        or _git_stat_identity(path_info) != lease.identity
    ):
        raise InventoryError("PONTIUS_GIT launch lease changed")


def _git_environment(git: Path, temporary: Path) -> dict[str, str]:
    folded = {key.casefold(): value for key, value in os.environ.items()}
    result: dict[str, str] = {}
    for key in ("SystemRoot", "WINDIR", "ComSpec", "PATHEXT"):
        value = folded.get(key.casefold())
        if value is not None:
            result[key] = value
    result.update({
        "PATH": (
            os.pathsep.join(
                (
                    str(git.parent),
                    str(Path(os.environ.get("SystemRoot", "/")) / "System32"),
                )
            )
            if os.name == "nt"
            else os.pathsep.join((str(git.parent), "/usr/bin", "/bin"))
        ),
        "TEMP": str(temporary),
        "TMP": str(temporary),
        "HOME": str(temporary),
        "USERPROFILE": str(temporary),
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": "NUL" if os.name == "nt" else "/dev/null",
        "GIT_NO_REPLACE_OBJECTS": "1", "GIT_LITERAL_PATHSPECS": "1",
    })
    return result


def _run_git_metadata(
    lease: _GitLaunchLease,
    repository_root: Path,
    environment: Mapping[str, str],
    arguments: Sequence[str],
) -> bytes:
    _revalidate_git_launch_lease(lease)
    return_code, stdout, stderr = _run_bounded_process(
        lease.path,
        repository_root,
        environment,
        arguments,
        b"",
        stdout_limit=MAXIMUM_GIT_METADATA_BYTES,
        stderr_limit=MAXIMUM_GIT_METADATA_BYTES,
        timeout_seconds=120,
        launch_executable=lease.launch_executable,
        pass_fds=lease.pass_fds,
    )
    _revalidate_git_launch_lease(lease)
    if return_code != 0 or stderr:
        raise InventoryError("Git object metadata command was not exact and bounded")
    return stdout


def _parse_git_tree(raw: bytes) -> tuple[tuple[str, str], ...]:
    if not raw or not raw.endswith(b"\0") or raw.startswith(b"\0") or b"\0\0" in raw:
        raise InventoryError("Git tree records require exactly one terminal NUL")
    rows: list[tuple[str, str]] = []
    seen_paths: set[str] = set()
    for encoded in raw[:-1].split(b"\0"):
        try:
            metadata, path_raw = encoded.split(b"\t", 1)
            mode, kind, oid = metadata.decode("ascii").split(" ")
            relative = path_raw.decode("utf-8", errors="strict")
        except (UnicodeDecodeError, ValueError) as error:
            raise InventoryError("Git tree row is malformed") from error
        path = PurePosixPath(relative)
        if (
            mode not in {"100644", "100755"}
            or kind != "blob"
            or _HEX40.fullmatch(oid) is None
            or path.is_absolute()
            or len(path.parts) != 2
            or path.parts[0] != "tests"
            or ".." in path.parts
            or relative != path.as_posix()
            or relative in seen_paths
        ):
            raise InventoryError("Git tree row violates the baseline source contract")
        seen_paths.add(relative)
        if path.name.startswith("test") and path.suffix == ".py":
            rows.append((relative, oid))
    if tuple(rows) != tuple(sorted(rows)) or not rows:
        raise InventoryError("Git tree test sources are absent or not sorted")
    return tuple(rows)


def _verify_governance_attributes(
    lease: _GitLaunchLease,
    repository_root: Path,
    environment: Mapping[str, str],
) -> None:
    raw = _run_git_metadata(
        lease,
        repository_root,
        environment,
        (
            "check-attr",
            "-z",
            "text",
            "eol",
            "--",
            *_GOVERNANCE_ATTRIBUTE_PATHS,
        ),
    )
    expected = b"".join(
        path.encode("ascii")
        + b"\0text\0set\0"
        + path.encode("ascii")
        + b"\0eol\0lf\0"
        for path in _GOVERNANCE_ATTRIBUTE_PATHS
    )
    if raw != expected:
        raise InventoryError(
            "effective governance attributes must be exactly text eol=lf"
        )


def _read_git_object_batch(
    lease: _GitLaunchLease,
    repository_root: Path,
    environment: Mapping[str, str],
    rows: Sequence[tuple[str, str, str]],
    *,
    maximum_bytes: int = MAXIMUM_ARCHIVE_BYTES,
) -> dict[str, bytes]:
    if (
        not rows
        or len({label for label, _, _ in rows}) != len(rows)
        or any(
            _HEX40.fullmatch(oid) is None
            or kind not in {"blob", "commit", "tree"}
            for _, oid, kind in rows
        )
    ):
        raise InventoryError("Git object request is invalid")
    request = "".join(f"{oid}\n" for _, oid, _ in rows).encode("ascii")
    maximum_output = maximum_bytes + len(rows) * 128
    _revalidate_git_launch_lease(lease)
    return_code, stdout, stderr = _run_bounded_process(
        lease.path,
        repository_root,
        environment,
        ("cat-file", "--batch"),
        request,
        stdout_limit=maximum_output,
        stderr_limit=MAXIMUM_GIT_METADATA_BYTES,
        timeout_seconds=120,
        launch_executable=lease.launch_executable,
        pass_fds=lease.pass_fds,
    )
    _revalidate_git_launch_lease(lease)
    if return_code != 0 or stderr:
        raise InventoryError("Git blob reader did not complete exactly and bounded")
    stream = memoryview(stdout)
    offset = 0
    objects: dict[str, bytes] = {}
    total = 0
    for label, expected_oid, expected_kind in rows:
        line_end = stdout.find(b"\n", offset, offset + 256)
        if line_end < 0:
            raise InventoryError("Git blob header is absent or oversized")
        try:
            oid, kind, size_text = bytes(stream[offset:line_end]).decode("ascii").split(" ")
            size = int(size_text)
        except (UnicodeDecodeError, ValueError) as error:
            raise InventoryError("Git blob header is malformed") from error
        offset = line_end + 1
        if (
            oid != expected_oid
            or kind != expected_kind
            or size < 0
            or size > maximum_bytes
            or total + size > maximum_bytes
            or offset + size >= len(stream)
        ):
            raise InventoryError("Git object identity or size is invalid")
        raw = bytes(stream[offset : offset + size])
        framed = kind.encode("ascii") + b" " + str(size).encode("ascii")
        framed += b"\0" + raw
        if sha1(framed).hexdigest() != expected_oid:
            raise InventoryError("Git object bytes do not match the identifier")
        objects[label] = raw
        offset += size
        if stream[offset] != 0x0A:
            raise InventoryError("Git blob record terminator is invalid")
        offset += 1
        total += size
    if offset != len(stream):
        raise InventoryError("Git blob stream contains extra output")
    return objects


def _read_git_blob_batch(
    lease: _GitLaunchLease,
    repository_root: Path,
    environment: Mapping[str, str],
    rows: Sequence[tuple[str, str]],
) -> dict[str, bytes]:
    requests = [(relative, oid, "blob") for relative, oid in rows]
    return _read_git_object_batch(
        lease,
        repository_root,
        environment,
        requests,
    )


def _parse_raw_git_tree(raw: bytes) -> tuple[tuple[str, str, str], ...]:
    rows: list[tuple[str, str, str]] = []
    offset = 0
    seen: set[str] = set()
    while offset < len(raw):
        separator = raw.find(b" ", offset, offset + 16)
        terminator = raw.find(b"\0", separator + 1)
        if separator < 0 or terminator < 0 or terminator + 21 > len(raw):
            raise InventoryError("raw Git tree record is truncated")
        try:
            mode = raw[offset:separator].decode("ascii")
            name = raw[separator + 1 : terminator].decode("utf-8")
        except UnicodeDecodeError as error:
            raise InventoryError("raw Git tree record is not canonical text") from error
        oid = raw[terminator + 1 : terminator + 21].hex()
        if (
            mode not in {"40000", "100644", "100755"}
            or not name
            or name in {".", ".."}
            or "/" in name
            or "\0" in name
            or name in seen
            or _HEX40.fullmatch(oid) is None
        ):
            raise InventoryError("raw Git tree record violates the source contract")
        seen.add(name)
        rows.append((mode, name, oid))
        offset = terminator + 21
    if not rows:
        raise InventoryError("raw Git tree is empty")
    return tuple(rows)


def _raw_git_test_rows(
    lease: _GitLaunchLease,
    repository_root: Path,
    environment: Mapping[str, str],
    root_tree_oid: str,
) -> tuple[tuple[str, str], ...]:
    root_raw = _read_git_object_batch(
        lease,
        repository_root,
        environment,
        (("root", root_tree_oid, "tree"),),
        maximum_bytes=MAXIMUM_GIT_METADATA_BYTES,
    )["root"]
    root_rows = _parse_raw_git_tree(root_raw)
    test_entries = [row for row in root_rows if row[1] == "tests"]
    if len(test_entries) != 1 or test_entries[0][0] != "40000":
        raise InventoryError("baseline root tree lacks one exact tests directory")
    tests_tree_oid = test_entries[0][2]
    tests_raw = _read_git_object_batch(
        lease,
        repository_root,
        environment,
        (("tests", tests_tree_oid, "tree"),),
        maximum_bytes=MAXIMUM_GIT_METADATA_BYTES,
    )["tests"]
    rows: list[tuple[str, str]] = []
    for mode, name, oid in _parse_raw_git_tree(tests_raw):
        path = PurePosixPath("tests", name)
        if mode == "40000":
            raise InventoryError("baseline test sources must be direct files")
        if path.name.startswith("test") and path.suffix == ".py":
            rows.append((path.as_posix(), oid))
    rows.sort()
    if not rows:
        raise InventoryError("baseline test sources are absent")
    return tuple(rows)


def _run_bounded_process(
    executable: Path,
    cwd: Path,
    environment: Mapping[str, str],
    arguments: Sequence[str],
    stdin_bytes: bytes,
    *,
    stdout_limit: int,
    stderr_limit: int,
    timeout_seconds: float,
    launch_executable: Path | None = None,
    pass_fds: tuple[int, ...] = (),
) -> tuple[int, bytes, bytes]:
    if (
        stdout_limit < 0
        or stderr_limit < 0
        or timeout_seconds <= 0
        or type(stdin_bytes) is not bytes
    ):
        raise InventoryError("bounded process limits are invalid")
    try:
        popen_options: dict[str, object] = {}
        if launch_executable is not None:
            popen_options["executable"] = str(launch_executable)
        if pass_fds:
            popen_options["pass_fds"] = pass_fds
        process = subprocess.Popen(
            [str(executable), *arguments],
            cwd=cwd,
            env=dict(environment),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            **popen_options,
        )
    except OSError as error:
        raise InventoryError("bounded process could not start") from error
    if process.stdin is None or process.stdout is None or process.stderr is None:
        raise InventoryError("bounded process pipes are absent")
    overflow = threading.Event()
    reader_failures: list[BaseException] = []
    writer_failures: list[BaseException] = []
    outputs: dict[str, list[bytes]] = {"stdout": [], "stderr": []}

    def drain(name: str, stream: Any, limit: int) -> None:
        total = 0
        try:
            while True:
                chunk = stream.read(64 * 1024)
                if not chunk:
                    return
                remaining = limit - total
                if len(chunk) > remaining:
                    if remaining > 0:
                        outputs[name].append(chunk[:remaining])
                    overflow.set()
                    return
                outputs[name].append(chunk)
                total += len(chunk)
        except BaseException as error:
            reader_failures.append(error)

    def feed() -> None:
        try:
            offset = 0
            while offset < len(stdin_bytes):
                written = process.stdin.write(stdin_bytes[offset : offset + 64 * 1024])
                if written is None or written <= 0:
                    raise InventoryError(
                        "bounded process input write made no progress"
                    )
                offset += written
            process.stdin.close()
        except BaseException as error:
            writer_failures.append(error)

    readers = (
        threading.Thread(
            target=drain,
            args=("stdout", process.stdout, stdout_limit),
            daemon=True,
        ),
        threading.Thread(
            target=drain,
            args=("stderr", process.stderr, stderr_limit),
            daemon=True,
        ),
    )
    for reader in readers:
        reader.start()
    writer = threading.Thread(target=feed, daemon=True)
    writer.start()
    primary_failure: BaseException | None = None
    deadline = time.monotonic() + timeout_seconds
    try:
        while process.poll() is None:
            if overflow.is_set():
                raise InventoryError("bounded process exceeded its output limit")
            if time.monotonic() >= deadline:
                raise InventoryError("bounded process timed out")
            overflow.wait(0.01)
        if overflow.is_set():
            raise InventoryError("bounded process exceeded its output limit")
    except BaseException as error:
        primary_failure = error
    cleanup_failures: list[BaseException] = []
    if primary_failure is not None and process.poll() is None:
        try:
            process.terminate()
        except BaseException as error:
            cleanup_failures.append(error)
        try:
            process.wait(timeout=1)
        except subprocess.TimeoutExpired as error:
            cleanup_failures.append(error)
            try:
                process.kill()
            except BaseException as kill_error:
                cleanup_failures.append(kill_error)
            else:
                try:
                    process.wait(timeout=1)
                except BaseException as wait_error:
                    cleanup_failures.append(wait_error)
        except BaseException as error:
            cleanup_failures.append(error)
    cleanup_deadline = time.monotonic() + 5
    for thread in (*readers, writer):
        thread.join(timeout=max(0, cleanup_deadline - time.monotonic()))
    if primary_failure is None and writer.is_alive():
        primary_failure = InventoryError(
            "bounded process exited before consuming its exact input"
        )
    if primary_failure is None and any(reader.is_alive() for reader in readers):
        primary_failure = InventoryError(
            "bounded process descendant retained an output pipe"
        )
    retained_threads = tuple(
        thread for thread in (*readers, writer) if thread.is_alive()
    )
    if retained_threads:
        cleanup_failures.append(
            InventoryError("bounded process thread cleanup did not complete")
        )
        _RETAINED_BOUNDED_PROCESS_OWNERS.append(
            (process, readers, writer)
        )
    for reader, stream in zip(
        readers,
        (process.stdout, process.stderr),
        strict=True,
    ):
        if reader.is_alive():
            continue
        try:
            stream.close()
        except BaseException as error:
            cleanup_failures.append(error)
    if not writer.is_alive():
        try:
            process.stdin.close()
        except BaseException as error:
            cleanup_failures.append(error)
    cleanup_failures.extend(reader_failures)
    cleanup_failures.extend(writer_failures)
    if primary_failure is not None:
        if cleanup_failures:
            raise InventoryError(
                "bounded process body and cleanup both failed"
            ) from ExceptionGroup(
                "bounded process failures",
                (primary_failure, *cleanup_failures),
            )
        raise primary_failure
    if cleanup_failures:
        raise InventoryError("bounded process cleanup failed") from ExceptionGroup(
            "bounded process cleanup failures",
            tuple(cleanup_failures),
        )
    return (
        int(process.returncode),
        b"".join(outputs["stdout"]),
        b"".join(outputs["stderr"]),
    )


def _git_blob_sources(
    repository_root: Path,
    git_path: Path,
    *,
    commit: str,
    root_tree_oid: str,
    verify_governance_attributes: bool = False,
) -> dict[str, bytes]:
    if _HEX40.fullmatch(commit) is None or _HEX40.fullmatch(root_tree_oid) is None:
        raise InventoryError("Git baseline commit/tree identity is invalid")
    git, raw_identity, identity = _strict_git_snapshot(git_path)
    lease = _acquire_git_launch_lease(git, identity)
    primary_failure: BaseException | None = None
    sources: dict[str, bytes] = {}
    try:
        with tempfile.TemporaryDirectory(
            prefix="pontius-inventory-git-"
        ) as temporary_text:
            temporary = Path(temporary_text)
            environment = _git_environment(git, temporary)
            if verify_governance_attributes:
                _verify_governance_attributes(
                    lease,
                    repository_root,
                    environment,
                )
            commit_raw = _read_git_object_batch(
                lease,
                repository_root,
                environment,
                (("commit", commit, "commit"),),
                maximum_bytes=MAXIMUM_GIT_METADATA_BYTES,
            )["commit"]
            first_line = commit_raw.partition(b"\n")[0]
            if first_line != f"tree {root_tree_oid}".encode("ascii"):
                raise InventoryError(
                    "baseline commit does not bind the approved root tree"
                )
            rows = _raw_git_test_rows(
                lease,
                repository_root,
                environment,
                root_tree_oid,
            )
            sources = _read_git_blob_batch(
                lease,
                repository_root,
                environment,
                rows,
            )
            if verify_governance_attributes:
                _verify_governance_attributes(
                    lease,
                    repository_root,
                    environment,
                )
            _revalidate_git_launch_lease(lease)
    except BaseException as error:
        primary_failure = error
    close_failure: BaseException | None = None
    try:
        lease.close()
    except BaseException as error:
        close_failure = error
    if primary_failure is not None:
        if close_failure is not None:
            raise InventoryError(
                "Git acquisition and launch-lease cleanup both failed"
            ) from ExceptionGroup(
                "Git acquisition failures",
                (primary_failure, close_failure),
            )
        raise primary_failure
    if close_failure is not None:
        raise InventoryError("Git launch lease cleanup failed") from close_failure
    after_git, after_raw, after_identity = _strict_git_snapshot(git_path)
    if after_git != git or after_raw != raw_identity or after_identity != identity:
        raise InventoryError("PONTIUS_GIT identity changed during baseline acquisition")
    return sources


def _baseline_sources(repository_root: Path, git_path: Path) -> dict[str, bytes]:
    return _git_blob_sources(
        repository_root,
        git_path,
        commit=BASELINE_COMMIT,
        root_tree_oid=BASELINE_ROOT_TREE_OID,
        verify_governance_attributes=True,
    )


def _with_governance_attribute_lease(
    repository_root: Path,
    git_path: Path,
    action: Any,
) -> object:
    git, raw_identity, identity = _strict_git_snapshot(git_path)
    lease = _acquire_git_launch_lease(git, identity)
    primary_failure: BaseException | None = None
    result: object | None = None
    try:
        with tempfile.TemporaryDirectory(
            prefix="pontius-governance-attributes-"
        ) as temporary_text:
            environment = _git_environment(git, Path(temporary_text))

            def revalidate() -> None:
                _verify_governance_attributes(
                    lease,
                    repository_root,
                    environment,
                )
                _revalidate_git_launch_lease(lease)

            revalidate()
            result = action(revalidate)
    except BaseException as error:
        primary_failure = error
    close_failure: BaseException | None = None
    try:
        lease.close()
    except BaseException as error:
        close_failure = error
    if primary_failure is not None:
        if close_failure is not None:
            raise InventoryError(
                "governance attribute action and cleanup both failed"
            ) from ExceptionGroup(
                "governance attribute action failures",
                (primary_failure, close_failure),
            )
        raise primary_failure
    if close_failure is not None:
        raise InventoryError("governance attribute lease cleanup failed") from close_failure
    after_git, after_raw, after_identity = _strict_git_snapshot(git_path)
    if after_git != git or after_raw != raw_identity or after_identity != identity:
        raise InventoryError("PONTIUS_GIT changed during governance publication")
    return result


def _working_tests_directory_identity(tests: Path) -> tuple[int, ...]:
    try:
        info = os.lstat(tests)
    except OSError as error:
        raise InventoryError("working tests directory cannot be inspected") from error
    if (
        stat.S_ISLNK(info.st_mode)
        or secure_filesystem._is_disallowed_reparse(info)
        or not stat.S_ISDIR(info.st_mode)
    ):
        raise InventoryError("working tests path is not a secure directory")
    return secure_filesystem._directory_identity(info)


def _working_source_names(
    tests: Path,
    *,
    include_support_modules: bool = False,
) -> tuple[str, ...]:
    support_names = {
        PurePosixPath(relative).name
        for relative in STABILIZATION_TEST_FILES
        if not PurePosixPath(relative).name.startswith("test")
    }
    try:
        with os.scandir(tests) as entries:
            names = sorted(
                entry.name
                for entry in entries
                if entry.name.endswith(".py")
                and (
                    entry.name.startswith("test")
                    or (include_support_modules and entry.name in support_names)
                )
            )
    except OSError as error:
        raise InventoryError("working test source names cannot be listed") from error
    if len(names) != len(set(names)):
        raise InventoryError("working test source names are duplicated")
    return tuple(f"tests/{name}" for name in names)


def _registered_probe_source_names(
    repository_root: Path,
    *,
    include: bool,
) -> tuple[str, ...]:
    if not include:
        return ()
    paths = sorted(
        {relative_path for relative_path, _ in REGISTERED_PROBE_IMPLEMENTATIONS.values()}
    )
    return tuple(
        relative_path
        for relative_path in paths
        if os.path.lexists(repository_root / PurePosixPath(relative_path))
    )


def _capture_working_sources(
    repository_root: Path,
    *,
    include_support_modules: bool = False,
) -> WorkingSourcesSnapshot:
    root = Path(os.path.abspath(repository_root))
    tests = root / "tests"
    directory_identity = _working_tests_directory_identity(tests)
    names = _working_source_names(
        tests,
        include_support_modules=include_support_modules,
    )
    probe_names = _registered_probe_source_names(
        root,
        include=include_support_modules,
    )
    sources: dict[str, bytes] = {}
    snapshots: list[object] = []
    for relative in names + probe_names:
        path = root / PurePosixPath(relative)
        try:
            snapshot = secure_filesystem.read_regular_snapshot(
                path,
                maximum_bytes=MAXIMUM_SOURCE_BYTES,
                root=root,
            )
        except Exception as error:
            raise InventoryError(
                f"working test source cannot be read securely: {relative}"
            ) from error
        sources[relative] = snapshot.raw
        snapshots.append(snapshot)
    if _working_tests_directory_identity(tests) != directory_identity:
        raise InventoryError("working tests directory changed during capture")
    if _working_source_names(
        tests,
        include_support_modules=include_support_modules,
    ) != names:
        raise InventoryError("working test source set changed during capture")
    return WorkingSourcesSnapshot(
        root,
        tests,
        directory_identity,
        sources,
        tuple(snapshots),
        include_support_modules,
        probe_names,
    )


def _working_sources(repository_root: Path) -> dict[str, bytes]:
    return dict(_capture_working_sources(repository_root).sources)


_AUTOMATIC_DESTINATION_IDENTITY = object()


@dataclass(slots=True)
class _GovernanceWriteOutcome:
    published: bool = False
    snapshot: object | None = None
    recovery_path: Path | None = None


@dataclass(slots=True)
class _GovernancePublishState:
    recovery_name: str | None = None
    destination_handle: int | None = None
    displaced: bool = False
    published: bool = False


def _windows_open_relative_governance_file(
    directory_handle: int,
    name: str,
) -> int:
    name = secure_filesystem._validated_relative_name(name)
    create, _, _, _, _ = secure_filesystem._windows_file_api()
    encoded = name.encode("utf-16-le")
    name_buffer = secure_filesystem.ctypes.create_unicode_buffer(name)
    unicode_name = secure_filesystem._WindowsUnicodeString(
        len(encoded),
        len(encoded),
        secure_filesystem.ctypes.cast(
            name_buffer,
            secure_filesystem.wintypes.LPWSTR,
        ),
    )
    attributes = secure_filesystem._WindowsObjectAttributes(
        secure_filesystem.ctypes.sizeof(
            secure_filesystem._WindowsObjectAttributes
        ),
        secure_filesystem.wintypes.HANDLE(directory_handle),
        secure_filesystem.ctypes.pointer(unicode_name),
        0x40,
        None,
        None,
    )
    status_block = secure_filesystem._WindowsIOStatusBlock()
    handle = secure_filesystem.wintypes.HANDLE()
    status = int(
        create(
            secure_filesystem.ctypes.byref(handle),
            0x00000080 | 0x00010000 | 0x00100000,
            secure_filesystem.ctypes.byref(attributes),
            secure_filesystem.ctypes.byref(status_block),
            None,
            0x80,
            0x00000001,
            1,
            0x20 | 0x40 | 0x00200000,
            None,
            0,
        )
    )
    invalid = secure_filesystem.ctypes.c_void_p(-1).value
    if (
        status != 0
        or int(status_block.Status) != 0
        or not handle.value
        or int(handle.value) == invalid
    ):
        raise InventoryError("governance destination lock could not be acquired")
    return int(handle.value)


def _windows_rename_governance_file(
    handle: int,
    directory_handle: int,
    destination_name: str,
) -> None:
    destination_name = secure_filesystem._validated_relative_name(
        destination_name
    )
    _, set_information, _, _, _ = secure_filesystem._windows_file_api()
    encoded = destination_name.encode("utf-16-le")
    structure = secure_filesystem._WindowsFileRenameInformation
    name_offset = structure.FileName.offset
    buffer = secure_filesystem.ctypes.create_string_buffer(
        name_offset + len(encoded)
    )
    information = secure_filesystem.ctypes.cast(
        buffer,
        secure_filesystem.ctypes.POINTER(structure),
    ).contents
    information.ReplaceIfExists = 0
    information.RootDirectory = secure_filesystem.wintypes.HANDLE(
        directory_handle
    )
    information.FileNameLength = len(encoded)
    secure_filesystem.ctypes.memmove(
        secure_filesystem.ctypes.addressof(buffer) + name_offset,
        encoded,
        len(encoded),
    )
    status_block = secure_filesystem._WindowsIOStatusBlock()
    status = int(
        set_information(
            secure_filesystem.wintypes.HANDLE(handle),
            secure_filesystem.ctypes.byref(status_block),
            secure_filesystem.ctypes.byref(buffer),
            len(buffer),
            10,
        )
    )
    if status != 0 or int(status_block.Status) != 0:
        raise InventoryError("governance no-replace rename was refused")


def _governance_directory_chain(
    parent: Path,
) -> tuple[tuple[Path, tuple[int, ...]], ...]:
    paths = [
        path
        for path in reversed(parent.parents)
        if path != path.parent
    ]
    paths.append(parent)
    identities: list[tuple[Path, tuple[int, ...]]] = []
    for path in paths:
        try:
            info = os.lstat(path)
        except OSError as error:
            raise InventoryError(
                "governance destination ancestor cannot be inspected"
            ) from error
        if (
            stat.S_ISLNK(info.st_mode)
            or secure_filesystem._is_disallowed_reparse(info)
            or not stat.S_ISDIR(info.st_mode)
        ):
            raise InventoryError(
                "governance destination ancestor is not a secure directory"
            )
        identities.append(
            (path, secure_filesystem._directory_identity(info))
        )
    return tuple(identities)


def _revalidate_governance_directory_chain(
    chain: Sequence[tuple[Path, tuple[int, ...]]],
) -> None:
    for path, expected in chain:
        info = os.lstat(path)
        if (
            stat.S_ISLNK(info.st_mode)
            or secure_filesystem._is_disallowed_reparse(info)
            or not stat.S_ISDIR(info.st_mode)
            or secure_filesystem._directory_identity(info) != expected
        ):
            raise InventoryError(
                "governance destination ancestor identity changed"
            )


def _governance_destination_identity(
    path: Path,
) -> tuple[int, ...] | None:
    if not os.path.lexists(path):
        return None
    try:
        snapshot = secure_filesystem.read_regular_snapshot(
            path,
            maximum_bytes=MAXIMUM_SOURCE_BYTES,
            root=path.parent,
        )
    except Exception as error:
        raise InventoryError(
            "governance destination is not a secure regular file"
        ) from error
    return snapshot.identity


def _require_governance_destination_identity(
    path: Path,
    expected: tuple[int, ...] | None,
) -> None:
    if _governance_destination_identity(path) != expected:
        raise InventoryError("governance destination identity changed")


def _publish_staged_governance(
    *,
    temporary_name: str,
    temporary_handle: int,
    destination_name: str,
    parent_handle: int,
    windows: bool,
    destination_path: Path,
    expected_identity: tuple[int, ...] | None,
    state: _GovernancePublishState,
    outcome: _GovernanceWriteOutcome,
) -> None:
    _require_governance_destination_identity(
        destination_path,
        expected_identity,
    )
    if windows:
        if expected_identity is not None:
            state.destination_handle = _windows_open_relative_governance_file(
                parent_handle,
                destination_name,
            )
            _require_governance_destination_identity(
                destination_path,
                expected_identity,
            )
            state.recovery_name = (
                f".{destination_name}.{uuid.uuid4().hex}.recovery"
            )
            outcome.recovery_path = destination_path.with_name(
                state.recovery_name
            )
            _windows_rename_governance_file(
                state.destination_handle,
                parent_handle,
                state.recovery_name,
            )
            state.displaced = True
        _windows_rename_governance_file(
            temporary_handle,
            parent_handle,
            destination_name,
        )
        state.published = True
        outcome.published = True
        return
    before_handle = os.fstat(temporary_handle)
    before_path = os.stat(
        temporary_name,
        dir_fd=parent_handle,
        follow_symlinks=False,
    )
    if (
        not stat.S_ISREG(before_handle.st_mode)
        or not stat.S_ISREG(before_path.st_mode)
        or secure_filesystem._path_handle_identity(before_handle)
        != secure_filesystem._path_handle_identity(before_path)
    ):
        raise InventoryError("governance staging name changed before publish")
    recovery_name = f".{destination_name}.{uuid.uuid4().hex}.recovery"
    state.recovery_name = recovery_name
    outcome.recovery_path = destination_path.with_name(recovery_name)
    if expected_identity is not None:
        state.destination_handle = os.open(
            destination_name,
            os.O_RDONLY
            | os.O_NOFOLLOW
            | getattr(os, "O_NONBLOCK", 0)
            | getattr(os, "O_CLOEXEC", 0),
            dir_fd=parent_handle,
        )
        destination_info = os.fstat(state.destination_handle)
        if secure_filesystem._file_identity(destination_info) != expected_identity:
            raise InventoryError("governance destination changed before displacement")
        os.rename(
            destination_name,
            recovery_name,
            src_dir_fd=parent_handle,
            dst_dir_fd=parent_handle,
        )
        state.displaced = True
        recovery_info = os.stat(
            recovery_name,
            dir_fd=parent_handle,
            follow_symlinks=False,
        )
        if (
            secure_filesystem._path_handle_identity(recovery_info)
            != secure_filesystem._path_handle_identity(destination_info)
        ):
            raise InventoryError(
                "governance destination raced into the recovery artifact"
            )
    os.link(
        temporary_name,
        destination_name,
        src_dir_fd=parent_handle,
        dst_dir_fd=parent_handle,
        follow_symlinks=False,
    )
    os.unlink(temporary_name, dir_fd=parent_handle)
    state.published = True
    outcome.published = True


def _write_posix_governance(
    path: Path,
    raw: bytes,
    chain: Sequence[tuple[Path, tuple[int, ...]]],
    expected_identity: tuple[int, ...] | None,
    outcome: _GovernanceWriteOutcome,
    lifetime_check: Any | None,
) -> None:
    required = (os.link, os.open, os.rename, os.stat, os.unlink)
    if (
        not hasattr(os, "O_DIRECTORY")
        or not hasattr(os, "O_NOFOLLOW")
        or any(function not in os.supports_dir_fd for function in required)
        or os.stat not in os.supports_follow_symlinks
    ):
        raise InventoryError("secure POSIX governance primitives are absent")
    directory_flags = (
        os.O_RDONLY
        | os.O_DIRECTORY
        | os.O_NOFOLLOW
        | getattr(os, "O_CLOEXEC", 0)
    )
    directory = os.open(path.parent, directory_flags)
    temporary_name = f".{path.name}.{uuid.uuid4().hex}.tmp"
    temporary: int | None = None
    published = False
    publish_state = _GovernancePublishState()
    primary_failure: BaseException | None = None
    cleanup_failures: list[BaseException] = []
    try:
        parent_info = os.fstat(directory)
        if secure_filesystem._directory_identity(parent_info) != chain[-1][1]:
            raise InventoryError("bound governance directory identity differs")
        temporary = os.open(
            temporary_name,
            os.O_WRONLY
            | os.O_CREAT
            | os.O_EXCL
            | os.O_NOFOLLOW
            | getattr(os, "O_CLOEXEC", 0),
            0o600,
            dir_fd=directory,
        )
        offset = 0
        while offset < len(raw):
            written = os.write(temporary, raw[offset:])
            if written <= 0:
                raise InventoryError(
                    "governance output write made no progress"
                )
            offset += written
        os.fsync(temporary)
        _revalidate_governance_directory_chain(chain)
        _require_governance_destination_identity(path, expected_identity)
        if lifetime_check is not None:
            lifetime_check()
        _publish_staged_governance(
            temporary_name=temporary_name,
            temporary_handle=temporary,
            destination_name=path.name,
            parent_handle=directory,
            windows=False,
            destination_path=path,
            expected_identity=expected_identity,
            state=publish_state,
            outcome=outcome,
        )
        published = True
        os.fsync(directory)
        if lifetime_check is not None:
            lifetime_check()
        if publish_state.recovery_name is not None:
            os.unlink(publish_state.recovery_name, dir_fd=directory)
            publish_state.displaced = False
            outcome.recovery_path = None
        os.fsync(directory)
    except BaseException as error:
        primary_failure = error
    if (
        primary_failure is not None
        and publish_state.published
        and publish_state.displaced
    ):
        try:
            if publish_state.recovery_name is None or temporary is None:
                raise InventoryError("governance recovery state is incomplete")
            published_info = os.stat(
                path.name,
                dir_fd=directory,
                follow_symlinks=False,
            )
            staged_info = os.fstat(temporary)
            if (
                secure_filesystem._path_handle_identity(published_info)
                != secure_filesystem._path_handle_identity(staged_info)
            ):
                raise InventoryError(
                    "governance rollback refused a concurrent destination"
                )
            os.unlink(path.name, dir_fd=directory)
            os.link(
                publish_state.recovery_name,
                path.name,
                src_dir_fd=directory,
                dst_dir_fd=directory,
                follow_symlinks=False,
            )
            os.unlink(publish_state.recovery_name, dir_fd=directory)
            publish_state.displaced = False
            publish_state.published = False
            outcome.published = False
            outcome.recovery_path = None
            published = False
        except BaseException as error:
            cleanup_failures.append(error)
    if temporary is not None:
        if not published:
            try:
                handle_info = os.fstat(temporary)
                path_info = os.stat(
                    temporary_name,
                    dir_fd=directory,
                    follow_symlinks=False,
                )
                if (
                    secure_filesystem._path_handle_identity(handle_info)
                    == secure_filesystem._path_handle_identity(path_info)
                ):
                    os.unlink(temporary_name, dir_fd=directory)
            except FileNotFoundError:
                pass
            except BaseException as error:
                cleanup_failures.append(error)
        try:
            os.close(temporary)
        except BaseException as error:
            cleanup_failures.append(error)
    if publish_state.destination_handle is not None:
        try:
            os.close(publish_state.destination_handle)
        except BaseException as error:
            cleanup_failures.append(error)
    if publish_state.displaced and not publish_state.published:
        try:
            if publish_state.recovery_name is None:
                raise InventoryError("governance recovery name is absent")
            os.link(
                publish_state.recovery_name,
                path.name,
                src_dir_fd=directory,
                dst_dir_fd=directory,
                follow_symlinks=False,
            )
            os.unlink(publish_state.recovery_name, dir_fd=directory)
            publish_state.displaced = False
        except BaseException as error:
            cleanup_failures.append(error)
    try:
        os.close(directory)
    except BaseException as error:
        cleanup_failures.append(error)
    if primary_failure is not None:
        if cleanup_failures:
            raise InventoryError(
                "governance write and cleanup both failed"
            ) from ExceptionGroup(
                "governance write failures",
                (primary_failure, *cleanup_failures),
            )
        raise primary_failure
    if cleanup_failures:
        raise InventoryError("governance cleanup failed") from ExceptionGroup(
            "governance cleanup failures",
            tuple(cleanup_failures),
        )


def _write_windows_governance(
    path: Path,
    raw: bytes,
    chain: Sequence[tuple[Path, tuple[int, ...]]],
    expected_identity: tuple[int, ...] | None,
    outcome: _GovernanceWriteOutcome,
    lifetime_check: Any | None,
) -> None:
    directory: int | None = None
    temporary: object | None = None
    publish_state = _GovernancePublishState()
    primary_failure: BaseException | None = None
    cleanup_failures: list[BaseException] = []
    try:
        directory, bound_identity = secure_filesystem._windows_open_directory(
            path.parent
        )
        temporary_name = f".{path.name}.{uuid.uuid4().hex}.tmp"
        temporary = secure_filesystem._StagedBaseline(
            temporary_name,
            None,
        )
        handle = secure_filesystem._windows_create_relative_file(
            directory,
            temporary_name,
            owner=temporary,
        )
        secure_filesystem._write_staged_bytes(handle, raw, windows=True)
        _revalidate_governance_directory_chain(chain)
        if (
            secure_filesystem._windows_directory_handle_identity(
                directory,
                path.parent,
            )
            != bound_identity
        ):
            raise InventoryError("bound governance directory identity changed")
        _require_governance_destination_identity(path, expected_identity)
        if lifetime_check is not None:
            lifetime_check()
        _publish_staged_governance(
            temporary_name=temporary_name,
            temporary_handle=handle,
            destination_name=path.name,
            parent_handle=directory,
            windows=True,
            destination_path=path,
            expected_identity=expected_identity,
            state=publish_state,
            outcome=outcome,
        )
        temporary.renamed = True
        if lifetime_check is not None:
            lifetime_check()
        if publish_state.destination_handle is not None:
            secure_filesystem._windows_dispose_relative_file(
                publish_state.destination_handle
            )
            secure_filesystem._windows_close_file(
                publish_state.destination_handle
            )
            publish_state.destination_handle = None
            publish_state.displaced = False
            outcome.recovery_path = None
    except BaseException as error:
        primary_failure = error
    if (
        primary_failure is not None
        and publish_state.published
        and publish_state.displaced
        and publish_state.destination_handle is not None
        and temporary is not None
        and temporary.handle is not None
    ):
        try:
            secure_filesystem._windows_dispose_relative_file(
                temporary.handle
            )
            secure_filesystem._windows_close_file(temporary.handle)
            temporary.handle = None
            temporary.state = "closed"
            _windows_rename_governance_file(
                publish_state.destination_handle,
                directory,
                path.name,
            )
            publish_state.displaced = False
            publish_state.published = False
            outcome.published = False
            outcome.recovery_path = None
        except BaseException as error:
            cleanup_failures.append(error)
    if (
        publish_state.destination_handle is not None
        and publish_state.displaced
        and not publish_state.published
    ):
        try:
            _windows_rename_governance_file(
                publish_state.destination_handle,
                directory,
                path.name,
            )
            publish_state.displaced = False
            outcome.recovery_path = None
        except BaseException as error:
            cleanup_failures.append(error)
    if publish_state.destination_handle is not None:
        try:
            secure_filesystem._windows_close_file(
                publish_state.destination_handle
            )
            publish_state.destination_handle = None
        except BaseException as error:
            cleanup_failures.append(error)
    if temporary is not None:
        try:
            secure_filesystem._cleanup_windows_temporary(temporary)
        except BaseException as error:
            cleanup_failures.append(error)
    if directory is not None:
        try:
            secure_filesystem._windows_close_directory(directory)
        except BaseException as error:
            cleanup_failures.append(error)
    if primary_failure is not None:
        if cleanup_failures:
            raise InventoryError(
                "governance write and cleanup both failed"
            ) from ExceptionGroup(
                "governance write failures",
                (primary_failure, *cleanup_failures),
            )
        raise primary_failure
    if cleanup_failures:
        raise InventoryError("governance cleanup failed") from ExceptionGroup(
            "governance cleanup failures",
            tuple(cleanup_failures),
        )


def write_atomic_lf(
    path: Path,
    raw: bytes,
    *,
    expected_identity: tuple[int, ...] | None | object = (
        _AUTOMATIC_DESTINATION_IDENTITY
    ),
    _outcome: _GovernanceWriteOutcome | None = None,
    _lifetime_check: Any | None = None,
) -> object:
    if not isinstance(path, Path) or not path.is_absolute() or type(raw) is not bytes:
        raise InventoryError("atomic LF writes require an absolute path and exact bytes")
    if len(raw) > MAXIMUM_SOURCE_BYTES:
        raise InventoryError("governance output exceeds the write bound")
    if (
        raw.startswith(b"\xef\xbb\xbf")
        or b"\r" in raw
        or not raw.endswith(b"\n")
        or raw.endswith(b"\n\n")
    ):
        raise InventoryError("governance output must be BOM-free canonical LF with one final LF")
    candidate = Path(os.path.abspath(path))
    chain = _governance_directory_chain(candidate.parent)
    captured_identity = (
        _governance_destination_identity(candidate)
        if expected_identity is _AUTOMATIC_DESTINATION_IDENTITY
        else expected_identity
    )
    if captured_identity is not None and not isinstance(
        captured_identity,
        tuple,
    ):
        raise InventoryError("governance expected destination identity is invalid")
    _require_governance_destination_identity(candidate, captured_identity)
    outcome = _outcome or _GovernanceWriteOutcome()
    if os.name == "nt":
        _write_windows_governance(
            candidate,
            raw,
            chain,
            captured_identity,
            outcome,
            _lifetime_check,
        )
    else:
        _write_posix_governance(
            candidate,
            raw,
            chain,
            captured_identity,
            outcome,
            _lifetime_check,
        )
    snapshot = secure_filesystem.read_regular_snapshot(
        candidate,
        maximum_bytes=MAXIMUM_SOURCE_BYTES,
        root=candidate.parent,
    )
    if snapshot.raw != raw:
        raise InventoryError("published governance bytes differ from staging bytes")
    outcome.snapshot = snapshot
    return snapshot


def _write_governance_pair(
    first_path: Path,
    first_raw: bytes,
    first_snapshot: object,
    second_path: Path,
    second_raw: bytes,
    second_snapshot: object,
    *,
    lifetime_check: Any | None = None,
) -> None:
    originals = (
        (first_path, first_raw, first_snapshot),
        (second_path, second_raw, second_snapshot),
    )
    published: dict[Path, object] = {}
    outcomes = {
        first_path: _GovernanceWriteOutcome(),
        second_path: _GovernanceWriteOutcome(),
    }
    try:
        published[first_path] = write_atomic_lf(
            first_path,
            first_raw,
            expected_identity=first_snapshot.identity,
            _outcome=outcomes[first_path],
            _lifetime_check=lifetime_check,
        )
        published[second_path] = write_atomic_lf(
            second_path,
            second_raw,
            expected_identity=second_snapshot.identity,
            _outcome=outcomes[second_path],
            _lifetime_check=lifetime_check,
        )
        for snapshot in published.values():
            snapshot.revalidate()
    except BaseException as primary_failure:
        rollback_failures: list[BaseException] = []
        for path, new_raw, original in reversed(originals):
            try:
                ours = published.get(path)
                if ours is None and outcomes[path].published:
                    ours = secure_filesystem.read_regular_snapshot(
                        path,
                        maximum_bytes=MAXIMUM_SOURCE_BYTES,
                        root=path.parent,
                    )
                    if ours.raw != new_raw:
                        raise InventoryError(
                            "published governance outcome is ambiguous"
                        )
                    published[path] = ours
                if ours is None:
                    try:
                        original.revalidate()
                    except BaseException:
                        restored = secure_filesystem.read_regular_snapshot(
                            path,
                            maximum_bytes=MAXIMUM_SOURCE_BYTES,
                            root=path.parent,
                        )
                        if restored.raw != original.raw:
                            raise InventoryError(
                                "governance rollback refused changed bytes"
                            )
                    continue
                current = secure_filesystem.read_regular_snapshot(
                    path,
                    maximum_bytes=MAXIMUM_SOURCE_BYTES,
                    root=path.parent,
                )
                if (
                    current.identity != ours.identity
                    or current.raw != ours.raw
                ):
                    raise InventoryError(
                        "governance rollback refused concurrent mutation"
                    )
                write_atomic_lf(
                    path,
                    original.raw,
                    expected_identity=current.identity,
                )
                restored = secure_filesystem.read_regular_snapshot(
                    path,
                    maximum_bytes=MAXIMUM_SOURCE_BYTES,
                    root=path.parent,
                )
                if restored.raw != original.raw:
                    raise InventoryError("governance rollback bytes differ")
            except BaseException as error:
                rollback_failures.append(error)
        if rollback_failures:
            raise InventoryError(
                "governance pair write and rollback both failed"
            ) from ExceptionGroup(
                "governance pair failures",
                (primary_failure, *rollback_failures),
            )
        raise primary_failure


def _inventory_semantic(inventory: Mapping[str, object]) -> str:
    return sha256(_semantic_bytes(inventory)).hexdigest()


def _item_universe(
    inventory: Mapping[str, object],
    discovery: Discovery,
) -> tuple[tuple[str, str], ...]:
    entries = inventory["entries"]
    design_stable_ids = {
        str(entry["stable_id"])
        for entry in entries
        if str(entry["assignment"]["profile_name"]) != "historical"
    }
    items = [("stable_id", stable_id) for stable_id in design_stable_ids]
    items.extend(
        ("fixture", fixture.fixture_id)
        for fixture in discovery.lifecycle_fixtures
        if set(fixture.member_ids).issubset(design_stable_ids)
    )
    items.append(("probe", DESIGN_GPU_PROBE_ID))
    return tuple(sorted(items))


def _qualified_name(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _qualified_name(node.value)
        return None if parent is None else f"{parent}.{node.attr}"
    return None


def _literal_string_mapping(node: ast.expr | None) -> dict[str, str] | None:
    if node is None:
        return {}
    try:
        value = ast.literal_eval(node)
    except (ValueError, TypeError):
        return None
    if not isinstance(value, dict) or any(
        type(key) is not str or type(item) is not str for key, item in value.items()
    ):
        return None
    return {key: value[key] for key in sorted(value)}


_SUBPROCESS_FUNCTIONS = {
    "subprocess.run",
    "subprocess.Popen",
    "subprocess.call",
    "subprocess.check_call",
    "subprocess.check_output",
}
_OWNER_CALLS = {
    "pontius.gpu_occupied_card_quotient.run_frozen_gpu_quotient_keystone",
    (
        "pontius.legal_river_quotient_cuda_consumer."
        "run_bounded_cuda_consumer_conformance"
    ),
    "pontius.gpu_quotient_validation_seam.run_bounded_quotient_validation_seam",
    (
        "pontius.legal_river_exact_cubin_inspector_diagnostic_runner."
        "execute_owner_to_path"
    ),
    (
        "pontius.legal_river_exact_cubin_zero_suffix_diagnostic_runner."
        "execute_owner_to_path"
    ),
    (
        "pontius.legal_river_quotient_cuda_compensated_work_preflight_runner."
        "execute_owner_to_path"
    ),
    (
        "pontius.legal_river_quotient_cuda_compensated_work_preflight_v2_runner."
        "execute_owner_to_path"
    ),
    (
        "pontius.legal_river_quotient_cuda_compensated_work_preflight_v3_runner."
        "execute_owner_to_path"
    ),
    (
        "pontius.legal_river_quotient_cuda_compensated_work_preflight_v4_runner."
        "execute_owner_to_path"
    ),
    (
        "pontius.legal_river_quotient_fixed_width_device_preflight_runner."
        "execute_owner_to_path"
    ),
    "pontius.literal_45_quotient_target_runner.execute_owner_to_path",
    "pontius.gpu_quotient_staged_scaling_runner.execute_campaign_to_path",
    "pontius.gpu_quotient_staged_scaling_v2_runner.execute_campaign_to_path",
    (
        "pontius.legal_river_quotient_selective_certified_separation_runner."
        "run"
    ),
    (
        "pontius.legal_river_quotient_selective_certified_separation_runner."
        "main"
    ),
}
_CUDA_CALLS = {
    "cupy.cuda.get_current_stream": ("cuda_query", "stream"),
    "cupy.get_default_memory_pool": ("cuda_query", "memory_pool"),
    (
        "cupy.get_default_pinned_memory_pool"
    ): ("cuda_query", "pinned_memory_pool"),
    "cupy.asnumpy": ("cuda_query", "host_array"),
    "cupy.testing.assert_array_equal": ("cuda_query", "none_or_assertion"),
    "cupy.arange": ("cuda_allocation", "device_array"),
    "cupy.linspace": ("cuda_allocation", "device_array"),
    "cupy.cuda.runtime.getDeviceCount": (
        "cuda_query",
        "nonnegative_integer",
    ),
}
_CUDA_BLOCKED_CALLS = {
    "cupy.cuda.get_current_stream().synchronize",
    "cupy.get_default_memory_pool().free_all_blocks",
    "cupy.get_default_pinned_memory_pool().free_all_blocks",
    "cupy.arange().reshape",
    "cupy.linspace().reshape",
}
_SCIENTIFIC_PROTECTED_CALLS = {
    (
        "pontius.affine_resident_heterogeneous_leaf_contraction."
        "CuPyAffineResidentAutomatonCache.compile"
    ),
    (
        "pontius.canonical_affine_resident_automaton_cache."
        "CuPyCanonicalAffineResidentAutomatonCache.compile"
    ),
    "pontius.cupy_sparse_incidence.CuPyBidirectionalIncidence.compile",
    (
        "pontius.resident_heterogeneous_leaf_contraction."
        "CuPyResidentAutomatonCache.compile"
    ),
    (
        "pontius.resident_heterogeneous_leaf_contraction."
        "CuPyResidentBeliefCache.compile"
    ),
    (
        "pontius.shared_resident_response_context."
        "SharedResidentAutomatonBundle.compile"
    ),
    (
        "pontius.shared_resident_response_context."
        "bind_resident_response_context"
    ),
    (
        "pontius.incremental_leaf_adjoint_response."
        "compile_leaf_adjoint_response_caches"
    ),
    "pontius.h32_action_width_quality_audit._compile_cache",
    "pontius.h32_action_width_quality_audit._arm_plan",
    "pontius.h32_action_width_quality_audit._verify_candidate_stream",
    "pontius.full_width_river_capacity_preflight._small_control",
    "pontius.full_width_river_capacity_preflight_v2._runtime_snapshot",
    "pontius.legal_river_quotient_cuda_compensated_tiles._kernels",
    "pontius.legal_river_quotient_cuda_compensated_tiles._run_primitive_controls",
    "pontius.legal_river_quotient_cuda_compensated_tiles._allocate_resident",
    "pontius.legal_river_quotient_cuda_compensated_tiles._query_weight_evidence",
    "pontius.legal_river_quotient_cuda_compensated_tiles._ten_card_evidence",
    (
        "pontius.heterogeneous_leaf_contraction."
        "contract_heterogeneous_leaf_terms"
    ),
    "pontius.leaf_adjoint_evaluation.evaluate_leaf_adjoint_seat",
    (
        "pontius.cross_payoff_adjoint_result."
        "evaluate_typed_multi_size_affine_cross_payoff"
    ),
    (
        "pontius.device_fold_resident_heterogeneous_leaf_contraction."
        "contract_device_fold_resident_heterogeneous_leaf_terms"
    ),
    (
        "pontius.device_fold_resident_heterogeneous_leaf_contraction_v2."
        "contract_device_fold_resident_heterogeneous_leaf_terms_v2"
    ),
    (
        "pontius.device_fold_selector_stable_affine_response."
        "evaluate_device_fold_batched_selector_stable_affine_opponents"
    ),
    (
        "pontius.device_fold_selector_stable_affine_response."
        "evaluate_device_fold_selector_stable_affine_leaf_adjoint_seat"
    ),
    (
        "pontius.device_fold_selector_stable_affine_response_v2."
        "evaluate_device_fold_selector_stable_affine_leaf_adjoint_seat_v2"
    ),
    (
        "pontius.multi_size_affine_resident_leaf_adjoint_cfr."
        "multi_size_affine_resident_leaf_adjoint_cfr_traverser"
    ),
    (
        "pontius.multi_size_affine_resident_leaf_adjoint_evaluation."
        "evaluate_multi_size_affine_resident_profile"
    ),
    (
        "pontius.multi_size_resident_leaf_adjoint_cfr."
        "multi_size_resident_leaf_adjoint_cfr_traverser"
    ),
    (
        "pontius.resident_heterogeneous_leaf_contraction."
        "contract_resident_heterogeneous_leaf_terms"
    ),
    (
        "pontius.resident_leaf_adjoint_cfr."
        "resident_leaf_adjoint_cfr_traverser"
    ),
    (
        "pontius.resident_leaf_adjoint_evaluation."
        "evaluate_resident_leaf_adjoint_seat"
    ),
    (
        "pontius.resident_record_to_hand_fold_v2."
        "finalize_resident_record_accumulators_v2"
    ),
}
_STATIC_UNRESOLVED = object()


def _module_import_aliases(tree: ast.Module) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, ast.Import):
            for imported in node.names:
                local = imported.asname or imported.name.split(".", 1)[0]
                aliases[local] = imported.name if imported.asname else local
        elif isinstance(node, ast.ImportFrom) and node.module:
            for imported in node.names:
                local = imported.asname or imported.name
                aliases[local] = f"{node.module}.{imported.name}"
    return aliases


def _resolved_qualified_name(
    node: ast.expr,
    aliases: Mapping[str, str],
) -> str | None:
    supplied = _qualified_name(node)
    if supplied is None:
        return None
    first, separator, remainder = supplied.partition(".")
    resolved = aliases.get(first, first)
    return f"{resolved}.{remainder}" if separator else resolved


def _resolved_callable_name(
    node: ast.expr,
    aliases: Mapping[str, str],
) -> str | None:
    direct = _resolved_qualified_name(node, aliases)
    if direct is not None:
        return direct
    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Call):
        parent = _resolved_callable_name(node.value.func, aliases)
        if parent is not None:
            return f"{parent}().{node.attr}"
    return None


def _static_assignments(nodes: Iterable[ast.stmt]) -> dict[str, ast.expr]:
    assignments: dict[str, ast.expr] = {}
    for node in nodes:
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
        ):
            assignments[node.targets[0].id] = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.value is not None:
                assignments[node.target.id] = node.value
    return assignments


def _static_value(
    node: ast.expr,
    assignments: Mapping[str, ast.expr],
    *,
    seen: frozenset[str] = frozenset(),
) -> object:
    if isinstance(node, ast.Constant) and type(node.value) in {
        str,
        bool,
        int,
        float,
        type(None),
    }:
        return node.value
    if isinstance(node, ast.Name):
        if node.id in seen or node.id not in assignments:
            return _STATIC_UNRESOLVED
        return _static_value(
            assignments[node.id],
            assignments,
            seen=seen | {node.id},
        )
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = _static_value(node.left, assignments, seen=seen)
        right = _static_value(node.right, assignments, seen=seen)
        if type(left) is str and type(right) is str:
            return left + right
        return _STATIC_UNRESOLVED
    if isinstance(node, (ast.List, ast.Tuple)):
        values = [
            _static_value(item, assignments, seen=seen)
            for item in node.elts
        ]
        if _STATIC_UNRESOLVED in values:
            return _STATIC_UNRESOLVED
        return values
    if isinstance(node, ast.Dict):
        result: dict[str, str] = {}
        for key_node, value_node in zip(node.keys, node.values, strict=True):
            if key_node is None:
                return _STATIC_UNRESOLVED
            key = _static_value(key_node, assignments, seen=seen)
            value = _static_value(value_node, assignments, seen=seen)
            if type(key) is not str or type(value) is not str:
                return _STATIC_UNRESOLVED
            result[key] = value
        return result
    return _STATIC_UNRESOLVED


def _review_blocker(
    item_id: str,
    relative_path: str,
    node: ast.AST,
    reason: str,
) -> dict[str, object]:
    return {
        "item_id": item_id,
        "relative_path": relative_path,
        "line": int(getattr(node, "lineno", 0)),
        "reason": reason,
    }


def _capability_id(prefix: str, definition: Mapping[str, object]) -> str:
    digest = sha256(_semantic_bytes(definition)).hexdigest()
    return f"{prefix}:{digest[:24]}"


@dataclass(frozen=True, slots=True)
class _ReviewFunction:
    relative_path: str
    node: ast.FunctionDef | ast.AsyncFunctionDef
    aliases: Mapping[str, str]
    module_assignments: Mapping[str, ast.expr]
    class_name: str | None


class _ExecutionScopeVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.calls: list[ast.Call] = []
        self.imports: list[ast.Import | ast.ImportFrom] = []
        self.assignments: list[ast.Assign | ast.AnnAssign] = []
        self.local_functions: set[str] = set()

    def visit_Call(self, node: ast.Call) -> None:
        self.calls.append(node)
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        self.imports.append(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        self.imports.append(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        self.assignments.append(node)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        self.assignments.append(node)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.local_functions.add(node.name)
        for expression in (*node.decorator_list, *node.args.defaults):
            self.visit(expression)
        for expression in node.args.kw_defaults:
            if expression is not None:
                self.visit(expression)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.local_functions.add(node.name)
        for expression in (*node.decorator_list, *node.args.defaults):
            self.visit(expression)
        for expression in node.args.kw_defaults:
            if expression is not None:
                self.visit(expression)

    def visit_Lambda(self, node: ast.Lambda) -> None:
        return

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        return


class _DefinitionTimeVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.calls: list[tuple[ast.Call, str | None]] = []
        self.class_name: str | None = None

    def visit_Call(self, node: ast.Call) -> None:
        self.calls.append((node, self.class_name))
        self.generic_visit(node)

    def _visit_function_metadata(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
    ) -> None:
        for decorator in node.decorator_list:
            self.visit(decorator)
        for default in (*node.args.defaults, *node.args.kw_defaults):
            if default is not None:
                self.visit(default)
        for parameter in (
            *node.args.posonlyargs,
            *node.args.args,
            *node.args.kwonlyargs,
        ):
            if parameter.annotation is not None:
                self.visit(parameter.annotation)
        if node.args.vararg is not None and node.args.vararg.annotation is not None:
            self.visit(node.args.vararg.annotation)
        if node.args.kwarg is not None and node.args.kwarg.annotation is not None:
            self.visit(node.args.kwarg.annotation)
        if node.returns is not None:
            self.visit(node.returns)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_function_metadata(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_function_metadata(node)

    def visit_Lambda(self, node: ast.Lambda) -> None:
        for default in (*node.args.defaults, *node.args.kw_defaults):
            if default is not None:
                self.visit(default)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        previous = self.class_name
        for expression in (*node.decorator_list, *node.bases):
            self.visit(expression)
        for keyword in node.keywords:
            self.visit(keyword.value)
        self.class_name = node.name
        for statement in node.body:
            self.visit(statement)
        self.class_name = previous


def _execution_scope(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> _ExecutionScopeVisitor:
    visitor = _ExecutionScopeVisitor()
    for statement in node.body:
        visitor.visit(statement)
    return visitor


def _function_aliases(
    aliases: Mapping[str, str],
    imports: Iterable[ast.Import | ast.ImportFrom],
    assignments: Iterable[ast.Assign | ast.AnnAssign],
) -> dict[str, str]:
    result = dict(aliases)
    assignment_nodes = tuple(assignments)
    for node in imports:
        if isinstance(node, ast.Import):
            for imported in node.names:
                local = imported.asname or imported.name.split(".", 1)[0]
                result[local] = imported.name if imported.asname else local
        elif node.module:
            for imported in node.names:
                local = imported.asname or imported.name
                result[local] = f"{node.module}.{imported.name}"
    qualified_assignments: dict[str, list[str | None]] = {}
    for node in assignment_nodes:
        target: ast.expr | None = None
        value: ast.expr | None = None
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
        ):
            target = node.targets[0]
            value = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            target = node.target
            value = node.value
        if isinstance(target, ast.Name) and value is not None:
            qualified_assignments.setdefault(target.id, []).append(
                _resolved_qualified_name(value, result)
            )
    for name, resolved_values in qualified_assignments.items():
        if len(resolved_values) == 1 and resolved_values[0] is not None:
            result[name] = resolved_values[0]
    for node in assignment_nodes:
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], (ast.Tuple, ast.List))
            and isinstance(node.value, ast.Call)
        ):
            factory = _resolved_qualified_name(node.value.func, result)
            targets = node.targets[0].elts
            if (
                factory == "pontius.cupy_sparse_incidence._cupy_modules"
                and targets
                and isinstance(targets[0], ast.Name)
            ):
                result[targets[0].id] = "cupy"
    return result


def _review_function_registry(
    parsed: Mapping[str, ast.Module],
) -> dict[str, _ReviewFunction]:
    registry: dict[str, _ReviewFunction] = {}

    def register(key: str, definition: _ReviewFunction) -> None:
        previous = registry.get(key)
        if previous is not None and previous != definition:
            raise InventoryError(
                f"ambiguous design helper registry key: {key}"
            )
        registry[key] = definition

    for relative_path, tree in parsed.items():
        aliases = _module_import_aliases(tree)
        assignments = _static_assignments(tree.body)
        source_path = PurePosixPath(relative_path)
        module_name = ".".join(source_path.with_suffix("").parts)
        shorthand = source_path.stem
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                definition = _ReviewFunction(
                    relative_path,
                    node,
                    aliases,
                    assignments,
                    None,
                )
                for key in (
                    f"{relative_path}::{node.name}",
                    f"{module_name}.{node.name}",
                    f"{shorthand}.{node.name}",
                ):
                    register(key, definition)
            elif isinstance(node, ast.ClassDef):
                for method in node.body:
                    if not isinstance(
                        method,
                        (ast.FunctionDef, ast.AsyncFunctionDef),
                    ):
                        continue
                    definition = _ReviewFunction(
                        relative_path,
                        method,
                        aliases,
                        assignments,
                        node.name,
                    )
                    register(
                        f"{relative_path}::{node.name}::{method.name}",
                        definition,
                    )
                    register(
                        f"{module_name}.{node.name}.{method.name}",
                        definition,
                    )
                    register(
                        f"{shorthand}.{node.name}.{method.name}",
                        definition,
                    )
    return registry


def _helper_is_bound(
    call: ast.Call,
    definition: _ReviewFunction,
    aliases: Mapping[str, str],
) -> bool:
    if definition.class_name is None:
        return False
    raw = _qualified_name(call.func)
    if raw is not None and raw.startswith(("self.", "cls.")):
        return True
    decorators = {
        _resolved_qualified_name(decorator, definition.aliases)
        for decorator in definition.node.decorator_list
    }
    if "classmethod" not in decorators:
        return False
    resolved = _resolved_qualified_name(call.func, aliases)
    local_name = f"{definition.class_name}.{definition.node.name}"
    return resolved is not None and (
        resolved == local_name or resolved.endswith(f".{local_name}")
    )


def _bind_helper_arguments(
    call: ast.Call,
    definition: _ReviewFunction,
    aliases: Mapping[str, str],
) -> dict[str, tuple[ast.expr, bool]] | None:
    arguments = definition.node.args
    if (
        arguments.vararg is not None
        or arguments.kwarg is not None
        or any(isinstance(value, ast.Starred) for value in call.args)
        or any(keyword.arg is None for keyword in call.keywords)
    ):
        return None
    positional = [*arguments.posonlyargs, *arguments.args]
    if _helper_is_bound(call, definition, aliases):
        if not positional:
            return None
        positional = positional[1:]
    if len(call.args) > len(positional):
        return None
    supplied: dict[str, tuple[ast.expr, bool]] = {}
    for parameter, value in zip(positional, call.args, strict=False):
        supplied[parameter.arg] = (value, False)
    positional_only = {parameter.arg for parameter in arguments.posonlyargs}
    allowed_keywords = {
        parameter.arg for parameter in (*arguments.args, *arguments.kwonlyargs)
    }
    if _helper_is_bound(call, definition, aliases) and arguments.args:
        allowed_keywords.discard(arguments.args[0].arg)
    for keyword in call.keywords:
        if (
            keyword.arg is None
            or keyword.arg in positional_only
            or keyword.arg not in allowed_keywords
            or keyword.arg in supplied
        ):
            return None
        supplied[keyword.arg] = (keyword.value, False)
    positional_defaults = {
        parameter.arg: value
        for parameter, value in zip(
            positional[-len(arguments.defaults) :] if arguments.defaults else (),
            arguments.defaults,
            strict=True,
        )
    }
    for parameter in positional:
        if parameter.arg in supplied:
            continue
        default = positional_defaults.get(parameter.arg)
        if default is None:
            return None
        supplied[parameter.arg] = (default, True)
    for parameter, default in zip(
        arguments.kwonlyargs,
        arguments.kw_defaults,
        strict=True,
    ):
        if parameter.arg in supplied:
            continue
        if default is None:
            return None
        supplied[parameter.arg] = (default, True)
    return supplied


def _unresolved_helper_assignments(
    definition: _ReviewFunction,
) -> dict[str, ast.expr]:
    assignments = dict(definition.module_assignments)
    arguments = definition.node.args
    parameters = [
        *arguments.posonlyargs,
        *arguments.args,
        *arguments.kwonlyargs,
    ]
    if arguments.vararg is not None:
        parameters.append(arguments.vararg)
    if arguments.kwarg is not None:
        parameters.append(arguments.kwarg)
    for parameter in parameters:
        assignments[parameter.arg] = ast.Name(
            id=f"__pontius_unresolved_{parameter.arg}",
            ctx=ast.Load(),
        )
    return assignments


def _resolved_helper(
    call: ast.Call,
    *,
    relative_path: str,
    class_name: str | None,
    aliases: Mapping[str, str],
    registry: Mapping[str, _ReviewFunction],
) -> tuple[str, _ReviewFunction] | None:
    raw = _qualified_name(call.func)
    if raw is None:
        return None
    candidates: list[str] = []
    if "." not in raw:
        candidates.append(f"{relative_path}::{raw}")
    if class_name is not None and raw.startswith(("self.", "cls.")):
        candidates.append(
            f"{relative_path}::{class_name}::{raw.split('.', 1)[1]}"
        )
    if raw.count(".") == 1 and not raw.startswith(("self.", "cls.")):
        candidate_class, candidate_method = raw.split(".", 1)
        candidates.append(
            f"{relative_path}::{candidate_class}::{candidate_method}"
        )
    resolved = _resolved_qualified_name(call.func, aliases)
    if resolved is not None:
        candidates.append(resolved)
    for key in candidates:
        definition = registry.get(key)
        if definition is not None:
            return key, definition
    return None


def _cwd_class(
    node: ast.expr | None,
    assignments: Mapping[str, ast.expr],
) -> str | None:
    if node is None:
        return "target"
    value = _static_value(node, assignments)
    if value == ".":
        return "target"
    if value in {"target", "temporary"}:
        return str(value)
    if isinstance(node, ast.Name) and (
        node.id == "_ROOT" or node.id.endswith("_ROOT")
    ):
        return "target"
    return None


def _process_definition(
    call: ast.Call,
    *,
    aliases: Mapping[str, str],
    assignments: Mapping[str, ast.expr],
) -> tuple[dict[str, object] | None, str | None]:
    function = _resolved_qualified_name(call.func, aliases)
    if function not in _SUBPROCESS_FUNCTIONS:
        return None, None
    if any(keyword.arg is None for keyword in call.keywords):
        return None, "subprocess **kwargs are dynamically unresolved"
    if len(call.args) != 1:
        return None, "subprocess requires one exact argv argument"
    argv_node = call.args[0]
    if not isinstance(argv_node, (ast.List, ast.Tuple)) or not argv_node.elts:
        return None, "subprocess argv is dynamically unresolved"
    first = _resolved_qualified_name(argv_node.elts[0], aliases)
    if first != "sys.executable":
        return None, "subprocess executable is not the active Python worker"
    argv: list[str] = []
    for node in argv_node.elts[1:]:
        value = _static_value(node, assignments)
        if type(value) is not str:
            return None, "subprocess argv tokens are dynamically unresolved"
        argv.append(value)
    if not argv:
        return None, "subprocess Python argv is empty"
    keywords = {keyword.arg: keyword.value for keyword in call.keywords}
    shell = (
        False
        if "shell" not in keywords
        else _static_value(keywords["shell"], assignments)
    )
    if shell is not False:
        return None, "subprocess shell semantics are forbidden or unresolved"
    if "timeout" not in keywords:
        return None, "subprocess timeout must be explicitly bounded"
    timeout = _static_value(keywords["timeout"], assignments)
    if type(timeout) not in (int, float) or timeout <= 0:
        return None, "subprocess timeout is dynamically unresolved"
    environment: dict[str, str] = {}
    if "env" in keywords:
        supplied_environment = _static_value(keywords["env"], assignments)
        if not isinstance(supplied_environment, dict):
            return None, "subprocess environment is dynamically unresolved"
        environment = supplied_environment
    cwd = _cwd_class(keywords.get("cwd"), assignments)
    if cwd is None:
        return None, "subprocess cwd is dynamically unresolved"
    check = (
        function in {"subprocess.check_call", "subprocess.check_output"}
        if "check" not in keywords
        else _static_value(keywords["check"], assignments)
    )
    if type(check) is not bool:
        return None, "subprocess return contract is dynamically unresolved"
    dynamic_program_sha256: str | None = None
    if "-c" in argv:
        indices = [index for index, token in enumerate(argv) if token == "-c"]
        if len(indices) != 1 or indices[0] + 1 >= len(argv):
            return None, "subprocess dynamic Python program is incomplete"
        program = argv[indices[0] + 1]
        dynamic_program_sha256 = sha256(program.encode("utf-8")).hexdigest()
        try:
            program_tree = ast.parse(program, filename="<subprocess-python-c>")
        except SyntaxError:
            return None, "subprocess dynamic Python program cannot be parsed"
        program_aliases = _module_import_aliases(program_tree)
        for child in ast.walk(program_tree):
            if not isinstance(child, ast.Call):
                continue
            if (
                _call_definition(child, program_aliases) is not None
                or _protected_call_blocker_reason(
                    child,
                    program_aliases,
                )
                is not None
            ):
                return (
                    None,
                    "subprocess dynamic Python program contains a protected call",
                )
    definition: dict[str, object] = {
        "executable_role": "python",
        "executable_slot": "active_worker",
        "executable_constraints": {},
        "argv": argv,
        "argv_template": [],
        "dynamic_program_sha256": dynamic_program_sha256,
        "cwd_class": cwd,
        "environment_additions": environment,
        "environment_removals": [],
        "timeout_ns": int(timeout * 1_000_000_000),
        "expected_return_category": (
            "spawned"
            if function == "subprocess.Popen"
            else "success" if check else "completed"
        ),
        "read_roots": [cwd],
        "write_roots": [],
        "fixed_descendant_permission": False,
    }
    return definition, None


def _call_definition(
    call: ast.Call,
    aliases: Mapping[str, str],
) -> dict[str, object] | None:
    qualified = _resolved_callable_name(call.func, aliases)
    if qualified is None:
        return None
    if qualified in _OWNER_CALLS:
        kind = "owner"
        module_name = qualified.rsplit(".", 1)[0]
        return_contract = "opaque"
    elif qualified in _CUDA_CALLS:
        kind, return_contract = _CUDA_CALLS[qualified]
        module_name = "cupy"
    else:
        return None
    return {
        "kind": kind,
        "module_name": module_name,
        "qualified_name": qualified,
        "action": "invoke",
        "maximum_calls": 1,
        "return_contract": return_contract,
    }


def _protected_call_blocker_reason(
    call: ast.Call,
    aliases: Mapping[str, str],
) -> str | None:
    qualified = _resolved_callable_name(call.func, aliases)
    if qualified in _SCIENTIFIC_PROTECTED_CALLS:
        return "protected scientific call awaits explicit classification"
    if qualified in _CUDA_BLOCKED_CALLS:
        return "CuPy action or view is outside the approved call scope"
    if qualified is not None and qualified.startswith("cupy."):
        if qualified not in _CUDA_CALLS:
            return "unregistered CuPy call is unresolved"
    return None


def _is_sensitive_namespace(qualified: str) -> bool:
    if qualified == "cupy" or qualified.startswith("cupy."):
        return True
    protected = _OWNER_CALLS | _SCIENTIFIC_PROTECTED_CALLS
    return any(
        name == qualified or name.startswith(f"{qualified}.")
        for name in protected
    )


def _review_body(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    *,
    item_id: str,
    relative_path: str,
    aliases: Mapping[str, str],
    module_assignments: Mapping[str, ast.expr],
    class_name: str | None,
    helper_registry: Mapping[str, _ReviewFunction],
    active_helpers: frozenset[str] = frozenset(),
    analyzed_sites: list[dict[str, object]] | None = None,
    helper_edges: list[dict[str, object]] | None = None,
    closure_depth: int = 0,
    closure_helper_key: str | None = None,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    if analyzed_sites is None:
        analyzed_sites = []
    if helper_edges is None:
        helper_edges = []
    execution = _execution_scope(node)
    body_aliases = _function_aliases(
        aliases,
        execution.imports,
        execution.assignments,
    )
    assignments = dict(module_assignments)
    assignments.update(_static_assignments(node.body))
    rows: list[dict[str, object]] = []
    blockers: list[dict[str, object]] = []
    dynamic_names: set[str] = set()
    for statement in execution.assignments:
        if (
            isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
            and isinstance(statement.value, ast.Call)
            and _resolved_qualified_name(
                statement.value.func,
                body_aliases,
            )
            == "getattr"
        ):
            base = (
                _resolved_qualified_name(
                    statement.value.args[0],
                    body_aliases,
                )
                if statement.value.args
                else None
            )
            if base and _is_sensitive_namespace(base):
                dynamic_names.add(statement.targets[0].id)
    call_counts: dict[bytes, tuple[dict[str, object], int]] = {}
    for call in execution.calls:
        function = _resolved_qualified_name(call.func, body_aliases)
        callable_name = _resolved_callable_name(call.func, body_aliases)
        if function in _SUBPROCESS_FUNCTIONS:
            analyzed_sites.append(
                {
                    "item_id": item_id,
                    "relative_path": relative_path,
                    "line": int(getattr(call, "lineno", 0)),
                    "sink_kind": "subprocess",
                    "qualified_name": function,
                    "closure_depth": closure_depth,
                    "closure_helper_key": closure_helper_key,
                }
            )
        elif (
            callable_name in _OWNER_CALLS
            or callable_name in _SCIENTIFIC_PROTECTED_CALLS
            or (
                callable_name is not None
                and callable_name.startswith("cupy.")
            )
        ):
            analyzed_sites.append(
                {
                    "item_id": item_id,
                    "relative_path": relative_path,
                    "line": int(getattr(call, "lineno", 0)),
                    "sink_kind": (
                        "cupy"
                        if callable_name is not None
                        and callable_name.startswith("cupy.")
                        else "protected_call"
                    ),
                    "qualified_name": callable_name,
                    "closure_depth": closure_depth,
                    "closure_helper_key": closure_helper_key,
                }
            )
        raw_function = _qualified_name(call.func)
        if raw_function in execution.local_functions:
            blockers.append(
                _review_blocker(
                    item_id,
                    relative_path,
                    call,
                    "directly invoked nested helper closure is unresolved",
                )
            )
            continue
        if function in dynamic_names:
            blockers.append(
                _review_blocker(
                    item_id,
                    relative_path,
                    call,
                    "dynamic sensitive call target is unresolved",
                )
            )
            continue
        helper = _resolved_helper(
            call,
            relative_path=relative_path,
            class_name=class_name,
            aliases=body_aliases,
            registry=helper_registry,
        )
        if helper is not None:
            helper_key, definition = helper
            helper_edges.append(
                {
                    "item_id": item_id,
                    "caller_path": relative_path,
                    "line": int(getattr(call, "lineno", 0)),
                    "callee_path": definition.relative_path,
                    "helper_key": helper_key,
                    "callee_function": definition.node.name,
                    "closure_depth": closure_depth,
                }
            )
            if helper_key in active_helpers:
                blockers.append(
                    _review_blocker(
                        item_id,
                        relative_path,
                        call,
                        "recursive helper capability closure is unresolved",
                    )
                )
                continue
            supplied_arguments = _bind_helper_arguments(
                call,
                definition,
                body_aliases,
            )
            if supplied_arguments is None:
                blockers.append(
                    _review_blocker(
                        item_id,
                        relative_path,
                        call,
                        "dynamic helper arguments are unresolved",
                    )
                )
                _, refused = _review_body(
                    definition.node,
                    item_id=item_id,
                    relative_path=definition.relative_path,
                    aliases=definition.aliases,
                    module_assignments=_unresolved_helper_assignments(definition),
                    class_name=definition.class_name,
                    helper_registry=helper_registry,
                    active_helpers=active_helpers | {helper_key},
                    analyzed_sites=analyzed_sites,
                    helper_edges=helper_edges,
                    closure_depth=closure_depth + 1,
                    closure_helper_key=helper_key,
                )
                blockers.extend(refused)
                continue
            helper_assignments = dict(definition.module_assignments)
            argument_failure = False
            for parameter, (expression, is_default) in (
                supplied_arguments.items()
            ):
                value = _static_value(
                    expression,
                    (
                        definition.module_assignments
                        if is_default
                        else assignments
                    ),
                )
                if value is _STATIC_UNRESOLVED:
                    argument_failure = True
                    break
                helper_assignments[parameter] = ast.parse(
                    repr(value),
                    mode="eval",
                ).body
            if argument_failure:
                blockers.append(
                    _review_blocker(
                        item_id,
                        relative_path,
                        call,
                        "dynamic helper arguments are unresolved",
                    )
                )
                _, refused = _review_body(
                    definition.node,
                    item_id=item_id,
                    relative_path=definition.relative_path,
                    aliases=definition.aliases,
                    module_assignments=_unresolved_helper_assignments(definition),
                    class_name=definition.class_name,
                    helper_registry=helper_registry,
                    active_helpers=active_helpers | {helper_key},
                    analyzed_sites=analyzed_sites,
                    helper_edges=helper_edges,
                    closure_depth=closure_depth + 1,
                    closure_helper_key=helper_key,
                )
                blockers.extend(refused)
                continue
            added, refused = _review_body(
                definition.node,
                item_id=item_id,
                relative_path=definition.relative_path,
                aliases=definition.aliases,
                module_assignments=helper_assignments,
                class_name=definition.class_name,
                helper_registry=helper_registry,
                active_helpers=active_helpers | {helper_key},
                analyzed_sites=analyzed_sites,
                helper_edges=helper_edges,
                closure_depth=closure_depth + 1,
                closure_helper_key=helper_key,
            )
            rows.extend(added)
            blockers.extend(refused)
            continue
        if function is not None and (
            function.startswith("tests.")
            or function.split(".", 1)[0].endswith("_test_support")
        ):
            blockers.append(
                _review_blocker(
                    item_id,
                    relative_path,
                    call,
                    "imported test-local helper closure is unresolved",
                )
            )
            continue
        process, process_error = _process_definition(
            call,
            aliases=body_aliases,
            assignments=assignments,
        )
        if process_error is not None:
            blockers.append(
                _review_blocker(item_id, relative_path, call, process_error)
            )
            continue
        if process is not None:
            capability_id = _capability_id("process", process)
            rows.append(
                {
                    "item_id": item_id,
                    "approval_scope": "design",
                    "capability_kind": "subprocess",
                    "capability_id": capability_id,
                    **process,
                }
            )
            continue
        protected_error = _protected_call_blocker_reason(
            call,
            body_aliases,
        )
        if protected_error is not None:
            blockers.append(
                _review_blocker(
                    item_id,
                    relative_path,
                    call,
                    protected_error,
                )
            )
            continue
        call_definition = _call_definition(call, body_aliases)
        if call_definition is not None:
            count_key = _semantic_bytes(
                {
                    key: value
                    for key, value in call_definition.items()
                    if key != "maximum_calls"
                }
            )
            previous = call_counts.get(count_key)
            call_counts[count_key] = (
                call_definition,
                1 if previous is None else previous[1] + 1,
            )
    for definition, maximum_calls in call_counts.values():
        definition["maximum_calls"] = maximum_calls
        capability_id = _capability_id("call", definition)
        rows.append(
            {
                "item_id": item_id,
                "approval_scope": "design",
                "capability_kind": "call",
                "capability_id": capability_id,
                **definition,
            }
        )
    return rows, blockers


def _definition_time_blockers(
    relative_path: str,
    tree: ast.Module,
    aliases: Mapping[str, str],
    module_assignments: Mapping[str, ast.expr],
    helper_registry: Mapping[str, _ReviewFunction],
) -> list[dict[str, object]]:
    visitor = _DefinitionTimeVisitor()
    visitor.visit(tree)
    blockers: list[dict[str, object]] = []
    for call, class_name in visitor.calls:
        function = _resolved_qualified_name(call.func, aliases)
        reason: str | None = None
        if function in _SUBPROCESS_FUNCTIONS:
            reason = "import-time subprocess call is unowned"
        elif (
            function == "getattr"
            and call.args
            and (
                base := _resolved_qualified_name(call.args[0], aliases)
            )
            is not None
            and _is_sensitive_namespace(base)
        ):
            reason = "import-time dynamic protected target is unowned"
        elif _call_definition(call, aliases) is not None:
            reason = "import-time protected call is unowned"
        elif _protected_call_blocker_reason(call, aliases) is not None:
            reason = "import-time protected call is unowned"
        else:
            helper = _resolved_helper(
                call,
                relative_path=relative_path,
                class_name=class_name,
                aliases=aliases,
                registry=helper_registry,
            )
            if helper is not None:
                helper_key, definition = helper
                rows, refused = _review_body(
                    definition.node,
                    item_id="unowned:import-time",
                    relative_path=definition.relative_path,
                    aliases=definition.aliases,
                    module_assignments=definition.module_assignments,
                    class_name=definition.class_name,
                    helper_registry=helper_registry,
                    active_helpers=frozenset({helper_key}),
                )
                if rows or refused:
                    reason = "import-time helper capability closure is unowned"
            elif function is not None and (
                function.startswith("tests.")
                or function.split(".", 1)[0].endswith("_test_support")
            ):
                reason = "import-time test-local helper closure is unresolved"
        if reason is not None:
            blockers.append(
                _review_blocker(
                    "unowned:import-time",
                    relative_path,
                    call,
                    reason,
                )
            )
    return blockers


def _normalise_review_rows(
    rows: Iterable[Mapping[str, object]],
) -> tuple[list[dict[str, object]], set[str]]:
    subprocess_rows: dict[
        tuple[str, str, str],
        dict[str, object],
    ] = {}
    duplicate_subprocess_items: set[str] = set()
    call_groups: dict[
        tuple[str, bytes],
        tuple[dict[str, object], int],
    ] = {}
    for supplied in rows:
        row = dict(supplied)
        item_id = str(row["item_id"])
        if row["capability_kind"] == "subprocess":
            key = (
                item_id,
                "subprocess",
                str(row["capability_id"]),
            )
            if key in subprocess_rows:
                duplicate_subprocess_items.add(item_id)
            else:
                subprocess_rows[key] = row
            continue
        definition = {
            key: value
            for key, value in row.items()
            if key
            not in {
                "item_id",
                "approval_scope",
                "capability_kind",
                "capability_id",
                "maximum_calls",
            }
        }
        group_key = (item_id, _semantic_bytes(definition))
        previous = call_groups.get(group_key)
        call_groups[group_key] = (
            row,
            int(row["maximum_calls"])
            + (0 if previous is None else previous[1]),
        )
    normalized = [
        row
        for row in subprocess_rows.values()
        if str(row["item_id"]) not in duplicate_subprocess_items
    ]
    for row, maximum_calls in call_groups.values():
        definition = {
            key: value
            for key, value in row.items()
            if key
            not in {
                "item_id",
                "approval_scope",
                "capability_kind",
                "capability_id",
            }
        }
        definition["maximum_calls"] = maximum_calls
        row["maximum_calls"] = maximum_calls
        row["capability_id"] = _capability_id("call", definition)
        if str(row["item_id"]) not in duplicate_subprocess_items:
            normalized.append(row)
    normalized.sort(
        key=lambda row: (
            str(row["approval_scope"]),
            str(row["item_id"]),
            str(row["capability_kind"]),
            str(row["capability_id"]),
        )
    )
    return normalized, duplicate_subprocess_items


def _process_review_rows(
    sources: Mapping[str, bytes],
    inventory: Mapping[str, object],
    item_universe: Iterable[tuple[str, str]],
) -> tuple[
    list[dict[str, object]],
    list[dict[str, object]],
    list[dict[str, object]],
    list[dict[str, object]],
]:
    entries = inventory.get("entries")
    if not isinstance(entries, list):
        raise InventoryError("inventory entries are invalid for design derivation")
    expectations: dict[str, str] = {}
    design_items: set[str] = set()
    for entry in entries:
        if not isinstance(entry, Mapping) or not isinstance(entry.get("assignment"), Mapping):
            raise InventoryError("inventory assignment is invalid for design derivation")
        expectation = entry["assignment"].get("expectation")
        if not isinstance(expectation, Mapping):
            raise InventoryError("inventory expectation is invalid for design derivation")
        expectations[str(entry.get("stable_id"))] = str(expectation.get("kind"))
        if entry["assignment"].get("profile_name") != "historical":
            design_items.add(str(entry.get("stable_id")))
    reviewed_items = {item_id for _, item_id in item_universe}
    parsed: dict[str, ast.Module] = {}
    for relative_path in sorted(sources):
        canonical = _canonical_lf(sources[relative_path])
        try:
            parsed[relative_path] = ast.parse(
                canonical.decode("utf-8"),
                filename=relative_path,
            )
        except (UnicodeDecodeError, SyntaxError) as error:
            raise InventoryError(
                f"design source cannot be parsed: {relative_path}"
            ) from error
    helper_registry = _review_function_registry(parsed)
    rows: list[dict[str, object]] = []
    blockers: list[dict[str, object]] = []
    analyzed_sites: list[dict[str, object]] = []
    helper_edges: list[dict[str, object]] = []
    for relative_path, tree in parsed.items():
        blockers.extend(
            _definition_time_blockers(
                relative_path,
                tree,
                _module_import_aliases(tree),
                _static_assignments(tree.body),
                helper_registry,
            )
        )
    for probe_id, (probe_path, function_name) in (
        REGISTERED_PROBE_IMPLEMENTATIONS.items()
    ):
        if probe_id not in reviewed_items:
            continue
        definition = helper_registry.get(f"{probe_path}::{function_name}")
        if definition is None:
            blockers.append(
                {
                    "item_id": probe_id,
                    "relative_path": probe_path,
                    "line": 0,
                    "reason": "registered probe implementation is absent",
                }
            )
            continue
        added, refused = _review_body(
            definition.node,
            item_id=probe_id,
            relative_path=probe_path,
            aliases=definition.aliases,
            module_assignments=definition.module_assignments,
            class_name=None,
            helper_registry=helper_registry,
            analyzed_sites=analyzed_sites,
            helper_edges=helper_edges,
        )
        rows.extend(added)
        blockers.extend(refused)
    for relative_path, tree in parsed.items():
        aliases = _module_import_aliases(tree)
        module_assignments = _static_assignments(tree.body)
        module_fixture_id = f"fixture:{relative_path}"
        if module_fixture_id in reviewed_items:
            for function in (
                node
                for node in tree.body
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name in {"setUpModule", "tearDownModule"}
            ):
                added, refused = _review_body(
                    function,
                    item_id=module_fixture_id,
                    relative_path=relative_path,
                    aliases=aliases,
                    module_assignments=module_assignments,
                    class_name=None,
                    helper_registry=helper_registry,
                    analyzed_sites=analyzed_sites,
                    helper_edges=helper_edges,
                )
                rows.extend(added)
                blockers.extend(refused)
        for case in (node for node in tree.body if isinstance(node, ast.ClassDef)):
            if not any(_is_test_case_base(base) for base in case.bases):
                continue
            class_fixture_id = f"fixture:{relative_path}::{case.name}"
            if class_fixture_id in reviewed_items:
                for function in (
                    node
                    for node in case.body
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and node.name in {"setUpClass", "tearDownClass"}
                ):
                    added, refused = _review_body(
                        function,
                        item_id=class_fixture_id,
                        relative_path=relative_path,
                        aliases=aliases,
                        module_assignments=module_assignments,
                        class_name=case.name,
                        helper_registry=helper_registry,
                        analyzed_sites=analyzed_sites,
                        helper_edges=helper_edges,
                    )
                    rows.extend(added)
                    blockers.extend(refused)
            for method in (
                node for node in case.body
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name.startswith("test_")
            ):
                stable_id = f"{relative_path}::{case.name}::{method.name}"
                if stable_id not in design_items or stable_id not in reviewed_items:
                    continue
                if expectations.get(stable_id) == "declared_unconditional_skip":
                    continue
                added, refused = _review_body(
                    method,
                    item_id=stable_id,
                    relative_path=relative_path,
                    aliases=aliases,
                    module_assignments=module_assignments,
                    class_name=case.name,
                    helper_registry=helper_registry,
                    analyzed_sites=analyzed_sites,
                    helper_edges=helper_edges,
                )
                rows.extend(added)
                blockers.extend(refused)
    rows, duplicate_subprocess_items = _normalise_review_rows(rows)
    for item_id in sorted(duplicate_subprocess_items):
        blockers.append(
            {
                "item_id": item_id,
                "relative_path": item_id.split("::", 1)[0],
                "line": 0,
                "reason": "subprocess multiplicity is not representable",
            }
        )
    blockers.sort(key=lambda row: (
        str(row["item_id"]), str(row["relative_path"]), int(row["line"])
    ))
    analyzed_sites.sort(
        key=lambda row: (
            str(row["relative_path"]),
            int(row["line"]),
            str(row["sink_kind"]),
            str(row["item_id"]),
            str(row["closure_helper_key"]),
        )
    )
    helper_edges.sort(
        key=lambda row: (
            str(row["caller_path"]),
            int(row["line"]),
            str(row["callee_path"]),
            str(row["item_id"]),
        )
    )
    return rows, blockers, analyzed_sites, helper_edges


_STRING_DECOY_TOKENS = (
    "subprocess.run(",
    "subprocess.Popen(",
    "cupy.",
    "cp.",
)
_TASK2_SYNTHETIC_SOURCE = "tests/test_inventory_and_profiles.py"


def _production_decoy_provenance(
    *,
    relative_path: str,
    node: ast.Constant,
    parents: Mapping[ast.AST, ast.AST],
    profile_by_id: Mapping[str, str],
) -> str:
    function: ast.FunctionDef | ast.AsyncFunctionDef | None = None
    case: ast.ClassDef | None = None
    ancestor: ast.AST = node
    while ancestor in parents:
        ancestor = parents[ancestor]
        if isinstance(ancestor, (ast.FunctionDef, ast.AsyncFunctionDef)):
            function = ancestor
        elif isinstance(ancestor, ast.ClassDef):
            case = ancestor
            break
    profiles: set[str] = set()
    if function is not None and case is not None and function.name.startswith("test_"):
        stable_id = f"{relative_path}::{case.name}::{function.name}"
        profile = profile_by_id.get(stable_id)
        if profile is not None:
            profiles.add(profile)
    elif case is not None:
        prefix = f"{relative_path}::{case.name}::"
        profiles.update(
            profile
            for stable_id, profile in profile_by_id.items()
            if stable_id.startswith(prefix)
        )
    else:
        prefix = f"{relative_path}::"
        profiles.update(
            profile
            for stable_id, profile in profile_by_id.items()
            if stable_id.startswith(prefix)
        )
    if len(profiles) != 1:
        raise InventoryError(
            "string decoy production ownership is absent or ambiguous: "
            f"{relative_path}:{node.lineno}"
        )
    return (
        "historical_production"
        if profiles == {"historical"}
        else "design_production"
    )


def _string_decoy_census(
    sources: Mapping[str, bytes],
    inventory: Mapping[str, object],
) -> dict[str, object]:
    entries = inventory.get("entries")
    if not isinstance(entries, list):
        raise InventoryError("inventory entries are invalid for string census")
    profile_by_id = {
        str(entry["stable_id"]): str(entry["assignment"]["profile_name"])
        for entry in entries
    }
    rows_with_provenance: list[tuple[dict[str, object], str]] = []
    for relative_path in sorted(sources):
        path = PurePosixPath(relative_path)
        if (
            path.parent != PurePosixPath("tests")
            or not path.name.startswith("test")
            or path.suffix != ".py"
        ):
            continue
        tree = ast.parse(
            _canonical_lf(sources[relative_path]).decode("utf-8"),
            filename=relative_path,
        )
        parents = {
            child: parent
            for parent in ast.walk(tree)
            for child in ast.iter_child_nodes(parent)
        }
        for node in ast.walk(tree):
            if not isinstance(node, ast.Constant) or type(node.value) is not str:
                continue
            tokens = [token for token in _STRING_DECOY_TOKENS if token in node.value]
            if not tokens:
                continue
            if relative_path == _TASK2_SYNTHETIC_SOURCE:
                provenance = "task2_synthetic"
            elif relative_path in STABILIZATION_TEST_FILES:
                provenance = "prior_stabilization_synthetic"
            else:
                provenance = _production_decoy_provenance(
                    relative_path=relative_path,
                    node=node,
                    parents=parents,
                    profile_by_id=profile_by_id,
                )
            parent = parents.get(node)
            if parent is None:
                raise InventoryError("string decoy has no AST parent")
            rows_with_provenance.append(({
                "path": relative_path,
                "line": int(node.lineno),
                "parent": type(parent).__name__,
                "tokens": tokens,
            }, provenance))
    rows_with_provenance.sort(key=lambda item: (
        str(item[0]["path"]),
        int(item[0]["line"]),
        str(item[0]["parent"]),
        tuple(item[0]["tokens"]),
    ))
    identities = [
        (str(row["path"]), int(row["line"]))
        for row, _ in rows_with_provenance
    ]
    if len(identities) != len(set(identities)):
        raise InventoryError("string decoy source locations are duplicated")
    rows = [row for row, _ in rows_with_provenance]
    partitions = {
        name: sum(provenance == name for _, provenance in rows_with_provenance)
        for name in (
            "design_production",
            "historical_production",
            "prior_stabilization_synthetic",
            "task2_synthetic",
        )
    }
    return {
        "string_sink_decoy_count": len(rows),
        "string_sink_decoy_sha256": sha256(
            canonical_json_bytes(rows) + b"\n"
        ).hexdigest(),
        "string_sink_decoy_partitions": partitions,
    }


def derive_design_review(
    *,
    baseline_commit: str,
    baseline_root_tree_oid: str,
    inventory_document: Mapping[str, object],
    inventory_document_bytes: bytes,
    sources: Mapping[str, bytes],
    item_universe: Iterable[tuple[str, str]],
) -> dict[str, object]:
    canonical_sources = []
    for relative_path in sorted(sources):
        canonical = _canonical_lf(sources[relative_path])
        canonical_sources.append({
            "relative_path": relative_path,
            "byte_length": len(canonical),
            "canonical_lf_sha256": sha256(canonical).hexdigest(),
        })
    expanded_rows, blockers, analyzed_sites, helper_edges = _process_review_rows(
        sources,
        inventory_document,
        item_universe,
    )
    subprocess_sites = {
        (str(row["relative_path"]), int(row["line"])): int(
            row["closure_depth"]
        )
        for row in analyzed_sites
        if row["sink_kind"] == "subprocess"
    }
    cupy_sites = {
        (
            str(row["relative_path"]),
            int(row["line"]),
            str(row["qualified_name"]),
        )
        for row in analyzed_sites
        if row["sink_kind"] == "cupy"
    }
    helper_subprocess_sites = {
        str(row["closure_helper_key"])
        for row in analyzed_sites
        if row["sink_kind"] == "subprocess"
        and row["closure_depth"] > 0
        and row["closure_helper_key"] is not None
    }
    cross_file_fixture_edges = {
        (
            str(row["caller_path"]),
            int(row["line"]),
            str(row["callee_path"]),
            str(row["helper_key"]),
        )
        for row in helper_edges
        if row["caller_path"] != row["callee_path"]
        and row["callee_function"] == "setUpClass"
    }
    analysis_census = {
        "subprocess_direct_site_count": sum(
            depth == 0 for depth in subprocess_sites.values()
        ),
        "subprocess_helper_site_count": len(helper_subprocess_sites),
        "cross_file_helper_edge_count": len(cross_file_fixture_edges),
        "cupy_call_node_count": len(cupy_sites),
        "analyzed_sites_sha256": sha256(
            _semantic_bytes(analyzed_sites)
        ).hexdigest(),
        **_string_decoy_census(sources, inventory_document),
    }
    authorized_items = {str(row["item_id"]) for row in expanded_rows}
    deny_all = [
        {"item_kind": kind, "item_id": item_id}
        for kind, item_id in sorted(set(item_universe))
        if item_id not in authorized_items
    ]
    row_digest = (
        sha256(_semantic_bytes(expanded_rows)).hexdigest()
        if expanded_rows else ZERO_SHA256
    )
    receipt = {
        "schema_version": RECEIPT_SCHEMA_VERSION,
        "approval_scope": "design",
        "baseline_commit": baseline_commit,
        "baseline_root_tree_oid": baseline_root_tree_oid,
        "inventory_semantic_sha256": _inventory_semantic(inventory_document),
        "inventory_document_sha256": sha256(inventory_document_bytes).hexdigest(),
        "derivation_sources": canonical_sources,
        "spec_capabilities_sha256": row_digest,
        "expanded_rows": expanded_rows,
        "deny_all": deny_all,
    }
    receipt_digest = sha256(canonical_json_bytes(receipt)).hexdigest()
    return {
        "schema_version": REVIEW_SCHEMA_VERSION,
        "receipt": receipt,
        "spec_capabilities_sha256": row_digest,
        "unresolved_dynamic_blockers": blockers,
        "design_review_receipt_sha256": receipt_digest,
        "host_diagnostics": {},
        "analysis_census": analysis_census,
    }


def validate_design_approval(
    review: Mapping[str, object],
    approved_spec_capabilities_sha256: str,
    approved_design_review_receipt_sha256: str,
) -> tuple[Mapping[str, object], ...]:
    if not approved_spec_capabilities_sha256 or not approved_design_review_receipt_sha256:
        raise InventoryError("both approval tokens are required")
    if review.get("unresolved_dynamic_blockers"):
        raise InventoryError("unresolved dynamic design blockers prevent approval")
    row_digest = review.get("spec_capabilities_sha256")
    receipt_digest = review.get("design_review_receipt_sha256")
    if row_digest != approved_spec_capabilities_sha256:
        raise InventoryError("approval design capability token does not match fresh derivation")
    if receipt_digest != approved_design_review_receipt_sha256:
        raise InventoryError("approval design review receipt token does not match fresh derivation")
    receipt = review.get("receipt")
    if not isinstance(receipt, Mapping):
        raise InventoryError("design review receipt is invalid")
    if sha256(canonical_json_bytes(receipt)).hexdigest() != receipt_digest:
        raise InventoryError("design review receipt content drifted")
    rows = receipt.get("expanded_rows")
    if not isinstance(rows, list):
        raise InventoryError("design review rows are invalid")
    if row_digest == ZERO_SHA256 or not rows:
        raise InventoryError("empty design capability review cannot be approved")
    return tuple(rows)


@dataclass(frozen=True, slots=True)
class DesignInputSnapshot:
    repository_root: Path
    inventory_snapshot: object
    inventory_document: Mapping[str, object]
    working_snapshot: WorkingSourcesSnapshot
    profile_snapshot: object | None = None

    def revalidate(self) -> None:
        self.inventory_snapshot.revalidate()
        self.working_snapshot.revalidate()
        if self.profile_snapshot is not None:
            self.profile_snapshot.revalidate()


def _duplicate_rejecting_json_object(
    pairs: Sequence[tuple[str, object]],
) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _review_inventory_document(raw: bytes) -> Mapping[str, object]:
    try:
        document = json.loads(
            raw,
            object_pairs_hook=_duplicate_rejecting_json_object,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise InventoryError("inventory cannot be parsed for design review") from error
    if not isinstance(document, Mapping):
        raise InventoryError("inventory design review document must be an object")
    return document


def _capture_design_inputs(
    repository_root: Path,
    *,
    include_profile: bool,
) -> DesignInputSnapshot:
    root = Path(os.path.abspath(repository_root))
    inventory_path = root / "tests" / "test-inventory.json"
    try:
        inventory_snapshot = secure_filesystem.read_regular_snapshot(
            inventory_path,
            maximum_bytes=MAXIMUM_SOURCE_BYTES,
            root=root,
        )
        inventory_document = _review_inventory_document(inventory_snapshot.raw)
        working_snapshot = _capture_working_sources(
            root,
            include_support_modules=True,
        )
        profile_snapshot = (
            secure_filesystem.read_regular_snapshot(
                root / "tests" / "test-profiles.toml",
                maximum_bytes=MAXIMUM_SOURCE_BYTES,
                root=root,
            )
            if include_profile
            else None
        )
    except InventoryError:
        raise
    except Exception as error:
        raise InventoryError("design inputs cannot be captured securely") from error
    captured = DesignInputSnapshot(
        root,
        inventory_snapshot,
        inventory_document,
        working_snapshot,
        profile_snapshot,
    )
    captured.revalidate()
    return captured


def _derive_captured_design_review(
    captured: DesignInputSnapshot,
) -> dict[str, object]:
    discovery_sources = {
        path: raw
        for path, raw in captured.working_snapshot.sources.items()
        if path.startswith("tests/")
        and PurePosixPath(path).name.startswith("test")
    }
    discovery = discover_test_sources(discovery_sources)
    return derive_design_review(
        baseline_commit=BASELINE_COMMIT,
        baseline_root_tree_oid=BASELINE_ROOT_TREE_OID,
        inventory_document=captured.inventory_document,
        inventory_document_bytes=captured.inventory_snapshot.raw,
        sources=captured.working_snapshot.sources,
        item_universe=_item_universe(captured.inventory_document, discovery),
    )


def _validate_locked_inventory_snapshot(captured: DesignInputSnapshot) -> None:
    configured_git = os.environ.get("PONTIUS_GIT")
    if configured_git is None:
        raise InventoryError("PONTIUS_GIT is required for design inventory validation")
    baseline_sources = _baseline_sources(
        captured.repository_root,
        Path(configured_git),
    )
    working_sources = {
        path: raw
        for path, raw in captured.working_snapshot.sources.items()
        if path.startswith("tests/")
        and PurePosixPath(path).name.startswith("test")
    }
    rebuilt = build_inventory(
        baseline_sources,
        working_sources,
        enforce_baseline_lock=True,
    )
    if canonical_json_bytes(rebuilt) + b"\n" != captured.inventory_snapshot.raw:
        raise InventoryError("checked-in inventory differs from fresh design discovery")


def emit_design_review(
    repository_root: Path,
    destination: Path,
    *,
    enforce_repository_lock: bool = False,
) -> dict[str, object]:
    captured = _capture_design_inputs(repository_root, include_profile=False)
    if enforce_repository_lock:
        _validate_locked_inventory_snapshot(captured)
    review = _derive_captured_design_review(captured)
    captured.revalidate()
    write_atomic_lf(destination, canonical_json_bytes(review) + b"\n")
    return review


def _toml_inline_value(value: object) -> str:
    if type(value) is str:
        return _toml_string(value)
    if type(value) is bool:
        return "true" if value else "false"
    if type(value) is int:
        return str(value)
    if isinstance(value, Mapping):
        rendered = ", ".join(
            f"{key} = {_toml_inline_value(value[key])}" for key in sorted(value)
        )
        return "{ " + rendered + " }" if rendered else "{}"
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(_toml_inline_value(item) for item in value) + "]"
    raise InventoryError("design capability value cannot be rendered as TOML")


def _render_capability_scope(
    rows: Sequence[Mapping[str, object]],
    *,
    approval_scope: str,
    receipt_digest: str,
) -> bytes:
    if approval_scope not in {"design", "historical_review"}:
        raise InventoryError("capability scope is invalid")
    definitions: dict[tuple[str, str], dict[str, object]] = {}
    bindings: list[dict[str, object]] = []
    for supplied in rows:
        row = dict(supplied)
        if row.get("approval_scope") != approval_scope:
            raise InventoryError("capability write received a cross-scope row")
        kind = str(row.get("capability_kind"))
        capability_id = str(row.get("capability_id"))
        if kind not in {"subprocess", "call"} or not capability_id:
            raise InventoryError("design capability row kind or identifier is invalid")
        binding = {
            "item_id": row.pop("item_id"),
            "approval_scope": row.pop("approval_scope"),
            "capability_kind": row.pop("capability_kind"),
            "capability_id": capability_id,
        }
        definition = {
            key: value
            for key, value in row.items()
            if value is not None
        }
        identity = (kind, capability_id)
        previous = definitions.get(identity)
        if previous is not None and previous != definition:
            raise InventoryError("one capability identifier has conflicting definitions")
        definitions[identity] = definition
        bindings.append(binding)
    bindings.sort(
        key=lambda row: (
            str(row["approval_scope"]),
            str(row["item_id"]),
            str(row["capability_kind"]),
            str(row["capability_id"]),
        )
    )
    receipt_name = (
        "design_review_receipt_sha256"
        if approval_scope == "design"
        else "historical_review_receipt_sha256"
    )
    lines = [f"# {receipt_name} = {_toml_string(receipt_digest)}"]
    for (kind, _), definition in sorted(definitions.items()):
        lines.append(f"[[{kind}_capability]]")
        for key, value in definition.items():
            lines.append(f"{key} = {_toml_inline_value(value)}")
        lines.append("")
    for binding in bindings:
        lines.append("[[capability_binding]]")
        for key in (
            "item_id",
            "approval_scope",
            "capability_kind",
            "capability_id",
        ):
            lines.append(f"{key} = {_toml_inline_value(binding[key])}")
        lines.append("")
    return ("\n".join(lines).rstrip("\n") + "\n").encode("ascii")


def _render_design_scope(
    rows: Sequence[Mapping[str, object]],
    *,
    receipt_digest: str,
) -> bytes:
    return _render_capability_scope(
        rows,
        approval_scope="design",
        receipt_digest=receipt_digest,
    )


def _replace_root_digest(raw: bytes, field: str, digest: str) -> bytes:
    prefix = f"{field} = \"".encode("ascii")
    lines = raw.splitlines(keepends=True)
    matches = [index for index, line in enumerate(lines) if line.startswith(prefix)]
    if len(matches) != 1 or _HEX64.fullmatch(digest) is None:
        raise InventoryError(f"profile root {field} cannot be replaced exactly")
    lines[matches[0]] = prefix + digest.encode("ascii") + b"\"\n"
    return b"".join(lines)


def _replace_design_scope(
    profile_raw: bytes,
    rows: Sequence[Mapping[str, object]],
    *,
    spec_digest: str,
    receipt_digest: str,
) -> bytes:
    if (
        profile_raw.startswith(b"\xef\xbb\xbf")
        or b"\r" in profile_raw
        or not profile_raw.endswith(b"\n")
    ):
        raise InventoryError("profile bytes are not canonical LF")
    begin = b"# BEGIN GENERATED DESIGN SCOPE\n"
    end = b"# END GENERATED DESIGN SCOPE\n"
    if profile_raw.count(begin) != 1 or profile_raw.count(end) != 1:
        raise InventoryError("profile design scope markers are invalid")
    prefix, remainder = profile_raw.split(begin)
    _, suffix = remainder.split(end)
    updated = _replace_root_digest(prefix, "spec_capabilities_sha256", spec_digest)
    design = _render_design_scope(rows, receipt_digest=receipt_digest)
    return updated + begin + design + end + suffix


_SCOPE_MARKERS = {
    "design": (
        b"# BEGIN GENERATED DESIGN SCOPE\n",
        b"# END GENERATED DESIGN SCOPE\n",
    ),
    "historical_review": (
        b"# BEGIN GENERATED HISTORICAL SCOPE\n",
        b"# END GENERATED HISTORICAL SCOPE\n",
    ),
}


def _scope_content(raw: bytes, scope: str) -> bytes:
    begin, end = _SCOPE_MARKERS[scope]
    if raw.count(begin) != 1 or raw.count(end) != 1:
        raise InventoryError(f"profile {scope} scope markers are invalid")
    _, remainder = raw.split(begin)
    content, _ = remainder.split(end)
    return content


def _replace_scope_content(raw: bytes, scope: str, content: bytes) -> bytes:
    begin, end = _SCOPE_MARKERS[scope]
    if raw.count(begin) != 1 or raw.count(end) != 1:
        raise InventoryError(f"profile {scope} scope markers are invalid")
    prefix, remainder = raw.split(begin)
    _, suffix = remainder.split(end)
    return prefix + begin + content + end + suffix


def _scope_receipt_digest(content: bytes, scope: str) -> str | None:
    name = (
        "design_review_receipt_sha256"
        if scope == "design"
        else "historical_review_receipt_sha256"
    )
    pattern = re.compile(
        rb"^# " + name.encode("ascii") + rb" = \"([0-9a-f]{64})\"$",
        re.MULTILINE,
    )
    matches = pattern.findall(content)
    if len(matches) > 1:
        raise InventoryError(f"profile {scope} receipt binding is duplicated")
    return matches[0].decode("ascii") if matches else None


def _profile_document(raw: bytes) -> Mapping[str, object]:
    if (
        raw.startswith(b"\xef\xbb\xbf")
        or b"\r" in raw
        or not raw.endswith(b"\n")
    ):
        raise InventoryError("profile bytes are not canonical LF")
    try:
        document = tomllib.loads(raw.decode("utf-8", errors="strict"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as error:
        raise InventoryError("profile is not strict UTF-8 TOML") from error
    if not isinstance(document, Mapping):
        raise InventoryError("profile TOML root must be a table")
    return document


def _expanded_profile_capability_rows(
    document: Mapping[str, object],
) -> dict[str, list[dict[str, object]]]:
    definitions: dict[tuple[str, str], Mapping[str, object]] = {}
    for kind, table_name in (
        ("subprocess", "subprocess_capability"),
        ("call", "call_capability"),
    ):
        values = document.get(table_name, [])
        if not isinstance(values, list):
            raise InventoryError(f"profile {table_name} must be a table array")
        for supplied in values:
            if not isinstance(supplied, Mapping):
                raise InventoryError(f"profile {table_name} row is invalid")
            normalized = dict(supplied)
            if kind == "subprocess":
                normalized.setdefault("dynamic_program_sha256", None)
            capability_id = normalized.get("capability_id")
            if type(capability_id) is not str or not capability_id:
                raise InventoryError("profile capability identifier is invalid")
            identity = (kind, capability_id)
            if identity in definitions:
                raise InventoryError("profile capability definition is duplicated")
            definitions[identity] = normalized
    bindings = document.get("capability_binding", [])
    if not isinstance(bindings, list):
        raise InventoryError("profile capability_binding must be a table array")
    rows: dict[str, list[dict[str, object]]] = {
        "design": [],
        "historical_review": [],
    }
    referenced: dict[tuple[str, str], str] = {}
    seen_bindings: set[tuple[str, str, str, str]] = set()
    for supplied in bindings:
        if not isinstance(supplied, Mapping):
            raise InventoryError("profile capability binding row is invalid")
        try:
            scope = str(supplied["approval_scope"])
            item_id = str(supplied["item_id"])
            kind = str(supplied["capability_kind"])
            capability_id = str(supplied["capability_id"])
        except KeyError as error:
            raise InventoryError("profile capability binding is incomplete") from error
        if scope not in rows or kind not in {"subprocess", "call"}:
            raise InventoryError("profile capability binding kind/scope is invalid")
        identity = (scope, item_id, kind, capability_id)
        if identity in seen_bindings:
            raise InventoryError("profile capability binding is duplicated")
        seen_bindings.add(identity)
        definition_identity = (kind, capability_id)
        definition = definitions.get(definition_identity)
        if definition is None:
            raise InventoryError("profile capability binding is dangling")
        previous_scope = referenced.get(definition_identity)
        if previous_scope is not None and previous_scope != scope:
            raise InventoryError("profile capability definition crosses scopes")
        referenced[definition_identity] = scope
        row = {
            "item_id": item_id,
            "approval_scope": scope,
            "capability_kind": kind,
        }
        row.update(definition)
        rows[scope].append(row)
    if set(definitions) != set(referenced):
        raise InventoryError("profile capability definition is unused")
    for scope_rows in rows.values():
        scope_rows.sort(
            key=lambda row: (
                str(row["approval_scope"]),
                str(row["item_id"]),
                str(row["capability_kind"]),
                str(row["capability_id"]),
            )
        )
    return rows


def _validate_profile_capability_scopes(
    raw: bytes,
) -> tuple[Mapping[str, object], dict[str, list[dict[str, object]]]]:
    document = _profile_document(raw)
    rows = _expanded_profile_capability_rows(document)
    for scope, field in (
        ("design", "spec_capabilities_sha256"),
        ("historical_review", "capability_bindings_sha256"),
    ):
        digest = document.get(field)
        if type(digest) is not str or _HEX64.fullmatch(digest) is None:
            raise InventoryError(f"profile {field} is invalid")
        content = _scope_content(raw, scope)
        receipt = _scope_receipt_digest(content, scope)
        if not rows[scope]:
            if digest != ZERO_SHA256 or receipt is not None or content:
                raise InventoryError(f"empty {scope} scope is not canonical zero mode")
        elif (
            digest == ZERO_SHA256
            or digest != sha256(_semantic_bytes(rows[scope])).hexdigest()
            or receipt is None
        ):
            raise InventoryError(f"approved {scope} scope is not self-consistent")
    return document, rows


def _profile_without_approvals(raw: bytes) -> bytes:
    result = _replace_root_digest(raw, "spec_capabilities_sha256", ZERO_SHA256)
    result = _replace_root_digest(
        result,
        "capability_bindings_sha256",
        ZERO_SHA256,
    )
    for scope in ("design", "historical_review"):
        result = _replace_scope_content(result, scope, b"")
    return result


def preserve_approved_profile_scopes(
    generated: bytes,
    existing: bytes,
    *,
    existing_inventory: bytes,
    generated_inventory: bytes,
    review: Mapping[str, object],
) -> bytes:
    document, rows = _validate_profile_capability_scopes(existing)
    generated_document, generated_rows = _validate_profile_capability_scopes(generated)
    if any(generated_rows.values()):
        raise InventoryError("ordinary profile generation unexpectedly approved a scope")
    design_digest = str(document["spec_capabilities_sha256"])
    historical_digest = str(document["capability_bindings_sha256"])
    if design_digest == ZERO_SHA256 and historical_digest == ZERO_SHA256:
        return generated
    if existing_inventory != generated_inventory:
        raise InventoryError("approved capability inventory drift requires renewed review")
    if _profile_without_approvals(existing) != _profile_without_approvals(generated):
        raise InventoryError("approved profile structure drift requires renewed review")
    if design_digest != ZERO_SHA256:
        content = _scope_content(existing, "design")
        receipt = _scope_receipt_digest(content, "design")
        validate_design_approval(review, design_digest, str(receipt))
    if historical_digest != ZERO_SHA256 and not rows["historical_review"]:
        raise InventoryError("approved historical scope rows are absent")
    result = generated
    for scope, field in (
        ("design", "spec_capabilities_sha256"),
        ("historical_review", "capability_bindings_sha256"),
    ):
        digest = str(document[field])
        result = _replace_root_digest(result, field, digest)
        result = _replace_scope_content(
            result,
            scope,
            _scope_content(existing, scope),
        )
    if generated_document["schema_version"] != document["schema_version"]:
        raise InventoryError("approved profile schema changed")
    return result


def write_design_capabilities(
    repository_root: Path,
    *,
    approved_spec_capabilities_sha256: str,
    approved_design_review_receipt_sha256: str,
    enforce_repository_lock: bool = False,
) -> None:
    captured = _capture_design_inputs(repository_root, include_profile=True)
    if enforce_repository_lock:
        _validate_locked_inventory_snapshot(captured)
    review = _derive_captured_design_review(captured)
    rows = validate_design_approval(
        review,
        approved_spec_capabilities_sha256,
        approved_design_review_receipt_sha256,
    )
    if captured.profile_snapshot is None:
        raise InventoryError("profile snapshot is absent during design write")
    _validate_profile_capability_scopes(captured.profile_snapshot.raw)
    updated = _replace_design_scope(
        captured.profile_snapshot.raw,
        rows,
        spec_digest=str(review["spec_capabilities_sha256"]),
        receipt_digest=str(review["design_review_receipt_sha256"]),
    )
    captured.revalidate()
    profile_path = captured.repository_root / "tests" / "test-profiles.toml"
    if enforce_repository_lock:
        configured_git = os.environ.get("PONTIUS_GIT")
        if configured_git is None:
            raise InventoryError("PONTIUS_GIT is required for design publication")
        _with_governance_attribute_lease(
            captured.repository_root,
            Path(configured_git),
            lambda lifetime_check: write_atomic_lf(
                profile_path,
                updated,
                expected_identity=captured.profile_snapshot.identity,
                _lifetime_check=lifetime_check,
            ),
        )
    else:
        write_atomic_lf(
            profile_path,
            updated,
            expected_identity=captured.profile_snapshot.identity,
        )


def parse_arguments(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--check", action="store_true")
    action.add_argument("--write", action="store_true")
    action.add_argument("--emit-design-capability-review", type=Path)
    action.add_argument("--write-design-capabilities", action="store_true")
    parser.add_argument("--approved-spec-capabilities-sha256")
    parser.add_argument("--approved-design-review-receipt-sha256")
    parsed = parser.parse_args(argv)
    if not any(
        (
            parsed.check,
            parsed.write,
            parsed.emit_design_capability_review,
            parsed.write_design_capabilities,
        )
    ):
        parsed.check = True
    return parsed


def main(argv: Sequence[str] | None = None) -> int:
    arguments = parse_arguments(argv)
    repository_root = Path(__file__).resolve().parents[1]
    inventory_path = repository_root / "tests" / "test-inventory.json"
    profile_path = repository_root / "tests" / "test-profiles.toml"
    try:
        if arguments.emit_design_capability_review is not None:
            destination = arguments.emit_design_capability_review
            if (
                not destination.is_absolute()
                or destination.parent.resolve()
                != Path(tempfile.gettempdir()).resolve()
            ):
                raise InventoryError("design review destination must be an absolute OS-temp child")
            emit_design_review(
                repository_root,
                destination,
                enforce_repository_lock=True,
            )
            return 0
        if arguments.write_design_capabilities:
            if (
                not arguments.approved_spec_capabilities_sha256
                or not arguments.approved_design_review_receipt_sha256
            ):
                raise InventoryError("design write requires both approval tokens")
            write_design_capabilities(
                repository_root,
                approved_spec_capabilities_sha256=(
                    arguments.approved_spec_capabilities_sha256
                ),
                approved_design_review_receipt_sha256=(
                    arguments.approved_design_review_receipt_sha256
                ),
                enforce_repository_lock=True,
            )
            return 0
        configured_git = os.environ.get("PONTIUS_GIT")
        if configured_git is None:
            raise InventoryError("PONTIUS_GIT must name an absolute Git executable")
        baseline_sources = _baseline_sources(repository_root, Path(configured_git))
        working_snapshot = _capture_working_sources(
            repository_root,
            include_support_modules=True,
        )
        review_sources = working_snapshot.sources
        working_sources = {
            path: raw
            for path, raw in review_sources.items()
            if path.startswith("tests/")
            and PurePosixPath(path).name.startswith("test")
        }
        inventory = build_inventory(
            baseline_sources, working_sources, enforce_baseline_lock=True
        )
        discovery = discover_test_sources(working_sources)
        inventory_raw = canonical_json_bytes(inventory) + b"\n"
        generated_profile = render_profiles(inventory, discovery)
        existing_inventory = secure_filesystem.read_regular_snapshot(
            inventory_path,
            maximum_bytes=MAXIMUM_SOURCE_BYTES,
            root=repository_root,
        )
        existing_profile = secure_filesystem.read_regular_snapshot(
            profile_path,
            maximum_bytes=MAXIMUM_SOURCE_BYTES,
            root=repository_root,
        )
        review = derive_design_review(
            baseline_commit=BASELINE_COMMIT,
            baseline_root_tree_oid=BASELINE_ROOT_TREE_OID,
            inventory_document=inventory,
            inventory_document_bytes=inventory_raw,
            sources=review_sources,
            item_universe=_item_universe(inventory, discovery),
        )
        profile_raw = preserve_approved_profile_scopes(
            generated_profile,
            existing_profile.raw,
            existing_inventory=existing_inventory.raw,
            generated_inventory=inventory_raw,
            review=review,
        )
        working_snapshot.revalidate()
        existing_inventory.revalidate()
        existing_profile.revalidate()
        if arguments.write:
            _with_governance_attribute_lease(
                repository_root,
                Path(configured_git),
                lambda lifetime_check: _write_governance_pair(
                    inventory_path,
                    inventory_raw,
                    existing_inventory,
                    profile_path,
                    profile_raw,
                    existing_profile,
                    lifetime_check=lifetime_check,
                ),
            )
        else:
            for path, snapshot, expected in (
                (inventory_path, existing_inventory, inventory_raw),
                (profile_path, existing_profile, profile_raw),
            ):
                actual = snapshot.raw
                if b"\r" in actual or actual != expected:
                    relative = path.relative_to(repository_root)
                    raise InventoryError(
                        f"generated governance file differs: {relative}"
                    )
                snapshot.revalidate()
    except (InventoryError, OSError, ValueError) as error:
        print(f"test inventory generation failed: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
