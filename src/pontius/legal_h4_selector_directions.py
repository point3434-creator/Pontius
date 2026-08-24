"""Selector-map directions with real downstream customers on the legal h4 tree.

The compiler is deliberately selector-free.  It produces three per-public-
block regret vertices using the established one-step DCFR rule and reconstructs
the retained restricted-master proposal from ADR-0349's exact initial rows.
It never asks for a best response or opens a selector value.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Mapping

from .cfr import TabularCFR
from .evaluation import Policy, collect_information_sets
from .game import Action, ExtensiveFormGame
from .one_seat_convex_generation import (
    AffinePayoff,
    ResponseSignature,
    _ResponseRow,
    _master,
    _sequence_axis,
)


@dataclass(frozen=True, slots=True)
class LegalH4SelectorDirection:
    """One frozen source-to-endpoint direction for a selector fan section."""

    label: str
    direction_class: str
    changed_public_histories: tuple[str, ...]
    endpoint_policy_sha256: str
    endpoint_policy: Policy


def _action_token(action: object) -> str:
    return str(action)


def policy_sha256(policy: Mapping[str, Mapping[Action, float]]) -> str:
    payload = [
        {
            "information_key": key,
            "actions": [
                {
                    "action": _action_token(action),
                    "probability_hex": float(probability).hex(),
                }
                for action, probability in sorted(
                    policy[key].items(), key=lambda item: _action_token(item[0])
                )
            ],
        }
        for key in sorted(policy)
    ]
    rendered = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(rendered.encode("ascii")).hexdigest()


def _history(key: str) -> str:
    try:
        return key.rsplit("|history=", 1)[1]
    except IndexError as exc:
        raise ValueError("legal h4 information key has no public history") from exc


def _clone(policy: Mapping[str, Mapping[Action, float]]) -> Policy:
    return {key: dict(row) for key, row in policy.items()}


def _regret_vertex_directions(
    game: ExtensiveFormGame,
    source: Policy,
    *,
    acting_player: int,
) -> tuple[LegalH4SelectorDirection, ...]:
    solver = TabularCFR(game, variant="dcfr")
    warm_mass = 1.0
    solver.warm_start(source, warm_mass)
    solver.step()
    postdiscount = {
        key: dict(data.regrets) for key, data in solver.information_sets.items()
    }
    acting_sets = collect_information_sets(game, acting_player)
    histories = tuple(sorted({_history(key) for key in acting_sets}))
    result = []
    for history in histories:
        endpoint = _clone(source)
        keys = tuple(key for key in acting_sets if _history(key) == history)
        if not keys:
            raise AssertionError("legal h4 regret block is empty")
        for key in keys:
            actions = acting_sets[key]
            regrets = {
                action: 2.0 * float(postdiscount[key][action])
                - warm_mass * float(source[key][action])
                for action in actions
            }
            selected = max(actions, key=regrets.__getitem__)
            endpoint[key] = {
                action: float(action == selected) for action in actions
            }
        digest = policy_sha256(endpoint)
        result.append(
            LegalH4SelectorDirection(
                label=f"regret_vertex::{history}",
                direction_class="one_step_dcfr_regret_vertex",
                changed_public_histories=(history,),
                endpoint_policy_sha256=digest,
                endpoint_policy=endpoint,
            )
        )
    return tuple(result)


def _token_maps(
    game: ExtensiveFormGame,
) -> tuple[dict[str, dict[str, Action]], ...]:
    result = []
    for player in range(game.num_players):
        rows = {}
        for key, actions in collect_information_sets(game, player).items():
            tokens = {_action_token(action): action for action in actions}
            if len(tokens) != len(actions):
                raise ValueError("legal h4 action tokens collide")
            rows[key] = tokens
        result.append(rows)
    return tuple(result)


def _lp_proposed_direction(
    game: ExtensiveFormGame,
    source: Policy,
    parent: Mapping[str, Any],
    *,
    acting_player: int,
    tolerance: float,
) -> LegalH4SelectorDirection:
    if parent.get("passed") is not True or parent.get("converged") is not True:
        raise ValueError("legal h4 LP direction requires the accepted parent")
    axis = _sequence_axis(game, acting_player)
    token_maps = _token_maps(game)
    rows_by_player: tuple[dict[ResponseSignature, _ResponseRow], ...] = tuple(
        {} for _ in range(game.num_players)
    )
    for record in parent["response_rows"]:
        target = int(record["target_player"])
        signature = tuple(
            sorted(
                (
                    item["information_key"],
                    token_maps[target][item["information_key"]][item["action"]],
                )
                for item in record["signature"]
            )
        )
        coefficients = []
        for token, coefficient in zip(
            axis.variables,
            record["coefficients"],
            strict=True,
        ):
            key, action = token
            if (
                coefficient["information_key"] != key
                or coefficient["action"] != _action_token(action)
            ):
                raise ValueError("retained legal h4 row axis drifted")
            coefficients.append(float.fromhex(coefficient["subject_hex"]))
        row = _ResponseRow(
            target_player=target,
            signature=signature,
            gain=AffinePayoff(
                float.fromhex(record["constant_subject_hex"]),
                tuple(coefficients),
            ),
        )
        if signature in rows_by_player[target]:
            raise ValueError("retained legal h4 response row is duplicated")
        rows_by_player[target][signature] = row
    if tuple(len(rows) for rows in rows_by_player) != tuple(
        parent["response_rows_by_player"]
    ):
        raise ValueError("retained legal h4 response row counts drifted")
    _, realization, _ = _master(
        axis,
        rows_by_player,
        tuple(float(value) for value in parent["caps"]),
        tolerance,
    )
    endpoint = axis.behavioral_policy(realization, source, tolerance)
    digest = policy_sha256(endpoint)
    if digest != parent["final_policy_sha256"]:
        raise ValueError("retained legal h4 restricted master policy did not reproduce")
    acting_sets = collect_information_sets(game, acting_player)
    histories = tuple(
        sorted(
            {
                _history(key)
                for key in acting_sets
                if endpoint[key] != source[key]
            }
        )
    )
    if not histories:
        raise ValueError("retained legal h4 LP direction is a no-op")
    return LegalH4SelectorDirection(
        label="lp_proposed::adr0349_restricted_master",
        direction_class="retained_restricted_master_proposal",
        changed_public_histories=histories,
        endpoint_policy_sha256=digest,
        endpoint_policy=endpoint,
    )


def compile_legal_h4_selector_directions(
    game: ExtensiveFormGame,
    source: Policy,
    parent: Mapping[str, Any],
    *,
    acting_player: int = 0,
    tolerance: float = 1e-10,
) -> tuple[LegalH4SelectorDirection, ...]:
    """Compile three regret-block rays and the retained LP-proposed ray."""

    regret = _regret_vertex_directions(
        game,
        source,
        acting_player=acting_player,
    )
    lp = _lp_proposed_direction(
        game,
        source,
        parent,
        acting_player=acting_player,
        tolerance=tolerance,
    )
    result = (*regret, lp)
    if len(result) != 4 or len({row.label for row in result}) != 4:
        raise AssertionError("legal h4 selector direction inventory drifted")
    return result


__all__ = [
    "LegalH4SelectorDirection",
    "compile_legal_h4_selector_directions",
    "policy_sha256",
]
