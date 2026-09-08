"""Index retained exact-candidate acceptance receipts without running repository code."""
import hashlib
import json
from pathlib import Path
import re
import sys

root = Path('D:/Pontius/tmp/v0a-evaluation-source-r001')
round_name = sys.argv[1]
assert re.fullmatch(r'r[0-9]{3}', round_name)
packet = root / 'packets' / round_name
identity = json.loads((packet / 'candidate.json').read_bytes())
commands = (
    ('status', ['-m', 'pontius.status_generation', '--check']),
    ('status-tests', ['tests/test_status_generation.py']),
    ('boundaries', ['tools/check_stabilization_boundaries.py']),
    ('inventory-check', ['tools/generate_test_inventory.py', '--check']),
    ('inventory-tests', ['tests/test_inventory_and_profiles.py']),
    ('evaluation-contract', ['tests/test_v0a_evaluation_contract.py']),
    ('evaluation-runner', ['tests/test_v0a_evaluation_runner.py']),
    ('evaluation-boundary', ['tests/test_v0a_evaluation_boundary.py']),
    ('seeded', ['tests/test_seeded_deals.py']),
    ('seeded-boundary', ['tests/test_seeded_deals_boundary.py']),
    ('host', ['tests/test_v0a_table_host.py']),
    ('host-boundary', ['tests/test_v0a_table_host_boundary.py']),
    ('session', ['tests/test_v0a_table_session.py']),
    ('session-boundary', ['tests/test_v0a_table_session_boundary.py']),
    ('provider-session', ['tests/test_decision_provider_session.py']),
    ('provider-transport', ['tests/test_decision_provider_transport.py']),
)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


rows = []
totals = {}
previous_finish = None
for slot, version, executable in (
    ('311', '3.11.15', 'D:/Pontius-tools/py311/Scripts/python.exe'),
    ('314', '3.14.6', 'D:/Pontius/.venv/Scripts/python.exe'),
):
    totals[slot] = {'commands': 0, 'tests': 0, 'skips': 0}
    for number, (name, arguments) in enumerate(commands, 1):
        run_name = f'a-{round_name}-{number:02d}-{slot}'
        path = root / 'run-records' / (run_name + '.json')
        records = json.loads(path.read_bytes())
        assert len(records) == 2, path
        probe, payload = records
        assert all(r['exit_code'] == 0 and r['snapshot_head'] == identity['commit']
                   and Path(r['interpreter']) == Path(executable) for r in records), path
        expected_snapshot = root / 'snapshots' / run_name
        assert all(Path(r['snapshot']) == expected_snapshot for r in records), path
        assert probe['argv'][:3] == ['-B', '-P', '-c'], path
        assert probe['stdout'].startswith(version + ' '), path
        assert payload['argv'] == ['-B', '-P', *arguments], path
        if previous_finish is not None:
            assert probe['started_utc'] >= previous_finish, path
        previous_finish = payload['finished_utc']
        output = payload['stdout'] + '\n' + payload['stderr']
        matches = re.findall(r'Ran (\d+) tests? in ([\d.]+)s', output)
        tests = int(matches[-1][0]) if matches else 0
        skips = sum(map(int, re.findall(r'skipped=(\d+)', output)))
        if arguments[0].startswith('tests/'):
            assert len(matches) == 1 and re.search(r'^OK(?:\s|$)', output, re.M), path
        totals[slot]['commands'] += 1
        totals[slot]['tests'] += tests
        totals[slot]['skips'] += skips
        rows.append({'slot': slot, 'name': name, 'argv': payload['argv'],
                     'receipt': str(path), 'sha256': digest(path), 'tests': tests,
                     'skips': skips, 'started_utc': payload['started_utc'],
                     'finished_utc': payload['finished_utc']})
assert all(t['commands'] == 16 for t in totals.values())
assert totals['311']['tests'] == totals['314']['tests']
harness = root / 'run-source-snapshot-v2.ps1'
result = {'version': 'pontius-evaluation-final-acceptance-summary-v1',
          'candidate': identity, 'harness': {'path': str(harness), 'sha256': digest(harness)},
          'totals': totals, 'acceptance_receipts': rows,
          'retained_prior_receipts': [
              {'path': str(p), 'sha256': digest(p)}
              for p in sorted((root / 'run-records').glob('*.json'))
              if p.name not in {Path(r['receipt']).name for r in rows}],
          'standing': 'Source correctness checks only; no evaluation or source-seal authority.'}
directory = packet / 'checks'
directory.mkdir(exist_ok=True)
destination = directory / 'final-acceptance-summary.json'
raw = (json.dumps(result, sort_keys=True, indent=2) + '\n').encode('utf-8')
with destination.open('xb') as stream:
    assert stream.write(raw) == len(raw)
assert destination.read_bytes() == raw
print(json.dumps({'path': str(destination), 'sha256': digest(destination), 'totals': totals}))
