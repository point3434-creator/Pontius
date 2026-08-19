"""Aggregate anytime constrained-generation quality across blueprint regimes."""

from __future__ import annotations

import argparse
import json
import time
from itertools import product
from math import isfinite, prod
from pathlib import Path
from statistics import mean
from typing import Any

from .constrained_generation_experiment import (
    CONFIG_FIELDS,
    run_constrained_generation_experiment,
)
from .leaf_experiment import PreparedBlueprint, prepare_blueprint
from .reporting import environment_metadata


def _history_key(history: list[Any]) -> str:
    return json.dumps(history, separators=(",", ":"))


def _flatten_run(result: dict[str, Any], run_index: int) -> list[dict[str, Any]]:
    config = result["config"]
    records: list[dict[str, Any]] = []
    for boundary in result["boundaries"]:
        boundary_id = (
            f"{run_index}:{config['blueprint_solver']}:"
            f"{config['blueprint_iterations']}:{_history_key(boundary['history'])}"
        )
        build = 0.0
        solve = 0.0
        conversion = 0.0
        separation = 0.0
        pricing = 0.0
        hidden = 0.0
        unsafe = 0
        for update in boundary["updates"]:
            build += update["master_build_seconds"]
            solve += update["master_solve_seconds"]
            conversion += update["policy_conversion_seconds"]
            separation += update["separation_seconds"]
            pricing += update["pricing_seconds"]
            hidden += update["hidden_diagnostic_seconds"]
            unsafe += int(not update["safe_candidate"])
            records.append(
                {
                    **update,
                    "run_index": run_index,
                    "boundary_id": boundary_id,
                    "blueprint_solver": config["blueprint_solver"],
                    "blueprint_iterations": config["blueprint_iterations"],
                    "history": boundary["history"],
                    "resolver_player": boundary["resolver_player"],
                    "public_reach_probability": boundary[
                        "public_reach_probability"
                    ],
                    "exact_sum_margin_optimum": boundary[
                        "exact_sum_margin_optimum"
                    ],
                    "exact_hidden_br_optimum": boundary[
                        "exact_hidden_br_optimum"
                    ],
                    "final_converged": boundary["converged"],
                    "final_update": boundary["updates_executed"],
                    "resolver_normal_form_plans": boundary[
                        "resolver_normal_form_plans"
                    ],
                    "cumulative_unsafe_candidates": unsafe,
                    "cumulative_master_build_seconds": build,
                    "cumulative_master_solve_seconds": solve,
                    "cumulative_policy_conversion_seconds": conversion,
                    "cumulative_separation_seconds": separation,
                    "cumulative_pricing_seconds": pricing,
                    "cumulative_hidden_diagnostic_seconds_excluded": hidden,
                    "setup_seconds": boundary["setup_seconds"],
                    "columns_after_update": (
                        update["columns_before_update"]
                        + int(update["added_column"] is not None)
                    ),
                    "response_constraints_after_update": (
                        update["response_constraints_before_update"]
                        + update["added_response_constraints"]
                    ),
                }
            )
    return records


def _safe_ratio(numerator: float, denominator: float) -> float | None:
    return numerator / denominator if denominator > 0.0 else None


