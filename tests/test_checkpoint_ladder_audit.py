from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from pontius.leaf_adjoint_checkpoint_ladder_audit import (
    parse_checkpoint_ladder_config,
)


_ROOT = Path(__file__).parents[1]
_CONFIG = (
    _ROOT
    / "experiments"
    / "configs"
    / "leaf-adjoint-checkpoint-ladder-v1.json"
)


class CheckpointLadderAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(_CONFIG.read_text(encoding="utf-8"))

    def test_frozen_config_pins_restart_curve_and_quality_bill(self) -> None:
        parsed = parse_checkpoint_ladder_config(self.config)
        self.assertEqual(parsed["checkpoint_iterations"], (1, 2, 4, 8, 16, 32))
        self.assertEqual(parsed["live_evaluation_iterations"], (4, 8, 16, 32))
        self.assertEqual(parsed["wide_restart_iteration"], 16)
        self.assertEqual(parsed["validation_family"], "blocker_heavy")
        self.assertEqual(
            parsed["gates"]["maximum_total_audit_seconds"],
            3600.0,
        )

    def test_stage_source_schedule_restart_hardware_and_gates_are_immutable(self) -> None:
        mutations = []

        stage = deepcopy(self.config)
        stage["evidence_stage"] = "iteration4_revealed"
        mutations.append(stage)

        source = deepcopy(self.config)
        source["expected_quality_source_sha256"] = "0" * 64
        mutations.append(source)

        checkpoints = deepcopy(self.config)
        checkpoints["checkpoint_iterations"] = [1, 2, 4, 8, 16]
        mutations.append(checkpoints)

        live = deepcopy(self.config)
        live["live_evaluation_iterations"] = [8, 16, 32]
        mutations.append(live)

        restart = deepcopy(self.config)
        restart["wide_restart_iteration"] = 8
        mutations.append(restart)

        validation = deepcopy(self.config)
        validation["validation_family"] = "balanced"
        mutations.append(validation)

        runtime = deepcopy(self.config)
        runtime["required_cuda_runtime_version"] = 13030
        mutations.append(runtime)

        quality = deepcopy(self.config)
        quality["gates"][
            "minimum_final_average_normalized_improvement_over_step2"
        ] = 0.0
        mutations.append(quality)

        wall = deepcopy(self.config)
        wall["gates"]["maximum_total_audit_seconds"] = 7200.0
        mutations.append(wall)

        extra = deepcopy(self.config)
        extra["early_stop_iteration"] = 8
        mutations.append(extra)

        for mutation in mutations:
            with self.subTest(mutation=mutation):
                with self.assertRaises(ValueError):
                    parse_checkpoint_ladder_config(mutation)


if __name__ == "__main__":
    unittest.main()
