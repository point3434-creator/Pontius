from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from pontius.cfr import TabularCFR
from pontius.coalition import (
    assess_multiplayer_candidate,
    evaluate_coalition_threats,
)
from pontius.dependency_tape import CompiledPolicyDeltaTape
from pontius.evaluation import best_response, evaluate_profile
from pontius.multiway_river_context import (
    generate_multiway_river_contexts,
    make_multiway_range_targets,
)
from pontius.multiway_source_tape_audit import (
    _evaluation_error,
    _unique_index,
    parse_source_tape_audit_config,
    primary_reuse_curve,
)


ROOT = Path(__file__).parents[1]
AUDIT_CONFIG = json.loads(
    (
        ROOT
        / "experiments"
        / "configs"
        / "multiway-source-tape-reuse-audit-v1.json"
    ).read_text(encoding="utf-8")
)
SOURCE_CONFIG = json.loads(
    (
        ROOT
        / "experiments"
        / "configs"
        / "multiway-river-search-acceptance-development-v1.json"
    ).read_text(encoding="utf-8")
)


class MultiwaySourceTapeAuditTests(unittest.TestCase):
    def test_frozen_config_parses_and_cannot_expand_scope(self) -> None:
        parsed = parse_source_tape_audit_config(copy.deepcopy(AUDIT_CONFIG))
        self.assertEqual(parsed["included_splits"], ("development",))
        self.assertEqual(parsed["expected_candidate_records"], 1728)
        self.assertEqual(parsed["primary_break_even_maximum_reuses"], 8)

        changed = copy.deepcopy(AUDIT_CONFIG)
        changed["source_outcome_universe"] = "target_union"
        with self.assertRaisesRegex(ValueError, "execution scope"):
            parse_source_tape_audit_config(changed)

        changed = copy.deepcopy(AUDIT_CONFIG)
        changed["included_splits"] = ["development", "validation"]
        with self.assertRaisesRegex(ValueError, "only development"):
            parse_source_tape_audit_config(changed)

        changed = copy.deepcopy(AUDIT_CONFIG)
        changed["post_label_override"] = True
        with self.assertRaisesRegex(ValueError, "fields differ"):
            parse_source_tape_audit_config(changed)

    def test_primary_break_even_curve_charges_compile_by_reuse(self) -> None:
        result = primary_reuse_curve(
            accepted_raw_reduction=15.0,
            blind_raw_reduction=10.0,
            blind_solver_ms=10.0,
            source_compile_ms=4.0,
            targets_per_context=4.0,
            baseline_update_ms=1.0,
            candidate_update_ms=1.0,
            maximum_reuses=8,
        )
        self.assertEqual(result["minimum_winning_reuses"], 6)
        self.assertTrue(result["precompiled_strictly_beats_blind"])
        self.assertEqual(
            result["reuse_curve"][0]["source_compile_charge_ms"],
            16.0,
        )
        self.assertEqual(
            result["reuse_curve"][7]["source_compile_charge_ms"],
            2.0,
        )
        with self.assertRaisesRegex(ValueError, "valid ranges"):
            primary_reuse_curve(
                accepted_raw_reduction=0.0,
                blind_raw_reduction=1.0,
                blind_solver_ms=1.0,
                source_compile_ms=1.0,
                targets_per_context=1.0,
                baseline_update_ms=0.0,
                candidate_update_ms=0.0,
                maximum_reuses=1,
            )

    def test_duplicate_frozen_record_keys_are_rejected(self) -> None:
        rows = [
            {"target_id": "a", "solver": "dcfr", "checkpoint": 2},
            {"target_id": "a", "solver": "dcfr", "checkpoint": 2},
        ]
        with self.assertRaisesRegex(ValueError, "duplicate candidate"):
            _unique_index(
                rows,
                ("target_id", "solver", "checkpoint"),
                "candidate",
            )

    def test_source_relative_range_and_policy_calls_match_exact_controls(self) -> None:
        context = generate_multiway_river_contexts(
            groups=1,
            seed=19,
            hands_per_player=2,
            families=("balanced",),
            splits=("development", "validation", "test"),
            pot_options=(12.0,),
            bet_to_pot_options=(0.5,),
            effective_stack_to_pot=2.0,
            weight_options=(0.5, 1.0, 2.0),
        )[0]
        blueprint_solver = TabularCFR(context.game, variant="dcfr")
        blueprint_solver.run(8)
        blueprint = blueprint_solver.average_strategy()
        targets = make_multiway_range_targets(
            context,
            SOURCE_CONFIG["target_specs"],
        )
        first, second = targets[:2]
        source_tape = CompiledPolicyDeltaTape(context.game, blueprint)

        candidate_solver = TabularCFR(first.game, variant="lcfr")
        candidate_solver.warm_start_from_schema(
            blueprint,
            0.1 * first.game.payoff_span,
            source_tape.policy_input_schema,
        )
        candidate_solver.run(4)
        candidate = candidate_solver.average_strategy()
        first_distribution = dict(first.game.initial_state().chance_outcomes())
        source_result = source_tape.recertify_profile(
            first_distribution,
            candidate,
            mode="dense",
        )
        target_tape = CompiledPolicyDeltaTape(first.game, blueprint)
        target_result = target_tape.recertify_policy(candidate, mode="dense")
        ordinary = evaluate_profile(first.game, candidate)

        self.assertEqual(
            set(first_distribution),
            set(context.game.joint_distribution()),
        )
        self.assertEqual(
            source_tape.policy_input_schema,
            target_tape.policy_input_schema,
        )
        self.assertLessEqual(
            _evaluation_error(source_result.evaluation, ordinary),
            1e-12,
        )
        self.assertLessEqual(
            _evaluation_error(target_result.evaluation, ordinary),
            1e-12,
        )
        reference_actions = tuple(
            best_response(first.game, candidate, player)[1]
            for player in range(first.game.num_players)
        )
        self.assertEqual(source_result.best_response_actions, reference_actions)
        self.assertEqual(target_result.best_response_actions, reference_actions)

        baseline_ordinary = evaluate_profile(first.game, blueprint)
        baseline_source = source_tape.recertify_profile(
            first_distribution,
            blueprint,
            mode="dense",
        ).evaluation
        source_assessment = assess_multiplayer_candidate(
            baseline_source,
            source_result.evaluation,
            evaluate_coalition_threats(first.game, blueprint),
            evaluate_coalition_threats(first.game, candidate),
            payoff_span=first.game.payoff_span,
        )
        ordinary_assessment = assess_multiplayer_candidate(
            baseline_ordinary,
            ordinary,
            evaluate_coalition_threats(first.game, blueprint),
            evaluate_coalition_threats(first.game, candidate),
            payoff_span=first.game.payoff_span,
        )
        self.assertEqual(source_assessment, ordinary_assessment)

        source_tape.recertify_profile(
            dict(second.game.initial_state().chance_outcomes()),
            blueprint,
            mode="dense",
        )
        replay = source_tape.recertify_profile(
            first_distribution,
            candidate,
            mode="dense",
        )
        self.assertEqual(replay.evaluation, source_result.evaluation)
        self.assertEqual(
            replay.best_response_actions,
            source_result.best_response_actions,
        )


if __name__ == "__main__":
    unittest.main()
