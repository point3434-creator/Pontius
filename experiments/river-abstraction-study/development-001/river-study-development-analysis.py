"""Verify saved development policies against original RiverState terminal returns."""
from hashlib import sha256
import json
from math import fsum, isfinite
from pathlib import Path
import sys

ROOT = Path('D:/Pontius-worktrees/eval-runner-consolidation')
OUT = Path('D:/Pontius/tmp/river-study-development-20260910-01')
sys.path.insert(0, str(ROOT / 'src'))
from pontius.river import BET, CALL, CHECK, FOLD, RiverHoldem, RiverState

METHODS = ('exact', 'uniform_equity_200', 'range_equity', 'range_response')
STEPS = (100, 1000, 10000)
all_records = []
max_error = 0.0
case_info = []
for board in (0, 1):
    for regime in ('uniform', 'polarized'):
        label = f'd{board}-{regime}'
        folder = OUT / label
        manifest = json.loads((folder / 'manifest.json').read_text())
        assert set(manifest) == {'started.json', 'inputs.json', 'result.json'}
        for name, digest in manifest.items():
            assert sha256((folder / name).read_bytes()).hexdigest() == digest
        started = json.loads((folder / 'started.json').read_text())
        for name, digest in started['source_sha256'].items():
            assert sha256((ROOT / name).read_bytes()).hexdigest() == digest
        inputs = json.loads((folder / 'inputs.json').read_text())
        result = json.loads((folder / 'result.json').read_text())
        assert result['complete'] is True and started['iterations'] == 10000
        assert started['board'] == inputs['board'] and started['regime'] == regime
        weights = [{tuple(hand): weight for hand, weight in rows} for rows in inputs['ranges']]
        assert [len(w) for w in weights] == [96, 96]
        game = RiverHoldem.from_independent_ranges(
            board=inputs['board'], pot=inputs['pot'], stacks=inputs['stacks'],
            bet_size=inputs['bet'], player0_weights=weights[0], player1_weights=weights[1])
        assert game.provenance_digest == inputs['provenance_digest']
        assert len(game.deals) == result['accepted_joint_deals']
        hands = [[tuple(h) for h in pool] for pool in inputs['hands']]
        assert hands == [sorted(game.marginal_distribution(p)) for p in (0, 1)]
        indices = [{h: i for i, h in enumerate(pool)} for pool in hands]
        terminals = []
        for deal, mass in game.deals:
            state = RiverState(game, deal)
            bet = state.apply_action(BET)
            i, j = indices[0][deal.player0], indices[1][deal.player1]
            assert mass == inputs['joint'][i][j]
            terminals.append((i, j, mass, state.apply_action(CHECK).returns()[0],
                              bet.apply_action(FOLD).returns()[0], bet.apply_action(CALL).returns()[0]))
        grid = {(r['method'], r['iteration']) for r in result['records']}
        assert grid == {(m, n) for m in METHODS for n in STEPS}
        assert len(result['records']) == 12
        for record in result['records']:
            x, y = record['hand_bet'], record['hand_call']
            assert len(x) == len(y) == 96
            assert all(isfinite(p) and 0 <= p <= 1 for p in x + y)
            groups = inputs['groups'][record['method']]
            assert x == [record['group_bet'][g] for g in groups[0]]
            assert y == [record['group_call'][g] for g in groups[1]]
            n0, n1 = record['occupied_groups']
            assert [set(g) for g in groups] == [set(range(n0)), set(range(n1))]
            row_check, row_bet = [[] for _ in x], [[] for _ in x]
            col_fold, col_call, values, check_value = [[] for _ in y], [[] for _ in y], [], []
            for i, j, mass, check, fold, call in terminals:
                betting = (1-y[j]) * fold + y[j] * call
                row_check[i].append(mass * check)
                row_bet[i].append(mass * betting)
                col_fold[j].append(mass * x[i] * fold)
                col_call[j].append(mass * x[i] * call)
                check_value.append(mass * (1-x[i]) * check)
                values.append(mass * ((1-x[i]) * check + x[i] * betting))
            value = fsum(values)
            upper = fsum(max(fsum(c), fsum(b)) for c, b in zip(row_check, row_bet))
            lower = fsum(check_value) + fsum(min(fsum(f), fsum(c))
                                             for f, c in zip(col_fold, col_call))
            recomputed = {'value': value, 'upper': upper, 'lower': lower,
                          'deviation0': upper-value, 'deviation1': value-lower,
                          'exploitability': (upper-lower)/2}
            for name, expected in recomputed.items():
                error = abs(expected - record['full_game'][name])
                max_error = max(error, max_error)
                assert error < 1e-11, (label, record['method'], name, error)
            record = dict(record, case=label,
                          full_game_fraction_of_pot={k: v / game.pot
                                                    for k, v in record['full_game'].items()},
                          restricted_game_fraction_of_pot={k: v / game.pot
                                                          for k, v in record['restricted_game'].items()})
            all_records.append(record)
        case_info.append({'case': label, 'deals': len(game.deals),
                          'groups': {r['method']: r['occupied_groups']
                                     for r in result['records'] if r['iteration'] == 10000}})
means = {str(n): {m: fsum(r['full_game']['exploitability'] for r in all_records
                         if r['iteration'] == n and r['method'] == m) / 4
                 for m in METHODS} for n in STEPS}
summary = {'kind': 'verified local development trial; no holdout or formal campaign',
           'verified_records': len(all_records), 'max_original_state_error_chips': max_error,
           'cases': case_info, 'equal_weight_mean_exploitability_chips': means,
           'records': all_records}
with (OUT / 'analysis.json').open('x', encoding='utf-8', newline='\n') as stream:
    stream.write(json.dumps(summary, indent=2, sort_keys=True, allow_nan=False) + '\n')
print(json.dumps({k: v for k, v in summary.items() if k != 'records'}, indent=2))
print(json.dumps([{'case': r['case'], 'method': r['method'],
                   'full': r['full_game']['exploitability'],
                   'restricted': r['restricted_game']['exploitability']}
                 for r in all_records if r['iteration'] == 10000], indent=2))
