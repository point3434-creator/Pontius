from __future__ import annotations

import json
import unittest
from pathlib import Path

from pontius.factor_tt_contraction_audit import (
    _synthetic_train,
    _terminal_group,
    parse_factor_tt_contraction_config,
)

_ROOT = Path(__file__).parents[1]
_CONFIG = (
    _ROOT
    / "experiments"
    / "configs"
    / "factor-tt-direct-contraction-audit-v1.json"
)


def config() -> dict[str, object]:
    return json.loads(_CONFIG.read_text(encoding="utf-8"))


class FactorTTContractionAuditTests(unittest.TestCase):
    def test_frozen_config_parses_exactly(self) -> None:
        parsed = parse_factor_tt_contraction_config(config())
        self.assertEqual(parsed["actual_hands_per_player"], (4, 5, 7))
        self.assertEqual(parsed["performance_hands_per_player"], (4, 7, 10, 16, 24, 32))
        self.assertEqual(len(parsed["actual_operator_cases"]), 6)

    def test_terminal_groups_and_synthetic_train_are_deterministic(self) -> None:
        all_check = _terminal_group("all_check", 6)
        heads_up = _terminal_group("contenders_0_5", 6)
        self.assertFalse(all_check.contributed)
        self.assertEqual(all_check.contenders, tuple(range(6)))
        self.assertTrue(heads_up.contributed)
        self.assertEqual(heads_up.contenders, (0, 5))
        first = _synthetic_train(hand_count=3, players=6, rank=4, seed=7)
        second = _synthetic_train(hand_count=3, players=6, rank=4, seed=7)
        self.assertEqual(first.ranks, (1, 4, 4, 4, 4, 4, 1))
        for left, right in zip(first.cores, second.cores, strict=True):
            self.assertTrue((left == right).all())

    def test_stage_hash_case_timing_and_gate_mutations_fail(self) -> None:
        unknown = config()
        unknown["batch_all_operators"] = True
        with self.assertRaisesRegex(ValueError, "fields differ"):
            parse_factor_tt_contraction_config(unknown)

        hidden = config()
        hidden["evidence_stage"] = "validation"
        with self.assertRaisesRegex(ValueError, "preregistered revealed"):
            parse_factor_tt_contraction_config(hidden)

        changed_hash = config()
        changed_hash["expected_tensor_train_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "source hash mismatch"):
            parse_factor_tt_contraction_config(changed_hash)

        changed_case = config()
        changed_case["actual_operator_cases"][0]["player"] = 1
        with self.assertRaisesRegex(ValueError, "operator cases"):
            parse_factor_tt_contraction_config(changed_case)

        changed_timing = config()
        changed_timing["query_chunk_records"] = 512
        with self.assertRaisesRegex(ValueError, "execution contract"):
            parse_factor_tt_contraction_config(changed_timing)

        relaxed = config()
        relaxed["gates"]["maximum_direct_vs_reconstructed_expectation_error"] = 1e-5
        with self.assertRaisesRegex(ValueError, "differs from ADR-0065"):
            parse_factor_tt_contraction_config(relaxed)


if __name__ == "__main__":
    unittest.main()
