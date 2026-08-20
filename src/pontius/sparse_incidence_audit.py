"""Run the frozen CSR open-mode incidence backend screen."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from statistics import median
import time
from typing import Any

import numpy as np

from .open_mode_audit import _canonical_belief, _open_workspace
from .open_mode_showdown import (
    OpenModeShowdownBatchContraction,
    contract_open_mode_showdown_batch,
)
from .reporting import environment_metadata
from .river import parse_cards
from .showdown_value_rank_screen import _rank_codes
from .sparse_incidence_open_mode import (
    SparseBidirectionalIncidence,
    SparseOpenModeShowdownContraction,
    contract_sparse_open_mode_showdown_batch,
)
from .structured_showdown_automaton import build_structured_showdown_automaton

_ROOT = Path(__file__).parents[2]
_CONFIG = _ROOT / "experiments" / "configs" / "sparse-incidence-open-mode-audit-v1.json"
_IMPLEMENTATION = Path(__file__)
_CONFIG_FIELDS = {
    "evidence_stage",
    "seed",
    "axis_seed",
    "expected_pyproject_sha256",
    "expected_open_mode_audit_sha256",
    "expected_open_mode_factor_tt_sha256",
    "expected_open_mode_showdown_sha256",
    "expected_sparse_backend_sha256",
    "expected_audit_implementation_sha256",
    "board",
    "pot",
    "bet_size",
    "players",
    "hands_per_player",
    "range_families",
    "validation_speed_family",
    "mixture_components",
    "split_index",
    "query_chunk_records",
    "maximum_feature_width_per_batch",
    "timing_warmups",
    "timing_repeats",
    "timing_order",
    "weighted_reach_rule",
    "required_numpy_version",
    "required_scipy_version",
    "gates",
}
_GATE_FIELDS = {
    "maximum_reach_error",
    "maximum_numerator_error",
    "maximum_conditional_error",
    "maximum_weighted_reach_error",
    "maximum_weighted_numerator_error",
    "maximum_weighted_conditional_error",
    "maximum_action_identity_mismatches",
    "maximum_zero_sum_error",
    "expected_rows",
    "minimum_validation_h32_speedup",
    "minimum_all_h32_speedup",
    "maximum_h32_sparse_median_ms",
    "maximum_h32_sparse_peak_numeric_bytes",
    "maximum_h32_sparse_operator_numeric_bytes",
    "require_charged_first_use_faster_at_h32",
    "require_exact_source_nnz",
    "require_finite_sparse_outputs",
}
_SOURCE_PATHS = {
    "expected_pyproject_sha256": _ROOT / "pyproject.toml",
    "expected_open_mode_audit_sha256": _ROOT / "src" / "pontius" / "open_mode_audit.py",
    "expected_open_mode_factor_tt_sha256": _ROOT / "src" / "pontius" / "open_mode_factor_tt.py",
    "expected_open_mode_showdown_sha256": _ROOT / "src" / "pontius" / "open_mode_showdown.py",
    "expected_sparse_backend_sha256": _ROOT / "src" / "pontius" / "sparse_incidence_open_mode.py",
    "expected_audit_implementation_sha256": _IMPLEMENTATION,
}


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required frozen input is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_sparse_incidence_audit_config(config: dict[str, Any]) -> dict[str, Any]:
    if set(config) != _CONFIG_FIELDS:
        raise ValueError(
            "sparse-incidence audit fields differ from ADR-0083: "
            f"missing={sorted(_CONFIG_FIELDS - set(config))!r}, "
            f"unknown={sorted(set(config) - _CONFIG_FIELDS)!r}"
        )
    frozen = {
        "evidence_stage": (
            "preregistered_after_balanced_h32_csr_development_before_"
            "blocker_h32_validation"
        ),
        "seed": 20260820,
        "axis_seed": 20260819,
        "board": ["2c", "7d", "9h", "Js", "Qc"],
        "pot": 12.0,
        "bet_size": 3.0,
        "players": 6,
        "hands_per_player": [7, 16, 32],
        "range_families": ["balanced", "blocker_heavy"],
        "validation_speed_family": "blocker_heavy",
        "mixture_components": 3,
        "split_index": 3,
        "query_chunk_records": 256,
        "maximum_feature_width_per_batch": 96,
        "timing_warmups": 1,
        "timing_repeats": 3,
        "timing_order": "alternating_sparse_first_then_numpy_first",
        "weighted_reach_rule": "sha256_positive_1_to_31_over_31_per_seat_hand",
        "required_numpy_version": "2.5.2",
        "required_scipy_version": "1.18.0",
    }
    if any(config[field] != value for field, value in frozen.items()):
        raise ValueError("sparse-incidence execution contract differs from ADR-0083")
    for field, path in _SOURCE_PATHS.items():
        if config[field] != _sha256(path):
            raise ValueError(f"frozen source hash mismatch for {field}")
    gates = config["gates"]
    if not isinstance(gates, dict) or set(gates) != _GATE_FIELDS:
        raise ValueError("sparse-incidence gates differ from ADR-0083")
    expected_gates = {
        "maximum_reach_error": 1e-10,
        "maximum_numerator_error": 1e-10,
        "maximum_conditional_error": 1e-10,
        "maximum_weighted_reach_error": 1e-10,
        "maximum_weighted_numerator_error": 1e-10,
        "maximum_weighted_conditional_error": 1e-10,
        "maximum_action_identity_mismatches": 0,
        "maximum_zero_sum_error": 1e-9,
        "expected_rows": 6,
        "minimum_validation_h32_speedup": 5.0,
        "minimum_all_h32_speedup": 5.0,
        "maximum_h32_sparse_median_ms": 4000.0,
        "maximum_h32_sparse_peak_numeric_bytes": 600_000_000,
        "maximum_h32_sparse_operator_numeric_bytes": 100_000_000,
        "require_charged_first_use_faster_at_h32": True,
        "require_exact_source_nnz": True,
        "require_finite_sparse_outputs": True,
    }
    if gates != expected_gates:
        raise ValueError("sparse-incidence gates differ from ADR-0083")
    return {
        **config,
        "hands_per_player": tuple(config["hands_per_player"]),
        "range_families": tuple(config["range_families"]),
        "gates": dict(gates),
    }


def _mode_factors(
    shape: tuple[int, ...],
    *,
    seed: int,
    hand_count: int,
    family: str,
) -> tuple[np.ndarray, ...]:
    result = []
    for seat, size in enumerate(shape):
        values = []
        for hand in range(size):
            payload = f"{seed}|weighted-reach|{hand_count}|{family}|{seat}|{hand}"
            score = int.from_bytes(
                hashlib.sha256(payload.encode("utf-8")).digest()[:8],
                "big",
            )
            values.append((1 + score % 31) / 31.0)
        result.append(np.ascontiguousarray(values, dtype=np.float64))
    return tuple(result)


def _timed_pair(
    numpy_function: Any,
    sparse_function: Any,
    *,
    warmups: int,
    repeats: int,
) -> tuple[
    list[float],
    list[float],
    tuple[OpenModeShowdownBatchContraction, OpenModeShowdownBatchContraction],
    tuple[SparseOpenModeShowdownContraction, SparseOpenModeShowdownContraction],
]:
    numpy_result = None
    sparse_result = None
    for _ in range(warmups):
        numpy_result = numpy_function()
        sparse_result = sparse_function()
    numpy_times = []
    sparse_times = []
    for repeat in range(repeats):
        ordered = (
            (("sparse", sparse_function), ("numpy", numpy_function))
            if repeat % 2 == 0
            else (("numpy", numpy_function), ("sparse", sparse_function))
        )
        for label, function in ordered:
            started = time.perf_counter()
            result = function()
            elapsed = (time.perf_counter() - started) * 1000.0
            if label == "numpy":
                numpy_times.append(elapsed)
                numpy_result = result
            else:
                sparse_times.append(elapsed)
                sparse_result = result
    if numpy_result is None or sparse_result is None:
        raise AssertionError("paired timing produced no result")
    return numpy_times, sparse_times, numpy_result, sparse_result


def _own_values(
    left: Any,
    right: Any,
) -> tuple[Any, ...]:
    return tuple(left.for_automaton(index).for_seat(index) for index in range(3)) + tuple(
        right.for_automaton(index).for_seat(index + 3) for index in range(3)
    )


def _maximum_errors(
    numpy_values: tuple[Any, ...],
    sparse_values: tuple[Any, ...],
) -> dict[str, float]:
    return {
        "reach": max(
            float(
                np.max(
                    np.abs(first.root_normalized_reaches - second.root_normalized_reaches)
                )
            )
            for first, second in zip(numpy_values, sparse_values, strict=True)
        ),
        "numerator": max(
            float(
                np.max(
                    np.abs(
                        first.root_normalized_numerators
                        - second.root_normalized_numerators
                    )
                )
            )
            for first, second in zip(numpy_values, sparse_values, strict=True)
        ),
        "conditional": max(
            float(np.max(np.abs(first.conditional_values - second.conditional_values)))
            for first, second in zip(numpy_values, sparse_values, strict=True)
        ),
    }


def _case(
    *,
    parsed: dict[str, Any],
    board: tuple[int, ...],
    hand_count: int,
    family: str,
    scipy_import_ms: float,
) -> dict[str, object]:
    belief = _canonical_belief(
        board=board,
        hand_count=hand_count,
        family=family,
        components=parsed["mixture_components"],
        seed=parsed["axis_seed"],
    )
    workspace, workspace_timing = _open_workspace(
        belief,
        split_index=parsed["split_index"],
        query_chunk_records=parsed["query_chunk_records"],
    )
    compile_started = time.perf_counter()
    sparse_topology = SparseBidirectionalIncidence.compile(workspace)
    sparse_compile_wall_ms = (time.perf_counter() - compile_started) * 1000.0
    codes = tuple(
        np.ascontiguousarray(values, dtype=np.int32)
        for values in _rank_codes(board, belief.hands_by_player)
    )
    automata = tuple(
        build_structured_showdown_automaton(
            strength_codes=codes,
            contenders=tuple(range(parsed["players"])),
            target_player=target,
            contributed=False,
            pot=parsed["pot"],
            bet_size=parsed["bet_size"],
        )
        for target in range(parsed["players"])
    )
    cap = parsed["maximum_feature_width_per_batch"]

    def numpy_evaluate() -> tuple[
        OpenModeShowdownBatchContraction,
        OpenModeShowdownBatchContraction,
    ]:
        return (
            contract_open_mode_showdown_batch(
                workspace,
                automata[:3],
                target_seats=(0, 1, 2),
                maximum_feature_width_per_batch=cap,
            ),
            contract_open_mode_showdown_batch(
                workspace,
                automata[3:],
                target_seats=(3, 4, 5),
                maximum_feature_width_per_batch=cap,
            ),
        )

    def sparse_evaluate() -> tuple[
        SparseOpenModeShowdownContraction,
        SparseOpenModeShowdownContraction,
    ]:
        return (
            contract_sparse_open_mode_showdown_batch(
                workspace,
                sparse_topology,
                automata[:3],
                target_seats=(0, 1, 2),
                maximum_feature_width_per_batch=cap,
            ),
            contract_sparse_open_mode_showdown_batch(
                workspace,
                sparse_topology,
                automata[3:],
                target_seats=(3, 4, 5),
                maximum_feature_width_per_batch=cap,
            ),
        )

    numpy_times, sparse_times, numpy_result, sparse_result = _timed_pair(
        numpy_evaluate,
        sparse_evaluate,
        warmups=parsed["timing_warmups"],
        repeats=parsed["timing_repeats"],
    )
    numpy_values = _own_values(*numpy_result)
    sparse_values = _own_values(*sparse_result)
    errors = _maximum_errors(numpy_values, sparse_values)
    numpy_zero_sum = abs(
        math.fsum(
            value.total_unnormalized_numerator / workspace.base.partition
            for value in numpy_values
        )
    )
    sparse_zero_sum = abs(
        math.fsum(
            value.total_unnormalized_numerator / workspace.base.partition
            for value in sparse_values
        )
    )
    shortcut_value = -parsed["pot"] / parsed["players"]
    numpy_actions = tuple(
        np.column_stack(
            (
                value.root_normalized_numerators,
                shortcut_value * value.root_normalized_reaches,
            )
        )
        for value in numpy_values
    )
    sparse_actions = tuple(
        np.column_stack(
            (
                value.root_normalized_numerators,
                shortcut_value * value.root_normalized_reaches,
            )
        )
        for value in sparse_values
    )
    action_mismatches = sum(
        int(
            np.count_nonzero(
                np.argmax(first, axis=1) != np.argmax(second, axis=1)
            )
        )
        for first, second in zip(numpy_actions, sparse_actions, strict=True)
    )

    factors = _mode_factors(
        belief.hand_counts,
        seed=parsed["seed"],
        hand_count=hand_count,
        family=family,
    )
    weighted_numpy = contract_open_mode_showdown_batch(
        workspace,
        (automata[0],),
        target_seats=(0,),
        mode_factors=factors,
        maximum_feature_width_per_batch=cap,
    ).for_automaton(0).for_seat(0)
    weighted_sparse = contract_sparse_open_mode_showdown_batch(
        workspace,
        sparse_topology,
        (automata[0],),
        target_seats=(0,),
        mode_factors=factors,
        maximum_feature_width_per_batch=cap,
    ).for_automaton(0).for_seat(0)
    weighted_errors = {
        "reach": float(
            np.max(
                np.abs(
                    weighted_numpy.root_normalized_reaches
                    - weighted_sparse.root_normalized_reaches
                )
            )
        ),
        "numerator": float(
            np.max(
                np.abs(
                    weighted_numpy.root_normalized_numerators
                    - weighted_sparse.root_normalized_numerators
                )
            )
        ),
        "conditional": float(
            np.max(
                np.abs(
                    weighted_numpy.conditional_values
                    - weighted_sparse.conditional_values
                )
            )
        ),
    }
    numpy_median = float(median(numpy_times))
    sparse_median = float(median(sparse_times))
    sparse_peak = max(
        result.estimated_peak_total_numeric_bytes for result in sparse_result
    )
    numpy_peak = max(
        result.estimated_peak_total_numeric_bytes for result in numpy_result
    )
    charged_sparse_first = (
        scipy_import_ms + sparse_compile_wall_ms + sparse_median
    )
    source_nnz_exact = all(
        direction.source_nnz
        == direction.source_records * direction.source_subset_count
        for direction in (
            sparse_topology.right_to_left,
            sparse_topology.left_to_right,
        )
    )
    finite = all(
        np.all(np.isfinite(value.conditional_values))
        and np.all(np.isfinite(value.root_normalized_numerators))
        and np.all(np.isfinite(value.root_normalized_reaches))
        for value in sparse_values
    )
    return {
        "hands_per_player": hand_count,
        "range_family": family,
        "middle_ranks": list(sparse_result[0].middle_ranks)
        + list(sparse_result[1].middle_ranks),
        "numpy_timings_ms": numpy_times,
        "sparse_timings_ms": sparse_times,
        "numpy_median_ms": numpy_median,
        "sparse_median_ms": sparse_median,
        "speedup": numpy_median / sparse_median,
        "sparse_compile_wall_ms": sparse_compile_wall_ms,
        "sparse_compile_internal_ms": sparse_topology.compile_ms,
        "scipy_import_ms_charged": scipy_import_ms,
        "charged_sparse_first_use_ms": charged_sparse_first,
        "charged_numpy_first_use_ms": numpy_median,
        "charged_first_use_sparse_is_faster": charged_sparse_first < numpy_median,
        "sparse_operator_numeric_bytes": sparse_topology.numeric_bytes,
        "sparse_peak_numeric_bytes": sparse_peak,
        "numpy_peak_numeric_bytes": numpy_peak,
        "sparse_to_numpy_peak_ratio": sparse_peak / numpy_peak,
        "maximum_reach_error": errors["reach"],
        "maximum_numerator_error": errors["numerator"],
        "maximum_conditional_error": errors["conditional"],
        "maximum_weighted_reach_error": weighted_errors["reach"],
        "maximum_weighted_numerator_error": weighted_errors["numerator"],
        "maximum_weighted_conditional_error": weighted_errors["conditional"],
        "action_identity_mismatches": action_mismatches,
        "numpy_zero_sum_error": numpy_zero_sum,
        "sparse_zero_sum_error": sparse_zero_sum,
        "source_nnz_exact": source_nnz_exact,
        "finite_sparse_outputs": finite,
        "forward_source_nnz": sparse_topology.right_to_left.source_nnz,
        "forward_query_nnz": sparse_topology.right_to_left.query_nnz,
        "reverse_source_nnz": sparse_topology.left_to_right.source_nnz,
        "reverse_query_nnz": sparse_topology.left_to_right.query_nnz,
        "sparse_direction_work": [
            {
                field: getattr(work, field)
                for field in work.__dataclass_fields__
            }
            for result in sparse_result
            for work in result.directions
        ],
        "workspace_timing": workspace_timing,
    }


def run_sparse_incidence_audit(config: dict[str, Any]) -> dict[str, object]:
    parsed = parse_sparse_incidence_audit_config(config)
    import_started = time.perf_counter()
    import scipy

    scipy_import_ms = (time.perf_counter() - import_started) * 1000.0
    if np.__version__ != parsed["required_numpy_version"]:
        raise ValueError("NumPy version differs from sparse-screen freeze")
    if scipy.__version__ != parsed["required_scipy_version"]:
        raise ValueError("SciPy version differs from sparse-screen freeze")
    board = parse_cards(*parsed["board"])
    started = time.perf_counter()
    rows = []
    for hand_count in parsed["hands_per_player"]:
        for family in parsed["range_families"]:
            rows.append(
                _case(
                    parsed=parsed,
                    board=board,
                    hand_count=hand_count,
                    family=family,
                    scipy_import_ms=scipy_import_ms,
                )
            )
    aggregate = {
        "maximum_reach_error": max(float(row["maximum_reach_error"]) for row in rows),
        "maximum_numerator_error": max(
            float(row["maximum_numerator_error"]) for row in rows
        ),
        "maximum_conditional_error": max(
            float(row["maximum_conditional_error"]) for row in rows
        ),
        "maximum_weighted_reach_error": max(
            float(row["maximum_weighted_reach_error"]) for row in rows
        ),
        "maximum_weighted_numerator_error": max(
            float(row["maximum_weighted_numerator_error"]) for row in rows
        ),
        "maximum_weighted_conditional_error": max(
            float(row["maximum_weighted_conditional_error"]) for row in rows
        ),
        "action_identity_mismatches": sum(
            int(row["action_identity_mismatches"]) for row in rows
        ),
        "maximum_zero_sum_error": max(
            max(float(row["numpy_zero_sum_error"]), float(row["sparse_zero_sum_error"]))
            for row in rows
        ),
        "minimum_h32_speedup": min(
            float(row["speedup"]) for row in rows if row["hands_per_player"] == 32
        ),
        "validation_h32_speedup": next(
            float(row["speedup"])
            for row in rows
            if row["hands_per_player"] == 32
            and row["range_family"] == parsed["validation_speed_family"]
        ),
        "maximum_h32_sparse_median_ms": max(
            float(row["sparse_median_ms"])
            for row in rows
            if row["hands_per_player"] == 32
        ),
        "maximum_h32_sparse_peak_numeric_bytes": max(
            int(row["sparse_peak_numeric_bytes"])
            for row in rows
            if row["hands_per_player"] == 32
        ),
        "maximum_h32_sparse_operator_numeric_bytes": max(
            int(row["sparse_operator_numeric_bytes"])
            for row in rows
            if row["hands_per_player"] == 32
        ),
    }
    gates = parsed["gates"]
    gate_results = {
        "reach_identity": aggregate["maximum_reach_error"]
        <= gates["maximum_reach_error"],
        "numerator_identity": aggregate["maximum_numerator_error"]
        <= gates["maximum_numerator_error"],
        "conditional_identity": aggregate["maximum_conditional_error"]
        <= gates["maximum_conditional_error"],
        "weighted_reach_identity": aggregate["maximum_weighted_reach_error"]
        <= gates["maximum_weighted_reach_error"],
        "weighted_numerator_identity": aggregate["maximum_weighted_numerator_error"]
        <= gates["maximum_weighted_numerator_error"],
        "weighted_conditional_identity": aggregate[
            "maximum_weighted_conditional_error"
        ]
        <= gates["maximum_weighted_conditional_error"],
        "action_identity": aggregate["action_identity_mismatches"]
        <= gates["maximum_action_identity_mismatches"],
        "zero_sum": aggregate["maximum_zero_sum_error"]
        <= gates["maximum_zero_sum_error"],
        "row_count": len(rows) == gates["expected_rows"],
        "validation_h32_speedup": aggregate["validation_h32_speedup"]
        >= gates["minimum_validation_h32_speedup"],
        "all_h32_speedup": aggregate["minimum_h32_speedup"]
        >= gates["minimum_all_h32_speedup"],
        "h32_sparse_latency": aggregate["maximum_h32_sparse_median_ms"]
        <= gates["maximum_h32_sparse_median_ms"],
        "h32_sparse_peak": aggregate["maximum_h32_sparse_peak_numeric_bytes"]
        <= gates["maximum_h32_sparse_peak_numeric_bytes"],
        "h32_sparse_operator_bytes": aggregate[
            "maximum_h32_sparse_operator_numeric_bytes"
        ]
        <= gates["maximum_h32_sparse_operator_numeric_bytes"],
        "charged_first_use": all(
            bool(row["charged_first_use_sparse_is_faster"])
            for row in rows
            if row["hands_per_player"] == 32
        )
        == gates["require_charged_first_use_faster_at_h32"],
        "source_nnz": all(bool(row["source_nnz_exact"]) for row in rows)
        == gates["require_exact_source_nnz"],
        "finite_outputs": all(bool(row["finite_sparse_outputs"]) for row in rows)
        == gates["require_finite_sparse_outputs"],
    }
    gate_results["passed"] = all(gate_results.values())
    return {
        "schema_version": 1,
        "experiment_type": "csr_sparse_incidence_open_mode_backend_audit",
        "status": "frozen_audit_executed",
        "config": parsed,
        "config_sha256": _sha256(_CONFIG),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "rows": rows,
        "counts": {"rows": len(rows)},
        "aggregate": aggregate,
        "gates": gate_results,
        "timing": {
            "wall_seconds": time.perf_counter() - started,
            "scipy_import_ms": scipy_import_ms,
        },
        "environment": {
            **environment_metadata(),
            "numpy_version": np.__version__,
            "scipy_version": scipy.__version__,
        },
        "limitations": [
            "SciPy CSR is an optional performance ceiling and not yet the final native CPU/GPU kernel.",
            "The speed customer is six direct all-check terminal automata; full policy-conditioned public-tree composition remains unmeasured.",
            "Balanced h32 and the cap-96 choice are disclosed development evidence; blocker-heavy h32 is the untouched speed validation family.",
            "Sparse query multiplication changes Float64 summation order and is accepted only through final hand-vector, action, and zero-sum gates.",
            "This audit measures exact evaluation mechanics, not policy improvement or multiplayer convergence.",
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
    result = run_sparse_incidence_audit(config)
    rendered = json.dumps(result, indent=2, sort_keys=True, allow_nan=False)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered + "\n", encoding="utf-8")
    print(
        "sparse-incidence audit: "
        f"rows={result['counts']['rows']}, "
        f"validation_speedup={result['aggregate']['validation_h32_speedup']:.3f}x, "
        f"passed={result['gates']['passed']}, "
        f"wall={result['timing']['wall_seconds']:.3f}s"
    )
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
