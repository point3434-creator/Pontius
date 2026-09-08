"""Direct r002 costs over frozen legal witnesses; controller owns invocation and memory."""
from __future__ import annotations

import gc
from hashlib import sha256
from pathlib import Path
import re
import sys
import time
import tracemalloc

from pontius.blueprint_artifact.codec import decode_blueprint
from pontius.blueprint_preparation.lookup import PreparedBlueprintProvider
from pontius.decision_provider.providers import BlueprintProvider
from pontius.immutable_blueprint import BlueprintDecisionKey

OPERATIONS = ('key', 'hash', 'lookup', 'identity', 'provider')
BYTE_FIELDS = ('wire_bytes', 'key_bytes', 'canonical_bytes')
FILE_LIMIT = 128 * 1024 * 1024


class Refusal(ValueError):
    def __init__(self, code='input_invalid'):
        super().__init__(code)
        self.code = code


def require(condition, code='input_invalid'):
    if not condition:
        raise Refusal(code)


def normal_runtime():
    require(gc.isenabled() and not tracemalloc.is_tracing()
            and sys.getprofile() is None and sys.gettrace() is None, 'profile_invalid')


def checked_inputs(inputs):
    require(type(inputs) is dict and set(inputs) == {
        'artifact_path', 'artifact_metadata', 'selections', 'population', 'clock', 'stage'})
    require(callable(inputs['clock']) and callable(inputs['stage'])
            and callable(inputs['population'].replay_context))
    metadata = inputs['artifact_metadata']
    require(type(metadata) is dict)
    for name in (*BYTE_FIELDS, 'size'):
        require(type(metadata.get(name)) is int and metadata[name] >= 0)
    require(metadata['wire_bytes'] <= FILE_LIMIT, 'capture_limit')
    require(type(metadata.get('source_sha256')) is str and
            re.fullmatch('[0-9a-f]{64}', metadata['source_sha256']) is not None)
    require(type(metadata.get('file')) is dict and
            type(metadata['file'].get('sha256')) is str and
            re.fullmatch('[0-9a-f]{64}', metadata['file']['sha256']) is not None)
    require(type(inputs['selections']) is dict)
    require(Path(inputs['artifact_path']).is_absolute())
    return metadata


def tick(clock):
    value = clock()
    require(type(value) is int and value >= 0, 'profile_invalid')
    return value


def elapsed(clock, start):
    value = tick(clock) - start
    require(value >= 0, 'profile_invalid')
    return value


def timed(clock, function):
    start = tick(clock)
    result = function()
    return result, elapsed(clock, start)


def read_artifact(inputs):
    with Path(inputs['artifact_path']).open('rb') as stream:
        raw = stream.read(FILE_LIMIT + 1)
    require(len(raw) <= FILE_LIMIT, 'capture_limit')
    return raw


def decode_artifact(raw, metadata):
    require(len(raw) == metadata['wire_bytes'])
    try:
        source = decode_blueprint(raw)
    except ValueError as error:
        raise Refusal('input_invalid') from error
    require(len(source.entries) == metadata['size'] and source.digest == metadata['source_sha256'])
    return source


def byte_metadata(metadata):
    return dict(memory_samples=[], source_sha256=metadata['source_sha256'],
                **{name: metadata[name] for name in BYTE_FIELDS})


def key_for(observation):
    return BlueprintDecisionKey.from_state(cards=observation.cards, betting=observation.betting,
                                           decision=observation.decision)


def action_value(action):
    return (action.kind.value, action.raise_to)


def proposal_value(proposal):
    return (proposal.decision_sha256, action_value(proposal.action), proposal.reason)


def prepare_queries(records, source, population, hit=None):
    """Independent legacy/frozen expectations and fresh equal-valued keys, outside timing."""
    require(type(records) is list)
    legacy, queries = BlueprintProvider(source), []
    for record in records:
        observation = population.replay_context(record)
        key = key_for(observation)
        expected = record['expected']
        selection = source.action_for(cards=observation.cards, betting=observation.betting,
                                      decision=observation.decision)
        proposal = legacy.propose(observation)
        passive = expected['passive_action']
        require(key.canonical_bytes().hex() == expected['key_hex'] and
                key.digest == expected['key_sha256'] and
                observation.decision_sha256 == expected['decision_sha256'] and
                selection.key == key and selection.source_digest == source.digest and
                (hit is None or selection.table_hit is hit) and
                action_value(selection.action) == (passive['kind'], passive['raise_to']) and
                proposal_value(proposal) == (expected['decision_sha256'],
                    (passive['kind'], passive['raise_to']),
                    'blueprint_hit' if selection.table_hit else 'blueprint_default'),
                'parity_failed')
        queries.append(dict(record=record, observation=observation, key=key,
            hash=hash(key), hit=selection.table_hit, action=action_value(selection.action),
            proposal=proposal_value(proposal)))
    return queries


