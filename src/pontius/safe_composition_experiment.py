"""Evaluate exact-frontier safe resolving in two-player Kuhn poker."""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict
from math import isfinite
from pathlib import Path
from typing import Any

from .continual import public_belief, public_histories
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
from .reporting import environment_metadata
from .safe_resolving import (
    SafeContinualResolveResult,
    SafeResolveResult,
    resolve_all_public_histories_safely,
    resolve_subgame_safely,
)


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
        raise ValueError("safe resolving experiment requires two-player evaluation")
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


def _safe_result_summary(result: SafeResolveResult) -> dict[str, Any]:
    return {
        "resolver_player": result.frontier.resolver_player,
        "opponent_player": result.frontier.opponent_player,
        "opponent_counterfactual_reach": (
            result.frontier.total_counterfactual_reach
        ),
        "frontier_information_sets": len(result.frontier.entries),
        "resolver_information_sets": result.resolver_information_sets,
        "search_seconds": result.search_seconds,
        "certificate_seconds": result.certificate_seconds,
        "decision_compute_seconds": result.decision_compute_seconds,
        "gadget_nash_conv": result.gadget_evaluation.nash_conv,
        "gadget_exploitability": result.gadget_evaluation.exploitability,
        "gadget_opponent_security_residual": (
            result.gadget_opponent_security_residual
        ),
        "total_positive_frontier_violation": (
            result.total_positive_frontier_violation
        ),
        "max_positive_frontier_violation": (
            result.max_positive_frontier_violation
        ),
        "frontier": [asdict(item) for item in result.comparisons],
    }


def _continual_summary(result: SafeContinualResolveResult) -> dict[str, Any]:
    return {
        "structural_public_histories": result.structural_public_histories,
        "searched_public_histories": result.searched_public_histories,
        "deployed_public_histories": sum(
            record.candidate_deployed for record in result.records
        ),
        "skipped_zero_counterfactual_reach_histories": [
            list(history)
            for history in result.skipped_zero_counterfactual_reach_histories
        ],
        "total_search_seconds": result.total_search_seconds,
        "total_certificate_seconds": result.total_certificate_seconds,
        "total_decision_compute_seconds": result.total_decision_compute_seconds,
        "expected_search_seconds_per_hand": result.expected_search_seconds_per_hand,
        "expected_certificate_seconds_per_hand": (
            result.expected_certificate_seconds_per_hand
        ),
        "expected_decision_compute_seconds_per_hand": (
            result.expected_decision_compute_seconds_per_hand
        ),
        "expected_public_decisions_per_hand": (
            result.expected_public_decisions_per_hand
        ),
        "cumulative_exploitability_increase_bound": (
            result.cumulative_exploitability_increase_bound
        ),
        "max_search_seconds_at_one_public_state": (
            result.max_search_seconds_at_one_public_state
        ),
        "records": [asdict(record) for record in result.records],
    }


def _acting_player(game: Any, policy: Policy, history: Any) -> tuple[int, float]:
    belief = public_belief(game, policy, history)
    if belief is not None:
        return belief.acting_player, belief.public_reach_probability
    structural = public_belief(game, {}, history)
    if structural is None:
        raise AssertionError("uniform policy cannot reach a legal public history")
    return structural.acting_player, 0.0


