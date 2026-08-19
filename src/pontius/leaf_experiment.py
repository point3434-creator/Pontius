"""Paired experiments mapping controlled leaf error to full-game strategy error."""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict, dataclass
from math import isfinite, sqrt
from pathlib import Path
from typing import Any

from .cfr import TabularCFR
from .depth_limited import (
    CutoffReach,
    DepthLimitedGame,
    DeterministicPerturbedValues,
    PolicyContinuationValues,
    collect_cutoff_reaches,
)
from .evaluation import (
    EvaluationResult,
    Policy,
    collect_information_sets,
    evaluate_profile,
    policy_distribution,
)
from .game import Action, ExtensiveFormGame
from .kuhn import KuhnPoker
from .policy import interpolate_policy
from .reporting import environment_metadata, json_policy

SOLVERS = {"cfr", "lcfr", "cfr_plus", "dcfr"}
ERROR_GROUPINGS = {"concrete", "public_history"}
ERROR_SCOPES = {
    "all",
    "top_half_by_blueprint_reach",
    "bottom_half_by_blueprint_reach",
    "public_actions",
}


@dataclass(frozen=True, slots=True)
class PreparedBlueprint:
    game_name: str
    solver_name: str
    iterations: int
    game: KuhnPoker
    policy: Policy
    evaluation: EvaluationResult
    solver_seconds: float
    evaluation_seconds: float


def _parse_game(game_name: str) -> KuhnPoker:
    if not game_name.startswith("kuhn") or not game_name[4:].isdigit():
        raise ValueError(f"unsupported game {game_name!r}")
    num_players = int(game_name[4:])
    if not 2 <= num_players <= 6:
        raise ValueError(f"unsupported game {game_name!r}")
    return KuhnPoker(num_players)


def prepare_blueprint(
    game_name: str,
    solver_name: str,
    iterations: int,
) -> PreparedBlueprint:
    """Train and exactly evaluate a reusable experiment blueprint."""

    game = _parse_game(game_name)
    if solver_name not in SOLVERS:
        raise ValueError(f"unsupported blueprint solver {solver_name!r}")
    if iterations <= 0:
        raise ValueError("blueprint iterations must be positive")

    solver = TabularCFR(game, variant=solver_name)  # type: ignore[arg-type]
    solver_start = time.perf_counter()
    solver.run(iterations)
    solver_seconds = time.perf_counter() - solver_start
    policy = solver.average_strategy()
    evaluation_start = time.perf_counter()
    evaluation = evaluate_profile(game, policy)
    evaluation_seconds = time.perf_counter() - evaluation_start
    return PreparedBlueprint(
        game_name=game_name,
        solver_name=solver_name,
        iterations=iterations,
        game=game,
        policy=policy,
        evaluation=evaluation,
        solver_seconds=solver_seconds,
        evaluation_seconds=evaluation_seconds,
    )


def _resolved_information_sets(
    game: ExtensiveFormGame,
) -> dict[str, tuple[Action, ...]]:
    result: dict[str, tuple[Action, ...]] = {}
    for player in range(game.num_players):
        for key, actions in collect_information_sets(game, player).items():
            previous = result.setdefault(key, actions)
            if previous != actions:
                raise ValueError(f"information-set collision for {key!r}")
    return result


def _public_history_key(state: Any) -> str:
    history = getattr(state, "history", None)
    if history is None:
        raise ValueError("public-history grouping requires states with history")
    return repr(tuple(history))


def _public_actions(state: Any) -> tuple[str, ...]:
    history = getattr(state, "history", None)
    if history is None:
        raise ValueError("public-action scope requires states with history")
    return tuple(str(action) for _, action in history)


