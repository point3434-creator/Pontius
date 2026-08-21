"""Prospective exact-union value audit on two previously unlabeled h32 targets."""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import math
from pathlib import Path
import time
from typing import Any, Mapping

import numpy as np

from .axis_cfr_checkpoint import axis_cfr_checkpoint_digest
from .cupy_sparse_incidence import (
    CuPyBidirectionalIncidence,
    release_cupy_memory_pool,
)
from .delta_certificate_contract import interpolate_policy_atoms
from .factor_tt_contraction import FactorTTBeliefWorkspace
from .fresh_h32_strategy_transfer_audit import (
    _belief_digest,
    _resident_quality_row,
)
from .h32_affine_resident_cache_preflight import (
    _strict_git_metadata,
    _validate_runtime,
)
from .h32_atomic_response_preflight import select_one_atom_per_acting_seat
from .h32_atomic_street_scheduler_audit import may_start_certificate
from .h32_fresh_board_panel_cache_preflight import _json_digest
from .h32_warm_search_acceptance_audit import (
    _average_policy_from_state,
    _local_blocker_likelihoods,
)
from .incremental_leaf_adjoint_response import (
    verify_incremental_leaf_adjoint_candidate,
)
from .leaf_adjoint_checkpoint_ladder_audit import _build_case
from .open_mode_factor_tt import OpenModeFactorTTWorkspace
from .real_policy import policy_digest
from .reporting import environment_metadata
from .resident_leaf_adjoint_cfr import ResidentLeafAdjointPublicTreeCFR
from .river import parse_cards
from .shared_resident_response_context import (
    SharedResidentAutomatonBundle,
    bind_resident_response_context,
)


_ROOT = Path(__file__).parents[2]
_CONFIG = _ROOT / "experiments/configs/h32-fresh-union-value-v1.json"
_OUTPUT = _ROOT / "experiments/results/h32-fresh-union-value-v1.json"
_SOURCE = _ROOT / "experiments/results/h32-fresh-panel-source-blueprints-v1.json"
_SOURCE_CONFIG = _ROOT / "experiments/configs/h32-fresh-panel-source-blueprints-v1.json"
_REQUIREMENTS = _ROOT / "experiments/requirements/leaf-adjoint-gpu-screen-v1.txt"
_IMPLEMENTATION = Path(__file__)
_TEST = _ROOT / "tests/test_h32_fresh_union_value_audit.py"

_PATHS = {
    "expected_source_result_sha256": _SOURCE,
    "expected_source_config_sha256": _SOURCE_CONFIG,
    "expected_requirements_sha256": _REQUIREMENTS,
    "expected_target_builder_sha256": (
        _ROOT / "src/pontius/h32_warm_search_acceptance_audit.py"
    ),
    "expected_shared_context_sha256": (
        _ROOT / "src/pontius/shared_resident_response_context.py"
    ),
    "expected_incremental_verifier_sha256": (
        _ROOT / "src/pontius/incremental_leaf_adjoint_response.py"
    ),
    "expected_resident_cfr_sha256": (
        _ROOT / "src/pontius/resident_leaf_adjoint_cfr.py"
    ),
    "expected_atom_manifest_sha256": (
        _ROOT / "src/pontius/h32_atomic_response_preflight.py"
    ),
    "expected_deadline_scheduler_sha256": (
        _ROOT / "src/pontius/h32_atomic_street_scheduler_audit.py"
    ),
    "expected_interpolation_sha256": (
        _ROOT / "src/pontius/delta_certificate_contract.py"
    ),
    "expected_audit_implementation_sha256": _IMPLEMENTATION,
    "expected_control_test_sha256": _TEST,
}