def operation(name, query, provider):
    if name == 'key':
        return key_for(query['observation'])
    if name == 'hash':
        return hash(query['key'])
    if name == 'lookup':
        return provider._blueprint._actions.get(query['key'])
    if name == 'identity':
        return query['observation'].decision_sha256
    if name == 'provider':
        return provider.propose(query['observation'])
    raise Refusal()


def validate_result(name, result, query):
    try:
        if name == 'key':
            valid = (type(result) is BlueprintDecisionKey and
                     result.canonical_bytes().hex() == query['record']['expected']['key_hex'])
        elif name == 'hash':
            valid = type(result) is int and result == query['hash']
        elif name == 'lookup':
            valid = (action_value(result) == query['action'] if query['hit'] else result is None)
        elif name == 'identity':
            valid = type(result) is str and result == query['record']['expected']['decision_sha256']
        elif name == 'provider':
            valid = proposal_value(result) == query['proposal']
        else:
            valid = False
        require(valid, 'parity_failed')
    except (AttributeError, TypeError, ValueError) as error:
        if isinstance(error, Refusal):
            raise
        raise Refusal('parity_failed') from error


def construction_observation(inputs):
    normal_runtime()
    metadata = checked_inputs(inputs)
    observation = inputs['population'].replay_context(inputs['selections']['first_context'])
    clock = inputs['clock']
    outer = tick(clock)
    raw, read_ns = timed(clock, lambda: read_artifact(inputs))
    source, decode_ns = timed(clock, lambda: decode_artifact(raw, metadata))
    provider, prepare_ns = timed(clock, lambda: PreparedBlueprintProvider(source))
    proposal, first_ns = timed(clock, lambda: provider.propose(observation))
    outer_ns = elapsed(clock, outer)
    canonical, canonical_ns = timed(clock, source.canonical_bytes)
    digest, sha_ns = timed(clock, lambda: sha256(canonical).hexdigest())
    query = prepare_queries([inputs['selections']['first_context']],
                            source, inputs['population'])[0]
    validate_result('provider', proposal, query)
    require(digest == metadata['source_sha256'] and len(canonical) == metadata['canonical_bytes']
            and sum(len(e.key.canonical_bytes()) for e in source.entries) == metadata['key_bytes'],
            'parity_failed')
    return dict(**byte_metadata(metadata), read_ns=read_ns, decode_ns=decode_ns,
                prepare_ns=prepare_ns, first_ns=first_ns, outer_total_ns=outer_ns,
                canonical_ns=canonical_ns, sha_ns=sha_ns)


def memory_observation(inputs, *, traced):
    normal_runtime()
    metadata = checked_inputs(inputs)
    record = inputs['selections']['first_context']
    observation = inputs['population'].replay_context(record)
    stage = inputs['stage']
    if not traced:
        stage('idle')
    raw = read_artifact(inputs)
    if not traced:
        stage('read')
    # Raw bytes and first observation are owned before incremental tracing begins.
    if traced:
        tracemalloc.start()
    try:
        source = decode_artifact(raw, metadata)
        if not traced:
            stage('decode')
        provider = PreparedBlueprintProvider(source)
        if not traced:
            stage('prepare')
        if traced:
            retained, peak = tracemalloc.get_traced_memory()
        else:
            proposal = provider.propose(observation)
            stage('first')
            stage('final')
    finally:
        if traced:
            tracemalloc.stop()
    if traced:
        # Sample the still-owned graph after excluding handshake allocations from tracing.
        stage('final')
    # Keep all owned inputs and the result through final stage, then validate.
    query = prepare_queries([record], source, inputs['population'])[0]
    if not traced:
        validate_result('provider', proposal, query)
    require(provider._blueprint.digest == metadata['source_sha256'], 'parity_failed')
    result = dict(**byte_metadata(metadata), excluded_raw_bytes=len(raw),
                  excluded_observation=record['id'])
    if traced:
        result.update(retained_bytes=retained, peak_bytes=peak)
    return result


def verify_cached(provider, expected_digest, clock):
    """Hash owned bytes against independently frozen source identity before every hand."""
    digest, duration = timed(clock,
                             lambda: sha256(provider._blueprint.canonical_bytes()).hexdigest())
    require(digest == expected_digest, 'parity_failed')
    return duration


