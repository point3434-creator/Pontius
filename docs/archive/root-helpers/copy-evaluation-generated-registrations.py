"""Copy only the two successful snapshot-generated governance artifacts."""
import hashlib
import json
from pathlib import Path
import sys

root = Path('D:/Pontius/tmp/v0a-evaluation-source-r001')
repo = root / 'authoring'
name = sys.argv[1]
receipt_path = root / 'run-records' / (name + '-311.json')
records = json.loads(receipt_path.read_bytes())
assert len(records) == 2 and all(r['exit_code'] == 0 for r in records)
record = records[-1]
assert record['argv'] == ['-B', '-P', 'tools/generate_test_inventory.py', '--write']
assert records[0]['stdout'].startswith('3.11.15 ')
snapshot = Path(record['snapshot'])
assert snapshot == root / 'snapshots' / (name + '-311')
paths = ('tests/test-inventory.json', 'tests/test-profiles.toml')
rows = []
for path in paths:
    raw = (snapshot / path).read_bytes()
    assert b'\r' not in raw and not raw.startswith(b'\xef\xbb\xbf') and raw.endswith(b'\n')
    rows.append(dict(path=path, sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw)))
output = root / (name + '-generated-copy.json')
assert not output.exists()
for path in paths:
    (repo / path).write_bytes((snapshot / path).read_bytes())
with output.open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(dict(receipt=str(receipt_path),
        receipt_sha256=hashlib.sha256(receipt_path.read_bytes()).hexdigest(),
        generation_snapshot=record['snapshot_head'], copied=rows), stream, indent=2)
    stream.write('\n')
print(json.dumps(dict(receipt=str(output), copied=rows)))
