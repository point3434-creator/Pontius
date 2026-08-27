"""Strict, pure-byte parsers for the evidence manifest contracts."""

from __future__ import annotations

from collections.abc import Mapping
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath, PureWindowsPath
import tomllib

from .errors import EvidenceConfigurationError, EvidenceIntegrityError
from .model import (
    EvidenceFileIdentity,
    HistoricalBlobIdentity,
    HistoricalBlobsManifest,
    HistoricalSnapshot,
    LoadedRetainedV7Manifest,
    RetainedV7Manifest,
    SealedCurrentAbsenceEntry,
    SealedCurrentAbsencesManifest,
    SealedCurrentFileEntry,
    SealedCurrentFilesManifest,
)


_FILE_KEYS = frozenset({"relative_path", "byte_length", "raw_sha256", "role", "governing_decision", "owner"})
_ABSENCE_KEYS = frozenset({"relative_path", "role", "governing_decision", "owner"})
_SNAPSHOT_KEYS = frozenset({"phase", "commit", "root_tree_oid", "governing_decision"})
_BLOB_KEYS = frozenset({"commit", "relative_path", "git_blob_oid", "raw_sha256", "role", "phase", "governing_decision"})
_IDENTITY_KEYS = frozenset({"relative_path", "byte_length", "raw_sha256", "role"})
_CURRENT_FILES_KEYS = frozenset({"schema_version", "baseline_commit", "entry_count", "files"})
_CURRENT_ABSENCES_KEYS = frozenset({"schema_version", "baseline_commit", "entry_count", "absences"})
_HISTORICAL_KEYS = frozenset({
    "schema_version", "baseline_commit", "snapshot_count", "entry_count", "entries_sha256", "approved_seed_sha256", "snapshots", "blobs",
})
_RETAINED_KEYS = frozenset({
    "schema_version", "source_seal_commit", "authorization_commit", "historical_reader_commit", "journal_protocol_sha256", "campaign_sha256",
    "record_count", "observation_count", "calibration_cell_count", "warmup_cell_count", "measured_labelled_partial_cell_count", "terminal",
    "journal_complete", "scientific_campaign_complete", "scientific_call_count", "authoritative_measured_call_count", "passed",
    "laboratory_elapsed_ns", "laboratory_wall_ns", "outside_laboratory_elapsed_ns", "outside_laboratory_wall_ns", "public_elapsed_ns", "public_wall_ns",
    "fit_projection_present", "production_base_classification", "candidate_selection_present", "topology_selection_present",
    "arithmetic_schedule_selection_present", "truncation_authorized", "historical_blobs_manifest_path", "absent_launch_paths",
    "expected_null_claim_paths", "result", "attempt", "consumed_launch",
})


