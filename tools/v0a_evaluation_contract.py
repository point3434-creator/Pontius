"""Pure canonical planning and bounded observations; confers no execution authority."""
from __future__ import annotations
import base64
import hashlib
import json
import math
import re

POLICIES = ('passive', 'fold_to_bet', 'min_raise_once', 'shove_once')
STRATEGIES = ('baseline-rules-v1', 'blueprint-v1')
FAILURES = ('invalid_event event_order invalid_decision_context invalid_blueprint_entry '
            'clock_invalid clock_reversed work_cutoff_exceeded action_deadline_exceeded '
            'delivery_rejected delivery_ambiguous trace_write_failed trace_invalid '
            'settlement_mismatch source_binding_mismatch authority_absent').split()
DELIVERY = ('not_attempted', 'rejected', 'accepted', 'unknown')
STREETS = ('preflop', 'flop', 'turn', 'river')
TIMING = ('status interruption_reason wall_start_ns last_valid_observation_ns '
          'emission_observed_ns elapsed_ns response_compute_seconds '
          'response_uninstrumented_seconds '
          'work_cutoff_crossed deadline_crossed')
DECISION = ('hand_id event_index action_index street_action_index seat street state_before_sha256 '
            'state_after_sha256 visible_cards_sha256 selected_action timing preparation_use '
            'failure_reason ')
V2 = ('schema_version decision_sha256 source_manifest_sha256 provider config_sha256 '
      'fallback_blueprint_sha256 fallback_action fallback_reason proposal provider_outcome '
      'selection_reason selection_origin applied_action delivery_status delivered_action')
WIRE = {'ready': 'source_commit source_manifest_sha256 blueprint_artifact_sha256 '
                'blueprint_sha256 evidentiary',
        'action': 'hand_id action_index seat street action',
        'event_result': 'event_index status decision failure',
        'hand_result': 'complete settlement rank_source evidentiary preparation_compute_seconds '
                       'post_terminal_compute_seconds interrupted_response_count '
                       'accounting_complete '
                       'failure_reason secondary_failures',
        'session_result': 'status terminal_publication_compute_seconds accounting_complete '
                          'failure_reason secondary_failures accounting_scope evidentiary'}
IDENTITY = 'source_commit blueprint_artifact_sha256 blueprint_sha256'
COMMON = 'version session_id status failure_reason secondary_failures input_sha256 ' + IDENTITY
OUTER = COMMON + (' stop_reason requested_hands completed_hands next_button carried_stacks hands')
HAND = COMMON + (' applied_actions settlement child_exit_code child_stdout_base64 '
                 'child_stderr_base64 capture_truncated')


def require(condition, code='schema_invalid'):
    if not condition:
        raise ValueError(code)


def integer(value, low=0, high=10**640 - 1):
    return type(value) is int and low <= value <= high


def exact(value, fields):
    require(type(value) is dict and set(value) == set(fields.split()))
    return value


def label(value, choices):
    require(type(value) is str and value in choices)


def digest(value):
    require(type(value) is str and re.fullmatch('[0-9a-f]{64}', value))


def seconds(value):
    require(type(value) is float and math.isfinite(value) and value >= 0)


def encode(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True,
                       allow_nan=False) + '\n').encode('utf-8')


def decode(raw, cap, depth_limit, digits, floats=True):
    def number(token):
        require(len(token.lstrip('-')) <= digits)
        return int(token)
    def reject(token):
        raise ValueError('number_invalid')
    def pairs(items):
        value = {}
        for key, item in items:
            require(key not in value, 'duplicate_key')
            value[key] = item
        return value
    require(type(raw) is bytes and 0 < len(raw) <= cap and b'\r' not in raw
            and not raw.startswith(b'\xef\xbb\xbf'), 'capture_invalid')
    depth, quoted, escaped = 0, False, False
    for byte in raw:
        if quoted:
            if escaped:
                escaped = False
            elif byte == 92:
                escaped = True
            elif byte == 34:
                quoted = False
        elif byte == 34:
            quoted = True
        elif byte in (91, 123):
            depth += 1
            require(depth <= depth_limit, 'depth_exceeded')
        elif byte in (93, 125):
            depth -= 1
    return json.loads(raw.decode('utf-8'), parse_int=number, object_pairs_hook=pairs,
                      parse_float=float if floats else reject, parse_constant=reject)


