from __future__ import annotations

import hashlib
import importlib.util
import unittest

import numpy as np

from pontius.canonical_affine_resident_automaton_cache import (
    CuPyCanonicalAffineResidentAutomatonCache,
)
from pontius.cupy_sparse_incidence import CuPyBidirectionalIncidence
from pontius.game import TERMINAL_PLAYER
from pontius.multi_size_affine_resident_leaf_adjoint_evaluation import (
    evaluate_multi_size_affine_resident_profile,
)
from pontius.multi_size_affine_resident_leaf_adjoint_cfr import (
    MultiSizeAffineResidentLeafAdjointPublicTreeCFR,
)
from pontius.multi_size_policy_bridge import (
    deserialize_sized_policy,
    embed_one_size_policy,
    serialize_sized_policy,
    sized_policy_digest,
)
from pontius.public_tree_tensor import PublicTreeTensorEvaluator
from pontius.resident_heterogeneous_leaf_contraction import (
    CuPyResidentAutomatonCache,
    CuPyResidentBeliefCache,
)
from pontius.river import BET, CHECK
from pontius.river_multi_size import BetAction
from pontius.river_multiway import MultiwayRiverHoldem
import tests.test_multi_size_leaf_adjoint as sized_fixture


def _one_size_layout(source) -> PublicTreeTensorEvaluator:
    game = MultiwayRiverHoldem.from_joint_weights(
        board=source.belief.board,
        pot=12.0,
        stacks=(30.0,) * 6,
        bet_size=3.0,
        joint_weights=dict(source.layout.game.deals),
    )
    return PublicTreeTensorEvaluator(game)


def _one_size_policy(layout: PublicTreeTensorEvaluator):
    result = {}
    for key, actions in layout.information_schema().items():
        digest = hashlib.sha256(key.encode("utf-8")).digest()
        weights = tuple(float(1 + digest[index] % 19) for index in range(len(actions)))
        total = sum(weights)
        result[key] = {
            action: weights[index] / total for index, action in enumerate(actions)
        }
    return result


@unittest.skipUnless(importlib.util.find_spec("scipy"), "optional SciPy screen")
class MultiSizePolicyBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        sized_fixture.MultiSizeLeafAdjointTests.setUpClass()
        cls.source = sized_fixture.MultiSizeLeafAdjointTests
        cls.one_layout = _one_size_layout(cls.source)
        cls.one_policy = _one_size_policy(cls.one_layout)
        cls.embedded = embed_one_size_policy(
            cls.one_layout,
            cls.source.layout,
            cls.source.belief.hands_by_player,
            cls.one_policy,
            retained_bet_size=3.0,
        )

    def test_embedding_is_complete_and_added_size_has_zero_opening_mass(self) -> None:
        self.assertEqual(
            set(self.embedded),
            set(self.source.layout.information_schema()),
        )
        for node in self.source.layout.nodes:
            if node.player == TERMINAL_PLAYER or CHECK not in node.actions:
                continue
            added = next(
                action
                for action in node.actions
                if isinstance(action, BetAction) and action.amount == 6.0
            )
            for key in node.information_keys:
                self.assertEqual(self.embedded[key][added], 0.0)
                retained = next(
                    action
                    for action in node.actions
                    if isinstance(action, BetAction) and action.amount == 3.0
                )
                self.assertAlmostEqual(
                    self.embedded[key][CHECK] + self.embedded[key][retained],
                    1.0,
                )

    def test_embedding_preserves_profile_utilities_in_the_one_size_support(self) -> None:
        one = self.one_layout.evaluate(self.one_policy).evaluation.utilities
        sized = self.source.layout.evaluate(self.embedded).evaluation.utilities
        np.testing.assert_allclose(sized, one, atol=2e-13, rtol=0.0)

    def test_sized_policy_serialization_round_trips_action_types(self) -> None:
        record = serialize_sized_policy(self.embedded)
        restored = deserialize_sized_policy(
            record,
            self.source.layout,
            self.source.belief.hands_by_player,
        )
        self.assertEqual(sized_policy_digest(restored), record["policy_sha256"])
        self.assertEqual(restored, self.embedded)

    def test_digest_distinguishes_added_bet_probability(self) -> None:
        changed = {key: dict(row) for key, row in self.embedded.items()}
        root = self.source.layout.nodes[0]
        key = root.information_keys[0]
        retained = next(
            action
            for action in root.actions
            if isinstance(action, BetAction) and action.amount == 3.0
        )
        added = next(
            action
            for action in root.actions
            if isinstance(action, BetAction) and action.amount == 6.0
        )
        moved = min(0.01, changed[key][retained])
        changed[key][retained] -= moved
        changed[key][added] += moved
        self.assertNotEqual(
            sized_policy_digest(changed),
            sized_policy_digest(self.embedded),
        )


