"""Finite literal decision rules and exact engine-side provider admission."""
import copy
import hashlib
import json
from dataclasses import fields, replace
from pathlib import Path
import unittest

from pontius.decision_provider.model import DecisionObservation, DecisionProposal
from pontius.decision_provider.providers import make_provider, visible_rank
from pontius.decision_provider.selection import resolve_proposal
from pontius.holdem_cards import OneSeatCardState
from pontius.immutable_blueprint import (
    BlueprintActionEntry, BlueprintDecisionKey, ImmutableBlueprintActionSource,
)
from pontius.no_limit_betting import CALL, CHECK, FOLD, BettingStreet, NoLimitBettingState, raise_to
from pontius.river import parse_cards


def observation(case=None):
    case = case or {'hole': 'As Ah'}
    stacks = [200] * 6
    if 'short' in case:
        stacks[3] = case['short']
    if 'call_stack' in case:
        stacks[2 if 'board' in case else 4] = case['call_stack']
    if case.get('cost') == 1:
        stacks[1] = 3
    state = NoLimitBettingState.new_hand(
        button=0, starting_stacks=tuple(stacks), small_blind=1, big_blind=2)
    board = tuple(parse_cards(*case.get('board', '').split()))
    target = {0: BettingStreet.PREFLOP, 3: BettingStreet.FLOP,
              4: BettingStreet.TURN, 5: BettingStreet.RIVER}[len(board)]
    if case.get('prior_raise'):
        state = state.apply_action(CALL)
        state = state.apply_action(CALL)
        state = state.apply_action(CALL)
        state = state.apply_action(CALL)
        state = state.apply_action(raise_to(4))
    while state.street != target:
        while not state.round_complete:
            state = state.apply_action(CHECK if state.legal_decision().can_check else CALL)
        state = state.advance_street()
    if case.get('free'):
        while state.acting_seat != 2:
            state = state.apply_action(CALL)
    if case.get('own_raise'):
        actor = state.acting_seat
        amount = state.legal_decision().raise_bounds.minimum_raise_to
        state = state.apply_action(raise_to(amount))
        state = state.apply_action(raise_to(amount + case['cost']))
        while state.acting_seat != actor:
            state = state.apply_action(CALL)
    elif 'cost' in case:
        state = state.apply_action(raise_to(case['cost']))
    cards = OneSeatCardState(
        controlled_seat=state.acting_seat,
        private_hand=tuple(sorted(parse_cards(*case['hole'].split()))),
        street=target, board=board)
    return DecisionObservation(
        version='pontius-decision-observation-v1',
        hand_id='pontius-v0a-event-interface-v2-correctness-rules',
        action_index=1, cards=cards, betting=state, decision=state.legal_decision(),
        remaining_work_ns=13_000_000_000)


