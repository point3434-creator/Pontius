# Proposed first research comparison

Status: preparation while the single opposing review is pending. This document
does not record run authorization or imply that any comparison has executed.

Use the reviewed candidate, CPython 3.14.6, one BLAS thread, and four sequential
cases. Holdout boards are excluded. No policy or grouping selection is changed
after the author smoke observations.

| Case | Development board | Range regime | Hands per player | Iterations |
| --- | --- | --- | --- | --- |
| d0-uniform | 2c 7d 9h Js Qc | uniform | 96 | 10,000 |
| d0-polarized | 2c 7d 9h Js Qc | polarized | 96 | 10,000 |
| d1-uniform | 2h 7h Jh Qc Ks | uniform | 96 | 10,000 |
| d1-polarized | 2h 7h Jh Qc Ks | polarized | 96 | 10,000 |

All four representations run in each case with checkpoint policies at 100, 1,000,
and 10,000 iterations. This yields 48 profile records across the four cases.
The input ranges and joint distributions are fixed and retained. Collisions are
rejected once when constructing each case, with no policy-dependent exclusion.

The result summary must recompute each checkpoint's exact-hand metrics from the
saved policies and ranges, verify all file hashes, and require the complete
4 cases x 4 methods x 3 checkpoints grid before any aggregate comparison.
Every per-case result remains visible, including deterioration.

Primary comparison: full-game exploitability in chips and pot fractions at the
same iteration checkpoints, with per-case differences against baseline bins and
an equal-weight mean across the four declared cases. Separately report restricted
exploitability, exact-hand reference bounds, training time and array storage.
No sampling confidence interval or claim of generalization to other boards.

Interpretation: reduced full-game exploitability at 10,000 iterations is evidence
of an advantage for these fixed cases at this training budget. It is not proof
of a smaller asymptotic abstraction floor. Mixed signs mean mixed results.
Never select the best earlier checkpoint per method as the headline comparison.
The range-equity-only control is retained regardless of which method wins.

Before a formal retained campaign: complete the review, bind the final bytes,
add the bounded multi-case plan consumer required by the design, and measure and
bind its resource limit. All four development runs fit one approval scope; a
separate approval per case is unnecessary. Holdout execution is a later decision.
