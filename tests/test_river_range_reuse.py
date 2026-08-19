from __future__ import annotations

import unittest

from pontius.river_context import generate_river_contexts
from pontius.river_range_reuse import (
    make_blocker_perturbation,
    run_river_range_reuse_experiment,
)


class RiverRangeReuseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = {
            "groups": 4,
            "seed": 5,
            "hands_per_player": 3,
            "families": ["balanced"],
            "included_splits": ["development"],
            "sequential_raise": True,
            "perturbations": [
                {
                    "name": "p0_shift",
                    "player": 0,
                    "root_tv_budget": 0.01,
                    "maximum_donor_fraction": 0.75,
                }
            ],
            "solver": "dcfr",
            "checkpoints": [0, 1, 2],
            "warm_start_regret_mass_by_payoff_span": [0.01, 0.1],
            "certification_normalized_exploitability_thresholds": [0.01, 0.02],
            "primary_checkpoint": 2,
            "folds": 2,
            "minimum_cold_residual_capture": 0.01,
        }
        cls.result = run_river_range_reuse_experiment(cls.config)

    def test_blocker_perturbation_preserves_support_but_not_provenance(self) -> None:
        context = generate_river_contexts(
            groups=1,
            seed=5,
            hands_per_player=3,
            families=("balanced",),
            splits=("development",),
            sequential_raise=True,
        )[0]
        target, metadata = make_blocker_perturbation(
            context.game,
            player=0,
            root_tv_budget=0.01,
            maximum_donor_fraction=0.75,
        )

        self.assertEqual(context.game.structural_digest, target.structural_digest)
        self.assertNotEqual(context.game.provenance_digest, target.provenance_digest)
        self.assertTrue(metadata["support_preserved"])
        self.assertTrue(metadata["selected_private_hand_marginal_preserved"])
        self.assertLessEqual(metadata["actual_root_joint_total_variation"], 0.01 + 1e-12)
        self.assertGreater(metadata["selected_conditional_total_variation"], 0.0)

    def test_experiment_enforces_cache_identity_and_separates_costs(self) -> None:
        self.assertEqual(
            self.result["experiment_type"],
            "exact_river_range_reuse_and_recertification",
        )
        self.assertTrue(
            self.result["safety_contract"][
                "exact_provenance_required_for_direct_strategy_deployment"
            ]
        )
        self.assertGreater(self.result["counts"]["range_pairs"], 0)
        self.assertEqual(self.result["counts"]["arms_per_pair"], 3)
        for pair in self.result["pairs"]:
            self.assertEqual(pair["reuse_assessment"]["match"], "structural_only")
            self.assertFalse(
                pair["reuse_assessment"]["direct_strategy_deployable"]
            )
            self.assertGreaterEqual(
                pair["timing"]["stale_exact_recertification_milliseconds"],
                0.0,
            )
        self.assertTrue(
            all(
                row["bound_false_positives"] == 0
                for row in self.result["tv_certificate_summary"]
            )
        )

    def test_cached_schema_warm_start_has_matched_solver_state_work(self) -> None:
        by_key = {
            (row["target_id"], row["arm"], row["checkpoint"]): row
            for row in self.result["records"]
        }
        warm_arm = "warm_span_0_01"
        for pair in self.result["pairs"]:
            target = pair["target_id"]
            cold = by_key[(target, "cold", 2)]
            warm = by_key[(target, warm_arm, 2)]
            stale = by_key[(target, warm_arm, 0)]
            self.assertEqual(warm["state_visits"], cold["state_visits"])
            self.assertGreater(warm["cached_schema_entries"], 0)
            self.assertAlmostEqual(
                stale["exploitability"],
                pair["stale_policy_target_exploitability"],
            )

    def test_reserved_splits_and_unknown_fields_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "development-only"):
            run_river_range_reuse_experiment(
                {**self.config, "included_splits": ["validation"]}
            )
        with self.assertRaisesRegex(ValueError, "unknown"):
            run_river_range_reuse_experiment({**self.config, "future_label": 1})


if __name__ == "__main__":
    unittest.main()
