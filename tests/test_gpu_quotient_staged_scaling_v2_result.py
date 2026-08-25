from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import unittest

from pontius.gpu_quotient_staged_scaling import STAGE_CARDS
from pontius.gpu_quotient_staged_scaling_v2_result import (
    rebind_staged_scaling_v2_file,
)


_ROOT = Path(__file__).parents[1]
_RESULT = _ROOT / "artifacts/gpu_occupied_card_quotient_staged_scaling_v2.jsonl"
_RESULT_BYTES = 65_114
_RESULT_SHA256 = "dd5b6d04cd45db0c3a95acdd1bcd05355c72be0852701df347696442261a2b72"
_CONFIG_SHA256 = "569083e612dd20139aead4452c01b9bf4fb01f615063da7b6924d35ac9a85838"
_SOURCE_COMMIT = "e7a4975c1a26704e2d0625f599dabf6d70f4b77b"
_CAMPAIGN_SHA256 = "eee4dff5f95ddfebb9db037d8876028178cd1cc757dfc1487b5fe9de486cbf5f"
_CLAIMS = {
    "literal_45_card_result": None,
    "action_clock_result": None,
    "decision_quality_result": None,
    "truncation_authorized": False,
    "poker_strength_result": None,
}


class GpuQuotientStagedScalingV2ResultTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.raw = _RESULT.read_bytes()
        cls.result = rebind_staged_scaling_v2_file(
            _RESULT,
            expected_config_sha256=_CONFIG_SHA256,
            expected_source_commit=_SOURCE_COMMIT,
        )

    def test_retained_bytes_campaign_and_terminal_are_exact(self) -> None:
        self.assertEqual(len(self.raw), _RESULT_BYTES)
        self.assertEqual(sha256(self.raw).hexdigest(), _RESULT_SHA256)
        self.assertEqual(self.result.journal_byte_count, _RESULT_BYTES)
        self.assertEqual(self.result.journal_sha256, _RESULT_SHA256)
        self.assertEqual(self.result.campaign_sha256, _CAMPAIGN_SHA256)
        self.assertEqual(self.result.source_commit, _SOURCE_COMMIT)
        self.assertEqual(self.result.terminal, "completed_pass")
        self.assertTrue(self.result.passed)
        self.assertEqual(self.result.completed_stage_cards, STAGE_CARDS)
        self.assertIsNone(self.result.failed_stage_cards)
        self.assertEqual(
            self.result.campaign_wall_ms.hex(),
            "0x1.48e769c0eb5e0p+16",
        )

    def test_every_stage_gate_allocation_and_claim_boundary_passes(self) -> None:
        expected_peaks = (
            71_499_680,
            117_915_320,
            364_705_168,
            1_265_911_592,
            3_842_056_832,
            10_046_423_704,
        )
        self.assertEqual(len(self.result.stage_payloads), len(STAGE_CARDS))
        for cards, peak, stage in zip(
            STAGE_CARDS,
            expected_peaks,
            self.result.stage_payloads,
            strict=True,
        ):
            with self.subTest(cards=cards):
                self.assertEqual(stage["available_cards"], cards)
                self.assertIs(stage["passed"], True)
                self.assertIsNone(stage["rejection_reason"])
                self.assertEqual(len(stage["gates"]), 21)
                self.assertTrue(all(value is True for value in stage["gates"].values()))
                self.assertEqual(
                    stage["allocation"]["requested_device_peak_bytes"],
                    peak,
                )
                self.assertIs(stage["allocation"]["fixed_cap_pass"], True)
                self.assertIs(stage["allocation"]["physical_reserve_pass"], True)
                self.assertIs(stage["allocation"]["live_reserve_pass"], True)
                self.assertEqual(stage["allocation"]["pool_used_bytes_after_release"], 0)
                self.assertEqual(stage["allocation"]["pool_total_bytes_after_release"], 0)
                self.assertEqual(stage["claims"], _CLAIMS)

    def test_exact_stage_and_phase_walls_are_retained_without_unit_promotion(self) -> None:
        expected = (
            (
                "0x1.c49a54605e000p+9",
                "0x1.8d9f908000000p-1",
                "0x1.410f94a000000p-2",
                "0x1.7de93a0000000p-2",
                "0x1.b0ccbc0000000p-4",
                "0x1.7acc4f0000000p-3",
                "0x1.323bbc0000000p-1",
            ),
            (
                "0x1.21e71758cc000p+8",
                "0x1.5171e2c000000p+0",
                "0x1.2133c25000000p+0",
                "0x1.36ed677000000p+0",
                "0x1.ac929b8000000p-2",
                "0x1.690ff92000000p+0",
                "0x1.93a6040000000p+5",
            ),
            (
                "0x1.d0d00346c8000p+9",
                "0x1.c83ec93000000p+2",
                "0x1.b221854000000p+2",
                "0x1.acb4af6800000p+2",
                "0x1.8edc3c6000000p+0",
                "0x1.ffb7e8e600000p+3",
                "0x1.3205c40000000p+9",
            ),
            (
                "0x1.0fb173eab3e00p+12",
                "0x1.16d1281800000p+5",
                "0x1.03e9206800000p+5",
                "0x1.01bc232c00000p+5",
                "0x1.6f294de000000p+2",
                "0x1.6b34043d00000p+6",
                "0x1.b6a2560000000p+11",
            ),
            (
                "0x1.195232b021580p+14",
                "0x1.cf12658800000p+6",
                "0x1.b1b4cb9800000p+6",
                "0x1.b5a2499800000p+6",
                "0x1.ee746d4000000p+3",
                "0x1.76bea92880000p+8",
                "0x1.d9ba600000000p+13",
            ),
            (
                "0x1.d21b36e2eabc0p+15",
                "0x1.693375d800000p+8",
                "0x1.479f31d000000p+8",
                "0x1.2831316800000p+8",
                "0x1.028d328000000p+5",
                "0x1.fbbaa7f780000p+9",
                "0x1.832a7a0000000p+15",
            ),
        )
        observed = []
        for stage in self.result.stage_payloads:
            timings = stage["timings"]
            observed.append(
                (
                    timings["host_hex"]["stage_total"],
                    timings["cold"]["phases"]["device_sum"]["median_hex"],
                    timings["warm"]["phases"]["device_sum"]["median_hex"],
                    timings["source_refresh"]["phases"]["device_sum"]["median_hex"],
                    timings["query_only"]["phases"]["device_sum"]["median_hex"],
                    timings["adjoint"]["phases"]["device_sum"]["median_hex"],
                    timings["direct_query"]["phases"]["direct_scan"]["median_hex"],
                )
            )
        self.assertEqual(tuple(observed), expected)

    def test_numerical_maxima_are_rebound_from_raw_stage_errors(self) -> None:
        maxima = {
            field: max(
                float.fromhex(stage["errors_hex"][field])
                for stage in self.result.stage_payloads
            )
            for field in self.result.stage_payloads[0]["errors_hex"]
        }
        self.assertEqual(maxima["source_sample_absolute"].hex(), "0x1.4000000000000p-61")
        self.assertEqual(maxima["source_sample_relative"].hex(), "0x1.4000000000000p-61")
        self.assertEqual(maxima["direct_query_absolute"].hex(), "0x1.fa00000000000p-35")
        self.assertEqual(maxima["direct_query_relative"].hex(), "0x1.3c183816ab44fp-44")
        self.assertEqual(maxima["affine_sample_absolute"].hex(), "0x1.0000000000000p-57")
        self.assertEqual(maxima["dot_product_absolute"].hex(), "0x1.4000000000000p-31")
        self.assertEqual(maxima["dot_product_relative"].hex(), "0x1.399fd39d2e13bp-49")


if __name__ == "__main__":
    unittest.main()
