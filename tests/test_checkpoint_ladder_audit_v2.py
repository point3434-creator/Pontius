from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from pontius.leaf_adjoint_checkpoint_ladder_audit_v2 import (
    _current_policy_from_state,
    _policy_distance,
    parse_checkpoint_ladder_v2_config,
)
from pontius.real_policy import policy_digest


_ROOT = Path(__file__).parents[1]
_CONFIG = (
    _ROOT
    / "experiments"
    / "configs"
    / "leaf-adjoint-checkpoint-ladder-v2.json"
)


class CheckpointLadderAuditV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(_CONFIG.read_text(encoding="utf-8"))

    def test_frozen_config_pins_literal_per_policy_measurement_matrix(self) -> None:
        parsed = parse_checkpoint_ladder_v2_config(self.config)
        self.assertEqual(parsed["checkpoint_iterations"], (1, 2, 4, 8, 16, 32))
        self.assertEqual(
            parsed["live_evaluation_points"],
            (
                "2:current",
                "4:current",
                "4:average",
                "8:current",
                "8:average",
                "16:current",
                "16:average",
                "32:current",
                "32:average",
            ),
        )
        self.assertEqual(
            parsed["declared_source_reuse_points"],
            ("1:current", "1:average", "2:average"),
        )
        self.assertEqual(
            parsed["gates"]["expected_live_quality_profiles_per_family"], 9
        )
        self.assertEqual(
            parsed["gates"]["expected_reused_quality_profiles_per_family"], 3
        )

    def test_source_schedule_restart_hardware_and_gates_are_immutable(self) -> None:
        mutations = []

        stage = deepcopy(self.config)
        stage["evidence_stage"] = "later_quality_revealed"
        mutations.append(stage)

        source = deepcopy(self.config)
        source["expected_policy_source_sha256"] = "0" * 64
        mutations.append(source)

        base = deepcopy(self.config)
        base["expected_base_ladder_implementation_sha256"] = "0" * 64
        mutations.append(base)

        checkpoints = deepcopy(self.config)
        checkpoints["checkpoint_iterations"] = [1, 2, 4, 8, 16]
        mutations.append(checkpoints)

        live = deepcopy(self.config)
        live["live_evaluation_points"] = live["live_evaluation_points"][1:]
        mutations.append(live)

        reuse = deepcopy(self.config)
        reuse["declared_source_reuse_points"] = ["1:current", "1:average"]
        mutations.append(reuse)

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

        count = deepcopy(self.config)
        count["gates"]["expected_live_quality_profiles_per_family"] = 10
        mutations.append(count)

        extra = deepcopy(self.config)
        extra["policy_distance_reuse_threshold"] = 1e-9
        mutations.append(extra)

        for mutation in mutations:
            with self.subTest(mutation=mutation):
                with self.assertRaises(ValueError):
                    parse_checkpoint_ladder_v2_config(mutation)

    def test_state_policy_reconstruction_and_distance_are_literal(self) -> None:
        policy = {
            "a": {"fold": 0.25, "call": 0.75},
            "b": {"fold": 0.5, "call": 0.5},
        }
        state = {
            "regrets": {
                "a": {"fold": 1.0, "call": 3.0},
                "b": {"fold": -2.0, "call": 0.0},
            },
            "current_policy_sha256": policy_digest(policy),
        }
        rebuilt = _current_policy_from_state(state)
        self.assertEqual(rebuilt, policy)

        shifted = deepcopy(policy)
        shifted["a"] = {"fold": 0.5, "call": 0.5}
        distance = _policy_distance(policy, shifted)
        self.assertEqual(distance["maximum_probability_error"], 0.25)
        self.assertEqual(distance["nonzero_entries"], 2)
        self.assertEqual(distance["differing_information_rows"], 1)
        self.assertEqual(distance["mean_total_variation"], 0.125)


if __name__ == "__main__":
    unittest.main()
