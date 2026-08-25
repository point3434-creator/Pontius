from __future__ import annotations

import ast
from fractions import Fraction
from hashlib import sha256
from math import comb
import os
from pathlib import Path
import subprocess
import sys
import unittest

import numpy as np

from pontius.literal_45_quotient_liveness import (
    AVAILABLE_CARDS,
    CLAIMS,
    DEVICE_NUMERIC_CAP_BYTES,
    DEVICE_RESERVE_BYTES,
    EXCLUDED_MEMORY_CLASSES,
    FEATURE_WIDTH,
    LITERAL_45_LIVENESS_REPORT,
    MINIMUM_DEVICE_PHYSICAL_BYTES,
    PHASES,
    RETAINED_STAGED_ARTIFACT_SHA256,
    SOURCE_RANK,
    STAGED_MECHANISM_CANONICAL_LF_SHA256,
    VALIDATION_CHUNK_BYTES,
    build_literal_45_liveness_report,
    chunk_diagnostic_sha256,
    chunk_spans,
    legacy_staged_allocation,
    literal_chunk_equal,
    streamed_dot_exact,
)


_ROOT = Path(__file__).parents[1]
_SOURCE = _ROOT / "src/pontius/literal_45_quotient_liveness.py"
_STAGED_SOURCE = _ROOT / "src/pontius/gpu_quotient_staged_scaling.py"
_ARTIFACT = _ROOT / "artifacts/gpu_occupied_card_quotient_staged_scaling_v2.jsonl"


