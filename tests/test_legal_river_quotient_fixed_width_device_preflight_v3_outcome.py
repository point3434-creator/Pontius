from __future__ import annotations

from dataclasses import asdict
from hashlib import sha256
from pathlib import Path
import subprocess
import unittest

from pontius.legal_river_quotient_fixed_width_device_preflight_v3_outcome import (
    RESULT_BYTES,
    RESULT_PATH,
    RESULT_SHA256,
    assess_device_preflight_v3_outcome_bytes,
    assess_device_preflight_v3_outcome_file,
)
from pontius.legal_river_quotient_fixed_width_device_preflight_v3_result import (
    assess_device_preflight_v3_bytes,
)


ROOT = Path(__file__).parents[1]


class FixedWidthDevicePreflightV3OutcomeTests(unittest.TestCase):
    def test_exact_retained_completed_terminal_is_assessed(self) -> None:
        self.assertEqual(
            asdict(assess_device_preflight_v3_outcome_file()),
            {
                "terminal": "completed_device_preflight",
                "passed": True,
                "source_commit": "f271e6deeefe11f228d582c9734a166c0ba32b45",
                "record_count": 59,
                "event_count": 57,
                "eligible_arms": (
                    "positional",
                    "batched_five_then_four_RRNS",
                ),
                "ineligible_arms": ("resident_nine_RRNS",),
                "candidate_selected": None,
                "cubin_sha256": (
                    "cc19a8de2fc44bf576f41be365e797667cc4ec4d7afd842d7a14289c3188ac8d"
                ),
                "cubin_bytes": 634_144,
                "laboratory_elapsed_ns": 19_672_450_800,
                "outside_laboratory_elapsed_ns": 4_279_150_100,
                "public_elapsed_ns": 23_951_600_900,
            },
        )

    def test_retained_raw_identity_and_unfiltered_path(self) -> None:
        raw = RESULT_PATH.read_bytes()
        self.assertEqual(len(raw), RESULT_BYTES)
        self.assertEqual(sha256(raw).hexdigest(), RESULT_SHA256)
        relative = RESULT_PATH.relative_to(ROOT).as_posix()
        completed = subprocess.run(
            ["git", "check-attr", "text", "--", relative],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.stdout.strip(), f"{relative}: text: unset")

    def test_source_sealed_reader_and_artifact_bound_assessor_agree(self) -> None:
        raw = RESULT_PATH.read_bytes()
        source = asdict(assess_device_preflight_v3_bytes(raw))
        outcome = asdict(assess_device_preflight_v3_outcome_bytes(raw))
        for key in (
            "terminal",
            "passed",
            "source_commit",
            "event_count",
            "eligible_arms",
            "candidate_selected",
            "laboratory_elapsed_ns",
            "public_elapsed_ns",
        ):
            self.assertEqual(outcome[key], source[key])

    def test_any_raw_mutation_rejects(self) -> None:
        raw = RESULT_PATH.read_bytes()
        changed = bytearray(raw)
        changed[len(changed) // 2] ^= 1
        for mutated in (bytes(changed), raw[:-1], raw + b"{}\n"):
            with self.subTest(size=len(mutated)):
                with self.assertRaises(ValueError):
                    assess_device_preflight_v3_outcome_bytes(mutated)

    def test_claim_boundary_remains_closed(self) -> None:
        outcome = assess_device_preflight_v3_outcome_file()
        self.assertIsNone(outcome.candidate_selected)
        self.assertEqual(
            outcome.eligible_arms,
            ("positional", "batched_five_then_four_RRNS"),
        )
        self.assertEqual(outcome.ineligible_arms, ("resident_nine_RRNS",))


if __name__ == "__main__":
    unittest.main()
