from __future__ import annotations

import ast
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from pontius.exact_sequence_form_coefficient_oracle import exact_sequence_axis
from pontius.legal_responder_raise_h4_coefficient_differential import (
    _build_game,
    _coverage_response,
    _endpoint_policies,
    _execute_differential,
    _parse_config,
    _policy_sha256,
    _response_sha256,
    _source_policy,
    _tree_terminal_paths,
    run_legal_responder_raise_h4_coefficient_differential,
)
from pontius.no_limit_betting import CALL, FOLD, raise_to
from pontius.one_seat_convex_generation import (
    _sequence_axis,
    path_single_visit_report,
)


_ROOT = Path(__file__).parents[1]
_CONFIG = (
    _ROOT
    / "experiments/configs/legal-responder-raise-h4-coefficient-differential-v1.json"
)
_SOURCE = (
    _ROOT / "src/pontius/legal_responder_raise_h4_coefficient_differential.py"
)


class LegalResponderRaiseH4CoefficientDifferentialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.raw_config = json.loads(_CONFIG.read_text(encoding="utf-8"))
        cls.parsed = _parse_config(cls.raw_config)
        cls.game = _build_game(cls.parsed)
        cls.result = _execute_differential(
            cls.parsed,
            git={"dirty": False, "commit": "synthetic-control"},
        )

    def test_config_freezes_h4_without_widening_the_claim(self) -> None:
        self.assertEqual(self.parsed["acting_player"], 0)
        self.assertEqual(len(self.parsed["root_hands"]), 4)
        self.assertEqual(len(self.parsed["responder_hands"]), 4)
        self.assertEqual(sum(map(sum, self.parsed["joint_weight_numerators"])), 32)
        self.assertEqual(
            self.parsed["endpoint_labels"],
            (
                "source",
                "check_fold",
                "bet2_call",
                "bet3_fold",
                "bet3_call",
                "all_in_call",
            ),
        )
        self.assertIn("no_selector_capacity_latency", self.parsed["claims_policy"])

    def test_fixture_is_exact_h4_on_the_adr0345_public_tree(self) -> None:
        game = self.game
        hands = [
            {deal.hand(player) for deal, _ in game.deals}
            for player in range(game.num_players)
        ]
        self.assertEqual(tuple(map(len, hands)), (4, 4))
        self.assertEqual(len(game.deals), 16)
        self.assertEqual(_tree_terminal_paths(game), 176)
        self.assertEqual(
            game.provenance_digest,
            self.parsed["expected_h4_game_provenance_sha256"],
        )
        float_axis = _sequence_axis(game, 0)
        exact_axis = exact_sequence_axis(game, 0)
        self.assertEqual(len(float_axis.information_sets), 12)
        self.assertEqual(len(float_axis.variables), 32)
        self.assertEqual(set(float_axis.variables), set(exact_axis.variables))
        self.assertFalse(path_single_visit_report(game).passed)

    def test_frozen_policies_bind_endpoints_and_both_raise_classes(self) -> None:
        source = _source_policy(self.game)
        endpoints = _endpoint_policies(self.game, source)
        coverage = _coverage_response(self.game)
        self.assertEqual(
            _policy_sha256(source),
            self.parsed["expected_source_policy_sha256"],
        )
        self.assertEqual(
            tuple(_policy_sha256(policy) for _, policy in endpoints),
            self.parsed["expected_endpoint_policy_sha256s"],
        )
        self.assertEqual(
            _response_sha256(coverage),
            self.parsed["expected_coverage_response_sha256"],
        )
        self.assertEqual(sum(action == raise_to(4) for action in coverage.values()), 8)
        self.assertEqual(sum(action == FOLD for action in coverage.values()), 2)
        self.assertEqual(sum(action == CALL for action in coverage.values()), 2)

    def test_fraction_teacher_matches_every_subject_row_and_endpoint(self) -> None:
        result = self.result
        self.assertTrue(result["passed"])
        self.assertEqual(
            result["decision"],
            "authorize_legal_responder_raise_h4_row_growth_preregistration",
        )
        self.assertEqual(len(result["payoff_rows"]), 4)
        self.assertEqual(len(result["gain_rows"]), 2)
        self.assertTrue(all(row["coefficient_entries"] == 32 for row in result["payoff_rows"]))
        self.assertTrue(all(row["coefficient_entries"] == 32 for row in result["gain_rows"]))
        self.assertEqual(result["coverage_nonzero_final_histories"], ["raise-to-2", "raise-to-3"])
        self.assertEqual(result["exact_affine_identity_mismatches"], 0)
        self.assertEqual(result["exact_gain_identity_mismatches"], 0)
        self.assertLessEqual(result["maximum_coefficient_error"], 1e-12)
        self.assertLessEqual(result["maximum_realization_error"], 1e-12)
        self.assertLessEqual(result["maximum_affine_value_error"], 1e-12)
        self.assertLessEqual(result["maximum_gain_value_error"], 1e-12)
        self.assertLessEqual(result["maximum_float_exact_utility_error"], 1e-12)
        self.assertEqual(result["endpoint_responder_selector_calls"], 0)
        self.assertTrue(result["fixture"]["chance_probabilities_dyadic"])
        self.assertTrue(result["gates"]["source_response_tape_identities"])
        self.assertTrue(all(result["gates"].values()))
        self.assertEqual(result["strategy_labels_generated"], 0)
        self.assertEqual(result["quality_rows_serialized"], 0)

    def test_provenance_policy_and_tolerance_mutations_fail_closed(self) -> None:
        mutations = []
        source = deepcopy(self.raw_config)
        source["expected_exact_oracle_sha256"] = "0" * 64
        mutations.append(source)
        tolerance = deepcopy(self.raw_config)
        tolerance["tolerance"] = 1e-9
        mutations.append(tolerance)
        gate = deepcopy(self.raw_config)
        gate["gates"]["maximum_coefficient_error"] = 1e-9
        mutations.append(gate)
        for mutation in mutations:
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                _parse_config(mutation)

        policy = deepcopy(self.raw_config)
        policy["expected_source_policy_sha256"] = "0" * 64
        parsed = _parse_config(policy)
        result = _execute_differential(
            parsed,
            git={"dirty": False, "commit": "synthetic-control"},
        )
        self.assertFalse(result["passed"])
        self.assertFalse(result["gates"]["source_policy_identity"])

    def test_public_runner_retains_typed_failure_and_never_clobbers(self) -> None:
        mutation = deepcopy(self.raw_config)
        mutation["tolerance"] = 1e-9
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = root / "config.json"
            output = root / "result.json"
            config.write_text(
                json.dumps(mutation),
                encoding="utf-8",
                newline="\n",
            )
            result = run_legal_responder_raise_h4_coefficient_differential(
                config,
                output,
            )
            retained = json.loads(output.read_text(encoding="utf-8"))
            self.assertFalse(result["passed"])
            self.assertEqual(retained["failure"]["stage"], "config")
            self.assertEqual(retained["failure"]["type"], "ValueError")
            with self.assertRaises(FileExistsError):
                run_legal_responder_raise_h4_coefficient_differential(
                    config,
                    output,
                )

    def test_runner_has_one_subject_and_teacher_callsite_and_no_optimizer(self) -> None:
        tree = ast.parse(_SOURCE.read_text(encoding="utf-8"))
        calls = [
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        ]
        attributes = {
            node.func.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        }
        self.assertEqual(calls.count("open_axis_payoff_coefficients"), 1)
        self.assertEqual(calls.count("exact_open_axis_payoff_coefficients"), 1)
        self.assertEqual(calls.count("best_response"), 2)
        self.assertNotIn("maximize_linear_program", calls)
        self.assertNotIn("solve_one_seat_with_row_generation", calls)
        self.assertNotIn("linprog", set(calls) | attributes)


if __name__ == "__main__":
    unittest.main()
