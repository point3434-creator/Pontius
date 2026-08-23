from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import unittest
from dataclasses import replace
from fractions import Fraction
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pontius.certified_sizing_validation_runner as runner
from pontius.certified_sizing_validation_runner import (
    CanonicalValidationPath,
    CanonicalValidationPlan,
    CanonicalValidationTask,
    build_adr0319_canonical_validation_plan,
    execute_canonical_validation_plan,
    verify_adr0319_plan_identity,
    verify_adr0319_source_and_dependencies,
)
from pontius.native_simplex_audit_corpus import (
    ADR0311_COMPLETE_CORPUS_SHA256,
    AuditBaseFamily,
    AuditLinearProgramBase,
    AuditVariantKind,
    build_audit_variant_descriptors,
    materialize_audit_variant,
)
from pontius.native_simplex_audit_runner import (
    AuditEnvironmentIdentity,
    BackendTermination,
)
from pontius.native_simplex_audit_structures import (
    AuditExactProbability,
    AuditWidthFourContext,
    ExactMicroLinearProgram,
    Sha256CounterStream,
    _shuffled_deck,
)
from pontius.reduced_river_sizing_lp import (
    LinearProgramConstraintUnit,
    LinearProgramObjectiveUnit,
    LinearProgramVariableUnit,
    compile_reduced_river_sizing_lp,
)


_TOY_ENVIRONMENT = AuditEnvironmentIdentity("toy", "0", "0", "0", "0")


def _toy_micro_case(case_id: str) -> ExactMicroLinearProgram:
    return ExactMicroLinearProgram(
        case_id=case_id,
        objective=(1, 1),
        coefficients=(
            (1, 0),
            (0, 1),
            (-1, 0),
            (0, -1),
            (1, 1),
            (1, 1),
            (1, 1),
            (1, 1),
            (1, 1),
        ),
        bounds=(2, 3, 0, 0, 2, 2, 2, 2, 2),
        feasible_witness=(1, 1),
        lower_bounds=(0, 0),
        upper_bounds=(2, 3),
    )


def _micro_base(case: ExactMicroLinearProgram) -> AuditLinearProgramBase:
    return AuditLinearProgramBase(
        base_id=case.case_id,
        family=AuditBaseFamily.EXACT_MICRO,
        source_input_sha256=case.digest,
        context_id=None,
        bet_sizes=None,
        objective=tuple(float(value) for value in case.objective),
        coefficients=tuple(
            tuple(float(value) for value in row) for row in case.coefficients
        ),
        bounds=tuple(float(value) for value in case.bounds),
        row_units=(LinearProgramConstraintUnit.DIMENSIONLESS,) * len(case.coefficients),
        variable_units=(
            LinearProgramVariableUnit.DIMENSIONLESS_GENERIC,
        )
        * case.variable_count,
        trusted_box_lower_bounds=(0.0,) * case.variable_count,
        trusted_box_upper_bounds=tuple(float(value) for value in case.upper_bounds),
        objective_unit=LinearProgramObjectiveUnit.DIMENSIONLESS,
        objective_offset=0.0,
    )


def _micro_task(ordinal: int, case_id: str) -> CanonicalValidationTask:
    case = _toy_micro_case(case_id)
    base = _micro_base(case)
    descriptor = build_audit_variant_descriptors(base)[0]
    return CanonicalValidationTask(
        ordinal=ordinal,
        base=base,
        descriptor=descriptor,
        materialized=materialize_audit_variant(base=base, descriptor=descriptor),
        path=CanonicalValidationPath.EXACT_MICRO_HIGHS_DS,
        exact_micro_case=case,
        sizing_context=None,
    )


def _successful_micro_linprog(*args: object, **kwargs: object) -> object:
    del args
    row_count = len(kwargs["b_ub"])  # type: ignore[arg-type]
    multipliers = [0.0] * row_count
    multipliers[4] = -1.0
    return SimpleNamespace(
        success=True,
        status=0,
        message="unsealed toy optimum",
        x=(0.0, 2.0),
        fun=-2.0,
        nit=1,
        crossover_nit=0,
        ineqlin=SimpleNamespace(marginals=tuple(multipliers)),
    )


def _toy_width_four_context() -> AuditWidthFourContext:
    stream = Sha256CounterStream(
        "pontius:test:adr0319:unsealed-width-four-validation-toy:v1"
    )
    probabilities = tuple(
        tuple(AuditExactProbability(1, 16) for _ in range(4)) for _ in range(4)
    )
    for attempt in range(1, 1_001):
        deck = _shuffled_deck(stream)
        try:
            return AuditWidthFourContext(
                context_id=f"adr0319-unsealed-sizing-toy-{attempt}",
                board=deck[:5],
                pot=6,
                stack=10,
                minimum_bet=2,
                opener_hands=tuple(
                    tuple(sorted(deck[offset : offset + 2]))
                    for offset in range(5, 13, 2)
                ),
                responder_hands=tuple(
                    tuple(sorted(deck[offset : offset + 2]))
                    for offset in range(13, 21, 2)
                ),
                joint_probabilities=probabilities,
            )
        except ValueError as error:
            if "showdown filter" not in str(error):
                raise
    raise AssertionError("unsealed width-four stream did not satisfy the filter")


