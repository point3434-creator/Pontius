"""Frozen small-game gate for exact legal responder-raise semantics.

The prospective run binds the six-seat betting kernel to a two-player checked-
to river continuation, then compares sequence-form row generation with the
complete normal-form teacher.  The result is a semantic and finite-algebra
control only; it carries no strategy-quality or latency label.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import time
from typing import Any

from .evaluation import evaluate_profile
from .game import TERMINAL_PLAYER
from .h32_affine_resident_cache_preflight import _strict_git_metadata
from .legal_decision_spine_v2 import public_betting_state_sha256
from .legal_river_continuation import LegalHeadsUpRiverContinuation
from .no_limit_betting import (
    CALL,
    CHECK,
    FOLD,
    BettingStreet,
    NoLimitBettingState,
    raise_to,
)
from .one_seat_convex_generation import (
    path_single_visit_report,
    require_behavioral_affine_shortcut,
    retreat_one_seat_policy,
    solve_one_seat_complete_normal_form_teacher,
    solve_one_seat_with_row_generation,
)
from .river import RiverDeal, evaluate_seven, make_hole, parse_cards
from .river_multi_size import BetAction, MultiSizeRiverHoldem
from .runner_harness import assemble_environment, finalize_gates, serialize_result


_ROOT = Path(__file__).parents[2]
_CONFIG = _ROOT / "experiments/configs/responder-raise-semantics-keystone-v1.json"
_OUTPUT = _ROOT / "experiments/results/responder-raise-semantics-keystone-v1.json"
_PARENT_DECISION = (
    _ROOT
    / "docs/decisions/ADR-0343-retain-and-seal-the-width-three-transfer-confirmation.md"
)
_LEGAL_KERNEL = _ROOT / "src/pontius/no_limit_betting.py"
_LEGAL_GAME = _ROOT / "src/pontius/legal_river_continuation.py"
_SEQUENCE_FORM = _ROOT / "src/pontius/one_seat_convex_generation.py"
_LEGAL_GAME_TEST = _ROOT / "tests/test_legal_river_continuation.py"
_IMPLEMENTATION = Path(__file__)
_TEST = _ROOT / "tests/test_responder_raise_semantics_keystone.py"

_PATHS = {
    "expected_parent_decision_sha256": _PARENT_DECISION,
    "expected_legal_kernel_sha256": _LEGAL_KERNEL,
    "expected_legal_game_sha256": _LEGAL_GAME,
    "expected_sequence_form_sha256": _SEQUENCE_FORM,
    "expected_legal_game_test_sha256": _LEGAL_GAME_TEST,
    "expected_implementation_sha256": _IMPLEMENTATION,
    "expected_control_test_sha256": _TEST,
}


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required responder-raise input is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _parse_config(config: dict[str, Any]) -> dict[str, Any]:
    expected = {
        "evidence_stage",
        *_PATHS,
        "board",
        "button",
        "starting_stack",
        "small_blind",
        "big_blind",
        "expected_root_public_state_sha256",
        "expected_table_seats",
        "expected_root_raise_to_totals",
        "expected_public_schema_sha256",
        "root_hand",
        "responder_hand",
        "acting_player",
        "blueprint",
        "guard",
        "retreat_factor",
        "max_iterations",
        "max_pure_plans",
        "tolerance",
        "claims_policy",
        "gates",
    }
    if set(config) != expected:
        raise ValueError("responder-raise config fields differ from ADR-0344")
    for field, path in _PATHS.items():
        if config[field] != _sha256(path):
            raise ValueError(f"responder-raise provenance mismatch: {field}")
    frozen = {
        "evidence_stage": (
            "preregistered_after_adr0343_before_legal_responder_raise_keystone_run"
        ),
        "board": ["2c", "7d", "9h", "Js", "Qc"],
        "button": 0,
        "starting_stack": 6,
        "small_blind": 1,
        "big_blind": 2,
        "expected_table_seats": [2, 1],
        "expected_root_raise_to_totals": [2, 3, 4],
        "root_hand": ["As", "Ad"],
        "responder_hand": ["Kh", "Kd"],
        "acting_player": 0,
        "blueprint": "uniform_behavioral",
        "guard": 0.25,
        "retreat_factor": 0.8,
        "max_iterations": 128,
        "max_pure_plans": 1000,
        "tolerance": 1e-10,
        "claims_policy": (
            "legal_semantics_and_finite_algebra_only_no_quality_latency_or_multiway_claim"
        ),
    }
    for field, value in frozen.items():
        if config[field] != value:
            raise ValueError(f"responder-raise field differs from ADR-0344: {field}")
    if not isinstance(config["expected_root_public_state_sha256"], str) or len(
        config["expected_root_public_state_sha256"]
    ) != 64:
        raise ValueError("responder-raise root-state digest is invalid")
    if not isinstance(config["expected_public_schema_sha256"], str) or len(
        config["expected_public_schema_sha256"]
    ) != 64:
        raise ValueError("responder-raise public-schema digest is invalid")
    expected_gates = {
        "expected_strategic_nodes": 6,
        "expected_terminal_nodes": 11,
        "expected_acting_pure_plans": 16,
        "expected_response_pure_plans": 18,
        "expected_short_all_in_raise_branches": 1,
        "maximum_terminal_oracle_error_chips": 0.0,
        "maximum_teacher_objective_error": 1e-9,
        "maximum_exact_incumbent_error": 1e-9,
        "maximum_final_optimality_gap": 1e-9,
        "maximum_retreat_jensen_error": 1e-9,
        "maximum_realization_equivalence_error": 1e-9,
        "maximum_total_seconds": 60.0,
        "require_clean_git_state": True,
        "require_every_action_from_kernel": True,
        "require_full_raise_branch": True,
        "require_short_all_in_branch": True,
        "require_short_all_in_final_response_only": True,
        "require_legacy_short_all_in_omission_detected": True,
        "require_repeated_actor_topology": True,
        "require_behavioral_shortcut_rejection": True,
        "require_bound_monotonicity": True,
        "require_exact_digest_dedup_only": True,
        "require_finite": True,
    }
    if config["gates"] != expected_gates:
        raise ValueError("responder-raise gates differ from ADR-0344")
    return {
        **config,
        "board": tuple(config["board"]),
        "expected_table_seats": tuple(config["expected_table_seats"]),
        "expected_root_raise_to_totals": tuple(
            config["expected_root_raise_to_totals"]
        ),
        "root_hand": tuple(config["root_hand"]),
        "responder_hand": tuple(config["responder_hand"]),
        "gates": dict(config["gates"]),
    }


def _checked_to_river(parsed: dict[str, Any]) -> NoLimitBettingState:
    stack = int(parsed["starting_stack"])
    state = NoLimitBettingState.new_hand(
        button=int(parsed["button"]),
        starting_stacks=(stack,) * 6,
        small_blind=int(parsed["small_blind"]),
        big_blind=int(parsed["big_blind"]),
    )
    for expected_seat, action in (
        (3, FOLD),
        (4, FOLD),
        (5, FOLD),
        (0, FOLD),
        (1, CALL),
        (2, CHECK),
    ):
        if state.acting_seat != expected_seat:
            raise AssertionError("preregistered preflop order drifted")
        state = state.apply_action(action)
    for street in (BettingStreet.FLOP, BettingStreet.TURN, BettingStreet.RIVER):
        state = state.advance_street()
        if state.street is not street:
            raise AssertionError("preregistered street order drifted")
        if street is not BettingStreet.RIVER:
            state = state.apply_action(CHECK).apply_action(CHECK)
    if state.acting_seat != 1:
        raise AssertionError("preregistered first river actor drifted")
    return state.apply_action(CHECK)


def _action_token(action: object) -> str:
    return str(action)


def _history_token(history: tuple[tuple[int, object], ...]) -> str:
    if not history:
        return "root"
    return "/".join(f"p{player}:{_action_token(action)}" for player, action in history)


def _terminal_oracle(game: LegalHeadsUpRiverContinuation, state: Any) -> tuple[float, float]:
    history = tuple(action for _, action in state.continuation_history)
    if not history:
        raise AssertionError("terminal continuation has no public action")
    root_rank = evaluate_seven((*game.board, *state.deal.player0))
    responder_rank = evaluate_seven((*game.board, *state.deal.player1))
    root_sign = 1.0 if root_rank > responder_rank else -1.0
    if root_rank == responder_rank:
        root_sign = 0.0
    if history == (CHECK,):
        magnitude = game.base_state.pot / 2.0
        root_value = root_sign * magnitude
    elif history[-1] == FOLD:
        if len(history) == 2:
            root_value = game.base_state.pot / 2.0
        elif len(history) == 3:
            opening = history[0].raise_to
            if opening is None:
                raise AssertionError("post-raise fold lacks an opening amount")
            root_value = -(game.base_state.pot / 2.0 + opening)
        else:
            raise AssertionError("fold terminal has an unknown history")
    elif history[-1] == CALL:
        contribution = history[-2].raise_to
        if contribution is None:
            raise AssertionError("call terminal lacks a wager amount")
        magnitude = game.base_state.pot / 2.0 + contribution
        root_value = root_sign * magnitude
    else:
        raise AssertionError("terminal history has no independent oracle case")
    return float(root_value), float(-root_value)


def _public_semantics(game: LegalHeadsUpRiverContinuation) -> dict[str, Any]:
    deal = game.deals[0][0]
    root = game.initial_state().apply_action(deal)
    schema: dict[str, dict[str, Any]] = {}
    terminals: dict[str, tuple[float, float]] = {}
    oracle_errors = []
    every_action_from_kernel = True
    full_raise_branches = 0
    short_all_in_branches = 0
    short_all_in_final_response_only = True

    def walk(state: Any) -> None:
        nonlocal every_action_from_kernel
        nonlocal full_raise_branches
        nonlocal short_all_in_branches
        nonlocal short_all_in_final_response_only
        history = _history_token(state.continuation_history)
        if state.current_player == TERMINAL_PLAYER:
            actual = state.returns()
            expected = _terminal_oracle(game, state)
            terminals[history] = actual
            oracle_errors.extend(abs(left - right) for left, right in zip(actual, expected))
            return
        actions = state.legal_actions()
        direct = tuple(
            action
            for action in (
                FOLD if state.betting.legal_decision().can_fold else None,
                CHECK if state.betting.legal_decision().can_check else None,
                CALL if state.betting.legal_decision().can_call else None,
            )
            if action is not None
        )
        bounds = state.betting.legal_decision().raise_bounds
        direct = (*direct, *(
            ()
            if bounds is None
            else tuple(
                raise_to(amount)
                for amount in range(bounds.minimum_raise_to, bounds.maximum_raise_to + 1)
            )
        ))
        every_action_from_kernel &= actions == direct
        schema[history] = {
            "acting_player": state.current_player,
            "actions": [_action_token(action) for action in actions],
        }
        for action in actions:
            child = state.apply_action(action)
            if action == raise_to(4) and len(child.continuation_history) == 2:
                if child.betting.history[-1].full_raise:
                    full_raise_branches += 1
                else:
                    short_all_in_branches += 1
                    short_all_in_final_response_only &= child.legal_actions() == (
                        FOLD,
                        CALL,
                    )
            walk(child)

    walk(root)
    rendered = json.dumps(schema, separators=(",", ":"), sort_keys=True)
    return {
        "public_schema": schema,
        "public_schema_sha256": hashlib.sha256(rendered.encode("ascii")).hexdigest(),
        "strategic_nodes": len(schema),
        "terminal_nodes": len(terminals),
        "terminal_histories": sorted(terminals),
        "maximum_terminal_oracle_error_chips": max(oracle_errors, default=0.0),
        "every_action_from_kernel": every_action_from_kernel,
        "full_raise_branches": full_raise_branches,
        "short_all_in_raise_branches": short_all_in_branches,
        "short_all_in_final_response_only": short_all_in_final_response_only,
    }


def _legacy_short_all_in_omission(parsed: dict[str, Any], deal: RiverDeal) -> bool:
    game = MultiSizeRiverHoldem.from_joint_weights(
        board=parse_cards(*parsed["board"]),
        pot=4.0,
        stacks=(4.0, 4.0),
        bet_sizes=(2.0, 3.0, 4.0),
        raise_to_sizes=(4.0,),
        joint_weights={deal: 1.0},
    )
    dealt = game.initial_state().apply_action(deal)
    bet_three = next(action for action in game.bet_actions if action == BetAction(3.0))
    legacy_actions = dealt.apply_action(bet_three).legal_actions()
    return len(legacy_actions) == 2 and tuple(map(str, legacy_actions)) == ("fold", "call")


def _finite_tree(value: Any) -> bool:
    if value is None or isinstance(value, (str, bool)):
        return True
    if isinstance(value, (int, float)):
        return value == value and value not in (float("inf"), float("-inf"))
    if isinstance(value, dict):
        return all(_finite_tree(key) and _finite_tree(item) for key, item in value.items())
    if isinstance(value, (list, tuple)):
        return all(_finite_tree(item) for item in value)
    return False


def _write_exclusive(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        try:
            os.close(descriptor)
        except OSError:
            pass
        raise


def run_responder_raise_semantics_keystone(
    config_path: Path = _CONFIG,
    output_path: Path = _OUTPUT,
) -> dict[str, Any]:
    """Run the frozen ADR-0344 gate once and retain it without clobbering."""

    started = time.perf_counter()
    if output_path.exists():
        raise FileExistsError("responder-raise result path already exists")
    parsed = _parse_config(json.loads(config_path.read_text(encoding="utf-8")))
    git = _strict_git_metadata()
    base = _checked_to_river(parsed)
    if public_betting_state_sha256(base) != parsed["expected_root_public_state_sha256"]:
        raise ValueError("responder-raise root betting state digest differs")
    deal = RiverDeal(
        make_hole(*parsed["root_hand"]),
        make_hole(*parsed["responder_hand"]),
    )
    game = LegalHeadsUpRiverContinuation(
        board=parse_cards(*parsed["board"]),
        base_state=base,
        deals=((deal, 1.0),),
    )
    if game.table_seats != parsed["expected_table_seats"]:
        raise ValueError("responder-raise table-seat mapping differs")
    root_actions = game.initial_state().apply_action(deal).legal_actions()
    root_raises = tuple(
        action.raise_to for action in root_actions if action.raise_to is not None
    )
    if root_raises != parsed["expected_root_raise_to_totals"]:
        raise ValueError("responder-raise root legal universe differs")

    semantics = _public_semantics(game)
    topology = path_single_visit_report(game)
    shortcut_rejected = False
    try:
        require_behavioral_affine_shortcut(game)
    except ValueError:
        shortcut_rejected = True

    generated = solve_one_seat_with_row_generation(
        game,
        {},
        acting_player=int(parsed["acting_player"]),
        guard=float(parsed["guard"]),
        max_iterations=int(parsed["max_iterations"]),
        tolerance=float(parsed["tolerance"]),
    )
    teacher = solve_one_seat_complete_normal_form_teacher(
        game,
        {},
        acting_player=int(parsed["acting_player"]),
        guard=float(parsed["guard"]),
        max_pure_plans=int(parsed["max_pure_plans"]),
        tolerance=float(parsed["tolerance"]),
    )
    baseline = evaluate_profile(game, {})
    endpoint = evaluate_profile(game, generated.policy)
    retreated_policy = retreat_one_seat_policy(
        game,
        {},
        generated.policy,
        acting_player=int(parsed["acting_player"]),
        factor=float(parsed["retreat_factor"]),
        tolerance=float(parsed["tolerance"]),
    )
    retreated = evaluate_profile(game, retreated_policy)
    factor = float(parsed["retreat_factor"])
    jensen_errors = tuple(
        max(0.0, mixed - ((1.0 - factor) * source + factor * target))
        for mixed, source, target in zip(
            retreated.deviation_gains,
            baseline.deviation_gains,
            endpoint.deviation_gains,
            strict=True,
        )
    )
    summed_jensen_error = max(
        0.0,
        factor * (baseline.nash_conv - endpoint.nash_conv)
        - (baseline.nash_conv - retreated.nash_conv),
    )
    maximum_jensen_error = max((*jensen_errors, summed_jensen_error), default=0.0)
    lower_bounds = tuple(row.master_lower_bound for row in generated.iterations)
    upper_bounds = tuple(row.incumbent_upper_bound for row in generated.iterations)
    maximum_equivalence_error = max(
        (row.realization_equivalence_max_error for row in generated.iterations),
        default=0.0,
    )
    total_seconds = time.perf_counter() - started
    gates = parsed["gates"]
    checks = {
        "clean_git": (not git["dirty"]) == gates["require_clean_git_state"],
        "public_schema": semantics["public_schema_sha256"]
        == parsed["expected_public_schema_sha256"],
        "strategic_node_count": semantics["strategic_nodes"]
        == gates["expected_strategic_nodes"],
        "terminal_node_count": semantics["terminal_nodes"]
        == gates["expected_terminal_nodes"],
        "every_action_from_kernel": semantics["every_action_from_kernel"]
        == gates["require_every_action_from_kernel"],
        "full_raise_branch": (semantics["full_raise_branches"] >= 1)
        == gates["require_full_raise_branch"],
        "short_all_in_branch": (
            semantics["short_all_in_raise_branches"]
            == gates["expected_short_all_in_raise_branches"]
        )
        == gates["require_short_all_in_branch"],
        "short_all_in_final_response_only": semantics[
            "short_all_in_final_response_only"
        ]
        == gates["require_short_all_in_final_response_only"],
        "legacy_short_all_in_omission_detected": _legacy_short_all_in_omission(
            parsed,
            deal,
        )
        == gates["require_legacy_short_all_in_omission_detected"],
        "terminal_oracle_identity": semantics["maximum_terminal_oracle_error_chips"]
        <= gates["maximum_terminal_oracle_error_chips"],
        "repeated_actor_topology": (not topology.passed and topology.repeated_player == 0)
        == gates["require_repeated_actor_topology"],
        "behavioral_shortcut_rejection": shortcut_rejected
        == gates["require_behavioral_shortcut_rejection"],
        "generated_converged": generated.converged,
        "teacher_plan_counts": teacher.acting_pure_plans
        == gates["expected_acting_pure_plans"]
        and teacher.response_pure_plans[1] == gates["expected_response_pure_plans"],
        "teacher_objective_identity": abs(generated.lower_bound - teacher.objective)
        <= gates["maximum_teacher_objective_error"],
        "incumbent_identity": abs(generated.upper_bound - teacher.objective)
        <= gates["maximum_exact_incumbent_error"],
        "final_gap": generated.optimality_gap <= gates["maximum_final_optimality_gap"],
        "retreat_jensen": maximum_jensen_error
        <= gates["maximum_retreat_jensen_error"],
        "realization_equivalence": maximum_equivalence_error
        <= gates["maximum_realization_equivalence_error"],
        "bound_monotonicity": (
            lower_bounds == tuple(sorted(lower_bounds))
            and upper_bounds == tuple(sorted(upper_bounds, reverse=True))
        )
        == gates["require_bound_monotonicity"],
        "exact_digest_dedup_only": (generated.exact_duplicate_response_hits == 0)
        == gates["require_exact_digest_dedup_only"],
        "total_time": total_seconds <= gates["maximum_total_seconds"],
    }
    payload = {
        "root_public_state_sha256": public_betting_state_sha256(base),
        "game_structural_sha256": game.structural_digest,
        "game_provenance_sha256": game.provenance_digest,
        "table_seats": list(game.table_seats),
        "root_raise_to_totals": list(root_raises),
        "semantics": semantics,
        "topology": {
            "path_single_visit": topology.passed,
            "repeated_player": topology.repeated_player,
            "witness": [_action_token(action) for action in topology.witness_actions],
            "behavioral_shortcut_rejected": shortcut_rejected,
        },
        "generated": {
            "baseline_nash_conv": generated.baseline_nash_conv,
            "caps": list(generated.caps),
            "converged": generated.converged,
            "lower_bound": generated.lower_bound,
            "upper_bound": generated.upper_bound,
            "optimality_gap": generated.optimality_gap,
            "iterations": [asdict(row) for row in generated.iterations],
            "response_rows_by_player": list(generated.response_rows_by_player),
            "conditioning_by_player": [
                asdict(row) for row in generated.conditioning_by_player
            ],
            "exact_duplicate_response_hits": generated.exact_duplicate_response_hits,
        },
        "teacher": {
            "objective": teacher.objective,
            "exact_nash_conv": teacher.exact_nash_conv,
            "acting_pure_plans": teacher.acting_pure_plans,
            "response_pure_plans": list(teacher.response_pure_plans),
            "simplex_pivots": teacher.simplex_pivots,
            "maximum_exact_error": teacher.maximum_exact_error,
        },
        "retreat": {
            "factor": factor,
            "maximum_jensen_error": maximum_jensen_error,
        },
        "maximum_realization_equivalence_error": maximum_equivalence_error,
        "quality_rows_serialized": 0,
        "strategy_labels_generated": 0,
    }
    checks["finite"] = _finite_tree(payload) == gates["require_finite"]
    gate_result = finalize_gates(checks)
    result = {
        "schema_version": 1,
        "status": "legal_responder_raise_semantics_keystone_executed",
        "environment": assemble_environment(
            runtime={"backend": "cpu_float64_exact_small_game"},
            git=git,
        ),
        "config_sha256": _sha256(config_path),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "legal_game_sha256": _sha256(_LEGAL_GAME),
        "methodology": {
            "betting_authority": "NoLimitBettingState",
            "open_axis": "one_seat_sequence_form_realization",
            "teacher": "complete_mixed_normal_form_direct_utility_evaluation",
            "quality_rows": 0,
            "strategy_labels": 0,
        },
        **payload,
        **gate_result,
        "decision": (
            "authorize_h4_legal_responder_raise_open_axis_differential"
            if gate_result["passed"]
            else "reject_legal_responder_raise_keystone"
        ),
        "total_seconds": total_seconds,
        "strategy_quality_claim": None,
        "limitations": [
            "This is one deterministic checked-to heads-up river continuation.",
            "Private width is one hand per player and supplies no population evidence.",
            "The result does not establish multiway closure, selector stability, or latency.",
            "The result emits no production action and carries no poker-strength label.",
        ],
    }
    rendered = serialize_result(result)
    _write_exclusive(output_path, rendered)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=_CONFIG)
    parser.add_argument("--output", type=Path, default=_OUTPUT)
    args = parser.parse_args()
    result = run_responder_raise_semantics_keystone(args.config, args.output)
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
