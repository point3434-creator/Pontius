from __future__ import annotations

import ast
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
from itertools import combinations
import math
from pathlib import Path
import random
import subprocess
import sys
import unittest

import pontius.legal_river_quotient_cuda_compensated_tiles as paired
import pontius.legal_river_quotient_exact_integer_operator as exact


_ROOT = Path(__file__).parents[1]
_SOURCE = _ROOT / "src/pontius/legal_river_quotient_exact_integer_operator.py"
_CONFIG = (
    _ROOT
    / "experiments/configs/"
    "legal-river-quotient-exact-integer-operator-keystone-v1.json"
)
_CORRECTION = (
    _ROOT
    / "experiments/configs/"
    "legal-river-quotient-exact-integer-operator-keystone-v2-provenance.json"
)


def _independent_canonical_lf_sha256(path: Path) -> str:
    raw = path.read_bytes()
    normalized = bytearray()
    index = 0
    while index < len(raw):
        if raw[index] == 13 and index + 1 < len(raw) and raw[index + 1] == 10:
            normalized.append(10)
            index += 2
        else:
            normalized.append(raw[index])
            index += 1
    return sha256(bytes(normalized)).hexdigest()


def _captured(value: paired.FloatPair) -> exact.CapturedPair:
    return exact.CapturedPair(float(value.high), float(value.low))


def _mask(cards: tuple[int, ...]) -> int:
    return sum(1 << card for card in cards)


def _pair_exact(value: exact.CapturedPair) -> Fraction:
    return Fraction.from_float(value.high) + Fraction.from_float(value.low)


def _scaled_fraction(value: int, exponent: int) -> Fraction:
    if exponent >= 0:
        return Fraction(value << exponent, 1)
    return Fraction(value, 1 << -exponent)


def _make_signed_population() -> exact.CapturedOperatorInput:
    cards = 12
    source_masks = exact.complete_masks(cards, 6)
    query_occupancies = exact.complete_masks(cards, 4)
    source_rows: list[tuple[exact.CapturedPair, ...]] = []
    for rank, _ in enumerate(source_masks):
        row = []
        for feature in range(5):
            if feature == 4:
                high = math.ldexp(float(8 + rank % 5), -3)
                low = math.ldexp(1.0, -96 - rank % 3)
            elif (rank + 3 * feature) % 17 == 0:
                high = -0.0 if rank & 1 else 0.0
                low = 0.0
            else:
                sign = -1.0 if (rank + feature) & 1 else 1.0
                high_exponent = -18 if (rank + feature) % 3 else 21
                high = sign * math.ldexp(float(8 + (rank + feature) % 7), high_exponent - 3)
                low = -sign * math.ldexp(1.0, -104 + (rank + feature) % 5)
            row.append(exact.CapturedPair(high, low))
        source_rows.append(tuple(row))

    query_masks: list[int] = []
    query_labels: list[int] = []
    covectors: list[tuple[exact.CapturedPair, ...]] = []
    weights: list[exact.CapturedPair] = []
    for occupancy_rank, query_mask in enumerate(query_occupancies):
        for label in range(6):
            query_masks.append(query_mask)
            query_labels.append(label)
            weight_high = math.ldexp(float(9 + (occupancy_rank + label) % 6), -4)
            weight_low = math.ldexp(1.0, -101 - label % 3)
            weights.append(exact.CapturedPair(weight_high, weight_low))
            row = []
            for feature in range(5):
                if (occupancy_rank + label + feature) % 19 == 0:
                    row.append(exact.CapturedPair(0.0, -0.0))
                    continue
                sign = -1.0 if (occupancy_rank + 2 * label + feature) & 1 else 1.0
                exponent = -14 if (occupancy_rank + feature) % 4 else 17
                high = sign * math.ldexp(
                    float(8 + (occupancy_rank + label + feature) % 5),
                    exponent - 3,
                )
                low = -sign * math.ldexp(
                    1.0,
                    -109 + (occupancy_rank + label + feature) % 7,
                )
                row.append(exact.CapturedPair(high, low))
            covectors.append(tuple(row))

    window = exact.FrozenExponentWindow(-120, 30)
    return exact.CapturedOperatorInput(
        available_cards=cards,
        source_masks=source_masks,
        source_rows=tuple(source_rows),
        query_masks=tuple(query_masks),
        query_labels=tuple(query_labels),
        query_covectors=tuple(covectors),
        query_weights=tuple(weights),
        reach_feature=4,
        source_window=window,
        covector_window=window,
        weight_window=window,
    )


