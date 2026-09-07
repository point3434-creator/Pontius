"""Exact provider decision wire records, separate from the sealed v1 trace."""
from __future__ import annotations

from pontius.decision_provider.model import (
    PROPOSAL_REASONS, PROVIDER_OUTCOMES, SELECTION_REASONS,
    ProviderDecisionRecord, own_value, require_label,
)
from pontius.v0a.model import FailureCode, HandAction
from pontius.v0a.trace import (
    _TIMING_KEYS, _require_digest, _require_int, _require_text, _validate_action, _validate_timing,
    action_payload, preparation_payload, timing_payload,
)

FIELDS = frozenset(ProviderDecisionRecord.__dataclass_fields__)


def _keys(value, fields):
    if (type(value) is not dict or any(type(key) is not str for key in value)
            or set(value) != set(fields)):
        raise ValueError("provider object has incorrect fields")


def decision_payload(record):
    if type(record) is not ProviderDecisionRecord:
        raise TypeError("requires an exact provider record")
    record = own_value(record)
    payload = {name: getattr(record, name) for name in FIELDS}
    for name in ("fallback_action", "selected_action", "applied_action", "delivered_action"):
        value = payload[name]
        payload[name] = None if value is None else action_payload(value)
    proposal = record.proposal
    payload["proposal"] = None if proposal is None else {
        "decision_sha256": proposal.decision_sha256,
        "action": None if proposal.action is None else action_payload(
            HandAction.from_betting_action(proposal.action)), "reason": proposal.reason}
    payload["delivery_status"] = record.delivery_status.value
    payload["failure_reason"] = (
        None if record.failure_reason is None else record.failure_reason.value)
    payload["timing"] = timing_payload(record.timing)
    payload["preparation_use"] = preparation_payload(record.preparation_use)
    return validate_decision(payload)


def validate_decision(payload):
    """Validate a parsed v2 decision; transport owns raw JSON/frame admission."""
    _keys(payload, FIELDS)
    require_label(payload["schema_version"], ("pontius-provider-decision-v1",))
    require_label(payload["provider"], ("baseline-rules-v1",))
    _require_text(payload["hand_id"], label="hand id")
    for name in ("event_index", "action_index", "street_action_index"):
        _require_int(payload[name], label=name, minimum=0 if name == "event_index" else 1)
    _require_int(payload["seat"], label="seat", minimum=0, maximum=5)
    require_label(payload["street"], ("preflop", "flop", "turn", "river"))
    for name in FIELDS:
        if name.endswith("_sha256"):
            if name != "state_after_sha256" or payload[name] is not None:
                _require_digest(payload[name], label=name)
    for name in ("fallback_action", "selected_action", "applied_action", "delivered_action"):
        if name in ("applied_action", "delivered_action") and payload[name] is None:
            continue
        _keys(payload[name], ("kind", "raise_to"))
        _validate_action(payload[name], label=name)
    require_label(payload["fallback_reason"], ("table_hit", "passive_default"))
    outcome, reason, origin = (payload[name] for name in (
        "provider_outcome", "selection_reason", "selection_origin"))
    require_label(outcome, PROVIDER_OUTCOMES)
    require_label(reason, SELECTION_REASONS)
    require_label(origin, ("provider", "blueprint_fallback"))
    proposal = payload["proposal"]
    if proposal is not None:
        _keys(proposal, ("decision_sha256", "action", "reason"))
        _require_digest(proposal["decision_sha256"], label="proposal digest")
        require_label(proposal["reason"], PROPOSAL_REASONS)
        if (proposal["action"] is None) != (proposal["reason"] == "abstain"):
            raise ValueError("abstention action and reason differ")
        if proposal["action"] is not None:
            _keys(proposal["action"], ("kind", "raise_to"))
            _validate_action(proposal["action"], label="proposal action")
    if outcome in ("not_called", "error") and proposal is not None:
        raise ValueError("unavailable provider output cannot carry a proposal")
    if outcome in ("proposed", "abstained"):
        if (proposal is None or proposal["decision_sha256"] != payload["decision_sha256"]
                or (proposal["action"] is None) != (outcome == "abstained")):
            raise ValueError("provider outcome contradicts proposal")
    expected = {"provider_selected": "proposed", "provider_abstained": "abstained",
                "provider_invalid": "invalid", "provider_error": "error",
                "provider_skipped_cutoff": "not_called"}
    if reason != "provider_late" and outcome != expected[reason]:
        raise ValueError("selection reason contradicts provider outcome")
    if reason == "provider_late" and outcome == "not_called":
        raise ValueError("a skipped provider cannot return late")
    if (origin == "provider") != (reason == "provider_selected"):
        raise ValueError("selection origin contradicts reason")
    expected_action = proposal["action"] if origin == "provider" else payload["fallback_action"]
    if payload["selected_action"] != expected_action:
        raise ValueError("selected action contradicts selection")
    applied, delivered = payload["applied_action"], payload["delivered_action"]
    if (applied is None) != (payload["state_after_sha256"] is None):
        raise ValueError("application and resulting state disagree")
    if applied is not None and applied != payload["selected_action"]:
        raise ValueError("applied action contradicts selection")
    status = payload["delivery_status"]
    require_label(status, ("not_attempted", "rejected", "accepted", "unknown"))
    if (delivered is not None) != (status == "accepted"):
        raise ValueError("confirmed delivery and status disagree")
    if status != "not_attempted" and applied is None:
        raise ValueError("delivery requires local application")
    if delivered is not None and delivered != applied:
        raise ValueError("confirmed delivery contradicts local application")
    timing, failure = payload["timing"], payload["failure_reason"]
    if type(timing) is not dict:
        raise ValueError("provider decision requires timing")
    _keys(timing, _TIMING_KEYS)
    _validate_timing(timing, label="provider decision")
    preparation = payload["preparation_use"]
    _keys(preparation, ("producer_status", "artifact_sha256s", "credited_seconds"))
    require_label(preparation["producer_status"], ("producer_absent",))
    if (type(preparation["artifact_sha256s"]) is not list or preparation["artifact_sha256s"]
            or type(preparation["credited_seconds"]) is not int
            or preparation["credited_seconds"] != 0):
        raise ValueError("preparation credit must remain absent")
    if failure is not None:
        require_label(failure, tuple(code.value for code in FailureCode))
    if reason in ("provider_late", "provider_skipped_cutoff"):
        if timing["work_cutoff_crossed"] is not True or failure is None:
            raise ValueError("late or skipped fallback must retain cutoff failure")
    if timing["status"] == "completed":
        if timing["work_cutoff_crossed"] and reason not in (
                "provider_late", "provider_skipped_cutoff"):
            raise ValueError("completed work cutoff requires late or skipped fallback")
        expected_failure = ("action_deadline_exceeded" if timing["deadline_crossed"]
                            else "work_cutoff_exceeded" if timing["work_cutoff_crossed"] else None)
        if failure != expected_failure or status != "accepted":
            raise ValueError("completed timing contradicts delivery or failure")
    elif failure != timing["interruption_reason"]:
        raise ValueError("interrupted timing contradicts failure")
    return payload
