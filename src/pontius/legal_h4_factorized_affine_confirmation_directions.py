"""Frozen downstream direction compiler for legal-h4 confirmation.

This module contains value-opening machinery but performs no work at import.
The exclusive ADR-0361 owner is its only fresh-population caller.  Three DCFR
history vertices are followed by one audited row-growth proposal whose rows,
evaluations, feasibility and convergence classifications are independently
rebound with exact Fraction arithmetic before the endpoint becomes eligible.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from fractions import Fraction
from hashlib import sha256
import json
from math import isfinite
from types import MappingProxyType
from typing import Any, Mapping

from .cfr import TabularCFR
from .evaluation import Policy, collect_information_sets
from .exact_sequence_form_coefficient_oracle import (
    ExactAffinePayoff,
    exact_expected_utilities,
    exact_open_axis_payoff_coefficients,
    exact_sequence_axis,
)
from .game import Action, ExtensiveFormGame
from .legal_h4_factorized_affine_confirmation_population import policy_sha256
from .one_seat_convex_generation import ResponseSignature
from .one_seat_row_growth_audit import (
    AuditedEvaluation,
    AuditedResponseRow,
    audit_one_seat_row_growth,
)


REGRET_PUBLIC_HISTORIES = (
    "p0:raise-to-2/p1:raise-to-4",
    "p0:raise-to-3/p1:raise-to-4",
    "root",
)


def _canonical_sha256(value: object) -> str:
    return sha256(
        json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()


def _fraction_record(value: Fraction) -> dict[str, int]:
    return {"denominator": value.denominator, "numerator": value.numerator}


def _action_token(action: object) -> str:
    return str(action)


def _response_record(signature: ResponseSignature) -> list[dict[str, str]]:
    return [
        {"action": _action_token(action), "information_key": key}
        for key, action in signature
    ]


def _response_sha256(signature: ResponseSignature) -> str:
    return _canonical_sha256(_response_record(signature))


def _exact_affine_record(
    row: ExactAffinePayoff,
    variables: tuple[tuple[str, Action], ...],
) -> dict[str, object]:
    return {
        "coefficients": [
            {
                "action": _action_token(action),
                "information_key": key,
                "value": _fraction_record(row.coefficients[(key, action)]),
            }
            for key, action in variables
        ],
        "constant": _fraction_record(row.constant),
    }


def _clone(policy: Mapping[str, Mapping[Action, float]]) -> Policy:
    return {key: dict(row) for key, row in policy.items()}


def _history(key: str) -> str:
    try:
        return key.rsplit("|history=", 1)[1]
    except IndexError as exc:
        raise ValueError("confirmation information key has no public history") from exc


@dataclass(frozen=True, slots=True)
class LegalH4ConfirmationDirection:
    context_id: str
    label: str
    direction_class: str
    changed_public_histories: tuple[str, ...]
    endpoint_policy_sha256: str
    endpoint_policy: Policy


@dataclass(frozen=True, slots=True)
class LegalH4ConfirmationDirectionCompilation:
    context_id: str
    directions: tuple[LegalH4ConfirmationDirection, ...]
    row_growth: Mapping[str, object]


class RowGrowthDirectionRejected(RuntimeError):
    """Typed scientific rejection carrying the complete non-policy audit."""

    def __init__(self, record: Mapping[str, object]) -> None:
        super().__init__("fresh legal h4 row-growth direction failed its exact gates")
        self.record = dict(record)


def _regret_vertex_directions(
    game: ExtensiveFormGame,
    source: Policy,
    *,
    context_id: str,
    acting_player: int,
) -> tuple[LegalH4ConfirmationDirection, ...]:
    solver = TabularCFR(game, variant="dcfr")
    warm_mass = 1.0
    solver.warm_start(source, warm_mass)
    solver.step()
    postdiscount = {
        key: dict(data.regrets) for key, data in solver.information_sets.items()
    }
    acting_sets = collect_information_sets(game, acting_player)
    histories = tuple(sorted({_history(key) for key in acting_sets}))
    if histories != REGRET_PUBLIC_HISTORIES:
        raise ValueError("confirmation regret-history inventory drifted")
    result = []
    for history in histories:
        endpoint = _clone(source)
        keys = tuple(key for key in acting_sets if _history(key) == history)
        if not keys:
            raise AssertionError("confirmation regret block is empty")
        for key in keys:
            actions = acting_sets[key]
            regrets = {
                action: 2.0 * float(postdiscount[key][action])
                - warm_mass * float(source[key][action])
                for action in actions
            }
            # max() preserves the exact legal action order on a numerical tie.
            selected = max(actions, key=regrets.__getitem__)
            endpoint[key] = {
                action: float(action == selected) for action in actions
            }
        result.append(
            LegalH4ConfirmationDirection(
                context_id=context_id,
                label=f"regret_vertex::{history}",
                direction_class="one_step_dcfr_regret_vertex_per_public_history",
                changed_public_histories=(history,),
                endpoint_policy_sha256=policy_sha256(endpoint),
                endpoint_policy=endpoint,
            )
        )
    return tuple(result)


def _deterministic_response_policy(
    game: ExtensiveFormGame,
    policy: Policy,
    player: int,
    signature: ResponseSignature,
) -> Policy:
    information_sets = collect_information_sets(game, player)
    selected = dict(signature)
    if len(selected) != len(signature) or set(selected) != set(information_sets):
        raise ValueError("confirmation response signature does not cover its infosets")
    result = _clone(policy)
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
    game: ExtensiveFormGame,
    source: Policy,
    acting_player: int,
    exact_profile: tuple[ExactAffinePayoff, ...],
    row: AuditedResponseRow,
) -> ExactAffinePayoff:
    fixed = _deterministic_response_policy(
        game,
        source,
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
) -> tuple[dict[str, object], float, bool]:
    if set(exact.coefficients) != set(variables):
        raise ValueError("confirmation exact response row axis drifted")
    errors = [abs(row.gain.constant - float(exact.constant))]
    exact_float_identity = Fraction.from_float(row.gain.constant) == exact.constant
    coefficients = []
    for token, subject in zip(variables, row.gain.coefficients, strict=True):
        exact_value = exact.coefficients[token]
        error = abs(subject - float(exact_value))
        errors.append(error)
        exact_float_identity &= Fraction.from_float(subject) == exact_value
        coefficients.append(
            {
                "action": _action_token(token[1]),
                "absolute_error": error,
                "exact": _fraction_record(exact_value),
                "information_key": token[0],
                "subject_hex": subject.hex(),
            }
        )
    exact_record = _exact_affine_record(exact, variables)
    record: dict[str, object] = {
        "after_iteration": row.after_iteration,
        "coefficients": coefficients,
        "constant_exact": _fraction_record(exact.constant),
        "constant_subject_hex": row.gain.constant.hex(),
        "exact_float_identity": exact_float_identity,
        "exact_row_sha256": _canonical_sha256(exact_record),
        "maximum_absolute_error": max(errors, default=0.0),
        "ordinal": row.ordinal,
        "phase": row.phase,
        "signature": _response_record(row.signature),
        "signature_sha256": _response_sha256(row.signature),
        "target_player": row.target_player,
    }
    return record, max(errors, default=0.0), exact_float_identity


def _exact_evaluation(
    game: ExtensiveFormGame,
    audited: AuditedEvaluation,
) -> tuple[dict[str, object], tuple[Fraction, ...], float, bool]:
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
    exact_nash_conv = sum(gains, Fraction(0))
    subject = audited.evaluation
    errors = [
        *(
            abs(value - float(exact))
            for value, exact in zip(subject.utilities, utilities, strict=True)
        ),
        *(
            abs(value - float(exact))
            for value, exact in zip(
                subject.best_response_values, response_values, strict=True
            )
        ),
        *(
            abs(value - float(exact))
            for value, exact in zip(subject.deviation_gains, gains, strict=True)
        ),
        abs(subject.nash_conv - float(exact_nash_conv)),
    ]
    record: dict[str, object] = {
        "best_response_values_exact": [
            _fraction_record(value) for value in response_values
        ],
        "deviation_gains_exact": [_fraction_record(value) for value in gains],
        "exact_gains_nonnegative": all(value >= 0 for value in gains),
        "maximum_float_exact_error": max(errors, default=0.0),
        "nash_conv_exact": _fraction_record(exact_nash_conv),
        "ordinal": audited.ordinal,
        "policy_sha256": policy_sha256(audited.policy),
        "response_signature_sha256s": [
            _response_sha256(signature)
            for signature in audited.response_signatures
        ],
        "response_signatures": [
            _response_record(signature) for signature in audited.response_signatures
        ],
        "utilities_exact": [_fraction_record(value) for value in utilities],
    }
    return (
        record,
        gains,
        max(errors, default=0.0),
        all(value >= 0 for value in gains),
    )


def _row_growth_direction(
    game: ExtensiveFormGame,
    source: Policy,
    *,
    context_id: str,
    acting_player: int,
    guard: float,
    max_iterations: int,
    tolerance: float,
) -> tuple[LegalH4ConfirmationDirection, dict[str, object]]:
    audit = audit_one_seat_row_growth(
        game,
        source,
        acting_player=acting_player,
        guard=guard,
        max_iterations=max_iterations,
        tolerance=tolerance,
    )
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
    maximum_row_error = 0.0
    all_rows_exact = True
    for row in audit.response_rows:
        exact = _exact_response_row(
            game,
            source,
            acting_player,
            exact_profile,
            row,
        )
        record, error, exact_identity = _row_record(
            row,
            exact,
            exact_axis.variables,
        )
        row_records.append(record)
        maximum_row_error = max(maximum_row_error, error)
        all_rows_exact &= exact_identity

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

    exact_threshold = Fraction.from_float(100.0 * tolerance)
    exact_guard = Fraction.from_float(guard)
    exact_caps = tuple(value + exact_guard for value in exact_gains[0])
    cap_identity_error = max(
        (
            abs(value - float(exact))
            for value, exact in zip(audit.result.caps, exact_caps, strict=True)
        ),
        default=0.0,
    )
    iteration_records = []
    exact_feasibility_classification = True
    exact_convergence_classification = True
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
        exact_feasibility_classification &= (
            exact_feasible == update.candidate_feasible
        )
        exact_convergence_classification &= exact_converged == update.converged
        iteration_records.append(
            {
                **asdict(update),
                "epigraph_hex": [value.hex() for value in master.epigraph],
                "exact_candidate_feasible": exact_feasible,
                "exact_converged": exact_converged,
                "master": {
                    "dual_objective_hex": master.solution.dual_objective.hex(),
                    "duality_gap": master.solution.duality_gap,
                    "maximum_constraint_violation": (
                        master.solution.max_constraint_violation
                    ),
                    "objective_hex": master.solution.objective.hex(),
                    "pivots": master.solution.pivots,
                },
                "maximum_exact_cap_violation": _fraction_record(
                    max(cap_violations, default=Fraction(0))
                ),
                "maximum_exact_epigraph_violation": _fraction_record(
                    max(epigraph_violations, default=Fraction(0))
                ),
            }
        )

    candidate_by_digest = {
        str(record["policy_sha256"]): (record, gains)
        for record, gains in zip(evaluation_records, exact_gains, strict=True)
    }
    endpoint_digest = policy_sha256(audit.result.policy)
    if endpoint_digest not in candidate_by_digest:
        raise AssertionError("confirmation row-growth endpoint was not evaluated")
    final_record, final_gains = candidate_by_digest[endpoint_digest]
    final_exact_nash_conv = sum(final_gains, Fraction(0))
    final_exact_feasible = (
        max(
            (
                gain - cap
                for gain, cap in zip(final_gains, exact_caps, strict=True)
            ),
            default=Fraction(0),
        )
        <= exact_threshold
    )
    maximum_duality_gap = max(
        (master.solution.duality_gap for master in audit.masters),
        default=float("inf"),
    )
    maximum_constraint_violation = max(
        (master.solution.max_constraint_violation for master in audit.masters),
        default=float("inf"),
    )
    final_iteration = iteration_records[-1] if iteration_records else None
    exact_signature_dedup = len(
        {(row.target_player, row.signature) for row in audit.response_rows}
    ) == len(audit.response_rows)
    gates = {
        "all_response_rows_exactly_rebound": all_rows_exact,
        "candidate_feasible": bool(
            final_iteration is not None
            and final_iteration["candidate_feasible"] is True
        ),
        "converged": audit.result.converged is True,
        "exact_candidate_feasible": bool(
            final_iteration is not None
            and final_iteration["exact_candidate_feasible"] is True
            and final_exact_feasible
        ),
        "exact_converged": bool(
            final_iteration is not None
            and final_iteration["exact_converged"] is True
        ),
        "exact_cap_identity": cap_identity_error == 0.0,
        "exact_duplicate_response_free": (
            exact_signature_dedup
            and audit.result.exact_duplicate_response_hits == 0
        ),
        "exact_float_classifications": (
            exact_feasibility_classification
            and exact_convergence_classification
            and exact_gains_nonnegative
        ),
        "maximum_master_constraint_violation_at_most_1e-8": (
            isfinite(maximum_constraint_violation)
            and maximum_constraint_violation <= 1e-8
        ),
        "maximum_master_duality_gap_at_most_1e-8": (
            isfinite(maximum_duality_gap) and maximum_duality_gap <= 1e-8
        ),
        "nontrivial_endpoint": endpoint_digest != policy_sha256(source),
    }
    record: dict[str, object] = {
        "acting_player": audit.result.acting_player,
        "baseline_nash_conv": audit.result.baseline_nash_conv,
        "cap_identity_error": cap_identity_error,
        "caps_exact": [_fraction_record(value) for value in exact_caps],
        "context_id": context_id,
        "endpoint_evaluation_ordinal": final_record["ordinal"],
        "endpoint_policy_sha256": endpoint_digest,
        "evaluations": evaluation_records,
        "exact_duplicate_response_hits": audit.result.exact_duplicate_response_hits,
        "final_exact_nash_conv": _fraction_record(final_exact_nash_conv),
        "gates": gates,
        "guard": guard,
        "iterations": iteration_records,
        "maximum_float_exact_evaluation_error": maximum_evaluation_error,
        "maximum_float_exact_row_error": maximum_row_error,
        "maximum_master_constraint_violation": maximum_constraint_violation,
        "maximum_master_duality_gap": maximum_duality_gap,
        "max_iterations": max_iterations,
        "oracle_accounting": {
            "best_response_calls": audit.best_response_calls,
            "evaluation_calls": len(audit.evaluations),
            "expected_utilities_calls": audit.expected_utilities_calls,
            "master_calls": len(audit.masters),
            "open_axis_coefficient_calls": audit.open_axis_coefficient_calls,
            "response_row_calls": len(audit.response_rows),
        },
        "passed": all(gates.values()),
        "response_rows": row_records,
        "response_rows_by_player": list(audit.result.response_rows_by_player),
        "source_policy_sha256": policy_sha256(source),
        "tolerance": tolerance,
    }
    semantic_iterations = [
        {
            key: value
            for key, value in iteration.items()
            if key
            not in {
                "cut_extraction_seconds",
                "exact_oracle_seconds",
                "master_solve_seconds",
            }
        }
        for iteration in iteration_records
    ]
    record["row_growth_semantic_sha256"] = _canonical_sha256(
        {**record, "iterations": semantic_iterations}
    )
    if record["passed"] is not True:
        raise RowGrowthDirectionRejected(record)

    acting_sets = collect_information_sets(game, acting_player)
    changed_histories = tuple(
        sorted(
            {
                _history(key)
                for key in acting_sets
                if audit.result.policy[key] != source[key]
            }
        )
    )
    if not changed_histories:
        raise RowGrowthDirectionRejected(
            {
                **record,
                "passed": False,
                "post_gate_failure": "row_growth_endpoint_is_a_no_op",
            }
        )
    direction = LegalH4ConfirmationDirection(
        context_id=context_id,
        label=f"row_growth_proposal::{context_id}",
        direction_class="converged_one_seat_row_growth_proposal",
        changed_public_histories=changed_histories,
        endpoint_policy_sha256=endpoint_digest,
        endpoint_policy=_clone(audit.result.policy),
    )
    return direction, record


def compile_legal_h4_confirmation_directions(
    game: ExtensiveFormGame,
    source: Policy,
    *,
    context_id: str,
    acting_player: int = 0,
    guard: float = 0.25,
    max_iterations: int = 128,
    tolerance: float = 1e-10,
) -> LegalH4ConfirmationDirectionCompilation:
    """Open exactly the frozen four-direction family for one context."""

    if not isinstance(context_id, str) or not context_id:
        raise TypeError("confirmation direction context identity must be nonempty")
    if acting_player != 0:
        raise ValueError("confirmation acting player must remain zero")
    if guard != 0.25 or max_iterations != 128 or tolerance != 1e-10:
        raise ValueError("confirmation direction parameters differ from ADR-0360")
    regret = _regret_vertex_directions(
        game,
        source,
        context_id=context_id,
        acting_player=acting_player,
    )
    proposal, row_growth = _row_growth_direction(
        game,
        source,
        context_id=context_id,
        acting_player=acting_player,
        guard=guard,
        max_iterations=max_iterations,
        tolerance=tolerance,
    )
    directions = (*regret, proposal)
    if (
        len(directions) != 4
        or tuple(direction.direction_class for direction in directions)
        != (
            "one_step_dcfr_regret_vertex_per_public_history",
            "one_step_dcfr_regret_vertex_per_public_history",
            "one_step_dcfr_regret_vertex_per_public_history",
            "converged_one_seat_row_growth_proposal",
        )
        or len({direction.label for direction in directions}) != 4
        or len({direction.endpoint_policy_sha256 for direction in directions}) != 4
    ):
        raise ValueError("confirmation direction inventory drifted")
    return LegalH4ConfirmationDirectionCompilation(
        context_id=context_id,
        directions=directions,
        row_growth=MappingProxyType(dict(row_growth)),
    )


def direction_descriptor(
    direction: LegalH4ConfirmationDirection,
) -> dict[str, object]:
    return {
        "changed_public_histories": list(direction.changed_public_histories),
        "context_id": direction.context_id,
        "direction_class": direction.direction_class,
        "endpoint_policy_sha256": direction.endpoint_policy_sha256,
        "label": direction.label,
    }


__all__ = [
    "LegalH4ConfirmationDirection",
    "LegalH4ConfirmationDirectionCompilation",
    "REGRET_PUBLIC_HISTORIES",
    "RowGrowthDirectionRejected",
    "compile_legal_h4_confirmation_directions",
    "direction_descriptor",
]
