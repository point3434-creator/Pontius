"""Independent lifecycle reader for the ADR-0427 V3 journal."""

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
from . import legal_river_quotient_cuda_shared_direct_device_v2_result as _v2


_ROOT = Path(__file__).parents[2]
CONFIG_RELATIVE_PATH = (
    "experiments/configs/legal-river-quotient-cuda-shared-direct-device-v3.json"
)
RESULT_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_cuda_shared_direct_device_v3.jsonl"
)
V2_RESULT_RELATIVE_PATH = _v2.RESULT_RELATIVE_PATH
V1_RESULT_RELATIVE_PATH = _v2.V1_RESULT_RELATIVE_PATH
RESERVED_ACTUAL_RESULT_RELATIVE_PATH = (
    _v2.RESERVED_ACTUAL_RESULT_RELATIVE_PATH
)
CONFIG_SHA256 = (
    "e9265c9626fa8ba568922fb6297db75f68ca65fcaeb138cf1431aa7867d8ec5f"
)
PREREGISTRATION_COMMIT = "4be8b0316e115f3cb1548ddce43b211dcbf84101"
PROTOCOL_SHA256 = sha256(
    b"pontius-adr0427-shared-direct-device-sample-plan-journal-v3"
).hexdigest()
CAMPAIGN_SHA256 = sha256(
    b"pontius-adr0427-shared-direct-device-sample-plan-campaign-v3"
).hexdigest()
LITERAL_WORKER_MODULE = (
    "pontius.legal_river_quotient_cuda_shared_direct_device_v3_runner"
)
MAXIMUM_ARTIFACT_BYTES = 67_108_864
CLAIMS = dict(_v2.CLAIMS)

DEPENDENCY_RELATIVE_PATHS = tuple(
    dict.fromkeys(
        (
            CONFIG_RELATIVE_PATH,
            "docs/decisions/ADR-0427-preregister-the-shared-sample-plan-v3-successor.md",
            "docs/decisions/ADR-0426-retain-the-v2-population-sample-plan-rejection.md",
            "docs/decisions/ADR-0425-source-seal-the-launcher-safe-shared-direct-v2-owner.md",
            "run_legal_river_quotient_cuda_shared_direct_device_v3.py",
            "src/pontius/legal_river_quotient_cuda_shared_direct_sample_plan.py",
            "src/pontius/legal_river_quotient_cuda_shared_direct_device_v3_runner.py",
            "src/pontius/legal_river_quotient_cuda_shared_direct_device_v3_result.py",
            "tests/test_legal_river_quotient_cuda_shared_direct_device_v3.py",
            V2_RESULT_RELATIVE_PATH,
            *_v2.DEPENDENCY_RELATIVE_PATHS,
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
class V3Rebinding:
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
        raise ValueError(f"shared-direct V3 {label} digest differs")
    return value


def _mapping(value: object, *, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"shared-direct V3 {label} mapping differs")
    return value


def canonical_lf_sha256(path: Path) -> str:
    if not isinstance(path, Path) or not path.is_file():
        raise ValueError(f"shared-direct V3 reader path is absent: {path}")
    return sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def verify_preregistered_contract() -> None:
    path = _ROOT / CONFIG_RELATIVE_PATH
    if canonical_lf_sha256(path) != CONFIG_SHA256:
        raise ValueError("shared-direct V3 reader config hash differs")
    config = json.loads(path.read_text(encoding="utf-8"))
    owner = _mapping(
        config.get("fresh_runner_and_reader_contract"), label="reader contract"
    )
    if (
        config.get("schema_version")
        != "legal-river-quotient-cuda-shared-direct-sample-plan-v3"
        or owner.get(
            "v3_lifecycle_must_be_independently_validated_"
            "before_exact_v3_to_v2_projection"
        ) is not True
        or owner.get(
            "only_journal_header_wrapper_and_bootstrap_"
            "lifecycle_identity_may_change"
        ) is not True
        or owner.get(
            "all_post_bootstrap_events_and_outer_terminal_remain_exactly_v2"
        ) is not True
    ):
        raise ValueError("shared-direct V3 reader contract differs")


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
            "schema_version": "legal-river-shared-direct-owner-header-v2",
            "config_sha256": _v2.CONFIG_SHA256,
            "preregistration_commit": _v2.PREREGISTRATION_COMMIT,
            "dependency_hashes": {
                relative: dependencies[relative]
                for relative in _v2.DEPENDENCY_RELATIVE_PATHS
            },
            "result_relative_path": _v2.RESULT_RELATIVE_PATH,
        }
    )
    for payload in payloads[1:-1]:
        assert isinstance(payload, dict)
        payload["config_sha256"] = _v2.CONFIG_SHA256
        if payload.get("kind") == "bootstrap_handshake":
            event = payload.get("event")
            assert isinstance(event, dict)
            event["literal_module"] = _v2.LITERAL_WORKER_MODULE
            event["spec_name"] = _v2.LITERAL_WORKER_MODULE
    previous: str | None = None
    lines: list[bytes] = []
    for sequence, (record, payload) in enumerate(
        zip(records, payloads, strict=True)
    ):
        body = build_journal_record_body(
            protocol_sha256=_v2.PROTOCOL_SHA256,
            campaign_sha256=_v2.CAMPAIGN_SHA256,
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


def _validate_v3_lifecycle(
    records: tuple[object, ...], *, rebind_current_sources: bool
) -> str:
    if len(records) < 3:
        raise ValueError("shared-direct V3 record count differs")
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
        raise ValueError("shared-direct V3 record structure differs")
    for record in records:
        payload = record.body.payload  # type: ignore[attr-defined]
        retained_semantic = record.body.semantic_identity_sha256  # type: ignore[attr-defined]
        if _semantic(payload) != retained_semantic:
            raise ValueError("shared-direct V3 semantic identity differs")
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
        != "legal-river-shared-direct-owner-header-v3"
        or header.get("config_sha256") != CONFIG_SHA256
        or header.get("preregistration_commit") != PREREGISTRATION_COMMIT
        or header.get("result_relative_path") != RESULT_RELATIVE_PATH
        or header.get("reserved_actual_result_relative_path")
        != RESERVED_ACTUAL_RESULT_RELATIVE_PATH
        or header.get("claims") != CLAIMS
    ):
        raise ValueError("shared-direct V3 header differs")
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
        raise ValueError("shared-direct V3 source git differs")
    dependencies = _mapping(
        header.get("dependency_hashes"), label="dependencies"
    )
    if set(dependencies) != set(DEPENDENCY_RELATIVE_PATHS):
        raise ValueError("shared-direct V3 dependency inventory differs")
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
                    f"shared-direct V3 dependency differs: {relative}"
                )
    if rebind_current_sources and (
        (_ROOT / V1_RESULT_RELATIVE_PATH).exists()
        or (_ROOT / RESERVED_ACTUAL_RESULT_RELATIVE_PATH).exists()
    ):
        raise ValueError("shared-direct V3 protected result exists")
    observations = [
        record.body.payload  # type: ignore[attr-defined]
        for record in records[1:-1]
    ]
    if [
        index
        for index, observation in enumerate(observations)
        if observation.get("kind") == "bootstrap_handshake"
    ] != [0]:
        raise ValueError("shared-direct V3 bootstrap cardinality differs")
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
            raise ValueError("shared-direct V3 observation wrapper differs")
        if index == 0:
            if observation.get("kind") != "bootstrap_handshake":
                raise ValueError("shared-direct V3 bootstrap is not first")
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
                raise ValueError("shared-direct V3 bootstrap identity differs")
            _digest(event.get("challenge_sha256"), label="challenge")
    return commit


