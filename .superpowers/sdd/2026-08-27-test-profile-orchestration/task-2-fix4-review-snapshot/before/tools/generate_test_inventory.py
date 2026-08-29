"""Generate and verify the immutable test ownership and profile lock."""

from __future__ import annotations

import argparse
import ast
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
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
    ancestor_handles: tuple[int, ...] = ()
    ancestor_chain: tuple[tuple[Path, tuple[int, ...]], ...] = ()
    snapshot_sha256: str | None = None

    def close(self) -> None:
        failures: list[BaseException] = []
        try:
            os.close(self.descriptor)
        except BaseException as error:
            failures.append(error)
        for handle in reversed(self.ancestor_handles):
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
        return None
    supplied = _qualified_name(node)
    if supplied is None:
        return None
    first, separator, remainder = supplied.partition(".")
    resolved = bindings.get(first, first)
    return f"{resolved}.{remainder}" if separator else resolved


def _conditional_skip_aliases(
    nodes: Iterable[ast.stmt],
    inherited: Mapping[str, str] | None = None,
) -> dict[str, str]:
    aliases = dict(inherited or {})
    for node in nodes:
        if isinstance(node, ast.If):
            first = _conditional_skip_aliases(node.body, aliases)
            second = _conditional_skip_aliases(node.orelse, aliases)
            aliases = {
                name: first[name]
                for name in set(first) & set(second)
                if first[name] == second[name]
            }
            continue
        if isinstance(node, ast.Import):
            for imported in node.names:
                if imported.name == "unittest":
                    aliases[imported.asname or "unittest"] = "unittest"
        elif isinstance(node, ast.ImportFrom) and node.module == "unittest":
            for imported in node.names:
                if imported.name in {"skipIf", "skipUnless"}:
                    aliases[imported.asname or imported.name] = (
                        f"unittest.{imported.name}"
                    )
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
            if resolved is not None:
                aliases[target.id] = resolved
            else:
                aliases.pop(target.id, None)
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


