from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest


_ROOT = Path(__file__).parents[1]
_RESULT = _ROOT / "experiments/results/h32-one-seat-retreat-quality-v2.json"
_CONFIG = _ROOT / "experiments/configs/h32-one-seat-retreat-quality-v2.json"
_BASE_CONFIG = _ROOT / "experiments/configs/h32-one-seat-retreat-quality-v1.json"
_EXPECTED_SHA256 = "126d3fbff1751902c067f96073703699165a494ba8b4fecfe0841dfc61fb157d"


class H32OneSeatRetreatQualityResultTests(unittest.TestCase):
    def test_accepted_artifact_authorizes_only_fresh_replication(self) -> None:
        raw = _RESULT.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), _EXPECTED_SHA256)
        result = json.loads(raw)
        config = json.loads(_CONFIG.read_text(encoding="utf-8"))
        base = json.loads(_BASE_CONFIG.read_text(encoding="utf-8"))

        self.assertTrue(result["passed"])
        self.assertTrue(all(result["gates"].values()))
        self.assertEqual(
            result["decision"],
            "authorize_preregistered_fresh_target_retreat_replication",
        )
        self.assertEqual(
            result["environment"]["git"]["commit"],
            "a7960be318dcada8cc60fda56f621796a05a4056",
        )
        self.assertFalse(result["environment"]["git"]["dirty"])
        self.assertEqual(result["config_sha256"], hashlib.sha256(_CONFIG.read_bytes()).hexdigest())

        barrier = result["feature_label_barrier"]
        self.assertEqual(
            barrier["events"],
            [
                "inputs_pinned",
                "candidate_frozen",
                "retreat_certificate_complete",
                "sealed_comparator_opened",
            ],
        )
        self.assertTrue(all(barrier["semantic_identity_checks"].values()))
        self.assertEqual(
            barrier["policy_digest_diagnostics"],
            {
                "endpoint_policy": False,
                "first_candidate_policy": False,
                "retreat_policy": False,
            },
        )
        self.assertTrue(all(result["first_oracle_reproduction_checks"].values()))
        self.assertEqual(base["cap_numerical_allowance"], 2e-11)
        self.assertEqual(base["epigraph_separation_allowance"], 1e-9)
        self.assertNotIn("expected_fallback_exact_value", config)
        self.assertNotIn("expected_fallback_charged_ledger_ms", config)

        target = result["target"]
        retreat = target["retreat"]
        certificate = retreat["exact_certificate"]
        self.assertTrue(retreat["independently_certified"])
        self.assertTrue(retreat["shadow_accepted"])
        self.assertTrue(certificate["cap_feasible"])
        self.assertEqual(certificate["maximum_cap_violation"], 0.0)
        self.assertGreaterEqual(
            certificate["minimum_cap_slack"],
            retreat["required_interior_slack"],
        )
        self.assertLessEqual(
            certificate["nash_conv"],
            retreat["jensen_objective_ceiling"] + base["quality_numerical_allowance"],
        )
        self.assertTrue(target["ledger"]["fits_measured_street"])
        self.assertTrue(target["ledger"]["fits_conservative_street"])

        comparison = result["comparison"]
        self.assertTrue(comparison["material_value_win"])
        self.assertTrue(comparison["conservative_rate_win"])
        self.assertTrue(comparison["authorizes_fresh_target_replication"])
        self.assertGreater(
            comparison["retreat_exact_value"],
            comparison["fallback_exact_value"] + target["raw_guard"],
        )
        self.assertEqual(target["candidate_policies_emitted"], 0)
        self.assertEqual(
            result["actual_emitted_policy"],
            "immutable_restricted_blueprint_only",
        )
        self.assertEqual(
            result["strategy_quality_claim"],
            "single_retained_target_shadow_exact_value_only",
        )
        self.assertIsNone(result["strategy_population_claim"])


if __name__ == "__main__":
    unittest.main()
