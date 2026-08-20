"""Audit signed and rank-optimized clean-fringe policy-delta reads."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from statistics import median
import time
from typing import Any, Callable

import numpy as np

from .batched_factor_tt_contraction import (
    BatchedFactorTTContraction,
    contract_weighted_sum,
)
from .clean_fringe_tt import (
    CleanFringeDeltaTerms,
    compile_clean_fringe_delta_terms,
    compile_clean_fringe_plan,
)
from .factor_tt_contraction import FactorTTBeliefWorkspace, FactorTTTopology
from .factorized_belief_audit import _derived_seed, _raw_factors, generate_hand_axes
from .incremental_policy_tt import (
    PolicyDeltaTTCache,
    apply_policy_delta_tt_plan,
    compile_policy_probability_tape,
    plan_policy_delta_tt_from_probabilities,
)
from .profiled_policy_tt import profile_policy_delta_tt_cache_from_probabilities
from .public_policy_tt import representative_public_tree
from .real_policy import mean_policy_total_variation, policy_digest
from .real_policy_representation_audit import (
    _candidate_specs,
    _flat_expected_utilities,
    _game_from_belief,
    _median_timed,
    _policy_from_json,
    _structured_terminal_library,
)
from .real_policy_representation_audit_v2 import _canonicalized_factorized_belief
from .reporting import environment_metadata
from .river import format_card, parse_cards
from .signed_clean_fringe_tt import (
    ReachWeightedFringeBound,
    SignedCleanFringeDeltaTerms,
    compile_rank_optimized_clean_fringe_plan,
    compile_signed_clean_fringe_delta_terms,
    evaluate_reach_weighted_fringe_bound,
)
from .tensor_train import TensorTrain

_ROOT = Path(__file__).parents[2]
_CONFIG = _ROOT / "experiments" / "configs" / "signed-clean-fringe-audit-v1.json"
_SOURCE_ARTIFACT = _ROOT / "experiments" / "results" / "real-policy-source-v1.json"
_PREDECESSOR_ARTIFACT = (
    _ROOT / "experiments" / "results" / "real-policy-representation-audit-v2.json"
)
_IMPLEMENTATION = Path(__file__)
_FAMILIES = ("balanced", "blocker_heavy")
_REUSE_COUNTS = (1, 2, 4, 8, 16, 32, 64)
_TARGET_TRANSITIONS = ((4, 16), (16, 64))
_SOURCE_PATHS = {
    "expected_batched_factor_tt_contraction_sha256": (
        _ROOT / "src" / "pontius" / "batched_factor_tt_contraction.py"
    ),
    "expected_clean_fringe_tt_sha256": (
        _ROOT / "src" / "pontius" / "clean_fringe_tt.py"
    ),
    "expected_factor_tt_contraction_sha256": (
        _ROOT / "src" / "pontius" / "factor_tt_contraction.py"
    ),
    "expected_incremental_policy_tt_sha256": (
        _ROOT / "src" / "pontius" / "incremental_policy_tt.py"
    ),
    "expected_real_policy_representation_audit_sha256": (
        _ROOT / "src" / "pontius" / "real_policy_representation_audit.py"
    ),
    "expected_real_policy_representation_audit_v2_sha256": (
        _ROOT / "src" / "pontius" / "real_policy_representation_audit_v2.py"
    ),
    "expected_signed_clean_fringe_tt_sha256": (
        _ROOT / "src" / "pontius" / "signed_clean_fringe_tt.py"
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


def _time_once(function: Callable[[], Any]) -> tuple[float, Any]:
    started = time.perf_counter()
    result = function()
    return (time.perf_counter() - started) * 1000.0, result


def _contract_terms(
    workspace: FactorTTBeliefWorkspace,
    compiled: tuple[CleanFringeDeltaTerms | SignedCleanFringeDeltaTerms, ...],
    *,
    maximum_feature_width_per_batch: int,
) -> tuple[tuple[float, ...], tuple[BatchedFactorTTContraction | None, ...]]:
    values = []
    diagnostics = []
    for delta in compiled:
        contraction = (
            None
            if not delta.terms
            else contract_weighted_sum(
                workspace,
                delta.terms,
                maximum_feature_width_per_batch=maximum_feature_width_per_batch,
            )
        )
        values.append(0.0 if contraction is None else contraction.expectation)
        diagnostics.append(contraction)
    return tuple(values), tuple(diagnostics)


def _evaluate_bounds(
    workspace: FactorTTBeliefWorkspace,
    caches: tuple[PolicyDeltaTTCache, ...],
    compiled: tuple[SignedCleanFringeDeltaTerms, ...],
    *,
    maximum_feature_width_per_batch: int,
) -> tuple[ReachWeightedFringeBound, ...]:
    return tuple(
        evaluate_reach_weighted_fringe_bound(
            workspace,
            cache,
            delta,
            maximum_feature_width_per_batch=maximum_feature_width_per_batch,
        )
        for cache, delta in zip(caches, compiled, strict=True)
    )


def _maximum_scratch(
    diagnostics: tuple[BatchedFactorTTContraction | None, ...],
) -> int:
    return max(
        (
            0
            if diagnostic is None
            else diagnostic.estimated_peak_batch_scratch_bytes
            for diagnostic in diagnostics
        ),
        default=0,
    )


def _validate_profile_digests(geometry: dict[str, object]) -> None:
    profiles = geometry["profiles"]
    if not isinstance(profiles, list):
        raise ValueError("source geometry profiles must be a list")
    for profile in profiles:
        policy = _policy_from_json(profile["policy"])
        if policy_digest(policy) != profile["policy_sha256"]:
            raise ValueError("source profile policy digest is corrupt")


def run_signed_clean_fringe_audit(config: dict[str, Any]) -> dict[str, object]:
    """Run the frozen five-arm candidate-read audit on all source policies."""

    parsed = parse_signed_clean_fringe_config(config)
    if _sha256(_SOURCE_ARTIFACT) != parsed["expected_source_artifact_sha256"]:
        raise ValueError("canonical source artifact SHA-256 mismatch")
    if _sha256(_PREDECESSOR_ARTIFACT) != parsed[
        "expected_predecessor_artifact_sha256"
    ]:
        raise ValueError("ADR-0078 predecessor artifact SHA-256 mismatch")
    source = json.loads(_SOURCE_ARTIFACT.read_text(encoding="utf-8"))
    observed_geometries = {
        (int(row["hands_per_player"]), str(row["range_family"]))
        for row in source["geometries"]
    }
    expected_geometries = {
        (hands, family)
        for hands in parsed["hands_per_player"]
        for family in parsed["range_families"]
    }
    if observed_geometries != expected_geometries or len(source["geometries"]) != len(
        expected_geometries
    ):
        raise ValueError("canonical source geometry matrix differs from the freeze")
    started = time.perf_counter()
    board = parse_cards(*parsed["board"])
    candidate_rows: list[dict[str, object]] = []
    bill_rows: list[dict[str, object]] = []
    terminal_rows: list[dict[str, object]] = []
    geometry_rows: list[dict[str, object]] = []

    for source_geometry in source["geometries"]:
        hand_count = int(source_geometry["hands_per_player"])
        family = str(source_geometry["range_family"])
        _validate_profile_digests(source_geometry)
        axis_seed = _derived_seed(
            parsed["seed"], "public-policy-root-axis", hand_count, family
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
        belief = _canonicalized_factorized_belief(
            hands_by_player=axes,
            mixture_weights=mixture,
            unary_weights=unaries,
            board=board,
        )
        reproduced_axes = [
            [[format_card(hand[0]), format_card(hand[1])] for hand in hands]
            for hands in belief.hands_by_player
        ]
        if reproduced_axes != source_geometry["hand_axes"]:
            raise ValueError("source artifact hand axes do not reproduce")

        topology_layout_ms, layout = _time_once(
            lambda: representative_public_tree(
                belief,
                pot=parsed["pot"],
                stack=parsed["stack"],
                bet_size=parsed["bet_size"],
            )
        )
        flat_compile_ms, game = _time_once(
            lambda: _game_from_belief(
                belief=belief,
                pot=parsed["pot"],
                stack=parsed["stack"],
                bet_size=parsed["bet_size"],
            )
        )
        from .public_tree_tensor import PublicTreeTensorEvaluator

        flat_layout_started = time.perf_counter()
        flat = PublicTreeTensorEvaluator(game)
        flat_compile_ms += (time.perf_counter() - flat_layout_started) * 1000.0
        if game.provenance_digest != source_geometry["game_provenance_digest"]:
            raise ValueError("source artifact game provenance does not reproduce")

        terminal_trains: list[dict[str, TensorTrain]] = []
        terminal_bounds: list[dict[str, float]] = []
        terminal_compile_ms = 0.0
        for player in range(parsed["players"]):
            _, trains, bounds, summary = _structured_terminal_library(
                layout=layout,
                axes=belief.hands_by_player,
                board=board,
                player=player,
                pot=parsed["pot"],
                bet_size=parsed["bet_size"],
            )
            terminal_trains.append(trains)
            terminal_bounds.append(bounds)
            terminal_compile_ms += float(summary["production_compile_ms"])
            terminal_rows.append(
                {"hands_per_player": hand_count, "family": family, **summary}
            )

        factor_topology_ms, factor_topology = _time_once(
            lambda: FactorTTTopology.compile(
                belief, split_index=parsed["split_index"]
            )
        )
        workspace_ms, workspace = _time_once(
            lambda: FactorTTBeliefWorkspace.compile(
                factor_topology,
                belief,
                query_chunk_records=parsed["query_chunk_records"],
            )
        )
        probability_cache: dict[str, tuple[object, float]] = {}
        value_cache: dict[
            tuple[str, int], tuple[PolicyDeltaTTCache, np.ndarray, float]
        ] = {}

        def probability_tape(policy: dict[str, object]) -> tuple[object, float]:
            digest = policy_digest(policy)  # type: ignore[arg-type]
            retained = probability_cache.get(digest)
            if retained is None:
                compile_ms, tape = _time_once(
                    lambda: compile_policy_probability_tape(
                        layout,
                        belief.hands_by_player,
                        policy,  # type: ignore[arg-type]
                    )
                )
                retained = (tape, compile_ms)
                probability_cache[digest] = retained
            return retained

        def player_cache(
            policy: dict[str, object], player: int
        ) -> tuple[PolicyDeltaTTCache, np.ndarray, float]:
            digest = policy_digest(policy)  # type: ignore[arg-type]
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

        candidates = _candidate_specs(layout, source_geometry)
        for candidate_spec in candidates:
            baseline = candidate_spec["baseline"]
            candidate = candidate_spec["candidate"]
            if not isinstance(baseline, dict) or not isinstance(candidate, dict):
                raise ValueError("candidate policies must be mappings")
            baseline_tape, baseline_probability_ms = probability_tape(baseline)
            cache_rows = tuple(
                player_cache(baseline, player)
                for player in range(parsed["players"])
            )
            caches = tuple(row[0] for row in cache_rows)

            candidate_probability_ms, candidate_tape = _time_once(
                lambda: compile_policy_probability_tape(
                    layout, belief.hands_by_player, candidate
                )
            )
            dirty_plan_ms, policy_plan = _time_once(
                lambda: plan_policy_delta_tt_from_probabilities(
                    caches[0], candidate_tape
                )
            )
            immediate_plan_ms, immediate_plan = _time_once(
                lambda: compile_clean_fringe_plan(caches[0], policy_plan)
            )
            optimized_plan_ms, optimized = _time_once(
                lambda: compile_rank_optimized_clean_fringe_plan(
                    caches,
                    policy_plan,
                    belief_components=belief.component_count,
                    split_index=parsed["split_index"],
                )
            )

            two_compile_ms, two_compiled = _median_timed(
                lambda: tuple(
                    compile_clean_fringe_delta_terms(
                        cache,
                        immediate_plan,
                        belief_components=belief.component_count,
                        split_index=parsed["split_index"],
                    )
                    for cache in caches
                ),
                warmups=parsed["timing_warmups"],
                repeats=parsed["timing_repeats"],
            )
            signed_immediate_compile_ms, signed_immediate_compiled = _median_timed(
                lambda: tuple(
                    compile_signed_clean_fringe_delta_terms(
                        cache,
                        immediate_plan,
                        changed_modes=optimized.changed_reach_modes,
                        belief_components=belief.component_count,
                        split_index=parsed["split_index"],
                    )
                    for cache in caches
                ),
                warmups=parsed["timing_warmups"],
                repeats=parsed["timing_repeats"],
            )
            signed_optimized_compile_ms, signed_optimized_compiled = _median_timed(
                lambda: tuple(
                    compile_signed_clean_fringe_delta_terms(
                        cache,
                        optimized.optimized_plan,
                        changed_modes=optimized.changed_reach_modes,
                        belief_components=belief.component_count,
                        split_index=parsed["split_index"],
                    )
                    for cache in caches
                ),
                warmups=parsed["timing_warmups"],
                repeats=parsed["timing_repeats"],
            )
            two_compiled = two_compiled  # type: ignore[assignment]
            signed_immediate_compiled = signed_immediate_compiled  # type: ignore[assignment]
            signed_optimized_compiled = signed_optimized_compiled  # type: ignore[assignment]

            two_core_ms, two_result = _median_timed(
                lambda: _contract_terms(
                    workspace,
                    two_compiled,  # type: ignore[arg-type]
                    maximum_feature_width_per_batch=parsed[
                        "maximum_feature_width_per_batch"
                    ],
                ),
                warmups=parsed["timing_warmups"],
                repeats=parsed["timing_repeats"],
            )
            signed_immediate_core_ms, signed_immediate_result = _median_timed(
                lambda: _contract_terms(
                    workspace,
                    signed_immediate_compiled,  # type: ignore[arg-type]
                    maximum_feature_width_per_batch=parsed[
                        "maximum_feature_width_per_batch"
                    ],
                ),
                warmups=parsed["timing_warmups"],
                repeats=parsed["timing_repeats"],
            )
            signed_optimized_core_ms, signed_optimized_result = _median_timed(
                lambda: _contract_terms(
                    workspace,
                    signed_optimized_compiled,  # type: ignore[arg-type]
                    maximum_feature_width_per_batch=parsed[
                        "maximum_feature_width_per_batch"
                    ],
                ),
                warmups=parsed["timing_warmups"],
                repeats=parsed["timing_repeats"],
            )
            immediate_bound_ms, immediate_bound_result = _median_timed(
                lambda: _evaluate_bounds(
                    workspace,
                    caches,
                    signed_immediate_compiled,  # type: ignore[arg-type]
                    maximum_feature_width_per_batch=parsed[
                        "maximum_feature_width_per_batch"
                    ],
                ),
                warmups=parsed["timing_warmups"],
                repeats=parsed["timing_repeats"],
            )
            optimized_bound_ms, optimized_bound_result = _median_timed(
                lambda: _evaluate_bounds(
                    workspace,
                    caches,
                    signed_optimized_compiled,  # type: ignore[arg-type]
                    maximum_feature_width_per_batch=parsed[
                        "maximum_feature_width_per_batch"
                    ],
                ),
                warmups=parsed["timing_warmups"],
                repeats=parsed["timing_repeats"],
            )

            def recompose_evaluate() -> tuple[float, ...]:
                return tuple(
                    workspace.contract(
                        apply_policy_delta_tt_plan(cache, policy_plan).cache.root
                    ).expectation
                    for cache in caches
                )

            recompose_ms, recompose_values = _median_timed(
                recompose_evaluate,
                warmups=parsed["timing_warmups"],
                repeats=parsed["timing_repeats"],
            )
            flat_ms, exact_values = _median_timed(
                lambda: _flat_expected_utilities(flat, candidate),
                warmups=parsed["timing_warmups"],
                repeats=parsed["timing_repeats"],
            )
            baseline_oracle_ms, baseline_exact = _time_once(
                lambda: _flat_expected_utilities(flat, baseline)
            )

            two_deltas, two_diagnostics = two_result  # type: ignore[misc]
            signed_immediate_deltas, signed_immediate_diagnostics = (
                signed_immediate_result  # type: ignore[misc]
            )
            signed_optimized_deltas, signed_optimized_diagnostics = (
                signed_optimized_result  # type: ignore[misc]
            )
            immediate_bounds = immediate_bound_result  # type: ignore[assignment]
            optimized_bounds = optimized_bound_result  # type: ignore[assignment]
            exact_deltas = tuple(
                float(candidate_value) - float(baseline_value)
                for candidate_value, baseline_value in zip(
                    exact_values, baseline_exact, strict=True  # type: ignore[arg-type]
                )
            )
            machine_noise = (
                np.finfo(np.float64).eps
                * parsed["machine_noise_multiplier"]
                * caches[0].public_depth
                * parsed["payoff_span"]
            )

            def errors(values: tuple[float, ...]) -> tuple[float, ...]:
                return tuple(
                    abs(float(value) - exact)
                    for value, exact in zip(values, exact_deltas, strict=True)
                )

            two_errors = errors(two_deltas)
            signed_immediate_errors = errors(signed_immediate_deltas)
            signed_optimized_errors = errors(signed_optimized_deltas)
            recompose_errors = tuple(
                abs(float(value) - float(exact))
                for value, exact in zip(
                    recompose_values, exact_values, strict=True  # type: ignore[arg-type]
                )
            )
            immediate_bound_values = tuple(
                bound.upper_bound for bound in immediate_bounds
            )
            optimized_bound_values = tuple(
                bound.upper_bound for bound in optimized_bounds
            )
            immediate_violations = tuple(
                max(0.0, error - bound - machine_noise)
                for error, bound in zip(
                    signed_immediate_errors,
                    immediate_bound_values,
                    strict=True,
                )
            )
            optimized_violations = tuple(
                max(0.0, error - bound - machine_noise)
                for error, bound in zip(
                    signed_optimized_errors,
                    optimized_bound_values,
                    strict=True,
                )
            )
            legacy_bounds = tuple(
                delta.legacy_shared_fringe_error_bound
                for delta in signed_immediate_compiled  # type: ignore[union-attr]
            )
            bound_looseness_violations = tuple(
                max(0.0, bound - legacy - machine_noise)
                for bound, legacy in zip(
                    immediate_bound_values, legacy_bounds, strict=True
                )
            )
            guard = parsed["fixed_policy_sign_guard"] * parsed["payoff_span"]
            certificates = []
            false_certificates = 0
            for estimate, exact, bound in zip(
                signed_optimized_deltas,
                exact_deltas,
                optimized_bound_values,
                strict=True,
            ):
                threshold = bound + machine_noise + guard
                certificate = (
                    1
                    if estimate > threshold
                    else -1
                    if estimate < -threshold
                    else 0
                )
                false_certificates += int(
                    certificate != 0
                    and (
                        exact == 0.0
                        or math.copysign(1.0, exact) != certificate
                    )
                )
                certificates.append(certificate)

            total_node_ms = sum(float(np.sum(row[1])) for row in cache_rows)
            dirty_node_ms = sum(
                float(np.sum(row[1][list(policy_plan.dirty_nodes)]))
                for row in cache_rows
            )
            baseline_cache_compile_ms = sum(row[2] for row in cache_rows)
            tt_compile_ms = (
                topology_layout_ms
                + factor_topology_ms
                + terminal_compile_ms
                + workspace_ms
                + float(baseline_probability_ms)
                + baseline_cache_compile_ms
            )
            common_marginal_ms = candidate_probability_ms + dirty_plan_ms
            two_marginal_ms = (
                common_marginal_ms
                + immediate_plan_ms
                + two_compile_ms
                + two_core_ms
            )
            signed_immediate_marginal_ms = (
                common_marginal_ms
                + immediate_plan_ms
                + signed_immediate_compile_ms
                + signed_immediate_core_ms
                + immediate_bound_ms
            )
            signed_optimized_marginal_ms = (
                common_marginal_ms
                + optimized_plan_ms
                + signed_optimized_compile_ms
                + signed_optimized_core_ms
                + optimized_bound_ms
            )
            recompose_marginal_ms = common_marginal_ms + recompose_ms
            two_width = sum(
                delta.total_component_rank_width
                for delta in two_compiled  # type: ignore[union-attr]
            )
            signed_immediate_width = sum(
                delta.total_component_rank_width
                for delta in signed_immediate_compiled  # type: ignore[union-attr]
            )
            signed_optimized_width = sum(
                delta.total_component_rank_width
                for delta in signed_optimized_compiled  # type: ignore[union-attr]
            )
            if signed_immediate_width != (
                optimized.immediate_all_value_component_rank_width
            ):
                raise AssertionError("immediate signed width accounting diverged")
            if signed_optimized_width != (
                optimized.optimized_all_value_component_rank_width
            ):
                raise AssertionError("optimized signed width accounting diverged")

            target_customer = (
                hand_count == 7
                and candidate_spec["candidate_kind"]
                == "consecutive_checkpoint_single_seat"
                and (
                    int(candidate_spec["baseline_checkpoint"]),
                    int(candidate_spec["donor_checkpoint"]),
                )
                in parsed["target_checkpoint_transitions"]
            )
            row_id = len(candidate_rows)
            candidate_rows.append(
                {
                    "candidate_row_id": row_id,
                    "hands_per_player": hand_count,
                    "family": family,
                    "candidate_name": candidate_spec["candidate_name"],
                    "candidate_kind": candidate_spec["candidate_kind"],
                    "seat": candidate_spec["seat"],
                    "baseline_checkpoint": candidate_spec["baseline_checkpoint"],
                    "donor_checkpoint": candidate_spec["donor_checkpoint"],
                    "synthetic_scale": candidate_spec.get("synthetic_scale"),
                    "target_customer": target_customer,
                    "mean_policy_total_variation": mean_policy_total_variation(
                        baseline, candidate
                    ),
                    "changed_reach_modes": optimized.changed_reach_modes,
                    "changed_policy_nodes": len(policy_plan.changed_policy_nodes),
                    "dirty_nodes": len(policy_plan.dirty_nodes),
                    "dirty_node_fraction": (
                        len(policy_plan.dirty_nodes) / layout.public_node_count
                    ),
                    "cost_weighted_dirty_fraction": (
                        dirty_node_ms / total_node_ms if total_node_ms else 0.0
                    ),
                    "immediate_frontier_nodes": len(immediate_plan.frontier_nodes),
                    "immediate_support_frontier_nodes": len(
                        immediate_plan.delta_support_frontier_nodes
                    ),
                    "optimized_frontier_nodes": len(
                        optimized.optimized_plan.frontier_nodes
                    ),
                    "optimized_support_frontier_nodes": len(
                        optimized.optimized_plan.delta_support_frontier_nodes
                    ),
                    "expanded_clean_nodes": len(optimized.expanded_clean_nodes),
                    "two_sided_terms_all_players": sum(
                        len(delta.terms)
                        for delta in two_compiled  # type: ignore[union-attr]
                    ),
                    "signed_immediate_terms_all_players": sum(
                        len(delta.terms)
                        for delta in signed_immediate_compiled  # type: ignore[union-attr]
                    ),
                    "signed_optimized_terms_all_players": sum(
                        len(delta.terms)
                        for delta in signed_optimized_compiled  # type: ignore[union-attr]
                    ),
                    "two_sided_feature_width_all_players": two_width,
                    "signed_immediate_feature_width_all_players": (
                        signed_immediate_width
                    ),
                    "signed_optimized_feature_width_all_players": (
                        signed_optimized_width
                    ),
                    "optimized_to_immediate_width_ratio": (
                        signed_optimized_width / signed_immediate_width
                        if signed_immediate_width
                        else 0.0
                    ),
                    "immediate_frontier_rank_histograms": [
                        delta.frontier_middle_ranks
                        for delta in signed_immediate_compiled  # type: ignore[union-attr]
                    ],
                    "optimized_frontier_rank_histograms": [
                        delta.frontier_middle_ranks
                        for delta in signed_optimized_compiled  # type: ignore[union-attr]
                    ],
                    "immediate_weighted_bounds": immediate_bound_values,
                    "optimized_weighted_bounds": optimized_bound_values,
                    "legacy_immediate_bounds": legacy_bounds,
                    "maximum_positive_weighted_vs_legacy_violation": max(
                        bound_looseness_violations
                    ),
                    "maximum_two_sided_utility_error": max(two_errors),
                    "maximum_signed_immediate_utility_error": max(
                        signed_immediate_errors
                    ),
                    "maximum_signed_optimized_utility_error": max(
                        signed_optimized_errors
                    ),
                    "maximum_recompose_utility_error": max(recompose_errors),
                    "maximum_positive_immediate_bound_violation": max(
                        immediate_violations
                    ),
                    "maximum_positive_optimized_bound_violation": max(
                        optimized_violations
                    ),
                    "immediate_zero_sum_residual": abs(
                        sum(signed_immediate_deltas)
                    ),
                    "immediate_zero_sum_envelope": (
                        sum(immediate_bound_values)
                        + parsed["players"] * machine_noise
                    ),
                    "positive_immediate_zero_sum_bound_violation": max(
                        0.0,
                        abs(sum(signed_immediate_deltas))
                        - sum(immediate_bound_values)
                        - parsed["players"] * machine_noise,
                    ),
                    "optimized_zero_sum_residual": abs(
                        sum(signed_optimized_deltas)
                    ),
                    "optimized_zero_sum_envelope": (
                        sum(optimized_bound_values)
                        + parsed["players"] * machine_noise
                    ),
                    "positive_optimized_zero_sum_bound_violation": max(
                        0.0,
                        abs(sum(signed_optimized_deltas))
                        - sum(optimized_bound_values)
                        - parsed["players"] * machine_noise,
                    ),
                    "certificates": certificates,
                    "false_certificates": false_certificates,
                    "candidate_probability_compile_ms": candidate_probability_ms,
                    "dirty_plan_ms": dirty_plan_ms,
                    "immediate_plan_ms": immediate_plan_ms,
                    "optimized_plan_ms": optimized_plan_ms,
                    "two_sided_term_compile_ms": two_compile_ms,
                    "signed_immediate_term_compile_ms": (
                        signed_immediate_compile_ms
                    ),
                    "signed_optimized_term_compile_ms": (
                        signed_optimized_compile_ms
                    ),
                    "two_sided_core_ms": two_core_ms,
                    "signed_immediate_core_ms": signed_immediate_core_ms,
                    "signed_optimized_core_ms": signed_optimized_core_ms,
                    "immediate_bound_core_ms": immediate_bound_ms,
                    "optimized_bound_core_ms": optimized_bound_ms,
                    "recompose_core_ms": recompose_ms,
                    "flat_core_ms": flat_ms,
                    "two_sided_marginal_ms": two_marginal_ms,
                    "signed_immediate_certified_marginal_ms": (
                        signed_immediate_marginal_ms
                    ),
                    "signed_optimized_certified_marginal_ms": (
                        signed_optimized_marginal_ms
                    ),
                    "recompose_marginal_ms": recompose_marginal_ms,
                    "flat_marginal_ms": flat_ms,
                    "audit_baseline_oracle_ms_unbilled": baseline_oracle_ms,
                    "maximum_two_sided_batch_scratch_bytes": _maximum_scratch(
                        two_diagnostics
                    ),
                    "maximum_signed_immediate_batch_scratch_bytes": (
                        _maximum_scratch(signed_immediate_diagnostics)
                    ),
                    "maximum_signed_optimized_batch_scratch_bytes": (
                        _maximum_scratch(signed_optimized_diagnostics)
                    ),
                    "maximum_immediate_bound_batch_scratch_bytes": max(
                        bound.estimated_peak_batch_scratch_bytes
                        for bound in immediate_bounds
                    ),
                    "maximum_optimized_bound_batch_scratch_bytes": max(
                        bound.estimated_peak_batch_scratch_bytes
                        for bound in optimized_bounds
                    ),
                    "tt_compile_ms": tt_compile_ms,
                    "flat_compile_ms": flat_compile_ms,
                }
            )
            for reuse in parsed["reuse_counts"]:
                bill_rows.append(
                    {
                        "candidate_row_id": row_id,
                        "reuse_count": reuse,
                        "two_sided_charged_ms": (
                            two_marginal_ms + tt_compile_ms / reuse
                        ),
                        "signed_immediate_certified_charged_ms": (
                            signed_immediate_marginal_ms + tt_compile_ms / reuse
                        ),
                        "signed_optimized_certified_charged_ms": (
                            signed_optimized_marginal_ms + tt_compile_ms / reuse
                        ),
                        "recompose_charged_ms": (
                            recompose_marginal_ms + tt_compile_ms / reuse
                        ),
                        "flat_charged_ms": flat_ms + flat_compile_ms / reuse,
                    }
                )

        geometry_rows.append(
            {
                "hands_per_player": hand_count,
                "family": family,
                "joint_deals": flat.deal_count,
                "topology_layout_compile_ms": topology_layout_ms,
                "factor_topology_compile_ms": factor_topology_ms,
                "flat_compile_ms": flat_compile_ms,
                "terminal_compile_ms_all_players": terminal_compile_ms,
                "workspace_compile_ms": workspace_ms,
                "workspace_numeric_bytes": workspace.numeric_bytes,
                "factor_topology_numeric_bytes": factor_topology.numeric_bytes,
                "cached_policy_tapes": len(probability_cache),
                "cached_player_value_caches": len(value_cache),
            }
        )

    gates = parsed["gates"]
    target_rows = [row for row in candidate_rows if row["target_customer"]]
    target_speedup = sum(
        float(row["recompose_marginal_ms"]) for row in target_rows
    ) / sum(
        float(row["signed_optimized_certified_marginal_ms"])
        for row in target_rows
    )
    aggregate = {
        "maximum_structured_terminal_error": max(
            float(row["maximum_terminal_error"]) for row in terminal_rows
        ),
        "maximum_two_sided_utility_error": max(
            float(row["maximum_two_sided_utility_error"])
            for row in candidate_rows
        ),
        "maximum_signed_immediate_utility_error": max(
            float(row["maximum_signed_immediate_utility_error"])
            for row in candidate_rows
        ),
        "maximum_signed_optimized_utility_error": max(
            float(row["maximum_signed_optimized_utility_error"])
            for row in candidate_rows
        ),
        "maximum_recompose_utility_error": max(
            float(row["maximum_recompose_utility_error"])
            for row in candidate_rows
        ),
        "maximum_positive_immediate_bound_violation": max(
            float(row["maximum_positive_immediate_bound_violation"])
            for row in candidate_rows
        ),
        "maximum_positive_optimized_bound_violation": max(
            float(row["maximum_positive_optimized_bound_violation"])
            for row in candidate_rows
        ),
        "maximum_positive_weighted_vs_legacy_violation": max(
            float(row["maximum_positive_weighted_vs_legacy_violation"])
            for row in candidate_rows
        ),
        "maximum_positive_immediate_zero_sum_bound_violation": max(
            float(row["positive_immediate_zero_sum_bound_violation"])
            for row in candidate_rows
        ),
        "maximum_positive_optimized_zero_sum_bound_violation": max(
            float(row["positive_optimized_zero_sum_bound_violation"])
            for row in candidate_rows
        ),
        "false_fixed_policy_sign_certificates": sum(
            int(row["false_certificates"]) for row in candidate_rows
        ),
        "target_customer_rows": len(target_rows),
        "target_recompose_to_signed_optimized_certified_marginal_speedup": (
            target_speedup
        ),
        "median_optimized_to_immediate_width_ratio_nonzero": median(
            float(row["optimized_to_immediate_width_ratio"])
            for row in candidate_rows
            if int(row["signed_immediate_feature_width_all_players"]) > 0
        ),
    }
    gate_results = {
        "structured_terminal_identity": (
            aggregate["maximum_structured_terminal_error"]
            <= gates["maximum_structured_terminal_error"]
        ),
        "two_sided_identity": (
            aggregate["maximum_two_sided_utility_error"]
            <= gates["maximum_fixed_policy_delta_error"]
        ),
        "signed_immediate_identity": (
            aggregate["maximum_signed_immediate_utility_error"]
            <= gates["maximum_fixed_policy_delta_error"]
        ),
        "signed_optimized_identity": (
            aggregate["maximum_signed_optimized_utility_error"]
            <= gates["maximum_fixed_policy_delta_error"]
        ),
        "recompose_identity": (
            aggregate["maximum_recompose_utility_error"]
            <= gates["maximum_recompose_utility_error"]
        ),
        "immediate_reach_bound_conservative": (
            aggregate["maximum_positive_immediate_bound_violation"]
            <= gates["maximum_positive_bound_violation"]
        ),
        "optimized_reach_bound_conservative": (
            aggregate["maximum_positive_optimized_bound_violation"]
            <= gates["maximum_positive_bound_violation"]
        ),
        "reach_bound_never_looser_than_legacy": (
            aggregate["maximum_positive_weighted_vs_legacy_violation"]
            <= gates["maximum_positive_bound_violation"]
        ),
        "immediate_zero_sum_envelope_conservative": (
            aggregate["maximum_positive_immediate_zero_sum_bound_violation"]
            <= gates["maximum_positive_zero_sum_bound_violation"]
        ),
        "optimized_zero_sum_envelope_conservative": (
            aggregate["maximum_positive_optimized_zero_sum_bound_violation"]
            <= gates["maximum_positive_zero_sum_bound_violation"]
        ),
        "no_false_fixed_policy_sign_certificates": (
            aggregate["false_fixed_policy_sign_certificates"]
            <= gates["maximum_false_fixed_policy_sign_certificates"]
        ),
        "unilateral_signed_width_is_exactly_half": all(
            int(row["two_sided_feature_width_all_players"])
            == 2 * int(row["signed_immediate_feature_width_all_players"])
            for row in candidate_rows
        ),
        "rank_optimized_cut_never_widens": all(
            int(row["signed_optimized_feature_width_all_players"])
            <= int(row["signed_immediate_feature_width_all_players"])
            for row in candidate_rows
        ),
        "all_nonzero_candidates_change_one_declared_seat": all(
            (
                len(row["changed_reach_modes"]) == 0
                if int(row["changed_policy_nodes"]) == 0
                else tuple(row["changed_reach_modes"]) == (int(row["seat"]),)
            )
            for row in candidate_rows
        ),
        "target_customer_speedup": (
            len(target_rows) == parsed["expected_target_customer_rows"]
            and target_speedup
            >= gates[
                "minimum_target_recompose_to_signed_optimized_certified_speedup"
            ]
        ),
        "synthetic_below_guard_abstains": all(
            all(int(value) == 0 for value in row["certificates"])
            for row in candidate_rows
            if row["candidate_kind"] == "synthetic_guard_below"
        )
        and sum(
            row["candidate_kind"] == "synthetic_guard_below"
            for row in candidate_rows
        )
        == 1,
        "synthetic_above_guard_certifies": any(
            any(int(value) != 0 for value in row["certificates"])
            for row in candidate_rows
            if row["candidate_kind"] == "synthetic_guard_above"
        )
        and sum(
            row["candidate_kind"] == "synthetic_guard_above"
            for row in candidate_rows
        )
        == 1,
        "complete_candidate_rows": (
            len(candidate_rows) == parsed["expected_candidate_rows"]
        ),
        "complete_bill_rows": (
            len(bill_rows)
            == len(candidate_rows) * len(parsed["reuse_counts"])
        ),
    }
    return {
        "schema_version": 1,
        "experiment_type": "signed_rank_optimized_clean_fringe_audit",
        "status": "preregistered_successor_audit",
        "config": parsed,
        "config_sha256": _sha256(_CONFIG),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "source_artifact_sha256": _sha256(_SOURCE_ARTIFACT),
        "predecessor_artifact_sha256": _sha256(_PREDECESSOR_ARTIFACT),
        "environment": environment_metadata(),
        "counts": {
            "geometry_rows": len(geometry_rows),
            "terminal_rows": len(terminal_rows),
            "candidate_rows": len(candidate_rows),
            "bill_rows": len(bill_rows),
        },
        "aggregate": aggregate,
        "gates": {"results": gate_results, "passed": all(gate_results.values())},
        "timing": {"wall_seconds": time.perf_counter() - started},
        "geometry_rows": geometry_rows,
        "terminal_rows": terminal_rows,
        "candidate_rows": candidate_rows,
        "bill_rows": bill_rows,
        "limitations": [
            "Every certificate covers a fixed-policy utility delta only, never a best response, coalition, Pareto comparison, NashConv, or equilibrium change.",
            "The exact flat incumbent is available only on the four- and seven-hand audit axes; no small-axis speed result authorizes Cartesian enumeration at 32 hands.",
            "The Python kernels evaluate six value operators separately; a future native widened pass may have different constants but must preserve these identities and bills.",
            "The cut dynamic program minimizes measured component-times-middle-rank width, not wall time or a fitted future-label objective.",
            "The target speed gate is restricted before execution to h7 DCFR-average checkpoint 4-to-16 and 16-to-64 unilateral candidates.",
            "Source policies are finite selected-axis multiplayer DCFR objects without a multiplayer convergence guarantee.",
        ],
    }


def parse_signed_clean_fringe_config(config: dict[str, Any]) -> dict[str, Any]:
    """Strictly validate the frozen ADR-0079 contract and source hashes."""

    required = {
        "evidence_stage",
        "seed",
        "expected_source_artifact_sha256",
        "expected_predecessor_artifact_sha256",
        "board",
        "pot",
        "stack",
        "bet_size",
        "payoff_span",
        "players",
        "hands_per_player",
        "range_families",
        "mixture_components",
        "split_index",
        "node_relative_tolerance",
        "query_chunk_records",
        "timing_warmups",
        "timing_repeats",
        "reuse_counts",
        "fixed_policy_sign_guard",
        "machine_noise_multiplier",
        "maximum_feature_width_per_batch",
        "target_checkpoint_transitions",
        "expected_candidate_rows",
        "expected_target_customer_rows",
        "gates",
        *_SOURCE_PATHS,
    }
    if set(config) != required:
        raise ValueError("signed clean-fringe config fields differ from ADR-0079")
    for field, path in _SOURCE_PATHS.items():
        if config[field] != _sha256(path):
            raise ValueError(f"frozen source hash mismatch for {field}")
    frozen = {
        "evidence_stage": "preregistered_before_real_policy_signed_or_cut_results",
        "seed": 20260819,
        "expected_source_artifact_sha256": (
            "cdcae48dcca5fd1447fd5ad33426a4b20f04e098c88897d8f0f6eddb797ef36e"
        ),
        "expected_predecessor_artifact_sha256": (
            "ed037fe36a351c286b5a0940537d3b2d39e110028bf8d012f02ba6787a3b3b50"
        ),
        "board": ["2c", "7d", "9h", "Js", "Qc"],
        "pot": 12.0,
        "stack": 30.0,
        "bet_size": 3.0,
        "payoff_span": 30.0,
        "players": 6,
        "hands_per_player": [4, 7],
        "range_families": list(_FAMILIES),
        "mixture_components": 3,
        "split_index": 3,
        "node_relative_tolerance": 1e-12,
        "query_chunk_records": 256,
        "timing_warmups": 1,
        "timing_repeats": 3,
        "reuse_counts": list(_REUSE_COUNTS),
        "fixed_policy_sign_guard": 1e-10,
        "machine_noise_multiplier": 256.0,
        "maximum_feature_width_per_batch": 512,
        "target_checkpoint_transitions": [list(row) for row in _TARGET_TRANSITIONS],
        "expected_candidate_rows": 134,
        "expected_target_customer_rows": 24,
    }
    if any(config[field] != value for field, value in frozen.items()):
        raise ValueError("signed clean-fringe contract differs from ADR-0079")
    expected_gates = {
        "maximum_structured_terminal_error": 1e-12,
        "maximum_fixed_policy_delta_error": 1e-8,
        "maximum_recompose_utility_error": 1e-8,
        "maximum_positive_bound_violation": 0.0,
        "maximum_positive_zero_sum_bound_violation": 0.0,
        "maximum_false_fixed_policy_sign_certificates": 0,
        "minimum_target_recompose_to_signed_optimized_certified_speedup": 1.5,
    }
    if config["gates"] != expected_gates:
        raise ValueError("signed clean-fringe gates differ from ADR-0079")
    return {
        **config,
        "hands_per_player": tuple(config["hands_per_player"]),
        "range_families": tuple(config["range_families"]),
        "reuse_counts": tuple(config["reuse_counts"]),
        "target_checkpoint_transitions": tuple(
            tuple(int(value) for value in row)
            for row in config["target_checkpoint_transitions"]
        ),
        "gates": dict(config["gates"]),
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    result = run_signed_clean_fringe_audit(config)
    rendered = json.dumps(result, indent=2, sort_keys=True, allow_nan=False)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered + "\n", encoding="utf-8")
    print(
        "signed clean fringe: "
        f"candidates={result['counts']['candidate_rows']}, "
        f"passed={result['gates']['passed']}, "
        f"wall={result['timing']['wall_seconds']:.3f}s"
    )
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
