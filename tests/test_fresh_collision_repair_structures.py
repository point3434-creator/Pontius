from __future__ import annotations

import ast
import hashlib
import json
import unittest
from dataclasses import FrozenInstanceError, replace
from fractions import Fraction
from pathlib import Path
from typing import Any

from test_reduced_river_sizing_oracle import _contexts

from pontius.action_abstraction_confirmation import (
    ADR0293_POTS,
    ADR0293_STACKS,
    build_adr0293_confirmation_panel,
)
from pontius.collision_repair_action_abstraction import (
    ADR0300_COLLISION_REPAIR_SOURCE_SHA256,
)
from pontius.fresh_collision_repair_structures import (
    ADR0301_COLLISION_REPAIR_SOURCE_SHA256,
    ADR0301_QUALIFIED_POOL_CANDIDATE_ATTEMPTS,
    ADR0301_QUALIFIED_POOL_CONTEXT_COUNT,
    ADR0301_QUALIFIED_POOL_SEED,
    ADR0301_QUALIFIED_POOL_SHA256,
    ADR0301_REPRESENTATIVE_CANDIDATE_ATTEMPTS,
    ADR0301_REPRESENTATIVE_CONTEXT_COUNT,
    ADR0301_REPRESENTATIVE_SEED,
    ADR0301_REPRESENTATIVE_SHA256,
    FreshExactProbability,
    FreshStructureKind,
    build_adr0301_fresh_structure,
)
from pontius.sizing_power_diagnostic import build_adr0295_sizing_power_pool
from pontius.width_four_sizing_power import (
    _structurally_admissible_width_four,
    build_adr0297_width_four_pool,
)

_PRIOR_CONTEXT_COUNT = 604
_PRIOR_SEMANTIC_INVENTORY_SHA256 = (
    "a6b1c8863c40f475ebdf05a16bde258138b483d9de8e08172609e78ea6d702ef"
)
_REPRESENTATIVE_SEMANTIC_INVENTORY_SHA256 = (
    "f22ee49b3217292e7b3db0a27e6720ab4ed8120ea4a904de6c31e0514ba424ec"
)
_QUALIFIED_POOL_SEMANTIC_INVENTORY_SHA256 = (
    "deac14a912d46d15997436e03514e61d738f37a59583cda684f266fb442ef8ff"
)
_DISJOINTNESS_EVIDENCE_SHA256 = (
    "a8db09b3800acfb53be14edc97f4ba9034cc38c2ec3410051bbc5e3483bacd97"
)


