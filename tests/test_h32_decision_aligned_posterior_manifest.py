from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import unittest

from pontius.h32_decision_aligned_posterior_manifest import (
    _TARGET_PLAN,
    observed_bet_then_one_call_sequence,
    parse_h32_decision_aligned_posterior_manifest_config,
    public_prefix_from_observations,
)
from pontius.continuation_public_tree_tensor import (
    ContinuationPublicTreeTensorEvaluator,
    _state_after_public_prefix,
)
from pontius.river import parse_cards
from pontius.river_multiway import MultiwayRiverDeal, MultiwayRiverHoldem


ROOT = Path(__file__).parents[1]
CONFIG = ROOT / "experiments/configs/h32-decision-aligned-posterior-manifest-v1.json"


class H32DecisionAlignedPosteriorManifestTests(unittest.TestCase):
    def test_one_call_sequence_leaves_second_responder_on_clock(self) -> None:
        for bettor in range(6):
            observations = observed_bet_then_one_call_sequence(bettor)
            prefix = public_prefix_from_observations(observations)
            self.assertEqual(prefix[-2], (bettor, "bet"))
            self.assertEqual(prefix[-1], ((bettor + 1) % 6, "call"))
            self.assertEqual(len(prefix), bettor + 2)
            expected_history = "/".join(
                f"p{actor}:{action}" for actor, action in prefix[:-1]
            )
            self.assertEqual(observations[-1]["public_history"], expected_history)

    def test_target_plan_balances_every_positional_role_without_selection(self) -> None:
        self.assertEqual(len(_TARGET_PLAN), 6)
        self.assertEqual(
            Counter(row["source"] for row in _TARGET_PLAN),
            Counter({row["source"]: 1 for row in _TARGET_PLAN}),
        )
        for field in ("observed_bettor", "observed_responder", "acting_player"):
            self.assertEqual(
                Counter(int(row[field]) for row in _TARGET_PLAN),
                Counter({seat: 1 for seat in range(6)}),
            )
        self.assertTrue(
            all(
                row["observed_responder"] == (row["observed_bettor"] + 1) % 6
                and row["acting_player"] == (row["observed_bettor"] + 2) % 6
                and row["observed_response"] == "call"
                for row in _TARGET_PLAN
            )
        )
        self.assertEqual(len({row["target_id"] for row in _TARGET_PLAN}), 6)

    def test_every_frozen_prefix_is_legal_and_ends_before_the_current_actor(self) -> None:
        cards = parse_cards(
            "2c", "3c", "4c", "5c", "6c",
            "7c", "8c", "9c", "Tc", "Jc", "Qc", "Kc",
            "Ac", "2d", "3d", "4d", "5d",
        )
        deal = MultiwayRiverDeal(
            tuple((cards[5 + 2 * seat], cards[6 + 2 * seat]) for seat in range(6))
        )
        game = MultiwayRiverHoldem.from_joint_weights(
            board=cards[:5],
            pot=12.0,
            stacks=(30.0,) * 6,
            bet_size=3.0,
            joint_weights={deal: 1.0},
        )
        for bettor in range(6):
            prefix = public_prefix_from_observations(
                observed_bet_then_one_call_sequence(bettor)
            )
            state = _state_after_public_prefix(game, deal, prefix)
            continuation = ContinuationPublicTreeTensorEvaluator(
                game,
                public_prefix=prefix,
            )
            self.assertEqual(state.current_player, (bettor + 2) % 6)
            self.assertEqual(state.legal_actions(), ("fold", "call"))
            self.assertEqual(len(state.pending_responders), 4)
            self.assertEqual(continuation.nodes[0].player, state.current_player)
            self.assertEqual(continuation.topology_mismatch_count(), 0)

    def test_config_freezes_label_blind_decision_aligned_contract(self) -> None:
        parsed = parse_h32_decision_aligned_posterior_manifest_config(
            json.loads(CONFIG.read_text(encoding="utf-8"))
        )
        self.assertEqual(parsed["target_plan"], _TARGET_PLAN)
        self.assertEqual(parsed["gates"]["expected_behavioral_information_sets"], 32)
        self.assertEqual(parsed["gates"]["expected_policy_variables"], 64)
        self.assertEqual(parsed["gates"]["expected_remaining_responders"], 4)
        self.assertIn("zero_warm_steps", parsed["label_policy"])


if __name__ == "__main__":
    unittest.main()
