"""Measure progressive CFR gadget policies against exact safe objectives."""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict
from math import isfinite
from pathlib import Path
from typing import Any

from .cfr import TabularCFR
from .continual import PublicHistory, public_belief, public_histories
from .evaluation import (
    Policy,
    best_response,
    collect_information_sets,
    policy_distribution,
)
from .game import Action
from .leaf_experiment import PreparedBlueprint, SOLVERS, prepare_blueprint
from .maxmargin import (
    ConstrainedOracleResult,
    solve_safe_best_response_subgame,
    solve_safe_sum_margin_subgame,
)
from .reporting import environment_metadata
from .safe_resolving import (
    CounterfactualFrontier,
    ResolvingGadgetGame,
    build_counterfactual_frontier,
    counterfactual_best_response_values,
)

CONFIG_FIELDS = {
    "game",
    "blueprint_solver",
    "blueprint_iterations",
    "search_solvers",
    "checkpoints",
    "output_policies",
    "initializations",
    "strict_frontier_tolerance",
    "oracle_tolerance",
    "max_pure_plans",
}
OUTPUT_POLICIES = {"average", "current"}
INITIALIZATION_SOURCES = {"none", "blueprint", "sum_margin_oracle"}


def _safe_rate(value: float, seconds: float) -> float | None:
    return value / (1_000.0 * seconds) if seconds > 0.0 else None


def _copy_policy(policy: Policy) -> Policy:
    return {key: dict(distribution) for key, distribution in policy.items()}


def _acting_player(
    game: Any,
    policy: Policy,
    history: PublicHistory,
) -> tuple[int, float]:
    belief = public_belief(game, policy, history)
    if belief is not None:
        return belief.acting_player, belief.public_reach_probability
    structural = public_belief(game, {}, history)
    if structural is None:
        raise AssertionError("uniform policy cannot reach a legal public history")
    return structural.acting_player, 0.0


def _parse_initializations(raw: Any) -> tuple[dict[str, Any], ...]:
    if raw is None:
        raw = [
            {"name": "cold", "source": "none"},
            {"name": "blueprint_10", "source": "blueprint", "regret_mass": 10.0},
            {
                "name": "sum_oracle_1000",
                "source": "sum_margin_oracle",
                "regret_mass": 1_000.0,
                "deployable": False,
            },
        ]
    if not isinstance(raw, list) or not raw:
        raise ValueError("initializations must be a nonempty list")
    parsed: list[dict[str, Any]] = []
    names: set[str] = set()
    for item in raw:
        if not isinstance(item, dict):
            raise ValueError("each initialization must be an object")
        unknown = set(item) - {"name", "source", "regret_mass", "deployable"}
        if unknown:
            raise ValueError(f"unknown initialization fields: {sorted(unknown)!r}")
        name = str(item.get("name", ""))
        source = str(item.get("source", ""))
        if not name or name in names:
            raise ValueError("initialization names must be nonempty and unique")
        if source not in INITIALIZATION_SOURCES:
            raise ValueError(f"unknown initialization source {source!r}")
        raw_mass = item.get("regret_mass")
        mass = None if raw_mass is None else float(raw_mass)
        if source == "none":
            if mass is not None:
                raise ValueError("cold initialization cannot have regret_mass")
        elif mass is None or not isfinite(mass) or mass <= 0.0:
            raise ValueError("warm initialization regret_mass must be positive")
        default_deployable = source != "sum_margin_oracle"
        deployable = bool(item.get("deployable", default_deployable))
        if source == "sum_margin_oracle" and deployable:
            raise ValueError("exact oracle initialization cannot be deployable")
        parsed.append(
            {
                "name": name,
                "source": source,
                "regret_mass": mass,
                "deployable": deployable,
            }
        )
        names.add(name)
    return tuple(parsed)


def _resolver_policy_distance(
    policy: Policy,
    target: Policy,
    information_sets: dict[str, tuple[Action, ...]],
) -> float:
    distances = []
    for key, actions in information_sets.items():
        candidate = policy_distribution(policy, key, actions)
        reference = policy_distribution(target, key, actions)
        distances.append(
            0.5
            * sum(abs(candidate[action] - reference[action]) for action in actions)
        )
    return sum(distances) / len(distances)


def _deploy_resolver_component(
    blueprint: Policy,
    gadget_policy: Policy,
    information_sets: dict[str, tuple[Action, ...]],
) -> Policy:
    missing = set(information_sets) - set(gadget_policy)
    if missing:
        raise ValueError(f"solver omitted resolver information sets {sorted(missing)!r}")
    result = _copy_policy(blueprint)
    for key in information_sets:
        result[key] = dict(gadget_policy[key])
    return result


