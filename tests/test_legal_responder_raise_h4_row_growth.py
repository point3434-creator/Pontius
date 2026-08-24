from __future__ import annotations

import ast
from copy import deepcopy
from fractions import Fraction
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import pontius.legal_responder_raise_h4_row_growth as row_growth
from pontius.exact_sequence_form_coefficient_oracle import (
    exact_open_axis_payoff_coefficients,
    exact_sequence_axis,
)
from pontius.legal_responder_raise_h4_row_growth import (
    _build_game,
    _exact_affine_digest,
    _exact_response_row,
    _execute_growth,
    _parse_config,
    _policy_sha256,
    _response_sha256,
    _row_record,
    _source_policy,
    run_legal_responder_raise_h4_row_growth,
)
from pontius.one_seat_row_growth_audit import audit_one_seat_row_growth


_ROOT = Path(__file__).parents[1]
_CONFIG = _ROOT / "experiments/configs/legal-responder-raise-h4-row-growth-v1.json"
_SOURCE = _ROOT / "src/pontius/legal_responder_raise_h4_row_growth.py"


class LegalResponderRaiseH4RowGrowthTests(unittest.TestCase):
    def config(self) -> dict[str, object]:
        return json.loads(_CONFIG.read_text(encoding="utf-8"))

    def parsed(self) -> dict[str, object]:
        return _parse_config(self.config())

    def test_frozen_fixture_is_exactly_adr0347_without_opening_growth(self) -> None:
        parsed = self.parsed()
        game = _build_game(parsed)
        source = _source_policy(game)

        self.assertEqual(game.table_seats, (2, 1))
        self.assertEqual(len(game.deals), 16)
        self.assertEqual(
            game.provenance_digest,
            parsed["expected_h4_game_provenance_sha256"],
        )
        self.assertEqual(_policy_sha256(source), parsed["expected_source_policy_sha256"])
        self.assertEqual(parsed["guard"], 0.25)
        self.assertEqual(parsed["max_iterations"], 128)
        self.assertIn("no_selector_stability", parsed["claims_policy"])

    def test_config_and_gate_mutations_fail_closed(self) -> None:
        config = self.config()
        mutations = []
        changed_parent = deepcopy(config)
        changed_parent["expected_parent_artifact_sha256"] = "0" * 64
        mutations.append(changed_parent)
        changed_guard = deepcopy(config)
        changed_guard["guard"] = 0.5
        mutations.append(changed_guard)
        changed_dedup = deepcopy(config)
        changed_dedup["response_signature_identity"] = "digest_only"
        mutations.append(changed_dedup)
        changed_gate = deepcopy(config)
        changed_gate["gates"]["maximum_total_seconds"] = 121.0
        mutations.append(changed_gate)
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                with self.assertRaises(ValueError):
                    _parse_config(mutation)

    def test_runner_has_one_subject_call_and_no_out_of_band_selector(self) -> None:
        tree = ast.parse(_SOURCE.read_text(encoding="utf-8"))
        calls = [
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        ]
        self.assertEqual(calls.count("audit_one_seat_row_growth"), 1)
        self.assertNotIn("solve_one_seat_with_row_generation", calls)
        self.assertNotIn("best_response", calls)

    def test_generic_h1_row_serialization_binds_exact_fraction_coefficients(self) -> None:
        parsed = self.parsed()
        game = _build_game(parsed)
        # Use one already-opened deal and the uniform fallback so this control
        # cannot reveal the frozen h4 target trajectory.
        h1 = type(game)(
            board=game.board,
            base_state=game.base_state,
            deals=((game.deals[0][0], 1.0),),
        )
        h1_source = _source_policy(h1)
        audit = audit_one_seat_row_growth(
            h1,
            h1_source,
            acting_player=0,
            guard=0.25,
            max_iterations=128,
            tolerance=1e-10,
        )
        exact_profile = tuple(
            exact_open_axis_payoff_coefficients(
                h1,
                h1_source,
                acting_player=0,
                payoff_player=player,
            )
            for player in range(h1.num_players)
        )
        exact_axis = exact_sequence_axis(h1, 0)
        exact = _exact_response_row(
            h1,
            h1_source,
            0,
            exact_profile,
            audit.response_rows[0],
        )
        record, retained_bytes, error, identity = _row_record(
            audit.response_rows[0],
            exact,
            exact_axis.variables,
        )

        self.assertTrue(identity)
        self.assertEqual(error, 0.0)
        self.assertGreater(retained_bytes, 0)
        self.assertEqual(record["retained_bytes"], retained_bytes)
        self.assertEqual(
            Fraction.from_float(audit.response_rows[0].gain.constant),
            Fraction(
                record["constant_exact"]["numerator"],
                record["constant_exact"]["denominator"],
            ),
        )

    def test_failure_terminal_is_typed_and_exclusive(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = root / "invalid.json"
            config.write_text('{"unexpected":true}\n', encoding="utf-8")
            output = root / "result.json"

            result = run_legal_responder_raise_h4_row_growth(config, output)

            self.assertFalse(result["passed"])
            self.assertEqual(result["failure"]["stage"], "config")
            self.assertEqual(result["failure"]["type"], "ValueError")
            self.assertTrue(output.is_file())
            with self.assertRaises(FileExistsError):
                run_legal_responder_raise_h4_row_growth(config, output)

    def test_complete_success_path_rehearses_only_the_opened_h1_fixture(self) -> None:
        parsed = self.parsed()
        h4 = _build_game(parsed)
        h1 = type(h4)(
            board=h4.board,
            base_state=h4.base_state,
            deals=((h4.deals[0][0], 1.0),),
        )
        source = _source_policy(h1)
        audit = audit_one_seat_row_growth(
            h1,
            source,
            acting_player=0,
            guard=0.25,
            max_iterations=128,
            tolerance=1e-10,
        )
        exact_profile = tuple(
            exact_open_axis_payoff_coefficients(
                h1,
                source,
                acting_player=0,
                payoff_player=player,
            )
            for player in range(h1.num_players)
        )
        initial = tuple(row for row in audit.response_rows if row.phase == "initial")
        exact_initial = tuple(
            _exact_response_row(h1, source, 0, exact_profile, row) for row in initial
        )
        rehearsal = dict(parsed)
        rehearsal.update(
            {
                "expected_public_schema_sha256": "h1-opened-control",
                "expected_game_structural_sha256": h1.structural_digest,
                "expected_h4_game_provenance_sha256": h1.provenance_digest,
                "expected_source_policy_sha256": _policy_sha256(source),
                "expected_initial_response_sha256s": tuple(
                    _response_sha256(row.signature) for row in initial
                ),
                "expected_initial_exact_row_sha256s": tuple(
                    _exact_affine_digest(row) for row in exact_initial
                ),
            }
        )
        gates = dict(rehearsal["gates"])
        gates.update(
            {
                "expected_hand_counts": [1, 1],
                "expected_joint_deals": 1,
                "expected_terminal_paths": 11,
                "expected_acting_information_sets": 3,
                "expected_sequence_variables": 8,
            }
        )
        rehearsal["gates"] = gates
        parent = SimpleNamespace(
            record={"public_schema_sha256": "h1-opened-control", "passed": True}
        )
        with (
            patch.object(row_growth, "_build_game", return_value=h1),
            patch.object(row_growth, "_source_policy", return_value=source),
            patch.object(
                row_growth,
                "verify_adr0347_legal_h4_coefficient_result_artifact",
                return_value=parent,
            ),
        ):
            result = _execute_growth(
                rehearsal,
                git={"dirty": False},
            )

        self.assertTrue(result["passed"])
        self.assertEqual(result["fixture"]["hand_counts"], [1, 1])
        self.assertEqual(result["response_rows_by_player"], [1, 1])
        self.assertTrue(result["oracle_accounting"]["identity"])
        self.assertEqual(result["maximum_float_exact_row_error"], 0.0)
        self.assertGreater(result["retained_row_bytes"], 0)


if __name__ == "__main__":
    unittest.main()
