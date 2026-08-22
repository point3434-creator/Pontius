from __future__ import annotations

import csv
import io
import json
from pathlib import Path
import unittest

from pontius import h32_resident_sparse_ncu_profile as profile


_ROOT = Path(__file__).parents[1]
_CONFIG = _ROOT / "experiments/configs/h32-resident-sparse-ncu-profile-v1.json"


def _kernel_row(
    *,
    duration: float = 100.0,
    sm: float = 20.0,
    dram: float = 20.0,
    l2: float = 20.0,
    l1: float = 20.0,
    occupancy: float = 80.0,
    waves: float = 2.0,
) -> dict[str, object]:
    return {
        "kernel_name": "synthetic_kernel",
        "metrics": {
            "gpu__time_duration.sum": duration,
            "sm__throughput.avg.pct_of_peak_sustained_elapsed": sm,
            "gpu__dram_throughput.avg.pct_of_peak_sustained_elapsed": dram,
            "lts__throughput.avg.pct_of_peak_sustained_elapsed": l2,
            "l1tex__throughput.avg.pct_of_peak_sustained_active": l1,
            "sm__warps_active.avg.pct_of_peak_sustained_active": occupancy,
            "launch__waves_per_multiprocessor": waves,
        },
    }


def _classify(row: dict[str, object]) -> str:
    return profile.classify_kernel_pressure(
        [row],
        dominant_fraction=0.90,
        pressure_threshold=60.0,
        pressure_ratio=1.25,
        low_throughput=50.0,
        low_occupancy=40.0,
        low_waves=1.0,
    )["classification"]


class H32ResidentSparseNcuProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(_CONFIG.read_text(encoding="utf-8"))

    def test_frozen_profile_scope(self) -> None:
        parsed = profile.parse_h32_resident_sparse_ncu_profile_config(self.config)
        self.assertEqual(
            parsed["representative_target"],
            "panel_2/balanced/local_blocker_seat2_x2",
        )
        self.assertEqual(parsed["directions"], ["right_to_left", "left_to_right"])
        self.assertEqual(parsed["feature_width"], 384)
        self.assertEqual(parsed["ncu_set"], "basic")
        self.assertEqual(parsed["ncu_replay_mode"], "kernel")

    def test_wide_raw_csv_parser_retains_nvtx_and_core_metrics(self) -> None:
        header = [
            "ID",
            "Process ID",
            "Process Name",
            "Host Name",
            "Kernel Name",
            "Context",
            "Stream",
            "Block Size",
            "Grid Size",
            "Device",
            "CC",
            "NVTX Push/Pop_Range",
            *profile._METRICS,
        ]
        units = ["", "", "", "", "", "", "", "", "", "", "", ""] + [
            "nsecond" if name == "gpu__time_duration.sum" else "%"
            for name in profile._METRICS
        ]
        data = [
            "1",
            "42",
            "python.exe",
            "host",
            "csr_spmm",
            "1",
            "7",
            "(128, 1, 1)",
            "(64, 1, 1)",
            "NVIDIA GeForce RTX 5080",
            "12.0",
            "PONTIUS_H32_SPARSE_RIGHT_TO_LEFT_W384",
            *[
                "1234" if name == "gpu__time_duration.sum" else "25.5"
                for name in profile._METRICS
            ],
        ]
        buffer = io.StringIO()
        writer = csv.writer(buffer, lineterminator="\n", quoting=csv.QUOTE_ALL)
        writer.writerow(header)
        writer.writerow(units)
        writer.writerow(data)
        parsed = profile.parse_ncu_raw_csv(buffer.getvalue())
        self.assertEqual(len(parsed["kernel_rows"]), 1)
        row = parsed["kernel_rows"][0]
        self.assertEqual(row["kernel_name"], "csr_spmm")
        self.assertIn("RIGHT_TO_LEFT", row["nvtx_push_pop_range"])
        self.assertEqual(row["metrics"]["gpu__time_duration.sum"], 1234.0)

    def test_frozen_classifier_has_all_four_outcomes(self) -> None:
        self.assertEqual(
            _classify(_kernel_row(sm=30.0, dram=80.0)),
            "memory_pressure",
        )
        self.assertEqual(
            _classify(_kernel_row(sm=80.0, dram=20.0, l2=20.0, l1=20.0)),
            "compute_pressure",
        )
        self.assertEqual(
            _classify(
                _kernel_row(
                    sm=20.0,
                    dram=20.0,
                    l2=20.0,
                    l1=20.0,
                    occupancy=20.0,
                    waves=0.5,
                )
            ),
            "launch_or_occupancy_pressure",
        )
        self.assertEqual(
            _classify(_kernel_row(sm=55.0, dram=55.0, l2=55.0, l1=55.0)),
            "mixed_or_unresolved",
        )

    def test_profile_source_is_nvtx_isolated_and_claim_limited(self) -> None:
        source = profile._IMPLEMENTATION.read_text(encoding="utf-8")
        workload = profile._WORKLOAD.read_text(encoding="utf-8")
        self.assertIn('f"{range_name}]"', source)
        self.assertIn('"--set"', source)
        self.assertEqual(self.config["ncu_set"], "basic")
        self.assertIn('"strategy_labels_loaded": 0', source)
        self.assertIn("operator.source_matrix @ features", workload)
        self.assertIn("operator.query_matrix @ incidence", workload)

    def test_workload_and_source_mutations_are_rejected(self) -> None:
        changed = json.loads(json.dumps(self.config))
        changed["feature_width"] = 385
        with self.assertRaisesRegex(ValueError, "workload differs"):
            profile.parse_h32_resident_sparse_ncu_profile_config(changed)

        changed = json.loads(json.dumps(self.config))
        changed["expected_workload_implementation_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "source mismatch"):
            profile.parse_h32_resident_sparse_ncu_profile_config(changed)


if __name__ == "__main__":
    unittest.main()
