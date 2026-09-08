"""Read-only r002 evidence reductions. No poker imports or execution authority."""
import base64
import hashlib
import json
import math
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
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


def session_profile(events, outer_ns, strategy):
    """Admit complete one-hand observation before any quantitative phase attribution."""
    require(strategy in ('blueprint-v1', 'baseline-rules-v1'), 'invalid profile strategy')
    result = reduce_spans(events, outer_ns)
    optional = {'host:WireConsumer.provider_expected'} if strategy == 'blueprint-v1' else set()
    require(all(result['counts'][point] > 0 for point in CATEGORIES.keys() - optional),
            'missing applicable profile point', 'profile_invalid')
    counts = result['counts']
    expected = dict.fromkeys(CATEGORIES, 1)
    expected.update({'session:Schedule.derive': 2, 'session:Session.validate': 4,
                     'session:Admission.check': 6, 'host:Source.check': 7,
                     'host:OwnedInput.check': 8})
    exchanges, actions = counts['host:WireConsumer.exchange'], counts['host:WireConsumer.decision']
    expected.update({'host:WireConsumer.exchange': exchanges, 'host:Table.next_event': exchanges,
                     'host:ChildConnection.send': exchanges + 1,
                     'host:ChildConnection.receive': exchanges + actions + 4,
                     'host:WireConsumer.decision': actions,
                     'host:WireConsumer.provider_expected': 0 if optional else actions})
    require(counts == expected and exchanges >= actions > 0,
            'applicable profile count/relationship differs', 'profile_invalid')
    stack = []
    for event in events:
        point = event['point']
        if event['event'] == 'call':
            require(point == 'session:Session.run' or 'session:Session.run' in stack,
                    'applicable point outside Session.run', 'profile_invalid')
            parents = {'session:Admission.__init__': 'session:Session.prepare',
                       'host:Source.__init__': 'session:Admission.__init__',
                       'host:ChildConnection.__init__': 'session:Session.play_hand',
                       'host:WireConsumer.ready': 'session:Session.play_hand',
                       'host:WireConsumer.complete': 'session:Session.play_hand'}
            require(point not in parents or parents[point] in stack,
                    'applicable profile parent missing', 'profile_invalid')
            stack.append(point)
        else:
            stack.pop()
    return result


def query_traffic(natural):
    """The unrepeated independent-query census, separate from successful CLI actions."""
    require(type(natural) is list, 'natural query census must be list')
    seen, hits, other = set(), 0, 0
    for row in natural:
        shape(row, 'id trajectory_id hit street history_atoms')
        require(type(row['id']) is str and row['id'] and row['id'] not in seen and
                type(row['trajectory_id']) is str and row['trajectory_id'] and
                row['id'].startswith(row['trajectory_id'] + '-') and type(row['hit']) is bool and
                row['street'] in ('preflop', 'flop', 'turn', 'river'),
                'invalid or duplicate natural query context')
        atoms = integer(row['history_atoms'])
        require(atoms < 256, 'invalid query history length')
        seen.add(row['id'])
        hits += int(row['hit'])
        other += int(not (atoms == 0 or 3 <= atoms <= 5 or 7 <= atoms <= 9 or
                         15 <= atoms <= 17 or 31 <= atoms <= 33))
    return dict(count=len(natural), hits=hits, misses=len(natural) - hits,
                other_count=other, trajectory_count=len({r['trajectory_id'] for r in natural}),
                raw=natural)


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
          'worker_failed', 'cleanup_failed', 'containment_failed', 'interrupted'}
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
          'exit_code cleanup captures' +
          (' failed_session_facts' if 'failed_session_facts' in record else ''))
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
    if 'failed_session_facts' in record:
        require(record['status'] in ('failed', 'interrupted'), 'failed facts on successful cell')
        validate_failed_facts(record['failed_session_facts'], record['cell_id'])


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
            reduced = session_profile(obs['raw_events'], record['outer_ns'],
                                      cell['parameters']['strategy'])
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
    safety = response_safety(actions, n_fit) if n_fit is not None else {
        'triggered': None, 'contract_failure': False, 'actions': [], 'first_to_act_case_ids': []}
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


def summarize(records, plan, retention=None, envelope=None):
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
        if 'failed_session_facts' in record:
            require(cells[ident]['kind'] == 'session' and
                    record['failed_session_facts']['session_id'] ==
                    cells[ident]['parameters']['session_id'], 'failed facts cell binding differs')
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
        failed = [r['failed_session_facts'] for r in report['retained_results']
                  if 'failed_session_facts' in r]
        safety = report['rules']['response_margin']
        safety['failed_session_facts'] = failed
        positive = any(timing is not None and (timing['work_cutoff_crossed'] is True or
                       timing['deadline_crossed'] is True) for facts in failed for fact in
                       facts['facts'] for timing in [fact['record']['failure']['timing']])
        if positive:
            safety.update(triggered=True, contract_failure=True)
        elif any(c['kind'] == 'session' for c in incomplete) and not safety['contract_failure']:
            safety['contract_failure'] = None
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
    failures = [] if retention is None else retention['failures']
    durable = retention is None or retention['complete'] and not retention['missing']
    stopped = envelope is not None and envelope['stop'] is not None
    run_status = ('failed' if failures or stopped or census['failed'] or census['interrupted'] else
                  'completed' if complete and durable else 'incomplete')
    return {'planned': list(cells), 'census': census, 'run_status': run_status,
            'retention_failures': failures,
            'clean': complete and durable and not failures and not stopped and
                     all(not row['unresolved'] for row in runtimes.values()),
            'runtimes': runtimes}


_LIMIT = 128 * 1024 * 1024
_STREETS = ("preflop", "flop", "turn", "river")
_FAILURES = frozenset(("invalid_event event_order invalid_decision_context invalid_blueprint_entry "
    "clock_invalid clock_reversed work_cutoff_exceeded action_deadline_exceeded delivery_rejected "
    "delivery_ambiguous trace_write_failed trace_invalid settlement_mismatch "
    "source_binding_mismatch "
    "authority_absent").split())
_OUTER_FAILURES = _FAILURES | frozenset(("source_invalid input_invalid process_start_failed "
    "containment_failed protocol_invalid transport_failed action_invalid state_mismatch "
    "child_failed cleanup_failed output_failed input_failed command_invalid interrupted "
    "host_limit").split())
_TIMING = ("status interruption_reason wall_start_ns last_valid_observation_ns "
    "emission_observed_ns elapsed_ns response_compute_seconds response_uninstrumented_seconds "
    "work_cutoff_crossed deadline_crossed")
_WIRE_FIELDS = {
    "ready": ("source_commit source_manifest_sha256 blueprint_artifact_sha256 "
              "blueprint_sha256 evidentiary"),
    "action": "hand_id action_index seat street action",
    "event_result": "event_index status decision failure",
    "hand_result": ("complete settlement rank_source evidentiary preparation_compute_seconds "
        "post_terminal_compute_seconds interrupted_response_count accounting_complete "
        "failure_reason secondary_failures"),
    "session_result": ("status terminal_publication_compute_seconds accounting_complete "
        "failure_reason "
        "secondary_failures accounting_scope evidentiary"),
}
_BINDING = ("source_commit source_manifest_sha256 session_input_sha256 hand_input_sha256 "
    "blueprint_artifact_sha256 blueprint_sha256 controlled_seat button starting_stacks")


def _need(condition, code="protocol_invalid"):
    if not condition:
        raise ValueError(code)


def _shape(value, fields):
    _need(type(value) is dict and set(value) == set(fields.split()))


def _int(value, minimum=0, maximum=None):
    _need(type(value) is int and value >= minimum and (maximum is None or value <= maximum))
    return value


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _digest(value, width=64):
    _need(type(value) is str and re.fullmatch("[0-9a-f]{" + str(width) + "}", value) is not None)


def _encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
            + "\n").encode()


def _loads(raw):
    _need(type(raw) is bytes and 0 < len(raw) <= _LIMIT, "capture_invalid")
    def pairs(items):
        result = {}
        for key, value in items:
            _need(key not in result, "json_invalid")
            result[key] = value
        return result
    def integer(text):
        _need(len(text.lstrip("-")) <= 640, "json_invalid")
        return int(text)
    def constant(text):
        raise ValueError("json_invalid")
    value = json.loads(raw.decode("utf-8"), object_pairs_hook=pairs,
                       parse_int=integer, parse_constant=constant)
    return value


def _action(value):
    _shape(value, "kind raise_to")
    _need(value["kind"] in ("fold", "check", "call", "raise"))
    if value["kind"] == "raise":
        _int(value["raise_to"], 1)
    else:
        _need(value["raise_to"] is None)
    return value


def _seconds(value):
    _need(type(value) is float and math.isfinite(value) and value >= 0)
    return value


