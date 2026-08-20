from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from pontius.leaf_adjoint_batch_width_audit_v2 import (
    _measure_family_schedule,
    parse_leaf_adjoint_batch_width_v2_config,
)


_ROOT = Path(__file__).parents[1]
_CONFIG = (
    _ROOT
    / "experiments"
    / "configs"
    / "leaf-adjoint-batch-width-audit-v2.json"
)


def _fake_step(width: int) -> dict[str, object]:
    return {
        "width": width,
        "step_wall_ms": float(width),
        "_regrets": {"i": {"a": 1.0, "b": -1.0}},
        "_strategy_sums": {"i": {"a": 2.0, "b": 2.0}},
        "_current": {"i": {"a": 0.75, "b": 0.25}},
        "_average": {"i": {"a": 0.5, "b": 0.5}},
    }


class LeafAdjointBatchWidthAuditV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(_CONFIG.read_text(encoding="utf-8"))

    def test_complete_family_scope_crosses_warmup_schedule_and_compaction(self) -> None:
        calls = []

        def fake_run(**kwargs):
            calls.append(kwargs["width"])
            return _fake_step(kwargs["width"])

        parsed = {"warmup_width": 384, "width_schedule": (384, 768, 1536, 1536, 768, 384)}
        with patch(
            "pontius.leaf_adjoint_batch_width_audit_v2._v1._run_restored_step",
            side_effect=fake_run,
        ):
            warmup, rows = _measure_family_schedule(
                parsed=parsed,
                family="balanced",
                belief=object(),
                topology=object(),
                workspace=object(),
                sparse=object(),
                automata=object(),
                gpu=SimpleNamespace(upload_ms=1.25),
                source_state={},
                workspace_timing={"compile_ms": 2.5},
            )
        self.assertEqual(calls, [384, 384, 768, 1536, 1536, 768, 384])
        self.assertEqual(len(rows), 6)
        self.assertEqual(warmup["range_family"], "balanced")
        self.assertEqual(warmup["gpu_operator_upload_ms"], 1.25)
        self.assertFalse(any(key.startswith("_") for key in warmup))
        self.assertTrue(
            all(not any(key.startswith("_") for key in row) for row in rows)
        )
        self.assertTrue(
            all(row["regret_accumulator_error"] == 0.0 for row in rows)
        )
        self.assertEqual(
            [row["repeat_index_for_width"] for row in rows], [1, 1, 1, 2, 2, 2]
        )

    def test_corrected_config_retains_every_scientific_field_and_gate(self) -> None:
        parsed = parse_leaf_adjoint_batch_width_v2_config(self.config)
        self.assertEqual(
            parsed["width_schedule"], (384, 768, 1536, 1536, 768, 384)
        )
        self.assertEqual(parsed["source_iteration"], 32)
        self.assertEqual(parsed["result_iteration"], 33)
        self.assertEqual(parsed["gates"]["expected_rows"], 12)
        self.assertEqual(
            parsed["expected_rejected_audit_implementation_sha256"],
            "d41fab3383dd4f9d0fb65bc8acf3b7cbdbf7a06e06004e8e734b26036c74696f",
        )

    def test_stage_source_schedule_and_gates_are_immutable(self) -> None:
        mutations = []

        stage = deepcopy(self.config)
        stage["evidence_stage"] = "row_values_observed"
        mutations.append(stage)

        rejected = deepcopy(self.config)
        rejected["expected_rejected_audit_implementation_sha256"] = "0" * 64
        mutations.append(rejected)

        implementation = deepcopy(self.config)
        implementation["expected_audit_implementation_sha256"] = "0" * 64
        mutations.append(implementation)

        schedule = deepcopy(self.config)
        schedule["width_schedule"] = [384, 768, 1536]
        mutations.append(schedule)

        exactness = deepcopy(self.config)
        exactness["gates"]["maximum_current_policy_probability_error"] = 1e-6
        mutations.append(exactness)

        economics = deepcopy(self.config)
        economics["gates"]["minimum_selected_pooled_step_speedup"] = 1.0
        mutations.append(economics)

        extra = deepcopy(self.config)
        extra["continue_after_width"] = 1536
        mutations.append(extra)

        for mutation in mutations:
            with self.subTest(mutation=mutation):
                with self.assertRaises(ValueError):
                    parse_leaf_adjoint_batch_width_v2_config(mutation)


if __name__ == "__main__":
    unittest.main()
