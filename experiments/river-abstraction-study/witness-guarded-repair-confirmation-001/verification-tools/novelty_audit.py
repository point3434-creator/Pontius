"""Independent stdlib audit of new-board admission; no game evaluation or fitting."""
from collections import Counter
from hashlib import sha256
from itertools import permutations
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
plan = json.loads((HERE/'plan.json').read_bytes())


def boards_in(value):
    if type(value) is dict:
        children = value.values()
    elif type(value) is list:
        if len(value) == len(set(map(str, value))) == 5 and all(
                type(c) is int and 0 <= c < 52 for c in value):
            yield value
            return
        children = value
    else:
        return
    for child in children:
        yield from boards_in(child)


def equivalent(a, b):
    # Compare relabelings directly instead of calling the selector's canonicalizer.
    target = sorted(b)
    return any(sorted(4*(card//4)+p[card%4] for card in a) == target
               for p in permutations(range(4)))


historical = []
for name, expected in plan['historical_plans'].items():
    raw = Path(name).read_bytes()
    assert sha256(raw).hexdigest() == expected, name
    historical.extend(boards_in(json.loads(raw)))
history = sorted({tuple(sorted(b)) for b in historical})
selected = plan['boards']
assert len(selected) == 16
for i, board in enumerate(selected):
    assert len(set(board)) == 5 and all(type(c) is int and 0 <= c < 52 for c in board)
    assert all(not equivalent(board, old) for old in history), (i, 'history collision')
    assert all(not equivalent(board, old) for old in plan['excluded_boards'])
    assert all(not equivalent(board, old) for old in selected[:i]), (i, 'duplicate')
assert Counter(r['texture'] for r in plan['selection_receipt']) == {
    'unpaired-no-flush': 4, 'unpaired-flush-possible': 4,
    'one-pair': 4, 'multiple-pairs-or-trips': 4}
result = dict(passed=True, fresh_boards=16, historical_plans=len(plan['historical_plans']),
    historical_literal_boards=len(history), excluded_suit_classes=len(plan['excluded_boards']),
    direct_suit_permutations=24, project_code_executed=False,
    plan_sha256=sha256((HERE/'plan.json').read_bytes()).hexdigest())
with (HERE/'novelty-audit.json').open('x', encoding='utf-8', newline='\n') as f:
    f.write(json.dumps(result, sort_keys=True, indent=2)+'\n')
print(result)
