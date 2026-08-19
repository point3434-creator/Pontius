"""Matrix runner for exact safe-strategy objective comparisons."""

from __future__ import annotations

import argparse
import json
import time
from itertools import product
from math import prod
from pathlib import Path
from statistics import mean, median
from typing import Any

from .leaf_experiment import PreparedBlueprint, prepare_blueprint
from .reporting import environment_metadata
from .safe_oracle_experiment import run_safe_oracle_experiment

CONFIG_FIELDS = {
    "game",
    "blueprint_solver",
    "blueprint_iterations",
    "max_pure_plans",
    "tolerance",
}
ARCHITECTURES = ("max_min", "sum_margin", "hidden_best_response_greedy")


def _compact_architecture(data: dict[str, Any]) -> dict[str, Any]:
    candidate = data["candidate"]
    return {
        "objective_name": data["objective_name"],
        "full_game_target_used": data["full_game_target_used"],
        "nash_conv": candidate["nash_conv"],
        "nash_conv_improvement_over_blueprint": candidate[
            "nash_conv_improvement_over_blueprint"
        ],
        "decision_compute_seconds": candidate["decision_compute_seconds"],
        "nash_conv_improvement_per_decision_compute_millisecond": candidate[
            "nash_conv_improvement_per_decision_compute_millisecond"
        ],
        "mean_policy_tv": candidate["policy_distance_from_blueprint"][
            "mean_information_set_total_variation"
        ],
        "cumulative_exploitability_increase_bound": data[
            "cumulative_exploitability_increase_bound"
        ],
        "residual_adjusted_bound_holds": candidate[
            "residual_adjusted_bound_holds"
        ],
        "searched_public_histories": data["searched_public_histories"],
    }


def _compact_run(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "config": result["config"],
        "blueprint_nash_conv": result["blueprint"]["nash_conv"],
        **{
            architecture: _compact_architecture(result[architecture])
            for architecture in ARCHITECTURES
        },
        "paired": result["paired"],
        "wall_seconds": result["timing"]["wall_seconds"],
    }


def _architecture_summary(
    runs: list[dict[str, Any]],
    architecture: str,
) -> dict[str, Any]:
    candidates = [run[architecture] for run in runs]
    improvements = [
        float(candidate["nash_conv_improvement_over_blueprint"])
        for candidate in candidates
    ]
    milliseconds = [
        1_000.0 * float(candidate["decision_compute_seconds"])
        for candidate in candidates
    ]
    rates = [
        float(candidate["nash_conv_improvement_per_decision_compute_millisecond"])
        for candidate in candidates
        if candidate["nash_conv_improvement_per_decision_compute_millisecond"]
        is not None
    ]
    return {
        "cases": len(candidates),
        "positive_improvement": sum(value > 0.0 for value in improvements),
        "mean_nash_conv_improvement": mean(improvements),
        "median_nash_conv_improvement": median(improvements),
        "worst_nash_conv_improvement": min(improvements),
        "best_nash_conv_improvement": max(improvements),
        "mean_decision_compute_milliseconds": mean(milliseconds),
        "mean_nash_conv_improvement_per_decision_compute_millisecond": mean(rates),
        "aggregate_nash_conv_improvement_per_decision_compute_millisecond": (
            sum(improvements) / sum(milliseconds)
        ),
        "residual_adjusted_bound_failures": sum(
            candidate["residual_adjusted_bound_holds"] is False
            for candidate in candidates
        ),
    }


