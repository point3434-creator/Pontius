from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from pontius.leaf_adjoint_batch_width_audit import (
    _attach_reference_errors,
    _width_summaries,
    parse_leaf_adjoint_batch_width_config,
)


_ROOT = Path(__file__).parents[1]
_CONFIG = (
    _ROOT
    / "experiments"
    / "configs"
    / "leaf-adjoint-batch-width-audit-v1.json"
)


class LeafAdjointBatchWidthAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(_CONFIG.read_text(encoding="utf-8"))

    def test_frozen_config_pins_mirrored_width_schedule_and_selection(self) -> None:
        parsed = parse_leaf_adjoint_batch_width_config(self.config)
        self.assertEqual(parsed["source_iteration"], 32)
        self.assertEqual(parsed["result_iteration"], 33)
        self.assertEqual(
            parsed["width_schedule"], (384, 768, 1536, 1536, 768, 384)
        )
        self.assertEqual(
            parsed["selection_rule"],
            "minimum_sum_family_median_step_ms_ties_smaller_width",
        )
        self.assertEqual(parsed["gates"]["expected_rows"], 12)

    def test_stage_source_schedule_hardware_and_gates_are_immutable(self) -> None:
        mutations = []

        stage = deepcopy(self.config)
        stage["evidence_stage"] = "step33_observed"
        mutations.append(stage)

        source = deepcopy(self.config)
        source["expected_checkpoint_source_sha256"] = "0" * 64
        mutations.append(source)

        implementation = deepcopy(self.config)
        implementation["expected_audit_implementation_sha256"] = "0" * 64
        mutations.append(implementation)

        schedule = deepcopy(self.config)
        schedule["width_schedule"] = [384, 768, 1536]
        mutations.append(schedule)

        width = deepcopy(self.config)
        width["warmup_width"] = 768
        mutations.append(width)

        selection = deepcopy(self.config)
        selection["selection_rule"] = "best_per_family"
        mutations.append(selection)

        runtime = deepcopy(self.config)
        runtime["required_cuda_runtime_version"] = 13030
        mutations.append(runtime)

        exactness = deepcopy(self.config)
        exactness["gates"]["maximum_regret_accumulator_error"] = 1e-6
        mutations.append(exactness)

        economics = deepcopy(self.config)
        economics["gates"]["minimum_selected_pooled_step_speedup"] = 1.0
        mutations.append(economics)

        extra = deepcopy(self.config)
        extra["adaptive_width"] = True
        mutations.append(extra)

        for mutation in mutations:
            with self.subTest(mutation=mutation):
                with self.assertRaises(ValueError):
                    parse_leaf_adjoint_batch_width_config(mutation)

    def test_reference_errors_cover_accumulators_and_both_policies(self) -> None:
        reference = {
            "_regrets": {"i": {"a": 1.0, "b": -1.0}},
            "_strategy_sums": {"i": {"a": 2.0, "b": 2.0}},
            "_current": {"i": {"a": 0.75, "b": 0.25}},
            "_average": {"i": {"a": 0.5, "b": 0.5}},
        }
        row = deepcopy(reference)
        row["_regrets"]["i"]["a"] += 1e-12
        row["_current"]["i"] = {"a": 0.5, "b": 0.5}
        _attach_reference_errors(row, reference)
        self.assertAlmostEqual(row["regret_accumulator_error"], 1e-12, places=15)
        self.assertEqual(row["strategy_sum_accumulator_error"], 0.0)
        self.assertEqual(row["current_policy_probability_error"], 0.25)
        self.assertEqual(row["current_policy_mean_tv"], 0.25)
        self.assertEqual(row["average_policy_probability_error"], 0.0)
        self.assertFalse(any(key.startswith("_") for key in row))

    def test_pooled_selector_uses_family_medians_and_smaller_tie_break(self) -> None:
        rows = []
        costs = {
            "balanced": {384: (100.0, 102.0), 768: (80.0, 82.0), 1536: (70.0, 72.0)},
            "blocker_heavy": {
                384: (60.0, 62.0),
                768: (50.0, 52.0),
                1536: (40.0, 42.0),
            },
        }
        batches = {384: 400, 768: 200, 1536: 100}
        for family, by_width in costs.items():
            for width, values in by_width.items():
                for value in values:
                    rows.append(
                        {
                            "range_family": family,
                            "width": width,
                            "step_wall_ms": value,
                            "terminal_contraction_ms": value - 1.0,
                            "operator_wall_ms": value - 10.0,
                            "host_to_device_ms": value / 5.0,
                            "gpu_kernel_ms": value / 4.0,
                            "device_to_host_ms": value / 6.0,
                            "terminal_nonoperator_ms": 9.0,
                            "reported_sparse_batches": batches[width],
                            "maximum_gpu_pool_bytes": width,
                            "maximum_host_peak_numeric_bytes": 2 * width,
                        }
                    )
        summaries, selected, speedup = _width_summaries(
            rows,
            families=("balanced", "blocker_heavy"),
            widths=(384, 768, 1536),
        )
        self.assertEqual(len(summaries), 6)
        self.assertEqual(selected, 1536)
        self.assertAlmostEqual(speedup, (101.0 + 61.0) / (71.0 + 41.0))


if __name__ == "__main__":
    unittest.main()
