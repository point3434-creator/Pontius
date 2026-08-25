"""Bootstrap-safe exclusive successor for ADR-0375's closed v1 owner."""

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
_CONFIG = _ROOT / "experiments/configs/gpu-quotient-staged-scaling-v2.json"
_OUTPUT = _ROOT / "artifacts/gpu_occupied_card_quotient_staged_scaling_v2.jsonl"
_PARTIAL = Path(f"{_OUTPUT}.partial")
_V1_OUTPUT = _ROOT / "artifacts/gpu_occupied_card_quotient_staged_scaling_v1.jsonl"
_V1_PARTIAL = Path(f"{_V1_OUTPUT}.partial")
_ARTIFACT_PARENT = _ROOT / "artifacts"
_ARTIFACT_MARKER = _ARTIFACT_PARENT / "README.md"
_PARENT_CONFIG = (
    _ROOT / "experiments/configs/gpu-quotient-staged-scaling-v1.json"
)
_MECHANISM = _ROOT / "src/pontius/gpu_quotient_staged_scaling.py"
_PARENT_RUNNER = _ROOT / "src/pontius/gpu_quotient_staged_scaling_runner.py"
_PARENT_READER = _ROOT / "src/pontius/gpu_quotient_staged_scaling_result.py"
_PARENT_TEST = _ROOT / "tests/test_gpu_quotient_staged_scaling.py"
_DURABLE_JOURNAL = _ROOT / "src/pontius/durable_evidence_journal.py"
_RUNNER = Path(__file__)
_RESULT_READER = (
    _ROOT / "src/pontius/gpu_quotient_staged_scaling_v2_result.py"
)
_CONTROL_TEST = _ROOT / "tests/test_gpu_quotient_staged_scaling_v2.py"
_ADR0373 = (
    _ROOT
    / "docs/decisions/ADR-0373-preregister-the-staged-gpu-quotient-scaling-ladder.md"
)
_ADR0374 = (
    _ROOT
    / "docs/decisions/ADR-0374-source-seal-the-staged-gpu-quotient-scaling-owner.md"
)
_ADR0375 = (
    _ROOT
    / "docs/decisions/ADR-0375-retain-the-staged-scaling-pre-journal-bootstrap-failure.md"
)

_CLAIMS = {
    "literal_45_card_result": None,
    "action_clock_result": None,
    "decision_quality_result": None,
    "truncation_authorized": False,
    "poker_strength_result": None,
}
_CANONICAL_PATHS = {
    "expected_adr0373_sha256": _ADR0373,
    "expected_adr0374_sha256": _ADR0374,
    "expected_adr0375_sha256": _ADR0375,
    "expected_parent_config_sha256": _PARENT_CONFIG,
    "expected_mechanism_sha256": _MECHANISM,
    "expected_parent_runner_sha256": _PARENT_RUNNER,
    "expected_parent_reader_sha256": _PARENT_READER,
    "expected_parent_tests_sha256": _PARENT_TEST,
    "expected_durable_journal_sha256": _DURABLE_JOURNAL,
    "expected_artifact_marker_sha256": _ARTIFACT_MARKER,
    "expected_v2_runner_sha256": _RUNNER,
    "expected_v2_result_reader_sha256": _RESULT_READER,
    "expected_v2_control_tests_sha256": _CONTROL_TEST,
}


