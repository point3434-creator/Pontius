"""Prospective paired h32 soft-generator and regret-vertex opportunity audit."""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import math
from pathlib import Path
import time
from typing import Any, Callable, Mapping, Sequence

import numpy as np

from .axis_cfr_checkpoint import axis_cfr_checkpoint_digest
from .cupy_sparse_incidence import CuPyBidirectionalIncidence, release_cupy_memory_pool
from .delta_certificate_contract import atomic_policy_manifest, geometric_halving_scales, interpolate_policy_atoms
from .factor_tt_contraction import FactorTTBeliefWorkspace
from .fresh_h32_strategy_transfer_audit import _belief_digest, _resident_quality_row
from .h32_affine_resident_cache_preflight import _strict_git_metadata, _validate_runtime
from .h32_atomic_response_preflight import select_one_atom_per_acting_seat
from .h32_fresh_board_panel_cache_preflight import _json_digest
from .h32_fresh_public_block_radius_audit import certificate_binding_diagnostics
from .h32_fresh_public_block_value_audit import build_public_node_blocks, information_key_public_coordinates
from .h32_fresh_union_value_audit import _certificate, _memory_snapshot, _positive_value, _safe_ratio
from .h32_warm_search_acceptance_audit import _average_policy_from_state, _local_blocker_likelihoods, _policy_distance
from .leaf_adjoint_checkpoint_ladder_audit import _build_case
from .open_mode_factor_tt import OpenModeFactorTTWorkspace
from .real_policy import policy_digest
from .reporting import environment_metadata
from .resident_leaf_adjoint_cfr import ResidentLeafAdjointPublicTreeCFR
from .river import parse_cards
from .shared_resident_response_context import SharedResidentAutomatonBundle, bind_resident_response_context


_ROOT = Path(__file__).parents[2]
_CONFIG = _ROOT / "experiments/configs/h32-fresh-regret-vertex-opportunity-v1.json"
_OUTPUT = _ROOT / "experiments/results/h32-fresh-regret-vertex-opportunity-v1.json"
_SOURCE = _ROOT / "experiments/results/h32-fresh-panel-source-blueprints-v1.json"
_PARENT_RESULT = _ROOT / "experiments/results/h32-fresh-public-block-radius-v1.json"
_PARENT_ADR = _ROOT / "docs/decisions/ADR-0176-public-block-radii-exist-but-certified-value-remains-microscopic.md"
_REQUIREMENTS = _ROOT / "experiments/requirements/leaf-adjoint-gpu-screen-v1.txt"
_IMPLEMENTATION = Path(__file__)
_TEST = _ROOT / "tests/test_h32_fresh_regret_vertex_opportunity_audit.py"

_PATHS = {
    "expected_source_result_sha256": _SOURCE,
    "expected_parent_result_sha256": _PARENT_RESULT,
    "expected_parent_decision_sha256": _PARENT_ADR,
    "expected_requirements_sha256": _REQUIREMENTS,
    "expected_target_builder_sha256": _ROOT / "src/pontius/h32_warm_search_acceptance_audit.py",
    "expected_public_block_builder_sha256": _ROOT / "src/pontius/h32_fresh_public_block_value_audit.py",
    "expected_radius_diagnostics_sha256": _ROOT / "src/pontius/h32_fresh_public_block_radius_audit.py",
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
        "target": "panel_1/balanced/local_blocker_seat1_x2", "board_id": "panel_1",
        "board": ["5c", "8c", "8d", "Jc", "As"], "range_family": "balanced",
        "target_shift": "local_blocker_seat1_x2",
        "source_belief_sha256": "376e8a44217f35dfdf305035fe8f3bbfb52b010e14050bedaf55da78c9e72885",
        "target_belief_sha256": "574a600b803f7980b70c8c1b9334aba2def3fea283b4aa8536c7c3df03bd6d26",
        "target_descriptor_sha256": "6109b0afb8548629870f6484d5f1050468aad320c0e1c92e8506d841c9dc7f7b",
    },
    {
        "target": "panel_1/blocker_heavy/local_blocker_seat1_x2", "board_id": "panel_1",
        "board": ["5c", "8c", "8d", "Jc", "As"], "range_family": "blocker_heavy",
        "target_shift": "local_blocker_seat1_x2",
        "source_belief_sha256": "aa3a5a8abe8dc72fe436134d4b619239a87b002134cdad88a908d833318b5067",
        "target_belief_sha256": "17296f1cb926397d8374ea0fba0a4d49197b913f3005df851cfdea89590cb640",
        "target_descriptor_sha256": "d8ed3c8858646a30fef0ae26c94f50c8193a28eab00697dda54c6f1177763891",
    },
    {
        "target": "panel_2/balanced/local_blocker_seat1_x2", "board_id": "panel_2",
        "board": ["2c", "3s", "5d", "Js", "Qc"], "range_family": "balanced",
        "target_shift": "local_blocker_seat1_x2",
        "source_belief_sha256": "0662b2cf2436cbc6dcc5669fe75a2c15f03e652fb40a6903703a10dd14cfa289",
        "target_belief_sha256": "862f5df07d822a36dd378a9ea537dea5c48e882157f7b8c14040e56400326a17",
        "target_descriptor_sha256": "a3bdedd913cc37208fd1b18c190333c289da906d11beec6103359fa0ab2b48bc",
    },
    {
        "target": "panel_2/blocker_heavy/local_blocker_seat1_x2", "board_id": "panel_2",
        "board": ["2c", "3s", "5d", "Js", "Qc"], "range_family": "blocker_heavy",
        "target_shift": "local_blocker_seat1_x2",
        "source_belief_sha256": "59f955c6b89bdc56670dc16b19795451404fe80ff37f519bac007975d85200f1",
        "target_belief_sha256": "b0ab91f3eeb388ae0e5854dd57c3dded75ae0a64cc4f6baa7def53950f981c26",
        "target_descriptor_sha256": "0e04ef8a7fdad7fd67b648753a436738c007a58de594f12e2242a7070201b577",
    },
    {
        "target": "panel_3/balanced/local_blocker_seat1_x2", "board_id": "panel_3",
        "board": ["4h", "7h", "9s", "Jd", "Kc"], "range_family": "balanced",
        "target_shift": "local_blocker_seat1_x2",
        "source_belief_sha256": "cadd9449259f56de43ae4d710c2e3fd6ae4733e7b7c8323836b87578a3cc9a71",
        "target_belief_sha256": "d8ad6fc5c9f4bd9e486fb12aa83f3e86b1eaace694a8e0f21e6951adc32c83f8",
        "target_descriptor_sha256": "e621bfd7c0d23d598f8b60c27fd69d913798859a71f10d422799c8841f3e441c",
    },
    {
        "target": "panel_3/blocker_heavy/local_blocker_seat1_x2", "board_id": "panel_3",
        "board": ["4h", "7h", "9s", "Jd", "Kc"], "range_family": "blocker_heavy",
        "target_shift": "local_blocker_seat1_x2",
        "source_belief_sha256": "74ce0c18ac82e9ebb799be851f140c7011ad75671a3409f94c7db1db3187278e",
        "target_belief_sha256": "647c67acf4ebe3e1dab908dc614c1f23ea3dc59a2ab608eaebcd9a4685b8ca39",
        "target_descriptor_sha256": "de67f2fbba92ea16ad5ede876b9c6451affb06d103e5f1f6e0b30c4df8b56eeb",
    },
]

