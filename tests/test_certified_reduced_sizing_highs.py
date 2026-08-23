from __future__ import annotations

import ast
import importlib.util
import tempfile
import unittest
from dataclasses import replace
from fractions import Fraction
from pathlib import Path

import pontius.certified_reduced_sizing_highs as adapter
from pontius.certified_reduced_sizing_highs import (
    ADR0318_CERTIFIED_SIZING_ALLOWANCES,
    ADR0318_HIGHS_DS_OPTIONS,
    CertificateReversalAllowance,
    CertificateWidthAllowance,
    CertifiedSizingAdapterError,
    CertifiedSizingVerificationAllowances,
    solve_certified_reduced_sizing_highs,
    verify_adr0318_runtime_identity,
    verify_adr0318_source_and_dependencies,
)


_PROBABILITIES = (
    (Fraction(1, 4), Fraction(1, 4)),
    (Fraction(1, 4), Fraction(1, 4)),
)
_SIGNS = ((1, 1), (-1, -1))
_KWARGS = {
    "pot": 10,
    "stack": 20,
    "minimum_bet": 2,
    "joint_probabilities": _PROBABILITIES,
    "showdown_signs": _SIGNS,
    "bet_sizes": (2, 20),
}


class CertifiedReducedSizingSourceBoundaryTests(unittest.TestCase):
    def test_import_graph_excludes_native_and_candidate_consumers(self) -> None:
        source_path = Path(adapter.__file__)
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                imported.add(node.module)

        forbidden = {
            "linear_program",
            "reduced_river_sizing_oracle",
            "native_simplex_audit_runner",
            "fresh_capacity_filling_qualification",
            "capacity_filling_action_abstraction",
        }
        self.assertTrue(imported.isdisjoint(forbidden))
        legacy = source_path.with_name("reduced_river_sizing_oracle.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("certified_reduced_sizing_highs", legacy)

    def test_allowance_fields_are_nominally_distinct(self) -> None:
        with self.assertRaisesRegex(TypeError, "nonsemantic field"):
            CertifiedSizingVerificationAllowances(
                policy_nonnegativity=(
                    ADR0318_CERTIFIED_SIZING_ALLOWANCES.policy_nonnegativity
                ),
                policy_simplex_mass=(
                    ADR0318_CERTIFIED_SIZING_ALLOWANCES.policy_simplex_mass
                ),
                envelope_feasibility=(
                    ADR0318_CERTIFIED_SIZING_ALLOWANCES.envelope_feasibility
                ),
                reported_objective=(
                    ADR0318_CERTIFIED_SIZING_ALLOWANCES.reported_objective
                ),
                behavioral_reconstruction=(
                    ADR0318_CERTIFIED_SIZING_ALLOWANCES.behavioral_reconstruction
                ),
                certificate_reversal=(
                    ADR0318_CERTIFIED_SIZING_ALLOWANCES.certificate_reversal
                ),
                certificate_width=CertificateReversalAllowance(1e-9),  # type: ignore[arg-type]
            )

    def test_source_seal_is_line_ending_stable(self) -> None:
        verify_adr0318_source_and_dependencies()
        verify_adr0318_runtime_identity()
        from pontius.certified_reduced_sizing_highs_seal import (
            ADR0318_SOURCE_MANIFEST,
        )

        with self.assertRaises(TypeError):
            ADR0318_SOURCE_MANIFEST[  # type: ignore[index]
                "certified_reduced_sizing_highs.py"
            ] = "0" * 64

        source_path = Path(adapter.__file__)
        self.assertEqual(
            adapter.canonical_lf_source_sha256(source_path),
            ADR0318_SOURCE_MANIFEST["certified_reduced_sizing_highs.py"],
        )
        with tempfile.TemporaryDirectory() as directory:
            copy = Path(directory) / "adapter.py"
            normalized = source_path.read_bytes().replace(b"\r\n", b"\n")
            copy.write_bytes(normalized.replace(b"\n", b"\r\n"))
            self.assertEqual(
                adapter.canonical_lf_source_sha256(copy),
                ADR0318_SOURCE_MANIFEST["certified_reduced_sizing_highs.py"],
            )


@unittest.skipUnless(importlib.util.find_spec("scipy"), "optional SciPy screen")
class CertifiedReducedSizingHighsTests(unittest.TestCase):
    def test_canonical_toy_returns_exact_behavioral_interval(self) -> None:
        solved = solve_certified_reduced_sizing_highs(**_KWARGS)

        self.assertAlmostEqual(
            solved.feasible_behavioral_lower_bound_chips,
            10.0 / 3.0,
            delta=1e-12,
        )
        self.assertGreaterEqual(
            solved.certified_upper_bound_chips + 1e-9,
            solved.feasible_behavioral_lower_bound_chips,
        )
        self.assertLessEqual(solved.certified_gap_chips, 1e-9)
        self.assertEqual(solved.policy_clips, ())
        self.assertEqual(solved.highs_status_code, 0)
        self.assertEqual(
            tuple(sum(row, start=Fraction(0)) for row in solved.exact_opening_policy),
            (Fraction(1), Fraction(1)),
        )
        self.assertLessEqual(solved.reported_objective_error_chips, 1e-9)
        self.assertLessEqual(solved.behavioral_reconstruction_error_chips, 1e-9)

    def test_one_type_analytic_win_and_loss_controls(self) -> None:
        for sign, expected in ((1, 5.0), (-1, -5.0)):
            with self.subTest(sign=sign):
                solved = solve_certified_reduced_sizing_highs(
                    pot=10,
                    stack=20,
                    minimum_bet=2,
                    joint_probabilities=((Fraction(1),),),
                    showdown_signs=((sign,),),
                    bet_sizes=(2, 20),
                )
                self.assertAlmostEqual(
                    solved.feasible_behavioral_lower_bound_chips,
                    expected,
                    delta=1e-12,
                )
                self.assertLessEqual(solved.certified_gap_chips, 1e-9)

    def test_two_by_two_policy_matches_bounded_normal_form_teacher(self) -> None:
        from pontius.reduced_river_sizing_oracle import (
            ExactDealProbability,
            ReducedRiverSizingContext,
            solve_bounded_normal_form_sizing_teacher,
        )
        from pontius.river import make_hole, parse_cards

        context = ReducedRiverSizingContext(
            context_id="adr0318-bounded-toy",
            board=parse_cards("2c", "7d", "9h", "Js", "Qc"),
            pot=10,
            stack=20,
            minimum_bet=2,
            opener_hands=(make_hole("Ks", "Td"), make_hole("4s", "5s")),
            responder_hands=(make_hole("Ts", "8s"), make_hole("Kh", "Kd")),
            joint_probabilities=(
                (ExactDealProbability(1, 4), ExactDealProbability(1, 4)),
                (ExactDealProbability(1, 4), ExactDealProbability(1, 4)),
            ),
        )
        sizes = (2, 20)
        solved = solve_certified_reduced_sizing_highs(
            pot=context.pot,
            stack=context.stack,
            minimum_bet=context.minimum_bet,
            joint_probabilities=tuple(
                tuple(value.fraction for value in row)
                for row in context.joint_probabilities
            ),
            showdown_signs=context.showdown_signs,
            bet_sizes=sizes,
        )
        teacher = solve_bounded_normal_form_sizing_teacher(context, sizes)

        self.assertAlmostEqual(
            solved.feasible_behavioral_lower_bound_chips,
            teacher.value_chips,
            delta=1e-9,
        )
        self.assertLessEqual(teacher.duality_gap, 1e-9)
        self.assertLessEqual(solved.certified_gap_chips, 1e-9)

    def test_public_highs_options_and_trusted_box_are_exact(self) -> None:
        import scipy.optimize

        captured: dict[str, object] = {}

        def recording_backend(*args: object, **kwargs: object) -> object:
            captured["args"] = args
            captured["kwargs"] = kwargs
            return scipy.optimize.linprog(*args, **kwargs)

        solved = solve_certified_reduced_sizing_highs(
            **_KWARGS,
            linprog_function=recording_backend,
        )
        kwargs = captured["kwargs"]
        assert isinstance(kwargs, dict)
        self.assertEqual(kwargs["method"], "highs-ds")
        self.assertEqual(kwargs["options"], ADR0318_HIGHS_DS_OPTIONS.scipy_options)
        bounds = kwargs["bounds"]
        assert isinstance(bounds, tuple)
        self.assertEqual(len(bounds), len(solved.raw_primal_variables))
        self.assertTrue(all(left == 0.0 and right < float("inf") for left, right in bounds))

    def test_backend_status_shape_finiteness_and_objective_fail_closed(self) -> None:
        import scipy.optimize

        def backend_for(mutation: str):
            def mutated(*args: object, **kwargs: object) -> object:
                result = scipy.optimize.linprog(*args, **kwargs)
                if mutation == "status":
                    result.success = False
                    result.status = 1
                elif mutation == "shape":
                    result.x = result.x[:-1]
                elif mutation == "nan":
                    result.x[0] = float("nan")
                elif mutation == "objective":
                    result.fun += 0.01
                elif mutation == "dual":
                    result.ineqlin.marginals = None
                else:  # pragma: no cover - test construction guard
                    raise AssertionError("unknown mutation")
                return result

            return mutated

        cases = (
            ("status", "did not return an optimal"),
            ("shape", "wrong width"),
            ("nan", "nonfinite"),
            ("objective", "reported objective differs"),
            ("dual", "not iterable"),
        )
        for mutation, message in cases:
            with (
                self.subTest(mutation=mutation),
                self.assertRaisesRegex(CertifiedSizingAdapterError, message),
            ):
                solve_certified_reduced_sizing_highs(
                    **_KWARGS,
                    linprog_function=backend_for(mutation),
                )

    def test_probability_and_certificate_mutations_fail_closed(self) -> None:
        import scipy.optimize

        def bad_probability(*args: object, **kwargs: object) -> object:
            result = scipy.optimize.linprog(*args, **kwargs)
            result.x[0] = 1.1
            return result

        with self.assertRaisesRegex(CertifiedSizingAdapterError, "nonnegativity"):
            solve_certified_reduced_sizing_highs(
                **_KWARGS,
                linprog_function=bad_probability,
            )

        def bad_certificate(*args: object, **kwargs: object) -> object:
            result = scipy.optimize.linprog(*args, **kwargs)
            result.ineqlin.marginals[:] = 0.0
            return result

        with self.assertRaisesRegex(CertifiedSizingAdapterError, "interval exceeds"):
            solve_certified_reduced_sizing_highs(
                **_KWARGS,
                linprog_function=bad_certificate,
            )

    def test_invalid_exact_input_and_nonsemantic_bundle_fail_before_backend(self) -> None:
        called = False

        def forbidden_backend(*args: object, **kwargs: object) -> object:
            nonlocal called
            called = True
            raise AssertionError("backend should not run")

        with self.assertRaisesRegex(ValueError, "sum exactly"):
            solve_certified_reduced_sizing_highs(
                pot=10,
                stack=20,
                minimum_bet=2,
                joint_probabilities=((Fraction(1, 2),),),
                showdown_signs=((1,),),
                bet_sizes=(2, 20),
                linprog_function=forbidden_backend,
            )
        self.assertFalse(called)
        with self.assertRaisesRegex(TypeError, "allowances must be semantic"):
            solve_certified_reduced_sizing_highs(
                **_KWARGS,
                allowances=object(),  # type: ignore[arg-type]
                linprog_function=forbidden_backend,
            )
        self.assertFalse(called)
        relaxed = replace(
            ADR0318_CERTIFIED_SIZING_ALLOWANCES,
            certificate_width=CertificateWidthAllowance(1.0),
        )
        with self.assertRaisesRegex(ValueError, "differ from the frozen contract"):
            solve_certified_reduced_sizing_highs(
                **_KWARGS,
                allowances=relaxed,
                linprog_function=forbidden_backend,
            )
        self.assertFalse(called)

    def test_result_schema_rejects_policy_semantic_mutation(self) -> None:
        solved = solve_certified_reduced_sizing_highs(**_KWARGS)
        invalid = (
            (Fraction(1), Fraction(0), Fraction(0)),
            (Fraction(1), Fraction(1), Fraction(0)),
        )
        with self.assertRaisesRegex(ValueError, "row-stochastic"):
            replace(solved, exact_opening_policy=invalid)


if __name__ == "__main__":
    unittest.main()
