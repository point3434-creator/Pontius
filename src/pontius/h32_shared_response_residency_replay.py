"""Frozen h32 replay of one shared automaton bundle across two belief shifts."""

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
from .h32_warm_search_acceptance_audit import build_target_belief
from .leaf_adjoint_checkpoint_ladder_audit import _build_case
from .open_mode_factor_tt import OpenModeFactorTTWorkspace
from .real_policy import policy_digest
from .reporting import environment_metadata
from .river import parse_cards
from .shared_resident_response_context import (
    SharedResidentAutomatonBundle,
    bind_resident_response_context,
    shared_device_numeric_bytes,
    unique_response_numeric_bytes,
)


_ROOT = Path(__file__).parents[2]
_CONFIG = _ROOT / "experiments/configs/h32-shared-response-residency-replay-v1.json"
_OUTPUT = _ROOT / "experiments/results/h32-shared-response-residency-replay-v1.json"
_PARENT_CONFIG = _ROOT / "experiments/configs/h32-policy-delta-verifier-audit-v1.json"
_PARENT_RESULT = _ROOT / "experiments/results/h32-policy-delta-verifier-audit-v1.json"
_ATOMIC_RESULT = _ROOT / "experiments/results/h32-atomic-response-preflight-v1.json"
_REQUIREMENTS = _ROOT / "experiments/requirements/leaf-adjoint-gpu-screen-v1.txt"
_SHARED_IMPLEMENTATION = _ROOT / "src/pontius/shared_resident_response_context.py"
_INCREMENTAL_IMPLEMENTATION = _ROOT / "src/pontius/incremental_leaf_adjoint_response.py"
_IMPLEMENTATION = Path(__file__)

