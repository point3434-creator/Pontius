from __future__ import annotations

import json
import unittest
from pathlib import Path

from pontius.dependency_tape import CompiledPolicyDeltaTape
from pontius.public_tree_quotient_audit import (
    _build_disjoint_game,
    _hashed_policy,
    _ordinary_schema,
    parse_public_tree_quotient_config,
)

_ROOT = Path(__file__).parents[1]
_CONFIG = (
    _ROOT
    / "experiments"
    / "configs"
    / "multiway-public-tree-quotient-audit-v1.json"
)


def config() -> dict[str, object]:
    return json.loads(_CONFIG.read_text(encoding="utf-8"))


class PublicTreeQuotientAuditTests(unittest.TestCase):
    def test_frozen_config_parses_and_disjoint_count_is_cubic(self) -> None:
        parsed = parse_public_tree_quotient_config(config())
        game = _build_disjoint_game(parsed, 3)
        self.assertEqual(len(game.deals), 27)
        self.assertEqual(parsed["stress_families"], (
            "balanced",
            "polarized",
            "blocker_stress",
            "correlated",
        ))

    def test_hash_policies_are_deterministic_positive_or_pure(self) -> None:
        parsed = parse_public_tree_quotient_config(config())
        game = _build_disjoint_game(parsed, 2)
        schema = _ordinary_schema(game)
        dense = _hashed_policy(schema, seed=parsed["seed"], pure=False)
        pure = _hashed_policy(schema, seed=parsed["seed"], pure=True)
        self.assertEqual(
            dense,
            _hashed_policy(schema, seed=parsed["seed"], pure=False),
        )
        for key, actions in schema.items():
            self.assertTrue(all(dense[key][action] > 0.0 for action in actions))
            self.assertAlmostEqual(sum(dense[key].values()), 1.0)
            self.assertEqual(sum(pure[key].values()), 1.0)
            self.assertEqual(sum(value == 0.0 for value in pure[key].values()), 1)
        CompiledPolicyDeltaTape(game, {}).recertify_policy(dense, mode="dense")

    def test_unknown_fields_stage_changes_and_source_changes_fail(self) -> None:
        unknown = config()
        unknown["approximation_rank"] = 2
        with self.assertRaisesRegex(ValueError, "fields differ"):
            parse_public_tree_quotient_config(unknown)

        hidden = config()
        hidden["evidence_stage"] = "preregistered_validation"
        with self.assertRaisesRegex(ValueError, "revealed engineering"):
            parse_public_tree_quotient_config(hidden)

        changed = config()
        changed["expected_evaluation_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "source hash mismatch"):
            parse_public_tree_quotient_config(changed)


if __name__ == "__main__":
    unittest.main()
