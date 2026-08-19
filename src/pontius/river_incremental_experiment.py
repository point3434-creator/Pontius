"""Finite-policy benchmark for exact delta-aware river recertification."""

from __future__ import annotations

import argparse
import json
import math
import time
from dataclasses import asdict
from pathlib import Path
from statistics import mean, median
from typing import Any, Callable, TypeVar

from .cfr import TabularCFR
from .evaluation import EvaluationResult, Policy, evaluate_profile
from .reporting import environment_metadata
from .river import RiverHoldem
from .river_cache import transferred_exploitability_certificate
from .river_context import CONTEXT_FAMILIES, generate_river_contexts
from .river_incremental import (
    RiverPolicyEvaluationCache,
    RiverRangeDelta,
    make_support_swap_perturbation,
)
from .river_range_reuse import make_blocker_perturbation
from .updates import UPDATE_RULES

T = TypeVar("T")


def _timed(
    operation: Callable[[], T],
    *,
    batches: int,
    inner_repetitions: int,
) -> tuple[T, dict[str, object]]:
    samples = []
    result: T | None = None
    for _ in range(batches):
        start = time.perf_counter_ns()
        for _ in range(inner_repetitions):
            result = operation()
        elapsed = time.perf_counter_ns() - start
        samples.append(elapsed / inner_repetitions / 1_000_000.0)
    assert result is not None
    return result, {
        "batches": batches,
        "inner_repetitions": inner_repetitions,
        "median_milliseconds": median(samples),
        "minimum_milliseconds": min(samples),
        "maximum_milliseconds": max(samples),
        "batch_milliseconds_per_call": samples,
    }


def _evaluation_error(first: EvaluationResult, second: EvaluationResult) -> float:
    first_values = (
        *first.utilities,
        *first.best_response_values,
        *first.deviation_gains,
        first.nash_conv,
        first.exploitability or 0.0,
    )
    second_values = (
        *second.utilities,
        *second.best_response_values,
        *second.deviation_gains,
        second.nash_conv,
        second.exploitability or 0.0,
    )
    return max(
        abs(left - right)
        for left, right in zip(first_values, second_values, strict=True)
    )


def _percentile(values: list[float], quantile: float) -> float:
    if not values:
        raise ValueError("percentile requires at least one value")
    ordered = sorted(values)
    position = quantile * (len(ordered) - 1)
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def _make_target(
    source: RiverHoldem,
    perturbation: dict[str, object],
) -> tuple[RiverHoldem, dict[str, object]]:
    kind = str(perturbation["kind"])
    player = int(perturbation["player"])
    if kind == "blocker_reweight":
        return make_blocker_perturbation(
            source,
            player=player,
            root_tv_budget=float(perturbation["root_tv_budget"]),
            maximum_donor_fraction=float(perturbation["maximum_donor_fraction"]),
        )
    if kind == "support_swap":
        return make_support_swap_perturbation(source, player=player)
    raise AssertionError(f"unvalidated perturbation kind {kind!r}")


