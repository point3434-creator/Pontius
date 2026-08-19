"""Behavior-policy transformations used by controlled search experiments."""

from __future__ import annotations

from .evaluation import Policy, policy_distribution
from .game import Action


def interpolate_policy(
    blueprint: Policy,
    candidate: Policy,
    information_sets: dict[str, tuple[Action, ...]],
    candidate_weight: float,
) -> Policy:
    """Overlay a candidate through a fixed linear trust region.

    A weight of zero is the explicit blueprint/no-op policy; a weight of one is
    full candidate replacement. Only information sets present in ``candidate``
    are changed.
    """

    if not 0.0 <= candidate_weight <= 1.0:
        raise ValueError("candidate_weight must be between zero and one")
    unknown = set(candidate) - set(information_sets)
    if unknown:
        raise ValueError(f"candidate contains unknown information sets: {unknown!r}")

    merged = {
        key: dict(distribution) for key, distribution in blueprint.items()
    }
    blueprint_weight = 1.0 - candidate_weight
    for key, supplied in candidate.items():
        actions = information_sets[key]
        base_distribution = policy_distribution(blueprint, key, actions)
        candidate_distribution = policy_distribution(candidate, key, actions)
        merged[key] = {
            action: (
                blueprint_weight * base_distribution[action]
                + candidate_weight * candidate_distribution[action]
            )
            for action in actions
        }
    return merged