def _score_candidate(
    game: Any,
    blueprint: Policy,
    gadget_policy: Policy,
    frontier: CounterfactualFrontier,
    resolver_information_sets: dict[str, tuple[Action, ...]],
    sum_oracle: ConstrainedOracleResult,
    hidden_oracle: ConstrainedOracleResult,
    strict_tolerance: float,
    decision_base_seconds: float,
) -> dict[str, Any]:
    certificate_start = time.perf_counter()
    policy = _deploy_resolver_component(
        blueprint,
        gadget_policy,
        resolver_information_sets,
    )
    candidate_values = counterfactual_best_response_values(frontier, policy)
    margins = tuple(
        entry.blueprint_cbr_value - candidate_values[entry.key]
        for entry in frontier.entries
    )
    violations = tuple(max(0.0, -margin) for margin in margins)
    total_violation = sum(violations)
    certificate_seconds = time.perf_counter() - certificate_start
    safe = total_violation <= strict_tolerance
    signed_sum_margin = sum(margins)
    safe_sum_margin = signed_sum_margin if safe else 0.0

    diagnostic_start = time.perf_counter()
    candidate_best_response = best_response(
        game,
        policy,
        frontier.opponent_player,
    )[0]
    diagnostic_seconds = time.perf_counter() - diagnostic_start
    blueprint_best_response = hidden_oracle.blueprint_opponent_best_response_value
    if blueprint_best_response is None:
        raise AssertionError("hidden oracle omitted blueprint best response")
    opponent_br_reduction = blueprint_best_response - candidate_best_response
    safe_br_reduction = opponent_br_reduction if safe else 0.0
    sum_optimum = sum_oracle.verified_sum_margin
    hidden_optimum = hidden_oracle.verified_objective_value
    allowed = 1e-8 * max(1.0, abs(sum_optimum), abs(hidden_optimum))
    if safe and safe_sum_margin > sum_optimum + allowed:
        raise AssertionError("safe CFR candidate exceeds exact sum-margin optimum")
    if safe and safe_br_reduction > hidden_optimum + allowed:
        raise AssertionError("safe CFR candidate exceeds exact hidden optimum")
    decision_compute_seconds = decision_base_seconds + certificate_seconds

    return {
        "safe_at_strict_tolerance": safe,
        "minimum_frontier_margin": min(margins),
        "signed_sum_frontier_margin": signed_sum_margin,
        "positive_frontier_margin_sum": sum(max(0.0, margin) for margin in margins),
        "total_positive_frontier_violation": total_violation,
        "max_positive_frontier_violation": max(violations, default=0.0),
        "strict_sum_margin_score": safe_sum_margin,
        "sum_margin_regret_if_safe": (
            sum_optimum - signed_sum_margin if safe else None
        ),
        "strict_sum_margin_regret": sum_optimum - safe_sum_margin,
        "strict_sum_margin_capture": (
            safe_sum_margin / sum_optimum if sum_optimum > strict_tolerance else None
        ),
        "opponent_best_response_value": candidate_best_response,
        "opponent_best_response_reduction": opponent_br_reduction,
        "strict_opponent_best_response_reduction": safe_br_reduction,
        "hidden_br_regret_if_safe": (
            hidden_optimum - opponent_br_reduction if safe else None
        ),
        "strict_hidden_br_regret": hidden_optimum - safe_br_reduction,
        "strict_hidden_br_capture": (
            safe_br_reduction / hidden_optimum
            if hidden_optimum > strict_tolerance
            else None
        ),
        "mean_resolver_tv_from_blueprint": _resolver_policy_distance(
            policy,
            blueprint,
            resolver_information_sets,
        ),
        "mean_resolver_tv_from_sum_oracle": _resolver_policy_distance(
            policy,
            sum_oracle.policy,
            resolver_information_sets,
        ),
        "gadget_security_residual": total_violation,
        "certificate_seconds": certificate_seconds,
        "hidden_diagnostic_seconds": diagnostic_seconds,
        "decision_compute_seconds": decision_compute_seconds,
        "raw_br_reduction_per_decision_compute_millisecond": _safe_rate(
            opponent_br_reduction,
            decision_compute_seconds,
        ),
        "strict_br_reduction_per_decision_compute_millisecond": _safe_rate(
            safe_br_reduction,
            decision_compute_seconds,
        ),
        "strict_sum_margin_per_decision_compute_millisecond": _safe_rate(
            safe_sum_margin,
            decision_compute_seconds,
        ),
        "frontier": [
            {
                "key": entry.key,
                "blueprint_cbr_value": entry.blueprint_cbr_value,
                "candidate_cbr_value": candidate_values[entry.key],
                "margin": margin,
                "positive_violation": violation,
            }
            for entry, margin, violation in zip(
                frontier.entries,
                margins,
                violations,
                strict=True,
            )
        ],
    }


