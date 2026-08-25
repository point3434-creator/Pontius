from __future__ import annotations

import ast
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import subprocess
import sys
import unittest

import numpy as np

import pontius.legal_river_quotient_cuda_consumer as consumer


_ROOT = Path(__file__).parents[1]
_SOURCE = _ROOT / "src/pontius/legal_river_quotient_cuda_consumer.py"
_CONFIG = _ROOT / "experiments/configs/legal-river-quotient-cuda-consumer-v1.json"
_RESERVED = _ROOT / "artifacts/legal_river_quotient_cuda_consumer_v1.jsonl"


class LegalRiverQuotientCudaConsumerSourceTests(unittest.TestCase):
    def test_import_is_device_free_and_preregistered_contract_rebinds(self) -> None:
        code = (
            "import sys; "
            "import pontius.legal_river_quotient_cuda_consumer as m; "
            "print(int('cupy' in sys.modules), m.cupy_import_call_count(), "
            "m.actual_execution_call_count(), "
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
        self.assertEqual(completed.stdout.strip(), "0 0 0 0 0")
        self.assertEqual(
            sha256(_CONFIG.read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
            consumer.PREREGISTERED_CONFIG_SHA256,
        )
        config = consumer.load_preregistered_cuda_consumer_config()
        self.assertIsNone(consumer.verify_preregistered_cuda_consumer_contract(config))

    def test_contract_rejects_dependency_geometry_and_claim_mutations(self) -> None:
        config = consumer.load_preregistered_cuda_consumer_config()
        changed_dependency = deepcopy(config)
        changed_dependency["expected_sources"]["adr0388"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "dependency differs"):
            consumer.verify_preregistered_cuda_consumer_contract(changed_dependency)
        changed_geometry = deepcopy(config)
        changed_geometry["geometry"]["source_rank"] = 174
        with self.assertRaisesRegex(ValueError, "geometry differs"):
            consumer.verify_preregistered_cuda_consumer_contract(changed_geometry)
        changed_claim = deepcopy(config)
        changed_claim["claims"]["actual_context_full_width_quotient_value"] = 1.0
        with self.assertRaisesRegex(ValueError, "claims are open"):
            consumer.verify_preregistered_cuda_consumer_contract(changed_claim)

    def test_bounded_compiler_retains_full_actual_axes_without_cupy(self) -> None:
        before = consumer.cupy_import_call_count()
        fixture = consumer.compile_consumer_population_fixture(10)
        self.assertEqual(fixture.available_cards, 10)
        self.assertEqual(fixture.pair_to_hand.shape, (45, 45))
        self.assertEqual(fixture.transitions[2].shape[1], 990)
        self.assertEqual(fixture.query_masks.shape, (1_260,))
        self.assertEqual(fixture.query_hand_indices.shape, (1_260, 2))
        self.assertTrue(all(not values.flags.writeable for values in fixture.transitions))
        self.assertEqual(consumer.cupy_import_call_count(), before)

    def test_complete_ten_card_fraction_authority_is_self_transpose(self) -> None:
        fixture = consumer.compile_consumer_population_fixture(10)
        reference = consumer.complete_ten_card_reference(fixture)
        self.assertEqual(reference.source.shape, (210, 176))
        self.assertEqual(reference.compatible.shape, (1_260, 176))
        self.assertEqual(reference.fold.shape, (1_260, 2))
        self.assertEqual(reference.adjoint.shape, (210, 176))
        self.assertEqual(reference.scalar_order[2], reference.scalar_order[7])
        self.assertGreater(reference.scalar_order[3], 0.0)
        self.assertTrue(np.all(np.isfinite(reference.source)))

    def test_kernel_roles_are_additive_offset_aware_and_allocation_explicit(self) -> None:
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
            "source_coefficients_slice",
            "zeta_level_slice",
            "signed_targets_chunk",
            "fold_query_slice",
            "build_numerator_covector_chunk",
            "aggregate_query_labels_into_level",
            "source_adjoint_contract_chunk",
            "reduce_pair_in_place",
            "reduce_scalar_in_place",
            "accumulate_results",
        ):
            self.assertIn(f'extern "C" __global__ void {role}', source)
        for required in (
            "global_feature_start",
            "occupancy_rank_start",
            "target_rank_or_record_start",
            "query_record_start",
            "source_rank_start",
            "active_width",
            "physical_stride",
        ):
            self.assertIn(required, source)
        for forbidden in (
            "cp.sum(",
            "cp.einsum(",
            "cp.repeat(",
            "atomicAdd",
        ):
            self.assertNotIn(forbidden, source)

    def test_public_bounded_entry_cannot_name_or_create_reserved_result(self) -> None:
        source = _SOURCE.read_text(encoding="utf-8")
        public = next(
            node
            for node in ast.parse(source).body
            if isinstance(node, ast.FunctionDef)
            and node.name == "run_bounded_cuda_consumer_conformance"
        )
        public_source = ast.get_source_segment(source, public)
        assert public_source is not None
        self.assertNotIn("45", public_source)
        self.assertNotIn("open(", public_source)
        self.assertNotIn("write", public_source)
        self.assertFalse(_RESERVED.exists())


@unittest.skipUnless(
    consumer.population_geometry(25).source_occupancies == 177_100,
    "frozen bounded geometry is unavailable",
)
class LegalRiverQuotientCudaConsumerDeviceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = consumer.run_bounded_cuda_consumer_conformance()

    def test_complete_ten_card_device_boundary_passes(self) -> None:
        evidence = self.report.ten_card
        self.assertTrue(evidence.all_gates_pass)
        self.assertTrue(all(evidence.gates.values()))
        self.assertLessEqual(
            evidence.maximum_errors["transpose_absolute"], 2e-10
        )

    def test_twenty_five_card_rejects_only_frozen_absolute_transpose_gate(self) -> None:
        evidence = self.report.twenty_five_card
        failed = tuple(name for name, passed in evidence.gates.items() if not passed)
        self.assertEqual(failed, ("transpose_identity",))
        self.assertEqual(
            evidence.maximum_errors["transpose_absolute"].hex(),
            "0x1.0000000000000p-20",
        )
        self.assertLessEqual(
            evidence.maximum_errors["transpose_scale_relative"], 2e-11
        )
        self.assertTrue(evidence.gates["default_alternate_byte_identity"])
        self.assertTrue(evidence.gates["repeat_byte_identity"])
        self.assertTrue(evidence.gates["selected_direct_forward"])
        self.assertTrue(evidence.gates["selected_direct_fold"])
        self.assertTrue(evidence.gates["selected_direct_adjoint"])

    def test_source_seal_fails_closed_without_actual_population_or_artifact(self) -> None:
        report = self.report
        self.assertFalse(report.all_gates_pass)
        self.assertTrue(all(report.gates.values()))
        self.assertEqual(
            (
                report.actual_execution_calls_before,
                report.actual_execution_calls_after,
                report.actual_numeric_allocation_calls_before,
                report.actual_numeric_allocation_calls_after,
                report.actual_scientific_calls_before,
                report.actual_scientific_calls_after,
            ),
            (0, 0, 0, 0, 0, 0),
        )
        self.assertFalse(_RESERVED.exists())


if __name__ == "__main__":
    unittest.main()
