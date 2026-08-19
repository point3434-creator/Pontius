from __future__ import annotations

import unittest
from dataclasses import dataclass

from pontius.cfr import TabularCFR
from pontius.dependency_tape import (
    CompiledPolicyDependencyTape,
    assess_finite_policy_reuse,
)
from pontius.evaluation import (
    EvaluationResult,
    best_response,
    collect_information_sets,
    evaluate_profile,
)
from pontius.game import Action, CHANCE_PLAYER, GameState
from pontius.kuhn import KuhnPoker
from pontius.river import (
    BET,
    CALL,
    FOLD,
    RiverDeal,
    RiverHoldem,
    make_hole,
    parse_cards,
)
from pontius.river_context import CONTEXT_FAMILIES, generate_river_contexts
from pontius.river_incremental import (
    RiverPolicyEvaluationCache,
    make_support_swap_perturbation,
)
from pontius.river_range_reuse import make_blocker_perturbation


def _assert_evaluation_equal(
    test: unittest.TestCase,
    actual: EvaluationResult,
    expected: EvaluationResult,
) -> None:
    for actual_values, expected_values in (
        (actual.utilities, expected.utilities),
        (actual.best_response_values, expected.best_response_values),
        (actual.deviation_gains, expected.deviation_gains),
    ):
        for left, right in zip(actual_values, expected_values, strict=True):
            test.assertAlmostEqual(left, right, places=10)
    test.assertAlmostEqual(actual.nash_conv, expected.nash_conv, places=10)
    test.assertEqual(actual.exploitability is None, expected.exploitability is None)
    if actual.exploitability is not None and expected.exploitability is not None:
        test.assertAlmostEqual(actual.exploitability, expected.exploitability, places=10)


def _finite_policy(game: RiverHoldem, iterations: int = 7) -> dict:
    solver = TabularCFR(game, variant="dcfr")
    solver.run(iterations)
    return solver.average_strategy()


def _blocker_flip_pair() -> tuple[RiverHoldem, RiverHoldem, RiverDeal, tuple[int, int]]:
    board = parse_cards("2c", "7d", "9h", "Js", "Qc")
    common = RiverDeal(make_hole("Ac", "Ad"), make_hole("Kh", "Kd"))
    target_hand = make_hole("Ah", "3h")
    nuts = RiverDeal(make_hole("Ts", "Ks"), target_hand)
    bluff = RiverDeal(make_hole("4s", "5s"), target_hand)
    arguments = {
        "board": board,
        "pot": 10.0,
        "stacks": (20.0, 20.0),
        "bet_size": 5.0,
    }
    source = RiverHoldem.from_joint_weights(
        **arguments,
        joint_weights={common: 0.99, nuts: 0.01},
    )
    target = RiverHoldem.from_joint_weights(
        **arguments,
        joint_weights={common: 0.99, bluff: 0.01},
    )
    return source, target, nuts, target_hand


@dataclass(frozen=True, slots=True)
class _WeightedRootState:
    base: GameState
    outcomes: tuple[tuple[Action, float], ...]

    @property
    def current_player(self) -> int:
        return CHANCE_PLAYER

    def legal_actions(self) -> tuple[Action, ...]:
        return ()

    def chance_outcomes(self) -> tuple[tuple[Action, float], ...]:
        return self.outcomes

    def apply_action(self, action: Action) -> GameState:
        if action not in dict(self.outcomes):
            raise ValueError(f"unknown weighted root action {action!r}")
        return self.base.apply_action(action)

    def information_state_key(self, player: int) -> str:
        raise ValueError("weighted chance root has no information state")

    def returns(self) -> tuple[float, ...]:
        raise ValueError("weighted chance root is not terminal")


@dataclass(frozen=True, slots=True)
class _WeightedKuhn:
    num_players: int
    outcomes: tuple[tuple[Action, float], ...]

    def initial_state(self) -> GameState:
        return _WeightedRootState(
            base=KuhnPoker(self.num_players).initial_state(),
            outcomes=self.outcomes,
        )


