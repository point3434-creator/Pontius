from __future__ import annotations

import ast
import hashlib
import json
import unittest
from dataclasses import FrozenInstanceError, replace
from fractions import Fraction
from pathlib import Path
from typing import Any

from pontius.action_abstraction_confirmation import (
    ADR0293_GENERATOR_VERSION,
    ADR0293_POTS,
    ADR0293_STACKS,
    build_adr0293_confirmation_panel,
)
from pontius.action_abstraction_confirmation import (
    _DigestStream as _Adr0293DigestStream,
)
from pontius.action_abstraction_confirmation import (
    _showdown_signs as _adr0293_showdown_signs,
)
from pontius.action_abstraction_confirmation import (
    _shuffled_deck as _adr0293_shuffled_deck,
)
from pontius.fresh_capacity_filling_structures import (
    ADR0305_V4_DEPENDENCY_GENERATOR_VERSION,
    ADR0305_V4_POTS,
    ADR0305_V4_QUALIFIED_A_CANDIDATE_ATTEMPTS,
    ADR0305_V4_QUALIFIED_A_SEED,
    ADR0305_V4_QUALIFIED_A_SHA256,
    ADR0305_V4_QUALIFIED_B_CANDIDATE_ATTEMPTS,
    ADR0305_V4_QUALIFIED_B_SEED,
    ADR0305_V4_QUALIFIED_B_SHA256,
    ADR0305_V4_QUALIFIED_CONTEXT_COUNT,
    ADR0305_V4_REPRESENTATIVE_CANDIDATE_ATTEMPTS,
    ADR0305_V4_REPRESENTATIVE_CONTEXT_COUNT,
    ADR0305_V4_REPRESENTATIVE_SEED,
    ADR0305_V4_REPRESENTATIVE_SHA256,
    ADR0305_V4_SOURCE_COMMIT,
    ADR0305_V4_SOURCE_ID,
    ADR0305_V4_SOURCE_SHA256,
    ADR0305_V4_STACKS,
    ADR0305_V4_STRUCTURAL_FILTER_VERSION,
    ADR0305_V4_STRUCTURE_GENERATOR_VERSION,
    CapacityFillingExactProbability,
    CapacityFillingStructureKind,
    _DigestStream,
    _showdown_signs,
    _shuffled_deck,
    _structurally_admissible_width_four,
    build_adr0305_v4_structure,
)
from pontius.fresh_collision_repair_structures import (
    ADR0301_STRUCTURAL_FILTER_VERSION,
    FreshStructureKind,
    build_adr0301_fresh_structure,
)
from pontius.sizing_power_diagnostic import build_adr0295_sizing_power_pool
from pontius.width_four_sizing_power import build_adr0297_width_four_pool
from tests.test_reduced_river_sizing_oracle import _contexts

_PRIOR_CONTEXT_COUNT = 748
_PRIOR_SEMANTIC_INVENTORY_SHA256 = (
    "cbeae15bb963fa9117cffeb12fddf189d2bcf9b5b46a491d5f8065e0b88de683"
)
_REPRESENTATIVE_SEMANTIC_INVENTORY_SHA256 = (
    "6310faf33536eb822986f63bc2f691a03b9c3d92d22163c9a57736cd8e80097f"
)
_QUALIFIED_A_SEMANTIC_INVENTORY_SHA256 = (
    "448b857005c3d88a1dfe8a4179719c5249d7086bf41ea488b023bf5918b4bad8"
)
_QUALIFIED_B_SEMANTIC_INVENTORY_SHA256 = (
    "46e462dabb8b4c5d47f9699c4550d8c0c1806b1a9ef8a64eb14560ad9bb46905"
)
_DISJOINTNESS_EVIDENCE_SHA256 = "ee25807ce514b97b686595b328cf8c16b7812681309f9ba778bff4a26bda83d4"


def _semantic_payload(context: Any) -> dict[str, object]:
    return {
        "board": context.board,
        "joint_probabilities": tuple(
            tuple((probability.numerator, probability.denominator) for probability in row)
            for row in context.joint_probabilities
        ),
        "minimum_bet": context.minimum_bet,
        "opener_hands": context.opener_hands,
        "pot": context.pot,
        "responder_hands": context.responder_hands,
        "stack": context.stack,
    }


