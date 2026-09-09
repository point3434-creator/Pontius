"""Slice A export bridge: replayed river root, capacity, per-hand T1, singleton reference.

Teacher computation works on one hero hand at a time. Production action values are exact
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
from .blueprint_preparation.lookup import PreparedBlueprint
from .decision_provider.model import DecisionObservation
from .decision_provider.providers import BlueprintProvider
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


def _teacher_json(document):
    return json.dumps(document, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("ascii")


def _teacher_domain():
    return dict(version="pontius-river-teacher-v1", prefix=prefix_document(),
                root=dict(button=0, starting_stacks=[DECLARED_STACK] * SEAT_COUNT,
                          small_blind=1, big_blind=2, controlled_seat=CONTROLLED_SEAT),
                opponent=dict(seat=VILLAIN_SEAT, response="always_call",
                              range="uniform_compatible_hands", denominator=VILLAIN_COUNT))


def _teacher_validate(document):
    """Validate declared row consistency, not the truth of an unevaluated poker policy."""
    domain = _teacher_domain()
    if type(document) is not dict or set(document) != set(domain) | {
            "board", "permutation", "hands", "rows"}:
        raise ValueError("teacher has missing or unknown fields")
    if any(_teacher_json(document[name]) != _teacher_json(value)
           for name, value in domain.items()):
        raise ValueError("teacher differs from the fixed root, prefix or opponent law")
    if type(document["board"]) is not list or any(
            type(name) is not str for name in document["board"]):
        raise ValueError("teacher board must contain canonical card names")
    board = board_cards(document["board"])
    if document["board"] != [format_card(card) for card in board]:
        raise ValueError("teacher board names must use canonical rank and suit spelling")
    universe = {hand_name(hand): hand for hand in hero_hands(board)}
    permutation, hands, rows = (document[name] for name in ("permutation", "hands", "rows"))
    if any(type(value) is not list for value in (permutation, hands, rows)):
        raise ValueError("teacher permutation, hands and rows must be arrays")
    if (len(permutation) != HERO_COUNT or any(type(name) is not str for name in permutation)
            or set(permutation) != set(universe)):
        raise ValueError("teacher permutation must cover the complete distinct hand universe")
    if not hands or hands != permutation[:len(hands)] or len(rows) != len(hands):
        raise ValueError("teacher H and rows must cover a nonempty exact permutation prefix")
    actions = {}
    core = {"hand", "check_total", "bet_total", "denominator", "action", "bet"}
    outcomes = {"wins", "losses", "ties"}
    for name, row in zip(hands, rows):
        if type(row) is not dict or not core <= set(row) or set(row) - core - outcomes - {"work"}:
            raise ValueError("teacher row has missing or unknown fields")
        if row["hand"] != name or type(row["hand"]) is not str:
            raise ValueError("teacher rows must cover H exactly in order")
        if any(type(row[field]) is not int for field in
               ("check_total", "bet_total", "denominator")):
            raise ValueError("teacher totals and denominator must be exact integers")
        check, bet = row["check_total"], row["bet_total"]
        if (row["denominator"] != VILLAIN_COUNT or abs(check) > 2 * VILLAIN_COUNT
                or check % 2 or bet != 2 * check):
            raise ValueError("teacher totals violate the declared s=4 settlement domain")
        action = DECLARED_BET if bet > check else CHECK
        if (type(row["action"]) is not str or row["action"] != str(action)
                or type(row["bet"]) is not str or row["bet"] != str(DECLARED_BET)):
            raise ValueError("teacher action must maximize totals with CHECK first on a tie")
        if outcomes & set(row):
            if not outcomes <= set(row) or any(type(row[field]) is not int or row[field] < 0
                                               for field in outcomes):
                raise ValueError("teacher outcome counts must be complete nonnegative integers")
            if (sum(row[field] for field in outcomes) != VILLAIN_COUNT
                    or check != 2 * (row["wins"] - row["losses"])):
                raise ValueError("teacher outcome counts and supplied totals disagree")
        if "work" in row:
            expected_work = dict(villain_hands=VILLAIN_COUNT, settlements=2 * VILLAIN_COUNT,
                                 ranker_calls=VILLAIN_COUNT + 1)
            if _teacher_json(row["work"]) != _teacher_json(expected_work):
                raise ValueError("teacher work metadata differs from per-hand enumeration")
        actions[name] = action
    return board, tuple(universe[name] for name in hands), actions


def teacher_bytes(board, permutation, rows):
    """Freeze supplied per-hand rows and H as canonical ASCII JSON; never solve a hand.

    The complete strength-blind permutation is bound along with its nonempty solved
    prefix. Core row fields are mandatory; outcome counts and work may be omitted,
    but supplied metadata must exactly match the current hand_totals schema.
    """
    if (type(board) is not tuple or len(board) != 5
            or any(type(card) is not int or card not in DECK for card in board)):
        raise ValueError("teacher board must be a tuple of five exact card integers")
    if type(permutation) not in (tuple, list) or any(
            type(hand) is not tuple or len(hand) != 2
            or any(type(card) is not int or card not in DECK for card in hand)
            for hand in permutation):
        raise ValueError("teacher permutation must contain exact two-card tuples")
    if type(rows) not in (tuple, list) or any(type(row) is not dict for row in rows):
        raise ValueError("teacher rows must be a sequence of exact dictionaries")
    document = dict(_teacher_domain(), board=[format_card(card) for card in board],
                    permutation=[hand_name(hand) for hand in permutation],
                    hands=[row.get("hand") for row in rows], rows=list(rows))
    _teacher_validate(document)
    return _teacher_json(document)


def teacher_actions(raw):
    """Read only canonical immutable teacher bytes, including duplicate-key refusal."""
    if type(raw) is not bytes:
        raise TypeError("teacher input must be immutable bytes")
    document = json.loads(raw)
    # Equality also refuses duplicate keys, whitespace, NaN, and alternate spellings.
    if _teacher_json(document) != raw:
        raise ValueError("teacher input must use the declared canonical JSON serialization")
    return _teacher_validate(document)


def _teacher_entries(raw):
    board, hands, actions = teacher_actions(raw)
    root = require_declared_root(replay_root())
    # Traverse the legal continuation shape: no second hero decision is reachable.
    _terminal(root.apply_action(CHECK))
    response = root.apply_action(DECLARED_BET)
    if (response.acting_seat != VILLAIN_SEAT
            or response.legal_decision().action_kinds != (BettingActionKind.FOLD,
                                                         BettingActionKind.CALL)):
        raise ValueError("teacher root does not have the declared singleton decision shape")
    for action in (CALL, FOLD):
        _terminal(response.apply_action(action))
    entries = tuple(BlueprintActionEntry(root_key(root, board, hand), actions[hand_name(hand)])
                    for hand in hands)
    return board, hands, actions, root, entries


def export_teacher(raw, cap=ARTIFACT_CAP):
    """Encode supplied teacher policy only; validate actual wire size and full decoded rows."""
    if type(cap) is not int or cap <= 0 or cap > ARTIFACT_CAP:
        raise ValueError("artifact cap must be a positive integer no larger than ARTIFACT_CAP")
    _, hands, _, _, entries = _teacher_entries(raw)
    teacher_digest = sha256(raw).hexdigest()
    source = ImmutableBlueprintActionSource("t1:" + teacher_digest, entries)
    wire = encode_blueprint(source)
    if len(wire) > cap:
        raise ValueError("actual encoded teacher artifact exceeds the declared wire cap")
    decoded = decode_blueprint(wire)
    expected = {entry.key: entry.action for entry in entries}
    actual = {entry.key: entry.action for entry in decoded.entries}
    if (decoded.source_id != source.source_id or len(decoded.entries) != len(entries)
            or actual != expected):
        raise ValueError("decoded artifact differs from the complete teacher key/action map")
    return wire, dict(passed=True, teacher_sha256=teacher_digest, source_id=source.source_id,
                      source_sha256=decoded.digest, wire_sha256=sha256(wire).hexdigest(),
                      wire_bytes=len(wire), cap=cap, hands_count=len(hands),
                      keys_equal=True, actions_equal=True)


def validate_membership(raw, wire):
    """Exhaustive library/provider root check, separate from any host agreement claim."""
    board, hands, actions, root, entries = _teacher_entries(raw)
    source = decode_blueprint(wire)
    expected = {entry.key: entry.action for entry in entries}
    actual = {entry.key: entry.action for entry in source.entries}
    exact = (source.source_id == "t1:" + sha256(raw).hexdigest()
             and len(source.entries) == len(entries) and actual == expected)
    prepared, provider = PreparedBlueprint(source), BlueprintProvider(source)
    rows, hits, unsupported, disagreements = [], 0, 0, 0
    decision = root.legal_decision()
    for index, hand in enumerate(hero_hands(board), 1):
        name = hand_name(hand)
        cards = OneSeatCardState(controlled_seat=CONTROLLED_SEAT, private_hand=hand,
                                 street=BettingStreet.RIVER, board=board)
        selection = prepared.action_for(cards=cards, betting=root, decision=decision)
        observation = DecisionObservation("pontius-decision-observation-v1", "membership",
                                          index, cards, root, decision, 14_000_000_000)
        proposal = provider.propose(observation)
        in_pool, wanted = name in actions, actions.get(name, CHECK)
        reason = "blueprint_hit" if in_pool else "blueprint_default"
        passed = (selection.key == root_key(root, board, hand)
                  and selection.table_hit == in_pool and selection.action == wanted
                  and proposal.reason == reason and proposal.action == wanted
                  and proposal.decision_sha256 == observation.decision_sha256)
        classification = ("hit" if in_pool else "unsupported") if passed else "disagreement"
        hits += classification == "hit"
        unsupported += classification == "unsupported"
        disagreements += not passed
        rows.append(dict(hand=name, in_pool=in_pool, table_hit=selection.table_hit,
                         prepared_action=str(selection.action),
                         provider_action=str(proposal.action),
                         provider_reason=proposal.reason, classification=classification))
    return dict(passed=exact and disagreements == 0, scope="exhaustive_library_provider_root",
                teacher_sha256=sha256(raw).hexdigest(), wire_sha256=sha256(wire).hexdigest(),
                exact_entries=exact, universe_count=len(rows), hands_count=len(hands),
                hits=hits, unsupported=unsupported, disagreements=disagreements, rows=rows)


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