_DIRECTION_FAMILIES = ["soft_dcfr", "regret_vertex"]


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required regret-vertex input is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_h32_fresh_regret_vertex_opportunity_config(config: dict[str, Any]) -> dict[str, Any]:
    """Validate ADR-0177's complete pre-label paired-opportunity contract."""

    fields = {
        "evidence_stage", *_PATHS, "seed", "targets", "target_construction",
        "local_blocker_target_seat", "pot", "stack", "bet_size", "players",
        "hands_per_player", "axis_seed", "mixture_components", "split_index",
        "query_chunk_records", "solver_variant", "warm_regret_mass_payoff_fraction",
        "search_steps_per_target", "block_anchor_selection", "block_membership",
        "acting_seats", "direction_families", "regret_delta_recovery",
        "regret_vertex_rule", "opportunity_proxy", "scale_grid", "numerical_floor",
        "radius_search", "objective_search", "convex_scope", "certificate_anchor_rule",
        "seat_order", "acceptance_guard_normalized", "maximum_feature_width_per_batch",
        "measurement_context", "street_budget_ms", "emission_reserve_ms", "emitted_policy",
        "maximum_warm_start_probability_error", "maximum_warm_start_mean_total_variation",
        "required_numpy_version", "required_scipy_version", "required_cupy_version",
        "required_cuda_runtime_version", "minimum_cuda_driver_version",
        "required_compute_capability", "cuda_dll_environment_variable", "gates",
    }
    if set(config) != fields:
        raise ValueError("fresh regret-vertex fields differ from ADR-0177")
    frozen = {
        "evidence_stage": "preregistered_after_adr0176_before_any_seat1_target_policy_step_or_quality_measurement",
        "seed": 20260821,
        "targets": _FROZEN_TARGETS,
        "target_construction": "double_label_free_maximum_overlap_then_strength_then_smallest_canonical_hand_at_seat1",
        "local_blocker_target_seat": 1,
        "pot": 12.0, "stack": 30.0, "bet_size": 3.0, "players": 6,
        "hands_per_player": 32, "axis_seed": 20260819, "mixture_components": 3,
        "split_index": 3, "query_chunk_records": 256, "solver_variant": "dcfr",
        "warm_regret_mass_payoff_fraction": 0.1, "search_steps_per_target": 1,
        "block_anchor_selection": "lexicographically_first_changed_information_set_per_acting_seat",
        "block_membership": "all_changed_information_sets_with_anchor_acting_seat_and_exact_public_history",
        "acting_seats": [0, 1, 2, 3, 4, 5],
        "direction_families": _DIRECTION_FAMILIES,
        "regret_delta_recovery": "iteration_one_dcfr_postdiscount_times_two_minus_warm_mass_times_blueprint",
        "regret_vertex_rule": "per_information_set_pure_action_with_largest_recovered_instantaneous_regret_first_action_tie_break",
        "opportunity_proxy": "block_sum_positive_best_action_regret_and_regret_span_before_any_certificate_label",
        "scale_grid": "shared_geometric_halving_inclusive_while_scale_at_least_numerical_floor",
        "numerical_floor": 1e-10,
        "radius_search": "exact_endpoint_then_discrete_bisection_for_first_complete_scale",
        "objective_search": "exact_binary_unimodal_minimum_nashconv_over_complete_scale_suffix",
        "convex_scope": "one_common_scale_one_acting_seat_one_exact_public_node_no_union",
        "certificate_anchor_rule": "immutable_source_average64_independent_one_shot_for_every_queried_scale_never_reanchors",
        "seat_order": [0, 1, 2, 3, 4, 5],
        "acceptance_guard_normalized": 1e-10,
        "maximum_feature_width_per_batch": 384,
        "measurement_context": "off_clock_generator_identification_not_a_live_scheduler",
        "street_budget_ms": 15000.0, "emission_reserve_ms": 1000.0,
        "emitted_policy": "immutable_blueprint_research_only",
        "maximum_warm_start_probability_error": 1e-12,
        "maximum_warm_start_mean_total_variation": 1e-13,
        "required_numpy_version": "2.5.2", "required_scipy_version": "1.18.0",
        "required_cupy_version": "14.2.0", "required_cuda_runtime_version": 13020,
        "minimum_cuda_driver_version": 13000, "required_compute_capability": "120",
        "cuda_dll_environment_variable": "PONTIUS_CUDA_DLL_DIRECTORY",
    }
    if any(config[key] != value for key, value in frozen.items()):
        raise ValueError("fresh regret-vertex workload differs from ADR-0177")
    for field, path in _PATHS.items():
        if config[field] != _sha256(path):
            raise ValueError(f"fresh regret-vertex source mismatch: {field}")
    gates = {
        "expected_target_rows": 6, "expected_search_steps": 6,
        "expected_public_blocks": 36, "expected_direction_rows": 72,
        "expected_blueprint_quality_labels": 6, "maximum_queries_per_direction": 16,
        "maximum_total_certificate_queries": 1152, "maximum_search_step_ms": 60000.0,
        "maximum_certificate_ms": 60000.0, "maximum_gpu_pool_bytes": 12000000000,
        "minimum_physical_free_bytes": 1000000000, "maximum_total_audit_seconds": 2400.0,
        "require_clean_git_state": True, "require_parent_passed": True,
        "require_source_checkpoint_identity": True, "require_target_identity": True,
        "require_blueprint_identity": True, "require_numerical_warm_start_identity": True,
        "require_nonempty_coherent_blocks": True, "require_direction_family_identity": True,
        "require_convex_scope": True, "require_search_invariants": True,
        "require_immutable_anchor": True, "require_independent_certificates": True,
        "require_regret_recovery_finite": True, "require_blueprint_emission": True,
        "require_finite": True, "require_strategy_population_claim_null": True,
    }
    if config["gates"] != gates:
        raise ValueError("fresh regret-vertex gates differ from ADR-0177")
    return {
        **config, "targets": tuple(dict(row) for row in config["targets"]),
        "acting_seats": tuple(config["acting_seats"]),
        "direction_families": tuple(config["direction_families"]),
        "seat_order": tuple(config["seat_order"]), "gates": dict(gates),
    }


