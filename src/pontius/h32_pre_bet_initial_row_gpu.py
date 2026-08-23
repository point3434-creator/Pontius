"""Exact h32 GPU construction for one pre-bet initial-row cache bundle.

This module is deliberately narrower than the rejected ADR-0277 capacity
runner.  It constructs the immutable-blueprint source oracle and the 2N-1
affine rows required by :mod:`pre_bet_initial_row_cache`; it has no warm
solver, master, candidate, separation, certificate, or policy-emission path.
"""

from __future__ import annotations

import ast
from collections.abc import Mapping
from dataclasses import dataclass
import gc
import hashlib
import json
import math
from pathlib import Path
import time
from typing import Any, Literal

import numpy as np

from .cupy_sparse_incidence import release_cupy_memory_pool
from .h32_pre_bet_action_width_capacity import (
    _compile_cache_arm,
    _layout_geometry,
    _memory_snapshot,
    _one_pass,
    _two_pass,
)
from .incremental_leaf_adjoint_response import (
    compile_leaf_adjoint_response_caches,
)
from .incremental_policy_tt import compile_policy_probability_tape
from .multi_size_affine_resident_leaf_adjoint_evaluation import (
    evaluate_multi_size_affine_resident_profile,
)
from .pre_bet_initial_row_cache import (
    PreBetInitialRow,
    PreBetInitialRowSource,
    PreBetRowCacheIdentity,
    assemble_pre_bet_gain_rows,
    build_pre_bet_row_cache_identity,
    lookup_pre_bet_initial_row_cache,
    write_pre_bet_initial_row_cache,
)
from .sequence_form_open_axis import (
    splice_fixed_response_probability_tape_for_axes,
)


H32PreBetArm = Literal["one_size", "two_size"]
_PACKAGE = Path(__file__).resolve().parent
_ROOT_MODULES = (
    "pontius.h32_pre_bet_initial_row_gpu",
    "pontius.h32_pre_bet_action_width_capacity",
    "pontius.pre_bet_initial_row_cache",
)
_MANIFEST_SCHEMA = "pontius-h32-pre-bet-gpu-row-primitive-manifest-v1"


def _json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def _module_path(module_name: str) -> Path | None:
    prefix = "pontius."
    if not module_name.startswith(prefix):
        return None
    relative = module_name[len(prefix) :].replace(".", "/")
    module_path = _PACKAGE / f"{relative}.py"
    if module_path.is_file():
        return module_path
    package_path = _PACKAGE / relative / "__init__.py"
    return package_path if package_path.is_file() else None


def _resolve_from_import(
    current_module: str,
    node: ast.ImportFrom,
) -> tuple[str, ...]:
    if node.level:
        package = current_module.split(".")[:-1]
        remove = node.level - 1
        if remove > len(package):
            return ()
        base = package[: len(package) - remove]
        if node.module:
            base.extend(node.module.split("."))
        resolved = ".".join(base)
    else:
        resolved = node.module or ""
    candidates = []
    if resolved.startswith("pontius"):
        candidates.append(resolved)
        if node.module is None:
            candidates.extend(f"{resolved}.{alias.name}" for alias in node.names)
    return tuple(candidates)


def _pontius_import_closure(root_modules: tuple[str, ...]) -> tuple[dict[str, Any], ...]:
    """Hash the literal local-source closure of the frozen primitive roots."""

    pending = list(root_modules)
    observed: set[str] = set()
    records: list[dict[str, Any]] = []
    while pending:
        module_name = pending.pop()
        if module_name in observed:
            continue
        path = _module_path(module_name)
        if path is None:
            raise ValueError(f"h32 row primitive module is unavailable: {module_name}")
        observed.add(module_name)
        payload = path.read_bytes()
        canonical_payload = payload.replace(b"\r\n", b"\n")
        if b"\r" in canonical_payload:
            raise ValueError(
                f"h32 row primitive module has unsupported line endings: {module_name}"
            )
        try:
            tree = ast.parse(canonical_payload, filename=str(path))
        except (SyntaxError, UnicodeDecodeError) as exc:
            raise ValueError(
                f"h32 row primitive module cannot be parsed: {module_name}"
            ) from exc
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(
                    alias.name for alias in node.names if alias.name.startswith("pontius.")
                )
            elif isinstance(node, ast.ImportFrom):
                imported.update(_resolve_from_import(module_name, node))
        for candidate in sorted(imported, reverse=True):
            if _module_path(candidate) is not None and candidate not in observed:
                pending.append(candidate)
        records.append(
            {
                "module": module_name,
                "path": path.relative_to(_PACKAGE.parent.parent).as_posix(),
                "hash_mode": "canonical_lf",
                "byte_length": len(canonical_payload),
                "sha256": hashlib.sha256(canonical_payload).hexdigest(),
            }
        )
    return tuple(sorted(records, key=lambda row: row["module"]))


