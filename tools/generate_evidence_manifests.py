"""Deterministically derive and guard the evidence-boundary manifests.

This tool is standard-library-only and deliberately does not import pontius.
"""

from __future__ import annotations

import argparse
import ast
from collections.abc import Mapping, Sequence
from hashlib import sha256
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import stat
import subprocess
import sys
import tempfile
import tomllib
from typing import Any
import uuid


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
_PATH_LITERAL = re.compile(r"(?:src/pontius|tests|experiments/configs|docs/decisions|artifacts/work_preflight)/[A-Za-z0-9_./-]+")
_REPARSE_ATTRIBUTE = 0x400


class GenerationError(RuntimeError):
    """A fail-closed generator error."""


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


def read_regular_file_once(path: Path, *, maximum_bytes: int) -> bytes:
    """Read one bounded snapshot from a regular nonlink/nonreparse path."""
    if (
        type(maximum_bytes) is not int
        or maximum_bytes < 0
        or not isinstance(path, Path)
        or not path.is_absolute()
    ):
        raise GenerationError("secure read arguments are invalid")
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
        with os.fdopen(descriptor, "rb", closefd=True) as stream:
            descriptor = -1
            raw = stream.read(maximum_bytes + 1)
            after_handle = os.fstat(stream.fileno())
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


def _validated_executable() -> tuple[Path, tuple[int, ...]]:
    try:
        resolved = GIT_EXECUTABLE.resolve(strict=True)
    except OSError as error:
        raise GenerationError("the bound Git executable is unavailable") from error
    if os.path.normcase(str(resolved)) != os.path.normcase(str(GIT_EXECUTABLE)):
        raise GenerationError("the bound Git executable resolved to a different identity")
    for component in (resolved, *resolved.parents[:-1]):
        info = os.lstat(component)
        if stat.S_ISLNK(info.st_mode) or _is_reparse(info):
            raise GenerationError("the bound Git executable has a link or reparse component")
    info = os.lstat(resolved)
    if not stat.S_ISREG(info.st_mode):
        raise GenerationError("the bound Git executable is not regular")
    return resolved, _identity(info)


class _Git:
    def __init__(self, repository_root: Path, private_home: Path) -> None:
        self.root = repository_root.resolve(strict=True)
        self.executable, self.executable_identity = _validated_executable()
        self.environment = git_environment(private_home)
        self._cache: dict[tuple[str, ...], bytes] = {}

    def _run(self, arguments: Sequence[str], *, maximum_stdout: int) -> bytes:
        key = tuple(arguments)
        if key in self._cache:
            return self._cache[key]
        if _identity(os.lstat(self.executable)) != self.executable_identity:
            raise GenerationError("the bound Git executable identity changed")
        with tempfile.TemporaryFile() as stdout_file, tempfile.TemporaryFile() as stderr_file:
            try:
                completed = subprocess.run(
                    [str(self.executable), *arguments],
                    cwd=self.root,
                    env=self.environment,
                    stdin=subprocess.DEVNULL,
                    stdout=stdout_file,
                    stderr=stderr_file,
                    timeout=10.0,
                    check=False,
                    shell=False,
                )
            except subprocess.TimeoutExpired as error:
                raise GenerationError(f"Git command timed out: {arguments[0]}") from error
            if _identity(os.lstat(self.executable)) != self.executable_identity:
                raise GenerationError("the bound Git executable identity changed during execution")
            stdout_file.seek(0, os.SEEK_END)
            stdout_size = stdout_file.tell()
            stderr_file.seek(0, os.SEEK_END)
            stderr_size = stderr_file.tell()
            if stdout_size > maximum_stdout or stderr_size > 65536:
                raise GenerationError(f"Git command output exceeded its bound: {arguments[0]}")
            stdout_file.seek(0)
            stderr_file.seek(0)
            stdout = stdout_file.read(maximum_stdout + 1)
            stderr = stderr_file.read(65537)
        if completed.returncode != 0:
            detail = stderr.decode("utf-8", "replace").strip()[:500]
            raise GenerationError(f"Git command failed ({arguments[0]}): {detail}")
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
            if base == "pontius":
                modules.extend(f"pontius.{alias.name}" for alias in node.names if alias.name != "*")
        for module in modules:
            path = _module_path(module, tracked)
            if path is not None:
                result.add(path)
            elif module.startswith("pontius") and module != "pontius":
                raise GenerationError(f"unresolved local import {module!r} in {current_path}")
    return result


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
    candidates: set[str] = set(_PATH_LITERAL.findall(text.replace("\\", "/")))
    for node in ast.walk(tree):
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            parts = _slash_strings(node)
            if parts:
                normalized = "/".join(part.strip("/\\") for part in parts if part)
                for prefix in ("src/", "tests/", "experiments/", "docs/", "artifacts/", "run_"):
                    position = normalized.find(prefix)
                    if position >= 0:
                        candidates.add(normalized[position:])
        if isinstance(node, ast.Constant) and type(node.value) is str:
            value = node.value.replace("\\", "/")
            if value in tracked:
                candidates.add(value)
    allowed = (
        "src/pontius/",
        "tests/",
        "experiments/configs/",
        "docs/decisions/",
        "artifacts/work_preflight/",
        "run_",
    )
    return {_relative_path(path) for path in candidates if path in tracked and path.startswith(allowed)}


