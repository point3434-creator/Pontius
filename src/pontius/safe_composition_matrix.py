"""Cartesian convergence and quality-per-millisecond safe-resolving matrix."""

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
from .safe_composition_experiment import run_safe_composition_experiment

CONFIG_FIELDS = {
    "game",
    "blueprint_solver",
    "blueprint_iterations",
    "search_solver",
    "search_iterations",
    "strict_frontier_tolerance",
}
ARCHITECTURES = ("safe_continual", "strict_safe_continual", "global_control")


def _compact_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
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
        "exploitability_increase_bound": candidate[
            "exploitability_increase_bound"
        ],
        "residual_adjusted_bound_holds": candidate[
            "residual_adjusted_bound_holds"
        ],
    }


def _compact_run(result: dict[str, Any]) -> dict[str, Any]:
    single_records = result["single_boundary"]["records"]
    compact: dict[str, Any] = {
        "config": result["config"],
        "blueprint_nash_conv": result["blueprint"]["nash_conv"],
        "single_boundary": {
            "cases": len(single_records),
            "positive_improvement": sum(
                record["candidate"]["nash_conv_improvement_over_blueprint"] > 0.0
                for record in single_records
            ),
            "bound_failures": sum(
                not record["candidate"]["residual_adjusted_bound_holds"]
                for record in single_records
            ),
            "mean_improvement": mean(
                record["candidate"]["nash_conv_improvement_over_blueprint"]
                for record in single_records
            ),
            "expected_decision_compute_seconds_per_hand": result[
                "single_boundary"
            ]["expected_decision_compute_seconds_per_hand"],
        },
        "wall_seconds": result["timing"]["wall_seconds"],
    }
    for architecture in ARCHITECTURES:
        data = result[architecture]
        compact[architecture] = {
            "candidate": _compact_candidate(data["candidate"]),
        }
        if architecture != "global_control":
            compact[architecture].update(
                {
                    "searched_public_histories": data[
                        "searched_public_histories"
                    ],
                    "deployed_public_histories": data[
                        "deployed_public_histories"
                    ],
                    "expected_certificate_seconds_per_hand": data[
                        "expected_certificate_seconds_per_hand"
                    ],
                    "cumulative_exploitability_increase_bound": data[
                        "cumulative_exploitability_increase_bound"
                    ],
                }
            )
    return compact


def _architecture_summary(
    runs: list[dict[str, Any]],
    architecture: str,
) -> dict[str, Any]:
    candidates = [run[architecture]["candidate"] for run in runs]
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
    bounds = [
        candidate["exploitability_increase_bound"] for candidate in candidates
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
        "mean_exploitability_increase_bound": (
            mean(float(value) for value in bounds if value is not None)
            if any(value is not None for value in bounds)
            else None
        ),
        "total_deployed_public_histories": (
            sum(run[architecture]["deployed_public_histories"] for run in runs)
            if architecture != "global_control"
            else None
        ),
    }


def _paired_summary(runs: list[dict[str, Any]]) -> dict[str, Any]:
    raw = [
        float(
            run["safe_continual"]["candidate"][
                "nash_conv_improvement_over_blueprint"
            ]
        )
        for run in runs
    ]
    strict = [
        float(
            run["strict_safe_continual"]["candidate"][
                "nash_conv_improvement_over_blueprint"
            ]
        )
        for run in runs
    ]
    global_control = [
        float(
            run["global_control"]["candidate"][
                "nash_conv_improvement_over_blueprint"
            ]
        )
        for run in runs
    ]
    return {
        "strict_minus_raw_mean_improvement": mean(
            strict_value - raw_value
            for strict_value, raw_value in zip(strict, raw, strict=True)
        ),
        "strict_beats_raw": sum(
            strict_value > raw_value
            for strict_value, raw_value in zip(strict, raw, strict=True)
        ),
        "global_beats_raw": sum(
            global_value > raw_value
            for global_value, raw_value in zip(
                global_control,
                raw,
                strict=True,
            )
        ),
        "global_beats_strict": sum(
            global_value > strict_value
            for global_value, strict_value in zip(
                global_control,
                strict,
                strict=True,
            )
        ),
    }


def run_safe_composition_matrix(matrix_config: dict[str, Any]) -> dict[str, Any]:
    base = dict(matrix_config.get("base", {}))
    axes = dict(matrix_config.get("axes", {}))
    max_runs = int(matrix_config.get("max_runs", 10_000))
    store_full_runs = bool(matrix_config.get("store_full_runs", False))
    unknown = (set(base) | set(axes)) - CONFIG_FIELDS
    if unknown:
        raise ValueError(f"unknown safe-composition fields: {sorted(unknown)!r}")
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
        result = run_safe_composition_experiment(
            config,
            prepared_blueprint=prepared,
            environment=environment,
        )
        compact_runs.append(_compact_run(result))
        if store_full_runs:
            full_runs.append(result)

    output = {
        "schema_version": 1,
        "experiment_type": "safe_resolver_composition_matrix",
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
        "single_boundary_summary": {
            "cases": sum(run["single_boundary"]["cases"] for run in compact_runs),
            "positive_improvement": sum(
                run["single_boundary"]["positive_improvement"]
                for run in compact_runs
            ),
            "bound_failures": sum(
                run["single_boundary"]["bound_failures"] for run in compact_runs
            ),
        },
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
    result = run_safe_composition_matrix(config)
    rendered = json.dumps(result, indent=2, sort_keys=True, allow_nan=False)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    summary = result["architecture_summary"]
    print(
        f"safe composition matrix: runs={result['run_count']}, "
        f"raw+={summary['safe_continual']['positive_improvement']}, "
        f"strict+={summary['strict_safe_continual']['positive_improvement']}, "
        f"global+={summary['global_control']['positive_improvement']}, "
        f"wall={result['wall_seconds']:.3f}s"
    )
    if args.output is not None:
        print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