_CONFIG_FIELDS = {
    "evidence_stage",
    "seed",
    "expected_parent_config_sha256",
    "expected_parent_result_sha256",
    "expected_atomic_result_sha256",
    "expected_acceptance_source_sha256",
    "expected_candidate_source_sha256",
    "expected_ladder_source_sha256",
    "expected_extension_source_sha256",
    "expected_requirements_sha256",
    "expected_shared_implementation_sha256",
    "expected_incremental_implementation_sha256",
    "expected_audit_implementation_sha256",
    "range_family",
    "target_shifts",
    "source_policy",
    "maximum_feature_width_per_batch",
    "non_cache_reserve_bytes",
    "pool_ceiling_bytes",
    "gates",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def _object_digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _descriptor_core(descriptor: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in descriptor.items()
        if key
        not in {
            "source_partition",
            "target_partition",
            "target_to_source_partition_ratio",
            "marginal_total_variations",
            "mean_marginal_total_variation",
            "maximum_marginal_total_variation",
            "marginal_measurement_ms",
        }
    }


def parse_h32_shared_response_residency_config(
    config: dict[str, Any],
) -> dict[str, Any]:
    """Validate the outcome-neutral ADR-0161 protocol."""

    if set(config) != _CONFIG_FIELDS:
        raise ValueError("shared-response config fields differ from ADR-0161")
    frozen = {
        "evidence_stage": "preregistered_after_adr0160_before_shared_h32_residency",
        "seed": 20260821,
        "range_family": "balanced",
        "target_shifts": ["local_blocker_seat3_x2", "all_seat_strength_1_to2"],
        "source_policy": "blueprint_average64",
        "maximum_feature_width_per_batch": 384,
        "non_cache_reserve_bytes": 5184456164,
        "pool_ceiling_bytes": 12000000000,
    }
    if any(config[key] != value for key, value in frozen.items()):
        raise ValueError("shared-response workload differs from ADR-0161")
    sources = {
        "expected_parent_config_sha256": _PARENT_CONFIG,
        "expected_parent_result_sha256": _PARENT_RESULT,
        "expected_atomic_result_sha256": _ATOMIC_RESULT,
        "expected_acceptance_source_sha256": _ACCEPTANCE_SOURCE,
        "expected_candidate_source_sha256": _CANDIDATE_SOURCE,
        "expected_ladder_source_sha256": _LADDER_SOURCE,
        "expected_extension_source_sha256": _EXTENSION_SOURCE,
        "expected_requirements_sha256": _REQUIREMENTS,
        "expected_shared_implementation_sha256": _SHARED_IMPLEMENTATION,
        "expected_incremental_implementation_sha256": _INCREMENTAL_IMPLEMENTATION,
        "expected_audit_implementation_sha256": _IMPLEMENTATION,
    }
    for field, path in sources.items():
        if config[field] != _sha256(path):
            raise ValueError(f"shared-response source hash mismatch for {field}")
    expected_gates = {
        "expected_context_rows": 2,
        "expected_source_seat_evaluations": 12,
        "expected_new_strategy_quality_labels": 0,
        "maximum_utility_error": 1e-9,
        "maximum_best_response_error": 1e-9,
        "maximum_deviation_gain_error": 1e-9,
        "maximum_shared_device_numeric_bytes": 5000000000,
        "maximum_unique_response_numeric_bytes": 1000000,
        "maximum_pool_total_bytes": 12000000000,
        "minimum_physical_free_bytes": 5184456164,
        "maximum_bundle_compile_ms": 120000.0,
        "maximum_context_bind_ms": 60000.0,
        "maximum_total_audit_seconds": 600.0,
        "require_target_identity": True,
        "require_policy_identity": True,
        "require_shared_topology_identity": True,
    }
    if config["gates"] != expected_gates:
        raise ValueError("shared-response gates differ from ADR-0161")
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


def _source_errors(response_caches: tuple[Any, ...], teacher: dict[str, Any]) -> dict[str, float]:
    return {
        "maximum_utility_error": max(
            abs(cache.source_evaluation.profile_utility - teacher["utilities"][seat])
            for seat, cache in enumerate(response_caches)
        ),
        "maximum_best_response_error": max(
            abs(
                cache.source_evaluation.best_response_value
                - teacher["best_response_values"][seat]
            )
            for seat, cache in enumerate(response_caches)
        ),
        "maximum_deviation_gain_error": max(
            abs(
                cache.source_evaluation.deviation_gain
                - teacher["deviation_gains"][seat]
            )
            for seat, cache in enumerate(response_caches)
        ),
    }


def run_h32_shared_response_residency_replay(
    config: dict[str, Any],
) -> dict[str, Any]:
    """Build two target contexts around one h32 automaton payload."""

    parsed = parse_h32_shared_response_residency_config(config)
    parent_config = json.loads(_PARENT_CONFIG.read_text(encoding="utf-8"))
    parent = parse_h32_policy_delta_verifier_config(parent_config)
    parent_result = json.loads(_PARENT_RESULT.read_text(encoding="utf-8"))
    atomic_result = json.loads(_ATOMIC_RESULT.read_text(encoding="utf-8"))
    acceptance = json.loads(_ACCEPTANCE_SOURCE.read_text(encoding="utf-8"))
    candidate_source = json.loads(_CANDIDATE_SOURCE.read_text(encoding="utf-8"))
    ladder = json.loads(_LADDER_SOURCE.read_text(encoding="utf-8"))
    extension = json.loads(_EXTENSION_SOURCE.read_text(encoding="utf-8"))
    if not parent_result["gates"]["passed"] or not atomic_result["gates"]["passed"]:
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
    source_belief, layout, sparse, retained = _build_case(
        parsed=parent,
        board=board,
        hand_count=parent["wide_hands_per_player"],
        family=parsed["range_family"],
    )
    source_workspace, _, automata = retained
    gpu = CuPyBidirectionalIncidence.compile(sparse)
    target_rows = []
    workspaces = []
    blueprints = []
    teachers = []
    target_beliefs = []
    target_descriptors = []
    target_identity = True
    policy_identity = True
    for shift in parsed["target_shifts"]:
        acceptance_target = _source_target(
            acceptance, family=parsed["range_family"], shift=shift
        )
        candidate_target = _source_target(
            candidate_source, family=parsed["range_family"], shift=shift
        )
        target_belief, descriptor = build_target_belief(
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
            target_belief,
            query_chunk_records=parent["query_chunk_records"],
        )
        workspace = OpenModeFactorTTWorkspace.compile(source_workspace.topology, base)
        blueprint, _, source_identity = reconstruct_candidate_policies(
            family=parsed["range_family"],
            acceptance_target=acceptance_target,
            candidate_target=candidate_target,
            ladder_source=ladder,
            extension_source=extension,
            candidate_order=tuple(parent["candidate_order"]),
        )
        teacher = acceptance_target["blueprint_quality"]
        policy_identity = policy_identity and source_identity and (
            policy_digest(blueprint) == teacher["policy_sha256"]
        )
        workspaces.append(workspace)
        blueprints.append(blueprint)
        teachers.append(teacher)
        target_beliefs.append(target_belief)
        target_descriptors.append(descriptor)

    before_bundle = _memory_snapshot(cp)
    bundle = SharedResidentAutomatonBundle.compile(workspaces[0], automata)
    after_bundle = _memory_snapshot(cp)
    contexts = []
    for shift, workspace, blueprint, teacher, target_belief, descriptor in zip(
        parsed["target_shifts"],
        workspaces,
        blueprints,
        teachers,
        target_beliefs,
        target_descriptors,
        strict=True,
    ):
        before = _memory_snapshot(cp)
        context = bind_resident_response_context(
            bundle,
            layout=layout,
            workspace=workspace,
            sparse=sparse,
            source_policy=blueprint,
            hands_by_player=target_belief.hands_by_player,
            cupy_sparse=gpu,
            maximum_feature_width_per_batch=parsed[
                "maximum_feature_width_per_batch"
            ],
        )
        after = _memory_snapshot(cp)
        contexts.append(context)
        target_rows.append(
            {
                "range_family": parsed["range_family"],
                "target_shift": shift,
                "target_descriptor_sha256": _object_digest(
                    _descriptor_core(descriptor)
                ),
                "blueprint_policy_sha256": policy_digest(blueprint),
                "belief_cache_numeric_bytes": context.numeric_bytes,
                "belief_cache_compile_ms": context.belief_compile_ms,
                "response_cache_compile_ms": context.response_compile_ms,
                "context_bind_ms": (
                    context.belief_compile_ms + context.response_compile_ms
                ),
                "response_cache_raw_numeric_bytes": sum(
                    cache.persistent_numeric_bytes for cache in context.response_caches
                ),
                "source_terminal_contractions": sum(
                    cache.terminal_contractions for cache in context.response_caches
                ),
                "source_maximum_terminal_middle_rank": max(
                    cache.source_evaluation.maximum_terminal_middle_rank
                    for cache in context.response_caches
                ),
                "source_errors": _source_errors(context.response_caches, teacher),
                "memory_before_bind": before,
                "memory_after_bind": after,
            }
        )

    context_tuple = tuple(contexts)
    shared_device_bytes = shared_device_numeric_bytes(bundle, context_tuple)
    duplicated_device_bytes = sum(
        bundle.numeric_bytes + context.numeric_bytes for context in contexts
    )
    unique_response_bytes = unique_response_numeric_bytes(context_tuple)
    after_all = _memory_snapshot(cp)
    total_seconds = time.perf_counter() - started
    maximum_utility_error = max(
        row["source_errors"]["maximum_utility_error"] for row in target_rows
    )
    maximum_response_error = max(
        row["source_errors"]["maximum_best_response_error"] for row in target_rows
    )
    maximum_gain_error = max(
        row["source_errors"]["maximum_deviation_gain_error"] for row in target_rows
    )
    minimum_free = min(
        snapshot["gpu_free_bytes"]
        for snapshot in (
            before_bundle,
            after_bundle,
            *(row["memory_after_bind"] for row in target_rows),
            after_all,
        )
    )
    maximum_pool = max(
        snapshot["gpu_pool_total_bytes"]
        for snapshot in (
            before_bundle,
            after_bundle,
            *(row["memory_after_bind"] for row in target_rows),
            after_all,
        )
    )
    gates_config = parsed["gates"]
    shared_topology_identity = all(
        context.workspace.topology is bundle.topology for context in contexts
    ) and all(cache.topology is bundle.topology for cache in bundle.automaton_caches)
    gates = {
        "context_rows": len(target_rows) == gates_config["expected_context_rows"],
        "source_seat_evaluations": len(target_rows) * layout.num_players
        == gates_config["expected_source_seat_evaluations"],
        "zero_new_strategy_quality_labels": gates_config[
            "expected_new_strategy_quality_labels"
        ]
        == 0,
        "target_identity": target_identity
        == gates_config["require_target_identity"],
        "policy_identity": policy_identity
        == gates_config["require_policy_identity"],
        "shared_topology_identity": shared_topology_identity
        == gates_config["require_shared_topology_identity"],
        "source_exact": (
            maximum_utility_error <= gates_config["maximum_utility_error"]
            and maximum_response_error
            <= gates_config["maximum_best_response_error"]
            and maximum_gain_error
            <= gates_config["maximum_deviation_gain_error"]
        ),
        "shared_device_numeric_bytes": shared_device_bytes
        <= gates_config["maximum_shared_device_numeric_bytes"],
        "unique_response_numeric_bytes": unique_response_bytes
        <= gates_config["maximum_unique_response_numeric_bytes"],
        "pool_total_bytes": maximum_pool
        <= gates_config["maximum_pool_total_bytes"],
        "physical_free_bytes": minimum_free
        >= gates_config["minimum_physical_free_bytes"],
        "bundle_compile_ms": bundle.compile_ms
        <= gates_config["maximum_bundle_compile_ms"],
        "context_bind_ms": max(row["context_bind_ms"] for row in target_rows)
        <= gates_config["maximum_context_bind_ms"],
        "total_audit_seconds": total_seconds
        <= gates_config["maximum_total_audit_seconds"],
    }
    gates["passed"] = all(gates.values())
    result = {
        "status": "frozen_h32_shared_response_residency_replay_executed",
        "methodology": {
            "shared_payload": "one_immutable_topology_automaton_bundle",
            "target_payload": "one_belief_cache_and_blueprint_response_overlay_per_shift",
            "source_quality": "retained_blueprint_teacher_only",
            "new_strategy_quality_labels": 0,
            "strategy_selection": "forbidden",
            "strategy_quality_claim": "none",
        },
        "environment": environment_metadata(),
        "config_sha256": _sha256(_CONFIG),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "memory_before_bundle": before_bundle,
        "memory_after_bundle": after_bundle,
        "memory_after_all_contexts": after_all,
        "bundle": {
            "compile_ms": bundle.compile_ms,
            "numeric_bytes": bundle.numeric_bytes,
            "seat_caches": len(bundle.automaton_caches),
            "total_middle_rank": sum(
                cache.total_middle_rank for cache in bundle.automaton_caches
            ),
            "maximum_middle_rank": max(
                cache.maximum_middle_rank for cache in bundle.automaton_caches
            ),
        },
        "target_rows": target_rows,
        "aggregate": {
            "context_rows": len(target_rows),
            "source_seat_evaluations": len(target_rows) * layout.num_players,
            "new_strategy_quality_labels": 0,
            "shared_device_numeric_bytes": shared_device_bytes,
            "duplicated_device_numeric_bytes": duplicated_device_bytes,
            "device_numeric_bytes_saved": duplicated_device_bytes
            - shared_device_bytes,
            "shared_to_duplicated_device_ratio": shared_device_bytes
            / duplicated_device_bytes,
            "unique_response_numeric_bytes": unique_response_bytes,
            "maximum_pool_total_bytes": maximum_pool,
            "minimum_physical_free_bytes": minimum_free,
            "pool_headroom_below_ceiling_bytes": parsed["pool_ceiling_bytes"]
            - maximum_pool,
            "headroom_rule_safe": (
                parsed["pool_ceiling_bytes"] - maximum_pool
                >= parsed["non_cache_reserve_bytes"]
                and minimum_free >= parsed["non_cache_reserve_bytes"]
            ),
            "maximum_utility_error": maximum_utility_error,
            "maximum_best_response_error": maximum_response_error,
            "maximum_deviation_gain_error": maximum_gain_error,
            "bundle_compile_ms": bundle.compile_ms,
            "total_context_bind_ms": sum(
                row["context_bind_ms"] for row in target_rows
            ),
            "total_cold_construction_ms": bundle.compile_ms
            + sum(row["context_bind_ms"] for row in target_rows),
            "total_audit_seconds": total_seconds,
        },
        "gates": gates,
    }
    del contexts, context_tuple, bundle, gpu
    gc.collect()
    release_cupy_memory_pool()
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=_CONFIG)
    parser.add_argument("--output", type=Path, default=_OUTPUT)
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    result = run_h32_shared_response_residency_replay(config)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "gates": result["gates"]}, indent=2))
    if not result["gates"]["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
