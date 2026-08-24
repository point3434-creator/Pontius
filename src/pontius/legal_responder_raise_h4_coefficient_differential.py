"""Frozen h4 coefficient differential on the exact legal responder tree.

The subject is the generic Float64 sequence-form open-axis traversal.  The
teacher is a separate Fraction enumerator.  This is a coefficient and fixed-
tape value identity only; it does not optimize a policy or measure capacity.
"""

from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import json
from math import isfinite
import os
from pathlib import Path
from types import MappingProxyType
import time
from typing import Any, Mapping

from .evaluation import (
    Policy,
    best_response,
    collect_information_sets,
    expected_utilities,
)
from .exact_sequence_form_coefficient_oracle import (
    ExactAffinePayoff,
    exact_expected_utilities,
    exact_open_axis_payoff_coefficients,
    exact_sequence_axis,
)
from .game import Action, CHANCE_PLAYER, TERMINAL_PLAYER, GameState
from .h32_affine_resident_cache_preflight import _strict_git_metadata
from .legal_decision_spine_v2 import public_betting_state_sha256
from .legal_river_continuation import LegalHeadsUpRiverContinuation
from .no_limit_betting import (
    CALL,
    CHECK,
    FOLD,
    BettingAction,
    BettingStreet,
    NoLimitBettingState,
    raise_to,
)
from .one_seat_convex_generation import (
    AffinePayoff,
    _sequence_axis,
    open_axis_payoff_coefficients,
    path_single_visit_report,
    require_behavioral_affine_shortcut,
)
from .responder_raise_semantics_keystone_result import (
    verify_adr0345_responder_raise_semantics_result_artifact,
)
from .river import RiverDeal, make_hole, parse_cards
from .runner_harness import assemble_environment, finalize_gates, serialize_result


