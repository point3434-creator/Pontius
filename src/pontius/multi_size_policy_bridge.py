"""Complete one-size river policies inside a sized public-action universe.

The one-size control and the sized game deliberately have different structural
digests and action types.  This module supplies the explicit deployment bridge
needed for a common-game quality comparison: the retained one-size bet maps to
one sized bet, every additional opening size receives zero probability, and
fold/call behavior below every sized bet is copied from the corresponding
one-size continuation.
"""

from __future__ import annotations

from collections.abc import Mapping
import hashlib
import json
import math
from typing import Any

from .evaluation import Policy, policy_distribution
from .game import Action, TERMINAL_PLAYER
from .public_policy_tt import _information_key
from .public_tree_tensor import PublicTreeTensorEvaluator
from .river import BET, CALL, CHECK, FOLD, HoleCards
from .river_multi_size import BetAction
from .river_multiway import MultiwayRiverHoldem
from .river_multiway_multi_size import MultiwayMultiSizeRiverHoldem
from .multi_size_public_tree_tensor import MultiSizePublicTreeTensorEvaluator


def _collapsed_history(
    history: tuple[tuple[int, Action], ...],
) -> tuple[tuple[int, Action], ...]:
    return tuple(
        (seat, BET if isinstance(action, BetAction) else action)
        for seat, action in history
    )


def _same_public_context(
    one_game: MultiwayRiverHoldem,
    sized_game: MultiwayMultiSizeRiverHoldem,
    *,
    retained_bet_size: float,
) -> bool:
    return (
        one_game.board == sized_game.board
        and one_game.pot == sized_game.pot
        and one_game.stacks == sized_game.stacks
        and one_game.bet_size == retained_bet_size
        and retained_bet_size in sized_game.bet_sizes
        and one_game.num_players == sized_game.num_players
    )


def embed_one_size_policy(
    one_layout: PublicTreeTensorEvaluator,
    sized_layout: MultiSizePublicTreeTensorEvaluator,
    hands_by_player: tuple[tuple[HoleCards, ...], ...],
    policy: Policy,
    *,
    retained_bet_size: float,
) -> Policy:
    """Return a complete sized policy with zero mass on added opening bets.

    Response behavior below an added bet is intentionally not left uniform.
    It is copied from the one-size response at the history obtained by erasing
    the amount.  This makes the off-tree completion fixed, explicit, and
    independent of any sized-game quality label.
    """

    if not isinstance(one_layout, PublicTreeTensorEvaluator) or isinstance(
        one_layout, MultiSizePublicTreeTensorEvaluator
    ):
        raise TypeError("the source policy bridge requires a one-size layout")
    if not isinstance(sized_layout, MultiSizePublicTreeTensorEvaluator):
        raise TypeError("the target policy bridge requires a sized layout")
    if not isinstance(one_layout.game, MultiwayRiverHoldem) or not isinstance(
        sized_layout.game, MultiwayMultiSizeRiverHoldem
    ):
        raise TypeError("the policy bridge requires matching multiway river games")
    if isinstance(retained_bet_size, bool) or not math.isfinite(retained_bet_size):
        raise ValueError("the retained bet size must be finite")
    retained_bet_size = float(retained_bet_size)
    if not _same_public_context(
        one_layout.game,
        sized_layout.game,
        retained_bet_size=retained_bet_size,
    ):
        raise ValueError("one-size and sized public contexts do not match")
    if len(hands_by_player) != one_layout.num_players or any(
        not hands for hands in hands_by_player
    ):
        raise ValueError("the policy bridge requires one nonempty hand axis per seat")

    one_nodes = {
        (node.player, node.history): node
        for node in one_layout.nodes
        if node.player != TERMINAL_PLAYER
    }
    result: Policy = {}
    for sized_node in sized_layout.nodes:
        if sized_node.player == TERMINAL_PLAYER:
            continue
        source_key = (sized_node.player, _collapsed_history(sized_node.history))
        try:
            one_node = one_nodes[source_key]
        except KeyError as error:
            raise ValueError("a sized public history has no one-size completion") from error

        opening = CHECK in sized_node.actions
        if opening:
            if one_node.actions != (CHECK, BET):
                raise ValueError("one-size opening schema is not check/bet")
            sized_bets = tuple(
                action for action in sized_node.actions if isinstance(action, BetAction)
            )
            if len(sized_bets) != len(sized_node.actions) - 1:
                raise ValueError("sized opening schema contains an unknown action")
            retained = tuple(
                action for action in sized_bets if action.amount == retained_bet_size
            )
            if len(retained) != 1:
                raise ValueError("sized opening schema lacks one retained bet")
        elif one_node.actions != (FOLD, CALL) or sized_node.actions != (FOLD, CALL):
            raise ValueError("one-size and sized response schemas differ")

        player = sized_node.player
        for hand in hands_by_player[player]:
            one_information_key = _information_key(
                one_layout,
                player,
                hand,
                one_node.history,
            )
            supplied = policy_distribution(
                policy,
                one_information_key,
                one_node.actions,
            )
            sized_information_key = _information_key(
                sized_layout,
                player,
                hand,
                sized_node.history,
            )
            if opening:
                row = {action: 0.0 for action in sized_node.actions}
                row[CHECK] = supplied[CHECK]
                row[retained[0]] = supplied[BET]
            else:
                row = {action: supplied[action] for action in sized_node.actions}
            if sized_information_key in result:
                raise ValueError("the sized policy bridge produced a duplicate information set")
            result[sized_information_key] = row

    expected_schema = {
        _information_key(sized_layout, node.player, hand, node.history): node.actions
        for node in sized_layout.nodes
        if node.player != TERMINAL_PLAYER
        for hand in hands_by_player[node.player]
    }
    if set(result) != set(expected_schema):
        raise AssertionError("the sized policy completion is not schema-complete")
    for key, actions in expected_schema.items():
        row = result[key]
        if set(row) != set(actions) or any(
            not math.isfinite(value) or value < 0.0 for value in row.values()
        ):
            raise AssertionError("the sized policy completion is invalid")
        if abs(math.fsum(row.values()) - 1.0) > 1e-12:
            raise AssertionError("the sized policy completion is not normalized")
    return dict(sorted(result.items()))