def _platform_condition_values(node: ast.expr) -> dict[str, bool] | None:
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        inner = _platform_condition_values(node.operand)
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
        and node.left.value.id == "os"
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
        values = _platform_condition_values(decorator.args[0])
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
    for relative_path in sorted(normalized_sources):
        raw = normalized_sources[relative_path]
        try:
            tree = ast.parse(raw.decode("utf-8", errors="strict"), filename=relative_path)
        except (UnicodeDecodeError, SyntaxError) as error:
            raise InventoryError(f"test source cannot be parsed: {relative_path}") from error
        conditional_aliases = _conditional_skip_aliases(tree.body)
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
        for class_node in (node for node in tree.body if isinstance(node, ast.ClassDef)):
            if not any(_is_test_case_base(base) for base in class_node.bases):
                continue
            if len(class_node.bases) != 1:
                raise InventoryError(
                    "inherited or mixin fixture ownership is unsupported: "
                    f"{relative_path}::{class_node.name}"
                )
            class_conditional_aliases = _conditional_skip_aliases(
                class_node.body,
                conditional_aliases,
            )
            class_platforms = _decorator_platforms(
                class_node.decorator_list,
                conditional_aliases,
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
            for node in class_node.body:
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                if node.name in {"setUpClass", "tearDownClass"}:
                    class_fixture_names.append(node.name)
                if node.name in {"setUp", "tearDown"}:
                    per_test_fixture_names.append(node.name)
                if not node.name.startswith("test_"):
                    continue
                method_platforms = _decorator_platforms(
                    node.decorator_list,
                    class_conditional_aliases,
                )
                applicable_platforms = tuple(
                    sorted(set(class_platforms) & set(method_platforms))
                )
                if not applicable_platforms:
                    raise InventoryError(
                        "conditional skip excludes every supported platform"
                    )
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
        chain.append((ancestor, secure_filesystem._directory_identity(info)))
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
            or secure_filesystem._directory_identity(info) != expected
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
) -> tuple[
    tuple[int, ...],
    tuple[tuple[Path, tuple[int, ...]], ...],
]:
    chain = _git_ancestor_chain(path)
    create, _, _, _ = secure_filesystem._windows_directory_api()
    handles: list[int] = []
    try:
        for ancestor, expected in chain:
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
            handles.append(numeric)
            volume, file_id = secure_filesystem._windows_directory_handle_identity(
                numeric,
                ancestor,
            )
            if (volume, int.from_bytes(file_id, "little")) != expected[:2]:
                raise InventoryError("PONTIUS_GIT ancestor handle identity differs")
        _revalidate_git_ancestor_chain(chain)
        return tuple(handles), chain
    except BaseException as error:
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
    before = _git_path_stat(path)
    if _git_stat_identity(before) != expected_identity:
        raise InventoryError("PONTIUS_GIT changed before launch lease acquisition")
    descriptor: int | None = None
    ancestor_handles: tuple[int, ...] = ()
    try:
        if os.name == "nt":
            ancestor_handles, ancestor_chain = (
                _windows_git_ancestor_handles(path)
            )
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
            snapshot_sha256 = None
        else:
            ancestor_chain = ()
            raw = _read_git_bytes(path, before)
            if expected_raw is not None and raw != expected_raw:
                raise InventoryError("PONTIUS_GIT bytes changed before snapshot")
            descriptor, launch_executable = _posix_executable_snapshot(
                raw,
                before.st_mode,
            )
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
        return _GitLaunchLease(
            path,
            expected_identity,
            descriptor,
            launch_executable,
            pass_fds,
            ancestor_handles,
            ancestor_chain,
            snapshot_sha256,
        )
    except BaseException as error:
        cleanup_failures: list[BaseException] = []
        if descriptor is not None:
            try:
                os.close(descriptor)
            except BaseException as close_error:
                cleanup_failures.append(close_error)
        for handle in reversed(ancestor_handles):
            try:
                secure_filesystem._windows_close_directory(handle)
            except BaseException as close_error:
                cleanup_failures.append(close_error)
        if cleanup_failures:
            raise InventoryError(
                "PONTIUS_GIT launch lease and cleanup both failed"
            ) from ExceptionGroup(
                "PONTIUS_GIT launch lease failures",
                (error, *cleanup_failures),
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


def _with_governance_attribute_lease(
    repository_root: Path,
    git_path: Path,
    action: Any,
) -> object:
    git, raw_identity, identity = _strict_git_snapshot(git_path)
    lease = _acquire_git_launch_lease(git, identity, raw_identity)
    primary_failure: BaseException | None = None
    result: object | None = None
    transactions: list[object] = []
    previous_collector = _governance_transaction_collector()
    try:
        _GOVERNANCE_TRANSACTION_CONTEXT.collector = transactions
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
            _coordinate_governance_commit(
                tuple(transactions),
                lifetime_check=revalidate,
            )
    except BaseException as error:
        primary_failure = error
    finally:
        if previous_collector is None:
            try:
                del _GOVERNANCE_TRANSACTION_CONTEXT.collector
            except AttributeError:
                pass
        else:
            _GOVERNANCE_TRANSACTION_CONTEXT.collector = previous_collector
    if primary_failure is not None:
        rollback_failures: list[BaseException] = []
        for transaction in reversed(transactions):
            try:
                transaction.rollback()
            except BaseException as error:
                rollback_failures.append(error)
        close_failure: BaseException | None = None
        try:
            lease.close()
        except BaseException as error:
            close_failure = error
        failures = (primary_failure, *rollback_failures)
        if close_failure is not None:
            failures += (close_failure,)
        if len(failures) > 1:
            raise InventoryError(
                "governance attribute action and rollback both failed"
            ) from ExceptionGroup(
                "governance attribute action failures",
                failures,
            )
        raise failures[0]
    _best_effort_governance_close(lease.close)
    if isinstance(result, _GovernanceWriteTransaction):
        return result.snapshot
    if isinstance(result, _GovernancePairTransaction):
        return None
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


def _best_effort_governance_close(
    action: Any,
    *,
    retry_if_open: Any | None = None,
) -> None:
    """Release a handle after the governance commit point without failing it."""

    try:
        action()
    except BaseException:
        if retry_if_open is None:
            return
        try:
            should_retry = retry_if_open()
        except BaseException:
            return
        if not should_retry:
            return
        try:
            action()
        except BaseException:
            return


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
    recovery_deletion_armed: bool = False
    posix_exchange: bool = False
    published_handle: int | None = None


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
            _restore_finalized_governance(self)
            self._state = "rolled_back"
            return
        if self._state != "open":
            raise InventoryError("governance transaction state is invalid")
        self._rollback_action()
        self._state = "rolled_back"

    def finalize(self) -> None:
        if self._state != "open":
            raise InventoryError("governance transaction is no longer open")
        if not self._validated:
            self.revalidate()
        try:
            self._finalize_action()
        except BaseException as primary_failure:
            try:
                self._rollback_action()
            except BaseException as rollback_failure:
                raise InventoryError(
                    "governance finalization and rollback both failed"
                ) from ExceptionGroup(
                    "governance finalization failures",
                    (primary_failure, rollback_failure),
                )
            self._state = "rolled_back"
            raise primary_failure
        self._state = "finalized"


@dataclass(slots=True)
class _GovernancePairTransaction:
    transactions: tuple[_GovernanceWriteTransaction, ...]
    _lifetime_check: Any | None = None
    _state: str = "open"
    _validated: bool = False

    def revalidate(self) -> None:
        if self._state != "open":
            raise InventoryError("governance pair transaction is no longer open")
        if self._lifetime_check is not None:
            self._lifetime_check()
        for transaction in self.transactions:
            transaction.revalidate()
        if self._lifetime_check is not None:
            self._lifetime_check()
        self._validated = True

    def rollback(self) -> None:
        if self._state == "rolled_back":
            return
        failures: list[BaseException] = []
        for transaction in reversed(self.transactions):
            try:
                transaction.rollback()
            except BaseException as error:
                failures.append(error)
        self._state = "rolled_back"
        if failures:
            raise InventoryError("governance pair rollback failed") from ExceptionGroup(
                "governance pair rollback failures",
                tuple(failures),
            )

    def finalize(self) -> None:
        if self._state != "open":
            raise InventoryError("governance pair transaction is no longer open")
        if not self._validated:
            self.revalidate()
        finalized: list[_GovernanceWriteTransaction] = []
        try:
            for transaction in self.transactions:
                transaction.finalize()
                finalized.append(transaction)
        except BaseException as primary_failure:
            rollback_failures: list[BaseException] = []
            for transaction in reversed(self.transactions):
                try:
                    transaction.rollback()
                except BaseException as error:
                    rollback_failures.append(error)
            self._state = "rolled_back"
            if rollback_failures:
                raise InventoryError(
                    "governance pair finalization and rollback both failed"
                ) from ExceptionGroup(
                    "governance pair finalization failures",
                    (primary_failure, *rollback_failures),
                )
            raise primary_failure
        self._state = "finalized"


def _coordinate_governance_commit(
    transactions: Sequence[object],
    *,
    lifetime_check: Any | None = None,
) -> None:
    """Validate one logical publication and commit without a lease gap."""

    try:
        if lifetime_check is not None:
            lifetime_check()
        for transaction in transactions:
            transaction.revalidate()
        if lifetime_check is not None:
            lifetime_check()
        for transaction in transactions:
            transaction.finalize()
    except BaseException as primary_failure:
        rollback_failures: list[BaseException] = []
        for transaction in reversed(transactions):
            try:
                transaction.rollback()
            except BaseException as error:
                rollback_failures.append(error)
        if rollback_failures:
            raise InventoryError(
                "governance commit and rollback both failed"
            ) from ExceptionGroup(
                "governance commit failures",
                (primary_failure, *rollback_failures),
            )
        raise


_GOVERNANCE_TRANSACTION_CONTEXT = threading.local()


def _governance_transaction_collector() -> list[object] | None:
    return getattr(_GOVERNANCE_TRANSACTION_CONTEXT, "collector", None)


def _windows_open_relative_governance_file_raw(
    directory_handle: int,
    name: str,
    *,
    read_data: bool = False,
    share_write: bool = True,
    delete_access: bool = True,
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
    if (
        status != 0
        or int(status_block.Status) != 0
        or not handle.value
        or int(handle.value) == invalid
    ):
        raise InventoryError("governance destination lock could not be acquired")
    return int(handle.value)


def _windows_open_relative_governance_file(
    directory_handle: int,
    name: str,
) -> int:
    return _windows_open_relative_governance_file_raw(
        directory_handle,
        name,
        share_write=False,
    )


def _windows_read_relative_governance_file(
    directory_handle: int,
    name: str,
) -> tuple[tuple[int, int], bytes]:
    handle = _windows_open_relative_governance_file_raw(
        directory_handle,
        name,
        read_data=True,
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
        result = (_windows_governance_handle_file_id(handle), raw)
    except BaseException as error:
        primary_failure = error
    try:
        secure_filesystem._windows_close_file(handle)
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
) -> tuple[int, tuple[int, bytes]]:
    """Bind a publication directory for handle-relative operations."""

    create, _, _, close = secure_filesystem._windows_directory_api()
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
        identity = secure_filesystem._windows_directory_handle_identity(
            handle,
            path,
        )
        return handle, identity
    except BaseException as primary_failure:
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
) -> None:
    _require_governance_destination_identity(
        destination_path,
        expected_identity,
    )
    if windows:
        if expected_identity is not None:
            state.recovery_name = (
                f".{destination_name}.{uuid.uuid4().hex}.recovery"
            )
            outcome.recovery_path = destination_path.with_name(
                state.recovery_name
            )
            original_handle = _windows_open_relative_governance_file_raw(
                parent_handle,
                destination_name,
                share_write=True,
            )
            try:
                if _windows_governance_handle_file_id(
                    original_handle
                ) != expected_identity[:2]:
                    raise InventoryError(
                        "governance destination handle identity differs"
                    )
                _windows_link_governance_file(
                    original_handle,
                    parent_handle,
                    state.recovery_name,
                )
                state.displaced = True
                state.destination_handle = (
                    _windows_open_relative_governance_file(
                        parent_handle,
                        state.recovery_name,
                    )
                )
            finally:
                if original_handle is not None:
                    secure_filesystem._windows_close_file(original_handle)
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
            ) != recovery.identity[:2]:
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
    os.unlink(temporary_name, dir_fd=parent_handle)
    state.published = True
    outcome.published = True


