"""Read-only extraction of pinned baseline equity functions; no bucket-cache load."""
import ast
from hashlib import sha256
import importlib.util
import itertools
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path('D:/Pontius-worktrees/eval-runner-consolidation')
sys.path.insert(0, str(ROOT / 'src'))
from pontius.river_abstraction_study import DEVELOPMENT_BOARDS, uniform_equities

assert sys.version_info[:3] == (3, 14, 6)
base = Path('D:/Projects/pluribus-lite/pluribus_lite')
expected = {
    'abstraction.py': '91ae39e94d8f1e2f908bcc3be2690d6e7a9114e4c1143330c290fe7c463a5518',
    'evaluator.py': 'de8f618eca9d316320ca2d06fb16a7eb9b02b00e973644c3530fcbfd6c9ca0b6',
}
for name, digest in expected.items():
    assert sha256((base / name).read_bytes()).hexdigest() == digest
spec = importlib.util.spec_from_file_location('saved_baseline_evaluator', base / 'evaluator.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
tree = ast.parse((base / 'abstraction.py').read_text(encoding='utf-8'))
functions = {'_river_table', 'river_equity'}
constants = {'_PAIR_POS', '_TOUCH_POS', '_RIVER_TABLES', 'RIVER_TABLE_CAP'}
nodes = [node for node in tree.body
         if (isinstance(node, ast.FunctionDef) and node.name in functions)
         or (isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id in constants
                                                 for t in node.targets))]
assert len(nodes) == 6
namespace = {'np': np, 'itertools': itertools, 'hand_rank': module.hand_rank}
exec(compile(ast.Module(body=nodes, type_ignores=[]), 'pinned-baseline-extraction', 'exec'), namespace)
ours = uniform_equities(DEVELOPMENT_BOARDS[0])
differences = []
for hand, equity in ours.items():
    reference = namespace['river_equity'](hand, DEVELOPMENT_BOARDS[0])
    if equity.hex() != reference.hex() or min(int(equity * 200), 199) != min(int(reference * 200), 199):
        differences.append(list(hand))
result = {'python': sys.version, 'baseline_sources': expected, 'backend': module.BACKEND,
          'board': list(DEVELOPMENT_BOARDS[0]), 'hands': len(ours),
          'equity_and_bucket_mismatches': differences,
          'scope': 'One development board; exact hex float and 200-bin identities.',
          'script_sha256': sha256(Path(__file__).read_bytes()).hexdigest()}
path = Path('D:/Pontius/tmp/river-study-author/baseline-check.json')
with path.open('x', encoding='utf-8', newline='\n') as stream:
    stream.write(json.dumps(result, indent=2, sort_keys=True) + '\n')
print(json.dumps(result))
assert not differences
