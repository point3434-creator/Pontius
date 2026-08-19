"""Aggregate progressive safe-solver objective gaps across blueprints."""

from __future__ import annotations

import argparse
import json
import time
from collections import defaultdict
from itertools import product
from math import prod
from pathlib import Path
from statistics import mean, median
from typing import Any

from .leaf_experiment import PreparedBlueprint, prepare_blueprint
from .reporting import environment_metadata
from .safe_solver_gap_experiment import (
    CONFIG_FIELDS,
    run_safe_solver_gap_experiment,
)

CANDIDATE_GROUP_FIELDS = (
    "search_solver",
    "initialization_name",
    "output_policy",
    "checkpoint",
)
INCUMBENT_GROUP_FIELDS = (
    "search_solver",
    "initialization_name",
    "checkpoint",
)


def _history_key(history: list[Any]) -> str:
    return json.dumps(history, separators=(",", ":"))


def _flatten_run(
    result: dict[str, Any],
    run_index: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    candidates: list[dict[str, Any]] = []
    incumbents: list[dict[str, Any]] = []
    config = result["config"]
    for boundary in result["boundaries"]:
        history = boundary["history"]
        boundary_id = (
            f"{config['blueprint_solver']}:{config['blueprint_iterations']}:"
            f"{_history_key(history)}"
        )
        sum_optimum = boundary["exact"]["sum_margin"]["verified_sum_margin"]
        hidden_optimum = boundary["exact"]["hidden_best_response"][
            "verified_best_response_reduction"
        ]
        for trajectory in boundary["trajectories"]:
            initialization = trajectory["initialization"]
            common = {
                "run_index": run_index,
                "boundary_id": boundary_id,
                "blueprint_solver": config["blueprint_solver"],
                "blueprint_iterations": config["blueprint_iterations"],
                "history": history,
                "resolver_player": boundary["resolver_player"],
                "public_reach_probability": boundary[
                    "public_reach_probability"
                ],
                "sum_margin_optimum": sum_optimum,
                "hidden_br_optimum": hidden_optimum,
                "search_solver": trajectory["search_solver"],
                "initialization_name": initialization["name"],
                "initialization_source": initialization["source"],
                "initialization_regret_mass": initialization["regret_mass"],
                "initialization_deployable": initialization["deployable"],
            }
            for checkpoint in trajectory["checkpoints"]:
                checkpoint_value = checkpoint["checkpoint"]
                for output_policy, candidate in checkpoint["candidates"].items():
                    candidates.append(
                        {
                            **common,
                            "checkpoint": checkpoint_value,
                            "output_policy": output_policy,
                            **{
                                key: value
                                for key, value in candidate.items()
                                if key != "frontier"
                            },
                        }
                    )
                incumbents.append(
                    {
                        **common,
                        "checkpoint": checkpoint_value,
                        **checkpoint["incumbent"],
                    }
                )
    return candidates, incumbents


def _group_records(
    records: list[dict[str, Any]],
    fields: tuple[str, ...],
) -> dict[tuple[Any, ...], list[dict[str, Any]]]:
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[tuple(record[field] for field in fields)].append(record)
    return dict(grouped)


def _candidate_summary(
    key: tuple[Any, ...],
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    milliseconds = [1_000.0 * row["decision_compute_seconds"] for row in records]
    strict_sum = [row["strict_sum_margin_score"] for row in records]
    strict_hidden = [
        row["strict_opponent_best_response_reduction"] for row in records
    ]
    sum_optima = [row["sum_margin_optimum"] for row in records]
    hidden_optima = [row["hidden_br_optimum"] for row in records]
    return {
        **dict(zip(CANDIDATE_GROUP_FIELDS, key, strict=True)),
        "initialization_source": records[0]["initialization_source"],
        "initialization_regret_mass": records[0]["initialization_regret_mass"],
        "initialization_deployable": records[0]["initialization_deployable"],
        "cases": len(records),
        "safe_cases": sum(row["safe_at_strict_tolerance"] for row in records),
        "safe_fraction": mean(
            float(row["safe_at_strict_tolerance"]) for row in records
        ),
        "raw_harmful_cases": sum(
            row["opponent_best_response_reduction"] < -1e-12 for row in records
        ),
        "strict_positive_cases": sum(value > 1e-12 for value in strict_hidden),
        "mean_total_positive_frontier_violation": mean(
            row["total_positive_frontier_violation"] for row in records
        ),
        "median_total_positive_frontier_violation": median(
            row["total_positive_frontier_violation"] for row in records
        ),
        "mean_resolver_tv_from_blueprint": mean(
            row["mean_resolver_tv_from_blueprint"] for row in records
        ),
        "mean_resolver_tv_from_sum_oracle": mean(
            row["mean_resolver_tv_from_sum_oracle"] for row in records
        ),
        "mean_strict_sum_margin_score": mean(strict_sum),
        "mean_strict_opponent_br_reduction": mean(strict_hidden),
        "aggregate_strict_sum_margin_capture": sum(strict_sum) / sum(sum_optima),
        "aggregate_strict_hidden_br_capture": (
            sum(strict_hidden) / sum(hidden_optima)
        ),
        "mean_decision_compute_milliseconds": mean(milliseconds),
        "mean_certificate_milliseconds": mean(
            1_000.0 * row["certificate_seconds"] for row in records
        ),
        "aggregate_strict_sum_margin_per_decision_millisecond": (
            sum(strict_sum) / sum(milliseconds)
        ),
        "aggregate_strict_br_reduction_per_decision_millisecond": (
            sum(strict_hidden) / sum(milliseconds)
        ),
    }


def _incumbent_summary(
    key: tuple[Any, ...],
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    milliseconds = [1_000.0 * row["decision_compute_seconds"] for row in records]
    sum_scores = [row["strict_sum_margin_score"] for row in records]
    hidden_scores = [
        row["strict_opponent_best_response_reduction"] for row in records
    ]
    sum_optima = [row["sum_margin_optimum"] for row in records]
    hidden_optima = [row["hidden_br_optimum"] for row in records]
    return {
        **dict(zip(INCUMBENT_GROUP_FIELDS, key, strict=True)),
        "initialization_source": records[0]["initialization_source"],
        "initialization_regret_mass": records[0]["initialization_regret_mass"],
        "initialization_deployable": records[0]["initialization_deployable"],
        "cases": len(records),
        "solver_selected_cases": sum(
            row["source"] == "solver_snapshot" for row in records
        ),
        "blueprint_no_op_cases": sum(row["source"] == "blueprint" for row in records),
        "selected_average_cases": sum(
            row["source_output_policy"] == "average" for row in records
        ),
        "selected_current_cases": sum(
            row["source_output_policy"] == "current" for row in records
        ),
        "mean_selected_source_checkpoint": mean(
            row["source_checkpoint"] for row in records
        ),
        "positive_hidden_improvement_cases": sum(
            value > 1e-12 for value in hidden_scores
        ),
        "mean_sum_margin_score": mean(sum_scores),
        "mean_opponent_br_reduction": mean(hidden_scores),
        "aggregate_sum_margin_capture": sum(sum_scores) / sum(sum_optima),
        "aggregate_hidden_br_capture": sum(hidden_scores) / sum(hidden_optima),
        "mean_decision_compute_milliseconds": mean(milliseconds),
        "mean_monitoring_certificate_milliseconds": mean(
            1_000.0 * row["monitoring_certificate_seconds"] for row in records
        ),
        "aggregate_sum_margin_per_decision_millisecond": (
            sum(sum_scores) / sum(milliseconds)
        ),
        "aggregate_br_reduction_per_decision_millisecond": (
            sum(hidden_scores) / sum(milliseconds)
        ),
    }


def _best_available_incumbent(
    summaries: list[dict[str, Any]],
) -> dict[str, Any] | None:
    available = [row for row in summaries if row["initialization_deployable"]]
    if not available:
        return None
    best = max(
        available,
        key=lambda row: (
            row["aggregate_sum_margin_per_decision_millisecond"],
            row["aggregate_sum_margin_capture"],
            -row["checkpoint"],
        ),
    )
    return {
        "selection_target": "target-free certified sum-margin per millisecond",
        "search_solver": best["search_solver"],
        "initialization_name": best["initialization_name"],
        "checkpoint": best["checkpoint"],
        "aggregate_sum_margin_capture": best["aggregate_sum_margin_capture"],
        "aggregate_hidden_br_capture_diagnostic": best[
            "aggregate_hidden_br_capture"
        ],
        "aggregate_sum_margin_per_decision_millisecond": best[
            "aggregate_sum_margin_per_decision_millisecond"
        ],
        "aggregate_br_reduction_per_decision_millisecond_diagnostic": best[
            "aggregate_br_reduction_per_decision_millisecond"
        ],
    }


def run_safe_solver_gap_matrix(matrix_config: dict[str, Any]) -> dict[str, Any]:
    base = dict(matrix_config.get("base", {}))
    axes = dict(matrix_config.get("axes", {}))
    max_runs = int(matrix_config.get("max_runs", 10_000))
    store_full_runs = bool(matrix_config.get("store_full_runs", False))
    store_records = bool(matrix_config.get("store_records", True))
    unknown = (set(base) | set(axes)) - CONFIG_FIELDS
    if unknown:
        raise ValueError(f"unknown safe-solver-gap fields: {sorted(unknown)!r}")
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
    full_runs: list[dict[str, Any]] = []
    compact_runs: list[dict[str, Any]] = []
    candidate_records: list[dict[str, Any]] = []
    incumbent_records: list[dict[str, Any]] = []
    blueprints: dict[tuple[str, str, int], PreparedBlueprint] = {}
    for run_index, combination in enumerate(
        product(*(axes[name] for name in axis_names))
    ):
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
        result = run_safe_solver_gap_experiment(
            config,
            prepared_blueprint=prepared,
            environment=environment,
        )
        candidates, incumbents = _flatten_run(result, run_index)
        candidate_records.extend(candidates)
        incumbent_records.extend(incumbents)
        compact_runs.append(
            {
                "config": result["config"],
                "blueprint_nash_conv": result["blueprint"]["nash_conv"],
                "boundaries": len(result["boundaries"]),
                "candidate_records": len(candidates),
                "incumbent_records": len(incumbents),
                "wall_seconds": result["timing"]["wall_seconds"],
            }
        )
        if store_full_runs:
            full_runs.append(result)

    candidate_summaries = [
        _candidate_summary(key, records)
        for key, records in sorted(
            _group_records(candidate_records, CANDIDATE_GROUP_FIELDS).items(),
            key=lambda item: repr(item[0]),
        )
    ]
    incumbent_summaries = [
        _incumbent_summary(key, records)
        for key, records in sorted(
            _group_records(incumbent_records, INCUMBENT_GROUP_FIELDS).items(),
            key=lambda item: repr(item[0]),
        )
    ]
    output = {
        "schema_version": 1,
        "experiment_type": "safe_solver_objective_gap_matrix",
        "matrix_config": {
            "base": base,
            "axes": axes,
            "max_runs": max_runs,
            "store_full_runs": store_full_runs,
            "store_records": store_records,
        },
        "environment": environment,
        "prepared_blueprints": len(blueprints),
        "run_count": run_count,
        "wall_seconds": time.perf_counter() - started,
        "candidate_record_count": len(candidate_records),
        "incumbent_record_count": len(incumbent_records),
        "candidate_summary": candidate_summaries,
        "incumbent_summary": incumbent_summaries,
        "best_available_initialization": _best_available_incumbent(
            incumbent_summaries
        ),
        "runs": compact_runs,
    }
    if store_records:
        output["candidate_records"] = candidate_records
        output["incumbent_records"] = incumbent_records
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
    result = run_safe_solver_gap_matrix(config)
    rendered = json.dumps(result, indent=2, sort_keys=True, allow_nan=False)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    best = result["best_available_initialization"]
    print(
        f"safe solver gap matrix: runs={result['run_count']}, "
        f"candidates={result['candidate_record_count']}, best={best}, "
        f"wall={result['wall_seconds']:.3f}s"
    )
    if args.output is not None:
        print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