def decode_request(raw: bytes) -> dict:
    value = exact(decode(raw, 4096, 4, 8, False), 'version seed deal_count lineups '
                  'seat_start initial_button total_budget_ms trial_budget_ms')
    require(value['version'] == 'pontius-v0a-evaluation-request-v1')
    digest(value['seed'])
    for key, low, high in (('deal_count', 1, 4), ('seat_start', 0, 5),
                          ('initial_button', 0, 5), ('trial_budget_ms', 1, 3600000),
                          ('total_budget_ms', 1, 86400000)):
        require(integer(value[key], low, high))
    require(value['total_budget_ms'] >= value['trial_budget_ms'] + 5000)
    lineups = value['lineups']
    require(type(lineups) is list and 1 <= len(lineups) <= 4)
    for lineup in lineups:
        require(type(lineup) is list and len(lineup) == 5)
        for policy in lineup:
            label(policy, POLICIES)
    require(len({tuple(lineup) for lineup in lineups}) == len(lineups))
    require(encode(value) == raw, 'noncanonical_request')
    return value


def build_matrix(request: dict, deals: list, suffix: str) -> dict:
    request = decode_request(encode(request))
    require(type(suffix) is str and re.fullmatch('[A-Za-z0-9_-]{1,16}', suffix))
    require(type(deals) is list and len(deals) == request['deal_count'])
    pairs, units = [], []
    for d, deal in enumerate(deals):
        exact(deal, 'private_hands board_runout')
        require(type(deal['private_hands']) is list and len(deal['private_hands']) == 6)
        require(all(type(pair) is list and len(pair) == 2 for pair in deal['private_hands']))
        require(type(deal['board_runout']) is list and len(deal['board_runout']) == 5)
        cards = sum(deal['private_hands'], []) + deal['board_runout']
        require(all(integer(card, 0, 51) for card in cards) and len(set(cards)) == 17)
        for l, lineup in enumerate(request['lineups']):
            for r in range(6):
                p, s = len(pairs), (request['seat_start'] + r) % 6
                b = (request['initial_button'] + d) % 6
                opponents = [None] * 6
                for j, policy in enumerate(lineup):
                    opponents[(s + 1 + j) % 6] = policy
                data = encode(dict(version='pontius-v0a-table-session-v1', hands=[deal],
                    button=b, controlled_seat=s, starting_stacks=[200] * 6,
                    small_blind=1, big_blind=2, opponents=opponents))
                common = dict(pair_index=p, input_path='pairs/p%03d.json' % p,
                              input_sha256=hashlib.sha256(data).hexdigest())
                pairs.append(dict(common, deal_index=d, lineup_index=l, rotation=r,
                                  controlled_seat=s, button=b, input_bytes=data))
                for strategy in STRATEGIES if p % 2 == 0 else STRATEGIES[::-1]:
                    u, v = len(units) + 1, 2 if strategy == STRATEGIES[0] else 1
                    units.append(dict(common, ordinal=u, strategy=strategy, session_id=
                        'pontius-v0a-table-session-v%d-correctness-eval-%s-u%03d' % (v, suffix, u)))
    return dict(pairs=pairs, units=units)


def action(value):
    exact(value, 'kind raise_to')
    label(value['kind'], ('fold', 'check', 'call', 'raise'))
    require(integer(value['raise_to'], 1) if value['kind'] == 'raise'
            else value['raise_to'] is None)