def reuse_group(source, sequences, population, arm, expected_digest, clock):
    normal_runtime()
    require(arm in ('fresh', 'retained') and type(sequences) is list and len(sequences) > 0)
    # Replay only; independent legacy validation happens after the entire measured group.
    observations = [[population.replay_context(record) for record in hand] for hand in sequences]
    preparations, hashes, retained = [], [], []
    outer = tick(clock)
    provider = None
    for hand in observations:
        if arm == 'fresh' or provider is None:
            provider, duration = timed(clock, lambda: PreparedBlueprintProvider(source))
            preparations.append(duration)
        if arm == 'retained':
            hashes.append(verify_cached(provider, expected_digest, clock))
        retained.append([provider.propose(observation) for observation in hand])
    total = elapsed(clock, outer)
    require(provider._blueprint.digest == expected_digest, 'parity_failed')
    records = [record for hand in sequences for record in hand]
    queries = prepare_queries(records, source, population)
    for proposal, query in zip((p for hand in retained for p in hand), queries):
        validate_result('provider', proposal, query)
    return dict(group_ns=total, prepare_ns=preparations, hash_ns=hashes,
                query_count=len(records), distinct_keys=len({q['key'] for q in queries}),
                context_ids=[record['id'] for record in records])


def operation_phase(name, queries, provider, clock, *, count, batch_calls,
                    individual=False, offset=0):
    """Retain a complete measured phase before validation, with an explicit finite seam."""
    require(name in OPERATIONS and len(queries) > 0)
    retained, samples = [], []
    width = 1 if individual else batch_calls
    for _ in range(count):
        selected = [queries[(offset + i) % len(queries)] for i in range(width)]
        start = tick(clock)
        if individual:
            value = operation(name, selected[0], provider)
        else:
            values = [operation(name, query, provider) for query in selected]
        samples.append(elapsed(clock, start))
        if individual:
            values = [value]
        retained.append((selected, values))
        offset += width
    for selected, values in retained:
        for query, result in zip(selected, values):
            validate_result(name, result, query)
    return samples, offset


def clock_controls(clock, *, brackets=10000, batches=5, calls=100):
    info = time.get_clock_info('perf_counter')
    bracket_samples, empty, loops = [], [], []
    def empty_call():
        return None
    for _ in range(brackets):
        start = tick(clock)
        bracket_samples.append(elapsed(clock, start))
    for _ in range(batches):
        start = tick(clock)
        for _ in range(calls):
            empty_call()
        empty.append(elapsed(clock, start))
    for _ in range(batches):
        start = tick(clock)
        values = [empty_call() for _ in range(calls)]
        loops.append(elapsed(clock, start))
        require(len(values) == calls, 'parity_failed')
    return dict(clock=dict(implementation=info.implementation, monotonic=info.monotonic,
                adjustable=info.adjustable, resolution=info.resolution),
                empty_brackets_ns=bracket_samples, empty_batches_ns=empty, loop_batches_ns=loops)


def history_block(name, queries, provider, clock, offsets, *, warmups=10, batches=10,
                  batch_calls=100, individual_calls=1000):
    """One ABBA block; reduced counts are internal finite correctness controls only."""
    block = {label: dict(context_ids=[q['record']['id'] for q in queries[label]],
                        batch_ns=[], individual_ns=[]) for label in ('hit', 'miss')}
    offsets = dict(offsets)
    for label in ('hit', 'miss', 'miss', 'hit'):
        if not queries[label]:
            continue
        warm = [queries[label][(offsets[label] + i) % len(queries[label])] for i in range(warmups)]
        values = [operation(name, query, provider) for query in warm]
        for query, result in zip(warm, values):
            validate_result(name, result, query)
        offsets[label] += warmups
        for field, count, individual in [('batch_ns', batches, False),
                                         ('individual_ns', individual_calls, True)]:
            samples, offsets[label] = operation_phase(name, queries[label], provider, clock,
                count=count, batch_calls=batch_calls, individual=individual, offset=offsets[label])
            block[label][field].extend(samples)
    return block, offsets


def history_blocks(source, selected, population, operation_name, clock):
    provider = PreparedBlueprintProvider(source)
    queries = {label: prepare_queries(selected[label], source, population, label == 'hit')
               for label in ('hit', 'miss')}
    offsets, blocks = dict(hit=0, miss=0), []
    for _ in range(5):
        block, offsets = history_block(operation_name, queries, provider, clock, offsets)
        blocks.append(block)
    return blocks


