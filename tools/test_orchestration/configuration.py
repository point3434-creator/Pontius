"""Strict profile/inventory parsing and pure orchestration selection."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import replace
import json
from pathlib import Path, PurePosixPath, PureWindowsPath
import tomllib
from typing import Any

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
    candidate = (root / PurePosixPath(relative)).resolve(strict=False)
    try:
        candidate.relative_to(root)
    except ValueError as error:
        raise ValueError(f"{name} escapes repository_root") from error
    return relative, candidate


def _read_bounded(path: Path, *, root: Path, label: str) -> bytes:
    if not isinstance(path, Path) or not path.is_absolute():
        raise ValueError(f"{label} path must be absolute")
    resolved = path.resolve(strict=True)
    try:
        resolved.relative_to(root)
    except ValueError as error:
        raise ValueError(f"{label} path must be below repository_root") from error
    if not resolved.is_file() or resolved.is_symlink():
        raise ValueError(f"{label} path must be a regular non-link file")
    size = resolved.stat().st_size
    if size > MAX_CONFIGURATION_BYTES:
        raise ValueError(f"{label} exceeds the configuration size bound")
    raw = resolved.read_bytes()
    if len(raw) != size:
        raise ValueError(f"{label} changed while being read")
    return raw


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
    table = _exact_keys(
        value, required={"kind"}, optional={"applicable_platforms", "skip_safe_reason_code"},
        label="inventory expectation",
    )
    return InventoryExpectation(
        _exact_string(table["kind"], "expectation.kind"),
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
        data, required={"schema_version", "baseline_commit", "entries"},
        label="inventory root",
    )
    if root["schema_version"] != INVENTORY_SCHEMA:
        raise ValueError("inventory schema_version is unsupported")
    baseline = _require_lower_hex(root["baseline_commit"], "inventory.baseline_commit", 40)
    entries: list[InventoryEntry] = []
    assigned_rows: list[tuple[ResolvedInventoryItem, str, str]] = []
    seen: set[str] = set()
    for index, raw_entry in enumerate(_exact_list(root["entries"], "inventory.entries")):
        entry = _exact_keys(
            raw_entry,
            required={"stable_id", "relative_path", "case_name", "method_name"},
            optional={"assignment", "exclusion"},
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
    entries.sort(key=lambda item: item.selector.stable_id)
    assigned_rows.sort(key=lambda row: row[0].selector.stable_id)
    return baseline, entries, assigned_rows, root


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


def _fixture_union(payloads: Iterable[PayloadPlan]) -> tuple[FixtureSpec, ...]:
    by_path: dict[str, FixtureSpec] = {}
    for payload in payloads:
        for fixture in payload.fixture_specs:
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


def _parse_item_expectation(value: object, label: str) -> HistoricalItemExpectation:
    table = _exact_keys(
        value,
        required={"item_id", "outcome"},
        optional={"phase", "exception_type", "safe_reason_code", "body_entered", "capability_counters"},
        label=label,
    )
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
        _exact_string(table["outcome"], f"{label}.outcome"),
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
            "argv", "argv_template", "dynamic_program_sha256", "cwd_class",
            "environment_additions", "environment_removals", "timeout_ns",
            "expected_return_category", "read_roots", "write_roots",
            "fixed_descendant_permission",
        },
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
        _optional_string(table["dynamic_program_sha256"], f"{label}.dynamic_program_sha256"),
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
    for payload in payloads.values():
        if set(payload.allowed_interpreter_slots) - set(slots):
            raise ValueError("payload references an unknown interpreter slot")
    for case in cases.values():
        if set(case.payload_ids) - set(payloads) or set(case.overlay_ids) - set(overlays):
            raise ValueError("historical case contains an unknown payload or overlay")
    known_items = {item.selector.stable_id for item, _, _ in inventory_rows}
    for payload in payloads.values():
        known_items.update(payload.probe_ids)
        known_items.update(fixture.fixture_id for fixture in payload.lifecycle_fixtures)
    for binding in bindings:
        definitions: Mapping[str, object]
        if binding.capability_kind == "subprocess":
            definitions = subprocess_capabilities
        else:
            definitions = call_capabilities
        if binding.capability_id not in definitions:
            raise ValueError("capability binding references an unknown capability")
        if binding.item_id not in known_items:
            raise ValueError("capability binding references an unknown item")


def load_configuration(
    profiles_path: Path,
    inventory_path: Path,
    *,
    repository_root: Path,
) -> ConfigurationBundle:
    try:
        if not isinstance(repository_root, Path) or not repository_root.is_absolute():
            raise ValueError("repository_root must be an absolute Path")
        root = repository_root.resolve(strict=True)
        if not root.is_dir() or root.is_symlink():
            raise ValueError("repository_root must be a regular directory root")
        profile_raw = _read_bounded(profiles_path, root=root, label="profiles")
        inventory_raw = _read_bounded(inventory_path, root=root, label="inventory")
        profile_data = _parse_toml(profile_raw, profiles_path)
        inventory_data = _parse_json(inventory_raw, inventory_path)
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
        if expected_inventory_path != inventory_path.resolve(strict=True):
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
        _validate_references(
            slots=slots, profiles=profiles, payloads=payloads, cases=cases, overlays=overlays,
            subprocess_capabilities=subprocess_capabilities, call_capabilities=call_capabilities,
            bindings=bindings, inventory_rows=inventory_rows,
        )
        stabilization_files = [
            _relative_path(item, "stabilization_test_files")
            for item in _exact_list(profile_root["stabilization_test_files"], "stabilization_test_files")
        ]
        spec_digest = _require_lower_hex(profile_root["spec_capabilities_sha256"], "spec_capabilities_sha256", 64)
        binding_digest = _require_lower_hex(profile_root["capability_bindings_sha256"], "capability_bindings_sha256", 64)
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
        normalized_inventory = {
            "schema_version": INVENTORY_SCHEMA,
            "baseline_commit": inventory_baseline,
            "entries": tuple(inventory_entries),
        }
        return ConfigurationBundle(
            root,
            profiles_path.resolve(strict=True),
            inventory_path.resolve(strict=True),
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
    if payload_id is not None:
        if payload_id not in profile.payload_ids:
            raise _configuration_error(
                "payload_unknown", "payload does not belong to the selected profile",
                profile=name, payload_id=payload_id,
            )
        payload = bundle.payloads[payload_id]
        return replace(
            profile,
            payload_ids=(payload_id,),
            historical_case_ids=(),
            fixture_specs=payload.fixture_specs,
        )
    if historical_case is not None:
        if historical_case not in profile.historical_case_ids:
            raise _configuration_error(
                "historical_case_unknown", "historical case does not belong to the selected profile",
                profile=name, historical_case=historical_case,
            )
        case = bundle.historical_cases[historical_case]
        payloads = tuple(bundle.payloads[payload] for payload in case.payload_ids)
        return replace(
            profile,
            payload_ids=case.payload_ids,
            historical_case_ids=(historical_case,),
            fixture_specs=_fixture_union(payloads),
        )
    return profile


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