_FROZEN_TARGETS = [
    {
        "target": "panel_1/balanced/local_blocker_seat4_x2",
        "board_id": "panel_1",
        "board": ["5c", "8c", "8d", "Jc", "As"],
        "range_family": "balanced",
        "target_shift": "local_blocker_seat4_x2",
        "source_belief_sha256": (
            "376e8a44217f35dfdf305035fe8f3bbfb52b010e14050bedaf55da78c9e72885"
        ),
        "target_belief_sha256": (
            "08e0cc46cc259e29f138152d52f69f53e2fc5442487d29ee22007b9e615f1c36"
        ),
        "target_descriptor_sha256": (
            "6c8f96aeba9c2c70212177518c135ec69eb071e3928641a4dbc7da97a306510a"
        ),
    },
    {
        "target": "panel_2/blocker_heavy/local_blocker_seat4_x2",
        "board_id": "panel_2",
        "board": ["2c", "3s", "5d", "Js", "Qc"],
        "range_family": "blocker_heavy",
        "target_shift": "local_blocker_seat4_x2",
        "source_belief_sha256": (
            "59f955c6b89bdc56670dc16b19795451404fe80ff37f519bac007975d85200f1"
        ),
        "target_belief_sha256": (
            "cd2d7a0f10610ec0ac46999014475d3792f8eb4c345bd4c7eac42a446dbfa4d0"
        ),
        "target_descriptor_sha256": (
            "f637685f81bb5a452ff00344cb4424a71deb86b651735f0dadc63f38d67f4686"
        ),
    },
]

_FROZEN_UNIONS = [
    {"candidate_id": "union_all_six", "acting_seats": [0, 1, 2, 3, 4, 5]},
    {"candidate_id": "union_prefix_four", "acting_seats": [0, 1, 2, 3]},
    {"candidate_id": "union_prefix_two", "acting_seats": [0, 1]},
]


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required frozen input is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_h32_fresh_union_value_config(config: dict[str, Any]) -> dict[str, Any]:
    """Validate the complete pre-label contract from ADR-0169."""

    fields = {
        "evidence_stage",
        *_PATHS,
        "seed",
        "targets",
        "target_construction",
        "local_blocker_target_seat",
        "pot",
        "stack",
        "bet_size",
        "players",
        "hands_per_player",
        "axis_seed",
        "mixture_components",
        "split_index",
        "query_chunk_records",
        "solver_variant",
        "warm_regret_mass_payoff_fraction",
        "search_steps_per_target",
        "atom_selection",
        "atom_scale",
        "union_library",
        "union_order_rule",
        "post_ledger_atomic_diagnostics",
        "certificate_anchor_rule",
        "seat_order",
        "acceptance_guard_normalized",
        "decision_budget_ms",
        "emission_reserve_ms",
        "certificate_start_reserve_ms",
        "maximum_feature_width_per_batch",
        "shadow_selection_rule",
        "emitted_policy",
        "required_numpy_version",
        "required_scipy_version",
        "required_cupy_version",
        "required_cuda_runtime_version",
        "minimum_cuda_driver_version",
        "required_compute_capability",
        "cuda_dll_environment_variable",
        "gates",
    }
    if set(config) != fields:
        raise ValueError("fresh-union fields differ from ADR-0169")
    frozen = {
        "evidence_stage": (
            "preregistered_after_adr0168_before_any_seat4_target_policy_step_"
            "or_quality_measurement"
        ),
        "seed": 20260821,
        "targets": _FROZEN_TARGETS,
        "target_construction": (
            "double_label_free_maximum_overlap_then_strength_then_smallest_"
            "canonical_hand_at_seat4"
        ),
        "local_blocker_target_seat": 4,
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
        "atom_selection": (
            "lexicographically_first_changed_information_set_per_acting_seat"
        ),
        "atom_scale": 1.0,
        "union_library": _FROZEN_UNIONS,
        "union_order_rule": "descending_cardinality_then_frozen_candidate_id",
        "post_ledger_atomic_diagnostics": (
            "all_six_singletons_exactly_recertified_after_emission_and_ineligible"
        ),
        "certificate_anchor_rule": (
            "immutable_source_average64_one_shot_target_certificate_never_reanchors"
        ),
        "seat_order": [0, 1, 2, 3, 4, 5],
        "acceptance_guard_normalized": 1e-10,
        "decision_budget_ms": 15000.0,
        "emission_reserve_ms": 1000.0,
        "certificate_start_reserve_ms": 1250.0,
        "maximum_feature_width_per_batch": 384,
        "shadow_selection_rule": (
            "maximum_positive_certified_value_among_complete_usable_live_unions_"
            "then_frozen_order"
        ),
        "emitted_policy": "immutable_blueprint_research_shadow_only",
        "required_numpy_version": "2.5.2",
        "required_scipy_version": "1.18.0",
        "required_cupy_version": "14.2.0",
        "required_cuda_runtime_version": 13020,
        "minimum_cuda_driver_version": 13000,
        "required_compute_capability": "120",
        "cuda_dll_environment_variable": "PONTIUS_CUDA_DLL_DIRECTORY",
    }
    if any(config[key] != value for key, value in frozen.items()):
        raise ValueError("fresh-union workload differs from ADR-0169")
    for field, path in _PATHS.items():
        if config[field] != _sha256(path):
            raise ValueError(f"fresh-union source mismatch: {field}")
    gates = {
        "expected_target_rows": 2,
        "expected_search_steps": 2,
        "expected_manifest_atoms": 12,
        "expected_union_library_rows": 6,
        "expected_post_ledger_atomic_labels": 12,
        "expected_blueprint_quality_labels": 2,
        "maximum_search_step_ms": 60000.0,
        "maximum_union_certificate_ms": 60000.0,
        "maximum_atomic_certificate_ms": 60000.0,
        "maximum_gpu_pool_bytes": 12000000000,
        "minimum_physical_free_bytes": 1000000000,
        "maximum_total_audit_seconds": 1200.0,
        "require_clean_git_state": True,
        "require_source_parent_passed": True,
        "require_source_checkpoint_identity": True,
        "require_target_identity": True,
        "require_blueprint_identity": True,
        "require_warm_start_identity": True,
        "require_union_key_identity": True,
        "require_immutable_anchor": True,
        "require_deadline_discipline": True,
        "require_fail_closed_shadow_selection": True,
        "require_blueprint_emission": True,
        "require_post_ledger_ineligibility": True,
        "require_finite": True,
        "require_strategy_population_claim_null": True,
    }
    if config["gates"] != gates:
        raise ValueError("fresh-union gates differ from ADR-0169")
    return {
        **config,
        "targets": tuple(dict(row) for row in config["targets"]),
        "union_library": tuple(dict(row) for row in config["union_library"]),
        "seat_order": tuple(config["seat_order"]),
        "gates": dict(gates),
    }


