"""Cache-only portability preflight for the second h32 action-width board."""

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

from . import h32_action_width_quality_audit as action_width
from .cupy_sparse_incidence import (
    CuPyBidirectionalIncidence,
    _cupy_modules,
    release_cupy_memory_pool,
)
from .fresh_h32_strategy_transfer_audit import _belief_digest
from .h32_affine_resident_cache_preflight import (
    _strict_git_metadata,
    _validate_runtime,
)
from .h32_warm_search_acceptance_audit import (
    build_target_belief,
    parse_h32_warm_search_config,
)
from .leaf_adjoint_checkpoint_ladder_audit import _build_case
from .multi_size_leaf_adjoint import (
    build_multi_size_leaf_adjoint_terminal_automata,
    multi_size_terminal_groups,
)
from .reporting import environment_metadata
from .river import parse_cards
from .showdown_value_rank_screen import _rank_codes


_ROOT = Path(__file__).parents[2]
_CONFIG = (
    _ROOT / "experiments" / "configs" / "h32-second-board-resident-cache-v1.json"
)
_OUTPUT = (
    _ROOT / "experiments" / "results" / "h32-second-board-resident-cache-v1.json"
)
_WARM_PARENT = (
    _ROOT / "experiments" / "results" / "h32-warm-search-acceptance-v1.json"
)
_WARM_CONFIG = (
    _ROOT / "experiments" / "configs" / "h32-warm-search-acceptance-v1.json"
)
_ACTION_WIDTH_PARENT = (
    _ROOT / "experiments" / "results" / "h32-action-width-quality-v2.json"
)
_ACTION_WIDTH_DECISION = (
    _ROOT
    / "docs"
    / "decisions"
    / "ADR-0137-target-identity-successor-passes-without-action-width-ranking.md"
)
_ACTION_WIDTH_CONFIG = (
    _ROOT / "experiments" / "configs" / "h32-action-width-quality-v1.json"
)
_ACTION_WIDTH_IMPLEMENTATION = (
    _ROOT / "src" / "pontius" / "h32_action_width_quality_audit.py"
)
_WARM_IMPLEMENTATION = (
    _ROOT / "src" / "pontius" / "h32_warm_search_acceptance_audit.py"
)
_CACHE_PARENT = (
    _ROOT / "experiments" / "results" / "h32-canonical-affine-cache-replay-v1.json"
)
_CACHE_PARENT_CONFIG = (
    _ROOT / "experiments" / "configs" / "h32-canonical-affine-cache-replay-v1.json"
)
_IMPLEMENTATION = Path(__file__)
_CONTROL_TEST = _ROOT / "tests" / "test_h32_second_board_resident_cache_preflight.py"

_COMMON_CONSTRUCTION_FIELDS = frozenset(
    {
        "shift",
        "likelihood_minimum",
        "likelihood_maximum",
        "likelihood_mean",
        "positive_likelihoods",
        "hand_axes_identity",
        "tie_rule",
    }
)
_CONSTRUCTION_FIELDS_BY_SHIFT = {
    "local_blocker_seat3_x2": _COMMON_CONSTRUCTION_FIELDS
    | {
        "selected_seat",
        "selected_hand_index",
        "selected_hand",
        "opponent_axis_card_overlap_count",
    },
    "all_seat_strength_1_to2": _COMMON_CONSTRUCTION_FIELDS
    | {"distinct_strength_levels_by_seat"},
}
_PARENT_MEASUREMENT_FIELDS = frozenset(
    {
        "source_partition",
        "target_partition",
        "target_to_source_partition_ratio",
        "marginal_total_variations",
        "mean_marginal_total_variation",
        "maximum_marginal_total_variation",
        "marginal_measurement_ms",
    }
)