def _write_posix_governance(
    path: Path,
    raw: bytes,
    chain: Sequence[tuple[Path, tuple[int, ...]]],
    expected_identity: tuple[int, ...] | None,
    expected_raw: bytes | None,
    outcome: _GovernanceWriteOutcome,
    lifetime_check: Any | None,
    post_publish_lifetime_check: Any | None,
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
    temporary_name = f".{path.name}.{uuid.uuid4().hex}.tmp"
    temporary: int | None = None
    publish_state = _GovernancePublishState()

    published_snapshot: object | None = None

    def close_resources() -> None:
        nonlocal directory, temporary
        failures: list[BaseException] = []
        if publish_state.destination_handle is not None:
            try:
                os.close(publish_state.destination_handle)
                publish_state.destination_handle = None
            except BaseException as error:
                failures.append(error)
        if temporary is not None:
            try:
                os.close(temporary)
                temporary = None
            except BaseException as error:
                failures.append(error)
        if directory is not None:
            try:
                os.close(directory)
                directory = None
            except BaseException as error:
                failures.append(error)
        if failures:
            raise InventoryError("governance handle cleanup failed") from ExceptionGroup(
                "governance handle cleanup failures",
                tuple(failures),
            )

    def staged_destination_is_current() -> None:
        if directory is None or temporary is None:
            raise InventoryError("governance transaction handles are absent")
        current = os.stat(
            path.name,
            dir_fd=directory,
            follow_symlinks=False,
        )
        staged = os.fstat(temporary)
        if (
            secure_filesystem._path_handle_identity(current)
            != secure_filesystem._path_handle_identity(staged)
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
                pass
        if temporary is not None and not publish_state.published:
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

    def revalidate_transaction() -> None:
        if directory is None or published_snapshot is None:
            raise InventoryError("governance transaction is incomplete")
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
                        os.unlink(publish_state.recovery_name, dir_fd=directory)
                    else:
                        os.replace(
                            publish_state.recovery_name,
                            path.name,
                            src_dir_fd=directory,
                            dst_dir_fd=directory,
                        )
                else:
                    os.unlink(path.name, dir_fd=directory)
                os.fsync(directory)
                publish_state.published = False
                publish_state.displaced = False
                publish_state.posix_exchange = False
                outcome.published = False
                outcome.snapshot = None
                outcome.recovery_path = None
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
        nonlocal directory, temporary
        if directory is None:
            raise InventoryError("governance finalization directory is absent")
        if publish_state.destination_handle is not None:
            try:
                os.close(publish_state.destination_handle)
            except BaseException as error:
                raise InventoryError(
                    "governance destination close failed before commit"
                ) from error
            publish_state.destination_handle = None
        if publish_state.recovery_name is not None:
            os.unlink(publish_state.recovery_name, dir_fd=directory)
            publish_state.recovery_name = None
            publish_state.displaced = False
            outcome.recovery_path = None
        committed_temporary = temporary
        temporary = None
        if committed_temporary is not None:
            _best_effort_governance_close(
                lambda: os.close(committed_temporary)
            )
        committed_directory = directory
        directory = None
        _best_effort_governance_close(
            lambda: os.close(committed_directory)
        )

    try:
        directory = os.open(path.parent, directory_flags)
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
            expected_raw=expected_raw,
            state=publish_state,
            outcome=outcome,
        )
        os.fsync(directory)
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
) -> _GovernanceWriteTransaction:
    directory: int | None = None
    directory_lock: object | None = None
    temporary: object | None = None
    staged_snapshot: object | None = None
    published_snapshot: object | None = None
    bound_identity: tuple[int, bytes] | None = None
    publish_state = _GovernancePublishState()

    def close_raw_handle(handle: int, label: str) -> None:
        try:
            secure_filesystem._windows_close_file(handle)
        except BaseException as close_error:
            try:
                remains_open = _windows_governance_handle_is_open(handle)
            except BaseException as state_error:
                raise InventoryError(
                    f"{label} close outcome is unavailable"
                ) from ExceptionGroup(
                    f"{label} close failures",
                    (close_error, state_error),
                )
            if remains_open:
                raise InventoryError(
                    f"{label} close failed before close"
                ) from close_error

    def close_owner(owner: object, label: str) -> None:
        if owner.handle is None:
            owner.state = "closed"
            return
        handle = owner.handle
        close_raw_handle(handle, label)
        owner.handle = None
        owner.state = "closed"

    def close_published_handle() -> None:
        if publish_state.published_handle is None:
            return
        handle = publish_state.published_handle
        close_raw_handle(handle, "published governance")
        publish_state.published_handle = None

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
        if directory is not None:
            handle = directory
            try:
                secure_filesystem._windows_close_directory(handle)
            except BaseException as close_error:
                try:
                    remains_open = _windows_governance_handle_is_open(handle)
                except BaseException as state_error:
                    raise InventoryError(
                        "governance directory close outcome is unavailable"
                    ) from ExceptionGroup(
                        "governance directory close failures",
                        (close_error, state_error),
                    )
                if remains_open:
                    raise InventoryError(
                        "governance directory close failed before close"
                    ) from close_error
            directory = None

    def acquire_recovery_for_cleanup() -> int | None:
        if publish_state.destination_handle is not None:
            return publish_state.destination_handle
        if directory is None or publish_state.recovery_name is None:
            return None
        try:
            handle = _windows_open_relative_governance_file_raw(
                directory,
                publish_state.recovery_name,
            )
        except BaseException:
            return None
        publish_state.destination_handle = handle
        return handle

    def close_recovery_handle() -> None:
        if publish_state.destination_handle is None:
            return
        handle = publish_state.destination_handle
        close_raw_handle(handle, "governance recovery")
        publish_state.destination_handle = None

    def current_destination_is_staged() -> None:
        if directory is None:
            raise InventoryError("governance directory handle is absent")
        if staged_snapshot is None:
            raise InventoryError("governance staging identity is absent")
        current_identity, current_raw = _windows_read_relative_governance_file(
            directory,
            path.name,
        )
        if (
            current_identity != staged_snapshot.identity[:2]
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
        handle = acquire_recovery_for_cleanup()
        if handle is None:
            raise InventoryError("governance recovery cleanup handle is absent")
        secure_filesystem._windows_dispose_relative_file(handle)
        publish_state.recovery_deletion_armed = True
        close_recovery_handle()
        publish_state.recovery_deletion_armed = False
        publish_state.displaced = False
        publish_state.recovery_name = None
        outcome.recovery_path = None

    def cleanup_temporary() -> None:
        nonlocal temporary
        if temporary is None:
            return
        if not temporary.renamed and temporary.state != "deletion_armed":
            secure_filesystem._windows_dispose_relative_file(
                temporary.handle
            )
            temporary.state = "deletion_armed"
        close_owner(temporary, "governance staging handle")
        temporary = None

    def cleanup_directory_lock() -> None:
        nonlocal directory_lock
        if directory_lock is None:
            return
        if directory_lock.handle is not None:
            if directory_lock.state != "deletion_armed":
                _windows_dispose_governance_lock(directory_lock.handle)
                directory_lock.state = "deletion_armed"
            close_owner(directory_lock, "governance writer lock")
        directory_lock = None

    def rollback_transaction() -> None:
        failures: list[BaseException] = []
        try:
            if publish_state.published:
                if directory is None or temporary is None:
                    raise InventoryError("governance rollback state is incomplete")
                retry_cleanup(close_published_handle)
                retry_cleanup(cleanup_temporary)
                current_destination_is_staged()
                if publish_state.displaced:
                    recovery_handle = acquire_recovery_for_cleanup()
                    if recovery_handle is None:
                        raise InventoryError("governance recovery handle is absent")
                    if publish_state.recovery_deletion_armed:
                        _windows_cancel_relative_disposition(recovery_handle)
                        publish_state.recovery_deletion_armed = False
                    _windows_rename_governance_file(
                        recovery_handle,
                        directory,
                        path.name,
                        replace=True,
                    )
                else:
                    published_handle = (
                        _windows_open_relative_governance_file_raw(
                            directory,
                            path.name,
                        )
                    )
                    secure_filesystem._windows_dispose_relative_file(
                        published_handle
                    )
                    close_raw_handle(
                        published_handle,
                        "published governance rollback",
                    )
                publish_state.published = False
                publish_state.displaced = False
                publish_state.recovery_name = None
                outcome.published = False
                outcome.snapshot = None
                outcome.recovery_path = None
            else:
                cleanup_unpublished_recovery()
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
        try:
            retry_cleanup(cleanup_directory_lock)
        except BaseException as error:
            failures.append(error)
        try:
            close_directory()
        except BaseException as error:
            failures.append(error)
        if failures:
            raise InventoryError("governance rollback failed") from ExceptionGroup(
                "governance rollback failures",
                tuple(failures),
            )

    def finalize_transaction() -> None:
        nonlocal directory, temporary
        if directory is None or temporary is None:
            raise InventoryError("governance finalization state is incomplete")
        if publish_state.destination_handle is not None:
            recovery_handle = publish_state.destination_handle
            secure_filesystem._windows_dispose_relative_file(
                recovery_handle
            )
            publish_state.recovery_deletion_armed = True
            close_raw_handle(recovery_handle, "governance recovery")
            publish_state.destination_handle = None
            publish_state.recovery_deletion_armed = False
            publish_state.displaced = False
            publish_state.recovery_name = None
            outcome.recovery_path = None
        committed_temporary = temporary
        committed_lock = directory_lock
        committed_directory = directory
        temporary = None
        directory = None
        _best_effort_governance_close(
            close_published_handle,
            retry_if_open=lambda: (
                publish_state.published_handle is not None
                and _windows_governance_handle_is_open(
                    publish_state.published_handle
                )
            ),
        )
        _best_effort_governance_close(
            lambda: close_owner(
                committed_temporary,
                "governance staging handle",
            ),
            retry_if_open=lambda: (
                committed_temporary.handle is not None
                and _windows_governance_handle_is_open(
                    committed_temporary.handle
                )
            ),
        )
        _best_effort_governance_close(
            lambda: close_owner(
                committed_lock,
                "governance writer lock",
            ),
            retry_if_open=lambda: (
                committed_lock.handle is not None
                and _windows_governance_handle_is_open(
                    committed_lock.handle
                )
            ),
        )
        _best_effort_governance_close(
            lambda: secure_filesystem._windows_close_directory(
                committed_directory
            ),
            retry_if_open=lambda: _windows_governance_handle_is_open(
                committed_directory
            ),
        )

    try:
        directory, bound_identity = _windows_open_governance_directory(
            path.parent
        )
        lock_name = f".{path.name}.pontius-governance.lock"
        directory_lock = secure_filesystem._StagedBaseline(
            lock_name,
            None,
        )
        _windows_create_relative_governance_file(
            directory,
            lock_name,
            owner=directory_lock,
            share_delete=False,
        )
        _windows_dispose_governance_lock(directory_lock.handle)
        directory_lock.state = "deletion_armed"
        temporary_name = f".{path.name}.{uuid.uuid4().hex}.tmp"
        temporary = secure_filesystem._StagedBaseline(
            temporary_name,
            None,
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
            expected_raw=expected_raw,
            state=publish_state,
            outcome=outcome,
        )
        temporary.renamed = True
        close_owner(temporary, "governance staging handle")
        publish_state.published_handle = (
            _windows_open_relative_governance_file_raw(
                directory,
                path.name,
                read_data=True,
                share_write=False,
                delete_access=False,
            )
        )
        if _windows_governance_handle_file_id(
            publish_state.published_handle
        ) != staged_snapshot.identity[:2]:
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
        _validated=True,
    )


