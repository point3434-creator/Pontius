from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from pontius.multi_size_leaf_adjoint_audit import (
    parse_multi_size_leaf_adjoint_config,
)


_ROOT = Path(__file__).parents[1]
_CONFIG = (
    _ROOT
    / "experiments"
    / "configs"
    / "multi-size-leaf-adjoint-audit-v1.json"
)


class MultiSizeLeafAdjointAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(_CONFIG.read_text(encoding="utf-8"))

    def test_frozen_workload_is_exactly_the_first_action_width_ladder(self) -> None:
        parsed = parse_multi_size_leaf_adjoint_config(self.config)
        self.assertEqual(parsed["bet_sizes"], (3.0, 6.0))
        self.assertEqual(parsed["hands_per_player"], (4, 7))
        self.assertEqual(parsed["range_families"], ("balanced", "blocker_heavy"))
        self.assertEqual(parsed["gates"]["expected_two_size_public_nodes"], 763)
        self.assertEqual(parsed["gates"]["expected_leaf_action_reads"], 1512)
        self.assertEqual(parsed["gates"]["maximum_action_value_loss"], 1e-9)

    def test_config_rejects_source_workload_and_gate_edits(self) -> None:
        changed = copy.deepcopy(self.config)
        changed["bet_sizes"] = [3.0, 9.0]
        with self.assertRaisesRegex(ValueError, "workload"):
            parse_multi_size_leaf_adjoint_config(changed)

        changed = copy.deepcopy(self.config)
        changed["expected_sized_leaf_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "source hash"):
            parse_multi_size_leaf_adjoint_config(changed)

        changed = copy.deepcopy(self.config)
        changed["gates"]["maximum_action_numerator_error"] = 1e-6
        with self.assertRaisesRegex(ValueError, "gates"):
            parse_multi_size_leaf_adjoint_config(changed)


if __name__ == "__main__":
    unittest.main()
