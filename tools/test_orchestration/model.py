"""Frozen value contracts shared by the standard-library test orchestrator."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, fields, is_dataclass
from enum import IntEnum, StrEnum
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath, PureWindowsPath
from types import MappingProxyType
from typing import Any, TypeAlias


FrozenValue: TypeAlias = (
    str | int | bool | None | tuple["FrozenValue", ...] | Mapping[str, "FrozenValue"]
)
FrozenMapping: TypeAlias = Mapping[str, FrozenValue]


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


def _require_string(value: object, name: str) -> str:
    if type(value) is not str or not value:
        raise ValueError(f"{name} must be a non-empty string")
    return value


def _require_optional_string(value: object, name: str) -> str | None:
    if value is None:
        return None
    return _require_string(value, name)


def _require_int(value: object, name: str, *, positive: bool = False) -> int:
    if type(value) is not int or value < (1 if positive else 0):
        qualifier = "positive" if positive else "non-negative"
        raise ValueError(f"{name} must be a {qualifier} integer")
    return value


def _require_bool(value: object, name: str) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{name} must be a boolean")
    return value


def _require_sha256(value: object, name: str, *, optional: bool = False) -> str | None:
    if optional and value is None:
        return None
    text = _require_string(value, name)
    if len(text) != 64 or any(character not in "0123456789abcdef" for character in text):
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    return text


def _require_git_oid(value: object, name: str) -> str:
    text = _require_string(value, name)
    if len(text) != 40 or any(character not in "0123456789abcdef" for character in text):
        raise ValueError(f"{name} must be a lowercase Git object identity")
    return text


def _normalise_relative_path(value: object, name: str) -> str:
    text = _require_string(value, name)
    if PureWindowsPath(text).drive or text.startswith(("/", "\\")):
        raise ValueError(f"{name} must be repository-relative")
    candidate = PurePosixPath(text.replace("\\", "/"))
    if candidate.is_absolute() or any(part in ("", ".", "..") for part in candidate.parts):
        raise ValueError(f"{name} must be normalized below the repository root")
    normalised = candidate.as_posix()
    if normalised in ("", "."):
        raise ValueError(f"{name} must name a path")
    return normalised


def _normalise_probe_id(value: object, name: str) -> str:
    text = _require_string(value, name)
    if not text.startswith("probe:") or text.count(":") != 1:
        raise ValueError(f"{name} must use the probe:<name> form")
    probe_name = text.removeprefix("probe:")
    if (
        not probe_name
        or probe_name != probe_name.lower()
        or not probe_name[0].isalnum()
        or not probe_name[-1].isalnum()
        or any(
            not character.isascii()
            or (not character.isalnum() and character not in "-_")
            for character in probe_name
        )
    ):
        raise ValueError(f"{name} contains an invalid probe name")
    return text


def _require_absolute_path(value: object, name: str) -> str:
    text = _require_string(value, name)
    windows = PureWindowsPath(text)
    posix = PurePosixPath(text)
    if not windows.is_absolute() and not posix.is_absolute():
        raise ValueError(f"{name} must be absolute")
    return text


def _freeze_value(value: object, name: str) -> Any:
    if value is None or type(value) in (str, int, bool):
        return value
    if isinstance(value, StrEnum):
        return value
    if isinstance(value, Mapping):
        items: list[tuple[str, Any]] = []
        for key, nested in value.items():
            if type(key) is not str or not key:
                raise ValueError(f"{name} mapping keys must be non-empty strings")
            items.append((key, _freeze_value(nested, f"{name}.{key}")))
        return MappingProxyType(dict(sorted(items)))
    if isinstance(value, (tuple, list)):
        return tuple(_freeze_value(item, name) for item in value)
    if is_dataclass(value) or isinstance(value, (Path, PurePosixPath)):
        return value
    raise ValueError(f"{name} contains an unsupported value")


def _semantic_value(value: object) -> object:
    if value is None or type(value) in (str, int, bool):
        return value
    if isinstance(value, (IntEnum, StrEnum)):
        return value.value
    if isinstance(value, (Path, PurePosixPath)):
        return value.as_posix()
    if is_dataclass(value):
        return {field.name: _semantic_value(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Mapping):
        if not all(type(key) is str for key in value):
            raise ValueError("semantic mappings require string keys")
        return {key: _semantic_value(value[key]) for key in sorted(value)}
    if isinstance(value, (tuple, list)):
        return [_semantic_value(item) for item in value]
    raise ValueError("semantic value has an unsupported type")


def canonical_semantic_bytes(value: object) -> bytes:
    return json.dumps(
        _semantic_value(value), allow_nan=False, ensure_ascii=True,
        separators=(",", ":"), sort_keys=True,
    ).encode("ascii")


def semantic_sha256(value: object) -> str:
    return sha256(canonical_semantic_bytes(value)).hexdigest()


def _sort_key(value: object) -> bytes:
    return canonical_semantic_bytes(value)


def _normalise_tuple(
    value: object,
    name: str,
    normaliser: Any = None,
    *,
    sort: bool = True,
    unique: bool = True,
    sort_key: Callable[[Any], object] | None = None,
) -> tuple[Any, ...]:
    if isinstance(value, (str, bytes, bytearray, Mapping)) or not isinstance(value, Iterable):
        raise ValueError(f"{name} must be a collection")
    convert = normaliser if normaliser is not None else (lambda item, _: _freeze_value(item, name))
    items = tuple(convert(item, name) for item in value)
    keys = tuple(_sort_key(item) for item in items)
    if unique and len(set(keys)) != len(keys):
        raise ValueError(f"{name} must not contain duplicates")
    if sort:
        order_keys = tuple(
            _sort_key(sort_key(item) if sort_key is not None else item)
            for item in items
        )
        return tuple(
            item
            for _, _, item in sorted(
                zip(order_keys, keys, items), key=lambda row: (row[0], row[1])
            )
        )
    return items


def _string_item(value: object, name: str) -> str:
    return _require_string(value, name)


def _path_item(value: object, name: str) -> str:
    return _normalise_relative_path(value, name)


def _model_item(expected_type: type[Any]) -> Any:
    def validate(value: object, name: str) -> object:
        if not isinstance(value, expected_type):
            raise ValueError(f"{name} values must be {expected_type.__name__}")
        return value
    return validate


def _index_unique(
    values: Iterable[Any], name: str, key: Callable[[Any], object],
) -> dict[object, Any]:
    indexed: dict[object, Any] = {}
    for item in values:
        identity = key(item)
        if identity in indexed:
            raise ValueError(f"{name} must be unique by semantic identity")
        indexed[identity] = item
    return indexed


def _freeze_mapping(value: object, name: str) -> MappingProxyType:
    frozen = _freeze_value(value, name)
    if not isinstance(frozen, MappingProxyType):
        raise ValueError(f"{name} must be a mapping")
    return frozen


def _freeze_count_mapping(value: object, name: str) -> MappingProxyType:
    frozen = _freeze_mapping(value, name)
    for key, count in frozen.items():
        _require_int(count, f"{name}.{key}")
    return frozen


def _enum(value: object, enum_type: type[Any], name: str) -> Any:
    try:
        return enum_type(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{name} has an unsupported value") from error


@dataclass(frozen=True, slots=True)
class StageBudgets:
    setup_ns: int
    child_ns: int
    termination_grace_ns: int
    cleanup_ns: int
    total_ns: int

    def __post_init__(self) -> None:
        for name in ("setup_ns", "child_ns", "termination_grace_ns", "cleanup_ns", "total_ns"):
            _require_int(getattr(self, name), name, positive=True)
        reserved = self.setup_ns + self.child_ns + self.termination_grace_ns + self.cleanup_ns
        if self.total_ns < reserved:
            raise ValueError("total_ns must reserve every stage budget")


@dataclass(frozen=True, slots=True)
class StableSelector:
    stable_id: str
    relative_path: PurePosixPath
    case_name: str
    method_name: str

    def __post_init__(self) -> None:
        _require_string(self.stable_id, "stable_id")
        path = PurePosixPath(_normalise_relative_path(self.relative_path.as_posix(), "relative_path"))
        if not path.parts or path.parts[0] != "tests" or path.suffix != ".py":
            raise ValueError("relative_path must name a Python file below tests")
        object.__setattr__(self, "relative_path", path)
        if not _require_string(self.case_name, "case_name").isidentifier():
            raise ValueError("case_name must be a Python identifier")
        method = _require_string(self.method_name, "method_name")
        if not method.isidentifier() or not method.startswith("test_"):
            raise ValueError("method_name must be a test_ Python identifier")
        expected = f"{path.as_posix()}::{self.case_name}::{method}"
        if self.stable_id != expected:
            raise ValueError("stable_id fields do not agree")


@dataclass(frozen=True, slots=True)
class InterpreterIdentity:
    executable: str
    resolved_executable: str
    platform_identity: str
    executable_sha256: str
    implementation: str
    version: tuple[int, int, int, str, int]
    prefix: str
    base_prefix: str
    no_user_site: bool
    safe_path: bool
    dont_write_bytecode: bool
    distributions_sha256: str
    dependency_lock_sha256: str | None

    def __post_init__(self) -> None:
        for name in ("executable", "resolved_executable", "prefix", "base_prefix"):
            _require_absolute_path(getattr(self, name), name)
        _require_string(self.platform_identity, "platform_identity")
        for name in ("executable_sha256", "distributions_sha256"):
            _require_sha256(getattr(self, name), name)
        _require_sha256(self.dependency_lock_sha256, "dependency_lock_sha256", optional=True)
        _require_string(self.implementation, "implementation")
        version = _normalise_tuple(self.version, "version", sort=False, unique=False)
        if len(version) != 5:
            raise ValueError("version must contain major, minor, micro, release level, and serial")
        for index in (0, 1, 2, 4):
            _require_int(version[index], f"version[{index}]")
        if type(version[3]) is not str or version[3] not in ("alpha", "beta", "candidate", "final"):
            raise ValueError("version release level is unsupported")
        object.__setattr__(self, "version", version)
        for name in ("no_user_site", "safe_path", "dont_write_bytecode"):
            _require_bool(getattr(self, name), name)


@dataclass(frozen=True, slots=True)
class InterpreterBinding:
    slot_name: str
    identity: InterpreterIdentity

    def __post_init__(self) -> None:
        _require_string(self.slot_name, "slot_name")
        if not isinstance(self.identity, InterpreterIdentity):
            raise ValueError("identity must be an InterpreterIdentity")


@dataclass(frozen=True, slots=True)
class TargetIdentity:
    kind: TargetKind
    root: str
    head_commit: str
    root_tree_oid: str
    file_inventory_sha256: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "kind", _enum(self.kind, TargetKind, "kind"))
        _require_absolute_path(self.root, "root")
        _require_git_oid(self.head_commit, "head_commit")
        _require_git_oid(self.root_tree_oid, "root_tree_oid")
        _require_sha256(self.file_inventory_sha256, "file_inventory_sha256")


@dataclass(frozen=True, slots=True)
class PrimaryRootIdentity:
    resolved_path: str
    platform_identity: str
    capture_sha256: str

    def __post_init__(self) -> None:
        _require_absolute_path(self.resolved_path, "resolved_path")
        _require_string(self.platform_identity, "platform_identity")
        _require_sha256(self.capture_sha256, "capture_sha256")


@dataclass(frozen=True, slots=True)
class GitToolIdentity:
    executable: str
    resolved_executable: str
    platform_identity: str
    executable_sha256: str

    def __post_init__(self) -> None:
        _require_absolute_path(self.executable, "executable")
        _require_absolute_path(self.resolved_executable, "resolved_executable")
        _require_string(self.platform_identity, "platform_identity")
        _require_sha256(self.executable_sha256, "executable_sha256")


@dataclass(frozen=True, slots=True)
class InterpreterSlot:
    name: str
    resolution: str
    windows_relative_path: str | None
    posix_relative_path: str | None
    environment_variable: str | None
    implementation: str
    minimum_version: tuple[int, int] | None
    exact_version: tuple[int, int] | None
    required_for_full: bool

    def __post_init__(self) -> None:
        _require_string(self.name, "name")
        _require_string(self.implementation, "implementation")
        _require_bool(self.required_for_full, "required_for_full")
        if self.resolution not in ("repository_relative", "environment_absolute"):
            raise ValueError("resolution must be repository_relative or environment_absolute")
        for name in ("windows_relative_path", "posix_relative_path"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, _normalise_relative_path(value, name))
        _require_optional_string(self.environment_variable, "environment_variable")
        for name in ("minimum_version", "exact_version"):
            value = getattr(self, name)
            if value is not None:
                pair = _normalise_tuple(value, name, lambda item, label: _require_int(item, label), sort=False)
                if len(pair) != 2:
                    raise ValueError(f"{name} must contain exactly major and minor")
                object.__setattr__(self, name, pair)
        if self.resolution == "repository_relative":
            if None in (self.windows_relative_path, self.posix_relative_path, self.minimum_version):
                raise ValueError("repository_relative slots require both paths and minimum_version")
            if self.environment_variable is not None or self.exact_version is not None:
                raise ValueError("repository_relative slots cannot declare environment/exact values")
        else:
            if self.environment_variable is None or self.exact_version is None:
                raise ValueError("environment_absolute slots require environment_variable and exact_version")
            if self.windows_relative_path is not None or self.posix_relative_path is not None or self.minimum_version is not None:
                raise ValueError("environment_absolute slots cannot declare repository-relative values")


@dataclass(frozen=True, slots=True)
class FixtureSpec:
    relative_path: str
    path_kind: str
    byte_length: int
    raw_sha256: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "relative_path", _normalise_relative_path(self.relative_path, "relative_path"))
        _require_string(self.path_kind, "path_kind")
        _require_int(self.byte_length, "byte_length")
        _require_sha256(self.raw_sha256, "raw_sha256")


@dataclass(frozen=True, slots=True)
class ProfilePlan:
    name: str
    interpreter_slots: tuple[str, ...]
    default_interpreter_slot: str | None
    payload_ids: tuple[str, ...]
    historical_case_ids: tuple[str, ...]
    subprofiles: tuple[str, ...]
    budgets: StageBudgets
    fixture_specs: tuple[FixtureSpec, ...]
    gpu_optional: bool
    definition_sha256: str

    def __post_init__(self) -> None:
        _require_string(self.name, "name")
        for name in ("interpreter_slots", "payload_ids", "historical_case_ids", "subprofiles"):
            object.__setattr__(self, name, _normalise_tuple(getattr(self, name), name, _string_item))
        _require_optional_string(self.default_interpreter_slot, "default_interpreter_slot")
        if self.default_interpreter_slot is not None and self.default_interpreter_slot not in self.interpreter_slots:
            raise ValueError("default_interpreter_slot must belong to interpreter_slots")
        if self.name == "full":
            if self.default_interpreter_slot is not None or self.payload_ids or self.historical_case_ids or not self.subprofiles:
                raise ValueError("full requires only subprofiles and no direct default or selectors")
        elif self.default_interpreter_slot is None or self.subprofiles or not (self.payload_ids or self.historical_case_ids):
            raise ValueError("direct profiles require a default, direct selectors, and no subprofiles")
        if not isinstance(self.budgets, StageBudgets):
            raise ValueError("budgets must be StageBudgets")
        object.__setattr__(self, "fixture_specs", _normalise_tuple(
            self.fixture_specs, "fixture_specs", _model_item(FixtureSpec),
            sort_key=lambda item: item.relative_path,
        ))
        _require_bool(self.gpu_optional, "gpu_optional")
        _require_sha256(self.definition_sha256, "definition_sha256")


@dataclass(frozen=True, slots=True)
class InventoryExpectation:
    kind: str
    applicable_platforms: tuple[str, ...]
    skip_safe_reason_code: str | None

    def __post_init__(self) -> None:
        if self.kind not in ("pass", "platform_conditioned", "case_defined"):
            raise ValueError("inventory expectation kind is unsupported")
        object.__setattr__(self, "applicable_platforms", _normalise_tuple(self.applicable_platforms, "applicable_platforms", _string_item))
        _require_optional_string(self.skip_safe_reason_code, "skip_safe_reason_code")
        if self.kind == "platform_conditioned":
            if not self.applicable_platforms or set(self.applicable_platforms) - {"windows", "posix"} or self.skip_safe_reason_code is None:
                raise ValueError("platform_conditioned expectations require platforms and a reason")
        elif self.applicable_platforms or self.skip_safe_reason_code is not None:
            raise ValueError("only platform_conditioned expectations carry platform fields")


@dataclass(frozen=True, slots=True)
class ResolvedInventoryItem:
    selector: StableSelector
    expectation: InventoryExpectation

    def __post_init__(self) -> None:
        if not isinstance(self.selector, StableSelector) or not isinstance(self.expectation, InventoryExpectation):
            raise ValueError("resolved inventory item has invalid nested values")


@dataclass(frozen=True, slots=True)
class InventoryEntry:
    selector: StableSelector
    profile_name: str | None
    payload_id: str | None
    expectation: InventoryExpectation | None
    exclusion_reason: str | None
    exclusion_owner: str | None
    exclusion_milestone: str | None

    def __post_init__(self) -> None:
        if not isinstance(self.selector, StableSelector):
            raise ValueError("selector must be StableSelector")
        for name in (
            "profile_name", "payload_id", "exclusion_reason", "exclusion_owner",
            "exclusion_milestone",
        ):
            _require_optional_string(getattr(self, name), name)
        if self.expectation is not None and not isinstance(self.expectation, InventoryExpectation):
            raise ValueError("expectation must be InventoryExpectation or null")
        assignment = (self.profile_name, self.payload_id, self.expectation)
        exclusion = (self.exclusion_reason, self.exclusion_owner, self.exclusion_milestone)
        assignment_complete = all(value is not None for value in assignment)
        exclusion_complete = all(value is not None for value in exclusion)
        if assignment_complete == exclusion_complete:
            raise ValueError("inventory entry requires exactly one complete assignment or exclusion")
        if not assignment_complete and any(value is not None for value in assignment):
            raise ValueError("inventory assignment fields must be all present or all null")
        if not exclusion_complete and any(value is not None for value in exclusion):
            raise ValueError("inventory exclusion fields must be all present or all null")


@dataclass(frozen=True, slots=True)
class LifecycleFixturePlan:
    fixture_id: str
    kind: str
    relative_path: str
    class_name: str | None
    member_ids: tuple[str, ...]
    allowed_write_roots: tuple[str, ...]
    forbidden_relative_paths: tuple[str, ...]
    serialized: bool

    def __post_init__(self) -> None:
        _require_string(self.fixture_id, "fixture_id")
        if self.kind not in ("module", "class"):
            raise ValueError("lifecycle fixture kind must be module or class")
        object.__setattr__(self, "relative_path", _normalise_relative_path(self.relative_path, "relative_path"))
        _require_optional_string(self.class_name, "class_name")
        if (self.kind == "class") != (self.class_name is not None):
            raise ValueError("class_name must be present exactly for class fixtures")
        object.__setattr__(self, "member_ids", _normalise_tuple(self.member_ids, "member_ids", _string_item))
        object.__setattr__(self, "allowed_write_roots", _normalise_tuple(self.allowed_write_roots, "allowed_write_roots", _string_item))
        object.__setattr__(self, "forbidden_relative_paths", _normalise_tuple(self.forbidden_relative_paths, "forbidden_relative_paths", _path_item))
        _require_bool(self.serialized, "serialized")


@dataclass(frozen=True, slots=True)
class PayloadPlan:
    payload_id: str
    profile_name: str
    target_kind: TargetKind
    allowed_interpreter_slots: tuple[str, ...]
    inventory_items: tuple[ResolvedInventoryItem, ...]
    probe_ids: tuple[str, ...]
    lifecycle_fixtures: tuple[LifecycleFixturePlan, ...]
    environment_additions: FrozenMapping
    environment_removals: tuple[str, ...]
    allowed_write_roots: tuple[str, ...]
    forbidden_relative_paths: tuple[str, ...]
    fixture_specs: tuple[FixtureSpec, ...]
    serialized: bool

    def __post_init__(self) -> None:
        _require_string(self.payload_id, "payload_id")
        _require_string(self.profile_name, "profile_name")
        object.__setattr__(self, "target_kind", _enum(self.target_kind, TargetKind, "target_kind"))
        object.__setattr__(self, "allowed_interpreter_slots", _normalise_tuple(self.allowed_interpreter_slots, "allowed_interpreter_slots", _string_item))
        object.__setattr__(self, "inventory_items", _normalise_tuple(
            self.inventory_items, "inventory_items", _model_item(ResolvedInventoryItem),
            sort_key=lambda item: item.selector.stable_id,
        ))
        object.__setattr__(self, "probe_ids", _normalise_tuple(
            self.probe_ids, "probe_ids", _normalise_probe_id,
        ))
        object.__setattr__(self, "lifecycle_fixtures", _normalise_tuple(
            self.lifecycle_fixtures, "lifecycle_fixtures", _model_item(LifecycleFixturePlan),
            sort_key=lambda item: item.fixture_id,
        ))
        additions = _freeze_mapping(self.environment_additions, "environment_additions")
        if any(type(value) is not str for value in additions.values()):
            raise ValueError("environment_additions values must be strings")
        object.__setattr__(self, "environment_additions", additions)
        for name in ("environment_removals", "allowed_write_roots"):
            object.__setattr__(self, name, _normalise_tuple(getattr(self, name), name, _string_item))
        object.__setattr__(self, "forbidden_relative_paths", _normalise_tuple(self.forbidden_relative_paths, "forbidden_relative_paths", _path_item))
        object.__setattr__(self, "fixture_specs", _normalise_tuple(
            self.fixture_specs, "fixture_specs", _model_item(FixtureSpec),
            sort_key=lambda item: item.relative_path,
        ))
        _require_bool(self.serialized, "serialized")


@dataclass(frozen=True, slots=True)
class HistoricalItemExpectation:
    item_id: str
    outcome: str
    phase: str | None
    exception_type: str | None
    safe_reason_code: str | None
    body_entered: bool | None
    capability_counters: FrozenMapping

    def __post_init__(self) -> None:
        _require_string(self.item_id, "item_id")
        if self.outcome not in ("pass", "expected_negative"):
            raise ValueError("historical outcome must be pass or expected_negative")
        for name in ("phase", "exception_type", "safe_reason_code"):
            _require_optional_string(getattr(self, name), name)
        if self.body_entered is not None:
            _require_bool(self.body_entered, "body_entered")
        object.__setattr__(self, "capability_counters", _freeze_count_mapping(self.capability_counters, "capability_counters"))
        negative_fields = (self.phase, self.exception_type, self.safe_reason_code, self.body_entered)
        if self.outcome == "expected_negative" and any(value is None for value in negative_fields):
            raise ValueError("expected_negative requires complete failure fields")
        if self.outcome == "pass" and any(value is not None for value in negative_fields):
            raise ValueError("pass expectations cannot carry failure fields")


@dataclass(frozen=True, slots=True)
class HistoricalSnapshotExpectation:
    phase: str
    commit: str
    root_tree_oid: str
    governing_decision: str

    def __post_init__(self) -> None:
        _require_string(self.phase, "phase")
        _require_git_oid(self.commit, "commit")
        _require_git_oid(self.root_tree_oid, "root_tree_oid")
        _require_string(self.governing_decision, "governing_decision")


@dataclass(frozen=True, slots=True)
class HistoricalBlobExpectation:
    commit: str
    relative_path: str
    git_blob_oid: str
    raw_sha256: str
    role: str
    phase: str
    governing_decision: str

    def __post_init__(self) -> None:
        _require_git_oid(self.commit, "commit")
        object.__setattr__(self, "relative_path", _normalise_relative_path(self.relative_path, "relative_path"))
        _require_git_oid(self.git_blob_oid, "git_blob_oid")
        _require_sha256(self.raw_sha256, "raw_sha256")
        for name in ("role", "phase", "governing_decision"):
            _require_string(getattr(self, name), name)


@dataclass(frozen=True, slots=True)
class HistoricalCase:
    case_id: str
    phase: str
    commit: str
    root_tree_oid: str
    payload_ids: tuple[str, ...]
    expected_vector: FrozenMapping
    item_expectations: tuple[HistoricalItemExpectation, ...]
    overlay_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        for name in ("case_id", "phase"):
            _require_string(getattr(self, name), name)
        _require_git_oid(self.commit, "commit")
        _require_git_oid(self.root_tree_oid, "root_tree_oid")
        object.__setattr__(self, "payload_ids", _normalise_tuple(self.payload_ids, "payload_ids", _string_item))
        if not self.payload_ids:
            raise ValueError("historical case payload_ids must not be empty")
        vector = _freeze_mapping(self.expected_vector, "expected_vector")
        kind = vector.get("kind")
        positive_fields = {
            "kind", "passed", "assertion_failed", "setup_failed", "body_entered",
            "owner_calls", "scientific_calls",
        }
        negative_fields = positive_fields | {"phase", "exception_type", "safe_reason_code"}
        expected_fields = positive_fields if kind == "positive" else negative_fields if kind == "negative" else None
        if expected_fields is None or set(vector) != expected_fields:
            raise ValueError("expected_vector must be an exact positive or negative variant")
        for name in positive_fields - {"kind"}:
            _require_int(vector[name], f"expected_vector.{name}")
        if kind == "negative":
            for name in ("phase", "exception_type", "safe_reason_code"):
                _require_string(vector[name], f"expected_vector.{name}")
        object.__setattr__(self, "expected_vector", vector)
        object.__setattr__(self, "item_expectations", _normalise_tuple(
            self.item_expectations, "item_expectations", _model_item(HistoricalItemExpectation),
            sort_key=lambda item: item.item_id,
        ))
        object.__setattr__(self, "overlay_ids", _normalise_tuple(self.overlay_ids, "overlay_ids", _string_item))


@dataclass(frozen=True, slots=True)
class OverlaySpec:
    overlay_id: str
    source_commit: str
    source_path: str
    destination_path: str
    byte_length: int
    raw_sha256: str

    def __post_init__(self) -> None:
        _require_string(self.overlay_id, "overlay_id")
        _require_git_oid(self.source_commit, "source_commit")
        for name in ("source_path", "destination_path"):
            object.__setattr__(self, name, _normalise_relative_path(getattr(self, name), name))
        _require_int(self.byte_length, "byte_length")
        _require_sha256(self.raw_sha256, "raw_sha256")


@dataclass(frozen=True, slots=True)
class SubprocessCapability:
    capability_id: str
    executable_role: str
    executable_slot: str
    executable_constraints: FrozenMapping
    argv: tuple[str, ...]
    argv_template: tuple[str, ...]
    dynamic_program_sha256: str | None
    cwd_class: str
    environment_additions: FrozenMapping
    environment_removals: tuple[str, ...]
    timeout_ns: int
    expected_return_category: str
    read_roots: tuple[str, ...]
    write_roots: tuple[str, ...]
    fixed_descendant_permission: bool

    def __post_init__(self) -> None:
        for name in ("capability_id", "cwd_class", "expected_return_category"):
            _require_string(getattr(self, name), name)
        if self.executable_role not in ("python", "git"):
            raise ValueError("executable_role must be python or git")
        if self.executable_slot not in ("active_worker", "development", "cpython311", "git"):
            raise ValueError("executable_slot is unsupported")
        if (self.executable_role == "git") != (self.executable_slot == "git"):
            raise ValueError("executable role and slot disagree")
        object.__setattr__(self, "executable_constraints", _freeze_mapping(self.executable_constraints, "executable_constraints"))
        object.__setattr__(self, "argv", _normalise_tuple(self.argv, "argv", _string_item, sort=False, unique=False))
        object.__setattr__(self, "argv_template", _normalise_tuple(self.argv_template, "argv_template", _string_item, sort=False, unique=False))
        if bool(self.argv) == bool(self.argv_template):
            raise ValueError("exactly one of argv and argv_template must be nonempty")
        _require_sha256(self.dynamic_program_sha256, "dynamic_program_sha256", optional=True)
        additions = _freeze_mapping(self.environment_additions, "environment_additions")
        if any(type(value) is not str for value in additions.values()):
            raise ValueError("environment_additions values must be strings")
        object.__setattr__(self, "environment_additions", additions)
        for name in ("environment_removals", "read_roots", "write_roots"):
            object.__setattr__(self, name, _normalise_tuple(getattr(self, name), name, _string_item))
        _require_int(self.timeout_ns, "timeout_ns", positive=True)
        _require_bool(self.fixed_descendant_permission, "fixed_descendant_permission")


@dataclass(frozen=True, slots=True)
class CallCapability:
    capability_id: str
    kind: str
    module_name: str
    qualified_name: str
    action: str
    maximum_calls: int
    return_contract: str

    def __post_init__(self) -> None:
        for name in ("capability_id", "module_name", "qualified_name", "action"):
            _require_string(getattr(self, name), name)
        if self.kind not in ("owner", "scientific", "cuda_query", "cuda_allocation"):
            raise ValueError("call capability kind is unsupported")
        _require_int(self.maximum_calls, "maximum_calls", positive=True)
        _require_string(self.return_contract, "return_contract")


@dataclass(frozen=True, slots=True)
class CapabilityBinding:
    item_id: str
    approval_scope: str
    capability_kind: str
    capability_id: str

    def __post_init__(self) -> None:
        for name in ("item_id", "capability_id"):
            _require_string(getattr(self, name), name)
        if self.approval_scope not in ("design", "historical_review"):
            raise ValueError("approval_scope is unsupported")
        if self.capability_kind not in ("subprocess", "call"):
            raise ValueError("capability_kind is unsupported")


def _normalise_capability_bindings(value: object) -> tuple[CapabilityBinding, ...]:
    bindings = _normalise_tuple(
        value, "capability_bindings", _model_item(CapabilityBinding), sort=False
    )
    return tuple(sorted(
        bindings,
        key=lambda item: (
            item.approval_scope, item.item_id, item.capability_kind, item.capability_id,
        ),
    ))


@dataclass(frozen=True, slots=True)
class EvidenceManifestIdentity:
    relative_path: str
    schema_version: str
    byte_length: int
    raw_sha256: str
    semantic_sha256: str
    platform_identity: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "relative_path", _normalise_relative_path(self.relative_path, "relative_path"))
        _require_string(self.schema_version, "schema_version")
        _require_int(self.byte_length, "byte_length")
        _require_sha256(self.raw_sha256, "raw_sha256")
        _require_sha256(self.semantic_sha256, "semantic_sha256")
        _require_string(self.platform_identity, "platform_identity")


@dataclass(frozen=True, slots=True)
class EvidenceFileExpectation:
    relative_path: str
    byte_length: int
    raw_sha256: str
    role: str
    platform_identity: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "relative_path", _normalise_relative_path(self.relative_path, "relative_path"))
        _require_int(self.byte_length, "byte_length")
        _require_sha256(self.raw_sha256, "raw_sha256")
        _require_string(self.role, "role")
        _require_string(self.platform_identity, "platform_identity")


@dataclass(frozen=True, slots=True)
class EvidenceAbsenceExpectation:
    relative_path: str
    role: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "relative_path", _normalise_relative_path(self.relative_path, "relative_path"))
        _require_string(self.role, "role")


@dataclass(frozen=True, slots=True)
class EvidenceGuardPlan:
    semantic_sha256: str
    manifest_identities: tuple[EvidenceManifestIdentity, ...]
    present_files: tuple[EvidenceFileExpectation, ...]
    absences: tuple[EvidenceAbsenceExpectation, ...]

    def __post_init__(self) -> None:
        for name, expected in (("manifest_identities", EvidenceManifestIdentity), ("present_files", EvidenceFileExpectation), ("absences", EvidenceAbsenceExpectation)):
            object.__setattr__(self, name, _normalise_tuple(
                getattr(self, name), name, _model_item(expected),
                sort_key=lambda item: item.relative_path,
            ))
        if (
            len(self.manifest_identities) != 4
            or len(self.present_files) != 6
            or len(self.absences) != 18
        ):
            raise ValueError("evidence guard requires exactly four manifests, six files, and eighteen absences")
        path_groups = (
            tuple(item.relative_path for item in self.manifest_identities),
            tuple(item.relative_path for item in self.present_files),
            tuple(item.relative_path for item in self.absences),
        )
        if any(len(paths) != len(set(paths)) for paths in path_groups):
            raise ValueError("evidence guard paths must be unique within each collection")
        if set(path_groups[1]) & set(path_groups[2]):
            raise ValueError("present and absent evidence paths must be disjoint")
        expected_digest = semantic_sha256({
            "manifest_identities": self.manifest_identities,
            "present_files": self.present_files,
            "absences": self.absences,
        })
        _require_sha256(self.semantic_sha256, "semantic_sha256")
        if self.semantic_sha256 != expected_digest:
            raise ValueError("evidence guard semantic_sha256 does not match its canonical form")


@dataclass(frozen=True, slots=True)
class ObservedCondition:
    category: str
    code: str
    affects_exit: bool
    context: FrozenMapping

    def __post_init__(self) -> None:
        allowed = {"integrity", "configuration", "phase", "runtime", "test_failure", "optional_unavailable"}
        if self.category not in allowed:
            raise ValueError("condition category is unsupported")
        _require_string(self.code, "code")
        _require_bool(self.affects_exit, "affects_exit")
        if self.category != "optional_unavailable" and not self.affects_exit:
            raise ValueError("non-optional conditions must affect the process exit")
        object.__setattr__(self, "context", _freeze_mapping(self.context, "context"))


@dataclass(frozen=True, slots=True)
class EvidenceGuardSummary:
    before_semantic_sha256: str | None
    after_semantic_sha256: str | None
    status: str
    conditions: tuple[ObservedCondition, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "conditions", _normalise_tuple(self.conditions, "conditions", _model_item(ObservedCondition)))
        if self.status not in ("unchanged", "changed", "not_measured"):
            raise ValueError("evidence guard status is unsupported")
        _require_sha256(self.before_semantic_sha256, "before_semantic_sha256", optional=True)
        _require_sha256(self.after_semantic_sha256, "after_semantic_sha256", optional=True)
        if self.status == "not_measured":
            if self.before_semantic_sha256 is not None or self.after_semantic_sha256 is not None:
                raise ValueError("not_measured requires both digests to be null")
        elif self.before_semantic_sha256 is None or self.after_semantic_sha256 is None:
            raise ValueError("measured guards require both digests")
        elif (self.before_semantic_sha256 == self.after_semantic_sha256) != (self.status == "unchanged"):
            raise ValueError("evidence guard status disagrees with measured digests")
        if self.status == "changed" and not any(item.category == "integrity" for item in self.conditions):
            raise ValueError("changed evidence requires an integrity condition")


@dataclass(frozen=True, slots=True)
class ResolvedWorkerPlan:
    semantic_sha256: str
    profile: ProfilePlan
    inventory_entries: tuple[ResolvedInventoryItem, ...]
    payloads: tuple[PayloadPlan, ...]
    historical_cases: tuple[HistoricalCase, ...]
    historical_snapshots: tuple[HistoricalSnapshotExpectation, ...]
    historical_blobs: tuple[HistoricalBlobExpectation, ...]
    overlays: tuple[OverlaySpec, ...]
    subprocess_capabilities: tuple[SubprocessCapability, ...]
    call_capabilities: tuple[CallCapability, ...]
    capability_bindings: tuple[CapabilityBinding, ...]
    spec_capabilities_sha256: str
    capability_bindings_sha256: str

    def __post_init__(self) -> None:
        if not isinstance(self.profile, ProfilePlan):
            raise ValueError("profile must be ProfilePlan")
        collections = (
            ("inventory_entries", ResolvedInventoryItem, lambda item: item.selector.stable_id),
            ("payloads", PayloadPlan, lambda item: item.payload_id),
            ("historical_cases", HistoricalCase, lambda item: item.case_id),
            ("historical_snapshots", HistoricalSnapshotExpectation, lambda item: (item.phase, item.commit)),
            ("historical_blobs", HistoricalBlobExpectation, lambda item: (item.commit, item.relative_path)),
            ("overlays", OverlaySpec, lambda item: item.overlay_id),
            ("subprocess_capabilities", SubprocessCapability, lambda item: item.capability_id),
            ("call_capabilities", CallCapability, lambda item: item.capability_id),
            ("capability_bindings", CapabilityBinding, None),
        )
        for name, expected, sort_key in collections:
            object.__setattr__(self, name, _normalise_tuple(
                getattr(self, name), name, _model_item(expected), sort_key=sort_key,
            ))
        for name in ("spec_capabilities_sha256", "capability_bindings_sha256"):
            _require_sha256(getattr(self, name), name)
        object.__setattr__(self, "capability_bindings", _normalise_capability_bindings(self.capability_bindings))
        payloads = _index_unique(self.payloads, "payloads", lambda item: item.payload_id)
        if set(payloads) != set(self.profile.payload_ids):
            raise ValueError("resolved payloads must exactly match the selected profile")
        if any(item.profile_name != self.profile.name for item in payloads.values()):
            raise ValueError("resolved payload ownership must match the selected profile")

        expected_inventory: dict[str, ResolvedInventoryItem] = {}
        expected_fixtures: dict[str, FixtureSpec] = {}
        known_item_ids: set[str] = set()
        for payload in payloads.values():
            for item in payload.inventory_items:
                stable_id = item.selector.stable_id
                if stable_id in expected_inventory:
                    raise ValueError("resolved inventory ownership must be exact")
                expected_inventory[stable_id] = item
                known_item_ids.add(stable_id)
            known_item_ids.update(payload.probe_ids)
            for fixture in payload.lifecycle_fixtures:
                if fixture.fixture_id in known_item_ids:
                    raise ValueError("resolved item identities must be unique")
                known_item_ids.add(fixture.fixture_id)
            for fixture in payload.fixture_specs:
                previous = expected_fixtures.get(fixture.relative_path)
                if previous is not None and previous != fixture:
                    raise ValueError("resolved fixtures contain conflicting identities")
                expected_fixtures[fixture.relative_path] = fixture
        actual_inventory = _index_unique(
            self.inventory_entries, "inventory_entries",
            lambda item: item.selector.stable_id,
        )
        if actual_inventory != expected_inventory:
            raise ValueError("resolved inventory must exactly match payload ownership")
        profile_fixtures = _index_unique(
            self.profile.fixture_specs, "profile.fixture_specs",
            lambda item: item.relative_path,
        )
        if profile_fixtures != expected_fixtures:
            raise ValueError("resolved fixtures must exactly match the selected profile")

        cases = _index_unique(
            self.historical_cases, "historical_cases", lambda item: item.case_id,
        )
        if set(cases) != set(self.profile.historical_case_ids):
            raise ValueError("resolved historical cases must exactly match the selected profile")
        expected_overlay_ids: set[str] = set()
        snapshot_keys: set[tuple[str, str, str]] = set()
        case_commits: set[str] = set()
        for case in cases.values():
            if not set(case.payload_ids).issubset(payloads):
                raise ValueError("historical case references an unresolved payload")
            expected_overlay_ids.update(case.overlay_ids)
            snapshot_keys.add((case.phase, case.commit, case.root_tree_oid))
            case_commits.add(case.commit)
            case_item_ids: set[str] = set()
            for payload_id in case.payload_ids:
                payload = payloads[payload_id]
                case_item_ids.update(
                    item.selector.stable_id for item in payload.inventory_items
                )
                case_item_ids.update(payload.probe_ids)
                case_item_ids.update(
                    fixture.fixture_id for fixture in payload.lifecycle_fixtures
                )
            if any(item.item_id not in case_item_ids for item in case.item_expectations):
                raise ValueError("historical expectations reference unresolved items")
        overlays = _index_unique(self.overlays, "overlays", lambda item: item.overlay_id)
        if set(overlays) != expected_overlay_ids:
            raise ValueError("resolved overlays must exactly match historical cases")
        snapshots = _index_unique(
            self.historical_snapshots, "historical_snapshots",
            lambda item: (item.phase, item.commit, item.root_tree_oid),
        )
        if set(snapshots) != snapshot_keys:
            raise ValueError("resolved snapshots must exactly match historical cases")
        blobs = _index_unique(
            self.historical_blobs, "historical_blobs",
            lambda item: (item.commit, item.relative_path),
        )
        blob_commits = {item.commit for item in blobs.values()}
        if blob_commits - case_commits or (case_commits and blob_commits != case_commits):
            raise ValueError("resolved blobs must cover only and every historical commit")

        subprocess_capabilities = _index_unique(
            self.subprocess_capabilities, "subprocess_capabilities",
            lambda item: item.capability_id,
        )
        call_capabilities = _index_unique(
            self.call_capabilities, "call_capabilities",
            lambda item: item.capability_id,
        )
        referenced_subprocess: set[str] = set()
        referenced_calls: set[str] = set()
        for binding in self.capability_bindings:
            if binding.item_id not in known_item_ids:
                raise ValueError("capability binding references an unresolved item")
            if binding.capability_kind == "subprocess":
                referenced_subprocess.add(binding.capability_id)
            else:
                referenced_calls.add(binding.capability_id)
        if set(subprocess_capabilities) != referenced_subprocess:
            raise ValueError("resolved subprocess definitions must exactly match bindings")
        if set(call_capabilities) != referenced_calls:
            raise ValueError("resolved call definitions must exactly match bindings")
        _require_sha256(self.semantic_sha256, "semantic_sha256")
        payload = {field.name: getattr(self, field.name) for field in fields(self) if field.name != "semantic_sha256"}
        if self.semantic_sha256 != semantic_sha256(payload):
            raise ValueError("resolved plan semantic_sha256 does not match its canonical form")


@dataclass(frozen=True, slots=True)
class ExecutionBundle:
    configuration: ConfigurationBundle
    evidence_guard_plan: EvidenceGuardPlan
    historical_snapshots: tuple[HistoricalSnapshotExpectation, ...]
    historical_blobs: tuple[HistoricalBlobExpectation, ...]
    semantic_sha256: str

    def __post_init__(self) -> None:
        if not isinstance(self.configuration, ConfigurationBundle):
            raise ValueError("configuration must be ConfigurationBundle")
        if not isinstance(self.evidence_guard_plan, EvidenceGuardPlan):
            raise ValueError("evidence_guard_plan must be EvidenceGuardPlan")
        object.__setattr__(self, "historical_snapshots", _normalise_tuple(
            self.historical_snapshots, "historical_snapshots",
            _model_item(HistoricalSnapshotExpectation),
            sort_key=lambda item: (item.phase, item.commit),
        ))
        object.__setattr__(self, "historical_blobs", _normalise_tuple(
            self.historical_blobs, "historical_blobs",
            _model_item(HistoricalBlobExpectation),
            sort_key=lambda item: (item.commit, item.relative_path),
        ))
        _require_sha256(self.semantic_sha256, "semantic_sha256")
        payload = {field.name: getattr(self, field.name) for field in fields(self) if field.name != "semantic_sha256"}
        if self.semantic_sha256 != semantic_sha256(payload):
            raise ValueError("execution bundle semantic_sha256 does not match its canonical form")


@dataclass(frozen=True, slots=True)
class CapturedStreamIdentity:
    byte_length: int
    raw_sha256: str
    truncated: bool

    def __post_init__(self) -> None:
        _require_int(self.byte_length, "byte_length")
        _require_sha256(self.raw_sha256, "raw_sha256")
        _require_bool(self.truncated, "truncated")


@dataclass(frozen=True, slots=True)
class CapturedOutputIdentity:
    stdout: CapturedStreamIdentity
    stderr: CapturedStreamIdentity

    def __post_init__(self) -> None:
        if not isinstance(self.stdout, CapturedStreamIdentity) or not isinstance(self.stderr, CapturedStreamIdentity):
            raise ValueError("captured output requires stream identities")


@dataclass(frozen=True, slots=True)
class ChildExecutionResult:
    report: object | None
    process_return_category: str
    captured_output: CapturedOutputIdentity
    completed: bool

    def __post_init__(self) -> None:
        if self.process_return_category not in ("protocol_committed", "protocol_failure"):
            raise ValueError("process_return_category is unsupported")
        if not isinstance(self.captured_output, CapturedOutputIdentity):
            raise ValueError("captured_output must be CapturedOutputIdentity")
        _require_bool(self.completed, "completed")
        if self.process_return_category == "protocol_committed" and self.report is None:
            raise ValueError("protocol_committed requires a report")
        if self.completed and self.process_return_category != "protocol_committed":
            raise ValueError("completed child execution requires a committed protocol")


def _normalise_status(value: object) -> ExecutionStatus:
    return _enum(value, ExecutionStatus, "status")


def _normalise_outcomes(value: object) -> tuple[Mapping[str, FrozenValue], ...]:
    items = _normalise_tuple(value, "outcomes", sort=False)
    outcomes: list[Mapping[str, FrozenValue]] = []
    identifiers: set[str] = set()
    for item in items:
        if not isinstance(item, Mapping):
            raise ValueError("outcomes must contain mappings")
        stable_id = _require_string(item.get("stable_id"), "outcome.stable_id")
        if stable_id in identifiers:
            raise ValueError("outcomes must contain unique stable IDs")
        identifiers.add(stable_id)
        outcomes.append(item)
    return tuple(sorted(outcomes, key=lambda item: item["stable_id"]))


def _outcome_ids(outcomes: tuple[Mapping[str, FrozenValue], ...]) -> tuple[str, ...]:
    return tuple(str(item["stable_id"]) for item in outcomes)


def _failure_count(counts: Mapping[str, object]) -> int:
    return sum(
        int(value)
        for key, value in counts.items()
        if key in {"failed", "failures", "errors", "assertion_failed", "setup_failed"}
    )


@dataclass(frozen=True, slots=True)
class PayloadSummary:
    payload_id: str
    status: ExecutionStatus
    requested_ids: tuple[str, ...]
    outcomes: tuple[FrozenValue, ...]
    counts: FrozenMapping
    conditions: tuple[ObservedCondition, ...]
    captured_output: CapturedOutputIdentity | None
    duration_ns: int
    completed: bool

    def __post_init__(self) -> None:
        _require_string(self.payload_id, "payload_id")
        object.__setattr__(self, "status", _normalise_status(self.status))
        if self.status is ExecutionStatus.OPTIONAL_UNAVAILABLE:
            raise ValueError("optional_unavailable is not a payload status")
        object.__setattr__(self, "requested_ids", _normalise_tuple(self.requested_ids, "requested_ids", _string_item))
        object.__setattr__(self, "outcomes", _normalise_outcomes(self.outcomes))
        object.__setattr__(self, "counts", _freeze_count_mapping(self.counts, "counts"))
        object.__setattr__(self, "conditions", _normalise_tuple(self.conditions, "conditions", _model_item(ObservedCondition)))
        if self.captured_output is not None and not isinstance(self.captured_output, CapturedOutputIdentity):
            raise ValueError("captured_output must be CapturedOutputIdentity or null")
        _require_int(self.duration_ns, "duration_ns")
        _require_bool(self.completed, "completed")
        if self.status is ExecutionStatus.NOT_RUN_SAFETY_STOP:
            if self.completed or self.duration_ns or self.requested_ids or self.outcomes or self.counts or self.captured_output is not None or not self.conditions:
                raise ValueError("not_run_safety_stop must be an empty unstarted result with a condition")
        if self.status in (ExecutionStatus.PASSED, ExecutionStatus.TEST_FAILURE):
            if (
                not self.completed
                or self.requested_ids != _outcome_ids(self.outcomes)
                or self.captured_output is None
            ):
                raise ValueError("completed test results require exact outcomes and captured output")
            failures = _failure_count(self.counts)
            if (self.status is ExecutionStatus.PASSED and failures) or (self.status is ExecutionStatus.TEST_FAILURE and failures == 0):
                raise ValueError("test status disagrees with failure counts")
        if self.status in (ExecutionStatus.CONFIGURATION_FAILURE, ExecutionStatus.INTEGRITY_FAILURE, ExecutionStatus.PHASE_FAILURE):
            if self.completed or self.outcomes:
                raise ValueError("configuration/integrity/phase failures discard outcomes")
        if self.status in (ExecutionStatus.RUNTIME_SAFETY_STOP, ExecutionStatus.CANCELLED) and self.completed:
            raise ValueError("active safety stops are incomplete")
        if self.status in (ExecutionStatus.RUNTIME_SAFETY_STOP, ExecutionStatus.CANCELLED):
            if self.captured_output is None:
                raise ValueError("active safety stops require parent-owned captured output")
            outcome_ids = _outcome_ids(self.outcomes)
            if outcome_ids != self.requested_ids[:len(outcome_ids)]:
                raise ValueError("active safety-stop outcomes must be a bounded requested prefix")


@dataclass(frozen=True, slots=True)
class WorkerSummary:
    profile: str
    interpreter_binding: InterpreterBinding
    status: ExecutionStatus
    summary: ProfileSummary | None
    conditions: tuple[ObservedCondition, ...]
    duration_ns: int
    completed: bool

    def __post_init__(self) -> None:
        _require_string(self.profile, "profile")
        if not isinstance(self.interpreter_binding, InterpreterBinding):
            raise ValueError("interpreter_binding must be InterpreterBinding")
        object.__setattr__(self, "status", _normalise_status(self.status))
        if self.summary is not None and not isinstance(self.summary, ProfileSummary):
            raise ValueError("summary must be ProfileSummary or null")
        object.__setattr__(self, "conditions", _normalise_tuple(self.conditions, "conditions", _model_item(ObservedCondition)))
        _require_int(self.duration_ns, "duration_ns")
        _require_bool(self.completed, "completed")
        if self.status is ExecutionStatus.NOT_RUN_SAFETY_STOP:
            if self.completed or self.duration_ns or self.summary is not None or not self.conditions:
                raise ValueError("not_run_safety_stop workers must be empty and carry a trigger")
        if self.status is ExecutionStatus.OPTIONAL_UNAVAILABLE and (not self.completed or self.summary is not None or len(self.conditions) != 1 or self.conditions[0].category != "optional_unavailable"):
            raise ValueError("optional_unavailable worker requires one optional condition and no summary")
        if self.status in (ExecutionStatus.PASSED, ExecutionStatus.TEST_FAILURE):
            if not self.completed or self.summary is None or not self.summary.completed:
                raise ValueError("completed worker statuses require a direct profile summary")
            failures = _failure_count(self.summary.counts)
            if (self.status is ExecutionStatus.PASSED and failures) or (self.status is ExecutionStatus.TEST_FAILURE and failures == 0):
                raise ValueError("worker status disagrees with nested failure counts")
        if self.status in (ExecutionStatus.RUNTIME_SAFETY_STOP, ExecutionStatus.CANCELLED) and self.completed:
            raise ValueError("active worker safety stops are incomplete")
        if self.status in (ExecutionStatus.CONFIGURATION_FAILURE, ExecutionStatus.INTEGRITY_FAILURE, ExecutionStatus.PHASE_FAILURE) and (self.completed or self.summary is not None):
            raise ValueError("worker configuration/integrity/phase failures discard summaries")
        if self.summary is not None:
            if self.summary.profile != self.profile:
                raise ValueError("worker and nested profile identities must match")
            if self.summary.interpreter_bindings != (self.interpreter_binding,):
                raise ValueError("worker and nested interpreter bindings must match")
            if self.status in (ExecutionStatus.RUNTIME_SAFETY_STOP, ExecutionStatus.CANCELLED) and self.summary.completed:
                raise ValueError("active worker summaries must remain incomplete")


@dataclass(frozen=True, slots=True)
class ProfileSummary:
    profile: str
    profile_definition_sha256: str
    inventory_sha256: str
    spec_capabilities_sha256: str
    capability_bindings_sha256: str
    interpreter_bindings: tuple[InterpreterBinding, ...]
    payload_summaries: tuple[PayloadSummary, ...]
    worker_summaries: tuple[WorkerSummary, ...]
    requested_ids: tuple[str, ...]
    outcomes: tuple[FrozenValue, ...]
    counts: FrozenMapping
    conditions: tuple[ObservedCondition, ...]
    evidence_guard_sha256: str
    evidence_guard: EvidenceGuardSummary
    duration_ns: int
    completed: bool

    def __post_init__(self) -> None:
        _require_string(self.profile, "profile")
        for name in ("profile_definition_sha256", "inventory_sha256", "spec_capabilities_sha256", "capability_bindings_sha256", "evidence_guard_sha256"):
            _require_sha256(getattr(self, name), name)
        object.__setattr__(self, "interpreter_bindings", _normalise_tuple(
            self.interpreter_bindings, "interpreter_bindings", _model_item(InterpreterBinding),
            sort_key=lambda item: item.slot_name,
        ))
        if len({item.slot_name for item in self.interpreter_bindings}) != len(self.interpreter_bindings):
            raise ValueError("interpreter bindings must be unique by slot_name")
        object.__setattr__(self, "payload_summaries", _normalise_tuple(
            self.payload_summaries, "payload_summaries", _model_item(PayloadSummary),
            sort_key=lambda item: item.payload_id,
        ))
        object.__setattr__(self, "worker_summaries", _normalise_tuple(
            self.worker_summaries, "worker_summaries", _model_item(WorkerSummary),
            sort_key=lambda item: (item.profile, item.interpreter_binding.slot_name),
        ))
        object.__setattr__(self, "requested_ids", _normalise_tuple(self.requested_ids, "requested_ids", _string_item))
        object.__setattr__(self, "outcomes", _normalise_outcomes(self.outcomes))
        object.__setattr__(self, "counts", _freeze_count_mapping(self.counts, "counts"))
        object.__setattr__(self, "conditions", _normalise_tuple(self.conditions, "conditions", _model_item(ObservedCondition)))
        if not isinstance(self.evidence_guard, EvidenceGuardSummary):
            raise ValueError("evidence_guard must be EvidenceGuardSummary")
        _require_int(self.duration_ns, "duration_ns")
        _require_bool(self.completed, "completed")
        if self.completed and self.evidence_guard.status == "not_measured":
            raise ValueError("completed profiles require measured evidence")
        if self.completed and self.requested_ids != _outcome_ids(self.outcomes):
            raise ValueError("completed profile outcomes must exactly match requested IDs")
        if self.completed and not any(item.affects_exit for item in self.conditions) and _failure_count(self.counts) == 0 and self.evidence_guard.status != "unchanged":
            raise ValueError("successful completed profiles require unchanged evidence")
        if self.profile == "full":
            if self.completed and not self.worker_summaries:
                raise ValueError("completed full profiles require worker summaries")
            worker_bindings = tuple(worker.interpreter_binding for worker in self.worker_summaries)
            if set(worker_bindings) != set(self.interpreter_bindings) or len(worker_bindings) != len(set(worker_bindings)):
                raise ValueError("full bindings must equal the unique worker binding union")
            if self.completed and any(
                not worker.completed
                or worker.status not in (
                    ExecutionStatus.PASSED, ExecutionStatus.TEST_FAILURE,
                    ExecutionStatus.OPTIONAL_UNAVAILABLE,
                )
                for worker in self.worker_summaries
            ):
                raise ValueError("completed full profiles require terminal worker rows")
        else:
            if self.worker_summaries:
                raise ValueError("direct profiles cannot contain worker summaries")
            if not self.interpreter_bindings:
                if self.completed or self.payload_summaries:
                    raise ValueError("pre-resolution failures cannot contain payload summaries")
            elif len(self.interpreter_bindings) != 1:
                raise ValueError("resolved direct profiles require exactly one interpreter binding")
            elif not self.payload_summaries:
                raise ValueError("resolved direct profiles require payload summaries")
            if self.completed and any(
                not payload.completed
                or payload.status not in (
                    ExecutionStatus.PASSED, ExecutionStatus.TEST_FAILURE,
                )
                for payload in self.payload_summaries
            ):
                raise ValueError("completed direct profiles require terminal payload rows")
            if self.completed:
                child_requested = tuple(sorted(
                    stable_id
                    for payload in self.payload_summaries
                    for stable_id in payload.requested_ids
                ))
                if len(child_requested) != len(set(child_requested)) or self.requested_ids != child_requested:
                    raise ValueError("direct requested IDs must equal the payload union")
        if self.completed:
            child_failed = any(
                payload.status is ExecutionStatus.TEST_FAILURE
                for payload in self.payload_summaries
            ) or any(
                worker.status is ExecutionStatus.TEST_FAILURE
                for worker in self.worker_summaries
            )
            if child_failed != (_failure_count(self.counts) > 0):
                raise ValueError("profile failure counts must agree with child statuses")


@dataclass(frozen=True, slots=True)
class RunSummary:
    run_id: str
    requested_profile: str
    profile_summaries: tuple[ProfileSummary, ...]
    conditions: tuple[ObservedCondition, ...]
    exit_code: ExitCode
    duration_ns: int
    completed: bool

    def __post_init__(self) -> None:
        _require_string(self.run_id, "run_id")
        _require_string(self.requested_profile, "requested_profile")
        object.__setattr__(self, "profile_summaries", _normalise_tuple(
            self.profile_summaries, "profile_summaries", _model_item(ProfileSummary),
            sort_key=lambda item: item.profile,
        ))
        object.__setattr__(self, "conditions", _normalise_tuple(self.conditions, "conditions", _model_item(ObservedCondition)))
        object.__setattr__(self, "exit_code", _enum(self.exit_code, ExitCode, "exit_code"))
        _require_int(self.duration_ns, "duration_ns")
        _require_bool(self.completed, "completed")
        precedence = (
            ("integrity", ExitCode.INTEGRITY),
            ("configuration", ExitCode.CONFIGURATION),
            ("phase", ExitCode.PHASE),
            ("runtime", ExitCode.RUNTIME),
            ("test_failure", ExitCode.TEST_FAILURE),
            ("optional_unavailable", ExitCode.OPTIONAL_UNAVAILABLE),
        )
        categories = {
            condition.category for condition in self.conditions if condition.affects_exit
        }
        all_categories = {condition.category for condition in self.conditions}
        run_condition_keys = {_sort_key(condition) for condition in self.conditions}
        nested_conditions: list[ObservedCondition] = []
        required_categories: set[str] = set()

        def inspect_profile(summary: ProfileSummary) -> None:
            nested_conditions.extend(summary.conditions)
            nested_conditions.extend(summary.evidence_guard.conditions)
            if summary.evidence_guard.status == "changed":
                required_categories.add("integrity")
            if _failure_count(summary.counts):
                required_categories.add("test_failure")
            for payload in summary.payload_summaries:
                nested_conditions.extend(payload.conditions)
                category = {
                    ExecutionStatus.TEST_FAILURE: "test_failure",
                    ExecutionStatus.CONFIGURATION_FAILURE: "configuration",
                    ExecutionStatus.INTEGRITY_FAILURE: "integrity",
                    ExecutionStatus.PHASE_FAILURE: "phase",
                    ExecutionStatus.RUNTIME_SAFETY_STOP: "runtime",
                    ExecutionStatus.CANCELLED: "runtime",
                    ExecutionStatus.NOT_RUN_SAFETY_STOP: "runtime",
                }.get(payload.status)
                if category is not None:
                    required_categories.add(category)
            for worker in summary.worker_summaries:
                nested_conditions.extend(worker.conditions)
                category = {
                    ExecutionStatus.TEST_FAILURE: "test_failure",
                    ExecutionStatus.CONFIGURATION_FAILURE: "configuration",
                    ExecutionStatus.INTEGRITY_FAILURE: "integrity",
                    ExecutionStatus.PHASE_FAILURE: "phase",
                    ExecutionStatus.RUNTIME_SAFETY_STOP: "runtime",
                    ExecutionStatus.CANCELLED: "runtime",
                    ExecutionStatus.NOT_RUN_SAFETY_STOP: "runtime",
                    ExecutionStatus.OPTIONAL_UNAVAILABLE: "optional_unavailable",
                }.get(worker.status)
                if category is not None:
                    required_categories.add(category)
                if worker.summary is not None:
                    inspect_profile(worker.summary)

        for summary in self.profile_summaries:
            inspect_profile(summary)
        if any(_sort_key(condition) not in run_condition_keys for condition in nested_conditions):
            raise ValueError("run conditions must retain every nested observed condition")
        if "optional_unavailable" in required_categories and "optional_unavailable" not in all_categories:
            raise ValueError("optional unavailability requires a retained run condition")
        exit_required = required_categories - {"optional_unavailable"}
        if not exit_required.issubset(categories):
            raise ValueError("run conditions must cover every nested terminal status")
        expected_exit = next(
            (code for category, code in precedence if category in categories),
            ExitCode.SUCCESS,
        )
        if self.exit_code is not expected_exit:
            raise ValueError("run exit_code disagrees with observed conditions")
        if self.completed and any(not summary.completed for summary in self.profile_summaries):
            raise ValueError("completed runs require completed profile summaries")
        if self.exit_code is ExitCode.SUCCESS and not self.completed:
            raise ValueError("successful runs must be complete")


@dataclass(frozen=True, slots=True)
class ConfigurationBundle:
    repository_root: Path
    profiles_path: Path
    inventory_path: Path
    baseline_commit: str
    sealed_current_files_manifest: str
    sealed_current_absences_manifest: str
    historical_blobs_manifest: str
    retained_v7_manifest: str
    profile_definition_sha256: str
    inventory_sha256: str
    spec_capabilities_sha256: str
    capability_bindings_sha256: str
    inventory_entries: tuple[InventoryEntry, ...]
    interpreter_slots: Mapping[str, InterpreterSlot]
    profiles: Mapping[str, ProfilePlan]
    payloads: Mapping[str, PayloadPlan]
    historical_cases: Mapping[str, HistoricalCase]
    overlays: Mapping[str, OverlaySpec]
    subprocess_capabilities: Mapping[str, SubprocessCapability]
    call_capabilities: Mapping[str, CallCapability]
    capability_bindings: tuple[CapabilityBinding, ...]
    stabilization_test_files: tuple[str, ...]

    def __post_init__(self) -> None:
        for name in ("repository_root", "profiles_path", "inventory_path"):
            value = getattr(self, name)
            if not isinstance(value, Path) or not value.is_absolute():
                raise ValueError(f"{name} must be an absolute Path")
        _require_git_oid(self.baseline_commit, "baseline_commit")
        for name in ("sealed_current_files_manifest", "sealed_current_absences_manifest", "historical_blobs_manifest", "retained_v7_manifest"):
            object.__setattr__(self, name, _normalise_relative_path(getattr(self, name), name))
        for name in ("profile_definition_sha256", "inventory_sha256", "spec_capabilities_sha256", "capability_bindings_sha256"):
            _require_sha256(getattr(self, name), name)
        object.__setattr__(self, "inventory_entries", _normalise_tuple(
            self.inventory_entries, "inventory_entries", _model_item(InventoryEntry),
            sort_key=lambda item: item.selector.stable_id,
        ))
        mappings = (
            ("interpreter_slots", InterpreterSlot), ("profiles", ProfilePlan), ("payloads", PayloadPlan),
            ("historical_cases", HistoricalCase), ("overlays", OverlaySpec),
            ("subprocess_capabilities", SubprocessCapability), ("call_capabilities", CallCapability),
        )
        for name, expected_type in mappings:
            value = getattr(self, name)
            if not isinstance(value, Mapping) or any(type(key) is not str or not isinstance(item, expected_type) for key, item in value.items()):
                raise ValueError(f"{name} must map strings to {expected_type.__name__}")
            object.__setattr__(self, name, MappingProxyType(dict(sorted(value.items()))))
        object.__setattr__(self, "capability_bindings", _normalise_capability_bindings(self.capability_bindings))
        object.__setattr__(self, "stabilization_test_files", _normalise_tuple(self.stabilization_test_files, "stabilization_test_files", _path_item))
