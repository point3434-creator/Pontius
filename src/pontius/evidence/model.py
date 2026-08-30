"""Immutable, validated values shared by the evidence layer."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath, PureWindowsPath
from typing import Literal, TypeAlias


def _require_string(value: object, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a non-empty string")
    return value


def _require_int(value: object, name: str) -> int:
    if type(value) is not int or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")
    return value


def _require_bool(value: object, name: str) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{name} must be a boolean")
    return value


def _require_sha256(value: object, name: str) -> str:
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
    if candidate.is_absolute() or any(part == ".." for part in candidate.parts):
        raise ValueError(f"{name} must not escape the repository")
    normalised = candidate.as_posix()
    if normalised in ("", "."):
        raise ValueError(f"{name} must name a file")
    return normalised


def _normalise_paths(values: object, name: str) -> tuple[str, ...]:
    if not isinstance(values, tuple):
        raise ValueError(f"{name} must be a tuple")
    normalised = tuple(sorted(_normalise_relative_path(value, name) for value in values))
    if len(set(normalised)) != len(normalised):
        raise ValueError(f"{name} must not contain duplicate paths")
    return normalised


def _require_string_tuple(values: object, name: str) -> tuple[str, ...]:
    if not isinstance(values, tuple):
        raise ValueError(f"{name} must be a tuple")
    return tuple(_require_string(value, name) for value in values)


@dataclass(frozen=True, slots=True)
class EvidenceFileIdentity:
    relative_path: str
    byte_length: int
    raw_sha256: str
    role: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "relative_path", _normalise_relative_path(self.relative_path, "relative_path"))
        _require_int(self.byte_length, "byte_length")
        _require_sha256(self.raw_sha256, "raw_sha256")
        _require_string(self.role, "role")


@dataclass(frozen=True, slots=True)
class FileIdentity:
    platform: Literal["windows", "posix"]
    volume_or_device: int
    file_id: int
    byte_length: int
    created_or_changed_ns: int
    modified_ns: int
    mode_or_attributes: int
    reparse_tag: int | None

    def __post_init__(self) -> None:
        if self.platform not in ("windows", "posix"):
            raise ValueError("platform must be windows or posix")
        for name in ("volume_or_device", "file_id", "byte_length", "created_or_changed_ns", "modified_ns", "mode_or_attributes"):
            _require_int(getattr(self, name), name)
        if self.platform == "posix":
            if self.reparse_tag is not None:
                raise ValueError("reparse_tag must be None on posix")
        else:
            if self.reparse_tag is None:
                raise ValueError("reparse_tag is required on windows")
            _require_int(self.reparse_tag, "reparse_tag")


@dataclass(frozen=True, slots=True)
class GitTreeEntry:
    mode: str
    object_type: Literal["blob"]
    object_oid: str
    relative_path: str

    def __post_init__(self) -> None:
        _require_string(self.mode, "mode")
        if self.object_type != "blob":
            raise ValueError("object_type must be blob")
        _require_git_oid(self.object_oid, "object_oid")
        object.__setattr__(self, "relative_path", _normalise_relative_path(self.relative_path, "relative_path"))


@dataclass(frozen=True, slots=True)
class GitIndexEntry:
    mode: str
    blob_oid: str
    stage: int
    relative_path: str

    def __post_init__(self) -> None:
        _require_string(self.mode, "mode")
        _require_git_oid(self.blob_oid, "blob_oid")
        if type(self.stage) is not int or self.stage not in (0, 1, 2, 3):
            raise ValueError("stage must be an integer from 0 through 3")
        object.__setattr__(self, "relative_path", _normalise_relative_path(self.relative_path, "relative_path"))


@dataclass(frozen=True, slots=True)
class AuthorizationPolicy:
    config_path: str
    schema_version: str
    authorization_commit_paths: tuple[str, ...]
    maximum_config_bytes: int = 65_536

    def __post_init__(self) -> None:
        object.__setattr__(self, "config_path", _normalise_relative_path(self.config_path, "config_path"))
        _require_string(self.schema_version, "schema_version")
        object.__setattr__(self, "authorization_commit_paths", _normalise_paths(self.authorization_commit_paths, "authorization_commit_paths"))
        if type(self.maximum_config_bytes) is not int or self.maximum_config_bytes <= 0:
            raise ValueError("maximum_config_bytes must be a positive integer")


@dataclass(frozen=True, slots=True)
class PreauthorizationState:
    head_commit: str
    config_path: str
    present: Literal[False] = False
    in_head: Literal[False] = False
    in_index: Literal[False] = False

    def __post_init__(self) -> None:
        _require_git_oid(self.head_commit, "head_commit")
        object.__setattr__(self, "config_path", _normalise_relative_path(self.config_path, "config_path"))
        if self.present is not False or self.in_head is not False or self.in_index is not False:
            raise ValueError("preauthorization state must contain only false flags")


@dataclass(frozen=True, slots=True)
class LiveAuthorizationState:
    head_commit: str
    authorization_commit: str
    source_seal_commit: str
    config_path: str
    config_raw_sha256: str
    config_canonical_lf_sha256: str
    authorization_commit_paths: tuple[str, ...]

    def __post_init__(self) -> None:
        for name in ("head_commit", "authorization_commit", "source_seal_commit"):
            _require_git_oid(getattr(self, name), name)
        object.__setattr__(self, "config_path", _normalise_relative_path(self.config_path, "config_path"))
        _require_sha256(self.config_raw_sha256, "config_raw_sha256")
        _require_sha256(self.config_canonical_lf_sha256, "config_canonical_lf_sha256")
        object.__setattr__(self, "authorization_commit_paths", _normalise_paths(self.authorization_commit_paths, "authorization_commit_paths"))


AuthorizationState: TypeAlias = PreauthorizationState | LiveAuthorizationState


@dataclass(frozen=True, slots=True)
class SealedCurrentFileEntry:
    relative_path: str
    byte_length: int
    raw_sha256: str
    role: str
    governing_decision: str
    owner: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "relative_path", _normalise_relative_path(self.relative_path, "relative_path"))
        _require_int(self.byte_length, "byte_length")
        _require_sha256(self.raw_sha256, "raw_sha256")
        for name in ("role", "governing_decision", "owner"):
            _require_string(getattr(self, name), name)


@dataclass(frozen=True, slots=True)
class SealedCurrentAbsenceEntry:
    relative_path: str
    role: str
    governing_decision: str
    owner: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "relative_path", _normalise_relative_path(self.relative_path, "relative_path"))
        for name in ("role", "governing_decision", "owner"):
            _require_string(getattr(self, name), name)


@dataclass(frozen=True, slots=True)
class HistoricalSnapshot:
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
class HistoricalBlobIdentity:
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
class SealedCurrentFilesManifest:
    schema_version: str
    baseline_commit: str
    entry_count: int
    files: tuple[SealedCurrentFileEntry, ...]

    def __post_init__(self) -> None:
        _require_string(self.schema_version, "schema_version")
        _require_git_oid(self.baseline_commit, "baseline_commit")
        _require_int(self.entry_count, "entry_count")
        if not isinstance(self.files, tuple) or not all(isinstance(item, SealedCurrentFileEntry) for item in self.files):
            raise ValueError("files must be a tuple of SealedCurrentFileEntry values")
        if self.entry_count != len(self.files):
            raise ValueError("entry_count must match the number of files")


@dataclass(frozen=True, slots=True)
class SealedCurrentAbsencesManifest:
    schema_version: str
    baseline_commit: str
    entry_count: int
    absences: tuple[SealedCurrentAbsenceEntry, ...]

    def __post_init__(self) -> None:
        _require_string(self.schema_version, "schema_version")
        _require_git_oid(self.baseline_commit, "baseline_commit")
        _require_int(self.entry_count, "entry_count")
        if not isinstance(self.absences, tuple) or not all(isinstance(item, SealedCurrentAbsenceEntry) for item in self.absences):
            raise ValueError("absences must be a tuple of SealedCurrentAbsenceEntry values")
        if self.entry_count != len(self.absences):
            raise ValueError("entry_count must match the number of absences")


@dataclass(frozen=True, slots=True)
class HistoricalBlobsManifest:
    schema_version: str
    baseline_commit: str
    snapshot_count: int
    entry_count: int
    entries_sha256: str
    approved_seed_sha256: str
    snapshots: tuple[HistoricalSnapshot, ...]
    blobs: tuple[HistoricalBlobIdentity, ...]

    def __post_init__(self) -> None:
        _require_string(self.schema_version, "schema_version")
        _require_git_oid(self.baseline_commit, "baseline_commit")
        _require_int(self.snapshot_count, "snapshot_count")
        _require_int(self.entry_count, "entry_count")
        _require_sha256(self.entries_sha256, "entries_sha256")
        _require_sha256(self.approved_seed_sha256, "approved_seed_sha256")
        if not isinstance(self.snapshots, tuple) or not all(isinstance(item, HistoricalSnapshot) for item in self.snapshots):
            raise ValueError("snapshots must be a tuple of HistoricalSnapshot values")
        if not isinstance(self.blobs, tuple) or not all(isinstance(item, HistoricalBlobIdentity) for item in self.blobs):
            raise ValueError("blobs must be a tuple of HistoricalBlobIdentity values")
        if self.snapshot_count != len(self.snapshots):
            raise ValueError("snapshot_count must match the number of snapshots")
        if self.entry_count != len(self.blobs):
            raise ValueError("entry_count must match the number of blobs")


@dataclass(frozen=True, slots=True)
class RetainedV7Manifest:
    schema_version: str
    source_seal_commit: str
    authorization_commit: str
    historical_reader_commit: str
    journal_protocol_sha256: str
    campaign_sha256: str
    record_count: int
    observation_count: int
    calibration_cell_count: int
    warmup_cell_count: int
    measured_labelled_partial_cell_count: int
    terminal: str
    journal_complete: bool
    scientific_campaign_complete: bool
    scientific_call_count: int
    authoritative_measured_call_count: int
    passed: bool
    laboratory_elapsed_ns: int
    laboratory_wall_ns: int
    outside_laboratory_elapsed_ns: int
    outside_laboratory_wall_ns: int
    public_elapsed_ns: int
    public_wall_ns: int
    fit_projection_present: bool
    production_base_classification: str
    candidate_selection_present: bool
    topology_selection_present: bool
    arithmetic_schedule_selection_present: bool
    truncation_authorized: bool
    historical_blobs_manifest_path: str
    absent_launch_paths: tuple[str, ...]
    expected_null_claim_paths: tuple[str, ...]
    result: EvidenceFileIdentity
    attempt: EvidenceFileIdentity
    consumed_launch: EvidenceFileIdentity

    def __post_init__(self) -> None:
        _require_string(self.schema_version, "schema_version")
        for name in ("source_seal_commit", "authorization_commit", "historical_reader_commit"):
            _require_git_oid(getattr(self, name), name)
        for name in ("journal_protocol_sha256", "campaign_sha256"):
            _require_sha256(getattr(self, name), name)
        for name in (
            "record_count", "observation_count", "calibration_cell_count", "warmup_cell_count",
            "measured_labelled_partial_cell_count", "scientific_call_count", "authoritative_measured_call_count",
            "laboratory_elapsed_ns", "laboratory_wall_ns", "outside_laboratory_elapsed_ns",
            "outside_laboratory_wall_ns", "public_elapsed_ns", "public_wall_ns",
        ):
            _require_int(getattr(self, name), name)
        _require_string(self.terminal, "terminal")
        for name in (
            "journal_complete", "scientific_campaign_complete", "passed", "fit_projection_present",
            "candidate_selection_present", "topology_selection_present", "arithmetic_schedule_selection_present",
            "truncation_authorized",
        ):
            _require_bool(getattr(self, name), name)
        _require_string(self.production_base_classification, "production_base_classification")
        object.__setattr__(self, "historical_blobs_manifest_path", _normalise_relative_path(self.historical_blobs_manifest_path, "historical_blobs_manifest_path"))
        object.__setattr__(self, "absent_launch_paths", _normalise_paths(self.absent_launch_paths, "absent_launch_paths"))
        object.__setattr__(self, "expected_null_claim_paths", _require_string_tuple(self.expected_null_claim_paths, "expected_null_claim_paths"))
        for name in ("result", "attempt", "consumed_launch"):
            if not isinstance(getattr(self, name), EvidenceFileIdentity):
                raise ValueError(f"{name} must be an EvidenceFileIdentity")


@dataclass(frozen=True, slots=True)
class LoadedRetainedV7Manifest:
    manifest: RetainedV7Manifest
    source_identity: EvidenceFileIdentity
    semantic_sha256: str

    def __post_init__(self) -> None:
        if not isinstance(self.manifest, RetainedV7Manifest):
            raise ValueError("manifest must be a RetainedV7Manifest")
        if not isinstance(self.source_identity, EvidenceFileIdentity):
            raise ValueError("source_identity must be an EvidenceFileIdentity")
        _require_sha256(self.semantic_sha256, "semantic_sha256")


@dataclass(frozen=True, slots=True)
class RetainedV7Assessment:
    manifest_identity: str
    terminal: str
    journal_complete: bool
    scientific_campaign_complete: bool
    scientific_call_count: int
    authoritative_measured_call_count: int
    passed: bool
    historical_commit: str

    def __post_init__(self) -> None:
        _require_sha256(self.manifest_identity, "manifest_identity")
        _require_string(self.terminal, "terminal")
        _require_bool(self.journal_complete, "journal_complete")
        _require_bool(self.scientific_campaign_complete, "scientific_campaign_complete")
        _require_int(self.scientific_call_count, "scientific_call_count")
        _require_int(self.authoritative_measured_call_count, "authoritative_measured_call_count")
        _require_bool(self.passed, "passed")
        _require_git_oid(self.historical_commit, "historical_commit")