def _exact_boundary_record(
    sum_oracle: ConstrainedOracleResult,
    hidden_oracle: ConstrainedOracleResult,
) -> dict[str, Any]:
    return {
        "sum_margin": {
            "objective_value": sum_oracle.objective_value,
            "verified_sum_margin": sum_oracle.verified_sum_margin,
            "verified_min_margin": sum_oracle.verified_min_margin,
            "oracle_seconds": sum_oracle.oracle_seconds,
            "resolver_support_size": sum_oracle.resolver_support_size,
            "frontier": [asdict(record) for record in sum_oracle.frontier_records],
        },
        "hidden_best_response": {
            "objective_value": hidden_oracle.objective_value,
            "verified_best_response_reduction": (
                hidden_oracle.verified_objective_value
            ),
            "oracle_seconds": hidden_oracle.oracle_seconds,
            "resolver_support_size": hidden_oracle.resolver_support_size,
        },
    }


def _initialization_policy(
    initialization: dict[str, Any],
    blueprint: Policy,
    sum_oracle: ConstrainedOracleResult,
) -> Policy | None:
    source = initialization["source"]
    if source == "none":
        return None
    if source == "blueprint":
        return blueprint
    if source == "sum_margin_oracle":
        return sum_oracle.policy
    raise AssertionError(f"unhandled initialization source {source!r}")


def _run_trajectory(
    game: Any,
    blueprint: Policy,
    gadget: ResolvingGadgetGame,
    frontier: CounterfactualFrontier,
    resolver_information_sets: dict[str, tuple[Action, ...]],
    sum_oracle: ConstrainedOracleResult,
    hidden_oracle: ConstrainedOracleResult,
    solver_name: str,
    initialization: dict[str, Any],
    checkpoints: tuple[int, ...],
    output_policies: tuple[str, ...],
    strict_tolerance: float,
    frontier_setup_seconds: float,
) -> dict[str, Any]:
    initialization_start = time.perf_counter()
    solver = TabularCFR(gadget, variant=solver_name)
    warm_policy = _initialization_policy(initialization, blueprint, sum_oracle)
    if warm_policy is not None:
        solver.warm_start(warm_policy, initialization["regret_mass"])
    solver_initialization_seconds = time.perf_counter() - initialization_start

    cumulative_iteration_seconds = 0.0
    cumulative_monitoring_certificate_seconds = 0.0
    previous_checkpoint = 0
    incumbent = {
        "source": "blueprint",
        "source_output_policy": None,
        "source_checkpoint": 0,
        "strict_sum_margin_score": 0.0,
        "strict_opponent_best_response_reduction": 0.0,
        "mean_resolver_tv_from_blueprint": 0.0,
    }
    checkpoint_records: list[dict[str, Any]] = []
    for checkpoint in checkpoints:
        iteration_start = time.perf_counter()
        solver.run(checkpoint - previous_checkpoint)
        cumulative_iteration_seconds += time.perf_counter() - iteration_start
        previous_checkpoint = checkpoint
        decision_base_seconds = (
            frontier_setup_seconds
            + solver_initialization_seconds
            + cumulative_iteration_seconds
        )
        candidates: dict[str, dict[str, Any]] = {}
        for output_policy in output_policies:
            gadget_policy = (
                solver.average_strategy()
                if output_policy == "average"
                else solver.current_strategy()
            )
            candidate = _score_candidate(
                game,
                blueprint,
                gadget_policy,
                frontier,
                resolver_information_sets,
                sum_oracle,
                hidden_oracle,
                strict_tolerance,
                decision_base_seconds,
            )
            candidate["output_policy"] = output_policy
            candidates[output_policy] = candidate
            cumulative_monitoring_certificate_seconds += candidate[
                "certificate_seconds"
            ]
            if (
                candidate["safe_at_strict_tolerance"]
                and candidate["signed_sum_frontier_margin"]
                > incumbent["strict_sum_margin_score"] + strict_tolerance
            ):
                incumbent = {
                    "source": "solver_snapshot",
                    "source_output_policy": output_policy,
                    "source_checkpoint": checkpoint,
                    "strict_sum_margin_score": candidate[
                        "signed_sum_frontier_margin"
                    ],
                    "strict_opponent_best_response_reduction": candidate[
                        "opponent_best_response_reduction"
                    ],
                    "mean_resolver_tv_from_blueprint": candidate[
                        "mean_resolver_tv_from_blueprint"
                    ],
                }

        incumbent_decision_seconds = (
            decision_base_seconds + cumulative_monitoring_certificate_seconds
        )
        incumbent_record = {
            **incumbent,
            "sum_margin_regret": (
                sum_oracle.verified_sum_margin
                - incumbent["strict_sum_margin_score"]
            ),
            "sum_margin_capture": (
                incumbent["strict_sum_margin_score"]
                / sum_oracle.verified_sum_margin
                if sum_oracle.verified_sum_margin > strict_tolerance
                else None
            ),
            "hidden_br_regret": (
                hidden_oracle.verified_objective_value
                - incumbent["strict_opponent_best_response_reduction"]
            ),
            "hidden_br_capture": (
                incumbent["strict_opponent_best_response_reduction"]
                / hidden_oracle.verified_objective_value
                if hidden_oracle.verified_objective_value > strict_tolerance
                else None
            ),
            "monitoring_certificate_seconds": (
                cumulative_monitoring_certificate_seconds
            ),
            "decision_compute_seconds": incumbent_decision_seconds,
            "sum_margin_per_decision_compute_millisecond": _safe_rate(
                incumbent["strict_sum_margin_score"],
                incumbent_decision_seconds,
            ),
            "br_reduction_per_decision_compute_millisecond": _safe_rate(
                incumbent["strict_opponent_best_response_reduction"],
                incumbent_decision_seconds,
            ),
        }
        checkpoint_records.append(
            {
                "checkpoint": checkpoint,
                "cumulative_iteration_seconds": cumulative_iteration_seconds,
                "candidates": candidates,
                "incumbent": incumbent_record,
            }
        )

    return {
        "search_solver": solver.variant,
        "initialization": dict(initialization),
        "frontier_setup_seconds": frontier_setup_seconds,
        "solver_initialization_seconds": solver_initialization_seconds,
        "checkpoints": checkpoint_records,
    }