def _failed_timing(timing):
    """Exact trace.py:705-777 semantics; do not infer work cutoff from emission."""
    if timing is None:
        return None
    _shape(timing, _TIMING)
    _need(timing["status"] in ("completed", "interrupted"))
    start = _int(timing["wall_start_ns"])
    last = _int(timing["last_valid_observation_ns"], start)
    observed = last - start
    def converted(ns):
        try:
            return ns / 1_000_000_000
        except OverflowError:
            return math.inf
    def bounds(seconds, elapsed):
        _seconds(seconds)
        result = []
        for strict in (False, True):
            low, high = 0, elapsed + 1
            while low < high:
                mid = (low + high) // 2
                value = converted(mid)
                if value > seconds or (not strict and value == seconds):
                    high = mid
                else:
                    low = mid + 1
            result.append(low)
        _need(result[0] <= elapsed and converted(result[0]) == seconds)
        return result[0], result[1] - 1
    if timing["status"] == "completed":
        _need(timing["interruption_reason"] is None)
        _need(_int(timing["emission_observed_ns"]) == last)
        elapsed = _int(timing["elapsed_ns"])
        _need(elapsed == observed)
        intervals = [bounds(timing[key], elapsed) for key in
                     ("response_compute_seconds", "response_uninstrumented_seconds")]
        _need(sum(pair[0] for pair in intervals) <= elapsed <= sum(pair[1] for pair in intervals))
        _need(type(timing["work_cutoff_crossed"]) is bool and
              type(timing["deadline_crossed"]) is bool)
        _need(timing["deadline_crossed"] == (elapsed > 15_000_000_000))
    else:
        _need(timing["interruption_reason"] in _FAILURES)
        _need(all(timing[key] is None for key in ("emission_observed_ns", "elapsed_ns",
                  "response_compute_seconds", "response_uninstrumented_seconds")))
        _need(all(timing[key] is None or timing[key] is True
                  for key in ("work_cutoff_crossed", "deadline_crossed")))
    _need(timing["work_cutoff_crossed"] is not True or observed >= 14_000_000_000)
    _need(timing["deadline_crossed"] is not True or observed > 15_000_000_000)
    return timing


def session_binding(session_raw, source_commit, source_manifest_sha256,
                    blueprint_artifact_sha256, blueprint_sha256, strategy):
    """Caller first admits session/config/metadata. This hashes exact original input bytes."""
    _digest(source_commit, 40)
    for value in (source_manifest_sha256, blueprint_artifact_sha256, blueprint_sha256):
        _digest(value)
    _need(strategy in ("blueprint-v1", "baseline-rules-v1"))
    config = _loads(session_raw)
    _shape(config, "version button controlled_seat starting_stacks small_blind big_blind "
           "opponents hands")
    _need(config["version"] == "pontius-v0a-table-session-v1")
    _need(type(config["hands"]) is list and len(config["hands"]) == 1)
    _shape(config["hands"][0], "private_hands board_runout")
    _int(config["button"], 0, 5)
    _int(config["controlled_seat"], 0, 5)
    _need(type(config["starting_stacks"]) is list and len(config["starting_stacks"]) == 6)
    for stack in config["starting_stacks"]:
        _int(stack, 1)
    common = {key: value for key, value in config.items() if key != "hands"}
    common["version"] = "pontius-v0a-table-input-v1"
    hand_raw = _encoded(dict(common, **config["hands"][0]))
    result = dict(source_commit=source_commit, source_manifest_sha256=source_manifest_sha256,
        session_input_sha256=_sha(session_raw), hand_input_sha256=_sha(hand_raw),
        blueprint_artifact_sha256=blueprint_artifact_sha256, blueprint_sha256=blueprint_sha256,
        controlled_seat=config["controlled_seat"], button=config["button"],
        starting_stacks=list(config["starting_stacks"]))
    if strategy == "baseline-rules-v1":
        provider_config = dict(max_raises_per_street=1, playable_any_pair=True,
            playable_rank_min=10,
            playable_suited_ace=True, postflop_pair_call_cap_bb=1, postflop_two_pair_call_cap_bb=2,
            preflop_call_cap_bb=2, premium_ace_kickers=[12, 13], premium_call_cap_bb=None,
            premium_pair_min=10, provider="baseline-rules-v1", raise_size="legal_minimum",
            river_board_only="check_or_fold", version="pontius-decision-provider-config-v1")
        result.update(provider="baseline-rules-v1",
                      config_sha256=_sha(_encoded(provider_config)[:-1]))
    return result


def _session_ids(cell):
    _need(cell["kind"] == "session")
    params = cell["parameters"]
    _need(params["strategy"] in ("blueprint-v1", "baseline-rules-v1"))
    version = 2 if params["strategy"] == "baseline-rules-v1" else 1
    prefix = f"pontius-v0a-table-session-v{version}-correctness-"
    session_id = params["session_id"]
    _need(type(session_id) is str and session_id.startswith(prefix))
    suffix = session_id[len(prefix):]
    _need(re.fullmatch("[A-Za-z0-9_-]{1,40}", suffix) is not None)
    suffix += "-h01"
    protocol = f"pontius-v0a-event-interface-v{version}"
    return version, session_id, protocol, protocol + "-correctness-table-" + suffix, (
        f"pontius-v0a-table-host-v{version}-correctness-" + suffix)


def _ordered_failures(row, allowed):
    primary, secondary = row["failure_reason"], row["secondary_failures"]
    _need(primary is None or type(primary) is str and primary in allowed)
    _need(type(secondary) is list and all(type(v) is str and v in allowed for v in secondary))
    _need(len(set(secondary)) == len(secondary) and primary not in secondary)
    _need(primary is not None or not secondary)


def _session_envelope(raw_stdout, cell, reference):
    """Reusable envelope seam. No ready-frame value supplies an expected identity."""
    _shape(reference, "trajectory binding")
    binding = reference["binding"]
    version, session_id, protocol, child_id, hand_id = _session_ids(cell)
    extra = " provider config_sha256" if version == 2 else ""
    _shape(binding, _BINDING + extra)
    _digest(binding["source_commit"], 40)
    for key, value in binding.items():
        if key.endswith("sha256"):
            _digest(value)
    _need(binding["controlled_seat"] == cell["parameters"]["seat"])
    outer = _loads(raw_stdout)
    _shape(outer, "version session_id status stop_reason failure_reason secondary_failures "
        "source_commit "
        "input_sha256 blueprint_artifact_sha256 blueprint_sha256 requested_hands completed_hands "
        "next_button carried_stacks hands" + extra)
    _need(outer["version"] == f"pontius-v0a-table-session-result-v{version}"
          and outer["session_id"] == session_id)
    _need(outer["status"] in ("completed", "failed", "interrupted", "stopped"))
    _ordered_failures(outer, _OUTER_FAILURES)
    _need(_int(outer["requested_hands"], 1, 1) == 1 and _int(outer["completed_hands"], 0, 1) <= 1)
    _need(type(outer["hands"]) is list and len(outer["hands"]) == 1, "hand_unavailable")
    _need(outer["input_sha256"] == binding["session_input_sha256"])
    entry = outer["hands"][0]
    _shape(entry, "ordinal button starting_stacks result")
    _need(_int(entry["ordinal"], 1, 1) == 1 and _int(entry["button"], 0, 5) == binding["button"])
    _need(entry["starting_stacks"] == binding["starting_stacks"])
    hand = entry["result"]
    _shape(hand, "version session_id status failure_reason secondary_failures input_sha256 "
        "blueprint_artifact_sha256 blueprint_sha256 source_commit applied_actions settlement "
        "child_exit_code child_stdout_base64 child_stderr_base64 capture_truncated" + extra)
    _need(hand["version"] == f"pontius-v0a-table-session-hand-result-v{version}"
          and hand["session_id"] == hand_id)
    _need(hand["input_sha256"] == binding["hand_input_sha256"] and
          hand["status"] in ("completed", "failed"))
    for row in (outer, hand):
        for key in ("source_commit", "blueprint_artifact_sha256", "blueprint_sha256"):
            _need(row[key] == binding[key])
        if version == 2:
            _need(row["provider"] == binding["provider"] == "baseline-rules-v1"
                  and row["config_sha256"] == binding["config_sha256"])
    _ordered_failures(hand, _OUTER_FAILURES)
    _need(hand["child_exit_code"] is None or type(hand["child_exit_code"]) is int)
    _need(type(hand["capture_truncated"]) is bool)
    _need(type(hand["applied_actions"]) is list and len(hand["applied_actions"]) <= 256)
    for index, action in enumerate(hand["applied_actions"]):
        _shape(action, "index seat street action origin")
        _need(_int(action["index"]) == index)
        _int(action["seat"], 0, 5)
        _need(action["street"] in _STREETS and action["origin"] in ("bot", "opponent"))
        _need((action["origin"] == "bot") == (action["seat"] == binding["controlled_seat"]))
        _action(action["action"])
    if hand["status"] == "failed":
        _need(hand["settlement"] is None and outer["completed_hands"] == 0)
        _need(outer["carried_stacks"] == binding["starting_stacks"] and
              _int(outer["next_button"], 0, 5) == binding["button"])
    elif outer["completed_hands"] == 1:
        _need(hand["failure_reason"] is None and not hand["secondary_failures"])
    def captured(name):
        text = hand[name]
        _need(type(text) is str and len(text) <= _LIMIT)
        value = base64.b64decode(text, validate=True)
        _need(base64.b64encode(value).decode("ascii") == text and len(value) <= _LIMIT)
        return value
    child = captured("child_stdout_base64")
    captured("child_stderr_base64")
    return outer, hand, child, (version, session_id, protocol, child_id), binding


