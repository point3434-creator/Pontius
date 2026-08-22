from __future__ import annotations

import gc
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest

from pontius.canonical_affine_resident_automaton_cache import (
    CuPyCanonicalAffineResidentAutomatonCache,
)
from pontius.cupy_sparse_incidence import (
    CuPyBidirectionalIncidence,
    release_cupy_memory_pool,
)
from pontius.h32_pre_bet_action_width_capacity import (
    _master_telemetry,
    _parse_config,
    _runtime_arm,
    derive_capacity_proxy,
    pre_bet_check_observations,
    target_specs,
)
from pontius.leaf_adjoint_cfr import build_leaf_adjoint_terminal_automata
from pontius.multi_size_policy_bridge import embed_one_size_policy, sized_policy_digest
from pontius.public_policy_tt import information_schema_for_axes
from pontius.public_tree_tensor import PublicTreeTensorEvaluator
from pontius.real_policy import policy_digest
from pontius.resident_heterogeneous_leaf_contraction import CuPyResidentAutomatonCache
from pontius.river_multiway import MultiwayRiverDeal, MultiwayRiverHoldem
import tests.test_multi_size_leaf_adjoint as sized_fixture


ROOT = Path(__file__).parents[1]
CONFIG = ROOT / "experiments/configs/h32-pre-bet-action-width-capacity-v1.json"


