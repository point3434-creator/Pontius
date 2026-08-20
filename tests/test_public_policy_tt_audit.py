from __future__ import annotations

import json
import unittest
from pathlib import Path

from pontius.public_policy_tt_audit import (
    _arm_names,
    _arm_rank,
    parse_public_policy_tt_config,
)

_ROOT = Path(__file__).parents[1]
_CONFIG = (
    _ROOT / "experiments" / "configs" / "public-policy-root-tt-audit-v1.json"
)


def config() -> dict[str, object]:
    return json.loads(_CONFIG.read_text(encoding="utf-8"))


class PublicPolicyTTAuditTests(unittest.TestCase):
    def test_frozen_config_and_arms_parse_exactly(self) -> None:
        parsed = parse_public_policy_tt_config(config())
        self.assertEqual(parsed["hands_per_player"], (4, 7))
        self.assertEqual(parsed["target_players"], (0, 3, 5))
        self.assertEqual(
            _arm_names(parsed),
            ("rank_8", "rank_16", "rank_32", "relative_tolerance_only"),
        )
        self.assertIsNone(_arm_rank("relative_tolerance_only"))
        self.assertEqual(_arm_rank("rank_16"), 16)

    def test_stage_hash_axis_rule_and_gate_mutations_fail(self) -> None:
        unknown = config()
        unknown["target_actions"] = True
        with self.assertRaisesRegex(ValueError, "fields differ"):
            parse_public_policy_tt_config(unknown)

        hidden = config()
        hidden["evidence_stage"] = "validation"
        with self.assertRaisesRegex(ValueError, "preregistered revealed"):
            parse_public_policy_tt_config(hidden)

        changed_hash = config()
        changed_hash["expected_factor_tt_contraction_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "source hash mismatch"):
            parse_public_policy_tt_config(changed_hash)

        changed_players = config()
        changed_players["target_players"] = [0, 1, 2, 3, 4, 5]
        with self.assertRaisesRegex(ValueError, "differs from ADR-0067"):
            parse_public_policy_tt_config(changed_players)

        changed_rule = config()
        changed_rule["branch_rule"] = "dense_reconstruct_each_node"
        with self.assertRaisesRegex(ValueError, "execution contract"):
            parse_public_policy_tt_config(changed_rule)

        relaxed = config()
        relaxed["gates"]["maximum_exact_root_tensor_error"] = 1e-3
        with self.assertRaisesRegex(ValueError, "differs from ADR-0067"):
            parse_public_policy_tt_config(relaxed)


if __name__ == "__main__":
    unittest.main()
