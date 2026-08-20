"""Run the frozen dense-free leaf-adjoint best-response quality audit."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import time
from typing import Any

import numpy as np

from .axis_public_cfr import AxisPublicCFRState
from .cupy_sparse_incidence import (
    CuPyBidirectionalIncidence,
    _cupy_modules,
    release_cupy_memory_pool,
)
from .incremental_policy_tt import compile_policy_probability_tape
from .leaf_adjoint_cfr import build_leaf_adjoint_terminal_automata
from .leaf_adjoint_evaluation import (
    LeafAdjointProfileEvaluation,
    evaluate_leaf_adjoint_profile,
    evaluate_leaf_adjoint_seat,
)
from .open_mode_audit import (
    _canonical_belief,
    _open_workspace,
    _policy_from_json,
)
from .public_policy_tt import representative_public_tree
from .public_tree_tensor import PublicTreeTensorEvaluator
from .real_policy import policy_digest
from .reporting import environment_metadata
from .river import format_card, parse_cards
from .showdown_value_rank_screen import _game_from_belief, _rank_codes
from .sparse_incidence_open_mode import SparseBidirectionalIncidence

_ROOT = Path(__file__).parents[2]
_CONFIG = _ROOT / "experiments" / "configs" / "leaf-adjoint-evaluation-audit-v1.json"
_SMALL_SOURCE = _ROOT / "experiments" / "results" / "real-policy-source-v1.json"
_WIDE_SOURCE = (
    _ROOT / "experiments" / "results" / "leaf-adjoint-cfr-gpu-audit-v1.json"
)
_IMPLEMENTATION = Path(__file__)

_CONFIG_FIELDS = {
    "evidence_stage",
    "seed",
    "axis_seed",
    "expected_small_source_sha256",
    "expected_wide_source_sha256",
    "expected_requirements_sha256",
    "expected_cupy_sparse_incidence_sha256",
    "expected_heterogeneous_leaf_sha256",
    "expected_leaf_adjoint_cfr_sha256",
    "expected_leaf_adjoint_evaluation_sha256",
    "expected_sparse_incidence_sha256",
    "expected_structured_showdown_sha256",
    "expected_audit_implementation_sha256",
    "board",
    "pot",
    "stack",
    "bet_size",
    "players",
    "small_hands_per_player",
    "small_policy_kinds",
    "small_source_checkpoint",
    "wide_hands_per_player",
    "range_families",
    "validation_family",
    "wide_policy_kinds",
    "mixture_components",
    "split_index",
    "query_chunk_records",
    "maximum_feature_width_per_batch",
    "cpu_crosscheck_target",
    "required_numpy_version",
    "required_scipy_version",
    "required_cupy_version",
    "required_cuda_runtime_version",
    "minimum_cuda_driver_version",
    "required_compute_capability",
    "cuda_dll_environment_variable",
    "gates",
}
_GATE_FIELDS = {
    "expected_small_rows",
    "maximum_small_utility_error",
    "maximum_small_best_response_error",
    "maximum_small_deviation_gain_error",
    "maximum_small_nash_conv_error",
    "maximum_small_selected_response_value_error",
    "maximum_small_zero_sum_residual",
    "expected_wide_rows",
    "expected_wide_profiles_per_family",
    "maximum_wide_cpu_gpu_profile_utility_error",
    "maximum_wide_cpu_gpu_best_response_error",
    "maximum_wide_cpu_gpu_deviation_gain_error",
    "maximum_wide_zero_sum_residual",
    "minimum_validation_charged_gpu_speedup",
    "minimum_all_charged_gpu_speedup",
    "maximum_wide_profile_evaluation_ms",
    "maximum_wide_host_peak_numeric_bytes",
    "maximum_wide_gpu_pool_bytes",
    "expected_wide_information_sets",
    "expected_wide_response_actions_per_seat",
    "minimum_average2_normalized_nash_conv_improvement",
    "require_finite_wide_evaluations",
}
_SOURCE_PATHS = {
    "expected_small_source_sha256": _SMALL_SOURCE,
    "expected_wide_source_sha256": _WIDE_SOURCE,
    "expected_requirements_sha256": (
        _ROOT / "experiments" / "requirements" / "leaf-adjoint-gpu-screen-v1.txt"
    ),
    "expected_cupy_sparse_incidence_sha256": (
        _ROOT / "src" / "pontius" / "cupy_sparse_incidence.py"
    ),
    "expected_heterogeneous_leaf_sha256": (
        _ROOT / "src" / "pontius" / "heterogeneous_leaf_contraction.py"
    ),
    "expected_leaf_adjoint_cfr_sha256": (
        _ROOT / "src" / "pontius" / "leaf_adjoint_cfr.py"
    ),
    "expected_leaf_adjoint_evaluation_sha256": (
        _ROOT / "src" / "pontius" / "leaf_adjoint_evaluation.py"
    ),
    "expected_sparse_incidence_sha256": (
        _ROOT / "src" / "pontius" / "sparse_incidence_open_mode.py"
    ),
    "expected_structured_showdown_sha256": (
        _ROOT / "src" / "pontius" / "structured_showdown_automaton.py"
    ),
    "expected_audit_implementation_sha256": _IMPLEMENTATION,
}


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required frozen input is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_leaf_adjoint_evaluation_audit_config(
    config: dict[str, Any],
) -> dict[str, Any]:
    if set(config) != _CONFIG_FIELDS:
        raise ValueError(
            "leaf-adjoint evaluation audit fields differ from ADR-0087: "
            f"missing={sorted(_CONFIG_FIELDS - set(config))!r}, "
            f"unknown={sorted(set(config) - _CONFIG_FIELDS)!r}"
        )
    frozen = {
        "evidence_stage": (
            "preregistered_after_h4_dense_bridge_before_any_h7_or_h32_"
            "leaf_adjoint_best_response_result"
        ),
        "seed": 20260820,
        "axis_seed": 20260819,
        "board": ["2c", "7d", "9h", "Js", "Qc"],
        "pot": 12.0,
        "stack": 30.0,
        "bet_size": 3.0,
        "players": 6,
        "small_hands_per_player": [4, 7],
        "small_policy_kinds": ["uniform", "checkpoint16_average"],
        "small_source_checkpoint": 16,
        "wide_hands_per_player": 32,
        "range_families": ["balanced", "blocker_heavy"],
        "validation_family": "blocker_heavy",
        "wide_policy_kinds": [
            "uniform",
            "current_step1",
            "current_step2",
            "average_step2",
        ],
        "mixture_components": 3,
        "split_index": 3,
        "query_chunk_records": 256,
        "maximum_feature_width_per_batch": 384,
        "cpu_crosscheck_target": 0,
        "required_numpy_version": "2.5.2",
        "required_scipy_version": "1.18.0",
        "required_cupy_version": "14.2.0",
        "required_cuda_runtime_version": 13020,
        "minimum_cuda_driver_version": 13000,
        "required_compute_capability": "120",
        "cuda_dll_environment_variable": "PONTIUS_CUDA_DLL_DIRECTORY",
    }
    if any(config[field] != value for field, value in frozen.items()):
        raise ValueError("leaf-adjoint evaluation workload differs from ADR-0087")
    for field, path in _SOURCE_PATHS.items():
        if config[field] != _sha256(path):
            raise ValueError(f"frozen source hash mismatch for {field}")
    expected_gates = {
        "expected_small_rows": 8,
        "maximum_small_utility_error": 1e-10,
        "maximum_small_best_response_error": 1e-10,
        "maximum_small_deviation_gain_error": 1e-10,
        "maximum_small_nash_conv_error": 1e-10,
        "maximum_small_selected_response_value_error": 1e-10,
        "maximum_small_zero_sum_residual": 1e-10,
        "expected_wide_rows": 2,
        "expected_wide_profiles_per_family": 4,
        "maximum_wide_cpu_gpu_profile_utility_error": 1e-9,
        "maximum_wide_cpu_gpu_best_response_error": 1e-9,
        "maximum_wide_cpu_gpu_deviation_gain_error": 1e-9,
        "maximum_wide_zero_sum_residual": 1e-9,
        "minimum_validation_charged_gpu_speedup": 3.0,
        "minimum_all_charged_gpu_speedup": 3.0,
        "maximum_wide_profile_evaluation_ms": 60_000.0,
        "maximum_wide_host_peak_numeric_bytes": 3_000_000_000,
        "maximum_wide_gpu_pool_bytes": 4_000_000_000,
        "expected_wide_information_sets": 6_144,
        "expected_wide_response_actions_per_seat": 1_024,
        "minimum_average2_normalized_nash_conv_improvement": 1e-6,
        "require_finite_wide_evaluations": True,
    }
    gates = config["gates"]
    if (
        not isinstance(gates, dict)
        or set(gates) != _GATE_FIELDS
        or gates != expected_gates
    ):
        raise ValueError("leaf-adjoint evaluation gates differ from ADR-0087")
    return {
        **config,
        "small_hands_per_player": tuple(config["small_hands_per_player"]),
        "small_policy_kinds": tuple(config["small_policy_kinds"]),
        "range_families": tuple(config["range_families"]),
        "wide_policy_kinds": tuple(config["wide_policy_kinds"]),
        "gates": dict(gates),
    }


def _small_source_policy(
    source: dict[str, Any],
    *,
    hand_count: int,
    family: str,
    checkpoint: int,
) -> tuple[dict[str, Any], dict[str, dict[str, float]]]:
    geometry = next(
        row
        for row in source["geometries"]
        if int(row["hands_per_player"]) == hand_count
        and row["range_family"] == family
    )
    profile = next(
        row
        for row in geometry["profiles"]
        if row["provenance"]["kind"] == "dcfr_average"
        and int(row["provenance"]["checkpoint"]) == checkpoint
    )
    return geometry, _policy_from_json(profile["policy"])


def _small_case(
    *,
    parsed: dict[str, Any],
    source: dict[str, Any],
    board: tuple[int, ...],
    hand_count: int,
    family: str,
    policy_kind: str,
) -> dict[str, object]:
    belief = _canonical_belief(
        board=board,
        hand_count=hand_count,
        family=family,
        components=parsed["mixture_components"],
        seed=parsed["axis_seed"],
    )
    source_geometry, checkpoint_policy = _small_source_policy(
        source,
        hand_count=hand_count,
        family=family,
        checkpoint=parsed["small_source_checkpoint"],
    )
    axes = [
        [[format_card(hand[0]), format_card(hand[1])] for hand in hands]
        for hands in belief.hands_by_player
    ]
    if axes != source_geometry["hand_axes"]:
        raise ValueError("small evaluation axes differ from source artifact")
    policy = {} if policy_kind == "uniform" else checkpoint_policy
    game = _game_from_belief(
        belief=belief,
        pot=parsed["pot"],
        stack=parsed["stack"],
        bet_size=parsed["bet_size"],
    )
    dense = PublicTreeTensorEvaluator(game)
    topology = representative_public_tree(
        belief,
        pot=parsed["pot"],
        stack=parsed["stack"],
        bet_size=parsed["bet_size"],
    )
    workspace, _ = _open_workspace(
        belief,
        split_index=parsed["split_index"],
        query_chunk_records=parsed["query_chunk_records"],
    )
    sparse = SparseBidirectionalIncidence.compile(workspace)
    codes = tuple(
        np.ascontiguousarray(values, dtype=np.int32)
        for values in _rank_codes(board, belief.hands_by_player)
    )
    automata = build_leaf_adjoint_terminal_automata(
        topology,
        codes,
        pot=parsed["pot"],
        bet_size=parsed["bet_size"],
    )
    expected = dense.evaluate(policy)
    actual = evaluate_leaf_adjoint_profile(
        topology,
        workspace,
        sparse,
        policy,
        automata,
        hands_by_player=belief.hands_by_player,
        maximum_feature_width_per_batch=parsed["maximum_feature_width_per_batch"],
    )
    utility_error = max(
        abs(first - second)
        for first, second in zip(
            actual.evaluation.utilities,
            expected.evaluation.utilities,
            strict=True,
        )
    )
    response_error = max(
        abs(first - second)
        for first, second in zip(
            actual.evaluation.best_response_values,
            expected.evaluation.best_response_values,
            strict=True,
        )
    )
    gain_error = max(
        abs(first - second)
        for first, second in zip(
            actual.evaluation.deviation_gains,
            expected.evaluation.deviation_gains,
            strict=True,
        )
    )
    schema = dense.information_schema()
    selected_value_error = 0.0
    action_mismatches = 0
    for target, selected in enumerate(actual.best_response_actions):
        candidate = {key: dict(values) for key, values in policy.items()}
        for key, action in selected.items():
            candidate[key] = {
                legal: float(legal == action) for legal in schema[key]
            }
        selected_value = dense._expected_utilities(
            dense._prepare_policy(candidate)
        )[target]
        selected_value_error = max(
            selected_value_error,
            abs(selected_value - expected.evaluation.best_response_values[target]),
        )
        action_mismatches += sum(
            action != expected.best_response_actions[target][key]
            for key, action in selected.items()
        )
    return {
        "hands_per_player": hand_count,
        "range_family": family,
        "policy_kind": policy_kind,
        "deals": dense.deal_count,
        "policy_sha256": policy_digest(policy),
        "utility_error": utility_error,
        "best_response_error": response_error,
        "deviation_gain_error": gain_error,
        "nash_conv_error": abs(
            actual.evaluation.nash_conv - expected.evaluation.nash_conv
        ),
        "selected_response_value_error": selected_value_error,
        "raw_action_mismatches": action_mismatches,
        "zero_sum_residual": actual.zero_sum_residual,
        "leaf_nash_conv": actual.evaluation.nash_conv,
        "dense_nash_conv": expected.evaluation.nash_conv,
        "leaf_wall_ms": actual.wall_ms,
        "terminal_contraction_ms": sum(
            row.terminal_contraction_ms for row in actual.seats
        ),
        "exact_action_ties": sum(row.exact_action_ties for row in actual.seats),
        "minimum_action_gap": min(row.minimum_action_gap for row in actual.seats),
    }


def _small_gate_results(
    rows: list[dict[str, object]], gates: dict[str, Any]
) -> dict[str, bool]:
    return {
        "small_row_count": len(rows) == gates["expected_small_rows"],
        "small_utility_identity": max(float(row["utility_error"]) for row in rows)
        <= gates["maximum_small_utility_error"],
        "small_best_response_identity": max(
            float(row["best_response_error"]) for row in rows
        )
        <= gates["maximum_small_best_response_error"],
        "small_deviation_gain_identity": max(
            float(row["deviation_gain_error"]) for row in rows
        )
        <= gates["maximum_small_deviation_gain_error"],
        "small_nash_conv_identity": max(
            float(row["nash_conv_error"]) for row in rows
        )
        <= gates["maximum_small_nash_conv_error"],
        "small_selected_response_value": max(
            float(row["selected_response_value_error"]) for row in rows
        )
        <= gates["maximum_small_selected_response_value_error"],
        "small_zero_sum": max(float(row["zero_sum_residual"]) for row in rows)
        <= gates["maximum_small_zero_sum_residual"],
    }


def _wide_source_policies(
    row: dict[str, Any],
) -> tuple[tuple[str, dict[str, dict[str, float]], str], ...]:
    checkpoints = {int(value["iteration"]): value for value in row["checkpoints"]}
    first = checkpoints[1]
    second = checkpoints[2]
    entries = (
        ("uniform", first["average_policy"], first["average_policy_sha256"]),
        ("current_step1", first["current_policy"], first["current_policy_sha256"]),
        ("current_step2", second["current_policy"], second["current_policy_sha256"]),
        ("average_step2", second["average_policy"], second["average_policy_sha256"]),
    )
    result = []
    for kind, raw, expected_digest in entries:
        policy = _policy_from_json(raw)
        if policy_digest(policy) != expected_digest:
            raise ValueError(f"wide source policy digest differs for {kind}")
        result.append((kind, policy, expected_digest))
    if any(
        abs(probability - 0.5) > 0.0
        for distribution in result[0][1].values()
        for probability in distribution.values()
    ):
        raise ValueError("wide source first average is not exact uniform")
    return tuple(result)


def _evaluation_is_finite(result: LeafAdjointProfileEvaluation) -> bool:
    values = (
        *result.evaluation.utilities,
        *result.evaluation.best_response_values,
        *result.evaluation.deviation_gains,
        result.evaluation.nash_conv,
        result.zero_sum_residual,
    )
    return all(math.isfinite(value) for value in values) and all(
        gain >= 0.0 for gain in result.evaluation.deviation_gains
    )


def _wide_profile_row(
    *,
    kind: str,
    digest: str,
    result: LeafAdjointProfileEvaluation,
    payoff_span: float,
    terminal_automaton_bytes: int,
) -> dict[str, object]:
    maximum_contraction_peak = max(
        row.maximum_terminal_peak_numeric_bytes for row in result.seats
    )
    return {
        "policy_kind": kind,
        "policy_sha256": digest,
        "utilities": result.evaluation.utilities,
        "best_response_values": result.evaluation.best_response_values,
        "deviation_gains": result.evaluation.deviation_gains,
        "nash_conv": result.evaluation.nash_conv,
        "normalized_nash_conv": result.evaluation.nash_conv / payoff_span,
        "zero_sum_residual": result.zero_sum_residual,
        "wall_ms": result.wall_ms,
        "terminal_contraction_ms": sum(
            row.terminal_contraction_ms for row in result.seats
        ),
        "reverse_evaluation_ms": sum(
            row.reverse_evaluation_ms for row in result.seats
        ),
        "terminal_contractions": sum(
            row.terminal_contractions for row in result.seats
        ),
        "terminal_sparse_batches": sum(
            row.terminal_sparse_batches for row in result.seats
        ),
        "response_actions_per_seat": tuple(
            len(row.best_response_actions) for row in result.seats
        ),
        "exact_action_ties": sum(row.exact_action_ties for row in result.seats),
        "minimum_action_gap": min(row.minimum_action_gap for row in result.seats),
        "maximum_host_peak_numeric_bytes": (
            maximum_contraction_peak + terminal_automaton_bytes
        ),
        "maximum_gpu_pool_bytes": max(
            row.maximum_gpu_pool_total_bytes for row in result.seats
        ),
        "finite": _evaluation_is_finite(result),
    }


def _wide_case(
    *,
    parsed: dict[str, Any],
    source: dict[str, Any],
    board: tuple[int, ...],
    family: str,
) -> dict[str, object]:
    source_row = next(
        row for row in source["wide_rows"] if row["range_family"] == family
    )
    policies = _wide_source_policies(source_row)
    if tuple(kind for kind, _, _ in policies) != parsed["wide_policy_kinds"]:
        raise ValueError("wide source policy kinds differ from ADR-0087")
    belief = _canonical_belief(
        board=board,
        hand_count=parsed["wide_hands_per_player"],
        family=family,
        components=parsed["mixture_components"],
        seed=parsed["axis_seed"],
    )
    topology = representative_public_tree(
        belief,
        pot=parsed["pot"],
        stack=parsed["stack"],
        bet_size=parsed["bet_size"],
    )
    schema = AxisPublicCFRState(
        topology,
        belief.hands_by_player,
    ).information_schema()
    for kind, policy, _ in policies:
        if set(policy) != set(schema) or any(
            set(policy[key]) != set(actions) for key, actions in schema.items()
        ):
            raise ValueError(f"wide source policy schema differs for {kind}")
    workspace, workspace_timing = _open_workspace(
        belief,
        split_index=parsed["split_index"],
        query_chunk_records=parsed["query_chunk_records"],
    )
    sparse = SparseBidirectionalIncidence.compile(workspace)
    gpu = CuPyBidirectionalIncidence.compile(sparse)
    codes = tuple(
        np.ascontiguousarray(values, dtype=np.int32)
        for values in _rank_codes(board, belief.hands_by_player)
    )
    automata = build_leaf_adjoint_terminal_automata(
        topology,
        codes,
        pot=parsed["pot"],
        bet_size=parsed["bet_size"],
    )
    unique_automata = {
        id(automaton): automaton
        for library in automata
        for automaton in library.values()
    }
    automaton_bytes = sum(value.numeric_bytes for value in unique_automata.values())
    payoff_span = float(topology.game.payoff_span)

    profile_rows = []
    profile_results: dict[str, LeafAdjointProfileEvaluation] = {}
    for kind, policy, digest in policies:
        result = evaluate_leaf_adjoint_profile(
            topology,
            workspace,
            sparse,
            policy,
            automata,
            hands_by_player=belief.hands_by_player,
            maximum_feature_width_per_batch=parsed[
                "maximum_feature_width_per_batch"
            ],
            cupy_sparse=gpu,
        )
        profile_results[kind] = result
        profile_rows.append(
            _wide_profile_row(
                kind=kind,
                digest=digest,
                result=result,
                payoff_span=payoff_span,
                terminal_automaton_bytes=automaton_bytes,
            )
        )

    average_policy = next(
        policy for kind, policy, _ in policies if kind == "average_step2"
    )
    probabilities = compile_policy_probability_tape(
        topology,
        belief.hands_by_player,
        average_policy,
    )
    target = parsed["cpu_crosscheck_target"]
    cpu = evaluate_leaf_adjoint_seat(
        topology,
        workspace,
        sparse,
        probabilities,
        automata[target],
        target_player=target,
        hands_by_player=belief.hands_by_player,
        maximum_feature_width_per_batch=parsed["maximum_feature_width_per_batch"],
    )
    gpu_seat = profile_results["average_step2"].seats[target]
    action_mismatches = sum(
        action != gpu_seat.best_response_actions[key]
        for key, action in cpu.best_response_actions.items()
    )
    crosscheck = {
        "target_player": target,
        "cpu_ms": cpu.wall_ms,
        "gpu_ms": gpu_seat.wall_ms,
        "gpu_operator_upload_ms": gpu.upload_ms,
        "raw_gpu_speedup": cpu.wall_ms / gpu_seat.wall_ms,
        "charged_gpu_speedup": cpu.wall_ms / (gpu_seat.wall_ms + gpu.upload_ms),
        "profile_utility_error": abs(
            cpu.profile_utility - gpu_seat.profile_utility
        ),
        "best_response_error": abs(
            cpu.best_response_value - gpu_seat.best_response_value
        ),
        "deviation_gain_error": abs(cpu.deviation_gain - gpu_seat.deviation_gain),
        "raw_action_mismatches": action_mismatches,
        "cpu_exact_action_ties": cpu.exact_action_ties,
        "gpu_exact_action_ties": gpu_seat.exact_action_ties,
        "cpu_minimum_action_gap": cpu.minimum_action_gap,
        "gpu_minimum_action_gap": gpu_seat.minimum_action_gap,
    }
    by_kind = {row["policy_kind"]: row for row in profile_rows}
    normalized_improvement = float(by_kind["uniform"]["normalized_nash_conv"]) - float(
        by_kind["average_step2"]["normalized_nash_conv"]
    )
    return {
        "hands_per_player": parsed["wide_hands_per_player"],
        "range_family": family,
        "information_sets": len(schema),
        "payoff_span": payoff_span,
        "workspace_timing": workspace_timing,
        "sparse_operator_numeric_bytes": sparse.numeric_bytes,
        "terminal_automaton_numeric_bytes": automaton_bytes,
        "profiles": profile_rows,
        "average2_normalized_nash_conv_improvement": normalized_improvement,
        "cpu_gpu_average2_crosscheck": crosscheck,
        "gpu": {
            "cupy_version": gpu.cupy_version,
            "cuda_runtime_version": gpu.cuda_runtime_version,
            "cuda_driver_version": gpu.cuda_driver_version,
            "compute_capability": gpu.compute_capability,
        },
    }


def run_leaf_adjoint_evaluation_audit(
    config: dict[str, Any],
) -> dict[str, object]:
    parsed = parse_leaf_adjoint_evaluation_audit_config(config)
    import scipy

    cupy_started = time.perf_counter()
    cp, _ = _cupy_modules()
    cupy_import_ms = (time.perf_counter() - cupy_started) * 1000.0
    if np.__version__ != parsed["required_numpy_version"]:
        raise ValueError("NumPy version differs from ADR-0087")
    if scipy.__version__ != parsed["required_scipy_version"]:
        raise ValueError("SciPy version differs from ADR-0087")
    if cp.__version__ != parsed["required_cupy_version"]:
        raise ValueError("CuPy version differs from ADR-0087")
    if cp.cuda.runtime.runtimeGetVersion() != parsed["required_cuda_runtime_version"]:
        raise ValueError("CUDA runtime differs from ADR-0087")
    if cp.cuda.runtime.driverGetVersion() < parsed["minimum_cuda_driver_version"]:
        raise ValueError("CUDA driver is older than the ADR-0087 floor")
    if str(cp.cuda.Device(0).compute_capability) != parsed["required_compute_capability"]:
        raise ValueError("GPU compute capability differs from ADR-0087")
    if not os.environ.get(parsed["cuda_dll_environment_variable"]):
        raise ValueError("optional CUDA DLL directory is not configured")

    started = time.perf_counter()
    board = parse_cards(*parsed["board"])
    small_source = json.loads(_SMALL_SOURCE.read_text(encoding="utf-8"))
    small_rows = [
        _small_case(
            parsed=parsed,
            source=small_source,
            board=board,
            hand_count=hand_count,
            family=family,
            policy_kind=policy_kind,
        )
        for hand_count in parsed["small_hands_per_player"]
        for family in parsed["range_families"]
        for policy_kind in parsed["small_policy_kinds"]
    ]
    gates = parsed["gates"]
    gate_results = _small_gate_results(small_rows, gates)
    if not all(gate_results.values()):
        gate_results["passed"] = False
        return _result(
            parsed=parsed,
            small_rows=small_rows,
            wide_rows=[],
            aggregate={"wide_skipped_after_small_rejection": True},
            gate_results=gate_results,
            started=started,
            cupy_import_ms=cupy_import_ms,
            cp=cp,
            scipy=scipy,
            status="small_bridge_rejected_before_wide_execution",
        )

    wide_source = json.loads(_WIDE_SOURCE.read_text(encoding="utf-8"))
    wide_rows = []
    for family in parsed["range_families"]:
        release_cupy_memory_pool()
        wide_rows.append(
            _wide_case(parsed=parsed, source=wide_source, board=board, family=family)
        )

    profile_rows = [profile for row in wide_rows for profile in row["profiles"]]
    crosschecks = [row["cpu_gpu_average2_crosscheck"] for row in wide_rows]
    aggregate = {
        "maximum_small_utility_error": max(
            float(row["utility_error"]) for row in small_rows
        ),
        "maximum_small_best_response_error": max(
            float(row["best_response_error"]) for row in small_rows
        ),
        "maximum_small_deviation_gain_error": max(
            float(row["deviation_gain_error"]) for row in small_rows
        ),
        "maximum_small_nash_conv_error": max(
            float(row["nash_conv_error"]) for row in small_rows
        ),
        "maximum_small_selected_response_value_error": max(
            float(row["selected_response_value_error"]) for row in small_rows
        ),
        "maximum_small_zero_sum_residual": max(
            float(row["zero_sum_residual"]) for row in small_rows
        ),
        "small_raw_action_mismatches": sum(
            int(row["raw_action_mismatches"]) for row in small_rows
        ),
        "maximum_wide_cpu_gpu_profile_utility_error": max(
            float(row["profile_utility_error"]) for row in crosschecks
        ),
        "maximum_wide_cpu_gpu_best_response_error": max(
            float(row["best_response_error"]) for row in crosschecks
        ),
        "maximum_wide_cpu_gpu_deviation_gain_error": max(
            float(row["deviation_gain_error"]) for row in crosschecks
        ),
        "minimum_charged_gpu_speedup": min(
            float(row["charged_gpu_speedup"]) for row in crosschecks
        ),
        "validation_charged_gpu_speedup": next(
            float(row["cpu_gpu_average2_crosscheck"]["charged_gpu_speedup"])
            for row in wide_rows
            if row["range_family"] == parsed["validation_family"]
        ),
        "maximum_wide_zero_sum_residual": max(
            float(row["zero_sum_residual"]) for row in profile_rows
        ),
        "maximum_wide_profile_evaluation_ms": max(
            float(row["wall_ms"]) for row in profile_rows
        ),
        "maximum_wide_host_peak_numeric_bytes": max(
            int(row["maximum_host_peak_numeric_bytes"]) for row in profile_rows
        ),
        "maximum_wide_gpu_pool_bytes": max(
            int(row["maximum_gpu_pool_bytes"]) for row in profile_rows
        ),
        "minimum_average2_normalized_nash_conv_improvement": min(
            float(row["average2_normalized_nash_conv_improvement"])
            for row in wide_rows
        ),
    }
    gate_results.update(
        {
            "wide_row_count": len(wide_rows) == gates["expected_wide_rows"],
            "wide_profile_count": all(
                len(row["profiles"]) == gates["expected_wide_profiles_per_family"]
                for row in wide_rows
            ),
            "wide_profile_utility_identity": aggregate[
                "maximum_wide_cpu_gpu_profile_utility_error"
            ]
            <= gates["maximum_wide_cpu_gpu_profile_utility_error"],
            "wide_best_response_identity": aggregate[
                "maximum_wide_cpu_gpu_best_response_error"
            ]
            <= gates["maximum_wide_cpu_gpu_best_response_error"],
            "wide_deviation_gain_identity": aggregate[
                "maximum_wide_cpu_gpu_deviation_gain_error"
            ]
            <= gates["maximum_wide_cpu_gpu_deviation_gain_error"],
            "wide_zero_sum": aggregate["maximum_wide_zero_sum_residual"]
            <= gates["maximum_wide_zero_sum_residual"],
            "validation_gpu_speedup": aggregate["validation_charged_gpu_speedup"]
            >= gates["minimum_validation_charged_gpu_speedup"],
            "all_gpu_speedup": aggregate["minimum_charged_gpu_speedup"]
            >= gates["minimum_all_charged_gpu_speedup"],
            "wide_latency": aggregate["maximum_wide_profile_evaluation_ms"]
            <= gates["maximum_wide_profile_evaluation_ms"],
            "wide_host_peak": aggregate["maximum_wide_host_peak_numeric_bytes"]
            <= gates["maximum_wide_host_peak_numeric_bytes"],
            "wide_gpu_peak": aggregate["maximum_wide_gpu_pool_bytes"]
            <= gates["maximum_wide_gpu_pool_bytes"],
            "wide_schema": all(
                int(row["information_sets"])
                == gates["expected_wide_information_sets"]
                and all(
                    all(
                        int(count)
                        == gates["expected_wide_response_actions_per_seat"]
                        for count in profile["response_actions_per_seat"]
                    )
                    for profile in row["profiles"]
                )
                for row in wide_rows
            ),
            "wide_finite": all(bool(row["finite"]) for row in profile_rows)
            == gates["require_finite_wide_evaluations"],
            "average2_strategy_improves": aggregate[
                "minimum_average2_normalized_nash_conv_improvement"
            ]
            >= gates["minimum_average2_normalized_nash_conv_improvement"],
        }
    )
    gate_results["passed"] = all(gate_results.values())
    return _result(
        parsed=parsed,
        small_rows=small_rows,
        wide_rows=wide_rows,
        aggregate=aggregate,
        gate_results=gate_results,
        started=started,
        cupy_import_ms=cupy_import_ms,
        cp=cp,
        scipy=scipy,
        status="frozen_audit_executed",
    )


def _result(
    *,
    parsed: dict[str, Any],
    small_rows: list[dict[str, object]],
    wide_rows: list[dict[str, object]],
    aggregate: dict[str, object],
    gate_results: dict[str, bool],
    started: float,
    cupy_import_ms: float,
    cp: Any,
    scipy: Any,
    status: str,
) -> dict[str, object]:
    properties = cp.cuda.runtime.getDeviceProperties(0)
    name = properties["name"]
    if isinstance(name, bytes):
        name = name.decode("utf-8")
    return {
        "schema_version": 1,
        "experiment_type": "leaf_adjoint_dense_free_best_response_quality_audit",
        "status": status,
        "config": parsed,
        "config_sha256": _sha256(_CONFIG),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "small_source_sha256": _sha256(_SMALL_SOURCE),
        "wide_source_sha256": _sha256(_WIDE_SOURCE),
        "small_rows": small_rows,
        "wide_rows": wide_rows,
        "aggregate": aggregate,
        "gates": gate_results,
        "counts": {"small_rows": len(small_rows), "wide_rows": len(wide_rows)},
        "timing": {
            "wall_seconds": time.perf_counter() - started,
            "cupy_import_ms": cupy_import_ms,
        },
        "environment": {
            **environment_metadata(),
            "numpy_version": np.__version__,
            "scipy_version": scipy.__version__,
            "cupy_version": cp.__version__,
            "cuda_runtime_version": cp.cuda.runtime.runtimeGetVersion(),
            "cuda_driver_version": cp.cuda.runtime.driverGetVersion(),
            "gpu_name": str(name),
            "compute_capability": str(cp.cuda.Device(0).compute_capability),
        },
        "limitations": [
            "NashConv is exact unilateral reduced-game telemetry, not two-player exploitability or coalition safety.",
            "The wide policies contain only two cold DCFR iterations and carry no equilibrium-quality claim.",
            "The evaluator uses the equal-stack one-bet river abstraction, not full six-max no-limit hold'em.",
            "CPU/GPU response actions may differ inside floating tie envelopes; response value, not raw argmax identity, is gated.",
            "The embedded ADR-0085 policies are evaluable but do not contain restartable regret and average accumulators.",
        ],
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    result = run_leaf_adjoint_evaluation_audit(config)
    rendered = json.dumps(result, indent=2, sort_keys=True, allow_nan=False)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered + "\n", encoding="utf-8")
    improvement = result.get("aggregate", {}).get(
        "minimum_average2_normalized_nash_conv_improvement"
    )
    improvement_text = "unmeasured" if improvement is None else f"{improvement:.6g}"
    print(
        "leaf-adjoint evaluation audit: "
        f"small={result['counts']['small_rows']}, "
        f"wide={result['counts']['wide_rows']}, "
        f"min_average2_improvement={improvement_text}, "
        f"passed={result['gates']['passed']}, "
        f"wall={result['timing']['wall_seconds']:.3f}s"
    )
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