def _dynamic_program_imports(tree: ast.AST, current_path: str, tracked: set[str]) -> set[str]:
    result: set[str] = set()
    for node in ast.walk(tree):
        if (
            not isinstance(node, ast.Constant)
            or type(node.value) is not str
            or "pontius" not in node.value
            or "import" not in node.value
        ):
            continue
        try:
            program = ast.parse(node.value, filename=f"{current_path}::<dynamic-c>")
        except SyntaxError:
            continue
        result.update(_import_paths(program, current_path, tracked))
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
        reached = (
            _import_paths(tree, path, tracked)
            | _literal_paths(tree, text, tracked)
            | _dynamic_program_imports(tree, path, tracked)
        )
        for candidate in sorted(reached):
            if candidate not in discovered:
                discovered.add(candidate)
                if candidate.startswith(("src/pontius/", "tests/", "run_")):
                    pending.append(candidate)
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
                identity = (str(row["commit"]), str(row["relative_path"]))
                if identity in identities:
                    raise GenerationError(f"historical phase derivation collided at {identity}")
                identities.add(identity)
                rows.append(row)
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
            identity = (str(row["commit"]), str(row["relative_path"]))
            if identity in identities:
                raise GenerationError(f"historical source-seal collision at {identity}")
            identities.add(identity)
            rows.append(row)
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
            identity = (str(row["commit"]), str(row["relative_path"]))
            if identity in identities:
                raise GenerationError(f"historical authorization collision at {identity}")
            identities.add(identity)
            rows.append(row)
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
    if type(supplied) is not str or _HEX64.fullmatch(supplied) is None:
        raise GenerationError(
            "--write requires a lowercase 64-hex --approved-seed-sha256"
        )
    if supplied != expected:
        raise GenerationError(
            "the supplied approval digest does not match the freshly derived seed"
        )
    return supplied


def _verified_destinations(repository_root: Path) -> dict[str, Path]:
    if not repository_root.is_absolute():
        raise GenerationError("repository root must be absolute")
    root = repository_root.resolve(strict=True)
    architecture = (root / "docs" / "architecture").resolve(strict=True)
    result: dict[str, Path] = {}
    for relative in MANIFEST_PATHS:
        destination = root / relative
        if destination.parent.resolve(strict=True) != architecture:
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
    return result


def write_manifests(
    repository_root: Path,
    state: Mapping[str, object],
    *,
    approved_seed_sha256: str | None,
) -> None:
    approved = validate_approval_digest(
        approved_seed_sha256, str(state["entries_sha256"])
    )
    destinations = _verified_destinations(repository_root)
    rendered = _render_all(state, approved)
    temporary: dict[str, Path] = {}
    try:
        for relative, destination in destinations.items():
            candidate = (
                destination.parent / f".{destination.name}.{uuid.uuid4().hex}.tmp"
            )
            with candidate.open("xb") as stream:
                stream.write(rendered[relative])
                stream.flush()
                os.fsync(stream.fileno())
            temporary[relative] = candidate
        for relative, destination in destinations.items():
            os.replace(temporary[relative], destination)
            temporary.pop(relative)
    finally:
        for candidate in temporary.values():
            try:
                candidate.unlink()
            except FileNotFoundError:
                pass


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
