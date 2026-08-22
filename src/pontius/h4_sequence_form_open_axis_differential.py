"""Label-free h4 differential for sequence-form open-axis cut extraction."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
from math import fsum, isfinite
from pathlib import Path
import time
from typing import Any

import numpy as np

from .continuation_public_tree_tensor import ContinuationPublicTreeTensorEvaluator
from .cross_payoff_leaf_adjoint import splice_fixed_response_probability_tape
from .h32_affine_resident_cache_preflight import _strict_git_metadata
from .incremental_policy_tt import compile_policy_probability_tape
from .leaf_adjoint_cfr import build_leaf_adjoint_terminal_automata
from .one_seat_convex_generation import compiled_layout_path_single_visit_report
from .open_mode_audit import _canonical_belief, _open_workspace
from .public_policy_tt import _information_key, information_schema_for_axes
from .public_tree_tensor import PublicTreeTensorEvaluator
from .real_policy import policy_digest
from .river import parse_cards
from .runner_harness import assemble_environment, finalize_gates, serialize_result
from .sequence_form_open_axis import (
    SequenceFormAffineRow,
    affine_row_conditioning,
    constant_minus_affine_row,
    extract_sequence_form_open_axis_payoff,
    sequence_form_realization_tape,
    splice_fixed_response_probability_tape_for_axes,
    subtract_affine_rows,
)
from .showdown_value_rank_screen import _game_from_belief, _rank_codes
from .sparse_incidence_open_mode import SparseBidirectionalIncidence


_ROOT = Path(__file__).parents[2]
_CONFIG = _ROOT / "experiments/configs/h4-sequence-form-open-axis-v1.json"
_OUTPUT = _ROOT / "experiments/results/h4-sequence-form-open-axis-v1.json"
_PARENT_RESULT = _ROOT / "experiments/results/one-seat-convex-keystone-v1.json"
_PARENT_DECISION = (
    _ROOT
    / "docs/decisions/ADR-0241-one-seat-convex-generation-matches-complete-teacher.md"
)
_PRIMITIVE = _ROOT / "src/pontius/sequence_form_open_axis.py"
_PRIMITIVE_TEST = _ROOT / "tests/test_sequence_form_open_axis.py"
_IMPLEMENTATION = Path(__file__)
_TEST = _ROOT / "tests/test_h4_sequence_form_open_axis_differential.py"

_PATHS = {
    "expected_parent_result_sha256": _PARENT_RESULT,
    "expected_parent_decision_sha256": _PARENT_DECISION,
    "expected_primitive_sha256": _PRIMITIVE,
    "expected_primitive_test_sha256": _PRIMITIVE_TEST,
    "expected_implementation_sha256": _IMPLEMENTATION,
    "expected_control_test_sha256": _TEST,
}


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required h4 open-axis input is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _parse_config(config: dict[str, Any]) -> dict[str, Any]:
    expected = {
        "evidence_stage",
        *_PATHS,
        "board",
        "players",
        "hands_per_player",
        "range_family",
        "axis_seed",
        "mixture_components",
        "pot",
        "stack",
        "bet_size",
        "split_index",
        "query_chunk_records",
        "maximum_feature_width_per_batch",
        "layouts",
        "source_policy_sha256",
        "strategy_label_policy",
        "gates",
    }
    if set(config) != expected:
        raise ValueError("h4 open-axis config fields differ from ADR-0242")
    for field, path in _PATHS.items():
        if config[field] != _sha256(path):
            raise ValueError(f"h4 open-axis provenance mismatch: {field}")
    frozen = {
        "evidence_stage": "preregistered_after_adr0241_before_h4_open_axis_run",
        "board": ["2c", "7d", "9h", "Js", "Qc"],
        "players": 6,
        "hands_per_player": 4,
        "range_family": "balanced",
        "axis_seed": 20260819,
        "mixture_components": 3,
        "pot": 12.0,
        "stack": 30.0,
        "bet_size": 3.0,
        "split_index": 3,
        "query_chunk_records": 256,
        "maximum_feature_width_per_batch": 96,
        "layouts": [
            {
                "layout_id": "full_repeated_actor",
                "public_prefix": [],
                "acting_player": 0,
                "expected_path_single_visit": False,
                "expected_public_nodes": 385,
                "expected_sequence_entries": 256,
            },
            {
                "layout_id": "post_bet_single_visit",
                "public_prefix": [[0, "check"], [1, "bet"]],
                "acting_player": 2,
                "expected_path_single_visit": True,
                "expected_public_nodes": 63,
                "expected_sequence_entries": 8,
            },
        ],
        "source_policy_sha256": {
            "full_repeated_actor": (
                "d761103c5e609117d0ce29e75122c1ae9f5f5efbbf4b0ac2da3d51218fa9d75d"
            ),
            "post_bet_single_visit": (
                "1bb1f2f8d5faf271bfcdd1b6011ca54b3c364a4158bd13868f8b85e3a0ed1ebf"
            ),
        },
        "strategy_label_policy": "zero_certificates_zero_quality_rows_label_free",
    }
    for field, value in frozen.items():
        if config[field] != value:
            raise ValueError(f"h4 open-axis field differs from ADR-0242: {field}")
    expected_gates = {
        "expected_layouts": 2,
        "expected_profile_passes_per_layout": 6,
        "expected_fixed_response_passes_per_layout": 5,
        "maximum_profile_row_error": 2e-11,
        "maximum_fixed_response_row_error": 2e-11,
        "maximum_gain_row_error": 2e-11,
        "maximum_acting_br_invariance_error": 2e-11,
        "maximum_source_zero_sum_residual": 2e-11,
        "maximum_row_persistent_bytes": 1000000,
        "maximum_total_seconds": 60.0,
        "minimum_external_axis_embedded_mismatch_entries": 1,
        "require_parent_passed": True,
        "require_clean_git_state": True,
        "require_topology_classification": True,
        "require_external_axis_corrected_splice": True,
        "require_no_approximate_row_deduplication": True,
        "require_no_strategy_labels": True,
        "require_finite": True,
    }
    if config["gates"] != expected_gates:
        raise ValueError("h4 open-axis gates differ from ADR-0242")
    return {
        **config,
        "board": tuple(config["board"]),
        "layouts": tuple(
            {
                **row,
                "public_prefix": tuple(
                    (int(actor), str(action))
                    for actor, action in row["public_prefix"]
                ),
            }
            for row in config["layouts"]
        ),
    }


def _dense_policy(schema: dict[str, tuple[str, ...]]) -> dict[str, dict[str, float]]:
    policy = {}
    for key, actions in schema.items():
        digest = hashlib.sha256(key.encode("utf-8")).digest()
        weights = tuple(float(1 + digest[index] % 23) for index in range(len(actions)))
        total = sum(weights)
        policy[key] = {
            action: weights[index] / total
            for index, action in enumerate(actions)
        }
    return policy


def _endpoint_policy(
    layout: Any,
    hands_by_player: tuple[tuple[Any, ...], ...],
    source: dict[str, dict[str, float]],
    acting_player: int,
) -> dict[str, dict[str, float]]:
    result = {key: dict(row) for key, row in source.items()}
    for node_index, node in enumerate(layout.nodes):
        if node.player != acting_player:
            continue
        for hand_index, hand in enumerate(hands_by_player[acting_player]):
            key = _information_key(layout, acting_player, hand, node.history)
            selected = (node_index + hand_index + 1) % len(node.actions)
            result[key] = {
                action: float(action_index == selected)
                for action_index, action in enumerate(node.actions)
            }
    return result


def _fixed_response_policy(
    layout: Any,
    hands_by_player: tuple[tuple[Any, ...], ...],
    source: dict[str, dict[str, float]],
    response_actions: dict[str, Any],
) -> dict[str, dict[str, float]]:
    result = {key: dict(row) for key, row in source.items()}
    schema = information_schema_for_axes(layout, hands_by_player)
    if not set(response_actions).issubset(schema):
        raise ValueError("direct response teacher has off-axis keys")
    for key, selected in response_actions.items():
        result[key] = {
            action: float(action == selected)
            for action in schema[key]
        }
    return result


def _finite_tree(value: Any) -> bool:
    if value is None or isinstance(value, (str, bool)):
        return True
    if isinstance(value, (int, float)):
        return isfinite(float(value))
    if isinstance(value, dict):
        return all(_finite_tree(key) and _finite_tree(item) for key, item in value.items())
    if isinstance(value, (list, tuple)):
        return all(_finite_tree(item) for item in value)
    return False


def _external_axis_mutation(
    layout: Any,
    hands_by_player: tuple[tuple[Any, ...], ...],
    policy: dict[str, dict[str, float]],
) -> dict[str, Any]:
    axes = tuple(tuple(reversed(axis)) for axis in hands_by_player)
    probabilities = compile_policy_probability_tape(layout, axes, policy)
    responding_player = 1
    response_actions = {}
    for node in layout.nodes:
        if node.player != responding_player:
            continue
        for hand_index, hand in enumerate(axes[responding_player]):
            key = _information_key(
                layout,
                responding_player,
                hand,
                node.history,
            )
            response_actions[key] = node.actions[hand_index % len(node.actions)]
    corrected = splice_fixed_response_probability_tape_for_axes(
        layout,
        probabilities,
        response_actions,
        responding_player=responding_player,
        hands_by_player=axes,
    )
    embedded = splice_fixed_response_probability_tape(
        layout,
        probabilities,
        response_actions,
        responding_player=responding_player,
    )
    mismatches = 0
    corrected_errors = 0
    for node_index, node in enumerate(layout.nodes):
        if node.player != responding_player:
            continue
        actual = corrected[node_index]
        old = embedded[node_index]
        if actual is None or old is None:
            raise AssertionError("response mutation strategic row is absent")
        mismatches += int(np.count_nonzero(actual != old))
        for hand_index, hand in enumerate(axes[responding_player]):
            key = _information_key(
                layout,
                responding_player,
                hand,
                node.history,
            )
            selected = node.actions.index(response_actions[key])
            corrected_errors += int(actual[hand_index, selected] != 1.0)
    return {
        "reordered_external_axes": True,
        "embedded_splice_mismatch_entries": mismatches,
        "corrected_splice_errors": corrected_errors,
        "passed": mismatches > 0 and corrected_errors == 0,
    }


def _automaton_bytes(automata: tuple[dict[str, Any], ...]) -> int:
    unique = {
        id(automaton): automaton
        for library in automata
        for automaton in library.values()
    }
    return sum(int(automaton.numeric_bytes) for automaton in unique.values())


def _run_layout(
    parsed: dict[str, Any],
    spec: dict[str, Any],
    layout: Any,
    workspace: Any,
    sparse: Any,
    hands_by_player: tuple[tuple[Any, ...], ...],
    automata: tuple[dict[str, Any], ...],
) -> dict[str, Any]:
    acting_player = int(spec["acting_player"])
    schema = information_schema_for_axes(layout, hands_by_player)
    source_policy = _dense_policy(schema)
    if policy_digest(source_policy) != parsed["source_policy_sha256"][spec["layout_id"]]:
        raise ValueError("h4 open-axis source policy digest differs")
    endpoint_policy = _endpoint_policy(
        layout,
        hands_by_player,
        source_policy,
        acting_player,
    )
    source_probabilities = compile_policy_probability_tape(
        layout,
        hands_by_player,
        source_policy,
    )
    endpoint_probabilities = compile_policy_probability_tape(
        layout,
        hands_by_player,
        endpoint_policy,
    )
    source_realization = sequence_form_realization_tape(
        layout,
        source_probabilities,
        acting_player=acting_player,
        hands_by_player=hands_by_player,
    )
    endpoint_realization = sequence_form_realization_tape(
        layout,
        endpoint_probabilities,
        acting_player=acting_player,
        hands_by_player=hands_by_player,
    )

    oracle_started = time.perf_counter()
    source_evaluation = layout.evaluate(source_policy)
    response_oracle_ms = (time.perf_counter() - oracle_started) * 1000.0
    teacher_started = time.perf_counter()
    endpoint_evaluation = layout.evaluate(endpoint_policy)
    teacher_ms = (time.perf_counter() - teacher_started) * 1000.0

    profile_results = []
    profile_errors = []
    response_errors = []
    gain_errors = []
    gain_rows: list[SequenceFormAffineRow] = []
    response_results = []
    for payoff_player in range(layout.num_players):
        profile = extract_sequence_form_open_axis_payoff(
            layout,
            workspace,
            sparse,
            source_probabilities,
            automata[payoff_player],
            acting_player=acting_player,
            payoff_player=payoff_player,
            hands_by_player=hands_by_player,
            maximum_feature_width_per_batch=int(
                parsed["maximum_feature_width_per_batch"]
            ),
        )
        profile_results.append(profile)
        source_profile_value = source_evaluation.evaluation.utilities[payoff_player]
        endpoint_profile_value = endpoint_evaluation.evaluation.utilities[payoff_player]
        profile_errors.extend(
            (
                abs(profile.row.value(source_realization) - source_profile_value),
                abs(profile.row.value(endpoint_realization) - endpoint_profile_value),
            )
        )
        if payoff_player == acting_player:
            gain = constant_minus_affine_row(
                source_evaluation.evaluation.best_response_values[acting_player],
                profile.row,
            )
            source_gain = (
                source_evaluation.evaluation.best_response_values[acting_player]
                - source_profile_value
            )
            endpoint_gain = (
                source_evaluation.evaluation.best_response_values[acting_player]
                - endpoint_profile_value
            )
        else:
            actions = source_evaluation.best_response_actions[payoff_player]
            source_response_probabilities = (
                splice_fixed_response_probability_tape_for_axes(
                    layout,
                    source_probabilities,
                    actions,
                    responding_player=payoff_player,
                    hands_by_player=hands_by_player,
                )
            )
            endpoint_response_probabilities = (
                splice_fixed_response_probability_tape_for_axes(
                    layout,
                    endpoint_probabilities,
                    actions,
                    responding_player=payoff_player,
                    hands_by_player=hands_by_player,
                )
            )
            response = extract_sequence_form_open_axis_payoff(
                layout,
                workspace,
                sparse,
                source_response_probabilities,
                automata[payoff_player],
                acting_player=acting_player,
                payoff_player=payoff_player,
                hands_by_player=hands_by_player,
                maximum_feature_width_per_batch=int(
                    parsed["maximum_feature_width_per_batch"]
                ),
            )
            response_results.append(response)
            teacher_started = time.perf_counter()
            source_response_policy = _fixed_response_policy(
                layout,
                hands_by_player,
                source_policy,
                dict(actions),
            )
            endpoint_response_policy = _fixed_response_policy(
                layout,
                hands_by_player,
                endpoint_policy,
                dict(actions),
            )
            source_response_value = layout.evaluate(
                source_response_policy
            ).evaluation.utilities[payoff_player]
            endpoint_response_value = layout.evaluate(
                endpoint_response_policy
            ).evaluation.utilities[payoff_player]
            teacher_ms += (time.perf_counter() - teacher_started) * 1000.0
            response_errors.extend(
                (
                    abs(
                        response.row.value(source_realization)
                        - source_response_value
                    ),
                    abs(
                        response.row.value(endpoint_realization)
                        - endpoint_response_value
                    ),
                )
            )
            gain = subtract_affine_rows(response.row, profile.row)
            source_gain = source_response_value - source_profile_value
            endpoint_gain = endpoint_response_value - endpoint_profile_value
        gain_rows.append(gain)
        gain_errors.extend(
            (
                abs(gain.value(source_realization) - source_gain),
                abs(gain.value(endpoint_realization) - endpoint_gain),
            )
        )

    all_results = [*profile_results, *response_results]
    topology = compiled_layout_path_single_visit_report(layout)
    conditioning = affine_row_conditioning(tuple(gain_rows), tolerance=1e-12)
    source_zero_sum = abs(fsum(source_evaluation.evaluation.utilities))
    acting_br_invariance = abs(
        source_evaluation.evaluation.best_response_values[acting_player]
        - endpoint_evaluation.evaluation.best_response_values[acting_player]
    )
    sequence_entries = sum(node.values.size for node in gain_rows[0].nodes)
    return {
        "layout_id": spec["layout_id"],
        "acting_player": acting_player,
        "public_prefix": [list(row) for row in spec["public_prefix"]],
        "path_single_visit": topology.passed,
        "repeated_player": topology.repeated_player,
        "public_nodes": layout.public_node_count,
        "terminal_nodes": layout.terminal_node_count,
        "acting_public_nodes": len(gain_rows[0].nodes),
        "sequence_entries_per_row": sequence_entries,
        "profile_passes": len(profile_results),
        "fixed_response_passes": len(response_results),
        "maximum_profile_row_error": max(profile_errors),
        "maximum_fixed_response_row_error": max(response_errors),
        "maximum_gain_row_error": max(gain_errors),
        "acting_best_response_invariance_error": acting_br_invariance,
        "source_zero_sum_residual": source_zero_sum,
        "response_oracle_ms": response_oracle_ms,
        "direct_teacher_ms": teacher_ms,
        "coefficient_construction_ms": sum(row.work.wall_ms for row in all_results),
        "coefficient_contraction_ms": sum(
            row.work.contraction_ms for row in all_results
        ),
        "coefficient_assembly_ms": sum(row.work.assembly_ms for row in all_results),
        "maximum_middle_rank": max(row.work.maximum_middle_rank for row in all_results),
        "maximum_peak_numeric_bytes": max(
            row.work.maximum_peak_numeric_bytes for row in all_results
        ),
        "maximum_gpu_pool_total_bytes": max(
            row.work.maximum_gpu_pool_total_bytes for row in all_results
        ),
        "gain_row_persistent_bytes": sum(row.numeric_bytes for row in gain_rows),
        "conditioning": asdict(conditioning),
        "layout_memory": layout.memory_summary(),
        "workspace_numeric_bytes": int(workspace.numeric_bytes),
        "sparse_operator_numeric_bytes": int(sparse.numeric_bytes),
        "terminal_automaton_numeric_bytes": _automaton_bytes(automata),
        "source_policy_sha256": policy_digest(source_policy),
        "endpoint_policy_sha256": policy_digest(endpoint_policy),
        "quality_rows_serialized": 0,
        "certificates_executed": 0,
        "strategy_labels_generated": 0,
    }


def run_h4_sequence_form_open_axis_differential(
    config_path: Path = _CONFIG,
    output_path: Path = _OUTPUT,
) -> dict[str, Any]:
    started = time.perf_counter()
    parsed = _parse_config(json.loads(config_path.read_text(encoding="utf-8")))
    git = _strict_git_metadata()
    parent = json.loads(_PARENT_RESULT.read_text(encoding="utf-8"))
    board = parse_cards(*parsed["board"])
    belief = _canonical_belief(
        board=board,
        hand_count=int(parsed["hands_per_player"]),
        family=parsed["range_family"],
        components=int(parsed["mixture_components"]),
        seed=int(parsed["axis_seed"]),
    )
    game = _game_from_belief(
        belief=belief,
        pot=float(parsed["pot"]),
        stack=float(parsed["stack"]),
        bet_size=float(parsed["bet_size"]),
    )
    workspace, workspace_build = _open_workspace(
        belief,
        split_index=int(parsed["split_index"]),
        query_chunk_records=int(parsed["query_chunk_records"]),
    )
    sparse_started = time.perf_counter()
    sparse = SparseBidirectionalIncidence.compile(workspace)
    sparse_compile_ms = (time.perf_counter() - sparse_started) * 1000.0
    codes = tuple(
        np.ascontiguousarray(values, dtype=np.int32)
        for values in _rank_codes(board, belief.hands_by_player)
    )

    rows = []
    full_layout: Any | None = None
    full_policy: dict[str, dict[str, float]] | None = None
    for spec in parsed["layouts"]:
        layout = (
            PublicTreeTensorEvaluator(game)
            if not spec["public_prefix"]
            else ContinuationPublicTreeTensorEvaluator(
                game,
                public_prefix=spec["public_prefix"],
            )
        )
        automata = build_leaf_adjoint_terminal_automata(
            layout,
            codes,
            pot=float(parsed["pot"]),
            bet_size=float(parsed["bet_size"]),
        )
        row = _run_layout(
            parsed,
            spec,
            layout,
            workspace,
            sparse,
            belief.hands_by_player,
            automata,
        )
        rows.append(row)
        if spec["layout_id"] == "full_repeated_actor":
            full_layout = layout
            full_policy = _dense_policy(
                information_schema_for_axes(layout, belief.hands_by_player)
            )
    if full_layout is None or full_policy is None:
        raise AssertionError("h4 open-axis full layout was not executed")
    mutation = _external_axis_mutation(
        full_layout,
        belief.hands_by_player,
        full_policy,
    )
    total_seconds = time.perf_counter() - started
    gates = parsed["gates"]
    specs = {row["layout_id"]: row for row in parsed["layouts"]}
    checks = {
        "parent_passed": bool(parent.get("passed")) == gates["require_parent_passed"],
        "clean_git": (not git["dirty"]) == gates["require_clean_git_state"],
        "layout_count": len(rows) == gates["expected_layouts"],
        "topology_classification": all(
            row["path_single_visit"]
            == bool(specs[row["layout_id"]]["expected_path_single_visit"])
            for row in rows
        )
        == gates["require_topology_classification"],
        "public_node_counts": all(
            row["public_nodes"] == specs[row["layout_id"]]["expected_public_nodes"]
            for row in rows
        ),
        "sequence_entry_counts": all(
            row["sequence_entries_per_row"]
            == specs[row["layout_id"]]["expected_sequence_entries"]
            for row in rows
        ),
        "pass_counts": all(
            row["profile_passes"] == gates["expected_profile_passes_per_layout"]
            and row["fixed_response_passes"]
            == gates["expected_fixed_response_passes_per_layout"]
            for row in rows
        ),
        "profile_row_identity": all(
            row["maximum_profile_row_error"] <= gates["maximum_profile_row_error"]
            for row in rows
        ),
        "fixed_response_row_identity": all(
            row["maximum_fixed_response_row_error"]
            <= gates["maximum_fixed_response_row_error"]
            for row in rows
        ),
        "gain_row_identity": all(
            row["maximum_gain_row_error"] <= gates["maximum_gain_row_error"]
            for row in rows
        ),
        "acting_br_invariance": all(
            row["acting_best_response_invariance_error"]
            <= gates["maximum_acting_br_invariance_error"]
            for row in rows
        ),
        "source_zero_sum": all(
            row["source_zero_sum_residual"]
            <= gates["maximum_source_zero_sum_residual"]
            for row in rows
        ),
        "row_persistent_bytes": all(
            row["gain_row_persistent_bytes"]
            <= gates["maximum_row_persistent_bytes"]
            for row in rows
        ),
        "external_axis_corrected_splice": (
            mutation["passed"]
            and mutation["embedded_splice_mismatch_entries"]
            >= gates["minimum_external_axis_embedded_mismatch_entries"]
        )
        == gates["require_external_axis_corrected_splice"],
        "no_approximate_row_deduplication": True
        == gates["require_no_approximate_row_deduplication"],
        "no_strategy_labels": all(
            row["quality_rows_serialized"] == 0
            and row["certificates_executed"] == 0
            and row["strategy_labels_generated"] == 0
            for row in rows
        )
        == gates["require_no_strategy_labels"],
        "total_time": total_seconds <= gates["maximum_total_seconds"],
    }
    payload = {
        "workspace_build_ms": workspace_build,
        "sparse_compile_ms": sparse_compile_ms,
        "external_axis_mutation": mutation,
        "layout_rows": rows,
    }
    checks["finite"] = _finite_tree(payload) == gates["require_finite"]
    gate_result = finalize_gates(checks)
    result = {
        "schema_version": 1,
        "status": "h4_sequence_form_open_axis_differential_executed",
        "environment": assemble_environment(
            runtime={"backend": "cpu_float64_h4_sparse_leaf_contraction"},
            git=git,
        ),
        "config_sha256": _sha256(config_path),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "primitive_sha256": _sha256(_PRIMITIVE),
        "methodology": {
            "layouts": [row["layout_id"] for row in rows],
            "profile_passes": sum(row["profile_passes"] for row in rows),
            "fixed_response_passes": sum(
                row["fixed_response_passes"] for row in rows
            ),
            "teacher": "direct_dense_deal_axis_source_and_endpoint_utilities",
            "row_coordinates": "last_action_sequence_form_realization",
            "row_deduplication": "none_in_differential_exact_signature_only_later",
            "quality_rows": 0,
            "certificates": 0,
            "strategy_labels": 0,
        },
        **payload,
        **gate_result,
        "decision": (
            "authorize_external_axis_h32_row_extraction_preflight"
            if gate_result["passed"]
            else "reject_sequence_form_open_axis_extractor"
        ),
        "total_seconds": total_seconds,
        "strategy_quality_claim": None,
        "limitations": [
            "This is a label-free h4 coefficient identity and cost differential.",
            (
                "The dense teacher and sparse extractor share game semantics "
                "but not the open-axis assembly path."
            ),
            "h4 CPU timing does not predict resident h32 GPU latency or cut count.",
            (
                "A pass authorizes only an h32 label-free extraction preflight, "
                "not optimization or emission."
            ),
        ],
    }
    output_path.write_text(serialize_result(result), encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=_CONFIG)
    parser.add_argument("--output", type=Path, default=_OUTPUT)
    args = parser.parse_args()
    result = run_h4_sequence_form_open_axis_differential(args.config, args.output)
    print(
        json.dumps(
            {
                "output": str(args.output),
                "passed": result["passed"],
                "decision": result["decision"],
                "total_seconds": result["total_seconds"],
            },
            indent=2,
        )
    )
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
