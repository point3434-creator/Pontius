"""Post-gate diagnostic; original failing receipt and tolerance remain unchanged."""
import importlib.util
import sys
from pathlib import Path
from time import perf_counter
sys.path[:0] = ['D:/Pontius/.venv/Lib/site-packages', str(Path(__file__).parent)]
import numpy as np
import cupy as cp
import experiment as e
from solver import Solver
from gpu_adapter import Solver as GPU

e.bindings()
spec, arrays = e.game('raise')
cpu = Solver(spec['nodes'], arrays, e.CONFIG)
gpu = GPU(spec['nodes'], {k:cp.asarray(a) for k,a in arrays.items()}, e.CONFIG)
same = GPU(spec['nodes'], gpu.arrays, e.CONFIG)
rows=[]
for iteration in range(1,33):
    same.iteration = cpu.iteration
    for attr in ('policy','regret','accumulator'):
        setattr(same,attr,{k:cp.asarray(a) for k,a in getattr(cpu,attr).items()})
    cpu.step()
    gpu.step()
    same.step()
    row=dict(iteration=iteration,free={},reset={})
    for tag,model in [('free',gpu),('reset',same)]:
        for attr in ('policy','regret','accumulator'):
            worst=None
            for k,a in getattr(cpu,attr).items():
                b=cp.asnumpy(getattr(model,attr)[k])
                delta=np.abs(a-b)
                ij=np.unravel_index(delta.argmax(),delta.shape)
                value=float(delta[ij])
                if worst is None or value>worst['max_abs']:
                    worst=dict(node=k,hand=int(ij[0]),action=int(ij[1]),max_abs=value,
                               cpu=float(a[ij]),gpu=float(b[ij]),
                               cpu_regret_row=cpu.regret[k][ij[0]].tolist(),
                               gpu_regret_row=cp.asnumpy(model.regret[k][ij[0]]).tolist())
            row[tag][attr]=worst
    rows.append(row)
e.write(e.HERE/'diagnostic.json',dict(rows=rows,original_gate='FAILED; not relabelled'))
print('free', {a:max(r['free'][a]['max_abs'] for r in rows)
               for a in ('policy','regret','accumulator')})
print('reset', {a:max(r['reset'][a]['max_abs'] for r in rows)
                for a in ('policy','regret','accumulator')})
