"""Build causal opportunity traces and perfect-information allocation controls.

Exact objectives and future outcomes are diagnostic labels only.  Online features
are assembled from explicit allowlists at each phase so a candidate-ready stop
decision cannot see the pricing result it is deciding whether to buy.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from copy import deepcopy
from math import ceil, floor, isfinite
from pathlib import Path
from statistics import mean, median
from typing import Any, Iterable


TOLERANCE = 1e-12

START_FEATURE_NAMES = (
    "public_reach_probability",
    "public_history_length",
    "resolver_player",
)

CANDIDATE_FEATURE_NAMES = (
    *START_FEATURE_NAMES,
    "update_index",
    "columns_before_update",
    "response_constraints_before_update",
    "response_constraints_after_separation",
    "new_response_constraints",
    "candidate_support_size",
    "candidate_max_column_weight",
    "candidate_column_weight_concentration",
    "candidate_column_weight_entropy",
    "safe_candidate",
    "incumbent_updated",
    "actual_sum_margin",
    "actual_min_margin",
    "positive_frontier_violation",
    "incumbent_sum_margin",
    "latest_incumbent_gain",
    "restricted_master_objective",
    "restricted_auxiliary_margin_sum",
    "master_optimism_gap",
    "master_to_incumbent_gap",
    "master_duality_gap",
    "effective_column_dual",
    "response_dual_mass",
    "response_dual_active_count",
    "response_dual_max_share",
    "response_dual_concentration",
    "response_dual_entropy",
    "current_candidate_phase_milliseconds",
    "latest_complete_cycle_milliseconds",
    "mean_observed_candidate_phase_milliseconds",
    "mean_prior_pricing_milliseconds",
    "cumulative_candidate_milliseconds",
    "observed_unsafe_fraction",
)

POST_PRICING_FEATURE_NAMES = (
    *CANDIDATE_FEATURE_NAMES,
    "pricing_performed",
    "pricing_milliseconds",
    "best_pricing_score",
    "best_reduced_cost",
    "positive_reduced_cost",
    "column_added",
    "columns_after_pricing",
    "response_constraints_after_pricing",
    "converged",
    "cumulative_paid_milliseconds",
)

LABEL_NAMES = (
    "exact_sum_margin_optimum",
    "exact_remaining_headroom",
    "trace_attainable_sum_margin",
    "trace_remaining_gain",
    "future_improvement_positive",
    "next_candidate_exists",
    "next_candidate_gain",
    "next_candidate_cost_milliseconds",
    "next_candidate_gain_per_millisecond",
    "first_future_improvement_update",
    "candidate_steps_to_first_improvement",
    "cost_to_first_improvement_milliseconds",
    "first_future_improvement_gain",
    "first_future_improvement_gain_per_millisecond",
    "best_future_gain_per_millisecond",
    "best_rate_future_update",
    "hidden_exact_br_optimum",
    "hidden_current_br_reduction",
    "hidden_trace_remaining_gain",
)

FORBIDDEN_ONLINE_NAME_FRAGMENTS = (
    "exact",
    "hidden",
    "optimum",
    "future",
    "regret",
    "capture",
    "final_",
)


def _number(value: Any, name: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be numeric, not boolean")
    result = float(value)
    if not isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def _optional_number(value: Any) -> float | None:
    if value is None:
        return None
    result = float(value)
    return result if isfinite(result) else None


def _milliseconds(row: dict[str, Any], field: str) -> float:
    return 1_000.0 * _number(row[field], field)


def _safe_ratio(numerator: float, denominator: float) -> float | None:
    return numerator / denominator if denominator > TOLERANCE else None


def _percentile(values: Iterable[float], percentile: float) -> float:
    ordered = sorted(values)
    if not ordered:
        raise ValueError("cannot take a percentile of an empty sequence")
    index = max(0, ceil(percentile * len(ordered)) - 1)
    return ordered[index]


def _group_source_records(
    source_name: str,
    matrix: dict[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    if matrix.get("experiment_type") != "dynamic_constrained_generation_matrix":
        raise ValueError(f"{source_name} is not a constrained-generation matrix")
    raw_records = matrix.get("records")
    if not isinstance(raw_records, list) or not raw_records:
        raise ValueError(f"{source_name} must contain nonempty records")
    grouped: dict[str, list[dict[str, Any]]] = {}
    for raw in raw_records:
        if not isinstance(raw, dict):
            raise ValueError(f"{source_name} contains a non-object record")
        local_id = str(raw.get("boundary_id", ""))
        if not local_id:
            raise ValueError(f"{source_name} record omits boundary_id")
        grouped.setdefault(f"{source_name}:{local_id}", []).append(deepcopy(raw))
    for boundary_id, rows in grouped.items():
        rows.sort(key=lambda row: int(row["update"]))
        previous_candidate = -1.0
        previous_decision = -1.0
        previous_incumbent = -TOLERANCE
        exact_optimum: float | None = None
        for expected_update, row in enumerate(rows, start=1):
            update = int(row["update"])
            if update != expected_update:
                raise ValueError(f"{boundary_id} updates must be consecutive from one")
            candidate = _milliseconds(row, "cumulative_candidate_compute_seconds")
            decision = _milliseconds(row, "cumulative_decision_compute_seconds")
            incumbent = _number(row["incumbent_sum_margin"], "incumbent_sum_margin")
            optimum = _number(row["exact_sum_margin_optimum"], "exact_sum_margin_optimum")
            if candidate + TOLERANCE < previous_decision:
                raise ValueError(f"{boundary_id} candidate time is not causal")
            if decision + TOLERANCE < candidate:
                raise ValueError(f"{boundary_id} decision time precedes its candidate")
            if candidate + TOLERANCE < previous_candidate:
                raise ValueError(f"{boundary_id} candidate time is not monotone")
            if incumbent + TOLERANCE < previous_incumbent:
                raise ValueError(f"{boundary_id} incumbent is not monotone")
            if exact_optimum is not None and abs(optimum - exact_optimum) > 1e-9:
                raise ValueError(f"{boundary_id} exact optimum changes within a trace")
            if incumbent > optimum + 1e-8:
                raise ValueError(f"{boundary_id} incumbent exceeds the exact optimum")
            previous_candidate = candidate
            previous_decision = decision
            previous_incumbent = incumbent
            exact_optimum = optimum
    return grouped


def _metadata(source_name: str, boundary_id: str, row: dict[str, Any]) -> dict[str, Any]:
    return {
        "source": source_name,
        "boundary_id": boundary_id,
        "blueprint_solver": row.get("blueprint_solver"),
        "blueprint_iterations": row.get("blueprint_iterations"),
        "history": deepcopy(row.get("history", [])),
    }


def _start_features(row: dict[str, Any]) -> dict[str, Any]:
    history = row.get("history", [])
    if not isinstance(history, list):
        raise ValueError("history must be a list")
    return {
        "public_reach_probability": _number(
            row["public_reach_probability"], "public_reach_probability"
        ),
        "public_history_length": len(history),
        "resolver_player": int(row["resolver_player"]),
    }


def _candidate_features(
    rows: list[dict[str, Any]],
    index: int,
) -> dict[str, Any]:
    row = rows[index]
    previous = rows[index - 1] if index else None
    features = _start_features(row)
    candidate_ms = _milliseconds(row, "cumulative_candidate_compute_seconds")
    previous_candidate_ms = (
        _milliseconds(previous, "cumulative_candidate_compute_seconds")
        if previous is not None
        else 0.0
    )
    previous_decision_ms = (
        _milliseconds(previous, "cumulative_decision_compute_seconds")
        if previous is not None
        else 0.0
    )
    previous_incumbent = (
        _number(previous["incumbent_sum_margin"], "incumbent_sum_margin")
        if previous is not None
        else 0.0
    )
    observed_candidate_phase_costs = []
    for phase_index, phase_row in enumerate(rows[: index + 1]):
        if phase_index == 0:
            phase_start = 0.0
        else:
            phase_start = _milliseconds(
                rows[phase_index - 1], "cumulative_decision_compute_seconds"
            )
        observed_candidate_phase_costs.append(
            _milliseconds(phase_row, "cumulative_candidate_compute_seconds")
            - phase_start
        )
    prior_pricing_costs = [
        _milliseconds(prior, "pricing_seconds") for prior in rows[:index]
    ]
    incumbent = _number(row["incumbent_sum_margin"], "incumbent_sum_margin")
    actual = _number(row["actual_sum_margin"], "actual_sum_margin")
    restricted = _number(
        row["restricted_master_objective"], "restricted_master_objective"
    )
    auxiliary = _number(
        row["restricted_auxiliary_margin_sum"],
        "restricted_auxiliary_margin_sum",
    )
    constraints_before = int(row["response_constraints_before_update"])
    new_constraints = int(row["added_response_constraints"])
    features.update(
        {
            "update_index": int(row["update"]),
            "columns_before_update": int(row["columns_before_update"]),
            "response_constraints_before_update": constraints_before,
            "response_constraints_after_separation": (
                constraints_before + new_constraints
            ),
            "new_response_constraints": new_constraints,
            "candidate_support_size": int(row["candidate_support_size"]),
            "candidate_max_column_weight": _number(
                row.get("candidate_max_column_weight", 0.0),
                "candidate_max_column_weight",
            ),
            "candidate_column_weight_concentration": _number(
                row.get("candidate_column_weight_concentration", 0.0),
                "candidate_column_weight_concentration",
            ),
            "candidate_column_weight_entropy": _number(
                row.get("candidate_column_weight_entropy", 0.0),
                "candidate_column_weight_entropy",
            ),
            "safe_candidate": bool(row["safe_candidate"]),
            "incumbent_updated": bool(row["incumbent_updated"]),
            "actual_sum_margin": actual,
            "actual_min_margin": _number(row["actual_min_margin"], "actual_min_margin"),
            "positive_frontier_violation": _number(
                row["total_positive_frontier_violation"],
                "total_positive_frontier_violation",
            ),
            "incumbent_sum_margin": incumbent,
            "latest_incumbent_gain": incumbent - previous_incumbent,
            "restricted_master_objective": restricted,
            "restricted_auxiliary_margin_sum": auxiliary,
            "master_optimism_gap": auxiliary - actual,
            "master_to_incumbent_gap": restricted - incumbent,
            "master_duality_gap": _number(
                row["master_duality_gap"], "master_duality_gap"
            ),
            "effective_column_dual": _number(
                row["effective_column_dual"], "effective_column_dual"
            ),
            "response_dual_mass": _number(
                row.get("response_dual_mass", 0.0), "response_dual_mass"
            ),
            "response_dual_active_count": int(
                row.get("response_dual_active_count", 0)
            ),
            "response_dual_max_share": _number(
                row.get("response_dual_max_share", 0.0),
                "response_dual_max_share",
            ),
            "response_dual_concentration": _number(
                row.get("response_dual_concentration", 0.0),
                "response_dual_concentration",
            ),
            "response_dual_entropy": _number(
                row.get("response_dual_entropy", 0.0),
                "response_dual_entropy",
            ),
            "current_candidate_phase_milliseconds": (
                candidate_ms - previous_decision_ms
            ),
            "latest_complete_cycle_milliseconds": (
                candidate_ms - previous_candidate_ms
            ),
            "mean_observed_candidate_phase_milliseconds": mean(
                observed_candidate_phase_costs
            ),
            "mean_prior_pricing_milliseconds": (
                mean(prior_pricing_costs) if prior_pricing_costs else 0.0
            ),
            "cumulative_candidate_milliseconds": candidate_ms,
            "observed_unsafe_fraction": _number(
                row["cumulative_unsafe_candidates"],
                "cumulative_unsafe_candidates",
            )
            / int(row["update"]),
        }
    )
    return features


def _post_pricing_features(
    rows: list[dict[str, Any]],
    index: int,
) -> dict[str, Any]:
    row = rows[index]
    features = _candidate_features(rows, index)
    reduced_cost = _optional_number(row.get("best_reduced_cost"))
    features.update(
        {
            "pricing_performed": bool(row["pricing_performed"]),
            "pricing_milliseconds": _milliseconds(row, "pricing_seconds"),
            "best_pricing_score": _optional_number(row.get("best_pricing_score")),
            "best_reduced_cost": reduced_cost,
            "positive_reduced_cost": (
                max(0.0, reduced_cost) if reduced_cost is not None else None
            ),
            "column_added": row.get("added_column") is not None,
            "columns_after_pricing": int(row["columns_after_update"]),
            "response_constraints_after_pricing": int(
                row["response_constraints_after_update"]
            ),
            "converged": bool(row["converged"]),
            "cumulative_paid_milliseconds": _milliseconds(
                row, "cumulative_decision_compute_seconds"
            ),
        }
    )
    return features


def _labels(
    rows: list[dict[str, Any]],
    index: int | None,
    phase: str,
) -> dict[str, Any]:
    first = rows[0]
    current = rows[index] if index is not None else None
    future = rows if index is None else rows[index + 1 :]
    current_margin = (
        _number(current["incumbent_sum_margin"], "incumbent_sum_margin")
        if current is not None
        else 0.0
    )
    current_hidden = (
        _number(
            current["incumbent_hidden_br_reduction"],
            "incumbent_hidden_br_reduction",
        )
        if current is not None
        else 0.0
    )
    exact_optimum = _number(
        first["exact_sum_margin_optimum"], "exact_sum_margin_optimum"
    )
    hidden_optimum = _number(
        first["exact_hidden_br_optimum"], "exact_hidden_br_optimum"
    )
    trace_attainable = max(
        _number(row["incumbent_sum_margin"], "incumbent_sum_margin")
        for row in rows
    )
    hidden_trace_attainable = max(
        _number(
            row["incumbent_hidden_br_reduction"],
            "incumbent_hidden_br_reduction",
        )
        for row in rows
    )
    next_row = future[0] if future else None
    if current is None:
        current_time_ms = 0.0
    elif phase == "candidate_ready":
        current_time_ms = _milliseconds(
            current, "cumulative_candidate_compute_seconds"
        )
    else:
        current_time_ms = _milliseconds(
            current, "cumulative_decision_compute_seconds"
        )
    if next_row is None:
        next_gain = 0.0
        next_cost = None
        next_rate = None
    else:
        next_gain = max(
            0.0,
            _number(next_row["incumbent_sum_margin"], "incumbent_sum_margin")
            - current_margin,
        )
        next_cost = (
            _milliseconds(next_row, "cumulative_candidate_compute_seconds")
            - current_time_ms
        )
        next_rate = _safe_ratio(next_gain, next_cost)
    first_improving_row = next(
        (
            future_row
            for future_row in future
            if _number(
                future_row["incumbent_sum_margin"], "incumbent_sum_margin"
            )
            > current_margin + TOLERANCE
        ),
        None,
    )
    if first_improving_row is None:
        first_improvement_update = None
        steps_to_first_improvement = None
        cost_to_first_improvement = None
        first_improvement_gain = 0.0
        first_improvement_rate = None
    else:
        first_improvement_update = int(first_improving_row["update"])
        current_update = int(current["update"]) if current is not None else 0
        steps_to_first_improvement = first_improvement_update - current_update
        cost_to_first_improvement = (
            _milliseconds(
                first_improving_row, "cumulative_candidate_compute_seconds"
            )
            - current_time_ms
        )
        first_improvement_gain = (
            _number(
                first_improving_row["incumbent_sum_margin"],
                "incumbent_sum_margin",
            )
            - current_margin
        )
        first_improvement_rate = _safe_ratio(
            first_improvement_gain, cost_to_first_improvement
        )
    best_rate: float | None = None
    best_rate_update: int | None = None
    for future_row in future:
        gain = max(
            0.0,
            _number(future_row["incumbent_sum_margin"], "incumbent_sum_margin")
            - current_margin,
        )
        cost = (
            _milliseconds(future_row, "cumulative_candidate_compute_seconds")
            - current_time_ms
        )
        rate = _safe_ratio(gain, cost)
        if rate is not None and (best_rate is None or rate > best_rate + TOLERANCE):
            best_rate = rate
            best_rate_update = int(future_row["update"])
    remaining_gain = max(0.0, trace_attainable - current_margin)
    return {
        "exact_sum_margin_optimum": exact_optimum,
        "exact_remaining_headroom": max(0.0, exact_optimum - current_margin),
        "trace_attainable_sum_margin": trace_attainable,
        "trace_remaining_gain": remaining_gain,
        "future_improvement_positive": remaining_gain > TOLERANCE,
        "next_candidate_exists": next_row is not None,
        "next_candidate_gain": next_gain,
        "next_candidate_cost_milliseconds": next_cost,
        "next_candidate_gain_per_millisecond": next_rate,
        "first_future_improvement_update": first_improvement_update,
        "candidate_steps_to_first_improvement": steps_to_first_improvement,
        "cost_to_first_improvement_milliseconds": cost_to_first_improvement,
        "first_future_improvement_gain": first_improvement_gain,
        "first_future_improvement_gain_per_millisecond": first_improvement_rate,
        "best_future_gain_per_millisecond": best_rate,
        "best_rate_future_update": best_rate_update,
        "hidden_exact_br_optimum": hidden_optimum,
        "hidden_current_br_reduction": current_hidden,
        "hidden_trace_remaining_gain": max(
            0.0, hidden_trace_attainable - current_hidden
        ),
    }


def _assert_feature_contract(phase: str, features: dict[str, Any]) -> None:
    expected = {
        "boundary_start": START_FEATURE_NAMES,
        "candidate_ready": CANDIDATE_FEATURE_NAMES,
        "after_pricing": POST_PRICING_FEATURE_NAMES,
    }[phase]
    if tuple(features) != expected:
        raise AssertionError(f"{phase} feature order or membership changed")
    leaked = [
        name
        for name in features
        if any(fragment in name for fragment in FORBIDDEN_ONLINE_NAME_FRAGMENTS)
    ]
    if leaked:
        raise AssertionError(f"oracle-derived names entered online features: {leaked}")


def _trace_records(
    grouped: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for boundary_id in sorted(grouped):
        rows = grouped[boundary_id]
        source_name = boundary_id.split(":", 1)[0]
        first = rows[0]
        start_features = _start_features(first)
        _assert_feature_contract("boundary_start", start_features)
        records.append(
            {
                "decision_id": f"{boundary_id}:start",
                "phase": "boundary_start",
                "update": 0,
                "metadata": _metadata(source_name, boundary_id, first),
                "features": start_features,
                "labels": _labels(rows, None, "boundary_start"),
            }
        )
        for index, row in enumerate(rows):
            update = int(row["update"])
            candidate_features = _candidate_features(rows, index)
            _assert_feature_contract("candidate_ready", candidate_features)
            records.append(
                {
                    "decision_id": f"{boundary_id}:candidate:{update}",
                    "phase": "candidate_ready",
                    "update": update,
                    "metadata": _metadata(source_name, boundary_id, row),
                    "features": candidate_features,
                    "labels": _labels(rows, index, "candidate_ready"),
                }
            )
            if bool(row["pricing_performed"]):
                post_features = _post_pricing_features(rows, index)
                _assert_feature_contract("after_pricing", post_features)
                records.append(
                    {
                        "decision_id": f"{boundary_id}:pricing:{update}",
                        "phase": "after_pricing",
                        "update": update,
                        "metadata": _metadata(source_name, boundary_id, row),
                        "features": post_features,
                        "labels": _labels(rows, index, "after_pricing"),
                    }
                )
    return records


def _candidate_choices(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    choices = [{"update": 0, "cost_milliseconds": 0.0, "sum_margin": 0.0}]
    for row in rows:
        choice = {
            "update": int(row["update"]),
            "cost_milliseconds": _milliseconds(
                row, "cumulative_candidate_compute_seconds"
            ),
            "sum_margin": _number(
                row["incumbent_sum_margin"], "incumbent_sum_margin"
            ),
        }
        dominated = any(
            prior["cost_milliseconds"] <= choice["cost_milliseconds"] + TOLERANCE
            and prior["sum_margin"] >= choice["sum_margin"] - TOLERANCE
            for prior in choices
        )
        if not dominated:
            choices.append(choice)
    return choices


def _choice_summary(
    selections: list[dict[str, Any]],
    exact_total: float,
    available_ms: float,
) -> dict[str, Any]:
    score = sum(choice["sum_margin"] for choice in selections)
    costs = [choice["cost_milliseconds"] for choice in selections]
    used = sum(costs)
    return {
        "aggregate_sum_margin": score,
        "aggregate_sum_margin_capture": _safe_ratio(score, exact_total),
        "positive_boundaries": sum(
            choice["sum_margin"] > TOLERANCE for choice in selections
        ),
        "mean_selected_update": mean(choice["update"] for choice in selections),
        "mean_compute_used_milliseconds": mean(costs),
        "p95_compute_used_milliseconds": _percentile(costs, 0.95),
        "compute_utilization_fraction": _safe_ratio(used, available_ms),
        "sum_margin_per_used_millisecond": _safe_ratio(score, used),
        "sum_margin_per_available_millisecond": _safe_ratio(score, available_ms),
    }


def _independent_deadline_oracle(
    choices_by_boundary: list[list[dict[str, Any]]],
    deadline_ms: float,
    exact_total: float,
) -> dict[str, Any]:
    selected = []
    for choices in choices_by_boundary:
        eligible = [
            choice
            for choice in choices
            if choice["cost_milliseconds"] <= deadline_ms + TOLERANCE
        ]
        selected.append(
            max(
                eligible,
                key=lambda choice: (
                    choice["sum_margin"],
                    -choice["cost_milliseconds"],
                ),
            )
        )
    result = _choice_summary(
        selected,
        exact_total,
        deadline_ms * len(choices_by_boundary),
    )
    result["deadline_overruns"] = 0
    return result


def _quantized_group_value(
    choices_by_boundary: list[list[dict[str, Any]]],
    available_ms: float,
    quantum_ms: float,
    *,
    optimistic: bool,
) -> float:
    capacity = floor(available_ms / quantum_ms + TOLERANCE)
    full_choices = [
        max(
            choices,
            key=lambda choice: (
                choice["sum_margin"],
                -choice["cost_milliseconds"],
            ),
        )
        for choices in choices_by_boundary
    ]
    full_ticks = sum(
        (
            floor(choice["cost_milliseconds"] / quantum_ms + TOLERANCE)
            if optimistic
            else ceil(choice["cost_milliseconds"] / quantum_ms - TOLERANCE)
        )
        for choice in full_choices
    )
    if full_ticks <= capacity:
        return sum(choice["sum_margin"] for choice in full_choices)
    negative_infinity = float("-inf")
    values = [negative_infinity] * (capacity + 1)
    values[0] = 0.0
    for choices in choices_by_boundary:
        priced_choices = []
        for choice in choices:
            raw_ticks = choice["cost_milliseconds"] / quantum_ms
            ticks = (
                floor(raw_ticks + TOLERANCE)
                if optimistic
                else ceil(raw_ticks - TOLERANCE)
            )
            if ticks <= capacity:
                priced_choices.append((ticks, choice["sum_margin"]))
        next_values = [negative_infinity] * (capacity + 1)
        for ticks, score in priced_choices:
            for budget in range(ticks, capacity + 1):
                prior = values[budget - ticks]
                if prior != negative_infinity:
                    candidate = prior + score
                    if candidate > next_values[budget]:
                        next_values[budget] = candidate
        values = next_values
    return max(values)


def _fixed_checkpoint_selection(
    grouped: dict[str, list[dict[str, Any]]],
    update_budget: int,
) -> list[dict[str, Any]]:
    selections = []
    for rows in grouped.values():
        eligible = [row for row in rows if int(row["update"]) <= update_budget]
        row = eligible[-1]
        converged_early = bool(row["final_converged"]) and int(
            row["final_update"]
        ) < update_budget
        cost_field = (
            "cumulative_decision_compute_seconds"
            if converged_early
            else "cumulative_candidate_compute_seconds"
        )
        selections.append(
            {
                "update": int(row["update"]),
                "cost_milliseconds": _milliseconds(row, cost_field),
                "sum_margin": _number(
                    row["incumbent_sum_margin"], "incumbent_sum_margin"
                ),
            }
        )
    return selections


def _best_uniform_checkpoint(
    grouped: dict[str, list[dict[str, Any]]],
    deadline_ms: float,
    exact_total: float,
) -> dict[str, Any]:
    available = deadline_ms * len(grouped)
    candidates = []
    maximum_update = max(int(rows[-1]["update"]) for rows in grouped.values())
    for update in range(1, maximum_update + 1):
        selections = _fixed_checkpoint_selection(grouped, update)
        used = sum(choice["cost_milliseconds"] for choice in selections)
        if used <= available + TOLERANCE:
            summary = _choice_summary(selections, exact_total, available)
            summary["uniform_update_budget"] = update
            summary["deadline_overruns"] = sum(
                choice["cost_milliseconds"] > deadline_ms + TOLERANCE
                for choice in selections
            )
            candidates.append(summary)
    if not candidates:
        return {
            **_choice_summary(
                [
                    {"update": 0, "cost_milliseconds": 0.0, "sum_margin": 0.0}
                    for _ in grouped
                ],
                exact_total,
                available,
            ),
            "uniform_update_budget": 0,
            "deadline_overruns": 0,
        }
    return max(
        candidates,
        key=lambda row: (
            row["aggregate_sum_margin"],
            -row["mean_compute_used_milliseconds"],
        ),
    )


def _allocation_oracles(
    grouped: dict[str, list[dict[str, Any]]],
    deadlines_ms: tuple[float, ...],
    quantum_ms: float,
) -> list[dict[str, Any]]:
    choices_by_boundary = [_candidate_choices(rows) for rows in grouped.values()]
    exact_total = sum(
        _number(rows[0]["exact_sum_margin_optimum"], "exact_sum_margin_optimum")
        for rows in grouped.values()
    )
    summaries = []
    for deadline in deadlines_ms:
        available = deadline * len(grouped)
        independent = _independent_deadline_oracle(
            choices_by_boundary, deadline, exact_total
        )
        pooled_lower = _quantized_group_value(
            choices_by_boundary,
            available,
            quantum_ms,
            optimistic=False,
        )
        pooled_upper = _quantized_group_value(
            choices_by_boundary,
            available,
            quantum_ms,
            optimistic=True,
        )
        uniform = _best_uniform_checkpoint(grouped, deadline, exact_total)
        fixed_six = _choice_summary(
            _fixed_checkpoint_selection(grouped, 6),
            exact_total,
            available,
        )
        fixed_six["deadline_overruns"] = sum(
            choice["cost_milliseconds"] > deadline + TOLERANCE
            for choice in _fixed_checkpoint_selection(grouped, 6)
        )
        summaries.append(
            {
                "deadline_milliseconds": deadline,
                "boundaries": len(grouped),
                "aggregate_available_milliseconds": available,
                "independent_phase_fit_oracle": independent,
                "pooled_perfect_information": {
                    "conservative_sum_margin": pooled_lower,
                    "optimistic_sum_margin": pooled_upper,
                    "quantization_gap": pooled_upper - pooled_lower,
                    "conservative_sum_margin_capture": _safe_ratio(
                        pooled_lower, exact_total
                    ),
                    "optimistic_sum_margin_capture": _safe_ratio(
                        pooled_upper, exact_total
                    ),
                    "conservative_sum_margin_per_available_millisecond": (
                        _safe_ratio(pooled_lower, available)
                    ),
                    "gain_over_independent_phase_fit": (
                        pooled_lower - independent["aggregate_sum_margin"]
                    ),
                    "quantum_milliseconds": quantum_ms,
                },
                "best_uniform_checkpoint_under_aggregate_budget": uniform,
                "fixed_six_checkpoint": fixed_six,
            }
        )
    return summaries


def _blueprint_regime_groups(
    grouped: dict[str, list[dict[str, Any]]],
) -> dict[str, dict[str, list[dict[str, Any]]]]:
    regimes: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for boundary_id, rows in grouped.items():
        row = rows[0]
        source = boundary_id.split(":", 1)[0]
        regime_id = (
            f"{source}:{row.get('blueprint_solver')}:"
            f"{row.get('blueprint_iterations')}"
        )
        regimes.setdefault(regime_id, {})[boundary_id] = rows
    return regimes


def _regime_allocation_oracles(
    grouped: dict[str, list[dict[str, Any]]],
    deadlines_ms: tuple[float, ...],
    quantum_ms: float,
) -> dict[str, Any]:
    regimes = _blueprint_regime_groups(grouped)
    details = []
    for regime_id, regime_grouped in sorted(regimes.items()):
        details.append(
            {
                "regime_id": regime_id,
                "opportunity_distribution": _opportunity_distribution(
                    regime_grouped
                ),
                "allocation_oracles": _allocation_oracles(
                    regime_grouped, deadlines_ms, quantum_ms
                ),
            }
        )
    aggregate = []
    exact_total = sum(
        detail["opportunity_distribution"][
            "aggregate_exact_sum_margin_headroom"
        ]
        for detail in details
    )
    weighted_top_25_share = _safe_ratio(
        sum(
            detail["opportunity_distribution"][
                "aggregate_exact_sum_margin_headroom"
            ]
            * (
                detail["opportunity_distribution"][
                    "top_25_percent_headroom_share"
                ]
                or 0.0
            )
            for detail in details
        ),
        exact_total,
    )
    weighted_top_50_share = _safe_ratio(
        sum(
            detail["opportunity_distribution"][
                "aggregate_exact_sum_margin_headroom"
            ]
            * (
                detail["opportunity_distribution"][
                    "top_50_percent_headroom_share"
                ]
                or 0.0
            )
            for detail in details
        ),
        exact_total,
    )
    for deadline_index, deadline in enumerate(deadlines_ms):
        independent_score = sum(
            detail["allocation_oracles"][deadline_index][
                "independent_phase_fit_oracle"
            ]["aggregate_sum_margin"]
            for detail in details
        )
        conservative_score = sum(
            detail["allocation_oracles"][deadline_index][
                "pooled_perfect_information"
            ]["conservative_sum_margin"]
            for detail in details
        )
        optimistic_score = sum(
            detail["allocation_oracles"][deadline_index][
                "pooled_perfect_information"
            ]["optimistic_sum_margin"]
            for detail in details
        )
        regime_uniform_score = sum(
            detail["allocation_oracles"][deadline_index][
                "best_uniform_checkpoint_under_aggregate_budget"
            ]["aggregate_sum_margin"]
            for detail in details
        )
        aggregate.append(
            {
                "deadline_milliseconds": deadline,
                "blueprint_regimes": len(details),
                "aggregate_exact_sum_margin_headroom": exact_total,
                "independent_sum_margin": independent_score,
                "independent_sum_margin_capture": _safe_ratio(
                    independent_score, exact_total
                ),
                "regime_pooled_conservative_sum_margin": conservative_score,
                "regime_pooled_optimistic_sum_margin": optimistic_score,
                "regime_pooled_conservative_capture": _safe_ratio(
                    conservative_score, exact_total
                ),
                "regime_pooled_optimistic_capture": _safe_ratio(
                    optimistic_score, exact_total
                ),
                "regime_pooled_gain_over_independent": (
                    conservative_score - independent_score
                ),
                "regime_pooled_quantization_gap": (
                    optimistic_score - conservative_score
                ),
                "regime_best_uniform_checkpoint_sum_margin": (
                    regime_uniform_score
                ),
                "regime_best_uniform_checkpoint_capture": _safe_ratio(
                    regime_uniform_score, exact_total
                ),
                "regime_pool_gain_over_regime_best_uniform": (
                    conservative_score - regime_uniform_score
                ),
            }
        )
    return {
        "scope": (
            "compute can move among public boundaries only within one fixed "
            "blueprint solver/strength regime"
        ),
        "weighted_within_regime_top_25_percent_headroom_share": (
            weighted_top_25_share
        ),
        "weighted_within_regime_top_50_percent_headroom_share": (
            weighted_top_50_share
        ),
        "aggregate": aggregate,
        "regimes": details,
    }


def _average_ranks(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=values.__getitem__)
    ranks = [0.0] * len(values)
    position = 0
    while position < len(order):
        end = position + 1
        while end < len(order) and values[order[end]] == values[order[position]]:
            end += 1
        rank = (position + end - 1) / 2.0
        for index in order[position:end]:
            ranks[index] = rank
        position = end
    return ranks


def _spearman(left: list[float], right: list[float]) -> float | None:
    if len(left) < 3 or len(left) != len(right):
        return None
    left_ranks = _average_ranks(left)
    right_ranks = _average_ranks(right)
    left_mean = mean(left_ranks)
    right_mean = mean(right_ranks)
    numerator = sum(
        (a - left_mean) * (b - right_mean)
        for a, b in zip(left_ranks, right_ranks, strict=True)
    )
    left_scale = sum((value - left_mean) ** 2 for value in left_ranks) ** 0.5
    right_scale = sum((value - right_mean) ** 2 for value in right_ranks) ** 0.5
    return _safe_ratio(numerator, left_scale * right_scale)


def _signal_diagnostics(records: list[dict[str, Any]]) -> dict[str, Any]:
    slices = {
        "boundary_start": [row for row in records if row["phase"] == "boundary_start"],
        "candidate_ready_update_1": [
            row
            for row in records
            if row["phase"] == "candidate_ready" and row["update"] == 1
        ],
        "after_pricing_update_1": [
            row
            for row in records
            if row["phase"] == "after_pricing" and row["update"] == 1
        ],
        "all_candidate_ready": [
            row for row in records if row["phase"] == "candidate_ready"
        ],
        "all_after_pricing": [
            row for row in records if row["phase"] == "after_pricing"
        ],
    }
    targets = (
        "exact_remaining_headroom",
        "trace_remaining_gain",
        "next_candidate_gain_per_millisecond",
        "best_future_gain_per_millisecond",
    )
    result: dict[str, Any] = {}
    for slice_name, rows in slices.items():
        correlations = []
        feature_names = rows[0]["features"] if rows else {}
        for target in targets:
            for feature in feature_names:
                pairs = []
                for row in rows:
                    feature_value = row["features"].get(feature)
                    target_value = row["labels"].get(target)
                    if (
                        isinstance(feature_value, (int, float, bool))
                        and feature_value is not None
                        and isinstance(target_value, (int, float))
                        and target_value is not None
                        and isfinite(float(feature_value))
                        and isfinite(float(target_value))
                    ):
                        pairs.append((float(feature_value), float(target_value)))
                if len({left for left, _ in pairs}) < 2 or len(
                    {right for _, right in pairs}
                ) < 2:
                    continue
                correlation = _spearman(
                    [left for left, _ in pairs],
                    [right for _, right in pairs],
                )
                if correlation is not None:
                    correlations.append(
                        {
                            "feature": feature,
                            "target_label": target,
                            "cases": len(pairs),
                            "spearman_rank_correlation": correlation,
                        }
                    )
        correlations.sort(
            key=lambda row: abs(row["spearman_rank_correlation"]),
            reverse=True,
        )
        strongest_by_target = {
            target: [
                row for row in correlations if row["target_label"] == target
            ][:10]
            for target in targets
        }
        result[slice_name] = {
            "records": len(rows),
            "future_positive_records": sum(
                row["labels"]["future_improvement_positive"] for row in rows
            ),
            "strongest_univariate_rank_diagnostics": correlations[:20],
            "strongest_by_target": strongest_by_target,
        }
    return result


def _opportunity_distribution(
    grouped: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    headrooms = [
        _number(rows[0]["exact_sum_margin_optimum"], "exact_sum_margin_optimum")
        for rows in grouped.values()
    ]
    ordered = sorted(headrooms, reverse=True)
    total = sum(headrooms)

    def top_share(fraction: float) -> float | None:
        count = max(1, ceil(fraction * len(ordered)))
        return _safe_ratio(sum(ordered[:count]), total)

    return {
        "boundaries": len(headrooms),
        "positive_headroom_boundaries": sum(value > TOLERANCE for value in headrooms),
        "aggregate_exact_sum_margin_headroom": total,
        "mean_exact_sum_margin_headroom": mean(headrooms),
        "median_exact_sum_margin_headroom": median(headrooms),
        "p95_exact_sum_margin_headroom": _percentile(headrooms, 0.95),
        "maximum_exact_sum_margin_headroom": max(headrooms),
        "top_10_percent_headroom_share": top_share(0.10),
        "top_25_percent_headroom_share": top_share(0.25),
        "top_50_percent_headroom_share": top_share(0.50),
    }


def _phase_distribution(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    keys = sorted({(row["phase"], row["update"]) for row in records})
    result = []
    for phase, update in keys:
        rows = [
            row
            for row in records
            if row["phase"] == phase and row["update"] == update
        ]
        next_costs = [
            row["labels"]["next_candidate_cost_milliseconds"]
            for row in rows
            if row["labels"]["next_candidate_cost_milliseconds"] is not None
        ]
        next_gains = [row["labels"]["next_candidate_gain"] for row in rows]
        steps_to_gain = [
            row["labels"]["candidate_steps_to_first_improvement"]
            for row in rows
            if row["labels"]["candidate_steps_to_first_improvement"] is not None
        ]
        costs_to_gain = [
            row["labels"]["cost_to_first_improvement_milliseconds"]
            for row in rows
            if row["labels"]["cost_to_first_improvement_milliseconds"] is not None
        ]
        future_positive = sum(
            row["labels"]["future_improvement_positive"] for row in rows
        )
        next_positive = sum(gain > TOLERANCE for gain in next_gains)
        result.append(
            {
                "phase": phase,
                "update": update,
                "records": len(rows),
                "future_positive_records": future_positive,
                "next_candidate_positive_records": next_positive,
                "myopic_next_candidate_recall": _safe_ratio(
                    next_positive, future_positive
                ),
                "mean_next_candidate_gain": mean(next_gains),
                "mean_next_candidate_cost_milliseconds": (
                    mean(next_costs) if next_costs else None
                ),
                "mean_candidate_steps_to_first_improvement": (
                    mean(steps_to_gain) if steps_to_gain else None
                ),
                "maximum_candidate_steps_to_first_improvement": (
                    max(steps_to_gain) if steps_to_gain else None
                ),
                "mean_cost_to_first_improvement_milliseconds": (
                    mean(costs_to_gain) if costs_to_gain else None
                ),
            }
        )
    return result


def analyze_opportunity_matrices(
    sources: list[tuple[str, dict[str, Any]]],
    *,
    deadlines_ms: tuple[float, ...] = (5.0, 20.0, 50.0),
    quantum_ms: float = 0.05,
    store_records: bool = True,
) -> dict[str, Any]:
    """Analyze revealed matrices without fitting a scheduler."""

    if not sources:
        raise ValueError("at least one matrix source is required")
    source_names = [name for name, _ in sources]
    if any(not name or ":" in name for name in source_names):
        raise ValueError("source names must be nonempty and cannot contain colons")
    if len(set(source_names)) != len(source_names):
        raise ValueError("source names must be unique")
    if (
        not deadlines_ms
        or any(not isfinite(value) or value <= 0.0 for value in deadlines_ms)
        or len(set(deadlines_ms)) != len(deadlines_ms)
    ):
        raise ValueError("deadlines must be finite, positive, and unique")
    if not isfinite(quantum_ms) or quantum_ms <= 0.0:
        raise ValueError("quantum_ms must be finite and positive")
    grouped: dict[str, list[dict[str, Any]]] = {}
    source_summary = []
    for source_name, matrix in sources:
        source_grouped = _group_source_records(source_name, matrix)
        grouped.update(source_grouped)
        source_summary.append(
            {
                "name": source_name,
                "boundaries": len(source_grouped),
                "update_records": sum(len(rows) for rows in source_grouped.values()),
            }
        )
    records = _trace_records(grouped)
    result = {
        "schema_version": 1,
        "experiment_type": "opportunity_phase_trace_analysis",
        "status": "measurement_only_no_scheduler_fit",
        "sources": source_summary,
        "boundary_count": len(grouped),
        "decision_record_count": len(records),
        "phase_record_counts": {
            phase: sum(row["phase"] == phase for row in records)
            for phase in ("boundary_start", "candidate_ready", "after_pricing")
        },
        "feature_contract": {
            "schema_version": 1,
            "boundary_start": list(START_FEATURE_NAMES),
            "candidate_ready": list(CANDIDATE_FEATURE_NAMES),
            "after_pricing": list(POST_PRICING_FEATURE_NAMES),
            "forbidden_online_name_fragments": list(
                FORBIDDEN_ONLINE_NAME_FRAGMENTS
            ),
            "blueprint_solver_and_iterations_are_metadata_not_features": True,
            "candidate_ready_excludes_current_pricing_output_and_cost": True,
        },
        "label_contract": {
            "fields": list(LABEL_NAMES),
            "exact_and_hidden_fields_are_diagnostic_only": True,
            "future_trace_fields_are_training_oracle_labels_only": True,
        },
        "opportunity_distribution": _opportunity_distribution(grouped),
        "phase_distribution": _phase_distribution(records),
        "unfitted_signal_diagnostics": _signal_diagnostics(records),
        "allocation_oracles": _allocation_oracles(
            grouped, deadlines_ms, quantum_ms
        ),
        "blueprint_regime_allocation": _regime_allocation_oracles(
            grouped, deadlines_ms, quantum_ms
        ),
        "allocation_protocol": {
            "independent_phase_fit": (
                "perfectly knows realized candidate completion times within each "
                "hard per-boundary deadline"
            ),
            "pooled_perfect_information": (
                "multiple-choice allocation across boundaries with exact future "
                "quality; models an optimistic shared/speculative compute pool"
            ),
            "preferred_pool_scope": (
                "blueprint_regime_allocation; cross-regime pooling is a looser "
                "benchmark diagnostic and not a deployment claim"
            ),
            "pooled_quantization": (
                "round-up costs give a feasible conservative value; round-down "
                "costs give an optimistic upper value"
            ),
            "uniform_checkpoint": (
                "one update count for every boundary under aggregate compute; "
                "early convergence pays the pricing used to detect convergence"
            ),
            "not_deployable": True,
        },
    }
    if store_records:
        result["records"] = records
    return result


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def _load_configured_sources(
    config: dict[str, Any],
    config_path: Path,
) -> tuple[list[tuple[str, dict[str, Any]]], list[dict[str, Any]]]:
    raw_sources = config.get("sources")
    if not isinstance(raw_sources, list) or not raw_sources:
        raise ValueError("config sources must be a nonempty list")
    sources = []
    provenance = []
    for item in raw_sources:
        if not isinstance(item, dict) or set(item) != {"name", "path"}:
            raise ValueError("each source must contain exactly name and path")
        path = Path(str(item["path"]))
        if not path.is_absolute():
            path = config_path.parent / path
        raw = path.read_bytes()
        sources.append((str(item["name"]), json.loads(raw)))
        provenance.append(
            {
                "name": str(item["name"]),
                "path": str(path.resolve()),
                "sha256": hashlib.sha256(raw).hexdigest(),
            }
        )
    return sources, provenance


def main() -> None:
    args = _parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    sources, provenance = _load_configured_sources(config, args.config)
    deadlines = tuple(
        float(value)
        for value in config.get("deadline_milliseconds", [5, 20, 50])
    )
    result = analyze_opportunity_matrices(
        sources,
        deadlines_ms=deadlines,
        quantum_ms=float(config.get("pool_quantum_milliseconds", 0.05)),
        store_records=bool(config.get("store_records", True)),
    )
    result["source_provenance"] = provenance
    rendered = json.dumps(result, indent=2, sort_keys=True, allow_nan=False)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(
        "opportunity trace: "
        f"boundaries={result['boundary_count']}, "
        f"decisions={result['decision_record_count']}, "
        f"status={result['status']}"
    )
    if args.output is not None:
        print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