_ROOT = Path(__file__).parents[2]
_CONFIG = (
    _ROOT
    / "experiments/configs/legal-responder-raise-h4-coefficient-differential-v1.json"
)
_OUTPUT = (
    _ROOT
    / "experiments/results/legal-responder-raise-h4-coefficient-differential-v1.json"
)
_IMPLEMENTATION = Path(__file__)
_PATHS = {
    "expected_parent_decision_sha256": (
        _ROOT
        / "docs/decisions/ADR-0345-retain-and-seal-the-legal-responder-raise-keystone.md"
    ),
    "expected_parent_artifact_sha256": (
        _ROOT / "experiments/results/responder-raise-semantics-keystone-v1.json"
    ),
    "expected_parent_result_owner_sha256": (
        _ROOT / "src/pontius/responder_raise_semantics_keystone_result.py"
    ),
    "expected_legal_kernel_sha256": _ROOT / "src/pontius/no_limit_betting.py",
    "expected_legal_game_sha256": (
        _ROOT / "src/pontius/legal_river_continuation.py"
    ),
    "expected_coefficient_primitive_sha256": (
        _ROOT / "src/pontius/one_seat_convex_generation.py"
    ),
    "expected_evaluation_sha256": _ROOT / "src/pontius/evaluation.py",
    "expected_exact_oracle_sha256": (
        _ROOT / "src/pontius/exact_sequence_form_coefficient_oracle.py"
    ),
    "expected_exact_oracle_test_sha256": (
        _ROOT / "tests/test_exact_sequence_form_coefficient_oracle.py"
    ),
    "expected_implementation_sha256": _IMPLEMENTATION,
    "expected_control_test_sha256": (
        _ROOT
        / "tests/test_legal_responder_raise_h4_coefficient_differential.py"
    ),
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
_FROZEN_ENDPOINT_LABELS = (
    "source",
    "check_fold",
    "bet2_call",
    "bet3_fold",
    "bet3_call",
    "all_in_call",
)


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required h4 coefficient input is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _action_token(action: object) -> str:
    return str(action)


def _fraction_record(value: Fraction) -> dict[str, int]:
    return {
        "numerator": value.numerator,
        "denominator": value.denominator,
    }


def _canonical_sha256(value: object) -> str:
    rendered = json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def _policy_sha256(policy: Policy) -> str:
    payload = [
        {
            "information_key": key,
            "actions": [
                {
                    "action": _action_token(action),
                    "probability_hex": float(probability).hex(),
                }
                for action, probability in sorted(
                    row.items(),
                    key=lambda item: _action_token(item[0]),
                )
            ],
        }
        for key, row in sorted(policy.items())
    ]
    return _canonical_sha256(payload)


def _response_sha256(response: Mapping[str, object]) -> str:
    return _canonical_sha256(
        [
            {"information_key": key, "action": _action_token(action)}
            for key, action in sorted(response.items())
        ]
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
        "coverage_response_version",
        "endpoint_labels",
        "expected_root_public_state_sha256",
        "expected_public_schema_sha256",
        "expected_game_structural_sha256",
        "expected_h4_game_provenance_sha256",
        "expected_source_policy_sha256",
        "expected_coverage_response_sha256",
        "expected_endpoint_policy_sha256s",
        "expected_responder_best_response_sha256",
        "expected_responder_best_response_value_hex",
        "expected_acting_best_response_sha256",
        "expected_acting_best_response_value_hex",
        "tolerance",
        "claims_policy",
        "gates",
    }
    if set(config) != expected:
        raise ValueError("h4 legal coefficient config fields differ from ADR-0346")
    for field, path in _PATHS.items():
        if config[field] != _sha256(path):
            raise ValueError(f"h4 legal coefficient provenance mismatch: {field}")
    frozen = {
        "evidence_stage": (
            "preregistered_after_adr0345_before_legal_h4_coefficient_run"
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
        "coverage_response_version": (
            "adr0346-full-and-short-raise-coverage-response-v1"
        ),
        "endpoint_labels": list(_FROZEN_ENDPOINT_LABELS),
        "tolerance": 1e-12,
        "claims_policy": (
            "legal_h4_coefficient_identity_only_no_selector_capacity_latency_"
            "quality_or_action_claim"
        ),
    }
    for field, value in frozen.items():
        if config[field] != value:
            raise ValueError(f"h4 legal coefficient field differs: {field}")
    digest_fields = (
        "expected_root_public_state_sha256",
        "expected_public_schema_sha256",
        "expected_game_structural_sha256",
        "expected_h4_game_provenance_sha256",
        "expected_source_policy_sha256",
        "expected_coverage_response_sha256",
        "expected_responder_best_response_sha256",
        "expected_acting_best_response_sha256",
    )
    if any(
        not isinstance(config[field], str) or len(config[field]) != 64
        for field in digest_fields
    ):
        raise ValueError("h4 legal coefficient digest field is malformed")
    endpoint_digests = config["expected_endpoint_policy_sha256s"]
    if (
        not isinstance(endpoint_digests, list)
        or len(endpoint_digests) != len(_FROZEN_ENDPOINT_LABELS)
        or any(not isinstance(value, str) or len(value) != 64 for value in endpoint_digests)
    ):
        raise ValueError("h4 legal coefficient endpoint digests are malformed")
    for field in (
        "expected_responder_best_response_value_hex",
        "expected_acting_best_response_value_hex",
    ):
        try:
            value = float.fromhex(config[field])
        except (TypeError, ValueError) as exc:
            raise ValueError(f"h4 legal coefficient {field} is malformed") from exc
        if not isfinite(value):
            raise ValueError(f"h4 legal coefficient {field} is nonfinite")
    expected_gates = {
        "expected_hand_counts": [4, 4],
        "expected_joint_deals": 16,
        "expected_terminal_paths": 176,
        "expected_acting_information_sets": 12,
        "expected_sequence_variables": 32,
        "expected_final_response_variables": 16,
        "expected_endpoint_policies": 6,
        "expected_profile_rows": 2,
        "expected_fixed_response_rows": 2,
        "expected_gain_rows": 2,
        "expected_coverage_raise_choices": 8,
        "expected_coverage_fold_choices": 2,
        "expected_coverage_call_choices": 2,
        "maximum_coefficient_error": 1e-12,
        "maximum_realization_error": 1e-12,
        "maximum_affine_value_error": 1e-12,
        "maximum_float_exact_utility_error": 1e-12,
        "maximum_acting_br_identity_error": 1e-12,
        "maximum_total_seconds": 60.0,
        "require_clean_git_state": True,
        "require_parent_pass": True,
        "require_dyadic_chance_mass": True,
        "require_repeated_actor_topology": True,
        "require_behavioral_shortcut_rejection": True,
        "require_full_and_short_final_sequence_coverage": True,
        "require_exact_affine_identities": True,
        "require_exact_zero_sum": True,
        "require_source_response_tape_identities": True,
        "require_finite": True,
    }
    if config["gates"] != expected_gates:
        raise ValueError("h4 legal coefficient gates differ from ADR-0346")
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
        "endpoint_labels": tuple(config["endpoint_labels"]),
        "expected_endpoint_policy_sha256s": tuple(endpoint_digests),
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
            raise AssertionError("h4 legal fixture preflop order drifted")
        state = state.apply_action(action)
    for street in (BettingStreet.FLOP, BettingStreet.TURN, BettingStreet.RIVER):
        state = state.advance_street()
        if state.street is not street:
            raise AssertionError("h4 legal fixture street order drifted")
        if street is not BettingStreet.RIVER:
            state = state.apply_action(CHECK).apply_action(CHECK)
    if state.acting_seat != 1:
        raise AssertionError("h4 legal fixture first river actor drifted")
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
                raise ValueError("h4 source policy found an unexpected action width") from exc
            digest = hashlib.sha256(
                f"adr0346|player={player}|{key}".encode("utf-8")
            ).digest()
            probabilities = _rotated(template, int.from_bytes(digest[:2], "big"))
            policy[key] = dict(zip(actions, probabilities, strict=True))
    return policy


def _clone_policy(policy: Policy) -> Policy:
    return {key: dict(row) for key, row in policy.items()}


def _deterministic_row(
    actions: tuple[Action, ...],
    selected: Action,
) -> dict[Action, float]:
    if selected not in actions:
        raise ValueError("deterministic h4 policy selected an unavailable action")
    return {action: float(action == selected) for action in actions}


def _endpoint_policies(
    game: LegalHeadsUpRiverContinuation,
    source: Policy,
) -> tuple[tuple[str, Policy], ...]:
    acting_sets = collect_information_sets(game, 0)
    semantic = {
        "check_fold": (CHECK, FOLD),
        "bet2_call": (raise_to(2), CALL),
        "bet3_fold": (raise_to(3), FOLD),
        "bet3_call": (raise_to(3), CALL),
        "all_in_call": (raise_to(4), CALL),
    }
    result: list[tuple[str, Policy]] = [("source", _clone_policy(source))]
    for label in _FROZEN_ENDPOINT_LABELS[1:]:
        root_action, final_action = semantic[label]
        policy = _clone_policy(source)
        for key, actions in acting_sets.items():
            selected = root_action if key.endswith("history=root") else final_action
            policy[key] = _deterministic_row(actions, selected)  # type: ignore[assignment]
        result.append((label, policy))
    return tuple(result)


def _coverage_response(
    game: LegalHeadsUpRiverContinuation,
) -> dict[str, BettingAction]:
    information_sets = collect_information_sets(game, 1)
    selected: dict[str, BettingAction] = {}
    final_index = 0
    for key, actions in information_sets.items():
        if raise_to(4) in actions:
            selected[key] = raise_to(4)
        else:
            selected[key] = FOLD if final_index % 2 == 0 else CALL
            final_index += 1
    return selected


def _policy_with_response(
    source: Policy,
    information_sets: Mapping[str, tuple[Action, ...]],
    response: Mapping[str, Action],
) -> Policy:
    if set(information_sets) != set(response):
        raise ValueError("fixed h4 response does not cover its information sets")
    result = _clone_policy(source)
    for key, actions in information_sets.items():
        result[key] = _deterministic_row(actions, response[key])  # type: ignore[assignment]
    return result


def _replace_acting_policy(
    base: Policy,
    endpoint: Policy,
    acting_sets: Mapping[str, tuple[Action, ...]],
) -> Policy:
    result = _clone_policy(base)
    for key in acting_sets:
        result[key] = dict(endpoint[key])
    return result


def _tree_terminal_paths(game: LegalHeadsUpRiverContinuation) -> int:
    def walk(state: GameState) -> int:
        player = state.current_player
        if player == TERMINAL_PLAYER:
            return 1
        if player == CHANCE_PLAYER:
            return sum(
                walk(state.apply_action(action))
                for action, _ in state.chance_outcomes()
            )
        return sum(
            walk(state.apply_action(action)) for action in state.legal_actions()
        )

    return walk(game.initial_state())


def _exact_affine_digest(row: ExactAffinePayoff) -> str:
    payload = {
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
    return _canonical_sha256(payload)


def _compare_rows(
    label: str,
    subject: AffinePayoff,
    exact: ExactAffinePayoff,
    variables: tuple[tuple[str, Action], ...],
) -> dict[str, Any]:
    if len(subject.coefficients) != len(variables):
        raise ValueError("subject h4 coefficient width differs from its axis")
    if set(exact.coefficients) != set(variables):
        raise ValueError("exact h4 coefficient axis differs from subject")
    coefficients = []
    errors = [abs(subject.constant - float(exact.constant))]
    for token, subject_value in zip(
        variables,
        subject.coefficients,
        strict=True,
    ):
        exact_value = exact.coefficients[token]
        error = abs(subject_value - float(exact_value))
        errors.append(error)
        coefficients.append(
            {
                "information_key": token[0],
                "action": _action_token(token[1]),
                "subject_hex": subject_value.hex(),
                "exact": _fraction_record(exact_value),
                "absolute_error": error,
            }
        )
    return {
        "label": label,
        "constant_subject_hex": subject.constant.hex(),
        "constant_exact": _fraction_record(exact.constant),
        "coefficient_entries": len(coefficients),
        "coefficients": coefficients,
        "exact_row_sha256": _exact_affine_digest(exact),
        "maximum_coefficient_error": max(errors, default=0.0),
    }


def _extract_pair(
    game: LegalHeadsUpRiverContinuation,
    fixed_policy: Policy,
    *,
    acting_player: int,
    payoff_player: int,
) -> tuple[AffinePayoff, ExactAffinePayoff, float, float]:
    subject_started = time.perf_counter()
    subject = open_axis_payoff_coefficients(
        game,
        fixed_policy,
        acting_player=acting_player,
        payoff_player=payoff_player,
    )
    subject_seconds = time.perf_counter() - subject_started
    exact_started = time.perf_counter()
    exact = exact_open_axis_payoff_coefficients(
        game,
        fixed_policy,
        acting_player=acting_player,
        payoff_player=payoff_player,
    )
    exact_seconds = time.perf_counter() - exact_started
    return subject, exact, subject_seconds, exact_seconds


def _subtract_subject(left: AffinePayoff, right: AffinePayoff) -> AffinePayoff:
    return left.subtract(right)


def _constant_minus_subject(constant: float, row: AffinePayoff) -> AffinePayoff:
    return AffinePayoff(
        constant - row.constant,
        tuple(-value for value in row.coefficients),
    )


def _constant_minus_exact(
    constant: Fraction,
    row: ExactAffinePayoff,
) -> ExactAffinePayoff:
    return ExactAffinePayoff(
        constant - row.constant,
        MappingProxyType(
            {token: -value for token, value in row.coefficients.items()}
        ),
    )


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
        raise FileExistsError(f"h4 coefficient result path already exists: {path}")
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
    git_record = (
        dict(git)
        if git is not None
        else {
            "available": False,
            "reason": "failure_before_git_snapshot",
        }
    )
    return assemble_environment(
        runtime={"backend": "cpu_float64_subject_fraction_teacher"},
        git=git_record,
    )


def _execute_differential(
    parsed: Mapping[str, Any],
    *,
    git: Mapping[str, Any],
) -> dict[str, Any]:
    started = time.perf_counter()
    parent = verify_adr0345_responder_raise_semantics_result_artifact()
    game = _build_game(parsed)
    if public_betting_state_sha256(game.base_state) != parsed[
        "expected_root_public_state_sha256"
    ]:
        raise ValueError("h4 coefficient root state differs from ADR-0345")
    if game.structural_digest != parsed["expected_game_structural_sha256"]:
        raise ValueError("h4 coefficient structural game differs from ADR-0345")
    if game.provenance_digest != parsed["expected_h4_game_provenance_sha256"]:
        raise ValueError("h4 coefficient private-range provenance differs")
    if parent.record["semantics"]["public_schema_sha256"] != parsed[
        "expected_public_schema_sha256"
    ]:
        raise ValueError("h4 coefficient parent public schema differs")

    acting_player = int(parsed["acting_player"])
    source = _source_policy(game)
    endpoints = _endpoint_policies(game, source)
    coverage_response = _coverage_response(game)
    responder_sets = collect_information_sets(game, 1)
    coverage_policy = _policy_with_response(
        source,
        responder_sets,
        coverage_response,
    )
    responder_br_value, responder_br = best_response(game, source, 1)
    responder_br_policy = _policy_with_response(
        source,
        responder_sets,
        responder_br,
    )
    acting_sets = collect_information_sets(game, acting_player)
    acting_br_value, acting_br = best_response(game, source, acting_player)
    acting_br_policy = _policy_with_response(source, acting_sets, acting_br)
    exact_acting_br_value = exact_expected_utilities(
        game,
        acting_br_policy,
    )[acting_player]
    float_acting_br_direct = expected_utilities(game, acting_br_policy)[acting_player]

    axis = _sequence_axis(game, acting_player)
    exact_axis = exact_sequence_axis(game, acting_player)
    if set(axis.variables) != set(exact_axis.variables):
        raise ValueError("h4 subject and exact sequence axes differ")

    contexts = {
        "profile": source,
        "coverage_response": coverage_policy,
        "responder_best_response": responder_br_policy,
    }
    endpoint_evidence: dict[str, list[dict[str, Any]]] = {}
    context_cache: dict[
        tuple[str, str],
        tuple[
            tuple[float, ...],
            tuple[Fraction, ...],
            tuple[float, ...],
            Mapping[tuple[str, Action], Fraction],
        ],
    ] = {}
    maximum_realization_error = 0.0
    maximum_float_exact_utility_error = 0.0
    exact_zero_sum = True
    for context_label, fixed_policy in contexts.items():
        records = []
        for endpoint_label, endpoint in endpoints:
            combined = _replace_acting_policy(fixed_policy, endpoint, acting_sets)
            float_utilities = expected_utilities(game, combined)
            exact_utilities = exact_expected_utilities(game, combined)
            realization = axis.realization_from_policy(combined)
            exact_realization = exact_axis.realization(combined)
            realization_error = max(
                (
                    abs(value - float(exact_realization[token]))
                    for token, value in zip(
                        axis.variables,
                        realization,
                        strict=True,
                    )
                ),
                default=0.0,
            )
            utility_error = max(
                (
                    abs(value - float(exact))
                    for value, exact in zip(
                        float_utilities,
                        exact_utilities,
                        strict=True,
                    )
                ),
                default=0.0,
            )
            maximum_realization_error = max(
                maximum_realization_error,
                realization_error,
            )
            maximum_float_exact_utility_error = max(
                maximum_float_exact_utility_error,
                utility_error,
            )
            exact_zero_sum &= sum(exact_utilities, Fraction(0)) == 0
            context_cache[(context_label, endpoint_label)] = (
                float_utilities,
                exact_utilities,
                realization,
                exact_realization,
            )
            records.append(
                {
                    "endpoint": endpoint_label,
                    "policy_sha256": _policy_sha256(combined),
                    "realization_error": realization_error,
                    "float_exact_utility_error": utility_error,
                    "float_utilities_hex": [value.hex() for value in float_utilities],
                    "exact_utilities": [
                        _fraction_record(value) for value in exact_utilities
                    ],
                }
            )
        endpoint_evidence[context_label] = records

    extracted: dict[str, tuple[AffinePayoff, ExactAffinePayoff]] = {}
    row_records = []
    subject_seconds = 0.0
    exact_seconds = 0.0
    row_specs = (
        ("profile_player0", "profile", 0),
        ("profile_player1", "profile", 1),
        ("coverage_response_player1", "coverage_response", 1),
        ("best_response_player1", "responder_best_response", 1),
    )
    maximum_coefficient_error = 0.0
    maximum_affine_value_error = 0.0
    exact_affine_identity_mismatches = 0
    for label, context_label, payoff_player in row_specs:
        subject, exact, subject_time, exact_time = _extract_pair(
            game,
            contexts[context_label],
            acting_player=acting_player,
            payoff_player=payoff_player,
        )
        subject_seconds += subject_time
        exact_seconds += exact_time
        extracted[label] = subject, exact
        record = _compare_rows(label, subject, exact, axis.variables)
        maximum_coefficient_error = max(
            maximum_coefficient_error,
            record["maximum_coefficient_error"],
        )
        endpoint_rows = []
        for endpoint_label, _ in endpoints:
            float_utilities, exact_utilities, realization, exact_realization = (
                context_cache[(context_label, endpoint_label)]
            )
            subject_value = subject.value(realization)
            exact_value = exact.value(exact_realization)
            float_error = abs(subject_value - float_utilities[payoff_player])
            maximum_affine_value_error = max(
                maximum_affine_value_error,
                float_error,
            )
            exact_match = exact_value == exact_utilities[payoff_player]
            exact_affine_identity_mismatches += int(not exact_match)
            endpoint_rows.append(
                {
                    "endpoint": endpoint_label,
                    "subject_value_hex": subject_value.hex(),
                    "direct_value_hex": float_utilities[payoff_player].hex(),
                    "absolute_error": float_error,
                    "exact_identity": exact_match,
                }
            )
        record["endpoint_values"] = endpoint_rows
        row_records.append(record)

    profile0_subject, profile0_exact = extracted["profile_player0"]
    profile1_subject, profile1_exact = extracted["profile_player1"]
    response_subject, response_exact = extracted["best_response_player1"]
    own_gain_subject = _constant_minus_subject(acting_br_value, profile0_subject)
    own_gain_exact = _constant_minus_exact(exact_acting_br_value, profile0_exact)
    opponent_gain_subject = _subtract_subject(response_subject, profile1_subject)
    opponent_gain_exact = response_exact.subtract(profile1_exact)
    gain_specs = (
        ("acting_gain", own_gain_subject, own_gain_exact),
        ("responder_gain", opponent_gain_subject, opponent_gain_exact),
    )
    gain_records = []
    maximum_gain_value_error = 0.0
    exact_gain_identity_mismatches = 0
    for label, subject, exact in gain_specs:
        record = _compare_rows(label, subject, exact, axis.variables)
        maximum_coefficient_error = max(
            maximum_coefficient_error,
            record["maximum_coefficient_error"],
        )
        values = []
        for endpoint_label, _ in endpoints:
            profile_float, profile_exact, realization, exact_realization = (
                context_cache[("profile", endpoint_label)]
            )
            if label == "acting_gain":
                direct_float = acting_br_value - profile_float[0]
                direct_exact = exact_acting_br_value - profile_exact[0]
            else:
                response_float, response_exact_values, _, _ = context_cache[
                    ("responder_best_response", endpoint_label)
                ]
                direct_float = response_float[1] - profile_float[1]
                direct_exact = response_exact_values[1] - profile_exact[1]
            subject_value = subject.value(realization)
            exact_value = exact.value(exact_realization)
            error = abs(subject_value - direct_float)
            maximum_gain_value_error = max(maximum_gain_value_error, error)
            exact_match = exact_value == direct_exact
            exact_gain_identity_mismatches += int(not exact_match)
            values.append(
                {
                    "endpoint": endpoint_label,
                    "subject_value_hex": subject_value.hex(),
                    "direct_value_hex": direct_float.hex(),
                    "absolute_error": error,
                    "exact_identity": exact_match,
                }
            )
        record["endpoint_values"] = values
        gain_records.append(record)

    coverage_exact = extracted["coverage_response_player1"][1]
    coverage_final_histories = sorted(
        {
            "raise-to-2" if "history=p0:raise-to-2/" in key else "raise-to-3"
            for (key, _), value in coverage_exact.coefficients.items()
            if value != 0
            and (
                "history=p0:raise-to-2/p1:raise-to-4" in key
                or "history=p0:raise-to-3/p1:raise-to-4" in key
            )
        }
    )
    topology = path_single_visit_report(game)
    shortcut_rejected = False
    try:
        require_behavioral_affine_shortcut(game)
    except ValueError:
        shortcut_rejected = True

    hand_counts = [
        len({deal.hand(player) for deal, _ in game.deals})
        for player in range(game.num_players)
    ]
    chance_fractions = [Fraction.from_float(probability) for _, probability in game.deals]
    chance_mass_exact = sum(chance_fractions, Fraction(0)) == 1
    chance_probabilities_dyadic = chance_mass_exact and all(
        value.denominator > 0
        and value.denominator & (value.denominator - 1) == 0
        for value in chance_fractions
    )
    root = game.initial_state().apply_action(game.deals[0][0])
    root_raises = [
        action.raise_to
        for action in root.legal_actions()
        if isinstance(action, BettingAction) and action.raise_to is not None
    ]
    final_response_variables = sum(
        len(information_set.actions)
        for information_set in exact_axis.information_sets
        if "p1:raise-to-4" in information_set.key
    )
    response_counts = {
        "raise-to-4": sum(action == raise_to(4) for action in coverage_response.values()),
        "fold": sum(action == FOLD for action in coverage_response.values()),
        "call": sum(action == CALL for action in coverage_response.values()),
    }
    acting_br_identity_error = max(
        abs(acting_br_value - float(exact_acting_br_value)),
        abs(float_acting_br_direct - float(exact_acting_br_value)),
    )
    total_seconds = time.perf_counter() - started
    gates = parsed["gates"]
    checks = {
        "clean_git": (not git["dirty"]) == gates["require_clean_git_state"],
        "parent_pass": bool(parent.record["passed"]) == gates["require_parent_pass"],
        "root_state_identity": public_betting_state_sha256(game.base_state)
        == parsed["expected_root_public_state_sha256"],
        "public_schema_identity": parent.record["semantics"]["public_schema_sha256"]
        == parsed["expected_public_schema_sha256"],
        "structural_game_identity": game.structural_digest
        == parsed["expected_game_structural_sha256"],
        "h4_provenance_identity": game.provenance_digest
        == parsed["expected_h4_game_provenance_sha256"],
        "legal_root_universe": root_raises == [2, 3, 4],
        "h4_hand_counts": hand_counts == gates["expected_hand_counts"],
        "joint_deal_count": len(game.deals) == gates["expected_joint_deals"],
        "terminal_path_count": _tree_terminal_paths(game)
        == gates["expected_terminal_paths"],
        "dyadic_chance_mass": chance_probabilities_dyadic
        == gates["require_dyadic_chance_mass"],
        "source_policy_identity": _policy_sha256(source)
        == parsed["expected_source_policy_sha256"],
        "coverage_response_identity": _response_sha256(coverage_response)
        == parsed["expected_coverage_response_sha256"],
        "source_response_tape_identities": (
            _response_sha256(responder_br)
            == parsed["expected_responder_best_response_sha256"]
            and responder_br_value.hex()
            == parsed["expected_responder_best_response_value_hex"]
            and _response_sha256(acting_br)
            == parsed["expected_acting_best_response_sha256"]
            and acting_br_value.hex()
            == parsed["expected_acting_best_response_value_hex"]
        )
        == gates["require_source_response_tape_identities"],
        "endpoint_policy_identities": tuple(
            _policy_sha256(policy) for _, policy in endpoints
        )
        == parsed["expected_endpoint_policy_sha256s"],
        "endpoint_count": len(endpoints) == gates["expected_endpoint_policies"],
        "acting_information_set_count": len(axis.information_sets)
        == gates["expected_acting_information_sets"],
        "sequence_variable_count": len(axis.variables)
        == gates["expected_sequence_variables"],
        "final_response_variable_count": final_response_variables
        == gates["expected_final_response_variables"],
        "row_counts": len(row_records) == (
            gates["expected_profile_rows"] + gates["expected_fixed_response_rows"]
        )
        and len(gain_records) == gates["expected_gain_rows"],
        "coverage_response_counts": response_counts
        == {
            "raise-to-4": gates["expected_coverage_raise_choices"],
            "fold": gates["expected_coverage_fold_choices"],
            "call": gates["expected_coverage_call_choices"],
        },
        "full_and_short_final_sequence_coverage": coverage_final_histories
        == ["raise-to-2", "raise-to-3"]
        and gates["require_full_and_short_final_sequence_coverage"],
        "repeated_actor_topology": (
            not topology.passed and topology.repeated_player == acting_player
        )
        == gates["require_repeated_actor_topology"],
        "behavioral_shortcut_rejection": shortcut_rejected
        == gates["require_behavioral_shortcut_rejection"],
        "coefficient_identity": maximum_coefficient_error
        <= gates["maximum_coefficient_error"],
        "realization_identity": maximum_realization_error
        <= gates["maximum_realization_error"],
        "affine_value_identity": max(
            maximum_affine_value_error,
            maximum_gain_value_error,
        )
        <= gates["maximum_affine_value_error"],
        "float_exact_utility_identity": maximum_float_exact_utility_error
        <= gates["maximum_float_exact_utility_error"],
        "exact_affine_identities": (
            exact_affine_identity_mismatches == 0
            and exact_gain_identity_mismatches == 0
        )
        == gates["require_exact_affine_identities"],
        "acting_br_identity": acting_br_identity_error
        <= gates["maximum_acting_br_identity_error"],
        "exact_zero_sum": exact_zero_sum == gates["require_exact_zero_sum"],
        "total_time": total_seconds <= gates["maximum_total_seconds"],
    }
    payload = {
        "parent_artifact_sha256": _sha256(_PATHS["expected_parent_artifact_sha256"]),
        "root_public_state_sha256": public_betting_state_sha256(game.base_state),
        "public_schema_sha256": parent.record["semantics"]["public_schema_sha256"],
        "game_structural_sha256": game.structural_digest,
        "game_provenance_sha256": game.provenance_digest,
        "table_seats": list(game.table_seats),
        "root_raise_to_totals": root_raises,
        "fixture": {
            "hand_counts": hand_counts,
            "joint_deals": len(game.deals),
            "terminal_paths": _tree_terminal_paths(game),
            "chance_mass_exact": chance_mass_exact,
            "chance_probabilities_dyadic": chance_probabilities_dyadic,
            "chance_probabilities": [
                _fraction_record(value) for value in chance_fractions
            ],
        },
        "topology": {
            "path_single_visit": topology.passed,
            "repeated_player": topology.repeated_player,
            "witness": [_action_token(action) for action in topology.witness_actions],
            "behavioral_shortcut_rejected": shortcut_rejected,
        },
        "axis": {
            "acting_player": acting_player,
            "information_sets": len(axis.information_sets),
            "sequence_variables": len(axis.variables),
            "final_response_variables": final_response_variables,
        },
        "policies": {
            "source_sha256": _policy_sha256(source),
            "endpoint_sha256s": [
                {"label": label, "sha256": _policy_sha256(policy)}
                for label, policy in endpoints
            ],
            "coverage_response_sha256": _response_sha256(coverage_response),
            "coverage_response_counts": response_counts,
            "responder_best_response_sha256": _response_sha256(responder_br),
            "responder_best_response_value_hex": responder_br_value.hex(),
            "acting_best_response_sha256": _response_sha256(acting_br),
            "acting_best_response_value_hex": acting_br_value.hex(),
            "responder_best_response_calls": 1,
            "acting_best_response_calls": 1,
            "endpoint_responder_selector_calls": 0,
        },
        "endpoint_contexts": endpoint_evidence,
        "payoff_rows": row_records,
        "gain_rows": gain_records,
        "coverage_nonzero_final_histories": coverage_final_histories,
        "maximum_coefficient_error": maximum_coefficient_error,
        "maximum_realization_error": maximum_realization_error,
        "maximum_affine_value_error": maximum_affine_value_error,
        "maximum_gain_value_error": maximum_gain_value_error,
        "maximum_float_exact_utility_error": maximum_float_exact_utility_error,
        "exact_affine_identity_mismatches": exact_affine_identity_mismatches,
        "exact_gain_identity_mismatches": exact_gain_identity_mismatches,
        "acting_br_identity_error": acting_br_identity_error,
        "exact_zero_sum": exact_zero_sum,
        "timing": {
            "float_subject_seconds": subject_seconds,
            "fraction_oracle_seconds": exact_seconds,
            "total_seconds": total_seconds,
        },
        "quality_rows_serialized": 0,
        "strategy_labels_generated": 0,
        "endpoint_responder_selector_calls": 0,
    }
    checks["finite"] = _finite_tree(payload) == gates["require_finite"]
    gate_result = finalize_gates(checks)
    return {
        **payload,
        **gate_result,
        "decision": (
            "authorize_legal_responder_raise_h4_row_growth_preregistration"
            if gate_result["passed"]
            else "reject_legal_responder_raise_h4_coefficient_path"
        ),
        "total_seconds": total_seconds,
    }


def run_legal_responder_raise_h4_coefficient_differential(
    config_path: Path = _CONFIG,
    output_path: Path = _OUTPUT,
) -> dict[str, Any]:
    """Execute the sole frozen ADR-0346 invocation and retain its terminal."""

    if os.path.lexists(output_path):
        raise FileExistsError(f"h4 coefficient result path already exists: {output_path}")
    started = time.perf_counter()
    stage = "config"
    git: Mapping[str, Any] | None = None
    try:
        parsed = _parse_config(json.loads(config_path.read_text(encoding="utf-8")))
        stage = "git"
        git = _strict_git_metadata()
        stage = "differential"
        payload = _execute_differential(parsed, git=git)
        result = {
            "schema_version": 1,
            "status": "legal_responder_raise_h4_coefficient_differential_executed",
            "environment": _environment(git),
            "config_sha256": _sha256(config_path),
            "implementation_sha256": _sha256(_IMPLEMENTATION),
            "exact_oracle_sha256": _sha256(_PATHS["expected_exact_oracle_sha256"]),
            "methodology": {
                "betting_authority": "NoLimitBettingState",
                "subject": "float64_direct_sequence_form_open_axis_traversal",
                "teacher": "independent_fraction_terminal_enumerator",
                "response_tapes": "source_fixed_no_endpoint_selector_recomputation",
                "quality_rows": 0,
                "strategy_labels": 0,
            },
            **payload,
            "strategy_quality_claim": None,
            "limitations": [
                "This is one h4 private-axis coefficient identity on the ADR-0345 tree.",
                "Response tapes are fixed; selector stability is not measured.",
                "Direct traversal cost is not response-row capacity or action latency.",
                "No policy is optimized and no production action or quality label is emitted.",
            ],
        }
    except Exception as error:
        result = {
            "schema_version": 1,
            "status": "legal_responder_raise_h4_coefficient_differential_failed",
            "environment": _environment(git),
            "config_sha256": (
                _sha256(config_path) if config_path.is_file() else None
            ),
            "implementation_sha256": _sha256(_IMPLEMENTATION),
            "passed": False,
            "decision": "reject_legal_responder_raise_h4_coefficient_path",
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
    result = run_legal_responder_raise_h4_coefficient_differential(
        args.config,
        args.output,
    )
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
