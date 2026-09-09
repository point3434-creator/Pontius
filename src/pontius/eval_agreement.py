"""Classify one retained host attempt; settlement and agreement are separate gates."""
from __future__ import annotations

import base64
import binascii
import json
import math

from .blueprint_preparation.lookup import PreparedBlueprint
from .eval_bridge import hand_name, replay_root, root_key
from .holdem_cards import OneSeatCardState, SixSeatHoldemDeal
from .legal_decision_spine_v2 import public_betting_state_sha256
from .no_limit_betting import NoLimitBettingState, TerminalReason
from .v0a.model import (DecisionRecord, HandAction, PreparationUseRecord, SelectionReason,
                        TimingRecord, TimingStatus, visible_cards_sha256)

WIRE_FIELDS = {
    'ready': 'source_commit source_manifest_sha256 blueprint_artifact_sha256 '
             'blueprint_sha256 evidentiary',
    'action': 'hand_id action_index seat street action',
    'event_result': 'event_index status decision failure',
    'hand_result': 'complete settlement rank_source evidentiary preparation_compute_seconds '
                   'post_terminal_compute_seconds interrupted_response_count accounting_complete '
                   'failure_reason secondary_failures',
    'session_result': 'status terminal_publication_compute_seconds accounting_complete '
                      'failure_reason secondary_failures accounting_scope evidentiary',
}


class Unusable(ValueError):
    """An observation failed before it could enter the agreement denominator."""


def require(condition, cause):
    if not condition:
        raise Unusable(cause)


def clean(value, label):
    require(type(value) is dict, label + ':missing')
    secondary = [] if label == 'decision' else value['secondary_failures']
    causes = [value['failure_reason'], *secondary]
    require(value['failure_reason'] is None and secondary == [],
            label + ':' + ','.join(str(v) for v in causes if v is not None))


def seconds(value):
    return type(value) is float and math.isfinite(value) and value >= 0


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'wire:duplicate_key')
        result[key] = value
    return result


def reject_constant(value):
    raise Unusable('wire:nonfinite:' + value)


def finite_float(value):
    parsed = float(value)
    require(math.isfinite(parsed), 'wire:nonfinite')
    return parsed


def bind_identity(ready, hand, report):
    version = ready['protocol'][-2:]
    prefix = 'pontius-v0a-table-session-' + version + '-correctness-'
    require(report['version'] == 'pontius-v0a-table-session-result-' + version
            and type(report['session_id']) is str and report['session_id'].startswith(prefix),
            'wire:outer_session_identity')
    suffix = report['session_id'][len(prefix):] + '-h01'
    require(hand['version'] == 'pontius-v0a-table-session-hand-result-' + version
            and hand['session_id'] == 'pontius-v0a-table-host-' + version + '-correctness-' + suffix
            and ready['session_id'] == ready['protocol'] + '-correctness-table-' + suffix,
            'wire:child_session_identity')
    for field in ('source_commit', 'blueprint_artifact_sha256', 'blueprint_sha256'):
        require(ready[field] == hand[field] == report[field], 'wire:identity_mismatch:' + field)
    # Session envelopes do not retain the manifest hash; admission owns that comparison.
    for field, length in (('source_commit', 40), ('source_manifest_sha256', 64),
                          ('blueprint_artifact_sha256', 64)):
        value = ready[field]
        require(type(value) is str and len(value) == length
                and all(char in '0123456789abcdef' for char in value),
                'wire:identity_shape:' + field)


