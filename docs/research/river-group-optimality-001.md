# Group-optimality-001: what the fixed hand groups can represent

The single approved invocation completed successfully: eight already observed
cases, 32 fixed-group solutions, 64 asymmetric linear programs, and comparisons
against all 96 saved profiles. Worker exit and parent exit were both 0. The worker
took 26.521 seconds; the full invocation, including parent verification, took
45.877 seconds. No retry or additional optimization run was made.

The main result is that grouping restrictions account for most of the remaining
exploitability on the previously observed holdout cases. For range-response,
78.29% of the mean 10,000-iteration exploitability is forced by the fixed groups;
21.71% is recoverable through a different policy within those same groups.
These percentages are ratios of equal-weight means over four declared cases.

## Fixed headline: 10,000 iterations

All values below are exploitability in chips; lower is better. The pot is 10 chips.
The grouping floor is the certified minimum over policies obeying both players'
fixed group assignments, evaluated against unrestricted individual-hand responses.
The remaining gap is the saved policy's exploitability minus that floor.
Displayed decimals are rounded; exact rational intervals are retained in the data.

| Observed cohort | Grouping | Saved policy | Grouping floor | Remaining gap |
| --- | --- | ---: | ---: | ---: |
| Development | Uniform-equity | 0.01384237 | 0.00871572 | 0.00512665 |
| Development | Range-equity | 0.00812444 | 0.00552931 | 0.00259512 |
| Development | Range-response | 0.00703332 | 0.00513809 | 0.00189523 |
| Prior holdout | Uniform-equity | 0.01063976 | 0.00871034 | 0.00192943 |
| Prior holdout | Range-equity | 0.00920227 | 0.00700702 | 0.00219524 |
| Prior holdout | Range-response | 0.00900273 | 0.00704856 | 0.00195417 |

The exact-hand reference has a certified floor interval containing zero, with
cohort upper endpoints below 1.30e-16 chips. Its saved 10,000-iteration values
remain 0.0001694550 on development and 0.0001828181 on the prior holdout.

On development, range-response's floor is 41.05% lower than uniform-equity's and
7.08% lower than range-equity's. On the prior holdout, its floor is 19.08% lower
than uniform-equity's but 0.59% higher than range-equity's. Range-response's saved
policy was 2.17% better than range-equity's on that latter cohort; the certified
floor reverses this narrow average ordering. A finite-training comparison does
not by itself identify which grouping can represent the strongest policy.

## Per-case exceptions remain visible

| Prior holdout case | Uniform-equity floor | Range-equity floor | Range-response floor |
| --- | ---: | ---: | ---: |
| 0, uniform | 0.01238130 | 0.01061927 | 0.01166200 |
| 0, polarized | 0.01639077 | 0.01200964 | 0.01186147 |
| 1, uniform | 0.00268993 | 0.00276986 | 0.00290430 |
| 1, polarized | 0.00337934 | 0.00262933 | 0.00176647 |

Range-response has a lower floor than range-equity in two cases and a higher
floor in two. Against uniform-equity it is lower in three and higher in one.
The case 0 polarized saved range-response policy had a large gap (0.00456658
chips) despite a slightly better floor than range-equity. Conversely, in case 0
uniform it had a worse floor but a better saved policy. Both directions matter.

## Interpretation and next research decision

Improving group assignments is now the strongest next research target. Keep
range-equity and the current range-response method as controls, and investigate
group refinement based on disagreement in actual action values against retained
best-response witnesses. The certificates provide witnesses as well as scalar
scores, so the next design can locate which hands are being forced to share an
action despite different strategic incentives.

This is a recommendation, not a new run or an approved grouping change. A fair
next comparison should declare its grouping-capacity and compute budgets, tune on
development cases, and reserve new cases before inspecting their results. All
eight cases in this diagnostic were already observed. The prior holdout remains
useful for diagnosis but cannot serve again as unopened confirmation data.

The remaining gap combines finite-training and objective/policy-selection effects.
It is achievable within the fixed groups by pairing the two constrained-seat
witness policies; it is not a promise that more ordinary CFR iterations reach it.
The grouping floor is not the exploitability of an arbitrary equilibrium of the
game in which both opponents are compressed during training.

These are fixed two-player, one-bet river games with 96 hands per seat, not
six-max playing-strength, BB/100, all-board, or random-board statistical claims.
The certified inequalities concern exact rational encodings of stored binary64
payoff coefficients, not an ideal pre-rounding probability model.

## Verification and retention

The bound parent reconstructed the eight input games, reverified every rational
certificate and all saved-profile comparisons, and checked source and data pins
again before writing a complete summary and manifest. All 64 saddle certificates
passed the 1e-8-chip bound; the widest was 2.291e-15 chips.

A separate post-run arithmetic audit invoked no optimizer. It recomputed 64
asymmetric saddle pairs, all 32 paired constrained policies, and all 96 saved
profiles using scalar math.fsum accumulation. The maximum discrepancy from the
retained rational values was 2.186e-16 chips. It also recomputed the cohort means
and gap intervals with Fraction arithmetic. It reused reconstructed payoff
matrices and was not an independent card-evaluator implementation.

All 14 result-manifest members, 89 pre-existing packet members, seven identity
members, seven computational source pins and 32 input pins verified. The plan
copy exactly matches the authorized SHA-256:
de07461ea9364a4fb40d0bce72a506549bc30ac609761bb0bc57ff4600c3b11c.

Environment: Python 3.14.6, NumPy 2.5.2, SciPy 1.18.0 in the separately pinned
environment. The approved 300-second timeout applied to the worker; parent
verification and I/O were outside it. No process memory cap was imposed or peak
memory measurement claimed. Per-LP limits remained five seconds and 10,000 steps.

The original output at
D:/Pontius-training/river-abstraction-study/group-optimality-001
was not modified during analysis. Its byte-exact copy, invocation authority,
captures, independent arithmetic verification and helper scripts are retained in
the [named milestone](../../experiments/river-abstraction-study/group-optimality-001/).
The helper scripts are evidence, not authority to run again. The milestone's
manifest covers every other file in that archive.

- [Summary and all rational certificates](../../experiments/river-abstraction-study/group-optimality-001/summary.json)
- [Compact analysis](../../experiments/river-abstraction-study/group-optimality-001/invocation/analysis.json)
- [Verification receipt](../../experiments/river-abstraction-study/group-optimality-001/invocation/verification.json)
- [Authorization](river-group-optimality-r001/invocation-001/authorization.json)
- [Original reviewed disposition](river-group-optimality-r001/disposition.md)

Earlier readiness statements are preserved as historical records. This report
records the completed invocation. Source and results remain uncommitted and
unpushed; the controller approved this invocation, not publication or a later run.
