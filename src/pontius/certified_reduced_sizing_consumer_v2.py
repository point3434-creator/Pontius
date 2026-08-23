"""Fail-closed research consumer for certified reduced river sizing.

The consumer binds one exact two-live-seat river opening to an explicit subset
of kernel-legal raise-to totals.  It converts those street totals into distinct
incremental wagers before invoking ADR-0318 exactly once.  The reduced model
permits only fold/call responses, so this module returns evidence and never a
``BettingAction``.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from fractions import Fraction
from hashlib import sha256
from importlib import import_module
from itertools import pairwise
from pathlib import Path
from typing import Any

from .certified_reduced_sizing_highs import (
    CertifiedReducedSizingSolution,
    canonical_lf_source_sha256,
    solve_certified_reduced_sizing_highs,
    verify_adr0318_runtime_identity,
    verify_adr0318_source_and_dependencies,
)
from .legal_decision_spine_v2 import public_betting_state_sha256
from .no_limit_betting import BettingActionKind, BettingStreet, NoLimitBettingState
from .reduced_river_sizing_lp import compile_reduced_river_sizing_lp


_PROTOCOL = {
    "action_output": "none-research-evidence-only",
    "backend_calls": "exactly-one-public-highs-ds-after-all-preflight",
    "bet_conversion": "raise-to-minus-street-contribution-minus-call-amount",
    "fallback": "caller-owned-legal-decision-spine",
    "legal_set": "ordered-kernel-subset-with-minimum-and-fully-contestable-maximum",
    "response_model": "heads-up-fold-call-only",
    "version": "adr0321-certified-reduced-sizing-consumer-v2",
}


def _canonical_sha256(payload: object) -> str:
    encoded = json.dumps(
        payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")
    return sha256(encoded).hexdigest()


ADR0321_CONSUMER_PROTOCOL_SHA256 = _canonical_sha256(_PROTOCOL)


def _require_chip_count(value: object, *, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{label} must be an integer chip count")
    if value <= 0:
        raise ValueError(f"{label} must be positive")
    return value


def _require_digest(value: object, *, label: str, optional: bool = False) -> None:
    if optional and value is None:
        return
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"{label} must be a lowercase SHA-256 digest")


@dataclass(frozen=True, slots=True)
class KernelRaiseToTotal:
    """A total street contribution named by an exact raise action."""

    chips: int

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "chips",
            _require_chip_count(self.chips, label="kernel raise-to total"),
        )


@dataclass(frozen=True, slots=True)
class ReducedBetIncrement:
    """A wager beyond the call base in the reduced one-bet game."""

    chips: int

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "chips",
            _require_chip_count(self.chips, label="reduced bet increment"),
        )


class LegalRaiseSetScope(StrEnum):
    COMPLETE_INTEGER_UNIVERSE = "complete-integer-universe"
    STRICT_RESTRICTED_SUBSET = "strict-restricted-subset"


class ReducedSizingResponseModel(StrEnum):
    HEADS_UP_FOLD_CALL_ONLY = "heads-up-fold-call-only"


@dataclass(frozen=True, slots=True)
class CertifiedReducedSizingRequestV2:
    """One immutable exact research request; a human label is not semantic."""

    context_id: str
    betting: NoLimitBettingState
    response_model: ReducedSizingResponseModel
    legal_raise_scope: LegalRaiseSetScope
    legal_raise_to_totals: tuple[KernelRaiseToTotal, ...]
    joint_probabilities: tuple[tuple[Fraction, ...], ...]
    showdown_signs: tuple[tuple[int, ...], ...]

    def __post_init__(self) -> None:
        if not isinstance(self.context_id, str) or not self.context_id.strip():
            raise ValueError("certified sizing context id must be nonempty")
        if not isinstance(self.betting, NoLimitBettingState):
            raise TypeError("certified sizing request requires an exact betting state")
        if not isinstance(self.response_model, ReducedSizingResponseModel):
            raise TypeError("certified sizing response model must be semantic")
        if not isinstance(self.legal_raise_scope, LegalRaiseSetScope):
            raise TypeError("certified sizing legal-set scope must be semantic")
        if (
            not isinstance(self.legal_raise_to_totals, tuple)
            or not self.legal_raise_to_totals
            or any(
                not isinstance(value, KernelRaiseToTotal)
                for value in self.legal_raise_to_totals
            )
        ):
            raise TypeError("certified sizing legal raises must be a nonempty nominal tuple")
        if not isinstance(self.joint_probabilities, tuple):
            raise TypeError("certified sizing probabilities must be immutable")
        if not isinstance(self.showdown_signs, tuple):
            raise TypeError("certified sizing showdown signs must be immutable")


class CertifiedSizingConsumerStageV2(StrEnum):
    REQUEST_BINDING = "request-binding"
    SOURCE_VERIFICATION = "source-verification"
    RUNTIME_VERIFICATION = "runtime-verification"
    BACKEND_SELECTION = "backend-selection"
    CERTIFIED_ADAPTER = "certified-adapter"
    RESULT_BINDING = "result-binding"


class CertifiedSizingConsumerRejectionReasonV2(StrEnum):
    UNSUPPORTED_GAME_SHAPE = "unsupported-game-shape"
    STALE_OR_ILLEGAL_RAISE_SET = "stale-or-illegal-raise-set"
    INVALID_EXACT_CONTEXT = "invalid-exact-context"
    SOURCE_DRIFT = "source-drift"
    RUNTIME_DRIFT = "runtime-drift"
    BACKEND_UNAVAILABLE = "backend-unavailable"
    ADAPTER_REJECTED = "adapter-rejected"
    RESULT_BINDING_FAILED = "result-binding-failed"


class CallerFallbackDispositionV2(StrEnum):
    NOT_REQUIRED_RESEARCH_RESULT = "not-required-research-result"
    REQUIRED_CALLER_OWNED_LEGAL_FALLBACK = "required-caller-owned-legal-fallback"


@dataclass(frozen=True, slots=True)
class ConsumerExceptionDescriptorV2:
    module: str
    type_name: str
    message: str

    def __post_init__(self) -> None:
        if not isinstance(self.module, str) or not self.module:
            raise ValueError("consumer exception module must be nonempty")
        if not isinstance(self.type_name, str) or not self.type_name:
            raise ValueError("consumer exception type must be nonempty")
        if not isinstance(self.message, str):
            raise TypeError("consumer exception message must be text")


def _exception_chain(error: Exception) -> tuple[ConsumerExceptionDescriptorV2, ...]:
    chain: list[ConsumerExceptionDescriptorV2] = []
    seen: set[int] = set()
    current: BaseException | None = error
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        chain.append(
            ConsumerExceptionDescriptorV2(
                module=type(current).__module__,
                type_name=type(current).__qualname__,
                message=str(current),
            )
        )
        if current.__cause__ is not None:
            current = current.__cause__
        elif not current.__suppress_context__:
            current = current.__context__
        else:
            current = None
    return tuple(chain)


@dataclass(frozen=True, slots=True)
class CertifiedReducedSizingAcceptedV2:
    request: CertifiedReducedSizingRequestV2
    context_id: str
    response_model: ReducedSizingResponseModel
    legal_raise_scope: LegalRaiseSetScope
    request_sha256: str
    public_state_sha256: str
    legal_raise_set_sha256: str
    consumer_source_sha256: str
    consumer_protocol_sha256: str
    public_highs_ds_invocation_count: int
    legal_raise_to_totals: tuple[KernelRaiseToTotal, ...]
    reduced_bet_increments: tuple[ReducedBetIncrement, ...]
    exact_opening_policy: tuple[tuple[Fraction, ...], ...]
    responder_best_actions: tuple[tuple[str, ...], ...]
    feasible_behavioral_lower_bound_chips: float
    certified_upper_bound_chips: float
    signed_certificate_gap_chips: float
    certified_gap_chips: float
    solution: CertifiedReducedSizingSolution
    fallback_disposition: CallerFallbackDispositionV2 = (
        CallerFallbackDispositionV2.NOT_REQUIRED_RESEARCH_RESULT
    )
    emitted_action: None = None

    def __post_init__(self) -> None:
        if not isinstance(self.request, CertifiedReducedSizingRequestV2):
            raise TypeError("accepted consumer must retain its exact request")
        if not isinstance(self.context_id, str) or not self.context_id.strip():
            raise ValueError("accepted consumer context id must be nonempty")
        if self.context_id != self.request.context_id:
            raise ValueError("accepted consumer context label differs from its request")
        if not isinstance(self.response_model, ReducedSizingResponseModel):
            raise TypeError("accepted response model must be semantic")
        if not isinstance(self.legal_raise_scope, LegalRaiseSetScope):
            raise TypeError("accepted legal-set scope must be semantic")
        for label, digest in (
            ("accepted request", self.request_sha256),
            ("accepted public state", self.public_state_sha256),
            ("accepted legal raise set", self.legal_raise_set_sha256),
            ("accepted consumer source", self.consumer_source_sha256),
            ("accepted consumer protocol", self.consumer_protocol_sha256),
        ):
            _require_digest(digest, label=label)
        if self.consumer_protocol_sha256 != ADR0321_CONSUMER_PROTOCOL_SHA256:
            raise ValueError("accepted consumer protocol identity drifted")
        if self.public_highs_ds_invocation_count != 1:
            raise ValueError("accepted consumer must record exactly one public call")
        if not isinstance(self.solution, CertifiedReducedSizingSolution):
            raise TypeError("accepted consumer requires a certified solution")
        if (
            not isinstance(self.legal_raise_to_totals, tuple)
            or any(
                not isinstance(value, KernelRaiseToTotal)
                for value in self.legal_raise_to_totals
            )
        ):
            raise TypeError("accepted raise-to totals are not nominal and immutable")
        if (
            not isinstance(self.reduced_bet_increments, tuple)
            or any(
                not isinstance(value, ReducedBetIncrement)
                for value in self.reduced_bet_increments
            )
        ):
            raise TypeError("accepted bet increments are not nominal and immutable")
        if len(self.legal_raise_to_totals) != len(self.reduced_bet_increments):
            raise ValueError("accepted amount mapping is not one-to-one")
        if self.solution.bet_sizes != tuple(
            value.chips for value in self.reduced_bet_increments
        ):
            raise ValueError("accepted solution uses different reduced bet increments")
        rebound = _bind_request(self.request)
        if (
            self.request_sha256 != rebound.request_sha256
            or self.public_state_sha256 != rebound.public_state_sha256
            or self.legal_raise_set_sha256 != rebound.legal_raise_set_sha256
            or self.legal_raise_to_totals != rebound.legal_raise_to_totals
            or self.reduced_bet_increments != rebound.reduced_bet_increments
            or self.solution.linear_program_sha256 != rebound.linear_program_sha256
        ):
            raise ValueError("accepted evidence differs from its rebound exact request")
        expected_fields = (
            (self.exact_opening_policy, self.solution.exact_opening_policy),
            (self.responder_best_actions, self.solution.responder_best_actions),
            (
                self.feasible_behavioral_lower_bound_chips,
                self.solution.feasible_behavioral_lower_bound_chips,
            ),
            (self.certified_upper_bound_chips, self.solution.certified_upper_bound_chips),
            (self.signed_certificate_gap_chips, self.solution.signed_certificate_gap_chips),
            (self.certified_gap_chips, self.solution.certified_gap_chips),
        )
        if any(left != right for left, right in expected_fields):
            raise ValueError("accepted evidence differs from its certified solution")
        if (
            self.fallback_disposition
            is not CallerFallbackDispositionV2.NOT_REQUIRED_RESEARCH_RESULT
        ):
            raise ValueError("accepted research evidence has the wrong fallback disposition")
        if self.emitted_action is not None:
            raise ValueError("the research consumer cannot emit a betting action")


@dataclass(frozen=True, slots=True)
class CertifiedReducedSizingRejectedV2:
    request: CertifiedReducedSizingRequestV2
    context_id: str
    stage: CertifiedSizingConsumerStageV2
    reason: CertifiedSizingConsumerRejectionReasonV2
    request_sha256: str | None
    public_state_sha256: str | None
    legal_raise_set_sha256: str | None
    consumer_source_sha256: str | None
    consumer_protocol_sha256: str
    public_highs_ds_invocation_count: int
    exception_chain: tuple[ConsumerExceptionDescriptorV2, ...]
    fallback_disposition: CallerFallbackDispositionV2 = (
        CallerFallbackDispositionV2.REQUIRED_CALLER_OWNED_LEGAL_FALLBACK
    )
    emitted_action: None = None

    def __post_init__(self) -> None:
        if not isinstance(self.request, CertifiedReducedSizingRequestV2):
            raise TypeError("rejected consumer must retain its exact request")
        if not isinstance(self.context_id, str) or not self.context_id.strip():
            raise ValueError("rejected consumer context id must be nonempty")
        if self.context_id != self.request.context_id:
            raise ValueError("rejected consumer context label differs from its request")
        if not isinstance(self.stage, CertifiedSizingConsumerStageV2):
            raise TypeError("rejected consumer stage must be semantic")
        if not isinstance(self.reason, CertifiedSizingConsumerRejectionReasonV2):
            raise TypeError("rejected consumer reason must be semantic")
        for label, digest in (
            ("rejected request", self.request_sha256),
            ("rejected public state", self.public_state_sha256),
            ("rejected legal raise set", self.legal_raise_set_sha256),
            ("rejected consumer source", self.consumer_source_sha256),
        ):
            _require_digest(digest, label=label, optional=True)
        _require_digest(
            self.consumer_protocol_sha256,
            label="rejected consumer protocol",
        )
        if self.consumer_protocol_sha256 != ADR0321_CONSUMER_PROTOCOL_SHA256:
            raise ValueError("rejected consumer protocol identity drifted")
        if (
            isinstance(self.public_highs_ds_invocation_count, bool)
            or not isinstance(self.public_highs_ds_invocation_count, int)
            or self.public_highs_ds_invocation_count < 0
        ):
            raise ValueError("rejected consumer call count must be nonnegative")
        if (
            not isinstance(self.exception_chain, tuple)
            or not self.exception_chain
            or any(
                not isinstance(value, ConsumerExceptionDescriptorV2)
                for value in self.exception_chain
            )
        ):
            raise TypeError("rejected consumer must retain a typed exception chain")
        if (
            self.fallback_disposition
            is not CallerFallbackDispositionV2.REQUIRED_CALLER_OWNED_LEGAL_FALLBACK
        ):
            raise ValueError("rejected consumer must require the caller-owned fallback")
        if self.emitted_action is not None:
            raise ValueError("a rejected research consumer cannot emit a betting action")


CertifiedReducedSizingConsumerResultV2 = (
    CertifiedReducedSizingAcceptedV2 | CertifiedReducedSizingRejectedV2
)


class _RequestContractError(ValueError):
    def __init__(
        self,
        reason: CertifiedSizingConsumerRejectionReasonV2,
        message: str,
    ) -> None:
        self.reason = reason
        super().__init__(message)


@dataclass(frozen=True, slots=True)
class _BoundRequest:
    public_state_sha256: str
    request_sha256: str
    legal_raise_set_sha256: str
    legal_raise_to_totals: tuple[KernelRaiseToTotal, ...]
    reduced_bet_increments: tuple[ReducedBetIncrement, ...]
    minimum_bet_increment: ReducedBetIncrement
    maximum_bet_increment: ReducedBetIncrement
    linear_program_sha256: str


def _decision_payload(decision: object) -> dict[str, object]:
    from .no_limit_betting import LegalBettingDecision

    if not isinstance(decision, LegalBettingDecision):
        raise TypeError("consumer decision payload requires a legal decision")
    bounds = decision.raise_bounds
    return {
        "action_kinds": tuple(kind.value for kind in decision.action_kinds),
        "acting_seat": decision.acting_seat,
        "call_amount": decision.call_amount,
        "current_bet": decision.current_bet,
        "raise_bounds": (
            None
            if bounds is None
            else {
                "all_in_only": bounds.all_in_only,
                "maximum_contestable_raise_to": bounds.maximum_contestable_raise_to,
                "maximum_raise_to": bounds.maximum_raise_to,
                "minimum_full_raise_to": bounds.minimum_full_raise_to,
                "minimum_raise_to": bounds.minimum_raise_to,
            }
        ),
        "stack": decision.stack,
        "street": decision.street.value,
        "street_contribution": decision.street_contribution,
        "to_call": decision.to_call,
    }


def _bind_request(request: CertifiedReducedSizingRequestV2) -> _BoundRequest:
    state = request.betting
    try:
        state.assert_invariants()
        decision = state.legal_decision()
    except (AssertionError, TypeError, ValueError) as error:
        raise _RequestContractError(
            CertifiedSizingConsumerRejectionReasonV2.INVALID_EXACT_CONTEXT,
            "certified sizing public state has no exact live decision",
        ) from error

    if request.response_model is not ReducedSizingResponseModel.HEADS_UP_FOLD_CALL_ONLY:
        raise _RequestContractError(
            CertifiedSizingConsumerRejectionReasonV2.UNSUPPORTED_GAME_SHAPE,
            "certified sizing consumer supports only the heads-up fold/call model",
        )
    if state.street is not BettingStreet.RIVER or len(state.live_seats) != 2:
        raise _RequestContractError(
            CertifiedSizingConsumerRejectionReasonV2.UNSUPPORTED_GAME_SHAPE,
            "certified sizing consumer requires exactly two live seats on the river",
        )
    if (
        decision.to_call != 0
        or decision.call_amount != 0
        or not decision.can_check
        or decision.can_fold
        or decision.can_call
    ):
        raise _RequestContractError(
            CertifiedSizingConsumerRejectionReasonV2.UNSUPPORTED_GAME_SHAPE,
            "certified sizing consumer requires an unopened check-or-raise decision",
        )
    bounds = decision.raise_bounds
    if bounds is None:
        raise _RequestContractError(
            CertifiedSizingConsumerRejectionReasonV2.UNSUPPORTED_GAME_SHAPE,
            "certified sizing consumer requires at least one legal raise",
        )
    if bounds.maximum_contestable_raise_to != bounds.maximum_raise_to:
        raise _RequestContractError(
            CertifiedSizingConsumerRejectionReasonV2.UNSUPPORTED_GAME_SHAPE,
            "certified sizing consumer requires every modeled raise to be fully contestable",
        )
    if state.pot <= 0 or state.pot % 2:
        raise _RequestContractError(
            CertifiedSizingConsumerRejectionReasonV2.UNSUPPORTED_GAME_SHAPE,
            "certified sizing consumer requires a positive even public pot",
        )

    totals = request.legal_raise_to_totals
    amounts = tuple(value.chips for value in totals)
    if any(left >= right for left, right in pairwise(amounts)):
        raise _RequestContractError(
            CertifiedSizingConsumerRejectionReasonV2.STALE_OR_ILLEGAL_RAISE_SET,
            "kernel legal raise-to totals must increase strictly",
        )
    if amounts[0] != bounds.minimum_raise_to or amounts[-1] != bounds.maximum_raise_to:
        raise _RequestContractError(
            CertifiedSizingConsumerRejectionReasonV2.STALE_OR_ILLEGAL_RAISE_SET,
            "kernel legal raise-to subset must retain exact minimum and maximum anchors",
        )
    if any(
        amount < bounds.minimum_raise_to or amount > bounds.maximum_raise_to
        for amount in amounts
    ):
        raise _RequestContractError(
            CertifiedSizingConsumerRejectionReasonV2.STALE_OR_ILLEGAL_RAISE_SET,
            "caller-supplied raise-to total lies outside the kernel legal interval",
        )
    complete = (
        len(amounts) == bounds.maximum_raise_to - bounds.minimum_raise_to + 1
        and all(
            amount == bounds.minimum_raise_to + index
            for index, amount in enumerate(amounts)
        )
    )
    if (
        request.legal_raise_scope is LegalRaiseSetScope.COMPLETE_INTEGER_UNIVERSE
        and not complete
    ):
        raise _RequestContractError(
            CertifiedSizingConsumerRejectionReasonV2.STALE_OR_ILLEGAL_RAISE_SET,
            "restricted legal raises cannot claim complete-integer scope",
        )
    if (
        request.legal_raise_scope is LegalRaiseSetScope.STRICT_RESTRICTED_SUBSET
        and complete
    ):
        raise _RequestContractError(
            CertifiedSizingConsumerRejectionReasonV2.STALE_OR_ILLEGAL_RAISE_SET,
            "complete legal raises cannot claim strict-restricted scope",
        )

    base_raise_to = decision.street_contribution + decision.call_amount
    increments = tuple(
        ReducedBetIncrement(amount - base_raise_to) for amount in amounts
    )
    minimum_increment = ReducedBetIncrement(
        bounds.minimum_raise_to - base_raise_to
    )
    maximum_increment = ReducedBetIncrement(
        bounds.maximum_raise_to - base_raise_to
    )
    if increments[0] != minimum_increment or increments[-1] != maximum_increment:
        raise AssertionError("nominal raise-to conversion lost a legal endpoint")

    try:
        linear_program = compile_reduced_river_sizing_lp(
            pot=state.pot,
            stack=maximum_increment.chips,
            minimum_bet=minimum_increment.chips,
            joint_probabilities=request.joint_probabilities,
            showdown_signs=request.showdown_signs,
            bet_sizes=tuple(value.chips for value in increments),
        )
    except (TypeError, ValueError) as error:
        raise _RequestContractError(
            CertifiedSizingConsumerRejectionReasonV2.INVALID_EXACT_CONTEXT,
            "certified sizing exact probability/payoff context is invalid",
        ) from error

    public_digest = public_betting_state_sha256(state)
    decision_data = _decision_payload(decision)
    legal_digest = _canonical_sha256(
        {
            "decision": decision_data,
            "public_state_sha256": public_digest,
            "raise_to_totals": amounts,
            "scope": request.legal_raise_scope.value,
            "version": "adr0321-kernel-legal-raise-set-v1",
        }
    )
    request_digest = _canonical_sha256(
        {
            "bet_increments": tuple(value.chips for value in increments),
            "decision": decision_data,
            "joint_probabilities": tuple(
                tuple((value.numerator, value.denominator) for value in row)
                for row in request.joint_probabilities
            ),
            "legal_raise_set_sha256": legal_digest,
            "public_state_sha256": public_digest,
            "response_model": request.response_model.value,
            "showdown_signs": request.showdown_signs,
            "version": "adr0321-certified-reduced-sizing-request-v2",
        }
    )
    return _BoundRequest(
        public_state_sha256=public_digest,
        request_sha256=request_digest,
        legal_raise_set_sha256=legal_digest,
        legal_raise_to_totals=totals,
        reduced_bet_increments=increments,
        minimum_bet_increment=minimum_increment,
        maximum_bet_increment=maximum_increment,
        linear_program_sha256=linear_program.digest,
    )


class _CountedPublicHighsCall:
    def __init__(self, delegate: Callable[..., Any]) -> None:
        self.delegate = delegate
        self.invocation_count = 0

    def __call__(self, *args: object, **kwargs: object) -> object:
        self.invocation_count += 1
        if self.invocation_count > 1:
            raise RuntimeError("certified sizing consumer attempted a backend retry")
        return self.delegate(*args, **kwargs)


def verify_adr0321_consumer_source_and_dependencies() -> str:
    """Verify the source-only consumer seal before any backend proposal."""

    from .certified_reduced_sizing_consumer_v2_seal import (
        ADR0321_CONSUMER_PROTOCOL_SHA256 as expected_protocol,
        ADR0321_CONSUMER_SOURCE_MANIFEST,
    )

    source_root = Path(__file__).resolve().parent
    actual = {
        name: canonical_lf_source_sha256(source_root / name)
        for name in ADR0321_CONSUMER_SOURCE_MANIFEST
    }
    if actual != ADR0321_CONSUMER_SOURCE_MANIFEST:
        raise RuntimeError("ADR-0321 consumer source or dependency differs from its seal")
    if ADR0321_CONSUMER_PROTOCOL_SHA256 != expected_protocol:
        raise RuntimeError("ADR-0321 consumer protocol differs from its seal")
    return actual["certified_reduced_sizing_consumer_v2.py"]


def _rejection(
    request: CertifiedReducedSizingRequestV2,
    *,
    stage: CertifiedSizingConsumerStageV2,
    reason: CertifiedSizingConsumerRejectionReasonV2,
    error: Exception,
    bound: _BoundRequest | None,
    consumer_source_sha256: str | None,
    invocation_count: int,
) -> CertifiedReducedSizingRejectedV2:
    return CertifiedReducedSizingRejectedV2(
        request=request,
        context_id=request.context_id,
        stage=stage,
        reason=reason,
        request_sha256=None if bound is None else bound.request_sha256,
        public_state_sha256=(
            None if bound is None else bound.public_state_sha256
        ),
        legal_raise_set_sha256=(
            None if bound is None else bound.legal_raise_set_sha256
        ),
        consumer_source_sha256=consumer_source_sha256,
        consumer_protocol_sha256=ADR0321_CONSUMER_PROTOCOL_SHA256,
        public_highs_ds_invocation_count=invocation_count,
        exception_chain=_exception_chain(error),
    )


def consume_certified_reduced_sizing_v2(
    request: CertifiedReducedSizingRequestV2,
    *,
    linprog_function: Callable[..., Any] | None = None,
) -> CertifiedReducedSizingConsumerResultV2:
    """Return certified reduced-game evidence or a typed no-action rejection."""

    if not isinstance(request, CertifiedReducedSizingRequestV2):
        raise TypeError("certified sizing consumer requires a semantic v2 request")
    bound: _BoundRequest | None = None
    consumer_source: str | None = None
    try:
        bound = _bind_request(request)
    except _RequestContractError as error:
        return _rejection(
            request,
            stage=CertifiedSizingConsumerStageV2.REQUEST_BINDING,
            reason=error.reason,
            error=error,
            bound=None,
            consumer_source_sha256=None,
            invocation_count=0,
        )

    try:
        consumer_source = verify_adr0321_consumer_source_and_dependencies()
        verify_adr0318_source_and_dependencies()
    except Exception as error:  # source drift is evidence, never a backend call
        return _rejection(
            request,
            stage=CertifiedSizingConsumerStageV2.SOURCE_VERIFICATION,
            reason=CertifiedSizingConsumerRejectionReasonV2.SOURCE_DRIFT,
            error=error,
            bound=bound,
            consumer_source_sha256=None,
            invocation_count=0,
        )

    try:
        verify_adr0318_runtime_identity()
    except Exception as error:  # runtime drift is evidence, never a backend call
        return _rejection(
            request,
            stage=CertifiedSizingConsumerStageV2.RUNTIME_VERIFICATION,
            reason=CertifiedSizingConsumerRejectionReasonV2.RUNTIME_DRIFT,
            error=error,
            bound=bound,
            consumer_source_sha256=consumer_source,
            invocation_count=0,
        )

    try:
        backend = (
            import_module("scipy.optimize").linprog
            if linprog_function is None
            else linprog_function
        )
        if not callable(backend):
            raise TypeError("certified sizing public backend must be callable")
    except Exception as error:
        return _rejection(
            request,
            stage=CertifiedSizingConsumerStageV2.BACKEND_SELECTION,
            reason=CertifiedSizingConsumerRejectionReasonV2.BACKEND_UNAVAILABLE,
            error=error,
            bound=bound,
            consumer_source_sha256=consumer_source,
            invocation_count=0,
        )

    counted = _CountedPublicHighsCall(backend)
    try:
        solution = solve_certified_reduced_sizing_highs(
            pot=request.betting.pot,
            stack=bound.maximum_bet_increment.chips,
            minimum_bet=bound.minimum_bet_increment.chips,
            joint_probabilities=request.joint_probabilities,
            showdown_signs=request.showdown_signs,
            bet_sizes=tuple(value.chips for value in bound.reduced_bet_increments),
            linprog_function=counted,
        )
    except Exception as error:
        return _rejection(
            request,
            stage=CertifiedSizingConsumerStageV2.CERTIFIED_ADAPTER,
            reason=CertifiedSizingConsumerRejectionReasonV2.ADAPTER_REJECTED,
            error=error,
            bound=bound,
            consumer_source_sha256=consumer_source,
            invocation_count=counted.invocation_count,
        )

    try:
        if counted.invocation_count != 1:
            raise RuntimeError("certified sizing adapter did not make exactly one public call")
        if solution.linear_program_sha256 != bound.linear_program_sha256:
            raise RuntimeError("certified sizing solution belongs to another linear program")
        return CertifiedReducedSizingAcceptedV2(
            request=request,
            context_id=request.context_id,
            response_model=request.response_model,
            legal_raise_scope=request.legal_raise_scope,
            request_sha256=bound.request_sha256,
            public_state_sha256=bound.public_state_sha256,
            legal_raise_set_sha256=bound.legal_raise_set_sha256,
            consumer_source_sha256=consumer_source,
            consumer_protocol_sha256=ADR0321_CONSUMER_PROTOCOL_SHA256,
            public_highs_ds_invocation_count=counted.invocation_count,
            legal_raise_to_totals=bound.legal_raise_to_totals,
            reduced_bet_increments=bound.reduced_bet_increments,
            exact_opening_policy=solution.exact_opening_policy,
            responder_best_actions=solution.responder_best_actions,
            feasible_behavioral_lower_bound_chips=(
                solution.feasible_behavioral_lower_bound_chips
            ),
            certified_upper_bound_chips=solution.certified_upper_bound_chips,
            signed_certificate_gap_chips=solution.signed_certificate_gap_chips,
            certified_gap_chips=solution.certified_gap_chips,
            solution=solution,
        )
    except Exception as error:
        return _rejection(
            request,
            stage=CertifiedSizingConsumerStageV2.RESULT_BINDING,
            reason=CertifiedSizingConsumerRejectionReasonV2.RESULT_BINDING_FAILED,
            error=error,
            bound=bound,
            consumer_source_sha256=consumer_source,
            invocation_count=counted.invocation_count,
        )


__all__ = [
    "ADR0321_CONSUMER_PROTOCOL_SHA256",
    "CallerFallbackDispositionV2",
    "CertifiedReducedSizingAcceptedV2",
    "CertifiedReducedSizingConsumerResultV2",
    "CertifiedReducedSizingRejectedV2",
    "CertifiedReducedSizingRequestV2",
    "CertifiedSizingConsumerRejectionReasonV2",
    "CertifiedSizingConsumerStageV2",
    "ConsumerExceptionDescriptorV2",
    "KernelRaiseToTotal",
    "LegalRaiseSetScope",
    "ReducedBetIncrement",
    "ReducedSizingResponseModel",
    "consume_certified_reduced_sizing_v2",
    "verify_adr0321_consumer_source_and_dependencies",
]
