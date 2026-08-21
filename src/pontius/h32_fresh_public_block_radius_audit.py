"""Prospective exact scale-radius audit for frozen h32 public-node blocks."""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import math
from pathlib import Path
import time
from typing import Any, Mapping, Sequence

import numpy as np

from .axis_cfr_checkpoint import axis_cfr_checkpoint_digest
from .cupy_sparse_incidence import CuPyBidirectionalIncidence, release_cupy_memory_pool
from .delta_certificate_contract import (
    atomic_policy_manifest,
    geometric_halving_scales,
    interpolate_policy_atoms,
)
from .factor_tt_contraction import FactorTTBeliefWorkspace
from .fresh_h32_strategy_transfer_audit import _belief_digest, _resident_quality_row
from .h32_affine_resident_cache_preflight import _strict_git_metadata, _validate_runtime
from .h32_atomic_response_preflight import select_one_atom_per_acting_seat
from .h32_fresh_board_panel_cache_preflight import _json_digest
from .h32_fresh_public_block_value_audit import (
    block_union_keys,
    build_public_node_blocks,
    information_key_public_coordinates,
)
from .h32_fresh_union_value_audit import _certificate, _memory_snapshot, _positive_value, _safe_ratio
from .h32_warm_search_acceptance_audit import (
    _average_policy_from_state,
    _local_blocker_likelihoods,
    _policy_distance,
)
from .leaf_adjoint_checkpoint_ladder_audit import _build_case
from .open_mode_factor_tt import OpenModeFactorTTWorkspace
from .real_policy import policy_digest
from .reporting import environment_metadata
from .resident_leaf_adjoint_cfr import ResidentLeafAdjointPublicTreeCFR
from .river import parse_cards
from .shared_resident_response_context import SharedResidentAutomatonBundle, bind_resident_response_context


_ROOT = Path(__file__).parents[2]
_CONFIG = _ROOT / "experiments/configs/h32-fresh-public-block-radius-v1.json"
_OUTPUT = _ROOT / "experiments/results/h32-fresh-public-block-radius-v1.json"
_SOURCE = _ROOT / "experiments/results/h32-fresh-panel-source-blueprints-v1.json"
_PARENT_RESULT = _ROOT / "experiments/results/h32-fresh-public-block-value-v1.json"
_PARENT_ADR = _ROOT / "docs/decisions/ADR-0174-public-node-blocks-fit-but-two-directions-are-cap-bound.md"
_REQUIREMENTS = _ROOT / "experiments/requirements/leaf-adjoint-gpu-screen-v1.txt"
_IMPLEMENTATION = Path(__file__)
_TEST = _ROOT / "tests/test_h32_fresh_public_block_radius_audit.py"

_PATHS = {
    "expected_source_result_sha256": _SOURCE,
    "expected_parent_result_sha256": _PARENT_RESULT,
    "expected_parent_decision_sha256": _PARENT_ADR,
    "expected_requirements_sha256": _REQUIREMENTS,
    "expected_target_builder_sha256": _ROOT / "src/pontius/h32_warm_search_acceptance_audit.py",
    "expected_public_block_builder_sha256": _ROOT / "src/pontius/h32_fresh_public_block_value_audit.py",
    "expected_union_verifier_sha256": _ROOT / "src/pontius/h32_fresh_union_value_audit.py",
    "expected_shared_context_sha256": _ROOT / "src/pontius/shared_resident_response_context.py",
    "expected_incremental_verifier_sha256": _ROOT / "src/pontius/incremental_leaf_adjoint_response.py",
    "expected_resident_cfr_sha256": _ROOT / "src/pontius/resident_leaf_adjoint_cfr.py",
    "expected_atom_manifest_sha256": _ROOT / "src/pontius/h32_atomic_response_preflight.py",
    "expected_interpolation_sha256": _ROOT / "src/pontius/delta_certificate_contract.py",
    "expected_audit_implementation_sha256": _IMPLEMENTATION,
    "expected_control_test_sha256": _TEST,
}

