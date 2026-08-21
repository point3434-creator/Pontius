from __future__ import annotations

import json
from pathlib import Path
import unittest

from pontius.evidence_protocol import DEFAULT_GPU_NUMERICAL_IDENTITY
from pontius.h32_selector_stable_affine_certificate_audit_v2 import (
    _decision_signature,
    parse_h32_selector_stable_affine_certificate_v2_config,
)


_ROOT = Path(__file__).parents[1]
_CONFIG = (
    _ROOT / "experiments/configs/h32-selector-stable-affine-certificate-v2.json"
)
_FAILED = (
    _ROOT / "experiments/results/h32-selector-stable-affine-certificate-v1.json"
)


class H32SelectorStableAffineCertificateAuditV2Tests(unittest.TestCase):
    def test_successor_changes_only_the_forbidden_warm_digest_gate(self) -> None:
        config = json.loads(_CONFIG.read_text(encoding="utf-8"))
        parsed = parse_h32_selector_stable_affine_certificate_v2_config(config)
        self.assertEqual(
            parsed["maximum_warm_start_probability_error"],
            DEFAULT_GPU_NUMERICAL_IDENTITY.maximum_policy_probability_error,
        )
        self.assertEqual(
            parsed["maximum_warm_start_mean_total_variation"],
            DEFAULT_GPU_NUMERICAL_IDENTITY.maximum_policy_mean_information_set_total_variation,
        )
        self.assertFalse(parsed["require_warm_start_digest_identity"])
        self.assertEqual(len(parsed["base"]["targets"]), 6)

        for field, value in (
            ("maximum_warm_start_probability_error", 1e-11),
            ("maximum_warm_start_mean_total_variation", 1e-12),
            ("require_warm_start_digest_identity", True),
        ):
            mutated = dict(config)
            mutated[field] = value
            with self.assertRaisesRegex(ValueError, "workload differs"):
                parse_h32_selector_stable_affine_certificate_v2_config(mutated)

        mutated = dict(config)
        mutated["expected_failed_result_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "source mismatch"):
            parse_h32_selector_stable_affine_certificate_v2_config(mutated)

    def test_failed_artifact_has_only_the_known_gate_failure(self) -> None:
        failed = json.loads(_FAILED.read_text(encoding="utf-8"))
        identity = DEFAULT_GPU_NUMERICAL_IDENTITY
        mean_tv_ceiling = identity.maximum_policy_mean_information_set_total_variation
        false_gates = {
            key
            for key, value in failed["gates"].items()
            if key != "passed" and not value
        }
        self.assertEqual(false_gates, {"numerical_warm_start_identity"})
        self.assertTrue(
            all(
                target["warm_start_distance"]["maximum_probability_error"]
                <= DEFAULT_GPU_NUMERICAL_IDENTITY.maximum_policy_probability_error
                for target in failed["target_rows"]
            )
        )
        self.assertTrue(
            all(
                target["warm_start_distance"]["mean_total_variation"]
                <= mean_tv_ceiling
                for target in failed["target_rows"]
            )
        )

    def test_decision_signature_excludes_timing_and_value(self) -> None:
        failed = json.loads(_FAILED.read_text(encoding="utf-8"))
        first = _decision_signature(failed)
        failed["target_rows"][0]["search_step_ms"] *= 2.0
        failed["target_rows"][0]["block_rows"][0][
            "selected_positive_certified_value"
        ] *= 0.5
        self.assertEqual(first, _decision_signature(failed))


if __name__ == "__main__":
    unittest.main()
