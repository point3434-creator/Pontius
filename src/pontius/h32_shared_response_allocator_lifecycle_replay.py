"""Frozen allocator-trim lifecycle replay for two shared h32 response contexts."""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
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
from .h32_policy_delta_verifier_audit import (
    _ACCEPTANCE_SOURCE,
    _CANDIDATE_SOURCE,
    _EXTENSION_SOURCE,
    _LADDER_SOURCE,
    _source_target,
    parse_h32_policy_delta_verifier_config,
    reconstruct_candidate_policies,
)
from .h32_shared_response_residency_replay import _descriptor_core
from .h32_warm_search_acceptance_audit import build_target_belief
from .incremental_leaf_adjoint_response import (
    verify_incremental_leaf_adjoint_candidate,
)
from .leaf_adjoint_checkpoint_ladder_audit import _build_case
from .open_mode_factor_tt import OpenModeFactorTTWorkspace
from .real_policy import policy_digest
from .reporting import environment_metadata
from .river import parse_cards
from .shared_resident_response_context import (
    SharedResidentAutomatonBundle,
    bind_resident_response_context,
)


_ROOT = Path(__file__).parents[2]
_CONFIG = _ROOT / "experiments/configs/h32-shared-response-allocator-lifecycle-v1.json"
_OUTPUT = _ROOT / "experiments/results/h32-shared-response-allocator-lifecycle-v1.json"
_PARENT_CONFIG = _ROOT / "experiments/configs/h32-policy-delta-verifier-audit-v1.json"
_ATOMIC_RESULT = _ROOT / "experiments/results/h32-atomic-response-preflight-v1.json"
_RESIDENCY_CONFIG = (
    _ROOT / "experiments/configs/h32-shared-response-residency-replay-v1.json"
)
_RESIDENCY_RESULT = (
    _ROOT / "experiments/results/h32-shared-response-residency-replay-v1.json"
)
_REQUIREMENTS = _ROOT / "experiments/requirements/leaf-adjoint-gpu-screen-v1.txt"
_SHARED_IMPLEMENTATION = _ROOT / "src/pontius/shared_resident_response_context.py"
_INCREMENTAL_IMPLEMENTATION = _ROOT / "src/pontius/incremental_leaf_adjoint_response.py"
_RESIDENCY_IMPLEMENTATION = _ROOT / "src/pontius/h32_shared_response_residency_replay.py"
_IMPLEMENTATION = Path(__file__)

