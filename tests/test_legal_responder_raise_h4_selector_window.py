from __future__ import annotations

import ast
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from pontius.legal_h4_selector_directions import (
    LegalH4SelectorDirection,
    compile_legal_h4_selector_directions,
    policy_sha256,
)
from pontius.legal_h4_selector_fixture import (
    build_legal_h4_selector_game,
    legal_h4_source_policy,
)
from pontius.legal_responder_raise_h4_row_growth_result import (
    verify_adr0349_legal_h4_row_growth_result_artifact,
)
from pontius.legal_responder_raise_h4_selector_window import (
    _audit_direction,
    _direction_descriptor,
    _parse_config,
    run_legal_responder_raise_h4_selector_window,
)
from pontius.selector_fan_controls import run_selector_fan_controls


_ROOT = Path(__file__).parents[1]
_CONFIG = (
    _ROOT
    / "experiments/configs/legal-responder-raise-h4-selector-window-v1.json"
)
_RUNNER = _ROOT / "src/pontius/legal_responder_raise_h4_selector_window.py"
_DIRECTION_COMPILER = _ROOT / "src/pontius/legal_h4_selector_directions.py"


class LegalResponderRaiseH4SelectorWindowTests(unittest.TestCase):
    def config(self) -> dict[str, object]:
        return json.loads(_CONFIG.read_text(encoding="utf-8"))

    def parsed(self) -> dict[str, object]:
        return _parse_config(self.config())

    def test_fixture_and_selector_free_direction_inventory_are_frozen(self) -> None:
        parsed = self.parsed()
        parent = verify_adr0349_legal_h4_row_growth_result_artifact()
        game = build_legal_h4_selector_game()
        source = legal_h4_source_policy(game)
        directions = compile_legal_h4_selector_directions(
            game,
            source,
            parent.record,
        )

        self.assertEqual(game.structural_digest, parsed["expected_game_structural_sha256"])
        self.assertEqual(game.provenance_digest, parsed["expected_game_provenance_sha256"])
        self.assertEqual(policy_sha256(source), parsed["expected_source_policy_sha256"])
        self.assertEqual(
            tuple(_direction_descriptor(row) for row in directions),
            parsed["direction_descriptors"],
        )
        self.assertEqual([len(row.changed_public_histories) for row in directions], [1] * 4)
        self.assertEqual(directions[-1].endpoint_policy_sha256, parent.record["final_policy_sha256"])

    def test_only_one_production_selector_call_site_and_compiler_has_none(self) -> None:
        runner = ast.parse(_RUNNER.read_text(encoding="utf-8"))
        compiler = ast.parse(_DIRECTION_COMPILER.read_text(encoding="utf-8"))

        def names(tree: ast.AST) -> list[str]:
            return [
                node.func.id
                for node in ast.walk(tree)
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            ]

        self.assertEqual(names(runner).count("best_response"), 1)
        self.assertNotIn("best_response", names(compiler))
        self.assertNotIn("evaluate_profile", names(compiler))

    def test_three_state_tie_and_identity_semantics_are_binding(self) -> None:
        parsed = self.parsed()
        self.assertEqual(parsed["fan_states"], ("fixed", "tie_unresolved", "switched"))
        self.assertEqual(parsed["certificate_identity_authority"], "total_function_only")
        self.assertIn("positive_support", parsed["reachable_tape_identity"])
        self.assertIn("lebesgue", parsed["tie_measure_semantics"])
        self.assertIn("maximum", parsed["row_envelope_direction"])
        self.assertIn("no_action_clock", parsed["claims_policy"])
        self.assertTrue(parsed["gates"]["require_no_reachable_identity_gate"])

    def test_engineered_control_makes_unresolved_path_reachable(self) -> None:
        control = run_selector_fan_controls()
        self.assertEqual(control["crossing_breakpoint"], control["crossing_legacy_breakpoint"])
        self.assertEqual(control["crossing_breakpoint"].numerator, 1)
        self.assertEqual(control["crossing_breakpoint"].denominator, 2)
        self.assertEqual(control["crossing_tie_points"], (control["crossing_breakpoint"],))
        self.assertEqual(control["degenerate_total_tie_measure"], 1)
        self.assertEqual(control["degenerate_reachable_tie_measure"], 1)

    def test_opened_h1_rehearses_complete_direction_audit(self) -> None:
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
            label="opened_h1_regret_class_control",
            direction_class="one_step_dcfr_regret_vertex",
            changed_public_histories=("root",),
            endpoint_policy_sha256=policy_sha256(endpoint),
            endpoint_policy=endpoint,
        )

        record, metrics = _audit_direction(h1, source, direction, parsed)

        self.assertEqual(len(record["target_rows"]), 2)
        self.assertEqual(metrics["selector_calls"], 34)
        self.assertLessEqual(metrics["maximum_value_error"], 1e-12)
        self.assertLessEqual(metrics["maximum_breakpoint_error"], 1e-12)
        for field in (
            "exact_tape_optimality",
            "unique_selector_agreement",
            "fixed_tape_value_identity",
            "affine_row_activation",
            "upper_envelope_direction",
            "legacy_breakpoint_identity",
            "conservative_total_tape_window",
            "three_state_partition",
            "identity_columns",
        ):
            self.assertTrue(metrics[field], field)

    def test_config_and_gate_mutations_fail_closed(self) -> None:
        config = self.config()
        mutations = []
        wrong_identity = deepcopy(config)
        wrong_identity["certificate_identity_authority"] = "reachable_support"
        mutations.append(wrong_identity)
        missing_state = deepcopy(config)
        missing_state["fan_states"] = ["fixed", "switched"]
        mutations.append(missing_state)
        widened_schedule = deepcopy(config)
        widened_schedule["schedule_numerators"].append(17)
        mutations.append(widened_schedule)
        relaxed_gate = deepcopy(config)
        relaxed_gate["gates"]["maximum_total_seconds"] = 121.0
        mutations.append(relaxed_gate)
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

            result = run_legal_responder_raise_h4_selector_window(config, output)

            self.assertFalse(result["passed"])
            self.assertEqual(result["failure"]["stage"], "config")
            self.assertEqual(result["failure"]["type"], "ValueError")
            self.assertTrue(output.is_file())
            with self.assertRaises(FileExistsError):
                run_legal_responder_raise_h4_selector_window(config, output)


if __name__ == "__main__":
    unittest.main()
