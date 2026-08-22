import unittest

import numpy as np

from pontius.continuation_public_tree_tensor import (
    ContinuationPublicTreeTensorEvaluator,
)
from pontius.h32_continuation_root_preflight import (
    _automaton_identity,
    checks_then_bet_prefix,
    continuation_identity,
    mutation_controls,
)
from pontius.leaf_adjoint_cfr import build_leaf_adjoint_terminal_automata
from pontius.public_policy_tt import information_schema_for_axes
from pontius.public_tree_tensor import PublicTreeTensorEvaluator
from pontius.river import parse_cards
from pontius.river_multiway import MultiwayRiverDeal, MultiwayRiverHoldem


def _game() -> MultiwayRiverHoldem:
    board = parse_cards("2c", "7d", "9h", "Js", "Qc")
    deal = MultiwayRiverDeal(
        (
            parse_cards("As", "Ad"),
            parse_cards("Ks", "Kd"),
            parse_cards("Ts", "Td"),
        )
    )
    return MultiwayRiverHoldem.from_joint_weights(
        board=board,
        pot=12.0,
        stacks=(30.0, 30.0, 30.0),
        bet_size=3.0,
        joint_weights={deal: 1.0},
    )


class ContinuationRootPreflightTests(unittest.TestCase):
    def test_checks_then_bet_prefix_is_exact(self) -> None:
        self.assertEqual(checks_then_bet_prefix(0), ((0, "bet"),))
        self.assertEqual(
            checks_then_bet_prefix(3),
            ((0, "check"), (1, "check"), (2, "check"), (3, "bet")),
        )

    def test_restricted_policy_payoff_and_automata_match_full_subtree(self) -> None:
        game = _game()
        full = PublicTreeTensorEvaluator(game)
        continuation = ContinuationPublicTreeTensorEvaluator(
            game, public_prefix=checks_then_bet_prefix(1)
        )
        hands = tuple(tuple(game.marginal_distribution(seat)) for seat in range(3))
        schema = information_schema_for_axes(full, hands)
        blueprint = {
            key: {action: 1.0 / len(actions) for action in actions}
            for key, actions in schema.items()
        }
        identity = continuation_identity(
            full,
            continuation,
            hands_by_player=hands,
            blueprint=blueprint,
        )
        self.assertEqual(identity["topology_mismatches"], 0)
        self.assertEqual(identity["information_key_mismatches"], 0)
        self.assertEqual(identity["terminal_key_mismatches"], 0)
        self.assertEqual(identity["maximum_terminal_payoff_error"], 0.0)
        self.assertLessEqual(
            identity["maximum_fixed_policy_subtree_utility_error"], 1e-15
        )
        self.assertFalse(identity["missing_blueprint_information_sets"])

        codes = tuple(np.arange(len(axis), dtype=np.int32) for axis in hands)
        full_automata = build_leaf_adjoint_terminal_automata(
            full, codes, pot=12.0, bet_size=3.0
        )
        continuation_automata = build_leaf_adjoint_terminal_automata(
            continuation, codes, pot=12.0, bet_size=3.0
        )
        automaton = _automaton_identity(full_automata, continuation_automata)
        self.assertEqual(automaton["missing_full_tree_groups"], 0)
        self.assertEqual(automaton["semantic_field_mismatches"], 0)
        self.assertEqual(automaton["maximum_terminal_winner_value_error"], 0.0)
        self.assertLess(
            automaton["continuation_numeric_bytes"],
            automaton["full_numeric_bytes"],
        )

    def test_mutations_are_rejected(self) -> None:
        control = mutation_controls(PublicTreeTensorEvaluator(_game()))
        self.assertTrue(control["wrong_actor_rejected"])
        self.assertTrue(control["terminal_prefix_rejected"])
        self.assertTrue(control["passed"])


if __name__ == "__main__":
    unittest.main()
