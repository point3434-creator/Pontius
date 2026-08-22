"""Retrospective full-closure census for opened h32 one-seat contexts."""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict
import gc
import hashlib
import json
import math
from pathlib import Path
import time
from typing import Any, Mapping

import numpy as np

from .axis_cfr_checkpoint import axis_cfr_checkpoint_digest
from .behavioral_one_seat_master import (
    BehavioralOneSeatAxis,
    solve_behavioral_one_seat_master,
)
from .behavioral_open_axis import behavioral_open_axis_payoff_row
from .cross_payoff_leaf_adjoint import (
    evaluate_device_fold_cross_payoff_leaf_adjoint,
)
from .cupy_sparse_incidence import release_cupy_memory_pool
from .device_fold_resident_leaf_adjoint_cfr import (
    DeviceFoldResidentLeafAdjointPublicTreeCFR,
)
from .fresh_h32_strategy_transfer_audit import _belief_digest
from .h32_action_conditioned_posterior_manifest import _SOURCE_SPECS
from .h32_affine_resident_cache_preflight import (
    _strict_git_metadata,
    _validate_runtime,
)
from .h32_continuation_root_ledger import _setup as _wide_setup
from .h32_decision_aligned_continuation_setup import (
    build_decision_aligned_continuation_setup,
)
from .h32_fresh_convex_retreat_replication import (
    classify_resident_epigraph_violation,
)
from .h32_fresh_union_value_audit import _memory_snapshot
from .h32_one_round_convex_master import (
    _exact_oracle,
    _master_summary,
    bounded_gap,
)
from .h32_one_seat_open_axis_preflight import (
    _pass_telemetry,
    _response_signature,
    _run_pass,
)
from .h32_resident_record_to_hand_fold_differential import _work_ledger
from .h32_warm_search_acceptance_audit import _policy_distance
from .incremental_policy_tt import compile_policy_probability_tape
from .one_seat_convex_generation import compiled_layout_path_single_visit_report
from .payoff_semantics import payoff_span, raw_guard
from .real_policy import policy_digest
from .runner_harness import (
    artifact_passed,
    assemble_environment,
    finalize_gates,
    load_artifact,
    serialize_result,
)
from .sequence_form_open_axis import (
    SequenceFormAffineRow,
    affine_row_conditioning,
    constant_minus_affine_row,
    splice_fixed_response_probability_tape_for_axes,
    subtract_affine_rows,
)
from .shared_resident_response_context import (
    shared_device_numeric_bytes,
    unique_response_numeric_bytes,
)


_ROOT = Path(__file__).parents[2]
_CONFIG = _ROOT / "experiments/configs/h32-retained-convex-closure-census-v1.json"
_OUTPUT = _ROOT / "experiments/results/h32-retained-convex-closure-census-v1.json"
_SOURCE = _ROOT / "experiments/results/h32-fresh-panel-source-blueprints-v1.json"
_AB_MANIFEST = (
    _ROOT / "experiments/results/h32-action-conditioned-posterior-manifest-v1.json"
)
_CD_MANIFEST = (
    _ROOT
    / "experiments/results/h32-heldout-continuation-posterior-manifest-v1.json"
)
_EF_MANIFEST = (
    _ROOT / "experiments/results/h32-convex-replication-posterior-manifest-v1.json"
)
_CALL_MANIFEST = (
    _ROOT / "experiments/results/h32-decision-aligned-posterior-manifest-v1.json"
)
_AB_LABELS = (
    _ROOT / "experiments/results/h32-continuation-root-strategy-trial-v1.json"
)
_CD_LABELS = (
    _ROOT / "experiments/results/h32-heldout-continuation-depth-value-v1.json"
)
_E_LABELS = (
    _ROOT / "experiments/results/h32-fresh-convex-retreat-replication-v2.json"
)
_F_LABELS = (
    _ROOT / "experiments/results/h32-latin-f-convex-retreat-confirmation-v1.json"
)
_CALL_LABELS = (
    _ROOT / "experiments/results/h32-decision-aligned-live-shadow-v1.json"
)
_KEYSTONE = _ROOT / "experiments/results/h32-one-round-convex-master-v1.json"
_POST_FOLD = (
    _ROOT / "experiments/results/h32-post-fold-posterior-manifest-v1.json"
)
_DECISION = (
    _ROOT
    / "docs/decisions/ADR-0266-post-fold-panel-is-fresh-current-and-held-label-blind.md"
)
_IMPLEMENTATION = Path(__file__)
_TEST = _ROOT / "tests/test_h32_retained_convex_closure_census.py"

_MANIFEST_PATHS = {
    "latin_ab": _AB_MANIFEST,
    "latin_cd": _CD_MANIFEST,
    "latin_ef": _EF_MANIFEST,
    "post_call": _CALL_MANIFEST,
}
_LABEL_PATHS = {
    "latin_ab": (_AB_LABELS,),
    "latin_cd": (_CD_LABELS,),
    "latin_ef": (_E_LABELS, _F_LABELS),
    "post_call": (_CALL_LABELS,),
}
_PATHS = {
    "expected_source_result_sha256": _SOURCE,
    "expected_latin_ab_manifest_sha256": _AB_MANIFEST,
    "expected_latin_cd_manifest_sha256": _CD_MANIFEST,
    "expected_latin_ef_manifest_sha256": _EF_MANIFEST,
    "expected_post_call_manifest_sha256": _CALL_MANIFEST,
    "expected_latin_ab_labels_sha256": _AB_LABELS,
    "expected_latin_cd_labels_sha256": _CD_LABELS,
    "expected_latin_e_labels_sha256": _E_LABELS,
    "expected_latin_f_labels_sha256": _F_LABELS,
    "expected_post_call_labels_sha256": _CALL_LABELS,
    "expected_keystone_result_sha256": _KEYSTONE,
    "expected_post_fold_manifest_sha256": _POST_FOLD,
    "expected_parent_decision_sha256": _DECISION,
    "expected_master_sha256": _ROOT / "src/pontius/behavioral_one_seat_master.py",
    "expected_behavioral_row_sha256": _ROOT / "src/pontius/behavioral_open_axis.py",
    "expected_sequence_row_sha256": _ROOT / "src/pontius/sequence_form_open_axis.py",
    "expected_cross_payoff_sha256": _ROOT / "src/pontius/cross_payoff_leaf_adjoint.py",
    "expected_incremental_oracle_sha256": (
        _ROOT / "src/pontius/incremental_leaf_adjoint_response.py"
    ),
    "expected_payoff_semantics_sha256": _ROOT / "src/pontius/payoff_semantics.py",
    "expected_wide_setup_sha256": (
        _ROOT / "src/pontius/h32_continuation_root_ledger.py"
    ),
    "expected_current_setup_sha256": (
        _ROOT / "src/pontius/h32_decision_aligned_continuation_setup.py"
    ),
    "expected_one_round_core_sha256": (
        _ROOT / "src/pontius/h32_one_round_convex_master.py"
    ),
    "expected_preflight_implementation_sha256": (
        _ROOT / "src/pontius/h32_one_seat_open_axis_preflight.py"
    ),
    "expected_resident_classifier_sha256": (
        _ROOT / "src/pontius/h32_fresh_convex_retreat_replication.py"
    ),
    "expected_device_cfr_sha256": (
        _ROOT / "src/pontius/device_fold_resident_leaf_adjoint_cfr.py"
    ),
    "expected_runner_harness_sha256": _ROOT / "src/pontius/runner_harness.py",
    "expected_implementation_sha256": _IMPLEMENTATION,
    "expected_control_test_sha256": _TEST,
}


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required closure-census input is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json_digest(value: Any) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _row_target_ids(result: Mapping[str, Any]) -> set[str]:
    return {str(row["target_id"]) for row in result["target_rows"]}


