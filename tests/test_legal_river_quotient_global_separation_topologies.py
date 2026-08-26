from __future__ import annotations

import ast
from dataclasses import replace
from hashlib import sha256
from math import comb, factorial
from pathlib import Path
import unittest
from unittest.mock import patch

from pontius import legal_river_quotient_base_provenance as base
from pontius import legal_river_quotient_global_separation_topologies as source
from pontius import legal_river_quotient_selective_certified_separation as prefix


ROOT = Path(__file__).parents[1]
CONFIG = ROOT / source.CONFIG_RELATIVE_PATH
RESULT = ROOT / source.RESULT_RELATIVE_PATH
SOURCE = Path(source.__file__)
BASE_SOURCE = Path(base.__file__)


def _digest(label: str) -> str:
    return sha256(("adr0455-test|" + label).encode("ascii")).hexdigest()


def _required_width(bound: int) -> tuple[int, int, int]:
    bits = 1 if bound == 0 else bound.bit_length() + 1
    mathematical = (bits + 63) // 64
    return bits, mathematical, mathematical + 1


def _hybrid_switch_input(cards: int) -> source.ExactPriceInput:
    control = source.make_control_input(cards, "all_zero_tie")
    producer = control.base_producer
    if not isinstance(producer, base.OpaqueBaseProducer):
        raise AssertionError("hybrid control base is not opaque")
    # Six rank-one terms each contribute +120; every exact source is -1.
    # A five-card prefix can nevertheless combine all remaining positive
    # possibilities, so its conservative upper stays positive.
    shifted = replace(
        producer,
        source_values=tuple((mask, -721) for mask, _ in producer.source_values),
        structural_epoch=base.BaseStructuralEpoch(_digest(f"hybrid-{cards}")),
    )
    h_scalars = tuple(
        (mask, -1 if mask.bit_count() == 1 else 0)
        for mask, _ in control.h_scalars
    )
    return replace(
        control,
        family="hybrid_switch_control",
        h_scalars=h_scalars,
        base_producer=shifted,
    )


