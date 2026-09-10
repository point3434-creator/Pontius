"""Explicit solve/export/agreement phases for the existing eval-panel worker."""
from __future__ import annotations

import base64
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
VERSION = 'pontius-eval-panel-completion-plan-v1'
PHASES = ('solve', 'export', 'agreement')
HEX = '0123456789abcdef'
PREREQUISITES = {
    'capacity': '29f532a900289c3e7b274646a7fc7332ff1a0aa9e6d74c332319668783d89e53',
    'preflight': '8a17325eaa07e0f8774dcb7bc2050a3ae233cf47bebfc63a6b59574031fb742f',
    'decision': '037a0de1b8605dc182cdc99ef0ef146e8c5ab08f73d984e4497e5a7a94afe2cf',
}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def load_tool(name):
    alias = 'pontius_eval_completion_' + name
    path = ROOT / 'tools' / (name + '.py')
    if alias not in sys.modules:
        spec = importlib.util.spec_from_file_location(alias, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[alias] = module
        try:
            spec.loader.exec_module(module)
        except BaseException:
            del sys.modules[alias]
            raise
    module = sys.modules[alias]
    require(Path(module.__file__).resolve() == path.resolve(), 'tool cache root mismatch')
    return module


def digest(value):
    return type(value) is str and len(value) == 64 and all(c in HEX for c in value)


def binding(value):
    require(type(value) is dict and set(value) == {'path', 'sha256'}
            and type(value['path']) is str and Path(value['path']).is_absolute()
            and digest(value['sha256']), 'input must bind an absolute path and SHA-256')


def bound_bytes(value, limit=16 * 1024 * 1024):
    binding(value)
    owner = load_tool('v0a_table_host').OwnedInput(Path(value['path']), limit)
    require(hashlib.sha256(owner.raw).hexdigest() == value['sha256'], 'bound input digest mismatch')
    return owner.raw


def document(raw):
    def pairs(items):
        value = {}
        for key, item in items:
            require(key not in value, 'duplicate input member')
            value[key] = item
        return value

    def constant(value):
        raise ValueError('nonfinite input constant')

    return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)


def validate_bank(bank):
    require(type(bank) is dict and set(bank) == {
        'seed_start', 'seed_count', 'indices', 'holdout_seed_start', 'holdout_seed_count',
        'sizing_rationale'}, 'witness bank members differ')
    require(digest(bank['seed_start']) and digest(bank['holdout_seed_start']), 'invalid seed start')
    require(all(type(bank[k]) is int and 1 <= bank[k] <= 65536
                for k in ('seed_count', 'holdout_seed_count')), 'invalid finite seed count')
    first, reserved = int(bank['seed_start'], 16), int(bank['holdout_seed_start'], 16)
    end, reserved_end = first + bank['seed_count'], reserved + bank['holdout_seed_count']
    require(max(end, reserved_end) <= 2**256 and (end <= reserved or reserved_end <= first),
            'development and holdout seed ranges overlap or overflow')
    indices = bank['indices']
    require(type(indices) is list and indices and len(indices) <= 16
            and all(type(i) is int and 0 <= i <= 15 for i in indices)
            and indices == sorted(set(indices)), 'indices must be unique ascending 0..15')
    require(type(bank['sizing_rationale']) is str and 1 <= len(bank['sizing_rationale']) <= 2048,
            'bank needs an explicit sizing rationale and dependence assumptions')


