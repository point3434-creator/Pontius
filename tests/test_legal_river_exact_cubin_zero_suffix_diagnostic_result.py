from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import unittest

from pontius.legal_river_exact_cubin_zero_suffix_diagnostic_result import (
    rebind_zero_suffix_diagnostic_file,
)


_ROOT = Path(__file__).parents[1]
_ARTIFACT = (
    _ROOT
    / "artifacts/work_preflight/legal_river_exact_cubin_zero_suffix_diagnostic_v1.jsonl"
)


class ExactZeroSuffixDiagnosticResultTests(unittest.TestCase):
    def test_retained_artifact_identity_is_exact(self) -> None:
        raw = _ARTIFACT.read_bytes()
        self.assertEqual(len(raw), 6_164_894)
        self.assertEqual(len(raw.splitlines()), 15)
        self.assertEqual(
            sha256(raw).hexdigest(),
            "f4b3de941ed57e0f4acdfc7314315b6e70b10bd0034cf82113f17bf27e39a2de",
        )

    def test_independent_rebinding_derives_the_passing_terminal(self) -> None:
        rebound = rebind_zero_suffix_diagnostic_file(_ARTIFACT)
        self.assertEqual(rebound.terminal, "suffix_reconstruction_pass")
        self.assertTrue(rebound.passed)
        self.assertEqual(rebound.event_count, 13)
        self.assertEqual(
            rebound.source_commit,
            "f4d0b181bb89eb811b07aed06e5c170b72b75c82",
        )
        self.assertEqual(
            rebound.qualified_resource_instrument,
            "cuobjdump_resource_usage_on_exact_zero_suffix_payload",
        )

    def test_every_command_and_same_byte_module_seam_is_retained(self) -> None:
        rebound = rebind_zero_suffix_diagnostic_file(_ARTIFACT)
        self.assertEqual(
            tuple(candidate.candidate_id for candidate in rebound.candidates),
            (
                "cuobjdump_version",
                "cuobjdump_resource_usage",
                "cuobjdump_elf",
                "nvdisasm_version",
                "nvdisasm_default",
                "nvdisasm_no_dataflow",
            ),
        )
        self.assertTrue(
            all(
                candidate.status == "completed" and candidate.return_code == 0
                for candidate in rebound.candidates
            )
        )
        assert rebound.repaired_payload is not None
        self.assertEqual(rebound.repaired_payload.byte_count, 514_040)
        self.assertEqual(
            rebound.repaired_payload.sha256,
            "97693be7baafd882ad64a1a7da0ede23dc927efd872b0d15697b2486957ea894",
        )
        self.assertEqual(
            rebound.module_driver_rows,
            {
                "direct_selected_queries_tile": {
                    "local_size_bytes": 128,
                    "maximum_threads_per_block": 1024,
                    "registers": 38,
                    "shared_size_bytes": 0,
                },
                "direct_selected_fold_tile": {
                    "local_size_bytes": 1024,
                    "maximum_threads_per_block": 1024,
                    "registers": 48,
                    "shared_size_bytes": 0,
                },
                "direct_selected_adjoint_tile": {
                    "local_size_bytes": 128,
                    "maximum_threads_per_block": 1024,
                    "registers": 38,
                    "shared_size_bytes": 0,
                },
            },
        )
        self.assertEqual(
            rebound.resource_rows,
            {
                "direct_selected_queries_tile": {"REG": 38, "STACK": 128, "LOCAL": 0},
                "direct_selected_fold_tile": {"REG": 48, "STACK": 1024, "LOCAL": 0},
                "direct_selected_adjoint_tile": {"REG": 38, "STACK": 128, "LOCAL": 0},
            },
        )
        self.assertEqual(
            rebound.cleanup,
            {
                "schema_version": "legal-river-zero-suffix-cleanup-v1",
                "temporary_payload_removed": True,
                "candidate_events_retained": 6,
                "module_event_retained": True,
            },
        )

    def test_outcome_record_does_not_promote_resource_or_capacity_gates(self) -> None:
        text = (
            _ROOT
            / "docs/decisions/ADR-0412-retain-the-passing-one-byte-elf-suffix-diagnostic.md"
        ).read_text(encoding="utf-8")
        for phrase in (
            "qualified instrument, not a resource-gate verdict",
            "resource gate remains null",
            "no calibration population",
            "no complete 25-card numerical value",
            "no action",
            "no poker-strength claim",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
