"""Deterministically derive and guard the evidence-boundary manifests.

This tool is standard-library-only and deliberately does not import pontius.
"""

from __future__ import annotations

import argparse
import ast
from collections.abc import Mapping, Sequence
import errno
from hashlib import sha256
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
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

if os.name == "nt":
    import ctypes
    from ctypes import wintypes


BASELINE_COMMIT = "a842c4b6a73a2991a63a481f4107580b72750582"
GIT_EXECUTABLE = Path("C:/Program Files/Git/cmd/git.exe")
MANIFEST_PATHS = (
    "docs/architecture/sealed-current-files.toml",
    "docs/architecture/sealed-current-absences.toml",
    "docs/architecture/historical-blobs.toml",
    "docs/architecture/retained-v7.toml",
)

CURRENT_FILE_ENTRIES = (
    {"relative_path": "artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v2.jsonl", "byte_length": 3299268, "raw_sha256": "67ac14d408fe8c4299ee603ec1d8c454975094507d4ac28cda73001a42feb90d", "role": "retained_result", "governing_decision": "ADR-0462", "owner": "compiled_global_separation_calibration_v2"},
    {"relative_path": "artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v5.attempt.json", "byte_length": 606, "raw_sha256": "104820d0c67391365d18fb76ca72c704e40e467e2993a96c618d4bf91155600d", "role": "retained_attempt", "governing_decision": "ADR-0470", "owner": "compiled_global_separation_calibration_v5"},
    {"relative_path": "experiments/configs/legal-river-quotient-compiled-global-separation-calibration-v9-corrected-invocation-authorization.json", "byte_length": 482, "raw_sha256": "57c869df38c23e4c0520730986a65825f51814915f68cc3e4d32a2f39303a535", "role": "rejected_authorization", "governing_decision": "ADR-0473", "owner": "compiled_global_separation_calibration_v6"},
    {"relative_path": "artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v7.jsonl", "byte_length": 7858857, "raw_sha256": "78b2f8351ca49785756ec336d4f967bcc83a86f9ef96506a6144726cf3b312b3", "role": "retained_result", "governing_decision": "ADR-0476", "owner": "compiled_global_separation_calibration_v7"},
    {"relative_path": "artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v7.attempt.json", "byte_length": 1825, "raw_sha256": "ada1896f0bf63111e0c1e5e707315fbca6c13f6e2b63222805cb5ef4cb9dc413", "role": "retained_attempt", "governing_decision": "ADR-0476", "owner": "compiled_global_separation_calibration_v7"},
    {"relative_path": "artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v7.launch-consumed.json", "byte_length": 349, "raw_sha256": "c3c0a34cba6a677157034d8f8109cf47edea496a33c64992293176d879a2d629", "role": "consumed_launch_marker", "governing_decision": "ADR-0476", "owner": "compiled_global_separation_calibration_v7"},
)

CURRENT_ABSENCE_ENTRIES = (
    {"relative_path": "artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v3.jsonl", "role": "closed_result_absence", "governing_decision": "ADR-0466", "owner": "compiled_global_separation_calibration_v3"},
    {"relative_path": "artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v4.jsonl", "role": "closed_result_absence", "governing_decision": "ADR-0469", "owner": "compiled_global_separation_calibration_v4"},
    {"relative_path": "artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v4.attempt.json", "role": "closed_attempt_absence", "governing_decision": "ADR-0469", "owner": "compiled_global_separation_calibration_v4"},
    {"relative_path": "artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v4.launch-pending.json", "role": "closed_launch_pending_absence", "governing_decision": "ADR-0469", "owner": "compiled_global_separation_calibration_v4"},
    {"relative_path": "artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v4.launch-consumed.json", "role": "closed_launch_consumed_absence", "governing_decision": "ADR-0469", "owner": "compiled_global_separation_calibration_v4"},
    {"relative_path": "artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v4.launch-aborted.json", "role": "closed_launch_aborted_absence", "governing_decision": "ADR-0469", "owner": "compiled_global_separation_calibration_v4"},
    {"relative_path": "artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v5.jsonl", "role": "closed_result_absence", "governing_decision": "ADR-0470", "owner": "compiled_global_separation_calibration_v5"},
    {"relative_path": "artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v5.launch-pending.json", "role": "closed_launch_pending_absence", "governing_decision": "ADR-0470", "owner": "compiled_global_separation_calibration_v5"},
    {"relative_path": "artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v5.launch-consumed.json", "role": "closed_launch_consumed_absence", "governing_decision": "ADR-0470", "owner": "compiled_global_separation_calibration_v5"},
    {"relative_path": "artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v5.launch-aborted.json", "role": "closed_launch_aborted_absence", "governing_decision": "ADR-0470", "owner": "compiled_global_separation_calibration_v5"},
    {"relative_path": "experiments/configs/legal-river-quotient-compiled-global-separation-calibration-v8-corrected-invocation-authorization.json", "role": "rejected_authorization_absence", "governing_decision": "ADR-0473", "owner": "compiled_global_separation_calibration_v6"},
    {"relative_path": "artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v6.jsonl", "role": "closed_result_absence", "governing_decision": "ADR-0473", "owner": "compiled_global_separation_calibration_v6"},
    {"relative_path": "artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v6.attempt.json", "role": "closed_attempt_absence", "governing_decision": "ADR-0473", "owner": "compiled_global_separation_calibration_v6"},
    {"relative_path": "artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v6.launch-pending.json", "role": "closed_launch_pending_absence", "governing_decision": "ADR-0473", "owner": "compiled_global_separation_calibration_v6"},
    {"relative_path": "artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v6.launch-consumed.json", "role": "closed_launch_consumed_absence", "governing_decision": "ADR-0473", "owner": "compiled_global_separation_calibration_v6"},
    {"relative_path": "artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v6.launch-aborted.json", "role": "closed_launch_aborted_absence", "governing_decision": "ADR-0473", "owner": "compiled_global_separation_calibration_v6"},
    {"relative_path": "artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v7.launch-pending.json", "role": "closed_launch_pending_absence", "governing_decision": "ADR-0476", "owner": "compiled_global_separation_calibration_v7"},
    {"relative_path": "artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v7.launch-aborted.json", "role": "closed_launch_aborted_absence", "governing_decision": "ADR-0476", "owner": "compiled_global_separation_calibration_v7"},
)

SNAPSHOTS = (
    {"phase": "base_source_seal", "commit": "88148da07324c13b79c72ea494b14167a975c001", "root_tree_oid": "bc5d1952f690da5d49275344919de36224af26cb", "governing_decision": "ADR-0458"},
    {"phase": "v2_source_seal", "commit": "08bb6857f47f9669b8f531c65079d4decd52a573", "root_tree_oid": "0d01a4133a4e6ab10467ad0bd298630149702a73", "governing_decision": "ADR-0461"},
    {"phase": "v2_retained_rejection", "commit": "3de8e0c9eebf67f2cc2573041242a869468de6e9", "root_tree_oid": "ea80b86ac60cb324e3c18ddad83d8bbba0ade933", "governing_decision": "ADR-0462"},
    {"phase": "v3_source_seal", "commit": "77feb7c78990ca53e70b1302a6866fe5d781411f", "root_tree_oid": "d26ba99c033875342a652ae352067beee1ca44ee", "governing_decision": "ADR-0465"},
    {"phase": "v4_source_seal", "commit": "ba6a3418b7c991238cc1a65898fd61fa03b4a3cb", "root_tree_oid": "73b53cb04c91459e8b7028ccd292b972d2dfdf69", "governing_decision": "ADR-0467"},
    {"phase": "v4_authorization_rejection", "commit": "815d23c115289347e3d4028a4866eb9f87d4669a", "root_tree_oid": "894c026603156df4bba1134ba9861e98bd3a6663", "governing_decision": "ADR-0468"},
    {"phase": "v5_retained_attempt", "commit": "5c0c9a401e5f2ebf59296832d954d0075c4d4624", "root_tree_oid": "f3418410c442a4d06c62aba9777def72633ca5c5", "governing_decision": "ADR-0470"},
    {"phase": "v6_source_seal", "commit": "d633f3fb469a27dee688587293c6efb1d2cb2757", "root_tree_oid": "9c9ff658c2836bde5d1df71f5596d1d6aa1a5bd2", "governing_decision": "ADR-0471"},
    {"phase": "v6_authorization_rejection", "commit": "cbfa3598f22c7aba7d824f71356ca156f8b01b0c", "root_tree_oid": "9873ff13131c91b058307643dc838a8452268fbb", "governing_decision": "ADR-0472"},
    {"phase": "v7_source_seal", "commit": "56127da2970f5a8a8056a97a247ebe1fdf4b983b", "root_tree_oid": "ee2437ba1b2efbf2dc4ab3c21bbacdbf26c58648", "governing_decision": "ADR-0474"},
    {"phase": "v7_live_authorization", "commit": "aaca2dda40e29be8ebd091d58e7853bce1c62fd8", "root_tree_oid": "e7bd077f40b1970e9b40a83c891996ab02cd5ffd", "governing_decision": "ADR-0475"},
    {
        "phase": "v0a_evaluation_legacy",
        "commit": "363c9fb669e19a30375537ee5e92ea338a840a2d",
        "root_tree_oid": "10cc82ff78a84ef901242b2f69540f6a74ec498b",
        "governing_decision": "ADR-0512",
    },
)

LEGACY_EVALUATION_TEST_PATHS = (
    "tests/test_v0a_evaluation_boundary.py",
    "tests/test_v0a_evaluation_runner.py",
    "tests/test_v0a_evaluation_v2.py",
)

EARLIER_PHASES = (
    {**SNAPSHOTS[0], "selected_test": "tests/test_legal_river_quotient_compiled_global_separation_calibration.py", "selected_class": "CompiledGlobalSeparationSourceSealTests", "decision_path": "docs/decisions/ADR-0458-source-seal-the-compiled-global-separation-calibration.md"},
    {**SNAPSHOTS[1], "selected_test": "tests/test_legal_river_quotient_compiled_global_separation_calibration_v2.py", "selected_class": "AbsoluteGitCalibrationSuccessorTests", "decision_path": "docs/decisions/ADR-0461-source-seal-the-absolute-git-compiled-calibration-successor.md"},
    {**SNAPSHOTS[2], "selected_test": "tests/test_legal_river_quotient_compiled_global_separation_calibration_v2_outcome.py", "selected_class": "CompiledGlobalSeparationCalibrationV2OutcomeTests", "decision_path": "docs/decisions/ADR-0462-retain-the-timed-rrns-direct-launch-arity-rejection.md"},
    {**SNAPSHOTS[3], "selected_test": "tests/test_legal_river_quotient_compiled_global_separation_calibration_v3.py", "selected_class": "CompiledGlobalSeparationCalibrationV3Tests", "decision_path": "docs/decisions/ADR-0465-source-seal-the-kernel-launch-arity-successor.md"},
    {**SNAPSHOTS[4], "selected_test": "tests/test_legal_river_quotient_compiled_global_separation_calibration_v4.py", "selected_class": "CompiledGlobalSeparationCalibrationV4Tests", "decision_path": "docs/decisions/ADR-0467-source-seal-the-deferred-science-import-successor.md"},
    {**SNAPSHOTS[5], "selected_test": "tests/test_legal_river_quotient_compiled_global_separation_calibration_v4.py", "selected_class": "CompiledGlobalSeparationCalibrationV4Tests", "decision_path": "docs/decisions/ADR-0468-authorize-one-deferred-import-calibration-invocation.md"},
    {**SNAPSHOTS[6], "selected_test": "tests/test_legal_river_quotient_compiled_global_separation_calibration_v5.py", "selected_class": "CompiledGlobalSeparationCalibrationV5Tests", "decision_path": "docs/decisions/ADR-0470-retain-the-accidental-v5-preauthorization-attempt.md"},
    {**SNAPSHOTS[7], "selected_test": "tests/test_legal_river_quotient_compiled_global_separation_calibration_v6.py", "selected_class": "CompiledGlobalSeparationCalibrationV6Tests", "decision_path": "docs/decisions/ADR-0471-source-seal-the-retained-attempt-successor.md"},
    {**SNAPSHOTS[8], "selected_test": "tests/test_legal_river_quotient_compiled_global_separation_calibration_v6.py", "selected_class": "CompiledGlobalSeparationCalibrationV6Tests", "decision_path": "docs/decisions/ADR-0472-authorize-one-v6-retained-attempt-calibration-invocation.md"},
)

V7_AUTHORIZATION_PATHS = (
    "ARCHITECTURE.md", "RISK_REGISTER.md", "ROADMAP.md", "STATUS.md",
    "docs/decisions/ADR-0475-authorize-one-v7-authorization-phase-calibration-invocation.md",
    "experiments/configs/legal-river-quotient-compiled-global-separation-calibration-v11-authorization-phase-corrected-invocation-authorization.json",
)

EXPECTED_NULL_CLAIM_PATHS = (
    "$.arithmetic_schedule_selected", "$.candidate_selected", "$.claims.action_clock_result",
    "$.claims.arithmetic_schedule_selected", "$.claims.blueprint_result", "$.claims.candidate_selected",
    "$.claims.compiled_calibration_result", "$.claims.decision_quality_result",
    "$.claims.literal_45_numerical_result", "$.claims.material_zeta_speed_claim",
    "$.claims.poker_strength_result", "$.claims.production_base_numerical_admission",
    "$.claims.resolver_iteration_result", "$.claims.symbolic_45_primitive_projection",
    "$.claims.topology_selected", "$.topology_selected",
)

RETAINED_V7 = {
    "schema_version": "pontius-retained-v7-v1",
    "source_seal_commit": SNAPSHOTS[9]["commit"], "authorization_commit": SNAPSHOTS[10]["commit"],
    "historical_reader_commit": SNAPSHOTS[10]["commit"],
    "journal_protocol_sha256": "2dc6cd5636ca56b4b3b17592860737489a2bf1705de79a75bd395fa309b72272",
    "campaign_sha256": "669a959827590b883277840161cd2cdabbed18687ad390f6667bc312362fd23d",
    "record_count": 592, "observation_count": 590, "calibration_cell_count": 569,
    "warmup_cell_count": 480, "measured_labelled_partial_cell_count": 89,
    "terminal": "laboratory_wall_rejected", "journal_complete": True,
    "scientific_campaign_complete": False, "scientific_call_count": 569,
    "authoritative_measured_call_count": 0, "passed": False,
    "laboratory_elapsed_ns": 1510053980800, "laboratory_wall_ns": 1500000000000,
    "outside_laboratory_elapsed_ns": 48722365700, "outside_laboratory_wall_ns": 300000000000,
    "public_elapsed_ns": 1558776346500, "public_wall_ns": 1800000000000,
    "fit_projection_present": False, "production_base_classification": "producer_absent",
    "candidate_selection_present": False, "topology_selection_present": False,
    "arithmetic_schedule_selection_present": False, "truncation_authorized": False,
    "historical_blobs_manifest_path": "docs/architecture/historical-blobs.toml",
    "absent_launch_paths": (
        "artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v7.launch-aborted.json",
        "artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v7.launch-pending.json",
    ),
    "expected_null_claim_paths": EXPECTED_NULL_CLAIM_PATHS,
    "result": {key: value for key, value in CURRENT_FILE_ENTRIES[3].items() if key in {"relative_path", "byte_length", "raw_sha256", "role"}},
    "attempt": {key: value for key, value in CURRENT_FILE_ENTRIES[4].items() if key in {"relative_path", "byte_length", "raw_sha256", "role"}},
    "consumed_launch": {key: value for key, value in CURRENT_FILE_ENTRIES[5].items() if key in {"relative_path", "byte_length", "raw_sha256", "role"}},
}

