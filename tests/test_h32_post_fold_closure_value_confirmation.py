from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from pontius import h32_fresh_convex_retreat_replication as core
from pontius.h32_continuation_root_ledger import _setup as historical_setup
from pontius.h32_one_round_convex_master import _mix_policy as canonical_mix_policy
from pontius.h32_post_fold_closure_value_confirmation import (
    ConstructionCapture,
    _epigraph_sha256,
    _parse_config,
    attach_construction_capture,
    capture_sealed_core_construction,
    post_fold_confirmation_decision,
)
from pontius.h32_post_fold_current_decision_setup import (
    build_post_fold_current_decision_setup,
    post_fold_core_setup_adapter,
)
from pontius.real_policy import policy_digest


ROOT = Path(__file__).parents[1]
CONFIG = (
    ROOT / "experiments/configs/h32-post-fold-closure-value-confirmation-v1.json"
)


class H32PostFoldClosureValueConfirmationTests(unittest.TestCase):
    def test_setup_adapter_is_scoped_and_restores_after_success(self) -> None:
        self.assertIs(core._setup, historical_setup)
        with post_fold_core_setup_adapter():
            self.assertIs(core._setup, build_post_fold_current_decision_setup)
        self.assertIs(core._setup, historical_setup)

    def test_setup_adapter_restores_after_failure_and_rejects_nesting(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "negative control"):
            with post_fold_core_setup_adapter():
                with self.assertRaisesRegex(RuntimeError, "already replaced"):
                    with post_fold_core_setup_adapter():
                        self.fail("nested setup adapter unexpectedly opened")
                raise RuntimeError("negative control")
        self.assertIs(core._setup, historical_setup)

    def test_construction_capture_is_exact_and_restores(self) -> None:
        blueprint = {"node": {"fold": 0.75, "call": 0.25}}
        endpoint = {"node": {"fold": 0.25, "call": 0.75}}
        original_master = core.solve_behavioral_one_seat_master
        with capture_sealed_core_construction() as capture:
            self.assertIsNot(core._mix_policy, canonical_mix_policy)
            self.assertIsNot(core.solve_behavioral_one_seat_master, original_master)
            mixed, error = core._mix_policy(blueprint, endpoint, eta=0.5)
        self.assertEqual(error, 0.0)
        self.assertEqual(mixed["node"], {"fold": 0.5, "call": 0.5})
        self.assertEqual(capture.endpoint_policies, [endpoint])
        self.assertIs(core._mix_policy, canonical_mix_policy)
        self.assertIs(core.solve_behavioral_one_seat_master, original_master)

    def test_construction_capture_restores_after_failure_and_rejects_nesting(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "negative control"):
            with capture_sealed_core_construction():
                with self.assertRaisesRegex(RuntimeError, "already replaced"):
                    with capture_sealed_core_construction():
                        self.fail("nested construction capture unexpectedly opened")
                raise RuntimeError("negative control")
        self.assertIs(core._mix_policy, canonical_mix_policy)

    def test_capture_digest_control_fails_closed(self) -> None:
        endpoint = {"node": {"fold": 0.25, "call": 0.75}}
        epigraph = (0.1, 0.2)
        bundle = {
            "construction_row": {
                "endpoint_policy_sha256": policy_digest(endpoint),
                "masters": [{"epigraph_sha256": _epigraph_sha256(epigraph)}],
            }
        }
        attached = attach_construction_capture(
            bundle,
            ConstructionCapture(
                endpoint_policies=[endpoint],
                master_epigraphs=[epigraph],
            ),
        )
        self.assertEqual(attached["endpoint_policy"], endpoint)
        contaminated = deepcopy(bundle)
        contaminated["construction_row"]["masters"][0]["epigraph_sha256"] = "0" * 64
        with self.assertRaisesRegex(RuntimeError, "captured epigraph"):
            attach_construction_capture(
                contaminated,
                ConstructionCapture(
                    endpoint_policies=[endpoint],
                    master_epigraphs=[epigraph],
                ),
            )

    def test_config_freezes_six_post_fold_current_decisions(self) -> None:
        parsed = _parse_config(json.loads(CONFIG.read_text(encoding="utf-8")))
        targets = parsed["target_specs"]
        self.assertEqual(len(targets), 6)
        self.assertEqual({row["observed_response"] for row in targets}, {"fold"})
        self.assertEqual({row["acting_player"] for row in targets}, set(range(6)))
        self.assertEqual(parsed["gates"]["expected_behavioral_information_sets"], 32)
        self.assertEqual(parsed["gates"]["expected_policy_variables"], 64)
        self.assertEqual(parsed["interior_retreat_factor"], 0.5)
        self.assertEqual(parsed["incremental_endpoint_oracle_ceiling_ms"], 1000.0)
        self.assertEqual(parsed["endpoint_bound_tolerance"], 1e-8)

    def test_decision_table_separates_process_closure_and_value(self) -> None:
        self.assertEqual(
            post_fold_confirmation_decision(
                process_passed=False,
                all_globally_closed=True,
                all_safe_positive=True,
                transfers=True,
            ),
            "reject_post_fold_closure_value_confirmation_execution",
        )
        self.assertEqual(
            post_fold_confirmation_decision(
                process_passed=True,
                all_globally_closed=False,
                all_safe_positive=True,
                transfers=True,
            ),
            "accept_execution_retain_direction_fallback_on_fresh_closure_failure",
        )
        self.assertEqual(
            post_fold_confirmation_decision(
                process_passed=True,
                all_globally_closed=True,
                all_safe_positive=False,
                transfers=True,
            ),
            "accept_fresh_closure_retain_direction_fallback_on_value_failure",
        )
        self.assertEqual(
            post_fold_confirmation_decision(
                process_passed=True,
                all_globally_closed=True,
                all_safe_positive=True,
                transfers=True,
            ),
            "accept_fresh_post_fold_closure_and_value_confirmation_and_authorize_"
            "current_decision_direction_demotion_review",
        )


if __name__ == "__main__":
    unittest.main()
