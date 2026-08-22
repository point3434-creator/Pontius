"""Fresh live-like strategy trial on exact h32 continuation roots.

All continuation affine matrices and frozen winner choices are completed before
one independent exact-certificate teacher per selected target is opened.  The
repository artifact emits only the immutable restricted blueprint.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
import gc
import hashlib
import json
import math
from pathlib import Path
import time
from typing import Any, Mapping, Sequence

import numpy as np

from .axis_cfr_checkpoint import axis_cfr_checkpoint_digest
from .cupy_sparse_incidence import release_cupy_memory_pool
from .delta_certificate_contract import interpolate_policy_atoms
from .device_fold_resident_leaf_adjoint_cfr import (
    DeviceFoldResidentLeafAdjointPublicTreeCFR,
)
from .device_fold_selector_stable_affine_response import (
    evaluate_device_fold_selector_stable_affine_leaf_adjoint_seat,
)
from .fresh_h32_strategy_transfer_audit import _belief_digest
from .h32_action_conditioned_widened_selector_trial import (
    build_all_changed_public_node_blocks,
)
from .h32_affine_resident_cache_preflight import _strict_git_metadata, _validate_runtime
from .h32_continuation_root_ledger import _setup
from .h32_fresh_regret_vertex_opportunity_audit import (
    build_regret_vertex_candidate,
    direction_has_convex_scope,
    recover_iteration_one_dcfr_regret_deltas,
)
from .h32_fresh_union_value_audit import _certificate, _memory_snapshot
from .h32_selector_stable_affine_certificate_audit import _source_quality
from .h32_warm_search_acceptance_audit import _policy_distance
from .incremental_policy_tt import compile_policy_probability_tape
from .real_policy import policy_digest
from .reporting import environment_metadata
from .selector_stable_affine_response import (
    certify_selector_stable_affine_envelope,
    evaluate_selector_stable_affine_leaf_adjoint_seat,
)


_ROOT = Path(__file__).parents[2]
_CONFIG = _ROOT / "experiments/configs/h32-continuation-root-strategy-trial-v1.json"
_OUTPUT = _ROOT / "experiments/results/h32-continuation-root-strategy-trial-v1.json"
_SOURCE = _ROOT / "experiments/results/h32-fresh-panel-source-blueprints-v1.json"
_MANIFEST = _ROOT / "experiments/results/h32-action-conditioned-posterior-manifest-v1.json"
_PREFLIGHT = _ROOT / "experiments/results/h32-continuation-root-preflight-v1.json"
_LEDGER = _ROOT / "experiments/results/h32-continuation-root-ledger-v1.json"
_LEDGER_DECISION = _ROOT / "docs/decisions/ADR-0226-continuation-root-unbinds-the-complete-31-block-library.md"
_IMPLEMENTATION = Path(__file__)
_TEST = _ROOT / "tests/test_h32_continuation_root_strategy_trial.py"

_PATHS = {
    "expected_source_result_sha256": _SOURCE,
    "expected_manifest_result_sha256": _MANIFEST,
    "expected_preflight_result_sha256": _PREFLIGHT,
    "expected_ledger_result_sha256": _LEDGER,
    "expected_ledger_decision_sha256": _LEDGER_DECISION,
    "expected_continuation_implementation_sha256": _ROOT / "src/pontius/continuation_public_tree_tensor.py",
    "expected_ledger_implementation_sha256": _ROOT / "src/pontius/h32_continuation_root_ledger.py",
    "expected_device_cfr_sha256": _ROOT / "src/pontius/device_fold_resident_leaf_adjoint_cfr.py",
    "expected_device_affine_sha256": _ROOT / "src/pontius/device_fold_selector_stable_affine_response.py",
    "expected_affine_semantics_sha256": _ROOT / "src/pontius/selector_stable_affine_response.py",
    "expected_incremental_verifier_sha256": _ROOT / "src/pontius/incremental_leaf_adjoint_response.py",
    "expected_trial_implementation_sha256": _IMPLEMENTATION,
    "expected_control_test_sha256": _TEST,
}


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required continuation strategy input is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _finite_tree(value: Any) -> bool:
    if isinstance(value, Mapping):
        return all(_finite_tree(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return all(_finite_tree(item) for item in value)
    if isinstance(value, float):
        return math.isfinite(value)
    return True


def may_start_continuation_candidate(
    *,
    elapsed_ms: float,
    prior_maximum_candidate_ms: float,
    decision_budget_ms: float,
    emission_reserve_ms: float,
    certificate_start_reserve_ms: float,
    envelope_reserve_ms: float,
) -> bool:
    """Return the frozen pre-candidate hard-clock guard."""

    values = (
        elapsed_ms,
        prior_maximum_candidate_ms,
        decision_budget_ms,
        emission_reserve_ms,
        certificate_start_reserve_ms,
        envelope_reserve_ms,
    )
    if any(not math.isfinite(value) or value < 0.0 for value in values):
        raise ValueError("continuation candidate guard requires finite nonnegative inputs")
    if decision_budget_ms <= emission_reserve_ms:
        raise ValueError("continuation candidate guard has no pre-emission budget")
    cutoff = decision_budget_ms - emission_reserve_ms
    required = (
        prior_maximum_candidate_ms
        + certificate_start_reserve_ms
        + envelope_reserve_ms
    )
    return elapsed_ms + required <= cutoff


def select_full_affine_winner(
    rows: Sequence[Mapping[str, Any]],
) -> Mapping[str, Any] | None:
    """Select maximum positive complete affine value, then structural index."""

    eligible = [
        row
        for row in rows
        if bool(row["envelope"]["complete"])
        and row["envelope"]["selected_scale"] is not None
        and float(row["envelope"]["positive_certified_value"]) > 0.0
    ]
    if not eligible:
        return None
    return min(
        eligible,
        key=lambda row: (
            -float(row["envelope"]["positive_certified_value"]),
            int(row["schedule_index"]),
        ),
    )


def _parse_config(config: dict[str, Any]) -> dict[str, Any]:
    for field, path in _PATHS.items():
        if config.get(field) != _sha256(path):
            raise ValueError(f"continuation strategy provenance mismatch: {field}")
    exact = {
        "evidence_stage": "preregistered_after_adr0226_before_any_continuation_affine_value_or_strategy_label",
        "seed": 20260822,
        "scope": "all_twelve_exact_continuation_targets_one_warm_step_all_guard_completed_blocks_one_full_affine_winner_and_one_independent_teacher",
        "candidate_order": "continuation_public_tree_preorder_then_actor_then_full_public_history",
        "candidate_guard": "prior_target_maximum_complete_candidate_plus_ten_ms_envelope_plus_1250ms_certificate_before_14000ms_cutoff",
        "winner_rule": "maximum_positive_complete_full_affine_envelope_value_then_lowest_public_tree_schedule_index",
        "teacher_rule": "one_independent_incremental_exact_certificate_on_the_frozen_winner_only_no_adaptive_scale_search",
        "emitted_policy": "immutable_restricted_blueprint_research_only",
        "decision_budget_ms": 15000.0,
        "emission_reserve_ms": 1000.0,
        "certificate_start_reserve_ms": 1250.0,
        "envelope_reserve_ms": 10.0,
        "pot": 12.0,
        "stack": 30.0,
        "bet_size": 3.0,
        "players": 6,
        "hands_per_player": 32,
        "axis_seed": 20260819,
        "mixture_components": 3,
        "split_index": 3,
        "query_chunk_records": 256,
        "solver_variant": "dcfr",
        "warm_regret_mass_payoff_fraction": 0.1,
        "search_steps_per_target": 1,
        "acceptance_guard_normalized": 1e-10,
        "seat_order": [0, 1, 2, 3, 4, 5],
        "maximum_feature_width_per_batch": 384,
        "selector_margin_allowance": 2e-11,
        "envelope_numerical_allowance": 2e-11,
        "safety_fraction": 0.5,
        "numerical_floor": 1e-10,
        "required_numpy_version": "2.5.2",
        "required_scipy_version": "1.18.0",
        "required_cupy_version": "14.2.0",
        "required_cuda_runtime_version": 13020,
        "minimum_cuda_driver_version": 13000,
        "required_compute_capability": "120",
        "cuda_dll_environment_variable": "PONTIUS_CUDA_DLL_DIRECTORY",
    }
    for field, expected in exact.items():
        if config.get(field) != expected:
            raise ValueError(f"continuation strategy field differs from ADR-0227: {field}")
    if len(config.get("targets", ())) != 12:
        raise ValueError("continuation strategy trial requires all twelve targets")
    gates = {
        "expected_targets": 12,
        "expected_search_steps": 12,
        "expected_block_manifest_per_target": 31,
        "expected_information_sets_per_target": 992,
        "maximum_affine_intercept_error": 2e-11,
        "maximum_teacher_prediction_error": 2e-11,
        "maximum_warm_start_probability_error": 1e-12,
        "maximum_warm_start_mean_total_variation": 1e-13,
        "maximum_search_step_ms": 60000.0,
        "maximum_candidate_ms": 60000.0,
        "maximum_certificate_ms": 60000.0,
        "maximum_gpu_pool_bytes": 12000000000,
        "minimum_physical_free_bytes": 1000000000,
        "maximum_total_seconds": 1800.0,
        "require_clean_git_state": True,
        "require_parents_passed": True,
        "require_source_checkpoint_identity": True,
        "require_target_identity": True,
        "require_blueprint_identity": True,
        "require_warm_start_identity": True,
        "require_complete_block_manifest": True,
        "require_convex_scope": True,
        "require_five_opponent_calls": True,
        "require_zero_own_contractions": True,
        "require_hard_clock_guard": True,
        "require_feature_label_barrier": True,
        "require_exact_teacher_independence": True,
        "require_winner_selection_identity": True,
        "require_deadline_fallback_identity": True,
        "require_blueprint_emission": True,
        "require_strategy_population_claim_null": True,
        "require_finite": True,
    }
    if config.get("gates") != gates:
        raise ValueError("continuation strategy gates differ from ADR-0227")
    return {
        **config,
        "targets": tuple(dict(row) for row in config["targets"]),
        "gates": gates,
    }


def _release(objects: dict[str, Any]) -> None:
    objects.clear()
    gc.collect()
    release_cupy_memory_pool()


def _ordered_blocks(layout: Any, blueprint: Any, candidate: Any) -> tuple[dict[str, Any], ...]:
    blocks = build_all_changed_public_node_blocks(blueprint, candidate)
    node_order = {
        (
            node.player,
            "root"
            if not node.history
            else "/".join(f"p{seat}:{action}" for seat, action in node.history),
        ): index
        for index, node in enumerate(layout.nodes)
        if node.player >= 0
    }
    return tuple(
        sorted(
            blocks,
            key=lambda row: (
                node_order[(int(row["acting_seat"]), str(row["public_history"]))],
                int(row["acting_seat"]),
                str(row["public_history"]),
            ),
        )
    )


def _feature_target(
    parsed: Mapping[str, Any],
    source_parent: Mapping[str, Any],
    ledger_target: Mapping[str, Any],
    spec: Mapping[str, Any],
    cp: Any,
) -> tuple[dict[str, Any], dict[str, Any]]:
    objects = _setup(parsed, source_parent, spec)
    layout = objects["layout"]
    belief = objects["belief"]
    blueprint = objects["blueprint"]
    context = objects["context"]
    shared = objects["shared"]
    gpu = objects["gpu"]
    state = objects["state"]
    blueprint_quality = _source_quality(context, payoff_span=float(parsed["stack"]))
    solver = DeviceFoldResidentLeafAdjointPublicTreeCFR(
        layout,
        objects["workspace"],
        objects["sparse"],
        objects["automata"],
        str(parsed["solver_variant"]),
        belief_cache=context.belief_cache,
        automaton_caches=shared.automaton_caches,
        cupy_sparse=gpu,
        maximum_feature_width_per_batch=int(parsed["maximum_feature_width_per_batch"]),
        hands_by_player=belief.hands_by_player,
        record_to_hand_backend="gpu_cupy",
    )
    warm_mass = float(parsed["warm_regret_mass_payoff_fraction"]) * float(
        layout.game.payoff_span
    )
    solver.warm_start(blueprint, warm_mass)
    warm_distance = _policy_distance(blueprint, solver.current_strategy())
    release_cupy_memory_pool()
    memory_rows = [_memory_snapshot(cp)]
    cp.cuda.runtime.deviceSynchronize()
    street_started = time.perf_counter()
    solver.step()
    cp.cuda.runtime.deviceSynchronize()
    warm_step_ms = (time.perf_counter() - street_started) * 1000.0
    candidate = solver.current_strategy()
    regret_deltas = recover_iteration_one_dcfr_regret_deltas(
        blueprint,
        solver.regret_table(),
        warm_regret_mass=warm_mass,
    )
    blocks = _ordered_blocks(layout, blueprint, candidate)
    block_manifest = [
        {
            "schedule_index": index,
            "acting_seat": block["acting_seat"],
            "public_history": block["public_history"],
            "information_set_count": block["information_set_count"],
            "changed_entry_count": block["changed_entry_count"],
        }
        for index, block in enumerate(blocks)
    ]
    raw_guard = float(parsed["acceptance_guard_normalized"]) * float(parsed["stack"])
    scale_grid = tuple(
        2.0**-index
        for index in range(64)
        if 2.0**-index >= float(parsed["numerical_floor"])
    )
    prior_maximum = float(
        ledger_target["capacity_before_labels"]["maximum_candidate_ms"]
    )
    rows = []
    stop_reason = "complete_library"
    terminal_guard = None
    maximum_intercept_error = 0.0
    for schedule_index, block in enumerate(blocks):
        elapsed_before_ms = (time.perf_counter() - street_started) * 1000.0
        guard_passed = may_start_continuation_candidate(
            elapsed_ms=elapsed_before_ms,
            prior_maximum_candidate_ms=prior_maximum,
            decision_budget_ms=float(parsed["decision_budget_ms"]),
            emission_reserve_ms=float(parsed["emission_reserve_ms"]),
            certificate_start_reserve_ms=float(parsed["certificate_start_reserve_ms"]),
            envelope_reserve_ms=float(parsed["envelope_reserve_ms"]),
        )
        if not guard_passed:
            stop_reason = "candidate_start_guard"
            terminal_guard = {
                "schedule_index": schedule_index,
                "elapsed_before_ms": elapsed_before_ms,
                "guard_passed": False,
            }
            break
        cp.cuda.runtime.deviceSynchronize()
        candidate_started = time.perf_counter()
        seat = int(block["acting_seat"])
        keys = tuple(block["information_keys"])
        endpoint = build_regret_vertex_candidate(blueprint, regret_deltas, keys)
        probabilities = compile_policy_probability_tape(
            layout, belief.hands_by_player, endpoint
        )
        own = evaluate_selector_stable_affine_leaf_adjoint_seat(
            context.response_caches[seat],
            probabilities,
            acting_player=seat,
            selector_margin_allowance=float(parsed["selector_margin_allowance"]),
            maximum_feature_width_per_batch=int(parsed["maximum_feature_width_per_batch"]),
            belief_cache=context.belief_cache,
            automaton_cache=shared.automaton_caches[seat],
            cupy_sparse=gpu,
        )
        affine_rows = []
        opponent_calls = 0
        for target_player in range(6):
            if target_player == seat:
                affine_rows.append(own)
                continue
            measured = evaluate_device_fold_selector_stable_affine_leaf_adjoint_seat(
                context.response_caches[target_player],
                probabilities,
                acting_player=seat,
                selector_margin_allowance=float(parsed["selector_margin_allowance"]),
                maximum_feature_width_per_batch=int(parsed["maximum_feature_width_per_batch"]),
                belief_cache=context.belief_cache,
                automaton_cache=shared.automaton_caches[target_player],
                cupy_sparse=gpu,
                record_to_hand_backend="gpu_cupy",
            )
            affine_rows.append(measured.semantic)
            opponent_calls += 1
        envelope = certify_selector_stable_affine_envelope(
            tuple(affine_rows),
            blueprint_deviation_gains=tuple(blueprint_quality["deviation_gains"]),
            blueprint_nash_conv=float(blueprint_quality["nash_conv"]),
            raw_guard=raw_guard,
            scale_grid=scale_grid,
            safety_fraction=float(parsed["safety_fraction"]),
            numerical_allowance=float(parsed["envelope_numerical_allowance"]),
        )
        cp.cuda.runtime.deviceSynchronize()
        complete_ms = (time.perf_counter() - candidate_started) * 1000.0
        intercept_error = max(
            abs(
                float(row.deviation_gain_intercept)
                - float(blueprint_quality["deviation_gains"][target_player])
            )
            for target_player, row in enumerate(affine_rows)
        )
        maximum_intercept_error = max(maximum_intercept_error, intercept_error)
        rows.append(
            {
                **block,
                "candidate_id": f"block_{schedule_index:03d}_seat{seat}_regret_vertex",
                "schedule_index": schedule_index,
                "direction_family": "regret_vertex",
                "convex_scope": direction_has_convex_scope(block),
                "endpoint_policy_sha256": policy_digest(endpoint),
                "opponent_calls": opponent_calls,
                "own_affected_terminal_contractions": own.affected_terminal_contractions,
                "affine_rows": [asdict(row) for row in affine_rows],
                "envelope": asdict(envelope),
                "elapsed_before_ms": elapsed_before_ms,
                "complete_candidate_ms": complete_ms,
                "elapsed_completed_ms": (time.perf_counter() - street_started)
                * 1000.0,
                "guard_passed": True,
                "strategy_label": None,
            }
        )
        memory_rows.append(_memory_snapshot(cp))
    feature_elapsed_ms = (time.perf_counter() - street_started) * 1000.0
    winner = select_full_affine_winner(rows)
    result = {
        "target_id": spec["target_id"],
        "source": spec["source"],
        "observed_bettor": spec["observed_bettor"],
        "source_checkpoint_identity": axis_cfr_checkpoint_digest(state)
        == state["state_sha256"]
        and _belief_digest(objects["source"]) == spec["source_belief_sha256"],
        "target_identity": _belief_digest(belief) == spec["target_belief_sha256"],
        "blueprint_identity": policy_digest(objects["full_blueprint"])
        == state["average_policy_sha256"],
        "restricted_blueprint_policy_sha256": policy_digest(blueprint),
        "blueprint_quality": blueprint_quality,
        "warm_start_distance": warm_distance,
        "warm_step_ms": warm_step_ms,
        "block_manifest": block_manifest,
        "changed_information_set_count": sum(
            row["information_set_count"] for row in block_manifest
        ),
        "priced_candidate_rows": rows,
        "prior_maximum_candidate_ms": prior_maximum,
        "candidate_stop_reason": stop_reason,
        "terminal_guard": terminal_guard,
        "feature_elapsed_ms": feature_elapsed_ms,
        "maximum_affine_intercept_error": maximum_intercept_error,
        "frozen_winner_candidate_id": None if winner is None else winner["candidate_id"],
        "frozen_winner_schedule_index": None
        if winner is None
        else winner["schedule_index"],
        "frozen_winner_scale": None
        if winner is None
        else winner["envelope"]["selected_scale"],
        "frozen_winner_predicted_value": 0.0
        if winner is None
        else winner["envelope"]["positive_certified_value"],
        "teacher": None,
        "memory_rows": memory_rows,
        "actual_emitted_policy_sha256": policy_digest(blueprint),
    }
    payload = {
        "spec": dict(spec),
        "regret_deltas": regret_deltas,
        "winner_information_keys": None
        if winner is None
        else tuple(winner["information_keys"]),
    }
    del solver
    _release(objects)
    return result, payload


def _label_target(
    parsed: Mapping[str, Any],
    source_parent: Mapping[str, Any],
    target: dict[str, Any],
    payload: Mapping[str, Any],
    cp: Any,
) -> None:
    winner_id = target["frozen_winner_candidate_id"]
    if winner_id is None:
        target["teacher"] = {
            "queried": False,
            "reason": "no_positive_complete_affine_envelope",
            "strategy_label": 0.0,
            "shadow_selected_candidate_id": "blueprint_average64",
            "shadow_selected_policy_sha256": target[
                "restricted_blueprint_policy_sha256"
            ],
        }
        return
    objects = _setup(parsed, source_parent, payload["spec"])
    blueprint = objects["blueprint"]
    endpoint = build_regret_vertex_candidate(
        blueprint,
        payload["regret_deltas"],
        payload["winner_information_keys"],
    )
    scale = float(target["frozen_winner_scale"])
    policy = interpolate_policy_atoms(
        blueprint,
        endpoint,
        payload["winner_information_keys"],
        scale=scale,
    )
    start_guard_passed = target["feature_elapsed_ms"] <= (
        float(parsed["decision_budget_ms"])
        - float(parsed["emission_reserve_ms"])
        - float(parsed["certificate_start_reserve_ms"])
    )
    cp.cuda.runtime.deviceSynchronize()
    certificate = _certificate(
        candidate_id=str(winner_id),
        policy=policy,
        layout=objects["layout"],
        belief=objects["belief"],
        context=objects["context"],
        shared=objects["shared"],
        gpu=objects["gpu"],
        blueprint_quality=target["blueprint_quality"],
        parsed=dict(parsed),
    )
    cp.cuda.runtime.deviceSynchronize()
    simulated_completed_ms = target["feature_elapsed_ms"] + float(
        certificate["wall_ms"]
    )
    usable = start_guard_passed and simulated_completed_ms <= (
        float(parsed["decision_budget_ms"])
        - float(parsed["emission_reserve_ms"])
    )
    exact_value = (
        max(
            0.0,
            float(target["blueprint_quality"]["nash_conv"])
            - float(certificate["quality"]["nash_conv"]),
        )
        if certificate["complete"]
        else 0.0
    )
    winner_row = next(
        row for row in target["priced_candidate_rows"] if row["candidate_id"] == winner_id
    )
    envelope = winner_row["envelope"]
    prediction_error = 0.0
    if certificate["complete"]:
        prediction_error = max(
            abs(float(expected) - float(actual))
            for field in (
                "utilities",
                "best_response_values",
                "deviation_gains",
            )
            for expected, actual in zip(
                envelope[f"predicted_{field}"],
                certificate["quality"][field],
                strict=True,
            )
        )
    accepted = (
        usable
        and bool(certificate["complete"])
        and exact_value > float(parsed["envelope_numerical_allowance"])
        and prediction_error <= float(parsed["envelope_numerical_allowance"])
    )
    target["teacher"] = {
        "queried": True,
        "independent_incremental_certificate": True,
        "candidate_id": winner_id,
        "policy_sha256": certificate["policy_sha256"],
        "complete": bool(certificate["complete"]),
        "stop_reason": certificate["stop_reason"],
        "wall_ms": certificate["wall_ms"],
        "quality": certificate.get("quality"),
        "predicted_positive_value": target["frozen_winner_predicted_value"],
        "exact_positive_value": exact_value,
        "maximum_affine_teacher_error": prediction_error,
        "certificate_start_guard_passed": start_guard_passed,
        "simulated_live_completed_ms": simulated_completed_ms,
        "usable_before_emission_cutoff": usable,
        "accepted_by_shadow_rule": accepted,
        "strategy_label": exact_value if accepted else 0.0,
        "shadow_selected_candidate_id": winner_id
        if accepted
        else "blueprint_average64",
        "shadow_selected_policy_sha256": certificate["policy_sha256"]
        if accepted
        else target["restricted_blueprint_policy_sha256"],
    }
    target["memory_rows"].append(_memory_snapshot(cp))
    _release(objects)


def run_h32_continuation_root_strategy_trial(
    config_path: Path = _CONFIG,
    output_path: Path = _OUTPUT,
) -> dict[str, Any]:
    started = time.perf_counter()
    parsed = _parse_config(json.loads(config_path.read_text(encoding="utf-8")))
    git = _strict_git_metadata()
    cp, runtime = _validate_runtime(parsed)
    source_parent = json.loads(_SOURCE.read_text(encoding="utf-8"))
    manifest = json.loads(_MANIFEST.read_text(encoding="utf-8"))
    preflight = json.loads(_PREFLIGHT.read_text(encoding="utf-8"))
    ledger = json.loads(_LEDGER.read_text(encoding="utf-8"))
    ledger_by_target = {
        row["target_id"]: row for row in ledger["target_rows"]
    }
    target_rows = []
    payloads = []
    feature_started = time.perf_counter()
    for spec in parsed["targets"]:
        target, payload = _feature_target(
            parsed,
            source_parent,
            ledger_by_target[spec["target_id"]],
            spec,
            cp,
        )
        target_rows.append(target)
        payloads.append(payload)
    feature_seconds = time.perf_counter() - feature_started
    barrier = {
        "all_targets_completed_before_teacher": True,
        "target_matrices": len(target_rows),
        "priced_candidate_rows": sum(
            len(target["priced_candidate_rows"]) for target in target_rows
        ),
        "frozen_winners": sum(
            target["frozen_winner_candidate_id"] is not None for target in target_rows
        ),
        "non_null_strategy_labels_before_teacher": sum(
            row["strategy_label"] is not None
            for target in target_rows
            for row in target["priced_candidate_rows"]
        ),
        "teacher_rows_before_teacher": sum(
            target["teacher"] is not None for target in target_rows
        ),
        "feature_phase_seconds": feature_seconds,
    }
    teacher_started = time.perf_counter()
    for target, payload in zip(target_rows, payloads, strict=True):
        _label_target(parsed, source_parent, target, payload, cp)
    teacher_seconds = time.perf_counter() - teacher_started
    all_rows = [
        row for target in target_rows for row in target["priced_candidate_rows"]
    ]
    queried = [target["teacher"] for target in target_rows if target["teacher"]["queried"]]
    total_seconds = time.perf_counter() - started
    maximum_teacher_error = max(
        (
            teacher["maximum_affine_teacher_error"]
            for teacher in queried
            if teacher["complete"]
        ),
        default=0.0,
    )
    minimum_free = min(
        memory["gpu_free_bytes"]
        for target in target_rows
        for memory in target["memory_rows"]
    )
    maximum_pool = max(
        memory["gpu_pool_total_bytes"]
        for target in target_rows
        for memory in target["memory_rows"]
    )
    gate = parsed["gates"]
    gates = {
        "clean_git": (not git["dirty"]) == gate["require_clean_git_state"],
        "parents_passed": bool(manifest["passed"] and preflight["passed"] and ledger["passed"])
        == gate["require_parents_passed"],
        "target_count": len(target_rows) == gate["expected_targets"],
        "search_step_count": len(target_rows) == gate["expected_search_steps"],
        "block_manifests": all(
            len(target["block_manifest"]) == gate["expected_block_manifest_per_target"]
            and target["changed_information_set_count"]
            == gate["expected_information_sets_per_target"]
            for target in target_rows
        ),
        "source_checkpoint_identity": all(
            target["source_checkpoint_identity"] for target in target_rows
        )
        == gate["require_source_checkpoint_identity"],
        "target_identity": all(target["target_identity"] for target in target_rows)
        == gate["require_target_identity"],
        "blueprint_identity": all(target["blueprint_identity"] for target in target_rows)
        == gate["require_blueprint_identity"],
        "warm_start_identity": max(
            target["warm_start_distance"]["maximum_probability_error"]
            for target in target_rows
        )
        <= gate["maximum_warm_start_probability_error"]
        and max(
            target["warm_start_distance"]["mean_total_variation"]
            for target in target_rows
        )
        <= gate["maximum_warm_start_mean_total_variation"],
        "complete_block_manifest": all(
            target["changed_information_set_count"]
            == sum(row["information_set_count"] for row in target["block_manifest"])
            for target in target_rows
        )
        == gate["require_complete_block_manifest"],
        "convex_scope": all(row["convex_scope"] for row in all_rows)
        == gate["require_convex_scope"],
        "five_opponent_calls": all(row["opponent_calls"] == 5 for row in all_rows)
        == gate["require_five_opponent_calls"],
        "zero_own_contractions": all(
            row["own_affected_terminal_contractions"] == 0 for row in all_rows
        )
        == gate["require_zero_own_contractions"],
        "affine_intercepts": max(
            target["maximum_affine_intercept_error"] for target in target_rows
        )
        <= gate["maximum_affine_intercept_error"],
        "hard_clock_guard": all(
            row["guard_passed"] for row in all_rows
        )
        == gate["require_hard_clock_guard"],
        "feature_label_barrier": (
            barrier["all_targets_completed_before_teacher"]
            and barrier["target_matrices"] == 12
            and barrier["non_null_strategy_labels_before_teacher"] == 0
            and barrier["teacher_rows_before_teacher"] == 0
        )
        == gate["require_feature_label_barrier"],
        "exact_teacher_independence": all(
            teacher["independent_incremental_certificate"] for teacher in queried
        )
        == gate["require_exact_teacher_independence"],
        "winner_selection_identity": all(
            target["frozen_winner_candidate_id"]
            == (
                None
                if select_full_affine_winner(target["priced_candidate_rows"]) is None
                else select_full_affine_winner(target["priced_candidate_rows"])[
                    "candidate_id"
                ]
            )
            for target in target_rows
        )
        == gate["require_winner_selection_identity"],
        "teacher_prediction_identity": maximum_teacher_error
        <= gate["maximum_teacher_prediction_error"],
        "deadline_fallback_identity": all(
            target["teacher"]["shadow_selected_candidate_id"]
            == (
                target["frozen_winner_candidate_id"]
                if target["teacher"].get("accepted_by_shadow_rule", False)
                else "blueprint_average64"
            )
            for target in target_rows
        )
        == gate["require_deadline_fallback_identity"],
        "warm_step_time": max(target["warm_step_ms"] for target in target_rows)
        <= gate["maximum_search_step_ms"],
        "candidate_time": max(
            (row["complete_candidate_ms"] for row in all_rows), default=0.0
        )
        <= gate["maximum_candidate_ms"],
        "certificate_time": max(
            (teacher["wall_ms"] for teacher in queried), default=0.0
        )
        <= gate["maximum_certificate_ms"],
        "gpu_pool": maximum_pool <= gate["maximum_gpu_pool_bytes"],
        "physical_free": minimum_free >= gate["minimum_physical_free_bytes"],
        "blueprint_emission": all(
            target["actual_emitted_policy_sha256"]
            == target["restricted_blueprint_policy_sha256"]
            for target in target_rows
        )
        == gate["require_blueprint_emission"],
        "strategy_population_claim_null": True
        == gate["require_strategy_population_claim_null"],
        "total_time": total_seconds <= gate["maximum_total_seconds"],
        "finite": _finite_tree(target_rows) == gate["require_finite"],
    }
    gates["passed"] = all(gates.values())
    accepted = [
        target for target in target_rows if target["teacher"].get("accepted_by_shadow_rule", False)
    ]
    result = {
        "schema_version": 1,
        "status": "h32_continuation_root_strategy_trial_executed",
        "environment": {**environment_metadata(), "runtime": runtime, "git": git},
        "config_sha256": _sha256(config_path),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "feature_label_barrier": barrier,
        "target_rows": target_rows,
        "aggregate": {
            "block_manifest_rows": sum(len(target["block_manifest"]) for target in target_rows),
            "priced_candidate_rows": len(all_rows),
            "minimum_priced_candidates": min(
                len(target["priced_candidate_rows"]) for target in target_rows
            ),
            "maximum_priced_candidates": max(
                len(target["priced_candidate_rows"]) for target in target_rows
            ),
            "positive_affine_winners": sum(
                target["frozen_winner_candidate_id"] is not None for target in target_rows
            ),
            "teacher_queries": len(queried),
            "complete_teacher_queries": sum(teacher["complete"] for teacher in queried),
            "shadow_accepted_targets": len(accepted),
            "shadow_abstained_targets": len(target_rows) - len(accepted),
            "pooled_predicted_value": math.fsum(
                float(target["frozen_winner_predicted_value"]) for target in target_rows
            ),
            "pooled_delivered_exact_value": math.fsum(
                float(target["teacher"]["strategy_label"]) for target in target_rows
            ),
            "maximum_affine_intercept_error": max(
                target["maximum_affine_intercept_error"] for target in target_rows
            ),
            "maximum_teacher_prediction_error": maximum_teacher_error,
            "minimum_simulated_live_completed_ms": min(
                (teacher["simulated_live_completed_ms"] for teacher in queried),
                default=0.0,
            ),
            "maximum_simulated_live_completed_ms": max(
                (teacher["simulated_live_completed_ms"] for teacher in queried),
                default=0.0,
            ),
            "minimum_gpu_free_bytes": minimum_free,
            "maximum_gpu_pool_total_bytes": maximum_pool,
            "feature_phase_seconds": feature_seconds,
            "teacher_phase_seconds": teacher_seconds,
        },
        "gates": gates,
        "passed": gates["passed"],
        "decision": "interpret_fresh_continuation_strategy_result"
        if gates["passed"]
        else "reject_fresh_continuation_strategy_trial",
        "actual_emitted_policy": "immutable_restricted_blueprint_only",
        "strategy_population_claim": None,
        "total_seconds": total_seconds,
        "limitations": [
            "The exact teacher labels only the one full-affine winner per target, not the other continuation blocks.",
            "Simulated live completion excludes deterministic target-context reconstruction performed only to preserve the all-target feature-label barrier.",
            "The candidate family is one-step regret vertices only.",
            "No deployment, continual-resolving, composition, population, or broad poker-strength claim is made.",
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
    result = run_h32_continuation_root_strategy_trial(args.config, args.output)
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
