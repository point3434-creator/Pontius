from __future__ import annotations

import re
import unittest
from math import fsum

from pontius.cfr import TabularCFR
from pontius.dependency_tape import (
    CompiledPolicyDeltaTape,
    CompiledPolicyDependencyTape,
)
from pontius.evaluation import best_response, evaluate_profile
from pontius.game import CHANCE_PLAYER, TERMINAL_PLAYER
from pontius.river import BET, CALL, CHECK, FOLD, evaluate_seven, make_hole, parse_cards
from pontius.river_multiway import (
    MultiwayRiverDeal,
    MultiwayRiverHoldem,
    MultiwayRiverState,
)


BOARD = parse_cards("2c", "7d", "9h", "Js", "Qc")
HANDS = (
    make_hole("As", "Ad"),
    make_hole("Ks", "Kd"),
    make_hole("Ts", "Td"),
)
SECOND_HANDS = (
    make_hole("Ah", "Ac"),
    make_hole("Kh", "Kc"),
    make_hole("Th", "Tc"),
)


def three_player_game(
    *,
    deals: tuple[MultiwayRiverDeal, ...] | None = None,
    weights: tuple[float, ...] | None = None,
    scale: float = 1.0,
) -> MultiwayRiverHoldem:
    selected = deals or (MultiwayRiverDeal(HANDS),)
    selected_weights = weights or tuple(1.0 for _ in selected)
    return MultiwayRiverHoldem.from_joint_weights(
        board=BOARD,
        pot=12.0 * scale,
        stacks=(30.0 * scale,) * 3,
        bet_size=3.0 * scale,
        joint_weights=dict(zip(selected, selected_weights, strict=True)),
    )


def dealt(game: MultiwayRiverHoldem, index: int = 0) -> MultiwayRiverState:
    return game.initial_state().apply_action(game.deals[index][0])


def terminal_states(state: MultiwayRiverState) -> tuple[MultiwayRiverState, ...]:
    if state.current_player == TERMINAL_PLAYER:
        return (state,)
    return tuple(
        terminal
        for action in state.legal_actions()
        for terminal in terminal_states(state.apply_action(action))
    )


def independently_audited_returns(state: MultiwayRiverState) -> tuple[float, ...]:
    if state.current_player != TERMINAL_PLAYER or state.deal is None:
        raise AssertionError("audit requires a terminal dealt state")
    num_players = state.game.num_players
    contributions = [0.0] * num_players
    contenders = set(range(num_players))
    if state.bettor is not None:
        contenders = {state.bettor}
        for player, action in state.history:
            if action == CALL:
                contenders.add(player)
        for player in contenders:
            contributions[player] = state.game.bet_size

    ranks = [
        (
            evaluate_seven((*state.game.board, *state.deal.hand(player))),
            player,
        )
        for player in contenders
    ]
    best_rank = max(rank for rank, _ in ranks)
    winners = [player for rank, player in ranks if rank == best_rank]
    final_pot = state.game.pot + sum(contributions)
    payouts = [0.0] * num_players
    for player in winners:
        payouts[player] = final_pot / len(winners)
    sunk = state.game.pot / num_players
    return tuple(
        payouts[player] - sunk - contributions[player]
        for player in range(num_players)
    )


def assert_evaluation_equal(
    test: unittest.TestCase,
    left: object,
    right: object,
) -> None:
    for name in ("utilities", "best_response_values", "deviation_gains"):
        for left_value, right_value in zip(
            getattr(left, name),
            getattr(right, name),
            strict=True,
        ):
            test.assertAlmostEqual(left_value, right_value, places=10)
    test.assertAlmostEqual(left.nash_conv, right.nash_conv, places=10)
    test.assertEqual(left.exploitability, right.exploitability)


class MultiwayRiverPayoffTests(unittest.TestCase):
    def test_all_check_showdown_uses_equal_sunk_pot_shares(self) -> None:
        state = dealt(three_player_game())
        for _ in range(3):
            state = state.apply_action(CHECK)
        self.assertEqual(state.returns(), (8.0, -4.0, -4.0))

    def test_bet_call_fold_and_cyclic_response_order(self) -> None:
        state = dealt(three_player_game()).apply_action(CHECK).apply_action(BET)
        self.assertEqual(state.current_player, 2)
        state = state.apply_action(FOLD)
        self.assertEqual(state.current_player, 0)
        state = state.apply_action(CALL)
        self.assertEqual(state.returns(), (11.0, -7.0, -4.0))

    def test_bet_all_fold_returns_bettors_unmatched_chips(self) -> None:
        state = dealt(three_player_game()).apply_action(BET)
        state = state.apply_action(FOLD).apply_action(FOLD)
        self.assertEqual(state.returns(), (8.0, -4.0, -4.0))

    def test_public_board_tie_splits_only_among_contenders(self) -> None:
        board = parse_cards("Ah", "Kh", "Qh", "Jh", "Th")
        deal = MultiwayRiverDeal(
            (
                make_hole("2c", "3c"),
                make_hole("4d", "5d"),
                make_hole("6s", "7s"),
            )
        )
        game = MultiwayRiverHoldem.from_joint_weights(
            board=board,
            pot=12.0,
            stacks=(30.0,) * 3,
            bet_size=3.0,
            joint_weights={deal: 1.0},
        )
        state = dealt(game).apply_action(BET).apply_action(CALL).apply_action(FOLD)
        self.assertEqual(state.returns(), (2.0, 2.0, -4.0))

    def test_every_reachable_terminal_matches_independent_payoff_audit(self) -> None:
        terminals = terminal_states(dealt(three_player_game()))
        self.assertEqual(len(terminals), 13)
        for state in terminals:
            expected = independently_audited_returns(state)
            self.assertEqual(state.returns(), expected)
            self.assertAlmostEqual(fsum(state.returns()), 0.0, places=12)

    def test_payoff_span_is_exact_individual_range(self) -> None:
        game = three_player_game()
        all_returns = [
            value
            for terminal in terminal_states(dealt(game))
            for value in terminal.returns()
        ]
        self.assertEqual(game.payoff_span, 21.0)
        self.assertEqual(max(all_returns) - min(all_returns), game.payoff_span)


