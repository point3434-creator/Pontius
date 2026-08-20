from __future__ import annotations

import json
from pathlib import Path
import unittest

import numpy as np

from pontius.structured_showdown_automaton import (
    build_structured_showdown_automaton,
)
from pontius.structured_showdown_automaton_audit import (
    _literal_assignment_payoffs,
    parse_structured_showdown_config,
)

_ROOT = Path(__file__).parents[1]
_CONFIG = (
    _ROOT
    / "experiments"
    / "configs"
    / "structured-showdown-automaton-audit-v1.json"
)


def config() -> dict[str, object]:
    return json.loads(_CONFIG.read_text(encoding="utf-8"))


class StructuredShowdownAutomatonAuditTests(unittest.TestCase):
    def test_frozen_config_parses_exactly(self) -> None:
        parsed = parse_structured_showdown_config(config())
        self.assertEqual(parsed["hands_per_player"], (4, 7, 32))
        self.assertEqual(parsed["dense_control_hands"], (4, 7))
        self.assertEqual(parsed["target_players"], (0, 1, 2, 3, 4, 5))
        self.assertEqual(
            parsed["axis_orders"],
            ("generated", "within_axis_strength_sorted"),
        )
        self.assertEqual(len(parsed["permutation_control_cases"]), 6)

    def test_sampled_literal_oracle_is_independent_and_exact(self) -> None:
        strengths = (
            np.asarray([0, 4, 2], dtype=np.int32),
            np.asarray([3, 1, 4], dtype=np.int32),
            np.asarray([4, 2, 0], dtype=np.int32),
        )
        assignments = np.asarray(
            [[0, 0, 0], [1, 2, 0], [2, 0, 1], [1, 1, 2]],
            dtype=np.int32,
        )
        literal = _literal_assignment_payoffs(
            strength_codes=strengths,
            assignments=assignments,
            contenders=(0, 2),
            contributed=True,
            pot=12.0,
            bet_size=3.0,
        )
        compiled = np.stack(
            [
                build_structured_showdown_automaton(
                    strength_codes=strengths,
                    contenders=(0, 2),
                    target_player=player,
                    contributed=True,
                    pot=12.0,
                    bet_size=3.0,
                ).evaluate_assignments(assignments)
                for player in range(3)
            ]
        )
        np.testing.assert_array_equal(compiled, literal)
        np.testing.assert_allclose(np.sum(literal, axis=0), 0.0, atol=1e-15)

    def test_stage_hash_case_rule_and_gate_changes_fail(self) -> None:
        unknown = config()
        unknown["read_path_speed_gate"] = True
        with self.assertRaisesRegex(ValueError, "fields differ"):
            parse_structured_showdown_config(unknown)

        hidden = config()
        hidden["evidence_stage"] = "validation"
        with self.assertRaisesRegex(ValueError, "preregistered revealed"):
            parse_structured_showdown_config(hidden)

        changed_hash = config()
        changed_hash["expected_rank_screen_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "source hash mismatch"):
            parse_structured_showdown_config(changed_hash)

        changed_orders = config()
        changed_orders["axis_orders"] = ["generated"]
        with self.assertRaisesRegex(ValueError, "axis_orders"):
            parse_structured_showdown_config(changed_orders)

        changed_cases = config()
        changed_cases["permutation_control_cases"][0]["player"] = 1
        with self.assertRaisesRegex(ValueError, "permutation controls"):
            parse_structured_showdown_config(changed_cases)

        changed_rule = config()
        changed_rule["dense_export_rule"] = "svd_from_dense"
        with self.assertRaisesRegex(ValueError, "execution contract"):
            parse_structured_showdown_config(changed_rule)

        relaxed = config()
        relaxed["gates"]["maximum_wide_all_automata_bytes"] = 1_000_000_000
        with self.assertRaisesRegex(ValueError, "differs from ADR-0071"):
            parse_structured_showdown_config(relaxed)


if __name__ == "__main__":
    unittest.main()