def canonical_semantic_bytes(value: object) -> bytes:
    normalized = _normalize_semantic_value(value, path="$")
    return json.dumps(
        normalized,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")


def semantic_sha256(value: object) -> str:
    return sha256(canonical_semantic_bytes(value)).hexdigest()


def _normalize_semantic_value(value: object, *, path: str) -> object:
    if value is None or type(value) is bool or type(value) is int or type(value) is str:
        return value
    if isinstance(value, (list, tuple)):
        return [_normalize_semantic_value(item, path=f"{path}[{index}]") for index, item in enumerate(value)]
    if isinstance(value, Mapping):
        normalized: dict[str, object] = {}
        for key in sorted(value):
            if type(key) is not str:
                raise TypeError(f"semantic mapping key at {path} must be a string")
            normalized[key] = _normalize_semantic_value(value[key], path=f"{path}.{key}")
        return normalized
    raise TypeError(f"unsupported semantic value at {path}: {type(value).__name__}")


def _source_label(source_path: Path, repository_root: Path) -> str:
    if not isinstance(source_path, Path) or not isinstance(repository_root, Path):
        raise TypeError("source_path and repository_root must be Path values")
    try:
        label = source_path.relative_to(repository_root).as_posix()
    except ValueError as error:
        raise EvidenceConfigurationError(
            "manifest_source_path_invalid", "manifest source path is outside the repository root",
            context={"path": source_path.as_posix(), "repository_root": repository_root.as_posix()},
        ) from error
    if label in ("", ".") or PureWindowsPath(label).drive or PurePosixPath(label).is_absolute() or any(part == ".." for part in PurePosixPath(label).parts):
        raise EvidenceConfigurationError(
            "manifest_source_path_invalid", "manifest source path is not repository-relative",
            context={"path": source_path.as_posix(), "repository_root": repository_root.as_posix()},
        )
    return label


def _configuration_error(code: str, message: str, *, source_label: str, table: str, **context: object) -> EvidenceConfigurationError:
    return EvidenceConfigurationError(code, message, context={"path": source_label, "table": table, **context})


def _parse_toml(raw: bytes, *, source_path: Path, repository_root: Path) -> tuple[dict[str, object], str]:
    source_label = _source_label(source_path, repository_root)
    if type(raw) is not bytes:
        raise _configuration_error("manifest_bytes_invalid", "manifest must be immutable bytes", source_label=source_label, table="document")
    try:
        parsed = tomllib.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as error:
        raise EvidenceConfigurationError(
            "manifest_toml_invalid", "manifest is not valid TOML", context={"path": source_path.as_posix()},
        ) from error
    if not isinstance(parsed, dict):
        raise _configuration_error("manifest_schema_invalid", "manifest root must be a table", source_label=source_label, table="document")
    return parsed, source_label


def _exact_keys(table: object, expected: frozenset[str], *, source_label: str, table_name: str) -> dict[str, object]:
    if not isinstance(table, dict):
        raise _configuration_error("manifest_schema_invalid", "manifest table is not a TOML table", source_label=source_label, table=table_name)
    actual = set(table)
    if actual != expected:
        raise _configuration_error(
            "manifest_schema_invalid", "manifest table keys do not match its schema", source_label=source_label, table=table_name,
            missing=tuple(sorted(expected - actual)), extra=tuple(sorted(actual - expected)),
        )
    return table


def _string(value: object, *, source_label: str, table: str, field: str) -> str:
    if type(value) is not str or not value:
        raise _configuration_error("manifest_schema_invalid", "manifest field must be a non-empty string", source_label=source_label, table=table, field=field)
    return value


def _integer(value: object, *, source_label: str, table: str, field: str) -> int:
    if type(value) is not int or value < 0:
        raise _configuration_error("manifest_schema_invalid", "manifest field must be a non-negative integer", source_label=source_label, table=table, field=field)
    return value


def _boolean(value: object, *, source_label: str, table: str, field: str) -> bool:
    if type(value) is not bool:
        raise _configuration_error("manifest_schema_invalid", "manifest field must be a boolean", source_label=source_label, table=table, field=field)
    return value


def _digest(value: object, *, source_label: str, table: str, field: str) -> str:
    text = _string(value, source_label=source_label, table=table, field=field)
    if len(text) != 64 or any(character not in "0123456789abcdef" for character in text):
        raise _configuration_error("manifest_schema_invalid", "manifest field must be a lowercase SHA-256 digest", source_label=source_label, table=table, field=field)
    return text


def _commit(value: object, *, source_label: str, table: str, field: str) -> str:
    text = _string(value, source_label=source_label, table=table, field=field)
    if len(text) != 40 or any(character not in "0123456789abcdef" for character in text):
        raise _configuration_error("manifest_schema_invalid", "manifest field must be a lowercase Git object identity", source_label=source_label, table=table, field=field)
    return text


def _relative_path(value: object, *, source_label: str, table: str, field: str) -> str:
    text = _string(value, source_label=source_label, table=table, field=field)
    if PureWindowsPath(text).drive or text.startswith(("/", "\\")):
        raise _configuration_error("manifest_schema_invalid", "manifest path must be repository-relative", source_label=source_label, table=table, field=field)
    candidate = PurePosixPath(text.replace("\\", "/"))
    if candidate.is_absolute() or any(part == ".." for part in candidate.parts) or candidate.as_posix() in ("", "."):
        raise _configuration_error("manifest_schema_invalid", "manifest path must not escape the repository", source_label=source_label, table=table, field=field)
    return candidate.as_posix()


def _string_list(value: object, *, source_label: str, table: str, field: str, paths: bool) -> tuple[str, ...]:
    if type(value) is not list:
        raise _configuration_error("manifest_schema_invalid", "manifest field must be an array", source_label=source_label, table=table, field=field)
    if paths:
        return tuple(_relative_path(item, source_label=source_label, table=table, field=field) for item in value)
    return tuple(_string(item, source_label=source_label, table=table, field=field) for item in value)


def _table_array(value: object, *, source_label: str, table: str) -> list[dict[str, object]]:
    if type(value) is not list:
        raise _configuration_error("manifest_schema_invalid", "manifest field must be an array of tables", source_label=source_label, table=table)
    return [_exact_keys(item, _FILE_KEYS if table == "files" else _ABSENCE_KEYS if table == "absences" else _SNAPSHOT_KEYS if table == "snapshots" else _BLOB_KEYS, source_label=source_label, table_name=f"{table}[{index}]") for index, item in enumerate(value)]


def _file_entry(table: dict[str, object], *, source_label: str) -> SealedCurrentFileEntry:
    name = "files entry"
    return SealedCurrentFileEntry(
        _relative_path(table["relative_path"], source_label=source_label, table=name, field="relative_path"),
        _integer(table["byte_length"], source_label=source_label, table=name, field="byte_length"),
        _digest(table["raw_sha256"], source_label=source_label, table=name, field="raw_sha256"),
        _string(table["role"], source_label=source_label, table=name, field="role"),
        _string(table["governing_decision"], source_label=source_label, table=name, field="governing_decision"),
        _string(table["owner"], source_label=source_label, table=name, field="owner"),
    )


def _absence_entry(table: dict[str, object], *, source_label: str) -> SealedCurrentAbsenceEntry:
    name = "absences entry"
    return SealedCurrentAbsenceEntry(
        _relative_path(table["relative_path"], source_label=source_label, table=name, field="relative_path"),
        _string(table["role"], source_label=source_label, table=name, field="role"),
        _string(table["governing_decision"], source_label=source_label, table=name, field="governing_decision"),
        _string(table["owner"], source_label=source_label, table=name, field="owner"),
    )


def parse_sealed_current_files_manifest(raw: bytes, *, source_path: Path, repository_root: Path) -> SealedCurrentFilesManifest:
    document, label = _parse_toml(raw, source_path=source_path, repository_root=repository_root)
    root = _exact_keys(document, _CURRENT_FILES_KEYS, source_label=label, table_name="document")
    files = tuple(_file_entry(table, source_label=label) for table in _table_array(root["files"], source_label=label, table="files"))
    try:
        return SealedCurrentFilesManifest(
            _string(root["schema_version"], source_label=label, table="document", field="schema_version"),
            _commit(root["baseline_commit"], source_label=label, table="document", field="baseline_commit"),
            _integer(root["entry_count"], source_label=label, table="document", field="entry_count"), files,
        )
    except ValueError as error:
        raise _configuration_error("manifest_schema_invalid", "manifest values violate their schema", source_label=label, table="document") from error


def parse_sealed_current_absences_manifest(raw: bytes, *, source_path: Path, repository_root: Path) -> SealedCurrentAbsencesManifest:
    document, label = _parse_toml(raw, source_path=source_path, repository_root=repository_root)
    root = _exact_keys(document, _CURRENT_ABSENCES_KEYS, source_label=label, table_name="document")
    absences = tuple(_absence_entry(table, source_label=label) for table in _table_array(root["absences"], source_label=label, table="absences"))
    try:
        return SealedCurrentAbsencesManifest(
            _string(root["schema_version"], source_label=label, table="document", field="schema_version"),
            _commit(root["baseline_commit"], source_label=label, table="document", field="baseline_commit"),
            _integer(root["entry_count"], source_label=label, table="document", field="entry_count"), absences,
        )
    except ValueError as error:
        raise _configuration_error("manifest_schema_invalid", "manifest values violate their schema", source_label=label, table="document") from error


def _blob_record(blob: HistoricalBlobIdentity) -> dict[str, object]:
    return {
        "commit": blob.commit, "relative_path": blob.relative_path, "git_blob_oid": blob.git_blob_oid,
        "raw_sha256": blob.raw_sha256, "role": blob.role, "phase": blob.phase,
        "governing_decision": blob.governing_decision,
    }


def parse_historical_blobs_manifest(raw: bytes, *, source_path: Path, repository_root: Path) -> HistoricalBlobsManifest:
    document, label = _parse_toml(raw, source_path=source_path, repository_root=repository_root)
    root = _exact_keys(document, _HISTORICAL_KEYS, source_label=label, table_name="document")
    snapshots = tuple(sorted((HistoricalSnapshot(
        _string(table["phase"], source_label=label, table="snapshots entry", field="phase"),
        _commit(table["commit"], source_label=label, table="snapshots entry", field="commit"),
        _commit(table["root_tree_oid"], source_label=label, table="snapshots entry", field="root_tree_oid"),
        _string(table["governing_decision"], source_label=label, table="snapshots entry", field="governing_decision"),
    ) for table in _table_array(root["snapshots"], source_label=label, table="snapshots")), key=lambda item: (item.commit, item.phase)))
    blobs = tuple(sorted((HistoricalBlobIdentity(
        _commit(table["commit"], source_label=label, table="blobs entry", field="commit"),
        _relative_path(table["relative_path"], source_label=label, table="blobs entry", field="relative_path"),
        _commit(table["git_blob_oid"], source_label=label, table="blobs entry", field="git_blob_oid"),
        _digest(table["raw_sha256"], source_label=label, table="blobs entry", field="raw_sha256"),
        _string(table["role"], source_label=label, table="blobs entry", field="role"),
        _string(table["phase"], source_label=label, table="blobs entry", field="phase"),
        _string(table["governing_decision"], source_label=label, table="blobs entry", field="governing_decision"),
    ) for table in _table_array(root["blobs"], source_label=label, table="blobs")), key=lambda item: (item.commit, item.relative_path)))
    if len({(blob.commit, blob.relative_path) for blob in blobs}) != len(blobs):
        raise EvidenceIntegrityError("historical_blob_identity_duplicate", "historical blob identities must be unique", context={"path": label})
    claimed_digest = _digest(root["entries_sha256"], source_label=label, table="document", field="entries_sha256")
    actual_digest = semantic_sha256([_blob_record(blob) for blob in blobs])
    if claimed_digest != actual_digest:
        raise EvidenceIntegrityError("historical_entries_sha256_mismatch", "historical blob records do not match their claimed digest", context={"path": label, "expected": claimed_digest, "actual": actual_digest})
    try:
        return HistoricalBlobsManifest(
            _string(root["schema_version"], source_label=label, table="document", field="schema_version"),
            _commit(root["baseline_commit"], source_label=label, table="document", field="baseline_commit"),
            _integer(root["snapshot_count"], source_label=label, table="document", field="snapshot_count"),
            _integer(root["entry_count"], source_label=label, table="document", field="entry_count"), claimed_digest,
            _digest(root["approved_seed_sha256"], source_label=label, table="document", field="approved_seed_sha256"), snapshots, blobs,
        )
    except ValueError as error:
        raise _configuration_error("manifest_schema_invalid", "manifest values violate their schema", source_label=label, table="document") from error


def _identity(table: object, *, source_label: str, label: str) -> EvidenceFileIdentity:
    values = _exact_keys(table, _IDENTITY_KEYS, source_label=source_label, table_name=label)
    return EvidenceFileIdentity(
        _relative_path(values["relative_path"], source_label=source_label, table=label, field="relative_path"),
        _integer(values["byte_length"], source_label=source_label, table=label, field="byte_length"),
        _digest(values["raw_sha256"], source_label=source_label, table=label, field="raw_sha256"),
        _string(values["role"], source_label=source_label, table=label, field="role"),
    )


def parse_retained_v7_manifest(raw: bytes, *, source_path: Path, repository_root: Path) -> LoadedRetainedV7Manifest:
    document, label = _parse_toml(raw, source_path=source_path, repository_root=repository_root)
    root = _exact_keys(document, _RETAINED_KEYS, source_label=label, table_name="document")
    try:
        manifest = RetainedV7Manifest(
            _string(root["schema_version"], source_label=label, table="document", field="schema_version"),
            _commit(root["source_seal_commit"], source_label=label, table="document", field="source_seal_commit"),
            _commit(root["authorization_commit"], source_label=label, table="document", field="authorization_commit"),
            _commit(root["historical_reader_commit"], source_label=label, table="document", field="historical_reader_commit"),
            _digest(root["journal_protocol_sha256"], source_label=label, table="document", field="journal_protocol_sha256"),
            _digest(root["campaign_sha256"], source_label=label, table="document", field="campaign_sha256"),
            *(_integer(root[field], source_label=label, table="document", field=field) for field in ("record_count", "observation_count", "calibration_cell_count", "warmup_cell_count", "measured_labelled_partial_cell_count")),
            _string(root["terminal"], source_label=label, table="document", field="terminal"),
            *(_boolean(root[field], source_label=label, table="document", field=field) for field in ("journal_complete", "scientific_campaign_complete")),
            *(_integer(root[field], source_label=label, table="document", field=field) for field in ("scientific_call_count", "authoritative_measured_call_count")),
            _boolean(root["passed"], source_label=label, table="document", field="passed"),
            *(_integer(root[field], source_label=label, table="document", field=field) for field in ("laboratory_elapsed_ns", "laboratory_wall_ns", "outside_laboratory_elapsed_ns", "outside_laboratory_wall_ns", "public_elapsed_ns", "public_wall_ns")),
            _boolean(root["fit_projection_present"], source_label=label, table="document", field="fit_projection_present"),
            _string(root["production_base_classification"], source_label=label, table="document", field="production_base_classification"),
            *(_boolean(root[field], source_label=label, table="document", field=field) for field in ("candidate_selection_present", "topology_selection_present", "arithmetic_schedule_selection_present", "truncation_authorized")),
            _relative_path(root["historical_blobs_manifest_path"], source_label=label, table="document", field="historical_blobs_manifest_path"),
            _string_list(root["absent_launch_paths"], source_label=label, table="document", field="absent_launch_paths", paths=True),
            _string_list(root["expected_null_claim_paths"], source_label=label, table="document", field="expected_null_claim_paths", paths=False),
            _identity(root["result"], source_label=label, label="result"),
            _identity(root["attempt"], source_label=label, label="attempt"),
            _identity(root["consumed_launch"], source_label=label, label="consumed_launch"),
        )
    except ValueError as error:
        raise _configuration_error("manifest_schema_invalid", "manifest values violate their schema", source_label=label, table="document") from error
    source_identity = EvidenceFileIdentity(label, len(raw), sha256(raw).hexdigest(), "retained_v7_manifest")
    return LoadedRetainedV7Manifest(manifest, source_identity, semantic_sha256(manifest_to_semantic_value(manifest)))


def manifest_to_semantic_value(manifest: RetainedV7Manifest) -> dict[str, object]:
    """Return every retained-v7 field in a stable primitive representation."""
    value: dict[str, object] = {}
    for field in manifest.__dataclass_fields__:
        item = getattr(manifest, field)
        if isinstance(item, EvidenceFileIdentity):
            value[field] = {name: getattr(item, name) for name in item.__dataclass_fields__}
        else:
            value[field] = item
    return value


def validate_current_boundary(files_manifest: SealedCurrentFilesManifest, absences_manifest: SealedCurrentAbsencesManifest) -> None:
    if files_manifest.baseline_commit != absences_manifest.baseline_commit:
        raise EvidenceIntegrityError("current_manifest_baseline_mismatch", "current manifests disagree on baseline commit", context={"files_baseline": files_manifest.baseline_commit, "absences_baseline": absences_manifest.baseline_commit})
    if files_manifest.entry_count != len(files_manifest.files) or absences_manifest.entry_count != len(absences_manifest.absences):
        raise EvidenceIntegrityError("current_manifest_count_mismatch", "current manifest count does not match its entries", context={})
    present_paths = {entry.relative_path for entry in files_manifest.files}
    absent_paths = {entry.relative_path for entry in absences_manifest.absences}
    overlap = tuple(sorted(present_paths & absent_paths))
    if overlap:
        raise EvidenceIntegrityError("current_manifest_presence_overlap", "current manifests disagree on path presence", context={"paths": overlap})
    owners = [(entry.owner, entry.relative_path) for entry in files_manifest.files] + [(entry.owner, entry.relative_path) for entry in absences_manifest.absences]
    if len(set(owners)) != len(owners):
        raise EvidenceIntegrityError("current_manifest_owner_path_duplicate", "current manifests contain a duplicate owner/path identity", context={})
