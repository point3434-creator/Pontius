"""Frozen common-game action-width replication on the original h32 board."""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import math
from pathlib import Path
import time
from typing import Any

import numpy as np

from . import h32_action_width_quality_audit as action_width
from .cupy_sparse_incidence import (
    CuPyBidirectionalIncidence,
    release_cupy_memory_pool,
)
from .fresh_h32_strategy_transfer_audit import _belief_digest
from .h32_affine_resident_cache_preflight import (
    _strict_git_metadata,
    _validate_runtime,
)
from .h32_second_board_resident_cache_preflight import (
    _project_parent_descriptor,
    compute_label_free_target_identity_rows,
    parse_h32_second_board_cache_config,
)
from .h32_warm_search_acceptance_audit import (
    _source_policies,
    build_target_belief,
    parse_h32_warm_search_config,
)
from .leaf_adjoint_checkpoint_ladder_audit import _build_case
from .multi_size_affine_resident_leaf_adjoint_evaluation import (
    evaluate_multi_size_affine_resident_profile,
)
from .multi_size_leaf_adjoint import (
    build_multi_size_leaf_adjoint_terminal_automata,
)
from .multi_size_policy_bridge import embed_one_size_policy
from .real_policy import policy_digest
from .reporting import environment_metadata
from .river import parse_cards
from .showdown_value_rank_screen import _rank_codes


_ROOT = Path(__file__).parents[2]
_CONFIG = (
    _ROOT / "experiments" / "configs" / "h32-second-board-action-width-v1.json"
)
_OUTPUT = (
    _ROOT / "experiments" / "results" / "h32-second-board-action-width-v1.json"
)
_CACHE_PREFLIGHT = (
    _ROOT / "experiments" / "results" / "h32-second-board-resident-cache-v1.json"
)
_CACHE_PREFLIGHT_CONFIG = (
    _ROOT / "experiments" / "configs" / "h32-second-board-resident-cache-v1.json"
)
_CACHE_PREFLIGHT_IMPLEMENTATION = (
    _ROOT / "src" / "pontius" / "h32_second_board_resident_cache_preflight.py"
)
_WARM_PARENT = (
    _ROOT / "experiments" / "results" / "h32-warm-search-acceptance-v1.json"
)
_WARM_CONFIG = (
    _ROOT / "experiments" / "configs" / "h32-warm-search-acceptance-v1.json"
)
_LADDER_SOURCE = (
    _ROOT / "experiments" / "results" / "leaf-adjoint-checkpoint-ladder-v2.json"
)
_EXTENSION_SOURCE = (
    _ROOT / "experiments" / "results" / "leaf-adjoint-checkpoint-extension-v1.json"
)
_ACTION_WIDTH_PARENT = (
    _ROOT / "experiments" / "results" / "h32-action-width-quality-v2.json"
)
_ACTION_WIDTH_CONFIG = (
    _ROOT / "experiments" / "configs" / "h32-action-width-quality-v1.json"
)
_ACTION_WIDTH_IMPLEMENTATION = (
    _ROOT / "src" / "pontius" / "h32_action_width_quality_audit.py"
)
_ACCEPTANCE_PARENT = (
    _ROOT / "experiments" / "results" / "h32-acceptance-semantics-replay-v1.json"
)
_ACCEPTANCE_DECISION = (
    _ROOT
    / "docs"
    / "decisions"
    / "ADR-0106-fixed-blueprint-envelope-is-order-independent-and-recovers-safe-value.md"
)
_IMPLEMENTATION = Path(__file__)
_CONTROL_TEST = _ROOT / "tests" / "test_h32_second_board_action_width_quality.py"

