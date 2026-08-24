"""Unopened legal h4 selector-map fixture construction.

Only already-retained ADR-0346/0349 public semantics and source policy are
reconstructed here.  This module contains no response selector or solver.
"""

from __future__ import annotations

import hashlib

from .evaluation import Policy, collect_information_sets
from .legal_river_continuation import LegalHeadsUpRiverContinuation
from .no_limit_betting import (
    CALL,
    CHECK,
    FOLD,
    BettingStreet,
    NoLimitBettingState,
)
from .river import RiverDeal, make_hole, parse_cards


BOARD = ("2c", "7d", "9h", "Js", "Qc")
ROOT_HANDS = (("As", "Ad"), ("Kh", "Kd"), ("8s", "8d"), ("6s", "5s"))
RESPONDER_HANDS = (("Ts", "8h"), ("Qs", "Qd"), ("9s", "9d"), ("Ac", "Kc"))
JOINT_WEIGHT_NUMERATORS = (
    (1, 2, 1, 4),
    (2, 1, 3, 1),
    (1, 3, 1, 2),
    (4, 1, 2, 3),
)
JOINT_WEIGHT_DENOMINATOR = 32


def checked_to_river() -> NoLimitBettingState:
    state = NoLimitBettingState.new_hand(
        button=0,
        starting_stacks=(6,) * 6,
        small_blind=1,
        big_blind=2,
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
            raise AssertionError("legal h4 selector preflop order drifted")
        state = state.apply_action(action)
    for street in (BettingStreet.FLOP, BettingStreet.TURN, BettingStreet.RIVER):
        state = state.advance_street()
        if state.street is not street:
            raise AssertionError("legal h4 selector street order drifted")
        if street is not BettingStreet.RIVER:
            state = state.apply_action(CHECK).apply_action(CHECK)
    if state.acting_seat != 1:
        raise AssertionError("legal h4 selector first river actor drifted")
    return state.apply_action(CHECK)


def build_legal_h4_selector_game() -> LegalHeadsUpRiverContinuation:
    deals = tuple(
        (
            RiverDeal(make_hole(*root), make_hole(*responder)),
            float(JOINT_WEIGHT_NUMERATORS[root_index][responder_index]),
        )
        for root_index, root in enumerate(ROOT_HANDS)
        for responder_index, responder in enumerate(RESPONDER_HANDS)
    )
    return LegalHeadsUpRiverContinuation(
        board=parse_cards(*BOARD),
        base_state=checked_to_river(),
        deals=deals,
    )


def _rotated(values: tuple[float, ...], offset: int) -> tuple[float, ...]:
    index = offset % len(values)
    return (*values[index:], *values[:index])


def legal_h4_source_policy(game: LegalHeadsUpRiverContinuation) -> Policy:
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
                raise ValueError(
                    "legal h4 selector source found an unexpected action width"
                ) from exc
            digest = hashlib.sha256(
                f"adr0346|player={player}|{key}".encode("utf-8")
            ).digest()
            probabilities = _rotated(template, int.from_bytes(digest[:2], "big"))
            policy[key] = dict(zip(actions, probabilities, strict=True))
    return policy


__all__ = [
    "BOARD",
    "JOINT_WEIGHT_DENOMINATOR",
    "JOINT_WEIGHT_NUMERATORS",
    "RESPONDER_HANDS",
    "ROOT_HANDS",
    "build_legal_h4_selector_game",
    "checked_to_river",
    "legal_h4_source_policy",
]
