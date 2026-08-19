"""Analyze progressive probe trajectories without fitting a selector."""

from __future__ import annotations

import argparse
import json
from math import sqrt
from pathlib import Path
from statistics import mean
from typing import Any, Callable

from .benefit_matrix import _pearson, _ranks, _roc_auc

DEFAULT_CHECKPOINTS = (1, 3, 5, 10, 25)


def _linear_intercept(
    points: tuple[tuple[int, float], ...],
    transform: Callable[[int], float],
) -> float:
    transformed = tuple((transform(iteration), value) for iteration, value in points)
    x_mean = mean(x for x, _ in transformed)
    y_mean = mean(y for _, y in transformed)
    denominator = sum((x - x_mean) ** 2 for x, _ in transformed)
    if denominator <= 0.0:
        raise ValueError("trajectory fit requires distinct transformed checkpoints")
    slope = sum(
        (x - x_mean) * (y - y_mean) for x, y in transformed
    ) / denominator
    return y_mean - slope * x_mean


def _gain_per_movement(gain: float, movement: float) -> float:
    if movement > 0.0:
        return gain / movement
    if abs(gain) <= 1e-15:
        return 0.0
    raise ValueError("nonzero probe gain has zero policy movement")


def _feature_diagnostics(
    trajectories: list[dict[str, Any]],
) -> dict[str, Any]:
    targets = [float(item["target_full_game_improvement"]) for item in trajectories]
    labels = [target > 0.0 for target in targets]
    feature_names = tuple(trajectories[0]["features"]) if trajectories else ()
    diagnostics: dict[str, Any] = {}
    for feature_name in feature_names:
        values = [float(item["features"][feature_name]) for item in trajectories]
        diagnostics[feature_name] = {
            "pearson_with_full_game_improvement": _pearson(values, targets),
            "spearman_with_full_game_improvement": _pearson(
                _ranks(values),
                _ranks(targets),
            ),
            "roc_auc_for_positive_full_game_improvement": _roc_auc(
                values,
                labels,
            ),
        }
    return {
        "cases": len(trajectories),
        "positive_full_game_improvement": sum(labels),
        "nonpositive_full_game_improvement": len(labels) - sum(labels),
        "higher_feature_values_are_ranked_as_more_promising": True,
        "features": diagnostics,
    }


def _group_matrix_runs(
    matrix: dict[str, Any],
    checkpoints: tuple[int, ...],
) -> list[dict[int, dict[str, Any]]]:
    expected = set(checkpoints)
    groups: dict[tuple[tuple[str, Any], ...], dict[int, dict[str, Any]]] = {}
    for run in matrix.get("runs", ()):
        config = dict(run["config"])
        try:
            checkpoint = int(config.pop("probe_iterations"))
        except KeyError as error:
            raise ValueError("matrix run lacks probe_iterations") from error
        key = tuple(sorted(config.items()))
        if checkpoint in groups.setdefault(key, {}):
            raise ValueError("duplicate probe checkpoint for one configuration")
        groups[key][checkpoint] = run
    if not groups:
        raise ValueError("trajectory matrix has no runs")
    for runs in groups.values():
        missing = expected - set(runs)
        if missing:
            raise ValueError(f"trajectory is missing checkpoints {sorted(missing)!r}")
    return [
        {checkpoint: runs[checkpoint] for checkpoint in checkpoints}
        for runs in groups.values()
    ]


def _consistent_value(
    runs: dict[int, dict[str, Any]],
    checkpoints: tuple[int, ...],
    section: str,
    field: str,
) -> float:
    values = [float(runs[checkpoint][section][field]) for checkpoint in checkpoints]
    reference = values[0]
    if any(abs(value - reference) > 1e-12 for value in values[1:]):
        raise ValueError(f"{section}.{field} changed across probe checkpoints")
    return reference