def validate(plan, entry):
    from pontius import eval_bridge as bridge
    phase = plan.get('phase')
    expected = entry.COMMON_KEYS | {'coverage', 'pool_count', 'prerequisites', 'inputs'}
    if phase == 'agreement':
        expected |= {'witness_bank'}
    require(phase in PHASES and set(plan) == expected, 'invalid completion phase members')
    base = {key: value for key, value in plan.items() if key in entry.COMMON_KEYS}
    base.update(version=entry.PLAN_VERSION, phase='capacity')
    entry.validate_plan(base)
    require(plan['coverage'] in ('declared-full', 'test-subset'), 'invalid completion coverage')
    count = plan['pool_count']
    require(type(count) is int and 1 <= count <= bridge.HERO_COUNT, 'invalid pool count')
    require(type(plan['prerequisites']) is dict and type(plan['inputs']) is dict,
            'prerequisites and inputs must be objects')
    if plan['coverage'] == 'declared-full':
        require(count == bridge.HERO_COUNT and plan['board'] == entry.DEVELOPMENT_BOARD,
                'full pool differs from controller decision')
        require(set(plan['prerequisites']) == set(PREREQUISITES), 'missing measured prerequisites')
        for name, expected_hash in PREREQUISITES.items():
            item = plan['prerequisites'][name]
            binding(item)
            require(item['sha256'] == expected_hash, 'prerequisite differs from resource decision')
            raw = bound_bytes(item)
            if name != 'decision':
                result = document(raw)
                require(result['status'] == 'completed' and result['cleanup_verified'] is True,
                        'prerequisite did not complete')
                require(result['phase'] == name, 'wrong prerequisite phase')
                if name == 'capacity':
                    require(result['permutation_sha256'] == bridge.permutation_digest(
                        bridge.strength_blind_permutation(bridge.hero_hands(
                            bridge.board_cards(plan['board'])), plan['pool_seed'])),
                        'pool order differs from measured capacity')
                else:
                    require(result['sample_complete'] is True, 'preflight sample incomplete')
        if phase == 'solve':
            require(plan['resource'] == {'seconds': 600, 'memory_mib': 2048},
                    'solve envelope differs from controller decision')
    else:
        require(plan['prerequisites'] == {}, 'test subset cannot claim retained prerequisites')
        require(count < bridge.HERO_COUNT, 'test subset cannot masquerade as full pool')
    keys = set() if phase == 'solve' else {'teacher', 'producer_result'}
    if phase == 'agreement':
        keys.add('blueprint')
        validate_bank(plan['witness_bank'])
    require(set(plan['inputs']) == keys, 'phase inputs are missing or unexpected')
    for value in plan['inputs'].values():
        binding(value)
    return entry.AdmittedPlan(json.dumps(plan, separators=(',', ':')), ())


def witnesses(board, required, bank, *, deadline, progress=None):
    from pontius import eval_bridge as bridge
    validate_bank(bank)
    dealer = load_tool('v0a_seeded_deals')
    required = set(required)
    selected, draws = {}, []
    counts = dict(collision=0, witness=0, unused=0)
    for offset in range(bank['seed_count']):
        seed = format(int(bank['seed_start'], 16) + offset, '064x')
        for index in bank['indices']:
            require(time.perf_counter() < deadline, 'witness scan budget exhausted')
            deal = dealer.deal_for_hand(seed, index)
            hand = bridge.hand_name(deal['private_hands'][bridge.CONTROLLED_SEAT])
            if any(card in board for private in deal['private_hands'] for card in private):
                status = 'collision'
            elif hand in required and hand not in selected:
                status = 'witness'
                selected[hand] = dict(seed=seed, index=index,
                                      private_hands=deal['private_hands'])
            else:
                status = 'unused'
            counts[status] += 1
            draws.append(dict(seed=seed, index=index, hand=hand, status=status))
            if progress is not None:
                progress(draws[-1])
    collision_free = math.comb(47, 12) / math.comb(52, 12)
    estimate = min(1.0, len(required) * (1 - collision_free / bridge.HERO_COUNT)**len(draws))
    return dict(selected=selected, draws=draws, counts=counts,
                missing=sorted(required - selected.keys()), complete=set(selected) == required,
                planning=dict(iid_missing_union_bound_estimate=estimate,
                              assumptions='IID approximation only; seeded draws may be dependent; '
                              'acceptance uses the actual complete census'))


def artifact(emit, name, raw):
    emit(dict(event='observation', kind='artifact', name=name, bytes=len(raw),
              sha256=hashlib.sha256(raw).hexdigest(),
              artifact_base64=base64.b64encode(raw).decode('ascii')))


