from __future__ import annotations

import importlib.util
import unittest
from dataclasses import dataclass
from unittest.mock import patch

import numpy as np

from pontius.behavioral_one_seat_master import solve_behavioral_one_seat_master
from pontius.behavioral_one_seat_master_v2 import (
    BehavioralMasterVerificationTolerances,
    solve_behavioral_one_seat_master_v2,
)


@dataclass(frozen=True)
class _InformationSet:
    variable_indices: tuple[int, ...]


@dataclass(frozen=True)
class _Gain:
    constant: float
    coefficients: tuple[float, ...]


class _Axis:
    variable_count = 2
    information_sets = (_InformationSet((0, 1)),)

    @staticmethod
    def coefficients(gain: _Gain) -> np.ndarray:
        return np.asarray(gain.coefficients, dtype=np.float64)


def _rows() -> tuple[tuple[_Gain, ...], ...]:
    return (
        (
            _Gain(0.5, (1.0, 0.0)),
            _Gain(0.5, (0.0, 1.0)),
        ),
    )


def _verification(
    *,
    probability: float = 1e-8,
    chip: float = 1e-7,
) -> BehavioralMasterVerificationTolerances:
    return BehavioralMasterVerificationTolerances(
        probability_equality_absolute=probability,
        probability_bound_absolute=probability,
        chip_inequality_absolute=chip,
        chip_epigraph_bound_absolute=chip,
        stationarity_absolute=1e-7,
        chip_complementarity_absolute=chip,
        chip_objective_gap_absolute=chip,
        dual_sign_absolute=1e-8,
    )


@unittest.skipUnless(importlib.util.find_spec("scipy"), "optional SciPy screen")
class BehavioralOneSeatMasterV2Tests(unittest.TestCase):
    def test_v2_preserves_v1_candidate_but_uses_certified_bound(self) -> None:
        v1 = solve_behavioral_one_seat_master(
            _Axis(),
            _rows(),
            (2.0,),
            tolerance=1e-10,
        )
        v2 = solve_behavioral_one_seat_master_v2(
            _Axis(),
            _rows(),
            (2.0,),
            solver_feasibility_tolerance=1e-10,
            verification_tolerances=_verification(),
        )

        self.assertEqual(v2.variables, v1.variables)
        self.assertEqual(v2.epigraph, v1.epigraph)
        self.assertEqual(v2.raw_primal_objective, v1.lower_bound)
        self.assertAlmostEqual(v2.raw_primal_objective, 1.0)
        self.assertLessEqual(v2.lower_bound, 1.0)
        self.assertAlmostEqual(v2.lower_bound, 1.0)
        self.assertEqual(v2.lower_bound, max(0.0, v2.certified_dual_lower_bound))

    def test_finite_dual_mutation_cannot_overstate_certified_lower_bound(self) -> None:
        import scipy.optimize

        real_linprog = scipy.optimize.linprog

        def mutated_linprog(*args: object, **kwargs: object) -> object:
            solved = real_linprog(*args, **kwargs)
            solved.ineqlin.marginals[0] -= 1e-8
            return solved

        with patch("scipy.optimize.linprog", side_effect=mutated_linprog):
            solved = solve_behavioral_one_seat_master_v2(
                _Axis(),
                _rows(),
                (2.0,),
                solver_feasibility_tolerance=1e-10,
                verification_tolerances=_verification(),
            )

        self.assertGreater(solved.raw_dual_objective, solved.raw_primal_objective)
        self.assertLess(solved.raw_primal_minus_dual, 0.0)
        self.assertLess(solved.dual_residual_correction_lower_bound, -1e-8)
        self.assertLessEqual(solved.certified_dual_lower_bound, 1.0)
        self.assertLessEqual(solved.lower_bound, 1.0)

    def test_nonfinite_solver_primal_fails_closed_before_diagnostics(self) -> None:
        import scipy.optimize

        real_linprog = scipy.optimize.linprog

        def mutated_linprog(*args: object, **kwargs: object) -> object:
            solved = real_linprog(*args, **kwargs)
            solved.x[0] = np.nan
            return solved

        with (
            patch("scipy.optimize.linprog", side_effect=mutated_linprog),
            self.assertRaisesRegex(FloatingPointError, "primal variables"),
        ):
            solve_behavioral_one_seat_master_v2(
                _Axis(),
                _rows(),
                (2.0,),
                solver_feasibility_tolerance=1e-10,
                verification_tolerances=_verification(),
            )

    def test_probability_violation_never_scales_with_a_large_chip_cap(self) -> None:
        import scipy.optimize

        real_linprog = scipy.optimize.linprog

        def mutated_linprog(*args: object, **kwargs: object) -> object:
            solved = real_linprog(*args, **kwargs)
            solved.x[0] = 1.1
            solved.x[1] = -0.1
            return solved

        broad_chip_checks = _verification(probability=1e-8, chip=1e6)
        with (
            patch("scipy.optimize.linprog", side_effect=mutated_linprog),
            self.assertRaisesRegex(ArithmeticError, "verification failed"),
        ):
            solve_behavioral_one_seat_master_v2(
                _Axis(),
                _rows(),
                (1e12,),
                solver_feasibility_tolerance=1e-10,
                verification_tolerances=broad_chip_checks,
            )

    def test_verification_tolerance_bundle_is_nominally_typed(self) -> None:
        with self.assertRaisesRegex(TypeError, "VerificationTolerances"):
            solve_behavioral_one_seat_master_v2(
                _Axis(),
                _rows(),
                (2.0,),
                solver_feasibility_tolerance=1e-10,
                verification_tolerances=object(),  # type: ignore[arg-type]
            )


if __name__ == "__main__":
    unittest.main()
