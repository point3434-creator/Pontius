"""Label-free paired one-step/two-step continuation depth ledger."""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import math
from pathlib import Path
import time
from typing import Any, Mapping

import numpy as np

from .cupy_sparse_incidence import release_cupy_memory_pool
from .device_fold_resident_leaf_adjoint_cfr import (
    DeviceFoldResidentLeafAdjointPublicTreeCFR,
)
from .device_fold_selector_stable_affine_response import (
    evaluate_device_fold_selector_stable_affine_leaf_adjoint_seat,
)
from .h32_affine_resident_cache_preflight import _strict_git_metadata, _validate_runtime
from .h32_continuation_root_ledger import _setup
from .h32_continuation_root_strategy_trial import _ordered_blocks
from .h32_fresh_regret_vertex_opportunity_audit import (
    build_regret_vertex_candidate,
    direction_has_convex_scope,
)
from .h32_fresh_union_value_audit import _memory_snapshot
from .h32_resident_record_to_hand_fold_differential import _work_ledger
from .h32_warm_search_acceptance_audit import _policy_distance
from .incremental_policy_tt import compile_policy_probability_tape
from .real_policy import policy_digest
from .reporting import environment_metadata
from .selector_stable_affine_response import (
    evaluate_selector_stable_affine_leaf_adjoint_seat,
)
from .updates import CFRUpdateRule, update_rule


_ROOT = Path(__file__).parents[2]
_CONFIG = _ROOT / "experiments/configs/h32-continuation-depth-ledger-v1.json"
_OUTPUT = _ROOT / "experiments/results/h32-continuation-depth-ledger-v1.json"
_SOURCE = _ROOT / "experiments/results/h32-fresh-panel-source-blueprints-v1.json"
_MANIFEST = _ROOT / "experiments/results/h32-action-conditioned-posterior-manifest-v1.json"
_PREFLIGHT = _ROOT / "experiments/results/h32-continuation-root-preflight-v1.json"
_ONE_STEP_LEDGER = _ROOT / "experiments/results/h32-continuation-root-ledger-v1.json"
_PARENT_DECISION = _ROOT / "docs/decisions/ADR-0228-continuation-root-delivers-exact-safe-value-on-all-twelve-targets.md"
_IMPLEMENTATION = Path(__file__)
_TEST = _ROOT / "tests/test_h32_continuation_depth_ledger.py"

