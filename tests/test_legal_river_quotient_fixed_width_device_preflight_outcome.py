from __future__ import annotations

from dataclasses import asdict
from hashlib import sha256
import base64
import json
from pathlib import Path
import subprocess
import unittest

from pontius.legal_river_quotient_fixed_width_device_preflight_result import (
    RESULT_PATH,
    assess_device_preflight_bytes,
)


ROOT = Path(__file__).parents[1]
RESULT_SHA256 = "9b1ff216879c5e67090d8794242da74ba8bd52aac6753865c3bc822483550c69"
SOURCE_COMMIT = "e70f300ccd3aa406d6c6a4493f6a4067222bf9e5"


def retained_records() -> list[dict[str, object]]:
    return [json.loads(line) for line in RESULT_PATH.read_bytes().splitlines()]


class FixedWidthDevicePreflightOutcomeTests(unittest.TestCase):
    def test_retained_identity_and_independent_assessment(self) -> None:
        raw = RESULT_PATH.read_bytes()
        self.assertEqual(len(raw), 13_735)
        self.assertEqual(sha256(raw).hexdigest(), RESULT_SHA256)
        self.assertEqual(
            asdict(assess_device_preflight_bytes(raw)),
            {
                "terminal": "compiler_rejection",
                "passed": False,
                "source_commit": SOURCE_COMMIT,
                "event_count": 5,
                "eligible_arms": (),
                "candidate_selected": None,
                "laboratory_elapsed_ns": None,
                "public_elapsed_ns": 820_045_300,
            },
        )

    def test_compile_evidence_names_the_missing_host_compiler(self) -> None:
        records = retained_records()
        observations = {
            record["body"]["payload"]["kind"]: record["body"]["payload"]["event"]
            for record in records
            if record["body"]["kind"] == "observation"
        }
        compile_command = observations["compile"]["command"]
        self.assertEqual(compile_command["return_code"], 1)
        self.assertEqual(compile_command["elapsed_ns"], 10_231_300)
        self.assertEqual(compile_command["stderr_bytes"], 0)
        self.assertEqual(
            base64.b64decode(compile_command["stdout_base64"]),
            b"nvcc fatal   : Cannot find compiler 'cl.exe' in PATH\r\n",
        )
        self.assertEqual(
            observations["terminal_evidence"],
            {
                "schema_version": "legal-river-quotient-fixed-width-device-preflight-v1",
                "terminal": "compiler_rejection",
                "passed": False,
                "reason": "nvcc did not produce a cubin",
                "candidate_selected": None,
                "claims": {
                    "device_preflight_result": None,
                    "candidate_selected": None,
                    "population_25_numeric_value": None,
                    "actual_45_card_value": None,
                    "resolver_iteration_result": None,
                    "solve_result": None,
                    "action_result": None,
                    "action_clock_result": None,
                    "decision_quality_result": None,
                    "truncation_authorized": False,
                    "blueprint_result": None,
                    "poker_strength_result": None,
                },
            },
        )

    def test_retained_jsonl_path_is_not_text_filtered(self) -> None:
        relative = RESULT_PATH.relative_to(ROOT).as_posix()
        completed = subprocess.run(
            ["git", "check-attr", "text", "--", relative],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.stdout.strip(), f"{relative}: text: unset")


if __name__ == "__main__":
    unittest.main()
