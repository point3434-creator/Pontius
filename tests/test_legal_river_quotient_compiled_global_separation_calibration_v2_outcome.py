from __future__ import annotations

from dataclasses import asdict
from hashlib import sha256
from pathlib import Path
import subprocess
import unittest

from pontius.legal_river_quotient_compiled_global_separation_calibration_v2_outcome import (
    RESULT_BYTES,
    RESULT_PATH,
    RESULT_SHA256,
    assess_compiled_calibration_v2_outcome_bytes,
    assess_compiled_calibration_v2_outcome_file,
)
from pontius.legal_river_quotient_compiled_global_separation_calibration_v2_result import (
    assess_calibration_bytes,
)


ROOT = Path(__file__).parents[1]
PARENT_SOURCE = (
    ROOT
    / "src/pontius/legal_river_quotient_compiled_global_separation_calibration.py"
)


class CompiledGlobalSeparationCalibrationV2OutcomeTests(unittest.TestCase):
    def test_exact_retained_rejection_is_assessed(self) -> None:
        self.assertEqual(
            asdict(assess_compiled_calibration_v2_outcome_file()),
            {
                "terminal": "compiled_reduced_calibration_rejected",
                "passed": False,
                "source_commit": "08bb6857f47f9669b8f531c65079d4decd52a573",
                "record_count": 23,
                "event_count": 21,
                "scientific_call_count": 1,
                "measured_call_count": 0,
                "public_elapsed_ns": 173_015_658_900,
                "cubin_sha256": (
                    "2ee4c01232a68ae7608c3f6d1976335621dee61453f7f3b8f432fcde19c10f5b"
                ),
                "cubin_bytes": 582_880,
                "device_name": "NVIDIA GeForce RTX 5080",
                "compute_capability": "120",
                "device_total_bytes": 17_094_475_776,
                "reduced_campaign_peak_bytes": 194_402_210,
                "completed_cell_key": (
                    "10|contract_first_direct_57_scan|positive_witness|"
                    "opaque_per_source_base|exact_provenance_hit|positional"
                ),
                "completed_cell_primitive_ns": 2_126_968_200,
                "failing_kernel": "direct_prices_rrns_batch",
                "failure_code": "CUDA_ERROR_INVALID_VALUE",
                "candidate_selected": None,
                "topology_selected": None,
                "arithmetic_schedule_selected": None,
            },
        )

    def test_raw_identity_reader_agreement_and_unfiltered_path(self) -> None:
        raw = RESULT_PATH.read_bytes()
        self.assertEqual(len(raw), RESULT_BYTES)
        self.assertEqual(sha256(raw).hexdigest(), RESULT_SHA256)
        source = assess_calibration_bytes(raw)
        outcome = assess_compiled_calibration_v2_outcome_bytes(raw)
        self.assertEqual(outcome.terminal, source.terminal)
        self.assertEqual(outcome.source_commit, source.source_commit)
        self.assertEqual(outcome.event_count, source.event_count)
        relative = RESULT_PATH.relative_to(ROOT).as_posix()
        completed = subprocess.run(
            ["git", "check-attr", "text", "--", relative],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.stdout.strip(), f"{relative}: text: unset")

    def test_retained_source_exposes_the_launch_arity_defect(self) -> None:
        text = PARENT_SOURCE.read_text(encoding="utf-8")
        declaration = (
            "unsigned long long *prices, int cards, unsigned long long source_count,\n"
            "    const unsigned long long *moduli, const int *channels,\n"
            "    int channel_count, int *status)"
        )
        omitted = """\
                    "direct_prices_rrns_batch",
                    scan_count * channel_count,
                    (
                        h_decision,
                        base_decision,
                        scratch["rrns_batch_arena"],
                        np.int32(cell.cards),
                        prepared.moduli,"""
        complete = """\
                    "direct_prices_rrns_batch",
                    prepared.source_rows * channel_count,
                    (
                        scratch["h_positional"],
                        artifact["base"],
                        scratch["rrns_batch_arena"],
                        np.int32(cell.cards),
                        np.uint64(prepared.source_rows),
                        prepared.moduli,"""
        self.assertIn(declaration, text)
        self.assertEqual(text.count(omitted), 1)
        self.assertEqual(text.count(complete), 1)

    def test_any_raw_mutation_rejects(self) -> None:
        raw = RESULT_PATH.read_bytes()
        changed = bytearray(raw)
        changed[len(changed) // 2] ^= 1
        for mutated in (bytes(changed), raw[:-1], raw + b"{}\n"):
            with self.subTest(size=len(mutated)):
                with self.assertRaises(ValueError):
                    assess_compiled_calibration_v2_outcome_bytes(mutated)

    def test_claim_boundary_remains_closed(self) -> None:
        outcome = assess_compiled_calibration_v2_outcome_file()
        self.assertEqual(outcome.measured_call_count, 0)
        self.assertIsNone(outcome.candidate_selected)
        self.assertIsNone(outcome.topology_selected)
        self.assertIsNone(outcome.arithmetic_schedule_selected)


if __name__ == "__main__":
    unittest.main()
