"""Prepare local metadata-only snapshot/freezing adapters after source acceptance."""
import ast
import hashlib
import json
from pathlib import Path
import sys

source_root = Path('D:/Pontius/tmp/v0a-evaluation-source-r001')
round_name = sys.argv[1]
assert round_name.startswith('r') and round_name[1:].isdigit()
packet = source_root / 'packets' / round_name
summary_path = packet / 'checks/final-acceptance-summary.json'
summary = json.loads(summary_path.read_bytes())
assert all(row['commands'] == 16 and row['skips'] == 0 for row in summary['totals'].values())
assert summary['candidate'] == json.loads((packet / 'candidate.json').read_bytes())
seal_root = Path('D:/Pontius/tmp/v0a-evaluation-seal-r001')
seal_root.mkdir(exist_ok=False)
adr = 'docs/decisions/ADR-0509-source-seal-the-paired-local-evaluation-loop.md'
old_root = "'D:\\Pontius\\tmp\\v0a-evaluation-source-r001'"
new_root = "'D:\\Pontius\\tmp\\v0a-evaluation-seal-r001'"
rows = []
for old_name, new_name in (('run-source-snapshot-v2.ps1', 'run-seal-snapshot.ps1'),
                           ('freeze-source-v3.ps1', 'freeze-seal.ps1')):
    raw = (source_root / old_name).read_bytes()
    text = raw.decode().replace('\r\n', '\n')
    assert old_root in text
    text = text.replace(old_root, new_root)
    if old_name.startswith('run-'):
        old = "$work=Join-Path $taskRoot 'authoring'"
        replacement = "$work='D:\\Pontius\\tmp\\v0a-evaluation-source-r001\\authoring'"
        assert text.count(old) == 1
        text = text.replace(old, replacement)
        old = "'tests/test_inventory_and_profiles.py','.github/workflows/ci.yml')"
        assert text.count(old) == 1
        text = text.replace(old, old[:-1] + ", '" + adr + "', 'STATUS.md')")
        text = text.replace('refs/heads/snapshots/evaluation/', 'refs/heads/snapshots/evaluation-seal/')
        old = '; print(sys.version); print(sys.executable); print(pathlib.Path.cwd())"'
        assert text.count(old) == 1
        text = text.replace(old, '; import pontius.status_generation as m; assert '
            "pathlib.Path(m.__file__).resolve()==pathlib.Path('src/pontius/status_generation.py').resolve()" +
            '; print(sys.version); print(sys.executable); print(pathlib.Path.cwd()); print(m.__file__)"')
    else:
        old = "$work = Join-Path $taskRoot 'authoring'"
        assert text.count(old) == 1
        text = text.replace(old, "$work = 'D:\\Pontius\\tmp\\v0a-evaluation-source-r001\\authoring'")
        old = "'tests/test_inventory_and_profiles.py','.github/workflows/ci.yml')"
        assert text.count(old) == 1
        text = text.replace(old, old[:-1] + ", '" + adr + "', 'STATUS.md')")
        text = text.replace('v0a-evaluation-source', 'v0a-evaluation-seal')
        # The replacement above must not redirect the source authoring path.
        text = text.replace("$work = 'D:\\Pontius\\tmp\\v0a-evaluation-seal-r001\\authoring'",
                            "$work = 'D:\\Pontius\\tmp\\v0a-evaluation-source-r001\\authoring'")
    destination = seal_root / new_name
    destination.write_bytes(text.encode())
    rows.append(dict(original=str(source_root / old_name),
                     original_sha256=hashlib.sha256(raw).hexdigest(),
                     adapter=str(destination), adapter_sha256=hashlib.sha256(text.encode()).hexdigest()))
with (seal_root / 'source-acceptance-binding.json').open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(dict(source_candidate=summary['candidate'], summary=str(summary_path),
        summary_sha256=hashlib.sha256(summary_path.read_bytes()).hexdigest(), adapters=rows,
        metadata_paths=[adr, 'STATUS.md'],
        standing='Metadata preparation only; no decision commit, source seal or evaluation'), stream, indent=2)
    stream.write('\n')
print(json.dumps(dict(root=str(seal_root), source_candidate=summary['candidate']['commit'], adapters=rows)))