def _make_natural_complete_ten() -> exact.CapturedOperatorInput:
    fixture = paired.compile_consumer_population_fixture(10)
    unary = fixture.unary_weights.reshape(-1)
    factors = fixture.mode_factors.reshape(-1)
    source_masks: list[int] = []
    source_rows: list[tuple[exact.CapturedPair, ...]] = []
    t0, t1, t2 = fixture.transitions[:3]
    for rank in range(fixture.geometry.source_occupancies):
        cards = paired.colex_unrank(rank, 10, 6)
        source_masks.append(_mask(cards))
        row = [paired.FloatPair(0.0, 0.0) for _ in range(176)]
        for positions in fixture.source_pair_positions:
            hands = tuple(
                int(
                    fixture.pair_to_hand[
                        cards[int(positions[2 * seat])],
                        cards[int(positions[2 * seat + 1])],
                    ]
                )
                for seat in range(3)
            )
            state0 = int(t0[0, hands[0]])
            state1 = int(t1[state0, hands[1]])
            state2 = int(t2[state1, hands[2]])
            indices = tuple(
                int(fixture.unary_offsets[seat]) + hands[seat]
                for seat in range(3)
            )
            weight = paired._pair_weight_host(1.0, unary, factors, indices)
            row[state2] = paired._pair_add_host(row[state2], weight)
            row[paired.REACH_GLOBAL_FEATURE] = paired._pair_add_host(
                row[paired.REACH_GLOBAL_FEATURE], weight
            )
        source_rows.append(tuple(_captured(value) for value in row))

    query_masks: list[int] = []
    query_labels: list[int] = []
    covectors: list[tuple[exact.CapturedPair, ...]] = []
    weights: list[exact.CapturedPair] = []
    t3, t4 = fixture.transitions[3:5]
    for record in range(fixture.geometry.labeled_query_records):
        query_masks.append(int(fixture.query_masks[record]))
        query_labels.append(record % 6)
        h4 = int(fixture.query_hand_indices[record, 0])
        h5 = int(fixture.query_hand_indices[record, 1])
        indices = (
            int(fixture.unary_offsets[3]),
            int(fixture.unary_offsets[4]) + h4,
            int(fixture.unary_offsets[5]) + h5,
        )
        weight = paired._pair_weight_host(
            float(fixture.mixture_weights[0]), unary, factors, indices
        )
        weights.append(_captured(weight))
        row = []
        for feature in range(176):
            if feature == paired.REACH_GLOBAL_FEATURE:
                payoff = fixture.sunk_value
            else:
                state3 = int(t3[feature, 0])
                state4 = int(t4[state3, h4])
                payoff = float(fixture.terminal_winner_values[state4, h5])
            row.append(_captured(paired._pair_times_float64_host(weight, payoff)))
        covectors.append(tuple(row))
    return exact.CapturedOperatorInput(
        available_cards=10,
        source_masks=tuple(source_masks),
        source_rows=tuple(source_rows),
        query_masks=tuple(query_masks),
        query_labels=tuple(query_labels),
        query_covectors=tuple(covectors),
        query_weights=tuple(weights),
        reach_feature=paired.REACH_GLOBAL_FEATURE,
    )


def _apply_level_deltas(
    levels: exact.IntegerLevels,
    changes: tuple[tuple[int, int, tuple[int, ...]], ...],
) -> tuple[dict[int, tuple[int, ...]], ...]:
    mutable = [levels.level(level) for level in range(levels.maximum_level + 1)]
    for level, mask, delta in changes:
        before = mutable[level][mask]
        mutable[level][mask] = tuple(
            left + right for left, right in zip(before, delta, strict=True)
        )
    return tuple(mutable)


