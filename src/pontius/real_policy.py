"""Deterministic real-policy provenance helpers."""

from __future__ import annotations

import hashlib
import json
import math
from typing import Mapping

from .evaluation import Policy
from .game import Action
from .public_policy_tt import _information_key
from .public_tree_tensor import PublicTreeTensorEvaluator
from .river import HoleCards


def splice_unilateral_best_response(
    *,
    layout: PublicTreeTensorEvaluator,
    hands_by_player: tuple[tuple[HoleCards, ...], ...],
    baseline: Policy,
    target_player: int,
    best_response_actions: Mapping[str, Action],
) -> Policy:
    """Replace exactly one seat by a complete deterministic best response."""

    if target_player not in range(layout.num_players):
        raise ValueError("best-response target is outside the player range")
    result: Policy = {
        key: dict(distribution) for key, distribution in baseline.items()
    }
    expected_keys: set[str] = set()
    for node in layout.nodes:
        if node.player != target_player:
            continue
        for hand in hands_by_player[target_player]:
            key = _information_key(layout, target_player, hand, node.history)
            expected_keys.add(key)
            try:
                action = best_response_actions[key]
            except KeyError as error:
                raise ValueError("best-response action map is incomplete") from error
            if action not in node.actions:
                raise ValueError("best-response action is illegal at its information set")
            result[key] = {
                candidate: float(candidate == action) for candidate in node.actions
            }
    if set(best_response_actions) != expected_keys:
        raise ValueError("best-response action map has missing or extra information sets")
    return dict(sorted(result.items()))


def policy_digest(policy: Policy) -> str:
    """Return a canonical digest for one finite behavioral policy."""

    canonical = {
        key: {action: float(probability) for action, probability in sorted(row.items())}
        for key, row in sorted(policy.items())
    }
    rendered = json.dumps(canonical, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def policy_statistics(policy: Policy) -> dict[str, float | int]:
    """Summarize entropy, pure mass, and repeated hand distributions."""

    if not policy:
        raise ValueError("policy statistics require a nonempty policy")
    entropies = []
    pure = 0
    distributions: set[tuple[tuple[str, float], ...]] = set()
    for distribution in policy.values():
        if not distribution:
            raise ValueError("policy distribution cannot be empty")
        total = math.fsum(distribution.values())
        if (
            any(not math.isfinite(value) or value < 0.0 for value in distribution.values())
            or abs(total - 1.0) > 1e-12
        ):
            raise ValueError("policy distribution must be finite and normalized")
        entropies.append(
            -math.fsum(
                value * math.log(value)
                for value in distribution.values()
                if value > 0.0
            )
        )
        pure += int(sum(value == 1.0 for value in distribution.values()) == 1)
        distributions.add(tuple(sorted(distribution.items())))
    return {
        "information_sets": len(policy),
        "mean_entropy": math.fsum(entropies) / len(entropies),
        "pure_information_sets": pure,
        "pure_information_set_fraction": pure / len(policy),
        "distinct_action_distributions": len(distributions),
    }


def mean_policy_total_variation(first: Policy, second: Policy) -> float:
    """Return mean information-set TV for two equal-schema policies."""

    if set(first) != set(second) or not first:
        raise ValueError("policy TV requires equal nonempty information schemas")
    values = []
    for key in sorted(first):
        if set(first[key]) != set(second[key]):
            raise ValueError("policy TV action schemas differ")
        values.append(
            0.5
            * math.fsum(
                abs(first[key][action] - second[key][action])
                for action in first[key]
            )
        )
    return math.fsum(values) / len(values)
