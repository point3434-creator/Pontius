from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from pontius.leaf_adjoint_cfr_audit import parse_leaf_adjoint_cfr_audit_config


_ROOT = Path(__file__).parents[1]
_CONFIG = (
    _ROOT
    / "experiments"
    / "configs"
    / "leaf-adjoint-cfr-gpu-audit-v1.json"
)


class LeafAdjointCFRAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(_CONFIG.read_text(encoding="utf-8"))

    def test_frozen_config_pins_bridge_gpu_and_sealed_validation(self) -> None:
        parsed = parse_leaf_adjoint_cfr_audit_config(self.config)
        self.assertEqual(parsed["small_hands_per_player"], (4, 7))
        self.assertEqual(parsed["range_families"], ("balanced", "blocker_heavy"))
        self.assertEqual(parsed["validation_speed_family"], "blocker_heavy")
        self.assertEqual(parsed["maximum_feature_width_per_batch"], 384)
        self.assertEqual(parsed["wide_iterations"], 2)
        self.assertEqual(parsed["gates"]["minimum_all_wide_gpu_speedup"], 3.0)
        self.assertEqual(
            parsed["gates"]["maximum_wide_host_peak_numeric_bytes"],
            3_000_000_000,
        )

    def test_stage_hash_workload_hardware_and_gate_mutations_fail(self) -> None:
        mutations = []

        stage = deepcopy(self.config)
        stage["evidence_stage"] = "blocker_h32_revealed"
        mutations.append(stage)

        source = deepcopy(self.config)
        source["expected_leaf_adjoint_cfr_sha256"] = "0" * 64
        mutations.append(source)

        validation = deepcopy(self.config)
        validation["validation_speed_family"] = "balanced"
        mutations.append(validation)

        batch = deepcopy(self.config)
        batch["maximum_feature_width_per_batch"] = 768
        mutations.append(batch)

        iterations = deepcopy(self.config)
        iterations["wide_iterations"] = 1
        mutations.append(iterations)

        runtime = deepcopy(self.config)
        runtime["required_cuda_runtime_version"] = 13030
        mutations.append(runtime)

        speed = deepcopy(self.config)
        speed["gates"]["minimum_all_wide_gpu_speedup"] = 1.0
        mutations.append(speed)

        identity = deepcopy(self.config)
        identity["gates"]["maximum_wide_regret_error"] = 1e-6
        mutations.append(identity)

        extra = deepcopy(self.config)
        extra["selected_backend"] = "cupy"
        mutations.append(extra)

        for mutation in mutations:
            with self.subTest(mutation=mutation):
                with self.assertRaises(ValueError):
                    parse_leaf_adjoint_cfr_audit_config(mutation)


if __name__ == "__main__":
    unittest.main()
