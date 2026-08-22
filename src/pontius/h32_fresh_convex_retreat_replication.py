"""Fresh six-target replication of the one-seat convex half-retreat."""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
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
from .cross_payoff_leaf_adjoint import evaluate_device_fold_cross_payoff_leaf_adjoint
from .cupy_sparse_incidence import release_cupy_memory_pool
from .device_fold_resident_leaf_adjoint_cfr import (
    DeviceFoldResidentLeafAdjointPublicTreeCFR,
)
from .exact_oracle_assessment import assess_exact_oracle_gains
from .fresh_h32_strategy_transfer_audit import _belief_digest
from .h32_affine_resident_cache_preflight import _strict_git_metadata, _validate_runtime
from .h32_continuation_root_ledger import _setup
from .h32_fresh_union_value_audit import _memory_snapshot
from .h32_one_round_convex_master import (
    _exact_oracle,
    _finite_tree,
    _master_summary,
    _mix_policy,
)
from .h32_one_seat_open_axis_preflight import (
    _pass_telemetry,
    _response_signature,
    _run_pass,
)
from .h32_resident_record_to_hand_fold_differential import _work_ledger
from .h32_warm_search_acceptance_audit import _policy_distance
from .one_seat_convex_generation import compiled_layout_path_single_visit_report
from .payoff_semantics import normalized_quality, payoff_span, raw_guard
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
    constant_minus_affine_row,
    splice_fixed_response_probability_tape_for_axes,
    subtract_affine_rows,
)
from .shared_resident_response_context import (
    shared_device_numeric_bytes,
    unique_response_numeric_bytes,
)


_ROOT = Path(__file__).parents[2]
_CONFIG = _ROOT / "experiments/configs/h32-fresh-convex-retreat-replication-v1.json"
_OUTPUT = _ROOT / "experiments/results/h32-fresh-convex-retreat-replication-v1.json"
_SOURCE = _ROOT / "experiments/results/h32-fresh-panel-source-blueprints-v1.json"
_MANIFEST = (
    _ROOT / "experiments/results/h32-convex-replication-posterior-manifest-v1.json"
)
_MANIFEST_CONFIG = (
    _ROOT / "experiments/configs/h32-convex-replication-posterior-manifest-v1.json"
)
_MANIFEST_DECISION = (
    _ROOT / "docs/decisions/ADR-0254-final-latin-posterior-panel-is-fresh-and-balanced.md"
)
_KNOWN_RESULT = _ROOT / "experiments/results/h32-one-seat-retreat-quality-v2.json"
_KNOWN_DECISION = (
    _ROOT
    / "docs/decisions/ADR-0252-convex-retreat-beats-the-live-fallback-on-the-frozen-target.md"
)
_IMPLEMENTATION = Path(__file__)
_TEST = _ROOT / "tests/test_h32_fresh_convex_retreat_replication.py"

_PATHS = {
    "expected_source_result_sha256": _SOURCE,
    "expected_manifest_result_sha256": _MANIFEST,
    "expected_manifest_config_sha256": _MANIFEST_CONFIG,
    "expected_manifest_decision_sha256": _MANIFEST_DECISION,
    "expected_known_result_sha256": _KNOWN_RESULT,
    "expected_known_decision_sha256": _KNOWN_DECISION,
    "expected_master_sha256": _ROOT / "src/pontius/behavioral_one_seat_master.py",
    "expected_behavioral_row_sha256": _ROOT / "src/pontius/behavioral_open_axis.py",
    "expected_sequence_row_sha256": _ROOT / "src/pontius/sequence_form_open_axis.py",
    "expected_cross_payoff_sha256": _ROOT / "src/pontius/cross_payoff_leaf_adjoint.py",
    "expected_incremental_oracle_sha256": (
        _ROOT / "src/pontius/incremental_leaf_adjoint_response.py"
    ),
    "expected_assessment_sha256": _ROOT / "src/pontius/exact_oracle_assessment.py",
    "expected_payoff_semantics_sha256": _ROOT / "src/pontius/payoff_semantics.py",
    "expected_setup_sha256": _ROOT / "src/pontius/h32_continuation_root_ledger.py",
    "expected_device_cfr_sha256": (
        _ROOT / "src/pontius/device_fold_resident_leaf_adjoint_cfr.py"
    ),
    "expected_preflight_implementation_sha256": (
        _ROOT / "src/pontius/h32_one_seat_open_axis_preflight.py"
    ),
    "expected_exact_oracle_implementation_sha256": (
        _ROOT / "src/pontius/h32_one_round_convex_master.py"
    ),
    "expected_runner_harness_sha256": _ROOT / "src/pontius/runner_harness.py",
    "expected_implementation_sha256": _IMPLEMENTATION,
    "expected_control_test_sha256": _TEST,
}


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required fresh convex input is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


