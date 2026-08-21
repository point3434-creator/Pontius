from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import unittest

import numpy as np

from pontius.canonical_affine_resident_automaton_cache import (
    CuPyCanonicalAffineResidentAutomatonCache,
)
from pontius.cupy_sparse_incidence import CuPyBidirectionalIncidence, _cupy_modules
from pontius.h32_action_width_quality_audit import (
    _arm_plan,
    _compile_cache,
    _profile_row,
    _verify_candidate_stream,
    parse_h32_action_width_quality_config,
)
from pontius.leaf_adjoint_cfr import build_leaf_adjoint_terminal_automata
from pontius.multi_size_affine_resident_leaf_adjoint_evaluation import (
    evaluate_multi_size_affine_resident_profile,
)
from pontius.multi_size_policy_bridge import embed_one_size_policy
from pontius.showdown_value_rank_screen import _rank_codes
import tests.test_multi_size_leaf_adjoint as sized_fixture
from tests.test_multi_size_policy_bridge_and_evaluation import _one_size_layout


_ROOT = Path(__file__).parents[1]
_CONFIG = _ROOT / "experiments" / "configs" / "h32-action-width-quality-v1.json"


class H32ActionWidthQualityConfigTests(unittest.TestCase):
    def test_frozen_common_game_budget_and_outcome_neutral_gates(self) -> None:
        config = json.loads(_CONFIG.read_text(encoding="utf-8"))
        parsed = parse_h32_action_width_quality_config(config)
        self.assertEqual(parsed["construction_and_planning_budget_ms"], 90000.0)
        self.assertEqual(parsed["reserved_complete_step_ms"], 35000.0)
        self.assertEqual(parsed["maximum_complete_steps"], 8)
        self.assertEqual(parsed["expected_two_size_payoff_span"], 48.0)
        self.assertEqual(parsed["fixed_seat_order"], tuple(range(6)))
        self.assertNotIn("minimum_quality", parsed["gates"])
        self.assertNotIn("require_two_size_win", parsed["gates"])

    def test_source_budget_and_gate_mutations_are_rejected(self) -> None:
        config = json.loads(_CONFIG.read_text(encoding="utf-8"))
        for mutation in (
            lambda row: row.__setitem__("construction_and_planning_budget_ms", 91000.0),
            lambda row: row.__setitem__("expected_policy_bridge_sha256", "0" * 64),
            lambda row: row["gates"].__setitem__(
                "maximum_quality_zero_sum_residual", 1e-8
            ),
        ):
            changed = copy.deepcopy(config)
            mutation(changed)
            with self.assertRaises(ValueError):
                parse_h32_action_width_quality_config(changed)


@unittest.skipUnless(importlib.util.find_spec("cupy"), "optional CuPy screen")
class H32ActionWidthQualityH2OrchestrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        sized_fixture.MultiSizeLeafAdjointTests.setUpClass()
        cls.source = sized_fixture.MultiSizeLeafAdjointTests
        cls.one_layout = _one_size_layout(cls.source)
        cls.codes = tuple(
            np.ascontiguousarray(values, dtype=np.int32)
            for values in _rank_codes(
                cls.source.belief.board,
                cls.source.belief.hands_by_player,
            )
        )
        cls.one_libraries = build_leaf_adjoint_terminal_automata(
            cls.one_layout,
            cls.codes,
            pot=12.0,
            bet_size=3.0,
        )
        cls.gpu = CuPyBidirectionalIncidence.compile(cls.source.sparse)
        cls.cp, _ = _cupy_modules()
        config = json.loads(_CONFIG.read_text(encoding="utf-8"))
        cls.parsed = parse_h32_action_width_quality_config(config)
        cls.parsed["construction_and_planning_budget_ms"] = 10000.0
        cls.parsed["reserved_complete_step_ms"] = 3000.0
        cls.parsed["maximum_complete_steps"] = 2
        cls.parsed["maximum_feature_width_per_batch"] = 96
        cls.one_blueprint = {}
        cls.sized_blueprint = embed_one_size_policy(
            cls.one_layout,
            cls.source.layout,
            cls.source.belief.hands_by_player,
            cls.one_blueprint,
            retained_bet_size=3.0,
        )

    def test_two_arm_planning_and_sized_envelope_execute_without_labels_in_search(self) -> None:
        rows = {}
        live = {}
        for arm in ("one_size", "two_size"):
            rows[arm], live[arm] = _arm_plan(
                parsed=self.parsed,
                cp=self.cp,
                arm=arm,
                source_workspace=self.source.workspace,
                target_belief=self.source.belief,
                sparse=self.source.sparse,
                gpu=self.gpu,
                one_layout=self.one_layout,
                one_libraries=self.one_libraries,
                sized_layout=self.source.layout,
                sized_libraries=self.source.automata,
                one_blueprint=self.one_blueprint,
                sized_blueprint=self.sized_blueprint,
            )
            self.assertEqual(rows[arm]["completed_steps"], 2)
            self.assertGreaterEqual(len(live[arm]), 2)
            self.assertTrue(all(candidate["compact_round_trip"] for candidate in live[arm]))

        cache_row, belief_cache, caches = _compile_cache(
            self.cp,
            self.source.workspace,
            self.source.automata,
            arm="two_size",
        )
        self.assertEqual(cache_row["shared_affine_bases"], 378)
        self.assertTrue(
            all(isinstance(cache, CuPyCanonicalAffineResidentAutomatonCache) for cache in caches)
        )
        profile = evaluate_multi_size_affine_resident_profile(
            self.source.layout,
            self.source.workspace,
            self.source.sparse,
            self.sized_blueprint,
            self.source.automata,
            belief_cache=belief_cache,
            automaton_caches=caches,
            cupy_sparse=self.gpu,
            hands_by_player=self.source.belief.hands_by_player,
            maximum_feature_width_per_batch=96,
        )
        incumbent = _profile_row(
            "immutable_embedded_blueprint",
            profile,
            payoff_span=48.0,
        )
        selector_incumbent = {
            "candidate_id": incumbent["candidate_id"],
            "aliases": [incumbent["candidate_id"]],
            "quality": incumbent["quality"],
        }
        verified = _verify_candidate_stream(
            parsed=self.parsed,
            layout=self.source.layout,
            workspace=self.source.workspace,
            sparse=self.source.sparse,
            libraries=self.source.automata,
            belief_cache=belief_cache,
            automaton_caches=caches,
            gpu=self.gpu,
            hands_by_player=self.source.belief.hands_by_player,
            incumbent=selector_incumbent,
            candidates=live["two_size"],
        )
        self.assertFalse(verified["selection"]["selected_violating_seats"])
        self.assertEqual(verified["payoff_span_source"], "layout.game.payoff_span")


if __name__ == "__main__":
    unittest.main()