def write_atomic_lf(
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
        )
    collector = _governance_transaction_collector()
    retain = _retain_transaction is True or (
        _retain_transaction is None and collector is not None
    )
    if retain:
        if _retain_transaction is None and collector is not None:
            collector.append(transaction)
        return transaction
    _coordinate_governance_commit((transaction,))
    return transaction.snapshot


def _restore_finalized_governance(
    transaction: _GovernanceWriteTransaction,
) -> None:
    current = secure_filesystem.read_regular_snapshot(
        transaction.path,
        maximum_bytes=MAXIMUM_SOURCE_BYTES,
        root=transaction.path.parent,
    )
    if (
        current.identity != transaction.snapshot.identity
        or current.raw != transaction.snapshot.raw
    ):
        raise InventoryError(
            "governance rollback refused a concurrent finalized destination"
        )
    if transaction.original_identity is not None:
        if transaction.original_raw is None:
            raise InventoryError("governance original bytes are absent")
        write_atomic_lf(
            transaction.path,
            transaction.original_raw,
            expected_identity=current.identity,
            _expected_raw=current.raw,
            _retain_transaction=False,
        )
        return
    chain = _governance_directory_chain(transaction.path.parent)
    if os.name == "nt":
        directory, bound_identity = _windows_open_governance_directory(
            transaction.path.parent
        )
        handle: int | None = None
        try:
            handle = _windows_open_relative_governance_file(
                directory,
                transaction.path.name,
            )
            if _windows_governance_handle_file_id(handle) != current.identity[:2]:
                raise InventoryError(
                    "finalized governance rollback identity changed"
                )
            secure_filesystem._windows_dispose_relative_file(handle)
            secure_filesystem._windows_close_file(handle)
            handle = None
            if (
                secure_filesystem._windows_directory_handle_identity(
                    directory,
                    transaction.path.parent,
                )
                != bound_identity
            ):
                raise InventoryError(
                    "finalized governance rollback directory changed"
                )
        finally:
            if handle is not None:
                secure_filesystem._windows_close_file(handle)
            secure_filesystem._windows_close_directory(directory)
        return
    flags = (
        os.O_RDONLY
        | os.O_DIRECTORY
        | os.O_NOFOLLOW
        | getattr(os, "O_CLOEXEC", 0)
    )
    directory = os.open(transaction.path.parent, flags)
    try:
        _revalidate_governance_directory_chain(chain)
        info = os.stat(
            transaction.path.name,
            dir_fd=directory,
            follow_symlinks=False,
        )
        if secure_filesystem._file_identity(info) != current.identity:
            raise InventoryError("finalized governance rollback identity changed")
        os.unlink(transaction.path.name, dir_fd=directory)
        os.fsync(directory)
    finally:
        os.close(directory)


