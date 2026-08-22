from __future__ import annotations

import importlib.util
import unittest

import numpy as np

from pontius.resident_record_to_hand_fold_v2 import (
    finalize_resident_record_accumulators_v2,
)
from pontius.resident_record_to_hand_fold import (
    finalize_resident_record_accumulators as finalize_legacy,
)
import tests.test_leaf_adjoint_cfr as leaf_fixture


@unittest.skipUnless(importlib.util.find_spec("cupy"), "optional CuPy screen")
class ResidentRecordToHandFoldV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        leaf_fixture.LeafAdjointCFRTests.setUpClass()
        cls.workspace = leaf_fixture.LeafAdjointCFRTests.workspace

    def test_device_fold_does_not_consume_records_and_rejects_strided_views(self) -> None:
        import cupy as cp

        hand_count = int(self.workspace.topology.base.hand_counts[0])
        record_count = max(2, hand_count)
        indices = np.arange(record_count, dtype=np.int32) % hand_count
        device_indices = cp.asarray(indices)
        numerators = cp.arange(record_count, dtype=cp.float64).reshape(1, -1)
        reaches = cp.asarray(
            np.linspace(-1e-12, 1.0, record_count, dtype=np.float64).reshape(1, -1)
        )
        numerator_before = numerators.copy()
        reach_before = reaches.copy()
        expected = finalize_legacy(
            self.workspace,
            target_seat=0,
            term_keys=(0,),
            numerator_records=numerators.copy(),
            reach_records=reaches.copy(),
            host_hand_indices=indices,
            device_hand_indices=device_indices,
            backend="host_numpy",
        )
        actual = finalize_resident_record_accumulators_v2(
            self.workspace,
            target_seat=0,
            term_keys=(0,),
            numerator_records=numerators,
            reach_records=reaches,
            host_hand_indices=indices,
            device_hand_indices=device_indices,
            backend="gpu_cupy",
        )
        cp.testing.assert_array_equal(numerators, numerator_before)
        cp.testing.assert_array_equal(reaches, reach_before)
        expected_values = expected.values[0][1]
        actual_values = actual.values[0][1]
        np.testing.assert_allclose(
            actual_values.root_normalized_reaches,
            expected_values.root_normalized_reaches,
            atol=2e-13,
            rtol=0.0,
        )
        np.testing.assert_allclose(
            actual_values.root_normalized_numerators,
            expected_values.root_normalized_numerators,
            atol=2e-12,
            rtol=0.0,
        )

        strided_numerators = cp.zeros((1, record_count * 2), dtype=cp.float64)[:, ::2]
        self.assertFalse(strided_numerators.flags.c_contiguous)
        with self.assertRaisesRegex(ValueError, "C-contiguous"):
            finalize_resident_record_accumulators_v2(
                self.workspace,
                target_seat=0,
                term_keys=(0,),
                numerator_records=strided_numerators,
                reach_records=reaches,
                host_hand_indices=indices,
                device_hand_indices=device_indices,
                backend="gpu_cupy",
            )


if __name__ == "__main__":
    unittest.main()