@dataclass(slots=True)
class FreshCandidateBarrier:
    """Require a complete algorithmic candidate before its retreat label."""

    target_id: str
    phase: str = "inputs_pinned"
    events: list[str] = field(default_factory=lambda: ["inputs_pinned"])
    prelabel_checks: dict[str, bool] = field(default_factory=dict)

    def freeze_candidate(self, checks: Mapping[str, bool]) -> None:
        if self.phase != "inputs_pinned":
            raise RuntimeError("fresh convex candidate can be frozen only once")
        if not checks or any(type(value) is not bool for value in checks.values()):
            raise ValueError("fresh convex prelabel checks must be Boolean")
        if not all(checks.values()):
            failed = sorted(key for key, value in checks.items() if not value)
            raise RuntimeError(
                f"fresh convex candidate changed before label: {self.target_id}: {failed}"
            )
        self.prelabel_checks = dict(checks)
        self.phase = "candidate_frozen"
        self.events.append("candidate_frozen")

    def complete_retreat_certificate(self) -> None:
        if self.phase != "candidate_frozen":
            raise RuntimeError("fresh retreat certificate requires a frozen candidate")
        self.phase = "retreat_certificate_complete"
        self.events.append("retreat_certificate_complete")

    def snapshot(self) -> dict[str, Any]:
        return {
            "target_id": self.target_id,
            "phase": self.phase,
            "events": list(self.events),
            "prelabel_checks": dict(self.prelabel_checks),
        }


def fresh_replication_promotion(
    target_rows: list[Mapping[str, Any]],
    *,
    minimum_material_targets: int,
    minimum_material_exact_value: float,
) -> dict[str, Any]:
    """Apply the frozen transfer threshold without selecting a target post hoc."""

    if not target_rows:
        raise ValueError("fresh convex promotion requires target rows")
    if minimum_material_targets <= 0 or minimum_material_targets > len(target_rows):
        raise ValueError("fresh convex material target count is invalid")
    threshold = float(minimum_material_exact_value)
    if not math.isfinite(threshold) or threshold <= 0.0:
        raise ValueError("fresh convex material threshold must be finite and positive")
    material = [
        row
        for row in target_rows
        if row["retreat"]["shadow_accepted"]
        and float(row["retreat"]["exact_positive_value"]) > threshold
    ]
    families = {str(row["range_family"]) for row in material}
    all_schedules_fit = all(
        bool(row["ledger"]["fits_measured_street"])
        and bool(row["ledger"]["fits_effective_conservative_street"])
        for row in target_rows
    )
    return {
        "minimum_material_targets": minimum_material_targets,
        "minimum_material_exact_value": threshold,
        "material_target_count": len(material),
        "material_target_ids": [row["target_id"] for row in material],
        "material_range_families": sorted(families),
        "both_range_families_represented": families == {"balanced", "blocker_heavy"},
        "all_schedules_fit": all_schedules_fit,
        "authorizes_latin_f_confirmation": (
            len(material) >= minimum_material_targets
            and families == {"balanced", "blocker_heavy"}
            and all_schedules_fit
        ),
    }


