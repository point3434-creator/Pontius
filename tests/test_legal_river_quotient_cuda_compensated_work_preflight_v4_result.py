from __future__ import annotations

from collections import Counter, defaultdict
from hashlib import sha256
import json
from pathlib import Path
import unittest

from pontius.legal_river_quotient_cuda_compensated_work_preflight_v4_result import (
    rebind_work_preflight_v4_file,
)


_ROOT = Path(__file__).parents[1]
_ARTIFACT = (
    _ROOT
    / "artifacts/work_preflight/"
    "legal_river_quotient_cuda_compensated_work_preflight_v4.jsonl"
)
_RESERVED_ACTUAL = _ROOT / "artifacts/legal_river_quotient_cuda_consumer_v1.jsonl"


class RepairedExecutedCubinWorkPreflightV4ResultTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.raw = _ARTIFACT.read_bytes()
        cls.rebound = rebind_work_preflight_v4_file(_ARTIFACT)
        cls.rows = tuple(json.loads(line) for line in cls.raw.splitlines())
        cls.observations = tuple(
            row["body"]["payload"]
            for row in cls.rows
            if row["body"]["kind"] == "observation"
        )

    def test_retained_artifact_identity_is_exact(self) -> None:
        self.assertEqual(len(self.raw), 4_787_297)
        self.assertEqual(len(self.rows), 3_070)
        self.assertEqual(
            sha256(self.raw).hexdigest(),
            "4c038ffd45aa1b23e5e4aaf8cef4fbeafaf489a141e58335baf1b66e598816c6",
        )

    def test_independent_rebinding_derives_the_sole_capacity_rejection(self) -> None:
        self.assertEqual(self.rebound.terminal, "completed_capacity_rejection")
        self.assertFalse(self.rebound.passed)
        self.assertEqual(self.rebound.event_count, 3_068)
        self.assertEqual(len(self.rebound.phases), 3_052)
        self.assertEqual(self.rebound.journal_byte_count, len(self.raw))
        self.assertEqual(
            Counter(row["event_kind"] for row in self.observations),
            {
                "phase": 3_052,
                "laboratory": 3,
                "resource_command_stream": 2,
                "resource_command_terminal": 2,
                "population": 2,
                "provenance": 1,
                "bootstrap_handshake": 1,
                "adapter_probe": 1,
                "repaired_executed_cubin": 1,
                "resource_temporary_cleanup": 1,
                "projection": 1,
                "terminal_evidence": 1,
            },
        )

    def test_repaired_binary_resources_and_calibrations_pass(self) -> None:
        self.assertEqual(
            self.rebound.repair["repaired_payload_sha256"],
            "97693be7baafd882ad64a1a7da0ede23dc927efd872b0d15697b2486957ea894",
        )
        self.assertTrue(self.rebound.repair["retained_object_is_loaded_object"])
        self.assertEqual(
            [(row.command_id, row.status, row.return_code) for row in self.rebound.commands],
            [
                ("cuobjdump_version", "completed", 0),
                ("cuobjdump_resource_usage", "completed", 0),
            ],
        )
        runtime = next(
            row["event"]
            for row in self.observations
            if row["event_kind"] == "laboratory"
            and row["event"].get("kind") == "runtime_primitives_and_compiler"
        )
        resources = runtime["cubin_resource_usage"]
        self.assertEqual(
            resources["effective_maxima"],
            {
                "direct_selected_queries_tile": {
                    "registers": 38,
                    "stack_plus_local_backing_bytes": 128,
                },
                "direct_selected_fold_tile": {
                    "registers": 48,
                    "stack_plus_local_backing_bytes": 1_024,
                },
                "direct_selected_adjoint_tile": {
                    "registers": 38,
                    "stack_plus_local_backing_bytes": 128,
                },
            },
        )
        self.assertTrue(all(resources["gates"].values()))
        populations = {
            row["event"]["population"]: row["event"]
            for row in self.observations
            if row["event_kind"] == "population"
        }
        self.assertEqual(set(populations), {10, 22})
        self.assertEqual(populations[10]["campaign_host_ns"], 7_030_927_700)
        self.assertEqual(populations[22]["campaign_host_ns"], 56_209_478_000)
        self.assertTrue(all(row["all_gates_pass"] for row in populations.values()))

    def test_frozen_projection_rejects_without_opening_population_25(self) -> None:
        projection = self.rebound.projection
        self.assertIsNotNone(projection)
        assert projection is not None
        self.assertEqual(projection["target_population"], 25)
        self.assertEqual(projection["projected_host_ns"], 7_260_753_615_922)
        self.assertEqual(projection["wall_limit_ns"], 180_000_000_000)
        self.assertFalse(projection["passed"])
        self.assertTrue(
            all(
                row["candidate_10_ns"] > row["candidate_22_ns"]
                for row in projection["phase_rows"]
            )
        )
        phase_totals: dict[int, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        for row in self.rebound.phases:
            phase_totals[row.population][row.phase] += row.host_ns
        self.assertEqual(sum(phase_totals[10].values()), 7_030_927_700)
        self.assertEqual(sum(phase_totals[22].values()), 56_209_478_000)
        self.assertEqual(set(phase_totals), {10, 22})
        self.assertFalse(_RESERVED_ACTUAL.exists())

    def test_outcome_record_preserves_the_claims_boundary(self) -> None:
        text = (
            _ROOT
            / "docs/decisions/"
            "ADR-0416-retain-the-repaired-work-preflight-v4-capacity-rejection.md"
        ).read_text(encoding="utf-8")
        for phrase in (
            "no complete 25-card numerical value",
            "no actual 45-card value",
            "no action",
            "no 15-second result",
            "no decision-quality claim",
            "no truncation authority",
            "no poker-strength claim",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
