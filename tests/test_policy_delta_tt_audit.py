from __future__ import annotations

import json
from pathlib import Path
import unittest

from pontius.policy_delta_tt_audit import parse_policy_delta_tt_config

_ROOT = Path(__file__).parents[1]
_CONFIG = (
    _ROOT
    / "experiments"
    / "configs"
    / "policy-delta-tt-recomposition-audit-v1.json"
)


def config() -> dict[str, object]:
    return json.loads(_CONFIG.read_text(encoding="utf-8"))


class PolicyDeltaTTAuditTests(unittest.TestCase):
    def test_frozen_config_parses_exactly(self) -> None:
        parsed = parse_policy_delta_tt_config(config())
        self.assertEqual(parsed["hands_per_player"], (4, 7))
        self.assertEqual(parsed["target_players"], (0, 1, 2, 3, 4, 5))
        self.assertEqual(parsed["maximum_rank"], None)
        self.assertEqual(parsed["amortized_reuse_counts"], (1, 2, 4, 8, 16))

    def test_hash_mutation_rule_and_gate_changes_fail(self) -> None:
        unknown = config()
        unknown["elimination_orders"] = []
        with self.assertRaisesRegex(ValueError, "fields differ"):
            parse_policy_delta_tt_config(unknown)

        changed_hash = config()
        changed_hash["expected_public_policy_tt_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "source hash mismatch"):
            parse_policy_delta_tt_config(changed_hash)

        changed_mutations = config()
        changed_mutations["candidate_mutations"] = ["single_hand_root_swap"]
        with self.assertRaisesRegex(ValueError, "candidate_mutations"):
            parse_policy_delta_tt_config(changed_mutations)

        changed_authority = config()
        changed_authority["capped_product_authority"] = "acceptance"
        with self.assertRaisesRegex(ValueError, "execution contract"):
            parse_policy_delta_tt_config(changed_authority)

        relaxed = config()
        relaxed["gates"]["maximum_positive_bound_violation"] = 1e-8
        with self.assertRaisesRegex(ValueError, "differs from ADR-0069"):
            parse_policy_delta_tt_config(relaxed)


if __name__ == "__main__":
    unittest.main()
