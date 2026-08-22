from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from pontius import h32_retained_convex_closure_census as census
from pontius.h32_post_fold_failure_closure_diagnostic import (
    _failure_inventory,
    _marginal_round_rows,
    _parse_config,
    _reproduction_row,
    _write_checkpoint,
    post_fold_census_setup_adapter,
)


ROOT = Path(__file__).parents[1]
CONFIG = (
    ROOT / "experiments/configs/h32-post-fold-failure-closure-diagnostic-v1.json"
)
MANIFEST = ROOT / "experiments/results/h32-post-fold-posterior-manifest-v1.json"


class H32PostFoldFailureClosureDiagnosticTests(unittest.TestCase):
    def test_config_freezes_only_the_two_fresh_failures(self) -> None:
        parsed = _parse_config(json.loads(CONFIG.read_text(encoding="utf-8")))
        self.assertEqual(len(parsed["inventory"]), 2)
        self.assertEqual(
            [row["target_id"] for row in parsed["inventory"]],
            parsed["gates"]["expected_failure_target_ids"],
        )
        self.assertTrue(
            all(row["observed_response"] == "fold" for row in parsed["inventory"])
        )
        self.assertEqual(parsed["maximum_cut_rounds"], 32)
        self.assertEqual(parsed["bound_tolerance"], 1e-8)
        self.assertIn("zero_new_retreat_labels", parsed["label_policy"])

    def test_failure_inventory_rejects_an_unknown_target(self) -> None:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        with self.assertRaisesRegex(ValueError, "absent from manifest"):
            _failure_inventory(manifest, ("not/a/target",))

    def test_census_setup_adapter_restores_and_rejects_nesting(self) -> None:
        original = census._setup_target
        with post_fold_census_setup_adapter():
            self.assertIsNot(census._setup_target, original)
            with self.assertRaisesRegex(RuntimeError, "already replaced"):
                with post_fold_census_setup_adapter():
                    self.fail("nested census setup unexpectedly opened")
        self.assertIs(census._setup_target, original)

    def test_census_setup_adapter_restores_after_failure(self) -> None:
        original = census._setup_target
        with self.assertRaisesRegex(RuntimeError, "negative control"):
            with post_fold_census_setup_adapter():
                raise RuntimeError("negative control")
        self.assertIs(census._setup_target, original)

    def test_reproduction_control_checks_continuous_and_discrete_identity(self) -> None:
        fresh = {
            "source_nash_conv": 0.3,
            "masters": [{"lower_bound": 0.2}, {"lower_bound": 0.25}],
            "first_oracle": {"nash_conv": 0.28},
            "cut_rows": [{"target_player": 1}],
            "endpoint_certificate": {
                "exact_summary": {
                    "nash_conv": 0.26,
                    "epigraph_violating_players": [2],
                },
                "optimality_gap": 0.01,
            },
        }
        row = {
            "target_id": "target",
            "source_nash_conv": 0.3,
            "iterations": [
                {
                    "master": {"lower_bound": 0.2},
                    "oracle": {"objective": 0.28},
                    "cut_rows": [{"target_player": 1}],
                },
                {
                    "master": {"lower_bound": 0.25},
                    "oracle": {
                        "objective": 0.26,
                        "epigraph_violating_players": [2],
                    },
                    "optimality_gap": 0.01,
                },
            ],
        }
        reproduced = _reproduction_row(row, fresh)
        self.assertTrue(reproduced["discrete_identity"])
        self.assertEqual(reproduced["maximum_absolute_error"], 0.0)
        contaminated = deepcopy(row)
        contaminated["iterations"][1]["oracle"]["epigraph_violating_players"] = [3]
        self.assertFalse(_reproduction_row(contaminated, fresh)["discrete_identity"])

    def test_marginal_round_cost_excludes_the_already_charged_prefix(self) -> None:
        row = {
            "converged": True,
            "iterations": [
                {},
                {
                    "cut_extraction_ms": 10.0,
                    "cut_rows": [{"target_player": 2}],
                },
                {
                    "master": {"solve_ms": 2.0},
                    "oracle": {"wall_ms": 300.0},
                },
            ],
        }
        marginal = _marginal_round_rows(row)
        self.assertEqual(len(marginal), 1)
        self.assertEqual(marginal[0]["incremental_ms"], 312.0)
        self.assertTrue(marginal[0]["endpoint_globally_closed"])

    def test_checkpoint_atomically_replaces_complete_json(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "partial.json"
            first = _write_checkpoint({"attempted_targets": 1}, path)
            second = _write_checkpoint({"attempted_targets": 2}, path)
            self.assertNotEqual(first, second)
            self.assertEqual(
                json.loads(path.read_text(encoding="utf-8"))["attempted_targets"],
                2,
            )
            self.assertFalse(path.with_suffix(".json.tmp").exists())


if __name__ == "__main__":
    unittest.main()
