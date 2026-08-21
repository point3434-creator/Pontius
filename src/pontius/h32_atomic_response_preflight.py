"""Frozen h32 atomic preflight for the incremental response cache."""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import math
import os
from pathlib import Path
import statistics
import time
from typing import Any

import numpy as np

from .cupy_sparse_incidence import (
    CuPyBidirectionalIncidence,
    _cupy_modules,
    release_cupy_memory_pool,
)
from .delta_certificate_contract import atomic_policy_manifest, interpolate_policy_atoms
from .factor_tt_contraction import FactorTTBeliefWorkspace
from .fresh_h32_strategy_transfer_audit import _resident_quality_row
from .h32_policy_delta_verifier_audit import (
    _ACCEPTANCE_SOURCE,
    _CANDIDATE_SOURCE,
    _EXTENSION_SOURCE,
    _LADDER_SOURCE,
    _source_target,
    parse_h32_policy_delta_verifier_config,
    reconstruct_candidate_policies,
)
from .h32_warm_search_acceptance_audit import build_target_belief
from .incremental_leaf_adjoint_response import (
    compile_leaf_adjoint_response_caches,
    verify_incremental_leaf_adjoint_candidate,
)
from .leaf_adjoint_checkpoint_ladder_audit import _build_case
from .open_mode_factor_tt import OpenModeFactorTTWorkspace
from .public_policy_tt import _information_key
from .real_policy import policy_digest
from .reporting import environment_metadata
from .resident_heterogeneous_leaf_contraction import (
    CuPyResidentAutomatonCache,
    CuPyResidentBeliefCache,
)
from .river import parse_cards


_ROOT = Path(__file__).parents[2]
_CONFIG = _ROOT / "experiments/configs/h32-atomic-response-preflight-v1.json"
_OUTPUT = _ROOT / "experiments/results/h32-atomic-response-preflight-v1.json"
_PARENT_CONFIG = _ROOT / "experiments/configs/h32-policy-delta-verifier-audit-v1.json"
_PARENT_RESULT = _ROOT / "experiments/results/h32-policy-delta-verifier-audit-v1.json"
_IMPLEMENTATION = Path(__file__)
_INCREMENTAL = _ROOT / "src/pontius/incremental_leaf_adjoint_response.py"
_DELTA_CONTRACT = _ROOT / "src/pontius/delta_certificate_contract.py"
_REQUIREMENTS = _ROOT / "experiments/requirements/leaf-adjoint-gpu-screen-v1.txt"

