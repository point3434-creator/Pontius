from __future__ import annotations

from dataclasses import fields, replace
from itertools import combinations
import math
from math import comb
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest

from pontius import legal_river_quotient_exact_integer_operator as exact
from pontius import legal_river_quotient_fixed_width_work_comparison as fixed
from tests.test_legal_river_quotient_exact_integer_operator import (
    _make_natural_complete_ten,
    _make_signed_population,
)


ROOT = Path(__file__).parents[1]
SOURCE = ROOT / "src/pontius/legal_river_quotient_fixed_width_work_comparison.py"
CONTROLS = Path(__file__)
LIVE_CRLF_FIXTURE = b"left\r\nright"


class FixedWidthProvenanceTests(unittest.TestCase):
    def test_import_is_isolated_standard_library_and_result_free(self) -> None:
        before = {path.relative_to(ROOT) for path in ROOT.rglob("*") if path.is_file()}
        command = (
            "import importlib.util,json,pathlib,sys; "
            f"p=pathlib.Path({str(SOURCE)!r}); "
            "s=importlib.util.spec_from_file_location('pontius_fixed_width_isolated',p); "
            "m=importlib.util.module_from_spec(s); sys.modules[s.name]=m; "
            "s.loader.exec_module(m); m.verify_preregistered_contract(); "
            "print(json.dumps({'forbidden': sorted(set(sys.modules) & "
            "{'numpy','cupy','torch','numba','cuda'}), 'module': m.__name__}))"
        )
        completed = subprocess.run(
            [sys.executable, "-B", "-c", command],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn('"forbidden": []', completed.stdout)
        after = {path.relative_to(ROOT) for path in ROOT.rglob("*") if path.is_file()}
        self.assertEqual(before, after)
        fixed.verify_source_surface()

    def test_corrected_contract_rebinds_and_both_real_targets_are_armed(self) -> None:
        fixed.verify_preregistered_contract()
        source = fixed.literal_escape_mutation_receipt(
            SOURCE, expected_occurrences=1, require_armed=True
        )
        controls = fixed.literal_escape_mutation_receipt(
            CONTROLS, expected_occurrences=1, require_armed=True
        )
        self.assertEqual(source.occurrence_count, 1)
        self.assertEqual(controls.occurrence_count, 1)
        self.assertNotEqual(source.canonical_lf_sha256, source.forbidden_mutation_sha256)
        self.assertNotEqual(
            controls.canonical_lf_sha256, controls.forbidden_mutation_sha256
        )

    def test_mutation_requires_an_armed_fixture_and_counts_one_and_two(self) -> None:
        self.assertEqual(LIVE_CRLF_FIXTURE.count(bytes((13, 10))), 1)
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            token = bytes((92, 114, 92, 110))
            zero = base / "zero.bin"
            one = base / "one.bin"
            two = base / "two.bin"
            zero.write_bytes(b"token free")
            one.write_bytes(token)
            two.write_bytes(token + b"/" + token)
            with self.assertRaisesRegex(ValueError, "unarmed_literal_escape_mutation"):
                fixed.literal_escape_mutation_receipt(
                    zero, expected_occurrences=0, require_armed=True
                )
            one_receipt = fixed.literal_escape_mutation_receipt(
                one, expected_occurrences=1, require_armed=True
            )
            two_receipt = fixed.literal_escape_mutation_receipt(
                two, expected_occurrences=2, require_armed=True
            )
            self.assertNotEqual(
                one_receipt.canonical_lf_sha256,
                one_receipt.forbidden_mutation_sha256,
            )
            self.assertNotEqual(
                two_receipt.canonical_lf_sha256,
                two_receipt.forbidden_mutation_sha256,
            )

    def test_two_correct_normalizers_agree_and_independent_mutations_reject(self) -> None:
        raw = b"a" + bytes((13, 10)) + b"b" + bytes((13, 10))
        expected = b"a" + bytes((10,)) + b"b" + bytes((10,))
        self.assertEqual(fixed.canonical_lf_bytes(raw), expected)
        self.assertEqual(fixed.independent_canonical_lf_bytes(raw), expected)
        source = SOURCE.read_text(encoding="utf-8")
        fixed.validate_independent_normalizer_structure(source)
        wrapped = source + "\ndef independent_canonical_lf_bytes(data):\n    return canonical_lf_bytes(data)\n"
        replaced = source + "\ndef independent_canonical_lf_bytes(data):\n    return data.replace(b'x', b'y')\n"
        for mutation in (wrapped, replaced):
            with self.subTest(mutation=mutation[-70:]):
                with self.assertRaises(ValueError):
                    fixed.validate_independent_normalizer_structure(mutation)

    def test_structural_poison_patterns_reject(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")
        fixed.validate_source_semantics(source)
        inverse = source + "\ndef poison(p):\n    return pow(720, -1, p)\n"
        truncated = source + "\ndef poison(a, b):\n    return (a * b) & WORD_MASK\n"
        device = source + "\nimport cupy\n"
        for mutation in (inverse, truncated, device):
            with self.subTest(mutation=mutation[-60:]):
                with self.assertRaises(ValueError):
                    fixed.validate_source_semantics(mutation)
        fixed.validate_no_scale_inverse_constants(fixed.load_preregistered_config())
        with self.assertRaisesRegex(ValueError, "semantic inverse"):
            fixed.validate_no_scale_inverse_constants({"modular_inverse_of_720": 17})


class PositionalPrimitiveTests(unittest.TestCase):
    def test_limb_operations_match_unbounded_random_authority(self) -> None:
        generator = random.Random(436)
        plan = fixed.SignedLimbPlan.from_bound((1 << 180) - 1)
        product_plan = fixed.SignedLimbPlan.from_bound((1 << 360) - 1)
        for _ in range(500):
            left = generator.randrange(-(1 << 170), 1 << 170)
            right = generator.randrange(-(1 << 170), 1 << 170)
            factor = generator.randrange(-360, 361)
            encoded_left = fixed.SignedLimbs.encode(left, plan)
            encoded_right = fixed.SignedLimbs.encode(right, plan)
            self.assertEqual(fixed.limb_add(encoded_left, encoded_right)[0].decode(), left + right)
            self.assertEqual(
                fixed.limb_subtract(encoded_left, encoded_right)[0].decode(),
                left - right,
            )
            self.assertEqual(fixed.limb_negate(encoded_left)[0].decode(), -left)
            self.assertEqual(
                fixed.limb_multiply_small(encoded_left, factor)[0].decode(),
                left * factor,
            )
            self.assertEqual(
                fixed.limb_full_product(
                    encoded_left, encoded_right, product_plan
                )[0].decode(),
                left * right,
            )

    def test_guard_short_width_carry_borrow_negative_and_cancellation_fail_closed(self) -> None:
        plan = fixed.SignedLimbPlan.from_bound((1 << 190) - 1)
        with self.assertRaisesRegex(OverflowError, "guard limb"):
            fixed.SignedLimbPlan(
                plan.absolute_bound,
                plan.required_signed_bits,
                plan.mathematical_limbs,
                plan.mathematical_limbs,
            )
        words = list(fixed.SignedLimbs.encode(1, plan).words)
        words[-1] = 1
        with self.assertRaisesRegex(OverflowError, "sign extension"):
            fixed.SignedLimbs(tuple(words), plan)

        carry_left = (1 << 128) - 1
        carry_right = 1
        self.assertEqual(
            fixed.limb_add(
                fixed.SignedLimbs.encode(carry_left, plan),
                fixed.SignedLimbs.encode(carry_right, plan),
            )[0].decode(),
            1 << 128,
        )
        self.assertEqual(
            fixed.limb_subtract(
                fixed.SignedLimbs.encode(0, plan),
                fixed.SignedLimbs.encode(1 << 128, plan),
            )[0].decode(),
            -(1 << 128),
        )
        accumulator = fixed.SignedLimbs.encode(0, plan)
        for term in ((1 << 170), -(1 << 170), (1 << 130), -(1 << 130), -17):
            accumulator = fixed.limb_add(
                accumulator, fixed.SignedLimbs.encode(term, plan)
            )[0]
        self.assertEqual(accumulator.decode(), -17)
        with self.assertRaises(OverflowError):
            fixed.SignedLimbs.encode(plan.absolute_bound + 1, plan)
        mathematical_minimum = [0] * plan.allocated_limbs
        mathematical_minimum[plan.mathematical_limbs - 1] = 1 << 63
        mathematical_minimum[-1] = fixed.WORD_MASK
        with self.assertRaisesRegex(OverflowError, "semantic bound"):
            fixed.SignedLimbs(tuple(mathematical_minimum), plan)

    def test_schoolbook_high_halves_and_work_are_not_dropped(self) -> None:
        input_plan = fixed.SignedLimbPlan.from_bound((1 << 190) - 1)
        output_plan = fixed.SignedLimbPlan.from_bound((1 << 380) - 1)
        left = (1 << 189) - (1 << 65) + 3
        right = -(1 << 188) + (1 << 127) - 9
        result, work = fixed.limb_full_product(
            fixed.SignedLimbs.encode(left, input_plan),
            fixed.SignedLimbs.encode(right, input_plan),
            output_plan,
        )
        self.assertEqual(result.decode(), left * right)
        self.assertEqual(
            work.wide_products,
            input_plan.allocated_limbs * input_plan.allocated_limbs,
        )
        with self.assertRaises(OverflowError):
            fixed.limb_full_product(
                fixed.SignedLimbs.encode(left, input_plan),
                fixed.SignedLimbs.encode(right, input_plan),
                input_plan,
            )


class RRNSPrimitiveTests(unittest.TestCase):
    def test_primes_products_bounds_and_config_mutations(self) -> None:
        table, scalar = fixed.validate_frozen_rrns()
        self.assertEqual(table.working_product.bit_length(), 248)
        self.assertEqual(scalar.working_product.bit_length(), 496)
        self.assertGreaterEqual(table.working_product, 2 * table.absolute_bound + 1)
        self.assertGreaterEqual(scalar.working_product, 2 * scalar.absolute_bound + 1)
        for prime in scalar.all_moduli:
            self.assertTrue(fixed.is_prime_u64(prime))
            self.assertEqual(math.gcd(prime, 720), 1)
        mutations = (
            fixed.RRNSParameters(
                table.working_primes[:-1] + (table.working_primes[-2],),
                table.redundant_prime,
                table.absolute_bound,
            ),
            fixed.RRNSParameters(
                tuple(sorted((15,) + table.working_primes[:-1])),
                table.redundant_prime,
                table.absolute_bound,
            ),
            fixed.RRNSParameters(
                table.working_primes,
                4_611_686_018_427_387_631,
                table.absolute_bound,
            ),
            fixed.RRNSParameters(
                (table.working_primes[0],),
                table.redundant_prime,
                table.absolute_bound,
            ),
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                with self.assertRaises(ValueError):
                    mutation.validate()

    def test_every_single_changed_channel_is_detected_by_both_forms(self) -> None:
        for parameters in fixed.validate_frozen_rrns():
            for value in (0, 1, -1, parameters.absolute_bound, -parameters.absolute_bound):
                good = fixed.RRNSValue.encode(value, parameters)
                self.assertEqual(fixed.rrns_reconstruct_both(good), value)
                for index, (residue, modulus) in enumerate(
                    zip(good.residues, parameters.all_moduli, strict=True)
                ):
                    mutated = list(good.residues)
                    mutated[index] = (residue + 1) % modulus
                    bad = fixed.RRNSValue(tuple(mutated), parameters)
                    for check in (
                        fixed.rrns_reconstruct_full,
                        fixed.rrns_reconstruct_base_extension,
                    ):
                        with self.subTest(
                            channels=len(parameters.working_primes),
                            value=value,
                            index=index,
                            check=check.__name__,
                        ):
                            with self.assertRaisesRegex(
                                fixed.RRNSChannelFaultDetected,
                                "rrns_channel_fault_detected",
                            ):
                                check(bad)

    def test_single_channel_theorem_is_exhaustive_on_a_small_boundary_code(self) -> None:
        parameters = fixed.RRNSParameters((11, 13), 17, 71)
        parameters.validate()
        self.assertEqual(parameters.working_product, 2 * parameters.absolute_bound + 1)
        for value in range(-parameters.absolute_bound, parameters.absolute_bound + 1):
            good = fixed.RRNSValue.encode(value, parameters)
            self.assertEqual(fixed.rrns_reconstruct_full(good), value)
            self.assertEqual(fixed.rrns_reconstruct_base_extension(good), value)
            for index, modulus in enumerate(parameters.all_moduli):
                for replacement in range(modulus):
                    if replacement == good.residues[index]:
                        continue
                    residues = list(good.residues)
                    residues[index] = replacement
                    bad = fixed.RRNSValue(tuple(residues), parameters)
                    with self.assertRaises(fixed.RRNSChannelFaultDetected):
                        fixed.rrns_reconstruct_full(bad)
                    with self.assertRaises(fixed.RRNSChannelFaultDetected):
                        fixed.rrns_reconstruct_base_extension(bad)

    def test_consistent_corruption_fault_boundary_and_divisibility(self) -> None:
        _, parameters = fixed.validate_frozen_rrns()
        authority = 720 * 17
        wrong = authority + 720
        consistent_wrong = fixed.RRNSValue.encode(wrong, parameters)
        self.assertEqual(fixed.rrns_reconstruct_both(consistent_wrong), wrong)
        with self.assertRaisesRegex(ArithmeticError, "unbounded authority"):
            fixed.require_unbounded_match(wrong, authority)
        self.assertEqual(
            fixed.reconstruct_scaled_rrns(fixed.RRNSValue.encode(authority, parameters)),
            authority,
        )
        with self.assertRaisesRegex(ArithmeticError, "divisible by 720"):
            fixed.reconstruct_scaled_rrns(fixed.RRNSValue.encode(authority + 1, parameters))

        outside = parameters.absolute_bound + 1
        residues = tuple(outside % modulus for modulus in parameters.all_moduli)
        encoded_outside = fixed.RRNSValue(residues, parameters)
        for check in (fixed.rrns_reconstruct_full, fixed.rrns_reconstruct_base_extension):
            with self.assertRaises(fixed.RRNSChannelFaultDetected):
                check(encoded_outside)

        one_channel = fixed.observe_rrns_fault(
            fixed.RRNSValue.encode(authority, parameters), (0,)
        )
        self.assertTrue(one_channel.full_CRT_detected)
        self.assertTrue(one_channel.base_extension_detected)
        self.assertTrue(one_channel.eligible_for_single_channel_claim)
        two_channels = fixed.observe_rrns_fault(
            fixed.RRNSValue.encode(authority, parameters), (0, 1)
        )
        self.assertFalse(two_channels.eligible_for_single_channel_claim)

    def test_rrns_arithmetic_and_montgomery_boundaries(self) -> None:
        table, scalar = fixed.validate_frozen_rrns()
        left = fixed.RRNSValue.encode(123456789, table)
        right = fixed.RRNSValue.encode(-9876543, table)
        self.assertEqual(fixed.rrns_reconstruct_both(fixed.rrns_add(left, right)), 123456789 - 9876543)
        self.assertEqual(fixed.rrns_reconstruct_both(fixed.rrns_subtract(left, right)), 123456789 + 9876543)
        self.assertEqual(fixed.rrns_reconstruct_both(fixed.rrns_multiply(left, right)), 123456789 * -9876543)
        self.assertEqual(fixed.rrns_reconstruct_both(fixed.rrns_multiply_small(left, -30)), -30 * 123456789)
        for modulus in scalar.all_moduli:
            constants = fixed.montgomery_constants(modulus)
            self.assertEqual((modulus * constants.negative_inverse) & fixed.WORD_MASK, fixed.WORD_MASK)
            for a, b in ((0, 0), (1, 1), (modulus - 1, modulus - 1), (123456789, modulus - 2)):
                encoded_a = fixed.montgomery_encode(a, constants)
                encoded_b = fixed.montgomery_encode(b, constants)
                product = fixed.montgomery_multiply(encoded_a, encoded_b, constants)
                self.assertEqual(fixed.montgomery_decode(product, constants), (a * b) % modulus)


class OperatorComparisonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.natural = _make_natural_complete_ten()
        cls.signed = _make_signed_population()
        cls.natural_authority = exact.execute_exact_integer_operator(cls.natural)
        cls.signed_authority = exact.execute_exact_integer_operator(cls.signed)
        cls.results = {}
        for label, captured in (("complete_10", cls.natural), ("signed_12", cls.signed)):
            cls.results[(label, "positional")] = fixed.evaluate_positional_operator(captured)
            cls.results[(label, "resident")] = fixed.evaluate_rrns_operator(
                captured, schedule="resident_nine"
            )
            cls.results[(label, "batched")] = fixed.evaluate_rrns_operator(
                captured, schedule="batched_five_then_four"
            )

    def test_all_candidates_match_both_unbounded_populations(self) -> None:
        for label, authority in (
            ("complete_10", self.natural_authority),
            ("signed_12", self.signed_authority),
        ):
            for candidate in ("positional", "resident", "batched"):
                result = self.results[(label, candidate)]
                with self.subTest(label=label, candidate=candidate):
                    self.assertEqual(result.forward_integer_numerator, authority.forward_integer_numerator)
                    self.assertEqual(result.adjoint_integer_numerator, authority.adjoint_integer_numerator)
                    self.assertEqual(result.forward_integer_reach, authority.forward_integer_reach)
                    self.assertEqual(result.conditional_value_bits, authority.conditional_value_bits)

    def test_batched_schedule_records_replay_and_does_not_change_values(self) -> None:
        for label, captured in (("complete_10", self.natural), ("signed_12", self.signed)):
            resident = self.results[(label, "resident")]
            batched = self.results[(label, "batched")]
            geometry = fixed._reduced_geometry(
                captured.available_cards, len(captured.source_rows[0])
            )
            self.assertEqual(
                batched.recomputed_vector_edges,
                4
                * (
                    geometry.forward_recurrence_vector_edges
                    + geometry.adjoint_recurrence_vector_edges
                ),
            )
            self.assertEqual(resident.recomputed_vector_edges, 0)
            self.assertEqual(
                resident.forward_integer_numerator, batched.forward_integer_numerator
            )

    def test_known_family_telemetry_is_exact_and_separate(self) -> None:
        for label, captured in (("complete_10", self.natural), ("signed_12", self.signed)):
            rows = fixed.captured_operator_telemetry(captured)
            fixed.verify_known_telemetry(label, rows)
            self.assertEqual(len({row.family_fixed_point_exponent for row in rows}), 3)
            self.assertTrue(all(row.high.total_components == row.low.total_components for row in rows))


class SelectiveGlobalAndColexTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        captured = _make_signed_population()
        cls.authority = exact.execute_exact_integer_operator(captured)
        cls.source = dict(cls.authority.source_rows)
        cls.covectors = dict(cls.authority.aggregated_query_covectors)
        cls.forward_levels = exact.build_forward_levels(12, cls.source)
        cls.adjoint_levels = exact.build_adjoint_levels(12, cls.covectors)

    def test_selective_16_and_57_rows_match_every_dense_coordinate(self) -> None:
        for mask, expected in self.authority.forward_scaled_rows:
            row = fixed.selective_forward_row(self.forward_levels, mask)
            self.assertEqual(row.subset_rows_read, 16)
            self.assertEqual(row.values, expected)
        for mask, expected in self.authority.adjoint_scaled_rows:
            row = fixed.selective_adjoint_row(self.adjoint_levels, mask)
            self.assertEqual(row.subset_rows_read, 57)
            self.assertEqual(row.values, expected)

    def test_streamed_global_scan_binds_domain_order_chunks_and_values(self) -> None:
        domain = exact.complete_masks(12, exact.QUERY_CARDS)
        dense = dict(self.authority.forward_scaled_rows)
        receipt = fixed.stream_complete_domain(
            domain, domain, lambda mask: fixed.selective_forward_row(self.forward_levels, mask).values, chunk_size=37
        )
        authority = fixed.stream_complete_domain(
            domain, domain, lambda mask: dense[mask], chunk_size=37
        )
        self.assertEqual(receipt, authority)
        self.assertEqual(receipt.domain_count, len(domain))
        self.assertEqual(receipt.retained_coordinate_rows, 0)
        generated = fixed.stream_complete_domain(
            (mask for mask in domain),
            (mask for mask in domain),
            lambda mask: dense[mask],
            chunk_size=37,
        )
        self.assertEqual(generated, authority)
        with self.assertRaises(fixed.IncompleteGlobalClosure):
            fixed.stream_complete_domain(domain[:-1], domain, lambda mask: dense[mask], chunk_size=37)
        with self.assertRaises(fixed.IncompleteGlobalClosure):
            fixed.stream_complete_domain(tuple(reversed(domain)), domain, lambda mask: dense[mask], chunk_size=37)

    def test_global_certificate_rejects_active_basis_only_omission_and_violation(self) -> None:
        domain = tuple(range(20))
        receipt = fixed.exact_global_closure(domain, domain, lambda _: -1, chunk_size=7)
        self.assertEqual(receipt.violating_coordinates, 0)
        with self.assertRaises(fixed.IncompleteGlobalClosure):
            fixed.exact_global_closure(domain[:5], domain, lambda _: -1, chunk_size=7)
        with self.assertRaisesRegex(ArithmeticError, "positive reduced cost"):
            fixed.exact_global_closure(domain, domain, lambda value: 1 if value == 19 else -1, chunk_size=7)

    def test_colex_row_owner_is_exhaustive_at_10_and_12(self) -> None:
        for available in (10, 12):
            for width in range(6):
                by_rank = {
                    fixed.colex_rank(cards): cards
                    for cards in combinations(range(available), width)
                }
                self.assertEqual(set(by_rank), set(range(comb(available, width))))
                for rank, cards in by_rank.items():
                    receipt = fixed.row_owned_colex_child_ranks(rank, width, available)
                    self.assertEqual(receipt.parent_cards, cards)
                    expected = {
                        fixed.colex_rank(tuple(sorted(cards + (card,))))
                        for card in range(available)
                        if card not in cards
                    }
                    self.assertEqual({row.child_rank for row in receipt.children}, expected)
                    self.assertEqual(receipt.unrank_calls, 1)
                    self.assertEqual(receipt.insertion_position_advances, width)

    def test_literal_45_boundary_rows_need_no_population_values(self) -> None:
        for width in range(6):
            total = comb(45, width)
            for rank in sorted({0, total // 2, total - 1}):
                receipt = fixed.row_owned_colex_child_ranks(rank, width, 45)
                self.assertEqual(len(receipt.children), 45 - width)
                self.assertTrue(all(0 <= row.child_rank < comb(45, width + 1) for row in receipt.children))

    def test_colex_lex_off_by_one_wrong_insert_and_duplicate_mutations_reject(self) -> None:
        receipt = fixed.row_owned_colex_child_ranks(17, 3, 12)
        fixed.validate_colex_row_receipt(receipt, width=3, available_cards=12)
        first = receipt.children[0]
        mutations = (
            replace(receipt, parent_rank=receipt.parent_rank + 1),
            replace(
                receipt,
                children=(replace(first, child_rank=first.child_rank + 1),)
                + receipt.children[1:],
            ),
            replace(
                receipt,
                children=(replace(first, insertion_position=first.insertion_position + 1),)
                + receipt.children[1:],
            ),
            replace(receipt, children=(first, first) + receipt.children[2:]),
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                with self.assertRaises(ValueError):
                    fixed.validate_colex_row_receipt(
                        mutation, width=3, available_cards=12
                    )
        lexicographic = {
            cards: rank for rank, cards in enumerate(combinations(range(12), 4))
        }
        self.assertTrue(
            any(
                lexicographic[cards] != fixed.colex_rank(cards)
                for cards in lexicographic
            )
        )


class TelemetryBoundsAndLedgerTests(unittest.TestCase):
    def test_window_edges_admit_one_step_beyond_rejects_and_zero_is_typed(self) -> None:
        config = fixed.load_preregistered_config()
        windows = config["fixed_width_admission"]["known_control_only_windows"]
        for family, (low, high) in windows.items():
            admitted = exact.FrozenExponentWindow(low, high)
            for edge in (low, high):
                row = fixed.family_telemetry(
                    family,
                    ((exact.CapturedPair(math.ldexp(1.0, edge), -0.0),),),
                    admitted_window=admitted,
                )
                self.assertEqual(row.combined.finite_nonzero_components, 1)
            for outside in (low - 1, high + 1):
                with self.assertRaises(OverflowError):
                    fixed.family_telemetry(
                        family,
                        ((exact.CapturedPair(math.ldexp(1.0, outside), 0.0),),),
                        admitted_window=admitted,
                    )
        zero = fixed.family_telemetry(
            "zero",
            ((exact.CapturedPair(0.0, -0.0),),),
            admitted_window=exact.FrozenExponentWindow(-1, 1),
        )
        self.assertIsNone(zero.combined.canonical_odd_mantissa_exponent_minimum)
        self.assertEqual(zero.family_fixed_point_exponent, 0)
        self.assertEqual(zero.high.positive_zero_components, 1)
        self.assertEqual(zero.low.negative_zero_components, 1)
        with self.assertRaisesRegex(ValueError, "finite"):
            fixed.family_telemetry(
                "bad",
                ((exact.CapturedPair(float("inf"), 0.0),),),
                admitted_window=exact.FrozenExponentWindow(-1, 1),
            )

    def test_frozen_bounds_rrns_capacity_and_literal_geometry_rederive(self) -> None:
        profile = fixed.verify_frozen_bound_profile()
        self.assertEqual(profile.forward_table_plan.allocated_limbs, 5)
        self.assertEqual(profile.adjoint_table_plan.allocated_limbs, 5)
        self.assertEqual(profile.scalar_plan.allocated_limbs, 8)
        self.assertEqual(profile.reach_plan.allocated_limbs, 7)
        table, scalar = fixed.validate_frozen_rrns()
        self.assertGreaterEqual(table.working_product, 2 * profile.forward_table_bound + 1)
        self.assertGreaterEqual(scalar.working_product, 2 * profile.scalar_bound + 1)
        geometry = fixed.verify_literal_45_formulas()
        self.assertEqual(geometry.source_occupancies, 8_145_060)
        self.assertEqual(geometry.query_occupancies, 148_995)
        self.assertEqual(geometry.forward_recurrence_vector_edges, 55_619_730)
        self.assertEqual(geometry.adjoint_recurrence_vector_edges, 640_575)

    def test_work_ledgers_remain_heterogeneous_and_memory_never_claims_fit(self) -> None:
        ledgers = fixed.literal_45_work_ledgers()
        self.assertEqual(len(ledgers), 24)
        self.assertEqual(
            {row.candidate for row in ledgers},
            {"positional", "resident_nine_RRNS", "batched_five_then_four_RRNS"},
        )
        self.assertNotIn("total", {field.name for field in fields(fixed.PrimitiveWorkLedger)})
        batched = [
            row
            for row in ledgers
            if row.candidate == "batched_five_then_four_RRNS"
            and row.mode in {"cold_build_G", "cold_build_H"}
        ]
        self.assertTrue(all(row.recomputed_edges_under_channel_batching > 0 for row in batched))
        forward_selective = next(
            row
            for row in ledgers
            if row.candidate == "positional" and row.mode == "one_selective_forward_query"
        )
        forward_global = next(
            row
            for row in ledgers
            if row.candidate == "positional" and row.mode == "streamed_all_query_forward_scan"
        )
        self.assertGreater(forward_global.small_weight_products, forward_selective.small_weight_products)
        memory = fixed.literal_45_memory_ledgers()
        self.assertEqual(len(memory), 3)
        self.assertTrue(all(row.complete_dense_output_bytes_charged == 0 for row in memory))
        batched_memory = next(row for row in memory if row.candidate.startswith("batched"))
        self.assertGreater(
            batched_memory.second_batch_forward_recurrence_scratch_bytes, 0
        )
        self.assertGreater(
            batched_memory.second_batch_adjoint_recurrence_scratch_bytes, 0
        )
        self.assertGreater(batched_memory.forward_replay_input_bytes, 0)
        self.assertGreater(batched_memory.adjoint_replay_input_bytes, 0)


if __name__ == "__main__":
    unittest.main()
