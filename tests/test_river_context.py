from __future__ import annotations

import unittest

from pontius.river_context import (
    CONTEXT_FAMILIES,
    generate_river_contexts,
    river_context_features,
    serialize_river_context,
)
from pontius.river_oracle import solve_river_game


class RiverContextTests(unittest.TestCase):
    def test_generation_is_deterministic_and_groups_stay_in_one_split(self) -> None:
        first = generate_river_contexts(groups=2, seed=19)
        second = generate_river_contexts(groups=2, seed=19)

        self.assertEqual(len(first), 2 * len(CONTEXT_FAMILIES))
        self.assertEqual(
            [context.game.provenance_digest for context in first],
            [context.game.provenance_digest for context in second],
        )
        for group_id in {context.group_id for context in first}:
            group = [context for context in first if context.group_id == group_id]
            self.assertEqual(len({context.split for context in group}), 1)
            self.assertEqual(len({context.game.structural_digest for context in group}), 1)
            self.assertEqual({context.family for context in group}, set(CONTEXT_FAMILIES))

    def test_generated_ranges_have_supported_marginals_and_exact_oracles(self) -> None:
        contexts = generate_river_contexts(groups=1, seed=3)
        for context in contexts:
            game = context.game
            marginal0 = game.marginal_distribution(0)
            marginal1 = game.marginal_distribution(1)
            self.assertEqual(len(marginal0), 4)
            self.assertEqual(len(marginal1), 4)
            self.assertAlmostEqual(sum(probability for _, probability in game.deals), 1.0)
            self.assertTrue(all(probability > 0.0 for probability in marginal0.values()))
            self.assertTrue(all(probability > 0.0 for probability in marginal1.values()))
            self.assertLessEqual(solve_river_game(game).nash_conv, 1e-8)

    def test_features_and_serialization_preserve_range_provenance(self) -> None:
        context = generate_river_contexts(
            groups=1,
            seed=11,
            families=("blocker_stress",),
        )[0]
        features = river_context_features(context)
        serialized = serialize_river_context(context)

        self.assertGreater(float(features["player0_max_conditional_shift"]), 0.0)
        self.assertGreater(float(features["player1_max_conditional_shift"]), 0.0)
        self.assertGreater(float(features["range_mutual_information"]), 0.0)
        self.assertEqual(serialized["provenance_digest"], context.game.provenance_digest)
        self.assertAlmostEqual(
            sum(row["probability"] for row in serialized["joint_range"]),  # type: ignore[index]
            1.0,
        )

    def test_invalid_generation_parameters_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "groups"):
            generate_river_contexts(groups=0)
        with self.assertRaisesRegex(ValueError, "hands_per_player"):
            generate_river_contexts(groups=1, hands_per_player=1)
        with self.assertRaisesRegex(ValueError, "unsupported"):
            generate_river_contexts(groups=1, families=("imaginary",))
        with self.assertRaisesRegex(ValueError, "splits"):
            generate_river_contexts(groups=1, splits=("future",))

    def test_split_filter_does_not_materialize_reserved_contexts(self) -> None:
        contexts = generate_river_contexts(
            groups=20,
            seed=23,
            families=("balanced",),
            splits=("development",),
        )
        self.assertGreater(len(contexts), 0)
        self.assertEqual({context.split for context in contexts}, {"development"})


if __name__ == "__main__":
    unittest.main()
