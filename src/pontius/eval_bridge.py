"""Slice A export bridge: replayed river root, capacity, per-hand T1, singleton reference.

Everything here works on one hero hand at a time. Production action values are exact
integer net-chip totals from the kernel's own settlement over the 990 compatible villain
hands. The independent reference is the sealed ``LegalHeadsUpRiverContinuation`` for a
single hero hand, evaluated through the sealed evaluators and validated against the
``J/990`` lattice with an exact rational bound before any action is compared. The whole
rule is fixed to the declared ``s = 4`` root; any other root is refused, never adapted.
"""

from __future__ import annotations

from fractions import Fraction
from hashlib import sha256
from itertools import combinations
import json
import math
import random

from .blueprint_artifact.codec import decode_blueprint, encode_blueprint
from .evaluation import best_response, collect_information_sets, expected_utilities
from .game import CHANCE_PLAYER, TERMINAL_PLAYER
from .holdem_cards import DECK, OneSeatCardState
from .immutable_blueprint import (
    BlueprintActionEntry,
    BlueprintDecisionKey,
    ImmutableBlueprintActionSource,
)
from .legal_river_continuation import LegalHeadsUpRiverContinuation
from .no_limit_betting import (
    CALL,
    CHECK,
    FOLD,
    SEAT_COUNT,
    BettingActionKind,
    BettingStreet,
    NoLimitBettingState,
    raise_to,
)
from .river import RiverDeal, evaluate_seven, format_card, parse_cards

CONTROLLED_SEAT = 2
VILLAIN_SEAT = 1
DECLARED_STACK = 4
DECLARED_BET = raise_to(2)
ARTIFACT_CAP = 1_048_576
HERO_COUNT = 1081
VILLAIN_COUNT = 990
UTILITY_LIMIT = 4
REFERENCE_BOUND = Fraction(1, 2**40)
PLACEHOLDER_SOURCE_ID = "t1:" + "0" * 64
# The accepted checked-to prefix under button 0: seats 3, 4, 5, 0 fold for zero chips,
# the small blind completes, the big blind checks, both streets check through, and the
# small blind checks the river. ``None`` advances a street.
PREFIX = (
    (3, FOLD), (4, FOLD), (5, FOLD), (0, FOLD), (1, CALL), (2, CHECK),
    None, (1, CHECK), (2, CHECK),
    None, (1, CHECK), (2, CHECK),
    None, (1, CHECK),
)


def prefix_document():
    """The declared prefix as plain JSON rows, so a plan can bind to it exactly."""
    return [None if step is None else [step[0], step[1].kind.value] for step in PREFIX]


def board_cards(names):
    """Parse a five-card board and refuse anything but ascending library order."""
    board = parse_cards(*names)
    if len(board) != 5 or list(board) != sorted(board):
        raise ValueError("board must be five distinct cards in ascending library order")
    return board


def replay_root(*, stacks=DECLARED_STACK):
    """Replay the accepted prefix through the kernel and return the river root state.

    Other stack depths are permitted here only for labeled negative controls; every
    production and reference entry point re-checks the declared root.
    """
    state = NoLimitBettingState.new_hand(
        button=0, starting_stacks=(stacks,) * SEAT_COUNT, small_blind=1, big_blind=2)
    for step in PREFIX:
        if step is None:
            state = state.advance_street()
            continue
        seat, action = step
        if state.acting_seat != seat:
            raise ValueError("prefix replay drifted from the declared actor order")
        state = state.apply_action(action)
    if state.acting_seat != CONTROLLED_SEAT or state.street is not BettingStreet.RIVER:
        raise ValueError("prefix replay did not reach the controlled river root")
    return state


def require_declared_root(root):
    """Refuse any root but the declared s=4 one; the whole rule is derived for it alone."""
    decision = root.legal_decision()
    bounds = decision.raise_bounds
    declared = (
        root.street is BettingStreet.RIVER
        and root.acting_seat == CONTROLLED_SEAT
        and root.live_seats == (VILLAIN_SEAT, CONTROLLED_SEAT)
        and root.pot == 2 * DECLARED_BET.raise_to
        and root.stacks[VILLAIN_SEAT] == root.stacks[CONTROLLED_SEAT] == DECLARED_BET.raise_to
        and root.starting_stacks == (DECLARED_STACK,) * SEAT_COUNT
        and decision.action_kinds == (BettingActionKind.CHECK, BettingActionKind.RAISE)
        and bounds is not None
        and (bounds.minimum_raise_to, bounds.maximum_raise_to) == (2, 2)
    )
    if not declared:
        raise ValueError("the reference rule is fixed to the declared s=4 river root")
    return root


def bet_action(root):
    """The declared single all-in bet, returned only for the declared root."""
    require_declared_root(root)
    return DECLARED_BET