def _paired_summary(runs: list[dict[str, Any]]) -> dict[str, Any]:
    max_min = [
        float(run["max_min"]["nash_conv_improvement_over_blueprint"])
        for run in runs
    ]
    summed = [
        float(run["sum_margin"]["nash_conv_improvement_over_blueprint"])
        for run in runs
    ]
    hidden = [
        float(
            run["hidden_best_response_greedy"][
                "nash_conv_improvement_over_blueprint"
            ]
        )
        for run in runs
    ]
    fractions = [
        float(run["paired"]["sum_margin_fraction_of_hidden_improvement"])
        for run in runs
        if run["paired"]["sum_margin_fraction_of_hidden_improvement"] is not None
    ]
    return {
        "sum_margin_beats_max_min": sum(
            summed_value > max_min_value
            for summed_value, max_min_value in zip(summed, max_min, strict=True)
        ),
        "hidden_beats_sum_margin": sum(
            hidden_value > summed_value + 1e-12
            for hidden_value, summed_value in zip(hidden, summed, strict=True)
        ),
        "mean_sum_margin_minus_max_min_improvement": mean(
            summed_value - max_min_value
            for summed_value, max_min_value in zip(summed, max_min, strict=True)
        ),
        "mean_hidden_minus_sum_margin_improvement": mean(
            hidden_value - summed_value
            for hidden_value, summed_value in zip(hidden, summed, strict=True)
        ),
        "mean_sum_margin_fraction_of_hidden_improvement": mean(fractions),
        "worst_sum_margin_fraction_of_hidden_improvement": min(fractions),
        "aggregate_sum_margin_fraction_of_hidden_improvement": (
            sum(summed) / sum(hidden)
        ),
    }


def run_safe_oracle_matrix(matrix_config: dict[str, Any]) -> dict[str, Any]:
    base = dict(matrix_config.get("base", {}))
    axes = dict(matrix_config.get("axes", {}))
    max_runs = int(matrix_config.get("max_runs", 10_000))
    store_full_runs = bool(matrix_config.get("store_full_runs", False))
    unknown = (set(base) | set(axes)) - CONFIG_FIELDS
    if unknown:
        raise ValueError(f"unknown safe-oracle fields: {sorted(unknown)!r}")
    if not axes:
        raise ValueError("matrix axes cannot be empty")
    if any(not isinstance(values, list) or not values for values in axes.values()):
        raise ValueError("every matrix axis must be a nonempty list")
    run_count = prod(len(values) for values in axes.values())
    if max_runs <= 0 or run_count > max_runs:
        raise ValueError(f"matrix contains {run_count} runs; max_runs is {max_runs}")

    started = time.perf_counter()
    environment = environment_metadata()
    axis_names = tuple(axes)
    compact_runs: list[dict[str, Any]] = []
    full_runs: list[dict[str, Any]] = []
    blueprints: dict[tuple[str, str, int], PreparedBlueprint] = {}
    for combination in product(*(axes[name] for name in axis_names)):
        config = dict(base)
        config.update(zip(axis_names, combination, strict=True))
        blueprint_key = (
            str(config.get("game", "kuhn2")),
            str(config.get("blueprint_solver", "lcfr")),
            int(config.get("blueprint_iterations", 1_000)),
        )
        prepared = blueprints.get(blueprint_key)
        if prepared is None:
            prepared = prepare_blueprint(*blueprint_key)
            blueprints[blueprint_key] = prepared
        result = run_safe_oracle_experiment(
            config,
            prepared_blueprint=prepared,
            environment=environment,
        )
        compact_runs.append(_compact_run(result))
        if store_full_runs:
            full_runs.append(result)

    output = {
        "schema_version": 1,
        "experiment_type": "exact_safe_strategy_objective_matrix",
        "matrix_config": {
            "base": base,
            "axes": axes,
            "max_runs": max_runs,
            "store_full_runs": store_full_runs,
        },
        "environment": environment,
        "prepared_blueprints": len(blueprints),
        "run_count": run_count,
        "wall_seconds": time.perf_counter() - started,
        "architecture_summary": {
            architecture: _architecture_summary(compact_runs, architecture)
            for architecture in ARCHITECTURES
        },
        "paired_summary": _paired_summary(compact_runs),
        "runs": compact_runs,
    }
    if store_full_runs:
        output["full_runs"] = full_runs
    return output


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    result = run_safe_oracle_matrix(config)
    rendered = json.dumps(result, indent=2, sort_keys=True, allow_nan=False)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    paired = result["paired_summary"]
    print(
        f"safe objective matrix: runs={result['run_count']}, "
        f"sum>min={paired['sum_margin_beats_max_min']}, "
        f"capture={paired['aggregate_sum_margin_fraction_of_hidden_improvement']:.6f}, "
        f"wall={result['wall_seconds']:.3f}s"
    )
    if args.output is not None:
        print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
