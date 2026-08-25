from __future__ import annotations

import ast
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

from pontius.literal_45_quotient_liveness import LITERAL_45_LIVENESS_REPORT
from pontius.literal_45_quotient_target import (
    cupy_import_call_count,
    target_execution_call_count,
    target_model,
    target_numeric_allocation_call_count,
    target_sample_ranks,
    target_scientific_call_count,
)
from pontius.literal_45_quotient_target_result import (
    ALLOCATION_BIRTH_LAST_TRANSITION,
    COMPATIBLE_REFERENCE_BYTES,
    DEVICE_PEAK_BYTES,
    EXPECTED_TARGET_NUMERIC_ALLOCATION_CALLS,
    EXPECTED_TARGET_SCIENTIFIC_CALLS,
    SOURCE_REFERENCE_BYTES,
    chunk_spans,
    target_geometry,
    target_work,
)
from pontius.literal_45_quotient_target_runner import (
    canonical_lf_sha256,
    parse_config,
)


_ROOT = Path(__file__).parents[1]
_CONFIG = _ROOT / "experiments/configs/literal-45-quotient-target-v1.json"
_RESULT = _ROOT / "artifacts/literal_45_quotient_target_v1.jsonl"
_TARGET = _ROOT / "src/pontius/literal_45_quotient_target.py"
_RUNNER = _ROOT / "src/pontius/literal_45_quotient_target_runner.py"
_READER = _ROOT / "src/pontius/literal_45_quotient_target_result.py"
_TARGET_TEST = Path(__file__)
_READER_TEST = _ROOT / "tests/test_literal_45_quotient_target_result.py"


