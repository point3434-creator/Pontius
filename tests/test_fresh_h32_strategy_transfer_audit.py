from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

import numpy as np

from pontius.fresh_h32_strategy_transfer_audit import (
    _absolute_cap_order,
    _build_target_belief,
    _interpolation_diagnostics,
    parse_fresh_h32_strategy_transfer_config,
)
from pontius.h32_current_interpolation_audit import interpolate_behavioral_policy
from pontius.open_mode_audit import _canonical_belief
from pontius.river import parse_cards


_ROOT = Path(__file__).parents[1]
_CONFIG = (
    _ROOT / "experiments" / "configs" / "fresh-h32-strategy-transfer-audit-v1.json"
)


class FreshH32StrategyTransferAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(_CONFIG.read_text(encoding="utf-8"))

    def test_frozen_config_declares_fresh_strategy_and_nonreanchoring(self) -> None:
        parsed = parse_fresh_h32_strategy_transfer_config(self.config)
        self.assertEqual(parsed["board"], ["4h", "6s", "Td", "Qh", "As"])
        self.assertNotIn(tuple(parsed["board"]), parsed["disclosed_prior_boards"])
        self.assertEqual(parsed["local_blocker_target_seat"], 5)
        self.assertEqual(parsed["predicted_predecessor_seat"], 4)
        self.assertEqual(
            parsed["certificate_anchor_rule"],
            "immutable_episode_blueprint_never_selected_candidate",
        )
        self.assertEqual(len(parsed["candidate_order"]), 13)

    def test_config_rejects_source_gate_and_anchor_edits(self) -> None:
        changed = copy.deepcopy(self.config)
        changed["expected_resident_evaluation_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "source hash"):
            parse_fresh_h32_strategy_transfer_config(changed)

        changed = copy.deepcopy(self.config)
        changed["gates"]["maximum_total_audit_seconds"] = 10_000.0
        with self.assertRaisesRegex(ValueError, "gates"):
            parse_fresh_h32_strategy_transfer_config(changed)

        changed = copy.deepcopy(self.config)
        changed["certificate_anchor_rule"] = "selected_candidate"
        with self.assertRaisesRegex(ValueError, "workload"):
            parse_fresh_h32_strategy_transfer_config(changed)

    def test_absolute_cap_order_uses_only_declared_blueprint_vector(self) -> None:
        self.assertEqual(
            _absolute_cap_order((0.4, 0.1, 0.1, 0.3), raw_guard=1e-9),
            (1, 2, 3, 0),
        )

    def test_local_blocker_shift_moves_to_seat_five_and_preserves_support(self) -> None:
        board = parse_cards("4h", "6s", "Td", "Qh", "As")
        belief = _canonical_belief(
            board=board,
            hand_count=4,
            family="balanced",
            components=3,
            seed=20260819,
        )
        target, descriptor = _build_target_belief(
            belief,
            board=board,
            shift="local_blocker_seat5_x2",
            local_blocker_target_seat=5,
        )
        self.assertEqual(descriptor["selected_seat"], 5)
        self.assertTrue(descriptor["positive_likelihoods"])
        self.assertTrue(descriptor["hand_axes_identity"])
        self.assertEqual(descriptor["likelihood_minimum"], 1.0)
        self.assertEqual(descriptor["likelihood_maximum"], 2.0)
        for seat in range(5):
            np.testing.assert_array_equal(
                target.unary_weights[seat],
                belief.unary_weights[seat],
            )

    def test_interpolation_control_is_normalized(self) -> None:
        first = {"i": {"a": 1.0, "b": 0.0}}
        second = {"i": {"a": 0.0, "b": 1.0}}
        policy = interpolate_behavioral_policy(first, second, 0.25)
        diagnostics = _interpolation_diagnostics(policy)
        self.assertEqual(diagnostics["maximum_normalization_error"], 0.0)
        self.assertTrue(diagnostics["finite_nonnegative"])
        self.assertEqual(policy["i"], {"a": 0.75, "b": 0.25})


if __name__ == "__main__":
    unittest.main()