def _parse_config(config: dict[str, Any]) -> dict[str, Any]:
    expected = {
        "evidence_stage",
        *_PATHS,
        "seed",
        "target_selection_rule",
        "target_specs",
        "acting_player_rule",
        "scope",
        "construction_rule",
        "oracle_rule",
        "cut_rule",
        "retreat_rule",
        "acceptance_rule",
        "promotion_rule",
        "street_budget_ms",
        "emission_reserve_ms",
        "retreat_envelope_reserve_ms",
        "frozen_conservative_live_ledger_ms",
        "maximum_cut_rounds",
        "minimum_material_targets",
        "minimum_material_exact_value",
        "acceptance_guard_normalized",
        "interior_retreat_factor",
        "lp_tolerance",
        "epigraph_separation_allowance",
        "candidate_projection_tolerance",
        "cap_numerical_allowance",
        "quality_numerical_allowance",
        "minimum_interior_slack_allowance",
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
        "strategy_label_policy",
        "gates",
    }
    if set(config) != expected:
        raise ValueError("fresh convex replication config fields differ from ADR-0255")
    for field_name, path in _PATHS.items():
        if config[field_name] != _sha256(path):
            raise ValueError(f"fresh convex provenance mismatch: {field_name}")
    manifest = json.loads(_MANIFEST.read_text(encoding="utf-8"))
    latin_e = [row for row in manifest["target_rows"] if row["round"] == "latin_e"]
    source_map = {
        "panel_1/balanced": (["5c", "8c", "8d", "Jc", "As"], "balanced"),
        "panel_1/blocker_heavy": (
            ["5c", "8c", "8d", "Jc", "As"],
            "blocker_heavy",
        ),
        "panel_2/blocker_heavy": (
            ["2c", "3s", "5d", "Js", "Qc"],
            "blocker_heavy",
        ),
        "panel_2/balanced": (["2c", "3s", "5d", "Js", "Qc"], "balanced"),
        "panel_3/balanced": (["4h", "7h", "9s", "Jd", "Kc"], "balanced"),
        "panel_3/blocker_heavy": (
            ["4h", "7h", "9s", "Jd", "Kc"],
            "blocker_heavy",
        ),
    }
    frozen_specs = []
    for row in latin_e:
        board, family = source_map[row["source"]]
        frozen_specs.append(
            {
                "target_id": row["target_id"],
                "source": row["source"],
                "observed_bettor": row["observed_bettor"],
                "acting_player": row["acting_player"],
                "round": row["round"],
                "source_belief_sha256": row["source_belief_sha256"],
                "target_belief_sha256": row["target_belief_sha256"],
                "target_descriptor_sha256": row["target_descriptor_sha256"],
                "board": board,
                "range_family": family,
            }
        )
    exact = {
        "evidence_stage": "preregistered_after_adr0254_before_any_latin_e_warm_step_convex_candidate_or_strategy_label",
        "seed": 20260822,
        "target_selection_rule": "all_six_latin_e_targets_in_manifest_order_zero_tv_or_opportunity_selection_latin_f_unopened",
        "target_specs": frozen_specs,
        "acting_player_rule": "manifest_last_responder_immediately_before_bettor_modulo_six",
        "scope": "six_fresh_targets_one_per_source_bettor_and_acting_player_one_seat_shadow_only",
        "construction_rule": "source_master_all_six_exact_first_oracle_all_epigraph_violator_multicut_resolve_at_most_once_then_half_retreat",
        "oracle_rule": "exactly_two_all_seat_oracles_per_target_first_master_separation_then_independent_retreat_certificate",
        "cut_rule": "add_every_new_opponent_response_signature_above_1e_9_once_no_second_round",
        "retreat_rule": "fixed_factor_0_5_no_endpoint_oracle_no_jensen_claim_exact_retreat_oracle_is_authority",
        "acceptance_rule": "shadow_accept_only_exact_cap_safe_positive_interior_and_both_ledgers_fit_else_blueprint_abstention",
        "promotion_rule": "authorize_latin_f_only_if_at_least_four_material_targets_above_0_001_both_range_families_and_all_schedules_fit",
        "street_budget_ms": 15000.0,
        "emission_reserve_ms": 1000.0,
        "retreat_envelope_reserve_ms": 50.0,
        "frozen_conservative_live_ledger_ms": 13967.615699994712,
        "maximum_cut_rounds": 1,
        "minimum_material_targets": 4,
        "minimum_material_exact_value": 0.001,
        "acceptance_guard_normalized": 1e-10,
        "interior_retreat_factor": 0.5,
        "lp_tolerance": 1e-10,
        "epigraph_separation_allowance": 1e-9,
        "candidate_projection_tolerance": 1e-10,
        "cap_numerical_allowance": 2e-11,
        "quality_numerical_allowance": 1e-10,
        "minimum_interior_slack_allowance": 2e-11,
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
        "strategy_label_policy": "six_fixed_fresh_retreat_labels_no_cross_target_adaptation_latin_f_labels_zero",
    }
    for field_name, expected_value in exact.items():
        if config[field_name] != expected_value:
            raise ValueError(f"fresh convex field differs from ADR-0255: {field_name}")
    gates = {
        "expected_targets": 6,
        "expected_sources": 6,
        "expected_bettors": 6,
        "expected_acting_players": 6,
        "expected_behavioral_information_sets": 512,
        "expected_policy_variables": 1024,
        "expected_epigraph_variables": 6,
        "expected_initial_profile_passes_per_target": 6,
        "expected_initial_response_passes_per_target": 5,
        "expected_initial_gain_rows_per_target": 6,
        "expected_exact_oracles_per_target": 2,
        "expected_new_strategy_labels": 6,
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
        "maximum_cut_extraction_ms": 60000.0,
        "maximum_gpu_pool_bytes": 12000000000,
        "minimum_physical_free_bytes": 1000000000,
        "maximum_total_seconds": 1200.0,
        "require_clean_git_state": True,
        "require_parents_passed": True,
        "require_target_identity": True,
        "require_blueprint_identity": True,
        "require_warm_start_identity": True,
        "require_path_single_visit": True,
        "require_exact_external_axis_coverage": True,
        "require_all_first_oracle_violators_cut": True,
        "require_maximum_one_cut_round": True,
        "require_every_retreat_certificate_complete": True,
        "require_outcome_neutral_abstention": True,
        "require_no_cross_target_adaptation": True,
        "require_blueprint_external_emission": True,
        "require_latin_f_labels_zero": True,
        "require_no_global_optimality_claim": True,
        "require_no_population_claim": True,
        "require_finite": True,
    }
    if config["gates"] != gates:
        raise ValueError("fresh convex gates differ from ADR-0255")
    return {
        **config,
        "target_specs": tuple(dict(row) for row in config["target_specs"]),
        "gates": gates,
    }


def _oracle_summary(
    oracle: Mapping[str, Any],
    *,
    layout: Any,
    caps: tuple[float, ...],
    cap_allowance: float,
    epigraph: tuple[float, ...] | None = None,
    epigraph_allowance: float | None = None,
) -> dict[str, Any]:
    assessed = assess_exact_oracle_gains(
        oracle["raw_gains"],
        caps,
        cap_allowance=cap_allowance,
        epigraph=epigraph,
        epigraph_allowance=epigraph_allowance,
    )
    evaluations = oracle["evaluations"]
    objective = math.fsum(assessed.gains)
    return {
        "policy_sha256": oracle["policy_sha256"],
        "best_response_values": [float(row.best_response_value) for row in evaluations],
        "utilities": [float(row.profile_utility) for row in evaluations],
        "raw_deviation_gains": list(oracle["raw_gains"]),
        "deviation_gains": list(assessed.gains),
        "nash_conv": objective,
        "normalized_nash_conv": normalized_quality(layout, objective),
        "response_signature_sha256": list(oracle["response_signatures"]),
        "probability_compile_ms": oracle["probability_compile_ms"],
        "wall_ms": oracle["wall_ms"],
        "seat_wall_ms": list(oracle["seat_wall_ms"]),
        "zero_sum_residual": oracle["zero_sum_residual"],
        "response_action_flips": oracle["response_action_flips"],
        "affected_terminal_contractions": oracle["affected_terminal_contractions"],
        "maximum_middle_rank": oracle["maximum_middle_rank"],
        "maximum_gpu_pool_total_bytes": oracle["maximum_gpu_pool_total_bytes"],
        "cap_allowance": cap_allowance,
        "maximum_cap_violation": assessed.maximum_cap_violation,
        "minimum_cap_slack": min(
            cap - gain for cap, gain in zip(caps, assessed.gains, strict=True)
        ),
        "cap_feasible": assessed.cap_feasible,
        "epigraph_allowance": epigraph_allowance,
        "maximum_epigraph_violation": assessed.maximum_epigraph_violation,
        "epigraph_violating_players": list(assessed.epigraph_violating_players),
        "epigraph_closed": assessed.epigraph_closed,
    }


