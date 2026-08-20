from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
import unittest

from pontius.axis_cfr_checkpoint import (
    axis_cfr_checkpoint_digest,
    export_axis_cfr_checkpoint,
    restore_axis_cfr_checkpoint,
)
from pontius.leaf_adjoint_cfr import LeafAdjointPublicTreeCFR
import tests.test_leaf_adjoint_cfr as leaf_fixture


@unittest.skipUnless(importlib.util.find_spec("scipy"), "optional SciPy screen")
class AxisCFRCheckpointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        source = leaf_fixture.LeafAdjointCFRTests
        source.setUpClass()
        cls.layout = source.layout
        cls.workspace = source.workspace
        cls.sparse = source.sparse
        cls.automata = source.automata
        cls.policy = source.policy

    def solver(self, variant: str = "dcfr") -> LeafAdjointPublicTreeCFR:
        return LeafAdjointPublicTreeCFR(
            self.layout,
            self.workspace,
            self.sparse,
            self.automata,
            variant,
            maximum_feature_width_per_batch=96,
        )

    def test_json_checkpoint_resume_is_bit_identical_to_uninterrupted_dcfr(self) -> None:
        uninterrupted = self.solver()
        uninterrupted.warm_start(self.policy, 1.0)
        uninterrupted.step()
        checkpoint = export_axis_cfr_checkpoint(
            uninterrupted,
            context={"board": "2c7d9hJsQc", "family": "balanced"},
            provenance={"audit": "unit", "source": "checkpoint16"},
        )
        serialized = json.dumps(checkpoint, allow_nan=False, sort_keys=True)
        restored_payload = json.loads(serialized)
        self.assertEqual(
            axis_cfr_checkpoint_digest(restored_payload),
            checkpoint["state_sha256"],
        )

        resumed = self.solver()
        metadata = restore_axis_cfr_checkpoint(resumed, restored_payload)
        self.assertEqual(metadata["context"]["family"], "balanced")
        self.assertEqual(metadata["provenance"]["audit"], "unit")
        self.assertEqual(resumed.iteration, 1)
        self.assertIsNone(resumed.last_step_work)

        uninterrupted.run(2)
        resumed.run(2)
        self.assertEqual(resumed.iteration, 3)
        self.assertEqual(resumed.regret_table(), uninterrupted.regret_table())
        self.assertEqual(
            resumed.strategy_sum_table(),
            uninterrupted.strategy_sum_table(),
        )
        self.assertEqual(resumed.current_strategy(), uninterrupted.current_strategy())
        self.assertEqual(resumed.average_strategy(), uninterrupted.average_strategy())

    def test_mutation_variant_and_nonpristine_restore_are_rejected(self) -> None:
        source = self.solver()
        source.warm_start(self.policy, 1.0)
        source.step()
        checkpoint = export_axis_cfr_checkpoint(source)

        changed = deepcopy(checkpoint)
        first_key = next(iter(changed["regrets"]))
        first_action = next(iter(changed["regrets"][first_key]))
        changed["regrets"][first_key][first_action] += 1.0
        with self.assertRaisesRegex(ValueError, "digest"):
            restore_axis_cfr_checkpoint(self.solver(), changed)

        with self.assertRaisesRegex(ValueError, "variant"):
            restore_axis_cfr_checkpoint(self.solver("cfr"), checkpoint)

        occupied = self.solver()
        occupied.warm_start(self.policy, 1.0)
        with self.assertRaisesRegex(ValueError, "pristine"):
            restore_axis_cfr_checkpoint(occupied, checkpoint)

    def test_cold_dcfr_checkpoint_retains_non_warm_started_trajectory(self) -> None:
        uninterrupted = self.solver()
        uninterrupted.step()
        checkpoint = export_axis_cfr_checkpoint(uninterrupted)
        self.assertFalse(checkpoint["warm_started"])

        resumed = self.solver()
        restore_axis_cfr_checkpoint(resumed, json.loads(json.dumps(checkpoint)))
        uninterrupted.step()
        resumed.step()
        self.assertEqual(resumed.regret_table(), uninterrupted.regret_table())
        self.assertEqual(
            resumed.strategy_sum_table(),
            uninterrupted.strategy_sum_table(),
        )

    def test_checkpoint_metadata_must_be_canonical_json(self) -> None:
        solver = self.solver()
        with self.assertRaisesRegex(ValueError, "context"):
            export_axis_cfr_checkpoint(solver, context={"bad": float("nan")})
        with self.assertRaisesRegex(ValueError, "provenance"):
            export_axis_cfr_checkpoint(solver, provenance={"bad": {1, 2}})


if __name__ == "__main__":
    unittest.main()
