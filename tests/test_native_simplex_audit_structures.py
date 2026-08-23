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
    _DigestStream as _Adr0293DigestStream,
)
from pontius.action_abstraction_confirmation import (
    _showdown_signs as _adr0293_showdown_signs,
)
from pontius.action_abstraction_confirmation import (
    _shuffled_deck as _adr0293_shuffled_deck,
)
from pontius.action_abstraction_confirmation import build_adr0293_confirmation_panel
from pontius.fresh_capacity_filling_qualification import (
    ADR0310_QUALIFIED_B_FAILURE_SHA256,
    bind_capacity_filling_context_to_oracle,
)
from pontius.fresh_capacity_filling_structures import (
    CapacityFillingStructureKind,
    build_adr0305_v4_structure,
)
from pontius.fresh_collision_repair_structures import (
    FreshStructureKind,
    build_adr0301_fresh_structure,
)
from pontius.native_simplex_audit_corpus import (
    ADR0311_BASE_CORPUS_SHA256,
    ADR0311_BASE_COUNT,
    ADR0311_COMPLETE_CORPUS_SHA256,
    ADR0311_KNOWN_BINDING_SHA256,
    ADR0311_KNOWN_FAILURE_SHA256,
    ADR0311_KNOWN_ORACLE_CONTEXT_SHA256,
    ADR0311_KNOWN_REGRESSION_INPUT_SHA256,
    ADR0311_KNOWN_STRUCTURAL_CONTEXT_SHA256,
    ADR0311_TRANSFORM_SEED_PREFIX,
    ADR0311_TRANSFORM_VERSION,
    ADR0311_VARIANT_CORPUS_SHA256,
    ADR0311_VARIANT_COUNT,
    ADR0311_VARIANTS_PER_BASE,
    AuditBaseFamily,
    AuditRowRole,
    AuditSizingArm,
    AuditVariantKind,
    build_adr0311_known_regression_context,
    build_adr0311_native_simplex_audit_corpus,
    materialize_audit_variant,
)
from pontius.native_simplex_audit_structures import (
    ADR0311_DEPENDENCY_GENERATOR_VERSION,
    ADR0311_MICRO_CASE_COUNT,
    ADR0311_MICRO_GENERATOR_VERSION,
    ADR0311_MICRO_OBJECTIVE_CANDIDATE_ATTEMPTS,
    ADR0311_MICRO_RANDOM_ROW_CANDIDATE_ATTEMPTS,
    ADR0311_MICRO_SEED,
    ADR0311_MICRO_STRUCTURE_SHA256,
    ADR0311_STRUCTURAL_FILTER_VERSION,
    ADR0311_WIDTH4_CONTEXT_COUNT,
    ADR0311_WIDTH4_GENERATOR_VERSION,
    ADR0311_WIDTH4_POTS,
    ADR0311_WIDTH4_RAW_CARD_CANDIDATE_COUNT,
    ADR0311_WIDTH4_SEED,
    ADR0311_WIDTH4_STACKS,
    ADR0311_WIDTH4_STRUCTURE_SHA256,
    AuditExactProbability,
    Sha256CounterStream,
    _showdown_signs,
    _shuffled_deck,
    build_adr0311_micro_lp_structure,
    build_adr0311_width_four_structure,
)
from pontius.reduced_river_sizing_lp import (
    LinearProgramConstraintUnit,
    LinearProgramVariableUnit,
)
from pontius.sizing_power_diagnostic import build_adr0295_sizing_power_pool
from pontius.width_four_sizing_power import build_adr0297_width_four_pool
from tests.test_reduced_river_sizing_lp import _float_hex, _legacy_formula
from tests.test_reduced_river_sizing_oracle import _contexts

