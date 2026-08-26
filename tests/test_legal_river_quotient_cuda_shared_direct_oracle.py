from __future__ import annotations

import ast
from hashlib import sha256
import json
from math import comb
from pathlib import Path
import subprocess
import sys
import unittest

from pontius import legal_river_quotient_cuda_compensated_work_preflight as v4
from pontius import legal_river_quotient_cuda_shared_direct_oracle as source


_ROOT = Path(__file__).parents[1]
_SOURCE = _ROOT / "src/pontius/legal_river_quotient_cuda_shared_direct_oracle.py"
_CONFIG = (
    _ROOT
    / "experiments/configs/legal-river-quotient-cuda-shared-direct-oracle-v1.json"
)
_PROSPECTIVE_RESULT = (
    _ROOT
    / "artifacts/work_preflight/"
    "legal_river_quotient_cuda_shared_direct_oracle_v1.jsonl"
)
_RESERVED_ACTUAL = _ROOT / "artifacts/legal_river_quotient_cuda_consumer_v1.jsonl"


def _replace_parent_fold(kernel: str) -> str:
    start, stop = source._kernel_span(v4.CUDA_SOURCE, "direct_selected_fold_tile")
    return v4.CUDA_SOURCE[:start] + kernel + v4.CUDA_SOURCE[stop:]


