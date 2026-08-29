"""Generate and verify the immutable test ownership and profile lock."""

from __future__ import annotations

import argparse
import ast
import atexit
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
MAXIMUM_ANALYSIS_HELPER_DEPTH = 64
MAXIMUM_ANALYSIS_CHILD_DEPTH = 4
MAXIMUM_ANALYSIS_CONTAINER_ELEMENTS = 4096
MAXIMUM_ANALYSIS_CARDINALITY = 2_147_483_647
MAXIMUM_ANALYSIS_WORK_UNITS = 250_000
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
    for relative_path in sorted(normalized_sources):
        raw = normalized_sources[relative_path]
        try:
            tree = ast.parse(raw.decode("utf-8", errors="strict"), filename=relative_path)
        except (UnicodeDecodeError, SyntaxError) as error:
            raise InventoryError(f"test source cannot be parsed: {relative_path}") from error
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
        for class_index, class_node in enumerate(tree.body):
            if not isinstance(class_node, ast.ClassDef):
                continue
            if not any(_is_test_case_base(base) for base in class_node.bases):
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


def _governance_action_destinations(action: Any) -> tuple[Path, ...]:
    declared = getattr(action, "_governance_destination_paths", None)
    if declared is not None:
        return tuple(declared)
    closure = getattr(action, "__closure__", None) or ()
    paths: list[Path] = []
    for cell in closure:
        try:
            value = cell.cell_contents
        except ValueError:
            continue
        if isinstance(value, Path) and value.is_absolute():
            paths.append(value)
    return tuple(paths)


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


def _with_governance_attribute_lease(
    repository_root: Path,
    git_path: Path,
    action: Any,
) -> object:
    manager = _governance_cleanup_manager()
    reservation = manager.reserve()
    try:
        destinations = _GovernanceDestinationSet.build(
            _governance_action_destinations(action)
        )
        lock_set = _GovernanceLockSetLease.acquire(destinations, reservation)
    except BaseException:
        manager.release(reservation)
        raise
    group = _GovernanceWriteGroup(lock_set, reservation)
    previous_group = _governance_active_group()
    previous_collector = _governance_transaction_collector()
    legacy_transactions: list[object] = []
    result: object | None = None
    try:
        _GOVERNANCE_TRANSACTION_CONTEXT.group = group
        _GOVERNANCE_TRANSACTION_CONTEXT.collector = legacy_transactions
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

        def revalidate() -> None:
            _verify_governance_attributes(
                lease,
                repository_root,
                environment,
            )
            _revalidate_git_launch_lease(lease)

        revalidate()
        result = action(revalidate)
        for transaction in legacy_transactions:
            group.add_participant(
                _GovernanceTransactionParticipant(
                    transaction,
                    Path(),
                    b"",
                )
            )
        group.validate_all(revalidate)
    except BaseException as error:
        _restore_governance_context(previous_group, previous_collector)
        group.abort_precommit(error)
        raise AssertionError("unreachable governance attribute abort")
    _restore_governance_context(previous_group, previous_collector)
    group.mark_committed()
    group.finish_committed_cleanup()
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


