from __future__ import annotations

import ast
from dataclasses import fields, replace
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest

import pontius.legal_h4_factorized_affine_confirmation_population as population
from pontius.evaluation import collect_information_sets
from pontius.legal_decision_spine_v2 import public_betting_state_sha256
from pontius.legal_h4_factorized_affine_confirmation_population import (
    ADR0360_CONFIRMATION_CONTEXT_COUNT,
    ADR0360_CONFIRMATION_PRIVATE_WIDTH,
    ADR0360_CONFIRMATION_PROTOCOL,
    ADR0360_CONFIRMATION_PROTOCOL_SHA256,
    ADR0360_CONFIRMATION_SEED,
    ADR0360_CONFIRMATION_SEED_SHA256,
    ADR0360_CONFIRMATION_WEIGHT_DENOMINATOR,
    ADR0360_MECHANISM_SOURCE_COMMIT,
    FreshLegalH4ConfirmationContext,
    build_adr0360_confirmation_population,
    checked_to_confirmation_river,
    legal_h4_confirmation_source_policy,
    policy_sha256,
)
from pontius.legal_h4_factorized_affine_confirmation_population_seal import (
    ADR0360_CONFIRMATION_CANONICAL_BYTES,
    ADR0360_CONFIRMATION_CONTEXT_SHA256S,
    ADR0360_CONFIRMATION_GAME_PROVENANCE_SHA256S,
    ADR0360_CONFIRMATION_POLICY_SHA256S,
    ADR0360_CONFIRMATION_POPULATION_SHA256,
    ADR0360_CONFIRMATION_PROTOCOL_SHA256 as SEALED_PROTOCOL_SHA256,
    ADR0360_CONFIRMATION_PUBLIC_STATE_SHA256,
    ADR0360_CONFIRMATION_SOURCE_MANIFEST,
    ADR0360_DEVELOPMENT_SEMANTIC_SHA256,
)
from pontius.legal_h4_selector_fixture import (
    BOARD as DEVELOPMENT_BOARD,
    JOINT_WEIGHT_NUMERATORS as DEVELOPMENT_WEIGHTS,
    RESPONDER_HANDS as DEVELOPMENT_RESPONDER_HANDS,
    ROOT_HANDS as DEVELOPMENT_ROOT_HANDS,
)
from pontius.no_limit_betting import BettingActionKind
from pontius.river import RiverDeal, format_card, make_hole, parse_card