def _sizing_task(ordinal: int) -> CanonicalValidationTask:
    context = _toy_width_four_context()
    bet_sizes = (2, 10)
    compiled = compile_reduced_river_sizing_lp(
        pot=context.pot,
        stack=context.stack,
        minimum_bet=context.minimum_bet,
        joint_probabilities=tuple(
            tuple(probability.fraction for probability in row)
            for row in context.joint_probabilities
        ),
        showdown_signs=context.showdown_signs,
        bet_sizes=bet_sizes,
    )
    base = AuditLinearProgramBase(
        base_id="adr0319-unsealed-sizing-toy",
        family=AuditBaseFamily.FRESH_REDUCED_SIZING,
        source_input_sha256=context.digest,
        context_id=context.context_id,
        bet_sizes=bet_sizes,
        objective=compiled.objective,
        coefficients=compiled.coefficients,
        bounds=compiled.bounds,
        row_units=compiled.row_units,
        variable_units=compiled.variable_units,
        trusted_box_lower_bounds=compiled.trusted_box_lower_bounds,
        trusted_box_upper_bounds=compiled.trusted_box_upper_bounds,
        objective_unit=compiled.objective_unit,
        objective_offset=compiled.objective_offset_chips,
    )
    descriptor = build_audit_variant_descriptors(base)[0]
    return CanonicalValidationTask(
        ordinal=ordinal,
        base=base,
        descriptor=descriptor,
        materialized=materialize_audit_variant(base=base, descriptor=descriptor),
        path=CanonicalValidationPath.CERTIFIED_SIZING_ADAPTER,
        exact_micro_case=None,
        sizing_context=context,
    )


class CertifiedSizingValidationSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.plan = build_adr0319_canonical_validation_plan()

    def test_exact_canonical_schedule_is_frozen_before_invocation(self) -> None:
        from pontius.certified_sizing_validation_seal import (
            ADR0319_SCHEDULE_SHA256,
        )

        self.assertEqual(self.plan.corpus_sha256, ADR0311_COMPLETE_CORPUS_SHA256)
        self.assertEqual(len(self.plan.tasks), 177)
        self.assertEqual(self.plan.schedule_digest, ADR0319_SCHEDULE_SHA256)
        self.assertEqual(
            tuple(task.ordinal for task in self.plan.tasks),
            tuple(range(177)),
        )
        self.assertTrue(
            all(task.descriptor.kind is AuditVariantKind.CANONICAL for task in self.plan.tasks)
        )
        self.assertEqual(
            sum(
                task.path is CanonicalValidationPath.EXACT_MICRO_HIGHS_DS
                for task in self.plan.tasks
            ),
            48,
        )
        self.assertEqual(
            sum(
                task.path is CanonicalValidationPath.CERTIFIED_SIZING_ADAPTER
                for task in self.plan.tasks
            ),
            129,
        )
        verify_adr0319_plan_identity(self.plan)

    def test_source_and_protocol_seals_are_immutable_and_current(self) -> None:
        from pontius.certified_sizing_validation_seal import (
            ADR0319_PROTOCOL_SHA256,
            ADR0319_SOURCE_MANIFEST,
        )
        from pontius.native_simplex_audit_runner import canonical_audit_bytes

        runner_hash = verify_adr0319_source_and_dependencies()
        self.assertEqual(
            runner_hash,
            ADR0319_SOURCE_MANIFEST["certified_sizing_validation_runner.py"],
        )
        self.assertEqual(
            hashlib.sha256(canonical_audit_bytes(runner.ADR0319_PROTOCOL)).hexdigest(),
            ADR0319_PROTOCOL_SHA256,
        )
        with self.assertRaises(TypeError):
            ADR0319_SOURCE_MANIFEST["x.py"] = "0" * 64  # type: ignore[index]

    def test_import_graph_excludes_consumers_candidates_and_native_solver(self) -> None:
        source = Path(runner.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                imported.add(node.module)
        forbidden = {
            "linear_program",
            "reduced_river_sizing_oracle",
            "fresh_capacity_filling_qualification",
            "capacity_filling_action_abstraction",
        }
        self.assertTrue(imported.isdisjoint(forbidden))
        self.assertNotIn("v4", source.lower())

    def test_source_failure_precedes_plan_build_and_backend_execution(self) -> None:
        with (
            patch.object(
                runner,
                "verify_adr0319_source_and_dependencies",
                side_effect=RuntimeError("source drift"),
            ),
            patch.object(runner, "build_adr0319_canonical_validation_plan") as build,
            patch.object(runner, "execute_canonical_validation_plan") as execute,
        ):
            with self.assertRaisesRegex(RuntimeError, "source drift"):
                runner.execute_sealed_adr0319_canonical_validation()
        build.assert_not_called()
        execute.assert_not_called()

    def test_toy_executor_cannot_mark_the_sealed_plan_as_executed(self) -> None:
        calls = 0

        def forbidden_backend(*args: object, **kwargs: object) -> object:
            nonlocal calls
            del args, kwargs
            calls += 1
            return object()

        with self.assertRaisesRegex(RuntimeError, "sealed canonical plans require"):
            execute_canonical_validation_plan(
                self.plan,
                linprog_function=forbidden_backend,
                environment=_TOY_ENVIRONMENT,
            )

        self.assertEqual(calls, 0)


class CertifiedSizingValidationToyTests(unittest.TestCase):
    def test_backend_exception_does_not_truncate_the_next_task(self) -> None:
        tasks = (
            _micro_task(0, "adr0319-unsealed-micro-a"),
            _micro_task(1, "adr0319-unsealed-micro-b"),
        )
        plan = CanonicalValidationPlan("a" * 64, tasks, False)
        calls = 0

        def first_fails(*args: object, **kwargs: object) -> object:
            nonlocal calls
            calls += 1
            if calls == 1:
                raise RuntimeError("injected first-call failure")
            return _successful_micro_linprog(*args, **kwargs)

        campaign = execute_canonical_validation_plan(
            plan,
            linprog_function=first_fails,
            environment=_TOY_ENVIRONMENT,
            runner_source_sha256="b" * 64,
        )

        self.assertEqual(calls, 2)
        self.assertEqual(len(campaign.observations), 2)
        first, second = campaign.observations
        self.assertFalse(first.passed)
        self.assertEqual(first.public_highs_ds_invocation_count, 1)
        assert first.micro_backend_result is not None
        self.assertIs(first.micro_backend_result.termination, BackendTermination.EXCEPTION)
        self.assertTrue(second.passed, second.failures)
        self.assertEqual(second.public_highs_ds_invocation_count, 1)
        self.assertEqual(
            hashlib.sha256(campaign.canonical_bytes).hexdigest(),
            campaign.digest,
        )
        self.assertIsInstance(json.loads(campaign.canonical_bytes), dict)

    def test_last_resort_guard_retains_post_call_count_and_chained_cause(self) -> None:
        task = _micro_task(0, "adr0319-unsealed-post-call-schema-failure")
        plan = CanonicalValidationPlan("9" * 64, (task,), False)

        def post_call_failure(
            task: CanonicalValidationTask,
            *,
            public_highs_call: object,
        ) -> object:
            del task
            public_highs_call()  # type: ignore[operator]
            try:
                raise ValueError("injected inner schema cause")
            except ValueError as error:
                raise RuntimeError("injected post-call failure") from error

        with patch.object(runner, "_micro_observation", post_call_failure):
            campaign = execute_canonical_validation_plan(
                plan,
                linprog_function=lambda: object(),
                environment=_TOY_ENVIRONMENT,
                runner_source_sha256="8" * 64,
            )

        observation = campaign.observations[0]
        self.assertFalse(observation.passed)
        self.assertEqual(observation.public_highs_ds_invocation_count, 1)
        failure = observation.failures[0]
        self.assertEqual(failure.code, "runner-task-exception")
        assert failure.exception is not None
        self.assertEqual(failure.exception.qualname, "RuntimeError")
        self.assertEqual(tuple(cause.qualname for cause in failure.causes), ("ValueError",))

    @unittest.skipUnless(importlib.util.find_spec("scipy"), "optional SciPy screen")
    def test_unsealed_sizing_toy_passes_both_adapter_and_independent_verifier(self) -> None:
        task = _sizing_task(0)
        plan = CanonicalValidationPlan("c" * 64, (task,), False)

        campaign = execute_canonical_validation_plan(
            plan,
            environment=_TOY_ENVIRONMENT,
            runner_source_sha256="d" * 64,
        )

        observation = campaign.observations[0]
        self.assertTrue(observation.passed, observation.failures)
        self.assertEqual(observation.public_highs_ds_invocation_count, 1)
        self.assertIsNotNone(observation.sizing_adapter_result)
        self.assertIsNotNone(observation.sizing_independent_verification)
        assert observation.sizing_independent_verification is not None
        self.assertTrue(observation.sizing_independent_verification.passed)

    @unittest.skipUnless(importlib.util.find_spec("scipy"), "optional SciPy screen")
    def test_adapter_independent_comparison_detects_semantic_mutation(self) -> None:
        task = _sizing_task(0)
        plan = CanonicalValidationPlan("e" * 64, (task,), False)
        campaign = execute_canonical_validation_plan(
            plan,
            environment=_TOY_ENVIRONMENT,
            runner_source_sha256="f" * 64,
        )
        observation = campaign.observations[0]
        assert observation.sizing_adapter_result is not None
        assert observation.sizing_independent_verification is not None
        actions = observation.sizing_adapter_result.responder_best_actions
        mutated_actions = (
            tuple(
                "call" if action == "fold" else "fold"
                for action in actions[0]
            ),
            *actions[1:],
        )
        mutated = replace(
            observation.sizing_adapter_result,
            responder_best_actions=mutated_actions,
        )

        mismatches = runner._sizing_consistency_failures(  # noqa: SLF001
            task,
            mutated,
            observation.sizing_independent_verification,
        )

        self.assertIn("responder-actions", mismatches)


if __name__ == "__main__":
    unittest.main()