_CONFIG_FIELDS = {
    "evidence_stage",
    "expected_cache_preflight_sha256",
    "expected_cache_preflight_config_sha256",
    "expected_cache_preflight_implementation_sha256",
    "expected_warm_parent_sha256",
    "expected_warm_config_sha256",
    "expected_ladder_source_sha256",
    "expected_extension_source_sha256",
    "expected_action_width_parent_sha256",
    "expected_action_width_config_sha256",
    "expected_action_width_implementation_sha256",
    "expected_acceptance_parent_sha256",
    "expected_acceptance_decision_sha256",
    "expected_audit_implementation_sha256",
    "expected_control_test_sha256",
    "board",
    "pot",
    "stack",
    "one_size_bet",
    "two_size_bets",
    "expected_one_size_payoff_span",
    "expected_two_size_payoff_span",
    "players",
    "hands_per_player",
    "range_families",
    "target_shifts",
    "target_order",
    "arm_order_by_target",
    "target_belief_sha256_by_target",
    "solver_variant",
    "source_blueprint_point",
    "warm_regret_mass_payoff_fraction",
    "construction_and_planning_budget_ms",
    "reserved_complete_step_ms",
    "maximum_complete_steps",
    "candidate_rule",
    "interpolation_alpha",
    "fixed_seat_order",
    "acceptance_guard_normalized",
    "known_original_board_one_size_evidence",
    "prior_sized_board_outcome",
    "strategy_claim_policy",
    "mixture_components",
    "split_index",
    "query_chunk_records",
    "maximum_feature_width_per_batch",
    "required_numpy_version",
    "required_scipy_version",
    "required_cupy_version",
    "required_cuda_runtime_version",
    "minimum_cuda_driver_version",
    "required_compute_capability",
    "cuda_dll_environment_variable",
    "gates",
}


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required frozen input is unavailable: {path}")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def _warm_parent_target(parent: dict[str, Any], family: str, shift: str) -> dict[str, Any]:
    family_row = next(
        row for row in parent["family_rows"] if row["range_family"] == family
    )
    return next(row for row in family_row["targets"] if row["target_shift"] == shift)


def source_blueprint_from_frozen_checkpoints(
    ladder: dict[str, Any],
    extension: dict[str, Any],
    warm_parent: dict[str, Any],
    *,
    family: str,
) -> tuple[dict[str, dict[str, float]], dict[str, Any]]:
    """Reconstruct the exact original-board average-64 one-size incumbent."""

    _, _, blueprint, checkpoint_identity = _source_policies(
        ladder,
        extension,
        family=family,
    )
    expected = next(
        row for row in warm_parent["family_rows"] if row["range_family"] == family
    )
    digest = policy_digest(blueprint)
    expected_digest = expected["source_policy_digests"]["blueprint_average64"]
    diagnostics = {
        "range_family": family,
        "source_blueprint_point": "64:average",
        "policy_sha256": digest,
        "expected_policy_sha256": expected_digest,
        "checkpoint_policy_identity": checkpoint_identity,
        "parent_policy_identity": digest == expected_digest,
    }
    diagnostics["passed"] = bool(
        diagnostics["checkpoint_policy_identity"]
        and diagnostics["parent_policy_identity"]
    )
    return blueprint, diagnostics