def build_fresh_seat4_target(
    source: Any,
    *,
    board: tuple[int, ...],
    target_seat: int,
) -> tuple[Any, dict[str, Any]]:
    """Construct the frozen positive target without consulting a strategy label."""

    if target_seat != 4:
        raise ValueError("fresh-union target seat differs from ADR-0169")
    likelihoods, detail = _local_blocker_likelihoods(
        source, board=board, target_seat=target_seat
    )
    target = source
    for seat, likelihood in enumerate(likelihoods):
        target = target.with_likelihood(seat, likelihood)
    values = np.concatenate(likelihoods)
    return target, {
        "shift": "local_blocker_seat4_x2",
        "likelihood_minimum": float(np.min(values)),
        "likelihood_maximum": float(np.max(values)),
        "likelihood_mean": float(np.mean(values)),
        "positive_likelihoods": bool(np.all(values > 0.0)),
        "hand_axes_identity": target.hands_by_player == source.hands_by_player,
        **detail,
    }


def union_keys_by_seat(
    manifest: tuple[Mapping[str, Any], ...] | list[Mapping[str, Any]],
    acting_seats: tuple[int, ...] | list[int],
) -> tuple[str, ...]:
    """Resolve one selected atom per requested seat in frozen seat order."""

    by_seat = {int(row["acting_seat"]): str(row["information_key"]) for row in manifest}
    if len(by_seat) != len(manifest):
        raise ValueError("atomic manifest contains duplicate acting seats")
    seats = tuple(int(seat) for seat in acting_seats)
    if len(set(seats)) != len(seats) or any(seat not in by_seat for seat in seats):
        raise ValueError("union library cannot be resolved from atomic manifest")
    return tuple(by_seat[seat] for seat in seats)


def _positive_value(blueprint_nash: float, candidate_nash: float) -> float:
    return max(0.0, blueprint_nash - candidate_nash)


def _safe_ratio(numerator: float, denominator: float) -> float | None:
    return None if denominator <= 0.0 else numerator / denominator


def _memory_snapshot(cp: Any) -> dict[str, int]:
    free, total = cp.cuda.runtime.memGetInfo()
    pool = cp.get_default_memory_pool()
    return {
        "gpu_free_bytes": int(free),
        "gpu_total_bytes": int(total),
        "gpu_pool_used_bytes": int(pool.used_bytes()),
        "gpu_pool_total_bytes": int(pool.total_bytes()),
    }