def build_fresh_seat1_target(source: Any, *, board: tuple[int, ...], target_seat: int) -> tuple[Any, dict[str, Any]]:
    """Construct one frozen positive seat-1 belief shift without policy labels."""

    if target_seat != 1:
        raise ValueError("fresh regret-vertex target seat differs from ADR-0177")
    likelihoods, detail = _local_blocker_likelihoods(source, board=board, target_seat=target_seat)
    target = source
    for seat, likelihood in enumerate(likelihoods):
        target = target.with_likelihood(seat, likelihood)
    values = np.concatenate(likelihoods)
    return target, {
        "shift": "local_blocker_seat1_x2",
        "likelihood_minimum": float(np.min(values)), "likelihood_maximum": float(np.max(values)),
        "likelihood_mean": float(np.mean(values)), "positive_likelihoods": bool(np.all(values > 0.0)),
        "hand_axes_identity": target.hands_by_player == source.hands_by_player, **detail,
    }


def recover_iteration_one_dcfr_regret_deltas(
    blueprint: Mapping[str, Mapping[Any, float]],
    postdiscount_regrets: Mapping[str, Mapping[Any, float]],
    *, warm_regret_mass: float,
) -> dict[str, dict[Any, float]]:
    """Invert DCFR iteration-one's common one-half discount."""

    if not math.isfinite(warm_regret_mass) or warm_regret_mass <= 0.0:
        raise ValueError("warm regret mass must be positive and finite")
    if set(blueprint) != set(postdiscount_regrets):
        raise ValueError("regret and blueprint schemas differ")
    result = {}
    for key in sorted(blueprint):
        if set(blueprint[key]) != set(postdiscount_regrets[key]):
            raise ValueError("regret and blueprint action schemas differ")
        result[key] = {
            action: 2.0 * float(postdiscount_regrets[key][action]) - warm_regret_mass * float(probability)
            for action, probability in blueprint[key].items()
        }
    if any(not math.isfinite(value) for row in result.values() for value in row.values()):
        raise ValueError("recovered regret delta is not finite")
    return result


