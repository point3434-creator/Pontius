"""Attach raw source and initiating-site provenance to every new census occurrence."""
import argparse
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess

p = argparse.ArgumentParser()
p.add_argument('comparison')
p.add_argument('capture')
p.add_argument('output')
a = p.parse_args()
report = json.loads(Path(a.comparison).read_bytes())
capture = json.loads(Path(a.capture).read_bytes())
capture_hash = hashlib.sha256(Path(a.capture).read_bytes()).hexdigest()
candidate = capture['source_commit']
repo = Path('D:/Pontius/tmp/v0a-evaluation-source-r001/authoring')
git = 'C:/Program Files/Git/cmd/git.exe'
new = {f'tests/test_v0a_evaluation_{s}.py' for s in ('contract', 'runner', 'boundary')}
raws, trees, lines = {}, {}, {}
for path in new:
    raw = subprocess.run([git, '--no-replace-objects', '-c', 'safe.directory=' + repo.as_posix(),
        '-C', str(repo), 'cat-file', 'blob', candidate + ':' + path],
        check=True, capture_output=True).stdout
    raws[path], trees[path], lines[path] = raw, ast.parse(raw), raw.decode().splitlines()

def source(path, line):
    assert path in new and type(line) is int and 0 < line <= len(lines[path])
    return dict(path=path, line=line, source_line=lines[path][line - 1],
                source_sha256=hashlib.sha256(raws[path]).hexdigest())

def initiating(item):
    parts = item.removeprefix('fixture:').split('::')
    path, classname = parts[:2]
    cls = next(n for n in trees[path].body if isinstance(n, ast.ClassDef) and n.name == classname)
    node = cls
    if len(parts) == 3:
        node = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == parts[2])
    return source(path, node.lineno)

edges = capture['observed']['process_rows'][3]
notes = {}
for name, collection in report['collections'].items():
    assert not collection['missing'], (name, 'old population missing')
    counts = Counter(row['row_sha256'] for row in collection['additions'])
    for added in collection['additions']:
        row = added['row']
        obj = row[0] if name == 'decoys' else row
        item = row[1] if name == 'universe' else obj.get('item_id', '')
        if name == 'decoys':
            anchor = source(obj['path'], obj['line'])
            construct = f"Literal sink spelling under AST {obj['parent']}: {obj['tokens']}"
            reason = ('This exact new-suite literal is retained by the unchanged decoy census as '
                      + row[1] + '. Its provenance is preserved; it grants no runtime permission.')
            start = None
        else:
            start = initiating(item)
            path = obj.get('relative_path', obj.get('caller_path')) if isinstance(obj, dict) else None
            line = obj.get('line') if isinstance(obj, dict) else None
            anchor = source(path, line) if path in new and line else start
            if name == 'helpers':
                construct = (f"Helper edge to {obj['callee_path']}::{obj['callee_function']}; "
                             f"depth {obj['closure_depth']}, key {obj['helper_key']}")
                reason = ('The newly registered test or lifecycle fixture reaches this exact helper '
                          'call. The unchanged analyzer retains the edge at its actual source line.')
            elif name == 'blockers':
                construct = 'Refused construct: ' + obj['reason']
                reason = ('This new initiating test/fixture exposes the displayed call to the full '
                          'census. The original analyzer refuses exact derivation with that reason; '
                          'the blocker remains counted and does not install a capability grant.')
            elif name == 'analyzed':
                construct = f"{obj['sink_kind']} {obj['qualified_name']} at closure depth {obj['closure_depth']}"
                reason = ('The unchanged analyzer inspects this source-bound sink for the new item. '
                          'All emitted rows, including repeated occurrences, remain in the census.')
            elif name == 'universe':
                construct = 'New ' + row[0] + ' membership: ' + item
                reason = ('The exact new suite registration adds this independently discovered item '
                          'to the complete current-profile design universe.')
            elif name == 'deny_all':
                construct = 'Deny-all membership: ' + item
                reason = ('The unchanged analysis emits no expanded permission for this new item; '
                          'its deny-all row preserves the complete universe partition.')
            else:
                assert name == 'expanded'
                construct = 'Derived ' + obj['capability_kind'] + ': ' + obj['capability_id']
                reason = ('This source-bound new item has the displayed finite derived row. It is '
                          'analysis output only; both installed capability scope hashes stay zero.')
        note = dict(anchor, row_sha256=added['row_sha256'], construct=construct, reason=reason,
                    identical_addition_multiplicity=counts[added['row_sha256']])
        if start:
            note['initiating_item_definition'] = start
            note['complete_closure_reference'] = dict(
                capture=str(Path(a.capture).resolve()),
                capture_sha256=capture_hash,
                collection='observed.process_rows[3]',
                indices=[i for i, edge in enumerate(edges) if edge['item_id'] == item])
            note['initiating_calls'] = [dict(source(e['caller_path'], e['line']),
                helper_key=e['helper_key'], callee_path=e['callee_path'],
                callee_function=e['callee_function']) for e in edges if
                e['item_id'] == item and e['closure_depth'] == 0 and e['caller_path'] in new]
        notes[added['key']] = note
with Path(a.output).open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(notes, stream, sort_keys=True, indent=2)
    stream.write('\n')
print(json.dumps(dict(output=a.output, occurrences=len(notes),
                     standing='Source-bound draft; coordinator and independent semantic review required')))
