from __future__ import annotations

import ast
from hashlib import sha256
from pathlib import Path
import unittest

from pontius.durable_evidence_journal import recover_journal_bytes
from pontius.literal_45_quotient_target_result import (
    CAMPAIGN_SHA256,
    CLAIMS,
    DEVICE_PEAK_BYTES,
    OWNER_PROTOCOL_SHA256,
    TELEMETRY_TRANSITIONS,
    rebind_literal_45_quotient_target_journal,
)


_ROOT = Path(__file__).parents[1]
_ARTIFACT = _ROOT / "artifacts/literal_45_quotient_target_v1.jsonl"
_READER = _ROOT / "src/pontius/literal_45_quotient_target_result.py"
_EXPECTED_ARTIFACT_SHA256 = (
    "a8c4a91416c35ca94c53349a2bb2c1182d0defea7e8d81dd71ff949d98a11970"
)
_EXPECTED_CONFIG_SHA256 = (
    "8fbff13aa40b36e6286e0142d355e9e039b0816e402ee43aa2e5f71239689c40"
)
_EXPECTED_SOURCE_COMMIT = "102307bb565892fb07fc9ec8467e91c17cc09b83"


def _target_payload() -> dict[str, object]:
    raw = _ARTIFACT.read_bytes()
    recovery = recover_journal_bytes(
        raw,
        expected_protocol_sha256=OWNER_PROTOCOL_SHA256,
        expected_campaign_sha256=CAMPAIGN_SHA256,
    )
    if not recovery.is_complete or len(recovery.records) != 3:
        raise AssertionError("literal-45 retained journal is not complete")
    target = recovery.records[1].body.payload["target"]
    if not isinstance(target, dict):
        raise AssertionError("literal-45 retained target payload is malformed")
    return target


class Literal45QuotientTargetAssessmentTests(unittest.TestCase):
    def test_retained_bytes_and_independent_terminal_are_exact(self) -> None:
        raw = _ARTIFACT.read_bytes()
        self.assertEqual(len(raw), 21_663)
        self.assertEqual(sha256(raw).hexdigest(), _EXPECTED_ARTIFACT_SHA256)
        rebound = rebind_literal_45_quotient_target_journal(
            raw,
            expected_config_sha256=_EXPECTED_CONFIG_SHA256,
        )
        self.assertEqual(rebound.terminal, "completed_pass")
        self.assertEqual(rebound.reason, "all_literal_45_target_gates_passed")
        self.assertTrue(rebound.passed)
        self.assertEqual(rebound.source_commit, _EXPECTED_SOURCE_COMMIT)
        self.assertEqual(rebound.config_sha256, _EXPECTED_CONFIG_SHA256)
        self.assertEqual(rebound.journal_sha256, _EXPECTED_ARTIFACT_SHA256)
        self.assertIsNotNone(rebound.target)
        self.assertTrue(all(rebound.target.gates.values()))
        self.assertEqual(len(rebound.target.gates), 27)

    def test_live_memory_ownership_and_release_are_exact(self) -> None:
        target = _target_payload()
        rows = target["telemetry"]
        self.assertEqual(
            tuple(row["transition"] for row in rows),
            TELEMETRY_TRANSITIONS,
        )
        self.assertEqual(max(row["pool_used_bytes"] for row in rows), 11_620_817_408)
        self.assertEqual(max(row["pool_total_bytes"] for row in rows), 11_620_834_304)
        self.assertLess(max(row["pool_total_bytes"] for row in rows), DEVICE_PEAK_BYTES)
        self.assertEqual(min(row["device_free_bytes"] for row in rows), 3_135_119_360)
        self.assertEqual(
            min(row["host_available_physical_bytes"] for row in rows),
            30_789_107_712,
        )
        self.assertEqual(
            max(row["process_private_bytes"] for row in rows),
            22_494_642_176,
        )
        self.assertEqual(rows[0]["pool_used_bytes"], 0)
        self.assertEqual(rows[0]["pool_total_bytes"], 0)
        self.assertEqual(rows[-1]["pool_used_bytes"], 0)
        self.assertEqual(rows[-1]["pool_total_bytes"], 0)
        self.assertEqual(rows[-1]["pinned_free_blocks"], 0)
        self.assertEqual(rows[-1]["owned_arrays"], [])
        self.assertEqual(rows[-1]["device_free_bytes"], rows[0]["device_free_bytes"])

    def test_numerics_work_and_lane_timings_are_exact(self) -> None:
        target = _target_payload()
        self.assertEqual(target["wall_hex"], "0x1.ad0999b7179e0p+17")
        self.assertEqual(
            target["timings_hex"],
            {
                "adjoint": "0x1.3dc088b5c0000p+11",
                "adjoint_repeat": "0x1.3927b7ce40000p+11",
                "cold": "0x1.4e71994800000p+9",
                "direct": "0x1.c5d26e0000000p+16",
                "query_only": "0x1.47a96e0000000p+6",
                "query_only_repeat": "0x1.51f5ce4000000p+6",
                "source_refresh": "0x1.943c5e8e00000p+9",
                "source_refresh_repeat": "0x1.7c0a216c00000p+9",
                "warm": "0x1.555d84c200000p+9",
            },
        )
        self.assertEqual(
            target["errors_hex"],
            {
                "affine_sample_absolute": "0x1.0000000000000p-54",
                "direct_query_absolute": "0x1.9d00000000000p-34",
                "direct_query_relative": "0x1.afab562ef5163p-45",
                "dot_product_absolute": "0x1.4000000000000p-30",
                "dot_product_relative": "0x1.3630f53ca3da8p-50",
                "source_sample_absolute": "0x1.8000000000000p-62",
            },
        )
        self.assertEqual(
            target["counters"],
            {
                "target_execution_calls": 1,
                "target_numeric_allocation_calls": 35,
                "target_scientific_call_count": 19,
            },
        )
        self.assertEqual(
            {key: len(value) for key, value in target["chunks"].items()},
            {
                "compatible_forward_dot": 14,
                "source_reference": 125,
                "source_transpose_dot": 125,
            },
        )
        self.assertIsNone(target["allocation_failure"])
        self.assertEqual(target["claims"], CLAIMS)

    def test_assessment_is_artifact_only_and_owner_stays_closed(self) -> None:
        for path in (Path(__file__), _READER):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            imports: set[str] = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.update(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module is not None:
                    imports.add(node.module)
            self.assertFalse(
                {"cupy", "numpy", "pontius.literal_45_quotient_target"}
                & imports
            )
            calls: set[str] = set()
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                if isinstance(node.func, ast.Name):
                    calls.add(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    calls.add(node.func.attr)
            self.assertNotIn("execute_literal_45_quotient_target", calls)
        self.assertEqual(CLAIMS["action_result"], None)
        self.assertEqual(CLAIMS["action_clock_result"], None)
        self.assertEqual(CLAIMS["decision_quality_result"], None)
        self.assertFalse(CLAIMS["truncation_authorized"])


if __name__ == "__main__":
    unittest.main()
