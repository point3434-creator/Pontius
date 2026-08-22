"""Label-free h32 preflight for exact post-action continuation rooting."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import time
from typing import Any, Mapping

import numpy as np

from .axis_cfr_checkpoint import axis_cfr_checkpoint_digest
from .continuation_public_tree_tensor import ContinuationPublicTreeTensorEvaluator
from .fresh_h32_strategy_transfer_audit import _belief_digest
from .h32_action_conditioned_posterior_manifest import (
    build_action_conditioned_posterior,
    observed_bet_sequence,
)
from .h32_affine_resident_cache_preflight import _strict_git_metadata
from .h32_warm_search_acceptance_audit import _average_policy_from_state
from .leaf_adjoint_cfr import build_leaf_adjoint_terminal_automata
from .leaf_adjoint_checkpoint_ladder_audit import _build_case
from .public_policy_tt import (
    _terminal_keys_by_slot,
    information_schema_for_axes,
)
from .public_tree_tensor import PublicTreeTensorEvaluator
from .real_policy import policy_digest
from .reporting import environment_metadata
from .river import parse_cards
from .showdown_value_rank_screen import _rank_codes


_ROOT = Path(__file__).parents[2]
_CONFIG = _ROOT / "experiments/configs/h32-continuation-root-preflight-v1.json"
_OUTPUT = _ROOT / "experiments/results/h32-continuation-root-preflight-v1.json"
_SOURCE = _ROOT / "experiments/results/h32-fresh-panel-source-blueprints-v1.json"
_MANIFEST = _ROOT / "experiments/results/h32-action-conditioned-posterior-manifest-v1.json"
_PARENT = _ROOT / "experiments/results/h32-action-conditioned-widened-selector-v1.json"
_PARENT_DECISION = _ROOT / "docs/decisions/ADR-0222-widened-range-transfer-finds-value-but-live-selection-is-infeasible.md"
_IMPLEMENTATION = Path(__file__)
_TEST = _ROOT / "tests/test_h32_continuation_root_preflight.py"

_PATHS = {
    "expected_source_result_sha256": _SOURCE,
    "expected_manifest_result_sha256": _MANIFEST,
    "expected_parent_result_sha256": _PARENT,
    "expected_parent_decision_sha256": _PARENT_DECISION,
    "expected_public_tree_implementation_sha256": _ROOT / "src/pontius/public_tree_tensor.py",
    "expected_public_tree_control_test_sha256": _ROOT / "tests/test_public_tree_tensor.py",
    "expected_continuation_implementation_sha256": _ROOT / "src/pontius/continuation_public_tree_tensor.py",
    "expected_policy_implementation_sha256": _ROOT / "src/pontius/public_policy_tt.py",
    "expected_automaton_implementation_sha256": _ROOT / "src/pontius/leaf_adjoint_cfr.py",
    "expected_preflight_implementation_sha256": _IMPLEMENTATION,
    "expected_preflight_control_test_sha256": _TEST,
}


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required continuation-root input is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def checks_then_bet_prefix(bettor: int) -> tuple[tuple[int, str], ...]:
    rows = observed_bet_sequence(bettor)
    prefix = tuple((int(row["actor"]), str(row["action"])) for row in rows)
    expected = tuple((seat, "check") for seat in range(bettor)) + ((bettor, "bet"),)
    if prefix != expected:
        raise ValueError("continuation prefix is not exact checks-then-bet")
    return prefix


def _finite_tree(value: Any) -> bool:
    if isinstance(value, Mapping):
        return all(_finite_tree(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return all(_finite_tree(item) for item in value)
    if isinstance(value, float):
        return math.isfinite(value)
    return True


def _policy_subtree_utility(
    layout: PublicTreeTensorEvaluator,
    policy: Mapping[str, Mapping[str, float]],
    root_history: tuple[tuple[int, str], ...],
) -> tuple[float, ...]:
    probabilities = layout._prepare_policy(policy)
    root_index = next(
        index for index, node in enumerate(layout.nodes) if node.history == root_history
    )

    def evaluate(node_index: int) -> np.ndarray:
        node = layout.nodes[node_index]
        if node.terminal_slot >= 0:
            return layout.terminal_values[node.terminal_slot]
        result = np.zeros((layout.deal_count, layout.num_players), dtype=np.float64)
        values = probabilities[node_index]
        assert values is not None
        for action_index, child in enumerate(node.children):
            result += values[:, action_index, None] * evaluate(child)
        return result

    return tuple(layout.weights @ evaluate(root_index))


def continuation_identity(
    full: PublicTreeTensorEvaluator,
    continuation: PublicTreeTensorEvaluator,
    *,
    hands_by_player: tuple[tuple[Any, ...], ...],
    blueprint: Mapping[str, Mapping[str, float]],
) -> dict[str, Any]:
    """Compare one continuation layout to its exact full-tree subtree."""

    full_by_history = {node.history: node for node in full.nodes}
    full_terminal_keys = _terminal_keys_by_slot(full)
    continuation_terminal_keys = _terminal_keys_by_slot(continuation)
    topology_mismatches = 0
    information_key_mismatches = 0
    terminal_key_mismatches = 0
    maximum_terminal_error = 0.0
    for node in continuation.nodes:
        teacher = full_by_history.get(node.history)
        if teacher is None or (
            node.player,
            node.actions,
            tuple(continuation.nodes[child].history for child in node.children),
        ) != (
            teacher.player,
            teacher.actions,
            tuple(full.nodes[child].history for child in teacher.children),
        ):
            topology_mismatches += 1
            continue
        if node.information_keys != teacher.information_keys:
            information_key_mismatches += 1
        if node.terminal_slot >= 0:
            if (
                continuation_terminal_keys[node.terminal_slot]
                != full_terminal_keys[teacher.terminal_slot]
            ):
                terminal_key_mismatches += 1
            maximum_terminal_error = max(
                maximum_terminal_error,
                float(
                    np.max(
                        np.abs(
                            continuation.terminal_values[node.terminal_slot]
                            - full.terminal_values[teacher.terminal_slot]
                        )
                    )
                ),
            )
    schema = information_schema_for_axes(continuation, hands_by_player)
    missing = sorted(set(schema) - set(blueprint))
    action_mismatches = sum(
        key in blueprint and set(blueprint[key]) != set(actions)
        for key, actions in schema.items()
    )
    restricted = {key: dict(blueprint[key]) for key in schema if key in blueprint}
    full_utility = _policy_subtree_utility(full, blueprint, continuation.nodes[0].history)
    continuation_utility = continuation.evaluate(restricted).evaluation.utilities
    maximum_utility_error = max(
        abs(float(left) - float(right))
        for left, right in zip(full_utility, continuation_utility, strict=True)
    )
    return {
        "public_prefix": [list(row) for row in continuation.public_prefix],
        "public_nodes": continuation.public_node_count,
        "strategic_nodes": continuation.strategic_node_count,
        "terminal_nodes": continuation.terminal_node_count,
        "information_set_count": len(schema),
        "terminal_group_count": len(set(continuation_terminal_keys)),
        "topology_mismatches": topology_mismatches,
        "information_key_mismatches": information_key_mismatches,
        "terminal_key_mismatches": terminal_key_mismatches,
        "maximum_terminal_payoff_error": maximum_terminal_error,
        "missing_blueprint_information_sets": missing,
        "blueprint_action_schema_mismatches": action_mismatches,
        "restricted_blueprint_policy_sha256": policy_digest(restricted),
        "maximum_fixed_policy_subtree_utility_error": maximum_utility_error,
        "topology_mismatch_count_across_deals": continuation.topology_mismatch_count(),
    }


def _automaton_identity(
    full: tuple[dict[str, Any], ...],
    continuation: tuple[dict[str, Any], ...],
) -> dict[str, Any]:
    missing = 0
    maximum_error = 0.0
    field_mismatches = 0
    for target, library in enumerate(continuation):
        for key, actual in library.items():
            teacher = full[target].get(key)
            if teacher is None:
                missing += 1
                continue
            if (
                actual.contenders,
                actual.target_player,
                actual.contributed,
                actual.final_pot,
                actual.sunk_value,
            ) != (
                teacher.contenders,
                teacher.target_player,
                teacher.contributed,
                teacher.final_pot,
                teacher.sunk_value,
            ):
                field_mismatches += 1
            maximum_error = max(
                maximum_error,
                float(
                    np.max(
                        np.abs(
                            actual.terminal_winner_values
                            - teacher.terminal_winner_values
                        )
                    )
                ),
            )
    return {
        "missing_full_tree_groups": missing,
        "semantic_field_mismatches": field_mismatches,
        "maximum_terminal_winner_value_error": maximum_error,
        "full_unique_automata": len({id(value) for row in full for value in row.values()}),
        "continuation_unique_automata": len(
            {id(value) for row in continuation for value in row.values()}
        ),
        "full_numeric_bytes": sum(
            value.numeric_bytes for value in {id(v): v for row in full for v in row.values()}.values()
        ),
        "continuation_numeric_bytes": sum(
            value.numeric_bytes
            for value in {id(v): v for row in continuation for v in row.values()}.values()
        ),
    }


def mutation_controls(full: PublicTreeTensorEvaluator) -> dict[str, Any]:
    wrong_actor_rejected = False
    terminal_prefix_rejected = False
    try:
        ContinuationPublicTreeTensorEvaluator(
            full.game, public_prefix=((1, "check"),)
        )
    except ValueError:
        wrong_actor_rejected = True
    try:
        ContinuationPublicTreeTensorEvaluator(
            full.game,
            public_prefix=tuple((seat, "check") for seat in range(full.num_players)),
        )
    except ValueError:
        terminal_prefix_rejected = True
    return {
        "wrong_actor_rejected": wrong_actor_rejected,
        "terminal_prefix_rejected": terminal_prefix_rejected,
        "passed": wrong_actor_rejected and terminal_prefix_rejected,
    }


def _parse_config(config: dict[str, Any]) -> dict[str, Any]:
    for field, path in _PATHS.items():
        if config.get(field) != _sha256(path):
            raise ValueError(f"continuation-root provenance mismatch: {field}")
    exact = {
        "evidence_stage": "preregistered_after_adr0222_before_any_continuation_root_warm_step_feature_or_strategy_label",
        "seed": 20260821,
        "scope": "all_twelve_frozen_action_conditioned_targets_label_free_topology_policy_payoff_and_automaton_identity_only",
        "root_rule": "replay_every_observed_check_and_final_bet_then_compile_only_exact_descendants",
        "pot": 12.0,
        "stack": 30.0,
        "bet_size": 3.0,
        "players": 6,
        "hands_per_player": 32,
        "axis_seed": 20260819,
        "mixture_components": 3,
        "split_index": 3,
        "query_chunk_records": 256,
        "strategy_label_policy": "zero_warm_steps_zero_quality_evaluations_zero_affine_features_zero_certificates",
    }
    for field, value in exact.items():
        if config.get(field) != value:
            raise ValueError(f"continuation-root field differs from ADR-0223: {field}")
    if len(config.get("targets", ())) != 12:
        raise ValueError("continuation-root preflight requires all twelve targets")
    gates = {
        "expected_targets": 12,
        "expected_public_nodes": 63,
        "expected_strategic_nodes": 31,
        "expected_terminal_nodes": 32,
        "expected_information_sets": 992,
        "expected_terminal_groups": 32,
        "maximum_terminal_payoff_error": 0.0,
        "maximum_fixed_policy_utility_error": 1e-12,
        "maximum_automaton_value_error": 0.0,
        "maximum_total_seconds": 600.0,
        "require_clean_git_state": True,
        "require_parents_passed": True,
        "require_source_checkpoint_identity": True,
        "require_target_identity": True,
        "require_blueprint_identity": True,
        "require_topology_identity": True,
        "require_information_key_identity": True,
        "require_terminal_group_identity": True,
        "require_blueprint_restriction_identity": True,
        "require_automaton_identity": True,
        "require_mutation_controls": True,
        "require_new_strategy_labels_zero": True,
        "require_strategy_population_claim_null": True,
        "require_finite": True,
    }
    if config.get("gates") != gates:
        raise ValueError("continuation-root gates differ from ADR-0223")
    return {**config, "targets": tuple(dict(row) for row in config["targets"]), "gates": gates}


def run_h32_continuation_root_preflight(
    config_path: Path = _CONFIG, output_path: Path = _OUTPUT
) -> dict[str, Any]:
    started = time.perf_counter()
    parsed = _parse_config(json.loads(config_path.read_text(encoding="utf-8")))
    git = _strict_git_metadata()
    source_parent = json.loads(_SOURCE.read_text(encoding="utf-8"))
    manifest = json.loads(_MANIFEST.read_text(encoding="utf-8"))
    parent = json.loads(_PARENT.read_text(encoding="utf-8"))
    rows = []
    controls = None
    for spec in parsed["targets"]:
        board = parse_cards(*spec["board"])
        source, full, _, retained = _build_case(
            parsed=parsed,
            board=board,
            hand_count=int(parsed["hands_per_player"]),
            family=str(spec["range_family"]),
        )
        _, _, full_automata = retained
        source_row = next(
            row for row in source_parent["source_rows"] if row["source"] == spec["source"]
        )
        state = source_row["final_checkpoint"]
        blueprint = _average_policy_from_state(state)
        target, _ = build_action_conditioned_posterior(
            source, blueprint, bettor=int(spec["observed_bettor"])
        )
        prefix = checks_then_bet_prefix(int(spec["observed_bettor"]))
        continuation = ContinuationPublicTreeTensorEvaluator(
            full.game, public_prefix=prefix
        )
        identity = continuation_identity(
            full,
            continuation,
            hands_by_player=source.hands_by_player,
            blueprint=blueprint,
        )
        codes = tuple(
            np.ascontiguousarray(values, dtype=np.int32)
            for values in _rank_codes(board, source.hands_by_player)
        )
        continuation_automata = build_leaf_adjoint_terminal_automata(
            continuation,
            codes,
            pot=float(parsed["pot"]),
            bet_size=float(parsed["bet_size"]),
        )
        automaton = _automaton_identity(full_automata, continuation_automata)
        controls = mutation_controls(full) if controls is None else controls
        rows.append(
            {
                "target_id": spec["target_id"],
                "source": spec["source"],
                "observed_bettor": spec["observed_bettor"],
                "source_checkpoint_identity": axis_cfr_checkpoint_digest(state) == state["state_sha256"] and _belief_digest(source) == spec["source_belief_sha256"],
                "target_identity": _belief_digest(target) == spec["target_belief_sha256"],
                "blueprint_identity": policy_digest(blueprint) == state["average_policy_sha256"],
                "continuation": identity,
                "automaton": automaton,
            }
        )
    total_seconds = time.perf_counter() - started
    gate = parsed["gates"]
    gates = {
        "clean_git": (not git["dirty"]) == gate["require_clean_git_state"],
        "parents_passed": bool(manifest["passed"] and parent["passed"]) == gate["require_parents_passed"],
        "target_count": len(rows) == gate["expected_targets"],
        "source_checkpoint_identity": all(row["source_checkpoint_identity"] for row in rows) == gate["require_source_checkpoint_identity"],
        "target_identity": all(row["target_identity"] for row in rows) == gate["require_target_identity"],
        "blueprint_identity": all(row["blueprint_identity"] for row in rows) == gate["require_blueprint_identity"],
        "node_counts": all((row["continuation"]["public_nodes"], row["continuation"]["strategic_nodes"], row["continuation"]["terminal_nodes"], row["continuation"]["information_set_count"], row["continuation"]["terminal_group_count"]) == (gate["expected_public_nodes"], gate["expected_strategic_nodes"], gate["expected_terminal_nodes"], gate["expected_information_sets"], gate["expected_terminal_groups"]) for row in rows),
        "topology_identity": all(row["continuation"]["topology_mismatches"] == 0 and row["continuation"]["topology_mismatch_count_across_deals"] == 0 for row in rows) == gate["require_topology_identity"],
        "information_key_identity": all(row["continuation"]["information_key_mismatches"] == 0 for row in rows) == gate["require_information_key_identity"],
        "terminal_group_identity": all(row["continuation"]["terminal_key_mismatches"] == 0 and row["continuation"]["maximum_terminal_payoff_error"] <= gate["maximum_terminal_payoff_error"] for row in rows) == gate["require_terminal_group_identity"],
        "blueprint_restriction_identity": all(not row["continuation"]["missing_blueprint_information_sets"] and row["continuation"]["blueprint_action_schema_mismatches"] == 0 and row["continuation"]["maximum_fixed_policy_subtree_utility_error"] <= gate["maximum_fixed_policy_utility_error"] for row in rows) == gate["require_blueprint_restriction_identity"],
        "automaton_identity": all(row["automaton"]["missing_full_tree_groups"] == 0 and row["automaton"]["semantic_field_mismatches"] == 0 and row["automaton"]["maximum_terminal_winner_value_error"] <= gate["maximum_automaton_value_error"] for row in rows) == gate["require_automaton_identity"],
        "mutation_controls": bool(controls and controls["passed"]) == gate["require_mutation_controls"],
        "new_strategy_labels_zero": True == gate["require_new_strategy_labels_zero"],
        "strategy_population_claim_null": True == gate["require_strategy_population_claim_null"],
        "total_time": total_seconds <= gate["maximum_total_seconds"],
        "finite": _finite_tree(rows) == gate["require_finite"],
    }
    gates["passed"] = all(gates.values())
    result = {
        "schema_version": 1,
        "status": "h32_continuation_root_preflight_executed",
        "environment": {**environment_metadata(), "git": git},
        "config_sha256": _sha256(config_path),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "methodology": {"warm_steps": 0, "quality_evaluations": 0, "affine_features": 0, "certificates": 0, "strategy_labels": 0},
        "target_rows": rows,
        "mutation_controls": controls,
        "aggregate": {
            "full_public_nodes": 385,
            "continuation_public_nodes": 63,
            "full_strategic_nodes": 192,
            "continuation_strategic_nodes": 31,
            "strategic_node_reduction_fraction": 1.0 - 31.0 / 192.0,
            "full_terminal_nodes": 193,
            "full_terminal_groups": 64,
            "continuation_terminal_groups": 32,
            "automaton_numeric_byte_ratio": max(row["automaton"]["continuation_numeric_bytes"] / row["automaton"]["full_numeric_bytes"] for row in rows),
        },
        "gates": gates,
        "passed": gates["passed"],
        "decision": "authorize_continuation_root_warm_step_preregistration" if gates["passed"] else "reject_continuation_root_preflight",
        "strategy_population_claim": None,
        "total_seconds": total_seconds,
        "limitations": [
            "This preflight proves topology, policy-key, payoff, and automaton identity only.",
            "It performs no continuation-root warm step, quality evaluation, feature extraction, or strategy certificate.",
            "It does not yet establish wall-clock speedup or strategy quality.",
        ],
    }
    output_path.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=_CONFIG)
    parser.add_argument("--output", type=Path, default=_OUTPUT)
    args = parser.parse_args()
    result = run_h32_continuation_root_preflight(args.config, args.output)
    print(json.dumps({"output": str(args.output), "passed": result["passed"], "decision": result["decision"], "aggregate": result["aggregate"]}, indent=2))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
