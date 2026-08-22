from __future__ import annotations

import ast
import hashlib
import tempfile
import unittest
from pathlib import Path

from pontius.h32_pre_bet_work_reduction_analysis import (
    analyze_h32_pre_bet_work_reduction,
)

_ROOT = Path(__file__).parents[1]
_RESULT = _ROOT / "experiments/results/h32-pre-bet-action-width-capacity-v1.json"
_RUNNER = _ROOT / "src/pontius/h32_pre_bet_action_width_capacity.py"
_EXPECTED_RESULT_SHA256 = "d9b0518d6df8c71afaea573cca8668217fec6ed6490544f74b155ab67956f9d7"


class H32PreBetWorkReductionAnalysisTests(unittest.TestCase):
    def test_analysis_is_bound_to_the_rejected_label_free_artifact(self) -> None:
        self.assertEqual(
            hashlib.sha256(_RESULT.read_bytes()).hexdigest(),
            _EXPECTED_RESULT_SHA256,
        )
        report = analyze_h32_pre_bet_work_reduction(_RESULT)
        self.assertEqual(report["source_result_sha256"], _EXPECTED_RESULT_SHA256)
        self.assertEqual(
            report["evidence_boundary"],
            {
                "rejected_invocation_only": True,
                "failed_leaf_gate": "resource_caps/campaign_duration",
                "master_candidate_endpoint_evaluations": 0,
                "retreat_or_certificate_evaluations": 0,
                "strategy_quality_rows_serialized": 0,
                "candidate_policies_emitted": 0,
                "actual_emitted_policy": "immutable_one_size_blueprint_only",
            },
        )
        self.assertLessEqual(report["maximum_frozen_formula_error_ms"], 1e-9)

    def test_warm_removal_and_exact_initial_row_hit_are_separate_scenarios(self) -> None:
        report = analyze_h32_pre_bet_work_reduction(_RESULT)
        two = report["arms"]["two_size"]
        self.assertAlmostEqual(
            two["components_ms"]["warm_step"]["median"],
            9_331.228600000031,
        )
        self.assertAlmostEqual(
            two["components_ms"]["initial_eleven_rows"]["median"],
            17_292.335149999417,
        )
        frozen = two["scenarios"]["frozen"]
        warm_removed = two["scenarios"]["remove_nonfeeding_warm_step"]
        cached = two["scenarios"]["zero_cost_exact_initial_row_cache_hit"]
        combined = two["scenarios"]["remove_warm_plus_zero_cost_exact_initial_row_cache_hit"]
        self.assertEqual((frozen["fit_count"], frozen["complete_positions"]), (0, []))
        self.assertEqual(
            (warm_removed["fit_count"], warm_removed["complete_positions"]),
            (3, []),
        )
        self.assertEqual((cached["fit_count"], cached["complete_positions"]), (4, []))
        self.assertEqual(
            (combined["fit_count"], combined["complete_positions"]),
            (6, [5]),
        )
        self.assertAlmostEqual(
            combined["maximum_by_position_ms"]["5"],
            12_966.496699966956,
        )

    def test_paired_full_layout_timings_do_not_establish_an_overlay_cost(self) -> None:
        report = analyze_h32_pre_bet_work_reduction(_RESULT)
        paired = report["paired_diagnostics"]
        self.assertAlmostEqual(
            paired["initial_eleven_rows"]["two_over_one"]["median"],
            2.8328362193514716,
        )
        self.assertAlmostEqual(
            paired["source_all_seat_oracle"]["two_over_one"]["median"],
            1.9267087030587122,
        )
        self.assertTrue(all(row["all_two_size_slower"] for row in paired.values()))
        overlay = report["arms"]["two_size"]["unmeasured_overlay_arithmetic"]
        self.assertEqual(
            (
                overlay["initial_rows_only_after_warm_removal"]["fit_count"],
                overlay["initial_rows_only_after_warm_removal"]["complete_positions"],
            ),
            (3, []),
        )
        self.assertEqual(
            (
                overlay["initial_and_future_cut_rows_after_warm_removal"]["fit_count"],
                overlay["initial_and_future_cut_rows_after_warm_removal"]["complete_positions"],
            ),
            (5, []),
        )
        self.assertEqual(
            (
                overlay["all_contractions_after_warm_removal"]["fit_count"],
                overlay["all_contractions_after_warm_removal"]["complete_positions"],
            ),
            (6, [5]),
        )
        self.assertIn("optimistic counterfactual", overlay["evidence_status"])
        self.assertIn(
            "no savings are claimed",
            report["hypothesis_limits"]["incremental_bet6_overlay"],
        )
        self.assertIn(
            "cannot quantify",
            report["hypothesis_limits"]["anytime_separation"],
        )

    def test_measured_warm_step_state_is_not_consumed_by_the_master(self) -> None:
        tree = ast.parse(_RUNNER.read_text(encoding="utf-8"))
        runtime_arm = next(
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "_runtime_arm"
        )
        step_call = next(
            node
            for node in ast.walk(runtime_arm)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "solver"
            and node.func.attr == "step"
        )
        master_call = next(
            node
            for node in ast.walk(runtime_arm)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "solve_behavioral_one_seat_master"
        )
        self.assertLess(step_call.lineno, master_call.lineno)
        post_step_solver_reads = {
            node.attr
            for node in ast.walk(runtime_arm)
            if isinstance(node, ast.Attribute)
            and node.lineno > step_call.lineno
            and isinstance(node.value, ast.Name)
            and node.value.id == "solver"
        }
        self.assertEqual(post_step_solver_reads, {"last_step_work"})
        master_input_names = {
            node.id
            for node in ast.walk(master_call)
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)
        }
        self.assertTrue(
            {"solver", "warm_distance", "warm_works", "warm_row"}.isdisjoint(master_input_names)
        )

    def test_modified_artifact_fails_before_timing_analysis(self) -> None:
        raw = bytearray(_RESULT.read_bytes())
        raw[-2] = ord(" ")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "changed.json"
            path.write_bytes(raw)
            with self.assertRaisesRegex(ValueError, "digest differs"):
                analyze_h32_pre_bet_work_reduction(path)


if __name__ == "__main__":
    unittest.main()
