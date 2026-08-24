"""Frozen responder-row growth audit on ADR-0347's exact legal h4 tree.

This is a bounded infrastructure and finite-algebra experiment.  It observes
one production row-generation call, retains every exact response signature and
row, and checks those rows and candidate values with the independent Fraction
enumerator.  It emits no action and supplies no selector-stability, action-
clock, preparation-bank, full-width, or strategy-quality result.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
from fractions import Fraction
import hashlib
import json
from math import isfinite
import os
from pathlib import Path
from types import MappingProxyType
import time
from typing import Any, Mapping

import numpy as np

from .evaluation import Policy, collect_information_sets
from .exact_sequence_form_coefficient_oracle import (
    ExactAffinePayoff,
    exact_expected_utilities,
    exact_open_axis_payoff_coefficients,
    exact_sequence_axis,
)
from .game import Action, CHANCE_PLAYER, TERMINAL_PLAYER, GameState
from .h32_affine_resident_cache_preflight import _strict_git_metadata
from .legal_decision_spine_v2 import public_betting_state_sha256
from .legal_responder_raise_h4_coefficient_result import (
    verify_adr0347_legal_h4_coefficient_result_artifact,
)
from .legal_river_continuation import LegalHeadsUpRiverContinuation
from .no_limit_betting import (
    CALL,
    CHECK,
    FOLD,
    BettingAction,
    BettingStreet,
    NoLimitBettingState,
)
from .one_seat_convex_generation import AffinePayoff, ResponseSignature
from .one_seat_row_growth_audit import (
    AuditedEvaluation,
    AuditedResponseRow,
    OneSeatRowGrowthAudit,
    audit_one_seat_row_growth,
)
from .river import RiverDeal, make_hole, parse_cards
from .runner_harness import assemble_environment, finalize_gates, serialize_result


_ROOT = Path(__file__).parents[2]
_CONFIG = _ROOT / "experiments/configs/legal-responder-raise-h4-row-growth-v1.json"
_OUTPUT = _ROOT / "experiments/results/legal-responder-raise-h4-row-growth-v1.json"
_IMPLEMENTATION = Path(__file__)
_PATHS = {
    "expected_parent_decision_sha256": (
        _ROOT
        / "docs/decisions/ADR-0347-retain-and-seal-the-legal-h4-coefficient-result.md"
    ),
    "expected_parent_artifact_sha256": (
        _ROOT
        / "experiments/results/legal-responder-raise-h4-coefficient-differential-v1.json"
    ),
    "expected_parent_result_owner_sha256": (
        _ROOT / "src/pontius/legal_responder_raise_h4_coefficient_result.py"
    ),
    "expected_legal_kernel_sha256": _ROOT / "src/pontius/no_limit_betting.py",
    "expected_legal_game_sha256": _ROOT / "src/pontius/legal_river_continuation.py",
    "expected_generation_primitive_sha256": (
        _ROOT / "src/pontius/one_seat_convex_generation.py"
    ),
    "expected_audit_source_sha256": _ROOT / "src/pontius/one_seat_row_growth_audit.py",
    "expected_evaluation_sha256": _ROOT / "src/pontius/evaluation.py",
    "expected_exact_oracle_sha256": (
        _ROOT / "src/pontius/exact_sequence_form_coefficient_oracle.py"
    ),
    "expected_implementation_sha256": _IMPLEMENTATION,
    "expected_control_test_sha256": (
        _ROOT / "tests/test_legal_responder_raise_h4_row_growth.py"
    ),
    "expected_audit_test_sha256": _ROOT / "tests/test_one_seat_row_growth_audit.py",
}

_FROZEN_ROOT_HANDS = (
    ("As", "Ad"),
    ("Kh", "Kd"),
    ("8s", "8d"),
    ("6s", "5s"),
)
_FROZEN_RESPONDER_HANDS = (
    ("Ts", "8h"),
    ("Qs", "Qd"),
    ("9s", "9d"),
    ("Ac", "Kc"),
)
_FROZEN_JOINT_WEIGHT_NUMERATORS = (
    (1, 2, 1, 4),
    (2, 1, 3, 1),
    (1, 3, 1, 2),
    (4, 1, 2, 3),
)


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required h4 row-growth input is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_sha256(value: object) -> str:
    rendered = json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
        allow_nan=False,
    ).encode("utf-8")


def _action_token(action: object) -> str:
    return str(action)


def _fraction_record(value: Fraction) -> dict[str, int]:
    return {"numerator": value.numerator, "denominator": value.denominator}


def _policy_sha256(policy: Policy) -> str:
    return _canonical_sha256(
        [
            {
                "information_key": key,
                "actions": [
                    {
                        "action": _action_token(action),
                        "probability_hex": float(probability).hex(),
                    }
                    for action, probability in sorted(
                        row.items(), key=lambda item: _action_token(item[0])
                    )
                ],
            }
            for key, row in sorted(policy.items())
        ]
    )


def _response_sha256(signature: ResponseSignature) -> str:
    return _canonical_sha256(
        [
            {"information_key": key, "action": _action_token(action)}
            for key, action in signature
        ]
    )


def _exact_affine_digest(row: ExactAffinePayoff) -> str:
    return _canonical_sha256(
        {
            "constant": _fraction_record(row.constant),
            "coefficients": [
                {
                    "information_key": key,
                    "action": _action_token(action),
                    "value": _fraction_record(value),
                }
                for (key, action), value in sorted(
                    row.coefficients.items(),
                    key=lambda item: (item[0][0], _action_token(item[0][1])),
                )
            ],
        }
    )


def _parse_config(config: dict[str, Any]) -> dict[str, Any]:
    expected = {
        "evidence_stage",
        *_PATHS,
        "board",
        "button",
        "starting_stack",
        "small_blind",
        "big_blind",
        "root_hands",
        "responder_hands",
        "joint_weight_numerators",
        "joint_weight_denominator",
        "acting_player",
        "source_policy_version",
        "guard",
        "max_iterations",
        "tolerance",
        "response_signature_identity",
        "retained_row_byte_definition",
        "expected_root_public_state_sha256",
        "expected_public_schema_sha256",
        "expected_game_structural_sha256",
        "expected_h4_game_provenance_sha256",
        "expected_source_policy_sha256",
        "expected_initial_response_sha256s",
        "expected_initial_exact_row_sha256s",
        "claims_policy",
        "gates",
    }
    if set(config) != expected:
        raise ValueError("h4 row-growth config fields differ from ADR-0348")
    for field, path in _PATHS.items():
        if config[field] != _sha256(path):
            raise ValueError(f"h4 row-growth provenance mismatch: {field}")
    frozen = {
        "evidence_stage": (
            "preregistered_after_adr0347_before_legal_h4_row_growth_run"
        ),
        "board": ["2c", "7d", "9h", "Js", "Qc"],
        "button": 0,
        "starting_stack": 6,
        "small_blind": 1,
        "big_blind": 2,
        "root_hands": [list(hand) for hand in _FROZEN_ROOT_HANDS],
        "responder_hands": [list(hand) for hand in _FROZEN_RESPONDER_HANDS],
        "joint_weight_numerators": [
            list(row) for row in _FROZEN_JOINT_WEIGHT_NUMERATORS
        ],
        "joint_weight_denominator": 32,
        "acting_player": 0,
        "source_policy_version": "adr0346-dyadic-key-rotated-policy-v1",
        "guard": 0.25,
        "max_iterations": 128,
        "tolerance": 1e-10,
        "response_signature_identity": (
            "exact_target_player_plus_complete_sorted_information_key_action_tuple"
        ),
        "retained_row_byte_definition": (
            "canonical_compact_utf8_semantic_row_record_excluding_retained_bytes"
        ),
        "expected_root_public_state_sha256": (
            "d6976d35018153790f63698d7231d1f920f21c1dfb865a5a0733bd42d1cbcf52"
        ),
        "expected_public_schema_sha256": (
            "1b399b2b67b58bd2a8a42d3c0e8ddeb4fbf3d2445f2f059a36c3e5905227d5ff"
        ),
        "expected_game_structural_sha256": (
            "2eacfe54c73ea0030b45d472aaef86106e6a1ebf276d59bf196852cd35c6acaf"
        ),
        "expected_h4_game_provenance_sha256": (
            "31eb059bdd32f74fc0f72dd07927b21d32493cc2831cacac22b3fe8615658214"
        ),
        "expected_source_policy_sha256": (
            "b69b34a644a6c3cec3094584735e8807aed1b24abdaa39806bce3540bebda55a"
        ),
        "expected_initial_response_sha256s": [
            "83b57620097d496624aabfa49fdba1ab64ccb5cd519a9daf20130ade55f7e908",
            "778a91ab318ea0c94d1baa8dcfe9481ed6155604cc964a6b014720b0b20877f8",
        ],
        "expected_initial_exact_row_sha256s": [
            "7be24d40786a55761142e3bfdf230f5b6ddbac5320703cd44050d4d2f345f4a5",
            "3c1b73c33f1f5ede4ea8a9ccf415c5337a3c033ae4a5549177a19324b0543d90",
        ],
        "claims_policy": (
            "legal_h4_response_row_growth_and_infrastructure_only_no_selector_"
            "stability_preparation_bank_action_clock_action_quality_or_full_width_claim"
        ),
    }
    for field, value in frozen.items():
        if config[field] != value:
            raise ValueError(f"h4 row-growth field differs: {field}")
    expected_gates = {
        "expected_hand_counts": [4, 4],
        "expected_joint_deals": 16,
        "expected_terminal_paths": 176,
        "expected_acting_information_sets": 12,
        "expected_sequence_variables": 32,
        "expected_initial_rows_by_player": [1, 1],
        "maximum_iterations": 128,
        "maximum_final_optimality_gap": 1e-8,
        "maximum_float_exact_evaluation_error": 1e-9,
        "maximum_float_exact_row_error": 1e-12,
        "maximum_master_duality_gap": 1e-8,
        "maximum_master_constraint_violation": 1e-8,
        "maximum_realization_equivalence_error": 1e-8,
        "maximum_conditioning_rebind_error": 1e-10,
        "maximum_retained_row_bytes": 8388608,
        "maximum_subject_generation_seconds": 60.0,
        "maximum_total_seconds": 120.0,
        "require_clean_git_state": True,
        "require_parent_pass": True,
        "require_initial_row_identities": True,
        "require_exact_signature_dedup": True,
        "require_exact_row_identities": True,
        "require_exact_evaluation_identities": True,
        "require_exact_convergence_classification": True,
        "require_exact_incumbent_feasible": True,
        "require_bound_monotonicity": True,
        "require_oracle_accounting_identity": True,
        "require_conditioning_finite": True,
        "require_all_rows_retained": True,
        "require_converged": True,
        "require_finite": True,
    }
    if config["gates"] != expected_gates:
        raise ValueError("h4 row-growth gates differ from ADR-0348")
    return {
        **config,
        "board": tuple(config["board"]),
        "root_hands": tuple(tuple(hand) for hand in config["root_hands"]),
        "responder_hands": tuple(
            tuple(hand) for hand in config["responder_hands"]
        ),
        "joint_weight_numerators": tuple(
            tuple(int(value) for value in row)
            for row in config["joint_weight_numerators"]
        ),
        "expected_initial_response_sha256s": tuple(
            config["expected_initial_response_sha256s"]
        ),
        "expected_initial_exact_row_sha256s": tuple(
            config["expected_initial_exact_row_sha256s"]
        ),
        "gates": dict(config["gates"]),
    }


def _checked_to_river(parsed: Mapping[str, Any]) -> NoLimitBettingState:
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
            raise AssertionError("h4 row-growth preflop order drifted")
        state = state.apply_action(action)
    for street in (BettingStreet.FLOP, BettingStreet.TURN, BettingStreet.RIVER):
        state = state.advance_street()
        if state.street is not street:
            raise AssertionError("h4 row-growth street order drifted")
        if street is not BettingStreet.RIVER:
            state = state.apply_action(CHECK).apply_action(CHECK)
    if state.acting_seat != 1:
        raise AssertionError("h4 row-growth first river actor drifted")
    return state.apply_action(CHECK)


def _build_game(parsed: Mapping[str, Any]) -> LegalHeadsUpRiverContinuation:
    weights = parsed["joint_weight_numerators"]
    deals = tuple(
        (
            RiverDeal(make_hole(*root), make_hole(*responder)),
            float(weights[root_index][responder_index]),
        )
        for root_index, root in enumerate(parsed["root_hands"])
        for responder_index, responder in enumerate(parsed["responder_hands"])
    )
    return LegalHeadsUpRiverContinuation(
        board=parse_cards(*parsed["board"]),
        base_state=_checked_to_river(parsed),
        deals=deals,
    )


def _rotated(values: tuple[float, ...], offset: int) -> tuple[float, ...]:
    index = offset % len(values)
    return (*values[index:], *values[:index])


def _source_policy(game: LegalHeadsUpRiverContinuation) -> Policy:
    templates = {
        2: (0.25, 0.75),
        3: (0.25, 0.25, 0.5),
        4: (0.125, 0.25, 0.125, 0.5),
    }
    policy: Policy = {}
    for player in range(game.num_players):
        for key, actions in collect_information_sets(game, player).items():
            try:
                template = templates[len(actions)]
            except KeyError as exc:
                raise ValueError("h4 row-growth source found unexpected width") from exc
            digest = hashlib.sha256(
                f"adr0346|player={player}|{key}".encode("utf-8")
            ).digest()
            probabilities = _rotated(template, int.from_bytes(digest[:2], "big"))
            policy[key] = dict(zip(actions, probabilities, strict=True))
    return policy


def _tree_terminal_paths(game: LegalHeadsUpRiverContinuation) -> int:
    def walk(state: GameState) -> int:
        if state.current_player == TERMINAL_PLAYER:
            return 1
        if state.current_player == CHANCE_PLAYER:
            return sum(
                walk(state.apply_action(action))
                for action, _ in state.chance_outcomes()
            )
        return sum(walk(state.apply_action(action)) for action in state.legal_actions())

    return walk(game.initial_state())


def _deterministic_response_policy(
    game: LegalHeadsUpRiverContinuation,
    policy: Policy,
    player: int,
    signature: ResponseSignature,
) -> Policy:
    information_sets = collect_information_sets(game, player)
    selected = dict(signature)
    if set(selected) != set(information_sets):
        raise ValueError("h4 response signature does not cover its information sets")
    result = {key: dict(row) for key, row in policy.items()}
    result.update(
        {
            key: {
                action: float(action == selected[key]) for action in actions
            }
            for key, actions in information_sets.items()
        }
    )
    return result


def _exact_response_row(
    game: LegalHeadsUpRiverContinuation,
    blueprint: Policy,
    acting_player: int,
    exact_profile: tuple[ExactAffinePayoff, ...],
    row: AuditedResponseRow,
) -> ExactAffinePayoff:
    fixed = _deterministic_response_policy(
        game,
        blueprint,
        row.target_player,
        row.signature,
    )
    if row.target_player == acting_player:
        response_value = exact_expected_utilities(game, fixed)[acting_player]
        profile = exact_profile[acting_player]
        return ExactAffinePayoff(
            response_value - profile.constant,
            MappingProxyType(
                {token: -value for token, value in profile.coefficients.items()}
            ),
        )
    response = exact_open_axis_payoff_coefficients(
        game,
        fixed,
        acting_player=acting_player,
        payoff_player=row.target_player,
    )
    return response.subtract(exact_profile[row.target_player])


def _row_record(
    row: AuditedResponseRow,
    exact: ExactAffinePayoff,
    variables: tuple[tuple[str, Action], ...],
) -> tuple[dict[str, Any], int, float, bool]:
    if set(exact.coefficients) != set(variables):
        raise ValueError("h4 exact response row axis differs")
    errors = [abs(row.gain.constant - float(exact.constant))]
    exact_identity = Fraction.from_float(row.gain.constant) == exact.constant
    coefficients = []
    for token, subject in zip(variables, row.gain.coefficients, strict=True):
        exact_value = exact.coefficients[token]
        error = abs(subject - float(exact_value))
        errors.append(error)
        exact_identity &= Fraction.from_float(subject) == exact_value
        coefficients.append(
            {
                "information_key": token[0],
                "action": _action_token(token[1]),
                "subject_hex": subject.hex(),
                "exact": _fraction_record(exact_value),
                "absolute_error": error,
            }
        )
    semantic = {
        "ordinal": row.ordinal,
        "phase": row.phase,
        "after_iteration": row.after_iteration,
        "target_player": row.target_player,
        "signature": [
            {"information_key": key, "action": _action_token(action)}
            for key, action in row.signature
        ],
        "signature_sha256": _response_sha256(row.signature),
        "constant_subject_hex": row.gain.constant.hex(),
        "constant_exact": _fraction_record(exact.constant),
        "coefficients": coefficients,
        "exact_row_sha256": _exact_affine_digest(exact),
        "maximum_coefficient_error": max(errors, default=0.0),
        "exact_float_identity": exact_identity,
    }
    retained_bytes = len(_canonical_bytes(semantic))
    return (
        {**semantic, "retained_bytes": retained_bytes},
        retained_bytes,
        max(errors, default=0.0),
        exact_identity,
    )


def _exact_evaluation(
    game: LegalHeadsUpRiverContinuation,
    audited: AuditedEvaluation,
) -> tuple[dict[str, Any], tuple[Fraction, ...], float, bool]:
    utilities = exact_expected_utilities(game, audited.policy)
    response_values = tuple(
        exact_expected_utilities(
            game,
            _deterministic_response_policy(
                game,
                audited.policy,
                player,
                audited.response_signatures[player],
            ),
        )[player]
        for player in range(game.num_players)
    )
    gains = tuple(
        response - utility
        for response, utility in zip(response_values, utilities, strict=True)
    )
    nonnegative = all(value >= 0 for value in gains)
    exact_nash_conv = sum(gains, Fraction(0))
    subject = audited.evaluation
    errors = [
        *(abs(value - float(exact)) for value, exact in zip(subject.utilities, utilities)),
        *(
            abs(value - float(exact))
            for value, exact in zip(subject.best_response_values, response_values)
        ),
        *(
            abs(value - float(exact))
            for value, exact in zip(subject.deviation_gains, gains)
        ),
        abs(subject.nash_conv - float(exact_nash_conv)),
    ]
    record = {
        "ordinal": audited.ordinal,
        "policy_sha256": _policy_sha256(audited.policy),
        "response_signature_sha256s": [
            _response_sha256(signature)
            for signature in audited.response_signatures
        ],
        "response_signatures": [
            [
                {"information_key": key, "action": _action_token(action)}
                for key, action in signature
            ]
            for signature in audited.response_signatures
        ],
        "utilities_exact": [_fraction_record(value) for value in utilities],
        "best_response_values_exact": [
            _fraction_record(value) for value in response_values
        ],
        "deviation_gains_exact": [_fraction_record(value) for value in gains],
        "nash_conv_exact": _fraction_record(exact_nash_conv),
        "maximum_float_exact_error": max(errors, default=0.0),
        "exact_gains_nonnegative": nonnegative,
    }
    return record, gains, max(errors, default=0.0), nonnegative


def _conditioning_records(
    audit: OneSeatRowGrowthAudit,
    tolerance: float,
) -> tuple[list[dict[str, Any]], float, bool]:
    records = []
    maximum_error = 0.0
    finite = True
    for player, production in enumerate(audit.result.conditioning_by_player):
        rows = tuple(row for row in audit.response_rows if row.target_player == player)
        raw = np.asarray(
            [[row.gain.constant, *row.gain.coefficients] for row in rows],
            dtype=np.float64,
        )
        norms = np.linalg.norm(raw, axis=1)
        normalized = raw.copy()
        for index, norm in enumerate(norms):
            if norm > tolerance:
                normalized[index] /= norm
        minimum = None
        for left in range(len(rows)):
            for right in range(left + 1, len(rows)):
                distance = float(np.linalg.norm(normalized[left] - normalized[right]))
                minimum = distance if minimum is None else min(minimum, distance)
        singular = np.linalg.svd(normalized, compute_uv=False)
        threshold = tolerance * max(normalized.shape) * max(float(singular[0]), 1.0)
        nonzero = singular[singular > threshold]
        condition = None if len(nonzero) == 0 else float(nonzero[0] / nonzero[-1])
        rebound = {
            "rows": len(rows),
            "numerical_rank": len(nonzero),
            "minimum_normalized_separation": minimum,
            "effective_condition_number": condition,
        }
        production_record = asdict(production)
        for field in ("minimum_normalized_separation", "effective_condition_number"):
            left = production_record[field]
            right = rebound[field]
            if left is not None and right is not None:
                maximum_error = max(maximum_error, abs(float(left) - float(right)))
        finite &= all(
            value is None or not isinstance(value, float) or isfinite(value)
            for value in rebound.values()
        )
        records.append({"player": player, "production": production_record, "rebound": rebound})
    return records, maximum_error, finite


def _finite_tree(value: Any) -> bool:
    if value is None or isinstance(value, (str, bool)):
        return True
    if isinstance(value, (int, float)):
        return not isinstance(value, float) or isfinite(value)
    if isinstance(value, dict):
        return all(_finite_tree(key) and _finite_tree(item) for key, item in value.items())
    if isinstance(value, (list, tuple)):
        return all(_finite_tree(item) for item in value)
    return False


def _write_exclusive(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if os.path.lexists(path):
        raise FileExistsError(f"h4 row-growth result path already exists: {path}")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags, 0o644)
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


def _environment(git: Mapping[str, Any] | None) -> dict[str, Any]:
    return assemble_environment(
        runtime={"backend": "cpu_float64_generation_fraction_audit"},
        git=(
            dict(git)
            if git is not None
            else {"available": False, "reason": "failure_before_git_snapshot"}
        ),
    )


def _execute_growth(
    parsed: Mapping[str, Any],
    *,
    git: Mapping[str, Any],
) -> dict[str, Any]:
    started = time.perf_counter()
    parent = verify_adr0347_legal_h4_coefficient_result_artifact()
    game = _build_game(parsed)
    if public_betting_state_sha256(game.base_state) != parsed[
        "expected_root_public_state_sha256"
    ]:
        raise ValueError("h4 row-growth root state differs")
    if game.structural_digest != parsed["expected_game_structural_sha256"]:
        raise ValueError("h4 row-growth structural game differs")
    if game.provenance_digest != parsed["expected_h4_game_provenance_sha256"]:
        raise ValueError("h4 row-growth private range differs")
    if parent.record["public_schema_sha256"] != parsed["expected_public_schema_sha256"]:
        raise ValueError("h4 row-growth parent public schema differs")
    source = _source_policy(game)
    if _policy_sha256(source) != parsed["expected_source_policy_sha256"]:
        raise ValueError("h4 row-growth source policy differs")

    acting_player = int(parsed["acting_player"])
    subject_started = time.perf_counter()
    audit = audit_one_seat_row_growth(
        game,
        source,
        acting_player=acting_player,
        guard=float(parsed["guard"]),
        max_iterations=int(parsed["max_iterations"]),
        tolerance=float(parsed["tolerance"]),
    )
    subject_seconds = time.perf_counter() - subject_started

    exact_axis = exact_sequence_axis(game, acting_player)
    exact_profile = tuple(
        exact_open_axis_payoff_coefficients(
            game,
            source,
            acting_player=acting_player,
            payoff_player=player,
        )
        for player in range(game.num_players)
    )
    row_records = []
    retained_row_bytes = 0
    maximum_row_error = 0.0
    exact_row_identities = True
    for row in audit.response_rows:
        exact = _exact_response_row(
            game,
            source,
            acting_player,
            exact_profile,
            row,
        )
        record, row_bytes, row_error, exact_identity = _row_record(
            row,
            exact,
            exact_axis.variables,
        )
        row_records.append(record)
        retained_row_bytes += row_bytes
        maximum_row_error = max(maximum_row_error, row_error)
        exact_row_identities &= exact_identity

    evaluation_records = []
    exact_gains = []
    maximum_evaluation_error = 0.0
    exact_gains_nonnegative = True
    for evaluated in audit.evaluations:
        record, gains, error, nonnegative = _exact_evaluation(game, evaluated)
        evaluation_records.append(record)
        exact_gains.append(gains)
        maximum_evaluation_error = max(maximum_evaluation_error, error)
        exact_gains_nonnegative &= nonnegative

    tolerance = float(parsed["tolerance"])
    exact_threshold = Fraction.from_float(100.0 * tolerance)
    exact_guard = Fraction.from_float(float(parsed["guard"]))
    exact_caps = tuple(value + exact_guard for value in exact_gains[0])
    cap_error = max(
        (
            abs(value - float(exact))
            for value, exact in zip(audit.result.caps, exact_caps, strict=True)
        ),
        default=0.0,
    )
    iteration_records = []
    exact_convergence_classification = True
    exact_feasibility_classification = True
    for update, master, gains in zip(
        audit.result.iterations,
        audit.masters,
        exact_gains[1:],
        strict=True,
    ):
        cap_violations = tuple(
            gain - cap for gain, cap in zip(gains, exact_caps, strict=True)
        )
        epigraph_violations = tuple(
            gain - Fraction.from_float(value)
            for gain, value in zip(gains, master.epigraph, strict=True)
        )
        exact_feasible = max(cap_violations, default=Fraction(0)) <= exact_threshold
        exact_converged = (
            max(epigraph_violations, default=Fraction(0)) <= exact_threshold
        )
        exact_feasibility_classification &= exact_feasible == update.candidate_feasible
        exact_convergence_classification &= exact_converged == update.converged
        iteration_records.append(
            {
                **asdict(update),
                "response_signature_sha256s": evaluation_records[update.iteration][
                    "response_signature_sha256s"
                ],
                "epigraph_hex": [value.hex() for value in master.epigraph],
                "master": {
                    "objective_hex": master.solution.objective.hex(),
                    "dual_objective_hex": master.solution.dual_objective.hex(),
                    "duality_gap": master.solution.duality_gap,
                    "pivots": master.solution.pivots,
                    "maximum_constraint_violation": (
                        master.solution.max_constraint_violation
                    ),
                },
                "exact_candidate_feasible": exact_feasible,
                "exact_converged": exact_converged,
                "maximum_exact_cap_violation": _fraction_record(
                    max(cap_violations, default=Fraction(0))
                ),
                "maximum_exact_epigraph_violation": _fraction_record(
                    max(epigraph_violations, default=Fraction(0))
                ),
            }
        )

    # Re-select the final incumbent tapes through the production evaluator only
    # once outside the measured generator would violate the selector boundary.
    # The incumbent is therefore exact-checked when it equals a retained
    # candidate, which the policy digest binds below.
    candidate_by_digest = {
        record["policy_sha256"]: (record, gains)
        for record, gains in zip(evaluation_records, exact_gains, strict=True)
    }
    final_digest = _policy_sha256(audit.result.policy)
    if final_digest not in candidate_by_digest:
        raise AssertionError("h4 incumbent is not a retained evaluated policy")
    final_record, final_gains = candidate_by_digest[final_digest]
    final_exact_nash_conv = sum(final_gains, Fraction(0))
    final_upper_error = abs(audit.result.upper_bound - float(final_exact_nash_conv))
    exact_incumbent_feasible = (
        max(
            (gain - cap for gain, cap in zip(final_gains, exact_caps, strict=True)),
            default=Fraction(0),
        )
        <= exact_threshold
    )
    conditioning, conditioning_error, conditioning_finite = _conditioning_records(
        audit,
        tolerance,
    )
    signature_keys = [
        (row.target_player, row.signature) for row in audit.response_rows
    ]
    exact_signature_dedup = len(signature_keys) == len(set(signature_keys))
    initial_rows = tuple(row for row in row_records if row["phase"] == "initial")
    initial_identity = (
        tuple(row["target_player"] for row in initial_rows) == (0, 1)
        and tuple(row["signature_sha256"] for row in initial_rows)
        == parsed["expected_initial_response_sha256s"]
        and tuple(row["exact_row_sha256"] for row in initial_rows)
        == parsed["expected_initial_exact_row_sha256s"]
    )
    added_acting = sum(
        row.phase == "generated" and row.target_player == acting_player
        for row in audit.response_rows
    )
    responder_rows_before = []
    for update in audit.result.iterations:
        responder_rows_before.append(
            sum(
                row.target_player != acting_player
                and (
                    row.phase == "initial"
                    or (
                        row.after_iteration is not None
                        and row.after_iteration < update.iteration
                    )
                )
                for row in audit.response_rows
            )
        )
    expected_oracles = {
        "best_response_calls": 2 * (1 + len(audit.result.iterations)) + 1 + added_acting,
        "expected_utilities_calls": (
            1 + len(audit.result.iterations) + sum(responder_rows_before)
        ),
        "open_axis_coefficient_calls": 2
        + sum(row.target_player != acting_player for row in audit.response_rows),
        "evaluation_calls": 1 + len(audit.result.iterations),
        "master_calls": len(audit.result.iterations),
        "response_row_calls": len(audit.response_rows),
    }
    observed_oracles = {
        "best_response_calls": audit.best_response_calls,
        "expected_utilities_calls": audit.expected_utilities_calls,
        "open_axis_coefficient_calls": audit.open_axis_coefficient_calls,
        "evaluation_calls": len(audit.evaluations),
        "master_calls": len(audit.masters),
        "response_row_calls": len(audit.response_rows),
    }
    oracle_accounting_identity = observed_oracles == expected_oracles

    lower_bounds = tuple(update.master_lower_bound for update in audit.result.iterations)
    upper_bounds = tuple(update.incumbent_upper_bound for update in audit.result.iterations)
    maximum_duality_gap = max(
        (master.solution.duality_gap for master in audit.masters), default=0.0
    )
    maximum_constraint_violation = max(
        (master.solution.max_constraint_violation for master in audit.masters),
        default=0.0,
    )
    maximum_equivalence_error = max(
        (
            update.realization_equivalence_max_error
            for update in audit.result.iterations
        ),
        default=0.0,
    )
    total_seconds = time.perf_counter() - started
    gates = parsed["gates"]
    hand_counts = [
        len({deal.hand(player) for deal, _ in game.deals})
        for player in range(game.num_players)
    ]
    root = game.initial_state().apply_action(game.deals[0][0])
    root_raises = [
        action.raise_to
        for action in root.legal_actions()
        if isinstance(action, BettingAction) and action.raise_to is not None
    ]
    payload = {
        "parent_artifact_sha256": _sha256(_PATHS["expected_parent_artifact_sha256"]),
        "root_public_state_sha256": public_betting_state_sha256(game.base_state),
        "public_schema_sha256": parent.record["public_schema_sha256"],
        "game_structural_sha256": game.structural_digest,
        "game_provenance_sha256": game.provenance_digest,
        "fixture": {
            "hand_counts": hand_counts,
            "joint_deals": len(game.deals),
            "terminal_paths": _tree_terminal_paths(game),
            "table_seats": list(game.table_seats),
            "root_raise_to_totals": root_raises,
        },
        "axis": {
            "acting_player": acting_player,
            "information_sets": len(exact_axis.information_sets),
            "sequence_variables": len(exact_axis.variables),
        },
        "source_policy_sha256": _policy_sha256(source),
        "final_policy_sha256": final_digest,
        "final_policy_evaluation_ordinal": final_record["ordinal"],
        "baseline_nash_conv": audit.result.baseline_nash_conv,
        "caps": list(audit.result.caps),
        "exact_caps": [_fraction_record(value) for value in exact_caps],
        "cap_identity_error": cap_error,
        "converged": audit.result.converged,
        "lower_bound": audit.result.lower_bound,
        "upper_bound": audit.result.upper_bound,
        "optimality_gap": audit.result.optimality_gap,
        "final_exact_nash_conv": _fraction_record(final_exact_nash_conv),
        "final_upper_bound_exact_error": final_upper_error,
        "response_rows_by_player": list(audit.result.response_rows_by_player),
        "exact_duplicate_response_hits": audit.result.exact_duplicate_response_hits,
        "iterations": iteration_records,
        "evaluations": evaluation_records,
        "response_rows": row_records,
        "conditioning": conditioning,
        "oracle_accounting": {
            "observed": observed_oracles,
            "expected_from_call_graph": expected_oracles,
            "identity": oracle_accounting_identity,
        },
        "retained_row_bytes": retained_row_bytes,
        "maximum_float_exact_row_error": maximum_row_error,
        "maximum_float_exact_evaluation_error": maximum_evaluation_error,
        "maximum_conditioning_rebind_error": conditioning_error,
        "maximum_master_duality_gap": maximum_duality_gap,
        "maximum_master_constraint_violation": maximum_constraint_violation,
        "maximum_realization_equivalence_error": maximum_equivalence_error,
        "exact_row_identities": exact_row_identities,
        "exact_gains_nonnegative": exact_gains_nonnegative,
        "exact_convergence_classification": exact_convergence_classification,
        "exact_feasibility_classification": exact_feasibility_classification,
        "exact_incumbent_feasible": exact_incumbent_feasible,
        "timing": {
            "subject_generation_seconds": subject_seconds,
            "exact_audit_and_plumbing_seconds": max(0.0, total_seconds - subject_seconds),
            "total_infrastructure_seconds": total_seconds,
        },
        "quality_rows_serialized": 0,
        "strategy_labels_generated": 0,
    }
    checks = {
        "clean_git": (not git["dirty"]) == gates["require_clean_git_state"],
        "parent_pass": bool(parent.record["passed"]) == gates["require_parent_pass"],
        "fixture_identity": hand_counts == gates["expected_hand_counts"]
        and len(game.deals) == gates["expected_joint_deals"]
        and _tree_terminal_paths(game) == gates["expected_terminal_paths"],
        "axis_identity": len(exact_axis.information_sets)
        == gates["expected_acting_information_sets"]
        and len(exact_axis.variables) == gates["expected_sequence_variables"],
        "initial_row_identities": initial_identity
        == gates["require_initial_row_identities"],
        "initial_row_counts": [
            sum(
                row.phase == "initial" and row.target_player == player
                for row in audit.response_rows
            )
            for player in range(game.num_players)
        ]
        == gates["expected_initial_rows_by_player"],
        "iteration_bound": len(audit.result.iterations) <= gates["maximum_iterations"],
        "converged": audit.result.converged == gates["require_converged"],
        "final_gap": audit.result.optimality_gap
        <= gates["maximum_final_optimality_gap"],
        "exact_signature_dedup": exact_signature_dedup
        == gates["require_exact_signature_dedup"]
        and audit.result.exact_duplicate_response_hits == 0,
        "exact_row_identities": exact_row_identities
        == gates["require_exact_row_identities"]
        and maximum_row_error <= gates["maximum_float_exact_row_error"],
        "exact_evaluation_identities": exact_gains_nonnegative
        == gates["require_exact_evaluation_identities"]
        and maximum_evaluation_error
        <= gates["maximum_float_exact_evaluation_error"],
        "exact_convergence_classification": (
            exact_convergence_classification
            and exact_feasibility_classification
        )
        == gates["require_exact_convergence_classification"],
        "exact_incumbent_feasible": exact_incumbent_feasible
        == gates["require_exact_incumbent_feasible"]
        and final_upper_error <= gates["maximum_float_exact_evaluation_error"],
        "bound_monotonicity": (
            lower_bounds == tuple(sorted(lower_bounds))
            and upper_bounds == tuple(sorted(upper_bounds, reverse=True))
        )
        == gates["require_bound_monotonicity"],
        "master_certificate_diagnostics": maximum_duality_gap
        <= gates["maximum_master_duality_gap"]
        and maximum_constraint_violation
        <= gates["maximum_master_constraint_violation"],
        "realization_equivalence": maximum_equivalence_error
        <= gates["maximum_realization_equivalence_error"],
        "oracle_accounting": oracle_accounting_identity
        == gates["require_oracle_accounting_identity"],
        "conditioning": conditioning_finite
        == gates["require_conditioning_finite"]
        and conditioning_error <= gates["maximum_conditioning_rebind_error"],
        "all_rows_retained": len(row_records) == sum(audit.result.response_rows_by_player)
        and gates["require_all_rows_retained"],
        "retained_row_bytes": retained_row_bytes
        <= gates["maximum_retained_row_bytes"],
        "subject_time": subject_seconds
        <= gates["maximum_subject_generation_seconds"],
        "total_time": total_seconds <= gates["maximum_total_seconds"],
    }
    checks["finite"] = _finite_tree(payload) == gates["require_finite"]
    gate_result = finalize_gates(checks)
    return {
        **payload,
        **gate_result,
        "decision": (
            "authorize_legal_responder_raise_selector_stability_preregistration"
            if gate_result["passed"]
            else "reject_legal_h4_responder_row_growth_boundary"
        ),
        "total_seconds": total_seconds,
    }


def run_legal_responder_raise_h4_row_growth(
    config_path: Path = _CONFIG,
    output_path: Path = _OUTPUT,
) -> dict[str, Any]:
    """Execute the sole frozen ADR-0348 invocation and retain its terminal."""

    if os.path.lexists(output_path):
        raise FileExistsError(f"h4 row-growth result path already exists: {output_path}")
    started = time.perf_counter()
    stage = "config"
    git: Mapping[str, Any] | None = None
    try:
        parsed = _parse_config(json.loads(config_path.read_text(encoding="utf-8")))
        stage = "git"
        git = _strict_git_metadata()
        stage = "row_generation"
        payload = _execute_growth(parsed, git=git)
        result = {
            "schema_version": 1,
            "status": "legal_responder_raise_h4_row_growth_executed",
            "environment": _environment(git),
            "config_sha256": _sha256(config_path),
            "implementation_sha256": _sha256(_IMPLEMENTATION),
            "audit_source_sha256": _sha256(_PATHS["expected_audit_source_sha256"]),
            "methodology": {
                "betting_authority": "NoLimitBettingState",
                "subject": "production_one_seat_sequence_form_row_generation",
                "observer": "single_threaded_read_only_boundary_instrumentation",
                "teacher": "independent_fraction_terminal_and_coefficient_enumerator",
                "deduplication": parsed["response_signature_identity"],
                "retained_row_bytes": parsed["retained_row_byte_definition"],
                "quality_rows": 0,
                "strategy_labels": 0,
            },
            **payload,
            "strategy_quality_claim": None,
            "limitations": [
                "This is one h4 legal checked-to heads-up river infrastructure audit.",
                "Response signatures identify generated rows; selector stability is not claimed.",
                "The bounded subject wall is campaign infrastructure time, not action latency.",
                "No preparation-bank, full-width, action, or strategy-quality result is emitted.",
            ],
        }
    except Exception as error:
        result = {
            "schema_version": 1,
            "status": "legal_responder_raise_h4_row_growth_failed",
            "environment": _environment(git),
            "config_sha256": _sha256(config_path) if config_path.is_file() else None,
            "implementation_sha256": _sha256(_IMPLEMENTATION),
            "passed": False,
            "decision": "reject_legal_h4_responder_row_growth_boundary",
            "failure": {
                "stage": stage,
                "type": type(error).__name__,
                "message": str(error),
            },
            "total_seconds": time.perf_counter() - started,
            "strategy_quality_claim": None,
        }
    _write_exclusive(output_path, serialize_result(result))
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=_CONFIG)
    parser.add_argument("--output", type=Path, default=_OUTPUT)
    args = parser.parse_args()
    result = run_legal_responder_raise_h4_row_growth(args.config, args.output)
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
