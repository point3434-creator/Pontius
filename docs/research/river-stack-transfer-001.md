# Actual river stack transfer 001

Same four retained public ranges and group labels as blueprint-range-transfer-001.
Actual pots, stack-capped legal sizes and seat-ordered odd-chip ties.

## Domain census

| Case | Pot | Remaining live stack | SPR | Requested sizes map to | Result |
|---|---:|---:|---:|---|---|
| 0 | 279 | 76 | 0.2724 | [76, 76] | not_applicable_single_size |
| 1 | 29 | 186 | 6.4138 | [14, 29] | evaluated |
| 2 | 368 | 44 | 0.1196 | [44, 44] | not_applicable_single_size |
| 3 | 318 | 45 | 0.1415 | [45, 45] | not_applicable_single_size |

Three cases have only one distinct all-in size. The frozen size-choice repair is
inapplicable there. No duplicate action labels, substituted bets, or replacement cases.
These are structural outcomes, not missing runs or evaluated zero-gain observations.
There is no four-case pooled exploitability or broad applicability-rate claim.

## One eligible comparison

| Policy | Normalized exploitability | Actual-chip exploitability |
|---|---:|---:|
| initial | 0.015486020 | 0.044909458 |
| repair | 0.015148523 | 0.043930716 |
| continuation | 0.015473702 | 0.044873737 |

Repair relative improvement over continuation: 2.101%.
Repair gate accepted: True.
Continuation gate accepted: True.
Lower is better. Normalized values use payoff scaling 10/pot; actual-chip values undo it.
This is restricted-game exploitability, not BB/100 or measured six-max win rate.

Original grouping floor interval: [0.015404118935748914, 0.015404118935749589]
Proposed grouping floor interval: [0.015065607248800031, 0.015065607248800737]

## Procedure and cost

The frozen predecessor learner, proposal, exact gate, and full-combo verifier are reused.
Both incumbent roles receive 50000 updates. Caller then stays fixed. Repair retrains only
the bettor for 50000 updates. Continuation reconstructs the incumbent learner and receives
additional 250-update blocks until its measured work covers repair work, with the same
predeclared cap. Witness/proposal and setup count; gates are reported separately.
Continuation stopped at 114500 total bettor updates.
Repair work 2.852524s; gate 0.191215s.
Continuation work 2.855904s; gate 0.092433s.

One timing observation, repair first. These times are not a stable speed benchmark.

## Scope and interpretation

The three collapsed-size cases include case 3, responsible for most of the preceding
normalized-game improvement. That earlier gain cannot be assumed to survive their
actual stacks: the mechanism needs two distinct bet sizes, which those states lack.
Only case 1 is eligible here. Its outcome alone cannot establish generalization.
This does not imply single-size river states need no solving or no grouping improvement.

The retained public ranges remain dominated by early-checkpoint postflop fallbacks.
Raw/effective weights and their floor are unchanged. Folded-player cards are not jointly
marginalized. All 1081 board-legal combos and collision-compatible deals remain represented.
The restricted tree omits caller betting after a check, reraises and other legal sizes.
An actual-pot payoff adapter does not turn this into a full engine-state solution.

## Verification and retention

Four adapter tests, sixty engine settlements covering wins/ties/losses and check/fold/call.
The engine rounds a half-pot bet of 14.5 to 14. Odd pots give the lower seat the odd chip;
ties therefore retain a centered +/-0.5 payoff, rather than silently rounding to zero.
Fresh replay: 214500 updates; 5842805 coefficients checked; three certificate pairs; two gates.
No new verifier LP solves. Previous source, group and range identities verified.
Worker plus verifier: 41.683s; exit 0.
Python 3.14.6, one BLAS thread, no tracing, 1800s timeout per phase, no hard RSS cap.
All 33 prior milestones preserved. No production edits, commit or push.

Plan SHA-256: c1165c814901e49a7a424fac7acf8d71681b3204666bbd20c6089f8f9a4623c7

Results manifest SHA-256: de662a63c56681ac71fa8b2265cd7ddcc0fdc6bbf6ff91eb3ca2bf15fd08fd26
