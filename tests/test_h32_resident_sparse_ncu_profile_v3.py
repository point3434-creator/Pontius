from __future__ import annotations

import inspect
import json
from pathlib import Path
import unittest

from pontius import h32_resident_sparse_ncu_profile_v3 as profile_v3


_ROOT = Path(__file__).parents[1]
_CONFIG = _ROOT / "experiments/configs/h32-resident-sparse-ncu-profile-v3.json"


class H32ResidentSparseNcuProfileV3Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(_CONFIG.read_text(encoding="utf-8"))

    def test_final_correction_is_child_targeting_and_wide_raw_page(self) -> None:
        parsed = profile_v3.parse_h32_resident_sparse_ncu_profile_v3_config(
            self.config
        )
        self.assertEqual(
            parsed["correction_rule"],
            "target_all_python_child_processes_and_restore_the_v1_wide_raw_"
            "page_without_per_kernel_summary",
        )
        source = inspect.getsource(profile_v3._run_direction)
        self.assertIn('"--target-processes",\n            "all"', source)
        self.assertIn('"--page",\n            "raw"', source)
        self.assertNotIn("--print-summary", source)

    def test_v3_preserves_prior_artifacts_and_uses_v3_output(self) -> None:
        source = profile_v3._IMPLEMENTATION.read_text(encoding="utf-8")
        self.assertNotEqual(profile_v3._OUTPUT, profile_v3._V2_RESULT)
        self.assertNotIn("_V2_RESULT.write_text", source)
        self.assertIn('result["schema_version"] = 3', source)
        self.assertIn('result["methodology"]["rejected_v2_reused"] = False', source)

    def test_correction_and_source_mutations_are_rejected(self) -> None:
        changed = json.loads(json.dumps(self.config))
        changed["correction_rule"] = "target_all_and_change_metrics"
        with self.assertRaisesRegex(ValueError, "correction differs"):
            profile_v3.parse_h32_resident_sparse_ncu_profile_v3_config(changed)

        changed = json.loads(json.dumps(self.config))
        changed["expected_v2_result_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "source mismatch"):
            profile_v3.parse_h32_resident_sparse_ncu_profile_v3_config(changed)


if __name__ == "__main__":
    unittest.main()
