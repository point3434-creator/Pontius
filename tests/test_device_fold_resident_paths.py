from __future__ import annotations

import copy
import importlib.util
import unittest

import numpy as np

from pontius.batched_selector_stable_affine_response import (
    evaluate_batched_selector_stable_affine_opponents,
)
from pontius.cupy_sparse_incidence import CuPyBidirectionalIncidence
from pontius.device_fold_resident_heterogeneous_leaf_contraction import (
    contract_device_fold_resident_heterogeneous_leaf_terms,
)
from pontius.device_fold_resident_leaf_adjoint_cfr import (
    DeviceFoldResidentLeafAdjointPublicTreeCFR,
)
from pontius.device_fold_selector_stable_affine_response import (
    evaluate_device_fold_batched_selector_stable_affine_opponents,
    evaluate_device_fold_selector_stable_affine_leaf_adjoint_seat,
)
from pontius.heterogeneous_leaf_contraction import HeterogeneousLeafTerm
from pontius.incremental_leaf_adjoint_response import (
    compile_leaf_adjoint_response_caches,
)
from pontius.incremental_policy_tt import compile_policy_probability_tape
from pontius.leaf_adjoint_cfr import (
    _parent_metadata,
    _target_omitted_path_factors,
)
from pontius.public_policy_tt import _information_key, _terminal_keys_by_slot
from pontius.resident_heterogeneous_leaf_contraction import (
    CuPyResidentAutomatonCache,
    CuPyResidentBeliefCache,
    contract_resident_heterogeneous_leaf_terms,
)
from pontius.resident_leaf_adjoint_cfr import ResidentLeafAdjointPublicTreeCFR
from pontius.selector_stable_affine_response import (
    evaluate_selector_stable_affine_leaf_adjoint_seat,
)
import tests.test_leaf_adjoint_cfr as leaf_fixture
import tests.test_sparse_open_mode_cfr as sparse_fixture