def timing(value):
    exact(value, TIMING)
    label(value['status'], ('completed', 'interrupted'))
    start, last = value['wall_start_ns'], value['last_valid_observation_ns']
    require(integer(start) and integer(last, start))
    fields = ('emission_observed_ns elapsed_ns response_compute_seconds '
              'response_uninstrumented_seconds')
    if value['status'] == 'completed':
        require(value['interruption_reason'] is None and integer(value['emission_observed_ns'])
                and value['emission_observed_ns'] == last and integer(value['elapsed_ns'])
                and value['elapsed_ns'] == last - start)
        for key in fields.split()[2:]:
            seconds(value[key])
        require(all(type(value[k]) is bool for k in ('work_cutoff_crossed', 'deadline_crossed')))
    else:
        label(value['interruption_reason'], FAILURES)
        require(all(value[k] is None for k in fields.split()))
        require(all(value[k] is None or value[k] is True
                    for k in ('work_cutoff_crossed', 'deadline_crossed')))


def failure(value, child, event):
    exact(value, 'hand_id event_index action_index code delivery_status delivered_action timing')
    require(value['hand_id'] is None or value['hand_id'] == child)
    require(value['event_index'] is None or integer(value['event_index'])
            and value['event_index'] == event)
    require(value['action_index'] is None or integer(value['action_index'], 1))
    label(value['code'], FAILURES)
    label(value['delivery_status'], DELIVERY)
    if value['delivered_action'] is not None:
        action(value['delivered_action'])
        require(value['delivery_status'] == 'accepted')
    if value['timing'] is not None:
        timing(value['timing'])


def decision(value, binding, child, event, baseline):
    exact(value, DECISION + (V2 if baseline else 'blueprint_sha256 selection_reason spine_reason'))
    require(value['hand_id'] == child and integer(value['event_index'])
            and value['event_index'] == event and integer(value['action_index'], 1)
            and integer(value['street_action_index'], 1)
            and integer(value['seat'], 0, 5) and value['seat'] == binding['controlled_seat'])
    label(value['street'], STREETS)
    for key in value:
        if key.endswith('_sha256') and not (key == 'state_after_sha256' and value[key] is None):
            digest(value[key])
    action(value['selected_action'])
    timing(value['timing'])
    prep = exact(value['preparation_use'], 'producer_status artifact_sha256s credited_seconds')
    require(prep['producer_status'] == 'producer_absent' and type(prep['artifact_sha256s']) is list
            and prep['artifact_sha256s'] == [] and integer(prep['credited_seconds'], 0, 0))
    require(value['failure_reason'] is None or value['failure_reason'] in FAILURES)
    if not baseline:
        label(value['selection_reason'], ('table_hit', 'passive_default'))
        label(value['spine_reason'], ('candidate', 'no_candidate', 'illegal_candidate',
                                     'work_budget_exhausted', 'action_deadline_crossed'))
        require(value['blueprint_sha256'] == binding['blueprint_sha256'])
        require(value['state_after_sha256'] is not None and value['failure_reason'] is None)
        return
    require(value['schema_version'] == 'pontius-provider-decision-v1')
    for key in ('provider', 'config_sha256'):
        require(value[key] == binding[key])
    require(value['provider'] == 'baseline-rules-v1'
            and value['source_manifest_sha256'] == binding['child_source_manifest_sha256']
            and value['fallback_blueprint_sha256'] == binding['blueprint_sha256'])
    for key in ('fallback_action', 'applied_action', 'delivered_action'):
        if value[key] is not None or key == 'fallback_action':
            action(value[key])
    label(value['fallback_reason'], ('table_hit', 'passive_default'))
    outcome, reason, origin = (value[k] for k in (
        'provider_outcome', 'selection_reason', 'selection_origin'))
    expected = dict(provider_selected='proposed', provider_abstained='abstained',
                    provider_invalid='invalid', provider_error='error',
                    provider_skipped_cutoff='not_called')
    label(outcome, ('not_called', 'proposed', 'abstained', 'error', 'invalid'))
    label(reason, (*expected, 'provider_late'))
    label(origin, ('provider', 'blueprint_fallback'))
    proposal = value['proposal']
    if proposal is not None:
        exact(proposal, 'decision_sha256 action reason')
        digest(proposal['decision_sha256'])
        label(proposal['reason'], ('abstain', 'blueprint_hit', 'blueprint_default', 'premium_raise',
            'premium_call', 'playable_call', 'made_hand_raise', 'made_hand_call',
            'pair_call', 'free_check', 'weak_fold'))
        require((proposal['action'] is None) == (proposal['reason'] == 'abstain'))
        if proposal['action'] is not None:
            action(proposal['action'])
    require(outcome not in ('not_called', 'error') or proposal is None)
    if outcome in ('proposed', 'abstained'):
        require(proposal is not None and proposal['decision_sha256'] == value['decision_sha256']
                and (proposal['action'] is None) == (outcome == 'abstained'))
    require(outcome != 'not_called' if reason == 'provider_late' else outcome == expected[reason])
    require((origin == 'provider') == (reason == 'provider_selected'))
    require(value['selected_action'] == (proposal['action'] if origin == 'provider'
                                        else value['fallback_action']))
    applied, delivered, status = (value[k] for k in (
        'applied_action', 'delivered_action', 'delivery_status'))
    label(status, DELIVERY)
    require((applied is None) == (value['state_after_sha256'] is None)
            and (applied is None or applied == value['selected_action'])
            and (delivered is not None) == (status == 'accepted')
            and (status == 'not_attempted' or applied is not None)
            and (delivered is None or delivered == applied))
    t, cause = value['timing'], value['failure_reason']
    if reason in ('provider_late', 'provider_skipped_cutoff'):
        require(t['work_cutoff_crossed'] is True and cause is not None)
    if t['status'] == 'completed':
        require(not t['work_cutoff_crossed']
                or reason in ('provider_late', 'provider_skipped_cutoff'))
        expected_cause = ('action_deadline_exceeded' if t['deadline_crossed'] else
                          'work_cutoff_exceeded' if t['work_cutoff_crossed'] else None)
        require(cause == expected_cause and status == 'accepted')
    else:
        require(cause == t['interruption_reason'])