def _write_governance_pair(
    first_path: Path,
    first_raw: bytes,
    first_snapshot: object,
    second_path: Path,
    second_raw: bytes,
    second_snapshot: object,
    *,
    lifetime_check: Any | None = None,
) -> object:
    transactions: list[_GovernanceWriteTransaction] = []
    outcomes = {
        first_path: _GovernanceWriteOutcome(),
        second_path: _GovernanceWriteOutcome(),
    }
    post_publish_check = (
        None
        if lifetime_check is None
        else lambda _snapshot: lifetime_check()
    )
    try:
        first_transaction = write_atomic_lf(
            first_path,
            first_raw,
            expected_identity=first_snapshot.identity,
            _expected_raw=first_snapshot.raw,
            _outcome=outcomes[first_path],
            _lifetime_check=lifetime_check,
            _post_publish_lifetime_check=post_publish_check,
            _retain_transaction=True,
        )
        if not isinstance(first_transaction, _GovernanceWriteTransaction):
            raise InventoryError("first governance transaction is absent")
        transactions.append(first_transaction)
        second_transaction = write_atomic_lf(
            second_path,
            second_raw,
            expected_identity=second_snapshot.identity,
            _expected_raw=second_snapshot.raw,
            _outcome=outcomes[second_path],
            _lifetime_check=lifetime_check,
            _post_publish_lifetime_check=post_publish_check,
            _retain_transaction=True,
        )
        if not isinstance(second_transaction, _GovernanceWriteTransaction):
            raise InventoryError("second governance transaction is absent")
        transactions.append(second_transaction)
    except BaseException as primary_failure:
        rollback_failures: list[BaseException] = []
        for transaction in reversed(transactions):
            try:
                transaction.rollback()
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
    pair = _GovernancePairTransaction(
        tuple(transactions),
        _lifetime_check=lifetime_check,
    )
    collector = _governance_transaction_collector()
    if collector is not None:
        collector.append(pair)
        return pair
    _coordinate_governance_commit((pair,))
    return None


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
        self.local_functions: dict[
            str,
            ast.FunctionDef | ast.AsyncFunctionDef,
        ] = {}
        self.local_classes: set[str] = set()
        self.callback_names: set[str] = set()
        self.closure_blockers: list[tuple[ast.Call, str]] = []

    def visit_Call(self, node: ast.Call) -> None:
        self.calls.append(node)
        if isinstance(node.func, ast.Lambda) and _contains_sensitive_runtime(
            node.func.body
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
                and _contains_sensitive_runtime(node.value.body)
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
        self.local_functions[node.name] = node
        if _contains_sensitive_runtime(node):
            self.callback_names.add(node.name)
        for expression in (*node.decorator_list, *node.args.defaults):
            self.visit(expression)
        for expression in node.args.kw_defaults:
            if expression is not None:
                self.visit(expression)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.local_functions[node.name] = node
        if _contains_sensitive_runtime(node):
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


def _contains_sensitive_runtime(node: ast.AST) -> bool:
    for candidate in ast.walk(node):
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
) -> _ExecutionScopeVisitor:
    visitor = _ExecutionScopeVisitor()
    for statement in node.body:
        visitor.visit(statement)
    return visitor


def _merge_call_counts(
    *counts: Mapping[bytes, int],
) -> dict[bytes, int]:
    merged: dict[bytes, int] = {}
    for supplied in counts:
        for key, value in supplied.items():
            merged[key] = merged.get(key, 0) + value
    return merged


def _maximum_call_counts(
    first: Mapping[bytes, int],
    second: Mapping[bytes, int],
) -> dict[bytes, int]:
    return {
        key: max(first.get(key, 0), second.get(key, 0))
        for key in set(first) | set(second)
    }


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
                return len(range(*values))
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
) -> tuple[dict[bytes, int], set[bytes]]:
    if node is None or isinstance(
        node,
        (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef),
    ):
        return {}, set()
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
                repeated_keys = {
                    definitions[id(candidate)]
                    for candidate in ast.walk(repeated_node)
                    if isinstance(candidate, ast.Call)
                    and id(candidate) in definitions
                }
                dynamic |= repeated_keys
                return counts, dynamic
            repeated *= bound
            for condition in generator.ifs:
                condition_counts, condition_dynamic = _expression_call_counts(
                    condition,
                    definitions,
                    assignments=assignments,
                    relative_path=relative_path,
                    aliases=aliases,
                    helper_registry=helper_registry,
                    multiplier=repeated,
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
) -> tuple[dict[bytes, int], set[bytes]]:
    counts: dict[bytes, int] = {}
    dynamic: set[bytes] = set()
    for statement in statements:
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
            )
            body_counts, body_dynamic = _runtime_call_bounds(
                statement.body,
                definitions,
                assignments=assignments,
                relative_path=relative_path,
                aliases=aliases,
                helper_registry=helper_registry,
            )
            else_counts, else_dynamic = _runtime_call_bounds(
                statement.orelse,
                definitions,
                assignments=assignments,
                relative_path=relative_path,
                aliases=aliases,
                helper_registry=helper_registry,
            )
            counts = _merge_call_counts(
                counts,
                test_counts,
                _maximum_call_counts(body_counts, else_counts),
            )
            dynamic |= test_dynamic | body_dynamic | else_dynamic
            continue
        if isinstance(statement, (ast.For, ast.AsyncFor)):
            iterator_counts, iterator_dynamic = _expression_call_counts(
                statement.iter,
                definitions,
                assignments=assignments,
                relative_path=relative_path,
                aliases=aliases,
                helper_registry=helper_registry,
            )
            body_counts, body_dynamic = _runtime_call_bounds(
                statement.body,
                definitions,
                assignments=assignments,
                relative_path=relative_path,
                aliases=aliases,
                helper_registry=helper_registry,
            )
            else_counts, else_dynamic = _runtime_call_bounds(
                statement.orelse,
                definitions,
                assignments=assignments,
                relative_path=relative_path,
                aliases=aliases,
                helper_registry=helper_registry,
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
                body_counts = {
                    key: value * bound for key, value in body_counts.items()
                }
                dynamic |= body_dynamic
            counts = _merge_call_counts(
                counts, iterator_counts, body_counts, else_counts
            )
            dynamic |= iterator_dynamic | else_dynamic
            continue
        if isinstance(statement, ast.While):
            test_counts, test_dynamic = _expression_call_counts(
                statement.test,
                definitions,
                assignments=assignments,
                relative_path=relative_path,
                aliases=aliases,
                helper_registry=helper_registry,
            )
            body_counts, body_dynamic = _runtime_call_bounds(
                statement.body,
                definitions,
                assignments=assignments,
                relative_path=relative_path,
                aliases=aliases,
                helper_registry=helper_registry,
            )
            static_test = _static_value(statement.test, assignments)
            if static_test is False:
                body_counts = {}
            else:
                dynamic |= set(body_counts) | body_dynamic
                body_counts = {}
            else_counts, else_dynamic = _runtime_call_bounds(
                statement.orelse,
                definitions,
                assignments=assignments,
                relative_path=relative_path,
                aliases=aliases,
                helper_registry=helper_registry,
            )
            counts = _merge_call_counts(
                counts, test_counts, body_counts, else_counts
            )
            dynamic |= test_dynamic | else_dynamic
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
            )
            counts = _merge_call_counts(counts, body_counts)
            dynamic |= body_dynamic
            continue
        if isinstance(statement, ast.Match):
            subject_counts, subject_dynamic = _expression_call_counts(
                statement.subject,
                definitions,
                assignments=assignments,
                relative_path=relative_path,
                aliases=aliases,
                helper_registry=helper_registry,
            )
            alternative_counts: dict[bytes, int] = {}
            alternative_dynamic: set[bytes] = set()
            for case in statement.cases:
                guard_counts, guard_dynamic = _expression_call_counts(
                    case.guard,
                    definitions,
                    assignments=assignments,
                    relative_path=relative_path,
                    aliases=aliases,
                    helper_registry=helper_registry,
                )
                body_counts, body_dynamic = _runtime_call_bounds(
                    case.body,
                    definitions,
                    assignments=assignments,
                    relative_path=relative_path,
                    aliases=aliases,
                    helper_registry=helper_registry,
                )
                case_counts = _merge_call_counts(guard_counts, body_counts)
                alternative_counts = _maximum_call_counts(
                    alternative_counts,
                    case_counts,
                )
                alternative_dynamic |= guard_dynamic | body_dynamic
            counts = _merge_call_counts(
                counts,
                subject_counts,
                alternative_counts,
            )
            dynamic |= subject_dynamic | alternative_dynamic
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
            )
            alternative_counts, alternative_dynamic = _runtime_call_bounds(
                statement.orelse,
                definitions,
                assignments=assignments,
                relative_path=relative_path,
                aliases=aliases,
                helper_registry=helper_registry,
            )
            for handler in statement.handlers:
                type_counts, type_dynamic = _expression_call_counts(
                    handler.type,
                    definitions,
                    assignments=assignments,
                    relative_path=relative_path,
                    aliases=aliases,
                    helper_registry=helper_registry,
                )
                handler_counts, handler_dynamic = _runtime_call_bounds(
                    handler.body,
                    definitions,
                    assignments=assignments,
                    relative_path=relative_path,
                    aliases=aliases,
                    helper_registry=helper_registry,
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
            continue
        statement_counts, statement_dynamic = _expression_call_counts(
            statement,
            definitions,
            assignments=assignments,
            relative_path=relative_path,
            aliases=aliases,
            helper_registry=helper_registry,
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
) -> bool:
    for candidate in ast.walk(node):
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
        )
    }
    for key, definition in helper_registry.items():
        prefix = f"{relative_path}::"
        if not key.startswith(prefix):
            continue
        remainder = key[len(prefix) :]
        if "::" in remainder:
            continue
        if _helper_has_sensitive_closure(definition, helper_registry):
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
        ):
            continue
        dynamic[target.id] = (
            "callable alias is dynamically unresolved"
            if any(
                isinstance(candidate, ast.Name)
                and candidate.id in frozen_sensitive_names
                for candidate in ast.walk(value)
            )
            else "mixed protected receiver is dynamically unresolved"
        )
    return dynamic