def _context(reference, index, event_index, binding):
    trajectory = reference["trajectory"]
    contexts = trajectory["contexts"]
    _need(type(contexts) is list and 1 <= index <= len(contexts) <= 256, "context_unbound")
    context = contexts[index - 1]
    expected, prefix = context["expected"], context["prefix"]
    _need(type(prefix) is list and len(prefix) <= 256)
    _need(expected["actor"] == binding["controlled_seat"] and expected["street"] in _STREETS)
    _need(expected["history_atoms"] == len(prefix))
    _need(event_index == len(prefix) - (index - 1) + _STREETS.index(expected["street"]),
          "context_unbound")
    return context


def _decision(value, version, child_id, index, event_index, reference, binding):
    context = _context(reference, index, event_index, binding)
    common = ("hand_id event_index action_index street_action_index seat street "
              "state_before_sha256 "
              "state_after_sha256 visible_cards_sha256 timing preparation_use failure_reason")
    fields = ("blueprint_sha256 selected_action selection_reason spine_reason" if version == 1 else
        "schema_version decision_sha256 source_manifest_sha256 provider config_sha256 "
        "fallback_blueprint_sha256 fallback_action fallback_reason proposal provider_outcome "
        "selection_reason selection_origin "
        "selected_action applied_action delivery_status delivered_action")
    _shape(value, common + " " + fields)
    _need(value["hand_id"] == child_id and _int(value["event_index"]) == event_index
          and _int(value["action_index"], 1) == index)
    expected = context["expected"]
    _need(_int(value["seat"], 0, 5) == binding["controlled_seat"] and
          value["street"] == expected["street"])
    street_index = 1 + sum(c["expected"]["street"] == expected["street"]
                           for c in reference["trajectory"]["contexts"][:index - 1])
    _need(_int(value["street_action_index"], 1) == street_index)
    for key in value:
        if key.endswith("sha256") and not (key == "state_after_sha256" and value[key] is None):
            _digest(value[key])
    _action(value["selected_action"])
    timing = _failed_timing(value["timing"])
    _need(timing is not None)
    _shape(value["preparation_use"], "producer_status artifact_sha256s credited_seconds")
    _need(value["preparation_use"]["producer_status"] == "producer_absent"
          and type(value["preparation_use"]["artifact_sha256s"]) is list
          and value["preparation_use"]["artifact_sha256s"] == []
          and _int(value["preparation_use"]["credited_seconds"]) == 0)
    failure = value["failure_reason"]
    _need(failure is None or type(failure) is str and failure in _FAILURES)
    if version == 1:
        _need(value["blueprint_sha256"] == binding["blueprint_sha256"]
              and value["selection_reason"] in ("table_hit", "passive_default")
              and value["spine_reason"] in ("candidate", "no_candidate", "illegal_candidate",
                  "work_budget_exhausted", "action_deadline_crossed"))
        _need(failure is None and timing["status"] == "completed"
              and timing["work_cutoff_crossed"] is False and timing["deadline_crossed"] is False)
        return value
    _need(value["schema_version"] == "pontius-provider-decision-v1")
    for key in ("source_manifest_sha256", "provider", "config_sha256"):
        _need(value[key] == binding[key])
    _need(value["fallback_blueprint_sha256"] == binding["blueprint_sha256"])
    _action(value["fallback_action"])
    _need(value["fallback_reason"] in ("table_hit", "passive_default"))
    outcome, reason, origin = (value[key] for key in
                               ("provider_outcome", "selection_reason", "selection_origin"))
    _need(outcome in ("not_called", "proposed", "abstained", "error", "invalid"))
    expected_outcome = dict(provider_selected="proposed", provider_abstained="abstained",
        provider_invalid="invalid", provider_error="error", provider_skipped_cutoff="not_called")
    _need(reason in (*expected_outcome, "provider_late"))
    _need(origin in ("provider", "blueprint_fallback") and
          (origin == "provider") == (reason == "provider_selected"))
    proposal = value["proposal"]
    if proposal is not None:
        _shape(proposal, "decision_sha256 action reason")
        _digest(proposal["decision_sha256"])
        _need(proposal["reason"] in ("abstain", "blueprint_hit", "blueprint_default",
              "premium_raise", "premium_call", "playable_call", "made_hand_raise",
              "made_hand_call", "pair_call", "free_check", "weak_fold"))
        _need((proposal["action"] is None) == (proposal["reason"] == "abstain"))
        if proposal["action"] is not None:
            _action(proposal["action"])
    _need(outcome not in ("not_called", "error") or proposal is None)
    if outcome in ("proposed", "abstained"):
        _need(proposal is not None and proposal["decision_sha256"] == value["decision_sha256"]
              and (proposal["action"] is None) == (outcome == "abstained"))
    _need(outcome != "not_called" if reason == "provider_late"
          else outcome == expected_outcome[reason])
    _need(value["selected_action"] == (proposal["action"] if origin == "provider"
                                     else value["fallback_action"]))
    applied, delivered, delivery = (value[key] for key in
                                    ("applied_action", "delivered_action", "delivery_status"))
    _need(delivery in ("not_attempted", "rejected", "accepted", "unknown"))
    _need((applied is None) == (value["state_after_sha256"] is None))
    if applied is not None:
        _action(applied)
        _need(applied == value["selected_action"])
    _need((delivered is not None) == (delivery == "accepted"))
    _need(delivery == "not_attempted" or applied is not None)
    if delivered is not None:
        _action(delivered)
        _need(delivered == applied)
    if reason in ("provider_late", "provider_skipped_cutoff"):
        _need(timing["work_cutoff_crossed"] is True and failure is not None)
    if timing["status"] == "completed":
        _need(not timing["work_cutoff_crossed"] or
              reason in ("provider_late", "provider_skipped_cutoff"))
        expected_failure = ("action_deadline_exceeded" if timing["deadline_crossed"] else
                            "work_cutoff_exceeded" if timing["work_cutoff_crossed"] else None)
        _need(failure == expected_failure and delivery == "accepted")
    else:
        _need(failure == timing["interruption_reason"])
    return value


def _failed_event(record, cell, reference, child_id, previous_event, next_action):
    """Validate one failed response, including the v2 mirrored decision exactly once."""
    version = 2 if cell["parameters"]["strategy"] == "baseline-rules-v1" else 1
    binding = reference["binding"]
    _need(record["status"] == "failed" and _int(record["event_index"]) == previous_event + 1)
    failure = record["failure"]
    _shape(failure, "hand_id event_index action_index code delivery_status delivered_action timing")
    _need(failure["hand_id"] == child_id and _int(failure["event_index"]) == record["event_index"])
    _need(_int(failure["action_index"], 1) == next_action, "context_unbound")
    _context(reference, next_action, record["event_index"], binding)
    _need(type(failure["code"]) is str and failure["code"] in _FAILURES)
    _need(failure["delivery_status"] in ("not_attempted", "rejected", "accepted", "unknown"))
    _need((failure["delivered_action"] is not None) == (failure["delivery_status"] == "accepted"))
    if failure["delivered_action"] is not None:
        _action(failure["delivered_action"])
    _failed_timing(failure["timing"])
    decision = record["decision"]
    if decision is not None:
        _need(version == 2)
        _decision(decision, version, child_id, next_action,
                  record["event_index"], reference, binding)
        _need(failure["code"] == decision["failure_reason"])
        for key in ("hand_id", "event_index", "action_index", "delivery_status",
                    "delivered_action", "timing"):
            _need(failure[key] == decision[key])
    return failure


def _closure(row, failed_seen):
    _ordered_failures(row, _FAILURES)
    _need(type(row["accounting_complete"]) is bool and row["evidentiary"] is False)
    if row["type"] == "hand_result":
        _need(type(row["complete"]) is bool)
        _int(row["interrupted_response_count"])
        for key in ("preparation_compute_seconds", "post_terminal_compute_seconds"):
            if row[key] is not None:
                _seconds(row[key])
        _need(row["rank_source"] in (None, "not_required", "host_supplied"))
        _need(not failed_seen or row["complete"] is False)
        if not row["complete"]:
            _need(row["settlement"] is None and row["rank_source"] is None)
    else:
        _need(row["status"] in ("completed", "failed")
              and row["accounting_scope"] == "runtime_begin_to_final_publication")
        if row["terminal_publication_compute_seconds"] is not None:
            _seconds(row["terminal_publication_compute_seconds"])
        _need(not failed_seen or row["status"] == "failed")


