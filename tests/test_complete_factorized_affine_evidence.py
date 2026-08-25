from __future__ import annotations

import ast
import copy
from pathlib import Path
import unittest

import pontius.complete_factorized_affine_evidence as evidence
from pontius.complete_factorized_affine_evidence import (
    canonical_sha256,
    complete_factorized_affine_record,
    complete_factorized_affine_record_checks,
)
from pontius.factorized_tie_aware_affine import (
    build_factorized_tie_aware_affine_section,
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


class CompleteFactorizedAffineEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.game = build_legal_h4_selector_game()
        cls.source = legal_h4_source_policy(cls.game)
        cls.direction = compile_legal_h4_selector_directions(
            cls.game,
            cls.source,
            verify_adr0349_legal_h4_row_growth_result_artifact().record,
        )[0]
        cls.tie_result = build_factorized_tie_aware_affine_section(
            cls.game,
            cls.source,
            cls.direction.endpoint_policy,
            acting_player=0,
            target_player=0,
            selector_margin_allowance=1e-12,
        )
        cls.singleton_result = build_factorized_tie_aware_affine_section(
            cls.game,
            cls.source,
            cls.direction.endpoint_policy,
            acting_player=0,
            target_player=1,
            selector_margin_allowance=1e-12,
        )

    def test_complete_records_cover_tie_and_singleton_modes(self) -> None:
        for result in (self.tie_result, self.singleton_result):
            with self.subTest(mode=result.mode):
                record = complete_factorized_affine_record(result)
                checks = complete_factorized_affine_record_checks(result, record)
                self.assertTrue(all(checks.values()), checks)
                raw = record["raw_section"]
                self.assertEqual(
                    len(result.section.samples),
                    len(raw["samples"]),  # type: ignore[index]
                )
                self.assertTrue(
                    all(
                        sample["face"]["information_sets"]
                        for sample in raw["samples"]  # type: ignore[index]
                    )
                )
                self.assertEqual(
                    len(result.section.samples),
                    len(record["epigraph_residual_matrix"]),  # type: ignore[arg-type]
                )
                self.assertEqual(
                    record["complete_section_sha256"],
                    canonical_sha256(
                        {
                            key: value
                            for key, value in record.items()
                            if key != "complete_section_sha256"
                        }
                    ),
                )
        self.assertIsNone(
            complete_factorized_affine_record(self.tie_result)[
                "single_tape_window"
            ]
        )
        self.assertIsNotNone(
            complete_factorized_affine_record(self.singleton_result)[
                "single_tape_window"
            ]
        )

    def test_non_source_factor_mutation_is_detected_not_authenticated_only(self) -> None:
        record = complete_factorized_affine_record(self.tie_result)
        mutated = copy.deepcopy(record)
        samples = mutated["raw_section"]["samples"]  # type: ignore[index]
        non_source = next(
            sample
            for sample in samples
            if sample["scale"] != {"denominator": 1, "numerator": 0}
        )
        non_source["face"]["information_sets"][0]["state_count"] += 1
        checks = complete_factorized_affine_record_checks(self.tie_result, mutated)
        self.assertIs(checks["complete_raw_factors"], False)

    def test_every_row_residual_direction_and_active_count_are_checked(self) -> None:
        record = complete_factorized_affine_record(self.tie_result)
        mutated = copy.deepcopy(record)
        first = mutated["epigraph_residual_matrix"][0]["rows"][0]  # type: ignore[index]
        first["residual"] = {"denominator": 1, "numerator": -1}
        checks = complete_factorized_affine_record_checks(self.tie_result, mutated)
        self.assertIs(checks["epigraph_residual_orientation"], False)

        mutated = copy.deepcopy(record)
        mutated["epigraph_residual_matrix"][0]["active_rows"] += 1  # type: ignore[index]
        checks = complete_factorized_affine_record_checks(self.tie_result, mutated)
        self.assertIs(checks["epigraph_residual_orientation"], False)

    def test_row_piece_and_raw_section_digests_are_separate(self) -> None:
        record = complete_factorized_affine_record(self.tie_result)
        raw = record["raw_section"]
        self.assertEqual(
            len(raw["fan"]["cells"]),  # type: ignore[index]
            len(raw["cell_gain_rows"]),  # type: ignore[arg-type]
        )
        self.assertNotEqual(
            raw["section_sha256"],  # type: ignore[index]
            record["complete_section_sha256"],
        )
        self.assertTrue(
            all("row_sha256" in row for row in raw["cell_gain_rows"])  # type: ignore[union-attr]
        )

    def test_rehashed_piece_mutation_still_fails_live_identity(self) -> None:
        record = complete_factorized_affine_record(self.tie_result)
        mutated = copy.deepcopy(record)
        mutated["pieces"][0]["intercept"]["numerator"] += 1  # type: ignore[index]
        mutated["complete_section_sha256"] = canonical_sha256(
            {
                key: value
                for key, value in mutated.items()
                if key != "complete_section_sha256"
            }
        )
        checks = complete_factorized_affine_record_checks(
            self.tie_result,
            mutated,
        )
        self.assertIs(checks["complete_live_record_identity"], False)

    def test_serializer_has_no_cartesian_enumerator_or_writer(self) -> None:
        tree = ast.parse(Path(evidence.__file__).read_text(encoding="utf-8"))
        imported = set()
        names = set()
        attributes = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                imported.add(node.module)
                names.update(alias.name for alias in node.names)
            elif isinstance(node, ast.Name):
                names.add(node.id)
            elif isinstance(node, ast.Attribute):
                attributes.add(node.attr)
        self.assertNotIn("itertools", imported)
        self.assertNotIn("product", names)
        self.assertNotIn("write_bytes", attributes)
        self.assertFalse(any("result" in module for module in imported))


if __name__ == "__main__":
    unittest.main()