def canonical_lf_sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"v2 staged-scaling provenance path is absent: {path}")
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
        "parent_failure",
        "parent_source_commit",
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
        "artifact_parent_relative_path",
        "artifact_marker_relative_path",
        "result_relative_path",
        "partial_relative_path",
        "closed_v1_result_relative_path",
        "closed_v1_partial_relative_path",
        "require_clean_git_state",
        "require_tracked_parent",
        "require_v1_paths_absent",
        "require_result_absent",
        "require_partial_absent",
        "require_exclusive_create",
        "require_fsync_each_record",
        "require_stop_after_rejection",
        "require_zero_actions_quality_and_truncation",
        *_CANONICAL_PATHS,
    }
    if set(plain) != expected_fields:
        raise ValueError("v2 staged-scaling config fields differ from source seal")
    for field, path in _CANONICAL_PATHS.items():
        if plain[field] != canonical_lf_sha256(path):
            raise ValueError(f"v2 staged-scaling provenance mismatch: {field}")
    frozen = {
        "schema_version": "gpu-quotient-staged-scaling-config-v2",
        "evidence_stage": "source_sealed_after_adr0375_before_first_v2_invocation",
        "parent_failure": "journal parent directory does not exist",
        "parent_source_commit": "898ed38afa1ae9fd062035b11a5529f8db9017a1",
        "staged_protocol_sha256": GPU_QUOTIENT_STAGED_SCALING_PROTOCOL_SHA256,
        "durable_journal_protocol_sha256": DURABLE_EVIDENCE_JOURNAL_PROTOCOL_SHA256,
        "stage_cards": list(STAGE_CARDS),
        "source_rank": SOURCE_RANK,
        "feature_width": FEATURE_WIDTH,
        "warm_repetitions": WARM_REPETITIONS,
        "source_refresh_repetitions": SOURCE_REFRESH_REPETITIONS,
        "query_only_repetitions": QUERY_ONLY_REPETITIONS,
        "adjoint_warm_repetitions": ADJOINT_WARM_REPETITIONS,
        "stage_wall_limit_ms": int(STAGE_WALL_LIMIT_MS),
        "campaign_wall_limit_ms": int(CAMPAIGN_WALL_LIMIT_MS),
        "artifact_parent_relative_path": "artifacts",
        "artifact_marker_relative_path": "artifacts/README.md",
        "result_relative_path": (
            "artifacts/gpu_occupied_card_quotient_staged_scaling_v2.jsonl"
        ),
        "partial_relative_path": (
            "artifacts/gpu_occupied_card_quotient_staged_scaling_v2.jsonl.partial"
        ),
        "closed_v1_result_relative_path": (
            "artifacts/gpu_occupied_card_quotient_staged_scaling_v1.jsonl"
        ),
        "closed_v1_partial_relative_path": (
            "artifacts/gpu_occupied_card_quotient_staged_scaling_v1.jsonl.partial"
        ),
        "require_clean_git_state": True,
        "require_tracked_parent": True,
        "require_v1_paths_absent": True,
        "require_result_absent": True,
        "require_partial_absent": True,
        "require_exclusive_create": True,
        "require_fsync_each_record": True,
        "require_stop_after_rejection": True,
        "require_zero_actions_quality_and_truncation": True,
    }
    for field, expected in frozen.items():
        if plain[field] != expected:
            raise ValueError(f"v2 staged-scaling config drifted: {field}")
    return plain


def validate_output_bootstrap(
    *,
    output_path: Path,
    partial_path: Path,
    marker_path: Path,
    expected_marker_sha256: str,
) -> None:
    """Validate a source-owned parent without creating or removing a file."""

    for value, label in (
        (output_path, "output"),
        (partial_path, "partial"),
        (marker_path, "marker"),
    ):
        if not isinstance(value, Path):
            raise TypeError(f"v2 staged-scaling {label} path must be a Path")
    if output_path.parent.resolve() != marker_path.parent.resolve():
        raise ValueError("v2 staged-scaling marker and output parents differ")
    if partial_path != Path(f"{output_path}.partial"):
        raise ValueError("v2 staged-scaling partial path is not derived from output")
    if not output_path.parent.is_dir() or not marker_path.is_file():
        raise FileNotFoundError("v2 staged-scaling tracked output parent is absent")
    if canonical_lf_sha256(marker_path) != expected_marker_sha256:
        raise ValueError("v2 staged-scaling tracked output parent drifted")
    if output_path.exists() or partial_path.exists():
        raise FileExistsError("v2 staged-scaling result or partial already exists")