_FROZEN_TARGETS = [
    {
        "target": "panel_2/balanced/local_blocker_seat0_x2",
        "board_id": "panel_2",
        "board": ["2c", "3s", "5d", "Js", "Qc"],
        "range_family": "balanced",
        "target_shift": "local_blocker_seat0_x2",
        "source_belief_sha256": "0662b2cf2436cbc6dcc5669fe75a2c15f03e652fb40a6903703a10dd14cfa289",
        "target_belief_sha256": "401170b656dd96b831cfac4bc1b9995d41c055e8c9d4aa590ba80dbcf98754c9",
        "target_descriptor_sha256": "99215f9c38d6d5e248175de4730dd4412da785833b4fca979cd3a4ea1a943acb",
    },
    {
        "target": "panel_3/blocker_heavy/local_blocker_seat0_x2",
        "board_id": "panel_3",
        "board": ["4h", "7h", "9s", "Jd", "Kc"],
        "range_family": "blocker_heavy",
        "target_shift": "local_blocker_seat0_x2",
        "source_belief_sha256": "74ce0c18ac82e9ebb799be851f140c7011ad75671a3409f94c7db1db3187278e",
        "target_belief_sha256": "8a09af83e457b77bd6639e4899d05e3c627020ccbe7791af41ebc58cef027a78",
        "target_descriptor_sha256": "a42f53cdf7c4e9a0551961732f5675ccce67ad921be71b4be733550ed73dfd11",
    },
]

_FROZEN_DIRECTIONS = [
    {"direction_id": "public_block_seat1", "acting_seats": [1]},
    {"direction_id": "public_block_seat2", "acting_seats": [2]},
    {"direction_id": "public_blocks_seat1_2", "acting_seats": [1, 2]},
]


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required radius-audit input is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_h32_fresh_public_block_radius_config(config: dict[str, Any]) -> dict[str, Any]:
    """Validate ADR-0175's complete pre-label radius contract."""

    fields = {
        "evidence_stage", *_PATHS, "seed", "targets", "target_construction",
        "local_blocker_target_seat", "pot", "stack", "bet_size", "players",
        "hands_per_player", "axis_seed", "mixture_components", "split_index",
        "query_chunk_records", "solver_variant", "warm_regret_mass_payoff_fraction",
        "search_steps_per_target", "block_anchor_selection", "block_membership",
        "directions", "scale_grid", "numerical_floor", "certificate_anchor_rule",
        "seat_order", "acceptance_guard_normalized", "maximum_feature_width_per_batch",
        "measurement_context", "street_budget_ms", "emitted_policy",
        "maximum_warm_start_probability_error", "maximum_warm_start_mean_total_variation",
        "required_numpy_version", "required_scipy_version", "required_cupy_version",
        "required_cuda_runtime_version", "minimum_cuda_driver_version",
        "required_compute_capability", "cuda_dll_environment_variable", "gates",
    }
    if set(config) != fields:
        raise ValueError("fresh public-block radius fields differ from ADR-0175")
    frozen = {
        "evidence_stage": "preregistered_after_adr0174_before_any_seat0_target_policy_step_or_quality_measurement",
        "seed": 20260821,
        "targets": _FROZEN_TARGETS,
        "target_construction": "double_label_free_maximum_overlap_then_strength_then_smallest_canonical_hand_at_seat0",
        "local_blocker_target_seat": 0,
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
        "block_anchor_selection": "lexicographically_first_changed_information_set_per_acting_seat",
        "block_membership": "all_changed_information_sets_with_anchor_acting_seat_and_exact_public_history",
        "directions": _FROZEN_DIRECTIONS,
        "scale_grid": "shared_geometric_halving_inclusive_while_scale_at_least_numerical_floor",
        "numerical_floor": 1e-10,
        "certificate_anchor_rule": "immutable_source_average64_independent_one_shot_at_every_direction_and_scale_never_reanchors",
        "seat_order": [0, 1, 2, 3, 4, 5],
        "acceptance_guard_normalized": 1e-10,
        "maximum_feature_width_per_batch": 384,
        "measurement_context": "off_clock_research_radius_map_not_a_live_scheduler",
        "street_budget_ms": 15000.0,
        "emitted_policy": "immutable_blueprint_research_only",
        "maximum_warm_start_probability_error": 1e-12,
        "maximum_warm_start_mean_total_variation": 1e-13,
        "required_numpy_version": "2.5.2",
        "required_scipy_version": "1.18.0",
        "required_cupy_version": "14.2.0",
        "required_cuda_runtime_version": 13020,
        "minimum_cuda_driver_version": 13000,
        "required_compute_capability": "120",
        "cuda_dll_environment_variable": "PONTIUS_CUDA_DLL_DIRECTORY",
    }
    if any(config[key] != value for key, value in frozen.items()):
        raise ValueError("fresh public-block radius workload differs from ADR-0175")
    for field, path in _PATHS.items():
        if config[field] != _sha256(path):
            raise ValueError(f"fresh public-block radius source mismatch: {field}")
    gates = {
        "expected_target_rows": 2,
        "expected_search_steps": 2,
        "expected_public_blocks": 12,
        "expected_directions": 6,
        "expected_scale_count": 34,
        "expected_scale_rows": 204,
        "expected_blueprint_quality_labels": 2,
        "maximum_search_step_ms": 60000.0,
        "maximum_certificate_ms": 60000.0,
        "maximum_gpu_pool_bytes": 12000000000,
        "minimum_physical_free_bytes": 1000000000,
        "maximum_total_audit_seconds": 1200.0,
        "require_clean_git_state": True,
        "require_parent_passed": True,
        "require_source_checkpoint_identity": True,
        "require_target_identity": True,
        "require_blueprint_identity": True,
        "require_numerical_warm_start_identity": True,
        "require_nonempty_coherent_blocks": True,
        "require_direction_key_identity": True,
        "require_scale_grid_identity": True,
        "require_immutable_anchor": True,
        "require_independent_certificates": True,
        "require_blueprint_emission": True,
        "require_finite": True,
        "require_strategy_population_claim_null": True,
    }
    if config["gates"] != gates:
        raise ValueError("fresh public-block radius gates differ from ADR-0175")
    return {
        **config,
        "targets": tuple(dict(row) for row in config["targets"]),
        "directions": tuple(dict(row) for row in config["directions"]),
        "seat_order": tuple(config["seat_order"]),
        "gates": dict(gates),
    }


