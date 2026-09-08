"""Read-only check of all existing census expectation values against raw captures."""
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

root = Path('D:/Pontius/tmp/v0a-evaluation-source-r001')
stage = sys.argv[1]
assert stage.isalnum()
path = root / 'authoring/tests/test_inventory_and_profiles.py'
raw = path.read_bytes()
method = next(n for n in ast.walk(ast.parse(raw)) if isinstance(n, ast.FunctionDef)
              and n.name == 'test_working_discovery_binds_every_entry_and_introduced_id')
checks = []
for slot in ('311', '314'):
    capture_path = root / f'process-temp/c-{stage}-t-{slot}/census-test.json'
    doc = json.loads(capture_path.read_bytes())
    derivation = next(r for r in doc['review']['receipt']['derivation_sources']
                      if r['relative_path'] == 'tests/test_inventory_and_profiles.py')
    assert derivation['canonical_lf_sha256'] == hashlib.sha256(raw).hexdigest()
    review, verified = doc['review'], []
    for node in ast.walk(method):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and
                ast.unparse(node.func) == 'self.assertEqual' and len(node.args) == 2):
            continue
        observed, expected = node.args
        expr = ast.unparse(observed)
        values = {
            "len(review['receipt']['expanded_rows'])": len(review['receipt']['expanded_rows']),
            "review['spec_capabilities_sha256']": review['spec_capabilities_sha256'],
            "review['analysis_census']": review['analysis_census'],
            'len(blockers)': len(review['unresolved_dynamic_blockers']),
        }
        if expr in values:
            actual = values[expr]
        elif expr == "Counter((row['reason'] for row in blockers))":
            actual = dict(Counter(r['reason'] for r in review['unresolved_dynamic_blockers']))
            assert isinstance(expected, ast.Call) and ast.unparse(expected.func) == 'Counter'
            expected = expected.args[0]
        elif isinstance(observed, ast.ListComp) and isinstance(expected, ast.List) and (
                len(observed.generators) == 1 and ast.unparse(observed.generators[0].iter) == 'blockers'):
            reason = ast.literal_eval(observed.generators[0].ifs[0].comparators[0])
            actual = [(r['relative_path'], r['line']) for r in review['unresolved_dynamic_blockers']
                      if r['reason'] == reason]
        else:
            continue
        assert ast.literal_eval(expected) == actual, (slot, expr)
        verified.append(expr)
    assert len(verified) == 8
    checks.append(dict(slot=slot, capture=str(capture_path), assertions=verified,
                       capture_sha256=hashlib.sha256(capture_path.read_bytes()).hexdigest()))
out = root / f'census-{stage}-literal-verification.json'
with out.open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(dict(source_sha256=hashlib.sha256(raw).hexdigest(), checks=checks,
        standing='All eight literal expectation blocks equal actual complete captures; not a test run'),
        stream, indent=2)
    stream.write('\n')
print(json.dumps(dict(output=str(out), verified_blocks=16, source_sha256=hashlib.sha256(raw).hexdigest())))
