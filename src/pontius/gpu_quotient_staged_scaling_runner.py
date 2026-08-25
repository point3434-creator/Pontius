"""Exclusive durable owner for ADR-0373's staged GPU quotient ladder."""

from __future__ import annotations

import argparse
from collections.abc import Callable, Mapping
from hashlib import sha256
import json
from pathlib import Path
import subprocess
from time import perf_counter
from typing import Any

from .durable_evidence_journal import (
    DURABLE_EVIDENCE_JOURNAL_PROTOCOL_SHA256,
    DurableEvidenceJournalWriter,
    JournalRecordKind,
)
from .gpu_quotient_staged_scaling import (
    ADJOINT_WARM_REPETITIONS,
    CAMPAIGN_WALL_LIMIT_MS,
    FEATURE_WIDTH,
    GPU_QUOTIENT_STAGED_SCALING_PROTOCOL_SHA256,
    QUERY_ONLY_REPETITIONS,
    RESULT_RELATIVE_PATH,
    SOURCE_RANK,
    SOURCE_REFRESH_REPETITIONS,
    STAGE_CARDS,
    STAGE_WALL_LIMIT_MS,
    WARM_REPETITIONS,
    execute_gpu_stage,
    parse_float_text,
    stage_semantic_identity,
    validate_stage_payload,
)
from .runner_harness_v2 import load_config


_ROOT = Path(__file__).parents[2]
_CONFIG = _ROOT / "experiments/configs/gpu-quotient-staged-scaling-v1.json"
_OUTPUT = _ROOT / RESULT_RELATIVE_PATH
_PARTIAL = Path(f"{_OUTPUT}.partial")
_IMPLEMENTATION = _ROOT / "src/pontius/gpu_quotient_staged_scaling.py"
_RUNNER = Path(__file__)
_RESULT_READER = _ROOT / "src/pontius/gpu_quotient_staged_scaling_result.py"
_DURABLE_JOURNAL = _ROOT / "src/pontius/durable_evidence_journal.py"
_CONTROL_TEST = _ROOT / "tests/test_gpu_quotient_staged_scaling.py"
_BOUNDED_SOURCE = _ROOT / "src/pontius/gpu_occupied_card_quotient.py"
_BOUNDED_TEST = _ROOT / "tests/test_gpu_occupied_card_quotient.py"
_ADR0372 = (
    _ROOT
    / "docs/decisions/ADR-0372-seal-the-bounded-gpu-occupied-card-quotient-keystone.md"
)
_ADR0373 = (
    _ROOT
    / "docs/decisions/ADR-0373-preregister-the-staged-gpu-quotient-scaling-ladder.md"
)

_CANONICAL_PATHS = {
    "expected_adr0372_sha256": _ADR0372,
    "expected_adr0373_sha256": _ADR0373,
    "expected_bounded_source_sha256": _BOUNDED_SOURCE,
    "expected_bounded_tests_sha256": _BOUNDED_TEST,
    "expected_staged_source_sha256": _IMPLEMENTATION,
    "expected_runner_sha256": _RUNNER,
    "expected_result_reader_sha256": _RESULT_READER,
    "expected_durable_journal_sha256": _DURABLE_JOURNAL,
    "expected_control_tests_sha256": _CONTROL_TEST,
}


def canonical_lf_sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"staged scaling provenance path is absent: {path}")
    return sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain(item) for item in value]
    return value


def parse_config(config: Mapping[str, Any]) -> dict[str, Any]:
    plain = _plain(config)
    expected_fields = {
        "schema_version",
        "evidence_stage",
        "staged_protocol_sha256",
        "durable_journal_protocol_sha256",
        "stage_cards",
        "source_rank",
        "feature_width",
        "warm_repetitions",
        "source_refresh_repetitions",
        "query_only_repetitions",
        "adjoint_warm_repetitions",
        "stage_wall_limit_ms",
        "campaign_wall_limit_ms",
        "result_relative_path",
        "partial_relative_path",
        "require_clean_git_state",
        "require_result_absent",
        "require_partial_absent",
        "require_exclusive_create",
        "require_fsync_each_record",
        "require_stop_after_rejection",
        "require_zero_actions_quality_and_truncation",
        *_CANONICAL_PATHS,
    }
    if set(plain) != expected_fields:
        raise ValueError("staged scaling config fields differ from source seal")
    for field, path in _CANONICAL_PATHS.items():
        if plain[field] != canonical_lf_sha256(path):
            raise ValueError(f"staged scaling provenance mismatch: {field}")
    frozen = {
        "schema_version": "gpu-quotient-staged-scaling-config-v1",
        "evidence_stage": (
            "source_sealed_after_adr0373_before_first_staged_gpu_invocation"
        ),
        "staged_protocol_sha256": GPU_QUOTIENT_STAGED_SCALING_PROTOCOL_SHA256,
        "durable_journal_protocol_sha256": (
            DURABLE_EVIDENCE_JOURNAL_PROTOCOL_SHA256
        ),
        "stage_cards": list(STAGE_CARDS),
        "source_rank": SOURCE_RANK,
        "feature_width": FEATURE_WIDTH,
        "warm_repetitions": WARM_REPETITIONS,
        "source_refresh_repetitions": SOURCE_REFRESH_REPETITIONS,
        "query_only_repetitions": QUERY_ONLY_REPETITIONS,
        "adjoint_warm_repetitions": ADJOINT_WARM_REPETITIONS,
        "stage_wall_limit_ms": int(STAGE_WALL_LIMIT_MS),
        "campaign_wall_limit_ms": int(CAMPAIGN_WALL_LIMIT_MS),
        "result_relative_path": RESULT_RELATIVE_PATH,
        "partial_relative_path": f"{RESULT_RELATIVE_PATH}.partial",
        "require_clean_git_state": True,
        "require_result_absent": True,
        "require_partial_absent": True,
        "require_exclusive_create": True,
        "require_fsync_each_record": True,
        "require_stop_after_rejection": True,
        "require_zero_actions_quality_and_truncation": True,
    }
    for field, expected in frozen.items():
        if plain[field] != expected:
            raise ValueError(f"staged scaling config drifted: {field}")
    return plain


