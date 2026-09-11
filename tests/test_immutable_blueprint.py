from __future__ import annotations

import json
import unittest
from hashlib import sha256
from unittest.mock import patch
from dataclasses import fields, replace

from pontius.holdem_cards import OneSeatCardState, make_hole, parse_cards
from pontius.immutable_blueprint import (
    BlueprintActionEntry,
    BlueprintDecisionKey,
    ImmutableBlueprintActionSource,
)
from pontius.no_limit_betting import (
    CALL,
    CHECK,
    FOLD,
    BettingAction,
    BettingActionKind,
    BettingStreet,
    NoLimitBettingState,
    raise_to,
)


def _preflop_context() -> tuple[
    OneSeatCardState,
    NoLimitBettingState,
    BlueprintDecisionKey,
]:
    cards = OneSeatCardState.preflop(
        controlled_seat=3,
        private_hand=make_hole("Ks", "Td"),
    )
    betting = NoLimitBettingState.six_max_100bb(button=0)
    key = BlueprintDecisionKey.from_state(
        cards=cards,
        betting=betting,
        decision=betting.legal_decision(),
    )
    return cards, betting, key


def _flop_context() -> tuple[
    OneSeatCardState,
    NoLimitBettingState,
    BlueprintDecisionKey,
]:
    cards, betting, _ = _preflop_context()
    while not betting.round_complete:
        decision = betting.legal_decision()
        betting = betting.apply_action(CALL if decision.can_call else CHECK)
    betting = betting.advance_street()
    betting = betting.apply_action(CHECK).apply_action(CHECK)
    cards = cards.advance_to(
        BettingStreet.FLOP,
        parse_cards("2c", "7d", "9h"),
    )
    key = BlueprintDecisionKey.from_state(
        cards=cards,
        betting=betting,
        decision=betting.legal_decision(),
    )
    return cards, betting, key


