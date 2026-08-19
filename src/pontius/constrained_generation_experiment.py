"""Measure dynamic constrained generation against exact safe-objective teachers."""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict
from math import isfinite
from pathlib import Path
from typing import Any

from .constrained_generation import solve_sum_margin_with_generation
from .continual import public_belief, public_histories
from .leaf_experiment import PreparedBlueprint, SOLVERS, prepare_blueprint
from .reporting import environment_metadata

CONFIG_FIELDS = {
    "game",
    "blueprint_solver",
    "blueprint_iterations",
    "max_updates",
    "max_pure_plans",
    "tolerance",
    "verify_generated_responses",
    "verify_realization_equivalence",
    "price_after_last_update",
}


def run_constrained_generation_experiment(
    config: dict[str, Any],
    *,
    prepared_blueprint: PreparedBlueprint | None = None,
    environment: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run every Kuhn2 public boundary with one prepared blueprint."""

    unknown = set(config) - CONFIG_FIELDS
    if unknown:
        raise ValueError(f"unknown constrained-generation fields: {sorted(unknown)!r}")
    game_name = str(config.get("game", "kuhn2"))
    blueprint_solver = str(config.get("blueprint_solver", "lcfr"))
    blueprint_iterations = int(config.get("blueprint_iterations", 1_000))
    max_updates = int(config.get("max_updates", 20))
    max_pure_plans = int(config.get("max_pure_plans", 1_000_000))
    tolerance = float(config.get("tolerance", 1e-10))
    raw_verify_responses = config.get("verify_generated_responses", True)
    raw_verify_realization = config.get("verify_realization_equivalence", True)
    raw_terminal_pricing = config.get("price_after_last_update", True)
    if not all(
        isinstance(value, bool)
        for value in (
            raw_verify_responses,
            raw_verify_realization,
            raw_terminal_pricing,
        )
    ):
        raise ValueError("phase controls must be boolean")
    verify_generated_responses = raw_verify_responses
    verify_realization_equivalence = raw_verify_realization
    price_after_last_update = raw_terminal_pricing
    if game_name != "kuhn2":
        raise ValueError("constrained-generation experiment currently requires kuhn2")
    if blueprint_solver not in SOLVERS:
        raise ValueError(f"unsupported blueprint solver {blueprint_solver!r}")
    if blueprint_iterations <= 0 or max_updates <= 0 or max_pure_plans <= 0:
        raise ValueError("iterations, updates, and pure-plan limit must be positive")
    if not isfinite(tolerance) or tolerance <= 0.0:
        raise ValueError("tolerance must be finite and positive")

    wall_start = time.perf_counter()
    blueprint_prepared_in_run = prepared_blueprint is None
    if prepared_blueprint is None:
        prepared_blueprint = prepare_blueprint(
            game_name,
            blueprint_solver,
            blueprint_iterations,
        )
    elif (
        prepared_blueprint.game_name != game_name
        or prepared_blueprint.solver_name != blueprint_solver
        or prepared_blueprint.iterations != blueprint_iterations
    ):
        raise ValueError(
            "prepared blueprint does not match constrained-generation configuration"
        )

    game = prepared_blueprint.game
    blueprint = prepared_blueprint.policy
    boundaries: list[dict[str, Any]] = []
    for history in public_histories(game):
        belief = public_belief(game, blueprint, history)
        if belief is None:
            structural = public_belief(game, {}, history)
            if structural is None:
                raise AssertionError("uniform policy cannot reach a legal history")
            resolver_player = structural.acting_player
            public_reach_probability = 0.0
        else:
            resolver_player = belief.acting_player
            public_reach_probability = belief.public_reach_probability
        generated = solve_sum_margin_with_generation(
            game,
            blueprint,
            history,
            resolver_player,
            max_updates=max_updates,
            max_pure_plans=max_pure_plans,
            tolerance=tolerance,
            verify_generated_responses=verify_generated_responses,
            verify_realization_equivalence=verify_realization_equivalence,
            price_after_last_update=price_after_last_update,
        )
        boundaries.append(
            {
                "history": [list(action) for action in history],
                "resolver_player": resolver_player,
                "public_reach_probability": public_reach_probability,
                "frontier_entries": [
                    asdict(entry) for entry in generated.frontier.entries
                ],
                "exact_sum_margin_optimum": generated.exact_sum_margin_optimum,
                "exact_hidden_br_optimum": generated.exact_hidden_br_optimum,
                "exact_oracle_seconds_excluded": generated.exact_oracle_seconds,
                "resolver_normal_form_plans": (
                    generated.resolver_normal_form_plans
                ),
                "final_columns": generated.final_columns,
                "final_response_constraints": (
                    generated.final_response_constraints
                ),
                "converged": generated.converged,
                "updates_executed": len(generated.updates),
                "incumbent_sum_margin": generated.incumbent_sum_margin,
                "incumbent_hidden_br_reduction": (
                    generated.incumbent_hidden_br_reduction
                ),
                "decision_compute_seconds": generated.decision_compute_seconds,
                "setup_seconds": generated.setup_seconds,
                "master_build_seconds": generated.total_master_build_seconds,
                "master_solve_seconds": generated.total_master_solve_seconds,
                "policy_conversion_seconds": (
                    generated.total_policy_conversion_seconds
                ),
                "separation_seconds": generated.total_separation_seconds,
                "pricing_seconds": generated.total_pricing_seconds,
                "hidden_diagnostic_seconds_excluded": (
                    generated.total_hidden_diagnostic_seconds
                ),
                "updates": [asdict(update) for update in generated.updates],
            }
        )

    return {
        "schema_version": 1,
        "experiment_type": "dynamic_constrained_generation",
        "config": {
            "game": game_name,
            "blueprint_solver": blueprint_solver,
            "blueprint_iterations": blueprint_iterations,
            "max_updates": max_updates,
            "max_pure_plans": max_pure_plans,
            "tolerance": tolerance,
            "verify_generated_responses": verify_generated_responses,
            "verify_realization_equivalence": verify_realization_equivalence,
            "price_after_last_update": price_after_last_update,
        },
        "environment": environment_metadata() if environment is None else environment,
        "blueprint": {
            "nash_conv": prepared_blueprint.evaluation.nash_conv,
            "exploitability": prepared_blueprint.evaluation.exploitability,
            "solver_seconds": prepared_blueprint.solver_seconds,
            "evaluation_seconds": prepared_blueprint.evaluation_seconds,
            "prepared_in_run": blueprint_prepared_in_run,
        },
        "boundaries": boundaries,
        "protocol": {
            "initial_column": "complete behavioral blueprint",
            "row_oracle": "dynamic opponent counterfactual best response",
            "row_oracle_reverified_with_duplicate_traversal": (
                verify_generated_responses
            ),
            "mixture_realization_reverified_on_active_rows": (
                verify_realization_equivalence
            ),
            "column_oracle": "LP-dual-weighted dynamic resolver best response",
            "incumbent": "safe maximum observed target-free sum margin",
            "full_game_target_used_for_construction": False,
            "exact_normal_form_used_for_construction": False,
            "exact_normal_form_role": "excluded correctness and regret teacher",
            "hidden_best_response_role": "excluded diagnostic only",
            "decision_timing_includes": [
                "setup",
                "restricted-master build",
                "restricted-master solve",
                "mixed-to-behavioral conversion",
                "response separation",
                "resolver pricing",
            ],
            "candidate_checkpoint_excludes_current_pricing": True,
        },
        "timing": {
            "wall_seconds": time.perf_counter() - wall_start,
        },
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    result = run_constrained_generation_experiment(config)
    rendered = json.dumps(result, indent=2, sort_keys=True, allow_nan=False)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(
        "constrained generation: "
        f"boundaries={len(result['boundaries'])}, "
        f"wall={result['timing']['wall_seconds']:.3f}s"
    )
    if args.output is not None:
        print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
