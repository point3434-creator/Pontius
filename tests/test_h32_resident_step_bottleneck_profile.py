from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
import unittest

from pontius.evidence_protocol import DEFAULT_GPU_NUMERICAL_IDENTITY
from pontius.h32_resident_step_bottleneck_profile import (
    _counterfactuals,
    _profile_step_row,
    _summary,
    parse_h32_resident_step_bottleneck_config,
)


_ROOT = Path(__file__).parents[1]
_CONFIG = _ROOT / "experiments/configs/h32-resident-step-bottleneck-profile-v1.json"


def _traverser(seat: int) -> SimpleNamespace:
    resident = SimpleNamespace(
        wall_ms=140.0,
        factor_prepare_ms=2.0,
        factor_upload_ms=1.0,
        product_generation_gpu_ms=10.0,
        resident_pipeline_gpu_ms=70.0,
        device_to_host_ms=5.0,
        hand_fold_ms=40.0,
        batches=3,
        maximum_batch_feature_width=384,
        per_call_host_to_device_bytes=100,
        per_call_device_to_host_bytes=200,
        maximum_middle_rank=64,
    )
    return SimpleNamespace(
        traverser=seat,
        probability_compile_ms=1.0,
        own_reach_and_average_ms=1.0,
        reverse_adjoint_ms=1.0,
        regret_apply_ms=1.0,
        terminal_sparse_batches=3,
        maximum_gpu_pool_total_bytes=1000,
        resident_work=resident,
    )


class H32ResidentStepBottleneckProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(_CONFIG.read_text(encoding="utf-8"))

    def test_protocol_is_exposed_replay_with_numerical_identity(self) -> None:
        parsed = parse_h32_resident_step_bottleneck_config(self.config)
        self.assertEqual(len(parsed["targets"]), 2)
        self.assertEqual(parsed["restarts_per_target"], 3)
        self.assertEqual(
            parsed["maximum_policy_probability_error"],
            DEFAULT_GPU_NUMERICAL_IDENTITY.maximum_policy_probability_error,
        )
        self.assertEqual(
            parsed["maximum_policy_mean_total_variation"],
            DEFAULT_GPU_NUMERICAL_IDENTITY.maximum_policy_mean_information_set_total_variation,
        )
        self.assertIn("read_only_replay", parsed["evidence_stage"])
        self.assertNotIn("quality", parsed["classification_rule"])

    def test_stage_buckets_and_counterfactuals_are_additive(self) -> None:
        work = SimpleNamespace(
            iteration=1,
            wall_ms=900.0,
            terminal_contraction_ms=840.0,
            discount_ms=6.0,
            traversers=tuple(_traverser(seat) for seat in range(6)),
        )
        row = _profile_step_row(work, wall_ms=900.0, repetition=1)
        self.assertEqual(row["device_gpu_ms"], 480.0)
        self.assertEqual(row["host_hand_fold_ms"], 240.0)
        self.assertEqual(row["transfer_ms"], 36.0)
        self.assertAlmostEqual(row["explicitly_attributed_ms"], 798.0)
        self.assertAlmostEqual(row["stage_residual_ms"], 102.0)
        counterfactuals = _counterfactuals(row)
        self.assertEqual(counterfactuals["two_x_device_gpu_only_ms"], 660.0)
        self.assertAlmostEqual(
            counterfactuals["two_x_device_gpu_only_speedup"], 900.0 / 660.0
        )

    def test_summary_classifies_largest_bucket_without_acceptance_gate(self) -> None:
        rows = [
            {
                "wall_ms": 100.0,
                "device_gpu_ms": 60.0,
                "host_hand_fold_ms": 20.0,
                "transfer_ms": 5.0,
                "other_host_or_residual_ms": 15.0,
                "stage_residual_fraction": 0.01,
            },
            {
                "wall_ms": 120.0,
                "device_gpu_ms": 70.0,
                "host_hand_fold_ms": 25.0,
                "transfer_ms": 5.0,
                "other_host_or_residual_ms": 20.0,
                "stage_residual_fraction": -0.01,
            },
        ]
        result = _summary(rows)
        self.assertEqual(result["dominant_time_bucket"], "device_gpu")
        self.assertAlmostEqual(result["pooled_stage_share"]["device_gpu"], 130 / 220)

    def test_workload_and_source_mutations_are_rejected(self) -> None:
        changed = dict(self.config)
        changed["restarts_per_target"] = 2
        with self.assertRaisesRegex(ValueError, "workload differs"):
            parse_h32_resident_step_bottleneck_config(changed)

        changed = dict(self.config)
        changed["expected_resident_cfr_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "source mismatch"):
            parse_h32_resident_step_bottleneck_config(changed)


if __name__ == "__main__":
    unittest.main()