def _anytime_summary(
    records: list[dict[str, Any]],
    *,
    timing_field: str = "cumulative_decision_compute_seconds",
    checkpoint_phase: str = "after_pricing",
) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        grouped.setdefault(record["boundary_id"], []).append(record)
    for rows in grouped.values():
        rows.sort(key=lambda row: row["update"])
    maximum_budget = max(row["update"] for row in records)
    summaries: list[dict[str, Any]] = []
    for budget in range(1, maximum_budget + 1):
        selected = [
            max(
                (row for row in rows if row["update"] <= budget),
                key=lambda row: row["update"],
            )
            for rows in grouped.values()
        ]
        sum_score = sum(row["incumbent_sum_margin"] for row in selected)
        hidden_score = sum(
            row["incumbent_hidden_br_reduction"] for row in selected
        )
        sum_optimum = sum(
            row["exact_sum_margin_optimum"] for row in selected
        )
        hidden_optimum = sum(
            row["exact_hidden_br_optimum"] for row in selected
        )
        milliseconds = sum(
            1_000.0 * row[timing_field]
            for row in selected
        )
        summaries.append(
            {
                "checkpoint_phase": checkpoint_phase,
                "update_budget": budget,
                "cases": len(selected),
                "converged_cases": sum(
                    row["final_converged"] and row["final_update"] <= budget
                    for row in selected
                ),
                "positive_incumbent_cases": sum(
                    row["incumbent_sum_margin"] > 1e-12 for row in selected
                ),
                "unsafe_candidates_evaluated_through_budget": sum(
                    row["cumulative_unsafe_candidates"] for row in selected
                ),
                "aggregate_sum_margin": sum_score,
                "aggregate_hidden_br_reduction_diagnostic": hidden_score,
                "aggregate_sum_margin_capture": _safe_ratio(
                    sum_score,
                    sum_optimum,
                ),
                "aggregate_hidden_br_capture_diagnostic": _safe_ratio(
                    hidden_score,
                    hidden_optimum,
                ),
                "mean_decision_compute_milliseconds": milliseconds
                / len(selected),
                "mean_checkpoint_compute_milliseconds": milliseconds
                / len(selected),
                "maximum_decision_compute_milliseconds": max(
                    1_000.0 * row[timing_field]
                    for row in selected
                ),
                "maximum_checkpoint_compute_milliseconds": max(
                    1_000.0 * row[timing_field]
                    for row in selected
                ),
                "aggregate_sum_margin_per_decision_millisecond": _safe_ratio(
                    sum_score,
                    milliseconds,
                ),
                "aggregate_hidden_br_reduction_per_decision_millisecond": (
                    _safe_ratio(hidden_score, milliseconds)
                ),
                "mean_columns": mean(
                    (
                        row["columns_before_update"]
                        if checkpoint_phase == "candidate_ready"
                        else row["columns_after_update"]
                    )
                    for row in selected
                ),
                "mean_response_constraints": mean(
                    row["response_constraints_after_update"]
                    for row in selected
                ),
                "mean_setup_milliseconds": mean(
                    1_000.0 * row["setup_seconds"] for row in selected
                ),
                "mean_master_build_milliseconds": mean(
                    1_000.0 * row["cumulative_master_build_seconds"]
                    for row in selected
                ),
                "mean_master_solve_milliseconds": mean(
                    1_000.0 * row["cumulative_master_solve_seconds"]
                    for row in selected
                ),
                "mean_policy_conversion_milliseconds": mean(
                    1_000.0 * row["cumulative_policy_conversion_seconds"]
                    for row in selected
                ),
                "mean_separation_milliseconds": mean(
                    1_000.0 * row["cumulative_separation_seconds"]
                    for row in selected
                ),
                "mean_pricing_milliseconds": mean(
                    1_000.0 * row["cumulative_pricing_seconds"]
                    for row in selected
                ),
            }
        )
    return summaries


def _best_budget(summaries: list[dict[str, Any]]) -> dict[str, Any]:
    best = max(
        summaries,
        key=lambda row: (
            row["aggregate_sum_margin_per_decision_millisecond"] or 0.0,
            row["aggregate_sum_margin_capture"] or 0.0,
            -row["update_budget"],
        ),
    )
    return {
        "selection_target": "target-free certified sum margin per decision millisecond",
        **best,
    }