def hero_hands(board):
    remaining = tuple(card for card in DECK if card not in board)
    return tuple(combinations(remaining, 2))


def villain_hands(board, hero):
    blocked = set(board) | set(hero)
    remaining = tuple(card for card in DECK if card not in blocked)
    return tuple(combinations(remaining, 2))


def hand_name(hand):
    return "".join(format_card(card) for card in hand)


def hand_universe_digest(hands):
    return sha256(json.dumps(sorted(hand_name(hand) for hand in hands)).encode()).hexdigest()


def root_key(root, board, hero):
    cards = OneSeatCardState(
        controlled_seat=CONTROLLED_SEAT, private_hand=hero, street=BettingStreet.RIVER,
        board=board)
    return BlueprintDecisionKey.from_state(
        cards=cards, betting=root, decision=root.legal_decision())


def strength_blind_permutation(hands, seed_hex):
    """A seeded shuffle of the hand universe; the plan carries the ordered contents."""
    order = list(hands)
    random.Random(int(seed_hex, 16)).shuffle(order)
    return tuple(order)


def permutation_digest(permutation):
    return sha256(json.dumps([hand_name(hand) for hand in permutation]).encode()).hexdigest()


def placeholder_artifact(keys, count):
    entries = tuple(BlueprintActionEntry(key, CHECK) for key in keys[:count])
    return encode_blueprint(ImmutableBlueprintActionSource(PLACEHOLDER_SOURCE_ID, entries))


def capacity_probe(root, board, permutation, cap=ARTIFACT_CAP):
    """Largest prefix whose conservative artifact fits the wire cap, with boundary bytes."""
    keys = tuple(root_key(root, board, hero) for hero in permutation)
    encodings = {}

    def encoding(count):
        if count not in encodings:
            encodings[count] = placeholder_artifact(keys, count)
        return encodings[count]

    low, high = 0, len(keys)
    while low < high:  # wire length is strictly increasing in the nested prefix family
        middle = (low + high + 1) // 2
        if len(encoding(middle)) <= cap:
            low = middle
        else:
            high = middle - 1
    largest = low
    decoded = decode_blueprint(encoding(largest))
    if {entry.key for entry in decoded.entries} != set(keys[:largest]):
        raise ValueError("decoded placeholder keys differ from the frozen prefix")
    boundary = {largest: encoding(largest)}
    if largest < len(keys):
        boundary[largest + 1] = encoding(largest + 1)
    return dict(
        cap=cap, hands_total=len(keys), largest_fitting=largest,
        bytes_at_largest=len(boundary[largest]), all_fit=largest == len(keys),
        one_row_failure=largest == 0, placeholder_source_id=PLACEHOLDER_SOURCE_ID,
        bytes_at_next=None if largest == len(keys) else len(boundary[largest + 1]),
        boundary_encodings=boundary,
    )


def _terminal(state):
    if state.round_complete and not state.is_terminal:
        state = state.advance_street()
    if not state.is_terminal:
        raise ValueError("the forced line did not reach a terminal state")
    return state


def hand_totals(root, board, hero):
    """Exact integer net-chip totals for CHECK and the bet against an always-calling villain."""
    bet = bet_action(root)
    check_line = _terminal(root.apply_action(CHECK))
    bet_line = _terminal(root.apply_action(bet).apply_action(CALL))
    hero_strength = evaluate_seven((*board, *hero))
    totals = {CHECK: 0, bet: 0}
    outcomes = dict(wins=0, losses=0, ties=0)
    villains = villain_hands(board, hero)
    for villain in villains:
        strengths = [None] * SEAT_COUNT
        strengths[CONTROLLED_SEAT] = hero_strength
        strengths[VILLAIN_SEAT] = evaluate_seven((*board, *villain))
        for action, line in ((CHECK, check_line), (bet, bet_line)):
            totals[action] += line.settle(strengths).net_returns[CONTROLLED_SEAT]
        if hero_strength > strengths[VILLAIN_SEAT]:
            outcomes["wins"] += 1
        elif hero_strength < strengths[VILLAIN_SEAT]:
            outcomes["losses"] += 1
        else:
            outcomes["ties"] += 1
    action = bet if totals[bet] > totals[CHECK] else CHECK
    work = dict(villain_hands=len(villains), settlements=2 * len(villains),
                ranker_calls=len(villains) + 1)
    return dict(hand=hand_name(hero), check_total=totals[CHECK], bet_total=totals[bet],
                denominator=VILLAIN_COUNT, action=str(action), bet=str(bet), work=work,
                **outcomes)


