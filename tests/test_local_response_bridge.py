from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import unittest

from pontius.delta_certificate_contract import DeltaCertificateScope
from pontius.dependency_tape import CompiledPolicyDeltaTape
from pontius.evaluation import collect_information_sets, evaluate_profile
from pontius.h32_policy_delta_verifier_audit import (
    parse_h32_policy_delta_verifier_config,
)
from pontius.leaf_adjoint_checkpoint_ladder_audit import _build_case
from pontius.leaf_adjoint_evaluation import evaluate_leaf_adjoint_profile
from pontius.local_response_bridge import (
    certify_localized_policy_delta,
    decide_localized_response_certificate,
    simulate_exact_envelope_prefix,
)
from pontius.real_policy import policy_digest
from pontius.river import parse_cards
from pontius.river_multiway import MultiwayRiverDeal, MultiwayRiverHoldem
from pontius.kuhn import KuhnPoker


_ROOT = Path(__file__).parents[1]


def _pure_policy(game: KuhnPoker) -> dict:
    policy = {}
    for player in range(game.num_players):
        for key, actions in collect_information_sets(game, player).items():
            policy[key] = {
                action: float(index == 0) for index, action in enumerate(actions)
            }
    return policy


def _scope(tape: CompiledPolicyDeltaTape, candidate: dict, *, guard: float = 1e-9) -> DeltaCertificateScope:
    source = tape.source_result.evaluation
    return DeltaCertificateScope(
        episode_blueprint_policy_sha256=policy_digest(tape.source_policy),
        public_root_sha256="a" * 64,
        payoff_model_sha256="b" * 64,
        belief_sha256="c" * 64,
        deployed_prefix_sha256="d" * 64,
        candidate_policy_sha256=policy_digest(candidate),
        verifier_implementation_sha256="e" * 64,
        source_provenance_sha256="f" * 64,
        blueprint_deviation_gains=tuple(source.deviation_gains),
        cap_vector=tuple(value + guard for value in source.deviation_gains),
        raw_guard=guard,
        payoff_span=30.0,
        payoff_span_source="layout.game.payoff_span",
        certificate_epoch=1,
    )


