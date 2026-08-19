from __future__ import annotations

import json
import unittest
from pathlib import Path

from pontius.river_noop_full_replication import (
    _candidate_record,
    _helper_config,
    _replication_gates,
    _validate_config,
    _validate_rule,
    choose_rule_arm,
)
from pontius.evaluation import evaluate_profile
from pontius.river_context import generate_river_contexts
from pontius.river_selective import complete_information_schema
from pontius.river_selective_experiment import _range_targets, _wide_game


class RiverNoopFullReplicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(
            Path(
                "experiments/configs/river-noop-full-gate-replication-v1.json"
            ).read_text(encoding="utf-8")
        )
        cls.rule = json.loads(
            Path("experiments/rules/river-noop-full-gate-v1.json").read_text(
                encoding="utf-8"
            )
        )

    def test_frozen_config_and_rule_parse_exactly(self) -> None:
        parsed = _validate_config(self.config)
        decision = _validate_rule(self.rule, parsed)
        self.assertEqual(parsed["requested_groups"], 36)
        self.assertEqual(parsed["included_splits"], ("development",))
        self.assertEqual(decision["threshold"], 0.14835164835164835)

    def test_rule_uses_conservative_equality_tie(self) -> None:
        parsed = _validate_config(self.config)
        decision = _validate_rule(self.rule, parsed)
        threshold = float(decision["threshold"])
        self.assertEqual(choose_rule_arm(0.0, decision), "no_op")
        self.assertEqual(choose_rule_arm(threshold, decision), "no_op")
        self.assertEqual(choose_rule_arm(threshold + 1e-15, decision), "b3r2")
        with self.assertRaisesRegex(ValueError, r"\[0, 1\]"):
            choose_rule_arm(-0.1, decision)

    def test_post_freeze_seed_threshold_and_split_changes_are_rejected(self) -> None:
        for field, value in (
            ("seed", 1),
            ("requested_groups", 35),
            ("included_splits", ["development", "validation"]),
        ):
            changed = dict(self.config)
            changed[field] = value
            with self.assertRaises(ValueError):
                _validate_config(changed)

        parsed = _validate_config(self.config)
        changed_rule = json.loads(json.dumps(self.rule))
        changed_rule["decision"]["threshold"] = 0.2
        with self.assertRaisesRegex(ValueError, "decision changed"):
            _validate_rule(changed_rule, parsed)

    def test_gate_calculation_requires_joint_quality_transfer_and_arm_use(self) -> None:
        parsed = _validate_config(self.config)
        fixed = {
            "raw_reduction": 10.0,
            "normalized_reduction": 1.0,
            "state_visits": 100,
            "raw_reduction_per_millisecond": 0.001,
            "maximum_target_harm": 2.0,
            "group_raw_reduction": {"g0": 4.0, "g1": 3.0, "g2": 3.0},
        }
        selected = {
            "raw_reduction": 12.0,
            "normalized_reduction": 1.2,
            "state_visits": 60,
            "raw_reduction_per_millisecond": 0.002,
            "maximum_target_harm": 1.0,
            "group_raw_reduction": {"g0": 5.0, "g1": 4.0, "g2": 3.5},
            "selection_counts": {"no_op": 4, "b3r2": 6},
            "targets": 10,
        }
        oracle = {"raw_reduction": 14.0}
        blueprints = [
            {
                "quality_threshold_passed": True,
                "source_normalized_nash_conv": 1e-6,
            }
        ]
        freshness = {
            "discovery_board_overlap": 0,
            "discovery_full_range_overlap": 0,
            "all_returned_contexts_are_development": True,
            "development_only_requested": True,
        }
        results, diagnostics = _replication_gates(
            parsed=parsed,
            group_count=20,
            blueprint_records=blueprints,
            fixed=fixed,
            selected=selected,
            compact_oracle=oracle,
            freshness=freshness,
        )
        self.assertTrue(all(results.values()))
        self.assertEqual(diagnostics["positive_raw_uplift_group_fraction"], 1.0)
        self.assertEqual(
            diagnostics["compact_oracle_opportunity_capture_fraction"],
            0.5,
        )

        selected["normalized_reduction"] = 0.9
        results, _ = _replication_gates(
            parsed=parsed,
            group_count=20,
            blueprint_records=blueprints,
            fixed=fixed,
            selected=selected,
            compact_oracle=oracle,
            freshness=freshness,
        )
        self.assertFalse(
            results["aggregate_normalized_reduction_strictly_beats_fixed_b3r2"]
        )

    def test_candidate_measurement_uses_wide_payoff_span_and_respects_work(self) -> None:
        parsed = _validate_config(self.config)
        helper = _helper_config(parsed)
        context = generate_river_contexts(
            groups=1,
            seed=3,
            hands_per_player=3,
            families=("balanced",),
            splits=("development", "validation", "test"),
            sequential_raise=False,
        )[0]
        source = _wide_game(context.game, helper)
        source_schema = complete_information_schema(source)
        blueprint = {
            key: {action: 1.0 / len(actions) for action in actions}
            for key, actions in source_schema.items()
        }
        _, _, range_target, _ = _range_targets(context.game, helper)[0]
        target = _wide_game(range_target, helper)
        target_schema = complete_information_schema(target)
        baseline = evaluate_profile(target, blueprint)
        full_mask = next(
            mask for mask in parsed["candidate_masks"] if mask["name"] == "b3r2"
        )
        record = _candidate_record(
            target=target,
            blueprint=blueprint,
            baseline_nash_conv=baseline.nash_conv,
            target_schema=target_schema,
            mask_config=full_mask,
            parsed=parsed,
        )
        self.assertEqual(record["cutoff_states"], 0)
        self.assertLessEqual(record["actual_state_visits"], record["state_visit_budget"])
        self.assertAlmostEqual(
            record["normalized_reduction"],
            record["raw_reduction"] / target.payoff_span,
        )


if __name__ == "__main__":
    unittest.main()