_HEX40 = re.compile(r"[0-9a-f]{40}\Z")
_HEX64 = re.compile(r"[0-9a-f]{64}\Z")
_REPARSE_ATTRIBUTE = 0x400


class GenerationError(RuntimeError):
    """A fail-closed generator error."""

    def __init__(
        self,
        message: str,
        *,
        failures: Sequence[BaseException] = (),
        retained_owners: Sequence[object] = (),
    ) -> None:
        super().__init__(message)
        self.failures = tuple(failures)
        self.retained_owners = tuple(retained_owners)


def _aggregate_generation_errors(
    message: str,
    failures: Sequence[BaseException],
    *,
    retained_owners: Sequence[object] = (),
) -> GenerationError:
    supplied_failures = tuple(failures)
    if not supplied_failures:
        raise ValueError("generation error aggregation requires at least one failure")
    owners: list[object] = []
    for owner in retained_owners:
        if not any(existing is owner for existing in owners):
            owners.append(owner)

    ordered_failures: list[BaseException] = []

    def append_failure(failure: BaseException) -> None:
        if isinstance(failure, GenerationError):
            for owner in failure.retained_owners:
                if not any(existing is owner for existing in owners):
                    owners.append(owner)
            if failure.failures:
                for nested in failure.failures:
                    append_failure(nested)
                return
        ordered_failures.append(failure)

    for failure in supplied_failures:
        append_failure(failure)
    detail = "; ".join(
        f"{type(failure).__name__}: {failure}" for failure in ordered_failures
    )
    return GenerationError(
        f"{message}: {detail}",
        failures=tuple(ordered_failures),
        retained_owners=owners,
    )


def canonical_semantic_bytes(value: object) -> bytes:
    return json.dumps(
        _normalize_semantic(value, "$"),
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")


def semantic_sha256(value: object) -> str:
    return sha256(canonical_semantic_bytes(value)).hexdigest()


def _normalize_semantic(value: object, path: str) -> object:
    if value is None or type(value) in (bool, int, str):
        return value
    if isinstance(value, (list, tuple)):
        return [_normalize_semantic(item, f"{path}[{index}]") for index, item in enumerate(value)]
    if isinstance(value, Mapping):
        normalized: dict[str, object] = {}
        for key in sorted(value):
            if type(key) is not str:
                raise TypeError(f"semantic mapping key at {path} must be a string")
            normalized[key] = _normalize_semantic(value[key], f"{path}.{key}")
        return normalized
    raise TypeError(f"unsupported semantic value at {path}: {type(value).__name__}")


def _identity(info: Any) -> tuple[int, ...]:
    return (
        int(info.st_dev),
        int(info.st_ino),
        int(info.st_size),
        int(info.st_mtime_ns),
        int(info.st_ctime_ns),
        int(info.st_mode),
        int(getattr(info, "st_file_attributes", 0)),
        int(getattr(info, "st_reparse_tag", 0)),
    )


def _path_handle_identity(info: Any) -> tuple[int, ...]:
    """Fields Windows reports consistently through both lstat and fstat."""
    return (
        int(info.st_dev),
        int(info.st_ino),
        int(info.st_size),
        int(info.st_mtime_ns),
        int(info.st_mode),
        int(getattr(info, "st_file_attributes", 0)),
        int(getattr(info, "st_reparse_tag", 0)),
    )


def _is_reparse(info: Any) -> bool:
    return bool(int(getattr(info, "st_file_attributes", 0)) & _REPARSE_ATTRIBUTE) or bool(
        int(getattr(info, "st_reparse_tag", 0))
    )


class _ToolSecureReader:
    """Reusable tool-local secure-reader seam for the future active reader."""

    def read_regular_once(self, path: Path, *, maximum_bytes: int) -> bytes:
        return _read_regular_file_once(path, maximum_bytes=maximum_bytes)


def tool_secure_reader_factory() -> _ToolSecureReader:
    return _ToolSecureReader()


def _read_regular_file_once(path: Path, *, maximum_bytes: int) -> bytes:
    """Read one bounded snapshot from a regular nonlink/nonreparse path."""
    if (
        type(maximum_bytes) is not int
        or maximum_bytes < 0
        or not isinstance(path, Path)
        or not path.is_absolute()
    ):
        raise GenerationError("secure read arguments are invalid")
    for component in reversed(path.parents):
        if component == component.parent:
            continue
        try:
            component_info = os.lstat(component)
        except OSError as error:
            raise GenerationError(f"evidence path component cannot be inspected: {component}") from error
        if stat.S_ISLNK(component_info.st_mode) or _is_reparse(component_info):
            raise GenerationError(f"evidence path has a link or reparse component: {component}")
    try:
        before_path = os.lstat(path)
    except OSError as error:
        raise GenerationError(f"evidence path cannot be inspected: {path}") from error
    if (
        stat.S_ISLNK(before_path.st_mode)
        or _is_reparse(before_path)
        or not stat.S_ISREG(before_path.st_mode)
    ):
        raise GenerationError(f"evidence path is not a regular nonreparse file: {path}")
    if before_path.st_size > maximum_bytes:
        raise GenerationError(f"evidence file exceeds its bounded read: {path}")
    flags = (
        os.O_RDONLY
        | getattr(os, "O_BINARY", 0)
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOINHERIT", 0)
    )
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags)
    except OSError as error:
        raise GenerationError(f"evidence path cannot be opened without following links: {path}") from error
    try:
        before_handle = os.fstat(descriptor)
        if not stat.S_ISREG(before_handle.st_mode) or _is_reparse(before_handle):
            raise GenerationError(f"opened evidence handle is not regular: {path}")
        if _path_handle_identity(before_path) != _path_handle_identity(before_handle):
            raise GenerationError(f"evidence path changed while opening: {path}")
        raw = os.read(descriptor, maximum_bytes + 1)
        after_handle = os.fstat(descriptor)
        if len(raw) > maximum_bytes:
            raise GenerationError(f"evidence file exceeds its bounded read: {path}")
        if len(raw) != before_handle.st_size or _identity(before_handle) != _identity(after_handle):
            raise GenerationError(f"opened evidence file changed during its single read: {path}")
    finally:
        if descriptor >= 0:
            os.close(descriptor)
    try:
        after_path = os.lstat(path)
    except OSError as error:
        raise GenerationError(f"evidence path disappeared after reading: {path}") from error
    if (
        stat.S_ISLNK(after_path.st_mode)
        or _is_reparse(after_path)
        or _path_handle_identity(after_path) != _path_handle_identity(after_handle)
    ):
        raise GenerationError(f"evidence path identity changed after reading: {path}")
    return raw


def read_regular_file_once(path: Path, *, maximum_bytes: int) -> bytes:
    return tool_secure_reader_factory().read_regular_once(path, maximum_bytes=maximum_bytes)


def git_environment(private_home: Path) -> dict[str, str]:
    if not isinstance(private_home, Path) or not private_home.is_absolute():
        raise GenerationError("Git private home must be absolute")
    allowed = ("SystemRoot", "WINDIR", "ComSpec", "PATHEXT", "TEMP", "TMP", "TMPDIR")
    source = {key.casefold(): value for key, value in os.environ.items()}
    environment = {key: source[key.casefold()] for key in allowed if key.casefold() in source}
    environment["HOME"] = str(private_home)
    environment["USERPROFILE"] = str(private_home)
    system_root = Path(os.environ.get("SystemRoot", "C:/Windows"))
    environment["PATH"] = os.pathsep.join((str(GIT_EXECUTABLE.parent), str(system_root / "System32")))
    environment.update(
        {
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": "NUL" if os.name == "nt" else "/dev/null",
            "GIT_NO_REPLACE_OBJECTS": "1",
            "GIT_LITERAL_PATHSPECS": "1",
        }
    )
    return environment


def _validated_bound_executable(
    executable: Path = GIT_EXECUTABLE, expected_identity: tuple[int, ...] | None = None
) -> tuple[Path, tuple[int, ...]]:
    try:
        resolved = executable.resolve(strict=True)
    except OSError as error:
        raise GenerationError("the bound Git executable is unavailable") from error
    if os.path.normcase(str(resolved)) != os.path.normcase(str(executable)):
        raise GenerationError("the bound Git executable resolved to a different identity")
    for component in (resolved, *resolved.parents[:-1]):
        info = os.lstat(component)
        if stat.S_ISLNK(info.st_mode) or _is_reparse(info):
            raise GenerationError("the bound Git executable has a link or reparse component")
    info = os.lstat(resolved)
    if not stat.S_ISREG(info.st_mode):
        raise GenerationError("the bound Git executable is not regular")
    identity = _identity(info)
    if expected_identity is not None and identity != expected_identity:
        raise GenerationError("the bound Git executable identity changed")
    return resolved, identity


def _collect_bounded_process(
    process: Any, *, command: str, stdout_limit: int, stderr_limit: int, timeout: float
) -> tuple[bytes, bytes]:
    """Drain a child concurrently while retaining at most each declared bound."""
    outputs: dict[str, bytes] = {}
    exceeded = threading.Event()

    def drain(name: str, stream: Any, limit: int) -> None:
        chunks: list[bytes] = []
        remaining = limit
        while True:
            chunk = stream.read(min(65536, remaining + 1))
            if not chunk:
                break
            if len(chunk) > remaining:
                exceeded.set()
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        outputs[name] = b"".join(chunks)

    threads = (
        threading.Thread(target=drain, args=("stdout", process.stdout, stdout_limit), daemon=True),
        threading.Thread(target=drain, args=("stderr", process.stderr, stderr_limit), daemon=True),
    )
    for thread in threads:
        thread.start()
    deadline = time.monotonic() + timeout
    timed_out = False
    while True:
        if exceeded.is_set():
            process.kill()
            break
        remaining_time = deadline - time.monotonic()
        if remaining_time <= 0:
            timed_out = True
            process.kill()
            break
        try:
            process.wait(timeout=min(0.05, remaining_time))
            break
        except subprocess.TimeoutExpired:
            continue
    try:
        process.wait(timeout=1.0)
    except subprocess.TimeoutExpired:
        process.kill()
    for thread in threads:
        thread.join(timeout=1.0)
    process.stdout.close()
    process.stderr.close()
    if exceeded.is_set():
        raise GenerationError(f"Git command output exceeded its bound: {command}")
    if timed_out:
        raise GenerationError(f"Git command timed out: {command}")
    stdout = outputs.get("stdout", b"")
    stderr = outputs.get("stderr", b"")
    if process.returncode != 0:
        detail = stderr.decode("utf-8", "replace").strip()[:500]
        raise GenerationError(f"Git command failed ({command}): {detail}")
    return stdout, stderr


class _Git:
    def __init__(self, repository_root: Path, private_home: Path) -> None:
        self.root = repository_root.resolve(strict=True)
        self.executable, self.executable_identity = _validated_bound_executable()
        self.environment = git_environment(private_home)
        self._cache: dict[tuple[str, ...], bytes] = {}

    def _run(self, arguments: Sequence[str], *, maximum_stdout: int) -> bytes:
        if type(maximum_stdout) is not int or maximum_stdout < 0 or not arguments:
            raise GenerationError("Git command bounds are invalid")
        key = tuple(arguments)
        _validated_bound_executable(self.executable, self.executable_identity)
        if key in self._cache:
            cached = self._cache[key]
            if len(cached) > maximum_stdout:
                raise GenerationError(f"cached Git output exceeded its bound: {arguments[0]}")
            return cached
        try:
            process = subprocess.Popen(
                [str(self.executable), *arguments], cwd=self.root, env=self.environment,
                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                shell=False,
            )
        except OSError as error:
            raise GenerationError(f"Git command could not start: {arguments[0]}") from error
        stdout, _ = _collect_bounded_process(
            process, command=arguments[0], stdout_limit=maximum_stdout,
            stderr_limit=65536, timeout=10.0,
        )
        _validated_bound_executable(self.executable, self.executable_identity)
        self._cache[key] = stdout
        return stdout

    def root_tree_oid(self, commit: str) -> str:
        return self._oid(("rev-parse", "--verify", f"{commit}^{{tree}}"))

    def tracked_paths(self, commit: str) -> tuple[str, ...]:
        raw = self._run(
            ("ls-tree", "-r", "-z", "--name-only", commit, "--"),
            maximum_stdout=4 * 1024 * 1024,
        )
        if raw and not raw.endswith(b"\0"):
            raise GenerationError("Git tree path output is malformed")
        try:
            paths = tuple(part.decode("utf-8") for part in raw.split(b"\0") if part)
        except UnicodeDecodeError as error:
            raise GenerationError("Git tree path output is not UTF-8") from error
        if paths != tuple(sorted(paths)) or any(_relative_path(path) != path for path in paths):
            raise GenerationError("Git tree paths are malformed or unsorted")
        return paths

    def blob_oid(self, commit: str, relative_path: str) -> str:
        _relative_path(relative_path)
        return self._oid(("rev-parse", "--verify", f"{commit}:{relative_path}"))

    def show_blob(self, commit: str, relative_path: str) -> bytes:
        _relative_path(relative_path)
        return self._run(
            ("show", f"{commit}:{relative_path}", "--"),
            maximum_stdout=16 * 1024 * 1024,
        )

    def _oid(self, arguments: Sequence[str]) -> str:
        raw = self._run(arguments, maximum_stdout=256)
        try:
            value = raw.decode("ascii").strip()
        except UnicodeDecodeError as error:
            raise GenerationError("Git object identity is not ASCII") from error
        if _HEX40.fullmatch(value) is None:
            raise GenerationError("Git object identity is malformed")
        return value


def _relative_path(value: object) -> str:
    if (
        type(value) is not str
        or not value
        or PureWindowsPath(value).drive
        or value.startswith(("/", "\\"))
    ):
        raise GenerationError("repository path is invalid")
    candidate = PurePosixPath(value.replace("\\", "/"))
    if (
        candidate.is_absolute()
        or candidate.as_posix() in ("", ".")
        or any(part == ".." for part in candidate.parts)
    ):
        raise GenerationError("repository path escapes its root")
    return candidate.as_posix()


