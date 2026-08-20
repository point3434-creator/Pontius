from __future__ import annotations

import json
import unittest
from pathlib import Path

from pontius.factorized_belief_audit import (
    _all_hands_supported,
    _apply_updates,
    _distribution_error,
    _explicit_distribution,
    _materialized_dict,
    generate_hand_axes,
    make_factorized_case,
    parse_factorized_belief_audit_config,
)
from pontius.river import parse_cards

_ROOT = Path(__file__).parents[1]
_CONFIG = (
    _ROOT / "experiments" / "configs" / "factorized-card-belief-audit-v1.json"
)


def config() -> dict[str, object]:
    return json.loads(_CONFIG.read_text(encoding="utf-8"))


class FactorizedBeliefAuditTests(unittest.TestCase):
    def test_frozen_config_parses_exactly(self) -> None:
        parsed = parse_factorized_belief_audit_config(config())
        self.assertEqual(parsed["player_counts"], (2, 3, 4, 5, 6))
        self.assertEqual(parsed["wide_hands_per_player"], (16, 24, 32))
        self.assertEqual(parsed["range_families"], ("balanced", "blocker_heavy"))

    def test_axes_are_deterministic_supported_and_family_distinct(self) -> None:
        board = parse_cards("2c", "7d", "9h", "Js", "Qc")
        balanced = generate_hand_axes(
            board=board,
            players=6,
            hands_per_player=8,
            family="balanced",
            seed=17,
        )
        blocker = generate_hand_axes(
            board=board,
            players=6,
            hands_per_player=8,
            family="blocker_heavy",
            seed=17,
        )
        self.assertEqual(
            balanced,
            generate_hand_axes(
                board=board,
                players=6,
                hands_per_player=8,
                family="balanced",
                seed=17,
            ),
        )
        self.assertNotEqual(balanced, blocker)
        self.assertTrue(_all_hands_supported(balanced))
        self.assertTrue(_all_hands_supported(blocker))

    def test_small_independent_oracle_and_updates_match(self) -> None:
        board = parse_cards("2c", "7d", "9h", "Js", "Qc")
        belief, mixture, unaries = make_factorized_case(
            board=board,
            players=3,
            hands_per_player=3,
            family="blocker_heavy",
            components=3,
            seed=91,
        )
        explicit = _explicit_distribution(
            belief.hands_by_player,
            mixture,
            unaries,
        )
        self.assertLessEqual(
            _distribution_error(_materialized_dict(belief.materialize()), explicit),
            1e-15,
        )
        updated, explicit_updated = _apply_updates(
            belief,
            explicit,
            seed=91,
            updates_per_player=2,
        )
        self.assertIsNotNone(explicit_updated)
        self.assertLessEqual(
            _distribution_error(
                _materialized_dict(updated.materialize()),
                explicit_updated or {},
            ),
            1e-15,
        )
        self.assertIs(
            type(
                _distribution_error(
                    _materialized_dict(updated.materialize()),
                    explicit_updated or {},
                )
            ),
            float,
        )

    def test_schema_stage_hash_and_timing_mutations_fail(self) -> None:
        unknown = config()
        unknown["tensor_rank"] = 4
        with self.assertRaisesRegex(ValueError, "fields differ"):
            parse_factorized_belief_audit_config(unknown)

        hidden = config()
        hidden["evidence_stage"] = "preregistered_validation"
        with self.assertRaisesRegex(ValueError, "revealed engineering"):
            parse_factorized_belief_audit_config(hidden)

        changed_hash = config()
        changed_hash["expected_river_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "source hash mismatch"):
            parse_factorized_belief_audit_config(changed_hash)

        changed_timing = config()
        changed_timing["timing_repeats"] = 1
        with self.assertRaisesRegex(ValueError, "execution contract"):
            parse_factorized_belief_audit_config(changed_timing)


if __name__ == "__main__":
    unittest.main()
