"""Reconstruct every scaled LP and bind its saved vectors without optimizing."""
from diagnose import d, OLD
import scaling as s
from pathlib import Path
from types import SimpleNamespace
import json

HERE = Path(__file__).resolve().parent
OUT = HERE/'run'
reports = []
for j in range(4):
    saved = d.read(OUT/f'case-{j:03d}.json')
    game, _, meta = d.build(d.read(d.b.PRIOR/f'input-{j:03d}.json'))
    assert meta == saved['inputs']
    kernel = d.Kernel(game)
    d.m.bounds = kernel.bounds
    calls = []
    def replay(objective, **kw):
        old = saved['calls'][len(calls)]
        cost, scaled, policy = s.transform(objective, kw)
        matrix = scaled['A_ub'].copy()
        matrix[:,policy] /= s.SCALE
        assert d.np.array_equal(matrix, kw['A_ub'])
        assert d.np.array_equal(scaled['b_ub']/s.SCALE, kw['b_ub'])
        cost[policy] /= s.SCALE
        assert d.np.array_equal(cost, objective)
        raw = d.np.array(old['raw_scaled_x'])
        raw[~policy] /= s.SCALE
        assert d.np.array_equal(raw, old['original_units_x'])
        assert old['options'] == kw['options']
        original = d.np.abs(matrix)
        nonzero = d.np.abs(scaled['A_ub'][scaled['A_ub'] != 0])
        calls.append(dict(original_coefficients_below_cutoff=int(((original > 0)&(original <= 1e-9)).sum()),
            scaled_coefficients_below_cutoff=int((nonzero <= 1e-9).sum()),
            min_scaled_nonzero=float(nonzero.min()),
            matrix_entries_verified=matrix.size, value_unit_roundtrip=True))
        return SimpleNamespace(success=True,x=raw,nit=old['iterations'])
    d.c.opt.linprog = replay
    profile = d.m.pair(game,[list(range(1081))]*2)
    assert all(profile[k] == saved['profile'][k] for k in ('x','y','bounds'))
    assert len(calls) == 2
    reports.append(dict(case=j,calls=calls,passed=True))
result = dict(passed=True,new_lp_calls=0,cases=reports)
with (OUT/'scaling-audit.json').open('x',encoding='utf-8',newline='\n') as f:
    json.dump(result,f,indent=2,sort_keys=True)
    f.write('\n')
print(json.dumps(result,indent=2))
