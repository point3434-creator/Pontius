"""Preregistered finite control for one-seat convex row generation."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path
import time
from typing import Any

from .evaluation import evaluate_profile
from .h32_affine_resident_cache_preflight import _strict_git_metadata
from .leaf_experiment import prepare_blueprint
from .kuhn import KuhnPoker
from .one_seat_convex_generation import (
    path_single_visit_report,
    require_behavioral_affine_shortcut,
    retreat_one_seat_policy,
    solve_one_seat_complete_normal_form_teacher,
    solve_one_seat_with_row_generation,
)
from .real_policy import policy_digest
from .runner_harness import (
    assemble_environment,
    finalize_gates,
    serialize_result,
)


_ROOT = Path(__file__).parents[2]
_CONFIG = _ROOT / "experiments/configs/one-seat-convex-keystone-v1.json"
_OUTPUT = _ROOT / "experiments/results/one-seat-convex-keystone-v1.json"
_PARENT = (
    _ROOT
    / "docs/decisions/ADR-0239-reject-cross-payoff-v1-on-external-axis-key-mismatch.md"
)
_PRIMITIVE = _ROOT / "src/pontius/one_seat_convex_generation.py"
_PRIMITIVE_TEST = _ROOT / "tests/test_one_seat_convex_generation.py"
_PROOF = _ROOT / "docs/one-seat-convex-generation.md"
_IMPLEMENTATION = Path(__file__)
_TEST = _ROOT / "tests/test_one_seat_convex_keystone.py"

_PATHS = {
    "expected_parent_decision_sha256": _PARENT,
    "expected_primitive_sha256": _PRIMITIVE,
    "expected_primitive_test_sha256": _PRIMITIVE_TEST,
    "expected_proof_sha256": _PROOF,
    "expected_implementation_sha256": _IMPLEMENTATION,
    "expected_control_test_sha256": _TEST,
}


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required convex-keystone input is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _parse_config(config: dict[str, Any]) -> dict[str, Any]:
    expected = {
        "evidence_stage",
        *_PATHS,
        "game",
        "blueprint_solver",
        "blueprint_iterations",
        "acting_players",
        "guard",
        "retreat_factor",
        "max_iterations",
        "max_pure_plans",
        "tolerance",
        "claims_policy",
        "gates",
    }
    if set(config) != expected:
        raise ValueError("convex-keystone config fields differ from ADR-0240")
    for field, path in _PATHS.items():
        if config[field] != _sha256(path):
            raise ValueError(f"convex-keystone provenance mismatch: {field}")
    frozen = {
        "evidence_stage": "preregistered_after_adr0239_before_frozen_keystone_run",
        "game": "kuhn2",
        "blueprint_solver": "lcfr",
        "blueprint_iterations": 37,
        "acting_players": [0, 1],
        "guard": 0.25,
        "retreat_factor": 0.8,
        "max_iterations": 128,
        "max_pure_plans": 1000,
        "tolerance": 1e-10,
        "claims_policy": "finite_algebra_control_only_no_strategy_quality_claim",
    }
    for field, value in frozen.items():
        if config[field] != value:
            raise ValueError(f"convex-keystone field differs from ADR-0240: {field}")
    expected_gates = {
        "expected_acting_seats": 2,
        "expected_acting_pure_plans": 64,
        "expected_opponent_pure_plans": 64,
        "maximum_teacher_objective_error": 1e-9,
        "maximum_exact_incumbent_error": 1e-9,
        "maximum_final_optimality_gap": 1e-9,
        "maximum_retreat_jensen_error": 1e-9,
        "maximum_realization_equivalence_error": 1e-9,
        "maximum_total_seconds": 60.0,
        "require_clean_git_state": True,
        "require_repeated_actor_topology": True,
        "require_behavioral_shortcut_rejection": True,
        "require_all_opponent_multi_cut_control": True,
        "require_safe_timeout_incumbent": True,
        "require_bound_monotonicity": True,
        "require_exact_digest_dedup_only": True,
        "require_independent_certificate": True,
        "require_finite": True,
    }
    if config["gates"] != expected_gates:
        raise ValueError("convex-keystone gates differ from ADR-0240")
    return {**config, "acting_players": tuple(config["acting_players"])}


def _finite_tree(value: Any) -> bool:
    if isinstance(value, bool) or value is None or isinstance(value, str):
        return True
    if isinstance(value, (int, float)):
        return math.isfinite(float(value))
    if isinstance(value, dict):
        return all(_finite_tree(key) and _finite_tree(item) for key, item in value.items())
    if isinstance(value, (list, tuple)):
        return all(_finite_tree(item) for item in value)
    return False


def _monotone(values: list[float], *, increasing: bool, tolerance: float) -> bool:
    return all(
        (right + tolerance >= left if increasing else right <= left + tolerance)
        for left, right in zip(values, values[1:])
    )


def mutation_controls(tolerance: float) -> dict[str, Any]:
    """Cheap controls for shortcut rejection, multi-cut, and timeout safety."""

    game = KuhnPoker(2)
    shortcut_rejected = False
    try:
        require_behavioral_affine_shortcut(game)
    except ValueError:
        shortcut_rejected = True

    multi = solve_one_seat_with_row_generation(
        KuhnPoker(3),
        {},
        acting_player=0,
        guard=1.0,
        max_iterations=1,
        tolerance=tolerance,
    )
    timeout = solve_one_seat_with_row_generation(
        game,
        {},
        acting_player=0,
        guard=0.25,
        max_iterations=1,
        tolerance=tolerance,
    )
    timeout_evaluation = evaluate_profile(game, timeout.policy)
    timeout_safe = all(
        gain <= cap + 100.0 * tolerance
        for gain, cap in zip(
            timeout_evaluation.deviation_gains,
            timeout.caps,
            strict=True,
        )
    )
    return {
        "behavioral_shortcut_rejected": shortcut_rejected,
        "multi_cut_added_targets": list(multi.iterations[0].added_targets),
        "all_opponents_added_in_one_round": multi.iterations[0].added_targets == (1, 2),
        "timeout_converged": timeout.converged,
        "timeout_safe_incumbent": timeout_safe,
        "timeout_bound_orientation_correct": abs(
            timeout.optimality_gap - (timeout.upper_bound - timeout.lower_bound)
        )
        <= 100.0 * tolerance,
    }


def _run_acting_seat(
    parsed: dict[str, Any],
    blueprint: Any,
    acting_player: int,
) -> dict[str, Any]:
    generated_start = time.perf_counter()
    generated = solve_one_seat_with_row_generation(
        blueprint.game,
        blueprint.policy,
        acting_player=acting_player,
        guard=float(parsed["guard"]),
        max_iterations=int(parsed["max_iterations"]),
        tolerance=float(parsed["tolerance"]),
    )
    generated_seconds = time.perf_counter() - generated_start

    teacher_start = time.perf_counter()
    teacher = solve_one_seat_complete_normal_form_teacher(
        blueprint.game,
        blueprint.policy,
        acting_player=acting_player,
        guard=float(parsed["guard"]),
        max_pure_plans=int(parsed["max_pure_plans"]),
        tolerance=float(parsed["tolerance"]),
    )
    teacher_seconds = time.perf_counter() - teacher_start

    incumbent = evaluate_profile(blueprint.game, generated.policy)
    retreated_policy = retreat_one_seat_policy(
        blueprint.game,
        blueprint.policy,
        generated.policy,
        acting_player=acting_player,
        factor=float(parsed["retreat_factor"]),
        tolerance=float(parsed["tolerance"]),
    )
    retreated = evaluate_profile(blueprint.game, retreated_policy)
    factor = float(parsed["retreat_factor"])
    per_seat_jensen_errors = [
        mixed - ((1.0 - factor) * source + factor * endpoint)
        for mixed, source, endpoint in zip(
            retreated.deviation_gains,
            blueprint.evaluation.deviation_gains,
            incumbent.deviation_gains,
            strict=True,
        )
    ]
    objective_jensen_error = retreated.nash_conv - (
        (1.0 - factor) * blueprint.evaluation.nash_conv
        + factor * incumbent.nash_conv
    )
    lower_bounds = [update.master_lower_bound for update in generated.iterations]
    upper_bounds = [update.incumbent_upper_bound for update in generated.iterations]
    maximum_realization_error = max(
        update.realization_equivalence_max_error
        for update in generated.iterations
    )
    return {
        "acting_player": acting_player,
        "generated_seconds": generated_seconds,
        "teacher_seconds": teacher_seconds,
        "converged": generated.converged,
        "iterations": len(generated.iterations),
        "baseline_nash_conv": generated.baseline_nash_conv,
        "master_lower_bound": generated.lower_bound,
        "safe_incumbent_upper_bound": generated.upper_bound,
        "optimality_gap": generated.optimality_gap,
        "independent_incumbent_nash_conv": incumbent.nash_conv,
        "complete_teacher_objective": teacher.objective,
        "teacher_exact_nash_conv": teacher.exact_nash_conv,
        "teacher_objective_error": abs(teacher.objective - generated.upper_bound),
        "exact_incumbent_error": abs(incumbent.nash_conv - generated.upper_bound),
        "acting_pure_plans": teacher.acting_pure_plans,
        "response_pure_plans": list(teacher.response_pure_plans),
        "generated_response_rows_by_player": list(generated.response_rows_by_player),
        "exact_duplicate_response_hits": generated.exact_duplicate_response_hits,
        "conditioning_by_player": [
            asdict(row) for row in generated.conditioning_by_player
        ],
        "lower_bounds_monotone": _monotone(
            lower_bounds,
            increasing=True,
            tolerance=float(parsed["tolerance"]),
        ),
        "upper_bounds_monotone": _monotone(
            upper_bounds,
            increasing=False,
            tolerance=float(parsed["tolerance"]),
        ),
        "maximum_realization_equivalence_error": maximum_realization_error,
        "maximum_retreat_jensen_error": max(
            0.0,
            objective_jensen_error,
            *per_seat_jensen_errors,
        ),
        "retreated_nash_conv": retreated.nash_conv,
        "blueprint_policy_sha256": policy_digest(blueprint.policy),
        "incumbent_policy_sha256": policy_digest(generated.policy),
        "retreated_policy_sha256": policy_digest(retreated_policy),
        "iteration_rows": [asdict(update) for update in generated.iterations],
    }


def run_one_seat_convex_keystone(
    config_path: Path = _CONFIG,
    output_path: Path = _OUTPUT,
) -> dict[str, Any]:
    started = time.perf_counter()
    parsed = _parse_config(json.loads(config_path.read_text(encoding="utf-8")))
    git = _strict_git_metadata()
    blueprint = prepare_blueprint(
        parsed["game"],
        parsed["blueprint_solver"],
        int(parsed["blueprint_iterations"]),
    )
    topology = path_single_visit_report(blueprint.game)
    controls = mutation_controls(float(parsed["tolerance"]))
    rows = [
        _run_acting_seat(parsed, blueprint, acting_player)
        for acting_player in parsed["acting_players"]
    ]
    total_seconds = time.perf_counter() - started
    gates = parsed["gates"]
    expected_opponents = [
        [
            count
            for player, count in enumerate(row["response_pure_plans"])
            if player != row["acting_player"]
        ]
        for row in rows
    ]
    checks = {
        "clean_git": (not git["dirty"]) == gates["require_clean_git_state"],
        "acting_seat_count": len(rows) == gates["expected_acting_seats"],
        "repeated_actor_topology": (not topology.passed)
        == gates["require_repeated_actor_topology"],
        "behavioral_shortcut_rejection": controls["behavioral_shortcut_rejected"]
        == gates["require_behavioral_shortcut_rejection"],
        "all_opponent_multi_cut_control": controls["all_opponents_added_in_one_round"]
        == gates["require_all_opponent_multi_cut_control"],
        "safe_timeout_incumbent": (
            controls["timeout_safe_incumbent"]
            and controls["timeout_bound_orientation_correct"]
        )
        == gates["require_safe_timeout_incumbent"],
        "complete_teacher_counts": all(
            row["acting_pure_plans"] == gates["expected_acting_pure_plans"]
            and counts == [gates["expected_opponent_pure_plans"]]
            for row, counts in zip(rows, expected_opponents, strict=True)
        ),
        "teacher_objective_identity": all(
            row["teacher_objective_error"]
            <= gates["maximum_teacher_objective_error"]
            for row in rows
        ),
        "exact_incumbent_identity": all(
            row["exact_incumbent_error"]
            <= gates["maximum_exact_incumbent_error"]
            for row in rows
        )
        == gates["require_independent_certificate"],
        "global_gap": all(
            row["converged"]
            and row["optimality_gap"] <= gates["maximum_final_optimality_gap"]
            for row in rows
        ),
        "retreat_jensen": all(
            row["maximum_retreat_jensen_error"]
            <= gates["maximum_retreat_jensen_error"]
            for row in rows
        ),
        "realization_equivalence": all(
            row["maximum_realization_equivalence_error"]
            <= gates["maximum_realization_equivalence_error"]
            for row in rows
        ),
        "bound_monotonicity": all(
            row["lower_bounds_monotone"] and row["upper_bounds_monotone"]
            for row in rows
        )
        == gates["require_bound_monotonicity"],
        "exact_digest_dedup_only": all(
            row["exact_duplicate_response_hits"] == 0 for row in rows
        )
        == gates["require_exact_digest_dedup_only"],
        "total_time": total_seconds <= gates["maximum_total_seconds"],
    }
    preliminary = {
        "topology": asdict(topology),
        "mutation_controls": controls,
        "acting_seat_rows": rows,
    }
    checks["finite"] = _finite_tree(preliminary) == gates["require_finite"]
    gate_result = finalize_gates(checks)
    result = {
        "schema_version": 1,
        "status": "one_seat_convex_keystone_executed",
        "environment": assemble_environment(
            runtime={"backend": "cpu_float64_exact_small_game"},
            git=git,
        ),
        "config_sha256": _sha256(config_path),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "primitive_sha256": _sha256(_PRIMITIVE),
        "methodology": {
            "game": parsed["game"],
            "blueprint_solver": parsed["blueprint_solver"],
            "blueprint_iterations": parsed["blueprint_iterations"],
            "acting_players": list(parsed["acting_players"]),
            "guard": parsed["guard"],
            "retreat_factor": parsed["retreat_factor"],
            "generated_coordinates": "sequence_form_realization",
            "teacher_coordinates": "complete_mixed_normal_form",
            "cut_policy": "all_violated_opponent_epigraph_rows_per_iteration",
            "row_deduplication": "exact_response_signature_only",
            "timeout_policy": "best_independently_certified_feasible_incumbent",
            "gap_definition": "safe_incumbent_upper_bound_minus_master_lower_bound",
        },
        **preliminary,
        **gate_result,
        "decision": (
            "authorize_h4_open_axis_cut_extraction_differential"
            if gate_result["passed"]
            else "reject_one_seat_convex_row_generation_keystone"
        ),
        "total_seconds": total_seconds,
        "strategy_quality_claim": None,
        "limitations": [
            "This is a finite algebra and optimization control, not a poker-strength result.",
            "The complete teacher is tractable only because Kuhn2 has 64 pure plans per seat.",
            (
                "A pass does not price h4 or h32 cut extraction, cut count, "
                "conditioning, or the 15-second ledger."
            ),
            (
                "The exact evaluator remains emission authority; the restricted "
                "master never authorizes an unchecked policy."
            ),
        ],
    }
    output_path.write_text(serialize_result(result), encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=_CONFIG)
    parser.add_argument("--output", type=Path, default=_OUTPUT)
    args = parser.parse_args()
    result = run_one_seat_convex_keystone(args.config, args.output)
    print(
        json.dumps(
            {
                "output": str(args.output),
                "passed": result["passed"],
                "decision": result["decision"],
                "total_seconds": result["total_seconds"],
            },
            indent=2,
        )
    )
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
