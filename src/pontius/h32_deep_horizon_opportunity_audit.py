"""Frozen h32 depth ladder over exact single-public-node certificates."""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import math
from pathlib import Path
import time
from typing import Any, Mapping, Sequence

from .axis_cfr_checkpoint import axis_cfr_checkpoint_digest
from .cupy_sparse_incidence import CuPyBidirectionalIncidence, release_cupy_memory_pool
from .delta_certificate_contract import atomic_policy_manifest, geometric_halving_scales, interpolate_policy_atoms
from .factor_tt_contraction import FactorTTBeliefWorkspace
from .fresh_h32_strategy_transfer_audit import _belief_digest, _resident_quality_row
from .h32_affine_resident_cache_preflight import _strict_git_metadata, _validate_runtime
from .h32_fresh_board_panel_cache_preflight import _json_digest
from .h32_fresh_public_block_radius_audit import certificate_binding_diagnostics
from .h32_fresh_public_block_value_audit import build_public_node_blocks, information_key_public_coordinates
from .h32_fresh_regret_vertex_opportunity_audit import (
    build_fresh_seat1_target,
    direction_has_convex_scope,
    exact_discrete_convex_scale_search,
    search_invariants,
)
from .h32_fresh_union_value_audit import _certificate, _memory_snapshot, _positive_value, _safe_ratio
from .h32_resident_cfr_audit import _step_row
from .h32_warm_search_acceptance_audit import _average_policy_from_state, _policy_distance
from .leaf_adjoint_checkpoint_ladder_audit import _build_case
from .open_mode_factor_tt import OpenModeFactorTTWorkspace
from .real_policy import mean_policy_total_variation, policy_digest
from .reporting import environment_metadata
from .resident_leaf_adjoint_cfr import ResidentLeafAdjointPublicTreeCFR
from .river import parse_cards
from .shared_resident_response_context import SharedResidentAutomatonBundle, bind_resident_response_context


_ROOT = Path(__file__).parents[2]
_CONFIG = _ROOT / "experiments/configs/h32-deep-horizon-opportunity-v1.json"
_OUTPUT = _ROOT / "experiments/results/h32-deep-horizon-opportunity-v1.json"
_SOURCE = _ROOT / "experiments/results/h32-fresh-panel-source-blueprints-v1.json"
_PARENT_RESULT = _ROOT / "experiments/results/h32-fresh-regret-vertex-opportunity-v1.json"
_PARENT_ADR = _ROOT / "docs/decisions/ADR-0178-regret-vertices-expose-soft-generator-weakness-but-not-a-live-selector.md"
_REQUIREMENTS = _ROOT / "experiments/requirements/leaf-adjoint-gpu-screen-v1.txt"
_IMPLEMENTATION = Path(__file__)
_TEST = _ROOT / "tests/test_h32_deep_horizon_opportunity_audit.py"

_PATHS = {
    "expected_source_result_sha256": _SOURCE,
    "expected_parent_result_sha256": _PARENT_RESULT,
    "expected_parent_decision_sha256": _PARENT_ADR,
    "expected_requirements_sha256": _REQUIREMENTS,
    "expected_target_builder_sha256": _ROOT / "src/pontius/h32_fresh_regret_vertex_opportunity_audit.py",
    "expected_public_block_builder_sha256": _ROOT / "src/pontius/h32_fresh_public_block_value_audit.py",
    "expected_search_control_sha256": _ROOT / "src/pontius/h32_fresh_regret_vertex_opportunity_audit.py",
    "expected_union_verifier_sha256": _ROOT / "src/pontius/h32_fresh_union_value_audit.py",
    "expected_shared_context_sha256": _ROOT / "src/pontius/shared_resident_response_context.py",
    "expected_incremental_verifier_sha256": _ROOT / "src/pontius/incremental_leaf_adjoint_response.py",
    "expected_resident_cfr_sha256": _ROOT / "src/pontius/resident_leaf_adjoint_cfr.py",
    "expected_interpolation_sha256": _ROOT / "src/pontius/delta_certificate_contract.py",
    "expected_evidence_protocol_sha256": _ROOT / "src/pontius/evidence_protocol.py",
    "expected_audit_implementation_sha256": _IMPLEMENTATION,
    "expected_control_test_sha256": _TEST,
}

