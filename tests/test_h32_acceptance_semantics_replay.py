from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from pontius.h32_acceptance_semantics_replay import (
    _sha256,
    merge_policy_candidates,
    parse_h32_acceptance_semantics_config,
    replay_fixed_blueprint_stream,
    replay_incumbent_relative_pareto,
    select_fixed_blueprint_envelope,
)


_ROOT = Path(__file__).parents[1]
_CONFIG = (
    _ROOT / "experiments" / "configs" / "h32-acceptance-semantics-replay-v1.json"
)
_SOURCES = {
    "adr0099": (
        _ROOT / "experiments" / "results" / "h32-warm-search-acceptance-v1.json"
    ),
    "adr0101": (
        _ROOT / "experiments" / "results" / "h32-warm-candidate-stream-v1.json"
    ),
    "adr0103": (
        _ROOT / "experiments" / "results" / "h32-current-interpolation-audit-v1.json"
    ),
}


def _policy(
    candidate_id: str,
    digest_character: str,
    nash_conv: float,
    gains: list[float],
) -> dict[str, object]:
    return {
        "candidate_id": candidate_id,
        "aliases": [candidate_id],
        "source_refs": [f"synthetic:{candidate_id}"],
        "quality": {
            "policy_sha256": digest_character * 64,
            "nash_conv": nash_conv,
            "normalized_nash_conv": nash_conv,
            "deviation_gains": gains,
        },
    }


class H32AcceptanceSemanticsReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(_CONFIG.read_text(encoding="utf-8"))

    def test_frozen_protocol_has_mechanism_gates_only(self) -> None:
        parsed = parse_h32_acceptance_semantics_config(self.config)
        self.assertEqual(parsed["seeded_permutation_count"], 64)
        self.assertEqual(parsed["gates"]["expected_new_strategy_evaluations"], 0)
        self.assertEqual(
            parsed["fixed_envelope_contract"]["cap_anchor"],
            "blueprint_deviation_gain_plus_raw_guard_per_seat",
        )
        forbidden = {
            "minimum_strategy_improvement",
            "required_winning_candidate",
            "require_fixed_envelope_beats_legacy",
            "minimum_headroom_capture",
        }
        self.assertTrue(forbidden.isdisjoint(parsed["gates"]))

    def test_sources_contract_and_gates_are_immutable(self) -> None:
        mutations = []
        for key, value in (
            ("evidence_stage", "prospective_strategy_audit"),
            ("seed", 7),
            ("source_order", ["adr0103"]),
            ("acceptance_guard_normalized", 1e-8),
            ("seeded_permutation_count", 128),
        ):
            mutation = deepcopy(self.config)
            mutation[key] = value
            mutations.append(mutation)
        source = deepcopy(self.config)
        source["expected_source_sha256"]["adr0103"] = "0" * 64
        mutations.append(source)
        contract = deepcopy(self.config)
        contract["fixed_envelope_contract"]["coalition_safety"] = True
        mutations.append(contract)
        gate = deepcopy(self.config)
        gate["gates"]["expected_union_candidates_per_target"] = 12
        mutations.append(gate)
        extra = deepcopy(self.config)
        extra["quality_selector"] = "observed_best"
        mutations.append(extra)
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                with self.assertRaises(ValueError):
                    parse_h32_acceptance_semantics_config(mutation)

    def test_source_hashes_are_pinned_without_reading_strategy_labels(self) -> None:
        for source_id, path in _SOURCES.items():
            with self.subTest(source_id=source_id):
                self.assertEqual(
                    _sha256(path),
                    self.config["expected_source_sha256"][source_id],
                )

    def test_blueprint_abstains_below_guard_even_when_digest_loses(self) -> None:
        guard = 1e-3
        blueprint = _policy("blueprint_average64", "f", 1.0, [0.1] * 6)
        near = _policy("near", "0", 1.0 - 0.5 * guard, [0.09] * 6)
        result = select_fixed_blueprint_envelope(
            blueprint,
            [near],
            raw_guard=guard,
        )
        self.assertEqual(result["selected_candidate_id"], "blueprint_average64")
        self.assertTrue(result["blueprint_abstention"])

    def test_fixed_envelope_rejects_cap_breach_and_is_order_independent(self) -> None:
        guard = 1e-3
        blueprint = _policy("blueprint_average64", "f", 1.0, [0.1] * 6)
        best = _policy("best", "e", 0.5, [0.08] * 6)
        tied = _policy("digest_winner", "0", 0.5 + 0.5 * guard, [0.08] * 6)
        violating_gains = [0.08] * 6
        violating_gains[2] = 0.1 + 2.0 * guard
        violating = _policy("violating", "1", 0.1, violating_gains)
        forward = replay_fixed_blueprint_stream(
            blueprint,
            [best, tied, violating],
            raw_guard=guard,
        )
        reverse = replay_fixed_blueprint_stream(
            blueprint,
            [violating, tied, best],
            raw_guard=guard,
        )
        self.assertEqual(forward["selected_candidate_id"], "digest_winner")
        self.assertEqual(reverse["selected_policy_sha256"], "0" * 64)
        self.assertEqual(forward["selected_policy_sha256"], reverse["selected_policy_sha256"])
        self.assertEqual(forward["infeasible_candidate_count"], 1)
        self.assertEqual(reverse["selected_violating_seats"], [])

    def test_legacy_coordinate_monotonicity_is_path_dependent(self) -> None:
        blueprint = _policy("blueprint_average64", "f", 1.0, [0.2, 0.2])
        margin_builder = _policy("margin_builder", "a", 0.8, [0.1, 0.19])
        slack_spender = _policy("slack_spender", "b", 0.7, [0.15, 0.1])
        forward = replay_incumbent_relative_pareto(
            blueprint,
            [margin_builder, slack_spender],
            raw_guard=1e-9,
        )
        reverse = replay_incumbent_relative_pareto(
            blueprint,
            [slack_spender, margin_builder],
            raw_guard=1e-9,
        )
        self.assertEqual(forward["final_candidate_id"], "margin_builder")
        self.assertEqual(reverse["final_candidate_id"], "slack_spender")

    def test_duplicate_policy_merge_requires_quality_identity(self) -> None:
        first = _policy("first", "a", 0.5, [0.1, 0.2])
        second = _policy("second", "a", 0.5, [0.1, 0.2])
        merged, diagnostics = merge_policy_candidates(
            [first, second],
            maximum_quality_error=1e-15,
        )
        self.assertEqual(len(merged), 1)
        self.assertEqual(diagnostics["duplicate_rows"], 1)
        self.assertEqual(merged[0]["aliases"], ["first", "second"])
        mismatched = deepcopy(second)
        mismatched["quality"]["nash_conv"] = 0.6
        with self.assertRaises(ValueError):
            merge_policy_candidates(
                [first, mismatched],
                maximum_quality_error=1e-15,
            )


if __name__ == "__main__":
    unittest.main()
