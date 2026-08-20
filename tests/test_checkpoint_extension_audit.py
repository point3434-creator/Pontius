from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from pontius.leaf_adjoint_checkpoint_extension_audit import (
    build_guarded_incumbent_trace,
    parse_checkpoint_extension_config,
)


_ROOT = Path(__file__).parents[1]
_CONFIG = (
    _ROOT
    / "experiments"
    / "configs"
    / "leaf-adjoint-checkpoint-extension-v1.json"
)


def _candidate(index: int, value: float) -> dict[str, object]:
    return {
        "phase": "source" if index < 3 else "extension",
        "iteration": index,
        "policy_kind": "current" if index % 2 == 0 else "average",
        "policy_sha256": str(index) * 64,
        "normalized_nash_conv": value,
        "measurement_source": "test",
    }


class CheckpointExtensionAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(_CONFIG.read_text(encoding="utf-8"))

    def test_frozen_schedule_guard_and_outcome_neutral_gates(self) -> None:
        parsed = parse_checkpoint_extension_config(self.config)
        self.assertEqual(parsed["source_iteration"], 32)
        self.assertEqual(parsed["checkpoint_iterations"], (48, 64))
        self.assertEqual(parsed["restart_iteration"], 48)
        self.assertEqual(parsed["maximum_feature_width_per_batch"], 384)
        self.assertEqual(parsed["acceptance_guard_normalized"], 1e-10)
        self.assertNotIn("minimum_strategy_improvement", parsed["gates"])
        self.assertNotIn("maximum_final_nash_conv", parsed["gates"])

    def test_source_hardware_schedule_and_gates_are_immutable(self) -> None:
        mutations = []
        for key, value in (
            ("evidence_stage", "after_results"),
            ("expected_checkpoint_source_sha256", "0" * 64),
            ("checkpoint_iterations", [64]),
            ("restart_iteration", 64),
            ("candidate_order", ["average", "current"]),
            ("acceptance_guard_normalized", 1e-8),
            ("maximum_feature_width_per_batch", 768),
            ("required_cuda_runtime_version", 13030),
        ):
            mutation = deepcopy(self.config)
            mutation[key] = value
            mutations.append(mutation)
        gate = deepcopy(self.config)
        gate["gates"]["maximum_total_audit_seconds"] = 3600.0
        mutations.append(gate)
        extra = deepcopy(self.config)
        extra["strategy_quality_target"] = 0.004
        mutations.append(extra)
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                with self.assertRaises(ValueError):
                    parse_checkpoint_extension_config(mutation)

    def test_guarded_incumbent_exercises_accept_reject_and_abstain(self) -> None:
        candidates = [
            _candidate(0, 0.10),
            _candidate(1, 0.08),
            _candidate(2, 0.09),
            _candidate(3, 0.08 - 0.5e-10),
            _candidate(4, 0.07),
        ]
        result = build_guarded_incumbent_trace(candidates, guard=1e-10)
        self.assertEqual(
            [row["decision"] for row in result["trace"]],
            ["initialize", "accept", "reject", "abstain", "accept"],
        )
        self.assertTrue(result["nonworsening"])
        self.assertTrue(result["guard_semantics"])
        self.assertEqual(result["incumbent"]["normalized_nash_conv"], 0.07)

    def test_guarded_incumbent_rejects_invalid_inputs(self) -> None:
        with self.assertRaises(ValueError):
            build_guarded_incumbent_trace([], guard=1e-10)
        with self.assertRaises(ValueError):
            build_guarded_incumbent_trace([_candidate(0, -1.0)], guard=1e-10)
        with self.assertRaises(ValueError):
            build_guarded_incumbent_trace([_candidate(0, 1.0)], guard=-1.0)


if __name__ == "__main__":
    unittest.main()
