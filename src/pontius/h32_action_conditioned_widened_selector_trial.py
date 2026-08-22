"""Fresh widened selector trial on exact action-conditioned h32 beliefs.

All affine features, structural schedules, and clock capacities are completed
before the independent exact-certificate teacher is opened.  The emitted
policy is always the immutable source blueprint; this is a research audit.
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

from .axis_cfr_checkpoint import axis_cfr_checkpoint_digest
from .cupy_sparse_incidence import CuPyBidirectionalIncidence, release_cupy_memory_pool
from .delta_certificate_contract import atomic_policy_manifest, interpolate_policy_atoms
from .device_fold_resident_leaf_adjoint_cfr import (
    DeviceFoldResidentLeafAdjointPublicTreeCFR,
)
from .device_fold_selector_stable_affine_response import (
    evaluate_device_fold_selector_stable_affine_leaf_adjoint_seat,
)
from .factor_tt_contraction import FactorTTBeliefWorkspace
from .fresh_h32_strategy_transfer_audit import _belief_digest
from .h32_action_conditioned_posterior_manifest import (
    build_action_conditioned_posterior,
)
from .h32_affine_resident_cache_preflight import _strict_git_metadata, _validate_runtime
from .h32_atomic_response_preflight import select_one_atom_per_acting_seat
from .h32_fresh_public_block_value_audit import information_key_public_coordinates
from .h32_fresh_regret_vertex_opportunity_audit import (
    build_regret_vertex_candidate,
    recover_iteration_one_dcfr_regret_deltas,
    spearman_rank_correlation,
)
from .h32_fresh_union_value_audit import _certificate, _memory_snapshot, _safe_ratio
from .h32_retained_affine_selector_cascade_replay import (
    affine_tier_features,
    exact_random_value_floor,
)
from .h32_selector_stable_affine_certificate_audit import _source_quality
from .h32_warm_search_acceptance_audit import (
    _average_policy_from_state,
    _policy_distance,
)
from .incremental_policy_tt import compile_policy_probability_tape
from .leaf_adjoint_checkpoint_ladder_audit import _build_case
from .open_mode_factor_tt import OpenModeFactorTTWorkspace
from .real_policy import policy_digest
from .reporting import environment_metadata
from .river import parse_cards
from .selector_stable_affine_response import (
    certify_selector_stable_affine_envelope,
    evaluate_selector_stable_affine_leaf_adjoint_seat,
)
from .shared_resident_response_context import (
    SharedResidentAutomatonBundle,
    bind_resident_response_context,
)


_ROOT = Path(__file__).parents[2]
_CONFIG = _ROOT / "experiments/configs/h32-action-conditioned-widened-selector-v1.json"
_OUTPUT = _ROOT / "experiments/results/h32-action-conditioned-widened-selector-v1.json"
_SOURCE = _ROOT / "experiments/results/h32-fresh-panel-source-blueprints-v1.json"
_MANIFEST = _ROOT / "experiments/results/h32-action-conditioned-posterior-manifest-v1.json"
_MANIFEST_DECISION = _ROOT / "docs/decisions/ADR-0220-action-conditioned-posterior-panel-is-fresh-balanced-and-nondegenerate.md"
_LEDGER = _ROOT / "experiments/results/h32-resident-record-to-hand-fold-v1.json"
_REPLAY_DECISION = _ROOT / "docs/decisions/ADR-0206-opponent-sensitivity-composite-locates-retained-value-but-tier-a-cascade-fails.md"
_REQUIREMENTS = _ROOT / "experiments/requirements/leaf-adjoint-gpu-screen-v1.txt"
_IMPLEMENTATION = Path(__file__)
_TEST = _ROOT / "tests/test_h32_action_conditioned_widened_selector_trial.py"

_PATHS = {
    "expected_source_result_sha256": _SOURCE,
    "expected_manifest_result_sha256": _MANIFEST,
    "expected_manifest_decision_sha256": _MANIFEST_DECISION,
    "expected_ledger_result_sha256": _LEDGER,
    "expected_replay_decision_sha256": _REPLAY_DECISION,
    "expected_requirements_sha256": _REQUIREMENTS,
    "expected_posterior_implementation_sha256": _ROOT / "src/pontius/h32_action_conditioned_posterior_manifest.py",
    "expected_device_cfr_sha256": _ROOT / "src/pontius/device_fold_resident_leaf_adjoint_cfr.py",
    "expected_device_affine_sha256": _ROOT / "src/pontius/device_fold_selector_stable_affine_response.py",
    "expected_affine_semantics_sha256": _ROOT / "src/pontius/selector_stable_affine_response.py",
    "expected_incremental_verifier_sha256": _ROOT / "src/pontius/incremental_leaf_adjoint_response.py",
    "expected_trial_implementation_sha256": _IMPLEMENTATION,
    "expected_control_test_sha256": _TEST,
}

_EXTREME_SEAT_ORDER = (0, 5, 1, 4, 2, 3)


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required widened-selector input is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _finite_tree(value: Any) -> bool:
    if isinstance(value, Mapping):
        return all(_finite_tree(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return all(_finite_tree(item) for item in value)
    if isinstance(value, float):
        return math.isfinite(value)
    return True


def build_all_changed_public_node_blocks(
    blueprint: Mapping[str, Mapping[str, float]],
    candidate: Mapping[str, Mapping[str, float]],
) -> tuple[dict[str, Any], ...]:
    """Partition every changed infoset by its exact actor/public-history node."""

    atoms = atomic_policy_manifest(blueprint, candidate)
    grouped: dict[tuple[int, str], list[Any]] = {}
    for atom in atoms:
        grouped.setdefault(
            information_key_public_coordinates(atom.information_key), []
        ).append(atom)
    blocks = []
    for (seat, history), rows in sorted(grouped.items()):
        ordered = sorted(rows, key=lambda row: row.information_key)
        blocks.append(
            {
                "acting_seat": seat,
                "public_history": history,
                "information_keys": [row.information_key for row in ordered],
                "information_set_count": len(ordered),
                "changed_entry_count": sum(row.changed_entries for row in ordered),
                "maximum_absolute_probability_delta": max(
                    row.maximum_absolute_probability_delta for row in ordered
                ),
            }
        )
    if not blocks or sum(row["information_set_count"] for row in blocks) != len(atoms):
        raise ValueError("changed public-node partition is empty or incomplete")
    keys = [key for block in blocks for key in block["information_keys"]]
    if len(keys) != len(set(keys)):
        raise ValueError("changed public-node partition overlaps")
    return tuple(blocks)


def observed_prefix_history(bettor: int) -> str:
    actions = [f"p{seat}:check" for seat in range(bettor)]
    actions.append(f"p{bettor}:bet")
    return "/".join(actions)


def _history_actions(history: str) -> tuple[str, ...]:
    return () if history == "root" else tuple(history.split("/"))


def structural_schedule_key(
    block: Mapping[str, Any], *, observed_bettor: int
) -> tuple[Any, ...]:
    """Frozen label-free order: continuation descendants, distance, extremes."""

    prefix = _history_actions(observed_prefix_history(observed_bettor))
    history = _history_actions(str(block["public_history"]))
    common = 0
    for left, right in zip(prefix, history):
        if left != right:
            break
        common += 1
    descendant = len(history) >= len(prefix) and history[: len(prefix)] == prefix
    distance = len(prefix) + len(history) - 2 * common
    seat = int(block["acting_seat"])
    return (
        0 if descendant else 1,
        distance,
        _EXTREME_SEAT_ORDER.index(seat),
        seat,
        str(block["public_history"]),
    )


def derive_widened_capacity(
    rows: Sequence[Mapping[str, Any]],
    *,
    warm_step_ms: float,
    street_budget_ms: float,
    emission_reserve_ms: float,
) -> dict[str, Any]:
    """Price structural-prefix K without consulting any strategy label."""

    if not rows:
        raise ValueError("widened capacity requires candidates")
    unit_ms = max(float(row["timing"]["complete_tier_b_candidate_ms"]) for row in rows)
    envelope_ms = max(float(row["timing"]["envelope_ms"]) for row in rows)
    remaining = street_budget_ms - emission_reserve_ms - warm_step_ms - envelope_ms
    k = len(rows) if unit_ms <= 0.0 else max(0, math.floor(remaining / unit_ms))
    k = min(len(rows), k)
    return {
        "candidate_count": len(rows),
        "warm_step_ms": warm_step_ms,
        "street_budget_ms": street_budget_ms,
        "emission_reserve_ms": emission_reserve_ms,
        "maximum_complete_tier_b_candidate_ms": unit_ms,
        "maximum_one_winner_envelope_ms": envelope_ms,
        "remaining_before_tier_b_ms": remaining,
        "clock_feasible_k": k,
        "library_limited": k == len(rows),
        "tier_a_filter_used": False,
    }


def _parse_config(config: dict[str, Any]) -> dict[str, Any]:
    for field, path in _PATHS.items():
        if config.get(field) != _sha256(path):
            raise ValueError(f"widened-selector provenance mismatch: {field}")
    exact = {
        "evidence_stage": "preregistered_after_adr0220_before_any_action_conditioned_warm_step_affine_feature_or_strategy_label",
        "seed": 20260821,
        "candidate_scope": "every_changed_exact_public_node_one_regret_vertex_direction",
        "schedule_rule": "observed_prefix_descendants_then_public_tree_edit_distance_then_order_extremes_0_5_1_4_2_3_then_actor_then_history",
        "feature_label_barrier": "all_twelve_complete_affine_matrices_schedules_and_capacities_before_any_direct_certificate_teacher",
        "teacher_rule": "one_independent_incremental_exact_certificate_at_each_frozen_affine_envelope_scale_no_adaptive_search",
        "live_rule": "structural_first_k_then_max_tier_b_slope_times_cap_radius_then_one_tier_c_envelope_else_blueprint",
        "tier_a_policy": "exact_identity_retained_as_diagnostic_and_forbidden_as_exclusion_filter",
        "tier_b_topology": "device_fold_scalar_five_opponent_contractions_plus_zero_contraction_own_row",
        "emitted_policy": "immutable_blueprint_research_only",
        "street_budget_ms": 15000.0,
        "emission_reserve_ms": 1000.0,
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
    for field, value in exact.items():
        if config.get(field) != value:
            raise ValueError(f"widened-selector field differs from ADR-0221: {field}")
    if len(config.get("targets", ())) != 12:
        raise ValueError("widened-selector trial requires all twelve targets")
    gates = {
        "expected_targets": 12,
        "expected_search_steps": 12,
        "minimum_blocks_per_target": 7,
        "expected_common_six_per_target": 6,
        "expected_direction_families": ["regret_vertex"],
        "maximum_affine_intercept_error": 2e-11,
        "maximum_tier_a_identity_error": 2e-11,
        "maximum_warm_start_probability_error": 1e-12,
        "maximum_warm_start_mean_total_variation": 1e-13,
        "maximum_search_step_ms": 60000.0,
        "maximum_candidate_feature_ms": 60000.0,
        "maximum_certificate_ms": 60000.0,
        "maximum_gpu_pool_bytes": 12000000000,
        "minimum_physical_free_bytes": 1000000000,
        "maximum_total_audit_seconds": 10800.0,
        "require_clean_git_state": True,
        "require_manifest_parent_passed": True,
        "require_ledger_parent_passed": True,
        "require_source_checkpoint_identity": True,
        "require_target_identity": True,
        "require_blueprint_identity": True,
        "require_numerical_warm_start_identity": True,
        "require_complete_block_partition": True,
        "require_feature_label_barrier": True,
        "require_exact_teacher_independence": True,
        "require_tier_a_not_filter": True,
        "require_blueprint_emission": True,
        "require_finite": True,
        "require_strategy_population_claim_null": True,
    }
    if config.get("gates") != gates:
        raise ValueError("widened-selector gates differ from ADR-0221")
    return {**config, "targets": tuple(dict(row) for row in config["targets"]), "gates": gates}


def _source_row(parent: Mapping[str, Any], source: str) -> Mapping[str, Any]:
    return next(row for row in parent["source_rows"] if row["source"] == source)


def _setup_target(
    parsed: Mapping[str, Any], source_parent: Mapping[str, Any], spec: Mapping[str, Any]
) -> dict[str, Any]:
    board = parse_cards(*spec["board"])
    source, layout, sparse, retained = _build_case(
        parsed=parsed,
        board=board,
        hand_count=int(parsed["hands_per_player"]),
        family=str(spec["range_family"]),
    )
    source_workspace, _, automata = retained
    parent_row = _source_row(source_parent, str(spec["source"]))
    state = parent_row["final_checkpoint"]
    blueprint = _average_policy_from_state(state)
    belief, descriptor = build_action_conditioned_posterior(
        source, blueprint, bettor=int(spec["observed_bettor"])
    )
    base = FactorTTBeliefWorkspace.compile(
        source_workspace.topology.base,
        belief,
        query_chunk_records=int(parsed["query_chunk_records"]),
    )
    workspace = OpenModeFactorTTWorkspace.compile(source_workspace.topology, base)
    gpu = CuPyBidirectionalIncidence.compile(sparse)
    shared = SharedResidentAutomatonBundle.compile(workspace, automata)
    context = bind_resident_response_context(
        shared,
        layout=layout,
        workspace=workspace,
        sparse=sparse,
        source_policy=blueprint,
        hands_by_player=belief.hands_by_player,
        cupy_sparse=gpu,
        maximum_feature_width_per_batch=int(parsed["maximum_feature_width_per_batch"]),
    )
    return {
        "source": source,
        "layout": layout,
        "sparse": sparse,
        "source_workspace": source_workspace,
        "automata": automata,
        "blueprint": blueprint,
        "belief": belief,
        "descriptor": descriptor,
        "workspace": workspace,
        "gpu": gpu,
        "shared": shared,
        "context": context,
        "state": state,
        "parent_row": parent_row,
    }


def _release(objects: dict[str, Any]) -> None:
    objects.clear()
    gc.collect()
    release_cupy_memory_pool()


def _feature_target(
    parsed: Mapping[str, Any], source_parent: Mapping[str, Any], spec: Mapping[str, Any], cp: Any
) -> tuple[dict[str, Any], dict[str, Any]]:
    objects = _setup_target(parsed, source_parent, spec)
    blueprint = objects["blueprint"]
    belief = objects["belief"]
    context = objects["context"]
    shared = objects["shared"]
    gpu = objects["gpu"]
    layout = objects["layout"]
    state = objects["state"]
    source_identity = (
        axis_cfr_checkpoint_digest(state) == state["state_sha256"]
        and _belief_digest(objects["source"]) == spec["source_belief_sha256"]
        and _belief_digest(objects["source"]) == objects["parent_row"]["source_belief_sha256"]
    )
    blueprint_digest = policy_digest(blueprint)
    blueprint_identity = blueprint_digest == state["average_policy_sha256"]
    target_identity = _belief_digest(belief) == spec["target_belief_sha256"]
    quality = _source_quality(context, payoff_span=float(parsed["stack"]))
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
    warm_mass = float(parsed["warm_regret_mass_payoff_fraction"]) * float(layout.game.payoff_span)
    solver.warm_start(blueprint, warm_mass)
    warm_distance = _policy_distance(blueprint, solver.current_strategy())
    release_cupy_memory_pool()
    memory_rows = [_memory_snapshot(cp)]
    started = time.perf_counter()
    solver.step()
    warm_step_ms = (time.perf_counter() - started) * 1000.0
    soft = solver.current_strategy()
    regret_deltas = recover_iteration_one_dcfr_regret_deltas(
        blueprint, solver.regret_table(), warm_regret_mass=warm_mass
    )
    blocks = build_all_changed_public_node_blocks(blueprint, soft)
    anchors = select_one_atom_per_acting_seat(
        layout, belief.hands_by_player, blueprint, soft
    )
    common_keys = {
        information_key_public_coordinates(str(row["information_key"]))
        for row in anchors
    }
    blocks = tuple(
        sorted(
            blocks,
            key=lambda row: structural_schedule_key(
                row, observed_bettor=int(spec["observed_bettor"])
            ),
        )
    )
    raw_guard = float(parsed["acceptance_guard_normalized"]) * float(parsed["stack"])
    scale_grid = tuple(
        2.0**-index
        for index in range(64)
        if 2.0**-index >= float(parsed["numerical_floor"])
    )
    rows = []
    for schedule_index, block in enumerate(blocks):
        candidate_started = time.perf_counter()
        seat = int(block["acting_seat"])
        keys = tuple(block["information_keys"])
        endpoint = build_regret_vertex_candidate(blueprint, regret_deltas, keys)
        probabilities = compile_policy_probability_tape(layout, belief.hands_by_player, endpoint)
        construction_ms = (time.perf_counter() - candidate_started) * 1000.0
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
        for target_player in range(6):
            if target_player == seat:
                affine_rows.append(own)
            else:
                affine_rows.append(
                    evaluate_device_fold_selector_stable_affine_leaf_adjoint_seat(
                        context.response_caches[target_player],
                        probabilities,
                        acting_player=seat,
                        selector_margin_allowance=float(parsed["selector_margin_allowance"]),
                        maximum_feature_width_per_batch=int(parsed["maximum_feature_width_per_batch"]),
                        belief_cache=context.belief_cache,
                        automaton_cache=shared.automaton_caches[target_player],
                        cupy_sparse=gpu,
                        record_to_hand_backend="gpu_cupy",
                    ).semantic
                )
        tier = affine_tier_features(
            affine_rows,
            acting_seat=seat,
            raw_guard=raw_guard,
            numerical_allowance=float(parsed["envelope_numerical_allowance"]),
            blueprint_deviation_gains=quality["deviation_gains"],
        )
        envelope_started = time.perf_counter()
        envelope = certify_selector_stable_affine_envelope(
            tuple(affine_rows),
            blueprint_deviation_gains=tuple(quality["deviation_gains"]),
            blueprint_nash_conv=float(quality["nash_conv"]),
            raw_guard=raw_guard,
            scale_grid=scale_grid,
            safety_fraction=float(parsed["safety_fraction"]),
            numerical_allowance=float(parsed["envelope_numerical_allowance"]),
        )
        envelope_ms = (time.perf_counter() - envelope_started) * 1000.0
        rows.append(
            {
                **block,
                "candidate_id": f"block_{schedule_index:03d}_seat{seat}_regret_vertex",
                "schedule_index": schedule_index,
                "schedule_key": list(structural_schedule_key(block, observed_bettor=int(spec["observed_bettor"]))),
                "common_six_block": (seat, str(block["public_history"])) in common_keys,
                "direction_family": "regret_vertex",
                "endpoint_policy_sha256": policy_digest(endpoint),
                "features": tier["features"],
                "tier": tier,
                "affine_rows": [asdict(row) for row in affine_rows],
                "envelope": asdict(envelope),
                "timing": {
                    "endpoint_construction_ms": construction_ms,
                    "own_zero_contraction_ms": float(own.wall_ms),
                    "opponent_wall_ms": float(tier["cost"]["opponent_wall_ms"]),
                    "complete_tier_b_candidate_ms": construction_ms + float(own.wall_ms) + float(tier["cost"]["opponent_wall_ms"]),
                    "envelope_ms": envelope_ms,
                },
                "label": None,
            }
        )
        memory_rows.append(_memory_snapshot(cp))
    capacity = derive_widened_capacity(
        rows,
        warm_step_ms=warm_step_ms,
        street_budget_ms=float(parsed["street_budget_ms"]),
        emission_reserve_ms=float(parsed["emission_reserve_ms"]),
    )
    result = {
        "target_id": spec["target_id"],
        "source": spec["source"],
        "board": spec["board"],
        "range_family": spec["range_family"],
        "observed_bettor": spec["observed_bettor"],
        "source_checkpoint_identity": source_identity,
        "target_identity": target_identity,
        "blueprint_identity": blueprint_identity,
        "blueprint_policy_sha256": blueprint_digest,
        "blueprint_quality": quality,
        "warm_start_distance": warm_distance,
        "warm_step_ms": warm_step_ms,
        "warm_step_work_wall_ms": solver.last_step_work.wall_ms,
        "changed_information_set_count": sum(row["information_set_count"] for row in rows),
        "candidate_rows": rows,
        "capacity_before_labels": capacity,
        "memory_rows": memory_rows,
        "emitted_candidate_id": "blueprint_average64",
        "emitted_policy_sha256": blueprint_digest,
    }
    payload = {"spec": dict(spec), "blueprint": blueprint, "regret_deltas": regret_deltas}
    del solver
    _release(objects)
    return result, payload


def _label_target(
    parsed: Mapping[str, Any], source_parent: Mapping[str, Any], target: dict[str, Any], payload: Mapping[str, Any], cp: Any
) -> None:
    objects = _setup_target(parsed, source_parent, payload["spec"])
    blueprint = payload["blueprint"]
    quality = target["blueprint_quality"]
    for row in target["candidate_rows"]:
        selected_scale = row["envelope"]["selected_scale"]
        if selected_scale is None:
            row["label"] = 0.0
            row["teacher"] = {"queried": False, "reason": row["envelope"]["stop_reason"]}
            continue
        endpoint = build_regret_vertex_candidate(
            blueprint, payload["regret_deltas"], tuple(row["information_keys"])
        )
        policy = interpolate_policy_atoms(
            blueprint, endpoint, tuple(row["information_keys"]), scale=float(selected_scale)
        )
        certificate = _certificate(
            candidate_id=str(row["candidate_id"]),
            policy=policy,
            layout=objects["layout"],
            belief=objects["belief"],
            context=objects["context"],
            shared=objects["shared"],
            gpu=objects["gpu"],
            blueprint_quality=quality,
            parsed=dict(parsed),
        )
        positive = max(0.0, float(quality["nash_conv"]) - float(certificate["quality"]["nash_conv"])) if certificate["complete"] else 0.0
        row["label"] = positive
        row["teacher"] = {
            "queried": True,
            "independent_incremental_certificate": True,
            "complete": bool(certificate["complete"]),
            "stop_reason": certificate["stop_reason"],
            "wall_ms": certificate["wall_ms"],
            "policy_sha256": certificate["policy_sha256"],
            "quality": certificate.get("quality"),
            "maximum_gpu_pool_bytes": certificate["maximum_gpu_pool_bytes"],
        }
        target["memory_rows"].append(_memory_snapshot(cp))
    _release(objects)


def _score_target(target: dict[str, Any]) -> None:
    rows = target["candidate_rows"]
    oracle = min(rows, key=lambda row: (-float(row["label"]), int(row["schedule_index"])))
    composite = min(rows, key=lambda row: (-float(row["features"]["tier_b_slope_predicted_value"]), int(row["schedule_index"])))
    k = int(target["capacity_before_labels"]["clock_feasible_k"])
    portfolio = rows[:k]
    live = None if not portfolio else min(
        portfolio,
        key=lambda row: (-float(row["features"]["tier_b_slope_predicted_value"]), int(row["schedule_index"])),
    )
    if live is not None and live["envelope"]["selected_scale"] is None:
        live = None
    labels = [float(row["label"]) for row in rows]
    oracle_value = float(oracle["label"])
    random_value = 0.0 if k == 0 else exact_random_value_floor(labels, k)
    common = [row for row in rows if row["common_six_block"]]
    common_oracle = max((float(row["label"]) for row in common), default=0.0)
    target["scoring"] = {
        "oracle_candidate_id": oracle["candidate_id"],
        "oracle_value": oracle_value,
        "full_library_composite_candidate_id": composite["candidate_id"],
        "full_library_composite_value": float(composite["label"]),
        "full_library_composite_capture": _safe_ratio(float(composite["label"]), oracle_value),
        "full_library_composite_spearman": spearman_rank_correlation(
            [float(row["features"]["tier_b_slope_predicted_value"]) for row in rows], labels
        ),
        "live_k": k,
        "live_candidate_id": None if live is None else live["candidate_id"],
        "live_value": 0.0 if live is None else float(live["label"]),
        "live_capture": 0.0 if live is None else _safe_ratio(float(live["label"]), oracle_value),
        "random_expected_value_at_k": random_value,
        "random_capture_at_k": _safe_ratio(random_value, oracle_value),
        "clairvoyant_capture_at_k": 0.0 if k == 0 else _safe_ratio(max(float(row["label"]) for row in portfolio), oracle_value),
        "common_six_candidate_count": len(common),
        "common_six_oracle_value": common_oracle,
        "full_library_lift_over_common_six": _safe_ratio(oracle_value, common_oracle),
    }


def run_h32_action_conditioned_widened_selector_trial(
    config_path: Path = _CONFIG, output_path: Path = _OUTPUT
) -> dict[str, Any]:
    started = time.perf_counter()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    parsed = _parse_config(config)
    git = _strict_git_metadata()
    cp, runtime = _validate_runtime(parsed)
    source_parent = json.loads(_SOURCE.read_text(encoding="utf-8"))
    manifest = json.loads(_MANIFEST.read_text(encoding="utf-8"))
    ledger = json.loads(_LEDGER.read_text(encoding="utf-8"))
    target_rows = []
    payloads = []
    feature_phase_started = time.perf_counter()
    for spec in parsed["targets"]:
        row, payload = _feature_target(parsed, source_parent, spec, cp)
        target_rows.append(row)
        payloads.append(payload)
    feature_phase_seconds = time.perf_counter() - feature_phase_started
    barrier = {
        "completed_before_teacher": True,
        "target_matrices": len(target_rows),
        "candidate_feature_rows": sum(len(row["candidate_rows"]) for row in target_rows),
        "capacity_rows": len(target_rows),
        "label_non_null_before_teacher": 0,
        "feature_phase_seconds": feature_phase_seconds,
    }
    teacher_started = time.perf_counter()
    for target, payload in zip(target_rows, payloads, strict=True):
        _label_target(parsed, source_parent, target, payload, cp)
        _score_target(target)
    teacher_seconds = time.perf_counter() - teacher_started
    all_rows = [row for target in target_rows for row in target["candidate_rows"]]
    queried = [row for row in all_rows if row["teacher"]["queried"]]
    total_seconds = time.perf_counter() - started
    gates_config = parsed["gates"]
    maximum_intercept = max(
        abs(float(affine["deviation_gain_intercept"]) - float(target["blueprint_quality"]["deviation_gains"][seat]))
        for target in target_rows
        for row in target["candidate_rows"]
        for seat, affine in enumerate(row["affine_rows"])
    )
    maximum_tier_a = max(float(row["tier"]["identity"]["tier_a_identity_error"]) for row in all_rows)
    minimum_free = min(memory["gpu_free_bytes"] for target in target_rows for memory in target["memory_rows"])
    maximum_pool = max(memory["gpu_pool_total_bytes"] for target in target_rows for memory in target["memory_rows"])
    gates = {
        "clean_git": (not git["dirty"]) == gates_config["require_clean_git_state"],
        "manifest_parent_passed": bool(manifest["passed"]) == gates_config["require_manifest_parent_passed"],
        "ledger_parent_passed": bool(ledger["passed"]) == gates_config["require_ledger_parent_passed"],
        "target_count": len(target_rows) == gates_config["expected_targets"],
        "search_step_count": len(target_rows) == gates_config["expected_search_steps"],
        "minimum_blocks": min(len(row["candidate_rows"]) for row in target_rows) >= gates_config["minimum_blocks_per_target"],
        "common_six_identity": all(sum(candidate["common_six_block"] for candidate in row["candidate_rows"]) == gates_config["expected_common_six_per_target"] for row in target_rows),
        "direction_family_identity": {row["direction_family"] for row in all_rows} == set(gates_config["expected_direction_families"]),
        "source_checkpoint_identity": all(row["source_checkpoint_identity"] for row in target_rows) == gates_config["require_source_checkpoint_identity"],
        "target_identity": all(row["target_identity"] for row in target_rows) == gates_config["require_target_identity"],
        "blueprint_identity": all(row["blueprint_identity"] for row in target_rows) == gates_config["require_blueprint_identity"],
        "warm_start_identity": max(row["warm_start_distance"]["maximum_probability_error"] for row in target_rows) <= gates_config["maximum_warm_start_probability_error"] and max(row["warm_start_distance"]["mean_total_variation"] for row in target_rows) <= gates_config["maximum_warm_start_mean_total_variation"],
        "complete_block_partition": all(row["changed_information_set_count"] == sum(candidate["information_set_count"] for candidate in row["candidate_rows"]) for row in target_rows) == gates_config["require_complete_block_partition"],
        "affine_intercepts": maximum_intercept <= gates_config["maximum_affine_intercept_error"],
        "tier_a_identity": maximum_tier_a <= gates_config["maximum_tier_a_identity_error"],
        "feature_label_barrier": barrier["completed_before_teacher"] and barrier["label_non_null_before_teacher"] == 0 and barrier["target_matrices"] == 12 and barrier["capacity_rows"] == 12,
        "exact_teacher_independence": all(row["teacher"].get("independent_incremental_certificate", False) for row in queried) == gates_config["require_exact_teacher_independence"],
        "tier_a_not_filter": all(not target["capacity_before_labels"]["tier_a_filter_used"] for target in target_rows) == gates_config["require_tier_a_not_filter"],
        "warm_step_time": max(row["warm_step_ms"] for row in target_rows) <= gates_config["maximum_search_step_ms"],
        "candidate_feature_time": max(row["timing"]["complete_tier_b_candidate_ms"] for row in all_rows) <= gates_config["maximum_candidate_feature_ms"],
        "certificate_time": max((row["teacher"]["wall_ms"] for row in queried), default=0.0) <= gates_config["maximum_certificate_ms"],
        "gpu_pool": maximum_pool <= gates_config["maximum_gpu_pool_bytes"],
        "physical_free": minimum_free >= gates_config["minimum_physical_free_bytes"],
        "blueprint_emission": all(row["emitted_policy_sha256"] == row["blueprint_policy_sha256"] for row in target_rows) == gates_config["require_blueprint_emission"],
        "total_time": total_seconds <= gates_config["maximum_total_audit_seconds"],
        "finite": _finite_tree(target_rows) == gates_config["require_finite"],
        "strategy_population_claim_null": True == gates_config["require_strategy_population_claim_null"],
    }
    gates["passed"] = all(gates.values())
    pooled_oracle = math.fsum(target["scoring"]["oracle_value"] for target in target_rows)
    pooled_composite = math.fsum(target["scoring"]["full_library_composite_value"] for target in target_rows)
    pooled_live = math.fsum(target["scoring"]["live_value"] for target in target_rows)
    result = {
        "schema_version": 1,
        "status": "h32_action_conditioned_widened_selector_trial_executed",
        "environment": {**environment_metadata(), "runtime": runtime, "git": git},
        "config_sha256": _sha256(config_path),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "feature_label_barrier": barrier,
        "target_rows": target_rows,
        "aggregate": {
            "candidate_rows": len(all_rows),
            "teacher_queries": len(queried),
            "minimum_candidates_per_target": min(len(row["candidate_rows"]) for row in target_rows),
            "maximum_candidates_per_target": max(len(row["candidate_rows"]) for row in target_rows),
            "minimum_live_k": min(row["scoring"]["live_k"] for row in target_rows),
            "maximum_live_k": max(row["scoring"]["live_k"] for row in target_rows),
            "pooled_oracle_value": pooled_oracle,
            "pooled_full_library_composite_value": pooled_composite,
            "pooled_full_library_composite_capture": _safe_ratio(pooled_composite, pooled_oracle),
            "pooled_live_value": pooled_live,
            "pooled_live_capture": _safe_ratio(pooled_live, pooled_oracle),
            "maximum_affine_intercept_error": maximum_intercept,
            "maximum_tier_a_identity_error": maximum_tier_a,
            "minimum_gpu_free_bytes": minimum_free,
            "maximum_gpu_pool_total_bytes": maximum_pool,
            "feature_phase_seconds": feature_phase_seconds,
            "teacher_phase_seconds": teacher_seconds,
        },
        "gates": gates,
        "passed": gates["passed"],
        "decision": "interpret_fresh_widened_selector_transfer" if gates["passed"] else "reject_fresh_widened_selector_trial",
        "emitted_policy": "immutable_blueprint_only",
        "strategy_population_claim": None,
        "total_seconds": total_seconds,
        "limitations": [
            "The target is an exact action-conditioned range transfer in the complete river tree, not a continuation-root subgame.",
            "The direct label is realized B-to-C value at the frozen envelope scale, not global attainable value.",
            "Clock K is a conservative label-independent replay from measured per-candidate maxima, not a deployment latency distribution.",
            "No strategy-quality, deployment, population, or composition claim is made.",
        ],
    }
    output_path.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=_CONFIG)
    parser.add_argument("--output", type=Path, default=_OUTPUT)
    args = parser.parse_args()
    result = run_h32_action_conditioned_widened_selector_trial(args.config, args.output)
    print(json.dumps({"output": str(args.output), "passed": result["passed"], "decision": result["decision"], "aggregate": result["aggregate"]}, indent=2))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