def _json_no_duplicates(raw: str) -> object:
    def pairs(values: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in values:
            if key in result:
                raise GenerationError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    try:
        return json.loads(
            raw,
            object_pairs_hook=pairs,
            parse_constant=lambda value: (_ for _ in ()).throw(
                GenerationError(f"invalid JSON constant: {value}")
            ),
        )
    except json.JSONDecodeError as error:
        raise GenerationError("retained journal header is invalid JSON") from error


def _module_path(module: str, tracked: set[str]) -> str | None:
    if not module.startswith("pontius"):
        return None
    stem = "src/" + module.replace(".", "/")
    for candidate in (stem + ".py", stem + "/__init__.py"):
        if candidate in tracked:
            return candidate
    return None


def _import_paths(tree: ast.AST, current_path: str, tracked: set[str]) -> set[str]:
    result: set[str] = set()
    current_parts = PurePosixPath(current_path).with_suffix("").parts
    current_module = ".".join(current_parts[1:]) if current_parts and current_parts[0] == "src" else ""
    current_package = current_module.rsplit(".", 1)[0] if "." in current_module else current_module
    for node in ast.walk(tree):
        modules: list[str] = []
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                package_parts = current_package.split(".") if current_package else []
                keep = max(0, len(package_parts) - node.level + 1)
                prefix = package_parts[:keep]
                if node.module:
                    prefix.extend(node.module.split("."))
                base = ".".join(prefix)
            else:
                base = node.module or ""
            modules.append(base)
            if base.startswith("pontius"):
                modules.extend(f"{base}.{alias.name}" for alias in node.names if alias.name != "*")
        for module in modules:
            path = _module_path(module, tracked)
            if path is not None:
                result.add(path)
            elif module.startswith("pontius") and module != "pontius" and not any(
                isinstance(node, ast.ImportFrom)
                and module.endswith("." + alias.name)
                for alias in node.names
                if alias.name != "*"
            ):
                raise GenerationError(f"unresolved local import {module!r} in {current_path}")
    return result


def _bound_names(node: ast.stmt) -> set[str]:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return {node.name}
    if isinstance(node, (ast.Import, ast.ImportFrom)):
        return {alias.asname or alias.name.split(".")[0] for alias in node.names}
    targets: list[ast.AST] = []
    if isinstance(node, (ast.Assign, ast.AnnAssign, ast.NamedExpr)):
        targets = list(node.targets) if isinstance(node, ast.Assign) else [node.target]
    result: set[str] = set()
    for target in targets:
        for item in ast.walk(target):
            if isinstance(item, ast.Name):
                result.add(item.id)
    return result


def _loaded_names(node: ast.AST) -> set[str]:
    return {
        item.id for item in ast.walk(node)
        if isinstance(item, ast.Name) and isinstance(item.ctx, ast.Load)
    }


def _selected_class_scope(tree: ast.AST, selected_class: str) -> ast.Module:
    if not isinstance(tree, ast.Module) or type(selected_class) is not str or not selected_class:
        raise GenerationError("selected class scope arguments are invalid")
    matches = [node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == selected_class]
    if len(matches) != 1:
        raise GenerationError(f"selected class is missing or ambiguous: {selected_class}")
    bindings: dict[str, ast.stmt] = {}
    for node in tree.body:
        if node is matches[0]:
            continue
        for name in _bound_names(node):
            if name in bindings:
                raise GenerationError(f"module binding is ambiguous in selected-class scope: {name}")
            bindings[name] = node
    selected_nodes: list[ast.stmt] = [matches[0]]
    pending = list(_loaded_names(matches[0]))
    included: set[int] = {id(matches[0])}
    required_import_bindings: dict[int, set[str]] = {}
    while pending:
        name = pending.pop()
        node = bindings.get(name)
        if node is None:
            continue
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            required_import_bindings.setdefault(id(node), set()).add(name)
        if id(node) in included:
            continue
        included.add(id(node))
        selected_nodes.append(node)
        pending.extend(_loaded_names(node))
    order = {id(node): index for index, node in enumerate(tree.body)}
    selected_nodes.sort(key=lambda node: order[id(node)])
    pruned: list[ast.stmt] = []
    for node in selected_nodes:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            required = required_import_bindings[id(node)]
            aliases = [
                alias for alias in node.names
                if (alias.asname or alias.name.split(".")[0]) in required
            ]
            if isinstance(node, ast.Import):
                node = ast.Import(names=aliases)
            else:
                node = ast.ImportFrom(module=node.module, names=aliases, level=node.level)
        pruned.append(node)
    return ast.Module(body=pruned, type_ignores=[])


def _slash_strings(node: ast.AST) -> list[str] | None:
    if isinstance(node, ast.Constant) and type(node.value) is str:
        return [node.value]
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        left = _slash_strings(node.left)
        right = _slash_strings(node.right)
        if left is not None and right is not None:
            return [*left, *right]
    if isinstance(node, (ast.Name, ast.Attribute, ast.Subscript, ast.Call)):
        return []
    return None


def _literal_paths(tree: ast.AST, text: str, tracked: set[str]) -> set[str]:
    del text
    candidates: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            parts = _slash_strings(node)
            if parts:
                normalized = "/".join(part.strip("/\\") for part in parts if part)
                for prefix in ("experiments/configs/", "docs/decisions/"):
                    position = normalized.find(prefix)
                    if position >= 0:
                        candidates.add(normalized[position:])
        if isinstance(node, ast.Constant) and type(node.value) is str:
            value = node.value.replace("\\", "/")
            if value in tracked:
                candidates.add(value)
    allowed = ("experiments/configs/", "docs/decisions/")
    return {_relative_path(path) for path in candidates if path in tracked and path.startswith(allowed)}


class _StaticValue:
    __slots__ = ("alternate", "kind", "value")

    def __init__(self, kind: str, value: object = None, alternate: object = None) -> None:
        self.kind = kind
        self.value = value
        self.alternate = value if alternate is None else alternate


_UNRESOLVED_STATIC = _StaticValue("unresolved")
_SYMBOLIC_STATIC = _StaticValue("symbolic")
_SYMBOLIC_PRIMARY_TEXT = "a__pontius_symbolic__"
_SYMBOLIC_ALTERNATE_TEXT = "b__pontius_symbolic__"


def _target_names(target: ast.AST) -> set[str]:
    return {
        node.id for node in ast.walk(target)
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store)
    }


class _AssignmentInventory(ast.NodeVisitor):
    def __init__(self) -> None:
        self.counts: dict[str, int] = {}
        self.definitions: dict[str, list[ast.AST]] = {}

    def _record(self, target: ast.AST, value: ast.AST) -> None:
        for name in _target_names(target):
            self.counts[name] = self.counts.get(name, 0) + 1
            self.definitions.setdefault(name, []).append(value)

    def visit_Assign(self, node: ast.Assign) -> None:
        for target in node.targets:
            self._record(target, node.value)
        self.visit(node.value)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        self._record(node.target, node.value or ast.Constant(value=None))
        if node.value is not None:
            self.visit(node.value)

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        self._record(node.target, node.value)
        self.visit(node.value)

    def visit_NamedExpr(self, node: ast.NamedExpr) -> None:
        self._record(node.target, node.value)
        self.visit(node.value)

    def visit_For(self, node: ast.For) -> None:
        self._record(node.target, node.iter)
        self.generic_visit(node)

    visit_AsyncFor = visit_For

    def visit_With(self, node: ast.With) -> None:
        for item in node.items:
            if item.optional_vars is not None:
                self._record(item.optional_vars, item.context_expr)
        self.generic_visit(node)

    visit_AsyncWith = visit_With

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        if node.name is not None:
            target = ast.Name(id=node.name, ctx=ast.Store())
            self._record(target, node.type or ast.Constant(value=None))
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        return None

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        return None

    def visit_Lambda(self, node: ast.Lambda) -> None:
        return None


def _assignment_inventory(statements: Sequence[ast.stmt]) -> _AssignmentInventory:
    inventory = _AssignmentInventory()
    for statement in statements:
        inventory.visit(statement)
    return inventory


def _static_expression(node: ast.AST, environment: Mapping[str, _StaticValue]) -> _StaticValue:
    if isinstance(node, ast.Constant):
        return _StaticValue("exact", node.value)
    if isinstance(node, ast.Name):
        if node.id == "__file__":
            return _SYMBOLIC_STATIC
        return environment.get(node.id, _UNRESOLVED_STATIC)
    if isinstance(node, (ast.List, ast.Tuple)):
        return _StaticValue("sequence", tuple(_static_expression(item, environment) for item in node.elts))
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = _static_expression(node.left, environment)
        right = _static_expression(node.right, environment)
        if "unresolved" in (left.kind, right.kind):
            return _UNRESOLVED_STATIC
        if left.kind == right.kind == "exact":
            try:
                return _StaticValue(
                    "exact",
                    left.value + right.value,  # type: ignore[operator]
                    left.alternate + right.alternate,  # type: ignore[operator]
                )
            except (TypeError, ValueError):
                return _UNRESOLVED_STATIC
        if left.kind == right.kind == "sequence":
            return _StaticValue("sequence", tuple(left.value) + tuple(right.value))  # type: ignore[arg-type]
        return _SYMBOLIC_STATIC
    if isinstance(node, ast.BinOp):
        left = _static_expression(node.left, environment)
        right = _static_expression(node.right, environment)
        return (
            _UNRESOLVED_STATIC
            if "unresolved" in (left.kind, right.kind)
            else _SYMBOLIC_STATIC
        )
    if isinstance(node, ast.JoinedStr):
        pieces: list[str] = []
        alternate_pieces: list[str] = []
        for part in node.values:
            if isinstance(part, ast.Constant) and type(part.value) is str:
                pieces.append(part.value)
                alternate_pieces.append(part.value)
                continue
            if not isinstance(part, ast.FormattedValue):
                return _UNRESOLVED_STATIC
            value = _static_expression(part.value, environment)
            if value.kind == "unresolved":
                return _UNRESOLVED_STATIC
            if value.kind == "exact":
                rendered: object = value.value
                alternate_rendered: object = value.alternate
                if part.conversion == ord("r"):
                    rendered = repr(rendered)
                    alternate_rendered = repr(alternate_rendered)
                elif part.conversion == ord("s"):
                    rendered = str(rendered)
                    alternate_rendered = str(alternate_rendered)
                elif part.conversion == ord("a"):
                    rendered = ascii(rendered)
                    alternate_rendered = ascii(alternate_rendered)
                elif part.conversion not in (-1, None):
                    return _UNRESOLVED_STATIC
                if part.format_spec is not None:
                    spec = _static_expression(part.format_spec, environment)
                    if spec.kind != "exact" or type(spec.value) is not str:
                        return _UNRESOLVED_STATIC
                    try:
                        rendered = format(rendered, spec.value)
                        alternate_rendered = format(alternate_rendered, spec.alternate)
                    except (TypeError, ValueError):
                        return _UNRESOLVED_STATIC
                pieces.append(str(rendered))
                alternate_pieces.append(str(alternate_rendered))
            else:
                primary: object = _SYMBOLIC_PRIMARY_TEXT
                alternate: object = _SYMBOLIC_ALTERNATE_TEXT
                if part.conversion == ord("r"):
                    primary, alternate = repr(primary), repr(alternate)
                elif part.conversion == ord("s"):
                    primary, alternate = str(primary), str(alternate)
                elif part.conversion == ord("a"):
                    primary, alternate = ascii(primary), ascii(alternate)
                elif part.conversion not in (-1, None):
                    return _UNRESOLVED_STATIC
                if part.format_spec is not None:
                    spec = _static_expression(part.format_spec, environment)
                    if spec.kind != "exact" or type(spec.value) is not str:
                        return _UNRESOLVED_STATIC
                    try:
                        primary = format(primary, spec.value)
                        alternate = format(alternate, spec.alternate)
                    except (TypeError, ValueError):
                        return _UNRESOLVED_STATIC
                pieces.append(str(primary))
                alternate_pieces.append(str(alternate))
        return _StaticValue("exact", "".join(pieces), "".join(alternate_pieces))
    if isinstance(node, ast.UnaryOp):
        operand = _static_expression(node.operand, environment)
        if operand.kind != "exact":
            return operand
        try:
            if isinstance(node.op, ast.USub):
                return _StaticValue("exact", -operand.value)  # type: ignore[operator]
            if isinstance(node.op, ast.UAdd):
                return _StaticValue("exact", +operand.value)  # type: ignore[operator]
            if isinstance(node.op, ast.Not):
                return _StaticValue("exact", not operand.value)
        except (TypeError, ValueError):
            return _UNRESOLVED_STATIC
    if isinstance(node, (ast.Attribute, ast.Subscript)):
        base = _static_expression(node.value, environment)
        return _UNRESOLVED_STATIC if base.kind == "unresolved" else _SYMBOLIC_STATIC
    if isinstance(node, ast.Call):
        arguments = [_static_expression(argument, environment) for argument in node.args]
        arguments.extend(
            _static_expression(keyword.value, environment)
            for keyword in node.keywords
            if keyword.arg is not None
        )
        if any(argument.kind == "unresolved" for argument in arguments):
            return _UNRESOLVED_STATIC
        if isinstance(node.func, ast.Name) and node.func.id in {"str", "repr", "ascii"} and len(arguments) == 1:
            if arguments[0].kind == "exact":
                function = {"str": str, "repr": repr, "ascii": ascii}[node.func.id]
                return _StaticValue(
                    "exact",
                    function(arguments[0].value),
                    function(arguments[0].alternate),
                )
            return _SYMBOLIC_STATIC
        callee = _static_expression(node.func, environment)
        return _UNRESOLVED_STATIC if callee.kind == "unresolved" else _SYMBOLIC_STATIC
    if isinstance(node, (ast.Dict, ast.Set)):
        values = list(node.values) if isinstance(node, ast.Dict) else list(node.elts)
        fixed = [_static_expression(value, environment) for value in values]
        return _UNRESOLVED_STATIC if any(value.kind == "unresolved" for value in fixed) else _SYMBOLIC_STATIC
    return _UNRESOLVED_STATIC


def _bind_static_target(
    environment: dict[str, _StaticValue], target: ast.AST, value: _StaticValue,
    inventory: _AssignmentInventory, *, conditional: bool,
) -> None:
    if isinstance(target, ast.Name):
        environment[target.id] = (
            value
            if not conditional
            and (inventory.counts.get(target.id) == 1 or value.kind == "symbolic")
            else _UNRESOLVED_STATIC
        )
        return
    for name in _target_names(target):
        environment[name] = _UNRESOLVED_STATIC


def _mentions_dash_c(
    expression: ast.AST, definitions: Mapping[str, Sequence[ast.AST]], seen: set[str] | None = None
) -> bool:
    seen = set() if seen is None else seen
    for node in ast.walk(expression):
        if isinstance(node, ast.Constant) and node.value == "-c":
            return True
        if isinstance(node, ast.Name) and node.id not in seen:
            seen.add(node.id)
            if any(_mentions_dash_c(item, definitions, seen) for item in definitions.get(node.id, ())):
                return True
    return False


_IMPORT_CALL_CONTRACTS = {
    "importlib.import_module": (
        ("name", "package"),
        {"package": None},
    ),
    "__import__": (
        ("name", "globals", "locals", "fromlist", "level"),
        {"globals": None, "locals": None, "fromlist": (), "level": 0},
    ),
}


def _import_callable_name(call: ast.Call) -> str | None:
    if isinstance(call.func, ast.Name) and call.func.id == "__import__":
        return "__import__"
    if isinstance(call.func, ast.Attribute) and call.func.attr == "import_module":
        return "importlib.import_module"
    return None


