"""Audit real-policy TT rank and clean-fringe candidate-read economics."""

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

from .batched_factor_tt_contraction import contract_weighted_sum
from .clean_fringe_tt import (
    compile_clean_fringe_plan,
    compile_clean_fringe_delta_terms,
)
from .evaluation import Policy
from .factor_tt_contraction import FactorTTBeliefWorkspace, FactorTTTopology
from .factorized_belief import FactorizedCardBelief
from .factorized_belief_audit import _derived_seed, _raw_factors, generate_hand_axes
from .incremental_policy_tt import (
    PolicyDeltaTTCache,
    apply_policy_delta_tt_plan,
    compile_policy_probability_tape,
    plan_policy_delta_tt_from_probabilities,
)
from .profiled_policy_tt import profile_policy_delta_tt_cache_from_probabilities
from .public_policy_tt import (
    dense_public_policy_root,
    information_schema_for_axes,
    representative_public_tree,
)
from .real_policy import mean_policy_total_variation, policy_digest
from .reporting import environment_metadata
from .river import format_card, parse_cards
from .seat_order_tt import (
    screen_six_seat_orders,
    transpose_seat_tensor,
    unordered_three_three_partitions,
)
from .showdown_value_rank_screen import (
    _game_from_belief,
    _payoff_operator,
    _policies,
    _rank_codes,
    _terminal_groups,
)
from .structured_showdown_automaton import build_structured_showdown_automaton
from .tensor_train import TensorTrain

_ROOT = Path(__file__).parents[2]
_SOURCE_ARTIFACT = _ROOT / "experiments" / "results" / "real-policy-source-v1.json"
_FAMILIES = ("balanced", "blocker_heavy")
_TARGET_PLAYERS = (0, 3, 5)
_CONTROLS = ("uniform", "hashed_dense", "hashed_pure")
_RANK_CAPS = (8, 16, 32)
_REUSE_COUNTS = (1, 2, 4, 8, 16, 32, 64)
_SOURCE_PATHS = {
    "expected_public_tree_tensor_sha256": _ROOT / "src" / "pontius" / "public_tree_tensor.py",
    "expected_factorized_belief_sha256": _ROOT / "src" / "pontius" / "factorized_belief.py",
    "expected_factor_tt_contraction_sha256": _ROOT / "src" / "pontius" / "factor_tt_contraction.py",
    "expected_batched_factor_tt_contraction_sha256": _ROOT / "src" / "pontius" / "batched_factor_tt_contraction.py",
    "expected_incremental_policy_tt_sha256": _ROOT / "src" / "pontius" / "incremental_policy_tt.py",
    "expected_profiled_policy_tt_sha256": _ROOT / "src" / "pontius" / "profiled_policy_tt.py",
    "expected_clean_fringe_tt_sha256": _ROOT / "src" / "pontius" / "clean_fringe_tt.py",
    "expected_public_policy_tt_sha256": _ROOT / "src" / "pontius" / "public_policy_tt.py",
    "expected_real_policy_sha256": _ROOT / "src" / "pontius" / "real_policy.py",
    "expected_seat_order_tt_sha256": _ROOT / "src" / "pontius" / "seat_order_tt.py",
    "expected_structured_showdown_sha256": _ROOT / "src" / "pontius" / "structured_showdown_automaton.py",
    "expected_tensor_train_sha256": _ROOT / "src" / "pontius" / "tensor_train.py",
    "expected_tensor_train_algebra_sha256": _ROOT / "src" / "pontius" / "tensor_train_algebra.py",
    "expected_audit_implementation_sha256": _ROOT / "src" / "pontius" / "real_policy_representation_audit.py",
}


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required frozen artifact is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _policy_from_json(values: object) -> Policy:
    if not isinstance(values, dict):
        raise ValueError("serialized policy must be an object")
    return {
        str(key): {
            str(action): float(probability)
            for action, probability in distribution.items()
        }
        for key, distribution in values.items()
    }


def _flat_expected_utilities(layout: Any, policy: Policy) -> tuple[float, ...]:
    """Use the frozen evaluator's prepared-policy path without mutating it."""

    return tuple(
        float(value)
        for value in layout._expected_utilities(layout._prepare_policy(policy))
    )


def _train_digest(train: TensorTrain) -> str:
    digest = hashlib.sha256()
    digest.update(repr(train.shape).encode("ascii"))
    for core in train.cores:
        digest.update(repr(core.shape).encode("ascii"))
        digest.update(core.tobytes(order="C"))
    return digest.hexdigest()


