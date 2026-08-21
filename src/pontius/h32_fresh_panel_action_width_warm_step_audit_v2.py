"""Aggregation-only correction for the ADR-0150 fresh-panel width audit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

from . import h32_fresh_panel_action_width_warm_step_audit as v1
from .reporting import environment_metadata


_ROOT = Path(__file__).parents[2]
_CONFIG = _ROOT / "experiments/configs/h32-fresh-panel-action-width-warm-step-v2.json"
_OUTPUT = _ROOT / "experiments/results/h32-fresh-panel-action-width-warm-step-v2.json"
_V1_CONFIG = _ROOT / "experiments/configs/h32-fresh-panel-action-width-warm-step-v1.json"
_V1_IMPLEMENTATION = _ROOT / "src/pontius/h32_fresh_panel_action_width_warm_step_audit.py"
_FAILED_ADR = _ROOT / "docs/decisions/ADR-0151-fresh-panel-action-width-run-rejected-by-profile-timing-aggregation-bug.md"
_IMPLEMENTATION = Path(__file__)
_CONTROL_TEST = _ROOT / "tests/test_h32_fresh_panel_action_width_warm_step_audit_v2.py"

_PATHS = {
    "expected_v1_config_sha256": _V1_CONFIG,
    "expected_v1_implementation_sha256": _V1_IMPLEMENTATION,
    "expected_failed_execution_adr_sha256": _FAILED_ADR,
    "expected_audit_implementation_sha256": _IMPLEMENTATION,
    "expected_control_test_sha256": _CONTROL_TEST,
}


def _sha256(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_h32_fresh_panel_action_width_warm_step_v2_config(
    config: dict[str, Any],
) -> dict[str, Any]:
    fields = {
        "evidence_stage", *tuple(_PATHS), "correction_scope", "outcome_policy",
    }
    if set(config) != fields:
        raise ValueError("corrected fresh-panel action-width fields differ from ADR-0152")
    expected = {
        "evidence_stage": "preregistered_after_adr0151_before_corrected_fresh_panel_action_width_rerun",
        "correction_scope": "post_work_aggregation_only_use_outer_profile_rows_for_timing_and_gpu_pool_and_inner_quality_rows_for_exactness_and_finiteness",
        "outcome_policy": "reuse_adr0150_targets_order_steps_candidates_common_game_caps_thresholds_and_null_claim_without_tuning",
    }
    for key, value in expected.items():
        if config[key] != value:
            raise ValueError(f"corrected fresh-panel action-width workload differs: {key}")
    for field, path in _PATHS.items():
        if config[field] != _sha256(path):
            raise ValueError(f"corrected fresh-panel action-width source mismatch: {field}")
    base_raw = json.loads(_V1_CONFIG.read_text(encoding="utf-8"))
    base = v1.parse_h32_fresh_panel_action_width_warm_step_config(base_raw)
    return {"base": base, **expected}


def _corrected_gate_results(local: dict[str, Any]) -> tuple[dict[str, bool], list[dict[str, Any]]]:
    targets = local["targets"]
    parsed = local["parsed"]
    gates = local["gates"]
    git = local["git"]
    parent_identity = local["parent_identity"]
    cache_parent = local["cache_parent"]
    total_seconds = local["total_seconds"]
    arm_rows = [
        target["arm_planning"][arm]
        for target in targets
        for arm in ("one_size", "two_size")
    ]
    profile_rows = [target["incumbent"] for target in targets]
    profile_rows += [
        target["candidates"][arm]
        for target in targets
        for arm in ("one_size", "two_size")
    ]
    quality_rows = [row["quality"] for row in profile_rows]
    gate_results = {
        "clean_git": (not git["dirty"]) == gates["require_clean_git_state"],
        "parent_identity": parent_identity == gates["require_parent_identity"],
        "cache_headroom_safe": cache_parent["headroom"]["all_twenty_four_caches_safe"] == gates["require_cache_headroom_safe"],
        "target_count": len(targets) == gates["expected_targets"],
        "arm_count": len(arm_rows) == gates["expected_arms"],
        "step_count": sum(row["complete_steps"] for row in arm_rows) == gates["expected_steps"],
        "quality_count": len(profile_rows) == gates["expected_complete_quality_profiles"],
        "source_target_identity": all(row["source_identity"] and row["target_identity"] for row in targets) == gates["require_target_identity"],
        "payoff_spans": all(row["one_size_payoff_span"] == parsed["expected_one_size_payoff_span"] and row["two_size_payoff_span"] == parsed["expected_two_size_payoff_span"] for row in targets),
        "warm_start_distance": all(row["warm_start_distance"]["mean_total_variation"] <= gates["maximum_warm_start_mean_tv"] for row in arm_rows),
        "step_ceiling": all(row["step"]["wall_ms"] <= gates["maximum_complete_step_ms"] for row in arm_rows),
        "cache_ceiling": all(row["cache"]["cold_construction_ms"] <= gates["maximum_cache_compile_ms"] for row in arm_rows) and all(row["verifier_cache"]["cold_construction_ms"] <= gates["maximum_cache_compile_ms"] for row in targets),
        "quality_ceiling": all(row["wall_ms"] <= gates["maximum_quality_ms"] for row in profile_rows),
        "gpu_pool": max([row["cache"]["pool_total_bytes"] for row in arm_rows] + [row["step"]["maximum_gpu_pool_bytes"] for row in arm_rows] + [row["verifier_cache"]["pool_total_bytes"] for row in targets] + [row["maximum_gpu_pool_bytes"] for row in profile_rows]) <= gates["maximum_gpu_pool_bytes"],
        "compact_round_trip": all(row["compact_round_trip"] for row in arm_rows) == gates["require_compact_round_trip"],
        "planning_before_quality": all(row["planning_finished_before_quality"] for row in targets) == gates["require_planning_before_quality"],
        "quality_exactness": all(row["quality_vector_sum_error"] <= gates["maximum_quality_vector_sum_error"] and row["zero_sum_residual"] <= gates["maximum_zero_sum_residual"] for row in quality_rows),
        "fixed_envelope_cap_compliance": all((selection["selected_candidate_id"] == "immutable_embedded_source_average64") or selection["candidate_cap_diagnostics"]["feasible"] for target in targets for selection in target["selections"].values()) == gates["require_fixed_envelope_cap_compliance"],
        "finite": (all(row["finite"] for row in arm_rows) and all(row["finite"] for row in quality_rows)) == gates["require_finite"],
        "total_time": total_seconds <= gates["maximum_total_seconds"],
        "strategy_claim_null": (None is None) == gates["require_strategy_claim_null"],
    }
    return gate_results, profile_rows


def run_h32_fresh_panel_action_width_warm_step_v2_audit(
    config_path: Path = _CONFIG, output_path: Path = _OUTPUT,
) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    parse_h32_fresh_panel_action_width_warm_step_v2_config(config)
    captured: dict[str, Any] = {}

    def trace(frame: Any, event: str, argument: Any) -> Any:
        if event == "exception" and frame.f_code.co_name == "run_h32_fresh_panel_action_width_warm_step_audit":
            error_type, error, _traceback = argument
            if error_type is KeyError and error.args == ("wall_ms",):
                captured.update(frame.f_locals)
        return trace

    sys.settrace(trace)
    try:
        v1.run_h32_fresh_panel_action_width_warm_step_audit(
            _V1_CONFIG, output_path,
        )
    except KeyError as error:
        if error.args != ("wall_ms",) or not captured:
            raise
    else:
        raise RuntimeError("ADR-0150 unexpectedly did not reproduce its frozen aggregation failure")
    finally:
        sys.settrace(None)

    gate_results, profile_rows = _corrected_gate_results(captured)
    passed = all(gate_results.values())
    targets = captured["targets"]
    total_seconds = captured["total_seconds"]
    git = captured["git"]
    result = {
        "schema_version": 2,
        "status": "corrected_h32_fresh_panel_action_width_warm_step_executed",
        "experiment_type": "all_target_one_step_common_game_action_width_diagnostic",
        "config": config,
        "config_sha256": _sha256(config_path),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "reused_v1_config_sha256": _sha256(_V1_CONFIG),
        "reused_v1_implementation_sha256": _sha256(_V1_IMPLEMENTATION),
        "correction": {
            "scope": config["correction_scope"],
            "reproduced_v1_terminal_error": "KeyError: wall_ms",
            "workload_or_outcome_rule_changed": False,
        },
        "environment": {
            **environment_metadata(), "git": git, "runtime": captured["runtime"],
        },
        "parent_identity": captured["parent_identity"],
        "small_control": captured["small"],
        "targets": targets,
        "gate_results": gate_results,
        "passed": passed,
        "strategy_quality_claim": None,
        "decision": "record_claim_null_fresh_panel_action_width_diagnostic" if passed else "reject_corrected_fresh_panel_action_width_mechanism",
        "work_accounting": {
            "h32_one_size_steps": 12,
            "h32_two_size_steps": 12,
            "h32_widened_quality_profiles": len(profile_rows),
            "targets_filtered_by_prior_outcome": 0,
        },
        "timing": {"total_seconds": total_seconds},
        "limitations": [
            "The audit reports paired one-step diagnostics and makes no strategy-quality or action-width ranking claim.",
            "Each arm is separately certified against the same immutable embedded source blueprint; no selected candidate becomes a future anchor.",
            "ADR-0149 is disclosed and pinned but cannot filter targets, alter order, or define a gate.",
            "ADR-0152 changes only aggregate row selection after reproducing ADR-0150's frozen terminal KeyError.",
        ],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
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
    result = run_h32_fresh_panel_action_width_warm_step_v2_audit(args.config, args.output)
    print(f"corrected fresh-panel action-width warm step: passed={result['passed']}, wall={result['timing']['total_seconds']:.3f}s")


if __name__ == "__main__":
    main()
