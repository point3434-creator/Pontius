from __future__ import annotations

import ast
import unittest
from dataclasses import replace
from pathlib import Path

from pontius.sizing_power_diagnostic import QualificationStopReason
from pontius.width_four_sizing_power import (
    ADR0297_POOL_SHA256,
    build_adr0297_width_four_pool,
)
from pontius.width_four_sizing_power_evaluation import (
    ADR0297_CHIP_OBJECTIVE_ALLOWANCE,
    ADR0297_ENVELOPE_CONSTRAINT_ALLOWANCE,
    ADR0297_LP_DUALITY_ALLOWANCE,
    ADR0297_PROBABILITY_ALLOWANCE,
    ADR0297_SIMPLEX_PIVOT_CAP,
    WidthFourCampaignStopReason,
    run_adr0297_width_four_campaign,
)

_ROOT = Path(__file__).parents[1]


class WidthFourSizingPowerEvaluationTests(unittest.TestCase):
    def test_three_frozen_width_four_replications_pass_candidate_blind(self) -> None:
        paths = (
            _ROOT / "src/pontius/width_four_sizing_power_evaluation.py",
            _ROOT / "tests/test_width_four_sizing_power_evaluation.py",
        )
        for path in paths:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            imports = tuple(
                (node.module, tuple(alias.name for alias in node.names))
                for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom) and node.module is not None
            )
            imported_modules = {module for module, _names in imports}
            self.assertNotIn("pontius.legal_action_abstraction", imported_modules)
            self.assertNotIn("legal_action_abstraction", imported_modules)
            imported_names = {name for _module, names in imports for name in names}
            self.assertNotIn("build_adr0295_sizing_power_pool", imported_names)
            self.assertNotIn(
                "run_candidate_blind_sizing_power_qualification",
                imported_names,
            )

        campaign = run_adr0297_width_four_campaign()
        self.assertIs(
            campaign.stop_reason,
            WidthFourCampaignStopReason.PASSED_ALL_BATCHES,
        )
        self.assertTrue(campaign.passed)
        self.assertGreater(campaign.elapsed_seconds, 0.0)
        self.assertEqual(
            campaign.digest,
            "4c37efdf69c3c96cc3aeef0bf22ab5f2a8078fd673c429ecf61b0f96b55d4ccd",
        )

        expected_opened = (23, 24, 32)
        expected_indices = (
            (0, 1, 3, 5, 8, 10, 13, 15, 17, 20, 21, 22),
            (2, 5, 7, 8, 12, 13, 14, 16, 17, 18, 22, 23),
            (0, 5, 7, 8, 11, 13, 18, 25, 26, 27, 30, 31),
        )
        expected_result_digests = (
            "fcdd3a31301286b0db0e3c37201756f980ed611eaa9ed0f3acb2adb8e99c2a58",
            "829231b00f4f70f65343654c43bc289cd94677dd63ad6dfe93528470f11955a1",
            "eceb8b2d74be8de8360e1f23b7793745f6b53a3f93aa2d2ade4fe6cd0a3b6da6",
        )
        expected_panel_digests = (
            "7ad25925d2108f6201aaeab2781645ec2366d171e374d83d452dd729a536a034",
            "109e1a3f4c0841cbc7fe60e7b5add9688d9461df70f1468cf4a60283cf3beba3",
            "a9e6872992dc0f74f5c33f93abce4da0eedbb48ad8e53df728e91264230c042b",
        )
        expected_control_digests = (
            "8cf5150af471041182feb8dd6b518f85d2253357f0e61a5b0a9755caac8a0641",
            "c722d3b9ef44d2ee7dc78c053b30ec4b3f91ee16743fdbe267ec0ad707a60f3c",
            "f00843dc40945944856620c9067fcb3f67c7a36c94b8f35e18bd1d71f220202f",
        )
        self.assertEqual(len(campaign.batch_results), 3)
        self.assertEqual(len(campaign.teacher_controls), 3)
        for batch_index, (result, control) in enumerate(
            zip(campaign.batch_results, campaign.teacher_controls, strict=True)
        ):
            self.assertEqual(result.batch_index, batch_index)
            self.assertEqual(result.pool_digest, ADR0297_POOL_SHA256[batch_index])
            self.assertIs(result.stop_reason, QualificationStopReason.TARGET_REACHED)
            self.assertEqual(result.opened_context_count, expected_opened[batch_index])
            self.assertEqual(result.qualified_indices, expected_indices[batch_index])
            self.assertEqual(result.digest, expected_result_digests[batch_index])
            pool = build_adr0297_width_four_pool(batch_index=batch_index)
            result.verify_against_pool(pool=pool)
            panel = result.qualified_panel(pool=pool)
            self.assertEqual(panel.digest, expected_panel_digests[batch_index])
            selected = tuple(
                pool.contexts[index] for index in result.qualified_indices
            )
            self.assertGreaterEqual(len({context.pot for context in selected}), 3)
            self.assertGreaterEqual(len({context.stack for context in selected}), 3)
            self.assertGreaterEqual(
                len({context.showdown_signs for context in selected}),
                8,
            )
            for observation in result.observations:
                self.assertLessEqual(
                    observation.max_probability_residual,
                    ADR0297_PROBABILITY_ALLOWANCE.value,
                )
                self.assertLessEqual(
                    observation.max_chip_objective_error,
                    ADR0297_CHIP_OBJECTIVE_ALLOWANCE.chips,
                )
                self.assertLessEqual(
                    observation.max_lp_duality_gap,
                    ADR0297_LP_DUALITY_ALLOWANCE.chips,
                )
                self.assertLessEqual(
                    observation.max_envelope_constraint_violation_chips,
                    ADR0297_ENVELOPE_CONSTRAINT_ALLOWANCE.chips,
                )
                self.assertLessEqual(
                    observation.full_simplex_pivots,
                    ADR0297_SIMPLEX_PIVOT_CAP,
                )
                self.assertLessEqual(
                    observation.narrow_simplex_pivots,
                    ADR0297_SIMPLEX_PIVOT_CAP,
                )
            self.assertEqual(control.batch_index, batch_index)
            self.assertEqual(control.panel_digest, expected_panel_digests[batch_index])
            self.assertEqual(control.digest, expected_control_digests[batch_index])

        first = campaign.batch_results[0]
        invalid_observations = (
            replace(first.observations[0], payoff_span=first.observations[0].payoff_span + 1),
            *first.observations[1:],
        )
        invalid = replace(first, observations=invalid_observations)
        with self.assertRaisesRegex(ValueError, "payoff span"):
            invalid.verify_against_pool(pool=build_adr0297_width_four_pool(batch_index=0))


if __name__ == "__main__":
    unittest.main()