def failed_session_facts(raw_stdout, cell, reference, *, truncated=False):
    """Return bound raw failed event facts; complete means extraction coverage, not session success.

    Refusal offsets are decoded child byte offsets. Offset zero also denotes a
    failure before a child stream can be admitted. Missing closure uses EOF offset.
    """
    _need(type(raw_stdout) is bytes and type(truncated) is bool, "input_invalid")
    result = dict(version="workload-r002-failed-session-facts-v1", cell_id=cell["id"],
        session_id=cell["parameters"]["session_id"], stdout_sha256=_sha(raw_stdout),
        complete=False, refusals=[], facts=[])
    def refuse(offset, code):
        result["refusals"].append(dict(offset=offset, code=code))
    try:
        outer, hand, child, identities, binding = _session_envelope(raw_stdout, cell, reference)
    except (ValueError, TypeError, KeyError, RecursionError, OverflowError):
        refuse(0, "envelope_invalid")
        return result
    version, _, protocol, child_id = identities
    offset, previous_event, next_action = 0, -1, 1
    ready = failed_seen = hand_closed = session_closed = False
    last_observation = None
    pending = None
    seen = set()
    lines = child.splitlines(keepends=True)
    for line_number, line in enumerate(lines):
        try:
            _need(line_number < 1024 and line.endswith(b"\n") and b"\r" not in line,
                  "frame_invalid")
            _need(not session_closed, "trailing_frame")
            row = _loads(line)
            _need(type(row) is dict and row.get("type") in _WIRE_FIELDS)
            kind = row["type"]
            extra = " provider config_sha256" if kind == "ready" and version == 2 else ""
            _shape(row, "protocol session_id type " + _WIRE_FIELDS[kind] + extra)
            _need(row["protocol"] == protocol and row["session_id"] == child_id, "identity_invalid")
            if not ready:
                _need(kind == "ready" and row["evidentiary"] is False, "ready_invalid")
                for key in ("source_commit", "source_manifest_sha256",
                            "blueprint_artifact_sha256", "blueprint_sha256"):
                    _need(row[key] == binding[key], "identity_invalid")
                if version == 2:
                    _need(row["provider"] == binding["provider"] and
                          row["config_sha256"] == binding["config_sha256"])
                ready = True
            elif kind == "action":
                _need(not failed_seen and not hand_closed and pending is None)
                context = _context(reference, next_action, previous_event + 1, binding)
                _need(row["hand_id"] == child_id and _int(row["action_index"], 1) == next_action)
                _need(_int(row["seat"], 0, 5) == binding["controlled_seat"]
                      and row["street"] == context["expected"]["street"])
                _action(row["action"])
                pending = row
            elif kind == "event_result":
                _need(not failed_seen and not hand_closed and
                      _int(row["event_index"]) == previous_event + 1)
                _need(row["status"] in ("accepted", "decided", "failed"))
                if row["status"] == "failed":
                    _need(hand["status"] == "failed" and
                          outer["status"] in ("failed", "interrupted"))
                    failure = _failed_event(row, cell, reference, child_id,
                                            previous_event, next_action)
                    timing = failure["timing"]
                    if timing is not None:
                        _need(last_observation is None or
                              timing["wall_start_ns"] >= last_observation)
                    if failure["delivery_status"] == "accepted":
                        _need(pending is not None and
                              pending["action"] == failure["delivered_action"])
                    identity = (failure["hand_id"], failure["event_index"], failure["action_index"])
                    _need(identity not in seen, "duplicate_fact")
                    seen.add(identity)
                    result["facts"].append(dict(hand_id=identity[0], event_index=identity[1],
                        action_index=identity[2],
                        offset=offset, bytes=len(line), sha256=_sha(line), record=row))
                    failed_seen = True
                    pending = None
                elif row["status"] == "decided":
                    _need(pending is not None and row["failure"] is None)
                    decision = _decision(row["decision"], version, child_id, next_action,
                                         row["event_index"], reference, binding)
                    _need(decision["failure_reason"] is None and
                          decision["selected_action"] == pending["action"])
                    _need(decision["timing"]["status"] == "completed"
                          and decision["timing"]["work_cutoff_crossed"] is False
                          and decision["timing"]["deadline_crossed"] is False)
                    _need(last_observation is None or
                          decision["timing"]["wall_start_ns"] >= last_observation)
                    last_observation = decision["timing"]["last_valid_observation_ns"]
                    next_action += 1
                    pending = None
                else:
                    _need(pending is None and row["failure"] is None and row["decision"] is None)
                    # Cannot skip an expected controlled response with a row-shaped acknowledgement.
                    if next_action <= len(reference["trajectory"]["contexts"]):
                        ctx = reference["trajectory"]["contexts"][next_action - 1]
                        expected_event = (len(ctx["prefix"]) - (next_action - 1) +
                                          _STREETS.index(ctx["expected"]["street"]))
                        _need(row["event_index"] != expected_event, "context_unbound")
                previous_event = row["event_index"]
            elif kind == "hand_result":
                _need(not hand_closed and pending is None)
                _closure(row, failed_seen)
                hand_closed = True
            elif kind == "session_result":
                _need(hand_closed and pending is None)
                _closure(row, failed_seen)
                session_closed = True
            else:
                raise ValueError("unexpected_frame")
        except (ValueError, TypeError, KeyError, RecursionError, OverflowError) as error:
            allowed = {"frame_invalid", "trailing_frame", "identity_invalid", "ready_invalid",
                       "context_unbound", "duplicate_fact", "unexpected_frame"}
            refuse(offset, str(error) if str(error) in allowed else "protocol_invalid")
            break
        offset += len(line)
    if not session_closed:
        refuse(len(child), "closure_missing")
    if truncated or hand["capture_truncated"]:
        refuse(len(child), "capture_truncated")
    result["complete"] = session_closed and not result["refusals"]
    return result


def validate_failed_facts(value, cell_id):
    """Pure shape/timing admission; read_run separately re-derives all raw provenance."""
    shape(value, 'version cell_id session_id stdout_sha256 complete refusals facts')
    require(value['version'] == 'workload-r002-failed-session-facts-v1' and
            value['cell_id'] == cell_id and type(value['session_id']) is str and
            type(value['complete']) is bool and type(value['refusals']) is list and
            type(value['facts']) is list, 'invalid failed session facts')
    digest(value['stdout_sha256'])
    for refusal in value['refusals']:
        shape(refusal, 'offset code')
        integer(refusal['offset'])
        require(refusal['code'] in ('envelope_invalid', 'frame_invalid', 'trailing_frame',
            'identity_invalid', 'ready_invalid', 'context_unbound', 'duplicate_fact',
            'unexpected_frame', 'protocol_invalid', 'closure_missing', 'capture_truncated'),
            'unknown failed facts refusal')
    require(not value['complete'] or not value['refusals'], 'complete failed facts have refusal')
    seen, previous_end = set(), 0
    for fact in value['facts']:
        shape(fact, 'hand_id event_index action_index offset bytes sha256 record')
        require(type(fact['hand_id']) is str and fact['hand_id'], 'invalid failed hand identity')
        for key in ('event_index', 'action_index', 'offset', 'bytes'):
            integer(fact[key])
        digest(fact['sha256'])
        identity = fact['hand_id'], fact['event_index'], fact['action_index']
        require(identity not in seen and fact['action_index'] > 0 and fact['bytes'] > 0 and
                fact['offset'] >= previous_end, 'duplicate or overlapping failed facts')
        seen.add(identity)
        previous_end = fact['offset'] + fact['bytes']
        record = fact['record']
        shape(record, 'protocol session_id type event_index status decision failure')
        require(record['type'] == 'event_result' and record['status'] == 'failed' and
                record['event_index'] == fact['event_index'] and
                record['session_id'] == fact['hand_id'], 'failed frame identity differs')
        failure = record['failure']
        shape(failure, 'hand_id event_index action_index code delivery_status '
              'delivered_action timing')
        require(all(failure[key] == fact[key] for key in
                    ('hand_id', 'event_index', 'action_index')), 'failed identity mirror differs')
        _failed_timing(failure['timing'])
        if record['decision'] is not None:
            require(all(record['decision'].get(key) == failure[key] for key in
                ('hand_id', 'event_index', 'action_index', 'delivery_status',
                 'delivered_action', 'timing')), 'failed timing mirror differs')