def _structured_terminal_library(
    *,
    layout: Any,
    axes: tuple[tuple[tuple[int, int], ...], ...],
    board: tuple[int, ...],
    player: int,
    pot: float,
    bet_size: float,
) -> tuple[dict[str, np.ndarray], dict[str, TensorTrain], dict[str, float], dict[str, object]]:
    groups = _terminal_groups(layout)
    codes = tuple(np.ascontiguousarray(row, dtype=np.int32) for row in _rank_codes(board, axes))
    rank_matrix = np.ascontiguousarray(codes, dtype=np.int32)
    dense: dict[str, np.ndarray] = {}
    trains: dict[str, TensorTrain] = {}
    bounds: dict[str, float] = {}
    train_by_digest: dict[str, TensorTrain] = {}
    maximum_error = 0.0
    maximum_rank = 1
    production_compile_ms = 0.0
    audit_control_ms = 0.0
    for group in groups:
        production_started = time.perf_counter()
        automaton = build_structured_showdown_automaton(
            strength_codes=codes,
            contenders=group.contenders,
            target_player=player,
            contributed=group.contributed,
            pot=pot,
            bet_size=bet_size,
        )
        supplied = automaton.to_tensor_train()
        production_compile_ms += (time.perf_counter() - production_started) * 1000.0

        audit_started = time.perf_counter()
        values = automaton.to_dense()
        literal = _payoff_operator(
            group=group,
            rank_codes=rank_matrix,
            pot=pot,
            bet_size=bet_size,
        )[player]
        maximum_error = max(maximum_error, float(np.max(np.abs(values - literal))))
        digest = _train_digest(supplied)
        canonical = train_by_digest.setdefault(digest, supplied)
        if float(np.max(np.abs(canonical.to_dense() - values))) > 1e-12:
            raise AssertionError("structured terminal digest alias is not exact")
        dense[group.key] = values
        trains[group.key] = canonical
        bounds[group.key] = 0.0
        maximum_rank = max(maximum_rank, *canonical.ranks)
        audit_control_ms += (time.perf_counter() - audit_started) * 1000.0
    return dense, trains, bounds, {
        "player": player,
        "terminal_groups": len(groups),
        "deduplicated_trains": len(train_by_digest),
        "maximum_terminal_error": maximum_error,
        "maximum_terminal_rank": maximum_rank,
        "terminal_train_bytes": sum(train.storage_bytes for train in train_by_digest.values()),
        "production_compile_ms": production_compile_ms,
        "audit_control_ms": audit_control_ms,
    }


def _reorder_belief(
    belief: FactorizedCardBelief,
    order: tuple[int, ...],
) -> FactorizedCardBelief:
    if tuple(sorted(order)) != tuple(range(belief.num_players)):
        raise ValueError("belief order must be a seat permutation")
    return FactorizedCardBelief(
        hands_by_player=tuple(belief.hands_by_player[seat] for seat in order),
        mixture_weights=belief.mixture_weights,
        unary_weights=tuple(belief.unary_weights[seat] for seat in order),
        board=belief.board,
    )


def _splice_seat(
    layout: Any,
    baseline: Policy,
    donor: Policy,
    seat: int,
) -> Policy:
    result = {key: dict(row) for key, row in baseline.items()}
    for node in layout.nodes:
        if node.player != seat:
            continue
        for key in (
            candidate
            for candidate in result
            if f"|p{seat}|" in candidate
            and candidate.endswith(
                "history=root" if not node.history else "history=" + "/".join(
                    f"p{actor}:{action}" for actor, action in node.history
                )
            )
        ):
            result[key] = dict(donor[key])
    return dict(sorted(result.items()))


def _interpolate_seat(
    layout: Any,
    baseline: Policy,
    donor: Policy,
    seat: int,
    scale: float,
) -> Policy:
    if not 0.0 < scale <= 1.0:
        raise ValueError("policy interpolation scale must lie in (0, 1]")
    result = {key: dict(row) for key, row in baseline.items()}
    donor_seat = _splice_seat(layout, baseline, donor, seat)
    for key in result:
        if f"|p{seat}|" not in key:
            continue
        result[key] = {
            action: baseline[key][action]
            + scale * (donor_seat[key][action] - baseline[key][action])
            for action in baseline[key]
        }
    return dict(sorted(result.items()))


def _depth_rank_histogram(cache: PolicyDeltaTTCache, split_index: int) -> list[dict[str, object]]:
    rows = []
    for depth in sorted(set(int(value) for value in cache.depths)):
        ranks = [
            train.ranks[split_index]
            for node_index, train in enumerate(cache.node_trains)
            if int(cache.depths[node_index]) == depth
        ]
        rows.append(
            {
                "depth": depth,
                "nodes": len(ranks),
                "minimum_middle_rank": min(ranks),
                "median_middle_rank": median(ranks),
                "maximum_middle_rank": max(ranks),
            }
        )
    return rows


def _rank_specs(
    *,
    geometry: dict[str, object],
    controls: dict[str, Policy],
) -> list[dict[str, object]]:
    specs: list[dict[str, object]] = []
    for name in _CONTROLS:
        for player in _TARGET_PLAYERS:
            specs.append(
                {
                    "policy_name": name,
                    "provenance": "control",
                    "checkpoint": None,
                    "policy": controls[name],
                    "player": player,
                }
            )
    profiles = geometry["profiles"]
    assert isinstance(profiles, list)
    for profile in profiles:
        provenance = profile["provenance"]
        policy = _policy_from_json(profile["policy"])
        if policy_digest(policy) != profile["policy_sha256"]:
            raise ValueError("source profile policy digest is corrupt")
        if provenance["kind"] == "dcfr_average":
            for player in _TARGET_PLAYERS:
                specs.append(
                    {
                        "policy_name": profile["profile_id"],
                        "provenance": "dcfr_average",
                        "checkpoint": provenance["checkpoint"],
                        "policy": policy,
                        "player": player,
                    }
                )
        elif provenance["kind"] == "literal_unilateral_best_response":
            specs.append(
                {
                    "policy_name": profile["profile_id"],
                    "provenance": "literal_unilateral_best_response",
                    "checkpoint": provenance["against_checkpoint"],
                    "policy": policy,
                    "player": provenance["target_player"],
                }
            )
    return specs


