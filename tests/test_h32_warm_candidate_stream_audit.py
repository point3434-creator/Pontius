from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from pontius.h32_warm_candidate_stream_audit import (
    _descriptor_digest,
    _portfolio_row,
    _source_state_rows,
    _source_target,
    parse_h32_warm_candidate_stream_config,
)


_ROOT = Path(__file__).parents[1]
_CONFIG = _ROOT / "experiments" / "configs" / "h32-warm-candidate-stream-v1.json"
_SOURCE = _ROOT / "experiments" / "results" / "h32-warm-search-acceptance-v1.json"


def _quality(value: float, gains: list[float], wall_ms: float = 2.0) -> dict[str, object]:
    return {
        "nash_conv": value * 30.0,
        "normalized_nash_conv": value,
        "deviation_gains": gains,
        "wall_ms": wall_ms,
    }


def _candidate(
    candidate_id: str,
    kind: str,
    value: float,
    gains: list[float],
) -> dict[str, object]:
    return {
        "candidate_id": candidate_id,
        "policy_kind": kind,
        "cumulative_search_ms": 10.0,
        "quality": _quality(value, gains),
    }


class H32WarmCandidateStreamAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(_CONFIG.read_text(encoding="utf-8"))
        cls.source = json.loads(_SOURCE.read_text(encoding="utf-8"))

    def test_frozen_matrix_has_no_strategy_outcome_gate(self) -> None:
        parsed = parse_h32_warm_candidate_stream_config(self.config)
        self.assertEqual(parsed["source_search_iterations"], (1, 2, 4))
        self.assertEqual(parsed["final_search_iteration"], 8)
        self.assertEqual(
            parsed["candidate_order"],
            (
                "search_current1",
                "search_average1",
                "search_current2",
                "search_average2",
                "search_current4",
                "search_average4",
                "search_current8",
                "search_average8",
            ),
        )
        self.assertNotIn("minimum_quality_improvement", parsed["gates"])
        self.assertNotIn("minimum_current_acceptance", parsed["gates"])

    def test_sources_workload_schedule_and_gates_are_immutable(self) -> None:
        mutations = []
        for key, value in (
            ("evidence_stage", "after_current_labels"),
            ("expected_acceptance_source_sha256", "0" * 64),
            ("source_search_iterations", [1, 2]),
            ("final_search_iteration", 16),
            ("candidate_order", ["search_average1"]),
            ("portfolio_kinds", ["full_interleaved"]),
            ("acceptance_guard_normalized", 1e-8),
            ("maximum_feature_width_per_batch", 768),
        ):
            mutation = deepcopy(self.config)
            mutation[key] = value
            mutations.append(mutation)
        gate = deepcopy(self.config)
        gate["gates"]["maximum_total_audit_seconds"] = 3600.0
        mutations.append(gate)
        extra = deepcopy(self.config)
        extra["selector"] = "best_observed_policy_kind"
        mutations.append(extra)
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                with self.assertRaises(ValueError):
                    parse_h32_warm_candidate_stream_config(mutation)

    def test_all_twelve_source_states_and_policies_reconstruct_exactly(self) -> None:
        for family in self.config["range_families"]:
            for shift in self.config["target_shifts"]:
                with self.subTest(family=family, shift=shift):
                    target = _source_target(
                        self.source,
                        family=family,
                        shift=shift,
                    )
                    rows, currents, averages = _source_state_rows(
                        target,
                        iterations=(1, 2, 4),
                    )
                    self.assertEqual(len(rows), 3)
                    self.assertEqual(set(currents), {1, 2, 4})
                    self.assertEqual(set(averages), {1, 2, 4})
                    self.assertTrue(all(row["state_digest_identity"] for row in rows))
                    self.assertTrue(all(row["policy_digest_identity"] for row in rows))

    def test_descriptor_digest_excludes_timing_only(self) -> None:
        first = {"shift": "x", "partition": 1.25, "marginal_measurement_ms": 1.0}
        second = {"shift": "x", "partition": 1.25, "marginal_measurement_ms": 99.0}
        self.assertEqual(_descriptor_digest(first), _descriptor_digest(second))
        second["partition"] = 1.5
        self.assertNotEqual(_descriptor_digest(first), _descriptor_digest(second))

    def test_portfolio_preserves_vector_guard_and_charges_all_candidates(self) -> None:
        baseline = _quality(0.10, [0.5] * 6, wall_ms=3.0)
        safe = _candidate("search_current1", "current", 0.08, [0.4] * 6)
        aggregate_only = _candidate(
            "search_average1",
            "average",
            0.06,
            [0.3, 0.3, 0.3, 0.3, 0.3, 0.7],
        )
        portfolio = _portfolio_row(
            name="full_interleaved",
            baseline=baseline,
            candidates=[safe, aggregate_only],
            payoff_span=30.0,
            guard=1e-10,
            target_compile_ms=5.0,
        )
        self.assertEqual(portfolio["final_aggregate_incumbent"], "search_average1")
        self.assertEqual(portfolio["final_unilateral_incumbent"], "search_current1")
        self.assertAlmostEqual(portfolio["unilateral_normalized_reduction"], 0.02)
        self.assertEqual(portfolio["candidate_evaluation_ms"], 4.0)
        self.assertEqual(portfolio["verified_precompiled_ms"], 14.0)
        self.assertEqual(portfolio["verified_one_shot_ms"], 22.0)
        self.assertTrue(portfolio["nonworsening"])
        self.assertTrue(portfolio["guard_semantics"])


if __name__ == "__main__":
    unittest.main()
