"""Read-only r002 evidence reductions. No poker imports or execution authority."""
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import stat
import statistics

LIMIT = 128 * 1024 * 1024
POINTS = {
    'setup_admission': ('session:Admission.__init__', 'session:Session.prepare',
                        'host:Source.__init__'),
    'source_validation': ('session:Admission.check', 'session:Session.validate',
                          'host:Source.check', 'host:OwnedInput.check'),
    'native_launch': ('host:ChildConnection.__init__',),
    'ready_handshake': ('host:WireConsumer.ready',),
    'reference_validation': ('host:WireConsumer.provider_expected',
                             'host:WireConsumer.decision', 'host:WireConsumer.settlement'),
    'exchange_wait': ('host:WireConsumer.exchange', 'host:ChildConnection.send',
                      'host:ChildConnection.receive'),
    'progression': ('session:Schedule.derive', 'session:Session.play_hand',
                    'host:Table.start_event', 'host:Table.next_event'),
    'completion': ('host:WireConsumer.complete', 'host:ChildConnection.finish'),
    'orchestration': ('session:Session.run',),
}
CATEGORIES = {point: category for category, points in POINTS.items() for point in points}


class ReportError(ValueError):
    def __init__(self, message, code='input_invalid'):
        super().__init__(message)
        self.code = code


def require(condition, message, code='input_invalid'):
    if not condition:
        raise ReportError(message, code)


def integer(value):
    require(type(value) is int and 0 <= value <= 2**63 - 1, 'nonnegative integer required')
    return value


def shape(value, keys):
    require(type(value) is dict and set(value) == set(keys.split()), 'record fields differ')


def parse_json(raw, limit=LIMIT):
    """Strict bounded LF UTF-8; duplicate object keys never disappear."""
    require(type(raw) is bytes and len(raw) <= integer(limit),
            'JSON capture limit', 'capture_limit')
    require(b'\r' not in raw and not raw.startswith(b'\xef\xbb\xbf'), 'noncanonical encoding')

    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'duplicate JSON key')
            result[key] = value
        return result

    def visit(value, depth=0):
        require(depth <= 64, 'JSON nesting limit')
        if type(value) is float:
            require(math.isfinite(value), 'nonfinite JSON number')
        if type(value) in (dict, list):
            for item in value.values() if type(value) is dict else value:
                visit(item, depth + 1)

    try:
        value = json.loads(raw.decode('utf-8'), object_pairs_hook=pairs)
        visit(value)
        return value
    except (UnicodeError, RecursionError, json.JSONDecodeError) as exc:
        raise ReportError('invalid JSON encoding/nesting') from exc


