"""Correct and check a retained coordination comparator; never run repository code."""
import ast
import copy
import hashlib
from pathlib import Path
import subprocess

root = Path('D:/Pontius/tmp/v0a-evaluation-source-r001')
old = root / 'compare-census-v1.py'
new = root / 'compare-census-v2.py'
before = old.read_text(encoding='utf-8')
start = before.index('    def registered_tree(raw, remove):')
end = before.index('    check(registered_tree(', start)
replacement = '''    def registered_tree(raw, remove):
        tree = ast.parse(raw)
        assignments = [n for n in tree.body if isinstance(n, ast.Assign) and
                       any(isinstance(t, ast.Name) and t.id == 'STABILIZATION_TEST_FILES'
                           for t in n.targets)]
        check(len(assignments) == 1, 'registration assignment population changed')
        if len(assignments) != 1:
            return ast.dump(tree, include_attributes=False)
        node = assignments[0]
        value = node.value
        valid = (len(node.targets) == 1 and isinstance(value, ast.Call) and
                 isinstance(value.func, ast.Name) and value.func.id == 'frozenset' and
                 not value.keywords and len(value.args) == 1 and
                 isinstance(value.args[0], ast.Set) and all(
                     isinstance(e, ast.Constant) and type(e.value) is str
                     for e in value.args[0].elts))
        check(valid, 'registration shape changed')
        if valid:
            elements = value.args[0].elts
            names = [e.value for e in elements]
            check(len(names) == len(set(names)), 'duplicate literal registration')
            check(set(names) & NEW == (NEW if remove else set()),
                  'three literal registration population differs')
            if remove:
                value.args[0].elts = [e for e in elements if e.value not in NEW]
        return ast.dump(tree, include_attributes=False)
'''
after = before[:start] + replacement + before[end:]
ast.parse(after)
names = {f'tests/test_v0a_evaluation_{s}.py' for s in ('contract', 'runner', 'boundary')}
repo = root / 'authoring'
raw = subprocess.run([
    'C:/Program Files/Git/cmd/git.exe', '--no-replace-objects',
    '-c', f'safe.directory={repo.as_posix()}', '-C', str(repo), 'cat-file', 'blob',
    'e043f81ecec3ac16128720b42c3312bb41a4ed67:tools/generate_test_inventory.py',
], capture_output=True, check=True).stdout


def function(text, issues):
    node = next(n for n in ast.walk(ast.parse(text))
                if isinstance(n, ast.FunctionDef) and n.name == 'registered_tree')
    space = {'ast': ast, 'NEW': names,
             'check': lambda condition, message: issues.append(message) if not condition else None}
    exec(compile(ast.Module(body=[node], type_ignores=[]), '<coordination-check>', 'exec'), space)
    return space['registered_tree']


issues = []
old_function = function(before, issues)
try:
    old_function(raw, True)
except AttributeError:
    assert issues == ['registration shape changed']
else:
    raise AssertionError('Original shape defect was not reproduced')
issues = []
fixed = function(after, issues)
tree = ast.parse(raw)
registration = next(n for n in tree.body if isinstance(n, ast.Assign)
                    and any(isinstance(t, ast.Name) and t.id == 'STABILIZATION_TEST_FILES'
                            for t in n.targets))
registration.value.args[0].elts.extend(ast.Constant(value=s) for s in sorted(names))
candidate = ast.unparse(tree)
expected = ast.dump(ast.parse(raw), include_attributes=False)
assert fixed(raw, False) == expected and not issues
assert fixed(candidate, True) == expected and not issues
changed = copy.deepcopy(tree)
changed.body.append(ast.Assign(targets=[ast.Name(id='UNAUTHORIZED', ctx=ast.Store())],
                               value=ast.Constant(value=True)))
assert fixed(ast.unparse(ast.fix_missing_locations(changed)), True) != expected
wrong = copy.deepcopy(tree)
reg = next(n for n in wrong.body if isinstance(n, ast.Assign)
           and any(isinstance(t, ast.Name) and t.id == 'STABILIZATION_TEST_FILES'
                   for t in n.targets))
reg.value = ast.List(elts=reg.value.args[0].elts, ctx=ast.Load())
fixed(ast.unparse(ast.fix_missing_locations(wrong)), True)
assert issues == ['registration shape changed']
with new.open('xb') as stream:
    stream.write(after.encode('utf-8'))
print('Original coordination defect reproduced; strict baseline/addition/extra-edit/shape checks PASS.')
print('No repository module, analyzer, generator, test suite or poker code executed.')
print('Retained comparator v1 SHA256:', hashlib.sha256(old.read_bytes()).hexdigest())
print('Comparator v2 SHA256:', hashlib.sha256(new.read_bytes()).hexdigest())
