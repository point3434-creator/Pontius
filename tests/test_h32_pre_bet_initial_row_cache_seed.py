from __future__ import annotations

import ast
import copy
import gc
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from pontius.canonical_affine_resident_automaton_cache import (
    CuPyCanonicalAffineResidentAutomatonCache,
)
from pontius.cupy_sparse_incidence import (
    CuPyBidirectionalIncidence,
    release_cupy_memory_pool,
)
from pontius.h32_pre_bet_initial_row_cache_seed import (
    CacheSeedPrelabelBarrier,
    _cache_path,
    _parse_config,
)
from pontius.h32_pre_bet_initial_row_gpu import (
    h32_gpu_row_primitive_digest,
    h32_gpu_row_primitive_manifest,
    seed_h32_pre_bet_initial_row_cache,
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
CONFIG = ROOT / "experiments/configs/h32-pre-bet-initial-row-cache-seed-v1.json"
RUNNER = ROOT / "src/pontius/h32_pre_bet_initial_row_cache_seed.py"
GPU_PRIMITIVE = ROOT / "src/pontius/h32_pre_bet_initial_row_gpu.py"
SEALED_RUNNER = ROOT / "src/pontius/h32_pre_bet_action_width_capacity.py"
SEALED_RESULT = (
    ROOT / "experiments/results/h32-pre-bet-action-width-capacity-v1.json"
)


class H32PreBetInitialRowCacheSeedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.raw_config = json.loads(CONFIG.read_text(encoding="utf-8"))
        cls.parsed = _parse_config(copy.deepcopy(cls.raw_config))

    def test_seed_scope_is_only_seat5_both_arms_and_all_sources(self) -> None:
        parsed = self.parsed
        self.assertEqual(parsed["acting_player_order"], (5,))
        self.assertEqual(len(parsed["sources"]), 6)
        self.assertEqual(len(parsed["cache_entries"]), 12)
        self.assertEqual(
            [row["arm"] for row in parsed["cache_entries"]],
            ["one_size", "two_size"] * 6,
        )
        self.assertTrue(
            all(row["target_id"].endswith("/checks_to_seat5") for row in parsed["cache_entries"])
        )
        self.assertEqual(parsed["selection_evidence"]["complete_positions"], [5])
        self.assertAlmostEqual(
            parsed["selection_evidence"]["worst_selected_position_proxy_ms"],
            12966.496699966956,
        )
        self.assertEqual(
            hashlib.sha256(SEALED_RESULT.read_bytes()).hexdigest(),
            "d9b0518d6df8c71afaea573cca8668217fec6ed6490544f74b155ab67956f9d7",
        )

    def test_seed_config_cannot_authorize_or_self_trust_replay(self) -> None:
        self.assertEqual(self.parsed["authorized_phase"], "cache_seed_only")
        self.assertIsNone(self.parsed["trusted_seed_manifest_sha256"])
        self.assertFalse(self.parsed["capacity_replay_authorized"])
        for field_name, value in (
            ("trusted_seed_manifest_sha256", "0" * 64),
            ("capacity_replay_authorized", True),
            ("authorized_phase", "capacity_replay"),
        ):
            with self.subTest(field_name=field_name):
                changed = copy.deepcopy(self.raw_config)
                changed[field_name] = value
                with self.assertRaisesRegex(ValueError, "contract differs"):
                    _parse_config(changed)

        numeric_alias = copy.deepcopy(self.raw_config)
        numeric_alias["maximum_campaign_seconds"] = 3600
        with self.assertRaisesRegex(ValueError, "contract differs"):
            _parse_config(numeric_alias)

    def test_gpu_primitive_manifests_are_distinct_and_source_closed(self) -> None:
        manifests = {
            arm: h32_gpu_row_primitive_manifest(arm, self.parsed)
            for arm in ("one_size", "two_size")
        }
        digests = {
            arm: h32_gpu_row_primitive_digest(arm, self.parsed)
            for arm in manifests
        }
        self.assertNotEqual(digests["one_size"], digests["two_size"])
        for arm, manifest in manifests.items():
            self.assertEqual(
                digests[arm],
                self.parsed[f"expected_{arm}_gpu_row_primitive_sha256"],
            )
            modules = {row["module"] for row in manifest["files"]}
            self.assertIn("pontius.h32_pre_bet_initial_row_gpu", modules)
            self.assertIn("pontius.h32_pre_bet_action_width_capacity", modules)
            self.assertIn("pontius.pre_bet_initial_row_cache", modules)
            self.assertIn("pontius.public_node_open_axis", modules)
            self.assertIn("pontius.sequence_form_open_axis", modules)
            self.assertGreater(len(modules), 50)
            for row in manifest["files"]:
                path = ROOT / row["path"]
                canonical = path.read_bytes().replace(b"\r\n", b"\n")
                self.assertNotIn(b"\r", canonical)
                self.assertEqual(hashlib.sha256(canonical).hexdigest(), row["sha256"])
        self.assertEqual(manifests["one_size"]["contract"]["dtype"], "Float64")
        self.assertEqual(
            manifests["two_size"]["contract"]["role_order"],
            "all_profiles_then_nonacting_fixed_responses",
        )

    def test_seed_barrier_is_ordered_all_or_nothing_and_never_opens_replay(self) -> None:
        expected = tuple(
            (row["target_id"], row["arm"]) for row in self.parsed["cache_entries"]
        )
        barrier = CacheSeedPrelabelBarrier(expected)
        barrier.record(*expected[0])
        with self.assertRaisesRegex(RuntimeError, "order differs"):
            barrier.record(*expected[2])
        with self.assertRaisesRegex(RuntimeError, "incomplete"):
            barrier.freeze_untrusted_bytes()
        for row in expected[1:]:
            barrier.record(*row)
        barrier.freeze_untrusted_bytes()
        snapshot = barrier.snapshot()
        self.assertTrue(snapshot["complete"])
        self.assertEqual(snapshot["phase"], "cache_bytes_observed_untrusted")
        self.assertFalse(snapshot["capacity_replay_authorized"])
        self.assertIsNone(snapshot["trusted_seed_manifest_sha256"])
        self.assertEqual(snapshot["candidate_endpoints_opened"], 0)
        self.assertEqual(snapshot["certificates_opened"], 0)
        self.assertEqual(snapshot["strategy_quality_rows_opened"], 0)
        self.assertEqual(snapshot["candidate_policies_emitted"], 0)

    def test_every_gpu_unit_uses_the_shared_active_deadline_and_checkpoint(self) -> None:
        tree = ast.parse(RUNNER.read_text(encoding="utf-8"))
        run = next(
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef)
            and node.name == "run_h32_pre_bet_initial_row_cache_seed"
        )
        constructors = [
            node
            for node in ast.walk(run)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "MonotonicCampaignDeadline"
        ]
        bounded = [
            node
            for node in ast.walk(run)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "bounded_unit"
        ]
        self.assertEqual(len(constructors), 1)
        self.assertEqual(len(bounded), 2)
        self.assertTrue(
            all(any(keyword.arg == "checkpoint" for keyword in call.keywords) for call in bounded)
        )
        complete_frozen_units = (
            self.parsed["gates"]["expected_targets"]
            * self.parsed["maximum_context_unit_seconds"]
            + self.parsed["gates"]["expected_cache_entries"]
            * self.parsed["maximum_cache_seed_unit_seconds"]
        )
        self.assertEqual(complete_frozen_units, 2160.0)
        self.assertLess(complete_frozen_units, self.parsed["maximum_campaign_seconds"])

    def test_seed_primitive_has_no_warm_master_candidate_certificate_or_emission_path(self) -> None:
        runner_tree = ast.parse(RUNNER.read_text(encoding="utf-8"))
        gpu_tree = ast.parse(GPU_PRIMITIVE.read_text(encoding="utf-8"))
        combined_calls = set()
        for tree in (runner_tree, gpu_tree):
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                if isinstance(node.func, ast.Name):
                    combined_calls.add(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    combined_calls.add(node.func.attr)
        forbidden = {
            "warm_start",
            "step",
            "solve_behavioral_one_seat_master",
            "prepare_pre_bet_restricted_master_successor",
            "policy_from_variables",
            "serialize_candidate",
        }
        self.assertTrue(forbidden.isdisjoint(combined_calls))
        runner_source = RUNNER.read_text(encoding="utf-8")
        self.assertNotIn("capacity_replay(", runner_source)
        self.assertNotIn("strategy_quality(", runner_source)
        canonical_runner = SEALED_RUNNER.read_bytes().replace(b"\r\n", b"\n")
        self.assertEqual(
            hashlib.sha256(canonical_runner).hexdigest(),
            self.parsed["expected_parent_runner_sha256"],
        )

    def test_cache_paths_are_file_specific_and_cannot_escape(self) -> None:
        paths = [_cache_path(row["path"]) for row in self.parsed["cache_entries"]]
        self.assertEqual(len(paths), len(set(paths)))
        self.assertTrue(all(path.suffix == ".json" for path in paths))
        with self.assertRaisesRegex(ValueError, "escapes"):
            _cache_path("experiments/results/forbidden.json")

    @unittest.skipUnless(importlib.util.find_spec("cupy"), "optional CuPy control")
    def test_small_gpu_seed_round_trips_both_distinct_arms_without_optimizer_work(
        self,
    ) -> None:
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
            weights = tuple(float(1 + digest[index] % 23) for index in range(len(actions)))
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
            "hands_per_player": 2,
            "maximum_feature_width_per_batch": 96,
            "minimum_noncache_reserve_bytes": 0,
            "required_numpy_version": self.parsed["required_numpy_version"],
            "required_cupy_version": self.parsed["required_cupy_version"],
            "required_cuda_runtime_version": self.parsed[
                "required_cuda_runtime_version"
            ],
            "minimum_cuda_driver_version": self.parsed[
                "minimum_cuda_driver_version"
            ],
            "required_compute_capability": self.parsed[
                "required_compute_capability"
            ],
            "gates": {"maximum_gpu_pool_bytes": 12_000_000_000},
        }
        try:
            with tempfile.TemporaryDirectory() as directory:
                rows = {
                    arm: seed_h32_pre_bet_initial_row_cache(
                        parsed,
                        cp,
                        target,
                        arm,
                        Path(directory) / f"{arm}.json",
                    )
                    for arm in ("one_size", "two_size")
                }
        finally:
            del gpu
            gc.collect()
            release_cupy_memory_pool()
        self.assertNotEqual(
            rows["one_size"]["row_primitive_sha256"],
            rows["two_size"]["row_primitive_sha256"],
        )
        for row in rows.values():
            self.assertEqual(row["initial_profile_rows"], 6)
            self.assertEqual(row["initial_response_rows"], 5)
            self.assertEqual(row["initial_gain_rows"], 6)
            self.assertLessEqual(row["maximum_source_row_error"], 2e-11)
            self.assertLessEqual(row["maximum_gain_source_error"], 2e-11)
            self.assertTrue(row["exact_row_byte_round_trip"])
            self.assertEqual(row["mechanical_round_trip_reason"], "exact_hit")
            self.assertEqual(row["warm_steps"], 0)
            self.assertEqual(row["master_solves"], 0)
            self.assertEqual(row["candidate_endpoint_evaluations"], 0)
            self.assertEqual(row["separation_or_certificate_evaluations"], 0)
            self.assertEqual(row["strategy_quality_rows"], 0)
            self.assertEqual(row["candidate_policies_emitted"], 0)


if __name__ == "__main__":
    unittest.main()
