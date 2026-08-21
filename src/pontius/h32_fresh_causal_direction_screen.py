"""Fresh h32 causal opportunity-feature and third-direction screen."""

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
from .h32_fresh_public_block_radius_audit import certificate_binding_diagnostics
from .h32_fresh_public_block_value_audit import (
    build_public_node_blocks,
    information_key_public_coordinates,
)
from .h32_fresh_regret_vertex_opportunity_audit import (
    block_regret_opportunity_proxy,
    build_regret_vertex_candidate,
    direction_has_convex_scope,
    exact_discrete_convex_scale_search,
    recover_iteration_one_dcfr_regret_deltas,
    search_invariants,
    spearman_rank_correlation,
)
from .h32_fresh_union_value_audit import (
    _certificate,
    _memory_snapshot,
    _positive_value,
    _safe_ratio,
)
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
from .shared_resident_response_context import (
    SharedResidentAutomatonBundle,
    bind_resident_response_context,
)


_ROOT = Path(__file__).parents[2]
_CONFIG = _ROOT / "experiments/configs/h32-fresh-causal-direction-screen-v1.json"
_OUTPUT = _ROOT / "experiments/results/h32-fresh-causal-direction-screen-v1.json"
_SOURCE = _ROOT / "experiments/results/h32-fresh-panel-source-blueprints-v1.json"
_VERTEX_PARENT = _ROOT / "experiments/results/h32-fresh-regret-vertex-opportunity-v1.json"
_PARENT_RESULT = _ROOT / "experiments/results/h32-deep-horizon-correction-v1.json"
_PARENT_ADR = _ROOT / "docs/decisions/ADR-0184-ordinary-deep-dcfr-plateaus-while-purification-remains-direction-sensitive.md"
_REQUIREMENTS = _ROOT / "experiments/requirements/leaf-adjoint-gpu-screen-v1.txt"
_IMPLEMENTATION = Path(__file__)
_TEST = _ROOT / "tests/test_h32_fresh_causal_direction_screen.py"

_PATHS = {
    "expected_source_result_sha256": _SOURCE,
    "expected_vertex_parent_result_sha256": _VERTEX_PARENT,
    "expected_parent_result_sha256": _PARENT_RESULT,
    "expected_parent_decision_sha256": _PARENT_ADR,
    "expected_requirements_sha256": _REQUIREMENTS,
    "expected_target_builder_sha256": _ROOT / "src/pontius/h32_warm_search_acceptance_audit.py",
    "expected_public_block_builder_sha256": _ROOT / "src/pontius/h32_fresh_public_block_value_audit.py",
    "expected_search_control_sha256": _ROOT / "src/pontius/h32_fresh_regret_vertex_opportunity_audit.py",
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
        "target": "panel_1/balanced/local_blocker_seat2_x2",
        "board_id": "panel_1",
        "board": ["5c", "8c", "8d", "Jc", "As"],
        "range_family": "balanced",
        "target_shift": "local_blocker_seat2_x2",
        "source_belief_sha256": "376e8a44217f35dfdf305035fe8f3bbfb52b010e14050bedaf55da78c9e72885",
        "target_belief_sha256": "c9c80d8bb428c2d701284302ec3332d72d5114f41f74a186c9493561be4f7267",
        "target_descriptor_sha256": "9f57dc00d12ed45c2239ca1a513d9dabcf86224f0d75cdc4612a6f2fb16fda55",
    },
    {
        "target": "panel_1/blocker_heavy/local_blocker_seat2_x2",
        "board_id": "panel_1",
        "board": ["5c", "8c", "8d", "Jc", "As"],
        "range_family": "blocker_heavy",
        "target_shift": "local_blocker_seat2_x2",
        "source_belief_sha256": "aa3a5a8abe8dc72fe436134d4b619239a87b002134cdad88a908d833318b5067",
        "target_belief_sha256": "c9e24a106f970d3732b73c3a3325fd9b7f0fdbb0303d9621a5f1d0473301e718",
        "target_descriptor_sha256": "54e24bd368b9548b9e697815bed40dafc9f3c0f9704999b5a9f8167650d9d8e3",
    },
    {
        "target": "panel_2/balanced/local_blocker_seat2_x2",
        "board_id": "panel_2",
        "board": ["2c", "3s", "5d", "Js", "Qc"],
        "range_family": "balanced",
        "target_shift": "local_blocker_seat2_x2",
        "source_belief_sha256": "0662b2cf2436cbc6dcc5669fe75a2c15f03e652fb40a6903703a10dd14cfa289",
        "target_belief_sha256": "e359c590a2effaf6350274dd972a09e39a4fef37c57e548fd1fadef970128ed1",
        "target_descriptor_sha256": "b365f22dd814c132c60b5eb796c6b7e618fb7bc004006aa32b5dddce1d435f8a",
    },
    {
        "target": "panel_2/blocker_heavy/local_blocker_seat2_x2",
        "board_id": "panel_2",
        "board": ["2c", "3s", "5d", "Js", "Qc"],
        "range_family": "blocker_heavy",
        "target_shift": "local_blocker_seat2_x2",
        "source_belief_sha256": "59f955c6b89bdc56670dc16b19795451404fe80ff37f519bac007975d85200f1",
        "target_belief_sha256": "41e485b87d097862e4b6021adcbdab4470bfa2f759c695acab3b6c3edbce6c4f",
        "target_descriptor_sha256": "8d73f8025ba7b0bdf2fbdb32e0a96a127c9bfa0ca86fc5873145e9790973c326",
    },
    {
        "target": "panel_3/balanced/local_blocker_seat2_x2",
        "board_id": "panel_3",
        "board": ["4h", "7h", "9s", "Jd", "Kc"],
        "range_family": "balanced",
        "target_shift": "local_blocker_seat2_x2",
        "source_belief_sha256": "cadd9449259f56de43ae4d710c2e3fd6ae4733e7b7c8323836b87578a3cc9a71",
        "target_belief_sha256": "1014d3b5e6a6aaebce7189788612c94dafe8f2b826da76e2ed568b1abc2bdef5",
        "target_descriptor_sha256": "34ae37969a5247c209e2b411c729a2791c6f2025fb47e41163e58c55bc39970f",
    },
    {
        "target": "panel_3/blocker_heavy/local_blocker_seat2_x2",
        "board_id": "panel_3",
        "board": ["4h", "7h", "9s", "Jd", "Kc"],
        "range_family": "blocker_heavy",
        "target_shift": "local_blocker_seat2_x2",
        "source_belief_sha256": "74ce0c18ac82e9ebb799be851f140c7011ad75671a3409f94c7db1db3187278e",
        "target_belief_sha256": "bdf83667215c4e951759bfa8116a6889802a5d4b4cbd20ca8c4ae808c2b9187f",
        "target_descriptor_sha256": "78ee07ed9b45184ca3fc9850a9231ab28411736420b6729b5c5457de74a8e4a3",
    },
]

