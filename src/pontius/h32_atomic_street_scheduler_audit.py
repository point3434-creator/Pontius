"""Frozen generation-to-emission h32 atomic street scheduler ledger."""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import math
import os
from pathlib import Path
import time
from typing import Any

import numpy as np

from .cupy_sparse_incidence import (
    CuPyBidirectionalIncidence,
    _cupy_modules,
    release_cupy_memory_pool,
)
from .delta_certificate_contract import interpolate_policy_atoms
from .factor_tt_contraction import FactorTTBeliefWorkspace
from .h32_atomic_response_preflight import select_one_atom_per_acting_seat
from .h32_policy_delta_verifier_audit import (
    _ACCEPTANCE_SOURCE,
    _CANDIDATE_SOURCE,
    _EXTENSION_SOURCE,
    _LADDER_SOURCE,
    _source_target,
    parse_h32_policy_delta_verifier_config,
    reconstruct_candidate_policies,
)
from .h32_resident_cfr_audit import _policy_error
from .h32_shared_response_residency_replay import _descriptor_core
from .h32_warm_search_acceptance_audit import build_target_belief
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
_CONFIG = _ROOT / "experiments/configs/h32-atomic-street-scheduler-v1.json"
_OUTPUT = _ROOT / "experiments/results/h32-atomic-street-scheduler-v1.json"
_PARENT_CONFIG = _ROOT / "experiments/configs/h32-policy-delta-verifier-audit-v1.json"
_ACCEPTANCE_CONFIG = _ROOT / "experiments/configs/h32-warm-search-acceptance-v1.json"
_ATOMIC_RESULT = _ROOT / "experiments/results/h32-atomic-response-preflight-v1.json"
_LIFECYCLE_CONFIG = (
    _ROOT / "experiments/configs/h32-shared-response-allocator-lifecycle-v1.json"
)
_LIFECYCLE_RESULT = (
    _ROOT / "experiments/results/h32-shared-response-allocator-lifecycle-v1.json"
)
_REQUIREMENTS = _ROOT / "experiments/requirements/leaf-adjoint-gpu-screen-v1.txt"
_SHARED_IMPLEMENTATION = _ROOT / "src/pontius/shared_resident_response_context.py"
_INCREMENTAL_IMPLEMENTATION = _ROOT / "src/pontius/incremental_leaf_adjoint_response.py"
_RESIDENT_CFR_IMPLEMENTATION = _ROOT / "src/pontius/resident_leaf_adjoint_cfr.py"
_IMPLEMENTATION = Path(__file__)

