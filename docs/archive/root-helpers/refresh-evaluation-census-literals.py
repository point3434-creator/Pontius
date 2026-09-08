"""Refresh only existing census assertion values from explained raw analyzer rows."""
import argparse
import ast
from collections import Counter
import copy
import difflib
import hashlib
import json
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('capture')
p.add_argument('comparison')
p.add_argument('receipt')
a = p.parse_args()
doc = json.loads(Path(a.capture).read_bytes())
comparison = json.loads(Path(a.comparison).read_bytes())
assert doc['population'] == comparison['population'] == 'test'
assert comparison['mechanical_checks_pass'] and not comparison['issues']
assert comparison['inputs'][2]['sha256'] == hashlib.sha256(Path(a.capture).read_bytes()).hexdigest()
path = Path('D:/Pontius/tmp/v0a-evaluation-source-r001/authoring/tests/test_inventory_and_profiles.py')
raw = path.read_bytes()
derivation = next(r for r in doc['review']['receipt']['derivation_sources']
                  if r['relative_path'] == 'tests/test_inventory_and_profiles.py')
assert derivation['canonical_lf_sha256'] == hashlib.sha256(raw).hexdigest()
source = raw.decode()
tree = ast.parse(raw)
method = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and
          n.name == 'test_working_discovery_binds_every_entry_and_introduced_id']
assert len(method) == 1
lines = source.splitlines(keepends=True)
offsets = [0]
for line in lines:
    offsets.append(offsets[-1] + len(line))
edits = []

def substitute(node, text, purpose):
    start = offsets[node.lineno - 1] + node.col_offset
    end = offsets[node.end_lineno - 1] + node.end_col_offset
    if source[start:end] != text:
        edits.append((start, end, text, purpose, source[start:end]))

def scalar(node, value, purpose):
    assert type(ast.literal_eval(node)) is type(value)
    text = json.dumps(value) if isinstance(value, str) else str(value)
    substitute(node, text, purpose)

def dictionary(node, value, purpose):
    assert isinstance(node, ast.Dict)
    old = ast.literal_eval(node)
    assert set(old) <= set(value), ('old census key removed', purpose)
    for key, item in zip(node.keys, node.values):
        name = ast.literal_eval(key)
        if isinstance(item, ast.Dict):
            dictionary(item, value[name], purpose + '.' + name)
        else:
            scalar(item, value[name], purpose + '.' + name)
    extra = sorted(set(value) - set(old))
    if extra:
        # Insert before the original closing brace; retain every old key in order.
        start = offsets[node.end_lineno - 1]
        indent = ' ' * (node.col_offset + 4)
        text = ''.join(indent + json.dumps(k) + ': ' + json.dumps(value[k]) + ',\n' for k in extra)
        edits.append((start, start, text, purpose + ': added counted reasons', ''))

review = doc['review']
matched = []
for call in ast.walk(method[0]):
    if not (isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute) and
            isinstance(call.func.value, ast.Name) and call.func.value.id == 'self' and
            call.func.attr == 'assertEqual' and len(call.args) == 2):
        continue
    observed, expected = call.args
    expr = ast.unparse(observed)
    if expr == "len(review['receipt']['expanded_rows'])":
        scalar(expected, len(review['receipt']['expanded_rows']), expr)
    elif expr == "review['spec_capabilities_sha256']":
        scalar(expected, review['spec_capabilities_sha256'], expr)
    elif expr == "review['analysis_census']":
        dictionary(expected, review['analysis_census'], expr)
    elif expr == 'len(blockers)':
        scalar(expected, len(review['unresolved_dynamic_blockers']), expr)
    elif expr == "Counter((row['reason'] for row in blockers))":
        assert isinstance(expected, ast.Call) and ast.unparse(expected.func) == 'Counter'
        dictionary(expected.args[0], dict(Counter(
            r['reason'] for r in review['unresolved_dynamic_blockers'])), expr)
    elif isinstance(observed, ast.ListComp) and isinstance(expected, ast.List) and (
            len(observed.generators) == 1 and ast.unparse(observed.generators[0].iter) == 'blockers'):
        conditions = observed.generators[0].ifs
        assert len(conditions) == 1 and isinstance(conditions[0], ast.Compare)
        condition = conditions[0]
        assert ast.unparse(condition.left) == "row['reason']" and isinstance(condition.ops[0], ast.Eq)
        reason = ast.literal_eval(condition.comparators[0])
        assert reason in ('dynamic sensitive call result is unresolved',
                          'unregistered CuPy call is unresolved',
                          'deferred generator consumption is dynamically unresolved')
        values = [(r['relative_path'], r['line']) for r in review['unresolved_dynamic_blockers']
                  if r['reason'] == reason]
        current = ast.literal_eval(expected)
        if len(current) == len(values) and all(x[0] == y[0] for x, y in zip(current, values)):
            for node, value in zip(expected.elts, values):
                scalar(node.elts[1], value[1], reason + ': source line')
        else:
            indent = ' ' * (expected.col_offset + 4)
            text = '[\n' + ''.join(indent + '(' + json.dumps(name) + ', ' + str(line) + '),\n'
                                     for name, line in values)
            text += ' ' * expected.col_offset + ']'
            substitute(expected, text, reason + ': complete ordered location list')
    else:
        continue
    matched.append(expr)
