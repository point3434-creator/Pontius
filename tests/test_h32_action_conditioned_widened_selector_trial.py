import unittest

from pontius.h32_action_conditioned_widened_selector_trial import (
    build_all_changed_public_node_blocks,
    derive_widened_capacity,
    observed_prefix_history,
    structural_schedule_key,
)


class ActionConditionedWidenedSelectorTests(unittest.TestCase):
    def test_all_changed_infosets_partition_by_actor_and_history(self) -> None:
        blueprint = {
            "p0|hand=AsKd|history=root": {"check": 0.5, "bet": 0.5},
            "p0|hand=AhKh|history=root": {"check": 0.5, "bet": 0.5},
            "p1|hand=QsJd|history=p0:check": {"check": 0.6, "bet": 0.4},
            "p2|hand=9s9d|history=p0:bet/p1:call": {"fold": 0.2, "call": 0.8},
        }
        candidate = {
            **blueprint,
            "p0|hand=AsKd|history=root": {"check": 0.4, "bet": 0.6},
            "p0|hand=AhKh|history=root": {"check": 0.3, "bet": 0.7},
            "p2|hand=9s9d|history=p0:bet/p1:call": {"fold": 0.1, "call": 0.9},
        }
        blocks = build_all_changed_public_node_blocks(blueprint, candidate)
        self.assertEqual(len(blocks), 2)
        self.assertEqual(blocks[0]["acting_seat"], 0)
        self.assertEqual(blocks[0]["information_set_count"], 2)
        self.assertEqual(blocks[1]["public_history"], "p0:bet/p1:call")
        keys = [key for block in blocks for key in block["information_keys"]]
        self.assertEqual(len(keys), len(set(keys)))

    def test_schedule_prefers_observed_continuation_then_distance(self) -> None:
        self.assertEqual(
            observed_prefix_history(2), "p0:check/p1:check/p2:bet"
        )
        descendant = {
            "acting_seat": 5,
            "public_history": "p0:check/p1:check/p2:bet/p3:call/p4:call",
        }
        near_ancestor = {
            "acting_seat": 0,
            "public_history": "p0:check/p1:check",
        }
        remote = {"acting_seat": 0, "public_history": "p0:bet"}
        self.assertLess(
            structural_schedule_key(descendant, observed_bettor=2),
            structural_schedule_key(near_ancestor, observed_bettor=2),
        )
        self.assertLess(
            structural_schedule_key(near_ancestor, observed_bettor=2),
            structural_schedule_key(remote, observed_bettor=2),
        )

    def test_capacity_charges_no_tier_a_prefilter(self) -> None:
        rows = [
            {
                "timing": {
                    "complete_tier_b_candidate_ms": value,
                    "envelope_ms": 5.0,
                }
            }
            for value in (100.0, 200.0, 150.0, 175.0)
        ]
        capacity = derive_widened_capacity(
            rows,
            warm_step_ms=1000.0,
            street_budget_ms=2000.0,
            emission_reserve_ms=200.0,
        )
        self.assertEqual(capacity["clock_feasible_k"], 3)
        self.assertFalse(capacity["tier_a_filter_used"])
        self.assertFalse(capacity["library_limited"])


if __name__ == "__main__":
    unittest.main()
