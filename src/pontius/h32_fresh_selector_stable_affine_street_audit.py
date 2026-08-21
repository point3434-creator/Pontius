"""Prospective fresh h32 seat-0 selector-stable affine street trial."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import gc
import hashlib
import json
import math
from pathlib import Path
import subprocess
import time
from typing import Any, Mapping

from .axis_cfr_checkpoint import axis_cfr_checkpoint_digest
from .cupy_sparse_incidence import CuPyBidirectionalIncidence, release_cupy_memory_pool
from .delta_certificate_contract import (
    geometric_halving_scales,
    interpolate_policy_atoms,
)
from .evidence_protocol import DEFAULT_GPU_NUMERICAL_IDENTITY
from .factor_tt_contraction import FactorTTBeliefWorkspace
from .fresh_h32_strategy_transfer_audit import _belief_digest
from .h32_affine_resident_cache_preflight import _strict_git_metadata, _validate_runtime
from .h32_atomic_response_preflight import select_one_atom_per_acting_seat
from .h32_fresh_board_panel_cache_preflight import _json_digest
from .h32_fresh_public_block_radius_audit import build_fresh_seat0_target
from .h32_fresh_public_block_value_audit import (
    build_public_node_blocks,
    information_key_public_coordinates,
)
from .h32_fresh_regret_vertex_opportunity_audit import (
    build_regret_vertex_candidate,
    recover_iteration_one_dcfr_regret_deltas,
)
from .h32_fresh_union_value_audit import _memory_snapshot
from .h32_selector_stable_affine_certificate_audit import (
    _build_case,
    _direct_rows,
    _fixed_validation_scale,
    _source_quality,
    affine_direct_errors,
)
from .h32_warm_search_acceptance_audit import (
    _average_policy_from_state,
    _policy_distance,
)
from .incremental_leaf_adjoint_response import verify_incremental_leaf_adjoint_candidate
from .incremental_policy_tt import compile_policy_probability_tape
from .open_mode_factor_tt import OpenModeFactorTTWorkspace
from .real_policy import policy_digest
from .reporting import environment_metadata
from .resident_leaf_adjoint_cfr import ResidentLeafAdjointPublicTreeCFR
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
_CONFIG = (
    _ROOT / "experiments/configs/h32-fresh-selector-stable-affine-street-v1.json"
)
_OUTPUT = (
    _ROOT / "experiments/results/h32-fresh-selector-stable-affine-street-v1.json"
)
_SOURCE = _ROOT / "experiments/results/h32-fresh-panel-source-blueprints-v1.json"
_PARENT_CONFIG = (
    _ROOT / "experiments/configs/h32-selector-stable-affine-certificate-v2.json"
)
_PARENT_RESULT = (
    _ROOT / "experiments/results/h32-selector-stable-affine-certificate-v2.json"
)
_PARENT_ADR = (
    _ROOT
    / "docs/decisions"
    / "ADR-0190-selector-stable-affine-certificate-is-exact-and-fits-retained-street-ledgers.md"
)
_REQUIREMENTS = _ROOT / "experiments/requirements/leaf-adjoint-gpu-screen-v1.txt"
_IMPLEMENTATION = Path(__file__)
_TEST = _ROOT / "tests/test_h32_fresh_selector_stable_affine_street_audit.py"

_PATHS = {
    "expected_source_result_sha256": _SOURCE,
    "expected_affine_parent_config_sha256": _PARENT_CONFIG,
    "expected_affine_parent_result_sha256": _PARENT_RESULT,
    "expected_affine_parent_decision_sha256": _PARENT_ADR,
    "expected_requirements_sha256": _REQUIREMENTS,
    "expected_target_builder_sha256": (
        _ROOT / "src/pontius/h32_fresh_public_block_radius_audit.py"
    ),
    "expected_public_block_builder_sha256": (
        _ROOT / "src/pontius/h32_fresh_public_block_value_audit.py"
    ),
    "expected_direction_builder_sha256": (
        _ROOT / "src/pontius/h32_fresh_regret_vertex_opportunity_audit.py"
    ),
    "expected_shared_context_sha256": (
        _ROOT / "src/pontius/shared_resident_response_context.py"
    ),
    "expected_incremental_verifier_sha256": (
        _ROOT / "src/pontius/incremental_leaf_adjoint_response.py"
    ),
    "expected_affine_verifier_sha256": (
        _ROOT / "src/pontius/selector_stable_affine_response.py"
    ),
    "expected_resident_cfr_sha256": _ROOT / "src/pontius/resident_leaf_adjoint_cfr.py",
    "expected_atom_manifest_sha256": _ROOT / "src/pontius/h32_atomic_response_preflight.py",
    "expected_interpolation_sha256": _ROOT / "src/pontius/delta_certificate_contract.py",
    "expected_evidence_protocol_sha256": _ROOT / "src/pontius/evidence_protocol.py",
    "expected_audit_implementation_sha256": _IMPLEMENTATION,
    "expected_control_test_sha256": _TEST,
}

_FRESH_TARGETS = [
    {
        "target": "panel_1/balanced/local_blocker_seat0_x2",
        "board_id": "panel_1",
        "board": ["5c", "8c", "8d", "Jc", "As"],
        "range_family": "balanced",
        "target_shift": "local_blocker_seat0_x2",
        "source_belief_sha256": (
            "376e8a44217f35dfdf305035fe8f3bbfb52b010e14050bedaf55da78c9e72885"
        ),
        "target_belief_sha256": (
            "a1a69f7cb3cf89265895edea3eff6af218c8e455f01535a32092a1de758f18c7"
        ),
        "target_descriptor_sha256": (
            "e350d35a4e640d50d45fee6159fb65ce63272aaa77c958cd369bc337227eb979"
        ),
    },
    {
        "target": "panel_1/blocker_heavy/local_blocker_seat0_x2",
        "board_id": "panel_1",
        "board": ["5c", "8c", "8d", "Jc", "As"],
        "range_family": "blocker_heavy",
        "target_shift": "local_blocker_seat0_x2",
        "source_belief_sha256": (
            "aa3a5a8abe8dc72fe436134d4b619239a87b002134cdad88a908d833318b5067"
        ),
        "target_belief_sha256": (
            "a9976c59745a4765640dcf8baa2f4631b18ffdef81a4d4f4a95aa35cc93ae754"
        ),
        "target_descriptor_sha256": (
            "4ec5c47fd27c4c724102987ef28547831253c32f9edd59e6d04195af8bf0f96d"
        ),
    },
    {
        "target": "panel_2/blocker_heavy/local_blocker_seat0_x2",
        "board_id": "panel_2",
        "board": ["2c", "3s", "5d", "Js", "Qc"],
        "range_family": "blocker_heavy",
        "target_shift": "local_blocker_seat0_x2",
        "source_belief_sha256": (
            "59f955c6b89bdc56670dc16b19795451404fe80ff37f519bac007975d85200f1"
        ),
        "target_belief_sha256": (
            "e67c92d3137bd69cb2ecdbc46ddc89a9975c71b93324a6d57d4114d000a76790"
        ),
        "target_descriptor_sha256": (
            "47f5fa84d62bc72aba8a632b26ec5d62f0c0e53bc8fce3219b57971f78aa6934"
        ),
    },
    {
        "target": "panel_3/balanced/local_blocker_seat0_x2",
        "board_id": "panel_3",
        "board": ["4h", "7h", "9s", "Jd", "Kc"],
        "range_family": "balanced",
        "target_shift": "local_blocker_seat0_x2",
        "source_belief_sha256": (
            "cadd9449259f56de43ae4d710c2e3fd6ae4733e7b7c8323836b87578a3cc9a71"
        ),
        "target_belief_sha256": (
            "da203c79eb38f89fa4cdb38081b01b3b1a696c034b5590acc52358dfa022d086"
        ),
        "target_descriptor_sha256": (
            "7d089ba1d5ad9ac0c656a49d36be88d5715f3f30a07bf1db30b00368814595b4"
        ),
    },
]


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required fresh affine-street input is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _digest_absent_at_commit(digest: str, commit: str) -> bool:
    completed = subprocess.run(
        ["git", "grep", "-F", "-n", digest, commit, "--", "."],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode == 1:
        return True
    if completed.returncode == 0:
        return False
    raise RuntimeError(f"freshness history scan failed: {completed.stderr.strip()}")


def _start_allowed(
    elapsed_ms: float,
    *,
    work_guard_ms: float,
    emission_reserve_ms: float,
    street_budget_ms: float,
) -> bool:
    values = (elapsed_ms, work_guard_ms, emission_reserve_ms, street_budget_ms)
    if any(not math.isfinite(value) or value < 0.0 for value in values):
        raise ValueError("fresh affine-street deadline inputs must be finite and nonnegative")
    return elapsed_ms + work_guard_ms + emission_reserve_ms <= street_budget_ms


def parse_h32_fresh_selector_stable_affine_street_config(
    config: dict[str, Any],
) -> dict[str, Any]:
    """Validate ADR-0191's complete fresh causal street contract."""

    fields = {
        "evidence_stage",
        *_PATHS,
        "seed",
        "freshness_base_commit",
        "targets",
        "target_construction",
        "target_seat",
        "acting_seat",
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
        "direction_family",
        "affine_scope",
        "source_selector_rule",
        "selector_margin_allowance",
        "envelope_numerical_allowance",
        "safety_fraction",
        "scale_grid",
        "numerical_floor",
        "fixed_validation_scale_index",
        "seat_order",
        "acceptance_guard_normalized",
        "maximum_feature_width_per_batch",
        "street_budget_ms",
        "emission_reserve_ms",
        "candidate_ready_cutoff_ms",
        "post_step_candidate_proof_guard_ms",
        "post_construction_affine_guard_ms",
        "fallback_policy",
        "teacher_timing",
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
        raise ValueError("fresh affine-street fields differ from ADR-0191")
    identity = DEFAULT_GPU_NUMERICAL_IDENTITY
    frozen = {
        "evidence_stage": (
            "preregistered_after_adr0190_before_any_fresh_seat0_policy_step_or_quality_label"
        ),
        "seed": 20260821,
        "freshness_base_commit": "76bcc4b80d976376220deaeb2601e721d54eeb92",
        "targets": _FRESH_TARGETS,
        "target_construction": (
            "double_label_free_maximum_overlap_then_strength_then_smallest_canonical_hand_at_seat0"
        ),
        "target_seat": 0,
        "acting_seat": 0,
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
        "block_anchor_selection": (
            "lexicographically_first_changed_information_set_for_fixed_acting_seat0"
        ),
        "block_membership": (
            "all_changed_information_sets_at_fixed_acting_seat0_exact_public_history"
        ),
        "direction_family": "regret_vertex",
        "affine_scope": (
            "one_acting_seat0_one_exact_public_node_source_to_scale_one_endpoint"
        ),
        "source_selector_rule": (
            "immutable_blueprint_first_action_argmax_tape_until_first_conservative_tie"
        ),
        "selector_margin_allowance": 2e-11,
        "envelope_numerical_allowance": 2e-11,
        "safety_fraction": 0.5,
        "scale_grid": (
            "shared_geometric_halving_inclusive_while_scale_at_least_numerical_floor"
        ),
        "numerical_floor": 1e-10,
        "fixed_validation_scale_index": 16,
        "seat_order": [0, 1, 2, 3, 4, 5],
        "acceptance_guard_normalized": 1e-10,
        "maximum_feature_width_per_batch": 384,
        "street_budget_ms": 15000.0,
        "emission_reserve_ms": 1000.0,
        "candidate_ready_cutoff_ms": 14000.0,
        "post_step_candidate_proof_guard_ms": 1000.0,
        "post_construction_affine_guard_ms": 500.0,
        "fallback_policy": "preloaded_immutable_source_average64_blueprint",
        "teacher_timing": "strictly_after_live_emission_is_frozen",
        "maximum_warm_start_probability_error": (
            identity.maximum_policy_probability_error
        ),
        "maximum_warm_start_mean_total_variation": (
            identity.maximum_policy_mean_information_set_total_variation
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
        raise ValueError("fresh affine-street workload differs from ADR-0191")
    for field, path in _PATHS.items():
        if config[field] != _sha256(path):
            raise ValueError(f"fresh affine-street source mismatch: {field}")
    gates = {
        "expected_target_rows": 4,
        "expected_search_steps": 4,
        "expected_public_blocks": 4,
        "expected_affine_seat_rows": 24,
        "expected_fixed_direct_validations": 4,
        "maximum_affine_intercept_error": 2e-11,
        "maximum_direct_utility_error": 1e-9,
        "maximum_direct_best_response_error": 1e-9,
        "maximum_direct_deviation_gain_error": 1e-9,
        "maximum_search_step_ms": 60000.0,
        "maximum_construction_ms": 60000.0,
        "maximum_affine_sweep_ms": 60000.0,
        "maximum_direct_validation_ms": 60000.0,
        "maximum_gpu_pool_bytes": 12000000000,
        "minimum_physical_free_bytes": 1000000000,
        "maximum_total_audit_seconds": 1800.0,
        "require_clean_git_state": True,
        "require_parent_passed": True,
        "require_freshness_at_base_commit": True,
        "require_source_checkpoint_identity": True,
        "require_target_identity": True,
        "require_blueprint_identity": True,
        "require_numerical_warm_start_identity": True,
        "require_nonempty_coherent_block": True,
        "require_affine_scope_identity": True,
        "require_fixed_validation_inside_selector_interval": True,
        "require_fixed_validation_zero_response_flips": True,
        "require_selected_direct_completion": True,
        "require_selected_zero_response_flips": True,
        "require_causal_teacher_order": True,
        "require_fixed_rule_identity": True,
        "require_fail_closed_emission": True,
        "require_hard_deadline_fit": True,
        "require_finite": True,
        "require_strategy_population_claim_null": True,
    }
    if config["gates"] != gates:
        raise ValueError("fresh affine-street gates differ from ADR-0191")
    if config["candidate_ready_cutoff_ms"] != (
        config["street_budget_ms"] - config["emission_reserve_ms"]
    ):
        raise ValueError("fresh affine-street candidate cutoff is inconsistent")
    return {
        **config,
        "targets": tuple(dict(row) for row in config["targets"]),
        "seat_order": tuple(config["seat_order"]),
        "gates": dict(gates),
    }


def _construct_seat0_payload(
    *,
    layout: Any,
    hands_by_player: tuple[tuple[Any, ...], ...],
    blueprint: Mapping[str, Mapping[Any, float]],
    solver: ResidentLeafAdjointPublicTreeCFR,
    warm_regret_mass: float,
) -> tuple[dict[str, Any], float]:
    started = time.perf_counter()
    soft_candidate = solver.current_strategy()
    regret_deltas = recover_iteration_one_dcfr_regret_deltas(
        blueprint,
        solver.regret_table(),
        warm_regret_mass=warm_regret_mass,
    )
    anchors = select_one_atom_per_acting_seat(
        layout,
        hands_by_player,
        blueprint,
        soft_candidate,
    )
    blocks = build_public_node_blocks(blueprint, soft_candidate, anchors)
    seat0 = next(block for block in blocks if int(block["acting_seat"]) == 0)
    keys = tuple(seat0["information_keys"])
    endpoint = build_regret_vertex_candidate(blueprint, regret_deltas, keys)
    endpoint_probabilities = compile_policy_probability_tape(
        layout,
        hands_by_player,
        endpoint,
    )
    elapsed_ms = (time.perf_counter() - started) * 1000.0
    return {
        "block": seat0,
        "all_block_count": len(blocks),
        "information_keys": keys,
        "endpoint": endpoint,
        "endpoint_probabilities": endpoint_probabilities,
        "soft_candidate_policy_sha256": policy_digest(soft_candidate),
        "direction_policy_sha256": policy_digest(endpoint),
    }, elapsed_ms


def _affine_sweep(
    *,
    parsed: dict[str, Any],
    payload: Mapping[str, Any],
    context: Any,
    shared: Any,
    gpu: Any,
    blueprint_quality: Mapping[str, Any],
) -> tuple[tuple[Any, ...], Any, float]:
    started = time.perf_counter()
    affine_rows = tuple(
        evaluate_selector_stable_affine_leaf_adjoint_seat(
            cache,
            payload["endpoint_probabilities"],
            acting_player=parsed["acting_seat"],
            selector_margin_allowance=parsed["selector_margin_allowance"],
            maximum_feature_width_per_batch=parsed[
                "maximum_feature_width_per_batch"
            ],
            belief_cache=context.belief_cache,
            automaton_cache=shared.automaton_caches[target_player],
            cupy_sparse=gpu,
        )
        for target_player, cache in enumerate(context.response_caches)
    )
    envelope = certify_selector_stable_affine_envelope(
        affine_rows,
        blueprint_deviation_gains=tuple(blueprint_quality["deviation_gains"]),
        blueprint_nash_conv=float(blueprint_quality["nash_conv"]),
        raw_guard=parsed["acceptance_guard_normalized"] * parsed["stack"],
        scale_grid=geometric_halving_scales(
            numerical_floor=parsed["numerical_floor"]
        ),
        safety_fraction=parsed["safety_fraction"],
        numerical_allowance=parsed["envelope_numerical_allowance"],
    )
    return affine_rows, envelope, (time.perf_counter() - started) * 1000.0


def _selected_direct_errors(envelope: Any, direct: Mapping[str, Any]) -> dict[str, float]:
    quality = direct["quality"]
    if quality is None:
        raise ValueError("selected direct comparison requires complete quality")
    return {
        "maximum_utility_error": max(
            abs(left - right)
            for left, right in zip(
                envelope.predicted_utilities,
                quality["utilities"],
                strict=True,
            )
        ),
        "maximum_best_response_error": max(
            abs(left - right)
            for left, right in zip(
                envelope.predicted_best_response_values,
                quality["best_response_values"],
                strict=True,
            )
        ),
        "maximum_deviation_gain_error": max(
            abs(left - right)
            for left, right in zip(
                envelope.predicted_deviation_gains,
                quality["deviation_gains"],
                strict=True,
            )
        ),
    }


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
    belief, descriptor = build_fresh_seat0_target(
        source,
        board=board,
        target_seat=parsed["target_seat"],
    )
    target_digest = _belief_digest(belief)
    descriptor_digest = _json_digest(descriptor)
    target_identity = (
        target_digest == target_spec["target_belief_sha256"]
        and descriptor_digest == target_spec["target_descriptor_sha256"]
        and belief.hands_by_player == source.hands_by_player
    )
    freshness_at_base_commit = all(
        _digest_absent_at_commit(digest, parsed["freshness_base_commit"])
        for digest in (target_digest, descriptor_digest)
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
    blueprint_quality = _source_quality(context, payoff_span=parsed["stack"])
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
    warm_mass = parsed["warm_regret_mass_payoff_fraction"] * float(
        layout.game.payoff_span
    )
    solver.warm_start(blueprint, warm_mass)
    warm_start_distance = _policy_distance(blueprint, solver.current_strategy())
    release_cupy_memory_pool()
    memory_rows = [_memory_snapshot(cp)]

    decision_started = time.perf_counter()
    solver.step()
    search_ms = (time.perf_counter() - decision_started) * 1000.0
    memory_rows.append(_memory_snapshot(cp))
    post_step_elapsed_ms = (time.perf_counter() - decision_started) * 1000.0
    post_step_start_allowed = _start_allowed(
        post_step_elapsed_ms,
        work_guard_ms=parsed["post_step_candidate_proof_guard_ms"],
        emission_reserve_ms=parsed["emission_reserve_ms"],
        street_budget_ms=parsed["street_budget_ms"],
    )

    payload = None
    construction_ms = None
    construction_live = False
    affine_rows = None
    envelope = None
    affine_ms = None
    affine_live = False
    post_construction_start_allowed = None
    selected_policy = None
    selected_policy_digest = None
    live_candidate_ready_elapsed_ms = None
    live_stop_reason = "post_step_candidate_proof_guard"

    if post_step_start_allowed:
        payload, construction_ms = _construct_seat0_payload(
            layout=layout,
            hands_by_player=belief.hands_by_player,
            blueprint=blueprint,
            solver=solver,
            warm_regret_mass=warm_mass,
        )
        construction_live = True
        memory_rows.append(_memory_snapshot(cp))
        elapsed_after_construction = (time.perf_counter() - decision_started) * 1000.0
        post_construction_start_allowed = _start_allowed(
            elapsed_after_construction,
            work_guard_ms=parsed["post_construction_affine_guard_ms"],
            emission_reserve_ms=parsed["emission_reserve_ms"],
            street_budget_ms=parsed["street_budget_ms"],
        )
        live_stop_reason = "post_construction_affine_guard"
        if post_construction_start_allowed:
            affine_rows, envelope, affine_ms = _affine_sweep(
                parsed=parsed,
                payload=payload,
                context=context,
                shared=shared,
                gpu=gpu,
                blueprint_quality=blueprint_quality,
            )
            affine_live = True
            memory_rows.append(_memory_snapshot(cp))
            live_stop_reason = f"affine_{envelope.stop_reason}"
            if envelope.complete:
                selected_policy = interpolate_policy_atoms(
                    blueprint,
                    payload["endpoint"],
                    payload["information_keys"],
                    scale=envelope.selected_scale,
                )
                selected_policy_digest = policy_digest(selected_policy)
                live_candidate_ready_elapsed_ms = (
                    time.perf_counter() - decision_started
                ) * 1000.0
                if (
                    live_candidate_ready_elapsed_ms
                    <= parsed["candidate_ready_cutoff_ms"]
                ):
                    live_stop_reason = "candidate_selected_before_cutoff"
                else:
                    live_stop_reason = "candidate_ready_after_cutoff"

    live_closed_at = time.perf_counter()
    live_closed_elapsed_ms = (live_closed_at - decision_started) * 1000.0
    candidate_live_eligible = (
        affine_live
        and envelope is not None
        and envelope.complete
        and live_candidate_ready_elapsed_ms is not None
        and live_candidate_ready_elapsed_ms <= parsed["candidate_ready_cutoff_ms"]
    )
    emitted_candidate_id = (
        "seat0_regret_vertex_affine" if candidate_live_eligible else "blueprint_average64"
    )
    emitted_policy_sha256 = (
        selected_policy_digest if candidate_live_eligible else blueprint_digest
    )
    live_ledger_ms = live_closed_elapsed_ms + parsed["emission_reserve_ms"]
    live_hard_deadline_fit = (
        live_closed_elapsed_ms <= parsed["candidate_ready_cutoff_ms"]
        and live_ledger_ms <= parsed["street_budget_ms"]
    )
    live_emission_frozen = True
    teacher_started_at = time.perf_counter()
    teacher_started_after_live_close = teacher_started_at >= live_closed_at

    if payload is None:
        payload, construction_ms = _construct_seat0_payload(
            layout=layout,
            hands_by_player=belief.hands_by_player,
            blueprint=blueprint,
            solver=solver,
            warm_regret_mass=warm_mass,
        )
        memory_rows.append(_memory_snapshot(cp))
    if affine_rows is None:
        affine_rows, envelope, affine_ms = _affine_sweep(
            parsed=parsed,
            payload=payload,
            context=context,
            shared=shared,
            gpu=gpu,
            blueprint_quality=blueprint_quality,
        )
        memory_rows.append(_memory_snapshot(cp))
    assert envelope is not None

    scales = geometric_halving_scales(numerical_floor=parsed["numerical_floor"])
    selector_limit = min(row.selector_stable_scale for row in affine_rows)
    fixed_scale = _fixed_validation_scale(
        scales,
        preferred_index=parsed["fixed_validation_scale_index"],
        selector_limit=selector_limit,
    )
    fixed_validation = None
    if fixed_scale is not None:
        fixed_policy = interpolate_policy_atoms(
            blueprint,
            payload["endpoint"],
            payload["information_keys"],
            scale=fixed_scale,
        )
        fixed_rows, fixed_ms = _direct_rows(
            layout=layout,
            policy=fixed_policy,
            hands_by_player=belief.hands_by_player,
            context=context,
            shared=shared,
            gpu=gpu,
            maximum_feature_width_per_batch=parsed[
                "maximum_feature_width_per_batch"
            ],
        )
        fixed_validation = {
            "scale": fixed_scale,
            "strictly_inside_selector_interval": fixed_scale < selector_limit,
            "direct_wall_ms": fixed_ms,
            "direct_response_action_flips": sum(
                row.response_action_flips for row in fixed_rows
            ),
            "errors": affine_direct_errors(
                affine_rows,
                fixed_rows,
                scale=fixed_scale,
            ),
        }
        memory_rows.append(_memory_snapshot(cp))

    selected_validation = None
    selected_value = 0.0
    if envelope.complete:
        if selected_policy is None:
            selected_policy = interpolate_policy_atoms(
                blueprint,
                payload["endpoint"],
                payload["information_keys"],
                scale=envelope.selected_scale,
            )
            selected_policy_digest = policy_digest(selected_policy)
        direct = verify_incremental_leaf_adjoint_candidate(
            candidate_id="seat0_regret_vertex_affine_teacher",
            layout=layout,
            policy=selected_policy,
            hands_by_player=belief.hands_by_player,
            response_caches=context.response_caches,
            blueprint_deviation_gains=tuple(blueprint_quality["deviation_gains"]),
            best_complete_nash_conv=float(blueprint_quality["nash_conv"]),
            payoff_span=parsed["stack"],
            raw_guard=parsed["acceptance_guard_normalized"] * parsed["stack"],
            seat_order=parsed["seat_order"],
            maximum_feature_width_per_batch=parsed[
                "maximum_feature_width_per_batch"
            ],
            belief_cache=context.belief_cache,
            automaton_caches=shared.automaton_caches,
            cupy_sparse=gpu,
        )
        if direct["quality"] is not None:
            selected_value = max(
                0.0,
                float(blueprint_quality["nash_conv"])
                - float(direct["quality"]["nash_conv"]),
            )
        selected_validation = {
            "policy_sha256": policy_digest(selected_policy),
            "direct": direct,
            "errors": (
                None if direct["quality"] is None else _selected_direct_errors(envelope, direct)
            ),
            "direct_positive_certified_value": selected_value,
        }
        memory_rows.append(_memory_snapshot(cp))

    block = payload["block"]
    affine_intercept_error = max(
        abs(
            row.deviation_gain_intercept
            - float(blueprint_quality["deviation_gains"][row.target_player])
        )
        for row in affine_rows
    )
    affine_scope_identity = all(
        row.acting_player == parsed["acting_seat"]
        and row.changed_public_node == affine_rows[0].changed_public_node
        and row.changed_public_nodes == 1
        for row in affine_rows
    )
    fixed_rule_identity = (
        int(block["acting_seat"]) == parsed["acting_seat"]
        and all(
            information_key_public_coordinates(key)
            == (parsed["acting_seat"], block["public_history"])
            for key in payload["information_keys"]
        )
    )
    fail_closed_emission = (
        emitted_policy_sha256
        == (
            selected_validation["policy_sha256"]
            if candidate_live_eligible and selected_validation is not None
            else blueprint_digest
        )
    )

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
        "freshness_at_base_commit": freshness_at_base_commit,
        "source_checkpoint_identity": source_checkpoint_identity,
        "target_identity": target_identity,
        "blueprint_identity": blueprint_identity,
        "blueprint_policy_sha256": blueprint_digest,
        "blueprint_quality": blueprint_quality,
        "warm_start_distance": warm_start_distance,
        "search_step_ms": search_ms,
        "search_step_work_wall_ms": solver.last_step_work.wall_ms,
        "soft_candidate_policy_sha256": payload["soft_candidate_policy_sha256"],
        "block": {
            "acting_seat": int(block["acting_seat"]),
            "public_history": block["public_history"],
            "information_keys": list(payload["information_keys"]),
            "information_set_count": len(payload["information_keys"]),
            "all_block_count": payload["all_block_count"],
            "direction_policy_sha256": payload["direction_policy_sha256"],
            "construction_ms": construction_ms,
            "construction_live": construction_live,
            "affine_sweep_ms": affine_ms,
            "affine_live": affine_live,
            "affine_scope_identity": affine_scope_identity,
            "affine_intercept_error": affine_intercept_error,
            "affine_rows": [asdict(row) for row in affine_rows],
            "envelope": asdict(envelope),
            "fixed_validation": fixed_validation,
            "selected_validation": selected_validation,
            "selected_positive_certified_value": selected_value,
        },
        "live": {
            "fixed_rule_identity": fixed_rule_identity,
            "blueprint_preloaded": True,
            "teacher_influenced_selection": False,
            "emission_frozen_before_teacher": live_emission_frozen,
            "teacher_started_after_live_close": teacher_started_after_live_close,
            "post_step_start_allowed": post_step_start_allowed,
            "post_step_elapsed_ms": post_step_elapsed_ms,
            "post_construction_start_allowed": post_construction_start_allowed,
            "construction_started": construction_live,
            "affine_started": affine_live,
            "candidate_live_eligible": candidate_live_eligible,
            "candidate_ready_elapsed_ms": live_candidate_ready_elapsed_ms,
            "stop_reason": live_stop_reason,
            "work_closed_elapsed_ms": live_closed_elapsed_ms,
            "emission_reserve_ms": parsed["emission_reserve_ms"],
            "street_ledger_ms": live_ledger_ms,
            "hard_deadline_fit": live_hard_deadline_fit,
            "emitted_candidate_id": emitted_candidate_id,
            "emitted_policy_sha256": emitted_policy_sha256,
            "predicted_positive_certified_value": (
                envelope.positive_certified_value if candidate_live_eligible else 0.0
            ),
        },
        "fail_closed_emission": fail_closed_emission,
        "memory_rows": memory_rows,
    }
    del solver, context, shared, gpu, workspace, base, automata, source_workspace
    del sparse, layout, belief, source
    gc.collect()
    release_cupy_memory_pool()
    return result


def run_h32_fresh_selector_stable_affine_street_audit(
    config_path: Path = _CONFIG,
    output_path: Path = _OUTPUT,
) -> dict[str, Any]:
    """Execute ADR-0191's one-time fresh causal street trial."""

    started = time.perf_counter()
    parsed = parse_h32_fresh_selector_stable_affine_street_config(
        json.loads(config_path.read_text(encoding="utf-8"))
    )
    source_parent = json.loads(_SOURCE.read_text(encoding="utf-8"))
    affine_parent = json.loads(_PARENT_RESULT.read_text(encoding="utf-8"))
    git = _strict_git_metadata()
    cp, runtime = _validate_runtime(parsed)
    if git["dirty"]:
        raise RuntimeError("fresh affine-street execution requires clean Git state")
    if not source_parent["passed"] or not affine_parent["passed"]:
        raise ValueError("fresh affine-street parent did not pass")

    targets = []
    for target_spec in parsed["targets"]:
        print(f"fresh affine street: {target_spec['target']}", flush=True)
        targets.append(_run_target(parsed, source_parent, target_spec, cp))

    blocks = [target["block"] for target in targets]
    affine_rows = [row for block in blocks for row in block["affine_rows"]]
    fixed = [block["fixed_validation"] for block in blocks if block["fixed_validation"]]
    selected = [
        block["selected_validation"]
        for block in blocks
        if block["selected_validation"] is not None
    ]
    selected_errors = [row["errors"] for row in selected if row["errors"] is not None]
    direct_errors = [row["errors"] for row in fixed] + selected_errors
    maximum_direct_utility_error = max(
        (row["maximum_utility_error"] for row in direct_errors),
        default=None,
    )
    maximum_direct_best_response_error = max(
        (row["maximum_best_response_error"] for row in direct_errors),
        default=None,
    )
    maximum_direct_deviation_gain_error = max(
        (row["maximum_deviation_gain_error"] for row in direct_errors),
        default=None,
    )
    memory_rows = [row for target in targets for row in target["memory_rows"]]
    total_seconds = time.perf_counter() - started
    gates_config = parsed["gates"]
    finite_values = [
        total_seconds,
        *(target["search_step_ms"] for target in targets),
        *(block["construction_ms"] for block in blocks),
        *(block["affine_sweep_ms"] for block in blocks),
        *(target["live"]["street_ledger_ms"] for target in targets),
        *(value for row in direct_errors for value in row.values()),
    ]
    gates = {
        "clean_git": (not git["dirty"]) == gates_config["require_clean_git_state"],
        "parent_passed": (source_parent["passed"] and affine_parent["passed"])
        == gates_config["require_parent_passed"],
        "target_rows": len(targets) == gates_config["expected_target_rows"],
        "search_steps": len(targets) == gates_config["expected_search_steps"],
        "public_blocks": len(blocks) == gates_config["expected_public_blocks"],
        "affine_seat_rows": len(affine_rows)
        == gates_config["expected_affine_seat_rows"],
        "fixed_direct_validations": len(fixed)
        == gates_config["expected_fixed_direct_validations"],
        "freshness_at_base_commit": all(
            target["freshness_at_base_commit"] for target in targets
        )
        == gates_config["require_freshness_at_base_commit"],
        "source_checkpoint_identity": all(
            target["source_checkpoint_identity"] for target in targets
        )
        == gates_config["require_source_checkpoint_identity"],
        "target_identity": all(target["target_identity"] for target in targets)
        == gates_config["require_target_identity"],
        "blueprint_identity": all(target["blueprint_identity"] for target in targets)
        == gates_config["require_blueprint_identity"],
        "numerical_warm_start_identity": all(
            target["warm_start_distance"]["maximum_probability_error"]
            <= parsed["maximum_warm_start_probability_error"]
            and target["warm_start_distance"]["mean_total_variation"]
            <= parsed["maximum_warm_start_mean_total_variation"]
            for target in targets
        )
        == gates_config["require_numerical_warm_start_identity"],
        "nonempty_coherent_block": all(
            block["information_set_count"] > 0
            and block["acting_seat"] == parsed["acting_seat"]
            and block["all_block_count"] == parsed["players"]
            and all(
                information_key_public_coordinates(key)
                == (parsed["acting_seat"], block["public_history"])
                for key in block["information_keys"]
            )
            for block in blocks
        )
        == gates_config["require_nonempty_coherent_block"],
        "affine_scope_identity": all(block["affine_scope_identity"] for block in blocks)
        == gates_config["require_affine_scope_identity"],
        "affine_intercepts": max(block["affine_intercept_error"] for block in blocks)
        <= gates_config["maximum_affine_intercept_error"],
        "direct_utility": maximum_direct_utility_error is not None
        and maximum_direct_utility_error
        <= gates_config["maximum_direct_utility_error"],
        "direct_best_response": maximum_direct_best_response_error is not None
        and maximum_direct_best_response_error
        <= gates_config["maximum_direct_best_response_error"],
        "direct_deviation_gain": maximum_direct_deviation_gain_error is not None
        and maximum_direct_deviation_gain_error
        <= gates_config["maximum_direct_deviation_gain_error"],
        "fixed_inside_selector_interval": all(
            row["strictly_inside_selector_interval"] for row in fixed
        )
        == gates_config["require_fixed_validation_inside_selector_interval"],
        "fixed_zero_response_flips": all(
            row["direct_response_action_flips"] == 0 for row in fixed
        )
        == gates_config["require_fixed_validation_zero_response_flips"],
        "selected_direct_completion": all(
            row["direct"]["complete"] and row["direct"]["quality"] is not None
            for row in selected
        )
        == gates_config["require_selected_direct_completion"],
        "selected_zero_response_flips": all(
            row["direct"]["response_action_flips"] == 0 for row in selected
        )
        == gates_config["require_selected_zero_response_flips"],
        "causal_teacher_order": all(
            target["live"]["emission_frozen_before_teacher"]
            and target["live"]["teacher_started_after_live_close"]
            and not target["live"]["teacher_influenced_selection"]
            for target in targets
        )
        == gates_config["require_causal_teacher_order"],
        "fixed_rule_identity": all(
            target["live"]["fixed_rule_identity"] for target in targets
        )
        == gates_config["require_fixed_rule_identity"],
        "fail_closed_emission": all(
            target["fail_closed_emission"] for target in targets
        )
        == gates_config["require_fail_closed_emission"],
        "hard_deadline_fit": all(
            target["live"]["hard_deadline_fit"] for target in targets
        )
        == gates_config["require_hard_deadline_fit"],
        "search_step_ms": all(
            target["search_step_ms"] <= gates_config["maximum_search_step_ms"]
            for target in targets
        ),
        "construction_ms": all(
            block["construction_ms"] <= gates_config["maximum_construction_ms"]
            for block in blocks
        ),
        "affine_sweep_ms": all(
            block["affine_sweep_ms"] <= gates_config["maximum_affine_sweep_ms"]
            for block in blocks
        ),
        "direct_validation_ms": all(
            row["direct_wall_ms"] <= gates_config["maximum_direct_validation_ms"]
            for row in fixed
        )
        and all(
            row["direct"]["wall_ms"]
            <= gates_config["maximum_direct_validation_ms"]
            for row in selected
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
        "status": "fresh_h32_selector_stable_affine_street_audit_executed",
        "methodology": {
            "preregistered": True,
            "fresh_target_quality_labels": True,
            "fixed_acting_seat": parsed["acting_seat"],
            "fixed_direction_family": parsed["direction_family"],
            "no_opportunity_selector": True,
            "immutable_blueprint_anchor": True,
            "old_exact_teacher_after_live_close": True,
            "simulated_emission_only": True,
        },
        "config_sha256": _sha256(config_path),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "environment": {**environment_metadata(), **runtime, "git": git},
        "target_rows": targets,
        "aggregate": {
            "targets": len(targets),
            "live_construction_starts": sum(
                target["live"]["construction_started"] for target in targets
            ),
            "live_affine_starts": sum(
                target["live"]["affine_started"] for target in targets
            ),
            "live_non_blueprint_emissions": sum(
                target["live"]["candidate_live_eligible"] for target in targets
            ),
            "offline_affine_selections": len(selected),
            "live_predicted_positive_certified_value": math.fsum(
                target["live"]["predicted_positive_certified_value"]
                for target in targets
            ),
            "offline_exact_positive_certified_value": math.fsum(
                block["selected_positive_certified_value"] for block in blocks
            ),
            "maximum_live_street_ledger_ms": max(
                target["live"]["street_ledger_ms"] for target in targets
            ),
            "minimum_live_boundary_headroom_ms": min(
                parsed["street_budget_ms"] - target["live"]["street_ledger_ms"]
                for target in targets
            ),
            "maximum_affine_sweep_ms": max(
                block["affine_sweep_ms"] for block in blocks
            ),
            "maximum_direct_utility_error": maximum_direct_utility_error,
            "maximum_direct_best_response_error": (
                maximum_direct_best_response_error
            ),
            "maximum_direct_deviation_gain_error": (
                maximum_direct_deviation_gain_error
            ),
            "maximum_gpu_pool_bytes": max(
                row["gpu_pool_total_bytes"] for row in memory_rows
            ),
            "minimum_gpu_free_bytes": min(
                row["gpu_free_bytes"] for row in memory_rows
            ),
        },
        "gates": gates,
        "passed": gates["passed"],
        "decision": (
            "accept_four_context_fresh_affine_street_trial"
            if gates["passed"]
            else "reject_fresh_affine_street_trial"
        ),
        "total_audit_seconds": total_seconds,
        "strategy_population_claim": None,
        "limitations": [
            "Only four fresh seat-0 blocker shifts are measured.",
            "Emission is simulated and no external poker action is taken.",
            "The rule always chooses acting seat 0 and does not test a learned selector.",
            "Post-ledger exact teachers cannot influence live selection or emission.",
            "No latency distribution, deployment, composition, or population claim follows.",
        ],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
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
    result = run_h32_fresh_selector_stable_affine_street_audit(
        args.config,
        args.output,
    )
    print(
        json.dumps(
            {
                "output": str(args.output),
                "passed": result["passed"],
                "aggregate": result["aggregate"],
            },
            indent=2,
        )
    )
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