def build_regret_vertex_candidate(
    blueprint: Mapping[str, Mapping[Any, float]],
    regret_deltas: Mapping[str, Mapping[Any, float]],
    information_keys: Sequence[str],
) -> dict[str, dict[Any, float]]:
    """Move each selected infoset to its first maximum-regret pure action."""

    selected = tuple(information_keys)
    if len(selected) != len(set(selected)) or set(selected) - set(blueprint):
        raise ValueError("regret-vertex information-set selection is invalid")
    result = {key: {action: float(value) for action, value in row.items()} for key, row in blueprint.items()}
    for key in selected:
        actions = tuple(blueprint[key])
        if not actions or set(actions) != set(regret_deltas[key]):
            raise ValueError("regret-vertex action schema differs")
        winner = max(actions, key=lambda action: float(regret_deltas[key][action]))
        result[key] = {action: float(action == winner) for action in actions}
    return dict(sorted(result.items()))


def block_regret_opportunity_proxy(
    blueprint: Mapping[str, Mapping[Any, float]],
    regret_deltas: Mapping[str, Mapping[Any, float]],
    information_keys: Sequence[str],
    *, payoff_span: float,
) -> dict[str, Any]:
    """Summarize the causal one-step regret signal before certificate labels."""

    if not math.isfinite(payoff_span) or payoff_span <= 0.0:
        raise ValueError("opportunity proxy payoff span must be positive")
    best_regrets = []
    spans = []
    chosen: dict[str, int] = {}
    for key in information_keys:
        actions = tuple(blueprint[key])
        values = tuple(float(regret_deltas[key][action]) for action in actions)
        best_index = max(range(len(actions)), key=lambda index: values[index])
        chosen[str(actions[best_index])] = chosen.get(str(actions[best_index]), 0) + 1
        best_regrets.append(max(0.0, values[best_index]))
        spans.append(max(values) - min(values))
    positive_mass = math.fsum(best_regrets)
    span_mass = math.fsum(spans)
    return {
        "information_set_count": len(tuple(information_keys)),
        "positive_best_action_regret_mass": positive_mass,
        "normalized_positive_best_action_regret_mass": positive_mass / payoff_span,
        "mean_positive_best_action_regret": positive_mass / len(best_regrets) if best_regrets else 0.0,
        "maximum_positive_best_action_regret": max(best_regrets, default=0.0),
        "regret_span_mass": span_mass,
        "normalized_regret_span_mass": span_mass / payoff_span,
        "maximum_regret_span": max(spans, default=0.0),
        "vertex_action_counts": dict(sorted(chosen.items())),
    }


def exact_discrete_convex_scale_search(
    evaluate: Callable[[int], dict[str, Any]], *, scale_count: int,
) -> dict[str, Any]:
    """Find the complete suffix boundary and its discrete NashConv minimum."""

    if isinstance(scale_count, bool) or scale_count < 1:
        raise ValueError("scale count must be positive")
    cache: dict[int, dict[str, Any]] = {}
    query_order = []

    def read(index: int) -> dict[str, Any]:
        if index not in range(scale_count):
            raise ValueError("scale query is outside the frozen grid")
        if index not in cache:
            row = evaluate(index)
            if int(row["scale_index"]) != index:
                raise ValueError("scale evaluator returned the wrong index")
            cache[index] = row
            query_order.append(index)
        return cache[index]

    first = read(0)
    boundary = 0 if first["certificate"]["complete"] else None
    if boundary is None:
        floor = read(scale_count - 1)
        if floor["certificate"]["complete"]:
            low, high = 0, scale_count - 1
            while high - low > 1:
                middle = (low + high) // 2
                if read(middle)["certificate"]["complete"]:
                    high = middle
                else:
                    low = middle
            boundary = high

    best_index = None
    if boundary is not None:
        left, right = boundary, scale_count - 1
        while left < right:
            middle = (left + right) // 2
            current = read(middle)
            following = read(middle + 1)
            if not current["certificate"]["complete"] or not following["certificate"]["complete"]:
                raise ValueError("objective search left the complete suffix")
            current_nash = float(current["certificate"]["quality"]["nash_conv"])
            following_nash = float(following["certificate"]["quality"]["nash_conv"])
            if current_nash <= following_nash:
                right = middle
            else:
                left = middle + 1
        best_index = left
        read(best_index)

    return {
        "query_order": query_order,
        "queried_rows": [cache[index] for index in sorted(cache)],
        "query_count": len(cache),
        "largest_complete_scale_index": boundary,
        "best_complete_scale_index": best_index,
    }


def search_invariants(search: Mapping[str, Any], *, scale_count: int) -> bool:
    """Check endpoint, boundary, uniqueness, and best-row witness invariants."""

    rows = {int(row["scale_index"]): row for row in search["queried_rows"]}
    order = tuple(int(value) for value in search["query_order"])
    if len(rows) != len(order) or len(set(order)) != len(order) or set(rows) != set(order):
        return False
    boundary = search["largest_complete_scale_index"]
    best = search["best_complete_scale_index"]
    if boundary is None:
        return best is None and 0 in rows and scale_count - 1 in rows and not rows[scale_count - 1]["certificate"]["complete"]
    boundary = int(boundary)
    if boundary not in rows or not rows[boundary]["certificate"]["complete"]:
        return False
    if boundary > 0 and (boundary - 1 not in rows or rows[boundary - 1]["certificate"]["complete"]):
        return False
    return best is not None and int(best) in rows and rows[int(best)]["certificate"]["complete"]


def direction_has_convex_scope(direction: Mapping[str, Any]) -> bool:
    """Require exactly one acting seat and one exact public history."""

    expected_seat = int(direction["acting_seat"])
    coordinates = {
        information_key_public_coordinates(key)
        for key in direction["information_keys"]
    }
    return bool(coordinates) and coordinates == {
        (expected_seat, str(direction["public_history"]))
    }