def _semantic_key(context: object) -> str:
    return json.dumps(
        _semantic_payload(context),
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def _inventory_digest(contexts: tuple[object, ...]) -> str:
    canonical = json.dumps(
        sorted(_semantic_key(context) for context in contexts),
        allow_nan=False,
        separators=(",", ":"),
    ).encode("ascii")
    return hashlib.sha256(canonical).hexdigest()


class FreshCapacityFillingStructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.representative = build_adr0305_v4_structure(
            kind=CapacityFillingStructureKind.REPRESENTATIVE
        )
        cls.qualified_a = build_adr0305_v4_structure(kind=CapacityFillingStructureKind.QUALIFIED_A)
        cls.qualified_b = build_adr0305_v4_structure(kind=CapacityFillingStructureKind.QUALIFIED_B)

    def test_structures_rebuild_in_frozen_order_with_exact_identities(self) -> None:
        structures = (self.representative, self.qualified_a, self.qualified_b)
        self.assertEqual(
            tuple(structure.kind for structure in structures),
            tuple(CapacityFillingStructureKind),
        )
        rebuilt = tuple(
            build_adr0305_v4_structure(kind=kind) for kind in CapacityFillingStructureKind
        )
        self.assertEqual(structures, rebuilt)
        self.assertEqual(
            tuple(structure.seed for structure in structures),
            (
                ADR0305_V4_REPRESENTATIVE_SEED,
                ADR0305_V4_QUALIFIED_A_SEED,
                ADR0305_V4_QUALIFIED_B_SEED,
            ),
        )
        self.assertEqual(
            tuple(structure.candidate_attempts for structure in structures),
            (
                ADR0305_V4_REPRESENTATIVE_CANDIDATE_ATTEMPTS,
                ADR0305_V4_QUALIFIED_A_CANDIDATE_ATTEMPTS,
                ADR0305_V4_QUALIFIED_B_CANDIDATE_ATTEMPTS,
            ),
        )
        self.assertEqual(
            tuple(len(structure.contexts) for structure in structures),
            (
                ADR0305_V4_REPRESENTATIVE_CONTEXT_COUNT,
                ADR0305_V4_QUALIFIED_CONTEXT_COUNT,
                ADR0305_V4_QUALIFIED_CONTEXT_COUNT,
            ),
        )
        self.assertEqual(
            tuple(structure.digest for structure in structures),
            (
                ADR0305_V4_REPRESENTATIVE_SHA256,
                ADR0305_V4_QUALIFIED_A_SHA256,
                ADR0305_V4_QUALIFIED_B_SHA256,
            ),
        )
        self.assertEqual(
            {structure.generator_version for structure in structures},
            {ADR0305_V4_STRUCTURE_GENERATOR_VERSION},
        )
        self.assertEqual(
            ADR0305_V4_SOURCE_COMMIT,
            "a6f7d4b20a67f00b67be40bf412a5e9ff32fc84d",
        )
        self.assertEqual(
            ADR0305_V4_SOURCE_ID,
            "adr-0305-capacity-filling-pot-odds-v4",
        )
        self.assertEqual(
            ADR0305_V4_SOURCE_SHA256,
            "37824e44b7793b10b081957fc8be387bdca5c565b4bfe2386ca13f7e1c785c8b",
        )

    def test_every_context_preserves_cards_ranges_filter_and_diversity(self) -> None:
        structures = (self.representative, self.qualified_a, self.qualified_b)
        expected_sign_counts = (48, 94, 96)
        for structure, sign_count in zip(
            structures,
            expected_sign_counts,
            strict=True,
        ):
            self.assertEqual(
                {context.pot for context in structure.contexts},
                set(ADR0305_V4_POTS),
            )
            self.assertEqual(
                {context.stack for context in structure.contexts},
                set(ADR0305_V4_STACKS),
            )
            self.assertEqual(
                len({context.showdown_signs for context in structure.contexts}),
                sign_count,
            )
            for context in structure.contexts:
                physical_cards = (
                    *context.board,
                    *(card for hand in context.opener_hands for card in hand),
                    *(card for hand in context.responder_hands for card in hand),
                )
                self.assertEqual(len(physical_cards), 21)
                self.assertEqual(len(set(physical_cards)), 21)
                self.assertEqual(
                    sum(
                        (
                            probability.fraction
                            for row in context.joint_probabilities
                            for probability in row
                        ),
                        start=Fraction(0),
                    ),
                    1,
                )
                self.assertTrue(_structurally_admissible_width_four(context.showdown_signs))
                self.assertEqual(context.payoff_span, context.pot + 2 * context.stack)

    def test_finite_prior_and_three_fresh_inventories_are_disjoint(self) -> None:
        prior = (
            *_contexts(),
            *build_adr0293_confirmation_panel().contexts,
            *(
                context
                for batch_index in range(3)
                for context in build_adr0295_sizing_power_pool(batch_index=batch_index).contexts
            ),
            *(
                context
                for batch_index in range(3)
                for context in build_adr0297_width_four_pool(batch_index=batch_index).contexts
            ),
            *build_adr0301_fresh_structure(kind=FreshStructureKind.REPRESENTATIVE).contexts,
            *build_adr0301_fresh_structure(kind=FreshStructureKind.QUALIFIED_POOL).contexts,
        )
        families = {
            "representative": self.representative.contexts,
            "qualified_a": self.qualified_a.contexts,
            "qualified_b": self.qualified_b.contexts,
        }
        prior_keys = {_semantic_key(context) for context in prior}
        keys = {
            name: {_semantic_key(context) for context in contexts}
            for name, contexts in families.items()
        }

        self.assertEqual(len(prior), _PRIOR_CONTEXT_COUNT)
        self.assertEqual(len(prior_keys), _PRIOR_CONTEXT_COUNT)
        self.assertEqual(_inventory_digest(prior), _PRIOR_SEMANTIC_INVENTORY_SHA256)
        self.assertEqual(
            _inventory_digest(families["representative"]),
            _REPRESENTATIVE_SEMANTIC_INVENTORY_SHA256,
        )
        self.assertEqual(
            _inventory_digest(families["qualified_a"]),
            _QUALIFIED_A_SEMANTIC_INVENTORY_SHA256,
        )
        self.assertEqual(
            _inventory_digest(families["qualified_b"]),
            _QUALIFIED_B_SEMANTIC_INVENTORY_SHA256,
        )
        self.assertFalse(prior_keys & keys["representative"])
        self.assertFalse(prior_keys & keys["qualified_a"])
        self.assertFalse(prior_keys & keys["qualified_b"])
        self.assertFalse(keys["representative"] & keys["qualified_a"])
        self.assertFalse(keys["representative"] & keys["qualified_b"])
        self.assertFalse(keys["qualified_a"] & keys["qualified_b"])

        evidence = {
            "prior_count": len(prior),
            "prior_inventory_sha256": _inventory_digest(prior),
            "prior_qualified_a_overlap": len(prior_keys & keys["qualified_a"]),
            "prior_qualified_b_overlap": len(prior_keys & keys["qualified_b"]),
            "prior_representative_overlap": len(prior_keys & keys["representative"]),
            "prior_unique": len(prior_keys),
            "qualified_a_count": len(keys["qualified_a"]),
            "qualified_a_inventory_sha256": _inventory_digest(families["qualified_a"]),
            "qualified_b_count": len(keys["qualified_b"]),
            "qualified_b_inventory_sha256": _inventory_digest(families["qualified_b"]),
            "qualified_a_qualified_b_overlap": len(keys["qualified_a"] & keys["qualified_b"]),
            "representative_count": len(keys["representative"]),
            "representative_inventory_sha256": _inventory_digest(families["representative"]),
            "representative_qualified_a_overlap": len(keys["representative"] & keys["qualified_a"]),
            "representative_qualified_b_overlap": len(keys["representative"] & keys["qualified_b"]),
            "version": "adr0305-v4-finite-semantic-disjointness-v1",
        }
        evidence_digest = hashlib.sha256(
            json.dumps(
                evidence,
                allow_nan=False,
                separators=(",", ":"),
                sort_keys=True,
            ).encode("ascii")
        ).hexdigest()
        self.assertEqual(evidence_digest, _DISJOINTNESS_EVIDENCE_SHA256)

    def test_inherited_stream_card_and_filter_semantics_match(self) -> None:
        self.assertEqual(
            ADR0305_V4_DEPENDENCY_GENERATOR_VERSION,
            ADR0293_GENERATOR_VERSION,
        )
        self.assertEqual(ADR0305_V4_POTS, ADR0293_POTS)
        self.assertEqual(ADR0305_V4_STACKS, ADR0293_STACKS)
        self.assertEqual(
            ADR0305_V4_STRUCTURAL_FILTER_VERSION,
            ADR0301_STRUCTURAL_FILTER_VERSION,
        )
        for seed in (
            ADR0305_V4_REPRESENTATIVE_SEED,
            ADR0305_V4_QUALIFIED_A_SEED,
            ADR0305_V4_QUALIFIED_B_SEED,
        ):
            inherited = _Adr0293DigestStream(seed)
            successor = _DigestStream(seed)
            for bound in (2, 3, 5, 7, 9, 10, 16, 52, 97, 65_537):
                self.assertEqual(
                    successor.randbelow(bound),
                    inherited.randbelow(bound),
                )
            inherited_deck = _adr0293_shuffled_deck(inherited)
            successor_deck = _shuffled_deck(successor)
            self.assertEqual(successor_deck, inherited_deck)
            board = successor_deck[:5]
            opener = tuple(
                tuple(sorted(successor_deck[offset : offset + 2])) for offset in range(5, 13, 2)
            )
            responder = tuple(
                tuple(sorted(successor_deck[offset : offset + 2])) for offset in range(13, 21, 2)
            )
            self.assertEqual(
                _showdown_signs(board, opener, responder),
                _adr0293_showdown_signs(board, opener, responder),
            )

    def test_source_inventory_is_candidate_value_and_integration_free(self) -> None:
        path = (
            Path(__file__).parents[1] / "src" / "pontius" / "fresh_capacity_filling_structures.py"
        )
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path), feature_version=(3, 11))
        local_imports = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.level == 1 and node.module is not None
        }
        imported_names = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
            for alias in node.names
        }
        self.assertEqual(local_imports, {"river"})
        self.assertEqual(imported_names & {"evaluate_seven"}, {"evaluate_seven"})
        forbidden = (
            "action_abstraction",
            "sizing_oracle",
            "evaluation",
            "qualification",
            "reference_hand",
            "blueprint",
            "convex",
            "resolver",
            "strategy",
        )
        self.assertFalse(any(any(part in module for part in forbidden) for module in local_imports))
        self.assertNotIn("solve_reduced_river_sizing", source)
        self.assertNotIn("value_chips", source)
        self.assertNotIn("opening_policy", source)

    def test_invalid_mutated_and_mutable_inputs_fail_closed(self) -> None:
        with self.assertRaisesRegex(TypeError, "kind"):
            build_adr0305_v4_structure(kind="representative")  # type: ignore[arg-type]
        with self.assertRaisesRegex(ValueError, "seed"):
            replace(self.representative, seed="wrong")
        with self.assertRaisesRegex(ValueError, "generator"):
            replace(self.representative, generator_version="wrong")
        with self.assertRaisesRegex(ValueError, "attempt"):
            replace(
                self.representative,
                candidate_attempts=self.representative.candidate_attempts + 1,
            )
        with self.assertRaisesRegex(ValueError, "ids or ordering"):
            replace(
                self.representative,
                contexts=tuple(reversed(self.representative.contexts)),
            )

        first, second, *remaining = self.representative.contexts
        duplicate = replace(first, context_id=second.context_id)
        with self.assertRaisesRegex(ValueError, "repeats a semantic context"):
            replace(
                self.representative,
                contexts=(first, duplicate, *remaining),
            )
        changed_pot = next(pot for pot in ADR0305_V4_POTS if pot != first.pot)
        mutated = replace(first, pot=changed_pot)
        with self.assertRaisesRegex(ValueError, "sealed identity"):
            replace(
                self.representative,
                contexts=(mutated, *self.representative.contexts[1:]),
            )
        with self.assertRaisesRegex(ValueError, "21 distinct"):
            replace(
                first,
                responder_hands=(first.opener_hands[0], *first.responder_hands[1:]),
            )
        probability = first.joint_probabilities[0][0]
        changed = CapacityFillingExactProbability(
            probability.numerator + 1,
            probability.denominator,
        )
        with self.assertRaisesRegex(ValueError, "sum exactly"):
            replace(
                first,
                joint_probabilities=(
                    (changed, *first.joint_probabilities[0][1:]),
                    *first.joint_probabilities[1:],
                ),
            )
        with self.assertRaisesRegex(TypeError, "integer"):
            CapacityFillingExactProbability(True, 2)  # type: ignore[arg-type]
        with self.assertRaisesRegex(ValueError, "positive"):
            CapacityFillingExactProbability(0, 2)
        with self.assertRaisesRegex(ValueError, "ASCII"):
            _DigestStream("non-ascii-µ")
        with self.assertRaisesRegex(TypeError, "integer"):
            _DigestStream("seed").randbelow(True)  # type: ignore[arg-type]
        with self.assertRaises(FrozenInstanceError):
            self.representative.seed = "mutable"  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