def retained_opened_target_inventory() -> tuple[dict[str, Any], ...]:
    """Return every opened compatible identity in frozen parent order."""

    manifests = {name: _load_json(path) for name, path in _MANIFEST_PATHS.items()}
    labels = {
        name: tuple(_load_json(path) for path in paths)
        for name, paths in _LABEL_PATHS.items()
    }
    if not all(artifact_passed(row) for row in manifests.values()):
        raise ValueError("closure-census manifest parent failed")
    if not all(
        artifact_passed(row)
        for group in labels.values()
        for row in group
    ):
        raise ValueError("closure-census opened-label parent failed")

    source_specs = {
        source: {"board": list(board), "range_family": family}
        for source, board, family in _SOURCE_SPECS
    }
    inventory: list[dict[str, Any]] = []
    expected_rounds = {
        "latin_ab": {"latin_a", "latin_b"},
        "latin_cd": {"latin_c", "latin_d"},
        "latin_ef": {"latin_e", "latin_f"},
        "post_call": {"decision_aligned_call_v1"},
    }
    for panel, manifest in manifests.items():
        rows = manifest["target_rows"]
        label_ids = set().union(*(_row_target_ids(row) for row in labels[panel]))
        manifest_ids = {str(row["target_id"]) for row in rows}
        if label_ids != manifest_ids:
            raise ValueError(f"closure-census opened-label coverage differs: {panel}")
        if {str(row["round"]) for row in rows} != expected_rounds[panel]:
            raise ValueError(f"closure-census Latin round coverage differs: {panel}")
        for row in rows:
            bettor = int(row["observed_bettor"])
            if panel == "post_call":
                acting_player = int(row["acting_player"])
                setup_mode = "post_call_current_decision"
                expected_shape = {
                    "acting_public_nodes": 1,
                    "behavioral_information_sets": 32,
                    "policy_variables": 64,
                }
            else:
                acting_player = (bettor - 1) % 6
                if "acting_player" in row and int(row["acting_player"]) != acting_player:
                    raise ValueError("closure-census sealed wide actor differs")
                setup_mode = "checks_then_bet_wide_last_responder"
                expected_shape = {
                    "acting_public_nodes": 16,
                    "behavioral_information_sets": 512,
                    "policy_variables": 1024,
                }
            source = str(row["source"])
            spec = {
                "inventory_index": len(inventory),
                "panel": panel,
                "setup_mode": setup_mode,
                "target_id": str(row["target_id"]),
                "source": source,
                "observed_bettor": bettor,
                "acting_player": acting_player,
                "round": str(row["round"]),
                "source_belief_sha256": str(row["source_belief_sha256"]),
                "target_belief_sha256": str(row["target_belief_sha256"]),
                "target_descriptor_sha256": str(row["target_descriptor_sha256"]),
                **source_specs[source],
                **expected_shape,
            }
            if panel == "post_call":
                spec.update(
                    {
                        "observed_responder": int(row["observed_responder"]),
                        "observed_response": str(row["observed_response"]),
                        "public_prefix": [list(item) for item in row["public_prefix"]],
                    }
                )
            inventory.append(spec)

    ids = [row["target_id"] for row in inventory]
    digests = [row["target_belief_sha256"] for row in inventory]
    if len(inventory) != 42 or len(set(ids)) != 42 or len(set(digests)) != 42:
        raise ValueError("closure-census inventory is not 42 unique identities")
    for field in ("source", "observed_bettor", "acting_player"):
        if set(Counter(row[field] for row in inventory).values()) != {7}:
            raise ValueError(f"closure-census inventory is not balanced: {field}")

    post_fold = _load_json(_POST_FOLD)
    post_fold_ids = _row_target_ids(post_fold)
    post_fold_digests = {
        str(row["target_belief_sha256"]) for row in post_fold["target_rows"]
    }
    if set(ids) & post_fold_ids or set(digests) & post_fold_digests:
        raise ValueError("closure-census inventory leaks the held post-fold panel")
    return tuple(inventory)


def retained_inventory_sha256() -> str:
    return _json_digest(retained_opened_target_inventory())


