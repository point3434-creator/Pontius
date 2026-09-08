"""Prepare an isolated documentation-only paired rehearsal preregistration."""
import hashlib
import json
from pathlib import Path
import re
import subprocess

base = 'bd71f4b11dcc0177283431a4ec468fdc152e7686'
root = Path('D:/Pontius/tmp/v0a-paired-prereg-r001')
work = root / 'authoring'
git_exe = 'C:/Program Files/Git/cmd/git.exe'
paths = ['docs/decisions/ADR-0510-preregister-the-first-paired-evaluation-rehearsal.md',
         'docs/architecture/v0a-paired-prereg-r001/preregistration.md',
         'docs/architecture/v0a-paired-prereg-r001/rehearsal-request.json', 'STATUS.md']
assert not root.exists()
root.mkdir()
subprocess.run([git_exe, '--no-replace-objects', '-c', 'safe.directory=D:/Pontius',
    '-c', 'safe.directory=D:/Pontius/.git', 'clone', '--quiet', '--no-hardlinks',
    '--no-checkout', 'D:/Pontius', str(work)], check=True)
subprocess.run([git_exe, '--no-replace-objects', '-C', str(work), '-c', 'core.autocrlf=false',
    'checkout', '--quiet', '-b', 'codex/paired-evaluation-prereg', base], check=True)
request = dict(version='pontius-v0a-evaluation-request-v1', seed='0' * 64,
    deal_count=1, lineups=[['passive'] * 5,
        ['fold_to_bet', 'min_raise_once', 'passive', 'shove_once', 'passive']],
    seat_start=0, initial_button=0, trial_budget_ms=360000, total_budget_ms=9000000)
raw = (json.dumps(request, sort_keys=True, separators=(',', ':'), ensure_ascii=True) + '\n').encode()
for path in paths[:3]:
    (work / path).parent.mkdir(parents=True, exist_ok=True)
(work / paths[2]).write_bytes(raw)
pins = {}
for path in ('tools/v0a_evaluation.py','tools/v0a_evaluation_contract.py',
             'tools/v0a_seeded_deals.py','tools/v0a_table_session.py',
             'tests/fixtures/table_host/empty_blueprint.json'):
    blob = subprocess.run([git_exe, '--no-replace-objects', '-C', str(work), 'cat-file',
        'blob', base + ':' + path], capture_output=True, check=True).stdout
    pins[path] = hashlib.sha256(blob).hexdigest()
facts = dict(base=base, source_tree=subprocess.run([git_exe, '--no-replace-objects',
    '-C', str(work), 'rev-parse', base + '^{tree}'], capture_output=True,
    check=True).stdout.decode().strip(), paths=paths, request_sha256=hashlib.sha256(raw).hexdigest(),
    request_bytes=len(raw), pins=pins, safety_arithmetic_ms=24*(360000+5000)+240000,
    standing='Proposal preparation only; no source/poker/generator payload or commit')
(root / 'preparation-facts.json').write_text(json.dumps(facts, indent=2)+'\n', encoding='utf-8', newline='\n')
# Adapt previously used local snapshot/freezing plumbing to this new four-path scope.
old_root = 'D:\\Pontius\\tmp\\v0a-evaluation-seal-r001'
new_root = 'D:\\Pontius\\tmp\\v0a-paired-prereg-r001'
for old_name, new_name in [('run-seal-snapshot.ps1','run-prereg-snapshot.ps1'),
                           ('freeze-seal.ps1','freeze-prereg.ps1')]:
    script = (Path('D:/Pontius/tmp/v0a-evaluation-seal-r001') / old_name).read_text(encoding='utf-8')
    script = script.replace(old_root, new_root).replace(
        'D:\\Pontius\\tmp\\v0a-evaluation-source-r001\\authoring', new_root+'\\authoring')
    script = script.replace('34616938c708b1ca306b9d8a17b9d98e2f9e451f', base)
    script = script.replace('v0a-evaluation-seal', 'v0a-paired-prereg')
    script = script.replace('snapshots/evaluation-seal/', 'snapshots/paired-prereg/')
    script, count = re.subn(r'\$allowed\s*=\s*@\(.*?\)',
        '$allowed = @(' + ','.join("'" + path + "'" for path in paths) + ')',
        script, count=1, flags=re.S)
    assert count == 1
    (root / new_name).write_text(script, encoding='utf-8', newline='\n')
print(json.dumps(facts))
