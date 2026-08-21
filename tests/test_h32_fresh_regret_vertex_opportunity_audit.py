from __future__ import annotations

import json
from pathlib import Path
import unittest

from pontius.h32_fresh_regret_vertex_opportunity_audit import (
    block_regret_opportunity_proxy,
    build_regret_vertex_candidate,
    exact_discrete_convex_scale_search,
    parse_h32_fresh_regret_vertex_opportunity_config,
    recover_iteration_one_dcfr_regret_deltas,
    search_invariants,
    spearman_rank_correlation,
)


_ROOT = Path(__file__).parents[1]
_CONFIG = _ROOT / "experiments/configs/h32-fresh-regret-vertex-opportunity-v1.json"


class H32FreshRegretVertexOpportunityAuditTests(unittest.TestCase):
    def test_contract_rejects_target_direction_search_parent_and_gate_mutations(self) -> None:
        config = json.loads(_CONFIG.read_text(encoding="utf-8"))
        parsed = parse_h32_fresh_regret_vertex_opportunity_config(config)
        self.assertEqual(len(parsed["targets"]), 6)
        self.assertEqual(parsed["direction_families"], ("soft_dcfr", "regret_vertex"))

        mutated = json.loads(json.dumps(config))
        mutated["targets"][0]["target_belief_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "workload differs"):
            parse_h32_fresh_regret_vertex_opportunity_config(mutated)

        mutated = json.loads(json.dumps(config))
        mutated["direction_families"].reverse()
        with self.assertRaisesRegex(ValueError, "workload differs"):
            parse_h32_fresh_regret_vertex_opportunity_config(mutated)

        mutated = dict(config)
        mutated["objective_search"] = "outcome_tuned"
        with self.assertRaisesRegex(ValueError, "workload differs"):
            parse_h32_fresh_regret_vertex_opportunity_config(mutated)

        mutated = dict(config)
        mutated["expected_parent_result_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "source mismatch"):
            parse_h32_fresh_regret_vertex_opportunity_config(mutated)

        mutated = json.loads(json.dumps(config))
        mutated["gates"]["maximum_queries_per_direction"] = 34
        with self.assertRaisesRegex(ValueError, "gates differ"):
            parse_h32_fresh_regret_vertex_opportunity_config(mutated)

    def test_iteration_one_regret_recovery_inverts_common_half_discount(self) -> None:
        blueprint = {"k": {"a": 0.25, "b": 0.75}}
        warm_mass = 4.0
        instantaneous = {"a": 0.5, "b": -0.25}
        post = {
            "k": {
                action: 0.5 * (warm_mass * blueprint["k"][action] + instantaneous[action])
                for action in blueprint["k"]
            }
        }
        recovered = recover_iteration_one_dcfr_regret_deltas(
            blueprint, post, warm_regret_mass=warm_mass
        )
        self.assertAlmostEqual(recovered["k"]["a"], 0.5)
        self.assertAlmostEqual(recovered["k"]["b"], -0.25)

    def test_vertex_uses_per_infoset_first_action_tie_break(self) -> None:
        blueprint = {
            "k1": {"a": 0.4, "b": 0.6},
            "k2": {"a": 0.7, "b": 0.3},
        }
        deltas = {
            "k1": {"a": 2.0, "b": 1.0},
            "k2": {"a": 3.0, "b": 3.0},
        }
        vertex = build_regret_vertex_candidate(blueprint, deltas, ["k1", "k2"])
        self.assertEqual(vertex["k1"], {"a": 1.0, "b": 0.0})
        self.assertEqual(vertex["k2"], {"a": 1.0, "b": 0.0})
        proxy = block_regret_opportunity_proxy(
            blueprint, deltas, ["k1", "k2"], payoff_span=10.0
        )
        self.assertEqual(proxy["positive_best_action_regret_mass"], 5.0)
        self.assertEqual(proxy["regret_span_mass"], 1.0)
        self.assertEqual(proxy["vertex_action_counts"], {"a": 2})

    def test_exact_search_finds_every_complete_boundary_and_unimodal_optimum(self) -> None:
        maximum_queries = 0
        for boundary in range(34):
            for optimum in range(boundary, 34):
                def evaluate(index: int, boundary: int = boundary, optimum: int = optimum) -> dict:
                    complete = index >= boundary
                    return {
                        "scale_index": index,
                        "certificate": {
                            "complete": complete,
                            "quality": None if not complete else {"nash_conv": float((index - optimum) ** 2)},
                        },
                    }

                search = exact_discrete_convex_scale_search(evaluate, scale_count=34)
                self.assertEqual(search["largest_complete_scale_index"], boundary)
                self.assertEqual(search["best_complete_scale_index"], optimum)
                self.assertTrue(search_invariants(search, scale_count=34))
                maximum_queries = max(maximum_queries, search["query_count"])
        self.assertLessEqual(maximum_queries, 16)

    def test_exact_search_fails_closed_when_floor_is_not_complete(self) -> None:
        def evaluate(index: int) -> dict:
            return {
                "scale_index": index,
                "certificate": {"complete": False, "quality": None},
            }

        search = exact_discrete_convex_scale_search(evaluate, scale_count=34)
        self.assertIsNone(search["largest_complete_scale_index"])
        self.assertIsNone(search["best_complete_scale_index"])
        self.assertEqual(search["query_order"], [0, 33])
        self.assertTrue(search_invariants(search, scale_count=34))

    def test_spearman_uses_average_ranks_and_handles_constants(self) -> None:
        self.assertAlmostEqual(
            spearman_rank_correlation([1.0, 2.0, 3.0], [10.0, 20.0, 30.0]),
            1.0,
        )
        self.assertAlmostEqual(
            spearman_rank_correlation([1.0, 2.0, 3.0], [30.0, 20.0, 10.0]),
            -1.0,
        )
        self.assertIsNone(spearman_rank_correlation([1.0, 1.0], [2.0, 3.0]))


if __name__ == "__main__":
    unittest.main()