def frames_for(hand, blueprint, report):
    raw = base64.b64decode(hand['child_stdout_base64'], validate=True)
    require(raw and raw.endswith(b'\n'), 'wire:incomplete_frame')
    frames = [json.loads(line, object_pairs_hook=unique_object, parse_constant=reject_constant,
                          parse_float=finite_float)
              for line in raw.decode('utf-8').splitlines()]
    require(len(frames) >= 3 and all(type(row) is dict for row in frames), 'wire:shape')
    ready, terminal, closing = frames[0], frames[-2], frames[-1]
    require(ready['type'] == 'ready' and terminal['type'] == 'hand_result'
            and closing['type'] == 'session_result', 'wire:missing_terminal_closure')
    protocol, identity = ready['protocol'], ready['session_id']
    require(protocol in ('pontius-v0a-event-interface-v1', 'pontius-v0a-event-interface-v2')
            and type(identity) is str and bool(identity), 'wire:identity')
    require(ready['blueprint_sha256'] == blueprint.digest
            and hand['blueprint_sha256'] == blueprint.digest, 'wire:blueprint_identity')
    bind_identity(ready, hand, report)
    for row in frames:
        kind = row['type']
        require(kind in WIRE_FIELDS, 'wire:unexpected_frame')
        fields = set(('protocol session_id type ' + WIRE_FIELDS[kind]).split())
        if protocol.endswith('v2') and kind == 'ready':
            fields.update(('provider', 'config_sha256'))
        require(set(row) == fields, 'wire:frame_fields')
    require(all(row['protocol'] == protocol and row['session_id'] == identity
                for row in frames), 'wire:identity')
    events, pending = [], None
    for row in frames[1:-2]:
        if row['type'] == 'action':
            require(pending is None, 'wire:duplicate_action')
            pending = row
            continue
        require(row['type'] == 'event_result', 'wire:unexpected_frame')
        require(type(row['event_index']) is int and row['event_index'] == len(events),
                'wire:event_index')
        require(row['status'] in ('accepted', 'decided') and row['failure'] is None,
                'wire:event_failed:' + str(row['failure']))
        record = row['decision']
        require((row['status'] == 'decided') == (record is not None), 'wire:decision_status')
        require((pending is not None) == (record is not None), 'wire:missing_action_or_decision')
        if record is not None:
            clean(record, 'decision')
            require(record['event_index'] == row['event_index'] and record['hand_id'] == identity,
                    'wire:decision_identity')
            require(all(pending[k] == record[k]
                        for k in ('hand_id', 'action_index', 'seat', 'street'))
                    and pending['action'] == record['selected_action'], 'wire:action_mismatch')
            timing = dict(record['timing'])
            timing['status'] = TimingStatus(timing['status'])
            parsed = TimingRecord(**timing)
            require(parsed.status is TimingStatus.COMPLETED and not parsed.work_cutoff_crossed
                    and not parsed.deadline_crossed and parsed.elapsed_ns <= 15_000_000_000,
                    'wire:decision_timing')
            require(abs(parsed.response_compute_seconds + parsed.response_uninstrumented_seconds
                        - parsed.elapsed_ns / 1e9) <= 2e-9, 'wire:decision_timing')
            if protocol.endswith('v1'):
                prep = dict(record['preparation_use'])
                prep['artifact_sha256s'] = tuple(prep['artifact_sha256s'])
                DecisionRecord(**dict(record, timing=parsed,
                    selected_action=HandAction(**record['selected_action']),
                    preparation_use=PreparationUseRecord(**prep),
                    selection_reason=SelectionReason.PASSIVE_DEFAULT))
            if protocol.endswith('v2'):
                require(record['delivery_status'] == 'accepted'
                        and record['delivered_action'] == record['applied_action']
                        == record['selected_action'], 'wire:delivery')
        events.append(row)
        pending = None
    require(pending is None, 'wire:unpaired_action')
    for label, row in (('hand', terminal), ('closure', closing)):
        clean(row, label)
        require(row['accounting_complete'] is True and row['evidentiary'] is False,
                label + ':unaccounted')
    require(terminal['complete'] is True and terminal['interrupted_response_count'] == 0
            and seconds(terminal['preparation_compute_seconds'])
            and seconds(terminal['post_terminal_compute_seconds']), 'hand:incomplete')
    require(closing['status'] == 'completed'
            and closing['accounting_scope'] == 'runtime_begin_to_final_publication'
            and seconds(closing['terminal_publication_compute_seconds']), 'closure:incomplete')
    require(hand['settlement'] is not None and
            json.dumps(terminal['settlement'], sort_keys=True)
            == json.dumps(hand['settlement'], sort_keys=True),
            'hand:settlement_missing_or_mismatched')
    return events, terminal