def _bind_import_call(
    call: ast.Call, callable_name: str, current_path: str
) -> dict[str, ast.AST]:
    parameters, defaults = _IMPORT_CALL_CONTRACTS[callable_name]
    if any(isinstance(argument, ast.Starred) for argument in call.args):
        raise GenerationError(
            f"dynamic {callable_name} arguments are not statically bound in {current_path}"
        )
    if len(call.args) > len(parameters):
        raise GenerationError(
            f"dynamic {callable_name} has too many positional arguments in {current_path}"
        )
    bound = dict(zip(parameters, call.args, strict=False))
    for keyword in call.keywords:
        if keyword.arg is None:
            raise GenerationError(
                f"dynamic {callable_name} keyword expansion is not statically bound in {current_path}"
            )
        if keyword.arg not in parameters:
            raise GenerationError(
                f"dynamic {callable_name} has unknown argument {keyword.arg!r} in {current_path}"
            )
        if keyword.arg in bound:
            raise GenerationError(
                f"dynamic {callable_name} duplicates argument {keyword.arg!r} in {current_path}"
            )
        bound[keyword.arg] = keyword.value
    required = [parameter for parameter in parameters if parameter not in defaults]
    missing = [parameter for parameter in required if parameter not in bound]
    if missing:
        raise GenerationError(
            f"dynamic {callable_name} is missing argument {missing[0]!r} in {current_path}"
        )
    return bound


def _exact_import_argument(
    bound: Mapping[str, ast.AST], name: str, default: object, callable_name: str,
    current_path: str,
) -> object:
    if name not in bound:
        return default
    value = _static_expression(bound[name], {})
    if value.kind != "exact":
        raise GenerationError(
            f"dynamic {callable_name} argument {name!r} is not fixed in {current_path}"
        )
    return value.value


def _exact_fromlist(
    bound: Mapping[str, ast.AST], callable_name: str, current_path: str
) -> tuple[str, ...]:
    if "fromlist" not in bound:
        return ()
    value = _static_expression(bound["fromlist"], {})
    if value.kind != "sequence":
        raise GenerationError(
            f"dynamic {callable_name} argument 'fromlist' is not fixed in {current_path}"
        )
    result: list[str] = []
    for item in value.value:  # type: ignore[union-attr]
        if item.kind != "exact" or type(item.value) is not str:
            raise GenerationError(
                f"dynamic {callable_name} argument 'fromlist' is not fixed in {current_path}"
            )
        result.append(item.value)
    return tuple(result)


def _resolve_import_module_name(name: str, package: object, current_path: str) -> str:
    if not name:
        raise GenerationError(f"dynamic import module name is empty in {current_path}")
    if not name.startswith("."):
        return name
    if type(package) is not str or not package or package.startswith("."):
        raise GenerationError(
            f"dynamic relative import package is not fixed in {current_path}"
        )
    level = len(name) - len(name.lstrip("."))
    package_parts = package.rsplit(".", level - 1)
    if len(package_parts) < level or not package_parts[0]:
        raise GenerationError(
            f"dynamic relative import escapes its package in {current_path}"
        )
    suffix = name[level:]
    return f"{package_parts[0]}.{suffix}" if suffix else package_parts[0]


def _import_call_target(call: ast.Call, current_path: str) -> tuple[object, ...] | None:
    callable_name = _import_callable_name(call)
    if callable_name is None:
        return None
    bound = _bind_import_call(call, callable_name, current_path)
    name = _exact_import_argument(bound, "name", None, callable_name, current_path)
    if type(name) is not str or not name:
        raise GenerationError(
            f"dynamic {callable_name} argument 'name' is not a fixed string in {current_path}"
        )
    if callable_name == "importlib.import_module":
        package = _exact_import_argument(
            bound, "package", None, callable_name, current_path
        )
        if package is not None and type(package) is not str:
            raise GenerationError(
                f"dynamic {callable_name} argument 'package' is not a fixed string in {current_path}"
            )
        resolved = _resolve_import_module_name(name, package, current_path)
        return ("call", callable_name, resolved, package)

    fromlist = _exact_fromlist(bound, callable_name, current_path)
    if "*" in fromlist:
        raise GenerationError(
            f"dynamic {callable_name} wildcard fromlist is not statically resolved in {current_path}"
        )
    level = _exact_import_argument(bound, "level", 0, callable_name, current_path)
    if type(level) is not int or level < 0:
        raise GenerationError(
            f"dynamic {callable_name} argument 'level' is not a fixed nonnegative integer in {current_path}"
        )
    if level != 0 or name.startswith("."):
        raise GenerationError(
            f"dynamic relative {callable_name} context is not fixed in {current_path}"
        )
    return ("call", callable_name, name, fromlist, level)


def _dynamic_import_targets(program: ast.AST, current_path: str) -> tuple[object, ...]:
    targets: list[object] = []
    for node in ast.walk(program):
        if isinstance(node, ast.Import):
            targets.append(("import", tuple(alias.name for alias in node.names)))
        elif isinstance(node, ast.ImportFrom):
            targets.append(
                ("from", node.level, node.module, tuple(alias.name for alias in node.names))
            )
        elif isinstance(node, ast.Call):
            target = _import_call_target(node, current_path)
            if target is not None:
                targets.append(target)
    return tuple(targets)


def _dynamic_import_call_paths(
    targets: Sequence[object], current_path: str, tracked: set[str]
) -> set[str]:
    result: set[str] = set()
    for target in targets:
        if not isinstance(target, tuple) or not target or target[0] != "call":
            continue
        callable_name = target[1]
        module = target[2]
        if type(module) is not str:
            raise GenerationError(f"dynamic import target is malformed in {current_path}")
        path = _module_path(module, tracked)
        if path is not None:
            result.add(path)
        elif module == "pontius" or module.startswith("pontius."):
            raise GenerationError(
                f"unresolved dynamic local import {module!r} in {current_path}"
            )
        if callable_name != "__import__":
            continue
        fromlist = target[3]
        if not isinstance(fromlist, tuple):
            raise GenerationError(f"dynamic import fromlist is malformed in {current_path}")
        for member in fromlist:
            candidate = f"{module}.{member}"
            candidate_path = _module_path(candidate, tracked)
            if candidate_path is not None:
                result.add(candidate_path)
    return result


def _process_dynamic_program(
    source: str, alternate_source: str, current_path: str, tracked: set[str], result: set[str]
) -> None:
    try:
        program = ast.parse(source, filename=f"{current_path}::<dynamic-c>")
        alternate_program = ast.parse(alternate_source, filename=f"{current_path}::<dynamic-c>")
    except SyntaxError as error:
        raise GenerationError(f"dynamic -c program cannot be parsed: {current_path}") from error
    targets = _dynamic_import_targets(program, current_path)
    alternate_targets = _dynamic_import_targets(alternate_program, current_path)
    if targets != alternate_targets:
        raise GenerationError(f"dynamic import target is not fixed in {current_path}")
    result.update(_import_paths(program, current_path, tracked))
    result.update(_dynamic_import_call_paths(targets, current_path, tracked))


def _inspect_dynamic_call(
    call: ast.Call, environment: Mapping[str, _StaticValue], inventory: _AssignmentInventory,
    current_path: str, tracked: set[str], result: set[str],
) -> None:
    if not (
        isinstance(call.func, ast.Attribute)
        and isinstance(call.func.value, ast.Name)
        and call.func.value.id == "subprocess"
        and call.func.attr in {"run", "Popen", "call", "check_call", "check_output"}
    ):
        return
    arguments = list(call.args[:1])
    arguments.extend(keyword.value for keyword in call.keywords if keyword.arg == "args")
    for expression in arguments:
        argv = _static_expression(expression, environment)
        if argv.kind != "sequence":
            if _mentions_dash_c(expression, inventory.definitions):
                raise GenerationError(f"dynamic -c argv is not fixed in {current_path}")
            continue
        values = tuple(argv.value)  # type: ignore[arg-type]
        indexes = [
            index for index, value in enumerate(values)
            if value.kind == "exact" and value.value == "-c"
        ]
        if not indexes:
            if _mentions_dash_c(expression, inventory.definitions):
                raise GenerationError(f"dynamic -c argv is ambiguous in {current_path}")
            continue
        if len(indexes) != 1 or indexes[0] + 1 >= len(values):
            raise GenerationError(f"dynamic -c argv is malformed in {current_path}")
        program = values[indexes[0] + 1]
        if program.kind != "exact" or type(program.value) is not str:
            raise GenerationError(f"dynamic -c program is not statically fixed in {current_path}")
        _process_dynamic_program(
            program.value, program.alternate, current_path, tracked, result
        )


class _CallInspector(ast.NodeVisitor):
    def __init__(
        self, environment: Mapping[str, _StaticValue], inventory: _AssignmentInventory,
        current_path: str, tracked: set[str], result: set[str],
    ) -> None:
        self.environment = environment
        self.inventory = inventory
        self.current_path = current_path
        self.tracked = tracked
        self.result = result

    def visit_Call(self, node: ast.Call) -> None:
        _inspect_dynamic_call(
            node, self.environment, self.inventory, self.current_path, self.tracked, self.result
        )
        self.generic_visit(node)

    def visit_Lambda(self, node: ast.Lambda) -> None:
        return None


def _inspect_expression_calls(
    expression: ast.AST, environment: Mapping[str, _StaticValue],
    inventory: _AssignmentInventory, current_path: str, tracked: set[str], result: set[str],
) -> None:
    _CallInspector(environment, inventory, current_path, tracked, result).visit(expression)


def _analyze_dynamic_statements(
    statements: Sequence[ast.stmt], environment: dict[str, _StaticValue],
    inventory: _AssignmentInventory, current_path: str, tracked: set[str], result: set[str],
    *, conditional: bool = False,
) -> None:
    for statement in statements:
        if isinstance(statement, ast.Assign):
            _inspect_expression_calls(statement.value, environment, inventory, current_path, tracked, result)
            value = _static_expression(statement.value, environment)
            for target in statement.targets:
                _bind_static_target(environment, target, value, inventory, conditional=conditional)
        elif isinstance(statement, ast.AnnAssign):
            if statement.value is not None:
                _inspect_expression_calls(statement.value, environment, inventory, current_path, tracked, result)
                value = _static_expression(statement.value, environment)
            else:
                value = _UNRESOLVED_STATIC
            _bind_static_target(environment, statement.target, value, inventory, conditional=conditional)
        elif isinstance(statement, ast.AugAssign):
            _inspect_expression_calls(statement.value, environment, inventory, current_path, tracked, result)
            _bind_static_target(
                environment, statement.target, _UNRESOLVED_STATIC, inventory, conditional=True
            )
        elif isinstance(statement, (ast.Expr, ast.Return, ast.Raise, ast.Assert)):
            for value in (
                getattr(statement, "value", None), getattr(statement, "exc", None),
                getattr(statement, "test", None), getattr(statement, "msg", None),
            ):
                if isinstance(value, ast.AST):
                    _inspect_expression_calls(value, environment, inventory, current_path, tracked, result)
        elif isinstance(statement, (ast.With, ast.AsyncWith)):
            for item in statement.items:
                _inspect_expression_calls(item.context_expr, environment, inventory, current_path, tracked, result)
                if item.optional_vars is not None:
                    context = _static_expression(item.context_expr, environment)
                    value = _UNRESOLVED_STATIC if context.kind == "unresolved" else _SYMBOLIC_STATIC
                    _bind_static_target(
                        environment, item.optional_vars, value, inventory, conditional=conditional
                    )
            _analyze_dynamic_statements(
                statement.body, environment, inventory, current_path, tracked, result,
                conditional=conditional,
            )
        elif isinstance(statement, ast.If):
            _inspect_expression_calls(statement.test, environment, inventory, current_path, tracked, result)
            _analyze_dynamic_statements(
                statement.body, dict(environment), inventory, current_path, tracked, result,
                conditional=True,
            )
            _analyze_dynamic_statements(
                statement.orelse, dict(environment), inventory, current_path, tracked, result,
                conditional=True,
            )
            for name, count in inventory.counts.items():
                if count and any(name in _target_names(node) for node in ast.walk(statement)):
                    environment[name] = _UNRESOLVED_STATIC
        elif isinstance(statement, (ast.For, ast.AsyncFor, ast.While)):
            expression = statement.iter if isinstance(statement, (ast.For, ast.AsyncFor)) else statement.test
            _inspect_expression_calls(expression, environment, inventory, current_path, tracked, result)
            branch_environment = dict(environment)
            if isinstance(statement, (ast.For, ast.AsyncFor)):
                _bind_static_target(
                    branch_environment, statement.target, _UNRESOLVED_STATIC, inventory, conditional=True
                )
            _analyze_dynamic_statements(
                statement.body, branch_environment, inventory, current_path, tracked, result,
                conditional=True,
            )
            _analyze_dynamic_statements(
                statement.orelse, dict(environment), inventory, current_path, tracked, result,
                conditional=True,
            )
        elif isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
            _analyze_dynamic_function(statement, environment, current_path, tracked, result)
        elif isinstance(statement, ast.Try):
            for branch in (statement.body, statement.orelse, statement.finalbody):
                _analyze_dynamic_statements(
                    branch, dict(environment), inventory, current_path, tracked, result,
                    conditional=True,
                )
            for handler in statement.handlers:
                _analyze_dynamic_statements(
                    handler.body, dict(environment), inventory, current_path, tracked, result,
                    conditional=True,
                )


def _analyze_dynamic_function(
    function: ast.FunctionDef | ast.AsyncFunctionDef, enclosing: Mapping[str, _StaticValue],
    current_path: str, tracked: set[str], result: set[str],
) -> None:
    inventory = _assignment_inventory(function.body)
    environment = dict(enclosing)
    arguments = (
        list(function.args.posonlyargs) + list(function.args.args)
        + list(function.args.kwonlyargs)
    )
    if function.args.vararg is not None:
        arguments.append(function.args.vararg)
    if function.args.kwarg is not None:
        arguments.append(function.args.kwarg)
    for argument in arguments:
        environment[argument.arg] = _UNRESOLVED_STATIC
    _analyze_dynamic_statements(
        function.body, environment, inventory, current_path, tracked, result
    )


def _module_static_environment(tree: ast.Module) -> dict[str, _StaticValue]:
    inventory = _assignment_inventory(tree.body)
    environment: dict[str, _StaticValue] = {"__file__": _SYMBOLIC_STATIC}
    for statement in tree.body:
        if isinstance(statement, (ast.Import, ast.ImportFrom)):
            for alias in statement.names:
                environment[alias.asname or alias.name.split(".")[0]] = _SYMBOLIC_STATIC
        elif isinstance(statement, ast.Assign):
            value = _static_expression(statement.value, environment)
            for target in statement.targets:
                _bind_static_target(environment, target, value, inventory, conditional=False)
        elif isinstance(statement, ast.AnnAssign):
            value = (
                _static_expression(statement.value, environment)
                if statement.value is not None else _UNRESOLVED_STATIC
            )
            _bind_static_target(environment, statement.target, value, inventory, conditional=False)
    return environment


def _dynamic_program_imports(tree: ast.AST, current_path: str, tracked: set[str]) -> set[str]:
    if not isinstance(tree, ast.Module):
        raise GenerationError("dynamic program analysis requires a module")
    enclosing = _module_static_environment(tree)
    result: set[str] = set()
    module_inventory = _assignment_inventory(tree.body)
    module_environment: dict[str, _StaticValue] = {"__file__": _SYMBOLIC_STATIC}
    for statement in tree.body:
        if isinstance(statement, (ast.Import, ast.ImportFrom)):
            for alias in statement.names:
                module_environment[alias.asname or alias.name.split(".")[0]] = _SYMBOLIC_STATIC
        elif isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
            _analyze_dynamic_function(statement, enclosing, current_path, tracked, result)
        elif isinstance(statement, ast.ClassDef):
            for child in statement.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    _analyze_dynamic_function(child, enclosing, current_path, tracked, result)
        else:
            _analyze_dynamic_statements(
                [statement], module_environment, module_inventory, current_path, tracked, result
            )
    return result