class DependencyTapeTests(unittest.TestCase):
    def test_generated_family_matrix_matches_both_exact_controls(self) -> None:
        comparisons = 0
        for sequential_raise in (False, True):
            contexts = generate_river_contexts(
                groups=1,
                seed=7331,
                hands_per_player=5,
                families=CONTEXT_FAMILIES,
                splits=("development", "validation", "test"),
                sequential_raise=sequential_raise,
            )
            for context_index, context in enumerate(contexts):
                source = context.game
                reweight, _ = make_blocker_perturbation(
                    source,
                    player=0,
                    root_tv_budget=0.01,
                    maximum_donor_fraction=0.75,
                )
                support, _ = make_support_swap_perturbation(source, player=1)
                policy = _finite_policy(source, iterations=1 + context_index)
                tape = CompiledPolicyDependencyTape(
                    source,
                    policy,
                    universe_games=(reweight, support),
                )
                specialized = RiverPolicyEvaluationCache(source, policy)
                for target in (reweight, support):
                    sparse = tape.recertify_game(target, mode="sparse")
                    dense = tape.recertify_game(target, mode="dense")
                    full = evaluate_profile(target, policy)
                    _assert_evaluation_equal(self, sparse.evaluation, full)
                    _assert_evaluation_equal(self, dense.evaluation, full)
                    _assert_evaluation_equal(
                        self,
                        sparse.evaluation,
                        specialized.recertify(target).evaluation,
                    )
                    self.assertEqual(
                        sparse.best_response_actions,
                        dense.best_response_actions,
                    )
                    comparisons += 1
        self.assertEqual(comparisons, 16)

    def test_flat_tape_matches_full_and_specialized_river_controls(self) -> None:
        source = generate_river_contexts(
            groups=1,
            seed=17,
            hands_per_player=4,
            families=("balanced",),
            splits=("development", "validation", "test"),
            sequential_raise=True,
        )[0].game
        target, _ = make_blocker_perturbation(
            source,
            player=0,
            root_tv_budget=0.01,
            maximum_donor_fraction=0.75,
        )
        policy = _finite_policy(source)
        tape = CompiledPolicyDependencyTape(
            source,
            policy,
            universe_games=(target,),
        )

        _assert_evaluation_equal(
            self,
            tape.source_result.evaluation,
            evaluate_profile(source, policy),
        )
        specialized = RiverPolicyEvaluationCache(source, policy).recertify(target)
        results = {
            mode: tape.recertify_game(target, mode=mode)
            for mode in ("sparse", "dense", "auto")
        }
        for result in results.values():
            _assert_evaluation_equal(
                self,
                result.evaluation,
                evaluate_profile(target, policy),
            )
            _assert_evaluation_equal(
                self,
                result.evaluation,
                specialized.evaluation,
            )

        self.assertEqual(results["auto"].diagnostics.execution_mode, "sparse")
        self.assertLess(
            results["sparse"].diagnostics.recomputed_nodes,
            results["dense"].diagnostics.recomputed_nodes,
        )
        topology = tape.topology_summary()
        self.assertTrue(topology["dependencies_are_topological"])
        self.assertGreater(topology["contiguous_runtime_bytes"], 0)
        self.assertTrue(tape.node_kinds.readonly)
        for node in range(len(tape.node_kinds)):
            start = tape.input_offsets[node]
            end = start + tape.input_counts[node]
            self.assertTrue(all(tape.edge_inputs[edge] < node for edge in range(start, end)))

    def test_support_changes_and_call_order_remain_source_relative(self) -> None:
        source = generate_river_contexts(
            groups=1,
            seed=29,
            hands_per_player=5,
            families=("blocker_stress",),
            splits=("development", "validation", "test"),
            sequential_raise=True,
        )[0].game
        target0, metadata0 = make_support_swap_perturbation(source, player=0)
        target1, metadata1 = make_support_swap_perturbation(source, player=1)
        self.assertTrue(metadata0["new_private_hand_was_absent"])
        self.assertTrue(metadata1["new_private_hand_was_absent"])
        policy = _finite_policy(source, iterations=5)
        tape = CompiledPolicyDependencyTape(
            source,
            policy,
            universe_games=(target0, target1),
        )

        first0 = tape.recertify_game(target0, mode="sparse")
        first1 = tape.recertify_game(target1, mode="dense")
        second0 = tape.recertify_game(target0, mode="dense")
        source_again = tape.recertify_game(source, mode="sparse")

        for target, result in ((target0, first0), (target1, first1)):
            full = evaluate_profile(target, policy)
            specialized = RiverPolicyEvaluationCache(source, policy).recertify(target)
            _assert_evaluation_equal(self, result.evaluation, full)
            _assert_evaluation_equal(self, result.evaluation, specialized.evaluation)
            self.assertGreaterEqual(result.diagnostics.best_response_action_flips, 1)
        _assert_evaluation_equal(self, first0.evaluation, second0.evaluation)
        self.assertEqual(first0.best_response_actions, second0.best_response_actions)
        _assert_evaluation_equal(
            self,
            source_again.evaluation,
            tape.source_result.evaluation,
        )

    def test_known_blocker_change_propagates_information_set_action_flip(self) -> None:
        source, target, nuts, target_hand = _blocker_flip_pair()
        policy = {}
        for game in (source, target):
            for key, actions in collect_information_sets(game, 0).items():
                policy[key] = {
                    action: float(action == BET) for action in actions
                }
        tape = CompiledPolicyDependencyTape(
            source,
            policy,
            universe_games=(target,),
        )
        result = tape.recertify_game(target, mode="sparse")
        target_key = (
            source.initial_state()
            .apply_action(nuts)
            .apply_action(BET)
            .information_state_key(1)
        )

        self.assertEqual(tape.source_result.best_response_actions[1][target_key], FOLD)
        self.assertEqual(result.best_response_actions[1][target_key], CALL)
        self.assertGreaterEqual(result.diagnostics.best_response_action_flips, 1)
        _assert_evaluation_equal(self, result.evaluation, evaluate_profile(target, policy))
        self.assertAlmostEqual(source.total_variation(target), 0.01)
        self.assertAlmostEqual(
            source.conditional_opponent_total_variation(
                target,
                player=1,
                own_hand=target_hand,
            ),
            1.0,
        )

    def test_factorized_dense_likelihood_update_uses_dense_path_exactly(self) -> None:
        source = generate_river_contexts(
            groups=1,
            seed=41,
            hands_per_player=8,
            families=("correlated",),
            splits=("development", "validation", "test"),
            sequential_raise=True,
        )[0].game
        hands = tuple(source.marginal_distribution(0))
        likelihood = {
            hand: 0.5 + (index + 1) / len(hands)
            for index, hand in enumerate(hands)
        }
        target = RiverHoldem.from_joint_weights(
            board=source.board,
            pot=source.pot,
            stacks=source.stacks,
            bet_size=source.bet_size,
            raise_to=source.raise_to,
            joint_weights={
                deal: probability * likelihood[deal.player0]
                for deal, probability in source.deals
            },
        )
        policy = _finite_policy(source, iterations=3)
        tape = CompiledPolicyDependencyTape(
            source,
            policy,
            universe_games=(target,),
            dense_threshold=0.25,
        )
        result = tape.recertify_game(target, mode="auto")

        self.assertEqual(result.diagnostics.execution_mode, "dense")
        self.assertGreater(
            result.diagnostics.changed_root_outcomes,
            len(source.deals) // 2,
        )
        _assert_evaluation_equal(self, result.evaluation, evaluate_profile(target, policy))

    def test_multiplayer_best_response_tape_matches_three_player_full_evaluation(self) -> None:
        base = KuhnPoker(3).initial_state()
        uniform = tuple(base.chance_outcomes())
        source = _WeightedKuhn(3, uniform)
        probabilities = dict(uniform)
        actions = tuple(probabilities)
        probabilities[actions[0]] -= 0.01
        probabilities[actions[-1]] += 0.01
        target = _WeightedKuhn(3, tuple(probabilities.items()))
        solver = TabularCFR(source, variant="lcfr")
        solver.run(5)
        policy = solver.average_strategy()
        tape = CompiledPolicyDependencyTape(
            source,
            policy,
            universe_games=(target,),
        )
        result = tape.recertify_game(target, mode="sparse")

        _assert_evaluation_equal(self, result.evaluation, evaluate_profile(target, policy))
        self.assertIsNone(result.evaluation.exploitability)
        for player in range(3):
            value, actions_by_key = best_response(target, policy, player)
            self.assertAlmostEqual(
                result.evaluation.best_response_values[player],
                value,
                places=10,
            )
            for key, action in actions_by_key.items():
                self.assertEqual(result.best_response_actions[player][key], action)

    def test_absolute_and_transfer_budgets_cannot_mask_each_other(self) -> None:
        def evaluation(exploitability: float | None) -> EvaluationResult:
            return EvaluationResult(
                utilities=(0.0, 0.0),
                best_response_values=(0.0, 0.0),
                deviation_gains=(0.0, 0.0),
                nash_conv=0.0,
                exploitability=exploitability,
            )

        source = evaluation(0.02)
        target = evaluation(0.03)
        absolute_failure = assess_finite_policy_reuse(
            source,
            target,
            absolute_quality_budget=0.025,
            transfer_damage_budget=1.0,
        )
        transfer_failure = assess_finite_policy_reuse(
            source,
            target,
            absolute_quality_budget=1.0,
            transfer_damage_budget=0.005,
        )
        accepted = assess_finite_policy_reuse(
            source,
            target,
            absolute_quality_budget=0.04,
            transfer_damage_budget=0.02,
        )

        self.assertFalse(absolute_failure.accepted)
        self.assertFalse(absolute_failure.absolute_quality_passes)
        self.assertTrue(absolute_failure.transfer_damage_passes)
        self.assertFalse(transfer_failure.accepted)
        self.assertTrue(transfer_failure.absolute_quality_passes)
        self.assertFalse(transfer_failure.transfer_damage_passes)
        self.assertTrue(accepted.accepted)
        self.assertAlmostEqual(accepted.signed_transfer_damage, 0.01)
        with self.assertRaisesRegex(ValueError, "numerical guard"):
            assess_finite_policy_reuse(
                source,
                target,
                absolute_quality_budget=1.0,
                transfer_damage_budget=1.0,
                numerical_guard=1e-6,
            )
        with self.assertRaisesRegex(ValueError, "two players"):
            assess_finite_policy_reuse(
                evaluation(None),
                evaluation(None),
                absolute_quality_budget=1.0,
                transfer_damage_budget=1.0,
            )

    def test_invalid_structure_probabilities_and_modes_are_rejected(self) -> None:
        source, target, _, _ = _blocker_flip_pair()
        tape = CompiledPolicyDependencyTape(source, {}, universe_games=(target,))
        different_structure = RiverHoldem.from_joint_weights(
            board=source.board,
            pot=source.pot + 1.0,
            stacks=source.stacks,
            bet_size=source.bet_size,
            joint_weights=source.joint_distribution(),
        )
        unknown = RiverDeal(make_hole("2d", "3d"), make_hole("4d", "5d"))

        with self.assertRaisesRegex(ValueError, "structure"):
            tape.recertify_game(different_structure)
        with self.assertRaisesRegex(ValueError, "outside the topology epoch"):
            tape.recertify({unknown: 1.0})
        with self.assertRaisesRegex(ValueError, "sum to one"):
            tape.recertify({source.deals[0][0]: 0.5})
        with self.assertRaisesRegex(ValueError, "execution mode"):
            tape.recertify_game(target, mode="future")  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
