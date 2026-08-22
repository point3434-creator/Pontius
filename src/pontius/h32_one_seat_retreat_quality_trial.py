"""One-target quality gate for the independently certified h32 convex retreat."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, field
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
from .payoff_semantics import normalized_quality, payoff_span, raw_guard
from .one_seat_convex_generation import compiled_layout_path_single_visit_report
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
_CONFIG = _ROOT / "experiments/configs/h32-one-seat-retreat-quality-v1.json"
_OUTPUT = _ROOT / "experiments/results/h32-one-seat-retreat-quality-v1.json"
_SOURCE = _ROOT / "experiments/results/h32-fresh-panel-source-blueprints-v1.json"
_OPTIMIZER = _ROOT / "experiments/results/h32-one-round-convex-master-v1.json"
_OPTIMIZER_CONFIG = _ROOT / "experiments/configs/h32-one-round-convex-master-v1.json"
_OPTIMIZER_DECISION = (
    _ROOT
    / "docs/decisions/ADR-0247-one-round-h32-convex-master-closes-the-exact-gap.md"
)
_FALLBACK = _ROOT / "experiments/results/h32-heldout-continuation-depth-value-v1.json"
_FALLBACK_CONFIG = _ROOT / "experiments/configs/h32-heldout-continuation-depth-value-v1.json"
_FALLBACK_DECISION = (
    _ROOT
    / "docs/decisions/ADR-0235-one-step-retained-after-heldout-depth-value-trial.md"
)
_IMPLEMENTATION = Path(__file__)
_TEST = _ROOT / "tests/test_h32_one_seat_retreat_quality_trial.py"

_PATHS = {
    "expected_source_result_sha256": _SOURCE,
    "expected_optimizer_result_sha256": _OPTIMIZER,
    "expected_optimizer_config_sha256": _OPTIMIZER_CONFIG,
    "expected_optimizer_decision_sha256": _OPTIMIZER_DECISION,
    "expected_fallback_result_sha256": _FALLBACK,
    "expected_fallback_config_sha256": _FALLBACK_CONFIG,
    "expected_fallback_decision_sha256": _FALLBACK_DECISION,
    "expected_optimizer_implementation_sha256": (
        _ROOT / "src/pontius/h32_one_round_convex_master.py"
    ),
    "expected_master_sha256": _ROOT / "src/pontius/behavioral_one_seat_master.py",
    "expected_behavioral_row_sha256": _ROOT / "src/pontius/behavioral_open_axis.py",
    "expected_sequence_row_sha256": _ROOT / "src/pontius/sequence_form_open_axis.py",
    "expected_cross_payoff_sha256": _ROOT / "src/pontius/cross_payoff_leaf_adjoint.py",
    "expected_incremental_oracle_sha256": (
        _ROOT / "src/pontius/incremental_leaf_adjoint_response.py"
    ),
    "expected_payoff_semantics_sha256": _ROOT / "src/pontius/payoff_semantics.py",
    "expected_setup_sha256": _ROOT / "src/pontius/h32_continuation_root_ledger.py",
    "expected_device_cfr_sha256": (
        _ROOT / "src/pontius/device_fold_resident_leaf_adjoint_cfr.py"
    ),
    "expected_preflight_implementation_sha256": (
        _ROOT / "src/pontius/h32_one_seat_open_axis_preflight.py"
    ),
    "expected_runner_harness_sha256": _ROOT / "src/pontius/runner_harness.py",
    "expected_assessment_sha256": _ROOT / "src/pontius/exact_oracle_assessment.py",
    "expected_assessment_control_test_sha256": (
        _ROOT / "tests/test_exact_oracle_assessment.py"
    ),
    "expected_implementation_sha256": _IMPLEMENTATION,
    "expected_control_test_sha256": _TEST,
}


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required retreat-quality input is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


@dataclass(slots=True)
class QualityLabelBarrier:
    """Fail closed unless the comparator opens after the retreat certificate."""

    phase: str = "inputs_pinned"
    events: list[str] = field(default_factory=lambda: ["inputs_pinned"])

    def freeze_candidate(self, identity_checks: Mapping[str, bool]) -> None:
        if self.phase != "inputs_pinned":
            raise RuntimeError("quality candidate can be frozen only once")
        if not identity_checks or any(
            type(value) is not bool for value in identity_checks.values()
        ):
            raise ValueError("quality candidate identity checks must be Boolean")
        if not all(identity_checks.values()):
            raise RuntimeError("quality candidate differs before its label is opened")
        self.phase = "candidate_frozen"
        self.events.append("candidate_frozen")

    def complete_retreat_certificate(self) -> None:
        if self.phase != "candidate_frozen":
            raise RuntimeError("retreat certificate requires a frozen candidate")
        self.phase = "retreat_certificate_complete"
        self.events.append("retreat_certificate_complete")

    def open_sealed_comparator(self) -> None:
        if self.phase != "retreat_certificate_complete":
            raise RuntimeError("sealed comparator cannot open before retreat certification")
        self.phase = "sealed_comparator_opened"
        self.events.append("sealed_comparator_opened")

    def snapshot(self) -> dict[str, Any]:
        return {"phase": self.phase, "events": list(self.events)}


def adjudicate_retreat_replication(
    *,
    retreat_value: float,
    retreat_conservative_ledger_ms: float,
    fallback_value: float,
    fallback_ledger_ms: float,
    raw_guard_value: float,
) -> dict[str, float | bool]:
    """Apply the frozen material-value and conservative-rate comparison."""

    values = tuple(
        float(value)
        for value in (
            retreat_value,
            retreat_conservative_ledger_ms,
            fallback_value,
            fallback_ledger_ms,
            raw_guard_value,
        )
    )
    if any(not math.isfinite(value) for value in values):
        raise ValueError("retreat comparison inputs must be finite")
    retreat, retreat_ms, fallback, fallback_ms, guard = values
    if retreat < 0.0 or guard < 0.0:
        raise ValueError("retreat value and guard must be nonnegative")
    if fallback <= 0.0:
        raise ValueError("sealed fallback value must be positive")
    if retreat_ms <= 0.0 or fallback_ms <= 0.0:
        raise ValueError("retreat comparison ledgers must be positive")
    retreat_rate = retreat / retreat_ms
    fallback_rate = fallback / fallback_ms
    material_value_win = retreat > fallback + guard
    conservative_rate_win = retreat_rate > fallback_rate
    return {
        "retreat_exact_value": retreat,
        "fallback_exact_value": fallback,
        "value_difference": retreat - fallback,
        "materiality_floor": guard,
        "material_value_win": material_value_win,
        "retreat_conservative_value_per_ms": retreat_rate,
        "fallback_value_per_ms": fallback_rate,
        "value_rate_ratio": retreat_rate / fallback_rate if fallback_rate > 0.0 else math.inf,
        "conservative_rate_win": conservative_rate_win,
        "authorizes_fresh_target_replication": material_value_win and conservative_rate_win,
    }


def _parse_config(config: dict[str, Any]) -> dict[str, Any]:
    expected = {
        "evidence_stage",
        *_PATHS,
        "seed",
        "target",
        "acting_player",
        "scope",
        "construction_rule",
        "oracle_rule",
        "label_barrier_rule",
        "comparison_rule",
        "emission_rule",
        "promotion_rule",
        "street_budget_ms",
        "emission_reserve_ms",
        "retreat_envelope_reserve_ms",
        "conservative_live_ledger_ms",
        "maximum_cut_rounds",
        "acceptance_guard_normalized",
        "interior_retreat_factor",
        "lp_tolerance",
        "epigraph_separation_allowance",
        "bound_reproduction_tolerance",
        "candidate_projection_tolerance",
        "cap_numerical_allowance",
        "quality_numerical_allowance",
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
        "expected_blueprint_policy_sha256",
        "expected_first_candidate_policy_sha256",
        "expected_endpoint_policy_sha256",
        "expected_retreat_policy_sha256",
        "expected_cut_players",
        "expected_cut_response_signatures",
        "expected_row_counts_by_player",
        "expected_initial_lower_bound",
        "expected_final_lower_bound",
        "expected_source_nash_conv",
        "expected_fallback_depth",
        "expected_fallback_blocks",
        "expected_fallback_candidate_id",
        "expected_fallback_policy_sha256",
        "strategy_label_policy",
        "gates",
    }
    if set(config) != expected:
        raise ValueError("retreat-quality config fields differ from ADR-0249")
    for field_name, path in _PATHS.items():
        if config[field_name] != _sha256(path):
            raise ValueError(f"retreat-quality provenance mismatch: {field_name}")

    optimizer_config = json.loads(_OPTIMIZER_CONFIG.read_text(encoding="utf-8"))
    exact = {
        "evidence_stage": (
            "preregistered_after_adr0247_before_any_retreat_certificate_or_"
            "fallback_label_join"
        ),
        "seed": 20260822,
        "target": optimizer_config["target"],
        "acting_player": 0,
        "scope": "one_retained_target_one_acting_seat_half_retreat_shadow_quality_only",
        "construction_rule": (
            "reconstruct_source_rows_first_master_exact_multicut_seats4_and5_"
            "second_master_then_half_retreat_without_endpoint_oracle"
        ),
        "oracle_rule": (
            "two_all_seat_oracles_total_first_master_for_frozen_cuts_then_"
            "independent_half_retreat_certificate"
        ),
        "label_barrier_rule": (
            "candidate_and_optimizer_identity_frozen_before_retreat_label_then_"
            "open_sealed_fallback_comparator"
        ),
        "comparison_rule": (
            "retreat_exact_value_exceeds_fallback_by_one_raw_guard_and_"
            "conservative_value_rate_exceeds_fallback_rate"
        ),
        "emission_rule": (
            "development_shadow_only_actual_external_policy_remains_immutable_blueprint"
        ),
        "promotion_rule": (
            "passing_exact_safe_positive_material_and_rate_win_authorizes_"
            "fresh_target_replication_only"
        ),
        "street_budget_ms": 15000.0,
        "emission_reserve_ms": 1000.0,
        "retreat_envelope_reserve_ms": 50.0,
        "conservative_live_ledger_ms": 13967.615699994712,
        "maximum_cut_rounds": 1,
        "acceptance_guard_normalized": 1e-10,
        "interior_retreat_factor": 0.5,
        "lp_tolerance": 1e-10,
        "epigraph_separation_allowance": 1e-9,
        "bound_reproduction_tolerance": 1e-12,
        "candidate_projection_tolerance": 1e-10,
        "cap_numerical_allowance": 2e-11,
        "quality_numerical_allowance": 1e-10,
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
        "expected_blueprint_policy_sha256": (
            "32b49a5d96cf63c57dd3329717130ee9d0a24e90df67e2127077af2f7da37171"
        ),
        "expected_first_candidate_policy_sha256": (
            "42e3f2450170832cad3526fc5e51e1eee1938db2f3474d18894b2843b5c3ea7a"
        ),
        "expected_endpoint_policy_sha256": (
            "0eef0f484ac545134ce551d11d420bc1ec13ed2dd5cde27c1b7e6fd6a5428227"
        ),
        "expected_retreat_policy_sha256": (
            "e45b3cec1f24272faa315a7ae25ee2ca51fa5c4269c667a564454e8a1b8ba37b"
        ),
        "expected_cut_players": [4, 5],
        "expected_cut_response_signatures": [
            "f18d9a7054304b45daaa92739a4f6afbb4dce10c0c66c05e1e6b961074f78890",
            "78c8486b36c9d5e1d79303093c6f2dec647219b5dd2c923c932d5307d085a83a",
        ],
        "expected_row_counts_by_player": [1, 1, 1, 1, 2, 2],
        "expected_initial_lower_bound": 0.03606141790374194,
        "expected_final_lower_bound": 0.03704032080499536,
        "expected_source_nash_conv": 0.05280449697669187,
        "expected_fallback_depth": 1,
        "expected_fallback_blocks": 31,
        "expected_fallback_candidate_id": "depth1_block_004_seat0_regret_vertex",
        "expected_fallback_policy_sha256": (
            "0bce2cce946e50ea102c9672406c33b9ca12187ec46f1fc5e2c7ec8b0c2a2590"
        ),
        "strategy_label_policy": (
            "one_new_retreat_exact_value_after_candidate_freeze_one_previously_"
            "sealed_fallback_label_no_population_claim"
        ),
    }
    for field_name, expected_value in exact.items():
        if config[field_name] != expected_value:
            raise ValueError(f"retreat-quality field differs from ADR-0249: {field_name}")

    gates = {
        "expected_acting_public_nodes": 16,
        "expected_behavioral_information_sets": 512,
        "expected_policy_variables": 1024,
        "expected_epigraph_variables": 6,
        "expected_initial_profile_passes": 6,
        "expected_initial_response_passes": 5,
        "expected_initial_gain_rows": 6,
        "expected_exact_oracles": 2,
        "expected_cut_rows": 2,
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
        "maximum_total_seconds": 600.0,
        "require_clean_git_state": True,
        "require_parents_passed": True,
        "require_target_identity": True,
        "require_blueprint_identity": True,
        "require_warm_start_identity": True,
        "require_path_single_visit": True,
        "require_exact_external_axis_coverage": True,
        "require_optimizer_identity": True,
        "require_retreat_exact_certificate": True,
        "require_retreat_cap_feasible": True,
        "require_retreat_positive_value": True,
        "require_retreat_jensen_bound": True,
        "require_retreat_interior_slack": True,
        "require_fallback_identity": True,
        "require_label_barrier": True,
        "require_measured_street_fit": True,
        "require_conservative_street_fit": True,
        "require_blueprint_external_emission": True,
        "require_single_new_strategy_label": True,
        "require_no_population_claim": True,
        "require_finite": True,
    }
    if config["gates"] != gates:
        raise ValueError("retreat-quality gates differ from ADR-0249")
    return {**config, "target": dict(config["target"]), "gates": gates}


def _oracle_quality_summary(
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
    minimum_cap_slack = min(
        cap - gain for cap, gain in zip(caps, assessed.gains, strict=True)
    )
    return {
        "policy_sha256": oracle["policy_sha256"],
        "best_response_values": [float(row.best_response_value) for row in evaluations],
        "utilities": [float(row.profile_utility) for row in evaluations],
        "raw_deviation_gains": list(oracle["raw_gains"]),
        "deviation_gains": list(assessed.gains),
        "nash_conv": math.fsum(assessed.gains),
        "normalized_nash_conv": normalized_quality(layout, math.fsum(assessed.gains)),
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
        "minimum_cap_slack": minimum_cap_slack,
        "cap_feasible": assessed.cap_feasible,
        "epigraph_allowance": epigraph_allowance,
        "maximum_epigraph_violation": assessed.maximum_epigraph_violation,
        "epigraph_violating_players": list(assessed.epigraph_violating_players),
        "epigraph_closed": assessed.epigraph_closed,
    }


def _run_target(
    parsed: Mapping[str, Any],
    source_parent: Mapping[str, Any],
    optimizer_parent: Mapping[str, Any],
    cp: Any,
    barrier: QualityLabelBarrier,
) -> dict[str, Any]:
    cp.cuda.runtime.deviceSynchronize()
    setup_started = time.perf_counter()
    objects = _setup(parsed, source_parent, parsed["target"])
    cp.cuda.runtime.deviceSynchronize()
    cold_setup_ms = (time.perf_counter() - setup_started) * 1000.0
    layout = objects["layout"]
    belief = objects["belief"]
    blueprint = objects["blueprint"]
    context = objects["context"]
    shared = objects["shared"]
    acting_player = int(parsed["acting_player"])

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
        raise AssertionError("retreat-quality warm step emitted no work ledger")
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
                maximum_feature_width_per_batch=int(parsed["maximum_feature_width_per_batch"]),
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
    if not topology.passed:
        raise AssertionError("retreat-quality behavioral shortcut topology failed")
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
    first_summary = _oracle_quality_summary(
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
            raise ArithmeticError("retreat-quality invariant acting row is violated")
        signature = first_oracle["response_signatures"][player]
        if signature in row_libraries[player]:
            raise ArithmeticError("retreat-quality exact duplicate response remains violated")
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
    if int(bool(cut_rows)) != int(parsed["maximum_cut_rounds"]):
        raise RuntimeError("retreat-quality reconstruction did not use exactly one cut round")

    second_master = solve_master()
    endpoint_policy, second_projection_error = axis.policy_from_variables(
        second_master.variables,
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

    optimizer_target = optimizer_parent["target"]
    optimizer_identity_checks = {
        "blueprint_policy": policy_digest(blueprint)
        == parsed["expected_blueprint_policy_sha256"],
        "parent_blueprint_policy": optimizer_target["restricted_blueprint_policy_sha256"]
        == parsed["expected_blueprint_policy_sha256"],
        "first_candidate_policy": first_oracle["policy_sha256"]
        == parsed["expected_first_candidate_policy_sha256"],
        "cut_players": [row["target_player"] for row in cut_rows]
        == parsed["expected_cut_players"],
        "cut_response_signatures": [
            row["response_signature_sha256"] for row in cut_rows
        ]
        == parsed["expected_cut_response_signatures"],
        "row_counts": [len(rows) for rows in row_libraries]
        == parsed["expected_row_counts_by_player"],
        "endpoint_policy": policy_digest(endpoint_policy)
        == parsed["expected_endpoint_policy_sha256"],
        "retreat_policy": policy_digest(retreat_policy)
        == parsed["expected_retreat_policy_sha256"],
        "initial_lower_bound": abs(
            float(first_master.lower_bound) - float(parsed["expected_initial_lower_bound"])
        )
        <= float(parsed["bound_reproduction_tolerance"]),
        "final_lower_bound": abs(
            float(second_master.lower_bound) - float(parsed["expected_final_lower_bound"])
        )
        <= float(parsed["bound_reproduction_tolerance"]),
        "source_nash_conv": abs(
            source_nash_conv - float(parsed["expected_source_nash_conv"])
        )
        <= float(parsed["quality_numerical_allowance"]),
        "parent_endpoint_policy": optimizer_target["final_oracle"]["policy_sha256"]
        == parsed["expected_endpoint_policy_sha256"],
        "parent_retreat_policy": optimizer_target["retreat"]["policy_sha256"]
        == parsed["expected_retreat_policy_sha256"],
        "parent_cut_players": [
            row["target_player"] for row in optimizer_target["cut_rows"]
        ]
        == parsed["expected_cut_players"],
        "parent_row_counts": optimizer_target["row_counts_by_player"]
        == parsed["expected_row_counts_by_player"],
    }
    barrier.freeze_candidate(optimizer_identity_checks)

    retreat_oracle = _exact_oracle(
        objects=objects,
        policy=retreat_policy,
        cp=cp,
        maximum_feature_width_per_batch=int(parsed["maximum_feature_width_per_batch"]),
    )
    retreat_summary = _oracle_quality_summary(
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
    endpoint_upper = float(optimizer_target["incumbent_upper_bound"])
    eta = float(parsed["interior_retreat_factor"])
    jensen_ceiling = (1.0 - eta) * source_nash_conv + eta * endpoint_upper
    required_interior_slack = max(
        0.0,
        (1.0 - eta) * guard - float(parsed["cap_numerical_allowance"]),
    )

    masters = [_master_summary(first_master), _master_summary(second_master)]
    master_ms = math.fsum(row["solve_ms"] for row in masters)
    oracle_ms = float(first_oracle["wall_ms"]) + float(retreat_oracle["wall_ms"])
    measured_live_ms = (
        warm_step_ms
        + initial_row_ms
        + master_ms
        + oracle_ms
        + cut_extraction_ms
        + max(
            retreat_construction_ms,
            float(parsed["retreat_envelope_reserve_ms"]),
        )
        + float(parsed["emission_reserve_ms"])
    )
    conservative_live_ms = float(parsed["conservative_live_ledger_ms"])
    maximum_pool = max(
        max(row["gpu_pool_total_bytes"] for row in memory_rows),
        max(row["maximum_gpu_pool_total_bytes"] for row in initial_pass_rows),
        max(row["maximum_gpu_pool_total_bytes"] for row in cut_rows),
        int(first_oracle["maximum_gpu_pool_total_bytes"]),
        int(retreat_oracle["maximum_gpu_pool_total_bytes"]),
    )
    minimum_free = min(row["gpu_free_bytes"] for row in memory_rows)
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

    result = {
        "target_id": parsed["target"]["target_id"],
        "acting_player": acting_player,
        "acting_public_nodes": len(axis.acting_nodes),
        "path_single_visit": topology.passed,
        "behavioral_information_sets": len(axis.information_sets),
        "policy_variables": axis.variable_count,
        "epigraph_variables": layout.num_players,
        "payoff_span": payoff_span(layout),
        "payoff_span_source": "layout.game.payoff_span",
        "raw_guard": guard,
        "source_nash_conv": source_nash_conv,
        "caps": list(caps),
        "caps_sha256": hashlib.sha256(
            np.asarray(caps, dtype=np.float64).tobytes(order="C")
        ).hexdigest(),
        "cold_setup_ms": cold_setup_ms,
        "warm_start_distance": warm_distance,
        "warm_step": warm_work,
        "initial_profile_passes": sum(
            row["kind"] == "profile" for row in initial_pass_rows
        ),
        "initial_response_passes": sum(
            row["kind"] == "fixed_response" for row in initial_pass_rows
        ),
        "initial_gain_rows": sum(len(rows) for rows in row_libraries)
        - len(cut_rows),
        "initial_row_ms": initial_row_ms,
        "initial_pass_rows": initial_pass_rows,
        "maximum_initial_row_error": max(source_row_errors),
        "masters": masters,
        "first_candidate_projection_error": first_projection_error,
        "second_candidate_projection_error": second_projection_error,
        "first_oracle": first_summary,
        "cut_rounds": 1,
        "cut_rows": cut_rows,
        "cut_extraction_ms": cut_extraction_ms,
        "maximum_cut_row_error": max(cut_identity_errors),
        "row_counts_by_player": [len(rows) for rows in row_libraries],
        "maximum_profile_equivalence_error": max(profile_equivalence_errors),
        "maximum_master_primal_error": maximum_master_primal,
        "maximum_master_dual_error": maximum_master_dual,
        "optimizer_identity_checks": optimizer_identity_checks,
        "endpoint": {
            "policy_sha256": policy_digest(endpoint_policy),
            "lower_bound": float(second_master.lower_bound),
            "independently_recertified_in_this_trial": False,
            "quality_label_opened_in_this_trial": False,
            "emitted": False,
        },
        "retreat": {
            "factor": eta,
            "policy_sha256": policy_digest(retreat_policy),
            "maximum_simplex_mass_error": retreat_mass_error,
            "construction_ms": retreat_construction_ms,
            "exact_certificate": retreat_summary,
            "exact_positive_value": exact_positive_value,
            "jensen_objective_ceiling": jensen_ceiling,
            "jensen_bound_passed": float(retreat_summary["nash_conv"])
            <= jensen_ceiling + float(parsed["quality_numerical_allowance"]),
            "required_interior_slack": required_interior_slack,
            "interior_slack_passed": float(retreat_summary["minimum_cap_slack"])
            >= required_interior_slack,
            "independently_certified": True,
            "shadow_accepted": bool(
                retreat_summary["cap_feasible"]
                and exact_positive_value > float(parsed["quality_numerical_allowance"])
            ),
            "emitted": False,
        },
        "exact_oracles_executed": 2,
        "oracle_targets": ["first_master_candidate", "factor_0.5_retreat"],
        "ledger": {
            "measured_live_ms": measured_live_ms,
            "measured_headroom_ms": float(parsed["street_budget_ms"])
            - measured_live_ms,
            "conservative_live_ms": conservative_live_ms,
            "conservative_headroom_ms": float(parsed["street_budget_ms"])
            - conservative_live_ms,
            "fits_measured_street": measured_live_ms
            <= float(parsed["street_budget_ms"]),
            "fits_conservative_street": conservative_live_ms
            <= float(parsed["street_budget_ms"]),
            "components_ms": {
                "warm_step": warm_step_ms,
                "initial_rows": initial_row_ms,
                "masters": master_ms,
                "first_oracle": float(first_oracle["wall_ms"]),
                "retreat_oracle": float(retreat_oracle["wall_ms"]),
                "cut_extraction": cut_extraction_ms,
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
        "source_checkpoint_identity": axis_cfr_checkpoint_digest(objects["state"])
        == objects["state"]["state_sha256"]
        and _belief_digest(objects["source"])
        == parsed["target"]["source_belief_sha256"],
        "target_identity": _belief_digest(belief)
        == parsed["target"]["target_belief_sha256"],
        "blueprint_identity": policy_digest(objects["full_blueprint"])
        == objects["state"]["average_policy_sha256"],
        "exact_external_axis_coverage": external_axis_splices
        == (layout.num_players - 1) + len(cut_rows),
        "external_axis_splices": external_axis_splices,
        "barrier_at_certificate": barrier.snapshot(),
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


def _extract_fallback_comparator(
    artifact: Mapping[str, Any], parsed: Mapping[str, Any]
) -> tuple[dict[str, Any], dict[str, bool]]:
    target_rows = artifact.get("target_rows")
    if not isinstance(target_rows, list):
        raise ValueError("fallback artifact lacks target_rows")
    targets = [
        row
        for row in target_rows
        if isinstance(row, Mapping)
        and row.get("target_id") == parsed["target"]["target_id"]
    ]
    if len(targets) != 1:
        raise ValueError("fallback artifact does not contain one frozen target")
    arms = targets[0].get("arms")
    if not isinstance(arms, list):
        raise ValueError("fallback target lacks arms")
    matches = [
        arm
        for arm in arms
        if isinstance(arm, Mapping)
        and arm.get("depth") == parsed["expected_fallback_depth"]
    ]
    if len(matches) != 1:
        raise ValueError("fallback artifact does not contain one frozen depth arm")
    arm = matches[0]
    teacher = arm.get("teacher")
    quality = teacher.get("quality") if isinstance(teacher, Mapping) else None
    if not isinstance(teacher, Mapping) or not isinstance(quality, Mapping):
        raise ValueError("fallback depth arm lacks its sealed exact teacher")
    comparator = {
        "target_id": targets[0]["target_id"],
        "depth": arm["depth"],
        "block_manifest_count": arm["block_manifest_count"],
        "restricted_blueprint_policy_sha256": arm[
            "restricted_blueprint_policy_sha256"
        ],
        "raw_guard": float(arm["raw_guard"]),
        "payoff_span": float(arm["payoff_span"]),
        "blueprint_nash_conv": float(arm["blueprint_quality"]["nash_conv"]),
        "candidate_id": teacher["candidate_id"],
        "policy_sha256": teacher["policy_sha256"],
        "exact_positive_value": float(teacher["exact_positive_value"]),
        "nash_conv": float(quality["nash_conv"]),
        "charged_ledger_ms": float(teacher["charged_ledger_ms"]),
        "accepted_by_shadow_rule": teacher["accepted_by_shadow_rule"],
        "complete": teacher["complete"],
        "independent_incremental_certificate": teacher[
            "independent_incremental_certificate"
        ],
        "usable_before_emission_cutoff": teacher["usable_before_emission_cutoff"],
    }
    allowance = float(parsed["quality_numerical_allowance"])
    checks = {
        "artifact_passed": artifact_passed(artifact),
        "target": comparator["target_id"] == parsed["target"]["target_id"],
        "depth": comparator["depth"] == parsed["expected_fallback_depth"],
        "blocks": comparator["block_manifest_count"]
        == parsed["expected_fallback_blocks"],
        "blueprint": comparator["restricted_blueprint_policy_sha256"]
        == parsed["expected_blueprint_policy_sha256"],
        "raw_guard": abs(comparator["raw_guard"] - 3e-9) <= 1e-18,
        "payoff_span": comparator["payoff_span"] == 30.0,
        "candidate": comparator["candidate_id"]
        == parsed["expected_fallback_candidate_id"],
        "policy": comparator["policy_sha256"]
        == parsed["expected_fallback_policy_sha256"],
        "blueprint_quality": abs(
            comparator["blueprint_nash_conv"]
            - float(parsed["expected_source_nash_conv"])
        )
        <= allowance,
        "value_identity": abs(
            comparator["blueprint_nash_conv"]
            - comparator["nash_conv"]
            - comparator["exact_positive_value"]
        )
        <= allowance,
        "positive_value": comparator["exact_positive_value"] > allowance,
        "ledger": 0.0
        < comparator["charged_ledger_ms"]
        <= float(parsed["street_budget_ms"]),
        "accepted": comparator["accepted_by_shadow_rule"] is True,
        "complete": comparator["complete"] is True,
        "certificate": comparator["independent_incremental_certificate"] is True,
        "deadline": comparator["usable_before_emission_cutoff"] is True,
    }
    return comparator, checks


def run_h32_one_seat_retreat_quality_trial(
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
    optimizer = load_artifact(
        _OPTIMIZER,
        expected_sha256=parsed["expected_optimizer_result_sha256"],
        require_passed=True,
    ).payload
    barrier = QualityLabelBarrier()
    target = _run_target(parsed, source, optimizer, cp, barrier)

    barrier.open_sealed_comparator()
    fallback_artifact = load_artifact(
        _FALLBACK,
        expected_sha256=parsed["expected_fallback_result_sha256"],
        require_passed=True,
    ).payload
    fallback, fallback_checks = _extract_fallback_comparator(
        fallback_artifact,
        parsed,
    )
    comparison = adjudicate_retreat_replication(
        retreat_value=float(target["retreat"]["exact_positive_value"]),
        retreat_conservative_ledger_ms=float(target["ledger"]["conservative_live_ms"]),
        fallback_value=float(fallback["exact_positive_value"]),
        fallback_ledger_ms=float(fallback["charged_ledger_ms"]),
        raw_guard_value=float(target["raw_guard"]),
    )
    total_seconds = time.perf_counter() - started
    strategy_population_claim = None
    gate = parsed["gates"]
    masters = target["masters"]
    optimizer_identity = target["optimizer_identity_checks"]
    retreat = target["retreat"]
    certificate = retreat["exact_certificate"]
    checks = {
        "clean_git": (not git["dirty"]) == gate["require_clean_git_state"],
        "parents_passed": all(
            artifact_passed(row) for row in (source, optimizer, fallback_artifact)
        )
        == gate["require_parents_passed"],
        "target_identity": bool(
            target["source_checkpoint_identity"] and target["target_identity"]
        )
        == gate["require_target_identity"],
        "blueprint_identity": bool(target["blueprint_identity"])
        == gate["require_blueprint_identity"],
        "warm_start_identity": (
            target["warm_start_distance"]["maximum_probability_error"]
            <= gate["maximum_warm_start_probability_error"]
            and target["warm_start_distance"]["mean_total_variation"]
            <= gate["maximum_warm_start_mean_total_variation"]
        )
        == gate["require_warm_start_identity"],
        "path_single_visit": target["path_single_visit"]
        == gate["require_path_single_visit"],
        "acting_node_count": target["acting_public_nodes"]
        == gate["expected_acting_public_nodes"],
        "information_set_count": target["behavioral_information_sets"]
        == gate["expected_behavioral_information_sets"],
        "policy_variable_count": target["policy_variables"]
        == gate["expected_policy_variables"],
        "epigraph_variable_count": target["epigraph_variables"]
        == gate["expected_epigraph_variables"],
        "initial_profile_pass_count": target["initial_profile_passes"]
        == gate["expected_initial_profile_passes"],
        "initial_response_pass_count": target["initial_response_passes"]
        == gate["expected_initial_response_passes"],
        "initial_gain_row_count": target["initial_gain_rows"]
        == gate["expected_initial_gain_rows"],
        "initial_row_identity": target["maximum_initial_row_error"]
        <= gate["maximum_initial_row_error"],
        "cut_row_count": len(target["cut_rows"]) == gate["expected_cut_rows"],
        "cut_row_identity": target["maximum_cut_row_error"]
        <= gate["maximum_cut_row_error"],
        "profile_equivalence": target["maximum_profile_equivalence_error"]
        <= gate["maximum_profile_equivalence_error"],
        "master_primal": target["maximum_master_primal_error"]
        <= gate["maximum_master_primal_error"],
        "master_dual": target["maximum_master_dual_error"]
        <= gate["maximum_master_dual_error"],
        "candidate_projection": max(
            target["first_candidate_projection_error"],
            target["second_candidate_projection_error"],
        )
        <= gate["maximum_projection_error"],
        "raw_guard": abs(target["raw_guard"] - 3e-9)
        <= gate["maximum_raw_guard_error"],
        "cold_setup_time": target["cold_setup_ms"] <= gate["maximum_cold_setup_ms"],
        "warm_step_time": target["warm_step"]["wall_ms"]
        <= gate["maximum_warm_step_ms"],
        "initial_row_time": target["initial_row_ms"]
        <= gate["maximum_initial_row_ms"],
        "master_time": max(row["solve_ms"] for row in masters)
        <= gate["maximum_master_ms"],
        "oracle_time": max(
            target["first_oracle"]["wall_ms"], certificate["wall_ms"]
        )
        <= gate["maximum_oracle_ms"],
        "cut_extraction_time": target["cut_extraction_ms"]
        <= gate["maximum_cut_extraction_ms"],
        "gpu_pool": target["maximum_gpu_pool_total_bytes"]
        <= gate["maximum_gpu_pool_bytes"],
        "physical_free": target["minimum_gpu_free_bytes"]
        >= gate["minimum_physical_free_bytes"],
        "external_axis_coverage": target["exact_external_axis_coverage"]
        == gate["require_exact_external_axis_coverage"],
        "optimizer_identity": all(optimizer_identity.values())
        == gate["require_optimizer_identity"],
        "exact_oracle_count": target["exact_oracles_executed"]
        == gate["expected_exact_oracles"],
        "retreat_exact_certificate": bool(retreat["independently_certified"])
        == gate["require_retreat_exact_certificate"],
        "retreat_cap_feasible": bool(certificate["cap_feasible"])
        == gate["require_retreat_cap_feasible"],
        "retreat_positive_value": (
            retreat["exact_positive_value"]
            > float(parsed["quality_numerical_allowance"])
        )
        == gate["require_retreat_positive_value"],
        "retreat_jensen_bound": bool(retreat["jensen_bound_passed"])
        == gate["require_retreat_jensen_bound"],
        "retreat_interior_slack": bool(retreat["interior_slack_passed"])
        == gate["require_retreat_interior_slack"],
        "fallback_identity": all(fallback_checks.values())
        == gate["require_fallback_identity"],
        "label_barrier": barrier.events
        == [
            "inputs_pinned",
            "candidate_frozen",
            "retreat_certificate_complete",
            "sealed_comparator_opened",
        ]
        and gate["require_label_barrier"],
        "measured_street_fit": bool(target["ledger"]["fits_measured_street"])
        == gate["require_measured_street_fit"],
        "conservative_street_fit": bool(
            target["ledger"]["fits_conservative_street"]
        )
        == gate["require_conservative_street_fit"],
        "blueprint_external_emission": (
            target["actual_emitted_policy_sha256"]
            == target["restricted_blueprint_policy_sha256"]
            and target["candidate_policies_emitted"] == 0
        )
        == gate["require_blueprint_external_emission"],
        "single_new_strategy_label": (
            target["new_strategy_quality_labels_generated"] == 1
        )
        == gate["require_single_new_strategy_label"],
        "no_population_claim": (strategy_population_claim is None)
        == gate["require_no_population_claim"],
        "total_time": total_seconds <= gate["maximum_total_seconds"],
        "finite": bool(
            _finite_tree(target)
            and _finite_tree(fallback)
            and _finite_tree(comparison)
        )
        == gate["require_finite"],
    }
    gate_result = finalize_gates(checks)
    promote = bool(
        gate_result["passed"]
        and retreat["shadow_accepted"]
        and comparison["authorizes_fresh_target_replication"]
    )
    result = {
        "schema_version": 1,
        "status": "h32_one_seat_retreat_quality_trial_executed",
        "environment": assemble_environment(runtime=runtime, git=git),
        "config_sha256": _sha256(config_path),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "methodology": {
            "targets": 1,
            "acting_seats": 1,
            "cut_rounds": 1,
            "exact_oracles": 2,
            "new_strategy_quality_labels": 1,
            "sealed_comparator_labels_reused": 1,
            "candidate_policies_emitted": 0,
        },
        "feature_label_barrier": {
            **barrier.snapshot(),
            "fallback_bytes_sha256_pinned_before_run": True,
            "fallback_json_deserialized_after_retreat_certificate": True,
        },
        "target": target,
        "fallback_comparator": fallback,
        "fallback_identity_checks": fallback_checks,
        "comparison": comparison,
        "aggregate": {
            "retreat_nash_conv": certificate["nash_conv"],
            "retreat_exact_positive_value": retreat["exact_positive_value"],
            "fallback_nash_conv": fallback["nash_conv"],
            "fallback_exact_positive_value": fallback["exact_positive_value"],
            "value_difference": comparison["value_difference"],
            "value_rate_ratio": comparison["value_rate_ratio"],
            "retreat_minimum_cap_slack": certificate["minimum_cap_slack"],
            "measured_live_ms": target["ledger"]["measured_live_ms"],
            "conservative_live_ms": target["ledger"]["conservative_live_ms"],
            "authorize_fresh_target_replication": promote,
        },
        **gate_result,
        "decision": (
            "authorize_preregistered_fresh_target_retreat_replication"
            if promote
            else "retain_one_step_31_block_fallback_and_reject_fresh_retreat_replication"
            if gate_result["passed"]
            else "reject_retreat_quality_execution"
        ),
        "actual_emitted_policy": "immutable_restricted_blueprint_only",
        "strategy_quality_claim": (
            "single_retained_target_shadow_exact_value_only"
            if gate_result["passed"]
            else None
        ),
        "strategy_population_claim": strategy_population_claim,
        "total_seconds": total_seconds,
        "limitations": [
            (
                "This is one known retained target selected for the preceding optimizer "
                "gate, not fresh transfer evidence."
            ),
            (
                "The endpoint is reconstructed by frozen identity but is not independently "
                "recertified or quality-labeled in this trial."
            ),
            (
                "The retreat certificate authorizes shadow comparison only; actual external "
                "emission remains the immutable blueprint."
            ),
            (
                "No safety composition, multi-seat, cross-street, population, deployment, "
                "or broad poker-strength claim is made."
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
    result = run_h32_one_seat_retreat_quality_trial(args.config, args.output)
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