def comparison_blocks(source, selected, population, clock, *, blocks=5, warmups=20,
                      calls_per_class):
    providers = dict(legacy=BlueprintProvider(source), prepared=PreparedBlueprintProvider(source))
    # Frozen expectations are independent of either timed provider result.
    queries = {label: prepare_queries(selected[label], source, population, label == 'hit')
               for label in ('hit', 'miss')}
    result = []
    for index in range(blocks):
        order = ('legacy', 'prepared') if index % 2 == 0 else ('prepared', 'legacy')
        for name in order:
            for i in range(warmups):
                label = ('hit', 'miss')[i % 2]
                if queries[label]:
                    query = queries[label][(i // 2) % len(queries[label])]
                    proposal = providers[name].propose(population.replay_context(query['record']))
                    validate_result('provider', proposal, query)
        block = {name: {label: dict(context_ids=[], call_ns=[]) for label in ('hit', 'miss')}
                 for name in providers}
        retained = []
        for i in range(calls_per_class):
            for label in ('hit', 'miss'):
                if not queries[label]:
                    continue
                query = queries[label][(index * calls_per_class + i) % len(queries[label])]
                for name in order:
                    observation = population.replay_context(query['record'])
                    proposal, duration = timed(clock, lambda: providers[name].propose(observation))
                    block[name][label]['context_ids'].append(query['record']['id'])
                    block[name][label]['call_ns'].append(duration)
                    retained.append((proposal, query))
        for proposal, query in retained:
            validate_result('provider', proposal, query)
        result.append(block)
    return result


def measure_cell(cell, inputs):
    """Fixed worker dispatch; never receives an arbitrary count/operation schedule."""
    normal_runtime()
    metadata = checked_inputs(inputs)
    require(type(cell) is dict and
            set(cell) == {'id', 'runtime', 'kind', 'size', 'parameters', 'argv'})
    require(type(cell['id']) is str and len(cell['id']) > 0 and type(cell['runtime']) is str
            and cell['runtime'] in ('3.11', '3.14') and type(cell['kind']) is str
            and type(cell['argv']) is list and all(type(v) is str for v in cell['argv']))
    require(type(cell['size']) is int and cell['size'] == metadata['size'])
    kind, parameters = cell['kind'], cell['parameters']
    require(type(parameters) is dict)
    if kind in ('construction', 'memory_traced', 'memory_untraced'):
        require(set(parameters) == {'observation'} and type(parameters['observation']) is int
                and 0 <= parameters['observation'] < 5)
        return (construction_observation(inputs) if kind == 'construction' else
                memory_observation(inputs, traced=kind == 'memory_traced'))
    population, selected, clock = inputs['population'], inputs['selections'], inputs['clock']
    raw, read_ns = timed(clock, lambda: read_artifact(inputs))
    source, decode_ns = timed(clock, lambda: decode_artifact(raw, metadata))
    if kind == 'history':
        required = dict(blocks=5, subblocks=['hit', 'miss', 'miss', 'hit'], warmups=10,
                        batches=10, batch_calls=100, individual_calls=1000,
                        empty_brackets=10000, empty_batches=5, loop_batches=5)
        require(set(parameters) == {*required, 'bin', 'operation'} and
                all(type(parameters[k]) is type(v) and parameters[k] == v
                    for k, v in required.items())
                and parameters['operation'] in OPERATIONS and parameters['bin'] in population.BINS)
        result = clock_controls(clock)
        result['blocks'] = history_blocks(source, selected['history'][parameters['bin']],
                                         population, parameters['operation'], clock)
    elif kind == 'reuse':
        require(set(parameters) == {'hands', 'repetition', 'arm', 'trajectory_ordinals'} and
                type(parameters['hands']) is int and parameters['hands'] in (1, 2, 8, 32)
                and type(parameters['repetition']) is int and 0 <= parameters['repetition'] < 4
                and parameters['arm'] in ('fresh', 'retained') and
                type(parameters['trajectory_ordinals']) is list and
                all(type(v) is int for v in parameters['trajectory_ordinals']) and
                parameters['trajectory_ordinals'] ==
                population.reuse_ordinals()[:parameters['hands']])
        sequences = selected['reuse'][:parameters['hands']]
        require(len(selected['reuse']) == 32 and len(sequences) == parameters['hands'])
        result = reuse_group(source, sequences, population, parameters['arm'],
                             metadata['source_sha256'], clock)
        result.update(read_ns=read_ns, decode_ns=decode_ns)
    elif kind == 'comparison':
        required = dict(blocks=5, warmups=20,
                        calls_per_class={1024: 20, 8192: 10, 65536: 2}.get(cell['size']),
                        provider_order=['legacy', 'prepared'], alternate_provider_first=True,
                        continuous_cycle=True)
        require(required['calls_per_class'] is not None and set(parameters) == set(required)
                and all(type(parameters[k]) is type(v) and parameters[k] == v
                        for k, v in required.items()))
        result = dict(blocks=comparison_blocks(source, selected['comparisons'][str(cell['size'])],
                      population, clock, calls_per_class=parameters['calls_per_class']))
    else:
        raise Refusal()
    return dict(memory_samples=[], **result)
