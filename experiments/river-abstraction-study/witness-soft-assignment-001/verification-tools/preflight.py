"""Synthetic cost observation and static hygiene; never scores a research cell."""
from environment import np, scipy, PayoffGame, anchored_clusters
import ast
from pathlib import Path
import sys
from time import perf_counter
import experiment as e
import soft

root = Path(__file__).parent
issues = []
for path in sorted(root.glob('*.py')):
    raw = path.read_bytes()
    ast.parse(raw)
    for n, line in enumerate(raw.decode().splitlines(), 1):
        if len(line) > 100 or line != line.rstrip():
            issues.append(dict(file=path.name, line=n, columns=len(line)))
if issues:
    print(issues)
    raise SystemExit(1)

rng = np.random.default_rng(9261)
joint = rng.integers(0, 4, (96, 96)).astype(float)
joint /= joint.sum()
sign = rng.integers(-1, 2, (96, 96))
matrix = PayoffGame(joint, joint*sign*5, joint*5, joint*sign*10, None, 'synthetic-96')
weights = []
for seat in (0, 1):
    features = rng.random((96, 4))
    mass = joint.sum(axis=1-seat)
    labels = anchored_clusters(features, mass, 16)
    weights.append(soft.assignments(features, mass, labels)[1])
start = perf_counter()
result = soft.solve(matrix, weights)
lp_seconds = perf_counter()-start
start = perf_counter()
learner = soft.RegretBR(matrix, weights)
for _ in range(10000):
    learner.step()
learner_seconds = perf_counter()-start
start = perf_counter()
soft.verify(matrix, weights, result)
e.score(matrix, weights, learner.average())
verification_seconds = perf_counter()-start
e.write(root/'preflight.json', dict(passed=True, scored_research_panel=False,
    synthetic_shape=[96, 96], capacity=16, python=sys.version,
    numpy=np.__version__, scipy=scipy.__version__,
    lp_and_exact_certification_seconds=lp_seconds,
    learner_setup_and_10000_updates_seconds=learner_seconds,
    certificate_and_one_profile_verification_seconds=verification_seconds,
    meaning='One synthetic cost observation, not an execution-time guarantee.',
    tests=14, source_hygiene='AST valid; at most 100 columns; no trailing whitespace'))
print(e.read(root/'preflight.json'))
