# ADR-0022: Sequential river allows only a post-probe scheduler screen

**Status:** Accepted

**Date:** 2026-08-19

## Decision

Accept the fixed-raise river as the first exact sequential-action scheduler
gate. It adds one legal fixed raise-to action and a final opener fold/call
response, so the opener acts twice on bet-raise paths. The independent
normal-form teacher conditions mixed pure plans on remembered own actions when
converting them to behavioral play.

Reject total remaining improvement as the primary scheduler target. Report it
as headroom, but rank computation by payoff-normalized improvement per measured
solver millisecond and per deterministic state visit. Use state-visit efficiency
as the primary development target because it is reproducible; measured time is
its required timing replicate.

Do not fit a neural scheduler or reveal reserved boards yet. Authorize one
transparent development-only post-probe screen. Every context must pay for the
two iterations that create its early features. A candidate may allocate only
the remaining work and must be compared with the matched fixed checkpoint under
the same aggregate budget.

The candidate family should remain small: solver regret summaries, policy
movement, raise geometry, and at most a cheap shadow-regret statistic computed
from an already-paid traversal. It must have an explicit fixed-checkpoint
fallback. A separate preregistration must freeze its score, macro-options, and
failure thresholds before validation or test contexts are constructed.

## Exact sequential gate

The raise amount is a raise-to total, at least twice the opening bet, and no
larger than either starting river stack. If the opener folds, its initial bet is
sunk and the uncalled part of the raise is returned. If the raise is called,
showdown utility has magnitude `pot / 2 + raise_to`. Tests cover all terminal
payoffs, hidden opponent cards, remembered own action history, invalid raises,
dynamic versus exhaustive best response, and the independent LP.

On the analytical two-hand control with a uniform policy, exact NashConv is
`35/6` while summed positive one-step counterfactual regret is `20/3`. The
one-bet identity is therefore genuinely broken. At equilibrium, the behavioral
realization produced by the normal-form LP has machine-precision NashConv.

## Production evidence

The clean production run comes from commit `09acdfb`. It contains 256
development board groups, 1,024 exactly paired range contexts, 4,096 solver
trajectories, and 53,248 checkpoint records. Validation and test contexts were
not constructed. The raw artifact is 207,056,847 bytes with SHA-256
`e8ae3e078f588434eec7ef84300dab73015df8ca7a5bfd6769b1fc6d5d569ff7`.

Maximum teacher duality gap is `1.0413e-11`; maximum realized behavioral
NashConv is `1.0413e-11`. Fresh local regret differs materially from NashConv in
48,982 of 53,248 records (`91.99%`). Its mean absolute difference is `0.01298`
payoff spans and its maximum is `0.11738` payoff spans.

| Solver | Exploitability @ 4 | @ 16 | @ 64 | Any regression |
|---|---:|---:|---:|---:|
| CFR | 1.62104 | 0.38544 | 0.09952 | 25.10% |
| LCFR | 1.09951 | 0.15438 | 0.02834 | 57.03% |
| CFR+ | 0.97987 | 0.10479 | 0.01272 | 45.90% |
| DCFR | 0.91698 | 0.09794 | 0.00854 | 57.42% |

Checkpoint-two normalized positive regret ranks three different labels very
differently:

| Solver | Total future headroom | State-visit efficiency | Millisecond efficiency |
|---|---:|---:|---:|
| CFR | 0.796 | 0.518 | 0.513 |
| LCFR | 0.771 | 0.390 | 0.388 |
| CFR+ | 0.895 | 0.594 | 0.592 |
| DCFR | 0.869 | 0.473 | 0.473 |

All five board-group-preserving state-efficiency folds remain positive. Their
ranges are `0.432-0.564`, `0.271-0.475`, `0.450-0.645`, and `0.372-0.533` for
CFR, LCFR, CFR+, and DCFR. State-visit and independently measured-millisecond
target rankings agree at Spearman `0.9946-0.9991`. The signal is real, but much
weaker than the total-headroom headline.

The exact future allocator on the fixed 128-context sample has a budget-two
uplift of 18.1%-22.9%, far below the one-bet control's 51.1%-75.9%. Because a
checkpoint-two feature is unavailable until that work is paid, the causal
comparison is average budget four after a mandatory two-iteration probe:

| Solver | Perfect post-probe uplift over fixed checkpoint 4 |
|---|---:|
| CFR | 4.15% |
| LCFR | 5.04% |
| CFR+ | 6.00% |
| DCFR | 5.44% |

This remains an optimistic ceiling with exact future labels. It proves useful
allocation exists after feature-acquisition cost; it does not show that current
features can realize the gain.

## Paired non-transfer result

The one-bet and sequential production traces contain identical context IDs,
boards, opening bets, and complete joint ranges. Despite that pairing, the
one-bet feature ranks the sequential state-efficiency target at only `-0.070`,
`-0.191`, `0.009`, and `-0.132` for CFR, LCFR, CFR+, and DCFR. Feature-rank
stability itself is only `0.183-0.293`.

Therefore board/range "hardness" is not a reusable cache entry across tree
constructions. The useful statistic is produced by traversing the current tree.
This supports a cheap online probe or shared-traversal shadow statistic and
rejects static difficulty labels learned from the shallower abstraction.

## Dissent protocol

**Verdict:** the sequential gate passes; advance one transparent post-probe
scheduler screen, not a learned scheduler.

**Confidence:** high in game/oracle correctness and the development-only
measurements; moderate that a cheap rule can capture some of the 4%-6% ceiling;
low that the magnitude transfers to six-player, earlier-street hold'em.

**Supporting evidence:** independent LP teachers, dynamic/exhaustive response
agreement, explicit failure of the local-regret identity, 1,024 paired contexts,
positive group-preserving efficiency folds, measured-time replication, paid
probe accounting, and exact artifact provenance.

**Opposing evidence:** the game is heads-up, zero-sum, river-only, and permits
only one fixed raise; ranges and bet sizes are synthetic; the strongest scalar
efficiency correlation is only `0.594`; LCFR falls to `0.390`; and the perfect
post-probe ceiling is at most 6.00% at the primary budget.

**Largest unknown:** whether a low-overhead causal score can capture enough of
that narrow ceiling without overfitting bet geometry or solver identity.

**Cheapest falsifying experiment:** group-cross-validate a tiny transparent
score and a fixed set of post-probe macro-options at average budget four. Charge
all feature and decision costs. Freeze the rule before constructing any
reserved context.

**Kill criterion:** if no preregistered candidate improves fixed checkpoint four
in every development fold or captures at least 25% of the aggregate perfect
post-probe uplift, retain fixed scheduling and move to range-cache
recertification and richer reduced hold'em. If a candidate passes development
but fails its frozen reserved evaluation, reject it without retuning.

**Recommendation:** test a simple CFR+/DCFR-oriented score, including whether a
cheap shadow regret accumulated from the paid traversal improves ranking. Keep
the heuristic fallback; neural value-of-computation remains deferred.
