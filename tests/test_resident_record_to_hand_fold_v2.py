from __future__ import annotations

import importlib.util
import inspect
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np

import tests.test_leaf_adjoint_cfr as leaf_fixture
from pontius.resident_record_to_hand_fold import (
    finalize_resident_record_accumulators as finalize_legacy,
)
from pontius.resident_record_to_hand_fold_v2 import (
    AbsoluteNegativeReachAllowance,
    RelativeNegativeReachAllowance,
    ResidentReachTolerances,
    finalize_resident_record_accumulators_v2,
)


class _FakeRuntime:
    @staticmethod
    def deviceSynchronize() -> None:
        return None


class _FakeEvent:
    def record(self) -> None:
        return None

    def synchronize(self) -> None:
        return None


class _HostFakeCupy:
    float64 = np.float64
    int32 = np.int32
    cuda = SimpleNamespace(runtime=_FakeRuntime())
    asnumpy = staticmethod(lambda values: np.array(values, copy=True))
    all = staticmethod(np.all)
    isfinite = staticmethod(np.isfinite)


def _workspace(indices: np.ndarray | None = None) -> SimpleNamespace:
    supplied = (
        np.arange(3, dtype=np.int32)
        if indices is None
        else np.ascontiguousarray(indices, dtype=np.int32)
    )
    left = SimpleNamespace(
        seats=(0,),
        indices=supplied.reshape(-1, 1),
        records=len(supplied),
    )
    right = SimpleNamespace(
        seats=(),
        indices=np.empty((1, 0), dtype=np.int32),
        records=1,
    )
    base = SimpleNamespace(
        hand_counts=(3,),
        left=left,
        right=right,
    )
    return SimpleNamespace(
        topology=SimpleNamespace(base=base),
        base=SimpleNamespace(partition=2.0),
    )


def _tolerances(
    absolute: float = 2e-12,
    relative: float = 1e-10,
) -> ResidentReachTolerances:
    return ResidentReachTolerances(
        absolute=AbsoluteNegativeReachAllowance(absolute),
        relative=RelativeNegativeReachAllowance(relative),
    )