def solve(plan, emit, deadline, measure):
    from pontius import eval_bridge as bridge
    board, root = bridge.board_cards(plan['board']), bridge.replay_root()
    order = bridge.strength_blind_permutation(bridge.hero_hands(board), plan['pool_seed'])
    rows, tie_check = [], None
    for hero in order[:plan['pool_count']]:
        require(time.perf_counter() < deadline, 'solve budget exhausted before next hero')
        row, cost = measure(lambda: bridge.hand_totals(root, board, hero))
        rows.append(row)
        emit(dict(event='observation', kind='teacher_hand', row=row, cost=cost, complete=True))
        if (tie_check is None and row['check_total'] == row['bet_total']
                and row['wins'] + row['losses'] > 0):
            costs = {}

            def stage(name, function):
                require(time.perf_counter() < deadline, 'tie reference budget exhausted')
                value, costs[name] = measure(function)
                return value

            reference = stage('reference_construction',
                              lambda: bridge.build_reference(root, board, hero))
            values = {str(bridge.CHECK): stage('forced_check', lambda: bridge.forced_value(
                reference, bridge.CHECK)), row['bet']: stage('forced_bet',
                    lambda: bridge.forced_value(reference, reference['bet']))}
            value, selected = stage('best_response',
                                    lambda: bridge.reference_best_response(reference))
            comparison = stage('comparison', lambda: bridge.validate_reference(
                row, values, value, selected, reference['hero_key']))
            tie_check = dict(hand=row['hand'], values=values, comparison=comparison, costs=costs)
            emit(dict(event='observation', kind='nonzero_tie_reference', **tie_check))
            require(comparison['passed'], 'first nonzero-return tie disagrees with reference')
    require(time.perf_counter() < deadline, 'solve budget exhausted before teacher publication')
    raw = bridge.teacher_bytes(board, order, rows)
    artifact(emit, 'teacher.json', raw)
    emit(dict(event='observation', kind='solve_summary', complete=True,
              coverage=plan['coverage'], completed_hands=len(rows),
              nonzero_tie='validated_first' if tie_check else 'absent_in_completed_pool',
              teacher_sha256=hashlib.sha256(raw).hexdigest()))


def teacher_input(plan):
    from pontius import eval_bridge as bridge
    raw = bound_bytes(plan['inputs']['teacher'])
    board, hands, actions = bridge.teacher_actions(raw)
    require(list(map(bridge.hand_name, hands)) == plan['permutation'][:plan['pool_count']]
            and list(map(bridge.format_card, board)) == plan['board'],
            'teacher pool or board differs from plan')
    require(document(raw)['permutation'] == plan['permutation'], 'teacher order differs from plan')
    result = document(bound_bytes(plan['inputs']['producer_result']))
    expected = 'solve' if plan['phase'] == 'export' else 'export'
    require(result.get('status') == 'completed' and result.get('phase') == expected
            and result.get('cleanup_verified') is True
            and result.get('phase_complete') is True
            and result.get('coverage') == plan['coverage'], 'producer phase did not complete')
    previous = result['plan']
    require(previous['pool_count'] == plan['pool_count']
            and previous['prerequisites'] == plan['prerequisites']
            and result['permutation_sha256'] == bridge.permutation_digest(
                bridge.strength_blind_permutation(bridge.hero_hands(board), plan['pool_seed'])),
            'producer scope differs from phase plan')
    produced = {row['name']: row for row in result['observations'] if row.get('kind') == 'artifact'}
    for name, key in (('teacher.json', 'teacher'), ('blueprint.json', 'blueprint')):
        if key in plan['inputs']:
            row = produced.get(name, {})
            require(row.get('sha256') == plan['inputs'][key]['sha256']
                    and row.get('retention') == 'complete', 'producer artifact is not bound')
    return raw, board, hands, actions


