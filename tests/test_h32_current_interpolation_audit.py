from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from pontius.h32_current_interpolation_audit import (
    _acceptance_state,
    _candidate_source_row,
    interpolate_behavioral_policy,
    parse_h32_current_interpolation_config,
)
from pontius.h32_warm_candidate_stream_audit import _source_target
from pontius.h32_warm_search_acceptance_audit import _current_policy_from_state
from pontius.real_policy import policy_digest


_ROOT = Path(__file__).parents[1]
_CONFIG = _ROOT / "experiments" / "configs" / "h32-current-interpolation-audit-v1.json"
_CANDIDATE_SOURCE = (
    _ROOT / "experiments" / "results" / "h32-warm-candidate-stream-v1.json"
)
_ACCEPTANCE_SOURCE = (
    _ROOT / "experiments" / "results" / "h32-warm-search-acceptance-v1.json"
)


class H32CurrentInterpolationAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(_CONFIG.read_text(encoding="utf-8"))
        cls.candidate_source = json.loads(
            _CANDIDATE_SOURCE.read_text(encoding="utf-8")
        )
        cls.acceptance_source = json.loads(
            _ACCEPTANCE_SOURCE.read_text(encoding="utf-8")
        )

    def test_frozen_matrix_has_fixed_alphas_and_no_quality_gate(self) -> None:
        parsed = parse_h32_current_interpolation_config(self.config)
        self.assertEqual(parsed["endpoint_iterations"], (1, 2))
        self.assertEqual(parsed["interpolation_alphas"], (0.25, 0.5, 0.75))
        self.assertEqual(
            parsed["candidate_order"],
            (
                "search_current1",
                "interpolate_current1_to2_alpha025",
                "interpolate_current1_to2_alpha050",
                "interpolate_current1_to2_alpha075",
                "search_current2",
            ),
        )
        self.assertNotIn("minimum_safe_interpolation_gain", parsed["gates"])
        self.assertNotIn("required_winning_alpha", parsed["gates"])

    def test_sources_alphas_schedule_and_gates_are_immutable(self) -> None:
        mutations = []
        for key, value in (
            ("evidence_stage", "after_interpolation_labels"),
            ("expected_candidate_stream_source_sha256", "0" * 64),
            ("endpoint_iterations", [1, 4]),
            ("interpolation_alphas", [0.5]),
            ("candidate_order", ["search_current1"]),
            ("acceptance_guard_normalized", 1e-8),
            ("maximum_feature_width_per_batch", 768),
        ):
            mutation = deepcopy(self.config)
            mutation[key] = value
            mutations.append(mutation)
        gate = deepcopy(self.config)
        gate["gates"]["maximum_total_audit_seconds"] = 1800.0
        mutations.append(gate)
        extra = deepcopy(self.config)
        extra["alpha_selector"] = "largest_safe_observed"
        mutations.append(extra)
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                with self.assertRaises(ValueError):
                    parse_h32_current_interpolation_config(mutation)

    def test_behavioral_interpolation_has_exact_endpoints_and_midpoint(self) -> None:
        first = {
            "a": {"x": 0.25, "y": 0.75},
            "b": {"x": 1.0, "y": 0.0},
        }
        second = {
            "a": {"x": 0.75, "y": 0.25},
            "b": {"x": 0.0, "y": 1.0},
        }
        self.assertEqual(interpolate_behavioral_policy(first, second, 0.0), first)
        self.assertEqual(interpolate_behavioral_policy(first, second, 1.0), second)
        self.assertEqual(
            interpolate_behavioral_policy(first, second, 0.5),
            {"a": {"x": 0.5, "y": 0.5}, "b": {"x": 0.5, "y": 0.5}},
        )
        with self.assertRaises(ValueError):
            interpolate_behavioral_policy(first, second, -0.1)
        with self.assertRaises(ValueError):
            interpolate_behavioral_policy(first, {"c": {"x": 1.0}}, 0.5)

    def test_all_eight_endpoint_policies_match_both_frozen_sources(self) -> None:
        for family in self.config["range_families"]:
            for shift in self.config["target_shifts"]:
                with self.subTest(family=family, shift=shift):
                    candidate_target = _source_target(
                        self.candidate_source,
                        family=family,
                        shift=shift,
                    )
                    acceptance_target = _source_target(
                        self.acceptance_source,
                        family=family,
                        shift=shift,
                    )
                    for iteration in (1, 2):
                        state = _acceptance_state(
                            acceptance_target,
                            iteration=iteration,
                        )
                        policy = _current_policy_from_state(state)
                        quality = _candidate_source_row(
                            candidate_target,
                            f"search_current{iteration}",
                        )["quality"]
                        self.assertEqual(
                            policy_digest(policy),
                            state["current_policy_sha256"],
                        )
                        self.assertEqual(
                            policy_digest(policy),
                            quality["policy_sha256"],
                        )


if __name__ == "__main__":
    unittest.main()
