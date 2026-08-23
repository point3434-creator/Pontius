from __future__ import annotations

import inspect
import unittest

import pontius.device_fold_resident_heterogeneous_leaf_contraction_v2 as contraction_v2
import pontius.device_fold_selector_stable_affine_response_v2 as selector_v2
from pontius.convex_retreat_tolerances import (
    InterceptIdentityAllowance,
    SelectorMarginAllowance,
)
from pontius.resident_record_to_hand_fold_v2 import (
    AbsoluteNegativeReachAllowance,
    RelativeNegativeReachAllowance,
    ResidentReachTolerances,
)


class DeviceFoldSelectorStableAffineV2Tests(unittest.TestCase):
    def test_successor_is_transitively_wired_to_v2_contraction(self) -> None:
        self.assertIs(
            selector_v2.contract_device_fold_resident_heterogeneous_leaf_terms_v2,
            contraction_v2.contract_device_fold_resident_heterogeneous_leaf_terms_v2,
        )
        parameters = inspect.signature(
            selector_v2.evaluate_device_fold_selector_stable_affine_leaf_adjoint_seat_v2
        ).parameters
        self.assertIn("selector_margin_allowance", parameters)
        self.assertIn("intercept_identity_allowance", parameters)
        self.assertIn("reach_tolerances", parameters)

    def test_equal_numbers_with_crossed_semantics_fail_before_cache_access(self) -> None:
        same = 2e-11
        selector = SelectorMarginAllowance(same)
        identity = InterceptIdentityAllowance(same)
        reaches = ResidentReachTolerances(
            absolute=AbsoluteNegativeReachAllowance(1e-12),
            relative=RelativeNegativeReachAllowance(1e-10),
        )
        with self.assertRaisesRegex(TypeError, "SelectorMarginAllowance"):
            selector_v2.evaluate_device_fold_selector_stable_affine_leaf_adjoint_seat_v2(
                object(),  # type: ignore[arg-type]
                (),
                acting_player=0,
                selector_margin_allowance=identity,  # type: ignore[arg-type]
                intercept_identity_allowance=identity,
                reach_tolerances=reaches,
                belief_cache=object(),
                automaton_cache=object(),
                cupy_sparse=object(),
            )
        with self.assertRaisesRegex(TypeError, "InterceptIdentityAllowance"):
            selector_v2.evaluate_device_fold_selector_stable_affine_leaf_adjoint_seat_v2(
                object(),  # type: ignore[arg-type]
                (),
                acting_player=0,
                selector_margin_allowance=selector,
                intercept_identity_allowance=selector,  # type: ignore[arg-type]
                reach_tolerances=reaches,
                belief_cache=object(),
                automaton_cache=object(),
                cupy_sparse=object(),
            )


if __name__ == "__main__":
    unittest.main()