def replay(hand, entry, deal, stacks):
    require(entry['button'] == 0 and entry['starting_stacks'] == [stacks] * 6,
            'replay:initial_state')
    state = NoLimitBettingState.new_hand(button=0, starting_stacks=(stacks,) * 6,
                                         small_blind=1, big_blind=2)
    expected, event_index, street_index = [], 0, 0
    for index, row in enumerate(hand['applied_actions']):
        while state.round_complete and not state.is_terminal:
            state = state.advance_street()
            event_index += 1
            street_index = 0
        require(row['index'] == index and row['seat'] == state.acting_seat
                and row['street'] == state.street.value, 'replay:action_order')
        seat = state.acting_seat
        require(row['origin'] == ('bot' if seat == 2 else 'opponent'), 'replay:origin')
        action = HandAction(**row['action']).to_betting_action()
        before, state = state, state.apply_action(action)
        if seat != 2:
            event_index += 1
            continue
        street_index += 1
        cards = OneSeatCardState(2, deal.hand(2), before.street, deal.public_cards(before.street))
        expected.append(dict(state=before, cards=cards, action=action,
                             fields=dict(event_index=event_index, action_index=len(expected) + 1,
                                         street_action_index=street_index, seat=2,
                                         street=before.street.value,
                                         state_before_sha256=public_betting_state_sha256(before),
                                         state_after_sha256=public_betting_state_sha256(state),
                                         visible_cards_sha256=visible_cards_sha256(cards))))
    while state.round_complete and not state.is_terminal:
        previous_street = state.street
        state = state.advance_street()
        event_index += state.street != previous_street
    require(state.is_terminal, 'replay:not_terminal')
    showdown = state.terminal_reason is not TerminalReason.FOLD
    event_index += showdown  # The host always publishes a separate showdown_result.
    strengths = deal.showdown_strengths(state.live_seats) if showdown else None
    settled = state.settle(strengths)
    settlement = dict(payouts=list(settled.payouts), final_stacks=list(settled.final_stacks),
                      pots=[dict(amount=p.amount, seats=list(p.eligible_seats))
                            for p in settled.side_pots])
    require(json.dumps(hand['settlement'], sort_keys=True)
            == json.dumps(settlement, sort_keys=True),
            'replay:settlement_mismatch')
    return expected, settled.net_returns[2], event_index, showdown