class LocalResponseBridgeTests(unittest.TestCase):
    def test_localized_result_is_exact_and_every_call_is_source_relative(self) -> None:
        game = KuhnPoker(3)
        blueprint = _pure_policy(game)
        tape = CompiledPolicyDeltaTape(game, blueprint)
        keys = tuple(tape.source_policy)
        candidates = []
        for key in keys[:2]:
            candidate = tape.source_policy
            actions = tuple(candidate[key])
            candidate[key] = {
                action: float(index == 1) for index, action in enumerate(actions)
            }
            candidates.append(candidate)

        certificates = []
        for index, candidate in enumerate(candidates):
            scope = _scope(tape, candidate)
            certificate = certify_localized_policy_delta(
                tape,
                candidate,
                candidate_id=f"atom_{index}",
                scope=scope,
                expected_scope=scope,
                seat_order=(0, 1, 2),
                maximum_changed_information_sets=1,
            )
            expected = evaluate_profile(game, candidate)
            for actual, reference in (
                (certificate.evaluation.utilities, expected.utilities),
                (
                    certificate.evaluation.best_response_values,
                    expected.best_response_values,
                ),
                (certificate.evaluation.deviation_gains, expected.deviation_gains),
            ):
                self.assertLessEqual(
                    max(
                        abs(left - right)
                        for left, right in zip(actual, reference, strict=True)
                    ),
                    1e-14,
                )
            self.assertEqual(len(certificate.atoms), 1)
            certificates.append(certificate)

        self.assertEqual(
            tape.recertify_policy(blueprint).evaluation,
            tape.source_result.evaluation,
        )
        self.assertNotEqual(
            certificates[0].candidate_policy_sha256,
            certificates[1].candidate_policy_sha256,
        )

    def test_zero_reach_atom_still_recertifies_response_switches(self) -> None:
        game = KuhnPoker(3)
        blueprint = _pure_policy(game)
        candidate = {key: dict(row) for key, row in blueprint.items()}
        off_path = next(
            key
            for key in candidate
            if key.startswith("p1|") and "history=p0:bet" in key
        )
        actions = tuple(candidate[off_path])
        candidate[off_path] = {
            action: float(index == 1) for index, action in enumerate(actions)
        }
        tape = CompiledPolicyDeltaTape(game, blueprint)
        scope = _scope(tape, candidate)
        certificate = certify_localized_policy_delta(
            tape,
            candidate,
            candidate_id="zero_reach_atom",
            scope=scope,
            expected_scope=scope,
            seat_order=(0, 1, 2),
            maximum_changed_information_sets=1,
        )

        self.assertEqual(
            certificate.evaluation.utilities,
            tape.source_result.evaluation.utilities,
        )
        self.assertNotEqual(
            certificate.evaluation.best_response_values,
            tape.source_result.evaluation.best_response_values,
        )
        self.assertGreater(sum(certificate.response_action_flips_by_seat), 0)

    def test_prefix_keeps_cap_precedence_and_objective_lower_bound(self) -> None:
        cap = simulate_exact_envelope_prefix(
            (0.1, 0.1, 0.1),
            (0.11, 0.2, 0.2),
            best_complete_nash_conv=0.15,
            raw_guard=0.0,
            seat_order=(0, 1, 2),
        )
        objective = simulate_exact_envelope_prefix(
            (0.1, 0.1, 0.1),
            (0.09, 0.09, 0.09),
            best_complete_nash_conv=0.2,
            raw_guard=0.0,
            seat_order=(0, 1, 2),
        )
        self.assertEqual((cap.stop_reason, cap.stop_seat), ("blueprint_cap", 0))
        self.assertEqual(
            (objective.stop_reason, objective.stop_seat),
            ("objective_lower_bound", 2),
        )

    def test_scope_atom_limit_and_deadline_fail_closed(self) -> None:
        game = KuhnPoker(2)
        tape = CompiledPolicyDeltaTape(game, {})
        candidate = tape.source_policy
        key = next(iter(candidate))
        actions = tuple(candidate[key])
        candidate[key] = {
            action: float(index == 0) for index, action in enumerate(actions)
        }
        scope = _scope(tape, candidate)
        with self.assertRaises(ValueError):
            certify_localized_policy_delta(
                tape,
                candidate,
                candidate_id="atom",
                scope=replace(scope, certificate_epoch=2),
                expected_scope=scope,
                seat_order=(0, 1),
                maximum_changed_information_sets=1,
            )
        with self.assertRaisesRegex(ValueError, "atom limit"):
            certify_localized_policy_delta(
                tape,
                candidate,
                candidate_id="atom",
                scope=scope,
                expected_scope=scope,
                seat_order=(0, 1),
                maximum_changed_information_sets=0,
            )
        certificate = certify_localized_policy_delta(
            tape,
            candidate,
            candidate_id="atom",
            scope=scope,
            expected_scope=scope,
            seat_order=(0, 1),
            maximum_changed_information_sets=1,
        )
        decision = decide_localized_response_certificate(
            certificate,
            blueprint_candidate_id="blueprint",
            elapsed_ms=14500.0,
            emission_reserve_ms=500.0,
        )
        self.assertTrue(decision.blueprint_fallback)
        self.assertTrue(decision.deadline_fallback)
        self.assertEqual(decision.fallback_reason, "deadline")

    def test_h3_tape_matches_leaf_adjoint_reference(self) -> None:
        try:
            import scipy  # noqa: F401
        except ImportError:
            self.skipTest("optional SciPy screen")
        config = json.loads(
            (_ROOT / "experiments/configs/h32-policy-delta-verifier-audit-v1.json").read_text(
                encoding="utf-8"
            )
        )
        parsed = parse_h32_policy_delta_verifier_config(config)
        board = parse_cards(*parsed["board"])
        belief, topology, sparse, retained = _build_case(
            parsed=parsed,
            board=board,
            hand_count=3,
            family="balanced",
        )
        workspace, _, automata = retained
        materialized = belief.materialize()
        joint = {
            MultiwayRiverDeal(
                tuple(
                    belief.hands_by_player[seat][indices[seat]]
                    for seat in range(6)
                )
            ): float(probability)
            for indices, probability in zip(
                materialized.assignments,
                materialized.probabilities,
                strict=True,
            )
        }
        game = MultiwayRiverHoldem.from_joint_weights(
            board=belief.board,
            pot=parsed["pot"],
            stacks=(parsed["stack"],) * 6,
            bet_size=parsed["bet_size"],
            joint_weights=joint,
        )
        tape = CompiledPolicyDeltaTape(game, {})
        candidate = tape.source_policy
        key = next(iter(candidate))
        actions = tuple(candidate[key])
        candidate[key] = {
            action: float(index == 0) for index, action in enumerate(actions)
        }
        result = tape.recertify_policy(candidate, mode="sparse")
        reference = evaluate_leaf_adjoint_profile(
            topology,
            workspace,
            sparse,
            candidate,
            automata,
            hands_by_player=belief.hands_by_player,
            maximum_feature_width_per_batch=384,
        )
        for actual, expected in (
            (result.evaluation.utilities, reference.evaluation.utilities),
            (
                result.evaluation.best_response_values,
                reference.evaluation.best_response_values,
            ),
            (result.evaluation.deviation_gains, reference.evaluation.deviation_gains),
        ):
            self.assertLessEqual(
                max(abs(left - right) for left, right in zip(actual, expected, strict=True)),
                2e-14,
            )
        self.assertEqual(result.best_response_actions, reference.best_response_actions)
        self.assertEqual(result.diagnostics.changed_policy_information_sets, 1)
        self.assertEqual(result.diagnostics.execution_mode, "sparse")
        self.assertGreater(result.diagnostics.dirty_nodes, 0)


if __name__ == "__main__":
    unittest.main()
