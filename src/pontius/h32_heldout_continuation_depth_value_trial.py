"""Held-out one-step versus two-step h32 continuation value trial."""

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
from .h32_affine_resident_cache_preflight import _strict_git_metadata, _validate_runtime
from .h32_continuation_depth_ledger import recover_discounted_step_regret_deltas
from .h32_continuation_root_ledger import _setup
from .h32_continuation_root_strategy_trial import (
    _ordered_blocks,
    may_start_continuation_candidate,
    select_full_affine_winner,
)
from .h32_fresh_regret_vertex_opportunity_audit import (
    build_regret_vertex_candidate,
    direction_has_convex_scope,
)
from .h32_fresh_union_value_audit import _memory_snapshot
from .h32_selector_stable_affine_certificate_audit import _source_quality
from .h32_warm_search_acceptance_audit import _policy_distance
from .incremental_leaf_adjoint_response import (
    verify_incremental_leaf_adjoint_candidate,
)
from .incremental_policy_tt import compile_policy_probability_tape
from .payoff_semantics import normalized_quality, payoff_span, raw_guard
from .real_policy import policy_digest
from .runner_harness import (
    artifact_passed,
    assemble_environment,
    finalize_gates,
    load_artifact,
    require_path,
    serialize_result,
)
from .selector_stable_affine_response import (
    certify_selector_stable_affine_envelope,
    evaluate_selector_stable_affine_leaf_adjoint_seat,
)
from .updates import update_rule


_ROOT = Path(__file__).parents[2]
_CONFIG = _ROOT / "experiments/configs/h32-heldout-continuation-depth-value-v1.json"
_OUTPUT = _ROOT / "experiments/results/h32-heldout-continuation-depth-value-v1.json"
_SOURCE = _ROOT / "experiments/results/h32-fresh-panel-source-blueprints-v1.json"
_MANIFEST = _ROOT / "experiments/results/h32-heldout-continuation-posterior-manifest-v1.json"
_DEPTH = _ROOT / "experiments/results/h32-continuation-depth-ledger-v1.json"
_PROCESS = _ROOT / "docs/decisions/ADR-0233-shared-payoff-semantics-and-runner-contracts-retire-repeat-defects.md"
_IMPLEMENTATION = Path(__file__)
_TEST = _ROOT / "tests/test_h32_heldout_continuation_depth_value_trial.py"