class _GovernanceCleanupManager:
    def __init__(self) -> None:
        self._next_id = 1
        self._reservations: set[int] = set()
        self._pending: dict[int, tuple[object, int]] = {}
        self._mutex = threading.RLock()
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
            self._pending[reservation.token] = (owner, 0)
            return reservation.token

    def retry_pending(self, retry_id: int | None = None) -> None:
        with self._mutex:
            selected = (
                (retry_id,)
                if retry_id is not None
                else tuple(sorted(self._pending))
            )
        first_failure: BaseException | None = None
        for selected_id in selected:
            with self._mutex:
                pending = self._pending.get(selected_id)
            if pending is None:
                if retry_id is not None:
                    raise InventoryError("governance cleanup retry ID is absent")
                continue
            owner, attempts = pending
            try:
                owner.retry_pending_cleanup()
            except BaseException as error:
                with self._mutex:
                    if selected_id in self._pending:
                        self._pending[selected_id] = (owner, attempts + 1)
                if first_failure is None:
                    first_failure = error
                continue
            with self._mutex:
                self._pending.pop(selected_id, None)
        if first_failure is not None:
            raise InventoryError("governance pending cleanup failed") from first_failure

    def pending_descriptors(self) -> tuple[object, ...]:
        with self._mutex:
            return tuple(
                owner.pending_descriptor(retry_id, attempts)
                for retry_id, (owner, attempts) in sorted(self._pending.items())
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
    handle: int
    close_action: Any
    is_open_action: Any
    closed: bool = False

    def close(self) -> None:
        if self.closed:
            return
        try:
            self.close_action()
        except BaseException:
            try:
                remains_open = bool(self.is_open_action())
            except BaseException:
                raise
            if remains_open:
                raise
            self.closed = True
            return
        self.closed = True

    def retry_pending_cleanup(self) -> None:
        self.close()


@dataclass(slots=True)
class _PosixDescriptorOwner:
    role: str
    descriptor: int
    close_action: Any
    closed: bool = False

    def close(self) -> None:
        if self.closed:
            return
        self.close_action()
        self.closed = True

    def retry_pending_cleanup(self) -> None:
        self.close()


@dataclass(slots=True)
class _PosixDeterministicLockOwner:
    descriptor: int
    path: Path
    role: str = "deterministic_lock"
    descriptor_closed: bool = False
    name_unlinked: bool = False
    closed: bool = False

    def close(self) -> None:
        if self.closed:
            return
        if not self.descriptor_closed:
            os.close(self.descriptor)
            self.descriptor_closed = True
        if not self.name_unlinked:
            self.path.unlink()
            self.name_unlinked = True
        self.closed = True

    def retry_pending_cleanup(self) -> None:
        self.close()


@dataclass(slots=True)
class _WindowsDeterministicLockOwner:
    name: str
    handle: int | None = None
    state: str = "unopened"
    disposal_armed: bool = False
    role: str = "deterministic_lock"
    closed: bool = False

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
            self.closed = True
            self.state = "closed"
            return
        self.arm_disposal()
        try:
            secure_filesystem._windows_close_file(self.handle)
        except BaseException:
            if _windows_governance_handle_is_open(self.handle):
                raise
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

    @classmethod
    def build(cls, paths: Iterable[Path]) -> _GovernanceDestinationSet:
        rows: list[tuple[str, Path]] = []
        for supplied in paths:
            if not isinstance(supplied, Path) or not supplied.is_absolute():
                raise InventoryError("governance destination must be absolute")
            lexical = Path(os.path.abspath(supplied))
            key = str(lexical)
            if os.name == "nt":
                key = os.path.normcase(key)
            rows.append((key, lexical))
        keys = [key for key, _ in rows]
        if len(set(keys)) != len(keys):
            raise InventoryError("duplicate governance destination alias")
        rows.sort(key=lambda row: row[0])
        return cls(
            tuple(path for _, path in rows),
            tuple(key for key, _ in rows),
        )


@dataclass(slots=True)
class _GovernanceLockSetLease:
    destination_set: _GovernanceDestinationSet
    owners: list[object]
    canonical_keys: tuple[str, ...]
    closed: bool = False

    @classmethod
    def acquire(
        cls,
        destination_set: _GovernanceDestinationSet,
        reservation: _GovernanceCleanupReservation,
    ) -> _GovernanceLockSetLease:
        manager = _governance_cleanup_manager()
        manager.retry_pending()
        owners: list[object] = []
        lease = cls(destination_set, owners, destination_set.canonical_keys)
        try:
            for path in destination_set.paths:
                if os.name == "nt":
                    directory, _ = _windows_open_governance_directory(path.parent)
                    directory_owner = _WindowsHandleOwner(
                        "directory",
                        directory,
                        lambda handle=directory: (
                            secure_filesystem._windows_close_directory(handle)
                        ),
                        lambda handle=directory: (
                            _windows_governance_handle_is_open(handle)
                        ),
                    )
                    owners.append(directory_owner)
                    lock_name = f".{path.name}.pontius-governance.lock"
                    lock_owner = _WindowsDeterministicLockOwner(lock_name)
                    owners.append(lock_owner)
                    _windows_create_relative_governance_file(
                        directory,
                        lock_name,
                        owner=lock_owner,
                        share_delete=False,
                    )
                    lock_owner.arm_disposal()
                else:
                    lock_path = path.with_name(
                        f".{path.name}.pontius-governance.lock"
                    )
                    descriptor = os.open(
                        lock_path,
                        os.O_WRONLY | os.O_CREAT | os.O_EXCL
                        | getattr(os, "O_CLOEXEC", 0),
                        0o600,
                    )

                    owners.append(
                        _PosixDeterministicLockOwner(
                            descriptor,
                            lock_path,
                        )
                    )
        except BaseException as error:
            busy = InventoryError("governance writer lock is busy")
            busy.__cause__ = error
            group = _GovernanceWriteGroup(lease, reservation)
            group.abort_precommit(busy)
            raise AssertionError("unreachable governance lock cleanup")
        return lease

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
        return _GovernancePendingDescriptor(
            retry_id,
            attempts,
            self.decision,
            tuple(path for path, _ in rows) or fallback_paths,
            {path: sha256(raw).hexdigest() for path, raw in rows},
            self._outstanding_roles(),
            tuple(
                str(path)
                for participant in self.participants
                for path in (
                    participant.artifact_paths()
                    if hasattr(participant, "artifact_paths")
                    else (getattr(participant, "recovery_path", None),)
                )
                if isinstance(path, Path)
            ),
            tuple(getattr(self.lock_set, "canonical_keys", ())),
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
    temporary_name = f".{path.name}.{uuid.uuid4().hex}.tmp"
    temporary: int | None = None
    publish_state = _GovernancePublishState()

    published_snapshot: object | None = None

    def outstanding_roles() -> tuple[str, ...]:
        roles: list[str] = []
        if temporary is not None:
            roles.append("staging")
        if publish_state.destination_handle is not None:
            roles.append("published")
        if directory is not None:
            roles.append("directory")
        return tuple(roles)

    def artifact_paths() -> tuple[Path, ...]:
        return (
            (outcome.recovery_path,)
            if outcome.recovery_path is not None
            else ()
        )

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
        close_resources()

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
    directory_lock: object | None = None
    temporary: object | None = None
    staged_snapshot: object | None = None
    published_snapshot: object | None = None
    bound_identity: tuple[int, bytes] | None = None
    publish_state = _GovernancePublishState()

    def outstanding_roles() -> tuple[str, ...]:
        roles: list[str] = []
        if temporary is not None and temporary.handle is not None:
            roles.append("staging")
        if publish_state.published_handle is not None:
            roles.append("published")
        if publish_state.destination_handle is not None:
            roles.append("recovery")
        if directory is not None:
            roles.append("directory")
        return tuple(roles)

    def artifact_paths() -> tuple[Path, ...]:
        paths: list[Path] = []
        if temporary is not None and temporary.handle is not None:
            paths.append(path.with_name(temporary.name))
        if outcome.recovery_path is not None:
            paths.append(outcome.recovery_path)
        return tuple(paths)

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
            raise InventoryError("governance rollback failed") from error
        failures: list[BaseException] = []
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
        if publish_state.destination_handle is not None:
            if directory is None:
                raise InventoryError("governance finalization directory is absent")
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
        close_published_handle()
        cleanup_temporary()
        cleanup_directory_lock()
        close_directory()

    try:
        directory, bound_identity = _windows_open_governance_directory(
            path.parent
        )
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
            True,
        )
    if _retain_transaction is not True:
        raise InventoryError(
            "locked governance writer requires a group-owned transaction"
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
            )
        except _GovernancePreparationFailure as failure:
            active_group.add_participant(failure.participant)
            raise failure.primary
        if not isinstance(transaction, _GovernanceWriteTransaction):
            raise InventoryError("governance transaction is absent")
        active_group.add_participant(
            _GovernanceTransactionParticipant(transaction, path, raw)
        )
        return transaction.snapshot
    manager = _governance_cleanup_manager()
    reservation = manager.reserve()
    try:
        destinations = _GovernanceDestinationSet.build((path,))
        lock_set = _GovernanceLockSetLease.acquire(destinations, reservation)
    except BaseException:
        manager.release(reservation)
        raise
    group = _GovernanceWriteGroup(lock_set, reservation)
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
    first_snapshot: object,
    second_path: Path,
    second_raw: bytes,
    second_snapshot: object,
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
        first_index = len(group.participants)
        write_atomic_lf(
            first_path,
            first_raw,
            expected_identity=first_snapshot.identity,
            _expected_raw=first_snapshot.raw,
            _lifetime_check=lifetime_check,
            _post_publish_lifetime_check=post_publish_check,
        )
        write_atomic_lf(
            second_path,
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
        if (
            first_snapshot.identity == second_snapshot.identity
            or os.path.samefile(first_path, second_path)
        ):
            raise InventoryError("native hardlink destination alias is forbidden")
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
_SAFE_OBSERVATION_CALLS = {
    "inspect.getsource",
    "inspect.getsourcefile",
    "inspect.signature",
    "str",
}
_SAFE_MOCK_FACTORIES = {
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
        self.local_functions[node.name] = node
        if _contains_sensitive_runtime(node, self.budget):
            self.callback_names.add(node.name)
        for expression in (*node.decorator_list, *node.args.defaults):
            self.visit(expression)
        for expression in node.args.kw_defaults:
            if expression is not None:
                self.visit(expression)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
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
class _AnalysisBudget:
    work_units: int = 0

    def consume(self, units: int = 1) -> None:
        self.work_units += units
        if self.work_units > MAXIMUM_ANALYSIS_WORK_UNITS:
            raise InventoryError(
                "analysis work units exceed 250000"
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
    ) -> None:
        self.bindings: dict[str, str] = dict(aliases)
        self.helper_returns = dict(helper_returns or {})
        for name in self.helper_returns:
            self.bindings.setdefault(name, name)
        self.tainted = {
            name
            for name, qualified in aliases.items()
            if self._qualified_is_sensitive(qualified)
        }
        self.calls: set[int] = set()
        self.return_values: list[tuple[str | None, bool]] = []
        self.budget = budget

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
            if len(supplied) == 1 and None not in supplied:
                value = next(iter(supplied))
                if value is not None:
                    bindings[name] = value
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
            return None, False
        if isinstance(node, ast.Name):
            qualified = self.bindings.get(node.id)
            return qualified, (
                node.id in self.tainted
                or self._qualified_is_sensitive(qualified)
            )
        if isinstance(node, ast.Attribute):
            raw = _qualified_name(node)
            if raw is not None and raw in self.bindings:
                qualified = self.bindings[raw]
                return qualified, (
                    raw in self.tainted
                    or self._qualified_is_sensitive(qualified)
                )
            qualified, sensitive = self._expression(node.value)
            if qualified is None:
                return None, sensitive
            supplied = f"{qualified}.{node.attr}"
            return supplied, self._qualified_call_is_sensitive(supplied)
        if isinstance(node, ast.NamedExpr):
            qualified, sensitive = self._expression(node.value)
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
            for argument in node.args:
                _, sensitive = self._expression(argument)
                result_sensitive |= sensitive
            for keyword in node.keywords:
                _, sensitive = self._expression(keyword.value)
                result_sensitive |= sensitive
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
            return None, result_sensitive
        if isinstance(
            node,
            (ast.ListComp, ast.SetComp, ast.GeneratorExp, ast.DictComp),
        ):
            incoming = self._snapshot()
            may_skip = False
            repeated: int | None = 1
            result_sensitive = False
            for generator in node.generators:
                if repeated == 0:
                    break
                _, iterator_sensitive = self._expression(generator.iter)
                result_sensitive |= iterator_sensitive
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
            if may_skip:
                self._merge((incoming, executed))
            return None, result_sensitive
        if isinstance(node, ast.Lambda):
            for default in (*node.args.defaults, *node.args.kw_defaults):
                self._expression(default)
            return None, False
        sensitive = False
        for child in ast.iter_child_nodes(node):
            _, child_sensitive = self._expression(child)
            sensitive |= child_sensitive
        return None, sensitive

    def _statements(self, statements: Sequence[ast.stmt]) -> None:
        for statement in statements:
            self.budget.consume()
            if isinstance(statement, ast.Import):
                for imported in statement.names:
                    local = imported.asname or imported.name.split(".", 1)[0]
                    qualified = imported.name if imported.asname else local
                    self._bind(
                        ast.Name(id=local),
                        qualified,
                        self._qualified_is_sensitive(qualified),
                    )
                continue
            if isinstance(statement, ast.ImportFrom) and statement.module:
                for imported in statement.names:
                    local = imported.asname or imported.name
                    qualified = f"{statement.module}.{imported.name}"
                    self._bind(
                        ast.Name(id=local),
                        qualified,
                        self._qualified_is_sensitive(qualified),
                    )
                continue
            if isinstance(statement, ast.Assign):
                qualified, sensitive = self._expression(statement.value)
                for target in statement.targets:
                    self._bind(target, qualified, sensitive)
                continue
            if isinstance(statement, ast.AnnAssign):
                qualified, sensitive = self._expression(statement.value)
                self._bind(statement.target, qualified, sensitive)
                continue
            if isinstance(statement, ast.AugAssign):
                _, old_sensitive = self._expression(statement.target)
                _, new_sensitive = self._expression(statement.value)
                self._bind(statement.target, None, old_sensitive or new_sensitive)
                continue
            if isinstance(statement, ast.Expr):
                self._expression(statement.value)
                continue
            if isinstance(statement, ast.If):
                self._expression(statement.test)
                incoming = self._snapshot()
                if isinstance(statement.test, ast.Constant):
                    self._statements(
                        statement.body if bool(statement.test.value) else statement.orelse
                    )
                    continue
                self._statements(statement.body)
                first = self._snapshot()
                self._restore(incoming)
                self._statements(statement.orelse)
                self._merge((first, self._snapshot()))
                continue
            if isinstance(statement, (ast.For, ast.AsyncFor)):
                _, sensitive = self._expression(statement.iter)
                incoming = self._snapshot()
                bound = self._literal_iteration_bound(statement.iter)
                if bound != 0:
                    self._bind(statement.target, None, sensitive)
                    self._statements(statement.body)
                    entered = self._snapshot()
                    if bound is None:
                        self._merge((incoming, entered))
                self._statements(statement.orelse)
                continue
            if isinstance(statement, ast.While):
                self._expression(statement.test)
                incoming = self._snapshot()
                if not (
                    isinstance(statement.test, ast.Constant)
                    and not bool(statement.test.value)
                ):
                    self._statements(statement.body)
                    self._merge((incoming, self._snapshot()))
                self._statements(statement.orelse)
                continue
            if isinstance(statement, (ast.With, ast.AsyncWith)):
                for item in statement.items:
                    qualified, sensitive = self._expression(item.context_expr)
                    if item.optional_vars is not None:
                        self._bind(item.optional_vars, qualified, sensitive)
                self._statements(statement.body)
                continue
            try_types = (ast.Try,)
            if hasattr(ast, "TryStar"):
                try_types = (*try_types, ast.TryStar)
            if isinstance(statement, try_types):
                incoming = self._snapshot()
                alternatives: list[tuple[dict[str, str], set[str]]] = []
                self._statements(statement.body)
                self._statements(statement.orelse)
                alternatives.append(self._snapshot())
                for handler in statement.handlers:
                    self._restore(incoming)
                    self._expression(handler.type)
                    if handler.name is not None:
                        self._bind(ast.Name(id=handler.name), None, False)
                    self._statements(handler.body)
                    alternatives.append(self._snapshot())
                self._merge(alternatives)
                self._statements(statement.finalbody)
                continue
            if isinstance(statement, ast.Match):
                _, sensitive = self._expression(statement.subject)
                incoming = self._snapshot()
                alternatives = [incoming]
                for case in statement.cases:
                    self._restore(incoming)
                    self._bind(case.pattern, None, sensitive)
                    self._expression(case.guard)
                    self._statements(case.body)
                    alternatives.append(self._snapshot())
                self._merge(alternatives)
                continue
            if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for expression in (*statement.decorator_list, *statement.args.defaults):
                    self._expression(expression)
                for expression in statement.args.kw_defaults:
                    self._expression(expression)
                helper = _SensitivePreclassifier(
                    self.bindings,
                    self.budget,
                    self.helper_returns,
                )
                helper._statements(statement.body)
                if helper.return_values:
                    qualified_values = {
                        value[0] for value in helper.return_values
                    }
                    returned_qualified = (
                        next(iter(qualified_values))
                        if len(qualified_values) == 1
                        else None
                    )
                    self.helper_returns[statement.name] = (
                        returned_qualified,
                        any(value[1] for value in helper.return_values),
                    )
                self._bind(ast.Name(id=statement.name), statement.name, False)
                continue
            if isinstance(statement, ast.ClassDef):
                for expression in (*statement.decorator_list, *statement.bases):
                    self._expression(expression)
                for keyword in statement.keywords:
                    self._expression(keyword.value)
                self._statements(statement.body)
                self._bind(ast.Name(id=statement.name), statement.name, False)
                continue
            if isinstance(statement, ast.Return):
                self.return_values.append(
                    self._expression(statement.value)
                )
                break
            self._expression(statement)
            if isinstance(statement, (ast.Raise, ast.Break, ast.Continue)):
                break

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
) -> set[int]:
    helper_returns: dict[str, tuple[str | None, bool]] = {}
    for name, definition in helper_definitions.items():
        helper = _SensitivePreclassifier(
            aliases,
            budget,
            helper_returns,
        )
        helper._statements(definition.body)
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
    return _SensitivePreclassifier(
        aliases,
        budget,
        helper_returns,
    ).classify(statements)


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
        return _FlowValue("sequence", tuple(items))
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
    if value.kind == "sequence":
        return any(_flow_is_sensitive(item) for item in value.value)
    if value.kind == "mapping":
        return any(_flow_is_sensitive(item) for _, item in value.value)
    return False


def _flow_mapping_value(
    value: _FlowValue,
    key: object,
) -> _FlowValue | None:
    if value.kind != "mapping":
        return None
    for supplied_key, supplied_value in value.value:
        if supplied_key == key:
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
        elif isinstance(statement, (ast.Return, ast.Raise)):
            outcomes.add("terminal")
        elif isinstance(statement, ast.If):
            outcomes.update(_outer_loop_control_outcomes(statement.body))
            outcomes.update(_outer_loop_control_outcomes(statement.orelse))
        elif isinstance(statement, (ast.With, ast.AsyncWith)):
            outcomes.update(_outer_loop_control_outcomes(statement.body))
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
class _FlowSuccessors:
    normal: list[dict[str, _FlowValue]]
    breaks: list[dict[str, _FlowValue]]
    continues: list[dict[str, _FlowValue]]
    returns: list[dict[str, _FlowValue]]
    raises: list[dict[str, _FlowValue]]

    @classmethod
    def empty(cls) -> "_FlowSuccessors":
        return cls([], [], [], [], [])


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
    ) -> None:
        self.budget = budget or _AnalysisBudget()
        self.values = {
            name: _flow_qname(qualified)
            for name, qualified in aliases.items()
        }
        self.local_functions = dict(local_functions)
        self.helper_returns = dict(helper_returns or {})
        self.flow = _ReviewFlow({}, {}, {}, {}, {}, {}, [])
        self.return_values: list[_FlowValue] = []
        for name, expression in module_assignments.items():
            self.values[name] = self._evaluate(expression, self.values, False)
        for name, definition in local_functions.items():
            returned = _trivial_helper_return(
                definition,
                _flow_aliases(self.values),
                self.budget,
            )
            if returned is not None:
                self.helper_returns[name] = returned
            sensitive = _contains_sensitive_runtime(
                definition,
                self.budget,
            )
            self.values[name] = _FlowValue(
                "qname",
                name,
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
        if callable_name is not None:
            self.flow.callables_by_call[id(node)] = callable_name
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
        self.budget.consume()
        if node is None:
            return _FlowValue("scalar", None)
        if isinstance(node, ast.Constant):
            return _FlowValue("scalar", node.value)
        if isinstance(node, ast.Name):
            return values.get(node.id, _flow_qname(node.id))
        if isinstance(node, ast.Attribute):
            qualified = _qualified_name(node)
            if qualified is not None and qualified in values:
                return values[qualified]
            base = self._evaluate(node.value, values, record)
            stored = _flow_mapping_value(base, node.attr)
            if stored is not None:
                return stored
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
            index = self._evaluate(node.slice, values, record)
            if index.kind == "scalar":
                stored = _flow_mapping_value(base, index.value)
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
        if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
            self.budget.container(len(node.elts))
            return _FlowValue(
                "sequence",
                tuple(self._evaluate(item, values, record) for item in node.elts),
            )
        if isinstance(node, ast.Dict):
            self.budget.container(len(node.keys))
            additions: dict[str, str] = {}
            inherited = False
            items: list[tuple[str, _FlowValue]] = []
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
                    if unresolved_reason is None:
                        unresolved_reason = "mapping expansion is unresolved"
                    unresolved_sensitive |= _flow_is_sensitive(expanded)
                    continue
                key = self._evaluate(key_node, values, record)
                value = self._evaluate(value_node, values, record)
                unresolved_sensitive |= (
                    _flow_is_sensitive(key) or _flow_is_sensitive(value)
                )
                if key.kind != "scalar" or type(key.value) is not str:
                    if unresolved_reason is None:
                        unresolved_reason = "mapping key is unresolved"
                    unresolved_sensitive |= (
                        _flow_is_sensitive(key) or _flow_is_sensitive(value)
                    )
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
            return _flow_unknown(
                "binary value is dynamically unresolved",
                sensitive=_flow_is_sensitive(left) or _flow_is_sensitive(right),
            )
        if isinstance(node, ast.BoolOp):
            evaluated = [
                self._evaluate(item, values, record)
                for item in node.values
            ]
            if all(item.kind == "scalar" for item in evaluated):
                result = evaluated[0].value
                for item in evaluated[1:]:
                    if isinstance(node.op, ast.And):
                        result = item.value if result else result
                    else:
                        result = result if result else item.value
                return _FlowValue("scalar", result)
            if any(_flow_is_sensitive(item) for item in evaluated):
                return _flow_unknown(
                    "mixed protected receiver is dynamically unresolved",
                    sensitive=True,
                )
            return _flow_unknown("boolean value is dynamically unresolved")
        if isinstance(node, ast.IfExp):
            test = self._evaluate(node.test, values, record)
            if test.kind == "scalar" and type(test.value) is bool:
                chosen = node.body if test.value else node.orelse
                return self._evaluate(chosen, values, record)
            first_values = dict(values)
            second_values = dict(values)
            first = self._evaluate(node.body, first_values, record)
            second = self._evaluate(node.orelse, second_values, record)
            values.clear()
            values.update(self._merge_states((first_values, second_values)))
            return _merge_flow_values("conditional expression", (first, second))
        if isinstance(node, ast.NamedExpr):
            value = self._evaluate(node.value, values, record)
            self._assign(node.target, value, values)
            return value
        if isinstance(node, ast.Lambda):
            return _FlowValue(
                "callback",
                node,
                _contains_sensitive_runtime(node.body, self.budget),
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
            returned = self.helper_returns.get(str(callable_name))
            if returned is not None and not node.args and not node.keywords:
                if returned.kind in {"sequence", "mapping"}:
                    self.budget.container(len(returned.value))
                return returned
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
            if callable_name in _SAFE_OBSERVATION_CALLS:
                return _flow_unknown("observation result is dynamically unresolved")
            if callable_name in _SAFE_MOCK_FACTORIES:
                return _FlowValue("object", "unittest.mock.Mock()")
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
            if callable_name is not None and _is_sensitive_namespace(callable_name):
                return _FlowValue(
                    "object",
                    f"{callable_name}()",
                    sensitive=True,
                )
            if any(
                _flow_is_sensitive(value)
                for value in (*argument_values, *keyword_values)
            ):
                return _flow_unknown(
                    "dynamic sensitive call result is unresolved",
                    sensitive=True,
                )
            return _flow_unknown("call result is dynamically unresolved")
        if isinstance(
            node,
            (ast.ListComp, ast.SetComp, ast.GeneratorExp, ast.DictComp),
        ):
            repeated: int | None = 1
            local_values = dict(values)
            may_skip_evaluation = False
            for generator in node.generators:
                if repeated == 0:
                    break
                iterator = self._evaluate(generator.iter, local_values, record)
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
                self._assign(generator.target, iteration_value, local_values)
                for condition in generator.ifs:
                    condition_value = self._evaluate(
                        condition,
                        local_values,
                        record,
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
                if repeated == 0:
                    break
            expressions = (
                (node.key, node.value)
                if isinstance(node, ast.DictComp)
                else (node.elt,)
            )
            values_out = (
                []
                if repeated == 0
                else [
                    self._evaluate(expression, local_values, record)
                    for expression in expressions
                ]
            )
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
                        and local_values[name].kind == "qname"
                        and values[name] != local_values[name]
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
            return _FlowValue("sequence", tuple(values_out) * repeated)
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
        member_path = self._member_path(target, values)
        if member_path is not None:
            root, path = member_path
            current = values.get(root)
            if (
                current is not None
                and current.kind in {"qname", "object"}
                and all(type(item) is str for item in path)
            ):
                values[".".join((root, *path))] = value
                return
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
            else:
                self.flow.standalone_blockers.append((
                    target,
                    "protected value store target is dynamically unresolved",
                ))

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
            if isinstance(candidate, (ast.Call, ast.Await)):
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

        return _FlowSuccessors(
            merged(supplied.normal),
            merged(supplied.breaks),
            merged(supplied.continues),
            merged(supplied.returns),
            merged(supplied.raises),
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
        current = self._statements((statement,), dict(values))
        raised = (
            [dict(current)]
            if any(self._expression_may_raise(node) for node in expressions)
            else []
        )
        return _FlowSuccessors([current], [], [], [], raised)

    def _flow_statement(
        self,
        statement: ast.stmt,
        values: dict[str, _FlowValue],
    ) -> _FlowSuccessors:
        self.budget.consume()
        if isinstance(statement, ast.Return):
            current = self._statements((statement,), dict(values))
            raised = (
                [dict(current)]
                if self._expression_may_raise(statement.value)
                else []
            )
            return _FlowSuccessors([], [], [], [current], raised)
        if isinstance(statement, ast.Raise):
            current = self._statements((statement,), dict(values))
            return _FlowSuccessors([], [], [], [], [current])
        if isinstance(statement, ast.Break):
            return _FlowSuccessors([], [dict(values)], [], [], [])
        if isinstance(statement, ast.Continue):
            return _FlowSuccessors([], [], [dict(values)], [], [])
        if isinstance(statement, ast.If):
            current = dict(values)
            test = self._evaluate(statement.test, current)
            result = _FlowSuccessors.empty()
            if self._expression_may_raise(statement.test):
                result.raises.append(dict(current))
            if test.kind == "scalar" and type(test.value) is bool:
                branches = (
                    statement.body if test.value else statement.orelse,
                )
            else:
                branches = (statement.body, statement.orelse)
            for branch in branches:
                self._extend_successors(
                    result,
                    self._flow_statements(branch, current),
                )
            return self._coalesce_successors(result)
        if isinstance(statement, (ast.With, ast.AsyncWith)):
            current = dict(values)
            result = _FlowSuccessors.empty()
            for item in statement.items:
                supplied = self._evaluate(item.context_expr, current)
                if item.optional_vars is not None:
                    self._assign(item.optional_vars, supplied, current)
                if self._expression_may_raise(item.context_expr):
                    result.raises.append(dict(current))
            self._extend_successors(
                result,
                self._flow_statements(statement.body, current),
            )
            return self._coalesce_successors(result)
        if isinstance(statement, (ast.For, ast.AsyncFor)):
            current = dict(values)
            iterator = self._evaluate(statement.iter, current)
            result = _FlowSuccessors.empty()
            if self._expression_may_raise(statement.iter):
                result.raises.append(dict(current))
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
            current = dict(values)
            test = self._evaluate(statement.test, current)
            result = _FlowSuccessors.empty()
            if self._expression_may_raise(statement.test):
                result.raises.append(dict(current))
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
                after_state = dict(state)
                after = self._evaluate(statement.test, after_state, False)
                if self._expression_may_raise(statement.test):
                    result.raises.append(dict(after_state))
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
            current = dict(values)
            subject = self._evaluate(statement.subject, current)
            result = _FlowSuccessors.empty()
            if self._expression_may_raise(statement.subject):
                result.raises.append(dict(current))
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
                    guard = self._evaluate(case.guard, case_state)
                    if self._expression_may_raise(case.guard):
                        result.raises.append(dict(case_state))
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
                raised = self._merge_states(body.raises)
                for handler in statement.handlers:
                    handler_state = self._exceptional_environment_state(
                        dict(raised)
                    )
                    self._evaluate(handler.type, handler_state)
                    if self._expression_may_raise(handler.type):
                        result.raises.append(dict(handler_state))
                    self._extend_successors(
                        result,
                        self._flow_statements(handler.body, handler_state),
                    )
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
            for state in getattr(incoming, kind):
                final = self._flow_statements(statements, state)
                if kind == "normal":
                    result.normal.extend(final.normal)
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
                for expression in (*statement.decorator_list, *statement.args.defaults):
                    self._evaluate(expression, values)
                for expression in statement.args.kw_defaults:
                    self._evaluate(expression, values)
                values[statement.name] = _FlowValue(
                    "qname",
                    statement.name,
                    _contains_sensitive_runtime(statement, self.budget),
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
            if _statements_terminate_without_fallthrough(statement.body):
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
) -> _FlowValue | None:
    execution = _execution_scope(definition, budget)
    resolver = _SourceOrderedResolver(
        aliases,
        module_assignments,
        execution.local_functions,
        budget=budget,
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
) -> _ReviewFlow:
    return _SourceOrderedResolver(
        aliases,
        module_assignments,
        local_functions,
        sensitive_helper_names,
        helper_returns,
        budget,
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
        program_helper_returns = {
            name: returned
            for name, definition in program_execution.local_functions.items()
            for returned in (
                _source_ordered_helper_return(
                    definition,
                    program_aliases,
                    program_assignments,
                    analysis_budget,
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
    analysis_budget: _AnalysisBudget | None = None,
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
    sensitive_helper_names: set[str] = set()
    helper_returns: dict[str, _FlowValue] = {}
    for name in referenced_names:
        definition = helper_registry.get(f"{relative_path}::{name}")
        if definition is None:
            continue
        returned = _source_ordered_helper_return(
            definition.node,
            definition.aliases,
            definition.module_assignments,
            analysis_budget,
        )
        if returned is not None:
            helper_returns[name] = returned
        if _helper_has_sensitive_closure(
            definition,
            helper_registry,
            budget=analysis_budget,
        ):
            sensitive_helper_names.add(name)
    source_flow = _source_ordered_review_flow(
        node,
        aliases,
        module_assignments,
        execution.local_functions,
        frozenset(sensitive_helper_names),
        helper_returns,
        analysis_budget,
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
    blockers.extend(
        _review_blocker(item_id, relative_path, call, reason)
        for call, reason in execution.closure_blockers
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
    )
    resolved_sensitive_calls: set[int] = set()
    dispositions: dict[int, str] = {}
    for call in execution.calls:
        if (
            id(call) in sensitive_calls
            and id(call) not in source_flow.aliases_by_call
        ):
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
        if function in _SUBPROCESS_FUNCTIONS:
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
        elif (
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
        flow_blocker = source_flow.blockers_by_call.get(id(call))
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
                analysis_budget=analysis_budget,
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
                active_helpers=active_helpers | {helper_key},
                analyzed_sites=analyzed_sites,
                helper_edges=helper_edges,
                closure_depth=closure_depth + 1,
                closure_helper_key=helper_key,
                analysis_budget=analysis_budget,
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

        publish_with_attributes._governance_destination_paths = (profile_path,)

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

            publish_pair._governance_destination_paths = (
                inventory_path,
                profile_path,
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
