from __future__ import annotations

import unittest

from pontius.selector_window import (
    FixedResponseSelectorScores,
    FixedSelectorInformationSetScores,
)
from pontius.selector_window_v2 import fail_closed_affine_selector_window


def _scores(
    selected: float,
    competitor: float,
    *,
    player: int = 0,
) -> FixedResponseSelectorScores:
    return FixedResponseSelectorScores(
        player=player,
        value=selected,
        information_sets=(
            FixedSelectorInformationSetScores(
                key="selector-window-v2-control",
                actions=("selected", "competitor"),
                player_depth=0,
                action_values=(
                    ("selected", selected),
                    ("competitor", competitor),
                ),
                selected_action="selected",
            ),
        ),
    )


class SelectorWindowV2Tests(unittest.TestCase):
    def test_parallel_exact_tie_fails_closed_before_slope(self) -> None:
        window = fail_closed_affine_selector_window(
            _scores(0.0, 0.0),
            _scores(0.0, 0.0),
            selector_margin_allowance=0.0,
        )
        self.assertEqual(window.scale_limit, 0.0)
        self.assertEqual(window.exact_source_action_ties, 1)
        self.assertEqual(
            window.first_switch_information_key,
            "selector-window-v2-control",
        )

    def test_separating_exact_tie_still_fails_closed(self) -> None:
        window = fail_closed_affine_selector_window(
            _scores(0.0, 0.0),
            _scores(1.0, 0.0),
            selector_margin_allowance=0.0,
        )
        self.assertEqual(window.scale_limit, 0.0)
        self.assertEqual(window.exact_source_action_ties, 1)

    def test_margin_inside_reserve_fails_closed_even_when_slope_separates(self) -> None:
        window = fail_closed_affine_selector_window(
            _scores(1.0, 0.9995),
            _scores(2.0, 0.0),
            selector_margin_allowance=0.001,
        )
        self.assertEqual(window.scale_limit, 0.0)
        self.assertEqual(window.exact_source_action_ties, 0)

    def test_positive_separation_uses_closing_slope_after_reserve(self) -> None:
        exact = fail_closed_affine_selector_window(
            _scores(1.0, 0.0),
            _scores(0.0, 1.0),
            selector_margin_allowance=0.0,
        )
        reserved = fail_closed_affine_selector_window(
            _scores(1.0, 0.0),
            _scores(0.0, 1.0),
            selector_margin_allowance=0.2,
        )
        self.assertEqual(exact.scale_limit, 0.5)
        self.assertEqual(reserved.scale_limit, 0.4)

    def test_nonmaximal_source_outside_reserve_is_rejected(self) -> None:
        with self.assertRaises(ArithmeticError):
            fail_closed_affine_selector_window(
                _scores(0.0, 1.0),
                _scores(0.0, 1.0),
                selector_margin_allowance=0.1,
            )


if __name__ == "__main__":
    unittest.main()