_PATHS = {
    "expected_source_result_sha256": _SOURCE,
    "expected_manifest_result_sha256": _MANIFEST,
    "expected_depth_result_sha256": _DEPTH,
    "expected_process_decision_sha256": _PROCESS,
    "expected_setup_implementation_sha256": _ROOT / "src/pontius/h32_continuation_root_ledger.py",
    "expected_device_cfr_sha256": _ROOT / "src/pontius/device_fold_resident_leaf_adjoint_cfr.py",
    "expected_device_affine_sha256": _ROOT / "src/pontius/device_fold_selector_stable_affine_response.py",
    "expected_affine_semantics_sha256": _ROOT / "src/pontius/selector_stable_affine_response.py",
    "expected_verifier_sha256": _ROOT / "src/pontius/incremental_leaf_adjoint_response.py",
    "expected_payoff_semantics_sha256": _ROOT / "src/pontius/payoff_semantics.py",
    "expected_runner_harness_sha256": _ROOT / "src/pontius/runner_harness.py",
    "expected_implementation_sha256": _IMPLEMENTATION,
    "expected_control_test_sha256": _TEST,
}


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required held-out depth input is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _finite_tree(value: Any) -> bool:
    if isinstance(value, Mapping):
        return all(_finite_tree(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return all(_finite_tree(item) for item in value)
    if isinstance(value, float):
        return math.isfinite(value)
    return True


def depth_promotion_decision(
    *,
    one_value: float,
    two_value: float,
    one_ledger_ms: float,
    two_ledger_ms: float,
    materiality_floor: float,
) -> bool:
    """Return the frozen compute-value promotion decision."""

    values = (one_value, two_value, one_ledger_ms, two_ledger_ms, materiality_floor)
    if any(not math.isfinite(value) or value < 0.0 for value in values):
        raise ValueError("depth promotion inputs must be finite and nonnegative")
    if one_ledger_ms <= 0.0 or two_ledger_ms <= 0.0:
        raise ValueError("depth promotion ledgers must be positive")
    return (
        two_value > one_value + materiality_floor
        and two_value / two_ledger_ms > one_value / one_ledger_ms
    )


def _parse_config(config: dict[str, Any]) -> dict[str, Any]:
    fields = {
        "evidence_stage", *_PATHS, "seed", "targets", "arm_order",
        "direction_rule", "winner_rule", "teacher_rule", "promotion_rule",
        "decision_budget_ms", "certificate_start_reserve_ms",
        "emission_reserve_ms", "prior_maximum_candidate_ms",
        "envelope_reserve_ms", "pot", "stack", "bet_size", "players",
        "hands_per_player", "axis_seed", "mixture_components", "split_index",
        "query_chunk_records", "solver_variant", "warm_regret_mass_payoff_fraction",
        "depth_arms", "maximum_feature_width_per_batch",
        "selector_margin_allowance", "acceptance_guard_normalized",
        "safety_fraction", "numerical_floor", "envelope_numerical_allowance",
        "seat_order", "required_numpy_version", "required_scipy_version",
        "required_cupy_version", "required_cuda_runtime_version",
        "minimum_cuda_driver_version", "required_compute_capability",
        "cuda_dll_environment_variable", "label_policy", "gates",
    }
    if set(config) != fields:
        raise ValueError("held-out continuation depth fields differ from preregistration")
    for field, path in _PATHS.items():
        if config[field] != _sha256(path):
            raise ValueError(f"held-out continuation depth source mismatch: {field}")
    targets = config["targets"]
    if not isinstance(targets, list) or len(targets) != 12:
        raise ValueError("held-out continuation depth requires twelve targets")
    required_target = {
        "target_id", "source", "board", "range_family", "observed_bettor",
        "round", "source_belief_sha256", "target_belief_sha256",
        "target_descriptor_sha256",
    }
    if any(set(row) != required_target for row in targets):
        raise ValueError("held-out continuation target schema differs")
    if config["depth_arms"] != [1, 2] or config["seat_order"] != [0, 1, 2, 3, 4, 5]:
        raise ValueError("held-out continuation arm or seat order differs")
    if config["players"] != 6 or config["hands_per_player"] != 32:
        raise ValueError("held-out continuation h32 shape differs")
    expected = {
        "evidence_stage": "preregistered_after_adr0233_before_any_heldout_continuation_warm_step_affine_value_or_strategy_label",
        "arm_order": "even_target_index_one_then_two_odd_target_index_two_then_one",
        "direction_rule": "pure_regret_vertex_from_exactly_recovered_latest_step_instantaneous_dcfr_regret_delta",
        "winner_rule": "maximum_positive_complete_full_affine_envelope_value_then_lowest_public_tree_schedule_index",
        "teacher_rule": "one_independent_incremental_exact_certificate_per_frozen_arm_winner_after_all_twenty_four_feature_matrices",
        "promotion_rule": "two_step_pooled_exact_value_exceeds_one_step_by_one_raw_guard_per_target_and_two_step_pooled_value_per_charged_ledger_ms_is_higher",
        "label_policy": "all_twenty_four_feature_matrices_and_winners_frozen_before_any_teacher_label",
    }
    if any(config[key] != value for key, value in expected.items()):
        raise ValueError("held-out continuation frozen methodology differs")
    gate_fields = {
        "expected_targets", "expected_arms", "expected_steps", "expected_blocks_per_arm",
        "expected_candidate_rows", "expected_opponent_rows",
        "maximum_affine_intercept_error", "maximum_teacher_prediction_error",
        "maximum_warm_start_probability_error", "maximum_warm_start_mean_total_variation",
        "maximum_step_ms", "maximum_candidate_ms", "maximum_certificate_ms",
        "maximum_gpu_pool_bytes", "minimum_physical_free_bytes", "maximum_total_seconds",
        "require_clean_git_state", "require_parents_passed", "require_target_identity",
        "require_source_checkpoint_identity", "require_blueprint_identity",
        "require_counterbalanced_order", "require_complete_block_partition",
        "require_convex_scope", "require_five_opponent_calls",
        "require_zero_own_contractions", "require_latest_step_recovery",
        "require_feature_label_barrier", "require_exact_teacher_independence",
        "require_winner_selection_identity", "require_deadline_fallback_identity",
        "require_blueprint_emission", "require_strategy_population_claim_null",
        "require_finite",
    }
    if not isinstance(config["gates"], dict) or set(config["gates"]) != gate_fields:
        raise ValueError("held-out continuation gates differ")
    return {**config, "targets": tuple(dict(row) for row in targets), "gates": dict(config["gates"])}


def _release(objects: dict[str, Any]) -> None:
    objects.clear()
    gc.collect()
    release_cupy_memory_pool()


def _run_arm(
    parsed: Mapping[str, Any],
    source_parent: Mapping[str, Any],
    spec: Mapping[str, Any],
    *,
    depth: int,
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
    span = payoff_span(layout)
    blueprint_quality = _source_quality(context, payoff_span=span)
    blueprint_quality["normalized_nash_conv"] = normalized_quality(
        layout, float(blueprint_quality["nash_conv"])
    )
    solver = DeviceFoldResidentLeafAdjointPublicTreeCFR(
        layout, objects["workspace"], objects["sparse"], objects["automata"],
        str(parsed["solver_variant"]), belief_cache=context.belief_cache,
        automaton_caches=shared.automaton_caches, cupy_sparse=gpu,
        maximum_feature_width_per_batch=int(parsed["maximum_feature_width_per_batch"]),
        hands_by_player=belief.hands_by_player, record_to_hand_backend="gpu_cupy",
    )
    warm_mass = float(parsed["warm_regret_mass_payoff_fraction"]) * span
    solver.warm_start(blueprint, warm_mass)
    warm_distance = _policy_distance(blueprint, solver.current_strategy())
    release_cupy_memory_pool()
    memory_rows = [_memory_snapshot(cp)]
    street_started = time.perf_counter()
    step_rows = []
    latest_delta = None
    rule = update_rule(str(parsed["solver_variant"]))
    for expected_iteration in range(1, depth + 1):
        before = solver.regret_table()
        cp.cuda.runtime.deviceSynchronize()
        started = time.perf_counter()
        solver.step()
        cp.cuda.runtime.deviceSynchronize()
        wall_ms = (time.perf_counter() - started) * 1000.0
        after = solver.regret_table()
        latest_delta = recover_discounted_step_regret_deltas(
            before, after, rule=rule, iteration=expected_iteration
        )
        step_rows.append({"iteration": expected_iteration, "wall_ms": wall_ms})
        memory_rows.append(_memory_snapshot(cp))
    if latest_delta is None:
        raise AssertionError("held-out continuation arm ran no step")
    blocks = _ordered_blocks(layout, blueprint, solver.current_strategy())
    guard = raw_guard(layout, float(parsed["acceptance_guard_normalized"]))
    scale_grid = tuple(
        2.0**-index for index in range(64)
        if 2.0**-index >= float(parsed["numerical_floor"])
    )
    rows = []
    maximum_intercept_error = 0.0
    stop_reason = "complete_library"
    for schedule_index, block in enumerate(blocks):
        elapsed_before = (time.perf_counter() - street_started) * 1000.0
        if not may_start_continuation_candidate(
            elapsed_ms=elapsed_before,
            prior_maximum_candidate_ms=float(parsed["prior_maximum_candidate_ms"]),
            decision_budget_ms=float(parsed["decision_budget_ms"]),
            emission_reserve_ms=float(parsed["emission_reserve_ms"]),
            certificate_start_reserve_ms=float(parsed["certificate_start_reserve_ms"]),
            envelope_reserve_ms=float(parsed["envelope_reserve_ms"]),
        ):
            stop_reason = "candidate_start_guard"
            break
        cp.cuda.runtime.deviceSynchronize()
        started = time.perf_counter()
        seat = int(block["acting_seat"])
        keys = tuple(block["information_keys"])
        endpoint = build_regret_vertex_candidate(blueprint, latest_delta, keys)
        probabilities = compile_policy_probability_tape(
            layout, belief.hands_by_player, endpoint
        )
        own = evaluate_selector_stable_affine_leaf_adjoint_seat(
            context.response_caches[seat], probabilities, acting_player=seat,
            selector_margin_allowance=float(parsed["selector_margin_allowance"]),
            maximum_feature_width_per_batch=int(parsed["maximum_feature_width_per_batch"]),
            belief_cache=context.belief_cache,
            automaton_cache=shared.automaton_caches[seat], cupy_sparse=gpu,
        )
        affine_rows = []
        for target_player in range(6):
            if target_player == seat:
                affine_rows.append(own)
                continue
            measured = evaluate_device_fold_selector_stable_affine_leaf_adjoint_seat(
                context.response_caches[target_player], probabilities,
                acting_player=seat,
                selector_margin_allowance=float(parsed["selector_margin_allowance"]),
                maximum_feature_width_per_batch=int(parsed["maximum_feature_width_per_batch"]),
                belief_cache=context.belief_cache,
                automaton_cache=shared.automaton_caches[target_player],
                cupy_sparse=gpu, record_to_hand_backend="gpu_cupy",
            )
            affine_rows.append(measured.semantic)
        envelope = certify_selector_stable_affine_envelope(
            tuple(affine_rows),
            blueprint_deviation_gains=tuple(blueprint_quality["deviation_gains"]),
            blueprint_nash_conv=float(blueprint_quality["nash_conv"]),
            raw_guard=guard, scale_grid=scale_grid,
            safety_fraction=float(parsed["safety_fraction"]),
            numerical_allowance=float(parsed["envelope_numerical_allowance"]),
        )
        cp.cuda.runtime.deviceSynchronize()
        complete_ms = (time.perf_counter() - started) * 1000.0
        maximum_intercept_error = max(
            maximum_intercept_error,
            max(
                abs(float(row.deviation_gain_intercept) - float(blueprint_quality["deviation_gains"][target_player]))
                for target_player, row in enumerate(affine_rows)
            ),
        )
        rows.append({
            **block,
            "candidate_id": f"depth{depth}_block_{schedule_index:03d}_seat{seat}_regret_vertex",
            "schedule_index": schedule_index,
            "convex_scope": direction_has_convex_scope(block),
            "endpoint_policy_sha256": policy_digest(endpoint),
            "opponent_calls": 5,
            "own_affected_terminal_contractions": own.affected_terminal_contractions,
            "affine_rows": [asdict(row) for row in affine_rows],
            "envelope": asdict(envelope),
            "complete_candidate_ms": complete_ms,
            "elapsed_completed_ms": (time.perf_counter() - street_started) * 1000.0,
            "strategy_label": None,
        })
        memory_rows.append(_memory_snapshot(cp))
    feature_elapsed_ms = (time.perf_counter() - street_started) * 1000.0
    winner = select_full_affine_winner(rows)
    arm = {
        "depth": depth,
        "source_checkpoint_identity": axis_cfr_checkpoint_digest(state) == state["state_sha256"]
        and _belief_digest(objects["source"]) == spec["source_belief_sha256"],
        "target_identity": _belief_digest(belief) == spec["target_belief_sha256"],
        "blueprint_identity": policy_digest(objects["full_blueprint"]) == state["average_policy_sha256"],
        "restricted_blueprint_policy_sha256": policy_digest(blueprint),
        "blueprint_quality": blueprint_quality,
        "raw_guard": guard,
        "payoff_span": span,
        "payoff_span_source": "layout.game.payoff_span",
        "warm_start_distance": warm_distance,
        "step_rows": step_rows,
        "latest_step_recovery_iteration": depth,
        "block_manifest_count": len(blocks),
        "changed_information_set_count": sum(row["information_set_count"] for row in blocks),
        "priced_candidate_rows": rows,
        "candidate_stop_reason": stop_reason,
        "feature_elapsed_ms": feature_elapsed_ms,
        "maximum_affine_intercept_error": maximum_intercept_error,
        "frozen_winner_candidate_id": None if winner is None else winner["candidate_id"],
        "frozen_winner_scale": None if winner is None else winner["envelope"]["selected_scale"],
        "frozen_winner_predicted_value": 0.0 if winner is None else winner["envelope"]["positive_certified_value"],
        "teacher": None,
        "memory_rows": memory_rows,
        "actual_emitted_policy_sha256": policy_digest(blueprint),
    }
    payload = {
        "spec": dict(spec), "regret_deltas": latest_delta,
        "winner_information_keys": None if winner is None else tuple(winner["information_keys"]),
    }
    del solver
    _release(objects)
    return arm, payload


def _label_arm(
    parsed: Mapping[str, Any], source_parent: Mapping[str, Any],
    arm: dict[str, Any], payload: Mapping[str, Any], cp: Any,
) -> None:
    winner_id = arm["frozen_winner_candidate_id"]
    if winner_id is None:
        arm["teacher"] = {
            "queried": False, "independent_incremental_certificate": True,
            "strategy_label": 0.0, "accepted_by_shadow_rule": False,
            "shadow_selected_candidate_id": "blueprint_average64",
            "charged_ledger_ms": arm["feature_elapsed_ms"] + float(parsed["emission_reserve_ms"]),
        }
        return
    objects = _setup(parsed, source_parent, payload["spec"])
    layout = objects["layout"]
    blueprint = objects["blueprint"]
    endpoint = build_regret_vertex_candidate(
        blueprint, payload["regret_deltas"], payload["winner_information_keys"]
    )
    policy = interpolate_policy_atoms(
        blueprint, endpoint, payload["winner_information_keys"],
        scale=float(arm["frozen_winner_scale"]),
    )
    start_guard_passed = arm["feature_elapsed_ms"] <= (
        float(parsed["decision_budget_ms"]) - float(parsed["emission_reserve_ms"])
        - float(parsed["certificate_start_reserve_ms"])
    )
    cp.cuda.runtime.deviceSynchronize()
    certificate = verify_incremental_leaf_adjoint_candidate(
        candidate_id=str(winner_id), layout=layout, policy=policy,
        hands_by_player=objects["belief"].hands_by_player,
        response_caches=objects["context"].response_caches,
        blueprint_deviation_gains=tuple(float(value) for value in arm["blueprint_quality"]["deviation_gains"]),
        best_complete_nash_conv=float(arm["blueprint_quality"]["nash_conv"]),
        payoff_span=payoff_span(layout),
        raw_guard=raw_guard(layout, float(parsed["acceptance_guard_normalized"])),
        seat_order=tuple(parsed["seat_order"]),
        maximum_feature_width_per_batch=int(parsed["maximum_feature_width_per_batch"]),
        belief_cache=objects["context"].belief_cache,
        automaton_caches=objects["shared"].automaton_caches,
        cupy_sparse=objects["gpu"],
    )
    cp.cuda.runtime.deviceSynchronize()
    completed_ms = arm["feature_elapsed_ms"] + float(certificate["wall_ms"])
    charged_ledger_ms = completed_ms + float(parsed["emission_reserve_ms"])
    usable = start_guard_passed and charged_ledger_ms <= float(parsed["decision_budget_ms"])
    exact_value = max(
        0.0,
        float(arm["blueprint_quality"]["nash_conv"])
        - float(certificate["quality"]["nash_conv"]),
    ) if certificate["complete"] else 0.0
    winner = next(row for row in arm["priced_candidate_rows"] if row["candidate_id"] == winner_id)
    envelope = winner["envelope"]
    prediction_error = max(
        abs(float(expected) - float(actual))
        for field in ("utilities", "best_response_values", "deviation_gains")
        for expected, actual in zip(
            envelope[f"predicted_{field}"], certificate["quality"][field], strict=True
        )
    ) if certificate["complete"] else 0.0
    accepted = (
        usable and bool(certificate["complete"])
        and exact_value > float(parsed["envelope_numerical_allowance"])
        and prediction_error <= float(parsed["envelope_numerical_allowance"])
    )
    arm["teacher"] = {
        "queried": True, "independent_incremental_certificate": True,
        "candidate_id": winner_id, "policy_sha256": certificate["policy_sha256"],
        "complete": bool(certificate["complete"]), "stop_reason": certificate["stop_reason"],
        "wall_ms": certificate["wall_ms"], "quality": certificate.get("quality"),
        "predicted_positive_value": arm["frozen_winner_predicted_value"],
        "exact_positive_value": exact_value,
        "maximum_affine_teacher_error": prediction_error,
        "certificate_start_guard_passed": start_guard_passed,
        "simulated_live_completed_ms": completed_ms,
        "charged_ledger_ms": charged_ledger_ms,
        "usable_before_emission_cutoff": usable,
        "accepted_by_shadow_rule": accepted,
        "strategy_label": exact_value if accepted else 0.0,
        "shadow_selected_candidate_id": winner_id if accepted else "blueprint_average64",
    }
    arm["memory_rows"].append(_memory_snapshot(cp))
    _release(objects)


def run_h32_heldout_continuation_depth_value_trial(
    config_path: Path = _CONFIG, output_path: Path = _OUTPUT
) -> dict[str, Any]:
    started = time.perf_counter()
    parsed = _parse_config(json.loads(config_path.read_text(encoding="utf-8")))
    git = _strict_git_metadata()
    cp, runtime = _validate_runtime(parsed)
    source_loaded = load_artifact(_SOURCE, expected_sha256=parsed["expected_source_result_sha256"], require_passed=True)
    manifest_loaded = load_artifact(_MANIFEST, expected_sha256=parsed["expected_manifest_result_sha256"], require_passed=True)
    depth_loaded = load_artifact(_DEPTH, expected_sha256=parsed["expected_depth_result_sha256"], require_passed=True)
    source_parent = source_loaded.payload
    manifest = manifest_loaded.payload
    depth_parent = depth_loaded.payload
    manifest_targets = {row["target_id"]: row for row in require_path(manifest, ("target_rows",), artifact_name="heldout manifest")}
    target_rows = []
    payload_rows = []
    for target_index, spec in enumerate(parsed["targets"]):
        order = (1, 2) if target_index % 2 == 0 else (2, 1)
        arms = []
        payloads = []
        for depth in order:
            arm, payload = _run_arm(parsed, source_parent, spec, depth=depth, cp=cp)
            arms.append(arm)
            payloads.append(payload)
        target_rows.append({
            "target_index": target_index, "target_id": spec["target_id"],
            "source": spec["source"], "round": spec["round"],
            "observed_bettor": spec["observed_bettor"], "execution_order": list(order),
            "manifest_identity": (
                manifest_targets[spec["target_id"]]["target_belief_sha256"]
                == spec["target_belief_sha256"]
                and manifest_targets[spec["target_id"]]["target_descriptor_sha256"]
                == spec["target_descriptor_sha256"]
            ),
            "arms": arms, "comparison": None,
        })
        payload_rows.append(payloads)
    all_arms = [arm for target in target_rows for arm in target["arms"]]
    all_candidates = [row for arm in all_arms for row in arm["priced_candidate_rows"]]
    barrier = {
        "all_twenty_four_feature_matrices_before_teacher": len(all_arms) == 24,
        "candidate_rows_before_teacher": len(all_candidates),
        "non_null_candidate_labels_before_teacher": sum(row["strategy_label"] is not None for row in all_candidates),
        "teacher_rows_before_teacher": sum(arm["teacher"] is not None for arm in all_arms),
    }
    for target, payloads in zip(target_rows, payload_rows, strict=True):
        for arm, payload in zip(target["arms"], payloads, strict=True):
            _label_arm(parsed, source_parent, arm, payload, cp)
        by_depth = {arm["depth"]: arm for arm in target["arms"]}
        one, two = by_depth[1], by_depth[2]
        target["comparison"] = {
            "one_step_delivered_exact_value": one["teacher"]["strategy_label"],
            "two_step_delivered_exact_value": two["teacher"]["strategy_label"],
            "two_minus_one_exact_value": two["teacher"]["strategy_label"] - one["teacher"]["strategy_label"],
            "one_step_charged_ledger_ms": one["teacher"]["charged_ledger_ms"],
            "two_step_charged_ledger_ms": two["teacher"]["charged_ledger_ms"],
        }
    one_arms = [next(arm for arm in target["arms"] if arm["depth"] == 1) for target in target_rows]
    two_arms = [next(arm for arm in target["arms"] if arm["depth"] == 2) for target in target_rows]
    one_value = math.fsum(float(arm["teacher"]["strategy_label"]) for arm in one_arms)
    two_value = math.fsum(float(arm["teacher"]["strategy_label"]) for arm in two_arms)
    one_ledger = math.fsum(float(arm["teacher"]["charged_ledger_ms"]) for arm in one_arms)
    two_ledger = math.fsum(float(arm["teacher"]["charged_ledger_ms"]) for arm in two_arms)
    materiality = math.fsum(float(arm["raw_guard"]) for arm in one_arms)
    promote = depth_promotion_decision(
        one_value=one_value, two_value=two_value,
        one_ledger_ms=one_ledger, two_ledger_ms=two_ledger,
        materiality_floor=materiality,
    )
    memory_rows = [row for arm in all_arms for row in arm["memory_rows"]]
    queried = [arm["teacher"] for arm in all_arms if arm["teacher"]["queried"]]
    gate = parsed["gates"]
    expected_order = all(
        target["execution_order"] == ([1, 2] if target["target_index"] % 2 == 0 else [2, 1])
        for target in target_rows
    )
    checks = {
        "clean_git": (not git["dirty"]) == gate["require_clean_git_state"],
        "parents_passed": all(artifact_passed(parent) for parent in (source_parent, manifest, depth_parent)) == gate["require_parents_passed"],
        "target_count": len(target_rows) == gate["expected_targets"],
        "arm_count": len(all_arms) == gate["expected_arms"],
        "step_count": sum(len(arm["step_rows"]) for arm in all_arms) == gate["expected_steps"],
        "counterbalanced_order": expected_order == gate["require_counterbalanced_order"],
        "manifest_identity": all(target["manifest_identity"] for target in target_rows),
        "source_checkpoint_identity": all(arm["source_checkpoint_identity"] for arm in all_arms) == gate["require_source_checkpoint_identity"],
        "target_identity": all(arm["target_identity"] for arm in all_arms) == gate["require_target_identity"],
        "blueprint_identity": all(arm["blueprint_identity"] for arm in all_arms) == gate["require_blueprint_identity"],
        "warm_start_identity": max(arm["warm_start_distance"]["maximum_probability_error"] for arm in all_arms) <= gate["maximum_warm_start_probability_error"] and max(arm["warm_start_distance"]["mean_total_variation"] for arm in all_arms) <= gate["maximum_warm_start_mean_total_variation"],
        "complete_block_partition": all(arm["block_manifest_count"] == gate["expected_blocks_per_arm"] and len(arm["priced_candidate_rows"]) == gate["expected_blocks_per_arm"] and arm["candidate_stop_reason"] == "complete_library" for arm in all_arms) == gate["require_complete_block_partition"],
        "candidate_count": len(all_candidates) == gate["expected_candidate_rows"],
        "opponent_count": sum(row["opponent_calls"] for row in all_candidates) == gate["expected_opponent_rows"],
        "convex_scope": all(row["convex_scope"] for row in all_candidates) == gate["require_convex_scope"],
        "five_opponent_calls": all(row["opponent_calls"] == 5 for row in all_candidates) == gate["require_five_opponent_calls"],
        "zero_own_contractions": all(row["own_affected_terminal_contractions"] == 0 for row in all_candidates) == gate["require_zero_own_contractions"],
        "latest_step_recovery": all(arm["latest_step_recovery_iteration"] == arm["depth"] for arm in all_arms) == gate["require_latest_step_recovery"],
        "affine_intercepts": max(arm["maximum_affine_intercept_error"] for arm in all_arms) <= gate["maximum_affine_intercept_error"],
        "feature_label_barrier": (barrier["all_twenty_four_feature_matrices_before_teacher"] and barrier["non_null_candidate_labels_before_teacher"] == 0 and barrier["teacher_rows_before_teacher"] == 0) == gate["require_feature_label_barrier"],
        "teacher_independence": all(row["independent_incremental_certificate"] for row in queried) == gate["require_exact_teacher_independence"],
        "winner_selection_identity": all(arm["frozen_winner_candidate_id"] == (None if select_full_affine_winner(arm["priced_candidate_rows"]) is None else select_full_affine_winner(arm["priced_candidate_rows"])["candidate_id"]) for arm in all_arms) == gate["require_winner_selection_identity"],
        "teacher_prediction_identity": max((row["maximum_affine_teacher_error"] for row in queried if row["complete"]), default=0.0) <= gate["maximum_teacher_prediction_error"],
        "deadline_fallback_identity": all(arm["teacher"]["shadow_selected_candidate_id"] == (arm["frozen_winner_candidate_id"] if arm["teacher"]["accepted_by_shadow_rule"] else "blueprint_average64") for arm in all_arms) == gate["require_deadline_fallback_identity"],
        "step_time": max(row["wall_ms"] for arm in all_arms for row in arm["step_rows"]) <= gate["maximum_step_ms"],
        "candidate_time": max(row["complete_candidate_ms"] for row in all_candidates) <= gate["maximum_candidate_ms"],
        "certificate_time": max((row["wall_ms"] for row in queried), default=0.0) <= gate["maximum_certificate_ms"],
        "gpu_pool": max(row["gpu_pool_total_bytes"] for row in memory_rows) <= gate["maximum_gpu_pool_bytes"],
        "physical_free": min(row["gpu_free_bytes"] for row in memory_rows) >= gate["minimum_physical_free_bytes"],
        "blueprint_emission": all(arm["actual_emitted_policy_sha256"] == arm["restricted_blueprint_policy_sha256"] for arm in all_arms) == gate["require_blueprint_emission"],
        "strategy_population_claim_null": True == gate["require_strategy_population_claim_null"],
        "finite": _finite_tree(target_rows) == gate["require_finite"],
        "total_time": (time.perf_counter() - started) <= gate["maximum_total_seconds"],
    }
    gate_payload = finalize_gates(checks)
    aggregate = {
        "one_step_pooled_delivered_exact_value": one_value,
        "two_step_pooled_delivered_exact_value": two_value,
        "two_minus_one_pooled_exact_value": two_value - one_value,
        "one_step_pooled_charged_ledger_ms": one_ledger,
        "two_step_pooled_charged_ledger_ms": two_ledger,
        "one_step_value_per_charged_ledger_second": 1000.0 * one_value / one_ledger,
        "two_step_value_per_charged_ledger_second": 1000.0 * two_value / two_ledger,
        "two_step_target_wins": sum(row["comparison"]["two_minus_one_exact_value"] > 0.0 for row in target_rows),
        "two_step_target_ties": sum(row["comparison"]["two_minus_one_exact_value"] == 0.0 for row in target_rows),
        "two_step_target_losses": sum(row["comparison"]["two_minus_one_exact_value"] < 0.0 for row in target_rows),
        "materiality_floor": materiality,
        "promote_two_steps": promote,
        "minimum_gpu_free_bytes": min(row["gpu_free_bytes"] for row in memory_rows),
        "maximum_gpu_pool_total_bytes": max(row["gpu_pool_total_bytes"] for row in memory_rows),
    }
    result = {
        "schema_version": 1,
        "status": "h32_heldout_continuation_depth_value_trial_executed",
        "environment": assemble_environment(runtime=runtime, git=git),
        "config_sha256": _sha256(config_path),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "feature_label_barrier": barrier,
        "target_rows": target_rows,
        "aggregate": aggregate,
        **gate_payload,
        "decision": "promote_two_continuation_steps" if gate_payload["passed"] and promote else "retain_one_continuation_step" if gate_payload["passed"] else "reject_heldout_continuation_depth_trial",
        "actual_emitted_policy": "immutable_restricted_blueprint_only",
        "strategy_population_claim": None,
        "total_seconds": time.perf_counter() - started,
        "limitations": [
            "This compares one and two continuation steps on twelve reduced h32 posterior targets only.",
            "The exact teacher labels one frozen winner per arm after the complete feature-label barrier.",
            "The existing byte-pinned device-fold solver customer is reused; its record buffers remain contiguous and unobserved after folding.",
            "No deployment, composition, population, or broad poker-strength claim is made.",
        ],
    }
    output_path.write_text(serialize_result(result), encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=_CONFIG)
    parser.add_argument("--output", type=Path, default=_OUTPUT)
    args = parser.parse_args()
    result = run_h32_heldout_continuation_depth_value_trial(args.config, args.output)
    print(json.dumps({"output": str(args.output), "passed": result["passed"], "decision": result["decision"], "aggregate": result["aggregate"]}, indent=2))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