@unittest.skipUnless(importlib.util.find_spec("cupy"), "optional CuPy screen")
class MultiSizeAffineResidentEvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        sized_fixture.MultiSizeLeafAdjointTests.setUpClass()
        cls.source = sized_fixture.MultiSizeLeafAdjointTests
        cls.gpu = CuPyBidirectionalIncidence.compile(cls.source.sparse)
        cls.belief_cache = CuPyResidentBeliefCache.compile(cls.source.workspace)
        cls.caches = tuple(
            CuPyCanonicalAffineResidentAutomatonCache.compile(
                cls.source.workspace,
                cls.source.automata[seat],
                target_seat=seat,
            )
            for seat in range(6)
        )
        cls.raw_caches = tuple(
            CuPyResidentAutomatonCache.compile(
                cls.source.workspace,
                cls.source.automata[seat],
                target_seat=seat,
            )
            for seat in range(6)
        )

    def test_complete_profile_matches_dense_sized_teacher(self) -> None:
        dense = self.source.layout.evaluate(self.source.policy)
        resident = evaluate_multi_size_affine_resident_profile(
            self.source.layout,
            self.source.workspace,
            self.source.sparse,
            self.source.policy,
            self.source.automata,
            belief_cache=self.belief_cache,
            automaton_caches=self.caches,
            cupy_sparse=self.gpu,
            hands_by_player=self.source.belief.hands_by_player,
            maximum_feature_width_per_batch=96,
        )
        np.testing.assert_allclose(
            resident.evaluation.utilities,
            dense.evaluation.utilities,
            atol=2e-12,
            rtol=0.0,
        )
        np.testing.assert_allclose(
            resident.evaluation.best_response_values,
            dense.evaluation.best_response_values,
            atol=2e-12,
            rtol=0.0,
        )
        np.testing.assert_allclose(
            resident.evaluation.deviation_gains,
            dense.evaluation.deviation_gains,
            atol=2e-12,
            rtol=0.0,
        )
        self.assertLessEqual(
            abs(resident.evaluation.nash_conv - dense.evaluation.nash_conv),
            2e-12,
        )
        self.assertLessEqual(resident.zero_sum_residual, 2e-12)
        self.assertEqual(
            sum(cache.shared_topologies for cache in self.caches),
            378,
        )

    def test_three_step_canonical_trajectory_matches_raw_resident(self) -> None:
        from pontius.multi_size_resident_leaf_adjoint_cfr import (
            MultiSizeResidentLeafAdjointPublicTreeCFR,
        )

        raw = MultiSizeResidentLeafAdjointPublicTreeCFR(
            self.source.layout,
            self.source.workspace,
            self.source.sparse,
            self.source.automata,
            "dcfr",
            belief_cache=self.belief_cache,
            automaton_caches=self.raw_caches,
            cupy_sparse=self.gpu,
            maximum_feature_width_per_batch=96,
            hands_by_player=self.source.belief.hands_by_player,
        )
        canonical = MultiSizeAffineResidentLeafAdjointPublicTreeCFR(
            self.source.layout,
            self.source.workspace,
            self.source.sparse,
            self.source.automata,
            "dcfr",
            belief_cache=self.belief_cache,
            automaton_caches=self.caches,
            cupy_sparse=self.gpu,
            maximum_feature_width_per_batch=96,
            hands_by_player=self.source.belief.hands_by_player,
        )
        raw.warm_start(self.source.policy, 4.8)
        canonical.warm_start(self.source.policy, 4.8)
        raw.run(3)
        canonical.run(3)
        for left, right in (
            (raw.regret_table(), canonical.regret_table()),
            (raw.strategy_sum_table(), canonical.strategy_sum_table()),
        ):
            maximum = max(
                abs(float(left[key][action]) - float(right[key][action]))
                for key in left
                for action in left[key]
            )
            self.assertLessEqual(maximum, 2e-11)


if __name__ == "__main__":
    unittest.main()
