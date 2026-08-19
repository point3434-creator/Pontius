"""Compare exact safe-strategy objectives in two-player Kuhn poker."""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict
from math import isfinite
from pathlib import Path
from typing import Any

from .evaluation import EvaluationResult, Policy, evaluate_profile
from .game import Action
from .leaf_experiment import (
    PreparedBlueprint,
    SOLVERS,
    _policy_distance,
    _resolved_information_sets,
    prepare_blueprint,
)
from .maxmargin import (
    ConstrainedContinualResolveResult,
    MaxMarginContinualResolveResult,
    resolve_all_public_histories_best_response,
    resolve_all_public_histories_maxmargin,
    resolve_all_public_histories_sum_margin,
)
from .reporting import environment_metadata


def _safe_rate(improvement: float, seconds: float) -> float | None:
    return improvement / (1_000.0 * seconds) if seconds > 0.0 else None


def _candidate_record(
    evaluation: EvaluationResult,
    policy: Policy,
    blueprint: Policy,
    blueprint_evaluation: EvaluationResult,
    information_sets: dict[str, tuple[Action, ...]],
    decision_compute_seconds: float,
    exploitability_increase_bound: float,
) -> dict[str, Any]:
    blueprint_exploitability = blueprint_evaluation.exploitability
    candidate_exploitability = evaluation.exploitability
    if blueprint_exploitability is None or candidate_exploitability is None:
        raise ValueError("safe oracle experiment requires two-player evaluation")
    improvement = blueprint_evaluation.nash_conv - evaluation.nash_conv
    bound_slack = (
        blueprint_exploitability
        + exploitability_increase_bound
        - candidate_exploitability
    )
    return {
        **asdict(evaluation),
        "nash_conv_improvement_over_blueprint": improvement,
        "nash_conv_delta_from_blueprint": -improvement,
        "policy_distance_from_blueprint": _policy_distance(
            policy,
            blueprint,
            information_sets,
        ),
        "decision_compute_seconds": decision_compute_seconds,
        "nash_conv_improvement_per_decision_compute_millisecond": _safe_rate(
            improvement,
            decision_compute_seconds,
        ),
        "exploitability_increase_bound": exploitability_increase_bound,
        "residual_adjusted_bound_slack": bound_slack,
        "residual_adjusted_bound_holds": bound_slack >= -1e-10,
    }


def _max_min_summary(
    result: MaxMarginContinualResolveResult,
    evaluation: EvaluationResult,
    blueprint: Policy,
    blueprint_evaluation: EvaluationResult,
    information_sets: dict[str, tuple[Action, ...]],
) -> dict[str, Any]:
    return {
        "objective_name": "minimum_frontier_margin",
        "full_game_target_used": False,
        "structural_public_histories": result.structural_public_histories,
        "searched_public_histories": result.searched_public_histories,
        "skipped_zero_counterfactual_reach_histories": [
            list(history)
            for history in result.skipped_zero_counterfactual_reach_histories
        ],
        "total_oracle_seconds": result.total_oracle_seconds,
        "expected_oracle_seconds_per_hand": result.expected_oracle_seconds_per_hand,
        "expected_public_decisions_per_hand": (
            result.expected_public_decisions_per_hand
        ),
        "cumulative_exploitability_increase_bound": (
            result.cumulative_exploitability_increase_bound
        ),
        "reach_weighted_objective_value": result.reach_weighted_max_margin,
        "records": [asdict(record) for record in result.records],
        "candidate": _candidate_record(
            evaluation,
            result.policy,
            blueprint,
            blueprint_evaluation,
            information_sets,
            result.expected_oracle_seconds_per_hand,
            result.cumulative_exploitability_increase_bound,
        ),
    }


