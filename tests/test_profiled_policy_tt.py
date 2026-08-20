from __future__ import annotations

import unittest

import numpy as np

from pontius.incremental_policy_tt import (
    compile_policy_delta_tt_cache,
    compile_policy_probability_tape,
)
from pontius.profiled_policy_tt import (
    profile_policy_delta_tt_cache_from_probabilities,
)
from tests import test_incremental_policy_tt as incremental_fixture


class ProfiledPolicyTTTests(unittest.TestCase):
    def test_profiled_cold_compile_is_numerically_identical(self) -> None:
        fixture_type = incremental_fixture.IncrementalPolicyTTTests
        fixture_type.setUpClass()
        fixture = fixture_type()
        ordinary = compile_policy_delta_tt_cache(
            fixture.layout,
            fixture.belief.hands_by_player,
            fixture.baseline_policy,
            fixture.terminal_trains,
            fixture.terminal_bounds,
            relative_tolerance=1e-12,
            maximum_rank=None,
        )
        probabilities = compile_policy_probability_tape(
            fixture.layout,
            fixture.belief.hands_by_player,
            fixture.baseline_policy,
        )
        profiled = profile_policy_delta_tt_cache_from_probabilities(
            fixture.layout,
            fixture.belief.hands_by_player,
            probabilities,
            fixture.terminal_trains,
            fixture.terminal_bounds,
            relative_tolerance=1e-12,
            maximum_rank=None,
        )
        np.testing.assert_array_equal(
            profiled.cache.root.to_dense(), ordinary.root.to_dense()
        )
        self.assertEqual(
            profiled.node_compose_ms.shape,
            (fixture.layout.public_node_count,),
        )
        self.assertTrue(np.all(profiled.node_compose_ms >= 0.0))
        self.assertGreater(float(np.sum(profiled.node_compose_ms)), 0.0)


if __name__ == "__main__":
    unittest.main()