@dataclass(frozen=True, slots=True)
class _FlowValue:
    kind: str
    value: object = None
    sensitive: bool = False
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class _FlowEnvironment:
    owner: str
    additions: tuple[tuple[str, str], ...] = ()
    removals: tuple[str, ...] = ()
    poison: str | None = None


@dataclass(slots=True)
class _ReviewFlow:
    aliases_by_call: dict[int, dict[str, str]]
    assignments_by_call: dict[int, dict[str, ast.expr]]
    environments_by_call: dict[
        int,
        tuple[dict[str, str], list[str], str | None],
    ]
    blockers_by_call: dict[int, str]


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
    if value.kind == "sequence":
        return any(_flow_is_sensitive(item) for item in value.value)
    if value.kind == "mapping":
        return any(_flow_is_sensitive(item) for _, item in value.value)
    return False


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
    present = tuple(value for value in values if value is not None)
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
        return _FlowValue(
            "environment",
            _FlowEnvironment(
                owner,
                poison="subprocess environment branch state is ambiguous",
            ),
            reason="subprocess environment branch state is ambiguous",
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
    ) -> None:
        self.values = {
            name: _flow_qname(qualified)
            for name, qualified in aliases.items()
        }
        self.local_functions = dict(local_functions)
        self.flow = _ReviewFlow({}, {}, {}, {})
        for name, expression in module_assignments.items():
            self.values[name] = self._evaluate(expression, self.values, False)
        for name, definition in local_functions.items():
            self.values[name] = _FlowValue(
                "qname",
                name,
                _contains_sensitive_runtime(definition),
                "callable helper closure" if _contains_sensitive_runtime(
                    definition
                ) else None,
            )
        for name in sensitive_helper_names:
            self.values[name] = _FlowValue(
                "qname",
                name,
                sensitive=True,
                reason="callable helper closure",
            )

    def resolve(
        self,
        statements: Sequence[ast.stmt],
    ) -> _ReviewFlow:
        self._statements(statements, self.values)
        return self.flow

    def _snapshot_call(
        self,
        node: ast.Call,
        values: Mapping[str, _FlowValue],
        callable_value: _FlowValue,
    ) -> None:
        self.flow.aliases_by_call[id(node)] = _flow_aliases(values)
        self.flow.assignments_by_call[id(node)] = _flow_assignments(values)
        if callable_value.kind == "unknown" and callable_value.sensitive:
            self.flow.blockers_by_call[id(node)] = (
                callable_value.reason
                or "dynamic sensitive call target is unresolved"
            )
        callable_name = (
            str(callable_value.value)
            if callable_value.kind == "qname"
            else None
        )
        if callable_name in _SUBPROCESS_FUNCTIONS:
            keywords = {
                keyword.arg: keyword.value
                for keyword in node.keywords
                if keyword.arg is not None
            }
            self.flow.environments_by_call[id(node)] = (
                self._environment_snapshot(keywords.get("env"), values)
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

    def _evaluate(
        self,
        node: ast.AST | None,
        values: dict[str, _FlowValue],
        record: bool = True,
    ) -> _FlowValue:
        if node is None:
            return _FlowValue("scalar", None)
        if isinstance(node, ast.Constant):
            return _FlowValue("scalar", node.value)
        if isinstance(node, ast.Name):
            return values.get(node.id, _flow_qname(node.id))
        if isinstance(node, ast.Attribute):
            base = self._evaluate(node.value, values, record)
            if base.kind in {"qname", "object"}:
                return _flow_qname(f"{base.value}.{node.attr}")
            if _flow_is_sensitive(base):
                return _flow_unknown(
                    "mixed protected receiver is dynamically unresolved",
                    sensitive=True,
                )
            return _flow_unknown("attribute receiver is dynamically unresolved")
        if isinstance(node, ast.Subscript):
            base = self._evaluate(node.value, values, record)
            index = self._evaluate(node.slice, values, record)
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
                    "mixed protected receiver is dynamically unresolved",
                    sensitive=True,
                )
            return _flow_unknown("subscript receiver is dynamically unresolved")
        if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
            return _FlowValue(
                "sequence",
                tuple(self._evaluate(item, values, record) for item in node.elts),
            )
        if isinstance(node, ast.Dict):
            additions: dict[str, str] = {}
            inherited = False
            items: list[tuple[str, _FlowValue]] = []
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
                    return _flow_unknown("mapping expansion is unresolved")
                key = self._evaluate(key_node, values, record)
                value = self._evaluate(value_node, values, record)
                if key.kind != "scalar" or type(key.value) is not str:
                    return _flow_unknown("mapping key is unresolved")
                items.append((key.value, value))
                if value.kind == "scalar" and type(value.value) is str:
                    additions[key.value] = value.value
            if inherited:
                return _FlowValue(
                    "environment",
                    _FlowEnvironment(
                        "<literal-environment>",
                        tuple(sorted(additions.items())),
                    ),
                )
            return _FlowValue("mapping", tuple(items))
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            left = self._evaluate(node.left, values, record)
            right = self._evaluate(node.right, values, record)
            if (
                left.kind == "scalar"
                and right.kind == "scalar"
                and type(left.value) is str
                and type(right.value) is str
            ):
                return _FlowValue("scalar", left.value + right.value)
            return _flow_unknown("binary value is dynamically unresolved")
        if isinstance(node, ast.IfExp):
            self._evaluate(node.test, values, record)
            first = self._evaluate(node.body, dict(values), record)
            second = self._evaluate(node.orelse, dict(values), record)
            return _merge_flow_values("conditional expression", (first, second))
        if isinstance(node, ast.NamedExpr):
            value = self._evaluate(node.value, values, record)
            self._assign(node.target, value, values)
            return value
        if isinstance(node, ast.Lambda):
            return _FlowValue(
                "callback",
                node,
                _contains_sensitive_runtime(node.body),
                "callback closure",
            )
        if isinstance(node, ast.Call):
            callable_value = self._evaluate(node.func, values, record)
            argument_values = [
                self._evaluate(argument, values, record)
                for argument in node.args
            ]
            keyword_values = [
                self._evaluate(keyword.value, values, record)
                for keyword in node.keywords
            ]
            if record:
                self._snapshot_call(node, values, callable_value)
                if any(
                    value.kind == "callback" and value.sensitive
                    for value in (*argument_values, *keyword_values)
                ):
                    self.flow.blockers_by_call[id(node)] = "callback closure"
            callable_name = (
                str(callable_value.value)
                if callable_value.kind == "qname"
                else None
            )
            if callable_name == "getattr" and len(argument_values) == 2:
                base, attribute = argument_values
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
            if (
                isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
            ):
                owner_name = node.func.value.id
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
            if callable_name is not None and _is_sensitive_namespace(callable_name):
                return _FlowValue(
                    "object",
                    f"{callable_name}()",
                    sensitive=True,
                )
            return _flow_unknown("call result is dynamically unresolved")
        for child in ast.iter_child_nodes(node):
            self._evaluate(child, values, record)
        return _flow_unknown("expression is dynamically unresolved")

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
        if isinstance(target, (ast.Tuple, ast.List)):
            if value.kind != "sequence" or len(target.elts) != len(value.value):
                ambiguous = _flow_unknown(
                    "sequence assignment is dynamically unresolved",
                    sensitive=_flow_is_sensitive(value),
                )
                for item in target.elts:
                    self._assign(item, ambiguous, values)
                return
            for item, supplied in zip(target.elts, value.value, strict=True):
                self._assign(item, supplied, values)
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

    def _statements(
        self,
        statements: Sequence[ast.stmt],
        values: dict[str, _FlowValue],
    ) -> dict[str, _FlowValue]:
        for statement in statements:
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
                value = self._evaluate(statement.value, values)
                self._assign(statement.target, value, values)
                continue
            if isinstance(statement, ast.AugAssign):
                self._evaluate(statement.value, values)
                previous = self._evaluate(statement.target, values, False)
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
                    if isinstance(target, ast.Name):
                        values.pop(target.id, None)
                    elif (
                        isinstance(target, ast.Subscript)
                        and isinstance(target.value, ast.Name)
                    ):
                        key = self._evaluate(target.slice, values, False)
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
                        elif (
                            owner_value is not None
                            and owner_value.kind == "environment"
                        ):
                            self._poison_environment(
                                values,
                                owner_value.value.owner,
                                "subprocess environment removal is unresolved",
                            )
                continue
            if isinstance(statement, ast.Expr):
                self._evaluate(statement.value, values)
                continue
            if isinstance(statement, ast.If):
                test = self._evaluate(statement.test, values)
                if test.kind == "scalar" and type(test.value) is bool:
                    chosen = statement.body if test.value else statement.orelse
                    chosen_state = self._statements(chosen, dict(values))
                    values.clear()
                    values.update(chosen_state)
                    continue
                first = self._statements(statement.body, dict(values))
                second = self._statements(statement.orelse, dict(values))
                values.clear()
                values.update(self._merge_states((first, second)))
                continue
            if isinstance(statement, (ast.For, ast.AsyncFor)):
                iterator = self._evaluate(statement.iter, values)
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
                bound = (
                    len(iterator.value)
                    if iterator.kind == "sequence"
                    else None
                )
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
                if test.kind == "scalar" and test.value is False:
                    merged = dict(values)
                else:
                    body = self._statements(statement.body, dict(values))
                    merged = self._merge_states((values, body))
                merged = self._statements(statement.orelse, merged)
                values.clear()
                values.update(merged)
                continue
            if isinstance(statement, (ast.With, ast.AsyncWith)):
                for item in statement.items:
                    supplied = self._evaluate(item.context_expr, values)
                    if item.optional_vars is not None:
                        self._assign(item.optional_vars, supplied, values)
                self._statements(statement.body, values)
                continue
            try_types = (ast.Try,)
            if hasattr(ast, "TryStar"):
                try_types = (*try_types, ast.TryStar)
            if isinstance(statement, try_types):
                body = self._statements(statement.body, dict(values))
                normal = self._statements(statement.orelse, dict(body))
                alternatives = [normal]
                for handler in statement.handlers:
                    handler_state = dict(values)
                    self._evaluate(handler.type, handler_state)
                    alternatives.append(
                        self._statements(handler.body, handler_state)
                    )
                merged = self._merge_states(alternatives)
                merged = self._statements(statement.finalbody, merged)
                values.clear()
                values.update(merged)
                continue
            if isinstance(statement, ast.Match):
                self._evaluate(statement.subject, values)
                alternatives: list[dict[str, _FlowValue]] = []
                for case in statement.cases:
                    case_state = dict(values)
                    self._evaluate(case.guard, case_state)
                    alternatives.append(
                        self._statements(case.body, case_state)
                    )
                if alternatives:
                    values.clear()
                    values.update(self._merge_states(alternatives))
                continue
            if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for expression in (*statement.decorator_list, *statement.args.defaults):
                    self._evaluate(expression, values)
                for expression in statement.args.kw_defaults:
                    self._evaluate(expression, values)
                values[statement.name] = _FlowValue(
                    "qname",
                    statement.name,
                    _contains_sensitive_runtime(statement),
                )
                continue
            if isinstance(statement, ast.ClassDef):
                for expression in (*statement.decorator_list, *statement.bases):
                    self._evaluate(expression, values)
                for keyword in statement.keywords:
                    self._evaluate(keyword.value, values)
                class_statements = [
                    item
                    for item in statement.body
                    if not isinstance(
                        item,
                        (ast.FunctionDef, ast.AsyncFunctionDef),
                    )
                ]
                self._statements(class_statements, dict(values))
                values[statement.name] = _flow_qname(statement.name)
                continue
            for child in ast.iter_child_nodes(statement):
                self._evaluate(child, values)
        return values


