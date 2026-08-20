from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from pontius.fixed_envelope_verifier import (
    leaf_policy_delta_width_screen,
    simulate_fixed_envelope_verifier,
    verify_leaf_adjoint_candidate,
)
from pontius.h32_policy_delta_verifier_audit import (
    _source_target,
    _teacher_union,
    parse_h32_policy_delta_verifier_config,
    reconstruct_candidate_policies,
)
from pontius.leaf_adjoint_checkpoint_ladder_audit import _build_case
from pontius.leaf_adjoint_evaluation import evaluate_leaf_adjoint_profile
from pontius.real_policy import policy_digest
from pontius.river import parse_cards


_ROOT = Path(__file__).parents[1]
_CONFIG = (
    _ROOT / "experiments" / "configs" / "h32-policy-delta-verifier-audit-v1.json"
)
_RESULTS = _ROOT / "experiments" / "results"


def _quality_candidate(
    candidate_id: str,
    digest_character: str,
    gains: list[float],
) -> dict[str, object]:
    nash_conv = sum(gains)
    return {
        "candidate_id": candidate_id,
        "quality": {
            "policy_sha256": digest_character * 64,
            "deviation_gains": gains,
            "nash_conv": nash_conv,
            "normalized_nash_conv": nash_conv,
        },
    }


class FixedEnvelopeVerifierUnitTests(unittest.TestCase):
    def test_simulator_stops_on_cap_and_objective_without_changing_optimum(self) -> None:
        blueprint = _quality_candidate("blueprint_average64", "f", [0.5, 0.5])
        cap_break = _quality_candidate("cap_break", "a", [0.6, 0.1])
        incumbent = _quality_candidate("incumbent", "b", [0.1, 0.1])
        objective_loss = _quality_candidate("objective_loss", "c", [0.3, 0.1])
        result = simulate_fixed_envelope_verifier(
            blueprint,
            [cap_break, incumbent, objective_loss],
            seat_order=(0, 1),
            raw_guard=1e-9,
        )
        self.assertEqual(
            [row["stop_reason"] for row in result["candidate_rows"]],
            ["blueprint_cap", "complete", "objective_lower_bound"],
        )
        self.assertEqual(result["evaluated_seat_count"], 4)
        self.assertEqual(result["selection"]["selected_candidate_id"], "incumbent")

    def test_simulator_final_selection_is_order_independent(self) -> None:
        blueprint = _quality_candidate("blueprint_average64", "f", [0.5, 0.5])
        first = _quality_candidate("first", "a", [0.3, 0.3])
        second = _quality_candidate("second", "b", [0.1, 0.1])
        forward = simulate_fixed_envelope_verifier(
            blueprint,
            [first, second],
            seat_order=(0, 1),
            raw_guard=1e-9,
        )
        reverse = simulate_fixed_envelope_verifier(
            blueprint,
            [second, first],
            seat_order=(0, 1),
            raw_guard=1e-9,
        )
        self.assertEqual(
            forward["selection"]["selected_policy_sha256"],
            reverse["selection"]["selected_policy_sha256"],
        )
        self.assertLess(reverse["evaluated_seat_count"], forward["evaluated_seat_count"])


class H32PolicyDeltaVerifierAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(_CONFIG.read_text(encoding="utf-8"))
        cls.acceptance = json.loads(
            (_RESULTS / "h32-warm-search-acceptance-v1.json").read_text()
        )
        cls.candidate_source = json.loads(
            (_RESULTS / "h32-warm-candidate-stream-v1.json").read_text()
        )
        cls.interpolation = json.loads(
            (_RESULTS / "h32-current-interpolation-audit-v1.json").read_text()
        )
        cls.ladder = json.loads(
            (_RESULTS / "leaf-adjoint-checkpoint-ladder-v2.json").read_text()
        )
        cls.extension = json.loads(
            (_RESULTS / "leaf-adjoint-checkpoint-extension-v1.json").read_text()
        )

    def test_frozen_protocol_has_no_strategy_outcome_gate(self) -> None:
        parsed = parse_h32_policy_delta_verifier_config(self.config)
        self.assertEqual(parsed["seat_order"], (0, 1, 2, 3, 4, 5))
        self.assertEqual(parsed["gates"]["expected_new_strategy_quality_labels"], 0)
        forbidden = {
            "required_selected_candidate",
            "minimum_strategy_reduction",
            "require_delta_narrower_than_full",
            "minimum_headroom_capture",
        }
        self.assertTrue(forbidden.isdisjoint(parsed["gates"]))

    def test_workload_sources_and_gates_are_immutable(self) -> None:
        mutations = []
        for key, value in (
            ("evidence_stage", "prospective_strategy_audit"),
            ("candidate_order", ["search_current1"]),
            ("seat_order", [2, 0, 1, 3, 4, 5]),
            ("acceptance_guard_normalized", 1e-8),
            ("delta_comparison_tolerance", 1e-8),
            ("maximum_feature_width_per_batch", 768),
        ):
            mutation = deepcopy(self.config)
            mutation[key] = value
            mutations.append(mutation)
        source = deepcopy(self.config)
        source["expected_replay_source_sha256"] = "0" * 64
        mutations.append(source)
        gate = deepcopy(self.config)
        gate["gates"]["minimum_pooled_calibrated_speedup"] = 1.0
        mutations.append(gate)
        extra = deepcopy(self.config)
        extra["seat_selector"] = "observed_violation_rate"
        mutations.append(extra)
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                with self.assertRaises(ValueError):
                    parse_h32_policy_delta_verifier_config(mutation)

    def test_all_52_candidate_policies_reconstruct_to_teacher_digests(self) -> None:
        parsed = parse_h32_policy_delta_verifier_config(self.config)
        rows = 0
        for family in parsed["range_families"]:
            for shift in parsed["target_shifts"]:
                acceptance_target = _source_target(
                    self.acceptance,
                    family=family,
                    shift=shift,
                )
                candidate_target = _source_target(
                    self.candidate_source,
                    family=family,
                    shift=shift,
                )
                interpolation_target = _source_target(
                    self.interpolation,
                    family=family,
                    shift=shift,
                )
                teacher, diagnostics = _teacher_union(
                    (
                        ("adr0099", acceptance_target),
                        ("adr0101", candidate_target),
                        ("adr0103", interpolation_target),
                    ),
                    maximum_duplicate_error=1e-15,
                )
                blueprint, policies, source_identity = reconstruct_candidate_policies(
                    family=family,
                    acceptance_target=acceptance_target,
                    candidate_target=candidate_target,
                    ladder_source=self.ladder,
                    extension_source=self.extension,
                    candidate_order=parsed["candidate_order"],
                )
                self.assertTrue(source_identity)
                self.assertEqual(
                    policy_digest(blueprint),
                    acceptance_target["blueprint_quality"]["policy_sha256"],
                )
                self.assertEqual(diagnostics["unique_policies"], 13)
                self.assertEqual(
                    [row["policy_sha256"] for row in policies],
                    [row["quality"]["policy_sha256"] for row in teacher],
                )
                rows += len(policies)
        self.assertEqual(rows, 52)

    def test_h4_live_complete_vector_and_delta_screen_are_exact(self) -> None:
        parsed = parse_h32_policy_delta_verifier_config(self.config)
        board = parse_cards(*parsed["board"])
        belief, topology, sparse, retained = _build_case(
            parsed=parsed,
            board=board,
            hand_count=4,
            family="balanced",
        )
        workspace, _, automata = retained
        schema = topology.information_schema()
        key = next(iter(schema))
        actions = schema[key]
        baseline = {}
        candidate = {key: {actions[0]: 1.0, actions[1]: 0.0}}
        expected = evaluate_leaf_adjoint_profile(
            topology,
            workspace,
            sparse,
            candidate,
            automata,
            hands_by_player=belief.hands_by_player,
            maximum_feature_width_per_batch=384,
        )
        actual = verify_leaf_adjoint_candidate(
            candidate_id="h4_one_node",
            layout=topology,
            workspace=workspace,
            sparse=sparse,
            policy=candidate,
            terminal_automata=automata,
            hands_by_player=belief.hands_by_player,
            blueprint_deviation_gains=(1e6,) * 6,
            best_complete_nash_conv=1e6,
            payoff_span=30.0,
            raw_guard=3e-9,
            seat_order=(0, 1, 2, 3, 4, 5),
            maximum_feature_width_per_batch=384,
            cupy_sparse=None,
        )
        self.assertTrue(actual["complete"])
        self.assertLessEqual(
            max(
                abs(left - right)
                for left, right in zip(
                    actual["quality"]["deviation_gains"],
                    expected.evaluation.deviation_gains,
                    strict=True,
                )
            ),
            1e-14,
        )
        screen = leaf_policy_delta_width_screen(
            layout=topology,
            workspace=workspace,
            baseline_policy=baseline,
            candidate_policy=candidate,
            terminal_automata=automata,
            hands_by_player=belief.hands_by_player,
            comparison_tolerance=1e-15,
        )
        self.assertEqual(screen["changed_public_nodes"], 1)
        self.assertEqual(screen["changed_seats"], [0])
        self.assertGreater(screen["supported_delta_terms"], 0)
        self.assertLess(
            screen["optimistic_delta_to_existing_width_ratio"],
            1.0,
        )


if __name__ == "__main__":
    unittest.main()