def _phase_paths(git: _Git, phase: Mapping[str, str]) -> tuple[str, ...]:
    commit = phase["commit"]
    tracked = set(git.tracked_paths(commit))
    selected_test = phase["selected_test"]
    decision_path = phase["decision_path"]
    for required in (selected_test, decision_path):
        if required not in tracked:
            raise GenerationError(f"phase seed path is not tracked at {commit}: {required}")
    discovered = {selected_test, decision_path}
    pending = [selected_test]
    parsed: set[str] = set()
    while pending:
        path = pending.pop()
        if path in parsed or not path.endswith(".py"):
            continue
        parsed.add(path)
        raw = git.show_blob(commit, path)
        try:
            text = raw.decode("utf-8")
            tree = ast.parse(text, filename=f"{commit}:{path}")
        except (UnicodeDecodeError, SyntaxError) as error:
            raise GenerationError(f"phase Python blob cannot be parsed: {commit}:{path}") from error
        scoped_tree = _selected_class_scope(tree, str(phase["selected_class"])) if path == selected_test else tree
        reached = (
            _import_paths(scoped_tree, path, tracked)
            | _literal_paths(scoped_tree, text, tracked)
            | _dynamic_program_imports(scoped_tree, path, tracked)
        )
        for candidate in sorted(reached):
            if candidate not in discovered:
                discovered.add(candidate)
    return tuple(sorted(discovered))


def _historical_role(path: str, phase: Mapping[str, str]) -> str:
    if path == phase.get("selected_test"):
        return "selected_test"
    if path == phase.get("decision_path"):
        return "governing_decision"
    if path.startswith("src/pontius/"):
        return "source_dependency"
    if path.startswith("run_"):
        return "runner_dependency"
    if path.startswith("tests/"):
        return "test_dependency"
    if path.startswith("experiments/configs/"):
        return "configuration_dependency"
    if path.startswith("docs/decisions/"):
        return "decision_dependency"
    if path.startswith("artifacts/"):
        return "artifact_dependency"
    return "repository_dependency"


def _row(
    git: _Git,
    *,
    commit: str,
    relative_path: str,
    role: str,
    phase: str,
    decision: str,
) -> dict[str, object]:
    oid = git.blob_oid(commit, relative_path)
    raw = git.show_blob(commit, relative_path)
    return {
        "commit": commit,
        "relative_path": relative_path,
        "git_blob_oid": oid,
        "raw_sha256": sha256(raw).hexdigest(),
        "role": role,
        "phase": phase,
        "governing_decision": decision,
    }


def _measure_current(repository_root: Path) -> tuple[list[dict[str, object]], dict[str, bytes]]:
    present_paths = {entry["relative_path"] for entry in CURRENT_FILE_ENTRIES}
    absent_paths = {entry["relative_path"] for entry in CURRENT_ABSENCE_ENTRIES}
    if present_paths & absent_paths or len(present_paths) != 6 or len(absent_paths) != 18:
        raise GenerationError("current evidence constants overlap or have the wrong cardinality")
    measured: list[dict[str, object]] = []
    raw_by_path: dict[str, bytes] = {}
    for expected in CURRENT_FILE_ENTRIES:
        path = repository_root / str(expected["relative_path"])
        raw = read_regular_file_once(path, maximum_bytes=int(expected["byte_length"]))
        actual = (len(raw), sha256(raw).hexdigest())
        wanted = (expected["byte_length"], expected["raw_sha256"])
        if actual != wanted:
            raise GenerationError(
                "retained current file identity differs from the approved constant: "
                f"{expected['relative_path']}"
            )
        measured.append(dict(expected))
        raw_by_path[str(expected["relative_path"])] = raw
    for expected in CURRENT_ABSENCE_ENTRIES:
        path = repository_root / str(expected["relative_path"])
        if os.path.lexists(path):
            raise GenerationError(f"protected retained absence is present: {expected['relative_path']}")
    return measured, raw_by_path


def _dependency_hashes(v7_raw: bytes) -> dict[str, str]:
    first_line = v7_raw.split(b"\n", 1)[0]
    try:
        header = _json_no_duplicates(first_line.decode("utf-8"))
        body = header["body"]  # type: ignore[index]
        payload = body["payload"]  # type: ignore[index]
        dependencies = payload["dependency_hashes"]  # type: ignore[index]
    except (KeyError, TypeError) as error:
        raise GenerationError("retained v7 record zero does not contain dependency_hashes") from error
    if not isinstance(dependencies, dict) or len(dependencies) != 96:
        raise GenerationError("retained v7 dependency_hashes must contain exactly 96 paths")
    result: dict[str, str] = {}
    for path, digest in dependencies.items():
        normalized = _relative_path(path)
        if (
            type(digest) is not str
            or _HEX64.fullmatch(digest) is None
            or normalized in result
        ):
            raise GenerationError("retained v7 dependency_hashes contains a malformed entry")
        result[normalized] = digest
    return result


def historical_entries_sha256(rows: Sequence[Mapping[str, object]]) -> str:
    normalized = [
        dict(row)
        for row in sorted(rows, key=lambda item: (str(item["commit"]), str(item["relative_path"])))
    ]
    return semantic_sha256(normalized)


def _append_unique_row(
    rows: list[dict[str, object]], identities: set[tuple[str, str]], row: Mapping[str, object]
) -> None:
    identity = (str(row["commit"]), str(row["relative_path"]))
    if identity in identities:
        raise GenerationError(f"historical derivation collided at {identity}")
    identities.add(identity)
    rows.append(dict(row))


def derive_manifest_state(repository_root: Path) -> dict[str, object]:
    if not isinstance(repository_root, Path) or not repository_root.is_absolute():
        raise GenerationError("repository root must be absolute")
    root = repository_root.resolve(strict=True)
    current_files, raw_by_path = _measure_current(root)
    with tempfile.TemporaryDirectory(prefix="pontius-evidence-git-home-") as home_text:
        git = _Git(root, Path(home_text).resolve())
        for snapshot in SNAPSHOTS:
            actual_tree = git.root_tree_oid(str(snapshot["commit"]))
            if actual_tree != snapshot["root_tree_oid"]:
                raise GenerationError(f"historical root tree changed for {snapshot['commit']}")
        rows: list[dict[str, object]] = []
        identities: set[tuple[str, str]] = set()
        for phase in EARLIER_PHASES:
            for path in _phase_paths(git, phase):
                row = _row(
                    git,
                    commit=str(phase["commit"]),
                    relative_path=path,
                    role=_historical_role(path, phase),
                    phase=str(phase["phase"]),
                    decision=str(phase["governing_decision"]),
                )
                _append_unique_row(rows, identities, row)
        v7_path = str(CURRENT_FILE_ENTRIES[3]["relative_path"])
        dependencies = _dependency_hashes(raw_by_path[v7_path])
        source_snapshot = SNAPSHOTS[9]
        for path in sorted(dependencies):
            row = _row(
                git,
                commit=str(source_snapshot["commit"]),
                relative_path=path,
                role="source_seal_dependency",
                phase=str(source_snapshot["phase"]),
                decision=str(source_snapshot["governing_decision"]),
            )
            if row["raw_sha256"] != dependencies[path]:
                raise GenerationError(f"v7 source-seal dependency digest mismatch: {path}")
            _append_unique_row(rows, identities, row)
        authorization_snapshot = SNAPSHOTS[10]
        for path in V7_AUTHORIZATION_PATHS:
            row = _row(
                git,
                commit=str(authorization_snapshot["commit"]),
                relative_path=path,
                role="authorization_surface",
                phase=str(authorization_snapshot["phase"]),
                decision=str(authorization_snapshot["governing_decision"]),
            )
            _append_unique_row(rows, identities, row)
        evaluation_snapshot = SNAPSHOTS[11]
        for path in LEGACY_EVALUATION_TEST_PATHS:
            row = _row(
                git,
                commit=str(evaluation_snapshot["commit"]),
                relative_path=path,
                role="selected_test",
                phase=str(evaluation_snapshot["phase"]),
                decision=str(evaluation_snapshot["governing_decision"]),
            )
            _append_unique_row(rows, identities, row)
    rows.sort(key=lambda item: (str(item["commit"]), str(item["relative_path"])))
    return {
        "current_files": current_files,
        "current_absences": [dict(entry) for entry in CURRENT_ABSENCE_ENTRIES],
        "snapshots": [dict(snapshot) for snapshot in SNAPSHOTS],
        "blobs": rows,
        "entries_sha256": historical_entries_sha256(rows),
    }


def _toml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=True)


def _toml_value(value: object) -> str:
    if type(value) is bool:
        return "true" if value else "false"
    if type(value) is int:
        return str(value)
    if type(value) is str:
        return _toml_string(value)
    if isinstance(value, (list, tuple)) and all(type(item) is str for item in value):
        return "[" + ", ".join(_toml_string(item) for item in value) + "]"
    raise GenerationError(f"unsupported TOML value: {type(value).__name__}")


def _table_lines(values: Mapping[str, object], keys: Sequence[str]) -> list[str]:
    return [f"{key} = {_toml_value(values[key])}" for key in keys]


def _render_current_files(state: Mapping[str, object]) -> bytes:
    root = {
        "schema_version": "pontius-sealed-current-files-v1",
        "baseline_commit": BASELINE_COMMIT,
        "entry_count": len(state["current_files"]),
    }
    chunks = [_table_lines(root, ("schema_version", "baseline_commit", "entry_count"))]
    for item in state["current_files"]:
        chunks.append(
            [
                "[[files]]",
                *_table_lines(
                    item,
                    (
                        "relative_path",
                        "byte_length",
                        "raw_sha256",
                        "role",
                        "governing_decision",
                        "owner",
                    ),
                ),
            ]
        )
    return ("\n\n".join("\n".join(chunk) for chunk in chunks) + "\n").encode("utf-8")


def _render_absences(state: Mapping[str, object]) -> bytes:
    root = {
        "schema_version": "pontius-sealed-current-absences-v1",
        "baseline_commit": BASELINE_COMMIT,
        "entry_count": len(state["current_absences"]),
    }
    chunks = [_table_lines(root, ("schema_version", "baseline_commit", "entry_count"))]
    for item in sorted(state["current_absences"], key=lambda value: value["relative_path"]):
        chunks.append(
            [
                "[[absences]]",
                *_table_lines(
                    item,
                    ("relative_path", "role", "governing_decision", "owner"),
                ),
            ]
        )
    return ("\n\n".join("\n".join(chunk) for chunk in chunks) + "\n").encode("utf-8")


def _render_historical(state: Mapping[str, object], approved: str) -> bytes:
    root = {
        "schema_version": "pontius-historical-blobs-v1",
        "baseline_commit": BASELINE_COMMIT,
        "snapshot_count": len(state["snapshots"]),
        "entry_count": len(state["blobs"]),
        "entries_sha256": state["entries_sha256"],
        "approved_seed_sha256": approved,
    }
    chunks = [
        _table_lines(
            root,
            (
                "schema_version",
                "baseline_commit",
                "snapshot_count",
                "entry_count",
                "entries_sha256",
                "approved_seed_sha256",
            ),
        )
    ]
    for item in sorted(
        state["snapshots"], key=lambda value: (value["commit"], value["phase"])
    ):
        chunks.append(
            [
                "[[snapshots]]",
                *_table_lines(
                    item, ("phase", "commit", "root_tree_oid", "governing_decision")
                ),
            ]
        )
    for item in state["blobs"]:
        chunks.append(
            [
                "[[blobs]]",
                *_table_lines(
                    item,
                    (
                        "commit",
                        "relative_path",
                        "git_blob_oid",
                        "raw_sha256",
                        "role",
                        "phase",
                        "governing_decision",
                    ),
                ),
            ]
        )
    return ("\n\n".join("\n".join(chunk) for chunk in chunks) + "\n").encode("utf-8")


def _render_retained() -> bytes:
    scalar_keys = tuple(
        key for key in RETAINED_V7 if key not in ("result", "attempt", "consumed_launch")
    )
    chunks = [_table_lines(RETAINED_V7, scalar_keys)]
    for key in ("result", "attempt", "consumed_launch"):
        chunks.append(
            [
                f"[{key}]",
                *_table_lines(
                    RETAINED_V7[key],
                    ("relative_path", "byte_length", "raw_sha256", "role"),
                ),
            ]
        )
    return ("\n\n".join("\n".join(chunk) for chunk in chunks) + "\n").encode("utf-8")


def _render_all(state: Mapping[str, object], approved: str) -> dict[str, bytes]:
    return {
        MANIFEST_PATHS[0]: _render_current_files(state),
        MANIFEST_PATHS[1]: _render_absences(state),
        MANIFEST_PATHS[2]: _render_historical(state, approved),
        MANIFEST_PATHS[3]: _render_retained(),
    }


_FILE_KEYS = frozenset(
    ("relative_path", "byte_length", "raw_sha256", "role", "governing_decision", "owner")
)
_ABSENCE_KEYS = frozenset(("relative_path", "role", "governing_decision", "owner"))
_SNAPSHOT_KEYS = frozenset(("phase", "commit", "root_tree_oid", "governing_decision"))
_BLOB_KEYS = frozenset(
    (
        "commit",
        "relative_path",
        "git_blob_oid",
        "raw_sha256",
        "role",
        "phase",
        "governing_decision",
    )
)
_IDENTITY_KEYS = frozenset(("relative_path", "byte_length", "raw_sha256", "role"))
_RETAINED_KEYS = frozenset(RETAINED_V7)


def _exact(table: object, keys: frozenset[str], label: str) -> dict[str, object]:
    if not isinstance(table, dict) or set(table) != keys:
        raise GenerationError(f"{label} keys do not match the exact schema")
    return table


def _string(value: object, label: str) -> str:
    if type(value) is not str or not value:
        raise GenerationError(f"{label} must be a nonempty string")
    return value


def _integer(value: object, label: str) -> int:
    if type(value) is not int or value < 0:
        raise GenerationError(f"{label} must be a nonnegative exact integer")
    return value


def _boolean(value: object, label: str) -> bool:
    if type(value) is not bool:
        raise GenerationError(f"{label} must be an exact boolean")
    return value


def _digest(value: object, label: str) -> str:
    text = _string(value, label)
    if _HEX64.fullmatch(text) is None:
        raise GenerationError(f"{label} must be a lowercase SHA-256 digest")
    return text


def _oid_value(value: object, label: str) -> str:
    text = _string(value, label)
    if _HEX40.fullmatch(text) is None:
        raise GenerationError(f"{label} must be a lowercase Git identity")
    return text


def _array(value: object, label: str) -> list[object]:
    if type(value) is not list:
        raise GenerationError(f"{label} must be an array")
    return value


def _path_value(value: object, label: str) -> str:
    try:
        return _relative_path(value)
    except GenerationError as error:
        raise GenerationError(f"{label} must be a repository-relative path") from error


def _source_label(source_path: Path, repository_root: Path) -> None:
    if not isinstance(source_path, Path) or not isinstance(repository_root, Path):
        raise GenerationError("manifest paths must be Path values")
    try:
        relative = source_path.relative_to(repository_root)
    except ValueError as error:
        raise GenerationError("manifest source path is outside its repository root") from error
    _relative_path(relative.as_posix())


