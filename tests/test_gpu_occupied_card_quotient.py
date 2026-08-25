from __future__ import annotations

from fractions import Fraction
import importlib.util
import inspect
from itertools import combinations
from math import comb
from pathlib import Path
import unittest

import numpy as np

import pontius.gpu_occupied_card_quotient as subject
from pontius.gpu_occupied_card_quotient import (
    MAXIMUM_ADJOINT_ROW_ABSOLUTE_ERROR,
    MAXIMUM_AFFINE_FOLD_ABSOLUTE_ERROR,
    MAXIMUM_DOT_PRODUCT_ABSOLUTE_ERROR,
    MAXIMUM_FORWARD_ROW_ABSOLUTE_ERROR,
    MAXIMUM_SCALE_NORMALIZED_RELATIVE_ERROR,
    MAXIMUM_SOURCE_COEFFICIENT_ABSOLUTE_ERROR,
    bounded_device_allocation,
    build_frozen_quotient_fixture,
    cardinality_offsets,
    cardinality_recurrence_work,
    colex_rank,
    colex_unrank,
    cupy_import_call_count,
    recurrence_allocation,
)


class GpuOccupiedCardQuotientSourceTests(unittest.TestCase):
    def test_full_width_recurrence_arithmetic_is_exact_and_allocation_only(self) -> None:
        work = cardinality_recurrence_work(45, 6, 176)
        self.assertEqual(work.vector_edges, 55_619_730)
        self.assertEqual(work.scalar_additions, 9_789_072_480)
        self.assertLess(work.scalar_additions, 81_711_241_920)

        allocation = recurrence_allocation(
            available_cards=45,
            source_cards=6,
            target_cards=4,
            feature_width=128,
            target_records=893_970,
            target_chunk_records=65_536,
            persistent_bytes=15_159_204,
        )
        self.assertEqual(allocation.level_rows, 9_531_040)
        self.assertEqual(allocation.level_table_bytes, 9_759_784_960)
        self.assertEqual(allocation.target_chunk_bytes, 67_108_864)
        self.assertEqual(allocation.requested_device_bytes, 9_842_053_028)
        self.assertTrue(allocation.fixed_cap_pass)
        self.assertTrue(allocation.physical_reserve_pass)
        self.assertIsNone(allocation.live_reserve_pass)
        self.assertEqual((2_971 + 127) // 128, 24)

    def test_bounded_guard_rejects_before_cupy_for_every_non_ten_card_request(self) -> None:
        before = cupy_import_call_count()
        with self.assertRaisesRegex(ValueError, "restricted to ten cards"):
            bounded_device_allocation(
                available_cards=45,
                source_cards=6,
                target_cards=4,
                feature_width=1,
                target_records=1,
                target_chunk_records=1,
            )
        self.assertEqual(cupy_import_call_count(), before)

        with self.assertRaisesRegex(ValueError, "exceeds 128"):
            bounded_device_allocation(
                available_cards=10,
                source_cards=6,
                target_cards=4,
                feature_width=129,
                target_records=1,
                target_chunk_records=1,
            )
        self.assertEqual(cupy_import_call_count(), before)

    def test_bounded_live_guard_fails_closed_without_import(self) -> None:
        before = cupy_import_call_count()
        with self.assertRaisesRegex(MemoryError, "before allocation"):
            bounded_device_allocation(
                available_cards=10,
                source_cards=6,
                target_cards=4,
                feature_width=52,
                target_records=1_260,
                target_chunk_records=1_260,
                live_free_bytes=2_000_000_000,
            )
        self.assertEqual(cupy_import_call_count(), before)

    def test_colex_rank_is_collision_free_on_every_bounded_level(self) -> None:
        for width in range(7):
            ranked = tuple(
                colex_rank(colex_unrank(rank, 10, width))
                for rank in range(comb(10, width))
            )
            self.assertEqual(ranked, tuple(range(comb(10, width))))
        self.assertEqual(cardinality_offsets(10, 6), (0, 1, 11, 56, 176, 386, 638))

    def test_cardinality_recurrence_matches_literal_disjointness_exactly(self) -> None:
        cards = 8
        source_cards = 4
        source = {
            selected: (
                Fraction((sum(selected) + 3) * (selected[-1] + 1), 17),
                Fraction((-1) ** sum(selected) * (selected[0] + 2), 19),
            )
            for selected in combinations(range(cards), source_cards)
        }
        levels: dict[int, dict[tuple[int, ...], tuple[Fraction, Fraction]]] = {
            source_cards: source
        }
        for level in range(source_cards - 1, -1, -1):
            current = {}
            for selected in combinations(range(cards), level):
                values = []
                selected_set = set(selected)
                for feature in range(2):
                    numerator = sum(
                        (
                            levels[level + 1][tuple(sorted((*selected, card)))][feature]
                            for card in range(cards)
                            if card not in selected_set
                        ),
                        Fraction(0),
                    )
                    values.append(numerator / (source_cards - level))
                current[selected] = tuple(values)
            levels[level] = current

        for query in combinations(range(cards), 2):
            recurrence = []
            for feature in range(2):
                value = Fraction(0)
                for width in range(3):
                    for subset in combinations(query, width):
                        value += (-1 if width % 2 else 1) * levels[width][subset][feature]
                recurrence.append(value)
            literal = tuple(
                sum(
                    (
                        row[feature]
                        for selected, row in source.items()
                        if not set(selected) & set(query)
                    ),
                    Fraction(0),
                )
                for feature in range(2)
            )
            self.assertEqual(tuple(recurrence), literal)

    def test_frozen_fixture_is_complete_readonly_and_direct_automaton_shaped(self) -> None:
        fixture = build_frozen_quotient_fixture()
        self.assertEqual(fixture.available_cards, 10)
        self.assertEqual(len(fixture.hands), 45)
        self.assertEqual(fixture.source_pair_positions.shape, (90, 6))
        self.assertEqual(fixture.query_masks.shape, (1_260,))
        self.assertEqual(len(set(int(mask) for mask in fixture.query_masks)), 210)
        self.assertEqual(fixture.automaton.state_ranks, (1, 9, 17, 25, 16, 21, 1))
        self.assertEqual(fixture.source_rank, 25)
        self.assertEqual(fixture.feature_width, 52)
        for values in (
            fixture.unary_weights,
            fixture.mode_factors,
            fixture.mixture_weights,
            fixture.pair_to_hand,
            fixture.source_pair_positions,
            fixture.query_masks,
            fixture.query_hand_indices,
            fixture.unary_offsets,
        ):
            self.assertFalse(values.flags.writeable)

    def test_device_source_has_no_float_atomic_or_explicit_incidence_table(self) -> None:
        source = Path(inspect.getsourcefile(subject) or "").read_text(encoding="utf-8")
        self.assertNotIn("atomicAdd", subject._CUDA_SOURCE)
        self.assertNotIn("__managed__", subject._CUDA_SOURCE)
        self.assertNotIn("source_masks", inspect.getsource(subject._run_structured_gpu))
        self.assertNotIn("incidence", inspect.getsource(subject._run_structured_gpu))
        self.assertIn("source_coefficients", source)
        self.assertEqual(
            tuple(
                inspect.signature(
                    subject.run_frozen_gpu_quotient_keystone
                ).parameters
            ),
            (),
        )

    def test_numerical_tolerances_are_independent_literal_fields(self) -> None:
        self.assertEqual(MAXIMUM_SOURCE_COEFFICIENT_ABSOLUTE_ERROR, 2e-12)
        self.assertEqual(MAXIMUM_FORWARD_ROW_ABSOLUTE_ERROR, 2e-10)
        self.assertEqual(MAXIMUM_ADJOINT_ROW_ABSOLUTE_ERROR, 2e-10)
        self.assertEqual(MAXIMUM_AFFINE_FOLD_ABSOLUTE_ERROR, 2e-10)
        self.assertEqual(MAXIMUM_DOT_PRODUCT_ABSOLUTE_ERROR, 2e-10)
        self.assertEqual(MAXIMUM_SCALE_NORMALIZED_RELATIVE_ERROR, 2e-11)
        names = {
            "MAXIMUM_SOURCE_COEFFICIENT_ABSOLUTE_ERROR",
            "MAXIMUM_FORWARD_ROW_ABSOLUTE_ERROR",
            "MAXIMUM_ADJOINT_ROW_ABSOLUTE_ERROR",
            "MAXIMUM_AFFINE_FOLD_ABSOLUTE_ERROR",
            "MAXIMUM_DOT_PRODUCT_ABSOLUTE_ERROR",
            "MAXIMUM_SCALE_NORMALIZED_RELATIVE_ERROR",
        }
        module_source = Path(inspect.getsourcefile(subject) or "").read_text(encoding="utf-8")
        for name in names:
            self.assertIn(name, module_source)


@unittest.skipUnless(importlib.util.find_spec("cupy"), "CuPy is unavailable")
class GpuOccupiedCardQuotientDeviceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = subject.run_frozen_gpu_quotient_keystone()

    def test_every_natural_and_adversarial_gate_passes(self) -> None:
        self.assertTrue(
            self.report.all_gates_pass,
            [key for key, value in self.report.gates.items() if not value],
        )
        self.assertEqual(len(self.report.gates), 22)
        for gate in (
            "wrong_divisor_detected",
            "wrong_sign_detected",
            "adjoint_seam_detected",
            "dropped_source_factor_detected",
            "duplicate_sunk_detected",
        ):
            self.assertTrue(self.report.gates[gate])

    def test_complete_geometry_and_exact_work_counters_are_separate(self) -> None:
        self.assertEqual(self.report.available_cards, 10)
        self.assertEqual(self.report.source_occupancies, 210)
        self.assertEqual(self.report.labeled_source_pairings, 18_900)
        self.assertEqual(self.report.query_occupancies, 210)
        self.assertEqual(self.report.labeled_query_records, 1_260)
        self.assertEqual(self.report.source_rank, 25)
        self.assertEqual(self.report.feature_width, 52)
        self.assertEqual(
            dict(self.report.work),
            {
                "source_pairing_visits": 18_900,
                "source_state_reach_accumulations": 75_600,
                "source_coefficient_zero_writes": 10_920,
                "forward_recurrence_vector_edges": 3_820,
                "forward_recurrence_scalar_additions": 198_640,
                "signed_query_terms": 20_160,
                "signed_query_scalar_additions": 1_048_320,
                "query_automaton_state_folds": 63_000,
                "source_refresh_pairing_visits": 18_900,
                "source_refresh_recurrence_scalar_additions": 198_640,
                "query_only_source_pairing_visits": 0,
                "query_only_recurrence_scalar_additions": 0,
                "adjoint_query_aggregation_additions": 3_150,
                "adjoint_recurrence_scalar_additions": 3_900,
                "adjoint_signed_source_additions": 35_910,
                "adjoint_label_writes": 56_700,
            },
        )

    def test_all_numerical_errors_are_inside_their_frozen_envelopes(self) -> None:
        errors = self.report.maximum_errors
        self.assertLessEqual(errors["source_coefficient_absolute"], 2e-12)
        self.assertLessEqual(errors["forward_row_absolute"], 2e-10)
        self.assertLessEqual(errors["adjoint_row_absolute"], 2e-10)
        self.assertLessEqual(errors["affine_fold_absolute"], 2e-10)
        self.assertLessEqual(errors["dot_product_absolute"], 2e-10)
        self.assertLessEqual(errors["current_stack_normalized_value_absolute"], 2e-10)
        self.assertLessEqual(errors["source_refresh_absolute"], 2e-10)
        self.assertLessEqual(errors["source_permutation_absolute"], 2e-10)
        self.assertLessEqual(errors["scale_normalized_relative"], 2e-11)

    def test_warm_outputs_are_stable_and_have_frozen_digests(self) -> None:
        self.assertTrue(self.report.gates["warm_byte_identity"])
        self.assertEqual(
            dict(self.report.digests),
            {
                "source_coefficients": (
                    "737d4509187ed2be5fcc2338f9ba58ea"
                    "3925192e5127da2a6c2f434245bcd22b"
                ),
                "compatible": (
                    "fe2889f7cfeb08cf6feb3ab57093a213"
                    "3701686fe0d85823383e30838fc29ae7"
                ),
                "affine_outputs": (
                    "ee56cb418d92f1e6e49dc2252dbf88ce"
                    "0fbd646c2902d14a476f8d2aef1f32b3"
                ),
                "adjoint": (
                    "326584ccb09c76c61508de45bed60ef8"
                    "00857ec0e15f315829ec729a600a18c7"
                ),
            },
        )

    def test_live_allocation_and_phase_walls_are_bounded_units_only(self) -> None:
        allocation = self.report.allocation
        self.assertEqual(allocation.requested_device_bytes, 893_392)
        self.assertTrue(allocation.fixed_cap_pass)
        self.assertTrue(allocation.physical_reserve_pass)
        self.assertTrue(allocation.live_reserve_pass)
        self.assertGreater(
            allocation.live_free_bytes or 0,
            allocation.requested_device_bytes + 2_000_000_000,
        )
        self.assertGreater(self.report.timings_ms["source_coefficients"], 0.0)
        self.assertGreater(self.report.timings_ms["forward_recurrence"], 0.0)
        self.assertGreater(self.report.timings_ms["signed_query"], 0.0)
        self.assertGreater(self.report.timings_ms["affine_fold"], 0.0)
        self.assertGreater(self.report.timings_ms["warm_device_phases"], 0.0)
        self.assertGreater(
            self.report.timings_ms["source_refresh_device_phases"],
            0.0,
        )
        self.assertLessEqual(self.report.timings_ms["host_end_to_end"], 30_000.0)
        self.assertEqual(self.report.timings_ms["query_only_source_coefficients"], 0.0)
        self.assertEqual(self.report.timings_ms["query_only_forward_recurrence"], 0.0)
        self.assertTrue(str(self.report.device["name"]))
        self.assertTrue(str(self.report.device["compute_capability"]))
        self.assertGreater(int(self.report.device["cuda_runtime_version"]), 0)
        self.assertGreater(int(self.report.device["cuda_driver_version"]), 0)


if __name__ == "__main__":
    unittest.main()
