"""Replay h32 fixed-envelope selection by candidate availability time."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
import time
from typing import Any

from .h32_acceptance_semantics_replay import select_fixed_blueprint_envelope
from .reporting import environment_metadata


_ROOT = Path(__file__).parents[2]
_CONFIG = _ROOT / "experiments" / "configs" / "h32-candidate-availability-replay-v1.json"
_OUTPUT = _ROOT / "experiments" / "results" / "h32-candidate-availability-replay-v1.json"
_ORIGINAL = _ROOT / "experiments" / "results" / "h32-acceptance-semantics-replay-v1.json"
_ORIGINAL_TIMING = _ROOT / "experiments" / "results" / "h32-warm-candidate-stream-v1.json"
_FRESH = _ROOT / "experiments" / "results" / "fresh-h32-strategy-transfer-audit-v1.json"
_SELECTOR = _ROOT / "src" / "pontius" / "h32_acceptance_semantics_replay.py"
_IMPLEMENTATION = Path(__file__)

_FIELDS = {
    "evidence_stage",
    "expected_original_acceptance_sha256",
    "expected_original_timing_sha256",
    "expected_fresh_transfer_sha256",
    "expected_selector_sha256",
    "expected_replay_implementation_sha256",
    "raw_guard",
    "availability",
    "stages",
    "late_candidate_ids",
    "gates",
}
_GATES = {
    "expected_board_sources",
    "expected_targets",
    "expected_targets_per_board",
    "expected_candidates_per_target",
    "expected_stage_candidate_counts",
    "require_source_status_and_gates",
    "require_nested_exhaustive_stages",
    "require_full_stage_source_selection_identity",
    "maximum_quality_vector_sum_error",
    "require_finite_quality_and_cost",
    "expected_new_training_steps",
    "expected_new_strategy_evaluations",
    "expected_new_tensor_contractions",
    "maximum_replay_seconds",
}
_SOURCES = {
    "expected_original_acceptance_sha256": _ORIGINAL,
    "expected_original_timing_sha256": _ORIGINAL_TIMING,
    "expected_fresh_transfer_sha256": _FRESH,
    "expected_selector_sha256": _SELECTOR,
    "expected_replay_implementation_sha256": _IMPLEMENTATION,
}


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"availability replay source is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_h32_candidate_availability_config(config: dict[str, Any]) -> dict[str, Any]:
    if set(config) != _FIELDS:
        raise ValueError("candidate-availability config fields differ")
    frozen = {
        "evidence_stage": (
            "post_label_deterministic_replay_after_adr0113_with_zero_new_"
            "strategy_evaluations"
        ),
        "raw_guard": 3e-9,
        "availability": {
            "control_average32": 0,
            "control_current48": 0,
            "search_average1": 1,
            "search_current1": 1,
            "search_average2": 2,
            "search_current2": 2,
            "interpolate_current1_to2_alpha025": 2,
            "interpolate_current1_to2_alpha050": 2,
            "interpolate_current1_to2_alpha075": 2,
            "search_average4": 4,
            "search_current4": 4,
            "search_average8": 8,
            "search_current8": 8,
        },
        "stages": [0, 1, 2, 4, 8],
        "late_candidate_ids": [
            "search_average4",
            "search_current4",
            "search_average8",
            "search_current8",
        ],
    }
    if any(config[field] != value for field, value in frozen.items()):
        raise ValueError("candidate-availability workload differs")
    for field, path in _SOURCES.items():
        if config[field] != _sha256(path):
            raise ValueError(f"candidate-availability source hash differs for {field}")
    gates = config["gates"]
    expected_gates = {
        "expected_board_sources": 2,
        "expected_targets": 8,
        "expected_targets_per_board": 4,
        "expected_candidates_per_target": 13,
        "expected_stage_candidate_counts": [2, 4, 9, 11, 13],
        "require_source_status_and_gates": True,
        "require_nested_exhaustive_stages": True,
        "require_full_stage_source_selection_identity": True,
        "maximum_quality_vector_sum_error": 1e-12,
        "require_finite_quality_and_cost": True,
        "expected_new_training_steps": 0,
        "expected_new_strategy_evaluations": 0,
        "expected_new_tensor_contractions": 0,
        "maximum_replay_seconds": 5.0,
    }
    if not isinstance(gates, dict) or set(gates) != _GATES or gates != expected_gates:
        raise ValueError("candidate-availability gates differ")
    return {
        **config,
        "availability": dict(config["availability"]),
        "stages": tuple(config["stages"]),
        "late_candidate_ids": tuple(config["late_candidate_ids"]),
        "gates": {**gates, "expected_stage_candidate_counts": tuple(gates["expected_stage_candidate_counts"])},
    }


def _quality_from_flat(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "policy_sha256": row["policy_sha256"],
        "deviation_gains": row["deviation_gains"],
        "nash_conv": row["nash_conv"],
        "normalized_nash_conv": row["normalized_nash_conv"],
    }


def _original_targets(source: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for target in source["targets"]:
        pool = target["pools"]["full_measured_union"]
        blueprint = {
            "candidate_id": "blueprint_average64",
            "quality": _quality_from_flat(target["blueprint"]),
        }
        candidates = [
            {
                "candidate_id": row["candidate_id"],
                "quality": _quality_from_flat(row),
            }
            for row in pool["candidate_rows"]
        ]
        rows.append(
            {
                "board_source": "original",
                "range_family": target["range_family"],
                "target_shift": target["target_shift"],
                "blueprint": blueprint,
                "candidates": candidates,
                "source_selected_policy_sha256": pool["fixed_envelope"]["canonical"]["selected_policy_sha256"],
            }
        )
    return rows


def _fresh_targets(source: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for target in source["targets"]:
        rows.append(
            {
                "board_source": "fresh",
                "range_family": target["range_family"],
                "target_shift": target["target_shift"],
                "blueprint": {
                    "candidate_id": "blueprint_average64",
                    "quality": target["blueprint_quality"],
                },
                "candidates": [
                    {
                        "candidate_id": row["candidate_id"],
                        "quality": row["quality"],
                    }
                    for row in target["candidates"]
                ],
                "source_selected_policy_sha256": target["full_pool_selection"]["selected_policy_sha256"],
            }
        )
    return rows


def _timing_target(source: dict[str, Any], *, family: str, shift: str) -> dict[str, Any]:
    family_row = next(row for row in source["family_rows"] if row["range_family"] == family)
    return next(row for row in family_row["targets"] if row["target_shift"] == shift)


def _cost_row(
    target: dict[str, Any],
    *,
    original_timing: dict[str, Any],
    fresh_source: dict[str, Any],
    late_ids: tuple[str, ...],
) -> dict[str, Any]:
    family = target["range_family"]
    shift = target["target_shift"]
    if target["board_source"] == "original":
        timing = _timing_target(original_timing, family=family, shift=shift)
        by_id = {row["candidate_id"]: row for row in timing["candidates"]}
        step2 = float(by_id["search_current2"]["cumulative_search_ms"])
        step8 = float(by_id["search_current8"]["cumulative_search_ms"])
        late_evaluation = math.fsum(float(by_id[value]["quality"]["wall_ms"]) for value in late_ids)
    else:
        timing = next(
            row
            for row in fresh_source["targets"]
            if row["range_family"] == family and row["target_shift"] == shift
        )
        checkpoints = {int(row["iteration"]): row for row in timing["search_checkpoints"]}
        step2 = float(checkpoints[2]["cumulative_search_ms"])
        step8 = float(checkpoints[8]["cumulative_search_ms"])
        by_id = {row["candidate_id"]: row for row in timing["candidates"]}
        late_evaluation = math.fsum(float(by_id[value]["quality"]["wall_ms"]) for value in late_ids)
    return {
        "step2_cumulative_search_ms": step2,
        "step8_cumulative_search_ms": step8,
        "avoided_search_ms": step8 - step2,
        "avoided_full_teacher_evaluation_ms": late_evaluation,
        "avoided_recorded_full_measurement_ms": step8 - step2 + late_evaluation,
        "avoided_warm_steps": 6,
    }


def _vector_error(row: dict[str, Any]) -> float:
    quality = row["quality"]
    return abs(math.fsum(float(value) for value in quality["deviation_gains"]) - float(quality["nash_conv"]))


def run_h32_candidate_availability_replay(config: dict[str, Any]) -> dict[str, Any]:
    parsed = parse_h32_candidate_availability_config(config)
    started = time.perf_counter()
    original = json.loads(_ORIGINAL.read_text(encoding="utf-8"))
    original_timing = json.loads(_ORIGINAL_TIMING.read_text(encoding="utf-8"))
    fresh = json.loads(_FRESH.read_text(encoding="utf-8"))
    source_identity = all(
        source["status"] == "frozen_audit_executed" and bool(source["gates"]["passed"])
        for source in (original, original_timing, fresh)
    )
    targets = [*_original_targets(original), *_fresh_targets(fresh)]
    rows = []
    maximum_vector_error = 0.0
    finite = True
    nested = True
    for target in targets:
        candidate_ids = {row["candidate_id"] for row in target["candidates"]}
        if candidate_ids != set(parsed["availability"]):
            raise ValueError("candidate-availability target schema differs")
        previous: set[str] = set()
        stage_rows = []
        for stage in parsed["stages"]:
            available = {
                candidate_id
                for candidate_id, iteration in parsed["availability"].items()
                if int(iteration) <= stage
            }
            nested = nested and previous <= available
            selected = select_fixed_blueprint_envelope(
                target["blueprint"],
                [row for row in target["candidates"] if row["candidate_id"] in available],
                raw_guard=parsed["raw_guard"],
            )
            stage_rows.append(
                {
                    "stage_iteration": stage,
                    "available_candidate_count": len(available),
                    "available_candidate_ids": sorted(available),
                    "selection": selected,
                    "source_full_selection_identity": selected["selected_policy_sha256"] == target["source_selected_policy_sha256"],
                }
            )
            previous = available
        cost = _cost_row(
            target,
            original_timing=original_timing,
            fresh_source=fresh,
            late_ids=parsed["late_candidate_ids"],
        )
        for candidate in [target["blueprint"], *target["candidates"]]:
            maximum_vector_error = max(maximum_vector_error, _vector_error(candidate))
            quality = candidate["quality"]
            finite = finite and all(
                math.isfinite(float(value))
                for field in ("deviation_gains",)
                for value in quality[field]
            ) and all(
                math.isfinite(float(quality[field]))
                for field in ("nash_conv", "normalized_nash_conv")
            )
        finite = finite and all(math.isfinite(float(value)) and float(value) >= 0.0 for value in cost.values())
        rows.append(
            {
                "board_source": target["board_source"],
                "range_family": target["range_family"],
                "target_shift": target["target_shift"],
                "source_selected_policy_sha256": target["source_selected_policy_sha256"],
                "stage_rows": stage_rows,
                "step2_full_selection_identity": stage_rows[2]["source_full_selection_identity"],
                "full_stage_source_selection_identity": stage_rows[-1]["source_full_selection_identity"],
                "full_selected_candidate_id": stage_rows[-1]["selection"]["selected_candidate_id"],
                "full_selection_available_iteration": (
                    0
                    if stage_rows[-1]["selection"]["selected_candidate_id"] == "blueprint_average64"
                    else parsed["availability"][stage_rows[-1]["selection"]["selected_candidate_id"]]
                ),
                "cost": cost,
            }
        )
    elapsed = time.perf_counter() - started
    gates_config = parsed["gates"]
    stage_counts = tuple(len(row["stage_rows"][index]["available_candidate_ids"]) for index in range(len(parsed["stages"])))
    gates = {
        "source_status_and_gates": source_identity == gates_config["require_source_status_and_gates"],
        "board_sources": len({row["board_source"] for row in rows}) == gates_config["expected_board_sources"],
        "targets": len(rows) == gates_config["expected_targets"],
        "targets_per_board": all(sum(row["board_source"] == board for row in rows) == gates_config["expected_targets_per_board"] for board in ("original", "fresh")),
        "candidates_per_target": all(row["stage_rows"][-1]["available_candidate_count"] == gates_config["expected_candidates_per_target"] for row in rows),
        "stage_candidate_counts": stage_counts == gates_config["expected_stage_candidate_counts"],
        "nested_exhaustive_stages": nested and all(set(row["stage_rows"][-1]["available_candidate_ids"]) == set(parsed["availability"]) for row in rows) == gates_config["require_nested_exhaustive_stages"],
        "full_stage_source_selection_identity": all(row["full_stage_source_selection_identity"] for row in rows) == gates_config["require_full_stage_source_selection_identity"],
        "quality_vector_sum_error": maximum_vector_error <= gates_config["maximum_quality_vector_sum_error"],
        "finite_quality_and_cost": finite == gates_config["require_finite_quality_and_cost"],
        "zero_new_training_steps": gates_config["expected_new_training_steps"] == 0,
        "zero_new_strategy_evaluations": gates_config["expected_new_strategy_evaluations"] == 0,
        "zero_new_tensor_contractions": gates_config["expected_new_tensor_contractions"] == 0,
        "replay_seconds": elapsed <= gates_config["maximum_replay_seconds"],
    }
    gates["passed"] = all(gates.values())
    total_saved = math.fsum(row["cost"]["avoided_recorded_full_measurement_ms"] for row in rows)
    return {
        "schema_version": 1,
        "status": "post_label_replay_executed",
        "experiment_type": "h32_candidate_availability_replay",
        "config": config,
        "config_sha256": _sha256(_CONFIG),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "source_sha256": {field.removeprefix("expected_").removesuffix("_sha256"): _sha256(path) for field, path in _SOURCES.items()},
        "environment": environment_metadata(),
        "targets": rows,
        "aggregate": {
            "step2_full_selection_identity_count": sum(row["step2_full_selection_identity"] for row in rows),
            "targets": len(rows),
            "full_selection_available_by_iteration": {str(stage): sum(row["full_selection_available_iteration"] <= stage for row in rows) for stage in parsed["stages"]},
            "avoided_warm_steps": sum(row["cost"]["avoided_warm_steps"] for row in rows),
            "avoided_search_ms": math.fsum(row["cost"]["avoided_search_ms"] for row in rows),
            "avoided_full_teacher_evaluation_ms": math.fsum(row["cost"]["avoided_full_teacher_evaluation_ms"] for row in rows),
            "avoided_recorded_full_measurement_ms": total_saved,
            "avoided_recorded_full_measurement_minutes": total_saved / 60_000.0,
        },
        "correctness": {"maximum_quality_vector_sum_error": maximum_vector_error},
        "counts": {"new_training_steps": 0, "new_strategy_evaluations": 0, "new_tensor_contractions": 0},
        "gates": gates,
        "timing": {"replay_seconds": elapsed},
        "limitations": [
            "This is a post-label deterministic ledger, not a new strategic holdout.",
            "Recorded savings use complete teacher evaluation bills, not partial-verifier projections.",
            "Two boards and one one-bet river tree do not authorize a universal two-step stop.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=_CONFIG)
    parser.add_argument("--output", type=Path, default=_OUTPUT)
    args = parser.parse_args(argv)
    result = run_h32_candidate_availability_replay(json.loads(args.config.read_text(encoding="utf-8")))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, allow_nan=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "h32 candidate availability replay: "
        f"passed={result['gates']['passed']} "
        f"step2={result['aggregate']['step2_full_selection_identity_count']}/{result['aggregate']['targets']} "
        f"saved_minutes={result['aggregate']['avoided_recorded_full_measurement_minutes']:.3f}"
    )
    return 0 if result["gates"]["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
