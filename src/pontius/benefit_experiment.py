"""Exact-leaf experiments for resolver-benefit signal discovery."""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict
from math import isfinite
from pathlib import Path
from typing import Any

from .depth_limited import DepthLimitedGame, PolicyContinuationValues
from .evaluation import (
    CounterfactualRegretResult,
    EvaluationResult,
    Policy,
    counterfactual_regret_profile,
    evaluate_profile,
)
from .leaf_experiment import (
    PreparedBlueprint,
    SOLVERS,
    _policy_distance,
    _resolved_information_sets,
    _run_search,
    prepare_blueprint,
)
from .policy import interpolate_policy
from .reporting import environment_metadata


def _evaluation_summary(evaluation: EvaluationResult) -> dict[str, Any]:
    return asdict(evaluation)


def _regret_summary(result: CounterfactualRegretResult) -> dict[str, Any]:
    return asdict(result)


def _utility_mismatch(
    local: EvaluationResult,
    full: EvaluationResult,
) -> float:
    return max(
        abs(local_value - full_value)
        for local_value, full_value in zip(
            local.utilities,
            full.utilities,
            strict=True,
        )
    )


def _zero_safe_ratio(numerator: float, denominator: float) -> float:
    if denominator > 0.0:
        return numerator / denominator
    if abs(numerator) <= 1e-15:
        return 0.0
    raise ValueError("nonzero signal numerator has a zero normalization")


