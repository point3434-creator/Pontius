"""Append acceptance evidence after cold reviews and the four metadata gates."""
import hashlib
import json
from pathlib import Path
import re
import subprocess

root = Path('D:/Pontius/tmp/v0a-paired-closure-r001')
packet = Path('D:/Pontius-handoffs/v0a-paired-closure/r001')
work = root / 'authoring'
identity = json.loads((packet / 'candidate.json').read_bytes())
candidate = identity['commit']
git_exe = 'C:/Program Files/Git/cmd/git.exe'


def git(repo, *args):
    return subprocess.run([git_exe, '--no-replace-objects', '-c',
        f'safe.directory={repo.as_posix()}', '-C', str(repo), *args],
        check=True, capture_output=True).stdout


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        assert stream.write(raw) == len(raw)


assert candidate == 'e80b794050a466a3f8115b640b53dca3b51816a7'
assert git(work, 'rev-parse', identity['ref']).decode().strip() == candidate
assert git(work, 'rev-parse', candidate+'^{tree}').decode().strip() == identity['tree']
assert git(work, 'rev-parse', candidate+'^').decode().strip() == identity['base']
paths = git(work, 'diff', '--no-renames', '--name-only', identity['base'], candidate).decode().splitlines()
assert len(paths) == 5
rows = []
for path in paths:
    raw = git(work, 'cat-file', 'blob', candidate+':'+path)
    assert raw == (packet/'files'/path).read_bytes()
    rows.append(sha(raw)+'  '+path+'\n')
manifest = ''.join(sorted(rows)).encode()
assert manifest == (packet/'manifest.sha256').read_bytes()
assert sha(manifest) == identity['manifest_sha256']
reviews = []
for name in ('review-a.md', 'review-b.md'):
    raw = (packet/'reviews'/name).read_bytes()
    text = raw.decode()
    assert candidate in text and identity['manifest_sha256'] in text
    assert re.search(r'^Verdict: CLEAN(?:\.|\n)', text, re.M)
    reviews.append(dict(path='reviews/'+name, sha256=sha(raw)))
gates = []
previous_end = ''
for slot in ('311', '314'):
    for name, args in (
        ('status-check', ['-B', '-P', '-m', 'pontius.status_generation', '--check']),
        ('status-tests', ['-B', '-P', 'tests/test_status_generation.py']),
    ):
        receipt = root/'run-records'/f'{name}-{slot}.json'
        raw = receipt.read_bytes()
        records = json.loads(raw)
        assert len(records) == 2 and all(r['exit_code'] == 0 for r in records)
        probe, result = records
        assert result['argv'] == args
        assert all(r['snapshot_head'] == candidate for r in records)
        expected_version = '3.11.15' if slot == '311' else '3.14.6'
        assert probe['stdout'].startswith(expected_version+' ')
        assert 'pontius.status_generation as m' in probe['argv'][3]
        assert probe['started_utc'] > previous_end
        previous_end = result['finished_utc']
        snapshot = Path(result['snapshot'])
        assert git(snapshot, 'rev-parse', 'HEAD').decode().strip() == candidate
        assert not git(snapshot, 'status', '--porcelain', '--untracked-files=no')
        for path in paths:
            assert (snapshot/path).read_bytes() == (packet/'files'/path).read_bytes()
        count = 0
        if name == 'status-tests':
            assert re.search(r'Ran 12 tests in [0-9.]+s', result['stderr'])
            assert result['stderr'].strip().endswith('OK')
            assert 'skipped=' not in result['stderr']
            count = 12
        save(packet/'checks'/receipt.name, raw)
        gates.append(dict(receipt='checks/'+receipt.name, sha256=sha(raw),
            interpreter=expected_version, argv=args, exit_code=0, tests=count,
            snapshot=str(snapshot)))
run_root = Path('D:/Pontius/tmp/v0a-paired-evaluation-run-001')
assert not run_root.exists()
assert git(Path('D:/Pontius'), 'rev-parse', 'HEAD').decode().strip() == identity['base']
assert not git(Path('D:/Pontius'), 'status', '--porcelain', '--untracked-files=no')
summary = dict(candidate=identity, reviews=reviews, gates=gates,
    metadata_test_executions=24, failures=0, errors=0, skips=0,
    review_verdicts='Both CLEAN; coordinator read full independent reports',
    reserved_root_absent=True, comparison_invocations=0,
    standing='Prepared for exact decision commit/push and single comparison launch approval; not adopted')
raw = (json.dumps(summary, indent=2, sort_keys=True)+'\n').encode()
save(packet/'acceptance-summary.json', raw)
disposition = f'''# Disposition: v0a-paired-closure/r001

Candidate {candidate}; manifest {identity['manifest_sha256']}.
Both independent Tier C reviews CLEAN, specification/engineering PASS, design SOUND.
Four fresh metadata gates passed, actual 3.11.15 before 3.14.6; 24 tests,
zero failures/errors/skips. Acceptance summary SHA256 {sha(raw)}.
No production source changed, comparison ran, run root was created, or decision adopted.
Ready to request exact decision commit/push and the separately named single comparison.
Packet remains local; no new packet upload is represented as complete.

Reviewer A supplied a non-normative locator correction after issuing its report:
wrapper function anchors are run_trial:208, read_completed:495, publish:503,
execute:520 and main:605. The issued report remains unchanged. Function names,
semantics, evidence and CLEAN/PASS/PASS/SOUND verdict are unaffected.

The initial unsealed ADR heading caused gen1 status generation to refuse; the
exact Decision heading correction passed gen2. Both generation receipts and
snapshots are retained. No source change or extra game/reader invocation occurred.
'''
save(packet/'disposition.md', disposition.encode())
print(json.dumps(dict(summary=str(packet/'acceptance-summary.json'), sha256=sha(raw),
    metadata_test_executions=24, reserved_root_absent=True)))