def sized_action_token(action: Action) -> tuple[str, str]:
    """Return a JSON-safe, type-bound identity for a sized-game action."""

    if isinstance(action, BetAction):
        return ("bet", action.amount.hex())
    if isinstance(action, str):
        return ("literal", action)
    raise TypeError(f"unsupported sized policy action {action!r}")


def _canonical_policy_rows(policy: Mapping[str, Mapping[Action, float]]) -> list[dict[str, Any]]:
    rows = []
    for key in sorted(policy):
        actions = []
        for action, probability in sorted(
            policy[key].items(), key=lambda item: sized_action_token(item[0])
        ):
            value = float(probability)
            if not math.isfinite(value) or value < 0.0:
                raise ValueError("sized policy probabilities must be finite and nonnegative")
            actions.append(
                {
                    "token": sized_action_token(action),
                    "probability": value,
                }
            )
        if not actions or abs(math.fsum(row["probability"] for row in actions) - 1.0) > 1e-12:
            raise ValueError("sized policy rows must be nonempty and normalized")
        rows.append({"information_key": key, "actions": actions})
    if not rows:
        raise ValueError("a sized policy must contain at least one information set")
    return rows


def sized_policy_digest(policy: Mapping[str, Mapping[Action, float]]) -> str:
    """Return a canonical digest without relying on JSON object action keys."""

    rendered = json.dumps(
        _canonical_policy_rows(policy),
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def serialize_sized_policy(policy: Mapping[str, Mapping[Action, float]]) -> dict[str, Any]:
    """Serialize a complete sized policy with its self-verifying digest."""

    rows = _canonical_policy_rows(policy)
    digest = hashlib.sha256(
        json.dumps(
            rows,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()
    return {"schema_version": 1, "rows": rows, "policy_sha256": digest}


def deserialize_sized_policy(
    record: Mapping[str, Any],
    layout: MultiSizePublicTreeTensorEvaluator,
    hands_by_player: tuple[tuple[HoleCards, ...], ...],
) -> Policy:
    """Restore and schema-check a policy emitted by :func:`serialize_sized_policy`."""

    supplied = dict(record)
    if set(supplied) != {"schema_version", "rows", "policy_sha256"}:
        raise ValueError("sized policy record fields are missing or unknown")
    if supplied["schema_version"] != 1 or not isinstance(supplied["rows"], list):
        raise ValueError("sized policy record version or rows are invalid")
    schema = {
        _information_key(layout, node.player, hand, node.history): node.actions
        for node in layout.nodes
        if node.player != TERMINAL_PLAYER
        for hand in hands_by_player[node.player]
    }
    result: Policy = {}
    for row in supplied["rows"]:
        if not isinstance(row, dict) or set(row) != {"information_key", "actions"}:
            raise ValueError("sized policy row is invalid")
        key = row["information_key"]
        if key not in schema or key in result or not isinstance(row["actions"], list):
            raise ValueError("sized policy information schema differs")
        by_token = {sized_action_token(action): action for action in schema[key]}
        restored: dict[Action, float] = {}
        for action_row in row["actions"]:
            if not isinstance(action_row, dict) or set(action_row) != {
                "token",
                "probability",
            }:
                raise ValueError("sized policy action row is invalid")
            raw_token = action_row["token"]
            if not isinstance(raw_token, (list, tuple)) or len(raw_token) != 2:
                raise ValueError("sized policy action token is invalid")
            token = (str(raw_token[0]), str(raw_token[1]))
            try:
                action = by_token[token]
            except KeyError as error:
                raise ValueError("sized policy action schema differs") from error
            if action in restored:
                raise ValueError("sized policy action is duplicated")
            restored[action] = float(action_row["probability"])
        result[key] = restored
    if set(result) != set(schema):
        raise ValueError("sized policy record is incomplete")
    if sized_policy_digest(result) != supplied["policy_sha256"]:
        raise ValueError("sized policy record digest differs")
    return dict(sorted(result.items()))


def _external_information_schema(
    layout: MultiSizePublicTreeTensorEvaluator,
    hands_by_player: tuple[tuple[HoleCards, ...], ...],
) -> dict[str, tuple[Action, ...]]:
    if len(hands_by_player) != layout.num_players or any(
        not hands for hands in hands_by_player
    ):
        raise ValueError("sized policy schema requires one nonempty hand axis per seat")
    schema: dict[str, tuple[Action, ...]] = {}
    for node in layout.nodes:
        if node.player == TERMINAL_PLAYER:
            continue
        for hand in hands_by_player[node.player]:
            key = _information_key(layout, node.player, hand, node.history)
            previous = schema.setdefault(key, node.actions)
            if previous != node.actions:
                raise ValueError("sized policy external information schema is inconsistent")
    return dict(sorted(schema.items()))


def _external_schema_digest(schema: Mapping[str, tuple[Action, ...]]) -> str:
    payload = [
        {
            "information_key": key,
            "actions": [sized_action_token(action) for action in schema[key]],
        }
        for key in sorted(schema)
    ]
    rendered = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def serialize_compact_sized_policy(
    policy: Mapping[str, Mapping[Action, float]],
    layout: MultiSizePublicTreeTensorEvaluator,
    hands_by_player: tuple[tuple[HoleCards, ...], ...],
) -> dict[str, Any]:
    """Serialize only ordered probabilities against a bound external schema."""

    schema = _external_information_schema(layout, hands_by_player)
    if set(policy) != set(schema):
        raise ValueError("compact sized policy differs from the external schema")
    probabilities = []
    for key, actions in schema.items():
        row = policy[key]
        if set(row) != set(actions):
            raise ValueError("compact sized policy action schema differs")
        values = [float(row[action]) for action in actions]
        if any(not math.isfinite(value) or value < 0.0 for value in values):
            raise ValueError("compact sized policy probabilities are invalid")
        if abs(math.fsum(values) - 1.0) > 1e-12:
            raise ValueError("compact sized policy row is not normalized")
        probabilities.append(values)
    return {
        "schema_version": 1,
        "information_schema_sha256": _external_schema_digest(schema),
        "probabilities": probabilities,
        "policy_sha256": sized_policy_digest(policy),
    }


def deserialize_compact_sized_policy(
    record: Mapping[str, Any],
    layout: MultiSizePublicTreeTensorEvaluator,
    hands_by_player: tuple[tuple[HoleCards, ...], ...],
) -> Policy:
    """Restore a schema-bound compact sized policy and verify its digest."""

    supplied = dict(record)
    expected_fields = {
        "schema_version",
        "information_schema_sha256",
        "probabilities",
        "policy_sha256",
    }
    if set(supplied) != expected_fields or supplied["schema_version"] != 1:
        raise ValueError("compact sized policy fields or version are invalid")
    schema = _external_information_schema(layout, hands_by_player)
    if supplied["information_schema_sha256"] != _external_schema_digest(schema):
        raise ValueError("compact sized policy schema digest differs")
    raw_rows = supplied["probabilities"]
    if not isinstance(raw_rows, list) or len(raw_rows) != len(schema):
        raise ValueError("compact sized policy probability rows differ")
    policy: Policy = {}
    for (key, actions), raw in zip(schema.items(), raw_rows, strict=True):
        if not isinstance(raw, list) or len(raw) != len(actions):
            raise ValueError("compact sized policy action width differs")
        values = tuple(float(value) for value in raw)
        if any(not math.isfinite(value) or value < 0.0 for value in values):
            raise ValueError("compact sized policy probabilities are invalid")
        if abs(math.fsum(values) - 1.0) > 1e-12:
            raise ValueError("compact sized policy row is not normalized")
        policy[key] = {
            action: values[index] for index, action in enumerate(actions)
        }
    if sized_policy_digest(policy) != supplied["policy_sha256"]:
        raise ValueError("compact sized policy digest differs")
    return dict(sorted(policy.items()))
