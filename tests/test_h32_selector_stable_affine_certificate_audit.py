from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
import unittest

from pontius.h32_selector_stable_affine_certificate_audit import (
    _fixed_validation_scale,
    affine_direct_errors,
    parse_h32_selector_stable_affine_certificate_config,
)
from pontius.selector_stable_affine_response import (
    SelectorStableAffineSeatResult,
)


_ROOT = Path(__file__).parents[1]
_CONFIG = (
    _ROOT
    / "experiments/configs/h32-selector-stable-affine-certificate-v1.json"
)


def _row(*, target_player: int, utility: float, response: float) -> SelectorStableAffineSeatResult:
    return SelectorStableAffineSeatResult(
        target_player=target_player,
        acting_player=0,
        changed_public_node=1,
        profile_utility_intercept=utility,
        profile_utility_slope=-0.2,
        best_response_value_intercept=response,
        best_response_value_slope=-0.1,
        deviation_gain_intercept=max(0.0, response - utility),
        deviation_gap_slope=0.1,
        selector_stable_scale=0.75,
        first_switch_information_key=None,
        first_switch_source_action=None,
        first_switch_competing_action=None,
        first_switch_hand_index=None,
        selector_comparisons=1,
        exact_source_action_ties=0,
        changed_public_nodes=1,
        changed_opponent_public_nodes=int(target_player != 0),
        affected_terminal_contractions=1,
        full_terminal_contractions=2,
        reused_terminal_numerators=1,
        terminal_contraction_ms=1.0,
        reverse_evaluation_ms=1.0,
        wall_ms=2.0,
        maximum_terminal_middle_rank=1,
        maximum_gpu_pool_total_bytes=0,
    )


class H32SelectorStableAffineCertificateAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(_CONFIG.read_text(encoding="utf-8"))

    def test_frozen_retained_workload_and_proof_contract_are_exact(self) -> None:
        parsed = parse_h32_selector_stable_affine_certificate_config(self.config)
        self.assertEqual(len(parsed["targets"]), 6)
        self.assertEqual(parsed["acting_seats"], (0, 1, 2, 3, 4, 5))
        self.assertEqual(parsed["direction_family"], "regret_vertex")
        self.assertEqual(parsed["safety_fraction"], 0.5)
        self.assertEqual(parsed["fixed_validation_scale_index"], 16)
        self.assertEqual(parsed["gates"]["expected_public_blocks"], 36)
        self.assertNotIn(
            "minimum_selected_affine_candidates",
            parsed["gates"],
        )
        self.assertNotIn("require_street_ledger_fit", parsed["gates"])

    def test_contract_and_source_hash_mutations_are_rejected(self) -> None:
        changed = json.loads(json.dumps(self.config))
        changed["safety_fraction"] = 0.75
        with self.assertRaisesRegex(ValueError, "workload differs"):
            parse_h32_selector_stable_affine_certificate_config(changed)
        changed = json.loads(json.dumps(self.config))
        changed["expected_affine_verifier_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "source mismatch"):
            parse_h32_selector_stable_affine_certificate_config(changed)

    def test_fixed_validation_is_strictly_inside_the_selector_interval(self) -> None:
        scales = tuple(2.0**-index for index in range(34))
        selected = _fixed_validation_scale(
            scales,
            preferred_index=16,
            selector_limit=0.1,
        )
        self.assertIsNotNone(selected)
        assert selected is not None
        self.assertLess(selected, 0.1)
        self.assertLessEqual(selected, 2.0**-16)
        self.assertIsNone(
            _fixed_validation_scale(
                scales,
                preferred_index=16,
                selector_limit=1e-12,
            )
        )

    def test_affine_direct_error_helper_compares_all_three_quantities(self) -> None:
        rows = (
            _row(target_player=0, utility=1.0, response=1.5),
            _row(target_player=1, utility=-1.0, response=-0.25),
        )
        scale = 0.25
        direct = tuple(
            SimpleNamespace(
                profile_utility=row.profile_utility_intercept
                + scale * row.profile_utility_slope,
                best_response_value=row.best_response_value_intercept
                + scale * row.best_response_value_slope,
                deviation_gain=max(
                    0.0,
                    row.deviation_gain_intercept
                    + scale * row.deviation_gap_slope,
                ),
            )
            for row in rows
        )
        errors = affine_direct_errors(rows, direct, scale=scale)
        self.assertEqual(errors["maximum_utility_error"], 0.0)
        self.assertEqual(errors["maximum_best_response_error"], 0.0)
        self.assertLessEqual(errors["maximum_deviation_gain_error"], 2e-16)


if __name__ == "__main__":
    unittest.main()