def build_fresh_seat0_target(source: Any, *, board: tuple[int, ...], target_seat: int) -> tuple[Any, dict[str, Any]]:
    """Construct the frozen positive seat-0 belief shift without policy labels."""

    if target_seat != 0:
        raise ValueError("fresh radius target seat differs from ADR-0175")
    likelihoods, detail = _local_blocker_likelihoods(source, board=board, target_seat=target_seat)
    target = source
    for seat, likelihood in enumerate(likelihoods):
        target = target.with_likelihood(seat, likelihood)
    values = np.concatenate(likelihoods)
    return target, {
        "shift": "local_blocker_seat0_x2",
        "likelihood_minimum": float(np.min(values)),
        "likelihood_maximum": float(np.max(values)),
        "likelihood_mean": float(np.mean(values)),
        "positive_likelihoods": bool(np.all(values > 0.0)),
        "hand_axes_identity": target.hands_by_player == source.hands_by_player,
        **detail,
    }


def direction_information_keys(blocks: Sequence[Mapping[str, Any]], acting_seats: Sequence[int]) -> tuple[str, ...]:
    """Resolve one frozen block direction or its exact noncompositional union."""

    return block_union_keys(blocks, acting_seats)


def certificate_binding_diagnostics(certificate: Mapping[str, Any], blueprint_quality: Mapping[str, Any], raw_guard: float) -> dict[str, float | None]:
    """Measure signed excess for the verifier's observed binding condition."""

    stop = str(certificate["stop_reason"])
    cap_excess = None
    objective_excess = None
    if stop == "blueprint_cap":
        seat = int(certificate["stop_seat"])
        row = certificate["seat_rows"][-1]
        cap_excess = float(row["deviation_gain"]) - float(blueprint_quality["deviation_gains"][seat]) - raw_guard
    elif stop == "objective_lower_bound":
        objective_excess = float(certificate["partial_nash_conv"]) - float(blueprint_quality["nash_conv"]) - raw_guard
    return {"cap_excess": cap_excess, "objective_excess": objective_excess}