def run_safe_composition_experiment(
    config: dict[str, Any],
    *,
    prepared_blueprint: PreparedBlueprint | None = None,
    environment: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compare single, continual, strictly gated, and global exact controls."""

    game_name = str(config.get("game", "kuhn2"))
    blueprint_solver_name = str(config.get("blueprint_solver", "lcfr"))
    blueprint_iterations = int(config.get("blueprint_iterations", 1_000))
    search_solver_name = str(config.get("search_solver", "cfr_plus"))
    search_iterations = int(config.get("search_iterations", 1_000))
    strict_tolerance = float(config.get("strict_frontier_tolerance", 1e-12))
    if game_name != "kuhn2":
        raise ValueError("safe composition experiment currently requires kuhn2")
    if blueprint_solver_name not in SOLVERS:
        raise ValueError(f"unsupported blueprint solver {blueprint_solver_name!r}")
    if search_solver_name not in SOLVERS:
        raise ValueError(f"unsupported search solver {search_solver_name!r}")
    if blueprint_iterations <= 0 or search_iterations <= 0:
        raise ValueError("blueprint and search iterations must be positive")
    if not isfinite(strict_tolerance) or strict_tolerance < 0.0:
        raise ValueError("strict_frontier_tolerance must be finite and nonnegative")

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
        raise ValueError("prepared blueprint does not match safe configuration")

    game = prepared_blueprint.game
    blueprint = prepared_blueprint.policy
    blueprint_evaluation = prepared_blueprint.evaluation
    information_sets = _resolved_information_sets(game)

    single_results: list[tuple[Any, float, SafeResolveResult]] = []
    for history in public_histories(game):
        resolver_player, public_reach = _acting_player(game, blueprint, history)
        single_results.append(
            (
                history,
                public_reach,
                resolve_subgame_safely(
                    game,
                    blueprint,
                    history,
                    resolver_player,
                    solver_name=search_solver_name,
                    search_iterations=search_iterations,
                ),
            )
        )

    safe_continual = resolve_all_public_histories_safely(
        game,
        blueprint,
        solver_name=search_solver_name,
        search_iterations=search_iterations,
    )
    strict_safe_continual = resolve_all_public_histories_safely(
        game,
        blueprint,
        solver_name=search_solver_name,
        search_iterations=search_iterations,
        max_deployed_frontier_violation=strict_tolerance,
    )
    global_solver, global_initialization, global_iterations = _run_search(
        game,
        search_solver_name,
        search_iterations,
        blueprint,
        None,
        0.0,
    )
    global_policy = global_solver.average_strategy()

    evaluation_start = time.perf_counter()
    single_evaluations = [
        evaluate_profile(game, result.policy) for _, _, result in single_results
    ]
    safe_evaluation = evaluate_profile(game, safe_continual.policy)
    strict_evaluation = evaluate_profile(game, strict_safe_continual.policy)
    global_evaluation = evaluate_profile(game, global_policy)
    evaluation_seconds = time.perf_counter() - evaluation_start

    single_records = []
    for (history, public_reach, safe_result), evaluation in zip(
        single_results,
        single_evaluations,
        strict=True,
    ):
        single_records.append(
            {
                "history": list(history),
                "public_reach_probability": public_reach,
                **_safe_result_summary(safe_result),
                "candidate": _candidate_record(
                    evaluation,
                    safe_result.policy,
                    blueprint,
                    blueprint_evaluation,
                    information_sets,
                    safe_result.decision_compute_seconds,
                    safe_result.full_game_exploitability_increase_bound,
                ),
            }
        )

    safe_summary = _continual_summary(safe_continual)
    strict_summary = _continual_summary(strict_safe_continual)
    result = {
        "schema_version": 1,
        "experiment_type": "safe_resolver_composition",
        "config": {
            "game": game_name,
            "blueprint_solver": blueprint_solver_name,
            "blueprint_iterations": blueprint_iterations,
            "search_solver": search_solver_name,
            "search_iterations": search_iterations,
            "strict_frontier_tolerance": strict_tolerance,
        },
        "environment": environment_metadata() if environment is None else environment,
        "protocol": {
            "frontier": "exact opponent counterfactual best-response values",
            "gadget": "opponent terminate/follow per augmented root information set",
            "root_chance": "chance reach times resolver reach; opponent reach excluded",
            "deployed_strategy": "resolver subgame component only",
            "candidate_policy": "average",
            "strict_gate": "deploy only when exact total positive violation is within tolerance",
            "full_game_target_never_enters_policy_construction": True,
            "multiplayer_claim": False,
        },
        "timing": {
            "blueprint_prepared_in_run": blueprint_prepared_in_run,
            "blueprint_solver_seconds": prepared_blueprint.solver_seconds,
            "blueprint_full_evaluation_seconds": (
                prepared_blueprint.evaluation_seconds
            ),
            "candidate_full_evaluation_seconds": evaluation_seconds,
            "global_initialization_seconds": global_initialization,
            "global_iteration_seconds": global_iterations,
        },
        "blueprint": asdict(blueprint_evaluation),
        "single_boundary": {
            "expected_decision_compute_seconds_per_hand": sum(
                record["public_reach_probability"]
                * record["decision_compute_seconds"]
                for record in single_records
            ),
            "records": single_records,
        },
        "safe_continual": {
            **safe_summary,
            "candidate": _candidate_record(
                safe_evaluation,
                safe_continual.policy,
                blueprint,
                blueprint_evaluation,
                information_sets,
                safe_continual.expected_decision_compute_seconds_per_hand,
                safe_continual.cumulative_exploitability_increase_bound,
            ),
        },
        "strict_safe_continual": {
            **strict_summary,
            "candidate": _candidate_record(
                strict_evaluation,
                strict_safe_continual.policy,
                blueprint,
                blueprint_evaluation,
                information_sets,
                strict_safe_continual.expected_decision_compute_seconds_per_hand,
                strict_safe_continual.cumulative_exploitability_increase_bound,
            ),
        },
        "global_control": {
            "candidate": _candidate_record(
                global_evaluation,
                global_policy,
                blueprint,
                blueprint_evaluation,
                information_sets,
                global_initialization + global_iterations,
                float("inf"),
            )
        },
    }
    global_candidate = result["global_control"]["candidate"]
    global_candidate["exploitability_increase_bound"] = None
    global_candidate["residual_adjusted_bound_slack"] = None
    global_candidate["residual_adjusted_bound_holds"] = None
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
    result = run_safe_composition_experiment(config)
    rendered = json.dumps(result, indent=2, sort_keys=True, allow_nan=False)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    safe = result["safe_continual"]["candidate"]
    strict = result["strict_safe_continual"]["candidate"]
    print(
        f"safe composition on {result['config']['game']}: "
        f"raw={safe['nash_conv_improvement_over_blueprint']:.8g}, "
        f"strict={strict['nash_conv_improvement_over_blueprint']:.8g}, "
        f"bound={safe['exploitability_increase_bound']:.8g}"
    )
    if args.output is not None:
        print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