def _certificate(
    *,
    candidate_id: str,
    policy: dict[str, dict[str, float]],
    layout: Any,
    belief: Any,
    context: Any,
    shared: Any,
    gpu: Any,
    blueprint_quality: dict[str, Any],
    parsed: dict[str, Any],
) -> dict[str, Any]:
    return verify_incremental_leaf_adjoint_candidate(
        candidate_id=candidate_id,
        layout=layout,
        policy=policy,
        hands_by_player=belief.hands_by_player,
        response_caches=context.response_caches,
        blueprint_deviation_gains=tuple(
            float(value) for value in blueprint_quality["deviation_gains"]
        ),
        best_complete_nash_conv=float(blueprint_quality["nash_conv"]),
        payoff_span=parsed["stack"],
        raw_guard=parsed["acceptance_guard_normalized"] * parsed["stack"],
        seat_order=parsed["seat_order"],
        maximum_feature_width_per_batch=parsed["maximum_feature_width_per_batch"],
        belief_cache=context.belief_cache,
        automaton_caches=shared.automaton_caches,
        cupy_sparse=gpu,
    )


def _run_target(
    parsed: dict[str, Any],
    parent: dict[str, Any],
    target_spec: Mapping[str, Any],
    cp: Any,
) -> dict[str, Any]:
    board = parse_cards(*target_spec["board"])
    family = str(target_spec["range_family"])
    source, layout, sparse, retained = _build_case(
        parsed=parsed,
        board=board,
        hand_count=parsed["hands_per_player"],
        family=family,
    )
    source_workspace, _, automata = retained
    source_digest = _belief_digest(source)
    parent_row = next(
        row
        for row in parent["source_rows"]
        if row["source"] == f"{target_spec['board_id']}/{family}"
    )
    state = parent_row["final_checkpoint"]
    source_checkpoint_identity = (
        axis_cfr_checkpoint_digest(state) == state["state_sha256"]
        and source_digest == target_spec["source_belief_sha256"]
        and source_digest == parent_row["source_belief_sha256"]
    )
    blueprint = _average_policy_from_state(state)
    blueprint_identity = policy_digest(blueprint) == state["average_policy_sha256"]
    belief, descriptor = build_fresh_seat4_target(
        source,
        board=board,
        target_seat=parsed["local_blocker_target_seat"],
    )
    target_digest = _belief_digest(belief)
    descriptor_digest = _json_digest(descriptor)
    target_identity = (
        target_digest == target_spec["target_belief_sha256"]
        and descriptor_digest == target_spec["target_descriptor_sha256"]
        and belief.hands_by_player == source.hands_by_player
    )

    base = FactorTTBeliefWorkspace.compile(
        source_workspace.topology.base,
        belief,
        query_chunk_records=parsed["query_chunk_records"],
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
        maximum_feature_width_per_batch=parsed["maximum_feature_width_per_batch"],
    )
    blueprint_quality, _ = _resident_quality_row(
        layout=layout,
        workspace=workspace,
        sparse=sparse,
        automata=automata,
        policy=blueprint,
        label="blueprint_average64",
        hands_by_player=belief.hands_by_player,
        belief_cache=context.belief_cache,
        automaton_caches=shared.automaton_caches,
        gpu=gpu,
        payoff_span=parsed["stack"],
        maximum_feature_width_per_batch=parsed["maximum_feature_width_per_batch"],
    )
    solver = ResidentLeafAdjointPublicTreeCFR(
        layout,
        workspace,
        sparse,
        automata,
        parsed["solver_variant"],
        belief_cache=context.belief_cache,
        automaton_caches=shared.automaton_caches,
        cupy_sparse=gpu,
        maximum_feature_width_per_batch=parsed["maximum_feature_width_per_batch"],
        hands_by_player=belief.hands_by_player,
    )
    solver.warm_start(
        blueprint,
        parsed["warm_regret_mass_payoff_fraction"] * float(layout.game.payoff_span),
    )
    warm_start_identity = policy_digest(solver.current_strategy()) == policy_digest(
        blueprint
    )

    release_cupy_memory_pool()
    memory_rows = [_memory_snapshot(cp)]
    street_started = time.perf_counter()
    solver.step()
    search_completed = time.perf_counter()
    search_ms = (search_completed - street_started) * 1000.0
    candidate = solver.current_strategy()
    memory_rows.append(_memory_snapshot(cp))

    construction_started = time.perf_counter()
    manifest = select_one_atom_per_acting_seat(
        layout, belief.hands_by_player, blueprint, candidate
    )
    union_library = []
    union_policies: dict[str, dict[str, dict[str, float]]] = {}
    for frozen_union in parsed["union_library"]:
        keys = union_keys_by_seat(manifest, frozen_union["acting_seats"])
        candidate_id = frozen_union["candidate_id"]
        policy = interpolate_policy_atoms(
            blueprint, candidate, keys, scale=parsed["atom_scale"]
        )
        union_policies[candidate_id] = policy
        union_library.append(
            {
                **frozen_union,
                "information_keys": list(keys),
                "policy_sha256": policy_digest(policy),
            }
        )
    construction_ms = (time.perf_counter() - construction_started) * 1000.0

    live_rows = []
    deadline_reason = "union_library_exhausted"
    blueprint_nash = float(blueprint_quality["nash_conv"])
    cutoff_ms = parsed["decision_budget_ms"] - parsed["emission_reserve_ms"]
    for library_row in union_library:
        elapsed_before_ms = (time.perf_counter() - street_started) * 1000.0
        may_start = may_start_certificate(
            elapsed_ms=elapsed_before_ms,
            decision_budget_ms=parsed["decision_budget_ms"],
            emission_reserve_ms=parsed["emission_reserve_ms"],
            certificate_start_reserve_ms=parsed["certificate_start_reserve_ms"],
        )
        if not may_start:
            deadline_reason = "certificate_start_guard"
            break
        memory_before = _memory_snapshot(cp)
        live = _certificate(
            candidate_id=library_row["candidate_id"],
            policy=union_policies[library_row["candidate_id"]],
            layout=layout,
            belief=belief,
            context=context,
            shared=shared,
            gpu=gpu,
            blueprint_quality=blueprint_quality,
            parsed=parsed,
        )
        elapsed_completed_ms = (time.perf_counter() - street_started) * 1000.0
        memory_after = _memory_snapshot(cp)
        memory_rows.extend((memory_before, memory_after))
        usable = elapsed_completed_ms <= cutoff_ms
        candidate_nash = (
            None if not live["complete"] else float(live["quality"]["nash_conv"])
        )
        value = (
            0.0
            if candidate_nash is None
            else _positive_value(blueprint_nash, candidate_nash)
        )
        live_rows.append(
            {
                **library_row,
                "elapsed_before_ms": elapsed_before_ms,
                "start_guard_passed": may_start,
                "elapsed_completed_ms": elapsed_completed_ms,
                "usable_before_emission_cutoff": usable,
                "positive_certified_value": value,
                "value_per_certificate_second": _safe_ratio(
                    value, float(live["wall_ms"]) / 1000.0
                ),
                "value_per_street_second": _safe_ratio(
                    value, elapsed_completed_ms / 1000.0
                ),
                "certificate_anchor_policy_sha256": policy_digest(blueprint),
                "certificate_anchor_nash_conv": blueprint_nash,
                "certificate": live,
                "memory_before": memory_before,
                "memory_after": memory_after,
            }
        )
        if not usable:
            deadline_reason = "certificate_completed_after_cutoff"
            break

    eligible = [
        row
        for row in live_rows
        if row["usable_before_emission_cutoff"] and row["certificate"]["complete"]
    ]
    best_live = (
        None
        if not eligible
        else min(
            eligible,
            key=lambda row: (
                -row["positive_certified_value"],
                next(
                    index
                    for index, frozen in enumerate(parsed["union_library"])
                    if frozen["candidate_id"] == row["candidate_id"]
                ),
            ),
        )
    )
    shadow_selected_id = (
        "blueprint_average64"
        if best_live is None or best_live["positive_certified_value"] <= 0.0
        else best_live["candidate_id"]
    )
    before_emission_ms = (time.perf_counter() - street_started) * 1000.0
    hard_ledger_ms = before_emission_ms + parsed["emission_reserve_ms"]
    emitted_policy_sha256 = policy_digest(blueprint)

    atomic_rows = []
    for atom in manifest:
        seat = int(atom["acting_seat"])
        policy = interpolate_policy_atoms(
            blueprint,
            candidate,
            [atom["information_key"]],
            scale=parsed["atom_scale"],
        )
        label = _certificate(
            candidate_id=f"diagnostic_atomic_seat{seat}",
            policy=policy,
            layout=layout,
            belief=belief,
            context=context,
            shared=shared,
            gpu=gpu,
            blueprint_quality=blueprint_quality,
            parsed=parsed,
        )
        candidate_nash = (
            None if not label["complete"] else float(label["quality"]["nash_conv"])
        )
        atomic_rows.append(
            {
                **atom,
                "candidate_id": f"diagnostic_atomic_seat{seat}",
                "policy_sha256": policy_digest(policy),
                "post_ledger": True,
                "eligible_for_shadow_selection": False,
                "certificate_anchor_policy_sha256": policy_digest(blueprint),
                "certificate_anchor_nash_conv": blueprint_nash,
                "positive_certified_value": (
                    0.0
                    if candidate_nash is None
                    else _positive_value(blueprint_nash, candidate_nash)
                ),
                "certificate": label,
            }
        )
    memory_rows.append(_memory_snapshot(cp))

    full_union = next(
        (row for row in live_rows if row["candidate_id"] == "union_all_six"), None
    )
    full_union_value = (
        0.0 if full_union is None else full_union["positive_certified_value"]
    )
    complete_atoms = [row for row in atomic_rows if row["certificate"]["complete"]]
    sum_atomic_value = math.fsum(
        row["positive_certified_value"] for row in complete_atoms
    )
    best_atomic_value = max(
        (row["positive_certified_value"] for row in complete_atoms), default=0.0
    )
    interaction = {
        "full_union_attempted": full_union is not None,
        "full_union_complete": bool(
            full_union is not None and full_union["certificate"]["complete"]
        ),
        "full_union_positive_certified_value": full_union_value,
        "complete_atomic_count": len(complete_atoms),
        "cap_bound_atomic_count": sum(
            row["certificate"]["stop_reason"] == "blueprint_cap"
            for row in atomic_rows
        ),
        "objective_bound_atomic_count": sum(
            row["certificate"]["stop_reason"] == "objective_lower_bound"
            for row in atomic_rows
        ),
        "sum_complete_atomic_value": sum_atomic_value,
        "best_complete_atomic_value": best_atomic_value,
        "best_atomic_fraction_of_full_union_value": _safe_ratio(
            best_atomic_value, full_union_value
        ),
        "sum_atomic_fraction_of_full_union_value": _safe_ratio(
            sum_atomic_value, full_union_value
        ),
        "complete_full_union_with_stopped_constituent": bool(
            full_union is not None
            and full_union["certificate"]["complete"]
            and any(not row["certificate"]["complete"] for row in atomic_rows)
        ),
        "scalar_six_way_interaction_residual": (
            float(full_union["certificate"]["quality"]["nash_conv"])
            - blueprint_nash
            - math.fsum(
                float(row["certificate"]["quality"]["nash_conv"])
                - blueprint_nash
                for row in atomic_rows
            )
            if full_union is not None
            and full_union["certificate"]["complete"]
            and len(complete_atoms) == len(atomic_rows)
            else None
        ),
    }

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
        "warm_start_identity": warm_start_identity,
        "blueprint_quality": blueprint_quality,
        "search_step_ms": search_ms,
        "search_step_work_wall_ms": solver.last_step_work.wall_ms,
        "candidate_policy_sha256": policy_digest(candidate),
        "manifest": list(manifest),
        "union_library": union_library,
        "union_construction_ms": construction_ms,
        "live_union_rows": live_rows,
        "deadline_reason": deadline_reason,
        "before_emission_ms": before_emission_ms,
        "emission_reserve_ms": parsed["emission_reserve_ms"],
        "hard_ledger_ms": hard_ledger_ms,
        "within_decision_budget": hard_ledger_ms <= parsed["decision_budget_ms"],
        "shadow_selected_candidate_id": shadow_selected_id,
        "shadow_selected_positive_certified_value": (
            0.0
            if shadow_selected_id == "blueprint_average64"
            else best_live["positive_certified_value"]
        ),
        "emitted_candidate_id": "blueprint_average64",
        "emitted_policy_sha256": emitted_policy_sha256,
        "post_ledger_atomic_rows": atomic_rows,
        "interaction_diagnostics": interaction,
        "memory_rows": memory_rows,
    }

    del solver, context, shared, gpu, workspace, base, automata, source_workspace
    del sparse, layout, belief, source
    gc.collect()
    release_cupy_memory_pool()
    return result


