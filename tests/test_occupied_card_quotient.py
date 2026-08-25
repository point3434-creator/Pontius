from __future__ import annotations

from dataclasses import replace
from fractions import Fraction
from itertools import combinations, product
from math import comb, prod
import unittest

import numpy as np

from pontius.factor_tt_contraction import (
    FactorTTBeliefWorkspace,
    FactorTTTopology,
    _tt_half_vectors,
    enumerated_factor_tt_expectation,
    evaluate_tensor_train_assignments,
)
from pontius.factorized_belief import FactorizedCardBelief
from pontius.occupied_card_quotient import (
    OccupancyQuotientCombinatorics,
    OccupiedCardQuotientTopology,
)
from pontius.open_mode_factor_tt import (
    BidirectionalFactorTTTopology,
    OpenModeFactorTTWorkspace,
    contract_open_modes,
)
from pontius.tensor_train import TensorTrain


def _mask(hand: tuple[int, int]) -> int:
    return (1 << hand[0]) | (1 << hand[1])


def _hands(cards: range) -> tuple[tuple[int, int], ...]:
    return tuple(combinations(cards, 2))


def _compatible_records(
    axes: tuple[tuple[tuple[int, int], ...], ...],
) -> tuple[tuple[int, ...], tuple[tuple[int, ...], ...]]:
    masks = tuple(tuple(_mask(hand) for hand in axis) for axis in axes)
    record_masks = []
    record_indices = []
    for assignment in product(*(range(len(axis)) for axis in axes)):
        supplied = tuple(masks[seat][index] for seat, index in enumerate(assignment))
        union = 0
        for mask in supplied:
            union |= mask
        if union.bit_count() == 2 * len(axes):
            record_masks.append(union)
            record_indices.append(assignment)
    return tuple(record_masks), tuple(record_indices)


def _literal_disjoint(
    source_masks: tuple[int, ...],
    source_rows: tuple[tuple[Fraction, ...], ...],
    query_masks: tuple[int, ...],
) -> tuple[tuple[Fraction, ...], ...]:
    width = len(source_rows[0])
    return tuple(
        tuple(
            sum(
                (
                    row[feature]
                    for mask, row in zip(source_masks, source_rows, strict=True)
                    if not mask & query
                ),
                Fraction(0),
            )
            for feature in range(width)
        )
        for query in query_masks
    )


def _float_rows(values: tuple[tuple[Fraction, ...], ...]) -> np.ndarray:
    return np.asarray(
        [[float(value) for value in row] for row in values],
        dtype=np.float64,
    )


