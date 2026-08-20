"""Run the frozen guarded incremental policy-delta TT audit."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import time
from typing import Any

import numpy as np

from .evaluation import Policy
from .factor_tt_contraction import FactorTTBeliefWorkspace, FactorTTTopology
from .factorized_belief import FactorizedCardBelief, MaterializedCardBelief
from .factorized_belief_audit import _derived_seed, _raw_factors, generate_hand_axes
from .incremental_policy_tt import (
    PolicyDeltaTTCache,
    ancestor_closure,
    apply_policy_delta_tt_plan,
    compile_policy_delta_tt_cache_from_probabilities,
    compile_policy_probability_tape,
    plan_policy_delta_tt_from_probabilities,
)
from .public_policy_tt import (
    _information_key,
    dense_public_policy_root,
    information_schema_for_axes,
    representative_public_tree,
)
from .reporting import environment_metadata
from .river import HoleCards, parse_cards
from .showdown_value_rank_screen import (
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
    "expected_factorized_belief_sha256",
    "expected_factor_tt_contraction_sha256",
    "expected_tensor_train_sha256",
    "expected_public_policy_tt_sha256",
    "expected_public_policy_audit_sha256",
    "board",
    "pot",
    "stack",
    "bet_size",
    "players",
    "hands_per_player",
    "range_families",
    "mixture_components",
    "baseline_policy",
    "candidate_mutations",
    "target_players",
    "terminal_relative_tolerance",
    "node_relative_tolerance",
    "maximum_rank",
    "cache_rule",
    "dirty_rule",
    "cold_control_rule",
    "truncation_bound_rule",
    "machine_noise_rule",
    "acceptance_rule",
    "capped_product_authority",
    "exact_product_authority",
    "amortized_reuse_counts",
    "query_chunk_records",
    "gates",
}
_GATE_FIELDS = {
    "maximum_incremental_vs_cold_root_error",
    "maximum_incremental_vs_dense_utility_error",
    "maximum_positive_bound_violation",
    "maximum_zero_sum_bound_violation",
    "maximum_false_guarded_sign_certificates",
    "require_single_node_ancestor_path_only",
    "require_single_seat_four_reuse_amortized_speedup",
    "require_all_six_player_zero_sum_diagnostic",
}
_SOURCE_PATHS = {
    "expected_river_sha256": _ROOT / "src" / "pontius" / "river.py",
    "expected_factorized_belief_sha256": (
        _ROOT / "src" / "pontius" / "factorized_belief.py"
    ),
    "expected_factor_tt_contraction_sha256": (
        _ROOT / "src" / "pontius" / "factor_tt_contraction.py"
    ),
    "expected_tensor_train_sha256": _ROOT / "src" / "pontius" / "tensor_train.py",
    "expected_public_policy_tt_sha256": (
        _ROOT / "src" / "pontius" / "public_policy_tt.py"
    ),
    "expected_public_policy_audit_sha256": (
        _ROOT / "src" / "pontius" / "public_policy_tt_audit.py"
    ),
}
_FAMILIES = ("balanced", "blocker_heavy")
_MUTATIONS = (
    "single_hand_root_swap",
    "single_hand_deepest_swap",
    "all_hands_deepest_node_swap",
    "single_seat_three_all_nodes_swap",
    "full_hashed_dense_seed_shift",
)
_ONE_NODE_MUTATIONS = frozenset(_MUTATIONS[:3])


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


def parse_policy_delta_tt_config(config: dict[str, Any]) -> dict[str, Any]:
    """Strictly parse the preregistered ADR-0069 workload."""

    if set(config) != _CONFIG_FIELDS:
        raise ValueError(
            "policy-delta TT fields differ from ADR-0069: "
            f"missing={sorted(_CONFIG_FIELDS - set(config))!r}, "
            f"unknown={sorted(set(config) - _CONFIG_FIELDS)!r}"
        )
    if config["evidence_stage"] != "preregistered_revealed_engineering_audit":
        raise ValueError("policy-delta TT audit must remain preregistered revealed")
    if config["seed"] != 20260819:
        raise ValueError("policy-delta TT seed differs from ADR-0069")
    for field, path in _SOURCE_PATHS.items():
        if config[field] != _sha256(path):
            raise ValueError(f"frozen source hash mismatch for {field}")

    frozen_sequences = {
        "board": ("2c", "7d", "9h", "Js", "Qc"),
        "hands_per_player": (4, 7),
        "range_families": _FAMILIES,
        "candidate_mutations": _MUTATIONS,
        "target_players": (0, 1, 2, 3, 4, 5),
        "amortized_reuse_counts": (1, 2, 4, 8, 16),
    }
    parsed_sequences: dict[str, tuple[object, ...]] = {}
    for field, expected in frozen_sequences.items():
        values = tuple(config[field])
        if values != expected:
            raise ValueError(f"{field} differs from ADR-0069")
        parsed_sequences[field] = values

    frozen_scalars = {
        "pot": 12.0,
        "stack": 30.0,
        "bet_size": 3.0,
        "players": 6,
        "mixture_components": 3,
        "baseline_policy": "hashed_dense",
        "terminal_relative_tolerance": 1e-13,
        "node_relative_tolerance": 1e-12,
        "maximum_rank": None,
        "cache_rule": "persist_every_public_node_tt_probability_and_propagated_bound",
        "dirty_rule": "changed_policy_nodes_plus_unique_ancestor_closure",
        "cold_control_rule": "full_385_node_recomposition_from_same_terminal_library",
        "truncation_bound_rule": (
            "node_bound_equals_max_child_bound_plus_local_discarded_frobenius_bound"
        ),
        "machine_noise_rule": "epsilon_times_256_times_root_depth_times_payoff_span",
        "acceptance_rule": (
            "estimated_improvement_exceeds_candidate_plus_baseline_bounds_plus_"
            "machine_noise_plus_1e-10_span"
        ),
        "capped_product_authority": "value_estimation_and_scheduling_only_never_acceptance",
        "exact_product_authority": "guarded_acceptance_only_when_bound_clears",
        "query_chunk_records": 256,
    }
    if any(config[field] != value for field, value in frozen_scalars.items()):
        raise ValueError("policy-delta TT execution contract differs from ADR-0069")

    gates = config["gates"]
    if not isinstance(gates, dict) or set(gates) != _GATE_FIELDS:
        raise ValueError("policy-delta TT gates differ from ADR-0069")
    parsed_gates = dict(gates)
    frozen_tolerances = {
        "maximum_incremental_vs_cold_root_error": 1e-10,
        "maximum_incremental_vs_dense_utility_error": 1e-8,
        "maximum_positive_bound_violation": 0.0,
        "maximum_zero_sum_bound_violation": 0.0,
    }
    for field, expected in frozen_tolerances.items():
        parsed_gates[field] = _finite_nonnegative(gates[field], field)
        if parsed_gates[field] != expected:
            raise ValueError(f"{field} differs from ADR-0069")
    false_limit = gates["maximum_false_guarded_sign_certificates"]
    if isinstance(false_limit, bool) or false_limit != 0:
        raise ValueError("false-certificate gate differs from ADR-0069")
    for field in (
        "require_single_node_ancestor_path_only",
        "require_single_seat_four_reuse_amortized_speedup",
        "require_all_six_player_zero_sum_diagnostic",
    ):
        if gates[field] is not True:
            raise ValueError(f"{field} must remain true")
    return {
        **config,
        **parsed_sequences,
        **frozen_scalars,
        "gates": parsed_gates,
    }


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
    dict[str, float],
    dict[str, object],
]:
    dense_by_digest: dict[str, np.ndarray] = {}
    group_dense: dict[str, np.ndarray] = {}
    group_digest: dict[str, str] = {}
    literal_dense_bytes = 0
    for supplied_group in groups:
        group = supplied_group
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
        dense_by_digest.setdefault(digest, values)
        group_dense[group.key] = dense_by_digest[digest]
        group_digest[group.key] = digest

    train_by_digest: dict[str, TensorTrain] = {}
    bound_by_digest: dict[str, float] = {}
    maximum_error = 0.0
    maximum_rank = 1
    started = time.perf_counter()
    for digest, dense in dense_by_digest.items():
        rounded = round_tensor_train(
            TensorTrain.from_dense(dense),
            relative_tolerance=tolerance,
        )
        train_by_digest[digest] = rounded.train
        bound_by_digest[digest] = rounded.discarded_frobenius_bound
        maximum_rank = max(maximum_rank, *rounded.output_ranks)
        maximum_error = max(
            maximum_error,
            float(np.max(np.abs(rounded.train.to_dense() - dense))),
        )
    compile_ms = (time.perf_counter() - started) * 1000.0
    return (
        group_dense,
        {key: train_by_digest[digest] for key, digest in group_digest.items()},
        {key: bound_by_digest[digest] for key, digest in group_digest.items()},
        {
            "player": player,
            "terminal_groups": len(group_dense),
            "deduplicated_operators": len(dense_by_digest),
            "literal_group_dense_bytes": literal_dense_bytes,
            "deduplicated_dense_bytes": sum(x.nbytes for x in dense_by_digest.values()),
            "deduplicated_tt_bytes": sum(
                train.storage_bytes for train in train_by_digest.values()
            ),
            "maximum_terminal_rank": maximum_rank,
            "maximum_terminal_operator_error": maximum_error,
            "maximum_terminal_discarded_bound": max(bound_by_digest.values()),
            "terminal_compile_ms": compile_ms,
        },
    )


def _copy_policy(policy: Policy) -> Policy:
    return {key: dict(distribution) for key, distribution in policy.items()}


def _swap_key(policy: Policy, key: str, actions: tuple[str, ...]) -> None:
    if len(actions) != 2:
        raise ValueError("ADR-0069 probability swap requires exactly two actions")
    first, second = actions
    distribution = policy[key]
    distribution[first], distribution[second] = (
        distribution[second],
        distribution[first],
    )


def _first_asymmetric_key(
    *,
    layout: Any,
    hands_by_player: tuple[tuple[HoleCards, ...], ...],
    policy: Policy,
    node_index: int,
) -> str:
    node = layout.nodes[node_index]
    first, second = node.actions
    for hand in hands_by_player[node.player]:
        key = _information_key(layout, node.player, hand, node.history)
        if policy[key][first] != policy[key][second]:
            return key
    raise ValueError("frozen hashed policy is symmetric for every hand at target node")


def _candidate_policies(
    *,
    layout: Any,
    hands_by_player: tuple[tuple[HoleCards, ...], ...],
    schema: dict[str, tuple[str, ...]],
    baseline: Policy,
    seed: int,
) -> dict[str, tuple[Policy, int | None]]:
    strategic = [
        index for index, node in enumerate(layout.nodes) if node.player >= 0
    ]
    maximum_history = max(len(layout.nodes[index].history) for index in strategic)
    deepest = min(
        (index for index in strategic if len(layout.nodes[index].history) == maximum_history),
        key=lambda index: (layout.nodes[index].history, index),
    )

    root_single = _copy_policy(baseline)
    root_key = _first_asymmetric_key(
        layout=layout,
        hands_by_player=hands_by_player,
        policy=baseline,
        node_index=0,
    )
    _swap_key(root_single, root_key, layout.nodes[0].actions)

    deep_single = _copy_policy(baseline)
    deep_key = _first_asymmetric_key(
        layout=layout,
        hands_by_player=hands_by_player,
        policy=baseline,
        node_index=deepest,
    )
    _swap_key(deep_single, deep_key, layout.nodes[deepest].actions)

    deep_all = _copy_policy(baseline)
    deep_node = layout.nodes[deepest]
    for hand in hands_by_player[deep_node.player]:
        key = _information_key(layout, deep_node.player, hand, deep_node.history)
        _swap_key(deep_all, key, deep_node.actions)

    seat_all = _copy_policy(baseline)
    for node in layout.nodes:
        if node.player != 3:
            continue
        for hand in hands_by_player[3]:
            key = _information_key(layout, 3, hand, node.history)
            _swap_key(seat_all, key, node.actions)

    shifted_seed = _derived_seed(seed, "policy-delta-full-profile")
    full = _policies(schema, shifted_seed)["hashed_dense"]
    return {
        "single_hand_root_swap": (root_single, 0),
        "single_hand_deepest_swap": (deep_single, deepest),
        "all_hands_deepest_node_swap": (deep_all, deepest),
        "single_seat_three_all_nodes_swap": (seat_all, None),
        "full_hashed_dense_seed_shift": (full, None),
    }


def _aggregate_cache_bytes(caches: tuple[PolicyDeltaTTCache, ...]) -> int:
    trains: dict[int, TensorTrain] = {}
    arrays: dict[int, np.ndarray] = {}
    for cache in caches:
        for train in cache.node_trains:
            trains.setdefault(id(train), train)
        for values in cache.probabilities:
            if values is not None:
                arrays.setdefault(id(values), values)
        for values in (
            cache.node_bounds,
            cache.local_discarded_bounds,
            cache.parents,
            cache.depths,
        ):
            arrays.setdefault(id(values), values)
    return sum(train.storage_bytes for train in trains.values()) + sum(
        values.nbytes for values in arrays.values()
    )


def _new_tt_bytes(
    baseline: PolicyDeltaTTCache,
    candidate: PolicyDeltaTTCache,
) -> int:
    trains: dict[int, TensorTrain] = {}
    for old, new in zip(baseline.node_trains, candidate.node_trains, strict=True):
        if old is not new:
            trains.setdefault(id(new), new)
    return sum(train.storage_bytes for train in trains.values())


def run_policy_delta_tt_audit(config: dict[str, Any]) -> dict[str, Any]:
    """Execute the frozen ADR-0069 fixed-belief, varying-policy workload."""

    parsed = parse_policy_delta_tt_config(config)
    started = time.perf_counter()
    board = parse_cards(*parsed["board"])
    payoff_span = parsed["pot"] + parsed["players"] * parsed["bet_size"]
    terminal_rows: list[dict[str, object]] = []
    baseline_rows: list[dict[str, object]] = []
    candidate_player_rows: list[dict[str, object]] = []
    candidate_summaries: list[dict[str, object]] = []
    amortization_rows: list[dict[str, object]] = []
    zero_sum_rows: list[dict[str, object]] = []

    for hand_count in parsed["hands_per_player"]:
        for family in parsed["range_families"]:
            axis_seed = _derived_seed(
                parsed["seed"],
                "policy-delta-tt-axis",
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
            mixture, unaries = _raw_factors(
                hands_by_player=axes,
                components=parsed["mixture_components"],
                seed=axis_seed,
                family=family,
            )
            belief = FactorizedCardBelief(
                hands_by_player=axes,
                mixture_weights=mixture,
                unary_weights=unaries,
                board=board,
            )
            materialized = belief.materialize()
            layout = representative_public_tree(
                belief,
                pot=parsed["pot"],
                stack=parsed["stack"],
                bet_size=parsed["bet_size"],
            )
            if layout.public_node_count != 385:
                raise ValueError("public-policy topology differs from ADR-0069")
            groups = _terminal_groups(layout)
            if len(groups) != 64:
                raise ValueError("terminal payoff groups differ from ADR-0069")
            schema = information_schema_for_axes(layout, axes)
            baseline_policy = _policies(schema, axis_seed)[parsed["baseline_policy"]]
            candidates = _candidate_policies(
                layout=layout,
                hands_by_player=axes,
                schema=schema,
                baseline=baseline_policy,
                seed=axis_seed,
            )
            rank_codes = _rank_codes(board, axes)
            topology = FactorTTTopology.compile(belief, split_index=3)
            workspace = FactorTTBeliefWorkspace.compile(
                topology,
                belief,
                query_chunk_records=parsed["query_chunk_records"],
            )

            terminal_dense_by_player: list[dict[str, np.ndarray]] = []
            terminal_trains_by_player: list[dict[str, TensorTrain]] = []
            terminal_bounds_by_player: list[dict[str, float]] = []
            for player in parsed["target_players"]:
                dense, trains, bounds, summary = _terminal_library(
                    groups=groups,
                    rank_codes=rank_codes,
                    player=player,
                    pot=parsed["pot"],
                    bet_size=parsed["bet_size"],
                    tolerance=parsed["terminal_relative_tolerance"],
                )
                terminal_dense_by_player.append(dense)
                terminal_trains_by_player.append(trains)
                terminal_bounds_by_player.append(bounds)
                terminal_rows.append(
                    {
                        "hands_per_player": hand_count,
                        "family": family,
                        **summary,
                    }
                )

            probability_started = time.perf_counter()
            baseline_probabilities = compile_policy_probability_tape(
                layout,
                axes,
                baseline_policy,
            )
            baseline_probability_ms = (time.perf_counter() - probability_started) * 1000.0
            policy_probability_bytes = sum(
                values.nbytes for values in baseline_probabilities if values is not None
            )

            baseline_caches: list[PolicyDeltaTTCache] = []
            baseline_exact_utilities: list[float] = []
            baseline_estimated_utilities: list[float] = []
            baseline_compile_times: list[float] = []
            baseline_bounds: list[float] = []
            machine_noise = 0.0
            for player in parsed["target_players"]:
                compile_started = time.perf_counter()
                cache = compile_policy_delta_tt_cache_from_probabilities(
                    layout,
                    axes,
                    baseline_probabilities,
                    terminal_trains_by_player[player],
                    terminal_bounds_by_player[player],
                    relative_tolerance=parsed["node_relative_tolerance"],
                    maximum_rank=parsed["maximum_rank"],
                )
                compile_ms = (time.perf_counter() - compile_started) * 1000.0
                machine_noise = (
                    np.finfo(np.float64).eps
                    * 256.0
                    * cache.public_depth
                    * payoff_span
                )
                dense_started = time.perf_counter()
                dense_root = dense_public_policy_root(
                    layout,
                    axes,
                    baseline_policy,
                    terminal_dense_by_player[player],
                )
                dense_ms = (time.perf_counter() - dense_started) * 1000.0
                reconstructed = cache.root.to_dense()
                root_error = float(np.max(np.abs(reconstructed - dense_root)))
                estimated = workspace.contract(cache.root).expectation
                exact = _explicit_expectation(materialized, dense_root)
                violation = max(0.0, root_error - (cache.root_bound + machine_noise))
                baseline_caches.append(cache)
                baseline_exact_utilities.append(exact)
                baseline_estimated_utilities.append(estimated)
                baseline_compile_times.append(compile_ms)
                baseline_bounds.append(cache.root_bound)
                baseline_rows.append(
                    {
                        "hands_per_player": hand_count,
                        "family": family,
                        "player": player,
                        "baseline_probability_compile_ms_shared": baseline_probability_ms,
                        "cache_compile_ms": compile_ms,
                        "dense_oracle_ms": dense_ms,
                        "cache_numeric_bytes_per_player": cache.numeric_bytes,
                        "root_tt_bytes": cache.root.storage_bytes,
                        "root_middle_rank": cache.root.ranks[3],
                        "root_bound": cache.root_bound,
                        "machine_noise_allowance": machine_noise,
                        "actual_root_error": root_error,
                        "positive_bound_violation": violation,
                        "estimated_utility": estimated,
                        "exact_utility": exact,
                        "utility_error": abs(estimated - exact),
                    }
                )
            baseline_cache_tuple = tuple(baseline_caches)
            baseline_cache_bytes = _aggregate_cache_bytes(baseline_cache_tuple)
            baseline_zero_sum = abs(sum(baseline_estimated_utilities))
            baseline_zero_envelope = sum(baseline_bounds) + 6.0 * machine_noise
            zero_sum_rows.append(
                {
                    "hands_per_player": hand_count,
                    "family": family,
                    "policy": "baseline",
                    "players_present": len(baseline_estimated_utilities),
                    "estimated_zero_sum_residual": baseline_zero_sum,
                    "exact_zero_sum_residual": abs(sum(baseline_exact_utilities)),
                    "zero_sum_envelope": baseline_zero_envelope,
                    "positive_zero_sum_bound_violation": max(
                        0.0,
                        baseline_zero_sum - baseline_zero_envelope,
                    ),
                }
            )

            for mutation in parsed["candidate_mutations"]:
                candidate_policy, target_node = candidates[mutation]
                probability_started = time.perf_counter()
                candidate_probabilities = compile_policy_probability_tape(
                    layout,
                    axes,
                    candidate_policy,
                )
                candidate_probability_ms = (
                    time.perf_counter() - probability_started
                ) * 1000.0
                plan_started = time.perf_counter()
                plan = plan_policy_delta_tt_from_probabilities(
                    baseline_caches[0],
                    candidate_probabilities,
                )
                plan_ms = (time.perf_counter() - plan_started) * 1000.0
                path_exact: bool | None = None
                if mutation in _ONE_NODE_MUTATIONS:
                    assert target_node is not None
                    expected_path = ancestor_closure(
                        baseline_caches[0].parents,
                        (target_node,),
                    )
                    path_exact = (
                        plan.changed_policy_nodes == (target_node,)
                        and plan.dirty_nodes == expected_path
                    )

                candidate_caches: list[PolicyDeltaTTCache] = []
                candidate_estimated_utilities: list[float] = []
                candidate_exact_utilities: list[float] = []
                candidate_bounds: list[float] = []
                incremental_times: list[float] = []
                cold_times: list[float] = []
                false_certificates = 0
                positive_certificates = 0
                negative_certificates = 0
                abstentions = 0
                for player in parsed["target_players"]:
                    incremental_started = time.perf_counter()
                    recomposition = apply_policy_delta_tt_plan(
                        baseline_caches[player],
                        plan,
                    )
                    incremental_ms = (
                        time.perf_counter() - incremental_started
                    ) * 1000.0
                    candidate_cache = recomposition.cache

                    cold_started = time.perf_counter()
                    cold_cache = compile_policy_delta_tt_cache_from_probabilities(
                        layout,
                        axes,
                        candidate_probabilities,
                        terminal_trains_by_player[player],
                        terminal_bounds_by_player[player],
                        relative_tolerance=parsed["node_relative_tolerance"],
                        maximum_rank=parsed["maximum_rank"],
                    )
                    cold_ms = (time.perf_counter() - cold_started) * 1000.0

                    dense_started = time.perf_counter()
                    dense_root = dense_public_policy_root(
                        layout,
                        axes,
                        candidate_policy,
                        terminal_dense_by_player[player],
                    )
                    dense_ms = (time.perf_counter() - dense_started) * 1000.0
                    incremental_dense = candidate_cache.root.to_dense()
                    cold_dense = cold_cache.root.to_dense()
                    incremental_vs_cold = float(
                        np.max(np.abs(incremental_dense - cold_dense))
                    )
                    actual_root_error = float(
                        np.max(np.abs(incremental_dense - dense_root))
                    )
                    estimated = workspace.contract(candidate_cache.root).expectation
                    exact = _explicit_expectation(materialized, dense_root)
                    utility_error = abs(estimated - exact)
                    bound_violation = max(
                        0.0,
                        actual_root_error - (candidate_cache.root_bound + machine_noise),
                    )
                    estimated_delta = estimated - baseline_estimated_utilities[player]
                    exact_delta = exact - baseline_exact_utilities[player]
                    guard = (
                        baseline_bounds[player]
                        + candidate_cache.root_bound
                        + machine_noise
                        + 1e-10 * payoff_span
                    )
                    certificate = "abstain"
                    false_certificate = False
                    if estimated_delta > guard:
                        certificate = "positive"
                        positive_certificates += 1
                        false_certificate = exact_delta <= 0.0
                    elif estimated_delta < -guard:
                        certificate = "negative"
                        negative_certificates += 1
                        false_certificate = exact_delta >= 0.0
                    else:
                        abstentions += 1
                    false_certificates += int(false_certificate)

                    candidate_caches.append(candidate_cache)
                    candidate_estimated_utilities.append(estimated)
                    candidate_exact_utilities.append(exact)
                    candidate_bounds.append(candidate_cache.root_bound)
                    incremental_times.append(incremental_ms)
                    cold_times.append(cold_ms)
                    candidate_player_rows.append(
                        {
                            "hands_per_player": hand_count,
                            "family": family,
                            "mutation": mutation,
                            "player": player,
                            "changed_policy_nodes": len(plan.changed_policy_nodes),
                            "dirty_nodes": len(plan.dirty_nodes),
                            "recomputed_strategic_nodes": (
                                recomposition.recomputed_strategic_nodes
                            ),
                            "reused_node_train_objects": (
                                recomposition.reused_node_train_objects
                            ),
                            "candidate_probability_compile_ms_shared": (
                                candidate_probability_ms
                            ),
                            "dirty_plan_ms_shared": plan_ms,
                            "incremental_recomposition_ms": incremental_ms,
                            "cold_recomposition_ms": cold_ms,
                            "dense_oracle_ms": dense_ms,
                            "incremental_vs_cold_root_error": incremental_vs_cold,
                            "incremental_vs_dense_root_error": actual_root_error,
                            "incremental_vs_dense_utility_error": utility_error,
                            "root_bound": candidate_cache.root_bound,
                            "machine_noise_allowance": machine_noise,
                            "positive_bound_violation": bound_violation,
                            "estimated_utility": estimated,
                            "exact_utility": exact,
                            "estimated_delta_from_baseline": estimated_delta,
                            "exact_delta_from_baseline": exact_delta,
                            "acceptance_guard": guard,
                            "guarded_sign_certificate": certificate,
                            "false_guarded_sign_certificate": false_certificate,
                            "root_middle_rank": candidate_cache.root.ranks[3],
                            "candidate_cache_numeric_bytes_per_player": (
                                candidate_cache.numeric_bytes
                            ),
                            "incremental_new_tt_bytes": _new_tt_bytes(
                                baseline_caches[player],
                                candidate_cache,
                            ),
                        }
                    )

                candidate_cache_tuple = tuple(candidate_caches)
                total_incremental = sum(incremental_times)
                total_cold = sum(cold_times)
                total_baseline_compile = sum(baseline_compile_times)
                estimated_zero_sum = abs(sum(candidate_estimated_utilities))
                zero_sum_envelope = sum(candidate_bounds) + 6.0 * machine_noise
                zero_sum_rows.append(
                    {
                        "hands_per_player": hand_count,
                        "family": family,
                        "policy": mutation,
                        "players_present": len(candidate_estimated_utilities),
                        "estimated_zero_sum_residual": estimated_zero_sum,
                        "exact_zero_sum_residual": abs(sum(candidate_exact_utilities)),
                        "zero_sum_envelope": zero_sum_envelope,
                        "positive_zero_sum_bound_violation": max(
                            0.0,
                            estimated_zero_sum - zero_sum_envelope,
                        ),
                    }
                )
                summary = {
                    "hands_per_player": hand_count,
                    "family": family,
                    "mutation": mutation,
                    "target_node": target_node,
                    "single_node_ancestor_path_exact": path_exact,
                    "changed_policy_nodes": len(plan.changed_policy_nodes),
                    "dirty_nodes": len(plan.dirty_nodes),
                    "dirty_fraction": len(plan.dirty_nodes) / layout.public_node_count,
                    "baseline_probability_compile_ms_shared": baseline_probability_ms,
                    "candidate_probability_compile_ms_shared": candidate_probability_ms,
                    "dirty_plan_ms_shared": plan_ms,
                    "aggregate_incremental_recomposition_ms": total_incremental,
                    "aggregate_cold_recomposition_ms": total_cold,
                    "aggregate_baseline_cache_compile_ms": total_baseline_compile,
                    "raw_composition_speedup": total_cold / total_incremental,
                    "baseline_cache_numeric_bytes_all_players": baseline_cache_bytes,
                    "candidate_cache_numeric_bytes_all_players": (
                        _aggregate_cache_bytes(candidate_cache_tuple)
                    ),
                    "simultaneous_baseline_candidate_numeric_bytes": (
                        _aggregate_cache_bytes(
                            (*baseline_cache_tuple, *candidate_cache_tuple)
                        )
                    ),
                    "shared_policy_probability_bytes": policy_probability_bytes,
                    "positive_certificates": positive_certificates,
                    "negative_certificates": negative_certificates,
                    "abstentions": abstentions,
                    "false_certificates": false_certificates,
                    "estimated_zero_sum_residual": estimated_zero_sum,
                    "zero_sum_envelope": zero_sum_envelope,
                }
                candidate_summaries.append(summary)
                for reuse in parsed["amortized_reuse_counts"]:
                    amortized = total_incremental + total_baseline_compile / reuse
                    amortization_rows.append(
                        {
                            "hands_per_player": hand_count,
                            "family": family,
                            "mutation": mutation,
                            "reuse_count": reuse,
                            "amortized_incremental_ms": amortized,
                            "cold_recomposition_ms": total_cold,
                            "amortized_speedup": total_cold / amortized,
                            "strictly_faster": amortized < total_cold,
                        }
                    )

    expected_geometries = len(parsed["hands_per_player"]) * len(parsed["range_families"])
    expected_baselines = expected_geometries * parsed["players"]
    expected_candidates = expected_geometries * len(parsed["candidate_mutations"])
    expected_player_rows = expected_candidates * parsed["players"]
    if (
        len(terminal_rows) != expected_baselines
        or len(baseline_rows) != expected_baselines
        or len(candidate_summaries) != expected_candidates
        or len(candidate_player_rows) != expected_player_rows
        or len(amortization_rows)
        != expected_candidates * len(parsed["amortized_reuse_counts"])
        or len(zero_sum_rows) != expected_geometries * (1 + len(parsed["candidate_mutations"]))
    ):
        raise AssertionError("policy-delta TT row counts differ from ADR-0069")

    maximum_incremental_cold = max(
        float(row["incremental_vs_cold_root_error"])
        for row in candidate_player_rows
    )
    maximum_utility_error = max(
        float(row["incremental_vs_dense_utility_error"])
        for row in candidate_player_rows
    )
    maximum_bound_violation = max(
        *(
            float(row["positive_bound_violation"])
            for row in baseline_rows
        ),
        *(
            float(row["positive_bound_violation"])
            for row in candidate_player_rows
        ),
    )
    maximum_zero_sum_violation = max(
        float(row["positive_zero_sum_bound_violation"])
        for row in zero_sum_rows
    )
    false_certificates = sum(
        int(bool(row["false_guarded_sign_certificate"]))
        for row in candidate_player_rows
    )
    one_node_exact = all(
        row["single_node_ancestor_path_exact"] is True
        for row in candidate_summaries
        if row["mutation"] in _ONE_NODE_MUTATIONS
    )
    single_seat_reuse_four = [
        row
        for row in amortization_rows
        if row["mutation"] == "single_seat_three_all_nodes_swap"
        and row["reuse_count"] == 4
    ]
    pooled_single_seat_amortized = sum(
        float(row["amortized_incremental_ms"])
        for row in single_seat_reuse_four
    )
    pooled_single_seat_cold = sum(
        float(row["cold_recomposition_ms"])
        for row in single_seat_reuse_four
    )
    all_six_present = all(
        row["players_present"] == 6 for row in zero_sum_rows
    )
    gates = parsed["gates"]
    gate_results = {
        "incremental_cold_root_identity": (
            maximum_incremental_cold
            <= gates["maximum_incremental_vs_cold_root_error"]
        ),
        "incremental_dense_utility_identity": (
            maximum_utility_error
            <= gates["maximum_incremental_vs_dense_utility_error"]
        ),
        "truncation_plus_machine_bound": (
            maximum_bound_violation <= gates["maximum_positive_bound_violation"]
        ),
        "six_player_zero_sum_bound": (
            maximum_zero_sum_violation
            <= gates["maximum_zero_sum_bound_violation"]
        ),
        "zero_false_guarded_sign_certificates": (
            false_certificates
            <= gates["maximum_false_guarded_sign_certificates"]
        ),
        "single_node_ancestor_path_only": (
            one_node_exact
            if gates["require_single_node_ancestor_path_only"]
            else True
        ),
        "single_seat_four_reuse_amortized_speedup": (
            pooled_single_seat_amortized < pooled_single_seat_cold
            if gates["require_single_seat_four_reuse_amortized_speedup"]
            else True
        ),
        "all_six_player_zero_sum_diagnostic": (
            all_six_present
            if gates["require_all_six_player_zero_sum_diagnostic"]
            else True
        ),
    }
    certificate_count = sum(
        int(row["guarded_sign_certificate"] != "abstain")
        for row in candidate_player_rows
    )
    return {
        "schema_version": 1,
        "experiment_type": "guarded_incremental_policy_delta_tensor_train_audit",
        "status": "preregistered_revealed_engineering_audit_only",
        "config": parsed,
        "config_sha256": _sha256(
            _ROOT
            / "experiments"
            / "configs"
            / "policy-delta-tt-recomposition-audit-v1.json"
        ),
        "environment": environment_metadata(),
        "counts": {
            "terminal_rows": len(terminal_rows),
            "baseline_rows": len(baseline_rows),
            "candidate_player_rows": len(candidate_player_rows),
            "candidate_summaries": len(candidate_summaries),
            "amortization_rows": len(amortization_rows),
            "zero_sum_rows": len(zero_sum_rows),
            "guarded_sign_certificates": certificate_count,
            "guarded_abstentions": len(candidate_player_rows) - certificate_count,
            "false_guarded_sign_certificates": false_certificates,
        },
        "certificate_scope": {
            "quantity": "per_seat_fixed_policy_expected_utility_delta_only",
            "authorizes": "sign_of_the_audited_fixed_policy_delta_when_guard_clears",
            "does_not_authorize": (
                "best_response_pareto_coalition_nashconv_or_equilibrium_acceptance"
            ),
            "upper_bound_constraints": (
                "require_a_separate_sign_flipped_guarded_inequality_audit"
            ),
        },
        "aggregate": {
            "maximum_incremental_vs_cold_root_error": maximum_incremental_cold,
            "maximum_incremental_vs_dense_utility_error": maximum_utility_error,
            "maximum_positive_bound_violation": maximum_bound_violation,
            "maximum_zero_sum_bound_violation": maximum_zero_sum_violation,
            "pooled_single_seat_four_reuse_amortized_ms": (
                pooled_single_seat_amortized
            ),
            "pooled_single_seat_cold_ms": pooled_single_seat_cold,
            "pooled_single_seat_four_reuse_speedup": (
                pooled_single_seat_cold / pooled_single_seat_amortized
            ),
            "maximum_baseline_cache_numeric_bytes_all_players": max(
                int(row["baseline_cache_numeric_bytes_all_players"])
                for row in candidate_summaries
            ),
            "maximum_simultaneous_baseline_candidate_numeric_bytes": max(
                int(row["simultaneous_baseline_candidate_numeric_bytes"])
                for row in candidate_summaries
            ),
        },
        "gates": {"results": gate_results, "passed": all(gate_results.values())},
        "timing": {"wall_seconds": time.perf_counter() - started},
        "terminal_rows": terminal_rows,
        "baseline_rows": baseline_rows,
        "candidate_player_rows": candidate_player_rows,
        "candidate_summaries": candidate_summaries,
        "amortization_rows": amortization_rows,
        "zero_sum_rows": zero_sum_rows,
        "limitations": [
            (
                "The Float64 allowance is a frozen engineering margin, not a "
                "formal backward-error proof."
            ),
            (
                "Its four/seven-hand validation does not certify constant-multiplier "
                "extrapolation to 32-hand axes."
            ),
            (
                "Zero-sum residual is a mandatory scale-time health alarm but cannot "
                "certify errors that cancel across seats."
            ),
            "Dense terminal tensors and dense root oracles limit this audit to four/seven hands.",
            "Python composition timings establish algorithmic locality, not production latency.",
            (
                "Guarded fixed-policy value signs do not certify multiplayer "
                "equilibrium exploitability."
            ),
            "The capped/compressed ADR-0068 arm remains excluded from acceptance authority.",
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
    result = run_policy_delta_tt_audit(config)
    rendered = json.dumps(result, indent=2, sort_keys=True, allow_nan=False)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(
        "policy-delta TT: "
        f"candidate_rows={result['counts']['candidate_player_rows']}, "
        f"certificates={result['counts']['guarded_sign_certificates']}, "
        f"speedup={result['aggregate']['pooled_single_seat_four_reuse_speedup']:.3f}x, "
        f"passed={result['gates']['passed']}, "
        f"wall={result['timing']['wall_seconds']:.3f}s"
    )
    if args.output is not None:
        print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