_CONFIG_FIELDS = {
    "evidence_stage",
    "seed",
    "expected_parent_config_sha256",
    "expected_atomic_result_sha256",
    "expected_residency_config_sha256",
    "expected_residency_result_sha256",
    "expected_acceptance_source_sha256",
    "expected_candidate_source_sha256",
    "expected_ladder_source_sha256",
    "expected_extension_source_sha256",
    "expected_requirements_sha256",
    "expected_shared_implementation_sha256",
    "expected_incremental_implementation_sha256",
    "expected_residency_implementation_sha256",
    "expected_audit_implementation_sha256",
    "range_family",
    "target_shifts",
    "bundle_candidate_id",
    "atom_scale",
    "replay_order",
    "seat_order",
    "maximum_feature_width_per_batch",
    "non_cache_reserve_bytes",
    "pool_ceiling_bytes",
    "street_budget_ms",
    "emission_reserve_ms",
    "gates",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def parse_h32_shared_response_allocator_lifecycle_config(
    config: dict[str, Any],
) -> dict[str, Any]:
    """Validate the ADR-0163 allocator-lifecycle protocol."""

    if set(config) != _CONFIG_FIELDS:
        raise ValueError("allocator-lifecycle config fields differ from ADR-0163")
    frozen = {
        "evidence_stage": "preregistered_after_adr0162_before_any_allocator_trim",
        "seed": 20260821,
        "range_family": "balanced",
        "target_shifts": ["local_blocker_seat3_x2", "all_seat_strength_1_to2"],
        "bundle_candidate_id": "search_current1",
        "atom_scale": 1.0,
        "replay_order": "acting_seat_outer_then_target_shift",
        "seat_order": [0, 1, 2, 3, 4, 5],
        "maximum_feature_width_per_batch": 384,
        "non_cache_reserve_bytes": 5184456164,
        "pool_ceiling_bytes": 12000000000,
        "street_budget_ms": 15000.0,
        "emission_reserve_ms": 1000.0,
    }
    if any(config[key] != value for key, value in frozen.items()):
        raise ValueError("allocator-lifecycle workload differs from ADR-0163")
    sources = {
        "expected_parent_config_sha256": _PARENT_CONFIG,
        "expected_atomic_result_sha256": _ATOMIC_RESULT,
        "expected_residency_config_sha256": _RESIDENCY_CONFIG,
        "expected_residency_result_sha256": _RESIDENCY_RESULT,
        "expected_acceptance_source_sha256": _ACCEPTANCE_SOURCE,
        "expected_candidate_source_sha256": _CANDIDATE_SOURCE,
        "expected_ladder_source_sha256": _LADDER_SOURCE,
        "expected_extension_source_sha256": _EXTENSION_SOURCE,
        "expected_requirements_sha256": _REQUIREMENTS,
        "expected_shared_implementation_sha256": _SHARED_IMPLEMENTATION,
        "expected_incremental_implementation_sha256": _INCREMENTAL_IMPLEMENTATION,
        "expected_residency_implementation_sha256": _RESIDENCY_IMPLEMENTATION,
        "expected_audit_implementation_sha256": _IMPLEMENTATION,
    }
    for field, path in sources.items():
        if config[field] != _sha256(path):
            raise ValueError(f"allocator-lifecycle source hash mismatch for {field}")
    expected_gates = {
        "expected_context_rows": 2,
        "expected_replay_rows": 12,
        "expected_replay_seat_evaluations": 64,
        "expected_new_strategy_quality_labels": 0,
        "maximum_utility_error": 1e-9,
        "maximum_best_response_error": 1e-9,
        "maximum_deviation_gain_error": 1e-9,
        "maximum_pool_total_bytes": 12000000000,
        "minimum_physical_free_bytes": 5184456164,
        "maximum_replay_certificate_ms": 60000.0,
        "maximum_total_audit_seconds": 600.0,
        "require_target_identity": True,
        "require_policy_identity": True,
        "require_pointer_identity": True,
        "require_pool_used_identity_after_trim": True,
        "require_stop_identity": True,
        "require_work_identity": True,
    }
    if config["gates"] != expected_gates:
        raise ValueError("allocator-lifecycle gates differ from ADR-0163")
    return config


def _memory_snapshot(cp: Any) -> dict[str, int]:
    free, total = cp.cuda.runtime.memGetInfo()
    pool = cp.get_default_memory_pool()
    return {
        "gpu_free_bytes": int(free),
        "gpu_total_bytes": int(total),
        "gpu_pool_used_bytes": int(pool.used_bytes()),
        "gpu_pool_total_bytes": int(pool.total_bytes()),
    }


def _device_arrays(bundle: Any, contexts: tuple[Any, ...], gpu: Any) -> dict[str, Any]:
    arrays: dict[str, Any] = {}
    for seat, cache in enumerate(bundle.automaton_caches):
        for index, halves in enumerate(cache.half_vectors.values()):
            arrays[f"automaton/{seat}/{index}/left"] = halves[0]
            arrays[f"automaton/{seat}/{index}/right"] = halves[1]
    for context_index, context in enumerate(contexts):
        belief = context.belief_cache
        for name in (
            "mixture_weights",
            "left_component_products",
            "right_component_products",
            "left_indices",
            "right_indices",
        ):
            arrays[f"belief/{context_index}/{name}"] = getattr(belief, name)
    for direction_name in ("right_to_left", "left_to_right"):
        direction = getattr(gpu, direction_name)
        for matrix_name in ("source_matrix", "query_matrix"):
            matrix = getattr(direction, matrix_name)
            for array_name in ("data", "indices", "indptr"):
                arrays[f"sparse/{direction_name}/{matrix_name}/{array_name}"] = getattr(
                    matrix, array_name
                )
    return arrays


def _pointer_manifest(arrays: dict[str, Any]) -> dict[str, tuple[int, int]]:
    return {
        name: (int(values.data.ptr), int(values.nbytes))
        for name, values in sorted(arrays.items())
    }


def _manifest_digest(manifest: dict[str, tuple[int, int]]) -> str:
    payload = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    return hashlib.sha256(payload).hexdigest()


def _recorded_target(source: dict[str, Any], shift: str) -> dict[str, Any]:
    return next(
        target
        for target in source["targets"]
        if target["range_family"] == "balanced" and target["target_shift"] == shift
    )


def _replay_errors(live: dict[str, Any], recorded: dict[str, Any]) -> dict[str, float]:
    expected_by_seat = {
        int(row["target_player"]): row for row in recorded["seat_rows"]
    }
    return {
        "maximum_utility_error": max(
            abs(
                row["profile_utility"]
                - expected_by_seat[int(row["target_player"])]["profile_utility"]
            )
            for row in live["seat_rows"]
        ),
        "maximum_best_response_error": max(
            abs(
                row["best_response_value"]
                - expected_by_seat[int(row["target_player"])]["best_response_value"]
            )
            for row in live["seat_rows"]
        ),
        "maximum_deviation_gain_error": max(
            abs(
                row["deviation_gain"]
                - expected_by_seat[int(row["target_player"])]["deviation_gain"]
            )
            for row in live["seat_rows"]
        ),
    }


def run_h32_shared_response_allocator_lifecycle(
    config: dict[str, Any],
) -> dict[str, Any]:
    """Trim cached construction scratch and replay retained atomic labels."""

    parsed = parse_h32_shared_response_allocator_lifecycle_config(config)
    parent_config = json.loads(_PARENT_CONFIG.read_text(encoding="utf-8"))
    parent = parse_h32_policy_delta_verifier_config(parent_config)
    atomic_result = json.loads(_ATOMIC_RESULT.read_text(encoding="utf-8"))
    residency_result = json.loads(_RESIDENCY_RESULT.read_text(encoding="utf-8"))
    acceptance = json.loads(_ACCEPTANCE_SOURCE.read_text(encoding="utf-8"))
    candidate_source = json.loads(_CANDIDATE_SOURCE.read_text(encoding="utf-8"))
    ladder = json.loads(_LADDER_SOURCE.read_text(encoding="utf-8"))
    extension = json.loads(_EXTENSION_SOURCE.read_text(encoding="utf-8"))
    if not atomic_result["gates"]["passed"] or not residency_result["gates"]["passed"]:
        raise ValueError("frozen lifecycle parent gate did not pass")

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
    source_belief, layout, sparse, retained = _build_case(
        parsed=parent,
        board=board,
        hand_count=parent["wide_hands_per_player"],
        family=parsed["range_family"],
    )
    source_workspace, _, automata = retained
    gpu = CuPyBidirectionalIncidence.compile(sparse)
    workspaces = []
    target_beliefs = []
    blueprints = []
    bundles = []
    teachers = []
    target_identity = True
    policy_identity = True
    recorded_targets = []
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
        target_identity = target_identity and (
            _descriptor_core(descriptor)
            == _descriptor_core(acceptance_target["target_descriptor"])
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
        bundle_policy = next(
            row["policy"]
            for row in policies
            if row["candidate_id"] == parsed["bundle_candidate_id"]
        )
        teacher = acceptance_target["blueprint_quality"]
        recorded = _recorded_target(atomic_result, shift)
        policy_identity = policy_identity and source_identity and (
            policy_digest(blueprint) == teacher["policy_sha256"]
            == recorded["blueprint_policy_sha256"]
            and policy_digest(bundle_policy) == recorded["bundle_policy_sha256"]
        )
        workspaces.append(workspace)
        target_beliefs.append(belief)
        blueprints.append(blueprint)
        bundles.append(bundle_policy)
        teachers.append(teacher)
        recorded_targets.append(recorded)

    shared = SharedResidentAutomatonBundle.compile(workspaces[0], automata)
    contexts = tuple(
        bind_resident_response_context(
            shared,
            layout=layout,
            workspace=workspace,
            sparse=sparse,
            source_policy=blueprint,
            hands_by_player=belief.hands_by_player,
            cupy_sparse=gpu,
            maximum_feature_width_per_batch=parsed[
                "maximum_feature_width_per_batch"
            ],
        )
        for workspace, blueprint, belief in zip(
            workspaces, blueprints, target_beliefs, strict=True
        )
    )
    pre_trim = _memory_snapshot(cp)
    arrays = _device_arrays(shared, contexts, gpu)
    pre_manifest = _pointer_manifest(arrays)
    release_cupy_memory_pool()
    post_trim = _memory_snapshot(cp)
    post_manifest = _pointer_manifest(arrays)
    pointer_identity = pre_manifest == post_manifest
    pool_used_identity = (
        pre_trim["gpu_pool_used_bytes"] == post_trim["gpu_pool_used_bytes"]
    )

    replay_rows = []
    memory_rows = []
    for acting_seat in range(layout.num_players):
        for target_index, shift in enumerate(parsed["target_shifts"]):
            recorded_atom = next(
                row
                for row in recorded_targets[target_index]["atom_rows"]
                if int(row["acting_seat"]) == acting_seat
            )
            policy = interpolate_policy_atoms(
                blueprints[target_index],
                bundles[target_index],
                [recorded_atom["information_key"]],
                scale=parsed["atom_scale"],
            )
            policy_identity = policy_identity and (
                policy_digest(policy) == recorded_atom["policy_sha256"]
            )
            before = _memory_snapshot(cp)
            live = verify_incremental_leaf_adjoint_candidate(
                candidate_id=recorded_atom["candidate_id"],
                layout=layout,
                policy=policy,
                hands_by_player=target_beliefs[target_index].hands_by_player,
                response_caches=contexts[target_index].response_caches,
                blueprint_deviation_gains=tuple(
                    float(value) for value in teachers[target_index]["deviation_gains"]
                ),
                best_complete_nash_conv=float(teachers[target_index]["nash_conv"]),
                payoff_span=parent["stack"],
                raw_guard=parent["acceptance_guard_normalized"] * parent["stack"],
                seat_order=tuple(parsed["seat_order"]),
                maximum_feature_width_per_batch=parsed[
                    "maximum_feature_width_per_batch"
                ],
                belief_cache=contexts[target_index].belief_cache,
                automaton_caches=shared.automaton_caches,
                cupy_sparse=gpu,
            )
            after = _memory_snapshot(cp)
            expected = recorded_atom["incremental"]
            stop_identity = all(
                live[field] == expected[field]
                for field in (
                    "evaluated_seats",
                    "evaluated_seat_count",
                    "stop_reason",
                    "stop_seat",
                    "complete",
                )
            )
            work_identity = all(
                live[field] == expected[field]
                for field in (
                    "affected_terminal_contractions",
                    "full_terminal_contractions_for_evaluated_seats",
                    "reused_terminal_numerators",
                    "response_action_flips",
                )
            )
            replay_rows.append(
                {
                    "replay_index": len(replay_rows),
                    "range_family": parsed["range_family"],
                    "target_shift": shift,
                    "acting_seat": acting_seat,
                    "candidate_id": recorded_atom["candidate_id"],
                    "policy_sha256": policy_digest(policy),
                    "live": live,
                    "recorded_wall_ms": expected["wall_ms"],
                    "errors": _replay_errors(live, expected),
                    "stop_identity": stop_identity,
                    "work_identity": work_identity,
                    "fits_street_with_emission_reserve": (
                        live["wall_ms"] + parsed["emission_reserve_ms"]
                        <= parsed["street_budget_ms"]
                    ),
                    "memory_before": before,
                    "memory_after": after,
                }
            )
            memory_rows.extend((before, after))

    final_manifest = _pointer_manifest(arrays)
    pointer_identity = pointer_identity and final_manifest == pre_manifest
    final_memory = _memory_snapshot(cp)
    memory_rows.extend((pre_trim, post_trim, final_memory))
    maximum_pool = max(row["gpu_pool_total_bytes"] for row in memory_rows)
    minimum_free = min(row["gpu_free_bytes"] for row in memory_rows)
    maximum_utility_error = max(
        row["errors"]["maximum_utility_error"] for row in replay_rows
    )
    maximum_response_error = max(
        row["errors"]["maximum_best_response_error"] for row in replay_rows
    )
    maximum_gain_error = max(
        row["errors"]["maximum_deviation_gain_error"] for row in replay_rows
    )
    total_seconds = time.perf_counter() - started
    gates_config = parsed["gates"]
    gates = {
        "context_rows": len(contexts) == gates_config["expected_context_rows"],
        "replay_rows": len(replay_rows) == gates_config["expected_replay_rows"],
        "replay_seat_evaluations": sum(
            row["live"]["evaluated_seat_count"] for row in replay_rows
        )
        == gates_config["expected_replay_seat_evaluations"],
        "zero_new_strategy_quality_labels": gates_config[
            "expected_new_strategy_quality_labels"
        ]
        == 0,
        "target_identity": target_identity
        == gates_config["require_target_identity"],
        "policy_identity": policy_identity
        == gates_config["require_policy_identity"],
        "pointer_identity": pointer_identity
        == gates_config["require_pointer_identity"],
        "pool_used_identity_after_trim": pool_used_identity
        == gates_config["require_pool_used_identity_after_trim"],
        "stop_identity": all(row["stop_identity"] for row in replay_rows)
        == gates_config["require_stop_identity"],
        "work_identity": all(row["work_identity"] for row in replay_rows)
        == gates_config["require_work_identity"],
        "replay_exact": (
            maximum_utility_error <= gates_config["maximum_utility_error"]
            and maximum_response_error
            <= gates_config["maximum_best_response_error"]
            and maximum_gain_error
            <= gates_config["maximum_deviation_gain_error"]
        ),
        "pool_total_bytes": maximum_pool
        <= gates_config["maximum_pool_total_bytes"],
        "physical_free_bytes": minimum_free
        >= gates_config["minimum_physical_free_bytes"],
        "replay_certificate_ms": max(row["live"]["wall_ms"] for row in replay_rows)
        <= gates_config["maximum_replay_certificate_ms"],
        "total_audit_seconds": total_seconds
        <= gates_config["maximum_total_audit_seconds"],
    }
    gates["passed"] = all(gates.values())
    post_trim_and_replay_maximum_pool = max(
        row["gpu_pool_total_bytes"] for row in (post_trim, *memory_rows[: -3], final_memory)
    )
    post_trim_and_replay_minimum_free = min(
        row["gpu_free_bytes"] for row in (post_trim, *memory_rows[: -3], final_memory)
    )
    result = {
        "status": "frozen_h32_shared_response_allocator_lifecycle_executed",
        "methodology": {
            "trim_operation": "free_unreferenced_default_and_pinned_pool_blocks_once",
            "live_contexts": 2,
            "replay_labels": "retained_adr0160_atomic_labels_only",
            "replay_order": parsed["replay_order"],
            "new_strategy_quality_labels": 0,
            "strategy_selection": "forbidden",
            "strategy_quality_claim": "none",
        },
        "environment": environment_metadata(),
        "config_sha256": _sha256(_CONFIG),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "pointer_manifest": {
            "array_count": len(pre_manifest),
            "before_sha256": _manifest_digest(pre_manifest),
            "after_trim_sha256": _manifest_digest(post_manifest),
            "after_replay_sha256": _manifest_digest(final_manifest),
            "identity": pointer_identity,
        },
        "memory_before_trim": pre_trim,
        "memory_after_trim": post_trim,
        "memory_after_replay": final_memory,
        "replay_rows": replay_rows,
        "aggregate": {
            "context_rows": len(contexts),
            "replay_rows": len(replay_rows),
            "replay_seat_evaluations": sum(
                row["live"]["evaluated_seat_count"] for row in replay_rows
            ),
            "new_strategy_quality_labels": 0,
            "trimmed_pool_bytes": pre_trim["gpu_pool_total_bytes"]
            - post_trim["gpu_pool_total_bytes"],
            "pool_used_change_after_trim_bytes": post_trim["gpu_pool_used_bytes"]
            - pre_trim["gpu_pool_used_bytes"],
            "physical_free_gain_after_trim_bytes": post_trim["gpu_free_bytes"]
            - pre_trim["gpu_free_bytes"],
            "post_trim_and_replay_maximum_pool_total_bytes": (
                post_trim_and_replay_maximum_pool
            ),
            "post_trim_and_replay_minimum_physical_free_bytes": (
                post_trim_and_replay_minimum_free
            ),
            "pool_headroom_below_ceiling_bytes": parsed["pool_ceiling_bytes"]
            - post_trim_and_replay_maximum_pool,
            "headroom_rule_safe": (
                parsed["pool_ceiling_bytes"] - post_trim_and_replay_maximum_pool
                >= parsed["non_cache_reserve_bytes"]
                and post_trim_and_replay_minimum_free
                >= parsed["non_cache_reserve_bytes"]
            ),
            "maximum_utility_error": maximum_utility_error,
            "maximum_best_response_error": maximum_response_error,
            "maximum_deviation_gain_error": maximum_gain_error,
            "certificate_ms": {
                "minimum": min(row["live"]["wall_ms"] for row in replay_rows),
                "maximum": max(row["live"]["wall_ms"] for row in replay_rows),
            },
            "street_fit_with_emission_reserve": sum(
                row["fits_street_with_emission_reserve"] for row in replay_rows
            ),
            "maximum_pool_total_bytes_including_construction": maximum_pool,
            "minimum_physical_free_bytes_including_construction": minimum_free,
            "total_audit_seconds": total_seconds,
        },
        "gates": gates,
    }
    del contexts, shared, gpu
    gc.collect()
    release_cupy_memory_pool()
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=_CONFIG)
    parser.add_argument("--output", type=Path, default=_OUTPUT)
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    result = run_h32_shared_response_allocator_lifecycle(config)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "gates": result["gates"]}, indent=2))
    if not result["gates"]["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
