"""Strict profile/inventory parsing and pure orchestration selection."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
import ctypes
from dataclasses import dataclass, fields, replace
from hashlib import sha256
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import stat
import tomllib
from typing import Any

if os.name == "nt":
    from ctypes import wintypes
    import msvcrt

from .errors import EvidenceConfigurationError
from .model import (
    CallCapability,
    CapabilityBinding,
    ConfigurationBundle,
    ExitCode,
    FixtureSpec,
    HistoricalCase,
    HistoricalItemExpectation,
    InventoryEntry,
    InterpreterSlot,
    InventoryExpectation,
    LifecycleFixturePlan,
    ObservedCondition,
    OverlaySpec,
    PayloadPlan,
    ProfilePlan,
    ResolvedInventoryItem,
    StableSelector,
    StageBudgets,
    SubprocessCapability,
    TargetKind,
    _normalise_probe_id,
    canonical_semantic_bytes,
    semantic_sha256,
)


PROFILE_SCHEMA = "pontius-test-profiles-v1"
INVENTORY_SCHEMA = "pontius-test-inventory-v1"
MAX_CONFIGURATION_BYTES = 4 * 1024 * 1024
_NANOSECONDS_PER_SECOND = 1_000_000_000


_PROFILE_ROOT_REQUIRED = {
    "schema_version",
    "baseline_commit",
    "sealed_current_files_manifest",
    "sealed_current_absences_manifest",
    "historical_blobs_manifest",
    "retained_v7_manifest",
    "inventory_path",
    "spec_capabilities_sha256",
    "capability_bindings_sha256",
    "interpreter_slot",
    "profile",
    "payload",
    "stabilization_test_files",
}
_PROFILE_ROOT_OPTIONAL = {
    "historical_case",
    "overlay",
    "subprocess_capability",
    "call_capability",
    "capability_binding",
}


def _configuration_error(code: str, message: str, **context: object) -> EvidenceConfigurationError:
    return EvidenceConfigurationError(code, message, context=context)


def _exact_keys(
    value: object,
    *,
    required: set[str],
    optional: set[str] = frozenset(),
    label: str,
) -> Mapping[str, object]:
    if not isinstance(value, Mapping) or any(type(key) is not str for key in value):
        raise ValueError(f"{label} must be a string-keyed table")
    present = set(value)
    missing = required - present
    extra = present - required - optional
    if missing or extra:
        raise ValueError(
            f"{label} fields are invalid (missing={sorted(missing)!r}, extra={sorted(extra)!r})"
        )
    return value


def _exact_string(value: object, name: str) -> str:
    if type(value) is not str or not value:
        raise ValueError(f"{name} must be a non-empty string")
    return value


def _optional_string(value: object, name: str) -> str | None:
    if value is None:
        return None
    return _exact_string(value, name)


def _exact_int(value: object, name: str, *, positive: bool = False) -> int:
    if type(value) is not int or value < (1 if positive else 0):
        qualifier = "positive" if positive else "non-negative"
        raise ValueError(f"{name} must be a {qualifier} integer")
    return value


def _exact_bool(value: object, name: str) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{name} must be a boolean")
    return value


def _exact_list(value: object, name: str) -> list[object]:
    if type(value) is not list:
        raise ValueError(f"{name} must be an array")
    return value


def _string_list(value: object, name: str) -> list[str]:
    return [_exact_string(item, name) for item in _exact_list(value, name)]


def _string_mapping(value: object, name: str) -> Mapping[str, str]:
    table = _exact_keys(value, required=set(value) if isinstance(value, Mapping) else set(), label=name)
    result: dict[str, str] = {}
    for key, nested in table.items():
        result[_exact_string(key, f"{name} key")] = _exact_string(nested, f"{name}.{key}")
    return result


def _require_lower_hex(value: object, name: str, length: int) -> str:
    text = _exact_string(value, name)
    if len(text) != length or any(character not in "0123456789abcdef" for character in text):
        raise ValueError(f"{name} must be {length} lowercase hexadecimal characters")
    return text


def _relative_path(value: object, name: str) -> str:
    text = _exact_string(value, name)
    if PureWindowsPath(text).drive or text.startswith(("/", "\\")) or "\\" in text:
        raise ValueError(f"{name} must be a normalized POSIX relative path")
    path = PurePosixPath(text)
    if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
        raise ValueError(f"{name} must remain below the repository root")
    normalized = path.as_posix()
    if normalized in ("", ".") or normalized != text:
        raise ValueError(f"{name} must be normalized")
    return normalized


def _resolved_child(root: Path, value: object, name: str) -> tuple[str, Path]:
    relative = _relative_path(value, name)
    candidate = Path(os.path.abspath(root / PurePosixPath(relative)))
    try:
        candidate.relative_to(root)
    except ValueError as error:
        raise ValueError(f"{name} escapes repository_root") from error
    return relative, candidate


_IS_WINDOWS = os.name == "nt"
_WINDOWS_REPARSE_ATTRIBUTE = 0x400
_WINDOWS_REPARSE_NAME_SURROGATE = 0x20000000
_WINDOWS_CLOUD_REPARSE_BASE = 0x9000001A
_WINDOWS_CLOUD_REPARSE_MASK = 0xFFFF0FFF


class _WindowsFileAttributeTagInformation(ctypes.Structure):
    """Portable declaration for the Windows metadata adapter and its tests."""

    _fields_ = (
        ("FileAttributes", ctypes.c_uint32),
        ("ReparseTag", ctypes.c_uint32),
    )


def _is_supported_cloud_reparse_tag(tag: int) -> bool:
    return (
        type(tag) is int
        and tag & _WINDOWS_REPARSE_NAME_SURROGATE == 0
        and tag & _WINDOWS_CLOUD_REPARSE_MASK == _WINDOWS_CLOUD_REPARSE_BASE
    )


def _is_disallowed_reparse_values(attributes: int, tag: int) -> bool:
    if not (attributes & _WINDOWS_REPARSE_ATTRIBUTE or tag):
        return False
    return not _is_supported_cloud_reparse_tag(tag)


def _is_reparse(info: os.stat_result) -> bool:
    return _is_disallowed_reparse_values(
        int(getattr(info, "st_file_attributes", 0)),
        int(getattr(info, "st_reparse_tag", 0)),
    )


def _identity_reparse_values(
    info: os.stat_result,
    windows_metadata: tuple[int, int] | None = None,
) -> tuple[int, int]:
    if windows_metadata is not None:
        return windows_metadata
    return (
        int(getattr(info, "st_file_attributes", 0)),
        int(getattr(info, "st_reparse_tag", 0)),
    )


def _stat_identity(
    info: os.stat_result,
    windows_metadata: tuple[int, int] | None = None,
) -> tuple[int, ...]:
    attributes, tag = _identity_reparse_values(info, windows_metadata)
    return (
        int(info.st_dev),
        int(info.st_ino),
        int(info.st_size),
        int(info.st_mtime_ns),
        int(info.st_ctime_ns),
        int(info.st_mode),
        attributes,
        tag,
    )


def _path_handle_identity(
    info: os.stat_result,
    windows_metadata: tuple[int, int] | None = None,
) -> tuple[int, ...]:
    attributes, tag = _identity_reparse_values(info, windows_metadata)
    return (
        int(info.st_dev),
        int(info.st_ino),
        int(info.st_size),
        int(info.st_mtime_ns),
        int(info.st_mode),
        attributes,
        tag,
    )


def _directory_identity(info: os.stat_result) -> tuple[int, ...]:
    return (
        int(info.st_dev),
        int(info.st_ino),
        int(info.st_mode),
        int(getattr(info, "st_file_attributes", 0)),
        int(getattr(info, "st_reparse_tag", 0)),
    )


def _validated_ancestor_chain(
    path: Path,
    root: Path,
    *,
    root_identity: tuple[int, ...] | None = None,
) -> tuple[tuple[Path, tuple[int, ...]], ...]:
    chain: list[tuple[Path, tuple[int, ...]]] = []
    candidate = path.parent
    while True:
        info = os.lstat(candidate)
        if stat.S_ISLNK(info.st_mode) or _is_reparse(info) or not stat.S_ISDIR(info.st_mode):
            raise ValueError("configuration path ancestors must be nonreparse directories")
        identity = _directory_identity(info)
        chain.append((candidate, identity))
        if os.path.normcase(str(candidate)) == os.path.normcase(str(root)):
            if root_identity is not None and identity != root_identity:
                raise ValueError("repository_root changed before configuration read")
            return tuple(chain)
        parent = candidate.parent
        if parent == candidate:
            raise ValueError("configuration path escapes repository_root")
        candidate = parent


def _revalidate_ancestor_chain(
    chain: tuple[tuple[Path, tuple[int, ...]], ...],
) -> None:
    for path, identity in chain:
        info = os.lstat(path)
        if (
            stat.S_ISLNK(info.st_mode)
            or _is_reparse(info)
            or not stat.S_ISDIR(info.st_mode)
            or _directory_identity(info) != identity
        ):
            raise ValueError("configuration path ancestors changed while being read")


@dataclass(frozen=True, slots=True)
class _RepositoryRootCapture:
    path: Path
    identity: tuple[int, ...]


def _capture_repository_root(repository_root: Path) -> _RepositoryRootCapture:
    if not isinstance(repository_root, Path) or not repository_root.is_absolute():
        raise ValueError("repository_root must be an absolute Path")
    lexical = Path(os.path.abspath(repository_root))
    before = os.lstat(lexical)
    if (
        stat.S_ISLNK(before.st_mode)
        or _is_reparse(before)
        or not stat.S_ISDIR(before.st_mode)
    ):
        raise ValueError("repository_root must be a regular directory root")
    identity = _directory_identity(before)
    resolved = lexical.resolve(strict=True)
    if os.path.normcase(str(resolved)) != os.path.normcase(str(lexical)):
        raise ValueError("repository_root must not traverse a link or reparse point")
    after = os.lstat(lexical)
    if (
        stat.S_ISLNK(after.st_mode)
        or _is_reparse(after)
        or not stat.S_ISDIR(after.st_mode)
        or _directory_identity(after) != identity
    ):
        raise ValueError("repository_root changed while being resolved")
    return _RepositoryRootCapture(lexical, identity)


@dataclass(frozen=True, slots=True)
class _ConfigurationFileSnapshot:
    path: Path
    raw: bytes
    leaf_identity: tuple[int, ...]
    ancestor_chain: tuple[tuple[Path, tuple[int, ...]], ...]
    label: str

    def revalidate(self) -> None:
        try:
            info = os.lstat(self.path)
            if (
                stat.S_ISLNK(info.st_mode)
                or _is_reparse(info)
                or not stat.S_ISREG(info.st_mode)
                or _stat_identity(info) != self.leaf_identity
            ):
                raise ValueError(f"{self.label} changed after being read")
            _revalidate_ancestor_chain(self.ancestor_chain)
        except OSError as error:
            raise ValueError(
                f"{self.label} path could not be revalidated securely"
            ) from error


def _windows_path_api() -> tuple[Any, Any, Any]:
    if not _IS_WINDOWS:
        raise ValueError("Windows no-follow file APIs are unavailable")
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
        information = kernel32.GetFileInformationByHandleEx
        information.argtypes = (
            wintypes.HANDLE,
            ctypes.c_int,
            wintypes.LPVOID,
            wintypes.DWORD,
        )
        information.restype = wintypes.BOOL
        close = kernel32.CloseHandle
        close.argtypes = (wintypes.HANDLE,)
        close.restype = wintypes.BOOL
    except Exception as error:
        raise ValueError("Windows no-follow file APIs are unavailable") from error
    return create, information, close


def _windows_bind_handle(handle: int) -> int:
    if not _IS_WINDOWS:
        raise ValueError("Windows file-handle binding is unavailable")
    return msvcrt.open_osfhandle(
        int(handle), os.O_RDONLY | getattr(os, "O_BINARY", 0)
    )


def _windows_regular_handle_metadata(
    descriptor: int, path: Path
) -> tuple[int, int]:
    if not _IS_WINDOWS:
        raise ValueError("Windows regular-file metadata is unavailable")
    try:
        handle = msvcrt.get_osfhandle(descriptor)
        _, information, _ = _windows_path_api()
        value = _WindowsFileAttributeTagInformation()
        succeeded = information(
            wintypes.HANDLE(handle),
            9,
            ctypes.byref(value),
            ctypes.sizeof(value),
        )
    except Exception as error:
        raise ValueError(
            f"configuration file handle metadata cannot be inspected: {path}"
        ) from error
    if not succeeded:
        code = ctypes.get_last_error()
        raise ValueError(
            f"configuration file handle metadata cannot be inspected: {path}"
        ) from OSError(code, os.strerror(code), str(path))
    return int(value.FileAttributes), int(value.ReparseTag)


def _open_regular_no_follow(path: Path) -> int:
    if not _IS_WINDOWS:
        if not hasattr(os, "O_NOFOLLOW"):
            raise ValueError("secure no-follow file opens are unavailable")
        flags = (
            os.O_RDONLY
            | os.O_NOFOLLOW
            | getattr(os, "O_NONBLOCK", 0)
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_BINARY", 0)
        )
        try:
            return os.open(path, flags)
        except OSError as error:
            raise ValueError(
                f"configuration file cannot be opened without links: {path}"
            ) from error

    create, _, close = _windows_path_api()
    try:
        handle = create(
            str(path),
            0x80000000,
            0x00000001 | 0x00000002 | 0x00000004,
            None,
            3,
            0x00200000 | 0x08000000,
            None,
        )
    except Exception as error:
        raise ValueError(
            f"configuration file cannot be opened without reparses: {path}"
        ) from error
    invalid = ctypes.c_void_p(-1).value
    if not handle or int(handle) == invalid:
        code = ctypes.get_last_error()
        raise ValueError(
            f"configuration file cannot be opened without reparses: {path}"
        ) from OSError(code, os.strerror(code), str(path))
    try:
        return _windows_bind_handle(int(handle))
    except (OSError, OverflowError, ValueError) as binding_error:
        try:
            succeeded = close(ctypes.c_void_p(int(handle)))
            if not succeeded:
                code = ctypes.get_last_error()
                operating_error = OSError(code, os.strerror(code), str(path))
                raise ValueError(
                    f"configuration raw handle could not be closed: {path}"
                ) from operating_error
        except Exception as close_error:
            raise ValueError(
                f"configuration file handle binding and cleanup both failed: {path}"
            ) from ExceptionGroup(
                "configuration handle binding and cleanup failures",
                (binding_error, close_error),
            )
        raise ValueError(
            f"configuration file handle cannot be bound: {path}"
        ) from binding_error


def _path_matches_open_handle(
    path_info: os.stat_result,
    handle_info: os.stat_result,
    windows_metadata: tuple[int, int] | None,
) -> bool:
    if _path_handle_identity(path_info)[:5] != _path_handle_identity(handle_info)[:5]:
        return False
    if windows_metadata is None:
        return _path_handle_identity(path_info) == _path_handle_identity(handle_info)
    return _identity_reparse_values(path_info) == windows_metadata


def _metadata_is_reparse(metadata: tuple[int, int] | None) -> bool:
    return metadata is not None and _is_disallowed_reparse_values(
        metadata[0], metadata[1]
    )


def _is_retryable_windows_metadata_transition(
    before: os.stat_result,
    after: os.stat_result,
    before_metadata: tuple[int, int] | None,
    after_metadata: tuple[int, int] | None,
) -> bool:
    return (
        _IS_WINDOWS
        and _stat_identity(before, before_metadata)
        != _stat_identity(after, after_metadata)
        and before_metadata == after_metadata
        and _path_handle_identity(before, before_metadata)
        == _path_handle_identity(after, after_metadata)
    )


def _read_bounded_snapshot(
    path: Path,
    *,
    root: Path | _RepositoryRootCapture,
    label: str,
    _allow_windows_metadata_retry: bool = True,
) -> _ConfigurationFileSnapshot:
    if isinstance(root, _RepositoryRootCapture):
        root_path = root.path
        root_identity = root.identity
    else:
        root_path = root
        root_identity = None
    if not isinstance(path, Path) or not path.is_absolute():
        raise ValueError(f"{label} path must be absolute")
    supplied = Path(os.path.abspath(path))
    try:
        supplied.relative_to(root_path)
    except ValueError as error:
        raise ValueError(f"{label} path must be below repository_root") from error
    try:
        ancestors = _validated_ancestor_chain(
            supplied,
            root_path,
            root_identity=root_identity,
        )
        before_path = os.lstat(supplied)
        if (
            stat.S_ISLNK(before_path.st_mode)
            or _is_reparse(before_path)
            or not stat.S_ISREG(before_path.st_mode)
        ):
            raise ValueError(f"{label} path must be a regular non-link file")
        if before_path.st_size > MAX_CONFIGURATION_BYTES:
            raise ValueError(f"{label} exceeds the configuration size bound")
        descriptor = _open_regular_no_follow(supplied)
        primary_failure: Exception | None = None
        close_failure: Exception | None = None
        try:
            before_windows_metadata = (
                _windows_regular_handle_metadata(descriptor, supplied)
                if _IS_WINDOWS else None
            )
            before_handle = os.fstat(descriptor)
            if (
                stat.S_ISLNK(before_handle.st_mode)
                or _is_reparse(before_handle)
                or _metadata_is_reparse(before_windows_metadata)
                or not stat.S_ISREG(before_handle.st_mode)
                or not _path_matches_open_handle(
                    before_path, before_handle, before_windows_metadata
                )
            ):
                raise ValueError(f"{label} opened handle must be a regular file")
            if before_handle.st_size > MAX_CONFIGURATION_BYTES:
                raise ValueError(f"{label} exceeds the configuration size bound")
            chunks: list[bytes] = []
            remaining = MAX_CONFIGURATION_BYTES + 1
            while remaining:
                chunk = os.read(descriptor, min(1024 * 1024, remaining))
                if not chunk:
                    break
                chunks.append(chunk)
                remaining -= len(chunk)
            raw = b"".join(chunks)
            after_handle = os.fstat(descriptor)
            after_windows_metadata = (
                _windows_regular_handle_metadata(descriptor, supplied)
                if _IS_WINDOWS else None
            )
            if _metadata_is_reparse(after_windows_metadata):
                raise ValueError(f"{label} opened handle must be a regular file")
        except Exception as error:
            primary_failure = error
        try:
            os.close(descriptor)
        except Exception as error:
            close_failure = error
        if primary_failure is not None:
            if close_failure is not None:
                raise ValueError(
                    f"{label} read and handle cleanup both failed"
                ) from ExceptionGroup(
                    "configuration read and close failures",
                    (primary_failure, close_failure),
                )
            raise primary_failure
        if close_failure is not None:
            raise ValueError(f"{label} file handle could not be closed") from close_failure
        after_path = os.lstat(supplied)
        _revalidate_ancestor_chain(ancestors)
    except OSError as error:
        raise ValueError(f"{label} path could not be read securely") from error
    if len(raw) > MAX_CONFIGURATION_BYTES:
        raise ValueError(f"{label} exceeds the configuration size bound")
    retryable_transition = (
        _allow_windows_metadata_retry
        and len(raw) == after_handle.st_size
        and _is_retryable_windows_metadata_transition(
            before_handle,
            after_handle,
            before_windows_metadata,
            after_windows_metadata,
        )
        and _path_handle_identity(before_path)
        == _path_handle_identity(after_path)
    )
    if retryable_transition:
        return _read_bounded_snapshot(
            supplied,
            root=root,
            label=label,
            _allow_windows_metadata_retry=False,
        )
    if (
        not _path_matches_open_handle(
            before_path, before_handle, before_windows_metadata
        )
        or _stat_identity(before_handle, before_windows_metadata)
        != _stat_identity(after_handle, after_windows_metadata)
        or not _path_matches_open_handle(
            after_path, after_handle, after_windows_metadata
        )
        or _stat_identity(before_path) != _stat_identity(after_path)
        or len(raw) != after_handle.st_size
    ):
        raise ValueError(f"{label} changed while being read")
    return _ConfigurationFileSnapshot(
        supplied,
        raw,
        _stat_identity(after_path),
        ancestors,
        label,
    )


def _read_bounded(
    path: Path,
    *,
    root: Path | _RepositoryRootCapture,
    label: str,
    _allow_windows_metadata_retry: bool = True,
) -> bytes:
    return _read_bounded_snapshot(
        path,
        root=root,
        label=label,
        _allow_windows_metadata_retry=_allow_windows_metadata_retry,
    ).raw


def _duplicate_rejecting_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _parse_toml(raw: bytes, path: Path) -> Mapping[str, object]:
    try:
        text = raw.decode("utf-8", errors="strict")
        value = tomllib.loads(text)
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as error:
        raise _configuration_error(
            "profiles_toml_invalid", "profiles configuration is not valid TOML",
            path=path.as_posix(),
        ) from error
    return value


def _parse_json(raw: bytes, path: Path) -> Mapping[str, object]:
    try:
        text = raw.decode("utf-8", errors="strict")
        value = json.loads(text, object_pairs_hook=_duplicate_rejecting_object)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise _configuration_error(
            "inventory_json_invalid", "test inventory is not valid duplicate-free JSON",
            path=path.as_posix(),
        ) from error
    if not isinstance(value, Mapping):
        raise _configuration_error(
            "inventory_json_invalid", "test inventory root must be an object",
            path=path.as_posix(),
        )
    return value


def parse_stable_id(value: str) -> StableSelector:
    try:
        text = _exact_string(value, "stable_id")
        if text.count("::") != 2:
            raise ValueError("stable_id must contain exactly two selector separators")
        relative_text, case_name, method_name = text.split("::")
        if "\\" in relative_text:
            raise ValueError("stable_id paths use POSIX separators")
        relative_path = _relative_path(relative_text, "stable_id path")
        path = PurePosixPath(relative_path)
        if not path.parts or path.parts[0] != "tests" or path.suffix != ".py":
            raise ValueError("stable_id must name a Python file below tests")
        if not case_name.isidentifier():
            raise ValueError("stable_id class must be a Python identifier")
        if not method_name.isidentifier() or not method_name.startswith("test_"):
            raise ValueError("stable_id method must be a test_ Python identifier")
        return StableSelector(text, path, case_name, method_name)
    except ValueError as error:
        raise _configuration_error(
            "stable_id_invalid", "stable test ID is invalid", stable_id=value,
        ) from error


def _parse_inventory_expectation(value: object) -> InventoryExpectation:
    if not isinstance(value, Mapping):
        raise ValueError("inventory expectation must be a table")
    kind = _exact_string(value.get("kind"), "expectation.kind")
    variants = {
        "pass": ({"kind"}, set()),
        "case_defined": ({"kind"}, set()),
        "platform_conditioned": (
            {"kind", "applicable_platforms", "skip_safe_reason_code"}, set()
        ),
        "declared_unconditional_skip": (
            {"kind", "skip_safe_reason_code"}, set()
        ),
    }
    if kind not in variants:
        raise ValueError("inventory expectation kind is unsupported")
    required, optional = variants[kind]
    table = _exact_keys(
        value, required=required, optional=optional, label="inventory expectation"
    )
    return InventoryExpectation(
        kind,
        _string_list(table.get("applicable_platforms", []), "expectation.applicable_platforms"),
        _optional_string(table.get("skip_safe_reason_code"), "expectation.skip_safe_reason_code"),
    )


def _parse_inventory(
    data: Mapping[str, object],
) -> tuple[
    str,
    list[InventoryEntry],
    list[tuple[ResolvedInventoryItem, str, str]],
    object,
]:
    root = _exact_keys(
        data,
        required={
            "schema_version", "baseline_commit", "baseline_discovery",
            "discovery", "entries",
        },
        label="inventory root",
    )
    if root["schema_version"] != INVENTORY_SCHEMA:
        raise ValueError("inventory schema_version is unsupported")
    baseline = _require_lower_hex(root["baseline_commit"], "inventory.baseline_commit", 40)
    baseline_discovery = _exact_keys(
        root["baseline_discovery"],
        required={
            "test_file_count", "stable_id_count", "stable_ids_sha256",
            "historical_id_count", "historical_ids_sha256", "gpu_id_count",
            "gpu_ids_sha256", "core_id_count", "core_ids_sha256",
            "current_id_count", "current_ids_sha256", "explicit_exclusion_count",
        },
        label="inventory.baseline_discovery",
    )
    discovery = _exact_keys(
        root["discovery"],
        required={
            "test_file_count", "stable_id_count", "stable_ids_sha256",
            "introduced_id_count", "introduced_ids_sha256",
        },
        label="inventory.discovery",
    )
    for name, value in baseline_discovery.items():
        if name.endswith("sha256"):
            _require_lower_hex(value, f"baseline_discovery.{name}", 64)
        else:
            _exact_int(value, f"baseline_discovery.{name}")
    for name, value in discovery.items():
        if name.endswith("sha256"):
            _require_lower_hex(value, f"discovery.{name}", 64)
        else:
            _exact_int(value, f"discovery.{name}")
    entries: list[InventoryEntry] = []
    assigned_rows: list[tuple[ResolvedInventoryItem, str, str]] = []
    normalized_entries: list[Mapping[str, object]] = []
    baseline_ids: list[str] = []
    introduced_ids: list[str] = []
    baseline_profiles: dict[str, list[str]] = {
        "historical": [], "gpu": [], "core": [], "current": [],
    }
    baseline_exclusions = 0
    seen: set[str] = set()
    for index, raw_entry in enumerate(_exact_list(root["entries"], "inventory.entries")):
        entry = _exact_keys(
            raw_entry,
            required={"stable_id", "relative_path", "case_name", "method_name"},
            optional={
                "assignment", "exclusion", "baseline_assignment",
                "introduced_after_baseline",
            },
            label=f"inventory.entries[{index}]",
        )
        if ("assignment" in entry) == ("exclusion" in entry):
            raise ValueError("inventory entry requires assignment XOR exclusion")
        selector = parse_stable_id(_exact_string(entry["stable_id"], "stable_id"))
        if selector.stable_id in seen:
            raise ValueError("inventory stable IDs must be unique")
        seen.add(selector.stable_id)
        if _relative_path(entry["relative_path"], "inventory relative_path") != selector.relative_path.as_posix():
            raise ValueError("inventory relative_path disagrees with stable_id")
        if entry["case_name"] != selector.case_name or entry["method_name"] != selector.method_name:
            raise ValueError("inventory selector fields disagree with stable_id")
        if "assignment" in entry:
            assignment = _exact_keys(
                entry["assignment"],
                required={"profile_name", "payload_id", "expectation"},
                label=f"inventory.entries[{index}].assignment",
            )
            profile_name = _exact_string(assignment["profile_name"], "assignment.profile_name")
            payload_id = _exact_string(assignment["payload_id"], "assignment.payload_id")
            expectation = _parse_inventory_expectation(assignment["expectation"])
            item = ResolvedInventoryItem(selector, expectation)
            entries.append(InventoryEntry(
                selector, profile_name, payload_id, expectation, None, None, None
            ))
            assigned_rows.append((item, profile_name, payload_id))
            normalized_assignment: Mapping[str, object] = {
                "profile_name": profile_name,
                "payload_id": payload_id,
                "expectation": {
                    "kind": expectation.kind,
                    **(
                        {"applicable_platforms": expectation.applicable_platforms,
                         "skip_safe_reason_code": expectation.skip_safe_reason_code}
                        if expectation.kind == "platform_conditioned" else
                        {"skip_safe_reason_code": expectation.skip_safe_reason_code}
                        if expectation.kind == "declared_unconditional_skip" else {}
                    ),
                },
            }
        else:
            exclusion = _exact_keys(
                entry["exclusion"],
                required={"reason", "owner", "milestone"},
                label=f"inventory.entries[{index}].exclusion",
            )
            entries.append(InventoryEntry(
                selector, None, None, None,
                _exact_string(exclusion["reason"], "exclusion.reason"),
                _exact_string(exclusion["owner"], "exclusion.owner"),
                _exact_string(exclusion["milestone"], "exclusion.milestone"),
            ))
            normalized_assignment = {
                "reason": entries[-1].exclusion_reason,
                "owner": entries[-1].exclusion_owner,
                "milestone": entries[-1].exclusion_milestone,
            }
        has_baseline = "baseline_assignment" in entry
        has_introduced = "introduced_after_baseline" in entry
        if has_baseline == has_introduced:
            raise ValueError(
                "inventory entries require baseline_assignment XOR introduced_after_baseline"
            )
        if has_baseline:
            if "assignment" not in entry:
                raise ValueError("baseline exclusions are unsupported by the zero-exclusion lock")
            baseline_assignment = _exact_keys(
                entry["baseline_assignment"],
                required={"profile_name", "payload_id", "expectation"},
                label=f"inventory.entries[{index}].baseline_assignment",
            )
            baseline_profile = _exact_string(
                baseline_assignment["profile_name"], "baseline_assignment.profile_name"
            )
            baseline_payload = _exact_string(
                baseline_assignment["payload_id"], "baseline_assignment.payload_id"
            )
            baseline_expectation = _parse_inventory_expectation(
                baseline_assignment["expectation"]
            )
            if (
                baseline_profile != profile_name
                or baseline_payload != payload_id
                or baseline_expectation != expectation
            ):
                raise ValueError("baseline_assignment must equal the materialized assignment")
            if baseline_profile not in baseline_profiles:
                raise ValueError("baseline assignment profile is unsupported")
            baseline_profiles[baseline_profile].append(selector.stable_id)
            baseline_ids.append(selector.stable_id)
            metadata = {"baseline_assignment": normalized_assignment}
        else:
            if _exact_bool(
                entry["introduced_after_baseline"], "introduced_after_baseline"
            ) is not True:
                raise ValueError("introduced_after_baseline must be true")
            introduced_ids.append(selector.stable_id)
            metadata = {"introduced_after_baseline": True}
        normalized_entry: dict[str, object] = {
            "stable_id": selector.stable_id,
            "relative_path": selector.relative_path.as_posix(),
            "case_name": selector.case_name,
            "method_name": selector.method_name,
            ("assignment" if "assignment" in entry else "exclusion"):
                normalized_assignment,
            **metadata,
        }
        normalized_entries.append(normalized_entry)
    entries.sort(key=lambda item: item.selector.stable_id)
    assigned_rows.sort(key=lambda row: row[0].selector.stable_id)
    normalized_entries.sort(key=lambda item: str(item["stable_id"]))

    def stable_digest(values: Iterable[str]) -> str:
        ordered = tuple(sorted(values))
        return sha256(
            ("\n".join(ordered) + ("\n" if ordered else "")).encode("utf-8")
        ).hexdigest()

    baseline_id_set = set(baseline_ids)
    actual_baseline = {
        "test_file_count": len({
            item.selector.relative_path.as_posix()
            for item in entries
            if item.selector.stable_id in baseline_id_set
        }),
        "stable_id_count": len(baseline_ids),
        "stable_ids_sha256": stable_digest(baseline_ids),
        "historical_id_count": len(baseline_profiles["historical"]),
        "historical_ids_sha256": stable_digest(baseline_profiles["historical"]),
        "gpu_id_count": len(baseline_profiles["gpu"]),
        "gpu_ids_sha256": stable_digest(baseline_profiles["gpu"]),
        "core_id_count": len(baseline_profiles["core"]),
        "core_ids_sha256": stable_digest(baseline_profiles["core"]),
        "current_id_count": len(baseline_profiles["current"]),
        "current_ids_sha256": stable_digest(baseline_profiles["current"]),
        "explicit_exclusion_count": baseline_exclusions,
    }
    actual_discovery = {
        "test_file_count": len({item.selector.relative_path.as_posix() for item in entries}),
        "stable_id_count": len(entries),
        "stable_ids_sha256": stable_digest(item.selector.stable_id for item in entries),
        "introduced_id_count": len(introduced_ids),
        "introduced_ids_sha256": stable_digest(introduced_ids),
    }
    if dict(baseline_discovery) != actual_baseline:
        raise ValueError("baseline_discovery does not match materialized baseline entries")
    if dict(discovery) != actual_discovery:
        raise ValueError("discovery does not match working inventory entries")
    normalized = {
        "schema_version": INVENTORY_SCHEMA,
        "baseline_commit": baseline,
        "baseline_discovery": actual_baseline,
        "discovery": actual_discovery,
        "entries": tuple(normalized_entries),
    }
    return baseline, entries, assigned_rows, normalized


def _parse_slot(value: object, index: int) -> InterpreterSlot:
    table = _exact_keys(
        value,
        required={"name", "resolution", "implementation", "required_for_full"},
        optional={
            "windows_relative_path", "posix_relative_path", "environment_variable",
            "minimum_version", "exact_version",
        },
        label=f"interpreter_slot[{index}]",
    )
    resolution = _exact_string(table["resolution"], "interpreter_slot.resolution")
    minimum = table.get("minimum_version")
    exact = table.get("exact_version")
    if minimum is not None:
        minimum = [_exact_int(item, "minimum_version") for item in _exact_list(minimum, "minimum_version")]
    if exact is not None:
        exact = [_exact_int(item, "exact_version") for item in _exact_list(exact, "exact_version")]
    return InterpreterSlot(
        _exact_string(table["name"], "interpreter_slot.name"),
        resolution,
        _optional_string(table.get("windows_relative_path"), "windows_relative_path"),
        _optional_string(table.get("posix_relative_path"), "posix_relative_path"),
        _optional_string(table.get("environment_variable"), "environment_variable"),
        _exact_string(table["implementation"], "implementation"),
        minimum,
        exact,
        _exact_bool(table["required_for_full"], "required_for_full"),
    )


def _parse_fixture(value: object, label: str) -> FixtureSpec:
    table = _exact_keys(
        value, required={"relative_path", "path_kind", "byte_length", "raw_sha256"}, label=label,
    )
    return FixtureSpec(
        _relative_path(table["relative_path"], f"{label}.relative_path"),
        _exact_string(table["path_kind"], f"{label}.path_kind"),
        _exact_int(table["byte_length"], f"{label}.byte_length"),
        _require_lower_hex(table["raw_sha256"], f"{label}.raw_sha256", 64),
    )


def _parse_lifecycle_fixture(value: object, label: str) -> LifecycleFixturePlan:
    table = _exact_keys(
        value,
        required={
            "fixture_id", "kind", "relative_path", "member_ids", "allowed_write_roots",
            "forbidden_relative_paths", "serialized",
        },
        optional={"class_name"},
        label=label,
    )
    return LifecycleFixturePlan(
        _exact_string(table["fixture_id"], f"{label}.fixture_id"),
        _exact_string(table["kind"], f"{label}.kind"),
        _relative_path(table["relative_path"], f"{label}.relative_path"),
        _optional_string(table.get("class_name"), f"{label}.class_name"),
        _string_list(table["member_ids"], f"{label}.member_ids"),
        _string_list(table["allowed_write_roots"], f"{label}.allowed_write_roots"),
        [_relative_path(item, f"{label}.forbidden_relative_paths") for item in _exact_list(table["forbidden_relative_paths"], f"{label}.forbidden_relative_paths")],
        _exact_bool(table["serialized"], f"{label}.serialized"),
    )


def _parse_payload(
    value: object,
    index: int,
    inventory_rows: list[tuple[ResolvedInventoryItem, str, str]],
) -> PayloadPlan:
    label = f"payload[{index}]"
    table = _exact_keys(
        value,
        required={
            "payload_id", "profile_name", "target_kind", "allowed_interpreter_slots",
            "probe_ids", "environment_additions", "environment_removals", "allowed_write_roots",
            "forbidden_relative_paths", "serialized",
        },
        optional={"ignored_fixture", "lifecycle_fixture"},
        label=label,
    )
    payload_id = _exact_string(table["payload_id"], f"{label}.payload_id")
    inventory_items = [item for item, _, assigned_payload in inventory_rows if assigned_payload == payload_id]
    fixtures = [
        _parse_fixture(item, f"{label}.ignored_fixture[{fixture_index}]")
        for fixture_index, item in enumerate(_exact_list(table.get("ignored_fixture", []), f"{label}.ignored_fixture"))
    ]
    lifecycle = [
        _parse_lifecycle_fixture(item, f"{label}.lifecycle_fixture[{fixture_index}]")
        for fixture_index, item in enumerate(_exact_list(table.get("lifecycle_fixture", []), f"{label}.lifecycle_fixture"))
    ]
    return PayloadPlan(
        payload_id,
        _exact_string(table["profile_name"], f"{label}.profile_name"),
        _exact_string(table["target_kind"], f"{label}.target_kind"),
        _string_list(table["allowed_interpreter_slots"], f"{label}.allowed_interpreter_slots"),
        inventory_items,
        [
            _normalise_probe_id(item, f"{label}.probe_ids")
            for item in _exact_list(table["probe_ids"], f"{label}.probe_ids")
        ],
        lifecycle,
        _string_mapping(table["environment_additions"], f"{label}.environment_additions"),
        _string_list(table["environment_removals"], f"{label}.environment_removals"),
        _string_list(table["allowed_write_roots"], f"{label}.allowed_write_roots"),
        [_relative_path(item, f"{label}.forbidden_relative_paths") for item in _exact_list(table["forbidden_relative_paths"], f"{label}.forbidden_relative_paths")],
        fixtures,
        _exact_bool(table["serialized"], f"{label}.serialized"),
    )


def _parse_budgets(value: object, label: str) -> StageBudgets:
    table = _exact_keys(
        value,
        required={"setup_seconds", "child_seconds", "termination_seconds", "cleanup_seconds", "total_seconds"},
        label=label,
    )
    seconds = {
        name: _exact_int(table[name], f"{label}.{name}", positive=True)
        for name in table
    }
    return StageBudgets(
        seconds["setup_seconds"] * _NANOSECONDS_PER_SECOND,
        seconds["child_seconds"] * _NANOSECONDS_PER_SECOND,
        seconds["termination_seconds"] * _NANOSECONDS_PER_SECOND,
        seconds["cleanup_seconds"] * _NANOSECONDS_PER_SECOND,
        seconds["total_seconds"] * _NANOSECONDS_PER_SECOND,
    )


def _fixture_union(
    owners: Iterable[PayloadPlan | ProfilePlan],
) -> tuple[FixtureSpec, ...]:
    by_path: dict[str, FixtureSpec] = {}
    for owner in owners:
        for fixture in owner.fixture_specs:
            previous = by_path.get(fixture.relative_path)
            if previous is not None and previous != fixture:
                raise ValueError("profile payloads declare conflicting fixture identities")
            by_path[fixture.relative_path] = fixture
    return tuple(by_path[path] for path in sorted(by_path))


def _parse_profile(
    value: object,
    index: int,
    *,
    payloads: Mapping[str, PayloadPlan],
    slots: Mapping[str, InterpreterSlot],
) -> ProfilePlan:
    label = f"profile[{index}]"
    table = _exact_keys(
        value,
        required={
            "name", "interpreter_slots", "payload_ids",
            "historical_case_ids", "subprofiles", "gpu_optional", "budgets",
        },
        optional={"default_interpreter_slot"},
        label=label,
    )
    name = _exact_string(table["name"], f"{label}.name")
    interpreter_slots = _string_list(table["interpreter_slots"], f"{label}.interpreter_slots")
    payload_ids = _string_list(table["payload_ids"], f"{label}.payload_ids")
    unknown_slots = set(interpreter_slots) - set(slots)
    unknown_payloads = set(payload_ids) - set(payloads)
    if unknown_slots:
        raise ValueError(f"{label} references unknown interpreter slots")
    if unknown_payloads:
        raise ValueError(f"{label} references unknown payloads")
    for payload_id in payload_ids:
        payload = payloads[payload_id]
        if payload.profile_name != name:
            raise ValueError("payload profile_name disagrees with owning profile")
    default_slot = _optional_string(table.get("default_interpreter_slot"), f"{label}.default_interpreter_slot")
    if default_slot is not None:
        for payload_id in payload_ids:
            if default_slot not in payloads[payload_id].allowed_interpreter_slots:
                raise ValueError("default interpreter slot is not allowed by every selected payload")
    profile = ProfilePlan(
        name,
        interpreter_slots,
        default_slot,
        payload_ids,
        _string_list(table["historical_case_ids"], f"{label}.historical_case_ids"),
        _string_list(table["subprofiles"], f"{label}.subprofiles"),
        _parse_budgets(table["budgets"], f"{label}.budgets"),
        _fixture_union(payloads[payload_id] for payload_id in payload_ids),
        _exact_bool(table["gpu_optional"], f"{label}.gpu_optional"),
        "0" * 64,
    )
    definition = {
        field: getattr(profile, field)
        for field in (
            "name", "interpreter_slots", "default_interpreter_slot", "payload_ids",
            "historical_case_ids", "subprofiles", "budgets", "fixture_specs", "gpu_optional",
        )
    }
    return replace(profile, definition_sha256=semantic_sha256(definition))


def _profile_definition(profile: ProfilePlan) -> Mapping[str, object]:
    return {
        field: getattr(profile, field)
        for field in (
            "name", "interpreter_slots", "default_interpreter_slot", "payload_ids",
            "historical_case_ids", "subprofiles", "budgets", "fixture_specs",
            "gpu_optional",
        )
    }


def _resolve_profiles(
    profiles: Mapping[str, ProfilePlan],
) -> dict[str, ProfilePlan]:
    resolved: dict[str, ProfilePlan] = {}
    visiting: set[str] = set()

    def resolve(name: str) -> ProfilePlan:
        previous = resolved.get(name)
        if previous is not None:
            return previous
        profile = profiles.get(name)
        if profile is None:
            raise ValueError("profile references an unknown subprofile")
        if name in visiting:
            raise ValueError("profile graph contains a cycle")
        visiting.add(name)
        if profile.subprofiles:
            fixtures = _fixture_union(resolve(child) for child in profile.subprofiles)
        else:
            fixtures = profile.fixture_specs
        visiting.remove(name)
        finalized = replace(
            profile, fixture_specs=fixtures, definition_sha256="0" * 64
        )
        finalized = replace(
            finalized,
            definition_sha256=semantic_sha256(_profile_definition(finalized)),
        )
        resolved[name] = finalized
        return finalized

    for profile_name in sorted(profiles):
        resolve(profile_name)
    return resolved


def _parse_item_expectation(value: object, label: str) -> HistoricalItemExpectation:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be a table")
    outcome = _exact_string(value.get("outcome"), f"{label}.outcome")
    if outcome == "pass":
        required = {"item_id", "outcome"}
    elif outcome == "expected_negative":
        required = {
            "item_id", "outcome", "phase", "exception_type", "safe_reason_code",
            "body_entered", "capability_counters",
        }
    else:
        raise ValueError(f"{label}.outcome is unsupported")
    table = _exact_keys(value, required=required, label=label)
    body_entered = table.get("body_entered")
    if body_entered is not None:
        body_entered = _exact_bool(body_entered, f"{label}.body_entered")
    counters = table.get("capability_counters", {})
    if not isinstance(counters, Mapping):
        raise ValueError(f"{label}.capability_counters must be a mapping")
    for key, count in counters.items():
        _exact_string(key, f"{label}.capability_counters key")
        _exact_int(count, f"{label}.capability_counters.{key}")
    return HistoricalItemExpectation(
        _exact_string(table["item_id"], f"{label}.item_id"),
        outcome,
        _optional_string(table.get("phase"), f"{label}.phase"),
        _optional_string(table.get("exception_type"), f"{label}.exception_type"),
        _optional_string(table.get("safe_reason_code"), f"{label}.safe_reason_code"),
        body_entered,
        counters,
    )


def _parse_historical_case(value: object, index: int) -> HistoricalCase:
    label = f"historical_case[{index}]"
    table = _exact_keys(
        value,
        required={
            "case_id", "phase", "commit", "root_tree_oid", "payload_ids", "overlay_ids",
            "expected_vector", "item_expectation",
        },
        label=label,
    )
    vector = table["expected_vector"]
    if not isinstance(vector, Mapping):
        raise ValueError(f"{label}.expected_vector must be a table")
    return HistoricalCase(
        _exact_string(table["case_id"], f"{label}.case_id"),
        _exact_string(table["phase"], f"{label}.phase"),
        _require_lower_hex(table["commit"], f"{label}.commit", 40),
        _require_lower_hex(table["root_tree_oid"], f"{label}.root_tree_oid", 40),
        _string_list(table["payload_ids"], f"{label}.payload_ids"),
        vector,
        [_parse_item_expectation(item, f"{label}.item_expectation[{item_index}]") for item_index, item in enumerate(_exact_list(table["item_expectation"], f"{label}.item_expectation"))],
        _string_list(table["overlay_ids"], f"{label}.overlay_ids"),
    )


def _parse_overlay(value: object, index: int) -> OverlaySpec:
    label = f"overlay[{index}]"
    table = _exact_keys(
        value,
        required={"overlay_id", "source_commit", "source_path", "destination_path", "byte_length", "raw_sha256"},
        label=label,
    )
    return OverlaySpec(
        _exact_string(table["overlay_id"], f"{label}.overlay_id"),
        _require_lower_hex(table["source_commit"], f"{label}.source_commit", 40),
        _relative_path(table["source_path"], f"{label}.source_path"),
        _relative_path(table["destination_path"], f"{label}.destination_path"),
        _exact_int(table["byte_length"], f"{label}.byte_length"),
        _require_lower_hex(table["raw_sha256"], f"{label}.raw_sha256", 64),
    )


def _parse_subprocess_capability(value: object, index: int) -> SubprocessCapability:
    label = f"subprocess_capability[{index}]"
    table = _exact_keys(
        value,
        required={
            "capability_id", "executable_role", "executable_slot", "executable_constraints",
            "argv", "argv_template", "cwd_class",
            "environment_additions", "environment_removals", "timeout_ns",
            "expected_return_category", "read_roots", "write_roots",
            "fixed_descendant_permission",
        },
        optional={"dynamic_program_sha256"},
        label=label,
    )
    constraints = table["executable_constraints"]
    if not isinstance(constraints, Mapping):
        raise ValueError(f"{label}.executable_constraints must be a mapping")
    return SubprocessCapability(
        _exact_string(table["capability_id"], f"{label}.capability_id"),
        _exact_string(table["executable_role"], f"{label}.executable_role"),
        _exact_string(table["executable_slot"], f"{label}.executable_slot"),
        constraints,
        _string_list(table["argv"], f"{label}.argv"),
        _string_list(table["argv_template"], f"{label}.argv_template"),
        _optional_string(table.get("dynamic_program_sha256"), f"{label}.dynamic_program_sha256"),
        _exact_string(table["cwd_class"], f"{label}.cwd_class"),
        _string_mapping(table["environment_additions"], f"{label}.environment_additions"),
        _string_list(table["environment_removals"], f"{label}.environment_removals"),
        _exact_int(table["timeout_ns"], f"{label}.timeout_ns", positive=True),
        _exact_string(table["expected_return_category"], f"{label}.expected_return_category"),
        _string_list(table["read_roots"], f"{label}.read_roots"),
        _string_list(table["write_roots"], f"{label}.write_roots"),
        _exact_bool(table["fixed_descendant_permission"], f"{label}.fixed_descendant_permission"),
    )


def _parse_call_capability(value: object, index: int) -> CallCapability:
    label = f"call_capability[{index}]"
    table = _exact_keys(
        value,
        required={"capability_id", "kind", "module_name", "qualified_name", "action", "maximum_calls", "return_contract"},
        label=label,
    )
    return CallCapability(
        _exact_string(table["capability_id"], f"{label}.capability_id"),
        _exact_string(table["kind"], f"{label}.kind"),
        _exact_string(table["module_name"], f"{label}.module_name"),
        _exact_string(table["qualified_name"], f"{label}.qualified_name"),
        _exact_string(table["action"], f"{label}.action"),
        _exact_int(table["maximum_calls"], f"{label}.maximum_calls", positive=True),
        _exact_string(table["return_contract"], f"{label}.return_contract"),
    )


def _parse_capability_binding(value: object, index: int) -> CapabilityBinding:
    label = f"capability_binding[{index}]"
    table = _exact_keys(
        value,
        required={"item_id", "approval_scope", "capability_kind", "capability_id"},
        label=label,
    )
    return CapabilityBinding(
        _exact_string(table["item_id"], f"{label}.item_id"),
        _exact_string(table["approval_scope"], f"{label}.approval_scope"),
        _exact_string(table["capability_kind"], f"{label}.capability_kind"),
        _exact_string(table["capability_id"], f"{label}.capability_id"),
    )


def _unique_mapping(values: Iterable[Any], key_name: str, label: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for value in values:
        key = getattr(value, key_name)
        if key in result:
            raise ValueError(f"{label} identifiers must be unique")
        result[key] = value
    return result


_ZERO_SHA256 = "0" * 64
_SCOPE_DIGEST_FIELD = {
    "design": "spec_capabilities_sha256",
    "historical_review": "capability_bindings_sha256",
}


def _expanded_capability_rows(
    *,
    subprocess_capabilities: Mapping[str, SubprocessCapability],
    call_capabilities: Mapping[str, CallCapability],
    bindings: Iterable[CapabilityBinding],
) -> Mapping[str, tuple[Mapping[str, object], ...]]:
    rows: dict[str, list[Mapping[str, object]]] = {
        "design": [],
        "historical_review": [],
    }
    for binding in bindings:
        definitions: Mapping[str, SubprocessCapability | CallCapability]
        if binding.capability_kind == "subprocess":
            definitions = subprocess_capabilities
        else:
            definitions = call_capabilities
        capability = definitions.get(binding.capability_id)
        if capability is None:
            raise ValueError("capability binding references an unknown capability")
        row: dict[str, object] = {
            "item_id": binding.item_id,
            "approval_scope": binding.approval_scope,
            "capability_kind": binding.capability_kind,
        }
        row.update(
            (field.name, getattr(capability, field.name))
            for field in fields(capability)
        )
        rows[binding.approval_scope].append(row)
    return {
        scope: tuple(sorted(
            scope_rows,
            key=lambda row: (
                str(row["item_id"]),
                str(row["capability_kind"]),
                str(row["capability_id"]),
            ),
        ))
        for scope, scope_rows in rows.items()
    }


def _payload_item_scopes(
    payloads: Mapping[str, PayloadPlan],
) -> tuple[dict[str, str], dict[str, str]]:
    scopes: dict[str, str] = {}
    owners: dict[str, str] = {}
    for payload in payloads.values():
        scope = (
            "design"
            if payload.target_kind is TargetKind.CURRENT_SNAPSHOT
            else "historical_review"
        )
        item_ids = (
            tuple(item.selector.stable_id for item in payload.inventory_items)
            + payload.probe_ids
            + tuple(
                fixture.fixture_id for fixture in payload.lifecycle_fixtures
            )
        )
        for item_id in item_ids:
            if item_id in owners:
                raise ValueError("orchestration items require one payload owner")
            owners[item_id] = payload.payload_id
            scopes[item_id] = scope
    return scopes, owners


def _validate_capability_contract(
    *,
    payloads: Mapping[str, PayloadPlan],
    subprocess_capabilities: Mapping[str, SubprocessCapability],
    call_capabilities: Mapping[str, CallCapability],
    bindings: tuple[CapabilityBinding, ...],
    spec_digest: str,
    historical_digest: str,
) -> None:
    duplicate_ids = set(subprocess_capabilities) & set(call_capabilities)
    if duplicate_ids:
        raise ValueError("capability identifiers cannot mix definition kinds")
    item_scopes, _ = _payload_item_scopes(payloads)
    seen_bindings: set[tuple[str, str, str, str]] = set()
    definition_scopes: dict[tuple[str, str], str] = {}
    referenced_definitions: set[tuple[str, str]] = set()
    for binding in bindings:
        identity = (
            binding.approval_scope, binding.item_id, binding.capability_kind,
            binding.capability_id,
        )
        if identity in seen_bindings:
            raise ValueError("capability bindings must be unique")
        seen_bindings.add(identity)
        expected_scope = item_scopes.get(binding.item_id)
        if expected_scope is None:
            raise ValueError("capability binding references an unknown item")
        if binding.approval_scope != expected_scope:
            raise ValueError("capability binding scope disagrees with item ownership")
        definition_identity = (binding.capability_kind, binding.capability_id)
        previous_scope = definition_scopes.get(definition_identity)
        if previous_scope is not None and previous_scope != binding.approval_scope:
            raise ValueError("capability definition cannot be shared across scopes")
        definition_scopes[definition_identity] = binding.approval_scope
        referenced_definitions.add(definition_identity)
    defined = {
        ("subprocess", capability_id)
        for capability_id in subprocess_capabilities
    }
    defined.update(
        ("call", capability_id) for capability_id in call_capabilities
    )
    if defined != referenced_definitions:
        raise ValueError("capability definitions must be referenced exactly by bindings")
    rows = _expanded_capability_rows(
        subprocess_capabilities=subprocess_capabilities,
        call_capabilities=call_capabilities,
        bindings=bindings,
    )
    claimed = {
        "design": spec_digest,
        "historical_review": historical_digest,
    }
    for scope, scope_rows in rows.items():
        digest = claimed[scope]
        if not scope_rows:
            if digest != _ZERO_SHA256:
                raise ValueError("empty capability scope must use the zero digest")
            continue
        if digest == _ZERO_SHA256 or digest != semantic_sha256(scope_rows):
            raise ValueError("capability scope digest does not match expanded rows")
        if len({canonical_semantic_bytes(row) for row in scope_rows}) != len(scope_rows):
            raise ValueError("capability rows contain duplicate expanded semantics")


def _validate_references(
    *,
    slots: Mapping[str, InterpreterSlot],
    profiles: Mapping[str, ProfilePlan],
    payloads: Mapping[str, PayloadPlan],
    cases: Mapping[str, HistoricalCase],
    overlays: Mapping[str, OverlaySpec],
    subprocess_capabilities: Mapping[str, SubprocessCapability],
    call_capabilities: Mapping[str, CallCapability],
    bindings: tuple[CapabilityBinding, ...],
    inventory_rows: list[tuple[ResolvedInventoryItem, str, str]],
    spec_digest: str,
    historical_digest: str,
) -> None:
    for item, profile_name, payload_id in inventory_rows:
        if profile_name not in profiles or payload_id not in payloads:
            raise ValueError(f"inventory item {item.selector.stable_id} has an unknown assignment")
        if payloads[payload_id].profile_name != profile_name:
            raise ValueError("inventory assignment profile and payload disagree")
    for profile in profiles.values():
        if set(profile.historical_case_ids) - set(cases):
            raise ValueError("profile references an unknown historical case")
        if set(profile.subprofiles) - set(profiles):
            raise ValueError("profile references an unknown subprofile")
        for case_id in profile.historical_case_ids:
            if not set(cases[case_id].payload_ids).issubset(profile.payload_ids):
                raise ValueError(
                    "historical case payloads must belong to the owning profile"
                )
    for payload in payloads.values():
        if set(payload.allowed_interpreter_slots) - set(slots):
            raise ValueError("payload references an unknown interpreter slot")
        owner = profiles.get(payload.profile_name)
        if owner is None or payload.payload_id not in owner.payload_ids:
            raise ValueError("payload must belong to exactly its named profile")
    inventory_owners: dict[str, str] = {}
    module_members: dict[str, set[str]] = {}
    class_members: dict[tuple[str, str], set[str]] = {}
    for item, _, payload_id in inventory_rows:
        selector = item.selector
        stable_id = selector.stable_id
        relative_path = selector.relative_path.as_posix()
        inventory_owners[stable_id] = payload_id
        module_members.setdefault(relative_path, set()).add(stable_id)
        class_members.setdefault(
            (relative_path, selector.case_name), set()
        ).add(stable_id)
    for payload in payloads.values():
        for fixture in payload.lifecycle_fixtures:
            if fixture.class_name is None:
                expected_members = module_members.get(fixture.relative_path, set())
            else:
                expected_members = class_members.get(
                    (fixture.relative_path, fixture.class_name), set()
                )
            if set(fixture.member_ids) != expected_members or any(
                inventory_owners[stable_id] != payload.payload_id
                for stable_id in expected_members
            ):
                raise ValueError(
                    "lifecycle fixture members cannot span payload ownership"
                )
    _payload_item_scopes(payloads)
    for case in cases.values():
        if set(case.payload_ids) - set(payloads) or set(case.overlay_ids) - set(overlays):
            raise ValueError("historical case contains an unknown payload or overlay")
        owned_items: dict[str, str] = {}
        for payload_id in case.payload_ids:
            payload = payloads[payload_id]
            if payload.target_kind is not TargetKind.HISTORICAL_CLONE:
                raise ValueError("historical cases require historical-clone payloads")
            payload_items = {
                item.selector.stable_id: item for item in payload.inventory_items
            }
            runtime_ids = tuple(payload_items) + payload.probe_ids
            if not runtime_ids:
                raise ValueError("historical case payload must own a runtime item")
            for item_id in runtime_ids:
                if item_id in owned_items:
                    raise ValueError(
                        "historical case runtime items require one payload owner"
                    )
                owned_items[item_id] = payload_id
            if any(
                item.expectation.kind != "case_defined"
                for item in payload.inventory_items
            ):
                raise ValueError(
                    "historical inventory items require case_defined expectations"
                )
        if {item.item_id for item in case.item_expectations} != set(owned_items):
            raise ValueError(
                "historical case expectations must exactly match payload runtime items"
            )
    _validate_capability_contract(
        payloads=payloads,
        subprocess_capabilities=subprocess_capabilities,
        call_capabilities=call_capabilities,
        bindings=bindings,
        spec_digest=spec_digest,
        historical_digest=historical_digest,
    )


def load_configuration(
    profiles_path: Path,
    inventory_path: Path,
    *,
    repository_root: Path,
) -> ConfigurationBundle:
    try:
        root_capture = _capture_repository_root(repository_root)
        root = root_capture.path
        profile_snapshot = _read_bounded_snapshot(
            profiles_path, root=root_capture, label="profiles"
        )
        inventory_snapshot = _read_bounded_snapshot(
            inventory_path, root=root_capture, label="inventory"
        )
        profile_data = _parse_toml(profile_snapshot.raw, profile_snapshot.path)
        inventory_data = _parse_json(
            inventory_snapshot.raw, inventory_snapshot.path
        )
        profile_root = _exact_keys(
            profile_data,
            required=_PROFILE_ROOT_REQUIRED,
            optional=_PROFILE_ROOT_OPTIONAL,
            label="profiles root",
        )
        if profile_root["schema_version"] != PROFILE_SCHEMA:
            raise ValueError("profiles schema_version is unsupported")
        baseline = _require_lower_hex(profile_root["baseline_commit"], "baseline_commit", 40)
        inventory_baseline, inventory_entries, inventory_rows, normalized_inventory = _parse_inventory(inventory_data)
        if inventory_baseline != baseline:
            raise ValueError("profile and inventory baselines disagree")

        configured_inventory_path, expected_inventory_path = _resolved_child(
            root, profile_root["inventory_path"], "inventory_path"
        )
        if expected_inventory_path != inventory_snapshot.path:
            raise ValueError("inventory_path does not identify the supplied inventory")
        manifest_paths = {}
        for name in (
            "sealed_current_files_manifest", "sealed_current_absences_manifest",
            "historical_blobs_manifest", "retained_v7_manifest",
        ):
            manifest_paths[name], _ = _resolved_child(root, profile_root[name], name)

        slots = _unique_mapping(
            (_parse_slot(item, index) for index, item in enumerate(_exact_list(profile_root["interpreter_slot"], "interpreter_slot"))),
            "name", "interpreter slots",
        )
        payloads = _unique_mapping(
            (_parse_payload(item, index, inventory_rows) for index, item in enumerate(_exact_list(profile_root["payload"], "payload"))),
            "payload_id", "payloads",
        )
        profiles = _unique_mapping(
            (_parse_profile(item, index, payloads=payloads, slots=slots) for index, item in enumerate(_exact_list(profile_root["profile"], "profile"))),
            "name", "profiles",
        )
        profiles = _resolve_profiles(profiles)
        cases = _unique_mapping(
            (_parse_historical_case(item, index) for index, item in enumerate(_exact_list(profile_root.get("historical_case", []), "historical_case"))),
            "case_id", "historical cases",
        )
        overlays = _unique_mapping(
            (_parse_overlay(item, index) for index, item in enumerate(_exact_list(profile_root.get("overlay", []), "overlay"))),
            "overlay_id", "overlays",
        )
        subprocess_capabilities = _unique_mapping(
            (_parse_subprocess_capability(item, index) for index, item in enumerate(_exact_list(profile_root.get("subprocess_capability", []), "subprocess_capability"))),
            "capability_id", "subprocess capabilities",
        )
        call_capabilities = _unique_mapping(
            (_parse_call_capability(item, index) for index, item in enumerate(_exact_list(profile_root.get("call_capability", []), "call_capability"))),
            "capability_id", "call capabilities",
        )
        bindings = tuple(
            _parse_capability_binding(item, index)
            for index, item in enumerate(_exact_list(profile_root.get("capability_binding", []), "capability_binding"))
        )
        spec_digest = _require_lower_hex(
            profile_root["spec_capabilities_sha256"],
            "spec_capabilities_sha256", 64,
        )
        binding_digest = _require_lower_hex(
            profile_root["capability_bindings_sha256"],
            "capability_bindings_sha256", 64,
        )
        _validate_references(
            slots=slots, profiles=profiles, payloads=payloads, cases=cases, overlays=overlays,
            subprocess_capabilities=subprocess_capabilities, call_capabilities=call_capabilities,
            bindings=bindings, inventory_rows=inventory_rows,
            spec_digest=spec_digest, historical_digest=binding_digest,
        )
        stabilization_files = [
            _relative_path(item, "stabilization_test_files")
            for item in _exact_list(profile_root["stabilization_test_files"], "stabilization_test_files")
        ]
        stabilization_files = tuple(sorted(set(stabilization_files)))
        if len(stabilization_files) != len(_exact_list(profile_root["stabilization_test_files"], "stabilization_test_files")):
            raise ValueError("stabilization_test_files must be unique")
        normalized_profiles = {
            "schema_version": PROFILE_SCHEMA,
            "baseline_commit": baseline,
            "sealed_current_files_manifest": manifest_paths["sealed_current_files_manifest"],
            "sealed_current_absences_manifest": manifest_paths["sealed_current_absences_manifest"],
            "historical_blobs_manifest": manifest_paths["historical_blobs_manifest"],
            "retained_v7_manifest": manifest_paths["retained_v7_manifest"],
            "inventory_path": configured_inventory_path,
            "spec_capabilities_sha256": spec_digest,
            "capability_bindings_sha256": binding_digest,
            "interpreter_slots": tuple(slots[name] for name in sorted(slots)),
            "profiles": tuple(profiles[name] for name in sorted(profiles)),
            "payloads": tuple(payloads[name] for name in sorted(payloads)),
            "historical_cases": tuple(cases[name] for name in sorted(cases)),
            "overlays": tuple(overlays[name] for name in sorted(overlays)),
            "subprocess_capabilities": tuple(
                subprocess_capabilities[name] for name in sorted(subprocess_capabilities)
            ),
            "call_capabilities": tuple(
                call_capabilities[name] for name in sorted(call_capabilities)
            ),
            "capability_bindings": tuple(sorted(
                bindings,
                key=lambda item: (
                    item.approval_scope, item.item_id, item.capability_kind,
                    item.capability_id,
                ),
            )),
            "stabilization_test_files": stabilization_files,
        }
        profile_snapshot.revalidate()
        inventory_snapshot.revalidate()
        return ConfigurationBundle(
            root,
            profile_snapshot.path,
            inventory_snapshot.path,
            baseline,
            manifest_paths["sealed_current_files_manifest"],
            manifest_paths["sealed_current_absences_manifest"],
            manifest_paths["historical_blobs_manifest"],
            manifest_paths["retained_v7_manifest"],
            semantic_sha256(normalized_profiles),
            semantic_sha256(normalized_inventory),
            spec_digest,
            binding_digest,
            inventory_entries,
            slots,
            profiles,
            payloads,
            cases,
            overlays,
            subprocess_capabilities,
            call_capabilities,
            bindings,
            stabilization_files,
        )
    except EvidenceConfigurationError:
        raise
    except (OSError, ValueError, TypeError) as error:
        raise _configuration_error(
            "configuration_invalid", "test orchestration configuration is invalid",
            profiles_path=profiles_path.as_posix() if isinstance(profiles_path, Path) else str(profiles_path),
            inventory_path=inventory_path.as_posix() if isinstance(inventory_path, Path) else str(inventory_path),
        ) from error


def select_profile(
    bundle: ConfigurationBundle,
    name: str,
    *,
    payload_id: str | None = None,
    historical_case: str | None = None,
) -> ProfilePlan:
    if not isinstance(bundle, ConfigurationBundle):
        raise _configuration_error(
            "configuration_bundle_invalid", "configuration bundle is invalid",
            supplied_type=type(bundle).__name__,
        )
    if payload_id is not None and historical_case is not None:
        raise _configuration_error(
            "profile_selector_ambiguous", "payload and historical-case filters are mutually exclusive",
            profile=name,
        )
    profile = bundle.profiles.get(name)
    if profile is None:
        raise _configuration_error("profile_unknown", "profile is not defined", profile=name)
    selected = profile
    if payload_id is not None:
        if payload_id not in profile.payload_ids:
            raise _configuration_error(
                "payload_unknown", "payload does not belong to the selected profile",
                profile=name, payload_id=payload_id,
            )
        payload = bundle.payloads[payload_id]
        selected = replace(
            profile,
            payload_ids=(payload_id,),
            historical_case_ids=(),
            fixture_specs=payload.fixture_specs,
        )
    elif historical_case is not None:
        if historical_case not in profile.historical_case_ids:
            raise _configuration_error(
                "historical_case_unknown", "historical case does not belong to the selected profile",
                profile=name, historical_case=historical_case,
            )
        case = bundle.historical_cases[historical_case]
        payloads = tuple(bundle.payloads[payload] for payload in case.payload_ids)
        selected = replace(
            profile,
            payload_ids=case.payload_ids,
            historical_case_ids=(historical_case,),
            fixture_specs=_fixture_union(payloads),
        )
    applicable_scopes: set[str] = set()
    visiting: set[str] = set()

    def collect_scopes(candidate: ProfilePlan) -> None:
        if candidate.name in visiting:
            raise _configuration_error(
                "configuration_bundle_invalid", "profile graph contains a cycle",
                profile=candidate.name,
            )
        visiting.add(candidate.name)
        if candidate.subprofiles:
            for child_name in candidate.subprofiles:
                child = bundle.profiles.get(child_name)
                if child is None:
                    raise _configuration_error(
                        "configuration_bundle_invalid",
                        "profile references an unknown subprofile",
                        profile=candidate.name, subprofile=child_name,
                    )
                collect_scopes(child)
        else:
            for selected_payload_id in candidate.payload_ids:
                payload = bundle.payloads.get(selected_payload_id)
                if payload is None:
                    raise _configuration_error(
                        "configuration_bundle_invalid",
                        "profile references an unknown payload",
                        profile=candidate.name, payload_id=selected_payload_id,
                    )
                applicable_scopes.add(
                    "design"
                    if payload.target_kind is TargetKind.CURRENT_SNAPSHOT
                    else "historical_review"
                )
        visiting.remove(candidate.name)

    collect_scopes(selected)
    unapproved: set[str] = set()
    try:
        expanded = _expanded_capability_rows(
            subprocess_capabilities=bundle.subprocess_capabilities,
            call_capabilities=bundle.call_capabilities,
            bindings=bundle.capability_bindings,
        )
    except ValueError:
        expanded = {scope: () for scope in _SCOPE_DIGEST_FIELD}
    for scope in applicable_scopes:
        digest = getattr(bundle, _SCOPE_DIGEST_FIELD[scope])
        rows = expanded[scope]
        if (
            digest == _ZERO_SHA256
            or not rows
            or digest != semantic_sha256(rows)
        ):
            unapproved.add(scope)
    if unapproved:
        raise _configuration_error(
            "capability_approval_required",
            "applicable capabilities are not approved",
            profile=name, approval_scopes=tuple(sorted(unapproved)),
        )
    return selected


_EXIT_PRECEDENCE = (
    ("integrity", ExitCode.INTEGRITY),
    ("configuration", ExitCode.CONFIGURATION),
    ("phase", ExitCode.PHASE),
    ("runtime", ExitCode.RUNTIME),
    ("test_failure", ExitCode.TEST_FAILURE),
    ("optional_unavailable", ExitCode.OPTIONAL_UNAVAILABLE),
)


def choose_exit_code(conditions: Iterable[ObservedCondition]) -> ExitCode:
    observed: set[str] = set()
    for condition in conditions:
        if not isinstance(condition, ObservedCondition):
            raise ValueError("conditions must contain ObservedCondition values")
        if condition.affects_exit:
            observed.add(condition.category)
    for category, exit_code in _EXIT_PRECEDENCE:
        if category in observed:
            return exit_code
    return ExitCode.SUCCESS


__all__ = (
    "canonical_semantic_bytes",
    "choose_exit_code",
    "load_configuration",
    "parse_stable_id",
    "select_profile",
    "semantic_sha256",
)
