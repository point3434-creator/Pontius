from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from pontius.h32_current_decision_combined_ledger_replay import (
    build_current_decision_combined_ledger_rows,
    parse_h32_current_decision_combined_ledger_replay_config,
)


ROOT = Path(__file__).parents[1]
CONFIG = (
    ROOT / "experiments/configs/h32-current-decision-combined-ledger-replay-v1.json"
)
CLOSURE = ROOT / "experiments/results/h32-retained-convex-closure-census-v2.json"
SHADOW = ROOT / "experiments/results/h32-decision-aligned-live-shadow-v1.json"


def _payload(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _ledger_fields() -> dict:
    return {
        "street_budget_ms": 15000.0,
        "frozen_conservative_base_ms": 13967.615699994712,
        "incremental_endpoint_oracle_ceiling_ms": 1000.0,
        "incremental_endpoint_oracle_conservative_charge_ms": 1000.0,
        "maximum_numerical_identity_error": 2e-11,
    }


class H32CurrentDecisionCombinedLedgerReplayTests(unittest.TestCase):
    def test_config_freezes_a_zero_label_six_target_join(self) -> None:
        parsed = parse_h32_current_decision_combined_ledger_replay_config(
            _payload(CONFIG)
        )
        self.assertEqual(parsed["street_budget_ms"], 15000.0)
        self.assertEqual(parsed["frozen_conservative_base_ms"], 13967.615699994712)
        self.assertEqual(parsed["incremental_endpoint_oracle_ceiling_ms"], 1000.0)
        self.assertEqual(parsed["gates"]["expected_targets"], 6)
        self.assertEqual(parsed["gates"]["expected_round_zero_targets"], 4)
        self.assertEqual(parsed["gates"]["expected_round_one_targets"], 2)
        self.assertIn("zero_gpu_work", parsed["label_policy"])
        self.assertIn("post_fold_labels_zero", parsed["label_policy"])

    def test_sealed_rows_pair_and_the_frozen_ledgers_fit(self) -> None:
        rows, pairing = build_current_decision_combined_ledger_rows(
            _payload(CLOSURE),
            _payload(SHADOW),
            _ledger_fields(),
        )
        self.assertTrue(all(pairing.values()))
        self.assertEqual(len(rows), 6)
        self.assertEqual([row["cut_rounds"] for row in rows], [1, 0, 0, 1, 0, 0])
        self.assertTrue(all(all(row["identity"].values()) for row in rows))
        self.assertEqual(
            [row["combined_exact_oracles"] for row in rows],
            [3, 2, 2, 3, 2, 2],
        )
        self.assertEqual(
            [row["sealed_endpoint_independently_certified"] for row in rows],
            [False, True, True, False, True, True],
        )
        self.assertTrue(
            all(
                row["safe_retreat_certificate"]["independently_certified"]
                and row["safe_retreat_certificate"]["cap_feasible"]
                and row["safe_retreat_certificate"]["interior_slack_passed"]
                and row["safe_retreat_certificate"]["shadow_accepted"]
                and row["safe_retreat_certificate"]["exact_positive_value"] > 0.0
                for row in rows
            )
        )
        self.assertLess(
            max(row["incremental_endpoint_oracle_ms"] for row in rows),
            1000.0,
        )
        self.assertLess(
            max(row["measured_combined_ledger_ms"] for row in rows),
            6000.0,
        )
        self.assertAlmostEqual(
            min(row["conservative_combined_headroom_ms"] for row in rows),
            32.3843000052875,
        )
        self.assertTrue(all(row["measured_fits"] for row in rows))
        self.assertTrue(all(row["conservative_fits"] for row in rows))

    def test_numerical_identity_mutation_fails_closed(self) -> None:
        closure = _payload(CLOSURE)
        post_call = next(row for row in closure["target_rows"] if row["panel"] == "post_call")
        post_call["iterations"][0]["oracle"]["objective"] += 4e-11
        rows, _ = build_current_decision_combined_ledger_rows(
            closure,
            _payload(SHADOW),
            _ledger_fields(),
        )
        self.assertFalse(rows[0]["identity"]["numerical"])

    def test_manifest_reordering_fails_exact_pairing(self) -> None:
        shadow = deepcopy(_payload(SHADOW))
        shadow["target_rows"].reverse()
        _, pairing = build_current_decision_combined_ledger_rows(
            _payload(CLOSURE),
            shadow,
            _ledger_fields(),
        )
        self.assertTrue(pairing["exact_target_set"])
        self.assertFalse(pairing["manifest_order"])

    def test_incremental_oracle_ceiling_has_a_negative_control(self) -> None:
        fields = _ledger_fields()
        fields["incremental_endpoint_oracle_ceiling_ms"] = 700.0
        rows, _ = build_current_decision_combined_ledger_rows(
            _payload(CLOSURE),
            _payload(SHADOW),
            fields,
        )
        round_one = [row for row in rows if row["cut_rounds"] == 1]
        round_zero = [row for row in rows if row["cut_rounds"] == 0]
        self.assertTrue(
            all(
                not row["incremental_endpoint_oracle_within_ceiling"]
                for row in round_one
            )
        )
        self.assertTrue(
            all(row["incremental_endpoint_oracle_within_ceiling"] for row in round_zero)
        )


if __name__ == "__main__":
    unittest.main()