class ExactIntegerOperatorSourceTests(unittest.TestCase):
    def test_import_is_standard_library_device_and_result_free(self) -> None:
        code = (
            "import importlib.util, pathlib, sys; "
            f"p=pathlib.Path({str(_SOURCE)!r}); "
            "s=importlib.util.spec_from_file_location('pontius_exact_integer_isolated',p); "
            "m=importlib.util.module_from_spec(s); sys.modules[s.name]=m; "
            "s.loader.exec_module(m); "
            "m.verify_preregistered_contract(); "
            "print(int('numpy' in sys.modules), int('cupy' in sys.modules), "
            "m.PREREGISTERED_CONFIG_SHA256)"
        )
        completed = subprocess.run(
            [sys.executable, "-B", "-c", code],
            cwd=_ROOT,
            check=True,
            capture_output=True,
            text=True,
            timeout=30.0,
        )
        self.assertEqual(
            completed.stdout.strip(),
            f"0 0 {exact.PREREGISTERED_CONFIG_SHA256}",
        )
        tree = ast.parse(_SOURCE.read_text(encoding="utf-8"))
        imported_roots = {
            alias.name.split(".")[0]
            for node in tree.body
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names
        }
        self.assertTrue(
            imported_roots.isdisjoint({"numpy", "cupy", "numba", "torch"})
        )
        source = _SOURCE.read_text(encoding="utf-8").lower()
        for forbidden in ("run_actual", "population_25(", "rawmodule", "cuda."):
            self.assertNotIn(forbidden, source)

    def test_config_hash_parents_formulas_and_open_claims_rebind(self) -> None:
        self.assertEqual(
            sha256(_CONFIG.read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
            exact.PREREGISTERED_CONFIG_SHA256,
        )
        self.assertEqual(
            sha256(_CORRECTION.read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
            exact.CORRECTION_CONFIG_SHA256,
        )
        configs = exact.load_preregistered_configs()
        self.assertIsNone(exact.verify_preregistered_contract(configs))
        changed = deepcopy(configs)
        changed[0]["division_free_operator"]["adjoint_level_weights_k_0_through_4"] = [
            1,
            6,
            30,
            120,
            360,
        ]
        with self.assertRaisesRegex(ValueError, "factorial scale"):
            exact.verify_preregistered_contract(changed)
        changed = deepcopy(configs)
        changed[1]["claims"]["device_fit"] = True
        with self.assertRaisesRegex(ValueError, "correction claims are open"):
            exact.verify_preregistered_contract(changed)

    def test_corrected_hashes_match_independent_bytes_and_bad_transform_rejects(self) -> None:
        base, correction = exact.load_preregistered_configs()
        paths = {
            "adr0368": "docs/decisions/ADR-0368-seal-the-exact-occupied-card-quotient-keystone.md",
            "adr0393": "docs/decisions/ADR-0393-retain-the-paired-tile-wall-rejection.md",
            "adr0432": "docs/decisions/ADR-0432-retain-the-shared-direct-artifact-capacity-rejection.md",
            "occupied_card_quotient": "src/pontius/occupied_card_quotient.py",
            "gpu_occupied_card_quotient": "src/pontius/gpu_occupied_card_quotient.py",
            "legal_river_quotient_bridge": "src/pontius/legal_river_quotient_bridge.py",
            "legal_river_quotient_bridge_config": "experiments/configs/legal-river-quotient-bridge-v1.json",
            "legal_river_quotient_cuda_consumer": "src/pontius/legal_river_quotient_cuda_consumer.py",
            "legal_river_quotient_cuda_compensated_tiles": "src/pontius/legal_river_quotient_cuda_compensated_tiles.py",
            "legal_river_quotient_cuda_compensated_tiles_v2_config": "experiments/configs/legal-river-quotient-cuda-compensated-tiles-v2.json",
        }
        corrected = correction["corrected_expected_sources"]
        for label, relative in paths.items():
            path = _ROOT / relative
            with self.subTest(label=label):
                self.assertEqual(
                    exact.canonical_lf_sha256(path),
                    _independent_canonical_lf_sha256(path),
                )
                self.assertEqual(corrected[label], exact.canonical_lf_sha256(path))

        for label, row in correction["defect"]["affected_sources"].items():
            raw = (_ROOT / row["relative_path"]).read_bytes()
            bad = sha256(
                raw.replace(bytes((92, 114, 92, 110)), bytes((92, 110)))
            ).hexdigest()
            self.assertEqual(bad, row["v1_false_sha256"])
            self.assertEqual(bad, base["expected_sources"][label])
            self.assertNotEqual(bad, corrected[label])

    def test_pair_encoding_is_exact_global_and_window_admitted(self) -> None:
        pairs = (
            (exact.CapturedPair(6.0, -math.ldexp(1.0, -10)),),
            (exact.CapturedPair(math.ldexp(1.0, -10), math.ldexp(3.0, 8)),),
            (exact.CapturedPair(-0.0, 0.0),),
        )
        encoded = exact.encode_pair_matrix(
            pairs,
            admitted_window=exact.FrozenExponentWindow(-10, 8),
        )
        self.assertEqual(encoded.family_exponent, -10)
        for captured_row, integer_row in zip(pairs, encoded.rows, strict=True):
            self.assertEqual(
                _scaled_fraction(integer_row[0], encoded.family_exponent),
                _pair_exact(captured_row[0]),
            )
        zeros = exact.encode_pair_matrix(((exact.CapturedPair(-0.0, 0.0),),))
        self.assertEqual((zeros.family_exponent, zeros.rows), (0, ((0,),)))
        self.assertEqual(exact.canonical_float_component(6.0), (3, 1))
        self.assertIsNone(exact.canonical_float_component(-0.0))
        with self.assertRaisesRegex(OverflowError, "outside"):
            exact.encode_pair_matrix(
                ((exact.CapturedPair(math.ldexp(1.0, -11), 0.0),),),
                admitted_window=exact.FrozenExponentWindow(-10, 8),
            )
        with self.assertRaisesRegex(OverflowError, "outside"):
            exact.encode_pair_matrix(
                ((exact.CapturedPair(math.ldexp(1.0, 9), 0.0),),),
                admitted_window=exact.FrozenExponentWindow(-10, 8),
            )
        with self.assertRaises(ValueError):
            exact.CapturedPair(float("inf"), 0.0)

    def test_factorial_weights_are_distinct_and_mutations_reject(self) -> None:
        self.assertIsNone(exact.validate_factorial_weights())
        self.assertNotEqual(exact.FORWARD_LEVEL_WEIGHTS, exact.ADJOINT_LEVEL_WEIGHTS)
        with self.assertRaisesRegex(ValueError, "weights differ"):
            exact.validate_factorial_weights(adjoint=exact.FORWARD_LEVEL_WEIGHTS)
        with self.assertRaisesRegex(ValueError, "common scale"):
            exact.validate_factorial_weights(common_scale=360)

    def test_forward_and_adjoint_recurrences_equal_literal_factorial_marginals(self) -> None:
        source_map = {
            mask: (rank - 17, 3 * rank + 2)
            for rank, mask in enumerate(exact.complete_masks(10, 6))
        }
        forward = exact.build_forward_levels(10, source_map)
        for level in range(7):
            multiplier = math.factorial(6 - level)
            for mask, observed in forward.rows[level]:
                expected = tuple(
                    multiplier
                    * sum(
                        row[feature]
                        for source_mask, row in source_map.items()
                        if source_mask & mask == mask
                    )
                    for feature in range(2)
                )
                self.assertEqual(observed, expected)

        query_map = {
            mask: (2 * rank - 31, -rank - 5)
            for rank, mask in enumerate(exact.complete_masks(10, 4))
        }
        adjoint = exact.build_adjoint_levels(10, query_map)
        for level in range(5):
            multiplier = math.factorial(4 - level)
            for mask, observed in adjoint.rows[level]:
                expected = tuple(
                    multiplier
                    * sum(
                        row[feature]
                        for query_mask, row in query_map.items()
                        if query_mask & mask == mask
                    )
                    for feature in range(2)
                )
                self.assertEqual(observed, expected)

    def test_binary64_rounding_covers_ties_seams_sign_and_overflow(self) -> None:
        cases = (
            (2**53 + 1, 2**53, 0, 0x3FF0000000000000),
            (2**53 + 3, 2**53, 0, 0x3FF0000000000002),
            (2**54 - 1, 2**53, 0, 0x4000000000000000),
            (1, 1, -1075, 0x0000000000000000),
            (3, 1, -1076, 0x0000000000000001),
            (2**53 - 1, 1, -1075, 0x0010000000000000),
            (-1, 1, -1075, 0x8000000000000000),
            (0, 1, 10000, 0x0000000000000000),
        )
        for numerator, denominator, shift, expected_bits in cases:
            with self.subTest(
                numerator=numerator, denominator=denominator, shift=shift
            ):
                self.assertEqual(
                    exact.binary64_bits(
                        exact.correctly_rounded_binary64(
                            numerator, denominator, shift
                        )
                    ),
                    expected_bits,
                )
        with self.assertRaisesRegex(OverflowError, "finite binary64"):
            exact.correctly_rounded_binary64(1, 1, 1024)

        generator = random.Random(433)
        for _ in range(500):
            numerator = generator.randrange(-(1 << 80), 1 << 80) or 1
            denominator = generator.randrange(1, 1 << 40)
            shift = generator.randrange(-1120, 1001)
            authority = Fraction(numerator, denominator)
            authority = authority * (1 << shift) if shift >= 0 else authority / (
                1 << -shift
            )
            try:
                expected = float(authority)
            except OverflowError:
                with self.assertRaises(OverflowError):
                    exact.correctly_rounded_binary64(numerator, denominator, shift)
            else:
                actual = exact.correctly_rounded_binary64(
                    numerator, denominator, shift
                )
                self.assertEqual(exact.binary64_bits(actual), exact.binary64_bits(expected))

    def test_bound_plans_keep_table_and_accumulator_windows_separate(self) -> None:
        captured_bound = (1 << 210) - 1
        report = exact.operator_bound_report(
            available_cards=45,
            feature_width=176,
            source_maximum=captured_bound,
            covector_maximum=captured_bound,
            weight_maximum=captured_bound,
        )
        self.assertEqual(report.forward_table_plan.required_signed_bits, 245)
        self.assertEqual(report.adjoint_table_plan.required_signed_bits, 241)
        self.assertEqual(report.numerator_plan.required_signed_bits, 480)
        self.assertEqual(report.reach_plan.required_signed_bits, 473)
        self.assertEqual(report.forward_table_plan.guard_inclusive_limbs, 5)
        self.assertEqual(report.adjoint_table_plan.guard_inclusive_limbs, 5)
        self.assertEqual(report.numerator_plan.guard_inclusive_limbs, 9)
        self.assertEqual(report.reach_plan.guard_inclusive_limbs, 9)
        self.assertEqual(report.forward_scalar_bound, report.adjoint_scalar_bound)
        with self.assertRaisesRegex(OverflowError, "guard limb"):
            exact.require_guard_inclusive_limbs(
                report.numerator_plan,
                report.numerator_plan.guard_inclusive_limbs - 1,
            )

        carry = 1 << (64 * report.numerator_plan.mathematical_limbs)
        self.assertEqual(
            exact.emulate_signed_integer(
                carry, report.numerator_plan.guard_inclusive_limbs
            ),
            carry,
        )
        with self.assertRaises(OverflowError):
            exact.emulate_signed_integer(
                carry, report.numerator_plan.mathematical_limbs
            )
        cancellation = (1 << 400, -(1 << 400), -(1 << 300), 1 << 300, -17)
        self.assertEqual(sum(cancellation), sum(reversed(cancellation)))
        self.assertEqual(
            exact.emulate_signed_integer(
                sum(cancellation), report.numerator_plan.guard_inclusive_limbs
            ),
            -17,
        )

    def test_literal_45_work_memory_and_delta_arithmetic_are_exact(self) -> None:
        work = exact.literal_45_work_model()
        self.assertEqual(work.source_occupancies, 8_145_060)
        self.assertEqual(work.query_occupancies, 148_995)
        self.assertEqual(work.labeled_query_records, 893_970)
        self.assertEqual(work.forward_rows_levels_0_through_5, 1_385_980)
        self.assertEqual(work.adjoint_rows_levels_0_through_4, 164_221)
        self.assertEqual(work.forward_recurrence_vector_edges, 55_619_730)
        self.assertEqual(work.adjoint_recurrence_vector_edges, 640_575)
        self.assertEqual(work.forward_signed_subset_vector_terms_by_query_occupancy, 2_383_920)
        self.assertEqual(work.adjoint_signed_subset_vector_terms_by_source_occupancy, 464_268_420)
        self.assertEqual(work.query_label_vector_additions, 744_975)
        self.assertEqual(work.forward_aggregated_scalar_products, 26_223_120)
        self.assertEqual(work.adjoint_dense_scalar_products, 1_433_530_560)
        self.assertEqual(work.source_pairing_visits_per_full_capture, 733_055_400)

        memory = exact.literal_45_memory_model(
            logical_tile_width=64,
            forward_guard_inclusive_limbs=5,
            adjoint_guard_inclusive_limbs=5,
            query_occupancy_chunk=4096,
            source_occupancy_chunk=4096,
        )
        self.assertEqual(memory.repacked_pair_level_6_bytes, 8_340_541_440)
        self.assertEqual(memory.forward_level_5_integer_bytes, 3_127_703_040)
        self.assertEqual(memory.forward_pair_plus_level_5_peak_floor_bytes, 11_468_244_480)
        self.assertEqual(memory.forward_levels_0_through_5_integer_bytes, 3_548_108_800)
        self.assertEqual(memory.adjoint_levels_0_through_4_integer_bytes, 420_405_760)

        source_map = {
            mask: (rank - 100, 2 * rank + 1)
            for rank, mask in enumerate(exact.complete_masks(10, 6))
        }
        old_forward = exact.build_forward_levels(10, source_map)
        dirty_source = next(iter(source_map))
        source_delta = (19, -23)
        changed_source = dict(source_map)
        changed_source[dirty_source] = tuple(
            value + delta
            for value, delta in zip(
                changed_source[dirty_source], source_delta, strict=True
            )
        )
        warm_forward = _apply_level_deltas(
            old_forward,
            exact.source_delta_contributions(
                dirty_source, source_delta, available_cards=10
            ),
        )
        cold_forward = exact.build_forward_levels(10, changed_source)
        self.assertEqual(
            warm_forward[:5],
            tuple(cold_forward.level(level) for level in range(5)),
        )

        query_map = {
            mask: (rank + 7, -3 * rank)
            for rank, mask in enumerate(exact.complete_masks(10, 4))
        }
        old_adjoint = exact.build_adjoint_levels(10, query_map)
        dirty_query = next(iter(query_map))
        query_delta = (-11, 29)
        changed_query = dict(query_map)
        changed_query[dirty_query] = tuple(
            value + delta
            for value, delta in zip(
                changed_query[dirty_query], query_delta, strict=True
            )
        )
        warm_adjoint = _apply_level_deltas(
            old_adjoint,
            exact.query_delta_contributions(
                dirty_query, query_delta, available_cards=10
            ),
        )
        cold_adjoint = exact.build_adjoint_levels(10, changed_query)
        self.assertEqual(
            warm_adjoint,
            tuple(cold_adjoint.level(level) for level in range(5)),
        )

    def test_delta_epoch_and_nonpositive_reach_fail_closed(self) -> None:
        digest = "1" * 64
        epoch = exact.DeltaEpoch(digest, "2" * 64, -100, 5)
        self.assertIsNone(exact.require_same_delta_epoch(epoch, epoch))
        with self.assertRaisesRegex(ValueError, "cold rebuild"):
            exact.require_same_delta_epoch(
                epoch, exact.DeltaEpoch(digest, "2" * 64, -101, 5)
            )

        source_masks = exact.complete_masks(10, 6)
        query_masks = exact.complete_masks(10, 4)
        zero_reach = exact.CapturedOperatorInput(
            available_cards=10,
            source_masks=source_masks,
            source_rows=tuple((exact.CapturedPair(0.0, 0.0),) for _ in source_masks),
            query_masks=tuple(mask for mask in query_masks for _ in range(6)),
            query_labels=tuple(label for _ in query_masks for label in range(6)),
            query_covectors=tuple(
                (exact.CapturedPair(1.0, 0.0),)
                for _ in range(len(query_masks) * 6)
            ),
            query_weights=tuple(
                exact.CapturedPair(1.0, 0.0)
                for _ in range(len(query_masks) * 6)
            ),
            reach_feature=0,
        )
        with self.assertRaisesRegex(ArithmeticError, "not positive"):
            exact.execute_exact_integer_operator(zero_reach)


class ExactIntegerOperatorSignedPopulationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.captured = _make_signed_population()
        cls.result = exact.execute_exact_integer_operator(cls.captured)

    def test_signed_population_exact_identities_divisibility_and_bounds(self) -> None:
        result = self.result
        self.assertEqual(len(result.source_rows), 924)
        self.assertEqual(len(result.aggregated_query_covectors), 495)
        self.assertEqual(
            result.forward_integer_numerator,
            result.adjoint_integer_numerator,
        )
        self.assertEqual(
            result.forward_integer_numerator,
            result.literal_scaled_integer_numerator,
        )
        self.assertEqual(
            result.forward_integer_reach,
            result.literal_scaled_integer_reach,
        )
        self.assertGreater(result.forward_integer_reach, 0)
        self.assertTrue(
            all(
                value % 720 == 0
                for _, row in result.forward_scaled_rows
                for value in row
            )
        )
        self.assertTrue(
            all(
                value % 720 == 0
                for _, row in result.adjoint_scaled_rows
                for value in row
            )
        )
        self.assertEqual(
            exact.binary64_bits(result.conditional_value),
            exact.binary64_bits(float(result.exact_conditional_value)),
        )
        self.assertLessEqual(
            result.observed.forward_signed_partial,
            result.bounds.forward_signed_partial_bound,
        )
        self.assertLessEqual(
            result.observed.adjoint_signed_partial,
            result.bounds.adjoint_signed_partial_bound,
        )
        self.assertLess(result.observed.numerator_partial, result.bounds.forward_scalar_bound)
        self.assertGreater(result.observed.numerator_partial, 0)
        self.assertGreater(result.observed.adjoint_partial, 0)

    def test_order_feature_and_label_permutations_are_integer_identical(self) -> None:
        captured = self.captured
        order = tuple(range(len(captured.query_masks) - 1, -1, -1))
        source_order = tuple(range(len(captured.source_masks) - 1, -1, -1))
        feature_order = (4, 3, 2, 1, 0)
        permuted = exact.CapturedOperatorInput(
            available_cards=captured.available_cards,
            source_masks=tuple(captured.source_masks[index] for index in source_order),
            source_rows=tuple(
                tuple(captured.source_rows[index][feature] for feature in feature_order)
                for index in source_order
            ),
            query_masks=tuple(captured.query_masks[index] for index in order),
            query_labels=tuple(captured.query_labels[index] for index in order),
            query_covectors=tuple(
                tuple(captured.query_covectors[index][feature] for feature in feature_order)
                for index in order
            ),
            query_weights=tuple(captured.query_weights[index] for index in order),
            reach_feature=0,
            source_window=captured.source_window,
            covector_window=captured.covector_window,
            weight_window=captured.weight_window,
        )
        replay = exact.execute_exact_integer_operator(permuted)
        self.assertEqual(
            replay.forward_integer_numerator, self.result.forward_integer_numerator
        )
        self.assertEqual(replay.forward_integer_reach, self.result.forward_integer_reach)
        self.assertEqual(replay.conditional_value_bits, self.result.conditional_value_bits)
        self.assertEqual(replay.exact_conditional_value, self.result.exact_conditional_value)

    def test_missing_label_reversed_sign_and_dropped_low_mutations_are_caught(self) -> None:
        captured = self.captured
        missing = exact.CapturedOperatorInput(
            available_cards=captured.available_cards,
            source_masks=captured.source_masks,
            source_rows=captured.source_rows,
            query_masks=captured.query_masks[:-1],
            query_labels=captured.query_labels[:-1],
            query_covectors=captured.query_covectors[:-1],
            query_weights=captured.query_weights[:-1],
            reach_feature=captured.reach_feature,
        )
        with self.assertRaisesRegex(ValueError, "zero through five exactly once"):
            exact.execute_exact_integer_operator(missing)

        duplicate_labels = list(captured.query_labels)
        duplicate_labels[5] = 0
        duplicated = exact.CapturedOperatorInput(
            available_cards=captured.available_cards,
            source_masks=captured.source_masks,
            source_rows=captured.source_rows,
            query_masks=captured.query_masks,
            query_labels=tuple(duplicate_labels),
            query_covectors=captured.query_covectors,
            query_weights=captured.query_weights,
            reach_feature=captured.reach_feature,
        )
        with self.assertRaisesRegex(ValueError, "unique integers"):
            exact.execute_exact_integer_operator(duplicated)

        encoded = exact.encode_pair_matrix(captured.source_rows)
        dropped = exact.encode_pair_matrix(
            tuple(
                tuple(exact.CapturedPair(pair.high, 0.0) for pair in row)
                for row in captured.source_rows
            )
        )
        exact_values = tuple(
            tuple(_scaled_fraction(value, encoded.family_exponent) for value in row)
            for row in encoded.rows
        )
        dropped_values = tuple(
            tuple(_scaled_fraction(value, dropped.family_exponent) for value in row)
            for row in dropped.rows
        )
        self.assertNotEqual(exact_values, dropped_values)

        source_map = dict(self.result.source_rows)
        levels = exact.build_forward_levels(captured.available_cards, source_map)
        query_mask = self.result.forward_scaled_rows[0][0]
        level_maps = tuple(levels.level(level) for level in range(5))
        reversed_sign_row = [0] * 5
        for subset in (
            _mask(tuple(cards))
            for width in range(5)
            for cards in combinations(
                tuple(card for card in range(12) if query_mask & (1 << card)),
                width,
            )
        ):
            level = subset.bit_count()
            row = level_maps[level][subset]
            mutation_sign = 1 if level & 1 else -1
            for feature, value in enumerate(row):
                reversed_sign_row[feature] += (
                    mutation_sign * exact.FORWARD_LEVEL_WEIGHTS[level] * value
                )
        self.assertNotEqual(
            tuple(reversed_sign_row), self.result.forward_scaled_rows[0][1]
        )


class ExactIntegerOperatorNaturalPopulationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.captured = _make_natural_complete_ten()
        cls.result = exact.execute_exact_integer_operator(cls.captured)

    def test_complete_ten_current_pair_capture_matches_independent_fraction_authority(self) -> None:
        captured = self.captured
        result = self.result
        source = {
            mask: tuple(_pair_exact(value) for value in row)
            for mask, row in zip(
                captured.source_masks, captured.source_rows, strict=True
            )
        }
        numerator = Fraction(0)
        reach = Fraction(0)
        universe = (1 << 10) - 1
        for mask, covector, weight in zip(
            captured.query_masks,
            captured.query_covectors,
            captured.query_weights,
            strict=True,
        ):
            row = source[universe ^ mask]
            numerator += sum(
                (
                    row[feature] * _pair_exact(covector[feature])
                    for feature in range(176)
                ),
                Fraction(0),
            )
            reach += row[175] * _pair_exact(weight)
        authority = numerator / reach
        self.assertGreater(reach, 0)
        self.assertEqual(result.exact_conditional_value, authority)
        self.assertEqual(result.forward_integer_numerator, result.adjoint_integer_numerator)
        self.assertEqual(
            result.forward_integer_numerator, result.literal_scaled_integer_numerator
        )
        self.assertEqual(result.forward_integer_reach, result.literal_scaled_integer_reach)
        self.assertEqual(
            result.conditional_value_bits,
            exact.binary64_bits(float(authority)),
        )
        self.assertEqual(len(result.source_rows), 210)
        self.assertEqual(len(result.aggregated_query_covectors), 210)
        self.assertTrue(
            any(pair.low != 0.0 for row in captured.source_rows for pair in row)
        )
        self.assertTrue(
            any(pair.low != 0.0 for row in captured.query_covectors for pair in row)
        )
        self.assertTrue(any(pair.low != 0.0 for pair in captured.query_weights))


if __name__ == "__main__":
    unittest.main()
