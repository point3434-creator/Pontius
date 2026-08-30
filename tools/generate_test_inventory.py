"""Generate and verify the immutable test ownership and profile lock."""

from __future__ import annotations

import argparse
import ast
import atexit
import builtins
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field, replace
import errno
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
from types import MappingProxyType
from typing import Any, Callable
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
MAXIMUM_ANALYSIS_HELPER_DEPTH = 64
MAXIMUM_ANALYSIS_CHILD_DEPTH = 4
MAXIMUM_ANALYSIS_CONTAINER_ELEMENTS = 4096
MAXIMUM_ANALYSIS_CARDINALITY = 2_147_483_647
MAXIMUM_ANALYSIS_WORK_UNITS = 262_144
MAXIMUM_PENDING_GOVERNANCE_CLEANUPS = 16
GOVERNANCE_CLEANUP_SYNCHRONOUS_RETRIES = 3
GOVERNANCE_WRITER_SECURITY_BOUNDARY = (
    "Governance publication serializes cooperative Pontius writers with "
    "deterministic destination locks; arbitrary same-user namespace mutation "
    "is unsupported."
)
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
    "tests/test_retained_evidence_inventory.py",
    "tests/test_v0a_boundaries.py",
    "tests/test_v0a_contract_faults.py",
    "tests/test_v0a_hand_replay.py",
    "tests/test_v0a_replay.py",
    "tests/test_v0a_trace.py",
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
    ancestor_handles: tuple[int, ...] = ()
    ancestor_chain: tuple[tuple[Path, tuple[int, ...]], ...] = ()
    snapshot_sha256: str | None = None
    descriptor_closed: bool = False
    ancestor_closed: list[bool] | None = None
    descriptor_identity: tuple[int, ...] | None = None
    descriptor_close_attempted: bool = False
    ancestor_close_attempted: list[bool] | None = None
    owner_components: tuple[object, ...] = ()

    def __post_init__(self) -> None:
        self.ancestor_closed = [False for _ in self.ancestor_handles]
        self.ancestor_close_attempted = [False for _ in self.ancestor_handles]
        try:
            self.descriptor_identity = _posix_descriptor_identity(self.descriptor)
        except OSError:
            self.descriptor_identity = None

    def close(self) -> None:
        failures: list[BaseException] = []
        if self.owner_components:
            for component in reversed(self.owner_components):
                if getattr(component, "closed", False):
                    continue
                try:
                    component.close()
                except BaseException as error:
                    failures.append(error)
            if failures:
                raise InventoryError("Git launch lease cleanup failed") from (
                    ExceptionGroup(
                        "Git launch lease cleanup failures",
                        tuple(failures),
                    )
                )
            return
        if not self.descriptor_closed:
            if self.descriptor_close_attempted:
                self.descriptor_closed = True
            else:
                self.descriptor_close_attempted = True
                self.descriptor_closed = True
                try:
                    os.close(self.descriptor)
                except BaseException as error:
                    failures.append(error)
        if self.ancestor_closed is None:
            self.ancestor_closed = [False for _ in self.ancestor_handles]
        if self.ancestor_close_attempted is None:
            self.ancestor_close_attempted = [False for _ in self.ancestor_handles]
        for index in reversed(range(len(self.ancestor_handles))):
            if self.ancestor_closed[index]:
                continue
            if self.ancestor_close_attempted[index]:
                self.ancestor_closed[index] = True
                continue
            handle = self.ancestor_handles[index]
            self.ancestor_close_attempted[index] = True
            self.ancestor_closed[index] = True
            try:
                secure_filesystem._windows_close_directory(handle)
            except BaseException as error:
                failures.append(error)
        if failures:
            raise InventoryError("Git launch lease cleanup failed") from ExceptionGroup(
                "Git launch lease cleanup failures",
                tuple(failures),
            )


@dataclass(frozen=True, slots=True)
class TestMethod:
    relative_path: str
    case_name: str
    method_name: str
    decorator_dumps: tuple[str, ...]
    unconditional_skip_literal: str | None
    has_cupy_decorator: bool
    class_imports_cupy: bool
    applicable_platforms: tuple[str, ...]

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


_DISCOVERY_UNITTEST_MODULE = "unittest_module"
_DISCOVERY_UNITTEST_ALIAS = "unittest_alias"
_DISCOVERY_TESTCASE_ROOT = "testcase_root"
_DISCOVERY_TESTCASE_CLASS = "testcase_class"
_DISCOVERY_PLAIN_CLASS = "plain_class"
_DISCOVERY_UNKNOWN = "unknown"
_DISCOVERY_UNITTEST_CASE_ROOTS = frozenset({
    "FunctionTestCase",
    "IsolatedAsyncioTestCase",
    "TestCase",
})
_DISCOVERY_BUILTIN_CLASS_ROOTS = frozenset(
    name
    for name, value in vars(builtins).items()
    if isinstance(value, type)
)


def _discovery_binding_kind(
    node: ast.expr | None,
    bindings: Mapping[str, str],
) -> str:
    if node is None:
        return _DISCOVERY_UNKNOWN
    if isinstance(node, ast.Name):
        if node.id in _DISCOVERY_BUILTIN_CLASS_ROOTS:
            return _DISCOVERY_PLAIN_CLASS
        return bindings.get(node.id, _DISCOVERY_UNKNOWN)
    if (
        isinstance(node, ast.Attribute)
        and node.attr in _DISCOVERY_UNITTEST_CASE_ROOTS
        and isinstance(node.value, ast.Name)
    ):
        owner = bindings.get(node.value.id)
        if owner in {_DISCOVERY_UNITTEST_MODULE, _DISCOVERY_UNITTEST_ALIAS}:
            return _DISCOVERY_TESTCASE_ROOT
    return _DISCOVERY_UNKNOWN


def _discovery_assignment_is_proven_noncallable(node: ast.expr | None) -> bool:
    if isinstance(node, ast.Constant):
        return type(node.value) in {
            type(None),
            bool,
            int,
            float,
            complex,
            str,
            bytes,
        }
    if isinstance(node, (ast.List, ast.Tuple, ast.Set, ast.Dict)):
        return True
    if isinstance(node, ast.UnaryOp) and isinstance(
        node.op,
        (ast.UAdd, ast.USub, ast.Invert),
    ):
        return isinstance(node.operand, ast.Constant) and type(
            node.operand.value
        ) in {bool, int, float, complex}
    return False


def _discovery_class_decorator_is_proven_safe(node: ast.expr) -> bool:
    """Return whether a known decorator preserves unittest class ancestry."""

    target = node.func if isinstance(node, ast.Call) else node
    qualified = _qualified_name(target)
    return qualified in {
        "dataclass",
        "dataclasses.dataclass",
        "unittest.skip",
        "unittest.skipIf",
        "unittest.skipUnless",
    }


def _discovery_class_member_kinds(
    relative_path: str,
    node: ast.ClassDef,
    *,
    is_test_case: bool,
    enforce_runtime_discovery: bool,
) -> None:
    if not is_test_case:
        return
    for member in node.body:
        if isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if (
                enforce_runtime_discovery
                and isinstance(member, ast.AsyncFunctionDef)
                and member.name.startswith("test")
            ):
                raise InventoryError(
                    "plain unittest.TestCase async method is unsupported: "
                    f"{relative_path}::{node.name}::{member.name}"
                )
            if member.name.startswith("test") and not member.name.startswith(
                "test_"
            ):
                raise InventoryError(
                    "unittest method prefix outside canonical test_ grammar is "
                    f"unsupported: {relative_path}::{node.name}::{member.name}"
                )
            continue
        targets: list[ast.AST] = []
        value: ast.expr | None = None
        if isinstance(member, ast.Assign):
            targets.extend(member.targets)
            value = member.value
        elif isinstance(member, ast.AnnAssign):
            targets.append(member.target)
            value = member.value
        elif isinstance(member, ast.AugAssign):
            targets.append(member.target)
            value = member.value
        elif isinstance(member, ast.NamedExpr):
            targets.append(member.target)
            value = member.value
        elif isinstance(member, ast.ClassDef):
            if member.name.startswith("test"):
                raise InventoryError(
                    "callable unittest test member assignment is unsupported: "
                    f"{relative_path}::{node.name}::{member.name}"
                )
            continue
        for target in targets:
            for name in _python_bound_names(target):
                if not name.startswith("test"):
                    continue
                if name.startswith("test_") and (
                    _discovery_assignment_is_proven_noncallable(value)
                ):
                    continue
                raise InventoryError(
                    "callable or unresolved unittest test member assignment is "
                    f"unsupported: {relative_path}::{node.name}::{name}"
                )


def _supported_unittest_case_nodes(
    relative_path: str,
    tree: ast.Module,
    *,
    enforce_runtime_discovery: bool = True,
) -> tuple[ast.ClassDef, ...]:
    """Return the exact AST-only unittest discovery grammar or fail closed."""

    accepted: list[ast.ClassDef] = []
    bindings: dict[str, str] = {}
    assignments: dict[str, ast.expr] = {}

    def reject_testcase_namespace_mutation(
        target: ast.AST,
        current: Mapping[str, str],
        *,
        line: int,
    ) -> None:
        if not enforce_runtime_discovery:
            return
        if isinstance(target, ast.Name):
            if current.get(target.id) == _DISCOVERY_TESTCASE_CLASS:
                raise InventoryError(
                    "unittest class binding mutation is unsupported: "
                    f"{relative_path}:{line}"
                )
            return
        if not isinstance(target, ast.Attribute):
            return
        if (
            _discovery_binding_kind(target.value, current)
            == _DISCOVERY_TESTCASE_CLASS
            and target.attr.startswith("test")
        ):
            raise InventoryError(
                "post-definition unittest test member mutation is unsupported: "
                f"{relative_path}:{line}"
            )

    def reject_reflective_testcase_namespace_mutation(
        statement: ast.Expr,
        current: Mapping[str, str],
    ) -> None:
        if not enforce_runtime_discovery:
            return
        call = statement.value
        if not isinstance(call, ast.Call) or not isinstance(call.func, ast.Name):
            return
        if call.func.id not in {"setattr", "delattr"} or len(call.args) < 2:
            return
        if (
            _discovery_binding_kind(call.args[0], current)
            != _DISCOVERY_TESTCASE_CLASS
        ):
            return
        attribute = call.args[1]
        if not (
            isinstance(attribute, ast.Constant)
            and type(attribute.value) is str
            and not attribute.value.startswith("test")
        ):
            raise InventoryError(
                "reflective unittest test member mutation is unsupported: "
                f"{relative_path}:{statement.lineno}"
            )

    def merge_bindings(
        alternatives: Sequence[Mapping[str, str]],
    ) -> dict[str, str]:
        names = set().union(*(alternative.keys() for alternative in alternatives))
        result: dict[str, str] = {}
        for name in names:
            kinds = {alternative.get(name) for alternative in alternatives}
            if len(kinds) == 1 and None not in kinds:
                result[name] = next(iter(kinds))
            elif kinds & {_DISCOVERY_TESTCASE_ROOT, _DISCOVERY_TESTCASE_CLASS}:
                result[name] = _DISCOVERY_UNKNOWN
        return result

    def bind_target(
        target: ast.AST,
        kind: str,
        current: dict[str, str],
    ) -> None:
        for name in _python_bound_names(target):
            current[name] = kind

    def visit_statements(
        statements: Sequence[ast.stmt],
        current: dict[str, str],
        *,
        conditional: bool,
    ) -> dict[str, str]:
        for statement in statements:
            if isinstance(statement, ast.Import):
                for imported in statement.names:
                    local = imported.asname or imported.name.split(".", 1)[0]
                    if imported.name == "unittest" or (
                        imported.asname is None
                        and imported.name.startswith("unittest.")
                    ):
                        current[local] = (
                            _DISCOVERY_UNITTEST_MODULE
                            if local == "unittest" and imported.asname is None
                            else _DISCOVERY_UNITTEST_ALIAS
                        )
                    else:
                        current[local] = _DISCOVERY_UNKNOWN
                continue
            if isinstance(statement, ast.ImportFrom):
                if any(imported.name == "*" for imported in statement.names):
                    if statement.module == "unittest" or (
                        statement.module is not None
                        and statement.module.startswith("tests")
                    ):
                        raise InventoryError(
                            "star import can alter unittest discovery shape: "
                            f"{relative_path}:{statement.lineno}"
                        )
                for imported in statement.names:
                    local = imported.asname or imported.name
                    current[local] = (
                        _DISCOVERY_TESTCASE_ROOT
                        if statement.module == "unittest"
                        and imported.name == "TestCase"
                        else _DISCOVERY_UNKNOWN
                    )
                    if local == "load_tests" and current[local] == _DISCOVERY_UNKNOWN:
                        raise InventoryError(
                            "module load_tests customization is unsupported: "
                            f"{relative_path}:{statement.lineno}"
                        )
                continue
            if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if statement.name == "load_tests":
                    raise InventoryError(
                        "module load_tests customization is unsupported: "
                        f"{relative_path}:{statement.lineno}"
                    )
                current[statement.name] = _DISCOVERY_UNKNOWN
                continue
            if isinstance(statement, ast.ClassDef):
                if enforce_runtime_discovery:
                    unsafe_keywords = tuple(
                        keyword
                        for keyword in statement.keywords
                        if not (
                            keyword.arg == "metaclass"
                            and isinstance(keyword.value, ast.Name)
                            and keyword.value.id == "type"
                        )
                    )
                    if unsafe_keywords:
                        raise InventoryError(
                            "unittest class metaclass or keyword transformation is "
                            f"unsupported: {relative_path}::{statement.name}"
                        )
                    if any(
                        not _discovery_class_decorator_is_proven_safe(decorator)
                        for decorator in statement.decorator_list
                    ):
                        raise InventoryError(
                            "unittest class decorator identity is dynamically "
                            f"unresolved: {relative_path}::{statement.name}"
                        )
                base_kinds = tuple(
                    _discovery_binding_kind(base, current)
                    for base in statement.bases
                )
                direct_canonical = bool(
                    len(statement.bases) == 1
                    and _is_test_case_base(statement.bases[0])
                )
                testcase_ancestry = any(
                    kind in {_DISCOVERY_TESTCASE_ROOT, _DISCOVERY_TESTCASE_CLASS}
                    for kind in base_kinds
                )
                if (
                    enforce_runtime_discovery
                    and statement.bases
                    and _DISCOVERY_UNKNOWN in base_kinds
                    and not direct_canonical
                ):
                    raise InventoryError(
                        "unittest class ancestry is dynamically unresolved: "
                        f"{relative_path}::{statement.name}"
                    )
                if testcase_ancestry and (conditional or not direct_canonical):
                    if conditional:
                        reason = "conditional unittest class definition is unsupported"
                    elif len(statement.bases) != 1:
                        reason = "inherited or mixin fixture ownership is unsupported"
                    else:
                        reason = "aliased or inherited unittest class is unsupported"
                    raise InventoryError(
                        f"{reason}: {relative_path}::{statement.name}"
                    )
                if direct_canonical:
                    _discovery_class_member_kinds(
                        relative_path,
                        statement,
                        is_test_case=True,
                        enforce_runtime_discovery=enforce_runtime_discovery,
                    )
                    accepted.append(statement)
                    current[statement.name] = _DISCOVERY_TESTCASE_CLASS
                else:
                    current[statement.name] = _DISCOVERY_PLAIN_CLASS
                continue
            if isinstance(statement, ast.Expr):
                reject_reflective_testcase_namespace_mutation(statement, current)
            if isinstance(statement, ast.If):
                static = _static_value(statement.test, assignments)
                if static is False:
                    current = visit_statements(
                        statement.orelse,
                        dict(current),
                        conditional=conditional,
                    )
                    continue
                if static is True:
                    entered = visit_statements(
                        statement.body,
                        dict(current),
                        conditional=True,
                    )
                    current.clear()
                    current.update(entered)
                    continue
                alternatives = [
                    visit_statements(
                        statement.body,
                        dict(current),
                        conditional=True,
                    ),
                    visit_statements(
                        statement.orelse,
                        dict(current),
                        conditional=True,
                    ),
                ]
                current.clear()
                current.update(merge_bindings(alternatives))
                continue
            compound_suites: list[Sequence[ast.stmt]] = []
            if isinstance(statement, (ast.For, ast.AsyncFor, ast.While)):
                compound_suites.extend((statement.body, statement.orelse))
            elif isinstance(statement, (ast.With, ast.AsyncWith)):
                compound_suites.append(statement.body)
            else:
                try_types = (ast.Try,)
                if hasattr(ast, "TryStar"):
                    try_types = (*try_types, ast.TryStar)
                if isinstance(statement, try_types):
                    compound_suites.extend(
                        (statement.body, statement.orelse, statement.finalbody)
                    )
                    compound_suites.extend(
                        handler.body for handler in statement.handlers
                    )
                elif isinstance(statement, ast.Match):
                    compound_suites.extend(case.body for case in statement.cases)
            if compound_suites:
                alternatives = [dict(current)]
                alternatives.extend(
                    visit_statements(
                        suite,
                        dict(current),
                        conditional=True,
                    )
                    for suite in compound_suites
                )
                current.clear()
                current.update(merge_bindings(alternatives))
                continue
            targets: list[ast.AST] = []
            value: ast.expr | None = None
            if isinstance(statement, ast.Assign):
                targets.extend(statement.targets)
                value = statement.value
            elif isinstance(statement, ast.AnnAssign):
                targets.append(statement.target)
                value = statement.value
            elif isinstance(statement, ast.AugAssign):
                targets.append(statement.target)
                value = statement.value
            elif isinstance(statement, ast.Delete):
                for target in statement.targets:
                    reject_testcase_namespace_mutation(
                        target,
                        current,
                        line=statement.lineno,
                    )
                    for name in _python_bound_names(target):
                        current.pop(name, None)
                        assignments.pop(name, None)
                continue
            if targets:
                for target in targets:
                    reject_testcase_namespace_mutation(
                        target,
                        current,
                        line=statement.lineno,
                    )
                kind = _discovery_binding_kind(value, current)
                if kind == _DISCOVERY_TESTCASE_CLASS:
                    raise InventoryError(
                        "module alias duplicates unittest class discovery: "
                        f"{relative_path}:{statement.lineno}"
                    )
                for target in targets:
                    bound = _python_bound_names(target)
                    if "load_tests" in bound and not (
                        _discovery_assignment_is_proven_noncallable(value)
                    ):
                        raise InventoryError(
                            "module load_tests customization is unsupported: "
                            f"{relative_path}:{statement.lineno}"
                        )
                    bind_target(target, kind, current)
                    for name in bound:
                        if value is not None:
                            assignments[name] = value
                        else:
                            assignments.pop(name, None)
        return current

    visit_statements(tree.body, bindings, conditional=False)
    return tuple(accepted)


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


def _unittest_condition_kind(
    node: ast.expr,
    conditional_aliases: Mapping[str, str],
) -> str | None:
    if not isinstance(node, ast.Call):
        return None
    callable_name = _conditional_callable_name(
        node.func,
        conditional_aliases,
    )
    if callable_name == _UNRESOLVED_CONDITIONAL_SKIP:
        raise InventoryError("conditional skip decorator alias is unresolved")
    if callable_name not in {"unittest.skipIf", "unittest.skipUnless"}:
        if node.args and any(
            isinstance(candidate, ast.Attribute)
            and isinstance(candidate.value, ast.Name)
            and candidate.value.id == "os"
            and candidate.attr == "name"
            for candidate in ast.walk(node.args[0])
        ):
            raise InventoryError(
                "conditional skip decorator alias is unsupported"
            )
        return None
    if len(node.args) != 2 or node.keywords:
        raise InventoryError("conditional skip has an unsupported signature")
    return callable_name.rsplit(".", 1)[1]


def _conditional_callable_name(
    node: ast.expr,
    bindings: Mapping[str, str],
) -> str | None:
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "getattr"
        and len(node.args) == 2
        and not node.keywords
        and isinstance(node.args[1], ast.Constant)
        and node.args[1].value in {"skipIf", "skipUnless"}
    ):
        base = _conditional_callable_name(node.args[0], bindings)
        if base == "unittest":
            return f"unittest.{node.args[1].value}"
        if base == _UNRESOLVED_CONDITIONAL_SKIP:
            return _UNRESOLVED_CONDITIONAL_SKIP
        return None
    supplied = _qualified_name(node)
    if supplied is None:
        return None
    first, separator, remainder = supplied.partition(".")
    resolved = bindings.get(first)
    if resolved is None:
        if supplied in {"unittest.skipIf", "unittest.skipUnless"}:
            return _UNRESOLVED_CONDITIONAL_SKIP
        return None
    if resolved == _UNRESOLVED_CONDITIONAL_SKIP:
        return _UNRESOLVED_CONDITIONAL_SKIP
    return f"{resolved}.{remainder}" if separator else resolved


_UNRESOLVED_CONDITIONAL_SKIP = "__unresolved_conditional_skip__"


def _python_bound_names(target: ast.AST | None) -> set[str]:
    if isinstance(target, ast.Name):
        return {target.id}
    if isinstance(target, (ast.Tuple, ast.List)):
        return set().union(*(_python_bound_names(item) for item in target.elts))
    if isinstance(target, ast.MatchAs):
        names = _python_bound_names(target.pattern)
        if target.name is not None:
            names.add(target.name)
        return names
    if isinstance(target, ast.MatchStar):
        return set() if target.name is None else {target.name}
    if isinstance(target, ast.MatchMapping):
        names = set().union(*(
            _python_bound_names(pattern) for pattern in target.patterns
        ))
        if target.rest is not None:
            names.add(target.rest)
        return names
    if isinstance(target, ast.MatchSequence):
        return set().union(*(
            _python_bound_names(pattern) for pattern in target.patterns
        ))
    if isinstance(target, ast.MatchClass):
        return set().union(*(
            _python_bound_names(pattern)
            for pattern in (*target.patterns, *target.kwd_patterns)
        ))
    if isinstance(target, ast.MatchOr):
        return set().union(*(
            _python_bound_names(pattern) for pattern in target.patterns
        ))
    return set()


def _conditional_skip_aliases(
    nodes: Iterable[ast.stmt],
    inherited: Mapping[str, str] | None = None,
) -> dict[str, str]:
    def invalidate(result: dict[str, str], names: Iterable[str]) -> None:
        for name in names:
            retained = result.get(name)
            if retained is not None and (
                retained in {"unittest", "os"}
                or retained.startswith("unittest.skip")
                or retained == _UNRESOLVED_CONDITIONAL_SKIP
            ):
                result[name] = _UNRESOLVED_CONDITIONAL_SKIP
            else:
                result.pop(name, None)

    def merge(
        first: Mapping[str, str],
        second: Mapping[str, str],
    ) -> dict[str, str]:
        result: dict[str, str] = {}
        for name in set(first) | set(second):
            first_value = first.get(name)
            second_value = second.get(name)
            if first_value == second_value and first_value is not None:
                result[name] = first_value
            elif any(
                value is not None
                and (
                    value.startswith("unittest.skip")
                    or value == _UNRESOLVED_CONDITIONAL_SKIP
                )
                for value in (first_value, second_value)
            ):
                result[name] = _UNRESOLVED_CONDITIONAL_SKIP
        return result

    aliases = dict(inherited or {})
    for node in nodes:
        if isinstance(node, ast.If):
            first = _conditional_skip_aliases(node.body, aliases)
            second = _conditional_skip_aliases(node.orelse, aliases)
            aliases = merge(first, second)
            continue
        if isinstance(node, ast.Import):
            for imported in node.names:
                local = imported.asname or imported.name.split(".", 1)[0]
                if imported.name == "unittest":
                    aliases[local] = "unittest"
                elif imported.name == "os":
                    aliases[local] = "os"
                else:
                    invalidate(aliases, (local,))
            continue
        if isinstance(node, ast.ImportFrom):
            if any(imported.name == "*" for imported in node.names):
                invalidate(aliases, tuple(aliases))
                continue
            for imported in node.names:
                local = imported.asname or imported.name
                if (
                    node.module == "unittest"
                    and imported.name in {"skipIf", "skipUnless"}
                ):
                    aliases[local] = f"unittest.{imported.name}"
                else:
                    invalidate(aliases, (local,))
            continue
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            invalidate(aliases, (node.name,))
            continue
        if isinstance(node, (ast.For, ast.AsyncFor)):
            entered = dict(aliases)
            invalidate(entered, _python_bound_names(node.target))
            entered = _conditional_skip_aliases(node.body, entered)
            entered = _conditional_skip_aliases(node.orelse, entered)
            aliases = merge(aliases, entered)
            continue
        if isinstance(node, (ast.With, ast.AsyncWith)):
            entered = dict(aliases)
            invalidate(
                entered,
                set().union(*(
                    _python_bound_names(item.optional_vars)
                    for item in node.items
                    if item.optional_vars is not None
                )),
            )
            aliases = _conditional_skip_aliases(node.body, entered)
            continue
        try_types = (ast.Try,)
        if hasattr(ast, "TryStar"):
            try_types = (*try_types, ast.TryStar)
        if isinstance(node, try_types):
            body = _conditional_skip_aliases(node.body, aliases)
            alternatives = [_conditional_skip_aliases(node.orelse, body)]
            for handler in node.handlers:
                handler_aliases = dict(aliases)
                if handler.name is not None:
                    invalidate(handler_aliases, (handler.name,))
                alternatives.append(
                    _conditional_skip_aliases(handler.body, handler_aliases)
                )
            combined = alternatives[0]
            for alternative in alternatives[1:]:
                combined = merge(combined, alternative)
            aliases = _conditional_skip_aliases(node.finalbody, combined)
            continue
        if isinstance(node, ast.Match):
            alternatives = [dict(aliases)]
            for case in node.cases:
                case_aliases = dict(aliases)
                invalidate(case_aliases, _python_bound_names(case.pattern))
                alternatives.append(
                    _conditional_skip_aliases(case.body, case_aliases)
                )
            combined = alternatives[0]
            for alternative in alternatives[1:]:
                combined = merge(combined, alternative)
            aliases = combined
            continue
        target: ast.Name | None = None
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
        if target is not None and value is not None:
            resolved = _conditional_callable_name(value, aliases)
            retained = aliases.get(target.id)
            protected_rebinding = retained is not None and (
                retained in {"unittest", "os"}
                or retained == _UNRESOLVED_CONDITIONAL_SKIP
                or (
                    retained.startswith("unittest.skip")
                    and not (
                        resolved is not None
                        and resolved.startswith("unittest.skip")
                    )
                )
            )
            if protected_rebinding and resolved != retained:
                aliases[target.id] = _UNRESOLVED_CONDITIONAL_SKIP
            elif resolved is not None:
                aliases[target.id] = resolved
            elif aliases.get(target.id, "").startswith("unittest.skip") or (
                aliases.get(target.id) == _UNRESOLVED_CONDITIONAL_SKIP
            ):
                aliases[target.id] = _UNRESOLVED_CONDITIONAL_SKIP
            else:
                aliases.pop(target.id, None)
            continue
        assignment_targets: list[ast.AST] = []
        if isinstance(node, ast.Assign):
            assignment_targets.extend(node.targets)
        elif isinstance(node, (ast.AnnAssign, ast.AugAssign)):
            assignment_targets.append(node.target)
        elif isinstance(node, ast.Delete):
            assignment_targets.extend(node.targets)
        invalidate(
            aliases,
            set().union(*(
                _python_bound_names(target) for target in assignment_targets
            )),
        )
        invalidate(
            aliases,
            (
                candidate.target.id
                for candidate in ast.walk(node)
                if isinstance(candidate, ast.NamedExpr)
                and isinstance(candidate.target, ast.Name)
            ),
        )
    return aliases


def _is_supported_dependency_condition(node: ast.expr) -> bool:
    if isinstance(node, ast.Call) and len(node.args) == 1 and not node.keywords:
        return (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "find_spec"
            and isinstance(node.args[0], ast.Constant)
            and node.args[0].value in {"cupy", "scipy"}
        )
    if not (
        isinstance(node, ast.Compare)
        and len(node.ops) == 1
        and isinstance(node.ops[0], ast.Eq)
        and len(node.comparators) == 1
        and isinstance(node.comparators[0], ast.Constant)
        and node.comparators[0].value == 177100
        and isinstance(node.left, ast.Attribute)
        and node.left.attr == "source_occupancies"
        and isinstance(node.left.value, ast.Call)
        and len(node.left.value.args) == 1
        and not node.left.value.keywords
        and isinstance(node.left.value.args[0], ast.Constant)
        and node.left.value.args[0].value == 25
    ):
        return False
    return _qualified_name(node.left.value.func) in {
        "tiles.population_geometry",
        "consumer.population_geometry",
    }


def _platform_condition_values(
    node: ast.expr,
    aliases: Mapping[str, str],
) -> dict[str, bool] | None:
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        inner = _platform_condition_values(node.operand, aliases)
        if inner is None:
            return None
        return {platform: not value for platform, value in inner.items()}
    if _is_supported_dependency_condition(node):
        return None
    if not (
        isinstance(node, ast.Compare)
        and len(node.ops) == 1
        and len(node.comparators) == 1
        and isinstance(node.left, ast.Attribute)
        and isinstance(node.left.value, ast.Name)
        and aliases.get(node.left.value.id, node.left.value.id) == "os"
        and node.left.attr == "name"
        and isinstance(node.comparators[0], ast.Constant)
        and node.comparators[0].value in {"nt", "posix"}
        and isinstance(node.ops[0], (ast.Eq, ast.NotEq))
    ):
        raise InventoryError("conditional skip condition is unsupported")
    expected = node.comparators[0].value
    equals = isinstance(node.ops[0], ast.Eq)
    return {
        "windows": (("nt" == expected) == equals),
        "posix": (("posix" == expected) == equals),
    }


def _decorator_platforms(
    decorators: Sequence[ast.expr],
    conditional_aliases: Mapping[str, str],
) -> tuple[str, ...]:
    applicable = {"windows", "posix"}
    for decorator in decorators:
        condition_kind = _unittest_condition_kind(
            decorator,
            conditional_aliases,
        )
        if condition_kind is None:
            continue
        values = _platform_condition_values(
            decorator.args[0],
            conditional_aliases,
        )
        if values is None:
            continue
        applicable &= {
            platform
            for platform, condition in values.items()
            if condition == (condition_kind == "skipUnless")
        }
    if not applicable:
        raise InventoryError("conditional skip excludes every supported platform")
    return tuple(sorted(applicable))


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
    parsed_sources: dict[str, ast.Module] = {}
    for relative_path in sorted(normalized_sources):
        raw = normalized_sources[relative_path]
        try:
            parsed_sources[relative_path] = ast.parse(
                raw.decode("utf-8", errors="strict"),
                filename=relative_path,
            )
        except (UnicodeDecodeError, SyntaxError) as error:
            raise InventoryError(f"test source cannot be parsed: {relative_path}") from error
    supported_cases = {
        relative_path: _supported_unittest_case_nodes(relative_path, tree)
        for relative_path, tree in parsed_sources.items()
    }
    testcase_exports = {
        ".".join(PurePosixPath(relative_path).with_suffix("").parts): frozenset(
            node.name for node in supported_cases[relative_path]
        )
        for relative_path in parsed_sources
    }

    def module_scope_statements(
        statements: Sequence[ast.stmt],
    ) -> Iterable[ast.stmt]:
        for statement in statements:
            yield statement
            suites: list[Sequence[ast.stmt]] = []
            if isinstance(statement, ast.If):
                suites.extend((statement.body, statement.orelse))
            elif isinstance(statement, (ast.For, ast.AsyncFor, ast.While)):
                suites.extend((statement.body, statement.orelse))
            elif isinstance(statement, (ast.With, ast.AsyncWith)):
                suites.append(statement.body)
            else:
                try_types = (ast.Try,)
                if hasattr(ast, "TryStar"):
                    try_types = (*try_types, ast.TryStar)
                if isinstance(statement, try_types):
                    suites.extend(
                        (statement.body, statement.orelse, statement.finalbody)
                    )
                    suites.extend(handler.body for handler in statement.handlers)
                elif isinstance(statement, ast.Match):
                    suites.extend(case.body for case in statement.cases)
            for suite in suites:
                yield from module_scope_statements(suite)

    def imported_module_name(
        importer: str,
        statement: ast.ImportFrom,
    ) -> str | None:
        if statement.level == 0:
            return statement.module
        importer_parts = importer.split(".")
        package_parts = importer_parts[:-1]
        retained = len(package_parts) - statement.level + 1
        if retained < 0:
            return None
        parts = package_parts[:retained]
        if statement.module:
            parts.extend(statement.module.split("."))
        return ".".join(parts) or None

    def canonical_import_reference(
        expression: ast.expr | None,
        module_aliases: Mapping[str, str],
    ) -> str | None:
        if (
            isinstance(expression, ast.Call)
            and isinstance(expression.func, ast.Name)
            and expression.func.id == "__import__"
            and expression.args
            and isinstance(expression.args[0], ast.Constant)
            and type(expression.args[0].value) is str
        ):
            keyword_arguments = {
                keyword.arg: keyword.value
                for keyword in expression.keywords
                if keyword.arg is not None
            }
            level = (
                expression.args[4]
                if len(expression.args) > 4
                else keyword_arguments.get("level")
            )
            if level is not None and not (
                isinstance(level, ast.Constant)
                and level.value == 0
            ):
                return None
            fromlist = (
                expression.args[3]
                if len(expression.args) > 3
                else keyword_arguments.get("fromlist")
            )
            if fromlist is None:
                has_fromlist = False
            elif isinstance(fromlist, (ast.Tuple, ast.List)) and all(
                isinstance(item, ast.Constant)
                and type(item.value) is str
                for item in fromlist.elts
            ):
                has_fromlist = bool(fromlist.elts)
            elif (
                isinstance(fromlist, ast.Constant)
                and type(fromlist.value) is str
            ):
                has_fromlist = bool(fromlist.value)
            else:
                return None
            module_name = str(expression.args[0].value)
            return (
                module_name
                if has_fromlist
                else module_name.partition(".")[0]
            )
        if isinstance(expression, ast.Attribute):
            base = canonical_import_reference(
                expression.value,
                module_aliases,
            )
            if base is not None:
                return f"{base}.{expression.attr}"
        if (
            isinstance(expression, ast.Call)
            and isinstance(expression.func, ast.Name)
            and expression.func.id == "getattr"
            and len(expression.args) >= 2
            and isinstance(expression.args[1], ast.Constant)
            and type(expression.args[1].value) is str
        ):
            base = canonical_import_reference(
                expression.args[0],
                module_aliases,
            )
            if base is not None:
                return f"{base}.{expression.args[1].value}"
        qualified = _qualified_name(expression)
        if qualified is None:
            return None
        root, separator, tail = qualified.partition(".")
        module = module_aliases.get(root)
        if module is None:
            return None
        return module + (separator + tail if separator else "")

    def assignment_bindings(
        target: ast.AST,
        value: ast.expr,
    ) -> Iterable[tuple[str, ast.expr]]:
        if (
            isinstance(target, (ast.Tuple, ast.List))
            and isinstance(value, (ast.Tuple, ast.List))
            and len(target.elts) == len(value.elts)
        ):
            for child_target, child_value in zip(
                target.elts,
                value.elts,
                strict=True,
            ):
                yield from assignment_bindings(child_target, child_value)
            return
        for name in _python_bound_names(target):
            yield name, value

    def statement_expressions(statement: ast.stmt) -> Iterable[ast.expr]:
        if isinstance(statement, ast.If):
            yield statement.test
        elif isinstance(statement, ast.While):
            yield statement.test
        elif isinstance(statement, (ast.For, ast.AsyncFor)):
            yield statement.iter
        elif isinstance(statement, (ast.With, ast.AsyncWith)):
            yield from (item.context_expr for item in statement.items)
        elif isinstance(statement, ast.Match):
            yield statement.subject
            yield from (
                case.guard for case in statement.cases if case.guard is not None
            )
        elif isinstance(statement, ast.Expr):
            yield statement.value
        elif isinstance(statement, ast.Assign):
            yield statement.value
        elif isinstance(statement, ast.AnnAssign) and statement.value is not None:
            yield statement.value

    for relative_path, tree in parsed_sources.items():
        importer = ".".join(PurePosixPath(relative_path).with_suffix("").parts)
        module_aliases: dict[str, str] = {}
        for statement in module_scope_statements(tree.body):
            if isinstance(statement, ast.Import):
                for imported in statement.names:
                    local = imported.asname or imported.name.split(".", 1)[0]
                    module_aliases[local] = (
                        imported.name
                        if imported.asname is not None
                        else imported.name.split(".", 1)[0]
                    )
                continue
            if isinstance(statement, ast.ImportFrom):
                imported_module = imported_module_name(importer, statement)
                exported_cases = testcase_exports.get(imported_module or "")
                if exported_cases is not None and any(
                    imported.name == "*" or imported.name in exported_cases
                    for imported in statement.names
                ):
                    raise InventoryError(
                        "module-visible imported unittest class is unsupported: "
                        f"{relative_path}:{statement.lineno}"
                    )
                for imported in statement.names:
                    if imported.name == "*" or imported_module is None:
                        continue
                    candidate = f"{imported_module}.{imported.name}"
                    if candidate in testcase_exports:
                        module_aliases[imported.asname or imported.name] = candidate
                continue
            for expression in statement_expressions(statement):
                for candidate in ast.walk(expression):
                    if not isinstance(candidate, ast.NamedExpr):
                        continue
                    canonical = canonical_import_reference(
                        candidate.value,
                        module_aliases,
                    )
                    if canonical is None:
                        continue
                    if any(
                        canonical == f"{module}.{exported}"
                        for module, exports in testcase_exports.items()
                        for exported in exports
                    ):
                        raise InventoryError(
                            "module-visible imported unittest class is unsupported: "
                            f"{relative_path}:{candidate.lineno}"
                        )
            targets: Sequence[ast.AST] = ()
            value: ast.expr | None = None
            if isinstance(statement, ast.Assign):
                targets = statement.targets
                value = statement.value
            elif isinstance(statement, ast.AnnAssign):
                targets = (statement.target,)
                value = statement.value
            elif isinstance(statement, ast.NamedExpr):
                targets = (statement.target,)
                value = statement.value
            if not targets or value is None:
                continue
            for target in targets:
                for name, bound_value in assignment_bindings(target, value):
                    canonical = canonical_import_reference(
                        bound_value,
                        module_aliases,
                    )
                    if canonical is None:
                        continue
                    if any(
                        canonical == f"{module}.{exported}"
                        for module, exports in testcase_exports.items()
                        for exported in exports
                    ):
                        raise InventoryError(
                            "module-visible imported unittest class is unsupported: "
                            f"{relative_path}:{statement.lineno}"
                        )
                    if canonical in testcase_exports:
                        module_aliases[name] = canonical
    for relative_path in sorted(normalized_sources):
        tree = parsed_sources[relative_path]
        module_fixture_names = [
            node.name
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name in {"setUpModule", "tearDownModule"}
        ]
        if len(module_fixture_names) != len(set(module_fixture_names)):
            raise InventoryError(
                f"duplicate module fixture definitions: {relative_path}"
            )
        module_fixture_count = len(module_fixture_names)
        module_members: list[str] = []
        supported_case_ids = {id(case) for case in supported_cases[relative_path]}
        for class_index, class_node in enumerate(tree.body):
            if not (
                isinstance(class_node, ast.ClassDef)
                and id(class_node) in supported_case_ids
            ):
                continue
            if len(class_node.bases) != 1:
                raise InventoryError(
                    "inherited or mixin fixture ownership is unsupported: "
                    f"{relative_path}::{class_node.name}"
                )
            if any(
                _literal_unittest_skip(decorator) is not None
                for decorator in class_node.decorator_list
            ):
                raise InventoryError(
                    "class-level unconditional skip is unsupported: "
                    f"{relative_path}::{class_node.name}"
                )
            class_definition_aliases = _conditional_skip_aliases(
                tree.body[:class_index]
            )
            class_platforms = _decorator_platforms(
                class_node.decorator_list,
                class_definition_aliases,
            )
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
            class_fixture_names: list[str] = []
            per_test_fixture_names: list[str] = []
            for method_index, node in enumerate(class_node.body):
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                if node.name in {"setUpClass", "tearDownClass"}:
                    class_fixture_names.append(node.name)
                if node.name in {"setUp", "tearDown"}:
                    per_test_fixture_names.append(node.name)
                if not node.name.startswith("test_"):
                    continue
                method_definition_aliases = _conditional_skip_aliases(
                    class_node.body[:method_index],
                    class_definition_aliases,
                )
                method_platforms = _decorator_platforms(
                    node.decorator_list,
                    method_definition_aliases,
                )
                applicable_platforms = tuple(
                    sorted(set(class_platforms) & set(method_platforms))
                )
                if not applicable_platforms:
                    raise InventoryError(
                        "conditional skip excludes every supported platform"
                    )
                literal_skips = tuple(
                    (index, literal)
                    for index, decorator in enumerate(node.decorator_list)
                    for literal in (_literal_unittest_skip(decorator),)
                    if literal is not None
                )
                if literal_skips and (
                    len(literal_skips) != 1 or literal_skips[0][0] != 0
                ):
                    raise InventoryError(
                        "unconditional skip must be the single outermost "
                        "method decorator: "
                        f"{relative_path}::{class_node.name}::{node.name}"
                    )
                literal = literal_skips[0][1] if literal_skips else None
                method = TestMethod(
                    relative_path,
                    class_node.name,
                    node.name,
                    tuple(ast.dump(item, include_attributes=False) for item in node.decorator_list),
                    literal,
                    class_has_cupy_decorator
                    or any(_find_spec_cupy(item) for item in node.decorator_list),
                    class_imports_cupy,
                    applicable_platforms,
                )
                class_methods.append(method)
                methods.append(method)
                module_members.append(method.stable_id)
            if len(class_fixture_names) != len(set(class_fixture_names)):
                raise InventoryError(
                    "duplicate class fixture definitions: "
                    f"{relative_path}::{class_node.name}"
                )
            if len(per_test_fixture_names) != len(
                set(per_test_fixture_names)
            ):
                duplicate = next(
                    name
                    for name in per_test_fixture_names
                    if per_test_fixture_names.count(name) > 1
                )
                label = "setup" if duplicate == "setUp" else "teardown"
                raise InventoryError(
                    f"duplicate per-test {label} fixture definitions: "
                    f"{relative_path}::{class_node.name}"
                )
            if class_fixture_names and class_methods:
                fixtures.append(LifecycleDefinition(
                    "class", relative_path, class_node.name,
                    tuple(sorted(item.stable_id for item in class_methods)),
                ))
            elif class_fixture_names:
                raise InventoryError(
                    "class lifecycle fixture has no direct test methods: "
                    f"{relative_path}::{class_node.name}"
                )
        if module_fixture_count and module_members:
            fixtures.append(LifecycleDefinition(
                "module", relative_path, None, tuple(sorted(module_members))
            ))
        elif module_fixture_count:
            raise InventoryError(
                f"module lifecycle fixture has no direct test methods: {relative_path}"
            )
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
    if method.applicable_platforms == ("windows",):
        return {
            "kind": "platform_conditioned",
            "applicable_platforms": ["windows"],
            "skip_safe_reason_code": "requires_windows",
        }
    if method.applicable_platforms == ("posix",):
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


def _windows_ancestor_file_id(ancestor: Path) -> tuple[int, int]:
    """Independently open one ancestor and return its full-width identity.

    CPython <= 3.11 reports a 32-bit ``st_dev`` volume serial while the
    handle-based ``FileIdInfo`` identity is 64-bit, so stat-derived and
    handle-derived identities may never be compared. Every ancestor identity
    is therefore captured and revalidated through its own freshly opened
    directory handle.
    """

    create, _, _, close = secure_filesystem._windows_directory_api()
    handle = create(
        str(ancestor),
        0x00000001 | 0x00000080 | 0x00100000,
        0x00000001 | 0x00000002,
        None,
        3,
        0x02000000 | 0x00200000,
        None,
    )
    invalid = secure_filesystem.ctypes.c_void_p(-1).value
    if not handle or int(handle) == invalid:
        code = secure_filesystem.ctypes.get_last_error()
        raise OSError(code, os.strerror(code), str(ancestor))
    try:
        volume, file_id = secure_filesystem._windows_directory_handle_identity(
            int(handle),
            ancestor,
        )
    finally:
        close(secure_filesystem.wintypes.HANDLE(int(handle)))
    return int(volume), int.from_bytes(file_id, "little")


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
        identity = secure_filesystem._directory_identity(info)
        if os.name == "nt":
            identity = _windows_ancestor_file_id(ancestor) + identity[2:]
        chain.append((ancestor, identity))
    return tuple(chain)


def _revalidate_git_ancestor_chain(
    chain: Sequence[tuple[Path, tuple[int, ...]]],
) -> None:
    for ancestor, expected in chain:
        info = os.lstat(ancestor)
        identity = secure_filesystem._directory_identity(info)
        if os.name == "nt":
            identity = _windows_ancestor_file_id(ancestor) + identity[2:]
        if (
            stat.S_ISLNK(info.st_mode)
            or secure_filesystem._is_any_reparse(info)
            or not stat.S_ISDIR(info.st_mode)
            or identity != expected
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


def _posix_executable_snapshot(raw: bytes, mode: int) -> tuple[int, Path]:
    descriptor: int | None = None
    writable: int | None = None
    try:
        if not hasattr(os, "memfd_create"):
            raise InventoryError("sealed executable snapshots are unavailable")
        flags = getattr(os, "MFD_CLOEXEC", 0) | getattr(
            os,
            "MFD_ALLOW_SEALING",
            0,
        )
        if not flags & getattr(os, "MFD_ALLOW_SEALING", 0):
            raise InventoryError("sealed executable snapshots are unavailable")
        writable = os.memfd_create("pontius-git", flags)
        offset = 0
        while offset < len(raw):
            count = os.write(writable, raw[offset:])
            if count <= 0:
                raise InventoryError("Git executable snapshot write stalled")
            offset += count
        os.fchmod(writable, mode & 0o777)
        os.fsync(writable)
        import fcntl

        seals = (
            fcntl.F_SEAL_SEAL
            | fcntl.F_SEAL_SHRINK
            | fcntl.F_SEAL_GROW
            | fcntl.F_SEAL_WRITE
        )
        fcntl.fcntl(writable, fcntl.F_ADD_SEALS, seals)
        descriptor = writable
        writable = None
        candidates = (
            Path(f"/proc/self/fd/{descriptor}"),
            Path(f"/dev/fd/{descriptor}"),
        )
        launch_path = next(
            (candidate for candidate in candidates if candidate.exists()),
            None,
        )
        if launch_path is None:
            raise InventoryError("descriptor executable snapshots are unavailable")
        return descriptor, launch_path
    except BaseException:
        if descriptor is not None:
            os.close(descriptor)
        raise
    finally:
        if writable is not None:
            os.close(writable)


def _windows_git_ancestor_handles(
    path: Path,
    cleanup_owner: _GitAcquisitionCleanup | None = None,
) -> tuple[
    tuple[int, ...],
    tuple[tuple[Path, tuple[int, ...]], ...],
]:
    chain = _git_ancestor_chain(path)
    create, _, _, _ = secure_filesystem._windows_directory_api()
    handles: list[int] = []
    try:
        for ancestor, expected in chain:
            handle_owner = _WindowsHandleOwner("git_ancestor")
            handle_owner.close_action = lambda owner=handle_owner: (
                secure_filesystem._windows_directory_api()[3](
                    secure_filesystem.wintypes.HANDLE(owner.handle)
                )
            )
            handle_owner.is_open_action = lambda owner=handle_owner: (
                owner.handle is not None
                and _windows_governance_handle_is_open(owner.handle)
            )
            handle_owner.ambiguous_is_open_action = (
                lambda handle: _windows_governance_handle_is_open(handle)
            )
            handle_owner.identity_action = (
                lambda handle, ancestor=ancestor: (
                    secure_filesystem._windows_directory_handle_identity(
                        handle,
                        ancestor,
                    )
                )
            )
            if cleanup_owner is not None:
                cleanup_owner.add(handle_owner)
            handle = create(
                str(ancestor),
                0x00000001 | 0x00000080 | 0x00100000,
                0x00000001 | 0x00000002,
                None,
                3,
                0x02000000 | 0x00200000,
                None,
            )
            invalid = secure_filesystem.ctypes.c_void_p(-1).value
            if not handle or int(handle) == invalid:
                code = secure_filesystem.ctypes.get_last_error()
                raise OSError(code, os.strerror(code), str(ancestor))
            numeric = int(handle)
            if cleanup_owner is not None:
                handle_owner.adopt(numeric)
            handles.append(numeric)
            volume, file_id = secure_filesystem._windows_directory_handle_identity(
                numeric,
                ancestor,
            )
            handle_owner.bind_identity((volume, file_id))
            if (volume, int.from_bytes(file_id, "little")) != expected[:2]:
                raise InventoryError("PONTIUS_GIT ancestor handle identity differs")
        _revalidate_git_ancestor_chain(chain)
        return tuple(handles), chain
    except BaseException as error:
        if cleanup_owner is not None:
            raise
        close_failures: list[BaseException] = []
        for handle in reversed(handles):
            try:
                secure_filesystem._windows_close_directory(handle)
            except BaseException as close_error:
                close_failures.append(close_error)
        if close_failures:
            raise InventoryError(
                "PONTIUS_GIT ancestor lease and cleanup both failed"
            ) from ExceptionGroup(
                "PONTIUS_GIT ancestor lease failures",
                (error, *close_failures),
            )
        raise


def _acquire_git_launch_lease(
    path: Path,
    expected_identity: tuple[int, ...],
    expected_raw: bytes | None = None,
) -> _GitLaunchLease:
    manager = _governance_cleanup_manager()
    manager.retry_pending()
    reservation = manager.reserve()
    cleanup_owner = _GitAcquisitionCleanup()
    descriptor: int | None = None
    ancestor_handles: tuple[int, ...] = ()
    try:
        before = _git_path_stat(path)
        if _git_stat_identity(before) != expected_identity:
            raise InventoryError(
                "PONTIUS_GIT changed before launch lease acquisition"
            )
        if os.name == "nt":
            ancestor_handles, ancestor_chain = (
                _windows_git_ancestor_handles(path, cleanup_owner)
            )
            create, _, close = secure_filesystem._windows_path_api()
            raw_handle_owner = _WindowsHandleOwner("git_executable_handle")
            raw_handle_owner.close_action = lambda owner=raw_handle_owner: close(
                secure_filesystem.wintypes.HANDLE(owner.handle)
            )
            raw_handle_owner.is_open_action = lambda owner=raw_handle_owner: (
                owner.handle is not None
                and _windows_governance_handle_is_open(owner.handle)
            )
            raw_handle_owner.ambiguous_is_open_action = (
                lambda handle: _windows_governance_handle_is_open(handle)
            )
            raw_handle_owner.identity_action = (
                lambda handle: _windows_governance_handle_file_id(handle)
            )
            cleanup_owner.add(raw_handle_owner)
            descriptor_owner = _PosixDescriptorOwner("git_lease")
            cleanup_owner.add(descriptor_owner)
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
            raw_handle_owner.adopt(int(handle))
            raw_handle_owner.bind_identity(expected_identity[:2])
            try:
                descriptor = secure_filesystem.msvcrt.open_osfhandle(
                    int(handle),
                    os.O_RDONLY | getattr(os, "O_BINARY", 0),
                )
            except BaseException:
                raise
            descriptor_owner.adopt(descriptor)
            raw_handle_owner.handle = None
            raw_handle_owner.closed = True
            launch_executable = None
            pass_fds: tuple[int, ...] = ()
            snapshot_sha256 = None
        else:
            ancestor_chain = ()
            raw = _read_git_bytes(path, before)
            if expected_raw is not None and raw != expected_raw:
                raise InventoryError("PONTIUS_GIT bytes changed before snapshot")
            descriptor_owner = _PosixDescriptorOwner("git_lease")
            cleanup_owner.add(descriptor_owner)
            descriptor, launch_executable = _posix_executable_snapshot(
                raw,
                before.st_mode,
            )
            descriptor_owner.adopt(descriptor)
            pass_fds = (descriptor,)
            snapshot_sha256 = sha256(raw).hexdigest()
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
        if not stat.S_ISREG(handle_info.st_mode):
            raise InventoryError("PONTIUS_GIT launch lease identity changed")
        if os.name == "nt":
            if (
                handle_identity[:4] != expected_identity[:4]
                or _git_stat_identity(after) != expected_identity
            ):
                raise InventoryError("PONTIUS_GIT launch lease identity changed")
        elif (
            handle_info.st_size != len(raw)
            or _git_stat_identity(after) != expected_identity
        ):
            raise InventoryError("PONTIUS_GIT executable snapshot changed")
        lease = _GitLaunchLease(
            path,
            expected_identity,
            descriptor,
            launch_executable,
            pass_fds,
            ancestor_handles,
            ancestor_chain,
            snapshot_sha256,
            owner_components=tuple(cleanup_owner.components),
        )
        cleanup_owner.transfer_without_close()
        manager.release(reservation)
        return lease
    except BaseException as error:
        try:
            cleanup_owner.close()
        except BaseException:
            pass
        if not cleanup_owner.closed:
            manager.transfer(reservation, cleanup_owner)
        else:
            manager.release(reservation)
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
    if _git_stat_identity(path_info) != lease.identity:
        raise InventoryError("PONTIUS_GIT launch lease changed")
    if lease.snapshot_sha256 is not None:
        if not hasattr(os, "pread"):
            raise InventoryError("Git snapshot revalidation is unavailable")
        chunks: list[bytes] = []
        offset = 0
        while offset < handle_info.st_size:
            chunk = os.pread(
                lease.descriptor,
                min(1024 * 1024, handle_info.st_size - offset),
                offset,
            )
            if not chunk:
                break
            chunks.append(chunk)
            offset += len(chunk)
        if (
            offset != handle_info.st_size
            or sha256(b"".join(chunks)).hexdigest() != lease.snapshot_sha256
        ):
            raise InventoryError("PONTIUS_GIT sealed snapshot changed")
        return
    if handle_identity[:4] != lease.identity[:4]:
        raise InventoryError("PONTIUS_GIT launch lease changed")
    if os.name == "nt":
        _revalidate_git_ancestor_chain(lease.ancestor_chain)
        if len(lease.ancestor_handles) != len(lease.ancestor_chain):
            raise InventoryError("PONTIUS_GIT ancestor lease is incomplete")
        for handle, (_, expected) in zip(
            lease.ancestor_handles,
            lease.ancestor_chain,
            strict=True,
        ):
            volume, file_id = secure_filesystem._windows_directory_handle_identity(
                handle,
                lease.path.parent,
            )
            if (volume, int.from_bytes(file_id, "little")) != expected[:2]:
                raise InventoryError("PONTIUS_GIT ancestor lease changed")


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
    lease = _acquire_git_launch_lease(git, identity, raw_identity)
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


def _restore_governance_context(
    previous_group: object | None,
    previous_collector: object | None,
) -> None:
    for name, previous in (
        ("group", previous_group),
        ("collector", previous_collector),
    ):
        if previous is None:
            try:
                delattr(_GOVERNANCE_TRANSACTION_CONTEXT, name)
            except AttributeError:
                pass
        else:
            setattr(_GOVERNANCE_TRANSACTION_CONTEXT, name, previous)


@dataclass(frozen=True, slots=True)
class _GovernancePreparedPublication:
    payload: object


@dataclass(frozen=True, slots=True)
class _GovernanceDesignReviewPublication:
    repository_root: Path
    enforce_repository_lock: bool


@dataclass(frozen=True, slots=True)
class _GovernanceDesignCapabilitiesPublication:
    repository_root: Path
    approved_spec_capabilities_sha256: str
    approved_design_review_receipt_sha256: str
    enforce_repository_lock: bool


@dataclass(frozen=True, slots=True)
class _GovernanceInventoryPublication:
    repository_root: Path
    git_path: Path


_GOVERNANCE_PUBLICATION_DERIVATION_TYPES = (
    _GovernancePreparedPublication,
    _GovernanceDesignReviewPublication,
    _GovernanceDesignCapabilitiesPublication,
    _GovernanceInventoryPublication,
)


@dataclass(frozen=True, slots=True)
class _GovernancePublicationOperation:
    slots: tuple[Path, ...]
    derivation: object
    destination_set: _GovernanceDestinationSet = field(init=False)

    def __post_init__(self) -> None:
        if type(self.slots) is not tuple or not self.slots:
            raise InventoryError("governance publication slots are invalid")
        normalized: list[Path] = []
        keys: set[str] = set()
        for supplied in self.slots:
            key, lexical = _GovernanceDestinationSet.normalize(supplied)
            if key in keys:
                raise InventoryError("duplicate governance publication slot")
            keys.add(key)
            normalized.append(lexical)
        if type(self.derivation) not in _GOVERNANCE_PUBLICATION_DERIVATION_TYPES:
            raise InventoryError("governance payload derivation is not closed")
        if type(self.derivation) is _GovernancePreparedPublication:
            payload = self.derivation.payload
            if type(payload) not in (
                _GovernanceSinglePublication,
                _GovernancePairPublication,
            ):
                raise InventoryError("prepared governance payload is invalid")
            if (
                payload.lifetime_check is not None
                or (
                    type(payload) is _GovernanceSinglePublication
                    and payload.post_publish_lifetime_check is not None
                )
            ):
                raise InventoryError(
                    "prepared governance payload cannot contain callbacks"
                )
        object.__setattr__(self, "slots", tuple(normalized))
        object.__setattr__(
            self,
            "destination_set",
            _GovernanceDestinationSet.build(normalized),
        )


@dataclass(frozen=True, slots=True)
class _GovernanceSinglePublication:
    raw: bytes
    value: object = None
    expected_identity: tuple[int, ...] | None | object = field(
        default_factory=lambda: _AUTOMATIC_DESTINATION_IDENTITY
    )
    expected_raw: bytes | None = None
    lifetime_check: Any | None = None
    post_publish_lifetime_check: Any | None = None


@dataclass(frozen=True, slots=True)
class _GovernancePairPublication:
    first_raw: bytes
    second_raw: bytes
    value: object = None
    lifetime_check: Any | None = None


def _derive_governance_publication(
    derivation: object,
) -> _GovernanceSinglePublication | _GovernancePairPublication:
    if type(derivation) is _GovernancePreparedPublication:
        payload = derivation.payload
    elif type(derivation) is _GovernanceDesignReviewPublication:
        payload = _derive_design_review_publication(derivation)
    elif type(derivation) is _GovernanceDesignCapabilitiesPublication:
        payload = _derive_design_capabilities_publication(derivation)
    elif type(derivation) is _GovernanceInventoryPublication:
        payload = _derive_inventory_publication(derivation)
    else:
        raise InventoryError("governance payload derivation is not closed")
    if type(payload) not in (
        _GovernanceSinglePublication,
        _GovernancePairPublication,
    ):
        raise InventoryError("governance publication payload is invalid")
    return payload


def _with_governance_attribute_lease(
    repository_root: Path,
    git_path: Path | None,
    operation: _GovernancePublicationOperation,
) -> object:
    if type(operation) is not _GovernancePublicationOperation:
        raise InventoryError("closed governance publication operation is required")
    manager = _governance_cleanup_manager()
    manager.retry_pending()
    reservation = manager.reserve()
    try:
        lock_set = _GovernanceLockSetLease.acquire(
            operation.destination_set,
            reservation,
        )
    except BaseException:
        manager.release(reservation)
        raise
    group = _GovernanceWriteGroup(lock_set, reservation)
    previous_group = _governance_active_group()
    previous_collector = _governance_transaction_collector()
    lease: _GitLaunchLease | None = None
    environment: dict[str, str] | None = None
    try:
        _GOVERNANCE_TRANSACTION_CONTEXT.group = group
        _GOVERNANCE_TRANSACTION_CONTEXT.collector = []

        def revalidate() -> None:
            nonlocal lease, environment
            if git_path is None:
                return
            if lease is None:
                git, raw_identity, identity = _strict_git_snapshot(git_path)
                lease = _acquire_git_launch_lease(git, identity, raw_identity)
                group.attach_resource(_GitLaunchLeaseOwner(lease))
                temporary_context = tempfile.TemporaryDirectory(
                    prefix="pontius-governance-attributes-"
                )
                temporary_path = Path(temporary_context.__enter__())
                group.attach_resource(
                    _TemporaryEnvironmentOwner(temporary_context, temporary_path)
                )
                environment = _git_environment(git, temporary_path)
            if environment is None:
                raise InventoryError("Git attribute environment is absent")
            _verify_governance_attributes(
                lease,
                repository_root,
                environment,
            )
            _revalidate_git_launch_lease(lease)

        if git_path is not None:
            revalidate()
        payload = _derive_governance_publication(operation.derivation)
        if type(payload) is _GovernanceSinglePublication:
            if len(operation.slots) != 1:
                raise InventoryError(
                    "single publication requires exactly one bound slot"
                )
            write_atomic_lf(
                operation.slots[0],
                payload.raw,
                expected_identity=payload.expected_identity,
                _expected_raw=payload.expected_raw,
                _lifetime_check=payload.lifetime_check,
                _post_publish_lifetime_check=(
                    payload.post_publish_lifetime_check
                ),
            )
        elif type(payload) is _GovernancePairPublication:
            if len(operation.slots) != 2:
                raise InventoryError(
                    "pair publication requires exactly two bound slots"
                )
            _write_governance_pair(
                operation.slots[0],
                payload.first_raw,
                operation.slots[1],
                payload.second_raw,
                lifetime_check=payload.lifetime_check,
            )
        else:
            raise InventoryError("governance publication payload is invalid")
        group.validate_all(revalidate if git_path is not None else None)
    except BaseException as error:
        _restore_governance_context(previous_group, previous_collector)
        group.abort_precommit(error)
        raise AssertionError("unreachable governance attribute abort")
    _restore_governance_context(previous_group, previous_collector)
    group.mark_committed()
    group.finish_committed_cleanup()
    return payload.value


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


@dataclass(frozen=True, slots=True)
class _GovernancePendingDescriptor:
    retry_id: int
    attempts: int
    decision: str
    destination_paths: tuple[str, ...]
    output_sha256: dict[str, str]
    outstanding_owner_roles: tuple[str, ...]
    artifact_paths: tuple[str, ...]
    lock_keys: tuple[str, ...]
    released_lock_keys: tuple[str, ...] = ()


class GovernanceCleanupPendingError(InventoryError):
    def __init__(self, descriptor: _GovernancePendingDescriptor) -> None:
        super().__init__("governance rollback cleanup remains pending")
        self.committed = False
        self.descriptor = descriptor
        self.retry_id = descriptor.retry_id


class GovernanceCommittedWithCleanupFailure(InventoryError):
    def __init__(self, descriptor: _GovernancePendingDescriptor) -> None:
        super().__init__("governance commit completed with cleanup pending")
        self.committed = True
        self.descriptor = descriptor
        self.retry_id = descriptor.retry_id


@dataclass(frozen=True, slots=True)
class _GovernanceCleanupReservation:
    token: int


@dataclass(slots=True)
class _GovernancePendingCleanup:
    owner: object
    attempts: int = 0
    generation: int = 0
    running: bool = False
    last_error: BaseException | None = None
    generation_results: dict[int, tuple[bool, BaseException | None]] = field(
        default_factory=dict
    )
    generation_joiners: dict[int, int] = field(default_factory=dict)


class _GovernanceCleanupManager:
    def __init__(self) -> None:
        self._next_id = 1
        self._reservations: set[int] = set()
        self._pending: dict[int, _GovernancePendingCleanup] = {}
        self._mutex = threading.RLock()
        self._condition = threading.Condition(self._mutex)
        self.atexit_registration_count = 1
        atexit.register(self.retry_at_exit)

    def reserve(self) -> _GovernanceCleanupReservation:
        with self._mutex:
            if (
                len(self._reservations) + len(self._pending)
                >= MAXIMUM_PENDING_GOVERNANCE_CLEANUPS
            ):
                raise InventoryError("governance cleanup capacity is exhausted")
            token = self._next_id
            self._next_id += 1
            self._reservations.add(token)
            return _GovernanceCleanupReservation(token)

    def release(self, reservation: _GovernanceCleanupReservation) -> None:
        with self._mutex:
            self._reservations.discard(reservation.token)

    def transfer(
        self,
        reservation: _GovernanceCleanupReservation,
        owner: object,
    ) -> int:
        with self._mutex:
            if reservation.token not in self._reservations:
                raise InventoryError("governance cleanup reservation is invalid")
            self._reservations.remove(reservation.token)
            self._pending[reservation.token] = _GovernancePendingCleanup(owner)
            return reservation.token

    def _retry_one(self, retry_id: int, *, explicit: bool) -> None:
        with self._condition:
            pending = self._pending.get(retry_id)
            if pending is None:
                if explicit:
                    raise InventoryError("governance cleanup retry ID is absent")
                return
            if pending.running:
                joined_generation = pending.generation
                pending.generation_joiners[joined_generation] = (
                    pending.generation_joiners.get(joined_generation, 0) + 1
                )
                try:
                    while joined_generation not in pending.generation_results:
                        self._condition.wait()
                    succeeded, result_error = pending.generation_results[
                        joined_generation
                    ]
                finally:
                    remaining = pending.generation_joiners[joined_generation] - 1
                    if remaining:
                        pending.generation_joiners[joined_generation] = remaining
                    else:
                        pending.generation_joiners.pop(joined_generation, None)
                    self._condition.notify_all()
                if not succeeded:
                    if result_error is None:
                        raise InventoryError(
                            "governance cleanup generation failure is absent"
                        )
                    raise result_error
                return
            while pending.generation_joiners:
                self._condition.wait()
                current = self._pending.get(retry_id)
                if current is None:
                    return
                if current is not pending:
                    raise InventoryError("governance cleanup retry state changed")
            pending.generation_results.clear()
            pending.running = True
            pending.generation += 1
            generation = pending.generation
            pending.last_error = None
            owner = pending.owner
        try:
            owner.retry_pending_cleanup()
        except BaseException as error:
            with self._condition:
                current = self._pending.get(retry_id)
                if current is pending:
                    pending.attempts += 1
                    pending.running = False
                    pending.last_error = error
                    pending.generation_results[generation] = (False, error)
                self._condition.notify_all()
            raise
        with self._condition:
            current = self._pending.get(retry_id)
            if current is pending:
                pending.running = False
                pending.last_error = None
                pending.generation_results[generation] = (True, None)
                self._pending.pop(retry_id)
            self._condition.notify_all()

    def retry_pending(self, retry_id: int | None = None) -> None:
        with self._mutex:
            selected = (
                (retry_id,)
                if retry_id is not None
                else tuple(sorted(self._pending))
            )
        first_failure: BaseException | None = None
        for selected_id in selected:
            try:
                self._retry_one(selected_id, explicit=retry_id is not None)
            except BaseException as error:
                if first_failure is None:
                    first_failure = error
                continue
        if first_failure is not None:
            raise InventoryError("governance pending cleanup failed") from first_failure

    def pending_descriptors(self) -> tuple[object, ...]:
        with self._mutex:
            selected = tuple(
                (retry_id, pending.owner, pending.attempts)
                for retry_id, pending in sorted(self._pending.items())
            )
        return tuple(
            owner.pending_descriptor(retry_id, attempts)
            for retry_id, owner, attempts in selected
        )

    def retry_at_exit(self) -> None:
        try:
            self.retry_pending()
        except BaseException:
            return


_GOVERNANCE_CLEANUP_MANAGER: _GovernanceCleanupManager | None = None
_GOVERNANCE_CLEANUP_MANAGER_MUTEX = threading.Lock()


def _governance_cleanup_manager() -> _GovernanceCleanupManager:
    global _GOVERNANCE_CLEANUP_MANAGER
    if _GOVERNANCE_CLEANUP_MANAGER is None:
        with _GOVERNANCE_CLEANUP_MANAGER_MUTEX:
            if _GOVERNANCE_CLEANUP_MANAGER is None:
                _GOVERNANCE_CLEANUP_MANAGER = _GovernanceCleanupManager()
    return _GOVERNANCE_CLEANUP_MANAGER


@dataclass(slots=True)
class _WindowsHandleOwner:
    role: str
    handle: int | None = None
    close_action: Any = None
    is_open_action: Any = None
    closed: bool = False
    close_attempted: bool = False
    ambiguous_handle: int | None = None
    ambiguous_is_open_action: Any = None
    identity_action: Any = None
    expected_identity: object | None = None

    def adopt(self, handle: int) -> None:
        if (
            self.handle is not None
            or self.ambiguous_handle is not None
            or self.close_attempted
            or self.closed
        ):
            raise InventoryError("Windows handle slot is already resolved")
        self.handle = handle

    def bind_identity(self, identity: object) -> None:
        self.expected_identity = identity

    def _reconcile_ambiguous_close(self) -> None:
        handle = self.ambiguous_handle
        if handle is None:
            return
        if not callable(self.ambiguous_is_open_action):
            self.ambiguous_handle = None
            self.closed = True
            return
        try:
            is_open = bool(self.ambiguous_is_open_action(handle))
        except BaseException as error:
            raise InventoryError(
                f"{self.role} close outcome is unresolved"
            ) from error
        if not is_open:
            self.ambiguous_handle = None
            self.closed = True
            return
        if self.expected_identity is not None and callable(self.identity_action):
            try:
                current_identity = self.identity_action(handle)
            except BaseException as error:
                raise InventoryError(
                    f"{self.role} close outcome is unresolved"
                ) from error
            if current_identity != self.expected_identity:
                self.ambiguous_handle = None
                self.closed = True
                return
        raise InventoryError(f"{self.role} close outcome is unresolved")

    def close(self) -> None:
        if self.closed:
            return
        if self.ambiguous_handle is not None:
            self._reconcile_ambiguous_close()
            return
        if self.handle is None:
            self.closed = True
            return
        if not callable(self.close_action) or not callable(self.is_open_action):
            raise InventoryError("Windows handle owner actions are absent")
        try:
            is_open = bool(self.is_open_action())
        except BaseException:
            raise
        if not is_open:
            self.handle = None
            self.closed = True
            return
        try:
            result = self.close_action()
        except BaseException:
            handle = self.handle
            self.handle = None
            self.ambiguous_handle = handle
            self.close_attempted = True
            raise
        if result is not None and not bool(result):
            raise InventoryError(f"{self.role} close was refused")
        self.handle = None
        self.close_attempted = True
        self.closed = True

    def retry_pending_cleanup(self) -> None:
        self.close()


def _posix_descriptor_identity(descriptor: int) -> tuple[int, ...]:
    info = os.fstat(descriptor)
    return (
        int(info.st_dev),
        int(info.st_ino),
        int(info.st_mode),
    )


def _posix_descriptor_is_owned(
    descriptor: int,
    expected_identity: tuple[int, ...],
) -> bool:
    try:
        current = _posix_descriptor_identity(descriptor)
    except OSError as error:
        if error.errno == errno.EBADF:
            return False
        raise InventoryError("POSIX descriptor close outcome is unavailable") from error
    return current == expected_identity


@dataclass(slots=True)
class _PosixDescriptorOwner:
    role: str
    descriptor: int | None = None
    close_action: Any = None
    closed: bool = False
    expected_identity: tuple[int, ...] | None = None
    close_attempted: bool = False

    def adopt(self, descriptor: int, close_action: Any | None = None) -> None:
        if self.descriptor is not None or self.close_attempted or self.closed:
            raise InventoryError("POSIX descriptor slot is already resolved")
        self.descriptor = descriptor
        self.close_action = close_action

    def close(self) -> None:
        if self.closed:
            return
        if self.descriptor is None:
            self.closed = True
            return
        if self.close_attempted:
            self.closed = True
            return
        close_action = self.close_action
        descriptor = self.descriptor
        self.descriptor = None
        self.close_attempted = True
        self.closed = True
        try:
            if callable(close_action):
                close_action()
            else:
                os.close(descriptor)
        except BaseException:
            raise

    def retry_pending_cleanup(self) -> None:
        self.close()


@dataclass(slots=True)
class _GitAcquisitionCleanup:
    components: list[object] = field(default_factory=list)
    role: str = "git_lease"
    transferred: bool = False

    @property
    def closed(self) -> bool:
        return self.transferred or all(
            bool(getattr(component, "closed", False))
            for component in self.components
        )

    def add(self, component: object) -> None:
        self.components.append(component)

    def transfer_without_close(self) -> None:
        self.transferred = True

    def close(self) -> None:
        failures: list[BaseException] = []
        for component in reversed(self.components):
            if getattr(component, "closed", False):
                continue
            try:
                component.close()
            except BaseException as error:
                failures.append(error)
        if failures:
            raise InventoryError("partial Git acquisition cleanup failed") from (
                ExceptionGroup("partial Git cleanup failures", tuple(failures))
            )

    def retry_pending_cleanup(self) -> None:
        self.close()

    def pending_descriptor(
        self,
        retry_id: int,
        attempts: int,
    ) -> _GovernancePendingDescriptor:
        roles = tuple(
            sorted(
                {
                    str(getattr(component, "role", "git_lease"))
                    for component in self.components
                    if not getattr(component, "closed", False)
                }
            )
        )
        return _GovernancePendingDescriptor(
            retry_id,
            attempts,
            "acquisition_failed",
            (),
            {},
            roles or (self.role,),
            (),
            (),
            (),
        )


@dataclass(slots=True)
class _PosixParentDirectoryOwner:
    path: Path
    chain: tuple[tuple[Path, tuple[int, ...]], ...]
    descriptor: int
    identity: tuple[int, ...]
    dependents: list[object]
    descriptor_owner: _PosixDescriptorOwner | None = None
    role: str = "lock_parent_directory"
    closed: bool = False
    descriptor_identity: tuple[int, ...] | None = None

    def __post_init__(self) -> None:
        if self.descriptor_owner is not None:
            self.descriptor_identity = self.descriptor_owner.expected_identity
            return
        try:
            self.descriptor_identity = _posix_descriptor_identity(self.descriptor)
        except OSError:
            self.descriptor_identity = None
        self.descriptor_owner = _PosixDescriptorOwner(
            self.role,
            self.descriptor,
            lambda: os.close(self.descriptor),
            expected_identity=self.descriptor_identity,
        )

    def revalidate(self) -> None:
        if self.closed:
            raise InventoryError("bound governance parent is closed")
        _revalidate_governance_directory_chain(self.chain)
        current = os.fstat(self.descriptor)
        if secure_filesystem._directory_identity(current) != self.identity:
            raise InventoryError("bound governance directory identity changed")

    def close(self) -> None:
        if self.closed:
            return
        if any(not getattr(owner, "closed", False) for owner in self.dependents):
            raise InventoryError("governance lock parent still owns lock names")
        if self.descriptor_owner is None:
            raise InventoryError("governance parent descriptor owner is absent")
        self.descriptor_owner.close()
        self.closed = self.descriptor_owner.closed

    def retry_pending_cleanup(self) -> None:
        self.close()


@dataclass(slots=True)
class _PosixDeterministicLockOwner:
    descriptor: int | None = None
    path: Path | None = None
    destination_key: str | None = None
    parent_descriptor: int | None = None
    name: str | None = None
    role: str = "deterministic_lock"
    descriptor_closed: bool = False
    name_unlinked: bool = False
    closed: bool = False
    descriptor_identity: tuple[int, ...] | None = None
    descriptor_close_attempted: bool = False
    acquired: bool = False

    def __post_init__(self) -> None:
        if self.descriptor is None:
            return
        if self.path is None:
            raise InventoryError("POSIX lock artifact path is absent")
        self.acquired = True
        try:
            self.descriptor_identity = _posix_descriptor_identity(self.descriptor)
        except OSError:
            self.descriptor_identity = None

    def adopt(
        self,
        descriptor: int,
        path: Path,
        destination_key: str,
        parent_descriptor: int,
        name: str,
    ) -> None:
        if self.descriptor is not None or self.acquired or self.closed:
            raise InventoryError("POSIX lock owner slot is already resolved")
        self.descriptor = descriptor
        self.path = path
        self.destination_key = destination_key
        self.parent_descriptor = parent_descriptor
        self.name = name
        self.acquired = True

    def close(self) -> None:
        if self.closed:
            return
        if not self.acquired:
            self.closed = True
            return
        if not self.descriptor_closed:
            if self.descriptor is None:
                raise InventoryError("POSIX lock descriptor is absent")
            if self.descriptor_close_attempted:
                self.descriptor_closed = True
            else:
                self.descriptor_close_attempted = True
                self.descriptor_closed = True
                os.close(self.descriptor)
        if not self.name_unlinked:
            if self.parent_descriptor is None or self.name is None:
                if self.path is None:
                    raise InventoryError("POSIX lock artifact path is absent")
                self.path.unlink()
            else:
                os.unlink(self.name, dir_fd=self.parent_descriptor)
            self.name_unlinked = True
        self.closed = True

    def retry_pending_cleanup(self) -> None:
        self.close()


@dataclass(slots=True)
class _WindowsDeterministicLockOwner:
    name: str
    artifact_path: Path | None = None
    destination_key: str | None = None
    handle: int | None = None
    state: str = "unopened"
    disposal_armed: bool = False
    role: str = "deterministic_lock"
    closed: bool = False
    close_attempted: bool = False
    acquired: bool = False

    def arm_disposal(self) -> None:
        if self.handle is None:
            raise InventoryError("governance writer lock handle is absent")
        if self.disposal_armed:
            return
        _windows_dispose_governance_lock(self.handle)
        self.disposal_armed = True
        self.state = "deletion_armed"

    def close(self) -> None:
        if self.closed:
            return
        if self.handle is None:
            if (
                self.acquired
                and self.disposal_armed
                and self.artifact_path is not None
                and self.artifact_path.exists()
            ):
                raise InventoryError("governance writer lock close is unresolved")
            self.closed = True
            self.state = "closed"
            return
        self.arm_disposal()
        handle = self.handle
        try:
            succeeded = _windows_try_close_file(handle)
        except BaseException:
            self.handle = None
            self.close_attempted = True
            self.state = "close_outcome_unknown"
            raise
        if not succeeded:
            raise InventoryError("governance writer lock close was refused")
        self.handle = None
        self.close_attempted = True
        self.closed = True
        self.state = "closed"

    def retry_pending_cleanup(self) -> None:
        self.close()


@dataclass(slots=True)
class _GitLaunchLeaseOwner:
    lease: object
    role: str = "git_lease"
    closed: bool = False

    def close(self) -> None:
        if self.closed:
            return
        self.lease.close()
        self.closed = True

    def retry_pending_cleanup(self) -> None:
        self.close()


@dataclass(slots=True)
class _TemporaryEnvironmentOwner:
    context: object
    entered_path: Path
    role: str = "attribute_environment"
    closed: bool = False

    def close(self) -> None:
        if self.closed:
            return
        try:
            self.context.__exit__(None, None, None)
        except BaseException:
            if not self.entered_path.exists():
                self.closed = True
                return
            raise
        self.closed = True

    def retry_pending_cleanup(self) -> None:
        self.close()


@dataclass(frozen=True, slots=True)
class _GovernanceDestinationSet:
    paths: tuple[Path, ...]
    canonical_keys: tuple[str, ...]

    @staticmethod
    def normalize(path: Path) -> tuple[str, Path]:
        if not isinstance(path, Path) or not path.is_absolute():
            raise InventoryError("governance destination must be absolute")
        # Construct through the supplied path's own class: bare Path()
        # dispatches on os.name at call time, and CPython <= 3.11 refuses to
        # instantiate the foreign flavor under a simulated platform.
        lexical = type(path)(os.path.abspath(path))
        key = os.path.normcase(str(lexical))
        return key, lexical

    @classmethod
    def build(cls, paths: Iterable[Path]) -> _GovernanceDestinationSet:
        rows: list[tuple[str, Path]] = []
        for supplied in paths:
            key, lexical = cls.normalize(supplied)
            rows.append((key, lexical))
        keys = [key for key, _ in rows]
        if len(set(keys)) != len(keys):
            raise InventoryError("duplicate governance destination alias")
        rows.sort(key=lambda row: row[0])
        return cls(
            tuple(path for _, path in rows),
            tuple(key for key, _ in rows),
        )

    def require_member(self, path: Path) -> Path:
        key, lexical = self.normalize(path)
        try:
            index = self.canonical_keys.index(key)
        except ValueError as error:
            raise InventoryError(
                "write target is outside the declared destination set"
            ) from error
        return self.paths[index]


def _reject_native_destination_aliases(paths: Sequence[Path]) -> None:
    for index, first in enumerate(paths):
        for second in paths[index + 1:]:
            try:
                aliased = os.path.samefile(first, second)
            except FileNotFoundError:
                continue
            except OSError as error:
                raise InventoryError(
                    "native destination alias could not be inspected"
                ) from error
            if aliased:
                raise InventoryError(
                    "native hardlink destination alias is forbidden"
                )


@dataclass(slots=True)
class _GovernanceLockSetLease:
    destination_set: _GovernanceDestinationSet
    owners: list[object]
    canonical_keys: tuple[str, ...]
    closed: bool = False
    posix_parents: dict[str, _PosixParentDirectoryOwner] | None = None

    @classmethod
    def acquire(
        cls,
        destination_set: _GovernanceDestinationSet,
        reservation: _GovernanceCleanupReservation,
    ) -> _GovernanceLockSetLease:
        manager = _governance_cleanup_manager()
        owners: list[object] = []
        lease = cls(
            destination_set,
            owners,
            destination_set.canonical_keys,
            posix_parents={},
        )
        try:
            for path, destination_key in zip(
                destination_set.paths,
                destination_set.canonical_keys,
                strict=True,
            ):
                if os.name == "nt":
                    directory_owner = _WindowsHandleOwner("directory")
                    directory_owner.close_action = (
                        lambda owner=directory_owner: (
                            secure_filesystem._windows_close_directory(owner.handle)
                        )
                    )
                    directory_owner.is_open_action = (
                        lambda owner=directory_owner: (
                            owner.handle is not None
                            and _windows_governance_handle_is_open(owner.handle)
                        )
                    )
                    directory_owner.ambiguous_is_open_action = (
                        lambda handle: _windows_governance_handle_is_open(handle)
                    )
                    directory_owner.identity_action = (
                        lambda handle, parent=path.parent: (
                            secure_filesystem._windows_directory_handle_identity(
                                handle,
                                parent,
                            )
                        )
                    )
                    owners.append(directory_owner)
                    directory, _ = _windows_open_governance_directory(
                        path.parent,
                        owner=directory_owner,
                    )
                    if directory_owner.handle is None:
                        directory_owner.adopt(directory)
                    lock_name = f".{path.name}.pontius-governance.lock"
                    lock_owner = _WindowsDeterministicLockOwner(lock_name)
                    lock_owner.artifact_path = path.with_name(lock_name)
                    lock_owner.destination_key = destination_key
                    owners.append(lock_owner)
                    lock_handle = _windows_create_relative_governance_file(
                        directory,
                        lock_name,
                        owner=lock_owner,
                        share_delete=False,
                    )
                    if lock_owner.handle is None:
                        lock_owner.handle = lock_handle
                        lock_owner.state = "open"
                    lock_owner.acquired = True
                    lock_owner.arm_disposal()
                else:
                    if lease.posix_parents is None:
                        raise InventoryError("POSIX lock parent registry is absent")
                    parent_key = str(path.parent)
                    parent = lease.posix_parents.get(parent_key)
                    if parent is None:
                        chain = _governance_directory_chain(path.parent)
                        directory_flags = (
                            os.O_RDONLY
                            | getattr(os, "O_DIRECTORY", 0)
                            | getattr(os, "O_NOFOLLOW", 0)
                            | getattr(os, "O_CLOEXEC", 0)
                        )
                        provisional = _PosixDescriptorOwner(
                            "lock_parent_directory",
                        )
                        owners.append(provisional)
                        parent_descriptor = os.open(path.parent, directory_flags)
                        provisional.adopt(parent_descriptor)
                        parent_info = os.fstat(parent_descriptor)
                        if (
                            not stat.S_ISDIR(parent_info.st_mode)
                            or secure_filesystem._directory_identity(parent_info)
                            != chain[-1][1]
                        ):
                            raise InventoryError(
                                "bound governance directory identity differs"
                            )
                        parent = _PosixParentDirectoryOwner(
                            path.parent,
                            tuple(chain),
                            parent_descriptor,
                            tuple(chain[-1][1]),
                            [],
                            provisional,
                        )
                        provisional.expected_identity = (
                            _posix_descriptor_identity(parent_descriptor)
                        )
                        parent.descriptor_identity = provisional.expected_identity
                        lease.posix_parents[parent_key] = parent
                        owners[-1] = parent
                    lock_name = f".{path.name}.pontius-governance.lock"
                    lock_path = path.with_name(lock_name)
                    lock_owner = _PosixDeterministicLockOwner()
                    parent.dependents.append(lock_owner)
                    owners.append(lock_owner)
                    descriptor = os.open(
                        lock_name,
                        os.O_WRONLY | os.O_CREAT | os.O_EXCL
                        | getattr(os, "O_NOFOLLOW", 0)
                        | getattr(os, "O_CLOEXEC", 0),
                        0o600,
                        dir_fd=parent.descriptor,
                    )
                    lock_owner.adopt(
                        descriptor,
                        lock_path,
                        destination_key,
                        parent.descriptor,
                        lock_name,
                    )
                    lock_owner.descriptor_identity = (
                        _posix_descriptor_identity(descriptor)
                    )
            _reject_native_destination_aliases(destination_set.paths)
        except BaseException as error:
            primary = error
            if not (
                isinstance(error, InventoryError)
                and "alias" in str(error)
            ):
                primary = InventoryError("governance writer lock is busy")
                primary.__cause__ = error
            group = _GovernanceWriteGroup(lease, reservation)
            group.abort_precommit(primary)
            raise AssertionError("unreachable governance lock cleanup")
        return lease

    def posix_parent_for(self, path: Path) -> _PosixParentDirectoryOwner:
        candidate = self.destination_set.require_member(path)
        if self.posix_parents is None:
            raise InventoryError("POSIX lock parent registry is absent")
        parent = self.posix_parents.get(str(candidate.parent))
        if parent is None:
            raise InventoryError("POSIX lock parent is absent")
        parent.revalidate()
        return parent

    def close(self) -> None:
        if self.closed:
            return
        failures: list[BaseException] = []
        for owner in reversed(self.owners):
            try:
                owner.close()
            except BaseException as error:
                failures.append(error)
        if failures:
            raise InventoryError("governance lock release failed") from ExceptionGroup(
                "governance lock release failures",
                tuple(failures),
            )
        self.closed = True

    def outstanding_roles(self) -> tuple[str, ...]:
        return tuple(
            owner.role
            for owner in self.owners
            if not getattr(owner, "closed", False)
        )

    def outstanding_lock_keys(self) -> tuple[str, ...]:
        keyed = tuple(
            str(owner.destination_key)
            for owner in self.owners
            if getattr(owner, "role", None) == "deterministic_lock"
            and getattr(owner, "destination_key", None) is not None
            and getattr(owner, "acquired", True)
            and not getattr(owner, "closed", False)
        )
        acquired = tuple(
            str(owner.destination_key)
            for owner in self.owners
            if getattr(owner, "role", None) == "deterministic_lock"
            and getattr(owner, "destination_key", None) is not None
            and getattr(owner, "acquired", True)
        )
        has_keyed_owners = bool(acquired)
        if has_keyed_owners:
            return tuple(sorted(set(keyed)))
        return ()

    def released_lock_keys(self) -> tuple[str, ...]:
        outstanding = set(self.outstanding_lock_keys())
        acquired = {
            str(owner.destination_key)
            for owner in self.owners
            if getattr(owner, "role", None) == "deterministic_lock"
            and getattr(owner, "destination_key", None) is not None
            and getattr(owner, "acquired", True)
        }
        return tuple(
            key
            for key in self.canonical_keys
            if key in acquired and key not in outstanding
        )

    def artifact_paths(self) -> tuple[Path, ...]:
        return tuple(
            path
            for owner in self.owners
            if getattr(owner, "role", None) == "deterministic_lock"
            and getattr(owner, "acquired", True)
            and not getattr(owner, "closed", False)
            for path in (
                getattr(owner, "artifact_path", getattr(owner, "path", None)),
            )
            if isinstance(path, Path)
        )


class _GovernanceWriteGroup:
    def __init__(
        self,
        lock_set: object,
        reservation: _GovernanceCleanupReservation,
    ) -> None:
        self.lock_set = lock_set
        self.reservation = reservation
        self.participants: list[object] = []
        self.resources: list[object] = []
        self.decision = "precommit"
        self._retry_id: int | None = None

    def add_participant(self, participant: object) -> None:
        self.participants.append(participant)

    def require_destination(self, path: Path) -> Path:
        destination_set = getattr(self.lock_set, "destination_set", None)
        if not isinstance(destination_set, _GovernanceDestinationSet):
            raise InventoryError("governance group destination set is absent")
        return destination_set.require_member(path)

    def attach_resource(self, resource: object) -> None:
        self.resources.append(resource)

    def prepare_all(self) -> None:
        for participant in self.participants:
            participant.prepare()

    def publish_all(self) -> None:
        for participant in self.participants:
            participant.publish()

    def validate_all(self, lifetime_check: Any | None) -> None:
        if lifetime_check is not None:
            lifetime_check()
        for participant in self.participants:
            participant.validate()
        if lifetime_check is not None:
            lifetime_check()

    def mark_committed(self) -> None:
        if self.decision != "precommit":
            raise InventoryError("governance write group decision is already final")
        self.decision = "committed"

    def _destination_rows(self) -> tuple[tuple[str, bytes], ...]:
        rows: list[tuple[str, bytes]] = []
        for participant in self.participants:
            path = getattr(participant, "path", None)
            raw = getattr(participant, "raw", None)
            if isinstance(path, Path) and type(raw) is bytes:
                rows.append((str(path), raw))
        return tuple(rows)

    def _outstanding_roles(self) -> tuple[str, ...]:
        roles: list[str] = []
        for participant in self.participants:
            if not getattr(participant, "cleaned", False):
                if hasattr(participant, "outstanding_roles"):
                    roles.extend(participant.outstanding_roles())
                else:
                    roles.append("participant")
        for resource in self.resources:
            if not getattr(resource, "closed", False):
                roles.append(str(getattr(resource, "role", "resource")))
        if not getattr(self.lock_set, "closed", False):
            if hasattr(self.lock_set, "outstanding_roles"):
                lock_roles = self.lock_set.outstanding_roles()
                if isinstance(lock_roles, (tuple, list)):
                    roles.extend(str(role) for role in lock_roles)
                else:
                    roles.append("deterministic_lock")
            else:
                roles.append("deterministic_lock")
        return tuple(sorted(set(roles)))

    def pending_descriptor(
        self,
        retry_id: int,
        attempts: int,
    ) -> _GovernancePendingDescriptor:
        rows = self._destination_rows()
        destination_set = getattr(self.lock_set, "destination_set", None)
        destination_paths = getattr(destination_set, "paths", ())
        if not isinstance(destination_paths, (tuple, list)):
            destination_paths = ()
        fallback_paths = tuple(
            str(path)
            for path in destination_paths
        )
        lock_keys = (
            self.lock_set.outstanding_lock_keys()
            if hasattr(self.lock_set, "outstanding_lock_keys")
            else tuple(getattr(self.lock_set, "canonical_keys", ()))
        )
        released_lock_keys = (
            self.lock_set.released_lock_keys()
            if hasattr(self.lock_set, "released_lock_keys")
            else ()
        )
        artifact_paths = [
            str(path)
            for participant in self.participants
            for path in (
                participant.artifact_paths()
                if hasattr(participant, "artifact_paths")
                else (getattr(participant, "recovery_path", None),)
            )
            if isinstance(path, Path)
        ]
        if hasattr(self.lock_set, "artifact_paths"):
            artifact_paths.extend(
                str(path) for path in self.lock_set.artifact_paths()
            )
        return _GovernancePendingDescriptor(
            retry_id,
            attempts,
            self.decision,
            tuple(path for path, _ in rows) or fallback_paths,
            {path: sha256(raw).hexdigest() for path, raw in rows},
            self._outstanding_roles(),
            tuple(sorted(set(artifact_paths))),
            tuple(lock_keys),
            tuple(released_lock_keys),
        )

    def _cleanup_committed_once(self) -> None:
        failures: list[BaseException] = []
        for participant in self.participants:
            if getattr(participant, "cleaned", False):
                continue
            try:
                participant.cleanup_committed_step()
            except BaseException as error:
                failures.append(error)
            else:
                try:
                    participant.cleaned = True
                except BaseException:
                    pass
        if failures:
            raise InventoryError("governance committed cleanup failed") from (
                ExceptionGroup("governance cleanup failures", tuple(failures))
            )
        for resource in self.resources:
            if getattr(resource, "closed", False):
                continue
            try:
                resource.close()
            except BaseException as error:
                failures.append(error)
        if failures:
            raise InventoryError("governance committed cleanup failed") from (
                ExceptionGroup("governance cleanup failures", tuple(failures))
            )
        self.lock_set.close()

    def _rollback_once(self) -> None:
        failures: list[BaseException] = []
        for participant in reversed(self.participants):
            if getattr(participant, "cleaned", False):
                continue
            try:
                participant.rollback_step()
            except BaseException as error:
                failures.append(error)
            else:
                try:
                    participant.cleaned = True
                except BaseException:
                    pass
        if failures:
            raise InventoryError("governance rollback cleanup failed") from (
                ExceptionGroup("governance rollback failures", tuple(failures))
            )
        for resource in self.resources:
            if getattr(resource, "closed", False):
                continue
            try:
                resource.close()
            except BaseException as error:
                failures.append(error)
        if not failures:
            try:
                self.lock_set.close()
            except BaseException as error:
                failures.append(error)
        if failures:
            raise InventoryError("governance rollback cleanup failed") from (
                ExceptionGroup("governance rollback failures", tuple(failures))
            )
        self.decision = "rolled_back"

    def _try_three(self, action: Any) -> BaseException | None:
        failure: BaseException | None = None
        for _ in range(GOVERNANCE_CLEANUP_SYNCHRONOUS_RETRIES):
            try:
                action()
            except BaseException as error:
                failure = error
                continue
            return None
        return failure

    def finish_committed_cleanup(self) -> None:
        if self.decision != "committed":
            raise InventoryError("governance write group is not committed")
        failure = self._try_three(self._cleanup_committed_once)
        if failure is None:
            _governance_cleanup_manager().release(self.reservation)
            return
        self._retry_id = _governance_cleanup_manager().transfer(
            self.reservation,
            self,
        )
        descriptor = self.pending_descriptor(self._retry_id, 0)
        raise GovernanceCommittedWithCleanupFailure(descriptor) from failure

    def abort_precommit(self, primary: BaseException) -> None:
        if self.decision != "precommit":
            raise InventoryError("committed governance group cannot roll back")
        self.decision = "rollback_required"
        failure = self._try_three(self._rollback_once)
        if failure is None:
            _governance_cleanup_manager().release(self.reservation)
            raise primary
        self._retry_id = _governance_cleanup_manager().transfer(
            self.reservation,
            self,
        )
        descriptor = self.pending_descriptor(self._retry_id, 0)
        raise GovernanceCleanupPendingError(descriptor) from ExceptionGroup(
            "governance precommit and rollback failures",
            (primary, failure),
        )

    def retry_pending_cleanup(self) -> None:
        if self.decision == "committed":
            self._cleanup_committed_once()
            return
        if self.decision == "rollback_required":
            self._rollback_once()
            return
        raise InventoryError("governance cleanup decision is invalid")


@dataclass(slots=True)
class _GovernanceTransactionParticipant:
    transaction: object
    path: Path
    raw: bytes
    cleaned: bool = False

    def prepare(self) -> None:
        return None

    def publish(self) -> None:
        return None

    def validate(self) -> None:
        self.transaction.revalidate()

    def rollback_step(self) -> None:
        self.transaction.rollback()
        self.cleaned = True

    def cleanup_committed_step(self) -> None:
        self.transaction.finalize_committed()

    def outstanding_roles(self) -> tuple[str, ...]:
        if hasattr(self.transaction, "outstanding_roles"):
            return tuple(self.transaction.outstanding_roles())
        return ("participant",)

    def artifact_paths(self) -> tuple[Path, ...]:
        if hasattr(self.transaction, "artifact_paths"):
            return tuple(self.transaction.artifact_paths())
        return ()


@dataclass(slots=True)
class _GovernanceFailedParticipant:
    path: Path
    raw: bytes
    rollback_action: Any
    outstanding_roles_action: Any = lambda: ("participant",)
    artifact_paths_action: Any = lambda: ()
    cleaned: bool = False

    def prepare(self) -> None:
        return None

    def publish(self) -> None:
        return None

    def validate(self) -> None:
        raise InventoryError("failed governance participant cannot validate")

    def rollback_step(self) -> None:
        self.rollback_action()
        self.cleaned = True

    def cleanup_committed_step(self) -> None:
        raise InventoryError("failed governance participant cannot commit")

    def outstanding_roles(self) -> tuple[str, ...]:
        return tuple(self.outstanding_roles_action())

    def artifact_paths(self) -> tuple[Path, ...]:
        return tuple(self.artifact_paths_action())


class _GovernancePreparationFailure(InventoryError):
    def __init__(
        self,
        primary: BaseException,
        participant: _GovernanceFailedParticipant,
    ) -> None:
        super().__init__("governance preparation failed")
        self.primary = primary
        self.participant = participant


@dataclass(slots=True)
class _GovernanceWriteOutcome:
    published: bool = False
    snapshot: object | None = None
    recovery_path: Path | None = None


@dataclass(slots=True)
class _GovernancePublishState:
    recovery_name: str | None = None
    staging_name: str | None = None
    staging_path: Path | None = None
    destination_handle: int | None = None
    displaced: bool = False
    published: bool = False
    recovery_deletion_armed: bool = False
    posix_exchange: bool = False
    published_handle: int | None = None
    destination_descriptor_identity: tuple[int, ...] | None = None
    parent_sync_pending: bool = False
    published_disposition_armed: bool = False
    destination_owner: object | None = None
    published_owner: object | None = None
    original_owner: object | None = None


@dataclass(slots=True)
class _WindowsGovernanceFileOwner:
    role: str
    name: str
    artifact_path: Path
    handle: int | None = None
    renamed: bool = False
    state: str = "unacquired"
    acquired: bool = False
    namespace_owned: bool = False
    disposition_armed: bool = False
    ambiguous_handle: int | None = None
    expected_identity: tuple[int, int] | None = None
    closed: bool = False

    def adopt(self, handle: int) -> None:
        if (
            self.handle is not None
            or self.ambiguous_handle is not None
            or self.state == "close_outcome_unknown"
            or self.closed
        ):
            raise InventoryError(f"{self.role} handle slot is already resolved")
        self.handle = handle
        self.acquired = True
        self.state = "open"

    def bind_identity(self, identity: tuple[int, int]) -> None:
        self.expected_identity = tuple(identity)

    def _resolve_ambiguous_close(self, label: str) -> None:
        handle = self.ambiguous_handle
        if handle is None:
            return
        try:
            is_open = _windows_governance_handle_is_open(handle)
        except BaseException as error:
            raise InventoryError(f"{label} close outcome is unresolved") from error
        if is_open:
            if self.disposition_armed and self.namespace_owned:
                try:
                    artifact_absent = (
                        _governance_destination_identity(self.artifact_path) is None
                    )
                except BaseException as error:
                    raise InventoryError(
                        f"{label} close outcome is unresolved"
                    ) from error
                if not artifact_absent:
                    raise InventoryError(f"{label} close outcome is unresolved")
            elif self.expected_identity is not None:
                try:
                    current_identity = _windows_governance_handle_file_id(handle)
                except BaseException as error:
                    raise InventoryError(
                        f"{label} close outcome is unresolved"
                    ) from error
                if current_identity == self.expected_identity:
                    raise InventoryError(f"{label} close outcome is unresolved")
            else:
                raise InventoryError(f"{label} close outcome is unresolved")
        self.ambiguous_handle = None
        self.closed = True
        self.state = "closed"
        if self.disposition_armed:
            self.namespace_owned = False

    def close(self, label: str) -> None:
        if self.closed:
            return
        if self.ambiguous_handle is not None:
            self._resolve_ambiguous_close(label)
            return
        if self.handle is None:
            self.closed = True
            self.state = "closed"
            return
        handle = self.handle
        if self.expected_identity is None:
            try:
                self.bind_identity(_windows_governance_handle_file_id(handle))
            except BaseException as identity_error:
                raise InventoryError(
                    f"{label} identity is unresolved before close"
                ) from identity_error
        try:
            succeeded = _windows_try_close_file(handle)
        except BaseException as close_error:
            self.handle = None
            self.ambiguous_handle = handle
            self.state = "close_outcome_unknown"
            raise InventoryError(f"{label} close outcome is unknown") from close_error
        if not succeeded:
            raise InventoryError(f"{label} close was refused")
        self.handle = None
        self.closed = True
        self.state = "closed"
        if self.disposition_armed:
            self.namespace_owned = False


@dataclass(slots=True)
class _GovernanceWriteTransaction:
    """Own one published file and its recovery until validation commits it."""

    path: Path
    snapshot: object
    original_identity: tuple[int, ...] | None
    original_raw: bytes | None
    outcome: _GovernanceWriteOutcome
    _revalidate_action: Any
    _rollback_action: Any
    _finalize_action: Any
    _outstanding_roles_action: Any = lambda: ()
    _artifact_paths_action: Any = lambda: ()
    _state: str = "open"
    _validated: bool = False

    def revalidate(self) -> None:
        if self._state != "open":
            raise InventoryError("governance transaction is no longer open")
        self._revalidate_action()
        self._validated = True

    def rollback(self) -> None:
        if self._state == "rolled_back":
            return
        if self._state == "finalized":
            raise InventoryError("committed governance transaction cannot roll back")
        if self._state != "open":
            raise InventoryError("governance transaction state is invalid")
        self._rollback_action()
        self._state = "rolled_back"

    def finalize_committed(self) -> None:
        if self._state != "open":
            raise InventoryError("governance transaction is no longer open")
        if not self._validated:
            self.revalidate()
        self._finalize_action()
        self._state = "finalized"

    def outstanding_roles(self) -> tuple[str, ...]:
        return tuple(self._outstanding_roles_action())

    def artifact_paths(self) -> tuple[Path, ...]:
        return tuple(self._artifact_paths_action())


@dataclass(slots=True)
class _GovernancePairTransaction:
    transactions: tuple[_GovernanceWriteTransaction, ...]
    _lifetime_check: Any | None = None
    _validated: bool = False

    def revalidate(self) -> None:
        if self._lifetime_check is not None:
            self._lifetime_check()
        for transaction in self.transactions:
            transaction.revalidate()
        if self._lifetime_check is not None:
            self._lifetime_check()
        self._validated = True


_GOVERNANCE_TRANSACTION_CONTEXT = threading.local()


def _governance_transaction_collector() -> list[object] | None:
    return getattr(_GOVERNANCE_TRANSACTION_CONTEXT, "collector", None)


def _governance_active_group() -> _GovernanceWriteGroup | None:
    return getattr(_GOVERNANCE_TRANSACTION_CONTEXT, "group", None)


def _windows_open_relative_governance_file_raw(
    directory_handle: int,
    name: str,
    *,
    read_data: bool = False,
    share_write: bool = True,
    delete_access: bool = True,
    owner: _WindowsGovernanceFileOwner | None = None,
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
            0x00000080
            | (0x00010000 if delete_access else 0)
            | 0x00100000
            | (0x00000001 if read_data else 0),
            secure_filesystem.ctypes.byref(attributes),
            secure_filesystem.ctypes.byref(status_block),
            None,
            0x80,
            0x00000001
            | (0x00000002 if share_write else 0)
            | 0x00000004,
            1,
            0x20 | 0x40 | 0x00200000,
            None,
            0,
        )
    )
    invalid = secure_filesystem.ctypes.c_void_p(-1).value
    numeric = (
        int(handle.value)
        if handle.value and int(handle.value) != invalid
        else None
    )
    if numeric is not None and owner is not None:
        owner.adopt(numeric)
    if (
        status != 0
        or int(status_block.Status) != 0
        or numeric is None
    ):
        raise InventoryError("governance destination lock could not be acquired")
    if owner is not None:
        owner.bind_identity(_windows_governance_handle_file_id(numeric))
    return numeric


def _windows_open_relative_governance_file(
    directory_handle: int,
    name: str,
    *,
    owner: _WindowsGovernanceFileOwner | None = None,
) -> int:
    return _windows_open_relative_governance_file_raw(
        directory_handle,
        name,
        share_write=False,
        owner=owner,
    )


def _windows_read_relative_governance_file(
    directory_handle: int,
    name: str,
    *,
    owner: _WindowsGovernanceFileOwner | None = None,
) -> tuple[tuple[int, int], bytes]:
    if owner is None:
        owner = _WindowsGovernanceFileOwner("readback", name, Path(name))
    handle = _windows_open_relative_governance_file_raw(
        directory_handle,
        name,
        read_data=True,
        owner=owner,
    )
    primary_failure: BaseException | None = None
    result: tuple[tuple[int, int], bytes] | None = None
    try:
        kernel32 = secure_filesystem.ctypes.WinDLL(
            "kernel32",
            use_last_error=True,
        )
        read = kernel32.ReadFile
        read.argtypes = (
            secure_filesystem.wintypes.HANDLE,
            secure_filesystem.wintypes.LPVOID,
            secure_filesystem.wintypes.DWORD,
            secure_filesystem.wintypes.LPDWORD,
            secure_filesystem.wintypes.LPVOID,
        )
        read.restype = secure_filesystem.wintypes.BOOL
        chunks: list[bytes] = []
        length = 0
        while length <= MAXIMUM_SOURCE_BYTES:
            request = min(1024 * 1024, MAXIMUM_SOURCE_BYTES + 1 - length)
            buffer = secure_filesystem.ctypes.create_string_buffer(request)
            count = secure_filesystem.wintypes.DWORD()
            succeeded = read(
                secure_filesystem.wintypes.HANDLE(handle),
                secure_filesystem.ctypes.byref(buffer),
                request,
                secure_filesystem.ctypes.byref(count),
                None,
            )
            if not succeeded:
                code = secure_filesystem.ctypes.get_last_error()
                raise InventoryError("governance readback failed") from OSError(
                    code,
                    os.strerror(code),
                )
            size = int(count.value)
            if size == 0:
                break
            chunks.append(buffer.raw[:size])
            length += size
        raw = b"".join(chunks)
        if len(raw) > MAXIMUM_SOURCE_BYTES:
            raise InventoryError("governance readback exceeds the bound")
        identity = _windows_governance_handle_file_id(handle)
        owner.bind_identity(identity)
        result = (identity, raw)
    except BaseException as error:
        primary_failure = error
    try:
        owner.close("governance readback")
    except BaseException as close_failure:
        if primary_failure is not None:
            raise InventoryError(
                "governance readback and close both failed"
            ) from ExceptionGroup(
                "governance readback failures",
                (primary_failure, close_failure),
            )
        raise
    if primary_failure is not None:
        raise primary_failure
    if result is None:
        raise InventoryError("governance readback result is absent")
    return result


def _windows_open_governance_directory(
    path: Path,
    *,
    owner: _WindowsHandleOwner | None = None,
) -> tuple[int, tuple[int, bytes]]:
    """Bind a publication directory for handle-relative operations."""

    create, _, _, close = secure_filesystem._windows_directory_api()
    if owner is not None:
        owner.close_action = lambda owner=owner: close(
            secure_filesystem.wintypes.HANDLE(owner.handle)
        )
        if owner.is_open_action is None:
            owner.is_open_action = lambda owner=owner: (
                owner.handle is not None
                and _windows_governance_handle_is_open(owner.handle)
            )
        if owner.ambiguous_is_open_action is None:
            owner.ambiguous_is_open_action = (
                lambda handle: _windows_governance_handle_is_open(handle)
            )
        if owner.identity_action is None:
            owner.identity_action = lambda handle: (
                secure_filesystem._windows_directory_handle_identity(
                    handle,
                    path,
                )
            )
    handle: int | None = None
    try:
        opened = create(
            str(path),
            0x00000020 | 0x00000080 | 0x00100000,
            0x00000001 | 0x00000002 | 0x00000004,
            None,
            3,
            0x02000000 | 0x00200000,
            None,
        )
        invalid = secure_filesystem.ctypes.c_void_p(-1).value
        if not opened or int(opened) == invalid:
            code = secure_filesystem.ctypes.get_last_error()
            raise InventoryError(
                "governance directory lock could not be acquired"
            ) from OSError(code, os.strerror(code), str(path))
        handle = int(opened)
        if owner is not None:
            owner.adopt(handle)
        identity = secure_filesystem._windows_directory_handle_identity(
            handle,
            path,
        )
        if owner is not None:
            owner.bind_identity(identity)
        return handle, identity
    except BaseException as primary_failure:
        if owner is not None:
            raise
        if handle is not None:
            try:
                succeeded = close(secure_filesystem.wintypes.HANDLE(handle))
                if not succeeded:
                    code = secure_filesystem.ctypes.get_last_error()
                    raise OSError(code, os.strerror(code))
            except BaseException as cleanup_failure:
                raise InventoryError(
                    "governance directory acquisition and cleanup both failed"
                ) from ExceptionGroup(
                    "governance directory acquisition failures",
                    (primary_failure, cleanup_failure),
                )
        raise


def _windows_governance_handle_file_id(handle: int) -> tuple[int, int]:
    _, _, information, _ = secure_filesystem._windows_directory_api()
    identity = secure_filesystem._WindowsFileIdInformation()
    succeeded = information(
        secure_filesystem.wintypes.HANDLE(handle),
        18,
        secure_filesystem.ctypes.byref(identity),
        secure_filesystem.ctypes.sizeof(identity),
    )
    if not succeeded:
        code = secure_filesystem.ctypes.get_last_error()
        raise InventoryError("governance recovery identity is unavailable") from OSError(
            code,
            os.strerror(code),
        )
    return (
        int(identity.VolumeSerialNumber),
        int.from_bytes(bytes(identity.FileId.ByteIdentifier), "little"),
    )


def _windows_governance_handle_is_open(handle: int) -> bool:
    kernel32 = secure_filesystem.ctypes.WinDLL(
        "kernel32",
        use_last_error=True,
    )
    get_information = kernel32.GetHandleInformation
    get_information.argtypes = (
        secure_filesystem.wintypes.HANDLE,
        secure_filesystem.wintypes.LPDWORD,
    )
    get_information.restype = secure_filesystem.wintypes.BOOL
    flags = secure_filesystem.wintypes.DWORD()
    if get_information(
        secure_filesystem.wintypes.HANDLE(handle),
        secure_filesystem.ctypes.byref(flags),
    ):
        return True
    code = secure_filesystem.ctypes.get_last_error()
    if code == 6:
        return False
    raise InventoryError("governance handle state is unavailable") from OSError(
        code,
        os.strerror(code),
    )


def _windows_try_close_file(handle: int) -> bool:
    """Close one owned handle, preserving an explicit not-consumed result."""

    _, _, _, _, close = secure_filesystem._windows_file_api()
    return bool(close(secure_filesystem.wintypes.HANDLE(handle)))


def _windows_rename_governance_file(
    handle: int,
    directory_handle: int,
    destination_name: str,
    *,
    replace: bool = False,
) -> None:
    destination_name = secure_filesystem._validated_relative_name(
        destination_name
    )
    _, set_information, _, _, _ = secure_filesystem._windows_file_api()
    encoded = destination_name.encode("utf-16-le")
    structure = secure_filesystem._WindowsFileRenameInformation
    information_class = 10
    name_offset = structure.FileName.offset
    buffer = secure_filesystem.ctypes.create_string_buffer(
        name_offset + len(encoded)
    )
    information = secure_filesystem.ctypes.cast(
        buffer,
        secure_filesystem.ctypes.POINTER(structure),
    ).contents
    information.ReplaceIfExists = 1 if replace else 0
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
            information_class,
        )
    )
    if status != 0 or int(status_block.Status) != 0:
        raise InventoryError(
            "governance rename was refused: "
            f"0x{status & 0xFFFFFFFF:08x}/"
            f"0x{int(status_block.Status) & 0xFFFFFFFF:08x}"
        )


def _windows_replace_governance_file(
    destination_path: Path,
    temporary_path: Path,
    recovery_path: Path,
) -> None:
    try:
        kernel32 = secure_filesystem.ctypes.WinDLL(
            "kernel32",
            use_last_error=True,
        )
        replace_file = kernel32.ReplaceFileW
        replace_file.argtypes = (
            secure_filesystem.wintypes.LPCWSTR,
            secure_filesystem.wintypes.LPCWSTR,
            secure_filesystem.wintypes.LPCWSTR,
            secure_filesystem.wintypes.DWORD,
            secure_filesystem.wintypes.LPVOID,
            secure_filesystem.wintypes.LPVOID,
        )
        replace_file.restype = secure_filesystem.wintypes.BOOL
        succeeded = replace_file(
            str(destination_path),
            str(temporary_path),
            str(recovery_path),
            0x00000001,
            None,
            None,
        )
    except Exception as error:
        raise InventoryError("governance atomic replacement failed") from error
    if not succeeded:
        code = secure_filesystem.ctypes.get_last_error()
        raise InventoryError("governance atomic replacement failed") from OSError(
            code,
            os.strerror(code),
            str(destination_path),
        )


def _windows_create_relative_governance_file(
    directory_handle: int,
    name: str,
    *,
    owner: object,
    share_delete: bool = True,
    share_write: bool = False,
) -> int:
    """Create a staged file that permits one later atomic replacement."""

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
            0x00000002 | 0x00000080 | 0x00010000 | 0x00100000,
            secure_filesystem.ctypes.byref(attributes),
            secure_filesystem.ctypes.byref(status_block),
            None,
            0x80,
            0x00000001
            | (0x00000002 if share_write else 0)
            | (0x00000004 if share_delete else 0),
            2,
            0x20 | 0x40,
            None,
            0,
        )
    )
    invalid = secure_filesystem.ctypes.c_void_p(-1).value
    if handle.value and int(handle.value) != invalid:
        owner.handle = int(handle.value)
        owner.state = "open"
        if hasattr(owner, "acquired"):
            owner.acquired = True
        if hasattr(owner, "namespace_owned"):
            owner.namespace_owned = True
    if (
        status != 0
        or int(status_block.Status) != 0
        or int(status_block.Information) != 2
        or not handle.value
        or int(handle.value) == invalid
    ):
        label = (
            "writer lock"
            if name.endswith(".pontius-governance.lock")
            else "temporary"
        )
        raise InventoryError(f"governance {label} creation failed")
    if isinstance(owner, _WindowsGovernanceFileOwner):
        owner.bind_identity(
            _windows_governance_handle_file_id(int(handle.value))
        )
    return int(handle.value)


def _windows_link_governance_file(
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
            11,
        )
    )
    if status != 0 or int(status_block.Status) != 0:
        raise InventoryError("governance recovery link could not be created")


def _windows_cancel_relative_disposition(handle: int) -> None:
    _, set_information, _, _, _ = secure_filesystem._windows_file_api()
    information = secure_filesystem._WindowsFileDispositionInformation(0)
    status_block = secure_filesystem._WindowsIOStatusBlock()
    status = int(
        set_information(
            secure_filesystem.wintypes.HANDLE(handle),
            secure_filesystem.ctypes.byref(status_block),
            secure_filesystem.ctypes.byref(information),
            secure_filesystem.ctypes.sizeof(information),
            13,
        )
    )
    if status != 0 or int(status_block.Status) != 0:
        raise InventoryError("governance recovery deletion could not be canceled")


def _windows_dispose_governance_lock(handle: int) -> None:
    _, set_information, _, _, _ = secure_filesystem._windows_file_api()
    information = secure_filesystem._WindowsFileDispositionInformation(1)
    status_block = secure_filesystem._WindowsIOStatusBlock()
    status = int(
        set_information(
            secure_filesystem.wintypes.HANDLE(handle),
            secure_filesystem.ctypes.byref(status_block),
            secure_filesystem.ctypes.byref(information),
            secure_filesystem.ctypes.sizeof(information),
            13,
        )
    )
    if status != 0 or int(status_block.Status) != 0:
        raise InventoryError("governance directory lock disposal failed")


def _posix_exchange_governance_file(
    directory_handle: int,
    first_name: str,
    second_name: str,
) -> bool:
    """Atomically exchange two names when the host exposes renameat2."""

    if not sys.platform.startswith("linux"):
        return False
    library = secure_filesystem.ctypes.CDLL(None, use_errno=True)
    renameat2 = getattr(library, "renameat2", None)
    if renameat2 is None:
        return False
    renameat2.argtypes = (
        secure_filesystem.ctypes.c_int,
        secure_filesystem.ctypes.c_char_p,
        secure_filesystem.ctypes.c_int,
        secure_filesystem.ctypes.c_char_p,
        secure_filesystem.ctypes.c_uint,
    )
    renameat2.restype = secure_filesystem.ctypes.c_int
    result = renameat2(
        directory_handle,
        os.fsencode(first_name),
        directory_handle,
        os.fsencode(second_name),
        0x00000002,
    )
    if result == 0:
        return True
    code = secure_filesystem.ctypes.get_errno()
    if code in {errno.ENOSYS, errno.EINVAL, errno.ENOTSUP}:
        return False
    raise InventoryError("governance atomic exchange failed") from OSError(
        code,
        os.strerror(code),
    )


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


def _governance_destination_file_id(path: Path) -> tuple[int, int]:
    """Independently open one destination and return its full-width identity.

    Stat-derived and handle-derived identities may never be compared: CPython
    <= 3.11 reports 32-bit ``st_dev`` while ``FileIdInfo`` is 64-bit. Checks
    against retained handles therefore compare this fresh path-side
    ``FileIdInfo`` observation, never a stat tuple.
    """

    descriptor = secure_filesystem._open_regular_no_follow(path)
    try:
        return _windows_governance_handle_file_id(
            secure_filesystem.msvcrt.get_osfhandle(descriptor)
        )
    finally:
        os.close(descriptor)


def _publish_staged_governance(
    *,
    temporary_name: str,
    temporary_handle: int,
    destination_name: str,
    parent_handle: int,
    windows: bool,
    destination_path: Path,
    expected_identity: tuple[int, ...] | None,
    expected_raw: bytes | None,
    state: _GovernancePublishState,
    outcome: _GovernanceWriteOutcome,
    expected_file_id: tuple[int, int] | None = None,
) -> None:
    _require_governance_destination_identity(
        destination_path,
        expected_identity,
    )
    if windows and expected_identity is not None and expected_file_id is None:
        raise InventoryError(
            "governance expected destination identity is invalid"
        )
    if windows:
        if expected_identity is not None:
            state.recovery_name = (
                f".{destination_name}.{uuid.uuid4().hex}.recovery"
            )
            outcome.recovery_path = destination_path.with_name(
                state.recovery_name
            )
            original_owner = state.original_owner
            if not isinstance(original_owner, _WindowsGovernanceFileOwner):
                raise InventoryError("governance original owner slot is absent")
            original_handle = _windows_open_relative_governance_file_raw(
                parent_handle,
                destination_name,
                share_write=True,
                owner=original_owner,
            )
            try:
                original_identity = _windows_governance_handle_file_id(
                    original_handle
                )
                original_owner.bind_identity(original_identity)
                if original_identity != expected_file_id:
                    raise InventoryError(
                        "governance destination handle identity differs"
                    )
                _windows_link_governance_file(
                    original_handle,
                    parent_handle,
                    state.recovery_name,
                )
                state.displaced = True
                recovery_owner = state.destination_owner
                if not isinstance(recovery_owner, _WindowsGovernanceFileOwner):
                    raise InventoryError("governance recovery owner slot is absent")
                recovery_owner.name = state.recovery_name
                recovery_owner.artifact_path = outcome.recovery_path
                recovery_owner.namespace_owned = True
                state.destination_handle = _windows_open_relative_governance_file(
                    parent_handle,
                    state.recovery_name,
                    owner=recovery_owner,
                )
                recovery_owner.bind_identity(
                    _windows_governance_handle_file_id(
                        state.destination_handle
                    )
                )
            finally:
                original_owner.close("governance original")
            recovery = secure_filesystem.read_regular_snapshot(
                outcome.recovery_path,
                maximum_bytes=MAXIMUM_SOURCE_BYTES,
                root=destination_path.parent,
            )
            stable_recovery_identity = (
                recovery.identity[:4] + recovery.identity[5:]
            )
            stable_expected_identity = (
                expected_identity[:4] + expected_identity[5:]
            )
            if (
                stable_recovery_identity != stable_expected_identity
                or (
                    expected_raw is not None
                    and recovery.raw != expected_raw
                )
            ):
                raise InventoryError(
                    "governance destination raced into the recovery artifact"
                )
            if _windows_governance_handle_file_id(
                state.destination_handle
            ) != _governance_destination_file_id(outcome.recovery_path):
                raise InventoryError(
                    "governance recovery handle identity differs"
                )
            _windows_rename_governance_file(
                temporary_handle,
                parent_handle,
                destination_name,
                replace=True,
            )
            state.published = True
            outcome.published = True
            return
        _windows_rename_governance_file(
            temporary_handle,
            parent_handle,
            destination_name,
        )
        state.published = True
        outcome.published = True
        return
    before_handle = os.fstat(temporary_handle)
    state.staging_name = temporary_name
    state.staging_path = destination_path.with_name(temporary_name)
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
    if expected_identity is not None:
        state.destination_handle = os.open(
            destination_name,
            os.O_RDONLY
            | os.O_NOFOLLOW
            | getattr(os, "O_NONBLOCK", 0)
            | getattr(os, "O_CLOEXEC", 0),
            dir_fd=parent_handle,
        )
        state.destination_descriptor_identity = _posix_descriptor_identity(
            state.destination_handle
        )
        destination_info = os.fstat(state.destination_handle)
        if secure_filesystem._file_identity(destination_info) != expected_identity:
            raise InventoryError("governance destination changed before displacement")
        if _posix_exchange_governance_file(
            parent_handle,
            temporary_name,
            destination_name,
        ):
            recovery_name = temporary_name
            state.posix_exchange = True
            state.staging_name = None
            state.staging_path = None
        else:
            recovery_name = (
                f".{destination_name}.{uuid.uuid4().hex}.recovery"
            )
            state.recovery_name = recovery_name
            outcome.recovery_path = destination_path.with_name(recovery_name)
            os.link(
                destination_name,
                recovery_name,
                src_dir_fd=parent_handle,
                dst_dir_fd=parent_handle,
                follow_symlinks=False,
            )
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
                    "governance recovery link identity differs"
                )
            os.replace(
                temporary_name,
                destination_name,
                src_dir_fd=parent_handle,
                dst_dir_fd=parent_handle,
            )
            state.staging_name = None
            state.staging_path = None
        state.recovery_name = recovery_name
        outcome.recovery_path = destination_path.with_name(recovery_name)
        state.displaced = True
        state.published = True
        outcome.published = True
        recovery = secure_filesystem.read_regular_snapshot(
            outcome.recovery_path,
            maximum_bytes=MAXIMUM_SOURCE_BYTES,
            root=destination_path.parent,
        )
        stable_recovery_identity = (
            recovery.identity[:4] + recovery.identity[5:]
        )
        stable_expected_identity = (
            expected_identity[:4] + expected_identity[5:]
        )
        if (
            stable_recovery_identity != stable_expected_identity
            or (expected_raw is not None and recovery.raw != expected_raw)
        ):
            raise InventoryError(
                "governance destination raced into the recovery artifact"
            )
        return
    os.link(
        temporary_name,
        destination_name,
        src_dir_fd=parent_handle,
        dst_dir_fd=parent_handle,
        follow_symlinks=False,
    )
    state.published = True
    outcome.published = True
    os.unlink(temporary_name, dir_fd=parent_handle)
    state.staging_name = None
    state.staging_path = None


def _write_posix_governance(
    path: Path,
    raw: bytes,
    chain: Sequence[tuple[Path, tuple[int, ...]]],
    expected_identity: tuple[int, ...] | None,
    expected_raw: bytes | None,
    outcome: _GovernanceWriteOutcome,
    lifetime_check: Any | None,
    post_publish_lifetime_check: Any | None,
    parent_binding: _PosixParentDirectoryOwner | None = None,
    defer_failure: bool = False,
) -> _GovernanceWriteTransaction:
    required = (os.link, os.open, os.replace, os.stat, os.unlink)
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
    directory: int | None = None
    directory_owned = parent_binding is None
    directory_descriptor_identity: tuple[int, ...] | None = None
    directory_close_attempted = False
    temporary_name = f".{path.name}.{uuid.uuid4().hex}.tmp"
    temporary: int | None = None
    temporary_descriptor_identity: tuple[int, ...] | None = None
    temporary_close_attempted = False
    temporary_path_identity: tuple[int, ...] | None = None
    publish_state = _GovernancePublishState()

    published_snapshot: object | None = None
    destination_close_attempted = False

    def outstanding_roles() -> tuple[str, ...]:
        roles: list[str] = []
        if temporary is not None or publish_state.staging_name is not None:
            roles.append("staging")
        if publish_state.recovery_name is not None:
            roles.append("recovery")
        if publish_state.destination_handle is not None:
            roles.append("published")
        if directory is not None and directory_owned:
            roles.append("directory")
        return tuple(roles)

    def artifact_paths() -> tuple[Path, ...]:
        paths: list[Path] = []
        if publish_state.staging_path is not None:
            paths.append(publish_state.staging_path)
        if outcome.recovery_path is not None:
            paths.append(outcome.recovery_path)
        return tuple(paths)

    def close_resources() -> None:
        nonlocal directory, temporary
        nonlocal directory_close_attempted, temporary_close_attempted
        nonlocal destination_close_attempted
        failures: list[BaseException] = []
        if publish_state.destination_handle is not None:
            destination_handle = publish_state.destination_handle
            publish_state.destination_handle = None
            publish_state.destination_descriptor_identity = None
            if destination_close_attempted:
                pass
            else:
                destination_close_attempted = True
                try:
                    os.close(destination_handle)
                except BaseException as error:
                    failures.append(error)
        if temporary is not None:
            temporary_handle = temporary
            temporary = None
            if temporary_close_attempted:
                pass
            else:
                temporary_close_attempted = True
                try:
                    os.close(temporary_handle)
                except BaseException as error:
                    failures.append(error)
        if (
            directory is not None
            and directory_owned
            and publish_state.staging_name is None
            and publish_state.recovery_name is None
            and not publish_state.parent_sync_pending
        ):
            directory_handle = directory
            directory = None
            if directory_close_attempted:
                pass
            else:
                directory_close_attempted = True
                try:
                    os.close(directory_handle)
                except BaseException as error:
                    failures.append(error)
        if failures:
            raise InventoryError("governance handle cleanup failed") from ExceptionGroup(
                "governance handle cleanup failures",
                tuple(failures),
            )

    def staged_destination_is_current() -> None:
        if directory is None or temporary_path_identity is None:
            raise InventoryError("governance transaction identity is absent")
        current = os.stat(
            path.name,
            dir_fd=directory,
            follow_symlinks=False,
        )
        if (
            secure_filesystem._path_handle_identity(current)
            != temporary_path_identity
        ):
            raise InventoryError(
                "governance rollback refused a concurrent destination"
            )

    def remove_unpublished_names() -> None:
        if directory is None:
            return
        if publish_state.recovery_name is not None and not publish_state.published:
            try:
                os.unlink(publish_state.recovery_name, dir_fd=directory)
            except FileNotFoundError:
                publish_state.recovery_name = None
                outcome.recovery_path = None
            else:
                publish_state.recovery_name = None
                outcome.recovery_path = None
        if publish_state.staging_name is not None and not publish_state.published:
            try:
                path_info = os.stat(
                    publish_state.staging_name,
                    dir_fd=directory,
                    follow_symlinks=False,
                )
                if (
                    temporary_path_identity is None
                    or temporary_path_identity
                    == secure_filesystem._path_handle_identity(path_info)
                ):
                    os.unlink(publish_state.staging_name, dir_fd=directory)
                    publish_state.staging_name = None
                    publish_state.staging_path = None
            except FileNotFoundError:
                publish_state.staging_name = None
                publish_state.staging_path = None

    def revalidate_transaction() -> None:
        if directory is None or published_snapshot is None:
            raise InventoryError("governance transaction is incomplete")
        if parent_binding is not None:
            parent_binding.revalidate()
        else:
            _revalidate_governance_directory_chain(chain)
        parent_info = os.fstat(directory)
        if secure_filesystem._directory_identity(parent_info) != chain[-1][1]:
            raise InventoryError("bound governance directory identity changed")
        staged_destination_is_current()
        published_snapshot.revalidate()
        if post_publish_lifetime_check is not None:
            post_publish_lifetime_check(published_snapshot)

    def rollback_transaction() -> None:
        failures: list[BaseException] = []
        try:
            if publish_state.parent_sync_pending:
                if directory is None:
                    raise InventoryError("governance rollback directory is absent")
                os.fsync(directory)
                publish_state.parent_sync_pending = False
            if publish_state.published:
                if directory is None:
                    raise InventoryError("governance rollback directory is absent")
                staged_destination_is_current()
                if publish_state.displaced:
                    if publish_state.recovery_name is None:
                        raise InventoryError("governance recovery name is absent")
                    if publish_state.posix_exchange:
                        if not _posix_exchange_governance_file(
                            directory,
                            path.name,
                            publish_state.recovery_name,
                        ):
                            raise InventoryError(
                                "governance rollback exchange became unavailable"
                            )
                        publish_state.published = False
                        publish_state.displaced = False
                        publish_state.posix_exchange = False
                        outcome.published = False
                        outcome.snapshot = None
                        publish_state.parent_sync_pending = True
                        os.unlink(publish_state.recovery_name, dir_fd=directory)
                        publish_state.recovery_name = None
                        outcome.recovery_path = None
                    else:
                        os.replace(
                            publish_state.recovery_name,
                            path.name,
                            src_dir_fd=directory,
                            dst_dir_fd=directory,
                        )
                        publish_state.recovery_name = None
                        publish_state.published = False
                        publish_state.displaced = False
                        outcome.published = False
                        outcome.snapshot = None
                        outcome.recovery_path = None
                        publish_state.parent_sync_pending = True
                else:
                    os.unlink(path.name, dir_fd=directory)
                    publish_state.published = False
                    outcome.published = False
                    outcome.snapshot = None
                    publish_state.parent_sync_pending = True
                if publish_state.parent_sync_pending:
                    os.fsync(directory)
                    publish_state.parent_sync_pending = False
            else:
                remove_unpublished_names()
        except BaseException as error:
            failures.append(error)
        try:
            remove_unpublished_names()
        except BaseException as error:
            failures.append(error)
        try:
            close_resources()
        except BaseException as error:
            failures.append(error)
        if failures:
            raise InventoryError("governance rollback failed") from ExceptionGroup(
                "governance rollback failures",
                tuple(failures),
            )

    def finalize_transaction() -> None:
        nonlocal destination_close_attempted
        if directory is None:
            raise InventoryError("governance finalization directory is absent")
        if publish_state.destination_handle is not None:
            destination_handle = publish_state.destination_handle
            publish_state.destination_handle = None
            publish_state.destination_descriptor_identity = None
            if destination_close_attempted:
                pass
            else:
                destination_close_attempted = True
                try:
                    os.close(destination_handle)
                except BaseException as error:
                    raise InventoryError(
                        "governance destination close failed before commit"
                    ) from error
        if publish_state.recovery_name is not None:
            os.unlink(publish_state.recovery_name, dir_fd=directory)
            publish_state.recovery_name = None
            publish_state.displaced = False
            outcome.recovery_path = None
        close_resources()

    try:
        if parent_binding is None:
            directory = os.open(path.parent, directory_flags)
            parent_info = os.fstat(directory)
            if secure_filesystem._directory_identity(parent_info) != chain[-1][1]:
                raise InventoryError("bound governance directory identity differs")
            directory_descriptor_identity = _posix_descriptor_identity(directory)
        else:
            parent_binding.revalidate()
            directory = parent_binding.descriptor
            directory_descriptor_identity = parent_binding.descriptor_identity
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
        publish_state.staging_name = temporary_name
        publish_state.staging_path = path.with_name(temporary_name)
        temporary_descriptor_identity = _posix_descriptor_identity(temporary)
        offset = 0
        while offset < len(raw):
            written = os.write(temporary, raw[offset:])
            if written <= 0:
                raise InventoryError(
                    "governance output write made no progress"
                )
            offset += written
        os.fsync(temporary)
        temporary_path_identity = secure_filesystem._path_handle_identity(
            os.fstat(temporary)
        )
        if parent_binding is not None:
            parent_binding.revalidate()
        else:
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
            expected_raw=expected_raw,
            state=publish_state,
            outcome=outcome,
        )
        publish_state.parent_sync_pending = True
        os.fsync(directory)
        publish_state.parent_sync_pending = False
        snapshot = secure_filesystem.read_regular_snapshot(
            path,
            maximum_bytes=MAXIMUM_SOURCE_BYTES,
            root=path.parent,
        )
        if snapshot.raw != raw:
            raise InventoryError(
                "published governance bytes differ from staging bytes"
            )
        snapshot.revalidate()
        outcome.snapshot = snapshot
        published_snapshot = snapshot
        os.fsync(directory)
    except BaseException as error:
        if defer_failure:
            raise _GovernancePreparationFailure(
                error,
                _GovernanceFailedParticipant(
                    path,
                    raw,
                    rollback_transaction,
                    outstanding_roles,
                    artifact_paths,
                ),
            ) from error
        try:
            rollback_transaction()
        except BaseException as cleanup_error:
            raise InventoryError(
                "governance write and cleanup both failed"
            ) from ExceptionGroup(
                "governance write failures",
                (error, cleanup_error),
            )
        raise
    if published_snapshot is None:
        raise InventoryError("published governance snapshot is absent")

    return _GovernanceWriteTransaction(
        path=path,
        snapshot=published_snapshot,
        original_identity=expected_identity,
        original_raw=expected_raw,
        outcome=outcome,
        _revalidate_action=revalidate_transaction,
        _rollback_action=rollback_transaction,
        _finalize_action=finalize_transaction,
        _outstanding_roles_action=outstanding_roles,
        _artifact_paths_action=artifact_paths,
        _validated=True,
    )


def _write_windows_governance(
    path: Path,
    raw: bytes,
    chain: Sequence[tuple[Path, tuple[int, ...]]],
    expected_identity: tuple[int, ...] | None,
    expected_raw: bytes | None,
    outcome: _GovernanceWriteOutcome,
    lifetime_check: Any | None,
    post_publish_lifetime_check: Any | None,
    defer_failure: bool = False,
) -> _GovernanceWriteTransaction:
    directory: int | None = None
    directory_owner = _WindowsHandleOwner("directory")
    directory_lock: object | None = None
    temporary: _WindowsGovernanceFileOwner | None = None
    staged_snapshot: object | None = None
    staged_file_id: tuple[int, int] | None = None
    published_snapshot: object | None = None
    bound_identity: tuple[int, bytes] | None = None
    publish_state = _GovernancePublishState()
    recovery_owner = _WindowsGovernanceFileOwner("recovery", "", path)
    published_owner = _WindowsGovernanceFileOwner(
        "published",
        path.name,
        path,
    )
    published_disposal_owner = _WindowsGovernanceFileOwner(
        "published",
        path.name,
        path,
    )
    original_owner = _WindowsGovernanceFileOwner(
        "original",
        path.name,
        path,
    )
    readback_owners: list[_WindowsGovernanceFileOwner] = []
    publish_state.destination_owner = recovery_owner
    publish_state.published_owner = published_owner
    publish_state.original_owner = original_owner
    raw_close_attempted: set[tuple[str, int]] = set()

    def outstanding_roles() -> tuple[str, ...]:
        roles: list[str] = []
        if temporary is not None and (
            temporary.handle is not None
            or temporary.namespace_owned
            or temporary.state == "close_outcome_unknown"
        ):
            roles.append("staging")
        if (
            publish_state.published
            or published_owner.handle is not None
            or published_owner.state == "close_outcome_unknown"
            or published_disposal_owner.handle is not None
            or published_disposal_owner.state == "close_outcome_unknown"
        ):
            roles.append("published")
        if (
            recovery_owner.handle is not None
            or recovery_owner.ambiguous_handle is not None
            or recovery_owner.namespace_owned
            or recovery_owner.state == "close_outcome_unknown"
        ):
            roles.append("recovery")
        if original_owner.acquired and not original_owner.closed:
            roles.append("original")
        if any(owner.acquired and not owner.closed for owner in readback_owners):
            roles.append("readback")
        if (
            not directory_owner.closed
            and (
                directory_owner.handle is not None
                or directory_owner.ambiguous_handle is not None
            )
        ):
            roles.append("directory")
        return tuple(roles)

    def artifact_paths() -> tuple[Path, ...]:
        paths: list[Path] = []
        if temporary is not None and temporary.namespace_owned:
            paths.append(path.with_name(temporary.name))
        if recovery_owner.namespace_owned and outcome.recovery_path is not None:
            paths.append(outcome.recovery_path)
        if publish_state.published and not publish_state.displaced:
            paths.append(path)
        return tuple(paths)

    def close_raw_handle(handle: int, label: str) -> None:
        key = (label, handle)
        if key in raw_close_attempted:
            return
        raw_close_attempted.add(key)
        try:
            secure_filesystem._windows_close_file(handle)
        except BaseException as close_error:
            raise InventoryError(
                f"{label} close outcome is unknown"
            ) from close_error

    def close_owner(
        owner: _WindowsGovernanceFileOwner,
        label: str,
    ) -> None:
        owner.close(label)

    def close_published_handle() -> None:
        close_owner(published_owner, "published governance")
        publish_state.published_handle = published_owner.handle

    def retry_cleanup(action: Any) -> None:
        failures: list[BaseException] = []
        for _ in range(2):
            try:
                action()
            except BaseException as error:
                failures.append(error)
                continue
            return
        raise InventoryError("governance cleanup retry failed") from ExceptionGroup(
            "governance cleanup retry failures",
            tuple(failures),
        )

    def close_directory() -> None:
        nonlocal directory
        if directory_owner.closed:
            directory = None
            return
        directory_owner.close()
        if directory_owner.closed:
            directory = None

    def cleanup_auxiliary_handles() -> None:
        failures: list[BaseException] = []
        try:
            close_owner(original_owner, "governance original")
        except BaseException as error:
            failures.append(error)
        for owner in readback_owners:
            try:
                close_owner(owner, "governance readback")
            except BaseException as error:
                failures.append(error)
        if failures:
            raise InventoryError("governance auxiliary cleanup failed") from (
                ExceptionGroup(
                    "governance auxiliary cleanup failures",
                    tuple(failures),
                )
            )

    def acquire_recovery_for_cleanup() -> int | None:
        if recovery_owner.handle is not None:
            publish_state.destination_handle = recovery_owner.handle
            return recovery_owner.handle
        if directory is None or publish_state.recovery_name is None:
            return None
        try:
            handle = _windows_open_relative_governance_file_raw(
                directory,
                publish_state.recovery_name,
                owner=recovery_owner,
            )
        except BaseException:
            return None
        publish_state.destination_handle = handle
        return handle

    def close_recovery_handle() -> None:
        close_owner(recovery_owner, "governance recovery")
        publish_state.destination_handle = recovery_owner.handle

    def current_destination_is_staged() -> None:
        if directory is None:
            raise InventoryError("governance directory handle is absent")
        if staged_snapshot is None or staged_file_id is None:
            raise InventoryError("governance staging identity is absent")
        readback_owner = _WindowsGovernanceFileOwner(
            "readback",
            path.name,
            path,
        )
        readback_owners.append(readback_owner)
        current_identity, current_raw = _windows_read_relative_governance_file(
            directory,
            path.name,
            owner=readback_owner,
        )
        if (
            current_identity != staged_file_id
            or current_raw != raw
        ):
            raise InventoryError(
                "governance rollback refused a concurrent destination"
            )

    def revalidate_transaction() -> None:
        if (
            directory is None
            or bound_identity is None
            or published_snapshot is None
        ):
            raise InventoryError("governance transaction is incomplete")
        _revalidate_governance_directory_chain(chain)
        if (
            secure_filesystem._windows_directory_handle_identity(
                directory,
                path.parent,
            )
            != bound_identity
        ):
            raise InventoryError("bound governance directory identity changed")
        current_destination_is_staged()
        published_snapshot.revalidate()
        if post_publish_lifetime_check is not None:
            post_publish_lifetime_check(published_snapshot)

    def cleanup_unpublished_recovery() -> None:
        if not publish_state.displaced or publish_state.published:
            return
        if recovery_owner.ambiguous_handle is not None:
            close_recovery_handle()
            if (
                recovery_owner.closed
                and recovery_owner.disposition_armed
                and not recovery_owner.namespace_owned
            ):
                publish_state.recovery_deletion_armed = False
                recovery_owner.disposition_armed = False
                publish_state.displaced = False
                publish_state.recovery_name = None
                outcome.recovery_path = None
                return
        handle = acquire_recovery_for_cleanup()
        if handle is None:
            raise InventoryError("governance recovery cleanup handle is absent")
        if not publish_state.recovery_deletion_armed:
            secure_filesystem._windows_dispose_relative_file(handle)
            publish_state.recovery_deletion_armed = True
            recovery_owner.disposition_armed = True
        close_recovery_handle()
        publish_state.recovery_deletion_armed = False
        recovery_owner.disposition_armed = False
        recovery_owner.namespace_owned = False
        publish_state.displaced = False
        publish_state.recovery_name = None
        outcome.recovery_path = None

    def cleanup_temporary() -> None:
        nonlocal temporary
        if temporary is None:
            return
        if not temporary.renamed and not temporary.disposition_armed:
            if temporary.handle is None:
                close_owner(temporary, "governance staging handle")
                temporary = None
                return
            secure_filesystem._windows_dispose_relative_file(
                temporary.handle
            )
            temporary.disposition_armed = True
            temporary.state = "deletion_armed"
        close_owner(temporary, "governance staging handle")
        if temporary.disposition_armed:
            temporary.namespace_owned = False
        temporary = None

    def cleanup_directory_lock() -> None:
        nonlocal directory_lock
        if directory_lock is None:
            return
        directory_lock.close()
        directory_lock = None

    def rollback_transaction() -> None:
        try:
            retry_cleanup(cleanup_auxiliary_handles)
            if publish_state.published:
                if directory is None:
                    raise InventoryError("governance rollback state is incomplete")
                retry_cleanup(close_published_handle)
                retry_cleanup(cleanup_temporary)
                if publish_state.displaced:
                    current_destination_is_staged()
                    recovery_handle = acquire_recovery_for_cleanup()
                    if recovery_handle is None:
                        raise InventoryError("governance recovery handle is absent")
                    if publish_state.recovery_deletion_armed:
                        _windows_cancel_relative_disposition(recovery_handle)
                        publish_state.recovery_deletion_armed = False
                        recovery_owner.disposition_armed = False
                    _windows_rename_governance_file(
                        recovery_handle,
                        directory,
                        path.name,
                        replace=True,
                    )
                    recovery_owner.namespace_owned = False
                else:
                    if publish_state.published_disposition_armed:
                        close_owner(
                            published_disposal_owner,
                            "published governance rollback",
                        )
                        if published_disposal_owner.namespace_owned:
                            if _governance_destination_identity(path) is not None:
                                raise InventoryError(
                                    "published governance disposition remains pending"
                                )
                            published_disposal_owner.namespace_owned = False
                    else:
                        current_destination_is_staged()
                        if published_disposal_owner.handle is None:
                            published_handle = _windows_open_relative_governance_file_raw(
                                directory,
                                path.name,
                                owner=published_disposal_owner,
                            )
                        else:
                            published_handle = published_disposal_owner.handle
                        published_disposal_owner.namespace_owned = True
                        secure_filesystem._windows_dispose_relative_file(
                            published_handle
                        )
                        publish_state.published_disposition_armed = True
                        published_disposal_owner.disposition_armed = True
                        close_owner(
                            published_disposal_owner,
                            "published governance rollback",
                        )
                publish_state.published = False
                publish_state.published_disposition_armed = False
                published_disposal_owner.disposition_armed = False
                published_disposal_owner.namespace_owned = False
                publish_state.displaced = False
                publish_state.recovery_name = None
                outcome.published = False
                outcome.snapshot = None
                outcome.recovery_path = None
            else:
                cleanup_unpublished_recovery()
        except BaseException as error:
            raise InventoryError("governance rollback failed") from error
        failures: list[BaseException] = []
        try:
            retry_cleanup(cleanup_auxiliary_handles)
        except BaseException as error:
            failures.append(error)
        if publish_state.destination_handle is not None:
            try:
                retry_cleanup(close_recovery_handle)
            except BaseException as error:
                failures.append(error)
        try:
            retry_cleanup(close_published_handle)
        except BaseException as error:
            failures.append(error)
        try:
            retry_cleanup(cleanup_temporary)
        except BaseException as error:
            failures.append(error)
        if failures:
            raise InventoryError("governance rollback failed") from ExceptionGroup(
                "governance rollback failures",
                tuple(failures),
            )
        try:
            retry_cleanup(cleanup_directory_lock)
        except BaseException as error:
            raise InventoryError("governance rollback failed") from error
        try:
            close_directory()
        except BaseException as error:
            raise InventoryError("governance rollback failed") from error

    def finalize_transaction() -> None:
        nonlocal directory, temporary
        cleanup_auxiliary_handles()
        if publish_state.destination_handle is not None:
            if directory is None:
                raise InventoryError("governance finalization directory is absent")
            recovery_handle = publish_state.destination_handle
            if not publish_state.recovery_deletion_armed:
                secure_filesystem._windows_dispose_relative_file(
                    recovery_handle
                )
                publish_state.recovery_deletion_armed = True
                recovery_owner.disposition_armed = True
            close_recovery_handle()
            publish_state.recovery_deletion_armed = False
            recovery_owner.disposition_armed = False
            recovery_owner.namespace_owned = False
            publish_state.displaced = False
            publish_state.recovery_name = None
            outcome.recovery_path = None
        close_published_handle()
        cleanup_temporary()
        cleanup_directory_lock()
        close_directory()

    try:
        directory, bound_identity = _windows_open_governance_directory(
            path.parent,
            owner=directory_owner,
        )
        temporary_name = f".{path.name}.{uuid.uuid4().hex}.tmp"
        temporary = _WindowsGovernanceFileOwner(
            "staging",
            temporary_name,
            path.with_name(temporary_name),
        )
        handle = _windows_create_relative_governance_file(
            directory,
            temporary_name,
            owner=temporary,
        )
        secure_filesystem._write_staged_bytes(handle, raw, windows=True)
        temporary_path = path.with_name(temporary_name)
        staged_snapshot = secure_filesystem.read_regular_snapshot(
            temporary_path,
            maximum_bytes=MAXIMUM_SOURCE_BYTES,
            root=path.parent,
        )
        if staged_snapshot.raw != raw:
            raise InventoryError("governance staging bytes differ after write")
        staged_file_id = _windows_governance_handle_file_id(handle)
        temporary.bind_identity(staged_file_id)
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
        expected_file_id = (
            None
            if expected_identity is None
            else _governance_destination_file_id(path)
        )
        _publish_staged_governance(
            temporary_name=temporary_name,
            temporary_handle=handle,
            destination_name=path.name,
            parent_handle=directory,
            windows=True,
            expected_file_id=expected_file_id,
            destination_path=path,
            expected_identity=expected_identity,
            expected_raw=expected_raw,
            state=publish_state,
            outcome=outcome,
        )
        temporary.renamed = True
        temporary.namespace_owned = False
        close_owner(temporary, "governance staging handle")
        publish_state.published_handle = _windows_open_relative_governance_file_raw(
            directory,
            path.name,
            read_data=True,
            share_write=False,
            delete_access=False,
            owner=published_owner,
        )
        published_identity = _windows_governance_handle_file_id(
            publish_state.published_handle
        )
        published_owner.bind_identity(published_identity)
        if published_identity != staged_file_id:
            raise InventoryError(
                "published governance handle identity differs from staging"
            )
        snapshot = secure_filesystem.read_regular_snapshot(
            path,
            maximum_bytes=MAXIMUM_SOURCE_BYTES,
            root=path.parent,
        )
        if snapshot.raw != raw:
            raise InventoryError(
                "published governance bytes differ from staging bytes"
            )
        if staged_snapshot is None or snapshot.identity[:4] != (
            staged_snapshot.identity[:4]
        ):
            raise InventoryError(
                "published governance identity differs from staging identity"
            )
        snapshot.revalidate()
        outcome.snapshot = snapshot
        published_snapshot = snapshot
    except BaseException as error:
        if defer_failure:
            raise _GovernancePreparationFailure(
                error,
                _GovernanceFailedParticipant(
                    path,
                    raw,
                    rollback_transaction,
                    outstanding_roles,
                    artifact_paths,
                ),
            ) from error
        try:
            rollback_transaction()
        except BaseException as cleanup_error:
            raise InventoryError(
                "governance write and cleanup both failed"
            ) from ExceptionGroup(
                "governance write failures",
                (error, cleanup_error),
            )
        raise
    if published_snapshot is None:
        raise InventoryError("published governance snapshot is absent")
    return _GovernanceWriteTransaction(
        path=path,
        snapshot=published_snapshot,
        original_identity=expected_identity,
        original_raw=expected_raw,
        outcome=outcome,
        _revalidate_action=revalidate_transaction,
        _rollback_action=rollback_transaction,
        _finalize_action=finalize_transaction,
        _outstanding_roles_action=outstanding_roles,
        _artifact_paths_action=artifact_paths,
        _validated=True,
    )


def _write_atomic_lf_locked(
    path: Path,
    raw: bytes,
    *,
    expected_identity: tuple[int, ...] | None | object = (
        _AUTOMATIC_DESTINATION_IDENTITY
    ),
    _expected_raw: bytes | None = None,
    _outcome: _GovernanceWriteOutcome | None = None,
    _lifetime_check: Any | None = None,
    _post_publish_lifetime_check: Any | None = None,
    _retain_transaction: bool | None = None,
    _posix_parent_binding: _PosixParentDirectoryOwner | None = None,
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
    if _retain_transaction is not True:
        raise InventoryError(
            "locked governance writer requires a group-owned transaction"
        )
    candidate = Path(os.path.abspath(path))
    if _posix_parent_binding is not None:
        candidate = _posix_parent_binding.path / candidate.name
        _posix_parent_binding.revalidate()
        chain = _posix_parent_binding.chain
    else:
        chain = _governance_directory_chain(candidate.parent)
    automatic_snapshot = None
    if expected_identity is _AUTOMATIC_DESTINATION_IDENTITY:
        if os.path.lexists(candidate):
            automatic_snapshot = secure_filesystem.read_regular_snapshot(
                candidate,
                maximum_bytes=MAXIMUM_SOURCE_BYTES,
                root=candidate.parent,
            )
        captured_identity = (
            None if automatic_snapshot is None else automatic_snapshot.identity
        )
        captured_raw = (
            None if automatic_snapshot is None else automatic_snapshot.raw
        )
    else:
        captured_identity = expected_identity
        captured_raw = _expected_raw
    if captured_identity is not None and not isinstance(
        captured_identity,
        tuple,
    ):
        raise InventoryError("governance expected destination identity is invalid")
    _require_governance_destination_identity(candidate, captured_identity)
    outcome = _outcome or _GovernanceWriteOutcome()
    post_publish_lifetime_check = _post_publish_lifetime_check
    if post_publish_lifetime_check is None and _lifetime_check is not None:
        post_publish_lifetime_check = lambda _snapshot: _lifetime_check()
    if os.name == "nt":
        transaction = _write_windows_governance(
            candidate,
            raw,
            chain,
            captured_identity,
            captured_raw,
            outcome,
            _lifetime_check,
            post_publish_lifetime_check,
            True,
        )
    else:
        transaction = _write_posix_governance(
            candidate,
            raw,
            chain,
            captured_identity,
            captured_raw,
            outcome,
            _lifetime_check,
            post_publish_lifetime_check,
            _posix_parent_binding,
            True,
        )
    return transaction


def write_atomic_lf(
    path: Path,
    raw: bytes,
    *the_args: object,
    expected_identity: tuple[int, ...] | None | object = (
        _AUTOMATIC_DESTINATION_IDENTITY
    ),
    _expected_raw: bytes | None = None,
    _outcome: _GovernanceWriteOutcome | None = None,
    _lifetime_check: Any | None = None,
    _post_publish_lifetime_check: Any | None = None,
    _retain_transaction: bool | None = None,
) -> object:
    if the_args:
        raise InventoryError("atomic LF writes reject positional options")
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
        raise InventoryError(
            "governance output must be BOM-free canonical LF with one final LF"
        )
    active_group = _governance_active_group()
    if active_group is not None:
        candidate = active_group.require_destination(path)
        parent_binding = None
        if os.name != "nt":
            parent_binding = active_group.lock_set.posix_parent_for(candidate)
        try:
            transaction = _write_atomic_lf_locked(
                candidate,
                raw,
                expected_identity=expected_identity,
                _expected_raw=_expected_raw,
                _outcome=_outcome,
                _lifetime_check=_lifetime_check,
                _post_publish_lifetime_check=_post_publish_lifetime_check,
                _retain_transaction=True,
                _posix_parent_binding=parent_binding,
            )
        except _GovernancePreparationFailure as failure:
            active_group.add_participant(failure.participant)
            raise failure.primary
        if not isinstance(transaction, _GovernanceWriteTransaction):
            raise InventoryError("governance transaction is absent")
        active_group.add_participant(
            _GovernanceTransactionParticipant(transaction, candidate, raw)
        )
        return transaction.snapshot
    manager = _governance_cleanup_manager()
    manager.retry_pending()
    reservation = manager.reserve()
    try:
        destinations = _GovernanceDestinationSet.build((path,))
        lock_set = _GovernanceLockSetLease.acquire(destinations, reservation)
    except BaseException:
        manager.release(reservation)
        raise
    group = _GovernanceWriteGroup(lock_set, reservation)
    parent_binding = None
    if os.name != "nt":
        parent_binding = lock_set.posix_parent_for(path)
    try:
        transaction = _write_atomic_lf_locked(
            path,
            raw,
            expected_identity=expected_identity,
            _expected_raw=_expected_raw,
            _outcome=_outcome,
            _lifetime_check=_lifetime_check,
            _post_publish_lifetime_check=_post_publish_lifetime_check,
            _retain_transaction=True,
            _posix_parent_binding=parent_binding,
        )
    except _GovernancePreparationFailure as failure:
        group.add_participant(failure.participant)
        group.abort_precommit(failure.primary)
        raise AssertionError("unreachable governance abort")
    except BaseException as error:
        group.abort_precommit(error)
        raise AssertionError("unreachable governance abort")
    if not isinstance(transaction, _GovernanceWriteTransaction):
        group.abort_precommit(InventoryError("governance transaction is absent"))
        raise AssertionError("unreachable governance abort")
    group.add_participant(
        _GovernanceTransactionParticipant(transaction, path, raw)
    )
    try:
        group.validate_all(None)
    except BaseException as error:
        group.abort_precommit(error)
        raise AssertionError("unreachable governance abort")
    group.mark_committed()
    group.finish_committed_cleanup()
    return transaction.snapshot


def _write_governance_pair(
    first_path: Path,
    first_raw: bytes,
    second_path: Path,
    second_raw: bytes,
    *,
    lifetime_check: Any | None = None,
) -> object:
    post_publish_check = (
        None
        if lifetime_check is None
        else lambda _snapshot: lifetime_check()
    )

    def publish_into_active_group() -> _GovernancePairTransaction:
        group = _governance_active_group()
        if group is None:
            raise InventoryError("governance pair group is absent")
        first_target = group.require_destination(first_path)
        second_target = group.require_destination(second_path)
        _reject_native_destination_aliases((first_target, second_target))
        first_snapshot = secure_filesystem.read_regular_snapshot(
            first_target,
            maximum_bytes=MAXIMUM_SOURCE_BYTES,
            root=first_target.parent,
        )
        second_snapshot = secure_filesystem.read_regular_snapshot(
            second_target,
            maximum_bytes=MAXIMUM_SOURCE_BYTES,
            root=second_target.parent,
        )
        first_index = len(group.participants)
        write_atomic_lf(
            first_target,
            first_raw,
            expected_identity=first_snapshot.identity,
            _expected_raw=first_snapshot.raw,
            _lifetime_check=lifetime_check,
            _post_publish_lifetime_check=post_publish_check,
        )
        write_atomic_lf(
            second_target,
            second_raw,
            expected_identity=second_snapshot.identity,
            _expected_raw=second_snapshot.raw,
            _lifetime_check=lifetime_check,
            _post_publish_lifetime_check=post_publish_check,
        )
        participants = group.participants[first_index:]
        if (
            len(participants) != 2
            or any(
                not isinstance(item, _GovernanceTransactionParticipant)
                for item in participants
            )
        ):
            raise InventoryError("governance pair participants are incomplete")
        pair = _GovernancePairTransaction(
            tuple(item.transaction for item in participants),
            lifetime_check,
        )
        pair.revalidate()
        return pair

    if _governance_active_group() is not None:
        return publish_into_active_group()

    manager = _governance_cleanup_manager()
    manager.retry_pending()
    reservation = manager.reserve()
    try:
        destinations = _GovernanceDestinationSet.build((first_path, second_path))
        lock_set = _GovernanceLockSetLease.acquire(destinations, reservation)
    except BaseException:
        manager.release(reservation)
        raise
    group = _GovernanceWriteGroup(lock_set, reservation)
    previous_group = _governance_active_group()
    try:
        _GOVERNANCE_TRANSACTION_CONTEXT.group = group
        pair = publish_into_active_group()
        group.validate_all(None)
    except BaseException as error:
        if previous_group is None:
            try:
                del _GOVERNANCE_TRANSACTION_CONTEXT.group
            except AttributeError:
                pass
        else:
            _GOVERNANCE_TRANSACTION_CONTEXT.group = previous_group
        group.abort_precommit(error)
        raise AssertionError("unreachable governance pair abort")
    if previous_group is None:
        try:
            del _GOVERNANCE_TRANSACTION_CONTEXT.group
        except AttributeError:
            pass
    else:
        _GOVERNANCE_TRANSACTION_CONTEXT.group = previous_group
    group.mark_committed()
    group.finish_committed_cleanup()
    return pair


def _inventory_semantic(inventory: Mapping[str, object]) -> str:
    return sha256(_semantic_bytes(inventory)).hexdigest()


def _item_universe(
    inventory: Mapping[str, object],
    discovery: Discovery,
) -> tuple[tuple[str, str], ...]:
    entries = inventory["entries"]
    design_stable_ids: set[str] = set()
    for entry in entries:
        assignment = entry.get("assignment")
        exclusion = entry.get("exclusion")
        if isinstance(assignment, Mapping):
            if str(assignment["profile_name"]) != "historical":
                design_stable_ids.add(str(entry["stable_id"]))
        elif isinstance(exclusion, Mapping):
            design_stable_ids.add(str(entry["stable_id"]))
        else:
            raise InventoryError("inventory item has no assignment or exclusion")
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
_PROTECTED_NAMESPACE_MEMBERS = frozenset(
    _SUBPROCESS_FUNCTIONS
    | {
        "unittest.skip",
        "unittest.skipIf",
        "unittest.skipUnless",
    }
)
_PROTECTED_MUTATION_ALIAS = "__pontius_protected_namespace_member_mutated__"
_SAFE_OBSERVATION_CALLS = {
    "inspect.getsource",
    "inspect.getsourcefile",
    "inspect.signature",
    "str",
}
_SAFE_MOCK_FACTORIES = {
    "unittest.mock.MagicMock",
    "unittest.mock.Mock",
    "unittest.mock.patch",
    "unittest.mock.patch.object",
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
_SCIENTIFIC_COMPILE_CALLS = {
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
        "pontius.incremental_leaf_adjoint_response."
        "compile_leaf_adjoint_response_caches"
    ),
    "pontius.h32_action_width_quality_audit._compile_cache",
    "pontius.legal_river_quotient_cuda_compensated_tiles._kernels",
}
_SCIENTIFIC_BIND_CALLS = {
    (
        "pontius.shared_resident_response_context."
        "bind_resident_response_context"
    ),
}
_SCIENTIFIC_PLAN_CALLS = {
    "pontius.h32_action_width_quality_audit._arm_plan",
}
_SCIENTIFIC_VERIFY_CALLS = {
    "pontius.h32_action_width_quality_audit._verify_candidate_stream",
    (
        "pontius.legal_river_quotient_cuda_compensated_tiles."
        "_run_primitive_controls"
    ),
}
_SCIENTIFIC_QUERY_CALLS = {
    "pontius.full_width_river_capacity_preflight._small_control",
    "pontius.full_width_river_capacity_preflight_v2._runtime_snapshot",
    (
        "pontius.legal_river_quotient_cuda_compensated_tiles."
        "_query_weight_evidence"
    ),
    (
        "pontius.legal_river_quotient_cuda_compensated_tiles."
        "_ten_card_evidence"
    ),
}
_SCIENTIFIC_ALLOCATION_CALLS = {
    (
        "pontius.legal_river_quotient_cuda_compensated_tiles."
        "_allocate_resident"
    ),
}
_SCIENTIFIC_CONTRACT_CALLS = {
    (
        "pontius.heterogeneous_leaf_contraction."
        "contract_heterogeneous_leaf_terms"
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
        "pontius.resident_heterogeneous_leaf_contraction."
        "contract_resident_heterogeneous_leaf_terms"
    ),
}
_SCIENTIFIC_EVALUATE_CALLS = {
    "pontius.leaf_adjoint_evaluation.evaluate_leaf_adjoint_seat",
    (
        "pontius.cross_payoff_adjoint_result."
        "evaluate_typed_multi_size_affine_cross_payoff"
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
        "pontius.multi_size_affine_resident_leaf_adjoint_evaluation."
        "evaluate_multi_size_affine_resident_profile"
    ),
    (
        "pontius.resident_leaf_adjoint_evaluation."
        "evaluate_resident_leaf_adjoint_seat"
    ),
}
_SCIENTIFIC_TRAVERSE_CALLS = {
    (
        "pontius.multi_size_affine_resident_leaf_adjoint_cfr."
        "multi_size_affine_resident_leaf_adjoint_cfr_traverser"
    ),
    (
        "pontius.multi_size_resident_leaf_adjoint_cfr."
        "multi_size_resident_leaf_adjoint_cfr_traverser"
    ),
    (
        "pontius.resident_leaf_adjoint_cfr."
        "resident_leaf_adjoint_cfr_traverser"
    ),
}
_SCIENTIFIC_FINALIZE_CALLS = {
    (
        "pontius.resident_record_to_hand_fold_v2."
        "finalize_resident_record_accumulators_v2"
    ),
}
_SCIENTIFIC_CALL_CONTRACTS = {
    **{
        name: ("compile", "scientific_artifact")
        for name in _SCIENTIFIC_COMPILE_CALLS
    },
    **{
        name: ("bind", "scientific_context")
        for name in _SCIENTIFIC_BIND_CALLS
    },
    **{
        name: ("plan", "scientific_plan")
        for name in _SCIENTIFIC_PLAN_CALLS
    },
    **{
        name: ("verify", "scientific_evidence")
        for name in _SCIENTIFIC_VERIFY_CALLS
    },
    **{
        name: ("query", "scientific_evidence")
        for name in _SCIENTIFIC_QUERY_CALLS
    },
    **{
        name: ("allocate", "device_array")
        for name in _SCIENTIFIC_ALLOCATION_CALLS
    },
    **{
        name: ("contract", "scientific_result")
        for name in _SCIENTIFIC_CONTRACT_CALLS
    },
    **{
        name: ("evaluate", "scientific_result")
        for name in _SCIENTIFIC_EVALUATE_CALLS
    },
    **{
        name: ("traverse", "scientific_result")
        for name in _SCIENTIFIC_TRAVERSE_CALLS
    },
    **{
        name: ("finalize", "scientific_result")
        for name in _SCIENTIFIC_FINALIZE_CALLS
    },
}
if set(_SCIENTIFIC_CALL_CONTRACTS) != _SCIENTIFIC_PROTECTED_CALLS:
    raise RuntimeError("scientific call registry is not exactly classified")
_PROTECTED_NAMESPACE_MEMBERS = frozenset(
    _PROTECTED_NAMESPACE_MEMBERS
    | _OWNER_CALLS
    | _SCIENTIFIC_PROTECTED_CALLS
    | set(_CUDA_CALLS)
    | _CUDA_BLOCKED_CALLS
)
_STATIC_UNRESOLVED = object()


def _module_import_aliases(
    tree: ast.Module,
    *,
    stop_before: ast.stmt | None = None,
) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for node in tree.body:
        if node is stop_before:
            break
        if isinstance(node, ast.Import):
            for imported in node.names:
                local = imported.asname or imported.name.split(".", 1)[0]
                aliases[local] = imported.name if imported.asname else local
        elif isinstance(node, ast.ImportFrom) and node.module:
            for imported in node.names:
                local = imported.asname or imported.name
                aliases[local] = f"{node.module}.{imported.name}"
        elif stop_before is not None and isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    aliases.pop(target.id, None)
        elif (
            stop_before is not None
            and isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
        ):
            aliases.pop(node.target.id, None)
        elif stop_before is not None and isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef),
        ):
            aliases.pop(node.name, None)
        elif stop_before is not None and isinstance(node, ast.Delete):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    aliases.pop(target.id, None)
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


def _static_assignments_before(
    nodes: Iterable[ast.stmt],
    stop: ast.stmt,
) -> dict[str, ast.expr]:
    """Return simple bindings visible immediately before ``stop``."""

    assignments: dict[str, ast.expr] = {}
    for node in nodes:
        if node is stop:
            break
        if isinstance(node, ast.Assign):
            captured = node.value
            seen: set[str] = set()
            while (
                isinstance(captured, ast.Name)
                and captured.id in assignments
                and captured.id not in seen
            ):
                seen.add(captured.id)
                captured = assignments[captured.id]
            for target in node.targets:
                if isinstance(target, ast.Name):
                    assignments[target.id] = captured
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.value is not None:
                captured = node.value
                seen = set()
                while (
                    isinstance(captured, ast.Name)
                    and captured.id in assignments
                    and captured.id not in seen
                ):
                    seen.add(captured.id)
                    captured = assignments[captured.id]
                assignments[node.target.id] = captured
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            assignments.pop(node.name, None)
        elif isinstance(node, ast.Import):
            for imported in node.names:
                assignments.pop(
                    imported.asname or imported.name.split(".", 1)[0],
                    None,
                )
        elif isinstance(node, ast.ImportFrom):
            for imported in node.names:
                assignments.pop(imported.asname or imported.name, None)
        elif isinstance(node, ast.Delete):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    assignments.pop(target.id, None)
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
    module_bound_names: frozenset[str] = frozenset()
    enclosing_exception_names: frozenset[str] = frozenset()
    descriptor_kind: str | None = "ordinary"


def _metered_ast_walk(
    node: ast.AST,
    budget: "_AnalysisBudget",
) -> Iterable[ast.AST]:
    pending = [node]
    while pending:
        candidate = pending.pop()
        budget.consume()
        yield candidate
        pending.extend(reversed(tuple(ast.iter_child_nodes(candidate))))


class _ExecutionScopeVisitor(ast.NodeVisitor):
    def __init__(self, budget: "_AnalysisBudget | None" = None) -> None:
        self.budget = budget
        self.calls: list[ast.Call] = []
        self.imports: list[ast.Import | ast.ImportFrom] = []
        self.assignments: list[ast.Assign | ast.AnnAssign] = []
        self.local_functions: dict[
            str,
            ast.FunctionDef | ast.AsyncFunctionDef,
        ] = {}
        self.local_function_definitions: list[
            ast.FunctionDef | ast.AsyncFunctionDef
        ] = []
        self.local_classes: set[str] = set()
        self.callback_names: set[str] = set()
        self.closure_blockers: list[tuple[ast.Call, str]] = []

    def visit(self, node: ast.AST) -> object:
        if self.budget is not None:
            self.budget.consume()
        return super().visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        self.calls.append(node)
        if isinstance(node.func, ast.Lambda) and _contains_sensitive_runtime(
            node.func.body,
            self.budget,
        ):
            self.closure_blockers.append((node, "invoked lambda closure"))
        if (
            isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Call)
            and isinstance(node.func.value.func, ast.Name)
            and node.func.value.func.id in self.local_classes
        ):
            self.closure_blockers.append(
                (node, "local class runtime closure")
            )
        callback_arguments = [
            *node.args,
            *(keyword.value for keyword in node.keywords),
        ]
        if any(
            isinstance(argument, ast.Name)
            and argument.id in self.callback_names
            for argument in callback_arguments
        ):
            self.closure_blockers.append((node, "callback closure"))
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        self.imports.append(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        self.imports.append(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        self.assignments.append(node)
        if (
            len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
        ):
            if (
                isinstance(node.value, ast.Lambda)
                and _contains_sensitive_runtime(node.value.body, self.budget)
            ) or (
                isinstance(node.value, ast.Name)
                and node.value.id in self.callback_names
            ):
                self.callback_names.add(node.targets[0].id)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        self.assignments.append(node)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.local_function_definitions.append(node)
        self.local_functions[node.name] = node
        if _contains_sensitive_runtime(node, self.budget):
            self.callback_names.add(node.name)
        for expression in (*node.decorator_list, *node.args.defaults):
            self.visit(expression)
        for expression in node.args.kw_defaults:
            if expression is not None:
                self.visit(expression)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.local_function_definitions.append(node)
        self.local_functions[node.name] = node
        if _contains_sensitive_runtime(node, self.budget):
            self.callback_names.add(node.name)
        for expression in (*node.decorator_list, *node.args.defaults):
            self.visit(expression)
        for expression in node.args.kw_defaults:
            if expression is not None:
                self.visit(expression)

    def visit_Lambda(self, node: ast.Lambda) -> None:
        return

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.local_classes.add(node.name)
        for expression in (*node.decorator_list, *node.bases):
            self.visit(expression)
        for keyword in node.keywords:
            self.visit(keyword.value)
        for statement in node.body:
            if isinstance(
                statement,
                (ast.FunctionDef, ast.AsyncFunctionDef),
            ):
                for expression in (
                    *statement.decorator_list,
                    *statement.args.defaults,
                ):
                    self.visit(expression)
                for expression in statement.args.kw_defaults:
                    if expression is not None:
                        self.visit(expression)
                continue
            self.visit(statement)


def _contains_sensitive_runtime(
    node: ast.AST,
    budget: "_AnalysisBudget | None" = None,
) -> bool:
    candidates = (
        ast.walk(node)
        if budget is None
        else _metered_ast_walk(node, budget)
    )
    for candidate in candidates:
        if not isinstance(candidate, ast.Call):
            continue
        qualified = _qualified_name(candidate.func)
        if qualified in _SUBPROCESS_FUNCTIONS:
            return True
        if qualified is not None and (
            qualified.startswith(("cupy.", "cp.", "pontius."))
            or qualified.endswith((".run", ".Popen"))
        ):
            return True
    return False


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
    budget: "_AnalysisBudget | None" = None,
) -> _ExecutionScopeVisitor:
    visitor = _ExecutionScopeVisitor(budget)
    try:
        for statement in node.body:
            visitor.visit(statement)
    except RecursionError as error:
        raise InventoryError(
            "analysis expression depth exceeds safe recursion"
        ) from error
    return visitor


def _merge_call_counts(
    *counts: Mapping[bytes, int],
) -> dict[bytes, int]:
    merged: dict[bytes, int] = {}
    for supplied in counts:
        for key, value in supplied.items():
            merged[key] = _checked_cardinality_add(
                merged.get(key, 0),
                value,
            )
    return merged


def _maximum_call_counts(
    first: Mapping[bytes, int],
    second: Mapping[bytes, int],
) -> dict[bytes, int]:
    return {
        key: _checked_cardinality(max(first.get(key, 0), second.get(key, 0)))
        for key in set(first) | set(second)
    }


def _checked_cardinality(value: int) -> int:
    if value < 0 or value > MAXIMUM_ANALYSIS_CARDINALITY:
        raise InventoryError(
            "analysis expanded cardinality exceeds 2147483647"
        )
    return value


def _checked_cardinality_add(first: int, second: int) -> int:
    _checked_cardinality(first)
    _checked_cardinality(second)
    if first > MAXIMUM_ANALYSIS_CARDINALITY - second:
        raise InventoryError(
            "analysis expanded cardinality exceeds 2147483647"
        )
    return first + second


def _checked_cardinality_multiply(first: int, second: int) -> int:
    _checked_cardinality(first)
    _checked_cardinality(second)
    if first and second > MAXIMUM_ANALYSIS_CARDINALITY // first:
        raise InventoryError(
            "analysis expanded cardinality exceeds 2147483647"
        )
    return first * second


def _helper_return_cardinality(definition: _ReviewFunction) -> int | None:
    returns = [
        statement
        for statement in definition.node.body
        if isinstance(statement, ast.Return)
    ]
    if len(returns) != 1 or returns[0].value is None:
        return None
    value = returns[0].value
    if isinstance(value, (ast.Tuple, ast.List, ast.Set)):
        return len(value.elts)
    if isinstance(value, ast.Dict):
        return len(value.keys)
    return None


def _static_iteration_bound(
    node: ast.expr,
    *,
    assignments: Mapping[str, ast.expr],
    relative_path: str,
    aliases: Mapping[str, str],
    helper_registry: Mapping[str, _ReviewFunction],
    seen: frozenset[str] = frozenset(),
) -> int | None:
    annotated = getattr(node, "_pontius_iteration_bound", _STATIC_UNRESOLVED)
    if annotated is not _STATIC_UNRESOLVED:
        return annotated
    if isinstance(node, ast.Name):
        if node.id in seen or node.id not in assignments:
            return None
        return _static_iteration_bound(
            assignments[node.id],
            assignments=assignments,
            relative_path=relative_path,
            aliases=aliases,
            helper_registry=helper_registry,
            seen=seen | {node.id},
        )
    if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
        return len(node.elts)
    if isinstance(node, ast.Dict):
        return len(node.keys)
    if isinstance(node, ast.Call):
        function = _resolved_qualified_name(node.func, aliases)
        if function in {"enumerate", "tuple", "list"} and len(node.args) == 1:
            return _static_iteration_bound(
                node.args[0],
                assignments=assignments,
                relative_path=relative_path,
                aliases=aliases,
                helper_registry=helper_registry,
                seen=seen,
            )
        if function == "range" and 1 <= len(node.args) <= 3:
            values = [_static_value(argument, assignments) for argument in node.args]
            if all(type(value) is int for value in values):
                if len(values) == 3 and values[2] == 0:
                    raise InventoryError("analysis range step is zero")
                try:
                    cardinality = len(range(*values))
                except (OverflowError, ValueError) as error:
                    raise InventoryError(
                        "analysis range cardinality exceeds 2147483647"
                    ) from error
                if cardinality > MAXIMUM_ANALYSIS_CARDINALITY:
                    raise InventoryError(
                        "analysis expanded cardinality exceeds 2147483647"
                    )
                return cardinality
        helper = _resolved_helper(
            node,
            relative_path=relative_path,
            class_name=None,
            aliases=aliases,
            registry=helper_registry,
        )
        if helper is not None and not node.args and not node.keywords:
            return _helper_return_cardinality(helper[1])
    return None


def _expression_call_counts(
    node: ast.AST | None,
    definitions: Mapping[int, bytes],
    *,
    assignments: Mapping[str, ast.expr],
    relative_path: str,
    aliases: Mapping[str, str],
    helper_registry: Mapping[str, _ReviewFunction],
    multiplier: int = 1,
    analysis_budget: "_AnalysisBudget | None" = None,
) -> tuple[dict[bytes, int], set[bytes]]:
    if node is None:
        return {}, set()
    if analysis_budget is None:
        analysis_budget = _AnalysisBudget()
    analysis_budget.consume()
    if isinstance(
        node,
        (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef),
    ):
        return {}, set()
    if isinstance(node, ast.IfExp):
        test_counts, test_dynamic = _expression_call_counts(
            node.test,
            definitions,
            assignments=assignments,
            relative_path=relative_path,
            aliases=aliases,
            helper_registry=helper_registry,
            multiplier=multiplier,
            analysis_budget=analysis_budget,
        )
        body_counts, body_dynamic = _expression_call_counts(
            node.body,
            definitions,
            assignments=assignments,
            relative_path=relative_path,
            aliases=aliases,
            helper_registry=helper_registry,
            multiplier=multiplier,
            analysis_budget=analysis_budget,
        )
        else_counts, else_dynamic = _expression_call_counts(
            node.orelse,
            definitions,
            assignments=assignments,
            relative_path=relative_path,
            aliases=aliases,
            helper_registry=helper_registry,
            multiplier=multiplier,
            analysis_budget=analysis_budget,
        )
        return (
            _merge_call_counts(
                test_counts,
                _maximum_call_counts(body_counts, else_counts),
            ),
            test_dynamic | body_dynamic | else_dynamic,
        )
    if isinstance(
        node,
        (ast.ListComp, ast.SetComp, ast.GeneratorExp, ast.DictComp),
    ):
        counts: dict[bytes, int] = {}
        dynamic: set[bytes] = set()
        repeated = multiplier
        for generator in node.generators:
            iterator_counts, iterator_dynamic = _expression_call_counts(
                generator.iter,
                definitions,
                assignments=assignments,
                relative_path=relative_path,
                aliases=aliases,
                helper_registry=helper_registry,
                multiplier=repeated,
                analysis_budget=analysis_budget,
            )
            counts = _merge_call_counts(counts, iterator_counts)
            dynamic |= iterator_dynamic
            bound = _static_iteration_bound(
                generator.iter,
                assignments=assignments,
                relative_path=relative_path,
                aliases=aliases,
                helper_registry=helper_registry,
            )
            if bound is None:
                repeated_node: ast.AST = node
                repeated_keys: set[bytes] = set()
                pending = [repeated_node]
                while pending:
                    candidate = pending.pop()
                    analysis_budget.consume()
                    if (
                        isinstance(candidate, ast.Call)
                        and id(candidate) in definitions
                    ):
                        repeated_keys.add(definitions[id(candidate)])
                    pending.extend(ast.iter_child_nodes(candidate))
                dynamic |= repeated_keys
                return counts, dynamic
            repeated = _checked_cardinality_multiply(repeated, bound)
            for condition in generator.ifs:
                condition_counts, condition_dynamic = _expression_call_counts(
                    condition,
                    definitions,
                    assignments=assignments,
                    relative_path=relative_path,
                    aliases=aliases,
                    helper_registry=helper_registry,
                    multiplier=repeated,
                    analysis_budget=analysis_budget,
                )
                counts = _merge_call_counts(counts, condition_counts)
                dynamic |= condition_dynamic
        values = (
            (node.key, node.value)
            if isinstance(node, ast.DictComp)
            else (node.elt,)
        )
        for value in values:
            value_counts, value_dynamic = _expression_call_counts(
                value,
                definitions,
                assignments=assignments,
                relative_path=relative_path,
                aliases=aliases,
                helper_registry=helper_registry,
                multiplier=repeated,
                analysis_budget=analysis_budget,
            )
            counts = _merge_call_counts(counts, value_counts)
            dynamic |= value_dynamic
        return counts, dynamic
    counts: dict[bytes, int] = {}
    if isinstance(node, ast.Call) and id(node) in definitions:
        counts[definitions[id(node)]] = multiplier
    dynamic: set[bytes] = set()
    for child in ast.iter_child_nodes(node):
        child_counts, child_dynamic = _expression_call_counts(
            child,
            definitions,
            assignments=assignments,
            relative_path=relative_path,
            aliases=aliases,
            helper_registry=helper_registry,
            multiplier=multiplier,
            analysis_budget=analysis_budget,
        )
        counts = _merge_call_counts(counts, child_counts)
        dynamic |= child_dynamic
    return counts, dynamic


def _runtime_call_bounds(
    statements: Sequence[ast.stmt],
    definitions: Mapping[int, bytes],
    *,
    assignments: Mapping[str, ast.expr],
    relative_path: str,
    aliases: Mapping[str, str],
    helper_registry: Mapping[str, _ReviewFunction],
    analysis_budget: "_AnalysisBudget | None" = None,
) -> tuple[dict[bytes, int], set[bytes]]:
    try:
        return _runtime_call_bounds_impl(
            statements,
            definitions,
            assignments=assignments,
            relative_path=relative_path,
            aliases=aliases,
            helper_registry=helper_registry,
            analysis_budget=analysis_budget,
        )
    except RecursionError as error:
        raise InventoryError(
            "analysis expression depth exceeds safe recursion"
        ) from error


def _runtime_call_bounds_impl(
    statements: Sequence[ast.stmt],
    definitions: Mapping[int, bytes],
    *,
    assignments: Mapping[str, ast.expr],
    relative_path: str,
    aliases: Mapping[str, str],
    helper_registry: Mapping[str, _ReviewFunction],
    analysis_budget: "_AnalysisBudget | None" = None,
) -> tuple[dict[bytes, int], set[bytes]]:
    if analysis_budget is None:
        analysis_budget = _AnalysisBudget()
    counts: dict[bytes, int] = {}
    dynamic: set[bytes] = set()
    for statement in statements:
        analysis_budget.consume()
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
            expressions: list[ast.AST] = [
                *statement.decorator_list,
                *statement.args.defaults,
                *(
                    value
                    for value in statement.args.kw_defaults
                    if value is not None
                ),
            ]
            if statement.returns is not None:
                expressions.append(statement.returns)
            for expression in expressions:
                expression_counts, expression_dynamic = (
                    _expression_call_counts(
                        expression,
                        definitions,
                        assignments=assignments,
                        relative_path=relative_path,
                        aliases=aliases,
                        helper_registry=helper_registry,
                        analysis_budget=analysis_budget,
                    )
                )
                counts = _merge_call_counts(counts, expression_counts)
                dynamic |= expression_dynamic
            continue
        if isinstance(statement, ast.ClassDef):
            expressions = [
                *statement.decorator_list,
                *statement.bases,
                *(keyword.value for keyword in statement.keywords),
            ]
            for expression in expressions:
                expression_counts, expression_dynamic = (
                    _expression_call_counts(
                        expression,
                        definitions,
                        assignments=assignments,
                        relative_path=relative_path,
                        aliases=aliases,
                        helper_registry=helper_registry,
                        analysis_budget=analysis_budget,
                    )
                )
                counts = _merge_call_counts(counts, expression_counts)
                dynamic |= expression_dynamic
            class_counts, class_dynamic = _runtime_call_bounds(
                statement.body,
                definitions,
                assignments=assignments,
                relative_path=relative_path,
                aliases=aliases,
                helper_registry=helper_registry,
                analysis_budget=analysis_budget,
            )
            counts = _merge_call_counts(counts, class_counts)
            dynamic |= class_dynamic
            continue
        if isinstance(statement, ast.If):
            test_counts, test_dynamic = _expression_call_counts(
                statement.test,
                definitions,
                assignments=assignments,
                relative_path=relative_path,
                aliases=aliases,
                helper_registry=helper_registry,
                analysis_budget=analysis_budget,
            )
            body_counts, body_dynamic = _runtime_call_bounds(
                statement.body,
                definitions,
                assignments=assignments,
                relative_path=relative_path,
                aliases=aliases,
                helper_registry=helper_registry,
                analysis_budget=analysis_budget,
            )
            else_counts, else_dynamic = _runtime_call_bounds(
                statement.orelse,
                definitions,
                assignments=assignments,
                relative_path=relative_path,
                aliases=aliases,
                helper_registry=helper_registry,
                analysis_budget=analysis_budget,
            )
            counts = _merge_call_counts(
                counts,
                test_counts,
                _maximum_call_counts(body_counts, else_counts),
            )
            dynamic |= test_dynamic | body_dynamic | else_dynamic
            if _statements_terminate_without_fallthrough((statement,)):
                break
            continue
        if isinstance(statement, (ast.For, ast.AsyncFor)):
            iterator_counts, iterator_dynamic = _expression_call_counts(
                statement.iter,
                definitions,
                assignments=assignments,
                relative_path=relative_path,
                aliases=aliases,
                helper_registry=helper_registry,
                analysis_budget=analysis_budget,
            )
            body_counts, body_dynamic = _runtime_call_bounds(
                statement.body,
                definitions,
                assignments=assignments,
                relative_path=relative_path,
                aliases=aliases,
                helper_registry=helper_registry,
                analysis_budget=analysis_budget,
            )
            else_counts, else_dynamic = _runtime_call_bounds(
                statement.orelse,
                definitions,
                assignments=assignments,
                relative_path=relative_path,
                aliases=aliases,
                helper_registry=helper_registry,
                analysis_budget=analysis_budget,
            )
            bound = _static_iteration_bound(
                statement.iter,
                assignments=assignments,
                relative_path=relative_path,
                aliases=aliases,
                helper_registry=helper_registry,
            )
            if bound is None:
                dynamic |= set(body_counts) | body_dynamic
                body_counts = {}
            else:
                expanded_counts: dict[bytes, int] = {}
                for key, value in body_counts.items():
                    expanded_counts[key] = _checked_cardinality_multiply(
                        value,
                        bound,
                    )
                body_counts = expanded_counts
                dynamic |= body_dynamic
            counts = _merge_call_counts(
                counts, iterator_counts, body_counts, else_counts
            )
            dynamic |= iterator_dynamic | else_dynamic
            if _statements_terminate_without_fallthrough((statement,)):
                break
            continue
        if isinstance(statement, ast.While):
            test_counts, test_dynamic = _expression_call_counts(
                statement.test,
                definitions,
                assignments=assignments,
                relative_path=relative_path,
                aliases=aliases,
                helper_registry=helper_registry,
                analysis_budget=analysis_budget,
            )
            body_counts, body_dynamic = _runtime_call_bounds(
                statement.body,
                definitions,
                assignments=assignments,
                relative_path=relative_path,
                aliases=aliases,
                helper_registry=helper_registry,
                analysis_budget=analysis_budget,
            )
            bound = getattr(
                statement,
                "_pontius_iteration_bound",
                None,
            )
            if bound == 0:
                body_counts = {}
                test_evaluations = 1
            elif bound is None:
                dynamic |= set(test_counts) | test_dynamic
                test_counts = {}
                dynamic |= set(body_counts) | body_dynamic
                body_counts = {}
            else:
                test_evaluations = _checked_cardinality(
                    int(
                        getattr(
                            statement,
                            "_pontius_condition_evaluations",
                            _checked_cardinality_add(bound, 1),
                        )
                    )
                )
                test_counts = {
                    key: _checked_cardinality_multiply(
                        value,
                        test_evaluations,
                    )
                    for key, value in test_counts.items()
                }
                body_counts = {
                    key: _checked_cardinality_multiply(value, bound)
                    for key, value in body_counts.items()
                }
                dynamic |= body_dynamic
            else_counts, else_dynamic = _runtime_call_bounds(
                statement.orelse,
                definitions,
                assignments=assignments,
                relative_path=relative_path,
                aliases=aliases,
                helper_registry=helper_registry,
                analysis_budget=analysis_budget,
            )
            counts = _merge_call_counts(
                counts, test_counts, body_counts, else_counts
            )
            dynamic |= test_dynamic | else_dynamic
            if _statements_terminate_without_fallthrough((statement,)):
                break
            continue
        if isinstance(statement, (ast.With, ast.AsyncWith)):
            for item in statement.items:
                item_counts, item_dynamic = _expression_call_counts(
                    item.context_expr,
                    definitions,
                    assignments=assignments,
                    relative_path=relative_path,
                    aliases=aliases,
                    helper_registry=helper_registry,
                    analysis_budget=analysis_budget,
                )
                counts = _merge_call_counts(counts, item_counts)
                dynamic |= item_dynamic
            body_counts, body_dynamic = _runtime_call_bounds(
                statement.body,
                definitions,
                assignments=assignments,
                relative_path=relative_path,
                aliases=aliases,
                helper_registry=helper_registry,
                analysis_budget=analysis_budget,
            )
            counts = _merge_call_counts(counts, body_counts)
            dynamic |= body_dynamic
            if _statements_terminate_without_fallthrough((statement,)):
                break
            continue
        if isinstance(statement, ast.Match):
            subject_counts, subject_dynamic = _expression_call_counts(
                statement.subject,
                definitions,
                assignments=assignments,
                relative_path=relative_path,
                aliases=aliases,
                helper_registry=helper_registry,
                analysis_budget=analysis_budget,
            )
            alternative_counts: dict[bytes, int] = {}
            alternative_dynamic: set[bytes] = set()
            failed_guard_counts: dict[bytes, int] = {}
            failed_guard_dynamic: set[bytes] = set()
            for case in statement.cases:
                guard_counts, guard_dynamic = _expression_call_counts(
                    case.guard,
                    definitions,
                    assignments=assignments,
                    relative_path=relative_path,
                    aliases=aliases,
                    helper_registry=helper_registry,
                    analysis_budget=analysis_budget,
                )
                body_counts, body_dynamic = _runtime_call_bounds(
                    case.body,
                    definitions,
                    assignments=assignments,
                    relative_path=relative_path,
                    aliases=aliases,
                    helper_registry=helper_registry,
                    analysis_budget=analysis_budget,
                )
                reached_guard = _merge_call_counts(
                    failed_guard_counts,
                    guard_counts,
                )
                case_counts = _merge_call_counts(reached_guard, body_counts)
                alternative_counts = _maximum_call_counts(
                    alternative_counts,
                    case_counts,
                )
                alternative_dynamic |= (
                    failed_guard_dynamic | guard_dynamic | body_dynamic
                )
                guard_value = _static_value(case.guard, assignments)
                guard_can_fail = case.guard is not None and guard_value is not True
                pattern_can_fail = not _pattern_is_irrefutable(case.pattern)
                if guard_can_fail:
                    failed_guard_counts = reached_guard
                    failed_guard_dynamic |= guard_dynamic
                elif not pattern_can_fail:
                    failed_guard_counts = {}
                    failed_guard_dynamic = set()
                    break
                if pattern_can_fail:
                    alternative_counts = _maximum_call_counts(
                        alternative_counts,
                        failed_guard_counts,
                    )
            alternative_counts = _maximum_call_counts(
                alternative_counts,
                failed_guard_counts,
            )
            alternative_dynamic |= failed_guard_dynamic
            counts = _merge_call_counts(
                counts,
                subject_counts,
                alternative_counts,
            )
            dynamic |= subject_dynamic | alternative_dynamic
            if _statements_terminate_without_fallthrough((statement,)):
                break
            continue
        try_types = (ast.Try,)
        if hasattr(ast, "TryStar"):
            try_types = (*try_types, ast.TryStar)
        if isinstance(statement, try_types):
            body_counts, body_dynamic = _runtime_call_bounds(
                statement.body,
                definitions,
                assignments=assignments,
                relative_path=relative_path,
                aliases=aliases,
                helper_registry=helper_registry,
                analysis_budget=analysis_budget,
            )
            alternative_counts, alternative_dynamic = _runtime_call_bounds(
                statement.orelse,
                definitions,
                assignments=assignments,
                relative_path=relative_path,
                aliases=aliases,
                helper_registry=helper_registry,
                analysis_budget=analysis_budget,
            )
            for handler in statement.handlers:
                type_counts, type_dynamic = _expression_call_counts(
                    handler.type,
                    definitions,
                    assignments=assignments,
                    relative_path=relative_path,
                    aliases=aliases,
                    helper_registry=helper_registry,
                    analysis_budget=analysis_budget,
                )
                handler_counts, handler_dynamic = _runtime_call_bounds(
                    handler.body,
                    definitions,
                    assignments=assignments,
                    relative_path=relative_path,
                    aliases=aliases,
                    helper_registry=helper_registry,
                    analysis_budget=analysis_budget,
                )
                alternative_counts = _maximum_call_counts(
                    alternative_counts,
                    _merge_call_counts(type_counts, handler_counts),
                )
                alternative_dynamic |= type_dynamic | handler_dynamic
            final_counts, final_dynamic = _runtime_call_bounds(
                statement.finalbody,
                definitions,
                assignments=assignments,
                relative_path=relative_path,
                aliases=aliases,
                helper_registry=helper_registry,
                analysis_budget=analysis_budget,
            )
            counts = _merge_call_counts(
                counts,
                body_counts,
                alternative_counts,
                final_counts,
            )
            dynamic |= (
                body_dynamic | alternative_dynamic | final_dynamic
            )
            if _statements_terminate_without_fallthrough((statement,)):
                break
            continue
        if isinstance(statement, (ast.Return, ast.Raise)):
            statement_counts, statement_dynamic = _expression_call_counts(
                statement,
                definitions,
                assignments=assignments,
                relative_path=relative_path,
                aliases=aliases,
                helper_registry=helper_registry,
                analysis_budget=analysis_budget,
            )
            counts = _merge_call_counts(counts, statement_counts)
            dynamic |= statement_dynamic
            break
        if isinstance(statement, (ast.Break, ast.Continue)):
            break
        statement_counts, statement_dynamic = _expression_call_counts(
            statement,
            definitions,
            assignments=assignments,
            relative_path=relative_path,
            aliases=aliases,
            helper_registry=helper_registry,
            analysis_budget=analysis_budget,
        )
        counts = _merge_call_counts(counts, statement_counts)
        dynamic |= statement_dynamic
    return counts, dynamic


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


def _contains_sensitive_reference(
    node: ast.AST,
    aliases: Mapping[str, str],
    local_sensitive_names: frozenset[str],
    budget: "_AnalysisBudget",
) -> bool:
    for candidate in _metered_ast_walk(node, budget):
        if isinstance(candidate, ast.Name):
            if candidate.id in local_sensitive_names:
                return True
            resolved = aliases.get(candidate.id, candidate.id)
            if _is_sensitive_namespace(resolved):
                return True
        elif isinstance(candidate, ast.Attribute):
            resolved = _resolved_qualified_name(candidate, aliases)
            if resolved is not None and _is_sensitive_namespace(resolved):
                return True
    return False


def _dynamic_sensitive_aliases(
    execution: _ExecutionScopeVisitor,
    aliases: Mapping[str, str],
    helper_registry: Mapping[str, _ReviewFunction],
    *,
    relative_path: str,
    class_name: str | None,
    analysis_budget: "_AnalysisBudget",
) -> dict[str, str]:
    local_sensitive_names = {
        name
        for name, node in execution.local_functions.items()
        if _helper_has_sensitive_closure(
            _ReviewFunction(
                relative_path,
                node,
                aliases,
                {},
                class_name,
            ),
            helper_registry,
            budget=analysis_budget,
        )
    }
    for key, definition in helper_registry.items():
        prefix = f"{relative_path}::"
        if not key.startswith(prefix):
            continue
        remainder = key[len(prefix) :]
        if "::" in remainder:
            continue
        if _helper_has_sensitive_closure(
            definition,
            helper_registry,
            budget=analysis_budget,
        ):
            local_sensitive_names.add(remainder)
    frozen_sensitive_names = frozenset(local_sensitive_names)
    dynamic: dict[str, str] = {}
    for statement in execution.assignments:
        target: ast.Name | None = None
        value: ast.expr | None = None
        if (
            isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
        ):
            target = statement.targets[0]
            value = statement.value
        elif (
            isinstance(statement, ast.AnnAssign)
            and isinstance(statement.target, ast.Name)
        ):
            target = statement.target
            value = statement.value
        if target is None or value is None:
            continue
        if _resolved_qualified_name(value, aliases) is not None:
            continue
        if not _contains_sensitive_reference(
            value,
            aliases,
            frozen_sensitive_names,
            analysis_budget,
        ):
            continue
        dynamic[target.id] = (
            "callable alias is dynamically unresolved"
            if any(
                isinstance(candidate, ast.Name)
                and candidate.id in frozen_sensitive_names
                for candidate in _metered_ast_walk(value, analysis_budget)
            )
            else "mixed protected receiver is dynamically unresolved"
        )
    return dynamic


@dataclass(frozen=True, slots=True)
class _ImplicitClassDescriptor:
    name: str
    sensitive_methods: frozenset[str]
    defined_methods: frozenset[str] = frozenset()
    custom_new: bool = False
    exact_init_review: bool = False
    methods: tuple[ast.FunctionDef | ast.AsyncFunctionDef, ...] = ()
    method_slots: tuple[
        tuple[str, ast.FunctionDef | ast.AsyncFunctionDef], ...
    ] = ()
    descriptor_members: tuple[tuple[str, "_ImplicitClassDescriptor"], ...] = ()
    base_descriptors: tuple["_ImplicitClassDescriptor", ...] = ()
    local_overrides: frozenset[str] = frozenset()
    local_sensitive_methods: frozenset[str] = frozenset()
    local_defined_methods: frozenset[str] = frozenset()
    local_method_slots: tuple[
        tuple[str, ast.FunctionDef | ast.AsyncFunctionDef], ...
    ] = ()
    local_descriptor_members: tuple[
        tuple[str, "_ImplicitClassDescriptor"], ...
    ] = ()
    proven_non_not_implemented_methods: frozenset[str] = frozenset()


@dataclass(frozen=True, slots=True)
class _FlowValue:
    kind: str
    value: object = None
    sensitive: bool = False
    reason: str | None = None
    mutable_collection: bool = False
    mutable_collection_identity: int | None = None
    container_kind: str | None = None


@dataclass(frozen=True, slots=True)
class _FlowEnvironment:
    owner: str
    additions: tuple[tuple[str, str], ...] = ()
    removals: tuple[str, ...] = ()
    poison: str | None = None


@dataclass(slots=True)
class _AnalysisBudget:
    work_units: int = 0
    local_generator_dependencies: dict[
        ast.FunctionDef | ast.AsyncFunctionDef,
        tuple[str, ...] | None,
    ] = field(default_factory=dict)

    def consume(self, units: int = 1) -> None:
        self.work_units += units
        if self.work_units > MAXIMUM_ANALYSIS_WORK_UNITS:
            raise InventoryError(
                "analysis work units exceed "
                f"{MAXIMUM_ANALYSIS_WORK_UNITS}"
            )

    def container(self, length: int) -> None:
        if length > MAXIMUM_ANALYSIS_CONTAINER_ELEMENTS:
            raise InventoryError(
                "analysis container elements exceed 4096"
            )
        self.consume(length + 1)

    def cardinality(self, value: int) -> int:
        _checked_cardinality(value)
        self.consume()
        return value


@dataclass(slots=True)
class _PreclassifierExceptionalState:
    state: tuple[dict[str, str], set[str]]
    exception_tag: str | None = None
    explicit: bool = False
    excluded_handlers: frozenset[str] = frozenset()


_BUILTIN_EXCEPTION_CANONICAL_NAMES: Mapping[str, str] = MappingProxyType({
    name: candidate.__name__
    for name, candidate in vars(builtins).items()
    if isinstance(candidate, type)
    and issubclass(candidate, BaseException)
})

_BUILTIN_EXCEPTION_ANCESTORS: Mapping[str, frozenset[str]] = MappingProxyType({
    candidate.__name__: frozenset(
        base.__name__
        for base in candidate.__mro__[1:]
        if base.__module__ == "builtins"
        and issubclass(base, BaseException)
    )
    for candidate in vars(builtins).values()
    if isinstance(candidate, type)
    and issubclass(candidate, BaseException)
})

# Constructor safety is deliberately independent from class provenance.  A
# builtin may be a valid handler/cause without its constructor being safe to
# execute with an arbitrary argument list.
_SAFE_BUILTIN_EXCEPTION_CONSTRUCTOR_ARITIES: Mapping[
    str,
    frozenset[int],
] = MappingProxyType({
    name: frozenset({0, 1})
    for name in (
        "ArithmeticError",
        "AssertionError",
        "AttributeError",
        "BaseException",
        "EOFError",
        "Exception",
        "FileExistsError",
        "FileNotFoundError",
        "GeneratorExit",
        "ImportError",
        "IndexError",
        "KeyError",
        "KeyboardInterrupt",
        "LookupError",
        "MemoryError",
        "NameError",
        "NotImplementedError",
        "OSError",
        "OverflowError",
        "PermissionError",
        "RuntimeError",
        "StopIteration",
        "SystemExit",
        "TypeError",
        "ValueError",
    )
} | {
    "UnicodeDecodeError": frozenset({5}),
    "UnicodeEncodeError": frozenset({5}),
    "UnicodeTranslateError": frozenset({4}),
})


def _builtin_exception_constructor_outcome(
    expression: ast.AST,
    scope: "_ExceptionNameScope",
) -> tuple[str | None, str | None, bool]:
    """Return exact success tag, exact error tag, and unknown-error fork."""

    if not isinstance(expression, ast.Call):
        tag = _explicit_raise_exception_tag(expression, scope)
        if tag is not None:
            return tag, None, False
        if isinstance(
            expression,
            (
                ast.Constant,
                ast.List,
                ast.Tuple,
                ast.Set,
                ast.Dict,
                ast.Lambda,
                ast.ListComp,
                ast.SetComp,
                ast.DictComp,
                ast.GeneratorExp,
                ast.JoinedStr,
            ),
        ):
            return None, "TypeError", False
        return None, None, True
    tag = _explicit_raise_exception_tag(expression, scope)
    if tag is None:
        return None, None, True
    if expression.keywords:
        return None, "TypeError", False

    def closed_safe_literal(candidate: ast.AST) -> bool:
        return isinstance(candidate, ast.Constant) or (
            isinstance(candidate, (ast.List, ast.Tuple))
            and all(closed_safe_literal(item) for item in candidate.elts)
        )

    literal = tuple(
        argument.value if isinstance(argument, ast.Constant) else ...
        for argument in expression.args
    )
    required_types: tuple[type, ...] | None = {
        "UnicodeDecodeError": (str, bytes, int, int, str),
        "UnicodeEncodeError": (str, str, int, int, str),
        "UnicodeTranslateError": (str, int, int, str),
    }.get(tag)
    if required_types is not None:
        if len(literal) != len(required_types):
            return None, "TypeError", False
        if ... in literal:
            return tag, None, True
        if any(type(value) is not expected for value, expected in zip(
            literal,
            required_types,
            strict=True,
        )):
            return None, "TypeError", False
        index_values = literal[2:4] if tag != "UnicodeTranslateError" else literal[1:3]
        if any(abs(int(value)) > sys.maxsize for value in index_values):
            return None, "OverflowError", False
        return tag, None, False
    allowed = _SAFE_BUILTIN_EXCEPTION_CONSTRUCTOR_ARITIES.get(
        tag,
        frozenset(),
    )
    if len(expression.args) not in allowed:
        return None, "TypeError", False
    if not all(closed_safe_literal(argument) for argument in expression.args):
        return tag, None, True
    return tag, None, False


@dataclass(frozen=True, slots=True)
class _BoundedCallableSummary:
    exception_tag: str | None
    positional_only: tuple[str, ...]
    positional_or_keyword: tuple[str, ...]
    required_positional: frozenset[str]
    keyword_only: tuple[str, ...]
    required_keyword_only: frozenset[str]
    has_varargs: bool
    has_varkw: bool
    proven_normal_only: bool


@dataclass(frozen=True, slots=True)
class _ExpressionOutcomes:
    normal: bool
    raises: bool


@dataclass(frozen=True, slots=True)
class _DeferredGeneratorState:
    expression: ast.GeneratorExp
    identity: int
    remaining: int | None
    supported: bool = True
    outer_iterator_sensitive: bool = False
    outer_iterator_identity: int | None = None
    outer_iterator_version: int = 0


@dataclass(frozen=True, slots=True)
class _DeferredLocalGeneratorFactory:
    marker: str
    definition: ast.FunctionDef
    defaults: tuple[tuple[str, _FlowValue], ...] = ()


@dataclass(frozen=True, slots=True)
class _DeferredLocalGeneratorState:
    factory: _DeferredLocalGeneratorFactory
    identity: int
    creation_call_id: int
    bindings: tuple[tuple[str, _FlowValue], ...] = ()
    supported: bool = True
    exact_full_review: bool = True
    statement_index: int = 0
    frame: tuple[tuple[str, _FlowValue], ...] = ()
    delegate: _FlowValue | None = None
    exhausted: bool = False


@dataclass(frozen=True, slots=True)
class _DeferredLocalGeneratorResume:
    sensitive: bool
    value: _FlowValue
    yielded: bool
    normal: bool
    raises: tuple[tuple[str | None, bool], ...] = ()
    yielded_value: _FlowValue | None = None


@dataclass(frozen=True, slots=True)
class _DeferredGeneratorConsumption:
    blocked: bool
    normal: bool = True
    yielded: bool = False
    raises: tuple[tuple[str | None, bool], ...] = ()
    yielded_value: _FlowValue | None = None
    defaulted: bool = False


_DEFINITION_POINT_MARKER_PREFIX = "__definition_point__:"


def _definition_point_marker(
    definition: ast.FunctionDef | ast.AsyncFunctionDef,
) -> str:
    """Return a process-local identity for one executable definition point."""

    return f"{_DEFINITION_POINT_MARKER_PREFIX}{id(definition):x}"


def _bounded_local_generator_dependencies(
    definition: ast.FunctionDef | ast.AsyncFunctionDef,
    budget: "_AnalysisBudget",
) -> tuple[str, ...] | None:
    """Return simple yield-from dependencies for one bounded generator."""

    if definition in budget.local_generator_dependencies:
        return budget.local_generator_dependencies[definition]
    arguments = definition.args
    if (
        not isinstance(definition, ast.FunctionDef)
        or definition.decorator_list
    ):
        budget.local_generator_dependencies[definition] = None
        return None
    yielded = False
    dependencies: set[str] = set()
    pending: list[ast.AST] = list(definition.body)
    while pending:
        candidate = pending.pop()
        budget.consume()
        if isinstance(candidate, (ast.Yield, ast.YieldFrom)):
            yielded = True
            if (
                isinstance(candidate, ast.YieldFrom)
                and isinstance(candidate.value, ast.Call)
                and isinstance(candidate.value.func, ast.Name)
                and not candidate.value.args
                and not candidate.value.keywords
            ):
                dependencies.add(candidate.value.func.id)
            pending.extend(ast.iter_child_nodes(candidate))
            continue
        if isinstance(
            candidate,
            (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef),
        ):
            continue
        pending.extend(ast.iter_child_nodes(candidate))
    result = tuple(sorted(dependencies)) if yielded else None
    budget.local_generator_dependencies[definition] = result
    return result


def _bind_deferred_local_generator_call(
    node: ast.Call,
    factory: _DeferredLocalGeneratorFactory,
    positional_values: Sequence[_FlowValue],
    keyword_values: Sequence[_FlowValue],
) -> tuple[str, tuple[tuple[str, _FlowValue], ...]]:
    """Bind one local generator call without re-evaluating its arguments."""

    definition = factory.definition
    arguments = definition.args
    if arguments.vararg is not None or arguments.kwarg is not None:
        return "unsupported", ()
    if any(isinstance(argument, ast.Starred) for argument in node.args) or any(
        keyword.arg is None for keyword in node.keywords
    ):
        return "unsupported", ()
    positional_names = tuple(
        argument.arg for argument in (*arguments.posonlyargs, *arguments.args)
    )
    positional_only = frozenset(
        argument.arg for argument in arguments.posonlyargs
    )
    keyword_only = tuple(argument.arg for argument in arguments.kwonlyargs)
    if len(positional_values) > len(positional_names):
        return "invalid", ()
    bound: dict[str, _FlowValue] = dict(
        zip(positional_names, positional_values, strict=False)
    )
    for keyword, value in zip(node.keywords, keyword_values, strict=True):
        name = keyword.arg
        if (
            name is None
            or name in positional_only
            or name in bound
            or name not in {*positional_names, *keyword_only}
        ):
            return "invalid", ()
        bound[name] = value
    defaults = dict(factory.defaults)
    for name in (*positional_names, *keyword_only):
        if name not in bound and name in defaults:
            bound[name] = defaults[name]
    required_positional_count = len(positional_names) - len(arguments.defaults)
    required_positional = positional_names[:required_positional_count]
    required_keyword_only = tuple(
        argument.arg
        for argument, default in zip(
            arguments.kwonlyargs,
            arguments.kw_defaults,
            strict=True,
        )
        if default is None
    )
    if any(name not in bound for name in (*required_positional, *required_keyword_only)):
        return "invalid", ()
    return "valid", tuple(bound.items())


def _direct_literal_iteration_cardinality(node: ast.expr) -> int | None:
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        return len(node.elts)
    if isinstance(node, ast.Dict):
        return len(node.keys)
    if not (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "range"
        and 1 <= len(node.args) <= 3
        and not node.keywords
        and all(
            isinstance(argument, ast.Constant)
            and type(argument.value) is int
            for argument in node.args
        )
    ):
        return None
    arguments = [int(argument.value) for argument in node.args]
    if len(arguments) == 3 and arguments[2] == 0:
        return None
    try:
        return len(range(*arguments))
    except (OverflowError, ValueError):
        return None


def _direct_builtin_tuple_generator(
    node: ast.Call,
    *,
    callee_is_unshadowed_builtin: bool,
) -> ast.GeneratorExp | None:
    """Return the one deliberately supported immediate tuple generator."""

    if not (
        callee_is_unshadowed_builtin
        and isinstance(node.func, ast.Name)
        and node.func.id == "tuple"
        and len(node.args) == 1
        and isinstance(node.args[0], ast.GeneratorExp)
        and not node.keywords
        and not any(
            isinstance(candidate, ast.NamedExpr)
            for candidate in ast.walk(node.args[0])
        )
        and _direct_literal_iteration_cardinality(
            node.args[0].generators[0].iter
        )
        is not None
    ):
        return None
    return node.args[0]


def _bounded_callable_summary(
    definition: ast.FunctionDef | ast.AsyncFunctionDef,
    scope: _ExceptionNameScope,
) -> _BoundedCallableSummary | None:
    if isinstance(definition, ast.AsyncFunctionDef) or definition.decorator_list:
        return None
    if any(
        isinstance(node, (ast.Yield, ast.YieldFrom))
        for node in ast.walk(definition)
    ):
        return None
    positional_only = tuple(item.arg for item in definition.args.posonlyargs)
    positional_or_keyword = tuple(item.arg for item in definition.args.args)
    positional = positional_only + positional_or_keyword
    required_count = len(positional) - len(definition.args.defaults)
    required = frozenset(positional[:required_count])
    keyword_only = tuple(item.arg for item in definition.args.kwonlyargs)
    required_keyword_only = frozenset(
        item.arg
        for item, default in zip(
            definition.args.kwonlyargs,
            definition.args.kw_defaults,
            strict=True,
        )
        if default is None
    )

    def exits(
        statements: Sequence[ast.stmt],
    ) -> tuple[bool, frozenset[str], bool, bool]:
        normal = True
        tags: set[str] = set()
        nonraise_terminal = False
        supported = True
        for statement in statements:
            if not normal:
                break
            if isinstance(statement, ast.Raise):
                tag = (
                    _explicit_raise_exception_tag(statement.exc, scope)
                    if statement.cause is None
                    and _exception_expression_is_proven_nonthrowing(
                        statement.exc,
                        scope,
                        lambda _name: False,
                    )
                    else None
                )
                if tag is None:
                    supported = False
                else:
                    tags.add(tag)
                normal = False
                continue
            if isinstance(statement, ast.Return):
                normal = False
                nonraise_terminal = True
                continue
            if isinstance(statement, ast.If):
                body = exits(statement.body)
                alternate = exits(statement.orelse)
                normal = body[0] or alternate[0]
                tags.update(body[1])
                tags.update(alternate[1])
                nonraise_terminal |= body[2] or alternate[2]
                supported &= body[3] and alternate[3]
                continue
            if isinstance(
                statement,
                (
                    ast.Pass,
                    ast.Expr,
                    ast.Assign,
                    ast.AnnAssign,
                    ast.AugAssign,
                    ast.Import,
                    ast.ImportFrom,
                    ast.Delete,
                ),
            ):
                continue
            supported = False
        return normal, frozenset(tags), nonraise_terminal, supported

    normal, tags, nonraise_terminal, supported = exits(definition.body)
    tag = (
        next(iter(tags))
        if supported and not normal and not nonraise_terminal and len(tags) == 1
        else None
    )

    def safe_value(expression: ast.AST, bound: set[str]) -> bool:
        if isinstance(expression, ast.Name):
            return expression.id in bound
        if isinstance(expression, ast.Lambda):
            return not expression.args.defaults and not any(
                item is not None for item in expression.args.kw_defaults
            )
        return False

    def proven_normal_only() -> bool:
        bound = {
            *positional_only,
            *positional_or_keyword,
            *keyword_only,
        }
        if definition.args.vararg is not None:
            bound.add(definition.args.vararg.arg)
        if definition.args.kwarg is not None:
            bound.add(definition.args.kwarg.arg)
        for statement in definition.body:
            if isinstance(statement, ast.Pass):
                continue
            if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if (
                    statement.decorator_list
                    or statement.args.defaults
                    or any(
                        item is not None
                        for item in statement.args.kw_defaults
                    )
                ):
                    return False
                bound.add(statement.name)
                continue
            if isinstance(statement, ast.Return):
                return statement.value is not None and safe_value(
                    statement.value,
                    bound,
                )
            return False
        return False

    return _BoundedCallableSummary(
        tag,
        positional_only,
        positional_or_keyword,
        required,
        keyword_only,
        required_keyword_only,
        definition.args.vararg is not None,
        definition.args.kwarg is not None,
        proven_normal_only(),
    )


def _bounded_call_shape(
    node: ast.Call,
    summary: _BoundedCallableSummary,
) -> str:
    if any(isinstance(argument, ast.Starred) for argument in node.args) or any(
        keyword.arg is None for keyword in node.keywords
    ):
        return "unknown"
    positional = summary.positional_only + summary.positional_or_keyword
    if len(node.args) > len(positional) and not summary.has_varargs:
        return "invalid"
    bound = set(positional[: min(len(node.args), len(positional))])
    positional_only = set(summary.positional_only)
    keyword_names = set(summary.positional_or_keyword) | set(summary.keyword_only)
    for keyword in node.keywords:
        name = keyword.arg
        if name is None:
            return "unknown"
        if name in positional_only:
            if not summary.has_varkw:
                return "invalid"
            continue
        if name in keyword_names:
            if name in bound:
                return "invalid"
            bound.add(name)
            continue
        if not summary.has_varkw:
            return "invalid"
    if not summary.required_positional.issubset(bound):
        return "invalid"
    if not summary.required_keyword_only.issubset(bound):
        return "invalid"
    return "valid"


@dataclass(frozen=True, slots=True)
class _LexicalBindingScope:
    local_names: frozenset[str] = frozenset()
    global_names: frozenset[str] = frozenset()
    nonlocal_names: frozenset[str] = frozenset()
    parameter_names: frozenset[str] = frozenset()


@dataclass(frozen=True, slots=True)
class _ExceptionNameScope:
    shadowed_names: frozenset[str] = frozenset()
    enclosing_names: frozenset[str] = frozenset()
    entry_bound_names: frozenset[str] = frozenset()


@dataclass(frozen=True, slots=True)
class _ModuleExceptionProvenance:
    module_bound_names: frozenset[str]
    enclosing_names_by_node: Mapping[int, frozenset[str]]


class _ExceptionBindingVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.bound_names: set[str] = set()
        self.global_names: set[str] = set()
        self.nonlocal_names: set[str] = set()

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, (ast.Store, ast.Del)):
            self.bound_names.add(node.id)

    def visit_Global(self, node: ast.Global) -> None:
        self.global_names.update(node.names)

    def visit_Nonlocal(self, node: ast.Nonlocal) -> None:
        self.nonlocal_names.update(node.names)

    def visit_Import(self, node: ast.Import) -> None:
        self.bound_names.update(
            imported.asname or imported.name.split(".", 1)[0]
            for imported in node.names
        )

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        for imported in node.names:
            if imported.name == "*":
                self.bound_names.update(_BUILTIN_EXCEPTION_ANCESTORS)
            else:
                self.bound_names.add(imported.asname or imported.name)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        if node.name is not None:
            self.bound_names.add(node.name)
        if node.type is not None:
            self.visit(node.type)
        for statement in node.body:
            self.visit(statement)

    def visit_Match(self, node: ast.Match) -> None:
        self.visit(node.subject)
        for case in node.cases:
            self.bound_names.update(_python_bound_names(case.pattern))
            if case.guard is not None:
                self.visit(case.guard)
            for statement in case.body:
                self.visit(statement)

    def _visit_comprehension(
        self,
        generators: Sequence[ast.comprehension],
        expressions: Sequence[ast.AST],
    ) -> None:
        for generator in generators:
            self.visit(generator.iter)
            for condition in generator.ifs:
                self.visit(condition)
        for expression in expressions:
            self.visit(expression)

    def visit_ListComp(self, node: ast.ListComp) -> None:
        self._visit_comprehension(node.generators, (node.elt,))

    def visit_SetComp(self, node: ast.SetComp) -> None:
        self._visit_comprehension(node.generators, (node.elt,))

    def visit_GeneratorExp(self, node: ast.GeneratorExp) -> None:
        self._visit_comprehension(node.generators, (node.elt,))

    def visit_DictComp(self, node: ast.DictComp) -> None:
        self._visit_comprehension(node.generators, (node.key, node.value))

    def _visit_nested_function_metadata(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
    ) -> None:
        self.bound_names.add(node.name)
        for expression in (*node.decorator_list, *node.args.defaults):
            self.visit(expression)
        for expression in node.args.kw_defaults:
            if expression is not None:
                self.visit(expression)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_nested_function_metadata(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_nested_function_metadata(node)

    def visit_Lambda(self, node: ast.Lambda) -> None:
        for expression in (*node.args.defaults, *node.args.kw_defaults):
            if expression is not None:
                self.visit(expression)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.bound_names.add(node.name)
        for expression in (*node.decorator_list, *node.bases):
            self.visit(expression)
        for keyword in node.keywords:
            self.visit(keyword.value)


def _lexical_binding_scope(
    node: ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda | None,
) -> _LexicalBindingScope:
    if node is None:
        return _LexicalBindingScope()
    visitor = _ExceptionBindingVisitor()
    parameters = {
        argument.arg
        for argument in (
            *node.args.posonlyargs,
            *node.args.args,
            *node.args.kwonlyargs,
        )
    }
    if node.args.vararg is not None:
        parameters.add(node.args.vararg.arg)
    if node.args.kwarg is not None:
        parameters.add(node.args.kwarg.arg)
    visitor.bound_names.update(parameters)
    if isinstance(node, ast.Lambda):
        visitor.visit(node.body)
    else:
        for statement in node.body:
            visitor.visit(statement)
    return _LexicalBindingScope(
        frozenset(
            visitor.bound_names
            - visitor.global_names
            - visitor.nonlocal_names
        ),
        frozenset(visitor.global_names),
        frozenset(visitor.nonlocal_names),
        frozenset(parameters),
    )


def _derived_enclosing_binding_markers(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    definitions: Iterable[ast.FunctionDef | ast.AsyncFunctionDef],
) -> frozenset[str]:
    """Recover the bounded enclosing binding state from supplied AST identities."""

    def scan(
        statements: Sequence[ast.stmt],
        active: set[str],
    ) -> set[str] | None:
        for statement in statements:
            if statement is node:
                return set(active)
            if any(candidate is node for candidate in ast.walk(statement)):
                nested_bodies: list[Sequence[ast.stmt]] = []
                if isinstance(statement, (ast.If, ast.For, ast.AsyncFor, ast.While)):
                    nested_bodies.extend((statement.body, statement.orelse))
                elif isinstance(statement, (ast.With, ast.AsyncWith)):
                    nested_bodies.append(statement.body)
                elif isinstance(statement, ast.Try):
                    nested_bodies.extend(
                        (statement.body, statement.orelse, statement.finalbody)
                    )
                    nested_bodies.extend(handler.body for handler in statement.handlers)
                for body in nested_bodies:
                    found = scan(body, set(active))
                    if found is not None:
                        return found
            assigned: tuple[ast.expr, ast.expr] | None = None
            if isinstance(statement, ast.Assign) and len(statement.targets) == 1:
                assigned = (statement.targets[0], statement.value)
            elif isinstance(statement, ast.AnnAssign) and statement.value is not None:
                assigned = (statement.target, statement.value)
            if assigned is not None and isinstance(assigned[0], ast.Name):
                name = assigned[0].id
                active.add(f"__definite__:{name}")
                if (
                    isinstance(assigned[1], ast.Name)
                    and assigned[1].id in _BUILTIN_EXCEPTION_CANONICAL_NAMES
                ):
                    active.add(
                        "__builtin_binding__:"
                        f"{name}:{_BUILTIN_EXCEPTION_CANONICAL_NAMES[assigned[1].id]}"
                    )
        return None

    parents = [
        candidate
        for candidate in definitions
        if candidate is not node
        and any(descendant is node for descendant in ast.walk(candidate))
    ]
    if not parents:
        return frozenset()
    parent = min(parents, key=lambda candidate: sum(1 for _ in ast.walk(candidate)))
    lexical = _lexical_binding_scope(parent)
    return frozenset(
        scan(parent.body, set(lexical.local_names))
        or set(lexical.local_names)
    )


def _exception_name_scope(
    node: ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda | None,
    module_bound_names: Iterable[str] = (),
    enclosing_names: Iterable[str] = (),
) -> _ExceptionNameScope:
    relevant_module_names = set(module_bound_names) & set(
        _BUILTIN_EXCEPTION_ANCESTORS
    )
    relevant_enclosing_names = set(enclosing_names) & set(
        _BUILTIN_EXCEPTION_ANCESTORS
    )
    if node is None:
        return _ExceptionNameScope(
            frozenset(relevant_module_names | relevant_enclosing_names),
            frozenset(relevant_enclosing_names),
        )
    visitor = _ExceptionBindingVisitor()
    parameters = (
        *node.args.posonlyargs,
        *node.args.args,
        *node.args.kwonlyargs,
    )
    for parameter in parameters:
        visitor.bound_names.add(parameter.arg)
    if node.args.vararg is not None:
        visitor.bound_names.add(node.args.vararg.arg)
    if node.args.kwarg is not None:
        visitor.bound_names.add(node.args.kwarg.arg)
    try:
        if isinstance(node, ast.Lambda):
            visitor.visit(node.body)
        else:
            for statement in node.body:
                visitor.visit(statement)
    except RecursionError:
        return _ExceptionNameScope(
            frozenset(_BUILTIN_EXCEPTION_ANCESTORS),
            frozenset(_BUILTIN_EXCEPTION_ANCESTORS),
            frozenset(parameter.arg for parameter in parameters),
        )
    local_names = (
        visitor.bound_names - visitor.global_names - visitor.nonlocal_names
    ) & set(_BUILTIN_EXCEPTION_ANCESTORS)
    nonlocal_names = visitor.nonlocal_names & set(
        _BUILTIN_EXCEPTION_ANCESTORS
    )
    global_names = visitor.global_names & set(_BUILTIN_EXCEPTION_ANCESTORS)
    shadowed = (
        set(local_names)
        | set(nonlocal_names)
        | set(global_names)
        | relevant_module_names
    )
    shadowed.update(
        name
        for name in relevant_enclosing_names
        if name not in visitor.global_names
    )
    nested_enclosing = (
        set(local_names)
        | set(nonlocal_names)
        | set(global_names)
        | relevant_enclosing_names
    )
    return _ExceptionNameScope(
        frozenset(shadowed),
        frozenset(nested_enclosing),
        frozenset(
            relevant_module_names
            | relevant_enclosing_names
            | nonlocal_names
            | global_names
        )
        | frozenset(
            parameter.arg
            for parameter in parameters
        )
        | (
            frozenset({node.args.vararg.arg})
            if node.args.vararg is not None
            else frozenset()
        )
        | (
            frozenset({node.args.kwarg.arg})
            if node.args.kwarg is not None
            else frozenset()
        ),
    )


def _module_exception_provenance(
    tree: ast.Module,
) -> _ModuleExceptionProvenance:
    module_visitor = _ExceptionBindingVisitor()
    try:
        for statement in tree.body:
            module_visitor.visit(statement)
        module_bound_names = frozenset(module_visitor.bound_names)
    except RecursionError:
        module_bound_names = frozenset(_BUILTIN_EXCEPTION_ANCESTORS)

    enclosing_names_by_node: dict[int, frozenset[str]] = {}

    def definition_time_expressions(
        node: ast.FunctionDef | ast.AsyncFunctionDef,
    ) -> Iterable[ast.AST]:
        yield from node.decorator_list
        yield from node.args.defaults
        yield from (
            expression
            for expression in node.args.kw_defaults
            if expression is not None
        )
        yield from (
            argument.annotation
            for argument in (
                *node.args.posonlyargs,
                *node.args.args,
                *node.args.kwonlyargs,
            )
            if argument.annotation is not None
        )
        if node.args.vararg is not None and node.args.vararg.annotation is not None:
            yield node.args.vararg.annotation
        if node.args.kwarg is not None and node.args.kwarg.annotation is not None:
            yield node.args.kwarg.annotation
        if node.returns is not None:
            yield node.returns

    def visit(candidate: ast.AST, enclosing_names: frozenset[str]) -> None:
        if isinstance(candidate, (ast.FunctionDef, ast.AsyncFunctionDef)):
            enclosing_names_by_node[id(candidate)] = enclosing_names
            for expression in definition_time_expressions(candidate):
                visit(expression, enclosing_names)
            lexical = _lexical_binding_scope(candidate)
            nested = frozenset(
                set(enclosing_names)
                | set(lexical.local_names)
                | set(lexical.nonlocal_names)
            )
            active_nested = set(nested)
            for statement in candidate.body:
                visit(statement, frozenset(active_nested))
                assigned: tuple[ast.expr, ast.expr] | None = None
                if (
                    isinstance(statement, ast.Assign)
                    and len(statement.targets) == 1
                ):
                    assigned = (statement.targets[0], statement.value)
                elif (
                    isinstance(statement, ast.AnnAssign)
                    and statement.value is not None
                ):
                    assigned = (statement.target, statement.value)
                if assigned is not None and isinstance(assigned[0], ast.Name):
                    name = assigned[0].id
                    active_nested.add(f"__definite__:{name}")
                    if (
                        isinstance(assigned[1], ast.Name)
                        and assigned[1].id in _BUILTIN_EXCEPTION_CANONICAL_NAMES
                    ):
                        active_nested.add(
                            "__builtin_binding__:"
                            f"{name}:{_BUILTIN_EXCEPTION_CANONICAL_NAMES[assigned[1].id]}"
                        )
            return
        if isinstance(candidate, ast.Lambda):
            enclosing_names_by_node[id(candidate)] = enclosing_names
            for expression in (
                *candidate.args.defaults,
                *(
                    item
                    for item in candidate.args.kw_defaults
                    if item is not None
                ),
            ):
                visit(expression, enclosing_names)
            lexical = _lexical_binding_scope(candidate)
            nested = frozenset(
                set(enclosing_names)
                | set(lexical.local_names)
                | set(lexical.nonlocal_names)
            )
            visit(candidate.body, nested)
            return
        if isinstance(candidate, ast.ClassDef):
            for expression in (*candidate.decorator_list, *candidate.bases):
                visit(expression, enclosing_names)
            for keyword in candidate.keywords:
                visit(keyword.value, enclosing_names)
            for statement in candidate.body:
                visit(statement, enclosing_names)
            return
        for child in ast.iter_child_nodes(candidate):
            visit(child, enclosing_names)

    try:
        for statement in tree.body:
            visit(statement, frozenset())
    except RecursionError:
        for candidate in ast.walk(tree):
            if isinstance(
                candidate,
                (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda),
            ):
                enclosing_names_by_node[id(candidate)] = frozenset(
                    _BUILTIN_EXCEPTION_ANCESTORS
                )
    return _ModuleExceptionProvenance(
        module_bound_names,
        MappingProxyType(dict(enclosing_names_by_node)),
    )


def _proven_builtin_exception_name(
    expression: ast.AST | None,
    scope: _ExceptionNameScope,
) -> str | None:
    if (
        isinstance(expression, ast.Name)
        and expression.id in _BUILTIN_EXCEPTION_CANONICAL_NAMES
        and expression.id not in scope.shadowed_names
    ):
        return _BUILTIN_EXCEPTION_CANONICAL_NAMES[expression.id]
    return None


def _explicit_raise_exception_tag(
    exception: ast.expr | None,
    scope: _ExceptionNameScope = _ExceptionNameScope(),
) -> str | None:
    candidate: ast.AST | None = exception
    if isinstance(candidate, ast.Call):
        candidate = candidate.func
    return _proven_builtin_exception_name(candidate, scope)


def _exception_handler_validation(
    handler: ast.expr | None,
    scope: _ExceptionNameScope,
) -> str:
    if handler is None:
        return "valid"
    if isinstance(handler, ast.Tuple):
        validations = [
            _exception_handler_validation(element, scope)
            for element in handler.elts
        ]
        if "invalid" in validations:
            return "invalid"
        return "unknown" if "unknown" in validations else "valid"
    if _proven_builtin_exception_name(handler, scope) is not None:
        return "valid"
    if isinstance(handler, ast.NamedExpr):
        return _exception_handler_validation(handler.value, scope)
    if (
        isinstance(handler, ast.Call)
        and _explicit_raise_exception_tag(handler, scope) is not None
    ):
        return "invalid"
    if isinstance(
        handler,
        (
            ast.Constant,
            ast.List,
            ast.Set,
            ast.Dict,
            ast.Lambda,
            ast.ListComp,
            ast.SetComp,
            ast.DictComp,
            ast.GeneratorExp,
            ast.JoinedStr,
        ),
    ):
        return "invalid"
    return "unknown"


def _exception_expression_is_proven_nonthrowing(
    expression: ast.AST | None,
    scope: _ExceptionNameScope,
    name_is_bound: Callable[[str], bool],
) -> bool:
    if expression is None or isinstance(expression, ast.Constant):
        return True
    if isinstance(expression, ast.Name):
        return (
            _proven_builtin_exception_name(expression, scope) is not None
            or name_is_bound(expression.id)
        )
    if isinstance(expression, (ast.List, ast.Tuple)):
        return all(
            _exception_expression_is_proven_nonthrowing(item, scope, name_is_bound)
            for item in expression.elts
        )
    if isinstance(expression, (ast.Set, ast.Dict)):
        # Hashing set members/dict keys and validating ``**`` operands are
        # runtime operations even when every child expression is a literal.
        return False
    if isinstance(expression, ast.Lambda):
        return all(
            _exception_expression_is_proven_nonthrowing(
                default, scope, name_is_bound
            )
            for default in (*expression.args.defaults, *expression.args.kw_defaults)
            if default is not None
        )
    if isinstance(expression, ast.GeneratorExp):
        # Creation evaluates only the outermost iterable.
        return _exception_expression_is_proven_nonthrowing(
            expression.generators[0].iter,
            scope,
            name_is_bound,
        )
    if isinstance(expression, (ast.ListComp, ast.SetComp, ast.DictComp)):
        return False
    if isinstance(expression, ast.JoinedStr):
        return all(isinstance(item, ast.Constant) for item in expression.values)
    if isinstance(expression, ast.NamedExpr):
        return _exception_expression_is_proven_nonthrowing(
            expression.value, scope, name_is_bound
        )
    if isinstance(expression, ast.Call):
        success, error, unknown = _builtin_exception_constructor_outcome(
            expression,
            scope,
        )
        return bool(success is not None and error is None and not unknown)
    if isinstance(expression, ast.BoolOp) and expression.values:
        first = expression.values[0]
        if isinstance(first, ast.Constant):
            if isinstance(expression.op, ast.And) and not bool(first.value):
                return _exception_expression_is_proven_nonthrowing(
                    first, scope, name_is_bound
                )
            if isinstance(expression.op, ast.Or) and bool(first.value):
                return _exception_expression_is_proven_nonthrowing(
                    first, scope, name_is_bound
                )
    if isinstance(expression, ast.IfExp) and isinstance(
        expression.test,
        ast.Constant,
    ):
        selected = expression.body if bool(expression.test.value) else expression.orelse
        return _exception_expression_is_proven_nonthrowing(
            selected,
            scope,
            name_is_bound,
        )
    return False


def _raise_cause_validation(
    cause: ast.expr | None,
    scope: _ExceptionNameScope,
) -> str:
    if cause is None or (
        isinstance(cause, ast.Constant) and cause.value is None
    ):
        return "valid"
    if _proven_builtin_exception_name(cause, scope) is not None:
        return "valid"
    if (
        isinstance(cause, ast.Call)
        and _explicit_raise_exception_tag(cause, scope) is not None
    ):
        return "valid"
    if isinstance(
        cause,
        (
            ast.Constant,
            ast.List,
            ast.Set,
            ast.Dict,
            ast.Lambda,
            ast.ListComp,
            ast.SetComp,
            ast.DictComp,
            ast.GeneratorExp,
            ast.JoinedStr,
        ),
    ):
        return "invalid"
    return "unknown"


def _explicit_exception_handler_match(
    exception_tag: str | None,
    handler: ast.expr | None,
    scope: _ExceptionNameScope = _ExceptionNameScope(),
) -> str:
    if handler is None:
        return "match"
    if isinstance(handler, ast.Tuple):
        outcomes = {
            _explicit_exception_handler_match(exception_tag, element, scope)
            for element in handler.elts
        }
        if "match" in outcomes:
            return "match"
        return "unknown" if "unknown" in outcomes else "nonmatch"
    if exception_tag is None:
        return "unknown"
    handler_name = _proven_builtin_exception_name(handler, scope)
    if handler_name is None:
        return "unknown"
    if (
        handler_name == exception_tag
        or handler_name in _BUILTIN_EXCEPTION_ANCESTORS[exception_tag]
    ):
        return "match"
    return "nonmatch"


def _excluded_handler_proves_nonmatch(
    handler_name: str,
    excluded_handlers: Iterable[str],
) -> bool:
    return any(
        excluded == handler_name
        or excluded in _BUILTIN_EXCEPTION_ANCESTORS[handler_name]
        for excluded in excluded_handlers
    )


def _raise_expression_contains_fallible_evaluation(
    exception: ast.expr | None,
    cause: ast.expr | None,
    scope: _ExceptionNameScope,
) -> bool:
    def contains(node: ast.AST | None) -> bool:
        if node is None:
            return False
        pending = [node]
        while pending:
            candidate = pending.pop()
            if isinstance(candidate, (ast.Call, ast.Await, ast.Yield, ast.YieldFrom)):
                return True
            if isinstance(
                candidate,
                (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef),
            ) and candidate is not node:
                continue
            pending.extend(ast.iter_child_nodes(candidate))
        return False

    if contains(cause):
        return True
    if isinstance(exception, ast.Call) and _explicit_raise_exception_tag(
        exception,
        scope,
    ) is not None:
        return any(contains(argument) for argument in exception.args) or any(
            contains(keyword.value) for keyword in exception.keywords
        )
    return False


@dataclass(slots=True)
class _PreclassifierSuccessors:
    normal: list[tuple[dict[str, str], set[str]]] = field(default_factory=list)
    raises: list[_PreclassifierExceptionalState] = field(default_factory=list)
    returns: list[tuple[dict[str, str], set[str]]] = field(default_factory=list)
    breaks: list[tuple[dict[str, str], set[str]]] = field(default_factory=list)
    continues: list[tuple[dict[str, str], set[str]]] = field(default_factory=list)


class _SensitivePreclassifier:
    """Independent conservative census of potentially protected call sites."""

    def __init__(
        self,
        aliases: Mapping[str, str],
        budget: _AnalysisBudget,
        helper_returns: Mapping[
            str,
            tuple[str | None, bool],
        ] | None = None,
        helper_raises: Mapping[str, str] | None = None,
        exception_scope: _ExceptionNameScope | None = None,
        module_bound_names: Iterable[str] = (),
        helper_summaries: Mapping[str, _BoundedCallableSummary] | None = None,
        lexical_scope: _LexicalBindingScope | None = None,
        enclosing_bound_names: Iterable[str] = (),
    ) -> None:
        self.bindings: dict[str, str] = dict(aliases)
        self.helper_returns = dict(helper_returns or {})
        self.helper_raises = dict(helper_raises or {})
        self.helper_summaries = dict(helper_summaries or {})
        for name in (
            self.helper_returns.keys()
            | self.helper_raises.keys()
            | self.helper_summaries.keys()
        ):
            self.bindings.setdefault(name, name)
        self.tainted = {
            name
            for name, qualified in aliases.items()
            if self._qualified_call_is_sensitive(qualified)
        }
        self.calls: set[int] = set()
        self.return_values: list[tuple[str | None, bool]] = []
        self.deferred_generators: dict[str, _DeferredGeneratorState] = {}
        self.budget = budget
        self._throw_states: list[_PreclassifierExceptionalState] | None = None
        self._active_exception_tag: str | None = None
        self.exception_scope = exception_scope or _ExceptionNameScope()
        self.module_bound_names = frozenset(module_bound_names)
        self.lexical_scope = lexical_scope or _LexicalBindingScope()
        self.enclosing_bound_names = frozenset(enclosing_bound_names)
        for name in self.lexical_scope.local_names:
            if name in self.lexical_scope.parameter_names:
                self.bindings.setdefault(name, "__bound_unknown__")
            else:
                self.bindings[name] = "__unbound__"
            self.tainted.discard(name)
        for name in self.lexical_scope.nonlocal_names:
            builtin_marker = next(
                (
                    marker.rsplit(":", 1)[1]
                    for marker in self.enclosing_bound_names
                    if marker.startswith(
                        f"__builtin_binding__:{name}:"
                    )
                ),
                None,
            )
            if builtin_marker is not None:
                self.bindings[name] = (
                    f"__builtin_exception__:{builtin_marker}"
                )
            elif f"__definite__:{name}" in self.enclosing_bound_names:
                self.bindings[name] = "__bound_unknown__"
            else:
                self.bindings[name] = (
                    "__maybe_unbound__"
                    if name in self.enclosing_bound_names
                    else "__unbound__"
                )
            self.tainted.discard(name)
        for name in self.lexical_scope.global_names:
            if name not in self.module_bound_names and name not in self.bindings:
                self.bindings[name] = "__unbound__"
        for name in self.exception_scope.entry_bound_names:
            self.bindings.setdefault(name, "__bound_unknown__")

    def _exception_name(self, expression: ast.AST | None) -> str | None:
        proven = _proven_builtin_exception_name(expression, self.exception_scope)
        if proven is not None:
            return proven
        if not isinstance(expression, ast.Name):
            return None
        qualified = self.bindings.get(expression.id, "")
        prefix = "__builtin_exception__:"
        return qualified[len(prefix):] if qualified.startswith(prefix) else None

    def _name_is_bound(self, name: str) -> bool:
        supplied = self.bindings.get(name)
        return supplied is not None and not supplied.startswith(
            ("__unbound__", "__maybe_unbound__")
        )

    def _lookup_error_tag(self, name: str) -> str:
        return (
            "UnboundLocalError"
            if name in self.lexical_scope.local_names
            else "NameError"
        )

    def _expression_is_proven_nonthrowing(
        self,
        expression: ast.AST | None,
    ) -> bool:
        return _exception_expression_is_proven_nonthrowing(
            expression,
            self.exception_scope,
            self._name_is_bound,
        )

    def _handler_validation(self, handler: ast.expr | None) -> str:
        validation = _exception_handler_validation(handler, self.exception_scope)
        if validation != "unknown" or not isinstance(handler, ast.Name):
            return validation
        qualified = self.bindings.get(handler.id)
        if qualified is None:
            return "unknown"
        if qualified.startswith("__builtin_exception__:"):
            return "valid"
        if qualified.startswith((
            "__exception_invalid__",
            "__exception_instance__:",
        )):
            return "invalid"
        return "unknown"

    def _handler_match(
        self,
        exception_tag: str | None,
        handler: ast.expr | None,
    ) -> str:
        if handler is None:
            return "match"
        if isinstance(handler, ast.Tuple):
            outcomes = {
                self._handler_match(exception_tag, element)
                for element in handler.elts
            }
            if "match" in outcomes:
                return "match"
            return "unknown" if "unknown" in outcomes else "nonmatch"
        handler_name = self._exception_name(handler)
        if exception_tag is None or handler_name is None:
            return "unknown"
        if (
            handler_name == exception_tag
            or handler_name in _BUILTIN_EXCEPTION_ANCESTORS[exception_tag]
        ):
            return "match"
        return "nonmatch"

    def _handler_exception_names(
        self,
        handler: ast.expr | None,
    ) -> frozenset[str]:
        if handler is None:
            return frozenset({"BaseException"})
        if isinstance(handler, ast.Tuple):
            return frozenset().union(
                *(self._handler_exception_names(element) for element in handler.elts)
            )
        name = self._exception_name(handler)
        return frozenset() if name is None else frozenset({name})

    def _implicit_handler_match(
        self,
        exceptional: _PreclassifierExceptionalState,
        handler: ast.expr | None,
    ) -> str:
        if handler is None:
            return "match"
        names = self._handler_exception_names(handler)
        if not names:
            return "unknown"
        if "BaseException" in names:
            return "match"
        if all(
            _excluded_handler_proves_nonmatch(
                name,
                exceptional.excluded_handlers,
            )
            for name in names
        ):
            return "nonmatch"
        return "unknown"

    def _suppress_target_outcomes(
        self,
        exceptional: _PreclassifierExceptionalState,
        target: ast.expr,
    ) -> frozenset[str]:
        if isinstance(target, ast.Tuple):
            outcomes = {"nonmatch"}
            for element in target.elts:
                advanced = set(outcomes) - {"nonmatch"}
                if "nonmatch" in outcomes:
                    advanced.update(
                        self._suppress_target_outcomes(exceptional, element)
                    )
                outcomes = advanced
            return frozenset(outcomes)
        validation = self._handler_validation(target)
        if validation == "invalid":
            return frozenset({"invalid"})
        match = (
            self._handler_match(exceptional.exception_tag, target)
            if exceptional.explicit
            else self._implicit_handler_match(exceptional, target)
        )
        if match != "unknown":
            return frozenset({match})
        outcomes = {"match", "nonmatch"}
        if validation == "unknown":
            outcomes.add("invalid")
        return frozenset(outcomes)

    def _suppress_outcomes(
        self,
        exceptional: _PreclassifierExceptionalState,
        arguments: Sequence[ast.expr],
    ) -> frozenset[str]:
        outcomes = {"nonmatch"}
        for argument in arguments:
            advanced = set(outcomes) - {"nonmatch"}
            if "nonmatch" in outcomes:
                advanced.update(
                    self._suppress_target_outcomes(exceptional, argument)
                )
            outcomes = advanced
        return frozenset(outcomes)

    def _cause_validation(self, cause: ast.expr | None) -> str:
        validation = _raise_cause_validation(cause, self.exception_scope)
        if validation != "unknown" or not isinstance(cause, ast.Name):
            return validation
        qualified = self.bindings.get(cause.id)
        if qualified is None:
            return "unknown"
        if qualified.startswith((
            "__builtin_exception__:",
            "__exception_instance__:",
        )):
            return "valid"
        if qualified.startswith("__exception_invalid__"):
            return "invalid"
        return "unknown"

    def _record_throw_state(
        self,
        exception_tag: str | None = None,
        explicit: bool = False,
    ) -> None:
        if self._throw_states is not None:
            self._throw_states.append(
                _PreclassifierExceptionalState(
                    self._snapshot(),
                    exception_tag,
                    explicit,
                )
            )

    def _must_raise_tag(self, node: ast.AST | None) -> str | None:
        if not isinstance(node, ast.Call):
            return None
        if (
            isinstance(node.func, ast.Name)
            and node.func.id == "next"
            and (
                len(node.args) not in {1, 2}
                or bool(node.keywords)
            )
        ):
            return "TypeError"
        if (
            isinstance(node.func, ast.Name)
            and node.func.id == "next"
            and node.args
            and len(node.args) == 1
            and isinstance(node.args[0], ast.Name)
        ):
            marker = self.bindings.get(node.args[0].id)
            deferred = self.deferred_generators.get(marker or "")
            if deferred is not None and deferred.remaining == 0:
                return "StopIteration"
        qualified = self.bindings.get(node.func.id) if isinstance(node.func, ast.Name) else None
        summary = self.helper_summaries.get(qualified or "")
        if summary is not None:
            shape = _bounded_call_shape(node, summary)
            if shape == "invalid":
                return "TypeError"
            if shape == "valid":
                return summary.exception_tag
        return self.helper_raises.get(qualified or "")

    def _expression_outcomes(self, node: ast.AST | None) -> _ExpressionOutcomes:
        """Return the bounded normal/exceptional continuations of an expression."""

        if node is None or isinstance(node, ast.Constant):
            return _ExpressionOutcomes(True, False)
        if isinstance(node, ast.Name):
            qualified = self.bindings.get(node.id)
            if qualified == "__unbound__":
                return _ExpressionOutcomes(False, True)
            if qualified is not None and qualified.startswith(
                "__maybe_unbound__"
            ):
                return _ExpressionOutcomes(True, True)
            return _ExpressionOutcomes(True, qualified is None)
        if isinstance(node, ast.Lambda):
            return self._ordered_expression_outcomes(
                tuple(node.args.defaults)
                + tuple(item for item in node.args.kw_defaults if item is not None)
            )
        if isinstance(node, ast.GeneratorExp):
            return self._expression_outcomes(node.generators[0].iter)
        if isinstance(node, ast.BoolOp):
            normal = True
            raises = False
            short_circuit_normal = False
            for index, item in enumerate(node.values):
                supplied = self._expression_outcomes(item)
                raises |= normal and supplied.raises
                normal &= supplied.normal
                if not normal:
                    break
                if isinstance(item, ast.Constant):
                    truth = bool(item.value)
                    if (isinstance(node.op, ast.And) and not truth) or (
                        isinstance(node.op, ast.Or) and truth
                    ):
                        break
                elif index < len(node.values) - 1:
                    # The unknown truth branch can short-circuit normally.
                    short_circuit_normal = True
            return _ExpressionOutcomes(normal or short_circuit_normal, raises)
        if isinstance(node, ast.IfExp):
            test = self._expression_outcomes(node.test)
            if not test.normal:
                return test
            if isinstance(node.test, ast.Constant):
                branch = node.body if bool(node.test.value) else node.orelse
                selected = self._expression_outcomes(branch)
                return _ExpressionOutcomes(
                    selected.normal,
                    test.raises or selected.raises,
                )
            first = self._expression_outcomes(node.body)
            second = self._expression_outcomes(node.orelse)
            return _ExpressionOutcomes(
                first.normal or second.normal,
                test.raises or first.raises or second.raises,
            )
        if isinstance(node, ast.Call):
            prefix = self._ordered_expression_outcomes((
                node.func,
                *node.args,
                *(keyword.value for keyword in node.keywords),
            ))
            if not prefix.normal:
                return prefix
            constructor_success, constructor_error, constructor_unknown = (
                _builtin_exception_constructor_outcome(
                    node,
                    self.exception_scope,
                )
            )
            if constructor_error is not None and constructor_success is None:
                return _ExpressionOutcomes(False, True)
            if constructor_success is not None and not constructor_unknown:
                return _ExpressionOutcomes(True, prefix.raises)
            exact = self._must_raise_tag(node)
            if exact is not None:
                return _ExpressionOutcomes(False, True)
            return _ExpressionOutcomes(True, True)
        if isinstance(node, ast.NamedExpr):
            return self._expression_outcomes(node.value)
        if isinstance(node, (ast.Await, ast.Yield, ast.YieldFrom)):
            supplied = self._expression_outcomes(node.value)
            return _ExpressionOutcomes(supplied.normal, True)
        if isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp)):
            first = self._expression_outcomes(node.generators[0].iter)
            if not first.normal:
                return first
            bound = self._literal_iteration_bound(node.generators[0].iter)
            if bound == 0:
                return first
            first_generator = node.generators[0]
            if (
                isinstance(first_generator.target, (ast.Tuple, ast.List))
                and isinstance(first_generator.iter, (ast.Tuple, ast.List))
                and first_generator.iter.elts
                and all(
                    isinstance(item, (ast.Tuple, ast.List))
                    and len(item.elts) != len(first_generator.target.elts)
                    for item in first_generator.iter.elts
                )
            ):
                return _ExpressionOutcomes(False, True)
            conditions = [
                condition
                for generator in node.generators
                for condition in generator.ifs
            ]
            if any(
                isinstance(condition, ast.Constant)
                and not bool(condition.value)
                for condition in conditions
            ):
                return _ExpressionOutcomes(True, first.raises)
            children: list[ast.AST] = []
            for generator in node.generators[1:]:
                children.append(generator.iter)
                children.extend(generator.ifs)
            children.extend(node.generators[0].ifs)
            if isinstance(node, ast.DictComp):
                children.extend((node.key, node.value))
            else:
                children.append(node.elt)
            body = self._ordered_expression_outcomes(children)
            may_skip = bound is None or any(
                not isinstance(condition, ast.Constant)
                for condition in conditions
            )
            return _ExpressionOutcomes(
                body.normal or may_skip,
                first.raises or body.raises,
            )
        if isinstance(node, ast.Dict):
            children: list[ast.AST] = []
            for key, value in zip(node.keys, node.values, strict=True):
                if key is not None:
                    children.append(key)
                children.append(value)
            prefix = self._ordered_expression_outcomes(children)
            return _ExpressionOutcomes(prefix.normal, True)
        if isinstance(node, (ast.List, ast.Tuple, ast.Set, ast.JoinedStr)):
            prefix = self._ordered_expression_outcomes(tuple(ast.iter_child_nodes(node)))
            return _ExpressionOutcomes(
                prefix.normal,
                prefix.raises or isinstance(node, ast.Set),
            )
        prefix = self._ordered_expression_outcomes(tuple(ast.iter_child_nodes(node)))
        return _ExpressionOutcomes(prefix.normal, True)

    def _ordered_expression_outcomes(
        self,
        nodes: Sequence[ast.AST],
    ) -> _ExpressionOutcomes:
        normal = True
        raises = False
        for child in nodes:
            supplied = self._expression_outcomes(child)
            raises |= normal and supplied.raises
            normal &= supplied.normal
            if not normal:
                break
        return _ExpressionOutcomes(normal, raises)

    def _expression_definitely_terminates(self, node: ast.AST | None) -> bool:
        return not self._expression_outcomes(node).normal

    def _delete_target(self, target: ast.AST) -> bool:
        if isinstance(target, (ast.Tuple, ast.List)):
            for item in target.elts:
                if not self._delete_target(item):
                    return False
            return True
        if isinstance(target, ast.Name):
            supplied = self.bindings.get(target.id)
            if supplied is None or supplied == "__unbound__":
                self._record_throw_state(
                    self._lookup_error_tag(target.id),
                    True,
                )
                return False
            if supplied.startswith("__maybe_unbound__"):
                self._record_throw_state(
                    self._lookup_error_tag(target.id),
                    True,
                )
            self.bindings[target.id] = "__unbound__"
            self.tainted.discard(target.id)
            return True
        if isinstance(target, ast.Subscript):
            self._expression(target.value)
            if self._expression_definitely_terminates(target.value):
                return False
            self._expression(target.slice)
            if self._expression_definitely_terminates(target.slice):
                return False
            self._record_throw_state(None, True)
            return True
        if isinstance(target, ast.Attribute):
            self._expression(target.value)
            if self._expression_definitely_terminates(target.value):
                return False
            self._record_throw_state(None, True)
            return True
        self._expression(target)
        return not self._expression_definitely_terminates(target)

    @staticmethod
    def _qualified_is_sensitive(qualified: str | None) -> bool:
        return qualified is not None and (
            qualified in _SUBPROCESS_FUNCTIONS
            or _is_sensitive_namespace(qualified)
        )

    @staticmethod
    def _qualified_call_is_sensitive(qualified: str | None) -> bool:
        return qualified is not None and (
            qualified in _SUBPROCESS_FUNCTIONS
            or qualified in _OWNER_CALLS
            or qualified in _SCIENTIFIC_PROTECTED_CALLS
            or qualified == "cupy"
            or qualified.startswith("cupy.")
        )

    def _snapshot(self) -> tuple[dict[str, str], set[str]]:
        return dict(self.bindings), set(self.tainted)

    def _restore(self, state: tuple[dict[str, str], set[str]]) -> None:
        self.bindings, self.tainted = dict(state[0]), set(state[1])

    def _merge(
        self,
        states: Sequence[tuple[dict[str, str], set[str]]],
    ) -> None:
        names = set().union(*(state[0].keys() for state in states))
        bindings: dict[str, str] = {}
        for name in names:
            supplied = {state[0].get(name) for state in states}
            deferred_markers = {
                value
                for value in supplied
                if isinstance(value, str)
                and value.startswith("__deferred_generator__:")
            }
            if deferred_markers and (
                len(deferred_markers) != 1 or len(supplied) != 1
            ):
                marker = next(iter(deferred_markers))
                bindings[name] = marker
                deferred = self.deferred_generators.get(marker)
                if deferred is not None:
                    self.deferred_generators[marker] = replace(
                        deferred,
                        supported=False,
                    )
                    if _contains_sensitive_runtime(
                        deferred.expression,
                        self.budget,
                    ):
                        self.tainted.add(name)
                continue
            if len(supplied) == 1 and None not in supplied:
                value = next(iter(supplied))
                if value is not None:
                    bindings[name] = value
            elif name in (
                self.lexical_scope.local_names
                | self.lexical_scope.nonlocal_names
                | self.lexical_scope.global_names
            ):
                bound_values = {
                    value
                    for value in supplied
                    if value not in {None, "__unbound__"}
                    and not str(value).startswith("__maybe_unbound__")
                }
                retained = (
                    next(iter(bound_values))
                    if len(bound_values) == 1
                    else ""
                )
                bindings[name] = f"__maybe_unbound__:{retained}"
        self.bindings = bindings
        self.tainted = set().union(*(state[1] for state in states))

    def _bind(
        self,
        target: ast.AST,
        qualified: str | None,
        sensitive: bool,
    ) -> None:
        if isinstance(target, ast.Attribute):
            raw = _qualified_name(target)
            if raw is not None:
                self.bindings[raw] = qualified or "__safe_bound_value__"
                if sensitive:
                    self.tainted.add(raw)
                else:
                    self.tainted.discard(raw)
            return
        names = _python_bound_names(target)
        for name in names:
            if isinstance(target, ast.Name) and qualified is not None:
                self.bindings[name] = qualified
            elif isinstance(target, ast.Name):
                self.bindings[name] = "__bound_unknown__"
            else:
                self.bindings.pop(name, None)
            if sensitive:
                self.tainted.add(name)
            else:
                self.tainted.discard(name)
        if not isinstance(target, ast.Subscript):
            return
        container = _qualified_name(target.value)
        if container is not None and sensitive:
            self.tainted.add(container)
            mutable_marker = self.bindings.get(container)
            if (
                mutable_marker is not None
                and ":mutable:" in mutable_marker
            ):
                self.tainted.update(
                    name
                    for name, binding in self.bindings.items()
                    if binding == mutable_marker
                )
        root = target.value
        while isinstance(root, (ast.Attribute, ast.Subscript)):
            root = root.value
        if isinstance(root, ast.Name) and sensitive:
            self.tainted.add(root.id)

    def _literal_iteration_bound(self, node: ast.expr) -> int | None:
        if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
            return self.budget.cardinality(len(node.elts))
        if isinstance(node, ast.Dict):
            return self.budget.cardinality(len(node.keys))
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "range"
            and 1 <= len(node.args) <= 3
            and not node.keywords
            and all(
                isinstance(argument, ast.Constant)
                and type(argument.value) is int
                for argument in node.args
            )
        ):
            arguments = [int(argument.value) for argument in node.args]
            if len(arguments) == 3 and arguments[2] == 0:
                raise InventoryError("analysis range step is zero")
            try:
                cardinality = len(range(*arguments))
            except (OverflowError, ValueError) as error:
                raise InventoryError(
                    "analysis expanded cardinality exceeds 2147483647"
                ) from error
            return self.budget.cardinality(cardinality)
        return None

    def _expression(self, node: ast.AST | None) -> tuple[str | None, bool]:
        if node is None:
            return None, False
        self.budget.consume()
        if isinstance(node, ast.Constant):
            return "__exception_invalid__", False
        if isinstance(node, ast.Name):
            qualified = self.bindings.get(node.id)
            if qualified == "__unbound__":
                self._record_throw_state(
                    self._lookup_error_tag(node.id),
                    True,
                )
                return None, False
            maybe_prefix = "__maybe_unbound__:"
            if qualified is not None and qualified.startswith(maybe_prefix):
                self._record_throw_state(
                    self._lookup_error_tag(node.id),
                    True,
                )
                qualified = qualified.removeprefix(maybe_prefix) or None
            if qualified is None:
                proven = _proven_builtin_exception_name(
                    node,
                    self.exception_scope,
                )
                if proven is not None:
                    qualified = f"__builtin_exception__:{proven}"
                elif node.id in self.exception_scope.shadowed_names:
                    self._record_throw_state("NameError", True)
            return qualified, (
                node.id in self.tainted
                or self._qualified_call_is_sensitive(qualified)
            )
        if isinstance(node, ast.Attribute):
            raw = _qualified_name(node)
            if raw is not None and raw in self.bindings:
                qualified = self.bindings[raw]
                return qualified, (
                    raw in self.tainted
                    or self._qualified_call_is_sensitive(qualified)
                )
            qualified, sensitive = self._expression(node.value)
            if qualified is None:
                return None, sensitive
            supplied = f"{qualified}.{node.attr}"
            return supplied, (
                sensitive or self._qualified_call_is_sensitive(supplied)
            )
        if isinstance(node, ast.NamedExpr):
            qualified, sensitive = self._expression(node.value)
            if self._expression_definitely_terminates(node.value):
                return qualified, sensitive
            self._bind(node.target, qualified, sensitive)
            return qualified, sensitive
        if isinstance(node, ast.Call):
            qualified, callable_sensitive = self._expression(node.func)
            direct_sensitive = self._qualified_call_is_sensitive(qualified)
            if callable_sensitive or direct_sensitive:
                self.calls.add(id(node))
            result_sensitive = (
                callable_sensitive and qualified is None
            ) or (
                qualified is not None
                and (
                    qualified == "cupy"
                    or qualified.startswith("cupy.")
                )
            )
            argument_results: list[str | None] = []
            for argument in node.args:
                argument_qualified, sensitive = self._expression(argument)
                argument_results.append(argument_qualified)
                result_sensitive |= sensitive
                if self._expression_definitely_terminates(argument):
                    return None, result_sensitive
            for keyword in node.keywords:
                _, sensitive = self._expression(keyword.value)
                result_sensitive |= sensitive
                if self._expression_definitely_terminates(keyword.value):
                    return None, result_sensitive
            constructor_success, constructor_error, constructor_unknown = (
                _builtin_exception_constructor_outcome(
                    node,
                    self.exception_scope,
                )
            )
            if constructor_error is not None and constructor_success is None:
                self._record_throw_state(constructor_error, True)
                return "__constructor_failed__", result_sensitive
            must_raise_tag = self._must_raise_tag(node)
            call_summary = (
                self.helper_summaries.get(qualified or "")
                if isinstance(node.func, ast.Name)
                else None
            )
            proven_normal_call = bool(
                call_summary is not None
                and call_summary.proven_normal_only
                and _bounded_call_shape(node, call_summary) == "valid"
            )
            if must_raise_tag == "TypeError":
                self._record_throw_state("TypeError", True)
                return None, result_sensitive
            if (
                isinstance(node.func, ast.Name)
                and node.func.id == "next"
                and node.args
            ):
                supplied = argument_results[0]
                deferred = self.deferred_generators.get(supplied or "")
                if deferred is not None:
                    if not deferred.supported:
                        incoming = self._snapshot()
                        self._expression(deferred.expression.elt)
                        result_sensitive |= any(
                            identifier in self.calls
                            for identifier in (
                                id(candidate)
                                for candidate in ast.walk(
                                    deferred.expression.elt
                                )
                                if isinstance(candidate, ast.Call)
                            )
                        )
                        self._restore(incoming)
                        return None, result_sensitive
                    if deferred.remaining == 0:
                        if len(node.args) == 1:
                            self._record_throw_state("StopIteration", True)
                            return None, result_sensitive
                        return None, result_sensitive
                    incoming = self._snapshot()
                    expression = deferred.expression
                    next_state = replace(
                        deferred,
                        remaining=(
                            None
                            if deferred.remaining is None
                            else max(0, deferred.remaining - 1)
                        ),
                    )
                    for marker, candidate in tuple(
                        self.deferred_generators.items()
                    ):
                        if candidate.identity == deferred.identity:
                            self.deferred_generators[marker] = replace(
                                deferred,
                                remaining=0,
                            )
                    first = expression.generators[0]
                    self._bind(
                        first.target,
                        None,
                        deferred.outer_iterator_sensitive,
                    )
                    for condition in first.ifs:
                        condition_qualified, condition_sensitive = self._expression(condition)
                        result_sensitive |= condition_sensitive
                        if self._expression_definitely_terminates(condition):
                            return None, result_sensitive
                        if isinstance(condition, ast.Constant) and not bool(condition.value):
                            self._restore(incoming)
                            self.deferred_generators[supplied or ""] = replace(
                                deferred,
                                remaining=0,
                            )
                            return None, result_sensitive
                    for generator in expression.generators[1:]:
                        _, iterator_sensitive = self._expression(generator.iter)
                        self._bind(generator.target, None, iterator_sensitive)
                        for condition in generator.ifs:
                            self._expression(condition)
                    self._expression(expression.elt)
                    if self._expression_definitely_terminates(expression.elt):
                        return None, result_sensitive
                    executed = self._snapshot()
                    self._restore(incoming)
                    for candidate in ast.walk(expression):
                        if not isinstance(candidate, ast.NamedExpr):
                            continue
                        for name in _python_bound_names(candidate.target):
                            if name in executed[0]:
                                self.bindings[name] = executed[0][name]
                            if name in executed[1]:
                                self.tainted.add(name)
                            else:
                                self.tainted.discard(name)
                    for marker, candidate in tuple(self.deferred_generators.items()):
                        if candidate.identity == deferred.identity:
                            self.deferred_generators[marker] = next_state
            direct_tuple_expression = _direct_builtin_tuple_generator(
                node,
                callee_is_unshadowed_builtin=(
                    qualified is None and "tuple" not in self.bindings
                ),
            )
            direct_tuple_state = (
                self.deferred_generators.get(argument_results[0] or "")
                if direct_tuple_expression is not None
                else None
            )
            modeled_tuple = bool(
                direct_tuple_state is not None
                and direct_tuple_state.expression is direct_tuple_expression
                and direct_tuple_state.supported
                and direct_tuple_state.remaining is not None
            )
            if modeled_tuple and direct_tuple_state is not None:
                incoming = self._snapshot()
                try:
                    for _ in range(direct_tuple_state.remaining or 0):
                        first = direct_tuple_state.expression.generators[0]
                        self._bind(
                            first.target,
                            None,
                            direct_tuple_state.outer_iterator_sensitive,
                        )
                        skip_body = False
                        for condition in first.ifs:
                            _, condition_sensitive = self._expression(condition)
                            result_sensitive |= condition_sensitive
                            if self._expression_definitely_terminates(condition):
                                skip_body = True
                                break
                            if (
                                isinstance(condition, ast.Constant)
                                and not bool(condition.value)
                            ):
                                skip_body = True
                                break
                        if skip_body:
                            continue
                        _, body_sensitive = self._expression(
                            direct_tuple_state.expression.elt
                        )
                        result_sensitive |= body_sensitive
                finally:
                    self._restore(incoming)
            modeled_next = bool(
                isinstance(node.func, ast.Name)
                and node.func.id == "next"
                and node.args
                and isinstance(node.args[0], ast.Name)
                and (
                    marker := self.bindings.get(node.args[0].id)
                ) is not None
                and (
                    generator_state := self.deferred_generators.get(marker)
                ) is not None
                and generator_state.supported
            )
            if qualified is not None and qualified.startswith(
                "__constant_bool__:"
            ):
                return qualified, result_sensitive
            if (
                (constructor_success is None or constructor_unknown)
                and not modeled_next
                and not modeled_tuple
                and not proven_normal_call
            ):
                self._record_throw_state(
                    must_raise_tag,
                    must_raise_tag is not None,
                )
            if qualified in _SAFE_OBSERVATION_CALLS | _SAFE_MOCK_FACTORIES:
                result_sensitive = False
            if qualified in self.helper_returns:
                returned_qualified, returned_sensitive = (
                    self.helper_returns[qualified]
                )
                return (
                    returned_qualified,
                    returned_sensitive or result_sensitive,
                )
            if qualified == "pontius.cupy_sparse_incidence._cupy_modules":
                return None, True
            exception_prefix = "__builtin_exception__:"
            if constructor_success is not None:
                return (
                    f"__exception_instance__:{constructor_success}",
                    result_sensitive,
                )
            if qualified is not None and qualified.startswith(exception_prefix):
                return (
                    "__exception_instance__:"
                    f"{qualified[len(exception_prefix):]}",
                    result_sensitive,
                )
            return None, result_sensitive
        if isinstance(node, (ast.Await, ast.Yield, ast.YieldFrom)):
            qualified, sensitive = self._expression(node.value)
            self._record_throw_state()
            return qualified, sensitive
        if isinstance(node, ast.Raise):
            _, exception_sensitive = self._expression(node.exc)
            _, cause_sensitive = self._expression(node.cause)
            return None, exception_sensitive or cause_sensitive
        if isinstance(node, ast.GeneratorExp):
            # Generator creation evaluates only the outermost iterable; the
            # remaining generators, filters and body are deferred to next().
            _, sensitive = self._expression(node.generators[0].iter)
            marker = f"__deferred_generator__:{id(node)}"
            first = node.generators[0]
            remaining = self._literal_iteration_bound(first.iter)
            if any(
                isinstance(condition, ast.Constant)
                and not bool(condition.value)
                for condition in first.ifs
            ):
                remaining = 0
            supported = bool(
                remaining is not None
                and len(node.generators) == 1
                and all(
                    isinstance(condition, ast.Constant)
                    or (
                        isinstance(condition, ast.Call)
                        and isinstance(condition.func, ast.Name)
                        and (
                            filter_summary := self.helper_summaries.get(
                                self.bindings.get(condition.func.id, "")
                            )
                        ) is not None
                        and filter_summary.exception_tag is not None
                        and _bounded_call_shape(
                            condition,
                            filter_summary,
                        ) == "valid"
                    )
                    for condition in first.ifs
                )
            )
            self.deferred_generators[marker] = _DeferredGeneratorState(
                node,
                id(node),
                remaining,
                supported,
                sensitive,
            )
            return marker, sensitive
        if isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp)):
            incoming = self._snapshot()
            skipped_states: list[tuple[dict[str, str], set[str]]] = []
            may_skip = False
            repeated: int | None = 1
            result_sensitive = False
            for generator in node.generators:
                if repeated == 0:
                    break
                _, iterator_sensitive = self._expression(generator.iter)
                result_sensitive |= iterator_sensitive
                if self._expression_definitely_terminates(generator.iter):
                    if skipped_states:
                        self._merge(skipped_states)
                        repeated = 0
                        break
                    return None, result_sensitive
                bound = self._literal_iteration_bound(generator.iter)
                if bound is None:
                    repeated = None
                    may_skip = True
                elif repeated is not None:
                    repeated = self.budget.cardinality(
                        _checked_cardinality_multiply(repeated, bound)
                    )
                if bound == 0:
                    break
                if (
                    isinstance(generator.target, (ast.Tuple, ast.List))
                    and isinstance(generator.iter, (ast.Tuple, ast.List))
                    and generator.iter.elts
                    and all(
                        isinstance(item, (ast.Tuple, ast.List))
                        and len(item.elts) != len(generator.target.elts)
                        for item in generator.iter.elts
                    )
                ):
                    self._record_throw_state("ValueError", True)
                    return None, result_sensitive
                self._bind(generator.target, None, iterator_sensitive)
                for condition in generator.ifs:
                    _, condition_sensitive = self._expression(condition)
                    result_sensitive |= condition_sensitive
                    if (
                        isinstance(condition, ast.Constant)
                        and not bool(condition.value)
                    ):
                        repeated = 0
                        break
                    if not (
                        isinstance(condition, ast.Constant)
                        and bool(condition.value)
                    ):
                        repeated = None
                        may_skip = True
                        skipped_states.append(self._snapshot())
                if repeated == 0:
                    break
            if repeated != 0:
                expressions = (
                    (node.key, node.value)
                    if isinstance(node, ast.DictComp)
                    else (node.elt,)
                )
                for expression in expressions:
                    _, sensitive = self._expression(expression)
                    result_sensitive |= sensitive
            executed = self._snapshot()
            named_bindings = {
                name: executed[0].get(name)
                for candidate in ast.walk(node)
                if isinstance(candidate, ast.NamedExpr)
                for name in _python_bound_names(candidate.target)
            }
            named_taint = {
                name
                for name in named_bindings
                if name in executed[1]
            }
            self._restore(incoming)
            for name, supplied in named_bindings.items():
                if supplied is None:
                    self.bindings.pop(name, None)
                else:
                    self.bindings[name] = supplied
                if name in named_taint:
                    self.tainted.add(name)
            if may_skip:
                self._merge((incoming, self._snapshot()))
            self._record_throw_state(None, True)
            return None, result_sensitive
        if isinstance(node, ast.Lambda):
            for default in (*node.args.defaults, *node.args.kw_defaults):
                self._expression(default)
            if isinstance(node.body, ast.Constant) and type(node.body.value) is bool:
                return f"__constant_bool__:{node.body.value}", False
            return "__exception_invalid__", False
        if isinstance(node, ast.BoolOp):
            sensitive = False
            for index, item in enumerate(node.values):
                incoming = self._snapshot()
                _, item_sensitive = self._expression(item)
                sensitive |= item_sensitive
                if isinstance(item, ast.Constant):
                    if isinstance(node.op, ast.And) and not bool(item.value):
                        break
                    if isinstance(node.op, ast.Or) and bool(item.value):
                        break
                elif index:
                    executed = self._snapshot()
                    self._merge((incoming, executed))
            return None, sensitive
        if isinstance(node, ast.IfExp):
            _, test_sensitive = self._expression(node.test)
            if isinstance(node.test, ast.Constant):
                chosen = node.body if bool(node.test.value) else node.orelse
                _, branch_sensitive = self._expression(chosen)
                return None, test_sensitive or branch_sensitive
            incoming = self._snapshot()
            _, first_sensitive = self._expression(node.body)
            first = self._snapshot()
            self._restore(incoming)
            _, second_sensitive = self._expression(node.orelse)
            second = self._snapshot()
            self._merge((first, second))
            return None, test_sensitive or first_sensitive or second_sensitive
        if isinstance(node, ast.Dict):
            sensitive = False
            for key, value in zip(node.keys, node.values, strict=True):
                if key is None:
                    qualified, child_sensitive = self._expression(value)
                    sensitive |= child_sensitive
                    if self._expression_definitely_terminates(value):
                        return None, sensitive
                    if (
                        qualified is None
                        or not qualified.startswith("__mapping__")
                    ):
                        self._record_throw_state("TypeError", True)
                        return None, sensitive
                    continue
                _, key_sensitive = self._expression(key)
                sensitive |= key_sensitive
                if self._expression_definitely_terminates(key):
                    return None, sensitive
                _, value_sensitive = self._expression(value)
                sensitive |= value_sensitive
                if self._expression_definitely_terminates(value):
                    return None, sensitive
                self._record_throw_state(None, True)
            return f"__mapping__:mutable:{id(node)}", sensitive
        if isinstance(node, (ast.List, ast.Tuple, ast.Set, ast.JoinedStr)):
            sensitive = False
            for child in ast.iter_child_nodes(node):
                _, child_sensitive = self._expression(child)
                sensitive |= child_sensitive
                if self._expression_definitely_terminates(child):
                    return None, sensitive
            if isinstance(node, (ast.Set, ast.Dict)):
                self._record_throw_state(None, True)
            if isinstance(node, (ast.List, ast.Set)):
                return (
                    f"__exception_invalid__:mutable:{id(node)}",
                    sensitive,
                )
            return "__exception_invalid__", sensitive
        sensitive = False
        for child in ast.iter_child_nodes(node):
            _, child_sensitive = self._expression(child)
            sensitive |= child_sensitive
        return None, sensitive

    def _statements(
        self,
        statements: Sequence[ast.stmt],
    ) -> _PreclassifierSuccessors:
        successors = _PreclassifierSuccessors()

        def absorb(flow: _PreclassifierSuccessors) -> None:
            successors.raises.extend(flow.raises)
            successors.returns.extend(flow.returns)
            successors.breaks.extend(flow.breaks)
            successors.continues.extend(flow.continues)

        def continue_from(
            states: Sequence[tuple[dict[str, str], set[str]]],
        ) -> bool:
            if not states:
                return False
            self._merge(states)
            return True

        for statement_index, statement in enumerate(statements):
            self.budget.consume()

            def scan_unreachable_remainder() -> None:
                for remaining in statements[statement_index + 1:]:
                    self._expression(remaining)
            if isinstance(statement, ast.Import):
                for imported in statement.names:
                    local = imported.asname or imported.name.split(".", 1)[0]
                    qualified = imported.name if imported.asname else local
                    self._bind(
                        ast.Name(id=local),
                        qualified,
                        self._qualified_call_is_sensitive(qualified),
                    )
                continue
            if isinstance(statement, ast.ImportFrom) and statement.module:
                for imported in statement.names:
                    local = imported.asname or imported.name
                    qualified = f"{statement.module}.{imported.name}"
                    self._bind(
                        ast.Name(id=local),
                        qualified,
                        self._qualified_call_is_sensitive(qualified),
                    )
                continue
            if isinstance(statement, ast.Assign):
                qualified, sensitive = self._expression(statement.value)
                if self._expression_definitely_terminates(statement.value):
                    return successors
                for target in statement.targets:
                    self._bind(target, qualified, sensitive)
                continue
            if isinstance(statement, ast.AnnAssign):
                if statement.value is not None:
                    qualified, sensitive = self._expression(statement.value)
                    if self._expression_definitely_terminates(statement.value):
                        return successors
                    self._bind(statement.target, qualified, sensitive)
                continue
            if isinstance(statement, ast.AugAssign):
                _, old_sensitive = self._expression(statement.target)
                if self._expression_definitely_terminates(statement.target):
                    return successors
                _, new_sensitive = self._expression(statement.value)
                if self._expression_definitely_terminates(statement.value):
                    return successors
                self._bind(statement.target, None, old_sensitive or new_sensitive)
                continue
            if isinstance(statement, ast.Delete):
                for target in statement.targets:
                    if not self._delete_target(target):
                        return successors
                continue
            if isinstance(statement, ast.Expr):
                self._expression(statement.value)
                if self._expression_definitely_terminates(statement.value):
                    return successors
                continue
            if isinstance(statement, ast.If):
                self._expression(statement.test)
                if self._expression_definitely_terminates(statement.test):
                    return successors
                incoming = self._snapshot()
                branches = (
                    (statement.body,)
                    if isinstance(statement.test, ast.Constant)
                    and bool(statement.test.value)
                    else (
                        (statement.orelse,)
                        if isinstance(statement.test, ast.Constant)
                        else (statement.body, statement.orelse)
                    )
                )
                normal: list[tuple[dict[str, str], set[str]]] = []
                for branch in branches:
                    self._restore(incoming)
                    flow = self._statements(branch)
                    absorb(flow)
                    normal.extend(flow.normal)
                if not continue_from(normal):
                    scan_unreachable_remainder()
                    return successors
                continue
            if isinstance(statement, (ast.For, ast.AsyncFor)):
                _, sensitive = self._expression(statement.iter)
                if self._expression_definitely_terminates(statement.iter):
                    return successors
                incoming = self._snapshot()
                bound = self._literal_iteration_bound(statement.iter)
                body_flow = _PreclassifierSuccessors()
                if bound != 0:
                    self._bind(statement.target, None, sensitive)
                    body_flow = self._statements(statement.body)
                    successors.returns.extend(body_flow.returns)
                    successors.raises.extend(body_flow.raises)
                no_break = list(body_flow.normal) + list(body_flow.continues)
                if bound is None or bound == 0:
                    no_break.append(incoming)
                orelse_normal: list[tuple[dict[str, str], set[str]]] = []
                if no_break:
                    self._merge(no_break)
                    orelse_flow = self._statements(statement.orelse)
                    absorb(orelse_flow)
                    orelse_normal.extend(orelse_flow.normal)
                normal = list(body_flow.breaks) + orelse_normal
                if not continue_from(normal):
                    scan_unreachable_remainder()
                    return successors
                continue
            if isinstance(statement, ast.While):
                test_qualified, _ = self._expression(statement.test)
                if self._expression_definitely_terminates(statement.test):
                    return successors
                incoming = self._snapshot()
                body_flow = _PreclassifierSuccessors()
                definitely_false = (
                    isinstance(statement.test, ast.Constant)
                    and not bool(statement.test.value)
                )
                definitely_true = test_qualified == "__constant_bool__:True"
                if not definitely_false:
                    body_flow = self._statements(statement.body)
                    successors.returns.extend(body_flow.returns)
                    successors.raises.extend(body_flow.raises)
                no_break: list[tuple[dict[str, str], set[str]]] = []
                for continuing in (*body_flow.normal, *body_flow.continues):
                    self._restore(continuing)
                    repeated_qualified, _ = self._expression(statement.test)
                    if not self._expression_definitely_terminates(statement.test):
                        if repeated_qualified != "__constant_bool__:True":
                            no_break.append(self._snapshot())
                if definitely_false or (
                    not definitely_true
                    and not isinstance(statement.test, ast.Constant)
                ):
                    no_break.append(incoming)
                orelse_normal: list[tuple[dict[str, str], set[str]]] = []
                if no_break:
                    self._merge(no_break)
                    orelse_flow = self._statements(statement.orelse)
                    absorb(orelse_flow)
                    orelse_normal.extend(orelse_flow.normal)
                normal = list(body_flow.breaks) + orelse_normal
                if not continue_from(normal):
                    return successors
                continue
            if isinstance(statement, (ast.With, ast.AsyncWith)):
                suppress_arguments: list[tuple[ast.expr, ...]] = []
                for item in statement.items:
                    suppress_call = False
                    if isinstance(item.context_expr, ast.Call):
                        context_qualified, _ = self._expression(
                            item.context_expr.func
                        )
                        if context_qualified == "contextlib.suppress":
                            suppress_call = True
                            suppress_arguments.append(
                                tuple(item.context_expr.args)
                            )
                    retained_throw_count = (
                        len(self._throw_states)
                        if self._throw_states is not None
                        else 0
                    )
                    qualified, sensitive = self._expression(item.context_expr)
                    if self._expression_definitely_terminates(item.context_expr):
                        return successors
                    if (
                        suppress_call
                        and isinstance(item.context_expr, ast.Call)
                        and all(
                            self._expression_is_proven_nonthrowing(argument)
                            for argument in item.context_expr.args
                        )
                        and self._throw_states is not None
                    ):
                        del self._throw_states[retained_throw_count:]
                    if item.optional_vars is not None:
                        self._bind(item.optional_vars, qualified, sensitive)
                outer_throw_states = self._throw_states
                exceptional: list[_PreclassifierExceptionalState] = []
                self._throw_states = exceptional
                try:
                    flow = self._statements(statement.body)
                finally:
                    self._throw_states = outer_throw_states
                successors.returns.extend(flow.returns)
                successors.breaks.extend(flow.breaks)
                successors.continues.extend(flow.continues)
                normal = list(flow.normal)
                governed = [*flow.raises, *exceptional]
                if suppress_arguments:
                    for exception in governed:
                        outcomes = {"nonmatch"}
                        for arguments in reversed(suppress_arguments):
                            advanced = set(outcomes) - {"nonmatch"}
                            if "nonmatch" in outcomes:
                                advanced.update(
                                    self._suppress_outcomes(
                                        exception,
                                        arguments,
                                    )
                                )
                            outcomes = advanced
                        if "match" in outcomes:
                            normal.append(exception.state)
                        if "nonmatch" in outcomes:
                            successors.raises.append(exception)
                        if "invalid" in outcomes:
                            successors.raises.append(
                                _PreclassifierExceptionalState(
                                    exception.state,
                                    "TypeError",
                                    True,
                                )
                            )
                else:
                    successors.raises.extend(flow.raises)
                    if outer_throw_states is not None:
                        outer_throw_states.extend(exceptional)
                if not continue_from(normal):
                    scan_unreachable_remainder()
                    return successors
                continue
            try_types = (ast.Try,)
            if hasattr(ast, "TryStar"):
                try_types = (*try_types, ast.TryStar)
            if isinstance(statement, try_types):
                outer_throw_states = self._throw_states
                protected_exceptional: list[_PreclassifierExceptionalState] = []
                self._throw_states = protected_exceptional
                try:
                    protected_flow = self._statements(statement.body)
                finally:
                    self._throw_states = outer_throw_states
                local = _PreclassifierSuccessors(
                    returns=list(protected_flow.returns),
                    breaks=list(protected_flow.breaks),
                    continues=list(protected_flow.continues),
                )
                normal: list[tuple[dict[str, str], set[str]]] = []
                if protected_flow.normal:
                    self._merge(protected_flow.normal)
                    orelse_exceptional: list[_PreclassifierExceptionalState] = []
                    self._throw_states = orelse_exceptional
                    try:
                        orelse_flow = self._statements(statement.orelse)
                    finally:
                        self._throw_states = outer_throw_states
                    local.raises.extend(orelse_exceptional)
                    local.raises.extend(orelse_flow.raises)
                    local.returns.extend(orelse_flow.returns)
                    local.breaks.extend(orelse_flow.breaks)
                    local.continues.extend(orelse_flow.continues)
                    normal.extend(orelse_flow.normal)
                protected_raises = [
                    *protected_exceptional,
                    *protected_flow.raises,
                ]
                if statement.handlers:
                    for exceptional in protected_raises:
                        residual: _PreclassifierExceptionalState | None = (
                            exceptional
                        )
                        for handler in statement.handlers:
                            handler_exceptional: list[
                                _PreclassifierExceptionalState
                            ] = []
                            self._throw_states = handler_exceptional
                            try:
                                self._restore(residual.state)
                                validation = self._handler_validation(handler.type)
                                match = (
                                    self._handler_match(
                                        residual.exception_tag,
                                        handler.type,
                                    )
                                    if residual.explicit
                                    else self._implicit_handler_match(
                                        residual,
                                        handler.type,
                                    )
                                )
                                evaluation_state = self._snapshot()
                                self._expression(handler.type)
                                validation_state = self._snapshot()
                                if not self._expression_is_proven_nonthrowing(
                                    handler.type
                                ):
                                    local.raises.append(
                                        _PreclassifierExceptionalState(
                                            evaluation_state,
                                            None,
                                            True,
                                        )
                                    )
                                if validation == "invalid" or (
                                    validation == "unknown"
                                ):
                                    local.raises.append(
                                        _PreclassifierExceptionalState(
                                            validation_state,
                                            "TypeError",
                                            True,
                                        )
                                    )
                                if validation == "invalid" or match == "nonmatch":
                                    handler_flow = _PreclassifierSuccessors()
                                else:
                                    if handler.name is not None:
                                        self._bind(
                                            ast.Name(id=handler.name),
                                            "__exception_instance__:"
                                            f"{residual.exception_tag or 'unknown'}",
                                            False,
                                        )
                                    previous_active = self._active_exception_tag
                                    self._active_exception_tag = (
                                        residual.exception_tag
                                    )
                                    try:
                                        handler_flow = self._statements(
                                            handler.body
                                        )
                                    finally:
                                        self._active_exception_tag = previous_active
                            finally:
                                self._throw_states = outer_throw_states
                            local.raises.extend(handler_exceptional)
                            if handler.name is not None:
                                for supplied in (
                                    handler_flow.normal,
                                    handler_flow.returns,
                                    handler_flow.breaks,
                                    handler_flow.continues,
                                ):
                                    for state in supplied:
                                        state[0].pop(handler.name, None)
                                        state[1].discard(handler.name)
                                for raised in handler_flow.raises:
                                    raised.state[0].pop(handler.name, None)
                                    raised.state[1].discard(handler.name)
                                for raised in handler_exceptional:
                                    raised.state[0].pop(handler.name, None)
                                    raised.state[1].discard(handler.name)
                            local.raises.extend(handler_flow.raises)
                            local.returns.extend(handler_flow.returns)
                            local.breaks.extend(handler_flow.breaks)
                            local.continues.extend(handler_flow.continues)
                            normal.extend(handler_flow.normal)
                            if validation == "invalid":
                                residual = None
                                break
                            if match == "match":
                                residual = None
                                break
                            if not residual.explicit and match == "unknown":
                                residual = _PreclassifierExceptionalState(
                                    residual.state,
                                    residual.exception_tag,
                                    False,
                                    residual.excluded_handlers
                                    | self._handler_exception_names(handler.type),
                                )
                        if residual is not None:
                            local.raises.append(residual)
                else:
                    local.raises.extend(protected_raises)
                local.normal = normal
                if statement.finalbody:
                    transformed = _PreclassifierSuccessors()
                    for exit_kind in (
                        "normal",
                        "raises",
                        "returns",
                        "breaks",
                        "continues",
                    ):
                        incoming_states = getattr(local, exit_kind)
                        for incoming_state in incoming_states:
                            incoming_exception = (
                                incoming_state
                                if exit_kind == "raises"
                                else None
                            )
                            state = (
                                incoming_exception.state
                                if incoming_exception is not None
                                else incoming_state
                            )
                            self._restore(state)
                            final_exceptional: list[
                                _PreclassifierExceptionalState
                            ] = []
                            self._throw_states = final_exceptional
                            try:
                                final_flow = self._statements(statement.finalbody)
                            finally:
                                self._throw_states = outer_throw_states
                            transformed.raises.extend(final_exceptional)
                            transformed.raises.extend(final_flow.raises)
                            transformed.returns.extend(final_flow.returns)
                            transformed.breaks.extend(final_flow.breaks)
                            transformed.continues.extend(final_flow.continues)
                            if incoming_exception is None:
                                getattr(transformed, exit_kind).extend(
                                    final_flow.normal
                                )
                            else:
                                transformed.raises.extend(
                                    _PreclassifierExceptionalState(
                                        normal_state,
                                        incoming_exception.exception_tag,
                                        incoming_exception.explicit,
                                        incoming_exception.excluded_handlers,
                                    )
                                    for normal_state in final_flow.normal
                                )
                    local = transformed
                if outer_throw_states is not None:
                    outer_throw_states.extend(local.raises)
                successors.raises.extend(local.raises)
                successors.returns.extend(local.returns)
                successors.breaks.extend(local.breaks)
                successors.continues.extend(local.continues)
                normal = local.normal
                if not continue_from(normal):
                    scan_unreachable_remainder()
                    return successors
                continue
            if isinstance(statement, ast.Match):
                _, sensitive = self._expression(statement.subject)
                if self._expression_definitely_terminates(statement.subject):
                    return successors
                incoming = self._snapshot()
                normal: list[tuple[dict[str, str], set[str]]] = []
                residual: tuple[dict[str, str], set[str]] | None = incoming
                for case in statement.cases:
                    if residual is None:
                        break
                    self._restore(residual)
                    self._bind(case.pattern, None, sensitive)
                    self._expression(case.guard)
                    if self._expression_definitely_terminates(case.guard):
                        if _pattern_is_irrefutable(case.pattern):
                            residual = None
                            break
                        continue
                    flow = self._statements(case.body)
                    absorb(flow)
                    normal.extend(flow.normal)
                    if case.guard is None and _pattern_is_irrefutable(case.pattern):
                        residual = None
                if residual is not None:
                    normal.append(residual)
                if not continue_from(normal):
                    return successors
                continue
            if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
                definition_marker = _definition_point_marker(statement)
                decorator_values: list[tuple[str | None, bool]] = []
                for expression in statement.decorator_list:
                    decorator_values.append(self._expression(expression))
                    if self._expression_definitely_terminates(expression):
                        return successors
                for expression in statement.args.defaults:
                    self._expression(expression)
                    if self._expression_definitely_terminates(expression):
                        return successors
                for expression in statement.args.kw_defaults:
                    self._expression(expression)
                    if self._expression_definitely_terminates(expression):
                        return successors
                helper = _SensitivePreclassifier(
                    self.bindings,
                    self.budget,
                    self.helper_returns,
                    self.helper_raises,
                    _exception_name_scope(
                        statement,
                        self.module_bound_names,
                        self.exception_scope.enclosing_names,
                    ),
                    self.module_bound_names,
                    self.helper_summaries,
                    _lexical_binding_scope(statement),
                    self.enclosing_bound_names,
                )
                helper._statements(statement.body)
                if helper.return_values:
                    qualified_values = {value[0] for value in helper.return_values}
                    returned_qualified = (
                        next(iter(qualified_values))
                        if len(qualified_values) == 1
                        else None
                    )
                    self.helper_returns[definition_marker] = (
                        returned_qualified,
                        any(value[1] for value in helper.return_values),
                    )
                self.helper_raises.pop(statement.name, None)
                self.helper_raises.pop(definition_marker, None)
                self.helper_summaries.pop(statement.name, None)
                self.helper_summaries.pop(definition_marker, None)
                summary = _bounded_callable_summary(
                    statement,
                    helper.exception_scope,
                )
                if summary is not None:
                    self.helper_summaries[definition_marker] = summary
                installed_name: str | None = definition_marker
                installed_sensitive = False
                for decorator_name, decorator_sensitive in reversed(
                    decorator_values
                ):
                    installed_sensitive |= decorator_sensitive
                    decorator_summary = self.helper_summaries.get(
                        decorator_name or ""
                    )
                    if decorator_summary is not None:
                        synthetic = ast.Call(
                            func=ast.Name(id=decorator_name or "decorator"),
                            args=[ast.Name(id=statement.name)],
                            keywords=[],
                        )
                        application_shape = _bounded_call_shape(
                            synthetic,
                            decorator_summary,
                        )
                        if application_shape == "invalid":
                            self._record_throw_state("TypeError", True)
                            return successors
                        if (
                            application_shape == "valid"
                            and decorator_summary.exception_tag is not None
                        ):
                            self._record_throw_state(
                                decorator_summary.exception_tag,
                                True,
                            )
                            return successors
                    returned = self.helper_returns.get(decorator_name or "")
                    if returned is None:
                        installed_name = None
                    else:
                        installed_name, returned_sensitive = returned
                        installed_sensitive |= returned_sensitive
                if decorator_values:
                    self.helper_summaries.pop(statement.name, None)
                self._bind(
                    ast.Name(id=statement.name),
                    installed_name,
                    installed_sensitive,
                )
                continue
            if isinstance(statement, ast.ClassDef):
                for expression in (*statement.decorator_list, *statement.bases):
                    self._expression(expression)
                    if self._expression_definitely_terminates(expression):
                        return successors
                for keyword in statement.keywords:
                    self._expression(keyword.value)
                    if self._expression_definitely_terminates(keyword.value):
                        return successors
                self._statements(statement.body)
                self._bind(ast.Name(id=statement.name), statement.name, False)
                continue
            if isinstance(statement, ast.Return):
                self.return_values.append(self._expression(statement.value))
                if self._expression_definitely_terminates(statement.value):
                    return successors
                successors.returns.append(self._snapshot())
                return successors
            if isinstance(statement, ast.Raise):
                if statement.exc is None:
                    successors.raises.append(
                        _PreclassifierExceptionalState(
                            self._snapshot(),
                            self._active_exception_tag,
                            True,
                        )
                    )
                    return successors
                outer_throw_states = self._throw_states
                evaluation_throws: list[_PreclassifierExceptionalState] = []
                self._throw_states = evaluation_throws
                try:
                    exception_qualified, _ = self._expression(statement.exc)
                    exception_completed = not self._expression_definitely_terminates(
                        statement.exc
                    )
                    if exception_completed:
                        self._expression(statement.cause)
                finally:
                    self._throw_states = outer_throw_states
                if not exception_completed:
                    successors.raises.extend(evaluation_throws)
                    return successors
                raise_success, raise_error, raise_unknown = (
                    _builtin_exception_constructor_outcome(
                        statement.exc,
                        self.exception_scope,
                    )
                )
                if raise_error is not None and raise_success is None:
                    successors.raises.append(
                        _PreclassifierExceptionalState(
                            self._snapshot(),
                            raise_error,
                            True,
                        )
                    )
                    return successors
                if not self._expression_is_proven_nonthrowing(
                    statement.exc
                ) or not self._expression_is_proven_nonthrowing(
                    statement.cause
                ):
                    successors.raises.extend(
                        _PreclassifierExceptionalState(
                            exceptional.state,
                            None,
                            True,
                        )
                        for exceptional in evaluation_throws
                    )
                    if not evaluation_throws:
                        successors.raises.append(
                            _PreclassifierExceptionalState(
                                self._snapshot(),
                                None,
                                True,
                            )
                        )
                cause_validation = self._cause_validation(statement.cause)
                if cause_validation in {"invalid", "unknown"}:
                    successors.raises.append(
                        _PreclassifierExceptionalState(
                            self._snapshot(),
                            "TypeError",
                            True,
                        )
                    )
                if cause_validation == "invalid":
                    return successors
                exception_expression = statement.exc
                if isinstance(exception_expression, ast.Call):
                    exception_expression = exception_expression.func
                instance_prefix = "__exception_instance__:"
                instance_tag = (
                    exception_qualified.removeprefix(instance_prefix)
                    if exception_qualified is not None
                    and exception_qualified.startswith(instance_prefix)
                    else None
                )
                if instance_tag == "unknown":
                    instance_tag = None
                successors.raises.append(
                    _PreclassifierExceptionalState(
                        self._snapshot(),
                        instance_tag
                        or raise_success
                        or self._exception_name(exception_expression),
                        True,
                    )
                )
                return successors
            self._expression(statement)
            if isinstance(statement, ast.Break):
                successors.breaks.append(self._snapshot())
                return successors
            if isinstance(statement, ast.Continue):
                successors.continues.append(self._snapshot())
                return successors
        successors.normal.append(self._snapshot())
        return successors

    def classify(self, statements: Sequence[ast.stmt]) -> set[int]:
        self._statements(statements)
        return self.calls


def _preclassified_sensitive_calls(
    statements: Sequence[ast.stmt],
    aliases: Mapping[str, str],
    budget: _AnalysisBudget,
    helper_definitions: Mapping[
        str,
        ast.FunctionDef | ast.AsyncFunctionDef,
    ],
    *,
    scope_node: ast.FunctionDef | ast.AsyncFunctionDef | None = None,
    module_bound_names: Iterable[str] = (),
    enclosing_names: Iterable[str] = (),
    enclosing_names_by_node: Mapping[int, frozenset[str]] | None = None,
    entry_bound_unknown_names: Iterable[str] = (),
) -> set[int]:
    retained_module_bound_names = frozenset(module_bound_names)
    retained_enclosing_names = frozenset(enclosing_names)
    if scope_node is not None:
        retained_enclosing_names = frozenset(
            set(retained_enclosing_names)
            | set(
                _derived_enclosing_binding_markers(
                    scope_node,
                    helper_definitions.values(),
                )
            )
        )
    retained_enclosing_by_node = enclosing_names_by_node or {}
    helper_returns: dict[str, tuple[str | None, bool]] = {}
    helper_raises: dict[str, str] = {}
    helper_summaries: dict[str, _BoundedCallableSummary] = {}
    local_definition_ids = {
        id(candidate)
        for statement in statements
        for candidate in ast.walk(statement)
        if isinstance(candidate, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    for name, definition in helper_definitions.items():
        if id(definition) in local_definition_ids:
            continue
        definition_scope = _exception_name_scope(
            definition,
            retained_module_bound_names,
            retained_enclosing_by_node.get(id(definition), frozenset()),
        )
        summary = _bounded_callable_summary(definition, definition_scope)
        if summary is not None:
            helper_summaries[name] = summary
        helper = _SensitivePreclassifier(
            aliases,
            budget,
            helper_returns,
            helper_raises,
            definition_scope,
            retained_module_bound_names,
            lexical_scope=_lexical_binding_scope(definition),
            enclosing_bound_names=retained_enclosing_by_node.get(
                id(definition),
                frozenset(),
            ),
        )
        helper._statements(definition.body)
        for nested_name, nested_summary in helper.helper_summaries.items():
            helper_summaries.setdefault(nested_name, nested_summary)
        for nested_name, nested_return in helper.helper_returns.items():
            helper_returns.setdefault(nested_name, nested_return)
        if not helper.return_values:
            continue
        qualified_values = {value[0] for value in helper.return_values}
        helper_returns[name] = (
            (
                next(iter(qualified_values))
                if len(qualified_values) == 1
                else None
            ),
            any(value[1] for value in helper.return_values),
        )
    classifier = _SensitivePreclassifier(
        aliases,
        budget,
        helper_returns,
        helper_raises,
        _exception_name_scope(
            scope_node,
            retained_module_bound_names,
            retained_enclosing_names,
        ),
        retained_module_bound_names,
        helper_summaries,
        _lexical_binding_scope(scope_node),
        retained_enclosing_names,
    )
    for name in entry_bound_unknown_names:
        classifier.bindings[name] = "__bound_unknown__"
        classifier.tainted.discard(name)
    return classifier.classify(statements)


@dataclass(slots=True)
class _ReviewFlow:
    aliases_by_call: dict[int, dict[str, str]]
    assignments_by_call: dict[int, dict[str, ast.expr]]
    environments_by_call: dict[
        int,
        tuple[dict[str, str], list[str], str | None],
    ]
    blockers_by_call: dict[int, str]
    iterator_bounds: dict[int, int | None]
    callables_by_call: dict[int, str]
    standalone_blockers: list[tuple[ast.AST, str]]
    receiver_attributes: dict[int, ast.Attribute] = field(default_factory=dict)
    consumed_local_generator_calls: set[int] = field(default_factory=set)
    local_generator_consumption_modes: dict[int, set[str]] = field(
        default_factory=dict
    )
    proved_non_sensitive_calls: set[int] = field(default_factory=set)
    implicit_blocked_calls: set[int] = field(default_factory=set)
    implicit_protocol_events: list[
        tuple[
            ast.AST,
            _ImplicitClassDescriptor,
            frozenset[str],
            str,
        ]
    ] = field(default_factory=list)


def _trivial_helper_return(
    definition: ast.FunctionDef | ast.AsyncFunctionDef,
    aliases: Mapping[str, str],
    budget: _AnalysisBudget,
) -> _FlowValue | None:
    returns = [
        candidate
        for statement in definition.body
        for candidate in _metered_ast_walk(statement, budget)
        if isinstance(candidate, ast.Return)
    ]
    if len(returns) != 1:
        return None
    returned = returns[0].value
    if returned is None:
        return _FlowValue("scalar", None)
    qualified = _resolved_qualified_name(returned, aliases)
    if qualified is not None:
        return _flow_qname(qualified)
    if isinstance(returned, ast.Constant):
        return _FlowValue("scalar", returned.value)
    if isinstance(returned, (ast.Tuple, ast.List, ast.Set)):
        items: list[_FlowValue] = []
        for item in returned.elts:
            qualified = _resolved_qualified_name(item, aliases)
            if qualified is not None:
                items.append(_flow_qname(qualified))
            elif isinstance(item, ast.Constant):
                items.append(_FlowValue("scalar", item.value))
            else:
                items.append(
                    _flow_unknown(
                        "helper return element is dynamically unresolved",
                        sensitive=_contains_sensitive_runtime(item, budget),
                    )
                )
        return _FlowValue(
            "sequence",
            tuple(items),
            mutable_collection=isinstance(returned, ast.List),
            mutable_collection_identity=(
                id(returned) if isinstance(returned, ast.List) else None
            ),
        )
    if isinstance(returned, ast.Dict):
        items: list[tuple[object, _FlowValue]] = []
        for key, value in zip(returned.keys, returned.values, strict=True):
            if not isinstance(key, ast.Constant) or not isinstance(
                value,
                ast.Constant,
            ):
                return None
            items.append((key.value, _FlowValue("scalar", value.value)))
        return _FlowValue("mapping", tuple(items))
    return None


def _flow_qname(name: str) -> _FlowValue:
    sensitive = (
        name in _SUBPROCESS_FUNCTIONS
        or _is_sensitive_namespace(name)
    )
    return _FlowValue("qname", name, sensitive)


def _flow_unknown(reason: str, *, sensitive: bool = False) -> _FlowValue:
    return _FlowValue("unknown", None, sensitive, reason)


def _flow_is_sensitive(value: _FlowValue) -> bool:
    if value.sensitive:
        return True
    if value.kind == "starred_argument":
        return (
            isinstance(value.value, _FlowValue)
            and _flow_is_sensitive(value.value)
        )
    if value.kind in {"sequence", "slice"}:
        return any(_flow_is_sensitive(item) for item in value.value)
    if value.kind == "mapping":
        return any(_flow_is_sensitive(item) for _, item in value.value)
    if value.kind == "mapping_keys":
        return any(
            _flow_is_sensitive(key) or _flow_is_sensitive(item)
            for key, item in value.value
        )
    if value.kind == "deferred_generator_container_merged":
        return any(
            _flow_is_sensitive(item)
            for item in value.value
            if isinstance(item, _FlowValue)
        )
    return False


def _flow_may_be_unittest_receiver(value: _FlowValue) -> bool:
    if value.kind in {"unittest_receiver", "maybe_unittest_receiver"}:
        return True
    if value.kind == "maybe_unbound":
        return any(
            _flow_may_be_unittest_receiver(candidate)
            for candidate in value.value
            if isinstance(candidate, _FlowValue)
        )
    return False


def _flow_contains_unittest_receiver(value: _FlowValue) -> bool:
    pending = [value]
    while pending:
        candidate = pending.pop()
        if _flow_may_be_unittest_receiver(candidate):
            return True
        if candidate.kind == "sequence":
            pending.extend(candidate.value)
        elif candidate.kind == "mapping":
            pending.extend(item for _, item in candidate.value)
        elif candidate.kind == "mapping_keys":
            pending.extend(
                item
                for key, value in candidate.value
                for item in (key, value)
            )
    return False


_IMPLICIT_PROTOCOL_METHODS = {
    "constructor": frozenset({"__new__", "__init__", "__del__"}),
    "context": frozenset({"__enter__", "__exit__"}),
    "async_context": frozenset({"__aenter__", "__aexit__"}),
    "iteration": frozenset({"__iter__", "__next__", "__getitem__"}),
    "iterator_factory": frozenset({"__iter__", "__getitem__"}),
    "reverse_iteration": frozenset({
        "__reversed__", "__len__", "__getitem__",
    }),
    "async_iteration": frozenset({"__aiter__", "__anext__"}),
    "truth": frozenset({"__bool__", "__len__"}),
    "call": frozenset({"__call__"}),
    "item_load": frozenset({"__getitem__"}),
    "item_store": frozenset({"__setitem__"}),
    "item_delete": frozenset({"__delitem__"}),
    "attribute_load": frozenset({"__getattribute__", "__getattr__", "__get__"}),
    "attribute_store": frozenset({"__setattr__", "__set__"}),
    "attribute_delete": frozenset({"__delattr__", "__delete__"}),
    "await": frozenset({"__await__"}),
    "format": frozenset({"__format__", "__str__", "__repr__"}),
    "absolute": frozenset({"__abs__"}),
    "float": frozenset({"__float__", "__index__"}),
    "hash": frozenset({"__hash__"}),
    "integer": frozenset({"__int__", "__index__"}),
    "index": frozenset({"__index__"}),
    "comparison": frozenset({
        "__lt__", "__le__", "__eq__", "__ne__", "__gt__", "__ge__",
        "__contains__",
    }),
    "binary": frozenset({
        "__add__", "__radd__", "__iadd__",
        "__sub__", "__rsub__", "__isub__",
        "__mul__", "__rmul__", "__imul__",
        "__matmul__", "__rmatmul__", "__imatmul__",
        "__truediv__", "__rtruediv__", "__itruediv__",
        "__floordiv__", "__rfloordiv__", "__ifloordiv__",
        "__mod__", "__rmod__", "__imod__",
        "__pow__", "__rpow__", "__ipow__",
        "__lshift__", "__rlshift__", "__ilshift__",
        "__rshift__", "__rrshift__", "__irshift__",
        "__and__", "__rand__", "__iand__",
        "__xor__", "__rxor__", "__ixor__",
        "__or__", "__ror__", "__ior__",
    }),
    "unary": frozenset({"__pos__", "__neg__", "__invert__"}),
    "class_construction": frozenset({
        "__prepare__", "__new__", "__init__", "__init_subclass__",
        "__set_name__", "__mro_entries__", "__class_getitem__",
    }),
}
_IMPLICIT_CLASS_METHOD_NAMES = frozenset().union(
    *_IMPLICIT_PROTOCOL_METHODS.values()
)

_BINARY_PROTOCOL_METHODS: tuple[
    tuple[type[ast.operator], str, str, str], ...
] = (
    (ast.Add, "__add__", "__radd__", "__iadd__"),
    (ast.Sub, "__sub__", "__rsub__", "__isub__"),
    (ast.Mult, "__mul__", "__rmul__", "__imul__"),
    (ast.MatMult, "__matmul__", "__rmatmul__", "__imatmul__"),
    (ast.Div, "__truediv__", "__rtruediv__", "__itruediv__"),
    (ast.FloorDiv, "__floordiv__", "__rfloordiv__", "__ifloordiv__"),
    (ast.Mod, "__mod__", "__rmod__", "__imod__"),
    (ast.Pow, "__pow__", "__rpow__", "__ipow__"),
    (ast.LShift, "__lshift__", "__rlshift__", "__ilshift__"),
    (ast.RShift, "__rshift__", "__rrshift__", "__irshift__"),
    (ast.BitAnd, "__and__", "__rand__", "__iand__"),
    (ast.BitXor, "__xor__", "__rxor__", "__ixor__"),
    (ast.BitOr, "__or__", "__ror__", "__ior__"),
)

_UNARY_PROTOCOL_METHODS: tuple[
    tuple[type[ast.unaryop], frozenset[str]], ...
] = (
    (ast.UAdd, frozenset({"__pos__"})),
    (ast.USub, frozenset({"__neg__"})),
    (ast.Invert, frozenset({"__invert__"})),
    (ast.Not, _IMPLICIT_PROTOCOL_METHODS["truth"]),
)

_COMPARISON_PROTOCOL_METHODS: tuple[
    tuple[type[ast.cmpop], frozenset[str], frozenset[str]], ...
] = (
    (ast.Lt, frozenset({"__lt__"}), frozenset({"__gt__"})),
    (ast.LtE, frozenset({"__le__"}), frozenset({"__ge__"})),
    (ast.Eq, frozenset({"__eq__"}), frozenset({"__eq__"})),
    (ast.NotEq, frozenset({"__ne__"}), frozenset({"__ne__"})),
    (ast.Gt, frozenset({"__gt__"}), frozenset({"__lt__"})),
    (ast.GtE, frozenset({"__ge__"}), frozenset({"__le__"})),
)

_BUILTIN_IMPLICIT_PROTOCOLS: Mapping[str, frozenset[str]] = MappingProxyType({
    "abs": _IMPLICIT_PROTOCOL_METHODS["absolute"],
    "all": _IMPLICIT_PROTOCOL_METHODS["iteration"],
    "any": _IMPLICIT_PROTOCOL_METHODS["iteration"],
    "bool": _IMPLICIT_PROTOCOL_METHODS["truth"],
    "dict": _IMPLICIT_PROTOCOL_METHODS["iteration"],
    "format": _IMPLICIT_PROTOCOL_METHODS["format"],
    "float": _IMPLICIT_PROTOCOL_METHODS["float"],
    "frozenset": _IMPLICIT_PROTOCOL_METHODS["iteration"],
    "getattr": _IMPLICIT_PROTOCOL_METHODS["attribute_load"],
    "hash": _IMPLICIT_PROTOCOL_METHODS["hash"],
    "int": _IMPLICIT_PROTOCOL_METHODS["integer"],
    "iter": _IMPLICIT_PROTOCOL_METHODS["iterator_factory"],
    "len": frozenset({"__len__"}),
    "list": _IMPLICIT_PROTOCOL_METHODS["iteration"],
    "max": _IMPLICIT_PROTOCOL_METHODS["iteration"],
    "min": _IMPLICIT_PROTOCOL_METHODS["iteration"],
    "next": frozenset({"__next__"}),
    "operator.index": _IMPLICIT_PROTOCOL_METHODS["index"],
    "repr": frozenset({"__repr__"}),
    "reversed": _IMPLICIT_PROTOCOL_METHODS["reverse_iteration"],
    "set": _IMPLICIT_PROTOCOL_METHODS["iteration"],
    "sorted": _IMPLICIT_PROTOCOL_METHODS["iteration"],
    "str": frozenset({"__str__"}),
    "sum": _IMPLICIT_PROTOCOL_METHODS["iteration"],
    "tuple": _IMPLICIT_PROTOCOL_METHODS["iteration"],
})

_CALL_ARGUMENT_IMPLICIT_PROTOCOLS: Mapping[
    str,
    tuple[tuple[int, frozenset[str]], ...],
] = MappingProxyType({
    "heapq.heappush": ((1, frozenset({"__lt__"})),),
})

_CALL_CONTAINER_ELEMENT_IMPLICIT_PROTOCOLS: Mapping[
    str,
    tuple[tuple[int, frozenset[str]], ...],
] = MappingProxyType({
    "all": ((0, _IMPLICIT_PROTOCOL_METHODS["truth"]),),
    "any": ((0, _IMPLICIT_PROTOCOL_METHODS["truth"]),),
    "frozenset": (
        (0, _IMPLICIT_PROTOCOL_METHODS["hash"]),
        (0, frozenset({"__eq__"})),
    ),
    "heapq.heappush": ((0, frozenset({"__gt__"})),),
    "set": (
        (0, _IMPLICIT_PROTOCOL_METHODS["hash"]),
        (0, frozenset({"__eq__"})),
    ),
    "sorted": ((0, _IMPLICIT_PROTOCOL_METHODS["comparison"]),),
})

_CALL_KEYWORD_IMPLICIT_PROTOCOLS: Mapping[
    str,
    Mapping[str, frozenset[str]],
] = MappingProxyType({
    "sorted": MappingProxyType({
        "reverse": _IMPLICIT_PROTOCOL_METHODS["truth"],
    }),
})


def _binary_protocol_methods(
    operator: ast.operator,
) -> tuple[frozenset[str], frozenset[str], frozenset[str]]:
    for operator_type, direct, reflected, inplace in _BINARY_PROTOCOL_METHODS:
        if isinstance(operator, operator_type):
            return (
                frozenset({direct}),
                frozenset({reflected}),
                frozenset({inplace, direct}),
            )
    return frozenset(), frozenset(), frozenset()


def _unary_protocol_methods(operator: ast.unaryop) -> frozenset[str]:
    return next(
        (
            methods
            for operator_type, methods in _UNARY_PROTOCOL_METHODS
            if isinstance(operator, operator_type)
        ),
        frozenset(),
    )


def _comparison_protocol_methods(
    operator: ast.cmpop,
) -> tuple[frozenset[str], frozenset[str]]:
    return next(
        (
            (left, right)
            for operator_type, left, right in _COMPARISON_PROTOCOL_METHODS
            if isinstance(operator, operator_type)
        ),
        (frozenset(), frozenset()),
    )


def _class_namespace_assignment_names(
    statements: Sequence[ast.stmt],
) -> frozenset[str]:
    """Collect class-body stores without descending into deferred scopes."""

    names: set[str] = set()
    for statement in statements:
        targets: Sequence[ast.AST] = ()
        if isinstance(statement, ast.Assign):
            targets = statement.targets
        elif isinstance(statement, (ast.AnnAssign, ast.AugAssign)):
            targets = (statement.target,)
        elif isinstance(statement, (ast.For, ast.AsyncFor)):
            targets = (statement.target,)
        elif isinstance(statement, (ast.With, ast.AsyncWith)):
            targets = tuple(
                item.optional_vars
                for item in statement.items
                if item.optional_vars is not None
            )
        elif isinstance(statement, ast.Delete):
            targets = statement.targets
        names.update(
            set().union(*(_python_bound_names(target) for target in targets))
            if targets
            else ()
        )
        suites: list[Sequence[ast.stmt]] = []
        if isinstance(statement, ast.If):
            suites.extend((statement.body, statement.orelse))
        elif isinstance(statement, (ast.For, ast.AsyncFor, ast.While)):
            suites.extend((statement.body, statement.orelse))
        elif isinstance(statement, (ast.With, ast.AsyncWith)):
            suites.append(statement.body)
        else:
            try_types = (ast.Try,)
            if hasattr(ast, "TryStar"):
                try_types = (*try_types, ast.TryStar)
            if isinstance(statement, try_types):
                suites.extend(
                    (statement.body, statement.orelse, statement.finalbody)
                )
                suites.extend(handler.body for handler in statement.handlers)
            elif isinstance(statement, ast.Match):
                suites.extend(case.body for case in statement.cases)
        for suite in suites:
            names.update(_class_namespace_assignment_names(suite))
    return frozenset(names)


def _implicit_method_is_sensitive(
    definition: ast.FunctionDef | ast.AsyncFunctionDef,
    aliases: Mapping[str, str],
    module_assignments: Mapping[str, ast.expr],
    budget: _AnalysisBudget,
    sensitive_names: frozenset[str] = frozenset(),
) -> bool:
    if _contains_sensitive_runtime(definition, budget):
        return True
    pending_assignments = dict(module_assignments)
    for candidate in _metered_ast_walk(definition, budget):
        if not isinstance(candidate, (ast.Name, ast.Attribute)):
            continue
        if not isinstance(candidate.ctx, ast.Load):
            continue
        if isinstance(candidate, ast.Name) and candidate.id in sensitive_names:
            return True
        qualified = _resolved_qualified_name(candidate, aliases)
        if qualified is not None and _is_sensitive_namespace(qualified):
            return True
        if isinstance(candidate, ast.Name) and candidate.id in pending_assignments:
            assigned = pending_assignments[candidate.id]
            assigned_qualified = _resolved_qualified_name(assigned, aliases)
            if (
                assigned_qualified is not None
                and _is_sensitive_namespace(assigned_qualified)
            ):
                return True
    return False


def _implicit_descriptor_mro(
    bases: Sequence[_ImplicitClassDescriptor],
) -> tuple[_ImplicitClassDescriptor, ...]:
    """Return the bounded C3 order for locally modeled class descriptors."""

    memo: dict[int, tuple[_ImplicitClassDescriptor, ...]] = {}

    def linearize(
        descriptor: _ImplicitClassDescriptor,
    ) -> tuple[_ImplicitClassDescriptor, ...]:
        retained = memo.get(id(descriptor))
        if retained is not None:
            return retained
        tail = merge(descriptor.base_descriptors)
        result = (descriptor, *tail)
        memo[id(descriptor)] = result
        return result

    def merge(
        supplied_bases: Sequence[_ImplicitClassDescriptor],
    ) -> tuple[_ImplicitClassDescriptor, ...]:
        sequences = [list(linearize(base)) for base in supplied_bases]
        sequences.append(list(supplied_bases))
        result: list[_ImplicitClassDescriptor] = []
        while any(sequences):
            sequences = [sequence for sequence in sequences if sequence]
            selected: _ImplicitClassDescriptor | None = None
            for sequence in sequences:
                candidate = sequence[0]
                if not any(
                    any(item is candidate for item in other[1:])
                    for other in sequences
                ):
                    selected = candidate
                    break
            if selected is None:
                for sequence in sequences:
                    for candidate in sequence:
                        if not any(item is candidate for item in result):
                            result.append(candidate)
                break
            if not any(item is selected for item in result):
                result.append(selected)
            for sequence in sequences:
                if sequence and sequence[0] is selected:
                    sequence.pop(0)
        return tuple(result)

    return merge(tuple(bases))


def _implicit_method_is_proven_not_to_return_not_implemented(
    definition: ast.FunctionDef | ast.AsyncFunctionDef,
) -> bool:
    """Recognize the narrow return forms that cannot request reflected dispatch."""

    pending: list[ast.AST] = list(definition.body)
    while pending:
        candidate = pending.pop()
        if isinstance(candidate, ast.Return):
            if candidate.value is None:
                continue
            try:
                ast.literal_eval(candidate.value)
            except (ValueError, TypeError, SyntaxError, MemoryError, RecursionError):
                return False
            continue
        if isinstance(
            candidate,
            (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef),
        ):
            continue
        pending.extend(ast.iter_child_nodes(candidate))
    return True


def _compose_implicit_class_descriptor(
    *,
    name: str,
    base_descriptors: Sequence[_ImplicitClassDescriptor],
    local_overrides: frozenset[str],
    local_sensitive_methods: frozenset[str],
    local_defined_methods: frozenset[str],
    local_method_slots: Sequence[
        tuple[str, ast.FunctionDef | ast.AsyncFunctionDef]
    ],
    local_descriptor_members: Sequence[
        tuple[str, _ImplicitClassDescriptor]
    ],
    exact_init_review: bool,
) -> _ImplicitClassDescriptor:
    inherited_slots: dict[
        str,
        ast.FunctionDef | ast.AsyncFunctionDef,
    ] = {}
    inherited_members: dict[str, _ImplicitClassDescriptor] = {}
    inherited_sensitive: set[str] = set()
    inherited_defined: set[str] = set()
    inherited_member_names: set[str] = set()
    for descriptor in _implicit_descriptor_mro(base_descriptors):
        local_slots = dict(descriptor.local_method_slots)
        local_members = dict(descriptor.local_descriptor_members)
        for method_name in descriptor.local_overrides & _IMPLICIT_CLASS_METHOD_NAMES:
            if method_name in inherited_defined:
                continue
            inherited_defined.add(method_name)
            if method_name in descriptor.local_sensitive_methods:
                inherited_sensitive.add(method_name)
            method = local_slots.get(method_name)
            if method is not None:
                inherited_slots[method_name] = method
        for member_name in descriptor.local_overrides:
            if member_name in inherited_member_names:
                continue
            inherited_member_names.add(member_name)
            member = local_members.get(member_name)
            if member is not None:
                inherited_members[member_name] = member
    for overridden in local_overrides:
        inherited_slots.pop(overridden, None)
        inherited_members.pop(overridden, None)
        inherited_sensitive.discard(overridden)
        inherited_defined.discard(overridden)
    retained_slots = {
        **inherited_slots,
        **dict(local_method_slots),
    }
    retained_members = {
        **inherited_members,
        **dict(local_descriptor_members),
    }
    sensitive_methods = inherited_sensitive | set(local_sensitive_methods)
    defined_methods = inherited_defined | set(local_defined_methods)
    return _ImplicitClassDescriptor(
        name=name,
        sensitive_methods=frozenset(sensitive_methods),
        defined_methods=frozenset(defined_methods),
        custom_new="__new__" in defined_methods,
        exact_init_review=exact_init_review,
        methods=tuple(retained_slots.values()),
        method_slots=tuple(retained_slots.items()),
        descriptor_members=tuple(sorted(retained_members.items())),
        base_descriptors=tuple(base_descriptors),
        local_overrides=local_overrides,
        local_sensitive_methods=local_sensitive_methods,
        local_defined_methods=local_defined_methods,
        local_method_slots=tuple(local_method_slots),
        local_descriptor_members=tuple(sorted(local_descriptor_members)),
        proven_non_not_implemented_methods=frozenset(
            method_name
            for method_name, method in retained_slots.items()
            if _implicit_method_is_proven_not_to_return_not_implemented(method)
        ),
    )


def _implicit_class_descriptor(
    name: str,
    methods: Iterable[ast.FunctionDef | ast.AsyncFunctionDef],
    aliases: Mapping[str, str],
    module_assignments: Mapping[str, ast.expr],
    budget: _AnalysisBudget,
    *,
    exact_init_review: bool = False,
    proven_sensitive_methods: Iterable[str] = (),
    sensitive_names: frozenset[str] = frozenset(),
    descriptor_members: Iterable[
        tuple[str, _ImplicitClassDescriptor]
    ] = (),
    inherited_descriptors: Iterable[_ImplicitClassDescriptor] = (),
    overridden_names: frozenset[str] = frozenset(),
) -> _ImplicitClassDescriptor:
    supplied = tuple(methods)
    inherited = tuple(inherited_descriptors)
    retained = tuple(
        method
        for method in supplied
        if method.name in _IMPLICIT_CLASS_METHOD_NAMES
    )
    local_members = dict(descriptor_members)
    for method in supplied:
        if not any(
            _resolved_qualified_name(decorator, aliases) == "property"
            for decorator in method.decorator_list
        ):
            continue
        property_sensitive = _implicit_method_is_sensitive(
            method,
            aliases,
            module_assignments,
            budget,
            sensitive_names,
        )
        local_members[method.name] = _ImplicitClassDescriptor(
            name=f"{name}.{method.name}",
            sensitive_methods=(
                frozenset({"__get__"})
                if property_sensitive
                else frozenset()
            ),
            defined_methods=frozenset({"__get__"}),
            methods=(method,),
            method_slots=(("__get__", method),),
            local_overrides=frozenset({"__get__"}),
            local_sensitive_methods=(
                frozenset({"__get__"})
                if property_sensitive
                else frozenset()
            ),
            local_defined_methods=frozenset({"__get__"}),
            local_method_slots=(("__get__", method),),
        )
    local_sensitive = frozenset(
        method.name
        for method in retained
        if _implicit_method_is_sensitive(
            method,
            aliases,
            module_assignments,
            budget,
            sensitive_names,
        )
    )
    local_slots = tuple((method.name, method) for method in retained)
    local_defined = (
        frozenset(
            overridden_names & _IMPLICIT_CLASS_METHOD_NAMES
        )
        | frozenset(method.name for method in retained)
    )
    return _compose_implicit_class_descriptor(
        name=name,
        base_descriptors=inherited,
        local_overrides=overridden_names,
        local_sensitive_methods=(
            frozenset(proven_sensitive_methods) | local_sensitive
        ),
        local_defined_methods=local_defined,
        local_method_slots=local_slots,
        local_descriptor_members=tuple(local_members.items()),
        exact_init_review=exact_init_review,
    )


def _flow_contains_deferred_generator(value: _FlowValue) -> bool:
    if value.kind in {
        "generator",
        "deferred_generator_merged",
        "deferred_local_generator",
    }:
        return True
    if value.kind in {
        "sequence",
        "maybe_unbound",
        "deferred_generator_container_merged",
    }:
        return any(
            _flow_contains_deferred_generator(item)
            for item in value.value
            if isinstance(item, _FlowValue)
        )
    if value.kind == "mapping":
        return any(
            _flow_contains_deferred_generator(item)
            for _, item in value.value
            if isinstance(item, _FlowValue)
        )
    if value.kind == "mapping_keys":
        return any(
            _flow_contains_deferred_generator(candidate)
            for key, item in value.value
            for candidate in (key, item)
        )
    if value.kind == "starred_argument" and isinstance(
        value.value,
        _FlowValue,
    ):
        return _flow_contains_deferred_generator(value.value)
    return False


def _rewrite_implicit_class_descriptor(
    value: _FlowValue,
    previous: _ImplicitClassDescriptor,
    updated: _ImplicitClassDescriptor,
    *,
    _descriptor_memo: dict[int, _ImplicitClassDescriptor] | None = None,
) -> _FlowValue:
    """Rewrite one branch-local immutable class descriptor everywhere reachable."""

    descriptor_memo = (
        {} if _descriptor_memo is None else _descriptor_memo
    )
    descriptor_memo[id(previous)] = updated

    def rewrite_descriptor(
        descriptor: _ImplicitClassDescriptor,
    ) -> _ImplicitClassDescriptor:
        retained = descriptor_memo.get(id(descriptor))
        if retained is not None:
            return retained
        rewritten_bases = tuple(
            rewrite_descriptor(base) for base in descriptor.base_descriptors
        )
        rewritten_local_members = tuple(
            (name, rewrite_descriptor(member))
            for name, member in descriptor.local_descriptor_members
        )
        if all(
            rewritten is original
            for rewritten, original in zip(
                rewritten_bases,
                descriptor.base_descriptors,
                strict=True,
            )
        ) and all(
            rewritten is original
            for (_name, rewritten), (_old_name, original) in zip(
                rewritten_local_members,
                descriptor.local_descriptor_members,
                strict=True,
            )
        ):
            descriptor_memo[id(descriptor)] = descriptor
            return descriptor
        rewritten = _compose_implicit_class_descriptor(
            name=descriptor.name,
            base_descriptors=rewritten_bases,
            local_overrides=descriptor.local_overrides,
            local_sensitive_methods=descriptor.local_sensitive_methods,
            local_defined_methods=descriptor.local_defined_methods,
            local_method_slots=descriptor.local_method_slots,
            local_descriptor_members=rewritten_local_members,
            exact_init_review=descriptor.exact_init_review,
        )
        descriptor_memo[id(descriptor)] = rewritten
        return rewritten

    def rewrite_value(item: _FlowValue) -> _FlowValue:
        return _rewrite_implicit_class_descriptor(
            item,
            previous,
            updated,
            _descriptor_memo=descriptor_memo,
        )

    def rewrite_factory(
        factory: _DeferredLocalGeneratorFactory,
    ) -> _DeferredLocalGeneratorFactory:
        defaults = tuple(
            (name, rewrite_value(item))
            for name, item in factory.defaults
        )
        return replace(factory, defaults=defaults) if defaults != factory.defaults else factory

    if value.kind in {"implicit_class", "implicit_class_instance"} and isinstance(
        value.value,
        _ImplicitClassDescriptor,
    ):
        descriptor = rewrite_descriptor(value.value)
        if descriptor is value.value:
            return value
        return replace(
            value,
            value=descriptor,
            sensitive=bool(descriptor.sensitive_methods),
            reason=(
                "implicit class protocol execution is dynamically unresolved"
                if descriptor.sensitive_methods
                else None
            ),
        )
    if value.kind in {
        "deferred_generator_container_merged",
        "deferred_local_generator_factory_merged",
        "implicit_protocol_merged",
        "maybe_unbound",
        "maybe_unittest_receiver",
        "sequence",
        "slice",
    }:
        rewritten = tuple(
            rewrite_value(item)
            if isinstance(item, _FlowValue)
            else item
            for item in value.value
        )
        return replace(value, value=rewritten) if rewritten != value.value else value
    if value.kind == "mapping":
        rewritten_mapping = tuple(
            (
                key,
                rewrite_value(item),
            )
            for key, item in value.value
        )
        return (
            replace(value, value=rewritten_mapping)
            if rewritten_mapping != value.value
            else value
        )
    if value.kind == "mapping_keys":
        rewritten_mapping = tuple(
            (
                rewrite_value(key),
                rewrite_value(item),
            )
            for key, item in value.value
        )
        return (
            replace(value, value=rewritten_mapping)
            if rewritten_mapping != value.value
            else value
        )
    if value.kind == "starred_argument" and isinstance(value.value, _FlowValue):
        rewritten_item = rewrite_value(value.value)
        return replace(value, value=rewritten_item) if rewritten_item != value.value else value
    if value.kind == "deferred_generator_method" and isinstance(value.value, tuple):
        owner, method_name = value.value
        if isinstance(owner, _FlowValue):
            rewritten_owner = rewrite_value(owner)
            if rewritten_owner != owner:
                return replace(value, value=(rewritten_owner, method_name))
        return value
    if value.kind == "deferred_local_generator_factory" and isinstance(
        value.value,
        _DeferredLocalGeneratorFactory,
    ):
        factory = rewrite_factory(value.value)
        return replace(value, value=factory) if factory != value.value else value
    if value.kind == "deferred_local_generator" and isinstance(
        value.value,
        _DeferredLocalGeneratorState,
    ):
        state = value.value
        factory = rewrite_factory(state.factory)
        bindings = tuple(
            (name, rewrite_value(item))
            for name, item in state.bindings
        )
        frame = tuple(
            (name, rewrite_value(item))
            for name, item in state.frame
        )
        delegate = (
            rewrite_value(state.delegate)
            if state.delegate is not None
            else None
        )
        rewritten_state = replace(
            state,
            factory=factory,
            bindings=bindings,
            frame=frame,
            delegate=delegate,
        )
        return replace(value, value=rewritten_state) if rewritten_state != state else value
    return value


def _flow_contains_deferred_local_generator(value: _FlowValue) -> bool:
    if value.kind == "deferred_local_generator":
        return True
    if value.kind in {
        "deferred_generator_merged",
        "sequence",
        "maybe_unbound",
        "deferred_generator_container_merged",
    }:
        return any(
            _flow_contains_deferred_local_generator(candidate)
            for candidate in value.value
            if isinstance(candidate, _FlowValue)
        )
    if value.kind == "mapping":
        return any(
            _flow_contains_deferred_local_generator(candidate)
            for _, candidate in value.value
            if isinstance(candidate, _FlowValue)
        )
    if value.kind == "mapping_keys":
        return any(
            _flow_contains_deferred_local_generator(candidate)
            for key, item in value.value
            for candidate in (key, item)
        )
    if value.kind == "starred_argument" and isinstance(
        value.value,
        _FlowValue,
    ):
        return _flow_contains_deferred_local_generator(value.value)
    return False


def _deferred_local_generator_creation_ids(value: _FlowValue) -> frozenset[int]:
    if (
        value.kind == "deferred_local_generator"
        and isinstance(value.value, _DeferredLocalGeneratorState)
    ):
        return frozenset({value.value.creation_call_id})
    if value.kind in {
        "deferred_generator_merged",
        "sequence",
        "maybe_unbound",
        "deferred_generator_container_merged",
    }:
        return frozenset().union(*(
            _deferred_local_generator_creation_ids(candidate)
            for candidate in value.value
            if isinstance(candidate, _FlowValue)
        ))
    if value.kind == "mapping":
        return frozenset().union(*(
            _deferred_local_generator_creation_ids(candidate)
            for _, candidate in value.value
            if isinstance(candidate, _FlowValue)
        ))
    if value.kind == "mapping_keys":
        return frozenset().union(*(
            _deferred_local_generator_creation_ids(candidate)
            for key, item in value.value
            for candidate in (key, item)
        ))
    if value.kind == "starred_argument" and isinstance(
        value.value,
        _FlowValue,
    ):
        return _deferred_local_generator_creation_ids(value.value)
    return frozenset()


def _flow_mapping_value(
    value: _FlowValue,
    key: object,
) -> _FlowValue | None:
    if value.kind == "mapping":
        for supplied_key, supplied_value in value.value:
            if supplied_key == key:
                return supplied_value
        return None
    if value.kind == "mapping_keys":
        for supplied_key, supplied_value in value.value:
            if isinstance(key, _FlowValue):
                if supplied_key is key or supplied_key == key:
                    return supplied_value
            elif (
                supplied_key.kind == "scalar"
                and supplied_key.value == key
            ):
                return supplied_value
    return None


def _flow_store_path(
    current: _FlowValue | None,
    path: Sequence[object],
    value: _FlowValue,
) -> _FlowValue:
    if not path:
        return value
    key = path[0]
    existing = current if current is not None else _FlowValue("mapping", ())
    if existing.kind != "mapping":
        if _flow_is_sensitive(existing):
            return _flow_unknown(
                "mixed protected receiver is dynamically unresolved",
                sensitive=True,
            )
        existing = _FlowValue("mapping", ())
    items = dict(existing.value)
    items[key] = _flow_store_path(items.get(key), path[1:], value)
    return _FlowValue("mapping", tuple(items.items()))


def _flow_literal_expression(value: _FlowValue) -> ast.expr | None:
    if value.kind == "scalar":
        supplied = value.value
    elif value.kind == "sequence":
        items = [_flow_literal_expression(item) for item in value.value]
        if any(item is None for item in items):
            return None
        supplied = [ast.literal_eval(item) for item in items]
    elif value.kind == "mapping":
        supplied = {}
        for key, item in value.value:
            expression = _flow_literal_expression(item)
            if expression is None:
                return None
            supplied[key] = ast.literal_eval(expression)
    else:
        return None
    try:
        return ast.parse(repr(supplied), mode="eval").body
    except (SyntaxError, ValueError):
        return None


def _flow_aliases(values: Mapping[str, _FlowValue]) -> dict[str, str]:
    return {
        name: str(value.value)
        for name, value in values.items()
        if value.kind == "qname"
    }


def _deferred_generator_expressions(
    node: ast.GeneratorExp,
) -> tuple[ast.expr, ...]:
    """Return expressions evaluated only when the generator is consumed."""

    deferred: list[ast.expr] = list(node.generators[0].ifs)
    for generator in node.generators[1:]:
        deferred.append(generator.iter)
        deferred.extend(generator.ifs)
    deferred.append(node.elt)
    return tuple(deferred)


def _flow_assignments(values: Mapping[str, _FlowValue]) -> dict[str, ast.expr]:
    assignments: dict[str, ast.expr] = {}
    for name, value in values.items():
        expression = _flow_literal_expression(value)
        if expression is not None:
            assignments[name] = expression
    return assignments


def _merge_flow_values(
    name: str,
    values: Sequence[_FlowValue | None],
) -> _FlowValue:
    if values and all(value == values[0] for value in values):
        return values[0] or _flow_unknown(f"{name} is unbound")
    present = tuple(
        value
        for value in values
        if value is not None and value.kind != "unbound"
    )
    if len(present) != len(values):
        return _FlowValue(
            "maybe_unbound",
            tuple(present),
            any(_flow_is_sensitive(value) for value in present),
            f"{name} is only conditionally bound",
        )
    if any(_flow_may_be_unittest_receiver(value) for value in present):
        return _FlowValue(
            "maybe_unittest_receiver",
            present,
            reason="unittest receiver alias has divergent reaching definitions",
        )
    sequences = tuple(value for value in present if value.kind == "sequence")
    if (
        len(sequences) == len(present)
        and len({len(value.value) for value in sequences}) == 1
    ):
        return _FlowValue(
            "sequence",
            tuple(
                _merge_flow_values(
                    f"{name}[{index}]",
                    tuple(value.value[index] for value in sequences),
                )
                for index in range(len(sequences[0].value))
            ),
            container_kind=(
                sequences[0].container_kind
                if len({value.container_kind for value in sequences}) == 1
                else None
            ),
            mutable_collection=any(
                value.mutable_collection for value in sequences
            ),
            mutable_collection_identity=(
                sequences[0].mutable_collection_identity
                if len({
                    value.mutable_collection_identity for value in sequences
                }) == 1
                else None
            ),
            reason=(
                "mutable collection alias has divergent reaching definitions"
                if len({
                    value.mutable_collection_identity for value in sequences
                }) > 1
                else None
            ),
        )
    mappings = tuple(value for value in present if value.kind == "mapping")
    mapping_keys = tuple(
        tuple(key for key, _ in value.value)
        for value in mappings
    )
    if (
        len(mappings) == len(present)
        and mapping_keys
        and all(keys == mapping_keys[0] for keys in mapping_keys)
    ):
        return _FlowValue(
            "mapping",
            tuple(
                (
                    key,
                    _merge_flow_values(
                        f"{name}[{key!r}]",
                        tuple(value.value[index][1] for value in mappings),
                    ),
                )
                for index, key in enumerate(mapping_keys[0])
            ),
            container_kind=(
                mappings[0].container_kind
                if len({value.container_kind for value in mappings}) == 1
                else None
            ),
            mutable_collection=any(
                value.mutable_collection for value in mappings
            ),
            mutable_collection_identity=(
                mappings[0].mutable_collection_identity
                if len({
                    value.mutable_collection_identity for value in mappings
                }) == 1
                else None
            ),
            reason=(
                "mutable collection alias has divergent reaching definitions"
                if len({
                    value.mutable_collection_identity for value in mappings
                }) > 1
                else None
            ),
        )
    keyed_mappings = tuple(
        value for value in present if value.kind == "mapping_keys"
    )
    if (
        len(keyed_mappings) == len(present)
        and len({len(value.value) for value in keyed_mappings}) == 1
    ):
        return _FlowValue(
            "mapping_keys",
            tuple(
                (
                    _merge_flow_values(
                        f"{name}.key[{index}]",
                        tuple(value.value[index][0] for value in keyed_mappings),
                    ),
                    _merge_flow_values(
                        f"{name}.value[{index}]",
                        tuple(value.value[index][1] for value in keyed_mappings),
                    ),
                )
                for index in range(len(keyed_mappings[0].value))
            ),
            container_kind="dict",
        )
    local_generator_factories = tuple(
        value
        for value in present
        if value.kind in {
            "deferred_local_generator_factory",
            "deferred_local_generator_factory_merged",
        }
    )
    if local_generator_factories:
        candidates: list[_FlowValue] = []
        for value in present:
            if value.kind == "deferred_local_generator_factory_merged":
                candidates.extend(
                    candidate
                    for candidate in value.value
                    if isinstance(candidate, _FlowValue)
                )
            else:
                candidates.append(value)
        return _FlowValue(
            "deferred_local_generator_factory_merged",
            tuple(candidates),
            False,
            "local generator factory has divergent reaching definitions",
        )
    generators = tuple(value for value in present if value.kind == "generator")
    if generators and len(generators) == len(present):
        identities = {
            state.identity
            for value in generators
            if isinstance((state := value.value), _DeferredGeneratorState)
        }
        if len(identities) == 1:
            states = tuple(
                value.value
                for value in generators
                if isinstance(value.value, _DeferredGeneratorState)
            )
            if len(states) == len(generators):
                first = states[0]
                remaining_values = {state.remaining for state in states}
                remaining = (
                    next(iter(remaining_values))
                    if len(remaining_values) == 1
                    else None
                )
                outer_identities = {
                    state.outer_iterator_identity for state in states
                }
                outer_versions = {
                    state.outer_iterator_version for state in states
                }
                return _FlowValue(
                    "generator",
                    replace(
                        first,
                        remaining=remaining,
                        supported=(
                            all(state.supported for state in states)
                            and len(remaining_values) == 1
                            and len(outer_identities) == 1
                            and len(outer_versions) == 1
                        ),
                        outer_iterator_sensitive=any(
                            state.outer_iterator_sensitive for state in states
                        )
                        or len(outer_identities) != 1
                        or len(outer_versions) != 1,
                        outer_iterator_identity=(
                            next(iter(outer_identities))
                            if len(outer_identities) == 1
                            else None
                        ),
                        outer_iterator_version=(
                            next(iter(outer_versions))
                            if len(outer_versions) == 1
                            else max(outer_versions)
                        ),
                    ),
                )
        return _FlowValue(
            "deferred_generator_merged",
            tuple(value.value for value in generators),
            False,
            "deferred generator consumption is dynamically unresolved",
        )
    if generators:
        return _FlowValue(
            "deferred_generator_merged",
            tuple(value.value for value in generators),
            any(
                _flow_is_sensitive(value)
                for value in present
                if value.kind != "generator"
            ),
            "deferred generator consumption is dynamically unresolved",
        )
    if any(_flow_contains_deferred_generator(value) for value in present):
        return _FlowValue(
            "deferred_generator_container_merged",
            present,
            any(_flow_is_sensitive(value) for value in present),
            "deferred generator consumption is dynamically unresolved",
        )
    if any(
        _SourceOrderedResolver._implicit_protocol_descriptors(value)
        for value in present
    ):
        return _FlowValue(
            "implicit_protocol_merged",
            present,
            any(_flow_is_sensitive(value) for value in present),
            "implicit class protocol execution is dynamically unresolved",
        )
    environments = tuple(
        value for value in present if value.kind == "environment"
    )
    if environments:
        owners = {
            value.value.owner
            for value in environments
            if isinstance(value.value, _FlowEnvironment)
        }
        owner = next(iter(owners)) if len(owners) == 1 else name
        poisons = {
            environment.poison
            for value in environments
            if isinstance(
                (environment := value.value),
                _FlowEnvironment,
            )
            and environment.poison is not None
        }
        poison = (
            "subprocess environment exceptional state is ambiguous"
            if "subprocess environment exceptional state is ambiguous" in poisons
            else (
                next(iter(poisons))
                if len(poisons) == 1
                else "subprocess environment branch state is ambiguous"
            )
        )
        return _FlowValue(
            "environment",
            _FlowEnvironment(
                owner,
                poison=poison,
            ),
            reason=poison,
        )
    if any(_flow_is_sensitive(value) for value in present):
        reasons = tuple(
            value.reason
            for value in present
            if value.reason is not None
        )
        if any("callable" in reason for reason in reasons):
            reason = "callable alias is dynamically unresolved"
        elif any("dynamic sensitive" in reason for reason in reasons):
            reason = "dynamic sensitive call target is unresolved"
        else:
            reason = "mixed protected receiver is dynamically unresolved"
        return _flow_unknown(
            reason,
            sensitive=True,
        )
    return _flow_unknown(f"{name} has divergent reaching definitions")


def _outer_loop_control_outcomes(
    statements: Sequence[ast.stmt],
) -> frozenset[str]:
    """Conservatively classify exits from one outer-loop body path."""

    outcomes: set[str] = {"fallthrough"}
    for statement in statements:
        if "fallthrough" not in outcomes:
            break
        outcomes.remove("fallthrough")
        if isinstance(statement, ast.Break):
            outcomes.add("break")
        elif isinstance(statement, ast.Continue):
            outcomes.add("continue")
        elif isinstance(statement, ast.Return):
            outcomes.add("return")
        elif isinstance(statement, ast.Raise):
            outcomes.add("raise")
        elif isinstance(statement, ast.If):
            outcomes.update(_outer_loop_control_outcomes(statement.body))
            outcomes.update(_outer_loop_control_outcomes(statement.orelse))
        elif isinstance(statement, (ast.With, ast.AsyncWith)):
            body = _outer_loop_control_outcomes(statement.body)
            outcomes.update(body)
            if "raise" in body:
                outcomes.add("fallthrough")
        elif isinstance(statement, ast.Match):
            outcomes.add("fallthrough")
            for case in statement.cases:
                outcomes.update(_outer_loop_control_outcomes(case.body))
        elif isinstance(statement, (ast.For, ast.AsyncFor, ast.While)):
            # Break/continue in a nested loop do not target the outer loop.
            outcomes.add("fallthrough")
        else:
            try_types = (ast.Try,)
            if hasattr(ast, "TryStar"):
                try_types = (*try_types, ast.TryStar)
            if isinstance(statement, try_types):
                alternatives = [
                    _outer_loop_control_outcomes(statement.body),
                    *(
                        _outer_loop_control_outcomes(handler.body)
                        for handler in statement.handlers
                    ),
                ]
                combined = set().union(*alternatives)
                if statement.orelse and "fallthrough" in combined:
                    combined.remove("fallthrough")
                    combined.update(
                        _outer_loop_control_outcomes(statement.orelse)
                    )
                if statement.finalbody:
                    final = _outer_loop_control_outcomes(statement.finalbody)
                    if final != frozenset({"fallthrough"}):
                        combined.update(final - {"fallthrough"})
                outcomes.update(combined)
            else:
                outcomes.add("fallthrough")
    return frozenset(outcomes)


@dataclass(slots=True)
class _FlowExceptionalState:
    state: dict[str, _FlowValue]
    exception_tag: str | None = None
    explicit: bool = False
    excluded_handlers: frozenset[str] = frozenset()


@dataclass(slots=True)
class _FlowSuccessors:
    normal: list[dict[str, _FlowValue]]
    breaks: list[dict[str, _FlowValue]]
    continues: list[dict[str, _FlowValue]]
    returns: list[dict[str, _FlowValue]]
    raises: list[_FlowExceptionalState]

    @classmethod
    def empty(cls) -> "_FlowSuccessors":
        return cls([], [], [], [], [])


class _ExpressionDoesNotComplete(Exception):
    """Internal control transfer for a bounded locally-proven raise."""


class _SourceOrderedResolver:
    def __init__(
        self,
        aliases: Mapping[str, str],
        module_assignments: Mapping[str, ast.expr],
        local_functions: Mapping[
            str,
            ast.FunctionDef | ast.AsyncFunctionDef,
        ],
        sensitive_helper_names: frozenset[str] = frozenset(),
        helper_returns: Mapping[str, _FlowValue] | None = None,
        budget: _AnalysisBudget | None = None,
        exception_scope: _ExceptionNameScope | None = None,
        lexical_scope: _LexicalBindingScope | None = None,
        module_bound_names: Iterable[str] = (),
        enclosing_bound_names: Iterable[str] = (),
        sensitive_definition_markers: Iterable[str] = (),
        entry_values: Mapping[str, _FlowValue] | None = None,
    ) -> None:
        self.budget = budget or _AnalysisBudget()
        self.module_assignments = dict(module_assignments)
        self.values = {
            name: (
                _flow_unknown(
                    "protected namespace member mutation is dynamically unresolved",
                    sensitive=True,
                )
                if qualified == _PROTECTED_MUTATION_ALIAS
                else _flow_qname(qualified)
            )
            for name, qualified in aliases.items()
        }
        self.local_functions = dict(local_functions)
        self.helper_returns = dict(helper_returns or {})
        self.flow = _ReviewFlow({}, {}, {}, {}, {}, {}, [])
        self._call_states: dict[int, list[dict[str, _FlowValue]]] = {}
        self._call_values: dict[int, list[_FlowValue]] = {}
        self._active_deferred_generator_probes: set[int] = set()
        self._active_deferred_local_generators: set[str] = set()
        self._active_local_helper_returns: set[str] = set()
        self._next_deferred_local_generator_identity = 1
        self._deferred_local_generator_definitions: dict[
            str,
            _DeferredLocalGeneratorFactory,
        ] = {}
        self._local_function_definitions: dict[
            str,
            tuple[
                ast.FunctionDef,
                tuple[tuple[str, _FlowValue], ...],
            ],
        ] = {}
        self._plain_local_classes: set[str] = set()
        self._implicit_protocol_blocked_nodes: set[
            tuple[int, tuple[str, ...]]
        ] = set()
        self._implicit_protocol_event_keys: set[
            tuple[int, int, tuple[str, ...]]
        ] = set()
        self._try_star_blocked_nodes: set[int] = set()
        self._mutable_collection_versions: dict[int, int] = {}
        self.return_values: list[_FlowValue] = []
        self._throw_states: list[_FlowExceptionalState] | None = None
        self._active_exception_tag: str | None = None
        self.helper_raises: dict[str, str] = {}
        self.helper_raises.update({
            name: str(value.value)
            for name, value in self.helper_returns.items()
            if value.kind == "must_raise"
        })
        self.exception_scope = exception_scope or _ExceptionNameScope()
        self.lexical_scope = lexical_scope or _LexicalBindingScope()
        self.module_bound_names = frozenset(module_bound_names)
        self.enclosing_bound_names = frozenset(enclosing_bound_names)
        self.sensitive_definition_markers = frozenset(
            sensitive_definition_markers
        )
        for name, expression in module_assignments.items():
            self.values[name] = self._evaluate(expression, self.values, False)
        for name, definition in local_functions.items():
            definition_scope = _exception_name_scope(
                definition,
                self.exception_scope.shadowed_names,
                self.exception_scope.enclosing_names,
            )
            summary = _bounded_callable_summary(definition, definition_scope)
            returned = _trivial_helper_return(
                definition,
                _flow_aliases(self.values),
                self.budget,
            )
            if returned is not None:
                self.helper_returns.setdefault(name, returned)
            sensitive = _contains_sensitive_runtime(
                definition,
                self.budget,
            )
            self.values[name] = _FlowValue(
                "callable_summary" if summary is not None else "qname",
                (name, summary) if summary is not None else name,
                sensitive,
                "callable helper closure" if sensitive else None,
            )
        for name in sensitive_helper_names:
            self.values[name] = _FlowValue(
                "qname",
                name,
                sensitive=True,
                reason="callable helper closure",
            )
        self.values.update(entry_values or {})
        for name in self.lexical_scope.local_names:
            if name in self.lexical_scope.parameter_names:
                self.values.setdefault(
                    name,
                    _flow_unknown("function parameter is dynamically unresolved"),
                )
            else:
                self.values[name] = _FlowValue(
                    "unbound",
                    reason="local name is unbound at entry",
                )
        for name in self.lexical_scope.nonlocal_names:
            builtin_marker = next(
                (
                    marker.rsplit(":", 1)[1]
                    for marker in self.enclosing_bound_names
                    if marker.startswith(
                        f"__builtin_binding__:{name}:"
                    )
                ),
                None,
            )
            if builtin_marker is not None:
                self.values[name] = _flow_qname(builtin_marker)
            elif f"__definite__:{name}" in self.enclosing_bound_names:
                self.values[name] = _flow_unknown(
                    "enclosing value is dynamically unresolved"
                )
            else:
                self.values[name] = (
                    _FlowValue(
                        "maybe_unbound",
                        (),
                        reason="nonlocal name is only conditionally bound",
                    )
                    if name in self.enclosing_bound_names
                    else _FlowValue("unbound", reason="nonlocal name is unbound")
                )
        for name in self.lexical_scope.global_names:
            if name not in self.module_bound_names and name not in self.values:
                self.values[name] = (
                    _flow_unknown(
                        "global exception binding is source ordered"
                    )
                    if name in _BUILTIN_EXCEPTION_ANCESTORS
                    else _FlowValue(
                        "unbound",
                        reason="global name is unbound",
                    )
                )

    def _flow_decorator_preserves_identity(self, value: _FlowValue) -> bool:
        marker: str | None = None
        if (
            value.kind == "callable_summary"
            and isinstance(value.value, tuple)
            and len(value.value) == 2
        ):
            marker = str(value.value[0])
        elif value.kind == "qname":
            marker = str(value.value)
        if marker is None:
            return False
        local = self._local_function_definitions.get(marker)
        definition = (
            local[0]
            if local is not None
            else self.local_functions.get(marker)
        )
        return (
            definition is not None
            and _identity_decorator_definition(definition)
        )

    def _exception_name(
        self,
        expression: ast.AST | None,
        values: Mapping[str, _FlowValue],
    ) -> str | None:
        proven = _proven_builtin_exception_name(expression, self.exception_scope)
        if proven is not None:
            return proven
        if not isinstance(expression, ast.Name) or expression.id not in values:
            return None
        value = values[expression.id]
        if (
            value.kind == "qname"
            and str(value.value) in _BUILTIN_EXCEPTION_ANCESTORS
            and not (
                expression.id in self.exception_scope.shadowed_names
                and str(value.value) == expression.id
            )
        ):
            return str(value.value)
        return None

    @staticmethod
    def _flow_value_is_definitely_invalid_exception(value: _FlowValue) -> bool:
        return value.kind in {
            "scalar",
            "sequence",
            "mapping",
            "callback",
            "environment",
            "range",
            "exception_instance",
        }

    @staticmethod
    def _proven_builtin_indexable(value: _FlowValue) -> bool:
        return (
            value.kind == "range"
            or (
                value.kind == "sequence"
                and value.container_kind != "set"
            )
            or (
                value.kind == "scalar"
                and type(value.value) in {str, bytes}
            )
        )

    @staticmethod
    def _implicit_protocol_descriptors(
        value: _FlowValue,
    ) -> tuple[_ImplicitClassDescriptor, ...]:
        if (
            value.kind in {"implicit_class_instance", "implicit_class"}
            and isinstance(value.value, _ImplicitClassDescriptor)
        ):
            return (value.value,)
        if value.kind in {"maybe_unbound", "implicit_protocol_merged"}:
            retained: list[_ImplicitClassDescriptor] = []
            for candidate in value.value:
                if not isinstance(candidate, _FlowValue):
                    continue
                for descriptor in (
                    _SourceOrderedResolver._implicit_protocol_descriptors(candidate)
                ):
                    if descriptor not in retained:
                        retained.append(descriptor)
            return tuple(retained)
        return ()

    @classmethod
    def _extreme_flow_alternatives_are_complete(
        cls,
        value: _FlowValue,
    ) -> bool:
        """Reject comparison flows that contain an unmodeled runtime value."""

        if value.kind in {"unknown", "unbound", "maybe_unbound"}:
            return False
        if value.kind != "implicit_protocol_merged":
            return True
        candidates = tuple(
            candidate
            for candidate in value.value
            if isinstance(candidate, _FlowValue)
        )
        return bool(candidates) and len(candidates) == len(value.value) and all(
            cls._extreme_flow_alternatives_are_complete(candidate)
            and bool(cls._implicit_protocol_descriptors(candidate))
            for candidate in candidates
        )

    @classmethod
    def _lexicographic_comparison_values(
        cls,
        value: _FlowValue,
    ) -> tuple[_FlowValue, ...]:
        retained = [value]
        if (
            value.kind == "sequence"
            and value.container_kind in {None, "list", "tuple"}
        ):
            for item in value.value:
                retained.extend(cls._lexicographic_comparison_values(item))
        return tuple(retained)

    def _expanded_extreme_positional_values(
        self,
        argument_nodes: Sequence[ast.expr],
        argument_values: Sequence[_FlowValue],
    ) -> tuple[_FlowValue, ...] | None:
        """Expand only source-bounded starred operands for max/min."""

        if len(argument_nodes) != len(argument_values):
            return None
        expanded: list[_FlowValue] = []
        for argument, supplied in zip(
            argument_nodes,
            argument_values,
            strict=True,
        ):
            if not isinstance(argument, ast.Starred):
                expanded.append(supplied)
                continue
            if supplied.kind != "starred_argument" or not isinstance(
                supplied.value,
                _FlowValue,
            ):
                return None
            container = supplied.value
            if (
                container.kind != "sequence"
                or container.container_kind not in {None, "list", "tuple"}
            ):
                return None
            expanded.extend(container.value)
        return tuple(expanded)

    @staticmethod
    def _implicit_descriptor_is_strict_subclass(
        candidate: _ImplicitClassDescriptor,
        expected_base: _ImplicitClassDescriptor,
    ) -> bool:
        if candidate is expected_base:
            return False
        pending = list(candidate.base_descriptors)
        visited: set[int] = set()
        while pending:
            descriptor = pending.pop()
            identity = id(descriptor)
            if identity in visited:
                continue
            visited.add(identity)
            if descriptor is expected_base:
                return True
            pending.extend(descriptor.base_descriptors)
        return False

    @staticmethod
    def _implicit_method_may_return_not_implemented(
        descriptor: _ImplicitClassDescriptor,
        method_name: str,
    ) -> bool:
        return (
            method_name not in descriptor.defined_methods
            or method_name
            not in descriptor.proven_non_not_implemented_methods
        )

    @classmethod
    def _ordered_comparison_dispatches(
        cls,
        left: _FlowValue,
        right: _FlowValue,
        direct_method: str,
        reflected_method: str,
    ) -> tuple[tuple[_ImplicitClassDescriptor, str], ...]:
        """Return every reachable rich-comparison callback in runtime order."""

        retained: list[tuple[_ImplicitClassDescriptor, str]] = []
        retained_keys: set[tuple[int, str]] = set()

        def retain(
            descriptor: _ImplicitClassDescriptor,
            method_name: str,
        ) -> None:
            if method_name not in descriptor.defined_methods:
                return
            key = (id(descriptor), method_name)
            if key in retained_keys:
                return
            retained_keys.add(key)
            retained.append((descriptor, method_name))

        left_descriptors = cls._implicit_protocol_descriptors(left)
        right_descriptors = cls._implicit_protocol_descriptors(right)
        for left_descriptor in left_descriptors:
            for right_descriptor in right_descriptors:
                reflected_first = (
                    reflected_method in right_descriptor.defined_methods
                    and cls._implicit_descriptor_is_strict_subclass(
                        right_descriptor,
                        left_descriptor,
                    )
                )
                if reflected_first:
                    retain(right_descriptor, reflected_method)
                    if cls._implicit_method_may_return_not_implemented(
                        right_descriptor,
                        reflected_method,
                    ):
                        retain(left_descriptor, direct_method)
                    continue
                retain(left_descriptor, direct_method)
                if cls._implicit_method_may_return_not_implemented(
                    left_descriptor,
                    direct_method,
                ):
                    retain(right_descriptor, reflected_method)
        return tuple(retained)

    def _record_ordered_comparison_dispatch(
        self,
        node: ast.AST,
        left: _FlowValue,
        right: _FlowValue,
        direct_method: str,
        reflected_method: str,
    ) -> None:
        reason = (
            "implicit container-element protocol execution is dynamically "
            "unresolved"
        )
        if not (
            self._extreme_flow_alternatives_are_complete(left)
            and self._extreme_flow_alternatives_are_complete(right)
        ):
            if isinstance(node, ast.Call):
                self._block_extreme_call(
                    node,
                    "max/min comparison dispatch is dynamically unresolved",
                )
            else:
                self.flow.standalone_blockers.append((node, reason))
            return
        dispatches = self._ordered_comparison_dispatches(
            left,
            right,
            direct_method,
            reflected_method,
        )
        for descriptor, method_name in dispatches:
            self._record_implicit_protocol_blocker(
                node,
                _FlowValue("implicit_class_instance", descriptor),
                frozenset({method_name}),
                reason,
            )
        if dispatches:
            return
        if _flow_is_sensitive(left):
            self._record_implicit_protocol_blocker(
                node,
                left,
                frozenset({direct_method}),
                reason,
            )
        if _flow_is_sensitive(right):
            self._record_implicit_protocol_blocker(
                node,
                right,
                frozenset({reflected_method}),
                reason,
            )

    @staticmethod
    def _stable_scalar_equality(
        left: _FlowValue,
        right: _FlowValue,
    ) -> bool | None:
        stable_types = {type(None), bool, int, float, complex, str, bytes}
        if (
            left.kind != "scalar"
            or right.kind != "scalar"
            or type(left.value) not in stable_types
            or type(right.value) not in stable_types
        ):
            return None
        try:
            return bool(left.value == right.value)
        except (ArithmeticError, TypeError, ValueError):
            return None

    @staticmethod
    def _stable_extreme_candidate_wins(
        candidate: _FlowValue,
        current: _FlowValue,
        callable_name: str,
    ) -> bool | None:
        stable_types = {bool, int, float, str, bytes}
        if (
            candidate.kind != "scalar"
            or current.kind != "scalar"
            or type(candidate.value) not in stable_types
            or type(current.value) not in stable_types
            or (
                type(candidate.value) in {str, bytes}
                and type(candidate.value) is not type(current.value)
            )
        ):
            return None
        try:
            return bool(
                candidate.value > current.value
                if callable_name == "max"
                else candidate.value < current.value
            )
        except (ArithmeticError, TypeError, ValueError):
            return None

    @staticmethod
    def _implicit_method_literal_bool(
        descriptor: _ImplicitClassDescriptor,
        method_name: str,
    ) -> bool | None:
        method = dict(descriptor.method_slots).get(method_name)
        if not isinstance(method, ast.FunctionDef) or len(method.body) != 1:
            return None
        statement = method.body[0]
        if not (
            isinstance(statement, ast.Return)
            and isinstance(statement.value, ast.Constant)
            and type(statement.value.value) is bool
        ):
            return None
        return bool(statement.value.value)

    @classmethod
    def _ordered_comparison_literal_bool(
        cls,
        left: _FlowValue,
        right: _FlowValue,
        direct_method: str,
        reflected_method: str,
    ) -> bool | None:
        if not (
            cls._extreme_flow_alternatives_are_complete(left)
            and cls._extreme_flow_alternatives_are_complete(right)
            and len(cls._implicit_protocol_descriptors(left)) == 1
            and len(cls._implicit_protocol_descriptors(right)) == 1
        ):
            return None
        dispatches = cls._ordered_comparison_dispatches(
            left,
            right,
            direct_method,
            reflected_method,
        )
        if not dispatches:
            return None
        descriptor, method_name = dispatches[0]
        return cls._implicit_method_literal_bool(descriptor, method_name)

    def _record_extreme_lexicographic_pair(
        self,
        node: ast.AST,
        left: _FlowValue,
        right: _FlowValue,
        direct_method: str,
        reflected_method: str,
    ) -> str:
        """Record list/tuple equality-then-order stages in source order."""

        both_sequences = bool(
            left.kind == "sequence"
            and right.kind == "sequence"
            and left.container_kind in {None, "list", "tuple"}
            and right.container_kind in {None, "list", "tuple"}
        )
        if (
            both_sequences
            and left.container_kind in {"list", "tuple"}
            and right.container_kind in {"list", "tuple"}
            and left.container_kind != right.container_kind
        ):
            return "different"
        if not both_sequences:
            scalar_equal = self._stable_scalar_equality(left, right)
            if scalar_equal is not None:
                return "equal" if scalar_equal else "different"
            literal_equal = self._ordered_comparison_literal_bool(
                left,
                right,
                "__eq__",
                "__eq__",
            )
            if literal_equal is True:
                return "equal"
            if literal_equal is False:
                self._record_ordered_comparison_dispatch(
                    node,
                    left,
                    right,
                    direct_method,
                    reflected_method,
                )
                return "different"
            self._record_ordered_comparison_dispatch(
                node,
                left,
                right,
                "__eq__",
                "__eq__",
            )
            self._record_ordered_comparison_dispatch(
                node,
                left,
                right,
                direct_method,
                reflected_method,
            )
            return "unknown"

        unknown_equality = False
        for left_item, right_item in zip(
            left.value,
            right.value,
        ):
            outcome = self._record_extreme_lexicographic_pair(
                node,
                left_item,
                right_item,
                direct_method,
                reflected_method,
            )
            if outcome == "equal":
                continue
            if outcome == "different":
                return "unknown" if unknown_equality else "different"
            unknown_equality = True
        if unknown_equality:
            return "unknown"
        return "equal" if len(left.value) == len(right.value) else "different"

    def _record_extreme_comparison_pair(
        self,
        node: ast.AST,
        left: _FlowValue,
        right: _FlowValue,
        direct_method: str,
        reflected_method: str,
    ) -> None:
        if (
            left.kind == "sequence"
            and right.kind == "sequence"
            and left.container_kind in {"list", "tuple"}
            and right.container_kind in {"list", "tuple"}
            and left.container_kind != right.container_kind
        ):
            return
        if (
            left.kind == "sequence"
            and right.kind == "sequence"
            and left.container_kind in {None, "list", "tuple"}
            and right.container_kind in {None, "list", "tuple"}
        ):
            self._record_extreme_lexicographic_pair(
                node,
                left,
                right,
                direct_method,
                reflected_method,
            )
            return
        self._record_ordered_comparison_dispatch(
            node,
            left,
            right,
            direct_method,
            reflected_method,
        )

    @staticmethod
    def _extreme_key_expression_is_bounded(
        expression: ast.expr,
        parameter_name: str,
        values: Mapping[str, _FlowValue],
    ) -> bool:
        """Accept only projections whose result can be resolved without execution."""

        if isinstance(expression, ast.Constant):
            return True
        if isinstance(expression, ast.Name):
            return expression.id == parameter_name or expression.id in values
        if isinstance(expression, (ast.List, ast.Tuple)):
            return all(
                _SourceOrderedResolver._extreme_key_expression_is_bounded(
                    item,
                    parameter_name,
                    values,
                )
                for item in expression.elts
            )
        if not (
            isinstance(expression, ast.Call)
            and isinstance(expression.func, ast.Name)
            and not expression.args
            and not expression.keywords
        ):
            return False
        constructor = values.get(expression.func.id)
        if not (
            constructor is not None
            and constructor.kind == "implicit_class"
            and isinstance(constructor.value, _ImplicitClassDescriptor)
        ):
            return False
        descriptor = constructor.value
        return not bool(
            descriptor.sensitive_methods
            & frozenset({"__new__", "__init__", "__del__"})
        )

    @staticmethod
    def _extreme_callable_marker(value: _FlowValue) -> str | None:
        if value.kind == "callable_summary":
            supplied = value.value
            if isinstance(supplied, tuple) and supplied:
                return str(supplied[0])
        if value.kind == "qname":
            return str(value.value)
        return None

    def _block_extreme_call(self, node: ast.Call, reason: str) -> None:
        self.flow.blockers_by_call.setdefault(id(node), reason)

    def _extreme_key_projection(
        self,
        node: ast.Call,
        key_node: ast.expr | None,
        key_value: _FlowValue | None,
        element: _FlowValue,
        values: dict[str, _FlowValue],
    ) -> _FlowValue | None:
        if key_node is None or (
            key_value is not None
            and key_value.kind == "scalar"
            and key_value.value is None
        ):
            return element
        if key_value is None or _flow_is_sensitive(key_value):
            self._block_extreme_call(
                node,
                "max/min key projection is dynamically unresolved",
            )
            return None

        marker: str | None = None
        if isinstance(key_node, ast.Lambda):
            definition_arguments = key_node.args
            return_expression = key_node.body
        else:
            marker = self._extreme_callable_marker(key_value)
            retained = (
                self._local_function_definitions.get(marker)
                if marker is not None
                else None
            )
            if retained is None:
                self._block_extreme_call(
                    node,
                    "max/min key projection is dynamically unresolved",
                )
                return None
            definition, _defaults = retained
            if (
                definition.decorator_list
                or len(definition.body) != 1
                or not isinstance(definition.body[0], ast.Return)
                or definition.body[0].value is None
            ):
                self._block_extreme_call(
                    node,
                    "max/min key projection is dynamically unresolved",
                )
                return None
            definition_arguments = definition.args
            return_expression = definition.body[0].value

        positional = (
            *definition_arguments.posonlyargs,
            *definition_arguments.args,
        )
        if (
            len(positional) != 1
            or definition_arguments.defaults
            or definition_arguments.vararg is not None
            or definition_arguments.kwonlyargs
            or definition_arguments.kw_defaults
            or definition_arguments.kwarg is not None
            or not self._extreme_key_expression_is_bounded(
                return_expression,
                positional[0].arg,
                values,
            )
        ):
            self._block_extreme_call(
                node,
                "max/min key projection is dynamically unresolved",
            )
            return None

        local = dict(values)
        local[positional[0].arg] = element
        if marker is not None:
            if marker in self._active_local_helper_returns:
                self._block_extreme_call(
                    node,
                    "max/min key projection is dynamically unresolved",
                )
                return None
            self._active_local_helper_returns.add(marker)
        try:
            projected = self._evaluate(return_expression, local, False)
        finally:
            if marker is not None:
                self._active_local_helper_returns.discard(marker)
        if projected.kind in {"unknown", "maybe_unbound", "unbound"}:
            self._block_extreme_call(
                node,
                "max/min key projection is dynamically unresolved",
            )
            return None
        if not self._extreme_flow_alternatives_are_complete(projected):
            self._block_extreme_call(
                node,
                "max/min key projection is dynamically unresolved",
            )
            return None
        if (
            projected.kind == "implicit_class_instance"
            and isinstance(projected.value, _ImplicitClassDescriptor)
            and projected.value.sensitive_methods
            & frozenset({"__new__", "__init__", "__del__"})
        ):
            self._block_extreme_call(
                node,
                "max/min key projection executes an unresolved class protocol",
            )
            return None
        return projected

    def _record_extreme_call(
        self,
        node: ast.Call,
        callable_name: str,
        argument_values: Sequence[_FlowValue],
        keyword_values: Sequence[_FlowValue],
        values: dict[str, _FlowValue],
    ) -> None:
        """Record pair-aware max/min iteration, key projection, and comparison."""

        for argument, supplied in zip(
            node.args,
            argument_values,
            strict=True,
        ):
            if not isinstance(argument, ast.Starred):
                continue
            starred = (
                supplied.value
                if supplied.kind == "starred_argument"
                and isinstance(supplied.value, _FlowValue)
                else supplied
            )
            self._record_implicit_protocol_blocker(
                argument,
                starred,
                _IMPLICIT_PROTOCOL_METHODS["iteration"],
                "implicit starred-argument iteration is dynamically unresolved",
            )

        expanded = self._expanded_extreme_positional_values(
            node.args,
            argument_values,
        )
        if expanded is None or any(
            value.kind == "starred_argument" for value in expanded
        ):
            self._block_extreme_call(
                node,
                "max/min starred argument expansion is dynamically unresolved",
            )
            return

        supplied_keywords: dict[str, tuple[ast.expr, _FlowValue]] = {}
        for keyword, supplied in zip(
            node.keywords,
            keyword_values,
            strict=True,
        ):
            if keyword.arg is None:
                self._block_extreme_call(
                    node,
                    "max/min keyword binding is dynamically unresolved",
                )
                return
            if keyword.arg not in {"key", "default"}:
                # A known invalid keyword raises before iteration or key calls.
                return
            if keyword.arg in supplied_keywords:
                return
            supplied_keywords[keyword.arg] = (keyword.value, supplied)
        if "default" in supplied_keywords and len(expanded) != 1:
            # The variadic form rejects default before iteration or key calls.
            return

        unordered_elements = False
        if len(expanded) == 1:
            iterable = expanded[0]
            self._record_implicit_protocol_blocker(
                node,
                iterable,
                _IMPLICIT_PROTOCOL_METHODS["iteration"],
                "implicit builtin protocol execution is dynamically unresolved",
            )
            if iterable.kind == "sequence":
                elements = tuple(iterable.value)
                unordered_elements = iterable.container_kind == "set"
            elif iterable.kind == "mapping":
                elements = tuple(
                    _FlowValue("scalar", key)
                    for key, _value in iterable.value
                )
            elif iterable.kind == "mapping_keys":
                elements = tuple(key for key, _value in iterable.value)
            else:
                self._block_extreme_call(
                    node,
                    "max/min iterable contents are dynamically unresolved",
                )
                return
        else:
            elements = tuple(expanded)
        if not elements:
            return

        key_node, key_value = supplied_keywords.get("key", (None, None))

        projected: list[_FlowValue] = []
        for element in elements:
            key = self._extreme_key_projection(
                node,
                key_node,
                key_value,
                element,
                values,
            )
            if key is None:
                return
            projected.append(key)
        if len(projected) < 2:
            return

        direct_method, reflected_method = (
            ("__gt__", "__lt__")
            if callable_name == "max"
            else ("__lt__", "__gt__")
        )
        if unordered_elements:
            for candidate_index, candidate in enumerate(projected):
                for current_index, current in enumerate(projected):
                    if candidate_index == current_index:
                        continue
                    if self._stable_extreme_candidate_wins(
                        candidate,
                        current,
                        callable_name,
                    ) is not None:
                        continue
                    self.budget.consume()
                    self._record_extreme_comparison_pair(
                        node,
                        candidate,
                        current,
                        direct_method,
                        reflected_method,
                    )
            return
        possible_currents = [projected[0]]
        for candidate in projected[1:]:
            next_currents: list[_FlowValue] = []
            next_current_ids: set[int] = set()

            def retain_possible_current(value: _FlowValue) -> None:
                identity = id(value)
                if identity in next_current_ids:
                    return
                next_current_ids.add(identity)
                next_currents.append(value)

            for current in possible_currents:
                candidate_wins = self._stable_extreme_candidate_wins(
                    candidate,
                    current,
                    callable_name,
                )
                if candidate_wins is not None:
                    retain_possible_current(
                        candidate if candidate_wins else current
                    )
                    continue
                self.budget.consume()
                self._record_extreme_comparison_pair(
                    node,
                    candidate,
                    current,
                    direct_method,
                    reflected_method,
                )
                retain_possible_current(current)
                retain_possible_current(candidate)
            possible_currents = next_currents

    @staticmethod
    def _effective_implicit_protocol_methods(
        descriptor: _ImplicitClassDescriptor,
        method_names: frozenset[str],
    ) -> frozenset[str]:
        selected = set(method_names)
        if {"__bool__", "__len__"} <= selected:
            selected.difference_update({"__bool__", "__len__"})
            selected.add(
                "__bool__"
                if "__bool__" in descriptor.defined_methods
                else "__len__"
            )
        if {"__float__", "__index__"} <= selected:
            selected.difference_update({"__float__", "__index__"})
            selected.add(
                "__float__"
                if "__float__" in descriptor.defined_methods
                else "__index__"
            )
        if {"__int__", "__index__"} <= selected:
            selected.difference_update({"__int__", "__index__"})
            selected.add(
                "__int__"
                if "__int__" in descriptor.defined_methods
                else "__index__"
            )
        reverse_methods = {"__reversed__", "__len__", "__getitem__"}
        if reverse_methods <= selected:
            selected.difference_update(reverse_methods)
            selected.update(
                {"__reversed__"}
                if "__reversed__" in descriptor.defined_methods
                else {"__len__", "__getitem__"}
            )
        elif {"__iter__", "__getitem__"} <= selected:
            if "__iter__" in descriptor.defined_methods:
                selected.discard("__getitem__")
            else:
                selected.discard("__iter__")
                selected.discard("__next__")
        return frozenset(selected)

    @classmethod
    def _implicit_protocol_is_sensitive(
        cls,
        value: _FlowValue,
        method_names: frozenset[str],
    ) -> bool:
        return any(
            descriptor.sensitive_methods
            & cls._effective_implicit_protocol_methods(
                descriptor,
                method_names,
            )
            for descriptor in cls._implicit_protocol_descriptors(value)
        ) or (
            value.kind == "unknown"
            and value.sensitive
            and value.reason
            == "implicit class protocol execution is dynamically unresolved"
        )

    def _record_implicit_protocol_blocker(
        self,
        node: ast.AST,
        value: _FlowValue,
        method_names: frozenset[str],
        reason: str,
    ) -> None:
        descriptors = tuple(
            (
                descriptor,
                self._effective_implicit_protocol_methods(
                    descriptor,
                    method_names,
                ),
            )
            for descriptor in self._implicit_protocol_descriptors(value)
        )
        descriptors = tuple(
            (descriptor, effective_methods)
            for descriptor, effective_methods in descriptors
            if descriptor.sensitive_methods & effective_methods
        )
        unresolved = bool(
            value.kind == "unknown"
            and value.sensitive
            and value.reason
            == "implicit class protocol execution is dynamically unresolved"
        )
        if not descriptors and not unresolved:
            return
        key = (id(node), tuple(sorted(method_names)))
        if key not in self._implicit_protocol_blocked_nodes:
            self._implicit_protocol_blocked_nodes.add(key)
            self.flow.standalone_blockers.append((node, reason))
        for descriptor, effective_methods in descriptors:
            event_key = (
                id(node),
                id(descriptor),
                tuple(sorted(effective_methods)),
            )
            if event_key in self._implicit_protocol_event_keys:
                continue
            self._implicit_protocol_event_keys.add(event_key)
            self.flow.implicit_protocol_events.append((
                node,
                descriptor,
                effective_methods,
                reason,
            ))

    def _record_mapping_key_dispatch(
        self,
        node: ast.AST,
        mapping: _FlowValue,
        key: _FlowValue,
        *,
        operation: str,
    ) -> None:
        if mapping.kind not in {"mapping", "mapping_keys"}:
            return
        self._record_implicit_protocol_blocker(
            node,
            key,
            _IMPLICIT_PROTOCOL_METHODS["hash"],
            (
                f"implicit mapping-{operation} hash protocol execution "
                "is dynamically unresolved"
            ),
        )
        stored_keys = (
            tuple(stored for stored, _item in mapping.value)
            if mapping.kind == "mapping_keys"
            else tuple(
                _FlowValue("scalar", stored)
                for stored, _item in mapping.value
            )
        )
        if not stored_keys:
            return
        equality_reason = (
            f"implicit mapping-{operation} equality protocol execution "
            "is dynamically unresolved"
        )
        self._record_implicit_protocol_blocker(
            node,
            key,
            frozenset({"__eq__"}),
            equality_reason,
        )
        for stored_key in stored_keys:
            self._record_implicit_protocol_blocker(
                node,
                stored_key,
                frozenset({"__eq__"}),
                equality_reason,
            )

    def _local_callable_definition(
        self,
        value: _FlowValue,
    ) -> ast.FunctionDef | None:
        marker: str | None = None
        if value.kind == "callable_summary":
            supplied = value.value
            if isinstance(supplied, tuple) and supplied:
                marker = str(supplied[0])
        elif value.kind == "qname":
            marker = str(value.value)
        if marker is None:
            return None
        retained = self._local_function_definitions.get(marker)
        return retained[0] if retained is not None else None

    def _replace_implicit_class_descriptor_state(
        self,
        previous: _ImplicitClassDescriptor,
        updated: _ImplicitClassDescriptor,
        values: dict[str, _FlowValue],
    ) -> None:
        descriptor_memo = {id(previous): updated}
        for name, candidate in tuple(values.items()):
            values[name] = _rewrite_implicit_class_descriptor(
                candidate,
                previous,
                updated,
                _descriptor_memo=descriptor_memo,
            )
        self.helper_returns = {
            name: _rewrite_implicit_class_descriptor(
                value,
                previous,
                updated,
                _descriptor_memo=descriptor_memo,
            )
            for name, value in self.helper_returns.items()
        }
        self._local_function_definitions = {
            name: (
                definition,
                tuple(
                    (
                        binding_name,
                        _rewrite_implicit_class_descriptor(
                            binding_value,
                            previous,
                            updated,
                            _descriptor_memo=descriptor_memo,
                        ),
                    )
                    for binding_name, binding_value in bindings
                ),
            )
            for name, (definition, bindings) in self._local_function_definitions.items()
        }
        self._deferred_local_generator_definitions = {
            name: replace(
                factory,
                defaults=tuple(
                    (
                        default_name,
                        _rewrite_implicit_class_descriptor(
                            default_value,
                            previous,
                            updated,
                            _descriptor_memo=descriptor_memo,
                        ),
                    )
                    for default_name, default_value in factory.defaults
                ),
            )
            for name, factory in self._deferred_local_generator_definitions.items()
        }

    def _update_implicit_class_protocol(
        self,
        descriptor: _ImplicitClassDescriptor,
        method_name: str,
        value: _FlowValue,
        values: dict[str, _FlowValue],
    ) -> None:
        definition = self._local_callable_definition(value)
        locally_proven = bool(
            definition is not None
            or value.kind in {
                "callback",
                "callable_constant",
                "proved_non_sensitive_callable",
            }
        )
        dynamically_sensitive = bool(
            _flow_is_sensitive(value)
            or (
                value.kind in {"callable_summary", "qname", "unknown"}
                and not locally_proven
            )
        )
        local_sensitive_methods = set(descriptor.local_sensitive_methods)
        if dynamically_sensitive:
            local_sensitive_methods.add(method_name)
        else:
            local_sensitive_methods.discard(method_name)
        retained_slots = [
            (slot, method)
            for slot, method in descriptor.local_method_slots
            if slot != method_name
        ]
        if definition is not None:
            retained_slots.append((method_name, definition))
        updated = _compose_implicit_class_descriptor(
            name=descriptor.name,
            base_descriptors=descriptor.base_descriptors,
            local_overrides=(
                descriptor.local_overrides | frozenset({method_name})
            ),
            local_sensitive_methods=frozenset(local_sensitive_methods),
            local_defined_methods=(
                descriptor.local_defined_methods | frozenset({method_name})
            ),
            local_method_slots=tuple(retained_slots),
            local_descriptor_members=descriptor.local_descriptor_members,
            exact_init_review=descriptor.exact_init_review,
        )
        self._replace_implicit_class_descriptor_state(
            descriptor,
            updated,
            values,
        )

    def _delete_implicit_class_member(
        self,
        descriptor: _ImplicitClassDescriptor,
        member_name: str,
        values: dict[str, _FlowValue],
    ) -> bool:
        if member_name not in descriptor.local_overrides:
            return False
        updated = _compose_implicit_class_descriptor(
            name=descriptor.name,
            base_descriptors=descriptor.base_descriptors,
            local_overrides=(
                descriptor.local_overrides - frozenset({member_name})
            ),
            local_sensitive_methods=(
                descriptor.local_sensitive_methods - frozenset({member_name})
            ),
            local_defined_methods=(
                descriptor.local_defined_methods - frozenset({member_name})
            ),
            local_method_slots=tuple(
                item
                for item in descriptor.local_method_slots
                if item[0] != member_name
            ),
            local_descriptor_members=tuple(
                item
                for item in descriptor.local_descriptor_members
                if item[0] != member_name
            ),
            exact_init_review=descriptor.exact_init_review,
        )
        self._replace_implicit_class_descriptor_state(
            descriptor,
            updated,
            values,
        )
        return True

    def _name_is_bound(
        self,
        name: str,
        values: Mapping[str, _FlowValue],
    ) -> bool:
        return name in values and values[name].kind not in {"maybe_unbound", "unbound"}

    def _lookup_error_tag(self, name: str) -> str:
        return (
            "UnboundLocalError"
            if name in self.lexical_scope.local_names
            else "NameError"
        )

    def _expression_is_proven_nonthrowing(
        self,
        expression: ast.AST | None,
        values: Mapping[str, _FlowValue],
    ) -> bool:
        return _exception_expression_is_proven_nonthrowing(
            expression,
            self.exception_scope,
            lambda name: self._name_is_bound(name, values),
        )

    def _handler_validation(
        self,
        handler: ast.expr | None,
        values: Mapping[str, _FlowValue],
    ) -> str:
        validation = _exception_handler_validation(handler, self.exception_scope)
        if validation != "unknown" or not isinstance(handler, ast.Name):
            return validation
        if handler.id not in values:
            return "unknown"
        value = values[handler.id]
        if self._exception_name(handler, values) is not None:
            return "valid"
        if self._flow_value_is_definitely_invalid_exception(value):
            return "invalid"
        return "unknown"

    def _handler_match(
        self,
        exception_tag: str | None,
        handler: ast.expr | None,
        values: Mapping[str, _FlowValue],
    ) -> str:
        if handler is None:
            return "match"
        if isinstance(handler, ast.Tuple):
            outcomes = {
                self._handler_match(exception_tag, element, values)
                for element in handler.elts
            }
            if "match" in outcomes:
                return "match"
            return "unknown" if "unknown" in outcomes else "nonmatch"
        handler_name = self._exception_name(handler, values)
        if exception_tag is None or handler_name is None:
            return "unknown"
        if (
            handler_name == exception_tag
            or handler_name in _BUILTIN_EXCEPTION_ANCESTORS[exception_tag]
        ):
            return "match"
        return "nonmatch"

    def _handler_exception_names(
        self,
        handler: ast.expr | None,
        values: Mapping[str, _FlowValue],
    ) -> frozenset[str]:
        if handler is None:
            return frozenset({"BaseException"})
        if isinstance(handler, ast.Tuple):
            return frozenset().union(
                *(
                    self._handler_exception_names(element, values)
                    for element in handler.elts
                )
            )
        name = self._exception_name(handler, values)
        return frozenset() if name is None else frozenset({name})

    def _implicit_handler_match(
        self,
        exceptional: _FlowExceptionalState,
        handler: ast.expr | None,
        values: Mapping[str, _FlowValue],
    ) -> str:
        if handler is None:
            return "match"
        names = self._handler_exception_names(handler, values)
        if not names:
            return "unknown"
        if "BaseException" in names:
            return "match"
        if all(
            _excluded_handler_proves_nonmatch(
                name,
                exceptional.excluded_handlers,
            )
            for name in names
        ):
            return "nonmatch"
        return "unknown"

    def _suppress_target_outcomes(
        self,
        exceptional: _FlowExceptionalState,
        target: ast.expr,
        values: Mapping[str, _FlowValue],
    ) -> frozenset[str]:
        if isinstance(target, ast.Tuple):
            outcomes = {"nonmatch"}
            for element in target.elts:
                advanced = set(outcomes) - {"nonmatch"}
                if "nonmatch" in outcomes:
                    advanced.update(
                        self._suppress_target_outcomes(
                            exceptional,
                            element,
                            values,
                        )
                    )
                outcomes = advanced
            return frozenset(outcomes)
        validation = self._handler_validation(target, values)
        if validation == "invalid":
            return frozenset({"invalid"})
        match = (
            self._handler_match(
                exceptional.exception_tag,
                target,
                values,
            )
            if exceptional.explicit
            else self._implicit_handler_match(exceptional, target, values)
        )
        if match != "unknown":
            return frozenset({match})
        outcomes = {"match", "nonmatch"}
        if validation == "unknown":
            outcomes.add("invalid")
        return frozenset(outcomes)

    def _suppress_outcomes(
        self,
        exceptional: _FlowExceptionalState,
        arguments: Sequence[ast.expr],
        values: Mapping[str, _FlowValue],
    ) -> frozenset[str]:
        outcomes = {"nonmatch"}
        for argument in arguments:
            advanced = set(outcomes) - {"nonmatch"}
            if "nonmatch" in outcomes:
                advanced.update(
                    self._suppress_target_outcomes(
                        exceptional,
                        argument,
                        values,
                    )
                )
            outcomes = advanced
        return frozenset(outcomes)

    def _cause_validation(
        self,
        cause: ast.expr | None,
        values: Mapping[str, _FlowValue],
    ) -> str:
        validation = _raise_cause_validation(cause, self.exception_scope)
        if validation != "unknown" or not isinstance(cause, ast.Name):
            return validation
        if cause.id not in values:
            return "unknown"
        value = values[cause.id]
        if self._exception_name(cause, values) is not None or value.kind == "exception_instance":
            return "valid"
        if self._flow_value_is_definitely_invalid_exception(value):
            return "invalid"
        return "unknown"

    def resolve(
        self,
        statements: Sequence[ast.stmt],
    ) -> _ReviewFlow:
        successors = self._flow_statements(statements, self.values)
        if successors.normal:
            self.values.clear()
            self.values.update(self._merge_states(successors.normal))
        else:
            self.values.clear()
        return self.flow

    @staticmethod
    def _protected_namespace_mapping_owner(value: _FlowValue) -> str | None:
        if value.kind != "qname":
            return None
        qualified = str(value.value)
        if qualified.endswith(".__dict__"):
            owner = qualified.removesuffix(".__dict__")
        elif qualified.endswith(".__globals__"):
            owner = qualified.removesuffix(".__globals__")
            return (
                owner
                if owner in _PROTECTED_NAMESPACE_MEMBERS
                else None
            )
        else:
            return None
        return (
            owner
            if any(
                member.startswith(f"{owner}.")
                for member in _PROTECTED_NAMESPACE_MEMBERS
            )
            else None
        )

    @staticmethod
    def _known_mapping_string_keys(
        value: _FlowValue,
    ) -> frozenset[str] | None:
        if value.kind == "mapping":
            if not all(type(key) is str for key, _item in value.value):
                return None
            return frozenset(str(key) for key, _item in value.value)
        if value.kind == "mapping_keys":
            if not all(
                key.kind == "scalar" and type(key.value) is str
                for key, _item in value.value
            ):
                return None
            return frozenset(
                str(key.value) for key, _item in value.value
            )
        return None

    @staticmethod
    def _protected_members_affected(path: str) -> tuple[str, ...]:
        return tuple(
            member
            for member in _PROTECTED_NAMESPACE_MEMBERS
            if (
                member == path
                or member.startswith(f"{path}.")
                or path.startswith(f"{member}.")
            )
        )

    def _invalidate_protected_path(
        self,
        node: ast.AST,
        path: str,
        values: dict[str, _FlowValue],
    ) -> bool:
        members = self._protected_members_affected(path)
        if not members:
            return False
        for member in members:
            values[member] = _flow_unknown(
                "protected namespace member mutation is dynamically unresolved",
                sensitive=True,
            )
        self.flow.standalone_blockers.append((
            node,
            "protected namespace member mutation is dynamically unresolved",
        ))
        return True

    def _invalidate_protected_namespace_mapping(
        self,
        node: ast.AST,
        owner: str,
        keys: frozenset[str] | None,
        values: dict[str, _FlowValue],
    ) -> bool:
        callable_globals = owner in _PROTECTED_NAMESPACE_MEMBERS
        namespace_owner = (
            owner.rpartition(".")[0] if callable_globals else owner
        )
        members = tuple(
            member
            for member in _PROTECTED_NAMESPACE_MEMBERS
            if (
                member == owner
                or member.startswith(f"{namespace_owner}.")
            )
            and (
                member == owner
                or keys is None
                or member.removeprefix(
                    f"{namespace_owner}."
                ).split(".", 1)[0] in keys
            )
        )
        if not members:
            return False
        for member in members:
            values[member] = _flow_unknown(
                "protected namespace member mutation is dynamically unresolved",
                sensitive=True,
            )
        self.flow.standalone_blockers.append((
            node,
            "protected namespace member mutation is dynamically unresolved",
        ))
        return True

    def _invalidate_protected_mapping_call(
        self,
        node: ast.Call,
        callable_name: str | None,
        argument_values: Sequence[_FlowValue],
        keyword_values: Sequence[_FlowValue],
        values: dict[str, _FlowValue],
    ) -> _FlowValue | None:
        if callable_name is None:
            return None
        mutators = {
            "__delitem__",
            "__ior__",
            "__setitem__",
            "clear",
            "pop",
            "popitem",
            "setdefault",
            "update",
        }
        protected_mapping: _FlowValue | None = None
        supplied_values: Sequence[_FlowValue] = argument_values
        method_name: str | None = None
        for candidate in mutators:
            suffix = f".{candidate}"
            if not callable_name.endswith(suffix):
                continue
            bound_mapping = _flow_qname(
                callable_name.removesuffix(suffix)
            )
            if self._protected_namespace_mapping_owner(bound_mapping) is not None:
                protected_mapping = bound_mapping
                method_name = candidate
                break
        unbound_mutators = {
            "dict.__delitem__": "__delitem__",
            "dict.__ior__": "__ior__",
            "dict.__setitem__": "__setitem__",
            "dict.clear": "clear",
            "dict.pop": "pop",
            "dict.popitem": "popitem",
            "dict.setdefault": "setdefault",
            "dict.update": "update",
            "operator.delitem": "__delitem__",
            "operator.setitem": "__setitem__",
        }
        if protected_mapping is None and callable_name in unbound_mutators:
            if not argument_values:
                return None
            protected_mapping = argument_values[0]
            supplied_values = argument_values[1:]
            method_name = unbound_mutators[callable_name]
        if protected_mapping is None or method_name is None:
            return None
        positional_count = len(supplied_values)
        has_keywords = False
        for keyword, keyword_value in zip(
            node.keywords,
            keyword_values,
            strict=True,
        ):
            if keyword.arg is not None:
                has_keywords = True
                continue
            expanded_keys = self._known_mapping_string_keys(keyword_value)
            if expanded_keys:
                has_keywords = True
            elif expanded_keys is None:
                # The expansion may be empty (and therefore mutating), so
                # fail closed instead of treating the call as invalid.
                continue
        valid_arity = bool(
            (
                method_name == "__setitem__"
                and positional_count == 2
                and not has_keywords
            )
            or (
                method_name in {"__delitem__", "__ior__"}
                and positional_count == 1
                and not has_keywords
            )
            or (
                method_name in {"clear", "popitem"}
                and positional_count == 0
                and not has_keywords
            )
            or (
                method_name in {"pop", "setdefault"}
                and positional_count in {1, 2}
                and not has_keywords
            )
            or (
                method_name == "update"
                and positional_count <= 1
            )
        )
        if not valid_arity:
            return None
        owner = self._protected_namespace_mapping_owner(protected_mapping)
        if owner is None:
            return None

        keys: frozenset[str] | None
        if method_name in {"__delitem__", "__setitem__", "pop", "setdefault"}:
            if not supplied_values:
                return None
            key = supplied_values[0]
            keys = (
                frozenset({str(key.value)})
                if key.kind == "scalar" and type(key.value) is str
                else None
            )
        elif method_name in {"__ior__", "update"}:
            retained_keys = {
                keyword.arg
                for keyword in node.keywords
                if keyword.arg is not None
            }
            keys = (
                None
                if any(keyword.arg is None for keyword in node.keywords)
                else frozenset(retained_keys)
            )
            for supplied in supplied_values:
                supplied_keys = self._known_mapping_string_keys(supplied)
                if supplied_keys is None:
                    keys = None
                    break
                if keys is not None:
                    keys = keys | supplied_keys
        else:
            keys = None

        if keys == frozenset():
            return None
        if not self._invalidate_protected_namespace_mapping(
            node,
            owner,
            keys,
            values,
        ):
            return None
        mutation_reason = (
            "protected namespace member mutation is dynamically unresolved"
        )
        if self.flow.standalone_blockers[-1:] == [(node, mutation_reason)]:
            self.flow.standalone_blockers.pop()
        self.flow.blockers_by_call[id(node)] = mutation_reason
        if method_name == "__ior__":
            return protected_mapping
        if method_name in {"__delitem__", "__setitem__", "clear", "update"}:
            return _FlowValue("scalar", None)
        return _flow_unknown(
            "protected mapping method result is dynamically unresolved",
            sensitive=True,
        )

    def _snapshot_call(
        self,
        node: ast.Call,
        values: Mapping[str, _FlowValue],
        callable_value: _FlowValue,
    ) -> None:
        key = id(node)
        self._call_states.setdefault(key, []).append(dict(values))
        self._call_values.setdefault(key, []).append(callable_value)
        merged_values = self._merge_states(self._call_states[key])
        merged_callable = _merge_flow_values(
            "call target",
            self._call_values[key],
        )
        self.flow.aliases_by_call[key] = _flow_aliases(merged_values)
        self.flow.assignments_by_call[key] = _flow_assignments(merged_values)
        self.flow.blockers_by_call.pop(key, None)
        self.flow.callables_by_call.pop(key, None)
        self.flow.environments_by_call.pop(key, None)
        self.flow.proved_non_sensitive_calls.discard(key)
        if merged_callable.kind in {"unknown", "maybe_unbound"} and (
            _flow_is_sensitive(merged_callable)
        ):
            self.flow.blockers_by_call[key] = (
                merged_callable.reason
                or "dynamic sensitive call target is unresolved"
            )
        callable_name: str | None = None
        if merged_callable.kind == "qname":
            callable_name = str(merged_callable.value)
        elif merged_callable.kind == "proved_non_sensitive_callable":
            callable_name = str(merged_callable.value)
            self.flow.proved_non_sensitive_calls.add(key)
        elif (
            merged_callable.kind == "callable_summary"
            and isinstance(merged_callable.value, tuple)
            and len(merged_callable.value) == 2
        ):
            callable_name = str(merged_callable.value[0])
        elif (
            merged_callable.kind == "deferred_local_generator_factory"
            and isinstance(
                merged_callable.value,
                _DeferredLocalGeneratorFactory,
            )
        ):
            callable_name = merged_callable.value.marker
        if callable_name is not None:
            self.flow.callables_by_call[key] = callable_name
        if callable_name in _SUBPROCESS_FUNCTIONS:
            keywords = {
                keyword.arg: keyword.value
                for keyword in node.keywords
                if keyword.arg is not None
            }
            self.flow.environments_by_call[key] = (
                self._environment_snapshot(keywords.get("env"), merged_values)
            )

    def _environment_snapshot(
        self,
        node: ast.expr | None,
        values: Mapping[str, _FlowValue],
    ) -> tuple[dict[str, str], list[str], str | None]:
        if node is None:
            return {}, [], None
        value = self._evaluate(node, dict(values), False)
        if value.kind == "environment":
            environment = value.value
            if not isinstance(environment, _FlowEnvironment):
                raise RuntimeError("environment flow value is malformed")
            return (
                dict(environment.additions),
                list(environment.removals),
                environment.poison,
            )
        if value.kind == "qname" and value.value == "os.environ":
            return {}, [], None
        if value.kind == "mapping":
            return {}, [], "subprocess environment replacement is forbidden"
        return {}, [], (
            value.reason or "subprocess environment is dynamically unresolved"
        )

    def _poison_environment(
        self,
        values: dict[str, _FlowValue],
        owner: str,
        reason: str,
    ) -> None:
        for name, value in tuple(values.items()):
            if value.kind != "environment":
                continue
            environment = value.value
            if not isinstance(environment, _FlowEnvironment):
                continue
            if environment.owner != owner:
                continue
            values[name] = _FlowValue(
                "environment",
                _FlowEnvironment(
                    owner,
                    environment.additions,
                    environment.removals,
                    reason,
                ),
                reason=reason,
            )

    def _mutate_environment(
        self,
        values: dict[str, _FlowValue],
        name: str,
        *,
        additions: Mapping[str, str] = {},
        removals: Iterable[str] = (),
    ) -> None:
        value = values.get(name)
        if value is None or value.kind != "environment":
            return
        environment = value.value
        if not isinstance(environment, _FlowEnvironment):
            return
        if name != environment.owner:
            self._poison_environment(
                values,
                environment.owner,
                "subprocess environment alias mutation is unresolved",
            )
            return
        updated = dict(environment.additions)
        removed = set(environment.removals)
        for key, item in additions.items():
            updated[key] = item
            removed.discard(key)
        for key in removals:
            updated.pop(key, None)
            removed.add(key)
        replacement = _FlowValue(
            "environment",
            _FlowEnvironment(
                environment.owner,
                tuple(sorted(updated.items())),
                tuple(sorted(removed)),
                environment.poison,
            ),
            reason=environment.poison,
        )
        for bound_name, bound_value in tuple(values.items()):
            if bound_value.kind != "environment":
                continue
            bound_environment = bound_value.value
            if (
                isinstance(bound_environment, _FlowEnvironment)
                and bound_environment.owner == environment.owner
            ):
                values[bound_name] = replacement

    def _record_throw_state(
        self,
        values: Mapping[str, _FlowValue],
        exception_tag: str | None = None,
        explicit: bool = False,
    ) -> None:
        if self._throw_states is not None:
            self._throw_states.append(
                _FlowExceptionalState(
                    dict(values),
                    exception_tag,
                    explicit,
                )
            )

    def _evaluate_with_successors(
        self,
        node: ast.AST | None,
        values: Mapping[str, _FlowValue],
        *,
        record: bool = True,
    ) -> tuple[bool, _FlowValue, dict[str, _FlowValue], list[_FlowExceptionalState]]:
        current = dict(values)
        outer = self._throw_states
        thrown: list[_FlowExceptionalState] = []
        self._throw_states = thrown
        try:
            try:
                result = self._evaluate(node, current, record)
            except _ExpressionDoesNotComplete:
                return False, _flow_unknown("expression does not complete"), current, thrown
            return True, result, current, thrown
        finally:
            self._throw_states = outer

    def _deferred_generator_value_is_sensitive(
        self,
        value: _FlowValue,
        values: Mapping[str, _FlowValue],
        *,
        include_value_sensitivity: bool = True,
    ) -> bool:
        """Resolve delayed generator sensitivity at the consumption point."""

        if value.kind == "deferred_local_generator":
            return self._deferred_local_generator_is_sensitive(value, values)
        if value.kind == "generator":
            state = value.value
            return bool(
                (include_value_sensitivity and value.sensitive)
                or (
                    isinstance(state, _DeferredGeneratorState)
                    and self._deferred_generator_state_is_sensitive(
                        state,
                        values,
                        include_value_sensitivity=include_value_sensitivity,
                    )
                )
            )
        if value.kind == "deferred_generator_merged":
            return bool(
                (include_value_sensitivity and value.sensitive)
                or any(
                    self._deferred_generator_state_is_sensitive(
                        candidate,
                        values,
                        include_value_sensitivity=include_value_sensitivity,
                    )
                    if isinstance(candidate, _DeferredGeneratorState)
                    else (
                        self._deferred_generator_value_is_sensitive(
                            candidate,
                            values,
                            include_value_sensitivity=include_value_sensitivity,
                        )
                        if isinstance(candidate, _FlowValue)
                        else False
                    )
                    for candidate in value.value
                )
            )
        if value.kind in {
            "sequence",
            "maybe_unbound",
            "deferred_generator_container_merged",
        }:
            return any(
                self._deferred_generator_value_is_sensitive(
                    candidate,
                    values,
                    include_value_sensitivity=include_value_sensitivity,
                )
                for candidate in value.value
                if isinstance(candidate, _FlowValue)
            )
        if value.kind == "mapping":
            return any(
                self._deferred_generator_value_is_sensitive(
                    candidate,
                    values,
                    include_value_sensitivity=include_value_sensitivity,
                )
                for _, candidate in value.value
                if isinstance(candidate, _FlowValue)
            )
        if value.kind == "starred_argument" and isinstance(
            value.value,
            _FlowValue,
        ):
            return self._deferred_generator_value_is_sensitive(
                value.value,
                values,
                include_value_sensitivity=include_value_sensitivity,
            )
        return False

    def _deferred_local_generator_is_sensitive(
        self,
        value: _FlowValue,
        values: Mapping[str, _FlowValue],
    ) -> bool:
        resume = self._resume_deferred_local_generator_value(
            value,
            dict(values),
            mode="full",
            publish=False,
        )
        return resume.sensitive

    def _scope_statement_contains_yield(self, statement: ast.stmt) -> bool:
        pending: list[ast.AST] = [statement]
        while pending:
            candidate = pending.pop()
            self.budget.consume()
            if isinstance(candidate, (ast.Yield, ast.YieldFrom)):
                return True
            if candidate is not statement and isinstance(
                candidate,
                (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef),
            ):
                continue
            pending.extend(ast.iter_child_nodes(candidate))
        return False

    def _local_generator_probe_is_sensitive(self) -> bool:
        if self.flow.blockers_by_call or self.flow.standalone_blockers:
            return True
        if any(
            qualified in _SUBPROCESS_FUNCTIONS
            or _is_sensitive_namespace(qualified)
            for qualified in self.flow.callables_by_call.values()
        ):
            return True
        return any(
            _flow_is_sensitive(callable_value)
            for call_values in self._call_values.values()
            for callable_value in call_values
        )

    @staticmethod
    def _local_generator_frame(
        definition: ast.FunctionDef,
        values: Mapping[str, _FlowValue],
    ) -> tuple[tuple[str, _FlowValue], ...]:
        scope = _lexical_binding_scope(definition)
        return tuple(
            (name, values[name])
            for name in sorted(scope.local_names)
            if name in values
        )

    @staticmethod
    def _replace_deferred_local_generator_state_in_value(
        value: _FlowValue,
        identity: int,
        replacement: _FlowValue,
    ) -> _FlowValue:
        if (
            value.kind == "deferred_local_generator"
            and isinstance(value.value, _DeferredLocalGeneratorState)
            and value.value.identity == identity
        ):
            return replacement
        if value.kind in {
            "deferred_generator_merged",
            "sequence",
            "maybe_unbound",
            "deferred_generator_container_merged",
        }:
            return replace(
                value,
                value=tuple(
                    _SourceOrderedResolver._replace_deferred_local_generator_state_in_value(
                        candidate,
                        identity,
                        replacement,
                    )
                    if isinstance(candidate, _FlowValue)
                    else candidate
                    for candidate in value.value
                ),
            )
        if value.kind == "mapping":
            return replace(
                value,
                value=tuple(
                    (
                        key,
                        _SourceOrderedResolver._replace_deferred_local_generator_state_in_value(
                            candidate,
                            identity,
                            replacement,
                        ),
                    )
                    for key, candidate in value.value
                ),
            )
        if value.kind == "starred_argument" and isinstance(
            value.value,
            _FlowValue,
        ):
            return replace(
                value,
                value=_SourceOrderedResolver._replace_deferred_local_generator_state_in_value(
                    value.value,
                    identity,
                    replacement,
                ),
            )
        return value

    def _replace_deferred_local_generator_state(
        self,
        values: dict[str, _FlowValue],
        identity: int,
        replacement: _FlowValue,
    ) -> None:
        for name, value in tuple(values.items()):
            values[name] = self._replace_deferred_local_generator_state_in_value(
                value,
                identity,
                replacement,
            )

    def _resume_deferred_local_generator_value(
        self,
        value: _FlowValue,
        values: dict[str, _FlowValue],
        *,
        mode: str,
        publish: bool,
    ) -> _DeferredLocalGeneratorResume:
        if value.kind == "deferred_local_generator":
            return self._resume_deferred_local_generator(
                value,
                values,
                mode=mode,
                publish=publish,
            )
        if value.kind == "deferred_generator_merged":
            sensitive = bool(value.sensitive)
            yielded = False
            normal = False
            raises: list[tuple[str | None, bool]] = []
            candidates: list[object] = []
            yielded_values: list[_FlowValue] = []
            for candidate in value.value:
                if isinstance(candidate, _FlowValue) and (
                    _flow_contains_deferred_local_generator(candidate)
                ):
                    resumed = self._resume_deferred_local_generator_value(
                        candidate,
                        values,
                        mode=mode,
                        publish=publish,
                    )
                    sensitive |= resumed.sensitive
                    yielded |= resumed.yielded
                    normal |= resumed.normal
                    raises.extend(resumed.raises)
                    candidates.append(resumed.value)
                    if resumed.yielded and resumed.yielded_value is not None:
                        yielded_values.append(resumed.yielded_value)
                else:
                    sensitive |= bool(
                        isinstance(candidate, _FlowValue)
                        and _flow_is_sensitive(candidate)
                    )
                    normal = True
                    candidates.append(candidate)
            return _DeferredLocalGeneratorResume(
                sensitive,
                replace(value, value=tuple(candidates)),
                yielded,
                normal,
                tuple(raises),
                (
                    _merge_flow_values(
                        "local generator yielded value",
                        tuple(yielded_values),
                    )
                    if yielded_values
                    else None
                ),
            )
        return _DeferredLocalGeneratorResume(True, value, False, True)

    def _resume_deferred_local_generator(
        self,
        value: _FlowValue,
        values: dict[str, _FlowValue],
        *,
        mode: str,
        publish: bool,
    ) -> _DeferredLocalGeneratorResume:
        state = value.value
        if not isinstance(state, _DeferredLocalGeneratorState):
            return _DeferredLocalGeneratorResume(True, value, False, True)
        if state.exhausted:
            return _DeferredLocalGeneratorResume(
                False,
                value,
                False,
                mode != "one",
                (("StopIteration", True),) if mode == "one" else (),
            )
        marker = state.factory.marker
        if not state.supported or marker in self._active_deferred_local_generators:
            return _DeferredLocalGeneratorResume(
                True,
                replace(value, value=replace(state, supported=False)),
                False,
                True,
            )
        if (
            len(self._active_deferred_local_generators)
            >= MAXIMUM_ANALYSIS_HELPER_DEPTH
        ):
            raise InventoryError("analysis deferred generator depth exceeds 64")
        self._active_deferred_local_generators.add(marker)

        outer_flow = self.flow
        outer_call_states = self._call_states
        outer_call_values = self._call_values
        outer_throw_states = self._throw_states
        outer_return_values = self.return_values
        outer_mutable_collection_versions = dict(
            self._mutable_collection_versions
        )
        outer_definitions = dict(self._deferred_local_generator_definitions)
        outer_local_definitions = dict(self._local_function_definitions)
        outer_plain_classes = set(self._plain_local_classes)
        outer_helper_returns = dict(self.helper_returns)
        outer_exception_scope = self.exception_scope
        outer_lexical_scope = self.lexical_scope
        self.flow = _ReviewFlow({}, {}, {}, {}, {}, {}, [])
        self._call_states = {}
        self._call_values = {}
        self._throw_states = []
        self.return_values = []
        definition = state.factory.definition
        definition_scope = _lexical_binding_scope(definition)
        self.lexical_scope = definition_scope
        self.exception_scope = _exception_name_scope(
            definition,
            self.exception_scope.shadowed_names,
            self.exception_scope.enclosing_names,
        )
        local = dict(values)
        for name in definition_scope.local_names - definition_scope.parameter_names:
            local[name] = _FlowValue(
                "unbound",
                reason="local name is unbound at generator entry",
            )
        refreshed_bindings: list[tuple[str, _FlowValue]] = []
        for name, binding in state.bindings:
            identity = binding.mutable_collection_identity
            refreshed = next(
                (
                    candidate
                    for candidate in values.values()
                    if identity is not None
                    and candidate.mutable_collection_identity == identity
                ),
                binding,
            )
            refreshed_bindings.append((name, refreshed))
        local.update(refreshed_bindings)
        refreshed_frame: list[tuple[str, _FlowValue]] = []
        for name, frame_value in state.frame:
            identity = frame_value.mutable_collection_identity
            refreshed = next(
                (
                    candidate
                    for candidate in values.values()
                    if identity is not None
                    and candidate.mutable_collection_identity == identity
                ),
                frame_value,
            )
            refreshed_frame.append((name, refreshed))
        local.update(refreshed_frame)
        index = state.statement_index
        delegate = state.delegate
        yielded = False
        yielded_value: _FlowValue | None = None
        exhausted = False
        normal_exhaustion = False
        supported = True
        nested_sensitive = False
        raised_outcomes: list[tuple[str | None, bool]] = []
        try:
            while index < len(definition.body):
                statement = definition.body[index]
                direct_yield = (
                    statement.value
                    if isinstance(statement, ast.Expr)
                    and isinstance(statement.value, (ast.Yield, ast.YieldFrom))
                    else None
                )
                if direct_yield is None:
                    if self._scope_statement_contains_yield(statement):
                        supported = False
                        break
                    successors = self._flow_statement(statement, local)
                    raised_outcomes.extend(
                        (exceptional.exception_tag, exceptional.explicit)
                        for exceptional in successors.raises
                    )
                    if (
                        successors.breaks
                        or successors.continues
                        or len(successors.normal) > 1
                    ):
                        supported = False
                        break
                    if successors.normal:
                        local = dict(successors.normal[0])
                        index += 1
                        continue
                    exhausted = True
                    normal_exhaustion = not successors.raises
                    index = len(definition.body)
                    break
                if isinstance(direct_yield, ast.YieldFrom):
                    if delegate is None:
                        throw_start = len(self._throw_states or ())
                        try:
                            delegate = self._evaluate(
                                direct_yield.value,
                                local,
                            )
                        except _ExpressionDoesNotComplete:
                            raised_outcomes.extend(
                                (
                                    exceptional.exception_tag,
                                    exceptional.explicit,
                                )
                                for exceptional in (self._throw_states or ())[
                                    throw_start:
                                ]
                            )
                            exhausted = True
                            index = len(definition.body)
                            break
                        raised_outcomes.extend(
                            (
                                exceptional.exception_tag,
                                exceptional.explicit,
                            )
                            for exceptional in (self._throw_states or ())[
                                throw_start:
                            ]
                        )
                    if not _flow_contains_deferred_local_generator(delegate):
                        supported = False
                        break
                    delegate_resume = self._resume_deferred_local_generator_value(
                        delegate,
                        local,
                        mode="full" if mode == "full" else "one",
                        publish=True,
                    )
                    delegate = delegate_resume.value
                    nested_sensitive |= delegate_resume.sensitive
                    raised_outcomes.extend(delegate_resume.raises)
                    if delegate_resume.raises and not delegate_resume.yielded:
                        exhausted = True
                        index = len(definition.body)
                        break
                    if delegate_resume.yielded and mode != "full":
                        yielded = True
                        yielded_value = delegate_resume.yielded_value
                        break
                    if delegate_resume.yielded:
                        continue
                    delegate = None
                    index += 1
                    continue
                throw_start = len(self._throw_states or ())
                try:
                    yielded_value = self._evaluate(direct_yield.value, local)
                except _ExpressionDoesNotComplete:
                    raised_outcomes.extend(
                        (
                            exceptional.exception_tag,
                            exceptional.explicit,
                        )
                        for exceptional in (self._throw_states or ())[throw_start:]
                    )
                    exhausted = True
                    index = len(definition.body)
                    break
                raised_outcomes.extend(
                    (exceptional.exception_tag, exceptional.explicit)
                    for exceptional in (self._throw_states or ())[throw_start:]
                )
                index += 1
                if mode != "full":
                    yielded = True
                    break
            else:
                exhausted = True
                normal_exhaustion = True
            if not supported:
                nested_sensitive = True
            scope = _lexical_binding_scope(definition)
            shared_identities = {
                candidate.mutable_collection_identity
                for candidate in values.values()
                if candidate.mutable_collection_identity is not None
            }
            unresolved_outward_mutation = any(
                local.get(
                    name,
                    _flow_unknown("outward generator value is unresolved"),
                ).kind
                in {"maybe_unbound", "unbound", "unknown"}
                for name in scope.nonlocal_names | scope.global_names
                if local.get(name) != values.get(name)
            )
            sensitive_outward_mutation = any(
                _flow_is_sensitive(local[name])
                for name in scope.nonlocal_names | scope.global_names
                if name in local and local.get(name) != values.get(name)
            )
            for identity in shared_identities:
                if (
                    self._mutable_collection_versions.get(identity, 0)
                    == outer_mutable_collection_versions.get(identity, 0)
                ):
                    continue
                replacement_value = next(
                    (
                        candidate
                        for candidate in local.values()
                        if candidate.mutable_collection_identity == identity
                    ),
                    None,
                )
                unresolved_outward_mutation |= bool(
                    replacement_value is None
                    or replacement_value.kind
                    in {"maybe_unbound", "unbound", "unknown"}
                )
                sensitive_outward_mutation |= bool(
                    replacement_value is not None
                    and _flow_is_sensitive(replacement_value)
                )
            sensitive = bool(
                nested_sensitive
                or unresolved_outward_mutation
                or sensitive_outward_mutation
                or self._local_generator_probe_is_sensitive()
            )
            updated_state = replace(
                state,
                bindings=tuple(refreshed_bindings),
                statement_index=index,
                frame=self._local_generator_frame(definition, local),
                delegate=delegate,
                supported=supported,
                exhausted=exhausted,
            )
            updated = replace(value, value=updated_state)
            probe_consumed = set(self.flow.consumed_local_generator_calls)
            final_versions = dict(self._mutable_collection_versions)
            commit_mutations = bool(
                publish and supported and not sensitive_outward_mutation
            )
            if commit_mutations:
                for name in scope.nonlocal_names | scope.global_names:
                    if name in local:
                        values[name] = local[name]
                for name, outer_value in tuple(values.items()):
                    identity = outer_value.mutable_collection_identity
                    if identity is None:
                        continue
                    replacement_value = next(
                        (
                            candidate
                            for candidate in local.values()
                            if candidate.mutable_collection_identity == identity
                        ),
                        None,
                    )
                    if replacement_value is not None:
                        values[name] = replacement_value
                self._mutable_collection_versions = final_versions
            if publish:
                self._replace_deferred_local_generator_state(
                    values,
                    state.identity,
                    updated,
                )
            if mode == "one" and normal_exhaustion and not yielded:
                raised_outcomes.append(("StopIteration", True))
            return _DeferredLocalGeneratorResume(
                sensitive,
                updated,
                yielded,
                bool(
                    yielded
                    or not supported
                    or (mode == "full" and normal_exhaustion)
                ),
                tuple(raised_outcomes),
                yielded_value,
            )
        finally:
            self.flow = outer_flow
            self.flow.consumed_local_generator_calls.update(
                locals().get("probe_consumed", set())
            )
            self._call_states = outer_call_states
            self._call_values = outer_call_values
            self._throw_states = outer_throw_states
            self.return_values = outer_return_values
            if not locals().get("commit_mutations", False):
                self._mutable_collection_versions = outer_mutable_collection_versions
            self._deferred_local_generator_definitions = outer_definitions
            self._local_function_definitions = outer_local_definitions
            self._plain_local_classes = outer_plain_classes
            self.exception_scope = outer_exception_scope
            self.lexical_scope = outer_lexical_scope
            self.helper_returns.clear()
            self.helper_returns.update(outer_helper_returns)
            self._active_deferred_local_generators.discard(marker)

    def _deferred_generator_outer_iterator_changed(
        self,
        state: _DeferredGeneratorState,
    ) -> bool:
        identity = state.outer_iterator_identity
        return bool(
            identity is not None
            and self._mutable_collection_versions.get(identity, 0)
            != state.outer_iterator_version
        )

    def _record_mutable_collection_mutation(
        self,
        owner: _FlowValue,
    ) -> None:
        """Advance one modeled mutable-container mutation for every alias."""

        identity = owner.mutable_collection_identity
        if not owner.mutable_collection or identity is None:
            return
        self._mutable_collection_versions[identity] = (
            self._mutable_collection_versions.get(identity, 0) + 1
        )

    def _poison_mutable_collection(
        self,
        owner: _FlowValue,
        values: dict[str, _FlowValue],
        *,
        sensitive: bool,
        reason: str,
    ) -> None:
        """Invalidate exact contents while retaining alias and epoch identity."""

        identity = owner.mutable_collection_identity
        if not owner.mutable_collection or identity is None:
            return
        for name, candidate in tuple(values.items()):
            if candidate.mutable_collection_identity != identity:
                continue
            values[name] = replace(
                candidate,
                kind="unknown",
                value=None,
                sensitive=(sensitive or _flow_is_sensitive(candidate)),
                reason=reason,
            )
        self._record_mutable_collection_mutation(owner)

    def _record_deferred_generator_consumption(
        self,
        value: _FlowValue,
        values: dict[str, _FlowValue],
        site: ast.AST,
        *,
        mode: str = "full",
        has_default: bool = False,
    ) -> _DeferredGeneratorConsumption:
        """Fail closed when a syntax boundary executes a protected generator."""

        candidate = (
            value.value
            if value.kind == "starred_argument"
            and isinstance(value.value, _FlowValue)
            else value
        )
        if candidate.kind not in {
            "generator",
            "deferred_generator_merged",
            "deferred_local_generator",
        }:
            return _DeferredGeneratorConsumption(False)
        normal = True
        yielded = False
        raises: tuple[tuple[str | None, bool], ...] = ()
        yielded_value: _FlowValue | None = None
        defaulted = False
        if _flow_contains_deferred_local_generator(candidate):
            creation_ids = _deferred_local_generator_creation_ids(candidate)
            self.flow.consumed_local_generator_calls.update(creation_ids)
            for creation_id in creation_ids:
                self.flow.local_generator_consumption_modes.setdefault(
                    creation_id,
                    set(),
                ).add(mode)
            resume = self._resume_deferred_local_generator_value(
                candidate,
                values,
                mode=mode,
                publish=True,
            )
            sensitive = resume.sensitive
            yielded = resume.yielded
            yielded_value = resume.yielded_value
            effective_raises: list[tuple[str | None, bool]] = []
            for exception_tag, explicit in resume.raises:
                if (
                    mode == "one"
                    and has_default
                    and exception_tag == "StopIteration"
                ):
                    defaulted = True
                    continue
                effective_raises.append((exception_tag, explicit))
                self._record_throw_state(
                    values,
                    exception_tag,
                    explicit,
                )
            raises = tuple(effective_raises)
            normal = bool(resume.normal or defaulted)
        else:
            sensitive = self._deferred_generator_value_is_sensitive(
                candidate,
                values,
                include_value_sensitivity=False,
            )
        if not sensitive:
            return _DeferredGeneratorConsumption(
                False,
                normal,
                yielded,
                raises,
                yielded_value,
                defaulted,
            )
        if (
            mode == "full"
            and candidate.kind == "deferred_local_generator"
            and isinstance(candidate.value, _DeferredLocalGeneratorState)
            and candidate.value.exact_full_review
            and candidate.value.supported
        ):
            return _DeferredGeneratorConsumption(
                False,
                normal,
                yielded,
                raises,
                yielded_value,
                defaulted,
            )
        self.flow.standalone_blockers.append((
            site,
            "deferred generator consumption is dynamically unresolved",
        ))
        return _DeferredGeneratorConsumption(
            True,
            normal,
            yielded,
            raises,
            yielded_value,
            defaulted,
        )

    def _terminate_unstarted_local_generator_value(
        self,
        value: _FlowValue,
        values: dict[str, _FlowValue],
        *,
        mode: str,
    ) -> tuple[_FlowValue, bool]:
        """Close one unstarted/closed local generator without running its body."""

        if value.kind == "deferred_local_generator":
            state = value.value
            if not isinstance(state, _DeferredLocalGeneratorState):
                return value, False
            self.flow.consumed_local_generator_calls.add(
                state.creation_call_id
            )
            self.flow.local_generator_consumption_modes.setdefault(
                state.creation_call_id,
                set(),
            ).add(mode)
            unstarted = bool(
                state.statement_index == 0
                and not state.frame
                and state.delegate is None
            )
            if not state.exhausted and not unstarted:
                return value, False
            updated = replace(
                state,
                statement_index=len(state.factory.definition.body),
                delegate=None,
                exhausted=True,
            )
            replacement = replace(value, value=updated)
            self._replace_deferred_local_generator_state(
                values,
                state.identity,
                replacement,
            )
            return replacement, True
        if value.kind == "deferred_generator_merged":
            exact = True
            candidates: list[object] = []
            for candidate in value.value:
                if (
                    isinstance(candidate, _FlowValue)
                    and _flow_contains_deferred_local_generator(candidate)
                ):
                    updated, candidate_exact = (
                        self._terminate_unstarted_local_generator_value(
                            candidate,
                            values,
                            mode=mode,
                        )
                    )
                    candidates.append(updated)
                    exact &= candidate_exact
                else:
                    candidates.append(candidate)
                    exact = False
            return replace(value, value=tuple(candidates)), exact
        return value, False

    def _deferred_generator_node_is_sensitive(
        self,
        node: ast.GeneratorExp,
        values: Mapping[str, _FlowValue],
    ) -> bool:
        """Recover a generator hidden by an unsupported argument expansion."""

        outer_flow = self.flow
        outer_call_states = self._call_states
        outer_call_values = self._call_values
        outer_throw_states = self._throw_states
        outer_mutable_collection_versions = dict(
            self._mutable_collection_versions
        )
        self.flow = _ReviewFlow({}, {}, {}, {}, {}, {}, [])
        self._call_states = {}
        self._call_values = {}
        self._throw_states = []
        try:
            try:
                supplied = self._evaluate(node, dict(values), False)
            except _ExpressionDoesNotComplete:
                return False
        finally:
            self.flow = outer_flow
            self._call_states = outer_call_states
            self._call_values = outer_call_values
            self._throw_states = outer_throw_states
            self._mutable_collection_versions = outer_mutable_collection_versions
        return self._deferred_generator_value_is_sensitive(supplied, values)

    def _deferred_generator_state_is_sensitive(
        self,
        state: _DeferredGeneratorState,
        values: Mapping[str, _FlowValue],
        *,
        include_value_sensitivity: bool = True,
    ) -> bool:
        """Probe reachable delayed expressions without publishing probe state."""

        outer_iterator_changed = (
            self._deferred_generator_outer_iterator_changed(state)
        )
        if state.remaining == 0 and not outer_iterator_changed:
            return False
        if state.identity in self._active_deferred_generator_probes:
            return True
        if (
            len(self._active_deferred_generator_probes)
            >= MAXIMUM_ANALYSIS_HELPER_DEPTH
        ):
            raise InventoryError(
                "analysis deferred generator depth exceeds 64"
            )
        self._active_deferred_generator_probes.add(state.identity)

        outer_flow = self.flow
        outer_call_states = self._call_states
        outer_call_values = self._call_values
        outer_throw_states = self._throw_states
        outer_mutable_collection_versions = dict(
            self._mutable_collection_versions
        )
        self.flow = _ReviewFlow({}, {}, {}, {}, {}, {}, [])
        self._call_states = {}
        self._call_values = {}
        self._throw_states = []
        observed_sensitive = False

        def probe_observed_sensitive() -> bool:
            if self.flow.blockers_by_call or self.flow.standalone_blockers:
                return True
            if any(
                qualified in _SUBPROCESS_FUNCTIONS
                or _is_sensitive_namespace(qualified)
                for qualified in self.flow.callables_by_call.values()
            ):
                return True
            return any(
                _flow_is_sensitive(callable_value)
                for call_values in self._call_values.values()
                for callable_value in call_values
            )

        def evaluate(
            expression: ast.expr,
            local: dict[str, _FlowValue],
        ) -> _FlowValue:
            nonlocal observed_sensitive
            named_targets = {
                name
                for candidate in ast.walk(expression)
                if isinstance(candidate, ast.NamedExpr)
                for name in _python_bound_names(candidate.target)
            }
            before = {name: local.get(name) for name in named_targets}
            try:
                supplied = self._evaluate(expression, local, True)
            finally:
                observed_sensitive |= any(
                    local.get(name) != before[name]
                    and isinstance(local.get(name), _FlowValue)
                    and _flow_is_sensitive(local[name])
                    for name in named_targets
                )
            if include_value_sensitivity:
                observed_sensitive |= _flow_is_sensitive(supplied)
            return supplied

        def probe_result() -> bool:
            return bool(
                observed_sensitive
                or self._mutable_collection_versions
                != outer_mutable_collection_versions
                or probe_observed_sensitive()
            )

        try:
            local = dict(values)
            node = state.expression
            first = node.generators[0]
            self._assign(
                first.target,
                _flow_unknown(
                    "generator target is dynamically unresolved",
                    sensitive=(
                        state.outer_iterator_sensitive
                        or outer_iterator_changed
                    ),
                ),
                local,
            )
            try:
                for condition in first.ifs:
                    supplied = evaluate(condition, local)
                    if supplied.kind == "scalar" and not bool(supplied.value):
                        return probe_result()
                for generator in node.generators[1:]:
                    iterator = evaluate(generator.iter, local)
                    if self._iteration_bound_value(iterator) == 0:
                        return probe_result()
                    self._assign(
                        generator.target,
                        _flow_unknown(
                            "generator target is dynamically unresolved",
                            sensitive=_flow_is_sensitive(iterator),
                        ),
                        local,
                    )
                    for condition in generator.ifs:
                        supplied = evaluate(condition, local)
                        if supplied.kind == "scalar" and not bool(supplied.value):
                            return probe_result()
                evaluate(node.elt, local)
            except _ExpressionDoesNotComplete:
                pass
            return probe_result()
        finally:
            self.flow = outer_flow
            self._call_states = outer_call_states
            self._call_values = outer_call_values
            self._throw_states = outer_throw_states
            self._mutable_collection_versions = outer_mutable_collection_versions
            self._active_deferred_generator_probes.discard(state.identity)

    def _consume_generator_expression(
        self,
        state: _DeferredGeneratorState,
        values: dict[str, _FlowValue],
        record: bool,
        *,
        has_default: bool,
    ) -> _FlowValue:
        outer_iterator_changed = (
            self._deferred_generator_outer_iterator_changed(state)
        )
        if outer_iterator_changed:
            state = replace(state, remaining=None, supported=False)
        if not state.supported:
            if not self._deferred_generator_state_is_sensitive(state, values):
                return _flow_unknown(
                    "deferred generator result is dynamically unresolved"
                )
            blocked_call = False
            had_observed_call = False
            for expression in _deferred_generator_expressions(state.expression):
                for candidate in ast.walk(expression):
                    if not isinstance(candidate, ast.Call):
                        continue
                    blocked_call = True
                    had_observed_call |= id(candidate) in self._call_states
                    self.flow.callables_by_call.pop(id(candidate), None)
                    self.flow.blockers_by_call[id(candidate)] = (
                        "deferred generator consumption is dynamically unresolved"
                    )
            if not blocked_call or not had_observed_call:
                self.flow.standalone_blockers.append((
                    state.expression,
                    "deferred generator consumption is dynamically unresolved",
                ))
            return _flow_unknown(
                "deferred generator consumption is dynamically unresolved"
            )
        if state.remaining == 0:
            if not has_default:
                self._record_throw_state(values, "StopIteration", True)
                if self._throw_states is not None:
                    raise _ExpressionDoesNotComplete
            return _FlowValue("scalar", None)
        node = state.expression
        next_state = replace(
            state,
            remaining=(
                None
                if state.remaining is None
                else max(0, state.remaining - 1)
            ),
        )
        # A generator closes if filter/body evaluation escapes.  Publish the
        # consumption transition before either fallible region so a caught
        # exception cannot replay the same item on the next call.
        self._replace_generator_state(
            values,
            state.identity,
            replace(state, remaining=0),
        )
        local = dict(values)
        first = node.generators[0]
        self._assign(
            first.target,
            _flow_unknown(
                (
                    "mixed protected receiver is dynamically unresolved"
                    if (
                        state.outer_iterator_sensitive
                        or outer_iterator_changed
                    )
                    else "generator target is dynamically unresolved"
                ),
                sensitive=(
                    state.outer_iterator_sensitive
                    or outer_iterator_changed
                ),
            ),
            local,
        )
        for condition in first.ifs:
            supplied = self._evaluate(condition, local, record)
            if supplied.kind == "scalar" and not bool(supplied.value):
                next_state = replace(state, remaining=0)
                self._replace_generator_state(values, state.identity, next_state)
                if not has_default:
                    self._record_throw_state(values, "StopIteration", True)
                    if self._throw_states is not None:
                        raise _ExpressionDoesNotComplete
                return _FlowValue("scalar", None)
        for generator in node.generators[1:]:
            iterator = self._evaluate(generator.iter, local, record)
            self._assign(
                generator.target,
                _flow_unknown(
                    "generator target is dynamically unresolved",
                    sensitive=_flow_is_sensitive(iterator),
                ),
                local,
            )
            for condition in generator.ifs:
                self._evaluate(condition, local, record)
        result = self._evaluate(node.elt, local, record)
        for candidate in ast.walk(node):
            if isinstance(candidate, ast.NamedExpr):
                for name in _python_bound_names(candidate.target):
                    if name in local:
                        values[name] = local[name]
        self._replace_generator_state(values, state.identity, next_state)
        return result

    @staticmethod
    def _replace_generator_state(
        values: dict[str, _FlowValue],
        identity: int,
        state: _DeferredGeneratorState,
    ) -> None:
        for name, value in tuple(values.items()):
            if (
                value.kind == "generator"
                and isinstance(value.value, _DeferredGeneratorState)
                and value.value.identity == identity
            ):
                values[name] = _FlowValue(
                    "generator",
                    state,
                )

    def _instantiate_deferred_local_generator(
        self,
        node: ast.Call,
        factory: _DeferredLocalGeneratorFactory,
        argument_values: Sequence[_FlowValue],
        keyword_values: Sequence[_FlowValue],
        values: Mapping[str, _FlowValue],
        *,
        exact_full_review: bool,
    ) -> _FlowValue:
        status, bindings = _bind_deferred_local_generator_call(
            node,
            factory,
            argument_values,
            keyword_values,
        )
        if status == "invalid":
            self._record_throw_state(values, "TypeError", True)
            if self._throw_states is not None:
                raise _ExpressionDoesNotComplete
            return _flow_unknown("local generator call raises TypeError")
        reconciled_bindings: list[tuple[str, _FlowValue]] = []
        for name, binding in bindings:
            identity = binding.mutable_collection_identity
            current = next(
                (
                    candidate
                    for candidate in values.values()
                    if identity is not None
                    and candidate.mutable_collection_identity == identity
                ),
                binding,
            )
            reconciled_bindings.append((name, current))
        identity = self._next_deferred_local_generator_identity
        self._next_deferred_local_generator_identity += 1
        return _FlowValue(
            "deferred_local_generator",
            _DeferredLocalGeneratorState(
                factory,
                identity,
                id(node),
                tuple(reconciled_bindings),
                supported=status == "valid",
                exact_full_review=(
                    exact_full_review
                    and factory.marker in self.sensitive_definition_markers
                ),
            ),
            False,
            "deferred local generator body is dynamically unresolved",
        )

    def _simple_local_helper_deferred_return(
        self,
        node: ast.Call,
        marker: str | None,
        argument_values: Sequence[_FlowValue],
        keyword_values: Sequence[_FlowValue],
        values: dict[str, _FlowValue],
        record: bool,
    ) -> _FlowValue | None:
        if marker is None or marker in self._active_local_helper_returns:
            return None
        supplied = self._local_function_definitions.get(marker)
        if supplied is None:
            return None
        definition, defaults = supplied
        if len(definition.body) != 1 or not isinstance(
            definition.body[0],
            ast.Return,
        ):
            return None
        factory = _DeferredLocalGeneratorFactory(marker, definition, defaults)
        status, bindings = _bind_deferred_local_generator_call(
            node,
            factory,
            argument_values,
            keyword_values,
        )
        if status != "valid":
            return None
        local = dict(values)
        local.update(
            (
                name,
                next(
                    (
                        candidate
                        for candidate in values.values()
                        if value.mutable_collection_identity is not None
                        and candidate.mutable_collection_identity
                        == value.mutable_collection_identity
                    ),
                    value,
                ),
            )
            for name, value in bindings
        )
        self._active_local_helper_returns.add(marker)
        try:
            returned = self._evaluate(
                definition.body[0].value,
                local,
                False,
            )
        finally:
            self._active_local_helper_returns.discard(marker)
        return returned if _flow_contains_deferred_generator(returned) else None

    def _evaluate(
        self,
        node: ast.AST | None,
        values: dict[str, _FlowValue],
        record: bool = True,
    ) -> _FlowValue:
        self.budget.consume()
        if node is None:
            return _FlowValue("scalar", None)
        if isinstance(node, ast.Constant):
            return _FlowValue("scalar", node.value)
        if isinstance(node, ast.Name):
            value = values.get(node.id)
            if value is not None and value.kind not in {"maybe_unbound", "unbound"}:
                return value
            if value is not None or node.id in self.exception_scope.shadowed_names:
                self._record_throw_state(
                    values,
                    self._lookup_error_tag(node.id),
                    True,
                )
                if (
                    (value is None or value.kind == "unbound")
                    and self._throw_states is not None
                ):
                    raise _ExpressionDoesNotComplete
                if value is not None and value.kind == "maybe_unbound":
                    alternatives = tuple(
                        candidate
                        for candidate in value.value
                        if isinstance(candidate, _FlowValue)
                    )
                    if alternatives:
                        return _merge_flow_values(node.id, alternatives)
                return _flow_unknown(f"{node.id} may be unbound")
            return _flow_qname(node.id)
        if isinstance(node, ast.Attribute):
            qualified = _qualified_name(node)
            if qualified is not None and qualified in values:
                return values[qualified]
            base = self._evaluate(node.value, values, record)
            if record:
                self._record_implicit_protocol_blocker(
                    node,
                    base,
                    frozenset({"__getattribute__", "__getattr__"}),
                    "implicit attribute-load protocol execution is dynamically unresolved",
                )
            if record and _flow_may_be_unittest_receiver(base):
                self.flow.receiver_attributes[id(node)] = node
            if base.kind in {
                "generator",
                "deferred_generator_merged",
                "deferred_local_generator",
            }:
                return _FlowValue(
                    "deferred_generator_method",
                    (base, node.attr),
                )
            if base.kind == "qname":
                canonical_member = f"{base.value}.{node.attr}"
                if canonical_member in values:
                    return values[canonical_member]
            stored = _flow_mapping_value(base, node.attr)
            if stored is not None:
                return stored
            if (
                base.kind == "object"
                and str(base.value).startswith(
                    (
                        "unittest.mock.MagicMock()",
                        "unittest.mock.Mock()",
                    )
                )
            ):
                return _FlowValue(
                    "proved_non_sensitive_callable",
                    f"{base.value}.{node.attr}",
                )
            if base.kind == "implicit_class_instance" and isinstance(
                base.value,
                _ImplicitClassDescriptor,
            ):
                descriptor_member = dict(
                    base.value.descriptor_members
                ).get(node.attr)
                if descriptor_member is not None:
                    if record:
                        self._record_implicit_protocol_blocker(
                            node,
                            _FlowValue(
                                "implicit_class_instance",
                                descriptor_member,
                            ),
                            frozenset({"__get__"}),
                            "implicit descriptor access is dynamically unresolved",
                        )
                    return _flow_unknown(
                        "descriptor result is dynamically unresolved",
                        sensitive=bool(
                            descriptor_member.sensitive_methods
                            & frozenset({"__get__"})
                        ),
                    )
                return _flow_qname(f"{base.value.name}().{node.attr}")
            if base.kind in {"qname", "object"}:
                return _flow_qname(f"{base.value}.{node.attr}")
            if _flow_is_sensitive(base):
                return _flow_unknown(
                    base.reason
                    or "mixed protected receiver is dynamically unresolved",
                    sensitive=True,
                )
            return _flow_unknown("attribute receiver is dynamically unresolved")
        if isinstance(node, ast.Subscript):
            base = self._evaluate(node.value, values, record)
            if isinstance(node.slice, ast.Slice):
                slice_values = tuple(
                    (bound, self._evaluate(bound, values, record))
                    for bound in (
                        node.slice.lower,
                        node.slice.upper,
                        node.slice.step,
                    )
                    if bound is not None
                )
                if record and self._proven_builtin_indexable(base):
                    for bound, bound_value in slice_values:
                        self._record_implicit_protocol_blocker(
                            bound,
                            bound_value,
                            _IMPLICIT_PROTOCOL_METHODS["index"],
                            "implicit slice-index protocol execution is dynamically unresolved",
                        )
                index = _flow_unknown("slice result is dynamically unresolved")
            else:
                index = self._evaluate(node.slice, values, record)
                if record and self._proven_builtin_indexable(base):
                    if index.kind == "slice":
                        for bound in index.value:
                            if (
                                isinstance(bound, _FlowValue)
                                and not (
                                    bound.kind == "scalar"
                                    and bound.value is None
                                )
                            ):
                                self._record_implicit_protocol_blocker(
                                    node.slice,
                                    bound,
                                    _IMPLICIT_PROTOCOL_METHODS["index"],
                                    "implicit slice-index protocol execution is dynamically unresolved",
                                )
                    else:
                        self._record_implicit_protocol_blocker(
                            node.slice,
                            index,
                            _IMPLICIT_PROTOCOL_METHODS["index"],
                            "implicit sequence-index protocol execution is dynamically unresolved",
                        )
                if record:
                    self._record_mapping_key_dispatch(
                        node.slice,
                        base,
                        index,
                        operation="lookup",
                    )
            if record:
                self._record_implicit_protocol_blocker(
                    node,
                    base,
                    (
                        frozenset({"__class_getitem__"})
                        if base.kind == "implicit_class"
                        else _IMPLICIT_PROTOCOL_METHODS["item_load"]
                    ),
                    (
                        "implicit class subscription is dynamically unresolved"
                        if base.kind == "implicit_class"
                        else "implicit item-load protocol execution is dynamically unresolved"
                    ),
                )
            self._record_throw_state(values, None, True)
            if (
                base.kind == "mapping_keys"
                and any(key.kind != "scalar" for key, _value in base.value)
            ):
                return _flow_unknown(
                    base.reason or "mapping key identity is dynamically unresolved",
                    sensitive=_flow_is_sensitive(base),
                )
            stored = _flow_mapping_value(
                base,
                index.value if index.kind == "scalar" else index,
            )
            if stored is not None:
                return stored
            if (
                base.kind == "sequence"
                and index.kind == "scalar"
                and type(index.value) is int
            ):
                try:
                    return base.value[index.value]
                except IndexError:
                    return _flow_unknown("subscript index is out of range")
            if _flow_is_sensitive(base):
                return _flow_unknown(
                    base.reason
                    or "mixed protected receiver is dynamically unresolved",
                    sensitive=True,
                )
            return _flow_unknown("subscript receiver is dynamically unresolved")
        if isinstance(node, ast.Starred):
            return _FlowValue(
                "starred_argument",
                self._evaluate(node.value, values, record),
            )
        if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
            self.budget.container(len(node.elts))
            mutable_collection_identity = (
                id(node) if isinstance(node, (ast.List, ast.Set)) else None
            )
            if mutable_collection_identity is not None:
                self._mutable_collection_versions.setdefault(
                    mutable_collection_identity,
                    0,
                )
            supplied_items: list[_FlowValue] = []
            for item in node.elts:
                supplied = self._evaluate(item, values, record)
                supplied_items.append(supplied)
                if record and isinstance(node, ast.Set) and not isinstance(
                    item,
                    ast.Starred,
                ):
                    self._record_implicit_protocol_blocker(
                        item,
                        supplied,
                        _IMPLICIT_PROTOCOL_METHODS["hash"],
                        "implicit set-element hash protocol execution is dynamically unresolved",
                    )
                    for prior in supplied_items[:-1]:
                        self._record_implicit_protocol_blocker(
                            item,
                            prior,
                            frozenset({"__eq__"}),
                            "implicit set-element equality protocol execution is dynamically unresolved",
                        )
                        self._record_implicit_protocol_blocker(
                            item,
                            supplied,
                            frozenset({"__eq__"}),
                            "implicit set-element equality protocol execution is dynamically unresolved",
                        )
                if isinstance(item, ast.Starred):
                    if record and isinstance(supplied.value, _FlowValue):
                        self._record_implicit_protocol_blocker(
                            item,
                            supplied.value,
                            _IMPLICIT_PROTOCOL_METHODS["iteration"],
                            "implicit iterator protocol execution is dynamically unresolved",
                        )
                    self._record_deferred_generator_consumption(
                        supplied,
                        values,
                        node,
                    )
            result = _FlowValue(
                "sequence",
                tuple(supplied_items),
                mutable_collection=isinstance(node, (ast.List, ast.Set)),
                mutable_collection_identity=mutable_collection_identity,
                container_kind=(
                    "list"
                    if isinstance(node, ast.List)
                    else "set"
                    if isinstance(node, ast.Set)
                    else "tuple"
                ),
            )
            if isinstance(node, ast.Set):
                self._record_throw_state(values, None, True)
            return result
        if isinstance(node, ast.Dict):
            self.budget.container(len(node.keys))
            additions: dict[str, str] = {}
            inherited = False
            items: list[tuple[str, _FlowValue]] = []
            keyed_items: list[tuple[_FlowValue, _FlowValue]] = []
            has_non_string_key = False
            unresolved_reason: str | None = None
            unresolved_sensitive = False
            for key_node, value_node in zip(node.keys, node.values, strict=True):
                if key_node is None:
                    expanded = self._evaluate(value_node, values, record)
                    if expanded.kind == "environment" or (
                        expanded.kind == "qname"
                        and expanded.value == "os.environ"
                    ):
                        inherited = True
                        if expanded.kind == "environment":
                            environment = expanded.value
                            if isinstance(environment, _FlowEnvironment):
                                additions.update(environment.additions)
                        continue
                    if expanded.kind in {
                        "scalar",
                        "sequence",
                        "range",
                        "exception_instance",
                    }:
                        self._record_throw_state(
                            values,
                            "TypeError",
                            True,
                        )
                        if self._throw_states is not None:
                            raise _ExpressionDoesNotComplete
                        return _flow_unknown(
                            "mapping expansion raises TypeError"
                        )
                    if expanded.kind == "mapping":
                        continue
                    if unresolved_reason is None:
                        unresolved_reason = "mapping expansion is unresolved"
                    unresolved_sensitive |= _flow_is_sensitive(expanded)
                    continue
                key = self._evaluate(key_node, values, record)
                if record:
                    self._record_implicit_protocol_blocker(
                        key_node,
                        key,
                        _IMPLICIT_PROTOCOL_METHODS["hash"],
                        "implicit mapping-key hash protocol execution is dynamically unresolved",
                    )
                    for prior_key, _prior_value in keyed_items:
                        self._record_implicit_protocol_blocker(
                            key_node,
                            prior_key,
                            frozenset({"__eq__"}),
                            "implicit mapping-key equality protocol execution is dynamically unresolved",
                        )
                        self._record_implicit_protocol_blocker(
                            key_node,
                            key,
                            frozenset({"__eq__"}),
                            "implicit mapping-key equality protocol execution is dynamically unresolved",
                        )
                value = self._evaluate(value_node, values, record)
                keyed_items.append((key, value))
                unresolved_sensitive |= (
                    _flow_is_sensitive(key) or _flow_is_sensitive(value)
                )
                if key.kind != "scalar" or type(key.value) is not str:
                    has_non_string_key = True
                    continue
                items.append((key.value, value))
                if value.kind == "scalar" and type(value.value) is str:
                    additions[key.value] = value.value
            if unresolved_reason is not None:
                return _flow_unknown(
                    (
                        "mixed protected receiver is dynamically unresolved"
                        if unresolved_sensitive
                        else unresolved_reason
                    ),
                    sensitive=unresolved_sensitive,
                )
            if inherited:
                self._record_throw_state(values, None, True)
                return _FlowValue(
                    "environment",
                    _FlowEnvironment(
                        "<literal-environment>",
                        tuple(sorted(additions.items())),
                    ),
                )
            self._record_throw_state(values, None, True)
            mutable_collection_identity = id(node)
            self._mutable_collection_versions.setdefault(
                mutable_collection_identity,
                0,
            )
            if has_non_string_key:
                return _FlowValue(
                    "mapping_keys",
                    tuple(keyed_items),
                    sensitive=unresolved_sensitive,
                    reason=(
                        "mixed protected receiver is dynamically unresolved"
                        if unresolved_sensitive
                        else "mapping key identity is dynamically unresolved"
                    ),
                    mutable_collection=True,
                    mutable_collection_identity=mutable_collection_identity,
                    container_kind="dict",
                )
            return _FlowValue(
                "mapping",
                tuple(items),
                mutable_collection=True,
                mutable_collection_identity=mutable_collection_identity,
                container_kind="dict",
            )
        if isinstance(node, ast.BinOp):
            left = self._evaluate(node.left, values, record)
            right = self._evaluate(node.right, values, record)
            if record:
                direct, reflected, _inplace = _binary_protocol_methods(node.op)
                self._record_implicit_protocol_blocker(
                    node,
                    left,
                    direct,
                    "implicit binary protocol execution is dynamically unresolved",
                )
                self._record_implicit_protocol_blocker(
                    node,
                    right,
                    reflected,
                    "implicit binary protocol execution is dynamically unresolved",
                )
            self._record_throw_state(values, None, True)
            if (
                isinstance(node.op, ast.Add)
                and
                left.kind == "scalar"
                and right.kind == "scalar"
                and type(left.value) is str
                and type(right.value) is str
            ):
                return _FlowValue("scalar", left.value + right.value)
            return _flow_unknown(
                "binary value is dynamically unresolved",
                sensitive=_flow_is_sensitive(left) or _flow_is_sensitive(right),
            )
        if isinstance(node, ast.BoolOp):
            outer = self._throw_states
            active: list[dict[str, _FlowValue]] = [dict(values)]
            finished: list[tuple[dict[str, _FlowValue], _FlowValue]] = []
            for index, item in enumerate(node.values):
                following: list[dict[str, _FlowValue]] = []
                for incoming in active:
                    completed, supplied, current, thrown = (
                        self._evaluate_with_successors(
                            item,
                            incoming,
                            record=record,
                        )
                    )
                    if outer is not None:
                        outer.extend(thrown)
                    if not completed:
                        continue
                    if index == len(node.values) - 1:
                        finished.append((current, supplied))
                        continue
                    if record:
                        self._record_implicit_protocol_blocker(
                            item,
                            supplied,
                            _IMPLICIT_PROTOCOL_METHODS["truth"],
                            "implicit truth-value protocol execution is dynamically unresolved",
                        )
                    if supplied.kind == "scalar":
                        short_circuits = (
                            isinstance(node.op, ast.And)
                            and not bool(supplied.value)
                        ) or (
                            isinstance(node.op, ast.Or)
                            and bool(supplied.value)
                        )
                        if short_circuits:
                            finished.append((current, supplied))
                        else:
                            following.append(current)
                        continue
                    # Unknown truthiness has both the short-circuit and the
                    # continue successor; only the latter evaluates later
                    # operands and commits their side effects.
                    finished.append((dict(current), supplied))
                    following.append(current)
                active = following
                if not active and index < len(node.values) - 1:
                    break
            if not finished:
                raise _ExpressionDoesNotComplete
            values.clear()
            values.update(self._merge_states(tuple(state for state, _ in finished)))
            return _merge_flow_values(
                "boolean expression",
                tuple(supplied for _, supplied in finished),
            )
        if isinstance(node, ast.IfExp):
            test = self._evaluate(node.test, values, record)
            if record:
                self._record_implicit_protocol_blocker(
                    node.test,
                    test,
                    _IMPLICIT_PROTOCOL_METHODS["truth"],
                    "implicit truth-value protocol execution is dynamically unresolved",
                )
            if test.kind == "scalar" and type(test.value) is bool:
                chosen = node.body if test.value else node.orelse
                return self._evaluate(chosen, values, record)
            outer = self._throw_states
            completed_branches: list[
                tuple[dict[str, _FlowValue], _FlowValue]
            ] = []
            for branch in (node.body, node.orelse):
                completed, supplied, current, thrown = (
                    self._evaluate_with_successors(
                        branch,
                        values,
                        record=record,
                    )
                )
                if outer is not None:
                    outer.extend(thrown)
                if completed:
                    completed_branches.append((current, supplied))
            if not completed_branches:
                raise _ExpressionDoesNotComplete
            values.clear()
            values.update(self._merge_states(tuple(
                state for state, _ in completed_branches
            )))
            return _merge_flow_values(
                "conditional expression",
                tuple(value for _, value in completed_branches),
            )
        if isinstance(node, ast.UnaryOp):
            operand = self._evaluate(node.operand, values, record)
            if record:
                self._record_implicit_protocol_blocker(
                    node,
                    operand,
                    _unary_protocol_methods(node.op),
                    (
                        "implicit truth-value protocol execution is dynamically unresolved"
                        if isinstance(node.op, ast.Not)
                        else "implicit unary protocol execution is dynamically unresolved"
                    ),
                )
            self._record_throw_state(values, None, True)
            return _flow_unknown(
                (
                    "mixed protected receiver is dynamically unresolved"
                    if _flow_is_sensitive(operand)
                    else "unary value is dynamically unresolved"
                ),
                sensitive=_flow_is_sensitive(operand),
            )
        if isinstance(node, ast.FormattedValue):
            supplied = self._evaluate(node.value, values, record)
            self._evaluate(node.format_spec, values, record)
            if record:
                methods = (
                    frozenset({"__str__"})
                    if node.conversion == ord("s")
                    else frozenset({"__repr__"})
                    if node.conversion in {ord("r"), ord("a")}
                    else _IMPLICIT_PROTOCOL_METHODS["format"]
                )
                self._record_implicit_protocol_blocker(
                    node,
                    supplied,
                    methods,
                    "implicit formatting protocol execution is dynamically unresolved",
                )
            self._record_throw_state(values, None, True)
            return _FlowValue("scalar", "")
        if isinstance(node, ast.NamedExpr):
            value = self._evaluate(node.value, values, record)
            self._assign(node.target, value, values)
            return value
        if isinstance(node, ast.Lambda):
            for default in (*node.args.defaults, *node.args.kw_defaults):
                if default is not None:
                    self._evaluate(default, values, record)
            if isinstance(node.body, ast.Constant):
                return _FlowValue("callable_constant", node.body.value)
            return _FlowValue(
                "callback",
                node,
                _contains_sensitive_runtime(node.body, self.budget),
                "callback closure",
            )
        if isinstance(node, ast.Call):
            callable_value = self._evaluate(node.func, values, record)
            argument_values: list[_FlowValue] = []
            starred_consumption_blocked = False
            for argument in node.args:
                supplied = self._evaluate(argument, values, record)
                argument_values.append(supplied)
                if isinstance(argument, ast.Starred):
                    starred_consumption_blocked |= (
                        self._record_deferred_generator_consumption(
                            supplied,
                            values,
                            node,
                        ).blocked
                    )
            keyword_values: list[_FlowValue] = []
            for keyword in node.keywords:
                keyword_values.append(self._evaluate(keyword.value, values, record))
            if record:
                self._record_implicit_protocol_blocker(
                    node,
                    callable_value,
                    _IMPLICIT_PROTOCOL_METHODS["call"],
                    "implicit callable protocol execution is dynamically unresolved",
                )
                self._snapshot_call(node, values, callable_value)
                if any(
                    value.kind == "callback" and value.sensitive
                    for value in (*argument_values, *keyword_values)
                ):
                    self.flow.blockers_by_call[id(node)] = "callback closure"
            if callable_value.kind == "deferred_generator_method":
                owner, method_name = callable_value.value
                if (
                    method_name == "__iter__"
                    and not argument_values
                    and not keyword_values
                ):
                    return owner
                if method_name == "close":
                    if argument_values or keyword_values:
                        self._record_throw_state(values, "TypeError", True)
                        if self._throw_states is not None:
                            raise _ExpressionDoesNotComplete
                        return _flow_unknown(
                            "generator close call does not complete normally"
                        )
                    _, exact_close = (
                        self._terminate_unstarted_local_generator_value(
                            owner,
                            values,
                            mode="close",
                        )
                    )
                    if exact_close:
                        return _FlowValue("scalar", None)
                    self.flow.standalone_blockers.append((
                        node,
                        "deferred generator consumption is dynamically unresolved",
                    ))
                    return _flow_unknown(
                        "deferred generator consumption is dynamically unresolved",
                        sensitive=True,
                    )
                if method_name == "throw":
                    _, exact_throw = (
                        self._terminate_unstarted_local_generator_value(
                            owner,
                            values,
                            mode="throw",
                        )
                    )
                    if (
                        exact_throw
                        and len(argument_values) == 1
                        and not keyword_values
                        and argument_values[0].kind == "exception_instance"
                    ):
                        self._record_throw_state(
                            values,
                            str(argument_values[0].value),
                            True,
                        )
                        if self._throw_states is not None:
                            raise _ExpressionDoesNotComplete
                        return _flow_unknown(
                            "generator throw call does not complete normally"
                        )
                    self.flow.standalone_blockers.append((
                        node,
                        "deferred generator consumption is dynamically unresolved",
                    ))
                    self._record_throw_state(values)
                    return _flow_unknown(
                        "deferred generator consumption is dynamically unresolved",
                        sensitive=True,
                    )
                one_step_method = bool(
                    (
                        method_name == "__next__"
                        and not argument_values
                    )
                    or (
                        method_name == "send"
                        and len(argument_values) == 1
                        and argument_values[0].kind == "scalar"
                        and argument_values[0].value is None
                    )
                ) and not keyword_values
                consumption = self._record_deferred_generator_consumption(
                    owner,
                    values,
                    node,
                    mode="one" if one_step_method else "full",
                )
                if (
                    not consumption.normal
                    and consumption.raises
                    and self._throw_states is not None
                ):
                    raise _ExpressionDoesNotComplete
                if consumption.blocked:
                    return _flow_unknown(
                        "deferred generator consumption is dynamically unresolved",
                        sensitive=True,
                    )
                return _flow_unknown(
                    "generator method result is dynamically unresolved"
                )
            callable_name = (
                str(callable_value.value)
                if callable_value.kind in {
                    "proved_non_sensitive_callable",
                    "qname",
                }
                else None
            )
            summary: _BoundedCallableSummary | None = None
            if callable_value.kind == "callable_summary":
                supplied = callable_value.value
                if (
                    isinstance(supplied, tuple)
                    and len(supplied) == 2
                    and isinstance(supplied[1], _BoundedCallableSummary)
                ):
                    callable_name = str(supplied[0])
                    summary = supplied[1]
            if (
                record
                and isinstance(node.func, ast.Subscript)
                and callable_name in _PROTECTED_NAMESPACE_MEMBERS
            ):
                self.flow.blockers_by_call[id(node)] = (
                    "protected callable mapping lookup is outside the exact "
                    "call-site census"
                )
            if record and callable_name in {"max", "min"}:
                self._record_extreme_call(
                    node,
                    callable_name,
                    argument_values,
                    keyword_values,
                    values,
                )
            if record and argument_values:
                builtin_protocol = _BUILTIN_IMPLICIT_PROTOCOLS.get(
                    callable_name or ""
                )
                if (
                    builtin_protocol is not None
                    and callable_name not in {"max", "min"}
                ):
                    self._record_implicit_protocol_blocker(
                        node,
                        argument_values[0],
                        builtin_protocol,
                        "implicit builtin protocol execution is dynamically unresolved",
                    )
                for argument_index, protocol in (
                    _CALL_ARGUMENT_IMPLICIT_PROTOCOLS.get(
                        callable_name or "",
                        (),
                    )
                ):
                    if argument_index < len(argument_values):
                        self._record_implicit_protocol_blocker(
                            node,
                            argument_values[argument_index],
                            protocol,
                            "implicit library protocol execution is dynamically unresolved",
                        )
                for argument_index, protocol in (
                    _CALL_CONTAINER_ELEMENT_IMPLICIT_PROTOCOLS.get(
                        callable_name or "",
                        (),
                    )
                ):
                    if argument_index >= len(argument_values):
                        continue
                    container = argument_values[argument_index]
                    if container.kind == "sequence":
                        elements = tuple(container.value)
                    elif container.kind == "mapping":
                        elements = tuple(
                            _FlowValue("scalar", key)
                            for key, _value in container.value
                        )
                    elif container.kind == "mapping_keys":
                        elements = tuple(
                            key for key, _value in container.value
                        )
                    else:
                        continue
                    for element in elements:
                        operands = (
                            self._lexicographic_comparison_values(element)
                            if callable_name == "sorted"
                            else (element,)
                        )
                        for operand in operands:
                            self._record_implicit_protocol_blocker(
                                node,
                                operand,
                                protocol,
                                "implicit container-element protocol execution is dynamically unresolved",
                            )
            if record:
                keyword_protocols = _CALL_KEYWORD_IMPLICIT_PROTOCOLS.get(
                    callable_name or "",
                    {},
                )
                for keyword, keyword_value in zip(
                    node.keywords,
                    keyword_values,
                    strict=True,
                ):
                    protocol = (
                        keyword_protocols.get(keyword.arg)
                        if keyword.arg is not None
                        else None
                    )
                    if protocol is not None:
                        self._record_implicit_protocol_blocker(
                            keyword.value,
                            keyword_value,
                            protocol,
                            "implicit keyword protocol execution is dynamically unresolved",
                        )
            if (
                callable_name == "slice"
                and 1 <= len(argument_values) <= 3
                and not keyword_values
            ):
                supplied_bounds = tuple(argument_values)
                if len(supplied_bounds) == 1:
                    supplied_bounds = (
                        _FlowValue("scalar", None),
                        supplied_bounds[0],
                        _FlowValue("scalar", None),
                    )
                elif len(supplied_bounds) == 2:
                    supplied_bounds = (
                        supplied_bounds[0],
                        supplied_bounds[1],
                        _FlowValue("scalar", None),
                    )
                return _FlowValue("slice", supplied_bounds)
            if (
                callable_name in {"classmethod", "staticmethod"}
                and len(argument_values) == 1
                and not keyword_values
            ):
                return argument_values[0]
            if callable_value.kind == "implicit_class" and isinstance(
                callable_value.value,
                _ImplicitClassDescriptor,
            ):
                descriptor = callable_value.value
                callable_name = descriptor.name
                constructor_is_unresolved = (
                    "__new__" in descriptor.sensitive_methods
                    or (
                        "__init__" in descriptor.sensitive_methods
                        and (
                            not descriptor.exact_init_review
                            or descriptor.custom_new
                        )
                    )
                )
                if (
                    record
                    and constructor_is_unresolved
                    and id(node) not in self.flow.implicit_blocked_calls
                ):
                    self.flow.standalone_blockers.append((
                        node,
                        "implicit class constructor execution is dynamically unresolved",
                    ))
                    self.flow.implicit_blocked_calls.add(id(node))
                    self.flow.implicit_protocol_events.append((
                        node,
                        descriptor,
                        frozenset({"__new__", "__init__"}),
                        "implicit class constructor execution is dynamically unresolved",
                    ))
                if record:
                    self._record_implicit_protocol_blocker(
                        node,
                        _FlowValue("implicit_class_instance", descriptor),
                        frozenset({"__del__"}),
                        "implicit object finalizer execution is dynamically unresolved",
                    )
                if not self._expression_is_proven_nonthrowing(node, values):
                    self._record_throw_state(values)
                return _FlowValue(
                    "implicit_class_instance",
                    descriptor,
                    bool(descriptor.sensitive_methods),
                    "implicit class protocol execution is dynamically unresolved",
                )
            if (
                callable_value.kind == "deferred_local_generator_factory"
                and isinstance(
                    callable_value.value,
                    _DeferredLocalGeneratorFactory,
                )
            ):
                callable_name = callable_value.value.marker
                return self._instantiate_deferred_local_generator(
                    node,
                    callable_value.value,
                    argument_values,
                    keyword_values,
                    values,
                    exact_full_review=record,
                )
            if callable_value.kind == "deferred_local_generator_factory_merged":
                candidates: list[_FlowValue] = []
                for candidate in callable_value.value:
                    if (
                        isinstance(candidate, _FlowValue)
                        and candidate.kind == "deferred_local_generator_factory"
                        and isinstance(
                            candidate.value,
                            _DeferredLocalGeneratorFactory,
                        )
                    ):
                        status, _ = _bind_deferred_local_generator_call(
                            node,
                            candidate.value,
                            argument_values,
                            keyword_values,
                        )
                        if status == "invalid":
                            self._record_throw_state(values, "TypeError", True)
                            continue
                        candidates.append(
                            self._instantiate_deferred_local_generator(
                                node,
                                candidate.value,
                                argument_values,
                                keyword_values,
                                values,
                                exact_full_review=False,
                            )
                        )
                    elif isinstance(candidate, _FlowValue):
                        candidates.append(
                            _flow_unknown(
                                "merged local generator call target is unresolved",
                                sensitive=_flow_is_sensitive(candidate),
                            )
                        )
                if not candidates:
                    if self._throw_states is not None:
                        raise _ExpressionDoesNotComplete
                    return _flow_unknown(
                        "merged local generator call has no normal successor"
                    )
                return _FlowValue(
                    "deferred_generator_merged",
                    tuple(candidates),
                    False,
                    "deferred generator consumption is dynamically unresolved",
                )
            helper_return = self._simple_local_helper_deferred_return(
                node,
                callable_name,
                argument_values,
                keyword_values,
                values,
                record,
            )
            if helper_return is not None:
                return helper_return
            constructor_success, constructor_error, constructor_unknown = (
                _builtin_exception_constructor_outcome(
                    node,
                    self.exception_scope,
                )
            )
            if constructor_error is not None and constructor_success is None:
                self._record_throw_state(
                    values,
                    constructor_error,
                    True,
                )
                if self._throw_states is not None:
                    raise _ExpressionDoesNotComplete
                return _flow_unknown(
                    "exception constructor does not complete normally"
                )
            must_raise_tag = self.helper_raises.get(callable_name or "")
            summary_shape: str | None = None
            if summary is not None:
                summary_shape = _bounded_call_shape(node, summary)
                if summary_shape == "invalid":
                    must_raise_tag = "TypeError"
                elif summary_shape == "valid":
                    must_raise_tag = summary.exception_tag
            if callable_name == "next" and (
                len(node.args) not in {1, 2} or bool(node.keywords)
            ):
                must_raise_tag = "TypeError"
            modeled_next = bool(
                callable_name == "next"
                and argument_values
                and argument_values[0].kind == "generator"
                and isinstance(
                    argument_values[0].value,
                    _DeferredGeneratorState,
                )
                and argument_values[0].value.supported
            )
            modeled_local_consumption = bool(
                argument_values
                and _flow_contains_deferred_local_generator(argument_values[0])
                and not node.keywords
                and (
                    callable_name == "list" and len(node.args) == 1
                    or callable_name == "next" and len(node.args) in {1, 2}
                )
            )
            direct_tuple_expression = _direct_builtin_tuple_generator(
                node,
                callee_is_unshadowed_builtin=(
                    callable_value.kind == "qname"
                    and callable_value.value == "tuple"
                ),
            )
            direct_tuple_state = (
                argument_values[0].value
                if (
                    direct_tuple_expression is not None
                    and argument_values
                    and argument_values[0].kind == "generator"
                    and isinstance(
                        argument_values[0].value,
                        _DeferredGeneratorState,
                    )
                )
                else None
            )
            modeled_tuple = bool(
                direct_tuple_state is not None
                and direct_tuple_state.expression is direct_tuple_expression
                and direct_tuple_state.supported
                and direct_tuple_state.remaining is not None
            )
            if callable_value.kind == "callable_constant":
                return _FlowValue("scalar", callable_value.value)
            if (
                constructor_success is None or constructor_unknown
            ) and (
                must_raise_tag is not None
                or (
                    not modeled_next
                    and not modeled_tuple
                    and not modeled_local_consumption
                    and not (
                        summary is not None
                        and summary_shape == "valid"
                        and summary.proven_normal_only
                    )
                    and not self._expression_is_proven_nonthrowing(
                        node,
                        values,
                    )
                )
            ):
                self._record_throw_state(
                    values,
                    must_raise_tag,
                    must_raise_tag is not None,
                )
            if must_raise_tag is not None and self._throw_states is not None:
                raise _ExpressionDoesNotComplete
            if constructor_success is not None and not constructor_unknown:
                return _FlowValue(
                    "exception_instance",
                    constructor_success,
                )
            if modeled_tuple and direct_tuple_state is not None:
                materialized: list[_FlowValue] = []
                current = direct_tuple_state
                for _ in range(direct_tuple_state.remaining or 0):
                    materialized.append(
                        self._consume_generator_expression(
                            current,
                            values,
                            record,
                            has_default=False,
                        )
                    )
                    current = replace(
                        current,
                        remaining=(
                            None
                            if current.remaining is None
                            else max(0, current.remaining - 1)
                        ),
                    )
                return _FlowValue("sequence", tuple(materialized))
            tuple_generator_candidate = bool(
                callable_name == "tuple"
                and len(node.args) == 1
                and not node.keywords
                and (
                    (
                        argument_values
                        and argument_values[0].kind
                        in {"generator", "deferred_generator_merged"}
                    )
                    or any(
                        isinstance(candidate, ast.GeneratorExp)
                        for candidate in ast.walk(node.args[0])
                    )
                )
            )
            if tuple_generator_candidate:
                reason = "deferred generator consumption is dynamically unresolved"
                sensitive = any(
                    self._deferred_generator_value_is_sensitive(value, values)
                    if value.kind in {"generator", "deferred_generator_merged"}
                    else _flow_is_sensitive(value)
                    for value in argument_values
                )
                if not sensitive:
                    sensitive = any(
                        self._deferred_generator_node_is_sensitive(candidate, values)
                        for candidate in ast.walk(node.args[0])
                        if isinstance(candidate, ast.GeneratorExp)
                    )
                if sensitive:
                    self.flow.standalone_blockers.append((node, reason))
                return _flow_unknown(reason, sensitive=sensitive)
            if (
                callable_name == "next"
                and argument_values
                and argument_values[0].kind == "generator"
                and isinstance(
                    argument_values[0].value,
                    _DeferredGeneratorState,
                )
            ):
                return self._consume_generator_expression(
                    argument_values[0].value,
                    values,
                    record,
                    has_default=len(node.args) >= 2,
                )
            if (
                callable_name == "next"
                and argument_values
                and _flow_contains_deferred_local_generator(argument_values[0])
            ):
                consumption = self._record_deferred_generator_consumption(
                    argument_values[0],
                    values,
                    node,
                    mode="one",
                    has_default=len(node.args) >= 2,
                )
                if (
                    not consumption.normal
                    and consumption.raises
                    and self._throw_states is not None
                ):
                    raise _ExpressionDoesNotComplete
                if (
                    len(node.args) >= 2
                    and consumption.normal
                    and not consumption.yielded
                    and not consumption.raises
                    and not consumption.blocked
                ):
                    return argument_values[1]
                if consumption.yielded_value is not None:
                    result_candidates = [consumption.yielded_value]
                    if consumption.defaulted and len(argument_values) >= 2:
                        result_candidates.append(argument_values[1])
                    return _merge_flow_values(
                        "local generator next result",
                        tuple(result_candidates),
                    )
                return _flow_unknown(
                    "deferred generator consumption is dynamically unresolved",
                    sensitive=consumption.blocked,
                )
            if (
                callable_name == "next"
                and argument_values
                and argument_values[0].kind == "deferred_generator_merged"
            ):
                sensitive = self._deferred_generator_value_is_sensitive(
                    argument_values[0],
                    values,
                )
                if sensitive:
                    self.flow.standalone_blockers.append((
                        node,
                        "deferred generator consumption is dynamically unresolved",
                    ))
                return _flow_unknown(
                    "deferred generator consumption is dynamically unresolved",
                    sensitive=sensitive,
                )
            if (
                callable_name == "list"
                and argument_values
                and _flow_contains_deferred_generator(argument_values[0])
            ):
                consumption = self._record_deferred_generator_consumption(
                    argument_values[0],
                    values,
                    node,
                    mode="full",
                )
                if (
                    not consumption.normal
                    and consumption.raises
                    and self._throw_states is not None
                ):
                    raise _ExpressionDoesNotComplete
                return _flow_unknown(
                    "deferred generator consumption is dynamically unresolved",
                    sensitive=consumption.blocked,
                )
            deferred_local_definition = (
                self._deferred_local_generator_definitions.get(
                    str(callable_name)
                )
            )
            if deferred_local_definition is not None:
                return self._instantiate_deferred_local_generator(
                    node,
                    deferred_local_definition,
                    argument_values,
                    keyword_values,
                    values,
                    exact_full_review=record,
                )
            returned = self.helper_returns.get(str(callable_name))
            if returned is not None and (
                returned.kind == "implicit_class_instance"
                or (not node.args and not node.keywords)
            ):
                if (
                    returned.kind == "implicit_class_instance"
                    and isinstance(returned.value, _ImplicitClassDescriptor)
                ):
                    descriptor = returned.value
                    constructor_is_unresolved = (
                        "__new__" in descriptor.sensitive_methods
                        or (
                            "__init__" in descriptor.sensitive_methods
                            and (
                                not descriptor.exact_init_review
                                or descriptor.custom_new
                            )
                        )
                    )
                    if (
                        record
                        and constructor_is_unresolved
                        and id(node) not in self.flow.implicit_blocked_calls
                    ):
                        self.flow.standalone_blockers.append((
                            node,
                            "implicit class constructor execution is dynamically unresolved",
                        ))
                        self.flow.implicit_blocked_calls.add(id(node))
                if returned.kind in {"sequence", "mapping"}:
                    self.budget.container(len(returned.value))
                if returned.mutable_collection_identity is not None:
                    self._mutable_collection_versions.setdefault(
                        returned.mutable_collection_identity,
                        0,
                    )
                return returned
            if (
                callable_name == "vars"
                and len(argument_values) == 1
                and not keyword_values
                and argument_values[0].kind == "qname"
            ):
                mapping = _flow_qname(f"{argument_values[0].value}.__dict__")
                if self._protected_namespace_mapping_owner(mapping) is not None:
                    return mapping
            protected_mapping_result = self._invalidate_protected_mapping_call(
                node,
                callable_name,
                argument_values,
                keyword_values,
                values,
            )
            if protected_mapping_result is not None:
                return protected_mapping_result
            if (
                callable_name in {"setattr", "delattr"}
                and len(argument_values) >= 2
            ):
                base, attribute = argument_values[:2]
                if (
                    base.kind == "qname"
                    and attribute.kind == "scalar"
                    and type(attribute.value) is str
                    and self._invalidate_protected_path(
                        node,
                        f"{base.value}.{attribute.value}",
                        values,
                    )
                ):
                    return _FlowValue("scalar", None)
            if callable_name == "getattr" and len(argument_values) in {2, 3}:
                base, attribute = argument_values[:2]
                descriptor_members: list[_ImplicitClassDescriptor] = []
                literal_attribute = (
                    str(attribute.value)
                    if attribute.kind == "scalar"
                    and type(attribute.value) is str
                    else None
                )
                for descriptor in self._implicit_protocol_descriptors(base):
                    members = dict(descriptor.descriptor_members)
                    if literal_attribute is not None:
                        member = members.get(literal_attribute)
                        if member is not None and member not in descriptor_members:
                            descriptor_members.append(member)
                    else:
                        for member in members.values():
                            if member not in descriptor_members:
                                descriptor_members.append(member)
                if descriptor_members:
                    descriptor_value = (
                        _FlowValue(
                            "implicit_class_instance",
                            descriptor_members[0],
                        )
                        if len(descriptor_members) == 1
                        else _FlowValue(
                            "implicit_protocol_merged",
                            tuple(
                                _FlowValue("implicit_class_instance", member)
                                for member in descriptor_members
                            ),
                            any(
                                bool(member.sensitive_methods)
                                for member in descriptor_members
                            ),
                            "implicit descriptor access is dynamically unresolved",
                        )
                    )
                    if record:
                        self._record_implicit_protocol_blocker(
                            node,
                            descriptor_value,
                            frozenset({"__get__"}),
                            "implicit descriptor access is dynamically unresolved",
                        )
                    return _flow_unknown(
                        "descriptor result is dynamically unresolved",
                        sensitive=any(
                            bool(
                                member.sensitive_methods
                                & frozenset({"__get__"})
                            )
                            for member in descriptor_members
                        ),
                    )
                if (
                    base.kind == "qname"
                    and attribute.kind == "scalar"
                    and type(attribute.value) is str
                ):
                    return _flow_qname(f"{base.value}.{attribute.value}")
                if _flow_is_sensitive(base):
                    return _flow_unknown(
                        "dynamic sensitive call target is unresolved",
                        sensitive=True,
                    )
            if (
                callable_name == "__import__"
                and len(argument_values) == 1
                and argument_values[0].kind == "scalar"
                and type(argument_values[0].value) is str
            ):
                return _flow_qname(str(argument_values[0].value))
            if callable_name == "dict" and len(node.args) == 1:
                supplied = argument_values[0]
                if supplied.kind == "qname" and supplied.value == "os.environ":
                    return _FlowValue(
                        "environment",
                        _FlowEnvironment("<pending-environment>"),
                    )
                if supplied.kind == "environment":
                    return supplied
            if callable_name in _SAFE_OBSERVATION_CALLS:
                return _flow_unknown("observation result is dynamically unresolved")
            if callable_name in _SAFE_MOCK_FACTORIES:
                return _FlowValue("object", "unittest.mock.Mock()")
            if (
                callable_name in self._plain_local_classes
                and not argument_values
                and not keyword_values
            ):
                return _FlowValue("object", f"{callable_name}()")
            if callable_name in _BUILTIN_EXCEPTION_ANCESTORS:
                return _FlowValue("exception_instance", callable_name)
            if callable_name == "range" and 1 <= len(argument_values) <= 3:
                if all(
                    value.kind == "scalar" and type(value.value) is int
                    for value in argument_values
                ):
                    raw_values = [int(value.value) for value in argument_values]
                    if len(raw_values) == 3 and raw_values[2] == 0:
                        raise InventoryError("analysis range step is zero")
                    try:
                        length = len(range(*raw_values))
                    except (OverflowError, ValueError) as error:
                        raise InventoryError(
                            "analysis range cardinality exceeds 2147483647"
                        ) from error
                    return _FlowValue(
                        "range",
                        self.budget.cardinality(length),
                    )
            if isinstance(node.func, ast.Attribute):
                owner_name = (
                    node.func.value.id
                    if isinstance(node.func.value, ast.Name)
                    else None
                )
                direct_owner = self._evaluate(node.func.value, values, False)
                protected_copy_owner = (
                    self._protected_namespace_mapping_owner(direct_owner)
                    if (
                        node.func.attr == "copy"
                        and not argument_values
                        and not keyword_values
                    )
                    else None
                )
                if (
                    protected_copy_owner is not None
                ):
                    identity = id(node)
                    self._mutable_collection_versions.setdefault(identity, 0)
                    namespace_owner = (
                        protected_copy_owner.rpartition(".")[0]
                        if protected_copy_owner in _PROTECTED_NAMESPACE_MEMBERS
                        else protected_copy_owner
                    )
                    snapshot: dict[str, _FlowValue] = {}
                    prefix = f"{namespace_owner}."
                    for member in sorted(_PROTECTED_NAMESPACE_MEMBERS):
                        if not member.startswith(prefix):
                            continue
                        key = member.removeprefix(prefix).split(".", 1)[0]
                        path = f"{namespace_owner}.{key}"
                        snapshot.setdefault(
                            key,
                            values.get(path, _flow_qname(path)),
                        )
                    self.budget.container(len(snapshot))
                    return _FlowValue(
                        "mapping",
                        tuple(snapshot.items()),
                        mutable_collection=True,
                        mutable_collection_identity=identity,
                        container_kind="dict",
                    )
                if (
                    direct_owner.kind == "mapping"
                    and direct_owner.mutable_collection_identity is not None
                    and node.func.attr in {"items", "keys", "values"}
                    and not argument_values
                    and not keyword_values
                ):
                    if node.func.attr == "keys":
                        view_values = tuple(
                            _FlowValue("scalar", key)
                            for key, _ in direct_owner.value
                        )
                    elif node.func.attr == "values":
                        view_values = tuple(
                            value for _, value in direct_owner.value
                        )
                    else:
                        view_values = tuple(
                            _FlowValue(
                                "sequence",
                                (_FlowValue("scalar", key), value),
                            )
                            for key, value in direct_owner.value
                        )
                    return _FlowValue(
                        "sequence",
                        view_values,
                        mutable_collection=True,
                        mutable_collection_identity=(
                            direct_owner.mutable_collection_identity
                        ),
                    )
                mutation_methods = {
                    "__delitem__",
                    "__iadd__",
                    "__iand__",
                    "__imul__",
                    "__ior__",
                    "__isub__",
                    "__ixor__",
                    "__setitem__",
                    "add",
                    "append",
                    "clear",
                    "difference_update",
                    "discard",
                    "extend",
                    "insert",
                    "intersection_update",
                    "pop",
                    "popitem",
                    "remove",
                    "reverse",
                    "setdefault",
                    "sort",
                    "symmetric_difference_update",
                    "update",
                }
                if (
                    direct_owner.mutable_collection
                    and direct_owner.mutable_collection_identity is not None
                    and node.func.attr in mutation_methods
                ):
                    mutation_sensitive = bool(
                        _flow_is_sensitive(direct_owner)
                        or any(
                            _flow_is_sensitive(value)
                            for value in (*argument_values, *keyword_values)
                        )
                    )
                    self._record_throw_state(values, None, True)
                    self._poison_mutable_collection(
                        direct_owner,
                        values,
                        sensitive=mutation_sensitive,
                        reason="mixed protected receiver is dynamically unresolved",
                    )
                    if node.func.attr in {
                        "__delitem__",
                        "__setitem__",
                        "add",
                        "append",
                        "clear",
                        "difference_update",
                        "discard",
                        "extend",
                        "insert",
                        "intersection_update",
                        "remove",
                        "reverse",
                        "sort",
                        "symmetric_difference_update",
                        "update",
                    }:
                        return _FlowValue("scalar", None)
                    if node.func.attr in {
                        "__iadd__",
                        "__iand__",
                        "__imul__",
                        "__ior__",
                        "__isub__",
                        "__ixor__",
                    }:
                        return replace(
                            direct_owner,
                            kind="unknown",
                            value=None,
                            sensitive=mutation_sensitive,
                            reason=(
                                "mixed protected receiver is dynamically unresolved"
                            ),
                        )
                    return _flow_unknown(
                        "mutable collection method result is dynamically unresolved",
                        sensitive=mutation_sensitive,
                    )
                if (
                    node.func.attr == "copy"
                    and not node.args
                    and direct_owner.kind == "qname"
                    and direct_owner.value == "os.environ"
                ):
                    return _FlowValue(
                        "environment",
                        _FlowEnvironment("<pending-environment>"),
                    )
                if owner_name is None:
                    owner_value = None
                else:
                    owner_value = values.get(owner_name)
                if owner_value is not None and owner_value.kind == "environment":
                    if node.func.attr == "copy" and not node.args:
                        return owner_value
                    if node.func.attr == "update" and len(argument_values) == 1:
                        supplied = argument_values[0]
                        if supplied.kind == "mapping":
                            additions: dict[str, str] = {}
                            for key, item in supplied.value:
                                if item.kind != "scalar" or type(item.value) is not str:
                                    self._poison_environment(
                                        values,
                                        owner_value.value.owner,
                                        "subprocess environment update is unresolved",
                                    )
                                    break
                                additions[key] = item.value
                            else:
                                self._mutate_environment(
                                    values,
                                    owner_name,
                                    additions=additions,
                                )
                        else:
                            self._poison_environment(
                                values,
                                owner_value.value.owner,
                                "subprocess environment update is unresolved",
                            )
                        return _FlowValue("scalar", None)
                    if node.func.attr == "pop" and argument_values:
                        key = argument_values[0]
                        if key.kind == "scalar" and type(key.value) is str:
                            self._mutate_environment(
                                values,
                                owner_name,
                                removals=(key.value,),
                            )
                        else:
                            self._poison_environment(
                                values,
                                owner_value.value.owner,
                                "subprocess environment removal is unresolved",
                            )
                        return _flow_unknown("environment pop return is unresolved")
            if (
                callable_name
                == "pontius.cupy_sparse_incidence._cupy_modules"
            ):
                return _FlowValue(
                    "sequence",
                    (_flow_qname("cupy"), _flow_unknown("module tuple tail")),
                )
            invalid_direct_tuple_shape = bool(
                callable_name == "tuple"
                and isinstance(node.func, ast.Name)
                and node.func.id == "tuple"
                and not any(
                    isinstance(argument, ast.Starred) for argument in node.args
                )
                and (len(node.args) > 1 or bool(node.keywords))
            )
            local_consumer_blocked = False
            if not invalid_direct_tuple_shape and not starred_consumption_blocked:
                for supplied in (*argument_values, *keyword_values):
                    if not _flow_contains_deferred_local_generator(supplied):
                        continue
                    local_consumer_blocked |= (
                        self._record_deferred_generator_consumption(
                            supplied,
                            values,
                            node,
                            mode="full",
                        ).blocked
                    )
            deferred_consumer_sensitive = bool(
                not invalid_direct_tuple_shape
                and not starred_consumption_blocked
                and not local_consumer_blocked
                and any(
                    self._deferred_generator_value_is_sensitive(
                        value,
                        values,
                        include_value_sensitivity=False,
                    )
                    for value in (*argument_values, *keyword_values)
                )
            )
            if local_consumer_blocked:
                return _flow_unknown(
                    "deferred generator consumption is dynamically unresolved",
                    sensitive=True,
                )
            if deferred_consumer_sensitive:
                reason = "deferred generator consumption is dynamically unresolved"
                self.flow.standalone_blockers.append((node, reason))
                return _flow_unknown(reason, sensitive=True)
            escaped_call_sensitive = any(
                _flow_is_sensitive(value)
                for value in (*argument_values, *keyword_values)
            )
            escaped_collection_identities: set[int] = set()
            for escaped in (*argument_values, *keyword_values):
                identity = escaped.mutable_collection_identity
                if (
                    not escaped.mutable_collection
                    or identity is None
                    or identity in escaped_collection_identities
                ):
                    continue
                escaped_collection_identities.add(identity)
                self._poison_mutable_collection(
                    escaped,
                    values,
                    sensitive=True,
                    reason="mixed protected receiver is dynamically unresolved",
                )
            if callable_name is not None and _is_sensitive_namespace(callable_name):
                return _FlowValue(
                    "object",
                    f"{callable_name}()",
                    sensitive=True,
                )
            if escaped_call_sensitive:
                return _flow_unknown(
                    "dynamic sensitive call result is unresolved",
                    sensitive=True,
                )
            return _flow_unknown("call result is dynamically unresolved")
        if isinstance(node, (ast.Await, ast.Yield, ast.YieldFrom)):
            supplied = self._evaluate(node.value, values, record)
            if record and isinstance(node, ast.Await):
                self._record_implicit_protocol_blocker(
                    node,
                    supplied,
                    _IMPLICIT_PROTOCOL_METHODS["await"],
                    "implicit await protocol execution is dynamically unresolved",
                )
            if isinstance(node, ast.YieldFrom):
                if record:
                    self._record_implicit_protocol_blocker(
                        node,
                        supplied,
                        _IMPLICIT_PROTOCOL_METHODS["iteration"],
                        "implicit iterator protocol execution is dynamically unresolved",
                    )
                self._record_deferred_generator_consumption(
                    supplied,
                    values,
                    node,
                )
            self._record_throw_state(values)
            return supplied
        if isinstance(
            node,
            (ast.ListComp, ast.SetComp, ast.GeneratorExp, ast.DictComp),
        ):
            if isinstance(node, ast.GeneratorExp):
                # Only the outermost iterable is evaluated at creation.
                iterator = self._evaluate(
                    node.generators[0].iter,
                    values,
                    record,
                )
                if record:
                    self._record_implicit_protocol_blocker(
                        node.generators[0].iter,
                        iterator,
                        _IMPLICIT_PROTOCOL_METHODS["iteration"],
                        "implicit iterator protocol execution is dynamically unresolved",
                    )
                remaining = self._iteration_bound_value(iterator)
                outer_iterator_identity = iterator.mutable_collection_identity
                outer_iterator_version = self._mutable_collection_versions.get(
                    outer_iterator_identity,
                    0,
                )
                outer_deferred_sensitive = bool(
                    iterator.kind in {"generator", "deferred_generator_merged"}
                    and self._deferred_generator_value_is_sensitive(
                        iterator,
                        values,
                        include_value_sensitivity=False,
                    )
                )
                proven_empty_filter = any(
                    isinstance(condition, ast.Constant)
                    and not bool(condition.value)
                    for condition in node.generators[0].ifs
                )
                if proven_empty_filter:
                    remaining = 0
                elif outer_iterator_version:
                    remaining = None
                self.flow.iterator_bounds[id(node.generators[0].iter)] = remaining
                setattr(
                    node.generators[0].iter,
                    "_pontius_iteration_bound",
                    remaining,
                )
                supported = bool(
                    remaining is not None
                    and not outer_deferred_sensitive
                    and len(node.generators) == 1
                    and all(
                        isinstance(condition, ast.Constant)
                        or (
                            isinstance(condition, ast.Call)
                            and isinstance(condition.func, ast.Name)
                            and (
                                filter_value := values.get(condition.func.id)
                            ) is not None
                            and filter_value.kind == "callable_summary"
                            and isinstance(filter_value.value, tuple)
                            and len(filter_value.value) == 2
                            and isinstance(
                                filter_value.value[1],
                                _BoundedCallableSummary,
                            )
                            and filter_value.value[1].exception_tag is not None
                            and _bounded_call_shape(
                                condition,
                                filter_value.value[1],
                            ) == "valid"
                        )
                        for condition in node.generators[0].ifs
                    )
                )
                state = _DeferredGeneratorState(
                    node,
                    id(node),
                    remaining,
                    supported,
                    _flow_is_sensitive(iterator) or outer_deferred_sensitive,
                    outer_iterator_identity,
                    outer_iterator_version,
                )
                return _FlowValue("generator", state)
            repeated: int | None = 1
            local_values = dict(values)
            may_skip_evaluation = False
            skipped_states: list[dict[str, _FlowValue]] = []
            for generator in node.generators:
                if repeated == 0:
                    break
                try:
                    iterator = self._evaluate(
                        generator.iter,
                        local_values,
                        record,
                    )
                    if record:
                        self._record_implicit_protocol_blocker(
                            generator.iter,
                            iterator,
                            (
                                _IMPLICIT_PROTOCOL_METHODS["async_iteration"]
                                if generator.is_async
                                else _IMPLICIT_PROTOCOL_METHODS["iteration"]
                            ),
                            "implicit iterator protocol execution is dynamically unresolved",
                        )
                    self._record_deferred_generator_consumption(
                        iterator,
                        local_values,
                        generator.iter,
                    )
                except _ExpressionDoesNotComplete:
                    if not skipped_states:
                        raise
                    local_values = self._merge_states(skipped_states)
                    repeated = 0
                    break
                bound = self._iteration_bound_value(iterator)
                self.flow.iterator_bounds[id(generator.iter)] = bound
                setattr(generator.iter, "_pontius_iteration_bound", bound)
                if bound is None:
                    repeated = None
                    may_skip_evaluation = True
                else:
                    repeated = (
                        None
                        if repeated is None
                        else self.budget.cardinality(
                            _checked_cardinality_multiply(repeated, bound)
                        )
                    )
                if bound == 0:
                    break
                if iterator.kind == "sequence" and iterator.value:
                    iteration_value = _merge_flow_values(
                        "comprehension target",
                        tuple(iterator.value),
                    )
                else:
                    iteration_value = _flow_unknown(
                        "comprehension target is dynamically unresolved",
                        sensitive=_flow_is_sensitive(iterator),
                    )
                if (
                    isinstance(generator.target, (ast.Tuple, ast.List))
                    and iteration_value.kind == "sequence"
                    and len(generator.target.elts) != len(iteration_value.value)
                ):
                    self._record_throw_state(
                        local_values,
                        "ValueError",
                        True,
                    )
                    if self._throw_states is not None:
                        raise _ExpressionDoesNotComplete
                    return _flow_unknown(
                        "comprehension target unpack does not complete"
                    )
                self._assign(generator.target, iteration_value, local_values)
                for condition in generator.ifs:
                    condition_value = self._evaluate(
                        condition,
                        local_values,
                        record,
                    )
                    if record:
                        self._record_implicit_protocol_blocker(
                            condition,
                            condition_value,
                            _IMPLICIT_PROTOCOL_METHODS["truth"],
                            "implicit truth-value protocol execution is dynamically unresolved",
                        )
                    if (
                        condition_value.kind == "scalar"
                        and not bool(condition_value.value)
                    ):
                        repeated = 0
                        break
                    if not (
                        condition_value.kind == "scalar"
                        and bool(condition_value.value)
                    ):
                        repeated = None
                        may_skip_evaluation = True
                        skipped_states.append(dict(local_values))
                if repeated == 0:
                    break
            expressions = (
                (node.key, node.value)
                if isinstance(node, ast.DictComp)
                else (node.elt,)
            )
            values_out: list[_FlowValue] = []
            body_completed = repeated == 0
            if repeated != 0:
                try:
                    for expression in expressions:
                        values_out.append(
                            self._evaluate(expression, local_values, record)
                        )
                    body_completed = True
                except _ExpressionDoesNotComplete:
                    if not skipped_states:
                        raise
            if skipped_states:
                reaching = [*skipped_states]
                if body_completed and repeated != 0:
                    reaching.append(local_values)
                local_values = self._merge_states(reaching)
            comprehension_targets = {
                candidate.target.id
                for candidate in _metered_ast_walk(node, self.budget)
                if isinstance(candidate, ast.NamedExpr)
                and isinstance(candidate.target, ast.Name)
            }
            for name in comprehension_targets:
                if name in local_values:
                    if may_skip_evaluation and (
                        values.get(name) is not None
                        and values[name].kind == "qname"
                        and (
                            local_values[name].kind != "qname"
                            or values[name] != local_values[name]
                        )
                        and (
                            _flow_is_sensitive(values[name])
                            or _flow_is_sensitive(local_values[name])
                        )
                    ):
                        values[name] = _flow_unknown(
                            "callable alias is dynamically unresolved",
                            sensitive=True,
                        )
                    else:
                        values[name] = (
                            _merge_flow_values(
                                name,
                                (values.get(name), local_values[name]),
                            )
                            if may_skip_evaluation
                            else local_values[name]
                        )
            sensitive_result = any(
                _flow_is_sensitive(value) for value in values_out
            )
            self._record_throw_state(values, None, True)
            if repeated is None:
                return _flow_unknown(
                    (
                        "mixed protected receiver is dynamically unresolved"
                        if sensitive_result
                        else "comprehension result is not materialized"
                    ),
                    sensitive=sensitive_result,
                )
            storage_width = 2 if isinstance(node, ast.DictComp) else 1
            expanded_storage = _checked_cardinality_multiply(
                repeated,
                storage_width,
            )
            if expanded_storage > MAXIMUM_ANALYSIS_CONTAINER_ELEMENTS:
                return _flow_unknown(
                    (
                        "mixed protected receiver is dynamically unresolved"
                        if sensitive_result
                        else "comprehension result is not materialized"
                    ),
                    sensitive=sensitive_result,
                )
            mutable_collection_identity = (
                id(node) if isinstance(node, ast.ListComp) else None
            )
            if mutable_collection_identity is not None:
                self._mutable_collection_versions.setdefault(
                    mutable_collection_identity,
                    0,
                )
            return _FlowValue(
                "sequence",
                tuple(values_out) * repeated,
                mutable_collection=isinstance(node, ast.ListComp),
                mutable_collection_identity=mutable_collection_identity,
            )
        if isinstance(node, ast.Compare):
            compared_values = [self._evaluate(node.left, values, record)]
            for operator, comparator in zip(
                node.ops,
                node.comparators,
                strict=True,
            ):
                supplied = self._evaluate(comparator, values, record)
                previous = compared_values[-1]
                compared_values.append(supplied)
                if isinstance(operator, (ast.In, ast.NotIn)):
                    if record:
                        self._record_mapping_key_dispatch(
                            node,
                            supplied,
                            previous,
                            operation="membership",
                        )
                        self._record_implicit_protocol_blocker(
                            node,
                            supplied,
                            frozenset({"__contains__", "__iter__", "__getitem__"}),
                            "implicit membership protocol execution is dynamically unresolved",
                        )
                    self._record_deferred_generator_consumption(
                        supplied,
                        values,
                        node,
                    )
                elif not isinstance(operator, (ast.Is, ast.IsNot)) and record:
                    left_methods, right_methods = (
                        _comparison_protocol_methods(operator)
                    )
                    self._record_implicit_protocol_blocker(
                        node,
                        previous,
                        left_methods,
                        "implicit comparison protocol execution is dynamically unresolved",
                    )
                    self._record_implicit_protocol_blocker(
                        node,
                        supplied,
                        right_methods,
                        "implicit comparison protocol execution is dynamically unresolved",
                    )
            sensitive = any(
                _flow_is_sensitive(value) for value in compared_values
            )
            self._record_throw_state(values, None, True)
            return _flow_unknown(
                "comparison result is dynamically unresolved",
                sensitive=sensitive,
            )
        child_values = [
            self._evaluate(child, values, record)
            for child in ast.iter_child_nodes(node)
        ]
        sensitive = any(_flow_is_sensitive(value) for value in child_values)
        return _flow_unknown(
            (
                "mixed protected receiver is dynamically unresolved"
                if sensitive
                else "expression is dynamically unresolved"
            ),
            sensitive=sensitive,
        )

    @staticmethod
    def _iteration_bound_value(value: _FlowValue) -> int | None:
        if value.kind == "sequence":
            return len(value.value)
        if value.kind == "mapping":
            return len(value.value)
        if value.kind == "range":
            return int(value.value)
        return None

    def _assign(
        self,
        target: ast.expr,
        value: _FlowValue,
        values: dict[str, _FlowValue],
    ) -> None:
        if isinstance(target, ast.Name):
            if value.kind == "environment":
                environment = value.value
                if (
                    isinstance(environment, _FlowEnvironment)
                    and environment.owner == "<pending-environment>"
                ):
                    value = _FlowValue(
                        "environment",
                        _FlowEnvironment(
                            target.id,
                            environment.additions,
                            environment.removals,
                            environment.poison,
                        ),
                        reason=environment.poison,
                    )
            values[target.id] = value
            return
        subscript_owner: _FlowValue | None = None
        subscript_index: _FlowValue | None = None
        if isinstance(target, ast.Subscript):
            subscript_owner = self._evaluate(target.value, values, False)
            subscript_index = self._evaluate(target.slice, values, False)
            owner = self._protected_namespace_mapping_owner(subscript_owner)
            if owner is not None:
                keys = (
                    frozenset({str(subscript_index.value)})
                    if (
                        subscript_index.kind == "scalar"
                        and type(subscript_index.value) is str
                    )
                    else None
                )
                if self._invalidate_protected_namespace_mapping(
                    target,
                    owner,
                    keys,
                    values,
                ):
                    return
            self._record_implicit_protocol_blocker(
                target,
                subscript_owner,
                _IMPLICIT_PROTOCOL_METHODS["item_store"],
                "implicit item-store protocol execution is dynamically unresolved",
            )
            self._record_mapping_key_dispatch(
                target,
                subscript_owner,
                subscript_index,
                operation="store",
            )
        if isinstance(target, (ast.Tuple, ast.List)):
            self._record_implicit_protocol_blocker(
                target,
                value,
                _IMPLICIT_PROTOCOL_METHODS["iteration"],
                "implicit destructuring protocol execution is dynamically unresolved",
            )
            self._record_deferred_generator_consumption(
                value,
                values,
                target,
            )
            if value.kind != "sequence" or len(target.elts) != len(value.value):
                ambiguous = (
                    value
                    if _flow_may_be_unittest_receiver(value)
                    else _flow_unknown(
                        "sequence assignment is dynamically unresolved",
                        sensitive=_flow_is_sensitive(value),
                    )
                )
                for item in target.elts:
                    self._assign(item, ambiguous, values)
                return
            for item, supplied in zip(target.elts, value.value, strict=True):
                self._assign(item, supplied, values)
            return
        if isinstance(target, ast.Subscript) and isinstance(
            target.value,
            ast.Name,
        ):
            owner = subscript_owner
            index = subscript_index
            assert index is not None
            if (
                owner is not None
                and owner.mutable_collection
                and owner.mutable_collection_identity is None
            ):
                self._record_throw_state(values, None, True)
                if _flow_is_sensitive(value):
                    values[target.value.id] = _flow_unknown(
                        "mutable collection alias mutation is dynamically unresolved",
                        sensitive=True,
                    )
                    self.flow.standalone_blockers.append((
                        target,
                        "mutable collection alias mutation is dynamically unresolved",
                    ))
                return
            if (
                owner is not None
                and owner.kind == "sequence"
                and owner.mutable_collection
                and owner.mutable_collection_identity is not None
                and index.kind == "scalar"
                and type(index.value) is int
            ):
                sequence_version = self._mutable_collection_versions.get(
                    owner.mutable_collection_identity,
                    0,
                )
                if sequence_version == 0 and not (
                    -len(owner.value) <= int(index.value) < len(owner.value)
                ):
                    self._record_throw_state(values, "IndexError", True)
                    if self._throw_states is not None:
                        raise _ExpressionDoesNotComplete
                    return
                if sequence_version == 0:
                    items = list(owner.value)
                    items[int(index.value)] = value
                    identity = owner.mutable_collection_identity
                    for name, candidate in tuple(values.items()):
                        if candidate.mutable_collection_identity == identity:
                            values[name] = replace(
                                candidate,
                                value=tuple(items),
                            )
                    self._record_throw_state(values, None, True)
                    self._record_mutable_collection_mutation(owner)
                    return
                self._record_throw_state(values, None, True)
                self._poison_mutable_collection(
                    owner,
                    values,
                    sensitive=_flow_is_sensitive(value),
                    reason="mixed protected receiver is dynamically unresolved",
                )
                return
            if (
                owner is not None
                and owner.mutable_collection
                and owner.mutable_collection_identity is not None
            ):
                if owner.kind == "mapping" and index.kind == "scalar":
                    items = dict(owner.value)
                    items[index.value] = value
                    identity = owner.mutable_collection_identity
                    for name, candidate in tuple(values.items()):
                        if candidate.mutable_collection_identity == identity:
                            values[name] = replace(
                                candidate,
                                value=tuple(items.items()),
                            )
                    self._record_throw_state(values, None, True)
                    self._record_mutable_collection_mutation(owner)
                    return
                if owner.kind == "mapping_keys":
                    items = list(owner.value)
                    for item_index, (stored_key, _stored_value) in enumerate(
                        items
                    ):
                        if stored_key == index:
                            items[item_index] = (stored_key, value)
                            break
                    else:
                        items.append((index, value))
                    identity = owner.mutable_collection_identity
                    for name, candidate in tuple(values.items()):
                        if candidate.mutable_collection_identity == identity:
                            values[name] = replace(
                                candidate,
                                value=tuple(items),
                            )
                    self._record_throw_state(values, None, True)
                    self._record_mutable_collection_mutation(owner)
                    return
                self._record_throw_state(values, None, True)
                self._poison_mutable_collection(
                    owner,
                    values,
                    sensitive=_flow_is_sensitive(value),
                    reason="mixed protected receiver is dynamically unresolved",
                )
                return
        if isinstance(target, ast.Attribute):
            owner = self._evaluate(target.value, values, False)
            if (
                owner.kind == "implicit_class"
                and isinstance(owner.value, _ImplicitClassDescriptor)
                and target.attr in _IMPLICIT_CLASS_METHOD_NAMES
            ):
                self._update_implicit_class_protocol(
                    owner.value,
                    target.attr,
                    value,
                    values,
                )
                return
            if (
                owner.kind == "qname"
                and self._invalidate_protected_path(
                    target,
                    f"{owner.value}.{target.attr}",
                    values,
                )
            ):
                return
            self._record_implicit_protocol_blocker(
                target,
                owner,
                _IMPLICIT_PROTOCOL_METHODS["attribute_store"],
                "implicit attribute-store protocol execution is dynamically unresolved",
            )
        member_path = self._member_path(target, values)
        if member_path is not None:
            root, path = member_path
            current = values.get(root)
            if (
                current is not None
                and current.kind in {
                    "qname",
                    "object",
                    "implicit_class_instance",
                }
                and all(type(item) is str for item in path)
            ):
                for prefix_length in range(len(path) - 1, 0, -1):
                    prefix = ".".join((root, *path[:prefix_length]))
                    if prefix not in values:
                        continue
                    values[prefix] = _flow_store_path(
                        values[prefix],
                        path[prefix_length:],
                        value,
                    )
                    return
                values[".".join((root, *path))] = value
                return
            if (
                _flow_is_sensitive(value)
                and (
                    current is None
                    or current.kind
                    not in {
                        "mapping",
                        "object",
                        "qname",
                        "sequence",
                        "implicit_class_instance",
                    }
                )
            ):
                self.flow.standalone_blockers.append((
                    target,
                    "protected value store target is dynamically unresolved",
                ))
            values[root] = _flow_store_path(current, path, value)
            return
        if (
            isinstance(target, ast.Subscript)
            and isinstance(target.value, ast.Name)
        ):
            name = target.value.id
            owner_value = values.get(name)
            key = self._evaluate(target.slice, values, False)
            if (
                owner_value is not None
                and owner_value.kind == "environment"
                and key.kind == "scalar"
                and type(key.value) is str
                and value.kind == "scalar"
                and type(value.value) is str
            ):
                self._mutate_environment(
                    values,
                    name,
                    additions={key.value: value.value},
                )
            elif owner_value is not None and owner_value.kind == "environment":
                self._poison_environment(
                    values,
                    owner_value.value.owner,
                    "subprocess environment mutation is unresolved",
                )
                return
        if _flow_is_sensitive(value):
            root = self._store_root_name(target)
            if root is not None:
                values[root] = _flow_unknown(
                    "mixed protected receiver is dynamically unresolved",
                    sensitive=True,
                )
                self.flow.standalone_blockers.append((
                    target,
                    "protected value store target is dynamically unresolved",
                ))
            else:
                self.flow.standalone_blockers.append((
                    target,
                    "protected value store target is dynamically unresolved",
                ))

    def _delete_target(
        self,
        target: ast.expr,
        values: dict[str, _FlowValue],
    ) -> None:
        if isinstance(target, (ast.Tuple, ast.List)):
            for item in target.elts:
                self._delete_target(item, values)
            return
        if isinstance(target, ast.Name):
            current = values.get(target.id)
            if current is None or current.kind == "unbound":
                self._record_throw_state(
                    values,
                    self._lookup_error_tag(target.id),
                    True,
                )
                if self._throw_states is not None:
                    raise _ExpressionDoesNotComplete
                return
            if current.kind == "maybe_unbound":
                self._record_throw_state(
                    values,
                    self._lookup_error_tag(target.id),
                    True,
                )
            values[target.id] = _FlowValue(
                "unbound",
                reason="name was deleted",
            )
            return
        if isinstance(target, ast.Subscript):
            mutable_owner = (
                values.get(target.value.id)
                if isinstance(target.value, ast.Name)
                else None
            )
            supplied_owner = self._evaluate(target.value, values)
            self._record_implicit_protocol_blocker(
                target,
                supplied_owner,
                _IMPLICIT_PROTOCOL_METHODS["item_delete"],
                "implicit item-delete protocol execution is dynamically unresolved",
            )
            key = self._evaluate(target.slice, values)
            self._record_throw_state(values, None, True)
            if (
                mutable_owner is not None
                and mutable_owner.mutable_collection
                and mutable_owner.mutable_collection_identity is not None
            ):
                self._poison_mutable_collection(
                    mutable_owner,
                    values,
                    sensitive=False,
                    reason="mixed protected receiver is dynamically unresolved",
                )
            if isinstance(target.value, ast.Name):
                owner_value = values.get(target.value.id)
                if (
                    owner_value is not None
                    and owner_value.kind == "environment"
                    and key.kind == "scalar"
                    and type(key.value) is str
                ):
                    self._mutate_environment(
                        values,
                        target.value.id,
                        removals=(key.value,),
                    )
            return
        if isinstance(target, ast.Attribute):
            supplied_owner = self._evaluate(target.value, values)
            if (
                supplied_owner.kind == "implicit_class"
                and isinstance(
                    supplied_owner.value,
                    _ImplicitClassDescriptor,
                )
                and target.attr in supplied_owner.value.local_overrides
            ):
                self._record_throw_state(values, None, True)
                self._delete_implicit_class_member(
                    supplied_owner.value,
                    target.attr,
                    values,
                )
                return
            if (
                supplied_owner.kind == "qname"
                and self._invalidate_protected_path(
                    target,
                    f"{supplied_owner.value}.{target.attr}",
                    values,
                )
            ):
                self._record_throw_state(values, None, True)
                return
            self._record_implicit_protocol_blocker(
                target,
                supplied_owner,
                _IMPLICIT_PROTOCOL_METHODS["attribute_delete"],
                "implicit attribute-delete protocol execution is dynamically unresolved",
            )
            self._record_throw_state(values, None, True)
            return
        self._evaluate(target, values)

    @staticmethod
    def _store_root_name(target: ast.expr) -> str | None:
        current = target
        while isinstance(current, (ast.Attribute, ast.Subscript)):
            current = current.value
        return current.id if isinstance(current, ast.Name) else None

    def _member_path(
        self,
        target: ast.expr,
        values: dict[str, _FlowValue],
    ) -> tuple[str, tuple[object, ...]] | None:
        if isinstance(target, ast.Attribute):
            parent = self._member_path(target.value, values)
            if parent is not None:
                return parent[0], (*parent[1], target.attr)
            if isinstance(target.value, ast.Name):
                return target.value.id, (target.attr,)
            return None
        if isinstance(target, ast.Subscript):
            parent = self._member_path(target.value, values)
            if parent is None and isinstance(target.value, ast.Name):
                parent = (target.value.id, ())
            if parent is None:
                return None
            root_value = values.get(parent[0])
            if root_value is not None and root_value.kind == "environment":
                return None
            key = self._evaluate(target.slice, values, False)
            if key.kind != "scalar" or type(key.value) not in {str, int}:
                if root_value is not None and _flow_is_sensitive(root_value):
                    values[parent[0]] = _flow_unknown(
                        "mixed protected receiver is dynamically unresolved",
                        sensitive=True,
                    )
                return None
            return parent[0], (*parent[1], key.value)
        return None

    def _merge_states(
        self,
        states: Sequence[Mapping[str, _FlowValue]],
    ) -> dict[str, _FlowValue]:
        names = set().union(*(state.keys() for state in states))
        return {
            name: _merge_flow_values(
                name,
                tuple(state.get(name) for state in states),
            )
            for name in names
        }

    def _capture_auxiliary_state(self) -> tuple[
        dict[str, _FlowValue],
        dict[
            str,
            tuple[
                ast.FunctionDef,
                tuple[tuple[str, _FlowValue], ...],
            ],
        ],
        dict[str, _DeferredLocalGeneratorFactory],
    ]:
        return (
            dict(self.helper_returns),
            dict(self._local_function_definitions),
            dict(self._deferred_local_generator_definitions),
        )

    def _restore_auxiliary_state(
        self,
        state: tuple[
            dict[str, _FlowValue],
            dict[
                str,
                tuple[
                    ast.FunctionDef,
                    tuple[tuple[str, _FlowValue], ...],
                ],
            ],
            dict[str, _DeferredLocalGeneratorFactory],
        ],
    ) -> None:
        helper_returns, local_definitions, generator_definitions = state
        self.helper_returns = dict(helper_returns)
        self._local_function_definitions = dict(local_definitions)
        self._deferred_local_generator_definitions = dict(
            generator_definitions
        )

    def _merge_auxiliary_states(
        self,
        states: Sequence[
            tuple[
                dict[str, _FlowValue],
                dict[
                    str,
                    tuple[
                        ast.FunctionDef,
                        tuple[tuple[str, _FlowValue], ...],
                    ],
                ],
                dict[str, _DeferredLocalGeneratorFactory],
            ]
        ],
    ) -> None:
        if not states:
            return
        helper_names = set().union(*(state[0].keys() for state in states))
        helper_returns = {
            name: _merge_flow_values(
                f"helper return {name}",
                tuple(state[0].get(name) for state in states),
            )
            for name in helper_names
        }

        local_names = set().union(*(state[1].keys() for state in states))
        local_definitions: dict[
            str,
            tuple[
                ast.FunctionDef,
                tuple[tuple[str, _FlowValue], ...],
            ],
        ] = {}
        for name in local_names:
            present = tuple(
                state[1][name] for state in states if name in state[1]
            )
            definition = present[0][0]
            binding_names = tuple(dict.fromkeys(
                binding_name
                for _definition, bindings in present
                for binding_name, _value in bindings
            ))
            binding_maps = tuple(dict(bindings) for _definition, bindings in present)
            local_definitions[name] = (
                definition,
                tuple(
                    (
                        binding_name,
                        _merge_flow_values(
                            f"local default {name}.{binding_name}",
                            tuple(
                                bindings.get(binding_name)
                                for bindings in binding_maps
                            ),
                        ),
                    )
                    for binding_name in binding_names
                ),
            )

        generator_names = set().union(
            *(state[2].keys() for state in states)
        )
        generator_definitions: dict[
            str,
            _DeferredLocalGeneratorFactory,
        ] = {}
        for name in generator_names:
            present = tuple(
                state[2][name] for state in states if name in state[2]
            )
            factory = present[0]
            default_names = tuple(dict.fromkeys(
                default_name
                for candidate in present
                for default_name, _value in candidate.defaults
            ))
            default_maps = tuple(dict(candidate.defaults) for candidate in present)
            generator_definitions[name] = replace(
                factory,
                defaults=tuple(
                    (
                        default_name,
                        _merge_flow_values(
                            f"generator default {name}.{default_name}",
                            tuple(
                                defaults.get(default_name)
                                for defaults in default_maps
                            ),
                        ),
                    )
                    for default_name in default_names
                ),
            )
        self._restore_auxiliary_state((
            helper_returns,
            local_definitions,
            generator_definitions,
        ))

    def _bind_match_pattern(
        self,
        pattern: ast.pattern,
        subject: _FlowValue,
        values: dict[str, _FlowValue],
    ) -> None:
        if isinstance(pattern, ast.MatchAs) and pattern.pattern is None:
            if pattern.name is not None:
                values[pattern.name] = subject
            return
        names = _python_bound_names(pattern)
        if _flow_is_sensitive(subject):
            ambiguous = _flow_unknown(
                "protected match pattern is unsupported",
                sensitive=True,
            )
            for name in names:
                values[name] = ambiguous
            return
        for name in names:
            values[name] = _flow_unknown(
                "match capture is dynamically unresolved"
            )

    def _expression_may_raise(self, node: ast.AST | None) -> bool:
        if node is None:
            return False
        pending = [node]
        while pending:
            candidate = pending.pop()
            self.budget.consume()
            if isinstance(candidate, (ast.Call, ast.Await, ast.Yield, ast.YieldFrom)):
                return True
            if isinstance(candidate, (ast.Set, ast.Dict, ast.ListComp, ast.SetComp, ast.DictComp)):
                return True
            if isinstance(
                candidate,
                (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef),
            ) and candidate is not node:
                continue
            pending.extend(ast.iter_child_nodes(candidate))
        return False

    def _coalesce_successors(
        self,
        supplied: _FlowSuccessors,
    ) -> _FlowSuccessors:
        def merged(
            states: list[dict[str, _FlowValue]],
        ) -> list[dict[str, _FlowValue]]:
            return [] if not states else [self._merge_states(states)]

        def merged_raises(
            states: list[_FlowExceptionalState],
        ) -> list[_FlowExceptionalState]:
            grouped: dict[
                tuple[bool, str | None, frozenset[str]],
                list[dict[str, _FlowValue]],
            ] = {}
            for exceptional in states:
                grouped.setdefault(
                    (
                        exceptional.explicit,
                        exceptional.exception_tag,
                        exceptional.excluded_handlers,
                    ),
                    [],
                ).append(exceptional.state)
            return [
                _FlowExceptionalState(
                    self._merge_states(group),
                    exception_tag,
                    explicit,
                    excluded_handlers,
                )
                for (
                    explicit,
                    exception_tag,
                    excluded_handlers,
                ), group in grouped.items()
            ]

        return _FlowSuccessors(
            merged(supplied.normal),
            merged(supplied.breaks),
            merged(supplied.continues),
            merged(supplied.returns),
            merged_raises(supplied.raises),
        )

    @staticmethod
    def _extend_successors(
        target: _FlowSuccessors,
        supplied: _FlowSuccessors,
    ) -> None:
        target.normal.extend(supplied.normal)
        target.breaks.extend(supplied.breaks)
        target.continues.extend(supplied.continues)
        target.returns.extend(supplied.returns)
        target.raises.extend(supplied.raises)

    @staticmethod
    def _delete_handler_alias(
        supplied: _FlowSuccessors,
        name: str,
    ) -> None:
        for states in (
            supplied.normal,
            supplied.breaks,
            supplied.continues,
            supplied.returns,
        ):
            for state in states:
                state.pop(name, None)
        for exceptional in supplied.raises:
            exceptional.state.pop(name, None)

    def _flow_statements(
        self,
        statements: Sequence[ast.stmt],
        values: Mapping[str, _FlowValue],
    ) -> _FlowSuccessors:
        result = _FlowSuccessors([dict(values)], [], [], [], [])
        for statement in statements:
            next_normal: list[dict[str, _FlowValue]] = []
            for current in result.normal:
                supplied = self._flow_statement(statement, current)
                next_normal.extend(supplied.normal)
                result.breaks.extend(supplied.breaks)
                result.continues.extend(supplied.continues)
                result.returns.extend(supplied.returns)
                result.raises.extend(supplied.raises)
            result.normal = next_normal
            result = self._coalesce_successors(result)
            if not result.normal:
                break
        return result

    def _flow_expression_statement(
        self,
        statement: ast.stmt,
        values: dict[str, _FlowValue],
        expressions: Sequence[ast.AST | None],
    ) -> _FlowSuccessors:
        current = dict(values)
        outer = self._throw_states
        raised: list[_FlowExceptionalState] = []
        self._throw_states = raised
        try:
            try:
                current = self._statements((statement,), current)
            except _ExpressionDoesNotComplete:
                return _FlowSuccessors([], [], [], [], raised)
        finally:
            self._throw_states = outer
        return _FlowSuccessors([current], [], [], [], raised)

    def _flow_statement(
        self,
        statement: ast.stmt,
        values: dict[str, _FlowValue],
    ) -> _FlowSuccessors:
        self.budget.consume()
        if isinstance(statement, ast.Return):
            completed, returned, current, raised = self._evaluate_with_successors(
                statement.value,
                values,
            )
            if completed:
                self.return_values.append(returned)
                if _flow_contains_deferred_generator(
                    returned
                ) and self._deferred_generator_value_is_sensitive(
                    returned,
                    current,
                ):
                    self.flow.standalone_blockers.append((
                        statement,
                        "deferred generator consumption is dynamically unresolved",
                    ))
            return _FlowSuccessors(
                [],
                [],
                [],
                [current] if completed else [],
                raised,
            )
        if isinstance(statement, ast.Raise):
            if statement.exc is None:
                return _FlowSuccessors(
                    [],
                    [],
                    [],
                    [],
                    [
                        _FlowExceptionalState(
                            dict(values),
                            self._active_exception_tag,
                            True,
                        )
                    ],
                )
            completed, exception_value, current, raised = self._evaluate_with_successors(
                statement.exc,
                values,
            )
            if not completed:
                return _FlowSuccessors([], [], [], [], raised)
            cause_completed, _cause_value, current, cause_raised = (
                self._evaluate_with_successors(
                    statement.cause,
                    current,
                )
            )
            raised.extend(cause_raised)
            if not cause_completed:
                return _FlowSuccessors([], [], [], [], raised)
            cause_validation = self._cause_validation(statement.cause, current)
            if cause_validation in {"invalid", "unknown"}:
                raised.append(
                    _FlowExceptionalState(dict(current), "TypeError", True)
                )
            raise_success, raise_error, _raise_unknown = (
                _builtin_exception_constructor_outcome(
                    statement.exc,
                    self.exception_scope,
                )
            )
            if raise_error is not None and raise_success is None:
                raised.append(
                    _FlowExceptionalState(dict(current), raise_error, True)
                )
            elif cause_validation != "invalid":
                exception_expression = statement.exc
                if isinstance(exception_expression, ast.Call):
                    exception_expression = exception_expression.func
                exception_tag = (
                    exception_value.value
                    if exception_value.kind == "exception_instance"
                    and isinstance(exception_value.value, str)
                    else self._exception_name(exception_expression, current)
                )
                exception_tag = exception_tag or raise_success
                raised.append(
                    _FlowExceptionalState(
                        current,
                        exception_tag,
                        True,
                    )
                )
            return _FlowSuccessors(
                [],
                [],
                [],
                [],
                raised,
            )
        if isinstance(statement, ast.Break):
            return _FlowSuccessors([], [dict(values)], [], [], [])
        if isinstance(statement, ast.Continue):
            return _FlowSuccessors([], [], [dict(values)], [], [])
        if isinstance(statement, ast.If):
            completed, test, current, thrown = self._evaluate_with_successors(
                statement.test,
                values,
            )
            result = _FlowSuccessors([], [], [], [], thrown)
            if not completed:
                return self._coalesce_successors(result)
            self._record_implicit_protocol_blocker(
                statement.test,
                test,
                _IMPLICIT_PROTOCOL_METHODS["truth"],
                "implicit truth-value protocol execution is dynamically unresolved",
            )
            if test.kind == "scalar" and type(test.value) is bool:
                branches = (
                    statement.body if test.value else statement.orelse,
                )
            else:
                branches = (statement.body, statement.orelse)
            incoming_auxiliary = self._capture_auxiliary_state()
            branch_auxiliary = []
            for branch in branches:
                self._restore_auxiliary_state(incoming_auxiliary)
                self._extend_successors(
                    result,
                    self._flow_statements(branch, current),
                )
                branch_auxiliary.append(self._capture_auxiliary_state())
            self._merge_auxiliary_states(branch_auxiliary)
            return self._coalesce_successors(result)
        if isinstance(statement, (ast.With, ast.AsyncWith)):
            current = dict(values)
            result = _FlowSuccessors.empty()
            suppress_arguments: list[tuple[ast.expr, ...]] = []
            for item in statement.items:
                completed, supplied, current, thrown = self._evaluate_with_successors(
                    item.context_expr,
                    current,
                )
                suppress_call = (
                    isinstance(item.context_expr, ast.Call)
                    and self._exception_name(
                        item.context_expr.func,
                        current,
                    ) is None
                    and _resolved_qualified_name(
                        item.context_expr.func,
                        _flow_aliases(current),
                    ) == "contextlib.suppress"
                )
                if suppress_call and isinstance(item.context_expr, ast.Call):
                    suppress_arguments.append(tuple(item.context_expr.args))
                    if all(
                        self._expression_is_proven_nonthrowing(argument, current)
                        for argument in item.context_expr.args
                    ):
                        thrown.clear()
                result.raises.extend(thrown)
                if not completed:
                    return self._coalesce_successors(result)
                self._record_implicit_protocol_blocker(
                    item.context_expr,
                    supplied,
                    (
                        frozenset({"__aenter__", "__aexit__"})
                        if isinstance(statement, ast.AsyncWith)
                        else frozenset({"__enter__", "__exit__"})
                    ),
                    "implicit context-manager protocol execution is dynamically unresolved",
                )
                if item.optional_vars is not None:
                    self._assign(item.optional_vars, supplied, current)
            body = self._flow_statements(statement.body, current)
            result.normal.extend(body.normal)
            result.breaks.extend(body.breaks)
            result.continues.extend(body.continues)
            result.returns.extend(body.returns)
            if suppress_arguments:
                for exceptional in body.raises:
                    outcomes = {"nonmatch"}
                    for arguments in reversed(suppress_arguments):
                        advanced = set(outcomes) - {"nonmatch"}
                        if "nonmatch" in outcomes:
                            advanced.update(
                                self._suppress_outcomes(
                                    exceptional,
                                    arguments,
                                    exceptional.state,
                                )
                            )
                        outcomes = advanced
                    if "match" in outcomes:
                        result.normal.append(exceptional.state)
                    if "nonmatch" in outcomes:
                        result.raises.append(exceptional)
                    if "invalid" in outcomes:
                        result.raises.append(
                            _FlowExceptionalState(
                                dict(exceptional.state),
                                "TypeError",
                                True,
                            )
                        )
            else:
                result.raises.extend(body.raises)
            return self._coalesce_successors(result)
        if isinstance(statement, (ast.For, ast.AsyncFor)):
            completed, iterator, current, thrown = self._evaluate_with_successors(
                statement.iter,
                values,
            )
            result = _FlowSuccessors([], [], [], [], thrown)
            if not completed:
                return self._coalesce_successors(result)
            self._record_implicit_protocol_blocker(
                statement.iter,
                iterator,
                (
                    frozenset({"__aiter__", "__anext__"})
                    if isinstance(statement, ast.AsyncFor)
                    else frozenset({"__iter__", "__next__"})
                ),
                "implicit iterator protocol execution is dynamically unresolved",
            )
            self._record_deferred_generator_consumption(
                iterator,
                current,
                statement.iter,
            )
            bound = self._iteration_bound_value(iterator)
            self.flow.iterator_bounds[id(statement.iter)] = bound
            setattr(statement.iter, "_pontius_iteration_bound", bound)
            completed: list[dict[str, _FlowValue]] = []
            if bound != 0:
                entered = dict(current)
                if iterator.kind == "sequence" and iterator.value:
                    iteration_value = _merge_flow_values(
                        "loop target",
                        tuple(iterator.value),
                    )
                else:
                    iteration_value = _flow_unknown(
                        "loop target is dynamically unresolved",
                        sensitive=_flow_is_sensitive(iterator),
                    )
                self._assign(statement.target, iteration_value, entered)
                body = self._flow_statements(statement.body, entered)
                result.normal.extend(body.breaks)
                completed.extend(body.normal)
                completed.extend(body.continues)
                result.returns.extend(body.returns)
                result.raises.extend(body.raises)
            if bound in {0, None}:
                completed.append(dict(current))
            for state in completed:
                self._extend_successors(
                    result,
                    self._flow_statements(statement.orelse, state),
                )
            return self._coalesce_successors(result)
        if isinstance(statement, ast.While):
            completed, test, current, thrown = self._evaluate_with_successors(
                statement.test,
                values,
            )
            result = _FlowSuccessors([], [], [], [], thrown)
            if not completed:
                return self._coalesce_successors(result)
            self._record_implicit_protocol_blocker(
                statement.test,
                test,
                _IMPLICIT_PROTOCOL_METHODS["truth"],
                "implicit truth-value protocol execution is dynamically unresolved",
            )
            truth = bool(test.value) if test.kind == "scalar" else None
            if truth is False:
                setattr(statement, "_pontius_iteration_bound", 0)
                setattr(statement, "_pontius_condition_evaluations", 1)
                self._extend_successors(
                    result,
                    self._flow_statements(statement.orelse, current),
                )
                return self._coalesce_successors(result)
            body = self._flow_statements(statement.body, current)
            result.normal.extend(body.breaks)
            result.returns.extend(body.returns)
            result.raises.extend(body.raises)
            continuing = [*body.normal, *body.continues]
            after_states: list[dict[str, _FlowValue]] = []
            after_truths: list[bool | None] = []
            for state in continuing:
                completed_after, after, after_state, after_throws = (
                    self._evaluate_with_successors(
                        statement.test,
                        state,
                        record=False,
                    )
                )
                result.raises.extend(after_throws)
                if not completed_after:
                    continue
                after_states.append(after_state)
                after_truths.append(
                    bool(after.value) if after.kind == "scalar" else None
                )
            finite = bool(continuing) and all(
                supplied is False for supplied in after_truths
            )
            if not continuing:
                bound = 1
                condition_evaluations = 1
            elif finite:
                bound = 1
                condition_evaluations = 2
            else:
                bound = None
                condition_evaluations = None
            setattr(statement, "_pontius_iteration_bound", bound)
            if condition_evaluations is not None:
                setattr(
                    statement,
                    "_pontius_condition_evaluations",
                    condition_evaluations,
                )
            exhausted = after_states if finite else []
            if truth is None:
                exhausted.append(dict(current))
            if bound is None:
                result.normal.extend(after_states)
            for state in exhausted:
                self._extend_successors(
                    result,
                    self._flow_statements(statement.orelse, state),
                )
            return self._coalesce_successors(result)
        if isinstance(statement, ast.Match):
            completed, subject, current, thrown = self._evaluate_with_successors(
                statement.subject,
                values,
            )
            result = _FlowSuccessors([], [], [], [], thrown)
            if not completed:
                return self._coalesce_successors(result)
            residual = [dict(current)]
            for case in statement.cases:
                next_residual: list[dict[str, _FlowValue]] = []
                for incoming in residual:
                    case_state = dict(incoming)
                    self._bind_match_pattern(
                        case.pattern,
                        subject,
                        case_state,
                    )
                    completed, guard, case_state, guard_throws = (
                        self._evaluate_with_successors(
                            case.guard,
                            case_state,
                        )
                    )
                    result.raises.extend(guard_throws)
                    if not completed:
                        if not _pattern_is_irrefutable(case.pattern):
                            next_residual.append(incoming)
                        continue
                    if case.guard is not None:
                        self._record_implicit_protocol_blocker(
                            case.guard,
                            guard,
                            _IMPLICIT_PROTOCOL_METHODS["truth"],
                            "implicit truth-value protocol execution is dynamically unresolved",
                        )
                    guard_true = guard.kind == "scalar" and guard.value is True
                    guard_false = guard.kind == "scalar" and guard.value is False
                    if not guard_false:
                        self._extend_successors(
                            result,
                            self._flow_statements(case.body, case_state),
                        )
                    if case.guard is not None and not guard_true:
                        next_residual.append(case_state)
                    if not _pattern_is_irrefutable(case.pattern):
                        next_residual.append(incoming)
                residual = next_residual
                if not residual:
                    break
            result.normal.extend(residual)
            return self._coalesce_successors(result)
        try_types = (ast.Try,)
        if hasattr(ast, "TryStar"):
            try_types = (*try_types, ast.TryStar)
        if isinstance(statement, try_types):
            if (
                hasattr(ast, "TryStar")
                and isinstance(statement, ast.TryStar)
                and id(statement) not in self._try_star_blocked_nodes
            ):
                self._try_star_blocked_nodes.add(id(statement))
                self.flow.standalone_blockers.append((
                    statement,
                    "exception-group handler flow is dynamically unresolved",
                ))
            body = self._flow_statements(statement.body, values)
            result = _FlowSuccessors.empty()
            for state in body.normal:
                self._extend_successors(
                    result,
                    self._flow_statements(statement.orelse, state),
                )
            result.breaks.extend(body.breaks)
            result.continues.extend(body.continues)
            result.returns.extend(body.returns)
            if body.raises and statement.handlers:
                for exceptional in body.raises:
                    residual: _FlowExceptionalState | None = exceptional
                    for handler in statement.handlers:
                        initial_handler_state = self._exceptional_environment_state(
                            dict(residual.state)
                        )
                        completed, _handler_value, handler_state, handler_throws = (
                            self._evaluate_with_successors(
                                handler.type,
                                initial_handler_state,
                            )
                        )
                        result.raises.extend(handler_throws)
                        if not completed:
                            residual = None
                            break
                        validation = self._handler_validation(
                            handler.type,
                            handler_state,
                        )
                        match = (
                            self._handler_match(
                                residual.exception_tag,
                                handler.type,
                                handler_state,
                            )
                            if residual.explicit
                            else self._implicit_handler_match(
                                residual,
                                handler.type,
                                handler_state,
                            )
                        )
                        if not self._expression_is_proven_nonthrowing(
                            handler.type,
                            residual.state,
                        ) and not handler_throws:
                            result.raises.append(
                                _FlowExceptionalState(
                                    dict(handler_state),
                                    None,
                                    True,
                                )
                            )
                        if validation in {"invalid", "unknown"}:
                            result.raises.append(
                                _FlowExceptionalState(
                                    dict(handler_state),
                                    "TypeError",
                                    True,
                                )
                            )
                        if validation == "invalid":
                            residual = None
                            break
                        if match != "nonmatch":
                            if handler.name is not None:
                                handler_state[handler.name] = _FlowValue(
                                    "exception_instance",
                                    residual.exception_tag,
                                )
                            previous_active = self._active_exception_tag
                            self._active_exception_tag = residual.exception_tag
                            try:
                                handler_flow = self._flow_statements(
                                    handler.body,
                                    handler_state,
                                )
                            finally:
                                self._active_exception_tag = previous_active
                            if handler.name is not None:
                                self._delete_handler_alias(
                                    handler_flow,
                                    handler.name,
                                )
                            self._extend_successors(result, handler_flow)
                        if match == "match":
                            residual = None
                            break
                        if not residual.explicit and match == "unknown":
                            residual = _FlowExceptionalState(
                                residual.state,
                                residual.exception_tag,
                                False,
                                residual.excluded_handlers
                                | self._handler_exception_names(
                                    handler.type,
                                    handler_state,
                                ),
                            )
                    if residual is not None:
                        result.raises.append(residual)
            else:
                result.raises.extend(body.raises)
            if statement.finalbody:
                result = self._flow_finally(result, statement.finalbody)
            return self._coalesce_successors(result)
        expressions: Sequence[ast.AST | None]
        if isinstance(statement, ast.Assign):
            expressions = (statement.value,)
        elif isinstance(statement, ast.AnnAssign):
            expressions = (statement.value,)
        elif isinstance(statement, ast.AugAssign):
            expressions = (statement.target, statement.value)
        elif isinstance(statement, ast.Expr):
            expressions = (statement.value,)
        elif isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
            expressions = (
                *statement.decorator_list,
                *statement.args.defaults,
                *statement.args.kw_defaults,
            )
        elif isinstance(statement, ast.ClassDef):
            expressions = (
                *statement.decorator_list,
                *statement.bases,
                *(keyword.value for keyword in statement.keywords),
            )
        else:
            expressions = tuple(ast.iter_child_nodes(statement))
        return self._flow_expression_statement(statement, values, expressions)

    def _flow_finally(
        self,
        incoming: _FlowSuccessors,
        statements: Sequence[ast.stmt],
    ) -> _FlowSuccessors:
        result = _FlowSuccessors.empty()
        for kind in ("normal", "breaks", "continues", "returns", "raises"):
            for incoming_state in getattr(incoming, kind):
                incoming_exception = (
                    incoming_state if kind == "raises" else None
                )
                state = (
                    incoming_exception.state
                    if incoming_exception is not None
                    else incoming_state
                )
                final = self._flow_statements(statements, state)
                if kind == "normal":
                    result.normal.extend(final.normal)
                elif incoming_exception is not None:
                    result.raises.extend(
                        _FlowExceptionalState(
                            normal_state,
                            incoming_exception.exception_tag,
                            incoming_exception.explicit,
                            incoming_exception.excluded_handlers,
                        )
                        for normal_state in final.normal
                    )
                else:
                    getattr(result, kind).extend(final.normal)
                result.breaks.extend(final.breaks)
                result.continues.extend(final.continues)
                result.returns.extend(final.returns)
                result.raises.extend(final.raises)
        return self._coalesce_successors(result)

    def _try_body_states(
        self,
        statements: Sequence[ast.stmt],
        values: dict[str, _FlowValue],
    ) -> tuple[
        dict[str, _FlowValue] | None,
        dict[str, _FlowValue] | None,
    ]:
        normal_states: list[dict[str, _FlowValue]] = [dict(values)]
        exceptional_states: list[dict[str, _FlowValue]] = []
        for statement in statements:
            next_normal: list[dict[str, _FlowValue]] = []
            for current in normal_states:
                normal, exceptional = self._try_statement_states(
                    statement,
                    current,
                )
                next_normal.extend(normal)
                exceptional_states.extend(exceptional)
            normal_states = next_normal
            if not normal_states:
                break
        normal = (
            self._merge_states(normal_states) if normal_states else None
        )
        exceptional = (
            self._merge_states(exceptional_states)
            if exceptional_states
            else None
        )
        return normal, exceptional

    def _try_statement_states(
        self,
        statement: ast.stmt,
        values: dict[str, _FlowValue],
    ) -> tuple[
        list[dict[str, _FlowValue]],
        list[dict[str, _FlowValue]],
    ]:
        if isinstance(statement, ast.Raise):
            self._evaluate(statement.exc, values)
            self._evaluate(statement.cause, values)
            return [], [dict(values)]
        if isinstance(statement, ast.If):
            test = self._evaluate(statement.test, values)
            branches: tuple[Sequence[ast.stmt], ...]
            if test.kind == "scalar" and type(test.value) is bool:
                branches = (
                    statement.body if test.value else statement.orelse,
                )
            else:
                branches = (statement.body, statement.orelse)
            normal: list[dict[str, _FlowValue]] = []
            exceptional: list[dict[str, _FlowValue]] = []
            for branch in branches:
                branch_normal, branch_exceptional = self._try_body_states(
                    branch,
                    dict(values),
                )
                if branch_normal is not None:
                    normal.append(branch_normal)
                if branch_exceptional is not None:
                    exceptional.append(branch_exceptional)
            return normal, exceptional
        if isinstance(statement, (ast.With, ast.AsyncWith)):
            current = dict(values)
            for item in statement.items:
                supplied = self._evaluate(item.context_expr, current)
                if item.optional_vars is not None:
                    self._assign(item.optional_vars, supplied, current)
            normal, exceptional = self._try_body_states(
                statement.body,
                current,
            )
            return (
                [] if normal is None else [normal],
                [] if exceptional is None else [exceptional],
            )
        if isinstance(statement, (ast.For, ast.AsyncFor)):
            current = dict(values)
            iterator = self._evaluate(statement.iter, current)
            bound = self._iteration_bound_value(iterator)
            normal: list[dict[str, _FlowValue]] = []
            exceptional: list[dict[str, _FlowValue]] = []
            if bound != 0:
                entered = dict(current)
                if iterator.kind == "sequence" and iterator.value:
                    iteration_value = _merge_flow_values(
                        "loop target",
                        tuple(iterator.value),
                    )
                else:
                    iteration_value = _flow_unknown(
                        "loop target is dynamically unresolved",
                        sensitive=_flow_is_sensitive(iterator),
                    )
                self._assign(statement.target, iteration_value, entered)
                body, raised = self._try_body_states(
                    statement.body,
                    entered,
                )
                if body is not None:
                    normal.append(body)
                if raised is not None:
                    exceptional.append(raised)
            if bound in {0, None}:
                normal.append(current)
            completed: list[dict[str, _FlowValue]] = []
            for state in normal:
                else_normal, else_raised = self._try_body_states(
                    statement.orelse,
                    state,
                )
                if else_normal is not None:
                    completed.append(else_normal)
                if else_raised is not None:
                    exceptional.append(else_raised)
            return completed, exceptional
        if isinstance(statement, ast.While):
            current = dict(values)
            test = self._evaluate(statement.test, current)
            truth = bool(test.value) if test.kind == "scalar" else None
            normal: list[dict[str, _FlowValue]] = []
            exceptional: list[dict[str, _FlowValue]] = []
            if truth is not False:
                body, raised = self._try_body_states(
                    statement.body,
                    dict(current),
                )
                if body is not None:
                    normal.append(body)
                if raised is not None:
                    exceptional.append(raised)
            if truth is not True:
                normal.append(current)
            completed: list[dict[str, _FlowValue]] = []
            for state in normal:
                else_normal, else_raised = self._try_body_states(
                    statement.orelse,
                    state,
                )
                if else_normal is not None:
                    completed.append(else_normal)
                if else_raised is not None:
                    exceptional.append(else_raised)
            return completed, exceptional
        if isinstance(statement, ast.Match):
            subject = self._evaluate(statement.subject, values)
            residual = [dict(values)]
            normal: list[dict[str, _FlowValue]] = []
            exceptional: list[dict[str, _FlowValue]] = []
            for case in statement.cases:
                next_residual: list[dict[str, _FlowValue]] = []
                for incoming in residual:
                    case_state = dict(incoming)
                    self._bind_match_pattern(case.pattern, subject, case_state)
                    guard = self._evaluate(case.guard, case_state)
                    guard_true = guard.kind == "scalar" and guard.value is True
                    guard_false = guard.kind == "scalar" and guard.value is False
                    if not guard_false:
                        body, raised = self._try_body_states(
                            case.body,
                            dict(case_state),
                        )
                        if body is not None:
                            normal.append(body)
                        if raised is not None:
                            exceptional.append(raised)
                    if case.guard is not None and not guard_true:
                        next_residual.append(case_state)
                    if not _pattern_is_irrefutable(case.pattern):
                        next_residual.append(incoming)
                residual = next_residual
                if not residual:
                    break
            normal.extend(residual)
            return normal, exceptional
        current = self._statements((statement,), dict(values))
        exceptional = (
            [dict(current)]
            if any(
                isinstance(candidate, (ast.Call, ast.Await))
                for candidate in _metered_ast_walk(statement, self.budget)
            )
            else []
        )
        return [current], exceptional

    @staticmethod
    def _exceptional_environment_state(
        values: dict[str, _FlowValue],
    ) -> dict[str, _FlowValue]:
        result = dict(values)
        for name, value in tuple(result.items()):
            if value.kind != "environment":
                continue
            environment = value.value
            if not isinstance(environment, _FlowEnvironment):
                continue
            if environment.poison is None:
                continue
            reason = "subprocess environment exceptional state is ambiguous"
            result[name] = _FlowValue(
                "environment",
                _FlowEnvironment(
                    environment.owner,
                    environment.additions,
                    environment.removals,
                    reason,
                ),
                reason=reason,
            )
        return result

    def _statements(
        self,
        statements: Sequence[ast.stmt],
        values: dict[str, _FlowValue],
    ) -> dict[str, _FlowValue]:
        for statement in statements:
            self.budget.consume()
            if isinstance(statement, ast.Import):
                for imported in statement.names:
                    local = imported.asname or imported.name.split(".", 1)[0]
                    qualified = imported.name if imported.asname else local
                    values[local] = _flow_qname(qualified)
                continue
            if isinstance(statement, ast.ImportFrom) and statement.module:
                for imported in statement.names:
                    local = imported.asname or imported.name
                    values[local] = _flow_qname(
                        f"{statement.module}.{imported.name}"
                    )
                continue
            if isinstance(statement, ast.Assign):
                value = self._evaluate(statement.value, values)
                for target in statement.targets:
                    self._assign(target, value, values)
                continue
            if isinstance(statement, ast.AnnAssign):
                if statement.value is not None:
                    value = self._evaluate(statement.value, values)
                    self._assign(statement.target, value, values)
                elif (
                    isinstance(statement.target, ast.Name)
                    and statement.target.id not in values
                ):
                    values[statement.target.id] = _FlowValue(
                        "unbound",
                        None,
                        reason="annotation does not bind a runtime value",
                    )
                continue
            if isinstance(statement, ast.AugAssign):
                previous = self._evaluate(statement.target, values, False)
                supplied = self._evaluate(statement.value, values)
                protected_owner = self._protected_namespace_mapping_owner(
                    previous
                )
                if (
                    protected_owner is not None
                    and isinstance(statement.op, ast.BitOr)
                ):
                    self._invalidate_protected_namespace_mapping(
                        statement,
                        protected_owner,
                        self._known_mapping_string_keys(supplied),
                        values,
                    )
                    self._record_throw_state(values, None, True)
                    self._assign(statement.target, previous, values)
                    continue
                direct, reflected, inplace = _binary_protocol_methods(
                    statement.op
                )
                self._record_implicit_protocol_blocker(
                    statement,
                    previous,
                    inplace,
                    "implicit augmented binary protocol execution is dynamically unresolved",
                )
                self._record_implicit_protocol_blocker(
                    statement,
                    supplied,
                    reflected,
                    "implicit augmented binary protocol execution is dynamically unresolved",
                )
                if (
                    previous.mutable_collection
                    and previous.mutable_collection_identity is not None
                    and isinstance(statement.op, (ast.Add, ast.BitOr, ast.Mult))
                ):
                    self._record_throw_state(values, None, True)
                    self._poison_mutable_collection(
                        previous,
                        values,
                        sensitive=_flow_is_sensitive(supplied),
                        reason="mixed protected receiver is dynamically unresolved",
                    )
                    continue
                self._assign(
                    statement.target,
                    _flow_unknown(
                        "augmented assignment is dynamically unresolved",
                        sensitive=_flow_is_sensitive(previous),
                    ),
                    values,
                )
                continue
            if isinstance(statement, ast.Delete):
                for target in statement.targets:
                    self._delete_target(target, values)
                continue
            if isinstance(statement, ast.Expr):
                self._evaluate(statement.value, values)
                continue
            if isinstance(statement, ast.Return):
                self.return_values.append(
                    self._evaluate(statement.value, values)
                )
                return values
            if isinstance(statement, ast.Raise):
                self._evaluate(statement.exc, values)
                self._evaluate(statement.cause, values)
                return values
            if isinstance(statement, (ast.Break, ast.Continue)):
                return values
            if isinstance(statement, ast.If):
                test = self._evaluate(statement.test, values)
                self._record_implicit_protocol_blocker(
                    statement.test,
                    test,
                    _IMPLICIT_PROTOCOL_METHODS["truth"],
                    "implicit truth-value protocol execution is dynamically unresolved",
                )
                if test.kind == "scalar" and type(test.value) is bool:
                    chosen = statement.body if test.value else statement.orelse
                    chosen_state = self._statements(chosen, dict(values))
                    values.clear()
                    values.update(chosen_state)
                    continue
                incoming_auxiliary = self._capture_auxiliary_state()
                first = self._statements(statement.body, dict(values))
                first_auxiliary = self._capture_auxiliary_state()
                self._restore_auxiliary_state(incoming_auxiliary)
                second = self._statements(statement.orelse, dict(values))
                second_auxiliary = self._capture_auxiliary_state()
                self._merge_auxiliary_states((
                    first_auxiliary,
                    second_auxiliary,
                ))
                values.clear()
                values.update(self._merge_states((first, second)))
                continue
            if isinstance(statement, (ast.For, ast.AsyncFor)):
                iterator = self._evaluate(statement.iter, values)
                self._record_implicit_protocol_blocker(
                    statement.iter,
                    iterator,
                    (
                        _IMPLICIT_PROTOCOL_METHODS["async_iteration"]
                        if isinstance(statement, ast.AsyncFor)
                        else _IMPLICIT_PROTOCOL_METHODS["iteration"]
                    ),
                    "implicit iterator protocol execution is dynamically unresolved",
                )
                bound = self._iteration_bound_value(iterator)
                self.flow.iterator_bounds[id(statement.iter)] = bound
                setattr(statement.iter, "_pontius_iteration_bound", bound)
                body_state = dict(values)
                if iterator.kind == "sequence" and iterator.value:
                    iteration_value = _merge_flow_values(
                        "loop target",
                        tuple(iterator.value),
                    )
                else:
                    iteration_value = _flow_unknown(
                        "loop target is dynamically unresolved",
                        sensitive=_flow_is_sensitive(iterator),
                    )
                self._assign(statement.target, iteration_value, body_state)
                body_state = self._statements(statement.body, body_state)
                if bound == 0:
                    merged = dict(values)
                elif bound is not None:
                    merged = body_state
                else:
                    merged = self._merge_states((values, body_state))
                merged = self._statements(statement.orelse, merged)
                values.clear()
                values.update(merged)
                continue
            if isinstance(statement, ast.While):
                test = self._evaluate(statement.test, values)
                self._record_implicit_protocol_blocker(
                    statement.test,
                    test,
                    _IMPLICIT_PROTOCOL_METHODS["truth"],
                    "implicit truth-value protocol execution is dynamically unresolved",
                )
                test_truth = (
                    bool(test.value) if test.kind == "scalar" else None
                )
                if test_truth is False:
                    setattr(statement, "_pontius_iteration_bound", 0)
                    setattr(statement, "_pontius_condition_evaluations", 1)
                    merged = dict(values)
                else:
                    control = _outer_loop_control_outcomes(statement.body)
                    body = self._statements(statement.body, dict(values))
                    after = self._evaluate(
                        statement.test,
                        dict(body),
                        False,
                    )
                    after_truth = (
                        bool(after.value) if after.kind == "scalar" else None
                    )
                    if "continue" in control:
                        bound = None
                    elif "fallthrough" not in control:
                        bound = 1
                    elif test_truth is True and after_truth is False:
                        bound = 1
                    else:
                        bound = None
                    setattr(statement, "_pontius_iteration_bound", bound)
                    if bound == 1:
                        condition_evaluations = (
                            2 if "fallthrough" in control else 1
                        )
                        setattr(
                            statement,
                            "_pontius_condition_evaluations",
                            condition_evaluations,
                        )
                    merged = body if bound == 1 else self._merge_states((values, body))
                merged = self._statements(statement.orelse, merged)
                values.clear()
                values.update(merged)
                continue
            if isinstance(statement, (ast.With, ast.AsyncWith)):
                for item in statement.items:
                    supplied = self._evaluate(item.context_expr, values)
                    self._record_implicit_protocol_blocker(
                        item.context_expr,
                        supplied,
                        (
                            _IMPLICIT_PROTOCOL_METHODS["async_context"]
                            if isinstance(statement, ast.AsyncWith)
                            else _IMPLICIT_PROTOCOL_METHODS["context"]
                        ),
                        "implicit context-manager protocol execution is dynamically unresolved",
                    )
                    if item.optional_vars is not None:
                        self._assign(item.optional_vars, supplied, values)
                self._statements(statement.body, values)
                continue
            try_types = (ast.Try,)
            if hasattr(ast, "TryStar"):
                try_types = (*try_types, ast.TryStar)
            if isinstance(statement, try_types):
                body, raised = self._try_body_states(
                    statement.body,
                    dict(values),
                )
                alternatives: list[dict[str, _FlowValue]] = []
                if body is not None:
                    alternatives.append(
                        self._statements(statement.orelse, dict(body))
                    )
                if raised is not None:
                    for handler in statement.handlers:
                        handler_state = self._exceptional_environment_state(
                            dict(raised)
                        )
                        self._evaluate(handler.type, handler_state)
                        alternatives.append(
                            self._statements(handler.body, handler_state)
                        )
                if not alternatives:
                    if raised is None:
                        raise RuntimeError(
                            "try analysis produced no successor state"
                        )
                    alternatives.append(dict(raised))
                merged = self._merge_states(alternatives)
                merged = self._statements(statement.finalbody, merged)
                values.clear()
                values.update(merged)
                continue
            if isinstance(statement, ast.Match):
                subject = self._evaluate(statement.subject, values)
                alternatives: list[dict[str, _FlowValue]] = []
                residual_states: list[dict[str, _FlowValue]] = [dict(values)]
                for case in statement.cases:
                    next_residual: list[dict[str, _FlowValue]] = []
                    for residual in residual_states:
                        case_state = dict(residual)
                        self._bind_match_pattern(
                            case.pattern,
                            subject,
                            case_state,
                        )
                        guard = self._evaluate(case.guard, case_state)
                        if case.guard is not None:
                            self._record_implicit_protocol_blocker(
                                case.guard,
                                guard,
                                _IMPLICIT_PROTOCOL_METHODS["truth"],
                                "implicit truth-value protocol execution is dynamically unresolved",
                            )
                        guard_true = (
                            guard.kind == "scalar" and guard.value is True
                        )
                        guard_false = (
                            guard.kind == "scalar" and guard.value is False
                        )
                        if not guard_false:
                            alternatives.append(
                                self._statements(case.body, dict(case_state))
                            )
                        if case.guard is not None and not guard_true:
                            next_residual.append(case_state)
                        if not _pattern_is_irrefutable(case.pattern):
                            next_residual.append(dict(residual))
                    residual_states = next_residual
                    if not residual_states:
                        break
                alternatives.extend(residual_states)
                if alternatives:
                    values.clear()
                    values.update(self._merge_states(alternatives))
                continue
            if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
                definition_marker = _definition_point_marker(statement)
                supplied_return = self.helper_returns.get(
                    definition_marker,
                    self.helper_returns.get(statement.name),
                )
                if supplied_return is not None:
                    self.helper_returns.setdefault(
                        definition_marker,
                        supplied_return,
                    )
                decorator_values = [
                    self._evaluate(expression, values)
                    for expression in statement.decorator_list
                ]
                positional_names = tuple(
                    argument.arg
                    for argument in (
                        *statement.args.posonlyargs,
                        *statement.args.args,
                    )
                )
                positional_default_names = positional_names[
                    len(positional_names) - len(statement.args.defaults):
                ]
                captured_defaults: list[tuple[str, _FlowValue]] = []
                for name, expression in zip(
                    positional_default_names,
                    statement.args.defaults,
                    strict=True,
                ):
                    captured_defaults.append((
                        name,
                        self._evaluate(expression, values),
                    ))
                for argument, expression in zip(
                    statement.args.kwonlyargs,
                    statement.args.kw_defaults,
                    strict=True,
                ):
                    if expression is not None:
                        captured_defaults.append((
                            argument.arg,
                            self._evaluate(expression, values),
                        ))
                generator_shape = (
                    _bounded_local_generator_dependencies(
                        statement,
                        self.budget,
                    )
                    if isinstance(statement, ast.FunctionDef)
                    else None
                )
                generator_factory = (
                    _DeferredLocalGeneratorFactory(
                        definition_marker,
                        statement,
                        tuple(captured_defaults),
                    )
                    if isinstance(statement, ast.FunctionDef)
                    and generator_shape is not None
                    else None
                )
                if generator_factory is not None:
                    self._deferred_local_generator_definitions[
                        definition_marker
                    ] = generator_factory
                elif isinstance(statement, ast.FunctionDef):
                    self._local_function_definitions[definition_marker] = (
                        statement,
                        tuple(captured_defaults),
                    )
                summary = _bounded_callable_summary(
                    statement,
                    _exception_name_scope(
                        statement,
                        self.exception_scope.shadowed_names,
                        self.exception_scope.enclosing_names,
                    ),
                )
                installed = (
                    _FlowValue(
                        "deferred_local_generator_factory",
                        generator_factory,
                    )
                    if generator_factory is not None
                    else _FlowValue(
                        "callable_summary" if summary is not None else "qname",
                        (
                            (definition_marker, summary)
                            if summary is not None
                            else definition_marker
                        ),
                        (
                            definition_marker in self.sensitive_definition_markers
                            or _contains_sensitive_runtime(statement, self.budget)
                        ),
                    )
                )
                for decorator_value in reversed(decorator_values):
                    decorator_name: str | None = None
                    decorator_summary: _BoundedCallableSummary | None = None
                    if decorator_value.kind == "qname":
                        decorator_name = str(decorator_value.value)
                        resolved_decorator = values.get(decorator_name)
                        if (
                            resolved_decorator is not None
                            and resolved_decorator.kind == "callable_summary"
                            and isinstance(resolved_decorator.value, tuple)
                            and len(resolved_decorator.value) == 2
                            and isinstance(
                                resolved_decorator.value[1],
                                _BoundedCallableSummary,
                            )
                        ):
                            decorator_summary = resolved_decorator.value[1]
                    elif decorator_value.kind == "callable_summary":
                        supplied = decorator_value.value
                        if (
                            isinstance(supplied, tuple)
                            and len(supplied) == 2
                            and isinstance(
                                supplied[1],
                                _BoundedCallableSummary,
                            )
                        ):
                            decorator_name = str(supplied[0])
                            decorator_summary = supplied[1]
                    if decorator_summary is not None:
                        synthetic = ast.Call(
                            func=ast.Name(id=decorator_name or "decorator"),
                            args=[ast.Name(id=statement.name)],
                            keywords=[],
                        )
                        application_shape = _bounded_call_shape(
                            synthetic,
                            decorator_summary,
                        )
                        if application_shape == "invalid":
                            self._record_throw_state(values, "TypeError", True)
                            if self._throw_states is not None:
                                raise _ExpressionDoesNotComplete
                        if (
                            application_shape == "valid"
                            and decorator_summary.exception_tag is not None
                        ):
                            self._record_throw_state(
                                values,
                                decorator_summary.exception_tag,
                                True,
                            )
                            if self._throw_states is not None:
                                raise _ExpressionDoesNotComplete
                    returned = self.helper_returns.get(decorator_name or "")
                    if returned is None:
                        installed = _flow_unknown(
                            "decorated callable identity is dynamically unresolved"
                        )
                    else:
                        installed = returned
                values[statement.name] = installed
                continue
            if isinstance(statement, ast.ClassDef):
                decorator_values = tuple(
                    (expression, self._evaluate(expression, values))
                    for expression in statement.decorator_list
                )
                base_values = tuple(
                    (expression, self._evaluate(expression, values))
                    for expression in statement.bases
                )
                keyword_values = tuple(
                    (keyword, self._evaluate(keyword.value, values))
                    for keyword in statement.keywords
                )
                for expression, base_value in base_values:
                    if base_value.kind == "implicit_class_instance":
                        self._record_implicit_protocol_blocker(
                            expression,
                            base_value,
                            frozenset({"__mro_entries__"}),
                            "implicit class-base adaptation is dynamically unresolved",
                        )
                    elif base_value.kind == "implicit_class":
                        self._record_implicit_protocol_blocker(
                            expression,
                            base_value,
                            frozenset({"__init_subclass__"}),
                            "implicit subclass initialization is dynamically unresolved",
                        )
                    elif base_value.kind == "implicit_protocol_merged":
                        self._record_implicit_protocol_blocker(
                            expression,
                            base_value,
                            frozenset({"__mro_entries__", "__init_subclass__"}),
                            "implicit merged class ancestry is dynamically unresolved",
                        )
                        if (
                            _flow_is_sensitive(base_value)
                            and not self._implicit_protocol_is_sensitive(
                                base_value,
                                frozenset({
                                    "__mro_entries__",
                                    "__init_subclass__",
                                }),
                            )
                        ):
                            self.flow.standalone_blockers.append((
                                expression,
                                "implicit merged class ancestry is dynamically unresolved",
                            ))
                for keyword, keyword_value in keyword_values:
                    if keyword.arg == "metaclass":
                        self._record_implicit_protocol_blocker(
                            keyword.value,
                            keyword_value,
                            frozenset({"__prepare__", "__new__", "__init__"}),
                            "implicit metaclass construction is dynamically unresolved",
                        )
                class_statements = [
                    item
                    for item in statement.body
                    if not isinstance(
                        item,
                        (ast.FunctionDef, ast.AsyncFunctionDef),
                    )
                ]
                class_values = self._statements(
                    class_statements,
                    dict(values),
                )
                for member_name in _class_namespace_assignment_names(
                    class_statements
                ):
                    member_value = class_values.get(member_name)
                    if member_value is not None:
                        self._record_implicit_protocol_blocker(
                            statement,
                            member_value,
                            frozenset({"__set_name__"}),
                            "implicit descriptor installation is dynamically unresolved",
                        )
                methods = tuple(
                    item
                    for item in statement.body
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
                )
                overridden_names = (
                    _class_namespace_assignment_names(class_statements)
                    | frozenset(
                        item.name
                        for item in statement.body
                        if isinstance(
                            item,
                            (
                                ast.FunctionDef,
                                ast.AsyncFunctionDef,
                                ast.ClassDef,
                            ),
                        )
                    )
                )
                descriptor_members = tuple(
                    (member_name, member_value.value)
                    for member_name in _class_namespace_assignment_names(
                        class_statements
                    )
                    for member_value in (class_values.get(member_name),)
                    if member_value is not None
                    and member_value.kind == "implicit_class_instance"
                    and isinstance(
                        member_value.value,
                        _ImplicitClassDescriptor,
                    )
                )
                descriptor = _implicit_class_descriptor(
                    statement.name,
                    methods,
                    _flow_aliases(values),
                    self.module_assignments,
                    self.budget,
                    sensitive_names=frozenset(
                        name
                        for name, value in values.items()
                        if _flow_is_sensitive(value)
                    ),
                    descriptor_members=descriptor_members,
                    inherited_descriptors=tuple(
                        base_value.value
                        for _expression, base_value in base_values
                        if base_value.kind == "implicit_class"
                        and isinstance(
                            base_value.value,
                            _ImplicitClassDescriptor,
                        )
                    ),
                    overridden_names=overridden_names,
                )
                installed = _FlowValue(
                    "implicit_class",
                    descriptor,
                    bool(descriptor.sensitive_methods),
                    "implicit class protocol execution is dynamically unresolved",
                )
                for decorator, decorator_value in reversed(decorator_values):
                    if self._flow_decorator_preserves_identity(decorator_value):
                        continue
                    self.flow.standalone_blockers.append((
                        decorator,
                        "local class decorator runtime target is dynamically unresolved",
                    ))
                    installed = _flow_unknown(
                        "decorated local class identity is dynamically unresolved"
                    )
                    break
                values[statement.name] = installed
                continue
            for child in ast.iter_child_nodes(statement):
                self._evaluate(child, values)
        return values


def _pattern_is_irrefutable(pattern: ast.pattern) -> bool:
    if isinstance(pattern, ast.MatchAs):
        return pattern.pattern is None or _pattern_is_irrefutable(pattern.pattern)
    if isinstance(pattern, ast.MatchOr):
        return any(_pattern_is_irrefutable(item) for item in pattern.patterns)
    return False


def _statements_terminate_without_fallthrough(
    statements: Sequence[ast.stmt],
) -> bool:
    for statement in statements:
        if isinstance(statement, (ast.Return, ast.Raise, ast.Break, ast.Continue)):
            return True
        if isinstance(statement, ast.If) and statement.orelse:
            if _statements_terminate_without_fallthrough(
                statement.body
            ) and _statements_terminate_without_fallthrough(statement.orelse):
                return True
        if isinstance(statement, (ast.With, ast.AsyncWith)):
            control = _outer_loop_control_outcomes(statement.body)
            if "fallthrough" not in control and "raise" not in control:
                return True
        if isinstance(statement, ast.Match) and statement.cases:
            final = statement.cases[-1]
            if (
                final.guard is None
                and _pattern_is_irrefutable(final.pattern)
                and all(
                    _statements_terminate_without_fallthrough(case.body)
                    for case in statement.cases
                )
            ):
                return True
        try_types = (ast.Try,)
        if hasattr(ast, "TryStar"):
            try_types = (*try_types, ast.TryStar)
        if isinstance(statement, try_types):
            if statement.finalbody and _statements_terminate_without_fallthrough(
                statement.finalbody
            ):
                return True
            body_terminates = _statements_terminate_without_fallthrough(
                statement.body
            )
            normal_terminates = body_terminates or (
                bool(statement.orelse)
                and _statements_terminate_without_fallthrough(statement.orelse)
            )
            handlers_terminate = all(
                _statements_terminate_without_fallthrough(handler.body)
                for handler in statement.handlers
            )
            if normal_terminates and handlers_terminate:
                return True
    return False


def _source_ordered_helper_return(
    definition: ast.FunctionDef | ast.AsyncFunctionDef,
    aliases: Mapping[str, str],
    module_assignments: Mapping[str, ast.expr],
    budget: _AnalysisBudget,
    module_bound_names: Iterable[str] = (),
    enclosing_names: Iterable[str] = (),
) -> _FlowValue | None:
    execution = _execution_scope(definition, budget)
    resolver = _SourceOrderedResolver(
        aliases,
        module_assignments,
        execution.local_functions,
        budget=budget,
        exception_scope=_exception_name_scope(
            definition,
            frozenset(module_bound_names)
            or (frozenset(aliases) | frozenset(module_assignments)),
            enclosing_names,
        ),
    )
    for name in resolver.exception_scope.entry_bound_names:
        resolver.values.setdefault(
            name,
            _flow_unknown("function parameter is dynamically unresolved"),
        )
    resolver.resolve(definition.body)
    returned = list(resolver.return_values)
    if not _statements_terminate_without_fallthrough(definition.body):
        returned.append(_FlowValue("scalar", None))
    if not returned:
        return None
    if all(value == returned[0] for value in returned):
        return returned[0]
    if any(_flow_is_sensitive(value) for value in returned):
        return _flow_unknown(
            "callable alias is dynamically unresolved",
            sensitive=True,
        )
    return _merge_flow_values("helper return", tuple(returned))


def _source_ordered_review_flow(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    aliases: Mapping[str, str],
    module_assignments: Mapping[str, ast.expr],
    local_functions: Mapping[
        str,
        ast.FunctionDef | ast.AsyncFunctionDef,
    ],
    sensitive_helper_names: frozenset[str] = frozenset(),
    helper_returns: Mapping[str, _FlowValue] | None = None,
    budget: _AnalysisBudget | None = None,
    *,
    module_bound_names: Iterable[str] = (),
    enclosing_names: Iterable[str] = (),
    sensitive_definition_markers: Iterable[str] = (),
    entry_values: Mapping[str, _FlowValue] | None = None,
) -> _ReviewFlow:
    enclosing_names = frozenset(
        set(enclosing_names)
        | set(
            _derived_enclosing_binding_markers(
                node,
                local_functions.values(),
            )
        )
    )
    local_definition_ids = {
        id(candidate)
        for candidate in ast.walk(node)
        if isinstance(candidate, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    external_functions = {
        name: definition
        for name, definition in local_functions.items()
        if id(definition) not in local_definition_ids
    }
    analysis_budget = budget or _AnalysisBudget()
    precise_helper_returns = dict(helper_returns or {})
    for name, definition in external_functions.items():
        if name in precise_helper_returns:
            continue
        returned = _source_ordered_helper_return(
            definition,
            aliases,
            module_assignments,
            analysis_budget,
            module_bound_names,
            enclosing_names,
        )
        if (
            returned is not None
            and returned.kind == "callable_summary"
            and isinstance(returned.value, tuple)
            and len(returned.value) == 2
            and str(returned.value[0]).startswith(
                _DEFINITION_POINT_MARKER_PREFIX
            )
        ):
            precise_helper_returns[name] = returned
    resolver = _SourceOrderedResolver(
        aliases,
        module_assignments,
        external_functions,
        sensitive_helper_names,
        precise_helper_returns,
        analysis_budget,
        _exception_name_scope(
            node,
            frozenset(module_bound_names)
            or (frozenset(aliases) | frozenset(module_assignments)),
            enclosing_names,
        ),
        _lexical_binding_scope(node),
        module_bound_names,
        enclosing_names,
        sensitive_definition_markers,
        entry_values,
    )
    for name in resolver.exception_scope.entry_bound_names:
        resolver.values.setdefault(
            name,
            _flow_unknown("function parameter is dynamically unresolved"),
        )
    return resolver.resolve(node.body)


def _helper_descriptor_kind(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    unavailable_names: frozenset[str],
) -> str | None:
    """Accept only a single builtin descriptor whose spelling is unshadowed."""

    if not node.decorator_list:
        return "ordinary"
    if len(node.decorator_list) != 1:
        return None
    decorator = node.decorator_list[0]
    if (
        isinstance(decorator, ast.Name)
        and decorator.id in {"staticmethod", "classmethod"}
        and decorator.id not in unavailable_names
    ):
        return decorator.id
    return None


def _descriptor_unavailable_names(nodes: Sequence[ast.stmt]) -> frozenset[str]:
    visitor = _ExceptionBindingVisitor()
    try:
        for node in nodes:
            visitor.visit(node)
            if any(
                isinstance(child, ast.ImportFrom)
                and any(alias.name == "*" for alias in child.names)
                for child in ast.walk(node)
            ):
                visitor.bound_names.update({"staticmethod", "classmethod"})
    except RecursionError:
        visitor.bound_names.update({"staticmethod", "classmethod"})
    return frozenset(visitor.bound_names)


def _review_function_registry(
    parsed: Mapping[str, ast.Module],
    exception_provenance: Mapping[str, _ModuleExceptionProvenance] | None = None,
    protected_namespace_mutations: Mapping[
        str,
        frozenset[str],
    ] | None = None,
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
        provenance = (
            exception_provenance.get(relative_path)
            if exception_provenance is not None
            else None
        ) or _module_exception_provenance(tree)
        aliases = _module_import_aliases(tree)
        aliases.update({
            qualified: _PROTECTED_MUTATION_ALIAS
            for qualified in (
                (protected_namespace_mutations or {}).get(
                    relative_path,
                    frozenset(),
                )
            )
        })
        assignments = _static_assignments(tree.body)
        descriptor_names = _descriptor_unavailable_names(tree.body)
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
                    provenance.module_bound_names,
                    provenance.enclosing_names_by_node.get(id(node), frozenset()),
                )
                for key in (
                    f"{relative_path}::{node.name}",
                    f"{module_name}.{node.name}",
                    f"{shorthand}.{node.name}",
                ):
                    register(key, definition)
            elif isinstance(node, ast.ClassDef):
                unavailable_descriptors = (
                    descriptor_names | _descriptor_unavailable_names(node.body)
                )
                constructor = next(
                    (
                        method
                        for method in node.body
                        if isinstance(
                            method,
                            (ast.FunctionDef, ast.AsyncFunctionDef),
                        )
                        and method.name == "__init__"
                    ),
                    None,
                )
                if constructor is None:
                    constructor = ast.parse(
                        "def __init__(*args, **kwargs):\n    pass\n"
                    ).body[0]
                constructor_definition = _ReviewFunction(
                    relative_path,
                    constructor,
                    aliases,
                    assignments,
                    node.name,
                    provenance.module_bound_names,
                    provenance.enclosing_names_by_node.get(
                        id(constructor),
                        frozenset(),
                    ),
                    _helper_descriptor_kind(constructor, unavailable_descriptors),
                )
                for key in (
                    f"{relative_path}::{node.name}",
                    f"{module_name}.{node.name}",
                    f"{shorthand}.{node.name}",
                ):
                    register(key, constructor_definition)
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
                        provenance.module_bound_names,
                        provenance.enclosing_names_by_node.get(
                            id(method),
                            frozenset(),
                        ),
                        _helper_descriptor_kind(method, unavailable_descriptors),
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
    for _ in range(len(parsed) + 1):
        changed = False
        before_count = len(registry)
        for relative_path, tree in parsed.items():
            module_name = ".".join(
                PurePosixPath(relative_path).with_suffix("").parts
            )
            for local, target in _module_import_aliases(tree).items():
                if not target.startswith("tests."):
                    continue
                for key, definition in tuple(registry.items()):
                    if not key.startswith(f"{target}."):
                        continue
                    suffix = key[len(target) + 1 :]
                    register(
                        f"{module_name}.{local}.{suffix}",
                        definition,
                    )
        changed = len(registry) != before_count
        if not changed:
            break
    return registry


def _helper_receiver_kinds(definition: _ReviewFunction | None) -> dict[str, str]:
    if definition is None or definition.descriptor_kind not in {
        "ordinary", "classmethod"
    }:
        return {}
    positional = [*definition.node.args.posonlyargs, *definition.node.args.args]
    if not positional:
        return {}
    return {
        positional[0].arg: (
            "class" if definition.descriptor_kind == "classmethod" else "instance"
        )
    }


def _helper_is_bound(
    call: ast.Call,
    definition: _ReviewFunction,
    aliases: Mapping[str, str],
    *,
    receiver_kinds: Mapping[str, str],
) -> bool | None:
    if definition.class_name is None:
        return False
    if definition.descriptor_kind is None:
        return None
    raw = _qualified_name(call.func)
    if raw is not None and raw.startswith(("self.", "cls.")):
        receiver_kind = receiver_kinds.get(raw.split(".", 1)[0])
        if receiver_kind is None:
            return None
        return definition.descriptor_kind == "classmethod" or (
            definition.descriptor_kind == "ordinary" and receiver_kind == "instance"
        )
    if definition.descriptor_kind == "staticmethod":
        return False
    resolved = _resolved_qualified_name(call.func, aliases)
    if (
        definition.node.name == "__init__"
        and resolved is not None
        and (
            resolved == definition.class_name
            or resolved.endswith(f".{definition.class_name}")
        )
    ):
        return True
    if definition.descriptor_kind != "classmethod":
        return False
    local_name = f"{definition.class_name}.{definition.node.name}"
    return resolved is not None and (
        resolved == local_name or resolved.endswith(f".{local_name}")
    )


def _bind_helper_arguments(
    call: ast.Call,
    definition: _ReviewFunction,
    aliases: Mapping[str, str],
    *,
    receiver_kinds: Mapping[str, str],
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
    positional_defaults = {
        parameter.arg: value
        for parameter, value in zip(
            positional[-len(arguments.defaults) :] if arguments.defaults else (),
            arguments.defaults,
            strict=True,
        )
    }
    bound = _helper_is_bound(
        call, definition, aliases, receiver_kinds=receiver_kinds
    )
    if bound is None:
        return None
    if bound:
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
        parameter.arg for parameter in (*positional, *arguments.kwonlyargs)
        if parameter.arg not in positional_only
    }
    for keyword in call.keywords:
        if (
            keyword.arg is None
            or keyword.arg not in allowed_keywords
            or keyword.arg in supplied
        ):
            return None
        supplied[keyword.arg] = (keyword.value, False)
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
        if "." not in resolved:
            candidates.append(f"{relative_path}::{resolved}")
    for key in candidates:
        definition = registry.get(key)
        if definition is not None:
            return key, definition
    return None


def _helper_has_sensitive_closure(
    definition: _ReviewFunction,
    registry: Mapping[str, _ReviewFunction],
    *,
    budget: _AnalysisBudget,
    active: frozenset[str] = frozenset(),
    depth: int = 0,
) -> bool:
    if depth > MAXIMUM_ANALYSIS_HELPER_DEPTH:
        raise InventoryError("analysis helper depth exceeds 64")
    execution = _execution_scope(definition.node, budget)
    aliases = _function_aliases(
        definition.aliases,
        execution.imports,
        execution.assignments,
    )
    if execution.closure_blockers:
        return True
    if _preclassified_sensitive_calls(
        definition.node.body,
        definition.aliases,
        budget,
        execution.local_functions,
        scope_node=definition.node,
        module_bound_names=definition.module_bound_names,
        enclosing_names=definition.enclosing_exception_names,
    ):
        return True
    nested_enclosing = _exception_name_scope(
        definition.node,
        definition.module_bound_names,
        definition.enclosing_exception_names,
    ).enclosing_names
    for local_node in execution.local_functions.values():
        if _helper_has_sensitive_closure(
            _ReviewFunction(
                definition.relative_path,
                local_node,
                aliases,
                definition.module_assignments,
                definition.class_name,
                definition.module_bound_names,
                nested_enclosing,
            ),
            registry,
            budget=budget,
            active=active,
            depth=depth + 1,
        ):
            return True
    for call in execution.calls:
        function = _resolved_qualified_name(call.func, aliases)
        callable_name = _resolved_callable_name(call.func, aliases)
        if function in _SUBPROCESS_FUNCTIONS:
            return True
        if (
            callable_name in _OWNER_CALLS
            or callable_name in _SCIENTIFIC_PROTECTED_CALLS
            or (callable_name is not None and callable_name.startswith("cupy."))
        ):
            return True
        helper = _resolved_helper(
            call,
            relative_path=definition.relative_path,
            class_name=definition.class_name,
            aliases=aliases,
            registry=registry,
        )
        if helper is not None:
            helper_key, nested = helper
            if helper_key not in active and _helper_has_sensitive_closure(
                nested,
                registry,
                budget=budget,
                active=active | {helper_key},
                depth=depth + 1,
            ):
                return True
        raw_function = _qualified_name(call.func)
        raw_root = (
            None if raw_function is None else raw_function.split(".", 1)[0]
        )
        imported_root = None if raw_root is None else aliases.get(raw_root)
        if function is not None and imported_root is not None and (
            imported_root.startswith("tests.")
            or imported_root.split(".", 1)[0].endswith("_test_support")
        ):
            return True
    return False


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


def _is_inherited_environment(node: ast.expr) -> bool:
    if (
        isinstance(node, ast.Attribute)
        and node.attr == "environ"
        and isinstance(node.value, ast.Name)
        and node.value.id == "os"
    ):
        return True
    if (
        isinstance(node, ast.Attribute)
        and node.attr == "environ"
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Name)
        and node.value.func.id == "__import__"
        and len(node.value.args) == 1
        and isinstance(node.value.args[0], ast.Constant)
        and node.value.args[0].value == "os"
    ):
        return True
    if isinstance(node, ast.Call) and not node.keywords:
        if (
            isinstance(node.func, ast.Name)
            and node.func.id == "dict"
            and len(node.args) == 1
        ):
            return _is_inherited_environment(node.args[0])
        if (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "copy"
            and not node.args
        ):
            return _is_inherited_environment(node.func.value)
    return False


def _environment_delta(
    node: ast.expr | None,
    assignments: Mapping[str, ast.expr],
    execution: _ExecutionScopeVisitor,
    subprocess_call: ast.Call,
) -> tuple[dict[str, str], list[str], str | None]:
    if node is None:
        return {}, [], None
    additions: dict[str, str] = {}
    removals: set[str] = set()
    if isinstance(node, ast.Dict):
        inherited = False
        for key_node, value_node in zip(node.keys, node.values, strict=True):
            if key_node is None:
                if inherited or not _is_inherited_environment(value_node):
                    return {}, [], "subprocess environment is dynamically unresolved"
                inherited = True
                continue
            key = _static_value(key_node, assignments)
            value = _static_value(value_node, assignments)
            if type(key) is not str or type(value) is not str:
                return {}, [], "subprocess environment is dynamically unresolved"
            additions[key] = value
        if not inherited:
            return {}, [], "subprocess environment replacement is forbidden"
        return additions, [], None
    if not isinstance(node, ast.Name):
        if _is_inherited_environment(node):
            return {}, [], None
        return {}, [], "subprocess environment is dynamically unresolved"
    initial = assignments.get(node.id)
    if initial is None or not _is_inherited_environment(initial):
        return {}, [], "subprocess environment replacement is forbidden"
    call_position = (
        int(getattr(subprocess_call, "lineno", 0)),
        int(getattr(subprocess_call, "col_offset", 0)),
    )
    events: list[tuple[tuple[int, int], str, ast.AST]] = []
    for assignment in execution.assignments:
        events.append((
            (
                int(getattr(assignment, "lineno", 0)),
                int(getattr(assignment, "col_offset", 0)),
            ),
            "assignment",
            assignment,
        ))
    for candidate in execution.calls:
        events.append((
            (
                int(getattr(candidate, "lineno", 0)),
                int(getattr(candidate, "col_offset", 0)),
            ),
            "call",
            candidate,
        ))
    for position, event_kind, event in sorted(events, key=lambda row: row[0]):
        if position >= call_position:
            break
        if event_kind == "assignment":
            assignment = event
            if not (
                isinstance(assignment, ast.Assign)
                and len(assignment.targets) == 1
            ):
                continue
            target = assignment.targets[0]
            if not (
                isinstance(target, ast.Subscript)
                and isinstance(target.value, ast.Name)
                and target.value.id == node.id
            ):
                continue
            key = _static_value(target.slice, assignments)
            value = _static_value(assignment.value, assignments)
            if type(key) is not str or type(value) is not str:
                return {}, [], "subprocess environment mutation is unresolved"
            additions[key] = value
            removals.discard(key)
            continue
        candidate = event
        if not (
            isinstance(candidate, ast.Call)
            and isinstance(candidate.func, ast.Attribute)
            and candidate.func.attr == "pop"
            and isinstance(candidate.func.value, ast.Name)
            and candidate.func.value.id == node.id
            and candidate.args
        ):
            continue
        key = _static_value(candidate.args[0], assignments)
        if type(key) is not str:
            return {}, [], "subprocess environment removal is unresolved"
        additions.pop(key, None)
        removals.add(key)
    return additions, sorted(removals), None


_FLOW_ENV_NOT_CAPTURED = object()


def _process_definition(
    call: ast.Call,
    *,
    aliases: Mapping[str, str],
    assignments: Mapping[str, ast.expr],
    execution: _ExecutionScopeVisitor,
    environment_snapshot: object = _FLOW_ENV_NOT_CAPTURED,
    child_depth: int = 0,
    analysis_budget: _AnalysisBudget | None = None,
) -> tuple[
    dict[str, object] | None,
    str | None,
    list[tuple[str, dict[str, object]]],
]:
    if analysis_budget is None:
        analysis_budget = _AnalysisBudget()
    analysis_budget.consume()
    function = _resolved_qualified_name(call.func, aliases)
    if function not in _SUBPROCESS_FUNCTIONS:
        return None, None, []
    if any(keyword.arg is None for keyword in call.keywords):
        return None, "subprocess **kwargs are dynamically unresolved", []
    allowed_keywords = {
        "subprocess.run": {"check", "cwd", "env", "shell", "timeout"},
        "subprocess.call": {"cwd", "env", "shell", "timeout"},
        "subprocess.check_call": {"cwd", "env", "shell", "timeout"},
        "subprocess.check_output": {"cwd", "env", "shell", "timeout"},
        "subprocess.Popen": {"cwd", "env", "shell"},
    }[function]
    for keyword in call.keywords:
        if keyword.arg not in allowed_keywords:
            return (
                None,
                f"unsupported subprocess keyword: {keyword.arg}",
                [],
            )
    if len(call.args) != 1:
        return None, "subprocess requires one exact argv argument", []
    argv_node = call.args[0]
    if not isinstance(argv_node, (ast.List, ast.Tuple)) or not argv_node.elts:
        return None, "subprocess argv is dynamically unresolved", []
    first = _resolved_qualified_name(argv_node.elts[0], aliases)
    if first != "sys.executable":
        return (
            None,
            "subprocess executable is not the active Python worker",
            [],
        )
    argv: list[str] = []
    for node in argv_node.elts[1:]:
        value = _static_value(node, assignments)
        if type(value) is not str:
            return None, "subprocess argv tokens are dynamically unresolved", []
        argv.append(value)
    if not argv:
        return None, "subprocess Python argv is empty", []
    keywords = {keyword.arg: keyword.value for keyword in call.keywords}
    shell = (
        False
        if "shell" not in keywords
        else _static_value(keywords["shell"], assignments)
    )
    if shell is not False:
        return (
            None,
            "subprocess shell semantics are forbidden or unresolved",
            [],
        )
    if "timeout" not in keywords:
        return None, "subprocess timeout must be explicitly bounded", []
    timeout = _static_value(keywords["timeout"], assignments)
    if type(timeout) not in (int, float) or timeout <= 0:
        return None, "subprocess timeout is dynamically unresolved", []
    if environment_snapshot is _FLOW_ENV_NOT_CAPTURED:
        environment, removals, environment_error = _environment_delta(
            keywords.get("env"), assignments, execution, call
        )
    else:
        if not (
            isinstance(environment_snapshot, tuple)
            and len(environment_snapshot) == 3
        ):
            raise RuntimeError("captured subprocess environment is malformed")
        environment, removals, environment_error = environment_snapshot
    if environment_error is not None:
        return None, environment_error, []
    cwd = _cwd_class(keywords.get("cwd"), assignments)
    if cwd is None:
        return None, "subprocess cwd is dynamically unresolved", []
    check = (
        function in {"subprocess.check_call", "subprocess.check_output"}
        if "check" not in keywords
        else _static_value(keywords["check"], assignments)
    )
    if type(check) is not bool:
        return None, "subprocess return contract is dynamically unresolved", []
    dynamic_program_sha256: str | None = None
    child_definitions: list[tuple[str, dict[str, object]]] = []
    if "-c" in argv:
        if child_depth >= MAXIMUM_ANALYSIS_CHILD_DEPTH:
            return None, "subprocess child analysis depth exceeds 4", []
        indices = [index for index, token in enumerate(argv) if token == "-c"]
        if len(indices) != 1 or indices[0] + 1 >= len(argv):
            return None, "subprocess dynamic Python program is incomplete", []
        program = argv[indices[0] + 1]
        dynamic_program_sha256 = sha256(program.encode("utf-8")).hexdigest()
        try:
            program_tree = ast.parse(program, filename="<subprocess-python-c>")
        except SyntaxError:
            return (
                None,
                "subprocess dynamic Python program cannot be parsed",
                [],
            )
        program_execution = _ExecutionScopeVisitor(analysis_budget)
        try:
            for statement in program_tree.body:
                program_execution.visit(statement)
        except RecursionError as error:
            raise InventoryError(
                "analysis expression depth exceeds safe recursion"
            ) from error
        if program_execution.closure_blockers:
            return (
                None,
                "subprocess dynamic Python program has unresolved callback closure",
                [],
            )
        program_aliases = _function_aliases(
            _module_import_aliases(program_tree),
            program_execution.imports,
            program_execution.assignments,
        )
        program_assignments = _static_assignments(program_tree.body)
        program_exception_provenance = _module_exception_provenance(program_tree)
        program_helper_returns = {
            name: returned
            for name, definition in program_execution.local_functions.items()
            for returned in (
                _source_ordered_helper_return(
                    definition,
                    program_aliases,
                    program_assignments,
                    analysis_budget,
                    program_exception_provenance.module_bound_names,
                    program_exception_provenance.enclosing_names_by_node.get(
                        id(definition), frozenset()
                    ),
                ),
            )
            if returned is not None
        }
        program_flow = _SourceOrderedResolver(
            _module_import_aliases(program_tree),
            program_assignments,
            program_execution.local_functions,
            helper_returns=program_helper_returns,
            budget=analysis_budget,
            exception_scope=_exception_name_scope(
                None,
                program_exception_provenance.module_bound_names,
            ),
        ).resolve(program_tree.body)
        if program_flow.standalone_blockers:
            return (
                None,
                "subprocess dynamic Python program has unresolved sensitive dataflow",
                [],
            )
        child_keys: dict[int, bytes] = {}
        child_rows: dict[bytes, dict[str, object]] = {}
        child_processes: dict[int, dict[str, object]] = {}
        child_process_keys: dict[int, bytes] = {}
        for child_index, child in enumerate(program_execution.calls):
            child_aliases = program_flow.aliases_by_call.get(
                id(child),
                program_aliases,
            )
            child_assignments = program_flow.assignments_by_call.get(
                id(child),
                program_assignments,
            )
            child_callable = program_flow.callables_by_call.get(id(child))
            if id(child) in program_flow.blockers_by_call:
                return (
                    None,
                    "subprocess dynamic Python program has unresolved "
                    "sensitive dataflow",
                    [],
                )
            raw_child = _qualified_name(child.func)
            if (
                raw_child in program_execution.local_functions
                and _contains_sensitive_runtime(
                    program_execution.local_functions[raw_child],
                    analysis_budget,
                )
            ):
                return (
                    None,
                    "subprocess dynamic Python program has unresolved helper closure",
                    [],
                )
            child_process, child_error, nested = _process_definition(
                child,
                aliases=child_aliases,
                assignments=child_assignments,
                execution=program_execution,
                environment_snapshot=program_flow.environments_by_call.get(
                    id(child),
                    _FLOW_ENV_NOT_CAPTURED,
                ),
                child_depth=child_depth + 1,
                analysis_budget=analysis_budget,
            )
            if child_error is not None:
                if child_error == "subprocess child analysis depth exceeds 4":
                    return None, child_error, []
                if child_error == (
                    "subprocess environment exceptional state is ambiguous"
                ):
                    return (
                        None,
                        "subprocess dynamic Python program has unresolved "
                        "subprocess environment exceptional state",
                        [],
                    )
                return (
                    None,
                    "subprocess dynamic Python child subprocess is unresolved: "
                    f"{child_error}",
                    [],
                )
            if child_process is not None:
                child_processes[id(child)] = child_process
                process_key = f"process-site:{child_index}".encode("ascii")
                child_keys[id(child)] = process_key
                child_process_keys[id(child)] = process_key
                child_definitions.extend(nested)
                continue
            child_definition = _call_definition(
                child,
                child_aliases,
                child_callable,
            )
            if child_definition is not None:
                key = _semantic_bytes({
                    name: value
                    for name, value in child_definition.items()
                    if name != "maximum_calls"
                })
                child_keys[id(child)] = key
                child_rows[key] = child_definition
                continue
            protected_reason = _protected_call_blocker_reason(
                child,
                child_aliases,
                child_callable,
            )
            if protected_reason is not None:
                return (
                    None,
                    "subprocess dynamic Python program has unresolved protected call",
                    [],
                )
        child_counts, child_dynamic = _runtime_call_bounds(
            program_tree.body,
            child_keys,
            assignments=program_assignments,
            relative_path="<subprocess-python-c>",
            aliases=program_aliases,
            helper_registry={},
            analysis_budget=analysis_budget,
        )
        if child_dynamic:
            return (
                None,
                "subprocess dynamic Python program has dynamic repetition",
                [],
            )
        for child_id, child_process in child_processes.items():
            key = child_process_keys[child_id]
            maximum_calls = child_counts.get(key, 0)
            if maximum_calls != 1:
                return (
                    None,
                    "subprocess dynamic Python child subprocess repetition "
                    "is not representable",
                    [],
                )
            child_definitions.append(("subprocess", child_process))
        for key, maximum_calls in child_counts.items():
            if key not in child_rows:
                continue
            child_definition = dict(child_rows[key])
            child_definition["maximum_calls"] = maximum_calls
            child_definitions.append(("call", child_definition))
    definition: dict[str, object] = {
        "executable_role": "python",
        "executable_slot": "active_worker",
        "executable_constraints": {},
        "argv": argv,
        "argv_template": [],
        "dynamic_program_sha256": dynamic_program_sha256,
        "cwd_class": cwd,
        "environment_additions": environment,
        "environment_removals": removals,
        "timeout_ns": int(timeout * 1_000_000_000),
        "expected_return_category": (
            "spawned"
            if function == "subprocess.Popen"
            else "success" if check else "completed"
        ),
        "read_roots": [cwd],
        "write_roots": [],
        "fixed_descendant_permission": bool(child_definitions),
    }
    return definition, None, child_definitions


def _call_definition(
    call: ast.Call,
    aliases: Mapping[str, str],
    qualified_override: str | None = None,
) -> dict[str, object] | None:
    qualified = qualified_override or _resolved_callable_name(call.func, aliases)
    if qualified is None:
        return None
    if qualified in _OWNER_CALLS:
        kind = "owner"
        module_name = qualified.rsplit(".", 1)[0]
        action = "invoke"
        return_contract = "opaque"
    elif qualified in _SCIENTIFIC_CALL_CONTRACTS:
        kind = "scientific"
        module_name = qualified.rsplit(".", 1)[0]
        action, return_contract = _SCIENTIFIC_CALL_CONTRACTS[qualified]
    elif qualified in _CUDA_CALLS:
        kind, return_contract = _CUDA_CALLS[qualified]
        module_name = "cupy"
        action = "allocate" if kind == "cuda_allocation" else "query"
    else:
        return None
    return {
        "kind": kind,
        "module_name": module_name,
        "qualified_name": qualified,
        "action": action,
        "maximum_calls": 1,
        "return_contract": return_contract,
    }


def _protected_call_blocker_reason(
    call: ast.Call,
    aliases: Mapping[str, str],
    qualified_override: str | None = None,
) -> str | None:
    qualified = qualified_override or _resolved_callable_name(call.func, aliases)
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


def _scale_nested_review_rows(
    rows: Sequence[Mapping[str, object]],
    *,
    multiplier: int,
    dynamic: bool,
    item_id: str,
    relative_path: str,
    call: ast.Call,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    if not rows:
        return [], []
    if dynamic:
        return [], [
            _review_blocker(
                item_id,
                relative_path,
                call,
                "dynamic repetition prevents a finite helper call bound",
            )
        ]
    if multiplier == 0:
        return [], []
    copied = [dict(row) for row in rows]
    if multiplier == 1:
        return copied, []
    if any(row["capability_kind"] == "subprocess" for row in copied):
        return [], [
            _review_blocker(
                item_id,
                relative_path,
                call,
                "subprocess repetition through helper is not representable",
            )
        ]
    for row in copied:
        row["maximum_calls"] = _checked_cardinality_multiply(
            int(row["maximum_calls"]),
            multiplier,
        )
        definition = {
            key: value
            for key, value in row.items()
            if key not in {
                "item_id",
                "approval_scope",
                "capability_kind",
                "capability_id",
            }
        }
        row["capability_id"] = _capability_id("call", definition)
    return copied, []


def _append_implicit_protocol_analyzed_sites(
    events: Sequence[
        tuple[
            ast.AST,
            _ImplicitClassDescriptor,
            frozenset[str],
            str,
        ]
    ],
    *,
    item_id: str,
    relative_path: str,
    aliases: Mapping[str, str],
    analyzed_sites: list[dict[str, object]],
    closure_depth: int,
    closure_helper_key: str | None,
    budget: _AnalysisBudget,
) -> None:
    """Census implicit dispatch sites and protected calls hidden behind them."""

    seen = {
        (
            str(row["item_id"]),
            str(row["relative_path"]),
            int(row["line"]),
            str(row["sink_kind"]),
            str(row["qualified_name"]),
            int(row["closure_depth"]),
            row["closure_helper_key"],
        )
        for row in analyzed_sites
    }

    def append(
        node: ast.AST,
        sink_kind: str,
        qualified_name: str,
    ) -> None:
        key = (
            item_id,
            relative_path,
            int(getattr(node, "lineno", 0)),
            sink_kind,
            qualified_name,
            closure_depth,
            closure_helper_key,
        )
        if key in seen:
            return
        seen.add(key)
        analyzed_sites.append({
            "item_id": item_id,
            "relative_path": relative_path,
            "line": key[2],
            "sink_kind": sink_kind,
            "qualified_name": qualified_name,
            "closure_depth": closure_depth,
            "closure_helper_key": closure_helper_key,
        })

    visited_methods: set[tuple[int, str]] = set()
    for site, descriptor, method_names, _reason in events:
        active_methods = descriptor.sensitive_methods & method_names
        for method_name in sorted(active_methods):
            append(
                site,
                "implicit_protocol",
                f"{descriptor.name}.{method_name}",
            )
        for method in descriptor.methods:
            if method.name not in active_methods:
                continue
            method_key = (id(method), method.name)
            if method_key in visited_methods:
                continue
            visited_methods.add(method_key)
            execution = _execution_scope(method, budget)
            method_aliases = _function_aliases(
                aliases,
                execution.imports,
                execution.assignments,
            )
            for call in execution.calls:
                qualified = _resolved_callable_name(call.func, method_aliases)
                if qualified in _SUBPROCESS_FUNCTIONS:
                    append(call, "subprocess", qualified)
                elif qualified is not None and qualified.startswith("cupy."):
                    append(call, "cupy", qualified)
                elif qualified in _OWNER_CALLS | _SCIENTIFIC_PROTECTED_CALLS:
                    append(call, "protected_call", qualified)


def _review_body(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    *,
    item_id: str,
    relative_path: str,
    aliases: Mapping[str, str],
    module_assignments: Mapping[str, ast.expr],
    class_name: str | None,
    helper_registry: Mapping[str, _ReviewFunction],
    module_bound_names: Iterable[str] = (),
    enclosing_exception_names: Iterable[str] = (),
    active_helpers: frozenset[str] = frozenset(),
    analyzed_sites: list[dict[str, object]] | None = None,
    helper_edges: list[dict[str, object]] | None = None,
    closure_depth: int = 0,
    closure_helper_key: str | None = None,
    analysis_budget: _AnalysisBudget | None = None,
    entry_values: Mapping[str, _FlowValue] | None = None,
    receiver_kinds: Mapping[str, str] | None = None,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    if closure_depth > MAXIMUM_ANALYSIS_HELPER_DEPTH:
        raise InventoryError("analysis helper depth exceeds 64")
    if analysis_budget is None:
        analysis_budget = _AnalysisBudget()
    analysis_budget.consume()
    if analyzed_sites is None:
        analyzed_sites = []
    if helper_edges is None:
        helper_edges = []
    if receiver_kinds is None:
        caller = helper_registry.get(f"{relative_path}::{class_name}::{node.name}")
        receiver_kinds = _helper_receiver_kinds(
            caller if caller is not None and caller.node is node else None
        )
    body_receiver_kinds = dict(receiver_kinds)
    receiver_bindings = _ExceptionBindingVisitor()
    for statement in node.body:
        receiver_bindings.visit(statement)
    for name in receiver_bindings.bound_names:
        body_receiver_kinds.pop(name, None)
    execution = _execution_scope(node, analysis_budget)
    body_aliases = _function_aliases(
        aliases,
        execution.imports,
        execution.assignments,
    )
    assignments = dict(module_assignments)
    assignments.update(_static_assignments(node.body))
    referenced_names = {
        candidate.id
        for statement in execution.assignments
        for candidate in _metered_ast_walk(statement, analysis_budget)
        if isinstance(candidate, ast.Name)
    }
    referenced_names.update(
        raw.split(".", 1)[0]
        for call in execution.calls
        for raw in (_qualified_name(call.func),)
        if raw is not None
    )
    # Definition-time expressions (lambda defaults in particular) are eager
    # even when their bodies are deferred, so their local helper identities
    # must be available to the source-point expression resolver.
    referenced_names.update(
        candidate.func.id
        for candidate in ast.walk(node)
        if isinstance(candidate, ast.Call)
        and isinstance(candidate.func, ast.Name)
    )
    referenced_names.update(
        candidate.id
        for definition in ast.walk(node)
        if isinstance(definition, (ast.FunctionDef, ast.AsyncFunctionDef))
        for decorator in definition.decorator_list
        for candidate in ast.walk(decorator)
        if isinstance(candidate, ast.Name)
        and isinstance(candidate.ctx, ast.Load)
    )
    sensitive_helper_names: set[str] = set()
    helper_returns: dict[str, _FlowValue] = {}
    sensitive_definition_markers: set[str] = set()
    local_definitions = tuple(execution.local_function_definitions)
    local_enclosing_names = _exception_name_scope(
        node,
        module_bound_names,
        enclosing_exception_names,
    ).enclosing_names
    local_review_functions: dict[str, _ReviewFunction] = {}
    local_review_functions_by_marker: dict[str, _ReviewFunction] = {}
    for definition in local_definitions:
        reviewed = _ReviewFunction(
            relative_path,
            definition,
            aliases,
            module_assignments,
            class_name,
            frozenset(module_bound_names),
            frozenset(
                set(local_enclosing_names)
                | set(_derived_enclosing_binding_markers(definition, (node,)))
            ),
        )
        local_review_functions[f"{relative_path}::{definition.name}"] = reviewed
        local_review_functions_by_marker[
            _definition_point_marker(definition)
        ] = reviewed
    local_helper_registry = dict(helper_registry)
    local_helper_registry.update(local_review_functions)
    for definition in local_definitions:
        marker = _definition_point_marker(definition)
        reviewed = local_review_functions_by_marker[marker]
        registry = (
            helper_registry
            if _bounded_local_generator_dependencies(
                definition,
                analysis_budget,
            ) is not None
            else local_helper_registry
        )
        directly_reviewable = _helper_has_sensitive_closure(
            reviewed,
            registry,
            budget=analysis_budget,
            active=frozenset({f"{relative_path}::{definition.name}"}),
        )
        if directly_reviewable:
            sensitive_definition_markers.add(marker)
    for name in referenced_names:
        definition = helper_registry.get(f"{relative_path}::{name}")
        if definition is None:
            continue
        if (
            definition.class_name is not None
            and definition.node.name == "__init__"
            and name == definition.class_name
        ):
            class_method_definitions = tuple(
                (method_name, candidate)
                for method_name in _IMPLICIT_CLASS_METHOD_NAMES
                for candidate in (
                    helper_registry.get(
                        f"{definition.relative_path}::"
                        f"{definition.class_name}::{method_name}"
                    ),
                )
                if candidate is not None
            )
            descriptor = _implicit_class_descriptor(
                definition.class_name,
                tuple(
                    candidate.node
                    for _, candidate in class_method_definitions
                ),
                definition.aliases,
                definition.module_assignments,
                analysis_budget,
                exact_init_review=True,
                proven_sensitive_methods=(
                    method_name
                    for method_name, candidate in class_method_definitions
                    if _helper_has_sensitive_closure(
                        candidate,
                        helper_registry,
                        budget=analysis_budget,
                    )
                ),
            )
            returned = _FlowValue(
                "implicit_class_instance",
                descriptor,
                bool(descriptor.sensitive_methods),
                "implicit class protocol execution is dynamically unresolved",
            )
        else:
            returned = _source_ordered_helper_return(
                definition.node,
                definition.aliases,
                definition.module_assignments,
                analysis_budget,
                definition.module_bound_names,
                definition.enclosing_exception_names,
            )
        if returned is not None:
            helper_returns[name] = returned
        if _helper_has_sensitive_closure(
            definition,
            helper_registry,
            budget=analysis_budget,
        ):
            sensitive_helper_names.add(name)
    source_functions = dict(execution.local_functions)
    for name in referenced_names:
        definition = helper_registry.get(f"{relative_path}::{name}")
        if definition is not None:
            source_functions[name] = definition.node
    source_flow = _source_ordered_review_flow(
        node,
        aliases,
        module_assignments,
        source_functions,
        frozenset(sensitive_helper_names),
        helper_returns,
        analysis_budget,
        module_bound_names=module_bound_names,
        enclosing_names=enclosing_exception_names,
        sensitive_definition_markers=sensitive_definition_markers,
        entry_values=entry_values,
    )
    _append_implicit_protocol_analyzed_sites(
        source_flow.implicit_protocol_events,
        item_id=item_id,
        relative_path=relative_path,
        aliases=body_aliases,
        analyzed_sites=analyzed_sites,
        closure_depth=closure_depth,
        closure_helper_key=closure_helper_key,
        budget=analysis_budget,
    )
    site_keys = {
        id(call): f"site:{index}".encode("ascii")
        for index, call in enumerate(execution.calls)
    }
    site_bounds, dynamic_sites = _runtime_call_bounds(
        node.body,
        site_keys,
        assignments=assignments,
        relative_path=relative_path,
        aliases=body_aliases,
        helper_registry=helper_registry,
        analysis_budget=analysis_budget,
    )
    rows: list[dict[str, object]] = []
    blockers: list[dict[str, object]] = []
    local_definitions_by_marker = {
        _definition_point_marker(definition): definition
        for definition in execution.local_function_definitions
    }
    blockers.extend(
        _review_blocker(item_id, relative_path, call, reason)
        for call, reason in execution.closure_blockers
        if not (
            reason == "callback closure"
            and source_flow.callables_by_call.get(id(call), "")
            in local_definitions_by_marker
            and _bounded_local_generator_dependencies(
                local_definitions_by_marker[
                    source_flow.callables_by_call[id(call)]
                ],
                analysis_budget,
            )
            is not None
        )
    )
    blockers.extend(
        _review_blocker(item_id, relative_path, target, reason)
        for target, reason in source_flow.standalone_blockers
    )
    call_definitions: dict[int, bytes] = {}
    call_definition_rows: dict[bytes, dict[str, object]] = {}
    call_nodes: dict[bytes, ast.Call] = {}
    preclassified_helpers = dict(execution.local_functions)
    for name in referenced_names:
        definition = helper_registry.get(f"{relative_path}::{name}")
        if definition is not None:
            preclassified_helpers[name] = definition.node
    sensitive_calls = _preclassified_sensitive_calls(
        node.body,
        aliases,
        analysis_budget,
        preclassified_helpers,
        scope_node=node,
        module_bound_names=(
            frozenset(module_bound_names)
            or (frozenset(aliases) | frozenset(module_assignments))
        ),
        enclosing_names=enclosing_exception_names,
        enclosing_names_by_node={
            id(definition.node): definition.enclosing_exception_names
            for definition in helper_registry.values()
        },
        entry_bound_unknown_names=(entry_values or {}).keys(),
    )
    resolved_sensitive_calls: set[int] = set()
    dispositions: dict[int, str] = {}
    for call in execution.calls:
        if id(call) not in source_flow.aliases_by_call:
            dispositions[id(call)] = "proved_unreachable"
            continue
        call_aliases = source_flow.aliases_by_call.get(id(call), body_aliases)
        call_assignments = source_flow.assignments_by_call.get(
            id(call),
            assignments,
        )
        flow_callable = source_flow.callables_by_call.get(id(call))
        function = flow_callable or _resolved_qualified_name(
            call.func,
            call_aliases,
        )
        callable_name = flow_callable or _resolved_callable_name(
            call.func,
            call_aliases,
        )
        flow_blocker = source_flow.blockers_by_call.get(id(call))
        if flow_blocker is None and function in _SUBPROCESS_FUNCTIONS:
            resolved_sensitive_calls.add(id(call))
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
        elif flow_blocker is None and (
            callable_name in _OWNER_CALLS
            or callable_name in _SCIENTIFIC_PROTECTED_CALLS
            or (
                callable_name is not None
                and callable_name.startswith("cupy.")
            )
        ):
            resolved_sensitive_calls.add(id(call))
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
        if flow_blocker is not None:
            dispositions[id(call)] = "blocker"
            blockers.append(
                _review_blocker(
                    item_id,
                    relative_path,
                    call,
                    flow_blocker,
                )
            )
            continue
        if id(call) in source_flow.implicit_blocked_calls:
            dispositions[id(call)] = "blocker"
            continue
        if id(call) in source_flow.proved_non_sensitive_calls:
            dispositions[id(call)] = "proved_non_sensitive"
            continue
        raw_function = _qualified_name(call.func)
        exact_local_node = local_definitions_by_marker.get(flow_callable or "")
        local_name = None
        if exact_local_node is not None:
            local_name = exact_local_node.name
        elif raw_function in execution.local_functions:
            local_name = raw_function
        elif function in execution.local_functions:
            local_name = function
        if local_name is not None:
            local_node = (
                exact_local_node
                if exact_local_node is not None
                else execution.local_functions[local_name]
            )
            generator_shape = _bounded_local_generator_dependencies(
                local_node,
                analysis_budget,
            )
            if generator_shape is not None:
                modes = source_flow.local_generator_consumption_modes.get(
                    id(call),
                    set(),
                )
                marker = _definition_point_marker(local_node)
                if (
                    "full" not in modes
                    or marker not in sensitive_definition_markers
                    or local_node.args.vararg is not None
                    or local_node.args.kwarg is not None
                ):
                    continue
            local_definition = _ReviewFunction(
                relative_path,
                local_node,
                call_aliases,
                call_assignments,
                class_name,
                frozenset(module_bound_names),
                frozenset(
                    set(
                        _exception_name_scope(
                            node,
                            module_bound_names,
                            enclosing_exception_names,
                        ).enclosing_names
                    )
                    | set(
                        _derived_enclosing_binding_markers(
                            local_node,
                            (node,),
                        )
                    )
                ),
            )
            local_key = (
                f"{relative_path}::<local:{local_name}:"
                f"{int(getattr(local_node, 'lineno', 0))}>"
            )
            if not _helper_has_sensitive_closure(
                local_definition,
                helper_registry,
                budget=analysis_budget,
                active=active_helpers | {local_key},
            ):
                continue
            if local_key in active_helpers:
                blockers.append(
                    _review_blocker(
                        item_id,
                        relative_path,
                        call,
                        "recursive local helper closure is unresolved",
                    )
                )
                continue
            supplied = _bind_helper_arguments(
                call,
                local_definition,
                call_aliases,
                receiver_kinds=body_receiver_kinds,
            )
            local_assignments = dict(call_assignments)
            argument_failure = supplied is None
            if supplied is not None:
                for parameter, (expression, is_default) in supplied.items():
                    value = _static_value(
                        expression,
                        local_definition.module_assignments
                        if is_default
                        else call_assignments,
                    )
                    if value is _STATIC_UNRESOLVED:
                        argument_failure = True
                        break
                    local_assignments[parameter] = ast.parse(
                        repr(value),
                        mode="eval",
                    ).body
            if argument_failure:
                blockers.append(
                    _review_blocker(
                        item_id,
                        relative_path,
                        call,
                        "dynamic local helper arguments are unresolved",
                    )
                )
                local_assignments = _unresolved_helper_assignments(
                    local_definition
                )
            added, refused = _review_body(
                local_node,
                item_id=item_id,
                relative_path=relative_path,
                aliases=call_aliases,
                module_assignments=local_assignments,
                class_name=class_name,
                helper_registry=helper_registry,
                module_bound_names=local_definition.module_bound_names,
                enclosing_exception_names=(
                    local_definition.enclosing_exception_names
                ),
                active_helpers=active_helpers | {local_key},
                analyzed_sites=analyzed_sites,
                helper_edges=helper_edges,
                closure_depth=closure_depth + 1,
                closure_helper_key=local_key,
                analysis_budget=analysis_budget,
                receiver_kinds={
                    name: kind for name, kind in body_receiver_kinds.items()
                    if name not in _lexical_binding_scope(local_node).parameter_names
                },
            )
            site_key = site_keys[id(call)]
            scaled, scale_blockers = _scale_nested_review_rows(
                added,
                multiplier=site_bounds.get(site_key, 0),
                dynamic=site_key in dynamic_sites,
                item_id=item_id,
                relative_path=relative_path,
                call=call,
            )
            rows.extend(scaled)
            blockers.extend(refused)
            blockers.extend(scale_blockers)
            continue
        helper = _resolved_helper(
            call,
            relative_path=relative_path,
            class_name=class_name,
            aliases=call_aliases,
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
                call_aliases,
                receiver_kinds=body_receiver_kinds,
            )
            argument_failure = supplied_arguments is None
            if supplied_arguments is None:
                if not _helper_has_sensitive_closure(
                    definition,
                    helper_registry,
                    budget=analysis_budget,
                    active=active_helpers | {helper_key},
                ):
                    continue
                helper_assignments = _unresolved_helper_assignments(
                    definition
                )
            else:
                helper_assignments = dict(definition.module_assignments)
                for parameter, (expression, is_default) in (
                    supplied_arguments.items()
                ):
                    value = _static_value(
                        expression,
                        (
                            definition.module_assignments
                            if is_default
                            else call_assignments
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
                if not _helper_has_sensitive_closure(
                    definition,
                    helper_registry,
                    budget=analysis_budget,
                    active=active_helpers | {helper_key},
                ):
                    continue
                helper_assignments = _unresolved_helper_assignments(
                    definition
                )
            added, refused = _review_body(
                definition.node,
                item_id=item_id,
                relative_path=definition.relative_path,
                aliases=definition.aliases,
                module_assignments=helper_assignments,
                class_name=definition.class_name,
                helper_registry=helper_registry,
                module_bound_names=definition.module_bound_names,
                enclosing_exception_names=(
                    definition.enclosing_exception_names
                ),
                active_helpers=active_helpers | {helper_key},
                analyzed_sites=analyzed_sites,
                helper_edges=helper_edges,
                closure_depth=closure_depth + 1,
                closure_helper_key=helper_key,
                analysis_budget=analysis_budget,
                receiver_kinds={
                    name: kind
                    for name, kind in _helper_receiver_kinds(definition).items()
                    if supplied_arguments is not None and name not in supplied_arguments
                },
            )
            if argument_failure and (
                supplied_arguments is None or refused or not added
            ):
                blockers.append(
                    _review_blocker(
                        item_id,
                        relative_path,
                        call,
                        "dynamic helper arguments prevent exact sink derivation",
                    )
                )
            site_key = site_keys[id(call)]
            scaled, scale_blockers = _scale_nested_review_rows(
                added,
                multiplier=site_bounds.get(site_key, 0),
                dynamic=site_key in dynamic_sites,
                item_id=item_id,
                relative_path=relative_path,
                call=call,
            )
            rows.extend(scaled)
            blockers.extend(refused)
            blockers.extend(scale_blockers)
            continue
        raw_root = (
            None if raw_function is None else raw_function.split(".", 1)[0]
        )
        imported_root = (
            None if raw_root is None else call_aliases.get(raw_root)
        )
        if function is not None and imported_root is not None and (
            imported_root.startswith("tests.")
            or imported_root.split(".", 1)[0].endswith("_test_support")
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
        process, process_error, child_definitions = _process_definition(
            call,
            aliases=call_aliases,
            assignments=call_assignments,
            execution=execution,
            environment_snapshot=source_flow.environments_by_call.get(
                id(call),
                _FLOW_ENV_NOT_CAPTURED,
            ),
            analysis_budget=analysis_budget,
        )
        if process_error is not None:
            dispositions[id(call)] = "blocker"
            blockers.append(
                _review_blocker(item_id, relative_path, call, process_error)
            )
            continue
        if process is not None:
            site_key = site_keys[id(call)]
            if site_key in dynamic_sites:
                dispositions[id(call)] = "blocker"
                blockers.append(
                    _review_blocker(
                        item_id,
                        relative_path,
                        call,
                        "dynamic repetition prevents a finite subprocess bound",
                    )
                )
                continue
            if site_bounds.get(site_key, 0) != 1:
                if site_bounds.get(site_key, 0) > 1:
                    dispositions[id(call)] = "blocker"
                    blockers.append(
                        _review_blocker(
                            item_id,
                            relative_path,
                            call,
                            "subprocess repetition is not representable",
                        )
                    )
                else:
                    dispositions[id(call)] = "proved_unreachable"
                continue
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
            dispositions[id(call)] = "row"
            for child_kind, child_definition in child_definitions:
                prefix = "process" if child_kind == "subprocess" else "call"
                child_id = _capability_id(prefix, child_definition)
                rows.append(
                    {
                        "item_id": item_id,
                        "approval_scope": "design",
                        "capability_kind": child_kind,
                        "capability_id": child_id,
                        **child_definition,
                    }
                )
            continue
        protected_error = _protected_call_blocker_reason(
            call,
            call_aliases,
            flow_callable,
        )
        if protected_error is not None:
            dispositions[id(call)] = "blocker"
            blockers.append(
                _review_blocker(
                    item_id,
                    relative_path,
                    call,
                    protected_error,
                )
            )
            continue
        call_definition = _call_definition(
            call,
            call_aliases,
            flow_callable,
        )
        if call_definition is not None:
            count_key = _semantic_bytes(
                {
                    key: value
                    for key, value in call_definition.items()
                    if key != "maximum_calls"
                }
            )
            call_definitions[id(call)] = count_key
            call_definition_rows[count_key] = call_definition
            call_nodes.setdefault(count_key, call)
    call_counts, dynamic_call_keys = _runtime_call_bounds(
        node.body,
        call_definitions,
        assignments=assignments,
        relative_path=relative_path,
        aliases=body_aliases,
        helper_registry=helper_registry,
        analysis_budget=analysis_budget,
    )
    for count_key in sorted(dynamic_call_keys):
        for call_id, supplied_key in call_definitions.items():
            if supplied_key == count_key:
                dispositions[call_id] = "blocker"
        blockers.append(
            _review_blocker(
                item_id,
                relative_path,
                call_nodes[count_key],
                "dynamic repetition prevents a finite call bound",
            )
        )
    for count_key, maximum_calls in call_counts.items():
        if count_key in dynamic_call_keys or maximum_calls == 0:
            if maximum_calls == 0:
                for call_id, supplied_key in call_definitions.items():
                    if supplied_key == count_key:
                        dispositions[call_id] = "proved_unreachable"
            continue
        definition = call_definition_rows[count_key]
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
        for call_id, supplied_key in call_definitions.items():
            if supplied_key == count_key:
                dispositions[call_id] = "row"
    uncensused_resolved = resolved_sensitive_calls - sensitive_calls
    if uncensused_resolved:
        missing = min(
            (
                call
                for call in execution.calls
                if id(call) in uncensused_resolved
            ),
            key=lambda call: (
                int(getattr(call, "lineno", 0)),
                int(getattr(call, "col_offset", 0)),
            ),
        )
        raise InventoryError(
            "resolved sensitive site is absent from the independent census: "
            f"{relative_path}:{int(getattr(missing, 'lineno', 0))}"
        )
    missing_dispositions = sensitive_calls - dispositions.keys()
    if missing_dispositions:
        missing = min(
            (
                call
                for call in execution.calls
                if id(call) in missing_dispositions
            ),
            key=lambda call: (
                int(getattr(call, "lineno", 0)),
                int(getattr(call, "col_offset", 0)),
            ),
        )
        raise InventoryError(
            "sensitive census site lacks a review row, blocker, or proved "
            f"unreachable record: {relative_path}:"
            f"{int(getattr(missing, 'lineno', 0))}"
        )
    return rows, blockers


_IMPORT_TIME_CLASS_PROTOCOL_REASONS = frozenset({
    "implicit class-base adaptation is dynamically unresolved",
    "implicit class subscription is dynamically unresolved",
    "implicit descriptor installation is dynamically unresolved",
    "implicit metaclass construction is dynamically unresolved",
    "implicit subclass initialization is dynamically unresolved",
    "protected namespace member mutation is dynamically unresolved",
})


def _definition_time_protocol_resolver(
    relative_path: str,
    tree: ast.Module,
    aliases: Mapping[str, str],
    module_assignments: Mapping[str, ast.expr],
) -> _SourceOrderedResolver:
    """Run the bounded source-order resolver over eager module statements."""

    budget = _AnalysisBudget()
    resolver = _SourceOrderedResolver(
        aliases,
        {},
        {},
        budget=budget,
        exception_scope=_exception_name_scope(None, aliases.keys()),
        module_bound_names=aliases.keys(),
    )
    # The expressions are needed only for closure sensitivity.  Installing
    # them as entry values would violate module source order.
    resolver.module_assignments = dict(module_assignments)
    resolver.resolve(tree.body)
    return resolver


def _definition_time_protocol_blockers(
    relative_path: str,
    tree: ast.Module,
    aliases: Mapping[str, str],
    module_assignments: Mapping[str, ast.expr],
    resolver: _SourceOrderedResolver | None = None,
) -> list[dict[str, object]]:
    if resolver is None:
        resolver = _definition_time_protocol_resolver(
            relative_path,
            tree,
            aliases,
            module_assignments,
        )
    return [
        _review_blocker(
            "unowned:import-time",
            relative_path,
            target,
            f"import-time {reason}",
        )
        for target, reason in resolver.flow.standalone_blockers
        if reason in _IMPORT_TIME_CLASS_PROTOCOL_REASONS
    ]


def _module_protected_namespace_mutations(
    relative_path: str,
    tree: ast.Module,
    aliases: Mapping[str, str],
    module_assignments: Mapping[str, ast.expr],
    resolver: _SourceOrderedResolver | None = None,
) -> frozenset[str]:
    if resolver is None:
        resolver = _definition_time_protocol_resolver(
            relative_path,
            tree,
            aliases,
            module_assignments,
        )
    return frozenset(
        qualified
        for qualified in _PROTECTED_NAMESPACE_MEMBERS
        if qualified in resolver.values
        and _flow_is_sensitive(resolver.values[qualified])
    )


def _definition_time_blockers(
    relative_path: str,
    tree: ast.Module,
    aliases: Mapping[str, str],
    module_assignments: Mapping[str, ast.expr],
    helper_registry: Mapping[str, _ReviewFunction],
    protocol_resolver: _SourceOrderedResolver | None = None,
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
                    module_bound_names=definition.module_bound_names,
                    enclosing_exception_names=(
                        definition.enclosing_exception_names
                    ),
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
    blockers.extend(
        _definition_time_protocol_blockers(
            relative_path,
            tree,
            aliases,
            module_assignments,
            protocol_resolver,
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
            _checked_cardinality_add(
                int(row["maximum_calls"]),
                0 if previous is None else previous[1],
            ),
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


def _unittest_entry_signature_is_valid(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> bool:
    arguments = node.args
    positional = [*arguments.posonlyargs, *arguments.args]
    if not positional and arguments.vararg is None:
        return False
    defaults = len(arguments.defaults)
    required_positional = len(positional) - defaults
    if positional:
        required_after_bound_instance = max(0, required_positional - 1)
        if required_after_bound_instance:
            return False
    if any(default is None for default in arguments.kw_defaults):
        return False
    return True


def _unittest_parameter_entry_values(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> dict[str, _FlowValue]:
    parameters = [
        *node.args.posonlyargs,
        *node.args.args,
        *node.args.kwonlyargs,
    ]
    if node.args.vararg is not None:
        parameters.append(node.args.vararg)
    if node.args.kwarg is not None:
        parameters.append(node.args.kwarg)
    return {
        parameter.arg: _flow_unknown(
            "unittest entry parameter is dynamically unresolved"
        )
        for parameter in parameters
    }


def _identity_decorator_definition(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> bool:
    if not isinstance(node, ast.FunctionDef) or node.decorator_list:
        return False
    arguments = node.args
    positional = [*arguments.posonlyargs, *arguments.args]
    annotations = [
        argument.annotation
        for argument in (
            *arguments.posonlyargs,
            *arguments.args,
            *arguments.kwonlyargs,
        )
    ]
    if arguments.vararg is not None:
        annotations.append(arguments.vararg.annotation)
    if arguments.kwarg is not None:
        annotations.append(arguments.kwarg.annotation)
    return (
        len(positional) == 1
        and not arguments.defaults
        and arguments.vararg is None
        and arguments.kwarg is None
        and not arguments.kwonlyargs
        and not arguments.kw_defaults
        and node.returns is None
        and not any(annotation is not None for annotation in annotations)
        and not getattr(node, "type_params", ())
        and len(node.body) == 1
        and isinstance(node.body[0], ast.Return)
        and isinstance(node.body[0].value, ast.Name)
        and node.body[0].value.id == positional[0].arg
    )


def _identity_test_decorator(
    decorator: ast.expr,
    *,
    relative_path: str,
    aliases: Mapping[str, str],
    assignments: Mapping[str, ast.expr],
    helper_registry: Mapping[str, _ReviewFunction],
    budget: _AnalysisBudget,
) -> bool:
    resolved_decorator = _resolved_entry_assignment(
        decorator,
        assignments,
        budget,
    )
    if resolved_decorator is None:
        return False
    decorator = resolved_decorator
    if isinstance(decorator, ast.Call):
        return False
    raw = _qualified_name(decorator)
    resolved = _resolved_qualified_name(decorator, aliases)
    candidates = []
    if raw is not None and "." not in raw:
        candidates.append(f"{relative_path}::{raw}")
    if resolved is not None:
        candidates.append(resolved)
        if "." not in resolved:
            candidates.append(f"{relative_path}::{resolved}")
    for key in candidates:
        definition = helper_registry.get(key)
        if definition is None:
            continue
        if _identity_decorator_definition(definition.node):
            return True
    return False


def _resolved_entry_assignment(
    expression: ast.expr,
    assignments: Mapping[str, ast.expr],
    budget: _AnalysisBudget,
) -> ast.expr | None:
    seen: set[str] = set()
    current = expression
    while isinstance(current, ast.Name) and current.id in assignments:
        budget.consume()
        if current.id in seen:
            return None
        seen.add(current.id)
        current = assignments[current.id]
    return current


def _entry_expression_is_proven_safe(
    expression: ast.expr,
    aliases: Mapping[str, str],
    assignments: Mapping[str, ast.expr],
    *,
    relative_path: str,
    helper_registry: Mapping[str, _ReviewFunction],
    budget: _AnalysisBudget,
) -> bool:
    resolved_expression = _resolved_entry_assignment(
        expression,
        assignments,
        budget,
    )
    if resolved_expression is None:
        return False
    expression = resolved_expression
    try:
        ast.literal_eval(expression)
    except (ValueError, TypeError, SyntaxError, MemoryError, RecursionError):
        pass
    else:
        return True
    raw = _qualified_name(expression)
    qualified = _resolved_qualified_name(expression, aliases)
    helper_keys: list[str] = []
    if raw is not None and "." not in raw:
        helper_keys.append(f"{relative_path}::{raw}")
    if qualified is not None:
        helper_keys.append(qualified)
        if "." not in qualified:
            helper_keys.append(f"{relative_path}::{qualified}")
    for key in helper_keys:
        definition = helper_registry.get(key)
        if definition is not None:
            return not _helper_has_sensitive_closure(
                definition,
                helper_registry,
                budget=budget,
                active=frozenset({key}),
            )
    if isinstance(expression, ast.Call):
        callable_name = _resolved_qualified_name(expression.func, aliases)
        return (
            callable_name in _SAFE_MOCK_FACTORIES
            and not any(isinstance(argument, ast.Starred) for argument in expression.args)
            and not any(keyword.arg is None for keyword in expression.keywords)
        )
    return False


def _entry_expression_is_protected_binding(
    expression: ast.expr,
    aliases: Mapping[str, str],
    assignments: Mapping[str, ast.expr],
    seen: frozenset[str] = frozenset(),
) -> bool:
    qualified = _resolved_qualified_name(expression, aliases)
    if qualified is not None and (
        qualified in _SUBPROCESS_FUNCTIONS
        or _is_sensitive_namespace(qualified)
    ):
        return True
    if (
        isinstance(expression, ast.Name)
        and expression.id in assignments
        and expression.id not in seen
    ):
        return _entry_expression_is_protected_binding(
            assignments[expression.id],
            aliases,
            assignments,
            seen | {expression.id},
        )
    return False


def _unittest_receiver_attributes(
    method: ast.FunctionDef | ast.AsyncFunctionDef,
    aliases: Mapping[str, str],
    module_assignments: Mapping[str, ast.expr],
    budget: _AnalysisBudget,
) -> tuple[ast.Attribute, ...]:
    positional = [*method.args.posonlyargs, *method.args.args]
    if not positional:
        return ()
    execution = _execution_scope(method, budget)
    module_bound_names = frozenset(aliases) | frozenset(module_assignments)
    resolver = _SourceOrderedResolver(
        aliases,
        {},
        execution.local_functions,
        budget=budget,
        exception_scope=_exception_name_scope(
            method,
            module_bound_names,
        ),
        lexical_scope=_lexical_binding_scope(method),
        module_bound_names=module_bound_names,
        entry_values={
            positional[0].arg: _FlowValue("unittest_receiver"),
        },
    )
    resolver.resolve(method.body)
    return tuple(resolver.flow.receiver_attributes.values())


def _unittest_entry_preflight(
    method: ast.FunctionDef | ast.AsyncFunctionDef,
    case: ast.ClassDef,
    *,
    relative_path: str,
    aliases: Mapping[str, str],
    module_assignments: Mapping[str, ast.expr],
    helper_registry: Mapping[str, _ReviewFunction],
    budget: _AnalysisBudget,
) -> tuple[list[tuple[ast.AST, str]], bool]:
    refused: list[tuple[ast.AST, str]] = []
    for decorator in case.decorator_list:
        target = decorator.func if isinstance(decorator, ast.Call) else decorator
        qualified = _resolved_qualified_name(target, aliases)
        if qualified in {
            "unittest.skip",
            "unittest.skipIf",
            "unittest.skipUnless",
        }:
            continue
        if _identity_test_decorator(
            decorator,
            relative_path=relative_path,
            aliases=aliases,
            assignments=module_assignments,
            helper_registry=helper_registry,
            budget=budget,
        ):
            continue
        refused.append((
            decorator,
            "custom unittest class decorator runtime target is dynamically unresolved",
        ))
        return refused, True

    entry_assignments = dict(module_assignments)
    entry_assignments.update(_static_assignments_before(case.body, method))
    for decorator in method.decorator_list:
        target = decorator.func if isinstance(decorator, ast.Call) else decorator
        qualified = _resolved_qualified_name(target, aliases)
        if qualified in {"unittest.skipIf", "unittest.skipUnless"}:
            continue
        if _identity_test_decorator(
            decorator,
            relative_path=relative_path,
            aliases=aliases,
            assignments=entry_assignments,
            helper_registry=helper_registry,
            budget=budget,
        ):
            continue
        refused.append((
            decorator,
            "custom test decorator runtime target is dynamically unresolved",
        ))
        return refused, True

    if not _unittest_entry_signature_is_valid(method):
        refused.append((
            method,
            "unittest entry signature is dynamically unresolved",
        ))
        return refused, True

    positional = [*method.args.posonlyargs, *method.args.args]
    default_parameters = {
        parameter.arg: default
        for parameter, default in zip(
            positional[-len(method.args.defaults) :] if method.args.defaults else (),
            method.args.defaults,
            strict=True,
        )
    }
    default_parameters.update({
        parameter.arg: default
        for parameter, default in zip(
            method.args.kwonlyargs,
            method.args.kw_defaults,
            strict=True,
        )
        if default is not None
    })
    loaded_names = {
        candidate.id
        for candidate in _metered_ast_walk(method, budget)
        if isinstance(candidate, ast.Name)
        and isinstance(candidate.ctx, ast.Load)
    }
    for parameter, default in default_parameters.items():
        if (
            parameter in loaded_names
            and not _entry_expression_is_proven_safe(
                default,
                aliases,
                entry_assignments,
                relative_path=relative_path,
                helper_registry=helper_registry,
                budget=budget,
            )
        ):
            refused.append((
                default,
                "unittest default argument binding is dynamically unresolved",
            ))

    class_assignments = _static_assignments(case.body)
    class_properties = {
        statement.name: _implicit_method_is_sensitive(
            statement,
            aliases,
            module_assignments,
            budget,
        )
        for statement in case.body
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef))
        and any(
            _resolved_qualified_name(decorator, aliases) == "property"
            for decorator in statement.decorator_list
        )
    }
    fixture_mutations: dict[str, bool] = {}
    for fixture in case.body:
        if not isinstance(fixture, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if fixture.name not in {"setUp", "setUpClass"}:
            continue
        for candidate in _metered_ast_walk(fixture, budget):
            targets: Sequence[ast.expr] = ()
            if isinstance(candidate, ast.Assign):
                targets = candidate.targets
            elif isinstance(candidate, ast.AnnAssign):
                targets = (candidate.target,)
            elif isinstance(candidate, ast.AugAssign):
                targets = (candidate.target,)
            for target in targets:
                if (
                    isinstance(target, ast.Attribute)
                    and isinstance(target.value, ast.Name)
                    and target.value.id in {"self", "cls"}
                ):
                    fixture_mutations[target.attr] = (
                        fixture_mutations.get(target.attr, False)
                        or (
                            candidate.value is not None
                            and _entry_expression_is_protected_binding(
                                candidate.value,
                                aliases,
                                module_assignments,
                            )
                        )
                    )
    seen_attributes: set[str] = set()
    for candidate in _unittest_receiver_attributes(
        method,
        aliases,
        module_assignments,
        budget,
    ):
        if candidate.attr in seen_attributes:
            continue
        seen_attributes.add(candidate.attr)
        if fixture_mutations.get(candidate.attr, False) or class_properties.get(
            candidate.attr,
            False,
        ):
            refused.append((
                candidate,
                "unittest instance or class binding is dynamically unresolved",
            ))
            continue
        class_value = class_assignments.get(candidate.attr)
        if class_value is not None and not _entry_expression_is_proven_safe(
            class_value,
            aliases,
            {**module_assignments, **class_assignments},
            relative_path=relative_path,
            helper_registry=helper_registry,
            budget=budget,
        ):
            refused.append((
                candidate,
                "unittest instance or class binding is dynamically unresolved",
            ))
    return refused, False


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
        if not isinstance(entry, Mapping):
            raise InventoryError("inventory item is invalid for design derivation")
        assignment = entry.get("assignment")
        exclusion = entry.get("exclusion")
        stable_id = str(entry.get("stable_id"))
        if isinstance(assignment, Mapping):
            expectation = assignment.get("expectation")
            if not isinstance(expectation, Mapping):
                raise InventoryError(
                    "inventory expectation is invalid for design derivation"
                )
            expectations[stable_id] = str(expectation.get("kind"))
            if assignment.get("profile_name") != "historical":
                design_items.add(stable_id)
        elif isinstance(exclusion, Mapping):
            expectations[stable_id] = "excluded"
            design_items.add(stable_id)
        else:
            raise InventoryError(
                "inventory item has no assignment or exclusion for design derivation"
            )
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
    exception_provenance = {
        relative_path: _module_exception_provenance(tree)
        for relative_path, tree in parsed.items()
    }
    module_aliases_by_path = {
        relative_path: _module_import_aliases(tree)
        for relative_path, tree in parsed.items()
    }
    module_assignments_by_path = {
        relative_path: _static_assignments(tree.body)
        for relative_path, tree in parsed.items()
    }
    definition_time_protocol_resolvers = {
        relative_path: _definition_time_protocol_resolver(
            relative_path,
            tree,
            module_aliases_by_path[relative_path],
            module_assignments_by_path[relative_path],
        )
        for relative_path, tree in parsed.items()
    }
    protected_namespace_mutations = {
        relative_path: _module_protected_namespace_mutations(
            relative_path,
            tree,
            module_aliases_by_path[relative_path],
            module_assignments_by_path[relative_path],
            definition_time_protocol_resolvers[relative_path],
        )
        for relative_path, tree in parsed.items()
    }
    helper_registry = _review_function_registry(
        parsed,
        exception_provenance,
        protected_namespace_mutations,
    )
    rows: list[dict[str, object]] = []
    blockers: list[dict[str, object]] = []
    analyzed_sites: list[dict[str, object]] = []
    helper_edges: list[dict[str, object]] = []
    for relative_path, tree in parsed.items():
        blockers.extend(
            _definition_time_blockers(
                relative_path,
                tree,
                module_aliases_by_path[relative_path],
                module_assignments_by_path[relative_path],
                helper_registry,
                definition_time_protocol_resolvers[relative_path],
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
            module_bound_names=definition.module_bound_names,
            enclosing_exception_names=definition.enclosing_exception_names,
            analyzed_sites=analyzed_sites,
            helper_edges=helper_edges,
        )
        rows.extend(added)
        blockers.extend(refused)
    for relative_path, tree in parsed.items():
        aliases = dict(module_aliases_by_path[relative_path])
        aliases.update({
            qualified: _PROTECTED_MUTATION_ALIAS
            for qualified in protected_namespace_mutations[relative_path]
        })
        module_assignments = module_assignments_by_path[relative_path]
        provenance = exception_provenance[relative_path]
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
                    module_bound_names=provenance.module_bound_names,
                    enclosing_exception_names=(
                        provenance.enclosing_names_by_node.get(
                            id(function),
                            frozenset(),
                        )
                    ),
                    analyzed_sites=analyzed_sites,
                    helper_edges=helper_edges,
                )
                rows.extend(added)
                blockers.extend(refused)
        for case in _supported_unittest_case_nodes(
            relative_path,
            tree,
            enforce_runtime_discovery=False,
        ):
            entry_aliases = _module_import_aliases(
                tree,
                stop_before=case,
            )
            entry_aliases.update({
                qualified: _PROTECTED_MUTATION_ALIAS
                for qualified in protected_namespace_mutations[relative_path]
            })
            entry_module_assignments = _static_assignments_before(
                tree.body,
                case,
            )
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
                        module_bound_names=provenance.module_bound_names,
                        enclosing_exception_names=(
                            provenance.enclosing_names_by_node.get(
                                id(function),
                                frozenset(),
                            )
                        ),
                        analyzed_sites=analyzed_sites,
                        helper_edges=helper_edges,
                    )
                    rows.extend(added)
                    blockers.extend(refused)
            per_test_hooks = tuple(
                node
                for node in case.body
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name in {"setUp", "tearDown"}
            )
            per_test_names = [hook.name for hook in per_test_hooks]
            if len(per_test_names) != len(set(per_test_names)):
                raise InventoryError(
                    "duplicate per-test fixture definitions are ambiguous: "
                    f"{relative_path}::{case.name}"
                )
            for method in (
                node
                for node in case.body
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name.startswith("test_")
            ):
                stable_id = f"{relative_path}::{case.name}::{method.name}"
                if stable_id not in design_items or stable_id not in reviewed_items:
                    continue
                if expectations.get(stable_id) in {
                    "declared_unconditional_skip", "excluded",
                }:
                    continue
                for hook in per_test_hooks:
                    added, refused = _review_body(
                        hook,
                        item_id=stable_id,
                        relative_path=relative_path,
                        aliases=aliases,
                        module_assignments=module_assignments,
                        class_name=case.name,
                        helper_registry=helper_registry,
                        module_bound_names=provenance.module_bound_names,
                        enclosing_exception_names=(
                            provenance.enclosing_names_by_node.get(
                                id(hook),
                                frozenset(),
                            )
                        ),
                        analyzed_sites=analyzed_sites,
                        helper_edges=helper_edges,
                    )
                    rows.extend(added)
                    blockers.extend(refused)
                entry_refused, skip_original_body = _unittest_entry_preflight(
                    method,
                    case,
                    relative_path=relative_path,
                    aliases=entry_aliases,
                    module_assignments=entry_module_assignments,
                    helper_registry=helper_registry,
                    budget=_AnalysisBudget(),
                )
                blockers.extend(
                    _review_blocker(
                        stable_id,
                        relative_path,
                        target,
                        reason,
                    )
                    for target, reason in entry_refused
                )
                if skip_original_body:
                    continue
                added, refused = _review_body(
                    method,
                    item_id=stable_id,
                    relative_path=relative_path,
                    aliases=aliases,
                    module_assignments=module_assignments,
                    class_name=case.name,
                    helper_registry=helper_registry,
                    module_bound_names=provenance.module_bound_names,
                    enclosing_exception_names=(
                        provenance.enclosing_names_by_node.get(
                            id(method),
                            frozenset(),
                        )
                    ),
                    analyzed_sites=analyzed_sites,
                    helper_edges=helper_edges,
                    entry_values=_unittest_parameter_entry_values(method),
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
        if isinstance(entry, Mapping)
        and isinstance(entry.get("assignment"), Mapping)
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
            # Anchor f-string constants to the JoinedStr's own start line:
            # CPython <= 3.11 stamps every part with that line while 3.12+
            # records true part positions, so the anchor is the only
            # location both interpreters report identically.
            anchored_line = (
                int(parent.lineno)
                if isinstance(parent, ast.JoinedStr)
                else int(node.lineno)
            )
            rows_with_provenance.append(({
                "path": relative_path,
                "line": anchored_line,
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

    def revalidate_derivation_inputs(self) -> None:
        self.inventory_snapshot.revalidate()
        self.working_snapshot.revalidate()


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


def _derive_design_review_publication(
    derivation: _GovernanceDesignReviewPublication,
) -> _GovernanceSinglePublication:
    captured = _capture_design_inputs(
        derivation.repository_root,
        include_profile=False,
    )
    if derivation.enforce_repository_lock:
        _validate_locked_inventory_snapshot(captured)
    review = _derive_captured_design_review(captured)

    def lifetime_check() -> None:
        captured.revalidate()

    lifetime_check()
    return _GovernanceSinglePublication(
        canonical_json_bytes(review) + b"\n",
        value=review,
        lifetime_check=lifetime_check,
        post_publish_lifetime_check=lambda _snapshot: lifetime_check(),
    )


def emit_design_review(
    repository_root: Path,
    destination: Path,
    *,
    enforce_repository_lock: bool = False,
) -> dict[str, object]:
    root = Path(os.path.abspath(repository_root))

    configured_git = os.environ.get("PONTIUS_GIT")
    if enforce_repository_lock and configured_git is None:
        raise InventoryError("PONTIUS_GIT is required for design review publication")
    result = _with_governance_attribute_lease(
        root,
        Path(configured_git) if enforce_repository_lock else None,
        _GovernancePublicationOperation(
            (destination,),
            _GovernanceDesignReviewPublication(
                root,
                enforce_repository_lock,
            ),
        ),
    )
    if not isinstance(result, dict):
        raise InventoryError("design review publication result is invalid")
    return result


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


def _derive_design_capabilities_publication(
    derivation: _GovernanceDesignCapabilitiesPublication,
) -> _GovernanceSinglePublication:
    root = derivation.repository_root
    profile_path = root / "tests" / "test-profiles.toml"
    captured = _capture_design_inputs(root, include_profile=True)
    if derivation.enforce_repository_lock:
        _validate_locked_inventory_snapshot(captured)
    review = _derive_captured_design_review(captured)
    rows = validate_design_approval(
        review,
        derivation.approved_spec_capabilities_sha256,
        derivation.approved_design_review_receipt_sha256,
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

    def validate_published_profile(snapshot: object) -> None:
        captured.revalidate_derivation_inputs()
        if snapshot.path != profile_path or snapshot.raw != updated:
            raise InventoryError("published profile snapshot is not exact")
        snapshot.revalidate()

    captured.revalidate()
    return _GovernanceSinglePublication(
        updated,
        value=None,
        expected_identity=captured.profile_snapshot.identity,
        expected_raw=captured.profile_snapshot.raw,
        lifetime_check=captured.revalidate,
        post_publish_lifetime_check=validate_published_profile,
    )


def write_design_capabilities(
    repository_root: Path,
    *,
    approved_spec_capabilities_sha256: str,
    approved_design_review_receipt_sha256: str,
    enforce_repository_lock: bool = False,
) -> None:
    root = Path(os.path.abspath(repository_root))
    profile_path = root / "tests" / "test-profiles.toml"

    configured_git = os.environ.get("PONTIUS_GIT")
    if enforce_repository_lock and configured_git is None:
        raise InventoryError("PONTIUS_GIT is required for design publication")
    _with_governance_attribute_lease(
        root,
        Path(configured_git) if enforce_repository_lock else None,
        _GovernancePublicationOperation(
            (profile_path,),
            _GovernanceDesignCapabilitiesPublication(
                root,
                approved_spec_capabilities_sha256,
                approved_design_review_receipt_sha256,
                enforce_repository_lock,
            ),
        ),
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


def _derive_inventory_publication(
    derivation: _GovernanceInventoryPublication,
) -> _GovernancePairPublication:
    repository_root = derivation.repository_root
    configured_git = derivation.git_path
    inventory_path = repository_root / "tests" / "test-inventory.json"
    profile_path = repository_root / "tests" / "test-profiles.toml"
    baseline_sources = _baseline_sources(repository_root, configured_git)
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
        baseline_sources,
        working_sources,
        enforce_baseline_lock=True,
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

    def lifetime_check() -> None:
        working_snapshot.revalidate()

    return _GovernancePairPublication(
        inventory_raw,
        profile_raw,
        value=None,
        lifetime_check=lifetime_check,
    )


def main(argv: Sequence[str] | None = None) -> int:
    arguments = parse_arguments(argv)
    repository_root = Path(os.path.abspath(__file__)).parents[1]
    inventory_path = repository_root / "tests" / "test-inventory.json"
    profile_path = repository_root / "tests" / "test-profiles.toml"
    try:
        if arguments.emit_design_capability_review is not None:
            destination = arguments.emit_design_capability_review
            destination_parent = Path(os.path.abspath(destination.parent))
            temporary_root = Path(os.path.abspath(tempfile.gettempdir()))
            if (
                not destination.is_absolute()
                or os.path.normcase(str(destination_parent))
                != os.path.normcase(str(temporary_root))
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

        def generate_and_maybe_publish() -> _GovernancePairPublication | None:
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
                def lifetime_check() -> None:
                    working_snapshot.revalidate()

                return _GovernancePairPublication(
                    inventory_raw,
                    profile_raw,
                    value=None,
                    lifetime_check=lifetime_check,
                )
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
            return None

        if arguments.write:
            _with_governance_attribute_lease(
                repository_root,
                Path(configured_git),
                _GovernancePublicationOperation(
                    (inventory_path, profile_path),
                    _GovernanceInventoryPublication(
                        repository_root,
                        Path(configured_git),
                    ),
                ),
            )
        else:
            generate_and_maybe_publish()
    except (InventoryError, OSError, ValueError) as error:
        print(f"test inventory generation failed: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
