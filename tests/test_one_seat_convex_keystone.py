from __future__ import annotations

import json
from pathlib import Path
import unittest

from pontius.one_seat_convex_keystone import (
    _finite_tree,
    _monotone,
    _parse_config,
    mutation_controls,
)


_ROOT = Path(__file__).parents[1]
_CONFIG = _ROOT / "experiments/configs/one-seat-convex-keystone-v1.json"


class OneSeatConvexKeystoneTests(unittest.TestCase):
    def test_frozen_config_and_mutation_controls_fail_closed(self) -> None:
        parsed = _parse_config(json.loads(_CONFIG.read_text(encoding="utf-8")))
        controls = mutation_controls(float(parsed["tolerance"]))

        self.assertTrue(controls["behavioral_shortcut_rejected"])
        self.assertEqual(controls["multi_cut_added_targets"], [1, 2])
        self.assertTrue(controls["all_opponents_added_in_one_round"])
        self.assertTrue(controls["timeout_safe_incumbent"])
        self.assertTrue(controls["timeout_bound_orientation_correct"])

    def test_bound_and_finite_helpers_reject_wrong_shapes(self) -> None:
        self.assertTrue(_monotone([0.0, 0.5, 0.5], increasing=True, tolerance=0.0))
        self.assertFalse(_monotone([0.0, 0.5, 0.4], increasing=True, tolerance=0.0))
        self.assertTrue(_monotone([1.0, 0.5], increasing=False, tolerance=0.0))
        self.assertTrue(_finite_tree({"rows": [1.0, None, True]}))
        self.assertFalse(_finite_tree({"rows": [float("nan")]}))

    def test_config_hash_mutation_is_rejected(self) -> None:
        config = json.loads(_CONFIG.read_text(encoding="utf-8"))
        config["expected_primitive_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "provenance mismatch"):
            _parse_config(config)


if __name__ == "__main__":
    unittest.main()