class OccupiedCardQuotientTests(unittest.TestCase):
    def test_exact_randomized_small_universes_match_literal_compatibility(self) -> None:
        rng = np.random.default_rng(36_700)
        for available_cards, source_cards, query_cards in (
            (5, 2, 2),
            (6, 4, 2),
            (7, 2, 4),
            (8, 4, 4),
        ):
            unique_source = tuple(
                sum(1 << card for card in selected)
                for selected in combinations(range(available_cards), source_cards)
            )
            source_masks = tuple(
                mask
                for index, mask in enumerate(unique_source)
                for _ in range(1 + index % 3)
            )
            query_masks = tuple(
                sum(1 << card for card in selected)
                for selected in combinations(range(available_cards), query_cards)
            )
            numerators = rng.integers(-9, 10, size=(len(source_masks), 3))
            denominators = rng.integers(1, 8, size=(len(source_masks), 3))
            rows = tuple(
                tuple(
                    Fraction(
                        int(numerators[record, feature]),
                        int(denominators[record, feature]),
                    )
                    for feature in range(3)
                )
                for record in range(len(source_masks))
            )
            source_seats = tuple(range(source_cards // 2))
            query_seats = tuple(
                range(source_cards // 2, (source_cards + query_cards) // 2)
            )
            topology = OccupiedCardQuotientTopology.compile(
                source_seats=source_seats,
                query_seats=query_seats,
                open_seats=(query_seats[0],),
                source_record_masks=source_masks,
                query_record_masks=query_masks,
            )
            self.assertEqual(
                topology.apply_exact(rows).query_rows,
                _literal_disjoint(source_masks, rows, query_masks),
            )

    def test_full_width_arithmetic_exposes_the_exact_90_and_6_quotients(self) -> None:
        left_to_right = OccupancyQuotientCombinatorics(
            available_cards=45,
            source_pairs=3,
            query_pairs=2,
        )
        right_to_left = OccupancyQuotientCombinatorics(
            available_cards=45,
            source_pairs=2,
            query_pairs=3,
        )

        self.assertTrue(left_to_right.identities_hold())
        self.assertTrue(right_to_left.identities_hold())
        self.assertEqual(left_to_right.source_occupancy_masks, 8_145_060)
        self.assertEqual(left_to_right.source_pairing_multiplicity, 90)
        self.assertEqual(left_to_right.labeled_source_assignments, 733_055_400)
        self.assertEqual(left_to_right.query_occupancy_masks, 148_995)
        self.assertEqual(left_to_right.query_pairing_multiplicity, 6)
        self.assertEqual(left_to_right.labeled_query_assignments, 893_970)
        self.assertEqual(left_to_right.containment_key_universe, 164_221)
        self.assertEqual(left_to_right.marginal_updates_per_source_occupancy, 57)
        self.assertEqual(left_to_right.signed_terms_per_query_record, 16)
        self.assertEqual(right_to_left.containment_key_universe, 164_221)
        self.assertEqual(right_to_left.marginal_updates_per_source_occupancy, 16)
        self.assertEqual(right_to_left.signed_terms_per_query_record, 57)
        self.assertEqual(
            left_to_right.containment_key_universe,
            sum(comb(45, width) for width in range(5)),
        )

    def test_exact_forward_transpose_and_dot_product_match_literal_records(self) -> None:
        hands = _hands(range(6))
        source_masks, source_indices = _compatible_records((hands, hands))
        query_masks = tuple(_mask(hand) for hand in hands)
        source_rows = tuple(
            (
                Fraction((first + 1) * (second + 2), 7),
                Fraction(0) if (first + second) % 4 == 0 else Fraction(first - second, 5),
            )
            for first, second in source_indices
        )
        topology = OccupiedCardQuotientTopology.compile(
            source_seats=(0, 1),
            query_seats=(2,),
            open_seats=(2,),
            source_record_masks=source_masks,
            query_record_masks=query_masks,
        )

        result = topology.apply_exact(source_rows)
        expected = _literal_disjoint(source_masks, source_rows, query_masks)
        self.assertEqual(result.query_rows, expected)
        self.assertEqual(result.work.source_records, 90)
        self.assertEqual(result.work.unique_source_occupancies, 15)
        self.assertEqual(result.work.source_marginal_updates, 15 * 11)
        self.assertEqual(result.work.signed_query_terms, 15 * 4)

        query_rows = tuple(
            (Fraction(index - 4, 3), Fraction(0) if index % 3 else Fraction(5, 11))
            for index in range(len(query_masks))
        )
        adjoint = topology.apply_adjoint_exact(query_rows)
        literal_adjoint = tuple(
            tuple(
                sum(
                    (
                        query_rows[query][feature]
                        for query in range(len(query_masks))
                        if not source_mask & query_masks[query]
                    ),
                    Fraction(0),
                )
                for feature in range(2)
            )
            for source_mask in source_masks
        )
        self.assertEqual(adjoint, literal_adjoint)
        forward_dot = sum(
            (
                result.query_rows[query][feature] * query_rows[query][feature]
                for query in range(len(query_masks))
                for feature in range(2)
            ),
            Fraction(0),
        )
        transpose_dot = sum(
            (
                source_rows[source][feature] * adjoint[source][feature]
                for source in range(len(source_masks))
                for feature in range(2)
            ),
            Fraction(0),
        )
        self.assertEqual(forward_dot, transpose_dot)

    def test_source_seat_permutation_and_one_seat_refresh_are_canonical(self) -> None:
        hands = _hands(range(8))
        weights = {
            seat: tuple(
                Fraction((seat + 2) * (index + 1), index + 3)
                for index in range(len(hands))
            )
            for seat in (0, 1, 2)
        }
        changed = dict(weights)
        changed[1] = tuple(
            Fraction(0) if index % 5 == 0 else value * Fraction(7, 5)
            for index, value in enumerate(weights[1])
        )

        def records(
            order: tuple[int, ...],
            supplied: dict[int, tuple[Fraction, ...]],
        ) -> tuple[tuple[int, ...], tuple[tuple[Fraction, ...], ...]]:
            masks, indices = _compatible_records(tuple(hands for _ in order))
            rows = tuple(
                (
                    prod(supplied[seat][assignment[depth]] for depth, seat in enumerate(order)),
                    prod(
                        supplied[seat][assignment[depth]] * Fraction(seat + 1, 9)
                        for depth, seat in enumerate(order)
                    ),
                )
                for assignment in indices
            )
            return masks, rows

        source_masks, source_rows = records((0, 1, 2), weights)
        permuted_masks, permuted_rows = records((2, 0, 1), weights)
        query_masks = tuple(_mask(hand) for hand in hands)
        first = OccupiedCardQuotientTopology.compile(
            source_seats=(0, 1, 2),
            query_seats=(3,),
            open_seats=(3,),
            source_record_masks=source_masks,
            query_record_masks=query_masks,
        )
        permuted = OccupiedCardQuotientTopology.compile(
            source_seats=(2, 0, 1),
            query_seats=(3,),
            open_seats=(3,),
            source_record_masks=permuted_masks,
            query_record_masks=query_masks,
        )
        first_result = first.apply_exact(source_rows)
        permuted_result = permuted.apply_exact(permuted_rows)
        self.assertEqual(
            first_result.coefficients.canonical_bytes(),
            permuted_result.coefficients.canonical_bytes(),
        )
        self.assertEqual(first_result.query_rows, permuted_result.query_rows)
        self.assertEqual(set(first.source_multiplicities), {90})

        refreshed_masks, refreshed_rows = records((0, 1, 2), changed)
        self.assertEqual(refreshed_masks, source_masks)
        refreshed = first.refresh_one_source_seat_exact(
            first_result.coefficients,
            changed_seat=1,
            refreshed_record_values=refreshed_rows,
        )
        cold = OccupiedCardQuotientTopology.compile(
            source_seats=(0, 1, 2),
            query_seats=(3,),
            open_seats=(3,),
            source_record_masks=refreshed_masks,
            query_record_masks=query_masks,
        ).aggregate_exact(refreshed_rows)
        self.assertEqual(refreshed.canonical_bytes(), cold.canonical_bytes())
        self.assertNotEqual(
            refreshed.canonical_bytes(),
            first_result.coefficients.canonical_bytes(),
        )

    def test_fixed_card_projection_is_exact_and_unsafe_scope_rejects(self) -> None:
        hands = _hands(range(6))
        source_masks, source_indices = _compatible_records((hands, hands))
        source_rows = tuple(
            (Fraction(first + second + 1, 13),) for first, second in source_indices
        )
        hero = (1 << 10) | (1 << 11)
        plain_queries = tuple(_mask(hand) for hand in hands)
        fixed_queries = tuple(hero | mask for mask in plain_queries)
        plain = OccupiedCardQuotientTopology.compile(
            source_seats=(0, 1),
            query_seats=(2,),
            open_seats=(2,),
            source_record_masks=source_masks,
            query_record_masks=plain_queries,
        ).apply_exact(source_rows)
        projected = OccupiedCardQuotientTopology.compile(
            source_seats=(0, 1),
            query_seats=(2,),
            open_seats=(2,),
            source_record_masks=source_masks,
            query_record_masks=fixed_queries,
            query_fixed_mask=hero,
        ).apply_exact(source_rows)
        self.assertEqual(plain.query_rows, projected.query_rows)

        with self.assertRaisesRegex(ValueError, "open seat"):
            OccupiedCardQuotientTopology.compile(
                source_seats=(0, 1),
                query_seats=(2,),
                open_seats=(1,),
                source_record_masks=source_masks,
                query_record_masks=fixed_queries,
                query_fixed_mask=hero,
            )
        with self.assertRaisesRegex(ValueError, "disjoint"):
            OccupiedCardQuotientTopology.compile(
                source_seats=(0, 1),
                query_seats=(1, 2),
                open_seats=(2,),
                source_record_masks=source_masks,
                query_record_masks=fixed_queries,
                query_fixed_mask=hero,
            )
        unsafe_source = tuple(mask | (1 << 10) for mask in source_masks)
        with self.assertRaisesRegex(ValueError, "not absent"):
            OccupiedCardQuotientTopology.compile(
                source_seats=(0, 1),
                query_seats=(2,),
                open_seats=(2,),
                source_record_masks=unsafe_source,
                query_record_masks=fixed_queries,
                query_fixed_mask=hero,
            )

    def test_factor_tt_open_mode_and_dense_oracles_match_the_quotient(self) -> None:
        left_axis = _hands(range(7))
        hero = ((10, 11),)
        right_one = ((0, 7), (1, 7), (2, 8), (3, 8), (4, 9))
        right_two = ((8, 9), (7, 9), (7, 8), (5, 9), (6, 8))
        axes = (left_axis, left_axis, left_axis, hero, right_one, right_two)
        rng = np.random.default_rng(367)
        belief = FactorizedCardBelief(
            hands_by_player=axes,
            mixture_weights=np.asarray((0.6, 1.1), dtype=np.float64),
            unary_weights=tuple(
                rng.uniform(0.0, 1.0, size=(2, len(axis))) for axis in axes
            ),
        )
        dense_values = rng.normal(size=belief.hand_counts)
        train = TensorTrain.from_dense(dense_values, maximum_rank=3)
        topology = FactorTTTopology.compile(belief, split_index=3)
        base = FactorTTBeliefWorkspace.compile(
            topology,
            belief,
            query_chunk_records=7,
        )
        bidirectional = BidirectionalFactorTTTopology.compile(topology)
        workspace = OpenModeFactorTTWorkspace.compile(bidirectional, base)
        open_result = contract_open_modes(
            workspace,
            train,
            target_seats=(3, 4, 5),
        )
        self.assertEqual(
            tuple(direction.direction for direction in open_result.directions),
            ("left_to_right",),
        )

        left_vectors, right_vectors = _tt_half_vectors(train, topology)
        components = belief.component_count
        rank = left_vectors.shape[1]
        source_value_rows = (
            base.left_component_products[:, :, None] * left_vectors[:, None, :]
        ).reshape(topology.left.records, components * rank)
        quotient = OccupiedCardQuotientTopology.compile(
            source_seats=topology.left.seats,
            query_seats=topology.right.seats,
            open_seats=topology.right.seats,
            source_record_masks=topology.left.masks,
            query_record_masks=topology.right.masks,
            query_fixed_mask=_mask(hero[0]),
        )
        value_transform = quotient.apply_exact(source_value_rows)
        reach_transform = quotient.apply_exact(base.left_component_products)
        compatible_values = _float_rows(value_transform.query_rows).reshape(
            topology.right.records,
            components,
            rank,
        )
        compatible_reaches = _float_rows(reach_transform.query_rows)
        numerator_records = np.einsum(
            "k,qk,qkr,qr->q",
            base.mixture_weights,
            base.right_component_products,
            compatible_values,
            right_vectors,
            optimize=True,
        )
        reach_records = np.einsum(
            "k,qk,qk->q",
            base.mixture_weights,
            base.right_component_products,
            compatible_reaches,
            optimize=True,
        )

        materialized = belief.materialize()
        assignments = np.ascontiguousarray(materialized.assignments, dtype=np.int32)
        assignment_values = evaluate_tensor_train_assignments(train, assignments)
        dense_weights = materialized.unnormalized_weights
        for target in (3, 4, 5):
            depth = topology.right.seats.index(target)
            quotient_numerators = np.bincount(
                topology.right.indices[:, depth],
                weights=numerator_records,
                minlength=belief.hand_counts[target],
            )
            quotient_reaches = np.bincount(
                topology.right.indices[:, depth],
                weights=reach_records,
                minlength=belief.hand_counts[target],
            )
            dense_numerators = np.bincount(
                assignments[:, target],
                weights=dense_weights * assignment_values,
                minlength=belief.hand_counts[target],
            )
            dense_reaches = np.bincount(
                assignments[:, target],
                weights=dense_weights,
                minlength=belief.hand_counts[target],
            )
            current = open_result.for_seat(target)
            np.testing.assert_allclose(
                quotient_numerators,
                dense_numerators,
                atol=2e-11,
                rtol=0.0,
            )
            np.testing.assert_allclose(
                quotient_reaches,
                dense_reaches,
                atol=2e-11,
                rtol=0.0,
            )
            np.testing.assert_allclose(
                quotient_numerators,
                current.unnormalized_numerators,
                atol=2e-11,
                rtol=0.0,
            )
            np.testing.assert_allclose(
                quotient_reaches,
                current.unnormalized_reaches,
                atol=2e-11,
                rtol=0.0,
            )

        quotient_numerator = float(np.sum(numerator_records))
        current_scalar = base.contract(train)
        dense_scalar = enumerated_factor_tt_expectation(belief, train)
        self.assertAlmostEqual(
            quotient_numerator / base.partition,
            current_scalar.expectation,
            places=11,
        )
        self.assertAlmostEqual(
            quotient_numerator / base.partition,
            dense_scalar.expectation,
            places=11,
        )
        self.assertEqual(value_transform.work.source_records, 630)
        self.assertEqual(value_transform.work.unique_source_occupancies, 7)
        self.assertEqual(set(quotient.source_multiplicities), {90})

    def test_combinatorics_and_refresh_validation_fail_closed(self) -> None:
        with self.assertRaises(ValueError):
            OccupancyQuotientCombinatorics(
                available_cards=5,
                source_pairs=3,
                query_pairs=1,
            )
        topology = OccupiedCardQuotientTopology.compile(
            source_seats=(0,),
            query_seats=(1,),
            open_seats=(1,),
            source_record_masks=(3,),
            query_record_masks=(12,),
        )
        previous = topology.aggregate_exact(((Fraction(1),),))
        with self.assertRaisesRegex(ValueError, "open seat"):
            replace(topology, open_seats=(0,))
        with self.assertRaisesRegex(ValueError, "closed source"):
            topology.refresh_one_source_seat_exact(
                previous,
                changed_seat=1,
                refreshed_record_values=((Fraction(2),),),
            )
        with self.assertRaisesRegex(ValueError, "row"):
            topology.apply_exact(())


if __name__ == "__main__":
    unittest.main()
