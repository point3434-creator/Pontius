from __future__ import annotations

import ast
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import subprocess
import sys
import unittest

import numpy as np

import pontius.legal_river_quotient_cuda_compensated_tiles as tiles


_ROOT = Path(__file__).parents[1]
_SOURCE = _ROOT / "src/pontius/legal_river_quotient_cuda_compensated_tiles.py"
_CONFIG_V1 = (
    _ROOT
    / "experiments/configs/legal-river-quotient-cuda-compensated-tiles-v1.json"
)
_CONFIG_V2 = (
    _ROOT
    / "experiments/configs/legal-river-quotient-cuda-compensated-tiles-v2.json"
)
_RUNNER = _ROOT / "experiments/run_legal_river_quotient_cuda_compensated_tiles.py"
_RESERVED = _ROOT / "artifacts/legal_river_quotient_cuda_consumer_v1.jsonl"


class LegalRiverQuotientCompensatedTileSourceTests(unittest.TestCase):
    def test_import_is_device_free_and_composite_contract_rebinds(self) -> None:
        code = (
            "import sys; "
            "import pontius.legal_river_quotient_cuda_compensated_tiles as m; "
            "print(int('cupy' in sys.modules), m.cupy_import_call_count(), "
            "m.bounded_execution_call_count(), m.actual_execution_call_count(), "
            "m.actual_numeric_allocation_call_count(), "
            "m.actual_scientific_call_count())"
        )
        completed = subprocess.run(
            [sys.executable, "-B", "-c", code],
            cwd=_ROOT,
            check=True,
            capture_output=True,
            text=True,
            timeout=30.0,
        )
        self.assertEqual(completed.stdout.strip(), "0 0 0 0 0 0")
        self.assertEqual(
            sha256(_CONFIG_V1.read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
            tiles.PREREGISTERED_CONFIG_V1_SHA256,
        )
        self.assertEqual(
            sha256(_CONFIG_V2.read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
            tiles.PREREGISTERED_CONFIG_V2_SHA256,
        )
        configs = tiles.load_preregistered_compensated_tile_configs()
        self.assertIsNone(tiles.verify_preregistered_compensated_tile_contract(configs))

    def test_contract_rejects_tile_tolerance_divisor_order_and_claim_drift(self) -> None:
        v1, v2 = tiles.load_preregistered_compensated_tile_configs()
        changed_tile = deepcopy(v1)
        changed_tile["logical_tile_contract"]["ordered_global_logical_ranges"][1] = [
            63,
            128,
        ]
        with self.assertRaisesRegex(ValueError, "logical ranges differ"):
            tiles.verify_preregistered_compensated_tile_contract((changed_tile, v2))
        changed_tolerance = deepcopy(v1)
        changed_tolerance["numerical_limits"]["bounded_transpose_dot_absolute"] = 1e-6
        with self.assertRaisesRegex(ValueError, "absolute limit differs"):
            tiles.verify_preregistered_compensated_tile_contract(
                (changed_tolerance, v2)
            )
        changed_divisor = deepcopy(v2)
        changed_divisor["corrected_arithmetic_contract"][
            "pair_divide_positive_small_integer_contract"
        ]["allowed_divisors"] = [1, 2, 3]
        with self.assertRaisesRegex(ValueError, "divisors differ"):
            tiles.verify_preregistered_compensated_tile_contract((v1, changed_divisor))
        changed_order = deepcopy(v2)
        changed_order["corrected_arithmetic_contract"][
            "query_weight_contract"
        ]["seat_order"] = [5, 4, 3]
        with self.assertRaisesRegex(ValueError, "query factor order differs"):
            tiles.verify_preregistered_compensated_tile_contract((v1, changed_order))
        changed_claim = deepcopy(v2)
        changed_claim["claims"]["actual_45_card_value"] = 1.0
        with self.assertRaisesRegex(ValueError, "claims are open"):
            tiles.verify_preregistered_compensated_tile_contract((v1, changed_claim))

    def test_ten_card_fraction_authority_is_exactly_self_transpose(self) -> None:
        fixture = tiles.compile_consumer_population_fixture(10)
        authority = tiles._ten_card_authority(fixture)
        self.assertEqual(len(authority.source), 210)
        self.assertEqual(len(authority.fold), 1_260)
        self.assertEqual(authority.numerator, authority.transpose)
        self.assertEqual(authority.numerator, sum(authority.forward_tiles))
        self.assertEqual(authority.transpose, sum(authority.transpose_tiles))
        self.assertGreater(authority.reach, 0)
        self.assertEqual(authority.forward_tiles[1], 0)

    def test_kernel_source_preserves_pair_tiles_offsets_and_strict_nvrtc(self) -> None:
        source = _SOURCE.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = {
            alias.name
            for node in tree.body
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names
        }
        self.assertNotIn("cupy", imports)
        for role in (
            "primitive_pairs",
            "source_coefficients_tile",
            "zeta_level_tile",
            "signed_targets_tile",
            "fold_query_tile",
            "build_numerator_covector_tile",
            "aggregate_query_labels_tile",
            "source_adjoint_contract_tile",
            "reduce_contiguous_pairs",
            "reduce_strided_pairs",
            "finalize_pair_result",
        ):
            self.assertIn(f'extern "C" __global__ void {role}', source)
        for required in (
            "global_feature_start",
            "logical_width",
            "physical_stride",
            "pair_divide_small_integer",
            "query_weight_pair",
            "fma(left, right, -high)",
            "compile_using_nvrtc",
        ):
            self.assertIn(required, source)
        for forbidden in (
            "cp.RawModule",
            "--use_fast_math",
            "atomicAdd",
            "cp.sum(",
            "cp.einsum(",
            "_parent._kernels",
            "_parent._run_device_population",
        ):
            self.assertNotIn(forbidden, source)
        self.assertEqual(
            tiles._rawmodule_options_for_static_control(),
            (
                "--std=c++14",
                "--ftz=false",
                "--prec-div=true",
                "--prec-sqrt=true",
                "--fmad=false",
            ),
        )

    def test_rejected_source_creates_no_runner_owner_or_actual_artifact(self) -> None:
        source = _SOURCE.read_text(encoding="utf-8")
        public_names = {
            node.name
            for node in ast.parse(source).body
            if isinstance(node, ast.FunctionDef) and not node.name.startswith("_")
        }
        self.assertNotIn("run_actual", " ".join(public_names))
        self.assertFalse(_RUNNER.exists())
        self.assertFalse(_RESERVED.exists())
        self.assertEqual(tiles.actual_execution_call_count(), 0)
        self.assertEqual(tiles.actual_numeric_allocation_call_count(), 0)
        self.assertEqual(tiles.actual_scientific_call_count(), 0)


@unittest.skipUnless(
    tiles.population_geometry(25).source_occupancies == 177_100,
    "frozen bounded geometry is unavailable",
)
class LegalRiverQuotientCompensatedTileDeviceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        import cupy as cp

        cls.cp = cp
        cls.kernels = tiles._kernels(cp)
        cls.primitive = tiles._run_primitive_controls(cp, cls.kernels)
        cls.fixture = tiles.compile_consumer_population_fixture(10)
        resident = tiles._allocate_resident(cp, cls.fixture)
        cls.query_weight = tiles._query_weight_evidence(
            cp, cls.kernels, resident, cls.fixture
        )
        del resident
        cp.get_default_memory_pool().free_all_blocks()
        cls.ten = tiles._ten_card_evidence(
            cp,
            cls.kernels,
            tiles.load_preregistered_compensated_tile_configs()[0],
            cls.fixture,
        )

    def test_primitives_and_query_weight_mutations_pass(self) -> None:
        self.assertTrue(self.primitive.all_gates_pass)
        self.assertTrue(all(self.primitive.gates.values()))
        self.assertTrue(self.query_weight.all_gates_pass)
        self.assertTrue(all(self.query_weight.gates.values()))
        self.assertGreater(self.query_weight.nonzero_low_count, 0)

    def test_complete_ten_card_paired_boundary_passes(self) -> None:
        self.assertTrue(self.ten.all_gates_pass)
        self.assertTrue(all(self.ten.gates.values()))
        self.assertLessEqual(
            self.ten.maximum_errors["device_forward_transpose_absolute"],
            2e-10,
        )
        self.assertTrue(self.ten.gates["normal_reverse_tile_order_byte_identity"])
        self.assertTrue(self.ten.gates["repeat_snapshot_restore_byte_identity"])
        self.assertEqual(self.ten.telemetry["stored_subnormal_count"], 0)

    def test_bounded_controls_leave_actual_boundary_closed(self) -> None:
        self.assertEqual(tiles.actual_execution_call_count(), 0)
        self.assertEqual(tiles.actual_numeric_allocation_call_count(), 0)
        self.assertEqual(tiles.actual_scientific_call_count(), 0)
        self.assertFalse(_RESERVED.exists())


if __name__ == "__main__":
    unittest.main()
