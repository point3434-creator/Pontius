"""Append-only copies of coordination packets; never move retained evidence."""
import argparse
import hashlib
import json
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('batch')
p.add_argument('--whole-round')
a = p.parse_args()
assert a.batch.isalnum()
home = Path('D:/Pontius-handoffs')
source_root = Path('D:/Pontius/tmp/v0a-evaluation-source-r001')
opening_root = Path('D:/Pontius/tmp/v0a-evaluation-opening-r001')
rows = []

def save(origin, destination):
    assert origin.is_file() and not origin.is_symlink()
    raw = origin.read_bytes()
    if destination.exists():
        assert destination.read_bytes() == raw, ('published bytes differ', destination)
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open('xb') as stream:
            assert stream.write(raw) == len(raw)
    assert destination.read_bytes() == raw
    rows.append(dict(origin=str(origin), destination=str(destination), bytes=len(raw),
                     sha256=hashlib.sha256(raw).hexdigest()))

def tree(origin, destination):
    for path in sorted(origin.rglob('*')):
        assert not path.is_symlink()
        if path.is_file():
            save(path, destination / path.relative_to(origin))

for round_name in ('r001', 'r002'):
    tree(opening_root / 'packets' / round_name,
         home / 'v0a-evaluation-opening' / round_name)
for round_name in ('task1-r001', 'task1-r002', 'task2-r001', 'task2-r002'):
    tree(source_root / 'packets' / round_name,
         home / 'v0a-evaluation-source/checkpoints' / round_name)
if a.whole_round:
    assert a.whole_round.startswith('r') and a.whole_round[1:].isdigit()
    tree(source_root / 'packets' / a.whole_round,
         home / 'v0a-evaluation-source' / a.whole_round)
for task_root, task_id in ((opening_root, 'v0a-evaluation-opening'),
                           (source_root, 'v0a-evaluation-source')):
    records = task_root / 'run-records'
    if records.is_dir():
        for path in sorted(records.glob('*.json')):
            save(path, home / task_id / 'checks/iterations' / path.name)
sdd = source_root / 'authoring/.superpowers/sdd/2026-09-07-paired-local-evaluation'
save(sdd / 'progress.md', home / 'v0a-evaluation-source/ledger-snapshots' / (a.batch + '.md'))
for name in ('controller-budget-ruling-2026-09-07.md', 'task-3-report.md',
             'task-3-expected-cases.md', 'task-3-context-addendum-001.md'):
    save(sdd / name, home / 'v0a-evaluation-source/coordination' / name)
for name in ('registration-pre-edit-raw-pins.json', 'igen2-generated-copy.json',
             'census-literal-refresh-001.json', 'census-post1-literal-verification.json',
             'handoff-upload-blocked-001.md'):
    save(source_root / name, home / 'v0a-evaluation-source/coordination' / name)
mapping = home / 'v0a-evaluation-source/publications' / (a.batch + '.json')
mapping.parent.mkdir(parents=True, exist_ok=True)
with mapping.open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(dict(version='pontius-evaluation-packet-preservation-v1', files=rows,
                  standing='Coordination copies only; original snapshots/lifecycle roots remain in place'),
              stream, indent=2)
    stream.write('\n')
progress = home / 'v0a-evaluation-source/progress.md'
with progress.open('a', encoding='utf-8', newline='\n') as stream:
    if progress.stat().st_size == 0:
        stream.write('# Paired evaluation source packet ledger\n\n'
                     'Finalizer: Codex coordinator. Whole-source rounds use rNNN.\n'
                     'Named Task 1/2 checkpoints remain under checkpoints with their original\n'
                     'unaltered identities and findings; they do not reset the global FIX budget.\n'
                     'The original detailed implementation ledger remains at the source task root;\n'
                     'its byte-exact snapshots are linked here as publication records.\n\n')
    stream.write(f'- Publication {a.batch}: [copy map](publications/{a.batch}.json), '
                 f'[implementation ledger snapshot](ledger-snapshots/{a.batch}.md).\n')
index = home / 'INDEX.md'
text = index.read_text(encoding='utf-8')
if '## Paired local evaluation' not in text:
    with index.open('a', encoding='utf-8', newline='\n') as stream:
        stream.write('\n## Paired local evaluation\n\n'
            '- [Source opening r002](v0a-evaluation-opening/r002/handoff.md): '
            'adopted ADR-0508,34616938; r001 retained unchanged.\n'
            '- [Source progress](v0a-evaluation-source/progress.md): scoped checkpoints and '
            'whole-source review/acceptance; source seal and evaluation remain pending.\n')
print(json.dumps(dict(batch=a.batch, files=len(rows), mapping=str(mapping))))
