"""Source-only bridge from one legal river decision to the card quotient.

The full-width compiler constructs semantic host metadata only.  It does not
import CuPy and does not execute a quotient forward, adjoint, solver, or action
path.  A separately compiled reduced view exists solely for exact differential
controls against the retained leaf-adjoint terminal consumer.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from fractions import Fraction
from hashlib import sha256
from itertools import combinations
from math import comb, lcm
from pathlib import Path
from typing import Sequence

import numpy as np

from .factor_tt_contraction import FactorTTTopology
from .factorized_belief import FactorizedCardBelief
from .full_width_belief import FullWidthOneSeatBelief
from .full_width_reference_policy import ImmutableFullWidthReferencePolicy
from .gpu_occupied_card_quotient import (
    FrozenQuotientFixture,
    colex_unrank,
)
from .holdem_cards import HoleCards, OneSeatCardState, make_hole, parse_cards
from .legal_decision_spine_v2 import public_betting_state_sha256
from .no_limit_betting import (
    CALL,
    CHECK,
    SEAT_COUNT,
    BettingAction,
    BettingStreet,
    NoLimitBettingState,
    TerminalReason,
)
from .occupied_card_quotient import OccupiedCardQuotientTopology
from .river import evaluate_seven
from .structured_showdown_automaton import (
    StructuredShowdownAutomaton,
    build_structured_showdown_automaton,
)


_ROOT = Path(__file__).parents[2]
_CONFIG = _ROOT / "experiments/configs/legal-river-quotient-bridge-v1.json"
PREREGISTERED_CONFIG_SHA256 = (
    "af145f4d56cdbdcfb5a0d7ee36613677ad79f57620629266c729997785a1f1f6"
)
SOURCE_AXES = (0, 1, 2)
QUERY_AXES = (3, 4, 5)
TARGET_AXIS = 3


def _canonical_lf_sha256(path: Path) -> str:
    return sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def load_preregistered_bridge_config(
    path: Path = _CONFIG,
) -> dict[str, object]:
    """Load only the exact ADR-0385 config."""

    if _canonical_lf_sha256(path) != PREREGISTERED_CONFIG_SHA256:
        raise ValueError("legal river quotient bridge config digest differs")
    parsed = json.loads(path.read_text(encoding="utf-8"))
    if parsed.get("schema_version") != "legal-river-quotient-bridge-config-v1":
        raise ValueError("legal river quotient bridge config schema differs")
    if parsed.get("evidence_stage") != (
        "preregistered_after_adr0384_before_bridge_source_or_reduced_values"
    ):
        raise ValueError("legal river quotient bridge evidence stage differs")
    return parsed


@dataclass(frozen=True, slots=True)
class PreregisteredLegalRiverContext:
    cards: OneSeatCardState
    betting: NoLimitBettingState
    belief: FullWidthOneSeatBelief
    policy_digest: str


@dataclass(frozen=True, slots=True)
class QuotientBridgeOwnership:
    """Typed structural ledgers; byte views count NumPy payloads only.

    Resident and warm-mutable bytes are intentionally nonadditive views: the
    latter identifies the resident buffers eligible for rebinding.  None of
    these fields is a timing or whole-process-memory measurement.
    """

    preparation_work: tuple[tuple[str, int], ...]
    consumer_resident_arrays: tuple[tuple[str, int], ...]
    retained_host_validation_arrays: tuple[tuple[str, int], ...]
    retained_host_validation_entries: tuple[tuple[str, int], ...]
    warm_mutable_arrays: tuple[tuple[str, int], ...]

    @property
    def consumer_resident_numeric_bytes(self) -> int:
        return sum(value for _, value in self.consumer_resident_arrays)

    @property
    def retained_host_validation_numeric_bytes(self) -> int:
        return sum(value for _, value in self.retained_host_validation_arrays)

    @property
    def warm_mutable_numeric_bytes(self) -> int:
        return sum(value for _, value in self.warm_mutable_arrays)


@dataclass(frozen=True, slots=True)
class QuotientWarmInputs:
    belief_digest: str
    topology_digest: str
    automaton_digest: str
    unary_weights: np.ndarray
    mode_factors: np.ndarray


@dataclass(frozen=True, slots=True)
class LegalRiverQuotientBridge:
    """One source-only full-width binding with no quotient output values."""

    cards: OneSeatCardState
    betting: NoLimitBettingState
    terminal_betting: NoLimitBettingState
    belief: FullWidthOneSeatBelief
    policy_digest: str
    axis_table_seats: tuple[int, ...]
    source_axes: tuple[int, ...]
    query_axes: tuple[int, ...]
    target_axis: int
    local_to_physical_cards: tuple[int, ...]
    physical_hands: tuple[HoleCards, ...]
    factorized_belief: FactorizedCardBelief
    fixture: FrozenQuotientFixture
    ownership: QuotientBridgeOwnership
    topology_digest: str
    bridge_digest: str


@dataclass(frozen=True, slots=True)
class ReducedLegalRiverQuotientBridge:
    """Bounded semantic view used only by source controls."""

    parent_bridge_digest: str
    axis_table_seats: tuple[int, ...]
    physical_hands_by_axis: tuple[tuple[HoleCards, ...], ...]
    factorized_belief: FactorizedCardBelief
    automaton: StructuredShowdownAutomaton
    factor_topology: FactorTTTopology
    quotient_topology: OccupiedCardQuotientTopology
    compatible_assignments: tuple[tuple[int, ...], ...]


def _action_from_token(token: str) -> BettingAction:
    if token == "call":
        return CALL
    if token == "check":
        return CHECK
    raise ValueError("ADR-0385 context contains an unsupported action token")


def build_preregistered_legal_river_context(
    path: Path = _CONFIG,
) -> PreregisteredLegalRiverContext:
    """Replay the frozen public prefix and its action-conditioned belief."""

    parsed = load_preregistered_bridge_config(path)
    context = parsed["context"]
    if not isinstance(context, dict):
        raise ValueError("ADR-0385 context is malformed")
    hero = int(context["controlled_seat"])
    cards = OneSeatCardState.preflop(
        controlled_seat=hero,
        private_hand=make_hole(*context["private_hand"]),
    )
    belief = FullWidthOneSeatBelief.uniform(cards)
    policy = ImmutableFullWidthReferencePolicy(str(context["policy_source_id"]))
    betting = NoLimitBettingState.new_hand(
        button=int(context["button"]),
        starting_stacks=tuple(int(value) for value in context["starting_stacks"]),
        small_blind=int(context["small_blind"]),
        big_blind=int(context["big_blind"]),
    )
    likelihood_updates = 0

    def act(action: BettingAction) -> None:
        nonlocal belief, betting, likelihood_updates
        actor = betting.acting_seat
        if actor is None:
            raise AssertionError("ADR-0385 replay lost its acting seat")
        if actor != hero:
            likelihood = policy.likelihood_for_axis(
                visible_cards=cards,
                actor_seat=actor,
                hand_axis=belief.hand_axis,
                betting=betting,
                decision=betting.legal_decision(),
                observed_action=action,
            )
            belief = belief.with_action_likelihood(likelihood)
            likelihood_updates += 1
        betting = betting.apply_action(action)

    actors = tuple(int(value) for value in context["preflop_actors"])
    actions = tuple(_action_from_token(str(value)) for value in context["preflop_actions"])
    if len(actors) != len(actions):
        raise ValueError("ADR-0385 preflop actors and actions differ")
    for expected_actor, action in zip(actors, actions, strict=True):
        if betting.acting_seat != expected_actor:
            raise ValueError("ADR-0385 preflop actor order differs")
        act(action)

    board = parse_cards(*context["board"])
    reveal_by_street = (
        (BettingStreet.FLOP, board[:3]),
        (BettingStreet.TURN, board[3:4]),
        (BettingStreet.RIVER, board[4:5]),
    )
    opponent_order = tuple(
        int(value) for value in context["postflop_opponent_check_order"]
    )
    for street, reveal in reveal_by_street:
        betting = betting.advance_street()
        cards = cards.advance_to(street, reveal)
        belief = belief.advance_to(cards)
        for expected_actor in opponent_order:
            if betting.acting_seat != expected_actor:
                raise ValueError("ADR-0385 postflop actor order differs")
            act(CHECK)
        if street is not BettingStreet.RIVER:
            if betting.acting_seat != hero:
                raise ValueError("ADR-0385 controlled postflop actor differs")
            act(CHECK)

    expected = {
        "card": str(context["expected_card_state_sha256"]),
        "betting": str(context["expected_betting_state_sha256"]),
        "belief": str(context["expected_belief_sha256"]),
        "policy": str(context["expected_policy_sha256"]),
    }
    observed = {
        "card": cards.public_digest,
        "betting": public_betting_state_sha256(betting),
        "belief": belief.digest,
        "policy": policy.digest,
    }
    if observed != expected:
        raise ValueError("ADR-0385 context provenance differs")
    if likelihood_updates != int(context["expected_action_likelihood_updates"]):
        raise ValueError("ADR-0385 likelihood-update count differs")
    return PreregisteredLegalRiverContext(
        cards=cards,
        betting=betting,
        belief=belief,
        policy_digest=policy.digest,
    )


def _readonly(values: object, dtype: object) -> np.ndarray:
    result = np.array(values, dtype=dtype, order="C", copy=True)
    result.flags.writeable = False
    return result


def _card_mask(hand: HoleCards) -> int:
    return (1 << hand[0]) | (1 << hand[1])


def _pairing_template(cards: int, pairs: int) -> tuple[tuple[int, ...], ...]:
    if cards != 2 * pairs or pairs not in (2, 3):
        raise ValueError("bridge pairing templates support only two or three pairs")
    if pairs == 2:
        return tuple(
            (*first, *(card for card in range(cards) if card not in first))
            for first in combinations(range(cards), 2)
        )
    result = []
    for first in combinations(range(cards), 2):
        remaining = tuple(card for card in range(cards) if card not in first)
        for second in combinations(remaining, 2):
            final = tuple(card for card in remaining if card not in second)
            result.append((*first, *second, *final))
    return tuple(result)


def _normalized_axis_weights(
    belief: FullWidthOneSeatBelief,
    table_seat: int,
    hands: tuple[HoleCards, ...],
) -> np.ndarray:
    source = belief.weights_for(table_seat)
    source_by_hand = dict(zip(belief.hand_axis, source, strict=True))
    exact = tuple(source_by_hand[hand].fraction for hand in hands)
    maximum = max(exact)
    if maximum <= 0:
        raise ValueError("bridge opponent axis has no positive range weight")
    values = np.ascontiguousarray(
        [[float(value / maximum) for value in exact]],
        dtype=np.float64,
    )
    if not np.all(np.isfinite(values)) or np.any(values < 0.0):
        raise ArithmeticError("bridge range conversion produced an invalid Float64")
    if any(value > 0 and observed == 0.0 for value, observed in zip(exact, values[0])):
        raise ArithmeticError("bridge positive range weight underflowed")
    return values


def _factorized_axes(
    context: PreregisteredLegalRiverContext,
    axis_table_seats: tuple[int, ...],
    opponent_hands_by_axis: tuple[tuple[HoleCards, ...], ...],
) -> FactorizedCardBelief:
    if len(opponent_hands_by_axis) != 5:
        raise ValueError("bridge requires five opponent hand axes")
    hero = context.cards.controlled_seat
    opponent_cursor = 0
    axes: list[tuple[HoleCards, ...]] = []
    unaries: list[np.ndarray] = []
    for table_seat in axis_table_seats:
        if table_seat == hero:
            axes.append((context.cards.private_hand,))
            unaries.append(np.ones((1, 1), dtype=np.float64))
            continue
        hands = opponent_hands_by_axis[opponent_cursor]
        opponent_cursor += 1
        axes.append(hands)
        unaries.append(_normalized_axis_weights(context.belief, table_seat, hands))
    if opponent_cursor != 5:
        raise AssertionError("bridge opponent-axis cursor drifted")
    return FactorizedCardBelief(
        hands_by_player=tuple(axes),
        mixture_weights=np.ones(1, dtype=np.float64),
        unary_weights=tuple(unaries),
        board=context.cards.board,
    )


def _strength_codes(
    board: tuple[int, ...],
    hands_by_axis: tuple[tuple[HoleCards, ...], ...],
) -> tuple[np.ndarray, ...]:
    ranks = tuple(
        tuple(evaluate_seven((*board, *hand)) for hand in hands)
        for hands in hands_by_axis
    )
    ordered = tuple(sorted({rank for axis in ranks for rank in axis}))
    identifiers = {rank: index for index, rank in enumerate(ordered)}
    return tuple(
        _readonly([identifiers[rank] for rank in axis], np.int32)
        for axis in ranks
    )


def _require_bridge_context(
    context: PreregisteredLegalRiverContext,
    axis_table_seats: tuple[int, ...],
) -> NoLimitBettingState:
    if not isinstance(context.cards, OneSeatCardState):
        raise TypeError("bridge requires semantic one-seat cards")
    if not isinstance(context.betting, NoLimitBettingState):
        raise TypeError("bridge requires the exact betting state")
    if not isinstance(context.belief, FullWidthOneSeatBelief):
        raise TypeError("bridge requires a full-width one-seat belief")
    if context.cards.street is not BettingStreet.RIVER:
        raise ValueError("bridge context must be on the river")
    if context.betting.street is not BettingStreet.RIVER:
        raise ValueError("bridge betting state must be on the river")
    if context.belief.cards != context.cards:
        raise ValueError("bridge belief belongs to a stale card state")
    hero = context.cards.controlled_seat
    if context.betting.acting_seat != hero:
        raise ValueError("bridge controlled seat is not acting")
    if tuple(sorted(axis_table_seats)) != tuple(range(SEAT_COUNT)):
        raise ValueError("bridge table-to-axis mapping is not a permutation")
    if axis_table_seats[TARGET_AXIS] != hero:
        raise ValueError("bridge target is not on the frozen query axis")
    if any(axis == TARGET_AXIS for axis in SOURCE_AXES):
        raise AssertionError("bridge target entered the source half")
    if context.belief.opponent_seats != tuple(
        seat for seat in range(SEAT_COUNT) if seat != hero
    ):
        raise ValueError("bridge belief opponent seats differ from the table")
    expected_axis = context.cards.compatible_opponent_hands()
    if context.belief.hand_axis != expected_axis or len(expected_axis) != 990:
        raise ValueError("bridge requires the complete ordered 990-hand axis")
    decision = context.betting.legal_decision()
    if not decision.can_check:
        raise ValueError("bridge target check is not legal")
    terminal = context.betting.apply_action(CHECK)
    if terminal.terminal_reason is not TerminalReason.SHOWDOWN:
        raise ValueError("bridge target check is not a terminal showdown")
    if terminal.live_seats != tuple(range(SEAT_COUNT)):
        raise ValueError("bridge requires a six-way showdown")
    contributions = terminal.total_contributions
    if len(set(contributions)) != 1:
        raise ValueError("bridge requires equal sunk contributions")
    pots = terminal.side_pots()
    if len(pots) != 1 or pots[0].eligible_seats != tuple(range(SEAT_COUNT)):
        raise ValueError("bridge requires one flat six-way pot")
    divisor = lcm(*range(1, len(terminal.live_seats) + 1))
    if terminal.pot % divisor:
        raise ValueError("bridge flat pot exposes integer odd-chip semantics")
    config = load_preregistered_bridge_config()["context"]
    if not isinstance(config, dict):
        raise ValueError("ADR-0385 context is malformed")
    observed = (
        context.cards.public_digest,
        public_betting_state_sha256(context.betting),
        context.belief.digest,
        context.policy_digest,
    )
    expected = (
        str(config["expected_card_state_sha256"]),
        str(config["expected_betting_state_sha256"]),
        str(config["expected_belief_sha256"]),
        str(config["expected_policy_sha256"]),
    )
    if observed != expected:
        raise ValueError("bridge context differs from frozen ADR-0385 provenance")
    return terminal


def _topology_digest(
    *,
    axis_table_seats: tuple[int, ...],
    local_to_physical: tuple[int, ...],
    fixture: FrozenQuotientFixture,
) -> str:
    digest = sha256()
    digest.update(b"legal-river-quotient-topology-v1")
    digest.update(repr(axis_table_seats).encode("ascii"))
    digest.update(repr(local_to_physical).encode("ascii"))
    digest.update(repr((fixture.available_cards, fixture.hands)).encode("ascii"))
    digest.update(repr((SOURCE_AXES, QUERY_AXES, TARGET_AXIS)).encode("ascii"))
    for values in (
        fixture.pair_to_hand,
        fixture.source_pair_positions,
        fixture.query_masks,
        fixture.query_hand_indices,
        fixture.unary_offsets,
    ):
        digest.update(repr((values.shape, values.dtype.str)).encode("ascii"))
        digest.update(values.tobytes(order="C"))
    return digest.hexdigest()


def _bridge_identity_digest(
    *,
    context: PreregisteredLegalRiverContext,
    axis_table_seats: tuple[int, ...],
    topology_digest: str,
    automaton_digest: str,
) -> str:
    return sha256(
        "|".join(
            (
                "legal-river-quotient-bridge-v1",
                context.cards.public_digest,
                public_betting_state_sha256(context.betting),
                context.belief.digest,
                context.policy_digest,
                repr(axis_table_seats),
                topology_digest,
                automaton_digest,
            )
        ).encode("ascii")
    ).hexdigest()


def compile_legal_river_quotient_bridge(
    context: PreregisteredLegalRiverContext,
    *,
    axis_table_seats: tuple[int, ...] = (1, 2, 3, 0, 4, 5),
) -> LegalRiverQuotientBridge:
    """Compile the full host fixture without evaluating the quotient."""

    terminal = _require_bridge_context(context, axis_table_seats)
    local_to_physical = context.cards.remaining_deck
    if len(local_to_physical) != 45 or len(set(local_to_physical)) != 45:
        raise ValueError("bridge physical/local card map is not a 45-card bijection")
    local_hands = tuple(combinations(range(45), 2))
    physical_hands = tuple(
        (local_to_physical[first], local_to_physical[second])
        for first, second in local_hands
    )
    if physical_hands != context.belief.hand_axis:
        raise ValueError("bridge local hand order differs from the belief axis")

    opponent_axes = (physical_hands,) * 5
    factorized = _factorized_axes(context, axis_table_seats, opponent_axes)
    expected_widths = (990, 990, 990, 1, 990, 990)
    if factorized.hand_counts != expected_widths:
        raise AssertionError("bridge full-width logical axes drifted")
    strengths = _strength_codes(context.cards.board, factorized.hands_by_player)
    automaton = build_structured_showdown_automaton(
        strength_codes=strengths,
        contenders=tuple(range(SEAT_COUNT)),
        target_player=TARGET_AXIS,
        contributed=False,
        pot=float(terminal.pot),
        bet_size=0.0,
    )
    if automaton.transition_mismatches(strengths) != 0:
        raise AssertionError("bridge showdown automaton failed its transition replay")

    offsets = np.asarray((0, 990, 1980, 2970, 2971, 3961), dtype=np.int32)
    unary = _readonly(
        np.concatenate(factorized.unary_weights, axis=1),
        np.float64,
    )
    mode_factors = _readonly(np.ones_like(unary), np.float64)
    pair_to_hand = np.full((45, 45), -1, dtype=np.int32)
    for index, (first, second) in enumerate(local_hands):
        pair_to_hand[first, second] = index
        pair_to_hand[second, first] = index

    query_pairings = _pairing_template(4, 2)
    query_occupancies = comb(45, 4)
    query_records = query_occupancies * len(query_pairings)
    query_masks = np.empty(query_records, dtype=np.uint64)
    query_indices = np.empty((query_records, 2), dtype=np.int32)
    cursor = 0
    for occupancy_rank in range(query_occupancies):
        occupancy = colex_unrank(occupancy_rank, 45, 4)
        mask = sum(1 << card for card in occupancy)
        for pairing in query_pairings:
            first = tuple(sorted((occupancy[pairing[0]], occupancy[pairing[1]])))
            second = tuple(sorted((occupancy[pairing[2]], occupancy[pairing[3]])))
            query_masks[cursor] = mask
            query_indices[cursor] = (
                pair_to_hand[first],
                pair_to_hand[second],
            )
            cursor += 1
    if cursor != 893_970 or np.any(query_indices < 0):
        raise AssertionError("bridge query-label compiler omitted a full-width record")

    fixture = FrozenQuotientFixture(
        available_cards=45,
        hands=local_hands,
        automaton=automaton,
        unary_weights=unary,
        mode_factors=mode_factors,
        mixture_weights=_readonly(factorized.mixture_weights, np.float64),
        pair_to_hand=_readonly(pair_to_hand, np.int32),
        source_pair_positions=_readonly(_pairing_template(6, 3), np.int8),
        query_masks=_readonly(query_masks, np.uint64),
        query_hand_indices=_readonly(query_indices, np.int32),
        unary_offsets=_readonly(offsets, np.int32),
    )
    topology_digest = _topology_digest(
        axis_table_seats=axis_table_seats,
        local_to_physical=local_to_physical,
        fixture=fixture,
    )
    consumer = (
        ("automaton_runtime", automaton.runtime_numeric_bytes),
        ("mixture_weights", fixture.mixture_weights.nbytes),
        ("unary_weights", fixture.unary_weights.nbytes),
        ("mode_factors", fixture.mode_factors.nbytes),
        ("pair_to_hand", fixture.pair_to_hand.nbytes),
        ("source_pairing_template", fixture.source_pair_positions.nbytes),
        ("query_masks", fixture.query_masks.nbytes),
        ("query_hand_indices", fixture.query_hand_indices.nbytes),
        ("unary_offsets", fixture.unary_offsets.nbytes),
    )
    validation = (
        ("automaton_bond_state_metadata", automaton.state_metadata_bytes),
        ("factorized_belief_persistent", factorized.persistent_numeric_bytes),
    )
    ownership = QuotientBridgeOwnership(
        preparation_work=(
            ("physical_to_local_card_entries", 45),
            ("pair_to_hand_writes", 2 * 990),
            ("source_pairing_template_entries", 90 * 6),
            ("query_occupancy_visits", 148_995),
            ("labeled_query_records_generated", 893_970),
            ("strength_evaluations", 5 * 990 + 1),
        ),
        consumer_resident_arrays=consumer,
        retained_host_validation_arrays=validation,
        retained_host_validation_entries=(
            ("local_to_physical_card_entries", len(local_to_physical)),
            ("physical_hand_records", len(physical_hands)),
        ),
        warm_mutable_arrays=(
            ("unary_weights", fixture.unary_weights.nbytes),
            ("mode_factors", fixture.mode_factors.nbytes),
        ),
    )
    digest = _bridge_identity_digest(
        context=context,
        axis_table_seats=axis_table_seats,
        topology_digest=topology_digest,
        automaton_digest=automaton.digest,
    )
    return LegalRiverQuotientBridge(
        cards=context.cards,
        betting=context.betting,
        terminal_betting=terminal,
        belief=context.belief,
        policy_digest=context.policy_digest,
        axis_table_seats=axis_table_seats,
        source_axes=SOURCE_AXES,
        query_axes=QUERY_AXES,
        target_axis=TARGET_AXIS,
        local_to_physical_cards=local_to_physical,
        physical_hands=physical_hands,
        factorized_belief=factorized,
        fixture=fixture,
        ownership=ownership,
        topology_digest=topology_digest,
        bridge_digest=digest,
    )


def _require_compiled_bridge_integrity(
    bridge: LegalRiverQuotientBridge,
) -> None:
    if (
        bridge.source_axes != SOURCE_AXES
        or bridge.query_axes != QUERY_AXES
        or bridge.target_axis != TARGET_AXIS
    ):
        raise ValueError("warm bridge source/query topology differs")
    context = PreregisteredLegalRiverContext(
        cards=bridge.cards,
        betting=bridge.betting,
        belief=bridge.belief,
        policy_digest=bridge.policy_digest,
    )
    terminal = _require_bridge_context(context, bridge.axis_table_seats)
    if terminal != bridge.terminal_betting:
        raise ValueError("warm bridge terminal semantics differ")

    local_to_physical = bridge.cards.remaining_deck
    local_hands = tuple(combinations(range(45), 2))
    physical_hands = tuple(
        (local_to_physical[first], local_to_physical[second])
        for first, second in local_hands
    )
    if (
        bridge.local_to_physical_cards != local_to_physical
        or bridge.physical_hands != physical_hands
    ):
        raise ValueError("warm bridge card topology differs")
    if bridge.fixture.available_cards != 45 or bridge.fixture.hands != local_hands:
        raise ValueError("warm bridge quotient hand topology differs")

    expected_factorized = _factorized_axes(
        context,
        bridge.axis_table_seats,
        (physical_hands,) * 5,
    )
    if bridge.factorized_belief.hands_by_player != expected_factorized.hands_by_player:
        raise ValueError("warm bridge factorized hand topology differs")
    if not np.array_equal(
        bridge.factorized_belief.mixture_weights,
        expected_factorized.mixture_weights,
    ) or any(
        not np.array_equal(observed, expected)
        for observed, expected in zip(
            bridge.factorized_belief.unary_weights,
            expected_factorized.unary_weights,
            strict=True,
        )
    ):
        raise ValueError("warm bridge retained belief factors differ")

    expected_unary = np.concatenate(expected_factorized.unary_weights, axis=1)
    fixture = bridge.fixture
    if not np.array_equal(fixture.unary_weights, expected_unary):
        raise ValueError("warm bridge retained unary factors differ")
    if not np.array_equal(fixture.mode_factors, np.ones_like(expected_unary)):
        raise ValueError("warm bridge retained mode factors differ")
    if not np.array_equal(fixture.mixture_weights, expected_factorized.mixture_weights):
        raise ValueError("warm bridge retained mixture differs")
    if (
        fixture.automaton.shape != expected_factorized.hand_counts
        or fixture.automaton.target_player != TARGET_AXIS
        or fixture.automaton.contenders != tuple(range(SEAT_COUNT))
        or fixture.automaton.final_pot != float(terminal.pot)
        or fixture.automaton.sunk_value != -float(terminal.total_contributions[0])
    ):
        raise ValueError("warm bridge automaton semantics differ")

    topology_digest = _topology_digest(
        axis_table_seats=bridge.axis_table_seats,
        local_to_physical=local_to_physical,
        fixture=fixture,
    )
    if topology_digest != bridge.topology_digest:
        raise ValueError("warm bridge topology digest differs")
    identity = _bridge_identity_digest(
        context=context,
        axis_table_seats=bridge.axis_table_seats,
        topology_digest=topology_digest,
        automaton_digest=fixture.automaton.digest,
    )
    if identity != bridge.bridge_digest:
        raise ValueError("warm bridge automaton identity differs")


def compile_warm_inputs(
    bridge: LegalRiverQuotientBridge,
    belief: FullWidthOneSeatBelief,
    *,
    mode_factors_by_axis: Sequence[Sequence[float]] | None = None,
) -> QuotientWarmInputs:
    """Rebind only range/path factors while preserving semantic topology."""

    if not isinstance(bridge, LegalRiverQuotientBridge):
        raise TypeError("warm bridge input requires a compiled bridge")
    _require_compiled_bridge_integrity(bridge)
    if not isinstance(belief, FullWidthOneSeatBelief):
        raise TypeError("warm bridge input requires a full-width belief")
    if belief.cards != bridge.cards:
        raise ValueError("warm belief belongs to a stale card state")
    if belief.hand_axis != bridge.physical_hands:
        raise ValueError("warm belief changes the full-width topology")
    context = PreregisteredLegalRiverContext(
        cards=bridge.cards,
        betting=bridge.betting,
        belief=belief,
        policy_digest=bridge.policy_digest,
    )
    factorized = _factorized_axes(
        context,
        bridge.axis_table_seats,
        (bridge.physical_hands,) * 5,
    )
    unary = _readonly(
        np.concatenate(factorized.unary_weights, axis=1),
        np.float64,
    )
    if mode_factors_by_axis is None:
        factors = np.ones_like(unary)
    else:
        if len(mode_factors_by_axis) != SEAT_COUNT:
            raise ValueError("warm mode factors require one vector per logical axis")
        rows = []
        for axis, (values, width) in enumerate(
            zip(mode_factors_by_axis, factorized.hand_counts, strict=True)
        ):
            row = np.ascontiguousarray(values, dtype=np.float64)
            if row.shape != (width,):
                raise ValueError(f"warm mode-factor axis {axis} has the wrong width")
            if not np.all(np.isfinite(row)) or np.any(row < 0.0):
                raise ValueError("warm mode factors must be finite and nonnegative")
            rows.append(row)
        factors = np.concatenate(rows, axis=0)[None, :]
    factors = _readonly(factors, np.float64)
    if unary.shape != bridge.fixture.unary_weights.shape:
        raise AssertionError("warm unary shape changed the bridge topology")
    if factors.shape != bridge.fixture.mode_factors.shape:
        raise AssertionError("warm mode-factor shape changed the bridge topology")
    return QuotientWarmInputs(
        belief_digest=belief.digest,
        topology_digest=bridge.topology_digest,
        automaton_digest=bridge.fixture.automaton.digest,
        unary_weights=unary,
        mode_factors=factors,
    )


def _physical_reduced_hands(
    bridge: LegalRiverQuotientBridge,
    local_axes: Sequence[Sequence[Sequence[int]]],
) -> tuple[tuple[HoleCards, ...], ...]:
    if len(local_axes) != 5:
        raise ValueError("reduced bridge requires five opponent axes")
    result = []
    for axis in local_axes:
        hands = []
        for supplied in axis:
            if len(supplied) != 2:
                raise ValueError("reduced bridge hand must contain two local cards")
            first, second = (int(value) for value in supplied)
            if first == second or first not in range(45) or second not in range(45):
                raise ValueError("reduced bridge hand contains an invalid local card")
            hand = tuple(
                sorted(
                    (
                        bridge.local_to_physical_cards[first],
                        bridge.local_to_physical_cards[second],
                    )
                )
            )
            hands.append(hand)
        canonical = tuple(hands)
        if not canonical or len(set(canonical)) != len(canonical):
            raise ValueError("reduced bridge axes must be nonempty and unique")
        result.append(canonical)
    return tuple(result)


def compile_reduced_legal_river_quotient_bridge(
    bridge: LegalRiverQuotientBridge,
    local_opponent_hands_by_axis: Sequence[Sequence[Sequence[int]]],
) -> ReducedLegalRiverQuotientBridge:
    """Compile the ADR-0385 bounded differential view without solving it."""

    reduced_axes = _physical_reduced_hands(
        bridge,
        local_opponent_hands_by_axis,
    )
    context = PreregisteredLegalRiverContext(
        cards=bridge.cards,
        betting=bridge.betting,
        belief=bridge.belief,
        policy_digest=bridge.policy_digest,
    )
    factorized = _factorized_axes(context, bridge.axis_table_seats, reduced_axes)
    if factorized.hand_counts != (4, 4, 4, 1, 4, 4):
        raise ValueError("reduced bridge axes differ from frozen h4 widths")
    strengths = _strength_codes(bridge.cards.board, factorized.hands_by_player)
    automaton = build_structured_showdown_automaton(
        strength_codes=strengths,
        contenders=tuple(range(SEAT_COUNT)),
        target_player=TARGET_AXIS,
        contributed=False,
        pot=float(bridge.terminal_betting.pot),
        bet_size=0.0,
    )
    if automaton.transition_mismatches(strengths) != 0:
        raise AssertionError("reduced bridge automaton failed transition replay")
    factor_topology = FactorTTTopology.compile(factorized, split_index=3)
    hero_mask = _card_mask(bridge.cards.private_hand)
    quotient = OccupiedCardQuotientTopology.compile(
        source_seats=SOURCE_AXES,
        query_seats=QUERY_AXES,
        open_seats=(TARGET_AXIS,),
        source_record_masks=tuple(int(value) for value in factor_topology.left.masks),
        query_record_masks=tuple(int(value) for value in factor_topology.right.masks),
        query_fixed_mask=hero_mask,
    )
    materialized = factorized.materialize()
    assignments = materialized.assignments
    support = tuple(
        {
            assignment[axis]
            for assignment in assignments
        }
        for axis in range(SEAT_COUNT)
    )
    if any(len(values) != factorized.hand_counts[axis] for axis, values in enumerate(support)):
        raise ValueError("reduced bridge contains an unsupported private hand")
    return ReducedLegalRiverQuotientBridge(
        parent_bridge_digest=bridge.bridge_digest,
        axis_table_seats=bridge.axis_table_seats,
        physical_hands_by_axis=factorized.hands_by_player,
        factorized_belief=factorized,
        automaton=automaton,
        factor_topology=factor_topology,
        quotient_topology=quotient,
        compatible_assignments=assignments,
    )


def exact_float_rows(values: np.ndarray) -> tuple[tuple[Fraction, ...], ...]:
    """Expose the exact binary-rational rows used by reduced controls."""

    rows = np.ascontiguousarray(values, dtype=np.float64)
    if rows.ndim != 2 or not np.all(np.isfinite(rows)):
        raise ValueError("exact bridge rows must be a finite matrix")
    return tuple(
        tuple(Fraction(float(value)) for value in row)
        for row in rows
    )


__all__ = [
    "LegalRiverQuotientBridge",
    "PREREGISTERED_CONFIG_SHA256",
    "PreregisteredLegalRiverContext",
    "QUERY_AXES",
    "QuotientBridgeOwnership",
    "QuotientWarmInputs",
    "ReducedLegalRiverQuotientBridge",
    "SOURCE_AXES",
    "TARGET_AXIS",
    "build_preregistered_legal_river_context",
    "compile_legal_river_quotient_bridge",
    "compile_reduced_legal_river_quotient_bridge",
    "compile_warm_inputs",
    "exact_float_rows",
    "load_preregistered_bridge_config",
]
