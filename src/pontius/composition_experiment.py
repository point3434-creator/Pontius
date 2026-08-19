"""Compare prefix, Bayesian continual, and coherent global search controls."""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict
from math import isfinite
from pathlib import Path
from typing import Any

from .continual import ContinualResolveResult, resolve_all_public_histories
from .depth_limited import DepthLimitedGame, PolicyContinuationValues
from .evaluation import EvaluationResult, Policy, evaluate_profile
from .game import Action
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


def _safe_rate(improvement: float, seconds: float) -> float | None:
    return improvement / (1_000.0 * seconds) if seconds > 0.0 else None


def _candidate_record(
    evaluation: EvaluationResult,
    policy: Policy,
    blueprint: Policy,
    blueprint_evaluation: EvaluationResult,
    information_sets: dict[str, tuple[Action, ...]],
    decision_compute_seconds: float,
) -> dict[str, Any]:
    improvement = blueprint_evaluation.nash_conv - evaluation.nash_conv
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
    }


def _continual_summary(result: ContinualResolveResult) -> dict[str, Any]:
    weighted_root_model_gain = sum(
        record.public_reach_probability
        * record.root_candidate_model_nash_conv_improvement
        for record in result.records
    )
    weighted_full_local_gain = sum(
        record.public_reach_probability
        * record.full_local_model_nash_conv_improvement
        for record in result.records
    )
    return {
        "structural_public_histories": result.structural_public_histories,
        "searched_public_histories": result.searched_public_histories,
        "deployed_public_histories": result.deployed_public_histories,
        "skipped_zero_reach_histories": [
            list(history) for history in result.skipped_zero_reach_histories
        ],
        "searched_information_sets": result.searched_information_sets,
        "deployed_information_sets": result.deployed_information_sets,
        "total_search_seconds_to_materialize_profile": result.total_search_seconds,
        "total_gate_evaluation_seconds": result.total_gate_evaluation_seconds,
        "total_diagnostic_evaluation_seconds": (
            result.total_diagnostic_evaluation_seconds
        ),
        "expected_search_seconds_per_hand": result.expected_search_seconds_per_hand,
        "expected_gate_evaluation_seconds_per_hand": (
            result.expected_gate_evaluation_seconds_per_hand
        ),
        "expected_public_decisions_per_hand": (
            result.expected_public_decisions_per_hand
        ),
        "expected_search_seconds_per_public_decision": (
            result.expected_search_seconds_per_public_decision
        ),
        "max_search_seconds_at_one_public_state": (
            result.max_search_seconds_at_one_public_state
        ),
        "continuation_cache_states": result.continuation_cache_states,
        "reach_weighted_root_candidate_model_gain": weighted_root_model_gain,
        "reach_weighted_full_local_model_gain": weighted_full_local_gain,
        "records": [asdict(record) for record in result.records],
    }