def run_safe_solver_gap_experiment(
    config: dict[str, Any],
    *,
    prepared_blueprint: PreparedBlueprint | None = None,
    environment: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run progressive gadget solvers against exact boundary objectives."""

    unknown = set(config) - CONFIG_FIELDS
    if unknown:
        raise ValueError(f"unknown safe-solver-gap fields: {sorted(unknown)!r}")
    game_name = str(config.get("game", "kuhn2"))
    blueprint_solver_name = str(config.get("blueprint_solver", "lcfr"))
    blueprint_iterations = int(config.get("blueprint_iterations", 1_000))
    search_solvers = tuple(
        str(value)
        for value in config.get("search_solvers", ["lcfr", "cfr_plus"])
    )
    checkpoints = tuple(
        int(value) for value in config.get("checkpoints", [1, 10, 100, 1_000])
    )
    output_policies = tuple(
        str(value)
        for value in config.get("output_policies", ["average", "current"])
    )
    initializations = _parse_initializations(config.get("initializations"))
    strict_tolerance = float(config.get("strict_frontier_tolerance", 1e-10))
    oracle_tolerance = float(config.get("oracle_tolerance", 1e-10))
    max_pure_plans = int(config.get("max_pure_plans", 1_000_000))
    if game_name != "kuhn2":
        raise ValueError("safe solver gap experiment currently requires kuhn2")
    if blueprint_solver_name not in SOLVERS:
        raise ValueError(f"unsupported blueprint solver {blueprint_solver_name!r}")
    if not search_solvers or len(set(search_solvers)) != len(search_solvers):
        raise ValueError("search_solvers must be nonempty and unique")
    if any(solver not in SOLVERS for solver in search_solvers):
        raise ValueError("search_solvers contains an unsupported solver")
    if (
        not checkpoints
        or tuple(sorted(set(checkpoints))) != checkpoints
        or checkpoints[0] <= 0
    ):
        raise ValueError("checkpoints must be positive, unique, and increasing")
    if (
        not output_policies
        or len(set(output_policies)) != len(output_policies)
        or any(value not in OUTPUT_POLICIES for value in output_policies)
    ):
        raise ValueError("output_policies must be unique average/current values")
    if blueprint_iterations <= 0 or max_pure_plans <= 0:
        raise ValueError("blueprint iterations and max_pure_plans must be positive")
    if not isfinite(strict_tolerance) or strict_tolerance < 0.0:
        raise ValueError("strict_frontier_tolerance must be finite and nonnegative")
    if not isfinite(oracle_tolerance) or oracle_tolerance <= 0.0:
        raise ValueError("oracle_tolerance must be finite and positive")

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
        raise ValueError("prepared blueprint does not match solver-gap configuration")

    game = prepared_blueprint.game
    blueprint = prepared_blueprint.policy
    boundaries: list[dict[str, Any]] = []
    for history in public_histories(game):
        resolver_player, public_reach = _acting_player(game, blueprint, history)
        setup_start = time.perf_counter()
        frontier = build_counterfactual_frontier(
            game,
            blueprint,
            history,
            resolver_player,
        )
        gadget = ResolvingGadgetGame(frontier)
        resolver_information_sets = collect_information_sets(
            gadget,
            resolver_player,
        )
        frontier_setup_seconds = time.perf_counter() - setup_start
        sum_oracle = solve_safe_sum_margin_subgame(
            game,
            blueprint,
            history,
            resolver_player,
            max_pure_plans=max_pure_plans,
            tolerance=oracle_tolerance,
        )
        hidden_oracle = solve_safe_best_response_subgame(
            game,
            blueprint,
            history,
            resolver_player,
            max_pure_plans=max_pure_plans,
            tolerance=oracle_tolerance,
        )
        if frontier.entries != sum_oracle.frontier.entries:
            raise AssertionError("candidate and oracle frontiers differ")

        trajectories = [
            _run_trajectory(
                game,
                blueprint,
                gadget,
                frontier,
                resolver_information_sets,
                sum_oracle,
                hidden_oracle,
                solver_name,
                initialization,
                checkpoints,
                output_policies,
                strict_tolerance,
                frontier_setup_seconds,
            )
            for solver_name in search_solvers
            for initialization in initializations
        ]
        boundaries.append(
            {
                "history": list(history),
                "resolver_player": resolver_player,
                "opponent_player": frontier.opponent_player,
                "public_reach_probability": public_reach,
                "opponent_counterfactual_reach": (
                    frontier.total_counterfactual_reach
                ),
                "frontier_information_sets": len(frontier.entries),
                "resolver_information_sets": len(resolver_information_sets),
                "frontier_setup_seconds": frontier_setup_seconds,
                "exact": _exact_boundary_record(sum_oracle, hidden_oracle),
                "trajectories": trajectories,
            }
        )

    result = {
        "schema_version": 1,
        "experiment_type": "safe_solver_objective_gap_trajectories",
        "config": {
            "game": game_name,
            "blueprint_solver": blueprint_solver_name,
            "blueprint_iterations": blueprint_iterations,
            "search_solvers": list(search_solvers),
            "checkpoints": list(checkpoints),
            "output_policies": list(output_policies),
            "initializations": [dict(item) for item in initializations],
            "strict_frontier_tolerance": strict_tolerance,
            "oracle_tolerance": oracle_tolerance,
            "max_pure_plans": max_pure_plans,
        },
        "environment": environment_metadata() if environment is None else environment,
        "protocol": {
            "candidate_target": "terminate/follow gadget only",
            "strict_candidate": "unsafe snapshots become blueprint no-op",
            "incumbent_selection": "best certified sum margin seen so far",
            "incumbent_starts_at_blueprint": True,
            "full_game_target_enters_candidate_construction": False,
            "hidden_best_response_is_diagnostic_only": True,
            "sum_oracle_initialization_is_diagnostic_only": True,
            "candidate_timing_excludes_hidden_diagnostics": True,
            "multiplayer_claim": False,
        },
        "timing": {
            "blueprint_prepared_in_run": blueprint_prepared_in_run,
            "blueprint_solver_seconds": prepared_blueprint.solver_seconds,
            "blueprint_full_evaluation_seconds": (
                prepared_blueprint.evaluation_seconds
            ),
        },
        "blueprint": asdict(prepared_blueprint.evaluation),
        "boundaries": boundaries,
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
    result = run_safe_solver_gap_experiment(config)
    rendered = json.dumps(result, indent=2, sort_keys=True, allow_nan=False)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(
        f"safe solver gaps on {result['config']['game']}: "
        f"boundaries={len(result['boundaries'])}, "
        f"wall={result['timing']['wall_seconds']:.3f}s"
    )
    if args.output is not None:
        print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