class SharedSelectedDirectOracleSourceSealTests(unittest.TestCase):
    def test_config_and_parent_sources_rebind_without_result_paths(self) -> None:
        config = source.load_preregistered_shared_direct_config()
        source.verify_preregistered_shared_direct_contract(config)
        self.assertEqual(
            sha256(_CONFIG.read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
            source.PREREGISTERED_CONFIG_SHA256,
        )
        self.assertFalse(_PROSPECTIVE_RESULT.exists())
        self.assertFalse(_RESERVED_ACTUAL.exists())
        self.assertFalse(config["claims"]["successor_source_exists"])
        self.assertIsNone(config["claims"]["device_differential_result"])
        self.assertIsNone(config["claims"]["complete_25_capacity_projection_result"])

    def test_fresh_import_and_report_are_cupy_free(self) -> None:
        command = (
            "import sys; "
            "import pontius.legal_river_quotient_cuda_shared_direct_oracle as s; "
            "import pontius.legal_river_quotient_cuda_compensated_tiles as p; "
            "import pontius.legal_river_quotient_cuda_compensated_work_preflight as v; "
            "print(int('cupy' in sys.modules), p.cupy_import_call_count(), "
            "v.cupy_import_call_count(), int(s.source_seal_report()['all_gates_pass']))"
        )
        completed = subprocess.run(
            [sys.executable, "-B", "-c", command],
            cwd=_ROOT,
            env={**dict(__import__("os").environ), "PYTHONPATH": "src;."},
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(completed.stdout.strip(), "0 0 0 1")
        self.assertEqual(completed.stderr, "")

    def test_source_builder_changes_exactly_the_fold_kernel_span(self) -> None:
        parent_fold = source._kernel_span(v4.CUDA_SOURCE, "direct_selected_fold_tile")
        shared_fold = source._kernel_span(
            source.CUDA_SOURCE, "direct_selected_fold_tile"
        )
        self.assertEqual(
            source.CUDA_SOURCE[: shared_fold[0]], v4.CUDA_SOURCE[: parent_fold[0]]
        )
        self.assertEqual(
            source.CUDA_SOURCE[shared_fold[1] :], v4.CUDA_SOURCE[parent_fold[1] :]
        )
        parent_query = v4.CUDA_SOURCE[
            slice(*source._kernel_span(v4.CUDA_SOURCE, "direct_selected_queries_tile"))
        ]
        shared_query = source.CUDA_SOURCE[
            slice(
                *source._kernel_span(
                    source.CUDA_SOURCE, "direct_selected_queries_tile"
                )
            )
        ]
        self.assertEqual(shared_query.encode(), parent_query.encode())
        source.verify_shared_direct_cuda_source(source.CUDA_SOURCE)

    def test_sequence_model_proves_byte_identity_and_detects_mutations(self) -> None:
        report = source.run_shared_direct_sequence_controls()
        self.assertTrue(report["all_gates_pass"])
        self.assertEqual(report["reference_sha256"], report["shared_sha256"])
        self.assertTrue(all(report["gates"].values()))

        rows = (
            (
                source.FloatPair(1.0, 2.0**-54),
                source.FloatPair(-0.0, 2.0**-80),
                source.FloatPair(3.0, -2.0**-70),
            ),
            (
                source.FloatPair(-1.0, 2.0**-53),
                source.FloatPair(4.0, -2.0**-75),
                source.FloatPair(-3.0, 2.0**-69),
            ),
        )
        reference = source.reference_selected_query_pairs(rows, (True, False), (0, 2))
        coefficients, shared = source.shared_fold_coefficients_and_query_pairs(
            rows, (True, False), (0, 2)
        )
        self.assertEqual(shared, reference)
        self.assertEqual(shared, (coefficients[0], coefficients[2]))

    def test_work_reduction_is_independently_exact(self) -> None:
        expected = {
            10: (40_320, 512),
            22: (14_325_696, 9_504_768),
            25: (34_003_200, 27_783_168),
        }
        for cards, (unranks, additions) in expected.items():
            work = source.derive_shared_direct_work(cards)
            self.assertEqual(work.source_occupancies, comb(cards, 6))
            self.assertEqual(
                work.compatible_sources_per_query, comb(cards - 4, 6)
            )
            self.assertEqual(work.eliminated_query_source_unranks, unranks)
            self.assertEqual(
                work.eliminated_query_compatible_boundary_pair_adds, additions
            )
            self.assertEqual(work.replacement_boundary_pair_copies, 512)
            self.assertEqual(work.retained_fold_source_unranks, unranks)
            self.assertEqual(
                work.retained_fold_compatible_coefficient_pair_adds,
                16 * comb(cards - 4, 6) * 176 * 4,
            )

    def test_static_validator_rejects_early_copy_and_order_mutations(self) -> None:
        fold = source._FUSED_FOLD_KERNEL
        row_marker = "for (long long row = 0; row < source_rows; ++row)"
        row_start = fold.index(row_marker)
        row_open = fold.index("{", row_start + len(row_marker))
        row_stop = source._balanced_block_stop(fold, row_open)
        copy_marker = (
            "for (int feature_index = 0; feature_index < feature_count; "
            "++feature_index)"
        )
        copy_start = fold.index(copy_marker)
        copy_open = fold.index("{", copy_start)
        copy_stop = source._balanced_block_stop(fold, copy_open)
        early = (
            fold[:row_start]
            + fold[copy_start:copy_stop]
            + fold[row_stop:copy_start]
            + fold[row_start:row_stop]
            + fold[copy_stop:]
        )
        mutations = (
            early,
            fold.replace(
                "global_features[feature_index] - global_feature_start",
                "global_features[feature_index] + 1 - global_feature_start",
                1,
            ),
            fold.replace(
                "for (long long row = 0; row < source_rows; ++row)",
                "for (long long row = source_rows - 1; row >= 0; --row)",
                1,
            ),
            fold.replace(
                "double *query_output, double *output",
                "double *output, double *output_alias",
                1,
            ),
            fold.replace(
                "query_output[2 * index] = value.high;",
                "query_output[2 * index] = value.high + value.low;",
                1,
            ),
        )
        for mutated in mutations:
            with self.assertRaises(ValueError):
                source.verify_shared_direct_cuda_source(_replace_parent_fold(mutated))

    def test_source_builder_rejects_duplicate_parent_kernel(self) -> None:
        duplicated = v4.CUDA_SOURCE + v4.CUDA_SOURCE[
            slice(*source._kernel_span(v4.CUDA_SOURCE, "direct_selected_fold_tile"))
        ]
        with self.assertRaisesRegex(ValueError, "kernel occurrence differs"):
            source.build_shared_direct_cuda_source(duplicated)

    def test_source_has_no_owner_device_or_result_side_effect_surface(self) -> None:
        tree = ast.parse(_SOURCE.read_text(encoding="utf-8"))
        imports = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        imported_from = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module is not None
        }
        self.assertNotIn("cupy", imports)
        self.assertNotIn("subprocess", imports)
        self.assertNotIn("cupy", imported_from)
        text = _SOURCE.read_text(encoding="utf-8")
        for forbidden in ("compile_using_nvrtc(", "Module()", ".linear_launch(", "xb"):
            self.assertNotIn(forbidden, text)
        self.assertFalse(_PROSPECTIVE_RESULT.exists())
        self.assertFalse(_RESERVED_ACTUAL.exists())

    def test_source_seal_report_and_documentation_preserve_claims(self) -> None:
        report = source.source_seal_report()
        self.assertTrue(report["all_gates_pass"])
        self.assertTrue(all(report["gates"].values()))
        text = (
            _ROOT
            / "docs/decisions/"
            "ADR-0418-source-seal-the-shared-selected-direct-oracle.md"
        ).read_text(encoding="utf-8")
        for phrase in (
            "no device differential",
            "no capacity projection",
            "no complete 25-card numerical value",
            "no action",
            "no 15-second result",
            "no decision-quality claim",
            "no poker-strength claim",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