def build_reference(root, board, hero):
    """The sealed singleton game with an explicit always-CALL villain; refuses a changed domain."""
    bet = bet_action(root)
    deals = tuple((RiverDeal(hero, villain), 1.0) for villain in villain_hands(board, hero))
    game = LegalHeadsUpRiverContinuation(board=board, base_state=root, deals=deals)
    if len(game.deals) != VILLAIN_COUNT or len({weight for _, weight in game.deals}) != 1:
        raise ValueError("the reference rule requires 990 equally weighted villain deals")
    hero_sets = collect_information_sets(game, 0)
    if len(hero_sets) != 1 or tuple(hero_sets.values())[0] != (CHECK, bet):
        raise ValueError("the reference rule requires one hero root with CHECK and raise-to 2")
    villain_sets = collect_information_sets(game, 1)
    if not villain_sets or any(CALL not in actions for actions in villain_sets.values()):
        raise ValueError("every villain information set must admit CALL")
    dealt = game.initial_state().apply_action(game.deals[0][0])
    for line in ((CHECK,), (bet, CALL), (bet, FOLD)):
        state = dealt
        for action in line:
            if state.current_player in (CHANCE_PLAYER, TERMINAL_PLAYER):
                raise ValueError("the reference tree has an unexpected chance or terminal node")
            state = state.apply_action(action)
        returns = state.returns()
        if (state.current_player != TERMINAL_PLAYER or max(map(abs, returns)) > UTILITY_LIMIT
                or any(value != int(value) for value in returns)):
            raise ValueError("forced lines must end at integer terminals of magnitude <= 4")
    hero_key = next(iter(hero_sets))
    villain_policy = {key: {FOLD: 0.0, CALL: 1.0} for key in villain_sets}
    return dict(game=game, hero_key=hero_key, bet=bet, villain_policy=villain_policy)


def forced_value(reference, action):
    """Player-0 value of one forced hero action through the sealed evaluator."""
    hero_policy = {reference["hero_key"]: {CHECK: 0.0, reference["bet"]: 0.0}}
    hero_policy[reference["hero_key"]][action] = 1.0
    policy = dict(reference["villain_policy"], **hero_policy)
    return expected_utilities(reference["game"], policy)[0]


def reference_best_response(reference):
    value, selected = best_response(reference["game"], reference["villain_policy"], 0)
    return value, {key: str(action) for key, action in selected.items()}


def lattice_integer(value, denominator, bound):
    """The unique integer J with |value - J/n| <= bound, or None; exact rational arithmetic."""
    if not isinstance(value, float) or not math.isfinite(value):
        return None
    exact = Fraction(*value.as_integer_ratio())
    nearest = round(exact * denominator)
    candidates = [candidate for candidate in (nearest - 1, nearest, nearest + 1)
                  if abs(exact - Fraction(candidate, denominator)) <= bound]
    limit = UTILITY_LIMIT * denominator
    if len(candidates) != 1 or not -limit <= candidates[0] <= limit:
        return None
    return candidates[0]


def validate_reference(production, values, response_value, response_map, hero_key,
                       bound=REFERENCE_BOUND):
    """Compare production totals with reference values under the accepted lattice rule."""
    denominator = production["denominator"]
    bet = production["bet"]
    validated = {name: lattice_integer(values.get(name), denominator, bound)
                 for name in (str(CHECK), bet)}
    result = dict(bound=str(bound), validated_totals=validated, response_value=response_value,
                  response_map=response_map, classification=None, passed=False, reason=None)
    expected = {str(CHECK): production["check_total"], bet: production["bet_total"]}
    if any(total is None for total in validated.values()):
        result["reason"] = "reference value is not within the bound of a unique lattice integer"
        return result
    if validated != expected:
        result["reason"] = "validated reference totals differ from production totals"
        return result
    maximal = bet if expected[bet] > expected[str(CHECK)] else str(CHECK)
    if production["action"] != maximal:
        result["reason"] = "production action does not maximize the validated totals"
        return result
    best = Fraction(max(expected.values()), denominator)
    if (lattice_integer(response_value, denominator, bound) is None
            or abs(Fraction(*response_value.as_integer_ratio()) - best) > bound):
        result["reason"] = "best_response value is not within the bound of the validated maximum"
        return result
    if set(response_map) != {hero_key} or response_map[hero_key] not in (str(CHECK), bet):
        result["reason"] = "best_response map is not exactly the hero root with a legal action"
        return result
    reference_action = response_map[hero_key]
    if expected[str(CHECK)] != expected[bet]:
        if reference_action != production["action"]:
            result["reason"] = "reference action disagrees on a validated non-tie"
            return result
        result["classification"] = "agree"
    else:
        if production["action"] != str(CHECK):
            result["reason"] = "production must CHECK on a validated exact tie"
            return result
        result["classification"] = ("tie" if reference_action == str(CHECK)
                                    else "tie_reference_broke_differently")
    result["passed"] = True
    return result