def _deadline_summary(
    records: list[dict[str, Any]],
    deadlines: tuple[float, ...],
) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        grouped.setdefault(record["boundary_id"], []).append(record)
    for rows in grouped.values():
        rows.sort(key=lambda row: row["update"])
    summaries: list[dict[str, Any]] = []
    for deadline in deadlines:
        selected: list[dict[str, Any] | None] = []
        for rows in grouped.values():
            ready = [
                row
                for row in rows
                if 1_000.0 * row["cumulative_candidate_compute_seconds"]
                <= deadline
            ]
            selected.append(ready[-1] if ready else None)
        sum_score = sum(
            0.0 if row is None else row["incumbent_sum_margin"]
            for row in selected
        )
        hidden_score = sum(
            0.0 if row is None else row["incumbent_hidden_br_reduction"]
            for row in selected
        )
        sum_optimum = sum(
            rows[0]["exact_sum_margin_optimum"] for rows in grouped.values()
        )
        hidden_optimum = sum(
            rows[0]["exact_hidden_br_optimum"] for rows in grouped.values()
        )
        used_milliseconds = [
            0.0
            if row is None
            else 1_000.0 * row["cumulative_candidate_compute_seconds"]
            for row in selected
        ]
        sorted_used = sorted(used_milliseconds)
        p95_index = max(0, (95 * len(sorted_used) + 99) // 100 - 1)
        total_available = deadline * len(selected)
        total_used = sum(used_milliseconds)
        summaries.append(
            {
                "scheduler": "oracle phase-fit upper bound",
                "deadline_milliseconds": deadline,
                "cases": len(selected),
                "candidate_ready_cases": sum(row is not None for row in selected),
                "positive_incumbent_cases": sum(
                    row is not None and row["incumbent_sum_margin"] > 1e-12
                    for row in selected
                ),
                "mean_selected_update": mean(
                    0 if row is None else row["update"] for row in selected
                ),
                "aggregate_sum_margin_capture": _safe_ratio(
                    sum_score,
                    sum_optimum,
                ),
                "aggregate_hidden_br_capture_diagnostic": _safe_ratio(
                    hidden_score,
                    hidden_optimum,
                ),
                "mean_compute_used_milliseconds": total_used / len(selected),
                "p95_compute_used_milliseconds": sorted_used[p95_index],
                "compute_utilization_fraction": _safe_ratio(
                    total_used,
                    total_available,
                ),
                "aggregate_sum_margin_per_used_millisecond": _safe_ratio(
                    sum_score,
                    total_used,
                ),
                "aggregate_sum_margin_per_available_millisecond": _safe_ratio(
                    sum_score,
                    total_available,
                ),
            }
        )
    return summaries


def run_constrained_generation_matrix(
    matrix_config: dict[str, Any],
) -> dict[str, Any]:
    base = dict(matrix_config.get("base", {}))
    axes = dict(matrix_config.get("axes", {}))
    max_runs = int(matrix_config.get("max_runs", 10_000))
    store_full_runs = bool(matrix_config.get("store_full_runs", False))
    store_records = bool(matrix_config.get("store_records", True))
    raw_deadlines = matrix_config.get(
        "deadline_milliseconds",
        [2.0, 3.0, 4.0, 5.0, 6.0, 8.0, 10.0, 15.0, 20.0],
    )
    unknown = (set(base) | set(axes)) - CONFIG_FIELDS
    if unknown:
        raise ValueError(
            f"unknown constrained-generation matrix fields: {sorted(unknown)!r}"
        )
    if not axes:
        raise ValueError("matrix axes cannot be empty")
    if not isinstance(raw_deadlines, list) or not raw_deadlines:
        raise ValueError("deadline_milliseconds must be a nonempty list")
    deadlines = tuple(float(value) for value in raw_deadlines)
    if (
        any(not isfinite(value) or value <= 0.0 for value in deadlines)
        or len(set(deadlines)) != len(deadlines)
    ):
        raise ValueError("deadlines must be finite, positive, and unique")
    if any(not isinstance(values, list) or not values for values in axes.values()):
        raise ValueError("every matrix axis must be a nonempty list")
    run_count = prod(len(values) for values in axes.values())
    if max_runs <= 0 or run_count > max_runs:
        raise ValueError(f"matrix contains {run_count} runs; max_runs is {max_runs}")

    started = time.perf_counter()
    environment = environment_metadata()
    axis_names = tuple(axes)
    blueprints: dict[tuple[str, str, int], PreparedBlueprint] = {}
    full_runs: list[dict[str, Any]] = []
    compact_runs: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []
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
        run = run_constrained_generation_experiment(
            config,
            prepared_blueprint=prepared,
            environment=environment,
        )
        run_records = _flatten_run(run, run_index)
        records.extend(run_records)
        compact_runs.append(
            {
                "config": run["config"],
                "blueprint_nash_conv": run["blueprint"]["nash_conv"],
                "boundaries": len(run["boundaries"]),
                "update_records": len(run_records),
                "wall_seconds": run["timing"]["wall_seconds"],
            }
        )
        if store_full_runs:
            full_runs.append(run)

    summaries = _anytime_summary(records)
    candidate_summaries = _anytime_summary(
        records,
        timing_field="cumulative_candidate_compute_seconds",
        checkpoint_phase="candidate_ready",
    )
    result = {
        "schema_version": 1,
        "experiment_type": "dynamic_constrained_generation_matrix",
        "matrix_config": {
            "base": base,
            "axes": axes,
            "max_runs": max_runs,
            "store_full_runs": store_full_runs,
            "store_records": store_records,
            "deadline_milliseconds": list(deadlines),
        },
        "environment": environment,
        "prepared_blueprints": len(blueprints),
        "run_count": run_count,
        "boundary_count": len({row["boundary_id"] for row in records}),
        "update_record_count": len(records),
        "wall_seconds": time.perf_counter() - started,
        "anytime_summary": summaries,
        "best_update_budget": _best_budget(summaries),
        "candidate_anytime_summary": candidate_summaries,
        "best_candidate_checkpoint": _best_budget(candidate_summaries),
        "candidate_checkpoint_protocol": {
            "status": "counterfactual phase-stop diagnostic",
            "selection": "stop immediately before current-round pricing",
            "caveat": (
                "when a run previously paid pricing to discover convergence, "
                "the candidate summary removes that price and is not the cost "
                "of executing the fixed maximum-update loop"
            ),
            "executable_fixed_update_summary": "anytime_summary",
        },
        "deadline_summary": _deadline_summary(records, deadlines),
        "deadline_protocol": {
            "status": "optimistic upper bound",
            "selection": "latest completed candidate phase within each deadline",
            "fallback": "immediate blueprint when no candidate phase fits",
            "future_work_charged": False,
            "realized_phase_time_used_for_selection": True,
        },
        "runs": compact_runs,
    }
    if store_records:
        result["records"] = records
    if store_full_runs:
        result["full_runs"] = full_runs
    return result


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    result = run_constrained_generation_matrix(config)
    rendered = json.dumps(result, indent=2, sort_keys=True, allow_nan=False)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(
        "constrained-generation matrix: "
        f"runs={result['run_count']}, boundaries={result['boundary_count']}, "
        f"best={result['best_update_budget']}, "
        f"wall={result['wall_seconds']:.3f}s"
    )
    if args.output is not None:
        print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
