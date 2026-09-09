"""Replayed root, declared domain, capacity, per-hand totals, and the singleton reference."""

from __future__ import annotations

from fractions import Fraction
import math
import unittest

from pontius import eval_bridge as bridge
from pontius.blueprint_artifact.codec import decode_blueprint, encode_blueprint
from pontius.immutable_blueprint import BlueprintActionEntry, ImmutableBlueprintActionSource
from pontius.no_limit_betting import CHECK, BettingActionKind, raise_to
from pontius.river import make_hole, parse_cards

DEVELOPMENT = bridge.board_cards(("2c", "7d", "9h", "Js", "Qc"))
ROYAL = bridge.board_cards(("Ts", "Js", "Qs", "Ks", "As"))
SEED = "ab" * 32
N = bridge.VILLAIN_COUNT
BET = str(raise_to(2))


def artifact(key, action):
    source = ImmutableBlueprintActionSource(
        bridge.PLACEHOLDER_SOURCE_ID, (BlueprintActionEntry(key, action),))
    return encode_blueprint(source)


def reference_result(board, hero):
    root = bridge.replay_root()
    production = bridge.hand_totals(root, board, hero)
    reference = bridge.build_reference(root, board, hero)
    values = {str(action): bridge.forced_value(reference, action)
              for action in (CHECK, reference["bet"])}
    response_value, response_map = bridge.reference_best_response(reference)
    return production, bridge.validate_reference(
        production, values, response_value, response_map, reference["hero_key"])


class ReplayedRootTests(unittest.TestCase):
    def test_root_matches_the_accepted_prefix(self):
        root = bridge.replay_root()
        decision = root.legal_decision()
        bounds = decision.raise_bounds
        self.assertEqual((root.acting_seat, root.pot), (2, 4))
        self.assertEqual(root.total_contributions, (0, 2, 2, 0, 0, 0))
        self.assertEqual(tuple(root.folded), (True, False, False, True, True, True))
        self.assertEqual(decision.action_kinds,
                         (BettingActionKind.CHECK, BettingActionKind.RAISE))
        self.assertEqual((bounds.minimum_raise_to, bounds.maximum_raise_to), (2, 2))
        self.assertEqual(len(root.history), 11)
        self.assertIs(bridge.require_declared_root(root), root)
        self.assertEqual(bridge.bet_action(root), raise_to(2))
        document = bridge.prefix_document()
        self.assertEqual((len(document), document.count(None), document[0]), (14, 3, [3, "fold"]))

    def test_other_stack_depths_are_refused_everywhere_but_key_controls(self):
        hero = make_hole("2c", "3d")
        for stacks in (3, 6):
            root = bridge.replay_root(stacks=stacks)
            self.assertEqual(root.acting_seat, 2, stacks)
            for function in (bridge.require_declared_root, bridge.bet_action):
                with self.assertRaises(ValueError, msg=stacks):
                    function(root)
            with self.assertRaises(ValueError, msg=stacks):
                bridge.hand_totals(root, ROYAL, hero)
            with self.assertRaises(ValueError, msg=stacks):
                bridge.build_reference(root, ROYAL, hero)

    def test_universes_keys_and_board_order(self):
        root = bridge.replay_root()
        hands = bridge.hero_hands(DEVELOPMENT)
        self.assertEqual(len(hands), bridge.HERO_COUNT)
        self.assertEqual(len(bridge.villain_hands(DEVELOPMENT, hands[0])), N)
        keys = [bridge.root_key(root, DEVELOPMENT, hand) for hand in hands[:50]]
        self.assertEqual(len(set(keys)), 50)
        self.assertEqual(keys[0].board, DEVELOPMENT)
        self.assertEqual(len(bridge.hand_universe_digest(hands)), 64)
        with self.assertRaises(ValueError):
            bridge.board_cards(("Qc", "Js", "9h", "7d", "2c"))
        deeper = bridge.replay_root(stacks=6)
        self.assertNotEqual(bridge.root_key(deeper, DEVELOPMENT, hands[0]), keys[0])


class CapacityTests(unittest.TestCase):
    def test_placeholder_rows_are_conservative_and_monotone(self):
        root = bridge.replay_root()
        key = bridge.root_key(root, DEVELOPMENT, make_hole("As", "Ad"))
        self.assertEqual(len(artifact(key, CHECK)) - len(artifact(key, raise_to(2))), 3)
        hands = bridge.hero_hands(DEVELOPMENT)[:6]
        keys = [bridge.root_key(root, DEVELOPMENT, hand) for hand in hands]
        sizes = [len(bridge.placeholder_artifact(keys, count)) for count in range(7)]
        self.assertEqual(sizes, sorted(set(sizes)))

    def test_probe_reports_boundary_bytes_all_fit_and_one_row_failure(self):
        root = bridge.replay_root()
        hands = bridge.hero_hands(DEVELOPMENT)
        permutation = bridge.strength_blind_permutation(hands, SEED)
        self.assertEqual(permutation, bridge.strength_blind_permutation(hands, SEED))
        self.assertEqual(sorted(permutation), sorted(hands))
        few = permutation[:8]
        keys = [bridge.root_key(root, DEVELOPMENT, hand) for hand in few]
        cap = len(bridge.placeholder_artifact(keys, 3))
        report = bridge.capacity_probe(root, DEVELOPMENT, few, cap=cap)
        self.assertEqual((report["largest_fitting"], report["bytes_at_largest"]), (3, cap))
        self.assertGreater(report["bytes_at_next"], cap)
        self.assertEqual(set(report["boundary_encodings"]), {3, 4})
        decoded = decode_blueprint(report["boundary_encodings"][3])
        self.assertEqual({entry.key for entry in decoded.entries}, set(keys[:3]))
        self.assertFalse(report["all_fit"] or report["one_row_failure"])
        tiny = bridge.capacity_probe(root, DEVELOPMENT, few, cap=10)
        self.assertTrue(tiny["one_row_failure"])
        everything = bridge.capacity_probe(root, DEVELOPMENT, few, cap=10**9)
        self.assertTrue(everything["all_fit"] and everything["bytes_at_next"] is None)
        self.assertEqual(set(everything["boundary_encodings"]), {8})


