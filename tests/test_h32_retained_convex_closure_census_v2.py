from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from pontius.h32_retained_convex_closure_census_v2 import (
    _checkpoint_payload,
    _write_checkpoint,
    parse_h32_retained_convex_closure_census_v2_config,
)


ROOT = Path(__file__).parents[1]
CONFIG = ROOT / "experiments/configs/h32-retained-convex-closure-census-v2.json"


class H32RetainedConvexClosureCensusV2Tests(unittest.TestCase):
    def test_config_inherits_every_scientific_field_from_v1(self) -> None:
        parsed = parse_h32_retained_convex_closure_census_v2_config(
            json.loads(CONFIG.read_text(encoding="utf-8"))
        )
        base = parsed["base"]
        self.assertEqual(len(base["inventory"]), 42)
        self.assertEqual(base["maximum_cut_rounds"], 32)
        self.assertEqual(base["maximum_target_seconds"], 240.0)
        self.assertEqual(base["maximum_total_seconds"], 10800.0)
        self.assertEqual(base["epigraph_separation_allowance"], 1e-9)
        self.assertEqual(base["cap_numerical_allowance"], 2e-11)

    def test_config_discloses_partial_labels_and_only_known_error(self) -> None:
        parsed = parse_h32_retained_convex_closure_census_v2_config(
            json.loads(CONFIG.read_text(encoding="utf-8"))
        )
        self.assertIn("targets_1_to_5", parsed["partial_label_disclosure"])
        self.assertIn("target_6", parsed["partial_label_disclosure"])
        self.assertEqual(
            parsed["allowed_target_error"],
            "ArithmeticError:behavioral master primal/dual verification failed",
        )
        self.assertIn("no_tolerance_change", parsed["diagnostic_rule"])

    def test_checkpoint_replaces_complete_json_and_leaves_no_temporary(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "partial.json"
            first = _checkpoint_payload(
                config_sha256="config",
                inventory_sha256="inventory",
                outcomes=[{"target_id": "one", "status": "completed"}],
            )
            first_sha = _write_checkpoint(first, path)
            second = _checkpoint_payload(
                config_sha256="config",
                inventory_sha256="inventory",
                outcomes=[
                    {"target_id": "one", "status": "completed"},
                    {"target_id": "two", "status": "target_error_censored"},
                ],
            )
            second_sha = _write_checkpoint(second, path)
            stored = json.loads(path.read_text(encoding="utf-8"))
            self.assertNotEqual(first_sha, second_sha)
            self.assertEqual(stored["attempted_targets"], 2)
            self.assertEqual(len(stored["outcomes"]), 2)
            self.assertFalse(path.with_suffix(".json.tmp").exists())


if __name__ == "__main__":
    unittest.main()