_CONFIG_FIELDS = {
    "evidence_stage",
    "seed",
    "expected_parent_config_sha256",
    "expected_acceptance_config_sha256",
    "expected_atomic_result_sha256",
    "expected_lifecycle_config_sha256",
    "expected_lifecycle_result_sha256",
    "expected_acceptance_source_sha256",
    "expected_candidate_source_sha256",
    "expected_ladder_source_sha256",
    "expected_extension_source_sha256",
    "expected_requirements_sha256",
    "expected_shared_implementation_sha256",
    "expected_incremental_implementation_sha256",
    "expected_resident_cfr_implementation_sha256",
    "expected_audit_implementation_sha256",
    "range_family",
    "target_shifts",
    "solver_variant",
    "warm_regret_mass_payoff_fraction",
    "bundle_candidate_id",
    "atom_selection",
    "atom_order",
    "atom_scale",
    "seat_order",
    "decision_budget_ms",
    "emission_reserve_ms",
    "certificate_start_reserve_ms",
    "maximum_feature_width_per_batch",
    "packing_policy",
    "emitted_policy",
    "gates",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def parse_h32_atomic_street_scheduler_config(
    config: dict[str, Any],
) -> dict[str, Any]:
    """Validate the outcome-neutral ADR-0165 street ledger."""

    if set(config) != _CONFIG_FIELDS:
        raise ValueError("atomic street scheduler fields differ from ADR-0165")
    frozen = {
        "evidence_stage": "preregistered_after_adr0164_before_any_end_to_end_street_ledger",
        "seed": 20260821,
        "range_family": "balanced",
        "target_shifts": ["local_blocker_seat3_x2", "all_seat_strength_1_to2"],
        "solver_variant": "dcfr",
        "warm_regret_mass_payoff_fraction": 0.1,
        "bundle_candidate_id": "search_current1",
        "atom_selection": "lexicographically_first_changed_information_set_per_acting_seat",
        "atom_order": [0, 1, 2, 3, 4, 5],
        "atom_scale": 1.0,
        "seat_order": [0, 1, 2, 3, 4, 5],
        "decision_budget_ms": 15000.0,
        "emission_reserve_ms": 1000.0,
        "certificate_start_reserve_ms": 1250.0,
        "maximum_feature_width_per_batch": 384,
        "packing_policy": "not_invoked_composition_forbidden",
        "emitted_policy": "immutable_blueprint",
    }
    if any(config[key] != value for key, value in frozen.items()):
        raise ValueError("atomic street scheduler workload differs from ADR-0165")
    sources = {
        "expected_parent_config_sha256": _PARENT_CONFIG,
        "expected_acceptance_config_sha256": _ACCEPTANCE_CONFIG,
        "expected_atomic_result_sha256": _ATOMIC_RESULT,
        "expected_lifecycle_config_sha256": _LIFECYCLE_CONFIG,
        "expected_lifecycle_result_sha256": _LIFECYCLE_RESULT,
        "expected_acceptance_source_sha256": _ACCEPTANCE_SOURCE,
        "expected_candidate_source_sha256": _CANDIDATE_SOURCE,
        "expected_ladder_source_sha256": _LADDER_SOURCE,
        "expected_extension_source_sha256": _EXTENSION_SOURCE,
        "expected_requirements_sha256": _REQUIREMENTS,
        "expected_shared_implementation_sha256": _SHARED_IMPLEMENTATION,
        "expected_incremental_implementation_sha256": _INCREMENTAL_IMPLEMENTATION,
        "expected_resident_cfr_implementation_sha256": _RESIDENT_CFR_IMPLEMENTATION,
        "expected_audit_implementation_sha256": _IMPLEMENTATION,
    }
    for field, path in sources.items():
        if config[field] != _sha256(path):
            raise ValueError(f"atomic street scheduler source mismatch for {field}")
    expected_gates = {
        "expected_target_rows": 2,
        "expected_search_steps": 2,
        "expected_generated_atom_rows": 12,
        "expected_new_complete_strategy_quality_labels": 0,
        "maximum_candidate_probability_error": 1e-9,
        "maximum_candidate_mean_tv": 1e-9,
        "maximum_replay_utility_error": 1e-9,
        "maximum_replay_best_response_error": 1e-9,
        "maximum_replay_deviation_gain_error": 1e-9,
        "maximum_search_step_ms": 60000.0,
        "maximum_atom_extraction_ms": 30000.0,
        "maximum_certificate_ms": 60000.0,
        "maximum_pool_total_bytes": 12000000000,
        "minimum_physical_free_bytes": 1000000000,
        "maximum_total_audit_seconds": 600.0,
        "require_target_identity": True,
        "require_blueprint_identity": True,
        "require_atom_key_identity": True,
        "require_attempted_replay_exactness": True,
        "require_attempted_stop_identity": True,
        "require_attempted_work_identity": True,
        "require_deadline_discipline": True,
        "require_blueprint_emission": True,
    }
    if config["gates"] != expected_gates:
        raise ValueError("atomic street scheduler gates differ from ADR-0165")
    return config


def may_start_certificate(
    *,
    elapsed_ms: float,
    decision_budget_ms: float,
    emission_reserve_ms: float,
    certificate_start_reserve_ms: float,
) -> bool:
    """Return whether one more certificate may start before the hard cutoff."""

    values = (
        elapsed_ms,
        decision_budget_ms,
        emission_reserve_ms,
        certificate_start_reserve_ms,
    )
    if any(not math.isfinite(value) or value < 0.0 for value in values):
        raise ValueError("deadline scheduler values must be finite and nonnegative")
    cutoff = decision_budget_ms - emission_reserve_ms
    return elapsed_ms + certificate_start_reserve_ms <= cutoff


def _memory_snapshot(cp: Any) -> dict[str, int]:
    free, total = cp.cuda.runtime.memGetInfo()
    pool = cp.get_default_memory_pool()
    return {
        "gpu_free_bytes": int(free),
        "gpu_total_bytes": int(total),
        "gpu_pool_used_bytes": int(pool.used_bytes()),
        "gpu_pool_total_bytes": int(pool.total_bytes()),
    }


def _recorded_target(source: dict[str, Any], shift: str) -> dict[str, Any]:
    return next(
        target
        for target in source["targets"]
        if target["range_family"] == "balanced" and target["target_shift"] == shift
    )


def _replay_errors(live: dict[str, Any], recorded: dict[str, Any]) -> dict[str, float]:
    expected = {int(row["target_player"]): row for row in recorded["seat_rows"]}
    return {
        "maximum_utility_error": max(
            abs(row["profile_utility"] - expected[int(row["target_player"])]["profile_utility"])
            for row in live["seat_rows"]
        ),
        "maximum_best_response_error": max(
            abs(
                row["best_response_value"]
                - expected[int(row["target_player"])]["best_response_value"]
            )
            for row in live["seat_rows"]
        ),
        "maximum_deviation_gain_error": max(
            abs(row["deviation_gain"] - expected[int(row["target_player"])]["deviation_gain"])
            for row in live["seat_rows"]
        ),
    }


def run_h32_atomic_street_scheduler(config: dict[str, Any]) -> dict[str, Any]:
    """Execute two prepared-context search-to-emission ledgers."""

    parsed = parse_h32_atomic_street_scheduler_config(config)
    parent_config = json.loads(_PARENT_CONFIG.read_text(encoding="utf-8"))
    parent = parse_h32_policy_delta_verifier_config(parent_config)
    acceptance_config = json.loads(_ACCEPTANCE_CONFIG.read_text(encoding="utf-8"))
    if (
        acceptance_config["solver_variant"] != parsed["solver_variant"]
        or acceptance_config["warm_regret_mass_payoff_fraction"]
        != parsed["warm_regret_mass_payoff_fraction"]
    ):
        raise ValueError("scheduler warm-search contract differs from retained source")
    atomic_result = json.loads(_ATOMIC_RESULT.read_text(encoding="utf-8"))
    lifecycle_result = json.loads(_LIFECYCLE_RESULT.read_text(encoding="utf-8"))
    acceptance = json.loads(_ACCEPTANCE_SOURCE.read_text(encoding="utf-8"))
    candidate_source = json.loads(_CANDIDATE_SOURCE.read_text(encoding="utf-8"))
    ladder = json.loads(_LADDER_SOURCE.read_text(encoding="utf-8"))
    extension = json.loads(_EXTENSION_SOURCE.read_text(encoding="utf-8"))
    if not atomic_result["gates"]["passed"] or not lifecycle_result["gates"]["passed"]:
        raise ValueError("scheduler parent gate did not pass")

    import scipy

    cp, _ = _cupy_modules()
    if np.__version__ != parent["required_numpy_version"]:
        raise ValueError("NumPy version differs from frozen runtime")
    if scipy.__version__ != parent["required_scipy_version"]:
        raise ValueError("SciPy version differs from frozen runtime")
    if cp.__version__ != parent["required_cupy_version"]:
        raise ValueError("CuPy version differs from frozen runtime")
    if cp.cuda.runtime.runtimeGetVersion() != parent["required_cuda_runtime_version"]:
        raise ValueError("CUDA runtime differs from frozen runtime")
    if cp.cuda.runtime.driverGetVersion() < parent["minimum_cuda_driver_version"]:
        raise ValueError("CUDA driver is below the frozen floor")
    if str(cp.cuda.Device(0).compute_capability) != parent["required_compute_capability"]:
        raise ValueError("GPU compute capability differs from frozen runtime")
    if not os.environ.get(parent["cuda_dll_environment_variable"]):
        raise ValueError("optional CUDA DLL directory is not configured")

    audit_started = time.perf_counter()
    board = parse_cards(*parent["board"])
    source_belief, layout, sparse, retained = _build_case(
        parsed=parent,
        board=board,
        hand_count=parent["wide_hands_per_player"],
        family=parsed["range_family"],
    )
    source_workspace, _, automata = retained
    gpu = CuPyBidirectionalIncidence.compile(sparse)
    setup_rows = []
    for shift in parsed["target_shifts"]:
        acceptance_target = _source_target(
            acceptance, family=parsed["range_family"], shift=shift
        )
        candidate_target = _source_target(
            candidate_source, family=parsed["range_family"], shift=shift
        )
        belief, descriptor = build_target_belief(
            source_belief,
            board=board,
            shift=shift,
            local_blocker_target_seat=parent["local_blocker_target_seat"],
        )
        target_identity = _descriptor_core(descriptor) == _descriptor_core(
            acceptance_target["target_descriptor"]
        )
        base = FactorTTBeliefWorkspace.compile(
            source_workspace.topology.base,
            belief,
            query_chunk_records=parent["query_chunk_records"],
        )
        workspace = OpenModeFactorTTWorkspace.compile(source_workspace.topology, base)
        blueprint, policies, source_identity = reconstruct_candidate_policies(
            family=parsed["range_family"],
            acceptance_target=acceptance_target,
            candidate_target=candidate_target,
            ladder_source=ladder,
            extension_source=extension,
            candidate_order=tuple(parent["candidate_order"]),
        )
        retained_bundle = next(
            row["policy"]
            for row in policies
            if row["candidate_id"] == parsed["bundle_candidate_id"]
        )
        teacher = acceptance_target["blueprint_quality"]
        recorded = _recorded_target(atomic_result, shift)
        blueprint_identity = source_identity and (
            policy_digest(blueprint) == teacher["policy_sha256"]
            == recorded["blueprint_policy_sha256"]
        )
        setup_rows.append(
            {
                "shift": shift,
                "belief": belief,
                "workspace": workspace,
                "blueprint": blueprint,
                "retained_bundle": retained_bundle,
                "teacher": teacher,
                "recorded": recorded,
                "target_identity": target_identity,
                "blueprint_identity": blueprint_identity,
            }
        )

    shared = SharedResidentAutomatonBundle.compile(setup_rows[0]["workspace"], automata)
    for row in setup_rows:
        row["context"] = bind_resident_response_context(
            shared,
            layout=layout,
            workspace=row["workspace"],
            sparse=sparse,
            source_policy=row["blueprint"],
            hands_by_player=row["belief"].hands_by_player,
            cupy_sparse=gpu,
            maximum_feature_width_per_batch=parsed["maximum_feature_width_per_batch"],
        )
        row["solver"] = ResidentLeafAdjointPublicTreeCFR(
            layout,
            row["workspace"],
            sparse,
            automata,
            parsed["solver_variant"],
            belief_cache=row["context"].belief_cache,
            automaton_caches=shared.automaton_caches,
            cupy_sparse=gpu,
            maximum_feature_width_per_batch=parsed["maximum_feature_width_per_batch"],
            hands_by_player=row["belief"].hands_by_player,
        )
        row["solver"].warm_start(
            row["blueprint"],
            parsed["warm_regret_mass_payoff_fraction"] * float(layout.game.payoff_span),
        )

    target_rows = []
    memory_rows = []
    for setup in setup_rows:
        release_cupy_memory_pool()
        memory_before_street = _memory_snapshot(cp)
        street_started = time.perf_counter()
        setup["solver"].step()
        search_completed = time.perf_counter()
        memory_after_search = _memory_snapshot(cp)
        memory_rows.extend((memory_before_street, memory_after_search))
        search_ms = (search_completed - street_started) * 1000.0
        candidate = setup["solver"].current_strategy()
        candidate_error, candidate_tv = _policy_error(
            candidate, setup["retained_bundle"]
        )

        extraction_started = time.perf_counter()
        manifest = select_one_atom_per_acting_seat(
            layout,
            setup["belief"].hands_by_player,
            setup["blueprint"],
            candidate,
        )
        recorded_by_seat = {
            int(row["acting_seat"]): row for row in setup["recorded"]["atom_rows"]
        }
        atom_key_identity = all(
            row["information_key"]
            == recorded_by_seat[int(row["acting_seat"])]["information_key"]
            for row in manifest
        )
        atom_policies = {
            int(row["acting_seat"]): interpolate_policy_atoms(
                setup["blueprint"],
                candidate,
                [row["information_key"]],
                scale=parsed["atom_scale"],
            )
            for row in manifest
        }
        atom_policy_errors = {
            seat: _policy_error(
                atom_policies[seat],
                interpolate_policy_atoms(
                    setup["blueprint"],
                    setup["retained_bundle"],
                    [recorded_by_seat[seat]["information_key"]],
                    scale=parsed["atom_scale"],
                ),
            )
            for seat in parsed["atom_order"]
        }
        extraction_ms = (time.perf_counter() - extraction_started) * 1000.0

        certificate_rows = []
        deadline_reason = "atom_order_exhausted"
        for acting_seat in parsed["atom_order"]:
            elapsed_before = (time.perf_counter() - street_started) * 1000.0
            if not may_start_certificate(
                elapsed_ms=elapsed_before,
                decision_budget_ms=parsed["decision_budget_ms"],
                emission_reserve_ms=parsed["emission_reserve_ms"],
                certificate_start_reserve_ms=parsed[
                    "certificate_start_reserve_ms"
                ],
            ):
                deadline_reason = "certificate_start_guard"
                break
            recorded_atom = recorded_by_seat[acting_seat]
            before = _memory_snapshot(cp)
            live = verify_incremental_leaf_adjoint_candidate(
                candidate_id=recorded_atom["candidate_id"],
                layout=layout,
                policy=atom_policies[acting_seat],
                hands_by_player=setup["belief"].hands_by_player,
                response_caches=setup["context"].response_caches,
                blueprint_deviation_gains=tuple(
                    float(value) for value in setup["teacher"]["deviation_gains"]
                ),
                best_complete_nash_conv=float(setup["teacher"]["nash_conv"]),
                payoff_span=parent["stack"],
                raw_guard=parent["acceptance_guard_normalized"] * parent["stack"],
                seat_order=tuple(parsed["seat_order"]),
                maximum_feature_width_per_batch=parsed[
                    "maximum_feature_width_per_batch"
                ],
                belief_cache=setup["context"].belief_cache,
                automaton_caches=shared.automaton_caches,
                cupy_sparse=gpu,
            )
            completed_ms = (time.perf_counter() - street_started) * 1000.0
            after = _memory_snapshot(cp)
            memory_rows.extend((before, after))
            recorded_live = recorded_atom["incremental"]
            errors = _replay_errors(live, recorded_live)
            stop_identity = all(
                live[field] == recorded_live[field]
                for field in (
                    "evaluated_seats",
                    "evaluated_seat_count",
                    "stop_reason",
                    "stop_seat",
                    "complete",
                )
            )
            work_identity = all(
                live[field] == recorded_live[field]
                for field in (
                    "affected_terminal_contractions",
                    "full_terminal_contractions_for_evaluated_seats",
                    "reused_terminal_numerators",
                    "response_action_flips",
                )
            )
            usable = completed_ms <= (
                parsed["decision_budget_ms"] - parsed["emission_reserve_ms"]
            )
            certificate_rows.append(
                {
                    "acting_seat": acting_seat,
                    "candidate_id": recorded_atom["candidate_id"],
                    "elapsed_before_ms": elapsed_before,
                    "elapsed_completed_ms": completed_ms,
                    "usable_before_emission_cutoff": usable,
                    "live": live,
                    "errors": errors,
                    "stop_identity": stop_identity,
                    "work_identity": work_identity,
                    "memory_before": before,
                    "memory_after": after,
                }
            )
            if not usable:
                deadline_reason = "certificate_completed_after_cutoff"
                break

        selection_started = time.perf_counter()
        emitted_policy = setup["blueprint"]
        selected_candidate_id = "blueprint_average64"
        selection_ms = (time.perf_counter() - selection_started) * 1000.0
        before_emission_ms = (time.perf_counter() - street_started) * 1000.0
        hard_ledger_ms = before_emission_ms + parsed["emission_reserve_ms"]
        target_rows.append(
            {
                "range_family": parsed["range_family"],
                "target_shift": setup["shift"],
                "target_identity": setup["target_identity"],
                "blueprint_identity": setup["blueprint_identity"],
                "memory_before_street": memory_before_street,
                "memory_after_search": memory_after_search,
                "search_step_ms": search_ms,
                "search_step_work_wall_ms": setup["solver"].last_step_work.wall_ms,
                "candidate_policy_sha256": policy_digest(candidate),
                "retained_candidate_policy_sha256": policy_digest(
                    setup["retained_bundle"]
                ),
                "candidate_maximum_probability_error": candidate_error,
                "candidate_mean_total_variation": candidate_tv,
                "atom_key_identity": atom_key_identity,
                "atom_extraction_and_construction_ms": extraction_ms,
                "generated_atom_count": len(atom_policies),
                "maximum_atom_probability_error": max(
                    value[0] for value in atom_policy_errors.values()
                ),
                "maximum_atom_mean_total_variation": max(
                    value[1] for value in atom_policy_errors.values()
                ),
                "certificate_rows": certificate_rows,
                "attempted_certificate_count": len(certificate_rows),
                "usable_certificate_count": sum(
                    row["usable_before_emission_cutoff"] for row in certificate_rows
                ),
                "deadline_reason": deadline_reason,
                "packing_invoked": False,
                "selection_ms": selection_ms,
                "selected_candidate_id": selected_candidate_id,
                "emitted_policy_sha256": policy_digest(emitted_policy),
                "blueprint_fallback": True,
                "before_emission_ms": before_emission_ms,
                "emission_reserve_ms": parsed["emission_reserve_ms"],
                "hard_ledger_ms": hard_ledger_ms,
                "within_decision_budget": hard_ledger_ms
                <= parsed["decision_budget_ms"],
            }
        )

    certificates = [
        row for target in target_rows for row in target["certificate_rows"]
    ]
    maximum_pool = max(
        (row["gpu_pool_total_bytes"] for row in memory_rows), default=0
    )
    minimum_free = min((row["gpu_free_bytes"] for row in memory_rows), default=10**18)
    maximum_utility_error = max(
        (row["errors"]["maximum_utility_error"] for row in certificates),
        default=0.0,
    )
    maximum_response_error = max(
        (row["errors"]["maximum_best_response_error"] for row in certificates),
        default=0.0,
    )
    maximum_gain_error = max(
        (row["errors"]["maximum_deviation_gain_error"] for row in certificates),
        default=0.0,
    )
    total_seconds = time.perf_counter() - audit_started
    gates_config = parsed["gates"]
    attempted_exact = (
        maximum_utility_error <= gates_config["maximum_replay_utility_error"]
        and maximum_response_error
        <= gates_config["maximum_replay_best_response_error"]
        and maximum_gain_error
        <= gates_config["maximum_replay_deviation_gain_error"]
    )
    deadline_discipline = all(
        all(
            row["elapsed_before_ms"] + parsed["certificate_start_reserve_ms"]
            <= parsed["decision_budget_ms"] - parsed["emission_reserve_ms"]
            for row in target["certificate_rows"]
        )
        and not any(
            not row["usable_before_emission_cutoff"]
            for row in target["certificate_rows"][:-1]
        )
        for target in target_rows
    )
    gates = {
        "target_rows": len(target_rows) == gates_config["expected_target_rows"],
        "search_steps": len(target_rows) == gates_config["expected_search_steps"],
        "generated_atom_rows": sum(
            target["generated_atom_count"] for target in target_rows
        )
        == gates_config["expected_generated_atom_rows"],
        "zero_new_complete_strategy_quality_labels": gates_config[
            "expected_new_complete_strategy_quality_labels"
        ]
        == 0,
        "target_identity": all(target["target_identity"] for target in target_rows)
        == gates_config["require_target_identity"],
        "blueprint_identity": all(
            target["blueprint_identity"] for target in target_rows
        )
        == gates_config["require_blueprint_identity"],
        "candidate_identity": max(
            target["candidate_maximum_probability_error"] for target in target_rows
        )
        <= gates_config["maximum_candidate_probability_error"]
        and max(target["candidate_mean_total_variation"] for target in target_rows)
        <= gates_config["maximum_candidate_mean_tv"],
        "atom_key_identity": all(target["atom_key_identity"] for target in target_rows)
        == gates_config["require_atom_key_identity"],
        "attempted_replay_exactness": attempted_exact
        == gates_config["require_attempted_replay_exactness"],
        "attempted_stop_identity": all(row["stop_identity"] for row in certificates)
        == gates_config["require_attempted_stop_identity"],
        "attempted_work_identity": all(row["work_identity"] for row in certificates)
        == gates_config["require_attempted_work_identity"],
        "deadline_discipline": deadline_discipline
        == gates_config["require_deadline_discipline"],
        "blueprint_emission": all(
            target["selected_candidate_id"] == "blueprint_average64"
            and target["emitted_policy_sha256"]
            == next(
                setup["teacher"]["policy_sha256"]
                for setup in setup_rows
                if setup["shift"] == target["target_shift"]
            )
            for target in target_rows
        )
        == gates_config["require_blueprint_emission"],
        "search_step_ms": max(target["search_step_ms"] for target in target_rows)
        <= gates_config["maximum_search_step_ms"],
        "atom_extraction_ms": max(
            target["atom_extraction_and_construction_ms"] for target in target_rows
        )
        <= gates_config["maximum_atom_extraction_ms"],
        "certificate_ms": max(
            (row["live"]["wall_ms"] for row in certificates), default=0.0
        )
        <= gates_config["maximum_certificate_ms"],
        "pool_total_bytes": maximum_pool
        <= gates_config["maximum_pool_total_bytes"],
        "physical_free_bytes": minimum_free
        >= gates_config["minimum_physical_free_bytes"],
        "total_audit_seconds": total_seconds
        <= gates_config["maximum_total_audit_seconds"],
    }
    gates["passed"] = all(gates.values())
    result = {
        "status": "frozen_h32_atomic_street_scheduler_executed",
        "methodology": {
            "street_clock_starts": "immediately_before_one_resident_warm_step",
            "street_clock_includes": [
                "search_step",
                "current_policy_extraction",
                "atomic_manifest",
                "six_atomic_policy_constructions",
                "deadline_checks",
                "attempted_incremental_certificates",
                "blueprint_selection",
            ],
            "prepared_off_clock": [
                "shared_automaton_bundle",
                "two_belief_contexts",
                "blueprint_response_overlays",
                "warm_started_solvers",
                "allocator_trim",
            ],
            "packing": parsed["packing_policy"],
            "emission": "unmeasured_fixed_reserve_only",
            "emitted_policy": parsed["emitted_policy"],
            "new_complete_strategy_quality_labels": 0,
            "strategy_quality_claim": "none",
            "deployment_authorized": False,
        },
        "environment": environment_metadata(),
        "config_sha256": _sha256(_CONFIG),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "target_rows": target_rows,
        "aggregate": {
            "target_rows": len(target_rows),
            "search_steps": len(target_rows),
            "generated_atom_rows": sum(
                target["generated_atom_count"] for target in target_rows
            ),
            "attempted_certificate_rows": len(certificates),
            "usable_certificate_rows": sum(
                row["usable_before_emission_cutoff"] for row in certificates
            ),
            "new_complete_strategy_quality_labels": 0,
            "targets_within_decision_budget": sum(
                target["within_decision_budget"] for target in target_rows
            ),
            "search_step_ms": {
                "minimum": min(target["search_step_ms"] for target in target_rows),
                "maximum": max(target["search_step_ms"] for target in target_rows),
            },
            "atom_extraction_and_construction_ms": {
                "minimum": min(
                    target["atom_extraction_and_construction_ms"]
                    for target in target_rows
                ),
                "maximum": max(
                    target["atom_extraction_and_construction_ms"]
                    for target in target_rows
                ),
            },
            "hard_ledger_ms": {
                "minimum": min(target["hard_ledger_ms"] for target in target_rows),
                "maximum": max(target["hard_ledger_ms"] for target in target_rows),
            },
            "maximum_candidate_probability_error": max(
                target["candidate_maximum_probability_error"] for target in target_rows
            ),
            "maximum_candidate_mean_total_variation": max(
                target["candidate_mean_total_variation"] for target in target_rows
            ),
            "maximum_replay_utility_error": maximum_utility_error,
            "maximum_replay_best_response_error": maximum_response_error,
            "maximum_replay_deviation_gain_error": maximum_gain_error,
            "maximum_pool_total_bytes": maximum_pool,
            "minimum_physical_free_bytes": minimum_free,
            "total_audit_seconds": total_seconds,
        },
        "gates": gates,
    }
    del setup_rows, shared, gpu
    gc.collect()
    release_cupy_memory_pool()
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=_CONFIG)
    parser.add_argument("--output", type=Path, default=_OUTPUT)
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    result = run_h32_atomic_street_scheduler(config)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "gates": result["gates"]}, indent=2))
    if not result["gates"]["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