def _ranks(values: Sequence[float]) -> list[float]:
    order = sorted(range(len(values)), key=lambda index: values[index])
    ranks = [0.0] * len(values)
    start = 0
    while start < len(order):
        end = start + 1
        while end < len(order) and values[order[end]] == values[order[start]]:
            end += 1
        rank = 0.5 * (start + end - 1) + 1.0
        for position in range(start, end):
            ranks[order[position]] = rank
        start = end
    return ranks


def spearman_rank_correlation(first: Sequence[float], second: Sequence[float]) -> float | None:
    """Return a deterministic average-rank Spearman diagnostic."""

    if len(first) != len(second) or len(first) < 2:
        return None
    left, right = _ranks(tuple(float(value) for value in first)), _ranks(tuple(float(value) for value in second))
    left_mean, right_mean = math.fsum(left) / len(left), math.fsum(right) / len(right)
    covariance = math.fsum((x - left_mean) * (y - right_mean) for x, y in zip(left, right, strict=True))
    left_square = math.fsum((x - left_mean) ** 2 for x in left)
    right_square = math.fsum((y - right_mean) ** 2 for y in right)
    return None if left_square <= 0.0 or right_square <= 0.0 else covariance / math.sqrt(left_square * right_square)


def _run_target(parsed: dict[str, Any], source_parent: dict[str, Any], target_spec: Mapping[str, Any], cp: Any) -> dict[str, Any]:
    board = parse_cards(*target_spec["board"])
    family = str(target_spec["range_family"])
    source, layout, sparse, retained = _build_case(parsed=parsed, board=board, hand_count=parsed["hands_per_player"], family=family)
    source_workspace, _, automata = retained
    source_digest = _belief_digest(source)
    parent_row = next(row for row in source_parent["source_rows"] if row["source"] == f"{target_spec['board_id']}/{family}")
    state = parent_row["final_checkpoint"]
    source_checkpoint_identity = axis_cfr_checkpoint_digest(state) == state["state_sha256"] and source_digest == target_spec["source_belief_sha256"] and source_digest == parent_row["source_belief_sha256"]
    blueprint = _average_policy_from_state(state)
    blueprint_digest = policy_digest(blueprint)
    blueprint_identity = blueprint_digest == state["average_policy_sha256"]
    belief, descriptor = build_fresh_seat1_target(source, board=board, target_seat=parsed["local_blocker_target_seat"])
    target_digest, descriptor_digest = _belief_digest(belief), _json_digest(descriptor)
    target_identity = target_digest == target_spec["target_belief_sha256"] and descriptor_digest == target_spec["target_descriptor_sha256"] and belief.hands_by_player == source.hands_by_player

    base = FactorTTBeliefWorkspace.compile(source_workspace.topology.base, belief, query_chunk_records=parsed["query_chunk_records"])
    workspace = OpenModeFactorTTWorkspace.compile(source_workspace.topology, base)
    gpu = CuPyBidirectionalIncidence.compile(sparse)
    shared = SharedResidentAutomatonBundle.compile(workspace, automata)
    context = bind_resident_response_context(shared, layout=layout, workspace=workspace, sparse=sparse, source_policy=blueprint, hands_by_player=belief.hands_by_player, cupy_sparse=gpu, maximum_feature_width_per_batch=parsed["maximum_feature_width_per_batch"])
    blueprint_quality, _ = _resident_quality_row(
        layout=layout, workspace=workspace, sparse=sparse, automata=automata, policy=blueprint,
        label="blueprint_average64", hands_by_player=belief.hands_by_player,
        belief_cache=context.belief_cache, automaton_caches=shared.automaton_caches,
        gpu=gpu, payoff_span=parsed["stack"], maximum_feature_width_per_batch=parsed["maximum_feature_width_per_batch"],
    )
    solver = ResidentLeafAdjointPublicTreeCFR(
        layout, workspace, sparse, automata, parsed["solver_variant"], belief_cache=context.belief_cache,
        automaton_caches=shared.automaton_caches, cupy_sparse=gpu,
        maximum_feature_width_per_batch=parsed["maximum_feature_width_per_batch"], hands_by_player=belief.hands_by_player,
    )
    warm_mass = parsed["warm_regret_mass_payoff_fraction"] * float(layout.game.payoff_span)
    solver.warm_start(blueprint, warm_mass)
    warm_start_distance = _policy_distance(blueprint, solver.current_strategy())
    release_cupy_memory_pool()
    memory_rows = [_memory_snapshot(cp)]
    search_started = time.perf_counter()
    solver.step()
    search_ms = (time.perf_counter() - search_started) * 1000.0
    soft_candidate = solver.current_strategy()
    regret_deltas = recover_iteration_one_dcfr_regret_deltas(blueprint, solver.regret_table(), warm_regret_mass=warm_mass)
    memory_rows.append(_memory_snapshot(cp))
    anchors = select_one_atom_per_acting_seat(layout, belief.hands_by_player, blueprint, soft_candidate)
    blocks = build_public_node_blocks(blueprint, soft_candidate, anchors)
    scales = geometric_halving_scales(numerical_floor=parsed["numerical_floor"])
    raw_guard = parsed["acceptance_guard_normalized"] * parsed["stack"]
    blueprint_nash = float(blueprint_quality["nash_conv"])
    block_rows = []
    for block in blocks:
        seat = int(block["acting_seat"])
        keys = tuple(block["information_keys"])
        proxy = block_regret_opportunity_proxy(blueprint, regret_deltas, keys, payoff_span=parsed["stack"])
        vertex_candidate = build_regret_vertex_candidate(blueprint, regret_deltas, keys)
        candidates = {"soft_dcfr": soft_candidate, "regret_vertex": vertex_candidate}
        family_rows = []
        for direction_family in parsed["direction_families"]:
            direction_candidate = candidates[direction_family]
            query_started = time.perf_counter()

            def evaluate(scale_index: int) -> dict[str, Any]:
                construction_started = time.perf_counter()
                policy = interpolate_policy_atoms(blueprint, direction_candidate, keys, scale=scales[scale_index])
                construction_ms = (time.perf_counter() - construction_started) * 1000.0
                certificate = _certificate(
                    candidate_id=f"seat{seat}_{direction_family}@scale_{scale_index:02d}", policy=policy,
                    layout=layout, belief=belief, context=context, shared=shared, gpu=gpu,
                    blueprint_quality=blueprint_quality, parsed=parsed,
                )
                quality = certificate["quality"]
                value = 0.0 if quality is None else _positive_value(blueprint_nash, float(quality["nash_conv"]))
                binding = certificate_binding_diagnostics(certificate, blueprint_quality, raw_guard)
                memory = _memory_snapshot(cp)
                memory_rows.append(memory)
                return {
                    "scale_index": scale_index, "scale": scales[scale_index], "policy_sha256": policy_digest(policy),
                    "construction_ms": construction_ms,
                    "changed_information_set_count": len(atomic_policy_manifest(blueprint, policy)),
                    "certificate_anchor_policy_sha256": blueprint_digest,
                    "certificate_anchor_nash_conv": blueprint_nash, "independent_from_blueprint": True,
                    "positive_certified_value": value,
                    "normalized_objective_reduction": None if quality is None else (blueprint_nash - float(quality["nash_conv"])) / parsed["stack"],
                    "value_per_certificate_second": _safe_ratio(value, float(certificate["wall_ms"]) / 1000.0),
                    **binding, "certificate": certificate, "memory_after": memory,
                }

            search = exact_discrete_convex_scale_search(evaluate, scale_count=len(scales))
            best_index = search["best_complete_scale_index"]
            best_row = None if best_index is None else next(row for row in search["queried_rows"] if row["scale_index"] == best_index)
            boundary_index = search["largest_complete_scale_index"]
            boundary_row = None if boundary_index is None else next(row for row in search["queried_rows"] if row["scale_index"] == boundary_index)
            family_rows.append({
                "direction_family": direction_family, "acting_seat": seat,
                "public_history": block["public_history"], "information_keys": list(keys),
                "information_set_count": len(keys), "direction_policy_sha256": policy_digest(direction_candidate),
                "search_wall_ms": (time.perf_counter() - query_started) * 1000.0,
                "search": search,
                "largest_complete_scale": None if boundary_row is None else boundary_row["scale"],
                "best_complete_scale": None if best_row is None else best_row["scale"],
                "best_positive_certified_value": 0.0 if best_row is None else best_row["positive_certified_value"],
                "best_value_per_certificate_second": None if best_row is None else best_row["value_per_certificate_second"],
                "best_certificate_wall_ms": None if best_row is None else best_row["certificate"]["wall_ms"],
                "hypothetical_single_certificate_ledger_ms": None if best_row is None else search_ms + best_row["construction_ms"] + best_row["certificate"]["wall_ms"] + parsed["emission_reserve_ms"],
            })
        soft, vertex = family_rows
        if soft["direction_family"] != "soft_dcfr" or vertex["direction_family"] != "regret_vertex":
            raise AssertionError("direction family order changed")
        soft_value, vertex_value = float(soft["best_positive_certified_value"]), float(vertex["best_positive_certified_value"])
        oracle_value = max(soft_value, vertex_value)
        winner = "soft_dcfr" if soft_value >= vertex_value else "regret_vertex"
        block_rows.append({
            **block, "opportunity_proxy": proxy, "direction_rows": family_rows,
            "bounded_oracle_positive_certified_value": oracle_value,
            "bounded_oracle_winner": winner,
            "soft_dcfr_capture_fraction": None if oracle_value <= 0.0 else soft_value / oracle_value,
            "regret_vertex_minus_soft_value": vertex_value - soft_value,
            "regret_vertex_exceeds_soft_by_raw_guard": vertex_value > soft_value + raw_guard,
            "bounded_oracle_fraction_of_blueprint_nash_conv": _safe_ratio(oracle_value, blueprint_nash),
        })

    result = {
        "target": target_spec["target"], "board_id": target_spec["board_id"], "board": target_spec["board"],
        "range_family": family, "target_shift": target_spec["target_shift"],
        "source_belief_sha256": source_digest, "target_belief_sha256": target_digest,
        "target_descriptor_sha256": descriptor_digest, "target_descriptor": descriptor,
        "source_checkpoint_identity": source_checkpoint_identity, "target_identity": target_identity,
        "blueprint_identity": blueprint_identity, "warm_start_distance": warm_start_distance,
        "blueprint_quality": blueprint_quality,
        "blueprint_opportunity": {
            "nash_conv": blueprint_nash, "normalized_nash_conv": blueprint_nash / parsed["stack"],
            "maximum_deviation_gain": max(float(value) for value in blueprint_quality["deviation_gains"]),
            "maximum_deviation_gain_share": max(float(value) for value in blueprint_quality["deviation_gains"]) / blueprint_nash if blueprint_nash > 0.0 else 0.0,
            "deviation_gain_concentration": math.fsum(float(value) ** 2 for value in blueprint_quality["deviation_gains"]) / (blueprint_nash ** 2) if blueprint_nash > 0.0 else 0.0,
        },
        "search_step_ms": search_ms, "search_step_work_wall_ms": solver.last_step_work.wall_ms,
        "soft_candidate_policy_sha256": policy_digest(soft_candidate),
        "changed_information_set_count": len(atomic_policy_manifest(blueprint, soft_candidate)),
        "regret_delta_recovery_finite": all(math.isfinite(value) for row in regret_deltas.values() for value in row.values()),
        "scale_grid": list(scales), "block_rows": block_rows,
        "emitted_candidate_id": "blueprint_average64", "emitted_policy_sha256": blueprint_digest,
        "memory_rows": memory_rows,
    }
    del solver, context, shared, gpu, workspace, base, automata, source_workspace
    del sparse, layout, belief, source
    gc.collect()
    release_cupy_memory_pool()
    return result


