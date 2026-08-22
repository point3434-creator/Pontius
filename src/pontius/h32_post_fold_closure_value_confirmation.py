"""Fresh post-fold confirmation of current-decision closure and safe value."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from dataclasses import dataclass, field
import gc
import hashlib
import json
import math
from pathlib import Path
import time
from typing import Any, Iterator, Mapping

import numpy as np

from . import h32_fresh_convex_retreat_replication as core
from .axis_cfr_checkpoint import axis_cfr_checkpoint_digest
from .behavioral_one_seat_master import (
    solve_behavioral_one_seat_master as canonical_master_solve,
)
from .cupy_sparse_incidence import release_cupy_memory_pool
from .fresh_h32_strategy_transfer_audit import _belief_digest
from .h32_affine_resident_cache_preflight import _strict_git_metadata, _validate_runtime
from .h32_continuation_root_ledger import _setup as historical_setup
from .h32_decision_aligned_live_shadow_trial import (
    _manifest_target_specs,
    _parse_config as parse_decision_aligned_shadow_config,
    decision_aligned_transfer_assessment,
)
from .h32_fresh_union_value_audit import _memory_snapshot
from .h32_one_round_convex_master import (
    _mix_policy as canonical_mix_policy,
    bounded_gap,
)
from .h32_post_fold_current_decision_setup import (
    build_post_fold_current_decision_setup,
    post_fold_core_setup_adapter,
)
from .payoff_semantics import payoff_span, raw_guard
from .real_policy import policy_digest
from .runner_harness import (
    artifact_passed,
    assemble_environment,
    finalize_gates,
    load_artifact,
    serialize_result,
)


_ROOT = Path(__file__).parents[2]
_CONFIG = (
    _ROOT / "experiments/configs/h32-post-fold-closure-value-confirmation-v1.json"
)
_OUTPUT = (
    _ROOT / "experiments/results/h32-post-fold-closure-value-confirmation-v1.json"
)
_BASE_CONFIG = (
    _ROOT / "experiments/configs/h32-decision-aligned-live-shadow-v1.json"
)
_SOURCE = _ROOT / "experiments/results/h32-fresh-panel-source-blueprints-v1.json"
_MANIFEST = _ROOT / "experiments/results/h32-post-fold-posterior-manifest-v1.json"
_MANIFEST_DECISION = (
    _ROOT
    / "docs/decisions/ADR-0266-post-fold-panel-is-fresh-current-and-held-label-blind.md"
)
_LEDGER_RESULT = (
    _ROOT / "experiments/results/h32-current-decision-combined-ledger-replay-v1.json"
)
_LEDGER_DECISION = (
    _ROOT
    / "docs/decisions/ADR-0272-current-decision-closure-and-safe-retreat-fit-one-street.md"
)
_CORE_IMPLEMENTATION = (
    _ROOT / "src/pontius/h32_fresh_convex_retreat_replication.py"
)
_BASE_RUNNER = _ROOT / "src/pontius/h32_decision_aligned_live_shadow_trial.py"
_SETUP_IMPLEMENTATION = (
    _ROOT / "src/pontius/h32_post_fold_current_decision_setup.py"
)
_IMPLEMENTATION = Path(__file__)
_TEST = _ROOT / "tests/test_h32_post_fold_closure_value_confirmation.py"

_PATHS = {
    "expected_base_config_sha256": _BASE_CONFIG,
    "expected_source_parent_sha256": _SOURCE,
    "expected_post_fold_manifest_sha256": _MANIFEST,
    "expected_post_fold_manifest_decision_sha256": _MANIFEST_DECISION,
    "expected_combined_ledger_result_sha256": _LEDGER_RESULT,
    "expected_combined_ledger_decision_sha256": _LEDGER_DECISION,
    "expected_core_implementation_sha256": _CORE_IMPLEMENTATION,
    "expected_base_runner_sha256": _BASE_RUNNER,
    "expected_setup_implementation_sha256": _SETUP_IMPLEMENTATION,
    "expected_runner_harness_sha256": _ROOT / "src/pontius/runner_harness.py",
    "expected_implementation_sha256": _IMPLEMENTATION,
    "expected_control_test_sha256": _TEST,
}


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required post-fold confirmation input is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _epigraph_sha256(values: tuple[float, ...]) -> str:
    return hashlib.sha256(
        np.asarray(values, dtype=np.float64).tobytes(order="C")
    ).hexdigest()


def _copy_policy(
    policy: Mapping[str, Mapping[Any, float]],
) -> dict[str, dict[Any, float]]:
    return {
        key: {action: float(value) for action, value in row.items()}
        for key, row in policy.items()
    }


@dataclass(slots=True)
class ConstructionCapture:
    """Capture sealed-core outputs that its historical bundle did not retain."""

    endpoint_policies: list[dict[str, dict[Any, float]]] = field(
        default_factory=list
    )
    master_epigraphs: list[tuple[float, ...]] = field(default_factory=list)


@contextmanager
def capture_sealed_core_construction() -> Iterator[ConstructionCapture]:
    """Capture exact endpoint and epigraph values without changing core math."""

    if core._mix_policy is not canonical_mix_policy:
        raise RuntimeError("sealed core mix function was already replaced")
    if core.solve_behavioral_one_seat_master is not canonical_master_solve:
        raise RuntimeError("sealed core master function was already replaced")
    capture = ConstructionCapture()

    def captured_mix(blueprint, endpoint, *, eta):
        capture.endpoint_policies.append(_copy_policy(endpoint))
        return canonical_mix_policy(blueprint, endpoint, eta=eta)

    def captured_master(*args, **kwargs):
        solution = canonical_master_solve(*args, **kwargs)
        capture.master_epigraphs.append(
            tuple(float(value) for value in solution.epigraph)
        )
        return solution

    core._mix_policy = captured_mix
    core.solve_behavioral_one_seat_master = captured_master
    try:
        yield capture
    finally:
        core._mix_policy = canonical_mix_policy
        core.solve_behavioral_one_seat_master = canonical_master_solve


def attach_construction_capture(
    bundle: Mapping[str, Any],
    capture: ConstructionCapture,
) -> dict[str, Any]:
    """Verify captured values against sealed digests and attach them to a bundle."""

    row = bundle["construction_row"]
    if len(capture.endpoint_policies) != 1:
        raise RuntimeError("post-fold construction did not expose exactly one endpoint")
    if len(capture.master_epigraphs) != len(row["masters"]):
        raise RuntimeError("post-fold construction master capture count changed")
    endpoint = capture.endpoint_policies[0]
    if policy_digest(endpoint) != row["endpoint_policy_sha256"]:
        raise RuntimeError("captured endpoint differs from sealed construction")
    for epigraph, master in zip(
        capture.master_epigraphs,
        row["masters"],
        strict=True,
    ):
        if _epigraph_sha256(epigraph) != master["epigraph_sha256"]:
            raise RuntimeError("captured epigraph differs from sealed construction")
    return {
        **bundle,
        "endpoint_policy": endpoint,
        "final_epigraph": capture.master_epigraphs[-1],
        "construction_capture": {
            "endpoint_policy_sha256": policy_digest(endpoint),
            "master_epigraph_sha256": [
                _epigraph_sha256(values) for values in capture.master_epigraphs
            ],
            "master_count": len(capture.master_epigraphs),
        },
    }


def _parse_config(config: dict[str, Any]) -> dict[str, Any]:
    expected = {
        "evidence_stage",
        *_PATHS,
        "seed",
        "target_selection_rule",
        "target_specs",
        "inheritance_rule",
        "setup_rule",
        "adapter_rule",
        "capture_rule",
        "campaign_barrier_rule",
        "endpoint_rule",
        "retreat_rule",
        "ledger_rule",
        "promotion_rule",
        "strategy_label_policy",
        "success_decision",
        "claims_policy",
        "incremental_endpoint_oracle_ceiling_ms",
        "incremental_endpoint_oracle_conservative_charge_ms",
        "endpoint_bound_tolerance",
        "confirmation_gates",
    }
    if set(config) != expected:
        raise ValueError("post-fold confirmation fields differ from ADR-0273")
    for field_name, path in _PATHS.items():
        if config[field_name] != _sha256(path):
            raise ValueError(f"post-fold confirmation provenance mismatch: {field_name}")
    base = parse_decision_aligned_shadow_config(
        json.loads(_BASE_CONFIG.read_text(encoding="utf-8"))
    )
    manifest = json.loads(_MANIFEST.read_text(encoding="utf-8"))
    frozen_specs = _manifest_target_specs(manifest)
    exact = {
        "evidence_stage": (
            "preregistered_after_adr0272_before_any_post_fold_warm_step_"
            "optimizer_or_strategy_label"
        ),
        "seed": 20260822,
        "target_selection_rule": (
            "all_six_adr0266_post_fold_targets_in_manifest_order_zero_value_"
            "timing_facet_or_position_selection"
        ),
        "target_specs": frozen_specs,
        "inheritance_rule": (
            "byte_pinned_adr0263_current_decision_algorithm_and_tolerances_"
            "with_only_post_fold_setup_and_post_cut_endpoint_certificate_added"
        ),
        "setup_rule": (
            "reconstruct_checks_bet_first_fold_posterior_require_declared_actor_"
            "current_with_three_downstream_responders"
        ),
        "adapter_rule": (
            "temporarily_replace_only_sealed_core_setup_and_restore_on_success_"
            "or_failure"
        ),
        "capture_rule": (
            "scoped_exact_capture_of_existing_endpoint_argument_and_master_"
            "epigraph_outputs_digest_verified_and_restored"
        ),
        "campaign_barrier_rule": (
            "construct_capture_and_freeze_all_six_endpoints_and_retreats_before_"
            "any_post_cut_endpoint_or_final_retreat_label"
        ),
        "endpoint_rule": (
            "reuse_first_exact_oracle_when_zero_cut_otherwise_run_exactly_one_"
            "post_cut_endpoint_oracle_and_require_cap_epigraph_and_u_minus_l_"
            "closure"
        ),
        "retreat_rule": (
            "fixed_factor_0_5_independent_exact_all_seat_certificate_is_sole_"
            "safety_authority"
        ),
        "ledger_rule": (
            "complete_adr0264_measured_components_plus_post_cut_endpoint_oracle_"
            "and_13967_615699994712_ms_floor_plus_conditional_1000_ms_charge"
        ),
        "promotion_rule": (
            "confirm_only_if_all_six_globally_close_all_six_retreats_are_safe_"
            "positive_and_at_least_four_exceed_0_001_with_both_families"
        ),
        "strategy_label_policy": (
            "six_fixed_fresh_post_fold_paths_global_post_construction_barrier_"
            "no_cross_target_adaptation_immutable_blueprint_emission"
        ),
        "success_decision": (
            "accept_fresh_post_fold_closure_and_value_confirmation_and_authorize_"
            "current_decision_direction_demotion_review"
        ),
        "claims_policy": (
            "fresh_fixed_panel_current_decision_scope_only_no_population_"
            "deployment_multiseat_composition_chip_ev_or_poker_strength_claim"
        ),
        "incremental_endpoint_oracle_ceiling_ms": 1000.0,
        "incremental_endpoint_oracle_conservative_charge_ms": 1000.0,
        "endpoint_bound_tolerance": 1e-8,
    }
    for field_name, expected_value in exact.items():
        if config[field_name] != expected_value:
            raise ValueError(
                f"post-fold confirmation field differs from ADR-0273: {field_name}"
            )
    confirmation_gates = {
        "expected_targets": 6,
        "expected_sources": 6,
        "expected_bettors": 6,
        "expected_observed_responders": 6,
        "expected_acting_players": 6,
        "expected_candidates_frozen_before_labels": 6,
        "minimum_total_exact_oracles": 12,
        "maximum_total_exact_oracles": 18,
        "minimum_post_barrier_labels": 6,
        "maximum_post_barrier_labels": 12,
        "require_clean_git_state": True,
        "require_parents_passed": True,
        "require_manifest_authorized": True,
        "require_manifest_labels_zero": True,
        "require_combined_ledger_authorized": True,
        "require_manifest_order": True,
        "require_post_fold_only": True,
        "require_current_actor_rule": True,
        "require_setup_adapter_active": True,
        "require_setup_adapter_restored": True,
        "require_capture_restored": True,
        "require_capture_identity": True,
        "require_campaign_barrier_before_labels": True,
        "require_certificate_reconstruction_identity": True,
        "require_incremental_endpoint_ceiling": True,
        "require_measured_ledgers_fit": True,
        "require_conservative_ledgers_fit": True,
        "require_retreat_certificates_complete": True,
        "require_no_cross_target_adaptation": True,
        "require_blueprint_external_emission": True,
        "require_label_accounting": True,
        "require_population_claim_null": True,
        "require_finite": True,
    }
    if config["confirmation_gates"] != confirmation_gates:
        raise ValueError("post-fold confirmation gates differ from ADR-0273")
    return {
        **base,
        **{field_name: config[field_name] for field_name in _PATHS},
        **exact,
        "target_specs": tuple(dict(row) for row in config["target_specs"]),
        "scope": "six_fresh_post_fold_current_decision_one_seat_programs",
        "confirmation_gates": confirmation_gates,
    }


def _construct_target_candidate(
    parsed: Mapping[str, Any],
    source: Mapping[str, Any],
    spec: Mapping[str, Any],
    cp: Any,
) -> dict[str, Any]:
    with capture_sealed_core_construction() as capture:
        bundle = core._construct_target_candidate(parsed, source, spec, cp)
    return attach_construction_capture(bundle, capture)


def _certify_target_candidate(
    parsed: Mapping[str, Any],
    source_parent: Mapping[str, Any],
    bundle: Mapping[str, Any],
    cp: Any,
) -> dict[str, Any]:
    spec = bundle["spec"]
    construction_row = dict(bundle["construction_row"])
    endpoint_policy = bundle["endpoint_policy"]
    retreat_policy = bundle["retreat_policy"]
    profile_rows = bundle["profile_rows"]
    source_gains = tuple(float(value) for value in bundle["source_gains"])
    caps = tuple(float(value) for value in bundle["caps"])
    barrier = bundle["barrier"]
    gate = parsed["gates"]

    cp.cuda.runtime.deviceSynchronize()
    reconstruction_started = time.perf_counter()
    objects = core._setup(parsed, source_parent, spec)
    cp.cuda.runtime.deviceSynchronize()
    reconstruction_ms = (time.perf_counter() - reconstruction_started) * 1000.0
    layout = objects["layout"]
    context = objects["context"]
    belief = objects["belief"]
    blueprint = objects["blueprint"]
    reconstructed_source_gains = tuple(
        float(cache.source_evaluation.deviation_gain)
        for cache in context.response_caches
    )
    maximum_source_gain_error = max(
        abs(left - right)
        for left, right in zip(
            reconstructed_source_gains,
            source_gains,
            strict=True,
        )
    )
    reconstructed_caps = tuple(
        gain + raw_guard(layout, float(parsed["acceptance_guard_normalized"]))
        for gain in reconstructed_source_gains
    )
    maximum_cap_reconstruction_error = max(
        abs(left - right)
        for left, right in zip(reconstructed_caps, caps, strict=True)
    )
    reconstruction_checks = {
        "candidate_barrier_frozen": barrier.phase == "candidate_frozen",
        "source_checkpoint_identity": (
            axis_cfr_checkpoint_digest(objects["state"])
            == objects["state"]["state_sha256"]
            and _belief_digest(objects["source"]) == spec["source_belief_sha256"]
        ),
        "target_identity": _belief_digest(belief) == spec["target_belief_sha256"],
        "blueprint_identity": (
            policy_digest(objects["full_blueprint"])
            == objects["state"]["average_policy_sha256"]
            and policy_digest(blueprint)
            == construction_row["restricted_blueprint_policy_sha256"]
        ),
        "endpoint_policy_identity": (
            policy_digest(endpoint_policy)
            == construction_row["endpoint_policy_sha256"]
        ),
        "retreat_policy_identity": (
            policy_digest(retreat_policy)
            == construction_row["retreat"]["policy_sha256"]
        ),
        "payoff_span_identity": (
            payoff_span(layout) == float(construction_row["payoff_span"])
        ),
        "source_gain_identity": (
            maximum_source_gain_error <= gate["maximum_profile_equivalence_error"]
        ),
        "cap_identity": (
            maximum_cap_reconstruction_error
            <= gate["maximum_profile_equivalence_error"]
        ),
    }
    if not all(reconstruction_checks.values()):
        failed = sorted(
            key for key, value in reconstruction_checks.items() if not value
        )
        raise RuntimeError(
            f"post-fold certificate reconstruction changed before label: "
            f"{spec['target_id']}: {failed}"
        )
    reconstruction_memory = {
        "stage": "certificate_reconstruction",
        **_memory_snapshot(cp),
    }

    cut_rounds = int(construction_row["cut_rounds"])
    incremental_endpoint_ms = 0.0
    endpoint_profile_errors: list[float] = []
    endpoint_memory = None
    if cut_rounds:
        endpoint_oracle = core._exact_oracle(
            objects=objects,
            policy=endpoint_policy,
            cp=cp,
            maximum_feature_width_per_batch=int(
                parsed["maximum_feature_width_per_batch"]
            ),
        )
        endpoint_summary = core._oracle_summary(
            endpoint_oracle,
            layout=layout,
            caps=caps,
            cap_allowance=float(parsed["cap_numerical_allowance"]),
            epigraph=tuple(float(value) for value in bundle["final_epigraph"]),
            epigraph_allowance=float(parsed["epigraph_separation_allowance"]),
        )
        incremental_endpoint_ms = float(endpoint_oracle["wall_ms"])
        endpoint_profile_errors = [
            abs(
                profile_rows[player].value(endpoint_oracle["probabilities"])
                - endpoint_oracle["evaluations"][player].profile_utility
            )
            for player in range(layout.num_players)
        ]
        endpoint_memory = {"stage": "post_cut_endpoint_oracle", **_memory_snapshot(cp)}
    else:
        endpoint_summary = dict(construction_row["first_oracle"])
    endpoint_gap = bounded_gap(
        float(endpoint_summary["nash_conv"]),
        float(construction_row["masters"][-1]["lower_bound"]),
        tolerance=float(parsed["endpoint_bound_tolerance"]),
    )
    endpoint_within_ceiling = (
        not cut_rounds
        or incremental_endpoint_ms
        <= float(parsed["incremental_endpoint_oracle_ceiling_ms"])
    )
    endpoint_globally_closed = bool(
        endpoint_summary["cap_feasible"]
        and endpoint_summary["epigraph_closed"]
        and endpoint_gap <= float(parsed["endpoint_bound_tolerance"])
    )

    retreat_oracle = core._exact_oracle(
        objects=objects,
        policy=retreat_policy,
        cp=cp,
        maximum_feature_width_per_batch=int(parsed["maximum_feature_width_per_batch"]),
    )
    retreat_summary = core._oracle_summary(
        retreat_oracle,
        layout=layout,
        caps=caps,
        cap_allowance=float(parsed["cap_numerical_allowance"]),
    )
    barrier.complete_retreat_certificate()
    retreat_memory = {"stage": "retreat_oracle", **_memory_snapshot(cp)}
    retreat_profile_errors = [
        abs(
            profile_rows[player].value(retreat_oracle["probabilities"])
            - retreat_oracle["evaluations"][player].profile_utility
        )
        for player in range(layout.num_players)
    ]

    source_nash_conv = float(construction_row["source_nash_conv"])
    exact_positive_value = source_nash_conv - float(retreat_summary["nash_conv"])
    required_interior_slack = max(
        0.0,
        (1.0 - float(parsed["interior_retreat_factor"]))
        * float(construction_row["raw_guard"])
        - float(parsed["minimum_interior_slack_allowance"]),
    )
    components = dict(bundle["ledger_components_ms"])
    components["post_cut_endpoint_oracle"] = incremental_endpoint_ms
    components["retreat_oracle"] = float(retreat_oracle["wall_ms"])
    measured_live_ms = math.fsum(components.values())
    frozen_conservative_ms = float(parsed["frozen_conservative_live_ledger_ms"])
    conservative_incremental_ms = (
        float(parsed["incremental_endpoint_oracle_conservative_charge_ms"])
        if cut_rounds
        else 0.0
    )
    combined_conservative_ms = frozen_conservative_ms + conservative_incremental_ms
    effective_conservative_ms = max(combined_conservative_ms, measured_live_ms)
    fits_measured = measured_live_ms <= float(parsed["street_budget_ms"])
    fits_conservative = bool(
        effective_conservative_ms <= float(parsed["street_budget_ms"])
        and endpoint_within_ceiling
    )
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
    memory_rows = [
        *construction_row["memory_rows"],
        reconstruction_memory,
        *([endpoint_memory] if endpoint_memory is not None else []),
        retreat_memory,
    ]
    maximum_pool = max(
        int(construction_row["construction_maximum_gpu_pool_total_bytes"]),
        int(retreat_oracle["maximum_gpu_pool_total_bytes"]),
        *(int(row["gpu_pool_total_bytes"]) for row in memory_rows),
    )
    minimum_free = min(int(row["gpu_free_bytes"]) for row in memory_rows)
    construction_row["maximum_profile_equivalence_error"] = max(
        float(construction_row["maximum_profile_equivalence_error"]),
        max(endpoint_profile_errors, default=0.0),
        max(retreat_profile_errors),
    )
    construction_row["endpoint_certificate"] = {
        "oracle_source": (
            "post_cut_exact_oracle" if cut_rounds else "first_exact_oracle_reused"
        ),
        "exact_summary": endpoint_summary,
        "lower_bound": float(construction_row["masters"][-1]["lower_bound"]),
        "optimality_gap": endpoint_gap,
        "globally_closed": endpoint_globally_closed,
        "incremental_oracle_ms": incremental_endpoint_ms,
        "incremental_oracle_within_ceiling": endpoint_within_ceiling,
    }
    construction_row["endpoint_independently_certified"] = True
    construction_row["retreat"] = {
        **construction_row["retreat"],
        "exact_certificate": retreat_summary,
        "exact_positive_value": exact_positive_value,
        "required_interior_slack": required_interior_slack,
        "interior_slack_passed": interior_passed,
        "independently_certified": True,
        "acceptance_predicate_passed": acceptance_predicate_passed,
        "shadow_accepted": acceptance_predicate_passed,
        "combined_closure_and_value_passed": bool(
            acceptance_predicate_passed and endpoint_globally_closed
        ),
        "material_value": exact_positive_value
        > float(parsed["minimum_material_exact_value"]),
    }
    construction_row["certificate_reconstruction"] = {
        "wall_ms": reconstruction_ms,
        "excluded_from_live_ledger": True,
        "checks": reconstruction_checks,
        "maximum_source_gain_error": maximum_source_gain_error,
        "maximum_cap_reconstruction_error": maximum_cap_reconstruction_error,
    }
    construction_row["construction_capture"] = bundle["construction_capture"]
    construction_row["exact_oracles_executed"] = 2 + cut_rounds
    construction_row["oracle_targets"] = [
        "first_master_candidate",
        *(["post_cut_resolved_endpoint"] if cut_rounds else []),
        "factor_0.5_retreat",
    ]
    construction_row["ledger"] = {
        "measured_live_ms": measured_live_ms,
        "measured_headroom_ms": float(parsed["street_budget_ms"])
        - measured_live_ms,
        "frozen_conservative_base_ms": frozen_conservative_ms,
        "conservative_incremental_endpoint_charge_ms": conservative_incremental_ms,
        "combined_conservative_live_ms": combined_conservative_ms,
        "effective_conservative_live_ms": effective_conservative_ms,
        "effective_conservative_headroom_ms": float(parsed["street_budget_ms"])
        - effective_conservative_ms,
        "fits_measured_street": fits_measured,
        "fits_effective_conservative_street": fits_conservative,
        "components_ms": components,
    }
    construction_row["memory_rows"] = memory_rows
    construction_row["maximum_gpu_pool_total_bytes"] = maximum_pool
    construction_row["minimum_gpu_free_bytes"] = minimum_free
    construction_row["label_barrier"] = barrier.snapshot()
    construction_row["new_strategy_quality_labels_generated"] = 1 + cut_rounds

    objects.clear()
    gc.collect()
    release_cupy_memory_pool()
    return construction_row


def post_fold_confirmation_decision(
    *,
    process_passed: bool,
    all_globally_closed: bool,
    all_safe_positive: bool,
    transfers: bool,
) -> str:
    if not process_passed:
        return "reject_post_fold_closure_value_confirmation_execution"
    if not all_globally_closed:
        return "accept_execution_retain_direction_fallback_on_fresh_closure_failure"
    if not all_safe_positive or not transfers:
        return "accept_fresh_closure_retain_direction_fallback_on_value_failure"
    return (
        "accept_fresh_post_fold_closure_and_value_confirmation_and_authorize_"
        "current_decision_direction_demotion_review"
    )


def run_h32_post_fold_closure_value_confirmation(
    config_path: Path = _CONFIG,
    output_path: Path = _OUTPUT,
) -> dict[str, Any]:
    started = time.perf_counter()
    parsed = _parse_config(json.loads(config_path.read_text(encoding="utf-8")))
    git = _strict_git_metadata()
    if git["dirty"]:
        raise RuntimeError("post-fold confirmation requires a clean Git state")
    cp, runtime = _validate_runtime(parsed)
    source = load_artifact(
        _SOURCE,
        expected_sha256=parsed["expected_source_parent_sha256"],
        require_passed=True,
    ).payload
    manifest = load_artifact(
        _MANIFEST,
        expected_sha256=parsed["expected_post_fold_manifest_sha256"],
        require_passed=True,
    ).payload
    ledger = load_artifact(
        _LEDGER_RESULT,
        expected_sha256=parsed["expected_combined_ledger_result_sha256"],
        require_passed=True,
    ).payload

    campaign_events = ["inputs_pinned"]
    candidate_bundles = []
    adapter_active = False
    with post_fold_core_setup_adapter():
        adapter_active = core._setup is build_post_fold_current_decision_setup
        for spec in parsed["target_specs"]:
            candidate_bundles.append(
                _construct_target_candidate(parsed, source, spec, cp)
            )
            gc.collect()
            release_cupy_memory_pool()
        prelabel_snapshots = [
            bundle["barrier"].snapshot() for bundle in candidate_bundles
        ]
        candidates_frozen_before_labels = sum(
            row["phase"] == "candidate_frozen" for row in prelabel_snapshots
        )
        if candidates_frozen_before_labels != len(parsed["target_specs"]):
            raise RuntimeError("post-fold campaign did not freeze every candidate")
        if any(
            bundle["construction_row"]["new_strategy_quality_labels_generated"]
            != 0
            for bundle in candidate_bundles
        ):
            raise RuntimeError("post-fold final label opened before campaign barrier")
        campaign_events.append("all_candidates_frozen")
        target_rows = []
        for spec, bundle in zip(
            parsed["target_specs"],
            candidate_bundles,
            strict=True,
        ):
            row = _certify_target_candidate(parsed, source, bundle, cp)
            row.update(
                {
                    "observed_responder": spec["observed_responder"],
                    "observed_response": spec["observed_response"],
                    "public_prefix": spec["public_prefix"],
                    "root_current_player": spec["acting_player"],
                    "downstream_responders_after_actor": 3,
                }
            )
            target_rows.append(row)
            gc.collect()
            release_cupy_memory_pool()
        campaign_events.append("all_endpoint_and_retreat_certificates_complete")
    adapter_restored = core._setup is historical_setup
    capture_restored = bool(
        core._mix_policy is canonical_mix_policy
        and core.solve_behavioral_one_seat_master is canonical_master_solve
    )

    transfer = decision_aligned_transfer_assessment(
        target_rows,
        minimum_material_targets=int(parsed["minimum_material_targets"]),
        minimum_material_exact_value=float(parsed["minimum_material_exact_value"]),
    )
    all_globally_closed = all(
        row["endpoint_certificate"]["globally_closed"] for row in target_rows
    )
    all_safe_positive = all(
        row["retreat"]["shadow_accepted"]
        and row["retreat"]["exact_positive_value"] > 0.0
        for row in target_rows
    )
    total_seconds = time.perf_counter() - started
    gate = parsed["gates"]
    confirm = parsed["confirmation_gates"]
    fixed_ids = [row["target_id"] for row in parsed["target_specs"]]
    manifest_ids = [row["target_id"] for row in manifest["target_rows"]]
    total_exact_oracles = sum(row["exact_oracles_executed"] for row in target_rows)
    total_post_barrier_labels = sum(
        row["new_strategy_quality_labels_generated"] for row in target_rows
    )
    cut_rounds = sum(row["cut_rounds"] for row in target_rows)
    population_claim = None
    cross_target_adaptation = False
    checks = {
        "clean_git": (not git["dirty"]) == confirm["require_clean_git_state"],
        "parents_passed": all(
            artifact_passed(parent) for parent in (source, manifest, ledger)
        )
        == confirm["require_parents_passed"],
        "manifest_authorized": (
            manifest["decision"]
            == "seal_post_fold_identities_and_hold_strategy_labels_for_"
            "retrospective_closure_census"
        )
        == confirm["require_manifest_authorized"],
        "manifest_labels_zero": (manifest["methodology"]["strategy_labels"] == 0)
        == confirm["require_manifest_labels_zero"],
        "combined_ledger_authorized": (
            ledger["decision"]
            == "authorize_preregistered_post_fold_current_decision_closure_and_"
            "value_confirmation"
        )
        == confirm["require_combined_ledger_authorized"],
        "target_count": len(target_rows) == confirm["expected_targets"],
        "source_count": len({row["source"] for row in target_rows})
        == confirm["expected_sources"],
        "bettor_count": len({row["observed_bettor"] for row in target_rows})
        == confirm["expected_bettors"],
        "observed_responder_count": len(
            {row["observed_responder"] for row in target_rows}
        )
        == confirm["expected_observed_responders"],
        "acting_player_count": len({row["acting_player"] for row in target_rows})
        == confirm["expected_acting_players"],
        "manifest_order": fixed_ids == manifest_ids
        == [row["target_id"] for row in target_rows]
        and confirm["require_manifest_order"],
        "post_fold_only": all(
            row["round"] == "decision_aligned_fold_v1"
            and row["observed_response"] == "fold"
            for row in target_rows
        )
        == confirm["require_post_fold_only"],
        "current_actor_rule": all(
            row["observed_responder"] == (row["observed_bettor"] + 1) % 6
            and row["acting_player"] == (row["observed_bettor"] + 2) % 6
            and row["root_current_player"] == row["acting_player"]
            and row["downstream_responders_after_actor"] == 3
            for row in target_rows
        )
        == confirm["require_current_actor_rule"],
        "setup_adapter_active": adapter_active
        == confirm["require_setup_adapter_active"],
        "setup_adapter_restored": adapter_restored
        == confirm["require_setup_adapter_restored"],
        "capture_restored": capture_restored
        == confirm["require_capture_restored"],
        "capture_identity": all(
            row["construction_capture"]["endpoint_policy_sha256"]
            == row["endpoint_policy_sha256"]
            and row["construction_capture"]["master_epigraph_sha256"]
            == [master["epigraph_sha256"] for master in row["masters"]]
            for row in target_rows
        )
        == confirm["require_capture_identity"],
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
            row["acting_public_nodes"] == 1
            and row["behavioral_information_sets"]
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
            and row["initial_gain_rows"]
            == gate["expected_initial_gain_rows_per_target"]
            for row in target_rows
        ),
        "row_identity": all(
            row["maximum_initial_row_error"] <= gate["maximum_initial_row_error"]
            and row["maximum_cut_row_error"] <= gate["maximum_cut_row_error"]
            and row["maximum_resident_row_identity_error"]
            <= gate["maximum_resident_row_identity_error"]
            and row["maximum_resident_epigraph_residual"]
            <= gate["maximum_resident_epigraph_residual"]
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
        "certificate_reconstruction_time": max(
            row["certificate_reconstruction"]["wall_ms"] for row in target_rows
        )
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
            max(
                row["first_oracle"]["wall_ms"],
                row["endpoint_certificate"]["incremental_oracle_ms"],
                row["retreat"]["exact_certificate"]["wall_ms"],
            )
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
        "all_violators_accounted": all(
            row["all_first_oracle_violators_accounted"] for row in target_rows
        )
        == gate["require_all_first_oracle_violators_accounted"],
        "all_new_violators_cut": all(
            row["all_new_first_oracle_violators_cut"] for row in target_rows
        )
        == gate["require_all_new_first_oracle_violators_cut"],
        "maximum_one_cut_round": all(row["cut_rounds"] <= 1 for row in target_rows)
        == gate["require_maximum_one_cut_round"],
        "campaign_barrier_before_labels": (
            candidates_frozen_before_labels
            == confirm["expected_candidates_frozen_before_labels"]
            and campaign_events[:2] == ["inputs_pinned", "all_candidates_frozen"]
            and all(
                row["phase"] == "candidate_frozen"
                and row["events"] == ["inputs_pinned", "candidate_frozen"]
                for row in prelabel_snapshots
            )
        )
        == confirm["require_campaign_barrier_before_labels"],
        "certificate_reconstruction_identity": all(
            all(row["certificate_reconstruction"]["checks"].values())
            for row in target_rows
        )
        == confirm["require_certificate_reconstruction_identity"],
        "incremental_endpoint_ceiling": all(
            row["endpoint_certificate"]["incremental_oracle_within_ceiling"]
            for row in target_rows
        )
        == confirm["require_incremental_endpoint_ceiling"],
        "measured_ledgers_fit": all(
            row["ledger"]["fits_measured_street"] for row in target_rows
        )
        == confirm["require_measured_ledgers_fit"],
        "conservative_ledgers_fit": all(
            row["ledger"]["fits_effective_conservative_street"]
            for row in target_rows
        )
        == confirm["require_conservative_ledgers_fit"],
        "retreat_certificates_complete": all(
            row["retreat"]["independently_certified"]
            and row["exact_oracles_executed"] == 2 + row["cut_rounds"]
            for row in target_rows
        )
        == confirm["require_retreat_certificates_complete"],
        "no_cross_target_adaptation": (
            [row["target_id"] for row in target_rows] == fixed_ids
            and not cross_target_adaptation
        )
        == confirm["require_no_cross_target_adaptation"],
        "blueprint_external_emission": all(
            row["actual_emitted_policy_sha256"]
            == row["restricted_blueprint_policy_sha256"]
            and row["candidate_policies_emitted"] == 0
            for row in target_rows
        )
        == confirm["require_blueprint_external_emission"],
        "label_accounting": (
            confirm["minimum_total_exact_oracles"]
            <= total_exact_oracles
            <= confirm["maximum_total_exact_oracles"]
            and total_exact_oracles == 12 + cut_rounds
            and confirm["minimum_post_barrier_labels"]
            <= total_post_barrier_labels
            <= confirm["maximum_post_barrier_labels"]
            and total_post_barrier_labels == 6 + cut_rounds
        )
        == confirm["require_label_accounting"],
        "population_claim_null": (population_claim is None)
        == confirm["require_population_claim_null"],
        "total_time": total_seconds <= gate["maximum_total_seconds"],
        "finite": core._finite_tree(target_rows) == confirm["require_finite"],
    }
    gate_result = finalize_gates(checks)
    transfers = bool(
        gate_result["passed"] and transfer["decision_aligned_value_transfers"]
    )
    confirmation = bool(
        gate_result["passed"]
        and all_globally_closed
        and all_safe_positive
        and transfers
    )
    delivered_values = [
        float(row["retreat"]["exact_positive_value"])
        if row["retreat"]["shadow_accepted"]
        else 0.0
        for row in target_rows
    ]
    one_seat_claim = (
        "all_six_fresh_post_fold_current_decision_endpoints_globally_closed_"
        "within_1e_8"
        if gate_result["passed"] and all_globally_closed
        else None
    )
    result = {
        "schema_version": 1,
        "status": "h32_post_fold_closure_value_confirmation_executed",
        "environment": assemble_environment(runtime=runtime, git=git),
        "config_sha256": _sha256(config_path),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "methodology": {
            "fresh_post_fold_targets": len(target_rows),
            "warm_steps": len(target_rows),
            "adaptive_construction_oracles": len(target_rows),
            "post_cut_endpoint_labels": cut_rounds,
            "final_retreat_labels": len(target_rows),
            "total_exact_oracles": total_exact_oracles,
            "candidate_policies_emitted": 0,
            "cross_target_adaptation": cross_target_adaptation,
            "campaign_events": campaign_events,
            "candidates_frozen_before_labels": candidates_frozen_before_labels,
            "setup_adapter_active_during_campaign": adapter_active,
            "setup_adapter_restored_after_campaign": adapter_restored,
            "construction_capture_restored": capture_restored,
        },
        "parents": {
            "post_fold_manifest_sha256": _sha256(_MANIFEST),
            "combined_ledger_result_sha256": _sha256(_LEDGER_RESULT),
        },
        "target_rows": target_rows,
        "closure": {
            "all_globally_closed": all_globally_closed,
            "globally_closed_targets": sum(
                row["endpoint_certificate"]["globally_closed"]
                for row in target_rows
            ),
            "maximum_optimality_gap": max(
                row["endpoint_certificate"]["optimality_gap"]
                for row in target_rows
            ),
            "maximum_incremental_endpoint_oracle_ms": max(
                row["endpoint_certificate"]["incremental_oracle_ms"]
                for row in target_rows
            ),
            "cut_round_histogram": {
                str(rounds): sum(row["cut_rounds"] == rounds for row in target_rows)
                for rounds in (0, 1)
            },
        },
        "transfer": transfer,
        "aggregate": {
            "all_safe_positive": all_safe_positive,
            "shadow_accepted_targets": sum(
                row["retreat"]["shadow_accepted"] for row in target_rows
            ),
            "material_target_count": transfer["material_target_count"],
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
            "fresh_closure_and_value_confirmed": confirmation,
        },
        **gate_result,
        "decision": post_fold_confirmation_decision(
            process_passed=bool(gate_result["passed"]),
            all_globally_closed=all_globally_closed,
            all_safe_positive=all_safe_positive,
            transfers=transfers,
        ),
        "actual_emitted_policy": "immutable_restricted_blueprint_only_on_all_targets",
        "strategy_quality_claim": (
            "six_fresh_post_fold_current_decision_shadow_measurements_only"
            if gate_result["passed"]
            else None
        ),
        "one_seat_global_optimality_claim": one_seat_claim,
        "strategy_population_claim": population_claim,
        "total_seconds": total_seconds,
        "limitations": [
            (
                "The six boards and source blueprints are retained; freshness "
                "applies to sealed post-fold posterior identities and labels."
            ),
            (
                "The fixed panel is non-IID and covers one h32 current-decision "
                "continuation shape only."
            ),
            (
                "The globally closed endpoint and independently safe factor-0.5 "
                "retreat are distinct policies."
            ),
            (
                "All policies remain shadow-only immutable-blueprint emissions; "
                "no deployment, composition, chip-EV, or poker claim is made."
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
    result = run_h32_post_fold_closure_value_confirmation(
        args.config,
        args.output,
    )
    print(
        json.dumps(
            {
                "output": str(args.output),
                "passed": result["passed"],
                "decision": result["decision"],
                "closure": result["closure"],
                "aggregate": result["aggregate"],
            },
            indent=2,
        )
    )
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
