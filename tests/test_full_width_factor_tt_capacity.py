from __future__ import annotations

import unittest
from itertools import product

import numpy as np

from pontius.factor_tt_contraction import (
    FactorTTBeliefWorkspace,
    FactorTTTopology,
)
from pontius.factorized_belief import FactorizedCardBelief
from pontius.full_width_factor_tt_capacity import (
    FactorTTHalfAllocation,
    FactorTTPersistentAllocation,
    canonical_six_seat_river_allocation,
    labeled_disjoint_pair_assignments,
    minimum_scalar_topology_numeric_bytes,
)
from pontius.open_mode_factor_tt import (
    BidirectionalFactorTTTopology,
    OpenModeFactorTTWorkspace,
)
from pontius.river import make_hole, parse_cards


def _mask(hand: tuple[int, int]) -> int:
    return (1 << hand[0]) | (1 << hand[1])


class FullWidthFactorTTCapacityTests(unittest.TestCase):
    def test_labeled_complete_assignment_formula_matches_small_enumeration(self) -> None:
        for available in (6, 8, 10):
            hands = tuple(
                (first, second)
                for first in range(available)
                for second in range(first + 1, available)
            )
            for axes in range(4):
                expected = 0
                for assignment in product(hands, repeat=axes):
                    masks = tuple(_mask(hand) for hand in assignment)
                    if sum(mask.bit_count() for mask in masks) == (
                        0 if not masks else int(np.bitwise_or.reduce(masks)).bit_count()
                    ):
                        expected += 1
                self.assertEqual(
                    labeled_disjoint_pair_assignments(
                        available_cards=available,
                        opponent_axes=axes,
                    ),
                    expected,
                )

    def test_allocation_formula_matches_current_small_topologies_exactly(self) -> None:
        board = parse_cards("2c", "7d", "9h", "Js", "Qc")
        hero = make_hole("Ks", "Td")
        blocked = {*board, *hero}
        remaining = tuple(card for card in range(52) if card not in blocked)
        opponent_axis = tuple(
            make_hole(remaining[index], remaining[index + 1])
            for index in range(0, 24, 2)
        )
        hands = tuple(
            (hero,) if seat == 3 else opponent_axis for seat in range(6)
        )
        belief = FactorizedCardBelief(
            hands_by_player=hands,
            mixture_weights=np.ones(1, dtype=np.float64),
            unary_weights=tuple(
                np.ones((1, len(axis)), dtype=np.float64) for axis in hands
            ),
            board=board,
        )
        topology = FactorTTTopology.compile(belief, split_index=3)
        bidirectional = BidirectionalFactorTTTopology.compile(topology)
        base = FactorTTBeliefWorkspace.compile(topology, belief)
        workspace = OpenModeFactorTTWorkspace.compile(bidirectional, base)
        estimate = FactorTTPersistentAllocation(
            hand_counts=belief.hand_counts,
            split_index=3,
            left=FactorTTHalfAllocation(3, topology.left.records),
            right=FactorTTHalfAllocation(3, topology.right.records),
            component_count=belief.component_count,
            forward_incidence_entries=topology.incidence_entries,
            reverse_incidence_entries=bidirectional.reverse_incidence_entries,
        )

        self.assertEqual(estimate.base_topology_numeric_bytes, topology.numeric_bytes)
        self.assertEqual(
            estimate.bidirectional_topology_numeric_bytes,
            bidirectional.numeric_bytes,
        )
        self.assertEqual(estimate.base_workspace_numeric_bytes, base.numeric_bytes)
        self.assertEqual(estimate.open_workspace_numeric_bytes, workspace.numeric_bytes)
        expected_resident = (
            base.mixture_weights.nbytes
            + base.left_component_products.nbytes
            + base.right_component_products.nbytes
            + topology.left.indices.nbytes
            + topology.right.indices.nbytes
        )
        self.assertEqual(estimate.resident_belief_numeric_bytes, expected_resident)

    def test_optimistic_scalar_ordering_is_no_worse_on_reduced_axis(self) -> None:
        frozen = canonical_six_seat_river_allocation(
            controlled_seat=3,
            opponent_hand_count=45,
            available_cards=10,
        )
        optimistic = minimum_scalar_topology_numeric_bytes(
            opponent_hand_count=45,
            available_cards=10,
        )

        self.assertLess(optimistic, frozen.base_topology_numeric_bytes)
        self.assertGreater(
            frozen.bidirectional_topology_numeric_bytes,
            frozen.base_topology_numeric_bytes,
        )

    def test_semantic_integer_guards_reject_boolean_and_partial_width(self) -> None:
        with self.assertRaises(ValueError):
            labeled_disjoint_pair_assignments(available_cards=True, opponent_axes=2)
        with self.assertRaises(ValueError):
            labeled_disjoint_pair_assignments(available_cards=8, opponent_axes=True)
        with self.assertRaises(ValueError):
            canonical_six_seat_river_allocation(
                controlled_seat=3,
                opponent_hand_count=989,
                available_cards=45,
            )


if __name__ == "__main__":
    unittest.main()