def run_h32_fresh_union_value_audit(
    config_path: Path = _CONFIG,
    output_path: Path = _OUTPUT,
) -> dict[str, Any]:
    """Execute the frozen prospective holdout audit."""

    audit_started = time.perf_counter()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    parsed = parse_h32_fresh_union_value_config(config)
    parent = json.loads(_SOURCE.read_text(encoding="utf-8"))
    git = _strict_git_metadata()
    cp, runtime = _validate_runtime(parsed)
    if git["dirty"]:
        raise RuntimeError("fresh-union execution requires a clean Git state")
    if not parent["passed"]:
        raise ValueError("fresh-union source parent did not pass")

    target_rows = []
    for target_spec in parsed["targets"]:
        print(f"fresh union audit: {target_spec['target']}", flush=True)
        target_rows.append(_run_target(parsed, parent, target_spec, cp))

    union_rows = [row for target in target_rows for row in target["live_union_rows"]]
    atom_rows = [
        row for target in target_rows for row in target["post_ledger_atomic_rows"]
    ]
    memory_rows = [row for target in target_rows for row in target["memory_rows"]]
    total_seconds = time.perf_counter() - audit_started
    gates_config = parsed["gates"]
    finite_values = [
        value
        for target in target_rows
        for value in (
            target["blueprint_quality"]["nash_conv"],
            target["search_step_ms"],
            target["union_construction_ms"],
            target["before_emission_ms"],
            target["hard_ledger_ms"],
            target["shadow_selected_positive_certified_value"],
        )
    ]
    gates = {
        "clean_git": (not git["dirty"]) == gates_config["require_clean_git_state"],
        "source_parent": parent["passed"]
        == gates_config["require_source_parent_passed"],
        "target_rows": len(target_rows) == gates_config["expected_target_rows"],
        "search_steps": len(target_rows) == gates_config["expected_search_steps"],
        "manifest_atoms": sum(len(row["manifest"]) for row in target_rows)
        == gates_config["expected_manifest_atoms"],
        "union_library_rows": sum(len(row["union_library"]) for row in target_rows)
        == gates_config["expected_union_library_rows"],
        "post_ledger_atomic_labels": len(atom_rows)
        == gates_config["expected_post_ledger_atomic_labels"],
        "blueprint_quality_labels": len(target_rows)
        == gates_config["expected_blueprint_quality_labels"],
        "source_checkpoint_identity": all(
            row["source_checkpoint_identity"] for row in target_rows
        )
        == gates_config["require_source_checkpoint_identity"],
        "target_identity": all(row["target_identity"] for row in target_rows)
        == gates_config["require_target_identity"],
        "blueprint_identity": all(row["blueprint_identity"] for row in target_rows)
        == gates_config["require_blueprint_identity"],
        "warm_start_identity": all(row["warm_start_identity"] for row in target_rows)
        == gates_config["require_warm_start_identity"],
        "union_key_identity": all(
            row["information_keys"]
            == list(
                union_keys_by_seat(
                    target["manifest"],
                    next(
                        frozen["acting_seats"]
                        for frozen in parsed["union_library"]
                        if frozen["candidate_id"] == row["candidate_id"]
                    ),
                )
            )
            for target in target_rows
            for row in target["union_library"]
        )
        == gates_config["require_union_key_identity"],
        "immutable_anchor": all(
            row["certificate"]["candidate_id"] == row["candidate_id"]
            and row["certificate_anchor_policy_sha256"]
            == target["blueprint_quality"]["policy_sha256"]
            and row["certificate_anchor_nash_conv"]
            == target["blueprint_quality"]["nash_conv"]
            for target in target_rows
            for row in (
                target["live_union_rows"] + target["post_ledger_atomic_rows"]
            )
        )
        == gates_config["require_immutable_anchor"],
        "deadline_discipline": all(
            row["start_guard_passed"] for row in union_rows
        )
        == gates_config["require_deadline_discipline"],
        "fail_closed_shadow_selection": all(
            target["shadow_selected_candidate_id"] == "blueprint_average64"
            or any(
                row["candidate_id"] == target["shadow_selected_candidate_id"]
                and row["usable_before_emission_cutoff"]
                and row["certificate"]["complete"]
                and row["positive_certified_value"] > 0.0
                for row in target["live_union_rows"]
            )
            for target in target_rows
        )
        == gates_config["require_fail_closed_shadow_selection"],
        "blueprint_emission": all(
            target["emitted_candidate_id"] == "blueprint_average64"
            and target["emitted_policy_sha256"]
            == target["blueprint_quality"]["policy_sha256"]
            for target in target_rows
        )
        == gates_config["require_blueprint_emission"],
        "post_ledger_ineligibility": all(
            row["post_ledger"] and not row["eligible_for_shadow_selection"]
            for row in atom_rows
        )
        == gates_config["require_post_ledger_ineligibility"],
        "search_step_ms": all(
            row["search_step_ms"] <= gates_config["maximum_search_step_ms"]
            for row in target_rows
        ),
        "union_certificate_ms": all(
            row["certificate"]["wall_ms"]
            <= gates_config["maximum_union_certificate_ms"]
            for row in union_rows
        ),
        "atomic_certificate_ms": all(
            row["certificate"]["wall_ms"]
            <= gates_config["maximum_atomic_certificate_ms"]
            for row in atom_rows
        ),
        "memory": max(row["gpu_pool_total_bytes"] for row in memory_rows)
        <= gates_config["maximum_gpu_pool_bytes"]
        and min(row["gpu_free_bytes"] for row in memory_rows)
        >= gates_config["minimum_physical_free_bytes"],
        "finite": all(math.isfinite(float(value)) for value in finite_values)
        == gates_config["require_finite"],
        "strategy_population_claim_null": True
        == gates_config["require_strategy_population_claim_null"],
        "total_audit_seconds": total_seconds
        <= gates_config["maximum_total_audit_seconds"],
    }
    gates["passed"] = all(gates.values())
    result = {
        "schema_version": 1,
        "status": "frozen_h32_fresh_union_value_audit_executed",
        "methodology": {
            "preregistered": True,
            "fresh_target_quality_labels": True,
            "target_population_claim": None,
            "deployment_authorized": False,
            "emitted_policy": "immutable_blueprint",
            "post_ledger_atoms_eligible": False,
        },
        "config_sha256": _sha256(config_path),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "environment": {**environment_metadata(), **runtime, "git": git},
        "target_rows": target_rows,
        "aggregate": {
            "targets": len(target_rows),
            "blueprint_quality_labels": len(target_rows),
            "live_union_attempts": len(union_rows),
            "live_union_completions": sum(
                row["certificate"]["complete"] for row in union_rows
            ),
            "usable_live_union_completions": sum(
                row["certificate"]["complete"]
                and row["usable_before_emission_cutoff"]
                for row in union_rows
            ),
            "positive_live_union_completions": sum(
                row["certificate"]["complete"]
                and row["positive_certified_value"] > 0.0
                for row in union_rows
            ),
            "post_ledger_atomic_labels": len(atom_rows),
            "post_ledger_complete_atoms": sum(
                row["certificate"]["complete"] for row in atom_rows
            ),
            "shadow_non_blueprint_selections": sum(
                row["shadow_selected_candidate_id"] != "blueprint_average64"
                for row in target_rows
            ),
            "hard_ledger_ms": {
                "minimum": min(row["hard_ledger_ms"] for row in target_rows),
                "maximum": max(row["hard_ledger_ms"] for row in target_rows),
            },
            "maximum_gpu_pool_bytes": max(
                row["gpu_pool_total_bytes"] for row in memory_rows
            ),
            "minimum_gpu_free_bytes": min(
                row["gpu_free_bytes"] for row in memory_rows
            ),
        },
        "gates": gates,
        "total_audit_seconds": total_seconds,
        "decision": (
            "accept_prospective_holdout_measurement"
            if gates["passed"]
            else "reject_fresh_union_audit"
        ),
        "strategy_population_claim": None,
        "limitations": [
            "Two deliberately constructed target beliefs are not a population.",
            "The immutable blueprint was emitted regardless of the shadow result.",
            "No certificate composes with any other certificate.",
            "Post-ledger singleton labels cannot affect the live scheduler.",
        ],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    cp.get_default_memory_pool().free_all_blocks()
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=_CONFIG)
    parser.add_argument("--output", type=Path, default=_OUTPUT)
    args = parser.parse_args()
    result = run_h32_fresh_union_value_audit(args.config, args.output)
    print(
        json.dumps(
            {
                "output": str(args.output),
                "passed": result["gates"]["passed"],
                "aggregate": result["aggregate"],
            },
            indent=2,
        )
    )
    if not result["gates"]["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
