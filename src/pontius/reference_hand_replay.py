"""Complete explicit-deal replay through the one-seat legal decision spine."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import TypeVar

from .full_width_belief import FullWidthBeliefSnapshot, FullWidthOneSeatBelief
from .full_width_reference_policy import (
    BlueprintActionLikelihood,
    FullWidthPolicyDistribution,
    ImmutableFullWidthReferencePolicy,
)
from .holdem_cards import HandRank, OneSeatCardState, SixSeatHoldemDeal
from .immutable_blueprint import (
    BlueprintSelection,
    ImmutableBlueprintActionSource,
)
from .legal_decision_spine import (
    ActionSelectionReason,
    EmittedBettingAction,
    LegalDecisionSpine,
)
from .no_limit_betting import (
    BETTING_STREETS,
    SEAT_COUNT,
    BettingAction,
    BettingStreet,
    HandSettlement,
    NoLimitBettingState,
    TerminalReason,
)
from .street_deadline import StreetDeadlineSnapshot

_T = TypeVar("_T")


class ReplayOperationKind(StrEnum):
    BETTING_HAND_INITIALIZATION = "betting_hand_initialization"
    VISIBLE_CARD_INITIALIZATION = "visible_card_initialization"
    CARD_DOMAIN_AUDIT = "card_domain_audit"
    OPPONENT_EVENT_VALIDATION = "opponent_event_validation"
    OPPONENT_ACTION_APPLICATION = "opponent_action_application"
    CONTROLLED_DECISION_OPEN = "controlled_decision_open"
    BLUEPRINT_SELECTION = "blueprint_selection"
    CONTROLLED_ACTION_EMISSION = "controlled_action_emission"
    BETTING_STREET_TRANSITION = "betting_street_transition"
    PUBLIC_CARD_REVEAL = "public_card_reveal"
    FULL_WIDTH_BELIEF_INITIALIZATION = "full_width_belief_initialization"
    FULL_WIDTH_BELIEF_SNAPSHOT = "full_width_belief_snapshot"
    FULL_WIDTH_POLICY_SELECTION = "full_width_policy_selection"
    OPPONENT_ACTION_LIKELIHOOD = "opponent_action_likelihood"
    FULL_WIDTH_BELIEF_UPDATE = "full_width_belief_update"
    FULL_WIDTH_BOARD_FILTER = "full_width_board_filter"


@dataclass(frozen=True, slots=True)
class OpponentActionEvent:
    street: BettingStreet
    seat: int
    action: BettingAction

    def __post_init__(self) -> None:
        if not isinstance(self.street, BettingStreet):
            raise TypeError("opponent event street must be canonical")
        if (
            isinstance(self.seat, bool)
            or not isinstance(self.seat, int)
            or self.seat not in range(SEAT_COUNT)
        ):
            raise ValueError("opponent event seat must identify one of six seats")
        if not isinstance(self.action, BettingAction):
            raise TypeError("opponent event action must be semantic")


@dataclass(frozen=True, slots=True)
class ReferenceHandSpec:
    deal: SixSeatHoldemDeal
    button: int
    controlled_seat: int
    starting_stacks: tuple[int, ...]
    small_blind: int
    big_blind: int
    blueprint: ImmutableBlueprintActionSource
    opponent_actions: tuple[OpponentActionEvent, ...]
    full_width_policy: ImmutableFullWidthReferencePolicy | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.deal, SixSeatHoldemDeal):
            raise TypeError("reference hand requires an explicit six-seat deal")
        for name, seat in (
            ("button", self.button),
            ("controlled seat", self.controlled_seat),
        ):
            if (
                isinstance(seat, bool)
                or not isinstance(seat, int)
                or seat not in range(SEAT_COUNT)
            ):
                raise ValueError(f"reference hand {name} must identify one of six seats")
        if not isinstance(self.starting_stacks, tuple):
            raise TypeError("reference starting stacks must be an immutable tuple")
        if len(self.starting_stacks) != SEAT_COUNT:
            raise ValueError("reference hand requires six starting stacks")
        if not isinstance(self.blueprint, ImmutableBlueprintActionSource):
            raise TypeError("reference hand requires an immutable blueprint source")
        if self.full_width_policy is not None and not isinstance(
            self.full_width_policy,
            ImmutableFullWidthReferencePolicy,
        ):
            raise TypeError("full-width reference policy must be immutable and semantic")
        if not isinstance(self.opponent_actions, tuple):
            raise TypeError("opponent events must be an immutable tuple")
        if any(
            not isinstance(event, OpponentActionEvent)
            for event in self.opponent_actions
        ):
            raise TypeError("reference hand contains a non-event opponent action")
        if any(event.seat == self.controlled_seat for event in self.opponent_actions):
            raise ValueError("controlled-seat actions must come from the blueprint")


@dataclass(frozen=True, slots=True)
class ReplayChargedOperation:
    kind: ReplayOperationKind
    street: BettingStreet
    charged_before_seconds: float
    charged_after_seconds: float
    interval_before: int
    interval_after: int


@dataclass(frozen=True, slots=True)
class CardDomainSnapshot:
    street: BettingStreet
    public_board_size: int
    compatible_opponent_hands: int
    public_digest: str


@dataclass(frozen=True, slots=True)
class ReferenceHandResult:
    deal_digest: str
    blueprint_digest: str
    controlled_seat: int
    final_cards: OneSeatCardState
    final_betting: NoLimitBettingState
    controlled_selections: tuple[BlueprintSelection, ...]
    controlled_emissions: tuple[EmittedBettingAction, ...]
    opponent_events_consumed: int
    charged_operations: tuple[ReplayChargedOperation, ...]
    card_domains: tuple[CardDomainSnapshot, ...]
    completed_street_deadlines: tuple[StreetDeadlineSnapshot, ...]
    full_width_policy_digest: str | None
    final_full_width_belief: FullWidthOneSeatBelief | None
    full_width_belief_snapshots: tuple[FullWidthBeliefSnapshot, ...]
    opponent_action_likelihoods: tuple[BlueprintActionLikelihood, ...]
    controlled_policy_distributions: tuple[FullWidthPolicyDistribution, ...]
    showdown_strengths: tuple[HandRank | None, ...] | None
    settlement: HandSettlement
    post_hand_verification_wall_seconds: float


def replay_reference_hand(
    spec: ReferenceHandSpec,
    *,
    clock_ns: Callable[[], int] | None = None,
) -> ReferenceHandResult:
    """Replay one complete explicit hand with the controlled seat on blueprint."""

    if not isinstance(spec, ReferenceHandSpec):
        raise TypeError("reference replay requires a frozen hand specification")
    spine = LegalDecisionSpine.new_hand(
        button=spec.button,
        controlled_seat=spec.controlled_seat,
        starting_stacks=spec.starting_stacks,
        small_blind=spec.small_blind,
        big_blind=spec.big_blind,
        clock_ns=clock_ns,
    )
    initial_deadline = spine.deadline
    charged_operations: list[ReplayChargedOperation] = [
        ReplayChargedOperation(
            kind=ReplayOperationKind.BETTING_HAND_INITIALIZATION,
            street=BettingStreet.PREFLOP,
            charged_before_seconds=0.0,
            charged_after_seconds=initial_deadline.charged_compute_seconds,
            interval_before=0,
            interval_after=initial_deadline.charge_intervals,
        )
    ]

    def charged(kind: ReplayOperationKind, operation: Callable[[], _T]) -> _T:
        before = spine.deadline
        with spine.charge_compute():
            value = operation()
        after = spine.deadline
        if after.street != before.street:
            raise AssertionError("one charged replay operation crossed a street")
        if after.charge_intervals != before.charge_intervals + 1:
            raise AssertionError("charged replay operation did not own one interval")
        if after.charged_compute_seconds < before.charged_compute_seconds:
            raise AssertionError("charged replay operation moved time backwards")
        charged_operations.append(
            ReplayChargedOperation(
                kind=kind,
                street=BettingStreet(after.street),
                charged_before_seconds=before.charged_compute_seconds,
                charged_after_seconds=after.charged_compute_seconds,
                interval_before=before.charge_intervals,
                interval_after=after.charge_intervals,
            )
        )
        return value

    def record_internal_charge(
        kind: ReplayOperationKind,
        operation: Callable[[], _T],
    ) -> _T:
        """Record one interval owned and charged inside the decision spine."""

        before = spine.deadline
        value = operation()
        after = spine.deadline
        if after.street != before.street:
            raise AssertionError("nontransition operation crossed a street")
        if after.charge_intervals != before.charge_intervals + 1:
            raise AssertionError("spine operation did not own one charged interval")
        if after.charged_compute_seconds < before.charged_compute_seconds:
            raise AssertionError("spine operation moved time backwards")
        charged_operations.append(
            ReplayChargedOperation(
                kind=kind,
                street=BettingStreet(after.street),
                charged_before_seconds=before.charged_compute_seconds,
                charged_after_seconds=after.charged_compute_seconds,
                interval_before=before.charge_intervals,
                interval_after=after.charge_intervals,
            )
        )
        return value

    def advance_betting_street() -> NoLimitBettingState:
        """Record transition work against the street that it closes."""

        before = spine.deadline
        completed_before = len(spine.completed_street_deadlines)
        advanced = spine.advance_street()
        completed = spine.completed_street_deadlines
        if len(completed) != completed_before + 1:
            raise AssertionError("betting transition did not close exactly one ledger")
        closing = completed[-1]
        if closing.street != before.street:
            raise AssertionError("betting transition closed the wrong street ledger")
        if closing.charge_intervals != before.charge_intervals + 1:
            raise AssertionError("betting transition did not own one charged interval")
        if closing.charged_compute_seconds < before.charged_compute_seconds:
            raise AssertionError("betting transition moved time backwards")
        charged_operations.append(
            ReplayChargedOperation(
                kind=ReplayOperationKind.BETTING_STREET_TRANSITION,
                street=BettingStreet(closing.street),
                charged_before_seconds=before.charged_compute_seconds,
                charged_after_seconds=closing.charged_compute_seconds,
                interval_before=before.charge_intervals,
                interval_after=closing.charge_intervals,
            )
        )
        return advanced

    def initial_cards() -> OneSeatCardState:
        visible = OneSeatCardState.preflop(
            controlled_seat=spec.controlled_seat,
            private_hand=spec.deal.hand(spec.controlled_seat),
        )
        visible.require_compatible_deal(spec.deal)
        return visible

    cards = charged(
        ReplayOperationKind.VISIBLE_CARD_INITIALIZATION,
        initial_cards,
    )
    card_domains: list[CardDomainSnapshot] = []

    def record_card_domain(current_cards: OneSeatCardState) -> None:
        card_domains.append(
            charged(
                ReplayOperationKind.CARD_DOMAIN_AUDIT,
                lambda current_cards=current_cards: CardDomainSnapshot(
                    street=current_cards.street,
                    public_board_size=len(current_cards.board),
                    compatible_opponent_hands=(
                        current_cards.compatible_opponent_hand_count
                    ),
                    public_digest=current_cards.public_digest,
                ),
            )
        )

    record_card_domain(cards)
    full_width_belief: FullWidthOneSeatBelief | None = None
    belief_snapshots: list[FullWidthBeliefSnapshot] = []
    action_likelihoods: list[BlueprintActionLikelihood] = []
    policy_distributions: list[FullWidthPolicyDistribution] = []

    def record_belief_snapshot(current_belief: FullWidthOneSeatBelief) -> None:
        belief_snapshots.append(
            charged(
                ReplayOperationKind.FULL_WIDTH_BELIEF_SNAPSHOT,
                current_belief.snapshot,
            )
        )

    if spec.full_width_policy is not None:
        current_cards = cards
        full_width_belief = charged(
            ReplayOperationKind.FULL_WIDTH_BELIEF_INITIALIZATION,
            lambda current_cards=current_cards: FullWidthOneSeatBelief.uniform(
                current_cards
            ),
        )
        record_belief_snapshot(full_width_belief)
    event_index = 0
    selections: list[BlueprintSelection] = []
    emissions: list[EmittedBettingAction] = []

    while not spine.state.is_terminal:
        state = spine.state
        if state.round_complete:
            prior_street = state.street
            advanced = advance_betting_street()
            if advanced.is_terminal:
                break
            if advanced.street is prior_street:
                raise AssertionError("nonterminal betting transition did not advance")

            current_cards = cards

            def reveal_public_cards(
                current_cards: OneSeatCardState = current_cards,
                street: BettingStreet = advanced.street,
            ) -> OneSeatCardState:
                visible = current_cards.advance_to(
                    street,
                    spec.deal.reveal_for(street),
                )
                visible.require_compatible_deal(spec.deal)
                return visible

            cards = charged(
                ReplayOperationKind.PUBLIC_CARD_REVEAL,
                reveal_public_cards,
            )
            if full_width_belief is not None:
                prior_belief = full_width_belief
                current_cards = cards
                full_width_belief = charged(
                    ReplayOperationKind.FULL_WIDTH_BOARD_FILTER,
                    lambda prior_belief=prior_belief,
                    current_cards=current_cards: prior_belief.advance_to(current_cards),
                )
                record_belief_snapshot(full_width_belief)
            record_card_domain(cards)
            continue

        acting_seat = state.acting_seat
        if acting_seat == spec.controlled_seat:
            ticket = record_internal_charge(
                ReplayOperationKind.CONTROLLED_DECISION_OPEN,
                spine.open_controlled_decision,
            )
            current_cards = cards
            current_betting = spine.state
            current_decision = ticket.decision
            selection = charged(
                ReplayOperationKind.BLUEPRINT_SELECTION,
                lambda current_cards=current_cards,
                current_betting=current_betting,
                current_decision=current_decision: spec.blueprint.action_for(
                    cards=current_cards,
                    betting=current_betting,
                    decision=current_decision,
                ),
            )
            distribution: FullWidthPolicyDistribution | None = None
            if spec.full_width_policy is not None:
                distribution = charged(
                    ReplayOperationKind.FULL_WIDTH_POLICY_SELECTION,
                    lambda current_cards=current_cards,
                    current_betting=current_betting,
                    current_decision=current_decision: (
                        spec.full_width_policy.distribution_for(
                            cards=current_cards,
                            betting=current_betting,
                            decision=current_decision,
                        )
                    ),
                )
                policy_distributions.append(distribution)
            candidate = None if distribution is None else distribution.selected_action
            emitted = record_internal_charge(
                ReplayOperationKind.CONTROLLED_ACTION_EMISSION,
                lambda selection=selection, candidate=candidate: (
                    spine.emit_controlled_action(
                        candidate=candidate,
                        fallback=selection.action,
                    )
                ),
            )
            if distribution is None:
                if emitted.reason is not ActionSelectionReason.NO_CANDIDATE:
                    raise AssertionError("blueprint-only replay admitted a candidate")
                if emitted.selected != selection.action or not emitted.used_fallback:
                    raise AssertionError(
                        "controlled action did not use exact blueprint fallback"
                    )
            else:
                if emitted.reason is not ActionSelectionReason.CANDIDATE:
                    raise RuntimeError("full-width policy action missed its timely gate")
                if emitted.selected != distribution.selected_action:
                    raise AssertionError("emission changed the full-width policy action")
                if emitted.used_fallback:
                    raise AssertionError("timely full-width policy action used fallback")
            selections.append(selection)
            emissions.append(emitted)
            continue

        def decode_opponent_event(
            expected_index: int = event_index,
            expected_street: BettingStreet = state.street,
            expected_seat: int | None = acting_seat,
        ) -> OpponentActionEvent:
            if expected_index >= len(spec.opponent_actions):
                raise ValueError("opponent action script ended before the hand")
            event = spec.opponent_actions[expected_index]
            if event.street is not expected_street:
                raise ValueError("opponent action script names the wrong street")
            if event.seat != expected_seat:
                raise ValueError("opponent action script names the wrong acting seat")
            return event

        event = charged(
            ReplayOperationKind.OPPONENT_EVENT_VALIDATION,
            decode_opponent_event,
        )
        if full_width_belief is not None:
            if spec.full_width_policy is None:
                raise AssertionError("full-width belief lost its policy source")
            current_belief = full_width_belief
            current_cards = cards
            current_betting = spine.state
            observed_action = event.action
            actor_seat = event.seat
            likelihood = charged(
                ReplayOperationKind.OPPONENT_ACTION_LIKELIHOOD,
                lambda current_belief=current_belief,
                current_cards=current_cards,
                current_betting=current_betting,
                observed_action=observed_action,
                actor_seat=actor_seat: spec.full_width_policy.likelihood_for_axis(
                    visible_cards=current_cards,
                    actor_seat=actor_seat,
                    hand_axis=current_belief.hand_axis,
                    betting=current_betting,
                    decision=current_betting.legal_decision(),
                    observed_action=observed_action,
                ),
            )
            action_likelihoods.append(likelihood)
            full_width_belief = charged(
                ReplayOperationKind.FULL_WIDTH_BELIEF_UPDATE,
                lambda current_belief=current_belief,
                likelihood=likelihood: current_belief.with_action_likelihood(likelihood),
            )
        event_index += 1
        record_internal_charge(
            ReplayOperationKind.OPPONENT_ACTION_APPLICATION,
            lambda event=event: spine.observe_opponent_action(event.action),
        )

    if event_index != len(spec.opponent_actions):
        raise ValueError("opponent action script contains events after hand termination")
    cards.require_compatible_deal(spec.deal)
    final_betting = spine.state
    if cards.street is not final_betting.street:
        raise AssertionError("terminal card and betting streets disagree")
    if full_width_belief is not None:
        if full_width_belief.cards != cards:
            raise AssertionError("terminal full-width belief has a stale card state")
        if len(action_likelihoods) != event_index:
            raise AssertionError("not every opponent event updated the full-width belief")
        if len(belief_snapshots) != len(card_domains):
            raise AssertionError("full-width belief did not snapshot every visible street")

    completed = spine.completed_street_deadlines
    expected_streets = BETTING_STREETS[: len(completed)]
    if tuple(BettingStreet(snapshot.street) for snapshot in completed) != expected_streets:
        raise AssertionError("completed street ledger history is not contiguous")
    if any(snapshot.deadline_crossed for snapshot in completed):
        raise RuntimeError("reference hand exceeded a 15-second charged street budget")

    verification_started_ns = time.monotonic_ns()
    if final_betting.terminal_reason is TerminalReason.SHOWDOWN:
        if cards.street is not BettingStreet.RIVER or len(cards.board) != 5:
            raise AssertionError("showdown requires a complete public board")
        strengths = spec.deal.showdown_strengths(final_betting.live_seats)
        settlement = final_betting.settle(strengths)
    else:
        strengths = None
        settlement = final_betting.settle()
    verification_seconds = (
        time.monotonic_ns() - verification_started_ns
    ) / 1_000_000_000

    return ReferenceHandResult(
        deal_digest=spec.deal.digest,
        blueprint_digest=spec.blueprint.digest,
        controlled_seat=spec.controlled_seat,
        final_cards=cards,
        final_betting=final_betting,
        controlled_selections=tuple(selections),
        controlled_emissions=tuple(emissions),
        opponent_events_consumed=event_index,
        charged_operations=tuple(charged_operations),
        card_domains=tuple(card_domains),
        completed_street_deadlines=completed,
        full_width_policy_digest=(
            None if spec.full_width_policy is None else spec.full_width_policy.digest
        ),
        final_full_width_belief=full_width_belief,
        full_width_belief_snapshots=tuple(belief_snapshots),
        opponent_action_likelihoods=tuple(action_likelihoods),
        controlled_policy_distributions=tuple(policy_distributions),
        showdown_strengths=strengths,
        settlement=settlement,
        post_hand_verification_wall_seconds=verification_seconds,
    )


__all__ = [
    "CardDomainSnapshot",
    "OpponentActionEvent",
    "ReferenceHandResult",
    "ReferenceHandSpec",
    "ReplayChargedOperation",
    "ReplayOperationKind",
    "replay_reference_hand",
]
