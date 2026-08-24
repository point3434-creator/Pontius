"""Fail-closed selector windows with source separation as a prerequisite.

ADR-0351 closes the v1 helper for certificate use.  A source action whose
margin is at or inside the semantic reserve is not uniquely certified at the
source, regardless of whether the competing affine slope later closes,
separates, or remains parallel.  Slope is consulted only after positive
source separation has survived the reserve.
"""

from __future__ import annotations

from math import isfinite

from .game import Action
from .selector_window import (
    ConservativeSelectorWindow,
    FixedResponseSelectorScores,
)


def fail_closed_affine_selector_window(
    source: FixedResponseSelectorScores,
    endpoint: FixedResponseSelectorScores,
    *,
    selector_margin_allowance: float,
) -> ConservativeSelectorWindow:
    """Return zero unless every source selector margin clears its reserve."""

    if source.player != endpoint.player:
        raise ValueError("selector-window-v2 players differ")
    if not isfinite(selector_margin_allowance) or selector_margin_allowance < 0.0:
        raise ValueError(
            "selector-window-v2 allowance must be finite and nonnegative"
        )
    endpoint_rows = {row.key: row for row in endpoint.information_sets}
    if set(endpoint_rows) != {row.key for row in source.information_sets}:
        raise ValueError("selector-window-v2 information schemas differ")

    limit = 1.0
    first: tuple[str, Action, Action] | None = None
    comparisons = 0
    exact_ties = 0
    for source_row in source.information_sets:
        endpoint_row = endpoint_rows[source_row.key]
        if (
            source_row.actions != endpoint_row.actions
            or source_row.selected_action != endpoint_row.selected_action
        ):
            raise ValueError("selector-window-v2 fixed-tape schemas differ")
        source_values = dict(source_row.action_values)
        endpoint_values = dict(endpoint_row.action_values)
        selected = source_row.selected_action
        for action in source_row.actions:
            if action == selected:
                continue
            comparisons += 1
            margin = source_values[selected] - source_values[action]
            closing_slope = (
                endpoint_values[action]
                - source_values[action]
                - endpoint_values[selected]
                + source_values[selected]
            )
            if not isfinite(margin) or not isfinite(closing_slope):
                raise ArithmeticError("selector-window-v2 comparison is nonfinite")
            if margin < -selector_margin_allowance:
                raise ArithmeticError(
                    "selector-window-v2 source action is not maximal"
                )
            if margin == 0.0:
                exact_ties += 1

            # Source separation is a prerequisite, not a fact inferred from
            # the future slope.  This branch intentionally precedes the slope
            # test: a parallel or separating exact tie is still uncertified.
            if margin <= selector_margin_allowance:
                if limit > 0.0:
                    first = (source_row.key, selected, action)
                limit = 0.0
                continue
            if closing_slope <= 0.0:
                continue
            breakpoint = (margin - selector_margin_allowance) / closing_slope
            if breakpoint < limit:
                limit = max(0.0, breakpoint)
                first = (source_row.key, selected, action)

    return ConservativeSelectorWindow(
        scale_limit=min(1.0, max(0.0, limit)),
        first_switch_information_key=None if first is None else first[0],
        first_switch_source_action=None if first is None else first[1],
        first_switch_competing_action=None if first is None else first[2],
        selector_comparisons=comparisons,
        exact_source_action_ties=exact_ties,
    )


__all__ = ["fail_closed_affine_selector_window"]
