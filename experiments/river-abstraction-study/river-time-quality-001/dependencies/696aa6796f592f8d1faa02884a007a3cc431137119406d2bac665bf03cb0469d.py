"""Fresh-board, replicated-pool pilot using the frozen witness grouping method."""
from __future__ import annotations

from collections import Counter
from fractions import Fraction as Q
from hashlib import sha256
from itertools import combinations, permutations
import json
from statistics import stdev

from .river import RiverHoldem
from .river_abstraction_study import (DEVELOPMENT_BOARDS, HOLDOUT_BOARDS, PayoffGame,
                                      representations)
from .river_group_optimality import interval, require, solve_groups
from .river_witness_groups import METHODS, propose, result_record, verify_record as verify_candidate

SELECTION_SEED = 'river-witness-pilot-001'
TEXTURES = ('unpaired-no-flush', 'unpaired-flush-possible',
            'one-pair', 'multiple-pairs-or-trips')


def canonical_json(value):
    return json.dumps(value, sort_keys=True, allow_nan=False)


def checked_board(board):
    require(len(board) == 5 and all(type(c) is int and 0 <= c < 52 for c in board)
            and len(set(board)) == 5, 'five distinct integer cards required')
    return tuple(sorted(board))


def canonical_board(board):
    board = checked_board(board)
    return min(tuple(sorted(4*(c//4)+p[c%4] for c in board)) for p in permutations(range(4)))


def texture(board):
    board = checked_board(board)
    ranks = sorted(Counter(c//4 for c in board).values(), reverse=True)
    if ranks == [2, 1, 1, 1]:
        return TEXTURES[2]
    if ranks != [1]*5:
        return TEXTURES[3]
    return TEXTURES[int(max(Counter(c%4 for c in board).values()) >= 3)]


def select_boards():
    """First two per texture from a predeclared hash-shuffled deck sequence."""
    excluded = {canonical_board(b) for b in (*DEVELOPMENT_BOARDS, *HOLDOUT_BOARDS)}
    selected = {name: [] for name in TEXTURES}
    for attempt in range(10000):
        def order(card):
            return sha256(f'{SELECTION_SEED}|board|{attempt}|{card}'.encode()).digest(), card
        board = tuple(sorted(sorted(range(52), key=order)[:5]))
        key, name = canonical_board(board), texture(board)
        if key not in excluded and len(selected[name]) < 2:
            selected[name].append(board)
            excluded.add(key)
        if all(len(rows) == 2 for rows in selected.values()):
            return tuple(board for name in TEXTURES for board in selected[name])
    raise ValueError('board selection exhausted its declared attempt budget')


def hand_pool(board, pool, player, count):
    board = checked_board(board)
    require(type(pool) is int and pool in (0, 1, 2) and type(player) is int and player in (0, 1)
            and type(count) is int and 2 <= count <= 96, 'invalid hand-pool request')
    legal = combinations([c for c in range(52) if c not in board], 2)
    prefix = ','.join(map(str, board))
    def order(hand):
        text = f'{SELECTION_SEED}|pool|{prefix}|{pool}|{player}|{hand[0]},{hand[1]}'
        return sha256(text.encode()).digest(), hand
    return tuple(sorted(legal, key=order)[:count])


def case_grid(boards):
    return [dict(id=f'b{index:02d}-p{pool}-{regime}', board_index=index,
                 board=list(checked_board(board)), texture=texture(board), pool=pool, regime=regime)
            for index, board in enumerate(boards) for pool in range(3)
            for regime in ('uniform', 'polarized')]


def build_inputs(case, count, equities):
    require(case['regime'] in ('uniform', 'polarized'), 'unknown range regime')
    ranges = []
    for player in (0, 1):
        hands = hand_pool(case['board'], case['pool'], player, count)
        ranges.append({h: 4 if case['regime'] == 'polarized' and
                       (equities[h] <= .2 or equities[h] >= .8) else 1 for h in hands})
    game = RiverHoldem.from_independent_ranges(board=case['board'], pot=10, stacks=(20,20),
        bet_size=5, player0_weights=ranges[0], player1_weights=ranges[1])
    matrix = PayoffGame.from_river(game)
    require(matrix.joint.shape == (count, count), 'a selected hand has no compatible opponent')
    groups = representations(matrix, equities)
    inputs = dict(board=list(game.board), pot=10, bet=5, stacks=[20,20],
        provenance_digest=game.provenance_digest, accepted_joint_deals=len(game.deals),
        hands=[[list(h) for h in pool] for pool in matrix.hands], joint=matrix.joint.tolist(),
        ranges=[[[list(h),w] for h,w in sorted(r.items())] for r in ranges],
        groups={m:[g.tolist() for g in pair] for m,pair in groups.items()})
    return matrix, groups, inputs


def solve_record(case, count, equities):
    matrix, groups, inputs = build_inputs(case, count, equities)
    bank = dict(case=case['id'], methods=[dict(method=m, saved=[],
                solution=solve_groups(matrix, groups[m])) for m in METHODS])
    proposal = propose(matrix, groups, bank)
    candidate = result_record(matrix, groups, bank, solve_groups(matrix, proposal['groups']))
    return dict(case=case, inputs=inputs, bank=bank, candidate=candidate)


def verify_record(case, count, equities, record):
    require(set(record) == {'case','inputs','bank','candidate'} and
            canonical_json(record['case']) == canonical_json(case), 'result case mismatch')
    matrix, groups, inputs = build_inputs(case, count, equities)
    require(canonical_json(record['inputs']) == canonical_json(inputs),
            'input reconstruction mismatch')
    bank = record['bank']
    require(bank['case'] == case['id'] and [r['method'] for r in bank['methods']] == list(METHODS)
            and all(set(r) == {'method','saved','solution'} and r['saved'] == []
                    for r in bank['methods']), 'control bank mismatch')
    verify_candidate(matrix, groups, bank, record['candidate'])
    return record


def mean_interval(values):
    return interval(*(sum(Q(v[key]) for v in values)/len(values)
                      for key in ('lower_exact','upper_exact')))


def midpoint(value):
    return float((Q(value['lower_exact'])+Q(value['upper_exact']))/2)


def descriptive_sd(values):
    return stdev(values) if len(values) > 1 else 0.0


def statistics(rows):
    floors = {m:mean_interval([next(r for r in row['bank']['methods'] if r['method'] == m)
                              ['solution']['minimum_exploitability'] for row in rows])
              for m in METHODS}
    floors['witness_advantage'] = mean_interval([
        row['candidate']['solution']['minimum_exploitability'] for row in rows])
    differences = {}
    for name in METHODS:
        values = [row['candidate']['comparisons'][name] for row in rows]
        differences[name] = dict(**mean_interval(values), case_counts={
            label:sum(v['classification'] == label for v in values)
            for label in ('lower','higher','overlapping')},
            worst_case=max(rows, key=lambda r: Q(
                r['candidate']['comparisons'][name]['upper_exact']))
                       ['case']['id'])
    return dict(mean_floors=floors, comparisons=differences)


def summarize(cases, rows):
    require(len({c['id'] for c in cases}) == len(cases) and
            canonical_json([r['case'] for r in rows]) == canonical_json(cases),
            'missing, duplicated or reordered result case')
    indices = sorted({c['board_index'] for c in cases})
    boards = []
    for index in indices:
        selected = [r for r in rows if r['case']['board_index'] == index]
        pools = [statistics([r for r in selected if r['case']['pool'] == p])
                 for p in sorted({r['case']['pool'] for r in selected})]
        boards.append(dict(board_index=index, board=selected[0]['case']['board'],
            texture=selected[0]['case']['texture'], **statistics(selected), pool_means=pools,
            pool_sd_chips={m:descriptive_sd([midpoint(p['comparisons'][m]) for p in pools])
                           for m in METHODS}))
    overall = statistics(rows)
    # The complete balanced design makes this equal to the case-weighted mean.
    for name in METHODS:
        expected = mean_interval([b['comparisons'][name] for b in boards])
        actual = overall['comparisons'][name]
        require(all(expected[k] == actual[k] for k in expected), 'unequal board weighting')
    return dict(complete=True, case_count=len(rows), board_units=len(boards),
        lp_calls_planned=10*len(rows), primary_control='range_equity',
        secondary_control='range_response', overall=overall, boards=boards,
        between_board_sd_chips={m:descriptive_sd([midpoint(b['comparisons'][m]) for b in boards])
                                for m in METHODS},
        by_regime={regime:statistics([r for r in rows if r['case']['regime'] == regime])
                   for regime in sorted({c['regime'] for c in cases})},
        by_texture={name:statistics([r for r in rows if r['case']['texture'] == name])
                    for name in sorted({c['texture'] for c in cases})},
        leave_one_board_out=[dict(omitted=index, **statistics([
            r for r in rows if r['case']['board_index'] != index])) for index in indices]
            if len(indices) > 1 else [],
        cases=rows, interpretation='Oracle-assisted, fixed stratified pilot; '
        'eight board-level units '
        'in the full run, not 48 independent boards. SDs are descriptive; no confidence interval '
        'or all-board, six-max, BB/100 or equal-compute claim. Witness creation cost is included.')