def _trajectory_features(
    runs: dict[int, dict[str, Any]],
    checkpoints: tuple[int, ...],
) -> dict[str, float]:
    gain = {
        checkpoint: float(
            runs[checkpoint]["signals"]["probe_local_nash_conv_improvement"]
        )
        for checkpoint in checkpoints
    }
    movement = {
        checkpoint: float(runs[checkpoint]["signals"]["probe_mean_policy_tv"])
        for checkpoint in checkpoints
    }
    features: dict[str, float] = {}
    for checkpoint in checkpoints:
        if movement[checkpoint] < 0.0:
            raise ValueError("probe policy movement cannot be negative")
        features[f"probe_model_gain_at_{checkpoint}"] = gain[checkpoint]
        features[f"probe_model_gain_per_tv_at_{checkpoint}"] = _gain_per_movement(
            gain[checkpoint],
            movement[checkpoint],
        )
        features[f"probe_policy_stability_at_{checkpoint}"] = -movement[checkpoint]

    for start, end in zip(checkpoints, checkpoints[1:]):
        width = end - start
        features[f"probe_model_gain_slope_{start}_to_{end}"] = (
            gain[end] - gain[start]
        ) / width
        features[f"probe_policy_stability_slope_{start}_to_{end}"] = -(
            movement[end] - movement[start]
        ) / width

    required = {3, 5, 10, 25}
    if required.issubset(gain):
        features["inverse_iteration_asymptotic_gain_at_10"] = _linear_intercept(
            tuple((checkpoint, gain[checkpoint]) for checkpoint in (3, 5, 10)),
            lambda iteration: 1.0 / iteration,
        )
        features["inverse_sqrt_iteration_asymptotic_gain_at_10"] = (
            _linear_intercept(
                tuple(
                    (checkpoint, gain[checkpoint]) for checkpoint in (3, 5, 10)
                ),
                lambda iteration: 1.0 / sqrt(iteration),
            )
        )
        features["inverse_iteration_asymptotic_gain_at_25"] = _linear_intercept(
            tuple((checkpoint, gain[checkpoint]) for checkpoint in (5, 10, 25)),
            lambda iteration: 1.0 / iteration,
        )
        features["inverse_sqrt_iteration_asymptotic_gain_at_25"] = (
            _linear_intercept(
                tuple(
                    (checkpoint, gain[checkpoint]) for checkpoint in (5, 10, 25)
                ),
                lambda iteration: 1.0 / sqrt(iteration),
            )
        )

    features["postsearch_model_gain"] = _consistent_value(
        runs,
        checkpoints,
        "signals",
        "full_local_nash_conv_improvement",
    )
    features["postsearch_model_gain_per_tv"] = _consistent_value(
        runs,
        checkpoints,
        "signals",
        "full_local_improvement_per_mean_policy_tv",
    )
    features["postsearch_policy_stability"] = _consistent_value(
        runs,
        checkpoints,
        "signals",
        "full_policy_stability",
    )
    return features


def _source_summary(
    matrix: dict[str, Any],
    checkpoints: tuple[int, ...],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    grouped = _group_matrix_runs(matrix, checkpoints)
    trajectories: list[dict[str, Any]] = []
    for runs in grouped:
        first = runs[checkpoints[0]]
        config = dict(first["config"])
        config.pop("probe_iterations")
        trajectories.append(
            {
                "config": config,
                "target_full_game_improvement": _consistent_value(
                    runs,
                    checkpoints,
                    "targets",
                    "full_game_nash_conv_improvement",
                ),
                "features": _trajectory_features(runs, checkpoints),
            }
        )

    timing = {}
    for checkpoint in checkpoints:
        runs_at_checkpoint = [runs[checkpoint] for runs in grouped]
        timing[str(checkpoint)] = {
            "mean_probe_search_milliseconds": 1_000.0
            * mean(
                float(run["metrics"]["probe_search_seconds"])
                for run in runs_at_checkpoint
            ),
            "mean_probe_to_full_search_time_ratio": mean(
                float(run["metrics"]["probe_to_full_search_time_ratio"])
                for run in runs_at_checkpoint
            ),
        }
    return trajectories, timing


def analyze_probe_trajectories(
    matrices: dict[str, dict[str, Any]],
    *,
    checkpoints: tuple[int, ...] = DEFAULT_CHECKPOINTS,
) -> dict[str, Any]:
    """Compare deterministic probe-prefix features with exact hidden outcomes."""

    if not matrices:
        raise ValueError("at least one named matrix is required")
    if len(checkpoints) < 2 or any(checkpoint <= 0 for checkpoint in checkpoints):
        raise ValueError("checkpoints must contain at least two positive iterations")
    if tuple(sorted(set(checkpoints))) != checkpoints:
        raise ValueError("checkpoints must be strictly increasing and unique")

    sources: dict[str, Any] = {}
    combined: list[dict[str, Any]] = []
    for name, matrix in matrices.items():
        trajectories, timing = _source_summary(matrix, checkpoints)
        sources[name] = {
            "ranking_diagnostics": _feature_diagnostics(trajectories),
            "timing": timing,
            "trajectories": trajectories,
        }
        combined.extend(trajectories)

    return {
        "schema_version": 1,
        "experiment_type": "resolver_benefit_probe_trajectories",
        "protocol": {
            "checkpoints": list(checkpoints),
            "probe_features_use_depth_limited_model_only": True,
            "target_uses_untouched_full_game_exact_evaluation": True,
            "analysis_fits_no_selector_or_threshold": True,
            "postsearch_features_are_diagnostics_not_compute_saving_signals": True,
        },
        "sources": sources,
        "combined_ranking_diagnostics": _feature_diagnostics(combined),
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--matrix",
        action="append",
        nargs=2,
        metavar=("NAME", "PATH"),
        required=True,
    )
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    matrices = {
        name: json.loads(Path(path).read_text(encoding="utf-8"))
        for name, path in args.matrix
    }
    if len(matrices) != len(args.matrix):
        raise ValueError("matrix names must be unique")
    result = analyze_probe_trajectories(matrices)
    rendered = json.dumps(result, indent=2, sort_keys=True, allow_nan=False)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    combined = result["combined_ranking_diagnostics"]
    print(
        f"probe trajectories: cases={combined['cases']}, "
        f"positive={combined['positive_full_game_improvement']}"
    )
    if args.output is not None:
        print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