def run_composition_experiment(
    config: dict[str, Any],
    *,
    prepared_blueprint: PreparedBlueprint | None = None,
    environment: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Evaluate three target-blind policy-composition architectures."""

    game_name = str(config.get("game", "kuhn2"))
    blueprint_solver_name = str(config.get("blueprint_solver", "lcfr"))
    blueprint_iterations = int(config.get("blueprint_iterations", 1_000))
    search_solver_name = str(config.get("search_solver", "lcfr"))
    search_iterations = int(config.get("search_iterations", 100))
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
    if blueprint_iterations <= 0 or search_iterations <= 0:
        raise ValueError("blueprint and search iterations must be positive")
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
        raise ValueError("prepared blueprint does not match composition configuration")

    game = prepared_blueprint.game
    blueprint = prepared_blueprint.policy
    blueprint_evaluation = prepared_blueprint.evaluation
    full_information_sets = _resolved_information_sets(game)
    exact_continuation = PolicyContinuationValues(game.num_players, blueprint)
    prefix_model = DepthLimitedGame(game, depth_limit, exact_continuation)
    prefix_information_sets = _resolved_information_sets(prefix_model)

    prefix_solver, prefix_initialization, prefix_iterations = _run_search(
        prefix_model,
        search_solver_name,
        search_iterations,
        blueprint,
        warm_start_regret_mass,
        in_search_blueprint_weight,
    )
    prefix_policy = interpolate_policy(
        blueprint,
        prefix_solver.average_strategy(),
        prefix_information_sets,
        output_candidate_weight,
    )
    prefix_model_blueprint_evaluation = evaluate_profile(prefix_model, blueprint)
    prefix_model_candidate_evaluation = evaluate_profile(prefix_model, prefix_policy)

    continual = resolve_all_public_histories(
        game,
        blueprint,
        solver_name=search_solver_name,
        search_iterations=search_iterations,
        depth_limit=depth_limit,
        in_search_blueprint_weight=in_search_blueprint_weight,
        output_candidate_weight=output_candidate_weight,
        warm_start_regret_mass=warm_start_regret_mass,
        deployment_gate="always",
    )
    local_gated_continual = resolve_all_public_histories(
        game,
        blueprint,
        solver_name=search_solver_name,
        search_iterations=search_iterations,
        depth_limit=depth_limit,
        in_search_blueprint_weight=in_search_blueprint_weight,
        output_candidate_weight=output_candidate_weight,
        warm_start_regret_mass=warm_start_regret_mass,
        deployment_gate="positive_local_model_gain",
    )

    global_solver, global_initialization, global_iterations = _run_search(
        game,
        search_solver_name,
        search_iterations,
        blueprint,
        warm_start_regret_mass,
        in_search_blueprint_weight,
    )
    global_policy = interpolate_policy(
        blueprint,
        global_solver.average_strategy(),
        full_information_sets,
        output_candidate_weight,
    )

    evaluation_start = time.perf_counter()
    prefix_evaluation = evaluate_profile(game, prefix_policy)
    continual_evaluation = evaluate_profile(game, continual.policy)
    local_gated_continual_evaluation = evaluate_profile(
        game,
        local_gated_continual.policy,
    )
    global_evaluation = evaluate_profile(game, global_policy)
    candidate_full_evaluation_seconds = time.perf_counter() - evaluation_start

    prefix_search_seconds = prefix_initialization + prefix_iterations
    global_search_seconds = global_initialization + global_iterations
    continual_candidate = _candidate_record(
        continual_evaluation,
        continual.policy,
        blueprint,
        blueprint_evaluation,
        full_information_sets,
        continual.expected_search_seconds_per_hand,
    )
    continual_improvement = continual_candidate[
        "nash_conv_improvement_over_blueprint"
    ]
    continual_candidate[
        "nash_conv_improvement_per_total_materialization_millisecond"
    ] = _safe_rate(continual_improvement, continual.total_search_seconds)
    local_gated_decision_seconds = (
        local_gated_continual.expected_search_seconds_per_hand
        + local_gated_continual.expected_gate_evaluation_seconds_per_hand
    )
    local_gated_candidate = _candidate_record(
        local_gated_continual_evaluation,
        local_gated_continual.policy,
        blueprint,
        blueprint_evaluation,
        full_information_sets,
        local_gated_decision_seconds,
    )
    local_gated_improvement = local_gated_candidate[
        "nash_conv_improvement_over_blueprint"
    ]
    local_gated_candidate[
        "nash_conv_improvement_per_total_materialization_millisecond"
    ] = _safe_rate(
        local_gated_improvement,
        local_gated_continual.total_search_seconds
        + local_gated_continual.total_gate_evaluation_seconds,
    )

    result = {
        "schema_version": 1,
        "experiment_type": "resolver_policy_composition",
        "config": {
            "game": game_name,
            "blueprint_solver": blueprint_solver_name,
            "blueprint_iterations": blueprint_iterations,
            "search_solver": search_solver_name,
            "search_iterations": search_iterations,
            "depth_limit": depth_limit,
            "in_search_blueprint_weight": in_search_blueprint_weight,
            "output_candidate_weight": output_candidate_weight,
            "warm_start_regret_mass": warm_start_regret_mass,
        },
        "environment": environment_metadata() if environment is None else environment,
        "protocol": {
            "leaf_values": "exact blueprint continuation",
            "candidate_policy": "average",
            "full_game_target_never_enters_policy_construction": True,
            "prefix": "deploy every information set in one root depth-limited solve",
            "continual": (
                "forward Bayesian public belief; deploy only each public root; "
                "retain blueprint on zero-reach histories"
            ),
            "local_gated_continual": (
                "same composition, but veto root candidates with nonpositive "
                "exact local-model NashConv improvement"
            ),
            "global_control": "one coherent full-game anchored solve",
            "continual_safety_guarantee": False,
        },
        "timing": {
            "blueprint_prepared_in_run": blueprint_prepared_in_run,
            "blueprint_solver_seconds": prepared_blueprint.solver_seconds,
            "blueprint_full_evaluation_seconds": (
                prepared_blueprint.evaluation_seconds
            ),
            "prefix_initialization_seconds": prefix_initialization,
            "prefix_iteration_seconds": prefix_iterations,
            "global_initialization_seconds": global_initialization,
            "global_iteration_seconds": global_iterations,
            "candidate_full_evaluation_seconds": candidate_full_evaluation_seconds,
        },
        "blueprint": asdict(blueprint_evaluation),
        "prefix": {
            "model_information_sets": len(prefix_information_sets),
            "model_nash_conv_improvement": (
                prefix_model_blueprint_evaluation.nash_conv
                - prefix_model_candidate_evaluation.nash_conv
            ),
            "candidate": _candidate_record(
                prefix_evaluation,
                prefix_policy,
                blueprint,
                blueprint_evaluation,
                full_information_sets,
                prefix_search_seconds,
            ),
        },
        "continual": {
            **_continual_summary(continual),
            "candidate": continual_candidate,
        },
        "local_gated_continual": {
            **_continual_summary(local_gated_continual),
            "candidate": local_gated_candidate,
        },
        "global_control": {
            "candidate": _candidate_record(
                global_evaluation,
                global_policy,
                blueprint,
                blueprint_evaluation,
                full_information_sets,
                global_search_seconds,
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
    result = run_composition_experiment(config)
    rendered = json.dumps(result, indent=2, sort_keys=True, allow_nan=False)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    prefix = result["prefix"]["candidate"]["nash_conv_improvement_over_blueprint"]
    continual = result["continual"]["candidate"][
        "nash_conv_improvement_over_blueprint"
    ]
    local_gated = result["local_gated_continual"]["candidate"][
        "nash_conv_improvement_over_blueprint"
    ]
    global_control = result["global_control"]["candidate"][
        "nash_conv_improvement_over_blueprint"
    ]
    print(
        f"composition on {result['config']['game']}: "
        f"prefix={prefix:.8g}, continual={continual:.8g}, "
        f"local-gated={local_gated:.8g}, "
        f"global={global_control:.8g}"
    )
    if args.output is not None:
        print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