def h32_gpu_row_primitive_manifest(
    arm_name: H32PreBetArm,
    parsed: Mapping[str, Any],
) -> dict[str, Any]:
    """Return a distinct, source-closed manifest for one GPU row primitive."""

    if arm_name not in ("one_size", "two_size"):
        raise ValueError("h32 pre-bet row primitive arm is invalid")
    contract = {
        "arm": arm_name,
        "dtype": "Float64",
        "players": int(parsed["players"]),
        "hands_per_player": int(parsed["hands_per_player"]),
        "maximum_feature_width_per_batch": int(
            parsed["maximum_feature_width_per_batch"]
        ),
        "current_public_node": 0,
        "role_order": "all_profiles_then_nonacting_fixed_responses",
        "source_oracle": (
            "compile_leaf_adjoint_response_caches"
            if arm_name == "one_size"
            else "evaluate_multi_size_affine_resident_profile"
        ),
        "row_pass": (
            "evaluate_device_fold_cross_payoff_leaf_adjoint"
            if arm_name == "one_size"
            else "evaluate_multi_size_affine_cross_payoff"
        ),
        "record_to_hand_backend": (
            "gpu_cupy" if arm_name == "one_size" else "multi_size_affine_default"
        ),
        "required_numpy_version": str(parsed["required_numpy_version"]),
        "required_cupy_version": str(parsed["required_cupy_version"]),
        "required_cuda_runtime_version": int(parsed["required_cuda_runtime_version"]),
        "minimum_cuda_driver_version": int(parsed["minimum_cuda_driver_version"]),
        "required_compute_capability": str(parsed["required_compute_capability"]),
    }
    return {
        "schema": _MANIFEST_SCHEMA,
        "contract": contract,
        "files": list(_pontius_import_closure(_ROOT_MODULES)),
    }


def h32_gpu_row_primitive_digest(
    arm_name: H32PreBetArm,
    parsed: Mapping[str, Any],
) -> str:
    """Digest the complete literal manifest used in cache identity."""

    return hashlib.sha256(
        _json_bytes(h32_gpu_row_primitive_manifest(arm_name, parsed))
    ).hexdigest()


@dataclass(frozen=True, slots=True)
class _SourceOracle:
    probabilities: tuple[np.ndarray | None, ...]
    evaluations: tuple[Any, ...]
    wall_ms: float
    reported_wall_ms: float | None
    owner: object


def _source_oracle(
    parsed: Mapping[str, Any],
    cp: Any,
    target: Mapping[str, Any],
    arm_name: H32PreBetArm,
    belief_cache: Any,
    caches: tuple[Any, ...],
) -> _SourceOracle:
    arm = target["arms"][arm_name]
    layout = arm["layout"]
    blueprint = arm["blueprint"]
    belief = target["belief"]
    cp.cuda.runtime.deviceSynchronize()
    started_ns = time.perf_counter_ns()
    if arm_name == "one_size":
        owner = compile_leaf_adjoint_response_caches(
            layout,
            target["workspace"],
            target["sparse"],
            blueprint,
            tuple(arm["automata"]),
            hands_by_player=belief.hands_by_player,
            maximum_feature_width_per_batch=int(
                parsed["maximum_feature_width_per_batch"]
            ),
            belief_cache=belief_cache,
            automaton_caches=caches,
            cupy_sparse=target["gpu"],
        )
        probabilities = owner[0].source_probabilities
        evaluations = tuple(cache.source_evaluation for cache in owner)
        reported_wall_ms = None
    else:
        owner = evaluate_multi_size_affine_resident_profile(
            layout,
            target["workspace"],
            target["sparse"],
            blueprint,
            arm["automata"],
            belief_cache=belief_cache,
            automaton_caches=caches,
            cupy_sparse=target["gpu"],
            hands_by_player=belief.hands_by_player,
            maximum_feature_width_per_batch=int(
                parsed["maximum_feature_width_per_batch"]
            ),
        )
        probabilities = compile_policy_probability_tape(
            layout,
            belief.hands_by_player,
            blueprint,
        )
        evaluations = tuple(owner.seats)
        reported_wall_ms = float(owner.wall_ms)
    cp.cuda.runtime.deviceSynchronize()
    return _SourceOracle(
        probabilities=probabilities,
        evaluations=evaluations,
        wall_ms=(time.perf_counter_ns() - started_ns) / 1_000_000.0,
        reported_wall_ms=reported_wall_ms,
        owner=owner,
    )


