"""Audit immutable candidate blobs and retained registrations without source imports."""
import hashlib
import copy
import json
from pathlib import Path
import subprocess
import sys
import tomllib

root = Path('D:/Pontius/tmp/v0a-evaluation-source-r001')
repo = root / 'authoring'
git = 'C:/Program Files/Git/cmd/git.exe'
base = '34616938c708b1ca306b9d8a17b9d98e2f9e451f'
candidate, round_name = sys.argv[1:]
assert len(candidate) == 40 and set(candidate) <= set('0123456789abcdef')
assert round_name.startswith('r') and len(round_name) == 4 and round_name[1:].isdigit()
packet = root / 'packets' / round_name
identity = json.loads((packet / 'candidate.json').read_bytes())
assert identity['commit'] == candidate and identity['base'] == base


def run(*args):
    return subprocess.run([git, '--no-replace-objects', '-c', f'safe.directory={repo.as_posix()}',
                           '-C', str(repo), *args], capture_output=True, check=True).stdout


def blob(commit, path):
    return run('cat-file', 'blob', f'{commit}:{path}')


new = ('tools/v0a_evaluation.py', 'tools/v0a_evaluation_contract.py',
       'tests/test_v0a_evaluation_contract.py', 'tests/test_v0a_evaluation_runner.py',
       'tests/test_v0a_evaluation_boundary.py', 'tests/fixtures/evaluation/controls.json')
exceptions = ('tools/check_stabilization_boundaries.py', 'tools/generate_test_inventory.py',
              'tests/test-inventory.json', 'tests/test-profiles.toml',
              'tests/test_inventory_and_profiles.py', '.github/workflows/ci.yml')
expected_pins = ('9cc2ae8d8e82ccc77648ade4eb79ae9c34c88a9f',
                 '2ac1413b0f89fa848f1ee5df0814b58dcbfa15b8',
                 'c28445aa4b77a98cfd706672d955be4570b98a15',
                 '4469bf813b2e97116667c206784a7bc212f6eef5',
                 'e71a24322878361fb2feb44437d9210cff79c89e',
                 '3d873a2f75ff1b155bf3533583eddf971eb7790a')
changed = run('diff-tree', '-r', '--no-renames', '--no-commit-id', '--name-only',
              base, candidate).decode().splitlines()
assert set(changed) == set(new + exceptions), changed
status = run('diff-tree', '-r', '--no-renames', '--no-commit-id', '--name-status',
             base, candidate).decode().splitlines()
assert set(status) == {f'A\t{p}' for p in new} | {f'M\t{p}' for p in exceptions}
for path, pin in zip(exceptions, expected_pins):
    assert run('rev-parse', f'{base}:{path}').decode().strip() == pin, path
records = []
raw = {}
for path in changed:
    data = raw[path] = blob(candidate, path)
    assert data.endswith(b'\n') and b'\r' not in data and not data.startswith(b'\xef\xbb\xbf'), path
    lines = data.decode('utf-8').splitlines()
    if path in new[:5]:
        assert max(map(len, lines), default=0) <= 100, path
        assert all(line == line.rstrip() for line in lines), path
    records.append(dict(path=path, bytes=len(data), lines=len(lines),
                        sha256=hashlib.sha256(data).hexdigest()))
manifest = ''.join(sorted(f"{r['sha256']}  {r['path']}\n" for r in records)).encode()
assert manifest == (packet / 'manifest.sha256').read_bytes()
assert hashlib.sha256(manifest).hexdigest() == identity['manifest_sha256']
production = sum(len(raw[p].splitlines()) for p in new[:2])
tests = sum(len(raw[p].splitlines()) for p in new[2:5])
fixture_bytes = len(raw[new[5]])
manual = 0
for line in run('diff', '--no-renames', '--numstat', base, candidate, '--',
                *[p for p in exceptions if p not in exceptions[2:4]]).decode().splitlines():
    added, removed, _ = line.split('\t')
    manual += int(added) + int(removed)
assert production <= 1250 and tests <= 1800 and fixture_bytes <= 32768 and manual <= 160, (
    production, tests, fixture_bytes, manual)
old_inventory = json.loads(blob(base, exceptions[2]))
inventory = json.loads(raw[exceptions[2]])
assert set(inventory) == set(old_inventory)
assert all(inventory[key] == value for key, value in old_inventory.items()
           if key not in ('discovery', 'entries'))
old_entries = {r['stable_id']: r for r in old_inventory['entries']}
entries = {r['stable_id']: r for r in inventory['entries']}
assert len(entries) == len(inventory['entries'])
assert all(entries.get(key) == value for key, value in old_entries.items())
new_ids = sorted(set(entries) - set(old_entries))
assert new_ids and all(entries[key]['relative_path'] in new[2:5] for key in new_ids)
old_profiles = tomllib.loads(blob(base, exceptions[3]).decode())
profiles = tomllib.loads(raw[exceptions[3]].decode())
assert set(profiles) == set(old_profiles)
normalized_profiles = copy.deepcopy(profiles)
expected_new_payload_ids = {'current:' + Path(path).stem for path in new[2:5]}
for profile in normalized_profiles['profile']:
    added_members = [p for p in profile['payload_ids'] if p in expected_new_payload_ids]
    assert (len(added_members) == 3 and set(added_members) == expected_new_payload_ids
            if profile['name'] == 'current' else not added_members)
    profile['payload_ids'] = [p for p in profile['payload_ids'] if p not in expected_new_payload_ids]
assert all(normalized_profiles[key] == value for key, value in old_profiles.items()
           if key not in ('stabilization_test_files', 'payload'))
old_suite_paths = old_profiles['stabilization_test_files']
suite_paths = profiles['stabilization_test_files']
assert len(suite_paths) == len(old_suite_paths) + 3
assert set(suite_paths) - set(old_suite_paths) == set(new[2:5])
assert [p for p in suite_paths if p in old_suite_paths] == old_suite_paths
old_payloads = {r['payload_id']: r for r in old_profiles['payload']}
payloads = {r['payload_id']: r for r in profiles['payload']}
assert len(payloads) == len(profiles['payload'])
assert all(payloads.get(key) == value for key, value in old_payloads.items())
assert set(payloads) - set(old_payloads) == expected_new_payload_ids
assert [r['payload_id'] for r in profiles['payload'] if r['payload_id'] in old_payloads] == [
    r['payload_id'] for r in old_profiles['payload']]
result = dict(version='pontius-evaluation-source-audit-v1', candidate=identity,
              raw_files=records, production_lines=production, test_lines=tests,
              manual_registration_changed_lines=manual, fixture_bytes=fixture_bytes,
              old_entries_preserved=len(old_entries), old_payloads_preserved=len(old_payloads),
              new_test_ids=new_ids,
              new_payload_ids=sorted(set(payloads) - set(old_payloads)))
output = packet / 'source-audit.json'
encoded = (json.dumps(result, sort_keys=True, indent=2) + '\n').encode()
with output.open('xb') as stream:
    assert stream.write(encoded) == len(encoded)
assert output.read_bytes() == encoded
print(json.dumps(dict(output=str(output), sha256=hashlib.sha256(encoded).hexdigest(),
                     production_lines=production, test_lines=tests,
                     manual_registration_changed_lines=manual, new_tests=len(new_ids))))
