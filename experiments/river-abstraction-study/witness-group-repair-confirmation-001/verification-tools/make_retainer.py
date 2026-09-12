"""Adapt the previous independent retention audit; never mutate its original bytes."""
from pathlib import Path

here = Path(__file__).resolve().parent
source = Path('D:/Pontius/tmp/witness-group-repair-author/retain.py').read_text()


def replace(old, new):
    global source
    assert old in source, old
    source = source.replace(old, new)


replace('witness-group-repair-001', 'witness-group-repair-confirmation-001')
replace('Witness-directed group repair 001', 'Fresh-board witness group repair confirmation 001')
replace("== 128", "== 256")
replace('== 1920000', '== 3840000')
replace('range(32)', 'range(64)')
replace("'The original control gets five times as many solver updates, not equal wall',",
        "'The original control gets five times as many solver updates, not equal wall',")
replace("'Prior witness generation and model fitting costs are outside those timings.', '',",
        "'Baseline witness generation is separately timed in every new case. Prior',\n"
        "    'model fitting is excluded; there is no fitting in this confirmation.', '',")
replace("{value['changed_seats']}/32", "{value['changed_seats']}/64")
replace('32 observed cases: eight boards, one pool, two regimes, two bet sizes.',
        '64 observed cases: sixteen fresh boards, one pool, two regimes, two bet sizes.')
replace('10 author checks passed. 64 new LP calls and 64 trajectories completed.',
        '16 author checks passed. 256 new LP calls and 128 trajectories completed.')
replace("'128 asymmetric certificates and 128 saved profiles verified; 1,920,000',\n"
        "    'updates replayed with verifier LP calls disabled. The retained 10,000-update',\n"
        "    'hard policy reproduces exactly in every case.',",
        "'256 asymmetric certificates and 256 saved profiles verified; 3,840,000',\n"
        "    'updates replayed with verifier LP calls disabled. All new inputs and group',\n"
        "    'labels were rebuilt. Four historical cases reproduced before the freeze.',")
replace('Witness-directed group repair\\n', 'Fresh-board witness group repair confirmation\\n')
replace('[Witness-group-repair-001]', '[Witness-group-repair-confirmation-001]')
replace('tests one\\n', 'confirms one\\n')
replace('fixed-capacity split/merge per seat against unchanged grouping trained longer.',
        'unchanged fixed-capacity repair on sixteen new boards; every outcome is retained.')

# Additional descriptive robustness information from retained per-case results.
replace("primary = summary['panels']['5']['overall']", """
for bet, value in analysis.items():
    panel = summary['panels'][bet]
    selected = [r for r in rows if r['entry']['bet'] == int(bet)]
    def delta(row):
        return (Q(row['records']['repaired'][1]['exact_exploitability'])-
                Q(row['records']['control'][0]['exact_exploitability']))
    worst = max(selected, key=delta)
    value['worst_case'] = dict(case=worst['entry']['case'], actual_delta_exact=str(delta(worst)))
    value['actual_case_directions'] = dict(Counter(direction(delta(r)) for r in selected))
    value['leave_one_board_out_all_improve'] = all(
        Q(v['actual_delta_exact']) < 0 for v in panel['leave_one_board_out'].values())
    value['texture_actual_deltas'] = {k: float(Q(v['actual_delta_exact']))
                                     for k, v in panel['textures'].items()}
    value['regime_actual_deltas'] = {k: float(Q(v['actual_delta_exact']))
                                    for k, v in panel['regimes'].items()}
primary = summary['panels']['5']['overall']""")
replace("lines += ['', '## Verification and scope', '',", """
lines += ['', '## Freshness and worst regressions', '',
    'All 16 boards were frozen before evaluation. Four per texture, excluding 52',
    'historical board classes up to suit isomorphism. This is the unchanged',
    'one-step algorithm, including a fresh per-game offline witness; it is not a',
    'claim that the learned model alone generalizes to repaired group labels.', '',
    '| Bet | Worst case | Actual exploitability increase | LOBO means all improve |',
    '|---|---|---:|---|']
for bet, value in analysis.items():
    worst = value['worst_case']
    lines.append(f"| {bet} | {worst['case']['id']} | "
        f"{float(Q(worst['actual_delta_exact'])):+.9f} | "
        f"{value['leave_one_board_out_all_improve']} |")
lines += ['', '## Verification and scope', '',""")

target = here/'retain.py'
with target.open('x', encoding='utf-8', newline='\n') as stream:
    stream.write(source)