assert len(matched) == 8, matched
ordered = sorted(edits)
assert all(left[1] <= right[0] for left, right in zip(ordered, ordered[1:]))
result = source
for start, end, text, _, _ in reversed(ordered):
    result = result[:start] + text + result[end:]
# Added literal reason keys can move later source locations. Derive the two
# location-sensitive digest literals from complete captured rows and exact equal
# source-line blocks. Fresh post-edit captures must independently confirm them.
line_map = {}
for i, j, count in difflib.SequenceMatcher(
        None, source.splitlines(), result.splitlines(), autojunk=False).get_matching_blocks():
    line_map.update({i + n + 1: j + n + 1 for n in range(count)})
analyzed = copy.deepcopy(doc['observed']['process_rows'][2])
decoys = [copy.deepcopy(row[0]) for row in doc['observed']['decoy_rows_with_provenance']]
for rows, field in ((analyzed, 'relative_path'), (decoys, 'path')):
    for row in rows:
        if row[field] == 'tests/test_inventory_and_profiles.py' and row['line']:
            assert row['line'] in line_map, ('modified analyzed/decoy source anchor', row)
            row['line'] = line_map[row['line']]

def semantic(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True,
                      allow_nan=False).encode()

predictions = {
    'analyzed_sites_sha256': hashlib.sha256(semantic(analyzed)).hexdigest(),
    'string_sink_decoy_sha256': hashlib.sha256(semantic(decoys) + b'\n').hexdigest(),
}
for field, value in predictions.items():
    before = json.dumps(review['analysis_census'][field])
    assert result.count(before) == 1
    result = result.replace(before, json.dumps(value))
ast.parse(result)
assert result.count('self.assertEqual(') == source.count('self.assertEqual(')
assert result.count('self.assert') == source.count('self.assert')
record = dict(version='pontius-evaluation-mechanical-census-literals-v1',
              capture=str(Path(a.capture).resolve()),
              capture_sha256=hashlib.sha256(Path(a.capture).read_bytes()).hexdigest(),
              comparison=str(Path(a.comparison).resolve()),
              before_sha256=hashlib.sha256(raw).hexdigest(),
              after_sha256=hashlib.sha256(result.encode()).hexdigest(),
              changes=[dict(purpose=purpose, before=before, after=text, offset=start)
                       for start, end, text, purpose, before in ordered],
              source_position_digest_predictions=predictions,
              prediction_basis='Complete captured rows remapped only through exact equal source lines',
              matched_assertions=matched, standing='Requires fresh complete post-edit census verification')
with Path(a.receipt).open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(record, stream, indent=2)
    stream.write('\n')
path.write_bytes(result.encode())
print(json.dumps(dict(receipt=a.receipt, changes=len(edits), before_lines=len(raw.splitlines()),
                     after_lines=len(result.splitlines()))))
