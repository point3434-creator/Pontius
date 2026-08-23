from __future__ import annotations

import importlib.util
import unittest

import numpy as np

import tests.test_device_fold_resident_paths as historical_fixture
from pontius.device_fold_resident_heterogeneous_leaf_contraction_v2 import (
    contract_device_fold_resident_heterogeneous_leaf_terms_v2,
)
from pontius.device_fold_resident_leaf_adjoint_cfr_v2 import (
    DeviceFoldResidentLeafAdjointPublicTreeCFRV2,
)
from pontius.payoff_semantics import payoff_span
from pontius.resident_heterogeneous_leaf_contraction import (
    contract_resident_heterogeneous_leaf_terms,
)
from pontius.resident_leaf_adjoint_cfr import ResidentLeafAdjointPublicTreeCFR
from pontius.resident_record_to_hand_fold_v2 import (
    AbsoluteNegativeReachAllowance,
    RelativeNegativeReachAllowance,
    ResidentReachTolerances,
)


@unittest.skipUnless(importlib.util.find_spec("cupy"), "optional CuPy screen")
class DeviceFoldResidentPathV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        historical_fixture.DeviceFoldResidentPathTests.setUpClass()
        cls.fixture = historical_fixture.DeviceFoldResidentPathTests
        cls.reach_tolerances = ResidentReachTolerances(
            absolute=AbsoluteNegativeReachAllowance(2e-12),
            relative=RelativeNegativeReachAllowance(2e-12),
        )

    def test_v2_device_contraction_matches_host_oracle(self) -> None:
        source = self.fixture.source
        terms = self.fixture._terminal_terms(target=0, limit=12)
        expected = contract_resident_heterogeneous_leaf_terms(
            source.workspace,
            source.sparse,
            terms,
            target_seat=0,
            belief_cache=self.fixture.belief_cache,
            automaton_cache=self.fixture.automaton_caches[0],
            cupy_sparse=self.fixture.gpu,
            maximum_feature_width_per_batch=96,
        )
        actual = contract_device_fold_resident_heterogeneous_leaf_terms_v2(
            source.workspace,
            source.sparse,
            terms,
            target_seat=0,
            belief_cache=self.fixture.belief_cache,
            automaton_cache=self.fixture.automaton_caches[0],
            cupy_sparse=self.fixture.gpu,
            payoff_span=payoff_span(source.layout),
            reach_tolerances=self.reach_tolerances,
            maximum_feature_width_per_batch=96,
        )

        for key, expected_values in expected.values:
            actual_values = actual.for_key(key)
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

    def test_complete_v2_device_step_matches_host_oracle(self) -> None:
        source = self.fixture.source
        common = {
            "belief_cache": self.fixture.belief_cache,
            "automaton_caches": self.fixture.automaton_caches,
            "cupy_sparse": self.fixture.gpu,
            "maximum_feature_width_per_batch": 96,
            "hands_by_player": self.fixture.hands,
        }
        expected = ResidentLeafAdjointPublicTreeCFR(
            source.layout,
            source.workspace,
            source.sparse,
            source.automata,
            "dcfr",
            **common,
        )
        actual = DeviceFoldResidentLeafAdjointPublicTreeCFRV2(
            source.layout,
            source.workspace,
            source.sparse,
            source.automata,
            "dcfr",
            reach_tolerances=self.reach_tolerances,
            **common,
        )
        expected.warm_start(source.policy, 2.5)
        actual.warm_start(source.policy, 2.5)
        expected.step()
        actual.step()

        expected_regrets = expected.regret_table()
        actual_regrets = actual.regret_table()
        maximum_regret_error = max(
            abs(actual_regrets[key][action] - expected_regrets[key][action])
            for key in expected_regrets
            for action in expected_regrets[key]
        )
        self.assertLessEqual(maximum_regret_error, 2e-12)
        expected_sums = expected.strategy_sum_table()
        actual_sums = actual.strategy_sum_table()
        maximum_sum_error = max(
            abs(actual_sums[key][action] - expected_sums[key][action])
            for key in expected_sums
            for action in expected_sums[key]
        )
        self.assertLessEqual(maximum_sum_error, 2e-12)


if __name__ == "__main__":
    unittest.main()
