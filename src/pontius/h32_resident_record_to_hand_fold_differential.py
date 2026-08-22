"""Label-free h32 placement differential for the resident record-to-hand fold."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import gc
import hashlib
import json
import math
from pathlib import Path
import statistics
import subprocess
import time
from typing import Any, Mapping, Sequence

from . import h32_tier_b_opponent_batch_differential as batch_v1
from . import h32_tier_b_opponent_batch_differential_v2 as batch_v2
from .cupy_sparse_incidence import release_cupy_memory_pool
from .device_fold_resident_leaf_adjoint_cfr import (
    DeviceFoldResidentLeafAdjointPublicTreeCFR,
)
from .device_fold_selector_stable_affine_response import (
    evaluate_device_fold_batched_selector_stable_affine_opponents,
    evaluate_device_fold_selector_stable_affine_leaf_adjoint_seat,
)
from .h32_fresh_union_value_audit import _memory_snapshot
from .reporting import environment_metadata
from .resident_record_to_hand_fold import RecordToHandBackend
from .selector_stable_affine_response import (
    certify_selector_stable_affine_envelope,
)


_ROOT = Path(__file__).parents[2]
_CONFIG = _ROOT / "experiments/configs/h32-resident-record-to-hand-fold-v1.json"
_OUTPUT = _ROOT / "experiments/results/h32-resident-record-to-hand-fold-v1.json"
_SOURCE_RESULT = batch_v1.science._SOURCE
_BATCH_RESULT = _ROOT / "experiments/results/h32-tier-b-opponent-batch-v2.json"
_BATCH_DECISION = (
    _ROOT
    / "docs/decisions"
    / "ADR-0210-six-way-tier-b-batching-is-exact-but-does-not-reduce-resident-contraction-work.md"
)
_FOLD_IMPLEMENTATION = _ROOT / "src/pontius/resident_record_to_hand_fold.py"
_CONTRACTION_IMPLEMENTATION = (
    _ROOT / "src/pontius/device_fold_resident_heterogeneous_leaf_contraction.py"
)
_CFR_IMPLEMENTATION = _ROOT / "src/pontius/device_fold_resident_leaf_adjoint_cfr.py"
_AFFINE_IMPLEMENTATION = (
    _ROOT / "src/pontius/device_fold_selector_stable_affine_response.py"
)
_REDUCED_TEST = _ROOT / "tests/test_device_fold_resident_paths.py"
_IMPLEMENTATION = Path(__file__)
_TEST = _ROOT / "tests/test_h32_resident_record_to_hand_fold_differential.py"
_NCU = Path(
    "C:/Program Files/NVIDIA Corporation/Nsight Compute 2026.2.1/"
    "target/windows-desktop-win7-x64/ncu.exe"
)

_PATHS = {
    "expected_source_result_sha256": _SOURCE_RESULT,
    "expected_batch_result_sha256": _BATCH_RESULT,
    "expected_batch_decision_sha256": _BATCH_DECISION,
    "expected_batch_v2_config_sha256": batch_v2._CONFIG,
    "expected_batch_v2_implementation_sha256": batch_v2._IMPLEMENTATION,
    "expected_fold_implementation_sha256": _FOLD_IMPLEMENTATION,
    "expected_contraction_implementation_sha256": _CONTRACTION_IMPLEMENTATION,
    "expected_cfr_implementation_sha256": _CFR_IMPLEMENTATION,
    "expected_affine_implementation_sha256": _AFFINE_IMPLEMENTATION,
    "expected_reduced_control_test_sha256": _REDUCED_TEST,
    "expected_audit_implementation_sha256": _IMPLEMENTATION,
    "expected_audit_control_test_sha256": _TEST,
}

_WARM_ARMS = ("host_fold", "device_fold")
_TIER_CELLS = (
    "host_scalar",
    "host_batch",
    "device_scalar",
    "device_batch",
)


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required resident-fold input is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_h32_resident_record_to_hand_fold_config(
    config: dict[str, Any],
) -> dict[str, Any]:
    """Validate the frozen two-customer, four-cell placement differential."""

    fields = {
        "evidence_stage",
        *_PATHS,
        "target_scope",
        "candidate_scope",
        "warm_step_arms",
        "tier_b_cells",
        "placement_intervention",
        "timing_warmups_per_arm",
        "warm_step_schedule",
        "tier_b_schedule",
        "global_tier_b_choice_rule",
        "complete_ledger_rule",
        "street_budget_ms",
        "emission_reserve_ms",
        "minimum_prework_physical_free_bytes",
        "maximum_feature_width_per_batch",
        "minimum_material_speedup",
        "maximum_target_regression_ratio",
        "h3_device_batch_speedup_threshold",
        "h3_interaction_ratio_threshold",
        "profiler_rule",
        "outcome_policy",
        "gates",
    }
    if set(config) != fields:
        raise ValueError("resident-fold config fields differ from ADR-0211")
    frozen = {
        "evidence_stage": (
            "preregistered_after_adr0210_before_any_h32_device_fold_"
            "placement_or_timing_measurement"
        ),
        "target_scope": "all_six_retained_adr0186_contexts_without_label_load",
        "candidate_scope": (
            "the_same_six_regret_vertex_public_node_blocks_per_context_"
            "reconstructed_by_the_adr0209_path"
        ),
        "warm_step_arms": list(_WARM_ARMS),
        "tier_b_cells": list(_TIER_CELLS),
        "placement_intervention": (
            "all_new_cells_share_one_additive_resident_pipeline_and_change_"
            "only_record_to_hand_fold_placement_host_numpy_or_gpu_cupy"
        ),
        "timing_warmups_per_arm": 1,
        "warm_step_schedule": [
            ["host_fold", "device_fold"],
            ["device_fold", "host_fold"],
            ["host_fold", "device_fold"],
        ],
        "tier_b_schedule": [
            ["host_scalar", "host_batch", "device_scalar", "device_batch"],
            ["device_batch", "device_scalar", "host_batch", "host_scalar"],
            ["host_batch", "device_batch", "host_scalar", "device_scalar"],
        ],
        "global_tier_b_choice_rule": (
            "choose_one_device_cell_for_all_contexts_by_lower_pooled_"
            "measured_wall_median_with_device_scalar_on_exact_tie"
        ),
        "complete_ledger_rule": (
            "replace_the_search_step_with_the_device_fold_warm_median_and_"
            "tier_b_with_the_globally_chosen_device_cell_then_charge_endpoint_"
            "construction_own_rows_winner_envelope_and_one_second_emission"
        ),
        "street_budget_ms": 15000.0,
        "emission_reserve_ms": 1000.0,
        "minimum_prework_physical_free_bytes": 5_184_456_164,
        "maximum_feature_width_per_batch": 384,
        "minimum_material_speedup": 1.05,
        "maximum_target_regression_ratio": 1.02,
        "h3_device_batch_speedup_threshold": 1.10,
        "h3_interaction_ratio_threshold": 1.08,
        "profiler_rule": (
            "hardware_counters_are_forbidden_in_paired_timing_record_ncu_"
            "availability_only_and_run_any_counter_profile_later_as_a_"
            "separate_non_gating_artifact"
        ),
        "outcome_policy": (
            "validity_is_provenance_numerical_structural_memory_and_accounting_"
            "only_speed_h3_full_set_fit_and_promotion_are_preregistered_"
            "report_or_decision_branches_not_retroactive_validity_gates"
        ),
    }
    if any(config[key] != value for key, value in frozen.items()):
        raise ValueError("resident-fold workload differs from ADR-0211")
    expected_gates = {
        "expected_targets": 6,
        "expected_candidates_per_target": 6,
        "expected_warm_samples_per_arm": 3,
        "expected_tier_samples_per_cell": 3,
        "expected_opponent_rows_per_tier_cell": 30,
        "expected_scalar_calls_per_cell": 30,
        "expected_batch_calls_per_cell": 6,
        "maximum_affine_numeric_error": 2e-11,
        "maximum_composite_error": 2e-11,
        "maximum_warm_regret_error": 1e-12,
        "maximum_warm_strategy_sum_error": 1e-12,
        "maximum_warm_policy_probability_error": 1e-12,
        "maximum_warm_policy_mean_total_variation": 1e-13,
        "maximum_arm_wall_ms": 60000.0,
        "maximum_gpu_pool_bytes": 12_000_000_000,
        "minimum_postwork_physical_free_bytes": 1_000_000_000,
        "maximum_total_audit_seconds": 2400.0,
        "require_clean_git_state": True,
        "require_source_parent_passed": True,
        "require_source_checkpoint_identity": True,
        "require_target_identity": True,
        "require_blueprint_identity": True,
        "require_structural_identity": True,
        "require_fold_placement_accounting": True,
        "require_device_transfer_reduction": True,
        "require_safe_preflight": True,
        "require_blueprint_emission": True,
        "require_finite": True,
        "require_strategy_population_claim_null": True,
    }
    if config["gates"] != expected_gates:
        raise ValueError("resident-fold gates differ from ADR-0211")
    for field, path in _PATHS.items():
        if config[field] != _sha256(path):
            raise ValueError(f"resident-fold source mismatch: {field}")

    v2_config = json.loads(batch_v2._CONFIG.read_text(encoding="utf-8"))
    corrected = batch_v2.parse_h32_tier_b_opponent_batch_v2_config(v2_config)
    base = corrected["base"]
    if config["maximum_feature_width_per_batch"] != base["live"][
        "maximum_feature_width_per_batch"
    ]:
        raise ValueError("resident-fold feature width differs from live source")
    return {**config, "base": base}


def choose_global_device_tier_cell(
    timing_rows: Sequence[Mapping[str, Any]],
) -> str:
    """Choose one label-free device topology from pooled measured wall time."""

    medians = {}
    for cell in ("device_scalar", "device_batch"):
        samples = [float(row["wall_ms"]) for row in timing_rows if row["cell"] == cell]
        if not samples:
            raise ValueError(f"resident-fold timing lacks {cell}")
        medians[cell] = statistics.median(samples)
    if medians["device_scalar"] <= medians["device_batch"]:
        return "device_scalar"
    return "device_batch"


def _finite_tree(value: Any) -> bool:
    if value is None or isinstance(value, (str, bool)):
        return True
    if isinstance(value, (int, float)):
        return math.isfinite(float(value))
    if isinstance(value, Mapping):
        return all(_finite_tree(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return all(_finite_tree(item) for item in value)
    return True


def _table_difference(
    expected: Mapping[str, Mapping[str, float]],
    actual: Mapping[str, Mapping[str, float]],
) -> dict[str, Any]:
    structural = expected.keys() == actual.keys() and all(
        expected[key].keys() == actual[key].keys() for key in expected.keys() & actual.keys()
    )
    if not structural:
        return {"structural_identity": False, "maximum_error": math.inf}
    maximum = max(
        (
            abs(float(actual[key][action]) - float(expected[key][action]))
            for key in expected
            for action in expected[key]
        ),
        default=0.0,
    )
    return {"structural_identity": True, "maximum_error": maximum}


def _source_blueprint(
    source_parent: Mapping[str, Any],
    target_spec: Mapping[str, Any],
) -> dict[str, dict[str, float]]:
    source_row = next(
        row
        for row in source_parent["source_rows"]
        if row["source"]
        == f"{target_spec['board_id']}/{target_spec['range_family']}"
    )
    return batch_v1.science._average_policy_from_state(source_row["final_checkpoint"])


def _new_placed_solver(
    objects: Mapping[str, Any],
    blueprint: dict[str, dict[str, float]],
    *,
    backend: RecordToHandBackend,
    live: Mapping[str, Any],
) -> DeviceFoldResidentLeafAdjointPublicTreeCFR:
    solver = DeviceFoldResidentLeafAdjointPublicTreeCFR(
        objects["layout"],
        objects["workspace"],
        objects["sparse"],
        objects["automata"],
        str(live["solver_variant"]),
        belief_cache=objects["context"].belief_cache,
        automaton_caches=objects["shared"].automaton_caches,
        cupy_sparse=objects["gpu"],
        maximum_feature_width_per_batch=int(live["maximum_feature_width_per_batch"]),
        hands_by_player=objects["belief"].hands_by_player,
        record_to_hand_backend=backend,
    )
    warm_mass = float(live["warm_regret_mass_payoff_fraction"]) * float(
        objects["layout"].game.payoff_span
    )
    solver.warm_start(blueprint, warm_mass)
    return solver


def _sum_work_field(works: Sequence[Any], field: str) -> float:
    return math.fsum(float(getattr(work, field, 0.0)) for work in works)


def _work_ledger(works: Sequence[Any]) -> dict[str, Any]:
    if not works:
        return {
            "contraction_work_rows": 0,
            "factor_prepare_ms": 0.0,
            "factor_upload_ms": 0.0,
            "product_generation_gpu_ms": 0.0,
            "resident_pipeline_gpu_ms": 0.0,
            "device_hand_fold_gpu_ms": 0.0,
            "device_to_host_ms": 0.0,
            "host_hand_fold_ms": 0.0,
            "host_hand_finalize_ms": 0.0,
            "per_call_host_to_device_bytes": 0,
            "per_call_device_to_host_bytes": 0,
            "total_feature_width": 0,
            "sparse_batches": 0,
            "feature_width_fill_ratio": 0.0,
            "maximum_gpu_pool_total_bytes": 0,
        }
    total_width = sum(int(work.total_feature_width) for work in works)
    batches = sum(int(work.batches) for work in works)
    maximum_width = max(int(work.maximum_batch_feature_width) for work in works)
    return {
        "contraction_work_rows": len(works),
        "factor_prepare_ms": _sum_work_field(works, "factor_prepare_ms"),
        "factor_upload_ms": _sum_work_field(works, "factor_upload_ms"),
        "product_generation_gpu_ms": _sum_work_field(
            works, "product_generation_gpu_ms"
        ),
        "resident_pipeline_gpu_ms": _sum_work_field(
            works, "resident_pipeline_gpu_ms"
        ),
        "device_hand_fold_gpu_ms": _sum_work_field(
            works, "device_hand_fold_gpu_ms"
        ),
        "device_to_host_ms": _sum_work_field(works, "device_to_host_ms"),
        "host_hand_fold_ms": _sum_work_field(works, "host_hand_fold_ms"),
        "host_hand_finalize_ms": _sum_work_field(
            works, "host_hand_finalize_ms"
        ),
        "per_call_host_to_device_bytes": sum(
            int(work.per_call_host_to_device_bytes) for work in works
        ),
        "per_call_device_to_host_bytes": sum(
            int(work.per_call_device_to_host_bytes) for work in works
        ),
        "total_feature_width": total_width,
        "sparse_batches": batches,
        "maximum_batch_feature_width": maximum_width,
        "feature_width_fill_ratio": (
            total_width / (batches * 384) if batches else 0.0
        ),
        "maximum_gpu_pool_total_bytes": max(
            int(work.maximum_gpu_pool_total_bytes) for work in works
        ),
    }


def _run_warm_step(
    objects: Mapping[str, Any],
    blueprint: dict[str, dict[str, float]],
    *,
    arm: str,
    live: Mapping[str, Any],
    cp: Any,
) -> tuple[DeviceFoldResidentLeafAdjointPublicTreeCFR, dict[str, Any]]:
    backend: RecordToHandBackend = "host_numpy" if arm == "host_fold" else "gpu_cupy"
    solver = _new_placed_solver(objects, blueprint, backend=backend, live=live)
    cp.cuda.runtime.deviceSynchronize()
    started = time.perf_counter()
    solver.step()
    cp.cuda.runtime.deviceSynchronize()
    wall_ms = (time.perf_counter() - started) * 1000.0
    if solver.last_step_work is None:
        raise AssertionError("resident-fold warm step emitted no work ledger")
    works = [row.resident_work for row in solver.last_step_work.traversers]
    return solver, {
        "wall_ms": wall_ms,
        "traversers": len(works),
        "terminal_contraction_ms": solver.last_step_work.terminal_contraction_ms,
        **_work_ledger(works),
    }


def _warm_identity(expected: Any, actual: Any) -> dict[str, Any]:
    regret = _table_difference(expected.regret_table(), actual.regret_table())
    strategy_sum = _table_difference(
        expected.strategy_sum_table(), actual.strategy_sum_table()
    )
    policy = batch_v1.science._policy_distance(
        expected.current_strategy(), actual.current_strategy()
    )
    return {
        "regret_structural_identity": regret["structural_identity"],
        "maximum_regret_error": regret["maximum_error"],
        "strategy_sum_structural_identity": strategy_sum["structural_identity"],
        "maximum_strategy_sum_error": strategy_sum["maximum_error"],
        "maximum_policy_probability_error": policy["maximum_probability_error"],
        "mean_policy_total_variation": policy["mean_total_variation"],
        "iteration_identity": expected.iteration == actual.iteration,
    }


def _run_tier_cell(
    *,
    cell: str,
    endpoints: Sequence[Any],
    acting_players: Sequence[int],
    context: Any,
    shared: Any,
    gpu: Any,
    live: Mapping[str, Any],
    cp: Any,
) -> tuple[list[list[Any | None]], dict[str, Any]]:
    backend: RecordToHandBackend = (
        "host_numpy" if cell.startswith("host_") else "gpu_cupy"
    )
    batched = cell.endswith("_batch")
    cp.cuda.runtime.deviceSynchronize()
    started = time.perf_counter()
    rows: list[list[Any | None]] = [
        [None] * len(context.response_caches) for _ in endpoints
    ]
    works = []
    calls = 0
    affected = 0
    reverse_ms = 0.0
    term_prepare_ms = 0.0
    if not batched:
        for candidate_index, (endpoint, acting_player) in enumerate(
            zip(endpoints, acting_players, strict=True)
        ):
            for target_player, cache in enumerate(context.response_caches):
                if target_player == acting_player:
                    continue
                measured = evaluate_device_fold_selector_stable_affine_leaf_adjoint_seat(
                    cache,
                    endpoint,
                    acting_player=acting_player,
                    selector_margin_allowance=float(live["selector_margin_allowance"]),
                    maximum_feature_width_per_batch=int(
                        live["maximum_feature_width_per_batch"]
                    ),
                    belief_cache=context.belief_cache,
                    automaton_cache=shared.automaton_caches[target_player],
                    cupy_sparse=gpu,
                    record_to_hand_backend=backend,
                )
                rows[candidate_index][target_player] = measured.semantic
                if measured.work is not None:
                    works.append(measured.work)
                calls += 1
                affected += int(measured.semantic.affected_terminal_contractions)
                reverse_ms += float(measured.semantic.reverse_evaluation_ms)
    else:
        for target_player, cache in enumerate(context.response_caches):
            candidate_indices = [
                index
                for index, acting_player in enumerate(acting_players)
                if acting_player != target_player
            ]
            measured = evaluate_device_fold_batched_selector_stable_affine_opponents(
                cache,
                tuple(endpoints[index] for index in candidate_indices),
                acting_players=tuple(acting_players[index] for index in candidate_indices),
                selector_margin_allowance=float(live["selector_margin_allowance"]),
                maximum_feature_width_per_batch=int(
                    live["maximum_feature_width_per_batch"]
                ),
                belief_cache=context.belief_cache,
                automaton_cache=shared.automaton_caches[target_player],
                cupy_sparse=gpu,
                record_to_hand_backend=backend,
            )
            if measured.work.contraction is not None:
                works.append(measured.work.contraction)
            calls += measured.work.contraction_calls
            affected += measured.work.affected_terminal_contractions
            reverse_ms += measured.work.reverse_evaluation_ms
            term_prepare_ms += measured.work.term_prepare_ms
            for candidate_index, row in zip(
                candidate_indices, measured.seat_results, strict=True
            ):
                rows[candidate_index][target_player] = row
    cp.cuda.runtime.deviceSynchronize()
    return rows, {
        "wall_ms": (time.perf_counter() - started) * 1000.0,
        "opponent_rows": len(endpoints) * 5,
        "scalar_calls": calls if not batched else 0,
        "batch_calls": calls if batched else 0,
        "affected_terminal_contractions": affected,
        "term_prepare_ms": term_prepare_ms,
        "reverse_evaluation_ms": reverse_ms,
        **_work_ledger(works),
    }


def _affine_identity(
    teacher: Sequence[Sequence[Any | None]],
    actual: Sequence[Sequence[Any | None]],
    *,
    acting_players: Sequence[int],
    own_rows: Sequence[Any],
    blueprint_gains: Sequence[float],
    live: Mapping[str, Any],
) -> dict[str, Any]:
    comparisons = []
    composite_errors = []
    raw_guard = float(live["acceptance_guard_normalized"]) * float(live["stack"])
    for candidate_index, acting_player in enumerate(acting_players):
        teacher_full = list(teacher[candidate_index])
        actual_full = list(actual[candidate_index])
        teacher_full[acting_player] = own_rows[candidate_index]
        actual_full[acting_player] = own_rows[candidate_index]
        for target_player in range(6):
            if target_player == acting_player:
                continue
            comparisons.append(
                batch_v1.affine_semantic_difference(
                    teacher_full[target_player], actual_full[target_player]
                )
            )
        teacher_tier = batch_v1.science.affine_tier_features(
            teacher_full,
            acting_seat=acting_player,
            raw_guard=raw_guard,
            numerical_allowance=float(live["envelope_numerical_allowance"]),
            blueprint_deviation_gains=tuple(blueprint_gains),
        )
        actual_tier = batch_v1.science.affine_tier_features(
            actual_full,
            acting_seat=acting_player,
            raw_guard=raw_guard,
            numerical_allowance=float(live["envelope_numerical_allowance"]),
            blueprint_deviation_gains=tuple(blueprint_gains),
        )
        composite_errors.append(
            abs(
                float(
                    teacher_tier["features"]["tier_b_slope_predicted_value"]
                )
                - float(actual_tier["features"]["tier_b_slope_predicted_value"])
            )
        )
    return {
        "opponent_rows_compared": len(comparisons),
        "maximum_numeric_error": max(
            row["maximum_numeric_error"] for row in comparisons
        ),
        "structural_identity": all(
            row["structural_identity"] for row in comparisons
        ),
        "maximum_composite_error": max(composite_errors, default=0.0),
    }


def _rank_and_certify_without_emission(
    rows: Sequence[Sequence[Any | None]],
    *,
    acting_players: Sequence[int],
    own_rows: Sequence[Any],
    endpoint_rows: Sequence[Mapping[str, Any]],
    blueprint_quality: Mapping[str, Any],
    live: Mapping[str, Any],
) -> tuple[dict[str, Any], float]:
    started = time.perf_counter()
    blueprint_gains = tuple(float(value) for value in blueprint_quality["deviation_gains"])
    raw_guard = float(live["acceptance_guard_normalized"]) * float(live["stack"])
    full_rows = []
    features = []
    for candidate_index, acting_player in enumerate(acting_players):
        candidate = list(rows[candidate_index])
        candidate[acting_player] = own_rows[candidate_index]
        full_rows.append(tuple(candidate))
        tier = batch_v1.science.affine_tier_features(
            candidate,
            acting_seat=acting_player,
            raw_guard=raw_guard,
            numerical_allowance=float(live["envelope_numerical_allowance"]),
            blueprint_deviation_gains=blueprint_gains,
        )
        features.append(
            {
                **endpoint_rows[candidate_index],
                "tier_b_slope_predicted_value": float(
                    tier["features"]["tier_b_slope_predicted_value"]
                ),
            }
        )
    winner = min(
        range(len(features)),
        key=lambda index: (
            -features[index]["tier_b_slope_predicted_value"],
            features[index]["acting_player"],
            features[index]["public_history"],
        ),
    )
    envelope = certify_selector_stable_affine_envelope(
        full_rows[winner],
        blueprint_deviation_gains=blueprint_gains,
        blueprint_nash_conv=float(blueprint_quality["nash_conv"]),
        raw_guard=raw_guard,
        scale_grid=tuple(
            2.0**-index
            for index in range(34)
            if 2.0**-index >= float(live["numerical_floor"])
        ),
        safety_fraction=float(live["safety_fraction"]),
        numerical_allowance=float(live["envelope_numerical_allowance"]),
    )
    return (
        {
            "candidate_index": winner,
            "acting_player": acting_players[winner],
            "public_history": endpoint_rows[winner]["public_history"],
            "envelope_complete": bool(envelope.complete),
            "envelope_stop_reason": str(envelope.stop_reason),
            "selected_scale_diagnostic": envelope.selected_scale,
            "positive_certified_value_diagnostic": float(
                envelope.positive_certified_value
            ),
        },
        (time.perf_counter() - started) * 1000.0,
    )


def _run_target(
    parsed: Mapping[str, Any],
    source_parent: Mapping[str, Any],
    target_spec: Mapping[str, Any],
    cp: Any,
) -> dict[str, Any]:
    base = parsed["base"]
    live = base["live"]
    objects, result = batch_v1._prepare_target(base, source_parent, target_spec, cp)
    result["memory_rows"] = list(result["memory_rows"])
    if not result["batch_safe_preflight"]:
        result["status"] = "stopped_before_placement_work_for_physical_headroom"
        del objects
        gc.collect()
        release_cupy_memory_pool()
        return result

    blueprint = _source_blueprint(source_parent, target_spec)
    expected_solver = objects["solver"]
    endpoints = objects["endpoints"]
    acting_players = objects["acting_players"]
    context = objects["context"]
    shared = objects["shared"]
    gpu = objects["gpu"]

    teacher_rows, teacher_timing = batch_v1._run_scalar_opponents(
        endpoints=endpoints,
        acting_players=acting_players,
        context=context,
        shared=shared,
        gpu=gpu,
        live=live,
        cp=cp,
    )

    for arm in _WARM_ARMS:
        for _ in range(int(parsed["timing_warmups_per_arm"])):
            release_cupy_memory_pool()
            solver, _ = _run_warm_step(
                objects, blueprint, arm=arm, live=live, cp=cp
            )
            del solver
            gc.collect()

    warm_timing_rows = []
    warm_identity_rows = []
    for repetition, schedule in enumerate(parsed["warm_step_schedule"], start=1):
        for arm in schedule:
            release_cupy_memory_pool()
            result["memory_rows"].append(_memory_snapshot(cp))
            solver, timing = _run_warm_step(
                objects, blueprint, arm=arm, live=live, cp=cp
            )
            result["memory_rows"].append(_memory_snapshot(cp))
            warm_timing_rows.append({"repetition": repetition, "arm": arm, **timing})
            warm_identity_rows.append(
                {
                    "repetition": repetition,
                    "arm": arm,
                    **_warm_identity(expected_solver, solver),
                }
            )
            del solver
            gc.collect()

    for cell in _TIER_CELLS:
        for _ in range(int(parsed["timing_warmups_per_arm"])):
            release_cupy_memory_pool()
            rows, _ = _run_tier_cell(
                cell=cell,
                endpoints=endpoints,
                acting_players=acting_players,
                context=context,
                shared=shared,
                gpu=gpu,
                live=live,
                cp=cp,
            )
            del rows
            gc.collect()

    tier_timing_rows = []
    tier_identity_rows = []
    reference_by_cell: dict[str, list[list[Any | None]]] = {}
    blueprint_gains = tuple(
        float(value) for value in result["blueprint_quality"]["deviation_gains"]
    )
    for repetition, schedule in enumerate(parsed["tier_b_schedule"], start=1):
        for cell in schedule:
            release_cupy_memory_pool()
            result["memory_rows"].append(_memory_snapshot(cp))
            rows, timing = _run_tier_cell(
                cell=cell,
                endpoints=endpoints,
                acting_players=acting_players,
                context=context,
                shared=shared,
                gpu=gpu,
                live=live,
                cp=cp,
            )
            result["memory_rows"].append(_memory_snapshot(cp))
            tier_timing_rows.append(
                {"repetition": repetition, "cell": cell, **timing}
            )
            tier_identity_rows.append(
                {
                    "repetition": repetition,
                    "cell": cell,
                    **_affine_identity(
                        teacher_rows,
                        rows,
                        acting_players=acting_players,
                        own_rows=objects["own_rows"],
                        blueprint_gains=blueprint_gains,
                        live=live,
                    ),
                }
            )
            reference_by_cell[cell] = rows

    winner, ranking_ms = _rank_and_certify_without_emission(
        reference_by_cell["device_scalar"],
        acting_players=acting_players,
        own_rows=objects["own_rows"],
        endpoint_rows=result["endpoint_rows"],
        blueprint_quality=result["blueprint_quality"],
        live=live,
    )
    warm_summary = {
        arm: statistics.median(
            row["wall_ms"] for row in warm_timing_rows if row["arm"] == arm
        )
        for arm in _WARM_ARMS
    }
    tier_summary = {
        cell: statistics.median(
            row["wall_ms"] for row in tier_timing_rows if row["cell"] == cell
        )
        for cell in _TIER_CELLS
    }
    result.update(
        {
            "status": "completed",
            "accepted_scalar_teacher_timing_diagnostic": teacher_timing,
            "warm_timing_rows": warm_timing_rows,
            "warm_identity_rows": warm_identity_rows,
            "tier_timing_rows": tier_timing_rows,
            "tier_identity_rows": tier_identity_rows,
            "warm_median_ms": warm_summary,
            "tier_median_ms": tier_summary,
            "warm_device_speedup": (
                warm_summary["host_fold"] / warm_summary["device_fold"]
            ),
            "host_batch_speedup": (
                tier_summary["host_scalar"] / tier_summary["host_batch"]
            ),
            "device_batch_speedup": (
                tier_summary["device_scalar"] / tier_summary["device_batch"]
            ),
            "batch_placement_interaction_ratio": (
                (tier_summary["device_scalar"] / tier_summary["device_batch"])
                / (tier_summary["host_scalar"] / tier_summary["host_batch"])
            ),
            "winner_without_label_join_or_emission": winner,
            "ranking_and_winner_envelope_ms": ranking_ms,
            "device_transfer_reduction": all(
                max(
                    timing["per_call_device_to_host_bytes"]
                    for timing in tier_timing_rows
                    if timing["cell"] == f"device_{topology}"
                )
                < min(
                    timing["per_call_device_to_host_bytes"]
                    for timing in tier_timing_rows
                    if timing["cell"] == f"host_{topology}"
                )
                for topology in ("scalar", "batch")
            )
            and max(
                timing["per_call_device_to_host_bytes"]
                for timing in warm_timing_rows
                if timing["arm"] == "device_fold"
            )
            < min(
                timing["per_call_device_to_host_bytes"]
                for timing in warm_timing_rows
                if timing["arm"] == "host_fold"
            ),
        }
    )

    del teacher_rows, reference_by_cell, objects
    gc.collect()
    release_cupy_memory_pool()
    return result


def _ncu_metadata() -> dict[str, Any]:
    metadata = {"path": str(_NCU), "available": _NCU.is_file(), "version": None}
    if not metadata["available"]:
        return metadata
    try:
        completed = subprocess.run(
            [str(_NCU), "--version"],
            capture_output=True,
            check=False,
            text=True,
            timeout=10.0,
        )
        text = " ".join((completed.stdout + " " + completed.stderr).split())
        metadata["version"] = text or None
    except (OSError, subprocess.SubprocessError):
        pass
    return metadata


def run_h32_resident_record_to_hand_fold_differential(
    config_path: Path = _CONFIG,
    output_path: Path = _OUTPUT,
) -> dict[str, Any]:
    """Execute the frozen host/device placement differential once."""

    started = time.perf_counter()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    parsed = parse_h32_resident_record_to_hand_fold_config(config)
    source_parent = json.loads(_SOURCE_RESULT.read_text(encoding="utf-8"))
    if set(source_parent) != batch_v2._SOURCE_SCHEMA:
        raise ValueError("resident-fold source schema differs")
    git = batch_v1._strict_git_metadata()
    cp, runtime = batch_v1._validate_runtime(parsed["base"]["live"])
    if git["dirty"]:
        raise RuntimeError("resident-fold differential requires clean Git state")
    if not bool(source_parent["passed"]):
        raise ValueError("resident-fold source parent did not pass")

    target_rows = []
    for target_spec in parsed["base"]["live"]["targets"]:
        print(f"resident record fold: {target_spec['target']}", flush=True)
        row = _run_target(parsed, source_parent, target_spec, cp)
        target_rows.append(row)
        if not row["batch_safe_preflight"]:
            break

    total_seconds = time.perf_counter() - started
    completed = [row for row in target_rows if row["status"] == "completed"]
    all_warm = [timing for row in completed for timing in row["warm_timing_rows"]]
    all_tier = [timing for row in completed for timing in row["tier_timing_rows"]]
    all_warm_identity = [
        identity for row in completed for identity in row["warm_identity_rows"]
    ]
    all_tier_identity = [
        identity for row in completed for identity in row["tier_identity_rows"]
    ]
    global_cell = choose_global_device_tier_cell(all_tier) if completed else None

    ledgers = []
    linear_k_estimates = []
    if global_cell is not None:
        for row in completed:
            tier_ms = float(row["tier_median_ms"][global_cell])
            warm_ms = float(row["warm_median_ms"]["device_fold"])
            ledger = batch_v1.complete_six_block_ledger(
                search_step_ms=warm_ms,
                endpoint_construction_ms=float(row["endpoint_construction_ms"]),
                own_row_ms=float(row["own_row_ms"]["median"]),
                batched_opponent_ms=tier_ms,
                ranking_and_winner_envelope_ms=float(
                    row["ranking_and_winner_envelope_ms"]
                ),
                emission_reserve_ms=float(parsed["emission_reserve_ms"]),
                street_budget_ms=float(parsed["street_budget_ms"]),
            )
            fixed = (
                warm_ms
                + float(row["ranking_and_winner_envelope_ms"])
                + float(parsed["emission_reserve_ms"])
            )
            six_variable = (
                float(row["endpoint_construction_ms"])
                + float(row["own_row_ms"]["median"])
                + tier_ms
            )
            estimated_k = max(
                0,
                min(
                    6,
                    math.floor(
                        (float(parsed["street_budget_ms"]) - fixed)
                        / (six_variable / 6.0)
                    ),
                ),
            )
            row["globally_selected_device_tier_cell"] = global_cell
            row["repriced_complete_six_block_ledger"] = ledger
            row["linear_current_library_k_estimate_report_only"] = estimated_k
            ledgers.append(ledger)
            linear_k_estimates.append(estimated_k)

    memory_rows = [memory for row in target_rows for memory in row["memory_rows"]]
    maximum_pool = max(
        [int(memory["gpu_pool_total_bytes"]) for memory in memory_rows]
        + [
            int(timing["maximum_gpu_pool_total_bytes"])
            for timing in [*all_warm, *all_tier]
        ],
        default=0,
    )
    minimum_free = min(
        (int(memory["gpu_free_bytes"]) for memory in memory_rows), default=0
    )
    gates_config = parsed["gates"]
    maximum_affine_error = max(
        (row["maximum_numeric_error"] for row in all_tier_identity),
        default=math.inf,
    )
    maximum_composite_error = max(
        (row["maximum_composite_error"] for row in all_tier_identity),
        default=math.inf,
    )
    maximum_regret_error = max(
        (row["maximum_regret_error"] for row in all_warm_identity),
        default=math.inf,
    )
    maximum_sum_error = max(
        (row["maximum_strategy_sum_error"] for row in all_warm_identity),
        default=math.inf,
    )
    maximum_probability_error = max(
        (row["maximum_policy_probability_error"] for row in all_warm_identity),
        default=math.inf,
    )
    maximum_mean_tv = max(
        (row["mean_policy_total_variation"] for row in all_warm_identity),
        default=math.inf,
    )
    host_rows = [
        timing
        for timing in [*all_warm, *all_tier]
        if timing.get("arm") == "host_fold" or str(timing.get("cell", "")).startswith("host_")
    ]
    device_rows = [
        timing
        for timing in [*all_warm, *all_tier]
        if timing.get("arm") == "device_fold"
        or str(timing.get("cell", "")).startswith("device_")
    ]
    fold_accounting = all(
        float(row["device_hand_fold_gpu_ms"]) == 0.0
        and float(row["host_hand_fold_ms"]) > 0.0
        and float(row["host_hand_finalize_ms"]) == 0.0
        for row in host_rows
    ) and all(
        float(row["device_hand_fold_gpu_ms"]) > 0.0
        and float(row["host_hand_fold_ms"]) == 0.0
        and float(row["host_hand_finalize_ms"]) > 0.0
        for row in device_rows
    )
    transfer_reduction = all(
        row["device_transfer_reduction"] for row in completed
    )
    gates = {
        "clean_git": (not git["dirty"]) == gates_config["require_clean_git_state"],
        "source_parent_passed": bool(source_parent["passed"])
        == gates_config["require_source_parent_passed"],
        "target_count": len(completed) == gates_config["expected_targets"],
        "candidate_count": all(
            len(row["endpoint_rows"]) == gates_config["expected_candidates_per_target"]
            for row in completed
        ),
        "warm_sample_count": all(
            sum(timing["arm"] == arm for timing in row["warm_timing_rows"])
            == gates_config["expected_warm_samples_per_arm"]
            for row in completed
            for arm in _WARM_ARMS
        ),
        "tier_sample_count": all(
            sum(timing["cell"] == cell for timing in row["tier_timing_rows"])
            == gates_config["expected_tier_samples_per_cell"]
            for row in completed
            for cell in _TIER_CELLS
        ),
        "opponent_row_count": all(
            timing["opponent_rows"]
            == gates_config["expected_opponent_rows_per_tier_cell"]
            for timing in all_tier
        ),
        "call_count": all(
            (
                timing["scalar_calls"] == gates_config["expected_scalar_calls_per_cell"]
                and timing["batch_calls"] == 0
            )
            if timing["cell"].endswith("_scalar")
            else (
                timing["batch_calls"] == gates_config["expected_batch_calls_per_cell"]
                and timing["scalar_calls"] == 0
            )
            for timing in all_tier
        ),
        "source_checkpoint_identity": all(
            row["source_checkpoint_identity"] for row in target_rows
        )
        == gates_config["require_source_checkpoint_identity"],
        "target_identity": all(row["target_identity"] for row in target_rows)
        == gates_config["require_target_identity"],
        "blueprint_identity": all(row["blueprint_identity"] for row in target_rows)
        == gates_config["require_blueprint_identity"],
        "affine_numeric_identity": maximum_affine_error
        <= gates_config["maximum_affine_numeric_error"],
        "composite_identity": maximum_composite_error
        <= gates_config["maximum_composite_error"],
        "warm_regret_identity": maximum_regret_error
        <= gates_config["maximum_warm_regret_error"],
        "warm_strategy_sum_identity": maximum_sum_error
        <= gates_config["maximum_warm_strategy_sum_error"],
        "warm_policy_probability_identity": maximum_probability_error
        <= gates_config["maximum_warm_policy_probability_error"],
        "warm_policy_tv_identity": maximum_mean_tv
        <= gates_config["maximum_warm_policy_mean_total_variation"],
        "structural_identity": all(
            row["structural_identity"] for row in all_tier_identity
        )
        and all(
            row["regret_structural_identity"]
            and row["strategy_sum_structural_identity"]
            and row["iteration_identity"]
            for row in all_warm_identity
        )
        == gates_config["require_structural_identity"],
        "fold_placement_accounting": fold_accounting
        == gates_config["require_fold_placement_accounting"],
        "device_transfer_reduction": transfer_reduction
        == gates_config["require_device_transfer_reduction"],
        "safe_preflight": all(row["batch_safe_preflight"] for row in target_rows)
        == gates_config["require_safe_preflight"],
        "arm_wall_ms": max(
            (float(row["wall_ms"]) for row in [*all_warm, *all_tier]),
            default=math.inf,
        )
        <= gates_config["maximum_arm_wall_ms"],
        "gpu_pool": maximum_pool <= gates_config["maximum_gpu_pool_bytes"],
        "physical_free": minimum_free
        >= gates_config["minimum_postwork_physical_free_bytes"],
        "total_audit_seconds": total_seconds
        <= gates_config["maximum_total_audit_seconds"],
        "blueprint_emission": all(
            row["emitted_candidate_id"] == "blueprint_average64"
            and row["emitted_policy_sha256"] == row["blueprint_policy_sha256"]
            for row in target_rows
        )
        == gates_config["require_blueprint_emission"],
        "finite": _finite_tree({"targets": target_rows, "seconds": total_seconds})
        == gates_config["require_finite"],
        "strategy_population_claim_null": True
        == gates_config["require_strategy_population_claim_null"],
    }
    gates["passed"] = all(gates.values())

    pooled_warm_host = statistics.median(
        row["wall_ms"] for row in all_warm if row["arm"] == "host_fold"
    ) if completed else None
    pooled_warm_device = statistics.median(
        row["wall_ms"] for row in all_warm if row["arm"] == "device_fold"
    ) if completed else None
    pooled_tier = {
        cell: statistics.median(row["wall_ms"] for row in all_tier if row["cell"] == cell)
        for cell in _TIER_CELLS
    } if completed else {}
    host_peer = None
    if global_cell is not None:
        host_peer = "host_scalar" if global_cell == "device_scalar" else "host_batch"
    warm_speedup = (
        pooled_warm_host / pooled_warm_device
        if pooled_warm_host is not None and pooled_warm_device is not None
        else None
    )
    tier_speedup = (
        pooled_tier[host_peer] / pooled_tier[global_cell]
        if global_cell is not None and host_peer is not None
        else None
    )
    h3_resurrected = bool(
        completed
        and statistics.median(row["device_batch_speedup"] for row in completed)
        >= float(parsed["h3_device_batch_speedup_threshold"])
        and statistics.median(
            row["batch_placement_interaction_ratio"] for row in completed
        )
        >= float(parsed["h3_interaction_ratio_threshold"])
    )
    full_fit = [ledger["full_six_block_set_fits"] for ledger in ledgers]
    no_warm_regression = bool(
        completed
        and all(
            row["warm_median_ms"]["device_fold"]
            / row["warm_median_ms"]["host_fold"]
            <= float(parsed["maximum_target_regression_ratio"])
            for row in completed
        )
    )
    no_tier_regression = bool(
        completed
        and global_cell is not None
        and host_peer is not None
        and all(
            row["tier_median_ms"][global_cell]
            / row["tier_median_ms"][host_peer]
            <= float(parsed["maximum_target_regression_ratio"])
            for row in completed
        )
    )
    material_warm = bool(
        warm_speedup is not None
        and warm_speedup >= float(parsed["minimum_material_speedup"])
        and no_warm_regression
    )
    material_tier = bool(
        tier_speedup is not None
        and tier_speedup >= float(parsed["minimum_material_speedup"])
        and no_tier_regression
    )
    if not gates["passed"]:
        decision = "reject_resident_record_to_hand_fold_differential"
    elif material_warm and material_tier:
        decision = "accept_device_fold_for_warm_step_and_tier_b"
    elif material_warm:
        decision = "accept_device_fold_for_warm_step_only"
    elif material_tier:
        decision = "accept_device_fold_for_tier_b_only"
    else:
        decision = "retain_host_fold_pending_separate_sparse_profile"

    result = {
        "schema_version": 1,
        "status": "h32_resident_record_to_hand_fold_differential_executed",
        "methodology": {
            "retained_contexts_only": True,
            "strategy_labels_loaded": 0,
            "accepted_scalar_teacher_is_untimed_identity_only": True,
            "shared_additive_pipeline_changes_only_fold_placement": True,
            "hardware_counters_in_timed_process": False,
            "speed_and_full_set_fit_are_not_validity_gates": True,
            "immutable_blueprint_emission": True,
        },
        "environment": {
            **environment_metadata(),
            **runtime,
            "git": git,
            "nsight_compute_non_gating_availability": _ncu_metadata(),
        },
        "config_sha256": _sha256(config_path),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "fold_implementation_sha256": _sha256(_FOLD_IMPLEMENTATION),
        "target_rows": target_rows,
        "aggregate": {
            "targets_completed": len(completed),
            "candidate_rows": sum(len(row["endpoint_rows"]) for row in completed),
            "maximum_affine_numeric_error": maximum_affine_error if completed else None,
            "maximum_composite_error": maximum_composite_error if completed else None,
            "maximum_warm_regret_error": maximum_regret_error if completed else None,
            "maximum_warm_strategy_sum_error": maximum_sum_error if completed else None,
            "maximum_warm_policy_probability_error": (
                maximum_probability_error if completed else None
            ),
            "maximum_warm_policy_mean_total_variation": (
                maximum_mean_tv if completed else None
            ),
            "maximum_gpu_pool_bytes": maximum_pool,
            "minimum_gpu_free_bytes": minimum_free,
            "globally_selected_device_tier_cell": global_cell,
            "pooled_warm_host_median_ms": pooled_warm_host,
            "pooled_warm_device_median_ms": pooled_warm_device,
            "pooled_warm_speedup": warm_speedup,
            "pooled_tier_cell_medians_ms": pooled_tier,
            "pooled_selected_tier_speedup_vs_host_peer": tier_speedup,
            "no_warm_target_regression": no_warm_regression,
            "no_selected_tier_target_regression": no_tier_regression,
            "h3_batch_barrier_resurrected_diagnostic": h3_resurrected,
            "full_six_block_fit_targets": sum(full_fit),
            "linear_current_library_k_estimates_report_only": linear_k_estimates,
        },
        "gates": gates,
        "passed": gates["passed"],
        "decision": decision,
        "strategy_population_claim": None,
        "total_audit_seconds": total_seconds,
        "limitations": [
            "All six retained contexts and candidate blocks were exposed previously.",
            "No ADR-0186, ADR-0206, or later strategy label is deserialized or joined.",
            "The K estimate linearly scales a measured six-block bill and is report-only.",
            "Feature-width fill is a workload proxy, not an occupancy measurement.",
            "Nsight Compute availability does not authorize or gate a hardware claim.",
            (
                "No strategy-quality, transfer, deployment, population, or "
                "hardware claim is authorized."
            ),
        ],
    }
    output_path.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=_CONFIG)
    parser.add_argument("--output", type=Path, default=_OUTPUT)
    args = parser.parse_args()
    result = run_h32_resident_record_to_hand_fold_differential(
        args.config, args.output
    )
    print(
        json.dumps(
            {
                "output": str(args.output),
                "passed": result["passed"],
                "decision": result["decision"],
                "aggregate": result["aggregate"],
            },
            indent=2,
        )
    )
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