class H32PreBetActionWidthCapacityTests(unittest.TestCase):
    def test_config_freezes_all_sources_crossed_with_all_positions(self) -> None:
        parsed = _parse_config(json.loads(CONFIG.read_text(encoding="utf-8")))
        specs = target_specs(parsed)
        self.assertEqual(len(specs), 36)
        self.assertEqual(
            [row["acting_player"] for row in specs[:6]],
            list(range(6)),
        )
        self.assertEqual(len({row["target_id"] for row in specs}), 36)
        self.assertEqual(parsed["gates"]["expected_arms"], 72)
        self.assertIn("zero_master_candidate", parsed["candidate_label_rule"])

    def test_check_prefix_is_empty_for_opener_and_complete_for_last_actor(self) -> None:
        self.assertEqual(pre_bet_check_observations(0), ())
        rows = pre_bet_check_observations(5)
        self.assertEqual([row["actor"] for row in rows], list(range(5)))
        self.assertTrue(all(row["action"] == "check" for row in rows))
        self.assertEqual(rows[0]["public_history"], "root")
        self.assertEqual(
            rows[-1]["public_history"],
            "p0:check/p1:check/p2:check/p3:check",
        )

    def test_capacity_proxy_prices_two_oracles_and_frozen_reserves(self) -> None:
        row = derive_capacity_proxy(
            warm_step_ms=1000.0,
            initial_row_ms=2000.0,
            first_master_ms=3.0,
            source_oracle_ms=800.0,
            five_cut_row_proxy_ms=500.0,
            second_master_reserve_ms=500.0,
            proof_reserve_ms=1250.0,
            retreat_envelope_reserve_ms=50.0,
            emission_reserve_ms=1000.0,
            street_budget_ms=15000.0,
        )
        self.assertEqual(row["endpoint_oracle_proxy_ms_each"], 1000.0)
        self.assertEqual(row["second_master_proxy_ms"], 500.0)
        self.assertEqual(row["complete_one_round_proxy_ms"], 8303.0)
        self.assertTrue(row["fits_street"])

    def test_master_telemetry_redacts_every_optimizer_value(self) -> None:
        class Fake:
            variables = (0.25, 0.75)
            epigraph = (0.1, 0.2)
            equality_rows = 1
            inequality_rows = 2
            highs_iterations = 3
            solve_ms = 4.0
            maximum_equality_error = 0.0
            maximum_inequality_violation = 0.0
            maximum_bound_violation = 0.0
            maximum_stationarity_error = 0.0
            maximum_complementarity_error = 0.0
            duality_gap = 0.0

        row = _master_telemetry(Fake())
        self.assertNotIn("variables", row)
        self.assertNotIn("epigraph", row)
        self.assertNotIn("lower_bound", row)
        self.assertFalse(row["objective_epigraph_and_variables_serialized"])

    def test_invalid_actor_and_negative_capacity_fail_closed(self) -> None:
        with self.assertRaises(ValueError):
            pre_bet_check_observations(6)
        with self.assertRaises(ValueError):
            derive_capacity_proxy(
                warm_step_ms=-1.0,
                initial_row_ms=0.0,
                first_master_ms=0.0,
                source_oracle_ms=0.0,
                five_cut_row_proxy_ms=0.0,
                second_master_reserve_ms=0.0,
                proof_reserve_ms=0.0,
                retreat_envelope_reserve_ms=0.0,
                emission_reserve_ms=0.0,
                street_budget_ms=15000.0,
            )

    @unittest.skipUnless(importlib.util.find_spec("cupy"), "optional CuPy screen")
    def test_small_runtime_composition_keeps_candidate_at_current_node(self) -> None:
        cp = importlib.import_module("cupy")
        sized_fixture.MultiSizeLeafAdjointTests.setUpClass()
        fixture = sized_fixture.MultiSizeLeafAdjointTests
        materialized = fixture.belief.materialize()
        joint = {
            MultiwayRiverDeal(
                tuple(
                    fixture.belief.hands_by_player[seat][indices[seat]]
                    for seat in range(6)
                )
            ): mass
            for indices, mass in zip(
                materialized.assignments,
                materialized.probabilities,
                strict=True,
            )
        }
        one_layout = PublicTreeTensorEvaluator(
            MultiwayRiverHoldem.from_joint_weights(
                board=fixture.belief.board,
                pot=12.0,
                stacks=(30.0,) * 6,
                bet_size=3.0,
                joint_weights=joint,
            )
        )
        one_schema = information_schema_for_axes(
            one_layout,
            fixture.belief.hands_by_player,
        )
        one_blueprint = {}
        for key, actions in one_schema.items():
            digest = hashlib.sha256(key.encode("utf-8")).digest()
            weights = tuple(
                float(1 + digest[index] % 23) for index in range(len(actions))
            )
            total = sum(weights)
            one_blueprint[key] = {
                action: weights[index] / total
                for index, action in enumerate(actions)
            }
        two_blueprint = embed_one_size_policy(
            one_layout,
            fixture.layout,
            fixture.belief.hands_by_player,
            one_blueprint,
            retained_bet_size=3.0,
        )
        one_automata = build_leaf_adjoint_terminal_automata(
            one_layout,
            fixture.codes,
            pot=12.0,
            bet_size=3.0,
        )
        gpu = CuPyBidirectionalIncidence.compile(fixture.sparse)
        target = {
            "belief": fixture.belief,
            "workspace": fixture.workspace,
            "sparse": fixture.sparse,
            "gpu": gpu,
            "spec": {"acting_player": 0},
            "arms": {
                "one_size": {
                    "layout": one_layout,
                    "layout_ms": 0.0,
                    "automata": one_automata,
                    "automata_ms": 0.0,
                    "blueprint": one_blueprint,
                    "blueprint_sha256": policy_digest(one_blueprint),
                    "cache_class": CuPyResidentAutomatonCache,
                },
                "two_size": {
                    "layout": fixture.layout,
                    "layout_ms": 0.0,
                    "automata": fixture.automata,
                    "automata_ms": 0.0,
                    "blueprint": two_blueprint,
                    "blueprint_sha256": sized_policy_digest(two_blueprint),
                    "cache_class": CuPyCanonicalAffineResidentAutomatonCache,
                },
            },
        }
        parsed = {
            "players": 6,
            "solver_variant": "dcfr",
            "maximum_feature_width_per_batch": 96,
            "warm_regret_mass_payoff_fraction": 0.1,
            "acceptance_guard_normalized": 1e-10,
            "lp_tolerance": 1e-10,
            "candidate_projection_tolerance": 1e-10,
            "minimum_noncache_reserve_bytes": 0,
            "second_master_reserve_ms": 500.0,
            "proof_reserve_ms": 1250.0,
            "retreat_envelope_reserve_ms": 50.0,
            "emission_reserve_ms": 1000.0,
            "street_budget_ms": 15000.0,
            "gates": {"maximum_gpu_pool_bytes": 12_000_000_000},
        }
        try:
            rows = {
                arm: _runtime_arm(parsed, cp, target, arm)
                for arm in ("one_size", "two_size")
            }
        finally:
            del gpu
            gc.collect()
            release_cupy_memory_pool()
        self.assertEqual(rows["one_size"]["current_node_policy_variables"], 4)
        self.assertEqual(rows["two_size"]["current_node_policy_variables"], 6)
        for row in rows.values():
            self.assertEqual(row["initial_profile_passes"], 6)
            self.assertEqual(row["initial_response_passes"], 5)
            self.assertLessEqual(row["maximum_source_row_error"], 2e-11)
            self.assertTrue(set(row["candidate_changed_public_nodes"]).issubset({0}))
            self.assertTrue(row["off_node_policy_immutable"])
            self.assertEqual(row["master_candidate_evaluations"], 0)


if __name__ == "__main__":
    unittest.main()
