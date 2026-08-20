from __future__ import annotations

import unittest

from pontius.factorized_belief import FactorizedCardBelief
from pontius.public_policy_tt import (
    information_schema_for_axes,
    representative_public_tree,
)
from pontius.real_policy import (
    mean_policy_total_variation,
    policy_digest,
    policy_statistics,
    splice_unilateral_best_response,
)
from pontius.river import parse_cards


def _uniform(schema: dict[str, tuple[str, ...]]) -> dict[str, dict[str, float]]:
    return {
        key: {action: 1.0 / len(actions) for action in actions}
        for key, actions in schema.items()
    }


class RealPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.board = parse_cards("2c", "7d", "9h", "Js", "Qc")
        source = (
            parse_cards("3c", "4d"),
            parse_cards("Ah", "Ad"),
            parse_cards("8c", "8d"),
        )
        self.source_axes = (source, source)
        belief = FactorizedCardBelief(
            hands_by_player=self.source_axes,
            mixture_weights=[1.0],
            unary_weights=([[1.0, 1.0, 1.0]], [[1.0, 1.0, 1.0]]),
            board=self.board,
        )
        self.layout = representative_public_tree(
            belief,
            pot=12.0,
            stack=30.0,
            bet_size=3.0,
        )

    def test_unilateral_response_splice_changes_only_one_seat(self) -> None:
        schema = information_schema_for_axes(self.layout, self.source_axes)
        baseline = _uniform(schema)
        target_keys = {key for key in schema if "|p1|" in key}
        response = {key: schema[key][-1] for key in target_keys}
        candidate = splice_unilateral_best_response(
            layout=self.layout,
            hands_by_player=self.source_axes,
            baseline=baseline,
            target_player=1,
            best_response_actions=response,
        )
        self.assertEqual(set(candidate), set(baseline))
        for key in candidate:
            if key in target_keys:
                self.assertEqual(candidate[key][response[key]], 1.0)
            else:
                self.assertEqual(candidate[key], baseline[key])
        with self.assertRaisesRegex(ValueError, "incomplete"):
            splice_unilateral_best_response(
                layout=self.layout,
                hands_by_player=self.source_axes,
                baseline=baseline,
                target_player=1,
                best_response_actions={},
            )

    def test_policy_digest_statistics_and_tv_are_deterministic(self) -> None:
        schema = information_schema_for_axes(self.layout, self.source_axes)
        policy = _uniform(schema)
        copied = {key: dict(row) for key, row in reversed(tuple(policy.items()))}
        self.assertEqual(policy_digest(policy), policy_digest(copied))
        self.assertEqual(mean_policy_total_variation(policy, copied), 0.0)
        self.assertEqual(policy_statistics(policy)["information_sets"], len(policy))


if __name__ == "__main__":
    unittest.main()