def _parse_toml(
    raw: bytes, source_path: Path, repository_root: Path
) -> dict[str, object]:
    _source_label(source_path, repository_root)
    if type(raw) is not bytes:
        raise GenerationError("manifest input must be immutable bytes")
    try:
        result = tomllib.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as error:
        raise GenerationError("manifest is not valid TOML") from error
    if not isinstance(result, dict):
        raise GenerationError("manifest root is not a table")
    return result


def _parse_file_identity(value: object, label: str) -> dict[str, object]:
    item = _exact(value, _IDENTITY_KEYS, label)
    return {
        "relative_path": _path_value(item["relative_path"], "relative_path"),
        "byte_length": _integer(item["byte_length"], "byte_length"),
        "raw_sha256": _digest(item["raw_sha256"], "raw_sha256"),
        "role": _string(item["role"], "role"),
    }


def parse_manifest_bytes(
    kind: str,
    raw: bytes,
    *,
    source_path: Path,
    repository_root: Path,
) -> dict[str, object]:
    document = _parse_toml(raw, source_path, repository_root)
    if kind == "sealed-current-files":
        root = _exact(
            document,
            frozenset(("schema_version", "baseline_commit", "entry_count", "files")),
            "files root",
        )
        if _string(root["schema_version"], "schema_version") != "pontius-sealed-current-files-v1":
            raise GenerationError("sealed-current-files schema literal is invalid")
        files = []
        for value in _array(root["files"], "files"):
            item = _exact(value, _FILE_KEYS, "files entry")
            files.append(
                {
                    "relative_path": _path_value(item["relative_path"], "relative_path"),
                    "byte_length": _integer(item["byte_length"], "byte_length"),
                    "raw_sha256": _digest(item["raw_sha256"], "raw_sha256"),
                    "role": _string(item["role"], "role"),
                    "governing_decision": _string(
                        item["governing_decision"], "governing_decision"
                    ),
                    "owner": _string(item["owner"], "owner"),
                }
            )
        count = _integer(root["entry_count"], "entry_count")
        if count != len(files):
            raise GenerationError("files entry_count disagrees")
        return {
            "schema_version": root["schema_version"],
            "baseline_commit": _oid_value(root["baseline_commit"], "baseline_commit"),
            "entry_count": count,
            "files": files,
        }
    if kind == "sealed-current-absences":
        root = _exact(
            document,
            frozenset(("schema_version", "baseline_commit", "entry_count", "absences")),
            "absences root",
        )
        if (
            _string(root["schema_version"], "schema_version")
            != "pontius-sealed-current-absences-v1"
        ):
            raise GenerationError("sealed-current-absences schema literal is invalid")
        absences = []
        for value in _array(root["absences"], "absences"):
            item = _exact(value, _ABSENCE_KEYS, "absence entry")
            absences.append(
                {
                    "relative_path": _path_value(item["relative_path"], "relative_path"),
                    "role": _string(item["role"], "role"),
                    "governing_decision": _string(
                        item["governing_decision"], "governing_decision"
                    ),
                    "owner": _string(item["owner"], "owner"),
                }
            )
        count = _integer(root["entry_count"], "entry_count")
        if count != len(absences):
            raise GenerationError("absences entry_count disagrees")
        return {
            "schema_version": root["schema_version"],
            "baseline_commit": _oid_value(root["baseline_commit"], "baseline_commit"),
            "entry_count": count,
            "absences": absences,
        }
    if kind == "historical-blobs":
        return _parse_historical(document)
    if kind == "retained-v7":
        return _parse_retained(document)
    raise GenerationError(f"unknown manifest kind: {kind}")


def _parse_historical(document: dict[str, object]) -> dict[str, object]:
    root = _exact(
        document,
        frozenset(
            (
                "schema_version",
                "baseline_commit",
                "snapshot_count",
                "entry_count",
                "entries_sha256",
                "approved_seed_sha256",
                "snapshots",
                "blobs",
            )
        ),
        "historical root",
    )
    if _string(root["schema_version"], "schema_version") != "pontius-historical-blobs-v1":
        raise GenerationError("historical schema literal is invalid")
    snapshots = []
    for value in _array(root["snapshots"], "snapshots"):
        item = _exact(value, _SNAPSHOT_KEYS, "snapshot entry")
        snapshots.append(
            {
                "phase": _string(item["phase"], "phase"),
                "commit": _oid_value(item["commit"], "commit"),
                "root_tree_oid": _oid_value(item["root_tree_oid"], "root_tree_oid"),
                "governing_decision": _string(
                    item["governing_decision"], "governing_decision"
                ),
            }
        )
    blobs = []
    for value in _array(root["blobs"], "blobs"):
        item = _exact(value, _BLOB_KEYS, "blob entry")
        blobs.append(
            {
                "commit": _oid_value(item["commit"], "commit"),
                "relative_path": _path_value(item["relative_path"], "relative_path"),
                "git_blob_oid": _oid_value(item["git_blob_oid"], "git_blob_oid"),
                "raw_sha256": _digest(item["raw_sha256"], "raw_sha256"),
                "role": _string(item["role"], "role"),
                "phase": _string(item["phase"], "phase"),
                "governing_decision": _string(
                    item["governing_decision"], "governing_decision"
                ),
            }
        )
    snapshots.sort(key=lambda item: (item["commit"], item["phase"]))
    blobs.sort(key=lambda item: (item["commit"], item["relative_path"]))
    if len({(item["commit"], item["relative_path"]) for item in blobs}) != len(blobs):
        raise GenerationError("historical blob identities collide")
    snapshot_count = _integer(root["snapshot_count"], "snapshot_count")
    entry_count = _integer(root["entry_count"], "entry_count")
    if snapshot_count != len(snapshots) or entry_count != len(blobs):
        raise GenerationError("historical counts disagree")
    entries_digest = _digest(root["entries_sha256"], "entries_sha256")
    if entries_digest != historical_entries_sha256(blobs):
        raise GenerationError("historical entries digest disagrees")
    return {
        "schema_version": root["schema_version"],
        "baseline_commit": _oid_value(root["baseline_commit"], "baseline_commit"),
        "snapshot_count": snapshot_count,
        "entry_count": entry_count,
        "entries_sha256": entries_digest,
        "approved_seed_sha256": _digest(
            root["approved_seed_sha256"], "approved_seed_sha256"
        ),
        "snapshots": snapshots,
        "blobs": blobs,
    }


def _parse_retained(document: dict[str, object]) -> dict[str, object]:
    root = _exact(document, _RETAINED_KEYS, "retained root")
    if _string(root["schema_version"], "schema_version") != "pontius-retained-v7-v1":
        raise GenerationError("retained schema literal is invalid")
    result: dict[str, object] = {"schema_version": root["schema_version"]}
    commit_fields = (
        "source_seal_commit",
        "authorization_commit",
        "historical_reader_commit",
    )
    digest_fields = ("journal_protocol_sha256", "campaign_sha256")
    integer_fields = (
        "record_count",
        "observation_count",
        "calibration_cell_count",
        "warmup_cell_count",
        "measured_labelled_partial_cell_count",
        "scientific_call_count",
        "authoritative_measured_call_count",
        "laboratory_elapsed_ns",
        "laboratory_wall_ns",
        "outside_laboratory_elapsed_ns",
        "outside_laboratory_wall_ns",
        "public_elapsed_ns",
        "public_wall_ns",
    )
    boolean_fields = (
        "journal_complete",
        "scientific_campaign_complete",
        "passed",
        "fit_projection_present",
        "candidate_selection_present",
        "topology_selection_present",
        "arithmetic_schedule_selection_present",
        "truncation_authorized",
    )
    for field in commit_fields:
        result[field] = _oid_value(root[field], field)
    for field in digest_fields:
        result[field] = _digest(root[field], field)
    for field in integer_fields:
        result[field] = _integer(root[field], field)
    for field in boolean_fields:
        result[field] = _boolean(root[field], field)
    for field in ("terminal", "production_base_classification"):
        result[field] = _string(root[field], field)
    result["historical_blobs_manifest_path"] = _path_value(
        root["historical_blobs_manifest_path"], "historical_blobs_manifest_path"
    )
    absent_values = _array(root["absent_launch_paths"], "absent_launch_paths")
    result["absent_launch_paths"] = [
        _path_value(value, "absent_launch_paths") for value in absent_values
    ]
    claim_values = _array(root["expected_null_claim_paths"], "expected_null_claim_paths")
    result["expected_null_claim_paths"] = [
        _string(value, "expected_null_claim_paths") for value in claim_values
    ]
    for field in ("result", "attempt", "consumed_launch"):
        result[field] = _parse_file_identity(root[field], field)
    return result


def validate_approval_digest(supplied: str | None, expected: str) -> str:
    supplied = validate_approval_format(supplied)
    if supplied != expected:
        raise GenerationError(
            "the supplied approval digest does not match the freshly derived seed"
        )
    return supplied


def validate_approval_format(supplied: str | None) -> str:
    if type(supplied) is not str or _HEX64.fullmatch(supplied) is None:
        raise GenerationError(
            "--write requires a lowercase 64-hex --approved-seed-sha256"
        )
    return supplied


def _directory_identity(info: Any) -> tuple[int, ...]:
    return (
        int(info.st_dev),
        int(info.st_ino),
        int(info.st_mode),
        int(getattr(info, "st_file_attributes", 0)),
        int(getattr(info, "st_reparse_tag", 0)),
    )


def _validated_directory(path: Path, description: str) -> tuple[int, ...]:
    try:
        info = os.lstat(path)
    except OSError as error:
        raise GenerationError(f"{description} cannot be inspected: {path}") from error
    if stat.S_ISLNK(info.st_mode) or _is_reparse(info) or not stat.S_ISDIR(info.st_mode):
        raise GenerationError(f"{description} is not a directory without links or reparses: {path}")
    return _directory_identity(info)


def _manifest_destinations(
    repository_root: Path, *, allow_missing_architecture: bool
) -> dict[str, Path]:
    if not repository_root.is_absolute():
        raise GenerationError("repository root must be absolute")
    _validated_directory(repository_root, "repository root")
    root = repository_root.resolve(strict=True)
    _validated_directory(root, "resolved repository root")
    docs = root / "docs"
    docs_identity = _validated_directory(docs, "manifest docs ancestor")
    architecture = docs / "architecture"
    try:
        architecture_identity = _validated_directory(
            architecture, "manifest architecture directory"
        )
    except GenerationError:
        if os.path.lexists(architecture) or not allow_missing_architecture:
            raise
        architecture_identity = None
    result: dict[str, Path] = {}
    for relative in MANIFEST_PATHS:
        destination = root / relative
        if destination.parent != architecture:
            raise GenerationError(
                "manifest destination is outside the exact architecture directory"
            )
        if os.path.lexists(destination):
            info = os.lstat(destination)
            if (
                stat.S_ISLNK(info.st_mode)
                or _is_reparse(info)
                or not stat.S_ISREG(info.st_mode)
            ):
                raise GenerationError(
                    f"manifest destination is not a regular nonreparse file: {relative}"
                )
        result[relative] = destination
    if _validated_directory(docs, "manifest docs ancestor") != docs_identity:
        raise GenerationError("manifest docs ancestor identity changed during destination validation")
    if architecture_identity is not None:
        if (
            _validated_directory(architecture, "manifest architecture directory")
            != architecture_identity
        ):
            raise GenerationError("manifest architecture directory identity changed")
    return result


def _verified_destinations(repository_root: Path) -> dict[str, Path]:
    return _manifest_destinations(repository_root, allow_missing_architecture=False)


def _validated_write_destination_intent(repository_root: Path) -> dict[str, Path]:
    return _manifest_destinations(repository_root, allow_missing_architecture=True)


if os.name == "nt":
    class _WindowsDirectoryInformation(ctypes.Structure):
        _fields_ = (
            ("dwFileAttributes", wintypes.DWORD),
            ("ftCreationTime", wintypes.FILETIME),
            ("ftLastAccessTime", wintypes.FILETIME),
            ("ftLastWriteTime", wintypes.FILETIME),
            ("dwVolumeSerialNumber", wintypes.DWORD),
            ("nFileSizeHigh", wintypes.DWORD),
            ("nFileSizeLow", wintypes.DWORD),
            ("nNumberOfLinks", wintypes.DWORD),
            ("nFileIndexHigh", wintypes.DWORD),
            ("nFileIndexLow", wintypes.DWORD),
        )


    class _WindowsUnicodeString(ctypes.Structure):
        _fields_ = (
            ("Length", wintypes.USHORT),
            ("MaximumLength", wintypes.USHORT),
            ("Buffer", wintypes.LPWSTR),
        )


    class _WindowsObjectAttributes(ctypes.Structure):
        _fields_ = (
            ("Length", wintypes.ULONG),
            ("RootDirectory", wintypes.HANDLE),
            ("ObjectName", ctypes.POINTER(_WindowsUnicodeString)),
            ("Attributes", wintypes.ULONG),
            ("SecurityDescriptor", wintypes.LPVOID),
            ("SecurityQualityOfService", wintypes.LPVOID),
        )


    class _WindowsIOStatusValue(ctypes.Union):
        _fields_ = (("Status", wintypes.LONG), ("Pointer", wintypes.LPVOID))


    class _WindowsIOStatusBlock(ctypes.Structure):
        _anonymous_ = ("value",)
        _fields_ = (("value", _WindowsIOStatusValue), ("Information", ctypes.c_size_t))


    class _WindowsFileRenameInformation(ctypes.Structure):
        _fields_ = (
            ("ReplaceIfExists", ctypes.c_ubyte),
            ("RootDirectory", wintypes.HANDLE),
            ("FileNameLength", wintypes.DWORD),
            ("FileName", wintypes.WCHAR * 1),
        )


    class _WindowsFileDispositionInformation(ctypes.Structure):
        _fields_ = (("DeleteFile", ctypes.c_ubyte),)


def _windows_directory_api() -> tuple[Any, Any, Any]:
    if os.name != "nt":
        raise GenerationError("Windows directory handles are unavailable")
    try:
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        create = kernel32.CreateFileW
        create.argtypes = (
            wintypes.LPCWSTR,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.LPVOID,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.HANDLE,
        )
        create.restype = wintypes.HANDLE
        information = kernel32.GetFileInformationByHandle
        information.argtypes = (
            wintypes.HANDLE,
            ctypes.POINTER(_WindowsDirectoryInformation),
        )
        information.restype = wintypes.BOOL
        close = kernel32.CloseHandle
        close.argtypes = (wintypes.HANDLE,)
        close.restype = wintypes.BOOL
    except Exception as error:
        raise GenerationError("Windows directory handle APIs are unavailable") from error
    return create, information, close