def run_h32_fresh_regret_vertex_opportunity_audit(config_path: Path = _CONFIG, output_path: Path = _OUTPUT) -> dict[str, Any]:
    """Execute the frozen paired generator/opportunity audit."""

    started = time.perf_counter()
    parsed = parse_h32_fresh_regret_vertex_opportunity_config(json.loads(config_path.read_text(encoding="utf-8")))
    source_parent = json.loads(_SOURCE.read_text(encoding="utf-8"))
    parent = json.loads(_PARENT_RESULT.read_text(encoding="utf-8"))
    git = _strict_git_metadata()
    cp, runtime = _validate_runtime(parsed)
    if git["dirty"]:
        raise RuntimeError("fresh regret-vertex execution requires a clean Git state")
    if not source_parent["passed"] or not parent["gates"]["passed"]:
        raise ValueError("fresh regret-vertex parent did not pass")
    targets = []
    for target_spec in parsed["targets"]:
        print(f"fresh regret-vertex audit: {target_spec['target']}", flush=True)
        targets.append(_run_target(parsed, source_parent, target_spec, cp))

    blocks = [block for target in targets for block in target["block_rows"]]
    directions = [direction for block in blocks for direction in block["direction_rows"]]
    certificate_rows = [row for direction in directions for row in direction["search"]["queried_rows"]]
    memory_rows = [row for target in targets for row in target["memory_rows"]]
    total_seconds = time.perf_counter() - started
    gates_config = parsed["gates"]
    scales = geometric_halving_scales(numerical_floor=parsed["numerical_floor"])
    proxy_values = [float(block["opportunity_proxy"]["normalized_positive_best_action_regret_mass"]) for block in blocks]
    oracle_values = [float(block["bounded_oracle_positive_certified_value"]) for block in blocks]
    soft_values = [float(block["direction_rows"][0]["best_positive_certified_value"]) for block in blocks]
    vertex_uplifts = [float(block["regret_vertex_minus_soft_value"]) for block in blocks]
    finite_values = [
        value for target in targets for value in (
            target["blueprint_quality"]["nash_conv"], target["search_step_ms"],
            target["warm_start_distance"]["maximum_probability_error"], target["warm_start_distance"]["mean_total_variation"],
        )
    ] + [value for row in certificate_rows for value in (row["scale"], row["construction_ms"], row["positive_certified_value"], row["certificate"]["wall_ms"], row["certificate"]["partial_nash_conv"])]
    gates = {
        "clean_git": (not git["dirty"]) == gates_config["require_clean_git_state"],
        "parent_passed": (source_parent["passed"] and parent["gates"]["passed"]) == gates_config["require_parent_passed"],
        "target_rows": len(targets) == gates_config["expected_target_rows"],
        "search_steps": len(targets) == gates_config["expected_search_steps"],
        "public_blocks": len(blocks) == gates_config["expected_public_blocks"],
        "direction_rows": len(directions) == gates_config["expected_direction_rows"],
        "blueprint_quality_labels": len(targets) == gates_config["expected_blueprint_quality_labels"],
        "certificate_query_bound": len(certificate_rows) <= gates_config["maximum_total_certificate_queries"] and all(direction["search"]["query_count"] <= gates_config["maximum_queries_per_direction"] for direction in directions),
        "source_checkpoint_identity": all(target["source_checkpoint_identity"] for target in targets) == gates_config["require_source_checkpoint_identity"],
        "target_identity": all(target["target_identity"] for target in targets) == gates_config["require_target_identity"],
        "blueprint_identity": all(target["blueprint_identity"] for target in targets) == gates_config["require_blueprint_identity"],
        "numerical_warm_start_identity": all(target["warm_start_distance"]["maximum_probability_error"] <= parsed["maximum_warm_start_probability_error"] and target["warm_start_distance"]["mean_total_variation"] <= parsed["maximum_warm_start_mean_total_variation"] for target in targets) == gates_config["require_numerical_warm_start_identity"],
        "nonempty_coherent_blocks": all(block["information_set_count"] > 0 and all(information_key_public_coordinates(key) == (block["acting_seat"], block["public_history"]) for key in block["information_keys"]) for block in blocks) == gates_config["require_nonempty_coherent_blocks"],
        "direction_family_identity": all(tuple(row["direction_family"] for row in block["direction_rows"]) == parsed["direction_families"] for block in blocks) == gates_config["require_direction_family_identity"],
        "convex_scope": all(direction_has_convex_scope(row) for row in directions) == gates_config["require_convex_scope"],
        "search_invariants": all(search_invariants(direction["search"], scale_count=len(scales)) for direction in directions) == gates_config["require_search_invariants"],
        "immutable_anchor": all(row["certificate_anchor_policy_sha256"] == target["blueprint_quality"]["policy_sha256"] and row["certificate_anchor_nash_conv"] == target["blueprint_quality"]["nash_conv"] for target in targets for block in target["block_rows"] for direction in block["direction_rows"] for row in direction["search"]["queried_rows"]) == gates_config["require_immutable_anchor"],
        "independent_certificates": all(row["independent_from_blueprint"] for row in certificate_rows) == gates_config["require_independent_certificates"],
        "regret_recovery_finite": all(target["regret_delta_recovery_finite"] for target in targets) == gates_config["require_regret_recovery_finite"],
        "blueprint_emission": all(target["emitted_candidate_id"] == "blueprint_average64" and target["emitted_policy_sha256"] == target["blueprint_quality"]["policy_sha256"] for target in targets) == gates_config["require_blueprint_emission"],
        "search_step_ms": all(target["search_step_ms"] <= gates_config["maximum_search_step_ms"] for target in targets),
        "certificate_ms": all(row["certificate"]["wall_ms"] <= gates_config["maximum_certificate_ms"] for row in certificate_rows),
        "memory": max(row["gpu_pool_total_bytes"] for row in memory_rows) <= gates_config["maximum_gpu_pool_bytes"] and min(row["gpu_free_bytes"] for row in memory_rows) >= gates_config["minimum_physical_free_bytes"],
        "finite": all(math.isfinite(float(value)) for value in finite_values) == gates_config["require_finite"],
        "strategy_population_claim_null": True == gates_config["require_strategy_population_claim_null"],
        "total_audit_seconds": total_seconds <= gates_config["maximum_total_audit_seconds"],
    }
    gates["passed"] = all(gates.values())
    result = {
        "schema_version": 1, "status": "frozen_h32_fresh_regret_vertex_opportunity_audit_executed",
        "methodology": {
            "preregistered": True, "fresh_target_quality_labels": True,
            "measurement_context": "off_clock_generator_identification", "bounded_oracle_is_global_oracle": False,
            "generator_weakness_identification_is_one_sided": True, "target_population_claim": None,
            "deployment_authorized": False, "emitted_policy": "immutable_blueprint", "scale_labels_composable": False,
        },
        "config_sha256": _sha256(config_path), "implementation_sha256": _sha256(_IMPLEMENTATION),
        "environment": {**environment_metadata(), **runtime, "git": git}, "target_rows": targets,
        "aggregate": {
            "targets": len(targets), "blocks": len(blocks), "directions": len(directions),
            "certificate_queries": len(certificate_rows),
            "directions_with_complete_scale": sum(direction["search"]["best_complete_scale_index"] is not None for direction in directions),
            "regret_vertex_oracle_wins": sum(block["bounded_oracle_winner"] == "regret_vertex" for block in blocks),
            "regret_vertex_guard_material_wins": sum(block["regret_vertex_exceeds_soft_by_raw_guard"] for block in blocks),
            "sum_soft_positive_certified_value": math.fsum(soft_values),
            "sum_bounded_oracle_positive_certified_value": math.fsum(oracle_values),
            "aggregate_soft_capture_fraction": _safe_ratio(math.fsum(soft_values), math.fsum(oracle_values)),
            "maximum_bounded_oracle_fraction_of_blueprint_nash_conv": max((float(block["bounded_oracle_fraction_of_blueprint_nash_conv"] or 0.0) for block in blocks), default=0.0),
            "proxy_spearman_with_bounded_oracle_value": spearman_rank_correlation(proxy_values, oracle_values),
            "proxy_spearman_with_soft_value": spearman_rank_correlation(proxy_values, soft_values),
            "proxy_spearman_with_vertex_uplift": spearman_rank_correlation(proxy_values, vertex_uplifts),
            "maximum_gpu_pool_bytes": max(row["gpu_pool_total_bytes"] for row in memory_rows),
            "minimum_gpu_free_bytes": min(row["gpu_free_bytes"] for row in memory_rows),
        },
        "gates": gates, "total_audit_seconds": total_seconds,
        "decision": "accept_prospective_generator_identification_measurement" if gates["passed"] else "reject_fresh_regret_vertex_audit",
        "strategy_population_claim": None,
        "limitations": [
            "Six constructed target beliefs and thirty-six blocks are not a population.",
            "The two-direction bounded oracle is a lower bound, not global attainable value.",
            "A regret-vertex win identifies a weakness of the soft generator within this library; a non-win cannot prove opportunity exhaustion.",
            "Adaptive scale search is off-clock and no observed policy is emitted or reused compositionally.",
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
    result = run_h32_fresh_regret_vertex_opportunity_audit(args.config, args.output)
    print(json.dumps({"output": str(args.output), "passed": result["gates"]["passed"], "aggregate": result["aggregate"]}, indent=2))
    if not result["gates"]["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