def strict_git_metadata() -> dict[str, object]:
    def checked(*arguments: str) -> str:
        result = subprocess.run(
            ["git", *arguments],
            cwd=_ROOT,
            check=False,
            capture_output=True,
            text=True,
            timeout=10.0,
        )
        if result.returncode != 0:
            message = result.stderr.strip() or result.stdout.strip()
            raise RuntimeError(f"staged scaling Git metadata failed: {message}")
        return result.stdout.strip()

    commit = checked("rev-parse", "HEAD")
    status = checked("status", "--porcelain=v1", "--untracked-files=all")
    return {"commit": commit, "dirty": bool(status), "strict_status": True}


def campaign_identity(*, config_sha256: str, source_commit: str) -> str:
    if len(config_sha256) != 64 or len(source_commit) != 40:
        raise ValueError("campaign identity requires config and commit digests")
    payload = {
        "config_sha256": config_sha256,
        "protocol_sha256": GPU_QUOTIENT_STAGED_SCALING_PROTOCOL_SHA256,
        "source_commit": source_commit,
        "stage_semantic_identities": [
            stage_semantic_identity(cards) for cards in STAGE_CARDS
        ],
        "version": "gpu-quotient-staged-scaling-campaign-v1",
    }
    return sha256(
        json.dumps(
            payload,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
    ).hexdigest()


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


def _header_payload(
    *,
    config_sha256: str,
    source_commit: str,
    campaign_sha256: str,
) -> dict[str, object]:
    return {
        "schema_version": "gpu-quotient-staged-scaling-header-v1",
        "campaign_sha256": campaign_sha256,
        "config_sha256": config_sha256,
        "source_commit": source_commit,
        "source_dirty": False,
        "staged_protocol_sha256": GPU_QUOTIENT_STAGED_SCALING_PROTOCOL_SHA256,
        "durable_journal_protocol_sha256": (
            DURABLE_EVIDENCE_JOURNAL_PROTOCOL_SHA256
        ),
        "stage_cards": list(STAGE_CARDS),
        "stage_semantic_identities": [
            stage_semantic_identity(cards) for cards in STAGE_CARDS
        ],
        "claims": {
            "literal_45_card_result": None,
            "action_clock_result": None,
            "decision_quality_result": None,
            "truncation_authorized": False,
            "poker_strength_result": None,
        },
    }


def _terminal_payload(
    *,
    terminal: str,
    completed_stage_cards: list[int],
    failed_stage_cards: int | None,
    reason: str,
    campaign_wall_ms: float,
) -> dict[str, object]:
    if terminal not in {
        "completed_pass",
        "completed_stage_rejection",
        "infrastructure_failure",
    }:
        raise ValueError("unknown staged scaling terminal")
    return {
        "schema_version": "gpu-quotient-staged-scaling-terminal-v1",
        "terminal": terminal,
        "completed_stage_cards": completed_stage_cards,
        "failed_stage_cards": failed_stage_cards,
        "reason": reason,
        "campaign_wall_hex": float(campaign_wall_ms).hex(),
        "passed": terminal == "completed_pass",
        "claims": {
            "literal_45_card_result": None,
            "action_clock_result": None,
            "decision_quality_result": None,
            "truncation_authorized": False,
            "poker_strength_result": None,
        },
    }


def execute_campaign_to_path(
    *,
    output_path: Path,
    config_sha256: str,
    source_commit: str,
    stage_executor: Callable[[int], Mapping[str, object]] = execute_gpu_stage,
    monotonic: Callable[[], float] = perf_counter,
) -> dict[str, object]:
    """Write one durable campaign; tests inject only synthetic stage payloads."""

    campaign_sha256 = campaign_identity(
        config_sha256=config_sha256,
        source_commit=source_commit,
    )
    completed: list[int] = []
    started = monotonic()
    terminal_payload: dict[str, object] | None = None
    with DurableEvidenceJournalWriter.create(
        path=output_path,
        protocol_sha256=GPU_QUOTIENT_STAGED_SCALING_PROTOCOL_SHA256,
        campaign_sha256=campaign_sha256,
    ) as writer:
        header = _header_payload(
            config_sha256=config_sha256,
            source_commit=source_commit,
            campaign_sha256=campaign_sha256,
        )
        writer.append(
            kind=JournalRecordKind.HEADER,
            semantic_identity_sha256=_semantic_digest(header),
            payload=header,
        )
        try:
            for cards in STAGE_CARDS:
                elapsed_ms = (monotonic() - started) * 1000.0
                if elapsed_ms > CAMPAIGN_WALL_LIMIT_MS:
                    terminal_payload = _terminal_payload(
                        terminal="completed_stage_rejection",
                        completed_stage_cards=completed,
                        failed_stage_cards=cards,
                        reason="campaign_wall_crossed_before_stage",
                        campaign_wall_ms=elapsed_ms,
                    )
                    break
                supplied = stage_executor(cards)
                stage = validate_stage_payload(supplied, expected_cards=cards)
                writer.append(
                    kind=JournalRecordKind.OBSERVATION,
                    semantic_identity_sha256=stage["semantic_identity_sha256"],
                    payload=stage,
                )
                completed.append(cards)
                elapsed_ms = (monotonic() - started) * 1000.0
                if stage["passed"] is not True:
                    terminal_payload = _terminal_payload(
                        terminal="completed_stage_rejection",
                        completed_stage_cards=completed,
                        failed_stage_cards=cards,
                        reason=str(
                            stage.get("rejection_reason")
                            or "stage_conjunct_rejected"
                        ),
                        campaign_wall_ms=elapsed_ms,
                    )
                    break
                stage_wall = parse_float_text(
                    stage["timings"]["host_hex"]["stage_total"],
                    label="stage total wall",
                )
                if (
                    stage_wall > STAGE_WALL_LIMIT_MS
                    or elapsed_ms > CAMPAIGN_WALL_LIMIT_MS
                ):
                    terminal_payload = _terminal_payload(
                        terminal="completed_stage_rejection",
                        completed_stage_cards=completed,
                        failed_stage_cards=cards,
                        reason=(
                            "stage_wall_crossed"
                            if stage_wall > STAGE_WALL_LIMIT_MS
                            else "campaign_wall_crossed_after_stage"
                        ),
                        campaign_wall_ms=elapsed_ms,
                    )
                    break
            if terminal_payload is None:
                terminal_payload = _terminal_payload(
                    terminal="completed_pass",
                    completed_stage_cards=completed,
                    failed_stage_cards=None,
                    reason="all_six_non_target_stages_passed",
                    campaign_wall_ms=(monotonic() - started) * 1000.0,
                )
        except Exception as error:  # noqa: BLE001 - first durable failure is evidence
            terminal_payload = _terminal_payload(
                terminal="infrastructure_failure",
                completed_stage_cards=completed,
                failed_stage_cards=(
                    STAGE_CARDS[len(completed)]
                    if len(completed) < len(STAGE_CARDS)
                    else None
                ),
                reason=f"{type(error).__name__}: {error}",
                campaign_wall_ms=(monotonic() - started) * 1000.0,
            )
        writer.append(
            kind=JournalRecordKind.TERMINAL,
            semantic_identity_sha256=_semantic_digest(terminal_payload),
            payload=terminal_payload,
        )
    return terminal_payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=_CONFIG)
    parser.add_argument("--output", type=Path, default=_OUTPUT)
    arguments = parser.parse_args()
    if arguments.config.resolve() != _CONFIG.resolve():
        raise ValueError("staged scaling config path is frozen")
    if arguments.output.resolve() != _OUTPUT.resolve():
        raise ValueError("staged scaling result path is frozen")
    if _OUTPUT.exists() or _PARTIAL.exists():
        raise FileExistsError("staged scaling result or partial path already exists")
    loaded = load_config(
        arguments.config,
        schema_validator=parse_config,
        maximum_bytes=1_048_576,
    )
    parse_config(loaded.payload)
    git = strict_git_metadata()
    if git["dirty"] is not False:
        raise RuntimeError("staged scaling owner requires a clean Git state")
    terminal = execute_campaign_to_path(
        output_path=arguments.output,
        config_sha256=loaded.sha256,
        source_commit=str(git["commit"]),
    )
    print(
        "gpu quotient staged scaling: "
        f"terminal={terminal['terminal']} "
        f"completed={terminal['completed_stage_cards']}"
    )
    if terminal["terminal"] != "completed_pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()


__all__ = [
    "campaign_identity",
    "canonical_lf_sha256",
    "execute_campaign_to_path",
    "parse_config",
    "strict_git_metadata",
]