def _source_ordered_review_flow(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    aliases: Mapping[str, str],
    module_assignments: Mapping[str, ast.expr],
    local_functions: Mapping[
        str,
        ast.FunctionDef | ast.AsyncFunctionDef,
    ],
    sensitive_helper_names: frozenset[str] = frozenset(),
) -> _ReviewFlow:
    return _SourceOrderedResolver(
        aliases,
        module_assignments,
        local_functions,
        sensitive_helper_names,
    ).resolve(node.body)


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
    resolved = _resolved_qualified_name(call.func, aliases)
    if (
        definition.node.name == "__init__"
        and definition.class_name is not None
        and resolved is not None
        and (
            resolved == definition.class_name
            or resolved.endswith(f".{definition.class_name}")
        )
    ):
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
    active: frozenset[str] = frozenset(),
) -> bool:
    execution = _execution_scope(definition.node)
    aliases = _function_aliases(
        definition.aliases,
        execution.imports,
        execution.assignments,
    )
    if execution.closure_blockers:
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
                active=active | {helper_key},
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
) -> tuple[
    dict[str, object] | None,
    str | None,
    list[tuple[str, dict[str, object]]],
]:
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
        if child_depth >= 4:
            return None, "subprocess child analysis depth is exceeded", []
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
        program_execution = _ExecutionScopeVisitor()
        for statement in program_tree.body:
            program_execution.visit(statement)
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
        program_flow = _SourceOrderedResolver(
            _module_import_aliases(program_tree),
            program_assignments,
            program_execution.local_functions,
        ).resolve(program_tree.body)
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
                    program_execution.local_functions[raw_child]
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
            )
            if child_error is not None:
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
            child_definition = _call_definition(child, child_aliases)
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
) -> dict[str, object] | None:
    qualified = _resolved_callable_name(call.func, aliases)
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
) -> str | None:
    qualified = _resolved_callable_name(call.func, aliases)
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
        row["maximum_calls"] = int(row["maximum_calls"]) * multiplier
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
    referenced_names = {
        candidate.id
        for statement in execution.assignments
        for candidate in ast.walk(statement)
        if isinstance(candidate, ast.Name)
    }
    sensitive_helper_names: set[str] = set()
    for name in referenced_names:
        definition = helper_registry.get(f"{relative_path}::{name}")
        if definition is not None and _helper_has_sensitive_closure(
            definition,
            helper_registry,
        ):
            sensitive_helper_names.add(name)
    source_flow = _source_ordered_review_flow(
        node,
        aliases,
        module_assignments,
        execution.local_functions,
        frozenset(sensitive_helper_names),
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
    )
    rows: list[dict[str, object]] = []
    blockers: list[dict[str, object]] = []
    blockers.extend(
        _review_blocker(item_id, relative_path, call, reason)
        for call, reason in execution.closure_blockers
    )
    call_definitions: dict[int, bytes] = {}
    call_definition_rows: dict[bytes, dict[str, object]] = {}
    call_nodes: dict[bytes, ast.Call] = {}
    for call in execution.calls:
        call_aliases = source_flow.aliases_by_call.get(id(call), body_aliases)
        call_assignments = source_flow.assignments_by_call.get(
            id(call),
            assignments,
        )
        function = _resolved_qualified_name(call.func, call_aliases)
        callable_name = _resolved_callable_name(call.func, call_aliases)
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
        flow_blocker = source_flow.blockers_by_call.get(id(call))
        if flow_blocker is not None:
            blockers.append(
                _review_blocker(
                    item_id,
                    relative_path,
                    call,
                    flow_blocker,
                )
            )
            continue
        raw_function = _qualified_name(call.func)
        local_name = (
            raw_function
            if raw_function in execution.local_functions
            else function if function in execution.local_functions else None
        )
        if local_name is not None:
            local_node = execution.local_functions[local_name]
            local_definition = _ReviewFunction(
                relative_path,
                local_node,
                call_aliases,
                call_assignments,
                class_name,
            )
            local_key = (
                f"{relative_path}::<local:{local_name}:"
                f"{int(getattr(local_node, 'lineno', 0))}>"
            )
            if not _helper_has_sensitive_closure(
                local_definition,
                helper_registry,
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
                active_helpers=active_helpers | {local_key},
                analyzed_sites=analyzed_sites,
                helper_edges=helper_edges,
                closure_depth=closure_depth + 1,
                closure_helper_key=local_key,
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
            )
            argument_failure = supplied_arguments is None
            if supplied_arguments is None:
                if not _helper_has_sensitive_closure(
                    definition,
                    helper_registry,
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
                active_helpers=active_helpers | {helper_key},
                analyzed_sites=analyzed_sites,
                helper_edges=helper_edges,
                closure_depth=closure_depth + 1,
                closure_helper_key=helper_key,
            )
            if argument_failure and (refused or not added):
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
        )
        if process_error is not None:
            blockers.append(
                _review_blocker(item_id, relative_path, call, process_error)
            )
            continue
        if process is not None:
            site_key = site_keys[id(call)]
            if site_key in dynamic_sites:
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
                    blockers.append(
                        _review_blocker(
                            item_id,
                            relative_path,
                            call,
                            "subprocess repetition is not representable",
                        )
                    )
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
        call_definition = _call_definition(call, call_aliases)
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
    )
    for count_key in sorted(dynamic_call_keys):
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
                        analyzed_sites=analyzed_sites,
                        helper_edges=helper_edges,
                    )
                    rows.extend(added)
                    blockers.extend(refused)
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
    write_atomic_lf(
        destination,
        canonical_json_bytes(review) + b"\n",
        _lifetime_check=captured.revalidate,
        _post_publish_lifetime_check=lambda _snapshot: captured.revalidate(),
    )
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

    def validate_published_profile(snapshot: object) -> None:
        captured.revalidate_derivation_inputs()
        if snapshot.path != profile_path or snapshot.raw != updated:
            raise InventoryError("published profile snapshot is not exact")
        snapshot.revalidate()

    if enforce_repository_lock:
        configured_git = os.environ.get("PONTIUS_GIT")
        if configured_git is None:
            raise InventoryError("PONTIUS_GIT is required for design publication")
        def publish_with_attributes(attribute_check: Any) -> object:
            def lifetime_check() -> None:
                captured.revalidate()
                attribute_check()

            def post_publish_check(snapshot: object) -> None:
                validate_published_profile(snapshot)
                attribute_check()

            return write_atomic_lf(
                profile_path,
                updated,
                expected_identity=captured.profile_snapshot.identity,
                _expected_raw=captured.profile_snapshot.raw,
                _lifetime_check=lifetime_check,
                _post_publish_lifetime_check=post_publish_check,
            )

        _with_governance_attribute_lease(
            captured.repository_root,
            Path(configured_git),
            publish_with_attributes,
        )
    else:
        write_atomic_lf(
            profile_path,
            updated,
            expected_identity=captured.profile_snapshot.identity,
            _expected_raw=captured.profile_snapshot.raw,
            _lifetime_check=captured.revalidate,
            _post_publish_lifetime_check=validate_published_profile,
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
            def publish_pair(attribute_check: Any) -> None:
                def lifetime_check() -> None:
                    working_snapshot.revalidate()
                    attribute_check()

                _write_governance_pair(
                    inventory_path,
                    inventory_raw,
                    existing_inventory,
                    profile_path,
                    profile_raw,
                    existing_profile,
                    lifetime_check=lifetime_check,
                )

            _with_governance_attribute_lease(
                repository_root,
                Path(configured_git),
                publish_pair,
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