_TARGETS = [
    {
        "target": "panel_1/balanced/local_blocker_seat1_x2",
        "board_id": "panel_1",
        "board": ["5c", "8c", "8d", "Jc", "As"],
        "range_family": "balanced",
        "target_shift": "local_blocker_seat1_x2",
        "source_belief_sha256": "376e8a44217f35dfdf305035fe8f3bbfb52b010e14050bedaf55da78c9e72885",
        "target_belief_sha256": "574a600b803f7980b70c8c1b9334aba2def3fea283b4aa8536c7c3df03bd6d26",
        "target_descriptor_sha256": "6109b0afb8548629870f64853a960118a842b062b97809e908efbf3ca5f7d9d0d",
    },
    {
        "target": "panel_3/blocker_heavy/local_blocker_seat1_x2",
        "board_id": "panel_3",
        "board": ["4h", "7h", "9s", "Jd", "Kc"],
        "range_family": "blocker_heavy",
        "target_shift": "local_blocker_seat1_x2",
        "source_belief_sha256": "74ce0c18ac82e9ebb799be851f140c7011ad75671a3409f94c7db1db3187278e",
        "target_belief_sha256": "647c67acf4ebe3e1dab908dc614c1f23ea3dc59a2ab608eaebcd9a4685b8ca39",
        "target_descriptor_sha256": "de67f2fbba92ea16ad5ede876b9c6451affb06f0b30c4f6baa7def53950f981c26",
    },
]

_DIRECTIONS = [
    "current8", "average8", "current32", "average32",
    "current64", "average64", "purified_average64",
]


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required deep-horizon input is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_h32_deep_horizon_opportunity_config(config: dict[str, Any]) -> dict[str, Any]:
    """Validate ADR-0181's outcome-neutral depth contract."""

    fields = {
        "evidence_stage", *_PATHS, "seed", "targets", "target_selection_disclosure",
        "local_blocker_target_seat", "pot", "stack", "bet_size", "players",
        "hands_per_player", "axis_seed", "mixture_components", "split_index",
        "query_chunk_records", "solver_variant", "warm_regret_mass_payoff_fraction",
        "maximum_search_steps", "checkpoints", "endpoint_directions", "purification_rule",
        "block_source", "scale_grid", "numerical_floor", "radius_search",
        "objective_search", "convex_scope", "certificate_anchor_rule", "seat_order",
        "acceptance_guard_normalized", "maximum_feature_width_per_batch",
        "measurement_context", "material_lift_rule", "emitted_policy",
        "maximum_warm_start_probability_error", "maximum_warm_start_mean_total_variation",
        "required_numpy_version", "required_scipy_version", "required_cupy_version",
        "required_cuda_runtime_version", "minimum_cuda_driver_version",
        "required_compute_capability", "cuda_dll_environment_variable", "gates",
    }
    if set(config) != fields:
        raise ValueError("deep-horizon fields differ from ADR-0181")
    frozen = {
        "evidence_stage": "preregistered_after_adr0180_before_any_new_deep_h32_step_or_certificate_label",
        "seed": 20260821,
        "targets": _TARGETS,
        "target_selection_disclosure": "fastest_disclosed_one_step_target_within_each_range_family_panel1_balanced_and_panel3_blocker_heavy_are_on_different_boards_and_are_not_fresh_holdouts_no_strategy_label_selected_them",
        "local_blocker_target_seat": 1,
        "pot": 12.0, "stack": 30.0, "bet_size": 3.0, "players": 6,
        "hands_per_player": 32, "axis_seed": 20260819, "mixture_components": 3,
        "split_index": 3, "query_chunk_records": 256, "solver_variant": "dcfr",
        "warm_regret_mass_payoff_fraction": 0.1, "maximum_search_steps": 64,
        "checkpoints": [8, 32, 64], "endpoint_directions": _DIRECTIONS,
        "purification_rule": "at_average64_choose_first_maximum_probability_action_per_information_set_then_apply_only_the_frozen_public_block",
        "block_source": "exact_adr0178_one_step_soft_public_node_blocks_replayed_byte_for_byte",
        "scale_grid": "shared_geometric_halving_inclusive_while_scale_at_least_numerical_floor",
        "numerical_floor": 1e-10,
        "radius_search": "exact_endpoint_then_discrete_bisection_for_first_complete_scale",
        "objective_search": "exact_binary_unimodal_minimum_nashconv_over_complete_scale_suffix",
        "convex_scope": "one_common_scale_one_acting_seat_one_exact_public_node_no_union",
        "certificate_anchor_rule": "immutable_source_average64_independent_one_shot_for_every_queried_scale_never_reanchors",
        "seat_order": [0, 1, 2, 3, 4, 5], "acceptance_guard_normalized": 1e-10,
        "maximum_feature_width_per_batch": 384,
        "measurement_context": "off_clock_depth_identification_not_a_live_scheduler",
        "material_lift_rule": "best_32_or_64_current_or_average_sum_is_at_least_twice_best_8_sum_and_exceeds_it_by_one_raw_guard_per_block",
        "emitted_policy": "immutable_blueprint_research_only",
        "maximum_warm_start_probability_error": 1e-12,
        "maximum_warm_start_mean_total_variation": 1e-13,
        "required_numpy_version": "2.5.2", "required_scipy_version": "1.18.0",
        "required_cupy_version": "14.2.0", "required_cuda_runtime_version": 13020,
        "minimum_cuda_driver_version": 13000, "required_compute_capability": "120",
        "cuda_dll_environment_variable": "PONTIUS_CUDA_DLL_DIRECTORY",
    }
    if any(config[key] != value for key, value in frozen.items()):
        raise ValueError("deep-horizon workload differs from ADR-0181")
    for field, path in _PATHS.items():
        if config[field] != _sha256(path):
            raise ValueError(f"deep-horizon source mismatch: {field}")
    gates = {
        "expected_target_rows": 2, "expected_search_steps": 128,
        "expected_checkpoint_rows": 6, "expected_public_blocks": 12,
        "expected_direction_rows": 84, "expected_blueprint_quality_labels": 2,
        "maximum_queries_per_direction": 16, "maximum_total_certificate_queries": 1344,
        "maximum_search_step_ms": 60000.0, "maximum_certificate_ms": 60000.0,
        "maximum_gpu_pool_bytes": 12000000000, "minimum_physical_free_bytes": 1000000000,
        "maximum_total_audit_seconds": 4200.0, "require_clean_git_state": True,
        "require_parent_passed": True, "require_source_checkpoint_identity": True,
        "require_target_identity": True, "require_blueprint_identity": True,
        "require_numerical_warm_start_identity": True, "require_parent_block_replay": True,
        "require_checkpoint_identity": True, "require_endpoint_direction_identity": True,
        "require_convex_scope": True, "require_search_invariants": True,
        "require_immutable_anchor": True, "require_independent_certificates": True,
        "require_blueprint_emission": True, "require_finite": True,
        "require_strategy_population_claim_null": True,
    }
    if config["gates"] != gates:
        raise ValueError("deep-horizon gates differ from ADR-0181")
    return {
        **config, "targets": tuple(dict(row) for row in config["targets"]),
        "checkpoints": tuple(config["checkpoints"]),
        "endpoint_directions": tuple(config["endpoint_directions"]),
        "seat_order": tuple(config["seat_order"]), "gates": dict(gates),
    }


