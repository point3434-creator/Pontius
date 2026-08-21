"""Exact source-relative response certificates for localized policy deltas."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Literal, Mapping

from .delta_certificate_contract import (
    AtomicPolicyDelta,
    DeltaCertificateScope,
    EnvelopeProbeClassification,
    atomic_policy_manifest,
    certificate_scope_digest,
    classify_envelope_probe,
    deadline_fallback_required,
    validate_certificate_scope,
)
from .dependency_tape import (
    CompiledPolicyDeltaTape,
    DependencyTapeDiagnostics,
)
from .evaluation import EvaluationResult
from .fixed_envelope_verifier import _stop_reason
from .game import Action
from .real_policy import policy_digest


ExecutionMode = Literal["auto", "sparse", "dense"]


@dataclass(frozen=True, slots=True)
class EnvelopePrefixStop:
    """The exact fixed-order prefix that a fail-fast verifier would consume."""

    evaluated_seats: tuple[int, ...]
    partial_nash_conv: float
    stop_reason: str
    stop_seat: int | None
    complete: bool


@dataclass(frozen=True, slots=True)
class LocalizedResponseCertificate:
    """A complete exact vector plus its fail-fast envelope interpretation."""

    candidate_id: str
    candidate_policy_sha256: str
    scope_sha256: str
    atoms: tuple[AtomicPolicyDelta, ...]
    evaluation: EvaluationResult
    best_response_actions: tuple[dict[str, Action], ...]
    response_action_flips_by_seat: tuple[int, ...]
    diagnostics: DependencyTapeDiagnostics
    envelope: EnvelopeProbeClassification
    prefix: EnvelopePrefixStop


@dataclass(frozen=True, slots=True)
class LocalizedResponseDecision:
    """Fail-closed selection after applying the external wall-clock ledger."""

    selected_candidate_id: str
    blueprint_fallback: bool
    fallback_reason: str | None
    deadline_fallback: bool
    elapsed_ms: float
    emission_reserve_ms: float
    decision_budget_ms: float


def simulate_exact_envelope_prefix(
    blueprint_deviation_gains: tuple[float, ...],
    candidate_deviation_gains: tuple[float, ...],
    *,
    best_complete_nash_conv: float,
    raw_guard: float,
    seat_order: tuple[int, ...],
) -> EnvelopePrefixStop:
    """Apply the accepted cap-before-objective stopping rule to an exact vector."""

    players = len(blueprint_deviation_gains)
    if (
        players == 0
        or len(candidate_deviation_gains) != players
        or len(seat_order) != players
        or tuple(sorted(seat_order)) != tuple(range(players))
    ):
        raise ValueError("envelope prefix requires equal vectors and every seat once")
    values = (
        *blueprint_deviation_gains,
        *candidate_deviation_gains,
        best_complete_nash_conv,
        raw_guard,
    )
    if any(not math.isfinite(value) or value < 0.0 for value in values):
        raise ValueError("envelope prefix values must be finite and nonnegative")
    partial = 0.0
    evaluated = []
    for seat in seat_order:
        gain = float(candidate_deviation_gains[seat])
        partial += gain
        evaluated.append(seat)
        reason = _stop_reason(
            seat=seat,
            gain=gain,
            partial_nash_conv=partial,
            blueprint_gain=float(blueprint_deviation_gains[seat]),
            best_complete_nash_conv=best_complete_nash_conv,
            raw_guard=raw_guard,
        )
        if reason is not None:
            return EnvelopePrefixStop(
                evaluated_seats=tuple(evaluated),
                partial_nash_conv=partial,
                stop_reason=reason,
                stop_seat=seat,
                complete=False,
            )
    return EnvelopePrefixStop(
        evaluated_seats=tuple(evaluated),
        partial_nash_conv=partial,
        stop_reason="complete",
        stop_seat=None,
        complete=True,
    )


def certify_localized_policy_delta(
    tape: CompiledPolicyDeltaTape,
    candidate_policy: Mapping[str, Mapping[Action, float]],
    *,
    candidate_id: str,
    scope: DeltaCertificateScope,
    expected_scope: DeltaCertificateScope,
    seat_order: tuple[int, ...],
    maximum_changed_information_sets: int,
    mode: ExecutionMode = "sparse",
) -> LocalizedResponseCertificate:
    """Recertify one bounded policy delta from the immutable tape source."""

    validate_certificate_scope(scope, expected_scope)
    if not candidate_id:
        raise ValueError("localized response candidate id must be nonempty")
    if (
        isinstance(maximum_changed_information_sets, bool)
        or maximum_changed_information_sets <= 0
    ):
        raise ValueError("localized response atom limit must be positive")
    source_policy = tape.source_policy
    candidate_sha256 = policy_digest(candidate_policy)
    if policy_digest(source_policy) != scope.episode_blueprint_policy_sha256:
        raise ValueError("localized response source policy differs from certificate scope")
    if candidate_sha256 != scope.candidate_policy_sha256:
        raise ValueError("localized response candidate differs from certificate scope")
    source = tape.source_result.evaluation
    if tuple(source.deviation_gains) != tuple(scope.blueprint_deviation_gains):
        raise ValueError("localized response source gains differ from certificate anchor")
    if not math.isclose(
        source.nash_conv,
        math.fsum(scope.blueprint_deviation_gains),
        rel_tol=0.0,
        abs_tol=0.0,
    ):
        raise ValueError("localized response source NashConv differs from certificate anchor")

    atoms = atomic_policy_manifest(source_policy, candidate_policy)
    if not atoms:
        raise ValueError("localized response certificate requires a nonempty policy delta")
    if len(atoms) > maximum_changed_information_sets:
        raise ValueError("localized response policy delta exceeds the frozen atom limit")

    result = tape.recertify_policy(candidate_policy, mode=mode)
    evaluation = result.evaluation
    envelope = classify_envelope_probe(
        scope.blueprint_deviation_gains,
        evaluation.deviation_gains,
        blueprint_nash_conv=source.nash_conv,
        candidate_nash_conv=evaluation.nash_conv,
        raw_guard=scope.raw_guard,
        payoff_span=scope.payoff_span,
    )
    prefix = simulate_exact_envelope_prefix(
        tuple(scope.blueprint_deviation_gains),
        tuple(evaluation.deviation_gains),
        best_complete_nash_conv=source.nash_conv,
        raw_guard=scope.raw_guard,
        seat_order=seat_order,
    )
    source_actions = tape.source_result.best_response_actions
    flips = tuple(
        sum(
            source_actions[seat].get(key) != result.best_response_actions[seat].get(key)
            for key in set(source_actions[seat]) | set(result.best_response_actions[seat])
        )
        for seat in range(len(source.deviation_gains))
    )
    if sum(flips) != result.diagnostics.best_response_action_flips:
        raise AssertionError("localized response switch telemetry is inconsistent")
    return LocalizedResponseCertificate(
        candidate_id=candidate_id,
        candidate_policy_sha256=candidate_sha256,
        scope_sha256=certificate_scope_digest(scope),
        atoms=atoms,
        evaluation=evaluation,
        best_response_actions=result.best_response_actions,
        response_action_flips_by_seat=flips,
        diagnostics=result.diagnostics,
        envelope=envelope,
        prefix=prefix,
    )


def decide_localized_response_certificate(
    certificate: LocalizedResponseCertificate,
    *,
    blueprint_candidate_id: str,
    elapsed_ms: float,
    emission_reserve_ms: float,
    decision_budget_ms: float = 15000.0,
) -> LocalizedResponseDecision:
    """Select only a certified improvement that can still be emitted on time."""

    if not blueprint_candidate_id or blueprint_candidate_id == certificate.candidate_id:
        raise ValueError("localized response blueprint id must be distinct and nonempty")
    deadline = deadline_fallback_required(
        elapsed_ms=elapsed_ms,
        emission_reserve_ms=emission_reserve_ms,
        decision_budget_ms=decision_budget_ms,
    )
    if deadline:
        selected = blueprint_candidate_id
        reason = "deadline"
    elif certificate.envelope.classification != "admissible_improvement":
        selected = blueprint_candidate_id
        reason = certificate.envelope.classification
    else:
        selected = certificate.candidate_id
        reason = None
    return LocalizedResponseDecision(
        selected_candidate_id=selected,
        blueprint_fallback=selected == blueprint_candidate_id,
        fallback_reason=reason,
        deadline_fallback=deadline,
        elapsed_ms=float(elapsed_ms),
        emission_reserve_ms=float(emission_reserve_ms),
        decision_budget_ms=float(decision_budget_ms),
    )