def _semantic_payload(context: Any) -> dict[str, object]:
    probabilities = context.joint_probabilities
    return {
        "board": context.board,
        "joint_probabilities": tuple(
            tuple(
                (probability.numerator, probability.denominator)
                for probability in row
            )
            for row in probabilities
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
    rendered = sorted(_semantic_key(context) for context in contexts)
    canonical = json.dumps(
        rendered,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("ascii")
    return hashlib.sha256(canonical).hexdigest()


class FreshCollisionRepairStructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.representative = build_adr0301_fresh_structure(
            kind=FreshStructureKind.REPRESENTATIVE
        )
        cls.qualified_pool = build_adr0301_fresh_structure(
            kind=FreshStructureKind.QUALIFIED_POOL
        )

    def test_structures_rebuild_exactly_with_sealed_identity_and_diversity(self) -> None:
        representative_again = build_adr0301_fresh_structure(
            kind=FreshStructureKind.REPRESENTATIVE
        )
        qualified_again = build_adr0301_fresh_structure(
            kind=FreshStructureKind.QUALIFIED_POOL
        )
        self.assertEqual(self.representative, representative_again)
        self.assertEqual(self.qualified_pool, qualified_again)
        self.assertEqual(self.representative.seed, ADR0301_REPRESENTATIVE_SEED)
        self.assertEqual(self.qualified_pool.seed, ADR0301_QUALIFIED_POOL_SEED)
        self.assertEqual(
            self.representative.candidate_attempts,
            ADR0301_REPRESENTATIVE_CANDIDATE_ATTEMPTS,
        )
        self.assertEqual(
            self.qualified_pool.candidate_attempts,
            ADR0301_QUALIFIED_POOL_CANDIDATE_ATTEMPTS,
        )
        self.assertEqual(
            len(self.representative.contexts),
            ADR0301_REPRESENTATIVE_CONTEXT_COUNT,
        )
        self.assertEqual(
            len(self.qualified_pool.contexts),
            ADR0301_QUALIFIED_POOL_CONTEXT_COUNT,
        )
        self.assertEqual(self.representative.digest, ADR0301_REPRESENTATIVE_SHA256)
        self.assertEqual(self.qualified_pool.digest, ADR0301_QUALIFIED_POOL_SHA256)
        self.assertEqual(
            ADR0301_COLLISION_REPAIR_SOURCE_SHA256,
            ADR0300_COLLISION_REPAIR_SOURCE_SHA256,
        )

        for structure in (self.representative, self.qualified_pool):
            self.assertEqual({context.pot for context in structure.contexts}, set(ADR0293_POTS))
            self.assertEqual(
                {context.stack for context in structure.contexts},
                set(ADR0293_STACKS),
            )
            self.assertEqual(
                len({context.showdown_signs for context in structure.contexts}),
                len(structure.contexts),
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
                self.assertTrue(
                    _structurally_admissible_width_four(context.showdown_signs)
                )
                self.assertEqual(context.payoff_span, context.pot + 2 * context.stack)

    def test_finite_prior_and_cross_family_inventories_are_disjoint(self) -> None:
        prior = (
            *_contexts(),
            *build_adr0293_confirmation_panel().contexts,
            *(
                context
                for batch_index in range(3)
                for context in build_adr0295_sizing_power_pool(
                    batch_index=batch_index
                ).contexts
            ),
            *(
                context
                for batch_index in range(3)
                for context in build_adr0297_width_four_pool(
                    batch_index=batch_index
                ).contexts
            ),
        )
        representative_keys = {
            _semantic_key(context) for context in self.representative.contexts
        }
        qualified_keys = {
            _semantic_key(context) for context in self.qualified_pool.contexts
        }
        prior_keys = {_semantic_key(context) for context in prior}

        self.assertEqual(len(prior), _PRIOR_CONTEXT_COUNT)
        self.assertEqual(len(prior_keys), _PRIOR_CONTEXT_COUNT)
        self.assertEqual(_inventory_digest(prior), _PRIOR_SEMANTIC_INVENTORY_SHA256)
        self.assertEqual(
            _inventory_digest(tuple(self.representative.contexts)),
            _REPRESENTATIVE_SEMANTIC_INVENTORY_SHA256,
        )
        self.assertEqual(
            _inventory_digest(tuple(self.qualified_pool.contexts)),
            _QUALIFIED_POOL_SEMANTIC_INVENTORY_SHA256,
        )
        self.assertFalse(prior_keys & representative_keys)
        self.assertFalse(prior_keys & qualified_keys)
        self.assertFalse(representative_keys & qualified_keys)

        evidence = {
            "prior_count": len(prior),
            "prior_inventory_sha256": _inventory_digest(prior),
            "prior_qualified_overlap": len(prior_keys & qualified_keys),
            "prior_representative_overlap": len(prior_keys & representative_keys),
            "prior_unique": len(prior_keys),
            "qualified_pool_count": len(qualified_keys),
            "qualified_pool_inventory_sha256": _inventory_digest(
                tuple(self.qualified_pool.contexts)
            ),
            "representative_count": len(representative_keys),
            "representative_inventory_sha256": _inventory_digest(
                tuple(self.representative.contexts)
            ),
            "representative_qualified_overlap": len(
                representative_keys & qualified_keys
            ),
            "version": "adr0301-finite-semantic-disjointness-v1",
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

    def test_source_inventory_is_value_candidate_and_integration_free(self) -> None:
        path = Path(__file__).parents[1] / "src" / "pontius" / (
            "fresh_collision_repair_structures.py"
        )
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported_modules = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module is not None
        }
        imported_names = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
            for alias in node.names
        }
        self.assertFalse(
            {
                "reduced_river_sizing_oracle",
                "collision_repair_action_abstraction",
                "legal_action_abstraction",
                "reference_hand_replay",
                "width_four_sizing_power_evaluation",
            }
            & imported_modules
        )
        self.assertFalse(
            {
                "solve_reduced_river_sizing",
                "solve_bounded_normal_form_sizing_teacher",
                "CollisionRepairActionAbstractionSource",
            }
            & imported_names
        )
        self.assertNotIn("value_chips", source)
        self.assertNotIn("opening_policy", source)

    def test_invalid_or_mutated_structures_fail_closed(self) -> None:
        with self.assertRaisesRegex(TypeError, "kind"):
            build_adr0301_fresh_structure(  # type: ignore[arg-type]
                kind="representative"
            )
        with self.assertRaisesRegex(ValueError, "seed"):
            replace(self.representative, seed="wrong")
        with self.assertRaisesRegex(ValueError, "generator"):
            replace(self.representative, generator_version="wrong")
        with self.assertRaisesRegex(ValueError, "attempt count"):
            replace(
                self.representative,
                candidate_attempts=self.representative.candidate_attempts + 1,
            )
        with self.assertRaisesRegex(ValueError, "ids or ordering"):
            replace(
                self.representative,
                contexts=tuple(reversed(self.representative.contexts)),
            )

        context = self.representative.contexts[0]
        with self.assertRaisesRegex(ValueError, "frozen set"):
            replace(context, pot=7)
        with self.assertRaisesRegex(ValueError, "21 distinct"):
            replace(
                context,
                responder_hands=(context.opener_hands[0], *context.responder_hands[1:]),
            )
        first = context.joint_probabilities[0][0]
        wrong_first = FreshExactProbability(first.numerator + 1, first.denominator)
        wrong_row = (wrong_first, *context.joint_probabilities[0][1:])
        with self.assertRaisesRegex(ValueError, "sum exactly"):
            replace(
                context,
                joint_probabilities=(wrong_row, *context.joint_probabilities[1:]),
            )
        with self.assertRaisesRegex(TypeError, "integer"):
            FreshExactProbability(True, 2)  # type: ignore[arg-type]
        with self.assertRaisesRegex(ValueError, "positive"):
            FreshExactProbability(0, 2)
        with self.assertRaises(FrozenInstanceError):
            self.representative.seed = "mutable"  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
