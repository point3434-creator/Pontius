"""Solver-free reader for ADR-0375's bootstrap-safe v2 scaling journal."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Mapping

from .durable_evidence_journal import (
    DURABLE_EVIDENCE_JOURNAL_PROTOCOL_SHA256,
    JournalRecordKind,
    recover_journal_bytes,
)
from .gpu_quotient_staged_scaling import (
    CAMPAIGN_WALL_LIMIT_MS,
    GPU_QUOTIENT_STAGED_SCALING_PROTOCOL_SHA256,
    STAGE_CARDS,
    parse_float_text,
    stage_semantic_identity,
    validate_stage_payload,
)
from .gpu_quotient_staged_scaling_v2_runner import (
    campaign_identity,
    canonical_lf_sha256,
)


_ROOT = Path(__file__).parents[2]
_PARENT_FAILURE_ADR = (
    _ROOT
    / "docs/decisions/ADR-0375-retain-the-staged-scaling-pre-journal-bootstrap-failure.md"
)
_ARTIFACT_MARKER = _ROOT / "artifacts/README.md"
_CLAIMS = {
    "literal_45_card_result": None,
    "action_clock_result": None,
    "decision_quality_result": None,
    "truncation_authorized": False,
    "poker_strength_result": None,
}


def _semantic_digest(payload: Mapping[str, object]) -> str:
    return sha256(
        json.dumps(
            dict(payload),
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
    ).hexdigest()


def _digest(value: object, *, label: str, length: int) -> str:
    if (
        not isinstance(value, str)
        or len(value) != length
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"{label} is not a lowercase hexadecimal digest")
    return value


@dataclass(frozen=True, slots=True)
class StagedScalingV2Rebinding:
    campaign_sha256: str
    config_sha256: str
    source_commit: str
    parent_failure_adr_sha256: str
    artifact_marker_sha256: str
    terminal: str
    completed_stage_cards: tuple[int, ...]
    failed_stage_cards: int | None
    stage_payloads: tuple[Mapping[str, object], ...]
    campaign_wall_ms: float
    journal_sha256: str
    journal_byte_count: int

    @property
    def passed(self) -> bool:
        return self.terminal == "completed_pass"


def _validate_header(
    header: Mapping[str, object],
    *,
    envelope_campaign_sha256: str,
    semantic_identity_sha256: str,
    expected_config_sha256: str | None,
    expected_source_commit: str | None,
) -> tuple[str, str, str, str, str]:
    expected_fields = {
        "schema_version",
        "campaign_sha256",
        "config_sha256",
        "source_commit",
        "source_dirty",
        "parent_failure_adr_sha256",
        "artifact_marker_sha256",
        "staged_protocol_sha256",
        "durable_journal_protocol_sha256",
        "stage_cards",
        "stage_semantic_identities",
        "claims",
    }
    if set(header) != expected_fields:
        raise ValueError("v2 staged scaling header fields drifted")
    if header["schema_version"] != "gpu-quotient-staged-scaling-header-v2":
        raise ValueError("v2 staged scaling header schema drifted")
    config_sha256 = _digest(header["config_sha256"], label="config", length=64)
    source_commit = _digest(
        header["source_commit"], label="source commit", length=40
    )
    campaign_sha256 = _digest(
        header["campaign_sha256"], label="campaign", length=64
    )
    parent_failure_sha256 = _digest(
        header["parent_failure_adr_sha256"],
        label="parent failure ADR",
        length=64,
    )
    artifact_marker_sha256 = _digest(
        header["artifact_marker_sha256"],
        label="artifact marker",
        length=64,
    )
    if campaign_sha256 != envelope_campaign_sha256:
        raise ValueError("v2 staged scaling envelope/header campaign seam drifted")
    if expected_config_sha256 is not None and config_sha256 != _digest(
        expected_config_sha256,
        label="expected config",
        length=64,
    ):
        raise ValueError("v2 staged scaling config identity drifted")
    if expected_source_commit is not None and source_commit != _digest(
        expected_source_commit,
        label="expected source commit",
        length=40,
    ):
        raise ValueError("v2 staged scaling source commit drifted")
    if header["source_dirty"] is not False:
        raise ValueError("v2 staged scaling header records dirty source")
    if header["staged_protocol_sha256"] != GPU_QUOTIENT_STAGED_SCALING_PROTOCOL_SHA256:
        raise ValueError("v2 staged scaling protocol drifted")
    if (
        header["durable_journal_protocol_sha256"]
        != DURABLE_EVIDENCE_JOURNAL_PROTOCOL_SHA256
    ):
        raise ValueError("v2 staged scaling durable-journal protocol drifted")
    if header["stage_cards"] != list(STAGE_CARDS):
        raise ValueError("v2 staged scaling header population drifted")
    expected_semantics = [stage_semantic_identity(cards) for cards in STAGE_CARDS]
    if header["stage_semantic_identities"] != expected_semantics:
        raise ValueError("v2 staged scaling header semantic schedule drifted")
    if parent_failure_sha256 != canonical_lf_sha256(_PARENT_FAILURE_ADR):
        raise ValueError("v2 staged scaling parent-failure binding drifted")
    if artifact_marker_sha256 != canonical_lf_sha256(_ARTIFACT_MARKER):
        raise ValueError("v2 staged scaling artifact-parent binding drifted")
    if campaign_sha256 != campaign_identity(
        config_sha256=config_sha256,
        source_commit=source_commit,
    ):
        raise ValueError("v2 staged scaling campaign identity drifted")
    if semantic_identity_sha256 != _semantic_digest(header):
        raise ValueError("v2 staged scaling header semantic digest drifted")
    if header["claims"] != _CLAIMS:
        raise ValueError("v2 staged scaling header claims boundary drifted")
    return (
        campaign_sha256,
        config_sha256,
        source_commit,
        parent_failure_sha256,
        artifact_marker_sha256,
    )


def _validate_terminal(
    terminal_payload: Mapping[str, object],
    *,
    semantic_identity_sha256: str,
    stages: list[Mapping[str, object]],
) -> tuple[str, list[int], int | None, float]:
    expected_fields = {
        "schema_version",
        "terminal",
        "completed_stage_cards",
        "failed_stage_cards",
        "reason",
        "campaign_wall_hex",
        "passed",
        "claims",
    }
    if set(terminal_payload) != expected_fields:
        raise ValueError("v2 staged scaling terminal fields drifted")
    if terminal_payload["schema_version"] != "gpu-quotient-staged-scaling-terminal-v2":
        raise ValueError("v2 staged scaling terminal schema drifted")
    terminal = terminal_payload["terminal"]
    if terminal not in {
        "completed_pass",
        "completed_stage_rejection",
        "infrastructure_failure",
    }:
        raise ValueError("v2 staged scaling terminal class drifted")
    completed = terminal_payload["completed_stage_cards"]
    expected_completed = list(STAGE_CARDS[: len(stages)])
    if not isinstance(completed, list) or completed != expected_completed:
        raise ValueError("v2 staged scaling completed-stage prefix drifted")
    failed = terminal_payload["failed_stage_cards"]
    if failed is not None and failed not in STAGE_CARDS:
        raise ValueError("v2 staged scaling failed-stage identity drifted")
    campaign_wall = parse_float_text(
        terminal_payload["campaign_wall_hex"],
        label="v2 campaign wall",
    )
    if campaign_wall < 0.0:
        raise ValueError("v2 staged scaling campaign wall is negative")
    reason = terminal_payload["reason"]
    if not isinstance(reason, str) or not reason:
        raise ValueError("v2 staged scaling terminal reason is empty")
    if type(terminal_payload["passed"]) is not bool:
        raise TypeError("v2 staged scaling terminal pass bit is not Boolean")
    if semantic_identity_sha256 != _semantic_digest(terminal_payload):
        raise ValueError("v2 staged scaling terminal semantic digest drifted")
    if terminal_payload["claims"] != _CLAIMS:
        raise ValueError("v2 staged scaling terminal claims boundary drifted")

    if terminal == "completed_pass":
        if len(stages) != len(STAGE_CARDS):
            raise ValueError("passing v2 staged scaling journal is incomplete")
        if any(stage["passed"] is not True for stage in stages):
            raise ValueError("passing v2 terminal contains a rejected stage")
        if failed is not None or terminal_payload["passed"] is not True:
            raise ValueError("passing v2 terminal fields are inconsistent")
        if reason != "all_six_non_target_stages_passed":
            raise ValueError("passing v2 terminal reason drifted")
        if campaign_wall > CAMPAIGN_WALL_LIMIT_MS:
            raise ValueError("passing v2 terminal exceeds the campaign wall")
    elif terminal == "completed_stage_rejection":
        if terminal_payload["passed"] is not False:
            raise ValueError("v2 rejection terminal is marked passing")
        if stages and stages[-1]["passed"] is False:
            expected_failed = STAGE_CARDS[len(stages) - 1]
            if reason != stages[-1]["rejection_reason"]:
                raise ValueError("v2 stage-rejection reason seam drifted")
        elif reason == "campaign_wall_crossed_after_stage":
            if not stages or campaign_wall <= CAMPAIGN_WALL_LIMIT_MS:
                raise ValueError("v2 after-stage wall rejection is inconsistent")
            expected_failed = STAGE_CARDS[len(stages) - 1]
        elif reason == "campaign_wall_crossed_before_stage":
            if len(stages) >= len(STAGE_CARDS) or campaign_wall <= CAMPAIGN_WALL_LIMIT_MS:
                raise ValueError("v2 before-stage wall rejection is inconsistent")
            expected_failed = STAGE_CARDS[len(stages)]
        else:
            raise ValueError("v2 rejection terminal has no supported cause")
        if failed != expected_failed:
            raise ValueError("v2 rejection terminal failed-stage seam drifted")
        if any(stage["passed"] is not True for stage in stages[:-1]):
            raise ValueError("v2 rejection terminal has an earlier rejected stage")
    else:
        if terminal_payload["passed"] is not False:
            raise ValueError("v2 infrastructure terminal is marked passing")
        if any(stage["passed"] is not True for stage in stages):
            raise ValueError("v2 infrastructure terminal follows scientific rejection")
        expected_failed = (
            STAGE_CARDS[len(stages)]
            if len(stages) < len(STAGE_CARDS)
            else None
        )
        if failed != expected_failed:
            raise ValueError("v2 infrastructure terminal failed-stage seam drifted")
    return str(terminal), completed, None if failed is None else int(failed), campaign_wall


def rebind_staged_scaling_v2_journal(
    raw: bytes,
    *,
    expected_config_sha256: str | None = None,
    expected_source_commit: str | None = None,
) -> StagedScalingV2Rebinding:
    """Reconstruct every v2 stage and terminal without importing CuPy."""

    recovery = recover_journal_bytes(
        raw,
        expected_protocol_sha256=GPU_QUOTIENT_STAGED_SCALING_PROTOCOL_SHA256,
    )
    if not recovery.is_complete:
        reason = recovery.failure.reason if recovery.failure else "missing terminal"
        raise ValueError(f"v2 staged scaling journal is incomplete: {reason}")
    records = recovery.records
    if len(records) < 2:
        raise ValueError("v2 staged scaling journal omits header or terminal")
    if records[0].body.kind is not JournalRecordKind.HEADER:
        raise ValueError("v2 staged scaling first record is not a header")
    if records[-1].body.kind is not JournalRecordKind.TERMINAL:
        raise ValueError("v2 staged scaling last record is not a terminal")
    if any(
        record.body.kind is not JournalRecordKind.OBSERVATION
        for record in records[1:-1]
    ):
        raise ValueError("v2 staged scaling interior record is not a stage")

    header_record = records[0]
    (
        campaign_sha256,
        config_sha256,
        source_commit,
        parent_failure_sha256,
        artifact_marker_sha256,
    ) = _validate_header(
        header_record.body.payload,
        envelope_campaign_sha256=header_record.body.campaign_sha256,
        semantic_identity_sha256=header_record.body.semantic_identity_sha256,
        expected_config_sha256=expected_config_sha256,
        expected_source_commit=expected_source_commit,
    )

    stages: list[Mapping[str, object]] = []
    for index, record in enumerate(records[1:-1]):
        if index >= len(STAGE_CARDS):
            raise ValueError("v2 staged scaling journal has too many stages")
        expected_cards = STAGE_CARDS[index]
        stage = validate_stage_payload(
            record.body.payload,
            expected_cards=expected_cards,
        )
        if record.body.semantic_identity_sha256 != stage_semantic_identity(
            expected_cards
        ):
            raise ValueError("v2 staged scaling stage semantic identity drifted")
        stages.append(stage)

    terminal_record = records[-1]
    terminal, completed, failed, campaign_wall = _validate_terminal(
        terminal_record.body.payload,
        semantic_identity_sha256=terminal_record.body.semantic_identity_sha256,
        stages=stages,
    )
    return StagedScalingV2Rebinding(
        campaign_sha256=campaign_sha256,
        config_sha256=config_sha256,
        source_commit=source_commit,
        parent_failure_adr_sha256=parent_failure_sha256,
        artifact_marker_sha256=artifact_marker_sha256,
        terminal=terminal,
        completed_stage_cards=tuple(int(card) for card in completed),
        failed_stage_cards=failed,
        stage_payloads=tuple(stages),
        campaign_wall_ms=campaign_wall,
        journal_sha256=sha256(raw).hexdigest(),
        journal_byte_count=len(raw),
    )


def rebind_staged_scaling_v2_file(
    path: Path,
    *,
    expected_config_sha256: str | None = None,
    expected_source_commit: str | None = None,
) -> StagedScalingV2Rebinding:
    if not isinstance(path, Path):
        raise TypeError("v2 staged scaling result path must be a Path")
    return rebind_staged_scaling_v2_journal(
        path.read_bytes(),
        expected_config_sha256=expected_config_sha256,
        expected_source_commit=expected_source_commit,
    )


__all__ = [
    "StagedScalingV2Rebinding",
    "rebind_staged_scaling_v2_file",
    "rebind_staged_scaling_v2_journal",
]