def export(plan, emit, deadline, measure):
    from pontius import eval_bridge as bridge
    raw, _, _, _ = teacher_input(plan)
    require(time.perf_counter() < deadline, 'export budget exhausted')
    (wire, report), cost = measure(lambda: bridge.export_teacher(raw))
    repeated, _ = bridge.export_teacher(raw)
    require(wire == repeated, 'repeated export is not byte-identical')
    emit(dict(event='observation', kind='export_encoding', report=report, cost=cost))
    membership, member_cost = measure(lambda: bridge.validate_membership(raw, wire))
    emit(dict(event='observation', kind='membership', report=membership, cost=member_cost))
    require(membership['passed'], 'exact membership or direct provider check failed')
    require(time.perf_counter() < deadline, 'export budget exhausted before publication')
    artifact(emit, 'teacher.json', raw)
    artifact(emit, 'blueprint.json', wire)
    emit(dict(event='observation', kind='export_summary', complete=True,
              coverage=plan['coverage'], hands=plan['pool_count']))


def run(plan, emit, deadline, measure):
    require(time.perf_counter() < deadline, 'completion phase budget exhausted')
    {'solve': solve, 'export': export, 'agreement': agreement}[plan['phase']](
        plan, emit, deadline, measure)


def play(witness, board, wire, actions, directory, ordinal, label, *, stacks=4):
    from types import SimpleNamespace
    from pontius import eval_agreement
    from pontius.blueprint_artifact.codec import decode_blueprint
    from pontius.execution import CONTEXT_ENV
    context = document(os.environ[CONTEXT_ENV].encode())
    require(Path.cwd().resolve() == Path(context['root']).resolve() == ROOT.resolve(),
            'Session preparation root differs from inherited run root')
    require(directory.resolve().is_relative_to(ROOT.resolve()), 'host inputs leave owned run root')
    session_module = load_tool('v0a_table_session')
    schedule = dict(version=session_module.VERSION, button=0, controlled_seat=2,
                    starting_stacks=[stacks] * 6, small_blind=1, big_blind=2,
                    opponents=['fold_to_bet', 'passive', None,
                               'fold_to_bet', 'fold_to_bet', 'fold_to_bet'],
                    hands=[dict(private_hands=witness['private_hands'], board_runout=list(board))])
    directory.mkdir(parents=True, exist_ok=True)
    input_path, blueprint_path = directory / 'host-input.json', directory / 'host-blueprint.json'
    input_path.write_bytes(session_module.encode(schedule))
    blueprint_path.write_bytes(wire)
    args = SimpleNamespace(session=str(input_path), blueprint=str(blueprint_path), auto=True,
                           strategy='blueprint-v1', development=False,
                           reviewed_commit=context['commit'],
                           session_id=f'{session_module.PREFIX}bridge-{ordinal}-{label}')
    session = session_module.Session(args)
    result = session.run()
    classification = eval_agreement.classify(
        result, blueprint=decode_blueprint(wire), teacher_actions=actions, board=board,
        private_hands=tuple(tuple(h) for h in witness['private_hands']), stacks=stacks)
    return dict(label=label, witness=witness, session=result, classification=classification,
                blueprint_wire_sha256=hashlib.sha256(wire).hexdigest())