def validate_public_bootstrap(config: Mapping[str, Any]) -> None:
    expected_marker = str(config["expected_artifact_marker_sha256"])
    validate_output_bootstrap(
        output_path=_OUTPUT,
        partial_path=_PARTIAL,
        marker_path=_ARTIFACT_MARKER,
        expected_marker_sha256=expected_marker,
    )
    if _V1_OUTPUT.exists() or _V1_PARTIAL.exists():
        raise FileExistsError("closed v1 staged-scaling path became populated")


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
            raise RuntimeError(f"v2 staged-scaling Git metadata failed: {message}")
        return result.stdout.strip()

    commit = checked("rev-parse", "HEAD")
    status = checked("status", "--porcelain=v1", "--untracked-files=all")
    marker = checked(
        "ls-files",
        "--error-unmatch",
        "--",
        "artifacts/README.md",
    ).replace("\\", "/")
    if marker != "artifacts/README.md":
        raise RuntimeError("v2 staged-scaling artifact marker is not tracked exactly")
    return {
        "commit": commit,
        "dirty": bool(status),
        "strict_status": True,
        "artifact_marker_tracked": True,
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


def campaign_identity(*, config_sha256: str, source_commit: str) -> str:
    if len(config_sha256) != 64 or len(source_commit) != 40:
        raise ValueError("v2 campaign identity requires config and commit digests")
    payload = {
        "config_sha256": config_sha256,
        "parent_failure_adr_sha256": canonical_lf_sha256(_ADR0375),
        "protocol_sha256": GPU_QUOTIENT_STAGED_SCALING_PROTOCOL_SHA256,
        "source_commit": source_commit,
        "stage_semantic_identities": [
            stage_semantic_identity(cards) for cards in STAGE_CARDS
        ],
        "version": "gpu-quotient-staged-scaling-campaign-v2",
    }
    return _semantic_digest(payload)


def _header_payload(
    *,
    config_sha256: str,
    source_commit: str,
    campaign_sha256: str,
) -> dict[str, object]:
    return {
        "schema_version": "gpu-quotient-staged-scaling-header-v2",
        "campaign_sha256": campaign_sha256,
        "config_sha256": config_sha256,
        "source_commit": source_commit,
        "source_dirty": False,
        "parent_failure_adr_sha256": canonical_lf_sha256(_ADR0375),
        "artifact_marker_sha256": canonical_lf_sha256(_ARTIFACT_MARKER),
        "staged_protocol_sha256": GPU_QUOTIENT_STAGED_SCALING_PROTOCOL_SHA256,
        "durable_journal_protocol_sha256": DURABLE_EVIDENCE_JOURNAL_PROTOCOL_SHA256,
        "stage_cards": list(STAGE_CARDS),
        "stage_semantic_identities": [
            stage_semantic_identity(cards) for cards in STAGE_CARDS
        ],
        "claims": dict(_CLAIMS),
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
        raise ValueError("unknown v2 staged-scaling terminal")
    return {
        "schema_version": "gpu-quotient-staged-scaling-terminal-v2",
        "terminal": terminal,
        "completed_stage_cards": completed_stage_cards,
        "failed_stage_cards": failed_stage_cards,
        "reason": reason,
        "campaign_wall_hex": float(campaign_wall_ms).hex(),
        "passed": terminal == "completed_pass",
        "claims": dict(_CLAIMS),
    }


def execute_campaign_to_path(
    *,
    output_path: Path,
    config_sha256: str,
    source_commit: str,
    stage_executor: Callable[[int], Mapping[str, object]] = execute_gpu_stage,
    monotonic: Callable[[], float] = perf_counter,
) -> dict[str, object]:
    """Write one v2 campaign; only tests inject synthetic stage payloads."""

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
                stage = validate_stage_payload(
                    stage_executor(cards),
                    expected_cards=cards,
                )
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
                    label="v2 stage total wall",
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
        except Exception as error:  # noqa: BLE001 - first failure is evidence
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
        raise ValueError("v2 staged-scaling config path is frozen")
    if arguments.output.resolve() != _OUTPUT.resolve():
        raise ValueError("v2 staged-scaling result path is frozen")
    loaded = load_config(
        arguments.config,
        schema_validator=parse_config,
        maximum_bytes=1_048_576,
    )
    config = parse_config(loaded.payload)
    validate_public_bootstrap(config)
    git = strict_git_metadata()
    if git["dirty"] is not False or git["artifact_marker_tracked"] is not True:
        raise RuntimeError("v2 staged-scaling owner requires a clean Git state")
    terminal = execute_campaign_to_path(
        output_path=arguments.output,
        config_sha256=loaded.sha256,
        source_commit=str(git["commit"]),
    )
    print(
        "gpu quotient staged scaling v2: "
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
    "validate_output_bootstrap",
    "validate_public_bootstrap",
]
