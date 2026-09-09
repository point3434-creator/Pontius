"""Owned values and canonical identities; no runtime or transport authority."""
from __future__ import annotations

from dataclasses import dataclass, fields
from hashlib import sha256
import json
import math

from pontius.holdem_cards import OneSeatCardState
from pontius.immutable_blueprint import (
    BlueprintActionEntry, BlueprintDecisionKey, ImmutableBlueprintActionSource,
    WeightedBlueprintAction,
)
from pontius.no_limit_betting import (
    BettingAction, BettingActionKind, BettingActionRecord, BettingStreet,
    LegalBettingDecision, NoLimitBettingState, RaiseBounds, TerminalReason,
)
from pontius.v0a.model import (
    DeliveryStatus, FailureCode, HandAction, PreparationUseRecord, TimingRecord, TimingStatus,
    _require_ascii_id, _require_exact_int, _require_seat, _require_sha256, _require_street,
)

PROVIDERS = ('blueprint-v1', 'baseline-rules-v1')
PROPOSAL_REASONS = ('abstain', 'blueprint_hit', 'blueprint_default', 'premium_raise',
                    'premium_call', 'playable_call', 'made_hand_raise', 'made_hand_call',
                    'pair_call', 'free_check', 'weak_fold')
PROVIDER_OUTCOMES = ('not_called', 'proposed', 'abstained', 'error', 'invalid')
SELECTION_REASONS = ('provider_selected', 'provider_abstained', 'provider_error',
                     'provider_invalid', 'provider_late', 'provider_skipped_cutoff')


def require_label(value, choices):
    if type(value) is not str or value not in choices:
        raise ValueError('unknown or non-exact provider label')


def canonical_sha256(payload):
    return sha256(json.dumps(payload, sort_keys=True, separators=(',', ':'),
                             ensure_ascii=True, allow_nan=False).encode('ascii')).hexdigest()


def own_value(value, _depth=0):
    """Rebuild only known immutable types, without executing caller methods."""
    if _depth > 32:
        raise ValueError('provider value graph exceeds bounded depth')
    kind = type(value)
    if value is None or kind in (str, int, bool):
        return value
    if kind is float and math.isfinite(value):
        return value
    if kind in (BettingStreet, BettingActionKind, TerminalReason, DeliveryStatus,
                FailureCode, TimingStatus):
        return value
    if kind is tuple:
        return tuple(own_value(item, _depth + 1) for item in value)
    if kind in (OneSeatCardState, NoLimitBettingState, LegalBettingDecision, RaiseBounds,
                BettingAction, BettingActionRecord, BlueprintActionEntry, BlueprintDecisionKey,
                ImmutableBlueprintActionSource, WeightedBlueprintAction,
                DecisionProposal, ProviderIdentity,
                HandAction, TimingRecord, PreparationUseRecord, ProviderDecisionRecord):
        return kind(**{f.name: own_value(getattr(value, f.name), _depth + 1)
                       for f in fields(kind)})
    raise TypeError('provider value graph requires exact immutable types')


def same_exact(left, right):
    kind = type(right)
    if type(left) is not kind:
        return False
    if kind is tuple:
        return len(left) == len(right) and all(same_exact(a, b) for a, b in zip(left, right))
    if kind in (LegalBettingDecision, RaiseBounds):
        return all(same_exact(getattr(left, f.name), getattr(right, f.name)) for f in fields(kind))
    return left == right


@dataclass(frozen=True, slots=True)
class DecisionObservation:
    version: str
    hand_id: str
    action_index: int
    cards: OneSeatCardState
    betting: NoLimitBettingState
    decision: LegalBettingDecision
    remaining_work_ns: int

    def __post_init__(self):
        require_label(self.version, ('pontius-decision-observation-v1',))
        _require_ascii_id(self.hand_id, name='hand id')
        _require_exact_int(self.action_index, name='action index', minimum=1)
        _require_exact_int(self.remaining_work_ns, name='remaining work', minimum=0)
        if self.remaining_work_ns > 14_000_000_000:
            raise ValueError('remaining work exceeds the action work budget')
        if (type(self.cards) is not OneSeatCardState
                or type(self.betting) is not NoLimitBettingState
                or type(self.decision) is not LegalBettingDecision):
            raise TypeError('observation requires exact visible context')
        if type(self.betting.history) is not tuple or len(self.betting.history) > 256:
            raise ValueError('provider history exceeds finite action domain')
        cards, betting = own_value(self.cards), own_value(self.betting)
        if sum(betting.starting_stacks) >= 10**640:
            raise ValueError('chip total exceeds finite event domain')
        decision = betting.legal_decision()
        if not same_exact(self.decision, decision):
            raise ValueError('decision differs from recomputed legal context')
        BlueprintDecisionKey.from_state(cards=cards, betting=betting, decision=decision)
        object.__setattr__(self, 'cards', cards)
        object.__setattr__(self, 'betting', betting)
        object.__setattr__(self, 'decision', decision)

    @property
    def decision_sha256(self):
        key = BlueprintDecisionKey.from_state(
            cards=self.cards, betting=self.betting, decision=self.decision)
        legal = {f.name: getattr(self.decision, f.name) for f in fields(LegalBettingDecision)}
        bounds = self.decision.raise_bounds
        legal['raise_bounds'] = None if bounds is None else {
            f.name: getattr(bounds, f.name) for f in fields(RaiseBounds)}
        return canonical_sha256(dict(version=self.version, hand_id=self.hand_id,
            action_index=self.action_index, key=json.loads(key.canonical_bytes()), legal=legal))


