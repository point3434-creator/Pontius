"""Retained-label affine selector-cascade replay.

The GPU phase reconstructs every sealed h32 context and computes the frozen
feature matrix for all three already-labelled direction families.  The label
artifact is not opened until the feature matrix and clock-derived capacities
are complete.  This is feature extraction against retained labels, not a new
strategy-label campaign.
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
from .delta_certificate_contract import interpolate_policy_atoms
from .evidence_protocol import DEFAULT_GPU_NUMERICAL_IDENTITY
from .factor_tt_contraction import FactorTTBeliefWorkspace
from .fresh_h32_strategy_transfer_audit import _belief_digest
from .h32_affine_resident_cache_preflight import _strict_git_metadata, _validate_runtime
from .h32_atomic_response_preflight import select_one_atom_per_acting_seat
from .h32_fresh_board_panel_cache_preflight import _json_digest
from .h32_fresh_causal_direction_screen import (
    _DIRECTION_FAMILIES,
    _FROZEN_TARGETS,
    build_best_response_vertex_candidate,
    build_fresh_seat2_target,
)
from .h32_fresh_public_block_value_audit import build_public_node_blocks
from .h32_fresh_regret_vertex_opportunity_audit import (
    block_regret_opportunity_proxy,
    build_regret_vertex_candidate,
    recover_iteration_one_dcfr_regret_deltas,
    spearman_rank_correlation,
)
from .h32_fresh_union_value_audit import _memory_snapshot, _safe_ratio
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
from .resident_leaf_adjoint_cfr import ResidentLeafAdjointPublicTreeCFR
from .river import parse_cards
from .selector_stable_affine_response import (
    SelectorStableAffineSeatResult,
    certify_selector_stable_affine_envelope,
    evaluate_selector_stable_affine_leaf_adjoint_seat,
)
from .shared_resident_response_context import (
    SharedResidentAutomatonBundle,
    bind_resident_response_context,
)


_ROOT = Path(__file__).parents[2]
_CONFIG = (
    _ROOT
    / "experiments/configs/h32-retained-affine-selector-cascade-replay-v1.json"
)
_OUTPUT = (
    _ROOT
    / "experiments/results/h32-retained-affine-selector-cascade-replay-v1.json"
)
_SOURCE = _ROOT / "experiments/results/h32-fresh-panel-source-blueprints-v1.json"
_LABEL_CONFIG = (
    _ROOT / "experiments/configs/h32-fresh-causal-direction-screen-v1.json"
)
_LABEL_RESULT = (
    _ROOT / "experiments/results/h32-fresh-causal-direction-screen-v1.json"
)
_LABEL_ADR = (
    _ROOT
    / "docs/decisions"
    / "ADR-0186-fresh-vertices-replicate-generator-weakness-but-no-free-selector-transfers.md"
)
_AFFINE_CONFIG = (
    _ROOT / "experiments/configs/h32-selector-stable-affine-certificate-v2.json"
)
_AFFINE_RESULT = (
    _ROOT / "experiments/results/h32-selector-stable-affine-certificate-v2.json"
)
_AFFINE_ADR = (
    _ROOT
    / "docs/decisions"
    / "ADR-0190-selector-stable-affine-certificate-is-exact-and-fits-retained-street-ledgers.md"
)
_PROFILE_RESULT = (
    _ROOT / "experiments/results/h32-resident-step-bottleneck-profile-v2.json"
)
_PROFILE_ADR = (
    _ROOT
    / "docs/decisions/ADR-0198-device-pipeline-dominates-h32-step-host-fold-is-second.md"
)
_REQUIREMENTS = (
    _ROOT / "experiments/requirements/leaf-adjoint-gpu-screen-v1.txt"
)
_IMPLEMENTATION = Path(__file__)
_TEST = _ROOT / "tests/test_h32_retained_affine_selector_cascade_replay.py"

_PATHS = {
    "expected_source_result_sha256": _SOURCE,
    "expected_label_config_sha256": _LABEL_CONFIG,
    "expected_label_result_sha256": _LABEL_RESULT,
    "expected_label_decision_sha256": _LABEL_ADR,
    "expected_affine_config_sha256": _AFFINE_CONFIG,
    "expected_affine_result_sha256": _AFFINE_RESULT,
    "expected_affine_decision_sha256": _AFFINE_ADR,
    "expected_profile_result_sha256": _PROFILE_RESULT,
    "expected_profile_decision_sha256": _PROFILE_ADR,
    "expected_requirements_sha256": _REQUIREMENTS,
    "expected_target_builder_sha256": (
        _ROOT / "src/pontius/h32_fresh_causal_direction_screen.py"
    ),
    "expected_public_block_builder_sha256": (
        _ROOT / "src/pontius/h32_fresh_public_block_value_audit.py"
    ),
    "expected_direction_builder_sha256": (
        _ROOT / "src/pontius/h32_fresh_regret_vertex_opportunity_audit.py"
    ),
    "expected_affine_verifier_sha256": (
        _ROOT / "src/pontius/selector_stable_affine_response.py"
    ),
    "expected_shared_context_sha256": (
        _ROOT / "src/pontius/shared_resident_response_context.py"
    ),
    "expected_resident_cfr_sha256": (
        _ROOT / "src/pontius/resident_leaf_adjoint_cfr.py"
    ),
    "expected_interpolation_sha256": (
        _ROOT / "src/pontius/delta_certificate_contract.py"
    ),
    "expected_evidence_protocol_sha256": (
        _ROOT / "src/pontius/evidence_protocol.py"
    ),
    "expected_audit_implementation_sha256": _IMPLEMENTATION,
    "expected_control_test_sha256": _TEST,
}

_FEATURES = (
    "regret_mass",
    "negative_minimum_action_gap",
    "vertex_probe_estimated_cap_radius",
    "vertex_probe_positive_value",
    "tier_a_exact_own_gain_improvement_slope",
    "tier_b_exact_objective_improvement_slope",
    "tier_b_cap_radius",
    "tier_b_slope_predicted_value",
)
_SET_FAMILIES = {
    "regret_vertex_only": ("regret_vertex",),
    "all_families": tuple(_DIRECTION_FAMILIES),
    "soft_excluded": ("regret_vertex", "best_response_vertex"),
}
_FAMILY_ORDER = {family: index for index, family in enumerate(_DIRECTION_FAMILIES)}


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required selector-replay input is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_h32_retained_affine_selector_cascade_config(
    config: dict[str, Any],
) -> dict[str, Any]:
    """Validate ADR-0199's retained-feature and sealed-label protocol."""

    fields = {
        "evidence_stage",
        *_PATHS,
        "seed",
        "targets",
        "candidate_families",
        "candidate_sets",
        "primary_candidate_set",
        "secondary_candidate_set",
        "family_confound_control_set",
        "feature_list",
        "tier_a_identity",
        "tier_a_scope",
        "tier_b_charge",
        "tier_b_cap_radius",
        "tier_b_objective_slope",
        "tier_b_composite",
        "feature_label_order",
        "label_field",
        "score_rule",
        "recall_rule",
        "random_floor_rule",
        "clairvoyant_ceiling_rule",
        "structural_tie_break",
        "diagnostic_k_ladders",
        "capacity_rule",
        "tier_a_capacity_variants",
        "street_budget_ms",
        "emission_reserve_ms",
        "descriptive_materiality_floor_raw_guards",
        "prediction_composite",
        "prediction_tier_a",
        "prediction_policy",
        "measurement_context",
        "emitted_policy",
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
        "acceptance_guard_normalized",
        "selector_margin_allowance",
        "envelope_numerical_allowance",
        "safety_fraction",
        "numerical_floor",
        "maximum_feature_width_per_batch",
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
        raise ValueError("retained affine selector replay fields differ from ADR-0199")
    frozen = {
        "evidence_stage": (
            "preregistered_after_adr0198_before_any_missing_affine_feature_"
            "extraction_or_retained_label_join"
        ),
        "seed": 20260821,
        "targets": _FROZEN_TARGETS,
        "candidate_families": list(_DIRECTION_FAMILIES),
        "candidate_sets": {
            key: list(value) for key, value in _SET_FAMILIES.items()
        },
        "primary_candidate_set": "regret_vertex_only",
        "secondary_candidate_set": "all_families",
        "family_confound_control_set": "soft_excluded",
        "feature_list": list(_FEATURES),
        "tier_a_identity": (
            "acting_seat_only_d_gain_i_ds_equals_negative_d_u_i_ds_exact_"
            "because_own_best_response_value_is_policy_invariant"
        ),
        "tier_a_scope": (
            "exactly_one_public_node_and_no_off_seat_policy_probability_change"
        ),
        "tier_b_charge": (
            "exactly_five_opponent_best_response_conditioned_contraction_calls_"
            "with_device_contraction_and_reverse_overhead_reported_separately"
        ),
        "tier_b_cap_radius": (
            "minimum_over_positive_gain_slopes_of_anchor_cap_budget_divided_by_"
            "slope_clipped_to_zero_one_without_selector_stability"
        ),
        "tier_b_objective_slope": (
            "negative_anchor_directional_derivative_of_positive_part_nashconv_"
            "using_the_affine_envelope_anchor_rule"
        ),
        "tier_b_composite": (
            "maximum_zero_objective_improvement_slope_times_cap_radius"
        ),
        "feature_label_order": (
            "opaque_sha256_validation_may_read_label_bytes_up_front_but_compute_"
            "all_108_candidate_feature_rows_and_clock_capacities_before_label_"
            "json_deserialization_or_any_per_row_join"
        ),
        "label_field": (
            "retained_direction_best_positive_certified_value_from_adr0186"
        ),
        "score_rule": (
            "within_target_high_feature_first_then_structural_tie_break"
        ),
        "recall_rule": (
            "top_k_contains_canonical_highest_label_and_value_capture_is_best_"
            "label_inside_top_k_divided_by_target_best_label"
        ),
        "random_floor_rule": (
            "exact_uniform_k_subset_expected_best_label_and_k_over_n_recall"
        ),
        "clairvoyant_ceiling_rule": (
            "canonical_highest_label_recalled_and_full_target_value_at_every_"
            "positive_k"
        ),
        "structural_tie_break": (
            "lowest_acting_seat_then_lexicographic_public_history_then_frozen_"
            "direction_family_order"
        ),
        "diagnostic_k_ladders": {
            "regret_vertex_only": [1, 2, 3, 4, 5, 6],
            "all_families": [1, 2, 4, 6, 8, 12, 15, 18],
            "soft_excluded": [1, 2, 4, 6, 8, 10, 12],
        },
        "capacity_rule": (
            "per_target_before_label_join_floor_of_remaining_15000ms_after_"
            "warm_step_1000ms_reserve_all_set_tier_a_cost_and_one_max_envelope_"
            "cost_divided_by_max_set_tier_b_opponent_wall_cost_capped_by_set_size"
        ),
        "tier_a_capacity_variants": [
            "current_zero_contraction_reverse_cost_charged",
            "diagnostic_warm_telemetry_reuse_with_tier_a_reverse_cost_zero",
        ],
        "street_budget_ms": 15000.0,
        "emission_reserve_ms": 1000.0,
        "descriptive_materiality_floor_raw_guards": 1.0,
        "prediction_composite": (
            "tier_b_composite_wins_pooled_value_weighted_recall_and_its_misses_"
            "concentrate_on_cap_radius_overshooting_selector_stable_radius"
        ),
        "prediction_tier_a": (
            "tier_a_clears_value_recall_at_k_at_least_8_only_on_the_weak_"
            "secondary_18_set_because_the_primary_set_has_only_6_candidates"
        ),
        "prediction_policy": (
            "predictions_are_report_only_and_cannot_pass_or_fail_validity_gates"
        ),
        "measurement_context": (
            "off_clock_retained_label_feature_replay_not_a_live_scheduler_or_"
            "fresh_strategy_experiment"
        ),
        "emitted_policy": "immutable_blueprint_only",
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
        "selector_margin_allowance": 2e-11,
        "envelope_numerical_allowance": 2e-11,
        "safety_fraction": 0.5,
        "numerical_floor": 1e-10,
        "maximum_feature_width_per_batch": 384,
        "maximum_warm_start_probability_error": (
            DEFAULT_GPU_NUMERICAL_IDENTITY.maximum_policy_probability_error
        ),
        "maximum_warm_start_mean_total_variation": (
            DEFAULT_GPU_NUMERICAL_IDENTITY.maximum_policy_mean_information_set_total_variation
        ),
        "required_numpy_version": "2.5.2",
        "required_scipy_version": "1.18.0",
        "required_cupy_version": "14.2.0",
        "required_cuda_runtime_version": 13020,
        "minimum_cuda_driver_version": 13000,
        "required_compute_capability": "120",
        "cuda_dll_environment_variable": "PONTIUS_CUDA_DLL_DIRECTORY",
    }
    if any(config[key] != value for key, value in frozen.items()):
        raise ValueError("retained affine selector replay workload differs from ADR-0199")
    for field, path in _PATHS.items():
        if config[field] != _sha256(path):
            raise ValueError(f"retained affine selector replay source mismatch: {field}")
    gates = {
        "expected_target_rows": 6,
        "expected_public_blocks": 36,
        "expected_candidate_rows": 108,
        "expected_affine_seat_rows": 648,
        "expected_primary_candidates_per_target": 6,
        "expected_secondary_candidates_per_target": 18,
        "expected_soft_excluded_candidates_per_target": 12,
        "expected_opponent_br_calls_per_candidate": 5,
        "maximum_own_br_slope_error": 2e-11,
        "maximum_tier_a_identity_error": 2e-11,
        "maximum_affine_intercept_error": 2e-11,
        "maximum_source_quality_error": 2e-11,
        "maximum_search_step_ms": 60000.0,
        "maximum_candidate_feature_ms": 60000.0,
        "maximum_gpu_pool_bytes": 12000000000,
        "minimum_physical_free_bytes": 1000000000,
        "maximum_total_audit_seconds": 1800.0,
        "require_clean_git_state": True,
        "require_source_parent_passed": True,
        "require_label_parent_passed": True,
        "require_source_checkpoint_identity": True,
        "require_target_identity": True,
        "require_blueprint_identity": True,
        "require_numerical_warm_start_identity": True,
        "require_complete_feature_matrix_before_label_join": True,
        "require_direction_family_identity": True,
        "require_acting_seat_only_scope": True,
        "require_tier_a_impure_negative_control": True,
        "require_five_not_six_charge_control": True,
        "require_blueprint_emission": True,
        "require_finite": True,
        "require_strategy_population_claim_null": True,
    }
    if config["gates"] != gates:
        raise ValueError("retained affine selector replay gates differ from ADR-0199")
    return {
        **config,
        "targets": tuple(dict(row) for row in config["targets"]),
        "candidate_families": tuple(config["candidate_families"]),
        "candidate_sets": {
            key: tuple(value) for key, value in config["candidate_sets"].items()
        },
        "feature_list": tuple(config["feature_list"]),
        "diagnostic_k_ladders": {
            key: tuple(value)
            for key, value in config["diagnostic_k_ladders"].items()
        },
        "gates": dict(gates),
    }


def _field(row: SelectorStableAffineSeatResult | Mapping[str, Any], name: str) -> Any:
    return row[name] if isinstance(row, Mapping) else getattr(row, name)


def affine_tier_features(
    rows: Sequence[SelectorStableAffineSeatResult | Mapping[str, Any]],
    *,
    acting_seat: int,
    raw_guard: float,
    numerical_allowance: float,
    blueprint_deviation_gains: Sequence[float] | None = None,
) -> dict[str, Any]:
    """Return the frozen exact Tier-A and Tier-B features and priced work."""

    ordered = sorted(rows, key=lambda row: int(_field(row, "target_player")))
    if tuple(int(_field(row, "target_player")) for row in ordered) != tuple(range(6)):
        raise ValueError("affine tier pricing requires one ordered row per seat")
    if any(int(_field(row, "acting_player")) != acting_seat for row in ordered):
        raise ValueError("affine tier rows disagree on acting seat")
    own = ordered[acting_seat]
    opponents = [row for row in ordered if int(_field(row, "target_player")) != acting_seat]
    if len(opponents) != 5:
        raise ValueError("Tier B must charge exactly five opponent BR rows")
    if int(_field(own, "affected_terminal_contractions")) != 0:
        raise ValueError("Tier A own row unexpectedly contracted terminal values")

    own_utility_slope = float(_field(own, "profile_utility_slope"))
    own_br_slope = float(_field(own, "best_response_value_slope"))
    own_gain_slope = float(_field(own, "deviation_gap_slope"))
    tier_a_error = abs(own_gain_slope + own_utility_slope)
    anchor_gains = (
        tuple(float(_field(row, "deviation_gain_intercept")) for row in ordered)
        if blueprint_deviation_gains is None
        else tuple(float(value) for value in blueprint_deviation_gains)
    )
    if len(anchor_gains) != 6:
        raise ValueError("affine tier anchor gain vector has the wrong width")

    initial_nash_slope = math.fsum(
        (
            float(_field(row, "deviation_gap_slope"))
            if float(_field(row, "deviation_gain_intercept")) > numerical_allowance
            else max(0.0, float(_field(row, "deviation_gap_slope")))
        )
        for row in ordered
    )
    objective_improvement_slope = -initial_nash_slope
    cap_radius = 1.0
    cap_budgets = []
    for seat, row in enumerate(ordered):
        intercept = float(_field(row, "deviation_gain_intercept"))
        slope = float(_field(row, "deviation_gap_slope"))
        budget = anchor_gains[seat] + raw_guard - numerical_allowance - intercept
        cap_budgets.append(budget)
        if budget < 0.0:
            cap_radius = 0.0
            break
        if slope > 0.0:
            cap_radius = min(cap_radius, budget / slope)
    cap_radius = min(1.0, max(0.0, cap_radius))
    selector_radius = min(
        1.0, *(float(_field(row, "selector_stable_scale")) for row in ordered)
    )
    opponent_contraction_ms = math.fsum(
        float(_field(row, "terminal_contraction_ms")) for row in opponents
    )
    opponent_reverse_ms = math.fsum(
        float(_field(row, "reverse_evaluation_ms")) for row in opponents
    )
    opponent_wall_ms = math.fsum(float(_field(row, "wall_ms")) for row in opponents)
    return {
        "features": {
            "tier_a_exact_own_gain_improvement_slope": -own_gain_slope,
            "tier_b_exact_objective_improvement_slope": objective_improvement_slope,
            "tier_b_cap_radius": cap_radius,
            "tier_b_slope_predicted_value": (
                max(0.0, objective_improvement_slope) * cap_radius
            ),
        },
        "identity": {
            "own_best_response_value_slope": own_br_slope,
            "tier_a_identity_error": tier_a_error,
            "acting_seat_only": all(
                int(_field(row, "changed_public_nodes")) == 1
                and int(_field(row, "acting_player")) == acting_seat
                for row in ordered
            ),
        },
        "radii": {
            "cap_radius": cap_radius,
            "selector_stable_radius": selector_radius,
            "cap_minus_selector_radius": cap_radius - selector_radius,
            "cap_radius_overshoots_selector": cap_radius > selector_radius,
            "cap_budgets": cap_budgets,
        },
        "cost": {
            "opponent_br_conditioned_calls": len(opponents),
            "opponent_affected_terminal_terms": sum(
                int(_field(row, "affected_terminal_contractions"))
                for row in opponents
            ),
            "opponent_terminal_contraction_ms": opponent_contraction_ms,
            "opponent_reverse_evaluation_ms": opponent_reverse_ms,
            "opponent_other_overhead_ms": max(
                0.0, opponent_wall_ms - opponent_contraction_ms - opponent_reverse_ms
            ),
            "opponent_wall_ms": opponent_wall_ms,
            "acting_zero_contraction_reverse_ms": float(
                _field(own, "reverse_evaluation_ms")
            ),
            "acting_zero_contraction_wall_ms": float(_field(own, "wall_ms")),
        },
    }


def contaminated_tier_a_negative_control() -> dict[str, Any]:
    """Demonstrate that one off-seat edit invalidates the free Tier-A identity."""

    def utility(own_a: float, opponent_l: float) -> float:
        return own_a * opponent_l + (1.0 - own_a) * (1.0 - opponent_l)

    def best_response(opponent_l: float) -> float:
        return max(opponent_l, 1.0 - opponent_l)

    source_own = 0.25
    endpoint_own = 0.50
    source_opponent = 0.80
    pure_endpoint_opponent = source_opponent
    impure_endpoint_opponent = 0.60
    source_utility = utility(source_own, source_opponent)
    source_gain = best_response(source_opponent) - source_utility

    pure_utility = utility(endpoint_own, pure_endpoint_opponent)
    pure_gain = best_response(pure_endpoint_opponent) - pure_utility
    pure_free_slope = -(pure_utility - source_utility)
    pure_teacher_slope = pure_gain - source_gain

    impure_utility = utility(endpoint_own, impure_endpoint_opponent)
    impure_gain = best_response(impure_endpoint_opponent) - impure_utility
    impure_free_slope = -(impure_utility - source_utility)
    impure_teacher_slope = impure_gain - source_gain
    disagreement = abs(impure_free_slope - impure_teacher_slope)
    return {
        "pure_changed_node_players": [0],
        "impure_changed_node_players": [0, 1],
        "pure_scope_accepted": True,
        "impure_scope_rejected": True,
        "pure_free_path_slope": pure_free_slope,
        "pure_endpoint_teacher_slope": pure_teacher_slope,
        "pure_identity_error": abs(pure_free_slope - pure_teacher_slope),
        "impure_free_path_slope": impure_free_slope,
        "impure_endpoint_teacher_slope": impure_teacher_slope,
        "impure_disagreement": disagreement,
        "passed": (
            abs(pure_free_slope - pure_teacher_slope) <= 1e-15
            and disagreement > 0.0
        ),
    }


def exact_random_value_floor(labels: Sequence[float], k: int) -> float:
    """Expected best value from a uniform k-subset, computed without sampling."""

    ordered = sorted(float(value) for value in labels)
    n = len(ordered)
    if not 1 <= k <= n:
        raise ValueError("random-floor K is outside the candidate set")
    denominator = math.comb(n, k)
    return math.fsum(
        value * math.comb(index, k - 1) / denominator
        for index, value in enumerate(ordered)
        if index >= k - 1
    )


def _structural_key(row: Mapping[str, Any]) -> tuple[Any, ...]:
    return (
        int(row["acting_seat"]),
        str(row["public_history"]),
        _FAMILY_ORDER[str(row["direction_family"])],
    )


def _ranked(
    rows: Sequence[Mapping[str, Any]], feature: str
) -> list[Mapping[str, Any]]:
    return sorted(
        rows,
        key=lambda row: (-float(row["features"][feature]), *_structural_key(row)),
    )


def _canonical_oracle(rows: Sequence[Mapping[str, Any]]) -> Mapping[str, Any]:
    return min(rows, key=lambda row: (-float(row["label"]), *_structural_key(row)))


def score_feature_at_k(
    rows: Sequence[Mapping[str, Any]], *, feature: str, k: int
) -> dict[str, Any]:
    """Score one frozen feature within one target and candidate stratum."""

    if not rows or not 1 <= k <= len(rows):
        raise ValueError("feature score K is outside the candidate set")
    ranked = _ranked(rows, feature)
    selected = ranked[:k]
    oracle = _canonical_oracle(rows)
    captured = max(float(row["label"]) for row in selected)
    oracle_value = float(oracle["label"])
    selected_keys = {_structural_key(row) for row in selected}
    random_value = exact_random_value_floor(
        [float(row["label"]) for row in rows], k
    )
    return {
        "k": k,
        "canonical_best_recalled": _structural_key(oracle) in selected_keys,
        "captured_value": captured,
        "oracle_value": oracle_value,
        "value_capture_fraction": _safe_ratio(captured, oracle_value),
        "random_recall_floor": k / len(rows),
        "random_expected_captured_value": random_value,
        "random_expected_value_capture_fraction": _safe_ratio(
            random_value, oracle_value
        ),
        "clairvoyant_recall_ceiling": 1.0,
        "clairvoyant_value_capture_ceiling": 1.0,
        "selected_candidate_keys": [list(_structural_key(row)) for row in selected],
        "oracle_candidate_key": list(_structural_key(oracle)),
    }


def _aggregate_feature_curve(
    targets: Sequence[Mapping[str, Any]],
    *,
    set_name: str,
    families: Sequence[str],
    feature: str,
    k_ladder: Sequence[int],
) -> dict[str, Any]:
    per_k = []
    for k in k_ladder:
        scored = []
        for target in targets:
            rows = [
                row
                for row in target["candidate_rows"]
                if row["direction_family"] in families
            ]
            scored.append(
                {
                    "target": target["target"],
                    **score_feature_at_k(rows, feature=feature, k=k),
                }
            )
        captured_sum = math.fsum(row["captured_value"] for row in scored)
        oracle_sum = math.fsum(row["oracle_value"] for row in scored)
        random_sum = math.fsum(
            row["random_expected_captured_value"] for row in scored
        )
        per_k.append(
            {
                "k": k,
                "per_target": scored,
                "mean_target_recall": math.fsum(
                    float(row["canonical_best_recalled"]) for row in scored
                )
                / len(scored),
                "pooled_value_weighted_capture_fraction": _safe_ratio(
                    captured_sum, oracle_sum
                ),
                "pooled_random_value_floor_fraction": _safe_ratio(
                    random_sum, oracle_sum
                ),
                "pooled_clairvoyant_value_ceiling_fraction": 1.0,
            }
        )
    pooled_rows = [
        row
        for target in targets
        for row in target["candidate_rows"]
        if row["direction_family"] in families
    ]
    within = []
    for target in targets:
        rows = [
            row
            for row in target["candidate_rows"]
            if row["direction_family"] in families
        ]
        within.append(
            spearman_rank_correlation(
                [float(row["features"][feature]) for row in rows],
                [float(row["label"]) for row in rows],
            )
        )
    return {
        "candidate_set": set_name,
        "feature": feature,
        "pooled_spearman": spearman_rank_correlation(
            [float(row["features"][feature]) for row in pooled_rows],
            [float(row["label"]) for row in pooled_rows],
        ),
        "within_target_spearman": within,
        "mean_within_target_spearman": (
            None
            if not any(value is not None for value in within)
            else math.fsum(float(value) for value in within if value is not None)
            / sum(value is not None for value in within)
        ),
        "curve": per_k,
    }


def derive_capacity(
    rows: Sequence[Mapping[str, Any]],
    *,
    search_step_ms: float,
    street_budget_ms: float,
    emission_reserve_ms: float,
) -> dict[str, Any]:
    """Derive label-blind current and warm-reuse K for one candidate set."""

    if not rows:
        raise ValueError("capacity requires at least one candidate")
    tier_a_ms = math.fsum(
        float(row["timing"]["endpoint_construction_ms"])
        + float(row["tier"]["cost"]["acting_zero_contraction_wall_ms"])
        for row in rows
    )
    construction_ms = math.fsum(
        float(row["timing"]["endpoint_construction_ms"]) for row in rows
    )
    tier_b_unit_ms = max(
        float(row["tier"]["cost"]["opponent_wall_ms"]) for row in rows
    )
    tier_c_ms = max(float(row["timing"]["envelope_ms"]) for row in rows)

    def capacity(charged_tier_a_ms: float) -> tuple[int, float]:
        remaining = (
            street_budget_ms
            - emission_reserve_ms
            - search_step_ms
            - charged_tier_a_ms
            - tier_c_ms
        )
        if tier_b_unit_ms <= 0.0:
            result = len(rows)
        else:
            result = max(0, math.floor(remaining / tier_b_unit_ms))
        return min(len(rows), result), remaining

    current_k, current_remaining = capacity(tier_a_ms)
    warm_reuse_k, warm_reuse_remaining = capacity(construction_ms)
    return {
        "candidate_count": len(rows),
        "search_step_ms": search_step_ms,
        "emission_reserve_ms": emission_reserve_ms,
        "all_candidate_endpoint_construction_ms": construction_ms,
        "all_candidate_current_tier_a_ms": tier_a_ms,
        "maximum_candidate_tier_b_opponent_wall_ms": tier_b_unit_ms,
        "maximum_one_winner_envelope_ms": tier_c_ms,
        "current_remaining_before_tier_b_ms": current_remaining,
        "warm_reuse_remaining_before_tier_b_ms": warm_reuse_remaining,
        "current_clock_feasible_k": current_k,
        "warm_reuse_diagnostic_k": warm_reuse_k,
        "current_library_limited": current_k == len(rows),
        "warm_reuse_library_limited": warm_reuse_k == len(rows),
    }


def _cascade_at_honest_k(
    rows: Sequence[Mapping[str, Any]], *, k: int
) -> dict[str, Any]:
    if k <= 0:
        return {
            "k": k,
            "complete": False,
            "selected_candidate_key": None,
            "selected_value": 0.0,
            "oracle_value": float(_canonical_oracle(rows)["label"]),
            "value_capture_fraction": 0.0,
        }
    tier_a = _ranked(rows, "tier_a_exact_own_gain_improvement_slope")[:k]
    winner = _ranked(tier_a, "tier_b_slope_predicted_value")[0]
    oracle = _canonical_oracle(rows)
    return {
        "k": k,
        "complete": True,
        "selected_candidate_key": list(_structural_key(winner)),
        "selected_value": float(winner["label"]),
        "oracle_value": float(oracle["label"]),
        "value_capture_fraction": _safe_ratio(
            float(winner["label"]), float(oracle["label"])
        ),
        "selected_cap_radius_overshoots_selector": bool(
            winner["tier"]["radii"]["cap_radius_overshoots_selector"]
        ),
    }


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


def _run_feature_target(
    parsed: Mapping[str, Any],
    source_parent: Mapping[str, Any],
    target_spec: Mapping[str, Any],
    cp: Any,
) -> dict[str, Any]:
    board = parse_cards(*target_spec["board"])
    family = str(target_spec["range_family"])
    source, layout, sparse, retained = _build_case(
        parsed=parsed,
        board=board,
        hand_count=int(parsed["hands_per_player"]),
        family=family,
    )
    source_workspace, _, automata = retained
    source_digest = _belief_digest(source)
    source_row = next(
        row
        for row in source_parent["source_rows"]
        if row["source"] == f"{target_spec['board_id']}/{family}"
    )
    state = source_row["final_checkpoint"]
    source_checkpoint_identity = (
        axis_cfr_checkpoint_digest(state) == state["state_sha256"]
        and source_digest == target_spec["source_belief_sha256"]
        and source_digest == source_row["source_belief_sha256"]
    )
    blueprint = _average_policy_from_state(state)
    blueprint_digest = policy_digest(blueprint)
    blueprint_identity = blueprint_digest == state["average_policy_sha256"]
    belief, descriptor = build_fresh_seat2_target(source, board=board, target_seat=2)
    target_digest = _belief_digest(belief)
    target_identity = (
        target_digest == target_spec["target_belief_sha256"]
        and _json_digest(descriptor) == target_spec["target_descriptor_sha256"]
        and belief.hands_by_player == source.hands_by_player
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
    blueprint_quality = _source_quality(context, payoff_span=float(parsed["stack"]))
    solver = ResidentLeafAdjointPublicTreeCFR(
        layout,
        workspace,
        sparse,
        automata,
        str(parsed["solver_variant"]),
        belief_cache=context.belief_cache,
        automaton_caches=shared.automaton_caches,
        cupy_sparse=gpu,
        maximum_feature_width_per_batch=int(parsed["maximum_feature_width_per_batch"]),
        hands_by_player=belief.hands_by_player,
    )
    warm_mass = float(parsed["warm_regret_mass_payoff_fraction"]) * float(
        layout.game.payoff_span
    )
    solver.warm_start(blueprint, warm_mass)
    warm_start_distance = _policy_distance(blueprint, solver.current_strategy())
    release_cupy_memory_pool()
    memory_rows = [_memory_snapshot(cp)]
    search_started = time.perf_counter()
    solver.step()
    search_step_ms = (time.perf_counter() - search_started) * 1000.0
    memory_rows.append(_memory_snapshot(cp))

    soft_candidate = solver.current_strategy()
    regret_deltas = recover_iteration_one_dcfr_regret_deltas(
        blueprint, solver.regret_table(), warm_regret_mass=warm_mass
    )
    anchors = select_one_atom_per_acting_seat(
        layout, belief.hands_by_player, blueprint, soft_candidate
    )
    blocks = build_public_node_blocks(blueprint, soft_candidate, anchors)
    raw_guard = float(parsed["acceptance_guard_normalized"]) * float(parsed["stack"])
    blueprint_gains = tuple(float(value) for value in blueprint_quality["deviation_gains"])
    blueprint_nash = float(blueprint_quality["nash_conv"])
    candidate_rows = []
    for block in blocks:
        acting_seat = int(block["acting_seat"])
        keys = tuple(block["information_keys"])
        response_source = context.response_caches[acting_seat].source_evaluation
        proxy = block_regret_opportunity_proxy(
            blueprint,
            regret_deltas,
            keys,
            payoff_span=float(parsed["stack"]),
        )
        block_features = {
            "regret_mass": float(
                proxy["normalized_positive_best_action_regret_mass"]
            ),
            "negative_minimum_action_gap": -float(response_source.minimum_action_gap)
            / float(parsed["stack"]),
        }
        for direction_family in parsed["candidate_families"]:
            candidate_started = time.perf_counter()
            if direction_family == "soft_dcfr":
                endpoint = interpolate_policy_atoms(
                    blueprint, soft_candidate, keys, scale=1.0
                )
            elif direction_family == "regret_vertex":
                endpoint = build_regret_vertex_candidate(
                    blueprint, regret_deltas, keys
                )
            elif direction_family == "best_response_vertex":
                endpoint = build_best_response_vertex_candidate(
                    blueprint, response_source.best_response_actions, keys
                )
            else:  # pragma: no cover - frozen parser makes this unreachable
                raise AssertionError("unknown frozen direction family")
            endpoint_probabilities = compile_policy_probability_tape(
                layout, belief.hands_by_player, endpoint
            )
            endpoint_construction_ms = (
                time.perf_counter() - candidate_started
            ) * 1000.0
            affine_started = time.perf_counter()
            affine_rows = tuple(
                evaluate_selector_stable_affine_leaf_adjoint_seat(
                    cache,
                    endpoint_probabilities,
                    acting_player=acting_seat,
                    selector_margin_allowance=float(
                        parsed["selector_margin_allowance"]
                    ),
                    maximum_feature_width_per_batch=int(
                        parsed["maximum_feature_width_per_batch"]
                    ),
                    belief_cache=context.belief_cache,
                    automaton_cache=shared.automaton_caches[target_player],
                    cupy_sparse=gpu,
                )
                for target_player, cache in enumerate(context.response_caches)
            )
            affine_sweep_ms = (time.perf_counter() - affine_started) * 1000.0
            tier = affine_tier_features(
                affine_rows,
                acting_seat=acting_seat,
                raw_guard=raw_guard,
                numerical_allowance=float(parsed["envelope_numerical_allowance"]),
                blueprint_deviation_gains=blueprint_gains,
            )
            envelope_started = time.perf_counter()
            envelope = certify_selector_stable_affine_envelope(
                affine_rows,
                blueprint_deviation_gains=blueprint_gains,
                blueprint_nash_conv=blueprint_nash,
                raw_guard=raw_guard,
                scale_grid=tuple(
                    2.0**-index
                    for index in range(34)
                    if 2.0**-index >= float(parsed["numerical_floor"])
                ),
                safety_fraction=float(parsed["safety_fraction"]),
                numerical_allowance=float(parsed["envelope_numerical_allowance"]),
            )
            envelope_ms = (time.perf_counter() - envelope_started) * 1000.0
            features = {**block_features, **tier["features"]}
            # These two frozen prior-probe features are attached only after the
            # feature matrix is complete and the sealed parent is opened.
            features["vertex_probe_estimated_cap_radius"] = None
            features["vertex_probe_positive_value"] = None
            candidate_rows.append(
                {
                    "acting_seat": acting_seat,
                    "public_history": str(block["public_history"]),
                    "information_keys": list(keys),
                    "information_set_count": len(keys),
                    "direction_family": direction_family,
                    "local_endpoint_policy_sha256": policy_digest(endpoint),
                    "features": features,
                    "tier": tier,
                    "affine_rows": [asdict(row) for row in affine_rows],
                    "envelope_diagnostic": {
                        "complete": bool(envelope.complete),
                        "stop_reason": str(envelope.stop_reason),
                        "selected_scale": envelope.selected_scale,
                        "selector_scale_limit": envelope.selector_scale_limit,
                        "cap_scale_limit": envelope.cap_scale_limit,
                        "objective_scale_limit": envelope.objective_scale_limit,
                        "safe_scale_limit": envelope.safe_scale_limit,
                    },
                    "timing": {
                        "endpoint_construction_ms": endpoint_construction_ms,
                        "affine_sweep_ms": affine_sweep_ms,
                        "envelope_ms": envelope_ms,
                        "complete_candidate_feature_ms": (
                            endpoint_construction_ms + affine_sweep_ms + envelope_ms
                        ),
                    },
                }
            )
            memory_rows.append(_memory_snapshot(cp))

    capacities = {}
    for set_name, families in parsed["candidate_sets"].items():
        rows = [
            row for row in candidate_rows if row["direction_family"] in families
        ]
        capacities[set_name] = derive_capacity(
            rows,
            search_step_ms=search_step_ms,
            street_budget_ms=float(parsed["street_budget_ms"]),
            emission_reserve_ms=float(parsed["emission_reserve_ms"]),
        )
    result = {
        "target": target_spec["target"],
        "board_id": target_spec["board_id"],
        "board": target_spec["board"],
        "range_family": family,
        "target_shift": target_spec["target_shift"],
        "source_belief_sha256": source_digest,
        "target_belief_sha256": target_digest,
        "source_checkpoint_identity": source_checkpoint_identity,
        "target_identity": target_identity,
        "blueprint_identity": blueprint_identity,
        "blueprint_policy_sha256": blueprint_digest,
        "blueprint_quality": blueprint_quality,
        "warm_start_distance": warm_start_distance,
        "search_step_ms": search_step_ms,
        "search_step_work_wall_ms": solver.last_step_work.wall_ms,
        "soft_candidate_policy_sha256_diagnostic": policy_digest(soft_candidate),
        "candidate_rows": candidate_rows,
        "capacity_before_label_join": capacities,
        "emitted_candidate_id": "blueprint_average64",
        "emitted_policy_sha256": blueprint_digest,
        "memory_rows": memory_rows,
    }
    del solver, context, shared, gpu, workspace, base, automata, source_workspace
    del sparse, layout, belief, source
    gc.collect()
    release_cupy_memory_pool()
    return result


def _join_retained_labels(
    feature_targets: list[dict[str, Any]],
    label_parent: Mapping[str, Any],
) -> dict[str, Any]:
    """Attach every frozen prior feature and label after GPU feature extraction."""

    direction_identities = []
    source_quality_errors = []
    for target in feature_targets:
        label_target = next(
            row
            for row in label_parent["target_rows"]
            if row["target"] == target["target"]
        )
        source_quality_errors.extend(
            abs(float(left) - float(right))
            for field in ("utilities", "best_response_values", "deviation_gains")
            for left, right in zip(
                target["blueprint_quality"][field],
                label_target["blueprint_quality"][field],
                strict=True,
            )
        )
        blocks = {
            (int(row["acting_seat"]), str(row["public_history"])): row
            for row in label_target["block_rows"]
        }
        for candidate in target["candidate_rows"]:
            block = blocks[
                (int(candidate["acting_seat"]), str(candidate["public_history"]))
            ]
            direction = next(
                row
                for row in block["direction_rows"]
                if row["direction_family"] == candidate["direction_family"]
            )
            scale_one = next(
                (
                    row
                    for row in direction["unique_queried_rows"]
                    if float(row["scale"]) == 1.0
                ),
                None,
            )
            expected_local_digest = (
                None if scale_one is None else str(scale_one["policy_sha256"])
            )
            digest_identity = (
                expected_local_digest == candidate["local_endpoint_policy_sha256"]
            )
            direction_identities.append(digest_identity)
            candidate["features"]["vertex_probe_estimated_cap_radius"] = float(
                block["vertex_probe"]["estimated_cap_radius"]
            )
            candidate["features"]["vertex_probe_positive_value"] = float(
                block["vertex_probe"]["positive_certified_value"]
            )
            candidate["label"] = float(direction["best_positive_certified_value"])
            candidate["label_metadata"] = {
                "best_complete_scale": direction["best_complete_scale"],
                "largest_complete_scale": direction["largest_complete_scale"],
                "binding_constraint": direction["binding_constraint"],
                "retained_direction_policy_sha256": direction[
                    "direction_policy_sha256"
                ],
                "retained_scale_one_policy_sha256": expected_local_digest,
                "local_endpoint_digest_identity_diagnostic": digest_identity,
            }
    return {
        "maximum_source_quality_error": max(source_quality_errors, default=0.0),
        "local_endpoint_digest_identities_diagnostic": direction_identities,
        "local_endpoint_digest_identity_fraction_diagnostic": (
            math.fsum(float(value) for value in direction_identities)
            / len(direction_identities)
        ),
    }


def _score_replay(
    targets: Sequence[Mapping[str, Any]], parsed: Mapping[str, Any]
) -> dict[str, Any]:
    curves = []
    set_rows = []
    descriptive_materiality_floor = (
        float(parsed["descriptive_materiality_floor_raw_guards"])
        * float(parsed["acceptance_guard_normalized"])
        * float(parsed["stack"])
    )
    for set_name, families in parsed["candidate_sets"].items():
        for feature in parsed["feature_list"]:
            curves.append(
                _aggregate_feature_curve(
                    targets,
                    set_name=set_name,
                    families=families,
                    feature=feature,
                    k_ladder=parsed["diagnostic_k_ladders"][set_name],
                )
            )
        per_target = []
        for target in targets:
            rows = [
                row
                for row in target["candidate_rows"]
                if row["direction_family"] in families
            ]
            capacity = target["capacity_before_label_join"][set_name]
            current = _cascade_at_honest_k(
                rows, k=int(capacity["current_clock_feasible_k"])
            )
            warm_reuse = _cascade_at_honest_k(
                rows, k=int(capacity["warm_reuse_diagnostic_k"])
            )
            current_charged_ms = (
                float(capacity["all_candidate_current_tier_a_ms"])
                + int(capacity["current_clock_feasible_k"])
                * float(capacity["maximum_candidate_tier_b_opponent_wall_ms"])
                + float(capacity["maximum_one_winner_envelope_ms"])
            )
            warm_reuse_charged_ms = (
                float(capacity["all_candidate_endpoint_construction_ms"])
                + int(capacity["warm_reuse_diagnostic_k"])
                * float(capacity["maximum_candidate_tier_b_opponent_wall_ms"])
                + float(capacity["maximum_one_winner_envelope_ms"])
            )
            current["conservative_charged_ms"] = current_charged_ms
            current["certified_value_per_charged_second"] = (
                0.0
                if current_charged_ms <= 0.0
                else float(current["selected_value"]) * 1000.0 / current_charged_ms
            )
            warm_reuse["conservative_charged_ms"] = warm_reuse_charged_ms
            warm_reuse["certified_value_per_charged_second"] = (
                0.0
                if warm_reuse_charged_ms <= 0.0
                else float(warm_reuse["selected_value"])
                * 1000.0
                / warm_reuse_charged_ms
            )
            per_target.append(
                {
                    "target": target["target"],
                    "capacity": capacity,
                    "current_cascade": current,
                    "warm_reuse_diagnostic_cascade": warm_reuse,
                    "descriptive_materiality_floor": descriptive_materiality_floor,
                    "oracle_above_descriptive_materiality_floor": (
                        float(current["oracle_value"]) > descriptive_materiality_floor
                    ),
                    "current_selected_above_descriptive_materiality_floor": (
                        float(current["selected_value"])
                        > descriptive_materiality_floor
                    ),
                }
            )
        current_selected = math.fsum(
            row["current_cascade"]["selected_value"] for row in per_target
        )
        current_oracle = math.fsum(
            row["current_cascade"]["oracle_value"] for row in per_target
        )
        warm_selected = math.fsum(
            row["warm_reuse_diagnostic_cascade"]["selected_value"]
            for row in per_target
        )
        set_rows.append(
            {
                "candidate_set": set_name,
                "families": list(families),
                "per_target": per_target,
                "current_clock_feasible_pooled_capture_fraction": _safe_ratio(
                    current_selected, current_oracle
                ),
                "warm_reuse_diagnostic_pooled_capture_fraction": _safe_ratio(
                    warm_selected, current_oracle
                ),
                "current_library_limited_targets": sum(
                    row["capacity"]["current_library_limited"]
                    for row in per_target
                ),
                "warm_reuse_library_limited_targets": sum(
                    row["capacity"]["warm_reuse_library_limited"]
                    for row in per_target
                ),
                "oracle_material_targets_descriptive": sum(
                    row["oracle_above_descriptive_materiality_floor"]
                    for row in per_target
                ),
                "current_selected_material_targets_descriptive": sum(
                    row["current_selected_above_descriptive_materiality_floor"]
                    for row in per_target
                ),
            }
        )

    primary_composite = next(
        row
        for row in curves
        if row["candidate_set"] == parsed["primary_candidate_set"]
        and row["feature"] == "tier_b_slope_predicted_value"
    )
    composite_top1 = next(row for row in primary_composite["curve"] if row["k"] == 1)
    misses = [row for row in composite_top1["per_target"] if not row["canonical_best_recalled"]]
    selected_by_target = []
    primary_families = parsed["candidate_sets"][parsed["primary_candidate_set"]]
    for target, score in zip(targets, composite_top1["per_target"], strict=True):
        rows = [
            row
            for row in target["candidate_rows"]
            if row["direction_family"] in primary_families
        ]
        selected = _ranked(rows, "tier_b_slope_predicted_value")[0]
        selected_by_target.append(
            {
                "target": target["target"],
                "miss": not score["canonical_best_recalled"],
                "selected_cap_radius_overshoots_selector": bool(
                    selected["tier"]["radii"]["cap_radius_overshoots_selector"]
                ),
                "selected_cap_minus_selector_radius": float(
                    selected["tier"]["radii"]["cap_minus_selector_radius"]
                ),
            }
        )
    return {
        "feature_curves": curves,
        "cascade_by_candidate_set": set_rows,
        "composite_top1_miss_localization": {
            "per_target": selected_by_target,
            "misses": len(misses),
            "misses_with_selected_cap_radius_overshoot": sum(
                row["miss"] and row["selected_cap_radius_overshoots_selector"]
                for row in selected_by_target
            ),
        },
    }


def run_h32_retained_affine_selector_cascade_replay(
    config_path: Path = _CONFIG,
    output_path: Path = _OUTPUT,
) -> dict[str, Any]:
    """Execute frozen feature extraction, then join and score sealed labels."""

    started = time.perf_counter()
    parsed = parse_h32_retained_affine_selector_cascade_config(
        json.loads(config_path.read_text(encoding="utf-8"))
    )
    source_parent = json.loads(_SOURCE.read_text(encoding="utf-8"))
    git = _strict_git_metadata()
    cp, runtime = _validate_runtime(parsed)
    if git["dirty"]:
        raise RuntimeError("retained affine selector replay requires clean Git state")
    if not bool(source_parent["passed"]):
        raise ValueError("retained affine selector source parent did not pass")

    feature_targets = []
    for target_spec in parsed["targets"]:
        print(f"retained affine selector features: {target_spec['target']}", flush=True)
        feature_targets.append(
            _run_feature_target(parsed, source_parent, target_spec, cp)
        )

    feature_payload = [
        {
            "target": target["target"],
            "candidate_rows": target["candidate_rows"],
            "capacity_before_label_join": target["capacity_before_label_join"],
        }
        for target in feature_targets
    ]
    feature_matrix_sha256_before_label_join = hashlib.sha256(
        json.dumps(feature_payload, sort_keys=True, allow_nan=False).encode("utf-8")
    ).hexdigest()

    # Deliberately delayed: config validation checked the sealed SHA-256 as opaque
    # bytes, but this is the first semantic parse of any retained label content.
    label_join_started = time.perf_counter()
    label_parent = json.loads(_LABEL_RESULT.read_text(encoding="utf-8"))
    label_deserialized_after_complete_feature_matrix = all(
        len(target["candidate_rows"]) == 18 for target in feature_targets
    )
    join = _join_retained_labels(feature_targets, label_parent)
    label_join_ms = (time.perf_counter() - label_join_started) * 1000.0
    scoring = _score_replay(feature_targets, parsed)
    negative_control = contaminated_tier_a_negative_control()

    candidates = [
        row for target in feature_targets for row in target["candidate_rows"]
    ]
    affine_rows = [row for candidate in candidates for row in candidate["affine_rows"]]
    memory_rows = [row for target in feature_targets for row in target["memory_rows"]]
    total_seconds = time.perf_counter() - started
    gates_config = parsed["gates"]
    maximum_warm_probability = max(
        target["warm_start_distance"]["maximum_probability_error"]
        for target in feature_targets
    )
    maximum_warm_mean_tv = max(
        target["warm_start_distance"]["mean_total_variation"]
        for target in feature_targets
    )
    maximum_own_br_error = max(
        abs(float(candidate["tier"]["identity"]["own_best_response_value_slope"]))
        for candidate in candidates
    )
    maximum_tier_a_error = max(
        float(candidate["tier"]["identity"]["tier_a_identity_error"])
        for candidate in candidates
    )
    intercept_errors = []
    for target in feature_targets:
        anchor_gains = target["blueprint_quality"]["deviation_gains"]
        for candidate in target["candidate_rows"]:
            intercept_errors.extend(
                abs(
                    float(row["deviation_gain_intercept"])
                    - float(anchor_gains[int(row["target_player"])])
                )
                for row in candidate["affine_rows"]
            )
    maximum_intercept_error = max(intercept_errors, default=0.0)
    max_pool = max(int(row["gpu_pool_total_bytes"]) for row in memory_rows)
    min_free = min(int(row["gpu_physical_free_bytes"]) for row in memory_rows)
    control_five = all(
        int(candidate["tier"]["cost"]["opponent_br_conditioned_calls"])
        == gates_config["expected_opponent_br_calls_per_candidate"]
        for candidate in candidates
    )
    finite_payload = {
        "targets": feature_targets,
        "join": join,
        "scoring": scoring,
        "negative_control": negative_control,
        "total_seconds": total_seconds,
    }
    gates = {
        "clean_git": (not git["dirty"]) == gates_config["require_clean_git_state"],
        "source_parent_passed": bool(source_parent["passed"])
        == gates_config["require_source_parent_passed"],
        "label_parent_passed": bool(label_parent["gates"]["passed"])
        == gates_config["require_label_parent_passed"],
        "target_rows": len(feature_targets) == gates_config["expected_target_rows"],
        "public_blocks": len(candidates) // 3
        == gates_config["expected_public_blocks"],
        "candidate_rows": len(candidates) == gates_config["expected_candidate_rows"],
        "affine_seat_rows": len(affine_rows)
        == gates_config["expected_affine_seat_rows"],
        "candidate_set_cardinality": all(
            sum(
                candidate["direction_family"] in parsed["candidate_sets"][set_name]
                for candidate in target["candidate_rows"]
            )
            == expected
            for target in feature_targets
            for set_name, expected in (
                (
                    "regret_vertex_only",
                    gates_config["expected_primary_candidates_per_target"],
                ),
                (
                    "all_families",
                    gates_config["expected_secondary_candidates_per_target"],
                ),
                (
                    "soft_excluded",
                    gates_config["expected_soft_excluded_candidates_per_target"],
                ),
            )
        ),
        "source_checkpoint_identity": all(
            target["source_checkpoint_identity"] for target in feature_targets
        )
        == gates_config["require_source_checkpoint_identity"],
        "target_identity": all(target["target_identity"] for target in feature_targets)
        == gates_config["require_target_identity"],
        "blueprint_identity": all(
            target["blueprint_identity"] for target in feature_targets
        )
        == gates_config["require_blueprint_identity"],
        "warm_start_probability_error": maximum_warm_probability
        <= parsed["maximum_warm_start_probability_error"],
        "warm_start_mean_total_variation": maximum_warm_mean_tv
        <= parsed["maximum_warm_start_mean_total_variation"],
        "complete_feature_matrix_before_label_join": (
            label_deserialized_after_complete_feature_matrix
            == gates_config["require_complete_feature_matrix_before_label_join"]
        ),
        "direction_family_identity": all(
            tuple(
                candidate["direction_family"]
                for candidate in target["candidate_rows"]
            )
            == tuple(
                family
                for _block in range(6)
                for family in parsed["candidate_families"]
            )
            for target in feature_targets
        )
        == gates_config["require_direction_family_identity"],
        "acting_seat_only_scope": all(
            candidate["tier"]["identity"]["acting_seat_only"]
            for candidate in candidates
        )
        == gates_config["require_acting_seat_only_scope"],
        "own_br_invariance": maximum_own_br_error
        <= gates_config["maximum_own_br_slope_error"],
        "tier_a_identity": maximum_tier_a_error
        <= gates_config["maximum_tier_a_identity_error"],
        "affine_intercepts": maximum_intercept_error
        <= gates_config["maximum_affine_intercept_error"],
        "source_quality": join["maximum_source_quality_error"]
        <= gates_config["maximum_source_quality_error"],
        "tier_a_impure_negative_control": bool(negative_control["passed"])
        == gates_config["require_tier_a_impure_negative_control"],
        "five_not_six_charge_control": control_five
        == gates_config["require_five_not_six_charge_control"],
        "search_step_ms": max(target["search_step_ms"] for target in feature_targets)
        <= gates_config["maximum_search_step_ms"],
        "candidate_feature_ms": max(
            candidate["timing"]["complete_candidate_feature_ms"]
            for candidate in candidates
        )
        <= gates_config["maximum_candidate_feature_ms"],
        "gpu_pool": max_pool <= gates_config["maximum_gpu_pool_bytes"],
        "physical_free": min_free >= gates_config["minimum_physical_free_bytes"],
        "total_audit_seconds": total_seconds
        <= gates_config["maximum_total_audit_seconds"],
        "blueprint_emission": all(
            target["emitted_candidate_id"] == "blueprint_average64"
            and target["emitted_policy_sha256"] == target["blueprint_policy_sha256"]
            for target in feature_targets
        )
        == gates_config["require_blueprint_emission"],
        "finite": _finite_tree(finite_payload) == gates_config["require_finite"],
        "strategy_population_claim_null": True
        == gates_config["require_strategy_population_claim_null"],
    }
    gates["passed"] = all(gates.values())
    result = {
        "schema_version": 1,
        "status": "frozen_h32_retained_affine_selector_cascade_replay_executed",
        "methodology": {
            "opaque_label_sha256_checked_before_feature_extraction": True,
            "feature_rows_computed_before_label_json_deserialization": True,
            "feature_list_frozen_before_extraction": True,
            "labels_retained_from_adr0186": True,
            "fresh_strategy_labels": 0,
            "primary_set": parsed["primary_candidate_set"],
            "secondary_set": parsed["secondary_candidate_set"],
            "family_confound_control": parsed["family_confound_control_set"],
            "capacity_derived_before_label_join": True,
            "exact_digests_diagnostic_only_for_reconstructed_floating_policies": True,
        },
        "environment": environment_metadata(
            parsed["seed"],
            extra={
                **runtime,
                "git_commit": git["commit"],
                "git_dirty": git["dirty"],
            },
        ),
        "config_sha256": _sha256(config_path),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "feature_matrix_sha256_before_label_join": (
            feature_matrix_sha256_before_label_join
        ),
        "label_join": {
            "deserialized_after_complete_feature_matrix": (
                label_deserialized_after_complete_feature_matrix
            ),
            "label_join_ms": label_join_ms,
            **join,
        },
        "negative_controls": {
            "impure_direction": negative_control,
            "five_not_six_charge_passed": control_five,
        },
        "target_rows": feature_targets,
        "scoring": scoring,
        "aggregate": {
            "targets": len(feature_targets),
            "public_blocks": len(candidates) // 3,
            "candidate_rows": len(candidates),
            "affine_seat_rows": len(affine_rows),
            "opponent_br_conditioned_calls": sum(
                int(candidate["tier"]["cost"]["opponent_br_conditioned_calls"])
                for candidate in candidates
            ),
            "maximum_own_br_slope_error": maximum_own_br_error,
            "maximum_tier_a_identity_error": maximum_tier_a_error,
            "maximum_affine_intercept_error": maximum_intercept_error,
            "maximum_warm_start_probability_error": maximum_warm_probability,
            "maximum_warm_start_mean_total_variation": maximum_warm_mean_tv,
            "maximum_gpu_pool_bytes": max_pool,
            "minimum_gpu_free_bytes": min_free,
        },
        "gates": gates,
        "passed": gates["passed"],
        "decision": (
            "accept_retained_affine_selector_cascade_replay"
            if gates["passed"]
            else "reject_retained_affine_selector_cascade_replay"
        ),
        "strategy_population_claim": None,
        "total_audit_seconds": total_seconds,
        "limitations": [
            "All six targets and every label were exposed before this development replay.",
            "The primary six-set may be library-limited; saturation is not selector evidence.",
            "The raw 18-set can reward family discrimination, so it is weak evidence only.",
            (
                "The soft-excluded 12-set controls that family confound but "
                "retains near-duplicate vertices."
            ),
            (
                "The warm-telemetry-reuse capacity is diagnostic until the "
                "zero-contraction Tier-A coefficient is exposed by the live step."
            ),
            (
                "No new strategy label, policy emission, deployment rule, or "
                "strategy-quality claim is authorized."
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
    result = run_h32_retained_affine_selector_cascade_replay(
        args.config, args.output
    )
    print(
        json.dumps(
            {
                "output": str(args.output),
                "passed": result["passed"],
                "aggregate": result["aggregate"],
                "scoring": result["scoring"]["cascade_by_candidate_set"],
            },
            indent=2,
        )
    )
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