def purify_policy(policy: Mapping[str, Mapping[Any, float]]) -> dict[str, dict[Any, float]]:
    """Choose the first maximum-probability action at every information set."""

    result: dict[str, dict[Any, float]] = {}
    for key in sorted(policy):
        actions = tuple(policy[key])
        if not actions:
            raise ValueError("cannot purify an empty action row")
        winner = max(actions, key=lambda action: float(policy[key][action]))
        result[key] = {action: float(action == winner) for action in actions}
    return result


def material_depth_lift(shallow_value: float, deep_value: float, *, raw_guard_total: float) -> bool:
    """Apply the frozen twofold-plus-guard depth interpretation rule."""

    values = (shallow_value, deep_value, raw_guard_total)
    if any(not math.isfinite(value) or value < 0.0 for value in values):
        raise ValueError("material-lift inputs must be finite and nonnegative")
    return deep_value >= 2.0 * shallow_value and deep_value > shallow_value + raw_guard_total


def _parent_target(parent: Mapping[str, Any], target: str) -> Mapping[str, Any]:
    rows = [row for row in parent["target_rows"] if row["target"] == target]
    if len(rows) != 1:
        raise ValueError("deep-horizon parent target identity is not unique")
    return rows[0]


def _run_target(
    parsed: dict[str, Any], source_parent: dict[str, Any], parent: dict[str, Any],
    target_spec: Mapping[str, Any], cp: Any,
) -> dict[str, Any]:
    board = parse_cards(*target_spec["board"])
    family = str(target_spec["range_family"])
    source, layout, sparse, retained = _build_case(
        parsed=parsed, board=board, hand_count=parsed["hands_per_player"], family=family,
    )
    source_workspace, _, automata = retained
    source_digest = _belief_digest(source)
    source_row = next(
        row for row in source_parent["source_rows"]
        if row["source"] == f"{target_spec['board_id']}/{family}"
    )
    state = source_row["final_checkpoint"]
    source_identity = (
        axis_cfr_checkpoint_digest(state) == state["state_sha256"]
        and source_digest == target_spec["source_belief_sha256"]
        and source_digest == source_row["source_belief_sha256"]
    )
    blueprint = _average_policy_from_state(state)
    blueprint_digest = policy_digest(blueprint)
    blueprint_identity = blueprint_digest == state["average_policy_sha256"]
    belief, descriptor = build_fresh_seat1_target(
        source, board=board, target_seat=parsed["local_blocker_target_seat"],
    )
    target_digest, descriptor_digest = _belief_digest(belief), _json_digest(descriptor)
    target_identity = (
        target_digest == target_spec["target_belief_sha256"]
        and descriptor_digest == target_spec["target_descriptor_sha256"]
        and belief.hands_by_player == source.hands_by_player
    )

    base = FactorTTBeliefWorkspace.compile(
        source_workspace.topology.base, belief,
        query_chunk_records=parsed["query_chunk_records"],
    )
    workspace = OpenModeFactorTTWorkspace.compile(source_workspace.topology, base)
    gpu = CuPyBidirectionalIncidence.compile(sparse)
    shared = SharedResidentAutomatonBundle.compile(workspace, automata)
    context = bind_resident_response_context(
        shared, layout=layout, workspace=workspace, sparse=sparse,
        source_policy=blueprint, hands_by_player=belief.hands_by_player,
        cupy_sparse=gpu,
        maximum_feature_width_per_batch=parsed["maximum_feature_width_per_batch"],
    )
    blueprint_quality, _ = _resident_quality_row(
        layout=layout, workspace=workspace, sparse=sparse, automata=automata,
        policy=blueprint, label="blueprint_average64",
        hands_by_player=belief.hands_by_player, belief_cache=context.belief_cache,
        automaton_caches=shared.automaton_caches, gpu=gpu, payoff_span=parsed["stack"],
        maximum_feature_width_per_batch=parsed["maximum_feature_width_per_batch"],
    )
    solver = ResidentLeafAdjointPublicTreeCFR(
        layout, workspace, sparse, automata, parsed["solver_variant"],
        belief_cache=context.belief_cache, automaton_caches=shared.automaton_caches,
        cupy_sparse=gpu,
        maximum_feature_width_per_batch=parsed["maximum_feature_width_per_batch"],
        hands_by_player=belief.hands_by_player,
    )
    solver.warm_start(
        blueprint,
        parsed["warm_regret_mass_payoff_fraction"] * float(layout.game.payoff_span),
    )
    warm_distance = _policy_distance(blueprint, solver.current_strategy())
    release_cupy_memory_pool()
    memory_rows = [_memory_snapshot(cp)]
    step_rows = []
    checkpoints: dict[int, dict[str, Any]] = {}
    cumulative_ms = 0.0
    for iteration in range(1, parsed["maximum_search_steps"] + 1):
        started = time.perf_counter()
        solver.step()
        wall_ms = (time.perf_counter() - started) * 1000.0
        cumulative_ms += wall_ms
        if solver.last_step_work is None:
            raise AssertionError("deep-horizon step telemetry is absent")
        step_row = _step_row(solver.last_step_work, wall_ms=wall_ms)
        step_row["maximum_middle_rank"] = max(
            row.maximum_terminal_middle_rank for row in solver.last_step_work.traversers
        )
        step_row["maximum_terminal_peak_numeric_bytes"] = max(
            row.maximum_terminal_peak_numeric_bytes for row in solver.last_step_work.traversers
        )
        step_rows.append(step_row)
        memory_rows.append(_memory_snapshot(cp))
        if iteration in parsed["checkpoints"] or iteration == 1:
            current, average = solver.current_strategy(), solver.average_strategy()
            checkpoints[iteration] = {
                "iteration": iteration, "cumulative_search_ms": cumulative_ms,
                "current": current, "average": average,
                "current_policy_sha256": policy_digest(current),
                "average_policy_sha256": policy_digest(average),
                "current_mean_tv_from_blueprint": mean_policy_total_variation(blueprint, current),
                "average_mean_tv_from_blueprint": mean_policy_total_variation(blueprint, average),
            }
        if iteration % 8 == 0:
            print(f"  {target_spec['target']}: completed step {iteration}/64", flush=True)

    parent_target = _parent_target(parent, str(target_spec["target"]))
    parent_blocks = parent_target["block_rows"]
    anchors = [
        {"acting_seat": block["acting_seat"], "information_key": block["anchor_information_key"]}
        for block in parent_blocks
    ]
    replayed_blocks = build_public_node_blocks(
        blueprint, checkpoints[1]["current"], anchors,
    )
    parent_block_replay = all(
        replayed["acting_seat"] == opened["acting_seat"]
        and replayed["public_history"] == opened["public_history"]
        and replayed["anchor_information_key"] == opened["anchor_information_key"]
        and replayed["information_keys"] == opened["information_keys"]
        for replayed, opened in zip(replayed_blocks, parent_blocks, strict=True)
    )
    parent_soft_digest_match = (
        checkpoints[1]["current_policy_sha256"] == parent_target["soft_candidate_policy_sha256"]
    )

    endpoints = {
        f"{kind}{iteration}": checkpoints[iteration][kind]
        for iteration in parsed["checkpoints"]
        for kind in ("current", "average")
    }
    endpoints["purified_average64"] = purify_policy(checkpoints[64]["average"])
    if tuple(endpoints) != parsed["endpoint_directions"]:
        raise AssertionError("deep-horizon endpoint order changed")
    scales = geometric_halving_scales(numerical_floor=parsed["numerical_floor"])
    blueprint_nash = float(blueprint_quality["nash_conv"])
    raw_guard = parsed["acceptance_guard_normalized"] * parsed["stack"]
    block_rows = []
    for opened_block in parent_blocks:
        keys = tuple(opened_block["information_keys"])
        family_rows = []
        for family_name, endpoint in endpoints.items():
            search_started = time.perf_counter()

            def evaluate(scale_index: int) -> dict[str, Any]:
                construction_started = time.perf_counter()
                policy = interpolate_policy_atoms(
                    blueprint, endpoint, keys, scale=scales[scale_index],
                )
                construction_ms = (time.perf_counter() - construction_started) * 1000.0
                certificate = _certificate(
                    candidate_id=(
                        f"seat{opened_block['acting_seat']}_{family_name}"
                        f"@scale_{scale_index:02d}"
                    ),
                    policy=policy, layout=layout, belief=belief, context=context,
                    shared=shared, gpu=gpu, blueprint_quality=blueprint_quality,
                    parsed=parsed,
                )
                quality = certificate["quality"]
                value = 0.0 if quality is None else _positive_value(
                    blueprint_nash, float(quality["nash_conv"]),
                )
                memory = _memory_snapshot(cp)
                memory_rows.append(memory)
                return {
                    "scale_index": scale_index, "scale": scales[scale_index],
                    "policy_sha256": policy_digest(policy),
                    "construction_ms": construction_ms,
                    "changed_information_set_count": len(atomic_policy_manifest(blueprint, policy)),
                    "certificate_anchor_policy_sha256": blueprint_digest,
                    "certificate_anchor_nash_conv": blueprint_nash,
                    "independent_from_blueprint": True,
                    "positive_certified_value": value,
                    "normalized_objective_reduction": None if quality is None else (
                        blueprint_nash - float(quality["nash_conv"])
                    ) / parsed["stack"],
                    "value_per_certificate_second": _safe_ratio(
                        value, float(certificate["wall_ms"]) / 1000.0,
                    ),
                    **certificate_binding_diagnostics(certificate, blueprint_quality, raw_guard),
                    "certificate": certificate, "memory_after": memory,
                }

            search = exact_discrete_convex_scale_search(evaluate, scale_count=len(scales))
            best_index = search["best_complete_scale_index"]
            best = None if best_index is None else next(
                row for row in search["queried_rows"] if row["scale_index"] == best_index
            )
            boundary_index = search["largest_complete_scale_index"]
            boundary = None if boundary_index is None else next(
                row for row in search["queried_rows"] if row["scale_index"] == boundary_index
            )
            family_rows.append({
                "direction_family": family_name,
                "acting_seat": opened_block["acting_seat"],
                "public_history": opened_block["public_history"],
                "information_keys": list(keys), "information_set_count": len(keys),
                "endpoint_policy_sha256": policy_digest(endpoint),
                "endpoint_mean_tv_from_blueprint": mean_policy_total_variation(blueprint, endpoint),
                "search_wall_ms": (time.perf_counter() - search_started) * 1000.0,
                "search": search,
                "largest_complete_scale": None if boundary is None else boundary["scale"],
                "best_complete_scale": None if best is None else best["scale"],
                "best_positive_certified_value": 0.0 if best is None else best["positive_certified_value"],
                "best_value_per_certificate_second": None if best is None else best["value_per_certificate_second"],
                "best_certificate_wall_ms": None if best is None else best["certificate"]["wall_ms"],
            })
        parent_soft = next(
            row for row in opened_block["direction_rows"]
            if row["direction_family"] == "soft_dcfr"
        )
        parent_vertex = next(
            row for row in opened_block["direction_rows"]
            if row["direction_family"] == "regret_vertex"
        )
        block_rows.append({
            "acting_seat": opened_block["acting_seat"],
            "public_history": opened_block["public_history"],
            "anchor_information_key": opened_block["anchor_information_key"],
            "information_keys": list(keys), "information_set_count": len(keys),
            "parent_soft_positive_certified_value": parent_soft["best_positive_certified_value"],
            "parent_vertex_positive_certified_value": parent_vertex["best_positive_certified_value"],
            "parent_bounded_oracle_positive_certified_value": opened_block["bounded_oracle_positive_certified_value"],
            "direction_rows": family_rows,
        })

    result = {
        "target": target_spec["target"], "board_id": target_spec["board_id"],
        "board": target_spec["board"], "range_family": family,
        "target_shift": target_spec["target_shift"],
        "source_belief_sha256": source_digest, "target_belief_sha256": target_digest,
        "target_descriptor_sha256": descriptor_digest, "target_descriptor": descriptor,
        "source_checkpoint_identity": source_identity, "target_identity": target_identity,
        "blueprint_identity": blueprint_identity, "warm_start_distance": warm_distance,
        "blueprint_quality": blueprint_quality,
        "search_steps": step_rows,
        "checkpoint_rows": [
            {key: value for key, value in checkpoints[iteration].items() if key not in {"current", "average"}}
            for iteration in parsed["checkpoints"]
        ],
        "parent_soft_digest_match_diagnostic": parent_soft_digest_match,
        "parent_block_replay": parent_block_replay,
        "endpoint_policy_sha256": {
            name: policy_digest(policy) for name, policy in endpoints.items()
        },
        "block_rows": block_rows, "scale_grid": list(scales),
        "emitted_candidate_id": "blueprint_average64",
        "emitted_policy_sha256": blueprint_digest, "memory_rows": memory_rows,
    }
    del solver, context, shared, gpu, workspace, base, automata, source_workspace
    del sparse, layout, belief, source
    gc.collect()
    release_cupy_memory_pool()
    return result


