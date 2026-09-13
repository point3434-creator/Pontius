"""Validate tree/config identity before any retained expanded solve."""
from pathlib import Path
import json
import hashlib

HERE = Path(__file__).resolve().parent
PRIOR = HERE.parent/'river-cfr-comparison-001'


def read(p):
    return json.loads(p.read_text(encoding='utf-8'))


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


prior = read(PRIOR/'plan.json')
rows = []
for variant in ('checkback','raise'):
    cell = HERE/variant
    plan, spec, frozen = (read(cell/n) for n in ('plan.json','game.json','reference.json'))
    job = next(j for j in frozen['jobs'] if j['case']==1 and j['variant']==variant)
    assert spec['nodes'] == job['nodes'] and spec['sizes'] == job['sequences']
    assert read(cell/'input.json') == read(PRIOR/'input.json')
    assert plan['arms'] == [a for a in prior['arms'] if a['name'] in
                           ('cfr_g4','dcfr_paper','pdcfr_matched','dcfr_code')]
    for field in ('iterations','checkpoints','repeats','order','average',
                  'case_timeout_seconds','private_limit_mib','numpy'):
        assert plan[field] == prior[field], field
    for name in ('solver.py','test_solver.py','launch.py'):
        assert digest(cell/name) == digest(PRIOR/name), name
    for name, expected in plan['pins'].items():
        assert digest(Path(name)) == expected, name
    rows.append(dict(variant=variant, plan_sha256=digest(cell/'plan.json'),
                     tree_identity=True, configurations_fixed=True,
                     payoff_mib=plan['payoff_bytes']/1024**2,
                     nodes=len(spec['nodes']), terminals=job['terminals']))
result = dict(cells=rows, maximum_training_workers=24, maximum_audit_workers=8,
              clarification='Legacy comparison prose says last three controls. '
              'The actual arms array and design specify four arms: three matched plus dcfr_code. '
              'No other arms will execute; all four use gamma=4.')
with (HERE/'preflight.json').open('x', encoding='utf-8', newline='\n') as f:
    json.dump(result, f, indent=2, sort_keys=True)
    f.write('\n')
print(json.dumps(result))
