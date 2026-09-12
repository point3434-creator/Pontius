import hashlib, importlib.util, itertools, json, math, pathlib, sys
from collections import Counter
from fractions import Fraction as Q
from unittest.mock import patch
root = pathlib.Path('D:/Pontius-worktrees/eval-runner-consolidation')
sys.path.insert(0, str(root/'src'))
from pontius import river_witness_pilot as p
from pontius.river_abstraction_study import DEVELOPMENT_BOARDS, HOLDOUT_BOARDS
import numpy, scipy
assert sys.version_info[:3] == (3,14,6)
assert (numpy.__version__, scipy.__version__) == ('2.5.2','1.18.0')
seed = 'river-witness-pilot-001'
def canonical(board):
    return min(tuple(sorted((c//4)*4+s[c%4] for c in board)) for s in itertools.permutations(range(4)))
def category(board):
    r = sorted(Counter(c//4 for c in board).values())
    if r == [1,1,1,1,1]: return int(max(Counter(c%4 for c in board).values()) >= 3)
    return 2 if r == [1,1,1,2] else 3
bins = [[],[],[],[]]
seen = {canonical(b) for b in DEVELOPMENT_BOARDS+HOLDOUT_BOARDS}
for attempt in range(10000):
    deck = sorted(range(52), key=lambda c:(hashlib.sha256(f'{seed}|board|{attempt}|{c}'.encode('utf-8')).hexdigest(),c))
    board = tuple(sorted(deck[:5])); k = category(board); equiv = canonical(board)
    if equiv not in seen and len(bins[k]) < 2:
        bins[k].append(board); seen.add(equiv)
    if all(len(b) == 2 for b in bins): break
expected_boards = tuple(itertools.chain.from_iterable(bins))
assert expected_boards == p.select_boards()
plan = json.loads((root/'docs/research/river-witness-pilot-r001/plan.json').read_bytes())
assert plan['cases'] == p.case_grid(expected_boards)
for board in expected_boards:
    legal = list(itertools.combinations(sorted(set(range(52))-set(board)),2))
    assert len(legal) == 1081
    for pool in range(3):
        for seat in range(2):
            prefix = seed+'|pool|'+','.join(map(str,board))+f'|{pool}|{seat}|'
            expected = tuple(sorted(legal,key=lambda h:(hashlib.sha256((prefix+f'{h[0]},{h[1]}').encode()).hexdigest(),h))[:96])
            assert expected == p.hand_pool(board,pool,seat,96)
cases = plan['cases']; rows=[]
for c in cases:
    # Different regime, pool and board effects make accidental omission visible.
    x = Q(c['board_index']-4) + Q(c['pool'],10) + (Q(3,10) if c['regime']=='polarized' else 0)
    comparisons={m:dict(**p.interval(x-Q(1,100),x+Q(1,100)),classification='lower' if x+Q(1,100)<0 else 'higher' if x-Q(1,100)>0 else 'overlapping') for m in p.METHODS}
    rows.append(dict(case=c,bank=dict(methods=[dict(method=m,solution=dict(minimum_exploitability=p.interval(Q(10),Q(10)))) for m in p.METHODS]),candidate=dict(solution=dict(minimum_exploitability=p.interval(10+x-Q(1,100),10+x+Q(1,100))),comparisons=comparisons)))
summary=p.summarize(cases,rows)
mean=Q(-1,4)
assert Q(summary['overall']['comparisons']['range_equity']['lower_exact'])==mean-Q(1,100)
assert Q(summary['overall']['mean_floors']['witness_advantage']['upper_exact'])==10+mean+Q(1,100)
assert abs(summary['between_board_sd_chips']['range_equity']-math.sqrt(6))<1e-12
for b in summary['boards']:
    assert abs(b['pool_sd_chips']['range_equity']-.1)<1e-12
    bm=Q(b['board_index']-4)+Q(1,4)
    assert Q(b['comparisons']['range_equity']['upper_exact'])==bm+Q(1,100)
for omit in summary['leave_one_board_out']:
    expected=(8*mean-(Q(omit['omitted']-4)+Q(1,4)))/7
    assert Q(omit['comparisons']['range_equity']['lower_exact'])==expected-Q(1,100)
assert summary['overall']['comparisons']['exact']['worst_case']=='b07-p2-polarized'
for regime,effect in [('uniform',Q(0)),('polarized',Q(3,10))]:
    assert Q(summary['by_regime'][regime]['comparisons']['exact']['lower_exact'])==Q(-2,5)+effect-Q(1,100)
for name,indices in zip(p.TEXTURES,[(0,1),(2,3),(4,5),(6,7)]):
    assert Q(summary['by_texture'][name]['comparisons']['exact']['lower_exact'])==Q(sum(indices),2)-4+Q(1,4)-Q(1,100)
for bad in (rows[:-1], rows[::-1], [rows[0]]+rows[:-1]):
    try: p.summarize(cases,bad)
    except ValueError: pass
    else: raise AssertionError('bad panel accepted')
packet=root/'docs/research/river-witness-pilot-r001'
for name in ['.gitattributes','docs/research/README.md']:
    assert (root/name).read_bytes().startswith((packet/'predecessor-metadata'/name).read_bytes()), name
old=json.loads((packet/'predecessor-metadata/tests/cases.json').read_bytes())
new=json.loads((root/'tests/cases.json').read_bytes())
print(json.dumps(dict(python=sys.version, numpy=numpy.__version__,scipy=scipy.__version__,selection_last_attempt=attempt,boards=expected_boards,hand_pool_checks=48,synthetic_aggregation='passed',metadata_json_types=[type(old).__name__,type(new).__name__]),indent=2))
