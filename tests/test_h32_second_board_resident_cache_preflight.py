from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import unittest

from pontius import h32_action_width_quality_audit as action_width
from pontius.h32_second_board_resident_cache_preflight import (
    _FROZEN_TARGET_DIGESTS,
    _project_parent_descriptor,
    compute_label_free_target_identity_rows,
    parse_h32_second_board_cache_config,
)


_ROOT = Path(__file__).parents[1]
_CONFIG = _ROOT / "experiments" / "configs" / "h32-second-board-resident-cache-v1.json"
_WARM_CONFIG = (
    _ROOT / "experiments" / "configs" / "h32-warm-search-acceptance-v1.json"
)
_WARM_PARENT = (
    _ROOT / "experiments" / "results" / "h32-warm-search-acceptance-v1.json"
)


class H32SecondBoardResidentCacheConfigTests(unittest.TestCase):
    def test_config_is_cache_only_and_outcome_neutral(self) -> None:
        config = json.loads(_CONFIG.read_text(encoding="utf-8"))
        parsed = parse_h32_second_board_cache_config(config)
        self.assertEqual(parsed["board"], ["2c", "7d", "9h", "Js", "Qc"])
        self.assertEqual(parsed["target_belief_sha256_by_target"], _FROZEN_TARGET_DIGESTS)
        self.assertEqual(parsed["zero_step_rule"].count("zero_h32"), 3)
        self.assertEqual(parsed["strategy_claim_policy"], "always_null")
        self.assertNotIn("quality", parsed["gates"])
        self.assertNotIn("require_headroom_safe", parsed["gates"])

    def test_source_target_and_resource_mutations_are_rejected(self) -> None:
        config = json.loads(_CONFIG.read_text(encoding="utf-8"))
        for mutation in (
            lambda row: row.__setitem__("expected_warm_parent_sha256", "0" * 64),
            lambda row: row["target_belief_sha256_by_target"].__setitem__(
                "balanced/local_blocker_seat3_x2", "0" * 64
            ),
            lambda row: row["gates"].__setitem__(
                "maximum_gpu_pool_bytes", 13_000_000_000
            ),
        ):
            changed = copy.deepcopy(config)
            mutation(changed)
            with self.assertRaises(ValueError):
                parse_h32_second_board_cache_config(changed)


class H32SecondBoardTargetIdentityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.warm_config = json.loads(_WARM_CONFIG.read_text(encoding="utf-8"))
        cls.warm_parent = json.loads(_WARM_PARENT.read_text(encoding="utf-8"))

    def test_all_four_label_free_target_identities_reproduce(self) -> None:
        rows = compute_label_free_target_identity_rows(
            self.warm_config,
            self.warm_parent,
            expected_digests=_FROZEN_TARGET_DIGESTS,
        )
        self.assertEqual([row["target"] for row in rows], list(_FROZEN_TARGET_DIGESTS))
        self.assertTrue(all(row["passed"] for row in rows))

    def test_parent_projection_excludes_only_measurement_fields(self) -> None:
        family = self.warm_parent["family_rows"][0]
        for target in family["targets"]:
            projected = _project_parent_descriptor(
                target,
                shift=target["target_shift"],
            )
            self.assertNotIn("marginal_measurement_ms", projected)
            self.assertIn("hand_axes_identity", projected)
            changed = copy.deepcopy(target)
            changed["target_descriptor"].pop("tie_rule")
            with self.assertRaises(ValueError):
                _project_parent_descriptor(changed, shift=target["target_shift"])


@unittest.skipUnless(importlib.util.find_spec("cupy"), "optional CuPy screen")
class H32SecondBoardSmallCacheControlTests(unittest.TestCase):
    def test_h2_common_game_cache_control_remains_exact(self) -> None:
        config = json.loads(_CONFIG.read_text(encoding="utf-8"))
        parsed = parse_h32_second_board_cache_config(config)
        row = action_width._small_control(parsed)
        self.assertLessEqual(row["profile_utility_error"], 2e-13)
        self.assertLessEqual(row["quality_error"], 2e-11)
        self.assertLessEqual(row["zero_sum_residual"], 2e-11)
        self.assertEqual(row["shared_affine_bases"], 378)
        self.assertTrue(row["compact_round_trip"])


if __name__ == "__main__":
    unittest.main()