class ResidentRecordToHandFoldV2InterfaceTests(unittest.TestCase):
    def test_no_mapping_or_hybrid_tolerance_is_caller_supplied(self) -> None:
        parameters = inspect.signature(
            finalize_resident_record_accumulators_v2
        ).parameters
        self.assertNotIn("host_hand_indices", parameters)
        self.assertNotIn("device_hand_indices", parameters)
        self.assertNotIn("negative_reach_relative_allowance", parameters)
        self.assertIn("payoff_span", parameters)
        self.assertIn("reach_tolerances", parameters)

    def test_invalid_topology_and_nonfinite_host_values_fail_before_device_access(self) -> None:
        numerators = np.zeros((1, 3), dtype=np.float64)
        reaches = np.ones((1, 3), dtype=np.float64)
        with patch(
            "pontius.resident_record_to_hand_fold_v2._cupy_modules",
            side_effect=AssertionError("device runtime reached"),
        ) as modules:
            with self.assertRaisesRegex(ValueError, "target seat"):
                finalize_resident_record_accumulators_v2(
                    _workspace(),
                    target_seat=True,  # type: ignore[arg-type]
                    term_keys=(0,),
                    numerator_records=numerators,
                    reach_records=reaches,
                    payoff_span=30.0,
                    reach_tolerances=_tolerances(),
                    backend="gpu_cupy",
                )
            invalid_workspace = _workspace(np.array([-1, 1, 2], dtype=np.int32))
            with self.assertRaisesRegex(ValueError, "outside the target hand axis"):
                finalize_resident_record_accumulators_v2(
                    invalid_workspace,
                    target_seat=0,
                    term_keys=(0,),
                    numerator_records=numerators,
                    reach_records=reaches,
                    payoff_span=30.0,
                    reach_tolerances=_tolerances(),
                    backend="gpu_cupy",
                )
            for bad in (np.nan, np.inf, -np.inf):
                changed = reaches.copy()
                changed[0, 0] = bad
                with self.subTest(bad=bad), self.assertRaisesRegex(
                    FloatingPointError,
                    "finite",
                ):
                    finalize_resident_record_accumulators_v2(
                        _workspace(),
                        target_seat=0,
                        term_keys=(0,),
                        numerator_records=numerators,
                        reach_records=changed,
                        payoff_span=30.0,
                        reach_tolerances=_tolerances(),
                        backend="gpu_cupy",
                    )
        modules.assert_not_called()

    def test_valid_host_backend_matches_legacy_when_no_clamped_numerator_exists(self) -> None:
        indices = np.array([2, 0, 2, 1, 0], dtype=np.int32)
        workspace = _workspace(indices)
        numerators = np.array(
            [[1.0, 0.0, 3.0, 4.0, 5.0], [0.5, 1.5, -1.0, 2.0, 3.0]],
            dtype=np.float64,
        )
        reaches = np.array(
            [[0.2, -1e-12, 0.3, 0.4, 0.1], [0.1, 0.2, 0.0, 0.3, 0.4]],
            dtype=np.float64,
        )
        with patch(
            "pontius.resident_record_to_hand_fold._cupy_modules",
            return_value=(_HostFakeCupy(), None),
        ):
            expected = finalize_legacy(
                workspace,
                target_seat=0,
                term_keys=(7, 11),
                numerator_records=numerators,
                reach_records=reaches,
                host_hand_indices=indices,
                device_hand_indices=None,
                backend="host_numpy",
            )
        with patch(
            "pontius.resident_record_to_hand_fold_v2._cupy_modules",
            return_value=(_HostFakeCupy(), None),
        ):
            actual = finalize_resident_record_accumulators_v2(
                workspace,
                target_seat=0,
                term_keys=(7, 11),
                numerator_records=numerators,
                reach_records=reaches,
                payoff_span=30.0,
                reach_tolerances=_tolerances(),
                backend="host_numpy",
            )
        for (_, expected_row), (_, actual_row) in zip(
            expected.values,
            actual.values,
            strict=True,
        ):
            np.testing.assert_allclose(
                actual_row.root_normalized_numerators,
                expected_row.root_normalized_numerators,
                atol=0.0,
                rtol=0.0,
            )
            np.testing.assert_allclose(
                actual_row.root_normalized_reaches,
                expected_row.root_normalized_reaches,
                atol=0.0,
                rtol=0.0,
            )

    def test_near_zero_relative_reversal_and_clamped_numerator_fail_closed(self) -> None:
        workspace = _workspace(np.array([0, 1], dtype=np.int32))
        reaches = np.array([[-5e-11, 1e-20]], dtype=np.float64)
        zeros = np.zeros_like(reaches)
        with self.assertRaisesRegex(ArithmeticError, "negative reach"):
            finalize_resident_record_accumulators_v2(
                workspace,
                target_seat=0,
                term_keys=(0,),
                numerator_records=zeros,
                reach_records=reaches,
                payoff_span=30.0,
                reach_tolerances=_tolerances(absolute=1e-12, relative=1e-10),
            )

        small_reach = np.array([[-1e-12, 1.0]], dtype=np.float64)
        material_numerator = np.array([[1e-3, 0.0]], dtype=np.float64)
        with self.assertRaisesRegex(ArithmeticError, "material numerator"):
            finalize_resident_record_accumulators_v2(
                workspace,
                target_seat=0,
                term_keys=(0,),
                numerator_records=material_numerator,
                reach_records=small_reach,
                payoff_span=30.0,
                reach_tolerances=_tolerances(),
            )

    def test_device_copy_uses_topology_owned_indices(self) -> None:
        workspace = _workspace(np.array([0, 1, 2], dtype=np.int32))
        numerators = np.array([[2.0, 3.0, 5.0]], dtype=np.float64)
        reaches = np.array([[0.2, 0.3, 0.5]], dtype=np.float64)

        class FakeDeviceCupy(_HostFakeCupy):
            cuda = SimpleNamespace(
                Event=_FakeEvent,
                get_elapsed_time=lambda _first, _second: 0.0,
                runtime=_FakeRuntime(),
            )
            asarray = staticmethod(np.asarray)
            ascontiguousarray = staticmethod(
                lambda values, *, dtype: np.ascontiguousarray(values, dtype=dtype)
            )
            min = staticmethod(np.min)
            max = staticmethod(np.max)
            abs = staticmethod(np.abs)
            maximum = staticmethod(np.maximum)
            where = staticmethod(np.where)
            zeros = staticmethod(np.zeros)

        def fold_kernel(
            _blocks: tuple[int, ...],
            _threads: tuple[int, ...],
            arguments: tuple[object, ...],
        ) -> None:
            (
                supplied_numerators,
                supplied_reaches,
                supplied_indices,
                _record_count,
                _hand_count,
                _total_records,
                hand_numerators,
                hand_reaches,
            ) = arguments
            np.testing.assert_array_equal(supplied_indices, [0, 1, 2])
            for record, hand in enumerate(supplied_indices):
                if supplied_reaches[0, record] >= 0.0:
                    hand_numerators[0, hand] += supplied_numerators[0, record]
                    hand_reaches[0, hand] += supplied_reaches[0, record]

        with (
            patch(
                "pontius.resident_record_to_hand_fold_v2._cupy_modules",
                return_value=(FakeDeviceCupy, None),
            ),
            patch(
                "pontius.resident_record_to_hand_fold_v2._fold_kernel_v2",
                return_value=fold_kernel,
            ),
        ):
            result = finalize_resident_record_accumulators_v2(
                workspace,
                target_seat=0,
                term_keys=(5,),
                numerator_records=numerators,
                reach_records=reaches,
                payoff_span=30.0,
                reach_tolerances=_tolerances(),
                backend="gpu_cupy",
            )
        np.testing.assert_array_equal(
            result.values[0][1].unnormalized_numerators,
            [2.0, 3.0, 5.0],
        )


@unittest.skipUnless(importlib.util.find_spec("cupy"), "optional CuPy screen")
class ResidentRecordToHandFoldV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        leaf_fixture.LeafAdjointCFRTests.setUpClass()
        cls.workspace = leaf_fixture.LeafAdjointCFRTests.workspace

    def test_actual_device_fold_is_finite_non_consuming_and_topology_owned(self) -> None:
        import cupy as cp

        topology = self.workspace.topology.base
        half = topology.left if 0 in topology.left.seats else topology.right
        record_count = half.records
        numerators = cp.arange(record_count, dtype=cp.float64).reshape(1, -1)
        reaches = cp.linspace(0.0, 1.0, record_count, dtype=cp.float64).reshape(1, -1)
        numerator_before = numerators.copy()
        reach_before = reaches.copy()
        result = finalize_resident_record_accumulators_v2(
            self.workspace,
            target_seat=0,
            term_keys=(0,),
            numerator_records=numerators,
            reach_records=reaches,
            payoff_span=30.0,
            reach_tolerances=_tolerances(),
            backend="gpu_cupy",
        )
        cp.testing.assert_array_equal(numerators, numerator_before)
        cp.testing.assert_array_equal(reaches, reach_before)
        self.assertTrue(
            np.all(np.isfinite(result.values[0][1].root_normalized_numerators))
        )


if __name__ == "__main__":
    unittest.main()