def admit_schedule(plan, n_fit):
    """Public admission of the fixed r002 recipe; pure reducers accept smaller plans."""
    validate_plan(plan)
    require([r['id'] for r in plan['runtimes']] == ['3.11', '3.14'],
            'public runtime schedule differs')
    require(integer(n_fit) <= 65536, 'N_fit exceeds complete artifact population')
    expected = []
    ordinals = [d * 72 + seat * 12 + d % 3 * 2 + d % 2
                for d in range(16) for seat in (d % 6, (d + 3) % 6)]
    for index, runtime in enumerate(plan['runtimes']):
        executable = ('D:/Pontius-tools/py311/Scripts/python.exe',
                      'D:/Pontius/.venv/Scripts/python.exe')[index]
        require(PureWindowsPath(runtime['executable']) == PureWindowsPath(executable),
                'public runtime executable differs')
        for field in ('executable', 'resolved_executable', 'source_root',
                      'run_root', 'authorization'):
            path = PureWindowsPath(runtime[field])
            require(path.is_absolute() and '..' not in path.parts and
                    (field == 'resolved_executable' or path.drive.upper() == 'D:'),
                    'public runtime path differs')
        source = PureWindowsPath(runtime['source_root'])
        run = PureWindowsPath(runtime['run_root'])
        require(PureWindowsPath(runtime['authorization']) == source /
                'docs/architecture/v0a-blueprint-workload-r001/invocation-authority.json',
                'runtime authority path differs from admitted source')
        tag = runtime['id'].replace('.', '')
        def add(kind, size, parameters):
            ident = f'r002-{tag}-{len(expected):05d}'
            argv = [runtime['executable'], '-B', '-P',
                str(source / 'tools/v0a_blueprint_workload.py'), 'worker', '--source-root',
                str(source), '--run-root', str(run), '--authorization', runtime['authorization'],
                '--cell', ident]
            if kind == 'session' and not parameters['diagnostic']:
                argv = [runtime['executable'], '-B', '-P',
                    str(source / 'tools/v0a_table_session.py'), '--session',
                    parameters['session_path'], '--blueprint', parameters['blueprint_path'],
                    '--session-id', parameters['session_id'], '--strategy', parameters['strategy'],
                    '--auto', '--format', 'json']
            expected.append(dict(id=ident, runtime=runtime['id'], kind=kind, size=size,
                                 parameters=parameters, argv=argv))
        def construction(sizes):
            for size in dict.fromkeys(sizes):
                for kind in ('construction', 'memory_traced', 'memory_untraced'):
                    for observation in range(5):
                        add(kind, size, dict(observation=observation))
        construction([0, n_fit] if index == 0 else [0, n_fit, 8192])
        for name in (('0', '3-5', '7-9', '15-17', '31-33') if index == 0 else ('0', '31-33')):
            for operation in ('key', 'hash', 'lookup', 'identity', 'provider'):
                add('history', n_fit, dict(bin=name, operation=operation, blocks=5,
                    subblocks=['hit', 'miss', 'miss', 'hit'], warmups=10, batches=10,
                    batch_calls=100, individual_calls=1000, empty_brackets=10000,
                    empty_batches=5, loop_batches=5))
        for hands in ((1, 2, 8, 32) if index == 0 else (1, 8)):
            for repetition, arms in enumerate((('fresh', 'retained'), ('retained', 'fresh'),
                                               ('retained', 'fresh'), ('fresh', 'retained'))):
                for arm in arms:
                    add('reuse', n_fit, dict(hands=hands, repetition=repetition, arm=arm,
                                           trajectory_ordinals=ordinals[:hands]))
        ordinal = diagnostic_ordinal = 0
        for deal in ((0, 1) if index == 0 else (0,)):
            for seat in (range(6) if index == 0 else (0, 3)):
                for lineup in ((0, 1) if index == 0 else (0,)):
                    for size in (0, n_fit):
                        for strategy in ('blueprint-v1', 'baseline-rules-v1'):
                            diagnostic = (deal == 0 and seat in (0, 2, 3) and lineup == 0
                                          if index == 0 else size == n_fit)
                            modes = ([True, False] if diagnostic_ordinal % 2 == 0
                                     else [False, True])
                            version = 2 if strategy == 'baseline-rules-v1' else 1
                            for profile in modes if diagnostic else [False]:
                                add('session', size, dict(diagnostic=profile, ordinal=ordinal,
                                    deal=deal, seat=seat, lineup=lineup, strategy=strategy,
                                    session_id=(f'pontius-v0a-table-session-v{version}-correctness-'
                                                f'r002-{tag}-{ordinal:03d}-'
                                                + ('d' if profile else 'u')),
                                    session_path=str(run /
                                        f'sessions/d{deal}-s{seat}-l{lineup}.json'),
                                    blueprint_path=str(run / f'artifacts/{size}.json')))
                            ordinal += 1
                            diagnostic_ordinal += int(diagnostic)
        if index == 0:
            construction(n for n in (0, 128, 1024, 8192, 65536) if n not in (0, n_fit))
            for size, calls in ((1024, 20), (8192, 10), (65536, 2)):
                add('comparison', size, dict(blocks=5, warmups=20, calls_per_class=calls,
                    provider_order=['legacy', 'prepared'], alternate_provider_first=True,
                    continuous_cycle=True))
    require(plan['cells'] == expected, 'fixed public schedule/argv differs')


def context_record(record):
    shape(record, 'version id trajectory_id factors deal prefix expected')
    require(record['version'] == 'workload-r002-context-v1' and
            type(record['prefix']) is list and len(record['prefix']) < 256 and
            type(record['trajectory_id']) is str and
            record['id'] == f"{record['trajectory_id']}-{len(record['prefix']):03d}",
            'context identity differs')
    expected = record['expected']
    shape(expected, 'actor street history_atoms key_hex key_sha256 decision_sha256 passive_action')
    require(integer(expected['actor']) < 6 and
            integer(expected['history_atoms']) == len(record['prefix']),
            'context history/actor differs')
    digest(expected['key_sha256'])
    digest(expected['decision_sha256'])
    require(type(expected['key_hex']) is str, 'invalid context key bytes')
    try:
        key = bytes.fromhex(expected['key_hex'])
    except ValueError as exc:
        raise ReportError('invalid context key bytes') from exc
    require(key.hex() == expected['key_hex'] and hashlib.sha256(key).hexdigest() ==
            expected['key_sha256'], 'context key digest differs')
    return key


def admit_queries(population, read):
    """Bind every unrepeated query row and timed selection to retained byte identities."""
    selected = parse_json(read(population['selections']['path']))
    shape(selected, 'version first_context history natural reuse comparisons')
    require(selected['version'] == 'workload-r002-selections-v1', 'selection version differs')
    query_refs = [ref for ref in population['chunks'] if '/query-' in ref['path']]
    require([ref['path'] for ref in query_refs] ==
            [f'population/query-{n:03d}.jsonl' for n in range(9)], 'query chunk census differs')
    trajectories, contexts = [], []
    for ref in query_refs:
        lines = read(ref['path']).splitlines(keepends=True)
        require(len(lines) == 128 and all(line.endswith(b'\n') for line in lines),
                'query trajectory chunk count differs')
        for line in lines:
            trajectory = parse_json(line)
            shape(trajectory, 'version id factors seed deal contexts actions settlement')
            require(trajectory['version'] == 'workload-r002-trajectory-v1' and
                    trajectory['id'] == f'r002-query-{len(trajectories):04d}' and
                    type(trajectory['contexts']) is list and trajectory['contexts'],
                    'query trajectory identity differs')
            for context in trajectory['contexts']:
                context_record(context)
                require(context['trajectory_id'] == trajectory['id'], 'context parent differs')
                contexts.append(context)
            trajectories.append(trajectory)
    require(len(trajectories) == 1152, 'query trajectory census differs')
    require(selected['first_context'] == contexts[0], 'first context differs')
    keys_by_size = {}
    for artifact in population['artifacts']:
        document = parse_json(read(artifact['file']['path']))
        shape(document, 'version source_id entries')
        require(type(document['entries']) is list and len(document['entries']) == artifact['size'],
                'artifact key census differs')
        keys = []
        for entry in document['entries']:
            shape(entry, 'key action')
            keys.append(json.dumps(entry['key'], sort_keys=True,
                                   separators=(',', ':'), allow_nan=False).encode('ascii'))
        require(len(set(keys)) == len(keys), 'duplicate artifact key')
        keys_by_size[artifact['size']] = set(keys)
    fitted = keys_by_size[population['n_fit']]
    expected_natural = [dict(id=r['id'], trajectory_id=r['trajectory_id'],
        hit=bytes.fromhex(r['expected']['key_hex']) in fitted, street=r['expected']['street'],
        history_atoms=r['expected']['history_atoms']) for r in contexts]
    require(selected['natural'] == expected_natural, 'natural query membership/census differs')
    traffic = query_traffic(selected['natural'])
    ordinals = [d * 72 + s * 12 + d % 3 * 2 + d % 2
                for d in range(16) for s in (d % 6, (d + 3) % 6)]
    require(selected['reuse'] == [trajectories[i]['contexts'] for i in ordinals],
            'reuse selected context census/order differs')
    bins = ('0', '3-5', '7-9', '15-17', '31-33')
    shape(selected['history'], ' '.join(bins))
    shape(selected['comparisons'], '1024 8192 65536')
    def bucket(record):
        atoms = record['expected']['history_atoms']
        return next((b for b, lo, hi in [('0', 0, 0), ('3-5', 3, 5), ('7-9', 7, 9),
                     ('15-17', 15, 17), ('31-33', 31, 33)] if lo <= atoms <= hi), 'other')
    for choices, members, history_bin in (
            [(selected['history'][b], fitted, b) for b in bins] +
            [(selected['comparisons'][str(n)], keys_by_size[n], None)
             for n in (1024, 8192, 65536)]):
        shape(choices, 'hit miss')
        for label, rows in choices.items():
            require(type(rows) is list and len(rows) <= 100, 'selected context count differs')
            keys = [context_record(row) for row in rows]
            require(len(set(keys)) == len(keys) and all((key in members) == (label == 'hit')
                    for key in keys) and all(history_bin is None or bucket(r) == history_bin
                                           for r in rows), 'selected context membership differs')
        expected_misses, seen = [], set()
        for row in contexts:
            key = bytes.fromhex(row['expected']['key_hex'])
            if key not in members and key not in seen and (
                    history_bin is None or bucket(row) == history_bin):
                expected_misses.append(row)
                seen.add(key)
                if len(expected_misses) == 100:
                    break
        require(choices['miss'] == expected_misses, 'selected miss context order differs')
    return selected, trajectories, keys_by_size, traffic


