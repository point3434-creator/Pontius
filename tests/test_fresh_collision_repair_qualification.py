from __future__ import annotations

import ast
import unittest
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pontius.fresh_collision_repair_qualification as qualification_module
from pontius.fresh_collision_repair_qualification import (
    ADR0302_CAMPAIGN_SHA256,
    ADR0302_CHIP_OBJECTIVE_ALLOWANCE,
    ADR0302_ENVELOPE_ALLOWANCE,
    ADR0302_LP_DUALITY_ALLOWANCE,
    ADR0302_OPENED_CONTEXT_COUNT,
    ADR0302_PROBABILITY_ALLOWANCE,
    ADR0302_QUALIFICATION_RESULT_SHA256,
    ADR0302_QUALIFIED_CONTEXT_COUNT,
    ADR0302_QUALIFIED_INDICES,
    ADR0302_QUALIFIED_PANEL_SHA256,
    ADR0302_SIMPLEX_PIVOT_CAP,
    ADR0302_TEACHER_CONTROL_SHA256,
    FreshTeacherControl,
    bind_fresh_context_to_oracle,
    build_adr0302_qualified_panel,
    run_adr0302_fresh_qualification,
)
from pontius.fresh_collision_repair_structures import (
    FreshStructureKind,
    build_adr0301_fresh_structure,
)
from pontius.sizing_power_diagnostic import (
    QualificationStopReason,
    SizingPowerClassification,
)

_ROOT = Path(__file__).parents[1]


def _fake_solution(value_chips: float) -> SimpleNamespace:
    return SimpleNamespace(
        value_chips=value_chips,
        max_probability_simplex_residual=0.0,
        chip_objective_reconstruction_error=0.0,
        linear_program_duality_gap=0.0,
        max_envelope_constraint_violation_chips=0.0,
        simplex_pivots=0,
    )


def _qualifying_solver(
    _context: object,
    sizes: tuple[int, ...],
    **_kwargs: object,
) -> SimpleNamespace:
    return _fake_solution(1.0 if len(sizes) > 2 else 0.0)


class FreshCollisionRepairQualificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.pool = build_adr0301_fresh_structure(
            kind=FreshStructureKind.QUALIFIED_POOL
        )
        cls.campaign = run_adr0302_fresh_qualification()

    def test_owned_candidate_blind_qualification_reproduces_frozen_pass(self) -> None:
        campaign = self.campaign
        result = campaign.qualification
        self.assertTrue(campaign.passed)
        self.assertGreater(campaign.elapsed_seconds, 0.0)
        self.assertIs(result.stop_reason, QualificationStopReason.TARGET_REACHED)
        self.assertEqual(result.opened_context_count, ADR0302_OPENED_CONTEXT_COUNT)
        self.assertEqual(result.qualified_indices, ADR0302_QUALIFIED_INDICES)
        self.assertEqual(len(result.qualified_indices), ADR0302_QUALIFIED_CONTEXT_COUNT)
        self.assertEqual(result.digest, ADR0302_QUALIFICATION_RESULT_SHA256)
        self.assertEqual(campaign.digest, ADR0302_CAMPAIGN_SHA256)
        result.verify_against_pool(pool=self.pool)

        panel = result.qualified_panel(pool=self.pool)
        self.assertEqual(panel.digest, ADR0302_QUALIFIED_PANEL_SHA256)
        self.assertEqual(panel, build_adr0302_qualified_panel())
        control = campaign.teacher_control
        assert control is not None
        self.assertEqual(control.digest, ADR0302_TEACHER_CONTROL_SHA256)
        control.verify_against_pool(pool=self.pool, result=result)

        classifications = tuple(
            observation.classification for observation in result.observations
        )
        self.assertEqual(
            classifications.count(SizingPowerClassification.QUALIFYING),
            24,
        )
        self.assertEqual(
            classifications.count(SizingPowerClassification.NONQUALIFYING),
            36,
        )
        self.assertNotIn(SizingPowerClassification.AMBIGUOUS, classifications)
        threshold_distances = tuple(
            abs(
                observation.full_value_chips
                - observation.narrow_value_chips
                - 1e-4 * observation.payoff_span
            )
            for observation in result.observations
        )
        self.assertGreater(min(threshold_distances), 1e-8)

        selected = tuple(
            self.pool.contexts[index] for index in result.qualified_indices
        )
        self.assertEqual(len({context.pot for context in selected}), 10)
        self.assertEqual(len({context.stack for context in selected}), 6)
        self.assertEqual(len({context.showdown_signs for context in selected}), 24)

        for observation in result.observations:
            context = self.pool.contexts[observation.context_index]
            self.assertEqual(
                observation.full_bet_sizes,
                tuple(range(context.minimum_bet, context.stack + 1)),
            )
            self.assertEqual(
                observation.narrow_bet_sizes,
                (context.minimum_bet, context.stack),
            )
            self.assertEqual(
                observation.full_dimensions.variable_count,
                8 * context.stack - 4,
            )
            self.assertEqual(
                observation.full_dimensions.inequality_count,
                8 * context.stack,
            )
            self.assertEqual(observation.narrow_dimensions.variable_count, 20)
            self.assertEqual(observation.narrow_dimensions.inequality_count, 24)
            self.assertLessEqual(
                observation.max_probability_residual,
                ADR0302_PROBABILITY_ALLOWANCE.value,
            )
            self.assertLessEqual(
                observation.max_chip_objective_error,
                ADR0302_CHIP_OBJECTIVE_ALLOWANCE.chips,
            )
            self.assertLessEqual(
                observation.max_lp_duality_gap_chips,
                ADR0302_LP_DUALITY_ALLOWANCE.chips,
            )
            self.assertLessEqual(
                observation.max_envelope_violation_chips,
                ADR0302_ENVELOPE_ALLOWANCE.chips,
            )
            self.assertLessEqual(
                observation.full_simplex_pivots,
                ADR0302_SIMPLEX_PIVOT_CAP,
            )
            self.assertLessEqual(
                observation.narrow_simplex_pivots,
                ADR0302_SIMPLEX_PIVOT_CAP,
            )

        self.assertEqual(len(control.observations), 24)
        self.assertTrue(
            all(
                observation.teacher_opener_pure_plan_count == 9
                and observation.teacher_responder_pure_plan_count == 16
                for observation in control.observations
            )
        )

    def test_structural_to_oracle_binding_is_exact_unique_and_fail_closed(self) -> None:
        bindings = tuple(
            bind_fresh_context_to_oracle(context) for context in self.pool.contexts
        )
        self.assertEqual(len({binding.digest for binding in bindings}), len(bindings))
        for binding in bindings:
            structural = binding.structural_context
            oracle = binding.oracle_context
            self.assertEqual(structural.context_id, oracle.context_id)
            self.assertEqual(structural.board, oracle.board)
            self.assertEqual(structural.pot, oracle.pot)
            self.assertEqual(structural.stack, oracle.stack)
            self.assertEqual(structural.minimum_bet, oracle.minimum_bet)
            self.assertEqual(structural.opener_hands, oracle.opener_hands)
            self.assertEqual(structural.responder_hands, oracle.responder_hands)
            self.assertEqual(structural.payoff_span, oracle.payoff_span)
            self.assertEqual(structural.showdown_signs, oracle.showdown_signs)
            self.assertEqual(
                tuple(
                    tuple((p.numerator, p.denominator) for p in row)
                    for row in structural.joint_probabilities
                ),
                tuple(
                    tuple((p.numerator, p.denominator) for p in row)
                    for row in oracle.joint_probabilities
                ),
            )

        first = bindings[0]
        replacement_pot = 8 if first.oracle_context.pot != 8 else 10
        changed_oracle = replace(first.oracle_context, pot=replacement_pot)
        with self.assertRaisesRegex(ValueError, "changed a field"):
            replace(first, oracle_context=changed_oracle)
        with self.assertRaisesRegex(TypeError, "structural context"):
            bind_fresh_context_to_oracle("context")  # type: ignore[arg-type]

    def test_runner_owns_immediate_target_and_ambiguity_stops(self) -> None:
        with patch.object(
            qualification_module,
            "solve_reduced_river_sizing",
            side_effect=_qualifying_solver,
        ) as solver:
            result = qualification_module._run_qualification(pool=self.pool)
        self.assertIs(result.stop_reason, QualificationStopReason.TARGET_REACHED)
        self.assertEqual(result.opened_context_count, 24)
        self.assertEqual(result.qualified_indices, tuple(range(24)))
        self.assertEqual(solver.call_count, 48)

        with (
            patch.object(
                qualification_module,
                "solve_reduced_river_sizing",
                side_effect=_qualifying_solver,
            ) as solver,
            patch.object(
                qualification_module,
                "classify_sizing_opportunity",
                return_value=SizingPowerClassification.AMBIGUOUS,
            ),
        ):
            result = qualification_module._run_qualification(pool=self.pool)
        self.assertIs(result.stop_reason, QualificationStopReason.AMBIGUOUS)
        self.assertEqual(result.opened_context_count, 1)
        self.assertEqual(result.qualified_indices, ())
        self.assertEqual(solver.call_count, 2)

    def test_result_arm_teacher_and_campaign_mutations_fail_closed(self) -> None:
        result = self.campaign.qualification
        first = result.observations[0]
        forged_first = replace(first, full_bet_sizes=first.full_bet_sizes[1:])
        forged = replace(
            result,
            observations=(forged_first, *result.observations[1:]),
        )
        with self.assertRaisesRegex(ValueError, "full arm"):
            forged.verify_against_pool(pool=self.pool)

        control = self.campaign.teacher_control
        assert control is not None
        teacher_first = control.observations[0]
        forged_teacher_first = replace(
            teacher_first,
            bounded_context_digest="0" * 64,
        )
        forged_control = replace(
            control,
            observations=(forged_teacher_first, *control.observations[1:]),
        )
        with self.assertRaisesRegex(ValueError, "bounded context"):
            forged_control.verify_against_pool(pool=self.pool, result=result)

        wrong_panel_control = replace(control, panel_digest="0" * 64)
        self.assertIsInstance(wrong_panel_control, FreshTeacherControl)
        with self.assertRaisesRegex(ValueError, "wrong panel"):
            replace(self.campaign, teacher_control=wrong_panel_control)

    def test_source_and_value_free_panel_rebuilder_are_candidate_blind(self) -> None:
        path = _ROOT / "src/pontius/fresh_collision_repair_qualification.py"
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        imports = tuple(
            (node.module, tuple(alias.name for alias in node.names))
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module is not None
        )
        imported_modules = {module for module, _names in imports}
        imported_names = {name for _module, names in imports for name in names}
        self.assertNotIn("collision_repair_action_abstraction", imported_modules)
        self.assertNotIn("legal_action_abstraction", imported_modules)
        self.assertNotIn("CollisionRepairActionAbstractionSource", imported_names)
        self.assertNotIn("FreshStructureKind.REPRESENTATIVE", source)

        rebuilder = next(
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef)
            and node.name == "build_adr0302_qualified_panel"
        )
        called_names = {
            node.func.id
            for node in ast.walk(rebuilder)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        self.assertNotIn("solve_reduced_river_sizing", called_names)
        self.assertNotIn("solve_bounded_normal_form_sizing_teacher", called_names)


if __name__ == "__main__":
    unittest.main()
