from __future__ import annotations

import unittest

from pontius.cfr import TabularCFR
from pontius.depth_limited import PolicyContinuationValues
from pontius.evaluation import expected_utilities_from_state
from pontius.river import RiverDeal, make_hole, parse_cards
from pontius.river_multi_size import MultiSizeRiverHoldem
from pontius.river_selective import (
    MultiSizeExpansionMask,
    complete_information_schema,
    compose_selective_policy,
)
from pontius.selective_tree import (
    SelectiveExpansionGame,
    collect_selective_cutoff_states,
    full_tree_state_count,
)


def _game() -> MultiSizeRiverHoldem:
    board = parse_cards("2c", "7d", "9h", "Js", "Qc")
    first = RiverDeal(make_hole("Ts", "Ks"), make_hole("Ah", "3h"))
    second = RiverDeal(make_hole("4s", "5s"), make_hole("Ac", "Ad"))
    return MultiSizeRiverHoldem.from_joint_weights(
        board=board,
        pot=10.0,
        stacks=(20.0, 20.0),
        bet_sizes=(2.5, 5.0, 7.5),
        raise_to_sizes=(15.0, 20.0),
        joint_weights={first: 0.6, second: 0.4},
    )


def _uniform_blueprint(game: MultiSizeRiverHoldem) -> dict:
    return {
        key: {action: 1.0 / len(actions) for action in actions}
        for key, actions in complete_information_schema(game).items()
    }


def _mask(
    game: MultiSizeRiverHoldem,
    bets: tuple[float, ...],
    raises: tuple[float, ...],
) -> MultiSizeExpansionMask:
    return MultiSizeExpansionMask.from_amounts(
        game,
        bet_amounts=bets,
        raise_to_amounts=raises,
    )


class RiverSelectiveExpansionTests(unittest.TestCase):
    def test_unexpanded_actions_remain_legal_and_cut_to_exact_blueprint_values(self) -> None:
        game = _game()
        blueprint = _uniform_blueprint(game)
        values = PolicyContinuationValues(game.num_players, blueprint)
        selective = SelectiveExpansionGame(
            game,
            values,
            _mask(game, (5.0,), (15.0,)),
        )
        deal = game.deals[0][0]
        base_dealt = game.initial_state().apply_action(deal)
        dealt = selective.initial_state().apply_action(deal)

        self.assertEqual(tuple(dealt.legal_actions()), tuple(base_dealt.legal_actions()))
        small, medium, _ = game.bet_actions

        small_leaf = dealt.apply_action(small)
        self.assertTrue(small_leaf.is_cutoff)
        self.assertEqual(
            small_leaf.returns(),
            expected_utilities_from_state(
                game.num_players,
                base_dealt.apply_action(small),
                blueprint,
            ),
        )

        facing_medium = dealt.apply_action(medium)
        self.assertFalse(facing_medium.is_cutoff)
        self.assertEqual(
            tuple(facing_medium.legal_actions()),
            tuple(base_dealt.apply_action(medium).legal_actions()),
        )
        second_raise = game.raise_actions[1]
        raise_leaf = facing_medium.apply_action(second_raise)
        self.assertTrue(raise_leaf.is_cutoff)
        self.assertEqual(
            raise_leaf.returns(),
            expected_utilities_from_state(
                game.num_players,
                base_dealt.apply_action(medium).apply_action(second_raise),
                blueprint,
            ),
        )

    def test_zero_overlay_is_exact_no_op_and_unreached_information_sets_survive(self) -> None:
        game = _game()
        blueprint = _uniform_blueprint(game)
        full_schema = complete_information_schema(game)
        self.assertEqual(
            compose_selective_policy(blueprint, {}, full_schema),
            blueprint,
        )

        selective = SelectiveExpansionGame(
            game,
            PolicyContinuationValues(game.num_players, blueprint),
            _mask(game, (5.0,), (15.0,)),
        )
        solver = TabularCFR(selective, variant="dcfr")
        solver.warm_start(blueprint, regret_mass=1.0)
        solver.run(3)
        candidate = solver.average_strategy()
        completed = compose_selective_policy(blueprint, candidate, full_schema)

        absent = set(full_schema) - set(candidate)
        self.assertTrue(absent)
        for key in absent:
            self.assertEqual(completed[key], blueprint[key])
        for key, distribution in candidate.items():
            self.assertEqual(set(distribution), set(full_schema[key]))
            self.assertAlmostEqual(sum(completed[key].values()), 1.0)
        self.assertEqual(set(completed), set(full_schema))

    def test_full_expansion_is_identical_to_the_unwrapped_solver(self) -> None:
        game = _game()
        blueprint = _uniform_blueprint(game)
        values = PolicyContinuationValues(game.num_players, blueprint)
        selective = SelectiveExpansionGame(
            game,
            values,
            _mask(game, game.bet_sizes, game.raise_to_sizes),
        )
        direct = TabularCFR(game, variant="dcfr")
        wrapped = TabularCFR(selective, variant="dcfr")
        direct.warm_start(blueprint, regret_mass=2.5)
        wrapped.warm_start(blueprint, regret_mass=2.5)

        for _ in range(4):
            direct.step()
            wrapped.step()
            self.assertEqual(wrapped.current_strategy(), direct.current_strategy())
            self.assertEqual(wrapped.average_strategy(), direct.average_strategy())
        self.assertEqual(values.cache_size, 0)
        self.assertEqual(
            full_tree_state_count(selective.initial_state()),
            full_tree_state_count(game.initial_state()),
        )

    def test_nested_masks_have_strictly_increasing_tree_work(self) -> None:
        game = _game()
        blueprint = _uniform_blueprint(game)
        masks = (
            _mask(game, (5.0,), (15.0,)),
            _mask(game, (2.5, 5.0), (15.0,)),
            _mask(game, game.bet_sizes, (15.0,)),
            _mask(game, game.bet_sizes, game.raise_to_sizes),
        )
        counts = []
        cutoff_counts = []
        for mask in masks:
            selective = SelectiveExpansionGame(
                game,
                PolicyContinuationValues(game.num_players, blueprint),
                mask,
            )
            counts.append(full_tree_state_count(selective.initial_state()))
            cutoff_counts.append(len(collect_selective_cutoff_states(selective)))

        self.assertEqual(counts, sorted(set(counts)))
        self.assertEqual(cutoff_counts[-1], 0)
        self.assertGreater(cutoff_counts[0], cutoff_counts[-1])

    def test_mask_and_completion_reject_structural_or_schema_mismatch(self) -> None:
        game = _game()
        with self.assertRaisesRegex(ValueError, "outside the full game"):
            _mask(game, (1.0,), (15.0,))

        blueprint = _uniform_blueprint(game)
        schema = complete_information_schema(game)
        missing = dict(blueprint)
        missing.pop(next(iter(missing)))
        with self.assertRaisesRegex(ValueError, "blueprint must be complete"):
            compose_selective_policy(missing, {}, schema)


if __name__ == "__main__":
    unittest.main()