def rebind_shared_direct_device_v3_journal(
    raw: bytes,
    *,
    rebind_current_sources: bool = True,
) -> V3Rebinding:
    if not isinstance(raw, bytes) or not raw:
        raise TypeError("shared-direct V3 journal bytes differ")
    if len(raw) > MAXIMUM_ARTIFACT_BYTES:
        raise ValueError("shared-direct V3 journal exceeds cap")
    verify_preregistered_contract()
    recovery = recover_journal_bytes(
        raw,
        expected_protocol_sha256=PROTOCOL_SHA256,
        expected_campaign_sha256=CAMPAIGN_SHA256,
    )
    if recovery.failure is not None:
        raise ValueError(
            f"shared-direct V3 journal recovery failed: {recovery.failure.reason}"
        )
    records = recovery.records
    source_commit = _validate_v3_lifecycle(
        records, rebind_current_sources=rebind_current_sources
    )
    translated = _translated_journal(records)
    semantic = _v2.rebind_shared_direct_device_v2_journal(
        translated,
        rebind_current_sources=False,
    )
    if semantic.source_commit != source_commit:
        raise ValueError("shared-direct V3 semantic source commit differs")
    return V3Rebinding(
        terminal=semantic.terminal,
        passed=semantic.passed,
        source_commit=source_commit,
        container_mode=semantic.container_mode,
        compiler_payload_sha256=semantic.compiler_payload_sha256,
        shared_cubin_sha256=semantic.shared_cubin_sha256,
        complete_ten_control_passed=semantic.complete_ten_control_passed,
        populations=semantic.populations,
        phase_count=semantic.phase_count,
        event_count=semantic.event_count,
        lifecycle_allowlist=_LIFECYCLE_ALLOWLIST,
    )


def rebind_shared_direct_device_v3_file(
    path: Path = _ROOT / RESULT_RELATIVE_PATH,
    *,
    rebind_current_sources: bool = True,
) -> V3Rebinding:
    if not isinstance(path, Path):
        raise TypeError("shared-direct V3 result path differs")
    return rebind_shared_direct_device_v3_journal(
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
    "V3Rebinding",
    "rebind_shared_direct_device_v3_file",
    "rebind_shared_direct_device_v3_journal",
    "verify_preregistered_contract",
]
