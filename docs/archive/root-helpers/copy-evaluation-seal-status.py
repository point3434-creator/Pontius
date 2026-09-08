"""Copy the successful retained generation after diagnosing a coordinator-only guard error."""
import hashlib
import json
from pathlib import Path

root = Path('D:/Pontius/tmp/v0a-evaluation-seal-r001')
receipt = root / 'run-records/mgen1-311.json'
records = json.loads(receipt.read_bytes())
assert len(records) == 2 and all(r['exit_code'] == 0 for r in records)
source = Path(records[-1]['snapshot']) / 'STATUS.md'
destination = Path('D:/Pontius/tmp/v0a-evaluation-source-r001/authoring/STATUS.md')
raw = source.read_bytes()
assert raw.startswith(b'# Project Status') and not raw.startswith(b'\xef\xbb\xbf')
normalized = raw.replace(b'\r\n', b'\n')
assert b'\r' not in normalized
previous = destination.read_bytes()
record_path = root / 'status-generation-copy.json'
assert not record_path.exists()
diagnostic = dict(
    failed_coordinator_script=str(Path(__file__).with_name('generate-evaluation-seal-status.ps1')),
    failed_script_sha256=hashlib.sha256(Path(__file__).with_name('generate-evaluation-seal-status.ps1').read_bytes()).hexdigest(),
    failure='Generated status encoding; after generator passed, before copying STATUS',
    cause='Culture-sensitive .NET StartsWith treats U+FEFF as ignorable and returns true for plain text',
    minimal_reproduction={'plain_text_culture_starts_with_bom': True,
                          'plain_text_ordinal_starts_with_bom': False},
    actual_bytes={'first_12': list(raw[:12]), 'crlf_count': raw.count(b'\r\n'),
                  'utf8_bom': raw.startswith(b'\xef\xbb\xbf'),
                  'normalized_cr_count': normalized.count(b'\r')},
    disposition='Preserve successful generation and original failed helper; copy its exact bytes '
                'with only CRLF-to-LF normalization using explicit byte predicates. No payload rerun '
                'or production/source change.')
with (root / 'metadata-preparation-refusal-001.json').open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(diagnostic, stream, indent=2)
    stream.write('\n')
destination.write_bytes(normalized)
assert destination.read_bytes() == normalized
record = dict(receipt=str(receipt), receipt_sha256=hashlib.sha256(receipt.read_bytes()).hexdigest(),
    snapshot=records[-1]['snapshot'], snapshot_head=records[-1]['snapshot_head'], source=str(source),
    generated_raw_sha256=hashlib.sha256(raw).hexdigest(), destination=str(destination),
    previous_sha256=hashlib.sha256(previous).hexdigest(), copied_sha256=hashlib.sha256(normalized).hexdigest(),
    transformation='Only generated Windows CRLF to governance LF; no content edit',
    retained_coordinator_refusal=str(root / 'metadata-preparation-refusal-001.json'),
    standing='Generated metadata only; exact-candidate final checks remain pending')
with record_path.open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(record, stream, indent=2)
    stream.write('\n')
print(json.dumps(record))
