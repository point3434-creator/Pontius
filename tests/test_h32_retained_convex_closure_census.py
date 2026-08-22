from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import unittest

from pontius.h32_retained_convex_closure_census import (
    _oracle_summary,
    parse_h32_retained_convex_closure_census_config,
    retained_inventory_sha256,
    retained_opened_target_inventory,
)


ROOT = Path(__file__).parents[1]
CONFIG = ROOT / "experiments/configs/h32-retained-convex-closure-census-v1.json"


class H32RetainedConvexClosureCensusTests(unittest.TestCase):
    def test_inventory_contains_every_opened_compatible_identity_once(self) -> None:
        rows = retained_opened_target_inventory()
        self.assertEqual(len(rows), 42)
        self.assertEqual(len({row["target_id"] for row in rows}), 42)
        self.assertEqual(len({row["target_belief_sha256"] for row in rows}), 42)
        self.assertEqual(
            Counter(row["panel"] for row in rows),
            Counter({"latin_ab": 12, "latin_cd": 12, "latin_ef": 12, "post_call": 6}),
        )
        for field in ("source", "observed_bettor", "acting_player"):
            self.assertEqual(set(Counter(row[field] for row in rows).values()), {7})

    def test_inventory_freezes_wide_and_current_axis_rules(self) -> None:
        rows = retained_opened_target_inventory()
        wide = [row for row in rows if row["panel"] != "post_call"]
        current = [row for row in rows if row["panel"] == "post_call"]
        self.assertEqual(len(wide), 36)
        self.assertEqual(len(current), 6)
        for row in wide:
            self.assertEqual(row["acting_player"], (row["observed_bettor"] - 1) % 6)
            self.assertEqual(row["acting_public_nodes"], 16)
            self.assertEqual(row["behavioral_information_sets"], 512)
            self.assertEqual(row["policy_variables"], 1024)
        for row in current:
            self.assertEqual(row["observed_response"], "call")
            self.assertEqual(row["public_prefix"][-1][1], "call")
            self.assertEqual(row["acting_player"], (row["observed_bettor"] + 2) % 6)
            self.assertEqual(row["acting_public_nodes"], 1)
            self.assertEqual(row["behavioral_information_sets"], 32)
            self.assertEqual(row["policy_variables"], 64)

    def test_inventory_excludes_every_sealed_post_fold_identity(self) -> None:
        rows = retained_opened_target_inventory()
        post_fold = json.loads(
            (
                ROOT
                / "experiments/results/h32-post-fold-posterior-manifest-v1.json"
            ).read_text(encoding="utf-8")
        )["target_rows"]
        self.assertFalse(
            {row["target_id"] for row in rows}
            & {row["target_id"] for row in post_fold}
        )
        self.assertFalse(
            {row["target_belief_sha256"] for row in rows}
            & {row["target_belief_sha256"] for row in post_fold}
        )

    def test_oracle_summary_keeps_cap_and_epigraph_allowances_distinct(self) -> None:
        oracle = {
            "policy_sha256": "policy",
            "objective": 0.6,
            "response_signatures": ("a", "b"),
            "probability_compile_ms": 1.0,
            "wall_ms": 2.0,
            "zero_sum_residual": 0.0,
            "response_action_flips": 0,
            "affected_terminal_contractions": 1,
            "maximum_middle_rank": 2,
            "maximum_gpu_pool_total_bytes": 3,
            "seat_wall_ms": (0.4, 0.5),
            "gains": (0.2 + 5e-10, 0.4),
            "raw_gains": (0.2 + 5e-10, 0.4),
        }
        summary = _oracle_summary(
            oracle,
            caps=(0.2, 0.4),
            epigraph=(0.2, 0.4),
            cap_allowance=2e-11,
            epigraph_allowance=1e-9,
        )
        self.assertFalse(summary["cap_feasible"])
        self.assertEqual(summary["epigraph_violating_players"], [])
        self.assertEqual(summary["cap_allowance"], 2e-11)
        self.assertEqual(summary["epigraph_allowance"], 1e-9)

    def test_config_freezes_retrospective_full_closure_contract(self) -> None:
        parsed = parse_h32_retained_convex_closure_census_config(
            json.loads(CONFIG.read_text(encoding="utf-8"))
        )
        self.assertEqual(parsed["expected_inventory_sha256"], retained_inventory_sha256())
        self.assertEqual(len(parsed["inventory"]), 42)
        self.assertEqual(parsed["maximum_cut_rounds"], 32)
        self.assertIn("retrospective_optimizer_labels_allowed", parsed["label_policy"])
        self.assertIn("post_fold_excluded", parsed["target_rule"])
        self.assertIn("methodological_comparability", parsed["warm_step_rule"])


if __name__ == "__main__":
    unittest.main()
