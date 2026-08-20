from __future__ import annotations

from dataclasses import dataclass
import unittest

import numpy as np

from pontius.batched_factor_tt_contraction import contract_weighted_sum
from pontius.clean_fringe_tt import (
    compile_clean_fringe_delta_terms,
    compile_clean_fringe_plan,
)
from pontius.factor_tt_contraction import FactorTTBeliefWorkspace, FactorTTTopology
from pontius.factorized_belief import FactorizedCardBelief
from pontius.incremental_policy_tt import (
    PolicyDeltaTTCache,
    PolicyDeltaTTPlan,
    compile_policy_delta_tt_cache_from_probabilities,
    compile_policy_probability_tape,
    plan_policy_delta_tt_from_probabilities,
)
from pontius.public_policy_tt import dense_public_policy_root
from pontius.public_tree_tensor import PublicTreeTensorEvaluator
from pontius.river import HoleCards, parse_cards
from pontius.river_multiway import MultiwayRiverDeal, MultiwayRiverHoldem
from pontius.showdown_value_rank_screen import (
    _payoff_operator,
    _policies,
    _rank_codes,
    _terminal_groups,
)
from pontius.signed_clean_fringe_tt import (
    changed_reach_modes,
    compile_rank_optimized_clean_fringe_plan,
    compile_signed_clean_fringe_delta_terms,
    compose_signed_clean_fringe_delta_train,
    evaluate_reach_weighted_fringe_bound,
)
from pontius.tensor_train import TensorTrain


@dataclass(frozen=True)
class _Fixture:
    belief: FactorizedCardBelief
    layout: PublicTreeTensorEvaluator
    dense_terminals: tuple[dict[str, np.ndarray], ...]
    caches: tuple[PolicyDeltaTTCache, ...]
    baseline: dict[str, dict[object, float]]
    baseline_probabilities: tuple[np.ndarray | None, ...]


def _fixture(*, maximum_rank: int | None = None) -> _Fixture:
    board = parse_cards("2c", "7d", "9h", "Js", "Qc")
    available = tuple(card for card in range(52) if card not in set(board))
    cursor = 0
    axes: list[tuple[HoleCards, ...]] = []
    weights = []
    for player in range(3):
        hands = []
        row = []
        for hand_index in range(2):
            hands.append(tuple(sorted((available[cursor], available[cursor + 1]))))
            cursor += 2
            row.append(float(1 + player + hand_index))
        axes.append(tuple(hands))
        weights.append([row])
    belief = FactorizedCardBelief(
        hands_by_player=tuple(axes),
        mixture_weights=[1.0],
        unary_weights=tuple(weights),
        board=board,
    )
    materialized = belief.materialize()
    joint = {
        MultiwayRiverDeal(
            tuple(belief.hands_by_player[p][assignment[p]] for p in range(3))
        ): float(probability)
        for assignment, probability in zip(
            materialized.assignments, materialized.probabilities, strict=True
        )
    }
    game = MultiwayRiverHoldem.from_joint_weights(
        board=board,
        pot=12.0,
        stacks=(30.0,) * 3,
        bet_size=3.0,
        joint_weights=joint,
    )
    layout = PublicTreeTensorEvaluator(game)
    groups = _terminal_groups(layout)
    rank_codes = _rank_codes(board, layout.hands_by_player)
    dense: list[dict[str, np.ndarray]] = [dict() for _ in range(3)]
    trains: list[dict[str, TensorTrain]] = [dict() for _ in range(3)]
    for group in groups:
        values = _payoff_operator(
            group=group,
            rank_codes=rank_codes,
            pot=game.pot,
            bet_size=game.bet_size,
        )
        for player in range(3):
            dense[player][group.key] = values[player]
            trains[player][group.key] = TensorTrain.from_dense(values[player])
    baseline = _policies(layout.information_schema(), 17)["hashed_dense"]
    baseline_probabilities = compile_policy_probability_tape(
        layout,
        layout.hands_by_player,
        baseline,
    )
    caches = tuple(
        compile_policy_delta_tt_cache_from_probabilities(
            layout,
            layout.hands_by_player,
            baseline_probabilities,
            trains[player],
            {key: 0.0 for key in trains[player]},
            relative_tolerance=0.0,
            maximum_rank=maximum_rank,
        )
        for player in range(3)
    )
    return _Fixture(
        belief=belief,
        layout=layout,
        dense_terminals=tuple(dense),
        caches=caches,
        baseline=baseline,
        baseline_probabilities=baseline_probabilities,
    )