def run_h32_deep_horizon_opportunity_audit(
    config_path: Path = _CONFIG, output_path: Path = _OUTPUT,
) -> dict[str, Any]:
    """Execute the frozen two-target deep-horizon ladder."""

    started = time.perf_counter()
    parsed = parse_h32_deep_horizon_opportunity_config(
        json.loads(config_path.read_text(encoding="utf-8")),
    )
    source_parent = json.loads(_SOURCE.read_text(encoding="utf-8"))
    parent = json.loads(_PARENT_RESULT.read_text(encoding="utf-8"))
    git = _strict_git_metadata()
    cp, runtime = _validate_runtime(parsed)
    if git["dirty"]:
        raise RuntimeError("deep-horizon execution requires a clean Git state")
    if not source_parent["passed"] or not parent["gates"]["passed"]:
        raise ValueError("deep-horizon parent did not pass")
    targets = []
    for target_spec in parsed["targets"]:
        print(f"deep-horizon audit: {target_spec['target']}", flush=True)
        targets.append(_run_target(parsed, source_parent, parent, target_spec, cp))

    blocks = [block for target in targets for block in target["block_rows"]]
    directions = [row for block in blocks for row in block["direction_rows"]]
    certificates = [row for direction in directions for row in direction["search"]["queried_rows"]]
    steps = [row for target in targets for row in target["search_steps"]]
    checkpoints = [row for target in targets for row in target["checkpoint_rows"]]
    memory_rows = [row for target in targets for row in target["memory_rows"]]
    scales = geometric_halving_scales(numerical_floor=parsed["numerical_floor"])
    family_values = {
        family: math.fsum(
            float(row["best_positive_certified_value"])
            for row in directions if row["direction_family"] == family
        )
        for family in parsed["endpoint_directions"]
    }
    parent_soft_sum = math.fsum(float(block["parent_soft_positive_certified_value"]) for block in blocks)
    parent_vertex_sum = math.fsum(float(block["parent_vertex_positive_certified_value"]) for block in blocks)
    parent_oracle_sum = math.fsum(float(block["parent_bounded_oracle_positive_certified_value"]) for block in blocks)
    shallow_best = max(family_values["current8"], family_values["average8"])
    deep_best = max(
        family_values[name]
        for name in ("current32", "average32", "current64", "average64")
    )
    raw_guard_total = len(blocks) * parsed["acceptance_guard_normalized"] * parsed["stack"]
    total_seconds = time.perf_counter() - started
    gates_config = parsed["gates"]
    finite_values = [
        value for target in targets for value in (
            target["blueprint_quality"]["nash_conv"],
            target["warm_start_distance"]["maximum_probability_error"],
            target["warm_start_distance"]["mean_total_variation"],
        )
    ] + [
        value for row in certificates for value in (
            row["scale"], row["construction_ms"], row["positive_certified_value"],
            row["certificate"]["wall_ms"], row["certificate"]["partial_nash_conv"],
        )
    ]
    gates = {
        "clean_git": (not git["dirty"]) == gates_config["require_clean_git_state"],
        "parent_passed": (source_parent["passed"] and parent["gates"]["passed"]) == gates_config["require_parent_passed"],
        "target_rows": len(targets) == gates_config["expected_target_rows"],
        "search_steps": len(steps) == gates_config["expected_search_steps"],
        "checkpoint_rows": len(checkpoints) == gates_config["expected_checkpoint_rows"],
        "public_blocks": len(blocks) == gates_config["expected_public_blocks"],
        "direction_rows": len(directions) == gates_config["expected_direction_rows"],
        "blueprint_quality_labels": len(targets) == gates_config["expected_blueprint_quality_labels"],
        "certificate_query_bound": (
            len(certificates) <= gates_config["maximum_total_certificate_queries"]
            and all(row["search"]["query_count"] <= gates_config["maximum_queries_per_direction"] for row in directions)
        ),
        "source_checkpoint_identity": all(row["source_checkpoint_identity"] for row in targets) == gates_config["require_source_checkpoint_identity"],
        "target_identity": all(row["target_identity"] for row in targets) == gates_config["require_target_identity"],
        "blueprint_identity": all(row["blueprint_identity"] for row in targets) == gates_config["require_blueprint_identity"],
        "numerical_warm_start_identity": all(
            row["warm_start_distance"]["maximum_probability_error"] <= parsed["maximum_warm_start_probability_error"]
            and row["warm_start_distance"]["mean_total_variation"] <= parsed["maximum_warm_start_mean_total_variation"]
            for row in targets
        ) == gates_config["require_numerical_warm_start_identity"],
        "parent_block_replay": all(row["parent_block_replay"] for row in targets) == gates_config["require_parent_block_replay"],
        "checkpoint_identity": all(tuple(row["iteration"] for row in target["checkpoint_rows"]) == parsed["checkpoints"] for target in targets) == gates_config["require_checkpoint_identity"],
        "endpoint_direction_identity": all(tuple(row["direction_family"] for row in block["direction_rows"]) == parsed["endpoint_directions"] for block in blocks) == gates_config["require_endpoint_direction_identity"],
        "convex_scope": all(direction_has_convex_scope(row) for row in directions) == gates_config["require_convex_scope"],
        "search_invariants": all(search_invariants(row["search"], scale_count=len(scales)) for row in directions) == gates_config["require_search_invariants"],
        "immutable_anchor": all(
            row["certificate_anchor_policy_sha256"] == target["blueprint_quality"]["policy_sha256"]
            and row["certificate_anchor_nash_conv"] == target["blueprint_quality"]["nash_conv"]
            for target in targets for block in target["block_rows"]
            for direction in block["direction_rows"] for row in direction["search"]["queried_rows"]
        ) == gates_config["require_immutable_anchor"],
        "independent_certificates": all(row["independent_from_blueprint"] for row in certificates) == gates_config["require_independent_certificates"],
        "blueprint_emission": all(
            row["emitted_candidate_id"] == "blueprint_average64"
            and row["emitted_policy_sha256"] == row["blueprint_quality"]["policy_sha256"]
            for row in targets
        ) == gates_config["require_blueprint_emission"],
        "search_step_ms": all(row["wall_ms"] <= gates_config["maximum_search_step_ms"] for row in steps),
        "certificate_ms": all(row["certificate"]["wall_ms"] <= gates_config["maximum_certificate_ms"] for row in certificates),
        "memory": (
            max(
                max(row["gpu_pool_total_bytes"] for row in memory_rows),
                max(row["maximum_gpu_pool_bytes"] for row in steps),
            ) <= gates_config["maximum_gpu_pool_bytes"]
            and min(row["gpu_free_bytes"] for row in memory_rows) >= gates_config["minimum_physical_free_bytes"]
        ),
        "finite": all(math.isfinite(float(value)) for value in finite_values) == gates_config["require_finite"],
        "strategy_population_claim_null": True == gates_config["require_strategy_population_claim_null"],
        "total_audit_seconds": total_seconds <= gates_config["maximum_total_audit_seconds"],
    }
    gates["passed"] = all(gates.values())
    result = {
        "schema_version": 1, "status": "frozen_h32_deep_horizon_opportunity_audit_executed",
        "methodology": {
            "preregistered": True, "targets_are_fresh_holdouts": False,
            "measurement_context": "off_clock_depth_identification",
            "single_actor_single_public_node_scope": True,
            "adaptive_scale_is_available_live": False, "deployment_authorized": False,
            "emitted_policy": "immutable_blueprint", "strategy_population_claim": None,
        },
        "config_sha256": _sha256(config_path),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "environment": {**environment_metadata(), **runtime, "git": git},
        "target_rows": targets,
        "aggregate": {
            "targets": len(targets), "blocks": len(blocks), "directions": len(directions),
            "certificate_queries": len(certificates),
            "directions_with_complete_scale": sum(row["search"]["best_complete_scale_index"] is not None for row in directions),
            "family_positive_certified_value": family_values,
            "parent_soft_positive_certified_value": parent_soft_sum,
            "parent_vertex_positive_certified_value": parent_vertex_sum,
            "parent_bounded_oracle_positive_certified_value": parent_oracle_sum,
            "shallow_best_8_positive_certified_value": shallow_best,
            "deep_best_32_or_64_positive_certified_value": deep_best,
            "deep_to_shallow_ratio": _safe_ratio(deep_best, shallow_best),
            "deep_to_parent_bounded_oracle_ratio": _safe_ratio(deep_best, parent_oracle_sum),
            "material_depth_lift": material_depth_lift(shallow_best, deep_best, raw_guard_total=raw_guard_total),
            "purification_lift_over_average64": family_values["purified_average64"] - family_values["average64"],
            "raw_guard_total": raw_guard_total,
            "maximum_gpu_pool_bytes": max(
                max(row["gpu_pool_total_bytes"] for row in memory_rows),
                max(row["maximum_gpu_pool_bytes"] for row in steps),
            ),
            "minimum_gpu_free_bytes": min(row["gpu_free_bytes"] for row in memory_rows),
        },
        "gates": gates, "total_audit_seconds": total_seconds,
        "decision": "accept_prospective_deep_horizon_measurement" if gates["passed"] else "reject_deep_horizon_audit",
        "strategy_population_claim": None,
        "limitations": [
            "Two disclosed opened targets are a mechanism panel, not a population or holdout.",
            "Every scale search is off-clock and no observed scale is available to a live rule.",
            "The seven-direction library is a lower bound on attainable local value.",
            "A null depth result is evidence about this solver and contract, not proof of opportunity exhaustion.",
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
    result = run_h32_deep_horizon_opportunity_audit(args.config, args.output)
    print(json.dumps({"output": str(args.output), "passed": result["gates"]["passed"], "aggregate": result["aggregate"]}, indent=2))
    if not result["gates"]["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
