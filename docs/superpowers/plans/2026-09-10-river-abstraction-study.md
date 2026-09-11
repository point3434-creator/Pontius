# River Abstraction Study Implementation Plan

> Execute inline with superpowers:executing-plans. User cost policy: one opposing
> review after the candidate; no parallel reviewer fan-out.

**Goal:** Build and independently check the first bounded abstraction comparison.
**Architecture:** Compile the existing one-bet river game into joint weighted
payoff matrices. Aggregate matrices by private-hand groups, train alternating CFR,
and lift policies back into the exact-hand game for best-response evaluation.
**Tech Stack:** CPython 3.14.6, NumPy, existing unittest registry.
**Spec:** `docs/research/river-abstraction-study.md`.

## Global constraints

Python 3.14.6 only. No new dependencies. No holdout execution, blueprint mutation,
significant retained campaign, commit or push in this preparation task.
Keep training, preparation and evaluation timing separate from memory tracing.

## Task 1: Payoff kernel and regret updates

Create `src/pontius/river_abstraction_study.py` and
`tests/test_river_abstraction_study.py`; register the latter in `tests/cases.json`.
Interfaces: `PayoffGame.from_river(game)`, `.aggregate(groups)`, `.evaluate(x,y)`,
`.lift_policy(game,x,y)`, and `CFR(game).step()` / `.average()`.

- [x] Write a small weighted overlapping-hand fixture and independently evaluate
  complete policies through `evaluate_profile`, using these assertions:

  ```python
  actual = matrix.evaluate(x, y)
  expected = evaluate_profile(game, matrix.lift_policy(game, x, y))
  assert abs(actual['value'] - expected.utilities[0]) < 1e-12
  assert abs(actual['exploitability'] - expected.exploitability) < 1e-12
  ```

- [x] Run `python -m unittest tests.test_river_abstraction_study`; record the missing
  module RED. Implement the three payoff matrices and formulas in the spec.
- [x] Match current and average vanilla CFR strategies against `TabularCFR` at
  iterations 1, 2, 10 and 50, including a grouped information-state wrapper.
- [x] Check a tiny normal-form solution lies between computed L and U. Check ties,
  invalid policy lengths, NaN, raises and incomplete grouping fail explicitly.

## Task 2: Representations and bounded smoke

Add `uniform_equities(board)`, `representations(matrix,equities)` and
`development_case(board, hand_count, regime)` to the module. Create
`tools/river_abstraction_study.py` with one explicitly named output directory,
the two development boards, a maximum of 96 hands/player and 10,000 iterations.

- [x] Independently enumerate 990 opponents for baseline bucket checks; test
  collision-conditioned feature sums, occupied capacity and deterministic labels.
- [x] Implement seeded anchored clustering with 20 updates; test duplicate vectors.
- [x] Driver retains source/input hashes, exact hands/weights, policies, group maps,
  full/reduced metrics and separate times in an exclusively created directory.
- [x] Run the 16-hand, 100-iteration first-board smoke; no holdout access. Run focused
  tests plus original river/CFR suites and Ruff on changed Python files.
- [x] Write author results and limitations with exact commands and observed counts.
  Supply a review entrypoint; publication and campaign execution remain separate.
