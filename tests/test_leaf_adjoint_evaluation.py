from __future__ import annotations

import importlib.util
import unittest

from pontius.leaf_adjoint_cfr import build_leaf_adjoint_terminal_automata
from pontius.leaf_adjoint_evaluation import (
    evaluate_leaf_adjoint_profile,
    evaluate_leaf_adjoint_seat,
)
from pontius.public_policy_tt import representative_public_tree
from pontius.showdown_value_rank_screen import _rank_codes
import tests.test_sparse_open_mode_cfr as sparse_fixture


@unittest.skipUnless(importlib.util.find_spec("scipy"), "optional SciPy screen")
class LeafAdjointEvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        source = sparse_fixture.SparseOpenModeCFRTests
        source.setUpClass()
        cls.dense_layout = source.layout
        cls.belief = source.belief
        cls.workspace = source.workspace
        cls.sparse = source.sparse
        cls.policy = source.policy
        cls.topology = representative_public_tree(
            source.belief,
            pot=12.0,
            stack=30.0,
            bet_size=3.0,
        )
        codes = tuple(values.astype("int32") for values in _rank_codes(
            source.board,
            source.belief.hands_by_player,
        ))
        cls.automata = build_leaf_adjoint_terminal_automata(
            cls.topology,
            codes,
            pot=12.0,
            bet_size=3.0,
        )

    def test_profile_utilities_responses_and_nashconv_match_dense_oracle(self) -> None:
        expected = self.dense_layout.evaluate(self.policy)
        actual = evaluate_leaf_adjoint_profile(
            self.topology,
            self.workspace,
            self.sparse,
            self.policy,
            self.automata,
            hands_by_player=self.belief.hands_by_player,
            maximum_feature_width_per_batch=96,
        )

        for first, second in zip(
            actual.evaluation.utilities,
            expected.evaluation.utilities,
            strict=True,
        ):
            self.assertAlmostEqual(first, second, places=11)
        for first, second in zip(
            actual.evaluation.best_response_values,
            expected.evaluation.best_response_values,
            strict=True,
        ):
            self.assertAlmostEqual(first, second, places=11)
        for first, second in zip(
            actual.evaluation.deviation_gains,
            expected.evaluation.deviation_gains,
            strict=True,
        ):
            self.assertAlmostEqual(first, second, places=11)
        self.assertAlmostEqual(
            actual.evaluation.nash_conv,
            expected.evaluation.nash_conv,
            places=11,
        )
        self.assertLessEqual(actual.zero_sum_residual, 2e-12)
        self.assertEqual(len(actual.seats), 6)
        self.assertEqual(len(actual.best_response_actions), 6)

    def test_every_selected_leaf_response_attains_the_dense_best_value(self) -> None:
        actual = evaluate_leaf_adjoint_profile(
            self.topology,
            self.workspace,
            self.sparse,
            self.policy,
            self.automata,
            hands_by_player=self.belief.hands_by_player,
            maximum_feature_width_per_batch=96,
        )
        schema = self.dense_layout.information_schema()
        dense_response = self.dense_layout.evaluate(self.policy)
        for target, selected in enumerate(actual.best_response_actions):
            candidate = {
                key: dict(distribution)
                for key, distribution in self.policy.items()
            }
            for key, action in selected.items():
                candidate[key] = {
                    legal: float(legal == action) for legal in schema[key]
                }
            value = self.dense_layout._expected_utilities(
                self.dense_layout._prepare_policy(candidate)
            )[target]
            self.assertAlmostEqual(
                value,
                dense_response.evaluation.best_response_values[target],
                places=11,
            )
            self.assertAlmostEqual(
                value,
                actual.evaluation.best_response_values[target],
                places=11,
            )
            self.assertEqual(len(selected), 32 * 4)
            self.assertGreaterEqual(actual.seats[target].minimum_action_gap, 0.0)
            self.assertEqual(actual.seats[target].terminal_contractions, 193)

    def test_seat_contract_rejects_wrong_target_and_external_axes(self) -> None:
        from pontius.incremental_policy_tt import compile_policy_probability_tape

        probabilities = compile_policy_probability_tape(
            self.topology,
            self.belief.hands_by_player,
            self.policy,
        )
        with self.assertRaisesRegex(ValueError, "outside"):
            evaluate_leaf_adjoint_seat(
                self.topology,
                self.workspace,
                self.sparse,
                probabilities,
                self.automata[0],
                target_player=6,
                hands_by_player=self.belief.hands_by_player,
            )
        shortened = (
            self.belief.hands_by_player[0][:-1],
            *self.belief.hands_by_player[1:],
        )
        with self.assertRaisesRegex(ValueError, "hand axes"):
            evaluate_leaf_adjoint_seat(
                self.topology,
                self.workspace,
                self.sparse,
                probabilities,
                self.automata[0],
                target_player=0,
                hands_by_player=shortened,
            )


if __name__ == "__main__":
    unittest.main()
