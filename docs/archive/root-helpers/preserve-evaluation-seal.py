"""Create or verify exact local coordination copies, without Git or network."""
import hashlib
import json
from pathlib import Path
import sys

batch = sys.argv[1]
assert batch.isalnum()
root = Path('D:/Pontius/tmp/v0a-evaluation-seal-r001')
home = Path('D:/Pontius-handoffs/v0a-evaluation-seal')
rows = []


def copy(source, destination):
    assert source.is_file() and not source.is_symlink()
    raw = source.read_bytes()
    if destination.exists():
        assert destination.read_bytes() == raw
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open('xb') as stream:
            assert stream.write(raw) == len(raw)
    assert destination.read_bytes() == raw
    rows.append(dict(source=str(source), destination=str(destination), bytes=len(raw),
                     sha256=hashlib.sha256(raw).hexdigest()))


for path in sorted((root / 'packets/r001').rglob('*')):
    if path.is_file():
        copy(path, home / 'r001' / path.relative_to(root / 'packets/r001'))
for path in sorted((root / 'run-records').glob('*.json')):
    copy(path, home / 'checks' / path.name)
for name in ('source-acceptance-binding.json', 'status-generation-copy.json',
             'metadata-preparation-refusal-001.json'):
    copy(root / name, home / 'coordination' / name)
mapping = home / 'publications' / (batch + '.json')
mapping.parent.mkdir(parents=True, exist_ok=True)
with mapping.open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(dict(files=rows, standing='Local coordination copies only; no upload'), stream, indent=2)
    stream.write('\n')
with (home / 'progress.md').open('a', encoding='utf-8', newline='\n') as stream:
    stream.write(f'- Local preservation {batch}: publications/{batch}.json.\n')
index = home.parent / 'INDEX.md'
if 'v0a-evaluation-seal/r001/handoff.md' not in index.read_text(encoding='utf-8'):
    with index.open('a', encoding='utf-8', newline='\n') as stream:
        stream.write('\n- [Paired evaluation source-seal metadata r001]'
                     '(v0a-evaluation-seal/r001/handoff.md): exact source incorporation; '
                     'decision commit and remote upload pending.\n')
print(json.dumps(dict(batch=batch, files=len(rows), mapping=str(mapping))))