class MultiwayRiverRangeAndInformationTests(unittest.TestCase):
    def test_independent_ranges_remove_private_card_collisions(self) -> None:
        p0 = {make_hole("As", "Ad"): 2.0, make_hole("Ks", "Kd"): 1.0}
        p1 = {make_hole("As", "Kh"): 3.0, make_hole("Qh", "Qd"): 1.0}
        p2 = {make_hole("Ac", "Ah"): 1.0, make_hole("Tc", "Td"): 2.0}
        game = MultiwayRiverHoldem.from_independent_ranges(
            board=BOARD,
            pot=12.0,
            stacks=(30.0,) * 3,
            bet_size=3.0,
            player_weights=(p0, p1, p2),
        )
        self.assertAlmostEqual(sum(game.joint_distribution().values()), 1.0)
        self.assertTrue(game.joint_distribution())
        for deal in game.joint_distribution():
            cards = [card for hand in deal.hands for card in hand]
            self.assertEqual(len(cards), len(set(cards)))
            self.assertFalse(set(cards) & set(BOARD))

    def test_joint_conditionals_preserve_correlation(self) -> None:
        deal0 = MultiwayRiverDeal(HANDS)
        deal1 = MultiwayRiverDeal((HANDS[0], SECOND_HANDS[1], SECOND_HANDS[2]))
        game = three_player_game(deals=(deal0, deal1), weights=(1.0, 3.0))
        conditional = game.conditional_other_hands_distribution(0, HANDS[0])
        self.assertEqual(len(conditional), 2)
        self.assertAlmostEqual(conditional[(HANDS[1], HANDS[2])], 0.25)
        self.assertAlmostEqual(
            conditional[(SECOND_HANDS[1], SECOND_HANDS[2])],
            0.75,
        )

    def test_information_hides_opponents_and_range_but_team_key_shares_members(self) -> None:
        deal0 = MultiwayRiverDeal(HANDS)
        deal1 = MultiwayRiverDeal((HANDS[0], SECOND_HANDS[1], HANDS[2]))
        deal2 = MultiwayRiverDeal((HANDS[0], HANDS[1], SECOND_HANDS[2]))
        game = three_player_game(
            deals=(deal0, deal1, deal2),
            weights=(1.0, 1.0, 1.0),
        )
        states = tuple(game.initial_state().apply_action(deal) for deal in (deal0, deal1, deal2))
        individual = tuple(state.information_state_key(0) for state in states)
        self.assertEqual(individual[0], individual[1])
        self.assertEqual(individual[0], individual[2])

        team = tuple(
            state.coalition_information_state_key((0, 1)) for state in states
        )
        self.assertNotEqual(team[0], team[1])
        self.assertEqual(team[0], team[2])

        reweighted = game.with_joint_weights({deal0: 9.0, deal1: 1.0, deal2: 1.0})
        self.assertEqual(game.structural_digest, reweighted.structural_digest)
        self.assertNotEqual(game.provenance_digest, reweighted.provenance_digest)
        self.assertEqual(
            states[0].information_state_key(0),
            reweighted.initial_state().apply_action(deal0).information_state_key(0),
        )

    def test_information_key_remembers_own_check_before_facing_bet(self) -> None:
        state = dealt(three_player_game()).apply_action(CHECK).apply_action(BET)
        state = state.apply_action(CALL)
        self.assertEqual(state.current_player, 0)
        key = state.information_state_key(0)
        self.assertIn("p0:check/p1:bet/p2:call", key)

    def test_invalid_overlap_board_and_stack_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "overlap"):
            MultiwayRiverDeal((HANDS[0], HANDS[0], HANDS[2]))
        with self.assertRaisesRegex(ValueError, "public board"):
            MultiwayRiverHoldem.from_joint_weights(
                board=BOARD,
                pot=12.0,
                stacks=(30.0,) * 3,
                bet_size=3.0,
                joint_weights={
                    MultiwayRiverDeal(
                        (
                            make_hole("2c", "3c"),
                            HANDS[1],
                            HANDS[2],
                        )
                    ): 1.0
                },
            )
        with self.assertRaisesRegex(ValueError, "cannot exceed"):
            three_player_game(scale=1.0).__class__.from_joint_weights(
                board=BOARD,
                pot=12.0,
                stacks=(2.0, 30.0, 30.0),
                bet_size=3.0,
                joint_weights={MultiwayRiverDeal(HANDS): 1.0},
            )

    def test_two_through_six_players_have_exact_cyclic_order(self) -> None:
        all_hands = (
            make_hole("As", "Ad"),
            make_hole("Ks", "Kd"),
            make_hole("Ts", "Td"),
            make_hole("8s", "8d"),
            make_hole("6s", "6d"),
            make_hole("4s", "4d"),
        )
        for count in range(2, 7):
            deal = MultiwayRiverDeal(all_hands[:count])
            game = MultiwayRiverHoldem.from_joint_weights(
                board=BOARD,
                pot=12.0,
                stacks=(30.0,) * count,
                bet_size=3.0,
                joint_weights={deal: 1.0},
            )
            root = game.initial_state()
            self.assertEqual(root.current_player, CHANCE_PLAYER)
            self.assertAlmostEqual(sum(p for _, p in root.chance_outcomes()), 1.0)
            state = root.apply_action(deal)
            bettor = count - 1
            for _ in range(bettor):
                state = state.apply_action(CHECK)
            state = state.apply_action(BET)
            observed: list[int] = []
            while state.current_player >= 0:
                observed.append(state.current_player)
                state = state.apply_action(FOLD)
            self.assertEqual(observed, list(range(bettor)))
            self.assertAlmostEqual(sum(state.returns()), 0.0, places=12)


class MultiwayRiverEvaluationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.deals = (
            MultiwayRiverDeal(HANDS),
            MultiwayRiverDeal(SECOND_HANDS),
        )
        self.game = three_player_game(deals=self.deals, weights=(2.0, 1.0))

    def test_dynamic_best_response_matches_exhaustive_enumeration(self) -> None:
        from pontius.evaluation import best_response_enumerated

        for player in range(3):
            dynamic, _ = best_response(self.game, {}, player)
            enumerated, _ = best_response_enumerated(self.game, {}, player)
            self.assertAlmostEqual(dynamic, enumerated, places=12)

    def test_dependency_tape_matches_full_multiplayer_evaluation(self) -> None:
        source_solver = TabularCFR(self.game, variant="dcfr")
        source_solver.run(3)
        policy = source_solver.average_strategy()
        target = self.game.with_joint_weights({self.deals[0]: 1.0, self.deals[1]: 4.0})
        tape = CompiledPolicyDependencyTape(
            self.game,
            policy,
            universe_games=(target,),
        )
        result = tape.recertify_game(target, mode="dense")
        expected = evaluate_profile(target, policy)
        assert_evaluation_equal(self, result.evaluation, expected)
        self.assertIsNone(result.evaluation.exploitability)
        for player in range(3):
            value, actions = best_response(target, policy, player)
            self.assertAlmostEqual(result.evaluation.best_response_values[player], value)
            self.assertEqual(result.best_response_actions[player], actions)

    def test_policy_delta_tape_matches_full_multiplayer_evaluation(self) -> None:
        source_solver = TabularCFR(self.game, variant="dcfr")
        source_solver.run(2)
        candidate_solver = TabularCFR(self.game, variant="lcfr")
        candidate_solver.run(7)
        source = source_solver.average_strategy()
        candidate = candidate_solver.average_strategy()
        result = CompiledPolicyDeltaTape(self.game, source).recertify_policy(
            candidate,
            mode="dense",
        )
        assert_evaluation_equal(self, result.evaluation, evaluate_profile(self.game, candidate))

    def test_positive_payoff_scale_preserves_normalized_metrics_and_actions(self) -> None:
        scaled = three_player_game(deals=self.deals, weights=(2.0, 1.0), scale=4.0)
        base_evaluation = evaluate_profile(self.game, {})
        scaled_evaluation = evaluate_profile(scaled, {})
        for base, larger in zip(
            base_evaluation.deviation_gains,
            scaled_evaluation.deviation_gains,
            strict=True,
        ):
            self.assertAlmostEqual(larger, 4.0 * base, places=10)
        self.assertAlmostEqual(
            scaled_evaluation.nash_conv / scaled.payoff_span,
            base_evaluation.nash_conv / self.game.payoff_span,
            places=12,
        )

        def action_signature(actions: dict[str, object]) -> dict[str, object]:
            return {
                re.sub(r"structure=[0-9a-f]+", "structure=*", key): action
                for key, action in actions.items()
            }

        for player in range(3):
            _, base_actions = best_response(self.game, {}, player)
            _, scaled_actions = best_response(scaled, {}, player)
            self.assertEqual(action_signature(base_actions), action_signature(scaled_actions))


if __name__ == "__main__":
    unittest.main()