def causes(row, wire=False):
    primary, secondary = row['failure_reason'], row['secondary_failures']
    require(primary is None or type(primary) is str and bool(primary))
    require(type(secondary) is list and all(type(c) is str and bool(c) for c in secondary)
            and len(set(secondary)) == len(secondary) and primary not in secondary
            and (primary is not None or not secondary))
    result = ([primary] if primary is not None else []) + secondary
    require(not wire or all(c in FAILURES for c in result))
    return result


def settlement(value):
    exact(value, 'payouts final_stacks pots')
    for key in ('payouts', 'final_stacks'):
        require(type(value[key]) is list and len(value[key]) == 6
                and all(integer(v, 0, 1000000) for v in value[key]))
    require(sum(value['final_stacks']) == 1200 and type(value['pots']) is list
            and len(value['pots']) <= 6)
    for pot in value['pots']:
        exact(pot, 'amount seats')
        require(integer(pot['amount'], 1, 1000000) and type(pot['seats']) is list
                and 1 <= len(pot['seats']) <= 6 and all(integer(s, 0, 5) for s in pot['seats'])
                and pot['seats'] == sorted(set(pot['seats'])))
    require(sum(value['payouts']) == sum(p['amount'] for p in value['pots']))


def increment(counter, key):
    counter[key] = counter.get(key, 0) + 1


