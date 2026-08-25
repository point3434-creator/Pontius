from __future__ import annotations

import ast
from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from pontius.legal_h4_factorized_affine_confirmation import (
    ConfirmationRejected,
    _CONFIG,
    _OUTPUT,
    _parse_config,
    run_legal_h4_factorized_affine_confirmation,
)


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (
    ROOT / "src" / "pontius" / "legal_h4_factorized_affine_confirmation.py"
)


def _config() -> dict[str, object]:
    return json.loads(_CONFIG.read_text(encoding="utf-8"))


class LegalH4FactorizedAffineConfirmationTests(unittest.TestCase):
    def test_default_paths_and_exact_retention_attributes_are_frozen(self) -> None:
        self.assertTrue(_CONFIG.is_file())
        self.assertEqual(
            _OUTPUT,
            ROOT
            / "experiments/results/legal-h4-factorized-affine-confirmation-v1.json",
        )
        self.assertFalse(_OUTPUT.exists())
        attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8")
        self.assertIn(
            "/experiments/configs/legal-h4-factorized-affine-confirmation-v1.json -text",
            attributes,
        )
        self.assertIn(
            "/experiments/results/legal-h4-factorized-affine-confirmation-v1.json -text",
            attributes,
        )

    def test_strict_config_accepts_only_the_adr0360_boundary(self) -> None:
        config = _config()
        parsed = _parse_config(config)
        self.assertEqual(parsed["expected_context_sha256s"], config[
            "expected_context_sha256s"
        ])
        self.assertEqual(parsed["target_players"], [0, 1])
        self.assertEqual(parsed["maximum_fan_pieces"], 256)
        self.assertEqual(parsed["maximum_tree_nodes"], 100_000)
        self.assertEqual(parsed["selector_margin_allowance"], 1e-12)
        for field, replacement in (
            ("acting_player", 1),
            ("target_players", [1, 0]),
            ("row_growth_guard", 0.5),
            ("row_growth_max_iterations", 129),
            ("row_growth_tolerance", 1e-9),
            ("maximum_fan_pieces", 257),
            ("maximum_tree_nodes", 100_001),
            ("selector_margin_allowance", 0.0),
            ("identity_authority", "reachable_support"),
            ("claims_policy", "production"),
        ):
            with self.subTest(field=field):
                mutated = deepcopy(config)
                mutated[field] = replacement
                with self.assertRaises(ValueError):
                    _parse_config(mutated)

    def test_no_target_observation_can_enter_any_config_nesting(self) -> None:
        config = _config()
        for key, value in (
            ("mode_counts", {"factorized": 32}),
            ("endpoint_policy_sha256", "0" * 64),
            ("maximum_total_function_cardinality", 1),
            ("section_subject_seconds", 0.0),
        ):
            with self.subTest(key=key):
                mutated = deepcopy(config)
                assert isinstance(mutated["gates"], dict)
                mutated["gates"][key] = value
                with self.assertRaises(ValueError):
                    _parse_config(mutated)

    def test_call_graph_has_one_section_builder_and_no_closed_result_owner(self) -> None:
        tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
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
        self.assertNotIn(
            "legal_responder_raise_h4_factorized_affine_result",
            imported_modules,
        )
        self.assertNotIn(
            "legal_responder_raise_h4_factorized_affine",
            imported_modules,
        )
        self.assertNotIn("product", named_calls)
        self.assertNotIn("enumerate_exact_local_maximizer_tapes", named_calls)
        self.assertEqual(
            named_calls.count("build_factorized_tie_aware_affine_section"),
            1,
        )
        self.assertEqual(
            named_calls.count("build_adr0360_confirmation_population"),
            1,
        )
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn("os.O_EXCL", source)
        self.assertIn("os.fsync", source)

    def test_dirty_git_consumes_terminal_before_fresh_target_work(self) -> None:
        with TemporaryDirectory() as directory:
            output = Path(directory) / "dirty.json"
            with patch(
                "pontius.legal_h4_factorized_affine_confirmation._strict_git_metadata",
                return_value={
                    "commit": "0" * 40,
                    "dirty": True,
                    "strict_status": True,
                },
            ), patch(
                "pontius.legal_h4_factorized_affine_confirmation._execute_confirmation",
                side_effect=AssertionError("dirty source reached target work"),
            ):
                result = run_legal_h4_factorized_affine_confirmation(
                    config_path=_CONFIG,
                    output_path=output,
                )
            self.assertFalse(result["passed"])
            self.assertEqual(result["failure"]["stage"], "git_precondition")
            self.assertEqual(result["failure"]["type"], "RuntimeError")
            self.assertEqual(json.loads(output.read_text(encoding="utf-8")), result)

    def test_scientific_rejection_retains_first_partial_record(self) -> None:
        with TemporaryDirectory() as directory:
            output = Path(directory) / "rejected.json"
            rejection = ConfirmationRejected(
                "frozen row-growth rejection",
                {
                    "coordinate": {"context_id": "adr0360-legal-h4-confirmation-00"},
                    "evidence": {"passed": False},
                },
            )
            with patch(
                "pontius.legal_h4_factorized_affine_confirmation._strict_git_metadata",
                return_value={
                    "commit": "0" * 40,
                    "dirty": False,
                    "strict_status": True,
                },
            ), patch(
                "pontius.legal_h4_factorized_affine_confirmation._execute_confirmation",
                side_effect=rejection,
            ):
                result = run_legal_h4_factorized_affine_confirmation(
                    config_path=_CONFIG,
                    output_path=output,
                )
            self.assertFalse(result["passed"])
            self.assertEqual(result["failure"]["type"], "ConfirmationRejected")
            self.assertEqual(
                result["failure"]["scientific_rejection"], rejection.record
            )
            self.assertEqual(json.loads(output.read_text(encoding="utf-8")), result)

    def test_malformed_config_consumes_one_terminal_without_target_work(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            config = root / "bad.json"
            config.write_text("{}\n", encoding="utf-8")
            output = root / "failure.json"
            with patch(
                "pontius.legal_h4_factorized_affine_confirmation._execute_confirmation",
                side_effect=AssertionError("invalid config reached target work"),
            ):
                result = run_legal_h4_factorized_affine_confirmation(
                    config_path=config,
                    output_path=output,
                )
            self.assertFalse(result["passed"])
            self.assertEqual(result["failure"]["stage"], "config")
            with self.assertRaises(FileExistsError):
                run_legal_h4_factorized_affine_confirmation(
                    config_path=config,
                    output_path=output,
                )

    def test_preexisting_output_is_never_overwritten(self) -> None:
        with TemporaryDirectory() as directory:
            output = Path(directory) / "existing.json"
            original = b"retained-first-terminal\n"
            output.write_bytes(original)
            with self.assertRaises(FileExistsError):
                run_legal_h4_factorized_affine_confirmation(
                    config_path=_CONFIG,
                    output_path=output,
                )
            self.assertEqual(output.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
