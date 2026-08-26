"""Independent lifecycle reader for the ADR-0422/0423 V2 journal."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Mapping

from .durable_evidence_journal import (
    JournalRecordEnvelope,
    JournalRecordKind,
    build_journal_record_body,
    canonical_journal_json_bytes,
    recover_journal_bytes,
)
from . import legal_river_quotient_cuda_shared_direct_device_result as _v1


_ROOT = Path(__file__).parents[2]
CONFIG_RELATIVE_PATH = (
    "experiments/configs/legal-river-quotient-cuda-shared-direct-device-v2.json"
)
RESULT_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_cuda_shared_direct_device_v2.jsonl"
)
V1_RESULT_RELATIVE_PATH = _v1.RESULT_RELATIVE_PATH
RESERVED_ACTUAL_RESULT_RELATIVE_PATH = (
    _v1.RESERVED_ACTUAL_RESULT_RELATIVE_PATH
)
CONFIG_SHA256 = (
    "b8e0d9a5edafa16cdca26d3a5320826b43ccc973140706f8dc042b93b5a90bf9"
)
PREREGISTRATION_COMMIT = "22bcde5371d06a7886e0772c587e2215d8bba0e9"
PROTOCOL_SHA256 = sha256(
    b"pontius-adr0422-shared-direct-device-launcher-safe-journal-v2"
).hexdigest()
CAMPAIGN_SHA256 = sha256(
    b"pontius-adr0422-shared-direct-device-launcher-safe-campaign-v2"
).hexdigest()
LITERAL_WORKER_MODULE = (
    "pontius.legal_river_quotient_cuda_shared_direct_device_v2_runner"
)
MAXIMUM_ARTIFACT_BYTES = 67_108_864
CLAIMS = dict(_v1.CLAIMS)

DEPENDENCY_RELATIVE_PATHS = tuple(
    dict.fromkeys(
        (
            CONFIG_RELATIVE_PATH,
            "docs/decisions/ADR-0424-correct-the-v1-parent-hash-bindings-before-v2-source-seal.md",
            "docs/decisions/ADR-0423-correct-the-v2-reader-lifecycle-transduction-before-source.md",
            "docs/decisions/ADR-0422-preregister-the-launcher-safe-shared-direct-v2-owner.md",
            "docs/decisions/ADR-0421-retain-the-shared-direct-public-launch-failure.md",
            "docs/decisions/ADR-0420-source-seal-the-shared-direct-device-differential.md",
            "run_legal_river_quotient_cuda_shared_direct_device_v2.py",
            "src/pontius/legal_river_quotient_cuda_shared_direct_device_v2_runner.py",
            "src/pontius/legal_river_quotient_cuda_shared_direct_device_v2_result.py",
            "tests/test_legal_river_quotient_cuda_shared_direct_device_v2.py",
            *_v1.DEPENDENCY_RELATIVE_PATHS,
        )
    )
)

_LIFECYCLE_ALLOWLIST = (
    "journal.protocol_sha256",
    "journal.campaign_sha256",
    "header.schema_version",
    "header.config_sha256",
    "header.preregistration_commit",
    "header.dependency_hashes",
    "header.result_relative_path",
    "observations[*].config_sha256",
    "bootstrap.literal_module",
    "bootstrap.spec_name",
)


@dataclass(frozen=True, slots=True)
class V2Rebinding:
    terminal: str
    passed: bool
    source_commit: str
    container_mode: str | None
    compiler_payload_sha256: str | None
    shared_cubin_sha256: str | None
    complete_ten_control_passed: bool | None
    populations: tuple[int, ...]
    phase_count: int
    event_count: int
    lifecycle_allowlist: tuple[str, ...]


def _digest(value: object, *, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"shared-direct V2 {label} digest differs")
    return value


def _mapping(value: object, *, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"shared-direct V2 {label} mapping differs")
    return value


def canonical_lf_sha256(path: Path) -> str:
    if not isinstance(path, Path) or not path.is_file():
        raise ValueError(f"shared-direct V2 reader path is absent: {path}")
    return sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def verify_preregistered_contract() -> None:
    path = _ROOT / CONFIG_RELATIVE_PATH
    if canonical_lf_sha256(path) != CONFIG_SHA256:
        raise ValueError("shared-direct V2 reader config hash differs")
    config = json.loads(path.read_text(encoding="utf-8"))
    owner = _mapping(
        config.get("owner_and_reader_contract"), label="reader contract"
    )
    allowed = owner.get("allowlisted_lifecycle_identity_transduction")
    if (
        config.get("schema_version")
        != "legal-river-quotient-cuda-shared-direct-launcher-recovery-v2"
        or allowed
        != [
            "journal_protocol_and_campaign_sha256",
            "header_schema_config_preregistration_dependencies_and_result_path",
            "observation_wrapper_config_sha256",
            "bootstrap_literal_module_and_spec_name",
        ]
        or owner.get(
            "all_post_bootstrap_observation_event_payloads_"
            "and_the_outer_terminal_remain_exactly_v1"
        )
        is not True
    ):
        raise ValueError("shared-direct V2 reader contract differs")


def _semantic(payload: Mapping[str, object]) -> str:
    return sha256(canonical_journal_json_bytes(payload)).hexdigest()


def _translated_journal(
    records: tuple[object, ...],
) -> bytes:
    payloads = [deepcopy(record.body.payload) for record in records]  # type: ignore[attr-defined]
    header = payloads[0]
    assert isinstance(header, dict)
    dependencies = header["dependency_hashes"]
    assert isinstance(dependencies, dict)
    header.update(
        {
            "schema_version": "legal-river-shared-direct-owner-header-v1",
            "config_sha256": _v1.CONFIG_SHA256,
            "preregistration_commit": _v1.PREREGISTRATION_COMMIT,
            "dependency_hashes": {
                relative: dependencies[relative]
                for relative in _v1.DEPENDENCY_RELATIVE_PATHS
            },
            "result_relative_path": _v1.RESULT_RELATIVE_PATH,
        }
    )
    for payload in payloads[1:-1]:
        assert isinstance(payload, dict)
        payload["config_sha256"] = _v1.CONFIG_SHA256
        if payload.get("kind") == "bootstrap_handshake":
            event = payload.get("event")
            assert isinstance(event, dict)
            event["literal_module"] = _v1.LITERAL_WORKER_MODULE
            event["spec_name"] = _v1.LITERAL_WORKER_MODULE
    previous: str | None = None
    lines: list[bytes] = []
    for sequence, (record, payload) in enumerate(
        zip(records, payloads, strict=True)
    ):
        body = build_journal_record_body(
            protocol_sha256=_v1.PROTOCOL_SHA256,
            campaign_sha256=_v1.CAMPAIGN_SHA256,
            kind=record.body.kind,  # type: ignore[attr-defined]
            sequence=sequence,
            previous_record_sha256=previous,
            semantic_identity_sha256=_semantic(payload),
            payload=payload,
        )
        envelope = JournalRecordEnvelope(body=body)
        lines.append(envelope.line_bytes)
        previous = envelope.line_sha256
    return b"".join(lines)


def _validate_v2_lifecycle(
    records: tuple[object, ...], *, rebind_current_sources: bool
) -> str:
    if len(records) < 3:
        raise ValueError("shared-direct V2 record count differs")
    first = records[0].body  # type: ignore[attr-defined]
    last = records[-1].body  # type: ignore[attr-defined]
    if (
        first.kind is not JournalRecordKind.HEADER
        or last.kind is not JournalRecordKind.TERMINAL
        or any(
            record.body.kind is not JournalRecordKind.OBSERVATION  # type: ignore[attr-defined]
            for record in records[1:-1]
        )
    ):
        raise ValueError("shared-direct V2 record structure differs")
    for record in records:
        payload = record.body.payload  # type: ignore[attr-defined]
        retained_semantic = record.body.semantic_identity_sha256  # type: ignore[attr-defined]
        if _semantic(payload) != retained_semantic:
            raise ValueError("shared-direct V2 semantic identity differs")
    header = first.payload
    if set(header) != {
        "schema_version",
        "config_sha256",
        "preregistration_commit",
        "source_seal_git",
        "dependency_hashes",
        "result_relative_path",
        "reserved_actual_result_relative_path",
        "claims",
    } or (
        header.get("schema_version")
        != "legal-river-shared-direct-owner-header-v2"
        or header.get("config_sha256") != CONFIG_SHA256
        or header.get("preregistration_commit") != PREREGISTRATION_COMMIT
        or header.get("result_relative_path") != RESULT_RELATIVE_PATH
        or header.get("reserved_actual_result_relative_path")
        != RESERVED_ACTUAL_RESULT_RELATIVE_PATH
        or header.get("claims") != CLAIMS
    ):
        raise ValueError("shared-direct V2 header differs")
    source_git = _mapping(header.get("source_seal_git"), label="source git")
    commit = source_git.get("commit")
    if (
        set(source_git) != {"commit", "dirty", "strict_status"}
        or not isinstance(commit, str)
        or len(commit) != 40
        or any(character not in "0123456789abcdef" for character in commit)
        or source_git.get("dirty") is not False
        or source_git.get("strict_status") is not True
    ):
        raise ValueError("shared-direct V2 source git differs")
    dependencies = _mapping(
        header.get("dependency_hashes"), label="dependencies"
    )
    if set(dependencies) != set(DEPENDENCY_RELATIVE_PATHS):
        raise ValueError("shared-direct V2 dependency inventory differs")
    for relative, retained in dependencies.items():
        _digest(retained, label=f"dependency {relative}")
        if rebind_current_sources:
            path = _ROOT / relative
            current = sha256(
                path.read_bytes()
                if relative.startswith("artifacts/")
                else path.read_bytes().replace(b"\r\n", b"\n")
            ).hexdigest()
            if retained != current:
                raise ValueError(
                    f"shared-direct V2 dependency differs: {relative}"
                )
    if rebind_current_sources and (
        (_ROOT / V1_RESULT_RELATIVE_PATH).exists()
        or (_ROOT / RESERVED_ACTUAL_RESULT_RELATIVE_PATH).exists()
    ):
        raise ValueError("shared-direct V2 protected result exists")
    observations = [
        record.body.payload  # type: ignore[attr-defined]
        for record in records[1:-1]
    ]
    if [
        index
        for index, observation in enumerate(observations)
        if observation.get("kind") == "bootstrap_handshake"
    ] != [0]:
        raise ValueError("shared-direct V2 bootstrap cardinality differs")
    for index, observation in enumerate(observations):
        if set(observation) != {
            "schema_version",
            "kind",
            "event",
            "config_sha256",
        } or (
            observation.get("schema_version")
            != "legal-river-shared-direct-owner-observation-v1"
            or observation.get("config_sha256") != CONFIG_SHA256
        ):
            raise ValueError("shared-direct V2 observation wrapper differs")
        if index == 0:
            if observation.get("kind") != "bootstrap_handshake":
                raise ValueError("shared-direct V2 bootstrap is not first")
            event = _mapping(observation.get("event"), label="bootstrap")
            if set(event) != {
                "schema_version",
                "challenge_sha256",
                "literal_module",
                "spec_name",
                "runtime_name",
                "cupy_imported",
            } or (
                event.get("schema_version")
                != "legal-river-shared-direct-handshake-v1"
                or event.get("literal_module") != LITERAL_WORKER_MODULE
                or event.get("spec_name") != LITERAL_WORKER_MODULE
                or event.get("runtime_name") != "__main__"
                or event.get("cupy_imported") is not False
            ):
                raise ValueError("shared-direct V2 bootstrap identity differs")
            _digest(event.get("challenge_sha256"), label="challenge")
    return commit


def rebind_shared_direct_device_v2_journal(
    raw: bytes,
    *,
    rebind_current_sources: bool = True,
) -> V2Rebinding:
    if not isinstance(raw, bytes) or not raw:
        raise TypeError("shared-direct V2 journal bytes differ")
    if len(raw) > MAXIMUM_ARTIFACT_BYTES:
        raise ValueError("shared-direct V2 journal exceeds cap")
    verify_preregistered_contract()
    recovery = recover_journal_bytes(
        raw,
        expected_protocol_sha256=PROTOCOL_SHA256,
        expected_campaign_sha256=CAMPAIGN_SHA256,
    )
    if recovery.failure is not None:
        raise ValueError(
            f"shared-direct V2 journal recovery failed: {recovery.failure.reason}"
        )
    records = recovery.records
    source_commit = _validate_v2_lifecycle(
        records, rebind_current_sources=rebind_current_sources
    )
    translated = _translated_journal(records)
    semantic = _v1.rebind_shared_direct_device_journal(
        translated,
        rebind_current_sources=False,
    )
    if semantic.source_commit != source_commit:
        raise ValueError("shared-direct V2 semantic source commit differs")
    return V2Rebinding(
        terminal=semantic.terminal,
        passed=semantic.passed,
        source_commit=source_commit,
        container_mode=semantic.container_mode,
        compiler_payload_sha256=semantic.compiler_payload_sha256,
        shared_cubin_sha256=semantic.shared_cubin_sha256,
        complete_ten_control_passed=semantic.complete_ten_control_passed,
        populations=semantic.populations,
        phase_count=len(semantic.phases),
        event_count=semantic.event_count,
        lifecycle_allowlist=_LIFECYCLE_ALLOWLIST,
    )


def rebind_shared_direct_device_v2_file(
    path: Path = _ROOT / RESULT_RELATIVE_PATH,
    *,
    rebind_current_sources: bool = True,
) -> V2Rebinding:
    if not isinstance(path, Path):
        raise TypeError("shared-direct V2 result path differs")
    return rebind_shared_direct_device_v2_journal(
        path.read_bytes(), rebind_current_sources=rebind_current_sources
    )


__all__ = [
    "CAMPAIGN_SHA256",
    "CLAIMS",
    "CONFIG_SHA256",
    "DEPENDENCY_RELATIVE_PATHS",
    "LITERAL_WORKER_MODULE",
    "PROTOCOL_SHA256",
    "RESULT_RELATIVE_PATH",
    "V2Rebinding",
    "rebind_shared_direct_device_v2_file",
    "rebind_shared_direct_device_v2_journal",
    "verify_preregistered_contract",
]
