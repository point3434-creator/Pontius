from __future__ import annotations

import ast
import unittest
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pontius.fresh_capacity_filling_qualification as qualification_module
from pontius.fresh_capacity_filling_qualification import (
    ADR0305_V4_QUALIFICATION_CHIP_OBJECTIVE_ALLOWANCE,
    ADR0305_V4_QUALIFICATION_ENVELOPE_ALLOWANCE,
    ADR0305_V4_QUALIFICATION_LP_DUALITY_ALLOWANCE,
    ADR0305_V4_QUALIFICATION_PROBABILITY_ALLOWANCE,
    ADR0305_V4_QUALIFICATION_SIMPLEX_PIVOT_CAP,
    ADR0310_QUALIFIED_A_CAMPAIGN_SHA256,
    ADR0310_QUALIFIED_A_INDICES,
    ADR0310_QUALIFIED_A_OPENED_CONTEXT_COUNT,
    ADR0310_QUALIFIED_A_PROVISIONAL_PANEL_SHA256,
    ADR0310_QUALIFIED_A_RESULT_SHA256,
    ADR0310_QUALIFIED_A_TEACHER_CONTROL_SHA256,
    ADR0310_QUALIFIED_B_COMPLETED_CONTEXT_COUNT,
    ADR0310_QUALIFIED_B_COMPLETED_INDICES,
    ADR0310_QUALIFIED_B_COMPLETED_QUALIFYING_INDICES,
    ADR0310_QUALIFIED_B_FAILURE_CONTEXT_INDEX,
    ADR0310_QUALIFIED_B_FAILURE_SHA256,
    CapacityFillingQualificationArm,
    CapacityFillingQualificationCampaignResult,
    CapacityFillingQualificationNumericalFailure,
    bind_capacity_filling_context_to_oracle,
    run_adr0305_v4_qualified_a,
    run_adr0305_v4_qualified_b,
)
from pontius.fresh_capacity_filling_structures import (
    CapacityFillingStructureKind,
    build_adr0305_v4_structure,
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


def _nonqualifying_solver(
    _context: object,
    _sizes: tuple[int, ...],
    **_kwargs: object,
) -> SimpleNamespace:
    return _fake_solution(0.0)


class FreshCapacityFillingQualificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.pool_a = build_adr0305_v4_structure(kind=CapacityFillingStructureKind.QUALIFIED_A)
        cls.pool_b = build_adr0305_v4_structure(kind=CapacityFillingStructureKind.QUALIFIED_B)
        cls.campaign_a = run_adr0305_v4_qualified_a()
        try:
            run_adr0305_v4_qualified_b(qualified_a=cls.campaign_a)
        except CapacityFillingQualificationNumericalFailure as failure:
            cls.failure_b = failure
        else:
            raise AssertionError("ADR-0310 qualified B unexpectedly passed")

    def test_qualified_a_reproduces_frozen_provisional_pass(self) -> None:
        campaign = self.campaign_a
        result = campaign.qualification
        self.assertTrue(campaign.passed)
        self.assertGreater(campaign.elapsed_seconds, 0.0)
        self.assertIs(result.stop_reason, QualificationStopReason.TARGET_REACHED)
        self.assertEqual(
            result.opened_context_count,
            ADR0310_QUALIFIED_A_OPENED_CONTEXT_COUNT,
        )
        self.assertEqual(result.qualified_indices, ADR0310_QUALIFIED_A_INDICES)
        self.assertEqual(result.digest, ADR0310_QUALIFIED_A_RESULT_SHA256)
        self.assertEqual(campaign.digest, ADR0310_QUALIFIED_A_CAMPAIGN_SHA256)
        campaign.verify_against_pool(pool=self.pool_a)

        panel = result.qualified_panel(pool=self.pool_a)
        self.assertEqual(
            panel.digest,
            ADR0310_QUALIFIED_A_PROVISIONAL_PANEL_SHA256,
        )
        control = campaign.teacher_control
        assert control is not None
        self.assertEqual(
            control.digest,
            ADR0310_QUALIFIED_A_TEACHER_CONTROL_SHA256,
        )
        control.verify_against_pool(pool=self.pool_a, result=result)

        classifications = tuple(observation.classification for observation in result.observations)
        self.assertEqual(
            classifications.count(SizingPowerClassification.QUALIFYING),
            24,
        )
        self.assertEqual(
            classifications.count(SizingPowerClassification.NONQUALIFYING),
            49,
        )
        self.assertNotIn(SizingPowerClassification.AMBIGUOUS, classifications)
        self.assertGreater(
            min(
                abs(
                    observation.full_value_chips
                    - observation.narrow_value_chips
                    - 1e-4 * observation.payoff_span
                )
                for observation in result.observations
            ),
            1e-8,
        )

        selected = tuple(self.pool_a.contexts[index] for index in result.qualified_indices)
        self.assertEqual(len({context.pot for context in selected}), 10)
        self.assertEqual(len({context.stack for context in selected}), 5)
        self.assertEqual(len({context.showdown_signs for context in selected}), 24)

        for observation in result.observations:
            context = self.pool_a.contexts[observation.context_index]
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
                ADR0305_V4_QUALIFICATION_PROBABILITY_ALLOWANCE.value,
            )
            self.assertLessEqual(
                observation.max_chip_objective_error,
                ADR0305_V4_QUALIFICATION_CHIP_OBJECTIVE_ALLOWANCE.chips,
            )
            self.assertLessEqual(
                observation.max_lp_duality_gap_chips,
                ADR0305_V4_QUALIFICATION_LP_DUALITY_ALLOWANCE.chips,
            )
            self.assertLessEqual(
                observation.max_envelope_violation_chips,
                ADR0305_V4_QUALIFICATION_ENVELOPE_ALLOWANCE.chips,
            )
            self.assertLessEqual(
                observation.full_simplex_pivots,
                ADR0305_V4_QUALIFICATION_SIMPLEX_PIVOT_CAP,
            )
            self.assertLessEqual(
                observation.narrow_simplex_pivots,
                ADR0305_V4_QUALIFICATION_SIMPLEX_PIVOT_CAP,
            )

        self.assertEqual(len(control.observations), 24)
        self.assertTrue(
            all(
                observation.teacher_opener_pure_plan_count == 9
                and observation.teacher_responder_pure_plan_count == 16
                for observation in control.observations
            )
        )

    def test_qualified_b_reproduces_digest_bound_numerical_stop(self) -> None:
        failure = self.failure_b
        self.assertIs(
            failure.pool_kind,
            CapacityFillingStructureKind.QUALIFIED_B,
        )
        self.assertEqual(failure.digest, ADR0310_QUALIFIED_B_FAILURE_SHA256)
        self.assertEqual(
            failure.context_index,
            ADR0310_QUALIFIED_B_FAILURE_CONTEXT_INDEX,
        )
        self.assertEqual(
            failure.completed_context_count,
            ADR0310_QUALIFIED_B_COMPLETED_CONTEXT_COUNT,
        )
        self.assertEqual(
            tuple(observation.context_index for observation in failure.completed_observations),
            ADR0310_QUALIFIED_B_COMPLETED_INDICES,
        )
        self.assertEqual(
            failure.completed_qualified_indices,
            ADR0310_QUALIFIED_B_COMPLETED_QUALIFYING_INDICES,
        )
        self.assertEqual(failure.solver_call_number, 43)
        self.assertIs(
            failure.arm,
            CapacityFillingQualificationArm.FULL_INTEGER,
        )
        self.assertEqual(failure.cause_type, "AssertionError")
        self.assertEqual(
            failure.cause_message,
            "linear-program solution fails primal verification",
        )

        context = self.pool_b.contexts[ADR0310_QUALIFIED_B_FAILURE_CONTEXT_INDEX]
        binding = bind_capacity_filling_context_to_oracle(context)
        self.assertEqual(failure.structural_context_digest, binding.structural_context_digest)
        self.assertEqual(failure.oracle_context_digest, binding.oracle_context.digest)
        self.assertEqual(failure.binding_digest, binding.digest)
        self.assertEqual(failure.bet_sizes, tuple(range(2, 31)))
        self.assertEqual(failure.dimensions.variable_count, 236)
        self.assertEqual(failure.dimensions.inequality_count, 240)
        self.assertEqual(context.pot, 24)
        self.assertEqual(context.stack, 30)
        self.assertEqual(context.payoff_span, 84)
        self.assertEqual(
            sum(
                observation.classification is SizingPowerClassification.NONQUALIFYING
                for observation in failure.completed_observations
            ),
            10,
        )
        self.assertNotIn(
            SizingPowerClassification.AMBIGUOUS,
            tuple(observation.classification for observation in failure.completed_observations),
        )

    def test_conversion_is_exact_unique_and_fail_closed(self) -> None:
        for pool in (self.pool_a, self.pool_b):
            bindings = tuple(
                bind_capacity_filling_context_to_oracle(context) for context in pool.contexts
            )
            self.assertEqual(len({binding.digest for binding in bindings}), 96)
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

        first = bind_capacity_filling_context_to_oracle(self.pool_a.contexts[0])
        changed_oracle = replace(first.oracle_context, pot=first.oracle_context.pot + 2)
        with self.assertRaisesRegex(ValueError, "changed a context field"):
            replace(first, oracle_context=changed_oracle)
        with self.assertRaisesRegex(TypeError, "structural context"):
            bind_capacity_filling_context_to_oracle("context")  # type: ignore[arg-type]

    def test_runner_owns_target_ambiguity_numerical_and_family_stops(self) -> None:
        with patch.object(
            qualification_module,
            "solve_reduced_river_sizing",
            side_effect=_qualifying_solver,
        ) as solver:
            result = qualification_module._run_qualification(pool=self.pool_a)
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
            result = qualification_module._run_qualification(pool=self.pool_a)
        self.assertIs(result.stop_reason, QualificationStopReason.AMBIGUOUS)
        self.assertEqual(result.opened_context_count, 1)
        self.assertEqual(result.qualified_indices, ())
        self.assertEqual(solver.call_count, 2)

        with (
            patch.object(
                qualification_module,
                "solve_reduced_river_sizing",
                side_effect=RuntimeError("mock numerical failure"),
            ) as solver,
            self.assertRaises(CapacityFillingQualificationNumericalFailure) as caught,
        ):
            qualification_module._run_qualification(pool=self.pool_a)
        self.assertEqual(solver.call_count, 1)
        self.assertEqual(caught.exception.context_index, 0)
        self.assertEqual(caught.exception.completed_context_count, 0)
        self.assertEqual(caught.exception.solver_call_number, 1)

        representative = build_adr0305_v4_structure(
            kind=CapacityFillingStructureKind.REPRESENTATIVE
        )
        with (
            patch.object(
                qualification_module,
                "solve_reduced_river_sizing",
            ) as solver,
            self.assertRaisesRegex(ValueError, "excludes representative"),
        ):
            qualification_module._run_qualification(pool=representative)
        self.assertEqual(solver.call_count, 0)

    def test_b_requires_an_exact_passed_a_and_opens_no_value_after_failure(self) -> None:
        with patch.object(
            qualification_module,
            "solve_reduced_river_sizing",
            side_effect=_nonqualifying_solver,
        ):
            failed_result = qualification_module._run_qualification(pool=self.pool_a)
        failed_a = CapacityFillingQualificationCampaignResult(
            qualification=failed_result,
            teacher_control=None,
            elapsed_seconds=0.0,
        )
        with (
            patch.object(
                qualification_module,
                "_run_owned_campaign",
            ) as runner,
            self.assertRaisesRegex(ValueError, "failed qualified A"),
        ):
            run_adr0305_v4_qualified_b(qualified_a=failed_a)
        runner.assert_not_called()

        result = self.campaign_a.qualification
        changed_observation = replace(
            result.observations[0],
            full_value_chips=result.observations[0].full_value_chips + 1e-7,
        )
        changed_result = replace(
            result,
            observations=(changed_observation, *result.observations[1:]),
        )
        changed_a = replace(self.campaign_a, qualification=changed_result)
        with (
            patch.object(
                qualification_module,
                "_run_owned_campaign",
            ) as runner,
            self.assertRaisesRegex(ValueError, "exact qualified-A pass"),
        ):
            run_adr0305_v4_qualified_b(qualified_a=changed_a)
        runner.assert_not_called()

    def test_source_is_candidate_blind_and_never_builds_representative(self) -> None:
        path = _ROOT / "src/pontius/fresh_capacity_filling_qualification.py"
        source = path.read_text(encoding="utf-8")
        self.assertEqual(
            sha256(path.read_bytes()).hexdigest(),
            "800bf1ee8d50ef6a9da400a0b9557553bb10b80085815a0140dd84245ae1dd86",
        )
        tree = ast.parse(source, filename=str(path), feature_version=(3, 11))
        imports = tuple(
            (node.module, tuple(alias.name for alias in node.names))
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module is not None
        )
        imported_modules = {module for module, _names in imports}
        imported_names = {name for _module, names in imports for name in names}
        for forbidden in (
            "capacity_filling_action_abstraction",
            "collision_repair_action_abstraction",
            "legal_action_abstraction",
            "reference_hand_replay",
        ):
            self.assertNotIn(forbidden, imported_modules)
        for forbidden in (
            "CapacityFillingActionAbstractionSource",
            "CollisionRepairActionAbstractionSource",
        ):
            self.assertNotIn(forbidden, imported_names)
        self.assertNotIn("CapacityFillingStructureKind.REPRESENTATIVE", source)


if __name__ == "__main__":
    unittest.main()
