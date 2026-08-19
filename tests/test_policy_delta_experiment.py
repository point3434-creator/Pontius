from __future__ import annotations

import json
import unittest
from pathlib import Path

from pontius.policy_delta_experiment import _validate_config, accept_candidate


class PolicyDeltaExperimentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config_path = Path(
            "experiments/configs/policy-delta-recertification-development-v1.json"
        )
        cls.config = json.loads(cls.config_path.read_text(encoding="utf-8"))

    def test_frozen_config_parses_exactly(self) -> None:
        parsed = _validate_config(self.config)
        self.assertEqual(parsed["candidate_masks"], ("b3r1", "b3r2"))
        self.assertEqual(parsed["primary_mask"], "b3r2")
        self.assertEqual(parsed["timing_measurement_repetitions"], 7)
        self.assertEqual(parsed["execution_modes"], ("sparse", "dense", "auto"))

    def test_acceptance_is_scale_invariant_and_ties_choose_no_op(self) -> None:
        for scale in (0.5, 1.0, 2.0, 4.0):
            self.assertTrue(
                accept_candidate(
                    2.0 * scale,
                    1.5 * scale,
                    payoff_span=10.0 * scale,
                    tolerance_by_payoff_span=1e-10,
                )
            )
            self.assertFalse(
                accept_candidate(
                    2.0 * scale,
                    2.0 * scale - 0.5e-9 * scale,
                    payoff_span=10.0 * scale,
                    tolerance_by_payoff_span=1e-10,
                )
            )
            self.assertFalse(
                accept_candidate(
                    2.0 * scale,
                    2.1 * scale,
                    payoff_span=10.0 * scale,
                    tolerance_by_payoff_span=1e-10,
                )
            )

    def test_config_rejects_post_freeze_mask_or_timing_changes(self) -> None:
        changed_mask = dict(self.config)
        changed_mask["candidate_masks"] = ["b3r2"]
        with self.assertRaisesRegex(ValueError, "frozen"):
            _validate_config(changed_mask)

        changed_timing = dict(self.config)
        changed_timing["timing_measurement_repetitions"] = 3
        with self.assertRaisesRegex(ValueError, "timing protocol"):
            _validate_config(changed_timing)

    def test_acceptance_rejects_nonfinite_or_invalid_scale_inputs(self) -> None:
        with self.assertRaisesRegex(ValueError, "finite"):
            accept_candidate(
                float("nan"),
                1.0,
                payoff_span=10.0,
                tolerance_by_payoff_span=1e-10,
            )
        with self.assertRaisesRegex(ValueError, "positive"):
            accept_candidate(
                1.0,
                0.5,
                payoff_span=0.0,
                tolerance_by_payoff_span=1e-10,
            )


if __name__ == "__main__":
    unittest.main()
