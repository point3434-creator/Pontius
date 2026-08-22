"""Label-free h32 differential for the six-block Tier-B opponent batch."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import gc
import hashlib
import json
import math
from pathlib import Path
import statistics
import time
from typing import Any, Mapping, Sequence

from . import h32_retained_affine_selector_cascade_replay as science
from .axis_cfr_checkpoint import axis_cfr_checkpoint_digest
from .batched_selector_stable_affine_response import (
    evaluate_batched_selector_stable_affine_opponents,
)
from .cupy_sparse_incidence import (
    CuPyBidirectionalIncidence,
    release_cupy_memory_pool,
)
from .factor_tt_contraction import FactorTTBeliefWorkspace
from .h32_affine_resident_cache_preflight import (
    _strict_git_metadata,
    _validate_runtime,
)
from .h32_fresh_union_value_audit import _memory_snapshot
from .incremental_policy_tt import compile_policy_probability_tape
from .open_mode_factor_tt import OpenModeFactorTTWorkspace
from .real_policy import policy_digest
from .reporting import environment_metadata
from .resident_leaf_adjoint_cfr import ResidentLeafAdjointPublicTreeCFR
from .selector_stable_affine_response import (
    certify_selector_stable_affine_envelope,
    evaluate_selector_stable_affine_leaf_adjoint_seat,
)
from .shared_resident_response_context import (
    SharedResidentAutomatonBundle,
    bind_resident_response_context,
)


_ROOT = Path(__file__).parents[2]
_CONFIG = _ROOT / "experiments/configs/h32-tier-b-opponent-batch-v1.json"
_OUTPUT = _ROOT / "experiments/results/h32-tier-b-opponent-batch-v1.json"
_SELECTOR_RESULT = (
    _ROOT
    / "experiments/results/h32-retained-affine-selector-cascade-direct-v1.json"
)
_SELECTOR_DECISION = (
    _ROOT
    / "docs/decisions"
    / "ADR-0206-opponent-sensitivity-composite-locates-retained-value-but-tier-a-cascade-fails.md"
)
_BATCH_IMPLEMENTATION = (
    _ROOT / "src/pontius/batched_selector_stable_affine_response.py"
)
_BATCH_TEST = _ROOT / "tests/test_batched_selector_stable_affine_response.py"
_SCALAR_IMPLEMENTATION = _ROOT / "src/pontius/selector_stable_affine_response.py"
_IMPLEMENTATION = Path(__file__)
_TEST = _ROOT / "tests/test_h32_tier_b_opponent_batch_differential.py"

_PATHS = {
    "expected_science_config_sha256": science._CONFIG,
    "expected_source_result_sha256": science._SOURCE,
    "expected_selector_result_sha256": _SELECTOR_RESULT,
    "expected_selector_decision_sha256": _SELECTOR_DECISION,
    "expected_batch_implementation_sha256": _BATCH_IMPLEMENTATION,
    "expected_batch_control_test_sha256": _BATCH_TEST,
    "expected_scalar_implementation_sha256": _SCALAR_IMPLEMENTATION,
    "expected_audit_implementation_sha256": _IMPLEMENTATION,
    "expected_control_test_sha256": _TEST,
}


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required Tier-B batch input is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_h32_tier_b_opponent_batch_config(
    config: dict[str, Any],
) -> dict[str, Any]:
    """Validate the frozen no-label Tier-B batch differential."""

    fields = {
        "evidence_stage",
        *_PATHS,
        "target_scope",
        "candidate_family",
        "candidate_order",
        "batch_axis",
        "charged_work",
        "own_row_rule",
        "comparison_rule",
        "timing_warmups_per_arm",
        "timing_arm_schedule",
        "street_budget_ms",
        "emission_reserve_ms",
        "minimum_prebatch_physical_free_bytes",
        "maximum_feature_width_per_batch",
        "outcome_policy",
        "gates",
    }
    if set(config) != fields:
        raise ValueError("Tier-B batch config fields differ from ADR-0207")
    frozen = {
        "evidence_stage": (
            "preregistered_after_adr0206_before_any_h32_batched_opponent_"
            "coefficient_or_timing_measurement"
        ),
        "target_scope": "all_six_retained_adr0186_contexts_without_label_load",
        "candidate_family": "regret_vertex_only",
        "candidate_order": "one_public_node_block_per_acting_seat_zero_through_five",
        "batch_axis": (
            "for_each_responding_seat_pack_the_other_five_acting_seat_"
            "directions_into_one_resident_heterogeneous_contraction"
        ),
        "charged_work": (
            "six_batched_opponent_calls_replace_thirty_scalar_opponent_calls_"
            "for_the_complete_six_block_library"
        ),
        "own_row_rule": (
            "six_acting_seat_rows_use_the_exact_zero_terminal_contraction_"
            "reverse_and_are_timed_separately"
        ),
        "comparison_rule": (
            "compare_every_numeric_affine_coefficient_and_every_selector_"
            "switch_field_to_the_scalar_teacher_under_adr0179_ceilings"
        ),
        "timing_warmups_per_arm": 1,
        "timing_arm_schedule": [
            ["scalar", "batched"],
            ["batched", "scalar"],
            ["scalar", "batched"],
        ],
        "street_budget_ms": 15000.0,
        "emission_reserve_ms": 1000.0,
        "minimum_prebatch_physical_free_bytes": 5_184_456_164,
        "maximum_feature_width_per_batch": 384,
        "outcome_policy": (
            "validity_is_identity_memory_and_accounting_only_report_speed_"
            "and_full_set_fit_without_using_them_as_retroactive_validity_gates"
        ),
    }
    if any(config[key] != value for key, value in frozen.items()):
        raise ValueError("Tier-B batch workload differs from ADR-0207")
    expected_gates = {
        "expected_targets": 6,
        "expected_candidates_per_target": 6,
        "expected_opponent_rows_per_target": 30,
        "expected_scalar_opponent_calls_per_arm": 30,
        "expected_batch_calls_per_arm": 6,
        "maximum_numeric_error": 2e-11,
        "maximum_composite_error": 2e-11,
        "maximum_warm_start_probability_error": 1e-12,
        "maximum_warm_start_mean_total_variation": 1e-13,
        "maximum_search_step_ms": 60000.0,
        "maximum_arm_wall_ms": 60000.0,
        "maximum_gpu_pool_bytes": 12_000_000_000,
        "minimum_postwork_physical_free_bytes": 1_000_000_000,
        "maximum_total_audit_seconds": 1800.0,
        "require_clean_git_state": True,
        "require_source_parent_passed": True,
        "require_source_checkpoint_identity": True,
        "require_target_identity": True,
        "require_blueprint_identity": True,
        "require_structural_identity": True,
        "require_exactly_five_opponent_rows_per_candidate": True,
        "require_own_rows_zero_contraction": True,
        "require_batch_safe_preflight": True,
        "require_blueprint_emission": True,
        "require_finite": True,
        "require_strategy_population_claim_null": True,
    }
    if config["gates"] != expected_gates:
        raise ValueError("Tier-B batch gates differ from ADR-0207")
    for field, path in _PATHS.items():
        if config[field] != _sha256(path):
            raise ValueError(f"Tier-B batch source mismatch: {field}")
    science_config = json.loads(science._CONFIG.read_text(encoding="utf-8"))
    live = science.parse_h32_retained_affine_selector_cascade_config(science_config)
    if config["maximum_feature_width_per_batch"] != live[
        "maximum_feature_width_per_batch"
    ]:
        raise ValueError("Tier-B batch feature width differs from its live source")
    return {**config, "live": live}


def affine_semantic_difference(
    scalar: Any,
    batched: Any,
) -> dict[str, Any]:
    """Compare one batched semantic row with the scalar teacher."""

    numeric_fields = (
        "profile_utility_intercept",
        "profile_utility_slope",
        "best_response_value_intercept",
        "best_response_value_slope",
        "deviation_gain_intercept",
        "deviation_gap_slope",
        "selector_stable_scale",
    )
    structural_fields = (
        "target_player",
        "acting_player",
        "changed_public_node",
        "first_switch_information_key",
        "first_switch_source_action",
        "first_switch_competing_action",
        "first_switch_hand_index",
        "selector_comparisons",
        "exact_source_action_ties",
        "changed_public_nodes",
        "changed_opponent_public_nodes",
        "affected_terminal_contractions",
        "full_terminal_contractions",
        "reused_terminal_numerators",
    )
    errors = {
        field: abs(float(getattr(scalar, field)) - float(getattr(batched, field)))
        for field in numeric_fields
    }
    mismatches = [
        field
        for field in structural_fields
        if getattr(scalar, field) != getattr(batched, field)
    ]
    return {
        "maximum_numeric_error": max(errors.values(), default=0.0),
        "numeric_errors": errors,
        "structural_mismatches": mismatches,
        "structural_identity": not mismatches,
    }


def complete_six_block_ledger(
    *,
    search_step_ms: float,
    endpoint_construction_ms: float,
    own_row_ms: float,
    batched_opponent_ms: float,
    ranking_and_winner_envelope_ms: float,
    emission_reserve_ms: float,
    street_budget_ms: float,
) -> dict[str, Any]:
    """Charge every complete B-to-C stage once under the street boundary."""

    stages = {
        "search_step_ms": float(search_step_ms),
        "six_endpoint_construction_ms": float(endpoint_construction_ms),
        "six_zero_contraction_own_rows_ms": float(own_row_ms),
        "six_seat_batched_opponent_ms": float(batched_opponent_ms),
        "ranking_and_one_winner_envelope_ms": float(
            ranking_and_winner_envelope_ms
        ),
        "emission_reserve_ms": float(emission_reserve_ms),
    }
    total = math.fsum(stages.values())
    return {
        "stages": stages,
        "total_ms": total,
        "headroom_ms": float(street_budget_ms) - total,
        "full_six_block_set_fits": total <= float(street_budget_ms),
    }


def _finite_tree(value: Any) -> bool:
    if value is None or isinstance(value, (str, bool)):
        return True
    if isinstance(value, (int, float)):
        return math.isfinite(float(value))
    if isinstance(value, Mapping):
        return all(_finite_tree(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return all(_finite_tree(item) for item in value)
    return True


def _run_scalar_opponents(
    *,
    endpoints: Sequence[Any],
    acting_players: Sequence[int],
    context: Any,
    shared: Any,
    gpu: Any,
    live: Mapping[str, Any],
    cp: Any,
) -> tuple[list[list[Any | None]], dict[str, Any]]:
    cp.cuda.runtime.deviceSynchronize()
    started = time.perf_counter()
    rows: list[list[Any | None]] = [
        [None] * len(context.response_caches) for _ in endpoints
    ]
    calls = 0
    terminal_ms = 0.0
    reverse_ms = 0.0
    maximum_pool = 0
    for candidate_index, (endpoint, acting_player) in enumerate(
        zip(endpoints, acting_players, strict=True)
    ):
        for target_player, cache in enumerate(context.response_caches):
            if target_player == acting_player:
                continue
            row = evaluate_selector_stable_affine_leaf_adjoint_seat(
                cache,
                endpoint,
                acting_player=acting_player,
                selector_margin_allowance=float(live["selector_margin_allowance"]),
                maximum_feature_width_per_batch=int(
                    live["maximum_feature_width_per_batch"]
                ),
                belief_cache=context.belief_cache,
                automaton_cache=shared.automaton_caches[target_player],
                cupy_sparse=gpu,
            )
            rows[candidate_index][target_player] = row
            calls += 1
            terminal_ms += float(row.terminal_contraction_ms)
            reverse_ms += float(row.reverse_evaluation_ms)
            maximum_pool = max(
                maximum_pool, int(row.maximum_gpu_pool_total_bytes)
            )
    cp.cuda.runtime.deviceSynchronize()
    return rows, {
        "wall_ms": (time.perf_counter() - started) * 1000.0,
        "opponent_calls": calls,
        "terminal_contraction_ms": terminal_ms,
        "reverse_evaluation_ms": reverse_ms,
        "maximum_gpu_pool_total_bytes": maximum_pool,
    }


def _run_batched_opponents(
    *,
    endpoints: Sequence[Any],
    acting_players: Sequence[int],
    context: Any,
    shared: Any,
    gpu: Any,
    live: Mapping[str, Any],
    cp: Any,
) -> tuple[list[list[Any | None]], dict[str, Any]]:
    cp.cuda.runtime.deviceSynchronize()
    started = time.perf_counter()
    rows: list[list[Any | None]] = [
        [None] * len(context.response_caches) for _ in endpoints
    ]
    works = []
    for target_player, cache in enumerate(context.response_caches):
        candidate_indices = [
            index
            for index, acting_player in enumerate(acting_players)
            if acting_player != target_player
        ]
        result = evaluate_batched_selector_stable_affine_opponents(
            cache,
            tuple(endpoints[index] for index in candidate_indices),
            acting_players=tuple(acting_players[index] for index in candidate_indices),
            selector_margin_allowance=float(live["selector_margin_allowance"]),
            maximum_feature_width_per_batch=int(
                live["maximum_feature_width_per_batch"]
            ),
            belief_cache=context.belief_cache,
            automaton_cache=shared.automaton_caches[target_player],
            cupy_sparse=gpu,
        )
        works.append(result.work)
        for candidate_index, row in zip(
            candidate_indices, result.seat_results, strict=True
        ):
            rows[candidate_index][target_player] = row
    cp.cuda.runtime.deviceSynchronize()
    return rows, {
        "wall_ms": (time.perf_counter() - started) * 1000.0,
        "batch_calls": sum(work.contraction_calls for work in works),
        "opponent_rows": sum(work.candidate_rows for work in works),
        "affected_terminal_contractions": sum(
            work.affected_terminal_contractions for work in works
        ),
        "terminal_sparse_batches": sum(
            work.terminal_sparse_batches for work in works
        ),
        "term_prepare_ms": math.fsum(work.term_prepare_ms for work in works),
        "terminal_contraction_ms": math.fsum(
            work.terminal_contraction_ms for work in works
        ),
        "reverse_evaluation_ms": math.fsum(
            work.reverse_evaluation_ms for work in works
        ),
        "factor_prepare_ms": math.fsum(work.factor_prepare_ms for work in works),
        "factor_upload_ms": math.fsum(work.factor_upload_ms for work in works),
        "product_generation_gpu_ms": math.fsum(
            work.product_generation_gpu_ms for work in works
        ),
        "resident_pipeline_gpu_ms": math.fsum(
            work.resident_pipeline_gpu_ms for work in works
        ),
        "device_to_host_ms": math.fsum(
            work.device_to_host_ms for work in works
        ),
        "hand_fold_ms": math.fsum(work.hand_fold_ms for work in works),
        "maximum_terminal_middle_rank": max(
            work.maximum_terminal_middle_rank for work in works
        ),
        "maximum_gpu_pool_used_bytes": max(
            work.maximum_gpu_pool_used_bytes for work in works
        ),
        "maximum_gpu_pool_total_bytes": max(
            work.maximum_gpu_pool_total_bytes for work in works
        ),
        "work_by_target_seat": [asdict(work) for work in works],
    }


def _prepare_target(
    parsed: Mapping[str, Any],
    source_parent: Mapping[str, Any],
    target_spec: Mapping[str, Any],
    cp: Any,
) -> tuple[dict[str, Any], dict[str, Any]]:
    live = parsed["live"]
    board = science.parse_cards(*target_spec["board"])
    family = str(target_spec["range_family"])
    source, layout, sparse, retained = science._build_case(
        parsed=live,
        board=board,
        hand_count=int(live["hands_per_player"]),
        family=family,
    )
    source_workspace, _, automata = retained
    source_digest = science._belief_digest(source)
    source_row = next(
        row
        for row in source_parent["source_rows"]
        if row["source"] == f"{target_spec['board_id']}/{family}"
    )
    state = source_row["final_checkpoint"]
    source_checkpoint_identity = (
        axis_cfr_checkpoint_digest(state) == state["state_sha256"]
        and source_digest == target_spec["source_belief_sha256"]
        and source_digest == source_row["source_belief_sha256"]
    )
    blueprint = science._average_policy_from_state(state)
    blueprint_digest = policy_digest(blueprint)
    blueprint_identity = blueprint_digest == state["average_policy_sha256"]
    belief, descriptor = science.build_fresh_seat2_target(
        source, board=board, target_seat=2
    )
    target_digest = science._belief_digest(belief)
    target_identity = (
        target_digest == target_spec["target_belief_sha256"]
        and science._json_digest(descriptor)
        == target_spec["target_descriptor_sha256"]
        and belief.hands_by_player == source.hands_by_player
    )

    base = FactorTTBeliefWorkspace.compile(
        source_workspace.topology.base,
        belief,
        query_chunk_records=int(live["query_chunk_records"]),
    )
    workspace = OpenModeFactorTTWorkspace.compile(source_workspace.topology, base)
    gpu = CuPyBidirectionalIncidence.compile(sparse)
    shared = SharedResidentAutomatonBundle.compile(workspace, automata)
    context = bind_resident_response_context(
        shared,
        layout=layout,
        workspace=workspace,
        sparse=sparse,
        source_policy=blueprint,
        hands_by_player=belief.hands_by_player,
        cupy_sparse=gpu,
        maximum_feature_width_per_batch=int(
            live["maximum_feature_width_per_batch"]
        ),
    )
    blueprint_quality = science._source_quality(
        context, payoff_span=float(live["stack"])
    )
    solver = ResidentLeafAdjointPublicTreeCFR(
        layout,
        workspace,
        sparse,
        automata,
        str(live["solver_variant"]),
        belief_cache=context.belief_cache,
        automaton_caches=shared.automaton_caches,
        cupy_sparse=gpu,
        maximum_feature_width_per_batch=int(
            live["maximum_feature_width_per_batch"]
        ),
        hands_by_player=belief.hands_by_player,
    )
    warm_mass = float(live["warm_regret_mass_payoff_fraction"]) * float(
        layout.game.payoff_span
    )
    solver.warm_start(blueprint, warm_mass)
    warm_start_distance = science._policy_distance(
        blueprint, solver.current_strategy()
    )
    release_cupy_memory_pool()
    cp.cuda.runtime.deviceSynchronize()
    search_started = time.perf_counter()
    solver.step()
    cp.cuda.runtime.deviceSynchronize()
    search_step_ms = (time.perf_counter() - search_started) * 1000.0

    soft_candidate = solver.current_strategy()
    regret_deltas = science.recover_iteration_one_dcfr_regret_deltas(
        blueprint, solver.regret_table(), warm_regret_mass=warm_mass
    )
    anchors = science.select_one_atom_per_acting_seat(
        layout, belief.hands_by_player, blueprint, soft_candidate
    )
    blocks = science.build_public_node_blocks(blueprint, soft_candidate, anchors)
    if tuple(int(block["acting_seat"]) for block in blocks) != tuple(range(6)):
        raise ArithmeticError("Tier-B batch blocks are not in acting-seat order")

    endpoint_started = time.perf_counter()
    endpoints = []
    endpoint_rows = []
    for block in blocks:
        acting_player = int(block["acting_seat"])
        keys = tuple(block["information_keys"])
        endpoint_policy = science.build_regret_vertex_candidate(
            blueprint, regret_deltas, keys
        )
        endpoints.append(
            compile_policy_probability_tape(
                layout, belief.hands_by_player, endpoint_policy
            )
        )
        endpoint_rows.append(
            {
                "acting_player": acting_player,
                "public_history": str(block["public_history"]),
                "information_keys": list(keys),
                "endpoint_policy_sha256_diagnostic": policy_digest(endpoint_policy),
            }
        )
    endpoint_construction_ms = (time.perf_counter() - endpoint_started) * 1000.0
    acting_players = tuple(row["acting_player"] for row in endpoint_rows)

    own_times = []
    own_rows: list[Any] = []
    for _ in parsed["timing_arm_schedule"]:
        cp.cuda.runtime.deviceSynchronize()
        own_started = time.perf_counter()
        measured = []
        for candidate_index, acting_player in enumerate(acting_players):
            measured.append(
                evaluate_selector_stable_affine_leaf_adjoint_seat(
                    context.response_caches[acting_player],
                    endpoints[candidate_index],
                    acting_player=acting_player,
                    selector_margin_allowance=float(
                        live["selector_margin_allowance"]
                    ),
                    maximum_feature_width_per_batch=int(
                        live["maximum_feature_width_per_batch"]
                    ),
                    belief_cache=context.belief_cache,
                    automaton_cache=shared.automaton_caches[acting_player],
                    cupy_sparse=gpu,
                )
            )
        cp.cuda.runtime.deviceSynchronize()
        own_times.append((time.perf_counter() - own_started) * 1000.0)
        if not own_rows:
            own_rows = measured

    memory_rows = [_memory_snapshot(cp)]
    safe_preflight = (
        int(memory_rows[-1]["gpu_free_bytes"])
        >= int(parsed["minimum_prebatch_physical_free_bytes"])
    )
    objects = {
        "source": source,
        "layout": layout,
        "sparse": sparse,
        "source_workspace": source_workspace,
        "automata": automata,
        "base": base,
        "workspace": workspace,
        "gpu": gpu,
        "shared": shared,
        "context": context,
        "solver": solver,
        "belief": belief,
        "endpoints": tuple(endpoints),
        "acting_players": acting_players,
        "own_rows": own_rows,
    }
    metadata = {
        "target": target_spec["target"],
        "board_id": target_spec["board_id"],
        "range_family": family,
        "source_checkpoint_identity": source_checkpoint_identity,
        "target_identity": target_identity,
        "blueprint_identity": blueprint_identity,
        "blueprint_policy_sha256": blueprint_digest,
        "blueprint_quality": blueprint_quality,
        "warm_start_distance": warm_start_distance,
        "search_step_ms": search_step_ms,
        "endpoint_construction_ms": endpoint_construction_ms,
        "endpoint_rows": endpoint_rows,
        "own_row_ms": {
            "samples": own_times,
            "median": statistics.median(own_times),
            "maximum": max(own_times),
        },
        "own_rows_zero_contraction": all(
            row.affected_terminal_contractions == 0 for row in own_rows
        ),
        "batch_safe_preflight": safe_preflight,
        "memory_rows": memory_rows,
        "emitted_candidate_id": "blueprint_average64",
        "emitted_policy_sha256": blueprint_digest,
    }
    return objects, metadata


def _run_target(
    parsed: Mapping[str, Any],
    source_parent: Mapping[str, Any],
    target_spec: Mapping[str, Any],
    cp: Any,
) -> dict[str, Any]:
    objects, result = _prepare_target(parsed, source_parent, target_spec, cp)
    if not result["batch_safe_preflight"]:
        result["status"] = "stopped_before_batch_for_physical_headroom"
        del objects
        gc.collect()
        release_cupy_memory_pool()
        return result

    endpoints = objects["endpoints"]
    acting_players = objects["acting_players"]
    context = objects["context"]
    shared = objects["shared"]
    gpu = objects["gpu"]
    live = parsed["live"]

    for arm in ("scalar", "batched"):
        for _ in range(int(parsed["timing_warmups_per_arm"])):
            release_cupy_memory_pool()
            if arm == "scalar":
                _run_scalar_opponents(
                    endpoints=endpoints,
                    acting_players=acting_players,
                    context=context,
                    shared=shared,
                    gpu=gpu,
                    live=live,
                    cp=cp,
                )
            else:
                _run_batched_opponents(
                    endpoints=endpoints,
                    acting_players=acting_players,
                    context=context,
                    shared=shared,
                    gpu=gpu,
                    live=live,
                    cp=cp,
                )

    timing_rows = []
    scalar_reference = None
    batched_reference = None
    comparisons = []
    for repetition, arm_order in enumerate(parsed["timing_arm_schedule"], start=1):
        for arm in arm_order:
            release_cupy_memory_pool()
            result["memory_rows"].append(_memory_snapshot(cp))
            if arm == "scalar":
                rows, timing = _run_scalar_opponents(
                    endpoints=endpoints,
                    acting_players=acting_players,
                    context=context,
                    shared=shared,
                    gpu=gpu,
                    live=live,
                    cp=cp,
                )
                scalar_reference = rows
            else:
                rows, timing = _run_batched_opponents(
                    endpoints=endpoints,
                    acting_players=acting_players,
                    context=context,
                    shared=shared,
                    gpu=gpu,
                    live=live,
                    cp=cp,
                )
                batched_reference = rows
            result["memory_rows"].append(_memory_snapshot(cp))
            timing_rows.append(
                {"repetition": repetition, "arm": arm, **timing}
            )
        assert scalar_reference is not None and batched_reference is not None
        for candidate_index, acting_player in enumerate(acting_players):
            for target_player in range(6):
                if target_player == acting_player:
                    continue
                comparisons.append(
                    affine_semantic_difference(
                        scalar_reference[candidate_index][target_player],
                        batched_reference[candidate_index][target_player],
                    )
                )

    assert scalar_reference is not None and batched_reference is not None
    full_scalar = []
    full_batched = []
    composite_errors = []
    candidate_features = []
    raw_guard = float(live["acceptance_guard_normalized"]) * float(live["stack"])
    blueprint_gains = tuple(
        float(value) for value in result["blueprint_quality"]["deviation_gains"]
    )
    for candidate_index, acting_player in enumerate(acting_players):
        scalar_rows = list(scalar_reference[candidate_index])
        batched_rows = list(batched_reference[candidate_index])
        scalar_rows[acting_player] = objects["own_rows"][candidate_index]
        batched_rows[acting_player] = objects["own_rows"][candidate_index]
        full_scalar.append(tuple(scalar_rows))
        full_batched.append(tuple(batched_rows))
        scalar_tier = science.affine_tier_features(
            scalar_rows,
            acting_seat=acting_player,
            raw_guard=raw_guard,
            numerical_allowance=float(live["envelope_numerical_allowance"]),
            blueprint_deviation_gains=blueprint_gains,
        )
        batched_tier = science.affine_tier_features(
            batched_rows,
            acting_seat=acting_player,
            raw_guard=raw_guard,
            numerical_allowance=float(live["envelope_numerical_allowance"]),
            blueprint_deviation_gains=blueprint_gains,
        )
        scalar_value = float(
            scalar_tier["features"]["tier_b_slope_predicted_value"]
        )
        batched_value = float(
            batched_tier["features"]["tier_b_slope_predicted_value"]
        )
        composite_errors.append(abs(scalar_value - batched_value))
        candidate_features.append(
            {
                **result["endpoint_rows"][candidate_index],
                "tier_b_slope_predicted_value": batched_value,
                "tier_b_cap_radius": float(
                    batched_tier["features"]["tier_b_cap_radius"]
                ),
                "tier_b_exact_objective_improvement_slope": float(
                    batched_tier["features"][
                        "tier_b_exact_objective_improvement_slope"
                    ]
                ),
            }
        )

    ranking_started = time.perf_counter()
    winner_index = min(
        range(len(candidate_features)),
        key=lambda index: (
            -candidate_features[index]["tier_b_slope_predicted_value"],
            candidate_features[index]["acting_player"],
            candidate_features[index]["public_history"],
        ),
    )
    winner_envelope = certify_selector_stable_affine_envelope(
        full_batched[winner_index],
        blueprint_deviation_gains=blueprint_gains,
        blueprint_nash_conv=float(result["blueprint_quality"]["nash_conv"]),
        raw_guard=raw_guard,
        scale_grid=tuple(
            2.0**-index
            for index in range(34)
            if 2.0**-index >= float(live["numerical_floor"])
        ),
        safety_fraction=float(live["safety_fraction"]),
        numerical_allowance=float(live["envelope_numerical_allowance"]),
    )
    ranking_ms = (time.perf_counter() - ranking_started) * 1000.0

    scalar_times = [row["wall_ms"] for row in timing_rows if row["arm"] == "scalar"]
    batch_times = [row["wall_ms"] for row in timing_rows if row["arm"] == "batched"]
    scalar_median = statistics.median(scalar_times)
    batch_median = statistics.median(batch_times)
    result.update(
        {
            "status": "completed",
            "timing_rows": timing_rows,
            "summary": {
                "scalar_opponent_median_ms": scalar_median,
                "batched_opponent_median_ms": batch_median,
                "opponent_speedup": scalar_median / batch_median,
                "scalar_opponent_minimum_ms": min(scalar_times),
                "scalar_opponent_maximum_ms": max(scalar_times),
                "batched_opponent_minimum_ms": min(batch_times),
                "batched_opponent_maximum_ms": max(batch_times),
            },
            "identity": {
                "opponent_rows_compared": len(comparisons),
                "maximum_numeric_error": max(
                    row["maximum_numeric_error"] for row in comparisons
                ),
                "structural_identity": all(
                    row["structural_identity"] for row in comparisons
                ),
                "maximum_composite_error": max(composite_errors, default=0.0),
            },
            "candidate_features_without_labels": candidate_features,
            "winner_without_label_join": {
                "candidate_index": winner_index,
                "acting_player": acting_players[winner_index],
                "public_history": result["endpoint_rows"][winner_index][
                    "public_history"
                ],
                "envelope_complete": bool(winner_envelope.complete),
                "envelope_stop_reason": str(winner_envelope.stop_reason),
                "selected_scale": winner_envelope.selected_scale,
                "positive_certified_value": float(
                    winner_envelope.positive_certified_value
                ),
            },
            "ranking_and_winner_envelope_ms": ranking_ms,
            "complete_six_block_ledger": complete_six_block_ledger(
                search_step_ms=float(result["search_step_ms"]),
                endpoint_construction_ms=float(result["endpoint_construction_ms"]),
                own_row_ms=float(result["own_row_ms"]["median"]),
                batched_opponent_ms=float(batch_median),
                ranking_and_winner_envelope_ms=ranking_ms,
                emission_reserve_ms=float(parsed["emission_reserve_ms"]),
                street_budget_ms=float(parsed["street_budget_ms"]),
            ),
        }
    )

    del full_scalar, full_batched, scalar_reference, batched_reference
    del objects
    gc.collect()
    release_cupy_memory_pool()
    return result


def run_h32_tier_b_opponent_batch_differential(
    config_path: Path = _CONFIG,
    output_path: Path = _OUTPUT,
) -> dict[str, Any]:
    """Execute the frozen scalar-versus-batched Tier-B comparison once."""

    started = time.perf_counter()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    parsed = parse_h32_tier_b_opponent_batch_config(config)
    source_parent = json.loads(science._SOURCE.read_text(encoding="utf-8"))
    git = _strict_git_metadata()
    cp, runtime = _validate_runtime(parsed["live"])
    if git["dirty"]:
        raise RuntimeError("Tier-B batch differential requires clean Git state")
    if not bool(source_parent["gates"]["passed"]):
        raise ValueError("Tier-B batch source parent did not pass")

    target_rows = []
    for target_spec in parsed["live"]["targets"]:
        print(f"Tier-B opponent batch: {target_spec['target']}", flush=True)
        row = _run_target(parsed, source_parent, target_spec, cp)
        target_rows.append(row)
        if not row["batch_safe_preflight"]:
            break

    total_seconds = time.perf_counter() - started
    completed = [row for row in target_rows if row["status"] == "completed"]
    memory_rows = [memory for row in target_rows for memory in row["memory_rows"]]
    gates_config = parsed["gates"]
    maximum_numeric_error = max(
        (row["identity"]["maximum_numeric_error"] for row in completed),
        default=math.inf,
    )
    maximum_composite_error = max(
        (row["identity"]["maximum_composite_error"] for row in completed),
        default=math.inf,
    )
    maximum_probability_error = max(
        (
            row["warm_start_distance"]["maximum_probability_error"]
            for row in target_rows
        ),
        default=math.inf,
    )
    maximum_mean_tv = max(
        (
            row["warm_start_distance"]["mean_total_variation"]
            for row in target_rows
        ),
        default=math.inf,
    )
    reported_pool_rows = [
        int(timing["maximum_gpu_pool_total_bytes"])
        for row in completed
        for timing in row["timing_rows"]
    ]
    maximum_pool = max(
        [int(row["gpu_pool_total_bytes"]) for row in memory_rows]
        + reported_pool_rows,
        default=0,
    )
    minimum_free = min(
        (int(row["gpu_free_bytes"]) for row in memory_rows), default=0
    )
    all_timing_rows = [timing for row in completed for timing in row["timing_rows"]]
    gates = {
        "clean_git": (not git["dirty"])
        == gates_config["require_clean_git_state"],
        "source_parent_passed": bool(source_parent["gates"]["passed"])
        == gates_config["require_source_parent_passed"],
        "target_count": len(completed) == gates_config["expected_targets"],
        "candidate_count": all(
            len(row["endpoint_rows"])
            == gates_config["expected_candidates_per_target"]
            for row in completed
        ),
        "opponent_row_count": all(
            timing.get("opponent_rows", gates_config["expected_opponent_rows_per_target"])
            == gates_config["expected_opponent_rows_per_target"]
            for timing in all_timing_rows
        ),
        "scalar_call_count": all(
            timing["opponent_calls"]
            == gates_config["expected_scalar_opponent_calls_per_arm"]
            for timing in all_timing_rows
            if timing["arm"] == "scalar"
        ),
        "batch_call_count": all(
            timing["batch_calls"]
            == gates_config["expected_batch_calls_per_arm"]
            for timing in all_timing_rows
            if timing["arm"] == "batched"
        ),
        "source_checkpoint_identity": all(
            row["source_checkpoint_identity"] for row in target_rows
        )
        == gates_config["require_source_checkpoint_identity"],
        "target_identity": all(row["target_identity"] for row in target_rows)
        == gates_config["require_target_identity"],
        "blueprint_identity": all(row["blueprint_identity"] for row in target_rows)
        == gates_config["require_blueprint_identity"],
        "warm_start_probability_error": maximum_probability_error
        <= gates_config["maximum_warm_start_probability_error"],
        "warm_start_mean_total_variation": maximum_mean_tv
        <= gates_config["maximum_warm_start_mean_total_variation"],
        "numeric_identity": maximum_numeric_error
        <= gates_config["maximum_numeric_error"],
        "composite_identity": maximum_composite_error
        <= gates_config["maximum_composite_error"],
        "structural_identity": all(
            row["identity"]["structural_identity"] for row in completed
        )
        == gates_config["require_structural_identity"],
        "five_opponent_rows": all(
            timing["opponent_rows"]
            == len(row["endpoint_rows"]) * 5
            for row in completed
            for timing in row["timing_rows"]
            if timing["arm"] == "batched"
        )
        == gates_config["require_exactly_five_opponent_rows_per_candidate"],
        "own_zero_contraction": all(
            row["own_rows_zero_contraction"] for row in target_rows
        )
        == gates_config["require_own_rows_zero_contraction"],
        "batch_safe_preflight": all(
            row["batch_safe_preflight"] for row in target_rows
        )
        == gates_config["require_batch_safe_preflight"],
        "search_step_ms": max(
            (row["search_step_ms"] for row in target_rows), default=math.inf
        )
        <= gates_config["maximum_search_step_ms"],
        "arm_wall_ms": max(
            (timing["wall_ms"] for timing in all_timing_rows), default=math.inf
        )
        <= gates_config["maximum_arm_wall_ms"],
        "gpu_pool": maximum_pool <= gates_config["maximum_gpu_pool_bytes"],
        "physical_free": minimum_free
        >= gates_config["minimum_postwork_physical_free_bytes"],
        "total_audit_seconds": total_seconds
        <= gates_config["maximum_total_audit_seconds"],
        "blueprint_emission": all(
            row["emitted_candidate_id"] == "blueprint_average64"
            and row["emitted_policy_sha256"] == row["blueprint_policy_sha256"]
            for row in target_rows
        )
        == gates_config["require_blueprint_emission"],
        "finite": _finite_tree({"targets": target_rows, "seconds": total_seconds})
        == gates_config["require_finite"],
        "strategy_population_claim_null": True
        == gates_config["require_strategy_population_claim_null"],
    }
    gates["passed"] = all(gates.values())
    speedups = [row["summary"]["opponent_speedup"] for row in completed]
    full_fit = [
        row["complete_six_block_ledger"]["full_six_block_set_fits"]
        for row in completed
    ]
    if not gates["passed"]:
        decision = "reject_tier_b_batch_differential"
    elif all(full_fit):
        decision = "accept_full_six_block_b_to_c_path_on_retained_ledgers"
    elif speedups and statistics.median(speedups) > 1.0:
        decision = "accept_batch_primitive_but_continue_tier_b_optimization"
    else:
        decision = "retain_scalar_tier_b_path"

    result = {
        "schema_version": 1,
        "status": "h32_tier_b_opponent_batch_differential_executed",
        "methodology": {
            "retained_contexts_only": True,
            "strategy_labels_loaded": 0,
            "candidate_family": "regret_vertex",
            "scalar_teacher_calls_per_arm": 30,
            "batched_calls_per_arm": 6,
            "acting_seat_rows_charged_separately": True,
            "speed_and_full_set_fit_are_report_only": True,
            "immutable_blueprint_emission": True,
        },
        "environment": {
            **environment_metadata(),
            **runtime,
            "git": git,
        },
        "config_sha256": _sha256(config_path),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "batch_implementation_sha256": _sha256(_BATCH_IMPLEMENTATION),
        "target_rows": target_rows,
        "aggregate": {
            "targets_completed": len(completed),
            "candidate_rows": sum(len(row["endpoint_rows"]) for row in completed),
            "opponent_rows_per_timing_arm": 30,
            "maximum_numeric_error": (
                maximum_numeric_error if completed else None
            ),
            "maximum_composite_error": (
                maximum_composite_error if completed else None
            ),
            "maximum_warm_start_probability_error": maximum_probability_error,
            "maximum_warm_start_mean_total_variation": maximum_mean_tv,
            "maximum_gpu_pool_bytes": maximum_pool,
            "minimum_gpu_free_bytes": minimum_free,
            "opponent_speedup_median_across_targets": (
                statistics.median(speedups) if speedups else None
            ),
            "opponent_speedup_minimum": min(speedups) if speedups else None,
            "opponent_speedup_maximum": max(speedups) if speedups else None,
            "full_six_block_fit_targets": sum(full_fit),
        },
        "gates": gates,
        "passed": gates["passed"],
        "decision": decision,
        "strategy_population_claim": None,
        "total_audit_seconds": total_seconds,
        "limitations": [
            "All six retained contexts were exposed before this engineering differential.",
            "No ADR-0186 or ADR-0206 strategy label is deserialized or joined.",
            "Observed timings are paired development measurements, not a latency distribution.",
            "The six-block library is small and cannot establish widened-corpus transfer.",
            "No strategy-quality, deployment, population, or hardware claim is authorized.",
        ],
    }
    output_path.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=_CONFIG)
    parser.add_argument("--output", type=Path, default=_OUTPUT)
    args = parser.parse_args()
    result = run_h32_tier_b_opponent_batch_differential(args.config, args.output)
    print(
        json.dumps(
            {
                "output": str(args.output),
                "passed": result["passed"],
                "decision": result["decision"],
                "aggregate": result["aggregate"],
            },
            indent=2,
        )
    )
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
