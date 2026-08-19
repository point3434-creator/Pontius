from __future__ import annotations

import unittest

from pontius.depth_limited import (
    DepthLimitedGame,
    DeterministicPerturbedValues,
    PolicyContinuationValues,
    collect_cutoff_reaches,
    collect_cutoff_states,
)
from pontius.evaluation import expected_utilities_from_state
from pontius.kuhn import CHECK, KuhnPoker


class DepthLimitedGameTests(unittest.TestCase):
    def test_policy_continuation_matches_exact_subtree_evaluation(self) -> None:
        state = KuhnPoker().initial_state().apply_action((2, 0)).apply_action(CHECK)
        continuation = PolicyContinuationValues(2, {})

        self.assertEqual(continuation(state), expected_utilities_from_state(2, state, {}))
        self.assertEqual(continuation.cache_size, 1)
        self.assertEqual(continuation(state), continuation(state))
        self.assertEqual(continuation.cache_size, 1)

    def test_one_action_boundary_has_twelve_concrete_leaves(self) -> None:
        game = KuhnPoker()
        continuation = PolicyContinuationValues(2, {})
        truncated = DepthLimitedGame(game, depth_limit=1, leaf_values=continuation)
        leaves = collect_cutoff_states(truncated)

        self.assertEqual(len(leaves), 12)  # six ordered deals times two root actions
        self.assertEqual(len({repr(state) for state in leaves}), 12)
        self.assertTrue(all(len(state.history) == 1 for state in leaves))

    def test_true_terminal_takes_precedence_over_depth_boundary(self) -> None:
        game = KuhnPoker()
        continuation = PolicyContinuationValues(2, {})
        truncated = DepthLimitedGame(game, depth_limit=2, leaf_values=continuation)
        state = truncated.initial_state().apply_action((2, 0))
        state = state.apply_action(CHECK).apply_action(CHECK)

        self.assertFalse(state.is_cutoff)
        self.assertEqual(state.returns(), state.base.returns())
        self.assertEqual(continuation.cache_size, 0)

    def test_perturbations_are_deterministic_and_zero_sum(self) -> None:
        state = KuhnPoker().initial_state().apply_action((2, 0)).apply_action(CHECK)
        exact = PolicyContinuationValues(2, {})
        first = DeterministicPerturbedValues(exact, 2, scale=0.25, seed=17)
        repeated = DeterministicPerturbedValues(exact, 2, scale=0.25, seed=17)
        other_seed = DeterministicPerturbedValues(exact, 2, scale=0.25, seed=18)

        first_value = first(state)
        exact_value = exact(state)
        errors = tuple(value - base for value, base in zip(first_value, exact_value, strict=True))
        self.assertEqual(first_value, repeated(state))
        self.assertNotEqual(first_value, other_seed(state))
        self.assertAlmostEqual(sum(errors), 0.0)

    def test_realized_error_statistics_cover_every_leaf_and_player(self) -> None:
        base_game = KuhnPoker()
        exact = PolicyContinuationValues(2, {})
        noisy = DeterministicPerturbedValues(exact, 2, scale=0.1, seed=4)
        truncated = DepthLimitedGame(base_game, depth_limit=1, leaf_values=noisy)
        stats = noisy.error_stats(collect_cutoff_states(truncated))

        self.assertEqual(stats.leaf_states, 12)
        self.assertEqual(stats.scalar_values, 24)
        self.assertGreater(stats.rmse, 0.0)
        self.assertLessEqual(stats.mean_absolute_error, stats.max_absolute_error)
        self.assertEqual(len(stats.per_player_rmse), 2)
        self.assertAlmostEqual(stats.per_player_rmse[0], stats.per_player_rmse[1])

    def test_zero_scale_is_an_exact_leaf_oracle(self) -> None:
        state = KuhnPoker().initial_state().apply_action((2, 0)).apply_action(CHECK)
        exact = PolicyContinuationValues(2, {})
        oracle = DeterministicPerturbedValues(exact, 2, scale=0.0, seed=99)

        self.assertEqual(oracle(state), exact(state))

    def test_invalid_depth_and_error_scale_are_rejected(self) -> None:
        exact = PolicyContinuationValues(2, {})
        with self.assertRaises(ValueError):
            DepthLimitedGame(KuhnPoker(), depth_limit=0, leaf_values=exact)
        with self.assertRaises(ValueError):
            DeterministicPerturbedValues(exact, 2, scale=-0.01)

    def test_cutoff_reaches_factor_chance_and_player_probabilities(self) -> None:
        exact = PolicyContinuationValues(2, {})
        depth_one = DepthLimitedGame(KuhnPoker(), 1, exact)
        depth_one_reaches = collect_cutoff_reaches(depth_one, {})
        self.assertEqual(len(depth_one_reaches), 12)
        self.assertAlmostEqual(sum(record.joint_reach for record in depth_one_reaches), 1.0)
        self.assertEqual(
            tuple(
                round(
                    sum(record.counterfactual_reach(player) for record in depth_one_reaches),
                    12,
                )
                for player in range(2)
            ),
            (2.0, 1.0),
        )

        depth_two = DepthLimitedGame(KuhnPoker(), 2, exact)
        depth_two_reaches = collect_cutoff_reaches(depth_two, {})
        self.assertEqual(len(depth_two_reaches), 6)
        self.assertAlmostEqual(sum(record.joint_reach for record in depth_two_reaches), 0.25)
        self.assertEqual(
            tuple(
                round(
                    sum(record.counterfactual_reach(player) for record in depth_two_reaches),
                    12,
                )
                for player in range(2)
            ),
            (0.5, 0.5),
        )

    def test_reach_weighted_statistics_separate_conditional_and_root_error(self) -> None:
        exact = PolicyContinuationValues(2, {})
        noisy = DeterministicPerturbedValues(exact, 2, scale=0.1, seed=5)
        game = DepthLimitedGame(KuhnPoker(), 2, noisy)
        reaches = collect_cutoff_reaches(game, {})
        stats = noisy.reach_weighted_error_stats(reaches)

        self.assertAlmostEqual(stats.on_policy_reach_mass, 0.25)
        self.assertAlmostEqual(stats.counterfactual_reach_mass[0], 0.5)
        self.assertAlmostEqual(stats.counterfactual_reach_mass[1], 0.5)
        self.assertIsNotNone(stats.on_policy_rmse)
        assert stats.on_policy_rmse is not None
        self.assertAlmostEqual(stats.on_policy_root_l2, 0.5 * stats.on_policy_rmse)
        self.assertAlmostEqual(
            stats.per_player_on_policy_rmse[0] or 0.0,
            stats.per_player_on_policy_rmse[1] or 0.0,
        )

    def test_correlated_bias_and_scope_are_independent_controls(self) -> None:
        game = KuhnPoker()
        state_a = game.initial_state().apply_action((2, 0)).apply_action(CHECK)
        state_b = game.initial_state().apply_action((1, 0)).apply_action(CHECK)
        exact = PolicyContinuationValues(2, {})
        public_key = lambda state: repr(state.history)
        correlated = DeterministicPerturbedValues(
            exact,
            2,
            scale=0.1,
            seed=3,
            noise_key=public_key,
        )
        self.assertEqual(correlated.error_for(state_a), correlated.error_for(state_b))

        biased = DeterministicPerturbedValues(
            exact,
            2,
            scale=0.0,
            bias=(0.2, -0.2),
        )
        self.assertEqual(biased.error_for(state_a), (0.2, -0.2))

        scoped = DeterministicPerturbedValues(
            exact,
            2,
            scale=0.1,
            seed=3,
            active_state_keys=frozenset({repr(state_a)}),
        )
        self.assertNotEqual(scoped.error_for(state_a), (0.0, 0.0))
        self.assertEqual(scoped.error_for(state_b), (0.0, 0.0))


if __name__ == "__main__":
    unittest.main()