_DIRECTION_FAMILIES = ["soft_dcfr", "regret_vertex", "best_response_vertex"]
_FEATURES = [
    "regret_mass",
    "negative_minimum_action_gap",
    "vertex_probe_estimated_cap_radius",
    "vertex_probe_positive_value",
]


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required causal-screen input is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_h32_fresh_causal_direction_screen_config(
    config: dict[str, Any],
) -> dict[str, Any]:
    """Validate ADR-0185's complete pre-label causal-screen contract."""

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
        "block_anchor_selection",
        "block_membership",
        "acting_seats",
        "direction_families",
        "best_response_vertex_rule",
        "opportunity_features",
        "action_gap_rule",
        "vertex_probe_scale_index",
        "vertex_probe_rule",
        "directional_slope_rule",
        "selector_tie_break",
        "material_third_family_ratio",
        "candidate_feature_minimum_spearman",
        "candidate_feature_minimum_top1_capture",
        "scale_grid",
        "numerical_floor",
        "radius_search",
        "objective_search",
        "convex_scope",
        "certificate_anchor_rule",
        "seat_order",
        "acceptance_guard_normalized",
        "maximum_feature_width_per_batch",
        "measurement_context",
        "street_budget_ms",
        "emission_reserve_ms",
        "emitted_policy",
        "maximum_warm_start_probability_error",
        "maximum_warm_start_mean_total_variation",
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
        raise ValueError("fresh causal-screen fields differ from ADR-0185")
    frozen = {
        "evidence_stage": "preregistered_after_adr0184_before_any_seat2_target_policy_step_quality_label_or_probe",
        "seed": 20260821,
        "targets": _FROZEN_TARGETS,
        "target_construction": "double_label_free_maximum_overlap_then_strength_then_smallest_canonical_hand_at_seat2",
        "local_blocker_target_seat": 2,
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
        "acting_seats": [0, 1, 2, 3, 4, 5],
        "direction_families": _DIRECTION_FAMILIES,
        "best_response_vertex_rule": "per_information_set_pure_immutable_blueprint_best_response_action_first_action_tie_break",
        "opportunity_features": _FEATURES,
        "action_gap_rule": "negative_normalized_per_seat_minimum_blueprint_best_response_action_gap",
        "vertex_probe_scale_index": 16,
        "vertex_probe_rule": "one_exact_regret_vertex_certificate_at_two_to_negative_16_per_block_reused_if_adaptive_search_queries_it",
        "directional_slope_rule": "probe_gain_delta_divided_by_scale_with_cap_radius_guard_over_maximum_positive_observed_gain_slope",
        "selector_tie_break": "lowest_acting_seat_then_lexicographic_public_history",
        "material_third_family_ratio": 2.0,
        "candidate_feature_minimum_spearman": 0.5,
        "candidate_feature_minimum_top1_capture": 0.5,
        "scale_grid": "shared_geometric_halving_inclusive_while_scale_at_least_numerical_floor",
        "numerical_floor": 1e-10,
        "radius_search": "exact_endpoint_then_discrete_bisection_for_first_complete_scale",
        "objective_search": "exact_binary_unimodal_minimum_nashconv_over_complete_scale_suffix",
        "convex_scope": "one_common_scale_one_acting_seat_one_exact_public_node_no_union",
        "certificate_anchor_rule": "immutable_source_average64_independent_one_shot_for_every_queried_scale_never_reanchors",
        "seat_order": [0, 1, 2, 3, 4, 5],
        "acceptance_guard_normalized": 1e-10,
        "maximum_feature_width_per_batch": 384,
        "measurement_context": "off_clock_causal_direction_screen_not_a_live_scheduler",
        "street_budget_ms": 15000.0,
        "emission_reserve_ms": 1000.0,
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
        raise ValueError("fresh causal-screen workload differs from ADR-0185")
    for field, path in _PATHS.items():
        if config[field] != _sha256(path):
            raise ValueError(f"fresh causal-screen source mismatch: {field}")
    gates = {
        "expected_target_rows": 6,
        "expected_search_steps": 6,
        "expected_public_blocks": 36,
        "expected_direction_rows": 108,
        "expected_vertex_probes": 36,
        "expected_blueprint_quality_labels": 6,
        "maximum_adaptive_queries_per_direction": 16,
        "maximum_unique_queries_per_direction": 17,
        "maximum_total_certificate_queries": 1764,
        "maximum_search_step_ms": 60000.0,
        "maximum_certificate_ms": 60000.0,
        "maximum_gpu_pool_bytes": 12000000000,
        "minimum_physical_free_bytes": 1000000000,
        "maximum_total_audit_seconds": 3000.0,
        "require_clean_git_state": True,
        "require_parent_passed": True,
        "require_source_checkpoint_identity": True,
        "require_target_identity": True,
        "require_blueprint_identity": True,
        "require_numerical_warm_start_identity": True,
        "require_nonempty_coherent_blocks": True,
        "require_direction_family_identity": True,
        "require_best_response_vertex_identity": True,
        "require_feature_prelabel_identity": True,
        "require_probe_identity": True,
        "require_convex_scope": True,
        "require_search_invariants": True,
        "require_immutable_anchor": True,
        "require_independent_certificates": True,
        "require_regret_recovery_finite": True,
        "require_blueprint_emission": True,
        "require_finite": True,
        "require_strategy_population_claim_null": True,
    }
    if config["gates"] != gates:
        raise ValueError("fresh causal-screen gates differ from ADR-0185")
    return {
        **config,
        "targets": tuple(dict(row) for row in config["targets"]),
        "acting_seats": tuple(config["acting_seats"]),
        "direction_families": tuple(config["direction_families"]),
        "opportunity_features": tuple(config["opportunity_features"]),
        "seat_order": tuple(config["seat_order"]),
        "gates": dict(gates),
    }


def build_fresh_seat2_target(
    source: Any,
    *,
    board: tuple[int, ...],
    target_seat: int,
) -> tuple[Any, dict[str, Any]]:
    """Construct one frozen positive seat-2 shift without policy labels."""

    if target_seat != 2:
        raise ValueError("fresh causal-screen target seat differs from ADR-0185")
    likelihoods, detail = _local_blocker_likelihoods(
        source,
        board=board,
        target_seat=target_seat,
    )
    target = source
    for seat, likelihood in enumerate(likelihoods):
        target = target.with_likelihood(seat, likelihood)
    values = np.concatenate(likelihoods)
    return target, {
        "shift": "local_blocker_seat2_x2",
        "likelihood_minimum": float(np.min(values)),
        "likelihood_maximum": float(np.max(values)),
        "likelihood_mean": float(np.mean(values)),
        "positive_likelihoods": bool(np.all(values > 0.0)),
        "hand_axes_identity": target.hands_by_player == source.hands_by_player,
        **detail,
    }


def build_best_response_vertex_candidate(
    blueprint: Mapping[str, Mapping[Any, float]],
    best_response_actions: Mapping[str, Any],
    information_keys: Sequence[str],
) -> dict[str, dict[Any, float]]:
    """Move selected infosets to the immutable blueprint best-response action."""

    selected = tuple(information_keys)
    if len(selected) != len(set(selected)) or set(selected) - set(blueprint):
        raise ValueError("best-response vertex information-set selection is invalid")
    result = {
        key: {action: float(value) for action, value in row.items()}
        for key, row in blueprint.items()
    }
    for key in selected:
        if key not in best_response_actions:
            raise ValueError("best-response vertex action is unavailable")
        winner = best_response_actions[key]
        actions = tuple(blueprint[key])
        if winner not in actions:
            raise ValueError("best-response vertex action schema differs")
        result[key] = {action: float(action == winner) for action in actions}
    return dict(sorted(result.items()))


def vertex_probe_features(
    probe_row: Mapping[str, Any],
    blueprint_quality: Mapping[str, Any],
    *,
    raw_guard: float,
    payoff_span: float,
) -> dict[str, Any]:
    """Extract finite directional-sensitivity features from one charged probe."""

    scale = float(probe_row["scale"])
    if scale <= 0.0 or raw_guard <= 0.0 or payoff_span <= 0.0:
        raise ValueError("vertex probe feature scales must be positive")
    certificate = probe_row["certificate"]
    base_gains = tuple(float(value) for value in blueprint_quality["deviation_gains"])
    gain_slopes = []
    for row in certificate["seat_rows"]:
        seat = int(row["target_player"])
        gain_slopes.append(
            {
                "seat": seat,
                "gain_slope": (float(row["deviation_gain"]) - base_gains[seat]) / scale,
            }
        )
    maximum_positive = max(
        (max(0.0, float(row["gain_slope"])) for row in gain_slopes),
        default=0.0,
    )
    estimated_radius = 1.0 if maximum_positive <= 0.0 else min(1.0, raw_guard / maximum_positive)
    quality = certificate["quality"]
    objective_slope = 0.0
    if quality is not None:
        objective_slope = (
            float(blueprint_quality["nash_conv"]) - float(quality["nash_conv"])
        ) / scale
    return {
        "scale_index": int(probe_row["scale_index"]),
        "scale": scale,
        "complete": bool(certificate["complete"]),
        "stop_reason": str(certificate["stop_reason"]),
        "stop_seat": certificate["stop_seat"],
        "evaluated_seat_count": len(gain_slopes),
        "gain_slopes": gain_slopes,
        "maximum_positive_observed_gain_slope": maximum_positive,
        "normalized_maximum_positive_observed_gain_slope": maximum_positive / payoff_span,
        "estimated_cap_radius": estimated_radius,
        "cap_radius_censored": not bool(certificate["complete"]),
        "objective_improvement_slope": objective_slope,
        "normalized_objective_improvement_slope": objective_slope / payoff_span,
        "positive_certified_value": float(probe_row["positive_certified_value"]),
        "positive_value_slope": float(probe_row["positive_certified_value"]) / scale,
        "certificate_wall_ms": float(certificate["wall_ms"]),
        "construction_ms": float(probe_row["construction_ms"]),
    }


def direction_binding_constraint(search: Mapping[str, Any]) -> str:
    """Classify the constraint immediately outside the largest complete scale."""

    rows = {int(row["scale_index"]): row for row in search["queried_rows"]}
    boundary = search["largest_complete_scale_index"]
    if boundary is None:
        floor = max(rows)
        return str(rows[floor]["certificate"]["stop_reason"])
    boundary = int(boundary)
    if boundary == 0:
        return "grid_endpoint_complete"
    return str(rows[boundary - 1]["certificate"]["stop_reason"])


def select_feature_block(
    blocks: Sequence[Mapping[str, Any]],
    *,
    feature: str,
) -> Mapping[str, Any]:
    """Select one block using the frozen high-score and structural tie-break."""

    if feature not in _FEATURES:
        raise ValueError("unknown causal-screen feature")
    return min(
        blocks,
        key=lambda block: (
            -float(block["feature_scores"][feature]),
            int(block["acting_seat"]),
            str(block["public_history"]),
        ),
    )


def _search_direction(
    *,
    parsed: dict[str, Any],
    direction_family: str,
    direction_candidate: dict[str, dict[Any, float]],
    acting_seat: int,
    public_history: str,
    information_keys: tuple[str, ...],
    scales: tuple[float, ...],
    blueprint: dict[str, dict[Any, float]],
    blueprint_digest: str,
    blueprint_quality: dict[str, Any],
    layout: Any,
    belief: Any,
    context: Any,
    shared: Any,
    gpu: Any,
    cp: Any,
    memory_rows: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """Run one convex direction search, optionally seeding the fixed probe."""

    blueprint_nash = float(blueprint_quality["nash_conv"])
    raw_guard = parsed["acceptance_guard_normalized"] * parsed["stack"]
    evaluated: dict[int, dict[str, Any]] = {}

    def evaluate(scale_index: int) -> dict[str, Any]:
        if scale_index in evaluated:
            return evaluated[scale_index]
        construction_started = time.perf_counter()
        policy = interpolate_policy_atoms(
            blueprint,
            direction_candidate,
            information_keys,
            scale=scales[scale_index],
        )
        construction_ms = (time.perf_counter() - construction_started) * 1000.0
        certificate = _certificate(
            candidate_id=(
                f"seat{acting_seat}_{direction_family}@scale_{scale_index:02d}"
            ),
            policy=policy,
            layout=layout,
            belief=belief,
            context=context,
            shared=shared,
            gpu=gpu,
            blueprint_quality=blueprint_quality,
            parsed=parsed,
        )
        quality = certificate["quality"]
        value = (
            0.0
            if quality is None
            else _positive_value(blueprint_nash, float(quality["nash_conv"]))
        )
        memory = _memory_snapshot(cp)
        memory_rows.append(memory)
        row = {
            "scale_index": scale_index,
            "scale": scales[scale_index],
            "policy_sha256": policy_digest(policy),
            "construction_ms": construction_ms,
            "changed_information_set_count": len(
                atomic_policy_manifest(blueprint, policy)
            ),
            "certificate_anchor_policy_sha256": blueprint_digest,
            "certificate_anchor_nash_conv": blueprint_nash,
            "independent_from_blueprint": True,
            "positive_certified_value": value,
            "normalized_objective_reduction": (
                None
                if quality is None
                else (blueprint_nash - float(quality["nash_conv"]))
                / parsed["stack"]
            ),
            "value_per_certificate_second": _safe_ratio(
                value,
                float(certificate["wall_ms"]) / 1000.0,
            ),
            **certificate_binding_diagnostics(
                certificate,
                blueprint_quality,
                raw_guard,
            ),
            "certificate": certificate,
            "memory_after": memory,
        }
        evaluated[scale_index] = row
        return row

    probe_row = None
    probe_index = int(parsed["vertex_probe_scale_index"])
    if direction_family == "regret_vertex":
        probe_row = evaluate(probe_index)
    search_started = time.perf_counter()
    search = exact_discrete_convex_scale_search(evaluate, scale_count=len(scales))
    search_wall_ms = (time.perf_counter() - search_started) * 1000.0
    best_index = search["best_complete_scale_index"]
    best_row = (
        None
        if best_index is None
        else next(
            row
            for row in search["queried_rows"]
            if int(row["scale_index"]) == int(best_index)
        )
    )
    boundary_index = search["largest_complete_scale_index"]
    boundary_row = (
        None
        if boundary_index is None
        else next(
            row
            for row in search["queried_rows"]
            if int(row["scale_index"]) == int(boundary_index)
        )
    )
    unique_rows = [evaluated[index] for index in sorted(evaluated)]
    direction = {
        "direction_family": direction_family,
        "acting_seat": acting_seat,
        "public_history": public_history,
        "information_keys": list(information_keys),
        "information_set_count": len(information_keys),
        "direction_policy_sha256": policy_digest(direction_candidate),
        "search_wall_ms": search_wall_ms,
        "search": search,
        "unique_query_count": len(unique_rows),
        "unique_queried_rows": unique_rows,
        "probe_scale_index": probe_index if probe_row is not None else None,
        "probe_reused_by_adaptive_search": (
            None
            if probe_row is None
            else probe_index in tuple(int(value) for value in search["query_order"])
        ),
        "probe_policy_sha256": (
            None if probe_row is None else probe_row["policy_sha256"]
        ),
        "binding_constraint": direction_binding_constraint(search),
        "largest_complete_scale": (
            None if boundary_row is None else boundary_row["scale"]
        ),
        "best_complete_scale": None if best_row is None else best_row["scale"],
        "best_positive_certified_value": (
            0.0 if best_row is None else best_row["positive_certified_value"]
        ),
        "best_value_per_certificate_second": (
            None if best_row is None else best_row["value_per_certificate_second"]
        ),
        "best_certificate_wall_ms": (
            None if best_row is None else best_row["certificate"]["wall_ms"]
        ),
    }
    return direction, probe_row


def _run_target(
    parsed: dict[str, Any],
    source_parent: dict[str, Any],
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
        for row in source_parent["source_rows"]
        if row["source"] == f"{target_spec['board_id']}/{family}"
    )
    state = parent_row["final_checkpoint"]
    source_checkpoint_identity = (
        axis_cfr_checkpoint_digest(state) == state["state_sha256"]
        and source_digest == target_spec["source_belief_sha256"]
        and source_digest == parent_row["source_belief_sha256"]
    )
    blueprint = _average_policy_from_state(state)
    blueprint_digest = policy_digest(blueprint)
    blueprint_identity = blueprint_digest == state["average_policy_sha256"]
    belief, descriptor = build_fresh_seat2_target(
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
    warm_mass = (
        parsed["warm_regret_mass_payoff_fraction"] * float(layout.game.payoff_span)
    )
    solver.warm_start(blueprint, warm_mass)
    warm_start_distance = _policy_distance(blueprint, solver.current_strategy())
    release_cupy_memory_pool()
    memory_rows = [_memory_snapshot(cp)]
    search_started = time.perf_counter()
    solver.step()
    search_ms = (time.perf_counter() - search_started) * 1000.0
    soft_candidate = solver.current_strategy()
    regret_deltas = recover_iteration_one_dcfr_regret_deltas(
        blueprint,
        solver.regret_table(),
        warm_regret_mass=warm_mass,
    )
    memory_rows.append(_memory_snapshot(cp))
    anchors = select_one_atom_per_acting_seat(
        layout,
        belief.hands_by_player,
        blueprint,
        soft_candidate,
    )
    blocks = build_public_node_blocks(blueprint, soft_candidate, anchors)
    scales = geometric_halving_scales(numerical_floor=parsed["numerical_floor"])
    probe_index = int(parsed["vertex_probe_scale_index"])
    if probe_index not in range(len(scales)) or scales[probe_index] != 2.0**-16:
        raise ValueError("vertex probe scale identity failed")
    raw_guard = parsed["acceptance_guard_normalized"] * parsed["stack"]
    blueprint_nash = float(blueprint_quality["nash_conv"])
    block_rows = []
    for block in blocks:
        seat = int(block["acting_seat"])
        keys = tuple(block["information_keys"])
        proxy = block_regret_opportunity_proxy(
            blueprint,
            regret_deltas,
            keys,
            payoff_span=parsed["stack"],
        )
        response_source = context.response_caches[seat].source_evaluation
        action_gap = float(response_source.minimum_action_gap)
        quality_action_gap = float(
            blueprint_quality["seat_rows"][seat]["minimum_action_gap"]
        )
        action_gap_identity = abs(action_gap - quality_action_gap) <= 1e-12
        regret_vertex = build_regret_vertex_candidate(
            blueprint,
            regret_deltas,
            keys,
        )
        best_response_vertex = build_best_response_vertex_candidate(
            blueprint,
            response_source.best_response_actions,
            keys,
        )
        best_response_vertex_identity = all(
            best_response_vertex[key][response_source.best_response_actions[key]]
            == 1.0
            and math.fsum(best_response_vertex[key].values()) == 1.0
            for key in keys
        )
        candidates = {
            "soft_dcfr": soft_candidate,
            "regret_vertex": regret_vertex,
            "best_response_vertex": best_response_vertex,
        }
        free_features_prelabel = True
        family_rows = []
        probe_row = None
        for direction_family in parsed["direction_families"]:
            direction_row, possible_probe = _search_direction(
                parsed=parsed,
                direction_family=direction_family,
                direction_candidate=candidates[direction_family],
                acting_seat=seat,
                public_history=str(block["public_history"]),
                information_keys=keys,
                scales=scales,
                blueprint=blueprint,
                blueprint_digest=blueprint_digest,
                blueprint_quality=blueprint_quality,
                layout=layout,
                belief=belief,
                context=context,
                shared=shared,
                gpu=gpu,
                cp=cp,
                memory_rows=memory_rows,
            )
            family_rows.append(direction_row)
            if possible_probe is not None:
                if probe_row is not None:
                    raise AssertionError("vertex probe executed more than once per block")
                probe_row = possible_probe
        if tuple(row["direction_family"] for row in family_rows) != tuple(
            parsed["direction_families"]
        ):
            raise AssertionError("direction family order changed")
        if probe_row is None:
            raise AssertionError("vertex probe was not executed")
        probe = vertex_probe_features(
            probe_row,
            blueprint_quality,
            raw_guard=raw_guard,
            payoff_span=parsed["stack"],
        )
        by_family = {row["direction_family"]: row for row in family_rows}
        soft_value = float(by_family["soft_dcfr"]["best_positive_certified_value"])
        vertex_value = float(
            by_family["regret_vertex"]["best_positive_certified_value"]
        )
        best_response_value = float(
            by_family["best_response_vertex"]["best_positive_certified_value"]
        )
        two_direction_value = max(soft_value, vertex_value)
        oracle_value = max(two_direction_value, best_response_value)
        winner = next(
            family
            for family in parsed["direction_families"]
            if float(by_family[family]["best_positive_certified_value"])
            == oracle_value
        )
        feature_scores = {
            "regret_mass": float(
                proxy["normalized_positive_best_action_regret_mass"]
            ),
            "negative_minimum_action_gap": -action_gap / parsed["stack"],
            "vertex_probe_estimated_cap_radius": float(
                probe["estimated_cap_radius"]
            ),
            "vertex_probe_positive_value": float(probe["positive_certified_value"]),
        }
        block_rows.append(
            {
                **block,
                "opportunity_proxy": proxy,
                "minimum_action_gap": action_gap,
                "normalized_minimum_action_gap": action_gap / parsed["stack"],
                "action_gap_identity": action_gap_identity,
                "best_response_vertex_identity": best_response_vertex_identity,
                "free_features_prelabel": free_features_prelabel,
                "feature_scores": feature_scores,
                "vertex_probe": probe,
                "vertex_probe_policy_sha256": probe_row["policy_sha256"],
                "direction_rows": family_rows,
                "two_direction_oracle_positive_certified_value": two_direction_value,
                "bounded_oracle_positive_certified_value": oracle_value,
                "bounded_oracle_winner": winner,
                "best_response_vertex_incremental_value": (
                    oracle_value - two_direction_value
                ),
                "best_response_vertex_material_block_win": (
                    best_response_value > two_direction_value + raw_guard
                ),
                "bounded_oracle_fraction_of_blueprint_nash_conv": _safe_ratio(
                    oracle_value,
                    blueprint_nash,
                ),
            }
        )

    best_block = min(
        block_rows,
        key=lambda row: (
            -float(row["bounded_oracle_positive_certified_value"]),
            int(row["acting_seat"]),
            str(row["public_history"]),
        ),
    )
    selector_rows = []
    for feature in parsed["opportunity_features"]:
        selected = select_feature_block(block_rows, feature=feature)
        label = float(selected["bounded_oracle_positive_certified_value"])
        probe = selected["vertex_probe"]
        requires_all_probes = feature.startswith("vertex_probe_")
        selector_rows.append(
            {
                "feature": feature,
                "selected_acting_seat": int(selected["acting_seat"]),
                "selected_public_history": str(selected["public_history"]),
                "selected_feature_score": float(selected["feature_scores"][feature]),
                "selected_bounded_oracle_value": label,
                "target_best_bounded_oracle_value": float(
                    best_block["bounded_oracle_positive_certified_value"]
                ),
                "offline_top1_capture_fraction": _safe_ratio(
                    label,
                    float(best_block["bounded_oracle_positive_certified_value"]),
                ),
                "requires_all_six_block_probes_before_selection": requires_all_probes,
                "one_selected_probe_complete": bool(probe["complete"]),
                "one_selected_probe_positive_value": float(
                    probe["positive_certified_value"]
                ),
                "one_selected_probe_ledger_ms": (
                    search_ms
                    + float(probe["construction_ms"])
                    + float(probe["certificate_wall_ms"])
                    + parsed["emission_reserve_ms"]
                ),
            }
        )

    result = {
        "target": target_spec["target"],
        "board_id": target_spec["board_id"],
        "board": target_spec["board"],
        "range_family": str(target_spec["range_family"]),
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
        "soft_candidate_policy_sha256": policy_digest(soft_candidate),
        "changed_information_set_count": len(
            atomic_policy_manifest(blueprint, soft_candidate)
        ),
        "regret_delta_recovery_finite": all(
            math.isfinite(value)
            for row in regret_deltas.values()
            for value in row.values()
        ),
        "scale_grid": list(scales),
        "block_rows": block_rows,
        "selector_rows": selector_rows,
        "emitted_candidate_id": "blueprint_average64",
        "emitted_policy_sha256": blueprint_digest,
        "memory_rows": memory_rows,
    }
    del solver, context, shared, gpu, workspace, base, automata, source_workspace
    del sparse, layout, belief, source
    gc.collect()
    release_cupy_memory_pool()
    return result


def _mean_present(values: Sequence[float | None]) -> float | None:
    present = [float(value) for value in values if value is not None]
    return None if not present else math.fsum(present) / len(present)


def _finite_tree(value: Any) -> bool:
    if isinstance(value, bool) or value is None:
        return True
    if isinstance(value, (int, float)):
        return math.isfinite(float(value))
    if isinstance(value, Mapping):
        return all(_finite_tree(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return all(_finite_tree(item) for item in value)
    return True


def _feature_diagnostics(
    targets: Sequence[Mapping[str, Any]],
    *,
    parsed: Mapping[str, Any],
) -> list[dict[str, Any]]:
    blocks = [block for target in targets for block in target["block_rows"]]
    selectors = [row for target in targets for row in target["selector_rows"]]
    target_best_sum = math.fsum(
        max(
            float(block["bounded_oracle_positive_certified_value"])
            for block in target["block_rows"]
        )
        for target in targets
    )
    rows = []
    for feature in parsed["opportunity_features"]:
        pooled = spearman_rank_correlation(
            [float(block["feature_scores"][feature]) for block in blocks],
            [float(block["bounded_oracle_positive_certified_value"]) for block in blocks],
        )
        within = [
            spearman_rank_correlation(
                [
                    float(block["feature_scores"][feature])
                    for block in target["block_rows"]
                ],
                [
                    float(block["bounded_oracle_positive_certified_value"])
                    for block in target["block_rows"]
                ],
            )
            for target in targets
        ]
        selected = [row for row in selectors if row["feature"] == feature]
        selected_label_sum = math.fsum(
            float(row["selected_bounded_oracle_value"]) for row in selected
        )
        selected_probe_sum = math.fsum(
            float(row["one_selected_probe_positive_value"]) for row in selected
        )
        capture = _safe_ratio(selected_label_sum, target_best_sum)
        free_before_probe = not feature.startswith("vertex_probe_")
        candidate = (
            free_before_probe
            and pooled is not None
            and float(pooled) >= parsed["candidate_feature_minimum_spearman"]
            and capture is not None
            and float(capture) >= parsed["candidate_feature_minimum_top1_capture"]
        )
        rows.append(
            {
                "feature": feature,
                "available_before_any_candidate_certificate": free_before_probe,
                "pooled_spearman_with_bounded_oracle_value": pooled,
                "within_target_spearman": within,
                "mean_within_target_spearman": _mean_present(within),
                "selected_bounded_oracle_value_sum": selected_label_sum,
                "target_best_bounded_oracle_value_sum": target_best_sum,
                "aggregate_top1_opportunity_capture_fraction": capture,
                "selected_fixed_probe_positive_value_sum": selected_probe_sum,
                "selected_fixed_probe_complete_targets": sum(
                    bool(row["one_selected_probe_complete"]) for row in selected
                ),
                "selected_fixed_probe_ledger_fit_targets": sum(
                    float(row["one_selected_probe_ledger_ms"])
                    <= parsed["street_budget_ms"]
                    for row in selected
                ),
                "descriptive_candidate_for_separate_transfer": candidate,
            }
        )
    return rows


def run_h32_fresh_causal_direction_screen(
    config_path: Path = _CONFIG,
    output_path: Path = _OUTPUT,
) -> dict[str, Any]:
    """Execute the frozen causal feature and three-direction opportunity screen."""

    started = time.perf_counter()
    parsed = parse_h32_fresh_causal_direction_screen_config(
        json.loads(config_path.read_text(encoding="utf-8"))
    )
    source_parent = json.loads(_SOURCE.read_text(encoding="utf-8"))
    vertex_parent = json.loads(_VERTEX_PARENT.read_text(encoding="utf-8"))
    parent = json.loads(_PARENT_RESULT.read_text(encoding="utf-8"))
    git = _strict_git_metadata()
    cp, runtime = _validate_runtime(parsed)
    if git["dirty"]:
        raise RuntimeError("fresh causal-screen execution requires a clean Git state")
    if (
        not source_parent["passed"]
        or not vertex_parent["gates"]["passed"]
        or not parent["gates"]["passed"]
    ):
        raise ValueError("fresh causal-screen parent did not pass")
    targets = []
    for target_spec in parsed["targets"]:
        print(f"fresh causal direction screen: {target_spec['target']}", flush=True)
        targets.append(_run_target(parsed, source_parent, target_spec, cp))

    blocks = [block for target in targets for block in target["block_rows"]]
    directions = [
        direction
        for block in blocks
        for direction in block["direction_rows"]
    ]
    queries = [
        row
        for direction in directions
        for row in direction["unique_queried_rows"]
    ]
    probes = [block["vertex_probe"] for block in blocks]
    memory_rows = [row for target in targets for row in target["memory_rows"]]
    feature_rows = _feature_diagnostics(targets, parsed=parsed)
    total_seconds = time.perf_counter() - started
    gates_config = parsed["gates"]
    two_direction_value = math.fsum(
        float(block["two_direction_oracle_positive_certified_value"])
        for block in blocks
    )
    three_direction_value = math.fsum(
        float(block["bounded_oracle_positive_certified_value"])
        for block in blocks
    )
    raw_guard = parsed["acceptance_guard_normalized"] * parsed["stack"]
    material_third_family_lift = (
        three_direction_value
        >= parsed["material_third_family_ratio"] * two_direction_value
        and three_direction_value
        > two_direction_value + raw_guard * len(blocks)
    )
    parent_passed = (
        source_parent["passed"]
        and vertex_parent["gates"]["passed"]
        and parent["gates"]["passed"]
    )
    gates = {
        "clean_git": (not git["dirty"])
        == gates_config["require_clean_git_state"],
        "parent_passed": parent_passed
        == gates_config["require_parent_passed"],
        "target_rows": len(targets) == gates_config["expected_target_rows"],
        "search_steps": len(targets) == gates_config["expected_search_steps"],
        "public_blocks": len(blocks) == gates_config["expected_public_blocks"],
        "direction_rows": len(directions)
        == gates_config["expected_direction_rows"],
        "vertex_probes": len(probes) == gates_config["expected_vertex_probes"],
        "blueprint_quality_labels": len(targets)
        == gates_config["expected_blueprint_quality_labels"],
        "source_checkpoint_identity": all(
            target["source_checkpoint_identity"] for target in targets
        )
        == gates_config["require_source_checkpoint_identity"],
        "target_identity": all(target["target_identity"] for target in targets)
        == gates_config["require_target_identity"],
        "blueprint_identity": all(
            target["blueprint_identity"] for target in targets
        )
        == gates_config["require_blueprint_identity"],
        "numerical_warm_start_identity": all(
            target["warm_start_distance"]["maximum_probability_error"]
            <= parsed["maximum_warm_start_probability_error"]
            and target["warm_start_distance"]["mean_total_variation"]
            <= parsed["maximum_warm_start_mean_total_variation"]
            for target in targets
        )
        == gates_config["require_numerical_warm_start_identity"],
        "nonempty_coherent_blocks": all(
            block["information_set_count"] > 0
            and all(
                information_key_public_coordinates(key)
                == (int(block["acting_seat"]), str(block["public_history"]))
                for key in block["information_keys"]
            )
            for block in blocks
        )
        == gates_config["require_nonempty_coherent_blocks"],
        "direction_family_identity": all(
            tuple(
                row["direction_family"] for row in block["direction_rows"]
            )
            == tuple(parsed["direction_families"])
            for block in blocks
        )
        == gates_config["require_direction_family_identity"],
        "best_response_vertex_identity": all(
            block["best_response_vertex_identity"] for block in blocks
        )
        == gates_config["require_best_response_vertex_identity"],
        "feature_prelabel_identity": all(
            block["free_features_prelabel"]
            and block["action_gap_identity"]
            and tuple(block["feature_scores"])
            == tuple(parsed["opportunity_features"])
            for block in blocks
        )
        == gates_config["require_feature_prelabel_identity"],
        "probe_identity": all(
            int(block["vertex_probe"]["scale_index"])
            == parsed["vertex_probe_scale_index"]
            and next(
                row
                for row in block["direction_rows"]
                if row["direction_family"] == "regret_vertex"
            )["probe_policy_sha256"]
            == block["vertex_probe_policy_sha256"]
            for block in blocks
        )
        == gates_config["require_probe_identity"],
        "convex_scope": all(
            direction_has_convex_scope(direction) for direction in directions
        )
        == gates_config["require_convex_scope"],
        "search_invariants": all(
            search_invariants(direction["search"], scale_count=34)
            and int(direction["search"]["query_count"])
            <= gates_config["maximum_adaptive_queries_per_direction"]
            and int(direction["unique_query_count"])
            <= gates_config["maximum_unique_queries_per_direction"]
            for direction in directions
        )
        == gates_config["require_search_invariants"],
        "certificate_query_count": len(queries)
        <= gates_config["maximum_total_certificate_queries"],
        "immutable_anchor": all(
            row["certificate_anchor_policy_sha256"]
            == target["blueprint_quality"]["policy_sha256"]
            and row["certificate_anchor_nash_conv"]
            == target["blueprint_quality"]["nash_conv"]
            for target in targets
            for block in target["block_rows"]
            for direction in block["direction_rows"]
            for row in direction["unique_queried_rows"]
        )
        == gates_config["require_immutable_anchor"],
        "independent_certificates": all(
            row["independent_from_blueprint"] for row in queries
        )
        == gates_config["require_independent_certificates"],
        "regret_recovery_finite": all(
            target["regret_delta_recovery_finite"] for target in targets
        )
        == gates_config["require_regret_recovery_finite"],
        "blueprint_emission": all(
            target["emitted_candidate_id"] == "blueprint_average64"
            and target["emitted_policy_sha256"]
            == target["blueprint_quality"]["policy_sha256"]
            for target in targets
        )
        == gates_config["require_blueprint_emission"],
        "search_step_ms": all(
            target["search_step_ms"] <= gates_config["maximum_search_step_ms"]
            for target in targets
        ),
        "certificate_ms": all(
            row["certificate"]["wall_ms"]
            <= gates_config["maximum_certificate_ms"]
            for row in queries
        ),
        "memory": max(row["gpu_pool_total_bytes"] for row in memory_rows)
        <= gates_config["maximum_gpu_pool_bytes"]
        and min(row["gpu_free_bytes"] for row in memory_rows)
        >= gates_config["minimum_physical_free_bytes"],
        "finite": _finite_tree(targets) and _finite_tree(feature_rows),
        "strategy_population_claim_null": True
        == gates_config["require_strategy_population_claim_null"],
        "total_audit_seconds": total_seconds
        <= gates_config["maximum_total_audit_seconds"],
    }
    gates["passed"] = all(gates.values())
    result = {
        "schema_version": 1,
        "status": "frozen_h32_fresh_causal_direction_screen_executed",
        "methodology": {
            "preregistered": True,
            "fresh_target_quality_labels": True,
            "measurement_context": "off_clock_causal_screen",
            "target_population_claim": None,
            "deployment_authorized": False,
            "emitted_policy": "immutable_blueprint",
            "adaptive_labels_available_online": False,
            "all_block_probe_selection_available_online": False,
            "one_selected_probe_ledgers_descriptive": True,
        },
        "config_sha256": _sha256(config_path),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "environment": {**environment_metadata(), **runtime, "git": git},
        "target_rows": targets,
        "feature_diagnostics": feature_rows,
        "aggregate": {
            "targets": len(targets),
            "public_blocks": len(blocks),
            "direction_rows": len(directions),
            "vertex_probes": len(probes),
            "certificate_queries": len(queries),
            "adaptive_certificate_queries": sum(
                int(direction["search"]["query_count"])
                for direction in directions
            ),
            "probe_certificates_reused_by_adaptive_search": sum(
                direction["direction_family"] == "regret_vertex"
                and bool(direction["probe_reused_by_adaptive_search"])
                for direction in directions
            ),
            "two_direction_oracle_positive_certified_value": two_direction_value,
            "three_direction_oracle_positive_certified_value": three_direction_value,
            "third_family_lift_ratio": _safe_ratio(
                three_direction_value,
                two_direction_value,
            ),
            "third_family_material_lift": material_third_family_lift,
            "best_response_vertex_oracle_wins": sum(
                block["bounded_oracle_winner"] == "best_response_vertex"
                for block in blocks
            ),
            "best_response_vertex_material_block_wins": sum(
                block["best_response_vertex_material_block_win"] for block in blocks
            ),
            "binding_constraints": {
                reason: sum(
                    direction["binding_constraint"] == reason
                    for direction in directions
                )
                for reason in (
                    "blueprint_cap",
                    "objective_lower_bound",
                    "grid_endpoint_complete",
                )
            },
            "complete_vertex_probes": sum(probe["complete"] for probe in probes),
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
            "accept_prospective_causal_direction_screen"
            if gates["passed"]
            else "reject_fresh_causal_direction_screen"
        ),
        "strategy_population_claim": None,
        "limitations": [
            "Six deliberately constructed seat-2 belief shifts are not a population.",
            "The adaptive direction searches and all-block probe rankings are off-clock labels.",
            "Only a free selector followed by one fixed probe has a descriptive street ledger.",
            "No feature, direction, observed scale, or candidate is emitted or deployed.",
            "The three-direction oracle remains a lower bound on attainable local value.",
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
    result = run_h32_fresh_causal_direction_screen(args.config, args.output)
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
