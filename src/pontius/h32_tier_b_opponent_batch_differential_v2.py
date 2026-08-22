"""Top-level source-schema correction for the frozen Tier-B batch audit."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import statistics
import time
from typing import Any

from . import h32_tier_b_opponent_batch_differential as v1
from .reporting import environment_metadata


_ROOT = Path(__file__).parents[2]
_CONFIG = _ROOT / "experiments/configs/h32-tier-b-opponent-batch-v2.json"
_OUTPUT = _ROOT / "experiments/results/h32-tier-b-opponent-batch-v2.json"
_V1_DECISION = (
    _ROOT
    / "docs/decisions/ADR-0207-preregister-six-block-tier-b-opponent-batch-differential.md"
)
_REJECTION = (
    _ROOT
    / "docs/decisions"
    / "ADR-0208-tier-b-batch-v1-rejects-before-h32-work-on-source-pass-schema.md"
)
_IMPLEMENTATION = Path(__file__)
_TEST = _ROOT / "tests/test_h32_tier_b_opponent_batch_differential_v2.py"

_PATHS = {
    "expected_v1_config_sha256": v1._CONFIG,
    "expected_v1_implementation_sha256": v1._IMPLEMENTATION,
    "expected_v1_control_test_sha256": v1._TEST,
    "expected_v1_decision_sha256": _V1_DECISION,
    "expected_v1_rejection_sha256": _REJECTION,
    "expected_source_result_sha256": v1.science._SOURCE,
    "expected_v2_implementation_sha256": _IMPLEMENTATION,
    "expected_v2_control_test_sha256": _TEST,
}

_SOURCE_SCHEMA = {
    "config",
    "config_sha256",
    "counts",
    "decision",
    "environment",
    "experiment_type",
    "gate_results",
    "implementation_sha256",
    "limitations",
    "parent_cache_authorized",
    "passed",
    "phase_order",
    "schema_version",
    "source_quality_diagnostics",
    "source_rows",
    "status",
    "strategy_quality_claim",
    "timing",
}


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required Tier-B v2 input is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_h32_tier_b_opponent_batch_v2_config(
    config: dict[str, Any],
) -> dict[str, Any]:
    """Validate the source-pass-only successor and complete v1 science."""

    fields = {
        "evidence_stage",
        *_PATHS,
        "correction_rule",
        "source_schema_rule",
        "output_rule",
        "state_reuse_rule",
    }
    if set(config) != fields:
        raise ValueError("Tier-B batch v2 fields differ from ADR-0209")
    frozen = {
        "evidence_stage": (
            "preregistered_after_adr0208_before_any_corrected_h32_tier_b_"
            "batch_measurement"
        ),
        "correction_rule": (
            "replace_both_source_parent_gates_passed_reads_with_the_pinned_"
            "top_level_source_parent_passed_field_only"
        ),
        "source_schema_rule": (
            "require_the_exact_pinned_top_level_source_schema_with_passed_and_"
            "gate_results_and_without_gates"
        ),
        "output_rule": "write_only_h32_tier_b_opponent_batch_v2_json",
        "state_reuse_rule": (
            "reconstruct_every_target_and_measurement_from_scratch_without_"
            "failed_v1_process_state"
        ),
    }
    if any(config[key] != value for key, value in frozen.items()):
        raise ValueError("Tier-B batch v2 correction differs from ADR-0209")
    for field, path in _PATHS.items():
        if config[field] != _sha256(path):
            raise ValueError(f"Tier-B batch v2 source mismatch: {field}")
    source_parent = json.loads(v1.science._SOURCE.read_text(encoding="utf-8"))
    if set(source_parent) != _SOURCE_SCHEMA:
        raise ValueError("Tier-B batch v2 source schema differs")
    if "gates" in source_parent or not isinstance(source_parent["passed"], bool):
        raise ValueError("Tier-B batch v2 source pass field differs")
    base_config = json.loads(v1._CONFIG.read_text(encoding="utf-8"))
    base = v1.parse_h32_tier_b_opponent_batch_config(base_config)
    return {**config, "base": base}


def run_h32_tier_b_opponent_batch_v2_differential(
    config_path: Path = _CONFIG,
    output_path: Path = _OUTPUT,
) -> dict[str, Any]:
    """Execute v1 science with only the reviewed top-level pass correction."""

    started = time.perf_counter()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    correction = parse_h32_tier_b_opponent_batch_v2_config(config)
    parsed = correction["base"]
    source_parent = json.loads(v1.science._SOURCE.read_text(encoding="utf-8"))
    git = v1._strict_git_metadata()
    cp, runtime = v1._validate_runtime(parsed["live"])
    if git["dirty"]:
        raise RuntimeError("Tier-B batch v2 differential requires clean Git state")
    if not bool(source_parent["passed"]):
        raise ValueError("Tier-B batch v2 source parent did not pass")

    target_rows = []
    for target_spec in parsed["live"]["targets"]:
        print(f"Tier-B opponent batch v2: {target_spec['target']}", flush=True)
        row = v1._run_target(parsed, source_parent, target_spec, cp)
        target_rows.append(row)
        if not row["batch_safe_preflight"]:
            break

    total_seconds = time.perf_counter() - started
    completed = [row for row in target_rows if row["status"] == "completed"]
    memory_rows = [memory for row in target_rows for memory in row["memory_rows"]]
    gates_config = parsed["gates"]
    maximum_numeric_error = max(
        (row["identity"]["maximum_numeric_error"] for row in completed),
        default=math.inf,
    )
    maximum_composite_error = max(
        (row["identity"]["maximum_composite_error"] for row in completed),
        default=math.inf,
    )
    maximum_probability_error = max(
        (
            row["warm_start_distance"]["maximum_probability_error"]
            for row in target_rows
        ),
        default=math.inf,
    )
    maximum_mean_tv = max(
        (
            row["warm_start_distance"]["mean_total_variation"]
            for row in target_rows
        ),
        default=math.inf,
    )
    reported_pool_rows = [
        int(timing["maximum_gpu_pool_total_bytes"])
        for row in completed
        for timing in row["timing_rows"]
    ]
    maximum_pool = max(
        [int(row["gpu_pool_total_bytes"]) for row in memory_rows]
        + reported_pool_rows,
        default=0,
    )
    minimum_free = min(
        (int(row["gpu_free_bytes"]) for row in memory_rows), default=0
    )
    all_timing_rows = [timing for row in completed for timing in row["timing_rows"]]
    source_passed = bool(source_parent["passed"])
    gates = {
        "clean_git": (not git["dirty"])
        == gates_config["require_clean_git_state"],
        "source_parent_passed": source_passed
        == gates_config["require_source_parent_passed"],
        "target_count": len(completed) == gates_config["expected_targets"],
        "candidate_count": all(
            len(row["endpoint_rows"])
            == gates_config["expected_candidates_per_target"]
            for row in completed
        ),
        "opponent_row_count": all(
            timing.get(
                "opponent_rows", gates_config["expected_opponent_rows_per_target"]
            )
            == gates_config["expected_opponent_rows_per_target"]
            for timing in all_timing_rows
        ),
        "scalar_call_count": all(
            timing["opponent_calls"]
            == gates_config["expected_scalar_opponent_calls_per_arm"]
            for timing in all_timing_rows
            if timing["arm"] == "scalar"
        ),
        "batch_call_count": all(
            timing["batch_calls"]
            == gates_config["expected_batch_calls_per_arm"]
            for timing in all_timing_rows
            if timing["arm"] == "batched"
        ),
        "source_checkpoint_identity": all(
            row["source_checkpoint_identity"] for row in target_rows
        )
        == gates_config["require_source_checkpoint_identity"],
        "target_identity": all(row["target_identity"] for row in target_rows)
        == gates_config["require_target_identity"],
        "blueprint_identity": all(row["blueprint_identity"] for row in target_rows)
        == gates_config["require_blueprint_identity"],
        "warm_start_probability_error": maximum_probability_error
        <= gates_config["maximum_warm_start_probability_error"],
        "warm_start_mean_total_variation": maximum_mean_tv
        <= gates_config["maximum_warm_start_mean_total_variation"],
        "numeric_identity": maximum_numeric_error
        <= gates_config["maximum_numeric_error"],
        "composite_identity": maximum_composite_error
        <= gates_config["maximum_composite_error"],
        "structural_identity": all(
            row["identity"]["structural_identity"] for row in completed
        )
        == gates_config["require_structural_identity"],
        "five_opponent_rows": all(
            timing["opponent_rows"] == len(row["endpoint_rows"]) * 5
            for row in completed
            for timing in row["timing_rows"]
            if timing["arm"] == "batched"
        )
        == gates_config["require_exactly_five_opponent_rows_per_candidate"],
        "own_zero_contraction": all(
            row["own_rows_zero_contraction"] for row in target_rows
        )
        == gates_config["require_own_rows_zero_contraction"],
        "batch_safe_preflight": all(
            row["batch_safe_preflight"] for row in target_rows
        )
        == gates_config["require_batch_safe_preflight"],
        "search_step_ms": max(
            (row["search_step_ms"] for row in target_rows), default=math.inf
        )
        <= gates_config["maximum_search_step_ms"],
        "arm_wall_ms": max(
            (timing["wall_ms"] for timing in all_timing_rows), default=math.inf
        )
        <= gates_config["maximum_arm_wall_ms"],
        "gpu_pool": maximum_pool <= gates_config["maximum_gpu_pool_bytes"],
        "physical_free": minimum_free
        >= gates_config["minimum_postwork_physical_free_bytes"],
        "total_audit_seconds": total_seconds
        <= gates_config["maximum_total_audit_seconds"],
        "blueprint_emission": all(
            row["emitted_candidate_id"] == "blueprint_average64"
            and row["emitted_policy_sha256"] == row["blueprint_policy_sha256"]
            for row in target_rows
        )
        == gates_config["require_blueprint_emission"],
        "finite": v1._finite_tree(
            {"targets": target_rows, "seconds": total_seconds}
        )
        == gates_config["require_finite"],
        "strategy_population_claim_null": True
        == gates_config["require_strategy_population_claim_null"],
    }
    gates["passed"] = all(gates.values())
    speedups = [row["summary"]["opponent_speedup"] for row in completed]
    full_fit = [
        row["complete_six_block_ledger"]["full_six_block_set_fits"]
        for row in completed
    ]
    if not gates["passed"]:
        decision = "reject_tier_b_batch_v2_differential"
    elif all(full_fit):
        decision = "accept_full_six_block_b_to_c_path_on_retained_ledgers"
    elif speedups and statistics.median(speedups) > 1.0:
        decision = "accept_batch_primitive_but_continue_tier_b_optimization"
    else:
        decision = "retain_scalar_tier_b_path"

    result = {
        "schema_version": 2,
        "status": "h32_tier_b_opponent_batch_v2_differential_executed",
        "methodology": {
            "v1_science_reused_without_change": True,
            "source_pass_read_from_pinned_top_level_field": True,
            "retained_contexts_only": True,
            "strategy_labels_loaded": 0,
            "candidate_family": "regret_vertex",
            "scalar_teacher_calls_per_arm": 30,
            "batched_calls_per_arm": 6,
            "acting_seat_rows_charged_separately": True,
            "speed_and_full_set_fit_are_report_only": True,
            "immutable_blueprint_emission": True,
        },
        "environment": {
            **environment_metadata(),
            **runtime,
            "git": git,
        },
        "config_sha256": _sha256(config_path),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "v1_config_sha256": _sha256(v1._CONFIG),
        "v1_implementation_sha256": _sha256(v1._IMPLEMENTATION),
        "batch_implementation_sha256": _sha256(v1._BATCH_IMPLEMENTATION),
        "target_rows": target_rows,
        "aggregate": {
            "targets_completed": len(completed),
            "candidate_rows": sum(len(row["endpoint_rows"]) for row in completed),
            "opponent_rows_per_timing_arm": 30,
            "maximum_numeric_error": maximum_numeric_error if completed else None,
            "maximum_composite_error": (
                maximum_composite_error if completed else None
            ),
            "maximum_warm_start_probability_error": maximum_probability_error,
            "maximum_warm_start_mean_total_variation": maximum_mean_tv,
            "maximum_gpu_pool_bytes": maximum_pool,
            "minimum_gpu_free_bytes": minimum_free,
            "opponent_speedup_median_across_targets": (
                statistics.median(speedups) if speedups else None
            ),
            "opponent_speedup_minimum": min(speedups) if speedups else None,
            "opponent_speedup_maximum": max(speedups) if speedups else None,
            "full_six_block_fit_targets": sum(full_fit),
        },
        "gates": gates,
        "passed": gates["passed"],
        "decision": decision,
        "strategy_population_claim": None,
        "total_audit_seconds": total_seconds,
        "limitations": [
            "All six retained contexts were exposed before this engineering differential.",
            "No ADR-0186 or ADR-0206 strategy label is deserialized or joined.",
            "Observed timings are paired development measurements, not a latency distribution.",
            "The six-block library is small and cannot establish widened-corpus transfer.",
            "No strategy-quality, deployment, population, or hardware claim is authorized.",
        ],
    }
    output_path.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=_CONFIG)
    parser.add_argument("--output", type=Path, default=_OUTPUT)
    args = parser.parse_args()
    result = run_h32_tier_b_opponent_batch_v2_differential(
        args.config, args.output
    )
    print(
        json.dumps(
            {
                "output": str(args.output),
                "passed": result["passed"],
                "decision": result["decision"],
                "aggregate": result["aggregate"],
            },
            indent=2,
        )
    )
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