def agreement(plan, emit, deadline, measure):
    from pontius import eval_bridge as bridge, eval_agreement
    from pontius.execution import CONTEXT_ENV
    from pontius.immutable_blueprint import BlueprintActionEntry, ImmutableBlueprintActionSource
    from pontius.blueprint_artifact.codec import decode_blueprint, encode_blueprint
    raw, board, hands, actions = teacher_input(plan)
    wire = bound_bytes(plan['inputs']['blueprint'], bridge.ARTIFACT_CAP)
    expected, _ = bridge.export_teacher(raw)
    require(wire == expected, 'agreement wire differs from deterministic teacher export')
    names = [bridge.hand_name(hand) for hand in hands]
    scan, scan_cost = measure(lambda: witnesses(
        board, names, plan['witness_bank'], deadline=deadline,
        progress=lambda row: emit(dict(event='observation', kind='witness_draw', **row))))
    emit(dict(event='observation', kind='witness_scan', report=scan, cost=scan_cost))
    require(scan['complete'], 'finite bank does not cover the declared pool')
    context = document(os.environ[CONTEXT_ENV].encode())
    directory = ROOT / context['output_directory'] / 'host-inputs'
    results = []

    def attempt(name, control_wire, expected_actions, label, *, stacks=4):
        require(time.perf_counter() < deadline, 'agreement budget exhausted before next attempt')
        ordinal = len(results)
        emit(dict(event='observation', kind='attempt_scheduled', ordinal=ordinal,
                  label=label, hand=name, witness=scan['selected'][name]))
        result, cost = measure(lambda: play(scan['selected'][name], board, control_wire,
            expected_actions, directory, ordinal, label, stacks=stacks))
        results.append(result)
        emit(dict(event='observation', kind='host_attempt', ordinal=ordinal, hand=name,
                  result=result, cost=cost, complete=True))
        return result

    for name in names:
        result = attempt(name, wire, actions, 'primary')
        require(result['classification']['classification'] == 'hit',
                'host teacher agreement failed')
    first = names[0]
    source = decode_blueprint(wire)
    key = bridge.root_key(bridge.replay_root(), board, hands[0])
    off_wire = encode_blueprint(ImmutableBlueprintActionSource('test-off-pool-control',
        tuple(entry for entry in source.entries if entry.key != key)))
    check_wire = encode_blueprint(ImmutableBlueprintActionSource('test-check-hit-control',
        (BlueprintActionEntry(key, bridge.CHECK),)))
    artifact(emit, 'control-off-pool.json', off_wire)
    artifact(emit, 'control-check-hit.json', check_wire)
    off = attempt(first, off_wire,
                  {name: action for name, action in actions.items() if name != first}, 'off-pool')
    check = attempt(first, check_wire, {first: bridge.CHECK}, 'check-hit')
    changed = attempt(first, wire, actions, 'changed-stack', stacks=6)
    require(off['classification']['chip_eligible']
            and off['classification']['classification'] == 'unsupported', 'off-pool control failed')
    require(check['classification']['classification'] == 'hit', 'CHECK-hit control failed')
    require(changed['classification']['chip_eligible']
            and changed['classification']['observed_table_hits'] == 0, 'changed-stack control hit')
    summary = eval_agreement.summarize([row['classification'] for row in results[:len(names)]],
                                      len(names))
    emit(dict(event='observation', kind='agreement_summary', complete=summary['complete'],
              coverage=plan['coverage'], primary=summary, controls=3,
              action_categories=sorted({str(action) for action in actions.values()}),
              host_complement='test proper-subset control' if len(names) == bridge.HERO_COUNT
              else 'one off-pool host control; complete complement checked through provider'))


