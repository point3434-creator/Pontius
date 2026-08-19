"""Cartesian, replicated runner for paired leaf-error experiments."""

from __future__ import annotations

import argparse
import json
import time
from itertools import product
from math import prod
from pathlib import Path
from statistics import mean, stdev
from typing import Any

from .leaf_experiment import PreparedBlueprint, prepare_blueprint, run_leaf_experiment
from .reporting import environment_metadata

CONFIG_FIELDS = {
    "game",
    "blueprint_solver",
    "blueprint_iterations",
    "search_solver",
    "search_iterations",
    "depth_limit",
    "leaf_error_scale",
    "leaf_error_target_on_policy_root_l2",
    "leaf_error_seed",
    "zero_sum_errors",
    "warm_start_regret_mass",
    "in_search_blueprint_weight",
    "output_candidate_weight",
    "leaf_error_grouping",
    "leaf_error_scope",
    "leaf_error_scope_actions",
    "leaf_error_bias",
}


def _compact_run(result: dict[str, Any]) -> dict[str, Any]:
    average_effect = result["causal_effect"]["average"]
    current_effect = result["causal_effect"]["current"]
    return {
        "config": result["config"],
        "metrics": {
            "leaf_rmse": result["leaf_error"]["rmse"],
            "leaf_effective_scale": result["structured_error_protocol"][
                "effective_leaf_error_scale"
            ],
            "leaf_mean_absolute_error": result["leaf_error"][
                "mean_absolute_error"
            ],
            "leaf_on_policy_reach_mass": result["leaf_error_reach_weighted"][
                "on_policy_reach_mass"
            ],
            "leaf_on_policy_rmse": result["leaf_error_reach_weighted"][
                "on_policy_rmse"
            ],
            "leaf_on_policy_root_l2": result["leaf_error_reach_weighted"][
                "on_policy_root_l2"
            ],
            "leaf_aggregate_counterfactual_rmse": result[
                "leaf_error_reach_weighted"
            ]["aggregate_counterfactual_rmse"],
            "leaf_max_counterfactual_root_l2": max(
                result["leaf_error_reach_weighted"]["counterfactual_root_l2"]
            ),
            "leaf_active_on_policy_reach_mass": result[
                "structured_error_protocol"
            ]["active_on_policy_reach_mass"],
            "leaf_active_on_policy_reach_fraction": result[
                "structured_error_protocol"
            ]["active_on_policy_reach_fraction"],
            "leaf_active_error_groups": result["structured_error_protocol"][
                "active_error_groups"
            ],
            "blueprint_nash_conv": result["blueprint"]["nash_conv"],
            "exact_average_nash_conv_delta_from_blueprint": result[
                "exact_control"
            ]["average"]["nash_conv_delta_from_blueprint"],
            "perturbed_average_nash_conv_delta_from_blueprint": result[
                "perturbed"
            ]["average"]["nash_conv_delta_from_blueprint"],
            "exact_current_nash_conv_delta_from_blueprint": result[
                "exact_control"
            ]["current"]["nash_conv_delta_from_blueprint"],
            "perturbed_current_nash_conv_delta_from_blueprint": result[
                "perturbed"
            ]["current"]["nash_conv_delta_from_blueprint"],
            "exact_average_mean_policy_tv_from_blueprint": result[
                "exact_control"
            ]["average"]["resolved_policy_distance_from_blueprint"][
                "mean_information_set_total_variation"
            ],
            "perturbed_average_mean_policy_tv_from_blueprint": result[
                "perturbed"
            ]["average"]["resolved_policy_distance_from_blueprint"][
                "mean_information_set_total_variation"
            ],
            "exact_current_mean_policy_tv_from_blueprint": result[
                "exact_control"
            ]["current"]["resolved_policy_distance_from_blueprint"][
                "mean_information_set_total_variation"
            ],
            "perturbed_current_mean_policy_tv_from_blueprint": result[
                "perturbed"
            ]["current"]["resolved_policy_distance_from_blueprint"][
                "mean_information_set_total_variation"
            ],
            "exact_average_oracle_candidate_selected": result[
                "oracle_no_op_selection"
            ]["exact_control_average"]["candidate_selected"],
            "perturbed_average_oracle_candidate_selected": result[
                "oracle_no_op_selection"
            ]["perturbed_average"]["candidate_selected"],
            "exact_current_oracle_candidate_selected": result[
                "oracle_no_op_selection"
            ]["exact_control_current"]["candidate_selected"],
            "perturbed_current_oracle_candidate_selected": result[
                "oracle_no_op_selection"
            ]["perturbed_current"]["candidate_selected"],
            "average_nash_conv_delta": average_effect["nash_conv_delta"],
            "average_absolute_nash_conv_delta": average_effect[
                "absolute_nash_conv_delta"
            ],
            "average_mean_policy_tv": average_effect[
                "mean_information_set_total_variation"
            ],
            "current_nash_conv_delta": current_effect["nash_conv_delta"],
            "current_absolute_nash_conv_delta": current_effect[
                "absolute_nash_conv_delta"
            ],
            "current_mean_policy_tv": current_effect[
                "mean_information_set_total_variation"
            ],
            "exact_control_search_seconds": result["timing"][
                "exact_control_search_seconds"
            ],
            "perturbed_search_seconds": result["timing"][
                "perturbed_search_seconds"
            ],
        },
    }


