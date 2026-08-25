from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path
import unittest
from unittest.mock import patch

import pontius.legal_h4_factorized_affine_confirmation_directions as directions
from pontius.legal_h4_factorized_affine_confirmation_directions import (
    REGRET_PUBLIC_HISTORIES,
    RowGrowthDirectionRejected,
    compile_legal_h4_confirmation_directions,
    direction_descriptor,
)
from pontius.legal_h4_selector_directions import (
    compile_legal_h4_selector_directions,
)
from pontius.legal_h4_selector_fixture import (
    build_legal_h4_selector_game,
    legal_h4_source_policy,
)
from pontius.legal_responder_raise_h4_row_growth_result import (
    verify_adr0349_legal_h4_row_growth_result_artifact,
)
from pontius.one_seat_convex_generation import AffinePayoff
from pontius.one_seat_row_growth_audit import audit_one_seat_row_growth


class LegalH4FactorizedAffineConfirmationDirectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.game = build_legal_h4_selector_game()
        cls.source = legal_h4_source_policy(cls.game)
        cls.compilation = compile_legal_h4_confirmation_directions(
            cls.game,
            cls.source,
            context_id="development-control",
        )
        cls.raw_audit = audit_one_seat_row_growth(
            cls.game,
            cls.source,
            acting_player=0,
            guard=0.25,
            max_iterations=128,
            tolerance=1e-10,
        )

    def test_development_control_reproduces_the_existing_downstream_directions(self) -> None:
        parent = verify_adr0349_legal_h4_row_growth_result_artifact()
        historical = compile_legal_h4_selector_directions(
            self.game,
            self.source,
            parent.record,
            acting_player=0,
            tolerance=1e-10,
        )
        self.assertEqual(
            tuple(direction.endpoint_policy_sha256 for direction in historical),
            tuple(
                direction.endpoint_policy_sha256
                for direction in self.compilation.directions
            ),
        )
        self.assertEqual(
            (
                "bd9533ae86809b0cbcaeb643c3b1503794f6e7812c0b48950849bb976a7e4f9d",
                "e849f04dbc967c6422a719cf430d4e5a646ba59a6bb00a0c9b9e17ff27892209",
                "3372dd9b65180afdbb2c3260d43f559366c77017bfd9c498371406aa7d001e2e",
                "0f9be1f884cb09eb8318a88a1548afb402ec256e8fa52f19118c64569fe7658b",
            ),
            tuple(
                direction.endpoint_policy_sha256
                for direction in self.compilation.directions
            ),
        )
        self.assertEqual(
            REGRET_PUBLIC_HISTORIES,
            tuple(
                direction.changed_public_histories[0]
                for direction in self.compilation.directions[:3]
            ),
        )
        self.assertEqual(
            ["root"],
            direction_descriptor(self.compilation.directions[-1])[
                "changed_public_histories"
            ],
        )

    def test_row_growth_proposal_has_exact_rows_and_conjunctive_gates(self) -> None:
        row_growth = self.compilation.row_growth
        self.assertIs(row_growth["passed"], True)
        self.assertTrue(all(row_growth["gates"].values()))  # type: ignore[union-attr]
        self.assertEqual([1, 1], row_growth["response_rows_by_player"])
        self.assertEqual(2, len(row_growth["response_rows"]))  # type: ignore[arg-type]
        self.assertTrue(
            all(
                row["exact_float_identity"]
                for row in row_growth["response_rows"]  # type: ignore[union-attr]
            )
        )
        self.assertEqual(1, len(row_growth["iterations"]))  # type: ignore[arg-type]
        self.assertEqual(
            "67f878635c42efeefad5b6eac6e8d04af62d4bdb64dd333d50880186567398cd",
            row_growth["row_growth_semantic_sha256"],
        )
        with self.assertRaises(TypeError):
            row_growth["passed"] = False  # type: ignore[index]

    def test_parameter_and_nominal_identity_mutations_fail_closed(self) -> None:
        for kwargs in (
            {"acting_player": 1},
            {"guard": 0.2},
            {"max_iterations": 127},
            {"tolerance": 1e-9},
        ):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(ValueError):
                    compile_legal_h4_confirmation_directions(
                        self.game,
                        self.source,
                        context_id="development-control",
                        **kwargs,
                    )
        with self.assertRaises(TypeError):
            compile_legal_h4_confirmation_directions(
                self.game,
                self.source,
                context_id="",
            )

    def test_exact_row_mutation_rejects_the_proposal(self) -> None:
        first = self.raw_audit.response_rows[0]
        mutated_row = replace(
            first,
            gain=AffinePayoff(
                first.gain.constant + 0.125,
                first.gain.coefficients,
            ),
        )
        mutated = replace(
            self.raw_audit,
            response_rows=(mutated_row, *self.raw_audit.response_rows[1:]),
        )
        with patch.object(directions, "audit_one_seat_row_growth", return_value=mutated):
            with self.assertRaises(RowGrowthDirectionRejected) as caught:
                compile_legal_h4_confirmation_directions(
                    self.game,
                    self.source,
                    context_id="development-control",
                )
        self.assertIs(
            caught.exception.record["gates"]["all_response_rows_exactly_rebound"],  # type: ignore[index]
            False,
        )

    def test_master_certificate_mutation_rejects_the_proposal(self) -> None:
        first_master = self.raw_audit.masters[0]
        mutated_solution = replace(
            first_master.solution,
            duality_gap=1e-4,
        )
        mutated_master = replace(first_master, solution=mutated_solution)
        mutated = replace(
            self.raw_audit,
            masters=(mutated_master, *self.raw_audit.masters[1:]),
        )
        with patch.object(directions, "audit_one_seat_row_growth", return_value=mutated):
            with self.assertRaises(RowGrowthDirectionRejected) as caught:
                compile_legal_h4_confirmation_directions(
                    self.game,
                    self.source,
                    context_id="development-control",
                )
        self.assertIs(
            caught.exception.record["gates"][
                "maximum_master_duality_gap_at_most_1e-8"
            ],  # type: ignore[index]
            False,
        )

    def test_cap_semantics_mutation_rejects_the_proposal(self) -> None:
        mutated_result = replace(
            self.raw_audit.result,
            caps=(
                self.raw_audit.result.caps[0] + 0.125,
                *self.raw_audit.result.caps[1:],
            ),
        )
        mutated = replace(self.raw_audit, result=mutated_result)
        with patch.object(directions, "audit_one_seat_row_growth", return_value=mutated):
            with self.assertRaises(RowGrowthDirectionRejected) as caught:
                compile_legal_h4_confirmation_directions(
                    self.game,
                    self.source,
                    context_id="development-control",
                )
        self.assertIs(
            caught.exception.record["gates"]["exact_cap_identity"],  # type: ignore[index]
            False,
        )

    def test_module_has_no_import_time_target_or_result_owner(self) -> None:
        tree = ast.parse(Path(directions.__file__).read_text(encoding="utf-8"))
        imported = set()
        top_level_calls = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                imported.add(node.module)
        for node in tree.body:
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
                top_level_calls.append(node.value)
        self.assertFalse(
            any("factorized_affine_result" in module for module in imported)
        )
        self.assertFalse(
            any("legal_responder_raise_h4" in module for module in imported)
        )
        self.assertEqual([], top_level_calls)


if __name__ == "__main__":
    unittest.main()