_PATHS = {
    "expected_source_result_sha256": _SOURCE,
    "expected_manifest_result_sha256": _MANIFEST,
    "expected_preflight_result_sha256": _PREFLIGHT,
    "expected_one_step_ledger_result_sha256": _ONE_STEP_LEDGER,
    "expected_parent_decision_sha256": _PARENT_DECISION,
    "expected_continuation_implementation_sha256": _ROOT / "src/pontius/continuation_public_tree_tensor.py",
    "expected_setup_implementation_sha256": _ROOT / "src/pontius/h32_continuation_root_ledger.py",
    "expected_strategy_trial_implementation_sha256": _ROOT / "src/pontius/h32_continuation_root_strategy_trial.py",
    "expected_device_cfr_sha256": _ROOT / "src/pontius/device_fold_resident_leaf_adjoint_cfr.py",
    "expected_device_affine_sha256": _ROOT / "src/pontius/device_fold_selector_stable_affine_response.py",
    "expected_affine_semantics_sha256": _ROOT / "src/pontius/selector_stable_affine_response.py",
    "expected_update_rules_sha256": _ROOT / "src/pontius/updates.py",
    "expected_depth_implementation_sha256": _IMPLEMENTATION,
    "expected_control_test_sha256": _TEST,
}


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required continuation depth input is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _finite_tree(value: Any) -> bool:
    if isinstance(value, Mapping):
        return all(_finite_tree(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return all(_finite_tree(item) for item in value)
    if isinstance(value, float):
        return math.isfinite(value)
    return True


def recover_discounted_step_regret_deltas(
    before: Mapping[str, Mapping[Any, float]],
    after: Mapping[str, Mapping[Any, float]],
    *,
    rule: CFRUpdateRule,
    iteration: int,
) -> dict[str, dict[Any, float]]:
    """Invert the final CFR discount and recover the latest instantaneous row."""

    if isinstance(iteration, bool) or iteration < 1:
        raise ValueError("regret recovery iteration must be positive")
    if set(before) != set(after):
        raise ValueError("regret recovery schemas differ")
    positive_factor = rule.discount_regret(1.0, iteration)
    negative_factor = -rule.discount_regret(-1.0, iteration)
    if positive_factor <= 0.0 or negative_factor <= 0.0:
        raise ValueError("regret recovery requires invertible discount factors")
    result: dict[str, dict[Any, float]] = {}
    for key in sorted(before):
        if set(before[key]) != set(after[key]):
            raise ValueError("regret recovery action schemas differ")
        row = {}
        for action in before[key]:
            final = float(after[key][action])
            prior = float(before[key][action])
            if not math.isfinite(final) or not math.isfinite(prior):
                raise ValueError("regret recovery values must be finite")
            factor = positive_factor if final >= 0.0 else negative_factor
            row[action] = final / factor - prior
        result[key] = row
    return result


def depth_hard_ledger_ms(
    *,
    step_ms: tuple[float, ...],
    candidate_ms: tuple[float, ...],
    certificate_reserve_ms: float,
    emission_reserve_ms: float,
) -> float:
    values = (*step_ms, *candidate_ms, certificate_reserve_ms, emission_reserve_ms)
    if not step_ms or not candidate_ms or any(
        not math.isfinite(value) or value < 0.0 for value in values
    ):
        raise ValueError("depth ledger requires finite nonnegative measured rows")
    return math.fsum(values)


def _parse_config(config: dict[str, Any]) -> dict[str, Any]:
    for field, path in _PATHS.items():
        if config.get(field) != _sha256(path):
            raise ValueError(f"continuation depth provenance mismatch: {field}")
    exact = {
        "evidence_stage": "preregistered_after_adr0228_before_any_second_step_affine_value_or_new_strategy_label",
        "seed": 20260822,
        "scope": "paired_label_free_one_step_and_two_step_continuation_depth_arms_all_twelve_retained_targets",
        "arm_order": "even_target_index_one_then_two_odd_target_index_two_then_one",
        "direction_rule": "pure_regret_vertex_from_exactly_recovered_latest_step_instantaneous_dcfr_regret_delta",
        "candidate_order": "continuation_public_tree_preorder_then_actor_then_full_public_history",
        "hard_ledger_rule": "all_warm_steps_plus_all_thirty_one_tier_b_rows_plus_1250ms_certificate_reserve_plus_1000ms_emission_reserve",
        "promotion_rule": "authorize_fresh_held_out_one_versus_two_step_value_trial_only_if_every_two_step_hard_ledger_is_at_most_15000ms",
        "decision_budget_ms": 15000.0,
        "certificate_reserve_ms": 1250.0,
        "emission_reserve_ms": 1000.0,
        "pot": 12.0,
        "stack": 30.0,
        "bet_size": 3.0,
        "players": 6,
        "hands_per_player": 32,
        "axis_seed": 20260819,
        "mixture_components": 3,
        "split_index": 3,
        "query_chunk_records": 256,
        "solver_variant": "dcfr",
        "warm_regret_mass_payoff_fraction": 0.1,
        "depth_arms": [1, 2],
        "maximum_feature_width_per_batch": 384,
        "selector_margin_allowance": 2e-11,
        "required_numpy_version": "2.5.2",
        "required_scipy_version": "1.18.0",
        "required_cupy_version": "14.2.0",
        "required_cuda_runtime_version": 13020,
        "minimum_cuda_driver_version": 13000,
        "required_compute_capability": "120",
        "cuda_dll_environment_variable": "PONTIUS_CUDA_DLL_DIRECTORY",
        "label_policy": "zero_quality_rows_zero_affine_values_zero_certificates_zero_new_strategy_labels",
    }
    for field, expected in exact.items():
        if config.get(field) != expected:
            raise ValueError(f"continuation depth field differs from ADR-0229: {field}")
    if len(config.get("targets", ())) != 12:
        raise ValueError("continuation depth ledger requires all twelve targets")
    gates = {
        "expected_targets": 12,
        "expected_arms": 24,
        "expected_warm_steps": 36,
        "expected_blocks_per_arm": 31,
        "expected_information_sets_per_arm": 992,
        "expected_candidate_rows": 744,
        "expected_opponent_rows": 3720,
        "maximum_affine_intercept_error": 2e-11,
        "maximum_warm_start_probability_error": 1e-12,
        "maximum_warm_start_mean_total_variation": 1e-13,
        "maximum_step_ms": 60000.0,
        "maximum_candidate_ms": 60000.0,
        "maximum_gpu_pool_bytes": 12000000000,
        "minimum_physical_free_bytes": 1000000000,
        "maximum_total_seconds": 1800.0,
        "require_clean_git_state": True,
        "require_parents_passed": True,
        "require_counterbalanced_order": True,
        "require_warm_start_identity": True,
        "require_complete_block_partition": True,
        "require_convex_scope": True,
        "require_five_opponent_calls": True,
        "require_zero_own_contractions": True,
        "require_latest_step_recovery": True,
        "require_blueprint_emission": True,
        "require_new_strategy_labels_zero": True,
        "require_strategy_population_claim_null": True,
        "require_finite": True,
    }
    if config.get("gates") != gates:
        raise ValueError("continuation depth gates differ from ADR-0229")
    return {
        **config,
        "targets": tuple(dict(row) for row in config["targets"]),
        "gates": gates,
    }


def _step_row(solver: Any, wall_ms: float) -> dict[str, Any]:
    if solver.last_step_work is None:
        raise AssertionError("continuation depth step emitted no work")
    works = [row.resident_work for row in solver.last_step_work.traversers]
    return {
        "iteration": solver.iteration,
        "wall_ms": wall_ms,
        "terminal_contraction_ms": solver.last_step_work.terminal_contraction_ms,
        **_work_ledger(works),
    }


def _run_arm(
    parsed: Mapping[str, Any],
    source_parent: Mapping[str, Any],
    spec: Mapping[str, Any],
    *,
    depth: int,
    cp: Any,
) -> dict[str, Any]:
    objects = _setup(parsed, source_parent, spec)
    layout = objects["layout"]
    belief = objects["belief"]
    blueprint = objects["blueprint"]
    context = objects["context"]
    shared = objects["shared"]
    gpu = objects["gpu"]
    solver = DeviceFoldResidentLeafAdjointPublicTreeCFR(
        layout,
        objects["workspace"],
        objects["sparse"],
        objects["automata"],
        str(parsed["solver_variant"]),
        belief_cache=context.belief_cache,
        automaton_caches=shared.automaton_caches,
        cupy_sparse=gpu,
        maximum_feature_width_per_batch=int(parsed["maximum_feature_width_per_batch"]),
        hands_by_player=belief.hands_by_player,
        record_to_hand_backend="gpu_cupy",
    )
    warm_mass = float(parsed["warm_regret_mass_payoff_fraction"]) * float(
        layout.game.payoff_span
    )
    solver.warm_start(blueprint, warm_mass)
    warm_distance = _policy_distance(blueprint, solver.current_strategy())
    release_cupy_memory_pool()
    memory_rows = [_memory_snapshot(cp)]
    step_rows = []
    latest_delta = None
    rule = update_rule(str(parsed["solver_variant"]))
    for expected_iteration in range(1, depth + 1):
        before = solver.regret_table()
        cp.cuda.runtime.deviceSynchronize()
        started = time.perf_counter()
        solver.step()
        cp.cuda.runtime.deviceSynchronize()
        wall_ms = (time.perf_counter() - started) * 1000.0
        after = solver.regret_table()
        latest_delta = recover_discounted_step_regret_deltas(
            before,
            after,
            rule=rule,
            iteration=expected_iteration,
        )
        step_rows.append(_step_row(solver, wall_ms))
        memory_rows.append(_memory_snapshot(cp))
    if latest_delta is None:
        raise AssertionError("continuation depth arm ran no steps")
    current = solver.current_strategy()
    blocks = _ordered_blocks(layout, blueprint, current)
    source_gains = tuple(
        float(cache.source_evaluation.deviation_gain)
        for cache in context.response_caches
    )
    candidate_rows = []
    maximum_intercept_error = 0.0
    for index, block in enumerate(blocks):
        cp.cuda.runtime.deviceSynchronize()
        started = time.perf_counter()
        seat = int(block["acting_seat"])
        keys = tuple(block["information_keys"])
        endpoint = build_regret_vertex_candidate(blueprint, latest_delta, keys)
        probabilities = compile_policy_probability_tape(
            layout, belief.hands_by_player, endpoint
        )
        own = evaluate_selector_stable_affine_leaf_adjoint_seat(
            context.response_caches[seat],
            probabilities,
            acting_player=seat,
            selector_margin_allowance=float(parsed["selector_margin_allowance"]),
            maximum_feature_width_per_batch=int(parsed["maximum_feature_width_per_batch"]),
            belief_cache=context.belief_cache,
            automaton_cache=shared.automaton_caches[seat],
            cupy_sparse=gpu,
        )
        opponents = []
        works = []
        for target_player in range(6):
            if target_player == seat:
                continue
            measured = evaluate_device_fold_selector_stable_affine_leaf_adjoint_seat(
                context.response_caches[target_player],
                probabilities,
                acting_player=seat,
                selector_margin_allowance=float(parsed["selector_margin_allowance"]),
                maximum_feature_width_per_batch=int(parsed["maximum_feature_width_per_batch"]),
                belief_cache=context.belief_cache,
                automaton_cache=shared.automaton_caches[target_player],
                cupy_sparse=gpu,
                record_to_hand_backend="gpu_cupy",
            )
            opponents.append(measured.semantic)
            if measured.work is not None:
                works.append(measured.work)
        cp.cuda.runtime.deviceSynchronize()
        wall_ms = (time.perf_counter() - started) * 1000.0
        affine_rows = [own, *opponents]
        maximum_intercept_error = max(
            maximum_intercept_error,
            max(
                abs(
                    float(row.deviation_gain_intercept)
                    - source_gains[row.target_player]
                )
                for row in affine_rows
            ),
        )
        candidate_rows.append(
            {
                "candidate_index": index,
                "acting_seat": seat,
                "public_history": block["public_history"],
                "information_set_count": block["information_set_count"],
                "changed_entry_count": block["changed_entry_count"],
                "convex_scope": direction_has_convex_scope(block),
                "endpoint_policy_sha256": policy_digest(endpoint),
                "opponent_calls": len(opponents),
                "own_affected_terminal_contractions": own.affected_terminal_contractions,
                "opponent_affected_terminal_contractions": sum(
                    row.affected_terminal_contractions for row in opponents
                ),
                "maximum_terminal_middle_rank": max(
                    (row.maximum_terminal_middle_rank for row in opponents),
                    default=0,
                ),
                "complete_tier_b_candidate_ms": wall_ms,
                "device_work": _work_ledger(works),
            }
        )
        memory_rows.append(_memory_snapshot(cp))
    hard_ledger = depth_hard_ledger_ms(
        step_ms=tuple(float(row["wall_ms"]) for row in step_rows),
        candidate_ms=tuple(
            float(row["complete_tier_b_candidate_ms"]) for row in candidate_rows
        ),
        certificate_reserve_ms=float(parsed["certificate_reserve_ms"]),
        emission_reserve_ms=float(parsed["emission_reserve_ms"]),
    )
    result = {
        "depth": depth,
        "warm_start_distance": warm_distance,
        "step_rows": step_rows,
        "latest_step_recovery_iteration": depth,
        "latest_step_delta_digest": hashlib.sha256(
            json.dumps(
                {
                    key: {str(action): value for action, value in row.items()}
                    for key, row in latest_delta.items()
                },
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            ).encode("utf-8")
        ).hexdigest(),
        "changed_information_set_count": sum(
            row["information_set_count"] for row in candidate_rows
        ),
        "candidate_rows": candidate_rows,
        "maximum_affine_intercept_error": maximum_intercept_error,
        "hard_ledger_ms": hard_ledger,
        "deadline_headroom_ms": float(parsed["decision_budget_ms"]) - hard_ledger,
        "memory_rows": memory_rows,
        "emitted_policy_sha256": policy_digest(blueprint),
        "restricted_blueprint_policy_sha256": policy_digest(blueprint),
        "quality_rows": 0,
        "affine_values_serialized": 0,
        "certificates": 0,
        "new_strategy_labels": 0,
    }
    del solver
    objects.clear()
    gc.collect()
    release_cupy_memory_pool()
    return result


def run_h32_continuation_depth_ledger(
    config_path: Path = _CONFIG,
    output_path: Path = _OUTPUT,
) -> dict[str, Any]:
    started = time.perf_counter()
    parsed = _parse_config(json.loads(config_path.read_text(encoding="utf-8")))
    git = _strict_git_metadata()
    cp, runtime = _validate_runtime(parsed)
    source_parent = json.loads(_SOURCE.read_text(encoding="utf-8"))
    manifest = json.loads(_MANIFEST.read_text(encoding="utf-8"))
    preflight = json.loads(_PREFLIGHT.read_text(encoding="utf-8"))
    one_step_parent = json.loads(_ONE_STEP_LEDGER.read_text(encoding="utf-8"))
    target_rows = []
    execution_order = []
    for target_index, spec in enumerate(parsed["targets"]):
        depths = (1, 2) if target_index % 2 == 0 else (2, 1)
        arms = []
        for depth in depths:
            execution_order.append(
                {"target_index": target_index, "target_id": spec["target_id"], "depth": depth}
            )
            arms.append(
                _run_arm(parsed, source_parent, spec, depth=depth, cp=cp)
            )
        target_rows.append(
            {
                "target_index": target_index,
                "target_id": spec["target_id"],
                "execution_order": list(depths),
                "arms": sorted(arms, key=lambda row: row["depth"]),
            }
        )
    arms = [arm for target in target_rows for arm in target["arms"]]
    candidates = [row for arm in arms for row in arm["candidate_rows"]]
    memory_rows = [row for arm in arms for row in arm["memory_rows"]]
    total_seconds = time.perf_counter() - started
    gate = parsed["gates"]
    gates = {
        "clean_git": (not git["dirty"]) == gate["require_clean_git_state"],
        "parents_passed": bool(
            manifest["passed"] and preflight["passed"] and one_step_parent["passed"]
        )
        == gate["require_parents_passed"],
        "target_count": len(target_rows) == gate["expected_targets"],
        "arm_count": len(arms) == gate["expected_arms"],
        "warm_step_count": sum(len(arm["step_rows"]) for arm in arms)
        == gate["expected_warm_steps"],
        "counterbalanced_order": all(
            target["execution_order"]
            == ([1, 2] if target["target_index"] % 2 == 0 else [2, 1])
            for target in target_rows
        )
        == gate["require_counterbalanced_order"],
        "block_counts": all(
            len(arm["candidate_rows"]) == gate["expected_blocks_per_arm"]
            and arm["changed_information_set_count"]
            == gate["expected_information_sets_per_arm"]
            for arm in arms
        ),
        "candidate_count": len(candidates) == gate["expected_candidate_rows"],
        "opponent_row_count": sum(row["opponent_calls"] for row in candidates)
        == gate["expected_opponent_rows"],
        "warm_start_identity": max(
            arm["warm_start_distance"]["maximum_probability_error"] for arm in arms
        )
        <= gate["maximum_warm_start_probability_error"]
        and max(
            arm["warm_start_distance"]["mean_total_variation"] for arm in arms
        )
        <= gate["maximum_warm_start_mean_total_variation"],
        "complete_block_partition": all(
            arm["changed_information_set_count"]
            == sum(row["information_set_count"] for row in arm["candidate_rows"])
            for arm in arms
        )
        == gate["require_complete_block_partition"],
        "convex_scope": all(row["convex_scope"] for row in candidates)
        == gate["require_convex_scope"],
        "five_opponent_calls": all(row["opponent_calls"] == 5 for row in candidates)
        == gate["require_five_opponent_calls"],
        "zero_own_contractions": all(
            row["own_affected_terminal_contractions"] == 0 for row in candidates
        )
        == gate["require_zero_own_contractions"],
        "latest_step_recovery": all(
            arm["latest_step_recovery_iteration"] == arm["depth"] for arm in arms
        )
        == gate["require_latest_step_recovery"],
        "affine_intercepts": max(
            arm["maximum_affine_intercept_error"] for arm in arms
        )
        <= gate["maximum_affine_intercept_error"],
        "step_time": max(
            row["wall_ms"] for arm in arms for row in arm["step_rows"]
        )
        <= gate["maximum_step_ms"],
        "candidate_time": max(
            row["complete_tier_b_candidate_ms"] for row in candidates
        )
        <= gate["maximum_candidate_ms"],
        "gpu_pool": max(row["gpu_pool_total_bytes"] for row in memory_rows)
        <= gate["maximum_gpu_pool_bytes"],
        "physical_free": min(row["gpu_free_bytes"] for row in memory_rows)
        >= gate["minimum_physical_free_bytes"],
        "blueprint_emission": all(
            arm["emitted_policy_sha256"] == arm["restricted_blueprint_policy_sha256"]
            for arm in arms
        )
        == gate["require_blueprint_emission"],
        "new_strategy_labels_zero": (
            sum(arm["new_strategy_labels"] for arm in arms) == 0
        )
        == gate["require_new_strategy_labels_zero"],
        "strategy_population_claim_null": True
        == gate["require_strategy_population_claim_null"],
        "total_time": total_seconds <= gate["maximum_total_seconds"],
        "finite": _finite_tree(target_rows) == gate["require_finite"],
    }
    gates["passed"] = all(gates.values())
    one_arms = [arm for arm in arms if arm["depth"] == 1]
    two_arms = [arm for arm in arms if arm["depth"] == 2]
    promotion = all(arm["deadline_headroom_ms"] >= 0.0 for arm in two_arms)
    result = {
        "schema_version": 1,
        "status": "h32_continuation_depth_ledger_executed",
        "environment": {**environment_metadata(), "runtime": runtime, "git": git},
        "config_sha256": _sha256(config_path),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "execution_order": execution_order,
        "target_rows": target_rows,
        "aggregate": {
            "one_step_minimum_hard_ledger_ms": min(arm["hard_ledger_ms"] for arm in one_arms),
            "one_step_median_hard_ledger_ms": float(np.median([arm["hard_ledger_ms"] for arm in one_arms])),
            "one_step_maximum_hard_ledger_ms": max(arm["hard_ledger_ms"] for arm in one_arms),
            "two_step_minimum_hard_ledger_ms": min(arm["hard_ledger_ms"] for arm in two_arms),
            "two_step_median_hard_ledger_ms": float(np.median([arm["hard_ledger_ms"] for arm in two_arms])),
            "two_step_maximum_hard_ledger_ms": max(arm["hard_ledger_ms"] for arm in two_arms),
            "minimum_two_step_headroom_ms": min(arm["deadline_headroom_ms"] for arm in two_arms),
            "maximum_two_step_headroom_ms": max(arm["deadline_headroom_ms"] for arm in two_arms),
            "median_incremental_second_step_ms": float(
                np.median([arm["step_rows"][1]["wall_ms"] for arm in two_arms])
            ),
            "maximum_incremental_second_step_ms": max(
                arm["step_rows"][1]["wall_ms"] for arm in two_arms
            ),
            "maximum_affine_intercept_error": max(
                arm["maximum_affine_intercept_error"] for arm in arms
            ),
            "minimum_gpu_free_bytes": min(row["gpu_free_bytes"] for row in memory_rows),
            "maximum_gpu_pool_total_bytes": max(
                row["gpu_pool_total_bytes"] for row in memory_rows
            ),
            "promotion_threshold_met": promotion,
        },
        "methodology": {
            "quality_rows": sum(arm["quality_rows"] for arm in arms),
            "affine_values_serialized": sum(arm["affine_values_serialized"] for arm in arms),
            "certificates": sum(arm["certificates"] for arm in arms),
            "new_strategy_labels": sum(arm["new_strategy_labels"] for arm in arms),
        },
        "gates": gates,
        "passed": gates["passed"],
        "decision": (
            "authorize_fresh_held_out_continuation_depth_value_preregistration"
            if gates["passed"] and promotion
            else "retain_proven_one_step_continuation_path"
            if gates["passed"]
            else "reject_continuation_depth_ledger"
        ),
        "emitted_policy": "immutable_restricted_blueprint_only",
        "strategy_population_claim": None,
        "total_seconds": total_seconds,
        "limitations": [
            "Retained opened contexts are used only for label-free paired timing and structural work.",
            "No affine coefficient, envelope, quality row, certificate, or new strategy label is serialized.",
            "Deadline fit authorizes only a fresh held-out depth comparison, not a quality claim for two steps.",
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
    result = run_h32_continuation_depth_ledger(args.config, args.output)
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
