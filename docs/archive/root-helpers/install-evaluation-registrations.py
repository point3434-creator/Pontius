"""Install only the bounded prospective source registrations after retained RED."""
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path('D:/Pontius/tmp/v0a-evaluation-source-r001')
REPO = ROOT / 'authoring'
receipt = json.loads((ROOT / 'run-records/bregred1-311.json').read_bytes())
assert receipt[0]['exit_code'] == 0 and receipt[1]['exit_code'] == 1
assert 'Exact evaluation registration policy is absent' in receipt[1]['stderr']
pins = json.loads((ROOT / 'registration-pre-edit-raw-pins.json').read_bytes())
for row in pins['rows']:
    assert hashlib.sha256((REPO / row['path']).read_bytes()).hexdigest() == row['restored_sha256']
proposal = Path(__file__).with_name('evaluation-policy-proposal.txt').read_text()
ast.parse(proposal)
assert max(map(len, proposal.splitlines())) <= 100

def change(path, edits):
    target = REPO / path
    raw = target.read_bytes()
    text = raw.decode()
    for before, after in edits:
        assert text.count(before) == 1, (path, before)
        text = text.replace(before, after)
    assert '\r' not in text
    target.write_bytes(text.encode())

change('tools/check_stabilization_boundaries.py', [
    ('        "tools/v0a_seeded_deals.py",\n',
     '        "tools/v0a_seeded_deals.py",\n        "tools/v0a_evaluation.py",\n'
     '        "tools/v0a_evaluation_contract.py",\n'),
    ('def _read_regular_source(', proposal + 'def _read_regular_source('),
    ('    enforce_seeded_deals_import_policy(tool_sources)\n',
     '    enforce_seeded_deals_import_policy(tool_sources)\n'
     '    enforce_evaluation_import_policy(tool_sources)\n'),
])
for path in ('tools/generate_test_inventory.py', 'tests/test_inventory_and_profiles.py'):
    text = (REPO / path).read_text()
    old = '"tests/test_v0a_contract_faults.py", "tests/test_v0a_event_adapter.py",'
    line = next(line for line in text.splitlines() if old in line)
    indent = line[:len(line) - len(line.lstrip())]
    replacement = ('"tests/test_v0a_contract_faults.py",\n' + indent +
        '"tests/test_v0a_evaluation_boundary.py", "tests/test_v0a_evaluation_contract.py",\n' +
        indent + '"tests/test_v0a_evaluation_runner.py", "tests/test_v0a_event_adapter.py",')
    change(path, [(old, replacement)])
steps = ''.join('      - name: Paired evaluation ' + name + ' suite\n'
               '        if: ${{ !cancelled() }}\n'
               '        run: .venv\\Scripts\\python.exe -B -P tests\\test_v0a_evaluation_' +
               name + '.py\n\n' for name in ('contract', 'runner', 'boundary'))
change('.github/workflows/ci.yml', [('      - name: v0a trace suite\n',
                                    steps + '      - name: v0a trace suite\n')])
print('Installed the four manual registrations; generated artifacts and census remain pending.')
