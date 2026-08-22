from __future__ import annotations

import unittest

import numpy as np

from pontius.game import TERMINAL_PLAYER
from pontius.multi_size_continuation_public_tree_tensor import (
    MultiSizeContinuationPublicTreeTensorEvaluator,
)
from pontius.river import CHECK
from pontius.river_multi_size import BetAction
import tests.test_multi_size_leaf_adjoint as sized_fixture


def _subtree_indices(layout: object, root: int) -> tuple[int, ...]:
    result = []

    def collect(node_index: int) -> None:
        result.append(node_index)
        for child in layout.nodes[node_index].children:
            collect(child)

    collect(root)
    return tuple(result)


class MultiSizeContinuationPublicTreeTensorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        sized_fixture.MultiSizeLeafAdjointTests.setUpClass()
        cls.full = sized_fixture.MultiSizeLeafAdjointTests.layout

    def test_empty_and_check_prefixes_are_exact_full_subtrees(self) -> None:
        prefixes = (
            (),
            ((0, CHECK),),
            ((0, CHECK), (1, CHECK)),
            ((0, CHECK), (1, BetAction(6.0))),
        )
        for prefix in prefixes:
            with self.subTest(prefix=prefix):
                continuation = MultiSizeContinuationPublicTreeTensorEvaluator(
                    self.full.game,
                    public_prefix=prefix,
                )
                old_root = next(
                    index
                    for index, node in enumerate(self.full.nodes)
                    if node.history == prefix
                )
                old_indices = _subtree_indices(self.full, old_root)
                old_terminal_slots = [
                    self.full.nodes[index].terminal_slot
                    for index in old_indices
                    if self.full.nodes[index].player == TERMINAL_PLAYER
                ]
                self.assertEqual(len(continuation.nodes), len(old_indices))
                self.assertEqual(continuation.public_prefix, prefix)
                self.assertEqual(continuation.topology_mismatch_count(), 0)
                for new_index, old_index in enumerate(old_indices):
                    left = continuation.nodes[new_index]
                    right = self.full.nodes[old_index]
                    self.assertEqual(left.player, right.player)
                    self.assertEqual(left.actions, right.actions)
                    self.assertEqual(left.history, right.history)
                    self.assertEqual(left.information_keys, right.information_keys)
                np.testing.assert_array_equal(
                    continuation.terminal_values,
                    self.full.terminal_values[old_terminal_slots],
                )
                self.assertEqual(
                    continuation.terminal_descriptors,
                    tuple(
                        self.full.terminal_descriptors[slot]
                        for slot in old_terminal_slots
                    ),
                )

    def test_pre_bet_root_really_exposes_both_sizes(self) -> None:
        continuation = MultiSizeContinuationPublicTreeTensorEvaluator(
            self.full.game,
            public_prefix=((0, CHECK), (1, CHECK)),
        )
        self.assertEqual(continuation.nodes[0].player, 2)
        self.assertEqual(
            continuation.nodes[0].actions,
            (CHECK, BetAction(3.0), BetAction(6.0)),
        )

    def test_wrong_actor_illegal_action_and_terminal_prefix_fail_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "actor"):
            MultiSizeContinuationPublicTreeTensorEvaluator(
                self.full.game,
                public_prefix=((1, CHECK),),
            )
        with self.assertRaisesRegex(ValueError, "illegal"):
            MultiSizeContinuationPublicTreeTensorEvaluator(
                self.full.game,
                public_prefix=((0, "call"),),
            )
        with self.assertRaisesRegex(ValueError, "decision node"):
            MultiSizeContinuationPublicTreeTensorEvaluator(
                self.full.game,
                public_prefix=tuple((seat, CHECK) for seat in range(6)),
            )


if __name__ == "__main__":
    unittest.main()
