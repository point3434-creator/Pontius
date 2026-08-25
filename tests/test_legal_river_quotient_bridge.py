from __future__ import annotations

import ast
from dataclasses import replace
from fractions import Fraction
from hashlib import sha256
from math import fsum
import os
from pathlib import Path
import subprocess
import sys
import unittest

import numpy as np

from pontius.factor_tt_contraction import FactorTTBeliefWorkspace
from pontius.full_width_belief import ExactRangeWeight, FullWidthOneSeatBelief
from pontius.heterogeneous_leaf_contraction import (
    HeterogeneousLeafTerm,
    contract_heterogeneous_leaf_terms,
)
from pontius.legal_river_quotient_bridge import (
    PREREGISTERED_CONFIG_SHA256,
    PreregisteredLegalRiverContext,
    build_preregistered_legal_river_context,
    compile_legal_river_quotient_bridge,
    compile_reduced_legal_river_quotient_bridge,
    compile_warm_inputs,
    exact_float_rows,
    load_preregistered_bridge_config,
)
from pontius.no_limit_betting import BettingActionKind, BettingStreet, TerminalReason
from pontius.open_mode_factor_tt import (
    BidirectionalFactorTTTopology,
    OpenModeFactorTTWorkspace,
)
from pontius.open_mode_showdown import (
    _automaton_half_vectors,
    contract_open_mode_showdown_batch,
)
from pontius.river import evaluate_seven
from pontius.sparse_incidence_open_mode import SparseBidirectionalIncidence


_ROOT = Path(__file__).parents[1]
_SOURCE = _ROOT / "src/pontius/legal_river_quotient_bridge.py"
_DEPENDENCIES = {
    "adr0384": _ROOT
    / "docs/decisions/ADR-0384-retain-the-passing-literal-45-quotient-target.md",
    "full_width_belief": _ROOT / "src/pontius/full_width_belief.py",
    "full_width_reference_policy": _ROOT
    / "src/pontius/full_width_reference_policy.py",
    "gpu_occupied_card_quotient": _ROOT
    / "src/pontius/gpu_occupied_card_quotient.py",
    "heterogeneous_leaf_contraction": _ROOT
    / "src/pontius/heterogeneous_leaf_contraction.py",
    "holdem_cards": _ROOT / "src/pontius/holdem_cards.py",
    "legal_decision_spine_v2": _ROOT
    / "src/pontius/legal_decision_spine_v2.py",
    "no_limit_betting": _ROOT / "src/pontius/no_limit_betting.py",
    "occupied_card_quotient": _ROOT / "src/pontius/occupied_card_quotient.py",
    "open_mode_showdown": _ROOT / "src/pontius/open_mode_showdown.py",
    "structured_showdown_automaton": _ROOT
    / "src/pontius/structured_showdown_automaton.py",
}


def _canonical_sha256(path: Path) -> str:
    return sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _workspace(reduced):
    base = FactorTTBeliefWorkspace.compile(
        reduced.factor_topology,
        reduced.factorized_belief,
        query_chunk_records=64,
    )
    bidirectional = BidirectionalFactorTTTopology.compile(reduced.factor_topology)
    return OpenModeFactorTTWorkspace.compile(bidirectional, base)


def _open_value(reduced):
    workspace = _workspace(reduced)
    result = contract_open_mode_showdown_batch(
        workspace,
        (reduced.automaton,),
        target_seats=(3,),
        maximum_feature_width_per_batch=256,
    )
    return workspace, result.for_automaton(0).for_seat(3)


class LegalRiverQuotientBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = load_preregistered_bridge_config()
        cls.context = build_preregistered_legal_river_context()
        cls.bridge = compile_legal_river_quotient_bridge(cls.context)
        cls.reduced = compile_reduced_legal_river_quotient_bridge(
            cls.bridge,
            cls.config["reduced_control"]["opponent_hands_by_axis"],
        )

    def test_config_dependencies_and_exact_legal_context_are_bound(self) -> None:
        self.assertEqual(
            _canonical_sha256(
                _ROOT / "experiments/configs/legal-river-quotient-bridge-v1.json"
            ),
            PREREGISTERED_CONFIG_SHA256,
        )
        expected_sources = self.config["expected_sources"]
        self.assertEqual(set(expected_sources), set(_DEPENDENCIES))
        for label, path in _DEPENDENCIES.items():
            self.assertEqual(_canonical_sha256(path), expected_sources[label])

        context = self.config["context"]
        cards = self.context.cards
        betting = self.context.betting
        belief = self.context.belief
        self.assertEqual(cards.public_digest, context["expected_card_state_sha256"])
        self.assertEqual(belief.digest, context["expected_belief_sha256"])
        self.assertEqual(self.context.policy_digest, context["expected_policy_sha256"])
        self.assertEqual(len(belief.likelihood_digests), 20)
        self.assertEqual(belief.opponent_hand_counts, (990,) * 5)
        self.assertEqual(betting.acting_seat, 0)
        self.assertEqual(betting.pot, 60)
        self.assertEqual(betting.stacks, (190,) * 6)
        self.assertEqual(betting.total_contributions, (10,) * 6)
        self.assertEqual(betting.street_contributions, (0,) * 6)
        self.assertEqual(betting.pending_seats, (0,))
        self.assertEqual(tuple(pot.amount for pot in betting.side_pots()), (60,))
        decision = betting.legal_decision()
        self.assertEqual(
            decision.action_kinds,
            (BettingActionKind.CHECK, BettingActionKind.RAISE),
        )
        assert decision.raise_bounds is not None
        self.assertEqual(
            (
                decision.raise_bounds.minimum_raise_to,
                decision.raise_bounds.maximum_raise_to,
            ),
            (10, 190),
        )

    def test_full_width_compiler_is_structural_readonly_and_owned(self) -> None:
        bridge = self.bridge
        fixture = bridge.fixture
        self.assertEqual(
            bridge.bridge_digest,
            "bfe0f1e768bf323fa7d8036ef05176d5e0373f712e4875dcf76eabb96532a702",
        )
        self.assertEqual(
            bridge.topology_digest,
            "b499a4e92a739ea2bdf1d64b1653d5c652b707e5b88d8959db7f17f82f8761a9",
        )
        self.assertEqual(bridge.axis_table_seats, (1, 2, 3, 0, 4, 5))
        self.assertEqual(bridge.source_axes, (0, 1, 2))
        self.assertEqual(bridge.query_axes, (3, 4, 5))
        self.assertEqual(bridge.target_axis, 3)
        self.assertEqual(bridge.factorized_belief.hand_counts, (990, 990, 990, 1, 990, 990))
        self.assertEqual(len(bridge.local_to_physical_cards), 45)
        self.assertEqual(len(bridge.physical_hands), 990)
        self.assertEqual(fixture.available_cards, 45)
        self.assertEqual(fixture.query_masks.shape, (893_970,))
        self.assertEqual(fixture.query_hand_indices.shape, (893_970, 2))
        self.assertEqual(fixture.source_pair_positions.shape, (90, 6))
        self.assertEqual(fixture.source_rank, 175)
        self.assertEqual(fixture.feature_width, 176)
        self.assertEqual(fixture.automaton.sunk_value, -10.0)
        self.assertEqual(fixture.automaton.final_pot, 60.0)
        self.assertEqual(bridge.terminal_betting.terminal_reason, TerminalReason.SHOWDOWN)
        unique_masks, mask_counts = np.unique(fixture.query_masks, return_counts=True)
        self.assertEqual(len(unique_masks), 148_995)
        self.assertTrue(np.all(mask_counts == 6))
        local_hands = np.asarray(fixture.hands, dtype=np.uint64)
        query_cards = local_hands[fixture.query_hand_indices].reshape(-1, 4)
        reconstructed_masks = np.bitwise_or.reduce(
            np.left_shift(np.uint64(1), query_cards),
            axis=1,
        )
        self.assertTrue(np.array_equal(reconstructed_masks, fixture.query_masks))
        source_pairings = tuple(map(tuple, fixture.source_pair_positions.tolist()))
        self.assertEqual(len(set(source_pairings)), 90)
        for pairing in source_pairings:
            self.assertEqual(tuple(sorted(pairing)), tuple(range(6)))
            self.assertLess(pairing[0], pairing[1])
            self.assertLess(pairing[2], pairing[3])
            self.assertLess(pairing[4], pairing[5])
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
            self.assertTrue(values.flags.c_contiguous)
            self.assertFalse(values.flags.writeable)

        ownership = bridge.ownership
        self.assertEqual(ownership.consumer_resident_numeric_bytes, 15_888_996)
        self.assertEqual(ownership.retained_host_validation_numeric_bytes, 84_972)
        self.assertEqual(
            dict(ownership.retained_host_validation_entries),
            {
                "local_to_physical_card_entries": 45,
                "physical_hand_records": 990,
            },
        )
        self.assertEqual(ownership.warm_mutable_numeric_bytes, 79_216)
        self.assertEqual(
            dict(ownership.preparation_work),
            {
                "physical_to_local_card_entries": 45,
                "pair_to_hand_writes": 1_980,
                "source_pairing_template_entries": 540,
                "query_occupancy_visits": 148_995,
                "labeled_query_records_generated": 893_970,
                "strength_evaluations": 4_951,
            },
        )
        self.assertFalse(hasattr(bridge, "numerator"))
        self.assertFalse(hasattr(bridge, "action"))

    def test_reduced_quotient_matches_literal_leaf_adjoint_and_legal_chips(self) -> None:
        reduced = self.reduced
        gates = self.config["reduced_control"]
        self.assertEqual(reduced.factorized_belief.hand_counts, (4, 4, 4, 1, 4, 4))
        self.assertEqual(reduced.factorized_belief.cartesian_assignments, 1_024)
        self.assertEqual(len(reduced.compatible_assignments), 6)
        self.assertEqual(reduced.factor_topology.left.records, 16)
        self.assertEqual(reduced.factor_topology.right.records, 6)
        self.assertEqual(len(reduced.quotient_topology.source_occupancy_masks), 15)

        workspace, current = _open_value(reduced)
        left_vectors, right_vectors = _automaton_half_vectors(
            reduced.automaton,
            workspace,
        )
        components = workspace.component_count
        rank = left_vectors.shape[1]
        source_products = workspace.base.left_component_products
        source_values = (
            source_products[:, :, None] * left_vectors[:, None, :]
        ).reshape(reduced.factor_topology.left.records, components * rank)
        source_features = np.ascontiguousarray(
            np.concatenate((source_products, source_values), axis=1),
            dtype=np.float64,
        )
        exact_source = exact_float_rows(source_features)
        quotient_result = reduced.quotient_topology.apply_exact(exact_source)
        literal = tuple(
            tuple(
                sum(
                    (
                        row[feature]
                        for mask, row in zip(
                            reduced.quotient_topology.source_record_masks,
                            exact_source,
                            strict=True,
                        )
                        if mask & query_mask == 0
                    ),
                    Fraction(0),
                )
                for feature in range(source_features.shape[1])
            )
            for query_mask in reduced.quotient_topology.query_record_masks
        )
        self.assertEqual(quotient_result.query_rows, literal)

        compatible = np.asarray(
            [[float(value) for value in row] for row in quotient_result.query_rows],
            dtype=np.float64,
        )
        query_products = workspace.base.right_component_products
        compatible_reach = compatible[:, :components]
        compatible_values = compatible[:, components:].reshape(
            reduced.factor_topology.right.records,
            components,
            rank,
        )
        numerator_records = np.einsum(
            "k,qk,qkr,qr->q",
            workspace.base.mixture_weights,
            query_products,
            compatible_values,
            right_vectors,
            optimize=True,
        )
        reach_records = np.einsum(
            "k,qk,qk->q",
            workspace.base.mixture_weights,
            query_products,
            compatible_reach,
            optimize=True,
        )
        target_depth = reduced.factor_topology.right.seats.index(3)
        target_indices = reduced.factor_topology.right.indices[:, target_depth]
        quotient_numerators = np.bincount(
            target_indices,
            weights=numerator_records,
            minlength=1,
        )
        quotient_reaches = np.bincount(
            target_indices,
            weights=reach_records,
            minlength=1,
        )
        maximum_open_error = max(
            float(np.max(np.abs(quotient_numerators - current.unnormalized_numerators))),
            float(np.max(np.abs(quotient_reaches - current.unnormalized_reaches))),
        )
        self.assertLessEqual(maximum_open_error, gates["maximum_open_mode_absolute_error"])

        sparse = SparseBidirectionalIncidence.compile(workspace)
        term = HeterogeneousLeafTerm(
            key=0,
            automaton=reduced.automaton,
            mode_factors=tuple(
                np.ones(width, dtype=np.float64)
                for width in reduced.factorized_belief.hand_counts
            ),
        )
        leaf = contract_heterogeneous_leaf_terms(
            workspace,
            sparse,
            (term,),
            target_seat=3,
            maximum_feature_width_per_batch=256,
        ).for_key(0)
        maximum_leaf_error = max(
            float(np.max(np.abs(quotient_numerators - leaf.unnormalized_numerators))),
            float(np.max(np.abs(quotient_reaches - leaf.unnormalized_reaches))),
            float(np.max(np.abs(current.conditional_values - leaf.conditional_values))),
        )
        self.assertLessEqual(
            maximum_leaf_error,
            gates["maximum_leaf_adjoint_absolute_error"],
        )

        covectors = tuple(
            tuple(
                Fraction((query + 2) * (feature + 3), 97)
                for feature in range(source_features.shape[1])
            )
            for query in range(reduced.factor_topology.right.records)
        )
        adjoint = reduced.quotient_topology.apply_adjoint_exact(covectors)
        forward_dot = sum(
            (
                quotient_result.query_rows[query][feature]
                * covectors[query][feature]
                for query in range(len(covectors))
                for feature in range(source_features.shape[1])
            ),
            Fraction(0),
        )
        transpose_dot = sum(
            (
                exact_source[source][feature] * adjoint[source][feature]
                for source in range(len(exact_source))
                for feature in range(source_features.shape[1])
            ),
            Fraction(0),
        )
        self.assertEqual(forward_dot, transpose_dot)

        materialized = reduced.factorized_belief.materialize()
        legal_values = []
        maximum_legal_settlement_error = 0.0
        automaton_values = reduced.automaton.evaluate_assignments(
            materialized.assignments
        )
        for assignment, automaton_value in zip(
            materialized.assignments,
            automaton_values,
            strict=True,
        ):
            strengths = [None] * 6
            for logical_axis, table_seat in enumerate(reduced.axis_table_seats):
                hand = reduced.physical_hands_by_axis[logical_axis][
                    assignment[logical_axis]
                ]
                strengths[table_seat] = evaluate_seven((*self.bridge.cards.board, *hand))
            settlement = self.bridge.terminal_betting.settle(strengths)
            legal_value = settlement.net_returns[0]
            legal_values.append(float(legal_value))
            maximum_legal_settlement_error = max(
                maximum_legal_settlement_error,
                abs(float(legal_value) - float(automaton_value)),
            )
        self.assertLessEqual(
            maximum_legal_settlement_error,
            gates["maximum_legal_settlement_error_chips"],
        )
        dense_value = fsum(
            probability * value
            for probability, value in zip(
                materialized.probabilities,
                legal_values,
                strict=True,
            )
        )
        self.assertLessEqual(
            abs(dense_value - float(current.conditional_values[0])),
            gates["maximum_open_mode_absolute_error"],
        )

    def test_warm_rebinding_changes_only_named_fields(self) -> None:
        belief = self.bridge.belief
        weights = list(belief.weights_by_opponent)
        changed = []
        for index, weight in enumerate(weights[0]):
            multiplier = 2 if index % 7 == 0 else 1
            changed.append(
                ExactRangeWeight(weight.numerator * multiplier, weight.denominator)
            )
        weights[0] = tuple(changed)
        updated = replace(belief, weights_by_opponent=tuple(weights))
        warm = compile_warm_inputs(self.bridge, updated)
        self.assertEqual(warm.topology_digest, self.bridge.topology_digest)
        self.assertEqual(warm.automaton_digest, self.bridge.fixture.automaton.digest)
        self.assertNotEqual(warm.belief_digest, belief.digest)
        self.assertFalse(np.array_equal(warm.unary_weights, self.bridge.fixture.unary_weights))
        self.assertTrue(np.array_equal(warm.mode_factors, self.bridge.fixture.mode_factors))
        self.assertFalse(warm.unary_weights.flags.writeable)
        self.assertFalse(warm.mode_factors.flags.writeable)

        path_factors = [
            np.ones(width, dtype=np.float64)
            for width in self.bridge.factorized_belief.hand_counts
        ]
        path_factors[0][0] = 0.5
        path_factors[3][0] = 0.25
        rebound_path = compile_warm_inputs(
            self.bridge,
            belief,
            mode_factors_by_axis=path_factors,
        )
        self.assertEqual(rebound_path.topology_digest, self.bridge.topology_digest)
        self.assertTrue(
            np.array_equal(
                rebound_path.unary_weights,
                self.bridge.fixture.unary_weights,
            )
        )
        self.assertFalse(
            np.array_equal(
                rebound_path.mode_factors,
                self.bridge.fixture.mode_factors,
            )
        )
        self.assertEqual(rebound_path.mode_factors[0, 0], 0.5)
        self.assertEqual(rebound_path.mode_factors[0, 2_970], 0.25)

        with self.assertRaisesRegex(ValueError, "exact visible-card domain"):
            replace(updated, hand_axis=tuple(reversed(updated.hand_axis)))

        changed_board = replace(
            self.bridge.cards,
            board=(*self.bridge.cards.board[:-1], self.bridge.local_to_physical_cards[0]),
        )
        stale = FullWidthOneSeatBelief.uniform(changed_board)
        with self.assertRaisesRegex(ValueError, "stale card state"):
            compile_warm_inputs(self.bridge, stale)

        changed_masks = self.bridge.fixture.query_masks.copy()
        changed_masks[0] ^= np.uint64(1)
        changed_masks.flags.writeable = False
        changed_topology = replace(
            self.bridge,
            fixture=replace(self.bridge.fixture, query_masks=changed_masks),
        )
        with self.assertRaisesRegex(ValueError, "topology digest"):
            compile_warm_inputs(changed_topology, updated)

        changed_terminal = self.bridge.fixture.automaton.terminal_winner_values.copy()
        changed_terminal[0, 0] += 1.0
        changed_terminal.flags.writeable = False
        changed_automaton = replace(
            self.bridge.fixture.automaton,
            terminal_winner_values=changed_terminal,
        )
        changed_semantics = replace(
            self.bridge,
            fixture=replace(self.bridge.fixture, automaton=changed_automaton),
        )
        with self.assertRaisesRegex(ValueError, "automaton identity"):
            compile_warm_inputs(changed_semantics, updated)

    def test_source_seat_permutation_is_semantic_only_when_data_moves_with_it(self) -> None:
        local_axes = self.config["reduced_control"]["opponent_hands_by_axis"]
        permuted_mapping = (2, 1, 3, 0, 4, 5)
        permuted_bridge = compile_legal_river_quotient_bridge(
            self.context,
            axis_table_seats=permuted_mapping,
        )
        paired_axes = (
            local_axes[1],
            local_axes[0],
            local_axes[2],
            local_axes[3],
            local_axes[4],
        )
        paired = compile_reduced_legal_river_quotient_bridge(
            permuted_bridge,
            paired_axes,
        )
        unpaired = compile_reduced_legal_river_quotient_bridge(
            permuted_bridge,
            local_axes,
        )
        _, baseline_value = _open_value(self.reduced)
        _, paired_value = _open_value(paired)
        _, unpaired_value = _open_value(unpaired)
        tolerance = self.config["reduced_control"]["maximum_open_mode_absolute_error"]
        for baseline, observed in (
            (baseline_value.unnormalized_numerators, paired_value.unnormalized_numerators),
            (baseline_value.unnormalized_reaches, paired_value.unnormalized_reaches),
            (baseline_value.conditional_values, paired_value.conditional_values),
        ):
            self.assertLessEqual(float(np.max(np.abs(baseline - observed))), tolerance)
        self.assertGreater(
            float(
                np.max(
                    np.abs(
                        baseline_value.conditional_values
                        - unpaired_value.conditional_values
                    )
                )
            ),
            tolerance,
        )

    def test_semantic_adversaries_reject_before_numerical_use(self) -> None:
        context = self.context
        with self.assertRaisesRegex(ValueError, "target"):
            compile_legal_river_quotient_bridge(
                context,
                axis_table_seats=(0, 1, 2, 3, 4, 5),
            )

        nonterminal = replace(
            context.betting,
            pending_seats=(0, 1),
            round_complete=False,
        )
        with self.assertRaisesRegex(ValueError, "terminal showdown"):
            compile_legal_river_quotient_bridge(
                replace(context, betting=nonterminal)
            )

        turn_cards = replace(
            context.cards,
            street=BettingStreet.TURN,
            board=context.cards.board[:-1],
        )
        with self.assertRaisesRegex(ValueError, "on the river"):
            compile_legal_river_quotient_bridge(
                replace(
                    context,
                    cards=turn_cards,
                    belief=FullWidthOneSeatBelief.uniform(turn_cards),
                )
            )

        nonacting = replace(context.betting, pending_seats=(1,))
        with self.assertRaisesRegex(ValueError, "controlled seat is not acting"):
            compile_legal_river_quotient_bridge(
                replace(context, betting=nonacting)
            )

        folded = replace(
            context.betting,
            folded=(False, True, False, False, False, False),
        )
        with self.assertRaisesRegex(ValueError, "six-way showdown"):
            compile_legal_river_quotient_bridge(
                replace(context, betting=folded)
            )

        unequal = replace(
            context.betting,
            stacks=(195, 189, 189, 189, 189, 189),
            total_contributions=(5, 11, 11, 11, 11, 11),
        )
        with self.assertRaisesRegex(ValueError, "equal sunk"):
            compile_legal_river_quotient_bridge(
                replace(context, betting=unequal)
            )

        odd_chip = replace(
            context.betting,
            stacks=(198,) * 6,
            total_contributions=(2,) * 6,
        )
        with self.assertRaisesRegex(ValueError, "odd-chip"):
            compile_legal_river_quotient_bridge(
                replace(context, betting=odd_chip)
            )

        stale_policy = PreregisteredLegalRiverContext(
            cards=context.cards,
            betting=context.betting,
            belief=context.belief,
            policy_digest="0" * 64,
        )
        with self.assertRaisesRegex(ValueError, "provenance"):
            compile_legal_river_quotient_bridge(stale_policy)

        uniform = FullWidthOneSeatBelief.uniform(context.cards)
        with self.assertRaisesRegex(ValueError, "provenance"):
            compile_legal_river_quotient_bridge(
                replace(context, belief=uniform)
            )

        with self.assertRaisesRegex(ValueError, "exact visible-card domain"):
            replace(
                context.belief,
                hand_axis=tuple(reversed(context.belief.hand_axis)),
            )

        with self.assertRaisesRegex(ValueError, "invalid local card"):
            local_axes = self.config["reduced_control"]["opponent_hands_by_axis"]
            malformed = [list(map(list, axis)) for axis in local_axes]
            malformed[0][0] = [0, 45]
            compile_reduced_legal_river_quotient_bridge(self.bridge, malformed)

        with self.assertRaisesRegex(ValueError, "nonempty and unique"):
            aliased = [list(map(list, axis)) for axis in local_axes]
            aliased[0][1] = aliased[0][0]
            compile_reduced_legal_river_quotient_bridge(self.bridge, aliased)

        with self.assertRaisesRegex(ValueError, "frozen h4 widths"):
            omitted = [list(map(list, axis)) for axis in local_axes]
            omitted[0].pop()
            compile_reduced_legal_river_quotient_bridge(self.bridge, omitted)

    def test_source_import_and_full_compile_leave_cupy_and_owner_absent(self) -> None:
        tree = ast.parse(_SOURCE.read_text(encoding="utf-8"))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                imported.add(node.module)
        self.assertNotIn("cupy", imported)
        self.assertFalse(
            any("literal_45_quotient_target" in name for name in imported)
        )

        script = (
            "import sys; "
            "from pontius.gpu_occupied_card_quotient import cupy_import_call_count; "
            "from pontius.legal_river_quotient_bridge import "
            "build_preregistered_legal_river_context, compile_legal_river_quotient_bridge; "
            "c=build_preregistered_legal_river_context(); "
            "b=compile_legal_river_quotient_bridge(c); "
            "print(int('cupy' in sys.modules), cupy_import_call_count(), "
            "int('pontius.literal_45_quotient_target' in sys.modules), "
            "b.fixture.query_masks.size)"
        )
        environment = os.environ.copy()
        environment["PYTHONPATH"] = os.pathsep.join(
            (str(_ROOT / "src"), str(_ROOT))
        )
        completed = subprocess.run(
            (sys.executable, "-B", "-c", script),
            cwd=_ROOT,
            env=environment,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stdout.strip(), "0 0 0 893970")


if __name__ == "__main__":
    unittest.main()
