from __future__ import annotations

import ast
import unittest
from fractions import Fraction
from pathlib import Path

from pontius.action_abstraction_confirmation import (
    ADR0293_PANEL_SHA256,
    ADR0293_POTS,
    ADR0293_STACKS,
    build_adr0293_confirmation_panel,
)
from pontius.sizing_power_diagnostic import (
    ADR0295_BATCH_COUNT,
    ADR0295_POOL_CANDIDATE_ATTEMPTS,
    ADR0295_POOL_SHA256,
    build_adr0295_sizing_power_pool,
)
from pontius.width_four_sizing_power import (
    ADR0297_BATCH_COUNT,
    ADR0297_POOL_CANDIDATE_ATTEMPTS,
    ADR0297_POOL_CONTEXT_COUNT,
    ADR0297_POOL_SHA256,
    ADR0297_PRIVATE_WIDTH,
    build_adr0297_width_four_pool,
    width_four_lp_dimensions,
)

_ROOT = Path(__file__).parents[1]


class WidthFourSizingPowerPoolTests(unittest.TestCase):
    def test_three_width_four_pools_are_frozen_structural_and_unique(self) -> None:
        pools = tuple(
            build_adr0297_width_four_pool(batch_index=batch_index)
            for batch_index in range(ADR0297_BATCH_COUNT)
        )
        repeated = tuple(
            build_adr0297_width_four_pool(batch_index=batch_index)
            for batch_index in range(ADR0297_BATCH_COUNT)
        )
        self.assertEqual(pools, repeated)
        self.assertEqual(tuple(pool.digest for pool in pools), ADR0297_POOL_SHA256)
        self.assertEqual(
            tuple(pool.candidate_attempts for pool in pools),
            ADR0297_POOL_CANDIDATE_ATTEMPTS,
        )
        self.assertEqual(len({pool.digest for pool in pools}), ADR0297_BATCH_COUNT)
        for batch_index, pool in enumerate(pools):
            self.assertEqual(pool.batch_index, batch_index)
            self.assertEqual(len(pool.contexts), ADR0297_POOL_CONTEXT_COUNT)
            for context_index, context in enumerate(pool.contexts):
                self.assertEqual(
                    context.context_id,
                    f"adr0297-width4-b{batch_index}-c{context_index:02d}",
                )
                self.assertEqual(len(context.opener_hands), ADR0297_PRIVATE_WIDTH)
                self.assertEqual(len(context.responder_hands), ADR0297_PRIVATE_WIDTH)
                self.assertIn(context.pot, ADR0293_POTS)
                self.assertIn(context.stack, ADR0293_STACKS)
                self.assertEqual(context.minimum_bet, 2)
                cards = (
                    *context.board,
                    *(card for hand in context.opener_hands for card in hand),
                    *(card for hand in context.responder_hands for card in hand),
                )
                self.assertEqual(len(cards), 21)
                self.assertEqual(len(set(cards)), len(cards))
                signs = context.showdown_signs
                self.assertEqual({value for row in signs for value in row}, {-1, 1})
                self.assertGreaterEqual(len(set(signs)), 3)
                columns = tuple(
                    tuple(row[column] for row in signs)
                    for column in range(ADR0297_PRIVATE_WIDTH)
                )
                self.assertGreaterEqual(len(set(columns)), 3)
                probabilities = context.joint_probabilities
                self.assertEqual(len(probabilities), ADR0297_PRIVATE_WIDTH)
                self.assertTrue(
                    all(len(row) == ADR0297_PRIVATE_WIDTH for row in probabilities)
                )
                self.assertTrue(
                    all(
                        probability.numerator > 0
                        for row in probabilities
                        for probability in row
                    )
                )
                self.assertEqual(
                    sum(
                        (
                            probability.fraction
                            for row in probabilities
                            for probability in row
                        ),
                        start=Fraction(0),
                    ),
                    1,
                )

    def test_width_four_lp_dimensions_match_the_frozen_exact_work_formula(
        self,
    ) -> None:
        maxima = set()
        for batch_index in range(ADR0297_BATCH_COUNT):
            pool = build_adr0297_width_four_pool(batch_index=batch_index)
            for context in pool.contexts:
                full = width_four_lp_dimensions(
                    context,
                    tuple(range(context.minimum_bet, context.stack + 1)),
                )
                narrow = width_four_lp_dimensions(
                    context,
                    (context.minimum_bet, context.stack),
                )
                self.assertEqual(full.variable_count, 8 * context.stack - 4)
                self.assertEqual(full.inequality_count, 8 * context.stack)
                self.assertEqual(narrow.variable_count, 20)
                self.assertEqual(narrow.inequality_count, 24)
                maxima.add((full.variable_count, full.inequality_count))
        self.assertIn((236, 240), maxima)

    def test_structural_source_has_no_value_or_action_candidate_import(self) -> None:
        path = _ROOT / "src/pontius/width_four_sizing_power.py"
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imports = tuple(
            (node.module, tuple(alias.name for alias in node.names))
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module is not None
        )
        imported_modules = {module for module, _names in imports}
        self.assertNotIn("pontius.legal_action_abstraction", imported_modules)
        self.assertNotIn("legal_action_abstraction", imported_modules)
        imported_names = {name for _module, names in imports for name in names}
        self.assertNotIn("solve_reduced_river_sizing", imported_names)

    def test_earlier_structural_digests_remain_unchanged(self) -> None:
        self.assertEqual(
            build_adr0293_confirmation_panel().digest,
            ADR0293_PANEL_SHA256,
        )
        pools = tuple(
            build_adr0295_sizing_power_pool(batch_index=batch_index)
            for batch_index in range(ADR0295_BATCH_COUNT)
        )
        self.assertEqual(tuple(pool.digest for pool in pools), ADR0295_POOL_SHA256)
        self.assertEqual(
            tuple(pool.candidate_attempts for pool in pools),
            ADR0295_POOL_CANDIDATE_ATTEMPTS,
        )


if __name__ == "__main__":
    unittest.main()
