from __future__ import annotations

import unittest

from pontius.evaluation import (
    best_response,
    best_response_enumerated,
    collect_information_sets,
    counterfactual_regret_profile,
    evaluate_profile,
    expected_utilities,
)
from pontius.river import (
    BET,
    CALL,
    CHECK,
    FOLD,
    RiverDeal,
    RiverHoldem,
    evaluate_five,
    evaluate_seven,
    format_card,
    make_hole,
    parse_card,
    parse_cards,
)
from pontius.river_oracle import solve_river_game


def _board() -> tuple[int, ...]:
    return parse_cards("2c", "7d", "9h", "Js", "Qc")


def _deterministic_game() -> tuple[RiverHoldem, RiverDeal]:
    deal = RiverDeal(make_hole("Ts", "Ks"), make_hole("Ah", "3h"))
    game = RiverHoldem.from_joint_weights(
        board=_board(),
        pot=10.0,
        stacks=(20.0, 20.0),
        bet_size=5.0,
        joint_weights={deal: 1.0},
    )
    return game, deal


def _deterministic_policy(game: RiverHoldem, player: int, action: str) -> dict:
    return {
        key: {candidate: float(candidate == action) for candidate in actions}
        for key, actions in collect_information_sets(game, player).items()
    }


def _blocker_pair() -> tuple[RiverHoldem, RiverHoldem, RiverDeal, RiverDeal, tuple[int, int]]:
    common = RiverDeal(make_hole("Ac", "Ad"), make_hole("Kh", "Kd"))
    target_hand = make_hole("Ah", "3h")
    nuts = RiverDeal(make_hole("Ts", "Ks"), target_hand)
    bluff = RiverDeal(make_hole("4s", "5s"), target_hand)
    game_nuts = RiverHoldem.from_joint_weights(
        board=_board(),
        pot=10.0,
        stacks=(20.0, 20.0),
        bet_size=5.0,
        joint_weights={common: 0.99, nuts: 0.01},
    )
    game_bluff = RiverHoldem.from_joint_weights(
        board=_board(),
        pot=10.0,
        stacks=(20.0, 20.0),
        bet_size=5.0,
        joint_weights={common: 0.99, bluff: 0.01},
    )
    return game_nuts, game_bluff, nuts, bluff, target_hand