def _candidate_specs(
    layout: Any,
    geometry: dict[str, object],
) -> list[dict[str, object]]:
    profiles = geometry["profiles"]
    assert isinstance(profiles, list)
    averages = {
        int(profile["provenance"]["checkpoint"]): _policy_from_json(profile["policy"])
        for profile in profiles
        if profile["provenance"]["kind"] == "dcfr_average"
    }
    responses = [
        profile
        for profile in profiles
        if profile["provenance"]["kind"] == "literal_unilateral_best_response"
    ]
    specs = []
    checkpoints = tuple(sorted(averages))
    for left, right in zip(checkpoints[:-1], checkpoints[1:], strict=True):
        for seat in range(layout.num_players):
            candidate = _splice_seat(layout, averages[left], averages[right], seat)
            specs.append(
                {
                    "candidate_name": f"checkpoint_{left}_to_{right}|seat={seat}",
                    "candidate_kind": "consecutive_checkpoint_single_seat",
                    "seat": seat,
                    "baseline_checkpoint": left,
                    "donor_checkpoint": right,
                    "baseline": averages[left],
                    "candidate": candidate,
                }
            )
    baseline = averages[16]
    for profile in responses:
        target = int(profile["provenance"]["target_player"])
        specs.append(
            {
                "candidate_name": f"literal_br_against_16|seat={target}",
                "candidate_kind": "literal_unilateral_best_response",
                "seat": target,
                "baseline_checkpoint": 16,
                "donor_checkpoint": None,
                "baseline": baseline,
                "candidate": _policy_from_json(profile["policy"]),
            }
        )
    if int(geometry["hands_per_player"]) == 4 and geometry["range_family"] == "balanced":
        for name, scale in (("below", 1e-12), ("above", 1e-6)):
            specs.append(
                {
                    "candidate_name": f"synthetic_guard_{name}|seat=3|scale={scale:.0e}",
                    "candidate_kind": f"synthetic_guard_{name}",
                    "seat": 3,
                    "baseline_checkpoint": 16,
                    "donor_checkpoint": 64,
                    "synthetic_scale": scale,
                    "baseline": averages[16],
                    "candidate": _interpolate_seat(
                        layout, averages[16], averages[64], 3, scale
                    ),
                }
            )
    return specs


def _median_timed(function: Any, *, warmups: int, repeats: int) -> tuple[float, object]:
    result = None
    for _ in range(warmups):
        result = function()
    timings = []
    for _ in range(repeats):
        started = time.perf_counter()
        result = function()
        timings.append((time.perf_counter() - started) * 1000.0)
    return float(median(timings)), result