def run_benefit_experiment(
    config: dict[str, Any],
    *,
    prepared_blueprint: PreparedBlueprint | None = None,
    environment: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Measure model-only benefit signals against full-game improvement."""

    game_name = str(config.get("game", "kuhn2"))
    blueprint_solver_name = str(config.get("blueprint_solver", "lcfr"))
    blueprint_iterations = int(config.get("blueprint_iterations", 1_000))
    search_solver_name = str(config.get("search_solver", "lcfr"))
    search_iterations = int(config.get("search_iterations", 100))
    probe_iterations = int(config.get("probe_iterations", 5))
    depth_limit = int(config.get("depth_limit", 2))
    in_search_blueprint_weight = float(
        config.get("in_search_blueprint_weight", 0.99)
    )
    output_candidate_weight = float(config.get("output_candidate_weight", 1.0))
    raw_warm_start = config.get("warm_start_regret_mass")
    warm_start_regret_mass = (
        None if raw_warm_start is None else float(raw_warm_start)
    )

    if blueprint_solver_name not in SOLVERS:
        raise ValueError(f"unsupported blueprint solver {blueprint_solver_name!r}")
    if search_solver_name not in SOLVERS:
        raise ValueError(f"unsupported search solver {search_solver_name!r}")
    if blueprint_iterations <= 0:
        raise ValueError("blueprint_iterations must be positive")
    if search_iterations <= 0 or probe_iterations <= 0:
        raise ValueError("search and probe iterations must be positive")
    if depth_limit < 1:
        raise ValueError("depth_limit must be at least one")
    if not isfinite(in_search_blueprint_weight) or not (
        0.0 <= in_search_blueprint_weight <= 1.0
    ):
        raise ValueError("in_search_blueprint_weight must be finite and in [0, 1]")
    if not isfinite(output_candidate_weight) or not (
        0.0 <= output_candidate_weight <= 1.0
    ):
        raise ValueError("output_candidate_weight must be finite and in [0, 1]")
    if warm_start_regret_mass is not None and (
        not isfinite(warm_start_regret_mass) or warm_start_regret_mass <= 0.0
    ):
        raise ValueError("warm_start_regret_mass must be finite and positive")

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
        raise ValueError("prepared blueprint does not match benefit configuration")

    game = prepared_blueprint.game
    blueprint = prepared_blueprint.policy
    full_blueprint_evaluation = prepared_blueprint.evaluation
    exact_leaves = PolicyContinuationValues(game.num_players, blueprint)
    model_game = DepthLimitedGame(game, depth_limit, exact_leaves)
    information_sets = _resolved_information_sets(model_game)

    signal_start = time.perf_counter()
    blueprint_regret = counterfactual_regret_profile(model_game, blueprint)
    blueprint_model_evaluation = evaluate_profile(model_game, blueprint)
    blueprint_signal_seconds = time.perf_counter() - signal_start

    probe_solver, probe_init_seconds, probe_iteration_seconds = _run_search(
        model_game,
        search_solver_name,
        probe_iterations,
        blueprint,
        warm_start_regret_mass,
        in_search_blueprint_weight,
    )
    full_solver, full_init_seconds, full_iteration_seconds = _run_search(
        model_game,
        search_solver_name,
        search_iterations,
        blueprint,
        warm_start_regret_mass,
        in_search_blueprint_weight,
    )

    policy_start = time.perf_counter()
    probe_policy = interpolate_policy(
        blueprint,
        probe_solver.average_strategy(),
        information_sets,
        output_candidate_weight,
    )
    full_policy = interpolate_policy(
        blueprint,
        full_solver.average_strategy(),
        information_sets,
        output_candidate_weight,
    )
    probe_policy_distance = _policy_distance(
        probe_policy,
        blueprint,
        information_sets,
    )
    full_policy_distance = _policy_distance(
        full_policy,
        blueprint,
        information_sets,
    )
    policy_seconds = time.perf_counter() - policy_start

    model_evaluation_start = time.perf_counter()
    probe_regret = counterfactual_regret_profile(model_game, probe_policy)
    full_regret = counterfactual_regret_profile(model_game, full_policy)
    probe_model_evaluation = evaluate_profile(model_game, probe_policy)
    full_model_evaluation = evaluate_profile(model_game, full_policy)
    candidate_model_evaluation_seconds = (
        time.perf_counter() - model_evaluation_start
    )

    full_evaluation_start = time.perf_counter()
    probe_full_evaluation = evaluate_profile(game, probe_policy)
    full_full_evaluation = evaluate_profile(game, full_policy)
    candidate_full_evaluation_seconds = time.perf_counter() - full_evaluation_start

    max_utility_mismatch = max(
        _utility_mismatch(blueprint_model_evaluation, full_blueprint_evaluation),
        _utility_mismatch(probe_model_evaluation, probe_full_evaluation),
        _utility_mismatch(full_model_evaluation, full_full_evaluation),
    )
    blueprint_local_nash_conv = blueprint_model_evaluation.nash_conv
    probe_local_improvement = (
        blueprint_local_nash_conv - probe_model_evaluation.nash_conv
    )
    full_local_improvement = (
        blueprint_local_nash_conv - full_model_evaluation.nash_conv
    )
    probe_mean_tv = probe_policy_distance[
        "mean_information_set_total_variation"
    ]
    full_mean_tv = full_policy_distance[
        "mean_information_set_total_variation"
    ]

    result = {
        "schema_version": 1,
        "experiment_type": "resolver_benefit_signals",
        "config": {
            "game": game_name,
            "blueprint_solver": blueprint_solver_name,
            "blueprint_iterations": blueprint_iterations,
            "search_solver": search_solver_name,
            "search_iterations": search_iterations,
            "probe_iterations": probe_iterations,
            "depth_limit": depth_limit,
            "in_search_blueprint_weight": in_search_blueprint_weight,
            "output_candidate_weight": output_candidate_weight,
            "warm_start_regret_mass": warm_start_regret_mass,
        },
        "environment": environment_metadata() if environment is None else environment,
        "protocol": {
            "leaf_values": "exact blueprint continuation",
            "signal_information": "depth-limited model only",
            "target_information": "untouched full-game exact evaluation",
            "candidate_policy": "average",
            "probe_and_full_searches": "independent cold starts",
            "full_game_target_never_enters_signal_calculation": True,
        },
        "timing": {
            "blueprint_prepared_in_run": blueprint_prepared_in_run,
            "blueprint_solver_seconds": prepared_blueprint.solver_seconds,
            "blueprint_full_evaluation_seconds": (
                prepared_blueprint.evaluation_seconds
            ),
            "blueprint_signal_seconds": blueprint_signal_seconds,
            "probe_initialization_seconds": probe_init_seconds,
            "probe_iteration_seconds": probe_iteration_seconds,
            "probe_search_seconds": probe_init_seconds + probe_iteration_seconds,
            "full_initialization_seconds": full_init_seconds,
            "full_iteration_seconds": full_iteration_seconds,
            "full_search_seconds": full_init_seconds + full_iteration_seconds,
            "policy_construction_seconds": policy_seconds,
            "candidate_model_evaluation_seconds": (
                candidate_model_evaluation_seconds
            ),
            "candidate_full_evaluation_seconds": candidate_full_evaluation_seconds,
        },
        "model": {
            "information_sets": len(information_sets),
            "blueprint_counterfactual_regret": _regret_summary(blueprint_regret),
            "probe_counterfactual_regret": _regret_summary(probe_regret),
            "full_counterfactual_regret": _regret_summary(full_regret),
            "blueprint_evaluation": _evaluation_summary(
                blueprint_model_evaluation
            ),
            "probe_evaluation": _evaluation_summary(probe_model_evaluation),
            "full_evaluation": _evaluation_summary(full_model_evaluation),
            "probe_policy_distance_from_blueprint": probe_policy_distance,
            "full_policy_distance_from_blueprint": full_policy_distance,
        },
        "signals": {
            "blueprint_positive_counterfactual_regret": (
                blueprint_regret.total_positive_regret
            ),
            "blueprint_local_nash_conv": blueprint_local_nash_conv,
            "probe_counterfactual_regret_reduction": (
                blueprint_regret.total_positive_regret
                - probe_regret.total_positive_regret
            ),
            "probe_local_nash_conv_improvement": probe_local_improvement,
            "probe_local_improvement_fraction_of_headroom": _zero_safe_ratio(
                probe_local_improvement,
                blueprint_local_nash_conv,
            ),
            "probe_local_improvement_per_mean_policy_tv": _zero_safe_ratio(
                probe_local_improvement,
                probe_mean_tv,
            ),
            "probe_policy_stability": -probe_mean_tv,
            "probe_mean_policy_tv": probe_mean_tv,
            "full_counterfactual_regret_reduction": (
                blueprint_regret.total_positive_regret
                - full_regret.total_positive_regret
            ),
            "full_local_nash_conv_improvement": full_local_improvement,
            "full_local_improvement_fraction_of_headroom": _zero_safe_ratio(
                full_local_improvement,
                blueprint_local_nash_conv,
            ),
            "full_local_improvement_per_mean_policy_tv": _zero_safe_ratio(
                full_local_improvement,
                full_mean_tv,
            ),
            "full_policy_stability": -full_mean_tv,
            "full_mean_policy_tv": full_mean_tv,
        },
        "targets": {
            "probe_full_game_nash_conv_delta_from_blueprint": (
                probe_full_evaluation.nash_conv
                - full_blueprint_evaluation.nash_conv
            ),
            "probe_full_game_nash_conv_improvement": (
                full_blueprint_evaluation.nash_conv
                - probe_full_evaluation.nash_conv
            ),
            "full_game_nash_conv_delta_from_blueprint": (
                full_full_evaluation.nash_conv
                - full_blueprint_evaluation.nash_conv
            ),
            "full_game_nash_conv_improvement": (
                full_blueprint_evaluation.nash_conv
                - full_full_evaluation.nash_conv
            ),
            "blueprint_full_game_nash_conv": full_blueprint_evaluation.nash_conv,
            "probe_full_game_nash_conv": probe_full_evaluation.nash_conv,
            "full_candidate_full_game_nash_conv": full_full_evaluation.nash_conv,
            "max_model_full_utility_mismatch": max_utility_mismatch,
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
    result = run_benefit_experiment(config)
    rendered = json.dumps(result, indent=2, sort_keys=True)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(
        f"benefit signals on {result['config']['game']}: "
        f"probe={result['signals']['probe_local_nash_conv_improvement']:.8g}, "
        f"full={result['signals']['full_local_nash_conv_improvement']:.8g}, "
        f"target={result['targets']['full_game_nash_conv_improvement']:.8g}"
    )
    if args.output is not None:
        print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