class HandTotalTests(unittest.TestCase):
    def test_royal_board_ties_every_deal(self):
        totals = bridge.hand_totals(bridge.replay_root(), ROYAL, make_hole("2c", "3d"))
        self.assertEqual((totals["check_total"], totals["bet_total"], totals["ties"]), (0, 0, N))
        self.assertEqual(totals["action"], str(CHECK))
        self.assertEqual(totals["work"],
                         dict(villain_hands=N, settlements=2 * N, ranker_calls=N + 1))

    def test_development_hands_follow_the_settlement_identity(self):
        root = bridge.replay_root()
        for name in ("AsAd", "Td8d"):
            totals = bridge.hand_totals(root, DEVELOPMENT, make_hole(name[:2], name[2:]))
            self.assertEqual(totals["bet_total"], 2 * totals["check_total"])
            self.assertEqual(totals["check_total"], 2 * (totals["wins"] - totals["losses"]))
            self.assertEqual((totals["denominator"], totals["action"]), (N, BET), name)


class ReferenceTests(unittest.TestCase):
    def test_singleton_reference_on_the_royal_tie(self):
        production, result = reference_result(ROYAL, make_hole("2c", "3d"))
        self.assertTrue(result["passed"], result)
        self.assertEqual(result["validated_totals"], {str(CHECK): 0, BET: 0})
        self.assertIn(result["classification"], ("tie", "tie_reference_broke_differently"))

    def test_singleton_reference_on_a_nonzero_development_hand(self):
        production, result = reference_result(DEVELOPMENT, make_hole("As", "Ad"))
        self.assertTrue(result["passed"], result)
        self.assertEqual(result["classification"], "agree")
        self.assertGreater(production["check_total"], 0)
        self.assertEqual(result["validated_totals"],
                         {str(CHECK): production["check_total"], BET: production["bet_total"]})
        self.assertEqual(result["response_map"], {next(iter(result["response_map"])): BET})

    def test_reference_refuses_a_changed_domain(self):
        hero = make_hole("As", "Ad")
        with self.assertRaises(ValueError):
            bridge.build_reference(bridge.replay_root(), parse_cards("2c", "7d", "9h", "Js"), hero)

    def test_lattice_validation_arithmetic_fixtures(self):
        """Arithmetic fixtures for the comparison boundary; they impersonate no poker game."""
        bound = bridge.REFERENCE_BOUND
        residual = 3.122502256758253e-17
        self.assertEqual(bridge.lattice_integer(residual, N, bound), 0)
        self.assertEqual(bridge.lattice_integer(-residual, N, bound), 0)
        self.assertEqual(bridge.lattice_integer(1 / N, N, bound), 1)
        self.assertEqual(bridge.lattice_integer(-1 / N, N, bound), -1)
        for value in (0.5 / N, float(bound) * 3, math.nan, math.inf, 5.0, 1):
            self.assertIsNone(bridge.lattice_integer(value, N, bound), value)
        self.assertLess(2 * bound, Fraction(1, N))
        key = "hero"
        tie = dict(check_total=0, bet_total=0, denominator=N, action=str(CHECK), bet=BET)
        non_tie = dict(tie, check_total=2, bet_total=4, action=BET)
        near = {str(CHECK): 2 / N, BET: 4 / N}

        def check(production, values, value, action, extra_keys=()):
            response = {key: action, **{name: action for name in extra_keys}}
            return bridge.validate_reference(production, values, value, response, key)

        for sign in (1, -1):  # signed cancellation residuals on an exact production tie
            values = {str(CHECK): sign * residual, BET: 2 * sign * residual}
            for action in (str(CHECK), BET):
                outcome = check(tie, values, 2 * sign * residual, action)
                self.assertTrue(outcome["passed"], (sign, action, outcome))
                broke = action != str(CHECK)
                self.assertEqual(outcome["classification"],
                                 "tie_reference_broke_differently" if broke else "tie")
        for total, action in ((1, BET), (-1, str(CHECK))):  # smallest lattice gap, both signs
            gap = dict(tie, check_total=0, bet_total=total, action=action)
            outcome = check(gap, {str(CHECK): 0.0, BET: total / N}, max(0, total) / N, action)
            self.assertEqual((outcome["passed"], outcome["classification"]), (True, "agree"), total)
        self.assertFalse(check(tie, near, 4 / N, BET)["passed"])  # false production tie
        self.assertFalse(check(non_tie, {str(CHECK): 2 / N, BET: 6 / N}, 6 / N, BET)["passed"])
        self.assertFalse(check(dict(non_tie, action=str(CHECK)), near, 4 / N, BET)["passed"])
        self.assertEqual(check(non_tie, near, 4 / N, str(CHECK))["reason"],
                         "reference action disagrees on a validated non-tie")
        self.assertEqual(check(non_tie, near, 4 / N, BET)["classification"], "agree")
        self.assertFalse(check(non_tie, near, 4 / N, BET, extra_keys=("x",))["passed"])
        self.assertFalse(check(non_tie, {str(CHECK): 2 / N, BET: math.nan}, 4 / N, BET)["passed"])


if __name__ == "__main__":
    unittest.main()
