from __future__ import annotations

import json
from pathlib import Path
import unittest

from pontius.batched_selector_stable_affine_response import (
    evaluate_batched_selector_stable_affine_opponents,
)
from pontius.h32_policy_delta_verifier_audit import (
    parse_h32_policy_delta_verifier_config,
)
from pontius.incremental_leaf_adjoint_response import (
    compile_leaf_adjoint_response_caches,
)
from pontius.incremental_policy_tt import compile_policy_probability_tape
from pontius.leaf_adjoint_checkpoint_ladder_audit import _build_case
from pontius.public_policy_tt import _information_key
from pontius.river import parse_cards
from pontius.selector_stable_affine_response import (
    evaluate_selector_stable_affine_leaf_adjoint_seat,
)


_ROOT = Path(__file__).parents[1]


class BatchedSelectorStableAffineResponseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            import scipy  # noqa: F401
        except ImportError as error:
            raise unittest.SkipTest("optional SciPy screen") from error
        config = json.loads(
            (
                _ROOT
                / "experiments/configs/h32-policy-delta-verifier-audit-v1.json"
            ).read_text(encoding="utf-8")
        )
        parsed = parse_h32_policy_delta_verifier_config(config)
        board = parse_cards(*parsed["board"])
        cls.belief, cls.layout, cls.sparse, retained = _build_case(
            parsed=parsed,
            board=board,
            hand_count=3,
            family="balanced",
        )
        cls.workspace, _, cls.automata = retained
        cls.caches = compile_leaf_adjoint_response_caches(
            cls.layout,
            cls.workspace,
            cls.sparse,
            {},
            cls.automata,
            hands_by_player=cls.belief.hands_by_player,
            maximum_feature_width_per_batch=384,
        )

    def _endpoint_for_actor(self, actor: int):
        node = next(
            node
            for node in self.layout.nodes
            if node.player == actor and len(node.actions) >= 2
        )
        key = _information_key(
            self.layout,
            actor,
            self.belief.hands_by_player[actor][0],
            node.history,
        )
        policy = {
            key: {
                action: float(index == 0)
                for index, action in enumerate(node.actions)
            }
        }
        return compile_policy_probability_tape(
            self.layout,
            self.belief.hands_by_player,
            policy,
        )

    def test_batch_matches_independent_scalar_opponent_rows(self) -> None:
        target = 0
        actors = (1, 2, 3)
        endpoints = tuple(self._endpoint_for_actor(actor) for actor in actors)
        expected = tuple(
            evaluate_selector_stable_affine_leaf_adjoint_seat(
                self.caches[target],
                endpoint,
                acting_player=actor,
                selector_margin_allowance=1e-14,
            )
            for endpoint, actor in zip(endpoints, actors, strict=True)
        )
        actual = evaluate_batched_selector_stable_affine_opponents(
            self.caches[target],
            endpoints,
            acting_players=actors,
            selector_margin_allowance=1e-14,
        )

        numeric = (
            "profile_utility_intercept",
            "profile_utility_slope",
            "best_response_value_intercept",
            "best_response_value_slope",
            "deviation_gain_intercept",
            "deviation_gap_slope",
            "selector_stable_scale",
        )
        structural = (
            "target_player",
            "acting_player",
            "changed_public_node",
            "first_switch_information_key",
            "first_switch_source_action",
            "first_switch_competing_action",
            "first_switch_hand_index",
            "selector_comparisons",
            "exact_source_action_ties",
            "affected_terminal_contractions",
            "reused_terminal_numerators",
        )
        for scalar, batched in zip(expected, actual.seat_results, strict=True):
            for field in numeric:
                self.assertAlmostEqual(
                    getattr(scalar, field), getattr(batched, field), places=12
                )
            for field in structural:
                self.assertEqual(getattr(scalar, field), getattr(batched, field))
            self.assertEqual(batched.terminal_contraction_ms, 0.0)

        self.assertEqual(actual.work.target_player, target)
        self.assertEqual(actual.work.candidate_rows, len(actors))
        self.assertEqual(actual.work.contraction_calls, 1)
        self.assertEqual(
            actual.work.affected_terminal_contractions,
            sum(row.affected_terminal_contractions for row in expected),
        )
        self.assertGreater(actual.work.wall_ms, 0.0)

    def test_batch_rejects_own_seat_and_count_mismatch(self) -> None:
        endpoint = self._endpoint_for_actor(0)
        with self.assertRaisesRegex(ValueError, "opponent edits only"):
            evaluate_batched_selector_stable_affine_opponents(
                self.caches[0],
                (endpoint,),
                acting_players=(0,),
            )
        with self.assertRaisesRegex(ValueError, "counts differ"):
            evaluate_batched_selector_stable_affine_opponents(
                self.caches[0],
                (self._endpoint_for_actor(1),),
                acting_players=(1, 2),
            )


if __name__ == "__main__":
    unittest.main()
