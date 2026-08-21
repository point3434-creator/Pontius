from __future__ import annotations

import math
import unittest

from pontius.evidence_protocol import (
    DEFAULT_GPU_NUMERICAL_IDENTITY,
    GPUNumericalIdentityTolerances,
    validate_digest_gate_purpose,
    validate_gpu_numerical_identity,
)


class EvidenceProtocolTests(unittest.TestCase):
    def test_default_gpu_tolerances_are_the_corrected_repository_constants(self) -> None:
        self.assertEqual(
            DEFAULT_GPU_NUMERICAL_IDENTITY,
            GPUNumericalIdentityTolerances(
                maximum_accumulator_absolute_error=1e-12,
                maximum_policy_probability_error=1e-12,
                maximum_policy_mean_information_set_total_variation=1e-13,
                maximum_quality_absolute_error=1e-10,
            ),
        )

    def test_numerical_identity_accepts_ceilings_and_rejects_excess_or_nonfinite(self) -> None:
        validate_gpu_numerical_identity(
            maximum_accumulator_absolute_error=1e-12,
            maximum_policy_probability_error=1e-12,
            policy_mean_information_set_total_variation=1e-13,
            maximum_quality_absolute_error=1e-10,
        )
        with self.assertRaisesRegex(ValueError, "exceeds its frozen ceiling"):
            validate_gpu_numerical_identity(
                maximum_accumulator_absolute_error=1.0001e-12,
                maximum_policy_probability_error=0.0,
                policy_mean_information_set_total_variation=0.0,
                maximum_quality_absolute_error=0.0,
            )
        for field in (
            "maximum_accumulator_absolute_error",
            "maximum_policy_probability_error",
            "policy_mean_information_set_total_variation",
            "maximum_quality_absolute_error",
        ):
            values = {
                "maximum_accumulator_absolute_error": 0.0,
                "maximum_policy_probability_error": 0.0,
                "policy_mean_information_set_total_variation": 0.0,
                "maximum_quality_absolute_error": 0.0,
            }
            values[field] = math.inf
            with self.assertRaisesRegex(ValueError, "finite and nonnegative"):
                validate_gpu_numerical_identity(**values)

    def test_digest_gate_purpose_is_fail_closed_for_cross_run_semantics(self) -> None:
        for purpose in (
            "immutable_input_identity",
            "serialized_object_identity",
            "immediate_restore_reexport_identity",
            "explicit_bitwise_determinism_experiment",
        ):
            self.assertEqual(validate_digest_gate_purpose(purpose), purpose)
        with self.assertRaisesRegex(ValueError, "diagnostic"):
            validate_digest_gate_purpose("ordinary_cross_run_gpu_semantics")


if __name__ == "__main__":
    unittest.main()
