"""Restore the six authorized raw B representations before their first edit."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path('D:/Pontius/tmp/v0a-evaluation-source-r001')
REPO = ROOT / 'authoring'
GIT = 'C:/Program Files/Git/cmd/git.exe'
B = 'e043f81ecec3ac16128720b42c3312bb41a4ed67'
PINS = {
    'tools/check_stabilization_boundaries.py': '9cc2ae8d8e82ccc77648ade4eb79ae9c34c88a9f',
    'tools/generate_test_inventory.py': '2ac1413b0f89fa848f1ee5df0814b58dcbfa15b8',
    'tests/test-inventory.json': 'c28445aa4b77a98cfd706672d955be4570b98a15',
    'tests/test-profiles.toml': '4469bf813b2e97116667c206784a7bc212f6eef5',
    'tests/test_inventory_and_profiles.py': 'e71a24322878361fb2feb44437d9210cff79c89e',
    '.github/workflows/ci.yml': '3d873a2f75ff1b155bf3533583eddf971eb7790a',
}

def git(*args, raw=None):
    return subprocess.run([GIT, '--no-replace-objects', '-c',
                           'safe.directory=' + REPO.as_posix(), '-C', str(REPO), *args],
                          input=raw, check=True, capture_output=True).stdout

rows = []
prepared = []
for path, pin in PINS.items():
    raw = git('cat-file', 'blob', B + ':' + path)
    assert git('hash-object', '--stdin', raw=raw).decode().strip() == pin
    before = (REPO / path).read_bytes()
    assert before.replace(b'\r\n', b'\n') == raw, path + ': substantive prior edit'
    prepared.append((path, raw))
    rows.append(dict(path=path, base_blob=pin, prior_sha256=hashlib.sha256(before).hexdigest(),
                     restored_sha256=hashlib.sha256(raw).hexdigest(), prior_crlf=before.count(b'\r\n')))
out = ROOT / 'registration-pre-edit-raw-pins.json'
assert not out.exists()
for path, raw in prepared:
    (REPO / path).write_bytes(raw)
    assert git('hash-object', '--no-filters', str(REPO / path)).decode().strip() == PINS[path]
with out.open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(dict(base=B, rows=rows), stream, indent=2)
    stream.write('\n')
report = ROOT / 'packets/task2-r002/reviews/task-review.md'
assert hashlib.sha256(report.read_bytes()).hexdigest() == (
    'a0f567116d578a48a6b8aba057f7d889f4e67be0f46926936cb9887bfb1d52ec')
ledger = REPO / '.superpowers/sdd/2026-09-07-paired-local-evaluation/progress.md'
with ledger.open('a', encoding='utf-8', newline='\n') as stream:
    stream.write('''
## Task 2 FIX checkpoint closed; Task 3 released

Independent FIX review a0f567116d578a48a6b8aba057f7d889f4e67be0f46926936cb9887bfb1d52ec
is CLEAN/spec PASS/engineering PASS/design SOUND on candidate
07fc312e46d2def87a0016cc2c2e2e5c5b48034c, manifest
4dd5397c4606c07f61042a0fcc5325612b93a1c2d36f10fac348b43d04429c4f.
T2-01/T2-02 closed; preserved independent inventory preceded deferred coverage.
Coordinator read full report and verified its raw hash. No integrated acceptance claimed.
Task 3 boundary worker released with ownership only of its new suite/report; coordinator
owns six registration files and census. This implements the recorded split without
overlapping source writes. Absent-policy RED will precede registration implementation.
Six raw B blobs restored from Git and hash-object verified before first registration
edit; prior representations and exact pins retained in registration-pre-edit-raw-pins.json.
''')
print(json.dumps(dict(receipt=str(out), restored=len(rows), task2_review='CLEAN')))
