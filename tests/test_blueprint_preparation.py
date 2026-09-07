"""Finite parity, ownership and repeated-work controls for prepared blueprints."""

from __future__ import annotations

from copy import copy
from dataclasses import fields, replace
from hashlib import sha256
from itertools import combinations
from pathlib import Path
import unittest
from unittest.mock import patch

from pontius.blueprint_artifact.codec import decode_blueprint
from pontius.blueprint_preparation.lookup import PreparedBlueprint, PreparedBlueprintProvider
from pontius.decision_provider.model import DecisionObservation, DecisionProposal, ProviderIdentity
from pontius.decision_provider.providers import BlueprintProvider
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


def _context(street=BettingStreet.PREFLOP, *, facing_bet=False, small_blind=1, big_blind=2):
    betting = NoLimitBettingState.new_hand(
        button=0, starting_stacks=(200,) * 6, small_blind=small_blind, big_blind=big_blind)
    while betting.street is not street:
        while not betting.round_complete:
            betting = betting.apply_action(CHECK if betting.legal_decision().can_check else CALL)
        betting = betting.advance_street()
    if facing_bet and street is not BettingStreet.PREFLOP:
        betting = betting.apply_action(raise_to(big_blind))
    board = {
        BettingStreet.PREFLOP: (),
        BettingStreet.FLOP: parse_cards("2c", "7d", "9h"),
        BettingStreet.TURN: parse_cards("2c", "7d", "9h", "Js"),
        BettingStreet.RIVER: parse_cards("2c", "7d", "9h", "Js", "Ac"),
    }[street]
    cards = OneSeatCardState(
        controlled_seat=betting.acting_seat, private_hand=make_hole("Ks", "Td"),
        street=street, board=board)
    return cards, betting


def _key(cards, betting):
    return BlueprintDecisionKey.from_state(
        cards=cards, betting=betting, decision=betting.legal_decision())


def _source(cards, betting, action=CALL, source_id="prepared-control"):
    return ImmutableBlueprintActionSource(source_id, (BlueprintActionEntry(_key(cards, betting),
                                                                         action),))


def _observation(cards, betting):
    return DecisionObservation("pontius-decision-observation-v1", "prepared-control-hand", 1,
                               cards, betting, betting.legal_decision(), 14_000_000_000)


def _select(source, cards, betting):
    return source.action_for(cards=cards, betting=betting, decision=betting.legal_decision())


def _rewritten(value, path, replacement):
    """Corrupt a copied exact graph without constructors hiding the bad input."""
    if not path:
        return replacement
    name, *rest = path
    if type(value) is tuple:
        return tuple(_rewritten(item, rest, replacement) if index == name else item
                     for index, item in enumerate(value))
    result = copy(value)
    object.__setattr__(result, name, _rewritten(getattr(value, name), rest, replacement))
    return result


_GRAPH_CLASSES = (ImmutableBlueprintActionSource, BlueprintActionEntry,
                  BlueprintDecisionKey, BettingAction)


def _graph_nodes(value, path=()):
    yield path, value
    if type(value) is tuple:
        for index, item in enumerate(value):
            yield from _graph_nodes(item, (*path, index))
    elif type(value) in _GRAPH_CLASSES:
        for field in fields(type(value)):
            yield from _graph_nodes(getattr(value, field.name), (*path, field.name))


def _foreign(value):
    def forbidden(*args, **kwargs):
        raise AssertionError("caller subclass hook executed")

    kind = type(value)
    foreign = type("Foreign" + kind.__name__, (kind,), {
        "__getattribute__": forbidden, "__iter__": forbidden, "__hash__": forbidden,
        "__eq__": forbidden, "__str__": forbidden,
    })
    if kind in (int, str, tuple):
        return kind.__new__(foreign, value)
    result = object.__new__(foreign)
    for field in fields(kind):
        object.__setattr__(result, field.name, getattr(value, field.name))
    return result


