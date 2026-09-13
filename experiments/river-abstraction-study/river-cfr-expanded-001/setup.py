"""Create two bounded experiment cells from the preceding verified runner."""
from pathlib import Path
import shutil
import hashlib
import json

HERE = Path(__file__).resolve().parent
PRIOR = HERE.parent/'river-cfr-comparison-002'
template = (PRIOR/'experiment.py').read_text(encoding='utf-8')
for variant in ('checkback', 'raise'):
    dest = HERE/variant
    dest.mkdir()
    for name in ('solver.py','test_solver.py','launch.py'):
        shutil.copyfile(PRIOR/name, dest/name)
    shutil.copyfile(HERE/'design.md', dest/'design.md')
    text = template.replace('input-000.json','input-001.json').replace(
        "t.public_tree(record, 'baseline')",f"t.public_tree(record, '{variant}')").replace(
        'river-tree-expansion-001/run/000-baseline.json',
        'river-tree-expansion-001/author/plan.json').replace(
        "read(reference)['certificate']", 'read(reference)').replace(
        "name='river-cfr-comparison-002'",f"name='river-cfr-expanded-001-{variant}'").replace(
        "User: Ok let\\'s run the next", "User: Let\\'s test it").replace(
        "case=0, variant='baseline'",f"case=1, variant='{variant}'")
    text = text.replace("    paths = {Path(getattr(mod, '__file__', '')).resolve()",
        "    arms = [a for a in arms if a['name'] in "
        "('cfr_g4', 'dcfr_paper', 'pdcfr_matched', 'dcfr_code')]\n"
        "    paths = {Path(getattr(mod, '__file__', '')).resolve()")
    old = """    assert max(t.Q(cert['lower']),t.Q(reference['lower'])) <= min(
        t.Q(cert['upper']),t.Q(reference['upper']))"""
    new = """    frozen = next(j for j in reference['jobs']
                  if j['case'] == 1 and j['variant'] == plan['variant'])
    assert spec['nodes'] == frozen['nodes'] and spec['sizes'] == frozen['sequences']"""
    assert text.count(old) == 1
    text = text.replace(old, new).replace('retained_reference_overlap=True',
                                           'retained_tree_identity=True')
    text = text.replace('workers=18, certificates=6', 'workers=12, certificates=4')
    with (dest/'experiment.py').open('x',encoding='utf-8',newline='\n') as f:
        f.write(text)
    for name in ('solver.py','test_solver.py','launch.py'):
        assert (dest/name).read_bytes() == (PRIOR/name).read_bytes()
print('Two runners prepared; solver, tests and bootstrap unchanged.')