def distribution(values):
    require(type(values) is list, 'observations must be a list')
    ordered = sorted(integer(value) for value in values)
    n = len(ordered)
    return {'n': n, 'raw': list(values), 'median': statistics.median(ordered) if n else None,
            'maximum': ordered[-1] if n else None,
            'p95': ordered[(95 * n + 99) // 100 - 1] if n >= 20 else None,
            'p99': ordered[(99 * n + 99) // 100 - 1] if n >= 1000 else None}


def reduce_spans(events, outer_ns):
    """Charge intervals exclusively, with constructor-over-check precedence."""
    integer(outer_ns)
    require(type(events) is list, 'events must be a list', 'profile_invalid')
    phases = dict.fromkeys((*POINTS, 'residual'), 0)
    counts = dict.fromkeys(CATEGORIES, 0)
    stack, previous = [], 0
    for event in events:
        shape(event, 'event point ns')
        point, now = event['point'], integer(event['ns'])
        require(type(point) is str and point in CATEGORIES and previous <= now <= outer_ns,
                'unknown point or nonmonotonic/outside timestamp', 'profile_invalid')
        category = CATEGORIES[stack[-1]] if stack else 'residual'
        if category == 'source_validation' and any(
                item in ('session:Admission.__init__', 'host:Source.__init__') for item in stack):
            category = 'setup_admission'
        phases[category] += now - previous
        previous = now
        if event['event'] == 'call':
            stack.append(point)
            counts[point] += 1
        else:
            require(event['event'] == 'return' and stack and stack[-1] == point,
                    'non-LIFO return', 'profile_invalid')
            stack.pop()
    require(not stack and counts['session:Session.run'] == 1,
            'missing or unclosed Session.run', 'profile_invalid')
    phases['residual'] += outer_ns - previous
    require(sum(phases.values()) == outer_ns, 'phase closure failed', 'profile_invalid')
    return {'phases': phases, 'counts': counts, 'closed': True, 'outer_ns': outer_ns}


def phase_dominance(cases):
    hits, observations = {}, []
    for case in cases:
        shape(case, 'id outer_ns unprofiled_ns phases')
        outer, base = integer(case['outer_ns']), integer(case['unprofiled_ns'])
        require(type(case['phases']) is dict and set(case['phases']) <= set((*POINTS, 'residual')),
                'unknown phase', 'profile_invalid')
        require(sum(integer(n) for n in case['phases'].values()) == outer,
                'phase closure failed', 'profile_invalid')
        eligible = base > 0 and outer * 4 <= base * 5
        observations.append(dict(case, eligible=eligible,
                                 inflation=outer / base - 1 if base else None))
        if eligible:
            for phase, elapsed in case['phases'].items():
                if phase not in ('residual', 'orchestration') and elapsed >= 100_000_000 \
                        and elapsed * 2 >= outer:
                    hits.setdefault(phase, []).append(case['id'])
    return {'triggered': sorted(phase for phase, ids in hits.items() if len(set(ids)) >= 2),
            'raw_case_sets': hits, 'cases': observations}


def reuse(fresh_ns, retained_ns, hands):
    fresh, retained = distribution(fresh_ns), distribution(retained_ns)
    integer(hands)
    require(hands > 0 and len(fresh_ns) == len(retained_ns), 'invalid reuse pairs')
    savings = [(a - b) / hands for a, b in zip(fresh_ns, retained_ns)]
    saving = statistics.median(savings) if savings else None
    baseline = fresh['median'] / hands if savings else None
    eligible = hands == 8 and len(savings) == 4 and baseline > 0
    return {'fresh': fresh, 'retained': retained, 'hands': hands, 'savings_ns': savings,
            'median_saving_ns': saving, 'fresh_per_hand_ns': baseline,
            'fraction': saving / baseline if baseline else None,
            'triggered': (saving >= 10_000_000 and saving >= baseline * .2
                          and all(n > 0 for n in savings)) if eligible else None}


def miss_path(individual_ns, batch_ns, empty_ns, key_ns):
    individual, batches = distribution(individual_ns), distribution(batch_ns)
    empty, key = distribution(empty_ns), distribution(key_ns)
    sensitive = (empty['median'] * 20 > individual['median']) \
        if empty['n'] and individual['n'] else None
    eligible = sensitive is False and individual['p95'] is not None and batches['n'] > 0
    # Batch values are outer durations for exactly 100 calls; no overhead subtraction.
    batch_mean = {k: ([n / 100 for n in v] if k == 'raw' else
                      v / 100 if v is not None and k != 'n' else v) for k, v in batches.items()}
    return {'individual_ns': individual, 'batch_mean_ns': batch_mean, 'empty_ns': empty,
            'key_ns': key, 'primary': 'batch_mean_ns', 'instrumentation_sensitive': sensitive,
            'triggered': individual['p95'] >= 1_000_000 if eligible else None,
            'key_priority': key['median'] * 2 >= individual['median']
            if key['n'] and individual['n'] else None}


def scaling(samples, byte_work, component):
    require(component in ('decode', 'prepare', 'canonical', 'hash', 'retained'),
            'unknown scaling component')
    stats = {integer(n): distribution(values) for n, values in samples.items()}
    require(set(stats) == set(byte_work), 'byte-work census differs')
    work = {integer(n): integer(value) for n, value in byte_work.items()}
    results = {}
    for n, observed in stats.items():
        if n in (0, 1024):
            continue
        needed = [stats.get(k) for k in (0, 1024, n)]
        eligible = all(row and row['n'] == 5 and row['maximum'] - min(row['raw'])
                       <= row['median'] * 3 / 10 for row in needed)
        t0, t1 = (stats.get(k, {}).get('median') for k in (0, 1024))
        eligible = eligible and t1 > t0 and work[1024] > work[0] and work[n] > work[0]
        linear = t0 + (t1 - t0) * (work[n] - work[0]) / (work[1024] - work[0]) \
            if eligible else None
        ratio = (observed['median'] - t0) / (linear - t0) if eligible else None
        factor = math.log2(n) / 10 if n else 0
        results[n] = {'observations': observed, 'byte_work': work[n], 'linear': linear,
                      'sorting': t0 + (linear - t0) * factor if eligible else None,
                      'ratio': ratio, 'triggered': ratio > 1.25 if eligible else None,
                      'sorting_excess': ratio > 1.25 * factor if eligible and
                      component in ('prepare', 'canonical') else None,
                      'reason': None if eligible else
                      'missing, nonpositive or noisy anchors/target'}
    return results


def validate_actions(actions):
    require(type(actions) is list, 'actions must be a list')
    seen = set()
    for action in actions:
        enriched = 'membership' in action
        shape(action, 'id seat first size elapsed_ns compute_ns uninstrumented_ns work_cutoff '
              'deadline street history_atoms hit strategy trial_id' +
              (' membership fallback_used selection_origin' if enriched else ''))
        require(type(action['id']) is str and action['id'] and action['id'] not in seen,
                'duplicate action identity')
        seen.add(action['id'])
        for key in ('seat', 'size', 'elapsed_ns', 'compute_ns',
                    'uninstrumented_ns', 'history_atoms'):
            integer(action[key])
        require(action['seat'] < 6 and action['street'] in ('preflop', 'flop', 'turn', 'river')
                and action['strategy'] in ('blueprint-v1', 'baseline-rules-v1') and
                type(action['trial_id']) is str and action['trial_id'], 'invalid action identity')
        for key in ('first', 'work_cutoff', 'deadline'):
            require(type(action[key]) is bool, 'invalid action flag')
        if enriched:
            require(type(action['membership']) is bool and type(action['fallback_used']) is bool and
                    type(action['selection_origin']) is str, 'invalid selection attribution')
        primary = (enriched and action['strategy'] == 'baseline-rules-v1'
                   and not action['fallback_used'])
        require(action['hit'] is None if primary else type(action['hit']) is bool,
                'invalid hit attribution')
        # The accepted host allows 2 ns in original float-second components; two
        # independent integer rounding operations add at most another 1 ns.
        require(abs(action['compute_ns'] + action['uninstrumented_ns'] - action['elapsed_ns']) <= 3,
                'action elapsed components exceed accepted rounding tolerance')


def response_safety(actions, n_fit):
    validate_actions(actions)
    integer(n_fit)
    first = [a for a in actions if a['first'] and a['seat'] == 3 and a['size'] == n_fit]
    flags = any(a['work_cutoff'] or a['deadline'] for a in actions)
    return {'triggered': flags or any(a['elapsed_ns'] >= 1_400_000_000 for a in first)
            if flags or first else None, 'first_to_act_case_ids': [a['id'] for a in first],
            'contract_failure': flags,
            'actions': [dict(a, work_margin_ns=14_000_000_000 - a['elapsed_ns'],
                             deadline_margin_ns=15_000_000_000 - a['elapsed_ns'],
                             component_rounding_delta_ns=a['elapsed_ns'] - a['compute_ns'] -
                             a['uninstrumented_ns']) for a in actions]}


def capacity(n_fit):
    integer(n_fit)
    return {'n_fit': n_fit, 'requested': 8192, 'retained_fraction': n_fit / 8192,
            'triggered': n_fit < 8192}


def resource_concern(peak_private_bytes):
    observed = distribution(peak_private_bytes)
    return {'observations': observed,
            'triggered': observed['maximum'] >= 512 * 1024 * 1024 if observed['n'] else None}


def action_traffic(actions):
    """One interpreter's unprofiled child ledger; preserve natural weighting."""
    validate_actions(actions)
    strata = {}
    for action in actions:
        key = (action['strategy'], action['size'], action['hit'], action['first'],
               action.get('fallback_used'), action.get('selection_origin'),
               action.get('membership', action['hit']))
        strata.setdefault(key, []).append(action)
    return {'case_ids': [a['id'] for a in actions],
            'natural': distribution([a['elapsed_ns'] for a in actions]),
            'strata': [{'strategy': key[0], 'size': key[1], 'hit': key[2], 'first': key[3],
                        'fallback_used': key[4], 'selection_origin': key[5], 'membership': key[6],
                        'case_ids': [a['id'] for a in rows],
                        'distribution': distribution([a['elapsed_ns'] for a in rows])}
                       for key, rows in strata.items()], 'raw': actions}


CAUSES = {'source_invalid', 'input_invalid', 'coverage_missing', 'parity_failed',
          'profile_invalid', 'capture_limit', 'resource_limit', 'budget_exhausted',
          'worker_failed', 'cleanup_failed'}
PARAMETERS = {
    'construction': 'observation', 'memory_traced': 'observation',
    'memory_untraced': 'observation',
    'history': 'bin operation blocks subblocks warmups batches batch_calls individual_calls '
               'empty_brackets empty_batches loop_batches',
    'reuse': 'hands repetition arm trajectory_ordinals',
    'comparison': 'blocks warmups calls_per_class provider_order alternate_provider_first '
                  'continuous_cycle',
    'session': 'diagnostic ordinal deal seat lineup strategy session_id '
               'session_path blueprint_path',
}


def digest(value):
    require(type(value) is str and len(value) == 64 and
            all(char in '0123456789abcdef' for char in value), 'invalid SHA-256')


def file_ref(ref):
    shape(ref, 'path sha256 bytes')
    name = ref['path']
    require(type(name) is str and name and '\\' not in name and ':' not in name and
            not name.startswith('/') and all(part not in ('', '.', '..')
                                            for part in name.split('/')) and
            all(not part.endswith((' ', '.')) for part in name.split('/')),
            'noncanonical relative file path')
    digest(ref['sha256'])
    require(integer(ref['bytes']) <= LIMIT, 'file capture limit', 'capture_limit')
    return name


def validate_plan(plan):
    shape(plan, 'version population_sha256 runtimes cells')
    require(plan['version'] == 'workload-r002-plan-v1', 'unknown plan version')
    digest(plan['population_sha256'])
    require(type(plan['runtimes']) is list and plan['runtimes'], 'missing runtime identity')
    runtimes = {}
    for runtime in plan['runtimes']:
        shape(runtime, 'id version executable executable_sha256 resolved_executable '
              'resolved_executable_sha256 source_root run_root source_sha256 protocol_sha256 '
              'authorization')
        require(runtime['id'] in ('3.11', '3.14') and runtime['id'] not in runtimes and
                runtime['version'] == {'3.11': '3.11.15', '3.14': '3.14.6'}[runtime['id']],
                'runtime identity differs')
        for key, value in runtime.items():
            require(type(value) is str and value, 'invalid runtime field')
            if key.endswith('sha256'):
                digest(value)
        runtimes[runtime['id']] = runtime
    require(type(plan['cells']) is list, 'cells must be ordered list')
    cells = {}
    for cell in plan['cells']:
        shape(cell, 'id runtime kind size parameters argv')
        require(type(cell['id']) is str and cell['id'] and
                all(c.isalnum() or c in '-_' for c in cell['id']) and cell['id'] not in cells,
                'duplicate or invalid cell ID')
        require(type(cell['runtime']) is str and cell['runtime'] in runtimes and
                type(cell['kind']) is str and cell['kind'] in PARAMETERS,
                'unknown cell runtime/kind')
        integer(cell['size'])
        shape(cell['parameters'], PARAMETERS[cell['kind']])
        validate_parameters(cell)
        require(type(cell['argv']) is list and cell['argv'] and
                all(type(arg) is str and arg for arg in cell['argv']), 'invalid frozen argv')
        cells[cell['id']] = cell
    return cells


def validate_parameters(cell):
    params, kind = cell['parameters'], cell['kind']
    if kind in ('construction', 'memory_traced', 'memory_untraced'):
        require(integer(params['observation']) < 5, 'observation ordinal differs')
    elif kind == 'history':
        require(params['bin'] in ('0', '3-5', '7-9', '15-17', '31-33') and
                params['operation'] in ('key', 'hash', 'lookup', 'identity', 'provider') and
                params['subblocks'] == ['hit', 'miss', 'miss', 'hit'], 'history schedule differs')
        fixed = {'blocks': 5, 'warmups': 10, 'batches': 10, 'batch_calls': 100,
                 'individual_calls': 1000, 'empty_brackets': 10000,
                 'empty_batches': 5, 'loop_batches': 5}
        require(all(integer(params[key]) == value for key, value in fixed.items()),
                'history counts differ')
    elif kind == 'reuse':
        require(integer(params['hands']) in (1, 2, 8, 32) and integer(params['repetition']) < 4 and
                params['arm'] in ('fresh', 'retained') and
                type(params['trajectory_ordinals']) is list and
                len(params['trajectory_ordinals']) == params['hands'], 'reuse schedule differs')
        require(all(integer(n) < 1152 for n in params['trajectory_ordinals']),
                'invalid reuse trajectory')
    elif kind == 'comparison':
        require(integer(params['blocks']) == 5 and integer(params['warmups']) == 20 and
                integer(params['calls_per_class']) ==
                {1024: 20, 8192: 10, 65536: 2}.get(cell['size'])
                and params['provider_order'] == ['legacy', 'prepared'] and
                params['alternate_provider_first'] is True and params['continuous_cycle'] is True,
                'comparison schedule differs')
    elif kind == 'session':
        require(type(params['diagnostic']) is bool and integer(params['ordinal']) < 96 and
                integer(params['deal']) < 2 and integer(params['seat']) < 6 and
                integer(params['lineup']) < 2 and params['strategy'] in
                ('blueprint-v1', 'baseline-rules-v1'), 'session factors differ')
        require(all(type(params[key]) is str and params[key] for key in
                    ('session_id', 'session_path', 'blueprint_path')), 'invalid session paths/ID')


def validate_result(record):
    shape(record, 'version cell_id status cause secondary observations files outer_ns '
          'exit_code cleanup captures')
    require(record['version'] == 'workload-r002-result-v1' and type(record['cell_id']) is str,
            'result identity differs')
    require(type(record['status']) is str and record['status'] in
            ('completed', 'failed', 'interrupted', 'unattempted'),
            'invalid result status')
    require(record['cause'] is None or (type(record['cause']) is str and record['cause'] in CAUSES),
            'unknown cause')
    require(type(record['secondary']) is list and all(type(cause) is str and cause in CAUSES
                                                   for cause in record['secondary']),
            'unknown causes')
    require(type(record['observations']) is dict and type(record['files']) is list,
            'invalid result payload')
    for ref in record['files']:
        file_ref(ref)
    if record['outer_ns'] is not None:
        integer(record['outer_ns'])
    require(record['exit_code'] is None or type(record['exit_code']) is int, 'invalid exit code')
    shape(record['cleanup'], 'verified active')
    require(type(record['cleanup']['verified']) is bool, 'invalid cleanup flag')
    if record['cleanup']['active'] is not None:
        integer(record['cleanup']['active'])
    shape(record['captures'], 'stdout stderr truncated')
    require(type(record['captures']['truncated']) is bool, 'invalid truncation flag')
    for name in ('stdout', 'stderr'):
        if record['captures'][name] is not None:
            file_ref(record['captures'][name])
    if record['status'] == 'completed':
        require(record['cause'] is None and not record['secondary'] and
                record['outer_ns'] is not None and record['exit_code'] == 0 and
                record['cleanup'] == {'verified': True, 'active': 0} and
                not record['captures']['truncated'], 'completed result contains failure')
    else:
        require(record['cause'] in CAUSES, 'noncompleted result lacks reason')
        if record['status'] == 'unattempted':
            require(record['outer_ns'] is None and record['exit_code'] is None and
                    not record['observations'] and record['captures'] ==
                    {'stdout': None, 'stderr': None, 'truncated': False},
                    'unattempted result has execution')


OBSERVATIONS = {
    'construction': 'memory_samples source_sha256 read_ns decode_ns prepare_ns first_ns '
                    'outer_total_ns canonical_ns sha_ns wire_bytes key_bytes canonical_bytes',
    'memory_traced': 'memory_samples source_sha256 retained_bytes peak_bytes excluded_raw_bytes '
                     'excluded_observation wire_bytes key_bytes canonical_bytes',
    'memory_untraced': 'memory_samples source_sha256 excluded_raw_bytes excluded_observation '
                       'wire_bytes key_bytes canonical_bytes',
    'history': 'memory_samples clock empty_brackets_ns empty_batches_ns loop_batches_ns blocks',
    'reuse': 'memory_samples group_ns prepare_ns hash_ns read_ns decode_ns query_count '
             'distinct_keys context_ids',
    'comparison': 'memory_samples blocks',
    'session': 'raw_events actions preparation session_status settlement reference_id',
}


def identifiers(values):
    require(type(values) is list and all(type(value) is str and value for value in values),
            'invalid context IDs')


def validate_observations(obs, cell):
    kind, params = cell['kind'], cell['parameters']
    shape(obs, OBSERVATIONS[kind])
    for key, value in obs.items():
        if key == 'source_sha256':
            digest(value)
        elif (key.endswith('_ns') or key.endswith('_bytes') or
              key in ('query_count', 'distinct_keys')) and type(value) is not list:
            integer(value)
    if kind != 'session':
        require(type(obs['memory_samples']) is list, 'memory samples must be list')
        previous = 0
        pids = set()
        for sample in obs['memory_samples']:
            shape(sample, 'pid ns stage private_commit working_set '
                  'peak_private_commit peak_working_set')
            for key, value in sample.items():
                if key != 'stage':
                    integer(value)
            require(sample['pid'] > 0 and sample['ns'] >= previous and sample['stage'] in
                    ('idle', 'read', 'decode', 'prepare', 'first', 'final', 'ready', 'periodic'),
                    'invalid memory sample')
            previous = sample['ns']
            pids.add(sample['pid'])
        stages = [sample['stage'] for sample in obs['memory_samples']
                  if sample['stage'] != 'periodic']
        expected = ['ready', 'idle', 'read', 'decode', 'prepare', 'first', 'final'] \
            if kind == 'memory_untraced' else ['ready', 'final']
        require(len(pids) == 1 and stages == expected, 'missing or unordered memory stages/PID')
    if kind.startswith('memory'):
        require(type(obs['excluded_observation']) is str and obs['excluded_observation'],
                'missing excluded observation ownership')
        if kind == 'memory_traced':
            require(obs['retained_bytes'] <= obs['peak_bytes'], 'retained exceeds traced peak')
    elif kind == 'history':
        shape(obs['clock'], 'implementation monotonic adjustable resolution')
        clock = obs['clock']
        require(type(clock['implementation']) is str and type(clock['monotonic']) is bool and
                type(clock['adjustable']) is bool and type(clock['resolution']) in (int, float)
                and math.isfinite(clock['resolution']) and clock['resolution'] > 0,
                'invalid clock metadata')
        for key, count in (('empty_brackets_ns', 10000), ('empty_batches_ns', 5),
                           ('loop_batches_ns', 5)):
            require(distribution(obs[key])['n'] == count, 'timer control census differs')
        require(type(obs['blocks']) is list and len(obs['blocks']) == 5,
                'history block census differs')
        for block in obs['blocks']:
            shape(block, 'hit miss')
            for label, row in block.items():
                shape(row, 'context_ids batch_ns individual_ns')
                identifiers(row['context_ids'])
                count = len(row['context_ids'])
                require(count <= 100 and len(set(row['context_ids'])) == count and
                        row['context_ids'] == obs['blocks'][0][label]['context_ids'],
                        'history context census/order differs')
                require(distribution(row['batch_ns'])['n'] == (20 if count else 0) and
                        distribution(row['individual_ns'])['n'] == (2000 if count else 0),
                        'history observation census differs')
    elif kind == 'reuse':
        identifiers(obs['context_ids'])
        hands, fresh = params['hands'], params['arm'] == 'fresh'
        require(distribution(obs['prepare_ns'])['n'] == (hands if fresh else 1) and
                distribution(obs['hash_ns'])['n'] == (0 if fresh else hands) and
                obs['query_count'] == len(obs['context_ids']) and
                obs['distinct_keys'] <= obs['query_count'], 'reuse observation census differs')
    elif kind == 'comparison':
        require(type(obs['blocks']) is list and len(obs['blocks']) == 5, 'comparison blocks differ')
        for block in obs['blocks']:
            shape(block, 'legacy prepared')
            for provider in block.values():
                shape(provider, 'hit miss')
                for row in provider.values():
                    shape(row, 'context_ids call_ns')
                    identifiers(row['context_ids'])
                    count = distribution(row['call_ns'])['n']
                    require(count == len(row['context_ids']) and
                            count in (0, params['calls_per_class']),
                            'comparison observation census differs')
            require(all(block['legacy'][label]['context_ids'] ==
                        block['prepared'][label]['context_ids'] for label in ('hit', 'miss')),
                    'comparison providers use different contexts')
    elif kind == 'session':
        require(type(obs['raw_events']) is list and type(obs['actions']) is list and
                type(obs['preparation']) is list and type(obs['settlement']) is dict and
                all(type(obs[key]) is str and obs[key]
                    for key in ('session_status', 'reference_id')),
                'invalid session observations')
        require(obs['session_status'] == 'completed' and len(obs['preparation']) == 1 and
                obs['actions'], 'completed session lacks complete hand observations')
        previous_event = -1
        for ordinal, action in enumerate(obs['actions'], 1):
            shape(action, 'id hand_id event_index action_index street history_atoms hit first '
                  'elapsed_ns compute_ns uninstrumented_ns work_cutoff deadline fallback_used '
                  'selection_origin')
            for key in ('event_index', 'action_index'):
                integer(action[key])
            require(type(action['fallback_used']) is bool and all(type(action[key]) is str and
                    action[key] for key in ('hand_id', 'selection_origin')),
                    'invalid action identity')
            require(action['action_index'] == ordinal and action['first'] is (ordinal == 1) and
                    action['event_index'] > previous_event and
                    action['id'] == cell['id'] + '-a' + str(ordinal),
                    'session action identity/order differs')
            previous_event = action['event_index']
        for prep in obs['preparation']:
            shape(prep, 'hand_id preparation_compute_seconds post_terminal_compute_seconds '
                  'accounting_complete interrupted_response_count')
            require(type(prep['hand_id']) is str and type(prep['accounting_complete']) is bool,
                    'invalid preparation identity')
            integer(prep['interrupted_response_count'])
            require(prep['accounting_complete'] and prep['interrupted_response_count'] == 0 and
                    all(action['hand_id'] == prep['hand_id'] for action in obs['actions']),
                    'completed session has incomplete or mismatched hand accounting')
            for key in ('preparation_compute_seconds', 'post_terminal_compute_seconds'):
                require(type(prep[key]) in (int, float) and
                        math.isfinite(prep[key]) and prep[key] >= 0,
                        'invalid original preparation seconds')
        validate_actions(normalized_actions(obs, cell))


def normalized_actions(obs, cell):
    keys = ('id first elapsed_ns compute_ns uninstrumented_ns work_cutoff '
            'deadline street history_atoms hit')
    return [dict({key: action[key] for key in keys.split()}, seat=cell['parameters']['seat'],
                 size=cell['size'], strategy=cell['parameters']['strategy'], trial_id=cell['id'],
                 membership=action['hit'], fallback_used=action['fallback_used'],
                 selection_origin=action['selection_origin'],
                 **({'hit': None} if cell['parameters']['strategy'] == 'baseline-rules-v1' and
                    not action['fallback_used'] else {}))
            for action in obs['actions']]


def aggregate_rule(details):
    values = [row['triggered'] for row in details]
    return {'triggered': True if True in values else
            None if not values or None in values else False,
            'details': details,
            'case_ids': [ident for row in details for ident in row.get('case_ids', [])]}


def artifact_report(metadata):
    """Serialized row statistics use row bytes, never retained graph allocations."""
    shape(metadata, 'size source_sha256 canonical_bytes key_bytes wire_bytes root_bytes '
          'row_bytes comma_bytes row_census')
    digest(metadata['source_sha256'])
    for key, value in metadata.items():
        if key not in ('source_sha256', 'row_census'):
            integer(value)
    shape(metadata['row_census'], 'preflop flop turn river')
    census, count, total = {}, 0, 0
    for street, bins in metadata['row_census'].items():
        shape(bins, '0 3-5 7-9 15-17 31-33 other')
        census[street] = {}
        for name, lengths in bins.items():
            summary = distribution(lengths)
            n = summary['n']
            # Row p95 is a finite byte census, not an empirical latency-tail claim.
            summary.update(mean=sum(lengths) / n if n else None,
                           p95=sorted(lengths)[(95 * n + 99) // 100 - 1] if n else None)
            census[street][name] = summary
            count += n
            total += sum(lengths)
    require(count == metadata['size'] and total == metadata['row_bytes'] and
            metadata['comma_bytes'] == max(0, count - 1) and
            metadata['root_bytes'] + total + metadata['comma_bytes'] == metadata['wire_bytes'],
            'serialized byte/row census does not reconcile')
    return dict(metadata, row_census=census)


def runtime_summary(rows, cells, n_fit):
    actions, profiles, parent, raw = [], [], [], []
    by_kind = {kind: [] for kind in PARAMETERS}
    for record in rows:
        cell = cells[record['cell_id']]
        by_kind[cell['kind']].append((cell, record))
        raw.append({'cell_id': cell['id'], 'observations': record['observations']})
    sessions = by_kind['session']
    for cell, record in sessions:
        obs = record['observations']
        if not cell['parameters']['diagnostic']:
            require(not obs['raw_events'], 'unprofiled result contains profile events')
            parent.append(record['outer_ns'])
            actions.extend(normalized_actions(obs, cell))
        else:
            reduced = reduce_spans(obs['raw_events'], record['outer_ns'])
            matched = [(c, r) for c, r in sessions if not c['parameters']['diagnostic'] and
                       c['parameters']['ordinal'] == cell['parameters']['ordinal'] and
                       c['size'] == cell['size']]
            if len(matched) == 1:
                profiles.append({'id': cell['id'], 'outer_ns': record['outer_ns'],
                                 'unprofiled_ns': matched[0][1]['outer_ns'],
                                 'phases': reduced['phases']})
    phase = phase_dominance(profiles)
    phase['triggered_phases'] = phase['triggered']
    phase['triggered'] = (bool(phase['triggered']) if
                          sum(c['eligible'] for c in phase['cases']) >= 2 else None)
    phase['case_ids'] = [row['id'] for row in profiles]
    misses = []
    for cell, record in by_kind['history']:
        if cell['parameters']['operation'] != 'provider':
            continue
        obs = record['observations']
        keys = [r['observations'] for c, r in by_kind['history'] if
                c['parameters']['operation'] == 'key' and
                c['parameters']['bin'] == cell['parameters']['bin']]
        key_ns = [n for k in keys for block in k['blocks'] for n in block['miss']['individual_ns']]
        reduced = miss_path([n for b in obs['blocks'] for n in b['miss']['individual_ns']],
                            [n for b in obs['blocks'] for n in b['miss']['batch_ns']],
                            obs['empty_brackets_ns'], key_ns)
        misses.append(dict(reduced, case_ids=[cell['id']], history_bin=cell['parameters']['bin']))
    groups = {}
    for cell, record in by_kind['reuse']:
        if cell['parameters']['hands'] == 8 and cell['size'] == n_fit:
            key = cell['parameters']['repetition']
            require(cell['parameters']['arm'] not in groups.setdefault(key, {}),
                    'duplicate reuse arm')
            groups[key][cell['parameters']['arm']] = (cell, record)
    pairs = [pair for _, pair in sorted(groups.items()) if set(pair) == {'fresh', 'retained'}]
    require(all(all(pair['fresh'][1]['observations'][key] ==
                    pair['retained'][1]['observations'][key]
                    for key in ('context_ids', 'query_count', 'distinct_keys')) for pair in pairs),
            'paired reuse query/key census differs')
    reused = reuse([p['fresh'][1]['observations']['group_ns'] for p in pairs],
                   [p['retained'][1]['observations']['group_ns'] for p in pairs], 8)
    reused['case_ids'] = [p[arm][0]['id'] for p in pairs for arm in ('fresh', 'retained')]
    scale_results = []
    for component, kind, field in (('decode', 'construction', 'decode_ns'),
                                  ('prepare', 'construction', 'prepare_ns'),
                                  ('canonical', 'construction', 'canonical_ns'),
                                  ('hash', 'construction', 'sha_ns'),
                                  ('retained', 'memory_traced', 'retained_bytes')):
        samples, work, case_ids = {}, {}, {}
        for cell, record in by_kind[kind]:
            obs, size = record['observations'], cell['size']
            proxy = obs['wire_bytes'] if component == 'decode' else obs['canonical_bytes'] + (
                obs['key_bytes'] if component in ('prepare', 'canonical', 'retained') else 0)
            require(size not in work or work[size] == proxy, 'byte proxy differs within size')
            work[size] = proxy
            samples.setdefault(size, []).append(obs[field])
            case_ids.setdefault(size, []).append(cell['id'])
        results = scaling(samples, work, component)
        for size, result in results.items():
            scale_results.append(dict(result, component=component, size=size,
                                      case_ids=[ident for n in (0, 1024, size)
                                                for ident in case_ids.get(n, [])]))
    memory = [(c, r) for c, r in by_kind['memory_untraced'] if c['size'] == n_fit]
    resource = resource_concern([s['peak_private_commit'] for c, r in memory
                                 for s in r['observations']['memory_samples']])
    resource['case_ids'] = [c['id'] for c, r in memory]
    safety = response_safety(actions, n_fit) if n_fit is not None else {'triggered': None}
    rules = {'response_margin': safety, 'interface_cap': capacity(n_fit) if n_fit is not None else
             {'triggered': None}, 'dominant_session_phase': phase,
             'useful_preparation_reuse': reused, 'material_miss_path': aggregate_rule(misses),
             'excess_scaling': aggregate_rule(scale_results),
             'current_process_resource_concern': resource}
    return {'rules': rules, 'unresolved': [name for name, result in rules.items()
                                         if result['triggered'] is None], 'raw_cells': raw,
            'traffic': action_traffic(actions), 'parent_wall': distribution(parent),
            'parent_case_ids': [c['id'] for c, r in sessions if not c['parameters']['diagnostic']],
            'profile_cases': profiles}


def summarize(records, plan):
    """Preserve planned/failed denominators; a missing observation is unresolved."""
    cells = validate_plan(plan)
    require(type(records) is list, 'records must be ordered list')
    census = {status: [] for status in
              ('completed', 'failed', 'interrupted', 'unattempted', 'missing')}
    seen = set()
    for record in records:
        validate_result(record)
        ident = record['cell_id']
        require(ident in cells and ident not in seen, 'unknown or duplicate result cell')
        seen.add(ident)
        if record['status'] == 'completed':
            validate_observations(record['observations'], cells[ident])
            require(all(sample['ns'] <= record['outer_ns'] for sample in
                        record['observations'].get('memory_samples', [])),
                    'memory sample lies outside supervised process wall')
        census[record['status']].append(ident)
    census['missing'] = [ident for ident in cells if ident not in seen]
    fit_sizes = {cell['size'] for cell in cells.values() if cell['kind'] in ('history', 'reuse')}
    require(len(fit_sizes) <= 1, 'N_fit differs across frozen cells')
    n_fit = next(iter(fit_sizes)) if fit_sizes else None
    runtimes = {runtime['id']: runtime_summary(
        [r for r in records if cells[r['cell_id']]['runtime'] == runtime['id'] and
         r['status'] == 'completed'], cells, n_fit) for runtime in plan['runtimes']}
    for runtime, report in runtimes.items():
        report['retained_results'] = [r for r in records
                                      if cells[r['cell_id']]['runtime'] == runtime]
        incomplete = [c for c in cells.values() if c['runtime'] == runtime and
                      c['id'] not in census['completed']]
        dependencies = {
            'response_margin': {'session'}, 'dominant_session_phase': {'session'},
            'useful_preparation_reuse': {'reuse'}, 'material_miss_path': {'history'},
            'excess_scaling': {'construction', 'memory_traced'},
            'current_process_resource_concern': {'memory_untraced'}, 'interface_cap': set()}
        for name, rule in report['rules'].items():
            missing = [c['id'] for c in incomplete if c['kind'] in dependencies[name] and
                       (name != 'useful_preparation_reuse' or c['parameters']['hands'] == 8) and
                       (name != 'current_process_resource_concern' or c['size'] == n_fit)]
            rule['incomplete_case_ids'] = missing
            if missing:
                if rule['triggered'] is False:
                    rule['triggered'] = None
                if name not in report['unresolved']:
                    report['unresolved'].append(name)
    complete = all(not census[status] for status in
                   ('failed', 'interrupted', 'unattempted', 'missing'))
    return {'planned': list(cells), 'census': census,
            'clean': complete and all(not row['unresolved'] for row in runtimes.values()),
            'runtimes': runtimes}


def read_run(root):
    """Verify exact retained-file census and hashes, then reduce without writing."""
    root = Path(root)
    require(root.is_absolute(), 'run root must be absolute')

    def safe_read(path):
        for ancestor in (path, *path.parents):
            info = ancestor.lstat()
            require(not info.st_file_attributes & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0)
                    if hasattr(info, 'st_file_attributes') else not stat.S_ISLNK(info.st_mode),
                    'reparse/link path refused')
        before = path.stat()
        require(stat.S_ISREG(before.st_mode) and before.st_size <= LIMIT, 'invalid/oversize file')
        with path.open('rb') as stream:
            raw = stream.read(LIMIT + 1)
        after = path.stat()
        require((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) ==
                (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns) and
                len(raw) == before.st_size, 'file changed while reading')
        return raw

    try:
        manifest = parse_json(safe_read(root / 'manifest.json'))
        shape(manifest, 'version files')
        require(manifest['version'] == 'workload-r002-manifest-v1' and
                type(manifest['files']) is list, 'invalid manifest version/files')
        files, aliases = {}, set()
        for ref in manifest['files']:
            name = file_ref(ref)
            require(name.casefold() not in aliases and name.casefold() != 'manifest.json',
                    'duplicate or self-referential file')
            aliases.add(name.casefold())
            raw = safe_read(root.joinpath(*PurePosixPath(name).parts))
            require(len(raw) == ref['bytes'] and hashlib.sha256(raw).hexdigest() == ref['sha256'],
                    'manifest hash/length differs')
            # Hash every retained byte; keep only records needed for reductions in memory.
            needed = name in ('plan.json', 'terminal.json', 'population.json') or (
                name.startswith('admission/') and name.endswith('-runtime-stdout.bin')) or (
                name.startswith('cells/') and name.rsplit('/', 1)[-1] in
                ('intent.json', 'environment.json', 'result.json'))
            files[name] = raw if needed else None
        actual = {path.relative_to(root).as_posix() for path in root.rglob('*') if path.is_file()}
        require(actual == set(files) | {'manifest.json'}, 'retained-file census differs')
        require('plan.json' in files and 'terminal.json' in files, 'missing plan/terminal')
        plan = parse_json(files['plan.json'])
        cells = validate_plan(plan)
        clocks = {}
        for runtime in plan['runtimes']:
            name = 'admission/' + runtime['id'] + '-runtime-stdout.bin'
            metadata = None
            if name in files:
                # Probe stdout is a raw capture: Windows print supplies CRLF. Its
                # exact bytes were hashed above; remove only that final delimiter.
                probe = parse_json(files[name].removesuffix(b'\r\n'))
                shape(probe, 'version resolved implementation' +
                      (' clocks' if 'clocks' in probe else ''))
                require(probe['version'] == runtime['version'] and
                        probe['implementation'] == 'cpython' and
                        type(probe['resolved']) is str and
                        probe['resolved'].replace('\\', '/').casefold() ==
                        runtime['resolved_executable'].replace('\\', '/').casefold(),
                        'runtime clock probe identity differs')
                if 'clocks' in probe:
                    shape(probe['clocks'], 'monotonic perf_counter')
                    for info in probe['clocks'].values():
                        shape(info, 'implementation monotonic adjustable resolution')
                        require(type(info['implementation']) is str and
                                type(info['monotonic']) is bool and
                                type(info['adjustable']) is bool and
                                type(info['resolution']) in (int, float) and
                                0 < info['resolution'] < float('inf'), 'invalid runtime clock info')
                    metadata = probe['clocks']
            clocks[runtime['id']] = {
                'available': metadata is not None, 'clocks': metadata,
                'source': next((ref for ref in manifest['files'] if ref['path'] == name), None),
                'caveat': ('Ledger elapsed_ns uses the monotonic clock. Zero ledger durations '
                           'are resolution-limited observations, not proof of zero elapsed work. '
                           'They remain unchanged. History timings use perf_counter and their '
                           'separate empty-bracket instrumentation checks.' if metadata else
                           'Runtime clock metadata is unavailable; ledger zero durations cannot '
                           'establish zero elapsed work. History timer metadata is separate.')}
        require('population.json' in files and
                hashlib.sha256(files['population.json']).hexdigest() ==
                plan['population_sha256'], 'population identity differs')
        population = parse_json(files['population.json'])
        shape(population, 'version recipe table_trajectories query_trajectories n_fit capacity '
              'artifacts chunks sessions selections coverage')
        require(population['version'] == 'workload-r002-population-v1' and
                integer(population['table_trajectories']) == 8192 and
                integer(population['query_trajectories']) == 1152, 'population identity differs')
        integer(population['n_fit'])
        artifacts, artifact_summaries = {}, []
        require(type(population['artifacts']) is list, 'artifacts must be list')
        for artifact in population['artifacts']:
            shape(artifact, 'size source_sha256 canonical_bytes key_bytes wire_bytes root_bytes '
                  'row_bytes comma_bytes row_census file labels')
            require(artifact['file'] in manifest['files'] and type(artifact['labels']) is list and
                    all(type(label) is str for label in artifact['labels']),
                    'artifact identity differs')
            metadata = {key: value for key, value in artifact.items()
                        if key not in ('file', 'labels')}
            artifact_summaries.append(artifact_report(metadata))
            require(artifact['size'] not in artifacts and
                    artifact['wire_bytes'] == artifact['file']['bytes'],
                    'duplicate artifact size or byte identity differs')
            artifacts[artifact['size']] = artifact
        for ref in [population['selections'], *population['chunks'], *population['sessions']]:
            require(ref in manifest['files'], 'population file identity differs')
        require(all(c['size'] == population['n_fit'] for c in cells.values()
                    if c['kind'] in ('history', 'reuse')), 'N_fit population/plan differs')
        for cell in cells.values():
            prefix = 'cells/' + cell['id'] + '/'
            require(prefix + 'intent.json' in files and prefix + 'environment.json' in files,
                    'missing frozen cell intent/environment')
            intent = parse_json(files[prefix + 'intent.json'])
            shape(intent, 'version cell_id cell source_sha256 protocol_sha256 population_sha256')
            runtime = next(r for r in plan['runtimes'] if r['id'] == cell['runtime'])
            expected = {'version': 'workload-r002-intent-v1', 'cell_id': cell['id'],
                        'cell': cell, 'source_sha256': runtime['source_sha256'],
                        'protocol_sha256': runtime['protocol_sha256'],
                        'population_sha256': plan['population_sha256']}
            require(json.dumps(intent, sort_keys=True) == json.dumps(expected, sort_keys=True),
                    'cell intent differs')
            environment = parse_json(files[prefix + 'environment.json'])
            require(type(environment) is dict and all(type(k) is str and type(v) is str
                    for k, v in environment.items()), 'invalid frozen environment')
        result_paths = {'cells/' + ident + '/result.json' for ident in cells}
        require({name for name in files if name.startswith('cells/') and
                 name.endswith('/result.json')}
                == result_paths, 'result-file census differs')
        terminal = parse_json(files['terminal.json'])
        shape(terminal, 'version cells')
        require(terminal['version'] == 'workload-r002-terminal-v1' and
                type(terminal['cells']) is list, 'invalid terminal')
        records, terminal_ids = [], []
        for row in terminal['cells']:
            shape(row, 'cell_id status')
            require(type(row['cell_id']) is str and row['cell_id'] in cells,
                    'unknown terminal cell')
            terminal_ids.append(row['cell_id'])
            name = 'cells/' + row['cell_id'] + '/result.json'
            require(name in files, 'missing retained result')
            record = parse_json(files[name])
            validate_result(record)
            cell = cells[row['cell_id']]
            if record['status'] == 'completed' and cell['kind'] in (
                    'construction', 'memory_traced', 'memory_untraced'):
                require(cell['size'] in artifacts, 'missing measured artifact')
                require(all(record['observations'].get(key) == artifacts[cell['size']][key]
                            for key in ('source_sha256', 'wire_bytes',
                                        'key_bytes', 'canonical_bytes')),
                        'measurement artifact identity differs')
            require(record['cell_id'] == row['cell_id'] and record['status'] == row['status'],
                    'terminal/result identity differs')
            for ref in record['files'] + [ref for key, ref in record['captures'].items()
                                         if key != 'truncated' and ref is not None]:
                require(ref in manifest['files'], 'result file identity differs')
            records.append(record)
        require(terminal_ids == list(cells), 'terminal census/order differs')
        return {'plan': plan, 'population': population, 'records': records,
                'artifact_summaries': artifact_summaries, 'runtime_clocks': clocks,
                'summary': summarize(records, plan)}
    except (OSError, KeyError, TypeError) as exc:
        raise ReportError('missing or malformed retained run: ' + str(exc)) from exc