def run_real_policy_representation_audit(config: dict[str, Any]) -> dict[str, object]:
    """Run a preregistered rank and three-evaluator policy-candidate audit."""

    parsed = parse_real_policy_representation_config(config)
    if _sha256(_SOURCE_ARTIFACT) != parsed["expected_source_artifact_sha256"]:
        raise ValueError("canonical source policy artifact SHA-256 mismatch")
    source = json.loads(_SOURCE_ARTIFACT.read_text(encoding="utf-8"))
    started = time.perf_counter()
    board = parse_cards(*parsed["board"])
    rank_rows: list[dict[str, object]] = []
    partition_rows: list[dict[str, object]] = []
    cap_rows: list[dict[str, object]] = []
    candidate_rows: list[dict[str, object]] = []
    bill_rows: list[dict[str, object]] = []
    terminal_rows: list[dict[str, object]] = []
    geometry_rows: list[dict[str, object]] = []

    for source_geometry in source["geometries"]:
        hand_count = int(source_geometry["hands_per_player"])
        family = str(source_geometry["range_family"])
        axis_seed = _derived_seed(parsed["seed"], "public-policy-root-axis", hand_count, family)
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
        expected_axes = [
            [[format_card(hand[0]), format_card(hand[1])] for hand in hands]
            for hands in belief.hands_by_player
        ]
        if expected_axes != source_geometry["hand_axes"]:
            raise ValueError("source artifact hand axes do not reproduce")

        topology_started = time.perf_counter()
        layout = representative_public_tree(
            belief,
            pot=parsed["pot"],
            stack=parsed["stack"],
            bet_size=parsed["bet_size"],
        )
        topology_layout_ms = (time.perf_counter() - topology_started) * 1000.0
        schema = information_schema_for_axes(layout, belief.hands_by_player)
        controls = _policies(schema, axis_seed)

        flat_started = time.perf_counter()
        game = _game_from_belief(
            belief=belief,
            pot=parsed["pot"],
            stack=parsed["stack"],
            bet_size=parsed["bet_size"],
        )
        from .public_tree_tensor import PublicTreeTensorEvaluator

        flat = PublicTreeTensorEvaluator(game)
        flat_compile_ms = (time.perf_counter() - flat_started) * 1000.0
        if game.provenance_digest != source_geometry["game_provenance_digest"]:
            raise ValueError("source artifact game provenance does not reproduce")

        terminal_dense: list[dict[str, np.ndarray]] = []
        terminal_trains: list[dict[str, TensorTrain]] = []
        terminal_bounds: list[dict[str, float]] = []
        terminal_compile_ms = 0.0
        for player in range(parsed["players"]):
            dense, trains, bounds, summary = _structured_terminal_library(
                layout=layout,
                axes=belief.hands_by_player,
                board=board,
                player=player,
                pot=parsed["pot"],
                bet_size=parsed["bet_size"],
            )
            terminal_dense.append(dense)
            terminal_trains.append(trains)
            terminal_bounds.append(bounds)
            terminal_compile_ms += float(summary["production_compile_ms"])
            terminal_rows.append(
                {"hands_per_player": hand_count, "family": family, **summary}
            )

        factor_topology_started = time.perf_counter()
        topology = FactorTTTopology.compile(
            belief, split_index=parsed["split_index"]
        )
        factor_topology_compile_ms = (
            time.perf_counter() - factor_topology_started
        ) * 1000.0
        workspace_started = time.perf_counter()
        workspace = FactorTTBeliefWorkspace.compile(
            topology, belief, query_chunk_records=parsed["query_chunk_records"]
        )
        workspace_compile_ms = (time.perf_counter() - workspace_started) * 1000.0
        reordered_workspaces: dict[tuple[int, ...], FactorTTBeliefWorkspace] = {}
        probability_cache: dict[str, tuple[object, float]] = {}
        value_cache: dict[tuple[str, int], tuple[PolicyDeltaTTCache, np.ndarray, float]] = {}

        def probability_tape(policy: Policy) -> tuple[object, float]:
            digest = policy_digest(policy)
            retained = probability_cache.get(digest)
            if retained is None:
                tape_started = time.perf_counter()
                tape = compile_policy_probability_tape(layout, belief.hands_by_player, policy)
                retained = (tape, (time.perf_counter() - tape_started) * 1000.0)
                probability_cache[digest] = retained
            return retained

        def player_cache(policy: Policy, player: int) -> tuple[PolicyDeltaTTCache, np.ndarray, float]:
            digest = policy_digest(policy)
            key = (digest, player)
            retained = value_cache.get(key)
            if retained is None:
                tape, _ = probability_tape(policy)
                compile_started = time.perf_counter()
                profiled = profile_policy_delta_tt_cache_from_probabilities(
                    layout,
                    belief.hands_by_player,
                    tape,  # type: ignore[arg-type]
                    terminal_trains[player],
                    terminal_bounds[player],
                    relative_tolerance=parsed["node_relative_tolerance"],
                    maximum_rank=None,
                )
                retained = (
                    profiled.cache,
                    profiled.node_compose_ms,
                    (time.perf_counter() - compile_started) * 1000.0,
                )
                value_cache[key] = retained
            return retained

        specs = _rank_specs(geometry=source_geometry, controls=controls)
        for spec in specs:
            policy = spec["policy"]
            assert isinstance(policy, dict)
            player = int(spec["player"])
            cache, _, cache_compile_ms = player_cache(policy, player)
            dense_started = time.perf_counter()
            dense_root = dense_public_policy_root(
                layout, belief.hands_by_player, policy, terminal_dense[player]
            )
            dense_ms = (time.perf_counter() - dense_started) * 1000.0
            cache_root_error = float(np.max(np.abs(cache.root.to_dense() - dense_root)))
            order_started = time.perf_counter()
            order_screen = screen_six_seat_orders(
                dense_root,
                first_halves=unordered_three_three_partitions(),
                relative_threshold=parsed["numerical_rank_relative_threshold"],
            )
            order_ms = (time.perf_counter() - order_started) * 1000.0
            selected_dense = transpose_seat_tensor(dense_root, order_screen.selected.order)
            exact_selected = TensorTrain.from_dense(selected_dense)
            selected_error = float(
                np.max(np.abs(exact_selected.to_dense() - selected_dense))
            )
            rank_id = len(rank_rows)
            rank_rows.append(
                {
                    "rank_id": rank_id,
                    "hands_per_player": hand_count,
                    "family": family,
                    "policy_name": spec["policy_name"],
                    "provenance": spec["provenance"],
                    "checkpoint": spec["checkpoint"],
                    "player": player,
                    "dense_root_bytes": dense_root.nbytes,
                    "dense_root_ms": dense_ms,
                    "cache_compile_ms": cache_compile_ms,
                    "order_screen_ms": order_ms,
                    "original_root_ranks": cache.root.ranks,
                    "original_root_middle_rank": cache.root.ranks[parsed["split_index"]],
                    "original_root_bytes": cache.root.storage_bytes,
                    "cache_root_error": cache_root_error,
                    "selected_order": order_screen.selected.order,
                    "selected_numerical_ranks": order_screen.selected.numerical_ranks,
                    "selected_middle_rank": order_screen.selected.middle_rank,
                    "selected_exact_storage_bytes": order_screen.selected.estimated_storage_bytes,
                    "selected_exact_root_error": selected_error,
                    "maximum_partition_singular_value_relative_error": (
                        order_screen.maximum_partition_singular_value_relative_error
                    ),
                    "crown_depth_rank_histogram": _depth_rank_histogram(
                        cache, parsed["split_index"]
                    ),
                }
            )
            for candidate in order_screen.partition_best:
                partition_rows.append(
                    {
                        "rank_id": rank_id,
                        "first_half": candidate.first_half,
                        "selected_order": candidate.order,
                        "middle_rank": candidate.middle_rank,
                        "numerical_ranks": candidate.numerical_ranks,
                        "estimated_storage_bytes": candidate.estimated_storage_bytes,
                    }
                )
            order = order_screen.selected.order
            reordered_workspace = reordered_workspaces.get(order)
            if reordered_workspace is None:
                reordered = _reorder_belief(belief, order)
                reordered_workspace = FactorTTBeliefWorkspace.compile(
                    FactorTTTopology.compile(reordered, split_index=parsed["split_index"]),
                    reordered,
                    query_chunk_records=parsed["query_chunk_records"],
                )
                reordered_workspaces[order] = reordered_workspace
            exact_utility = _flat_expected_utilities(flat, policy)[player]
            for cap in parsed["rank_caps"]:
                cap_started = time.perf_counter()
                capped = TensorTrain.from_dense(selected_dense, maximum_rank=cap)
                estimate = reordered_workspace.contract(capped).expectation
                cap_ms = (time.perf_counter() - cap_started) * 1000.0
                normalized_error = abs(estimate - exact_utility) / parsed["payoff_span"]
                storage_ratio = capped.storage_bytes / dense_root.nbytes
                cap_rows.append(
                    {
                        "rank_id": rank_id,
                        "rank_cap": cap,
                        "actual_ranks": capped.ranks,
                        "middle_rank": capped.ranks[parsed["split_index"]],
                        "storage_bytes": capped.storage_bytes,
                        "storage_ratio": storage_ratio,
                        "estimated_utility": estimate,
                        "exact_utility": exact_utility,
                        "normalized_utility_error": normalized_error,
                        "compile_and_contract_ms": cap_ms,
                        "safe_value_product": (
                            normalized_error <= parsed["maximum_safe_normalized_utility_error"]
                            and storage_ratio <= parsed["maximum_safe_storage_ratio"]
                        ),
                    }
                )

        candidates = _candidate_specs(layout, source_geometry)
        for candidate_spec in candidates:
            baseline = candidate_spec["baseline"]
            candidate = candidate_spec["candidate"]
            assert isinstance(baseline, dict) and isinstance(candidate, dict)
            baseline_tape, baseline_probability_ms = probability_tape(baseline)
            caches = [player_cache(baseline, player) for player in range(parsed["players"])]
            candidate_tape_started = time.perf_counter()
            candidate_tape = compile_policy_probability_tape(
                layout, belief.hands_by_player, candidate
            )
            candidate_probability_ms = (time.perf_counter() - candidate_tape_started) * 1000.0
            plan_started = time.perf_counter()
            policy_plan = plan_policy_delta_tt_from_probabilities(
                caches[0][0], candidate_tape
            )
            dirty_plan_ms = (time.perf_counter() - plan_started) * 1000.0
            fringe_started = time.perf_counter()
            fringe_plan = compile_clean_fringe_plan(caches[0][0], policy_plan)
            fringe_plan_ms = (time.perf_counter() - fringe_started) * 1000.0
            baseline_oracle_started = time.perf_counter()
            baseline_exact = _flat_expected_utilities(flat, baseline)
            audit_baseline_oracle_ms = (
                time.perf_counter() - baseline_oracle_started
            ) * 1000.0

            def clean_evaluate() -> tuple[tuple[float, ...], tuple[object, ...]]:
                deltas = []
                diagnostics = []
                for cache, _, _ in caches:
                    delta = compile_clean_fringe_delta_terms(
                        cache,
                        fringe_plan,
                        belief_components=belief.component_count,
                        split_index=parsed["split_index"],
                    )
                    contraction = (
                        None
                        if not delta.terms
                        else contract_weighted_sum(
                            workspace,
                            delta.terms,
                            maximum_feature_width_per_batch=parsed[
                                "maximum_feature_width_per_batch"
                            ],
                        )
                    )
                    change = 0.0 if contraction is None else contraction.expectation
                    deltas.append(change)
                    diagnostics.append((delta, contraction))
                return tuple(deltas), tuple(diagnostics)

            def recompose_evaluate() -> tuple[float, ...]:
                values = []
                for cache, _, _ in caches:
                    recomposed = apply_policy_delta_tt_plan(cache, policy_plan).cache
                    values.append(workspace.contract(recomposed.root).expectation)
                return tuple(values)

            clean_ms, clean_result = _median_timed(
                clean_evaluate,
                warmups=parsed["timing_warmups"],
                repeats=parsed["timing_repeats"],
            )
            recompose_ms, recompose_result = _median_timed(
                recompose_evaluate,
                warmups=parsed["timing_warmups"],
                repeats=parsed["timing_repeats"],
            )
            flat_ms, exact_result = _median_timed(
                lambda: _flat_expected_utilities(flat, candidate),
                warmups=parsed["timing_warmups"],
                repeats=parsed["timing_repeats"],
            )
            clean_deltas, clean_diagnostics = clean_result  # type: ignore[misc]
            recompose_values = recompose_result  # type: ignore[assignment]
            exact_values = exact_result  # type: ignore[assignment]
            machine_noise = (
                np.finfo(np.float64).eps
                * 256.0
                * caches[0][0].public_depth
                * parsed["payoff_span"]
            )
            exact_deltas = tuple(
                float(exact) - float(baseline)
                for exact, baseline in zip(
                    exact_values, baseline_exact, strict=True
                )
            )
            clean_errors = [
                abs(float(estimate) - float(exact))
                for estimate, exact in zip(clean_deltas, exact_deltas, strict=True)
            ]
            recompose_errors = [
                abs(float(estimate) - float(exact))
                for estimate, exact in zip(recompose_values, exact_values, strict=True)
            ]
            bounds = [
                diagnostic[0].shared_fringe_error_bound
                for diagnostic in clean_diagnostics
            ]
            violations = [
                max(0.0, error - bound - machine_noise)
                for error, bound in zip(clean_errors, bounds, strict=True)
            ]
            guard = parsed["fixed_policy_sign_guard"] * parsed["payoff_span"]
            false_certificates = 0
            certificates = []
            for player in range(parsed["players"]):
                estimated_delta = clean_deltas[player]
                exact_delta = exact_deltas[player]
                threshold = bounds[player] + machine_noise + guard
                certificate = 1 if estimated_delta > threshold else -1 if estimated_delta < -threshold else 0
                false_certificates += int(
                    certificate != 0
                    and (exact_delta == 0.0 or math.copysign(1.0, exact_delta) != certificate)
                )
                certificates.append(certificate)
            total_node_ms = sum(float(np.sum(row[1])) for row in caches)
            dirty_node_ms = sum(
                float(np.sum(row[1][list(policy_plan.dirty_nodes)]))
                for row in caches
            )
            baseline_cache_compile_ms = sum(row[2] for row in caches)
            clean_marginal_ms = (
                candidate_probability_ms + dirty_plan_ms + fringe_plan_ms + clean_ms
            )
            recompose_marginal_ms = candidate_probability_ms + dirty_plan_ms + recompose_ms
            tt_compile_ms = (
                topology_layout_ms
                + factor_topology_compile_ms
                + terminal_compile_ms
                + workspace_compile_ms
                + float(baseline_probability_ms)
                + baseline_cache_compile_ms
            )
            candidate_row_id = len(candidate_rows)
            candidate_rows.append(
                {
                    "candidate_row_id": candidate_row_id,
                    "hands_per_player": hand_count,
                    "family": family,
                    "candidate_name": candidate_spec["candidate_name"],
                    "candidate_kind": candidate_spec["candidate_kind"],
                    "seat": candidate_spec["seat"],
                    "baseline_checkpoint": candidate_spec["baseline_checkpoint"],
                    "donor_checkpoint": candidate_spec["donor_checkpoint"],
                    "synthetic_scale": candidate_spec.get("synthetic_scale"),
                    "mean_policy_total_variation": mean_policy_total_variation(baseline, candidate),
                    "changed_policy_nodes": len(policy_plan.changed_policy_nodes),
                    "dirty_nodes": len(policy_plan.dirty_nodes),
                    "dirty_node_fraction": len(policy_plan.dirty_nodes) / layout.public_node_count,
                    "cost_weighted_dirty_fraction": dirty_node_ms / total_node_ms if total_node_ms else 0.0,
                    "frontier_nodes": len(fringe_plan.frontier_nodes),
                    "delta_support_frontier_nodes": len(fringe_plan.delta_support_frontier_nodes),
                    "frontier_rank_histograms": [
                        diagnostic[0].frontier_middle_ranks
                        for diagnostic in clean_diagnostics
                    ],
                    "total_batched_feature_width_all_players": sum(
                        diagnostic[0].total_component_rank_width
                        for diagnostic in clean_diagnostics
                    ),
                    "total_referenced_frontier_tt_bytes_all_players": sum(
                        diagnostic[0].referenced_tt_storage_bytes
                        for diagnostic in clean_diagnostics
                    ),
                    "total_reach_factor_bytes_all_players": sum(
                        diagnostic[0].reach_factor_numeric_bytes
                        for diagnostic in clean_diagnostics
                    ),
                    "total_streaming_batches_all_players": sum(
                        0 if diagnostic[1] is None else diagnostic[1].batches
                        for diagnostic in clean_diagnostics
                    ),
                    "maximum_streaming_batch_scratch_bytes": max(
                        0
                        if diagnostic[1] is None
                        else diagnostic[1].estimated_peak_batch_scratch_bytes
                        for diagnostic in clean_diagnostics
                    ),
                    "candidate_probability_compile_ms": candidate_probability_ms,
                    "audit_baseline_oracle_ms_unbilled": audit_baseline_oracle_ms,
                    "dirty_plan_ms": dirty_plan_ms,
                    "fringe_plan_ms": fringe_plan_ms,
                    "clean_core_ms": clean_ms,
                    "clean_marginal_ms": clean_marginal_ms,
                    "recompose_core_ms": recompose_ms,
                    "recompose_marginal_ms": recompose_marginal_ms,
                    "flat_marginal_ms": flat_ms,
                    "maximum_clean_utility_error": max(clean_errors),
                    "maximum_recompose_utility_error": max(recompose_errors),
                    "maximum_positive_fringe_bound_violation": max(violations),
                    "estimated_zero_sum_delta_residual": abs(sum(clean_deltas)),
                    "zero_sum_envelope": sum(bounds) + parsed["players"] * machine_noise,
                    "positive_zero_sum_bound_violation": max(
                        0.0,
                        abs(sum(clean_deltas))
                        - sum(bounds)
                        - parsed["players"] * machine_noise,
                    ),
                    "certificates": certificates,
                    "false_certificates": false_certificates,
                    "tt_compile_ms": tt_compile_ms,
                    "flat_compile_ms": flat_compile_ms,
                }
            )
            for reuse in parsed["reuse_counts"]:
                bill_rows.append(
                    {
                        "candidate_row_id": candidate_row_id,
                        "reuse_count": reuse,
                        "clean_charged_ms": clean_marginal_ms + tt_compile_ms / reuse,
                        "recompose_charged_ms": recompose_marginal_ms + tt_compile_ms / reuse,
                        "flat_charged_ms": flat_ms + flat_compile_ms / reuse,
                    }
                )

        geometry_rows.append(
            {
                "hands_per_player": hand_count,
                "family": family,
                "joint_deals": flat.deal_count,
                "topology_layout_compile_ms": topology_layout_ms,
                "factor_topology_compile_ms": factor_topology_compile_ms,
                "flat_layout_compile_ms": flat_compile_ms,
                "terminal_compile_ms_all_players": terminal_compile_ms,
                "workspace_compile_ms": workspace_compile_ms,
                "workspace_numeric_bytes": workspace.numeric_bytes,
                "topology_numeric_bytes": topology.numeric_bytes,
                "cached_policy_tapes": len(probability_cache),
                "cached_player_value_caches": len(value_cache),
            }
        )

    gates = parsed["gates"]
    latest = {4: 256, 7: 64}
    late_rank_ids = {
        int(row["rank_id"])
        for row in rank_rows
        if row["provenance"] == "dcfr_average"
        and row["checkpoint"] == latest[int(row["hands_per_player"])]
    }
    safe_late = all(
        any(
            cap["rank_id"] == rank_id
            and cap["rank_cap"] <= parsed["maximum_safe_rank_cap"]
            and cap["safe_value_product"]
            for cap in cap_rows
        )
        for rank_id in late_rank_ids
    )
    gate_results = {
        "structured_terminal_identity": max(float(row["maximum_terminal_error"]) for row in terminal_rows)
        <= gates["maximum_structured_terminal_error"],
        "cache_root_identity": max(float(row["cache_root_error"]) for row in rank_rows)
        <= gates["maximum_cache_root_error"],
        "selected_order_exact_identity": max(float(row["selected_exact_root_error"]) for row in rank_rows)
        <= gates["maximum_selected_order_exact_error"],
        "partition_spectrum_identity": max(float(row["maximum_partition_singular_value_relative_error"]) for row in rank_rows)
        <= gates["maximum_partition_spectrum_error"],
        "clean_fringe_utility_identity": max(float(row["maximum_clean_utility_error"]) for row in candidate_rows)
        <= gates["maximum_clean_fringe_utility_error"],
        "recompose_utility_identity": max(float(row["maximum_recompose_utility_error"]) for row in candidate_rows)
        <= gates["maximum_recompose_utility_error"],
        "fringe_bound_conservative": max(float(row["maximum_positive_fringe_bound_violation"]) for row in candidate_rows)
        <= gates["maximum_positive_fringe_bound_violation"],
        "zero_sum_bound_conservative": max(float(row["positive_zero_sum_bound_violation"]) for row in candidate_rows)
        <= gates["maximum_positive_zero_sum_bound_violation"],
        "no_false_fixed_policy_sign_certificates": sum(int(row["false_certificates"]) for row in candidate_rows)
        <= gates["maximum_false_fixed_policy_sign_certificates"],
        "latest_average_has_safe_capped_product": safe_late,
        "synthetic_below_guard_abstains": all(
            all(int(value) == 0 for value in row["certificates"])
            for row in candidate_rows
            if row["candidate_kind"] == "synthetic_guard_below"
        ) and sum(row["candidate_kind"] == "synthetic_guard_below" for row in candidate_rows) == 1,
        "synthetic_above_guard_certifies": any(
            any(int(value) != 0 for value in row["certificates"])
            for row in candidate_rows
            if row["candidate_kind"] == "synthetic_guard_above"
        ) and sum(row["candidate_kind"] == "synthetic_guard_above" for row in candidate_rows) == 1,
        "all_rank_partition_rows": len(partition_rows) == len(rank_rows) * 10,
        "all_candidate_bill_rows": len(bill_rows) == len(candidate_rows) * len(parsed["reuse_counts"]),
    }
    return {
        "schema_version": 1,
        "experiment_type": "real_policy_representation_and_clean_fringe_audit",
        "status": "preregistered_revealed_engineering_audit_only",
        "config": parsed,
        "config_sha256": _sha256(
            _ROOT / "experiments" / "configs" / "real-policy-representation-audit-v1.json"
        ),
        "implementation_sha256": _sha256(
            _ROOT / "src" / "pontius" / "real_policy_representation_audit.py"
        ),
        "source_artifact_sha256": _sha256(_SOURCE_ARTIFACT),
        "environment": environment_metadata(),
        "counts": {
            "rank_rows": len(rank_rows),
            "partition_rows": len(partition_rows),
            "cap_rows": len(cap_rows),
            "candidate_rows": len(candidate_rows),
            "bill_rows": len(bill_rows),
        },
        "aggregate": {
            "maximum_structured_terminal_error": max(float(row["maximum_terminal_error"]) for row in terminal_rows),
            "maximum_cache_root_error": max(float(row["cache_root_error"]) for row in rank_rows),
            "maximum_selected_order_exact_error": max(float(row["selected_exact_root_error"]) for row in rank_rows),
            "maximum_clean_fringe_utility_error": max(float(row["maximum_clean_utility_error"]) for row in candidate_rows),
            "maximum_recompose_utility_error": max(float(row["maximum_recompose_utility_error"]) for row in candidate_rows),
            "maximum_positive_fringe_bound_violation": max(float(row["maximum_positive_fringe_bound_violation"]) for row in candidate_rows),
            "maximum_positive_zero_sum_bound_violation": max(float(row["positive_zero_sum_bound_violation"]) for row in candidate_rows),
            "false_fixed_policy_sign_certificates": sum(int(row["false_certificates"]) for row in candidate_rows),
            "late_average_safe_capped_product": safe_late,
        },
        "gates": {"results": gate_results, "passed": all(gate_results.values())},
        "timing": {"wall_seconds": time.perf_counter() - started},
        "geometry_rows": geometry_rows,
        "terminal_rows": terminal_rows,
        "rank_rows": rank_rows,
        "partition_rows": partition_rows,
        "cap_rows": cap_rows,
        "candidate_rows": candidate_rows,
        "bill_rows": bill_rows,
        "limitations": [
            "All acceptance certificates cover fixed-policy utility deltas only, never best-response or NashConv quantities.",
            "The exact incumbent utility used to form audit-control deltas is ground truth only and is excluded from every online evaluator bill.",
            "The Python clean-fringe prototype batches frontier terms per value seat, not all six value seats in one native pass.",
            "No small-axis speed result authorizes a 32-hand online path.",
            "Per-node timing instrumentation is a noisy cost attribution diagnostic, not a portable CPU model.",
            "Source policies remain finite selected-axis six-player DCFR objects without a multiplayer convergence guarantee.",
        ],
    }


