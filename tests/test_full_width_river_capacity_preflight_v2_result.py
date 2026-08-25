from __future__ import annotations

import hashlib
import json
import unittest
from math import comb
from pathlib import Path

_ROOT = Path(__file__).parents[1]
_RESULT = (
    _ROOT / "experiments/results/full-width-river-capacity-preflight-v2.json"
)
_EXPECTED_BYTES = 11_602
_EXPECTED_SHA256 = "b486e3ac0269122fc3d578f9fc708ae9bd7472760c7b0603670464df1906b991"


class FullWidthRiverCapacityPreflightV2ResultTests(unittest.TestCase):
    def payload(self) -> dict[str, object]:
        raw = _RESULT.read_bytes()
        self.assertEqual(len(raw), _EXPECTED_BYTES)
        self.assertEqual(hashlib.sha256(raw).hexdigest(), _EXPECTED_SHA256)
        return json.loads(raw)

    def test_exact_first_terminal_is_clean_source_bound_and_passing(self) -> None:
        payload = self.payload()

        self.assertEqual(
            payload["source_commit"],
            "6fb001d58272856c35a437d49a7407c13ba77d48",
        )
        self.assertIs(payload["source_dirty"], False)
        self.assertEqual(
            payload["config_sha256"],
            "23cb6ea4521dc26c5fc1c3962574443b7a1d1b841f9e54c03355f9af9a58ff58",
        )
        self.assertEqual(
            payload["implementation_sha256"],
            "19f89f5124b703b01986c5478ddfbdd7a13c37e6dfc1550062963e51ba488821",
        )
        self.assertIs(payload["passed"], True)
        self.assertTrue(all(payload["gates"].values()))
        self.assertTrue(all(payload["target"]["gates"].values()))

    def test_standard_library_recomputes_the_allocation_lower_bound(self) -> None:
        allocation = self.payload()["target"]["allocation_lower_bound"]
        right_records = comb(45, 2) * comb(43, 2)
        left_records = right_records * comb(41, 2)
        axis_bytes = (1 + 5 * comb(45, 2)) * 8

        def half_bytes(records: int) -> int:
            return records * (8 + 3 * 4)

        def ids_bytes(records: int) -> int:
            return records * 64 * 4

        def signs_bytes(records: int) -> int:
            return records * 64

        base = (
            axis_bytes
            + half_bytes(left_records)
            + half_bytes(right_records)
            + ids_bytes(right_records)
            + ids_bytes(left_records)
            + signs_bytes(left_records)
        )
        reverse = (
            ids_bytes(left_records)
            + ids_bytes(right_records)
            + signs_bytes(right_records)
        )
        resident = (
            8
            + (left_records + right_records) * 8
            + (left_records * 3 + right_records * 3) * 4
        )
        alternative_base = (
            axis_bytes
            + half_bytes(right_records)
            + half_bytes(left_records)
            + ids_bytes(left_records)
            + ids_bytes(right_records)
            + signs_bytes(right_records)
        )

        self.assertEqual(allocation["left"]["records"], left_records)
        self.assertEqual(allocation["right"]["records"], right_records)
        self.assertEqual(allocation["base_topology_numeric_bytes"], base)
        self.assertEqual(allocation["reverse_topology_numeric_bytes"], reverse)
        self.assertEqual(
            allocation["bidirectional_topology_numeric_bytes"],
            base + reverse,
        )
        self.assertEqual(allocation["resident_belief_numeric_bytes"], resident)
        self.assertEqual(
            allocation["optimistic_scalar_topology_numeric_bytes"],
            min(base, alternative_base),
        )

    def test_every_frozen_resource_admission_conjunct_rejects(self) -> None:
        payload = self.payload()
        target = payload["target"]
        allocation = target["allocation_lower_bound"]
        caps = target["resource_caps"]
        runtime = payload["runtime_at_target_admission"]

        self.assertEqual(
            target["terminal"],
            "representation_rejected_before_target_allocation",
        )
        self.assertIs(target["capacity_admitted"], False)
        self.assertTrue(
            all(value is False for value in target["admission_checks"].values())
        )
        self.assertGreater(
            allocation["optimistic_scalar_topology_numeric_bytes"],
            caps["maximum_host_persistent_numeric_bytes"],
        )
        self.assertGreater(
            allocation["bidirectional_topology_numeric_bytes"]
            + caps["minimum_host_free_reserve_bytes"],
            runtime["host_available_physical_bytes"],
        )
        self.assertGreater(
            allocation["resident_belief_numeric_bytes"],
            caps["maximum_device_resident_numeric_bytes"],
        )
        self.assertGreater(
            allocation["resident_belief_numeric_bytes"]
            + caps["minimum_device_free_reserve_bytes"],
            runtime["device_free_bytes"],
        )
        for field in (
            "target_topology_builds",
            "target_scalar_contractions",
            "target_priming_contractions",
            "target_warm_contractions",
        ):
            self.assertEqual(target[field], 0)
        self.assertIsNone(target["workload"])

    def test_exact_street_widths_and_reduced_control_are_retained(self) -> None:
        payload = self.payload()
        rows = payload["target"]["street_inventory"]
        self.assertEqual(
            tuple(row["opponent_hand_counts"][0] for row in rows),
            (1225, 1081, 1035, 990),
        )
        self.assertTrue(
            all(
                row["opponent_hand_counts"]
                == [row["opponent_hand_counts"][0]] * 5
                for row in rows
            )
        )
        workload = payload["control"]["workload"]
        self.assertTrue(all(workload["allocation_model_matches"].values()))
        self.assertEqual(workload["prime_warm_maximum_repeat_error"], 0.0)
        self.assertEqual(workload["scalar_resident_expectation_error"], 0.0)
        self.assertLess(workload["warm_contraction_ms"], 14_000.0)

    def test_telemetry_claims_and_emissions_remain_bounded(self) -> None:
        payload = self.payload()
        telemetry = payload["typed_memory_telemetry_control"]

        self.assertIs(telemetry["passed"], True)
        self.assertTrue(all(telemetry["gates"].values()))
        self.assertEqual(
            telemetry["snapshot"]["process_counter_struct_bytes"],
            80,
        )
        self.assertEqual(
            payload["emissions"],
            {
                "actions": 0,
                "quality_claim": None,
                "strategy_labels": 0,
                "strategy_quality_rows": 0,
            },
        )
        self.assertIs(payload["claims"]["representation_result_only"], True)
        self.assertIs(payload["claims"]["certified_truncation_authorized"], False)
        self.assertIsNone(payload["claims"]["strategy_quality_prior"])
        attributes = (_ROOT / ".gitattributes").read_text(encoding="utf-8")
        self.assertIn(
            "/experiments/results/full-width-river-capacity-preflight-v2.json -text",
            attributes,
        )


if __name__ == "__main__":
    unittest.main()
