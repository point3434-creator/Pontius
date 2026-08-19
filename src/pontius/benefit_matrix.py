"""Cartesian runner and diagnostics for resolver-benefit signals."""

from __future__ import annotations

import argparse
import json
import time
from itertools import product
from math import prod, sqrt
from pathlib import Path
from statistics import mean
from typing import Any

from .benefit_experiment import run_benefit_experiment
from .leaf_experiment import PreparedBlueprint, prepare_blueprint
from .reporting import environment_metadata

CONFIG_FIELDS = {
    "game",
    "blueprint_solver",
    "blueprint_iterations",
    "search_solver",
    "search_iterations",
    "probe_iterations",
    "depth_limit",
    "in_search_blueprint_weight",
    "output_candidate_weight",
    "warm_start_regret_mass",
}

SIGNAL_FIELDS = (
    "blueprint_positive_counterfactual_regret",
    "blueprint_local_nash_conv",
    "probe_counterfactual_regret_reduction",
    "probe_local_nash_conv_improvement",
    "probe_local_improvement_fraction_of_headroom",
    "probe_local_improvement_per_mean_policy_tv",
    "probe_policy_stability",
    "probe_mean_policy_tv",
    "full_counterfactual_regret_reduction",
    "full_local_nash_conv_improvement",
    "full_local_improvement_fraction_of_headroom",
    "full_local_improvement_per_mean_policy_tv",
    "full_policy_stability",
    "full_mean_policy_tv",
)


def _safe_rate(numerator: float, denominator: float) -> float | None:
    return numerator / denominator if denominator > 0.0 else None


def _compact_run(result: dict[str, Any]) -> dict[str, Any]:
    probe_seconds = result["timing"]["probe_search_seconds"]
    full_seconds = result["timing"]["full_search_seconds"]
    probe_benefit = result["targets"]["probe_full_game_nash_conv_improvement"]
    full_benefit = result["targets"]["full_game_nash_conv_improvement"]
    return {
        "config": result["config"],
        "signals": result["signals"],
        "targets": result["targets"],
        "metrics": {
            "probe_search_seconds": probe_seconds,
            "full_search_seconds": full_seconds,
            "probe_full_game_improvement_per_search_millisecond": _safe_rate(
                probe_benefit,
                probe_seconds * 1_000.0,
            ),
            "full_game_improvement_per_search_millisecond": _safe_rate(
                full_benefit,
                full_seconds * 1_000.0,
            ),
            "probe_to_full_search_time_ratio": _safe_rate(
                probe_seconds,
                full_seconds,
            ),
            "blueprint_signal_seconds": result["timing"][
                "blueprint_signal_seconds"
            ],
            "candidate_model_evaluation_seconds": result["timing"][
                "candidate_model_evaluation_seconds"
            ],
        },
    }


def _pearson(left: list[float], right: list[float]) -> float | None:
    if len(left) != len(right) or not left:
        raise ValueError("correlation inputs must have equal nonzero length")
    left_mean = mean(left)
    right_mean = mean(right)
    numerator = sum(
        (left_value - left_mean) * (right_value - right_mean)
        for left_value, right_value in zip(left, right, strict=True)
    )
    left_sse = sum((value - left_mean) ** 2 for value in left)
    right_sse = sum((value - right_mean) ** 2 for value in right)
    denominator = sqrt(left_sse * right_sse)
    return numerator / denominator if denominator > 0.0 else None


def _ranks(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=values.__getitem__)
    result = [0.0] * len(values)
    index = 0
    while index < len(order):
        end = index + 1
        while end < len(order) and values[order[end]] == values[order[index]]:
            end += 1
        rank = 0.5 * (index + end - 1)
        for position in range(index, end):
            result[order[position]] = rank
        index = end
    return result


def _roc_auc(signal: list[float], labels: list[bool]) -> float | None:
    positives = [value for value, label in zip(signal, labels, strict=True) if label]
    negatives = [
        value for value, label in zip(signal, labels, strict=True) if not label
    ]
    if not positives or not negatives:
        return None
    wins = sum(
        float(positive > negative) + 0.5 * float(positive == negative)
        for positive in positives
        for negative in negatives
    )
    return wins / (len(positives) * len(negatives))


def _signal_diagnostics(runs: list[dict[str, Any]]) -> dict[str, Any]:
    target = [
        float(run["targets"]["full_game_nash_conv_improvement"]) for run in runs
    ]
    labels = [value > 0.0 for value in target]
    result: dict[str, Any] = {}
    for field in SIGNAL_FIELDS:
        values = [float(run["signals"][field]) for run in runs]
        predictions = [value > 0.0 for value in values]
        result[field] = {
            "pearson_with_full_game_improvement": _pearson(values, target),
            "spearman_with_full_game_improvement": _pearson(
                _ranks(values),
                _ranks(target),
            ),
            "roc_auc_for_positive_full_game_improvement": _roc_auc(
                values,
                labels,
            ),
            "sign_confusion": {
                "true_positive": sum(
                    predicted and label
                    for predicted, label in zip(predictions, labels, strict=True)
                ),
                "true_negative": sum(
                    not predicted and not label
                    for predicted, label in zip(predictions, labels, strict=True)
                ),
                "false_positive": sum(
                    predicted and not label
                    for predicted, label in zip(predictions, labels, strict=True)
                ),
                "false_negative": sum(
                    not predicted and label
                    for predicted, label in zip(predictions, labels, strict=True)
                ),
            },
        }
    return {
        "cases": len(runs),
        "positive_full_game_improvement": sum(labels),
        "nonpositive_full_game_improvement": len(labels) - sum(labels),
        "signals": result,
    }


def run_benefit_matrix(matrix_config: dict[str, Any]) -> dict[str, Any]:
    base = dict(matrix_config.get("base", {}))
    axes = dict(matrix_config.get("axes", {}))
    max_runs = int(matrix_config.get("max_runs", 10_000))
    store_full_runs = bool(matrix_config.get("store_full_runs", False))
    unknown = (set(base) | set(axes)) - CONFIG_FIELDS
    if unknown:
        raise ValueError(f"unknown benefit experiment fields: {sorted(unknown)!r}")
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
        result = run_benefit_experiment(
            config,
            prepared_blueprint=prepared,
            environment=environment,
        )
        compact_runs.append(_compact_run(result))
        if store_full_runs:
            full_runs.append(result)

    output = {
        "schema_version": 1,
        "experiment_type": "resolver_benefit_signal_matrix",
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
        "signal_diagnostics": _signal_diagnostics(compact_runs),
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
    result = run_benefit_matrix(config)
    rendered = json.dumps(result, indent=2, sort_keys=True, allow_nan=False)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    diagnostics = result["signal_diagnostics"]
    print(
        f"benefit matrix: runs={result['run_count']}, "
        f"positive={diagnostics['positive_full_game_improvement']}, "
        f"wall={result['wall_seconds']:.3f}s"
    )
    if args.output is not None:
        print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
