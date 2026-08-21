from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from pontius.h32_second_board_action_width_quality_audit import (
    parse_h32_second_board_action_width_config,
    source_blueprint_from_frozen_checkpoints,
)
from pontius.h32_second_board_resident_cache_preflight import (
    compute_label_free_target_identity_rows,
)


_ROOT = Path(__file__).parents[1]
_CONFIG = (
    _ROOT / "experiments" / "configs" / "h32-second-board-action-width-v1.json"
)
_CACHE_PREFLIGHT = (
    _ROOT / "experiments" / "results" / "h32-second-board-resident-cache-v1.json"
)
_WARM_CONFIG = (
    _ROOT / "experiments" / "configs" / "h32-warm-search-acceptance-v1.json"
)
_WARM_PARENT = (
    _ROOT / "experiments" / "results" / "h32-warm-search-acceptance-v1.json"
)
_LADDER = (
    _ROOT / "experiments" / "results" / "leaf-adjoint-checkpoint-ladder-v2.json"
)
_EXTENSION = (
    _ROOT
    / "experiments"
    / "results"
    / "leaf-adjoint-checkpoint-extension-v1.json"
)


class H32SecondBoardActionWidthConfigTests(unittest.TestCase):
    def test_frozen_replication_is_outcome_neutral_and_discloses_prior_evidence(
        self,
    ) -> None:
        config = json.loads(_CONFIG.read_text(encoding="utf-8"))
        parsed = parse_h32_second_board_action_width_config(config)
        self.assertEqual(parsed["board"], ["2c", "7d", "9h", "Js", "Qc"])
        self.assertEqual(parsed["source_blueprint_point"], "64:average")
        self.assertEqual(parsed["construction_and_planning_budget_ms"], 90000.0)
        self.assertEqual(parsed["reserved_complete_step_ms"], 35000.0)
        self.assertEqual(parsed["maximum_complete_steps"], 8)
        self.assertEqual(parsed["strategy_claim_policy"], "always_null")
        self.assertIn("revealed_complete_union", parsed["known_original_board_one_size_evidence"])
        self.assertIn("both_arms_abstained", parsed["prior_sized_board_outcome"])
        self.assertNotIn("selected_reduction", parsed["gates"])
        self.assertNotIn("require_two_size_win", parsed["gates"])

    def test_source_target_disclosure_and_gate_mutations_are_rejected(self) -> None:
        config = json.loads(_CONFIG.read_text(encoding="utf-8"))
        for mutation in (
            lambda row: row.__setitem__("expected_cache_preflight_sha256", "0" * 64),
            lambda row: row["target_belief_sha256_by_target"].__setitem__(
                "balanced/local_blocker_seat3_x2", "0" * 64
            ),
            lambda row: row.__setitem__(
                "known_original_board_one_size_evidence", "hidden"
            ),
            lambda row: row["gates"].__setitem__(
                "maximum_total_audit_seconds", 3601.0
            ),
        ):
            changed = copy.deepcopy(config)
            mutation(changed)
            with self.assertRaises(ValueError):
                parse_h32_second_board_action_width_config(changed)


class H32SecondBoardActionWidthIdentityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(_CONFIG.read_text(encoding="utf-8"))
        cls.warm_config = json.loads(_WARM_CONFIG.read_text(encoding="utf-8"))
        cls.warm_parent = json.loads(_WARM_PARENT.read_text(encoding="utf-8"))
        cls.ladder = json.loads(_LADDER.read_text(encoding="utf-8"))
        cls.extension = json.loads(_EXTENSION.read_text(encoding="utf-8"))

    def test_all_four_label_free_target_identities_reproduce(self) -> None:
        rows = compute_label_free_target_identity_rows(
            self.warm_config,
            self.warm_parent,
            expected_digests=self.config["target_belief_sha256_by_target"],
        )
        self.assertEqual([row["target"] for row in rows], self.config["target_order"])
        self.assertTrue(all(row["passed"] for row in rows))

    def test_average64_source_blueprints_reconstruct_exactly(self) -> None:
        for family in self.config["range_families"]:
            with self.subTest(family=family):
                policy, diagnostics = source_blueprint_from_frozen_checkpoints(
                    self.ladder,
                    self.extension,
                    self.warm_parent,
                    family=family,
                )
                self.assertEqual(len(policy), 6144)
                self.assertEqual(diagnostics["source_blueprint_point"], "64:average")
                self.assertTrue(diagnostics["passed"])

    def test_cache_preflight_authorizes_exactly_one_revealed_board_run(self) -> None:
        preflight = json.loads(_CACHE_PREFLIGHT.read_text(encoding="utf-8"))
        self.assertTrue(preflight["passed"])
        self.assertTrue(preflight["headroom"]["all_eight_caches_safe"])
        self.assertEqual(preflight["h32_steps_executed"], 0)
        self.assertEqual(preflight["h32_policies_constructed"], 0)
        self.assertEqual(preflight["h32_strategy_quality_evaluations"], 0)
        self.assertIsNone(preflight["strategy_quality_claim"])


if __name__ == "__main__":
    unittest.main()