class PreparedBlueprintTests(unittest.TestCase):
    def test_literal_call_and_empty_canonical_bytes(self):
        cards, betting = _context()
        source = _source(cards, betting)
        prepared = PreparedBlueprint(source)
        result = _select(prepared, cards, betting)
        self.assertEqual((result.action, result.table_hit), (CALL, True))
        self.assertEqual(result.source_digest, source.digest)
        self.assertEqual(prepared.canonical_bytes(), source.canonical_bytes())
        raw = (b'{"entries":[],"source_id":"prepared-empty",'
               b'"version":"immutable-reference-blueprint-v1"}')
        empty = PreparedBlueprint(ImmutableBlueprintActionSource("prepared-empty"))
        self.assertEqual(empty.canonical_bytes(), raw)
        self.assertEqual(empty.digest, sha256(raw).hexdigest())
        self.assertEqual((_select(empty, cards, betting).action,
                          _select(empty, cards, betting).table_hit), (CALL, False))

    def test_first_last_and_miss_parity_at_finite_table_sizes(self):
        _, betting = _context()
        holes = tuple(combinations(range(52), 2))
        for size in (0, 16, 128, 1024):
            entries = []
            for index, hole in enumerate(holes[:size]):
                cards = OneSeatCardState.preflop(controlled_seat=3, private_hand=hole)
                action = FOLD if index == 0 else raise_to(4) if index == size - 1 else CALL
                entries.append(BlueprintActionEntry(_key(cards, betting), action))
            source = ImmutableBlueprintActionSource(f"prepared-size-{size}", tuple(entries))
            prepared, provider = PreparedBlueprint(source), PreparedBlueprintProvider(source)
            reference = BlueprintProvider(source)
            self.assertEqual(prepared.canonical_bytes(), source.canonical_bytes())
            self.assertEqual(prepared.digest, source.digest)
            self.assertEqual(provider.identity, reference.identity)
            cases = [(holes[size], CALL, False)]
            if size:
                cases += [(holes[0], FOLD, True), (holes[size - 1], raise_to(4), True)]
            for hole, action, hit in cases:
                with self.subTest(size=size, hole=hole, hit=hit):
                    cards = OneSeatCardState.preflop(controlled_seat=3, private_hand=hole)
                    result = _select(prepared, cards, betting)
                    self.assertEqual((result.action, result.table_hit), (action, hit))
                    self.assertEqual(result, _select(source, cards, betting))
                    obs = _observation(cards, betting)
                    proposal = provider.propose(obs)
                    self.assertEqual(proposal, reference.propose(obs))
                    self.assertEqual((proposal.action, proposal.reason),
                                     (action, "blueprint_hit" if hit else "blueprint_default"))
                    betting.apply_action(result.action)

    def test_every_street_and_legal_action_uses_the_reference_validator(self):
        for street in BettingStreet:
            cards, betting = _context(street, facing_bet=True)
            maximum = 200 if street is BettingStreet.PREFLOP else 198
            for action in (FOLD, CALL, raise_to(4), raise_to(maximum)):
                with self.subTest(street=street, action=action):
                    source = _source(cards, betting, action)
                    result = _select(PreparedBlueprint(source), cards, betting)
                    self.assertEqual((result.action, result.table_hit), (action, True))
                    self.assertEqual(result, _select(source, cards, betting))
                    obs = _observation(cards, betting)
                    proposal = PreparedBlueprintProvider(source).propose(obs)
                    self.assertEqual((proposal.action, proposal.reason), (action, "blueprint_hit"))
                    self.assertEqual(proposal, BlueprintProvider(source).propose(obs))
                    betting.apply_action(result.action)
            if street is not BettingStreet.PREFLOP:
                cards, betting = _context(street)
                source = _source(cards, betting, CHECK)
                result = _select(PreparedBlueprint(source), cards, betting)
                self.assertEqual((result.action, result.table_hit), (CHECK, True))
                self.assertEqual(result, _select(source, cards, betting))
                obs = _observation(cards, betting)
                self.assertEqual(PreparedBlueprintProvider(source).propose(obs),
                                 BlueprintProvider(source).propose(obs))
                betting.apply_action(result.action)

    def test_passive_misses_preserve_call_and_check_on_all_streets(self):
        source = ImmutableBlueprintActionSource("prepared-passive")
        prepared, provider = PreparedBlueprint(source), PreparedBlueprintProvider(source)
        for street in BettingStreet:
            for facing_bet in (False, True):
                with self.subTest(street=street, facing_bet=facing_bet):
                    cards, betting = _context(street, facing_bet=facing_bet)
                    expected = CALL if street is BettingStreet.PREFLOP or facing_bet else CHECK
                    result = _select(prepared, cards, betting)
                    self.assertEqual((result.action, result.table_hit), (expected, False))
                    self.assertEqual(result, _select(source, cards, betting))
                    proposal = provider.propose(_observation(cards, betting))
                    self.assertEqual((proposal.action, proposal.reason),
                                     (expected, "blueprint_default"))
                    betting.apply_action(result.action)

    def test_illegal_matching_entries_refuse_instead_of_becoming_misses(self):
        cards, betting = _context()
        for action in (CHECK, raise_to(3), raise_to(201)):
            with self.subTest(action=action):
                source = _source(cards, betting, action)
                prepared, provider = PreparedBlueprint(source), PreparedBlueprintProvider(source)
                for candidate in (source, prepared):
                    with self.assertRaisesRegex(ValueError, "immutable blueprint"):
                        _select(candidate, cards, betting)
                for candidate in (BlueprintProvider(source), provider):
                    with self.assertRaisesRegex(ValueError, "immutable blueprint"):
                        candidate.propose(_observation(cards, betting))

    def test_stale_and_cross_context_queries_keep_reference_refusals(self):
        cards, betting = _context()
        source = _source(cards, betting)
        prepared = PreparedBlueprint(source)
        decision = betting.legal_decision()
        queries = (
            (cards, betting, replace(decision, call_amount=1)),
            (replace(cards, controlled_seat=4), betting, decision),
            (_context(BettingStreet.FLOP)[0], betting, decision),
        )
        for query_cards, query_betting, query_decision in queries:
            for candidate in (source, prepared):
                with self.subTest(candidate=type(candidate), cards=query_cards):
                    with self.assertRaises(ValueError):
                        candidate.action_for(cards=query_cards, betting=query_betting,
                                             decision=query_decision)

    def test_complete_key_differences_are_misses(self):
        cards, betting = _context(BettingStreet.RIVER, small_blind=2, big_blind=4)
        key = _key(cards, betting)
        changes = (
            {"controlled_seat": 2}, {"private_hand": make_hole("Qh", "Qd")},
            {"board": parse_cards("2c", "7d", "9h", "Js", "Ad")}, {"button": 1},
            {"small_blind": 1}, {"big_blind": 5},
            {"street": BettingStreet.TURN, "board": key.board[:4]},
            {"starting_stacks": (201, *key.starting_stacks[1:])},
            {"stacks": (197, *key.stacks[1:])},
            {"total_contributions": (5, *key.total_contributions[1:])},
            {"street_contributions": (1, *key.street_contributions[1:])},
            {"folded": (True, *key.folded[1:])},
            {"pending_seats": tuple(reversed(key.pending_seats))},
            {"last_full_raise_size": 5}, {"acted_at_bet": (1, *key.acted_at_bet[1:])},
            {"public_history": (*key.public_history, ("river", 0, "check", None,
                                                       0, False, None, 0))},
        )
        for change in changes:
            with self.subTest(fields=tuple(change)):
                other = replace(key, **change)
                self.assertNotEqual(other, key)
                source = ImmutableBlueprintActionSource("complete-key", (
                    BlueprintActionEntry(other, raise_to(4)),))
                prepared = PreparedBlueprint(source)
                result = _select(prepared, cards, betting)
                self.assertEqual((result.action, result.table_hit), (CHECK, False))
                self.assertEqual(result, _select(source, cards, betting))

    def test_hash_and_digest_collisions_still_resolve_by_complete_key_equality(self):
        cards, betting = _context()
        other = replace(cards, private_hand=make_hole("Qh", "Qd"))
        miss = replace(cards, private_hand=make_hole("8h", "8d"))
        # Control only the collision trigger; construction and lookup remain real.
        with patch.object(BlueprintDecisionKey, "__hash__", lambda self: 17), \
                patch.object(BlueprintDecisionKey, "digest", property(lambda self: "0" * 64)):
            key, other_key = _key(cards, betting), _key(other, betting)
            self.assertNotEqual(key, other_key)
            self.assertEqual(hash(key), hash(other_key))
            self.assertEqual(key.digest, other_key.digest)
            source = ImmutableBlueprintActionSource("collision-control", (
                BlueprintActionEntry(key, FOLD), BlueprintActionEntry(other_key, raise_to(4))))
            prepared, provider = PreparedBlueprint(source), PreparedBlueprintProvider(source)
            for query, expected, hit in ((cards, FOLD, True), (other, raise_to(4), True),
                                         (miss, CALL, False)):
                result = _select(prepared, query, betting)
                self.assertEqual((result.action, result.table_hit), (expected, hit))
                self.assertEqual(result, _select(source, query, betting))
                proposal = provider.propose(_observation(query, betting))
                self.assertEqual((proposal.action, proposal.reason),
                                 (expected, "blueprint_hit" if hit else "blueprint_default"))

    def test_canonical_identity_tracks_values_and_ignores_entry_order(self):
        cards, betting = _context()
        first = BlueprintActionEntry(_key(cards, betting), CALL)
        second = BlueprintActionEntry(_key(replace(cards, private_hand=make_hole("Qh", "Qd")),
                                               betting), FOLD)
        original = ImmutableBlueprintActionSource("identity-control", (first, second))
        variants = (
            (replace(original, entries=(second, first)), True),
            (replace(original, source_id="identity-changed"), False),
            (replace(original, entries=(replace(first, action=raise_to(4)), second)), False),
            (replace(original, entries=(replace(first, key=replace(first.key, button=1)),
                                        second)), False),
        )
        for source, same in ((original, True), *variants):
            with self.subTest(source=source.source_id, same=same):
                prepared = PreparedBlueprint(source)
                self.assertEqual(prepared.canonical_bytes(), source.canonical_bytes())
                self.assertEqual(prepared.digest, source.digest)
                self.assertEqual(prepared.digest == original.digest, same)
                provider = PreparedBlueprintProvider(source)
                self.assertEqual(provider.identity, BlueprintProvider(source).identity)
                self.assertEqual(provider.identity == BlueprintProvider(original).identity, same)

    def test_existing_artifacts_keep_canonical_bytes_and_provider_identity(self):
        fixtures = Path(__file__).with_name("fixtures") / "blueprint_artifact"
        for name in ("raise_control.json", "history_control.json"):
            with self.subTest(fixture=name):
                source = decode_blueprint((fixtures / name).read_bytes())
                prepared = PreparedBlueprint(source)
                self.assertEqual(prepared.canonical_bytes(), source.canonical_bytes())
                self.assertEqual(prepared.digest, source.digest)
                self.assertEqual(PreparedBlueprintProvider(source).identity,
                                 BlueprintProvider(source).identity)

    def test_source_entry_key_and_action_mutation_cannot_change_prepared_results(self):
        cards, betting = _context()
        mutations = (
            (("source_id",), "changed-after-preparation"), (("entries",), ()),
            (("entries", 0, "action"), FOLD),
            (("entries", 0, "key", "private_hand"), make_hole("Qh", "Qd")),
            (("entries", 0, "action", "raise_to"), 99),
        )
        for path, value in mutations:
            with self.subTest(path=path):
                source = _source(cards, betting, raise_to(4))
                raw, digest = source.canonical_bytes(), source.digest
                prepared, provider = PreparedBlueprint(source), PreparedBlueprintProvider(source)
                identity = provider.identity
                target = source
                for name in path[:-1]:
                    target = target[name] if type(name) is int else getattr(target, name)
                object.__setattr__(target, path[-1], value)
                self.assertEqual((prepared.canonical_bytes(), prepared.digest), (raw, digest))
                result = _select(prepared, cards, betting)
                self.assertEqual((result.action, result.table_hit, result.source_digest),
                                 (raise_to(4), True, digest))
                self.assertEqual(provider.identity, identity)
                proposal = provider.propose(_observation(cards, betting))
                self.assertEqual((proposal.action, proposal.reason), (raise_to(4), "blueprint_hit"))

    def test_returned_selection_and_proposal_graphs_do_not_alias_owned_state(self):
        cards, betting = _context()
        for hit in (False, True):
            source = (_source(cards, betting, raise_to(4)) if hit
                      else ImmutableBlueprintActionSource("owned-miss"))
            prepared, provider = PreparedBlueprint(source), PreparedBlueprintProvider(source)
            expected = raise_to(4) if hit else CALL
            result = _select(prepared, cards, betting)
            object.__setattr__(result.action, "kind", BettingActionKind.FOLD)
            object.__setattr__(result.key, "private_hand", make_hole("Qh", "Qd"))
            object.__setattr__(result, "source_digest", "0" * 64)
            object.__setattr__(result, "table_hit", not hit)
            again = _select(prepared, cards, betting)
            self.assertEqual((again.action, again.table_hit, again.source_digest),
                             (expected, hit, source.digest))
            self.assertEqual(again.key, _key(cards, betting))
            obs = _observation(cards, betting)
            proposal = provider.propose(obs)
            object.__setattr__(proposal.action, "kind", BettingActionKind.FOLD)
            object.__setattr__(proposal, "decision_sha256", "0" * 64)
            again_proposal = provider.propose(obs)
            self.assertEqual((again_proposal.action, again_proposal.decision_sha256),
                             (expected, obs.decision_sha256))
            self.assertEqual(CALL, BettingAction(BettingActionKind.CALL))

    def test_every_subclass_capable_source_node_refuses_before_its_hooks_run(self):
        cards, betting = _context(BettingStreet.RIVER)
        source = _source(cards, betting, raise_to(4))
        for path, value in _graph_nodes(source):
            if type(value) not in (*_GRAPH_CLASSES, tuple, str, int):
                continue
            malformed = _rewritten(source, path, _foreign(value))
            for constructor in (PreparedBlueprint, PreparedBlueprintProvider):
                with self.subTest(path=path, constructor=constructor.__name__):
                    with self.assertRaises(TypeError):
                        constructor(malformed)

    def test_malformed_exact_graphs_and_duplicate_entries_are_revalidated(self):
        cards, betting = _context()
        source = _source(cards, betting, raise_to(4))
        key_path = ("entries", 0, "key")
        changes = (
            (("source_id",), ""), (("source_id",), 1), (("entries",), []),
            (("entries", 0, "key"), "not-a-key"),
            (("entries", 0, "action"), "raise"),
            ((*key_path, "controlled_seat"), True),
            ((*key_path, "private_hand"), [0, 1]),
            ((*key_path, "private_hand"), (True, 1)),
            ((*key_path, "board"), (0,)), ((*key_path, "street"), "preflop"),
            ((*key_path, "stacks"), (True,) * 6), ((*key_path, "stacks"), (1,)),
            ((*key_path, "folded"), (0,) * 6), ((*key_path, "acted_at_bet"), (False,) * 6),
            ((*key_path, "public_history"), (("preflop", True, "call", None,
                                               2, False, None, 0),)),
            (("entries", 0, "action", "kind"), "raise"),
            (("entries", 0, "action", "raise_to"), True),
        )
        for path, value in changes:
            malformed = _rewritten(source, path, value)
            for constructor in (PreparedBlueprint, PreparedBlueprintProvider):
                with self.subTest(path=path, constructor=constructor.__name__):
                    with self.assertRaises((TypeError, ValueError)):
                        constructor(malformed)
        duplicate = _rewritten(source, ("entries",), source.entries * 2)
        for constructor in (PreparedBlueprint, PreparedBlueprintProvider):
            with self.assertRaisesRegex(ValueError, "duplicate"):
                constructor(duplicate)
            for foreign in (None, {}, CALL):
                with self.assertRaises(TypeError):
                    constructor(foreign)

    def test_ordinary_assignment_to_prepared_objects_is_refused(self):
        source = ImmutableBlueprintActionSource("assignment-control")
        prepared, provider = PreparedBlueprint(source), PreparedBlueprintProvider(source)
        # Writable cache slots could separate the stored actions from their bound digest.
        for target, names in (
            (prepared, ("_canonical", "_digest", "_actions", "digest",
                        "canonical_bytes", "entries")),
            (provider, ("_blueprint", "_identity", "identity", "propose", "blueprint")),
        ):
            for name in names:
                with self.subTest(kind=type(target).__name__, name=name):
                    with self.assertRaises((AttributeError, TypeError)):
                        setattr(target, name, None)
        self.assertEqual(prepared.digest, source.digest)
        self.assertEqual(provider.identity, BlueprintProvider(source).identity)

    def test_table_serializes_once_and_repeated_lookups_do_not_serialize(self):
        cards, betting = _context()
        source = _source(cards, betting, raise_to(4))
        miss = replace(cards, private_hand=make_hole("Qh", "Qd"))
        calls = []
        canonical = ImmutableBlueprintActionSource.canonical_bytes

        def count(actual):
            calls.append(type(actual))
            return canonical(actual)

        with patch.object(ImmutableBlueprintActionSource, "canonical_bytes", count):
            prepared = PreparedBlueprint(source)
            self.assertEqual(calls, [ImmutableBlueprintActionSource])
            for _ in range(8):
                for query, expected in ((cards, raise_to(4)), (miss, CALL)):
                    self.assertEqual(_select(prepared, query, betting).action, expected)
                    self.assertEqual(sha256(prepared.canonical_bytes()).hexdigest(),
                                     prepared.digest)
            self.assertEqual(calls, [ImmutableBlueprintActionSource])


