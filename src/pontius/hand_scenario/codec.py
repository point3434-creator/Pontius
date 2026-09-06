"""Closed JSON admission for one declared, non-evidentiary correctness hand."""
from __future__ import annotations

from dataclasses import dataclass
import json

from pontius.v0a.replay import Fixture, ScriptedAction, permutation_for_label

LIMIT = 10**640
RANKS, SUITS = '23456789TJQKA', 'cdhs'
STREETS = ('preflop', 'flop', 'turn', 'river')


class ScenarioError(ValueError):
    """The complete scenario was refused before host construction."""


@dataclass(frozen=True, slots=True)
class HandScenario:
    fixture: Fixture
    expected_actions: tuple[tuple[str, str, int | None, str], ...]


def require(condition, reason):
    if not condition:
        raise ScenarioError(reason)


def obj(value, fields):
    require(type(value) is dict and set(value) == set(fields.split()),
            'object has wrong type, missing or unknown members')
    return value


def array(value, width=None):
    require(type(value) is list and (width is None or len(value) == width),
            'array has wrong type or width')
    return value


def integer(value, lower=0, upper=LIMIT):
    require(type(value) is int and lower <= value < upper, 'integer outside exact range')
    return value


def integers(value, width=None, lower=0, upper=LIMIT):
    return tuple(integer(item, lower, upper) for item in array(value, width))


def action(row):
    require(row['street'] in STREETS, 'unknown street')
    require(row['kind'] in ('fold', 'check', 'call', 'raise'), 'unknown action')
    if row['kind'] == 'raise':
        integer(row['raise_to'], 1)
    else:
        require(row['raise_to'] is None, 'non-raise requires null raise_to')
    return row['street'], row['kind'], row['raise_to']


def pairs(items):
    result = {}
    for key, value in items:
        require(key not in result, 'duplicate JSON member')
        result[key] = value
    return result


def parse_integer(token):
    require(len(token.removeprefix('-')) <= 640, 'integer exceeds 640 decimal digits')
    return int(token)


def reject_number(token):
    raise ScenarioError('floating-point and nonfinite numbers are not admitted')


def admit(data):
    obj(data, 'version case_id button controlled_seat starting_stacks small_blind '
              'big_blind board hands opponent_actions expected')
    require(data['version'] == 'pontius-v0a-hand-scenario-v1', 'unsupported version')
    name = data['case_id']
    prefix = 'v0a-hand-adapter-correctness-'
    require(type(name) is str and name.startswith(prefix) and len(name) > len(prefix)
            and all(c.isascii() and (c.isalnum() or c in '_-') for c in name[len(prefix):]),
            'case_id requires the correctness namespace and ASCII suffix')
    button, seat = (integer(data[field], 0, 6) for field in ('button', 'controlled_seat'))
    small, big = (integer(data[field], 1) for field in ('small_blind', 'big_blind'))
    require(small < big, 'small blind must be smaller than big blind')
    stacks = integers(data['starting_stacks'], 6, big)
    total = integer(sum(stacks), 1)
    board = array(data['board'], 5)
    hands = [array(hand, 2) for hand in array(data['hands'], 6)]
    cards = board + [card for hand in hands for card in hand]
    require(all(type(c) is str and len(c) == 2 and c[0] in RANKS and c[1] in SUITS
                for c in cards), 'cards require exact ASCII rank/suit pairs')
    require(len(set(cards)) == 17, 'all seventeen cards must be distinct')
    script = []
    for row in array(data['opponent_actions']):
        obj(row, 'street seat kind raise_to')
        actor = integer(row['seat'], 0, 6)
        require(actor != seat, 'script cannot act for the controlled seat')
        street, kind, amount = action(row)
        script.append(ScriptedAction(street, actor, kind, amount))
    expected = obj(data['expected'], 'payouts pots controlled_actions')
    payouts = integers(expected['payouts'], 6, 0, total + 1)
    pots = integers(expected['pots'], lower=1, upper=total + 1)
    require(pots and sum(pots) <= total, 'pots must be nonempty and within starting total')
    actions = []
    for row in array(expected['controlled_actions']):
        obj(row, 'street kind raise_to selection_reason')
        require(row['selection_reason'] in ('table_hit', 'passive_default'), 'unknown reason')
        actions.append((*action(row), row['selection_reason']))
    label = 'pontius-v0a-hand-adapter-v1/' + name
    inverse = dict(zip(permutation_for_label(label), SUITS))
    def template(card):
        return card[0] + inverse[card[1]]
    fixture = Fixture(name=name, seed_label=label, hand_id=name, button=button,
        controlled_seat=seat, starting_stacks=stacks, small_blind=small, big_blind=big,
        board_text=tuple(template(card) for card in board),
        hand_text=tuple(' '.join(template(card) for card in hand) for hand in hands),
        script=tuple(script), expected_payouts=payouts, expected_pots=pots,
        expected_controlled_actions=len(actions))
    def numeric(card):
        return RANKS.index(card[0]) * 4 + SUITS.index(card[1])
    deal = fixture.deal()
    require(deal.board_runout == tuple(numeric(card) for card in board)
            and all(tuple(deal.hand(s)) == tuple(sorted(numeric(c) for c in hand))
                    for s, hand in enumerate(hands)), 'fixture changed the literal deal')
    return HandScenario(fixture, tuple(actions))


def decode_scenario(raw: bytes) -> HandScenario:
    """Admit immutable bytes only; do not execute a host or repair expectations."""
    require(type(raw) is bytes, 'scenario must be exact bytes')
    require(not raw.startswith(b'\xef\xbb\xbf'), 'UTF-8 BOM is not admitted')
    try:
        return admit(json.loads(raw.decode('utf-8'), object_pairs_hook=pairs,
                     parse_int=parse_integer, parse_float=reject_number,
                     parse_constant=reject_number))
    except ScenarioError:
        raise
    except (UnicodeError, ValueError, TypeError, RecursionError, OverflowError) as error:
        raise ScenarioError('malformed scenario encoding, structure or scalar') from error