def _constrained_summary(
    result: ConstrainedContinualResolveResult,
    evaluation: EvaluationResult,
    blueprint: Policy,
    blueprint_evaluation: EvaluationResult,
    information_sets: dict[str, tuple[Action, ...]],
) -> dict[str, Any]:
    return {
        "objective_name": result.objective_name,
        "full_game_target_used": result.full_game_target_used,
        "structural_public_histories": result.structural_public_histories,
        "searched_public_histories": result.searched_public_histories,
        "skipped_zero_counterfactual_reach_histories": [
            list(history)
            for history in result.skipped_zero_counterfactual_reach_histories
        ],
        "total_oracle_seconds": result.total_oracle_seconds,
        "expected_oracle_seconds_per_hand": result.expected_oracle_seconds_per_hand,
        "expected_public_decisions_per_hand": (
            result.expected_public_decisions_per_hand
        ),
        "cumulative_exploitability_increase_bound": (
            result.cumulative_exploitability_increase_bound
        ),
        "total_verified_objective_value": (
            result.total_verified_objective_value
        ),
        "reach_weighted_objective_value": result.reach_weighted_objective_value,
        "records": [asdict(record) for record in result.records],
        "candidate": _candidate_record(
            evaluation,
            result.policy,
            blueprint,
            blueprint_evaluation,
            information_sets,
            result.expected_oracle_seconds_per_hand,
            result.cumulative_exploitability_increase_bound,
        ),
    }