def admit_context_observations(observations, cell, selected):
    kind, params = cell['kind'], cell['parameters']
    if kind == 'history':
        choices = selected['history'][params['bin']]
        for block in observations['blocks']:
            require(all(block[label]['context_ids'] == [r['id'] for r in choices[label]]
                        for label in ('hit', 'miss')), 'history frozen context order differs')
    elif kind == 'reuse':
        rows = [r for sequence in selected['reuse'][:params['hands']] for r in sequence]
        require(observations['context_ids'] == [r['id'] for r in rows] and
                observations['distinct_keys'] == len({r['expected']['key_hex'] for r in rows}),
                'reuse frozen context order/key census differs')
    elif kind == 'comparison':
        choices = selected['comparisons'][str(cell['size'])]
        count = params['calls_per_class']
        for index, block in enumerate(observations['blocks']):
            for label, rows in choices.items():
                ids = [rows[(index * count + i) % len(rows)]['id']
                       for i in range(count)] if rows else []
                require(all(provider[label]['context_ids'] == ids for provider in block.values()),
                        'comparison frozen context cycle differs')


def admit_claim(stage, runtime, qualified, source_rows, read):
    claim = parse_json(read(stage + '-claim.json'))
    shape(claim, 'version stage controller_pid controller_created_100ns source_commit '
          'source_tree source_manifest_sha256 authority_sha256 run_root')
    authority = 'docs/architecture/v0a-blueprint-workload-r001/invocation-authority.json'
    require(claim['version'] == 'workload-r002-claim-v2' and claim['stage'] == stage and
            claim['source_commit'] == qualified['source_commit'] and
            claim['source_manifest_sha256'] == runtime['source_sha256'] and
            claim['authority_sha256'] == source_rows.get(authority) and
            PureWindowsPath(claim['run_root']) == PureWindowsPath(runtime['run_root']),
            'stage claim source/authority differs')
    digest(claim['authority_sha256'])
    require(type(claim['source_tree']) is str and
            re.fullmatch('[0-9a-f]{40}', claim['source_tree']), 'invalid claimed source tree')
    for key in ('controller_pid', 'controller_created_100ns'):
        require(integer(claim[key]) > 0, 'invalid controller identity')
    return claim


def admit_native(native, cell, runtime, claim, plan_ref, read, refs, *, completed=False):
    stage = claim['stage']
    qualification = stage == 'qualify'
    prefix = 'qualification-' if qualification else 'cells/' + cell['id'] + '/'
    shape(native, 'cause secondary exit_code truncated samples redirector_pid launch_ns '
          'outer_ns cleanup_ns cleanup worker_failure worker_grant' +
          (' stage_ns' if qualification else ''))
    require(native['cause'] is None or native['cause'] in CAUSES, 'unknown native cause')
    require(type(native['secondary']) is list and
            all(cause in CAUSES for cause in native['secondary']) and
            len(set(native['secondary'])) == len(native['secondary']), 'invalid native causes')
    for key in ('launch_ns', 'outer_ns', 'cleanup_ns'):
        integer(native[key])
    require(native['exit_code'] is None or type(native['exit_code']) is int,
            'invalid native exit code')
    require(type(native['truncated']) is bool and type(native['samples']) is list,
            'invalid native capture/samples')
    if native['redirector_pid'] is not None:
        require(integer(native['redirector_pid']) > 0, 'invalid redirector identity')
    shape(native['cleanup'], 'verified active')
    require(type(native['cleanup']['verified']) is bool, 'invalid native cleanup')
    if native['cleanup']['active'] is not None:
        integer(native['cleanup']['active'])
    previous = 0
    for sample in native['samples']:
        shape(sample, 'pid ns stage private_commit working_set '
              'peak_private_commit peak_working_set')
        for key in sample:
            if key != 'stage':
                integer(sample[key])
        require(sample['pid'] > 0 and previous <= sample['ns'] <= native['outer_ns'] and
                sample['stage'] in ('idle', 'read', 'decode', 'prepare', 'first', 'final',
                                    'ready', 'periodic'), 'invalid native memory sample')
        previous = sample['ns']
    if qualification:
        require(native['outer_ns'] <= integer(native['stage_ns']) <= 1_800_000_000_000,
                'qualification stage timing differs')
    if completed:
        require(native['cause'] is None and not native['secondary'] and
                native['exit_code'] == 0 and not native['truncated'] and
                native['cleanup'] == {'verified': True, 'active': 0},
                'completed native execution contains failure')
    stderr = read(prefix + 'stderr.bin')
    read(prefix + 'stdout.bin')
    control_frames = [line for line in stderr.splitlines(keepends=True)
                      if line.startswith(b'PONTIUS_WORKLOAD_CONTROL ')]
    require(not completed or not control_frames, 'completed worker has original failure frame')
    failure = native['worker_failure']
    if failure is not None:
        shape(failure, 'version cell_id cause secondary exception_type')
        require(failure['version'] == 'workload-r002-worker-failure-v1' and
                failure['cell_id'] == cell['id'] and failure['cause'] in CAUSES and
                type(failure['secondary']) is list and all(code in CAUSES for code in
                failure['secondary']) and len(set(failure['secondary'])) ==
                len(failure['secondary']) and type(failure['exception_type']) is str and
                0 < len(failure['exception_type']) <= 128, 'invalid typed worker failure')
        require(control_frames == [b'PONTIUS_WORKLOAD_CONTROL ' + _encoded(failure)],
                'typed worker failure raw provenance differs')
        causes = [native['cause'], *native['secondary']]
        ordered = [failure['cause'], *failure['secondary']]
        positions = [causes.index(code) if code in causes else -1 for code in ordered]
        require(all(position >= 0 for position in positions) and positions == sorted(positions),
                'typed worker causes lost from supervision')
    grant = native['worker_grant']
    worker = qualification or cell['kind'] != 'session' or cell['parameters']['diagnostic']
    require(worker or grant is None, 'ordinary session unexpectedly consumed worker grant')
    require(not completed or not worker or grant is not None, 'completed worker lacks grant')
    receipt_name, intent_name = prefix + 'worker-grant.json', prefix + 'worker-grant-intent.json'
    require((receipt_name in refs) == (grant is not None), 'consumed grant retention differs')
    if grant is None and intent_name not in refs:
        return
    require(worker, 'ordinary session has worker intent')
    intent = parse_json(read(intent_name))
    shape(intent, 'version stage cell_id runtime_id source_commit source_tree '
          'source_manifest_sha256 authority_sha256 stage_claim_sha256 runtime_sha256 '
          'plan_sha256 cell_sha256 controller_pid controller_created_100ns source_root '
          'run_root nonce_sha256')
    expected = dict(version='workload-r002-worker-grant-intent-v1', stage=stage,
        cell_id=cell['id'], runtime_id=runtime['id'], source_commit=claim['source_commit'],
        source_tree=claim['source_tree'], source_manifest_sha256=runtime['source_sha256'],
        authority_sha256=claim['authority_sha256'],
        stage_claim_sha256=refs[stage + '-claim.json']['sha256'],
        runtime_sha256=hashlib.sha256(_encoded(runtime)).hexdigest(),
        plan_sha256=None if qualification else plan_ref['sha256'],
        cell_sha256=hashlib.sha256(_encoded(cell)).hexdigest(),
        controller_pid=claim['controller_pid'],
        controller_created_100ns=claim['controller_created_100ns'])
    require(all(type(intent[key]) is type(value) and intent[key] == value
                for key, value in expected.items()), 'worker intent identity differs')
    for key in ('source_root', 'run_root'):
        require(type(intent[key]) is str and
                PureWindowsPath(intent[key]) == PureWindowsPath(runtime[key]),
                'worker intent path differs')
    digest(intent['nonce_sha256'])
    if grant is None:
        return
    shape(grant, ' '.join(intent) + ' intent_sha256 redirector_pid redirector_created_100ns '
          'worker_pid worker_created_100ns pipe_server_pid pipe_client_pid job_member consumed')
    expected = dict(intent, version='workload-r002-worker-grant-v1',
                    intent_sha256=refs[intent_name]['sha256'])
    require(all(type(grant[key]) is type(value) and grant[key] == value
                for key, value in expected.items()) and grant == parse_json(read(receipt_name)),
            'consumed grant provenance differs')
    for key in ('redirector_pid', 'redirector_created_100ns', 'worker_pid',
                'worker_created_100ns', 'pipe_server_pid', 'pipe_client_pid'):
        require(integer(grant[key]) > 0, 'invalid grant process identity')
    require(grant['job_member'] is True and grant['consumed'] is True and
            grant['redirector_pid'] == native['redirector_pid'] and
            grant['pipe_server_pid'] == grant['pipe_client_pid'] == claim['controller_pid'] and
            grant['worker_pid'] != claim['controller_pid'] and
            (grant['worker_pid'] != grant['redirector_pid'] or
             grant['worker_created_100ns'] == grant['redirector_created_100ns']),
            'consumed grant process binding differs')
    ready = {key: grant[key] for key in ('cell_id', 'intent_sha256', 'worker_pid',
             'worker_created_100ns', 'pipe_server_pid', 'pipe_client_pid')}
    ready['version'] = 'workload-r002-worker-ready-v1'
    frames = [line for line in stderr.splitlines(keepends=True)
              if line.startswith(b'PONTIUS_WORKLOAD_GRANT ')]
    expected_frame = b'PONTIUS_WORKLOAD_GRANT ' + _encoded(ready)
    failed_admission = not completed and 'source_invalid' in [native['cause'], *native['secondary']]
    require(frames == [expected_frame] or failed_admission and frames and
            frames[0] == expected_frame,
            'consumed grant ready provenance differs')


