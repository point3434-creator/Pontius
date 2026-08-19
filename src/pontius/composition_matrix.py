"""Cartesian comparison of resolver policy-composition architectures."""

from __future__ import annotations

import argparse
import json
import time
from itertools import product
from math import prod
from pathlib import Path
from statistics import mean, median
from typing import Any

from .benefit_matrix import _pearson, _ranks, _roc_auc
from .composition_experiment import run_composition_experiment
from .leaf_experiment import PreparedBlueprint, prepare_blueprint
from .reporting import environment_metadata

CONFIG_FIELDS = {
    "game",
    "blueprint_solver",
    "blueprint_iterations",
    "search_solver",
    "search_iterations",
    "depth_limit",
    "in_search_blueprint_weight",
    "output_candidate_weight",
    "warm_start_regret_mass",
}
ARCHITECTURES = (
    "prefix",
    "continual",
    "local_gated_continual",
    "global_control",
)


def _compact_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "nash_conv": candidate["nash_conv"],
        "nash_conv_improvement_over_blueprint": candidate[
            "nash_conv_improvement_over_blueprint"
        ],
        "nash_conv_improvement_per_decision_compute_millisecond": candidate[
            "nash_conv_improvement_per_decision_compute_millisecond"
        ],
        "decision_compute_seconds": candidate["decision_compute_seconds"],
        "mean_policy_tv": candidate["policy_distance_from_blueprint"][
            "mean_information_set_total_variation"
        ],
        "max_policy_tv": candidate["policy_distance_from_blueprint"][
            "max_information_set_total_variation"
        ],
    }


def _compact_run(result: dict[str, Any]) -> dict[str, Any]:
    compact = {
        "config": result["config"],
        "blueprint_nash_conv": result["blueprint"]["nash_conv"],
        "prefix": {
            "model_nash_conv_improvement": result["prefix"][
                "model_nash_conv_improvement"
            ],
            "candidate": _compact_candidate(result["prefix"]["candidate"]),
        },
        "global_control": {
            "candidate": _compact_candidate(result["global_control"]["candidate"]),
        },
        "wall_seconds": result["timing"]["wall_seconds"],
    }
    for architecture in ("continual", "local_gated_continual"):
        continual = result[architecture]
        compact[architecture] = {
            "reach_weighted_root_candidate_model_gain": continual[
                "reach_weighted_root_candidate_model_gain"
            ],
            "reach_weighted_full_local_model_gain": continual[
                "reach_weighted_full_local_model_gain"
            ],
            "searched_public_histories": continual["searched_public_histories"],
            "deployed_public_histories": continual[
                "deployed_public_histories"
            ],
            "skipped_zero_reach_histories": len(
                continual["skipped_zero_reach_histories"]
            ),
            "expected_public_decisions_per_hand": continual[
                "expected_public_decisions_per_hand"
            ],
            "expected_search_seconds_per_hand": continual[
                "expected_search_seconds_per_hand"
            ],
            "expected_gate_evaluation_seconds_per_hand": continual[
                "expected_gate_evaluation_seconds_per_hand"
            ],
            "expected_search_seconds_per_public_decision": continual[
                "expected_search_seconds_per_public_decision"
            ],
            "total_search_seconds_to_materialize_profile": continual[
                "total_search_seconds_to_materialize_profile"
            ],
            "candidate": _compact_candidate(continual["candidate"]),
        }
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
    rates = [
        candidate["nash_conv_improvement_per_decision_compute_millisecond"]
        for candidate in candidates
        if candidate[
            "nash_conv_improvement_per_decision_compute_millisecond"
        ]
        is not None
    ]
    return {
        "cases": len(candidates),
        "positive_improvement": sum(value > 0.0 for value in improvements),
        "nonpositive_improvement": sum(value <= 0.0 for value in improvements),
        "mean_nash_conv_improvement": mean(improvements),
        "median_nash_conv_improvement": median(improvements),
        "worst_nash_conv_improvement": min(improvements),
        "best_nash_conv_improvement": max(improvements),
        "mean_decision_compute_milliseconds": 1_000.0
        * mean(
            float(candidate["decision_compute_seconds"])
            for candidate in candidates
        ),
        "mean_nash_conv_improvement_per_decision_compute_millisecond": mean(
            rates
        ),
    }