def _active_state_keys(
    reaches: list[CutoffReach],
    scope: str,
    scope_actions: tuple[str, ...] | None,
) -> frozenset[str] | None:
    if scope == "all":
        return None
    if scope == "public_actions":
        if scope_actions is None:
            raise ValueError("public_actions scope requires leaf_error_scope_actions")
        selected = {
            repr(record.state)
            for record in reaches
            if _public_actions(record.state) == scope_actions
        }
    else:
        ordered = sorted(
            reaches,
            key=lambda record: (record.joint_reach, repr(record.state)),
        )
        count = max(1, (len(ordered) + 1) // 2)
        selected_records = (
            ordered[-count:]
            if scope == "top_half_by_blueprint_reach"
            else ordered[:count]
        )
        selected = {repr(record.state) for record in selected_records}
    if not selected:
        raise ValueError("leaf error scope selects no cutoff states")
    return frozenset(selected)


def _safe_ratio(numerator: float, denominator: float) -> float | None:
    return numerator / denominator if denominator > 0.0 else None


def _policy_distance(
    left: Policy,
    right: Policy,
    information_sets: dict[str, tuple[Action, ...]],
) -> dict[str, float | int]:
    total_variations: list[float] = []
    for key, actions in information_sets.items():
        left_distribution = policy_distribution(left, key, actions)
        right_distribution = policy_distribution(right, key, actions)
        total_variations.append(
            0.5
            * sum(
                abs(left_distribution[action] - right_distribution[action])
                for action in actions
            )
        )
    if not total_variations:
        raise ValueError("depth-limited game has no resolved information sets")
    return {
        "information_sets": len(total_variations),
        "mean_information_set_total_variation": sum(total_variations)
        / len(total_variations),
        "max_information_set_total_variation": max(total_variations),
    }


def _effect(
    treatment: EvaluationResult,
    control: EvaluationResult,
    treatment_policy: Policy,
    control_policy: Policy,
    information_sets: dict[str, tuple[Action, ...]],
) -> dict[str, Any]:
    utility_deltas = tuple(
        treated - exact
        for treated, exact in zip(treatment.utilities, control.utilities, strict=True)
    )
    return {
        # Positive means the perturbed-leaf result is more exploitable.
        "nash_conv_delta": treatment.nash_conv - control.nash_conv,
        "absolute_nash_conv_delta": abs(treatment.nash_conv - control.nash_conv),
        "utility_deltas": list(utility_deltas),
        "utility_rmse": sqrt(
            sum(delta * delta for delta in utility_deltas) / len(utility_deltas)
        ),
        **_policy_distance(
            treatment_policy,
            control_policy,
            information_sets,
        ),
    }


def _evaluation_record(
    evaluation: EvaluationResult,
    policy: Policy,
    blueprint: Policy,
    blueprint_nash_conv: float,
    information_sets: dict[str, tuple[Action, ...]],
) -> dict[str, Any]:
    return {
        **asdict(evaluation),
        "nash_conv_delta_from_blueprint": evaluation.nash_conv - blueprint_nash_conv,
        "nash_conv_improvement_over_blueprint": (
            blueprint_nash_conv - evaluation.nash_conv
        ),
        "resolved_policy_distance_from_blueprint": _policy_distance(
            policy,
            blueprint,
            information_sets,
        ),
        "policy": json_policy(policy),
    }


def _oracle_no_op_selection(
    candidate: EvaluationResult,
    blueprint: EvaluationResult,
) -> dict[str, Any]:
    candidate_selected = candidate.nash_conv < blueprint.nash_conv
    return {
        "candidate_selected": candidate_selected,
        "selected": "candidate" if candidate_selected else "blueprint",
        "candidate_nash_conv_delta": candidate.nash_conv - blueprint.nash_conv,
        "selected_nash_conv": (
            candidate.nash_conv if candidate_selected else blueprint.nash_conv
        ),
    }


def _run_search(
    game: ExtensiveFormGame,
    solver_name: str,
    iterations: int,
    blueprint: Policy,
    warm_start_regret_mass: float | None,
    in_search_blueprint_weight: float,
) -> tuple[TabularCFR, float, float]:
    initialization_start = time.perf_counter()
    solver = TabularCFR(
        game,
        variant=solver_name,  # type: ignore[arg-type]
        blueprint_policy=blueprint,
        blueprint_weight=in_search_blueprint_weight,
    )
    if warm_start_regret_mass is not None:
        solver.warm_start(blueprint, warm_start_regret_mass)
    initialization_seconds = time.perf_counter() - initialization_start
    start = time.perf_counter()
    solver.run(iterations)
    iteration_seconds = time.perf_counter() - start
    return solver, initialization_seconds, iteration_seconds


def run_leaf_experiment(
    config: dict[str, Any],
    *,
    prepared_blueprint: PreparedBlueprint | None = None,
    environment: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run exact-control and perturbed-leaf searches as a deterministic pair.

    Both arms share the blueprint, traversal rule, budget, and optional regret
    prior. They differ only in their leaf utilities. Both resulting policies
    are evaluated in the original full game, never in place of it.
    """

    game_name = str(config.get("game", "kuhn2"))
    blueprint_solver_name = str(config.get("blueprint_solver", "lcfr"))
    blueprint_iterations = int(config.get("blueprint_iterations", 1_000))
    search_solver_name = str(config.get("search_solver", "cfr_plus"))
    search_iterations = int(config.get("search_iterations", 100))
    depth_limit = int(config.get("depth_limit", 1))
    leaf_error_scale = float(config.get("leaf_error_scale", 0.0))
    raw_target_root_l2 = config.get("leaf_error_target_on_policy_root_l2")
    leaf_error_target_on_policy_root_l2 = (
        None if raw_target_root_l2 is None else float(raw_target_root_l2)
    )
    leaf_error_seed = int(config.get("leaf_error_seed", 0))
    zero_sum_errors = bool(config.get("zero_sum_errors", True))
    raw_warm_start = config.get("warm_start_regret_mass")
    warm_start_regret_mass = (
        None if raw_warm_start is None else float(raw_warm_start)
    )
    in_search_blueprint_weight = float(
        config.get("in_search_blueprint_weight", 0.0)
    )
    output_candidate_weight = float(config.get("output_candidate_weight", 1.0))
    leaf_error_grouping = str(config.get("leaf_error_grouping", "concrete"))
    leaf_error_scope = str(config.get("leaf_error_scope", "all"))
    raw_scope_actions = config.get("leaf_error_scope_actions")
    if raw_scope_actions is not None and not isinstance(raw_scope_actions, (list, tuple)):
        raise ValueError("leaf_error_scope_actions must be a list or null")
    leaf_error_scope_actions = (
        None
        if raw_scope_actions is None
        else tuple(str(action) for action in raw_scope_actions)
    )
    raw_bias = config.get("leaf_error_bias")
    if raw_bias is not None and not isinstance(raw_bias, (list, tuple)):
        raise ValueError("leaf_error_bias must be a list or null")
    leaf_error_bias = (
        None if raw_bias is None else tuple(float(value) for value in raw_bias)
    )

    parsed_game = _parse_game(game_name)
    if blueprint_solver_name not in SOLVERS:
        raise ValueError(f"unsupported blueprint solver {blueprint_solver_name!r}")
    if search_solver_name not in SOLVERS:
        raise ValueError(f"unsupported search solver {search_solver_name!r}")
    if blueprint_iterations <= 0 or search_iterations <= 0:
        raise ValueError("blueprint_iterations and search_iterations must be positive")
    if depth_limit < 1:
        raise ValueError("depth_limit must be at least one")
    if not isfinite(leaf_error_scale) or leaf_error_scale < 0.0:
        raise ValueError("leaf_error_scale must be finite and nonnegative")
    if leaf_error_target_on_policy_root_l2 is not None:
        if (
            not isfinite(leaf_error_target_on_policy_root_l2)
            or leaf_error_target_on_policy_root_l2 <= 0.0
        ):
            raise ValueError(
                "leaf_error_target_on_policy_root_l2 must be finite and positive"
            )
        if leaf_error_scale <= 0.0:
            raise ValueError("target root L2 calibration requires positive noise scale")
        if leaf_error_bias is not None:
            raise ValueError("target root L2 calibration does not support explicit bias")
    if warm_start_regret_mass is not None and warm_start_regret_mass <= 0.0:
        raise ValueError("warm_start_regret_mass must be positive or null")
    if not 0.0 <= in_search_blueprint_weight <= 1.0:
        raise ValueError("in_search_blueprint_weight must be between zero and one")
    if not 0.0 <= output_candidate_weight <= 1.0:
        raise ValueError("output_candidate_weight must be between zero and one")
    if leaf_error_grouping not in ERROR_GROUPINGS:
        raise ValueError(f"unsupported leaf_error_grouping {leaf_error_grouping!r}")
    if leaf_error_scope not in ERROR_SCOPES:
        raise ValueError(f"unsupported leaf_error_scope {leaf_error_scope!r}")
    if leaf_error_bias is not None and len(leaf_error_bias) != parsed_game.num_players:
        raise ValueError("leaf_error_bias count must match game players")

    experiment_start = time.perf_counter()
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
        raise ValueError("prepared blueprint does not match experiment configuration")

    game = prepared_blueprint.game
    blueprint = prepared_blueprint.policy
    blueprint_evaluation = prepared_blueprint.evaluation

    exact_leaves = PolicyContinuationValues(game.num_players, blueprint)
    exact_game = DepthLimitedGame(game, depth_limit, exact_leaves)
    leaf_start = time.perf_counter()
    cutoff_reaches = collect_cutoff_reaches(exact_game, blueprint)
    active_state_keys = _active_state_keys(
        cutoff_reaches,
        leaf_error_scope,
        leaf_error_scope_actions,
    )
    noise_key = _public_history_key if leaf_error_grouping == "public_history" else None
    effective_leaf_error_scale = leaf_error_scale

    def build_perturbed_leaves(scale: float) -> DeterministicPerturbedValues:
        return DeterministicPerturbedValues(
            exact_leaves,
            game.num_players,
            scale=scale,
            seed=leaf_error_seed,
            zero_sum=zero_sum_errors,
            noise_key=noise_key,
            bias=leaf_error_bias,
            active_state_keys=active_state_keys,
        )

    perturbed_leaves = build_perturbed_leaves(effective_leaf_error_scale)
    if leaf_error_target_on_policy_root_l2 is not None:
        calibration_root_l2 = perturbed_leaves.reach_weighted_error_stats(
            cutoff_reaches
        ).on_policy_root_l2
        if calibration_root_l2 <= 0.0:
            raise ValueError("cannot calibrate a zero realized perturbation")
        effective_leaf_error_scale *= (
            leaf_error_target_on_policy_root_l2 / calibration_root_l2
        )
        perturbed_leaves = build_perturbed_leaves(effective_leaf_error_scale)
    perturbed_game = DepthLimitedGame(game, depth_limit, perturbed_leaves)

    cutoff_states = [record.state for record in cutoff_reaches]
    leaf_error = perturbed_leaves.error_stats(cutoff_states)
    reach_weighted_leaf_error = perturbed_leaves.reach_weighted_error_stats(
        cutoff_reaches
    )
    leaf_materialization_seconds = time.perf_counter() - leaf_start
    active_records = [
        record for record in cutoff_reaches if perturbed_leaves.is_active(record.state)
    ]
    active_on_policy_mass = sum(record.joint_reach for record in active_records)
    active_counterfactual_mass = tuple(
        sum(record.counterfactual_reach(player) for record in active_records)
        for player in range(game.num_players)
    )
    total_counterfactual_mass = reach_weighted_leaf_error.counterfactual_reach_mass
    active_counterfactual_fraction = tuple(
        _safe_ratio(active, total)
        for active, total in zip(
            active_counterfactual_mass,
            total_counterfactual_mass,
            strict=True,
        )
    )
    active_on_policy_fraction = _safe_ratio(
        active_on_policy_mass,
        reach_weighted_leaf_error.on_policy_reach_mass,
    )
    error_group_key = noise_key or repr
    active_error_groups = len(
        {error_group_key(record.state) for record in active_records}
    )
    effective_bias = None
    if leaf_error_bias is not None:
        bias_mean = (
            sum(leaf_error_bias) / game.num_players if zero_sum_errors else 0.0
        )
        effective_bias = [value - bias_mean for value in leaf_error_bias]

    (
        control_solver,
        control_initialization_seconds,
        control_iteration_seconds,
    ) = _run_search(
        exact_game,
        search_solver_name,
        search_iterations,
        blueprint,
        warm_start_regret_mass,
        in_search_blueprint_weight,
    )
    (
        treatment_solver,
        treatment_initialization_seconds,
        treatment_iteration_seconds,
    ) = _run_search(
        perturbed_game,
        search_solver_name,
        search_iterations,
        blueprint,
        warm_start_regret_mass,
        in_search_blueprint_weight,
    )

    policy_construction_start = time.perf_counter()
    information_sets = _resolved_information_sets(exact_game)
    control_average = interpolate_policy(
        blueprint,
        control_solver.average_strategy(),
        information_sets,
        output_candidate_weight,
    )
    control_current = interpolate_policy(
        blueprint,
        control_solver.current_strategy(),
        information_sets,
        output_candidate_weight,
    )
    treatment_average = interpolate_policy(
        blueprint,
        treatment_solver.average_strategy(),
        information_sets,
        output_candidate_weight,
    )
    treatment_current = interpolate_policy(
        blueprint,
        treatment_solver.current_strategy(),
        information_sets,
        output_candidate_weight,
    )
    policy_construction_seconds = time.perf_counter() - policy_construction_start

    evaluation_start = time.perf_counter()
    control_average_evaluation = evaluate_profile(game, control_average)
    control_current_evaluation = evaluate_profile(game, control_current)
    treatment_average_evaluation = evaluate_profile(game, treatment_average)
    treatment_current_evaluation = evaluate_profile(game, treatment_current)
    candidate_evaluation_seconds = time.perf_counter() - evaluation_start

    result = {
        "schema_version": 3,
        "experiment_type": "paired_leaf_error",
        "config": {
            "game": game_name,
            "blueprint_solver": blueprint_solver_name,
            "blueprint_iterations": blueprint_iterations,
            "search_solver": search_solver_name,
            "search_iterations": search_iterations,
            "depth_limit": depth_limit,
            "leaf_error_scale": leaf_error_scale,
            "leaf_error_target_on_policy_root_l2": (
                leaf_error_target_on_policy_root_l2
            ),
            "leaf_error_seed": leaf_error_seed,
            "zero_sum_errors": zero_sum_errors,
            "warm_start_regret_mass": warm_start_regret_mass,
            "in_search_blueprint_weight": in_search_blueprint_weight,
            "output_candidate_weight": output_candidate_weight,
            "leaf_error_grouping": leaf_error_grouping,
            "leaf_error_scope": leaf_error_scope,
            "leaf_error_scope_actions": (
                None
                if leaf_error_scope_actions is None
                else list(leaf_error_scope_actions)
            ),
            "leaf_error_bias": (
                None if leaf_error_bias is None else list(leaf_error_bias)
            ),
        },
        "environment": environment_metadata() if environment is None else environment,
        "timing": {
            "blueprint_prepared_in_run": blueprint_prepared_in_run,
            "blueprint_solver_seconds": prepared_blueprint.solver_seconds,
            "blueprint_evaluation_seconds": prepared_blueprint.evaluation_seconds,
            "leaf_materialization_seconds": leaf_materialization_seconds,
            "exact_control_initialization_seconds": control_initialization_seconds,
            "exact_control_iteration_seconds": control_iteration_seconds,
            "exact_control_search_seconds": (
                control_initialization_seconds + control_iteration_seconds
            ),
            "perturbed_initialization_seconds": treatment_initialization_seconds,
            "perturbed_iteration_seconds": treatment_iteration_seconds,
            "perturbed_search_seconds": (
                treatment_initialization_seconds + treatment_iteration_seconds
            ),
            "policy_construction_seconds": policy_construction_seconds,
            "full_game_candidate_evaluation_seconds": candidate_evaluation_seconds,
        },
        "leaf_protocol": {
            "continuation_policy": "blueprint_average",
            "cache_mode": "precomputed_before_search",
            "perturbation_granularity": leaf_error_grouping,
            "error_weighting": (
                "uniform, blueprint on-policy reach, and per-player "
                "counterfactual reach"
            ),
            "policy_distance_weighting": "uniform_over_resolved_information_sets",
        },
        "structured_error_protocol": {
            "grouping": leaf_error_grouping,
            "scope": leaf_error_scope,
            "scope_actions": (
                None
                if leaf_error_scope_actions is None
                else list(leaf_error_scope_actions)
            ),
            "requested_bias": (
                None if leaf_error_bias is None else list(leaf_error_bias)
            ),
            "effective_bias_after_zero_sum_projection": effective_bias,
            "effective_leaf_error_scale": effective_leaf_error_scale,
            "active_leaf_states": len(active_records),
            "active_error_groups": active_error_groups,
            "active_on_policy_reach_mass": active_on_policy_mass,
            "active_on_policy_reach_fraction": active_on_policy_fraction,
            "active_counterfactual_reach_mass": list(active_counterfactual_mass),
            "active_counterfactual_reach_fraction": list(
                active_counterfactual_fraction
            ),
        },
        "strategy_protocol": {
            "in_search_constraint": (
                "blueprint_weight * blueprint + "
                "(1 - blueprint_weight) * CFR_candidate"
            ),
            "output_constraint": (
                "(1 - candidate_weight) * blueprint + "
                "candidate_weight * searched_policy"
            ),
            "maximum_unanchored_candidate_component": (
                output_candidate_weight * (1.0 - in_search_blueprint_weight)
            ),
            "oracle_no_op_uses_unavailable_full_game_nash_conv": True,
        },
        "leaf_error": asdict(leaf_error),
        "leaf_error_reach_weighted": asdict(reach_weighted_leaf_error),
        "blueprint": {
            **asdict(blueprint_evaluation),
            "policy": json_policy(blueprint),
        },
        "exact_control": {
            "information_sets": len(control_solver.information_sets),
            "average": _evaluation_record(
                control_average_evaluation,
                control_average,
                blueprint,
                blueprint_evaluation.nash_conv,
                information_sets,
            ),
            "current": _evaluation_record(
                control_current_evaluation,
                control_current,
                blueprint,
                blueprint_evaluation.nash_conv,
                information_sets,
            ),
        },
        "perturbed": {
            "information_sets": len(treatment_solver.information_sets),
            "average": _evaluation_record(
                treatment_average_evaluation,
                treatment_average,
                blueprint,
                blueprint_evaluation.nash_conv,
                information_sets,
            ),
            "current": _evaluation_record(
                treatment_current_evaluation,
                treatment_current,
                blueprint,
                blueprint_evaluation.nash_conv,
                information_sets,
            ),
        },
        "causal_effect": {
            "definition": "perturbed leaf result minus paired exact-leaf control",
            "average": _effect(
                treatment_average_evaluation,
                control_average_evaluation,
                treatment_average,
                control_average,
                information_sets,
            ),
            "current": _effect(
                treatment_current_evaluation,
                control_current_evaluation,
                treatment_current,
                control_current,
                information_sets,
            ),
        },
        "oracle_no_op_selection": {
            "warning": (
                "diagnostic upper bound only; full-game NashConv is not "
                "available to an online agent"
            ),
            "exact_control_average": _oracle_no_op_selection(
                control_average_evaluation,
                blueprint_evaluation,
            ),
            "exact_control_current": _oracle_no_op_selection(
                control_current_evaluation,
                blueprint_evaluation,
            ),
            "perturbed_average": _oracle_no_op_selection(
                treatment_average_evaluation,
                blueprint_evaluation,
            ),
            "perturbed_current": _oracle_no_op_selection(
                treatment_current_evaluation,
                blueprint_evaluation,
            ),
        },
    }
    result["timing"]["wall_seconds"] = time.perf_counter() - experiment_start
    return result


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, help="JSON configuration file")
    parser.add_argument("--game", choices=[f"kuhn{players}" for players in range(2, 7)])
    parser.add_argument("--blueprint-solver", choices=sorted(SOLVERS))
    parser.add_argument("--blueprint-iterations", type=int)
    parser.add_argument("--search-solver", choices=sorted(SOLVERS))
    parser.add_argument("--search-iterations", type=int)
    parser.add_argument("--depth-limit", type=int)
    parser.add_argument("--leaf-error-scale", type=float)
    parser.add_argument("--leaf-error-target-on-policy-root-l2", type=float)
    parser.add_argument("--leaf-error-seed", type=int)
    parser.add_argument("--warm-start-regret-mass", type=float)
    parser.add_argument("--in-search-blueprint-weight", type=float)
    parser.add_argument("--output-candidate-weight", type=float)
    parser.add_argument("--leaf-error-grouping", choices=sorted(ERROR_GROUPINGS))
    parser.add_argument("--leaf-error-scope", choices=sorted(ERROR_SCOPES))
    parser.add_argument("--leaf-error-scope-actions", nargs="+")
    parser.add_argument("--leaf-error-bias", nargs="+", type=float)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    config: dict[str, Any] = {}
    if args.config is not None:
        config = json.loads(args.config.read_text(encoding="utf-8"))
    for name in (
        "game",
        "blueprint_solver",
        "blueprint_iterations",
        "search_solver",
        "search_iterations",
        "depth_limit",
        "leaf_error_scale",
        "leaf_error_target_on_policy_root_l2",
        "leaf_error_seed",
        "warm_start_regret_mass",
        "in_search_blueprint_weight",
        "output_candidate_weight",
        "leaf_error_grouping",
        "leaf_error_scope",
        "leaf_error_scope_actions",
        "leaf_error_bias",
    ):
        value = getattr(args, name)
        if value is not None:
            config[name] = value

    result = run_leaf_experiment(config)
    rendered = json.dumps(result, indent=2, sort_keys=True)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")

    effect = result["causal_effect"]["average"]
    print(
        f"{result['config']['search_solver']} paired leaf experiment on "
        f"{result['config']['game']}: leaf_rmse={result['leaf_error']['rmse']:.8f}, "
        f"nash_conv_delta={effect['nash_conv_delta']:.8f}, "
        f"mean_policy_tv={effect['mean_information_set_total_variation']:.8f}"
    )
    if args.output is not None:
        print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