def _windows_open_directory(
    path: Path,
    *,
    owner: _BoundManifestDirectory | None = None,
) -> int:
    create, _, close = _windows_directory_api()
    try:
        handle = create(
            str(path),
            0x00000020 | 0x00000080 | 0x00100000,
            0x00000001 | 0x00000002,
            None,
            3,
            0x02000000 | 0x00200000,
            None,
        )
    except Exception as error:
        raise GenerationError(f"manifest directory handle could not be opened: {path}") from error
    invalid = ctypes.c_void_p(-1).value
    if not handle or handle == invalid:
        error = ctypes.get_last_error()
        raise GenerationError(f"manifest directory handle could not be opened: {path}") from OSError(
            error, os.strerror(error), str(path)
        )
    numeric_handle = int(handle)
    owned_entry: tuple[Path, int, tuple[int, int] | None] | None = None
    if owner is not None:
        owned_entry = (path, numeric_handle, None)
        owner._windows_handles.append(owned_entry)
    try:
        identity = _windows_directory_handle_identity(numeric_handle, path)
    except BaseException as body_error:
        if owner is not None:
            raise
        close_failure = None
        try:
            succeeded = close(numeric_handle)
        except Exception as error:
            close_failure = GenerationError("manifest directory handle close failed")
            close_failure.__cause__ = error
        else:
            if not succeeded:
                error = ctypes.get_last_error()
                close_failure = GenerationError("manifest directory handle close failed")
                close_failure.__cause__ = OSError(error, os.strerror(error))
        if close_failure is not None:
            aggregate = _aggregate_generation_errors(
                "manifest directory inspection and close both failed",
                (body_error, close_failure),
            )
            raise aggregate from body_error
        raise
    if owner is not None:
        assert owned_entry is not None
        for index, entry in enumerate(owner._windows_handles):
            if entry is owned_entry:
                owner._windows_handles[index] = (path, numeric_handle, identity)
                break
        else:
            raise GenerationError("manifest directory handle ownership was lost")
    return numeric_handle


def _windows_directory_handle_identity(handle: int, path: Path) -> tuple[int, int]:
    _, information, _ = _windows_directory_api()
    value = _WindowsDirectoryInformation()
    try:
        succeeded = information(handle, ctypes.byref(value))
    except Exception as error:
        raise GenerationError(f"manifest directory handle cannot be inspected: {path}") from error
    if not succeeded:
        error = ctypes.get_last_error()
        raise GenerationError(f"manifest directory handle cannot be inspected: {path}") from OSError(
            error, os.strerror(error), str(path)
        )
    attributes = int(value.dwFileAttributes)
    if not attributes & 0x00000010 or attributes & _REPARSE_ATTRIBUTE:
        raise GenerationError(f"manifest directory handle is not a nonreparse directory: {path}")
    file_index = (int(value.nFileIndexHigh) << 32) | int(value.nFileIndexLow)
    return int(value.dwVolumeSerialNumber), file_index


def _close_windows_directory(handle: int) -> None:
    _, _, close = _windows_directory_api()
    try:
        succeeded = close(handle)
    except Exception as error:
        raise GenerationError("manifest directory handle close failed") from error
    if not succeeded:
        error = ctypes.get_last_error()
        raise GenerationError("manifest directory handle close failed") from OSError(
            error, os.strerror(error)
        )


def _windows_file_api() -> tuple[Any, Any, Any, Any, Any]:
    if os.name != "nt":
        raise GenerationError("Windows handle-relative file APIs are unavailable")
    try:
        ntdll = ctypes.WinDLL("ntdll")
        create = ntdll.NtCreateFile
        create.argtypes = (
            ctypes.POINTER(wintypes.HANDLE),
            wintypes.DWORD,
            ctypes.POINTER(_WindowsObjectAttributes),
            ctypes.POINTER(_WindowsIOStatusBlock),
            wintypes.LPVOID,
            wintypes.ULONG,
            wintypes.ULONG,
            wintypes.ULONG,
            wintypes.ULONG,
            wintypes.LPVOID,
            wintypes.ULONG,
        )
        create.restype = wintypes.LONG
        set_information = ntdll.NtSetInformationFile
        set_information.argtypes = (
            wintypes.HANDLE,
            ctypes.POINTER(_WindowsIOStatusBlock),
            wintypes.LPVOID,
            wintypes.ULONG,
            ctypes.c_int,
        )
        set_information.restype = wintypes.LONG
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        write = kernel32.WriteFile
        write.argtypes = (
            wintypes.HANDLE,
            wintypes.LPCVOID,
            wintypes.DWORD,
            wintypes.LPDWORD,
            wintypes.LPVOID,
        )
        write.restype = wintypes.BOOL
        flush = kernel32.FlushFileBuffers
        flush.argtypes = (wintypes.HANDLE,)
        flush.restype = wintypes.BOOL
        close = kernel32.CloseHandle
        close.argtypes = (wintypes.HANDLE,)
        close.restype = wintypes.BOOL
    except Exception as error:
        raise GenerationError("Windows handle-relative file APIs are unavailable") from error
    return create, set_information, write, flush, close


def _validated_relative_manifest_name(name: str) -> str:
    if (
        not isinstance(name, str)
        or not name
        or name in (".", "..")
        or any(character in name for character in ("/", "\\", ":", "\0"))
    ):
        raise GenerationError("manifest mutation name must be one relative path component")
    return name


def _is_valid_windows_handle(value: object) -> bool:
    invalid = ctypes.c_void_p(-1).value
    return value is not None and bool(value) and int(value) != invalid


def _windows_create_relative_file(
    directory_handle: int,
    name: str,
    *,
    owner: _BoundTemporary | None = None,
) -> int:
    name = _validated_relative_manifest_name(name)
    create, _, _, _, _ = _windows_file_api()
    encoded_name = name.encode("utf-16-le")
    if len(encoded_name) > 0xFFFE:
        raise GenerationError("manifest temporary name is too long")
    name_buffer = ctypes.create_unicode_buffer(name)
    unicode_name = _WindowsUnicodeString(
        len(encoded_name),
        len(encoded_name),
        ctypes.cast(name_buffer, wintypes.LPWSTR),
    )
    attributes = _WindowsObjectAttributes(
        ctypes.sizeof(_WindowsObjectAttributes),
        wintypes.HANDLE(directory_handle),
        ctypes.pointer(unicode_name),
        0x00000040,
        None,
        None,
    )
    status_block = _WindowsIOStatusBlock()
    handle = wintypes.HANDLE()
    candidate = owner or _BoundTemporary(name, None, windows=True)
    try:
        status = int(
            create(
                ctypes.byref(handle),
                0x00000002 | 0x00000080 | 0x00010000 | 0x00100000,
                ctypes.byref(attributes),
                ctypes.byref(status_block),
                None,
                0x00000080,
                0,
                2,
                0x00000020 | 0x00000040,
                None,
                0,
            )
        )
    except Exception as error:
        if _is_valid_windows_handle(handle.value):
            candidate.claim_windows_handle(int(handle.value))
        failure = GenerationError("handle-relative manifest temporary creation failed")
        if owner is None:
            try:
                _cleanup_windows_temporary(candidate)
            except GenerationError as cleanup_error:
                aggregate = _aggregate_generation_errors(
                    "manifest temporary creation and cleanup both failed",
                    (failure, cleanup_error),
                    retained_owners=(candidate,)
                    if candidate.state != "closed"
                    else (),
                )
                raise aggregate from error
        raise failure from error
    invalid_handle = ctypes.c_void_p(-1).value
    if handle.value and int(handle.value) != invalid_handle:
        candidate.claim_windows_handle(int(handle.value))
    if (
        status != 0
        or int(status_block.Status) != 0
        or int(status_block.Information) != 2
        or not handle.value
        or int(handle.value) == invalid_handle
    ):
        failure = GenerationError(
            "handle-relative manifest temporary creation returned malformed status "
            f"0x{status & 0xFFFFFFFF:08x}/{int(status_block.Status) & 0xFFFFFFFF:08x}/"
            f"{int(status_block.Information)}"
        )
        if owner is None:
            try:
                _cleanup_windows_temporary(candidate)
            except GenerationError as cleanup_error:
                aggregate = _aggregate_generation_errors(
                    "malformed manifest temporary creation and cleanup both failed",
                    (failure, cleanup_error),
                    retained_owners=(candidate,)
                    if candidate.state != "closed"
                    else (),
                )
                raise aggregate from failure
        raise failure
    return int(handle.value)


def _windows_write_file(file_handle: int, raw: bytes) -> None:
    if not isinstance(raw, bytes):
        raise GenerationError("manifest temporary content must be bytes")
    _, _, write, _, _ = _windows_file_api()
    offset = 0
    while offset < len(raw):
        chunk = raw[offset : offset + 0xFFFFFFFF]
        buffer = ctypes.create_string_buffer(chunk)
        written = wintypes.DWORD()
        try:
            succeeded = write(
                wintypes.HANDLE(file_handle),
                ctypes.byref(buffer),
                len(chunk),
                ctypes.byref(written),
                None,
            )
        except Exception as error:
            raise GenerationError("handle-bound manifest temporary write failed") from error
        if not succeeded:
            error = ctypes.get_last_error()
            raise GenerationError("handle-bound manifest temporary write failed") from OSError(
                error, os.strerror(error)
            )
        count = int(written.value)
        if count <= 0 or count > len(chunk):
            raise GenerationError("handle-bound manifest temporary write returned malformed length")
        offset += count


def _windows_flush_file(file_handle: int) -> None:
    _, _, _, flush, _ = _windows_file_api()
    try:
        succeeded = flush(wintypes.HANDLE(file_handle))
    except Exception as error:
        raise GenerationError("handle-bound manifest temporary flush failed") from error
    if not succeeded:
        error = ctypes.get_last_error()
        raise GenerationError("handle-bound manifest temporary flush failed") from OSError(
            error, os.strerror(error)
        )


def _windows_close_file_handle(file_handle: int) -> None:
    _, _, _, _, close = _windows_file_api()
    try:
        succeeded = close(wintypes.HANDLE(file_handle))
    except Exception as error:
        raise GenerationError("manifest temporary handle close failed") from error
    if not succeeded:
        error = ctypes.get_last_error()
        raise GenerationError("manifest temporary handle close failed") from OSError(
            error, os.strerror(error)
        )


def _windows_rename_relative_file(
    file_handle: int, directory_handle: int, destination_name: str
) -> None:
    destination_name = _validated_relative_manifest_name(destination_name)
    _, set_information, _, _, _ = _windows_file_api()
    encoded_name = destination_name.encode("utf-16-le")
    name_offset = _WindowsFileRenameInformation.FileName.offset
    buffer = ctypes.create_string_buffer(name_offset + len(encoded_name))
    information = ctypes.cast(
        buffer, ctypes.POINTER(_WindowsFileRenameInformation)
    ).contents
    information.ReplaceIfExists = 1
    information.RootDirectory = wintypes.HANDLE(directory_handle)
    information.FileNameLength = len(encoded_name)
    ctypes.memmove(ctypes.addressof(buffer) + name_offset, encoded_name, len(encoded_name))
    status_block = _WindowsIOStatusBlock()
    try:
        status = int(
            set_information(
                wintypes.HANDLE(file_handle),
                ctypes.byref(status_block),
                ctypes.byref(buffer),
                len(buffer),
                10,
            )
        )
    except Exception as error:
        raise GenerationError("handle-relative manifest replacement failed") from error
    if status != 0 or int(status_block.Status) != 0:
        raise GenerationError(
            "handle-relative manifest replacement returned malformed status "
            f"0x{status & 0xFFFFFFFF:08x}/{int(status_block.Status) & 0xFFFFFFFF:08x}"
        )


def _windows_set_relative_disposition(file_handle: int, delete: bool) -> None:
    _, set_information, _, _, _ = _windows_file_api()
    information = _WindowsFileDispositionInformation(int(delete))
    status_block = _WindowsIOStatusBlock()
    try:
        status = int(
            set_information(
                wintypes.HANDLE(file_handle),
                ctypes.byref(status_block),
                ctypes.byref(information),
                ctypes.sizeof(information),
                13,
            )
        )
    except Exception as error:
        raise GenerationError("handle-bound manifest disposition failed") from error
    if status != 0 or int(status_block.Status) != 0:
        raise GenerationError(
            "handle-bound manifest disposition returned malformed status "
            f"0x{status & 0xFFFFFFFF:08x}/{int(status_block.Status) & 0xFFFFFFFF:08x}"
        )


def _windows_dispose_relative_file(file_handle: int) -> None:
    _windows_set_relative_disposition(file_handle, True)


class _BoundTemporary:
    def __init__(
        self,
        name: str,
        handle: int | None,
        *,
        windows: bool | None = None,
    ) -> None:
        self.name = name
        self.handle = handle
        is_windows = handle is not None if windows is None else windows
        if is_windows:
            self.state = "open" if handle is not None else "unacquired"
        else:
            self.state = "path_owned"

    @property
    def renamed(self) -> bool:
        return self.state == "renamed"

    def claim_windows_handle(self, handle: int) -> None:
        if self.state != "unacquired" or self.handle is not None:
            raise GenerationError("manifest temporary handle ownership transition is invalid")
        if not _is_valid_windows_handle(handle):
            raise GenerationError("manifest temporary handle ownership is invalid")
        self.handle = int(handle)
        self.state = "open"

    def mark_deletion_armed(self) -> None:
        if self.state != "open" or self.handle is None:
            raise GenerationError("manifest temporary deletion transition is invalid")
        self.state = "deletion_armed"

    def mark_renamed(self) -> None:
        if self.state != "open" or self.handle is None:
            raise GenerationError("manifest temporary rename transition is invalid")
        self.state = "renamed"

    def mark_closed(self) -> None:
        if self.state == "unacquired" and self.handle is None:
            self.state = "closed"
            return
        if self.state not in ("deletion_armed", "renamed") or self.handle is None:
            raise GenerationError("manifest temporary close transition is invalid")
        self.handle = None
        self.state = "closed"


def _cleanup_windows_temporary(temporary: _BoundTemporary) -> None:
    if temporary.state == "closed":
        return
    if temporary.state == "unacquired":
        temporary.mark_closed()
        return
    if temporary.state not in ("open", "deletion_armed", "renamed"):
        raise GenerationError("Windows manifest temporary state is invalid")
    if temporary.handle is None:
        raise GenerationError("Windows manifest temporary handle is absent")

    failures: list[GenerationError] = []
    if temporary.state == "open":
        for _ in range(2):
            try:
                _windows_dispose_relative_file(temporary.handle)
            except GenerationError as error:
                failures.append(error)
            except Exception as error:
                failure = GenerationError("handle-bound manifest disposition failed")
                failure.__cause__ = error
                failures.append(failure)
            else:
                temporary.mark_deletion_armed()
                break
        if temporary.state == "open":
            aggregate = _aggregate_generation_errors(
                "manifest temporary deletion could not be armed; handle remains open",
                failures,
                retained_owners=(temporary,),
            )
            raise aggregate from failures[0]

    try:
        _windows_close_file_handle(temporary.handle)
    except GenerationError as error:
        failures.append(error)
    except Exception as error:
        failure = GenerationError("manifest temporary handle close failed")
        failure.__cause__ = error
        failures.append(failure)
    else:
        temporary.mark_closed()

    if failures:
        retained = (temporary,) if temporary.state != "closed" else ()
        aggregate = _aggregate_generation_errors(
            "manifest temporary cleanup failed",
            failures,
            retained_owners=retained,
        )
        raise aggregate from failures[0]


