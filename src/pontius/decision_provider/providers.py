"""Two fixed built-ins; all strategy work uses already visible cards."""
from __future__ import annotations

from itertools import combinations
from pontius.decision_provider.model import (
    DecisionObservation, DecisionProposal, ProviderIdentity, canonical_sha256, own_value,
)
from pontius.immutable_blueprint import ImmutableBlueprintActionSource
from pontius.no_limit_betting import CALL, CHECK, FOLD, BettingActionKind, BettingStreet, raise_to
from pontius.river import evaluate_five, evaluate_seven


def visible_rank(cards):
    if len(cards) == 5:
        return evaluate_five(cards)
    if len(cards) == 6:
        return max(evaluate_five(group) for group in combinations(cards, 5))
    if len(cards) == 7:
        return evaluate_seven(cards)
    raise ValueError('expected five to seven already-visible cards')


class BlueprintProvider:
    __slots__ = ('_blueprint', '_identity')

    def __init__(self, blueprint):
        if type(blueprint) is not ImmutableBlueprintActionSource:
            raise TypeError('provider requires an exact immutable blueprint')
        self._blueprint = own_value(blueprint)
        config = dict(provider='blueprint-v1', blueprint_sha256=self._blueprint.digest,
                      version='pontius-decision-provider-config-v1')
        self._identity = ProviderIdentity('blueprint-v1', canonical_sha256(config))

    @property
    def identity(self):
        return self._identity

    def propose(self, observation):
        if type(observation) is not DecisionObservation:
            raise TypeError('provider requires an exact observation')
        result = self._blueprint.action_for(cards=observation.cards, betting=observation.betting,
                                            decision=observation.decision)
        return DecisionProposal(observation.decision_sha256, result.action,
                                'blueprint_hit' if result.table_hit else 'blueprint_default')


class BaselineProvider(BlueprintProvider):
    __slots__ = ()

    def __init__(self, blueprint):
        super().__init__(blueprint)
        if self._blueprint.uses_mixed_actions:
            raise ValueError('baseline requires a deterministic fallback blueprint')
        config = dict(max_raises_per_street=1, playable_any_pair=True, playable_rank_min=10,
            playable_suited_ace=True, postflop_pair_call_cap_bb=1, postflop_two_pair_call_cap_bb=2,
            preflop_call_cap_bb=2, premium_ace_kickers=[12, 13], premium_call_cap_bb=None,
            premium_pair_min=10, provider='baseline-rules-v1', raise_size='legal_minimum',
            river_board_only='check_or_fold', version='pontius-decision-provider-config-v1')
        self._identity = ProviderIdentity('baseline-rules-v1', canonical_sha256(config))

    def propose(self, observation):
        if type(observation) is not DecisionObservation:
            raise TypeError('provider requires an exact observation')
        cards, state, decision = observation.cards, observation.betting, observation.decision
        raised = any(r.seat == cards.controlled_seat and r.street is state.street
                     and r.action.kind is BettingActionKind.RAISE for r in state.history)
        strong, call_cap, prefix = False, -1, ''
        if state.street is BettingStreet.PREFLOP:
            low, high = sorted(card // 4 + 2 for card in cards.private_hand)
            strong = (low == high and low >= 10) or (high == 14 and low in (12, 13))
            playable = low == high or low >= 10 or (
                high == 14 and cards.private_hand[0] % 4 == cards.private_hand[1] % 4)
            call_cap = decision.call_amount if strong else 2 * state.big_blind if playable else -1
            prefix = 'premium' if strong else 'playable'
        else:
            rank = visible_rank(cards.known_cards)
            board_only = state.street is BettingStreet.RIVER and rank == evaluate_five(cards.board)
            if not board_only:
                strong = rank[0] >= 2
                call_cap = (2 if strong else 1 if rank[0] == 1 else -1) * state.big_blind
                prefix = 'made_hand' if strong else 'pair'
        if strong and not raised and decision.raise_bounds is not None:
            action, reason = raise_to(decision.raise_bounds.minimum_raise_to), prefix + '_raise'
        elif decision.can_call and decision.call_amount <= call_cap:
            action, reason = CALL, prefix + '_call'
        else:
            action, reason = (CHECK, 'free_check') if decision.can_check else (FOLD, 'weak_fold')
        return DecisionProposal(observation.decision_sha256, action, reason)


def make_provider(kind, blueprint):
    if type(kind) is not str or kind not in ('blueprint-v1', 'baseline-rules-v1'):
        raise ValueError('unknown fixed provider')
    return (BlueprintProvider if kind == 'blueprint-v1' else BaselineProvider)(blueprint)