def parse_h32_retained_convex_closure_census_config(
    config: dict[str, Any],
) -> dict[str, Any]:
    expected = {
        "evidence_stage",
        *_PATHS,
        "expected_inventory_sha256",
        "seed",
        "scope",
        "target_rule",
        "acting_axis_rule",
        "warm_step_rule",
        "master_rule",
        "oracle_rule",
        "cut_rule",
        "stopping_rule",
        "incumbent_rule",
        "decision_rule",
        "maximum_cut_rounds",
        "maximum_target_seconds",
        "maximum_total_seconds",
        "acceptance_guard_normalized",
        "lp_tolerance",
        "epigraph_separation_allowance",
        "cap_numerical_allowance",
        "resident_row_identity_allowance",
        "resident_epigraph_residual_allowance",
        "bound_tolerance",
        "candidate_projection_tolerance",
        "conditioning_tolerance",
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
        "maximum_feature_width_per_batch",
        "required_numpy_version",
        "required_scipy_version",
        "required_cupy_version",
        "required_cuda_runtime_version",
        "minimum_cuda_driver_version",
        "required_compute_capability",
        "cuda_dll_environment_variable",
        "label_policy",
        "gates",
    }
    if set(config) != expected:
        raise ValueError("closure-census config fields differ from ADR-0267")
    for field, path in _PATHS.items():
        if config[field] != _sha256(path):
            raise ValueError(f"closure-census provenance mismatch: {field}")
    if config["expected_inventory_sha256"] != retained_inventory_sha256():
        raise ValueError("closure-census inventory digest differs from ADR-0267")
    exact = {
        "evidence_stage": (
            "preregistered_after_adr0266_before_any_full_convergence_"
            "retrospective_oracle"
        ),
        "seed": 20260822,
        "scope": (
            "all_42_opened_compatible_h32_contexts_36_wide_last_responder_"
            "and_6_current_decision_post_call"
        ),
        "target_rule": (
            "all_rows_in_latin_ab_then_cd_then_ef_then_post_call_manifest_"
            "order_zero_value_timing_or_facet_selection_post_fold_excluded"
        ),
        "acting_axis_rule": (
            "wide_panels_use_last_responder_bettor_minus_one_mod_6_post_call_"
            "uses_sealed_current_actor"
        ),
        "warm_step_rule": (
            "exactly_one_frozen_resident_dcfr_step_retained_for_methodological_"
            "comparability_even_though_master_rows_remain_blueprint_conditioned"
        ),
        "master_rule": (
            "sparse_highs_dual_simplex_all_behavioral_simplex_rows_all_"
            "accumulated_exact_response_rows_no_deletion"
        ),
        "oracle_rule": (
            "one_exact_all_six_separation_oracle_per_master_candidate_no_"
            "seat_early_stop"
        ),
        "cut_rule": (
            "add_every_genuinely_new_epigraph_violating_opponent_response_in_"
            "one_multicut_round_resident_rows_classified_under_adr0257"
        ),
        "stopping_rule": (
            "iterate_to_no_new_facets_exact_cap_feasibility_and_verified_u_"
            "minus_l_gap_or_stop_at_frozen_round_or_target_time_cap"
        ),
        "incumbent_rule": (
            "minimum_exact_all_seat_objective_among_blueprint_and_exact_cap_"
            "feasible_master_candidates"
        ),
        "decision_rule": (
            "universal_one_round_closure_only_if_all_42_close_by_round_one_"
            "otherwise_retain_direction_fallback_and_report_distribution"
        ),
        "maximum_cut_rounds": 32,
        "maximum_target_seconds": 240.0,
        "maximum_total_seconds": 10800.0,
        "acceptance_guard_normalized": 1e-10,
        "lp_tolerance": 1e-10,
        "epigraph_separation_allowance": 1e-9,
        "cap_numerical_allowance": 2e-11,
        "resident_row_identity_allowance": 2e-11,
        "resident_epigraph_residual_allowance": 1e-8,
        "bound_tolerance": 1e-8,
        "candidate_projection_tolerance": 1e-10,
        "conditioning_tolerance": 1e-12,
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
        "maximum_feature_width_per_batch": 384,
        "required_numpy_version": "2.5.2",
        "required_scipy_version": "1.18.0",
        "required_cupy_version": "14.2.0",
        "required_cuda_runtime_version": 13020,
        "minimum_cuda_driver_version": 13000,
        "required_compute_capability": "120",
        "cuda_dll_environment_variable": "PONTIUS_CUDA_DLL_DIRECTORY",
        "label_policy": (
            "retrospective_optimizer_labels_allowed_only_on_opened_contexts_"
            "post_fold_labels_zero_immutable_blueprint_emission"
        ),
    }
    for field, expected_value in exact.items():
        if config[field] != expected_value:
            raise ValueError(f"closure-census field differs from ADR-0267: {field}")
    gates = {
        "expected_targets": 42,
        "expected_wide_targets": 36,
        "expected_current_targets": 6,
        "expected_targets_per_source": 7,
        "expected_targets_per_bettor": 7,
        "expected_targets_per_acting_player": 7,
        "expected_wide_acting_public_nodes": 16,
        "expected_wide_information_sets": 512,
        "expected_wide_policy_variables": 1024,
        "expected_current_acting_public_nodes": 1,
        "expected_current_information_sets": 32,
        "expected_current_policy_variables": 64,
        "expected_epigraph_variables": 6,
        "expected_initial_profile_passes": 6,
        "expected_initial_response_passes": 5,
        "expected_initial_gain_rows": 6,
        "maximum_initial_row_error": 2e-11,
        "maximum_cut_row_error": 2e-11,
        "maximum_profile_equivalence_error": 2e-11,
        "maximum_master_primal_error": 1e-8,
        "maximum_master_dual_error": 1e-8,
        "maximum_projection_error": 1e-8,
        "maximum_warm_start_probability_error": 1e-12,
        "maximum_warm_start_mean_total_variation": 1e-13,
        "maximum_raw_guard_error": 1e-18,
        "maximum_cold_setup_ms": 120000.0,
        "maximum_warm_step_ms": 60000.0,
        "maximum_initial_row_ms": 60000.0,
        "maximum_master_ms": 60000.0,
        "maximum_oracle_ms": 60000.0,
        "maximum_cut_row_ms": 60000.0,
        "maximum_gpu_pool_bytes": 12000000000,
        "minimum_physical_free_bytes": 1000000000,
        "maximum_keystone_replay_error": 2e-11,
        "require_clean_git_state": True,
        "require_parents_passed": True,
        "require_inventory_identity": True,
        "require_post_fold_excluded": True,
        "require_source_checkpoint_identity": True,
        "require_target_identity": True,
        "require_blueprint_identity": True,
        "require_warm_start_identity": True,
        "require_path_single_visit": True,
        "require_lower_bound_monotonicity": True,
        "require_exact_external_axis_coverage": True,
        "require_all_violators_accounted": True,
        "require_blueprint_emission": True,
        "require_retrospective_label_disclosure": True,
        "require_strategy_population_claim_null": True,
        "require_finite": True,
    }
    if config["gates"] != gates:
        raise ValueError("closure-census gates differ from ADR-0267")
    return {
        **config,
        "inventory": retained_opened_target_inventory(),
        "gates": gates,
    }


