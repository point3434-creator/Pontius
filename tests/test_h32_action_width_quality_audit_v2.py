from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from pontius.h32_action_width_quality_audit_v2 import (
    project_parent_construction_descriptor,
    parse_h32_action_width_quality_v2_config,
    target_identity_diagnostics,
)


_ROOT = Path(__file__).parents[1]
_CONFIG = _ROOT / "experiments" / "configs" / "h32-action-width-quality-v2.json"
_V1_RESULT = _ROOT / "experiments" / "results" / "h32-action-width-quality-v1.json"
_PARENT = _ROOT / "experiments" / "results" / "fresh-h32-strategy-transfer-audit-v1.json"


class H32ActionWidthQualityV2IdentityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.v1_result = json.loads(_V1_RESULT.read_text(encoding="utf-8"))
        cls.parent = json.loads(_PARENT.read_text(encoding="utf-8"))

    def _expected(self, actual: dict[str, object]) -> dict[str, object]:
        return next(
            row
            for row in self.parent["targets"]
            if row["range_family"] == actual["range_family"]
            and row["target_shift"] == actual["target_shift"]
        )

    def _diagnostics(
        self,
        actual: dict[str, object],
        *,
        descriptor: dict[str, object] | None = None,
        belief_digest: str | None = None,
        expected: dict[str, object] | None = None,
    ) -> dict[str, object]:
        target_descriptor = actual["target_descriptor"] if descriptor is None else descriptor
        return target_identity_diagnostics(
            descriptor=target_descriptor,
            target_belief_sha256=(
                actual["target_belief_sha256"]
                if belief_digest is None
                else belief_digest
            ),
            hands_by_player_identity=bool(target_descriptor["hand_axes_identity"]),
            expected=self._expected(actual) if expected is None else expected,
            shift=actual["target_shift"],
        )

    def test_all_v1_targets_match_exact_parent_core_projection(self) -> None:
        self.assertEqual(len(self.v1_result["targets"]), 4)
        for actual in self.v1_result["targets"]:
            with self.subTest(
                family=actual["range_family"], shift=actual["target_shift"]
            ):
                diagnostics = self._diagnostics(actual)
                self.assertTrue(diagnostics["passed"])
                self.assertTrue(diagnostics["construction_field_set_identity"])
                self.assertTrue(diagnostics["parent_field_set_identity"])
                self.assertTrue(diagnostics["parent_core_projection_identity"])
                self.assertTrue(diagnostics["belief_digest_identity"])
                self.assertTrue(diagnostics["hand_axes_identity"])

    def test_projection_does_not_mutate_augmented_parent(self) -> None:
        expected = copy.deepcopy(self.parent["targets"][0])
        before = copy.deepcopy(expected)
        projected = project_parent_construction_descriptor(
            expected,
            shift=expected["target_shift"],
        )
        self.assertEqual(expected, before)
        self.assertNotIn("marginal_measurement_ms", projected)
        self.assertIn("selected_hand", projected)

    def test_every_core_field_mutation_is_rejected(self) -> None:
        for actual in self.v1_result["targets"]:
            for field in actual["target_descriptor"]:
                changed = copy.deepcopy(actual["target_descriptor"])
                value = changed[field]
                if isinstance(value, bool):
                    changed[field] = not value
                elif isinstance(value, (int, float)):
                    changed[field] = value + 1
                elif isinstance(value, str):
                    changed[field] = value + "_changed"
                elif isinstance(value, list):
                    changed[field] = [*value, "changed"]
                else:
                    self.fail(f"unhandled descriptor type for {field}: {type(value)}")
                with self.subTest(
                    family=actual["range_family"],
                    shift=actual["target_shift"],
                    field=field,
                ):
                    self.assertFalse(self._diagnostics(actual, descriptor=changed)["passed"])

    def test_field_set_digest_and_axes_mutations_are_rejected(self) -> None:
        actual = self.v1_result["targets"][0]
        missing = copy.deepcopy(actual["target_descriptor"])
        missing.pop("tie_rule")
        self.assertFalse(self._diagnostics(actual, descriptor=missing)["passed"])

        extra = copy.deepcopy(actual["target_descriptor"])
        extra["marginal_measurement_ms"] = 0.0
        self.assertFalse(self._diagnostics(actual, descriptor=extra)["passed"])

        self.assertFalse(self._diagnostics(actual, belief_digest="0" * 64)["passed"])

        axes = copy.deepcopy(actual["target_descriptor"])
        axes["hand_axes_identity"] = False
        self.assertFalse(self._diagnostics(actual, descriptor=axes)["passed"])

    def test_unknown_parent_measurement_field_is_rejected(self) -> None:
        actual = self.v1_result["targets"][0]
        expected = copy.deepcopy(self._expected(actual))
        expected["target_descriptor"]["posthoc_unknown"] = 1
        diagnostics = self._diagnostics(actual, expected=expected)
        self.assertFalse(diagnostics["parent_field_set_identity"])
        self.assertFalse(diagnostics["passed"])


class H32ActionWidthQualityV2ConfigTests(unittest.TestCase):
    def test_config_pins_known_outcome_but_keeps_it_out_of_gates(self) -> None:
        config = json.loads(_CONFIG.read_text(encoding="utf-8"))
        parsed = parse_h32_action_width_quality_v2_config(config)
        self.assertEqual(
            parsed["known_v1_outcome"],
            "both_arms_abstained_on_all_four_targets_with_zero_selected_reduction",
        )
        self.assertEqual(
            parsed["strategy_claim_policy"],
            "top_level_claim_remains_null_regardless_of_arm_outcome",
        )
        self.assertNotIn("selected_reduction", parsed["gates"])
        self.assertNotIn("require_two_size_win", parsed["gates"])

    def test_identity_contract_or_failed_gate_mutation_is_rejected(self) -> None:
        config = json.loads(_CONFIG.read_text(encoding="utf-8"))
        for mutation in (
            lambda row: row.__setitem__("target_identity_contract", "weaker"),
            lambda row: row["gates"].__setitem__("expected_v1_failed_gates", []),
            lambda row: row.__setitem__("expected_v1_result_sha256", "0" * 64),
        ):
            changed = copy.deepcopy(config)
            mutation(changed)
            with self.assertRaises(ValueError):
                parse_h32_action_width_quality_v2_config(changed)


if __name__ == "__main__":
    unittest.main()
