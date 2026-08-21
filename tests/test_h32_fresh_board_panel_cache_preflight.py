from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import unittest

from pontius import h32_action_width_quality_audit as action_width
from pontius.h32_fresh_board_panel_cache_preflight import (
    _FROZEN_BOARD_DIGESTS,
    _FROZEN_DESCRIPTOR_DIGESTS,
    _FROZEN_PANELS,
    _FROZEN_SOURCE_DIGESTS,
    _FROZEN_TARGET_DIGESTS,
    _SAMPLER_NAMESPACE,
    _SEED_COMMIT,
    compute_label_free_panel_identity_rows,
    derive_fresh_panel_boards,
    panel_freshness_diagnostics,
    parse_h32_fresh_board_panel_cache_config,
)


_ROOT = Path(__file__).parents[1]
_CONFIG = (
    _ROOT / "experiments" / "configs" / "h32-fresh-board-panel-cache-v1.json"
)
_WARM_CONFIG = (
    _ROOT / "experiments" / "configs" / "h32-warm-search-acceptance-v1.json"
)


class H32FreshBoardPanelDerivationTests(unittest.TestCase):
    def test_seed_derives_three_exact_disjoint_fresh_boards(self) -> None:
        panels = derive_fresh_panel_boards(
            seed_commit=_SEED_COMMIT,
            namespace=_SAMPLER_NAMESPACE,
            panel_count=3,
        )
        self.assertEqual(panels, _FROZEN_PANELS)
        diagnostics = panel_freshness_diagnostics(
            panels,
            (
                ("2c", "7d", "9h", "Js", "Qc"),
                ("4h", "6s", "Td", "Qh", "As"),
            ),
        )
        self.assertEqual(diagnostics["unique_board_count"], 3)
        self.assertEqual(diagnostics["unique_panel_card_count"], 15)
        self.assertTrue(diagnostics["pairwise_card_disjoint"])
        self.assertTrue(
            diagnostics["absent_from_disclosed_prior_h32_strategy_boards"]
        )

    def test_sampler_seed_namespace_and_count_mutations_are_rejected(self) -> None:
        changed_seed = derive_fresh_panel_boards(
            seed_commit="0" * 40,
            namespace=_SAMPLER_NAMESPACE,
            panel_count=3,
        )
        self.assertNotEqual(changed_seed, _FROZEN_PANELS)
        for values in (
            (_SEED_COMMIT, "changed", 3),
            (_SEED_COMMIT, _SAMPLER_NAMESPACE, 2),
        ):
            with self.subTest(values=values), self.assertRaises(ValueError):
                derive_fresh_panel_boards(
                    seed_commit=values[0],
                    namespace=values[1],
                    panel_count=values[2],
                )


class H32FreshBoardPanelCacheConfigTests(unittest.TestCase):
    def test_config_is_cache_only_outcome_neutral_and_fresh(self) -> None:
        config = json.loads(_CONFIG.read_text(encoding="utf-8"))
        parsed = parse_h32_fresh_board_panel_cache_config(config)
        self.assertEqual(parsed["panels"], _FROZEN_PANELS)
        self.assertEqual(parsed["panel_board_sha256"], _FROZEN_BOARD_DIGESTS)
        self.assertEqual(
            parsed["source_belief_sha256_by_source"],
            _FROZEN_SOURCE_DIGESTS,
        )
        self.assertEqual(
            parsed["target_belief_sha256_by_target"],
            _FROZEN_TARGET_DIGESTS,
        )
        self.assertEqual(
            parsed["target_descriptor_sha256_by_target"],
            _FROZEN_DESCRIPTOR_DIGESTS,
        )
        self.assertIn("zero_panel_h32_steps", parsed["zero_step_rule"])
        self.assertEqual(parsed["strategy_claim_policy"], "always_null")
        self.assertNotIn("require_headroom_safe", parsed["gates"])
        self.assertNotIn("quality", parsed["gates"])

    def test_source_board_target_resource_and_gate_mutations_are_rejected(
        self,
    ) -> None:
        config = json.loads(_CONFIG.read_text(encoding="utf-8"))
        for mutation in (
            lambda row: row.__setitem__("expected_prior_result_sha256", "0" * 64),
            lambda row: row.__setitem__("seed_commit", "0" * 40),
            lambda row: row["panels"][0]["cards"].__setitem__(0, "2d"),
            lambda row: row["source_belief_sha256_by_source"].__setitem__(
                "panel_1/balanced", "0" * 64
            ),
            lambda row: row["target_descriptor_sha256_by_target"].__setitem__(
                "panel_3/blocker_heavy/all_seat_strength_1_to2", "0" * 64
            ),
            lambda row: row["gates"].__setitem__(
                "maximum_gpu_pool_bytes", 13_000_000_000
            ),
        ):
            changed = copy.deepcopy(config)
            mutation(changed)
            with self.assertRaises(ValueError):
                parse_h32_fresh_board_panel_cache_config(changed)


class H32FreshBoardPanelLabelFreeIdentityTests(unittest.TestCase):
    def test_all_six_sources_and_twelve_targets_reproduce(self) -> None:
        warm_config = json.loads(_WARM_CONFIG.read_text(encoding="utf-8"))
        sources, targets = compute_label_free_panel_identity_rows(
            warm_config,
            _FROZEN_PANELS,
            expected_sources=_FROZEN_SOURCE_DIGESTS,
            expected_targets=_FROZEN_TARGET_DIGESTS,
            expected_descriptors=_FROZEN_DESCRIPTOR_DIGESTS,
        )
        self.assertEqual([row["source"] for row in sources], list(_FROZEN_SOURCE_DIGESTS))
        self.assertEqual([row["target"] for row in targets], list(_FROZEN_TARGET_DIGESTS))
        self.assertTrue(all(row["passed"] for row in sources))
        self.assertTrue(all(row["passed"] for row in targets))


@unittest.skipUnless(importlib.util.find_spec("cupy"), "optional CuPy screen")
class H32FreshBoardPanelSmallCacheControlTests(unittest.TestCase):
    def test_h2_common_game_cache_control_remains_exact(self) -> None:
        config = json.loads(_CONFIG.read_text(encoding="utf-8"))
        parsed = parse_h32_fresh_board_panel_cache_config(config)
        row = action_width._small_control(parsed)
        self.assertLessEqual(row["profile_utility_error"], 2e-13)
        self.assertLessEqual(row["quality_error"], 2e-11)
        self.assertLessEqual(row["zero_sum_residual"], 2e-11)
        self.assertEqual(row["shared_affine_bases"], 378)
        self.assertTrue(row["compact_round_trip"])


if __name__ == "__main__":
    unittest.main()