def _finite_tree(value: Any) -> bool:
    if value is None or isinstance(value, (str, bool, int)):
        return True
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, Mapping):
        return all(_finite_tree(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return all(_finite_tree(item) for item in value)
    return True


def _setup_target(
    parsed: Mapping[str, Any],
    source_parent: Mapping[str, Any],
    spec: Mapping[str, Any],
) -> dict[str, Any]:
    if spec["setup_mode"] == "checks_then_bet_wide_last_responder":
        return _wide_setup(parsed, source_parent, spec)
    if spec["setup_mode"] == "post_call_current_decision":
        return build_decision_aligned_continuation_setup(parsed, source_parent, spec)
    raise ValueError("closure-census setup mode is unknown")


def _oracle_summary(
    oracle: Mapping[str, Any],
    *,
    caps: tuple[float, ...],
    epigraph: tuple[float, ...],
    cap_allowance: float,
    epigraph_allowance: float,
) -> dict[str, Any]:
    cap_violations = tuple(
        gain - cap for gain, cap in zip(oracle["gains"], caps, strict=True)
    )
    epigraph_violations = tuple(
        gain - value
        for gain, value in zip(oracle["raw_gains"], epigraph, strict=True)
    )
    return {
        "policy_sha256": oracle["policy_sha256"],
        "objective": float(oracle["objective"]),
        "response_signature_sha256": list(oracle["response_signatures"]),
        "probability_compile_ms": float(oracle["probability_compile_ms"]),
        "wall_ms": float(oracle["wall_ms"]),
        "zero_sum_residual": float(oracle["zero_sum_residual"]),
        "response_action_flips": int(oracle["response_action_flips"]),
        "affected_terminal_contractions": int(
            oracle["affected_terminal_contractions"]
        ),
        "maximum_middle_rank": int(oracle["maximum_middle_rank"]),
        "maximum_gpu_pool_total_bytes": int(
            oracle["maximum_gpu_pool_total_bytes"]
        ),
        "seat_wall_ms": [float(value) for value in oracle["seat_wall_ms"]],
        "maximum_cap_violation": max(0.0, max(cap_violations)),
        "maximum_epigraph_violation": max(0.0, max(epigraph_violations)),
        "cap_feasible": max(cap_violations) <= cap_allowance,
        "active_cap_players": [
            player
            for player, (gain, cap) in enumerate(
                zip(oracle["gains"], caps, strict=True)
            )
            if cap - gain <= cap_allowance
        ],
        "epigraph_violating_players": [
            player
            for player, violation in enumerate(epigraph_violations)
            if violation > epigraph_allowance
        ],
        "cap_allowance": cap_allowance,
        "epigraph_allowance": epigraph_allowance,
    }


def _run_target(
    parsed: Mapping[str, Any],
    source_parent: Mapping[str, Any],
    spec: Mapping[str, Any],
    cp: Any,
) -> dict[str, Any]:
    target_started = time.perf_counter()
    cp.cuda.runtime.deviceSynchronize()
    setup_started = time.perf_counter()
    objects = _setup_target(parsed, source_parent, spec)
    cp.cuda.runtime.deviceSynchronize()
    cold_setup_ms = (time.perf_counter() - setup_started) * 1000.0
    layout = objects["layout"]
    belief = objects["belief"]
    blueprint = objects["blueprint"]
    context = objects["context"]
    shared = objects["shared"]
    acting_player = int(spec["acting_player"])

    solver = DeviceFoldResidentLeafAdjointPublicTreeCFR(
        layout,
        objects["workspace"],
        objects["sparse"],
        objects["automata"],
        str(parsed["solver_variant"]),
        belief_cache=context.belief_cache,
        automaton_caches=shared.automaton_caches,
        cupy_sparse=objects["gpu"],
        maximum_feature_width_per_batch=int(parsed["maximum_feature_width_per_batch"]),
        hands_by_player=belief.hands_by_player,
        record_to_hand_backend="gpu_cupy",
    )
    warm_mass = float(parsed["warm_regret_mass_payoff_fraction"]) * payoff_span(layout)
    solver.warm_start(blueprint, warm_mass)
    warm_distance = _policy_distance(blueprint, solver.current_strategy())
    release_cupy_memory_pool()
    memory_rows = [{"stage": "resident_source", **_memory_snapshot(cp)}]
    cp.cuda.runtime.deviceSynchronize()
    warm_started = time.perf_counter()
    solver.step()
    cp.cuda.runtime.deviceSynchronize()
    warm_step_ms = (time.perf_counter() - warm_started) * 1000.0
    if solver.last_step_work is None:
        raise AssertionError("closure-census warm step emitted no work ledger")
    warm_works = tuple(row.resident_work for row in solver.last_step_work.traversers)
    warm_work = {
        "wall_ms": warm_step_ms,
        "terminal_contraction_ms": solver.last_step_work.terminal_contraction_ms,
        **_work_ledger(warm_works),
    }
    memory_rows.append({"stage": "warm_step", **_memory_snapshot(cp)})

    source_probabilities = context.response_caches[0].source_probabilities
    profile_rows: dict[int, SequenceFormAffineRow] = {}
    row_libraries: list[dict[str, SequenceFormAffineRow]] = [
        {} for _ in range(layout.num_players)
    ]
    initial_pass_rows = []
    initial_row_errors = []
    external_axis_splices = 0
    cp.cuda.runtime.deviceSynchronize()
    initial_started = time.perf_counter()
    for payoff_player in range(layout.num_players):
        cache = context.response_caches[payoff_player]
        row, telemetry, _ = _run_pass(
            objects=objects,
            probabilities=source_probabilities,
            acting_player=acting_player,
            payoff_player=payoff_player,
            source_value=float(cache.source_evaluation.profile_utility),
            kind="profile",
            cp=cp,
            maximum_feature_width_per_batch=int(
                parsed["maximum_feature_width_per_batch"]
            ),
        )
        profile_rows[payoff_player] = row
        initial_pass_rows.append(telemetry)
        initial_row_errors.append(
            abs(row.value(source_probabilities) - cache.source_evaluation.profile_utility)
        )
    for payoff_player in range(layout.num_players):
        cache = context.response_caches[payoff_player]
        actions = cache.source_evaluation.best_response_actions
        signature = _response_signature(actions)
        if payoff_player == acting_player:
            gain = constant_minus_affine_row(
                cache.source_evaluation.best_response_value,
                profile_rows[payoff_player],
            )
        else:
            response_probabilities = splice_fixed_response_probability_tape_for_axes(
                layout,
                source_probabilities,
                actions,
                responding_player=payoff_player,
                hands_by_player=belief.hands_by_player,
            )
            external_axis_splices += 1
            response, telemetry, _ = _run_pass(
                objects=objects,
                probabilities=response_probabilities,
                acting_player=acting_player,
                payoff_player=payoff_player,
                source_value=float(cache.source_evaluation.best_response_value),
                kind="fixed_response",
                cp=cp,
                maximum_feature_width_per_batch=int(
                    parsed["maximum_feature_width_per_batch"]
                ),
            )
            initial_pass_rows.append(telemetry)
            gain = subtract_affine_rows(response, profile_rows[payoff_player])
        initial_row_errors.append(
            abs(
                gain.value(source_probabilities)
                - (
                    cache.source_evaluation.best_response_value
                    - cache.source_evaluation.profile_utility
                )
            )
        )
        row_libraries[payoff_player][signature] = gain
    cp.cuda.runtime.deviceSynchronize()
    initial_row_ms = (time.perf_counter() - initial_started) * 1000.0
    memory_rows.append({"stage": "initial_rows", **_memory_snapshot(cp)})

    axis = BehavioralOneSeatAxis.compile(
        layout,
        belief.hands_by_player,
        blueprint,
        acting_player=acting_player,
    )
    topology = compiled_layout_path_single_visit_report(layout)
    if not topology.passed:
        raise AssertionError("closure-census behavioral topology failed")
    guard = raw_guard(layout, float(parsed["acceptance_guard_normalized"]))
    source_gains = tuple(
        float(cache.source_evaluation.deviation_gain)
        for cache in context.response_caches
    )
    caps = tuple(gain + guard for gain in source_gains)
    incumbent_upper = math.fsum(source_gains)
    incumbent_source = "blueprint"
    incumbent_policy_sha256 = policy_digest(blueprint)
    incumbent_iteration = -1
    lower_bound = 0.0
    lower_bound_nondecreasing = True
    iterations = []
    cut_rounds = 0
    total_cut_rows = 0
    total_cut_extraction_ms = 0.0
    maximum_profile_error = 0.0
    maximum_cut_error = 0.0
    maximum_projection_error = 0.0
    maximum_master_primal = 0.0
    maximum_master_dual = 0.0
    maximum_resident_identity_error = 0.0
    maximum_resident_residual = 0.0
    converged = False
    stop_reason = "not_started"

    while True:
        master = solve_behavioral_one_seat_master(
            axis,
            tuple(tuple(rows.values()) for rows in row_libraries),
            caps,
            tolerance=float(parsed["lp_tolerance"]),
        )
        master_row = _master_summary(master)
        prior_lower = lower_bound
        lower_bound = max(lower_bound, float(master.lower_bound))
        allowance = float(parsed["bound_tolerance"]) * max(
            1.0,
            abs(prior_lower),
            abs(lower_bound),
        )
        lower_bound_nondecreasing &= lower_bound >= prior_lower - allowance
        maximum_master_primal = max(
            maximum_master_primal,
            float(master.maximum_equality_error),
            float(master.maximum_inequality_violation),
            float(master.maximum_bound_violation),
        )
        maximum_master_dual = max(
            maximum_master_dual,
            float(master.maximum_stationarity_error),
            float(master.maximum_complementarity_error),
            float(master.duality_gap),
        )
        policy, projection_error = axis.policy_from_variables(
            master.variables,
            blueprint,
            tolerance=float(parsed["candidate_projection_tolerance"]),
        )
        maximum_projection_error = max(maximum_projection_error, projection_error)
        oracle = _exact_oracle(
            objects=objects,
            policy=policy,
            cp=cp,
            maximum_feature_width_per_batch=int(
                parsed["maximum_feature_width_per_batch"]
            ),
        )
        oracle_row = _oracle_summary(
            oracle,
            caps=caps,
            epigraph=master.epigraph,
            cap_allowance=float(parsed["cap_numerical_allowance"]),
            epigraph_allowance=float(parsed["epigraph_separation_allowance"]),
        )
        profile_errors = [
            abs(
                profile_rows[player].value(oracle["probabilities"])
                - oracle["evaluations"][player].profile_utility
            )
            for player in range(layout.num_players)
        ]
        maximum_profile_error = max(maximum_profile_error, *profile_errors)
        if oracle_row["cap_feasible"] and oracle["objective"] < incumbent_upper:
            incumbent_upper = float(oracle["objective"])
            incumbent_source = f"master_iteration_{len(iterations)}"
            incumbent_policy_sha256 = str(oracle["policy_sha256"])
            incumbent_iteration = len(iterations)
        gap = bounded_gap(
            incumbent_upper,
            lower_bound,
            tolerance=float(parsed["bound_tolerance"]),
        )

        resident_rows = []
        new_players = []
        for player in oracle_row["epigraph_violating_players"]:
            classification = classify_resident_epigraph_violation(
                player=player,
                acting_player=acting_player,
                exact_response_signature=oracle["response_signatures"][player],
                resident_rows=row_libraries[player],
                realization=oracle["probabilities"],
                raw_gain_value=oracle["raw_gains"][player],
                epigraph_value=master.epigraph[player],
                maximum_row_identity_error=float(
                    parsed["resident_row_identity_allowance"]
                ),
                maximum_residual=float(
                    parsed["resident_epigraph_residual_allowance"]
                ),
            )
            if classification is None:
                new_players.append(player)
            else:
                resident_rows.append(classification)
                maximum_resident_identity_error = max(
                    maximum_resident_identity_error,
                    float(classification["row_identity_error"]),
                )
                maximum_resident_residual = max(
                    maximum_resident_residual,
                    float(classification["epigraph_residual"]),
                )

        cut_rows = []
        cp.cuda.runtime.deviceSynchronize()
        cuts_started = time.perf_counter()
        for player in new_players:
            if player == acting_player:
                raise ArithmeticError("closure-census acting invariant exposed a new row")
            signature = oracle["response_signatures"][player]
            actions = oracle["evaluations"][player].best_response_actions
            response_probabilities = splice_fixed_response_probability_tape_for_axes(
                layout,
                source_probabilities,
                actions,
                responding_player=player,
                hands_by_player=belief.hands_by_player,
            )
            external_axis_splices += 1
            cp.cuda.runtime.deviceSynchronize()
            pass_started = time.perf_counter()
            extracted = evaluate_device_fold_cross_payoff_leaf_adjoint(
                layout,
                objects["workspace"],
                objects["sparse"],
                response_probabilities,
                objects["automata"][player],
                acting_player=acting_player,
                payoff_player=player,
                belief_cache=context.belief_cache,
                automaton_cache=shared.automaton_caches[player],
                cupy_sparse=objects["gpu"],
                maximum_feature_width_per_batch=int(
                    parsed["maximum_feature_width_per_batch"]
                ),
                record_to_hand_backend="gpu_cupy",
            )
            cp.cuda.runtime.deviceSynchronize()
            pass_ms = (time.perf_counter() - pass_started) * 1000.0
            response = behavioral_open_axis_payoff_row(
                layout,
                oracle["probabilities"],
                extracted,
                acting_player=acting_player,
                source_value=float(
                    oracle["evaluations"][player].best_response_value
                ),
            )
            gain = subtract_affine_rows(response, profile_rows[player])
            identity_error = abs(
                gain.value(oracle["probabilities"])
                - oracle["raw_gains"][player]
            )
            maximum_cut_error = max(maximum_cut_error, identity_error)
            if signature in row_libraries[player]:
                raise ArithmeticError("closure-census attempted a duplicate cut")
            row_libraries[player][signature] = gain
            cut_rows.append(
                {
                    "target_player": player,
                    "response_signature_sha256": signature,
                    "candidate_row_identity_error": identity_error,
                    **_pass_telemetry(
                        kind="generated_response",
                        payoff_player=player,
                        wall_ms=pass_ms,
                        result=extracted,
                    ),
                }
            )
        cp.cuda.runtime.deviceSynchronize()
        cut_extraction_ms = (time.perf_counter() - cuts_started) * 1000.0
        total_cut_extraction_ms += cut_extraction_ms
        total_cut_rows += len(cut_rows)
        if cut_rows:
            cut_rounds += 1
        memory_row = {
            "stage": f"iteration_{len(iterations)}",
            **_memory_snapshot(cp),
        }
        memory_rows.append(memory_row)
        elapsed_seconds = time.perf_counter() - target_started
        iteration = {
            "iteration": len(iterations),
            "master": master_row,
            "candidate_projection_error": projection_error,
            "oracle": oracle_row,
            "profile_equivalence_error": max(profile_errors),
            "resident_response_residual_rows": resident_rows,
            "new_violating_players": list(new_players),
            "cut_rows": cut_rows,
            "cut_extraction_ms": cut_extraction_ms,
            "cut_rounds_completed": cut_rounds,
            "row_counts_by_player": [len(rows) for rows in row_libraries],
            "lower_bound": lower_bound,
            "incumbent_upper_bound": incumbent_upper,
            "optimality_gap": gap,
            "incumbent_source": incumbent_source,
            "elapsed_seconds": elapsed_seconds,
            "memory": memory_row,
        }
        iterations.append(iteration)

        no_new_facets = not cut_rows
        converged = bool(
            no_new_facets
            and oracle_row["cap_feasible"]
            and gap <= float(parsed["bound_tolerance"])
        )
        if converged:
            stop_reason = "verified_epigraph_cap_and_bound_closure"
            break
        if no_new_facets:
            stop_reason = "no_new_facet_without_cap_or_bound_closure"
            break
        if cut_rounds >= int(parsed["maximum_cut_rounds"]):
            stop_reason = "maximum_cut_rounds_reached"
            break
        if elapsed_seconds >= float(parsed["maximum_target_seconds"]):
            stop_reason = "maximum_target_seconds_reached"
            break

    conditioning = [
        asdict(
            affine_row_conditioning(
                tuple(rows.values()),
                tolerance=float(parsed["conditioning_tolerance"]),
            )
        )
        for rows in row_libraries
    ]
    total_seconds = time.perf_counter() - target_started
    exact_external_axis_coverage = external_axis_splices == (
        layout.num_players - 1 + total_cut_rows
    )
    maximum_pool = max(
        *(int(row["gpu_pool_total_bytes"]) for row in memory_rows),
        *(int(row["maximum_gpu_pool_total_bytes"]) for row in initial_pass_rows),
        *(
            int(iteration["oracle"]["maximum_gpu_pool_total_bytes"])
            for iteration in iterations
        ),
        *(
            int(row["maximum_gpu_pool_total_bytes"])
            for iteration in iterations
            for row in iteration["cut_rows"]
        ),
    )
    minimum_free = min(int(row["gpu_free_bytes"]) for row in memory_rows)
    source_checkpoint_identity = (
        axis_cfr_checkpoint_digest(objects["state"])
        == objects["state"]["state_sha256"]
        and _belief_digest(objects["source"]) == spec["source_belief_sha256"]
    )
    target_identity = _belief_digest(belief) == spec["target_belief_sha256"]
    blueprint_identity = (
        policy_digest(objects["full_blueprint"])
        == objects["state"]["average_policy_sha256"]
    )
    result = {
        **dict(spec),
        "cold_setup_ms": cold_setup_ms,
        "warm_step": warm_work,
        "warm_start_distance": warm_distance,
        "warm_step_candidate_consumed_by_master": False,
        "acting_public_nodes_measured": len(axis.acting_nodes),
        "behavioral_information_sets_measured": len(axis.information_sets),
        "policy_variables_measured": axis.variable_count,
        "epigraph_variables": layout.num_players,
        "path_single_visit": topology.passed,
        "payoff_span": payoff_span(layout),
        "payoff_span_source": "layout.game.payoff_span",
        "raw_guard": guard,
        "source_nash_conv": math.fsum(source_gains),
        "caps_sha256": hashlib.sha256(
            np.asarray(caps, dtype=np.float64).tobytes(order="C")
        ).hexdigest(),
        "initial_profile_passes": sum(
            row["kind"] == "profile" for row in initial_pass_rows
        ),
        "initial_response_passes": sum(
            row["kind"] == "fixed_response" for row in initial_pass_rows
        ),
        "initial_gain_rows": layout.num_players,
        "initial_row_ms": initial_row_ms,
        "maximum_initial_row_error": max(initial_row_errors),
        "iterations": iterations,
        "masters_solved": len(iterations),
        "exact_oracles_executed": len(iterations),
        "cut_rounds": cut_rounds,
        "total_cut_rows": total_cut_rows,
        "total_cut_extraction_ms": total_cut_extraction_ms,
        "row_counts_by_player": [len(rows) for rows in row_libraries],
        "conditioning_by_player": conditioning,
        "lower_bound": lower_bound,
        "lower_bound_nondecreasing": lower_bound_nondecreasing,
        "incumbent_upper_bound": incumbent_upper,
        "optimality_gap": bounded_gap(
            incumbent_upper,
            lower_bound,
            tolerance=float(parsed["bound_tolerance"]),
        ),
        "incumbent_source": incumbent_source,
        "incumbent_iteration": incumbent_iteration,
        "incumbent_policy_sha256": incumbent_policy_sha256,
        "converged": converged,
        "rounds_to_closure": cut_rounds if converged else None,
        "stop_reason": stop_reason,
        "maximum_cut_row_error": maximum_cut_error,
        "maximum_profile_equivalence_error": maximum_profile_error,
        "maximum_projection_error": maximum_projection_error,
        "maximum_master_primal_error": maximum_master_primal,
        "maximum_master_dual_error": maximum_master_dual,
        "maximum_resident_row_identity_error": maximum_resident_identity_error,
        "maximum_resident_epigraph_residual": maximum_resident_residual,
        "exact_external_axis_coverage": exact_external_axis_coverage,
        "external_axis_splices": external_axis_splices,
        "all_violators_accounted": all(
            set(iteration["oracle"]["epigraph_violating_players"])
            == set(iteration["new_violating_players"])
            | {
                row["target_player"]
                for row in iteration["resident_response_residual_rows"]
            }
            for iteration in iterations
        ),
        "source_checkpoint_identity": source_checkpoint_identity,
        "target_identity": target_identity,
        "blueprint_identity": blueprint_identity,
        "restricted_blueprint_policy_sha256": policy_digest(blueprint),
        "actual_emitted_policy_sha256": policy_digest(blueprint),
        "candidate_policies_emitted": 0,
        "retrospective_optimizer_labels_generated": len(iterations),
        "fresh_post_fold_strategy_labels_generated": 0,
        "resident_numeric_bytes": {
            "shared_device": shared_device_numeric_bytes(shared, (context,)),
            "unique_response_host": unique_response_numeric_bytes((context,)),
            "solver": solver.memory_summary(),
        },
        "maximum_gpu_pool_total_bytes": maximum_pool,
        "minimum_gpu_free_bytes": minimum_free,
        "total_seconds": total_seconds,
    }
    del solver
    objects.clear()
    gc.collect()
    release_cupy_memory_pool()
    return result


def _keystone_replay_error(
    target_rows: list[Mapping[str, Any]],
    keystone: Mapping[str, Any],
) -> dict[str, Any]:
    teacher = keystone["target"]
    row = next(item for item in target_rows if item["target_id"] == teacher["target_id"])
    comparisons = {
        "initial_lower_bound": abs(
            float(row["iterations"][0]["lower_bound"])
            - float(teacher["masters"][0]["lower_bound"])
        ),
        "first_oracle_objective": abs(
            float(row["iterations"][0]["oracle"]["objective"])
            - float(teacher["first_oracle"]["objective"])
        ),
        "final_lower_bound": abs(float(row["lower_bound"]) - float(teacher["lower_bound"])),
        "final_upper_bound": abs(
            float(row["incumbent_upper_bound"])
            - float(teacher["incumbent_upper_bound"])
        ),
        "final_gap": abs(float(row["optimality_gap"]) - float(teacher["optimality_gap"])),
    }
    return {
        "target_id": row["target_id"],
        "census_cut_rounds": row["cut_rounds"],
        "teacher_cut_rounds": teacher["cut_rounds"],
        "census_first_cut_players": row["iterations"][0]["new_violating_players"],
        "teacher_first_cut_players": [
            item["target_player"] for item in teacher["cut_rows"]
        ],
        "absolute_errors": comparisons,
        "maximum_absolute_error": max(comparisons.values()),
        "discrete_identity": (
            row["cut_rounds"] == teacher["cut_rounds"]
            and row["iterations"][0]["new_violating_players"]
            == [item["target_player"] for item in teacher["cut_rows"]]
        ),
    }


def run_h32_retained_convex_closure_census(
    config_path: Path = _CONFIG,
    output_path: Path = _OUTPUT,
) -> dict[str, Any]:
    started = time.perf_counter()
    parsed = parse_h32_retained_convex_closure_census_config(
        json.loads(config_path.read_text(encoding="utf-8"))
    )
    git = _strict_git_metadata()
    if git["dirty"]:
        raise RuntimeError("closure census requires a clean Git state")
    cp, runtime = _validate_runtime(parsed)
    source_parent = load_artifact(
        _SOURCE,
        expected_sha256=parsed["expected_source_result_sha256"],
        require_passed=True,
    ).payload
    parents = [
        load_artifact(path, expected_sha256=parsed[field], require_passed=True).payload
        for field, path in (
            ("expected_latin_ab_manifest_sha256", _AB_MANIFEST),
            ("expected_latin_cd_manifest_sha256", _CD_MANIFEST),
            ("expected_latin_ef_manifest_sha256", _EF_MANIFEST),
            ("expected_post_call_manifest_sha256", _CALL_MANIFEST),
            ("expected_latin_ab_labels_sha256", _AB_LABELS),
            ("expected_latin_cd_labels_sha256", _CD_LABELS),
            ("expected_latin_e_labels_sha256", _E_LABELS),
            ("expected_latin_f_labels_sha256", _F_LABELS),
            ("expected_post_call_labels_sha256", _CALL_LABELS),
            ("expected_keystone_result_sha256", _KEYSTONE),
            ("expected_post_fold_manifest_sha256", _POST_FOLD),
        )
    ]
    keystone = parents[-2]
    target_rows = []
    for spec in parsed["inventory"]:
        if time.perf_counter() - started >= float(parsed["maximum_total_seconds"]):
            raise RuntimeError("closure-census total resource cap reached before target")
        target_row = _run_target(parsed, source_parent, spec, cp)
        target_rows.append(target_row)
        print(
            json.dumps(
                {
                    "completed_target": len(target_rows),
                    "total_targets": len(parsed["inventory"]),
                    "target_id": target_row["target_id"],
                    "converged": target_row["converged"],
                    "rounds_to_closure": target_row["rounds_to_closure"],
                    "stop_reason": target_row["stop_reason"],
                    "target_seconds": target_row["total_seconds"],
                },
                sort_keys=True,
            ),
            flush=True,
        )

    total_seconds = time.perf_counter() - started
    keystone_replay = _keystone_replay_error(target_rows, keystone)
    gate = parsed["gates"]
    panel_counts = Counter(row["panel"] for row in target_rows)
    source_counts = Counter(row["source"] for row in target_rows)
    bettor_counts = Counter(int(row["observed_bettor"]) for row in target_rows)
    actor_counts = Counter(int(row["acting_player"]) for row in target_rows)
    wide_rows = [
        row
        for row in target_rows
        if row["setup_mode"] == "checks_then_bet_wide_last_responder"
    ]
    current_rows = [
        row
        for row in target_rows
        if row["setup_mode"] == "post_call_current_decision"
    ]
    all_iterations = [
        iteration for row in target_rows for iteration in row["iterations"]
    ]
    all_cut_rows = [
        cut for iteration in all_iterations for cut in iteration["cut_rows"]
    ]
    checks = {
        "clean_git": (not git["dirty"]) == gate["require_clean_git_state"],
        "parents_passed": all(artifact_passed(row) for row in parents)
        == gate["require_parents_passed"],
        "inventory_identity": (
            retained_inventory_sha256() == parsed["expected_inventory_sha256"]
        )
        == gate["require_inventory_identity"],
        "post_fold_excluded": all(
            row["panel"] != "post_fold" for row in target_rows
        )
        == gate["require_post_fold_excluded"],
        "target_count": len(target_rows) == gate["expected_targets"],
        "mode_counts": (
            len(wide_rows) == gate["expected_wide_targets"]
            and len(current_rows) == gate["expected_current_targets"]
        ),
        "panel_counts": panel_counts
        == Counter({"latin_ab": 12, "latin_cd": 12, "latin_ef": 12, "post_call": 6}),
        "source_balance": set(source_counts.values())
        == {gate["expected_targets_per_source"]},
        "bettor_balance": set(bettor_counts.values())
        == {gate["expected_targets_per_bettor"]},
        "acting_player_balance": set(actor_counts.values())
        == {gate["expected_targets_per_acting_player"]},
        "source_checkpoint_identity": all(
            row["source_checkpoint_identity"] for row in target_rows
        )
        == gate["require_source_checkpoint_identity"],
        "target_identity": all(row["target_identity"] for row in target_rows)
        == gate["require_target_identity"],
        "blueprint_identity": all(row["blueprint_identity"] for row in target_rows)
        == gate["require_blueprint_identity"],
        "warm_start_identity": all(
            row["warm_start_distance"]["maximum_probability_error"]
            <= gate["maximum_warm_start_probability_error"]
            and row["warm_start_distance"]["mean_total_variation"]
            <= gate["maximum_warm_start_mean_total_variation"]
            for row in target_rows
        )
        == gate["require_warm_start_identity"],
        "path_single_visit": all(row["path_single_visit"] for row in target_rows)
        == gate["require_path_single_visit"],
        "wide_axis_shape": all(
            row["acting_public_nodes_measured"]
            == gate["expected_wide_acting_public_nodes"]
            and row["behavioral_information_sets_measured"]
            == gate["expected_wide_information_sets"]
            and row["policy_variables_measured"]
            == gate["expected_wide_policy_variables"]
            for row in wide_rows
        ),
        "current_axis_shape": all(
            row["acting_public_nodes_measured"]
            == gate["expected_current_acting_public_nodes"]
            and row["behavioral_information_sets_measured"]
            == gate["expected_current_information_sets"]
            and row["policy_variables_measured"]
            == gate["expected_current_policy_variables"]
            for row in current_rows
        ),
        "epigraph_shape": all(
            row["epigraph_variables"] == gate["expected_epigraph_variables"]
            for row in target_rows
        ),
        "initial_pass_counts": all(
            row["initial_profile_passes"] == gate["expected_initial_profile_passes"]
            and row["initial_response_passes"]
            == gate["expected_initial_response_passes"]
            and row["initial_gain_rows"] == gate["expected_initial_gain_rows"]
            for row in target_rows
        ),
        "initial_row_identity": max(
            row["maximum_initial_row_error"] for row in target_rows
        )
        <= gate["maximum_initial_row_error"],
        "cut_row_identity": max(
            (row["maximum_cut_row_error"] for row in target_rows),
            default=0.0,
        )
        <= gate["maximum_cut_row_error"],
        "profile_equivalence": max(
            row["maximum_profile_equivalence_error"] for row in target_rows
        )
        <= gate["maximum_profile_equivalence_error"],
        "master_primal": max(
            row["maximum_master_primal_error"] for row in target_rows
        )
        <= gate["maximum_master_primal_error"],
        "master_dual": max(
            row["maximum_master_dual_error"] for row in target_rows
        )
        <= gate["maximum_master_dual_error"],
        "projection": max(row["maximum_projection_error"] for row in target_rows)
        <= gate["maximum_projection_error"],
        "raw_guard": max(abs(row["raw_guard"] - 3e-9) for row in target_rows)
        <= gate["maximum_raw_guard_error"],
        "lower_bound_monotonicity": all(
            row["lower_bound_nondecreasing"] for row in target_rows
        )
        == gate["require_lower_bound_monotonicity"],
        "external_axis_coverage": all(
            row["exact_external_axis_coverage"] for row in target_rows
        )
        == gate["require_exact_external_axis_coverage"],
        "all_violators_accounted": all(
            row["all_violators_accounted"] for row in target_rows
        )
        == gate["require_all_violators_accounted"],
        "cold_setup_time": max(row["cold_setup_ms"] for row in target_rows)
        <= gate["maximum_cold_setup_ms"],
        "warm_step_time": max(row["warm_step"]["wall_ms"] for row in target_rows)
        <= gate["maximum_warm_step_ms"],
        "initial_row_time": max(row["initial_row_ms"] for row in target_rows)
        <= gate["maximum_initial_row_ms"],
        "master_time": max(
            iteration["master"]["solve_ms"] for iteration in all_iterations
        )
        <= gate["maximum_master_ms"],
        "oracle_time": max(
            iteration["oracle"]["wall_ms"] for iteration in all_iterations
        )
        <= gate["maximum_oracle_ms"],
        "cut_row_time": max(
            (row["wall_ms"] for row in all_cut_rows),
            default=0.0,
        )
        <= gate["maximum_cut_row_ms"],
        "target_resource_caps": all(
            row["total_seconds"] <= float(parsed["maximum_target_seconds"])
            + gate["maximum_oracle_ms"] / 1000.0
            for row in target_rows
        ),
        "total_time": total_seconds <= float(parsed["maximum_total_seconds"]),
        "gpu_pool": max(
            row["maximum_gpu_pool_total_bytes"] for row in target_rows
        )
        <= gate["maximum_gpu_pool_bytes"],
        "physical_free": min(row["minimum_gpu_free_bytes"] for row in target_rows)
        >= gate["minimum_physical_free_bytes"],
        "keystone_replay": (
            keystone_replay["discrete_identity"]
            and keystone_replay["maximum_absolute_error"]
            <= gate["maximum_keystone_replay_error"]
        ),
        "blueprint_emission": all(
            row["actual_emitted_policy_sha256"]
            == row["restricted_blueprint_policy_sha256"]
            and row["candidate_policies_emitted"] == 0
            for row in target_rows
        )
        == gate["require_blueprint_emission"],
        "retrospective_label_disclosure": all(
            row["retrospective_optimizer_labels_generated"]
            == row["exact_oracles_executed"]
            and row["fresh_post_fold_strategy_labels_generated"] == 0
            for row in target_rows
        )
        == gate["require_retrospective_label_disclosure"],
        "strategy_population_claim_null": True
        == gate["require_strategy_population_claim_null"],
        "finite": _finite_tree(target_rows) == gate["require_finite"],
    }
    gate_result = finalize_gates(checks)
    converged_rows = [row for row in target_rows if row["converged"]]
    one_round_rows = [
        row
        for row in converged_rows
        if int(row["rounds_to_closure"]) <= 1
    ]
    round_histogram = Counter(
        str(row["rounds_to_closure"])
        if row["rounds_to_closure"] is not None
        else f"censored:{row['stop_reason']}"
        for row in target_rows
    )
    universal_full_closure = len(converged_rows) == len(target_rows)
    universal_one_round = len(one_round_rows) == len(target_rows)
    result = {
        "schema_version": 1,
        "status": "h32_retained_convex_closure_census_executed",
        "environment": assemble_environment(runtime=runtime, git=git),
        "config_sha256": _sha256(config_path),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "inventory_sha256": retained_inventory_sha256(),
        "methodology": {
            "targets": len(target_rows),
            "wide_targets": len(wide_rows),
            "current_decision_targets": len(current_rows),
            "warm_steps": len(target_rows),
            "master_solves": sum(row["masters_solved"] for row in target_rows),
            "exact_all_seat_oracles": sum(
                row["exact_oracles_executed"] for row in target_rows
            ),
            "retrospective_optimizer_labels": sum(
                row["retrospective_optimizer_labels_generated"]
                for row in target_rows
            ),
            "fresh_post_fold_strategy_labels": 0,
            "candidate_policies_emitted": 0,
        },
        "target_rows": target_rows,
        "keystone_replay": keystone_replay,
        "aggregate": {
            "panel_counts": dict(sorted(panel_counts.items())),
            "source_counts": dict(sorted(source_counts.items())),
            "bettor_counts": {
                str(key): value for key, value in sorted(bettor_counts.items())
            },
            "acting_player_counts": {
                str(key): value for key, value in sorted(actor_counts.items())
            },
            "converged_targets": len(converged_rows),
            "one_round_closed_targets": len(one_round_rows),
            "rounds_to_closure_histogram": dict(sorted(round_histogram.items())),
            "universal_full_closure": universal_full_closure,
            "universal_one_round_closure": universal_one_round,
            "total_cut_rounds": sum(row["cut_rounds"] for row in target_rows),
            "total_new_response_rows": sum(
                row["total_cut_rows"] for row in target_rows
            ),
            "maximum_rounds_to_closure": max(
                (
                    int(row["rounds_to_closure"])
                    for row in converged_rows
                ),
                default=None,
            ),
            "maximum_optimality_gap": max(
                row["optimality_gap"] for row in target_rows
            ),
            "maximum_target_seconds": max(
                row["total_seconds"] for row in target_rows
            ),
            "maximum_gpu_pool_total_bytes": max(
                row["maximum_gpu_pool_total_bytes"] for row in target_rows
            ),
            "minimum_gpu_free_bytes": min(
                row["minimum_gpu_free_bytes"] for row in target_rows
            ),
        },
        **gate_result,
        "decision": (
            "retained_corpus_supports_universal_one_round_global_closure_"
            "authorize_fresh_confirmation"
            if gate_result["passed"] and universal_one_round
            else "full_closure_teacher_succeeds_but_one_round_is_not_universal_"
            "retain_live_direction_fallback"
            if gate_result["passed"] and universal_full_closure
            else "closure_census_is_censored_or_stalled_retain_live_direction_"
            "fallback"
            if gate_result["passed"]
            else "reject_retained_convex_closure_census_execution"
        ),
        "actual_emitted_policy": "immutable_restricted_blueprint_only",
        "strategy_population_claim": None,
        "total_seconds": total_seconds,
        "limitations": [
            (
                "All contexts already had strategy evidence open; this is "
                "retrospective optimization labeling, not fresh confirmation."
            ),
            (
                "The fixed 42-context corpus is balanced but not IID and does "
                "not estimate a deployment closure rate."
            ),
            (
                "The warm step is retained for methodological comparability "
                "even though the convex master remains blueprint-conditioned."
            ),
            "No seat-early-stop or response-tape warm-start optimization is introduced.",
            "The six sealed post-fold identities remain strategy-label blind.",
            (
                "No candidate is emitted and no deployment, composition, "
                "cross-street, global multiplayer, exploitation, or "
                "poker-strength claim is made."
            ),
        ],
    }
    output_path.write_text(serialize_result(result), encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=_CONFIG)
    parser.add_argument("--output", type=Path, default=_OUTPUT)
    args = parser.parse_args()
    result = run_h32_retained_convex_closure_census(args.config, args.output)
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