def _candidate_for_seats(
    fixture: _Fixture,
    seats: tuple[int, ...],
    *,
    interpolation: float = 1.0,
) -> tuple[dict[str, dict[object, float]], PolicyDeltaTTPlan]:
    candidate = {key: dict(row) for key, row in fixture.baseline.items()}
    for node in fixture.layout.nodes:
        if node.player not in seats:
            continue
        for key in node.information_keys:
            old = fixture.baseline[key]
            reversed_values = tuple(reversed(tuple(old[action] for action in node.actions)))
            candidate[key] = {
                action: (1.0 - interpolation) * old[action]
                + interpolation * replacement
                for action, replacement in zip(
                    node.actions, reversed_values, strict=True
                )
            }
    probabilities = compile_policy_probability_tape(
        fixture.layout,
        fixture.layout.hands_by_player,
        candidate,
    )
    plan = plan_policy_delta_tt_from_probabilities(
        fixture.caches[0],
        probabilities,
    )
    return candidate, plan


def _workspace(fixture: _Fixture) -> FactorTTBeliefWorkspace:
    topology = FactorTTTopology.compile(fixture.belief, split_index=1)
    return FactorTTBeliefWorkspace.compile(topology, fixture.belief)


class SignedCleanFringeTTTests(unittest.TestCase):
    def test_unilateral_overlapping_edits_halve_width_and_match_oracles(self) -> None:
        fixture = _fixture()
        candidate, policy_plan = _candidate_for_seats(fixture, (1,))
        cache = fixture.caches[0]
        fringe = compile_clean_fringe_plan(cache, policy_plan)
        modes = changed_reach_modes(cache, policy_plan)
        signed = compile_signed_clean_fringe_delta_terms(
            cache,
            fringe,
            changed_modes=modes,
            belief_components=fixture.belief.component_count,
            split_index=1,
        )
        two_sided = compile_clean_fringe_delta_terms(
            cache,
            fringe,
            belief_components=fixture.belief.component_count,
            split_index=1,
        )
        materialized = compose_signed_clean_fringe_delta_train(
            cache,
            fringe,
            changed_modes=modes,
            belief_components=fixture.belief.component_count,
            split_index=1,
        )
        self.assertIsNotNone(materialized.train)
        assert materialized.train is not None
        expected_dense = dense_public_policy_root(
            fixture.layout,
            fixture.layout.hands_by_player,
            candidate,
            fixture.dense_terminals[0],
        ) - dense_public_policy_root(
            fixture.layout,
            fixture.layout.hands_by_player,
            fixture.baseline,
            fixture.dense_terminals[0],
        )
        np.testing.assert_allclose(
            materialized.train.to_dense(), expected_dense, atol=2e-12, rtol=0.0
        )
        streamed = contract_weighted_sum(
            _workspace(fixture),
            signed.terms,
            maximum_feature_width_per_batch=4,
        ).expectation
        exact = (
            fixture.layout._expected_utilities(
                fixture.layout._prepare_policy(candidate)
            )[0]
            - fixture.layout._expected_utilities(
                fixture.layout._prepare_policy(fixture.baseline)
            )[0]
        )
        self.assertAlmostEqual(streamed, exact, delta=2e-12)
        self.assertEqual(modes, (1,))
        self.assertEqual(2 * len(signed.terms), len(two_sided.terms))
        self.assertEqual(
            2 * signed.total_component_rank_width,
            two_sided.total_component_rank_width,
        )

    def test_ordered_telescope_is_exact_when_two_seats_change(self) -> None:
        fixture = _fixture()
        candidate, policy_plan = _candidate_for_seats(fixture, (1, 2))
        cache = fixture.caches[0]
        modes = changed_reach_modes(cache, policy_plan)
        fringe = compile_clean_fringe_plan(cache, policy_plan)
        materialized = compose_signed_clean_fringe_delta_train(
            cache,
            fringe,
            changed_modes=modes,
            belief_components=fixture.belief.component_count,
            split_index=1,
        )
        self.assertIsNotNone(materialized.train)
        assert materialized.train is not None
        expected = dense_public_policy_root(
            fixture.layout,
            fixture.layout.hands_by_player,
            candidate,
            fixture.dense_terminals[0],
        ) - dense_public_policy_root(
            fixture.layout,
            fixture.layout.hands_by_player,
            fixture.baseline,
            fixture.dense_terminals[0],
        )
        np.testing.assert_allclose(
            materialized.train.to_dense(), expected, atol=3e-12, rtol=0.0
        )
        self.assertEqual(modes, (1, 2))

    def test_rank_optimized_cut_is_no_wider_and_remains_exact(self) -> None:
        fixture = _fixture()
        candidate, policy_plan = _candidate_for_seats(fixture, (1,))
        optimized = compile_rank_optimized_clean_fringe_plan(
            fixture.caches,
            policy_plan,
            belief_components=fixture.belief.component_count,
            split_index=1,
        )
        self.assertLessEqual(
            optimized.optimized_all_value_component_rank_width,
            optimized.immediate_all_value_component_rank_width,
        )
        signed = compile_signed_clean_fringe_delta_terms(
            fixture.caches[0],
            optimized.optimized_plan,
            changed_modes=optimized.changed_reach_modes,
            belief_components=fixture.belief.component_count,
            split_index=1,
        )
        streamed = contract_weighted_sum(
            _workspace(fixture),
            signed.terms,
            maximum_feature_width_per_batch=4,
        ).expectation
        exact = (
            fixture.layout._expected_utilities(
                fixture.layout._prepare_policy(candidate)
            )[0]
            - fixture.layout._expected_utilities(
                fixture.layout._prepare_policy(fixture.baseline)
            )[0]
        )
        self.assertAlmostEqual(streamed, exact, delta=3e-12)

        frontier = set(optimized.optimized_plan.frontier_nodes)
        for node in frontier:
            parent = int(fixture.caches[0].parents[node])
            while parent >= 0:
                self.assertNotIn(parent, frontier)
                parent = int(fixture.caches[0].parents[parent])
        self.assertFalse(
            set(optimized.expanded_clean_nodes) & set(policy_plan.dirty_nodes)
        )

    def test_reach_weighted_bound_is_safe_and_scales_with_edit_mass(self) -> None:
        fixture = _fixture(maximum_rank=1)
        workspace = _workspace(fixture)
        candidate, policy_plan = _candidate_for_seats(fixture, (1,))
        fringe = compile_clean_fringe_plan(fixture.caches[0], policy_plan)
        signed = compile_signed_clean_fringe_delta_terms(
            fixture.caches[0],
            fringe,
            changed_modes=(1,),
            belief_components=fixture.belief.component_count,
            split_index=1,
        )
        estimate = contract_weighted_sum(
            workspace,
            signed.terms,
            maximum_feature_width_per_batch=4,
        ).expectation
        exact = (
            fixture.layout._expected_utilities(
                fixture.layout._prepare_policy(candidate)
            )[0]
            - fixture.layout._expected_utilities(
                fixture.layout._prepare_policy(fixture.baseline)
            )[0]
        )
        bound = evaluate_reach_weighted_fringe_bound(
            workspace,
            fixture.caches[0],
            signed,
            maximum_feature_width_per_batch=4,
        )
        self.assertLessEqual(abs(estimate - exact), bound.upper_bound + 2e-12)
        self.assertLessEqual(
            bound.upper_bound,
            signed.legacy_shared_fringe_error_bound + 2e-12,
        )

        _, tiny_plan = _candidate_for_seats(
            fixture,
            (1,),
            interpolation=1e-6,
        )
        tiny_fringe = compile_clean_fringe_plan(fixture.caches[0], tiny_plan)
        tiny_signed = compile_signed_clean_fringe_delta_terms(
            fixture.caches[0],
            tiny_fringe,
            changed_modes=(1,),
            belief_components=fixture.belief.component_count,
            split_index=1,
        )
        tiny_bound = evaluate_reach_weighted_fringe_bound(
            workspace,
            fixture.caches[0],
            tiny_signed,
            maximum_feature_width_per_batch=4,
        )
        self.assertLess(tiny_bound.upper_bound, bound.upper_bound * 1e-4)


if __name__ == "__main__":
    unittest.main()
