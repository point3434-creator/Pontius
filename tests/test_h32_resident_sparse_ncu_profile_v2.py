from __future__ import annotations

import json
from pathlib import Path
import unittest

from pontius import h32_resident_sparse_ncu_profile_v2 as profile_v2


_ROOT = Path(__file__).parents[1]
_CONFIG = _ROOT / "experiments/configs/h32-resident-sparse-ncu-profile-v2.json"


class H32ResidentSparseNcuProfileV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(_CONFIG.read_text(encoding="utf-8"))

    def test_only_console_output_contract_changes(self) -> None:
        parsed = profile_v2.parse_h32_resident_sparse_ncu_profile_v2_config(
            self.config
        )
        base = parsed["parsed_base"]
        self.assertEqual(base["feature_width"], 384)
        self.assertEqual(base["directions"], ["right_to_left", "left_to_right"])
        self.assertEqual(
            parsed["correction_rule"],
            "add_print_summary_per_kernel_require_nonempty_stdout_and_make_"
            "core_metric_presence_nonvacuous",
        )

    def test_driver_requests_per_kernel_page_and_preserves_v1(self) -> None:
        source = profile_v2._IMPLEMENTATION.read_text(encoding="utf-8")
        self.assertIn('"--print-summary"', source)
        self.assertIn('"per-kernel"', source)
        self.assertIn('"stdout_nonempty"', source)
        self.assertIn('"core_metrics_present": bool(kernels)', source)
        self.assertIn('"metrics_finite": bool(kernels)', source)
        self.assertNotEqual(profile_v2._OUTPUT, profile_v2._V1_RESULT)
        self.assertNotIn("_V1_RESULT.write_text", source)

    def test_rejected_parent_and_source_mutations_are_rejected(self) -> None:
        changed = json.loads(json.dumps(self.config))
        changed["correction_rule"] = "also_change_the_metric_set"
        with self.assertRaisesRegex(ValueError, "correction differs"):
            profile_v2.parse_h32_resident_sparse_ncu_profile_v2_config(changed)

        changed = json.loads(json.dumps(self.config))
        changed["expected_v1_result_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "source mismatch"):
            profile_v2.parse_h32_resident_sparse_ncu_profile_v2_config(changed)

if __name__ == "__main__":
    unittest.main()
