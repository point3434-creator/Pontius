from __future__ import annotations

import ast
import hashlib
import json
import math
import unittest
from dataclasses import replace
from fractions import Fraction
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from pontius.native_simplex_audit_corpus import (
    AuditBaseFamily,
    AuditLinearProgramBase,
    AuditVariantKind,
    build_audit_variant_descriptors,
    materialize_audit_variant,
)
from pontius.native_simplex_audit_runner import (
    ADR0311_BACKEND_ORDER,
    ADR0311_CROSS_BACKEND_SIZING_ALLOWANCE,
    ADR0311_CROSS_VARIANT_SIZING_ALLOWANCE,
    ADR0311_ENVELOPE_FEASIBILITY_ALLOWANCE,
    ADR0311_HIGHS_DS_OPTIONS,
    ADR0311_HIGHS_IPM_OPTIONS,
    ADR0311_MICRO_DUAL_ALLOWANCE,
    ADR0311_MICRO_OBJECTIVE_ALLOWANCE,
    ADR0311_MICRO_PRIMAL_ALLOWANCE,
    ADR0311_MICRO_VARIANT_COMPARISON_ALLOWANCE,
    ADR0311_NATIVE_OPTIONS,
    ADR0311_POLICY_NONNEGATIVITY_ALLOWANCE,
    ADR0311_POLICY_SIMPLEX_MASS_ALLOWANCE,
    ADR0311_SIZING_CERTIFICATE_WIDTH_ALLOWANCE,
    ADR0311_SIZING_OBJECTIVE_ALLOWANCE,
    ADR0313_EXPECTED_ENVIRONMENT,
    ADR0313_EXPECTED_INVOCATION_COUNT,
    ADR0313_PROTOCOL,
    AuditBackend,
    AuditEnvironmentIdentity,
    BackendRawResult,
    BackendTermination,
    DualHintConvention,
    PreparedAuditPlan,
    PreparedAuditTask,
    build_audit_schedule,
    build_backend_certificate_diagnostics,
    build_backend_coordinate_diagnostics,
    capture_audit_environment_identity,
    enumerate_exact_micro_vertices,
    execute_audit_plan,
    invoke_highs_backend,
    invoke_native_backend,
    map_primal_to_canonical,
    reconstruct_dual_hint,
    reconstruct_native_failure_coordinates,
    verify_sizing_backend_result,
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

_RUNNER_SOURCE_SHA256 = "cfb127960e3d501a156f14d22244ecd122874b74fefb668685f9a721503ade16"
_NATIVE_SOURCE_SHA256 = "6069dac31bb2915284319d0d5551d5773f4b4cac294d07c440f4b4d9ee4c83f8"
_CERTIFICATE_SOURCE_SHA256 = "0ca8b0443eb8a0279247fad659694d88b723b15bf0b2d3e5f7c7ef2c2ddfa910"


def _toy_micro_case() -> ExactMicroLinearProgram:
    # Five duplicate oblique rows deliberately exercise degeneracy and
    # non-unique optima without looking at any sealed audit case.
    return ExactMicroLinearProgram(
        case_id="toy-audit-micro",
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


def _toy_micro_base(case: ExactMicroLinearProgram) -> AuditLinearProgramBase:
    return AuditLinearProgramBase(
        base_id=case.case_id,
        family=AuditBaseFamily.EXACT_MICRO,
        source_input_sha256=case.digest,
        context_id=None,
        bet_sizes=None,
        objective=tuple(float(value) for value in case.objective),
        coefficients=tuple(tuple(float(value) for value in row) for row in case.coefficients),
        bounds=tuple(float(value) for value in case.bounds),
        row_units=(LinearProgramConstraintUnit.DIMENSIONLESS,) * len(case.coefficients),
        variable_units=(LinearProgramVariableUnit.DIMENSIONLESS_GENERIC,) * case.variable_count,
        trusted_box_lower_bounds=(0.0,) * case.variable_count,
        trusted_box_upper_bounds=tuple(float(value) for value in case.upper_bounds),
        objective_unit=LinearProgramObjectiveUnit.DIMENSIONLESS,
        objective_offset=0.0,
    )


def _toy_context() -> AuditWidthFourContext:
    stream = Sha256CounterStream(
        "pontius:test:native-simplex-audit-runner:unsealed-width-four-toy:v1"
    )
    probabilities = tuple(tuple(AuditExactProbability(1, 16) for _ in range(4)) for _ in range(4))
    for attempt in range(1, 1_001):
        deck = _shuffled_deck(stream)
        try:
            return AuditWidthFourContext(
                context_id=f"toy-audit-width-four-{attempt}",
                board=deck[:5],
                pot=6,
                stack=10,
                minimum_bet=2,
                opener_hands=tuple(
                    tuple(sorted(deck[offset : offset + 2])) for offset in range(5, 13, 2)
                ),
                responder_hands=tuple(
                    tuple(sorted(deck[offset : offset + 2])) for offset in range(13, 21, 2)
                ),
                joint_probabilities=probabilities,
            )
        except ValueError as error:
            if "showdown filter" not in str(error):
                raise
    raise AssertionError("unsealed toy context stream did not satisfy the structural filter")


def _toy_sizing_base(context: AuditWidthFourContext) -> AuditLinearProgramBase:
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
    return AuditLinearProgramBase(
        base_id="toy-audit-sizing",
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


def _toy_task(
    *,
    task_index: int,
    case: ExactMicroLinearProgram,
    base: AuditLinearProgramBase,
    kind: AuditVariantKind,
) -> PreparedAuditTask:
    descriptor = build_audit_variant_descriptors(base)[tuple(AuditVariantKind).index(kind)]
    return PreparedAuditTask(
        task_index=task_index,
        base=base,
        descriptor=descriptor,
        materialized=materialize_audit_variant(base=base, descriptor=descriptor),
        exact_micro_case=case,
        sizing_context=None,
    )


def _as_backend(
    backend: AuditBackend,
    linear_program,
) -> BackendRawResult:
    native = invoke_native_backend(linear_program)
    if native.termination is not BackendTermination.OPTIMAL:
        raise AssertionError(native.message)
    return replace(native, backend=backend)


class NativeSimplexAuditRunnerTests(unittest.TestCase):
    def test_exact_fraction_enumerator_keeps_degenerate_nonunique_optima(self) -> None:
        result = enumerate_exact_micro_vertices(_toy_micro_case())

        self.assertEqual(result.active_set_count, math.comb(11, 2))
        self.assertEqual(result.vertex_count, 3)
        self.assertEqual(result.maximizer_count, 2)
        self.assertEqual(result.optimum.fraction, Fraction(2))
        self.assertEqual(
            tuple(value.fraction for value in result.lexicographically_smallest_maximizer),
            (Fraction(0), Fraction(2)),
        )

    def test_coordinate_maps_and_scaled_duplicate_duals_return_to_canonical_axes(self) -> None:
        case = _toy_micro_case()
        base = _toy_micro_base(case)
        variants = build_audit_variant_descriptors(base)
        variable_variant = variants[
            tuple(AuditVariantKind).index(AuditVariantKind.VARIABLE_PERMUTATION)
        ]
        variant_primal = (7.0, 11.0)
        canonical = map_primal_to_canonical(variant_primal, variable_variant)
        for variant_index, canonical_index in enumerate(
            variable_variant.variant_to_canonical_variables
        ):
            self.assertEqual(canonical[canonical_index], variant_primal[variant_index])

        scaled = variants[tuple(AuditVariantKind).index(AuditVariantKind.DYADIC_ROW_SCALING)]
        source = 4
        variant_row = scaled.canonical_to_variant_rows[source][0]
        scale = float(2 ** scaled.row_scale_exponents[variant_row])
        raw = [0.0] * len(scaled.variant_to_canonical_rows)
        raw[variant_row] = 1.0 / scale
        mapped = reconstruct_dual_hint(
            tuple(raw),
            convention=DualHintConvention.MAXIMIZATION_NONNEGATIVE,
            descriptor=scaled,
        )
        self.assertAlmostEqual(mapped.canonical_minimization_hint[source], -1.0)

        wrong_sign = [0.0] * len(scaled.variant_to_canonical_rows)
        wrong_sign[variant_row] = -0.25
        clipped = reconstruct_dual_hint(
            tuple(wrong_sign),
            convention=DualHintConvention.MAXIMIZATION_NONNEGATIVE,
            descriptor=scaled,
        )
        self.assertEqual(clipped.sign_clip_variant_rows, (variant_row,))
        self.assertEqual(clipped.clipped_minimization_variant_hint[variant_row], 0.0)

        redundancy = variants[tuple(AuditVariantKind).index(AuditVariantKind.REDUNDANCY)]
        source = next(
            index
            for index, variant_positions in enumerate(redundancy.canonical_to_variant_rows)
            if len(variant_positions) >= 2
        )
        positions = redundancy.canonical_to_variant_rows[source]
        raw = [0.0] * len(redundancy.variant_to_canonical_rows)
        for position in positions:
            raw[position] = 1.0 / len(positions)
        mapped = reconstruct_dual_hint(
            tuple(raw),
            convention=DualHintConvention.MAXIMIZATION_NONNEGATIVE,
            descriptor=redundancy,
        )
        self.assertAlmostEqual(mapped.canonical_minimization_hint[source], -1.0)

    def test_highs_adapters_pass_only_the_frozen_minimization_contract(self) -> None:
        case = _toy_micro_case()
        base = _toy_micro_base(case)
        descriptor = build_audit_variant_descriptors(base)[0]
        materialized = materialize_audit_variant(base=base, descriptor=descriptor)
        calls = []

        def fake_linprog(c, **kwargs):
            calls.append((c, kwargs))
            dual = [0.0] * len(materialized.bounds)
            dual[4] = -1.0
            return SimpleNamespace(
                success=True,
                status=0,
                message="toy optimal",
                x=(0.0, 2.0),
                fun=-2.0,
                nit=4,
                crossover_nit=1,
                ineqlin=SimpleNamespace(marginals=tuple(dual)),
            )

        for backend, frozen in (
            (AuditBackend.HIGHS_DS, ADR0311_HIGHS_DS_OPTIONS),
            (AuditBackend.HIGHS_IPM, ADR0311_HIGHS_IPM_OPTIONS),
        ):
            result = invoke_highs_backend(
                backend,
                materialized,
                linprog_function=fake_linprog,
            )
            self.assertIs(result.termination, BackendTermination.OPTIMAL)
            objective, arguments = calls[-1]
            self.assertEqual(objective, tuple(-value for value in materialized.objective))
            self.assertEqual(
                set(arguments),
                {"A_ub", "b_ub", "bounds", "method", "options"},
            )
            self.assertEqual(arguments["A_ub"], materialized.coefficients)
            self.assertEqual(arguments["b_ub"], materialized.bounds)
            self.assertEqual(arguments["bounds"], [(0.0, None)] * base.variable_count)
            self.assertEqual(arguments["method"], frozen.method)
            self.assertEqual(arguments["options"], frozen.scipy_options)

    def test_native_adapter_retains_failure_locals_without_a_second_solve(self) -> None:
        case = _toy_micro_case()
        base = _toy_micro_base(case)
        descriptor = build_audit_variant_descriptors(base)[0]
        materialized = materialize_audit_variant(base=base, descriptor=descriptor)
        calls = 0

        def maximize_linear_program(*args, **kwargs):
            nonlocal calls
            calls += 1
            variables = (0.0, 2.0)
            objective_value = 2.0
            dual_variables = (0.0,) * len(materialized.bounds)
            pivots = 7
            violations = [0.0] * len(materialized.bounds)
            violations[4] = 2.0
            allowed = 1e-8
            del args, kwargs, variables, objective_value, dual_variables, pivots
            del violations, allowed
            raise AssertionError("linear-program solution fails primal verification")

        # The locals are deliberately deleted above only after assignment to prove
        # that a traceback cannot invent missing diagnostics.
        with patch(
            "pontius.native_simplex_audit_runner.maximize_linear_program",
            maximize_linear_program,
        ):
            missing = invoke_native_backend(materialized)
        self.assertEqual(calls, 1)
        self.assertIsNone(missing.native_verification_trace)

        def maximize_linear_program(*args, **kwargs):
            nonlocal calls
            calls += 1
            variables = (0.0, 2.0)
            objective_value = 2.0
            dual_variables = (0.0,) * len(materialized.bounds)
            pivots = 7
            violations = [0.0] * len(materialized.bounds)
            violations[4] = 2.0
            allowed = 1e-8
            if not (
                variables
                and objective_value
                and dual_variables
                and pivots
                and violations
                and allowed
            ):  # pragma: no cover - keep diagnostic locals live
                raise RuntimeError
            if args is kwargs:  # pragma: no cover - keep both arguments live
                raise RuntimeError
            raise AssertionError("linear-program solution fails primal verification")

        with patch(
            "pontius.native_simplex_audit_runner.maximize_linear_program",
            maximize_linear_program,
        ):
            captured = invoke_native_backend(materialized)
        self.assertEqual(calls, 2)
        self.assertIs(captured.termination, BackendTermination.EXCEPTION)
        assert captured.native_verification_trace is not None
        coordinates = reconstruct_native_failure_coordinates(
            captured.native_verification_trace,
            descriptor,
        )
        assert coordinates is not None
        self.assertEqual(coordinates.failing_variant_rows, (4,))
        self.assertEqual(coordinates.failing_canonical_rows, (4,))
        self.assertEqual(coordinates.maximum_variant_residual, 2.0)
        coordinate_diagnostics = build_backend_coordinate_diagnostics(
            base=base,
            descriptor=descriptor,
            raw=captured,
        )
        certificate_diagnostics = build_backend_certificate_diagnostics(
            base=base,
            descriptor=descriptor,
            raw=captured,
        )
        self.assertEqual(coordinate_diagnostics.canonical_primal, (0.0, 2.0))
        self.assertEqual(len(coordinate_diagnostics.original_row_residuals), 9)
        self.assertTrue(
            math.isfinite(certificate_diagnostics.certified_value_upper_bound_with_offset)
        )

    def test_complete_toy_schedule_runs_variant_major_and_reuses_exact_work(self) -> None:
        case = _toy_micro_case()
        base = _toy_micro_base(case)
        tasks = tuple(
            _toy_task(task_index=index, case=case, base=base, kind=kind)
            for index, kind in enumerate(AuditVariantKind)
        )
        plan = PreparedAuditPlan(
            corpus_sha256="a" * 64,
            tasks=tasks,
            schedule=build_audit_schedule(tasks),
            sealed_adr0311=False,
        )
        calls = []

        def adapter(backend):
            def run(linear_program):
                calls.append(backend)
                return _as_backend(backend, linear_program)

            return run

        campaign = execute_audit_plan(
            plan,
            adapters={backend: adapter(backend) for backend in AuditBackend},
            environment=AuditEnvironmentIdentity("toy", "0", "0", "0", "0"),
            runner_source_sha256="b" * 64,
        )

        self.assertEqual(len(campaign.observations), 15)
        self.assertEqual(tuple(calls), ADR0311_BACKEND_ORDER * len(AuditVariantKind))
        self.assertTrue(all(observation.verified_pass for observation in campaign.observations))
        exact_work = {observation.exact_micro_work for observation in campaign.observations}
        self.assertEqual(len(exact_work), 1)
        self.assertEqual(campaign.canonical_bytes, campaign.canonical_bytes)
        self.assertEqual(hashlib.sha256(campaign.canonical_bytes).hexdigest(), campaign.digest)
        self.assertIsInstance(json.loads(campaign.canonical_bytes), dict)

    def test_backend_and_schema_failures_are_captured_without_truncation(self) -> None:
        case = _toy_micro_case()
        base = _toy_micro_base(case)
        tasks = (
            _toy_task(
                task_index=0,
                case=case,
                base=base,
                kind=AuditVariantKind.CANONICAL,
            ),
        )
        plan = PreparedAuditPlan(
            corpus_sha256="c" * 64,
            tasks=tasks,
            schedule=build_audit_schedule(tasks),
            sealed_adr0311=False,
        )
        calls = []

        def raises(linear_program):
            calls.append(AuditBackend.NATIVE)
            raise RuntimeError("toy backend failure")

        def malformed(linear_program):
            calls.append(AuditBackend.HIGHS_DS)
            return object()

        def succeeds(linear_program):
            calls.append(AuditBackend.HIGHS_IPM)
            return _as_backend(AuditBackend.HIGHS_IPM, linear_program)

        campaign = execute_audit_plan(
            plan,
            adapters={
                AuditBackend.NATIVE: raises,
                AuditBackend.HIGHS_DS: malformed,
                AuditBackend.HIGHS_IPM: succeeds,
            },
            environment=AuditEnvironmentIdentity("toy", "0", "0", "0", "0"),
            runner_source_sha256="d" * 64,
        )

        self.assertEqual(tuple(calls), ADR0311_BACKEND_ORDER)
        self.assertEqual(len(campaign.observations), 3)
        first, second, third = campaign.observations
        assert first.backend_result is not None
        self.assertIs(first.backend_result.termination, BackendTermination.EXCEPTION)
        self.assertEqual(first.backend_result.exception.message, "toy backend failure")
        self.assertIsNone(second.backend_result)
        self.assertEqual(second.runner_failures[0].stage.value, "backend-schema")
        self.assertTrue(third.verified_pass)

    def test_unsealed_width_four_toy_reconstructs_a_feasible_exact_policy_interval(self) -> None:
        context = _toy_context()
        base = _toy_sizing_base(context)
        for descriptor in build_audit_variant_descriptors(base):
            materialized = materialize_audit_variant(base=base, descriptor=descriptor)
            raw = invoke_native_backend(materialized)
            self.assertIs(raw.termination, BackendTermination.OPTIMAL)

            verified = verify_sizing_backend_result(
                base=base,
                descriptor=descriptor,
                raw=raw,
                context=context,
            )

            self.assertTrue(verified.passed, (descriptor.kind, verified.failures))
            self.assertEqual(len(verified.variant_row_residuals), len(materialized.bounds))
            for row in verified.exact_normalized_policy:
                self.assertEqual(sum((value.fraction for value in row), start=Fraction(0)), 1)
            self.assertLessEqual(
                verified.behavioral_lower_bound_chips,
                verified.certified_upper_bound_chips
                + ADR0311_SIZING_CERTIFICATE_WIDTH_ALLOWANCE.chips,
            )
            self.assertEqual(len(verified.responder_best_actions), 4)
            self.assertTrue(all(len(actions) == 2 for actions in verified.responder_best_actions))

    def test_every_equal_nominal_quantity_has_a_distinct_semantic_type(self) -> None:
        allowances = (
            ADR0311_MICRO_PRIMAL_ALLOWANCE,
            ADR0311_MICRO_DUAL_ALLOWANCE,
            ADR0311_MICRO_OBJECTIVE_ALLOWANCE,
            ADR0311_MICRO_VARIANT_COMPARISON_ALLOWANCE,
            ADR0311_POLICY_NONNEGATIVITY_ALLOWANCE,
            ADR0311_POLICY_SIMPLEX_MASS_ALLOWANCE,
            ADR0311_ENVELOPE_FEASIBILITY_ALLOWANCE,
            ADR0311_SIZING_OBJECTIVE_ALLOWANCE,
            ADR0311_SIZING_CERTIFICATE_WIDTH_ALLOWANCE,
            ADR0311_CROSS_BACKEND_SIZING_ALLOWANCE,
            ADR0311_CROSS_VARIANT_SIZING_ALLOWANCE,
        )
        self.assertEqual(len({type(value) for value in allowances}), len(allowances))
        self.assertTrue(
            all(
                (value.value if hasattr(value, "value") else value.chips) == 1e-9
                for value in allowances
            )
        )
        self.assertEqual(ADR0311_NATIVE_OPTIONS.tolerance, 1e-11)
        self.assertEqual(ADR0311_NATIVE_OPTIONS.maximum_pivots, 4_096)
        self.assertEqual(ADR0313_EXPECTED_INVOCATION_COUNT, 885 * 3)
        self.assertEqual(ADR0313_PROTOCOL.expected_invocation_count, 2_655)
        self.assertEqual(
            ADR0313_EXPECTED_ENVIRONMENT,
            AuditEnvironmentIdentity("CPython", "3.14.6", "2.5.2", "1.18.0", "1.12.0"),
        )
        self.assertEqual(capture_audit_environment_identity(), ADR0313_EXPECTED_ENVIRONMENT)

    def test_runner_source_is_candidate_free_and_frozen_native_is_unchanged(self) -> None:
        root = Path(__file__).parents[1] / "src" / "pontius"
        runner = root / "native_simplex_audit_runner.py"
        source = runner.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(runner), feature_version=(3, 11))
        local_imports = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.level == 1 and node.module is not None
        }
        self.assertEqual(
            local_imports,
            {
                "linear_program",
                "linear_program_certificate",
                "native_simplex_audit_corpus",
                "native_simplex_audit_seal",
                "native_simplex_audit_structures",
                "reduced_river_sizing_lp",
            },
        )
        forbidden = (
            "capacity_filling",
            "action_abstraction",
            "solve_reduced_river_sizing",
        )
        for name in forbidden:
            self.assertNotIn(name, source)
        self.assertEqual(hashlib.sha256(runner.read_bytes()).hexdigest(), _RUNNER_SOURCE_SHA256)
        self.assertEqual(
            hashlib.sha256((root / "linear_program.py").read_bytes()).hexdigest(),
            _NATIVE_SOURCE_SHA256,
        )
        self.assertEqual(
            hashlib.sha256((root / "linear_program_certificate.py").read_bytes()).hexdigest(),
            _CERTIFICATE_SOURCE_SHA256,
        )


if __name__ == "__main__":
    unittest.main()
