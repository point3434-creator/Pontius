from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from pontius.h32_warm_search_acceptance_audit import (
    build_sequential_incumbents,
    build_target_belief,
    compare_acceptance,
    parse_h32_warm_search_config,
)
from pontius.open_mode_audit import _canonical_belief
from pontius.river import parse_cards


_ROOT = Path(__file__).parents[1]
_CONFIG = _ROOT / "experiments" / "configs" / "h32-warm-search-acceptance-v1.json"


def _quality(nash_conv: float, gains: list[float]) -> dict[str, object]:
    return {
        "nash_conv": nash_conv,
        "normalized_nash_conv": nash_conv / 30.0,
        "deviation_gains": gains,
    }


class H32WarmSearchAcceptanceAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(_CONFIG.read_text(encoding="utf-8"))

    def test_frozen_matrix_has_no_strategy_outcome_gate(self) -> None:
        parsed = parse_h32_warm_search_config(self.config)
        self.assertEqual(parsed["target_shifts"], (
            "local_blocker_seat3_x2",
            "all_seat_strength_1_to2",
        ))
        self.assertEqual(parsed["search_checkpoint_iterations"], (1, 2, 4))
        self.assertEqual(parsed["primary_search_iteration"], 4)
        self.assertEqual(parsed["maximum_feature_width_per_batch"], 384)
        self.assertNotIn("minimum_strategy_improvement", parsed["gates"])
        self.assertNotIn("minimum_acceptance_rate", parsed["gates"])

    def test_sources_schedule_hardware_and_gates_are_immutable(self) -> None:
        mutations = []
        for key, value in (
            ("evidence_stage", "after_quality"),
            ("expected_extension_source_sha256", "0" * 64),
            ("target_shifts", ["all_seat_strength_1_to2"]),
            ("blueprint_point", "48:current"),
            ("search_checkpoint_iterations", [1, 2]),
            ("primary_search_iteration", 2),
            ("acceptance_guard_normalized", 1e-8),
            ("maximum_feature_width_per_batch", 768),
            ("required_cuda_runtime_version", 13030),
        ):
            mutation = deepcopy(self.config)
            mutation[key] = value
            mutations.append(mutation)
        gate = deepcopy(self.config)
        gate["gates"]["maximum_total_audit_seconds"] = 2400.0
        mutations.append(gate)
        extra = deepcopy(self.config)
        extra["selector"] = "best_observed"
        mutations.append(extra)
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                with self.assertRaises(ValueError):
                    parse_h32_warm_search_config(mutation)

    def test_target_shifts_are_positive_support_preserving_and_exactly_bounded(self) -> None:
        board = parse_cards("2c", "7d", "9h", "Js", "Qc")
        belief = _canonical_belief(
            board=board,
            hand_count=4,
            family="balanced",
            components=3,
            seed=20260819,
        )
        for shift in self.config["target_shifts"]:
            with self.subTest(shift=shift):
                target, descriptor = build_target_belief(
                    belief,
                    board=board,
                    shift=shift,
                    local_blocker_target_seat=3,
                )
                self.assertEqual(target.hands_by_player, belief.hands_by_player)
                self.assertTrue(descriptor["positive_likelihoods"])
                self.assertEqual(descriptor["likelihood_minimum"], 1.0)
                self.assertEqual(descriptor["likelihood_maximum"], 2.0)

    def test_acceptance_separates_aggregate_and_unilateral_constraints(self) -> None:
        baseline = _quality(0.30, [0.05] * 6)
        aggregate_only = _quality(0.24, [0.02, 0.02, 0.02, 0.02, 0.02, 0.14])
        safe = _quality(0.18, [0.03] * 6)
        first = compare_acceptance(
            baseline,
            aggregate_only,
            payoff_span=30.0,
            normalized_guard=1e-10,
        )
        self.assertTrue(first["aggregate_accept"])
        self.assertFalse(first["unilateral_accept"])
        self.assertEqual(first["unilateral_constraint_failures"], [5])
        second = compare_acceptance(
            baseline,
            safe,
            payoff_span=30.0,
            normalized_guard=1e-10,
        )
        self.assertTrue(second["aggregate_accept"])
        self.assertTrue(second["unilateral_accept"])

    def test_sequential_incumbents_are_source_relative_after_each_accept(self) -> None:
        baseline = _quality(0.30, [0.05] * 6)
        candidates = [
            {"candidate_id": "one", "quality": _quality(0.24, [0.04] * 6)},
            {"candidate_id": "two", "quality": _quality(0.27, [0.03] * 6)},
            {"candidate_id": "three", "quality": _quality(0.18, [0.03] * 6)},
        ]
        result = build_sequential_incumbents(
            baseline,
            candidates,
            payoff_span=30.0,
            normalized_guard=1e-10,
        )
        self.assertEqual(result["trace"][0]["resulting_aggregate_incumbent"], "one")
        self.assertEqual(result["trace"][1]["resulting_aggregate_incumbent"], "one")
        self.assertEqual(result["final_aggregate_incumbent"], "three")
        self.assertEqual(result["final_unilateral_incumbent"], "three")


if __name__ == "__main__":
    unittest.main()