def parse_h32_second_board_action_width_config(
    config: dict[str, Any],
) -> dict[str, Any]:
    """Validate the complete revealed-board action-width replication."""

    if set(config) != _CONFIG_FIELDS:
        raise ValueError("second-board action-width fields differ from ADR-0140")
    frozen = {
        "evidence_stage": (
            "preregistered_after_adr0139_before_any_original_board_h32_sized_"
            "policy_construction_or_common_game_quality_measurement"
        ),
        "board": ["2c", "7d", "9h", "Js", "Qc"],
        "pot": 12.0,
        "stack": 30.0,
        "one_size_bet": 3.0,
        "two_size_bets": [3.0, 6.0],
        "expected_one_size_payoff_span": 30.0,
        "expected_two_size_payoff_span": 48.0,
        "players": 6,
        "hands_per_player": 32,
        "range_families": ["balanced", "blocker_heavy"],
        "target_shifts": [
            "local_blocker_seat3_x2",
            "all_seat_strength_1_to2",
        ],
        "target_order": [
            "balanced/local_blocker_seat3_x2",
            "balanced/all_seat_strength_1_to2",
            "blocker_heavy/local_blocker_seat3_x2",
            "blocker_heavy/all_seat_strength_1_to2",
        ],
        "arm_order_by_target": [
            "one_then_two",
            "two_then_one",
            "two_then_one",
            "one_then_two",
        ],
        "solver_variant": "dcfr",
        "source_blueprint_point": "64:average",
        "warm_regret_mass_payoff_fraction": 0.1,
        "construction_and_planning_budget_ms": 90000.0,
        "reserved_complete_step_ms": 35000.0,
        "maximum_complete_steps": 8,
        "candidate_rule": (
            "deduplicated_current1_then_current1_current2_alpha050_then_"
            "deadline_current_then_deadline_average"
        ),
        "interpolation_alpha": 0.5,
        "fixed_seat_order": [0, 1, 2, 3, 4, 5],
        "acceptance_guard_normalized": 1e-10,
        "known_original_board_one_size_evidence": (
            "revealed_complete_union_selected_nonblueprint_on_both_local_"
            "targets_and_blueprint_on_both_strength_targets"
        ),
        "prior_sized_board_outcome": (
            "fresh_board_both_arms_abstained_on_all_four_targets"
        ),
        "strategy_claim_policy": "always_null",
        "mixture_components": 3,
        "split_index": 3,
        "query_chunk_records": 256,
        "maximum_feature_width_per_batch": 384,
        "required_numpy_version": "2.5.2",
        "required_scipy_version": "1.18.0",
        "required_cupy_version": "14.2.0",
        "required_cuda_runtime_version": 13020,
        "minimum_cuda_driver_version": 13000,
        "required_compute_capability": "120",
        "cuda_dll_environment_variable": "PONTIUS_CUDA_DLL_DIRECTORY",
    }
    if any(config[field] != value for field, value in frozen.items()):
        raise ValueError("second-board action-width workload differs from ADR-0140")
    expected_target_digests = {
        "balanced/local_blocker_seat3_x2": (
            "0837fb176c0ef13260c14e230bfb04d79755cdd232b71eabef69b29a2e08ab1a"
        ),
        "balanced/all_seat_strength_1_to2": (
            "587407ff8dea2e735aa68470933e4cd009f71bb147fd40561bfa89dd8290d7e7"
        ),
        "blocker_heavy/local_blocker_seat3_x2": (
            "a59d5c7efbd0fbc441d3986a83a0cf86f890d52cfb5d6a2f4de8d8d3acd708e5"
        ),
        "blocker_heavy/all_seat_strength_1_to2": (
            "221b112ad4407a06ecee2511344f71df93d4469f1572d5ed8569295296c326aa"
        ),
    }
    if config["target_belief_sha256_by_target"] != expected_target_digests:
        raise ValueError("second-board action-width target digests differ")

    sources = {
        "expected_cache_preflight_sha256": _CACHE_PREFLIGHT,
        "expected_cache_preflight_config_sha256": _CACHE_PREFLIGHT_CONFIG,
        "expected_cache_preflight_implementation_sha256": (
            _CACHE_PREFLIGHT_IMPLEMENTATION
        ),
        "expected_warm_parent_sha256": _WARM_PARENT,
        "expected_warm_config_sha256": _WARM_CONFIG,
        "expected_ladder_source_sha256": _LADDER_SOURCE,
        "expected_extension_source_sha256": _EXTENSION_SOURCE,
        "expected_action_width_parent_sha256": _ACTION_WIDTH_PARENT,
        "expected_action_width_config_sha256": _ACTION_WIDTH_CONFIG,
        "expected_action_width_implementation_sha256": (
            _ACTION_WIDTH_IMPLEMENTATION
        ),
        "expected_acceptance_parent_sha256": _ACCEPTANCE_PARENT,
        "expected_acceptance_decision_sha256": _ACCEPTANCE_DECISION,
        "expected_audit_implementation_sha256": _IMPLEMENTATION,
        "expected_control_test_sha256": _CONTROL_TEST,
    }
    for field, path in sources.items():
        if config[field] != _sha256(path):
            raise ValueError(f"second-board action-width source mismatch: {field}")

    cache_config = json.loads(_CACHE_PREFLIGHT_CONFIG.read_text(encoding="utf-8"))
    parse_h32_second_board_cache_config(cache_config)
    warm_config = json.loads(_WARM_CONFIG.read_text(encoding="utf-8"))
    parse_h32_warm_search_config(warm_config)
    action_config = json.loads(_ACTION_WIDTH_CONFIG.read_text(encoding="utf-8"))
    action_width.parse_h32_action_width_quality_config(action_config)

    expected_gates = {
        "expected_target_rows": 4,
        "expected_arm_rows": 8,
        "expected_one_size_public_nodes": 385,
        "expected_two_size_public_nodes": 763,
        "expected_two_size_terminal_groups": 127,
        "expected_one_size_information_sets": 6144,
        "expected_one_size_hand_action_entries": 12288,
        "expected_two_size_information_sets": 12096,
        "expected_two_size_hand_action_entries": 24384,
        "expected_shared_affine_bases": 378,
        "maximum_small_profile_utility_error": 2e-13,
        "maximum_small_quality_error": 2e-11,
        "maximum_small_zero_sum_residual": 2e-11,
        "maximum_complete_step_ms": 35000.0,
        "maximum_arm_construction_and_planning_ms": 90000.0,
        "maximum_cache_compile_ms": 120000.0,
        "maximum_quality_seat_ms": 60000.0,
        "maximum_quality_vector_sum_error": 1e-10,
        "maximum_quality_zero_sum_residual": 1e-9,
        "maximum_gpu_pool_bytes": 12000000000,
        "maximum_total_audit_seconds": 3600.0,
        "require_clean_git_state": True,
        "require_parent_identity": True,
        "require_cache_headroom_safe": True,
        "require_source_blueprint_identity": True,
        "require_target_identity": True,
        "require_common_game_payoff_span": True,
        "require_at_least_one_complete_step_per_arm": True,
        "require_compact_policy_round_trip": True,
        "require_planning_before_quality": True,
        "require_fixed_envelope_cap_compliance": True,
        "require_finite_policies_and_quality": True,
        "require_strategy_claim_null": True,
    }
    if config["gates"] != expected_gates:
        raise ValueError("second-board action-width gates differ from ADR-0140")
    return {
        **config,
        "two_size_bets": tuple(config["two_size_bets"]),
        "range_families": tuple(config["range_families"]),
        "target_shifts": tuple(config["target_shifts"]),
        "target_order": tuple(config["target_order"]),
        "arm_order_by_target": tuple(config["arm_order_by_target"]),
        "fixed_seat_order": tuple(config["fixed_seat_order"]),
        "gates": dict(config["gates"]),
    }