class ImmutableBlueprintTests(unittest.TestCase):
    def test_repeated_identity_reads_do_not_repeat_serialization(self):
        _, _, key = _preflop_context()
        source = ImmutableBlueprintActionSource("cached", (BlueprintActionEntry(key, CALL),))
        expected_key = sha256(key.canonical_bytes()).hexdigest()
        expected_source = sha256(source.canonical_bytes()).hexdigest()
        self.assertEqual((key.digest, source.digest), (expected_key, expected_source))
        with patch("pontius.immutable_blueprint.json.dumps", side_effect=AssertionError(
                "identity reserialized after first read")):
            self.assertEqual((key.digest, source.digest), (expected_key, expected_source))

    def test_admission_rebuilds_identity_after_caller_cache_poisoning(self):
        from pontius.decision_provider.model import own_value
        from pontius.blueprint_preparation.lookup import PreparedBlueprint
        from pontius.v0a.runtime import _admit_blueprint

        cards, betting, key = _preflop_context()
        source = ImmutableBlueprintActionSource("admitted", (BlueprintActionEntry(key, CALL),))
        original = source.digest
        # Cache state is not authority: valid field changes must be re-admitted.
        object.__setattr__(key, "button", 1)
        fresh_key = replace(key)
        fresh = replace(source, entries=(BlueprintActionEntry(fresh_key, CALL),))
        expected = sha256(fresh.canonical_bytes()).hexdigest()
        self.assertNotEqual(expected, original)
        for admit in (own_value, _admit_blueprint, PreparedBlueprint):
            with self.subTest(admit=admit.__name__):
                self.assertEqual(admit(source).digest, expected)

    def test_replace_recomputes_cached_identity_and_preserves_value_equality(self):
        _, _, key = _preflop_context()
        source = ImmutableBlueprintActionSource("replace", (BlueprintActionEntry(key, CALL),))
        original = source.digest
        copy = replace(source)
        self.assertEqual(source, copy)
        self.assertEqual(hash(source), hash(copy))
        self.assertEqual(copy.digest, original)
        changed = replace(source, source_id="changed")
        self.assertNotEqual(changed.digest, original)
        changed_key = replace(key, button=1)
        self.assertEqual(changed_key.digest, sha256(changed_key.canonical_bytes()).hexdigest())
        self.assertNotEqual(changed_key.digest, key.digest)

    def test_admission_ignores_forged_derived_slots(self):
        from pontius.decision_provider.model import own_value
        from pontius.blueprint_preparation.lookup import PreparedBlueprint
        from pontius.v0a.runtime import _admit_blueprint

        _, _, key = _preflop_context()
        source = ImmutableBlueprintActionSource("forged-cache", (BlueprintActionEntry(key, CALL),))
        expected = source.digest
        object.__setattr__(key, "_cached_digest", object())
        object.__setattr__(source, "_cached_digest", object())
        for admit in (own_value, _admit_blueprint, PreparedBlueprint):
            with self.subTest(admit=admit.__name__):
                self.assertEqual(admit(source).digest, expected)

    def test_copy_pickle_and_dataclass_views_do_not_depend_on_cache_state(self):
        from copy import copy, deepcopy
        import pickle

        _, _, key = _preflop_context()
        source = ImmutableBlueprintActionSource("copy-cache", (BlueprintActionEntry(key, CALL),))
        for value in (key, source):
            before = repr(value), hash(value), tuple(f.name for f in fields(value))
            expected = value.digest
            self.assertEqual(before, (repr(value), hash(value),
                                      tuple(f.name for f in fields(value))))
            self.assertNotIn("_cached_digest", before[2])
            for clone in (copy(value), deepcopy(value), pickle.loads(pickle.dumps(value))):
                self.assertEqual(clone, value)
                self.assertEqual(clone.digest, expected)
                self.assertEqual(clone.canonical_bytes(), value.canonical_bytes())

    def test_empty_table_has_deliberately_weak_total_passive_rule(self) -> None:
        source = ImmutableBlueprintActionSource("empty-reference-v1")
        cards, betting, _ = _preflop_context()
        preflop = source.action_for(
            cards=cards,
            betting=betting,
            decision=betting.legal_decision(),
        )
        self.assertEqual(preflop.action, CALL)
        self.assertFalse(preflop.table_hit)

        cards, betting, _ = _flop_context()
        flop = source.action_for(
            cards=cards,
            betting=betting,
            decision=betting.legal_decision(),
        )
        self.assertEqual(flop.action, CHECK)
        self.assertFalse(flop.table_hit)

    def test_exact_table_can_represent_every_semantic_action_and_raise_amount(self) -> None:
        pre_cards, pre_betting, pre_key = _preflop_context()
        for action in (FOLD, CALL, raise_to(4), raise_to(200)):
            with self.subTest(action=action):
                source = ImmutableBlueprintActionSource(
                    source_id=f"preflop-{action}",
                    entries=(BlueprintActionEntry(pre_key, action),),
                )
                selection = source.action_for(
                    cards=pre_cards,
                    betting=pre_betting,
                    decision=pre_betting.legal_decision(),
                )
                self.assertTrue(selection.table_hit)
                self.assertEqual(selection.action, action)
                self.assertEqual(selection.source_digest, source.digest)

        flop_cards, flop_betting, flop_key = _flop_context()
        source = ImmutableBlueprintActionSource(
            "explicit-check",
            (BlueprintActionEntry(flop_key, CHECK),),
        )
        selection = source.action_for(
            cards=flop_cards,
            betting=flop_betting,
            decision=flop_betting.legal_decision(),
        )
        self.assertTrue(selection.table_hit)
        self.assertEqual(selection.action, CHECK)

    def test_illegal_frozen_entries_fail_closed_instead_of_becoming_passive(self) -> None:
        cards, betting, key = _preflop_context()
        for illegal in (CHECK, raise_to(3), raise_to(201)):
            with self.subTest(action=illegal):
                source = ImmutableBlueprintActionSource(
                    "illegal-entry",
                    (BlueprintActionEntry(key, illegal),),
                )
                with self.assertRaisesRegex(ValueError, "immutable blueprint"):
                    source.action_for(
                        cards=cards,
                        betting=betting,
                        decision=betting.legal_decision(),
                    )

    def test_source_is_immutable_digest_bound_and_order_independent(self) -> None:
        _, _, pre_key = _preflop_context()
        _, _, flop_key = _flop_context()
        first = BlueprintActionEntry(pre_key, CALL)
        second = BlueprintActionEntry(flop_key, CHECK)
        source = ImmutableBlueprintActionSource("ordered", (first, second))
        reordered = ImmutableBlueprintActionSource("ordered", (second, first))
        changed = ImmutableBlueprintActionSource(
            "ordered",
            (first, BlueprintActionEntry(flop_key, FOLD)),
        )
        self.assertEqual(source.digest, reordered.digest)
        self.assertEqual(source.canonical_bytes(), reordered.canonical_bytes())
        self.assertNotEqual(source.digest, changed.digest)
        with self.assertRaisesRegex(TypeError, "immutable tuple"):
            ImmutableBlueprintActionSource(  # type: ignore[arg-type]
                "mutable",
                [first],
            )
        with self.assertRaisesRegex(ValueError, "duplicate"):
            ImmutableBlueprintActionSource("duplicate", (first, first))

    def test_decision_key_is_future_and_opponent_private_blind(self) -> None:
        _, _, key = _preflop_context()
        names = {field.name for field in fields(BlueprintDecisionKey)}
        forbidden_fragments = ("opponent", "future", "runout", "deal")
        self.assertTrue(
            all(
                fragment not in name
                for fragment in forbidden_fragments
                for name in names
            )
        )
        payload = json.loads(key.canonical_bytes())
        self.assertEqual(payload["private_hand"], list(key.private_hand))
        self.assertEqual(payload["board"], [])
        self.assertNotIn("opponent_hands", payload)
        self.assertNotIn("board_runout", payload)
        self.assertEqual(key.digest, BlueprintDecisionKey.from_state(
            cards=_preflop_context()[0],
            betting=_preflop_context()[1],
            decision=_preflop_context()[1].legal_decision(),
        ).digest)

    def test_key_factory_rejects_cross_street_and_noncontrolled_contexts(self) -> None:
        cards, betting, _ = _preflop_context()
        flop_cards = cards.advance_to(
            BettingStreet.FLOP,
            parse_cards("2c", "7d", "9h"),
        )
        with self.assertRaisesRegex(ValueError, "streets must agree"):
            BlueprintDecisionKey.from_state(
                cards=flop_cards,
                betting=betting,
                decision=betting.legal_decision(),
            )
        wrong_actor = OneSeatCardState.preflop(
            controlled_seat=4,
            private_hand=make_hole("Ah", "3h"),
        )
        with self.assertRaisesRegex(ValueError, "controlled actor"):
            BlueprintDecisionKey.from_state(
                cards=wrong_actor,
                betting=betting,
                decision=betting.legal_decision(),
            )

    def test_key_factory_rejects_a_partially_matching_stale_decision(self) -> None:
        cards, betting, _ = _preflop_context()
        exact = betting.legal_decision()
        stale = replace(exact, call_amount=exact.call_amount - 1)
        self.assertEqual(stale.acting_seat, exact.acting_seat)
        self.assertEqual(stale.street, exact.street)
        self.assertEqual(stale.current_bet, exact.current_bet)
        with self.assertRaisesRegex(ValueError, "complete public betting state"):
            BlueprintDecisionKey.from_state(
                cards=cards,
                betting=betting,
                decision=stale,
            )

    def test_semantic_categories_do_not_hide_behind_numeric_coincidences(self) -> None:
        _, _, key = _preflop_context()
        with self.assertRaisesRegex(TypeError, "fold flags"):
            replace(key, folded=(0,) * 6)  # type: ignore[arg-type]
        with self.assertRaisesRegex(ValueError, "acted-at-bet"):
            replace(key, acted_at_bet=(False,) * 6)  # type: ignore[arg-type]
        bad_history = (
            (
                BettingStreet.PREFLOP.value,
                3,
                BettingActionKind.CALL.value,
                None,
                2,
                0,
                None,
                0,
            ),
        )
        with self.assertRaisesRegex(TypeError, "full-raise flag"):
            replace(key, public_history=bad_history)  # type: ignore[arg-type]
        with self.assertRaisesRegex(ValueError, "nonsemantic label"):
            replace(
                key,
                public_history=(("preflop", 3, "wager", None, 2, False, None, 0),),
            )
        with self.assertRaisesRegex(TypeError, "kind"):
            BlueprintActionEntry(  # type: ignore[arg-type]
                key,
                BettingAction("call"),
            )


if __name__ == "__main__":
    unittest.main()