class Literal45TargetSourceSealTests(unittest.TestCase):
    def test_source_arithmetic_matches_the_sealed_liveness_boundary(self) -> None:
        geometry = target_geometry()
        report = LITERAL_45_LIVENESS_REPORT
        self.assertEqual(geometry["available_cards"], 45)
        self.assertEqual(geometry["hand_width"], 990)
        self.assertEqual(geometry["source_occupancies"], 8_145_060)
        self.assertEqual(geometry["query_occupancies"], 148_995)
        self.assertEqual(geometry["labeled_query_records"], 893_970)
        self.assertEqual(geometry["source_rank"], 127)
        self.assertEqual(geometry["feature_width"], 128)
        self.assertEqual(target_model()["host_peak_bytes"], report.host_peak_bytes)
        self.assertEqual(
            target_model()["device_peak_bytes"], report.device_peak_bytes
        )
        self.assertEqual(report.device_peak_bytes, DEVICE_PEAK_BYTES)
        self.assertEqual(len(chunk_spans(SOURCE_REFERENCE_BYTES)), 125)
        self.assertEqual(len(chunk_spans(COMPATIBLE_REFERENCE_BYTES)), 14)

    def test_work_and_independent_samples_are_frozen_without_target_entry(self) -> None:
        work = target_work()
        self.assertEqual(work["source_pairing_visits_per_build"], 733_055_400)
        self.assertEqual(
            work["adjoint_signed_additions_per_pass"], 171_211_506_977_280
        )
        self.assertEqual(work["source_build_invocations"], 4)
        self.assertEqual(work["signed_query_invocations"], 6)
        self.assertEqual(work["affine_fold_invocations"], 6)
        self.assertEqual(work["adjoint_invocations"], 2)
        self.assertEqual(
            len(ALLOCATION_BIRTH_LAST_TRANSITION),
            EXPECTED_TARGET_NUMERIC_ALLOCATION_CALLS,
        )
        self.assertEqual(EXPECTED_TARGET_NUMERIC_ALLOCATION_CALLS, 35)
        self.assertEqual(EXPECTED_TARGET_SCIENTIFIC_CALLS, 19)
        self.assertEqual(
            target_sample_ranks(lane="source"),
            (
                0,
                8_145_059,
                5_342_038,
                4_228_481,
                2_201_283,
                4_711_753,
                6_939_721,
                5_807_274,
                2_769_721,
                2_288_776,
                7_476_024,
                272_683,
                1_670_744,
                2_715_388,
                5_176_110,
                6_960_326,
            ),
        )
        self.assertEqual(
            target_sample_ranks(lane="query"),
            (0, 148_994, 23_812, 83_359, 148_110, 22_497, 10_679, 116_159),
        )

    def test_import_is_cupy_free_and_every_target_counter_stays_zero(self) -> None:
        self.assertEqual(target_execution_call_count(), 0)
        self.assertEqual(target_numeric_allocation_call_count(), 0)
        self.assertEqual(target_scientific_call_count(), 0)
        self.assertEqual(cupy_import_call_count(), 0)
        command = (
            "import json,sys;"
            "import pontius.literal_45_quotient_target as t;"
            "import pontius.literal_45_quotient_target_runner;"
            "import pontius.literal_45_quotient_target_result;"
            "print(json.dumps({'cupy': 'cupy' in sys.modules,"
            "'execution': t.target_execution_call_count(),"
            "'allocation': t.target_numeric_allocation_call_count(),"
            "'scientific': t.target_scientific_call_count(),"
            "'imports': t.cupy_import_call_count()}))"
        )
        environment = dict(os.environ)
        environment["PYTHONPATH"] = "src;."
        completed = subprocess.run(
            [sys.executable, "-B", "-c", command],
            cwd=_ROOT,
            env=environment,
            check=True,
            capture_output=True,
            text=True,
            timeout=30.0,
        )
        self.assertEqual(
            json.loads(completed.stdout),
            {
                "cupy": False,
                "execution": 0,
                "allocation": 0,
                "scientific": 0,
                "imports": 0,
            },
        )

    def test_config_hash_binds_every_source_and_exact_contract(self) -> None:
        parsed = parse_config(json.loads(_CONFIG.read_text(encoding="utf-8")))
        self.assertEqual(parsed["contract"]["geometry"], target_geometry())
        self.assertEqual(parsed["contract"]["work"], target_work())
        self.assertEqual(
            parsed["contract"]["target_call_counts"],
            {"execution": 1, "numeric_allocation": 35, "scientific": 19},
        )
        self.assertEqual(
            parsed["expected_target_sha256"], canonical_lf_sha256(_TARGET)
        )
        self.assertEqual(
            parsed["expected_runner_sha256"], canonical_lf_sha256(_RUNNER)
        )
        self.assertEqual(
            parsed["expected_reader_sha256"], canonical_lf_sha256(_READER)
        )
        self.assertEqual(
            parsed["expected_target_controls_sha256"],
            canonical_lf_sha256(_TARGET_TEST),
        )
        self.assertEqual(
            parsed["expected_reader_controls_sha256"],
            canonical_lf_sha256(_READER_TEST),
        )

    def test_result_is_absent_and_has_one_exact_binary_attribute(self) -> None:
        self.assertFalse(_RESULT.exists())
        attributes = (_ROOT / ".gitattributes").read_text(encoding="utf-8")
        rule = "/artifacts/literal_45_quotient_target_v1.jsonl -text"
        self.assertEqual(attributes.splitlines().count(rule), 1)
        self.assertTrue((_ROOT / "artifacts/README.md").is_file())

    def test_ast_forbids_consumed_owners_target_calls_and_full_device_oracles(self) -> None:
        forbidden_calls = {
            "execute_gpu_stage",
            "run_bounded_quotient_validation_seam",
            "run_gpu_occupied_card_quotient",
            "run_full_width_river_capacity_preflight_v2",
        }
        target_tree = ast.parse(_TARGET.read_text(encoding="utf-8"))
        observed: set[str] = set()
        for node in ast.walk(target_tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    observed.add(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    observed.add(node.func.attr)
        self.assertTrue(forbidden_calls.isdisjoint(observed))
        source = _TARGET.read_text(encoding="utf-8")
        self.assertNotIn("cp.asarray(source_reference", source)
        self.assertNotIn("cp.asarray(compatible_reference", source)
        self.assertNotIn("cp.multiply(", source)

        for path in (_TARGET_TEST, _READER_TEST):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                name = None
                if isinstance(node.func, ast.Name):
                    name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    name = node.func.attr
                self.assertNotEqual(name, "execute_literal_45_quotient_target")

    def test_runner_has_one_literal_path_no_arguments_and_lazy_target_import(self) -> None:
        source = _RUNNER.read_text(encoding="utf-8")
        self.assertNotIn("argparse", source)
        self.assertIn("if len(sys.argv) != 1", source)
        self.assertIn("This import is intentionally below the durable header", source)
        self.assertEqual(source.count("literal_45_quotient_target import execute"), 1)
        self.assertNotIn(".partial", source)


if __name__ == "__main__":
    unittest.main()