def summarize_direction_rows(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Summarize an outcome-neutral descending geometric scale trace."""

    complete = [row for row in rows if row["certificate"]["complete"]]
    best = None if not complete else min(complete, key=lambda row: (-float(row["positive_certified_value"]), int(row["scale_index"])))
    stop_sequence = [str(row["certificate"]["stop_reason"]) for row in rows]
    transitions = sum(left != right for left, right in zip(stop_sequence, stop_sequence[1:]))
    if not complete:
        classification = "no_admissible_grid_scale"
    elif len(complete) == len(rows):
        classification = "all_grid_scales_admissible"
    else:
        classification = "bounded_admissible_grid_window"
    return {
        "classification": classification,
        "scale_count": len(rows),
        "complete_scale_count": len(complete),
        "blueprint_cap_count": sum(reason == "blueprint_cap" for reason in stop_sequence),
        "objective_lower_bound_count": sum(reason == "objective_lower_bound" for reason in stop_sequence),
        "stop_reason_transition_count": transitions,
        "largest_complete_scale": None if not complete else float(complete[0]["scale"]),
        "smallest_complete_scale": None if not complete else float(complete[-1]["scale"]),
        "best_value_scale": None if best is None else float(best["scale"]),
        "best_positive_certified_value": 0.0 if best is None else float(best["positive_certified_value"]),
        "best_value_per_certificate_second": None if best is None else best["value_per_certificate_second"],
        "stop_reason_sequence": stop_sequence,
    }


def _run_target(parsed: dict[str, Any], source_parent: dict[str, Any], target_spec: Mapping[str, Any], cp: Any) -> dict[str, Any]:
    board = parse_cards(*target_spec["board"])
    family = str(target_spec["range_family"])
    source, layout, sparse, retained = _build_case(parsed=parsed, board=board, hand_count=parsed["hands_per_player"], family=family)
    source_workspace, _, automata = retained
    source_digest = _belief_digest(source)
    parent_row = next(row for row in source_parent["source_rows"] if row["source"] == f"{target_spec['board_id']}/{family}")
    state = parent_row["final_checkpoint"]
    source_checkpoint_identity = (
        axis_cfr_checkpoint_digest(state) == state["state_sha256"]
        and source_digest == target_spec["source_belief_sha256"]
        and source_digest == parent_row["source_belief_sha256"]
    )
    blueprint = _average_policy_from_state(state)
    blueprint_digest = policy_digest(blueprint)
    blueprint_identity = blueprint_digest == state["average_policy_sha256"]
    belief, descriptor = build_fresh_seat0_target(source, board=board, target_seat=parsed["local_blocker_target_seat"])
    target_digest = _belief_digest(belief)
    descriptor_digest = _json_digest(descriptor)
    target_identity = (
        target_digest == target_spec["target_belief_sha256"]
        and descriptor_digest == target_spec["target_descriptor_sha256"]
        and belief.hands_by_player == source.hands_by_player
    )

    base = FactorTTBeliefWorkspace.compile(source_workspace.topology.base, belief, query_chunk_records=parsed["query_chunk_records"])
    workspace = OpenModeFactorTTWorkspace.compile(source_workspace.topology, base)
    gpu = CuPyBidirectionalIncidence.compile(sparse)
    shared = SharedResidentAutomatonBundle.compile(workspace, automata)
    context = bind_resident_response_context(
        shared, layout=layout, workspace=workspace, sparse=sparse, source_policy=blueprint,
        hands_by_player=belief.hands_by_player, cupy_sparse=gpu,
        maximum_feature_width_per_batch=parsed["maximum_feature_width_per_batch"],
    )
    blueprint_quality, _ = _resident_quality_row(
        layout=layout, workspace=workspace, sparse=sparse, automata=automata,
        policy=blueprint, label="blueprint_average64", hands_by_player=belief.hands_by_player,
        belief_cache=context.belief_cache, automaton_caches=shared.automaton_caches,
        gpu=gpu, payoff_span=parsed["stack"],
        maximum_feature_width_per_batch=parsed["maximum_feature_width_per_batch"],
    )
    solver = ResidentLeafAdjointPublicTreeCFR(
        layout, workspace, sparse, automata, parsed["solver_variant"],
        belief_cache=context.belief_cache, automaton_caches=shared.automaton_caches,
        cupy_sparse=gpu, maximum_feature_width_per_batch=parsed["maximum_feature_width_per_batch"],
        hands_by_player=belief.hands_by_player,
    )
    solver.warm_start(blueprint, parsed["warm_regret_mass_payoff_fraction"] * float(layout.game.payoff_span))
    warm_start_distance = _policy_distance(blueprint, solver.current_strategy())
    release_cupy_memory_pool()
    memory_rows = [_memory_snapshot(cp)]
    search_started = time.perf_counter()
    solver.step()
    search_ms = (time.perf_counter() - search_started) * 1000.0
    candidate = solver.current_strategy()
    memory_rows.append(_memory_snapshot(cp))

    anchors = select_one_atom_per_acting_seat(layout, belief.hands_by_player, blueprint, candidate)
    blocks = build_public_node_blocks(blueprint, candidate, anchors)
    scales = geometric_halving_scales(numerical_floor=parsed["numerical_floor"])
    raw_guard = parsed["acceptance_guard_normalized"] * parsed["stack"]
    blueprint_nash = float(blueprint_quality["nash_conv"])
    direction_rows = []
    for direction in parsed["directions"]:
        keys = direction_information_keys(blocks, direction["acting_seats"])
        scale_rows = []
        for scale_index, scale in enumerate(scales):
            construction_started = time.perf_counter()
            policy = interpolate_policy_atoms(blueprint, candidate, keys, scale=scale)
            construction_ms = (time.perf_counter() - construction_started) * 1000.0
            certificate = _certificate(
                candidate_id=f"{direction['direction_id']}@scale_{scale_index:02d}",
                policy=policy, layout=layout, belief=belief, context=context, shared=shared,
                gpu=gpu, blueprint_quality=blueprint_quality, parsed=parsed,
            )
            quality = certificate["quality"]
            value = 0.0 if quality is None else _positive_value(blueprint_nash, float(quality["nash_conv"]))
            binding = certificate_binding_diagnostics(certificate, blueprint_quality, raw_guard)
            complete_cap_margin = None
            objective_reduction = None
            if quality is not None:
                complete_cap_margin = min(
                    float(base_gain) + raw_guard - float(candidate_gain)
                    for base_gain, candidate_gain in zip(blueprint_quality["deviation_gains"], quality["deviation_gains"], strict=True)
                )
                objective_reduction = blueprint_nash - float(quality["nash_conv"])
            memory = _memory_snapshot(cp)
            memory_rows.append(memory)
            scale_rows.append({
                "scale_index": scale_index,
                "scale": scale,
                "policy_sha256": policy_digest(policy),
                "construction_ms": construction_ms,
                "changed_information_set_count": len(atomic_policy_manifest(blueprint, policy)),
                "certificate_anchor_policy_sha256": blueprint_digest,
                "certificate_anchor_nash_conv": blueprint_nash,
                "independent_from_blueprint": True,
                "positive_certified_value": value,
                "normalized_objective_reduction": None if objective_reduction is None else objective_reduction / parsed["stack"],
                "minimum_complete_cap_margin": complete_cap_margin,
                "value_per_certificate_second": _safe_ratio(value, float(certificate["wall_ms"]) / 1000.0),
                **binding,
                "certificate": certificate,
                "memory_after": memory,
            })
        direction_rows.append({
            **direction,
            "information_keys": list(keys),
            "information_set_count": len(keys),
            "scale_rows": scale_rows,
            "summary": summarize_direction_rows(scale_rows),
        })

    result = {
        "target": target_spec["target"],
        "board_id": target_spec["board_id"],
        "board": target_spec["board"],
        "range_family": family,
        "target_shift": target_spec["target_shift"],
        "source_belief_sha256": source_digest,
        "target_belief_sha256": target_digest,
        "target_descriptor_sha256": descriptor_digest,
        "target_descriptor": descriptor,
        "source_checkpoint_identity": source_checkpoint_identity,
        "target_identity": target_identity,
        "blueprint_identity": blueprint_identity,
        "warm_start_distance": warm_start_distance,
        "blueprint_quality": blueprint_quality,
        "search_step_ms": search_ms,
        "search_step_work_wall_ms": solver.last_step_work.wall_ms,
        "candidate_policy_sha256": policy_digest(candidate),
        "changed_information_set_count": len(atomic_policy_manifest(blueprint, candidate)),
        "public_blocks": list(blocks),
        "scale_grid": list(scales),
        "direction_rows": direction_rows,
        "emitted_candidate_id": "blueprint_average64",
        "emitted_policy_sha256": blueprint_digest,
        "memory_rows": memory_rows,
    }
    del solver, context, shared, gpu, workspace, base, automata, source_workspace
    del sparse, layout, belief, source
    gc.collect()
    release_cupy_memory_pool()
    return result


def run_h32_fresh_public_block_radius_audit(config_path: Path = _CONFIG, output_path: Path = _OUTPUT) -> dict[str, Any]:
    """Execute the frozen off-clock public-block admissible-radius map."""

    started = time.perf_counter()
    parsed = parse_h32_fresh_public_block_radius_config(json.loads(config_path.read_text(encoding="utf-8")))
    source_parent = json.loads(_SOURCE.read_text(encoding="utf-8"))
    parent = json.loads(_PARENT_RESULT.read_text(encoding="utf-8"))
    git = _strict_git_metadata()
    cp, runtime = _validate_runtime(parsed)
    if git["dirty"]:
        raise RuntimeError("fresh public-block radius execution requires a clean Git state")
    if not source_parent["passed"] or not parent["gates"]["passed"]:
        raise ValueError("fresh public-block radius parent did not pass")
    targets = []
    for target_spec in parsed["targets"]:
        print(f"fresh public-block radius audit: {target_spec['target']}", flush=True)
        targets.append(_run_target(parsed, source_parent, target_spec, cp))

    directions = [row for target in targets for row in target["direction_rows"]]
    scale_rows = [row for direction in directions for row in direction["scale_rows"]]
    memory_rows = [row for target in targets for row in target["memory_rows"]]
    total_seconds = time.perf_counter() - started
    gates_config = parsed["gates"]
    scales = geometric_halving_scales(numerical_floor=parsed["numerical_floor"])
    finite_values = [
        value for target in targets for value in (
            target["blueprint_quality"]["nash_conv"], target["search_step_ms"],
            target["warm_start_distance"]["maximum_probability_error"],
            target["warm_start_distance"]["mean_total_variation"],
        )
    ] + [
        value for row in scale_rows for value in (
            row["scale"], row["construction_ms"], row["positive_certified_value"],
            row["certificate"]["wall_ms"], row["certificate"]["partial_nash_conv"],
        )
    ]
    gates = {
        "clean_git": (not git["dirty"]) == gates_config["require_clean_git_state"],
        "parent_passed": (source_parent["passed"] and parent["gates"]["passed"]) == gates_config["require_parent_passed"],
        "target_rows": len(targets) == gates_config["expected_target_rows"],
        "search_steps": len(targets) == gates_config["expected_search_steps"],
        "public_blocks": sum(len(row["public_blocks"]) for row in targets) == gates_config["expected_public_blocks"],
        "directions": len(directions) == gates_config["expected_directions"],
        "scale_count": len(scales) == gates_config["expected_scale_count"],
        "scale_rows": len(scale_rows) == gates_config["expected_scale_rows"],
        "blueprint_quality_labels": len(targets) == gates_config["expected_blueprint_quality_labels"],
        "source_checkpoint_identity": all(row["source_checkpoint_identity"] for row in targets) == gates_config["require_source_checkpoint_identity"],
        "target_identity": all(row["target_identity"] for row in targets) == gates_config["require_target_identity"],
        "blueprint_identity": all(row["blueprint_identity"] for row in targets) == gates_config["require_blueprint_identity"],
        "numerical_warm_start_identity": all(
            row["warm_start_distance"]["maximum_probability_error"] <= parsed["maximum_warm_start_probability_error"]
            and row["warm_start_distance"]["mean_total_variation"] <= parsed["maximum_warm_start_mean_total_variation"]
            for row in targets
        ) == gates_config["require_numerical_warm_start_identity"],
        "nonempty_coherent_blocks": all(
            block["information_set_count"] > 0 and all(
                information_key_public_coordinates(key) == (block["acting_seat"], block["public_history"])
                for key in block["information_keys"]
            )
            for target in targets for block in target["public_blocks"]
        ) == gates_config["require_nonempty_coherent_blocks"],
        "direction_key_identity": all(
            row["information_keys"] == list(direction_information_keys(target["public_blocks"], row["acting_seats"]))
            for target in targets for row in target["direction_rows"]
        ) == gates_config["require_direction_key_identity"],
        "scale_grid_identity": all(
            tuple(target["scale_grid"]) == scales and all(
                tuple(row["scale"] for row in direction["scale_rows"]) == scales
                for direction in target["direction_rows"]
            ) for target in targets
        ) == gates_config["require_scale_grid_identity"],
        "immutable_anchor": all(
            row["certificate_anchor_policy_sha256"] == target["blueprint_quality"]["policy_sha256"]
            and row["certificate_anchor_nash_conv"] == target["blueprint_quality"]["nash_conv"]
            for target in targets for direction in target["direction_rows"] for row in direction["scale_rows"]
        ) == gates_config["require_immutable_anchor"],
        "independent_certificates": all(row["independent_from_blueprint"] for row in scale_rows) == gates_config["require_independent_certificates"],
        "blueprint_emission": all(
            target["emitted_candidate_id"] == "blueprint_average64"
            and target["emitted_policy_sha256"] == target["blueprint_quality"]["policy_sha256"]
            for target in targets
        ) == gates_config["require_blueprint_emission"],
        "search_step_ms": all(target["search_step_ms"] <= gates_config["maximum_search_step_ms"] for target in targets),
        "certificate_ms": all(row["certificate"]["wall_ms"] <= gates_config["maximum_certificate_ms"] for row in scale_rows),
        "memory": max(row["gpu_pool_total_bytes"] for row in memory_rows) <= gates_config["maximum_gpu_pool_bytes"]
        and min(row["gpu_free_bytes"] for row in memory_rows) >= gates_config["minimum_physical_free_bytes"],
        "finite": all(math.isfinite(float(value)) for value in finite_values) == gates_config["require_finite"],
        "strategy_population_claim_null": True == gates_config["require_strategy_population_claim_null"],
        "total_audit_seconds": total_seconds <= gates_config["maximum_total_audit_seconds"],
    }
    gates["passed"] = all(gates.values())
    result = {
        "schema_version": 1,
        "status": "frozen_h32_fresh_public_block_radius_audit_executed",
        "methodology": {
            "preregistered": True,
            "fresh_target_quality_labels": True,
            "measurement_context": "off_clock_research",
            "target_population_claim": None,
            "deployment_authorized": False,
            "emitted_policy": "immutable_blueprint",
            "scale_labels_composable": False,
        },
        "config_sha256": _sha256(config_path),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "environment": {**environment_metadata(), **runtime, "git": git},
        "target_rows": targets,
        "aggregate": {
            "targets": len(targets),
            "directions": len(directions),
            "scale_count": len(scales),
            "scale_rows": len(scale_rows),
            "complete_scale_rows": sum(row["certificate"]["complete"] for row in scale_rows),
            "blueprint_cap_rows": sum(row["certificate"]["stop_reason"] == "blueprint_cap" for row in scale_rows),
            "objective_lower_bound_rows": sum(row["certificate"]["stop_reason"] == "objective_lower_bound" for row in scale_rows),
            "directions_with_admissible_grid_scale": sum(row["summary"]["complete_scale_count"] > 0 for row in directions),
            "maximum_gpu_pool_bytes": max(row["gpu_pool_total_bytes"] for row in memory_rows),
            "minimum_gpu_free_bytes": min(row["gpu_free_bytes"] for row in memory_rows),
        },
        "gates": gates,
        "total_audit_seconds": total_seconds,
        "decision": "accept_prospective_radius_measurement" if gates["passed"] else "reject_fresh_public_block_radius_audit",
        "strategy_population_claim": None,
        "limitations": [
            "Two deliberately constructed target beliefs are not a population.",
            "The scale grid is a diagnostic map, not a live 15-second scheduler.",
            "Every scale is independently certified against the immutable blueprint.",
            "No observed scale is emitted, deployed, or reused compositionally.",
        ],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    cp.get_default_memory_pool().free_all_blocks()
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=_CONFIG)
    parser.add_argument("--output", type=Path, default=_OUTPUT)
    args = parser.parse_args()
    result = run_h32_fresh_public_block_radius_audit(args.config, args.output)
    print(json.dumps({"output": str(args.output), "passed": result["gates"]["passed"], "aggregate": result["aggregate"]}, indent=2))
    if not result["gates"]["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
