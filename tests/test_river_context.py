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

    def test_sequential_generation_is_exact_and_exposes_raise_features(self) -> None:
        contexts = generate_river_contexts(
            groups=1,
            seed=3,
            hands_per_player=2,
            families=("balanced", "correlated"),
            sequential_raise=True,
        )

        self.assertEqual(len(contexts), 2)
        self.assertEqual(
            len({context.game.structural_digest for context in contexts}),
            1,
        )
        for context in contexts:
            game = context.game
            self.assertIsNotNone(game.raise_to)
            assert game.raise_to is not None
            self.assertGreaterEqual(game.raise_to, 2.0 * game.bet_size)
            self.assertLessEqual(game.raise_to, min(game.stacks))
            features = river_context_features(context)
            serialized = serialize_river_context(context)
            self.assertEqual(features["has_raise"], 1)
            self.assertEqual(features["raise_to"], game.raise_to)
            self.assertEqual(features["payoff_span"], game.payoff_span)
            self.assertEqual(serialized["raise_to"], game.raise_to)
            solution = solve_river_game(game)
            self.assertLessEqual(solution.nash_conv, 1e-8)
            self.assertEqual(solution.player0_pure_policies, 16)
            self.assertEqual(solution.player1_pure_policies, 9)

    def test_sequential_context_is_paired_with_the_same_one_bet_range(self) -> None:
        one_bet = generate_river_contexts(
            groups=1,
            seed=17,
            families=("blocker_stress",),
        )[0]
        sequential = generate_river_contexts(
            groups=1,
            seed=17,
            families=("blocker_stress",),
            sequential_raise=True,
        )[0]

        self.assertEqual(one_bet.context_id, sequential.context_id)
        self.assertEqual(one_bet.game.board, sequential.game.board)
        self.assertEqual(one_bet.game.pot, sequential.game.pot)
        self.assertEqual(one_bet.game.bet_size, sequential.game.bet_size)
        self.assertEqual(
            one_bet.game.joint_distribution(),
            sequential.game.joint_distribution(),
        )
        self.assertIsNone(one_bet.game.raise_to)
        self.assertIsNotNone(sequential.game.raise_to)

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
        with self.assertRaisesRegex(TypeError, "boolean"):
            generate_river_contexts(groups=1, sequential_raise=1)  # type: ignore[arg-type]

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