def run_h32_second_board_action_width_audit(
    config_path: Path = _CONFIG,
    output_path: Path = _OUTPUT,
) -> dict[str, Any]:
    """Execute the frozen second-board common-game comparison once."""

    started = time.perf_counter()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    parsed = parse_h32_second_board_action_width_config(config)
    cache_preflight = json.loads(_CACHE_PREFLIGHT.read_text(encoding="utf-8"))
    warm_parent = json.loads(_WARM_PARENT.read_text(encoding="utf-8"))
    warm_config = json.loads(_WARM_CONFIG.read_text(encoding="utf-8"))
    warm_parsed = parse_h32_warm_search_config(warm_config)
    ladder = json.loads(_LADDER_SOURCE.read_text(encoding="utf-8"))
    extension = json.loads(_EXTENSION_SOURCE.read_text(encoding="utf-8"))
    action_parent = json.loads(_ACTION_WIDTH_PARENT.read_text(encoding="utf-8"))
    acceptance_parent = json.loads(_ACCEPTANCE_PARENT.read_text(encoding="utf-8"))
    parent_identity = (
        cache_preflight["passed"]
        and cache_preflight["headroom"]["all_eight_caches_safe"]
        and cache_preflight["h32_steps_executed"] == 0
        and cache_preflight["h32_policies_constructed"] == 0
        and cache_preflight["h32_strategy_quality_evaluations"] == 0
        and cache_preflight["strategy_quality_claim"] is None
        and warm_parent["gates"]["passed"]
        and ladder["gates"]["passed"]
        and extension["gates"]["passed"]
        and action_parent["passed"]
        and action_parent["strategy_quality_claim"] is None
        and acceptance_parent["gates"]["passed"]
        and acceptance_parent["counts"]["new_strategy_evaluations"] == 0
    )
    if not parent_identity:
        raise ValueError("second-board action-width parent identity rejected")

    environment = environment_metadata()
    environment["git"] = _strict_git_metadata()
    cp, runtime = _validate_runtime(parsed)

    target_identity_preflight = compute_label_free_target_identity_rows(
        warm_config,
        warm_parent,
        expected_digests=parsed["target_belief_sha256_by_target"],
    )
    source_blueprint_preflight = []
    for family in parsed["range_families"]:
        _, diagnostics = source_blueprint_from_frozen_checkpoints(
            ladder,
            extension,
            warm_parent,
            family=family,
        )
        source_blueprint_preflight.append(diagnostics)
    if not all(row["passed"] for row in target_identity_preflight):
        raise ValueError("second-board target identity rejected before sized h32 work")
    if not all(row["passed"] for row in source_blueprint_preflight):
        raise ValueError("second-board blueprint identity rejected before sized h32 work")

    small = action_width._small_control(parsed)
    small_passed = (
        small["profile_utility_error"]
        <= parsed["gates"]["maximum_small_profile_utility_error"]
        and small["quality_error"]
        <= parsed["gates"]["maximum_small_quality_error"]
        and small["zero_sum_residual"]
        <= parsed["gates"]["maximum_small_zero_sum_residual"]
        and small["compact_round_trip"]
        and small["one_size_public_nodes"]
        == parsed["gates"]["expected_one_size_public_nodes"]
        and small["two_size_public_nodes"]
        == parsed["gates"]["expected_two_size_public_nodes"]
        and small["two_size_terminal_groups"]
        == parsed["gates"]["expected_two_size_terminal_groups"]
        and small["shared_affine_bases"]
        == parsed["gates"]["expected_shared_affine_bases"]
        and small["two_size_payoff_span"] == parsed["expected_two_size_payoff_span"]
    )
    if not small_passed:
        raise ValueError("small second-board action-width control failed")

    board = parse_cards(*parsed["board"])
    targets = []
    policy_artifacts: dict[str, dict[str, Any]] = {}
    phase_order_records = []
    target_index = 0
    for family in parsed["range_families"]:
        gc.collect()
        release_cupy_memory_pool()
        source_belief, one_layout, sparse, retained = _build_case(
            parsed=warm_parsed,
            board=board,
            hand_count=parsed["hands_per_player"],
            family=family,
        )
        source_workspace, _, one_libraries = retained
        one_blueprint, blueprint_identity = source_blueprint_from_frozen_checkpoints(
            ladder,
            extension,
            warm_parent,
            family=family,
        )
        codes = tuple(
            np.ascontiguousarray(values, dtype=np.int32)
            for values in _rank_codes(board, source_belief.hands_by_player)
        )
        sized_layout = action_width._representative_sized_tree(
            source_belief,
            pot=parsed["pot"],
            stack=parsed["stack"],
            bet_sizes=parsed["two_size_bets"],
        )
        sized_libraries = build_multi_size_leaf_adjoint_terminal_automata(
            sized_layout,
            codes,
            pot=parsed["pot"],
        )
        sized_blueprint = embed_one_size_policy(
            one_layout,
            sized_layout,
            source_belief.hands_by_player,
            one_blueprint,
            retained_bet_size=parsed["one_size_bet"],
        )
        gpu = CuPyBidirectionalIncidence.compile(sparse)
        for shift in parsed["target_shifts"]:
            expected = _warm_parent_target(warm_parent, family, shift)
            target_belief, descriptor = build_target_belief(
                source_belief,
                board=board,
                shift=shift,
                local_blocker_target_seat=warm_parsed[
                    "local_blocker_target_seat"
                ],
            )
            target_key = f"{family}/{shift}"
            target_identity = (
                descriptor == _project_parent_descriptor(expected, shift=shift)
                and _belief_digest(target_belief)
                == parsed["target_belief_sha256_by_target"][target_key]
                and target_belief.hands_by_player == source_belief.hands_by_player
            )
            order_name = parsed["arm_order_by_target"][target_index]
            arm_order = (
                ("one_size", "two_size")
                if order_name == "one_then_two"
                else ("two_size", "one_size")
            )
            arm_rows = {}
            live_by_arm = {}
            for arm in arm_order:
                arm_row, live = action_width._arm_plan(
                    parsed=parsed,
                    cp=cp,
                    arm=arm,
                    source_workspace=source_workspace,
                    target_belief=target_belief,
                    sparse=sparse,
                    gpu=gpu,
                    one_layout=one_layout,
                    one_libraries=one_libraries,
                    sized_layout=sized_layout,
                    sized_libraries=sized_libraries,
                    one_blueprint=one_blueprint,
                    sized_blueprint=sized_blueprint,
                )
                for candidate in arm_row["candidates"]:
                    artifact = candidate.pop("policy_artifact")
                    digest = candidate["policy_sha256"]
                    if digest in policy_artifacts and policy_artifacts[digest] != artifact:
                        raise ValueError("duplicate second-board policy artifacts differ")
                    policy_artifacts[digest] = artifact
                    candidate["policy_artifact_ref"] = digest
                arm_rows[arm] = arm_row
                live_by_arm[arm] = live
            target_planning_finished_at = time.perf_counter()

            gc.collect()
            release_cupy_memory_pool()
            verifier_workspace, verifier_workspace_ms = action_width._target_workspace(
                source_workspace,
                target_belief,
                query_chunk_records=parsed["query_chunk_records"],
            )
            verifier_cache, verifier_belief, verifier_automata = (
                action_width._compile_cache(
                    cp,
                    verifier_workspace,
                    sized_libraries,
                    arm="two_size",
                )
            )
            target_quality_started_at = time.perf_counter()
            phase_order_records.append(
                target_planning_finished_at <= target_quality_started_at
            )
            incumbent_profile = evaluate_multi_size_affine_resident_profile(
                sized_layout,
                verifier_workspace,
                sparse,
                sized_blueprint,
                sized_libraries,
                belief_cache=verifier_belief,
                automaton_caches=verifier_automata,
                cupy_sparse=gpu,
                hands_by_player=target_belief.hands_by_player,
                maximum_feature_width_per_batch=parsed[
                    "maximum_feature_width_per_batch"
                ],
            )
            incumbent = action_width._profile_row(
                "immutable_embedded_blueprint",
                incumbent_profile,
                payoff_span=float(sized_layout.game.payoff_span),
            )
            incumbent_selector_row = {
                "candidate_id": incumbent["candidate_id"],
                "aliases": [incumbent["candidate_id"]],
                "quality": incumbent["quality"],
            }
            verifiers = {}
            for arm in arm_order:
                verified = action_width._verify_candidate_stream(
                    parsed=parsed,
                    layout=sized_layout,
                    workspace=verifier_workspace,
                    sparse=sparse,
                    libraries=sized_libraries,
                    belief_cache=verifier_belief,
                    automaton_caches=verifier_automata,
                    gpu=gpu,
                    hands_by_player=target_belief.hands_by_player,
                    incumbent=incumbent_selector_row,
                    candidates=live_by_arm[arm],
                )
                planning_ms = arm_rows[arm]["construction_and_planning_ms"]
                verified["marginal_decision_ms"] = planning_ms + verified["wall_ms"]
                verified["full_one_shot_decision_ms"] = (
                    planning_ms
                    + verifier_workspace_ms
                    + verifier_cache["cold_construction_ms"]
                    + incumbent["wall_ms"]
                    + verified["wall_ms"]
                )
                reduction = verified["selected_normalized_nash_conv_reduction"]
                verified["selected_normalized_reduction_per_marginal_ms"] = (
                    reduction / verified["marginal_decision_ms"]
                )
                verified["selected_normalized_reduction_per_full_one_shot_ms"] = (
                    reduction / verified["full_one_shot_decision_ms"]
                )
                verifiers[arm] = verified

            target_row = {
                "range_family": family,
                "target_shift": shift,
                "target": target_key,
                "arm_order": order_name,
                "source_blueprint_identity": blueprint_identity,
                "target_descriptor": descriptor,
                "target_belief_sha256": _belief_digest(target_belief),
                "target_identity": target_identity,
                "one_size_payoff_span": float(one_layout.game.payoff_span),
                "two_size_payoff_span": float(sized_layout.game.payoff_span),
                "payoff_span_source": "layout.game.payoff_span",
                "one_size_information_sets": len(one_blueprint),
                "one_size_hand_action_entries": sum(
                    len(row) for row in one_blueprint.values()
                ),
                "two_size_information_sets": len(sized_blueprint),
                "two_size_hand_action_entries": sum(
                    len(row) for row in sized_blueprint.values()
                ),
                "arm_planning": arm_rows,
                "verifier_workspace_compile_ms": verifier_workspace_ms,
                "verifier_cache": verifier_cache,
                "incumbent": incumbent,
                "arm_verification": verifiers,
                "selected_two_minus_one_normalized_reduction": (
                    verifiers["two_size"][
                        "selected_normalized_nash_conv_reduction"
                    ]
                    - verifiers["one_size"][
                        "selected_normalized_nash_conv_reduction"
                    ]
                ),
            }
            targets.append(target_row)
            target_index += 1
            del incumbent_profile, verifier_automata, verifier_belief
            del verifier_workspace, target_belief
            gc.collect()
            release_cupy_memory_pool()
        del gpu
        gc.collect()
        release_cupy_memory_pool()

    total_seconds = time.perf_counter() - started
    gates = parsed["gates"]
    arm_rows = [
        target["arm_planning"][arm]
        for target in targets
        for arm in ("one_size", "two_size")
    ]
    verifier_rows = [
        target["arm_verification"][arm]
        for target in targets
        for arm in ("one_size", "two_size")
    ]
    complete_quality_rows = [target["incumbent"]["quality"] for target in targets]
    complete_quality_rows.extend(
        row["quality"]
        for verifier in verifier_rows
        for row in verifier["candidate_rows"]
        if row["quality"] is not None
    )
    actual_order = tuple(target["target"] for target in targets)
    planning_before_quality = (
        len(phase_order_records) == len(targets)
        and all(phase_order_records)
        and all(
            set(target["arm_planning"]) == {"one_size", "two_size"}
            for target in targets
        )
    )
    strategy_quality_claim = None
    gate_results = {
        "parent_identity": parent_identity == gates["require_parent_identity"],
        "cache_headroom_safe": cache_preflight["headroom"]["all_eight_caches_safe"]
        == gates["require_cache_headroom_safe"],
        "clean_git_state": (not bool(environment["git"]["dirty"]))
        == gates["require_clean_git_state"],
        "small_control": small_passed,
        "source_blueprint_identity": all(
            row["passed"] for row in source_blueprint_preflight
        )
        == gates["require_source_blueprint_identity"],
        "target_count_and_order": (
            len(targets) == gates["expected_target_rows"]
            and actual_order == parsed["target_order"]
        ),
        "arm_count": len(arm_rows) == gates["expected_arm_rows"],
        "target_identity": all(target["target_identity"] for target in targets)
        == gates["require_target_identity"],
        "topology_and_policy_width": all(
            target["one_size_information_sets"]
            == gates["expected_one_size_information_sets"]
            and target["one_size_hand_action_entries"]
            == gates["expected_one_size_hand_action_entries"]
            and target["two_size_information_sets"]
            == gates["expected_two_size_information_sets"]
            and target["two_size_hand_action_entries"]
            == gates["expected_two_size_hand_action_entries"]
            for target in targets
        ),
        "common_game_payoff_span": all(
            target["one_size_payoff_span"] == parsed["expected_one_size_payoff_span"]
            and target["two_size_payoff_span"]
            == parsed["expected_two_size_payoff_span"]
            for target in targets
        )
        == gates["require_common_game_payoff_span"],
        "complete_steps": all(row["completed_steps"] >= 1 for row in arm_rows)
        == gates["require_at_least_one_complete_step_per_arm"],
        "step_ceiling": all(
            step["wall_ms"] <= gates["maximum_complete_step_ms"]
            for row in arm_rows
            for step in row["steps"]
        ),
        "arm_budget": all(
            row["construction_and_planning_ms"]
            <= gates["maximum_arm_construction_and_planning_ms"]
            for row in arm_rows
        ),
        "cache_compile": all(
            row["cache"]["cold_construction_ms"]
            <= gates["maximum_cache_compile_ms"]
            for row in arm_rows
        )
        and all(
            target["verifier_cache"]["cold_construction_ms"]
            <= gates["maximum_cache_compile_ms"]
            for target in targets
        ),
        "canonical_basis_count": all(
            target["arm_planning"]["two_size"]["cache"]["shared_affine_bases"]
            == gates["expected_shared_affine_bases"]
            and target["verifier_cache"]["shared_affine_bases"]
            == gates["expected_shared_affine_bases"]
            for target in targets
        ),
        "compact_policy_round_trip": all(
            candidate["compact_round_trip"]
            for row in arm_rows
            for candidate in row["candidates"]
        )
        == gates["require_compact_policy_round_trip"],
        "planning_before_quality": planning_before_quality
        == gates["require_planning_before_quality"],
        "quality_exactness": all(
            row["quality_vector_sum_error"]
            <= gates["maximum_quality_vector_sum_error"]
            and row["zero_sum_residual"]
            <= gates["maximum_quality_zero_sum_residual"]
            for row in complete_quality_rows
        ),
        "quality_seat_ceiling": all(
            seat["wall_ms"] <= gates["maximum_quality_seat_ms"]
            for target in targets
            for seat in target["incumbent"]["seat_rows"]
        )
        and all(
            seat["wall_ms"] <= gates["maximum_quality_seat_ms"]
            for verifier in verifier_rows
            for candidate in verifier["candidate_rows"]
            for seat in candidate["seat_rows"]
        ),
        "fixed_envelope_cap_compliance": all(
            not verifier["selection"]["selected_violating_seats"]
            for verifier in verifier_rows
        )
        == gates["require_fixed_envelope_cap_compliance"],
        "finite_policies_and_quality": (
            all(row["finite"] for row in arm_rows)
            and all(row["finite"] for row in complete_quality_rows)
        )
        == gates["require_finite_policies_and_quality"],
        "gpu_pool_ceiling": max(
            [row["cache"]["pool_total_bytes"] for row in arm_rows]
            + [
                step["maximum_gpu_pool_bytes"]
                for row in arm_rows
                for step in row["steps"]
            ]
            + [target["verifier_cache"]["pool_total_bytes"] for target in targets]
            + [
                seat["maximum_gpu_pool_total_bytes"]
                for target in targets
                for seat in target["incumbent"]["seat_rows"]
            ]
            + [
                seat["maximum_gpu_pool_total_bytes"]
                for verifier in verifier_rows
                for candidate in verifier["candidate_rows"]
                for seat in candidate["seat_rows"]
            ]
        )
        <= gates["maximum_gpu_pool_bytes"],
        "strategy_claim_null": (strategy_quality_claim is None)
        == gates["require_strategy_claim_null"],
        "wall_time": total_seconds <= gates["maximum_total_audit_seconds"],
    }
    passed = all(gate_results.values())
    one_total = math.fsum(
        target["arm_verification"]["one_size"][
            "selected_normalized_nash_conv_reduction"
        ]
        for target in targets
    )
    two_total = math.fsum(
        target["arm_verification"]["two_size"][
            "selected_normalized_nash_conv_reduction"
        ]
        for target in targets
    )
    result = {
        "schema_version": 1,
        "status": "frozen_h32_second_board_action_width_audit_executed",
        "experiment_type": "h32_revealed_second_board_action_width_replication",
        "config": config,
        "config_sha256": _sha256(config_path),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "source_sha256": {
            field.removeprefix("expected_"): config[field]
            for field in config
            if field.startswith("expected_") and field.endswith("_sha256")
        },
        "environment": {**environment, **runtime},
        "parent_identity": parent_identity,
        "small_control": small,
        "source_blueprint_preflight": source_blueprint_preflight,
        "target_identity_preflight": target_identity_preflight,
        "known_original_board_one_size_evidence": parsed[
            "known_original_board_one_size_evidence"
        ],
        "prior_sized_board_outcome": {
            "disclosure": parsed["prior_sized_board_outcome"],
            "aggregate": action_parent["aggregate_strategy_outcome"],
        },
        "policy_artifacts": policy_artifacts,
        "targets": targets,
        "aggregate_strategy_outcome": {
            "targets": len(targets),
            "one_size_selected_normalized_reduction": one_total,
            "two_size_selected_normalized_reduction": two_total,
            "two_minus_one_selected_normalized_reduction": two_total - one_total,
            "one_size_blueprint_abstentions": sum(
                target["arm_verification"]["one_size"]["selection"][
                    "blueprint_abstention"
                ]
                for target in targets
            ),
            "two_size_blueprint_abstentions": sum(
                target["arm_verification"]["two_size"]["selection"][
                    "blueprint_abstention"
                ]
                for target in targets
            ),
            "outcome_is_not_a_gate": True,
        },
        "gate_results": gate_results,
        "passed": passed,
        "decision": (
            "record_revealed_second_board_diagnostics_without_width_ranking"
            if passed
            else "reject_second_board_action_width_mechanism"
        ),
        "strategy_quality_claim": strategy_quality_claim,
        "timing": {"total_seconds": total_seconds},
        "limitations": [
            (
                "The original board and its historical one-size candidate outcomes "
                "were revealed before this action-width replication."
            ),
            (
                "Both arms are scored in the same two-size game, but this is only "
                "the second sized board and four deterministic target shifts."
            ),
            (
                "The one-size off-tree response below the added bet copies its "
                "small-bet continuation."
            ),
            "Exact verification remains an offline laboratory bill, not a 250 ms deployment path.",
            (
                "No population, full-range, earlier-street, coalition-safety, or "
                "universal action-width claim follows."
            ),
        ],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=_CONFIG)
    parser.add_argument("--output", type=Path, default=_OUTPUT)
    arguments = parser.parse_args()
    result = run_h32_second_board_action_width_audit(
        arguments.config,
        arguments.output,
    )
    outcome = result["aggregate_strategy_outcome"]
    print(
        "h32 second-board action-width audit: "
        f"passed={result['passed']}, "
        f"two_minus_one={outcome['two_minus_one_selected_normalized_reduction']:.12g}, "
        f"wall={result['timing']['total_seconds']:.3f}s"
    )


if __name__ == "__main__":
    main()
