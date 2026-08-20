from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from pontius.leaf_adjoint_evaluation_audit import (
    parse_leaf_adjoint_evaluation_audit_config,
)


_ROOT = Path(__file__).parents[1]
_CONFIG = (
    _ROOT
    / "experiments"
    / "configs"
    / "leaf-adjoint-evaluation-audit-v1.json"
)


class LeafAdjointEvaluationAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(_CONFIG.read_text(encoding="utf-8"))

    def test_frozen_config_pins_quality_profiles_and_validation_family(self) -> None:
        parsed = parse_leaf_adjoint_evaluation_audit_config(self.config)
        self.assertEqual(parsed["small_hands_per_player"], (4, 7))
        self.assertEqual(
            parsed["wide_policy_kinds"],
            ("uniform", "current_step1", "current_step2", "average_step2"),
        )
        self.assertEqual(parsed["validation_family"], "blocker_heavy")
        self.assertEqual(parsed["maximum_feature_width_per_batch"], 384)
        self.assertEqual(
            parsed["gates"][
                "minimum_average2_normalized_nash_conv_improvement"
            ],
            1e-6,
        )

    def test_stage_source_workload_hardware_and_gate_mutations_fail(self) -> None:
        mutations = []

        stage = deepcopy(self.config)
        stage["evidence_stage"] = "h32_quality_revealed"
        mutations.append(stage)

        source = deepcopy(self.config)
        source["expected_wide_source_sha256"] = "0" * 64
        mutations.append(source)

        validation = deepcopy(self.config)
        validation["validation_family"] = "balanced"
        mutations.append(validation)

        profiles = deepcopy(self.config)
        profiles["wide_policy_kinds"] = ["uniform", "average_step2"]
        mutations.append(profiles)

        cap = deepcopy(self.config)
        cap["maximum_feature_width_per_batch"] = 768
        mutations.append(cap)

        hardware = deepcopy(self.config)
        hardware["required_compute_capability"] = "90"
        mutations.append(hardware)

        quality = deepcopy(self.config)
        quality["gates"][
            "minimum_average2_normalized_nash_conv_improvement"
        ] = 0.0
        mutations.append(quality)

        speed = deepcopy(self.config)
        speed["gates"]["minimum_all_charged_gpu_speedup"] = 1.0
        mutations.append(speed)

        extra = deepcopy(self.config)
        extra["selected_quality_metric"] = "nash_conv"
        mutations.append(extra)

        for mutation in mutations:
            with self.subTest(mutation=mutation):
                with self.assertRaises(ValueError):
                    parse_leaf_adjoint_evaluation_audit_config(mutation)


if __name__ == "__main__":
    unittest.main()