class ProviderRulesTests(unittest.TestCase):
    def setUp(self):
        self.blueprint = ImmutableBlueprintActionSource(source_id='provider-test')
        self.provider = make_provider('baseline-rules-v1', self.blueprint)

    def test_literal_rule_partitions(self):
        path = Path(__file__).parent / 'fixtures/decision_provider/rules.json'
        cases = json.loads(path.read_text(encoding='utf-8'))
        self.assertLessEqual(len(cases), 48)
        self.assertLessEqual(path.stat().st_size, 32768)
        for case in cases:
            with self.subTest(case=case):
                obs = observation(case)
                proposal = self.provider.propose(obs)
                self.assertEqual((proposal.action.kind.value, proposal.action.raise_to,
                                  proposal.reason),
                                 (case['kind'], case.get('amount'), case['reason']))
                self.assertEqual(proposal.decision_sha256, obs.decision_sha256)
                obs.betting.apply_action(proposal.action)

    def test_turn_rank_independent_best_five(self):
        self.assertEqual(visible_rank(parse_cards('Ac', '9d', '2c', '3c', '4c', '5c')),
                         (8, 5))
        self.assertEqual(visible_rank(parse_cards('As', 'Kh', '2c', '2d', '7s', '7h')),
                         (2, 7, 2, 14))
        with self.assertRaises(ValueError):
            visible_rank(parse_cards('As', 'Kh'))

    def test_blueprint_hit_and_default(self):
        obs = observation()
        default = make_provider('blueprint-v1', self.blueprint).propose(obs)
        self.assertEqual((default.action, default.reason), (CALL, 'blueprint_default'))
        key = BlueprintDecisionKey.from_state(
            cards=obs.cards, betting=obs.betting, decision=obs.decision)
        blueprint = ImmutableBlueprintActionSource(
            source_id='provider-hit', entries=(BlueprintActionEntry(key, FOLD),))
        hit = make_provider('blueprint-v1', blueprint).propose(obs)
        self.assertEqual((hit.action, hit.reason), (FOLD, 'blueprint_hit'))

    def test_fixed_configuration_identities(self):
        config = dict(max_raises_per_street=1, playable_any_pair=True, playable_rank_min=10,
                      playable_suited_ace=True, postflop_pair_call_cap_bb=1,
                      postflop_two_pair_call_cap_bb=2, preflop_call_cap_bb=2,
                      premium_ace_kickers=[12, 13], premium_call_cap_bb=None,
                      premium_pair_min=10, provider='baseline-rules-v1',
                      raise_size='legal_minimum', river_board_only='check_or_fold',
                      version='pontius-decision-provider-config-v1')
        def digest(value):
            return hashlib.sha256(json.dumps(value, sort_keys=True,
                                             separators=(',', ':')).encode('ascii')).hexdigest()
        self.assertEqual(self.provider.identity.config_sha256, digest(config))
        provider = make_provider('blueprint-v1', self.blueprint)
        self.assertEqual(provider.identity.config_sha256, digest(dict(
            provider='blueprint-v1', blueprint_sha256=self.blueprint.digest,
            version='pontius-decision-provider-config-v1')))
        for kind in ('baseline', None, lambda: None):
            with self.assertRaises((ValueError, TypeError)):
                make_provider(kind, self.blueprint)

    def test_observation_digest_literal_legal_and_stable_hint(self):
        obs = observation()
        key = BlueprintDecisionKey.from_state(cards=obs.cards, betting=obs.betting,
                                             decision=obs.decision)
        legal = dict(street='preflop', acting_seat=3, stack=200, street_contribution=0,
                     current_bet=2, to_call=2, call_amount=2,
                     action_kinds=['fold', 'call', 'raise'], raise_bounds=dict(
                         minimum_raise_to=4, maximum_raise_to=200, minimum_full_raise_to=4,
                         maximum_contestable_raise_to=200, all_in_only=False))
        payload = dict(version='pontius-decision-observation-v1', hand_id=obs.hand_id,
                       action_index=1, key=json.loads(key.canonical_bytes()), legal=legal)
        expected = hashlib.sha256(json.dumps(payload, sort_keys=True,
                                             separators=(',', ':')).encode('ascii')).hexdigest()
        self.assertEqual(obs.decision_sha256, expected)
        self.assertEqual(replace(obs, remaining_work_ns=0).decision_sha256, expected)
        self.assertNotEqual(replace(obs, action_index=2).decision_sha256, expected)
        self.assertEqual({f.name for f in fields(obs)}, {
            'version', 'hand_id', 'action_index', 'cards', 'betting', 'decision',
            'remaining_work_ns'})

    def test_observation_owns_graph_and_refuses_foreign_or_mutable_values(self):
        obs = observation()
        self.assertIsNot(obs.cards, observation().cards)
        original = obs.betting
        copied = replace(obs)
        self.assertIsNot(original, copied.betting)
        for changes in ({'remaining_work_ns': True}, {'remaining_work_ns': -1},
                        {'remaining_work_ns': 14_000_000_001}, {'action_index': False},
                        {'action_index': 0}, {'version': 'unknown'}):
            with self.subTest(changes=changes), self.assertRaises((TypeError, ValueError)):
                replace(obs, **changes)
        for name, value in [('stack', True), ('action_kinds', ['fold', 'call', 'raise'])]:
            bad = copy.copy(obs.decision)
            object.__setattr__(bad, name, value)
            with self.assertRaises((TypeError, ValueError)):
                replace(obs, decision=bad)
        bad_cards = copy.copy(obs.cards)
        object.__setattr__(bad_cards, 'private_hand', list(obs.cards.private_hand))
        with self.assertRaises((TypeError, ValueError)):
            replace(obs, cards=bad_cards)

    def test_proposal_admission_and_legal_binding(self):
        obs = observation()
        good = DecisionProposal(obs.decision_sha256, raise_to(4), 'premium_raise')
        selected = resolve_proposal(obs, good, CALL, 'passive_default')
        self.assertEqual((selected.provider_outcome, selected.selection_reason,
                          selected.selection_origin, selected.selected_action),
                         ('proposed', 'provider_selected', 'provider', raise_to(4)))
        self.assertIsNot(selected.proposal, good)
        for proposal in (DecisionProposal('0' * 64, CALL, 'premium_call'),
                         DecisionProposal(obs.decision_sha256, CHECK, 'free_check'),
                         DecisionProposal(obs.decision_sha256, raise_to(3), 'premium_raise')):
            result = resolve_proposal(obs, proposal, CALL, 'passive_default')
            self.assertEqual((result.provider_outcome, result.selection_reason,
                              result.selection_origin, result.selected_action),
                             ('invalid', 'provider_invalid', 'blueprint_fallback', CALL))
            self.assertEqual(result.proposal, proposal)
        abstain = DecisionProposal(obs.decision_sha256, None, 'abstain')
        self.assertEqual(resolve_proposal(obs, abstain, CALL, 'passive_default').provider_outcome,
                         'abstained')
        malformed = copy.copy(good)
        object.__setattr__(malformed, 'action', ['raise', 4])
        class Foreign:
            def __getattribute__(self, name):
                raise AssertionError('caller code must never run')
        for proposal in (None, {}, Foreign(), malformed):
            result = resolve_proposal(obs, proposal, CALL, 'passive_default')
            self.assertEqual(result.provider_outcome, 'invalid')
            self.assertIsNone(result.proposal)
        for action, reason in ((None, 'premium_call'), (CALL, 'abstain'), (CALL, 'anything')):
            with self.assertRaises((TypeError, ValueError)):
                DecisionProposal(obs.decision_sha256, action, reason)
        with self.assertRaises((TypeError, ValueError)):
            resolve_proposal(obs, good, CHECK, 'passive_default')

    def test_nested_foreign_values_and_stale_abstention(self):
        obs = observation()
        class Integer(int):
            pass
        class ForeignObservation(DecisionObservation):
            pass
        for name, value in (('controlled_seat', Integer(3)), ('private_hand', (True, 51))):
            cards = copy.copy(obs.cards)
            object.__setattr__(cards, name, value)
            with self.assertRaises((TypeError, ValueError)):
                replace(obs, cards=cards)
        foreign = ForeignObservation(**{f.name: getattr(obs, f.name) for f in fields(obs)})
        with self.assertRaises(TypeError):
            self.provider.propose(foreign)
        malformed = copy.copy(obs)
        object.__setattr__(malformed, 'remaining_work_ns', True)
        with self.assertRaises(TypeError):
            resolve_proposal(malformed, None, CALL, 'passive_default')
        stale = DecisionProposal('0' * 64, None, 'abstain')
        self.assertEqual(resolve_proposal(obs, stale, CALL, 'passive_default').provider_outcome,
                         'invalid')
        good = DecisionProposal(obs.decision_sha256, raise_to(4), 'premium_raise')
        malformed = copy.copy(good)
        action = copy.copy(good.action)
        object.__setattr__(action, 'raise_to', Integer(4))
        object.__setattr__(malformed, 'action', action)
        self.assertIsNone(resolve_proposal(obs, malformed, CALL, 'passive_default').proposal)



if __name__ == '__main__':
    unittest.main()
