"""Canonical restartable checkpoints for external-axis CFR solvers.

The ADR-0085 policy artifact was evaluable but could not resume its exact DCFR
trajectory.  This additive serializer records the literal regret and strategy-
sum accumulators, validates the public topology and private-hand axes, and
round-trips Float64 values through canonical JSON without changing their binary
value.
"""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Mapping

import numpy as np

from .axis_public_cfr import AxisPublicCFRState
from .real_policy import policy_digest
from .river import format_card

_CHECKPOINT_FIELDS = {
    "schema_version",
    "solver_variant",
    "iteration",
    "warm_started",
    "num_players",
    "public_node_count",
    "topology_sha256",
    "hand_axes_sha256",
    "information_schema_sha256",
    "regrets",
    "strategy_sums",
    "current_policy_sha256",
    "average_policy_sha256",
    "context",
    "provenance",
    "state_sha256",
}


def export_axis_cfr_checkpoint(
    solver: AxisPublicCFRState,
    *,
    context: Mapping[str, Any] | None = None,
    provenance: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return one canonical, self-digesting restart state."""

    if not isinstance(solver, AxisPublicCFRState):
        raise TypeError("axis CFR checkpoint requires an external-axis solver")
    retained_context = _json_object(context, "context")
    retained_provenance = _json_object(provenance, "provenance")
    payload: dict[str, Any] = {
        "schema_version": 1,
        "solver_variant": solver.variant,
        "iteration": solver.iteration,
        "warm_started": bool(solver._warm_started),
        "num_players": solver.num_players,
        "public_node_count": solver.layout.public_node_count,
        "topology_sha256": _topology_digest(solver),
        "hand_axes_sha256": _hand_axes_digest(solver),
        "information_schema_sha256": _information_schema_digest(solver),
        "regrets": solver.regret_table(),
        "strategy_sums": solver.strategy_sum_table(),
        "current_policy_sha256": policy_digest(solver.current_strategy()),
        "average_policy_sha256": policy_digest(solver.average_strategy()),
        "context": retained_context,
        "provenance": retained_provenance,
    }
    payload["state_sha256"] = _payload_digest(payload)
    return payload


def restore_axis_cfr_checkpoint(
    solver: AxisPublicCFRState,
    checkpoint: Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    """Restore a pristine compatible solver and return retained metadata."""

    if not isinstance(solver, AxisPublicCFRState):
        raise TypeError("axis CFR restore requires an external-axis solver")
    supplied = dict(checkpoint)
    if set(supplied) != _CHECKPOINT_FIELDS:
        raise ValueError("axis CFR checkpoint fields are missing or unknown")
    if supplied["schema_version"] != 1:
        raise ValueError("axis CFR checkpoint schema version is unsupported")
    if supplied["state_sha256"] != _payload_digest(supplied):
        raise ValueError("axis CFR checkpoint digest does not match its payload")
    if solver.iteration != 0 or solver._warm_started or any(
        np.any(values != 0.0)
        for arrays in (solver._regrets, solver._strategy_sums)
        for values in arrays
        if values is not None
    ):
        raise ValueError("axis CFR checkpoint restore requires a pristine solver")
    if supplied["solver_variant"] != solver.variant:
        raise ValueError("axis CFR checkpoint solver variant differs")
    if supplied["num_players"] != solver.num_players:
        raise ValueError("axis CFR checkpoint player count differs")
    if supplied["public_node_count"] != solver.layout.public_node_count:
        raise ValueError("axis CFR checkpoint public tree size differs")
    if supplied["topology_sha256"] != _topology_digest(solver):
        raise ValueError("axis CFR checkpoint public topology differs")
    if supplied["hand_axes_sha256"] != _hand_axes_digest(solver):
        raise ValueError("axis CFR checkpoint private-hand axes differ")
    if supplied["information_schema_sha256"] != _information_schema_digest(solver):
        raise ValueError("axis CFR checkpoint information schema differs")
    iteration = supplied["iteration"]
    if isinstance(iteration, bool) or not isinstance(iteration, int) or iteration < 0:
        raise ValueError("axis CFR checkpoint iteration is invalid")
    if not isinstance(supplied["warm_started"], bool):
        raise ValueError("axis CFR checkpoint warm-start flag is invalid")
    context = _json_object(supplied["context"], "context")
    provenance = _json_object(supplied["provenance"], "provenance")

    schema = solver.information_schema()
    regrets = _validated_table(supplied["regrets"], schema, nonnegative=False)
    sums = _validated_table(supplied["strategy_sums"], schema, nonnegative=True)
    prepared = []
    for key, (node_index, hand_index) in solver._key_locations.items():
        node = solver.layout.nodes[node_index]
        regret_array = solver._regrets[node_index]
        sum_array = solver._strategy_sums[node_index]
        if regret_array is None or sum_array is None:
            raise AssertionError("axis CFR checkpoint strategic array is absent")
        prepared.append(
            (
                regret_array,
                sum_array,
                hand_index,
                tuple(regrets[key][action] for action in node.actions),
                tuple(sums[key][action] for action in node.actions),
            )
        )
    for regret_array, sum_array, hand_index, regret_row, sum_row in prepared:
        regret_array[hand_index] = regret_row
        sum_array[hand_index] = sum_row
    solver.iteration = iteration
    solver._warm_started = supplied["warm_started"]
    if hasattr(solver, "last_step_work"):
        solver.last_step_work = None
    if policy_digest(solver.current_strategy()) != supplied["current_policy_sha256"]:
        raise ValueError("restored current policy digest differs")
    if policy_digest(solver.average_strategy()) != supplied["average_policy_sha256"]:
        raise ValueError("restored average policy digest differs")
    return {"context": context, "provenance": provenance}


def axis_cfr_checkpoint_digest(checkpoint: Mapping[str, Any]) -> str:
    """Return the canonical digest after validating the embedded digest."""

    supplied = dict(checkpoint)
    if set(supplied) != _CHECKPOINT_FIELDS:
        raise ValueError("axis CFR checkpoint fields are missing or unknown")
    digest = _payload_digest(supplied)
    if supplied["state_sha256"] != digest:
        raise ValueError("axis CFR checkpoint digest does not match its payload")
    return digest


def _validated_table(
    supplied: Any,
    schema: dict[str, tuple[str, ...]],
    *,
    nonnegative: bool,
) -> dict[str, dict[str, float]]:
    if not isinstance(supplied, dict) or set(supplied) != set(schema):
        raise ValueError("axis CFR checkpoint accumulator schema differs")
    result = {}
    for key, actions in schema.items():
        row = supplied[key]
        if not isinstance(row, dict) or set(row) != set(actions):
            raise ValueError("axis CFR checkpoint action schema differs")
        values = {}
        for action in actions:
            raw = row[action]
            if isinstance(raw, bool) or not isinstance(raw, (int, float)):
                raise ValueError("axis CFR checkpoint accumulator is not numeric")
            value = float(raw)
            if not math.isfinite(value) or (nonnegative and value < 0.0):
                raise ValueError("axis CFR checkpoint accumulator is invalid")
            values[action] = value
        result[key] = values
    return result


def _topology_digest(solver: AxisPublicCFRState) -> str:
    records = [
        {
            "player": node.player,
            "actions": node.actions,
            "children": node.children,
            "terminal_slot": node.terminal_slot,
            "history": node.history,
        }
        for node in solver.layout.nodes
    ]
    return _object_digest(records)


def _hand_axes_digest(solver: AxisPublicCFRState) -> str:
    axes = [
        [[format_card(hand[0]), format_card(hand[1])] for hand in hands]
        for hands in solver.hands_by_player
    ]
    return _object_digest(axes)


def _information_schema_digest(solver: AxisPublicCFRState) -> str:
    schema = {
        key: actions for key, actions in sorted(solver.information_schema().items())
    }
    return _object_digest(schema)


def _json_object(values: Mapping[str, Any] | None, label: str) -> dict[str, Any]:
    result = {} if values is None else dict(values)
    if any(not isinstance(key, str) for key in result):
        raise ValueError(f"axis CFR checkpoint {label} keys must be strings")
    try:
        rendered = json.dumps(
            result,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as error:
        raise ValueError(f"axis CFR checkpoint {label} is not canonical JSON") from error
    restored = json.loads(rendered)
    if not isinstance(restored, dict):
        raise ValueError(f"axis CFR checkpoint {label} must be an object")
    return restored


def _payload_digest(payload: Mapping[str, Any]) -> str:
    retained = {key: value for key, value in payload.items() if key != "state_sha256"}
    return _object_digest(retained)


def _object_digest(value: Any) -> str:
    rendered = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()
