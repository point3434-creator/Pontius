from dataclasses import replace
import unittest

from pontius.dependency_tape import CompiledPolicyDeltaTape
from pontius.evaluation import collect_information_sets
from pontius.kuhn import KuhnPoker
from pontius.delta_certificate_contract import (
    DeltaCertificateScope,
    atomic_policy_manifest,
    certificate_scope_digest,
    classify_envelope_probe,
    deadline_fallback_required,
    geometric_halving_scales,
    interaction_residual,
    interpolate_policy_atoms,
    validate_certificate_scope,
)


class DeltaCertificateContractTests(unittest.TestCase):
    def test_four_way_envelope_classifier(self) -> None:
        cases = (
            ((0.1, 0.2), 0.20, "admissible_improvement"),
            ((0.1, 0.4), 0.20, "cap_only_rejection"),
            ((0.1, 0.2), 0.31, "objective_only_rejection"),
            ((0.1, 0.4), 0.31, "cap_and_objective_rejection"),
        )
        for gains, nash_conv, expected in cases:
            row = classify_envelope_probe(
                (0.1, 0.2), gains,
                blueprint_nash_conv=0.3,
                candidate_nash_conv=nash_conv,
                raw_guard=1e-9,
                payoff_span=30.0,
            )
            self.assertEqual(row.classification, expected)

    def test_atomic_reconstruction_and_shared_grid(self) -> None:
        blueprint = {
            "a": {"x": 0.75, "y": 0.25},
            "b": {"x": 0.25, "y": 0.75},
        }
        candidate = {
            "a": {"x": 0.5, "y": 0.5},
            "b": {"x": 0.9, "y": 0.1},
        }
        atoms = atomic_policy_manifest(blueprint, candidate)
        rebuilt = interpolate_policy_atoms(
            blueprint, candidate, [row.information_key for row in atoms], scale=1.0,
        )
        self.assertEqual(rebuilt, candidate)
        scales = geometric_halving_scales(numerical_floor=1e-10)
        self.assertEqual(scales[0], 1.0)
        self.assertGreaterEqual(scales[-1], 1e-10)
        self.assertLess(scales[-1] * 0.5, 1e-10)

    def test_union_interaction_is_exact_inclusion_exclusion(self) -> None:
        residual = interaction_residual(
            (1.0, 2.0), (1.5, 2.0), (1.0, 1.5), (1.7, 1.1),
        )
        self.assertAlmostEqual(residual[0], 0.2)
        self.assertAlmostEqual(residual[1], -0.4)

    def test_scope_is_fail_closed_for_span_epoch_and_reanchoring(self) -> None:
        scope = DeltaCertificateScope(
            episode_blueprint_policy_sha256="a" * 64,
            public_root_sha256="b" * 64,
            payoff_model_sha256="c" * 64,
            belief_sha256="d" * 64,
            deployed_prefix_sha256="e" * 64,
            candidate_policy_sha256="f" * 64,
            verifier_implementation_sha256="1" * 64,
            source_provenance_sha256="2" * 64,
            blueprint_deviation_gains=(0.1, 0.2),
            cap_vector=(0.100000001, 0.200000001),
            raw_guard=1e-9,
            payoff_span=30.0,
            payoff_span_source="layout.game.payoff_span",
            certificate_epoch=7,
        )
        validate_certificate_scope(scope, scope)
        self.assertEqual(len(certificate_scope_digest(scope)), 64)
        for changed in (
            replace(scope, payoff_span=48.0),
            replace(scope, payoff_span_source="stack"),
            replace(scope, certificate_epoch=8),
            replace(scope, episode_blueprint_policy_sha256="3" * 64),
            replace(scope, selected_candidate_becomes_anchor=True),
            replace(scope, cumulative_episode_safety_claim=True),
        ):
            with self.assertRaises(ValueError):
                validate_certificate_scope(changed, scope)

    def test_fifteen_second_deadline_falls_back_before_emission_reserve(self) -> None:
        self.assertFalse(deadline_fallback_required(elapsed_ms=14400, emission_reserve_ms=500))
        self.assertTrue(deadline_fallback_required(elapsed_ms=14500, emission_reserve_ms=500))

    def test_disjoint_slice_control_requires_supremum_propagation(self) -> None:
        # Two child residuals occupy disjoint private-hand slices. Pointwise
        # policy mixing can expose either residual, so the parent sup bound is
        # max(child sup), not an average over disjoint support.
        left = (1.0, 0.0)
        right = (0.0, 1.0)
        policies = ((1.0, 0.0), (0.0, 1.0))
        parent = tuple(
            policies[index][0] * left[index] + policies[index][1] * right[index]
            for index in range(2)
        )
        self.assertEqual(max(abs(value) for value in parent), 1.0)
        self.assertEqual(max(max(map(abs, left)), max(map(abs, right))), 1.0)
        mean_child_absolute_error = max(
            sum(map(abs, child)) / len(child) for child in (left, right)
        )
        self.assertGreater(max(map(abs, parent)), mean_child_absolute_error)

    def test_zero_reach_fixed_utility_does_not_imply_zero_response_delta(self) -> None:
        game = KuhnPoker(3)
        blueprint = {}
        for player in range(game.num_players):
            for key, actions in collect_information_sets(game, player).items():
                blueprint[key] = {
                    action: float(index == 0) for index, action in enumerate(actions)
                }
        candidate = {key: dict(row) for key, row in blueprint.items()}
        off_path = next(
            key for key in candidate
            if key.startswith("p1|") and "history=p0:bet" in key
        )
        actions = tuple(candidate[off_path])
        candidate[off_path] = {
            action: float(index == 1) for index, action in enumerate(actions)
        }
        tape = CompiledPolicyDeltaTape(game, blueprint)
        result = tape.recertify_policy(candidate, mode="sparse")

        self.assertEqual(result.evaluation.utilities, tape.source_result.evaluation.utilities)
        self.assertNotEqual(
            result.evaluation.best_response_values,
            tape.source_result.evaluation.best_response_values,
        )
        # Every call remains source-relative; a later identity read cannot see
        # values left in the preceding epoch overlay.
        self.assertEqual(
            tape.recertify_policy(blueprint).evaluation,
            tape.source_result.evaluation,
        )


if __name__ == "__main__":
    unittest.main()
