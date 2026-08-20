"""Run the frozen direct factor-belief/tensor-train contraction audit."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
from pathlib import Path
from statistics import median
from typing import Any, Callable, TypeVar

import numpy as np

from .factor_tt_contraction import (
    EnumeratedFactorTTExpectation,
    FactorTTBeliefWorkspace,
    FactorTTContraction,
    FactorTTTopology,
    enumerated_factor_tt_expectation,
)
from .factorized_belief import FactorizedCardBelief, MaterializedCardBelief
from .factorized_belief_audit import _derived_seed, _raw_factors, generate_hand_axes
from .reporting import environment_metadata
from .river import parse_cards
from .showdown_value_rank_screen import _TerminalGroup, _payoff_operator, _rank_codes
from .tensor_train import TensorTrain

_T = TypeVar("_T")
_ROOT = Path(__file__).parents[2]
_CONFIG_FIELDS = {
    "evidence_stage",
    "seed",
    "expected_river_sha256",
    "expected_factorized_belief_sha256",
    "expected_factorized_audit_sha256",
    "expected_tensor_train_sha256",
    "expected_rank_screen_sha256",
    "board",
    "players",
    "split_index",
    "range_families",
    "actual_hands_per_player",
    "actual_mixture_component_counts",
    "actual_operator_cases",
    "actual_rank_cap",
    "exact_arm",
    "pot",
    "bet_size",
    "performance_hands_per_player",
    "performance_mixture_components",
    "performance_tt_rank",
    "performance_baseline_maximum_hands",
    "incidence_rule",
    "topology_reuse_rule",
    "belief_reuse_rule",
    "summation_rule",
    "query_chunk_records",
    "timing_repeats",
    "wide_timing_repeats",
    "warmup_repeats",
    "gates",
}
_GATE_FIELDS = {
    "maximum_partition_relative_error",
    "maximum_direct_vs_reconstructed_expectation_error",
    "maximum_untruncated_vs_literal_expectation_error",
    "maximum_synthetic_direct_vs_joint_error",
    "maximum_32_hand_peak_byte_ratio_to_dense_operator",
    "ten_hand_direct_strictly_faster_than_enumerated_joint",
    "require_contiguous_numeric_topology",
    "require_topology_and_belief_workspace_reuse",
}
_SOURCE_PATHS = {
    "expected_river_sha256": _ROOT / "src" / "pontius" / "river.py",
    "expected_factorized_belief_sha256": (
        _ROOT / "src" / "pontius" / "factorized_belief.py"
    ),
    "expected_factorized_audit_sha256": (
        _ROOT / "src" / "pontius" / "factorized_belief_audit.py"
    ),
    "expected_tensor_train_sha256": _ROOT / "src" / "pontius" / "tensor_train.py",
    "expected_rank_screen_sha256": (
        _ROOT / "src" / "pontius" / "showdown_value_rank_screen.py"
    ),
}
_FAMILIES = ("balanced", "blocker_heavy")
_OPERATOR_CASES = (
    ("all_check", 0),
    ("contenders_0", 0),
    ("contenders_0_5", 0),
    ("contenders_0_2_5", 2),
    ("contenders_0_1_2_3_4_5", 4),
    ("contenders_1_3_5", 0),
)
_EXACT_ARM = "untruncated_tt_svd"


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required frozen source is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _finite_nonnegative(value: object, label: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{label} must be finite and nonnegative")
    try:
        result = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as error:
        raise ValueError(f"{label} must be finite and nonnegative") from error
    if not math.isfinite(result) or result < 0.0:
        raise ValueError(f"{label} must be finite and nonnegative")
    return result


def parse_factor_tt_contraction_config(config: dict[str, Any]) -> dict[str, Any]:
    if set(config) != _CONFIG_FIELDS:
        raise ValueError(
            "factor–TT fields differ from ADR-0065: "
            f"missing={sorted(_CONFIG_FIELDS - set(config))!r}, "
            f"unknown={sorted(set(config) - _CONFIG_FIELDS)!r}"
        )
    if config["evidence_stage"] != "preregistered_revealed_engineering_audit":
        raise ValueError("factor–TT audit must remain preregistered revealed engineering")
    if config["seed"] != 20260819:
        raise ValueError("factor–TT seed differs from ADR-0065")
    for field, path in _SOURCE_PATHS.items():
        if config[field] != _sha256(path):
            raise ValueError(f"frozen source hash mismatch for {field}")

    frozen_sequences = {
        "board": ("2c", "7d", "9h", "Js", "Qc"),
        "range_families": _FAMILIES,
        "actual_hands_per_player": (4, 5, 7),
        "actual_mixture_component_counts": (1, 3),
        "performance_hands_per_player": (4, 7, 10, 16, 24, 32),
    }
    parsed_sequences: dict[str, tuple[object, ...]] = {}
    for field, expected in frozen_sequences.items():
        values = tuple(config[field])
        if values != expected:
            raise ValueError(f"{field} differs from ADR-0065")
        parsed_sequences[field] = values

    supplied_cases = config["actual_operator_cases"]
    if not isinstance(supplied_cases, list) or any(
        not isinstance(case, dict) or set(case) != {"terminal_group", "player"}
        for case in supplied_cases
    ):
        raise ValueError("factor–TT operator cases differ from ADR-0065")
    operator_cases = tuple(
        (case["terminal_group"], case["player"]) for case in supplied_cases
    )
    if operator_cases != _OPERATOR_CASES:
        raise ValueError("factor–TT operator cases differ from ADR-0065")

    frozen_scalars = {
        "players": 6,
        "split_index": 3,
        "actual_rank_cap": 8,
        "exact_arm": _EXACT_ARM,
        "pot": 12.0,
        "bet_size": 3.0,
        "performance_mixture_components": 3,
        "performance_tt_rank": 8,
        "performance_baseline_maximum_hands": 10,
        "incidence_rule": (
            "right_used_card_subsets_with_left_inclusion_exclusion"
        ),
        "topology_reuse_rule": "compile_once_per_board_axes_and_split",
        "belief_reuse_rule": (
            "compile_partition_and_half_unaries_once_per_range"
        ),
        "summation_rule": (
            "float64_pairwise_queries_and_fsum_outer_accumulation"
        ),
        "query_chunk_records": 256,
        "timing_repeats": 3,
        "wide_timing_repeats": 1,
        "warmup_repeats": 1,
    }
    if any(config[field] != value for field, value in frozen_scalars.items()):
        raise ValueError("factor–TT execution contract differs from ADR-0065")

    gates = config["gates"]
    if not isinstance(gates, dict) or set(gates) != _GATE_FIELDS:
        raise ValueError("factor–TT gates differ from ADR-0065")
    parsed_gates = dict(gates)
    frozen_tolerances = {
        "maximum_partition_relative_error": 1e-10,
        "maximum_direct_vs_reconstructed_expectation_error": 1e-10,
        "maximum_untruncated_vs_literal_expectation_error": 1e-9,
        "maximum_synthetic_direct_vs_joint_error": 1e-10,
        "maximum_32_hand_peak_byte_ratio_to_dense_operator": 0.01,
    }
    for field, expected in frozen_tolerances.items():
        parsed_gates[field] = _finite_nonnegative(gates[field], field)
        if parsed_gates[field] != expected:
            raise ValueError(f"{field} differs from ADR-0065")
    for field in (
        "ten_hand_direct_strictly_faster_than_enumerated_joint",
        "require_contiguous_numeric_topology",
        "require_topology_and_belief_workspace_reuse",
    ):
        if gates[field] is not True:
            raise ValueError(f"{field} must remain true")

    return {
        **config,
        **parsed_sequences,
        **frozen_scalars,
        "actual_operator_cases": operator_cases,
        "gates": parsed_gates,
    }


def _terminal_group(key: str, players: int) -> _TerminalGroup:
    if key == "all_check":
        return _TerminalGroup(
            key=key,
            contenders=tuple(range(players)),
            contributed=False,
            terminal_slots=(),
        )
    prefix = "contenders_"
    if not key.startswith(prefix):
        raise ValueError(f"unknown terminal payoff group {key!r}")
    contenders = tuple(int(value) for value in key.removeprefix(prefix).split("_"))
    if not contenders or tuple(sorted(set(contenders))) != contenders or any(
        player not in range(players) for player in contenders
    ):
        raise ValueError(f"invalid terminal contenders in {key!r}")
    return _TerminalGroup(
        key=key,
        contenders=contenders,
        contributed=True,
        terminal_slots=(),
    )


def _relative_error(first: float, second: float) -> float:
    return abs(first - second) / max(abs(first), abs(second), 1e-300)


def _timed(
    operation: Callable[[], _T],
    *,
    repeats: int,
    warmups: int,
) -> tuple[float, float, tuple[float, ...], _T]:
    result: _T
    for _ in range(warmups):
        result = operation()
    samples = []
    for _ in range(repeats):
        started = time.perf_counter()
        result = operation()
        samples.append((time.perf_counter() - started) * 1000.0)
    return median(samples), min(samples), tuple(samples), result


def _explicit_dense_expectation(
    materialized: MaterializedCardBelief,
    values: np.ndarray,
) -> float:
    indices = np.ascontiguousarray(materialized.assignments, dtype=np.int32)
    gathered = values[tuple(indices.T)]
    return float(materialized.probabilities @ gathered)


def _synthetic_train(
    *,
    hand_count: int,
    players: int,
    rank: int,
    seed: int,
) -> TensorTrain:
    rng = np.random.default_rng(seed)
    ranks = (1, *(rank for _ in range(players - 1)), 1)
    cores = []
    for mode in range(players):
        previous_rank = ranks[mode]
        next_rank = ranks[mode + 1]
        values = rng.normal(
            0.0,
            1.0 / math.sqrt(max(1, previous_rank)),
            size=(previous_rank, hand_count, next_rank),
        )
        cores.append(values)
    return TensorTrain(
        shape=(hand_count,) * players,
        cores=tuple(cores),
        decomposition_singular_values=tuple(
            np.empty(0, dtype=np.float64) for _ in range(players - 1)
        ),
    )


def _contraction_payload(result: FactorTTContraction) -> dict[str, object]:
    return {
        "expectation": result.expectation,
        "partition": result.partition,
        "middle_rank": result.middle_rank,
        "feature_width": result.feature_width,
        "left_records": result.left_records,
        "right_records": result.right_records,
        "incidence_entries": result.incidence_entries,
        "incidence_feature_updates": result.incidence_feature_updates,
        "query_feature_terms": result.query_feature_terms,
        "topology_numeric_bytes": result.topology_numeric_bytes,
        "belief_workspace_numeric_bytes": result.belief_workspace_numeric_bytes,
        "tt_storage_bytes": result.tt_storage_bytes,
        "operator_static_numeric_bytes": result.operator_static_numeric_bytes,
        "estimated_peak_scratch_numeric_bytes": (
            result.estimated_peak_scratch_numeric_bytes
        ),
        "estimated_peak_total_numeric_bytes": (
            result.estimated_peak_total_numeric_bytes
        ),
        "numerator_absolute_term_sum": result.numerator_absolute_term_sum,
        "numerator_cancellation_ratio": result.numerator_cancellation_ratio,
    }


def run_factor_tt_contraction_audit(config: dict[str, Any]) -> dict[str, Any]:
    """Execute the frozen ADR-0065 correctness and scaling workload."""

    parsed = parse_factor_tt_contraction_config(config)
    started = time.perf_counter()
    board = parse_cards(*parsed["board"])
    actual_rows = []
    performance_rows = []
    topology_layout_failures = 0
    reuse_failures = 0

    for hand_count in parsed["actual_hands_per_player"]:
        for family in parsed["range_families"]:
            axis_seed = _derived_seed(
                parsed["seed"],
                "direct-actual-axis",
                hand_count,
                family,
            )
            axes = generate_hand_axes(
                board=board,
                players=parsed["players"],
                hands_per_player=hand_count,
                family=family,
                seed=axis_seed,
            )
            base_mixture, base_unaries = _raw_factors(
                hands_by_player=axes,
                components=1,
                seed=axis_seed,
                family=family,
            )
            base_belief = FactorizedCardBelief(
                hands_by_player=axes,
                mixture_weights=base_mixture,
                unary_weights=base_unaries,
                board=board,
            )
            topology = FactorTTTopology.compile(
                base_belief,
                split_index=parsed["split_index"],
            )
            topology_layout_failures += int(
                not topology.storage_is_contiguous_fixed_dtype()
            )

            rank_codes = _rank_codes(board, axes)
            operator_payloads = []
            for group_key, player in parsed["actual_operator_cases"]:
                group = _terminal_group(group_key, parsed["players"])
                literal = _payoff_operator(
                    group=group,
                    rank_codes=rank_codes,
                    pot=parsed["pot"],
                    bet_size=parsed["bet_size"],
                )[player].copy(order="C")
                arms = {}
                for arm, rank_cap in (
                    (f"rank_{parsed['actual_rank_cap']}", parsed["actual_rank_cap"]),
                    (parsed["exact_arm"], None),
                ):
                    decomposition_started = time.perf_counter()
                    train = TensorTrain.from_dense(literal, maximum_rank=rank_cap)
                    decomposition_ms = (
                        time.perf_counter() - decomposition_started
                    ) * 1000.0
                    reconstruction_started = time.perf_counter()
                    reconstruction = train.to_dense()
                    reconstruction_ms = (
                        time.perf_counter() - reconstruction_started
                    ) * 1000.0
                    arms[arm] = (
                        train,
                        reconstruction,
                        decomposition_ms,
                        reconstruction_ms,
                    )
                operator_payloads.append((group_key, player, literal, arms))

            workspaces = []
            for components in parsed["actual_mixture_component_counts"]:
                mixture, unaries = _raw_factors(
                    hands_by_player=axes,
                    components=components,
                    seed=axis_seed,
                    family=family,
                )
                belief = FactorizedCardBelief(
                    hands_by_player=axes,
                    mixture_weights=mixture,
                    unary_weights=unaries,
                    board=board,
                )
                workspace = FactorTTBeliefWorkspace.compile(
                    topology,
                    belief,
                    query_chunk_records=parsed["query_chunk_records"],
                )
                workspaces.append(workspace)
                reuse_failures += int(workspace.topology is not topology)
                materialized = belief.materialize()
                partition_error = _relative_error(
                    workspace.partition,
                    materialized.partition,
                )
                for group_key, player, literal, arms in operator_payloads:
                    literal_expectation = _explicit_dense_expectation(
                        materialized,
                        literal,
                    )
                    for arm, (
                        train,
                        reconstruction,
                        decomposition_ms,
                        reconstruction_ms,
                    ) in arms.items():
                        contraction_started = time.perf_counter()
                        direct = workspace.contract(train)
                        contraction_ms = (
                            time.perf_counter() - contraction_started
                        ) * 1000.0
                        reconstructed_expectation = _explicit_dense_expectation(
                            materialized,
                            reconstruction,
                        )
                        actual_rows.append(
                            {
                                "hands_per_player": hand_count,
                                "family": family,
                                "mixture_components": components,
                                "terminal_group": group_key,
                                "player": player,
                                "arm": arm,
                                "tt_ranks": train.ranks,
                                "literal_expectation": literal_expectation,
                                "reconstructed_expectation": (
                                    reconstructed_expectation
                                ),
                                "direct_expectation": direct.expectation,
                                "direct_vs_reconstructed_expectation_error": abs(
                                    direct.expectation - reconstructed_expectation
                                ),
                                "direct_vs_literal_expectation_error": abs(
                                    direct.expectation - literal_expectation
                                ),
                                "partition_relative_error": partition_error,
                                "decomposition_ms": decomposition_ms,
                                "reconstruction_ms": reconstruction_ms,
                                "direct_contraction_ms": contraction_ms,
                                "contraction": _contraction_payload(direct),
                            }
                        )
            reuse_failures += int(
                len(workspaces) < 2
                or any(workspace.topology is not topology for workspace in workspaces)
                or len(operator_payloads) < 2
            )

    ten_hand_direct_samples: list[float] = []
    ten_hand_joint_samples: list[float] = []
    for hand_count in parsed["performance_hands_per_player"]:
        for family in parsed["range_families"]:
            case_seed = _derived_seed(
                parsed["seed"],
                "direct-performance",
                hand_count,
                family,
            )
            axes = generate_hand_axes(
                board=board,
                players=parsed["players"],
                hands_per_player=hand_count,
                family=family,
                seed=case_seed,
            )
            mixture, unaries = _raw_factors(
                hands_by_player=axes,
                components=parsed["performance_mixture_components"],
                seed=case_seed,
                family=family,
            )
            belief = FactorizedCardBelief(
                hands_by_player=axes,
                mixture_weights=mixture,
                unary_weights=unaries,
                board=board,
            )
            topology_started = time.perf_counter()
            topology = FactorTTTopology.compile(
                belief,
                split_index=parsed["split_index"],
            )
            topology_ms = (time.perf_counter() - topology_started) * 1000.0
            topology_layout_failures += int(
                not topology.storage_is_contiguous_fixed_dtype()
            )
            belief_started = time.perf_counter()
            workspace = FactorTTBeliefWorkspace.compile(
                topology,
                belief,
                query_chunk_records=parsed["query_chunk_records"],
            )
            belief_compile_ms = (time.perf_counter() - belief_started) * 1000.0
            reuse_failures += int(workspace.topology is not topology)
            train = _synthetic_train(
                hand_count=hand_count,
                players=parsed["players"],
                rank=parsed["performance_tt_rank"],
                seed=case_seed,
            )
            repeats = (
                parsed["timing_repeats"]
                if hand_count <= parsed["performance_baseline_maximum_hands"]
                else parsed["wide_timing_repeats"]
            )
            direct_ms, direct_min_ms, direct_samples, direct = _timed(
                lambda: workspace.contract(train),
                repeats=repeats,
                warmups=parsed["warmup_repeats"],
            )
            baseline_ms: float | None = None
            baseline_min_ms: float | None = None
            baseline_samples: tuple[float, ...] | None = None
            baseline: EnumeratedFactorTTExpectation | None = None
            expectation_error: float | None = None
            partition_error: float | None = None
            speedup: float | None = None
            if hand_count <= parsed["performance_baseline_maximum_hands"]:
                (
                    baseline_ms,
                    baseline_min_ms,
                    baseline_samples,
                    baseline,
                ) = _timed(
                    lambda: enumerated_factor_tt_expectation(belief, train),
                    repeats=repeats,
                    warmups=parsed["warmup_repeats"],
                )
                expectation_error = abs(direct.expectation - baseline.expectation)
                partition_error = _relative_error(
                    workspace.partition,
                    baseline.partition,
                )
                speedup = baseline_ms / direct_ms
                if hand_count == 10:
                    ten_hand_direct_samples.extend(direct_samples)
                    ten_hand_joint_samples.extend(baseline_samples)

            dense_operator_bytes = hand_count**parsed["players"] * 8
            performance_rows.append(
                {
                    "hands_per_player": hand_count,
                    "family": family,
                    "mixture_components": parsed["performance_mixture_components"],
                    "tt_rank": parsed["performance_tt_rank"],
                    "topology_compile_ms": topology_ms,
                    "belief_workspace_compile_ms": belief_compile_ms,
                    "hot_operator_median_ms": direct_ms,
                    "hot_operator_minimum_ms": direct_min_ms,
                    "hot_operator_samples_ms": direct_samples,
                    "enumerated_joint_median_ms": baseline_ms,
                    "enumerated_joint_minimum_ms": baseline_min_ms,
                    "enumerated_joint_samples_ms": baseline_samples,
                    "hot_speedup_over_enumerated_joint": speedup,
                    "synthetic_expectation_error": expectation_error,
                    "partition_relative_error": partition_error,
                    "enumerated_compatible_assignments": (
                        baseline.compatible_assignments if baseline is not None else None
                    ),
                    "enumerated_joint_numeric_bytes": (
                        baseline.numeric_bytes if baseline is not None else None
                    ),
                    "dense_operator_bytes": dense_operator_bytes,
                    "peak_byte_ratio_to_dense_operator": (
                        direct.estimated_peak_total_numeric_bytes
                        / dense_operator_bytes
                    ),
                    "contraction": _contraction_payload(direct),
                }
            )

    expected_actual_rows = (
        len(parsed["actual_hands_per_player"])
        * len(parsed["range_families"])
        * len(parsed["actual_mixture_component_counts"])
        * len(parsed["actual_operator_cases"])
        * 2
    )
    expected_performance_rows = (
        len(parsed["performance_hands_per_player"])
        * len(parsed["range_families"])
    )
    if len(actual_rows) != expected_actual_rows:
        raise AssertionError("factor–TT actual row count differs from ADR-0065")
    if len(performance_rows) != expected_performance_rows:
        raise AssertionError("factor–TT performance row count differs from ADR-0065")

    maximum_partition_error = max(
        [float(row["partition_relative_error"]) for row in actual_rows]
        + [
            float(row["partition_relative_error"])
            for row in performance_rows
            if row["partition_relative_error"] is not None
        ]
    )
    maximum_direct_reconstructed_error = max(
        float(row["direct_vs_reconstructed_expectation_error"])
        for row in actual_rows
    )
    maximum_untruncated_literal_error = max(
        float(row["direct_vs_literal_expectation_error"])
        for row in actual_rows
        if row["arm"] == parsed["exact_arm"]
    )
    maximum_synthetic_error = max(
        float(row["synthetic_expectation_error"])
        for row in performance_rows
        if row["synthetic_expectation_error"] is not None
    )
    maximum_32_hand_ratio = max(
        float(row["peak_byte_ratio_to_dense_operator"])
        for row in performance_rows
        if row["hands_per_player"] == 32
    )
    rank_eight_literal_by_hands = {
        str(hand_count): max(
            float(row["direct_vs_literal_expectation_error"])
            for row in actual_rows
            if row["hands_per_player"] == hand_count
            and row["arm"] == f"rank_{parsed['actual_rank_cap']}"
        )
        for hand_count in parsed["actual_hands_per_player"]
    }
    pooled_ten_direct_ms = median(ten_hand_direct_samples)
    pooled_ten_joint_ms = median(ten_hand_joint_samples)
    gates = parsed["gates"]
    gate_results = {
        "partition_identity": (
            maximum_partition_error <= gates["maximum_partition_relative_error"]
        ),
        "direct_reconstruction_identity": (
            maximum_direct_reconstructed_error
            <= gates["maximum_direct_vs_reconstructed_expectation_error"]
        ),
        "untruncated_literal_identity": (
            maximum_untruncated_literal_error
            <= gates["maximum_untruncated_vs_literal_expectation_error"]
        ),
        "synthetic_joint_identity": (
            maximum_synthetic_error
            <= gates["maximum_synthetic_direct_vs_joint_error"]
        ),
        "wide_memory_compression": (
            maximum_32_hand_ratio
            <= gates["maximum_32_hand_peak_byte_ratio_to_dense_operator"]
        ),
        "ten_hand_hot_crossover": (
            pooled_ten_direct_ms < pooled_ten_joint_ms
            if gates["ten_hand_direct_strictly_faster_than_enumerated_joint"]
            else True
        ),
        "contiguous_numeric_topology": (
            topology_layout_failures == 0
            if gates["require_contiguous_numeric_topology"]
            else True
        ),
        "topology_and_belief_reuse": (
            reuse_failures == 0
            if gates["require_topology_and_belief_workspace_reuse"]
            else True
        ),
    }

    return {
        "schema_version": 1,
        "experiment_type": "direct_factor_belief_tensor_train_contraction_audit",
        "status": "preregistered_revealed_engineering_audit_only",
        "config": parsed,
        "config_sha256": _sha256(
            _ROOT
            / "experiments"
            / "configs"
            / "factor-tt-direct-contraction-audit-v1.json"
        ),
        "environment": environment_metadata(),
        "counts": {
            "actual_rows": len(actual_rows),
            "performance_rows": len(performance_rows),
            "topology_layout_failures": topology_layout_failures,
            "reuse_failures": reuse_failures,
        },
        "aggregate": {
            "maximum_partition_relative_error": maximum_partition_error,
            "maximum_direct_vs_reconstructed_expectation_error": (
                maximum_direct_reconstructed_error
            ),
            "maximum_untruncated_vs_literal_expectation_error": (
                maximum_untruncated_literal_error
            ),
            "maximum_synthetic_direct_vs_joint_error": maximum_synthetic_error,
            "maximum_32_hand_peak_byte_ratio_to_dense_operator": (
                maximum_32_hand_ratio
            ),
            "rank_eight_literal_expectation_error_by_hands": (
                rank_eight_literal_by_hands
            ),
            "pooled_ten_hand_hot_operator_median_ms": pooled_ten_direct_ms,
            "pooled_ten_hand_enumerated_joint_median_ms": pooled_ten_joint_ms,
            "pooled_ten_hand_speedup": (
                pooled_ten_joint_ms / pooled_ten_direct_ms
            ),
        },
        "gates": {"results": gate_results, "passed": all(gate_results.values())},
        "timing": {"wall_seconds": time.perf_counter() - started},
        "actual_rows": actual_rows,
        "performance_rows": performance_rows,
        "limitations": [
            "Scalar expectations do not measure the conditional values required by CFR.",
            "Python/NumPy timings do not predict a native C++ latency budget.",
            "Rank-eight literal accuracy is tested on one board through seven hands only.",
            "Synthetic wide operators validate contraction scaling, not poker strategy.",
            "One operator table at a time does not measure batching across terminal groups.",
        ],
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    result = run_factor_tt_contraction_audit(config)
    rendered = json.dumps(result, indent=2, sort_keys=True, allow_nan=False)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(
        "factor–TT direct contraction: "
        f"actual={result['counts']['actual_rows']}, "
        f"performance={result['counts']['performance_rows']}, "
        f"passed={result['gates']['passed']}, "
        f"wall={result['timing']['wall_seconds']:.3f}s"
    )
    if args.output is not None:
        print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
