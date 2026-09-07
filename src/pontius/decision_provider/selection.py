"""Engine-side structural projection, decision binding, and legal selection."""
from __future__ import annotations

from pontius.decision_provider.model import (
    DecisionObservation, DecisionProposal, Selection, own_value, require_label,
)
from pontius.immutable_blueprint import require_legal_blueprint_action
from pontius.no_limit_betting import BettingAction


def resolve_proposal(observation, proposal, fallback_action, fallback_reason):
    if type(observation) is not DecisionObservation or type(fallback_action) is not BettingAction:
        raise TypeError('engine context and fallback must be exact')
    observation = DecisionObservation(**{name: getattr(observation, name) for name in (
        'version', 'hand_id', 'action_index', 'cards', 'betting', 'decision', 'remaining_work_ns')})
    fallback = own_value(fallback_action)
    require_label(fallback_reason, ('table_hit', 'passive_default'))
    require_legal_blueprint_action(fallback, observation.decision)
    safe, outcome = None, 'invalid'
    try:
        if type(proposal) is DecisionProposal:
            safe = own_value(proposal)
    except (TypeError, ValueError, AttributeError, RecursionError):
        pass
    if safe is not None and safe.decision_sha256 == observation.decision_sha256:
        if safe.action is None:
            outcome = 'abstained'
        else:
            try:
                require_legal_blueprint_action(safe.action, observation.decision)
            except (TypeError, ValueError):
                pass
            else:
                return Selection(safe, 'proposed', 'provider_selected', 'provider', safe.action)
    return Selection(safe, outcome, 'provider_' + outcome, 'blueprint_fallback', fallback)
