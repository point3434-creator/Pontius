from __future__ import annotations

import json
from pathlib import Path
import unittest

from pontius.h32_resident_step_bottleneck_profile_v2 import (
    _corrected_loads,
    _source_pass_alias,
    parse_h32_resident_step_bottleneck_v2_config,
)


_ROOT = Path(__file__).parents[1]
_CONFIG = _ROOT / "experiments/configs/h32-resident-step-bottleneck-profile-v2.json"


class H32ResidentStepBottleneckProfileV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(_CONFIG.read_text(encoding="utf-8"))

    def test_v1_scientific_protocol_is_reused_without_changes(self) -> None:
        parsed = parse_h32_resident_step_bottleneck_v2_config(self.config)
        base = parsed["v1_base"]
        for field in (
            "targets",
            "target_seat",
            "restarts_per_target",
            "restart_rule",
            "timing_boundary",
            "classification_rule",
            "hardware_counterfactuals",
            "maximum_policy_probability_error",
            "maximum_policy_mean_total_variation",
            "gates",
        ):
            self.assertEqual(parsed[field], base[field])

    def test_alias_adds_only_the_expected_pass_view(self) -> None:
        source = {
            "status": "frozen_h32_fresh_panel_source_blueprints_executed",
            "passed": True,
            "gate_results": {"source_count": True},
            "source_rows": [{"source": "panel_1/balanced"}],
        }
        corrected = _source_pass_alias(source)
        self.assertNotIn("gates", source)
        self.assertEqual(corrected["gates"], {"passed": True})
        self.assertIs(corrected["source_rows"], source["source_rows"])
        self.assertEqual(
            set(corrected) - set(source),
            {"gates"},
        )

    def test_corrected_loader_ignores_every_other_json_object(self) -> None:
        loads = _corrected_loads(json.loads)
        ordinary = {"status": "another_artifact", "passed": True}
        self.assertEqual(loads(json.dumps(ordinary)), ordinary)
        source = {
            "status": "frozen_h32_fresh_panel_source_blueprints_executed",
            "passed": False,
            "source_rows": [],
        }
        self.assertEqual(loads(json.dumps(source))["gates"]["passed"], False)

    def test_alias_and_config_mutations_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "wrong artifact"):
            _source_pass_alias({"status": "wrong", "passed": True, "source_rows": []})

        changed = dict(self.config)
        changed["correction_scope"] = "change_timing"
        with self.assertRaisesRegex(ValueError, "workload differs"):
            parse_h32_resident_step_bottleneck_v2_config(changed)

        changed = dict(self.config)
        changed["expected_v1_implementation_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "source mismatch"):
            parse_h32_resident_step_bottleneck_v2_config(changed)


if __name__ == "__main__":
    unittest.main()