class _BoundManifestDirectory:
    def __init__(self, repository_root: Path, *, create_missing: bool) -> None:
        self.repository_root = repository_root
        self.create_missing = create_missing
        self.root: Path | None = None
        self.docs: Path | None = None
        self.architecture: Path | None = None
        self.destinations: dict[str, Path] = {}
        self._posix_descriptors: list[tuple[Path, int, tuple[int, int]]] = []
        self._windows_handles: list[tuple[Path, int, tuple[int, int] | None]] = []
        self._architecture_descriptor: int | None = None
        self._owned_temporary: list[_BoundTemporary] = []

    def __enter__(self) -> "_BoundManifestDirectory":
        if not self.repository_root.is_absolute():
            raise GenerationError("repository root must be absolute")
        _validated_directory(self.repository_root, "repository root")
        self.root = self.repository_root.resolve(strict=True)
        self.docs = self.root / "docs"
        self.architecture = self.docs / "architecture"
        try:
            if os.name == "nt":
                self._bind_windows()
            else:
                self._bind_posix()
            self.destinations = _verified_destinations(self.root)
            self.reverify()
            return self
        except BaseException as body_error:
            try:
                self.close()
            except GenerationError as cleanup_error:
                aggregate = _aggregate_generation_errors(
                    "manifest transaction setup and cleanup both failed",
                    (body_error, cleanup_error),
                )
                raise aggregate from body_error
            if isinstance(body_error, Exception) and not isinstance(
                body_error, GenerationError
            ):
                failure = GenerationError(
                    "manifest transaction setup failed",
                    failures=(body_error,),
                )
                raise failure from body_error
            raise

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        try:
            self.close()
        except GenerationError as cleanup_error:
            if not isinstance(exc, BaseException):
                raise
            aggregate = _aggregate_generation_errors(
                "manifest transaction body and cleanup both failed",
                (exc, cleanup_error),
            )
            raise aggregate from exc

    def _bind_windows(self) -> None:
        assert self.root is not None and self.docs is not None and self.architecture is not None
        for path in (self.root, self.docs):
            _windows_open_directory(path, owner=self)
        if not os.path.lexists(self.architecture):
            if not self.create_missing:
                raise GenerationError("manifest architecture directory is absent")
            try:
                os.mkdir(self.architecture)
            except OSError as error:
                raise GenerationError(
                    "manifest architecture directory could not be securely created"
                ) from error
        _windows_open_directory(self.architecture, owner=self)

    def _bind_posix(self) -> None:
        assert self.root is not None and self.docs is not None and self.architecture is not None
        required = ("O_DIRECTORY", "O_NOFOLLOW")
        dir_fd_functions = (os.open, os.mkdir, os.replace, os.unlink)
        if (
            any(not hasattr(os, name) for name in required)
            or any(function not in os.supports_dir_fd for function in dir_fd_functions)
        ):
            raise GenerationError("secure POSIX directory primitives are unavailable")
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
        try:
            root_descriptor = os.open(self.root, flags)
            root_info = os.fstat(root_descriptor)
            self._posix_descriptors.append(
                (self.root, root_descriptor, (int(root_info.st_dev), int(root_info.st_ino)))
            )
            docs_descriptor = os.open("docs", flags, dir_fd=root_descriptor)
            docs_info = os.fstat(docs_descriptor)
            self._posix_descriptors.append(
                (self.docs, docs_descriptor, (int(docs_info.st_dev), int(docs_info.st_ino)))
            )
            try:
                architecture_descriptor = os.open("architecture", flags, dir_fd=docs_descriptor)
            except OSError as error:
                if error.errno != errno.ENOENT or not self.create_missing:
                    raise
                os.mkdir("architecture", dir_fd=docs_descriptor)
                architecture_descriptor = os.open("architecture", flags, dir_fd=docs_descriptor)
            architecture_info = os.fstat(architecture_descriptor)
            self._posix_descriptors.append(
                (
                    self.architecture,
                    architecture_descriptor,
                    (int(architecture_info.st_dev), int(architecture_info.st_ino)),
                )
            )
            self._architecture_descriptor = architecture_descriptor
        except OSError as error:
            raise GenerationError("manifest directory chain could not be securely bound") from error

    def reverify(self) -> None:
        if os.name == "nt":
            for path, handle, expected in self._windows_handles:
                if expected is None:
                    raise GenerationError(
                        f"manifest directory handle identity is unverified: {path}"
                    )
                if _windows_directory_handle_identity(handle, path) != expected:
                    raise GenerationError(f"held manifest directory identity changed: {path}")
                info = os.lstat(path)
                if (
                    stat.S_ISLNK(info.st_mode)
                    or _is_reparse(info)
                    or not stat.S_ISDIR(info.st_mode)
                    or int(info.st_ino) != expected[1]
                ):
                    raise GenerationError(f"manifest directory path no longer names its held handle: {path}")
        else:
            for path, descriptor, expected in self._posix_descriptors:
                handle_info = os.fstat(descriptor)
                handle_identity = (int(handle_info.st_dev), int(handle_info.st_ino))
                path_info = os.lstat(path)
                path_identity = (int(path_info.st_dev), int(path_info.st_ino))
                if (
                    handle_identity != expected
                    or path_identity != expected
                    or stat.S_ISLNK(path_info.st_mode)
                    or not stat.S_ISDIR(path_info.st_mode)
                ):
                    raise GenerationError(f"manifest directory path no longer names its held handle: {path}")

    def stage(self, destination: Path, raw: bytes) -> _BoundTemporary:
        assert self.architecture is not None
        self.reverify()
        name = f".{destination.name}.{uuid.uuid4().hex}.tmp"
        if os.name == "nt":
            if not self._windows_handles:
                raise GenerationError("Windows manifest directory handle is absent")
            architecture_handle = self._windows_handles[-1][1]
            temporary = _BoundTemporary(name, None, windows=True)
            self._owned_temporary.append(temporary)
            try:
                handle = _windows_create_relative_file(
                    architecture_handle,
                    name,
                    owner=temporary,
                )
            except GenerationError:
                raise
            except OSError as error:
                raise GenerationError("manifest temporary file could not be created") from error
            if temporary.handle != handle or temporary.state != "open":
                raise GenerationError("Windows manifest temporary ownership was not registered")
            try:
                self.reverify()
                _windows_write_file(temporary.handle, raw)
                _windows_flush_file(temporary.handle)
                self.reverify()
                return temporary
            except GenerationError:
                raise
            except OSError as error:
                raise GenerationError("manifest temporary file could not be staged") from error
        if self._architecture_descriptor is None:
            raise GenerationError("POSIX manifest directory descriptor is absent")
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
        try:
            descriptor = os.open(name, flags, 0o600, dir_fd=self._architecture_descriptor)
        except OSError as error:
            raise GenerationError("manifest temporary file could not be created") from error
        temporary = _BoundTemporary(name, None)
        self._owned_temporary.append(temporary)
        try:
            offset = 0
            while offset < len(raw):
                written = os.write(descriptor, raw[offset:])
                if written <= 0:
                    raise OSError("manifest temporary write made no progress")
                offset += written
            os.fsync(descriptor)
            self.reverify()
        except GenerationError:
            raise
        except OSError as error:
            raise GenerationError("manifest temporary file could not be staged") from error
        finally:
            os.close(descriptor)
        return temporary

    def replace(self, temporary: _BoundTemporary, destination: Path) -> None:
        if temporary not in self._owned_temporary:
            raise GenerationError("manifest temporary ownership is invalid")
        self.reverify()
        if os.name == "nt":
            if temporary.handle is None or not self._windows_handles:
                raise GenerationError("Windows manifest temporary handle is absent")
            architecture_handle = self._windows_handles[-1][1]
            _windows_rename_relative_file(
                temporary.handle, architecture_handle, destination.name
            )
            temporary.mark_renamed()
            self.cleanup(temporary)
            self.reverify()
            return
        if self._architecture_descriptor is None:
            raise GenerationError("POSIX manifest replacement arguments are invalid")
        os.replace(
            temporary.name,
            destination.name,
            src_dir_fd=self._architecture_descriptor,
            dst_dir_fd=self._architecture_descriptor,
        )
        self._owned_temporary.remove(temporary)
        self.reverify()

    def cleanup(self, temporary: _BoundTemporary) -> None:
        if temporary not in self._owned_temporary:
            return
        if os.name == "nt":
            try:
                _cleanup_windows_temporary(temporary)
            finally:
                if temporary.state == "closed" and temporary in self._owned_temporary:
                    self._owned_temporary.remove(temporary)
            return
        if self._architecture_descriptor is None:
            raise GenerationError("POSIX manifest directory descriptor is absent")
        try:
            os.unlink(temporary.name, dir_fd=self._architecture_descriptor)
        except FileNotFoundError:
            pass
        self._owned_temporary.remove(temporary)

    def close(self) -> None:
        failures: list[GenerationError] = []
        for temporary in tuple(self._owned_temporary):
            try:
                self.cleanup(temporary)
            except GenerationError as error:
                failures.append(error)
        for entry in tuple(reversed(self._posix_descriptors)):
            _, descriptor, _ = entry
            try:
                os.close(descriptor)
            except OSError as error:
                failures.append(
                    GenerationError("POSIX manifest directory descriptor close failed")
                )
                failures[-1].__cause__ = error
            else:
                self._posix_descriptors.remove(entry)
        for entry in tuple(reversed(self._windows_handles)):
            _, handle, _ = entry
            try:
                _close_windows_directory(handle)
            except GenerationError as error:
                failures.append(error)
            else:
                self._windows_handles.remove(entry)
        if failures:
            retained = (
                (self,)
                if self._owned_temporary
                or self._posix_descriptors
                or self._windows_handles
                else ()
            )
            aggregate = _aggregate_generation_errors(
                "manifest transaction cleanup failed",
                failures,
                retained_owners=retained,
            )
            raise aggregate from failures[0]


def write_manifests(
    repository_root: Path,
    state: Mapping[str, object],
    *,
    approved_seed_sha256: str | None,
) -> None:
    approved = validate_approval_digest(
        approved_seed_sha256, str(state["entries_sha256"])
    )
    rendered = _render_all(state, approved)
    with _BoundManifestDirectory(repository_root, create_missing=True) as transaction:
        temporary: dict[str, _BoundTemporary] = {}
        for relative, destination in transaction.destinations.items():
            temporary[relative] = transaction.stage(destination, rendered[relative])
        transaction.reverify()
        for relative, destination in transaction.destinations.items():
            transaction.replace(temporary[relative], destination)
        transaction.reverify()


def check_manifests(
    repository_root: Path, state: Mapping[str, object]
) -> None:
    historical_path = repository_root / MANIFEST_PATHS[2]
    try:
        historical_raw = read_regular_file_once(
            historical_path, maximum_bytes=4 * 1024 * 1024
        )
    except GenerationError as error:
        raise GenerationError(
            "historical manifest is absent or unreadable; approval and --write are still required"
        ) from error
    historical = parse_manifest_bytes(
        "historical-blobs",
        historical_raw,
        source_path=historical_path,
        repository_root=repository_root,
    )
    approved = validate_approval_digest(
        str(historical["approved_seed_sha256"]), str(state["entries_sha256"])
    )
    rendered = _render_all(state, approved)
    for relative, expected in rendered.items():
        path = repository_root / relative
        actual = read_regular_file_once(path, maximum_bytes=4 * 1024 * 1024)
        if actual != expected:
            raise GenerationError(
                f"manifest bytes differ from deterministic generation: {relative}"
            )


def render_seed_review(state: Mapping[str, object]) -> bytes:
    lines = [
        "pontius evidence historical seed review v1",
        f"normalized_sha256\t{state['entries_sha256']}",
        (
            "columns\tcommit\trelative_path\tgit_blob_oid\traw_sha256\trole\tphase"
            "\tgoverning_decision"
        ),
    ]
    for row in state["blobs"]:
        values = (
            row["commit"],
            row["relative_path"],
            row["git_blob_oid"],
            row["raw_sha256"],
            row["role"],
            row["phase"],
            row["governing_decision"],
        )
        if any(
            "\t" in str(value) or "\n" in str(value) or "\r" in str(value)
            for value in values
        ):
            raise GenerationError(
                "seed review field contains a forbidden control character"
            )
        lines.append("row\t" + "\t".join(str(value) for value in values))
    return ("\n".join(lines) + "\n").encode("utf-8")


def emit_seed_review(
    repository_root: Path,
    state: Mapping[str, object],
    output_path: Path,
) -> None:
    output_path = _validated_seed_review_output(repository_root, output_path)
    raw = render_seed_review(state)
    candidate = output_path.parent / f".{output_path.name}.{uuid.uuid4().hex}.tmp"
    try:
        with candidate.open("xb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(candidate, output_path)
    finally:
        try:
            candidate.unlink()
        except FileNotFoundError:
            pass


def _validated_seed_review_output(repository_root: Path, output_path: Path) -> Path:
    if not output_path.is_absolute():
        raise GenerationError("seed review output path must be absolute")
    repository = repository_root.resolve(strict=True)
    temporary_root = Path(tempfile.gettempdir()).resolve(strict=True)
    parent = output_path.parent.resolve(strict=True)
    resolved_output = output_path.resolve(strict=False)
    try:
        resolved_output.relative_to(temporary_root)
    except ValueError as error:
        raise GenerationError(
            "seed review output must be below the operating-system temporary directory"
        ) from error
    try:
        resolved_output.relative_to(repository)
    except ValueError:
        pass
    else:
        raise GenerationError("seed review output must be outside the repository")
    if parent != temporary_root and temporary_root not in parent.parents:
        raise GenerationError(
            "seed review parent is outside the operating-system temporary directory"
        )
    if os.path.lexists(output_path):
        info = os.lstat(output_path)
        if (
            stat.S_ISLNK(info.st_mode)
            or _is_reparse(info)
            or not stat.S_ISREG(info.st_mode)
        ):
            raise GenerationError(
                "seed review destination is not a regular nonreparse file"
            )
    return output_path


def _preflight_check(repository_root: Path) -> None:
    historical_path = repository_root / MANIFEST_PATHS[2]
    try:
        raw = read_regular_file_once(historical_path, maximum_bytes=4 * 1024 * 1024)
    except GenerationError as error:
        raise GenerationError(
            "historical manifest is absent or unreadable; approval and --write are still required"
        ) from error
    parsed = parse_manifest_bytes(
        "historical-blobs", raw, source_path=historical_path, repository_root=repository_root
    )
    validate_approval_format(str(parsed["approved_seed_sha256"]))


def _arguments(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_mutually_exclusive_group()
    commands.add_argument(
        "--check",
        action="store_true",
        help="compare generated bytes without writing (default)",
    )
    commands.add_argument(
        "--emit-seed-review", type=Path, metavar="ABSOLUTE_TEMP_PATH"
    )
    commands.add_argument(
        "--write",
        action="store_true",
        help="write only with the exact approved seed digest",
    )
    parser.add_argument("--approved-seed-sha256")
    parsed = parser.parse_args(argv)
    if parsed.approved_seed_sha256 is not None and not parsed.write:
        parser.error("--approved-seed-sha256 is valid only with --write")
    return parsed


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _arguments(argv)
    repository_root = Path(__file__).resolve().parents[1]
    try:
        if arguments.emit_seed_review is not None:
            _validated_seed_review_output(repository_root, arguments.emit_seed_review)
        elif arguments.write:
            validate_approval_format(arguments.approved_seed_sha256)
            _validated_write_destination_intent(repository_root)
        else:
            _preflight_check(repository_root)
        state = derive_manifest_state(repository_root)
        if arguments.emit_seed_review is not None:
            emit_seed_review(repository_root, state, arguments.emit_seed_review)
        elif arguments.write:
            write_manifests(
                repository_root,
                state,
                approved_seed_sha256=arguments.approved_seed_sha256,
            )
        else:
            check_manifests(repository_root, state)
    except GenerationError as error:
        print(f"evidence manifest generation failed: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
