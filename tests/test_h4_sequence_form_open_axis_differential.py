from __future__ import annotations

import json
from pathlib import Path
import unittest

from pontius.h4_sequence_form_open_axis_differential import (
    _dense_policy,
    _finite_tree,
    _parse_config,
)
from pontius.real_policy import policy_digest


_ROOT = Path(__file__).parents[1]
_CONFIG = _ROOT / "experiments/configs/h4-sequence-form-open-axis-v1.json"


class H4SequenceFormOpenAxisDifferentialTests(unittest.TestCase):
    def test_frozen_config_is_label_free_and_covers_both_topologies(self) -> None:
        parsed = _parse_config(json.loads(_CONFIG.read_text(encoding="utf-8")))

        self.assertEqual(
            [row["layout_id"] for row in parsed["layouts"]],
            ["full_repeated_actor", "post_bet_single_visit"],
        )
        self.assertEqual(
            [row["expected_path_single_visit"] for row in parsed["layouts"]],
            [False, True],
        )
        self.assertEqual(
            parsed["strategy_label_policy"],
            "zero_certificates_zero_quality_rows_label_free",
        )
        self.assertEqual(
            parsed["gates"]["expected_fixed_response_passes_per_layout"],
            5,
        )

    def test_source_policy_rule_is_deterministic_and_key_sensitive(self) -> None:
        schema = {
            "p0|a": ("check", "bet"),
            "p0|b": ("check", "bet"),
        }
        first = _dense_policy(schema)
        second = _dense_policy(dict(reversed(tuple(schema.items()))))

        self.assertEqual(first, second)
        self.assertEqual(policy_digest(first), policy_digest(second))
        self.assertNotEqual(first["p0|a"], first["p0|b"])

    def test_config_and_nonfinite_mutations_fail_closed(self) -> None:
        config = json.loads(_CONFIG.read_text(encoding="utf-8"))
        config["expected_primitive_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "provenance mismatch"):
            _parse_config(config)
        self.assertTrue(_finite_tree({"rows": [1.0, None, True]}))
        self.assertFalse(_finite_tree({"rows": [float("inf")]}))


if __name__ == "__main__":
    unittest.main()