class RiverHoldemTests(unittest.TestCase):
    def test_card_round_trip_and_canonical_private_hand(self) -> None:
        self.assertEqual(format_card(parse_card("AS")), "As")
        self.assertEqual(
            make_hole("Ks", "2c"),
            (parse_card("2c"), parse_card("Ks")),
        )
        with self.assertRaisesRegex(ValueError, "invalid card"):
            parse_card("1x")
        with self.assertRaisesRegex(ValueError, "distinct"):
            make_hole("As", "As")

    def test_exact_hand_evaluator_orders_categories_and_handles_wheel(self) -> None:
        royal_flush = evaluate_five(parse_cards("As", "Ks", "Qs", "Js", "Ts"))
        quads = evaluate_five(parse_cards("Ac", "Ad", "Ah", "As", "2c"))
        wheel = evaluate_five(parse_cards("As", "2d", "3h", "4c", "5s"))
        six_high = evaluate_five(parse_cards("2s", "3d", "4h", "5c", "6s"))

        self.assertEqual(royal_flush[0], 8)
        self.assertEqual(quads[0], 7)
        self.assertGreater(royal_flush, quads)
        self.assertEqual(wheel, (4, 5))
        self.assertGreater(six_high, wheel)

        seven_card_rank = evaluate_seven(
            parse_cards("As", "Ad", "Ah", "Ks", "Kd", "2c", "3c")
        )
        self.assertEqual(seven_card_rank, (6, 14, 13))

    def test_independent_ranges_apply_card_removal_before_normalizing(self) -> None:
        aces = make_hole("As", "Ac")
        kings = make_hole("Ks", "Kc")
        red_aces = make_hole("Ah", "Ad")
        ace_queen = make_hole("As", "Qd")
        game = RiverHoldem.from_independent_ranges(
            board=_board(),
            pot=10.0,
            stacks=(20.0, 20.0),
            bet_size=5.0,
            player0_weights={aces: 1.0, kings: 1.0},
            player1_weights={red_aces: 1.0, ace_queen: 1.0},
        )

        self.assertEqual(len(game.deals), 3)
        marginal0 = game.marginal_distribution(0)
        marginal1 = game.marginal_distribution(1)
        self.assertAlmostEqual(marginal0[aces], 1.0 / 3.0)
        self.assertAlmostEqual(marginal0[kings], 2.0 / 3.0)
        self.assertAlmostEqual(marginal1[red_aces], 2.0 / 3.0)
        self.assertAlmostEqual(marginal1[ace_queen], 1.0 / 3.0)
        self.assertEqual(
            game.conditional_opponent_distribution(0, aces),
            {red_aces: 1.0},
        )

    def test_river_tree_has_exact_zero_sum_payoffs(self) -> None:
        game, deal = _deterministic_game()
        dealt = game.initial_state().apply_action(deal)

        self.assertEqual(dealt.legal_actions(), (CHECK, BET))
        self.assertEqual(dealt.apply_action(CHECK).returns(), (5.0, -5.0))

        facing_bet = dealt.apply_action(BET)
        self.assertEqual(facing_bet.legal_actions(), (FOLD, CALL))
        self.assertEqual(facing_bet.apply_action(FOLD).returns(), (5.0, -5.0))
        self.assertEqual(facing_bet.apply_action(CALL).returns(), (10.0, -10.0))

        policy = _deterministic_policy(game, 0, BET)
        response_key = next(iter(collect_information_sets(game, 1)))
        policy[response_key] = {FOLD: 0.5, CALL: 0.5}
        utilities = expected_utilities(game, policy)
        self.assertAlmostEqual(utilities[0], 7.5)
        self.assertAlmostEqual(utilities[1], -7.5)

    def test_information_keys_ignore_ranges_but_provenance_does_not(self) -> None:
        game_nuts, game_bluff, nuts, bluff, _ = _blocker_pair()
        nuts_key = (
            game_nuts.initial_state()
            .apply_action(nuts)
            .apply_action(BET)
            .information_state_key(1)
        )
        bluff_key = (
            game_bluff.initial_state()
            .apply_action(bluff)
            .apply_action(BET)
            .information_state_key(1)
        )
        self.assertEqual(nuts_key, bluff_key)
        self.assertEqual(game_nuts.structural_digest, game_bluff.structural_digest)
        self.assertNotEqual(game_nuts.provenance_digest, game_bluff.provenance_digest)

    def test_one_percent_range_change_flips_conditional_best_response(self) -> None:
        game_nuts, game_bluff, nuts, _, target_hand = _blocker_pair()
        policy = _deterministic_policy(game_nuts, 0, BET)
        policy.update(_deterministic_policy(game_bluff, 0, BET))

        nuts_value, nuts_response = best_response(game_nuts, policy, 1)
        bluff_value, bluff_response = best_response(game_bluff, policy, 1)
        nuts_enumerated = best_response_enumerated(game_nuts, policy, 1)
        bluff_enumerated = best_response_enumerated(game_bluff, policy, 1)
        target_key = (
            game_nuts.initial_state()
            .apply_action(nuts)
            .apply_action(BET)
            .information_state_key(1)
        )

        self.assertAlmostEqual(game_nuts.total_variation(game_bluff), 0.01)
        self.assertAlmostEqual(
            game_nuts.conditional_opponent_total_variation(
                game_bluff, player=1, own_hand=target_hand
            ),
            1.0,
        )
        self.assertEqual(nuts_response[target_key], FOLD)
        self.assertEqual(bluff_response[target_key], CALL)
        self.assertAlmostEqual(nuts_enumerated[0], nuts_value)
        self.assertAlmostEqual(bluff_enumerated[0], bluff_value)
        self.assertEqual(nuts_enumerated[1], nuts_response)
        self.assertEqual(bluff_enumerated[1], bluff_response)

    def test_total_variation_bound_is_fixed_value_not_policy_reuse(self) -> None:
        game_nuts, game_bluff, _, _, _ = _blocker_pair()
        fixed_policy = {}
        for game in (game_nuts, game_bluff):
            fixed_policy.update(_deterministic_policy(game, 0, BET))
            fixed_policy.update(_deterministic_policy(game, 1, CALL))

        value_nuts = expected_utilities(game_nuts, fixed_policy)[0]
        value_bluff = expected_utilities(game_bluff, fixed_policy)[0]
        bound = game_nuts.fixed_policy_value_bound(game_bluff)

        self.assertEqual(game_nuts.payoff_span, 20.0)
        self.assertAlmostEqual(abs(value_nuts - value_bluff), 0.2)
        self.assertLessEqual(abs(value_nuts - value_bluff), bound + 1e-12)
        self.assertAlmostEqual(bound, 0.2)

    def test_normal_form_oracle_recovers_classic_bluffing_equilibrium(self) -> None:
        target_hand = make_hole("Ah", "3h")
        value_deal = RiverDeal(make_hole("Ts", "Ks"), target_hand)
        bluff_deal = RiverDeal(make_hole("4s", "5s"), target_hand)
        game = RiverHoldem.from_joint_weights(
            board=_board(),
            pot=10.0,
            stacks=(20.0, 20.0),
            bet_size=5.0,
            joint_weights={value_deal: 0.5, bluff_deal: 0.5},
        )

        solution = solve_river_game(game)
        value_key = (
            game.initial_state()
            .apply_action(value_deal)
            .information_state_key(0)
        )
        bluff_key = (
            game.initial_state()
            .apply_action(bluff_deal)
            .information_state_key(0)
        )
        response_key = (
            game.initial_state()
            .apply_action(value_deal)
            .apply_action(BET)
            .information_state_key(1)
        )

        self.assertAlmostEqual(solution.value_player0, 5.0 / 3.0)
        self.assertAlmostEqual(solution.policy[value_key][BET], 1.0)
        self.assertAlmostEqual(solution.policy[bluff_key][BET], 1.0 / 3.0)
        self.assertAlmostEqual(solution.policy[response_key][CALL], 2.0 / 3.0)
        self.assertLessEqual(solution.nash_conv, 1e-8)
        self.assertEqual(solution.player0_pure_policies, 4)
        self.assertEqual(solution.player1_pure_policies, 2)

    def test_local_counterfactual_regret_equals_nash_conv_in_this_shallow_tree(
        self,
    ) -> None:
        target_hand = make_hole("Ah", "3h")
        game = RiverHoldem.from_joint_weights(
            board=_board(),
            pot=10.0,
            stacks=(20.0, 20.0),
            bet_size=5.0,
            joint_weights={
                RiverDeal(make_hole("Ts", "Ks"), target_hand): 0.5,
                RiverDeal(make_hole("4s", "5s"), target_hand): 0.5,
            },
        )
        for policy in ({}, solve_river_game(game).policy):
            evaluation = evaluate_profile(game, policy)
            local_regret = counterfactual_regret_profile(game, policy)
            self.assertAlmostEqual(
                local_regret.total_positive_regret,
                evaluation.nash_conv,
            )

    def test_invalid_board_overlap_and_bet_are_rejected(self) -> None:
        overlapping = RiverDeal(make_hole("2c", "As"), make_hole("Kh", "Kd"))
        with self.assertRaisesRegex(ValueError, "overlap"):
            RiverHoldem.from_joint_weights(
                board=_board(),
                pot=10.0,
                stacks=(20.0, 20.0),
                bet_size=5.0,
                joint_weights={overlapping: 1.0},
            )
        with self.assertRaisesRegex(ValueError, "remaining stack"):
            RiverHoldem.from_joint_weights(
                board=_board(),
                pot=10.0,
                stacks=(4.0, 20.0),
                bet_size=5.0,
                joint_weights={
                    RiverDeal(
                        make_hole("As", "Ad"),
                        make_hole("Kh", "Kd"),
                    ): 1.0
                },
            )


if __name__ == "__main__":
    unittest.main()