@unittest.skipUnless(importlib.util.find_spec("cupy"), "optional CuPy screen")
class DeviceFoldResidentPathTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        leaf_fixture.LeafAdjointCFRTests.setUpClass()
        cls.source = leaf_fixture.LeafAdjointCFRTests
        cls.hands = sparse_fixture.SparseOpenModeCFRTests.belief.hands_by_player
        cls.gpu = CuPyBidirectionalIncidence.compile(cls.source.sparse)
        cls.belief_cache = CuPyResidentBeliefCache.compile(cls.source.workspace)
        cls.automaton_caches = tuple(
            CuPyResidentAutomatonCache.compile(
                cls.source.workspace,
                cls.source.automata[seat],
                target_seat=seat,
            )
            for seat in range(6)
        )
        cls.response_caches = compile_leaf_adjoint_response_caches(
            cls.source.layout,
            cls.source.workspace,
            cls.source.sparse,
            cls.source.policy,
            cls.source.automata,
            hands_by_player=cls.hands,
            maximum_feature_width_per_batch=96,
            belief_cache=cls.belief_cache,
            automaton_caches=cls.automaton_caches,
            cupy_sparse=cls.gpu,
        )

    @classmethod
    def _terminal_terms(cls, *, target: int, limit: int) -> tuple[HeterogeneousLeafTerm, ...]:
        parents, parent_actions = _parent_metadata(cls.source.layout)
        terminal_keys = _terminal_keys_by_slot(cls.source.layout)
        terms = []
        for node_index, node in enumerate(cls.source.layout.nodes):
            if node.terminal_slot < 0:
                continue
            terms.append(
                HeterogeneousLeafTerm(
                    key=node_index,
                    automaton=cls.source.automata[target][
                        terminal_keys[node.terminal_slot]
                    ],
                    mode_factors=_target_omitted_path_factors(
                        cls.source.layout,
                        cls.source.probabilities,
                        parents,
                        parent_actions,
                        terminal_node=node_index,
                        traverser=target,
                        shape=cls.source.workspace.topology.base.hand_counts,
                    ),
                )
            )
            if len(terms) == limit:
                break
        return tuple(terms)

    @classmethod
    def _endpoint_for_actor(cls, actor: int):
        node_index, node = next(
            (node_index, node)
            for node_index, node in enumerate(cls.source.layout.nodes)
            if node.player == actor and len(node.actions) >= 2
        )
        key = _information_key(
            cls.source.layout,
            actor,
            cls.hands[actor][0],
            node.history,
        )
        row = cls.source.probabilities[node_index]
        assert row is not None
        selected = int(np.argmin(row[0]))
        policy = copy.deepcopy(cls.source.policy)
        policy[key] = {
            action: float(index == selected)
            for index, action in enumerate(node.actions)
        }
        return compile_policy_probability_tape(
            cls.source.layout,
            cls.hands,
            policy,
        )

    def test_device_fold_matches_accepted_host_fold_vectors(self) -> None:
        terms = self._terminal_terms(target=0, limit=12)
        expected = contract_resident_heterogeneous_leaf_terms(
            self.source.workspace,
            self.source.sparse,
            terms,
            target_seat=0,
            belief_cache=self.belief_cache,
            automaton_cache=self.automaton_caches[0],
            cupy_sparse=self.gpu,
            maximum_feature_width_per_batch=96,
        )
        actual = contract_device_fold_resident_heterogeneous_leaf_terms(
            self.source.workspace,
            self.source.sparse,
            terms,
            target_seat=0,
            belief_cache=self.belief_cache,
            automaton_cache=self.automaton_caches[0],
            cupy_sparse=self.gpu,
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
        self.assertEqual(
            actual.work.operator_backend,
            "gpu_cupy_resident_device_fold",
        )
        self.assertGreater(actual.work.device_hand_fold_gpu_ms, 0.0)
        self.assertGreater(actual.work.host_hand_finalize_ms, 0.0)
        self.assertLess(
            actual.work.per_call_device_to_host_bytes,
            expected.work.per_call_device_to_host_bytes,
        )

    def test_complete_device_fold_step_matches_accepted_resident_step(self) -> None:
        common = dict(
            belief_cache=self.belief_cache,
            automaton_caches=self.automaton_caches,
            cupy_sparse=self.gpu,
            maximum_feature_width_per_batch=96,
            hands_by_player=self.hands,
        )
        expected = ResidentLeafAdjointPublicTreeCFR(
            self.source.layout,
            self.source.workspace,
            self.source.sparse,
            self.source.automata,
            "dcfr",
            **common,
        )
        actual = DeviceFoldResidentLeafAdjointPublicTreeCFR(
            self.source.layout,
            self.source.workspace,
            self.source.sparse,
            self.source.automata,
            "dcfr",
            **common,
        )
        expected.warm_start(self.source.policy, 2.5)
        actual.warm_start(self.source.policy, 2.5)
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
        self.assertIsNotNone(actual.last_step_work)
        assert actual.last_step_work is not None
        self.assertTrue(
            all(
                row.resident_work.device_hand_fold_gpu_ms > 0.0
                for row in actual.last_step_work.traversers
            )
        )

    def test_device_fold_scalar_and_batch_match_accepted_affine_rows(self) -> None:
        target = 0
        actors = (1, 2, 3)
        endpoints = tuple(self._endpoint_for_actor(actor) for actor in actors)
        host_scalar = tuple(
            evaluate_selector_stable_affine_leaf_adjoint_seat(
                self.response_caches[target],
                endpoint,
                acting_player=actor,
                selector_margin_allowance=1e-14,
                maximum_feature_width_per_batch=96,
                belief_cache=self.belief_cache,
                automaton_cache=self.automaton_caches[target],
                cupy_sparse=self.gpu,
            )
            for endpoint, actor in zip(endpoints, actors, strict=True)
        )
        device_scalar = tuple(
            evaluate_device_fold_selector_stable_affine_leaf_adjoint_seat(
                self.response_caches[target],
                endpoint,
                acting_player=actor,
                selector_margin_allowance=1e-14,
                maximum_feature_width_per_batch=96,
                belief_cache=self.belief_cache,
                automaton_cache=self.automaton_caches[target],
                cupy_sparse=self.gpu,
            )
            for endpoint, actor in zip(endpoints, actors, strict=True)
        )
        host_batch = evaluate_batched_selector_stable_affine_opponents(
            self.response_caches[target],
            endpoints,
            acting_players=actors,
            selector_margin_allowance=1e-14,
            maximum_feature_width_per_batch=96,
            belief_cache=self.belief_cache,
            automaton_cache=self.automaton_caches[target],
            cupy_sparse=self.gpu,
        )
        device_batch = evaluate_device_fold_batched_selector_stable_affine_opponents(
            self.response_caches[target],
            endpoints,
            acting_players=actors,
            selector_margin_allowance=1e-14,
            maximum_feature_width_per_batch=96,
            belief_cache=self.belief_cache,
            automaton_cache=self.automaton_caches[target],
            cupy_sparse=self.gpu,
        )

        numeric = (
            "profile_utility_intercept",
            "profile_utility_slope",
            "best_response_value_intercept",
            "best_response_value_slope",
            "deviation_gain_intercept",
            "deviation_gap_slope",
            "selector_stable_scale",
        )
        structural = (
            "target_player",
            "acting_player",
            "changed_public_node",
            "first_switch_information_key",
            "first_switch_source_action",
            "first_switch_competing_action",
            "first_switch_hand_index",
            "selector_comparisons",
            "exact_source_action_ties",
            "affected_terminal_contractions",
            "reused_terminal_numerators",
        )
        for index, expected in enumerate(host_scalar):
            alternatives = (
                device_scalar[index].semantic,
                host_batch.seat_results[index],
                device_batch.seat_results[index],
            )
            for actual in alternatives:
                for field in numeric:
                    self.assertLessEqual(
                        abs(getattr(actual, field) - getattr(expected, field)),
                        2e-11,
                    )
                for field in structural:
                    self.assertEqual(getattr(actual, field), getattr(expected, field))
        self.assertTrue(
            all(row.work is not None for row in device_scalar)
        )
        self.assertIsNotNone(device_batch.work.contraction)
        assert device_batch.work.contraction is not None
        self.assertGreater(
            device_batch.work.contraction.device_hand_fold_gpu_ms,
            0.0,
        )


if __name__ == "__main__":
    unittest.main()