def complete(observations, plan):
    """Reconcile the admitted phase against worker observations before reporting success."""
    from pontius import eval_bridge as bridge
    phase, count = plan['phase'], plan['pool_count']
    summaries = [row for row in observations if row.get('kind') == phase + '_summary']
    if len(summaries) != 1 or summaries[0].get('complete') is not True:
        return False
    if summaries[0].get('coverage') != plan['coverage']:
        return False
    names = plan['permutation'][:count]
    if phase == 'solve':
        rows = [row['row'] for row in observations if row.get('kind') == 'teacher_hand']
        if [row['hand'] for row in rows] != names or summaries[0]['completed_hands'] != count:
            return False
        needed = [row for row in rows if row['check_total'] == row['bet_total']
                  and row['wins'] + row['losses'] > 0]
        references = [row for row in observations if row.get('kind') == 'nonzero_tie_reference']
        if needed and (len(references) != 1 or references[0]['hand'] != needed[0]['hand']
                       or references[0]['comparison']['passed'] is not True):
            return False
        if not needed and references:
            return False
    elif phase == 'export':
        membership = [row for row in observations if row.get('kind') == 'membership']
        if len(membership) != 1 or membership[0]['report']['passed'] is not True:
            return False
    else:
        scheduled = [row for row in observations if row.get('kind') == 'attempt_scheduled']
        attempts = [row for row in observations if row.get('kind') == 'host_attempt']
        if (len(scheduled) != count + 3 or len(attempts) != count + 3
                or [row['ordinal'] for row in scheduled] != list(range(count + 3))
                or [row['ordinal'] for row in attempts] != list(range(count + 3))
                or [row['hand'] for row in attempts[:count]] != names
                or any(row['result']['classification']['classification'] != 'hit'
                       for row in attempts[:count])):
            return False
        off, check, changed = [row['result']['classification'] for row in attempts[count:]]
        if not (off['chip_eligible'] and off['classification'] == 'unsupported'
                and check['classification'] == 'hit' and changed['chip_eligible']
                and changed['observed_table_hits'] == 0):
            return False
    expected = {'solve': {'teacher.json'}, 'export': {'teacher.json', 'blueprint.json'},
                'agreement': {'control-off-pool.json', 'control-check-hit.json'}}[phase]
    artifacts = [row for row in observations if row.get('kind') == 'artifact']
    if len(artifacts) != len(expected) or {row['name'] for row in artifacts} != expected:
        return False
    for row in artifacts:
        raw = base64.b64decode(row['artifact_base64'], validate=True)
        if len(raw) != row['bytes'] or hashlib.sha256(raw).hexdigest() != row['sha256']:
            return False
        if row['name'] == 'teacher.json':
            board, hands, _ = bridge.teacher_actions(raw)
            if list(map(bridge.hand_name, hands)) != names:
                return False
            if phase == 'solve':
                order = bridge.strength_blind_permutation(
                    bridge.hero_hands(board), plan['pool_seed'])
                if (raw != bridge.teacher_bytes(board, order, rows)
                        or summaries[0]['teacher_sha256'] != row['sha256']):
                    return False
    return True


def accounting(observations, plan):
    from pontius.eval_agreement import summarize
    scheduled = [row for row in observations if row.get('kind') == 'attempt_scheduled']
    attempts = [row for row in observations if row.get('kind') == 'host_attempt']
    primary = [row for row in attempts if row['result']['label'] == 'primary']
    names = plan['permutation'][:plan['pool_count']]
    expected = [(name, 'primary') for name in names]
    expected.extend((names[0], label) for label in ('off-pool', 'check-hit', 'changed-stack'))
    require(len(scheduled) <= len(expected)
            and [row['ordinal'] for row in scheduled] == list(range(len(scheduled)))
            and [(row['hand'], row['label']) for row in scheduled] == expected[:len(scheduled)],
            'agreement schedule differs from admitted order')
    require(len(attempts) <= len(scheduled)
            and [row['ordinal'] for row in attempts] == list(range(len(attempts))),
            'orphan, duplicate or out-of-order agreement outcomes')
    for row, request in zip(attempts, scheduled):
        result = row['result']
        require(row['hand'] == request['hand'] and result['label'] == request['label']
                and result['witness'] == request['witness'],
                'outcome differs from scheduled witness')
    return dict(primary=summarize([row['result']['classification'] for row in primary], len(names)),
                scheduled_attempts=len(scheduled), observed_attempts=len(attempts),
                missing_outcomes=len(scheduled) - len(attempts),
                missing_pool_hands=[name for name in names
                                    if name not in {row['hand'] for row in primary}])


def retain(report, directory):
    """Bind intended artifact identity before rename and reconcile interrupted publication."""
    allowed = {'teacher.json', 'blueprint.json', 'control-off-pool.json', 'control-check-hit.json'}
    for row in report['observations']:
        if row.get('kind') != 'artifact':
            continue
        require(row['name'] in allowed, 'unexpected artifact name')
        raw = base64.b64decode(row['artifact_base64'], validate=True)
        require(len(raw) == row['bytes'] and hashlib.sha256(raw).hexdigest() == row['sha256'],
                'artifact bytes differ from intended identity')
        path = directory / row['name']
        staging = path.with_name(path.name + '.partial')
        row.update(path=path.name, retention='pending')
        try:
            with staging.open('xb') as stream:
                stream.write(raw)
            os.replace(staging, path)
        finally:
            if path.is_file():
                require(path.read_bytes() == raw, 'published artifact differs from intended bytes')
                row['retention'] = 'complete'
                del row['artifact_base64']