def _run_target(
    parsed: Mapping[str, Any],
    source_parent: Mapping[str, Any],
    spec: Mapping[str, Any],
    cp: Any,
) -> dict[str, Any]:
    barrier = FreshCandidateBarrier(str(spec["target_id"]))
    cp.cuda.runtime.deviceSynchronize()
    setup_started = time.perf_counter()
    objects = _setup(parsed, source_parent, spec)
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
        raise AssertionError("fresh convex warm step emitted no work ledger")
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
    source_row_errors = []
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
            maximum_feature_width_per_batch=int(parsed["maximum_feature_width_per_batch"]),
        )
        profile_rows[payoff_player] = row
        initial_pass_rows.append(telemetry)
        source_row_errors.append(
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
        source_row_errors.append(
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
    guard = raw_guard(layout, float(parsed["acceptance_guard_normalized"]))
    source_gains = tuple(
        float(cache.source_evaluation.deviation_gain) for cache in context.response_caches
    )
    source_nash_conv = math.fsum(source_gains)
    caps = tuple(gain + guard for gain in source_gains)

    def solve_master():
        return solve_behavioral_one_seat_master(
            axis,
            tuple(tuple(rows.values()) for rows in row_libraries),
            caps,
            tolerance=float(parsed["lp_tolerance"]),
        )

    first_master = solve_master()
    first_policy, first_projection_error = axis.policy_from_variables(
        first_master.variables,
        blueprint,
        tolerance=float(parsed["candidate_projection_tolerance"]),
    )
    first_oracle = _exact_oracle(
        objects=objects,
        policy=first_policy,
        cp=cp,
        maximum_feature_width_per_batch=int(parsed["maximum_feature_width_per_batch"]),
    )
    first_summary = _oracle_summary(
        first_oracle,
        layout=layout,
        caps=caps,
        cap_allowance=float(parsed["cap_numerical_allowance"]),
        epigraph=tuple(first_master.epigraph),
        epigraph_allowance=float(parsed["epigraph_separation_allowance"]),
    )
    memory_rows.append({"stage": "first_oracle", **_memory_snapshot(cp)})
    profile_equivalence_errors = [
        abs(
            profile_rows[player].value(first_oracle["probabilities"])
            - first_oracle["evaluations"][player].profile_utility
        )
        for player in range(layout.num_players)
    ]

    violating_players = tuple(first_summary["epigraph_violating_players"])
    cut_rows = []
    cut_identity_errors = []
    cut_started = time.perf_counter()
    for player in violating_players:
        if player == acting_player:
            raise ArithmeticError("fresh convex invariant acting row is violated")
        signature = first_oracle["response_signatures"][player]
        if signature in row_libraries[player]:
            raise ArithmeticError("fresh convex exact duplicate response remains violated")
        actions = first_oracle["evaluations"][player].best_response_actions
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
            maximum_feature_width_per_batch=int(parsed["maximum_feature_width_per_batch"]),
            record_to_hand_backend="gpu_cupy",
        )
        cp.cuda.runtime.deviceSynchronize()
        pass_ms = (time.perf_counter() - pass_started) * 1000.0
        response = behavioral_open_axis_payoff_row(
            layout,
            first_oracle["probabilities"],
            extracted,
            acting_player=acting_player,
            source_value=float(first_oracle["evaluations"][player].best_response_value),
        )
        gain = subtract_affine_rows(response, profile_rows[player])
        identity_error = abs(
            gain.value(first_oracle["probabilities"])
            - first_oracle["raw_gains"][player]
        )
        cut_identity_errors.append(identity_error)
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
    cut_extraction_ms = (time.perf_counter() - cut_started) * 1000.0
    memory_rows.append({"stage": "cuts", **_memory_snapshot(cp)})
    cut_rounds = int(bool(cut_rows))
    if cut_rounds > int(parsed["maximum_cut_rounds"]):
        raise RuntimeError("fresh convex construction exceeded one cut round")

    final_master = first_master
    second_projection_error = 0.0
    endpoint_policy = first_policy
    if cut_rows:
        final_master = solve_master()
        endpoint_policy, second_projection_error = axis.policy_from_variables(
            final_master.variables,
            blueprint,
            tolerance=float(parsed["candidate_projection_tolerance"]),
        )
    retreat_started = time.perf_counter()
    retreat_policy, retreat_mass_error = _mix_policy(
        blueprint,
        endpoint_policy,
        eta=float(parsed["interior_retreat_factor"]),
    )
    retreat_construction_ms = (time.perf_counter() - retreat_started) * 1000.0
    masters = [_master_summary(first_master)]
    if final_master is not first_master:
        masters.append(_master_summary(final_master))
    maximum_master_primal = max(
        max(row["maximum_equality_error"] for row in masters),
        max(row["maximum_inequality_violation"] for row in masters),
        max(row["maximum_bound_violation"] for row in masters),
    )
    maximum_master_dual = max(
        max(row["maximum_stationarity_error"] for row in masters),
        max(row["maximum_complementarity_error"] for row in masters),
        max(row["duality_gap"] for row in masters),
    )
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
    all_violators_cut = {
        row["target_player"] for row in cut_rows
    } == set(violating_players)
    exact_external_axis_coverage = external_axis_splices == (
        layout.num_players - 1 + len(cut_rows)
    )
    gate = parsed["gates"]
    prelabel_checks = {
        "source_checkpoint_identity": source_checkpoint_identity,
        "target_identity": target_identity,
        "blueprint_identity": blueprint_identity,
        "warm_start_identity": (
            warm_distance["maximum_probability_error"]
            <= gate["maximum_warm_start_probability_error"]
            and warm_distance["mean_total_variation"]
            <= gate["maximum_warm_start_mean_total_variation"]
        ),
        "path_single_visit": topology.passed,
        "information_set_count": len(axis.information_sets)
        == gate["expected_behavioral_information_sets"],
        "policy_variable_count": axis.variable_count == gate["expected_policy_variables"],
        "epigraph_variable_count": layout.num_players
        == gate["expected_epigraph_variables"],
        "initial_row_identity": max(source_row_errors)
        <= gate["maximum_initial_row_error"],
        "cut_row_identity": max(cut_identity_errors, default=0.0)
        <= gate["maximum_cut_row_error"],
        "profile_equivalence": max(profile_equivalence_errors)
        <= gate["maximum_profile_equivalence_error"],
        "master_primal": maximum_master_primal <= gate["maximum_master_primal_error"],
        "master_dual": maximum_master_dual <= gate["maximum_master_dual_error"],
        "projection": max(first_projection_error, second_projection_error)
        <= gate["maximum_projection_error"],
        "raw_guard": abs(guard - 3e-9) <= gate["maximum_raw_guard_error"],
        "all_violators_cut": all_violators_cut,
        "maximum_one_cut_round": cut_rounds <= 1,
        "external_axis_coverage": exact_external_axis_coverage,
        "cap_allowance_separate": first_summary["cap_allowance"]
        == float(parsed["cap_numerical_allowance"]),
        "epigraph_allowance_separate": first_summary["epigraph_allowance"]
        == float(parsed["epigraph_separation_allowance"]),
        "retreat_simplex": retreat_mass_error
        <= gate["maximum_warm_start_probability_error"],
    }
    barrier.freeze_candidate(prelabel_checks)

    retreat_oracle = _exact_oracle(
        objects=objects,
        policy=retreat_policy,
        cp=cp,
        maximum_feature_width_per_batch=int(parsed["maximum_feature_width_per_batch"]),
    )
    retreat_summary = _oracle_summary(
        retreat_oracle,
        layout=layout,
        caps=caps,
        cap_allowance=float(parsed["cap_numerical_allowance"]),
    )
    barrier.complete_retreat_certificate()
    memory_rows.append({"stage": "retreat_oracle", **_memory_snapshot(cp)})
    profile_equivalence_errors.extend(
        abs(
            profile_rows[player].value(retreat_oracle["probabilities"])
            - retreat_oracle["evaluations"][player].profile_utility
        )
        for player in range(layout.num_players)
    )

    exact_positive_value = source_nash_conv - float(retreat_summary["nash_conv"])
    required_interior_slack = max(
        0.0,
        (1.0 - float(parsed["interior_retreat_factor"])) * guard
        - float(parsed["minimum_interior_slack_allowance"]),
    )
    master_ms = math.fsum(row["solve_ms"] for row in masters)
    measured_live_ms = (
        warm_step_ms
        + initial_row_ms
        + master_ms
        + float(first_oracle["wall_ms"])
        + cut_extraction_ms
        + float(retreat_oracle["wall_ms"])
        + max(
            retreat_construction_ms,
            float(parsed["retreat_envelope_reserve_ms"]),
        )
        + float(parsed["emission_reserve_ms"])
    )
    effective_conservative_ms = max(
        float(parsed["frozen_conservative_live_ledger_ms"]),
        measured_live_ms,
    )
    fits_measured = measured_live_ms <= float(parsed["street_budget_ms"])
    fits_conservative = effective_conservative_ms <= float(parsed["street_budget_ms"])
    interior_passed = (
        float(retreat_summary["minimum_cap_slack"]) >= required_interior_slack
    )
    acceptance_predicate_passed = bool(
        retreat_summary["cap_feasible"]
        and exact_positive_value > float(parsed["quality_numerical_allowance"])
        and interior_passed
        and fits_measured
        and fits_conservative
    )
    shadow_accepted = acceptance_predicate_passed
    maximum_pool = max(
        max(row["gpu_pool_total_bytes"] for row in memory_rows),
        max(row["maximum_gpu_pool_total_bytes"] for row in initial_pass_rows),
        max((row["maximum_gpu_pool_total_bytes"] for row in cut_rows), default=0),
        int(first_oracle["maximum_gpu_pool_total_bytes"]),
        int(retreat_oracle["maximum_gpu_pool_total_bytes"]),
    )
    minimum_free = min(row["gpu_free_bytes"] for row in memory_rows)
    result = {
        "target_id": spec["target_id"],
        "source": spec["source"],
        "range_family": spec["range_family"],
        "observed_bettor": spec["observed_bettor"],
        "acting_player": acting_player,
        "round": spec["round"],
        "acting_public_nodes": len(axis.acting_nodes),
        "path_single_visit": topology.passed,
        "behavioral_information_sets": len(axis.information_sets),
        "policy_variables": axis.variable_count,
        "epigraph_variables": layout.num_players,
        "payoff_span": payoff_span(layout),
        "payoff_span_source": "layout.game.payoff_span",
        "raw_guard": guard,
        "source_nash_conv": source_nash_conv,
        "cold_setup_ms": cold_setup_ms,
        "warm_start_distance": warm_distance,
        "warm_step": warm_work,
        "initial_profile_passes": sum(
            row["kind"] == "profile" for row in initial_pass_rows
        ),
        "initial_response_passes": sum(
            row["kind"] == "fixed_response" for row in initial_pass_rows
        ),
        "initial_gain_rows": 6,
        "initial_row_ms": initial_row_ms,
        "initial_pass_rows": initial_pass_rows,
        "maximum_initial_row_error": max(source_row_errors),
        "masters": masters,
        "first_candidate_projection_error": first_projection_error,
        "second_candidate_projection_error": second_projection_error,
        "first_oracle": first_summary,
        "cut_rounds": cut_rounds,
        "cut_rows": cut_rows,
        "cut_extraction_ms": cut_extraction_ms,
        "maximum_cut_row_error": max(cut_identity_errors, default=0.0),
        "row_counts_by_player": [len(rows) for rows in row_libraries],
        "maximum_profile_equivalence_error": max(profile_equivalence_errors),
        "maximum_master_primal_error": maximum_master_primal,
        "maximum_master_dual_error": maximum_master_dual,
        "endpoint_policy_sha256": policy_digest(endpoint_policy),
        "endpoint_independently_certified": not bool(cut_rows),
        "retreat": {
            "factor": parsed["interior_retreat_factor"],
            "policy_sha256": policy_digest(retreat_policy),
            "maximum_simplex_mass_error": retreat_mass_error,
            "construction_ms": retreat_construction_ms,
            "exact_certificate": retreat_summary,
            "exact_positive_value": exact_positive_value,
            "required_interior_slack": required_interior_slack,
            "interior_slack_passed": interior_passed,
            "independently_certified": True,
            "acceptance_predicate_passed": acceptance_predicate_passed,
            "shadow_accepted": shadow_accepted,
            "material_value": exact_positive_value
            > float(parsed["minimum_material_exact_value"]),
            "emitted": False,
        },
        "exact_oracles_executed": 2,
        "oracle_targets": ["first_master_candidate", "factor_0.5_retreat"],
        "ledger": {
            "measured_live_ms": measured_live_ms,
            "measured_headroom_ms": float(parsed["street_budget_ms"])
            - measured_live_ms,
            "frozen_conservative_live_ms": float(
                parsed["frozen_conservative_live_ledger_ms"]
            ),
            "effective_conservative_live_ms": effective_conservative_ms,
            "effective_conservative_headroom_ms": float(parsed["street_budget_ms"])
            - effective_conservative_ms,
            "fits_measured_street": fits_measured,
            "fits_effective_conservative_street": fits_conservative,
            "components_ms": {
                "warm_step": warm_step_ms,
                "initial_rows": initial_row_ms,
                "masters": master_ms,
                "first_oracle": float(first_oracle["wall_ms"]),
                "cut_extraction": cut_extraction_ms,
                "retreat_oracle": float(retreat_oracle["wall_ms"]),
                "retreat_and_envelope_charged": max(
                    retreat_construction_ms,
                    float(parsed["retreat_envelope_reserve_ms"]),
                ),
                "emission_reserve": float(parsed["emission_reserve_ms"]),
            },
        },
        "memory_rows": memory_rows,
        "maximum_gpu_pool_total_bytes": maximum_pool,
        "minimum_gpu_free_bytes": minimum_free,
        "resident_numeric_bytes": {
            "shared_device": shared_device_numeric_bytes(shared, (context,)),
            "unique_response_host": unique_response_numeric_bytes((context,)),
            "solver": solver.memory_summary(),
        },
        "source_checkpoint_identity": source_checkpoint_identity,
        "target_identity": target_identity,
        "blueprint_identity": blueprint_identity,
        "exact_external_axis_coverage": exact_external_axis_coverage,
        "external_axis_splices": external_axis_splices,
        "all_first_oracle_violators_cut": all_violators_cut,
        "label_barrier": barrier.snapshot(),
        "restricted_blueprint_policy_sha256": policy_digest(blueprint),
        "actual_emitted_policy_sha256": policy_digest(blueprint),
        "candidate_policies_emitted": 0,
        "new_strategy_quality_labels_generated": 1,
    }
    del solver
    objects.clear()
    gc.collect()
    release_cupy_memory_pool()
    return result


def run_h32_fresh_convex_retreat_replication(
    config_path: Path = _CONFIG,
    output_path: Path = _OUTPUT,
) -> dict[str, Any]:
    started = time.perf_counter()
    parsed = _parse_config(json.loads(config_path.read_text(encoding="utf-8")))
    git = _strict_git_metadata()
    cp, runtime = _validate_runtime(parsed)
    source = load_artifact(
        _SOURCE,
        expected_sha256=parsed["expected_source_result_sha256"],
        require_passed=True,
    ).payload
    manifest = load_artifact(
        _MANIFEST,
        expected_sha256=parsed["expected_manifest_result_sha256"],
        require_passed=True,
    ).payload
    known = load_artifact(
        _KNOWN_RESULT,
        expected_sha256=parsed["expected_known_result_sha256"],
        require_passed=True,
    ).payload
    target_rows = [_run_target(parsed, source, spec, cp) for spec in parsed["target_specs"]]
    promotion = fresh_replication_promotion(
        target_rows,
        minimum_material_targets=int(parsed["minimum_material_targets"]),
        minimum_material_exact_value=float(parsed["minimum_material_exact_value"]),
    )
    total_seconds = time.perf_counter() - started
    fixed_target_ids = [row["target_id"] for row in parsed["target_specs"]]
    cross_target_adaptation = False
    latin_f_strategy_quality_labels = sum(
        row["new_strategy_quality_labels_generated"]
        for row in target_rows
        if row["round"] == "latin_f"
    )
    one_seat_global_optimality_claim = None
    strategy_population_claim = None
    gate = parsed["gates"]
    checks = {
        "clean_git": (not git["dirty"]) == gate["require_clean_git_state"],
        "parents_passed": all(artifact_passed(row) for row in (source, manifest, known))
        == gate["require_parents_passed"],
        "target_count": len(target_rows) == gate["expected_targets"],
        "source_count": len({row["source"] for row in target_rows})
        == gate["expected_sources"],
        "bettor_count": len({row["observed_bettor"] for row in target_rows})
        == gate["expected_bettors"],
        "acting_player_count": len({row["acting_player"] for row in target_rows})
        == gate["expected_acting_players"],
        "target_identity": all(
            row["source_checkpoint_identity"] and row["target_identity"]
            for row in target_rows
        )
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
        "axis_counts": all(
            row["behavioral_information_sets"]
            == gate["expected_behavioral_information_sets"]
            and row["policy_variables"] == gate["expected_policy_variables"]
            and row["epigraph_variables"] == gate["expected_epigraph_variables"]
            for row in target_rows
        ),
        "initial_pass_counts": all(
            row["initial_profile_passes"]
            == gate["expected_initial_profile_passes_per_target"]
            and row["initial_response_passes"]
            == gate["expected_initial_response_passes_per_target"]
            and row["initial_gain_rows"] == gate["expected_initial_gain_rows_per_target"]
            for row in target_rows
        ),
        "row_identity": all(
            row["maximum_initial_row_error"] <= gate["maximum_initial_row_error"]
            and row["maximum_cut_row_error"] <= gate["maximum_cut_row_error"]
            and row["maximum_profile_equivalence_error"]
            <= gate["maximum_profile_equivalence_error"]
            for row in target_rows
        ),
        "master_numerics": all(
            row["maximum_master_primal_error"] <= gate["maximum_master_primal_error"]
            and row["maximum_master_dual_error"] <= gate["maximum_master_dual_error"]
            for row in target_rows
        ),
        "projection": all(
            max(
                row["first_candidate_projection_error"],
                row["second_candidate_projection_error"],
            )
            <= gate["maximum_projection_error"]
            for row in target_rows
        ),
        "raw_guard": all(
            abs(row["raw_guard"] - 3e-9) <= gate["maximum_raw_guard_error"]
            for row in target_rows
        ),
        "cold_setup_time": max(row["cold_setup_ms"] for row in target_rows)
        <= gate["maximum_cold_setup_ms"],
        "warm_step_time": max(row["warm_step"]["wall_ms"] for row in target_rows)
        <= gate["maximum_warm_step_ms"],
        "initial_row_time": max(row["initial_row_ms"] for row in target_rows)
        <= gate["maximum_initial_row_ms"],
        "master_time": max(
            master["solve_ms"] for row in target_rows for master in row["masters"]
        )
        <= gate["maximum_master_ms"],
        "oracle_time": max(
            max(row["first_oracle"]["wall_ms"], row["retreat"]["exact_certificate"]["wall_ms"])
            for row in target_rows
        )
        <= gate["maximum_oracle_ms"],
        "cut_extraction_time": max(row["cut_extraction_ms"] for row in target_rows)
        <= gate["maximum_cut_extraction_ms"],
        "gpu_pool": max(row["maximum_gpu_pool_total_bytes"] for row in target_rows)
        <= gate["maximum_gpu_pool_bytes"],
        "physical_free": min(row["minimum_gpu_free_bytes"] for row in target_rows)
        >= gate["minimum_physical_free_bytes"],
        "external_axis_coverage": all(
            row["exact_external_axis_coverage"] for row in target_rows
        )
        == gate["require_exact_external_axis_coverage"],
        "all_violators_cut": all(
            row["all_first_oracle_violators_cut"] for row in target_rows
        )
        == gate["require_all_first_oracle_violators_cut"],
        "maximum_one_cut_round": all(row["cut_rounds"] <= 1 for row in target_rows)
        == gate["require_maximum_one_cut_round"],
        "retreat_certificates_complete": all(
            row["retreat"]["independently_certified"]
            and row["exact_oracles_executed"] == gate["expected_exact_oracles_per_target"]
            for row in target_rows
        )
        == gate["require_every_retreat_certificate_complete"],
        "outcome_neutral_abstention": all(
            row["retreat"]["shadow_accepted"]
            == row["retreat"]["acceptance_predicate_passed"]
            and (
                row["retreat"]["shadow_accepted"]
                or row["actual_emitted_policy_sha256"]
                == row["restricted_blueprint_policy_sha256"]
            )
            for row in target_rows
        )
        == gate["require_outcome_neutral_abstention"],
        "no_cross_target_adaptation": (
            [row["target_id"] for row in target_rows] == fixed_target_ids
            and not cross_target_adaptation
        )
        == gate["require_no_cross_target_adaptation"],
        "blueprint_external_emission": all(
            row["actual_emitted_policy_sha256"]
            == row["restricted_blueprint_policy_sha256"]
            and row["candidate_policies_emitted"] == 0
            for row in target_rows
        )
        == gate["require_blueprint_external_emission"],
        "strategy_label_count": sum(
            row["new_strategy_quality_labels_generated"] for row in target_rows
        )
        == gate["expected_new_strategy_labels"],
        "latin_f_labels_zero": (latin_f_strategy_quality_labels == 0)
        == gate["require_latin_f_labels_zero"],
        "no_global_optimality_claim": (one_seat_global_optimality_claim is None)
        == gate["require_no_global_optimality_claim"],
        "no_population_claim": (strategy_population_claim is None)
        == gate["require_no_population_claim"],
        "total_time": total_seconds <= gate["maximum_total_seconds"],
        "finite": _finite_tree(target_rows) == gate["require_finite"],
    }
    gate_result = finalize_gates(checks)
    promote = bool(
        gate_result["passed"] and promotion["authorizes_latin_f_confirmation"]
    )
    delivered_values = [
        float(row["retreat"]["exact_positive_value"])
        if row["retreat"]["shadow_accepted"]
        else 0.0
        for row in target_rows
    ]
    result = {
        "schema_version": 1,
        "status": "h32_fresh_convex_retreat_replication_executed",
        "environment": assemble_environment(runtime=runtime, git=git),
        "config_sha256": _sha256(config_path),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "methodology": {
            "fresh_targets": 6,
            "warm_steps": 6,
            "exact_oracles": 12,
            "adaptive_construction_oracles": 6,
            "final_retreat_strategy_labels": 6,
            "new_strategy_quality_labels": 6,
            "latin_f_strategy_quality_labels": latin_f_strategy_quality_labels,
            "candidate_policies_emitted": 0,
            "cross_target_adaptation": cross_target_adaptation,
        },
        "target_rows": target_rows,
        "promotion": promotion,
        "aggregate": {
            "shadow_accepted_targets": sum(
                row["retreat"]["shadow_accepted"] for row in target_rows
            ),
            "material_target_count": promotion["material_target_count"],
            "pooled_delivered_exact_value": math.fsum(delivered_values),
            "minimum_delivered_exact_value": min(delivered_values),
            "median_delivered_exact_value": float(np.median(delivered_values)),
            "maximum_delivered_exact_value": max(delivered_values),
            "maximum_measured_live_ms": max(
                row["ledger"]["measured_live_ms"] for row in target_rows
            ),
            "maximum_effective_conservative_live_ms": max(
                row["ledger"]["effective_conservative_live_ms"]
                for row in target_rows
            ),
            "authorize_latin_f_confirmation": promote,
        },
        **gate_result,
        "decision": (
            "authorize_preregistered_latin_f_convex_retreat_confirmation"
            if promote
            else "retain_known_target_result_and_reject_latin_f_confirmation"
            if gate_result["passed"]
            else "reject_fresh_convex_retreat_replication_execution"
        ),
        "actual_emitted_policy": "immutable_restricted_blueprint_only_on_all_targets",
        "strategy_quality_claim": (
            "six_fresh_target_shadow_measurement_only" if gate_result["passed"] else None
        ),
        "one_seat_global_optimality_claim": one_seat_global_optimality_claim,
        "strategy_population_claim": strategy_population_claim,
        "total_seconds": total_seconds,
        "limitations": [
            "Latin-E reuses source boards and blueprints but opens six previously unseen action-conditioned posterior labels.",
            "No fresh one-step fallback is evaluated, so this experiment tests convex value transfer rather than comparative dominance.",
            "A post-cut endpoint is not independently certified; only the half-retreat exact oracle has safety authority.",
            "Latin-F remains untouched and no population, deployment, composition, cross-street, or broad poker claim is made.",
        ],
    }
    output_path.write_text(serialize_result(result), encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=_CONFIG)
    parser.add_argument("--output", type=Path, default=_OUTPUT)
    args = parser.parse_args()
    result = run_h32_fresh_convex_retreat_replication(args.config, args.output)
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
