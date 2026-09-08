"""Prepare a concrete upload inventory locally; never stage, commit or transmit."""
import hashlib
import json
from pathlib import Path

home = Path('D:/Pontius-handoffs')
out = Path(__file__).parent
tasks = ['v0a-evaluation-opening', 'v0a-evaluation-source', 'v0a-evaluation-seal']
assert (home / tasks[-1] / 'r001/checks/metadata-acceptance-summary.json').is_file()
attributes = home / '.gitattributes'
original_attributes = attributes.read_bytes()
proposed_attributes = original_attributes
if not proposed_attributes.endswith(b'\n'):
    proposed_attributes += b'\n'
for task in tasks:
    rule = f'{task}/** -text'.encode()
    if rule not in proposed_attributes.splitlines():
        proposed_attributes += rule + b'\n'
rows = []
for task in tasks:
    for path in sorted((home / task).rglob('*')):
        assert not path.is_symlink()
        if path.is_file():
            raw = path.read_bytes()
            rows.append(dict(path=path.relative_to(home).as_posix(), bytes=len(raw),
                             sha256=hashlib.sha256(raw).hexdigest()))
raw_index = (home / 'INDEX.md').read_bytes()
rows.append(dict(path='INDEX.md', bytes=len(raw_index),
                 sha256=hashlib.sha256(raw_index).hexdigest()))
rows.append(dict(path='.gitattributes', bytes=len(proposed_attributes),
                 sha256=hashlib.sha256(proposed_attributes).hexdigest(),
                 transformation='Append only three scoped -text rules if absent',
                 original_sha256=hashlib.sha256(original_attributes).hexdigest()))
proposal = dict(destination='https://github.com/point3434-creator/Pontius-handoffs.git',
    branch='main', files=sorted(rows, key=lambda row: row['path']),
    file_count=len(rows), total_bytes=sum(row['bytes'] for row in rows),
    standing='Proposed coordination upload only; automatic review rejected earlier upload; '
             'no staging, commit or network performed; explicit user authorization pending')
for name, raw in (
    ('evaluation-handoff-upload-manifest.json',
     (json.dumps(proposal, sort_keys=True, indent=2) + '\n').encode()),
    ('evaluation-handoff-proposed.gitattributes', proposed_attributes),
):
    with (out / name).open('xb') as stream:
        assert stream.write(raw) == len(raw)
print(json.dumps(dict(file_count=proposal['file_count'], total_bytes=proposal['total_bytes'],
                     manifest=str(out / 'evaluation-handoff-upload-manifest.json'))))
