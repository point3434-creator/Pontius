"""Bind the four final metadata checks and independent verdict to the frozen candidate."""
import hashlib
import json
from pathlib import Path
import re

root = Path('D:/Pontius/tmp/v0a-evaluation-seal-r001')
packet = root / 'packets/r001'
identity = json.loads((packet / 'candidate.json').read_bytes())
review = packet / 'reviews/review-light.md'
review_text = review.read_text(encoding='utf-8')
assert identity['commit'] in review_text and identity['manifest_sha256'] in review_text
assert 'CLEAN' in review_text
rows = []
previous_finish = None
for slot, version in (('311', '3.11.15'), ('314', '3.14.6')):
    for name, arguments, expected_tests in (
        ('mcheck1', ['-m', 'pontius.status_generation', '--check'], 0),
        ('mtest1', ['tests/test_status_generation.py'], 12),
    ):
        receipt = root / 'run-records' / f'{name}-{slot}.json'
        records = json.loads(receipt.read_bytes())
        assert len(records) == 2
        probe, payload = records
        assert all(r['exit_code'] == 0 and r['snapshot_head'] == identity['commit']
                   for r in records)
        assert probe['stdout'].startswith(version + ' ')
        assert 'pontius.status_generation as m' in probe['argv'][3]
        assert probe['argv'][:3] == ['-B', '-P', '-c']
        assert payload['argv'] == ['-B', '-P', *arguments]
        if previous_finish is not None:
            assert probe['started_utc'] >= previous_finish
        previous_finish = payload['finished_utc']
        output = payload['stdout'] + '\n' + payload['stderr']
        if expected_tests:
            assert re.search(r'Ran 12 tests in [\d.]+s', output)
            assert re.search(r'^OK\s*$', output, re.M)
        else:
            assert 'STATUS.md is current' in output
        rows.append(dict(slot=slot, receipt=str(receipt),
            sha256=hashlib.sha256(receipt.read_bytes()).hexdigest(), tests=expected_tests,
            argv=payload['argv'], started_utc=payload['started_utc'],
            finished_utc=payload['finished_utc']))
result = dict(candidate=identity, review=str(review),
    review_sha256=hashlib.sha256(review.read_bytes()).hexdigest(),
    receipts=rows, commands=4, tests=24, failures=0, errors=0, skips=0,
    incorporation_audit_sha256=hashlib.sha256((packet / 'incorporation-audit.json').read_bytes()).hexdigest(),
    standing='Reviewed and checked metadata; decision commit and upload await exact authorization; no evaluation')
destination = packet / 'checks/metadata-acceptance-summary.json'
destination.parent.mkdir(exist_ok=True)
raw = (json.dumps(result, sort_keys=True, indent=2) + '\n').encode()
with destination.open('xb') as stream:
    assert stream.write(raw) == len(raw)
print(json.dumps(dict(path=str(destination), sha256=hashlib.sha256(raw).hexdigest(),
                     candidate=identity['commit'], tests=24, commands=4)))