def _validate_config(config: dict[str, Any]) -> dict[str, Any]:
    allowed = {
        "groups",
        "seed",
        "hands_per_player",
        "families",
        "included_splits",
        "sequential_raise",
        "perturbations",
        "solver",
        "source_policy_checkpoints",
        "normalized_exploitability_thresholds",
        "timing",
        "gates",
    }
    unknown = set(config) - allowed
    if unknown:
        raise ValueError(f"unknown incremental-recertification fields: {sorted(unknown)!r}")

    groups = int(config.get("groups", 8))
    seed = int(config.get("seed", 0))
    hands = int(config.get("hands_per_player", 5))
    families = tuple(str(value) for value in config.get("families", CONTEXT_FAMILIES))
    splits = tuple(str(value) for value in config.get("included_splits", ("development",)))
    sequential = config.get("sequential_raise", True)
    solver = str(config.get("solver", "dcfr"))
    checkpoints = tuple(
        int(value) for value in config.get("source_policy_checkpoints", (1, 4, 16))
    )
    thresholds = tuple(
        float(value)
        for value in config.get(
            "normalized_exploitability_thresholds",
            (0.001, 0.005, 0.01, 0.02),
        )
    )
    perturbations = config.get("perturbations")
    timing = config.get("timing")
    gates = config.get("gates")

    if groups <= 0:
        raise ValueError("groups must be positive")
    if not 2 <= hands <= 8:
        raise ValueError("hands_per_player must be between two and eight")
    if (
        not families
        or len(set(families)) != len(families)
        or set(families) - set(CONTEXT_FAMILIES)
    ):
        raise ValueError("families must be unique supported context families")
    if splits != ("development",):
        raise ValueError("the incremental recertification benchmark is development-only")
    if sequential is not True:
        raise ValueError("sequential_raise must be true")
    if solver not in UPDATE_RULES:
        raise ValueError(f"unsupported solver {solver!r}")
    if not checkpoints or checkpoints != tuple(sorted(set(checkpoints))) or checkpoints[0] <= 0:
        raise ValueError("source_policy_checkpoints must be sorted unique positive integers")
    if not thresholds or thresholds != tuple(sorted(set(thresholds))) or any(
        not math.isfinite(value) or value <= 0.0 for value in thresholds
    ):
        raise ValueError("normalized thresholds must be sorted unique positive values")

    if not isinstance(perturbations, list) or not perturbations:
        raise ValueError("perturbations must be a nonempty array")
    normalized_perturbations = []
    names = []
    kinds = set()
    for item in perturbations:
        if not isinstance(item, dict):
            raise ValueError("each perturbation must be an object")
        kind = str(item.get("kind", ""))
        required = (
            {"name", "kind", "player", "root_tv_budget", "maximum_donor_fraction"}
            if kind == "blocker_reweight"
            else {"name", "kind", "player"}
            if kind == "support_swap"
            else set()
        )
        if not required or set(item) != required:
            raise ValueError("perturbation fields do not match a supported frozen kind")
        name = str(item["name"])
        player = int(item["player"])
        if not name or player not in (0, 1):
            raise ValueError("perturbation name must be nonempty and player must be zero or one")
        normalized: dict[str, object] = {
            "name": name,
            "kind": kind,
            "player": player,
        }
        if kind == "blocker_reweight":
            root_tv = float(item["root_tv_budget"])
            donor_fraction = float(item["maximum_donor_fraction"])
            if not 0.0 < root_tv < 0.5 or not 0.0 < donor_fraction < 1.0:
                raise ValueError("blocker-reweight controls must lie in their open unit ranges")
            normalized.update(
                root_tv_budget=root_tv,
                maximum_donor_fraction=donor_fraction,
            )
        normalized_perturbations.append(normalized)
        names.append(name)
        kinds.add(kind)
    if len(set(names)) != len(names):
        raise ValueError("perturbation names must be unique")
    if kinds != {"blocker_reweight", "support_swap"}:
        raise ValueError("benchmark must include both reweight and support-swap perturbations")

    timing_fields = {
        "batches",
        "cache_inner_repetitions",
        "delta_inner_repetitions",
        "full_inner_repetitions",
        "incremental_inner_repetitions",
        "bound_inner_repetitions",
    }
    if not isinstance(timing, dict) or set(timing) != timing_fields:
        raise ValueError("timing must contain exactly the frozen timing controls")
    normalized_timing = {key: int(value) for key, value in timing.items()}
    if any(value <= 0 for value in normalized_timing.values()):
        raise ValueError("all timing controls must be positive")

    gate_fields = {
        "maximum_absolute_evaluation_error",
        "minimum_aggregate_hot_speedup",
        "minimum_shared_delta_speedup",
        "minimum_fraction_incremental_faster",
    }
    if not isinstance(gates, dict) or set(gates) != gate_fields:
        raise ValueError("gates must contain exactly the frozen performance controls")
    normalized_gates = {key: float(value) for key, value in gates.items()}
    if any(not math.isfinite(value) or value < 0.0 for value in normalized_gates.values()):
        raise ValueError("gate values must be finite and nonnegative")
    if normalized_gates["minimum_fraction_incremental_faster"] > 1.0:
        raise ValueError("minimum faster fraction cannot exceed one")

    return {
        "groups": groups,
        "seed": seed,
        "hands_per_player": hands,
        "families": families,
        "included_splits": splits,
        "sequential_raise": True,
        "perturbations": tuple(normalized_perturbations),
        "solver": solver,
        "source_policy_checkpoints": checkpoints,
        "normalized_exploitability_thresholds": thresholds,
        "timing": normalized_timing,
        "gates": normalized_gates,
    }


