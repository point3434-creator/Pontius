from __future__ import annotations

import json
from pathlib import Path
import unittest

from pontius.h32_deep_horizon_correction_replay import (
    parse_h32_deep_horizon_correction_config,
    validate_correction_payload,
)


_ROOT = Path(__file__).parents[1]
_CONFIG = _ROOT / "experiments/configs/h32-deep-horizon-correction-v1.json"
_SOURCE = _ROOT / "experiments/results/h32-deep-horizon-opportunity-v1.json"
_SOURCE_CONFIG = _ROOT / "experiments/configs/h32-deep-horizon-opportunity-v1.json"
_PARENT = _ROOT / "experiments/results/h32-fresh-regret-vertex-opportunity-v1.json"


class H32DeepHorizonCorrectionReplayTests(unittest.TestCase):
    def test_contract_and_retained_payload_pass_exact_correction_replay(self) -> None:
        config = json.loads(_CONFIG.read_text(encoding="utf-8"))
        parsed = parse_h32_deep_horizon_correction_config(config)
        replay = validate_correction_payload(
            parsed=parsed,
            source=json.loads(_SOURCE.read_text(encoding="utf-8")),
            source_config=json.loads(_SOURCE_CONFIG.read_text(encoding="utf-8")),
            parent=json.loads(_PARENT.read_text(encoding="utf-8")),
        )
        self.assertTrue(replay["gates"]["passed"])
        self.assertEqual(replay["substantive_false_gates"], ["target_identity"])
        self.assertTrue(replay["corrected_source_gates"]["passed"])

    def test_contract_rejects_correction_parent_and_gate_mutations(self) -> None:
        config = json.loads(_CONFIG.read_text(encoding="utf-8"))

        mutated = json.loads(json.dumps(config))
        mutated["corrections"][0]["correct_descriptor_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "workload differs"):
            parse_h32_deep_horizon_correction_config(mutated)

        mutated = dict(config)
        mutated["expected_source_result_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "source mismatch"):
            parse_h32_deep_horizon_correction_config(mutated)

        mutated = json.loads(json.dumps(config))
        mutated["gates"]["require_aggregate_identity"] = False
        with self.assertRaisesRegex(ValueError, "gates differ"):
            parse_h32_deep_horizon_correction_config(mutated)

    def test_payload_rejects_any_additional_failed_gate(self) -> None:
        config = parse_h32_deep_horizon_correction_config(
            json.loads(_CONFIG.read_text(encoding="utf-8")),
        )
        source = json.loads(_SOURCE.read_text(encoding="utf-8"))
        source["gates"]["memory"] = False
        replay = validate_correction_payload(
            parsed=config,
            source=source,
            source_config=json.loads(_SOURCE_CONFIG.read_text(encoding="utf-8")),
            parent=json.loads(_PARENT.read_text(encoding="utf-8")),
        )
        self.assertFalse(replay["gates"]["passed"])
        self.assertFalse(replay["gates"]["only_target_identity_failed"])
        self.assertFalse(replay["gates"]["all_other_source_gates_true"])


if __name__ == "__main__":
    unittest.main()
