# River CFR comparison 001

DCFR+ led this fixed-game comparison. Prediction did not beat discounting alone.
This is one observed river position, not a fresh-board confirmation or a bot-strength result.

## Frozen question and design

Compare update rules on retained case 001's baseline river tree: board card IDs [29, 1, 44, 32, 8],
pot 29, 1,081 private hands per role, collision-aware retained joint distribution,
half-pot and pot opening bets, fold/call responses, and forced checkback after a check.
No raises, sampled deals, hand abstraction, neural evaluation, GPU execution, or new LP calls.
The state/ranges and frozen binary64 payoff arrays are the same as the retained LP reference.
Reached ranges remain factorized; folded-player card bunching is not introduced here.

Each arm starts uniformly with zero regrets. One iteration updates role 0, then role 1.
Float64 CPU, one numerical thread, Python 3.14.6 and NumPy 2.5.2. Average strategies weight
each information set by its player's own reach. Three fresh-process repeats rotate arm order;
2,048 iterations and five checkpoints per run. The three repeats are timing replications,
not independent boards or random match samples. All policy arrays match byte for byte.

The first three arms use averaging exponent gamma=4. Both discounted arms there use
alpha=1.5 and denominator +1; their only update difference is prediction. The remaining
controls use ordinary linear-averaged CFR+, released DCFR+ (+1.5 denominator), and published
PDCFR+ (alpha=2.3, gamma=5). There is no parameter search on this game.

## Results at 2,048 iterations

Error is exploitability = half the exact best-response interval width, in units where
the starting pot is 10. Divide by 10 for fraction of pot. Smaller is better.

| Configuration | Exploitability | Median training s | Worker peak MiB | Exact audit s |
|---|---:|---:|---:|---:|
| CFR+, matched averaging | 4.93316e-05 | 3.427 | 130.7 | 0.887 |
| DCFR+, paper denominator +1 | 6.09262e-06 | 3.453 | 130.2 | 0.887 |
| PDCFR+, matched parameters | 3.65225e-05 | 3.471 | 130.4 | 0.901 |
| CFR+, linear averaging | 7.12163e-05 | 3.456 | 128.8 | 0.930 |
| DCFR+, released-code denominator +1.5 | 3.5038e-06 | 3.357 | 130.4 | 0.890 |
| PDCFR+, published parameters | 7.32175e-05 | 3.407 | 129.0 | 0.858 |

With averaging fixed, paper DCFR+ has 8.10x less
error than CFR+. Adding prediction with the same alpha/gamma increases error
5.99x relative to that DCFR+ arm.
Released-code DCFR+ has 20.33x less error than
linear-averaged CFR+; that comparison changes discounting and averaging together.
The two DCFR+ definitions are retained under separate names, without choosing one silently.

Training times exclude input load, checkpoint scoring and the independent rational audit.
Each worker loads the frozen arrays itself. Median complete worker walls, per-arm ranges,
verification memory and all checkpoint curves are in assessment.json and curves.csv.
Initial game/payoff preparation took 0.0338 s, excluding imports,
engine audits, serialization and freezing. The shared arrays use
35.66 MiB. This is not complete live decision latency.
Memory limits were sampled at 50 ms and were not hard caps. No worker hit a stop.

## Verification and interpretation

Four test methods passed, covering hand-derived discount/prediction updates, uniform
fallback, a convergent perfect-information toy game, literal hidden-hand profile values,
exhaustive pure best responses, and exclusion of own reach from regret. The frozen engine
audit checked every terminal with a win, loss and tie: 15 checks. The independent retained
rational evaluator recomputed all six final profile values and best-response intervals
after quantization onto the 2^48 behavior grid. Every float result agrees within 1e-10,
and every response interval contains the retained LP equilibrium interval.

These certificates validate the reported residuals. NONE passes the older strict
gap <= 1e-8 equilibrium threshold; the LP reference remains more accurate. Intermediate
curve points use the new floating evaluator, while final errors use exact rational checks.
No comparison here demonstrates a memory advantage on the two expanded trees that stopped
inside HiGHS. That remains the next useful test after checking transfer to another case.

## Formula provenance

- Paper Table 1: https://arxiv.org/html/2404.13891v2
- Released DCFR+ implementation:
  https://github.com/rpSebastian/PDCFRPlus/blob/main/pdcfrplus/cfr/dcfr_plus.py
- Released PDCFR+ implementation:
  https://github.com/rpSebastian/PDCFRPlus/blob/main/pdcfrplus/cfr/pdcfr_plus.py

The paper's DCFR+ denominator adds 1; the released implementation adds 1.5.
PDCFR+ discounts the accumulator, clips it, then uses a separately discounted accumulator
plus the latest instantaneous regret to predict the next policy. Accumulation excludes
that prediction term. The source-derived label documents what was tested; it is not a
claim to reproduce the paper's entire benchmark protocol or its plotted results.

## Retention

Plan SHA-256: f29618dc2eb2e73a89154b645ad20c778dd7cced85f45654edd559bc229354ea
The user authorized this comparison with "Let's run the comparisons". No commit, push,
policy adoption, large training or retained bot invocation was performed. New research
files are isolated; prior source and experiment bytes remain unchanged. This report was
written after the run. There was no independent agent review of this new harness.
