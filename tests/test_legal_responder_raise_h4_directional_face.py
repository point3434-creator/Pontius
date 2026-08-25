from __future__ import annotations

import ast
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pontius.legal_h4_selector_directions import (
    LegalH4SelectorDirection,
    compile_legal_h4_selector_directions,
    policy_sha256,
)
from pontius.legal_h4_selector_fixture import (
    build_legal_h4_selector_game,
    legal_h4_source_policy,
)
from pontius.legal_responder_raise_h4_directional_face import (
    _audit_section,
    _direction_descriptor,
    _parse_config,
    run_legal_responder_raise_h4_directional_face,
)
from pontius.legal_responder_raise_h4_row_growth_result import (
    verify_adr0349_legal_h4_row_growth_result_artifact,
)


_ROOT = Path(__file__).parents[1]
_CONFIG = (
    _ROOT
    / "experiments/configs/legal-responder-raise-h4-directional-face-v1.json"
)
_RUNNER = _ROOT / "src/pontius/legal_responder_raise_h4_directional_face.py"


class LegalResponderRaiseH4DirectionalFaceTests(unittest.TestCase):
    def config(self) -> dict[str, object]:
        return json.loads(_CONFIG.read_text(encoding="utf-8"))

    def parsed(self) -> dict[str, object]:
        return _parse_config(self.config())

    def test_fixture_and_four_prior_directions_are_frozen_without_face_calls(
        self,
    ) -> None:
        parsed = self.parsed()
        parent = verify_adr0349_legal_h4_row_growth_result_artifact()
        game = build_legal_h4_selector_game()
        source = legal_h4_source_policy(game)
        directions = compile_legal_h4_selector_directions(
            game,
            source,
            parent.record,
        )
        self.assertEqual(
            tuple(_direction_descriptor(row) for row in directions),
            parsed["direction_descriptors"],
        )
        self.assertEqual(len(directions), 4)
        self.assertEqual([len(row.changed_public_histories) for row in directions], [1] * 4)
        self.assertEqual(policy_sha256(source), parsed["expected_source_policy_sha256"])

    def test_config_has_no_face_cardinality_or_target_outcome_gate(self) -> None:
        parsed = self.parsed()
        self.assertEqual(
            parsed["cardinality_columns"],
            ("total_function", "reachable_support"),
        )
        self.assertEqual(parsed["face_instrument"], "two_independent_lexicographic_backward_passes")
        self.assertEqual(
            parsed["analysis_wall_semantics"],
            "execute_entry_through_scientific_payload_materialization_"
            "excluding_gate_evaluation_result_render_fsync_and_process_overhead",
        )
        self.assertIn("maximum_analysis_seconds", parsed["gates"])
        self.assertNotIn("maximum_prewrite_seconds", parsed["gates"])
        self.assertNotIn("maximum_face_tapes", parsed)
        self.assertNotIn("maximum_face_cardinality", parsed)
        for field in (
            "crossings",
            "maximum_total_function_cardinality",
            "maximum_reachable_support_cardinality",
            "maximum_total_cardinality_bit_length",
            "maximum_reachable_cardinality_bit_length",
        ):
            self.assertNotIn(field, parsed["gates"])
            self.assertNotIn(f"expected_{field}", parsed["gates"])

    def test_runner_has_no_closed_owner_or_cartesian_materializer(self) -> None:
        tree = ast.parse(_RUNNER.read_text(encoding="utf-8"))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.add(node.module or "")
                imports.update(alias.name for alias in node.names)
        calls = [
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        ]
        self.assertFalse(
            any("legal_responder_raise_h4_tie_aware_affine" in name for name in imports)
        )
        self.assertNotIn("product", calls)
        self.assertNotIn("build_exact_tie_aware_affine_section", calls)
        self.assertNotIn("best_response", calls)
        self.assertEqual(calls.count("compose_exact_directional_face_fan_section"), 1)
        self.assertEqual(calls.count("exact_directional_best_response_face"), 1)

    def test_opened_h1_rehearses_complete_composed_and_schedule_schema(self) -> None:
        parsed = self.parsed()
        h4 = build_legal_h4_selector_game()
        h1 = type(h4)(
            board=h4.board,
            base_state=h4.base_state,
            deals=((h4.deals[0][0], 1.0),),
        )
        source = legal_h4_source_policy(h1)
        endpoint = {key: dict(row) for key, row in source.items()}
        changed = []
        for key, row in source.items():
            if "|p0|" not in key or not key.endswith("history=root"):
                continue
            actions = tuple(row)
            endpoint[key] = {
                action: float(index == 0) for index, action in enumerate(actions)
            }
            changed.append(key)
        self.assertEqual(len(changed), 1)
        direction = LegalH4SelectorDirection(
            label="opened_h1_directional_face_control",
            direction_class="one_step_dcfr_regret_vertex",
            changed_public_histories=("root",),
            endpoint_policy_sha256=policy_sha256(endpoint),
            endpoint_policy=endpoint,
        )

        record, metrics = _audit_section(
            h1,
            source,
            direction,
            target_player=1,
            parsed=parsed,
        )

        self.assertEqual(len(record["schedule"]), 17)
        self.assertGreater(len(record["composed_section"]["samples"]), 0)
        self.assertEqual(metrics["schedule_face_calls"], 17)
        self.assertEqual(metrics["materialized_response_tapes"], 0)
        self.assertGreaterEqual(metrics["maximum_total_function_cardinality"], 1)
        self.assertTrue(all(record["checks"].values()))
        for row in record["schedule"]:
            self.assertEqual(row["face"]["work"]["lexicographic_passes"], 2)
            self.assertEqual(row["face"]["work"]["materialized_response_tapes"], 0)

    def test_config_and_gate_mutations_fail_closed(self) -> None:
        config = self.config()
        mutations = []
        bounded_face = deepcopy(config)
        bounded_face["maximum_face_tapes"] = 1024
        mutations.append(bounded_face)
        shared_pass = deepcopy(config)
        shared_pass["face_instrument"] = "one_shared_lexicographic_pass"
        mutations.append(shared_pass)
        collapsed_cardinality = deepcopy(config)
        collapsed_cardinality["cardinality_columns"] = ["reachable_support"]
        mutations.append(collapsed_cardinality)
        relaxed_tree = deepcopy(config)
        relaxed_tree["maximum_tree_nodes"] = 100_001
        mutations.append(relaxed_tree)
        outcome_gate = deepcopy(config)
        outcome_gate["gates"]["expected_crossings"] = 4
        mutations.append(outcome_gate)
        cell_gate = deepcopy(config)
        cell_gate["gates"]["expected_fan_cells"] = 8
        mutations.append(cell_gate)
        slope_gate = deepcopy(config)
        slope_gate["gates"]["expected_minimum_gain_slope"] = 0
        mutations.append(slope_gate)
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                with self.assertRaises(ValueError):
                    _parse_config(mutation)

    def test_failure_terminal_is_typed_and_exclusive(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = root / "invalid.json"
            config.write_text('{"unexpected":true}\n', encoding="utf-8")
            output = root / "result.json"

            result = run_legal_responder_raise_h4_directional_face(config, output)

            self.assertFalse(result["passed"])
            self.assertEqual(result["failure"]["stage"], "config")
            self.assertEqual(result["failure"]["type"], "ValueError")
            self.assertIsNone(result["config_sha256"])
            self.assertTrue(output.is_file())
            with self.assertRaises(FileExistsError):
                run_legal_responder_raise_h4_directional_face(config, output)

    def test_dirty_git_consumes_a_typed_terminal_before_target_work(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "result.json"
            git = {"available": True, "dirty": True, "commit": "dirty-control"}
            execute = (
                "pontius.legal_responder_raise_h4_directional_face."
                "_execute_directional_face"
            )
            metadata = (
                "pontius.legal_responder_raise_h4_directional_face."
                "_strict_git_metadata"
            )
            with patch(metadata, return_value=git), patch(execute) as subject:
                result = run_legal_responder_raise_h4_directional_face(
                    _CONFIG,
                    output,
                )

            self.assertFalse(result["passed"])
            self.assertEqual(result["failure"]["stage"], "git")
            self.assertEqual(result["failure"]["type"], "RuntimeError")
            subject.assert_not_called()
            self.assertTrue(output.is_file())


if __name__ == "__main__":
    unittest.main()