def _identity_digest(identity: PreBetRowCacheIdentity) -> str:
    return hashlib.sha256(_json_bytes(identity.to_record())).hexdigest()


def seed_h32_pre_bet_initial_row_cache(
    parsed: Mapping[str, Any],
    cp: Any,
    target: Mapping[str, Any],
    arm_name: H32PreBetArm,
    cache_path: Path,
) -> dict[str, Any]:
    """Construct, atomically persist, and mechanically round-trip one bundle."""

    if arm_name not in ("one_size", "two_size"):
        raise ValueError("h32 pre-bet cache seed arm is invalid")
    arm = target["arms"][arm_name]
    layout = arm["layout"]
    blueprint = arm["blueprint"]
    belief = target["belief"]
    acting_player = int(target["spec"]["acting_player"])
    primitive_manifest = h32_gpu_row_primitive_manifest(arm_name, parsed)
    primitive_sha256 = hashlib.sha256(_json_bytes(primitive_manifest)).hexdigest()
    belief_cache = None
    caches: tuple[Any, ...] = ()
    source_oracle: _SourceOracle | None = None
    try:
        cache_row, belief_cache, caches = _compile_cache_arm(
            cp,
            target,
            arm_name,
            parsed,
        )
        if not cache_row["safe_for_runtime"]:
            raise MemoryError("h32 row-cache seed opened after failed memory safety")
        source_oracle = _source_oracle(
            parsed,
            cp,
            target,
            arm_name,
            belief_cache,
            caches,
        )
        identity = build_pre_bet_row_cache_identity(
            layout,
            belief,
            belief.hands_by_player,
            blueprint,
            source_oracle.probabilities,
            acting_player=acting_player,
            public_node=0,
            row_primitive_sha256=primitive_sha256,
        )
        pass_function = _one_pass if arm_name == "one_size" else _two_pass
        sources: list[PreBetInitialRowSource] = []
        rows: list[PreBetInitialRow] = []
        pass_rows: list[dict[str, Any]] = []
        source_errors: list[float] = []
        cp.cuda.runtime.deviceSynchronize()
        rows_started_ns = time.perf_counter_ns()
        for payoff_player in range(layout.num_players):
            evaluation = source_oracle.evaluations[payoff_player]
            row, telemetry = pass_function(
                target,
                source_oracle.probabilities,
                acting_player=acting_player,
                payoff_player=payoff_player,
                source_value=float(evaluation.profile_utility),
                belief_cache=belief_cache,
                caches=caches,
                cp=cp,
                parsed=parsed,
            )
            telemetry["kind"] = "profile"
            source = PreBetInitialRowSource(
                "profile",
                payoff_player,
                source_oracle.probabilities,
                float(evaluation.profile_utility),
            )
            item = PreBetInitialRow("profile", payoff_player, row)
            sources.append(source)
            rows.append(item)
            pass_rows.append(telemetry)
            source_errors.append(
                abs(row.value(source.probabilities) - source.source_value)
            )
        for payoff_player in range(layout.num_players):
            if payoff_player == acting_player:
                continue
            evaluation = source_oracle.evaluations[payoff_player]
            response_probabilities = splice_fixed_response_probability_tape_for_axes(
                layout,
                source_oracle.probabilities,
                evaluation.best_response_actions,
                responding_player=payoff_player,
                hands_by_player=belief.hands_by_player,
            )
            row, telemetry = pass_function(
                target,
                response_probabilities,
                acting_player=acting_player,
                payoff_player=payoff_player,
                source_value=float(evaluation.best_response_value),
                belief_cache=belief_cache,
                caches=caches,
                cp=cp,
                parsed=parsed,
            )
            telemetry["kind"] = "fixed_response"
            source = PreBetInitialRowSource(
                "fixed_response",
                payoff_player,
                response_probabilities,
                float(evaluation.best_response_value),
            )
            item = PreBetInitialRow("fixed_response", payoff_player, row)
            sources.append(source)
            rows.append(item)
            pass_rows.append(telemetry)
            source_errors.append(
                abs(row.value(source.probabilities) - source.source_value)
            )
        cp.cuda.runtime.deviceSynchronize()
        initial_row_ms = (time.perf_counter_ns() - rows_started_ns) / 1_000_000.0
        gains = assemble_pre_bet_gain_rows(
            identity,
            sources,
            rows,
            acting_best_response_value=float(
                source_oracle.evaluations[acting_player].best_response_value
            ),
        )
        expected_gains = tuple(
            float(evaluation.best_response_value - evaluation.profile_utility)
            for evaluation in source_oracle.evaluations
        )
        gain_errors = tuple(
            abs(gain.value(source_oracle.probabilities) - expected)
            for gain, expected in zip(gains, expected_gains, strict=True)
        )

        write_started_ns = time.perf_counter_ns()
        persisted_sha256 = write_pre_bet_initial_row_cache(
            cache_path,
            identity,
            sources,
            rows,
        )
        cache_write_ms = (time.perf_counter_ns() - write_started_ns) / 1_000_000.0
        lookup = lookup_pre_bet_initial_row_cache(
            cache_path,
            persisted_sha256,
            identity,
            sources,
        )
        if not lookup.hit or lookup.rows is None:
            raise ArithmeticError("fresh h32 row cache failed mechanical round trip")
        exact_row_byte_round_trip = all(
            original.row.flattened().tobytes(order="C")
            == restored.row.flattened().tobytes(order="C")
            for original, restored in zip(rows, lookup.rows, strict=True)
        )
        if not exact_row_byte_round_trip:
            raise ArithmeticError("fresh h32 row cache changed affine row bytes")
        persisted = cache_path.read_bytes()
        if hashlib.sha256(persisted).hexdigest() != persisted_sha256:
            raise OSError("fresh h32 row cache byte hash changed after validation")
        memory = _memory_snapshot(cp)
        if any(
            not math.isfinite(float(value)) or float(value) < 0.0
            for value in (
                source_oracle.wall_ms,
                initial_row_ms,
                cache_write_ms,
                lookup.lookup_validation_ms,
                *source_errors,
                *gain_errors,
            )
        ):
            raise ArithmeticError("fresh h32 row cache telemetry is nonfinite")
        return {
            "arm": arm_name,
            "blueprint_sha256": arm["blueprint_sha256"],
            "geometry": _layout_geometry(target, arm_name),
            "row_primitive_sha256": primitive_sha256,
            "row_primitive_file_count": len(primitive_manifest["files"]),
            "cache_identity_sha256": _identity_digest(identity),
            "cache_identity": identity.to_record(),
            "cache_sha256": persisted_sha256,
            "cache_bytes": len(persisted),
            "cache_hash_status": "observed_untrusted_until_external_seal",
            "cache": cache_row,
            "source_oracle_ms": source_oracle.wall_ms,
            "source_oracle_reported_ms": source_oracle.reported_wall_ms,
            "baseline_seat_evaluations": len(source_oracle.evaluations),
            "initial_profile_rows": sum(row["kind"] == "profile" for row in pass_rows),
            "initial_response_rows": sum(
                row["kind"] == "fixed_response" for row in pass_rows
            ),
            "initial_rows": len(rows),
            "initial_gain_rows": len(gains),
            "initial_row_ms": initial_row_ms,
            "initial_pass_rows": pass_rows,
            "maximum_source_row_error": max(source_errors),
            "maximum_gain_source_error": max(gain_errors),
            "cache_write_ms": cache_write_ms,
            "mechanical_round_trip_lookup_ms": lookup.lookup_validation_ms,
            "mechanical_round_trip_reason": lookup.reason,
            "exact_row_byte_round_trip": exact_row_byte_round_trip,
            "memory_after_seed": memory,
            "warm_steps": 0,
            "master_solves": 0,
            "candidate_endpoint_evaluations": 0,
            "separation_or_certificate_evaluations": 0,
            "strategy_quality_rows": 0,
            "candidate_policies_emitted": 0,
        }
    finally:
        source_oracle = None
        caches = ()
        belief_cache = None
        gc.collect()
        release_cupy_memory_pool()