def _paired_summary(runs: list[dict[str, Any]]) -> dict[str, Any]:
    prefix = [
        float(run["prefix"]["candidate"]["nash_conv_improvement_over_blueprint"])
        for run in runs
    ]
    continual = [
        float(
            run["continual"]["candidate"]["nash_conv_improvement_over_blueprint"]
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
    local_gated = [
        float(
            run["local_gated_continual"]["candidate"][
                "nash_conv_improvement_over_blueprint"
            ]
        )
        for run in runs
    ]
    return {
        "continual_minus_prefix_mean_improvement": mean(
            continual_value - prefix_value
            for continual_value, prefix_value in zip(continual, prefix, strict=True)
        ),
        "continual_beats_prefix": sum(
            continual_value > prefix_value
            for continual_value, prefix_value in zip(continual, prefix, strict=True)
        ),
        "global_minus_continual_mean_improvement": mean(
            global_value - continual_value
            for global_value, continual_value in zip(
                global_control,
                continual,
                strict=True,
            )
        ),
        "global_beats_continual": sum(
            global_value > continual_value
            for global_value, continual_value in zip(
                global_control,
                continual,
                strict=True,
            )
        ),
        "local_gate_minus_continual_mean_improvement": mean(
            gated_value - continual_value
            for gated_value, continual_value in zip(
                local_gated,
                continual,
                strict=True,
            )
        ),
        "local_gate_beats_continual": sum(
            gated_value > continual_value
            for gated_value, continual_value in zip(
                local_gated,
                continual,
                strict=True,
            )
        ),
        "global_beats_local_gate": sum(
            global_value > gated_value
            for global_value, gated_value in zip(
                global_control,
                local_gated,
                strict=True,
            )
        ),
    }


def _signal_diagnostic(
    signal: list[float],
    target: list[float],
) -> dict[str, Any]:
    labels = [value > 0.0 for value in target]
    return {
        "pearson_with_full_game_improvement": _pearson(signal, target),
        "spearman_with_full_game_improvement": _pearson(
            _ranks(signal),
            _ranks(target),
        ),
        "roc_auc_for_positive_full_game_improvement": _roc_auc(signal, labels),
        "positive_signal_false_positives": sum(
            signal_value > 0.0 and target_value <= 0.0
            for signal_value, target_value in zip(signal, target, strict=True)
        ),
        "positive_signal_true_positives": sum(
            signal_value > 0.0 and target_value > 0.0
            for signal_value, target_value in zip(signal, target, strict=True)
        ),
    }


def _composition_signal_diagnostics(
    runs: list[dict[str, Any]],
) -> dict[str, Any]:
    prefix_target = [
        float(run["prefix"]["candidate"]["nash_conv_improvement_over_blueprint"])
        for run in runs
    ]
    continual_target = [
        float(
            run["continual"]["candidate"]["nash_conv_improvement_over_blueprint"]
        )
        for run in runs
    ]
    return {
        "prefix_model_gain": _signal_diagnostic(
            [float(run["prefix"]["model_nash_conv_improvement"]) for run in runs],
            prefix_target,
        ),
        "continual_reach_weighted_root_candidate_model_gain": _signal_diagnostic(
            [
                float(
                    run["continual"][
                        "reach_weighted_root_candidate_model_gain"
                    ]
                )
                for run in runs
            ],
            continual_target,
        ),
        "local_gated_reach_weighted_root_candidate_model_gain": (
            _signal_diagnostic(
                [
                    float(
                        run["local_gated_continual"][
                            "reach_weighted_root_candidate_model_gain"
                        ]
                    )
                    for run in runs
                ],
                [
                    float(
                        run["local_gated_continual"]["candidate"][
                            "nash_conv_improvement_over_blueprint"
                        ]
                    )
                    for run in runs
                ],
            )
        ),
        "continual_reach_weighted_full_local_model_gain": _signal_diagnostic(
            [
                float(
                    run["continual"]["reach_weighted_full_local_model_gain"]
                )
                for run in runs
            ],
            continual_target,
        ),
    }


def run_composition_matrix(matrix_config: dict[str, Any]) -> dict[str, Any]:
    base = dict(matrix_config.get("base", {}))
    axes = dict(matrix_config.get("axes", {}))
    max_runs = int(matrix_config.get("max_runs", 10_000))
    store_full_runs = bool(matrix_config.get("store_full_runs", False))
    unknown = (set(base) | set(axes)) - CONFIG_FIELDS
    if unknown:
        raise ValueError(f"unknown composition fields: {sorted(unknown)!r}")
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
        result = run_composition_experiment(
            config,
            prepared_blueprint=prepared,
            environment=environment,
        )
        compact_runs.append(_compact_run(result))
        if store_full_runs:
            full_runs.append(result)

    output = {
        "schema_version": 1,
        "experiment_type": "resolver_policy_composition_matrix",
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
        "signal_diagnostics": _composition_signal_diagnostics(compact_runs),
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
    result = run_composition_matrix(config)
    rendered = json.dumps(result, indent=2, sort_keys=True, allow_nan=False)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    summary = result["architecture_summary"]
    print(
        f"composition matrix: runs={result['run_count']}, "
        f"prefix+={summary['prefix']['positive_improvement']}, "
        f"continual+={summary['continual']['positive_improvement']}, "
        f"local-gated+={summary['local_gated_continual']['positive_improvement']}, "
        f"global+={summary['global_control']['positive_improvement']}, "
        f"wall={result['wall_seconds']:.3f}s"
    )
    if args.output is not None:
        print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
