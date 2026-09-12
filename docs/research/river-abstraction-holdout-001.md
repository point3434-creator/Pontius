# Holdout-001: fixed river-abstraction comparison

Completed once under the controller's approval of the r002 plan. All four cases
exited 0, all 48 checkpoint profiles are retained, and campaign exit was 0.
The invocation took 8.746 seconds including parent verification.
No source, feature, grouping, population, checkpoint or range parameter was tuned.

## Fixed headline: 10,000 iterations

Equal-weight means across the four declared holdout cases; lower is better.
Pot size is 10 chips. Exact-hand is a finite-budget reference, not exact equilibrium.

| Method | Exploitability, chips | Fraction of pot |
| --- | ---: | ---: |
| exact | 0.0001828181 | 0.0000182818 |
| uniform_equity_200 | 0.0106397620 | 0.0010639762 |
| range_equity | 0.0092022664 | 0.0009202266 |
| range_response | 0.0090027338 | 0.0009002734 |

Range-response grouping reduces the mean by 15.39% versus uniform-equity bins and
2.17% versus range-equity grouping. Range-equity alone reduces the baseline mean
by 13.51%. These are ratios of the declared equal-weight means, not means of ratios.

| Case | Uniform-equity bins | Range-equity | Range-response |
| --- | ---: | ---: | ---: |
| holdout-0-uniform | 0.0150032838 | 0.0154091014 | 0.0126135731 |
| holdout-0-polarized | 0.0174958857 | 0.0126857652 | 0.0164280568 |
| holdout-1-uniform | 0.0044710636 | 0.0045392993 | 0.0044887774 |
| holdout-1-polarized | 0.0055888148 | 0.0041748996 | 0.0024805279 |

Both range-response comparisons are mixed: three lower-exploitability cases and
one higher-exploitability case against each control. The second-board uniform
case is slightly worse than the baseline; the paired-board polarized case is
worse than range-equity. Neither exception is omitted or rounded into a tie.
The machine-readable summary retains exact differences and sign counts for all
three checkpoints; the headline was not selected from the observed trajectory.

The positive average direction carries over from development, but the baseline
reduction is smaller than development's 49.19%. This supports further investigation
of the features; it does not establish uniform superiority. In particular, the
increment over range-equity alone is small and case-dependent on this holdout.
The boards were declared cases, not a random board sample; these are conditional
finite-population results with finite-budget policies, not a confidence interval,
all-board guarantee, abstraction-floor proof, six-max strength or BB/100 claim.
These two boards are now observed and must not be described as unopened holdout
data in later tuning or confirmation work.

## Verification and retention

All 35 campaign manifest members verified and the copied plan is byte-identical
to the approved plan. All 18 comparisons were recomputed from retained records.
All 48 lifted policies were also evaluated independently through the original
RiverState terminal returns and scalar math.fsum calculations. Maximum discrepancy
was 1.09e-15 chips. The independent check reuses the
original game's card evaluator, but does not use the matrix payoff/BR implementation.
The runner separately reconciled inputs, capacities, lifted policies and restricted
metrics using its tested kernel. Equal group counts held for all compressed methods:
25/26 on the first board and 62/62 on the second; the exact reference used 96/96.

The original retained directory is
D:/Pontius-training/river-abstraction-study/holdout-001.
It was not modified during analysis. Its byte-exact campaign copy plus analysis,
authorization/captures/receipt and verification is the 45-file, 2,547,819-byte
[milestone](../../experiments/river-abstraction-study/holdout-001/).
The [milestone manifest](../../experiments/river-abstraction-study/holdout-001/milestone-manifest.json)
binds the archive. Absolute paths in retained scripts and receipts describe the
execution machine; archival scripts are evidence, not authorization to invoke again.

- [Summary and all comparisons](../../experiments/river-abstraction-study/holdout-001/summary.json)
- [Independent scalar analysis](../../experiments/river-abstraction-study/holdout-001/analysis.json)
- [Verification receipt](../../experiments/river-abstraction-study/holdout-001/verification.json)
- [Reviewed plan and disposition](river-abstraction-holdout-r002/disposition.md)
- [Prior development results](river-abstraction-study-development-001.md)

The source and results remain uncommitted and unpushed. Earlier packet readiness
statements are preserved as historical evidence; this report records the completed
invocation. Approval applied to this run only, not publication or another experiment.