_CONFIG_FIELDS = {
    "evidence_stage",
    "seed",
    "expected_parent_config_sha256",
    "expected_parent_result_sha256",
    "expected_acceptance_source_sha256",
    "expected_candidate_source_sha256",
    "expected_ladder_source_sha256",
    "expected_extension_source_sha256",
    "expected_requirements_sha256",
    "expected_incremental_implementation_sha256",
    "expected_delta_contract_sha256",
    "expected_audit_implementation_sha256",
    "range_families",
    "target_shifts",
    "bundle_candidate_id",
    "atom_selection",
    "atom_scale",
    "seat_order",
    "maximum_feature_width_per_batch",
    "street_budget_ms",
    "reserve_scenarios_ms",
    "gates",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def parse_h32_atomic_response_preflight_config(config: dict[str, Any]) -> dict[str, Any]:
    """Reject any drift from the outcome-neutral ADR-0159 protocol."""

    if set(config) != _CONFIG_FIELDS:
        raise ValueError("atomic response preflight fields differ from ADR-0159")
    frozen = {
        "evidence_stage": "preregistered_after_adr0158_before_any_h32_atomic_label",
        "seed": 20260821,
        "range_families": ["balanced", "blocker_heavy"],
        "target_shifts": ["local_blocker_seat3_x2", "all_seat_strength_1_to2"],
        "bundle_candidate_id": "search_current1",
        "atom_selection": "lexicographically_first_changed_information_set_per_acting_seat",
        "atom_scale": 1.0,
        "seat_order": [0, 1, 2, 3, 4, 5],
        "maximum_feature_width_per_batch": 384,
        "street_budget_ms": 15000.0,
        "reserve_scenarios_ms": [0.0, 250.0, 500.0, 1000.0],
    }
    if any(config[key] != value for key, value in frozen.items()):
        raise ValueError("atomic response workload differs from ADR-0159")
    sources = {
        "expected_parent_config_sha256": _PARENT_CONFIG,
        "expected_parent_result_sha256": _PARENT_RESULT,
        "expected_acceptance_source_sha256": _ACCEPTANCE_SOURCE,
        "expected_candidate_source_sha256": _CANDIDATE_SOURCE,
        "expected_ladder_source_sha256": _LADDER_SOURCE,
        "expected_extension_source_sha256": _EXTENSION_SOURCE,
        "expected_requirements_sha256": _REQUIREMENTS,
        "expected_incremental_implementation_sha256": _INCREMENTAL,
        "expected_delta_contract_sha256": _DELTA_CONTRACT,
        "expected_audit_implementation_sha256": _IMPLEMENTATION,
    }
    for field, path in sources.items():
        if config[field] != _sha256(path):
            raise ValueError(f"atomic response source hash mismatch for {field}")
    expected_gates = {
        "expected_target_rows": 4,
        "expected_atom_rows": 24,
        "expected_atoms_per_target": 6,
        "expected_complete_teacher_seat_evaluations": 144,
        "expected_new_diagnostic_quality_labels": 24,
        "maximum_source_utility_error": 1e-9,
        "maximum_source_best_response_error": 1e-9,
        "maximum_atom_utility_error": 1e-9,
        "maximum_atom_best_response_error": 1e-9,
        "maximum_atom_deviation_gain_error": 1e-9,
        "maximum_persistent_numeric_bytes": 1000000000,
        "maximum_gpu_pool_bytes": 12000000000,
        "minimum_gpu_free_headroom_bytes": 1000000000,
        "maximum_cache_compile_ms": 120000.0,
        "maximum_atom_certificate_ms": 60000.0,
        "maximum_total_audit_seconds": 1200.0,
        "require_policy_identity": True,
        "require_atom_identity": True,
        "require_stop_identity": True,
    }
    if config["gates"] != expected_gates:
        raise ValueError("atomic response gates differ from ADR-0159")
    return config


def _information_key_players(layout: Any, hands_by_player: Any) -> dict[str, int]:
    owners: dict[str, int] = {}
    for node in layout.nodes:
        if node.player < 0:
            continue
        for hand in hands_by_player[node.player]:
            key = _information_key(layout, node.player, hand, node.history)
            previous = owners.setdefault(key, int(node.player))
            if previous != node.player:
                raise AssertionError("information key has multiple acting seats")
    return owners


def select_one_atom_per_acting_seat(
    layout: Any,
    hands_by_player: Any,
    blueprint: dict[str, dict[str, float]],
    bundle: dict[str, dict[str, float]],
) -> tuple[dict[str, Any], ...]:
    """Apply the frozen label-independent atomic selection rule."""

    owners = _information_key_players(layout, hands_by_player)
    atoms = atomic_policy_manifest(blueprint, bundle)
    selected = []
    for seat in range(layout.num_players):
        atom = next((row for row in atoms if owners[row.information_key] == seat), None)
        if atom is None:
            raise ValueError(f"bundle has no changed atom for acting seat {seat}")
        selected.append(
            {
                "acting_seat": seat,
                "information_key": atom.information_key,
                "changed_entries": atom.changed_entries,
                "maximum_absolute_probability_delta": (
                    atom.maximum_absolute_probability_delta
                ),
            }
        )
    return tuple(selected)


def _unique_response_cache_bytes(caches: tuple[Any, ...]) -> int:
    arrays: dict[int, Any] = {}
    for cache in caches:
        for values in (
            cache.parents,
            cache.parent_actions,
            *cache.source_probabilities,
            *cache.terminal_values,
        ):
            if values is not None:
                arrays.setdefault(id(values), values)
    return sum(int(values.nbytes) for values in arrays.values())


def _source_errors(caches: tuple[Any, ...], quality: dict[str, Any]) -> dict[str, float]:
    return {
        "maximum_utility_error": max(
            abs(cache.source_evaluation.profile_utility - quality["utilities"][seat])
            for seat, cache in enumerate(caches)
        ),
        "maximum_best_response_error": max(
            abs(
                cache.source_evaluation.best_response_value
                - quality["best_response_values"][seat]
            )
            for seat, cache in enumerate(caches)
        ),
        "maximum_deviation_gain_error": max(
            abs(cache.source_evaluation.deviation_gain - quality["deviation_gains"][seat])
            for seat, cache in enumerate(caches)
        ),
    }


def _atom_errors(incremental: dict[str, Any], teacher: dict[str, Any]) -> dict[str, float]:
    by_seat = {int(row["target_player"]): row for row in incremental["seat_rows"]}
    seats = tuple(by_seat)
    return {
        "maximum_utility_error": max(
            abs(by_seat[seat]["profile_utility"] - teacher["utilities"][seat])
            for seat in seats
        ),
        "maximum_best_response_error": max(
            abs(
                by_seat[seat]["best_response_value"]
                - teacher["best_response_values"][seat]
            )
            for seat in seats
        ),
        "maximum_deviation_gain_error": max(
            abs(by_seat[seat]["deviation_gain"] - teacher["deviation_gains"][seat])
            for seat in seats
        ),
    }


def _expected_stop(
    gains: tuple[float, ...],
    blueprint_gains: tuple[float, ...],
    blueprint_nash: float,
    raw_guard: float,
    seat_order: tuple[int, ...],
) -> dict[str, Any]:
    partial = 0.0
    evaluated = []
    for seat in seat_order:
        partial += gains[seat]
        evaluated.append(seat)
        reason = None
        if gains[seat] > blueprint_gains[seat] + raw_guard:
            reason = "blueprint_cap"
        elif partial > blueprint_nash + raw_guard:
            reason = "objective_lower_bound"
        if reason is not None:
            return {
                "evaluated_seats": evaluated,
                "stop_reason": reason,
                "stop_seat": seat,
                "complete": False,
            }
    return {
        "evaluated_seats": evaluated,
        "stop_reason": "complete",
        "stop_seat": None,
        "complete": True,
    }


def _memory_snapshot(cp: Any) -> dict[str, int]:
    free, total = cp.cuda.runtime.memGetInfo()
    pool = cp.get_default_memory_pool()
    return {
        "gpu_free_bytes": int(free),
        "gpu_total_bytes": int(total),
        "gpu_pool_used_bytes": int(pool.used_bytes()),
        "gpu_pool_total_bytes": int(pool.total_bytes()),
    }


def _run_target(
    *,
    config: dict[str, Any],
    parent: dict[str, Any],
    family: str,
    shift: str,
    source_belief: Any,
    source_workspace: OpenModeFactorTTWorkspace,
    layout: Any,
    sparse: Any,
    automata: Any,
    gpu: Any,
    acceptance: dict[str, Any],
    candidate_source: dict[str, Any],
    ladder: dict[str, Any],
    extension: dict[str, Any],
    cp: Any,
) -> dict[str, Any]:
    acceptance_target = _source_target(acceptance, family=family, shift=shift)
    candidate_target = _source_target(candidate_source, family=family, shift=shift)
    target_belief, _ = build_target_belief(
        source_belief,
        board=source_belief.board,
        shift=shift,
        local_blocker_target_seat=parent["local_blocker_target_seat"],
    )
    base = FactorTTBeliefWorkspace.compile(
        source_workspace.topology.base,
        target_belief,
        query_chunk_records=parent["query_chunk_records"],
    )
    workspace = OpenModeFactorTTWorkspace.compile(source_workspace.topology, base)
    blueprint, policies, source_identity = reconstruct_candidate_policies(
        family=family,
        acceptance_target=acceptance_target,
        candidate_target=candidate_target,
        ladder_source=ladder,
        extension_source=extension,
        candidate_order=tuple(parent["candidate_order"]),
    )
    bundle_row = next(
        row for row in policies if row["candidate_id"] == config["bundle_candidate_id"]
    )
    bundle = bundle_row["policy"]
    blueprint_quality = acceptance_target["blueprint_quality"]
    policy_identity = source_identity and (
        policy_digest(blueprint) == blueprint_quality["policy_sha256"]
        and policy_digest(bundle) == bundle_row["policy_sha256"]
    )
    selected = select_one_atom_per_acting_seat(
        layout, target_belief.hands_by_player, blueprint, bundle
    )

    resident_started = time.perf_counter()
    belief_cache = CuPyResidentBeliefCache.compile(workspace)
    automaton_caches = tuple(
        CuPyResidentAutomatonCache.compile(
            workspace, automata[seat], target_seat=seat
        )
        for seat in range(layout.num_players)
    )
    resident_compile_ms = (time.perf_counter() - resident_started) * 1000.0
    after_resident = _memory_snapshot(cp)

    response_started = time.perf_counter()
    response_caches = compile_leaf_adjoint_response_caches(
        layout,
        workspace,
        sparse,
        blueprint,
        automata,
        hands_by_player=target_belief.hands_by_player,
        maximum_feature_width_per_batch=config["maximum_feature_width_per_batch"],
        belief_cache=belief_cache,
        automaton_caches=automaton_caches,
        cupy_sparse=gpu,
    )
    response_compile_ms = (time.perf_counter() - response_started) * 1000.0
    after_response = _memory_snapshot(cp)
    source_errors = _source_errors(response_caches, blueprint_quality)

    blueprint_gains = tuple(float(value) for value in blueprint_quality["deviation_gains"])
    blueprint_nash = float(blueprint_quality["nash_conv"])
    raw_guard = float(parent["acceptance_guard_normalized"] * parent["stack"])
    atom_rows = []
    for selected_atom in selected:
        key = selected_atom["information_key"]
        candidate_id = f"atomic_seat{selected_atom['acting_seat']}"
        policy = interpolate_policy_atoms(
            blueprint, bundle, [key], scale=config["atom_scale"]
        )
        teacher, _ = _resident_quality_row(
            layout=layout,
            workspace=workspace,
            sparse=sparse,
            automata=automata,
            policy=policy,
            label=candidate_id,
            hands_by_player=target_belief.hands_by_player,
            belief_cache=belief_cache,
            automaton_caches=automaton_caches,
            gpu=gpu,
            payoff_span=parent["stack"],
            maximum_feature_width_per_batch=config["maximum_feature_width_per_batch"],
        )
        incremental = verify_incremental_leaf_adjoint_candidate(
            candidate_id=candidate_id,
            layout=layout,
            policy=policy,
            hands_by_player=target_belief.hands_by_player,
            response_caches=response_caches,
            blueprint_deviation_gains=blueprint_gains,
            best_complete_nash_conv=blueprint_nash,
            payoff_span=parent["stack"],
            raw_guard=raw_guard,
            seat_order=tuple(config["seat_order"]),
            maximum_feature_width_per_batch=config["maximum_feature_width_per_batch"],
            belief_cache=belief_cache,
            automaton_caches=automaton_caches,
            cupy_sparse=gpu,
        )
        expected = _expected_stop(
            tuple(float(value) for value in teacher["deviation_gains"]),
            blueprint_gains,
            blueprint_nash,
            raw_guard,
            tuple(config["seat_order"]),
        )
        stop_identity = all(
            incremental[field] == expected[field]
            for field in ("evaluated_seats", "stop_reason", "stop_seat", "complete")
        )
        budget_rows = [
            {
                "reserve_ms": reserve,
                "certificate_only_fits": incremental["wall_ms"] + reserve
                <= config["street_budget_ms"],
            }
            for reserve in config["reserve_scenarios_ms"]
        ]
        atom_rows.append(
            {
                **selected_atom,
                "candidate_id": candidate_id,
                "policy_sha256": policy_digest(policy),
                "teacher_quality": teacher,
                "incremental": incremental,
                "teacher_errors": _atom_errors(incremental, teacher),
                "expected_stop": expected,
                "stop_identity": stop_identity,
                "budget_rows": budget_rows,
            }
        )

    memory = _memory_snapshot(cp)
    return {
        "range_family": family,
        "target_shift": shift,
        "policy_identity": policy_identity,
        "blueprint_policy_sha256": policy_digest(blueprint),
        "bundle_policy_sha256": policy_digest(bundle),
        "selected_atoms": list(selected),
        "resident_cache_compile_ms": resident_compile_ms,
        "response_cache_compile_ms": response_compile_ms,
        "cold_construction_ms": resident_compile_ms + response_compile_ms,
        "resident_cache_numeric_bytes": belief_cache.numeric_bytes
        + sum(cache.numeric_bytes for cache in automaton_caches),
        "response_cache_raw_numeric_bytes": sum(
            cache.persistent_numeric_bytes for cache in response_caches
        ),
        "response_cache_unique_numeric_bytes": _unique_response_cache_bytes(
            response_caches
        ),
        "source_terminal_contractions": sum(
            cache.terminal_contractions for cache in response_caches
        ),
        "source_maximum_terminal_middle_rank": max(
            cache.source_evaluation.maximum_terminal_middle_rank
            for cache in response_caches
        ),
        "source_errors": source_errors,
        "memory_after_resident_cache": after_resident,
        "memory_after_response_cache": after_response,
        "memory_after_atoms": memory,
        "atom_rows": atom_rows,
    }


def run_h32_atomic_response_preflight(config: dict[str, Any]) -> dict[str, Any]:
    """Execute the frozen h32 atomic response experiment."""

    parsed = parse_h32_atomic_response_preflight_config(config)
    parent_config = json.loads(_PARENT_CONFIG.read_text(encoding="utf-8"))
    parent = parse_h32_policy_delta_verifier_config(parent_config)
    parent_result = json.loads(_PARENT_RESULT.read_text(encoding="utf-8"))
    acceptance = json.loads(_ACCEPTANCE_SOURCE.read_text(encoding="utf-8"))
    candidate_source = json.loads(_CANDIDATE_SOURCE.read_text(encoding="utf-8"))
    ladder = json.loads(_LADDER_SOURCE.read_text(encoding="utf-8"))
    extension = json.loads(_EXTENSION_SOURCE.read_text(encoding="utf-8"))
    if not parent_result["gates"]["passed"]:
        raise ValueError("frozen parent gate did not pass")

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

    started = time.perf_counter()
    board = parse_cards(*parent["board"])
    targets = []
    for family in parsed["range_families"]:
        source_belief, layout, sparse, retained = _build_case(
            parsed=parent,
            board=board,
            hand_count=parent["wide_hands_per_player"],
            family=family,
        )
        source_workspace, _, automata = retained
        gpu = CuPyBidirectionalIncidence.compile(sparse)
        for shift in parsed["target_shifts"]:
            targets.append(
                _run_target(
                    config=parsed,
                    parent=parent,
                    family=family,
                    shift=shift,
                    source_belief=source_belief,
                    source_workspace=source_workspace,
                    layout=layout,
                    sparse=sparse,
                    automata=automata,
                    gpu=gpu,
                    acceptance=acceptance,
                    candidate_source=candidate_source,
                    ladder=ladder,
                    extension=extension,
                    cp=cp,
                )
            )
            gc.collect()
            release_cupy_memory_pool()
        del gpu
        gc.collect()
        release_cupy_memory_pool()

    atom_rows = [row for target in targets for row in target["atom_rows"]]
    total_seconds = time.perf_counter() - started
    gates_config = parsed["gates"]
    maximum_source_utility_error = max(
        target["source_errors"]["maximum_utility_error"] for target in targets
    )
    maximum_source_response_error = max(
        target["source_errors"]["maximum_best_response_error"] for target in targets
    )
    maximum_atom_utility_error = max(
        row["teacher_errors"]["maximum_utility_error"] for row in atom_rows
    )
    maximum_atom_response_error = max(
        row["teacher_errors"]["maximum_best_response_error"] for row in atom_rows
    )
    maximum_atom_gain_error = max(
        row["teacher_errors"]["maximum_deviation_gain_error"] for row in atom_rows
    )
    maximum_persistent = max(
        target["response_cache_unique_numeric_bytes"] for target in targets
    )
    maximum_gpu_pool = max(
        snapshot["gpu_pool_total_bytes"]
        for target in targets
        for snapshot in (
            target["memory_after_resident_cache"],
            target["memory_after_response_cache"],
            target["memory_after_atoms"],
        )
    )
    minimum_gpu_free = min(
        snapshot["gpu_free_bytes"]
        for target in targets
        for snapshot in (
            target["memory_after_resident_cache"],
            target["memory_after_response_cache"],
            target["memory_after_atoms"],
        )
    )
    gates = {
        "target_rows": len(targets) == gates_config["expected_target_rows"],
        "atom_rows": len(atom_rows) == gates_config["expected_atom_rows"],
        "atoms_per_target": all(
            len(target["atom_rows"]) == gates_config["expected_atoms_per_target"]
            for target in targets
        ),
        "complete_teacher_seat_evaluations": len(atom_rows) * 6
        == gates_config["expected_complete_teacher_seat_evaluations"],
        "new_diagnostic_quality_labels": len(atom_rows)
        == gates_config["expected_new_diagnostic_quality_labels"],
        "policy_identity": all(target["policy_identity"] for target in targets)
        == gates_config["require_policy_identity"],
        "atom_identity": all(
            [row["acting_seat"] for row in target["selected_atoms"]]
            == list(range(6))
            and len({row["information_key"] for row in target["selected_atoms"]}) == 6
            for target in targets
        )
        == gates_config["require_atom_identity"],
        "source_exact": (
            maximum_source_utility_error
            <= gates_config["maximum_source_utility_error"]
            and maximum_source_response_error
            <= gates_config["maximum_source_best_response_error"]
        ),
        "atom_exact": (
            maximum_atom_utility_error <= gates_config["maximum_atom_utility_error"]
            and maximum_atom_response_error
            <= gates_config["maximum_atom_best_response_error"]
            and maximum_atom_gain_error
            <= gates_config["maximum_atom_deviation_gain_error"]
        ),
        "stop_identity": all(row["stop_identity"] for row in atom_rows)
        == gates_config["require_stop_identity"],
        "persistent_numeric_bytes": maximum_persistent
        <= gates_config["maximum_persistent_numeric_bytes"],
        "gpu_pool_bytes": maximum_gpu_pool <= gates_config["maximum_gpu_pool_bytes"],
        "gpu_free_headroom": minimum_gpu_free
        >= gates_config["minimum_gpu_free_headroom_bytes"],
        "cache_compile_ms": max(target["cold_construction_ms"] for target in targets)
        <= gates_config["maximum_cache_compile_ms"],
        "atom_certificate_ms": max(row["incremental"]["wall_ms"] for row in atom_rows)
        <= gates_config["maximum_atom_certificate_ms"],
        "total_audit_seconds": total_seconds
        <= gates_config["maximum_total_audit_seconds"],
    }
    gates["passed"] = all(gates.values())
    certificate_ms = [float(row["incremental"]["wall_ms"]) for row in atom_rows]
    result = {
        "status": "frozen_h32_atomic_response_preflight_executed",
        "methodology": {
            "anchor": "immutable_blueprint",
            "bundle": parsed["bundle_candidate_id"],
            "selection": parsed["atom_selection"],
            "teacher_role": "complete_resident_exactness_teacher_only",
            "candidate_order_role": "fixed_by_acting_seat_before_labels",
            "composition": "forbidden",
            "strategy_selection": "forbidden",
            "strategy_quality_claim": "none",
            "wall_clock_scope": "certificate_only_search_and_atom_extraction_excluded",
        },
        "environment": environment_metadata(),
        "config_sha256": _sha256(_CONFIG),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "targets": targets,
        "aggregate": {
            "target_rows": len(targets),
            "atom_rows": len(atom_rows),
            "new_diagnostic_quality_labels": len(atom_rows),
            "complete_teacher_seat_evaluations": len(atom_rows) * 6,
            "maximum_source_utility_error": maximum_source_utility_error,
            "maximum_source_best_response_error": maximum_source_response_error,
            "maximum_atom_utility_error": maximum_atom_utility_error,
            "maximum_atom_best_response_error": maximum_atom_response_error,
            "maximum_atom_deviation_gain_error": maximum_atom_gain_error,
            "maximum_response_cache_unique_numeric_bytes": maximum_persistent,
            "maximum_gpu_pool_bytes": maximum_gpu_pool,
            "minimum_gpu_free_headroom_bytes": minimum_gpu_free,
            "maximum_source_terminal_middle_rank": max(
                target["source_maximum_terminal_middle_rank"] for target in targets
            ),
            "cold_construction_ms": {
                "minimum": min(target["cold_construction_ms"] for target in targets),
                "median": statistics.median(
                    target["cold_construction_ms"] for target in targets
                ),
                "maximum": max(target["cold_construction_ms"] for target in targets),
            },
            "certificate_ms": {
                "minimum": min(certificate_ms),
                "median": statistics.median(certificate_ms),
                "maximum": max(certificate_ms),
            },
            "affected_terminal_fraction": math.fsum(
                row["incremental"]["affected_terminal_contractions"]
                / row["incremental"]["full_terminal_contractions_for_evaluated_seats"]
                for row in atom_rows
            )
            / len(atom_rows),
            "response_action_flips": sum(
                row["incremental"]["response_action_flips"] for row in atom_rows
            ),
            "certificate_only_budget_fits": {
                str(reserve): sum(
                    next(
                        budget["certificate_only_fits"]
                        for budget in row["budget_rows"]
                        if budget["reserve_ms"] == reserve
                    )
                    for row in atom_rows
                )
                for reserve in parsed["reserve_scenarios_ms"]
            },
            "total_audit_seconds": total_seconds,
        },
        "gates": gates,
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=_CONFIG)
    parser.add_argument("--output", type=Path, default=_OUTPUT)
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    result = run_h32_atomic_response_preflight(config)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "gates": result["gates"]}, indent=2))
    if not result["gates"]["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
