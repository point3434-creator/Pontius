"""Solver-free reader for ADR-0373's durable staged-scaling journal."""

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
from .gpu_quotient_staged_scaling_runner import campaign_identity


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
class StagedScalingRebinding:
    campaign_sha256: str
    config_sha256: str
    source_commit: str
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


def rebind_staged_scaling_journal(
    raw: bytes,
    *,
    expected_config_sha256: str | None = None,
    expected_source_commit: str | None = None,
) -> StagedScalingRebinding:
    """Reconstruct every stage and terminal without importing CuPy."""

    recovery = recover_journal_bytes(
        raw,
        expected_protocol_sha256=(
            GPU_QUOTIENT_STAGED_SCALING_PROTOCOL_SHA256
        ),
    )
    if not recovery.is_complete:
        reason = recovery.failure.reason if recovery.failure else "missing terminal"
        raise ValueError(f"staged scaling journal is incomplete: {reason}")
    records = recovery.records
    if len(records) < 2:
        raise ValueError("staged scaling journal omits header or terminal")
    if records[0].body.kind is not JournalRecordKind.HEADER:
        raise ValueError("staged scaling first record is not a header")
    if records[-1].body.kind is not JournalRecordKind.TERMINAL:
        raise ValueError("staged scaling last record is not a terminal")
    if any(
        record.body.kind is not JournalRecordKind.OBSERVATION
        for record in records[1:-1]
    ):
        raise ValueError("staged scaling interior record is not a stage")

    header = records[0].body.payload
    expected_header_fields = {
        "schema_version",
        "campaign_sha256",
        "config_sha256",
        "source_commit",
        "source_dirty",
        "staged_protocol_sha256",
        "durable_journal_protocol_sha256",
        "stage_cards",
        "stage_semantic_identities",
        "claims",
    }
    if set(header) != expected_header_fields:
        raise ValueError("staged scaling header fields drifted")
    if header["schema_version"] != "gpu-quotient-staged-scaling-header-v1":
        raise ValueError("staged scaling header schema drifted")
    config_sha256 = _digest(header["config_sha256"], label="config", length=64)
    source_commit = _digest(header["source_commit"], label="source commit", length=40)
    campaign_sha256 = _digest(header["campaign_sha256"], label="campaign", length=64)
    if expected_config_sha256 is not None and config_sha256 != expected_config_sha256:
        raise ValueError("staged scaling config identity drifted")
    if expected_source_commit is not None and source_commit != expected_source_commit:
        raise ValueError("staged scaling source commit drifted")
    if header["source_dirty"] is not False:
        raise ValueError("staged scaling header records dirty source")
    if header["staged_protocol_sha256"] != GPU_QUOTIENT_STAGED_SCALING_PROTOCOL_SHA256:
        raise ValueError("staged scaling protocol drifted")
    if (
        header["durable_journal_protocol_sha256"]
        != DURABLE_EVIDENCE_JOURNAL_PROTOCOL_SHA256
    ):
        raise ValueError("staged scaling durable-journal protocol drifted")
    if header["stage_cards"] != list(STAGE_CARDS):
        raise ValueError("staged scaling header population drifted")
    expected_semantics = [stage_semantic_identity(cards) for cards in STAGE_CARDS]
    if header["stage_semantic_identities"] != expected_semantics:
        raise ValueError("staged scaling header semantic schedule drifted")
    if campaign_sha256 != campaign_identity(
        config_sha256=config_sha256,
        source_commit=source_commit,
    ):
        raise ValueError("staged scaling campaign identity drifted")
    if records[0].body.semantic_identity_sha256 != _semantic_digest(header):
        raise ValueError("staged scaling header semantic digest drifted")

    stages = []
    for index, record in enumerate(records[1:-1]):
        if index >= len(STAGE_CARDS):
            raise ValueError("staged scaling journal has too many stages")
        expected_cards = STAGE_CARDS[index]
        stage = validate_stage_payload(
            record.body.payload,
            expected_cards=expected_cards,
        )
        if record.body.semantic_identity_sha256 != stage_semantic_identity(
            expected_cards
        ):
            raise ValueError("staged scaling stage record semantic digest drifted")
        stages.append(stage)

    terminal_record = records[-1]
    terminal_payload = terminal_record.body.payload
    expected_terminal_fields = {
        "schema_version",
        "terminal",
        "completed_stage_cards",
        "failed_stage_cards",
        "reason",
        "campaign_wall_hex",
        "passed",
        "claims",
    }
    if set(terminal_payload) != expected_terminal_fields:
        raise ValueError("staged scaling terminal fields drifted")
    if (
        terminal_payload["schema_version"]
        != "gpu-quotient-staged-scaling-terminal-v1"
    ):
        raise ValueError("staged scaling terminal schema drifted")
    terminal = terminal_payload["terminal"]
    if terminal not in {
        "completed_pass",
        "completed_stage_rejection",
        "infrastructure_failure",
    }:
        raise ValueError("staged scaling terminal class drifted")
    completed = terminal_payload["completed_stage_cards"]
    if not isinstance(completed, list) or completed != list(STAGE_CARDS[: len(stages)]):
        raise ValueError("staged scaling completed-stage prefix drifted")
    failed = terminal_payload["failed_stage_cards"]
    if failed is not None and failed not in STAGE_CARDS:
        raise ValueError("staged scaling failed-stage identity drifted")
    campaign_wall = parse_float_text(
        terminal_payload["campaign_wall_hex"],
        label="campaign wall",
    )
    if campaign_wall < 0.0:
        raise ValueError("staged scaling campaign wall is negative")
    reason = terminal_payload["reason"]
    if not isinstance(reason, str) or not reason:
        raise ValueError("staged scaling terminal reason is empty")
    if type(terminal_payload["passed"]) is not bool:
        raise TypeError("staged scaling terminal pass bit is not Boolean")
    if terminal_record.body.semantic_identity_sha256 != _semantic_digest(
        terminal_payload
    ):
        raise ValueError("staged scaling terminal semantic digest drifted")

    expected_claims = {
        "literal_45_card_result": None,
        "action_clock_result": None,
        "decision_quality_result": None,
        "truncation_authorized": False,
        "poker_strength_result": None,
    }
    if header["claims"] != expected_claims or terminal_payload["claims"] != expected_claims:
        raise ValueError("staged scaling claims boundary drifted")

    if terminal == "completed_pass":
        if len(stages) != len(STAGE_CARDS):
            raise ValueError("passing staged scaling journal is incomplete")
        if any(stage["passed"] is not True for stage in stages):
            raise ValueError("passing terminal contains a rejected stage")
        if failed is not None or terminal_payload["passed"] is not True:
            raise ValueError("passing terminal fields are inconsistent")
        if campaign_wall > CAMPAIGN_WALL_LIMIT_MS:
            raise ValueError("passing terminal exceeds the campaign wall")
    elif terminal == "completed_stage_rejection":
        if terminal_payload["passed"] is not False:
            raise ValueError("rejection terminal is marked passing")
        if failed is None:
            if len(stages) >= len(STAGE_CARDS):
                raise ValueError("rejection terminal lacks a failed stage")
            expected_failed = STAGE_CARDS[len(stages)]
        else:
            expected_failed = (
                STAGE_CARDS[len(stages) - 1]
                if stages and stages[-1]["passed"] is False
                else STAGE_CARDS[len(stages)]
            )
        if failed != expected_failed:
            raise ValueError("rejection terminal failed-stage seam drifted")
        if stages and any(stage["passed"] is not True for stage in stages[:-1]):
            raise ValueError("rejection terminal has an earlier rejected stage")
    else:
        if terminal_payload["passed"] is not False:
            raise ValueError("infrastructure terminal is marked passing")
        if any(stage["passed"] is not True for stage in stages):
            raise ValueError("infrastructure terminal follows scientific rejection")
        expected_failed = (
            STAGE_CARDS[len(stages)]
            if len(stages) < len(STAGE_CARDS)
            else None
        )
        if failed != expected_failed:
            raise ValueError("infrastructure terminal failed-stage seam drifted")

    return StagedScalingRebinding(
        campaign_sha256=campaign_sha256,
        config_sha256=config_sha256,
        source_commit=source_commit,
        terminal=str(terminal),
        completed_stage_cards=tuple(int(card) for card in completed),
        failed_stage_cards=None if failed is None else int(failed),
        stage_payloads=tuple(stages),
        campaign_wall_ms=campaign_wall,
        journal_sha256=sha256(raw).hexdigest(),
        journal_byte_count=len(raw),
    )


def rebind_staged_scaling_file(
    path: Path,
    *,
    expected_config_sha256: str | None = None,
    expected_source_commit: str | None = None,
) -> StagedScalingRebinding:
    if not isinstance(path, Path):
        raise TypeError("staged scaling result path must be a Path")
    return rebind_staged_scaling_journal(
        path.read_bytes(),
        expected_config_sha256=expected_config_sha256,
        expected_source_commit=expected_source_commit,
    )


__all__ = [
    "StagedScalingRebinding",
    "rebind_staged_scaling_file",
    "rebind_staged_scaling_journal",
]
