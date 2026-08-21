from __future__ import annotations

import json
from pathlib import Path
import unittest

from pontius.h32_fresh_public_block_value_audit import (
    block_union_keys,
    build_public_node_blocks,
    information_key_public_coordinates,
    parse_h32_fresh_public_block_value_config,
)


_ROOT = Path(__file__).parents[1]
_CONFIG = _ROOT / "experiments/configs/h32-fresh-public-block-value-v1.json"


def _key(seat: int, hand: str, history: str) -> str:
    return f"river|structure=frozen|p{seat}|hand={hand}|history={history}"


class H32FreshPublicBlockValueAuditTests(unittest.TestCase):
    def test_contract_rejects_target_block_parent_and_gate_mutations(self) -> None:
        config = json.loads(_CONFIG.read_text(encoding="utf-8"))
        parsed = parse_h32_fresh_public_block_value_config(config)
        self.assertEqual(parsed["local_blocker_target_seat"], 2)
        self.assertEqual(parsed["maximum_warm_start_probability_error"], 1e-12)

        mutated = json.loads(json.dumps(config))
        mutated["targets"][0]["target_belief_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "workload differs"):
            parse_h32_fresh_public_block_value_config(mutated)

        mutated = dict(config)
        mutated["block_membership"] = "outcome_tuned"
        with self.assertRaisesRegex(ValueError, "workload differs"):
            parse_h32_fresh_public_block_value_config(mutated)

        mutated = dict(config)
        mutated["expected_parent_result_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "source mismatch"):
            parse_h32_fresh_public_block_value_config(mutated)

        mutated = json.loads(json.dumps(config))
        mutated["gates"]["expected_post_ledger_block_labels"] = 6
        with self.assertRaisesRegex(ValueError, "gates differ"):
            parse_h32_fresh_public_block_value_config(mutated)

    def test_public_coordinates_require_unique_player_and_history(self) -> None:
        self.assertEqual(
            information_key_public_coordinates(_key(3, "AsAd", "p0:bet")),
            (3, "p0:bet"),
        )
        with self.assertRaisesRegex(ValueError, "unique player/history"):
            information_key_public_coordinates("river|p0|hand=AsAd")

    def test_blocks_expand_across_changed_hands_at_exact_public_node(self) -> None:
        blueprint = {}
        candidate = {}
        anchors = []
        for seat in range(6):
            history = f"seat-{seat}-history"
            for hand in ("2c2d", "3c3d"):
                key = _key(seat, hand, history)
                blueprint[key] = {"check": 0.5, "bet": 0.5}
                candidate[key] = {"check": 0.4, "bet": 0.6}
            off_history = _key(seat, "4c4d", f"other-{seat}")
            blueprint[off_history] = {"check": 0.5, "bet": 0.5}
            candidate[off_history] = {"check": 0.3, "bet": 0.7}
            anchors.append(
                {
                    "acting_seat": seat,
                    "information_key": _key(seat, "2c2d", history),
                }
            )
        blocks = build_public_node_blocks(blueprint, candidate, anchors)
        self.assertEqual([row["information_set_count"] for row in blocks], [2] * 6)
        self.assertEqual(len(block_union_keys(blocks, [0, 1, 2])), 6)
        self.assertTrue(
            all("other" not in key for key in block_union_keys(blocks, range(6)))
        )
        with self.assertRaisesRegex(ValueError, "cannot be resolved"):
            block_union_keys(blocks, [6])


if __name__ == "__main__":
    unittest.main()
