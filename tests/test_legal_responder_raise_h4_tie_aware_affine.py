from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import pontius.legal_responder_raise_h4_tie_aware_affine as _runner_module
from pontius.legal_responder_raise_h4_tie_aware_affine import (
    _CONFIG,
    _OUTPUT,
    _audit_section,
    _identity_comparison,
    _parse_config,
    run_legal_responder_raise_h4_tie_aware_affine,
)
from tests.test_exact_tie_aware_affine_envelope import _CrossingGame, _policies


_ROOT = Path(__file__).parents[1]
_SOURCE = (
    _ROOT / "src/pontius/legal_responder_raise_h4_tie_aware_affine.py"
)
_HISTORICAL_CONTROL_SHA256 = (
    "dd691d01b271dfabb599a68df338602286e304287f35b7ae6fc1fc0a8709d92e"
)
_ORIGINAL_SHA256 = _runner_module._sha256


def _parse_as_invocation_source(config: dict[str, object]) -> dict[str, object]:
    """Reproduce config parsing against the sealed historical control hash."""

    def historical_sha256(path: Path) -> str:
        if path.resolve() == Path(__file__).resolve():
            return _HISTORICAL_CONTROL_SHA256
        return _ORIGINAL_SHA256(path)

    with patch.object(_runner_module, "_sha256", side_effect=historical_sha256):
        return _parse_config(config)


class LegalResponderRaiseH4TieAwareAffineTests(unittest.TestCase):
    def test_frozen_config_parses_without_invoking_closed_target(self) -> None:
        parsed = _parse_as_invocation_source(
            json.loads(_CONFIG.read_text(encoding="utf-8"))
        )
        self.assertEqual(
            parsed["evidence_stage"],
            "preregistered_after_adr0351_before_tie_aware_h4_run",
        )
        self.assertEqual(parsed["certificate_identity_authority"], "total_function_only")
        self.assertEqual(parsed["reachable_identity_role"], "reporting_only")
        self.assertEqual(
            parsed["same_fixture_evidence_scope"],
            "development_integration_only_not_untouched_confirmation",
        )
        raw = _OUTPUT.read_bytes()
        self.assertEqual(len(raw), 961)
        self.assertEqual(
            hashlib.sha256(raw).hexdigest(),
            "7608abd221114ed6143aa7fbf9af510a09024442f85fd8f4f3f5ed53e036f652",
        )

    def test_config_has_no_outcome_dependent_tie_or_row_gate(self) -> None:
        config = json.loads(_CONFIG.read_text(encoding="utf-8"))
        gates = config["gates"]
        forbidden = {
            "expected_source_active_tapes",
            "expected_affine_rows",
            "expected_tie_sections",
            "expected_equivalence_classes",
            "minimum_single_tape_scale",
        }
        self.assertFalse(forbidden & set(gates))
        self.assertIn(
            "alternate_source_tape_endpoint_equivalence",
            config["reconnaissance_disclosure"],
        )

    def test_config_and_source_hash_mutations_fail_closed(self) -> None:
        config = json.loads(_CONFIG.read_text(encoding="utf-8"))
        mutated = dict(config)
        mutated["certificate_identity_authority"] = "reachable_support"
        with self.assertRaises(ValueError):
            _parse_as_invocation_source(mutated)
        mutated = dict(config)
        mutated["expected_exact_tie_envelope_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            _parse_as_invocation_source(mutated)

    def test_identity_record_serializes_both_pruned_tapes(self) -> None:
        source_total = (("root", "stop"), ("child", "first"))
        current_total = (("root", "stop"), ("child", "second"))
        source_pruned = (("root", "stop"),)
        current_pruned = (("root", "stop"),)
        record = _identity_comparison(
            source_total,
            source_pruned,
            current_total,
            current_pruned,
        )
        self.assertFalse(record["total_identity"])
        self.assertTrue(record["reachable_identity"])
        self.assertEqual(record["current_unreachable_entry_changes"], 1)
        self.assertEqual(
            record["source_pruned_tape"],
            [{"information_key": "root", "action": "stop"}],
        )
        self.assertEqual(record["current_pruned_tape"], record["source_pruned_tape"])

    def test_synthetic_integration_selects_singleton_and_tie_modes(self) -> None:
        source, endpoint = _policies()
        parsed = {
            "maximum_fan_tapes": 16,
            "maximum_active_tapes_per_sample": 16,
            "maximum_affine_rows": 16,
            "selector_margin_allowance": 0.0,
            "schedule_numerators": (0, 1, 2),
            "schedule_denominator": 2,
        }
        singleton, singleton_metrics = _audit_section(
            _CrossingGame(),
            source,
            endpoint,
            acting_player=0,
            target_player=1,
            parsed=parsed,
        )
        tied, tied_metrics = _audit_section(
            _CrossingGame(tied=True),
            source,
            endpoint,
            acting_player=0,
            target_player=1,
            parsed=parsed,
        )
        self.assertEqual(singleton["integration_mode"], "v2_single_tape")
        self.assertEqual(tied["integration_mode"], "tie_aware_maximum_envelope")
        for metrics in (singleton_metrics, tied_metrics):
            for field in (
                "active_closure",
                "tie_mode_honest",
                "tie_fail_closed",
                "envelope_identity",
                "epigraph_direction",
                "pruned_tapes_complete",
            ):
                self.assertTrue(metrics[field])
            self.assertEqual(metrics["maximum_row_error"], 0.0)
        for record in tied["schedule"]:
            self.assertTrue(record["identity_comparisons"])
            self.assertIn("source_pruned_tape", record["identity_comparisons"][0])
            self.assertIn("current_pruned_tape", record["identity_comparisons"][0])

    def test_runner_has_no_production_selector_or_closed_runner_import(self) -> None:
        tree = ast.parse(_SOURCE.read_text(encoding="utf-8"))
        imports = set()
        calls = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                imports.add(node.module)
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    calls.append(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    calls.append(node.func.attr)
        self.assertNotIn("pontius.evaluation", imports)
        self.assertNotIn("evaluation", imports)
        self.assertNotIn("pontius.legal_responder_raise_h4_selector_window", imports)
        self.assertNotIn("legal_responder_raise_h4_selector_window", imports)
        self.assertNotIn("best_response", calls)
        self.assertEqual(calls.count("build_exact_tie_aware_affine_section"), 1)
        self.assertEqual(calls.count("fixed_response_selector_scores"), 2)
        self.assertEqual(calls.count("choose_tie_aware_affine_mode"), 1)

    def test_failure_terminal_is_typed_and_exclusive(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = root / "invalid.json"
            output = root / "result.json"
            config.write_text("{}\n", encoding="utf-8")
            result = run_legal_responder_raise_h4_tie_aware_affine(config, output)
            self.assertFalse(result["passed"])
            self.assertEqual(result["failure"]["stage"], "config")
            self.assertTrue(output.is_file())
            with self.assertRaises(FileExistsError):
                run_legal_responder_raise_h4_tie_aware_affine(config, output)


if __name__ == "__main__":
    unittest.main()