def run_safe_oracle_experiment(
    config: dict[str, Any],
    *,
    prepared_blueprint: PreparedBlueprint | None = None,
    environment: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compare max-min, target-free sum-margin, and hidden-target controls."""

    game_name = str(config.get("game", "kuhn2"))
    blueprint_solver_name = str(config.get("blueprint_solver", "lcfr"))
    blueprint_iterations = int(config.get("blueprint_iterations", 1_000))
    max_pure_plans = int(config.get("max_pure_plans", 1_000_000))
    tolerance = float(config.get("tolerance", 1e-10))
    if game_name != "kuhn2":
        raise ValueError("safe oracle experiment currently requires kuhn2")
    if blueprint_solver_name not in SOLVERS:
        raise ValueError(f"unsupported blueprint solver {blueprint_solver_name!r}")
    if blueprint_iterations <= 0 or max_pure_plans <= 0:
        raise ValueError("blueprint iterations and max_pure_plans must be positive")
    if not isfinite(tolerance) or tolerance <= 0.0:
        raise ValueError("tolerance must be finite and positive")

    wall_start = time.perf_counter()
    blueprint_prepared_in_run = prepared_blueprint is None
    if prepared_blueprint is None:
        prepared_blueprint = prepare_blueprint(
            game_name,
            blueprint_solver_name,
            blueprint_iterations,
        )
    elif (
        prepared_blueprint.game_name != game_name
        or prepared_blueprint.solver_name != blueprint_solver_name
        or prepared_blueprint.iterations != blueprint_iterations
    ):
        raise ValueError("prepared blueprint does not match safe oracle configuration")

    game = prepared_blueprint.game
    blueprint = prepared_blueprint.policy
    blueprint_evaluation = prepared_blueprint.evaluation
    information_sets = _resolved_information_sets(game)
    max_min = resolve_all_public_histories_maxmargin(
        game,
        blueprint,
        max_pure_plans=max_pure_plans,
        tolerance=tolerance,
    )
    sum_margin = resolve_all_public_histories_sum_margin(
        game,
        blueprint,
        max_pure_plans=max_pure_plans,
        tolerance=tolerance,
    )
    hidden_best_response = resolve_all_public_histories_best_response(
        game,
        blueprint,
        max_pure_plans=max_pure_plans,
        tolerance=tolerance,
    )

    evaluation_start = time.perf_counter()
    max_min_evaluation = evaluate_profile(game, max_min.policy)
    sum_margin_evaluation = evaluate_profile(game, sum_margin.policy)
    hidden_evaluation = evaluate_profile(game, hidden_best_response.policy)
    evaluation_seconds = time.perf_counter() - evaluation_start
    max_min_summary = _max_min_summary(
        max_min,
        max_min_evaluation,
        blueprint,
        blueprint_evaluation,
        information_sets,
    )
    sum_margin_summary = _constrained_summary(
        sum_margin,
        sum_margin_evaluation,
        blueprint,
        blueprint_evaluation,
        information_sets,
    )
    hidden_summary = _constrained_summary(
        hidden_best_response,
        hidden_evaluation,
        blueprint,
        blueprint_evaluation,
        information_sets,
    )
    max_min_gain = max_min_summary["candidate"][
        "nash_conv_improvement_over_blueprint"
    ]
    sum_margin_gain = sum_margin_summary["candidate"][
        "nash_conv_improvement_over_blueprint"
    ]
    hidden_gain = hidden_summary["candidate"][
        "nash_conv_improvement_over_blueprint"
    ]

    result = {
        "schema_version": 1,
        "experiment_type": "exact_safe_strategy_objectives",
        "config": {
            "game": game_name,
            "blueprint_solver": blueprint_solver_name,
            "blueprint_iterations": blueprint_iterations,
            "max_pure_plans": max_pure_plans,
            "tolerance": tolerance,
        },
        "environment": environment_metadata() if environment is None else environment,
        "protocol": {
            "frontier": "exact opponent counterfactual best-response values",
            "strategy_space": "enumerated pure plans converted to behavioral policy",
            "max_min_target": "minimum opponent-frontier safety margin",
            "sum_margin_target": "sum of per-frontier worst-case safety margins",
            "sum_margin_uses_full_game_target": False,
            "hidden_control_target": "current full-game opponent best-response reduction",
            "hidden_control_is_greedy_across_public_boundaries": True,
            "hidden_control_is_deployable": False,
            "all_replacements_frontier_safe": True,
            "multiplayer_claim": False,
        },
        "timing": {
            "blueprint_prepared_in_run": blueprint_prepared_in_run,
            "blueprint_solver_seconds": prepared_blueprint.solver_seconds,
            "blueprint_full_evaluation_seconds": (
                prepared_blueprint.evaluation_seconds
            ),
            "candidate_full_evaluation_seconds": evaluation_seconds,
        },
        "blueprint": asdict(blueprint_evaluation),
        "max_min": max_min_summary,
        "sum_margin": sum_margin_summary,
        "hidden_best_response_greedy": hidden_summary,
        "paired": {
            "sum_margin_minus_max_min_nash_conv_improvement": (
                sum_margin_gain - max_min_gain
            ),
            "hidden_minus_sum_margin_nash_conv_improvement": (
                hidden_gain - sum_margin_gain
            ),
            "sum_margin_fraction_of_hidden_improvement": (
                sum_margin_gain / hidden_gain if hidden_gain > tolerance else None
            ),
            "max_min_fraction_of_hidden_improvement": (
                max_min_gain / hidden_gain if hidden_gain > tolerance else None
            ),
        },
    }
    result["timing"]["wall_seconds"] = time.perf_counter() - wall_start
    return result


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    config = (
        {}
        if args.config is None
        else json.loads(args.config.read_text(encoding="utf-8"))
    )
    result = run_safe_oracle_experiment(config)
    rendered = json.dumps(result, indent=2, sort_keys=True, allow_nan=False)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    max_min_gain = result["max_min"]["candidate"][
        "nash_conv_improvement_over_blueprint"
    ]
    sum_gain = result["sum_margin"]["candidate"][
        "nash_conv_improvement_over_blueprint"
    ]
    hidden_gain = result["hidden_best_response_greedy"]["candidate"][
        "nash_conv_improvement_over_blueprint"
    ]
    print(
        f"safe objective oracle on {result['config']['game']}: "
        f"max-min={max_min_gain:.8g}, "
        f"sum={sum_gain:.8g}, hidden={hidden_gain:.8g}"
    )
    if args.output is not None:
        print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