def classify(session_report, *, blueprint, teacher_actions, board, private_hands,
             stacks=4, strategy='blueprint-v1'):
    """One scheduled single-hand Session report, including failed or absent outcomes.

    Caller inputs bind the actual deal and frozen teacher. Successful transport is
    taken only from retained host envelopes; card settlement and lookup are replayed.
    Constructed reports test this classifier, not the host's transport boundary.
    """
    prepared = PreparedBlueprint(blueprint)
    require(type(board) is tuple and board == tuple(sorted(board)), 'input:board_order')
    deal = SixSeatHoldemDeal(private_hands, board)
    name = hand_name(deal.hand(2))
    result = dict(chip_eligible=False, chips=None, agreement_eligible=False,
                  classification='excluded', causes=[], river_hand=name,
                  observed_table_hits=None, river_records=None)
    try:
        clean(session_report, 'session')
        require(session_report['status'] == 'completed'
                and session_report['stop_reason'] is None, 'session:not_completed')
        require(session_report['requested_hands'] == 1 and session_report['completed_hands'] == 1
                and len(session_report['hands']) == 1, 'session:missing_or_extra_outcome')
        entry = session_report['hands'][0]
        require(entry['ordinal'] == 1, 'session:ordinal')
        hand = entry['result']
        clean(hand, 'outcome')
        require(hand['status'] == 'completed', 'outcome:not_completed')
        require(hand['capture_truncated'] is False and type(hand['child_exit_code']) is int
                and hand['child_exit_code'] == 0, 'outcome:truncated_or_failed_child')
        events, terminal = frames_for(hand, prepared, session_report)
        expected, chips, final_event, showdown = replay(hand, entry, deal, stacks)
        require(len(events) == final_event + 1, 'wire:event_count')
        require(terminal['rank_source'] == ('host_supplied' if showdown else 'not_required'),
                'hand:rank_source')
    except (ValueError, TypeError, KeyError, IndexError, binascii.Error) as error:
        result['causes'] = [str(error)]
        return result
    records = [row['decision'] for row in events if row['decision'] is not None]
    result.update(chip_eligible=True, chips=chips, classification='unsupported',
                  observed_table_hits=sum(row.get('selection_reason') == 'table_hit'
                                          for row in records),
                  river_records=sum(row.get('street') == 'river' for row in records))
    if strategy != 'blueprint-v1':
        result['causes'] = ['agreement:baseline_outside_declared_root']
        return result
    causes, rivers = [], []
    if len(records) != len(expected):
        causes.append('agreement:controlled_decision_count')
    for index, record in enumerate(records):
        if index >= len(expected):
            break
        replayed = expected[index]
        if any(record.get(k) != value for k, value in replayed['fields'].items()):
            causes.append('agreement:replayed_state_mismatch')
        selection = prepared.action_for(cards=replayed['cards'], betting=replayed['state'],
                                        decision=replayed['state'].legal_decision())
        reason = 'table_hit' if selection.table_hit else 'passive_default'
        selected = HandAction(**record['selected_action']).to_betting_action()
        if selected != replayed['action'] or selected != selection.action:
            causes.append('agreement:selected_action_mismatch')
        if (record.get('blueprint_sha256') != prepared.digest
                or record.get('selection_reason') != reason):
            causes.append('agreement:lookup_reason_or_identity_mismatch')
        if record.get('street') == 'river':
            rivers.append((selection, selected))
        elif record.get('selection_reason') != 'passive_default':
            causes.append('agreement:nonpassive_preriver')
    if len(rivers) != 1:
        causes.append('agreement:river_decision_count:' + str(len(rivers)))
    else:
        selection, selected = rivers[0]
        declared = root_key(replay_root(), board, deal.hand(2))
        result['agreement_eligible'] = selection.key == declared
        if result['agreement_eligible']:
            teacher = teacher_actions.get(name)
            if teacher is None:
                if selection.table_hit:
                    causes.append('agreement:hit_outside_teacher_pool')
            elif not selection.table_hit or selected != teacher:
                causes.append('agreement:teacher_disagreement')
            elif not causes:
                result['classification'] = 'hit'
        elif selection.table_hit:
            causes.append('agreement:hit_outside_declared_root')
    if causes:
        result['classification'] = 'disagreement'
    result['causes'] = list(dict.fromkeys(causes))
    return result


def summarize(results, scheduled):
    """Reconcile exactly one disposition per observed attempt; missing stays visible."""
    require(type(scheduled) is int and scheduled >= 0 and len(results) <= scheduled,
            'summary:invalid_scheduled_count')
    counts = {label: 0 for label in ('hit', 'disagreement', 'unsupported', 'excluded')}
    for result in results:
        require(result['classification'] in counts, 'summary:invalid_classification')
        counts[result['classification']] += 1
    missing = scheduled - len(results)
    return dict(scheduled=scheduled, observed=len(results), missing=missing,
                completed=sum(row.get('chip_eligible', False) for row in results),
                agreement_eligible=sum(row.get('agreement_eligible', False) for row in results),
                hits=counts['hit'], disagreements=counts['disagreement'],
                unsupported=counts['unsupported'], excluded=counts['excluded'],
                complete=not (missing or counts['disagreement'] or counts['excluded']))
