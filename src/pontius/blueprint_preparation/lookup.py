"""Own a blueprint once and retain its canonical identity and complete-key index."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from types import MappingProxyType

from pontius.decision_provider.model import (
    DecisionObservation,
    DecisionProposal,
    ProviderIdentity,
    canonical_sha256,
    own_value,
)
from pontius.immutable_blueprint import (
    BlueprintDecisionKey,
    BlueprintSelection,
    ImmutableBlueprintActionSource,
    WeightedBlueprintAction,
    passive_blueprint_action,
    require_legal_blueprint_action,
)
from pontius.no_limit_betting import BettingAction, LegalBettingDecision, NoLimitBettingState


@dataclass(frozen=True, slots=True, init=False, eq=False, repr=False)
class PreparedBlueprint:
    """An owned table whose repeated selections never serialize the table again."""

    _canonical: bytes
    _digest: str
    _actions: MappingProxyType[BlueprintDecisionKey, BettingAction | WeightedBlueprintAction]

    def __init__(self, source: ImmutableBlueprintActionSource):
        if type(source) is not ImmutableBlueprintActionSource:
            raise TypeError("preparation requires an exact immutable blueprint")
        owned = own_value(source)
        canonical = ImmutableBlueprintActionSource.canonical_bytes(owned)
        actions = MappingProxyType({entry.key: entry.action for entry in owned.entries})
        object.__setattr__(self, "_canonical", canonical)
        object.__setattr__(self, "_digest", sha256(canonical).hexdigest())
        object.__setattr__(self, "_actions", actions)

    def canonical_bytes(self) -> bytes:
        return self._canonical

    @property
    def digest(self) -> str:
        return self._digest

    def action_for(
        self,
        *,
        cards,
        betting: NoLimitBettingState,
        decision: LegalBettingDecision,
    ) -> BlueprintSelection:
        key = BlueprintDecisionKey.from_state(cards=cards, betting=betting, decision=decision)
        action = self._actions.get(key)
        table_hit = action is not None
        if action is None:
            action = passive_blueprint_action(decision)
        require_legal_blueprint_action(action, decision)
        if isinstance(action, WeightedBlueprintAction):
            action = action.sample()
        return BlueprintSelection(
            key=own_value(key),
            action=own_value(action),
            table_hit=table_hit,
            source_digest=self._digest,
        )


@dataclass(frozen=True, slots=True, init=False, eq=False, repr=False)
class PreparedBlueprintProvider:
    """The legacy blueprint-v1 provider value contract over an owned prepared table."""

    _blueprint: PreparedBlueprint
    _identity: ProviderIdentity

    def __init__(self, blueprint: ImmutableBlueprintActionSource):
        prepared = PreparedBlueprint(blueprint)
        config = dict(provider="blueprint-v1", blueprint_sha256=prepared.digest,
                      version="pontius-decision-provider-config-v1")
        identity = ProviderIdentity("blueprint-v1", canonical_sha256(config))
        object.__setattr__(self, "_blueprint", prepared)
        object.__setattr__(self, "_identity", identity)

    @property
    def identity(self) -> ProviderIdentity:
        return own_value(self._identity)

    def propose(self, observation: DecisionObservation) -> DecisionProposal:
        if type(observation) is not DecisionObservation:
            raise TypeError("provider requires an exact observation")
        result = PreparedBlueprint.action_for(
            self._blueprint, cards=observation.cards, betting=observation.betting,
            decision=observation.decision)
        return DecisionProposal(observation.decision_sha256, result.action,
                                "blueprint_hit" if result.table_hit else "blueprint_default")
