"""Regret and average-strategy update policies shared by CFR traversals."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, TypeAlias

SolverVariant: TypeAlias = Literal["cfr", "lcfr", "cfr_plus", "dcfr"]


@dataclass(frozen=True, slots=True)
class CFRUpdateRule:
    """Numerical update rule applied after one infoset regret is aggregated.

    ``positive_alpha`` and ``negative_beta`` implement DCFR sign-dependent
    discounting. ``average_gamma`` discounts the accumulated average strategy.
    A missing exponent means that accumulator is not discounted.
    """

    name: SolverVariant
    clip_regrets: bool = False
    positive_alpha: float | None = None
    negative_beta: float | None = None
    average_gamma: float | None = None

    def add_regret(self, current: float, instantaneous: float) -> float:
        updated = current + instantaneous
        return max(0.0, updated) if self.clip_regrets else updated

    @staticmethod
    def _power_discount(iteration: int, exponent: float) -> float:
        powered = float(iteration) ** exponent
        return powered / (powered + 1.0)

    def discount_regret(self, regret: float, iteration: int) -> float:
        exponent = self.positive_alpha if regret >= 0.0 else self.negative_beta
        if exponent is None:
            return regret
        return regret * self._power_discount(iteration, exponent)

    def discount_strategy(self, contribution: float, iteration: int) -> float:
        if self.average_gamma is None:
            return contribution
        factor = (float(iteration) / (float(iteration) + 1.0)) ** self.average_gamma
        return contribution * factor


UPDATE_RULES: dict[SolverVariant, CFRUpdateRule] = {
    "cfr": CFRUpdateRule(name="cfr"),
    # DCFR(1, 1, 1), mathematically equivalent to weighting iteration t by t.
    "lcfr": CFRUpdateRule(
        name="lcfr",
        positive_alpha=1.0,
        negative_beta=1.0,
        average_gamma=1.0,
    ),
    # RM+ with quadratic averaging, the stronger CFR+ baseline used in the
    # experiments of Brown and Sandholm's DCFR paper.
    "cfr_plus": CFRUpdateRule(
        name="cfr_plus",
        clip_regrets=True,
        average_gamma=2.0,
    ),
    # Default DCFR parameters from Brown and Sandholm (2019).
    "dcfr": CFRUpdateRule(
        name="dcfr",
        positive_alpha=1.5,
        negative_beta=0.0,
        average_gamma=2.0,
    ),
}


def update_rule(variant: str) -> CFRUpdateRule:
    try:
        return UPDATE_RULES[variant]  # type: ignore[index]
    except KeyError as error:
        raise ValueError(f"unsupported CFR variant: {variant!r}") from error