def admit_qualification(plan, population, read, refs):
    qualified = parse_json(read('qualified.json'))
    shape(qualified, 'version source_commit plan_sha256 manifest')
    require(qualified['version'] == 'workload-r002-qualified-v1' and
            qualified['plan_sha256'] == refs['plan.json']['sha256'] and
            qualified['manifest'] == refs['qualification-manifest.json'],
            'qualification plan identity differs')
    commit = qualified['source_commit']
    require(type(commit) is str and len(commit) == 40 and
            all(c in '0123456789abcdef' for c in commit), 'qualification commit differs')
    manifest = parse_json(read('qualification-manifest.json'))
    shape(manifest, 'version files')
    require(manifest['version'] == 'workload-r002-manifest-v1' and
            type(manifest['files']) is list, 'qualification manifest differs')
    names = [file_ref(ref) for ref in manifest['files']]
    require(len(set(names)) == len(names) and all(ref == refs.get(ref['path'])
            for ref in manifest['files']), 'qualification retained provenance differs')
    required = {'plan.json', 'runtimes.json', 'population.json', 'qualification-environment.json',
                'qualification-intent.json', 'qualification-result.json', 'qualify-claim.json',
                'qualification-stdout.bin', 'qualification-stderr.bin',
                'qualification-worker-grant-intent.json', 'qualification-worker-grant.json',
                population['selections']['path']}
    required.update(ref['path'] for ref in population['chunks'] + population['sessions'])
    required.update(artifact['file']['path'] for artifact in population['artifacts'])
    require(parse_json(read('runtimes.json')) == plan['runtimes'],
            'qualification runtime identity differs')
    base = parse_json(read('qualification-environment.json'))
    allowed = {'systemroot', 'windir', 'comspec', 'systemdrive', 'number_of_processors',
               'processor_architecture', 'processor_identifier', 'userprofile', 'localappdata',
               'appdata', 'programdata', 'pythonpath', 'temp', 'tmp', 'pontius_git'}
    require(type(base) is dict and all(type(k) is str and type(v) is str for k, v in base.items())
            and len({k.casefold() for k in base}) == len(base) and
            {k.casefold() for k in base} <= allowed, 'qualification environment differs')
    environments, manifests = {}, {}
    for runtime in plan['runtimes']:
        prefix = 'admission/' + runtime['id']
        required.update(prefix + tail for tail in
                        ('-source.manifest', '-runtime-stdout.bin', '-runtime-stderr.bin',
                         '-venv.json'))
        require(read(prefix + '-runtime-stderr.bin') == b'', 'runtime probe stderr differs')
        source = read(prefix + '-source.manifest')
        require(hashlib.sha256(source).hexdigest() == runtime['source_sha256'] and
                source.endswith(b'\n') and b'\r' not in source, 'source manifest identity differs')
        lines = source.decode('ascii').splitlines()
        source_rows = {}
        for line in lines:
            require(len(line) > 66 and line[64:66] == '  ', 'source manifest row differs')
            sha, name = line[:64], line[66:]
            digest(sha)
            file_ref(dict(path=name, sha256=sha, bytes=0))
            require(name not in source_rows, 'duplicate source manifest row')
            source_rows[name] = sha
        require(list(source_rows) == sorted(source_rows) and source_rows.get(
            'docs/architecture/v0a-blueprint-workload-r001/execution-protocol.md') ==
            runtime['protocol_sha256'], 'source protocol binding differs')
        manifests[runtime['id']] = source_rows
        venv = parse_json(read(prefix + '-venv.json'))
        shape(venv, 'path sha256')
        digest(venv['sha256'])
        require(PureWindowsPath(venv['path']) ==
                PureWindowsPath(runtime['executable']).parents[1] / 'pyvenv.cfg',
                'runtime venv identity differs')
        environment = {k: v for k, v in base.items()
                       if k.casefold() not in ('pythonpath', 'temp', 'tmp', 'pontius_git')}
        environment.update(PYTHONPATH=str(PureWindowsPath(runtime['source_root']) / 'src'),
            TEMP=str(PureWindowsPath(runtime['run_root']) / 'temporary' / runtime['id']),
            TMP=str(PureWindowsPath(runtime['run_root']) / 'temporary' / runtime['id']),
            PONTIUS_GIT='C:\\Program Files\\Git\\cmd\\git.exe')
        environments[runtime['id']] = environment
    require(base == environments['3.11'], 'qualification environment invocation differs')
    require(required <= set(names), 'missing qualification provenance')
    runtime = plan['runtimes'][0]
    require(manifests['3.11'] == manifests['3.14'], 'runtime source snapshots differ')
    claims = {stage: admit_claim(stage, runtime, qualified, manifests['3.11'], read)
              for stage in ('qualify', 'run')}
    require(all(claims['qualify'][key] == claims['run'][key] for key in
                ('source_commit', 'source_tree', 'source_manifest_sha256', 'authority_sha256')),
            'qualification/run claimed source identity differs')
    intent = parse_json(read('qualification-intent.json'))
    shape(intent, 'argv recipe_sha256')
    argv = [runtime['executable'], '-B', '-P', str(PureWindowsPath(runtime['source_root']) /
        'tools/v0a_blueprint_workload.py'), 'worker', '--source-root',
        str(PureWindowsPath(runtime['source_root'])), '--run-root',
        str(PureWindowsPath(runtime['run_root'])), '--authorization',
        runtime['authorization'], '--cell', 'qualification']
    recipe_sha256 = hashlib.sha256(_encoded(population['recipe'])).hexdigest()
    require(intent == dict(argv=argv, recipe_sha256=recipe_sha256),
            'qualification invocation differs')
    qualification_cell = dict(id='qualification', kind='qualification', runtime=runtime['id'],
                              recipe_sha256=recipe_sha256)
    admit_native(parse_json(read('qualification-result.json')), qualification_cell, runtime,
                 claims['qualify'], refs['plan.json'], read, refs, completed=True)
    return qualified, environments, claims


def admit_raw_result(record, cell, read, refs, selected, runtime, claim, plan_ref):
    prefix = 'cells/' + cell['id'] + '/'
    expected = {name: ref for name, ref in refs.items()
                if name.startswith(prefix) and name != prefix + 'result.json'}
    require(len(record['files']) == len(expected) and
            {ref['path']: ref for ref in record['files']} == expected,
            'result raw file provenance differs')
    if record['outer_ns'] is None:
        require(record['status'] != 'completed', 'completed result has no supervision')
        return
    native = parse_json(read(prefix + 'supervision.json'))
    admit_native(native, cell, runtime, claim, plan_ref, read, refs,
                 completed=record['status'] == 'completed')
    require(all(record[key] == native[key] for key in ('outer_ns', 'exit_code', 'cleanup')) and
            record['captures']['truncated'] == native['truncated'],
            'result supervision provenance differs')
    for name in ('stdout', 'stderr'):
        require(record['captures'][name] == refs.get(prefix + name + '.bin') and
                record['captures'][name] is not None, 'missing original capture provenance')
    if record['status'] == 'completed':
        require(native['cause'] is None and native['secondary'] == [],
                'completed raw supervision contains failure')
        if cell['kind'] != 'session':
            observation = parse_json(read(prefix + 'observations.json'))
            require(observation.get('memory_samples') == [], 'raw worker samples differ')
            observation['memory_samples'] = native['samples']
            require(record['observations'] == observation, 'copied observations differ from raw')
            admit_context_observations(observation, cell, selected)
    else:
        failures = [native['cause']] if native['cause'] else []
        failures.extend(native['secondary'])
        retained = [record['cause'], *record['secondary']]
        require(not failures or retained[:len(failures)] == failures,
                'native failure order lost from result')


def retained_session_reference(cell, runtime, qualified, artifacts, trajectories, read):
    params = cell['parameters']
    ordinal = params['deal'] * 72 + params['seat'] * 12 + params['lineup'] * 2
    ordinal += int(params['strategy'] == 'baseline-rules-v1')
    artifact = artifacts[cell['size']]
    session_name = f"sessions/d{params['deal']}-s{params['seat']}-l{params['lineup']}.json"
    source = read('admission/' + runtime['id'] + '-source.manifest')
    selected = {line[66:]: line for line in source.splitlines(keepends=True)
                if line[66:].startswith(b'src/pontius/') or line[66:].removesuffix(b'\n') in
                (b'tools/v0a_event_adapter.py', b'tools/v0a_hand_adapter.py',
                 b'tools/v0a_rehearsal_driver.py')}
    require(all(name + b'\n' in selected for name in
                (b'tools/v0a_event_adapter.py', b'tools/v0a_hand_adapter.py',
                 b'tools/v0a_rehearsal_driver.py')) and
            any(name.startswith(b'src/pontius/') for name in selected),
            'missing admitted child source subset')
    child_manifest = hashlib.sha256(b''.join(sorted(selected.values()))).hexdigest()
    binding = session_binding(read(session_name), qualified['source_commit'],
        child_manifest, artifact['file']['sha256'], artifact['source_sha256'],
        params['strategy'])
    return dict(trajectory=trajectories[ordinal], binding=binding)