# Computed by the label-free preflight before the ADR/config freeze.
_FROZEN_TARGET_DIGESTS = {
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

_CONFIG_FIELDS = {
    "evidence_stage",
    "expected_warm_parent_sha256",
    "expected_warm_config_sha256",
    "expected_action_width_parent_sha256",
    "expected_action_width_decision_sha256",
    "expected_action_width_config_sha256",
    "expected_action_width_implementation_sha256",
    "expected_warm_implementation_sha256",
    "expected_cache_parent_sha256",
    "expected_cache_parent_config_sha256",
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
    "mixture_components",
    "split_index",
    "query_chunk_records",
    "maximum_feature_width_per_batch",
    "minimum_warm_noncache_reserve_bytes",
    "headroom_rule",
    "zero_step_rule",
    "strategy_claim_policy",
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


def _parent_target(
    parent: Mapping[str, Any], family: str, shift: str
) -> Mapping[str, Any]:
    family_row = next(
        row for row in parent["family_rows"] if row["range_family"] == family
    )
    return next(row for row in family_row["targets"] if row["target_shift"] == shift)


def _project_parent_descriptor(
    expected: Mapping[str, Any], *, shift: str
) -> dict[str, Any]:
    fields = _CONSTRUCTION_FIELDS_BY_SHIFT[shift]
    descriptor = expected["target_descriptor"]
    missing = fields - set(descriptor)
    if missing:
        raise ValueError(f"second-board parent omits core fields: {sorted(missing)}")
    return {field: descriptor[field] for field in sorted(fields)}


def compute_label_free_target_identity_rows(
    warm_config: Mapping[str, Any],
    warm_parent: Mapping[str, Any],
    *,
    expected_digests: Mapping[str, str] | None = None,
) -> list[dict[str, Any]]:
    """Rebuild target identities without constructing a sized policy or cache."""

    parsed = parse_h32_warm_search_config(dict(warm_config))
    board = parse_cards(*parsed["board"])
    rows = []
    for family in parsed["range_families"]:
        source_belief, _, _, retained = _build_case(
            parsed=parsed,
            board=board,
            hand_count=parsed["wide_hands_per_player"],
            family=family,
        )
        for shift in parsed["target_shifts"]:
            target, descriptor = build_target_belief(
                source_belief,
                board=board,
                shift=shift,
                local_blocker_target_seat=parsed["local_blocker_target_seat"],
            )
            expected = _parent_target(warm_parent, family, shift)
            key = f"{family}/{shift}"
            digest = _belief_digest(target)
            fields = _CONSTRUCTION_FIELDS_BY_SHIFT[shift]
            projection = _project_parent_descriptor(expected, shift=shift)
            construction_field_set_identity = set(descriptor) == fields
            parent_field_set_identity = set(expected["target_descriptor"]) == (
                fields | _PARENT_MEASUREMENT_FIELDS
            )
            core_projection_identity = descriptor == projection
            hand_axes_identity = (
                target.hands_by_player == source_belief.hands_by_player
                and descriptor["hand_axes_identity"] is True
                and projection["hand_axes_identity"] is True
            )
            digest_identity = (
                True if expected_digests is None else digest == expected_digests[key]
            )
            rows.append(
                {
                    "target": key,
                    "range_family": family,
                    "target_shift": shift,
                    "target_belief_sha256": digest,
                    "construction_descriptor": descriptor,
                    "construction_field_set_identity": (
                        construction_field_set_identity
                    ),
                    "parent_field_set_identity": parent_field_set_identity,
                    "parent_core_projection_identity": core_projection_identity,
                    "hand_axes_identity": hand_axes_identity,
                    "expected_digest_identity": digest_identity,
                    "passed": all(
                        (
                            construction_field_set_identity,
                            parent_field_set_identity,
                            core_projection_identity,
                            hand_axes_identity,
                            digest_identity,
                        )
                    ),
                }
            )
        del retained, source_belief
        gc.collect()
    return rows


def parse_h32_second_board_cache_config(config: dict[str, Any]) -> dict[str, Any]:
    """Validate the complete cache-only second-board contract."""

    if set(config) != _CONFIG_FIELDS:
        raise ValueError("second-board cache config fields differ from ADR-0138")
    frozen = {
        "evidence_stage": (
            "preregistered_after_adr0137_before_any_original_board_h32_two_"
            "size_policy_cache_or_common_game_quality_measurement"
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
        "mixture_components": 3,
        "split_index": 3,
        "query_chunk_records": 256,
        "maximum_feature_width_per_batch": 384,
        "minimum_warm_noncache_reserve_bytes": 5_184_456_164,
        "headroom_rule": (
            "all_eight_caches_must_leave_the_prior_pool_and_physical_"
            "noncache_reserve_before_a_later_strategy_audit"
        ),
        "zero_step_rule": (
            "compile_and_measure_only_zero_h32_steps_zero_h32_policies_zero_"
            "h32_quality_evaluations"
        ),
        "strategy_claim_policy": "always_null",
        "required_numpy_version": "2.5.2",
        "required_scipy_version": "1.18.0",
        "required_cupy_version": "14.2.0",
        "required_cuda_runtime_version": 13020,
        "minimum_cuda_driver_version": 13000,
        "required_compute_capability": "120",
        "cuda_dll_environment_variable": "PONTIUS_CUDA_DLL_DIRECTORY",
    }
    if any(config[field] != value for field, value in frozen.items()):
        raise ValueError("second-board cache workload differs from ADR-0138")
    if config["target_belief_sha256_by_target"] != _FROZEN_TARGET_DIGESTS:
        raise ValueError("second-board target belief digests differ from ADR-0138")

    sources = {
        "expected_warm_parent_sha256": _WARM_PARENT,
        "expected_warm_config_sha256": _WARM_CONFIG,
        "expected_action_width_parent_sha256": _ACTION_WIDTH_PARENT,
        "expected_action_width_decision_sha256": _ACTION_WIDTH_DECISION,
        "expected_action_width_config_sha256": _ACTION_WIDTH_CONFIG,
        "expected_action_width_implementation_sha256": (
            _ACTION_WIDTH_IMPLEMENTATION
        ),
        "expected_warm_implementation_sha256": _WARM_IMPLEMENTATION,
        "expected_cache_parent_sha256": _CACHE_PARENT,
        "expected_cache_parent_config_sha256": _CACHE_PARENT_CONFIG,
        "expected_audit_implementation_sha256": _IMPLEMENTATION,
        "expected_control_test_sha256": _CONTROL_TEST,
    }
    for field, path in sources.items():
        if config[field] != _sha256(path):
            raise ValueError(f"second-board cache source hash mismatch: {field}")

    warm_config = json.loads(_WARM_CONFIG.read_text(encoding="utf-8"))
    parse_h32_warm_search_config(warm_config)
    action_config = json.loads(_ACTION_WIDTH_CONFIG.read_text(encoding="utf-8"))
    action_width.parse_h32_action_width_quality_config(action_config)

    expected_gates = {
        "expected_target_rows": 4,
        "expected_cache_rows": 8,
        "expected_one_size_public_nodes": 385,
        "expected_two_size_public_nodes": 763,
        "expected_one_size_terminal_groups": 64,
        "expected_two_size_terminal_groups": 127,
        "expected_one_size_logical_automata": 384,
        "expected_two_size_logical_automata": 762,
        "expected_shared_affine_bases": 378,
        "maximum_small_profile_utility_error": 2e-13,
        "maximum_small_quality_error": 2e-11,
        "maximum_small_zero_sum_residual": 2e-11,
        "maximum_cache_compile_ms": 120000.0,
        "maximum_gpu_pool_bytes": 12000000000,
        "maximum_total_preflight_seconds": 1200.0,
        "require_clean_git_state": True,
        "require_parent_identity": True,
        "require_target_identity": True,
        "require_payoff_spans": True,
        "require_maximum_middle_rank_identity": True,
        "require_zero_h32_steps": True,
        "require_zero_h32_policies": True,
        "require_zero_h32_quality_evaluations": True,
    }
    if config["gates"] != expected_gates:
        raise ValueError("second-board cache gates differ from ADR-0138")
    return {
        **config,
        "two_size_bets": tuple(config["two_size_bets"]),
        "range_families": tuple(config["range_families"]),
        "target_shifts": tuple(config["target_shifts"]),
        "target_order": tuple(config["target_order"]),
        "arm_order_by_target": tuple(config["arm_order_by_target"]),
        "gates": dict(config["gates"]),
    }


def run_h32_second_board_cache_preflight(
    config_path: Path = _CONFIG,
    output_path: Path = _OUTPUT,
) -> dict[str, Any]:
    """Measure both resident widths on the original board without arithmetic."""

    started = time.perf_counter()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    parsed = parse_h32_second_board_cache_config(config)
    warm_parent = json.loads(_WARM_PARENT.read_text(encoding="utf-8"))
    warm_config = json.loads(_WARM_CONFIG.read_text(encoding="utf-8"))
    warm_parsed = parse_h32_warm_search_config(warm_config)
    action_parent = json.loads(_ACTION_WIDTH_PARENT.read_text(encoding="utf-8"))
    cache_parent = json.loads(_CACHE_PARENT.read_text(encoding="utf-8"))
    parent_identity = (
        warm_parent["gates"]["passed"]
        and warm_parent["config_sha256"] == parsed["expected_warm_config_sha256"]
        and action_parent["passed"]
        and action_parent["strategy_quality_claim"] is None
        and cache_parent["passed"]
        and cache_parent["strategy_quality_claim"] is None
        and cache_parent["h32_steps_executed"] == 0
    )
    if not parent_identity:
        raise ValueError("second-board cache parent identity rejected")

    environment = environment_metadata()
    environment["git"] = _strict_git_metadata()
    cp, runtime = _validate_runtime(parsed)

    target_identity_rows = compute_label_free_target_identity_rows(
        warm_config,
        warm_parent,
        expected_digests=parsed["target_belief_sha256_by_target"],
    )
    if not all(row["passed"] for row in target_identity_rows):
        raise ValueError("second-board target identity rejected before h32 cache work")

    small = action_width._small_control(parsed)
    small_passed = (
        small["profile_utility_error"]
        <= parsed["gates"]["maximum_small_profile_utility_error"]
        and small["quality_error"]
        <= parsed["gates"]["maximum_small_quality_error"]
        and small["zero_sum_residual"]
        <= parsed["gates"]["maximum_small_zero_sum_residual"]
        and small["compact_round_trip"]
        and small["shared_affine_bases"]
        == parsed["gates"]["expected_shared_affine_bases"]
    )
    if not small_passed:
        raise ValueError("small cache portability control failed before h32")

    board = parse_cards(*parsed["board"])
    measured_targets = []
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
        gpu = CuPyBidirectionalIncidence.compile(sparse)
        for shift in parsed["target_shifts"]:
            target, descriptor = build_target_belief(
                source_belief,
                board=board,
                shift=shift,
                local_blocker_target_seat=warm_parsed[
                    "local_blocker_target_seat"
                ],
            )
            key = f"{family}/{shift}"
            expected = _parent_target(warm_parent, family, shift)
            target_identity = (
                descriptor == _project_parent_descriptor(expected, shift=shift)
                and _belief_digest(target)
                == parsed["target_belief_sha256_by_target"][key]
                and target.hands_by_player == source_belief.hands_by_player
            )
            workspace, workspace_ms = action_width._target_workspace(
                source_workspace,
                target,
                query_chunk_records=parsed["query_chunk_records"],
            )
            order_name = parsed["arm_order_by_target"][target_index]
            arm_order = (
                ("one_size", "two_size")
                if order_name == "one_then_two"
                else ("two_size", "one_size")
            )
            arms = {}
            for arm in arm_order:
                gc.collect()
                release_cupy_memory_pool()
                libraries = one_libraries if arm == "one_size" else sized_libraries
                cache_row, belief_cache, automaton_caches = action_width._compile_cache(
                    cp,
                    workspace,
                    libraries,
                    arm=arm,
                )
                cache_row["pool_ceiling_headroom_bytes"] = (
                    parsed["gates"]["maximum_gpu_pool_bytes"]
                    - cache_row["pool_total_bytes"]
                )
                cache_row["warm_noncache_reserve_safe"] = (
                    cache_row["pool_ceiling_headroom_bytes"]
                    >= parsed["minimum_warm_noncache_reserve_bytes"]
                    and cache_row["physical_device_free_bytes"]
                    >= parsed["minimum_warm_noncache_reserve_bytes"]
                )
                arms[arm] = cache_row
                del automaton_caches, belief_cache
                gc.collect()
                release_cupy_memory_pool()

            one = arms["one_size"]
            two = arms["two_size"]
            measured_targets.append(
                {
                    "range_family": family,
                    "target_shift": shift,
                    "target": key,
                    "arm_order": order_name,
                    "target_descriptor": descriptor,
                    "target_belief_sha256": _belief_digest(target),
                    "target_identity": target_identity,
                    "target_workspace_compile_ms": workspace_ms,
                    "one_size_public_nodes": one_layout.public_node_count,
                    "two_size_public_nodes": sized_layout.public_node_count,
                    "one_size_terminal_groups": len(one_libraries[0]),
                    "two_size_terminal_groups": len(
                        multi_size_terminal_groups(sized_layout)
                    ),
                    "one_size_payoff_span": float(one_layout.game.payoff_span),
                    "two_size_payoff_span": float(sized_layout.game.payoff_span),
                    "arms": arms,
                    "two_over_one": {
                        "persistent_numeric_bytes": (
                            two["persistent_numeric_bytes"]
                            / one["persistent_numeric_bytes"]
                        ),
                        "automaton_numeric_bytes": (
                            two["automaton_numeric_bytes"]
                            / one["automaton_numeric_bytes"]
                        ),
                        "total_middle_rank": (
                            two["total_middle_rank"] / one["total_middle_rank"]
                        ),
                        "cold_construction_ms": (
                            two["cold_construction_ms"]
                            / one["cold_construction_ms"]
                        ),
                    },
                }
            )
            target_index += 1
            del workspace, target
            gc.collect()
            release_cupy_memory_pool()
        del gpu
        gc.collect()
        release_cupy_memory_pool()

    total_seconds = time.perf_counter() - started
    gates = parsed["gates"]
    cache_rows = [
        target["arms"][arm]
        for target in measured_targets
        for arm in ("one_size", "two_size")
    ]
    actual_order = tuple(target["target"] for target in measured_targets)
    headroom_safe = all(row["warm_noncache_reserve_safe"] for row in cache_rows)
    gate_results = {
        "parent_identity": parent_identity == gates["require_parent_identity"],
        "clean_git_state": (not bool(environment["git"]["dirty"]))
        == gates["require_clean_git_state"],
        "small_control": small_passed,
        "target_count_and_order": (
            len(measured_targets) == gates["expected_target_rows"]
            and actual_order == parsed["target_order"]
        ),
        "cache_count": len(cache_rows) == gates["expected_cache_rows"],
        "target_identity": all(
            target["target_identity"] for target in measured_targets
        )
        == gates["require_target_identity"],
        "public_topology": all(
            target["one_size_public_nodes"]
            == gates["expected_one_size_public_nodes"]
            and target["two_size_public_nodes"]
            == gates["expected_two_size_public_nodes"]
            and target["one_size_terminal_groups"]
            == gates["expected_one_size_terminal_groups"]
            and target["two_size_terminal_groups"]
            == gates["expected_two_size_terminal_groups"]
            for target in measured_targets
        ),
        "logical_automata_and_bases": all(
            target["arms"]["one_size"]["logical_automata"]
            == gates["expected_one_size_logical_automata"]
            and target["arms"]["two_size"]["logical_automata"]
            == gates["expected_two_size_logical_automata"]
            and target["arms"]["two_size"]["shared_affine_bases"]
            == gates["expected_shared_affine_bases"]
            for target in measured_targets
        ),
        "payoff_spans": all(
            target["one_size_payoff_span"]
            == parsed["expected_one_size_payoff_span"]
            and target["two_size_payoff_span"]
            == parsed["expected_two_size_payoff_span"]
            for target in measured_targets
        )
        == gates["require_payoff_spans"],
        "maximum_middle_rank_identity": all(
            target["arms"]["one_size"]["maximum_middle_rank"]
            == target["arms"]["two_size"]["maximum_middle_rank"]
            for target in measured_targets
        )
        == gates["require_maximum_middle_rank_identity"],
        "cache_compile": all(
            row["cold_construction_ms"] <= gates["maximum_cache_compile_ms"]
            for row in cache_rows
        ),
        "gpu_pool_ceiling": all(
            row["pool_total_bytes"] <= gates["maximum_gpu_pool_bytes"]
            for row in cache_rows
        ),
        "zero_h32_steps": True == gates["require_zero_h32_steps"],
        "zero_h32_policies": True == gates["require_zero_h32_policies"],
        "zero_h32_quality_evaluations": (
            True == gates["require_zero_h32_quality_evaluations"]
        ),
        "wall_time": total_seconds <= gates["maximum_total_preflight_seconds"],
    }
    passed = all(gate_results.values())
    result = {
        "schema_version": 1,
        "status": "frozen_h32_second_board_resident_cache_preflight_executed",
        "experiment_type": "h32_second_board_one_vs_two_size_cache_portability",
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
        "target_identity_preflight": target_identity_rows,
        "targets": measured_targets,
        "headroom": {
            "minimum_warm_noncache_reserve_bytes": parsed[
                "minimum_warm_noncache_reserve_bytes"
            ],
            "all_eight_caches_safe": headroom_safe,
            "outcome_is_not_a_mechanism_gate": True,
        },
        "h32_steps_executed": 0,
        "h32_policies_constructed": 0,
        "h32_strategy_quality_evaluations": 0,
        "gate_results": gate_results,
        "passed": passed,
        "decision": (
            "authorize_preregistered_second_board_action_width_quality_audit"
            if passed and headroom_safe
            else (
                "stop_before_second_board_strategy_and_revisit_cache"
                if passed
                else "reject_second_board_cache_preflight_mechanism"
            )
        ),
        "strategy_quality_claim": None,
        "timing": {"total_seconds": total_seconds},
        "limitations": [
            (
                "The board and one-size target corpus were revealed by earlier "
                "one-size audits; only the sized cache geometry is new."
            ),
            "Headroom is a conservative laboratory reserve, not a production concurrency proof.",
            "No h32 policy was embedded, trained, serialized, or evaluated.",
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
    result = run_h32_second_board_cache_preflight(
        arguments.config,
        arguments.output,
    )
    print(
        "h32 second-board cache preflight: "
        f"passed={result['passed']}, "
        f"headroom_safe={result['headroom']['all_eight_caches_safe']}, "
        f"wall={result['timing']['total_seconds']:.3f}s"
    )


if __name__ == "__main__":
    main()