def _summary_statistics(
    values: list[float | int | bool | None],
) -> dict[str, float | int | None]:
    defined = [float(value) for value in values if value is not None]
    if not defined:
        return {
            "count": len(values),
            "defined_count": 0,
            "mean": None,
            "sample_stddev": None,
            "min": None,
            "max": None,
        }
    return {
        "count": len(values),
        "defined_count": len(defined),
        "mean": mean(defined),
        "sample_stddev": stdev(defined) if len(defined) > 1 else 0.0,
        "min": min(defined),
        "max": max(defined),
    }


def _summarize(
    runs: list[dict[str, Any]],
    replicate_axes: set[str],
) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    group_configs: dict[str, dict[str, Any]] = {}
    for run in runs:
        group_config = {
            key: value
            for key, value in run["config"].items()
            if key not in replicate_axes
        }
        group_key = json.dumps(group_config, sort_keys=True)
        grouped.setdefault(group_key, []).append(run)
        group_configs[group_key] = group_config

    summaries: list[dict[str, Any]] = []
    for group_key in sorted(grouped):
        members = grouped[group_key]
        metric_names = tuple(members[0]["metrics"])
        summaries.append(
            {
                "config": group_configs[group_key],
                "replicates": len(members),
                "metrics": {
                    metric: _summary_statistics(
                        [member["metrics"][metric] for member in members]
                    )
                    for metric in metric_names
                },
            }
        )
    return summaries


def run_leaf_matrix(matrix_config: dict[str, Any]) -> dict[str, Any]:
    base = dict(matrix_config.get("base", {}))
    axes = dict(matrix_config.get("axes", {}))
    replicate_axes = set(matrix_config.get("replicate_axes", ["leaf_error_seed"]))
    store_full_runs = bool(matrix_config.get("store_full_runs", False))
    max_runs = int(matrix_config.get("max_runs", 10_000))

    unknown_base = set(base) - CONFIG_FIELDS
    unknown_axes = set(axes) - CONFIG_FIELDS
    if unknown_base or unknown_axes:
        raise ValueError(
            f"unknown leaf experiment fields: {sorted(unknown_base | unknown_axes)!r}"
        )
    if not axes:
        raise ValueError("matrix axes cannot be empty")
    if any(not isinstance(values, list) or not values for values in axes.values()):
        raise ValueError("every matrix axis must be a nonempty list")
    if not replicate_axes <= set(axes):
        raise ValueError("replicate_axes must name configured matrix axes")

    run_count = prod(len(values) for values in axes.values())
    if max_runs <= 0 or run_count > max_runs:
        raise ValueError(f"matrix contains {run_count} runs; max_runs is {max_runs}")

    started = time.perf_counter()
    shared_environment = environment_metadata()
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
        result = run_leaf_experiment(
            config,
            prepared_blueprint=prepared,
            environment=shared_environment,
        )
        compact_runs.append(_compact_run(result))
        if store_full_runs:
            full_runs.append(result)

    summaries = _summarize(compact_runs, replicate_axes)
    wall_seconds = time.perf_counter() - started
    output = {
        "schema_version": 3,
        "experiment_type": "paired_leaf_error_matrix",
        "matrix_config": {
            "base": base,
            "axes": axes,
            "replicate_axes": sorted(replicate_axes),
            "store_full_runs": store_full_runs,
            "max_runs": max_runs,
        },
        "environment": shared_environment,
        "prepared_blueprints": len(blueprints),
        "run_count": run_count,
        "wall_seconds": wall_seconds,
        "runs": compact_runs,
        "summaries": summaries,
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
    result = run_leaf_matrix(config)
    rendered = json.dumps(result, indent=2, sort_keys=True)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(
        f"paired leaf matrix: runs={result['run_count']}, "
        f"groups={len(result['summaries'])}, wall={result['wall_seconds']:.3f}s"
    )
    if args.output is not None:
        print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
