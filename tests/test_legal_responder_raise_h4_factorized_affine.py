from __future__ import annotations

import ast
from copy import deepcopy
from fractions import Fraction
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from pontius.factorized_tie_aware_affine import (
    FACTOR_TIE_AWARE_MAXIMUM_ENVELOPE,
    V2_SINGLE_TAPE,
    build_factorized_tie_aware_affine_section,
)
from pontius.legal_responder_raise_h4_directional_face_result import (
    verify_adr0356_legal_h4_directional_face_result_artifact,
)
from pontius.legal_responder_raise_h4_factorized_affine import (
    _CONFIG,
    _OUTPUT,
    _integration_checks,
    _integration_record,
    _parent_section_index,
    _parse_config,
    _section_record,
    run_legal_responder_raise_h4_factorized_affine,
)
from tests.test_exact_tie_aware_affine_envelope import (
    _CrossingGame,
    _policies,
)


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src" / "pontius" / "legal_responder_raise_h4_factorized_affine.py"


def _config() -> dict[str, object]:
    return json.loads(_CONFIG.read_text(encoding="utf-8"))


class LegalResponderRaiseH4FactorizedAffineTests(unittest.TestCase):
    def test_default_result_path_and_exact_retention_attribute_are_frozen(self) -> None:
        self.assertTrue(_CONFIG.is_file())
        self.assertEqual(
            _OUTPUT,
            ROOT
            / "experiments/results/legal-responder-raise-h4-factorized-affine-v1.json",
        )
        attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8")
        self.assertIn(
            "/experiments/configs/legal-responder-raise-h4-factorized-affine-v1.json -text",
            attributes,
        )
        self.assertIn(
            "/experiments/results/legal-responder-raise-h4-factorized-affine-v1.json -text",
            attributes,
        )

    def test_strict_config_accepts_only_the_frozen_source_boundary(self) -> None:
        config = _config()
        parsed = _parse_config(config)
        self.assertEqual(parsed["expected_parent_protocol_sha256"], config[
            "expected_parent_protocol_sha256"
        ])
        self.assertEqual(parsed["selector_margin_allowance"], 1e-12)
        self.assertEqual(parsed["maximum_tree_nodes"], 100_000)
        self.assertEqual(parsed["maximum_fan_pieces"], 256)
        self.assertEqual(
            parsed["cardinality_columns"],
            ("total_function", "reachable_support"),
        )

        for field, replacement in (
            ("selector_margin_allowance", 0.0),
            ("maximum_tree_nodes", 100_001),
            ("maximum_fan_pieces", 257),
            ("source_tie_mode", "elect_one_tape"),
            ("epigraph_orientation", "z_less_than_or_equal_to_row"),
            ("claims_policy", "production"),
        ):
            with self.subTest(field=field):
                mutated = deepcopy(config)
                mutated[field] = replacement
                with self.assertRaises(ValueError):
                    _parse_config(mutated)

    def test_target_outcomes_cannot_enter_the_gate(self) -> None:
        config = _config()
        mutated = deepcopy(config)
        assert isinstance(mutated["gates"], dict)
        mutated["gates"]["mode_counts"] = {
            FACTOR_TIE_AWARE_MAXIMUM_ENVELOPE: 4,
            V2_SINGLE_TAPE: 4,
        }
        with self.assertRaises(ValueError):
            _parse_config(mutated)

    def test_synthetic_crossing_and_tie_serialize_complete_integration(self) -> None:
        source, endpoint = _policies()
        for tied, expected_mode in (
            (False, V2_SINGLE_TAPE),
            (True, FACTOR_TIE_AWARE_MAXIMUM_ENVELOPE),
        ):
            with self.subTest(tied=tied):
                integrated = build_factorized_tie_aware_affine_section(
                    _CrossingGame(tied=tied),
                    source,
                    endpoint,
                    acting_player=0,
                    target_player=1,
                    selector_margin_allowance=0.0,
                )
                section = _section_record(integrated.section)
                record = _integration_record(
                    integrated,
                    parent_section_sha256=str(section["section_sha256"]),
                )
                self.assertEqual(record["mode"], expected_mode)
                self.assertTrue(
                    all(
                        _integration_checks(
                            record,
                            expected_acting_player=0,
                            expected_target_player=1,
                        ).values()
                    )
                )
                self.assertEqual(record["parent_section_identity"], True)
                self.assertEqual(record["work"]["materialized_response_tapes"], 0)
                self.assertEqual(
                    record["epigraph_orientation"],
                    "z_greater_than_or_equal_to_every_row",
                )
                self.assertEqual(
                    record["exact_envelope_domain"],
                    [
                        {"numerator": 0, "denominator": 1},
                        {"numerator": 1, "denominator": 1},
                    ],
                )

    def test_retained_parent_exposes_exactly_eight_unique_sections(self) -> None:
        parent = verify_adr0356_legal_h4_directional_face_result_artifact()
        index = _parent_section_index(parent.record)
        self.assertEqual(len(index), 8)
        self.assertEqual({target for _, target in index}, {0, 1})
        self.assertTrue(all(len(digest) == 64 for digest in index.values()))

    def test_production_call_graph_excludes_closed_owners_and_cartesian_products(self) -> None:
        tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
        imports = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names
        }
        imported_modules = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module is not None
        }
        named_calls = [
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        ]
        self.assertNotIn("legal_responder_raise_h4_tie_aware_affine", imports)
        self.assertNotIn("legal_responder_raise_h4_directional_face", imports)
        self.assertNotIn(
            "legal_responder_raise_h4_tie_aware_affine",
            imported_modules,
        )
        self.assertNotIn(
            "legal_responder_raise_h4_directional_face",
            imported_modules,
        )
        self.assertNotIn("product", imports | set(named_calls))
        self.assertNotIn("enumerate_exact_local_maximizer_tapes", named_calls)
        self.assertEqual(
            named_calls.count("build_factorized_tie_aware_affine_section"),
            1,
        )
        source_text = SOURCE.read_text(encoding="utf-8")
        self.assertIn("os.O_EXCL", source_text)
        self.assertIn("os.fsync", source_text)

    def test_dirty_git_consumes_a_typed_terminal_before_target_work(self) -> None:
        with TemporaryDirectory() as directory:
            output = Path(directory) / "dirty.json"
            with patch(
                "pontius.legal_responder_raise_h4_factorized_affine._strict_git_metadata",
                return_value={
                    "commit": "0" * 40,
                    "dirty": True,
                    "strict_status": True,
                },
            ), patch(
                "pontius.legal_responder_raise_h4_factorized_affine._execute_factorized_affine",
                side_effect=AssertionError("dirty source must not reach target work"),
            ):
                result = run_legal_responder_raise_h4_factorized_affine(
                    config_path=_CONFIG,
                    output_path=output,
                )
            self.assertFalse(result["passed"])
            self.assertEqual(result["failure"]["stage"], "git_precondition")
            self.assertEqual(result["failure"]["type"], "RuntimeError")
            self.assertTrue(output.is_file())
            self.assertEqual(json.loads(output.read_text(encoding="utf-8")), result)

    def test_malformed_config_consumes_one_terminal_without_target_work(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            config = root / "bad.json"
            config.write_text("{}\n", encoding="utf-8")
            output = root / "failure.json"
            with patch(
                "pontius.legal_responder_raise_h4_factorized_affine._execute_factorized_affine",
                side_effect=AssertionError("invalid config must not reach target work"),
            ):
                result = run_legal_responder_raise_h4_factorized_affine(
                    config_path=config,
                    output_path=output,
                )
            self.assertFalse(result["passed"])
            self.assertEqual(result["failure"]["stage"], "config")
            self.assertTrue(output.is_file())
            with self.assertRaises(FileExistsError):
                run_legal_responder_raise_h4_factorized_affine(
                    config_path=config,
                    output_path=output,
                )

    def test_preexisting_output_is_never_overwritten(self) -> None:
        with TemporaryDirectory() as directory:
            output = Path(directory) / "existing.json"
            original = b"retained-first-terminal\n"
            output.write_bytes(original)
            with self.assertRaises(FileExistsError):
                run_legal_responder_raise_h4_factorized_affine(
                    config_path=_CONFIG,
                    output_path=output,
                )
            self.assertEqual(output.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
