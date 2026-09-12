"""Synthetic capacity observation; no captured research outcomes or case selection."""
from support import *
from exact_kernel import Kernel
from inputs import build
from time import perf_counter
import json

board = [0, 5, 10, 23, 48]
n = 1081
record = dict(board=board, hands=[list(h) for h in ComboIndex(board).combos],
              ranges=[dict(effective=[1/n]*n)]*2)
times = {}
t = perf_counter()
game, groups, details = build(record)
times['build'] = perf_counter()-t
t = perf_counter()
kernel = Kernel(game)
times['exact_setup'] = perf_counter()-t
m.bounds = kernel.bounds
t = perf_counter()
solution = m.solve(game, groups)
times['two_certificate_pairs'] = perf_counter()-t
t = perf_counter()
trainer = m.Trainer(game, groups)
for _ in range(1000):
    trainer.step()
times['both_roles_setup_1000'] = perf_counter()-t
t = perf_counter()
values = kernel.values(solution['seat0']['y'])
proposal = r.exchange(groups[0], values)
times['proposal'] = perf_counter()-t
t = perf_counter()
r.accept(game, groups, *trainer.average(), [proposal['groups'], groups[1]],
         trainer.average()[0])
times['gate'] = perf_counter()-t
result = dict(passed=True, synthetic=True, research_outcomes=0, backend=evaluator.BACKEND,
              dimensions=list(game.check.shape), seconds=times)
with (Path(__file__).parent/'capacity.json').open('x') as f:
    json.dump(result, f, sort_keys=True, indent=2)
print(result)