def observe_trial(binding: dict, stdout: bytes, stderr: bytes,
                  exit_code: int | None, capture_complete: bool) -> dict:
    result = {k: binding[k] for k in ('ordinal', 'pair_index', 'strategy')}
    result.update(state='refused', exit_code=exit_code, capture_complete=capture_complete,
        report_complete=False, net_chips=None, applied_actions_by_kind=None,
        baseline_fallback_selections=None, baseline_fallback_applied=None, legacy_choices=None,
        unattributed_applied_actions=None, work_cutoff_actions=None, action_deadline_actions=None,
        observation_complete=False, action_failures=None, failure_reason=None,
        hand_failure_codes=[], session_failure_codes=[], capture_deficiencies=[],
        stdout_sha256=hashlib.sha256(stdout).hexdigest(),
        stderr_sha256=hashlib.sha256(stderr).hexdigest())
    defects = result['capture_deficiencies']
    baseline = binding['strategy'] == STRATEGIES[0]
    v, extra = ('2', ' provider config_sha256') if baseline else ('1', '')
    suffix = binding['session_id'].removeprefix('pontius-v0a-table-session-v' + v + '-correctness-')
    child = 'pontius-v0a-event-interface-v' + v + '-correctness-table-' + suffix + '-h01'
    host = 'pontius-v0a-table-host-v' + v + '-correctness-' + suffix + '-h01'
    try:
        require(type(capture_complete) is bool and (exit_code is None or type(exit_code) is int))
        require(len(stderr) <= 65536)
        report = exact(decode(stdout, 4194304, 16, 640), OUTER + extra)
        require(report['version'] == 'pontius-v0a-table-session-result-v' + v
                and report['session_id'] == binding['session_id']
                and report['input_sha256'] == binding['input_sha256'], 'identity_mismatch')
        for key in (IDENTITY + extra).split():
            require(report[key] == binding[key], 'identity_mismatch')
        label(report['status'], ('completed', 'failed', 'interrupted', 'stopped'))
        require(report['stop_reason'] in (None, 'insufficient_stacks', 'stop', 'quit', 'eof'))
        result['session_failure_codes'] = causes(report)
        require(integer(report['requested_hands'], 1, 1)
                and integer(report['completed_hands'], 0, 1)
                and integer(report['next_button'], 0, 5) and type(report['carried_stacks']) is list
                and len(report['carried_stacks']) == 6
                and all(integer(n, 0, 1000000) for n in report['carried_stacks']))
        require(type(report['hands']) is list and len(report['hands']) == 1, 'missing_hand')
        entry = exact(report['hands'][0], 'ordinal button starting_stacks result')
        require(integer(entry['ordinal'], 1, 1) and integer(entry['button'], 0, 5)
                and entry['button'] == binding['button'] and type(entry['starting_stacks']) is list
                and len(entry['starting_stacks']) == 6
                and all(integer(n, 200, 200) for n in entry['starting_stacks']))
        hand = exact(entry['result'], HAND + extra)
        require(hand['version'] == 'pontius-v0a-table-session-hand-result-v' + v
                and hand['session_id'] == host
                and hand['input_sha256'] == binding['table_input_sha256'],
                'identity_mismatch')
        for key in (IDENTITY + extra).split():
            require(hand[key] == binding[key], 'identity_mismatch')
        label(hand['status'], ('completed', 'failed'))
        require(type(hand['capture_truncated']) is bool
                and (hand['child_exit_code'] is None or type(hand['child_exit_code']) is int))
        result['hand_failure_codes'] = causes(hand)
        require(type(hand['applied_actions']) is list and len(hand['applied_actions']) <= 256)
        bots, counts = [], {}
        for index, applied in enumerate(hand['applied_actions']):
            exact(applied, 'index seat street action origin')
            require(integer(applied['index']) and applied['index'] == index
                    and integer(applied['seat'], 0, 5))
            label(applied['street'], STREETS)
            label(applied['origin'], ('bot', 'opponent'))
            require((applied['origin'] == 'bot') == (applied['seat'] == binding['controlled_seat']))
            action(applied['action'])
            if applied['origin'] == 'bot':
                bots.append(applied)
                increment(counts, applied['action']['kind'])
        result.update(applied_actions_by_kind=counts, unattributed_applied_actions=len(bots))
        for key, cap in (('child_stdout_base64', 2097152), ('child_stderr_base64', 65536)):
            require(type(hand[key]) is str and len(hand[key]) <= ((cap + 2) // 3) * 4)
            decoded = base64.b64decode(hand[key], validate=True)
            require(len(decoded) <= cap and base64.b64encode(decoded).decode('ascii') == hand[key])
            if key == 'child_stdout_base64':
                wire = decoded
        selected, attributed, legacy, decisions, seen, timed = {}, {}, {}, {}, {}, {}
        pending, event, ready, closed, terminal = None, 0, False, False, None
        finished = False
        failures, wire_seen = [], False
        rows = wire.splitlines(keepends=True)
        for position, raw in enumerate(rows):
            try:
                require(raw.endswith(b'\n'), 'partial_frame')
                row = decode(raw, 16384, 8, 640)
                require(type(row) is dict and type(row.get('type')) is str and row['type'] in WIRE,
                        'unknown_frame')
                kind = row['type']
                exact(row, 'protocol session_id type ' + WIRE[kind]
                      + (extra if kind == 'ready' else ''))
                require(row['protocol'] == 'pontius-v0a-event-interface-v' + v
                        and row['session_id'] == child, 'identity_mismatch')
                require(not finished, 'extra_frame')
                if kind == 'ready':
                    require(position == 0 and not ready and row['evidentiary'] is False)
                    for key in (IDENTITY + extra).split():
                        require(row[key] == binding[key], 'identity_mismatch')
                    require(row['source_manifest_sha256']
                            == binding['child_source_manifest_sha256'], 'identity_mismatch')
                    ready, wire_seen = True, True
                    continue
                require(ready, 'missing_ready')
                if kind == 'action':
                    require(terminal is None and pending is None and row['hand_id'] == child
                            and integer(row['action_index'], 1) and integer(row['seat'], 0, 5)
                            and row['seat'] == binding['controlled_seat'])
                    label(row['street'], STREETS)
                    action(row['action'])
                    pending = row
                    continue
                if kind == 'event_result':
                    require(terminal is None and integer(row['event_index']))
                    label(row['status'], ('accepted', 'decided', 'failed'))
                    dec, fail = row['decision'], row['failure']
                    # Check cross-row conflicts before committing any observation from this row.
                    if dec is not None:
                        decision(dec, binding, child, row['event_index'], baseline)
                        require(dec['action_index'] not in decisions
                                or decisions[dec['action_index']] == dec, 'conflicting_decision')
                        key = (child, dec['action_index'])
                        require(key not in timed or timed[key] == dec['timing'],
                                'conflicting_timing')
                    if row['status'] == 'failed':
                        require(baseline or dec is None)
                        require(fail is not None, 'missing_action_failure')
                        failure(fail, child, row['event_index'])
                        if dec is not None:
                            require(dec['failure_reason'] is not None and all(fail[k] == dec[k]
                                for k in ('hand_id', 'event_index', 'action_index',
                                          'delivery_status',
                                          'delivered_action', 'timing')))
                            require(fail['code'] == dec['failure_reason'], 'conflicting_failure')
                        key = tuple(fail[k] for k in ('hand_id', 'event_index', 'action_index'))
                        identity = key if None not in key else ('frame', position)
                        if (fail['timing'] is not None and fail['hand_id'] is not None
                                and fail['action_index'] is not None):
                            key = (fail['hand_id'], fail['action_index'])
                            require(key not in timed or timed[key] == fail['timing'],
                                    'conflicting_timing')
                        if identity in seen:
                            require(seen[identity][0] == fail, 'conflicting_failure')
                            if dec is not None:
                                seen[identity][1]['sources'] = ['decision', 'failure']
                        else:
                            failures.append({**{k: fail[k] for k in ('hand_id', 'event_index',
                                'action_index', 'code', 'delivery_status')},
                                'sources': (['decision', 'failure']
                                            if dec is not None else ['failure']),
                                'standing': 'unverified_prefix'})
                            seen[identity] = (fail, failures[-1])
                        if (fail['timing'] is not None and fail['hand_id'] is not None
                                and fail['action_index'] is not None):
                            key = (fail['hand_id'], fail['action_index'])
                            timed[key] = fail['timing']
                    else:
                        require(fail is None and row['event_index'] == event, 'event_order')
                        if row['status'] == 'accepted':
                            require(dec is None and pending is None)
                        else:
                            require(dec is not None and pending is not None, 'missing_decision')
                            require(dec['action_index'] == len(decisions) + 1
                                    and dec['street_action_index'] == 1 + sum(
                                        d['street'] == dec['street'] for d in decisions.values())
                                    and all(dec[k] == pending[k] for k in (
                                        'hand_id', 'action_index', 'seat', 'street'))
                                    and dec['selected_action'] == pending['action'])
                            require(dec['failure_reason'] is None
                                    and dec['timing']['status'] == 'completed')
                            t = dec['timing']
                            require(not t['work_cutoff_crossed'] and not t['deadline_crossed']
                                    and t['elapsed_ns'] <= 15000000000
                                    and abs(t['response_compute_seconds']
                                            + t['response_uninstrumented_seconds']
                                            - t['elapsed_ns'] / 1e9) <= 2e-9)
                    if dec is not None:
                        if dec['action_index'] not in decisions:
                            if baseline and dec['selection_origin'] == 'blueprint_fallback':
                                increment(selected, dec['selection_reason'])
                            elif not baseline:
                                increment(legacy, dec['selection_reason'])
                            decisions[dec['action_index']] = dec
                        key = (child, dec['action_index'])
                        timed[key] = dec['timing']
                    if row['event_index'] != event:
                        defects.append('event_order')
                    event, pending = max(event, row['event_index'] + 1), None
                    continue
                require(pending is None, 'missing_event_result')
                require(type(row['accounting_complete']) is bool and row['evidentiary'] is False)
                wire_causes = causes(row, True)
                if kind == 'hand_result':
                    require(terminal is None and type(row['complete']) is bool
                            and integer(row['interrupted_response_count']))
                    for key in ('preparation_compute_seconds', 'post_terminal_compute_seconds'):
                        seconds(row[key])
                    require(row['rank_source'] in (None, 'not_required', 'host_supplied'))
                    if row['complete']:
                        settlement(row['settlement'])
                        require(row['accounting_complete']
                                and row['interrupted_response_count'] == 0
                                and not wire_causes and row['rank_source'] is not None)
                    else:
                        require(row['settlement'] is None and row['rank_source'] is None)
                    terminal = row
                else:
                    require(terminal is not None)
                    label(row['status'], ('completed', 'failed'))
                    require(row['accounting_scope'] == 'runtime_begin_to_final_publication')
                    if row['terminal_publication_compute_seconds'] is not None:
                        seconds(row['terminal_publication_compute_seconds'])
                    require(row['status'] != 'completed' or row['accounting_complete']
                            and not wire_causes
                            and row['terminal_publication_compute_seconds'] is not None)
                    closed = row['status'] == 'completed' and terminal['complete']
                    finished = True
            except (ValueError, TypeError, KeyError, OverflowError, RecursionError) as error:
                defects.append(str(error) if type(error) is ValueError else 'schema_invalid')
                break
        if wire_seen:
            result.update(action_failures=failures,
                work_cutoff_actions=sum(t['work_cutoff_crossed'] is True for t in timed.values()),
                action_deadline_actions=sum(t['deadline_crossed'] is True for t in timed.values()),
                baseline_fallback_selections=selected if baseline else None,
                baseline_fallback_applied=attributed if baseline else None,
                legacy_choices=legacy if not baseline else None)
        for index, applied in enumerate(bots, 1):
            dec = decisions.get(index)
            if (dec is not None and dec['selected_action'] == applied['action']
                    and dec['street'] == applied['street']):
                result['unattributed_applied_actions'] -= 1
                if baseline and dec['selection_origin'] == 'blueprint_fallback':
                    increment(attributed, dec['selection_reason'])
        if not closed:
            defects.append('incomplete_wire')
        if result['unattributed_applied_actions'] or len(decisions) != len(bots):
            defects.append('incomplete_attribution')
        if hand['capture_truncated'] or not capture_complete:
            defects.append('capture_truncated')
        complete = (report['status'] == hand['status'] == 'completed' and exit_code == 0
            and hand['child_exit_code'] == 0 and not result['session_failure_codes']
            and not result['hand_failure_codes'] and not failures and report['stop_reason'] is None
            and report['completed_hands'] == 1 and binding['cleanup_complete'] is True)
        if complete:
            settlement(hand['settlement'])
            require(terminal is not None and hand['settlement'] == terminal['settlement']
                    and report['carried_stacks'] == hand['settlement']['final_stacks']
                    and report['next_button'] == (binding['button'] + 1) % 6, 'settlement_mismatch')
        result['report_complete'] = bool(complete and not defects)
        result['observation_complete'] = result['report_complete']
        result['state'] = ('completed' if result['report_complete'] else
                           'interrupted' if report['status'] == 'interrupted' else 'failed')
        if any(d not in ('incomplete_wire', 'incomplete_attribution',
                         'capture_truncated', 'event_order') for d in defects):
            result['state'] = 'refused'
        result['failure_reason'] = (None if result['report_complete']
                                    else report['failure_reason'] or 'trial_incomplete')
        if result['report_complete']:
            result['net_chips'] = (
                hand['settlement']['final_stacks'][binding['controlled_seat']] - 200)
    except (ValueError, TypeError, KeyError, OverflowError, RecursionError) as error:
        defects.append(str(error) if type(error) is ValueError else 'schema_invalid')
        result['failure_reason'] = 'report_refused'
    return result


def reduce_trials(plan: dict, trials: list) -> dict:
    pairs, used = [], set()
    valid = len(trials) == len(plan['units'])
    for pair in plan['pairs']:
        members = [t for t in trials if t.get('pair_index') == pair['pair_index']]
        units = [u for u in plan['units'] if u['pair_index'] == pair['pair_index']]
        complete = len(members) == len(units) == 2
        for t in members:
            matches = [u for u in units if all(t.get(k) == u[k]
                       for k in ('ordinal', 'pair_index', 'strategy'))]
            complete = (complete and len(matches) == 1 and type(t.get('ordinal')) is int
                        and t['ordinal'] not in used)
            used.add(t.get('ordinal'))
            complete = (complete and t.get('state') == 'completed'
                and t.get('report_complete') is True and t.get('observation_complete') is True
                and t.get('cleanup_complete', True) is True and type(t.get('net_chips')) is int)
        by_strategy = {t['strategy']: t for t in members}
        complete = complete and set(by_strategy) == set(STRATEGIES)
        b, p = (by_strategy[s]['net_chips'] for s in STRATEGIES) if complete else (None, None)
        pairs.append(dict(pair_index=pair['pair_index'], complete=bool(complete),
            baseline_net_chips=b, blueprint_net_chips=p, delta_chips=b - p if complete else None))
        valid = valid and complete
    def aggregate(rows):
        b, p = (sum(row[k] for row in rows) for k in ('baseline_net_chips', 'blueprint_net_chips'))
        return dict(baseline_net_chips=b, blueprint_net_chips=p, delta_chips=b-p,
                    mean_delta_numerator=b-p, mean_delta_denominator=len(rows))
    total = aggregate(pairs) if valid and pairs else None
    if total is not None:
        for field, name in (('lineup_index', 'by_lineup'), ('controlled_seat', 'by_seat')):
            total[name] = [dict(aggregate([row for row, source in zip(pairs, plan['pairs'])
                if source[field] == value]), **{field: value})
                for value in sorted({p[field] for p in plan['pairs']})]
    return dict(pairs=pairs, aggregate=total)
