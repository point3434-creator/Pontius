"""Run the frozen fixed-policy public-tree root tensor-train audit."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
from pathlib import Path
from typing import Any

import numpy as np

from .factor_tt_contraction import FactorTTBeliefWorkspace, FactorTTTopology
from .factorized_belief import FactorizedCardBelief, MaterializedCardBelief
from .factorized_belief_audit import _derived_seed, _raw_factors, generate_hand_axes
from .public_policy_tt import (
    compose_public_policy_root_tt,
    dense_public_policy_root,
    information_schema_for_axes,
    representative_public_tree,
)
from .public_tree_tensor import PublicTreeTensorEvaluator
from .reporting import environment_metadata
from .river import parse_cards
from .showdown_value_rank_screen import (
    _game_from_belief,
    _payoff_operator,
    _policies,
    _rank_codes,
    _terminal_groups,
)
from .tensor_train import TensorTrain
from .tensor_train_algebra import round_tensor_train

_ROOT = Path(__file__).parents[2]
_CONFIG_FIELDS = {
    "evidence_stage",
    "seed",
    "expected_river_sha256",
    "expected_multiway_game_sha256",
    "expected_public_tree_tensor_sha256",
    "expected_factorized_belief_sha256",
    "expected_factor_tt_contraction_sha256",
    "expected_tensor_train_sha256",
    "expected_rank_screen_sha256",
    "board",
    "pot",
    "stack",
    "bet_size",
    "players",
    "split_index",
    "expected_public_nodes",
    "expected_terminal_nodes",
    "expected_terminal_groups",
    "hands_per_player",
    "range_families",
    "mixture_component_counts",
    "policy_families",
    "target_players",
    "rank_caps",
    "exact_arm",
    "terminal_relative_tolerance",
    "node_relative_tolerance",
    "policy_core_rule",
    "branch_rule",
    "terminal_rule",
    "dense_oracle_rule",
    "literal_quotient_control_hands",
    "query_chunk_records",
    "gates",
}
_GATE_FIELDS = {
    "maximum_terminal_operator_error",
    "maximum_exact_root_tensor_error",
    "maximum_exact_root_utility_error",
    "maximum_literal_quotient_utility_error",
    "maximum_safe_normalized_utility_error",
    "maximum_safe_root_storage_ratio",
    "maximum_safe_middle_rank_ratio_to_64_rank8_passes",
    "maximum_safe_rank_cap",
    "require_single_safe_compressed_arm",
    "require_zero_reach_policy_coverage",
}
_SOURCE_PATHS = {
    "expected_river_sha256": _ROOT / "src" / "pontius" / "river.py",
    "expected_multiway_game_sha256": (
        _ROOT / "src" / "pontius" / "river_multiway.py"
    ),
    "expected_public_tree_tensor_sha256": (
        _ROOT / "src" / "pontius" / "public_tree_tensor.py"
    ),
    "expected_factorized_belief_sha256": (
        _ROOT / "src" / "pontius" / "factorized_belief.py"
    ),
    "expected_factor_tt_contraction_sha256": (
        _ROOT / "src" / "pontius" / "factor_tt_contraction.py"
    ),
    "expected_tensor_train_sha256": _ROOT / "src" / "pontius" / "tensor_train.py",
    "expected_rank_screen_sha256": (
        _ROOT / "src" / "pontius" / "showdown_value_rank_screen.py"
    ),
}
_FAMILIES = ("balanced", "blocker_heavy")
_POLICIES = ("uniform", "hashed_dense", "hashed_pure")
_EXACT_ARM = "relative_tolerance_only"


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


def parse_public_policy_tt_config(config: dict[str, Any]) -> dict[str, Any]:
    if set(config) != _CONFIG_FIELDS:
        raise ValueError(
            "public-policy TT fields differ from ADR-0067: "
            f"missing={sorted(_CONFIG_FIELDS - set(config))!r}, "
            f"unknown={sorted(set(config) - _CONFIG_FIELDS)!r}"
        )
    if config["evidence_stage"] != "preregistered_revealed_engineering_audit":
        raise ValueError("public-policy TT audit must remain preregistered revealed")
    if config["seed"] != 20260819:
        raise ValueError("public-policy TT seed differs from ADR-0067")
    for field, path in _SOURCE_PATHS.items():
        if config[field] != _sha256(path):
            raise ValueError(f"frozen source hash mismatch for {field}")

    frozen_sequences = {
        "board": ("2c", "7d", "9h", "Js", "Qc"),
        "hands_per_player": (4, 7),
        "range_families": _FAMILIES,
        "mixture_component_counts": (1, 3),
        "policy_families": _POLICIES,
        "target_players": (0, 3, 5),
        "rank_caps": (8, 16, 32),
    }
    parsed_sequences: dict[str, tuple[object, ...]] = {}
    for field, expected in frozen_sequences.items():
        values = tuple(config[field])
        if values != expected:
            raise ValueError(f"{field} differs from ADR-0067")
        parsed_sequences[field] = values

    frozen_scalars = {
        "pot": 12.0,
        "stack": 30.0,
        "bet_size": 3.0,
        "players": 6,
        "split_index": 3,
        "expected_public_nodes": 385,
        "expected_terminal_nodes": 193,
        "expected_terminal_groups": 64,
        "exact_arm": _EXACT_ARM,
        "terminal_relative_tolerance": 1e-13,
        "node_relative_tolerance": 1e-12,
        "policy_core_rule": (
            "multiply_acting_seat_mode_by_hand_action_probability"
        ),
        "branch_rule": "exact_tt_direct_sum_then_round_at_each_public_node",
        "terminal_rule": (
            "group_literal_payoffs_then_numerically_round_untruncated_tt"
        ),
        "dense_oracle_rule": (
            "recursive_full_cartesian_public_tree_without_joint_card_tensor"
        ),
        "literal_quotient_control_hands": 4,
        "query_chunk_records": 256,
    }
    if any(config[field] != value for field, value in frozen_scalars.items()):
        raise ValueError("public-policy TT execution contract differs from ADR-0067")

    gates = config["gates"]
    if not isinstance(gates, dict) or set(gates) != _GATE_FIELDS:
        raise ValueError("public-policy TT gates differ from ADR-0067")
    parsed_gates = dict(gates)
    frozen_tolerances = {
        "maximum_terminal_operator_error": 1e-9,
        "maximum_exact_root_tensor_error": 1e-8,
        "maximum_exact_root_utility_error": 1e-8,
        "maximum_literal_quotient_utility_error": 1e-10,
        "maximum_safe_normalized_utility_error": 1e-4,
        "maximum_safe_root_storage_ratio": 0.25,
        "maximum_safe_middle_rank_ratio_to_64_rank8_passes": 0.25,
    }
    for field, expected in frozen_tolerances.items():
        parsed_gates[field] = _finite_nonnegative(gates[field], field)
        if parsed_gates[field] != expected:
            raise ValueError(f"{field} differs from ADR-0067")
    if gates["maximum_safe_rank_cap"] != 32:
        raise ValueError("maximum safe public-policy TT rank differs from ADR-0067")
    for field in (
        "require_single_safe_compressed_arm",
        "require_zero_reach_policy_coverage",
    ):
        if gates[field] is not True:
            raise ValueError(f"{field} must remain true")
    return {
        **config,
        **parsed_sequences,
        **frozen_scalars,
        "gates": parsed_gates,
    }


def _arm_names(parsed: dict[str, Any]) -> tuple[str, ...]:
    return (
        *(f"rank_{rank}" for rank in parsed["rank_caps"]),
        parsed["exact_arm"],
    )


def _arm_rank(arm: str) -> int | None:
    return None if arm == _EXACT_ARM else int(arm.removeprefix("rank_"))


def _explicit_expectation(
    materialized: MaterializedCardBelief,
    values: np.ndarray,
) -> float:
    indices = np.ascontiguousarray(materialized.assignments, dtype=np.int32)
    return float(materialized.probabilities @ values[tuple(indices.T)])


def _terminal_library(
    *,
    groups: tuple[object, ...],
    rank_codes: np.ndarray,
    player: int,
    pot: float,
    bet_size: float,
    tolerance: float,
) -> tuple[
    dict[str, np.ndarray],
    dict[str, TensorTrain],
    dict[str, object],
]:
    dense_by_digest: dict[str, np.ndarray] = {}
    group_dense: dict[str, np.ndarray] = {}
    group_digest: dict[str, str] = {}
    literal_dense_bytes = 0
    for supplied_group in groups:
        group = supplied_group  # narrow private dataclass without exporting its type
        values = _payoff_operator(
            group=group,
            rank_codes=rank_codes,
            pot=pot,
            bet_size=bet_size,
        )[player].copy(order="C")
        literal_dense_bytes += values.nbytes
        digest = hashlib.sha256(values.tobytes(order="C")).hexdigest()
        previous = dense_by_digest.get(digest)
        if previous is not None and not np.array_equal(previous, values):
            raise AssertionError("terminal operator SHA-256 collision")
        canonical = previous if previous is not None else values
        dense_by_digest.setdefault(digest, canonical)
        group_dense[group.key] = canonical
        group_digest[group.key] = digest

    train_by_digest: dict[str, TensorTrain] = {}
    maximum_error = 0.0
    maximum_rank = 1
    started = time.perf_counter()
    for digest, dense in dense_by_digest.items():
        rounded = round_tensor_train(
            TensorTrain.from_dense(dense),
            relative_tolerance=tolerance,
        )
        train_by_digest[digest] = rounded.train
        maximum_rank = max(maximum_rank, *rounded.output_ranks)
        maximum_error = max(
            maximum_error,
            float(np.max(np.abs(rounded.train.to_dense() - dense))),
        )
    compile_ms = (time.perf_counter() - started) * 1000.0
    group_trains = {
        key: train_by_digest[digest] for key, digest in group_digest.items()
    }
    return (
        group_dense,
        group_trains,
        {
            "player": player,
            "terminal_groups": len(group_dense),
            "deduplicated_operators": len(dense_by_digest),
            "literal_group_dense_bytes": literal_dense_bytes,
            "deduplicated_dense_bytes": sum(
                values.nbytes for values in dense_by_digest.values()
            ),
            "deduplicated_tt_bytes": sum(
                train.storage_bytes for train in train_by_digest.values()
            ),
            "maximum_terminal_rank": maximum_rank,
            "maximum_terminal_operator_error": maximum_error,
            "terminal_compile_ms": compile_ms,
        },
    )


def run_public_policy_tt_audit(config: dict[str, Any]) -> dict[str, Any]:
    """Execute the frozen ADR-0067 public-policy root-TT workload."""

    parsed = parse_public_policy_tt_config(config)
    started = time.perf_counter()
    board = parse_cards(*parsed["board"])
    arms = _arm_names(parsed)
    terminal_rows = []
    composition_rows = []
    utility_rows = []
    pure_rows = 0

    for hand_count in parsed["hands_per_player"]:
        for family in parsed["range_families"]:
            axis_seed = _derived_seed(
                parsed["seed"],
                "public-policy-root-axis",
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
            layout = representative_public_tree(
                base_belief,
                pot=parsed["pot"],
                stack=parsed["stack"],
                bet_size=parsed["bet_size"],
            )
            groups = _terminal_groups(layout)
            if (
                layout.public_node_count != parsed["expected_public_nodes"]
                or layout.terminal_node_count != parsed["expected_terminal_nodes"]
                or len(groups) != parsed["expected_terminal_groups"]
            ):
                raise ValueError("public-policy topology differs from ADR-0067")
            schema = information_schema_for_axes(layout, axes)
            policies = _policies(schema, axis_seed)
            rank_codes = _rank_codes(board, axes)
            topology = FactorTTTopology.compile(
                base_belief,
                split_index=parsed["split_index"],
            )

            belief_cases: dict[
                int,
                tuple[FactorizedCardBelief, FactorTTBeliefWorkspace, MaterializedCardBelief],
            ] = {}
            for components in parsed["mixture_component_counts"]:
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
                belief_cases[components] = (
                    belief,
                    workspace,
                    belief.materialize(),
                )

            quotient_utilities: dict[tuple[int, str], tuple[float, ...]] = {}
            if hand_count == parsed["literal_quotient_control_hands"]:
                for components, (belief, _, _) in belief_cases.items():
                    literal_layout = PublicTreeTensorEvaluator(
                        _game_from_belief(
                            belief=belief,
                            pot=parsed["pot"],
                            stack=parsed["stack"],
                            bet_size=parsed["bet_size"],
                        )
                    )
                    if literal_layout.information_schema() != schema:
                        raise AssertionError("literal and topology-only schemas differ")
                    for policy_name in parsed["policy_families"]:
                        result = literal_layout.evaluate(policies[policy_name])
                        quotient_utilities[(components, policy_name)] = (
                            result.evaluation.utilities
                        )

            for player in parsed["target_players"]:
                terminal_dense, terminal_trains, terminal_summary = _terminal_library(
                    groups=groups,
                    rank_codes=rank_codes,
                    player=player,
                    pot=parsed["pot"],
                    bet_size=parsed["bet_size"],
                    tolerance=parsed["terminal_relative_tolerance"],
                )
                terminal_rows.append(
                    {
                        "hands_per_player": hand_count,
                        "family": family,
                        **terminal_summary,
                    }
                )
                for policy_name in parsed["policy_families"]:
                    policy = policies[policy_name]
                    dense_started = time.perf_counter()
                    dense_root = dense_public_policy_root(
                        layout,
                        axes,
                        policy,
                        terminal_dense,
                    )
                    dense_oracle_ms = (time.perf_counter() - dense_started) * 1000.0
                    for arm in arms:
                        composition_started = time.perf_counter()
                        composition = compose_public_policy_root_tt(
                            layout,
                            axes,
                            policy,
                            terminal_trains,
                            relative_tolerance=parsed["node_relative_tolerance"],
                            maximum_rank=_arm_rank(arm),
                        )
                        composition_ms = (
                            time.perf_counter() - composition_started
                        ) * 1000.0
                        reconstruction_started = time.perf_counter()
                        reconstructed = composition.root.to_dense()
                        reconstruction_ms = (
                            time.perf_counter() - reconstruction_started
                        ) * 1000.0
                        root_error = float(
                            np.max(np.abs(reconstructed - dense_root))
                        )
                        middle_rank = composition.root.ranks[parsed["split_index"]]
                        composition_rows.append(
                            {
                                "hands_per_player": hand_count,
                                "family": family,
                                "policy": policy_name,
                                "player": player,
                                "arm": arm,
                                "declared_rank_cap": _arm_rank(arm),
                                "dense_oracle_ms": dense_oracle_ms,
                                "composition_ms": composition_ms,
                                "reconstruction_ms": reconstruction_ms,
                                "root_tensor_error": root_error,
                                "root_ranks": composition.root.ranks,
                                "middle_rank": middle_rank,
                                "maximum_raw_rank": composition.maximum_raw_rank,
                                "maximum_output_rank": (
                                    composition.maximum_output_rank
                                ),
                                "maximum_relative_discarded_bound": (
                                    composition.maximum_relative_discarded_bound
                                ),
                                "sum_relative_discarded_bounds": (
                                    composition.sum_relative_discarded_bounds
                                ),
                                "root_tt_bytes": composition.root.storage_bytes,
                                "dense_root_bytes": dense_root.nbytes,
                                "root_storage_ratio": (
                                    composition.root.storage_bytes / dense_root.nbytes
                                ),
                                "middle_rank_ratio_to_64_rank8_passes": (
                                    middle_rank / (64 * 8)
                                ),
                            }
                        )
                        for components, (_, workspace, materialized) in belief_cases.items():
                            literal_utility = _explicit_expectation(
                                materialized,
                                dense_root,
                            )
                            contraction_started = time.perf_counter()
                            direct = workspace.contract(composition.root)
                            contraction_ms = (
                                time.perf_counter() - contraction_started
                            ) * 1000.0
                            quotient_error: float | None = None
                            if hand_count == parsed["literal_quotient_control_hands"]:
                                quotient_error = abs(
                                    literal_utility
                                    - quotient_utilities[(components, policy_name)][player]
                                )
                            utility_rows.append(
                                {
                                    "hands_per_player": hand_count,
                                    "family": family,
                                    "mixture_components": components,
                                    "policy": policy_name,
                                    "player": player,
                                    "arm": arm,
                                    "declared_rank_cap": _arm_rank(arm),
                                    "literal_root_utility": literal_utility,
                                    "candidate_root_utility": direct.expectation,
                                    "root_utility_error": abs(
                                        direct.expectation - literal_utility
                                    ),
                                    "normalized_root_utility_error": (
                                        abs(direct.expectation - literal_utility)
                                        / (parsed["pot"] + parsed["players"] * parsed["bet_size"])
                                    ),
                                    "literal_quotient_utility_error": quotient_error,
                                    "direct_contraction_ms": contraction_ms,
                                    "middle_rank": direct.middle_rank,
                                    "feature_width": direct.feature_width,
                                    "incidence_feature_updates": (
                                        direct.incidence_feature_updates
                                    ),
                                    "query_feature_terms": direct.query_feature_terms,
                                    "estimated_peak_total_numeric_bytes": (
                                        direct.estimated_peak_total_numeric_bytes
                                    ),
                                    "numerator_cancellation_ratio": (
                                        direct.numerator_cancellation_ratio
                                    ),
                                }
                            )
                            pure_rows += int(policy_name == "hashed_pure")

    expected_terminal_rows = (
        len(parsed["hands_per_player"])
        * len(parsed["range_families"])
        * len(parsed["target_players"])
    )
    expected_composition_rows = (
        expected_terminal_rows * len(parsed["policy_families"]) * len(arms)
    )
    expected_utility_rows = expected_composition_rows * len(
        parsed["mixture_component_counts"]
    )
    if (
        len(terminal_rows) != expected_terminal_rows
        or len(composition_rows) != expected_composition_rows
        or len(utility_rows) != expected_utility_rows
    ):
        raise AssertionError("public-policy TT row counts differ from ADR-0067")

    maximum_terminal_error = max(
        float(row["maximum_terminal_operator_error"]) for row in terminal_rows
    )
    exact_compositions = [
        row for row in composition_rows if row["arm"] == parsed["exact_arm"]
    ]
    exact_utilities = [
        row for row in utility_rows if row["arm"] == parsed["exact_arm"]
    ]
    maximum_exact_root_error = max(
        float(row["root_tensor_error"]) for row in exact_compositions
    )
    maximum_exact_utility_error = max(
        float(row["root_utility_error"]) for row in exact_utilities
    )
    maximum_quotient_error = max(
        float(row["literal_quotient_utility_error"])
        for row in utility_rows
        if row["literal_quotient_utility_error"] is not None
    )
    arm_summaries = []
    for arm in arms:
        arm_compositions = [row for row in composition_rows if row["arm"] == arm]
        arm_utilities = [row for row in utility_rows if row["arm"] == arm]
        rank_cap = _arm_rank(arm)
        summary = {
            "arm": arm,
            "declared_rank_cap": rank_cap,
            "maximum_root_tensor_error": max(
                float(row["root_tensor_error"]) for row in arm_compositions
            ),
            "maximum_root_utility_error": max(
                float(row["root_utility_error"]) for row in arm_utilities
            ),
            "maximum_normalized_root_utility_error": max(
                float(row["normalized_root_utility_error"])
                for row in arm_utilities
            ),
            "maximum_root_storage_ratio": max(
                float(row["root_storage_ratio"]) for row in arm_compositions
            ),
            "maximum_middle_rank_ratio_to_64_rank8_passes": max(
                float(row["middle_rank_ratio_to_64_rank8_passes"])
                for row in arm_compositions
            ),
            "maximum_middle_rank": max(
                int(row["middle_rank"]) for row in arm_compositions
            ),
            "total_composition_ms": sum(
                float(row["composition_ms"]) for row in arm_compositions
            ),
            "total_direct_contraction_ms": sum(
                float(row["direct_contraction_ms"]) for row in arm_utilities
            ),
        }
        gates = parsed["gates"]
        summary["value_safe_compressed_arm"] = bool(
            rank_cap is not None
            and rank_cap <= gates["maximum_safe_rank_cap"]
            and summary["maximum_normalized_root_utility_error"]
            <= gates["maximum_safe_normalized_utility_error"]
            and summary["maximum_root_storage_ratio"]
            <= gates["maximum_safe_root_storage_ratio"]
            and summary["maximum_middle_rank_ratio_to_64_rank8_passes"]
            <= gates["maximum_safe_middle_rank_ratio_to_64_rank8_passes"]
        )
        arm_summaries.append(summary)
    safe_arms = tuple(
        row["arm"] for row in arm_summaries if row["value_safe_compressed_arm"]
    )
    gates = parsed["gates"]
    expected_pure_rows = (
        expected_terminal_rows * len(arms) * len(parsed["mixture_component_counts"])
    )
    gate_results = {
        "terminal_operator_identity": (
            maximum_terminal_error <= gates["maximum_terminal_operator_error"]
        ),
        "exact_root_tensor_identity": (
            maximum_exact_root_error <= gates["maximum_exact_root_tensor_error"]
        ),
        "exact_root_utility_identity": (
            maximum_exact_utility_error <= gates["maximum_exact_root_utility_error"]
        ),
        "literal_quotient_utility_identity": (
            maximum_quotient_error <= gates["maximum_literal_quotient_utility_error"]
        ),
        "single_safe_compressed_arm": (
            bool(safe_arms)
            if gates["require_single_safe_compressed_arm"]
            else True
        ),
        "zero_reach_policy_coverage": (
            pure_rows == expected_pure_rows
            if gates["require_zero_reach_policy_coverage"]
            else True
        ),
    }

    return {
        "schema_version": 1,
        "experiment_type": "fixed_public_policy_root_tensor_train_audit",
        "status": "preregistered_revealed_engineering_audit_only",
        "config": parsed,
        "config_sha256": _sha256(
            _ROOT
            / "experiments"
            / "configs"
            / "public-policy-root-tt-audit-v1.json"
        ),
        "environment": environment_metadata(),
        "counts": {
            "terminal_rows": len(terminal_rows),
            "composition_rows": len(composition_rows),
            "utility_rows": len(utility_rows),
            "pure_policy_rows": pure_rows,
        },
        "aggregate": {
            "maximum_terminal_operator_error": maximum_terminal_error,
            "maximum_exact_root_tensor_error": maximum_exact_root_error,
            "maximum_exact_root_utility_error": maximum_exact_utility_error,
            "maximum_literal_quotient_utility_error": maximum_quotient_error,
            "value_safe_compressed_arms": safe_arms,
        },
        "arm_summaries": arm_summaries,
        "gates": {"results": gate_results, "passed": all(gate_results.values())},
        "timing": {"wall_seconds": time.perf_counter() - started},
        "terminal_rows": terminal_rows,
        "composition_rows": composition_rows,
        "utility_rows": utility_rows,
        "limitations": [
            "Fixed-policy scalar utilities do not certify best-response actions.",
            "Only one board and four/seven-hand axes are audited.",
            "Terminal dense tensors are used offline to compile exact TT controls.",
            "Python TT composition timings are not online latency predictions.",
            "Only target seats 0, 3, and 5 are screened.",
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
    result = run_public_policy_tt_audit(config)
    rendered = json.dumps(result, indent=2, sort_keys=True, allow_nan=False)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(
        "public-policy root TT: "
        f"composition={result['counts']['composition_rows']}, "
        f"safe={result['aggregate']['value_safe_compressed_arms']}, "
        f"passed={result['gates']['passed']}, "
        f"wall={result['timing']['wall_seconds']:.3f}s"
    )
    if args.output is not None:
        print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