@dataclass(frozen=True, slots=True)
class DecisionProposal:
    decision_sha256: str
    action: BettingAction | None
    reason: str

    def __post_init__(self):
        _require_sha256(self.decision_sha256, name='proposal decision digest')
        require_label(self.reason, PROPOSAL_REASONS)
        if (self.action is None) != (self.reason == 'abstain'):
            raise ValueError('null action and abstain reason must agree')
        if self.action is not None:
            if type(self.action) is not BettingAction:
                raise TypeError('proposal action must be exact')
            object.__setattr__(self, 'action', own_value(self.action))


@dataclass(frozen=True, slots=True)
class ProviderIdentity:
    provider: str
    config_sha256: str

    def __post_init__(self):
        require_label(self.provider, PROVIDERS)
        _require_sha256(self.config_sha256, name='provider config digest')


@dataclass(frozen=True, slots=True)
class Selection:
    proposal: DecisionProposal | None
    provider_outcome: str
    selection_reason: str
    selection_origin: str
    selected_action: BettingAction


@dataclass(frozen=True, slots=True)
class ProviderDecisionRecord:
    schema_version: str
    hand_id: str
    event_index: int
    action_index: int
    street_action_index: int
    seat: int
    street: str
    state_before_sha256: str
    state_after_sha256: str | None
    visible_cards_sha256: str
    decision_sha256: str
    source_manifest_sha256: str
    provider: str
    config_sha256: str
    fallback_blueprint_sha256: str
    fallback_action: HandAction
    fallback_reason: str
    proposal: DecisionProposal | None
    provider_outcome: str
    selection_reason: str
    selection_origin: str
    selected_action: HandAction
    applied_action: HandAction | None
    delivery_status: DeliveryStatus
    delivered_action: HandAction | None
    timing: TimingRecord
    preparation_use: PreparationUseRecord
    failure_reason: FailureCode | None

    def __post_init__(self):
        require_label(self.schema_version, ('pontius-provider-decision-v1',))
        _require_ascii_id(self.hand_id, name='hand id')
        for name in ('event_index', 'action_index', 'street_action_index'):
            _require_exact_int(getattr(self, name), name=name,
                               minimum=0 if name == 'event_index' else 1)
        _require_seat(self.seat, name='acting seat')
        _require_street(self.street)
        for f in fields(type(self)):
            value = getattr(self, f.name)
            if (f.name.endswith('_sha256')
                    and not (f.name == 'state_after_sha256' and value is None)):
                _require_sha256(value, name=f.name)
        for name, choices in (('provider', PROVIDERS),
                ('fallback_reason', ('table_hit', 'passive_default')),
                ('provider_outcome', PROVIDER_OUTCOMES), ('selection_reason', SELECTION_REASONS),
                ('selection_origin', ('provider', 'blueprint_fallback'))):
            require_label(getattr(self, name), choices)
        for name, kind, optional in (('fallback_action', HandAction, False),
                ('selected_action', HandAction, False), ('applied_action', HandAction, True),
                ('delivered_action', HandAction, True), ('proposal', DecisionProposal, True),
                ('timing', TimingRecord, False), ('preparation_use', PreparationUseRecord, False),
                ('delivery_status', DeliveryStatus, False), ('failure_reason', FailureCode, True)):
            value = getattr(self, name)
            if optional and value is None:
                continue
            if type(value) is not kind:
                raise TypeError('provider record has non-exact ' + name)
            object.__setattr__(self, name, own_value(value))
