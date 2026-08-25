from __future__ import annotations

from dataclasses import replace
from fractions import Fraction
from itertools import combinations
from itertools import product
import json
from math import comb
import unittest

from pontius.full_width_occupied_card_quotient_capacity import (
    DEVICE_NUMERIC_CAP_BYTES,
    FROZEN_FIXTURE_STATE_RANKS,
    FROZEN_OPPONENT_HANDS,
    FROZEN_QUERY_CHUNK,
    FROZEN_SOURCE_CHUNK,
    HOST_NUMERIC_CAP_BYTES,
    OccupiedCardGeometry,
    combination_rank,
    combination_unrank,
    fixture_capacity_model,
    safe_feature_envelope_model,
    showdown_state_rank_trace,
    subset_table_index,
)
from pontius.full_width_river_capacity_preflight import (
    _CONFIG,
    _parse_config,
    _six_axis_belief,
    _strength_codes,
    _street_inventory,
    _workload_automaton,
)
from pontius.occupied_card_quotient import OccupiedCardQuotientTopology
from pontius.structured_showdown_automaton import build_structured_showdown_automaton


def _mask(*cards: int) -> int:
    result = 0
    for card in cards:
        result |= 1 << card
    return result


class FullWidthOccupiedCardQuotientCapacityTests(unittest.TestCase):
    def test_frozen_geometry_rederives_every_preregistered_count(self) -> None:
        geometry = OccupiedCardGeometry()
        self.assertEqual(geometry.available_cards, 45)
        self.assertEqual(geometry.source_cards, 6)
        self.assertEqual(geometry.query_cards, 4)
        self.assertEqual(geometry.source_occupancies, 8_145_060)
        self.assertEqual(geometry.source_pairings_per_occupancy, 90)
        self.assertEqual(geometry.source_labeled_records, 733_055_400)
        self.assertEqual(geometry.query_occupancies, 148_995)
        self.assertEqual(geometry.query_pairings_per_occupancy, 6)
        self.assertEqual(geometry.query_labeled_records, 893_970)
        self.assertEqual(geometry.containment_keys, 164_221)
        self.assertEqual(geometry.forward_source_subset_visits, 57)
        self.assertEqual(geometry.forward_query_signed_terms, 16)
        self.assertEqual(geometry.adjoint_query_occupancy_subset_visits, 16)
        self.assertEqual(geometry.adjoint_source_occupancy_signed_terms, 57)

    def test_combinadic_is_exhaustive_and_collision_free_on_bounded_universes(self) -> None:
        for universe in range(1, 11):
            for width in range(min(6, universe) + 1):
                rows = tuple(combinations(range(universe), width))
                ranks = tuple(
                    combination_rank(row, universe_size=universe) for row in rows
                )
                self.assertEqual(len(set(ranks)), comb(universe, width))
                self.assertEqual(set(ranks), set(range(comb(universe, width))))
                unranked = tuple(
                    combination_unrank(
                        rank,
                        universe_size=universe,
                        cardinality=width,
                    )
                    for rank in range(comb(universe, width))
                )
                self.assertEqual(set(unranked), set(rows))
                self.assertEqual(
                    tuple(
                        combination_rank(row, universe_size=universe)
                        for row in unranked
                    ),
                    tuple(range(comb(universe, width))),
                )

    def test_full_width_combinadic_boundaries_and_samples_round_trip(self) -> None:
        for width in (0, 1, 2, 4, 6):
            count = comb(45, width)
            ranks = sorted(
                {
                    0,
                    count - 1,
                    count // 2,
                    count // 3,
                    (2 * count) // 3,
                }
            )
            for rank in ranks:
                cards = combination_unrank(
                    rank,
                    universe_size=45,
                    cardinality=width,
                )
                self.assertEqual(
                    combination_rank(cards, universe_size=45),
                    rank,
                )
        self.assertLess(
            subset_table_index(
                (41, 42, 43, 44), universe_size=45, maximum_cardinality=4
            ),
            164_221,
        )

    def test_ranked_bounded_layout_reuses_the_exact_forward_and_adjoint_oracle(self) -> None:
        source_masks = (
            _mask(0, 1, 2, 3, 4, 5),
            _mask(0, 1, 2, 3, 4, 5),
            _mask(0, 1, 2, 3, 6, 7),
        )
        query_masks = (_mask(0, 1, 8, 9), _mask(4, 5, 8, 9))
        topology = OccupiedCardQuotientTopology.compile(
            source_seats=(0, 1, 2),
            query_seats=(3, 4, 5),
            open_seats=(3,),
            source_record_masks=source_masks,
            query_record_masks=query_masks,
        )
        values = (
            (Fraction(1, 3), Fraction(-2, 5)),
            (Fraction(7, 4), Fraction(0)),
            (Fraction(-5, 6), Fraction(11, 7)),
        )
        result = topology.apply_exact(values)
        literal = tuple(
            tuple(
                sum(
                    values[index][feature]
                    for index, source in enumerate(source_masks)
                    if source & query == 0
                )
                for feature in range(2)
            )
            for query in query_masks
        )
        self.assertEqual(result.query_rows, literal)

        seen_ranks = set()
        for occupied_mask in result.coefficients.masks:
            cards = tuple(
                card for card in range(10) if occupied_mask & (1 << card)
            )
            rank = combination_rank(cards, universe_size=10)
            self.assertEqual(
                combination_unrank(rank, universe_size=10, cardinality=6),
                cards,
            )
            seen_ranks.add(rank)
            for width in range(5):
                for subset in combinations(cards, width):
                    self.assertLess(
                        subset_table_index(
                            subset, universe_size=10, maximum_cardinality=4
                        ),
                        sum(comb(10, size) for size in range(5)),
                    )
        self.assertEqual(len(seen_ranks), len(result.coefficients.masks))

        query_covectors = (
            (Fraction(2), Fraction(-1, 2)),
            (Fraction(-3, 7), Fraction(5, 9)),
        )
        adjoint = topology.apply_adjoint_exact(query_covectors)
        left = sum(
            result.query_rows[row][feature] * query_covectors[row][feature]
            for row in range(len(query_masks))
            for feature in range(2)
        )
        right = sum(
            values[row][feature] * adjoint[row][feature]
            for row in range(len(source_masks))
            for feature in range(2)
        )
        self.assertEqual(left, right)

    def test_fixture_rank_trace_and_automaton_bytes_are_independently_derived(self) -> None:
        parsed = _parse_config(json.loads(_CONFIG.read_text(encoding="utf-8")))
        river_belief, _ = _street_inventory(parsed)
        belief = _six_axis_belief(river_belief)
        codes = _strength_codes(belief)
        exact_codes = tuple(tuple(int(value) for value in row) for row in codes)
        trace = showdown_state_rank_trace(
            exact_codes,
            target_player=parsed["controlled_seat"],
            contenders=tuple(range(6)),
        )
        self.assertEqual(trace, FROZEN_FIXTURE_STATE_RANKS)
        self.assertEqual(len(set(exact_codes[0])), 59)

        automaton = _workload_automaton(
            belief,
            controlled_seat=parsed["controlled_seat"],
            pot_chips=parsed["showdown_pot_chips"],
            bet_chips=parsed["showdown_bet_chips"],
        )
        model = fixture_capacity_model()
        allocation = model.automata[0]
        self.assertEqual(automaton.state_ranks[1:-1], trace)
        self.assertEqual(allocation.numeric_bytes, automaton.numeric_bytes)
        self.assertEqual(
            allocation.forbidden_dense_tensor_train_bytes,
            automaton.dense_tt_export_bytes,
        )
        self.assertEqual(allocation.state_ranks[2], 175)
        self.assertEqual(model.feature_width, 176)

    def test_sunk_payoff_is_exactly_an_affine_fold_of_reach(self) -> None:
        strengths = (
            (0, 2),
            (1, 2),
            (0, 1),
            (1,),
            (0, 2),
            (1, 2),
        )
        automaton = build_structured_showdown_automaton(
            strength_codes=strengths,
            contenders=tuple(range(6)),
            target_player=3,
            contributed=False,
            pot=12.0,
            bet_size=0.0,
        )
        source_rank = automaton.state_ranks[3]
        self.assertEqual(
            source_rank,
            showdown_state_rank_trace(
                strengths,
                target_player=3,
                contenders=tuple(range(6)),
            )[2],
        )
        for assignment in product(*(range(len(axis)) for axis in strengths)):
            state = 0
            for mode in range(3):
                state = int(automaton.transitions[mode][state, assignment[mode]])
            query_state = state
            for mode in range(3, 5):
                query_state = int(
                    automaton.transitions[mode][query_state, assignment[mode]]
                )
            winner = float(
                automaton.terminal_winner_values[query_state, assignment[5]]
            )
            expected = winner + automaton.sunk_value * 1.0
            actual = float(automaton.evaluate_assignments((assignment,))[0])
            self.assertEqual(actual, expected)

    def test_fixture_layout_names_every_array_and_passes_only_source_caps(self) -> None:
        model = fixture_capacity_model()
        self.assertEqual(model.opponent_hand_count, FROZEN_OPPONENT_HANDS)
        self.assertEqual(model.source_chunk_occupancies, FROZEN_SOURCE_CHUNK)
        self.assertEqual(model.query_chunk_records, FROZEN_QUERY_CHUNK)
        self.assertEqual(model.persistent_labeled_source_numeric_bytes, 0)
        self.assertEqual(model.sparse_incidence_numeric_bytes, 0)
        self.assertEqual(model.allocated_tensor_train_numeric_bytes, 0)
        self.assertGreater(model.forbidden_dense_tensor_train_bytes, 0)
        self.assertTrue(model.excluded_nonnumeric_classes)
        self.assertEqual(
            model.host_persistent_numeric_bytes,
            sum(row.numeric_bytes for row in model.host_persistent_rows),
        )
        self.assertEqual(
            model.device_source_phase_numeric_bytes,
            model.device_persistent_numeric_bytes
            + sum(row.numeric_bytes for row in model.source_phase_rows),
        )
        self.assertEqual(
            model.device_query_phase_numeric_bytes,
            model.device_persistent_numeric_bytes
            + sum(row.numeric_bytes for row in model.query_phase_rows),
        )
        self.assertEqual(
            model.device_adjoint_phase_numeric_bytes,
            model.device_persistent_numeric_bytes
            + sum(row.numeric_bytes for row in model.adjoint_phase_rows),
        )
        self.assertEqual(
            model.device_peak_numeric_bytes,
            max(
                model.device_source_phase_numeric_bytes,
                model.device_query_phase_numeric_bytes,
                model.device_adjoint_phase_numeric_bytes,
            ),
        )
        names = {row.name for row in model.device_persistent_rows}
        self.assertTrue(
            {
                "query_card_masks",
                "query_first_hand_indices",
                "query_second_hand_indices",
                "binomial_table",
                "source_local_pairing_template",
                "seat_unary_weights",
                "term_mode_factors",
                "automaton_0_terminal_values",
            }.issubset(names)
        )
        self.assertLess(model.host_peak_numeric_bytes, HOST_NUMERIC_CAP_BYTES)
        self.assertLess(model.device_peak_numeric_bytes, DEVICE_NUMERIC_CAP_BYTES)
        self.assertEqual(model.host_persistent_numeric_bytes, 15_159_204)
        self.assertEqual(model.host_peak_numeric_bytes, 199_708_580)
        self.assertEqual(model.device_persistent_numeric_bytes, 15_159_204)
        self.assertEqual(model.device_source_phase_numeric_bytes, 292_650_788)
        self.assertEqual(model.device_query_phase_numeric_bytes, 445_235_284)
        self.assertEqual(model.device_adjoint_phase_numeric_bytes, 492_448_676)
        self.assertEqual(model.device_peak_numeric_bytes, 492_448_676)
        self.assertEqual(model.forbidden_dense_tensor_train_bytes, 221_323_520)
        self.assertTrue(all(model.admission_checks.values()))
        self.assertTrue(model.source_only_admitted)

    def test_safe_feature_envelope_is_separate_and_still_passes_fixed_bytes(self) -> None:
        fixture = fixture_capacity_model()
        envelope = safe_feature_envelope_model()
        self.assertEqual(envelope.source_state_ranks, (2_970,))
        self.assertEqual(envelope.feature_width, 2_971)
        self.assertGreater(
            envelope.device_peak_numeric_bytes,
            fixture.device_peak_numeric_bytes,
        )
        self.assertGreater(
            envelope.forbidden_dense_tensor_train_bytes,
            fixture.forbidden_dense_tensor_train_bytes,
        )
        self.assertEqual(envelope.host_persistent_numeric_bytes, 69_509_252)
        self.assertEqual(envelope.host_peak_numeric_bytes, 3_184_828_548)
        self.assertEqual(envelope.device_persistent_numeric_bytes, 69_509_252)
        self.assertEqual(envelope.device_source_phase_numeric_bytes, 4_751_674_876)
        self.assertEqual(envelope.device_query_phase_numeric_bytes, 7_102_336_812)
        self.assertEqual(envelope.device_adjoint_phase_numeric_bytes, 8_126_480_964)
        self.assertEqual(envelope.device_peak_numeric_bytes, 8_126_480_964)
        self.assertEqual(
            envelope.forbidden_dense_tensor_train_bytes,
            155_718_739_480,
        )
        self.assertTrue(all(envelope.admission_checks.values()))
        self.assertTrue(envelope.source_only_admitted)

    def test_work_keeps_cold_source_refresh_query_only_and_adjoint_distinct(self) -> None:
        model = fixture_capacity_model()
        geometry = model.geometry
        topology = model.topology_preparation_work
        cold = model.cold_forward_work
        source_refresh = model.source_seat_refresh_work
        query_refresh = model.query_only_refresh_work
        adjoint = model.adjoint_work
        self.assertEqual(cold, source_refresh)
        self.assertEqual(cold.source_pairing_record_visits, 733_055_400)
        self.assertEqual(
            cold.weighted_state_and_reach_accumulations,
            2 * 733_055_400,
        )
        self.assertEqual(
            cold.containment_scalar_additions,
            8_145_060 * 57 * 176,
        )
        self.assertEqual(
            cold.signed_query_scalar_additions,
            893_970 * 16 * 176,
        )
        self.assertEqual(query_refresh.source_occupancy_visits, 0)
        self.assertEqual(query_refresh.containment_scalar_additions, 0)
        self.assertEqual(
            query_refresh.signed_query_scalar_additions,
            cold.signed_query_scalar_additions,
        )
        self.assertEqual(
            adjoint.containment_scalar_additions,
            geometry.query_occupancies * 16 * 176,
        )
        self.assertEqual(
            adjoint.signed_source_scalar_additions,
            geometry.source_occupancies * 57 * 176,
        )
        self.assertEqual(
            adjoint.streamed_source_label_scalar_writes,
            733_055_400 * 176,
        )
        self.assertEqual(topology.binomial_table_cells, 46 * 7)
        self.assertEqual(topology.source_pairing_template_entries, 90 * 6)
        self.assertEqual(topology.query_pairing_template_entries, 6 * 4)
        self.assertEqual(topology.query_occupancy_visits, 148_995)
        self.assertEqual(topology.labeled_query_records_generated, 893_970)
        self.assertEqual(topology.labeled_query_numeric_field_writes, 3 * 893_970)

    def test_components_and_terms_scale_feature_arrays_and_work_exactly(self) -> None:
        base = fixture_capacity_model()
        wider = replace(
            base,
            automata=(base.automata[0], base.automata[0]),
            source_state_ranks=(175, 175),
            component_count=2,
        )
        self.assertEqual(wider.term_count, 2)
        self.assertEqual(wider.feature_width, 2 * ((175 + 1) + (175 + 1)))
        self.assertEqual(wider.payoff_state_width, 350)
        self.assertEqual(
            wider.forward_work.weighted_state_and_reach_accumulations,
            base.geometry.source_labeled_records * 2 * 2 * 2,
        )
        self.assertEqual(
            wider.forward_work.containment_scalar_additions,
            base.forward_work.containment_vector_updates * wider.feature_width,
        )
        self.assertGreater(
            wider.device_peak_numeric_bytes,
            base.device_peak_numeric_bytes,
        )

    def test_chunk_changes_only_scratch_not_semantics_or_persistent_storage(self) -> None:
        model = fixture_capacity_model()
        smaller = replace(
            model,
            source_chunk_occupancies=4_096,
            query_chunk_records=8_192,
        )
        self.assertEqual(model.forward_work, smaller.forward_work)
        self.assertEqual(model.adjoint_work, smaller.adjoint_work)
        self.assertEqual(
            model.host_persistent_numeric_bytes,
            smaller.host_persistent_numeric_bytes,
        )
        self.assertEqual(
            model.device_persistent_numeric_bytes,
            smaller.device_persistent_numeric_bytes,
        )
        self.assertLess(
            smaller.device_source_phase_numeric_bytes,
            model.device_source_phase_numeric_bytes,
        )
        self.assertLess(
            smaller.device_query_phase_numeric_bytes,
            model.device_query_phase_numeric_bytes,
        )
        self.assertLess(
            smaller.device_adjoint_phase_numeric_bytes,
            model.device_adjoint_phase_numeric_bytes,
        )

    def test_invalid_ranks_geometry_and_model_scope_fail_closed(self) -> None:
        with self.assertRaises(ValueError):
            combination_rank((1, 1), universe_size=5)
        with self.assertRaises(ValueError):
            combination_rank((0, 5), universe_size=5)
        with self.assertRaises(ValueError):
            combination_unrank(10, universe_size=5, cardinality=2)
        with self.assertRaises(ValueError):
            subset_table_index((0, 1, 2), universe_size=5, maximum_cardinality=2)
        with self.assertRaises(ValueError):
            OccupiedCardGeometry(available_cards=9)
        with self.assertRaises(ValueError):
            replace(fixture_capacity_model(), source_state_ranks=(174,))


if __name__ == "__main__":
    unittest.main()