class GlobalSeparationTopologyTests(unittest.TestCase):
    def test_config_identity_parent_chain_scope_and_result_absence(self) -> None:
        self.assertEqual(
            sha256(CONFIG.read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
            source.CONFIG_SHA256,
        )
        source.verify_preregistered_contract()
        self.assertEqual(
            source.PREREGISTRATION_COMMIT,
            "eca94fdba71b3c820b09255cd4aa4579d624972a",
        )
        self.assertFalse(RESULT.exists())
        self.assertEqual(source.DOMAINS, (10, 12))
        self.assertEqual(source.OUTPUT_SCALE, 24)
        self.assertEqual(source.PRICE_COEFFICIENTS, (30, -120, 360, -720, 720))
        self.assertEqual(source.H_SEED_WEIGHTS, (1, -24, 360, -2880, 8640))
        self.assertTrue(
            all(
                source.H_SEED_WEIGHTS[level]
                * factorial(source.SOURCE_WIDTH - level)
                == source.OUTPUT_SCALE * source.PRICE_COEFFICIENTS[level]
                for level in range(source.SUBSET_MAXIMUM + 1)
            )
        )

    def test_base_audit_is_typed_provenance_not_value_inference(self) -> None:
        absent = base.audit_base_producer(None)
        self.assertEqual(absent.classification, "producer_absent")
        self.assertEqual(
            absent.terminal, "base_producer_unavailable_no_bakeoff_selection"
        )
        expected = {
            "exact_lattice_base": "lattice_decomposable",
            "opaque_per_source_base": "genuinely_opaque",
            "lattice_plus_exact_sparse_master_support_correction": (
                "lattice_plus_sparse_correction"
            ),
        }
        for cards in source.DOMAINS:
            for family, classification in expected.items():
                producer = base.make_synthetic_base(cards, family)  # type: ignore[arg-type]
                audit = base.audit_base_producer(producer)
                self.assertEqual(audit.classification, classification)
                self.assertEqual(audit.refresh_cadence, "per_master_epoch")
                self.assertIsNone(audit.production_admission)
        with self.assertRaises(ValueError):
            base.ProducerIdentity(
                "src/pontius/production_base.py",
                _digest("production-source"),
                _digest("production-semantics"),
                "per_master_epoch",
                "production",
                None,
            )
        admission = base.ProductionBaseAdmission(-20, 12, 100, 1, 2)
        identity = base.ProducerIdentity(
            "src/pontius/production_base.py",
            _digest("production-source"),
            _digest("production-semantics"),
            "per_master_epoch",
            "production",
            admission,
        )
        self.assertIs(identity.admission, admission)
        with self.assertRaises(ValueError):
            base.OpaqueBaseProducer(
                identity,
                10,
                tuple((mask, 101) for mask in base.complete_masks(10, 6)),
                base.BaseStructuralEpoch(_digest("production-base-epoch")),
            )
        with self.assertRaises(ValueError):
            base.ProductionBaseAdmission(-20, 12, 100, 2, 3)

    def test_sparse_support_divisibility_and_semantic_epoch_mutations_reject(self) -> None:
        mixed = base.make_synthetic_base(
            10, "lattice_plus_exact_sparse_master_support_correction"
        )
        self.assertIsInstance(mixed, base.LatticeSparseBaseProducer)
        assert isinstance(mixed, base.LatticeSparseBaseProducer)
        outside = next(
            mask
            for mask in base.complete_masks(10, 6)
            if mask not in mixed.master_support
        )
        with self.assertRaises(ValueError):
            replace(mixed, corrections=mixed.corrections + ((outside, 1),))
        with self.assertRaises(ValueError):
            replace(mixed, master_support=mixed.master_support[:-1])
        component = mixed.component
        with self.assertRaises(ValueError):
            replace(component, output_scale=25)
        with self.assertRaises(TypeError):
            replace(
                mixed,
                correction_epoch=base.BaseStructuralEpoch(_digest("wrong-epoch-type")),
            )

    def test_prepared_h_and_base_artifacts_reject_only_the_stale_semantics(self) -> None:
        value = source.make_control_input(
            10, "lattice_plus_exact_sparse_master_support_correction"
        )
        prepared_h = source.prepare_h_artifact(value)
        prepared_base = source.prepare_base_artifact(value.base_producer)
        prepared_prefix = source.prepare_prefix_artifact(value)
        changed_h = replace(
            value,
            h_epoch=base.HSeedEpoch(_digest("changed-H-epoch")),
        )
        with self.assertRaises(ValueError):
            prepared_h.assert_fresh(changed_h)
        with self.assertRaises(ValueError):
            source.run_prefix(
                changed_h,
                "positive_witness",
                prepared=prepared_prefix,
            )
        prepared_base.assert_fresh(changed_h.base_producer)
        changed_rows = ((value.h_scalars[0][0], value.h_scalars[0][1] + 1),) + value.h_scalars[1:]
        with self.assertRaises(ValueError):
            prepared_h.assert_fresh(replace(value, h_scalars=changed_rows))

        producer = value.base_producer
        assert isinstance(producer, base.LatticeSparseBaseProducer)
        changed_component = replace(
            producer.component,
            structural_epoch=base.BaseStructuralEpoch(_digest("changed-base-epoch")),
        )
        changed_base = replace(producer, component=changed_component)
        prepared_h.assert_fresh(replace(value, base_producer=changed_base))
        prepared_base.assert_correction_fresh(changed_base)
        with self.assertRaises(ValueError):
            prepared_base.assert_structural_fresh(changed_base)

        changed_correction = replace(
            producer,
            correction_epoch=base.BaseCorrectionEpoch(_digest("changed-correction-epoch")),
        )
        prepared_base.assert_structural_fresh(changed_correction)
        with self.assertRaises(ValueError):
            prepared_base.assert_correction_fresh(changed_correction)
        with self.assertRaises(ValueError):
            source.evaluate_rank_truncated_zeta(
                replace(value, base_producer=changed_correction),
                prepared_h=prepared_h,
                prepared_base=prepared_base,
            )

    def test_zeta_every_rank_output_and_per_level_widths_match_exact_authority(self) -> None:
        families = source.LEGACY_FAMILIES + source.BASE_FAMILIES
        for cards in source.DOMAINS:
            expected_edges = sum(
                rank * comb(cards, rank) for rank in range(1, source.SOURCE_WIDTH + 1)
            )
            for family in families:
                value = source.make_control_input(cards, family)
                evaluated = source.evaluate_rank_truncated_zeta(
                    value,
                    prepared_h=source.prepare_h_artifact(value),
                    prepared_base=source.prepare_base_artifact(value.base_producer),
                )
                self.assertEqual(evaluated.prices, source.direct_price_map(value))
                self.assertEqual(evaluated.work.cover_edges, expected_edges)
                self.assertEqual(evaluated.work.rank_barriers, 6)
                self.assertEqual(evaluated.work.rank_six_output_reads, comb(cards, 6))
                self.assertEqual(
                    evaluated.work.output_required_signed_bits,
                    _required_width(evaluated.work.output_scaled_absolute_bound)[0],
                )
                for rank, receipt in enumerate(evaluated.work.rank_receipts):
                    self.assertEqual(receipt.rank, rank)
                    self.assertEqual(receipt.nodes, comb(cards, rank))
                    self.assertEqual(
                        receipt.cover_edges,
                        0 if rank == 0 else rank * comb(cards, rank),
                    )
                    self.assertLessEqual(
                        receipt.observed_maximum_absolute,
                        receipt.combined_absolute_bound,
                    )
                    self.assertEqual(
                        (
                            receipt.h_required_signed_bits,
                            receipt.h_mathematical_limbs,
                            receipt.h_guard_inclusive_limbs,
                        ),
                        _required_width(receipt.h_absolute_bound),
                    )
                    self.assertEqual(
                        (
                            receipt.base_required_signed_bits,
                            receipt.base_mathematical_limbs,
                            receipt.base_guard_inclusive_limbs,
                        ),
                        _required_width(receipt.base_absolute_bound),
                    )
                    self.assertEqual(
                        (
                            receipt.required_signed_bits,
                            receipt.mathematical_limbs,
                            receipt.guard_inclusive_limbs,
                        ),
                        _required_width(receipt.combined_absolute_bound),
                    )
                for _, scaled in evaluated.scaled_prices:
                    self.assertEqual(scaled % source.OUTPUT_SCALE, 0)

    def test_base_embedding_is_exact_before_h_is_added(self) -> None:
        for cards in source.DOMAINS:
            for family in source.BASE_FAMILIES:
                value = source.make_control_input(cards, family)
                zero_h = replace(
                    value,
                    h_scalars=tuple((mask, 0) for mask, _ in value.h_scalars),
                    h_epoch=base.HSeedEpoch(_digest(f"zero-H-{cards}-{family}")),
                )
                evaluated = source.evaluate_rank_truncated_zeta(zero_h)
                self.assertEqual(evaluated.prices, base.base_values(value.base_producer))
                if family == "opaque_per_source_base":
                    self.assertEqual(evaluated.work.base_seed_reads, 0)
                    self.assertEqual(evaluated.work.opaque_base_reads, comb(cards, 6))
                elif family == "exact_lattice_base":
                    self.assertGreater(evaluated.work.base_seed_reads, 0)
                    self.assertEqual(evaluated.work.sparse_patch_reads, 0)
                else:
                    self.assertEqual(evaluated.work.sparse_patch_reads, 3)

    def test_reverse_cover_graph_is_the_exact_direct_transpose(self) -> None:
        for cards in source.DOMAINS:
            sources = prefix.complete_masks(cards, 6)
            for salt in (7, 29):
                weights = tuple(
                    (mask, ((index * salt + 3) % 41) - 20)
                    for index, mask in enumerate(sources)
                )
                reverse = source.reverse_h_transpose_scaled(cards, weights)
                self.assertEqual(
                    reverse.scaled_h_transpose,
                    source.direct_h_transpose_scaled(cards, weights),
                )
                self.assertEqual(
                    reverse.cover_edges,
                    sum(rank * comb(cards, rank) for rank in range(1, 7)),
                )
                self.assertEqual(reverse.rank_barriers, 6)

    def test_all_four_arms_match_argmax_full_ties_and_positive_authority(self) -> None:
        for cards in source.DOMAINS:
            for family in source.LEGACY_FAMILIES + source.BASE_FAMILIES:
                value = source.make_control_input(cards, family)
                prices = source.direct_price_map(value)
                maximum = max(price for _, price in prices)
                ties = tuple(mask for mask, price in prices if price == maximum)
                positives = tuple(mask for mask, price in prices if price > 0)
                prepared_prefix = source.prepare_prefix_artifact(value)
                receipts = (
                    source.run_direct(value, "exact_argmax_full_ties"),
                    source.run_zeta(value, "exact_argmax_full_ties"),
                    source.run_prefix(
                        value, "exact_argmax_full_ties", prepared=prepared_prefix
                    ),
                    source.run_hybrid(
                        value, "exact_argmax_full_ties", prepared=prepared_prefix
                    ),
                )
                for arm, receipt in zip(source.ARM_NAMES, receipts, strict=True):
                    self.assertEqual(receipt.maximum_price, maximum, (cards, family, arm))
                    self.assertEqual(receipt.maximizers, ties, (cards, family, arm))
                    self.assertEqual(
                        receipt.positive_coordinates,
                        positives,
                        (cards, family, arm),
                    )
                    self.assertTrue(receipt.complete_domain_covered)
                    self.assertEqual(receipt.certified_source_count, comb(cards, 6))
                    self.assertEqual(
                        receipt.work.h_feature_contractions,
                        len(value.h_scalars) * source.FEATURE_WIDTH,
                    )

    def test_positive_witness_and_prove_none_modes_are_not_conflated(self) -> None:
        for cards in source.DOMAINS:
            positive = source.make_control_input(cards, "late_positive")
            positive_set = tuple(
                mask for mask, price in source.direct_price_map(positive) if price > 0
            )
            nonpositive = source.make_control_input(cards, "all_nonpositive")
            positive_prepared = source.prepare_prefix_artifact(positive)
            nonpositive_prepared = source.prepare_prefix_artifact(nonpositive)
            witness_receipts = (
                source.run_direct(positive, "positive_witness"),
                source.run_zeta(positive, "positive_witness"),
                source.run_prefix(
                    positive, "positive_witness", prepared=positive_prepared
                ),
                source.run_hybrid(
                    positive, "positive_witness", prepared=positive_prepared
                ),
            )
            closure_receipts = (
                source.run_direct(nonpositive, "prove_none"),
                source.run_zeta(nonpositive, "prove_none"),
                source.run_prefix(
                    nonpositive, "prove_none", prepared=nonpositive_prepared
                ),
                source.run_hybrid(
                    nonpositive, "prove_none", prepared=nonpositive_prepared
                ),
            )
            for arm, witness, closure in zip(
                source.ARM_NAMES, witness_receipts, closure_receipts, strict=True
            ):
                self.assertIn(witness.witness_coordinate, positive_set)
                self.assertGreater(witness.witness_price, 0)
                self.assertFalse(witness.closed_no_positive)
                self.assertIsNone(closure.witness_coordinate)
                self.assertTrue(closure.complete_domain_covered)
                self.assertTrue(closure.closed_no_positive)

    def test_hybrid_boundaries_and_integrated_switch_are_frozen_and_charged(self) -> None:
        population = 1_000
        def decision(leaves: int, covered: int) -> source.HybridSwitchDecision:
            return source.hybrid_switch_decision(
                population,
                leaves,
                covered,
                positive_witness=False,
                globally_closed=False,
            )

        before = decision(15, 15)
        exact_bad = decision(16, 499)
        after_bad = decision(17, 499)
        exact_good = decision(16, 500)
        hard_before = decision(124, 800)
        hard_exact = decision(125, 800)
        hard_after = decision(126, 800)
        self.assertFalse(before.switch)
        self.assertEqual(
            (exact_bad.switch, exact_bad.reason),
            (True, "early_insufficient_coverage"),
        )
        self.assertTrue(after_bad.switch)
        self.assertFalse(exact_good.switch)
        self.assertFalse(hard_before.switch)
        self.assertEqual(
            (hard_exact.switch, hard_exact.reason),
            (True, "hard_exact_leaf_checkpoint"),
        )
        self.assertTrue(hard_after.switch)
        self.assertFalse(
            source.hybrid_switch_decision(
                population, 125, 800, positive_witness=True, globally_closed=False
            ).switch
        )
        self.assertFalse(
            source.hybrid_switch_decision(
                population, 125, 1_000, positive_witness=False, globally_closed=True
            ).switch
        )
        for cards in source.DOMAINS:
            value = _hybrid_switch_input(cards)
            self.assertEqual({price for _, price in source.direct_price_map(value)}, {-1})
            receipt = source.run_hybrid(value, "prove_none")
            self.assertTrue(receipt.hybrid_switched)
            self.assertEqual(
                receipt.hybrid_switch_reason, "early_insufficient_coverage"
            )
            self.assertTrue(receipt.closed_no_positive)
            self.assertEqual(
                receipt.work.prefix_exact_leaves, (comb(cards, 6) + 63) // 64
            )
            self.assertEqual(
                receipt.work.zeta_cover_edges,
                sum(rank * comb(cards, rank) for rank in range(1, 7)),
            )
            self.assertGreater(receipt.work.direct_subset_reads, 0)

    def test_seed_rank_threshold_and_source_surface_mutations_fail_closed(self) -> None:
        original_weights = source.H_SEED_WEIGHTS
        with patch.object(source, "H_SEED_WEIGHTS", original_weights[:-1]):
            with self.assertRaises(ValueError):
                source.verify_preregistered_contract()
        poisoned = list(original_weights)
        poisoned[2] += 1
        with patch.object(source, "H_SEED_WEIGHTS", tuple(poisoned)):
            with self.assertRaises((ValueError, ArithmeticError)):
                source.verify_preregistered_contract()
            with self.assertRaises((ArithmeticError, IndexError)):
                source.evaluate_rank_truncated_zeta(
                    source.make_control_input(10, "deterministic_mixed_hash")
                )
        source_text = SOURCE.read_text(encoding="utf-8")
        base_text = BASE_SOURCE.read_text(encoding="utf-8")
        for text in (source_text, base_text):
            tree = ast.parse(text)
            direct_imports = {
                alias.name.split(".")[0]
                for node in ast.walk(tree)
                if isinstance(node, ast.Import)
                for alias in node.names
            }
            self.assertTrue({"numpy", "cupy", "torch", "time"}.isdisjoint(direct_imports))
        self.assertNotIn("feature_wise_dense_adjoint", source_text)
        original_read = Path.read_bytes

        def guarded(path: Path) -> bytes:
            if path.resolve() == RESULT.resolve():
                raise AssertionError("source-only seal touched the prospective result")
            return original_read(path)

        with patch.object(Path, "read_bytes", guarded):
            source.verify_preregistered_contract()
            source.evaluate_rank_truncated_zeta(
                source.make_control_input(10, "exact_lattice_base")
            )
        self.assertFalse(RESULT.exists())

    def test_claims_stop_at_source_only_and_literal_45_is_symbolic_work_only(self) -> None:
        claims = source.source_boundary_claims()
        self.assertTrue(claims["source_seal"])
        self.assertEqual(claims["base_producer_classification"], "producer_absent")
        for key in (
            "bakeoff_result",
            "topology_selected",
            "literal_45_fit",
            "resolver_iteration_result",
            "action_clock_result",
            "decision_quality_result",
            "blueprint_result",
            "poker_strength_result",
        ):
            self.assertIsNone(claims[key])
        self.assertFalse(claims["truncation_authorized"])
        self.assertEqual(comb(45, 6), 8_145_060)
        self.assertEqual(
            sum(rank * comb(45, rank) for rank in range(1, 7)), 55_619_730
        )
        self.assertEqual(comb(45, 6) * 57, 464_268_420)


if __name__ == "__main__":
    unittest.main()