class PreparedBlueprintProviderTests(unittest.TestCase):
    def test_provider_configuration_is_the_exact_legacy_value_and_owned(self):
        source = ImmutableBlueprintActionSource("provider-config")
        provider = PreparedBlueprintProvider(source)
        raw = (b'{"blueprint_sha256":"' + source.digest.encode("ascii")
               + b'","provider":"blueprint-v1","version":"pontius-decision-provider-config-v1"}')
        expected = ProviderIdentity("blueprint-v1", sha256(raw).hexdigest())
        self.assertEqual(provider.identity, expected)
        self.assertEqual(provider.identity, BlueprintProvider(source).identity)
        identity = provider.identity
        object.__setattr__(identity, "provider", "baseline-rules-v1")
        object.__setattr__(identity, "config_sha256", "0" * 64)
        self.assertEqual(provider.identity, expected)
        self.assertIsNot(provider.identity, identity)

    def test_exact_observation_digest_and_proposal_contract(self):
        cards, betting = _context()
        provider = PreparedBlueprintProvider(_source(cards, betting, raise_to(4)))
        obs = _observation(cards, betting)
        for candidate in (obs, replace(obs, hand_id="another-prepared-hand"),
                          replace(obs, action_index=2), replace(obs, remaining_work_ns=0)):
            proposal = provider.propose(candidate)
            self.assertIs(type(proposal), DecisionProposal)
            self.assertEqual(proposal.decision_sha256, candidate.decision_sha256)
            self.assertEqual((proposal.action, proposal.reason), (raise_to(4), "blueprint_hit"))
        for value in (None, {}, _foreign(obs)):
            with self.assertRaises(TypeError):
                provider.propose(value)

    def test_one_real_serialization_per_provider_and_no_repeated_warm_serialization(self):
        cards, betting = _context()
        source = _source(cards, betting, raise_to(4))
        observations = (_observation(cards, betting),
                        _observation(replace(cards, private_hand=make_hole("Qh", "Qd")), betting))
        canonical = ImmutableBlueprintActionSource.canonical_bytes
        for constructor in (PreparedBlueprintProvider, BlueprintProvider):
            calls = []

            def count(actual):
                calls.append(type(actual))
                return canonical(actual)

            with patch.object(ImmutableBlueprintActionSource, "canonical_bytes", count):
                provider = constructor(source)
                self.assertEqual(calls, [ImmutableBlueprintActionSource])
                for _ in range(8):
                    for obs, expected in zip(observations, (raise_to(4), CALL)):
                        self.assertEqual(provider.propose(obs).action, expected)
                        self.assertEqual(provider.identity.provider, "blueprint-v1")
                if constructor is PreparedBlueprintProvider:
                    self.assertEqual(len(calls), 1, "canonicalization repeated on warm lookup")
                else:
                    self.assertEqual(len(calls), 17)
                    with self.assertRaisesRegex(AssertionError, "canonicalization repeated"):
                        self.assertEqual(len(calls), 1, "canonicalization repeated on warm lookup")


if __name__ == "__main__":
    unittest.main()