_PRIOR_CONTEXT_COUNT = 988
_PRIOR_SEMANTIC_INVENTORY_SHA256 = (
    "8109c680918c689ca603a26cc19c846f3933cfd448f6c019da4755d08ae6155b"
)
_FRESH_SEMANTIC_INVENTORY_SHA256 = (
    "2553bbc6023eaebdf296d83b5ee130755934b433af3138c5239c7e8f9f26cbb5"
)
_DISJOINTNESS_EVIDENCE_SHA256 = "c5db1cecd1d31edc4847a9e9daec554ea90de165c4901384ee5bf4197809e653"
_SEALED_SOURCE_SHA256 = {
    "linear_program.py": "6069dac31bb2915284319d0d5551d5773f4b4cac294d07c440f4b4d9ee4c83f8",
    "native_simplex_audit_corpus.py": (
        "b65c301b9f0443b9f25da4da22fa7f8c15017cd63b4abe2670c5d98c32085918"
    ),
    "native_simplex_audit_structures.py": (
        "ea945d3ce76b38c893029884bcbda2280fc22ce66fdac30fdb09508929d39801"
    ),
    "reduced_river_sizing_lp.py": (
        "3a3ed588e90b84cdbc8186829fc7dac57d9ec40603f29dd5ddc70549748bd346"
    ),
    "reduced_river_sizing_oracle.py": (
        "3ea2dd0bff8b1ce2790138d466a1fcecb9c9e450ae4d73423215af71da8e3c84"
    ),
}


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
    encoded = json.dumps(
        sorted(_semantic_key(context) for context in contexts),
        allow_nan=False,
        separators=(",", ":"),
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


class NativeSimplexAuditStructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.micro = build_adr0311_micro_lp_structure()
        cls.width_four = build_adr0311_width_four_structure()
        cls.corpus = build_adr0311_native_simplex_audit_corpus()

    def test_exact_structures_rebuild_with_sealed_identities(self) -> None:
        rebuilt_micro = build_adr0311_micro_lp_structure()
        rebuilt_width_four = build_adr0311_width_four_structure()
        self.assertEqual(self.micro, rebuilt_micro)
        self.assertEqual(self.width_four, rebuilt_width_four)
        self.assertEqual(self.micro.seed, ADR0311_MICRO_SEED)
        self.assertEqual(self.micro.generator_version, ADR0311_MICRO_GENERATOR_VERSION)
        self.assertEqual(len(self.micro.cases), ADR0311_MICRO_CASE_COUNT)
        self.assertEqual(
            self.micro.random_row_candidate_attempts,
            ADR0311_MICRO_RANDOM_ROW_CANDIDATE_ATTEMPTS,
        )
        self.assertEqual(
            self.micro.objective_candidate_attempts,
            ADR0311_MICRO_OBJECTIVE_CANDIDATE_ATTEMPTS,
        )
        self.assertEqual(self.micro.digest, ADR0311_MICRO_STRUCTURE_SHA256)
        self.assertEqual(self.width_four.seed, ADR0311_WIDTH4_SEED)
        self.assertEqual(
            self.width_four.generator_version,
            ADR0311_WIDTH4_GENERATOR_VERSION,
        )
        self.assertEqual(len(self.width_four.contexts), ADR0311_WIDTH4_CONTEXT_COUNT)
        self.assertEqual(
            self.width_four.raw_card_candidate_count,
            ADR0311_WIDTH4_RAW_CARD_CANDIDATE_COUNT,
        )
        self.assertEqual(self.width_four.digest, ADR0311_WIDTH4_STRUCTURE_SHA256)

    def test_micro_inputs_are_exact_bounded_feasible_and_value_unopened(self) -> None:
        widths = tuple(case.variable_count for case in self.micro.cases)
        self.assertEqual(
            tuple(widths.count(width) for width in range(2, 6)),
            (12, 12, 12, 12),
        )
        for case in self.micro.cases:
            self.assertEqual(len(case.coefficients), 3 * case.variable_count + 3)
            self.assertTrue(any(case.objective))
            self.assertEqual(
                case.trusted_box_bounds,
                tuple((0, upper) for upper in case.upper_bounds),
            )
            for row, bound in zip(case.coefficients, case.bounds, strict=True):
                self.assertLessEqual(
                    sum(
                        coefficient * value
                        for coefficient, value in zip(
                            row,
                            case.feasible_witness,
                            strict=True,
                        )
                    ),
                    bound,
                )
        self.assertEqual(len({case.digest for case in self.micro.cases}), 48)

    def test_width_four_cards_ranges_grid_arms_and_diversity_are_exact(self) -> None:
        contexts = self.width_four.contexts
        self.assertEqual({context.pot for context in contexts}, set(ADR0311_WIDTH4_POTS))
        self.assertEqual(
            {context.stack for context in contexts},
            set(ADR0311_WIDTH4_STACKS),
        )
        self.assertEqual(
            tuple((context.pot, context.stack) for context in contexts[:4]),
            tuple((context.pot, context.stack) for context in contexts[60:]),
        )
        self.assertEqual(len({context.showdown_signs for context in contexts}), 64)
        for context in contexts:
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
            self.assertEqual(context.payoff_span, context.pot + 2 * context.stack)
        fresh_bases = tuple(
            base
            for base in self.corpus.bases
            if base.family is AuditBaseFamily.FRESH_REDUCED_SIZING
        )
        self.assertEqual(len(fresh_bases), 128)
        for context, minimum_all_in, full_integer in zip(
            contexts,
            fresh_bases[::2],
            fresh_bases[1::2],
            strict=True,
        ):
            self.assertEqual(minimum_all_in.bet_sizes, (2, context.stack))
            self.assertEqual(
                full_integer.bet_sizes,
                tuple(range(2, context.stack + 1)),
            )

    def test_fresh_contexts_are_disjoint_from_the_finite_inventory_through_adr0310(
        self,
    ) -> None:
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
            *build_adr0305_v4_structure(kind=CapacityFillingStructureKind.REPRESENTATIVE).contexts,
            *build_adr0305_v4_structure(kind=CapacityFillingStructureKind.QUALIFIED_A).contexts,
            *build_adr0305_v4_structure(kind=CapacityFillingStructureKind.QUALIFIED_B).contexts,
        )
        fresh = self.width_four.contexts
        prior_keys = {_semantic_key(context) for context in prior}
        fresh_keys = {_semantic_key(context) for context in fresh}
        self.assertEqual(len(prior), _PRIOR_CONTEXT_COUNT)
        self.assertEqual(len(prior_keys), _PRIOR_CONTEXT_COUNT)
        self.assertEqual(_inventory_digest(prior), _PRIOR_SEMANTIC_INVENTORY_SHA256)
        self.assertEqual(len(fresh_keys), ADR0311_WIDTH4_CONTEXT_COUNT)
        self.assertEqual(_inventory_digest(fresh), _FRESH_SEMANTIC_INVENTORY_SHA256)
        self.assertFalse(prior_keys & fresh_keys)
        evidence = {
            "fresh_count": len(fresh),
            "fresh_inventory_sha256": _inventory_digest(fresh),
            "fresh_unique": len(fresh_keys),
            "prior_count": len(prior),
            "prior_fresh_overlap": len(prior_keys & fresh_keys),
            "prior_inventory_sha256": _inventory_digest(prior),
            "prior_unique": len(prior_keys),
            "version": "adr0311-finite-semantic-disjointness-through-adr0310-v1",
        }
        self.assertEqual(
            hashlib.sha256(
                json.dumps(
                    evidence,
                    allow_nan=False,
                    separators=(",", ":"),
                    sort_keys=True,
                ).encode("ascii")
            ).hexdigest(),
            _DISJOINTNESS_EVIDENCE_SHA256,
        )

    def test_known_regression_snapshot_binds_only_the_disclosed_adr0310_input(
        self,
    ) -> None:
        prior = build_adr0305_v4_structure(kind=CapacityFillingStructureKind.QUALIFIED_B).contexts[
            21
        ]
        known = build_adr0311_known_regression_context()
        binding = bind_capacity_filling_context_to_oracle(prior)
        self.assertEqual(_semantic_payload(known), _semantic_payload(prior))
        self.assertEqual(
            binding.structural_context_digest,
            ADR0311_KNOWN_STRUCTURAL_CONTEXT_SHA256,
        )
        self.assertEqual(binding.oracle_context.digest, ADR0311_KNOWN_ORACLE_CONTEXT_SHA256)
        self.assertEqual(binding.digest, ADR0311_KNOWN_BINDING_SHA256)
        self.assertEqual(ADR0310_QUALIFIED_B_FAILURE_SHA256, ADR0311_KNOWN_FAILURE_SHA256)
        known_base = self.corpus.bases[0]
        self.assertIs(known_base.family, AuditBaseFamily.KNOWN_REGRESSION)
        self.assertEqual(
            known_base.source_input_sha256,
            ADR0311_KNOWN_REGRESSION_INPUT_SHA256,
        )
        self.assertEqual(known_base.variable_count, 236)
        self.assertEqual(known_base.row_count, 240)
        self.assertEqual(known_base.bet_sizes, tuple(range(2, 31)))

    def test_every_sizing_base_is_bit_exact_to_the_independent_legacy_formula(
        self,
    ) -> None:
        contexts_and_bases = (
            (build_adr0311_known_regression_context(), self.corpus.bases[0]),
            *(
                (context, base)
                for context, pair_start in zip(
                    self.width_four.contexts,
                    range(1 + ADR0311_MICRO_CASE_COUNT, ADR0311_BASE_COUNT, 2),
                    strict=True,
                )
                for base in self.corpus.bases[pair_start : pair_start + 2]
            ),
        )
        self.assertEqual(len(contexts_and_bases), 129)
        for context, base in contexts_and_bases:
            assert base.bet_sizes is not None
            objective, coefficients, bounds = _legacy_formula(
                context,  # type: ignore[arg-type]
                base.bet_sizes,
            )
            self.assertEqual(_float_hex(base.objective), _float_hex(objective))
            self.assertEqual(
                _float_hex(base.coefficients),
                _float_hex(coefficients),
            )
            self.assertEqual(_float_hex(base.bounds), _float_hex(bounds))

    def test_base_and_variant_manifests_are_complete_exact_and_rebuildable(self) -> None:
        self.assertEqual(len(self.corpus.bases), ADR0311_BASE_COUNT)
        self.assertEqual(len(self.corpus.variants), ADR0311_VARIANT_COUNT)
        self.assertEqual(ADR0311_VARIANTS_PER_BASE, 5)
        self.assertEqual(self.corpus.base_corpus_digest, ADR0311_BASE_CORPUS_SHA256)
        self.assertEqual(
            self.corpus.variant_corpus_digest,
            ADR0311_VARIANT_CORPUS_SHA256,
        )
        self.assertEqual(self.corpus.digest, ADR0311_COMPLETE_CORPUS_SHA256)
        self.assertEqual(
            {variant.kind for variant in self.corpus.variants},
            set(AuditVariantKind),
        )
        self.assertTrue(
            all(
                variant.seed == f"{ADR0311_TRANSFORM_SEED_PREFIX}:{variant.base_sha256}"
                for variant in self.corpus.variants
            )
        )
        self.assertEqual(ADR0311_TRANSFORM_VERSION, "exact-lp-metamorphic-variants-v1")
        rebuilt = build_adr0311_native_simplex_audit_corpus()
        self.assertEqual(rebuilt.base_corpus_digest, self.corpus.base_corpus_digest)
        self.assertEqual(rebuilt.variant_corpus_digest, self.corpus.variant_corpus_digest)
        self.assertEqual(rebuilt.digest, self.corpus.digest)

    def test_variant_maps_directions_units_scaling_and_redundancy_are_exact(self) -> None:
        selected_bases = (self.corpus.bases[1], self.corpus.bases[-1])
        by_id = {variant.variant_id: variant for variant in self.corpus.variants}
        for base in selected_bases:
            variants = tuple(by_id[f"{base.base_id}--{kind.value}"] for kind in AuditVariantKind)
            canonical = materialize_audit_variant(base=base, descriptor=variants[0])
            self.assertEqual(canonical.digest, base.linear_program_digest)
            row_permutation = variants[1]
            self.assertEqual(
                set(row_permutation.variant_to_canonical_rows),
                set(range(base.row_count)),
            )
            variable_permutation = variants[2]
            materialized_variables = materialize_audit_variant(
                base=base,
                descriptor=variable_permutation,
            )
            for variant_index, canonical_index in enumerate(
                variable_permutation.variant_to_canonical_variables
            ):
                self.assertEqual(
                    materialized_variables.objective[variant_index].hex(),
                    base.objective[canonical_index].hex(),
                )
                self.assertEqual(
                    materialized_variables.variable_units[variant_index],
                    base.variable_units[canonical_index],
                )
            scaled = variants[3]
            materialized_scaled = materialize_audit_variant(
                base=base,
                descriptor=scaled,
            )
            for variant_row, (origin, exponent) in enumerate(
                zip(
                    scaled.variant_to_canonical_rows,
                    scaled.row_scale_exponents,
                    strict=True,
                )
            ):
                self.assertIsNotNone(origin)
                assert origin is not None
                factor = float(2**exponent)
                self.assertEqual(
                    tuple(value.hex() for value in materialized_scaled.coefficients[variant_row]),
                    tuple((value * factor).hex() for value in base.coefficients[origin]),
                )
                self.assertEqual(
                    materialized_scaled.bounds[variant_row].hex(),
                    (base.bounds[origin] * factor).hex(),
                )
                self.assertEqual(scaled.row_units[variant_row], base.row_units[origin])
            redundancy = variants[4]
            materialized_redundancy = materialize_audit_variant(
                base=base,
                descriptor=redundancy,
            )
            duplicate_count = max(1, (base.row_count + 7) // 8)
            self.assertEqual(
                redundancy.row_roles.count(AuditRowRole.DUPLICATE),
                duplicate_count,
            )
            self.assertEqual(
                redundancy.row_roles.count(AuditRowRole.ZERO_REDUNDANCY),
                1,
            )
            zero_index = redundancy.row_roles.index(AuditRowRole.ZERO_REDUNDANCY)
            self.assertEqual(
                materialized_redundancy.coefficients[zero_index],
                (0.0,) * base.variable_count,
            )
            self.assertEqual(materialized_redundancy.bounds[zero_index], 0.0)
            self.assertIs(
                redundancy.row_units[zero_index],
                LinearProgramConstraintUnit.DIMENSIONLESS,
            )
            for canonical_index, positions in enumerate(redundancy.canonical_to_variant_rows):
                self.assertTrue(positions)
                self.assertTrue(
                    all(
                        redundancy.variant_to_canonical_rows[position] == canonical_index
                        for position in positions
                    )
                )

    def test_inherited_stream_shuffle_and_showdown_semantics_match(self) -> None:
        self.assertEqual(
            ADR0311_DEPENDENCY_GENERATOR_VERSION,
            "sha256-fisher-yates-structural-river-panel-v1",
        )
        self.assertEqual(
            ADR0311_STRUCTURAL_FILTER_VERSION,
            "width4-both-signs-three-rows-three-columns-v1",
        )
        for seed in (ADR0311_MICRO_SEED, ADR0311_WIDTH4_SEED):
            inherited = _Adr0293DigestStream(seed)
            successor = Sha256CounterStream(seed)
            for bound in (2, 3, 5, 7, 9, 10, 16, 52, 97, 65_537):
                self.assertEqual(successor.randbelow(bound), inherited.randbelow(bound))
        inherited = _Adr0293DigestStream(ADR0311_WIDTH4_SEED)
        successor = Sha256CounterStream(ADR0311_WIDTH4_SEED)
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

    def test_structure_and_corpus_sources_are_value_candidate_and_backend_free(self) -> None:
        root = Path(__file__).parents[1] / "src" / "pontius"
        expectations = {
            "native_simplex_audit_structures.py": {"river"},
            "native_simplex_audit_corpus.py": {
                "native_simplex_audit_structures",
                "reduced_river_sizing_lp",
            },
        }
        for relative, expected_imports in expectations.items():
            path = root / relative
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
            self.assertEqual(local_imports, expected_imports)
            self.assertFalse(
                imported_names
                & {
                    "maximize_linear_program",
                    "solve_reduced_river_sizing",
                    "certify_linear_program",
                    "linprog",
                }
            )
            self.assertNotIn("scipy", source)
            self.assertNotIn("numpy", source)
            self.assertNotIn("value_chips", source)
            self.assertNotIn("opening_policy", source)

    def test_new_sources_are_sealed_and_native_simplex_remains_byte_frozen(self) -> None:
        root = Path(__file__).parents[1] / "src" / "pontius"
        self.assertEqual(
            {
                relative: hashlib.sha256((root / relative).read_bytes()).hexdigest()
                for relative in _SEALED_SOURCE_SHA256
            },
            _SEALED_SOURCE_SHA256,
        )

    def test_mutation_wrong_units_collisions_and_mutability_fail_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "seed"):
            replace(self.micro, seed="wrong")
        with self.assertRaisesRegex(ValueError, "attempt"):
            replace(
                self.micro,
                random_row_candidate_attempts=(self.micro.random_row_candidate_attempts + 1),
            )
        with self.assertRaisesRegex(ValueError, "repeats"):
            repeated_micro = list(self.micro.cases)
            repeated_micro[4] = replace(
                repeated_micro[0],
                case_id=repeated_micro[4].case_id,
            )
            replace(
                self.micro,
                cases=tuple(repeated_micro),
            )
        with self.assertRaisesRegex(ValueError, "repeats a semantic"):
            repeated_contexts = list(self.width_four.contexts)
            repeated_contexts[60] = replace(
                repeated_contexts[0],
                context_id=repeated_contexts[60].context_id,
            )
            replace(
                self.width_four,
                contexts=tuple(repeated_contexts),
            )
        with self.assertRaisesRegex(ValueError, "sum exactly"):
            first = self.width_four.contexts[0]
            changed = AuditExactProbability(
                first.joint_probabilities[0][0].numerator + 1,
                first.joint_probabilities[0][0].denominator,
            )
            replace(
                first,
                joint_probabilities=(
                    (changed, *first.joint_probabilities[0][1:]),
                    *first.joint_probabilities[1:],
                ),
            )
        first_variant = self.corpus.variants[0]
        with self.assertRaisesRegex(ValueError, "permutation"):
            replace(
                first_variant,
                variant_to_canonical_variables=(0,)
                * len(first_variant.variant_to_canonical_variables),
            )
        with self.assertRaisesRegex(TypeError, "semantic"):
            replace(
                first_variant,
                variable_units=(
                    "dimensionless",  # type: ignore[arg-type]
                    *first_variant.variable_units[1:],
                ),
            )
        with self.assertRaises(FrozenInstanceError):
            self.micro.seed = "mutable"  # type: ignore[misc]
        self.assertIs(
            self.corpus.bases[1].variable_units[0],
            LinearProgramVariableUnit.DIMENSIONLESS_GENERIC,
        )
        self.assertEqual(
            tuple(AuditSizingArm),
            (AuditSizingArm.MINIMUM_ALL_IN, AuditSizingArm.FULL_INTEGER),
        )


if __name__ == "__main__":
    unittest.main()