def _finite_policies(
    game: RiverHoldem,
    *,
    solver_name: str,
    checkpoints: tuple[int, ...],
) -> tuple[dict[int, Policy], dict[int, float]]:
    solver = TabularCFR(game, variant=solver_name)  # type: ignore[arg-type]
    policies = {}
    cumulative_milliseconds = {}
    cumulative_ns = 0
    previous = 0
    for checkpoint in checkpoints:
        start = time.perf_counter_ns()
        solver.run(checkpoint - previous)
        cumulative_ns += time.perf_counter_ns() - start
        policies[checkpoint] = solver.average_strategy()
        cumulative_milliseconds[checkpoint] = cumulative_ns / 1_000_000.0
        previous = checkpoint
    return policies, cumulative_milliseconds


def run_river_incremental_experiment(config: dict[str, Any]) -> dict[str, Any]:
    parsed = _validate_config(config)
    experiment_start = time.perf_counter()
    timing = parsed["timing"]
    batches = timing["batches"]
    contexts = generate_river_contexts(
        groups=parsed["groups"],
        seed=parsed["seed"],
        hands_per_player=parsed["hands_per_player"],
        families=parsed["families"],
        splits=parsed["included_splits"],
        sequential_raise=True,
    )
    if not contexts:
        raise ValueError("configuration generated no development contexts")

    source_records: list[dict[str, Any]] = []
    pair_records: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []

    for context in contexts:
        source = context.game
        target_entries = []
        for perturbation in parsed["perturbations"]:
            target, metadata = _make_target(source, perturbation)
            initial_delta = RiverRangeDelta.between(source, target)
            measured_delta, delta_timing = _timed(
                lambda source=source, target=target: RiverRangeDelta.between(
                    source, target
                ),
                batches=batches,
                inner_repetitions=timing["delta_inner_repetitions"],
            )
            if measured_delta != initial_delta:
                raise AssertionError("range delta discovery is not deterministic")
            pair_record = {
                "target_id": f"{context.context_id}-{perturbation['name']}",
                "context_id": context.context_id,
                "group_id": context.group_id,
                "family": context.family,
                "perturbation": perturbation,
                "metadata": metadata,
                "source_deals": len(source.deals),
                "target_deals": len(target.deals),
                "changed_deals": len(initial_delta.changes),
                "changed_deal_fraction_of_source": len(initial_delta.changes) / len(source.deals),
                "added_deals": initial_delta.added_deals,
                "removed_deals": initial_delta.removed_deals,
                "reweighted_deals": initial_delta.reweighted_deals,
                "root_joint_total_variation": initial_delta.total_variation,
                "delta_discovery_timing": delta_timing,
            }
            pair_records.append(pair_record)
            target_entries.append((target, initial_delta, pair_record))

        policies, solver_milliseconds = _finite_policies(
            source,
            solver_name=parsed["solver"],
            checkpoints=parsed["source_policy_checkpoints"],
        )
        for checkpoint in parsed["source_policy_checkpoints"]:
            policy = policies[checkpoint]
            cache, cache_timing = _timed(
                lambda source=source, policy=policy: RiverPolicyEvaluationCache(
                    source, policy
                ),
                batches=batches,
                inner_repetitions=timing["cache_inner_repetitions"],
            )
            source_full = evaluate_profile(source, policy)
            source_error = _evaluation_error(cache.source_evaluation, source_full)
            source_record = {
                "context_id": context.context_id,
                "group_id": context.group_id,
                "family": context.family,
                "checkpoint": checkpoint,
                "solver": parsed["solver"],
                "solver_cumulative_milliseconds": solver_milliseconds[checkpoint],
                "information_sets": len(policy),
                "source_exploitability": source_full.exploitability,
                "normalized_source_exploitability": (
                    (source_full.exploitability or 0.0) / source.payoff_span
                ),
                "compiled_deals": cache.compiled_deals,
                "source_compiled_evaluation_error": source_error,
                "cache_build_timing": cache_timing,
            }
            source_records.append(source_record)

            for target, delta, pair_record in target_entries:
                incremental_once = cache.recertify(target, delta)
                full_once = evaluate_profile(target, policy)
                exact_error = _evaluation_error(incremental_once.evaluation, full_once)

                measured_full, full_timing = _timed(
                    lambda target=target, policy=policy: evaluate_profile(target, policy),
                    batches=batches,
                    inner_repetitions=timing["full_inner_repetitions"],
                )
                measured_incremental, incremental_timing = _timed(
                    lambda cache=cache, target=target, delta=delta: cache.recertify(
                        target, delta
                    ),
                    batches=batches,
                    inner_repetitions=timing["incremental_inner_repetitions"],
                )
                source_exploitability = source_full.exploitability or 0.0
                certificate_once = transferred_exploitability_certificate(
                    source,
                    target,
                    source_exploitability=source_exploitability,
                )
                measured_certificate, bound_timing = _timed(
                    lambda source=source,
                    target=target,
                    source_exploitability=source_exploitability: (
                        transferred_exploitability_certificate(
                            source,
                            target,
                            source_exploitability=source_exploitability,
                        )
                    ),
                    batches=batches,
                    inner_repetitions=timing["bound_inner_repetitions"],
                )
                exact_error = max(
                    exact_error,
                    _evaluation_error(measured_incremental.evaluation, measured_full),
                )
                if measured_certificate != certificate_once:
                    raise AssertionError("TV certificate is not deterministic")

                full_ms = float(full_timing["median_milliseconds"])
                incremental_ms = float(incremental_timing["median_milliseconds"])
                actual_exploitability = full_once.exploitability or 0.0
                threshold_results = []
                for threshold in parsed["normalized_exploitability_thresholds"]:
                    absolute_threshold = threshold * target.payoff_span
                    bound_passes = (
                        certificate_once.capped_target_upper_bound <= absolute_threshold
                    )
                    exact_passes = actual_exploitability <= absolute_threshold
                    threshold_results.append(
                        {
                            "normalized_threshold": threshold,
                            "tv_bound_certifies": bound_passes,
                            "exact_recertification_passes": exact_passes,
                            "bound_false_positive": bound_passes and not exact_passes,
                        }
                    )

                records.append(
                    {
                        "target_id": pair_record["target_id"],
                        "context_id": context.context_id,
                        "group_id": context.group_id,
                        "family": context.family,
                        "perturbation_name": pair_record["perturbation"]["name"],
                        "perturbation_kind": pair_record["perturbation"]["kind"],
                        "source_policy_checkpoint": checkpoint,
                        "source_policy_is_finite_dcfr": parsed["solver"] == "dcfr",
                        "source_exploitability": source_exploitability,
                        "target_exploitability": actual_exploitability,
                        "normalized_target_exploitability": (
                            actual_exploitability / target.payoff_span
                        ),
                        "tv_bound_target_upper": certificate_once.capped_target_upper_bound,
                        "normalized_tv_bound_target_upper": (
                            certificate_once.capped_target_upper_bound / target.payoff_span
                        ),
                        "maximum_absolute_evaluation_error": exact_error,
                        "full_recertification_timing": full_timing,
                        "incremental_recertification_timing": incremental_timing,
                        "tv_bound_timing": bound_timing,
                        "hot_exact_speedup": full_ms / incremental_ms,
                        "incremental_faster": incremental_ms < full_ms,
                        "diagnostics": asdict(incremental_once.diagnostics),
                        "threshold_results": threshold_results,
                    }
                )

    full_total = sum(
        float(record["full_recertification_timing"]["median_milliseconds"])
        for record in records
    )
    incremental_total = sum(
        float(record["incremental_recertification_timing"]["median_milliseconds"])
        for record in records
    )
    delta_total = sum(
        float(pair["delta_discovery_timing"]["median_milliseconds"])
        for pair in pair_records
    )
    cache_total = sum(
        float(source["cache_build_timing"]["median_milliseconds"])
        for source in source_records
    )
    bound_total = sum(
        float(record["tv_bound_timing"]["median_milliseconds"])
        for record in records
    )
    maximum_checkpoint = max(parsed["source_policy_checkpoints"])
    source_solver_total = sum(
        float(source["solver_cumulative_milliseconds"])
        for source in source_records
        if source["checkpoint"] == maximum_checkpoint
    )
    speedups = [float(record["hot_exact_speedup"]) for record in records]
    errors = [
        *(float(record["maximum_absolute_evaluation_error"]) for record in records),
        *(float(source["source_compiled_evaluation_error"]) for source in source_records),
    ]
    changed_fractions = [
        float(pair["changed_deal_fraction_of_source"]) for pair in pair_records
    ]
    faster_fraction = mean(float(record["incremental_faster"]) for record in records)
    hot_speedup = full_total / incremental_total
    shared_delta_speedup = full_total / (incremental_total + delta_total)
    deltas_per_record = len(parsed["source_policy_checkpoints"])
    unshared_delta_speedup = full_total / (
        incremental_total + delta_total * deltas_per_record
    )
    cache_charged_speedup = full_total / (
        incremental_total + delta_total + cache_total
    )
    fully_charged_speedup = full_total / (
        incremental_total + delta_total + cache_total + source_solver_total
    )
    mean_cache_build = cache_total / len(source_records)
    mean_hot_savings = (full_total - incremental_total) / len(records)
    cache_break_even_recertifications = (
        mean_cache_build / mean_hot_savings
        if mean_hot_savings > 0.0
        else None
    )

    threshold_summary = []
    for threshold in parsed["normalized_exploitability_thresholds"]:
        entries = [
            entry
            for record in records
            for entry in record["threshold_results"]
            if entry["normalized_threshold"] == threshold
        ]
        threshold_summary.append(
            {
                "normalized_threshold": threshold,
                "records": len(entries),
                "tv_bound_certified": sum(entry["tv_bound_certifies"] for entry in entries),
                "exact_recertification_passed": sum(
                    entry["exact_recertification_passes"] for entry in entries
                ),
                "bound_false_positives": sum(
                    entry["bound_false_positive"] for entry in entries
                ),
            }
        )

    gate_config = parsed["gates"]
    gate_results = {
        "exact_identity": max(errors) <= gate_config["maximum_absolute_evaluation_error"],
        "aggregate_hot_speedup": hot_speedup
        >= gate_config["minimum_aggregate_hot_speedup"],
        "shared_delta_speedup": shared_delta_speedup
        >= gate_config["minimum_shared_delta_speedup"],
        "incremental_faster_fraction": faster_fraction
        >= gate_config["minimum_fraction_incremental_faster"],
        "tv_bound_has_zero_false_positives": all(
            row["bound_false_positives"] == 0 for row in threshold_summary
        ),
        "support_swaps_are_exact_and_unseen": all(
            pair["changed_deals"] == 2
            and pair["added_deals"] == 1
            and pair["removed_deals"] == 1
            and pair["reweighted_deals"] == 0
            and pair["metadata"]["new_private_hand_was_absent"]
            for pair in pair_records
            if pair["perturbation"]["kind"] == "support_swap"
        ),
        "blocker_reweights_change_exactly_two_supported_deals": all(
            pair["changed_deals"] == 2
            and pair["added_deals"] == 0
            and pair["removed_deals"] == 0
            and pair["reweighted_deals"] == 2
            for pair in pair_records
            if pair["perturbation"]["kind"] == "blocker_reweight"
        ),
    }

    summaries = []
    for kind in ("blocker_reweight", "support_swap"):
        for checkpoint in parsed["source_policy_checkpoints"]:
            rows = [
                record
                for record in records
                if record["perturbation_kind"] == kind
                and record["source_policy_checkpoint"] == checkpoint
            ]
            row_full = sum(
                float(row["full_recertification_timing"]["median_milliseconds"])
                for row in rows
            )
            row_incremental = sum(
                float(
                    row["incremental_recertification_timing"]["median_milliseconds"]
                )
                for row in rows
            )
            summaries.append(
                {
                    "perturbation_kind": kind,
                    "source_policy_checkpoint": checkpoint,
                    "records": len(rows),
                    "mean_normalized_target_exploitability": mean(
                        float(row["normalized_target_exploitability"]) for row in rows
                    ),
                    "maximum_absolute_evaluation_error": max(
                        float(row["maximum_absolute_evaluation_error"]) for row in rows
                    ),
                    "aggregate_hot_exact_speedup": row_full / row_incremental,
                    "mean_affected_player0_hands": mean(
                        float(row["diagnostics"]["affected_player0_hands"])
                        for row in rows
                    ),
                    "mean_affected_player1_hands": mean(
                        float(row["diagnostics"]["affected_player1_hands"])
                        for row in rows
                    ),
                }
            )

    return {
        "schema_version": 1,
        "experiment_type": "finite_policy_exact_delta_river_recertification",
        "status": "development_measurement_only",
        "config": {
            **parsed,
            "families": list(parsed["families"]),
            "included_splits": list(parsed["included_splits"]),
            "perturbations": list(parsed["perturbations"]),
            "source_policy_checkpoints": list(parsed["source_policy_checkpoints"]),
            "normalized_exploitability_thresholds": list(
                parsed["normalized_exploitability_thresholds"]
            ),
        },
        "environment": environment_metadata(),
        "safety_contract": {
            "range_delta_is_lossless_and_provenance_bound": True,
            "direct_approximate_strategy_cache_hits_remain_forbidden": True,
            "incremental_result_must_match_independent_full_evaluation": True,
            "source_policies_are_finite_solver_outputs_not_equilibrium_teachers": True,
            "support_changes_include_an_unseen_private_hand": True,
            "delta_discovery_cache_build_and_application_costs_are_separate": True,
            "timings_are_hot_python_reference_kernel_measurements": True,
        },
        "counts": {
            "groups": len({context.group_id for context in contexts}),
            "source_contexts": len(contexts),
            "source_policy_caches": len(source_records),
            "range_pairs": len(pair_records),
            "recertification_records": len(records),
        },
        "aggregate": {
            "maximum_absolute_evaluation_error": max(errors),
            "full_recertification_median_time_sum_milliseconds": full_total,
            "incremental_apply_median_time_sum_milliseconds": incremental_total,
            "shared_delta_discovery_median_time_sum_milliseconds": delta_total,
            "compiled_cache_build_median_time_sum_milliseconds": cache_total,
            "tv_bound_median_time_sum_milliseconds": bound_total,
            "finite_source_solver_time_to_max_checkpoint_milliseconds": source_solver_total,
            "aggregate_hot_exact_speedup": hot_speedup,
            "aggregate_shared_delta_exact_speedup": shared_delta_speedup,
            "aggregate_unshared_delta_exact_speedup": unshared_delta_speedup,
            "aggregate_cache_build_and_shared_delta_charged_speedup": cache_charged_speedup,
            "one_batch_source_solver_cache_and_delta_charged_speedup": fully_charged_speedup,
            "estimated_cache_build_break_even_recertifications": (
                cache_break_even_recertifications
            ),
            "fraction_records_incremental_faster": faster_fraction,
            "median_record_hot_speedup": median(speedups),
            "p05_record_hot_speedup": _percentile(speedups, 0.05),
            "p95_record_hot_speedup": _percentile(speedups, 0.95),
            "median_changed_deal_fraction": median(changed_fractions),
            "maximum_changed_deal_fraction": max(changed_fractions),
        },
        "gates": {
            "requirements": gate_config,
            "results": gate_results,
            "passed": all(gate_results.values()),
        },
        "tv_certificate_summary": threshold_summary,
        "summaries": summaries,
        "timing": {"wall_seconds": time.perf_counter() - experiment_start},
        "sources": source_records,
        "pairs": pair_records,
        "records": records,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    result = run_river_incremental_experiment(config)
    rendered = json.dumps(result, indent=2, sort_keys=True, allow_nan=False)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(
        "finite-policy exact incremental recertification: "
        f"records={result['counts']['recertification_records']}, "
        f"hot_speedup={result['aggregate']['aggregate_hot_exact_speedup']:.3f}x, "
        f"shared_delta_speedup={result['aggregate']['aggregate_shared_delta_exact_speedup']:.3f}x, "
        f"passed={result['gates']['passed']}, "
        f"wall={result['timing']['wall_seconds']:.3f}s"
    )
    if args.output is not None:
        print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
