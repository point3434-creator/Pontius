"""Post-run, lossless tabular view of retained policy probabilities; no solving."""
import experiment as e
import csv
import io
from pluribus_lite.cards import cards_str

out = e.Path('D:/Pontius-training/river-abstraction-study')/e.NAME
assert e.read(out/'receipt.json')['complete']
exports = []
profiles = []
for j in range(4):
    row = e.read(out/f'case-{j:03d}.json')
    record = e.read(e.d.b.PRIOR/f'input-{j:03d}.json')
    game, groups, meta = e.d.build(record)
    calls = row['full']['calls']
    assert len(calls) == 2 and all(v['success'] for v in calls)
    bets = len(game.fold)
    x = e.d.np.clip(e.d.np.array(calls[0]['x'][:1081*(bets+1)]).reshape(1081, bets+1),
                   0, 1).tolist()
    y = e.d.np.clip(e.d.np.array(calls[1]['x'][:1081*bets]).reshape(bets, 1081), 0, 1).tolist()
    kernel = e.d.Kernel(game)
    low, high = kernel.bounds(game, x, y, [list(range(1081))]*2)
    full = dict(x=x, y=y, bounds=list(map(str, (low, high))))
    passed = high-low <= e.Q('1e-8')
    assert passed == (row['full']['status'] == 'certified')
    if passed:
        assert all(row['full']['solution'][k] == v for k, v in full.items())
    else:
        assert str(float(high-low)) == row['full']['error']
    # Literal Fraction subgames check the reconstructed profile independently.
    for start in (0, 237, 811):
        ii = [(start+17*k) % 1081 for k in range(9)]
        jj = [(start+31*k+7) % 1081 for k in range(11)]
        sub = e.d.m.Game(game.check[e.d.np.ix_(ii, jj)], game.fold[:, ii][:, :, jj],
                         game.call[:, ii][:, :, jj])
        xs, ys = [x[k] for k in ii], [[r[k] for k in jj] for r in y]
        gs = [list(range(9)), list(range(11))]
        assert e.d.Kernel(sub).bounds(sub, xs, ys, gs) == e.d.literal(sub, xs, ys, gs)
    first = e.read(e.Path('D:/Pontius-training/river-abstraction-study/full-combo-direct-001')/
                   f'case-{j:03d}.json')
    same = all(a['x'] == b['x'] for a, b in zip(calls, first['full']['calls']))
    profiles.append(dict(case=j, full_profile=full, exploitability_exact=str((high-low)/2),
        exploitability=float((high-low)/2), meets_frozen_gap_threshold=passed,
        raw_lp_solutions_identical_to_first_attempt=same,
        source_sha256=e.digest(out/f'case-{j:03d}.json'), new_lp_calls=0))
    xx, yy = e.d.m.policies(game, full['x'], full['y'])
    x, y = e.d.m.expand(groups, row['compressed']['x'], row['compressed']['y'])
    cx, cy = e.d.m.policies(game, x, y)
    _, joint, _, _ = e.d.b.population(record)
    marginals = [joint.sum(axis=1), joint.sum(axis=0)]
    data = []
    for i, hand in enumerate(record['hands']):
        item = dict(board=cards_str(record['board']), hand=cards_str(hand),
            meets_frozen_gap_threshold=int(passed),
            bettor_seat=record['role_seats'][0], caller_seat=record['role_seats'][1],
            bettor_range_before_collision=record['ranges'][0]['effective'][i],
            caller_range_before_collision=record['ranges'][1]['effective'][i],
            bettor_joint_marginal=float(marginals[0][i]),
            caller_joint_marginal=float(marginals[1][i]),
            bettor_group=groups[0][i], caller_group=groups[1][i],
            full_check=float(xx[i][0]), compressed_check=float(cx[i][0]))
        for s, size in enumerate(meta['menu']['distinct_sizes']):
            item[f'full_bet_{size}'] = float(xx[i][s+1])
            item[f'compressed_bet_{size}'] = float(cx[i][s+1])
            item[f'full_call_facing_{size}'] = float(yy[s][i])
            item[f'compressed_call_facing_{size}'] = float(cy[s][i])
        data.append(item)
    path = out/f'hand-detail-{j:03d}.csv'
    buffer = io.StringIO(newline='')
    writer = csv.DictWriter(buffer, fieldnames=list(data[0]), lineterminator='\n')
    writer.writeheader()
    writer.writerows(data)
    # A previous interrupted export contains case 0 without the new status column.
    # Preserve it as-is and publish all current tables with an explicit version suffix.
    path = out/f'hand-detail-{j:03d}-v2.csv'
    with path.open('x', encoding='utf-8', newline='') as f:
        f.write(buffer.getvalue())
    with path.open(newline='', encoding='utf-8') as f:
        replay = list(csv.DictReader(f))
    assert len(replay) == 1081
    for old, new in zip(data, replay):
        for key, value in old.items():
            assert (float(new[key]) == value if isinstance(value, (int, float)) else
                    new[key] == value)
    exports.append(dict(case=j, rows=1081, filename=path.name, sha256=e.digest(path)))
e.write(out/'hand-detail-export.json', dict(files=exports,
    purpose='Post-run view of retained policies; no new solve or strategy selection',
    probabilities='Bettor rows normalized exactly as in the certificate, then rendered binary64',
    caller='Call probabilities conditional on facing the named bet; fold is one minus call',
    limitation='Responses at unreachable branches can differ without changing exploitability'))
e.write(out/'full-profile-audit.json', dict(passed=True, profiles=profiles,
    new_lp_calls=0, literal_subgame_checks=12, threshold_unchanged='1e-8 gap',
    purpose='Post-run exact measurement of all returned strategies, including strict refusals'))
print('Four 1081-row policy tables exported and round-trip verified')
