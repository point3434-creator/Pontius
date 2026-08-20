from __future__ import annotations

import hashlib
import importlib.util
import unittest

from pontius.evaluation import Policy
from pontius.open_mode_audit import (
    _canonical_belief,
    _open_workspace,
    _terminal_library,
)
from pontius.public_tree_tensor import PublicTreeTensorEvaluator
from pontius.public_tree_tensor_cfr import PublicTreeTensorCFR
from pontius.river import parse_cards
from pontius.showdown_value_rank_screen import _game_from_belief
from pontius.sparse_incidence_open_mode import SparseBidirectionalIncidence
from pontius.sparse_open_mode_cfr import SparseOpenModePublicTreeCFR


def _dense_policy(schema: dict[str, tuple[str, ...]]) -> Policy:
    policy: Policy = {}
    for key, actions in schema.items():
        digest = hashlib.sha256(key.encode("utf-8")).digest()
        weights = tuple(float(1 + digest[index] % 23) for index in range(len(actions)))
        total = sum(weights)
        policy[key] = {
            action: weights[index] / total
            for index, action in enumerate(actions)
        }
    return policy


@unittest.skipUnless(importlib.util.find_spec("scipy"), "optional SciPy screen")
class SparseOpenModeCFRTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.board = parse_cards("2c", "7d", "9h", "Js", "Qc")
        cls.belief = _canonical_belief(
            board=cls.board,
            hand_count=4,
            family="balanced",
            components=3,
            seed=20260819,
        )
        game = _game_from_belief(
            belief=cls.belief,
            pot=12.0,
            stack=30.0,
            bet_size=3.0,
        )
        cls.layout = PublicTreeTensorEvaluator(game)
        cls.workspace, _ = _open_workspace(
            cls.belief,
            split_index=3,
            query_chunk_records=256,
        )
        cls.sparse = SparseBidirectionalIncidence.compile(cls.workspace)
        cls.libraries = tuple(
            _terminal_library(
                layout=cls.layout,
                belief=cls.belief,
                board=cls.board,
                target=target,
                pot=12.0,
                bet_size=3.0,
            )[:2]
            for target in range(6)
        )
        cls.policy = _dense_policy(cls.layout.information_schema())

    def assert_table_close(
        self,
        first: dict[str, dict[str, float]],
        second: dict[str, dict[str, float]],
        tolerance: float,
    ) -> None:
        self.assertEqual(first.keys(), second.keys())
        for key in first:
            self.assertEqual(first[key].keys(), second[key].keys())
            for action in first[key]:
                self.assertLessEqual(
                    abs(first[key][action] - second[key][action]),
                    tolerance,
                    msg=f"table mismatch at {key!r}/{action!r}",
                )

    def test_full_dcfr_trajectory_matches_dense_without_action_selection(self) -> None:
        dense = PublicTreeTensorCFR(self.layout, "dcfr")
        sparse = SparseOpenModePublicTreeCFR(
            self.layout,
            self.workspace,
            self.sparse,
            self.libraries,
            "dcfr",
            maximum_feature_width_per_batch=96,
        )
        dense.warm_start(self.policy, 2.5)
        sparse.warm_start(self.policy, 2.5)

        for iteration in range(2):
            dense.step()
            sparse.step()
            self.assertEqual(sparse.iteration, iteration + 1)
            self.assert_table_close(
                sparse.regret_table(),
                dense.regret_table(),
                2e-10,
            )
            self.assert_table_close(
                sparse.strategy_sum_table(),
                dense.strategy_sum_table(),
                2e-12,
            )
            self.assert_table_close(
                sparse.current_strategy(),
                dense.current_strategy(),
                2e-10,
            )
            self.assert_table_close(
                sparse.average_strategy(),
                dense.average_strategy(),
                2e-12,
            )

        work = sparse.last_step_work
        self.assertIsNotNone(work)
        assert work is not None
        self.assertEqual(len(work.traversers), 6)
        self.assertEqual(
            sum(row.strategic_reads for row in work.traversers),
            192,
        )
        self.assertGreater(work.cache_compile_ms, 0.0)
        self.assertGreater(work.action_read_ms, 0.0)
        memory = sparse.memory_summary()
        self.assertGreater(memory["sparse_operator_numeric_bytes"], 0)
        self.assertGreater(memory["last_step_maximum_read_peak_numeric_bytes"], 0)

    def test_constructor_rejects_mismatched_topology_and_terminal_count(self) -> None:
        with self.assertRaisesRegex(ValueError, "terminal library"):
            SparseOpenModePublicTreeCFR(
                self.layout,
                self.workspace,
                self.sparse,
                self.libraries[:-1],
            )
        other, _ = _open_workspace(
            self.belief,
            split_index=3,
            query_chunk_records=256,
        )
        with self.assertRaisesRegex(ValueError, "topology"):
            SparseOpenModePublicTreeCFR(
                self.layout,
                other,
                self.sparse,
                self.libraries,
            )

    def test_unrounded_write_path_matches_one_dense_cfr_step(self) -> None:
        dense = PublicTreeTensorCFR(self.layout, "cfr")
        sparse = SparseOpenModePublicTreeCFR(
            self.layout,
            self.workspace,
            self.sparse,
            self.libraries,
            "cfr",
            maximum_feature_width_per_batch=96,
            policy_cache_mode="unrounded",
        )
        dense.warm_start(self.policy, 1.0)
        sparse.warm_start(self.policy, 1.0)
        dense.step()
        sparse.step()
        self.assert_table_close(
            sparse.regret_table(),
            dense.regret_table(),
            2e-11,
        )
        self.assert_table_close(
            sparse.strategy_sum_table(),
            dense.strategy_sum_table(),
            2e-12,
        )
        self.assertIsNotNone(sparse.last_step_work)
        assert sparse.last_step_work is not None
        self.assertGreater(sparse.last_step_work.action_read_ms, 0.0)


if __name__ == "__main__":
    unittest.main()