def admit_completed_session(record, cell, reference, keys, read):
    """Reconcile retained original wire values; this does not execute legal replay."""
    prefix = 'cells/' + cell['id'] + '/'
    raw = read(prefix + 'stdout.bin')
    outer, hand, child, identities, binding = _session_envelope(raw, cell, reference)
    require(outer['status'] == 'completed' and outer['completed_hands'] == 1 and
            outer['stop_reason'] is None and outer['failure_reason'] is None and
            not outer['secondary_failures'] and hand['status'] == 'completed' and
            hand['child_exit_code'] == 0 and not hand['capture_truncated'],
            'completed result contradicts original session capture')
    inspected = failed_session_facts(raw, cell, reference)
    require(inspected['complete'] and not inspected['facts'],
            'completed original wire is incomplete or invalid')
    rows = [parse_json(line) for line in child.splitlines(keepends=True)]
    closure = rows[-1]
    require(closure['type'] == 'session_result' and closure['status'] == 'completed' and
            closure['accounting_complete'] and closure['failure_reason'] is None and
            not closure['secondary_failures'] and
            closure['terminal_publication_compute_seconds'] is not None,
            'completed original session closure contains failure')
    decisions = [row['decision'] for row in rows if row['type'] == 'event_result' and
                 row['status'] == 'decided']
    contexts = reference['trajectory']['contexts']
    require(len(decisions) == len(contexts), 'completed context/decision count differs')
    actions = []
    baseline = cell['parameters']['strategy'] == 'baseline-rules-v1'
    for value, context in zip(decisions, contexts):
        timing = value['timing']
        origin = value.get('selection_origin', 'blueprint')
        actions.append(dict(id=f"{cell['id']}-a{value['action_index']}",
            hand_id=value['hand_id'], event_index=value['event_index'],
            action_index=value['action_index'], street=value['street'],
            history_atoms=context['expected']['history_atoms'],
            hit=bytes.fromhex(context['expected']['key_hex']) in keys,
            first=value['action_index'] == 1, elapsed_ns=timing['elapsed_ns'],
            compute_ns=round(timing['response_compute_seconds'] * 1e9),
            uninstrumented_ns=round(timing['response_uninstrumented_seconds'] * 1e9),
            work_cutoff=timing['work_cutoff_crossed'], deadline=timing['deadline_crossed'],
            fallback_used=origin == 'blueprint_fallback' if baseline else True,
            selection_origin=origin))
    totals = [row for row in rows if row['type'] == 'hand_result']
    require(len(totals) == 1 and totals[0]['complete'] and totals[0]['accounting_complete'] and
            totals[0]['failure_reason'] is None and not totals[0]['secondary_failures'] and
            totals[0]['interrupted_response_count'] == 0 and
            totals[0]['settlement'] == hand['settlement'], 'raw settlement provenance differs')
    trajectory = reference['trajectory']
    require([{k: row[k] for k in ('seat', 'street', 'action')}
             for row in hand['applied_actions']] == trajectory['actions'] and
            all(hand['settlement'][key] == trajectory['settlement'][key]
                for key in ('payouts', 'final_stacks', 'pots')) and
            outer['carried_stacks'] == hand['settlement']['final_stacks'] and
            outer['next_button'] == (binding['button'] + 1) % 6,
            'completed reference action/settlement differs')
    preparation = [dict(hand_id=identities[3], **{key: totals[0][key] for key in (
        'preparation_compute_seconds', 'post_terminal_compute_seconds',
        'accounting_complete', 'interrupted_response_count')})]
    events = []
    if cell['parameters']['diagnostic']:
        native = parse_json(read(prefix + 'supervision.json'))
        events = [dict(event, ns=integer(event['ns']) - native['launch_ns'])
                  for event in parse_json(read(prefix + 'profile.json'))]
        session_profile(events, record['outer_ns'], cell['parameters']['strategy'])
    expected = dict(raw_events=events, actions=actions, preparation=preparation,
        session_status='completed', settlement=hand['settlement'], reference_id=trajectory['id'])
    require(record['observations'] == expected,
            'copied session observations differ from original capture')


def admit_retention(read, cells, refs):
    require('retention-final-refusal.json' not in {name.casefold() for name in refs},
            'late retention publication refusal')
    retention = parse_json(read('retention.json'))
    shape(retention, 'version complete failures missing')
    require(retention['version'] == 'workload-r002-retention-v1' and
            type(retention['complete']) is bool and type(retention['failures']) is list and
            type(retention['missing']) is list, 'invalid retention envelope')
    phases = ('admission intent environment execution source capture observation census result '
              'terminal envelope close manifest').split()
    for failure in retention['failures']:
        shape(failure, 'cell_id phase cause exception_type detail')
        require(failure['cell_id'] is None or failure['cell_id'] in cells,
                'unknown retention cell')
        require(failure['phase'] in phases and failure['cause'] in CAUSES and
                type(failure['exception_type']) is str and
                0 < len(failure['exception_type']) <= 128 and type(failure['detail']) is str and
                len(failure['detail']) <= 512, 'invalid retention failure')
    names = retention['missing']
    for name in names:
        file_ref(dict(path=name, bytes=0, sha256='0' * 64))
    require(len(set(names)) == len(names) and not set(names).intersection(refs) and
            (not retention['complete'] or not names), 'retention missing census differs')
    envelope = parse_json(read('run-envelope.json'))
    shape(envelope, 'started_ns finished_ns stop')
    require(integer(envelope['finished_ns']) >= integer(envelope['started_ns']) and
            (envelope['stop'] is None or envelope['stop'] in CAUSES), 'invalid run envelope')
    return retention, envelope


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
        refs = {ref['path']: ref for ref in manifest['files']}
        def read(name):
            require(name in files, 'missing retained provenance: ' + name)
            raw = files[name]
            if raw is None:
                raw = safe_read(root.joinpath(*PurePosixPath(name).parts))
            require(len(raw) == refs[name]['bytes'] and hashlib.sha256(raw).hexdigest() ==
                    refs[name]['sha256'], 'retained provenance changed')
            return raw
        require('plan.json' in files and 'terminal.json' in files, 'missing plan/terminal')
        plan = parse_json(files['plan.json'])
        cells = validate_plan(plan)
        population = parse_json(read('population.json'))
        admit_schedule(plan, population['n_fit'])
        qualified, environments, claims = admit_qualification(plan, population, read, refs)
        retention, envelope = admit_retention(read, cells, refs)
        clocks = {}
        for runtime in plan['runtimes']:
            name = 'admission/' + runtime['id'] + '-runtime-stdout.bin'
            metadata = None
            require(name in files, 'missing runtime qualification probe')
            if name in files:
                # Probe stdout is a raw capture: Windows print supplies CRLF. Its
                # exact bytes were hashed above; remove only that final delimiter.
                probe = parse_json(files[name].removesuffix(b'\r\n'))
                shape(probe, 'version resolved implementation' +
                      (' clocks' if 'clocks' in probe else ''))
                require('clocks' in probe, 'missing runtime clock provenance')
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
        require(set(artifacts) == {0, 128, 1024, 8192, 65536, population['n_fit']},
                'fixed artifact size census differs')
        require([ref['path'] for ref in population['chunks']] ==
                [f'population/table-{i:03d}.jsonl' for i in range(32)] +
                [f'population/query-{i:03d}.jsonl' for i in range(9)],
                'fixed population chunk census differs')
        require([ref['path'] for ref in population['sessions']] ==
                [f'sessions/d{d}-s{s}-l{l}.json' for d in (0, 1)
                 for s in range(6) for l in (0, 1)], 'fixed session input census differs')
        selected, trajectories, membership, traffic = admit_queries(population, read)
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
            require(environment == environments[cell['runtime']],
                    'frozen environment invocation differs')
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
            runtime = next(r for r in plan['runtimes'] if r['id'] == cell['runtime'])
            admit_raw_result(record, cell, read, refs, selected, runtime, claims['run'],
                             refs['plan.json'])
            if cell['kind'] == 'session' and record['status'] == 'completed':
                runtime = next(r for r in plan['runtimes'] if r['id'] == cell['runtime'])
                reference = retained_session_reference(cell, runtime, qualified, artifacts,
                                                       trajectories, read)
                admit_completed_session(record, cell, reference, membership[cell['size']], read)
            if cell['kind'] == 'session' and record['status'] in ('failed', 'interrupted'):
                if record['captures']['stdout'] is not None:
                    runtime = next(r for r in plan['runtimes'] if r['id'] == cell['runtime'])
                    reference = retained_session_reference(cell, runtime, qualified, artifacts,
                                                           trajectories, read)
                    facts = failed_session_facts(read(record['captures']['stdout']['path']), cell,
                        reference, truncated=record['captures']['truncated'])
                    require('failed_session_facts' not in record or
                            record['failed_session_facts'] == facts,
                            'copied failed facts differ from original capture')
                    record = dict(record, failed_session_facts=facts)
                else:
                    require('failed_session_facts' not in record, 'failed facts lack raw capture')
            records.append(record)
        require(terminal_ids == list(cells), 'terminal census/order differs')
        return {'plan': plan, 'population': population, 'records': records,
                'artifact_summaries': artifact_summaries, 'runtime_clocks': clocks,
                'query_traffic': traffic, 'retention': retention, 'run_envelope': envelope,
                'summary': summarize(records, plan, retention, envelope)}
    except (OSError, KeyError, TypeError) as exc:
        raise ReportError('missing or malformed retained run: ' + str(exc)) from exc
