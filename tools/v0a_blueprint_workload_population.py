"""Fixed r002 offline population and frozen schedule; invocation authority is external."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PureWindowsPath
import re
import sys
from types import ModuleType, SimpleNamespace

import pontius.no_limit_betting as betting
import pontius.holdem_cards as cards
from pontius.immutable_blueprint import (
    BlueprintActionEntry, BlueprintDecisionKey, ImmutableBlueprintActionSource,
    passive_blueprint_action,
)
from pontius.blueprint_artifact.codec import encode_blueprint
import pontius.decision_provider.model as model
from pontius.decision_provider.providers import make_provider

SOURCE_ID = 'workload-r002-passive'
STREETS = ('preflop', 'flop', 'turn', 'river')
BINS = ('0', '3-5', '7-9', '15-17', '31-33')
STACKS = ((200,) * 6, (40, 80, 120, 160, 200, 240))
STRATEGIES = ('blueprint-v1', 'baseline-rules-v1')
RECIPE = {'version': 'workload-r002-recipe-v1'}
FILE_LIMIT = 128 * 1024 * 1024
FACTORS = {'corpus', 'ordinal', 'deal_ordinal', 'button', 'controlled_seat',
           'stack_profile', 'lineup', 'strategy'}
EXPECTED = {'actor', 'street', 'history_atoms', 'key_hex', 'key_sha256',
            'decision_sha256', 'passive_action'}


class Refusal(ValueError):
    def __init__(self, code='input_invalid'):
        super().__init__(code)
        self.code = code


def require(condition, code='input_invalid'):
    if not condition:
        raise Refusal(code)


def exact(value, names):
    require(type(value) is dict and set(value) == set(names))


def integer(value, lower, upper):
    require(type(value) is int and lower <= value <= upper)


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)
            + '\n').encode('ascii')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _load_dealer():
    path = Path(__file__).resolve().parent / 'v0a_seeded_deals.py'
    raw = path.read_bytes()
    require(hashlib.sha1(b'blob ' + str(len(raw)).encode('ascii') + b'\0' + raw).hexdigest()
            == '2963004e38c6e66f76ae9ce3bd474063eee870fe', 'source_invalid')
    module = ModuleType('workload_captured_dealer')
    module.__file__ = str(path)
    sys.modules[module.__name__] = module
    exec(compile(raw, str(path), 'exec'), module.__dict__)
    return module


def _load_host():
    path = Path(__file__).resolve().parent / 'v0a_table_host.py'
    raw = path.read_bytes()
    require(hashlib.sha1(b'blob ' + str(len(raw)).encode('ascii') + b'\0' + raw).hexdigest()
            == '7beb178989b3ff98b684093ce4022667a1c61ece', 'source_invalid')
    module = ModuleType('workload_captured_host')
    module.__file__ = str(path)
    sys.modules[module.__name__] = module
    exec(compile(raw, str(path), 'exec'), module.__dict__)
    return module


def factors(corpus, ordinal):
    require(type(corpus) is str and corpus in ('table', 'query'))
    integer(ordinal, 0, 8191 if corpus == 'table' else 1151)
    if corpus == 'table':
        return dict(corpus=corpus, ordinal=ordinal, deal_ordinal=ordinal,
                    button=ordinal % 6, controlled_seat=None,
                    stack_profile=ordinal // 6 % 2, lineup=ordinal // 12 % 2,
                    strategy=None)
    deal, rest = divmod(ordinal, 72)
    seat, rest = divmod(rest, 12)
    stack, rest = divmod(rest, 6)
    lineup, strategy = divmod(rest, 2)
    return dict(corpus=corpus, ordinal=ordinal, deal_ordinal=deal, button=0,
                controlled_seat=seat, stack_profile=stack, lineup=lineup,
                strategy=STRATEGIES[strategy])


def _factors(value):
    exact(value, FACTORS)
    expected = factors(value['corpus'], value['ordinal'])
    require(all(type(value[k]) is type(v) and value[k] == v for k, v in expected.items()))


def seed_for(corpus, ordinal):
    require(type(corpus) is str and corpus in ('table', 'query'))
    integer(ordinal, 0, 8191 if corpus == 'table' else 15)
    return sha(f'pontius-v0a-workload-r002/{corpus}/{ordinal:08d}'.encode('ascii'))


def history_bin(atoms):
    integer(atoms, 0, 256)
    for name, lower, upper in (('0', 0, 0), ('3-5', 3, 5), ('7-9', 7, 9),
                                ('15-17', 15, 17), ('31-33', 31, 33)):
        if lower <= atoms <= upper:
            return name
    return 'other'


def _deal(value):
    exact(value, ('private_hands', 'board_runout'))
    require(type(value['private_hands']) is list and len(value['private_hands']) == 6)
    require(type(value['board_runout']) is list and len(value['board_runout']) == 5)
    for group in [*value['private_hands'], value['board_runout']]:
        require(type(group) is list and len(group) == (5 if group is value['board_runout'] else 2))
        for card in group:
            integer(card, 0, 51)
    return cards.SixSeatHoldemDeal(tuple(tuple(h) for h in value['private_hands']),
                                    tuple(value['board_runout']))


def _state(factor):
    return betting.NoLimitBettingState.new_hand(button=factor['button'],
        starting_stacks=STACKS[factor['stack_profile']], small_blind=1, big_blind=2)


def _advance(state):
    while state.round_complete and not state.is_terminal:
        state = state.advance_street()
    return state


def _action(value):
    exact(value, ('kind', 'raise_to'))
    require(type(value['kind']) is str and value['kind'] in ('fold', 'check', 'call', 'raise'))
    if value['kind'] == 'raise':
        integer(value['raise_to'], 1, 1040)
    else:
        require(value['raise_to'] is None)
    return betting.BettingAction(betting.BettingActionKind(value['kind']), value['raise_to'])


def action_payload(action):
    return {'kind': action.kind.value, 'raise_to': action.raise_to}


def context_key(observation):
    return BlueprintDecisionKey.from_state(cards=observation.cards, betting=observation.betting,
                                           decision=observation.decision)


def _observation(state, deal, trajectory_id, action_index):
    view = cards.OneSeatCardState(state.acting_seat, deal.hand(state.acting_seat),
                                 state.street, deal.public_cards(state.street))
    return model.DecisionObservation('pontius-decision-observation-v1', trajectory_id,
                                    action_index, view, state, state.legal_decision(),
                                    14_000_000_000)


def _expected(observation):
    key = context_key(observation)
    return dict(actor=observation.cards.controlled_seat, street=observation.betting.street.value,
                history_atoms=len(observation.betting.history), key_hex=key.canonical_bytes().hex(),
                key_sha256=key.digest, decision_sha256=observation.decision_sha256,
                passive_action=action_payload(passive_blueprint_action(observation.decision)))


def replay_context(record):
    """Reconstruct a fresh one-seat observation by legal replay of a closed witness."""
    try:
        exact(record, ('version', 'id', 'trajectory_id', 'factors', 'deal', 'prefix', 'expected'))
        require(record['version'] == 'workload-r002-context-v1')
        factor = record['factors']
        _factors(factor)
        trajectory_id = f"r002-{factor['corpus']}-{factor['ordinal']:04d}"
        require(type(record['trajectory_id']) is str and record['trajectory_id'] == trajectory_id)
        require(type(record['prefix']) is list and len(record['prefix']) < 256)
        require(type(record['id']) is str and
                record['id'] == f"{trajectory_id}-{len(record['prefix']):03d}")
        exact(record['expected'], EXPECTED)
        for name in ('actor', 'history_atoms'):
            integer(record['expected'][name], 0, 255 if name == 'history_atoms' else 5)
        for name in ('key_hex', 'key_sha256', 'decision_sha256', 'street'):
            require(type(record['expected'][name]) is str)
        _action(record['expected']['passive_action'])
        deal, state, index = _deal(record['deal']), _state(factor), 1
        for row in record['prefix']:
            exact(row, ('seat', 'street', 'action'))
            integer(row['seat'], 0, 5)
            state = _advance(state)
            require(not state.is_terminal and row['seat'] == state.acting_seat and
                    type(row['street']) is str and row['street'] == state.street.value)
            if factor['corpus'] == 'table' or state.acting_seat == factor['controlled_seat']:
                index += 1
            state = state.apply_action(_action(row['action']))
        state = _advance(state)
        require(not state.is_terminal)
        require(factor['corpus'] == 'table' or state.acting_seat == factor['controlled_seat'])
        observation = _observation(state, deal, trajectory_id, index)
        require(_expected(observation) == record['expected'], 'parity_failed')
        return observation
    except (KeyError, TypeError, ValueError, RecursionError) as error:
        if isinstance(error, Refusal):
            raise
        raise Refusal('input_invalid') from error


def opponents(factor):
    if factor['corpus'] == 'table':
        return [('passive', 'min_raise_once')[factor['lineup']]] * 6
    seat, lineup = factor['controlled_seat'], factor['lineup']
    result = ['passive' if lineup == 0 else 'min_raise_once'] * 6
    if lineup == 1:
        for offset, policy in enumerate(
                ('min_raise_once', 'passive', 'fold_to_bet', 'shove_once', 'passive'), 1):
            result[(seat + offset) % 6] = policy
    result[seat] = None
    return result


def trajectory(factor, *, seed=None, max_actions=256, capture=None):
    """Driver alone owns the complete deal; policies receive only actor-visible state."""
    _factors(factor)
    integer(max_actions, 1, 256)
    seed = seed_for(factor['corpus'], factor['deal_ordinal']) if seed is None else seed
    require(type(seed) is str and re.fullmatch('[0-9a-f]{64}', seed) is not None)
    raw_deal = _load_dealer().deal_for_hand(seed, 0)
    deal, state = _deal(raw_deal), _state(factor)
    host, modules = _load_host(), SimpleNamespace(model=model)
    policies = opponents(factor)
    provider = (None if factor['corpus'] == 'table' else
                make_provider(factor['strategy'], ImmutableBlueprintActionSource(SOURCE_ID)))
    name = f"r002-{factor['corpus']}-{factor['ordinal']:04d}"
    contexts, actions = [], []
    while True:
        state = _advance(state)
        if state.is_terminal:
            break
        require(len(actions) < max_actions, 'coverage_missing')
        controlled = provider is not None and state.acting_seat == factor['controlled_seat']
        observation = _observation(state, deal, name, len(contexts) + 1)
        if provider is None or controlled:
            contexts.append(dict(version='workload-r002-context-v1',
                id=f'{name}-{len(actions):03d}', trajectory_id=name, factors=dict(factor),
                deal=raw_deal, prefix=list(actions), expected=_expected(observation)))
            if capture is not None:
                capture(contexts[-1], observation)
        action = (provider.propose(observation).action if controlled else
                  host.select_opponent(policies[state.acting_seat], observation.cards, state,
                                       observation.decision, modules).to_betting_action())
        actions.append(dict(seat=state.acting_seat, street=state.street.value,
                            action=action_payload(action)))
        state = state.apply_action(action)
    strengths = deal.showdown_strengths(state.live_seats) if state.showdown_ready else None
    settlement = state.settle(strengths)
    return dict(version='workload-r002-trajectory-v1', id=name, factors=dict(factor), seed=seed,
                deal=raw_deal, contexts=contexts, actions=actions,
                settlement=dict(reason=settlement.reason.value, payouts=list(settlement.payouts),
                    final_stacks=list(settlement.final_stacks),
                    pots=[dict(amount=p.amount, seats=list(p.eligible_seats))
                          for p in settlement.side_pots]))


def interleave(streams):
    streets, seen = {street: [] for street in STREETS}, set()
    for stream in streams:
        for context in stream:
            key = context['expected']['key_hex']
            if key not in seen:
                seen.add(key)
                streets[context['expected']['street']].append(context)
    result = []
    for index in range(max(map(len, streets.values()), default=0)):
        for street in STREETS:
            if index < len(streets[street]):
                result.append(streets[street][index])
    return result


def _entry(record):
    observation = replay_context(record)
    return BlueprintActionEntry(context_key(observation),
                                passive_blueprint_action(observation.decision))


def prefix_capacity(row_lengths, root_bytes, limit):
    integer(root_bytes, 1, FILE_LIMIT)
    integer(limit, root_bytes, FILE_LIMIT)
    length, count = root_bytes, 0
    for row in row_lengths:
        integer(row, 1, FILE_LIMIT)
        extra = row + (1 if count else 0)
        if length + extra > limit:
            break
        length += extra
        count += 1
    return count


def _artifact_rows(rows):
    root_bytes = len(encode_blueprint(ImmutableBlueprintActionSource(SOURCE_ID)))
    lengths = [row[2] for row in rows]
    require(root_bytes + sum(lengths) + max(0, len(rows) - 1) <= FILE_LIMIT, 'capture_limit')
    entries = tuple(row[0] for row in rows)
    source = ImmutableBlueprintActionSource(SOURCE_ID, entries)
    raw = encode_blueprint(source)
    require(len(raw) <= FILE_LIMIT, 'capture_limit')
    census = {street: {name: [] for name in (*BINS, 'other')} for street in STREETS}
    for (_, member, length) in rows:
        expected = member['expected']
        census[expected['street']][history_bin(expected['history_atoms'])].append(length)
    metadata = dict(size=len(entries), source_sha256=source.digest,
                    canonical_bytes=len(source.canonical_bytes()),
                    key_bytes=sum(len(entry.key.canonical_bytes()) for entry in entries),
                    wire_bytes=len(raw), root_bytes=root_bytes, row_bytes=sum(lengths),
                    comma_bytes=max(0, len(entries) - 1), row_census=census)
    require(root_bytes + sum(lengths) + metadata['comma_bytes'] == len(raw), 'parity_failed')
    return raw, metadata


def _row(record, entry):
    root_bytes = len(encode_blueprint(ImmutableBlueprintActionSource(SOURCE_ID)))
    length = len(encode_blueprint(ImmutableBlueprintActionSource(SOURCE_ID, (entry,)))) - root_bytes
    witness = dict(record, expected={k: v for k, v in record['expected'].items() if k != 'key_hex'})
    return entry, witness, length


def member_context(row):
    entry, witness, _ = row
    return dict(witness, expected=dict(witness['expected'],
                                      key_hex=entry.key.canonical_bytes().hex()))


class TableMembers:
    """Bound retained membership to the largest requested equal-street prefix."""
    def __init__(self, per_street=16384):
        integer(per_street, 1, 16384)
        self.limit = per_street
        self.streets = {street: [] for street in STREETS}
        self.seen = {street: set() for street in STREETS}

    def add(self, record, observation):
        street = record['expected']['street']
        if len(self.streets[street]) == self.limit:
            return
        key = context_key(observation)
        token = key.canonical_bytes()
        if token in self.seen[street]:
            return
        self.seen[street].add(token)
        entry = BlueprintActionEntry(key, passive_blueprint_action(observation.decision))
        self.streets[street].append(_row(record, entry))

    def ordered(self):
        return [self.streets[street][i] for i in range(self.limit) for street in STREETS
                if i < len(self.streets[street])]


def artifact(members):
    return _artifact_rows([_row(record, _entry(record)) for record in members])


def capacity(members, limit=1048576):
    return _capacity_rows([_row(record, _entry(record)) for record in members], limit)


def _capacity_rows(rows, limit=1048576):
    root_bytes = len(encode_blueprint(ImmutableBlueprintActionSource(SOURCE_ID)))
    count = prefix_capacity([row[2] for row in rows], root_bytes, limit)
    require(count < len(rows), 'coverage_missing')
    current, following = _artifact_rows(rows[:count]), _artifact_rows(rows[:count + 1])
    require(len(current[0]) <= limit < len(following[0]), 'parity_failed')
    return dict(n_fit=count, fit=current[1], next=following[1])


def qualify_coverage(table, query):
    table_contexts = [r for t in table for r in t['contexts']]
    queries = [r for t in query for r in t['contexts']]
    require({r['expected']['street'] for r in table_contexts} == set(STREETS)
            and {r['expected']['street'] for r in queries} == set(STREETS)
            and {t['factors']['controlled_seat'] for t in query} == set(range(6))
            and {t['factors']['stack_profile'] for t in table} == {0, 1}
            and {t['factors']['lineup'] for t in table} == {0, 1}
            and {history_bin(r['expected']['history_atoms']) for r in queries} >= set(BINS),
            'coverage_missing')
    members = interleave([t['contexts'] for t in table])
    require(len(members) >= 65536 and all(sum(r['expected']['street'] == street
            for r in members[:65536]) == 16384 for street in STREETS), 'coverage_missing')
    return dict(streets=list(STREETS), seats=list(range(6)), stacks=[0, 1], rules=[0, 1],
                bins=list(BINS), unique_entries=len(members))


def reuse_ordinals():
    return [d * 72 + seat * 12 + (d % 3) * 2 + d % 2
            for d in range(16) for seat in (d % 6, (d + 3) % 6)]


def _first(records, predicate, limit=100):
    result, seen = [], set()
    for record in records:
        key = record['expected']['key_hex']
        if key not in seen and predicate(record):
            seen.add(key)
            result.append(record)
            if len(result) == limit:
                break
    return result


def select_contexts(members, queries):
    keys = {r['expected']['key_hex'] for r in members}
    traffic = [r for t in queries for r in t['contexts']]
    history = {name: dict(hit=_first(members, lambda r: history_bin(
        r['expected']['history_atoms']) == name), miss=_first(traffic, lambda r:
        r['expected']['key_hex'] not in keys
        and history_bin(r['expected']['history_atoms']) == name))
        for name in BINS}
    natural = [dict(id=r['id'], trajectory_id=r['trajectory_id'],
                    hit=r['expected']['key_hex'] in keys, street=r['expected']['street'],
                    history_atoms=r['expected']['history_atoms']) for r in traffic]
    return dict(history=history, natural=natural,
                comparison=dict(hit=_first(members, lambda r: True),
                                miss=_first(traffic,
                                            lambda r: r['expected']['key_hex'] not in keys)))


def _select_rows(rows, queries):
    keys = {entry.key.canonical_bytes() for entry, _, _ in rows}
    traffic = [r for t in queries for r in t['contexts']]
    misses = [r for r in traffic if bytes.fromhex(r['expected']['key_hex']) not in keys]
    history = {}
    for name in BINS:
        hits = [row for row in rows
                if history_bin(row[1]['expected']['history_atoms']) == name][:100]
        history[name] = dict(hit=[member_context(row) for row in hits], miss=_first(misses,
                            lambda r: history_bin(r['expected']['history_atoms']) == name))
    natural = [dict(id=r['id'], trajectory_id=r['trajectory_id'],
                    hit=bytes.fromhex(r['expected']['key_hex']) in keys,
                    street=r['expected']['street'], history_atoms=r['expected']['history_atoms'])
               for r in traffic]
    return dict(history=history, natural=natural,
                comparison=dict(hit=[member_context(row) for row in rows[:100]],
                                miss=_first(misses, lambda r: True)))


def build_population(recipe, sink):
    """Execute only after separate invocation admission; write fixed bounded chunks."""
    require(type(recipe) is dict and recipe == RECIPE
            and all(type(v) is str for v in recipe.values()))
    chunks, query, collector = [], [], TableMembers()
    observed_stacks, observed_rules, table_streets = set(), set(), set()

    def publish(path, raw):
        require(type(raw) is bytes and len(raw) <= FILE_LIMIT, 'capture_limit')
        sink(path, raw)
        return dict(path=path, sha256=sha(raw), bytes=len(raw))

    for corpus, count, width in (('table', 8192, 256), ('query', 1152, 128)):
        for start in range(0, count, width):
            block = [trajectory(factors(corpus, ordinal),
                     capture=collector.add if corpus == 'table' else None)
                     for ordinal in range(start, start + width)]
            chunks.append(publish(f'population/{corpus}-{start // width:03d}.jsonl',
                                  b''.join(encoded(row) for row in block)))
            if corpus == 'table':
                observed_stacks.update(t['factors']['stack_profile'] for t in block)
                observed_rules.update(t['factors']['lineup'] for t in block)
                table_streets.update(r['expected']['street'] for t in block for r in t['contexts'])
            else:
                query.extend(block)
        del block
    rows = collector.ordered()
    collector.seen.clear()
    query_contexts = [r for t in query for r in t['contexts']]
    require(len(rows) == 65536 and table_streets == set(STREETS)
            and observed_stacks == {0, 1} and observed_rules == {0, 1}
            and {r['expected']['street'] for r in query_contexts} == set(STREETS)
            and {r['expected']['actor'] for r in query_contexts} == set(range(6))
            and {history_bin(r['expected']['history_atoms']) for r in query_contexts} >= set(BINS),
            'coverage_missing')
    coverage = dict(streets=list(STREETS), seats=list(range(6)), stacks=[0, 1], rules=[0, 1],
                    bins=list(BINS), qualified_prefix_entries=len(rows))
    fit = _capacity_rows(rows)
    sizes = sorted({0, 128, 1024, 8192, 65536, fit['n_fit']})
    artifacts = []
    for size in sizes:
        raw, metadata = _artifact_rows(rows[:size])
        metadata['file'] = publish(f'artifacts/{size}.json', raw)
        metadata['labels'] = ([str(size)] if size in (0, 128, 1024, 8192, 65536) else [])
        if size == fit['n_fit']:
            metadata['labels'].append('N_fit')
        artifacts.append(metadata)
    selected = _select_rows(rows[:fit['n_fit']], query)
    selections = dict(version='workload-r002-selections-v1', first_context=query[0]['contexts'][0],
        history=selected['history'], natural=selected['natural'],
        reuse=[query[i]['contexts'] for i in reuse_ordinals()],
        comparisons={str(n): _select_rows(rows[:n], query)['comparison']
                     for n in (1024, 8192, 65536)})
    sessions = []
    for deal in (0, 1):
        for seat in range(6):
            for lineup in (0, 1):
                factor = factors('query', deal * 72 + seat * 12 + lineup * 2)
                trace = query[factor['ordinal']]
                config = dict(version='pontius-v0a-table-session-v1', button=0,
                    controlled_seat=seat, starting_stacks=[200] * 6, small_blind=1, big_blind=2,
                    opponents=opponents(factor), hands=[trace['deal']])
                sessions.append(publish(f'sessions/d{deal}-s{seat}-l{lineup}.json',
                                        encoded(config)))
    return dict(version='workload-r002-population-v1', recipe=dict(recipe),
                table_trajectories=8192, query_trajectories=1152, n_fit=fit['n_fit'],
                capacity=fit, artifacts=artifacts, chunks=chunks, sessions=sessions,
                selections=publish('selections.json', encoded(selections)), coverage=coverage)


def _runtime(runtime, index):
    exact(runtime, ('id', 'version', 'executable', 'executable_sha256', 'resolved_executable',
                   'resolved_executable_sha256', 'source_root', 'run_root', 'source_sha256',
                   'protocol_sha256', 'authorization'))
    expected = (('3.11', '3.11.15', 'D:/Pontius-tools/py311/Scripts/python.exe'),
                ('3.14', '3.14.6', 'D:/Pontius/.venv/Scripts/python.exe'))[index]
    require(all(type(v) is str for v in runtime.values()))
    require((runtime['id'], runtime['version']) == expected[:2])
    require(PureWindowsPath(runtime['executable']) == PureWindowsPath(expected[2]))
    for field in ('executable_sha256', 'resolved_executable_sha256',
                  'source_sha256', 'protocol_sha256'):
        require(re.fullmatch('[0-9a-f]{64}', runtime[field]) is not None)
    for field in ('executable', 'resolved_executable', 'source_root', 'run_root', 'authorization'):
        path = PureWindowsPath(runtime[field])
        require(path.is_absolute() and '..' not in path.parts)
        require(field == 'resolved_executable' or path.drive.upper() == 'D:')


def freeze_plan(population_manifest, runtimes):
    """Pure complete invocation census; no processes or future trajectories execute here."""
    require(type(population_manifest) is dict
            and population_manifest.get('version') == 'workload-r002-population-v1')
    fit = population_manifest['n_fit']
    integer(fit, 0, 65536)
    require(type(runtimes) is list and len(runtimes) == 2)
    cells = []
    for runtime_index, runtime in enumerate(runtimes):
        _runtime(runtime, runtime_index)
        tag = runtime['id']
        source, run = PureWindowsPath(runtime['source_root']), PureWindowsPath(runtime['run_root'])

        def add(kind, size, parameters):
            cell_id = f"r002-{tag.replace('.', '')}-{len(cells):05d}"
            argv = [runtime['executable'], '-B', '-P',
                    str(source / 'tools/v0a_blueprint_workload.py'),
                    'worker', '--source-root', str(source), '--run-root', str(run),
                    '--authorization', runtime['authorization'], '--cell', cell_id]
            if kind == 'session' and not parameters['diagnostic']:
                argv = [runtime['executable'], '-B', '-P',
                        str(source / 'tools/v0a_table_session.py'),
                        '--session', parameters['session_path'],
                        '--blueprint', parameters['blueprint_path'],
                        '--session-id', parameters['session_id'],
                        '--strategy', parameters['strategy'],
                        '--auto', '--format', 'json']
            cells.append(dict(id=cell_id, runtime=tag, kind=kind, size=size,
                              parameters=parameters, argv=argv))

        def construction(sizes):
            for size in dict.fromkeys(sizes):
                for kind in ('construction', 'memory_traced', 'memory_untraced'):
                    for observation in range(5):
                        add(kind, size, dict(observation=observation))

        construction([0, fit] if runtime_index == 0 else [0, fit, 8192])
        for name in (BINS if runtime_index == 0 else ('0', '31-33')):
            for operation in ('key', 'hash', 'lookup', 'identity', 'provider'):
                add('history', fit, dict(bin=name, operation=operation, blocks=5,
                    subblocks=['hit', 'miss', 'miss', 'hit'], warmups=10, batches=10,
                    batch_calls=100, individual_calls=1000, empty_brackets=10000,
                    empty_batches=5, loop_batches=5))
        for hands in ((1, 2, 8, 32) if runtime_index == 0 else (1, 8)):
            for repetition, arms in enumerate((('fresh', 'retained'), ('retained', 'fresh'),
                                                ('retained', 'fresh'), ('fresh', 'retained'))):
                for arm in arms:
                    add('reuse', fit, dict(hands=hands, repetition=repetition, arm=arm,
                                          trajectory_ordinals=reuse_ordinals()[:hands]))
        ordinal, diagnostic_ordinal = 0, 0
        for deal in ((0, 1) if runtime_index == 0 else (0,)):
            for seat in (range(6) if runtime_index == 0 else (0, 3)):
                for lineup in ((0, 1) if runtime_index == 0 else (0,)):
                    for size in (0, fit):
                        for strategy in STRATEGIES:
                            diagnostic = (deal == 0 and seat in (0, 2, 3) and lineup == 0
                                          if runtime_index == 0 else size == fit)
                            modes = ([True, False] if diagnostic_ordinal % 2 == 0
                                     else [False, True])
                            prefix = ('pontius-v0a-table-session-v2-correctness-' if
                                      strategy == 'baseline-rules-v1' else
                                      'pontius-v0a-table-session-v1-correctness-')
                            for profile in (modes if diagnostic else [False]):
                                add('session', size, dict(diagnostic=profile, ordinal=ordinal,
                                    deal=deal, seat=seat, lineup=lineup, strategy=strategy,
                                    session_id=(prefix +
                                                f"r002-{tag.replace('.', '')}-{ordinal:03d}-"
                                                f"{'d' if profile else 'u'}"),
                                    session_path=str(run /
                                                     f'sessions/d{deal}-s{seat}-l{lineup}.json'),
                                    blueprint_path=str(run / f'artifacts/{size}.json')))
                            diagnostic_ordinal += int(diagnostic)
                            ordinal += 1
        if runtime_index == 0:
            construction(n for n in (0, 128, 1024, 8192, 65536) if n not in (0, fit))
            for size, calls in ((1024, 20), (8192, 10), (65536, 2)):
                add('comparison', size, dict(blocks=5, warmups=20, calls_per_class=calls,
                    provider_order=['legacy', 'prepared'], alternate_provider_first=True,
                    continuous_cycle=True))
    return dict(version='workload-r002-plan-v1',
                population_sha256=sha(encoded(population_manifest)),
                runtimes=json.loads(encoded(runtimes)), cells=cells)