def _canonical_sha256(value: object) -> str:
    return sha256(
        json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()


def _independent_context(candidate_ordinal: int) -> FreshLegalH4ConfirmationContext:
    prefix = f"{ADR0360_CONFIRMATION_SEED}|candidate={candidate_ordinal}|card="
    deck = tuple(
        sorted(
            (format_card(card) for card in range(52)),
            key=lambda card: (
                sha256(f"{prefix}{card}".encode("ascii")).digest(),
                card,
            ),
        )
    )
    board = tuple(sorted(deck[:5], key=parse_card))
    roots = tuple(
        tuple(sorted(deck[index : index + 2], key=parse_card))
        for index in range(5, 13, 2)
    )
    responders = tuple(
        tuple(sorted(deck[index : index + 2], key=parse_card))
        for index in range(13, 21, 2)
    )
    weights = [1] * 16
    for allocation in range(48):
        digest = sha256(
            (
                f"{ADR0360_CONFIRMATION_SEED}|candidate={candidate_ordinal}|"
                f"weight-allocation={allocation}"
            ).encode("ascii")
        ).digest()
        weights[int.from_bytes(digest[:8], "big") % 16] += 1
    return FreshLegalH4ConfirmationContext(
        context_id=f"adr0360-legal-h4-confirmation-{candidate_ordinal:02d}",
        candidate_ordinal=candidate_ordinal,
        board=board,
        root_hands=roots,  # type: ignore[arg-type]
        responder_hands=responders,  # type: ignore[arg-type]
        joint_weight_numerators=tuple(
            tuple(weights[row * 4 : (row + 1) * 4]) for row in range(4)
        ),
        joint_weight_denominator=64,
    )


class LegalH4FactorizedAffineConfirmationPopulationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.pool = build_adr0360_confirmation_population()

    def test_source_protocol_seed_and_import_boundary_are_value_unopened(self) -> None:
        self.assertEqual(
            "23c7f023e686b8b84bc1145381c5fe7ba99dc8d4",
            ADR0360_MECHANISM_SOURCE_COMMIT,
        )
        self.assertEqual(
            "pontius|adr-0360|legal-h4-factorized-affine-confirmation|"
            "mechanism-commit=23c7f023e686b8b84bc1145381c5fe7ba99dc8d4",
            ADR0360_CONFIRMATION_SEED,
        )
        self.assertEqual(
            sha256(ADR0360_CONFIRMATION_SEED.encode("ascii")).hexdigest(),
            ADR0360_CONFIRMATION_SEED_SHA256,
        )
        self.assertEqual(SEALED_PROTOCOL_SHA256, ADR0360_CONFIRMATION_PROTOCOL_SHA256)
        self.assertEqual(
            ADR0360_CONFIRMATION_PROTOCOL_SHA256,
            _canonical_sha256(dict(ADR0360_CONFIRMATION_PROTOCOL)),
        )
        with self.assertRaises(TypeError):
            ADR0360_CONFIRMATION_PROTOCOL["confirmation_context_count"] = 1  # type: ignore[index]
        root = Path(population.__file__).resolve().parent
        actual_manifest = {
            name: sha256(
                (root / name).read_bytes().replace(bytes((13, 10)), b"\n")
            ).hexdigest()
            for name in ADR0360_CONFIRMATION_SOURCE_MANIFEST
        }
        self.assertEqual(dict(ADR0360_CONFIRMATION_SOURCE_MANIFEST), actual_manifest)
        with self.assertRaises(TypeError):
            ADR0360_CONFIRMATION_SOURCE_MANIFEST["river.py"] = "0" * 64  # type: ignore[index]

        source_path = Path(population.__file__)
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        imported: set[str] = set()
        names: set[str] = set()
        attributes: set[str] = set()
        function_names: set[str] = set()
        string_literals: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                imported.add(node.module)
                names.update(alias.name for alias in node.names)
            elif isinstance(node, ast.Name):
                names.add(node.id)
            elif isinstance(node, ast.Attribute):
                attributes.add(node.attr)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                function_names.add(node.name)
            elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                string_literals.add(node.value)
        forbidden_import_fragments = (
            "factorized_tie_aware_affine",
            "selector_window",
            "row_growth_audit",
            "factorized_affine_result",
            "directional_face_result",
        )
        self.assertFalse(
            any(
                fragment in module
                for module in imported
                for fragment in forbidden_import_fragments
            )
        )
        forbidden_names = {
            "TabularCFR",
            "audit_one_seat_row_growth",
            "best_response",
            "build_factorized_tie_aware_affine_section",
            "evaluate_seven",
            "exact_directional_best_response_face",
        }
        self.assertTrue(names.isdisjoint(forbidden_names))
        self.assertNotIn("utility", attributes)
        self.assertNotIn("write_bytes", attributes)
        self.assertFalse(any(name.startswith("run_") for name in function_names))
        self.assertFalse(
            any(
                "experiments/results/legal-responder-raise-h4-factorized-affine-v1.json"
                in literal
                for literal in string_literals
            )
        )

        with tempfile.TemporaryDirectory() as directory:
            copy = Path(directory) / "population.py"
            normalized = source_path.read_bytes().replace(bytes((13, 10)), b"\n")
            copy.write_bytes(normalized.replace(b"\n", bytes((13, 10))))
            self.assertEqual(
                sha256(normalized).hexdigest(),
                sha256(copy.read_bytes().replace(bytes((13, 10)), b"\n")).hexdigest(),
            )

    def test_first_four_candidates_reproduce_independently_without_filtering(self) -> None:
        independent = tuple(
            _independent_context(index)
            for index in range(ADR0360_CONFIRMATION_CONTEXT_COUNT)
        )
        self.assertEqual(
            tuple(context.semantic_payload for context in independent),
            tuple(context.semantic_payload for context in self.pool.contexts),
        )
        self.assertEqual(
            tuple(context.semantic_digest for context in independent),
            ADR0360_CONFIRMATION_CONTEXT_SHA256S,
        )
        self.assertEqual(
            tuple(range(ADR0360_CONFIRMATION_CONTEXT_COUNT)),
            tuple(context.candidate_ordinal for context in self.pool.contexts),
        )

    def test_population_context_policy_and_game_identities_are_exact(self) -> None:
        self.assertEqual(ADR0360_CONFIRMATION_POPULATION_SHA256, self.pool.digest)
        self.assertEqual(ADR0360_CONFIRMATION_CANONICAL_BYTES, len(self.pool.canonical_bytes))
        self.assertEqual(
            ADR0360_DEVELOPMENT_SEMANTIC_SHA256,
            self.pool.development_semantic_digest,
        )
        self.assertEqual(
            ADR0360_CONFIRMATION_CONTEXT_SHA256S,
            tuple(context.semantic_digest for context in self.pool.contexts),
        )
        self.assertEqual(
            ADR0360_CONFIRMATION_POLICY_SHA256S,
            tuple(
                policy_sha256(legal_h4_confirmation_source_policy(context))
                for context in self.pool.contexts
            ),
        )
        self.assertEqual(
            ADR0360_CONFIRMATION_GAME_PROVENANCE_SHA256S,
            tuple(context.build_game().provenance_digest for context in self.pool.contexts),
        )
        self.assertEqual(
            self.pool.canonical_bytes,
            build_adr0360_confirmation_population().canonical_bytes,
        )

    def test_every_context_is_collision_free_kernel_legal_h4_with_exact_dyadic_mass(self) -> None:
        state = checked_to_confirmation_river()
        decision = state.legal_decision()
        self.assertEqual(
            (BettingActionKind.CHECK, BettingActionKind.RAISE),
            decision.action_kinds,
        )
        self.assertIsNotNone(decision.raise_bounds)
        assert decision.raise_bounds is not None
        self.assertEqual((2, 4), (
            decision.raise_bounds.minimum_raise_to,
            decision.raise_bounds.maximum_raise_to,
        ))
        public_digest = public_betting_state_sha256(state)
        self.assertEqual(ADR0360_CONFIRMATION_PUBLIC_STATE_SHA256, public_digest)

        for context in self.pool.contexts:
            with self.subTest(context=context.context_id):
                cards = (
                    *context.board,
                    *(card for hand in context.root_hands for card in hand),
                    *(card for hand in context.responder_hands for card in hand),
                )
                self.assertEqual(21, len(set(cards)))
                self.assertEqual(public_digest, context.semantic_payload["betting_state_sha256"])
                self.assertEqual(64, sum(
                    value
                    for row in context.joint_weight_numerators
                    for value in row
                ))
                game = context.build_game()
                self.assertEqual(16, len(game.deals))
                probability_by_deal = dict(game.deals)
                for root_index, root in enumerate(context.root_hands):
                    for responder_index, responder in enumerate(context.responder_hands):
                        deal = RiverDeal(make_hole(*root), make_hole(*responder))
                        expected = Fraction(
                            context.joint_weight_numerators[root_index][responder_index],
                            64,
                        )
                        self.assertEqual(float(expected), probability_by_deal[deal])
                self.assertEqual(1.0, sum(probability_by_deal.values()))
                acting_sets = collect_information_sets(game, 0)
                histories = {
                    key.rsplit("|history=", 1)[1] for key in acting_sets
                }
                self.assertEqual(
                    {
                        "root",
                        "p0:raise-to-2/p1:raise-to-4",
                        "p0:raise-to-3/p1:raise-to-4",
                    },
                    histories,
                )
                policy = legal_h4_confirmation_source_policy(context, game)
                self.assertTrue(policy)
                for row in policy.values():
                    self.assertEqual(1.0, sum(row.values()))
                    self.assertTrue(all(value > 0.0 for value in row.values()))

    def test_protocol_freezes_complete_schema_work_and_conjunctive_interpretation(self) -> None:
        protocol = ADR0360_CONFIRMATION_PROTOCOL
        self.assertEqual(ADR0360_CONFIRMATION_CONTEXT_COUNT, protocol["confirmation_context_count"])
        self.assertEqual(ADR0360_CONFIRMATION_PRIVATE_WIDTH, protocol["private_width"])
        self.assertEqual(ADR0360_CONFIRMATION_WEIGHT_DENOMINATOR, protocol["weight_denominator"])
        self.assertEqual(4, protocol["direction_count_per_context"])
        self.assertEqual((0, 1), protocol["target_players"])
        self.assertEqual(
            ADR0360_CONFIRMATION_CONTEXT_COUNT
            * int(protocol["direction_count_per_context"])
            * len(protocol["target_players"]),  # type: ignore[arg-type]
            protocol["expected_sections"],
        )
        self.assertEqual(8, len(protocol["required_raw_section_fields"]))  # type: ignore[arg-type]
        raw = "|".join(protocol["required_raw_section_fields"])  # type: ignore[arg-type]
        for required in (
            "complete_cells_segments_points",
            "cell_gain_rows.complete_tapes",
            "samples.every_scale",
            "every_information_set_factor",
            "source_face.complete_factors",
            "pieces.complete_domains",
            "selector_window.complete_float_hex",
            "every_fan_row_by_every_point_exact_residual",
        ):
            self.assertIn(required, raw)
        self.assertIn("any_context_direction_target", protocol["failure_interpretation"])
        self.assertIn("without_drop_reseed_retry", protocol["failure_interpretation"])
        self.assertEqual(0, protocol["response_tape_materialization_limit"])
        self.assertEqual(
            (
                "one_step_dcfr_regret_vertex_per_public_history",
                "one_step_dcfr_regret_vertex_per_public_history",
                "one_step_dcfr_regret_vertex_per_public_history",
                "converged_one_seat_row_growth_proposal",
            ),
            protocol["direction_classes_in_order"],
        )
        self.assertEqual(0.25, protocol["row_growth_guard"])
        self.assertEqual(7, len(protocol["row_growth_acceptance"]))  # type: ignore[arg-type]
        self.assertIn(
            "all_response_rows_exactly_rebound",
            protocol["row_growth_acceptance"],  # type: ignore[operator]
        )
        self.assertEqual(128, protocol["row_growth_max_iterations"])
        self.assertEqual(1e-10, protocol["row_growth_tolerance"])
        self.assertEqual(
            (
                "p0:raise-to-2/p1:raise-to-4",
                "p0:raise-to-3/p1:raise-to-4",
                "root",
            ),
            protocol["direction_regret_public_histories_in_order"],
        )

        forbidden_fields = {
            "affine_result",
            "best_response",
            "candidate_value",
            "elapsed_seconds",
            "fan",
            "regret",
            "selected_direction",
            "selector",
        }
        self.assertTrue(
            {field.name for field in fields(FreshLegalH4ConfirmationContext)}.isdisjoint(
                forbidden_fields
            )
        )

    def test_semantic_identity_reduces_probabilities_and_excludes_development(self) -> None:
        first = self.pool.contexts[0]
        doubled = population._semantic_payload(
            board=first.board,
            root_hands=first.root_hands,
            responder_hands=first.responder_hands,
            joint_weight_numerators=tuple(
                tuple(2 * value for value in row)
                for row in first.joint_weight_numerators
            ),
            joint_weight_denominator=128,
        )
        self.assertEqual(first.semantic_payload, doubled)
        self.assertEqual(first.semantic_digest, _canonical_sha256(doubled))
        self.assertNotIn(
            self.pool.development_semantic_digest,
            {context.semantic_digest for context in self.pool.contexts},
        )

        development = FreshLegalH4ConfirmationContext(
            context_id="adr0360-legal-h4-confirmation-00",
            candidate_ordinal=0,
            board=tuple(sorted(DEVELOPMENT_BOARD, key=parse_card)),
            root_hands=tuple(
                tuple(sorted(hand, key=parse_card)) for hand in DEVELOPMENT_ROOT_HANDS
            ),  # type: ignore[arg-type]
            responder_hands=tuple(
                tuple(sorted(hand, key=parse_card))
                for hand in DEVELOPMENT_RESPONDER_HANDS
            ),  # type: ignore[arg-type]
            joint_weight_numerators=tuple(
                tuple(2 * value for value in row) for row in DEVELOPMENT_WEIGHTS
            ),
            joint_weight_denominator=64,
        )
        self.assertEqual(
            self.pool.development_semantic_digest,
            development.semantic_digest,
        )
        with self.assertRaises(ValueError):
            replace(self.pool, contexts=(development, *self.pool.contexts[1:]))

    def test_nominal_corruptions_fail_closed(self) -> None:
        first = self.pool.contexts[0]
        with self.assertRaises(ValueError):
            replace(self.pool, mechanism_source_commit="0" * 40)
        with self.assertRaises(ValueError):
            replace(self.pool, seed=self.pool.seed + "x")
        with self.assertRaises(ValueError):
            replace(self.pool, contexts=tuple(reversed(self.pool.contexts)))
        with self.assertRaises(ValueError):
            replace(first, context_id="wrong")
        with self.assertRaises(TypeError):
            replace(first, candidate_ordinal=True)
        with self.assertRaises(ValueError):
            replace(first, board=(*first.board[:-1], first.board[0]))
        with self.assertRaises(ValueError):
            replace(first, board=tuple(reversed(first.board)))
        with self.assertRaises(ValueError):
            replace(first, joint_weight_denominator=32)
        with self.assertRaises(ValueError):
            replace(
                first,
                joint_weight_numerators=(
                    (0, *first.joint_weight_numerators[0][1:]),
                    *first.joint_weight_numerators[1:],
                ),
            )
        with self.assertRaises(ValueError):
            replace(
                first,
                joint_weight_numerators=(
                    (first.joint_weight_numerators[0][0] + 1, *first.joint_weight_numerators[0][1:]),
                    *first.joint_weight_numerators[1:],
                ),
            )
        with self.assertRaises(TypeError):
            legal_h4_confirmation_source_policy(object())  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            legal_h4_confirmation_source_policy(
                first,
                self.pool.contexts[1].build_game(),
            )


if __name__ == "__main__":
    unittest.main()
