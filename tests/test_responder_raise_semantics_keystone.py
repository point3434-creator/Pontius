from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from pontius.legal_decision_spine_v2 import public_betting_state_sha256
from pontius.legal_river_continuation import LegalHeadsUpRiverContinuation
from pontius.responder_raise_semantics_keystone import (
    _checked_to_river,
    _legacy_short_all_in_omission,
    _parse_config,
    _public_semantics,
    _write_exclusive,
)
from pontius.river import RiverDeal, make_hole, parse_cards


_ROOT = Path(__file__).parents[1]
_CONFIG = _ROOT / "experiments/configs/responder-raise-semantics-keystone-v1.json"


class ResponderRaiseSemanticsKeystoneTests(unittest.TestCase):
    def parsed(self) -> dict[str, object]:
        return _parse_config(json.loads(_CONFIG.read_text(encoding="utf-8")))

    def game(self, parsed: dict[str, object]) -> LegalHeadsUpRiverContinuation:
        deal = RiverDeal(
            make_hole(*parsed["root_hand"]),  # type: ignore[arg-type]
            make_hole(*parsed["responder_hand"]),  # type: ignore[arg-type]
        )
        return LegalHeadsUpRiverContinuation(
            board=parse_cards(*parsed["board"]),  # type: ignore[arg-type]
            base_state=_checked_to_river(parsed),
            deals=((deal, 1.0),),
        )

    def test_frozen_config_names_only_the_small_semantic_keystone(self) -> None:
        parsed = self.parsed()

        self.assertEqual(parsed["acting_player"], 0)
        self.assertEqual(parsed["expected_root_raise_to_totals"], (2, 3, 4))
        self.assertEqual(parsed["gates"]["expected_acting_pure_plans"], 16)  # type: ignore[index]
        self.assertEqual(parsed["gates"]["expected_response_pure_plans"], 18)  # type: ignore[index]
        self.assertIn("no_quality", parsed["claims_policy"])

    def test_public_schema_includes_the_short_all_in_branch(self) -> None:
        parsed = self.parsed()
        game = self.game(parsed)
        semantics = _public_semantics(game)

        self.assertEqual(
            public_betting_state_sha256(game.base_state),
            parsed["expected_root_public_state_sha256"],
        )
        self.assertEqual(
            semantics["public_schema_sha256"],
            parsed["expected_public_schema_sha256"],
        )
        self.assertEqual(semantics["strategic_nodes"], 6)
        self.assertEqual(semantics["terminal_nodes"], 11)
        self.assertEqual(semantics["full_raise_branches"], 1)
        self.assertEqual(semantics["short_all_in_raise_branches"], 1)
        self.assertTrue(semantics["short_all_in_final_response_only"])
        self.assertEqual(semantics["maximum_terminal_oracle_error_chips"], 0.0)
        self.assertTrue(_legacy_short_all_in_omission(parsed, game.deals[0][0]))

    def test_provenance_and_gate_mutations_fail_closed(self) -> None:
        config = json.loads(_CONFIG.read_text(encoding="utf-8"))
        mutations = []
        changed_hash = deepcopy(config)
        changed_hash["expected_legal_game_sha256"] = "0" * 64
        mutations.append(changed_hash)
        changed_amount = deepcopy(config)
        changed_amount["expected_root_raise_to_totals"] = [2, 4]
        mutations.append(changed_amount)
        changed_gate = deepcopy(config)
        changed_gate["gates"]["maximum_teacher_objective_error"] = 1e-8
        mutations.append(changed_gate)
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                with self.assertRaises(ValueError):
                    _parse_config(mutation)

    def test_result_writer_is_exclusive(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "result.json"
            _write_exclusive(path, "first\n")
            self.assertEqual(path.read_text(encoding="utf-8"), "first\n")
            with self.assertRaises(FileExistsError):
                _write_exclusive(path, "second\n")


if __name__ == "__main__":
    unittest.main()