def parse_real_policy_representation_config(config: dict[str, Any]) -> dict[str, Any]:
    """Strictly validate the frozen ADR-0076 configuration."""

    required = {
        "evidence_stage", "seed", "expected_source_artifact_sha256", "board",
        "pot", "stack", "bet_size", "payoff_span", "players", "hands_per_player",
        "range_families", "mixture_components", "rank_target_players", "control_policies",
        "rank_caps", "split_index", "numerical_rank_relative_threshold",
        "node_relative_tolerance", "maximum_safe_normalized_utility_error",
        "maximum_safe_storage_ratio", "maximum_safe_rank_cap", "query_chunk_records",
        "timing_warmups", "timing_repeats", "reuse_counts", "fixed_policy_sign_guard",
        "maximum_feature_width_per_batch", "gates",
        *_SOURCE_PATHS,
    }
    if set(config) != required:
        raise ValueError("real-policy representation config fields differ from ADR-0076")
    for field, path in _SOURCE_PATHS.items():
        if config[field] != _sha256(path):
            raise ValueError(f"frozen source hash mismatch for {field}")
    frozen = {
        "evidence_stage": "preregistered_revealed_engineering_audit",
        "seed": 20260819,
        "expected_source_artifact_sha256": "cdcae48dcca5fd1447fd5ad33426a4b20f04e098c88897d8f0f6eddb797ef36e",
        "board": ["2c", "7d", "9h", "Js", "Qc"],
        "pot": 12.0,
        "stack": 30.0,
        "bet_size": 3.0,
        "payoff_span": 30.0,
        "players": 6,
        "hands_per_player": [4, 7],
        "range_families": list(_FAMILIES),
        "mixture_components": 3,
        "rank_target_players": list(_TARGET_PLAYERS),
        "control_policies": list(_CONTROLS),
        "rank_caps": list(_RANK_CAPS),
        "split_index": 3,
        "numerical_rank_relative_threshold": 1e-12,
        "node_relative_tolerance": 1e-12,
        "maximum_safe_normalized_utility_error": 1e-4,
        "maximum_safe_storage_ratio": 0.25,
        "maximum_safe_rank_cap": 32,
        "query_chunk_records": 256,
        "timing_warmups": 1,
        "timing_repeats": 3,
        "reuse_counts": list(_REUSE_COUNTS),
        "fixed_policy_sign_guard": 1e-10,
        "maximum_feature_width_per_batch": 512,
    }
    if any(config[field] != value for field, value in frozen.items()):
        raise ValueError("real-policy representation contract differs from ADR-0076")
    gates = config["gates"]
    expected_gates = {
        "maximum_structured_terminal_error": 1e-12,
        "maximum_cache_root_error": 1e-8,
        "maximum_selected_order_exact_error": 1e-8,
        "maximum_partition_spectrum_error": 1e-10,
        "maximum_clean_fringe_utility_error": 1e-8,
        "maximum_recompose_utility_error": 1e-8,
        "maximum_positive_fringe_bound_violation": 0.0,
        "maximum_positive_zero_sum_bound_violation": 0.0,
        "maximum_false_fixed_policy_sign_certificates": 0,
    }
    if gates != expected_gates:
        raise ValueError("real-policy representation gates differ from ADR-0076")
    return {
        **config,
        "hands_per_player": tuple(config["hands_per_player"]),
        "range_families": tuple(config["range_families"]),
        "rank_target_players": tuple(config["rank_target_players"]),
        "control_policies": tuple(config["control_policies"]),
        "rank_caps": tuple(config["rank_caps"]),
        "reuse_counts": tuple(config["reuse_counts"]),
        "gates": dict(gates),
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    result = run_real_policy_representation_audit(config)
    rendered = json.dumps(result, indent=2, sort_keys=True, allow_nan=False)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered + "\n", encoding="utf-8")
    print(
        "real-policy representation: "
        f"ranks={result['counts']['rank_rows']}, "
        f"candidates={result['counts']['candidate_rows']}, "
        f"passed={result['gates']['passed']}, "
        f"wall={result['timing']['wall_seconds']:.3f}s"
    )
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