class Literal45QuotientLivenessTests(unittest.TestCase):
    def test_target_geometry_and_lineage_are_independently_rederived(self) -> None:
        report = LITERAL_45_LIVENESS_REPORT
        geometry = report.geometry
        self.assertEqual(AVAILABLE_CARDS, 45)
        self.assertEqual(geometry.hand_width, comb(45, 2))
        self.assertEqual(geometry.source_occupancies, comb(45, 6))
        self.assertEqual(geometry.query_occupancies, comb(45, 4))
        self.assertEqual(geometry.labeled_query_records, 6 * comb(45, 4))
        self.assertEqual(
            geometry.source_recurrence_rows,
            sum(comb(45, width) for width in range(7)),
        )
        self.assertEqual(
            geometry.adjoint_recurrence_rows,
            sum(comb(45, width) for width in range(5)),
        )
        self.assertEqual((SOURCE_RANK, FEATURE_WIDTH), (127, 128))
        staged = _STAGED_SOURCE.read_bytes().replace(b"\r\n", b"\n")
        self.assertEqual(
            sha256(staged).hexdigest(),
            STAGED_MECHANISM_CANONICAL_LF_SHA256,
        )
        self.assertEqual(
            sha256(_ARTIFACT.read_bytes()).hexdigest(),
            RETAINED_STAGED_ARTIFACT_SHA256,
        )

    def test_rows_are_typed_unique_and_peaks_come_only_from_the_phase_sweep(self) -> None:
        report = build_literal_45_liveness_report()
        names = [row.name for row in report.rows]
        self.assertEqual(len(names), len(set(names)))
        self.assertTrue(
            all(
                row.numeric_bytes
                == int(np.prod(row.shape)) * np.dtype(row.dtype).itemsize
                for row in report.rows
            )
        )
        independent_host = {
            phase: sum(
                row.numeric_bytes
                for row in report.rows
                if row.placement == "host" and row.live_at(phase)
            )
            for phase in PHASES
        }
        independent_device = {
            phase: sum(
                row.numeric_bytes
                for row in report.rows
                if row.placement == "device" and row.live_at(phase)
            )
            for phase in PHASES
        }
        self.assertEqual(dict(report.host_phase_bytes), independent_host)
        self.assertEqual(dict(report.device_phase_bytes), independent_device)
        self.assertEqual(report.host_peak_bytes, max(independent_host.values()))
        self.assertEqual(report.device_peak_bytes, max(independent_device.values()))

    def test_literal_target_fixed_liveness_passes_but_live_authority_is_absent(self) -> None:
        report = LITERAL_45_LIVENESS_REPORT
        self.assertEqual(report.production_forward_bytes, 10_772_495_644)
        self.assertEqual(report.device_peak_phase, "forward_dot")
        self.assertEqual(report.device_peak_bytes, 11_755_029_796)
        self.assertEqual(report.adjoint_bytes, 9_645_290_380)
        self.assertEqual(report.host_peak_phase, "forward_reference")
        self.assertEqual(report.host_peak_bytes, 9_353_336_216)
        self.assertLessEqual(report.device_peak_bytes, DEVICE_NUMERIC_CAP_BYTES)
        self.assertLessEqual(
            report.device_peak_bytes + DEVICE_RESERVE_BYTES,
            MINIMUM_DEVICE_PHYSICAL_BYTES,
        )
        self.assertTrue(report.host_numeric_cap_pass)
        self.assertTrue(report.device_numeric_cap_pass)
        self.assertTrue(report.host_physical_reserve_pass)
        self.assertTrue(report.device_physical_reserve_pass)
        self.assertIsNone(report.live_host_free_bytes)
        self.assertIsNone(report.live_device_free_bytes)
        self.assertIsNone(report.live_admission_pass)
        self.assertEqual(report.excluded_memory_classes, EXCLUDED_MEMORY_CLASSES)
        self.assertIn("allocator fragmentation", report.excluded_memory_classes[1])
        self.assertEqual(report.claims, CLAIMS)
        self.assertTrue(all(value is None or value is False for value in CLAIMS.values()))

    def test_forward_release_precedes_unique_adjoint_and_host_buffer_bridges_dot(self) -> None:
        rows = {row.name: row for row in LITERAL_45_LIVENESS_REPORT.rows}
        source = rows["device_source_recurrence"]
        compatible = rows["device_compatible_queries"]
        unique = rows["device_unique_adjoint"]
        host_large = rows["host_large_reference_buffer"]
        self.assertTrue(source.live_at("forward_dot"))
        self.assertTrue(compatible.live_at("forward_dot"))
        self.assertFalse(unique.live_at("forward_dot"))
        self.assertFalse(source.live_at("adjoint"))
        self.assertFalse(compatible.live_at("adjoint"))
        self.assertTrue(unique.live_at("adjoint"))
        self.assertTrue(host_large.live_at("forward_dot"))
        self.assertTrue(host_large.live_at("adjoint_validation"))
        self.assertFalse(
            any(
                row.placement == "device" and "reference_buffer" in row.name
                for row in rows.values()
            )
        )
        self.assertEqual(rows["host_strength_codes"].numeric_bytes, 990 * 4)

    def test_old_schedule_reconstructs_every_retained_stage_and_exposes_hidden_product(self) -> None:
        expected = {
            10: 71_499_680,
            16: 117_915_320,
            22: 364_705_168,
            28: 1_265_911_592,
            34: 3_842_056_832,
            40: 10_046_423_704,
        }
        for cards, peak in expected.items():
            with self.subTest(cards=cards):
                self.assertEqual(
                    legacy_staged_allocation(cards).requested_device_peak_bytes,
                    peak,
                )
        target = LITERAL_45_LIVENESS_REPORT.legacy_counterfactual
        self.assertEqual(target.dot_product_peak_bytes, 20_349_274_988)
        self.assertEqual(target.requested_device_peak_bytes, 20_349_274_988)
        self.assertEqual(
            target.unnamed_full_product_counterfactual_bytes,
            21_264_700_268,
        )
        self.assertGreater(
            target.requested_device_peak_bytes,
            DEVICE_NUMERIC_CAP_BYTES,
        )
        self.assertGreater(
            target.unnamed_full_product_counterfactual_bytes,
            target.requested_device_peak_bytes,
        )

    def test_chunk_spans_are_complete_ordered_and_partition_only(self) -> None:
        for total in (0, 8, 31, 128, 4097):
            for chunk in (8, 16, 64, 128):
                spans = chunk_spans(total, chunk)
                rebuilt = (
                    b"".join(
                        bytes(range(256))[start:stop] for start, stop in spans
                    )
                    if total <= 256
                    else None
                )
                self.assertEqual(sum(stop - start for start, stop in spans), total)
                self.assertTrue(all(start < stop for start, stop in spans))
                self.assertTrue(
                    all(
                        spans[index][1] == spans[index + 1][0]
                        for index in range(len(spans) - 1)
                    )
                )
                if total <= 256:
                    self.assertEqual(rebuilt, bytes(range(256))[:total])
        self.assertEqual(VALIDATION_CHUNK_BYTES, 67_108_864)
        with self.assertRaisesRegex(ValueError, "align"):
            chunk_spans(64, 7)

    def test_literal_byte_comparison_detects_mutation_and_digest_never_decides(self) -> None:
        original = np.arange(513, dtype=np.float64).reshape(27, 19)
        same = original.copy()
        for chunk in (8, 40, 128, 4096):
            self.assertTrue(literal_chunk_equal(original, same, chunk_bytes=chunk))
            self.assertEqual(
                chunk_diagnostic_sha256(original, chunk_bytes=chunk),
                sha256(original.tobytes(order="C")).hexdigest(),
            )
        same.view(np.uint8).reshape(-1)[137] ^= np.uint8(1)
        self.assertFalse(literal_chunk_equal(original, same, chunk_bytes=40))
        self.assertNotEqual(
            chunk_diagnostic_sha256(original, chunk_bytes=40),
            chunk_diagnostic_sha256(same, chunk_bytes=40),
        )

    def test_bounded_exact_dot_is_partition_invariant_with_signed_zeros(self) -> None:
        left = np.asarray(
            [0.0, -0.0, 0.1, -3.25, 7.0, 1.0 / 3.0, 2.0**-40],
            dtype=np.float64,
        )
        right = np.asarray(
            [-9.0, 11.0, 2.5, -0.75, 0.0, -5.0, 2.0**32],
            dtype=np.float64,
        )
        direct = sum(
            (
                Fraction.from_float(float(a)) * Fraction.from_float(float(b))
                for a, b in zip(left, right, strict=True)
            ),
            Fraction(0),
        )
        for chunk in (8, 16, 24, 64, 4096):
            self.assertEqual(streamed_dot_exact(left, right, chunk_bytes=chunk), direct)
        mutation = right.copy()
        mutation[3] = np.nextafter(mutation[3], np.inf)
        self.assertNotEqual(streamed_dot_exact(left, mutation, chunk_bytes=16), direct)

    def test_source_is_cupy_free_and_contains_no_target_runtime_or_full_product(self) -> None:
        source = _SOURCE.read_text(encoding="utf-8")
        tree = ast.parse(source)
        self.assertNotIn("cupy", source.lower())
        self.assertNotIn("execute_gpu_stage", source)
        self.assertNotIn("compile_stage_fixture", source)
        self.assertNotIn("np.multiply", source)
        self.assertNotIn("device_output_reference", source)
        self.assertNotIn("record_expanded_adjoint", source)
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                modules = [alias.name for alias in node.names]
                if isinstance(node, ast.ImportFrom) and node.module:
                    modules.append(node.module)
                self.assertTrue(all("cupy" not in module.lower() for module in modules))
            if (
                isinstance(node, ast.BinOp)
                and isinstance(node.op, ast.Mult)
                and isinstance(node.left, ast.Name)
                and isinstance(node.right, ast.Name)
            ):
                self.assertNotEqual(
                    {node.left.id, node.right.id},
                    {"compatible", "query_covectors"},
                )
        environment = os.environ.copy()
        environment["PYTHONPATH"] = os.pathsep.join(
            (str(_ROOT / "src"), str(_ROOT))
        )
        isolated = subprocess.run(
            (
                sys.executable,
                "-B",
                "-c",
                "import sys; "
                "assert 'cupy' not in sys.modules; "
                "import pontius.literal_45_quotient_liveness; "
                "assert 'cupy' not in sys.modules",
            ),
            cwd=_ROOT,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(
            isolated.returncode,
            0,
            isolated.stdout + isolated.stderr,
        )


if __name__ == "__main__":
    unittest.main()
